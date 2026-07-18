## Why

`async-outside-voice` 那一轮 dogfood 咬出三处**同一形状**的缺陷：**命令 `exit 0`、报告照常产出，但事情根本没做成**。三条都不是「功能缺失」，而是**机械层谎报成功**——本仓质量体系最不能容忍的一类（假绿放不完整的活过关，见 `adr/0008` 纵深防御、`adr/0018` 机械校验器输出诚实性）。

| | 静默点 | 实测现象 | 后果 |
|---|---|---|---|
| **B9** | `render_prompt()` 的 200KB 截断按**字节**切，腰斩 CJK | `codex exec` 报 `input is not valid UTF-8 (invalid byte at offset 107475)` → rc=1 | 降级同族 fallback，**跨模型第二意见静默丢失**；报告仍出、锚行仍落 |
| **B10** | `do_exec()` 的 trap 清了 workdir 但**不杀 runner 子进程** | 实测 `42998 1 timeout -k 10 60 sleep 45`（ppid 已成 1） | 孤儿 runner 跑满内层超时，**脱离 harness 回收域** |
| **B11** | recorder 三脚本**跨 checkout 版本偏斜且无握手** | `块有 B10 但缺总览表行` + `tagged 0 项`，**`exit=0`** | `/sdflow-done` 的 defer 分诊对**每个后续 change** 静默失效 |

**为什么现在做**：B9 让中文文档仓的跨模型评审层命中率约 2/3——评审体系的承重墙之一在悄悄漏水；B11 的损害随 change 数线性累积。两条都是 P1，且**只有在目标态视角下才看得见**（现状「报告出来了、命令绿了」恰恰是伪装）。

### B11 的根因被现场推翻，且比原判严重

原判「sweep 读旧总览表投影」**是错的**。实证：

| 跑法 | 结果 |
|---|---|
| **开发** checkout 的 `buglist.py … --open-ungrouped --json` | 4 条 bug，`problems` 空 ✅ |
| **开发** checkout 的 `issues.py sweep` | **tagged 15 项** ✅ |
| **运行** checkout（`~/.claude/skills/` symlink 所指）同款 | `块有 …但缺总览表行` + **tagged 0，exit 0** ❌ |

`~/.claude/skills/sdflow-issues → ~/.skills/sdflow-skills`（运行 checkout，HEAD `7fd59e6`，**是本仓 main 的祖先**，滞后于 recorder-frontmatter 合并）。`issues.py` 按**自身文件位置**定位兄弟脚本（这是 `issues.py:59-66` 明确记录的设计），于是派出的是**前 canonical/overlay 版** `buglist.py`（`grep -c overlay`：开发版 **7**、运行版 **0**），它只认总览表投影，对 frontmatter items 完全无视。

**⇒ 目标态下的取数逻辑是对的**（`_build_effective_snapshot` 已是 `legacy_owned ∪ frontmatter_items`，正是「块/frontmatter 为唯一真相源、表为派生」）。真正缺的是两样：**跨脚本无版本握手** + **唯一告警信号被排除在退出码之外**。

**血半径比 sweep 大——`reindex` 会写盘丢数据。** 本轮在 scratch 副本实跑旧 `issues.py reindex`：

```
reindex：已重建 INDEX.md（open 108 项，已闭合 51 项）   exit=0
已闭合计数 57 → 51；B9 / B10 / B11 在重建后的 INDEX 中全部消失
```

`cmd_reindex` / `cmd_batch_rename` / `cmd_batch_add` / `set-status` / `lint` 均经 `read_pool → _scan_pool` 走同一条取数路径。**sweep 只是不干活，reindex 是拿残缺集合覆盖权威索引，且 exit 0。**

**为什么 `exit=0`**（危害最大的部分，两处叠加）：
1. `issues.py:2211-2214` — `problems` 只回显 stderr、注释显式声明「不收紧退出码」（收紧被 defer 成 roadmap T2.5 的 `reindex --strict`）；
2. `issues.py:2233-2235` — `if not tagged: return`，0 命中被当合法幂等态。

