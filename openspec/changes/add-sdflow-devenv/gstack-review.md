<!-- sdflow:step1-broad-review v1 mode="native" -->

# gstack-review — add-sdflow-devenv（Step1 广审 · autoplan 原生执行）

> **native 声明佐证**：autoplan 经 Skill 机制原生执行（其 SKILL.md 指令直接进主 session），非子代理转述模拟。运行痕迹：preamble 已跑（`BRANCH: feat/add-sdflow-devenv` · `SESSION_KIND: interactive` · `CODEX_BIN: codex-cli 0.144.1` · `CODEX_CFG: enabled`）；Phase 0 scope 检测已执行；Phase 1 / Phase 3 双声均为真实调用（Claude subagent 经 Agent 工具、codex 经 `codex exec -s read-only`）。
> **G2 适配**：autoplan 的两处人类门（premise 确认 / 最终批准）**不弹窗**，其自动决策与 taste/challenge 项一并登记进 `spec-review-report.md` 决策区，设计门一次拍板。

## Phase 0 — Scope 检测

| 项 | 判定 |
|---|---|
| **UI scope** | ❌ 否（本 change 不做界面）→ **Phase 2 (Design) skip** |
| **DX scope** | ✅ 是（开发者工具 / AI agent 为主要用户 / 含 CLI 脚本 + SKILL.md） |
| **Codex 可用** | ✅ `codex-cli 0.144.1`，preflight `ready` → 双声全开 |

## 实际执行的相位（诚实登记）

| Phase | 状态 | 声 |
|---|---|---|
| Phase 1 CEO | ✅ 已跑 | Claude subagent（独立，无前序上下文）+ codex |
| Phase 2 Design | ⏭️ skip | 无 UI scope |
| Phase 3 Eng | ✅ 已跑 | Claude subagent（独立，读了真实代码）+ codex |
| Phase 3.5 DX | ⛔ **未跑（显式跳过，非遗漏）** | 见下方跳过判定 |

### ⛔ 跳过判定（显著呈现，不埋进正文）

**Phase 3.5 (DX) 与 Step2 独立镜阵（领域镜 / 对抗镜 / 接地镜）未执行。**

**理由**：CEO + Eng 四声已收敛出 **5 条 CRITICAL 直指三根承重柱**（verify 执行器无归属 · negative control 无法机械分派且会破坏用户环境 · source 行号锚恒真 · 嵌套 YAML 解析无方案 · 跨 skill 并发失效）。设计需**重大返工**——对一份即将被推翻的设计继续加镜是浪费预算。

**接地已覆盖**：Eng 两声均**读了真实代码**（`sad_scaffold.py` / `sad_schema.py` / `init.py`），并据此产出了多条代码事实级 finding（PyYAML 缺失、`chmod 0o644`、锁参数 120s、`inject()` 裸 `open(w)`）——原则 2（接地）已满足，非跳过。

**对抗已覆盖**：CEO / Eng 两轮 prompt 均为对抗式（"证明它会爆炸"）——原则 3（对抗）已满足。

**未覆盖**：DX 视角（skill 的开发者体验：TTHW / 错误信息质量 / 触发词可发现性）· 独立领域镜。

**⇒ 返工后 MUST 重跑完整镜阵**（含 DX + 独立对抗 + 接地）。本次结论建立在 4 声之上，不是完整 8 镜。

---

## Phase 1 — CEO 双声（战略与 scope）

### CEO 共识表

| # | 维度 | Claude | Codex | 共识 |
|---|---|---|---|---|
| 1 | 前提有效？ | ❌ 三条前提全部不成立 | ❌ 同 | **CONFIRMED（否）** |
| 2 | 是对的问题？ | ⚠️ 问题真、**插入点错** | ⚠️ 同（价值在复利面非 day-0） | **CONFIRMED（部分）** |
| 3 | scope 校准正确？ | ❌ 过大，应按证据减 | ❌ 过大，应按垂直结果切 | **CONFIRMED（否）** |
| 4 | 替代方案充分探索？ | ❌ ADR-1 备选是稻草人 | ❌ 定义式排除，无成本对照 | **CONFIRMED（否）** |
| 5 | 竞争/市场风险覆盖？ | N/A（内部工具） | N/A | — |
| 6 | 6 个月轨迹健康？ | ❌ 三项负债 | ❌ 同 | **CONFIRMED（否）** |

