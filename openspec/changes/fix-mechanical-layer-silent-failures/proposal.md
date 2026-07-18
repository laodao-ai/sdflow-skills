## Why

`async-outside-voice` 那一轮 dogfood 咬出一批「**命令 `exit 0`、报告照常产出，但事情根本没做成**」的机械层静默失效。本 change 只处理其中**已被实测坐实、且不依赖任何未验证前提**的两条：

| | 静默点 | 实测现象 | 后果 |
|---|---|---|---|
| **B9** | `render_prompt()` 的 200KB 截断按**字节**切，腰斩 CJK | `codex exec` 报 `input is not valid UTF-8 (invalid byte at offset 107475)` → rc=1 | 降级同族 fallback，**跨模型第二意见静默丢失**；报告仍出、锚行仍落 |
| **B10** | `do_exec()` 的 trap 清了 workdir 但**不杀 runner 子进程** | 实测 `42998 1 timeout -k 10 60 sleep 45`（ppid 已成 1） | 孤儿 runner 跑满内层超时，**脱离 harness 回收域**，白烧 API 调用 |

两条都在 `sdflow-init/assets/hack/outside-voice.sh`——bundle 唯一权威源，改动经 `sdflow-init update` 推给所有消费仓。

## 范围收缩记录（本 change 曾包含 B11/B12，已拆出）

初版把 recorder 侧的 **B11**（`sweep` 静默 0 项）与 **B12**（`reindex` 拿残缺集合覆盖权威 `INDEX.md` 且 exit 0）一并纳入。经**三轮评审**（grill → 9 单元设计审 → 3 单元接缝冷审）后拆出，依据如下：

- recorder 半边独占约 **19 条致/高**，B9/B10 半边**≈0**（仅一条措辞级）；
- 其中**拓扑虚构错了两次**（第二版修法仍与 `_reindex_core(root, snapshot=updated)` 的实际分支不符），**退出码地基不成立**（`ValueError→2` 同时覆盖 malformed JSON、frontmatter 损坏这类**永久失败**，整个码空间不区分「可否重试」）；
- 判别式不是「难易」而是「**结论怎么来的**」：B9/B10 每条断言都有实验（201 个连续切点、`setsid` macOS 证伪、SIGTERM 验尸、杀 timeout 连带杀孙进程实测三层全灭）；recorder 侧的结论来自**读码**，在 5545 行 / 三份拷贝 / 双取数路径的规模上系统性不可靠。

**⇒ B11/B12 与其根因（recorder 三份物理复制 parser 的结构问题）合并为 `T170` 统一处理，MUST NOT 单独捡 B11/B12 修**——那正是已被三轮评审证否的路径。
**R7**（截断覆盖面诚实）经 `T171` 退出本 change：它是 grill 期按「低影响」fold 进来的，事后产出 4 条呈链式的缺陷，链条从未被真正跑过一次。

## What Changes

- **B9 — 截断在切点上就保证字符边界**（而非事后清洗）：头尾两半各自回扫 UTF-8 边界（≤4 字节，有界语法面）。**两半都要修，不能只修一头。**
- **B10 — 子进程生命周期焊进 helper**：runner 改后台执行 + 记 PID + `wait`，trap 覆盖 `INT TERM HUP` 并在清理时杀掉该 PID。

## Capabilities

### New Capabilities
- `outside-voice-exec-integrity`: outside-voice helper 自身的执行完整性——送出 prompt 的**字节合法性**，与 runner **子进程生命周期**归属（父被回收则子必死）。区别于既有 `host-adaptive-execution`（管宿主判定 / 锚契约 / 跨模型性），本能力管「helper 这个进程自己有没有把活干干净」。

### Modified Capabilities
（无）

## 需求优先级〔TG-19〕

| ID | 需求 | 优先级 | 依据 |
|---|---|---|---|
| R1 | 截断产出保证合法 UTF-8（头尾两半各自合法） | **P0** | 直接致跨模型评审层失效，中文仓高频命中 |
| R2 | 父被回收时 runner 子进程必死 | **P1** | 资源泄漏 + 脱离回收域 + 白烧 API；不致结论错误，故次于 P0 |

## Success Metrics〔D-5〕

1. **跨模型 voice 在超长中文 context 下的成功率** — 基准：>200KB 中文 context 时 rc=1 必失败（实测 1/1） → 目标：**rc=0 且锚行 `reason_code="ok"`** — 度量：造 >200KB 中文 context 跑一次 `outside-voice.sh exec`，记 rc 与锚行；另加切点扫描测试（连续偏移全覆盖，两半均严格模式解码通过，失败数 0）。
2. **孤儿 runner 进程数** — 基准：SIGTERM 后残留 1 个 reparent 到 PID1 的 runner（实测复现） → 目标：**0** — 度量：起脚本 → 外部 SIGTERM → `ps` 验尸须为空。