两条**单独都合理**，合起来构成「**最响的告警 + 最静的退出码**」：唯一能区分「真没东西」与「读错投影」的信号（`problems` 非空）恰恰被排除在退出码之外。

## What Changes

- **B9 — 截断在切点上就保证字符边界**（而非事后清洗）：`render_prompt()` 头尾两半各自回扫 UTF-8 边界（≤4 字节，有界语法面）。**两半都要修，不能只修一头**。
- **B10 — 子进程生命周期焊进 helper**：runner 改后台执行 + 记 PID + `wait`，trap 覆盖 `INT TERM HUP` 并在清理时杀掉该 PID。
- **B11 — 版本握手 + 反静默，两条缺一不可**：
  - **sibling 脚本 schema 握手，fail-closed**：`issues.py` 在派子进程**前**核对 `buglist.py`/`todolist.py` 的 recorder schema 版本，不匹配即硬停并给出可执行修复指令（`/sdflow-upgrade` + `setup.sh`）；
  - **`problems` 非空 ⇒ 非零退出**：把唯一的失配信号接进退出码。**红线取 `problems` 非空、不取 `tagged=0`**——后者单独确实可能合法（重跑幂等），前者才是「两套投影失配」的诚实信号。
- **面治而非点补**（基准 ③）：握手落在**共用取数入口** `read_pool` / 派子进程处，一次覆盖 `sweep`/`reindex`/`batch rename`/`batch add`/`set-status`/`lint` 全部调用方，**不只补 sweep 一处**。

## Capabilities

### New Capabilities
- `outside-voice-exec-integrity`: outside-voice helper 自身的执行完整性——送出 prompt 的**字节合法性**保证，与 runner **子进程生命周期**归属（父被回收则子必死）。区别于既有 `host-adaptive-execution`（管宿主判定 / 锚契约 / 跨模型性），本能力管「helper 这个进程自己有没有把活干干净」。
- `recorder-cross-script-handshake`: recorder 三脚本（`issues`/`buglist`/`todolist`）跨进程调用的**版本握手**与**失配 fail-closed**——版本偏斜在本仓 dev/runtime 双 checkout 纪律下是**结构性常态、不是意外**（`adr/0005` + pull→setup 窗口期），故须机械守而非人肉约定。

### Modified Capabilities
- `batch-triage`: sweep 的**反静默退出语义**——`problems` 非空即非零退出，`tagged 0` 不再无条件当成功。

## 需求优先级〔TG-19〕

| ID | 需求 | 优先级 | 依据 |
|---|---|---|---|
| R1 | 截断产出保证合法 UTF-8（头尾两半各自合法） | **P0** | 直接致跨模型评审层失效，中文仓高频命中 |
| R2 | recorder sibling 调用前版本握手，失配 fail-closed | **P0** | 挡住 `reindex` 的**写盘丢数据**路径，血半径最大 |
| R3 | `problems` 非空 ⇒ 非零退出 | **P0** | 唯一告警信号接进退出码；静默是损害的放大器 |
| R4 | 父被回收时 runner 子进程必死 | **P1** | 资源泄漏 + 脱离回收域；不致结论错误，故次于 P0 |
| R5 | 握手落共用取数入口，覆盖全部调用方 | **P1** | 基准 ③ 面治；防「修完 sweep，reindex 照瞎」 |

## Success Metrics〔D-5〕