**6/6 维度中 4 项 CONFIRMED-否，0 项 DISAGREE。两声高度收敛。**

<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="autoplan-ceo-voice" findings="9" truncated="true" -->

> **CODEX SAYS（CEO — 战略挑战）**：真实调用 `codex exec -s read-only`（codex-cli 0.144.1）。输出经 `tail` 截断（故 `truncated="true"`，可见 9 条，实际更多）。其独立命中：前提三条全不成立 · progressive DoD 无防腐机制（无 owner/deadline/required/CI gate，永久 `scaffolded` 是**默认结果**而非边缘风险）· brownfield relocation 是另一个产品 · negative control 被错误提升为通用真理且执行面不安全 · SM 只证实现自洽不证产品有效 · `path:line-range` 是六个月后最大维护负债 · `verified` 是会过期的事实却被当永久状态 · ADR 否决是定义式排除无成本对照 · 强制人问答 + Makefile 中心主义会拖垮跨项目采用。

### CEO findings

| ID | 严重度 | finding | 证据 | 声 |
|---|---|---|---|---|
| **CEO-1** | **CRITICAL** | **立项证据造假**：proposal 称「命令虚构」是「接地实测暴露」，但其引用的 `06:44` 白纸黑字写「**零虚构 target，行号全中**」。归位场景实测虚构率 = **0**；新建场景**零样本**。一个 greenfield 的**预测风险**被洗成了「实测暴露」，而 ADR-1 的支点正建于此 | `proposal.md:10` vs `06:44` / `05:140` / `07:180` | Claude |
| **CEO-2** | **CRITICAL** | **dogfood 自指坑**：proposal 把「无门禁（`assert-bindings` 无自动触发点）」列为立项理由 #3，而 **`devenv_lint` 自己也没有任何触发点**——全 change 与 `sdflow-done` / `ship_gate` / `sdflow-maintain` 零集成。更致命：R-3（防僵尸文档）的缓解是「lint 每次跑都复述未完成清单」= **一个没人会跑的 lint**。⇒ 前提 (b)「渐进 DoD 不会退化」**结构性不成立** | `proposal.md:10` · `spec.md:193-211` · `design.md:388` | 双声 |
| **CEO-3** | **HIGH** | **「88% 全是待决策项」是伪推论**：被同一份回执的**三分法**证伪（`06:53-60` 已把二分改三分：SAD 投影 / **构建配置投影** / 纯人写）。且真正的纯人写（坑 / 护栏 / 盲区）**day-0 根本问不出来**——坑还没踩。⇒ greenfield 天花板：一个 Makefile + 一张泳道表 + 一张待办清单，**不含回执认定的全部价值** | `proposal.md:12` vs `06:53-60` / `06:38` | Claude |
| **CEO-4** | **HIGH** | **归位模式是硬凑**：ADR-9 的合并理由是「后半段代码共用」= **实现复用**论证，而本仓基准（`change-scope-one-complete-stage-result`）明确「不按同批来源/顺手/共用」定 scope。归位自带独立步骤 ①'、三处置删源、git-clean 门、独立冷审镜、独立 SM——**以及全 skill 唯一不可逆操作（删用户文件）**。且价值分布是反的：归位边际价值最低（手写 prompt 已零虚构做成），新建价值最高但零样本 | `design.md:370-374` · CLAUDE.md 基准 4 | 双声 |
| **CEO-5** | **HIGH** | **`lane-patterns` n=1 过拟合**：五格中三格全来自 mqtt-console，然后拿 mqtt-console「自验 ⇒ 精确复现 6 条泳道 ⇒ **可被证伪，不是拍脑袋**」——**用蒸馏分类法的样本去复现该样本，是过拟合不是证伪**，却被写成可证伪性证据 | `07:412-422` | Claude |
| **CEO-6** | **HIGH** | **上游试点未跑就建下游**：`add-sdflow-architecture` 昨日归档，其 hand-off 明写「**首个真实试点（最高优先）**……SM-4 证伪钟起点」——**该试点未做**。而 devenv 对 SAD 的依赖是硬的（形态四问 ← §3 外边界；`covers` ← §5 contract）。若试点发现真实 SAD 的 §3/§5 不像模板假设，**devenv 的两条高价值投影同时塌方** | `hand-off.md:12,23` · `design.md:54` · `spec.md:26` | Claude |
| **CEO-7** | **HIGH** | **命令真相源认定与回执相左**：`06:44-51` 结论是命令的机械真相源 = **构建配置**（可核验、**甚至可生成**）。R-11 反过来宣布「frontmatter 为唯一机械真相源」⇒ `command` 被重新录入 frontmatter，与 Makefile 并存。**SM-5「零双写」只是把双写搬了个家**（靠 lint ① 对账）。回执自己的方案（解析 Makefile 直接渲染）**压根没有双写，也不需要 lint ①** | `spec.md:213-221` vs `06:44-51,104` | 双声 |
| **CEO-8** | **HIGH** | **`verified` 是会过期的事实，却被当永久状态**：无 `verified_at` / commit SHA / 依赖版本 / 环境指纹 / command hash。状态机承认依赖升级会使其失效，却**无任何自动检测**。⇒ 大量「档案上 verified、现实已坏」的假绿 | `design.md:109,269` · `spec.md:193` | Codex |
| **CEO-9** | **MEDIUM** | **ADR 的否决是定义式排除，无成本对照**：ADR-1 把备选 (a) 表述为「模板 + 手跑 prompt（**没有 lint**）」= **稻草人**。真正的候选是「**已验证的 prompt + 一个有触发点的 `devenv_lint`**」——`06 §4.1` 已把五条机械项精确划定，prompt 已在 mqtt-console 零虚构跑通。**这个组合从未被作为候选评估过**，成本是本计划的零头 | `design.md:317,323` · `06 §4.1` | 双声 |
| **CEO-10** | **MEDIUM** | **6 个月负债清单**：① **双 inject 分叉**（ADR-7 明知 `init.py` 非 fence-aware 却决定「devenv 自己实现一个正确的」⇒ 仓里并存一个对的和一个已知有缺陷的——这是分叉不是复用，违 `point-vs-surface-fix` 基准）② E1–E11 三处投影的永久一致性维护税 ③ 僵尸 scaffolded 文档 ④ `opsx-devenv` marker 债 | `design.md:357-362` | Claude |
| **CEO-11** | **HIGH** | **SM 只能证明实现自洽，不能证明产品有效**：SM-1 以人工归位结果为金标准 = **循环验证**；SM-2 单样例易 bootstrap 假绿；其余全是内部 schema/lint。**缺**：fresh clone 成功率 / 首次跑通耗时 / 人工决策次数 / 漂移率 / negative-control 误判率 / 生成改动被保留的比例 | `proposal.md:24-32` | Codex |