## Non-Goals〔D-3，每条附可证伪假设〕

- **不改 recorder 侧任何代码**（B11/B12 已拆出）。*可证伪假设*：B9/B10 的修复只触及 `outside-voice.sh`，与 recorder 取数路径零交集——若实现期发现必须动 recorder 才能完成，则假设被证伪，须停下重议拆分决定。
- **不做 R7（截断覆盖面诚实）**。*可证伪假设*：「截断产出合法 UTF-8」与「截断了要说出来」是两件可分离的事——若发现不做 R7 就无法验证 R1 的效果，则假设被证伪。
- **不做「让截断变聪明」**（分块多轮送 / 动态调上限 / 按内容智能裁剪）。*可证伪假设*：保头尾各半的既有策略本身不在本次讨论范围，本次只保证它产出的字节合法——若发现字符边界安全无法在现策略下达成，则假设被证伪。
- **不改锚行字段与 `anchor_lint` 合法组合矩阵**。*可证伪假设*：B9 修复后 `reason_code` 由 `exec-error` 变 `ok` 属既有枚举内取值变化；B10 引入的 143 由既有 catch-all（未知码 ⇒ 保守 `exec-error`）吸收——若需新状态才能诚实落锚，则假设被证伪。
- **不做 async/backgrounding 相关改动**。*可证伪假设*：B10 只涉及 `do_exec` 内部信号与子进程，不触碰两层 SKILL 的字节等值 marker 段——若修复必须改段内内容，则假设被证伪，须同步两侧并跑 parity 门。

## 假设列表〔TG-22〕

| # | 假设 | 失效影响 | 状态 |
|---|---|---|---|
| A1 | 截断修复在 macOS 与 Linux 行为一致 | 一个平台绿、另一个仍吐非法 UTF-8，且本地测不出 | **macOS 已实测**（201 连续切点 0 失败）；**Linux 待 CI 泳道覆盖** |
| A2 | 杀子进程手段可移植 | 修复只在一个平台生效 | **已收敛**：`setsid` 在 macOS **证伪不存在**；改用 `wait` + trap，实测 TERM 后 timeout / 中间脚本 / 孙进程**三层全灭** |
| A3 | 父进程被 **SIGKILL** 时孤儿不可避免 | 残余风险 | **已实测为真**：SIGKILL 不可 trap，shell 层无解 ⇒ 显式登记，**不得声称根治** |

## 利益相关方与外部依赖〔TG-20〕

- **下游消费项目**：`outside-voice.sh` 是 bundle **唯一权威源**，改动经 `sdflow-init update` 推给所有消费仓。对下游是**纯修复、无接口变化**。**禁止只改仓内副本。**
- **外部工具依赖**〔D-4〕：`codex` / `claude -p` / `timeout|gtimeout` / `od`（边界回扫用，macOS 与 Linux 基础系统均自带）。**推荐方案零新增运行时依赖**。runner 超时沿用既有 `--timeout`（缺省 300s）+ `timeout -k 10`；本 change 无写盘操作，故无回滚路径需求。
- **运行 checkout 纪律**：改 `assets/hack/` 下脚本后**必须重跑 `setup.sh`**（拷贝非 symlink），否则新 SKILL 调旧脚本。

## Impact

- `sdflow-init/assets/hack/outside-voice.sh`（bundle 权威源）
- `hack/tests/` 对应测试
- `.github/workflows/mechanical-gates.yml`（A1 需要 Linux 泳道）
- **不触及**：recorder 三脚本、async 字节等值 marker 段内部、`anchor_lint` 矩阵与锚行字段取值域

## Compliance〔D-6〕

| ADR / 边界 | 核对结论 |
|---|---|
| `adr/0005`（dev/runtime checkout 分离） | 遵守：改 `assets/hack/` 后须在开发 checkout 跑 `setup.sh` 才测得到 |
| `adr/0018`（机械校验器输出诚实性） | 遵守：SIGKILL 残余显式登记，**不声称根治** |
| `adr/0021`（可见成本非机械门） | 遵守：截断丢弃字节数写 stderr 属可见成本 |
| 基准 ⑤（无界语法禁手搓） | **UTF-8 是有界语法面**（≤4 字节、continuation 形态确定）⇒ 边界回扫合规，实测 201 切点 0 失败。**禁止演化成通用编码嗅探器**——只认 UTF-8，不做编码检测 |
| 跨产品 / 跨模块共享数据模型边界〔D-6 阻塞条款〕 | **不命中**：本 change 收缩后**不改任何数据契约**（`scan --json` 的 additive 扩展已随 B11/B12 拆出）。原 D-6 声明连同 recorder 内容一并移除 |