1. **跨模型 voice 在超长中文 context 下的成功率** — 基准：>200KB 中文 context 时 rc=1 必失败（实测 1/1） → 目标：**rc=0 且锚行 `reason_code="ok"`** — 度量：用本仓真实中文 diff 造 >200KB context 跑一次 `outside-voice.sh exec`，记 rc 与锚行；另加切点扫描测试（连续偏移全覆盖，两半均 `decode('utf-8')` 通过）。
2. **孤儿 runner 进程数** — 基准：SIGTERM 后残留 1 个 reparent 到 PID1 的 runner（实测） → 目标：**0** — 度量：起脚本 → 外部 SIGTERM → `ps` 验尸须为空。
3. **版本偏斜下的失败可见性** — 基准：旧 sibling + `reindex` ⇒ **exit 0 且 INDEX 被残缺集合覆盖**（实测：已闭合 57→51、B9/B10/B11 消失） → 目标：**非零退出、零写盘、stderr 给出可执行修复指令** — 度量：用滞后版 sibling 跑 `sweep`/`reindex`，断言退出码非零且 INDEX 字节未变。

## Non-Goals〔D-3，每条附可证伪假设〕

- **不重构 recorder 三脚本的物理复制**（各自自包含，`adr/0025` 明确「维护成本由 AST parity、golden bytes、call-graph 测试承担」）。*可证伪假设*：握手只需在**调用方**（`issues.py`）加预检 + 被调方加一个版本自报子命令，不需要合并实现——若发现握手语义本身必须在三份里各写一套**且无法用现有 parity 测试守住漂移**，则假设被证伪。
- **不把 `issues.py` 改成 in-process import sibling 模块**。*可证伪假设*：走 CLI 子进程的既有决策（`issues.py:59-66` 记录：避 args-namespace 脆弱性）在加了版本握手后仍成立——若握手无法在进程边界上可靠传递版本，则假设被证伪。
- **不改锚行契约与 `anchor_lint` 合法组合矩阵**。*可证伪假设*：B9 修复后 `reason_code` 由 `exec-error` 变 `ok` 属既有枚举内的取值变化——若需表达「曾截断但已安全」这类新状态才能诚实落锚，则假设被证伪。
- **不做 async/backgrounding 相关改动**（`async-outside-voice` 已交付）。*可证伪假设*：B10 只涉及 `do_exec` 内部信号与子进程，不触碰两层 SKILL 的字节等值 marker 段——若修复必须改段内内容，则假设被证伪，须同步两侧并跑 parity 门。
- **不迁移历史 legacy 表条目**（`adr/0025`：历史 Git 文档不批量重写）。*可证伪假设*：开发版取数逻辑已正确处理 `legacy_owned ∪ frontmatter_items`，本 change 零写侧迁移即可——若发现不迁移就无法区分 owner，则假设被证伪。
- **不自动升级运行 checkout**。*可证伪假设*：fail-closed + 可执行指令足以让人在 30 秒内自救；自动 `git pull` 会在 skill 运行中途改变自身代码，风险高于收益——若实践中发现该硬停频繁卡住自动链路，则假设被证伪，须重议。

## 假设列表〔TG-22〕

| # | 假设 | 失效影响 | 状态 |
|---|---|---|---|
| A1 | 截断修复在 macOS 与 Linux 行为一致 | 一个平台绿、另一个仍吐非法 UTF-8，且本地测不出（见 `windows-ci-bash-subprocess-traps` 同类坑） | **macOS 已实测**（201 个连续切点 0 失败）；**Linux 待 CI 泳道覆盖** |
| A2 | 杀子进程手段可移植 | 修复只在一个平台生效 | **已收敛**：`setsid` 在 macOS **不存在（证伪）**；改用 `wait` + trap，实测 TERM 后 timeout/中间脚本/孙进程三层全灭 |
| A3 | `exit 0` 改 fail-loud 不打断既有调用方 | `/sdflow-done` §2.1 由静默过变硬停，可能卡住收尾链 | **待验**：须通读全部调用点，确认与 done 的「非原子、fail-closed、重跑收敛」契约相容 |
| A4 | 三条缺陷相互独立，可在一个 change 内并行修 | 修一条踩另一条 | 各自独立测试 + 收尾全套件 |
| A5 | 父进程被 **SIGKILL** 时孤儿不可避免 | 残余风险，非本 change 可根治 | **已实测确认为真**：SIGKILL 不可 trap，shell 层无解 ⇒ 须在 design 显式登记为诚实边界，**不得声称根治** |