---

## Phase 3 — Eng 双声（架构 / 并发 / 安全 / 测试）

### Eng 共识表

| # | 维度 | Claude | Codex | 共识 |
|---|---|---|---|---|
| 1 | 架构健全？ | ❌ 三根承重柱空心 | ❌ 同 | **CONFIRMED（否）** |
| 2 | 测试覆盖充分？ | ❌ 最危险代码零覆盖 | ❌ 同 | **CONFIRMED（否）** |
| 3 | 性能风险已处理？ | ⚠️ 锁参数与长跑 smoke 冲突 | ⚠️ 同 | **CONFIRMED（否）** |
| 4 | 安全威胁已覆盖？ | ❌ 停服务无恢复 + secret 进 git | ❌ 同 | **CONFIRMED（否）** |
| 5 | 错误路径已处理？ | ❌ 失败表漏 9 项 | ❌ 同 | **CONFIRMED（否）** |
| 6 | 部署风险可控？ | ⚠️ YAML 解析无方案 | ⚠️ 同 | **CONFIRMED（否）** |

**6/6 全部 CONFIRMED-否，0 DISAGREE。两声完全收敛。**

<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="autoplan-eng-voice" findings="10" truncated="true" -->

> **CODEX SAYS（Eng — 架构挑战）**：真实调用 `codex exec -s read-only`，**读了它宣称复用的真实实现**（`sad_scaffold.py` / `init.py`）。输出经 `tail` 截断（可见 10 条）。其独立命中（与 Claude Eng 声高度收敛）：锁未记 owner UUID（A 释放可删 B 的锁）· **单文件原子写 ≠ 整个 workflow 原子**（写代码/写状态/append log/render/inject 是多个独立提交点，任一崩溃留下半完成仓库；需 write-ahead journal，**不要拿审计 log 当控制流真相源**）· `source: Makefile:11-14` 是错误的稳定标识 · **执行与 `verified` 迁移无可信耦合**（禁 `set-lane --status verified`，只允许 `verify-lane` 亲自执行并原子写 evidence）· negative control 的「红」可能是无关失败（需 dependency-specific expected-failure predicate，**普通非零不能通过**）· **timeout 不杀进程树**（需 process group + TERM→KILL + cleanup ledger）· clean worktree 不足以保护 brownfield 删除（需 HEAD 有效 / tracked / 非 submodule / 非 symlink / digest 一致 + 可恢复 patch）· **fence-aware 仍不足**（CommonMark 还有 `~~~`、四 backtick、缩进 fence；孤儿/逆序/交错 token 未定义）· 追加异构结构文件不是通用机械动作（需 per-adapter + 解析后重新验证，如 `make -n` / `docker compose config`）· 测试图未覆盖取消/信号/子进程残留/磁盘满/非 UTF-8/半提交恢复。

### Eng findings

| ID | 严重度 | finding | 证据 | 声 |
|---|---|---|---|---|
| **ENG-1** | **CRITICAL** | **`verified` 的执行器无归属 —— ADR-4 整条链是空的**：`devenv_scaffold.py` 子命令（`init`/`set-lane`/`render`/`inject`/`log`/`doctor-gen`）**无一个会执行 smoke**。实际流只能是「模型跑 → 模型读 exit code → 模型调 `set-lane --status verified`」⇒ 脚本对「跑没跑、绿没绿」**零独立证据**。「脚本执行验证」退化为「**模型自称，脚本盖章**」——正是 ADR-4 要防的。tasks 4.2「实现双向判据执行器」是一张**悬空的票**（没说住在哪个脚本，不在组件清单） | `design.md:36,102` · `spec.md:78` · `tasks.md:36` | **双声** |
| **ENG-2** | **CRITICAL** | **`deps` 是裸字符串 ⇒ negative control 无法机械分派**：Q-4 说「按 deps 类型分派」，但 `deps: [<name>]` **里根本没有类型**。给定 `["mosquitto"]`，执行器无从知道它是 compose 服务 / brew service / testcontainer ⇒ 只能猜，或回去问模型 ⇒ **「机械分派」变回模型判断**。同一个洞炸掉另一条 MUST：lane **无 `kind` 字段** ⇒ 「真硬件泳道 MUST NOT 执行」（spec.md:107）**无法机械识别**，只能靠模型自觉——而它防的恰恰是模型把烧板命令跑起来 | `design.md:89,408` · `spec.md:107` | Claude |
| **ENG-3** | **CRITICAL** | **抽依赖会停用户正在用的服务，且全程无恢复保证**：① **11 条失败模式表无一条说「MUST 恢复」**——smoke 超时 / 脚本崩溃 / Ctrl-C ⇒ 依赖**永久停在停止态**，skill 转头去跑下一条泳道 ② macOS 上 mosquitto 常是用户 `brew services` 起的**自己的开发 broker**，可能正被别的终端用着 ③ design 有明确护栏「MUST NOT 替操作者装依赖（副作用不可逆）」——**但装是加法，停是减法，后者更破坏性却无对称护栏** ④ 两条泳道共用 broker 时，给 A 做 negative run 会让 B 的正向跑拿到**虚假的红**；并发节只管**文件写**，完全没有「机器上的服务状态」这层共享资源 | `design.md:261-275,293,408,241-255` | **双声** |
| **ENG-4** | **HIGH** | **`source: "Makefile:11-14"` + 「查那行存不存在」= 对任何长度 ≥14 行的文件恒真 = 设计好的假绿**：用户在 Makefile 顶部插三行 ⇒ 11-14 行现在指向完全不同的 target ⇒ **lint 全绿、`verified` 保持、命令表继续声称出自那四行**。Scenario 只覆盖「行已不存在」（罕见），**不覆盖「行还在、内容变了」（必然）**。而这套锚是 SM-5「零双写」的全部依据 | `design.md:347` · `spec.md:127,195,201-203` | **双声** |
| **ENG-5** | **HIGH** | **嵌套 `lanes[]` 的 YAML 解析/序列化根本没有方案（会吃掉整个实现预算）**：核验——本机 `import yaml` **失败**（无 PyYAML，本仓无 requirements.txt/pyproject，skill 靠 symlink 直接跑、无依赖安装环节）；唯一先例 `sad_schema.parse_frontmatter` 是**手搓扁平标量解析器**（固定键白名单 + 枚举，无列表、无引号处理）；写侧 `_rewrite_top_key` 是**行级正则改写**——这套手法在 `lanes[]`（8 键 × 含列表 × 含中文自由文本 × 含带冒号的值）上**完全用不了**。tasks 1.2 对「用什么解析 YAML」**只字未提** | `design.md:79-93` · `tasks.md:9` · `sad_schema.py:111-158` · `sad_scaffold.py:453-488` · 本机 `import yaml` 失败 | Claude |
| **ENG-6** | **HIGH** | **跨 skill 并发：锁名不同 = 互斥域不相交**：devenv 用 `.devenv-scaffold.lock`，sad 用 `.sad-scaffold.lock`——**两把不同的锁**。但写入面**重叠**（都注入 CLAUDE/AGENTS/README/INDEX）。核验 `init.py:126`：其 inject 是**裸 `open(path,"w")` 全量覆写，无锁、无原子写** ⇒ devenv 注入 ‖ `/sdflow-init update` 覆写同一文件 ⇒ **devenv 的整块注入被静默吃掉**。「复用已验证机制」≠「**互斥性可组合**」，这层被措辞掩盖 | `design.md:245,249` · `init.py:126` | Claude |
| **ENG-7** | **HIGH** | **人门 diff 在执行之后 —— 模型生成的代码先跑后审**：时序是「写落地物 → 跑 smoke → … → 人门（含 diff 过目）」。**模型刚写的 recipe body 和 smoke 源码，在任何人看过一眼之前就已经被执行了**。步骤 ③ 的「跑前列命令给人过目」给人看的是 `make integration` 这**一行调用**——对「target 里到底跑什么」提供**零信息量**，人只能橡皮图章。且**人门否决 diff 时无撤销路径**（落地物已落盘且已执行） | `design.md:221-236,293,295` · `spec.md:183` | Claude |
| **ENG-8** | **HIGH** | **exit code 是唯一信号 ⇒「绿」的定义太弱；negative control 只证「命令耦合依赖」，不证「断言有效」**：`go test` 无匹配测试 → exit 0；pytest 全 skip → exit 0；recipe 是 `@echo TODO` → exit 0。更狠的是**方向反了的那类**：抽依赖后的红可能来自 **session-scope fixture 连不上 broker 直接 error**，于是 **smoke body 写 `assert True` 照样能拿到「正向绿 + 反向红」→ 被判 verified**。且 **testcontainers / 内嵌 fallback**（Go/Node 生态**主流**写法）对 `docker compose stop` 完全免疫 ⇒ **永久误判 vacuous**。proposal「把 vacuous 从纯语义降为两级机械」**这个断言过强** | `design.md:263-268,338-341,386` · `proposal.md:19` | **双声** |
| **ENG-9** | **HIGH** | **`deps: []` 是危险逃生口**：一条被误判 vacuous 的泳道，操作者最省力的出路就是**清空 `deps`** ⇒ negative control 整个消失 ⇒ **把假阴性换成了真·假绿**。且删 deps 会连带毁掉 doctor 和依赖清单 | `design.md:386` · `spec.md:86` | Claude |
| **ENG-10** | **HIGH** | **锁参数与长跑 smoke 直接冲突**：`sad_scaffold` 的锁是为**亚秒级**调的（`LOCK_STALE_SEC=120`）。若锁跨 smoke 持有（集成测试跑几分钟很正常）⇒ **并发 session 把活锁判成残留锁** → 提示用户「删锁重试」→ 用户照做 → **两 session 同时写**。**陈旧锁检测从保护变成攻击面**。若锁只包单次 `set-lane`（正确），则真正的临界区**跨越多次进程调用**（模型：读 lanes → 跑 smoke → 写 status）⇒ 经典 **lost update**，而 tasks 2.5 的测试「两进程并发 set-lane 不丢更新」**恰好只测那个不会出事的场景** | `sad_scaffold.py:39-41` · `design.md:217-236,252` · `tasks.md:20` | Claude |
| **ENG-11** | **HIGH** | **「追加者」抽象在 package.json / CI YAML 上不成立**：往 `package.json` 的 `scripts` 加一条 = **JSON 结构化读-改-写**（且 `package.json:11-14` 这种行号锚对 JSON 毫无意义）；往 `ci.yml` 加 step = **YAML 结构化编辑**（缩进敏感、注释保留）。三种入口（Makefile=行文本 / package.json=JSON / ci.yml=YAML）被一个「追加 + 行号锚」抽象一起盖住，**其中两种根本不适用** ⇒ 实现期要么现场发明三套语义（scope 爆炸），要么**悄悄只支持 Makefile**（Node/Rust 消费仓直接不可用） | `spec.md:131` · `design.md:68,88,267` | Claude |
| **ENG-12** | **MEDIUM-HIGH** | **secret 随命令输出进 committed 文件**：design 断言「不外发任何内容 ⇒ **无 secret 出境面**」——只看了「模型主动发出去」这条路，**漏了 ingress → git**：命令继承 agent session 的**完整环境变量**，失败命令回显 `AMQP_URL=amqp://user:pass@host` → 写进 `blocked_by` / `devenv-log.md` → **commit → push**。「不主动外发」但**把 secret 写进了必然被外发的载体** | `design.md:297,263-268,281` | Claude |
| **ENG-13** | **MEDIUM** | **`chmod 0o644` ⇒ 生成的脚本不可执行**：计划说「照抄已验证模式」，而 `sad_scaffold.py:78` 硬编码 `os.chmod(tmpname, 0o644)`（它只写 .md）。devenv 要生成 **doctor / broker 启停 / CI 脚本** ⇒ **落盘即不可执行** → `make integration` 调 `./hack/broker-up.sh` 直接 permission denied。**更阴**：这个失败发生在 smoke 阶段，被记成 `blocked_by="permission denied"` ⇒ **skill 自己写坏的东西，被它自己记成「环境问题」** | `sad_scaffold.py:78` · `design.md:36,69-71,245` | Claude |
| **ENG-14** | **MEDIUM** | **Makefile 追加三炸点**：① **无尾换行** → append 把新 target 粘在上一行尾 ⇒ **静默损坏用户 Makefile** ② **Tab**：recipe 必须字面 tab，模型生成空格缩进 → `missing separator` ③ **TOCTOU**：「追加前扫描已有 target 名」与 append 之间**没说要在同一把锁内**；且锁域声明**只点名三个 .md 文件，Makefile/CI/README 的追加根本不在锁域里** | `design.md:249-253,267` · `spec.md:249` | Claude |
| **ENG-15** | **MEDIUM** | **失败模式表漏 9 项**：抽依赖后未恢复 · 超时只杀父进程（`docker compose up` 孤儿容器继续占端口 → 下条泳道拿到假的「端口占用」）· 写坏用户 Makefile · secret 落 committed 文件 · 跨 skill 并发覆写 · **SAD 处于 `draft` 态**（devenv 只判 `present\|missing`，把 draft SAD 当 validated 用 ⇒ `covers` 锚到一批即将改名的 contract）· `sad: missing` 之后 SAD 被补上（**无再升级路径**，covers 对账**永久跳过**）· 人门否决 diff 无撤销 · **`verified` 泳道残留旧 `blocked_by`**（绿泳道上挂着「本机无 mosquitto」⇒ 文档在说谎） | `design.md:261-275` | Claude |
| **ENG-16** | **MEDIUM** | **两处「机械/语义」错标**：① F5 写「重名**且语义不符**」→「**脚本**报冲突」——脚本能判的只有**名字撞了**，「语义符不符」**没有确定性信号**，是模型判断。按 CLAUDE.md 切分判据应改为：**脚本对任何重名一律 fail-closed**，由模型 + 人决定「登记复用」还是「改名追加」 ② 冷审「诚实镜」要求查「`planned` 是否被伪装成 `verified`」——但 frontmatter 里**没有任何执行证据**（无 exit code / 时间戳 / neg_strategy），冷审只能读文件 ⇒ **这面镜子现在是空转的** | `design.md:267` · `spec.md:179` | Claude |
| **ENG-17** | **MEDIUM** | **测试覆盖图：最危险的代码零覆盖，最会腐烂的用例不可复现**：① **发出 `docker compose stop` 的那段代码**（本 skill 破坏性最强的部分）**一条测试都没有** ② **没有任何测试断言「模型不能直接 `set-lane --status verified`」**——而 ENG-1 的整个修法挂在这条上 ③ lint ① 的测试**测了但测不到真问题**（按现规格能造的坏输入只有「文件变短」，而最常见的失效「行还在内容变了」**在规格里就不是坏输入**）④ SM-1 靠 mqtt-console 副本 + 人工比对 ⇒ **跑一次之后永不再跑**，归位模式此后**零回归** ⑤ fence-aware 用**活语料**（本仓当前内容）当 fixture ⇒ 文件一改测试悄悄不再测那个场景 | `tasks.md:88-118,83,100-101` | 双声 |

---

## Cross-Phase 主题（2+ 相位独立命中 = 高置信信号）

| 主题 | 命中相位 | 说明 |
|---|---|---|
| **「机械」实为「模型自称」** | CEO（无门禁的 lint）+ Eng（ENG-1 verify 执行器无归属、ENG-16 冷审镜空转） | 全计划最系统性的病：**多处宣称机械保证，实际无独立证据** |
| **假绿的三种形态** | CEO（CEO-8 verified 过期）+ Eng（ENG-4 行号恒真、ENG-8 exit code 太弱） | 三条独立路径都通向「档案上绿、现实已坏」 |
| **不可逆操作缺护栏** | CEO（CEO-4 删用户文件）+ Eng（ENG-3 停用户服务无恢复） | 两个最危险的操作，**都在零验证的 v1 里，都缺对称护栏** |
| **scope 过大** | CEO（双声）+ Eng（承重柱空心 ⇒ 更该收窄） | 两相位独立得出「按证据减」的同一结论 |