## 利益相关方与外部依赖〔TG-20〕

- **下游消费项目**：`sdflow-init/assets/hack/outside-voice.sh` 是 bundle **唯一权威源**，改动经 `sdflow-init update` 推给所有消费仓。B9/B10 对下游是**纯修复、无接口变化**，但须走「改 assets → 推下游」纪律，**禁止只改仓内副本**。
- **外部工具依赖**〔D-4〕：`codex` / `claude -p` / `timeout|gtimeout` / `od`（B9 边界回扫用；macOS 与 Linux 基础系统均自带）。**推荐方案零新增运行时依赖**——`iconv` 与 `python3` 两条备选均不进 helper（理由见 design ADR）。
- **运行 checkout 纪律**：改 `assets/hack/` 下脚本后**必须重跑 `setup.sh`**（拷贝非 symlink）。本 change 的 R2 正是要把这条纪律从人肉约定升级为机械门。

## Impact

- `sdflow-init/assets/hack/outside-voice.sh`（B9/B10，bundle 权威源）
- `sdflow-issues/scripts/issues.py`（握手预检 + `problems` 退出码）、`sdflow-buglist/scripts/buglist.py`、`sdflow-todolist/scripts/todolist.py`（各加版本自报）
- 对应 `tests/`：三个 recorder skill 的 pytest + `hack/tests/`
- `.github/workflows/mechanical-gates.yml`（A1 需要 Linux 泳道覆盖截断切点测试）
- **不触及**：两层评审 SKILL 的 async 字节等值 marker 段、`anchor_lint` 矩阵、recorder frontmatter envelope schema

## Compliance〔D-6：逐条核对既有 ADR / 架构边界〕

| ADR / 边界 | 核对结论 |
|---|---|
| `adr/0025`（recorder frontmatter overlay） | **遵守**。目标态取数逻辑已正确实现；本 change 只加**跨脚本版本握手**与退出码，不改 envelope schema、不改 item JSON 形状、不改 ID 语义、不改 lock 协议、不批量迁移历史 |
| `adr/0010`（issues 机器态 markdown） | 已被 0025 supersede 新写决策；本 change 不复活旧写侧契约 |
| `adr/0011`（共用解析核心的返回语义按消费方各自定） | **命中**：握手落共用取数入口 ⇒ **每个调用方各自验证**（sweep / reindex / batch rename / batch add / set-status / lint），不得只测 sweep 一条 |
| `adr/0018`（机械校验器输出诚实性） | **遵守，且是 R3 的直接依据**：`problems` 非空不得伪装成成功 |
| `adr/0008`（gate 纵深防御非信任纪律） | **遵守，且是 R2 的直接依据**：把「记得先 upgrade」从人肉纪律换成机械 fail-closed |
| `adr/0005`（dev/runtime checkout 分离） | **遵守，且本 change 正是给该纪律补机械守**：版本偏斜是该架构的**结构性常态**（pull→setup 窗口期），不是意外 |
| `adr/0022`（skill 可改不可删用户文件） | **命中**：R2 的 fail-closed 必须在**任何写盘之前**——现状 `reindex` 是先算后覆盖，握手须前置到 discovery 之前 |
| 基准 ⑤（无界语法禁手搓） | **UTF-8 是有界语法面**（≤4 字节、continuation 形态确定）⇒ 边界回扫合规，且实测 201 切点 0 失败。**禁止演化成通用编码嗅探器**——只认 UTF-8，不做编码检测 |
| 跨产品 / 跨模块共享数据模型边界〔D-6 阻塞条款〕 | **命中并显式确认未越界**：issue 记录的 frontmatter envelope 是三脚本共享数据模型。本 change **只加版本握手与退出码语义，不改数据模型本身** ⇒ 不构成边界变更 |
