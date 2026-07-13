# tasks — add-sdflow-devenv

> 〔spec-review-amendment · round-2 · 2026-07-13〕本表已按 round-2 设计门（5 项拍板 + 45 条 canonical finding）**整体重写**。
> 前一版围绕 negative control / 门槛①② / `isolate` / `predicate` 的任务组**已作废**（见 `design.md` ADR-0/ADR-4）。原表见 git 历史。
> Requirement 追溯：`R-*` = `specs/devenv-provisioning/spec.md`；`A-1` = `specs/architecture-design/spec.md`；`M-1` = `specs/maintain-scan/spec.md`。
> 纪律：改 `scripts/` 必跑 `tests/`。复选框在 `/sdflow-done` 的 archive 阶段勾——**实现期 MUST NOT 勾**。

## 0. ⭐ 实现前置（设计门 Q2，MUST 先于第 1 组）

- [ ] 0.1 **跑 `sdflow-architecture` 的首个真实试点**——用本来要做 SM-3 的**同一个绿地项目**（上游 hand-off 自己写下的最高优先 next action，至今未做）
- [ ] 0.2 据试点结果核验四条经验前提，**结论回写 proposal**：① 真实 SAD 的 §3/§5 **能否长出** devenv 需要的锚 ② greenfield 的**「命令虚构」风险是否真实存在** ③ `lane-patterns` 五格在**第二个样本**上是否还成立（A-2 的 n=1 过拟合）④ **⭐ 模型能否为三层各自提出像样的验证方法**（A-8——**这是 ADR-0/ADR-4 整条路线的前提**）
- [ ] 0.3 若 ① 或 ④ 证伪 → **暂停本 change**，回 design 重议

## 1. 骨架与 schema

- [ ] 1.1 建 `sdflow-devenv/` 目录骨架（`SKILL.md` + `scripts/` + `references/` + `tests/`）
- [ ] 1.2 `scripts/devenv_schema.py`：**`.devenv-lanes.json` schema**（标准库 `json`，**零第三方依赖**）——lane 含 `id` / `layer`（unit\|integration\|e2e）/ `kind` / `status` / **`verification{method,executor,strength,evidence}`** / `source{file,kind,selector,digest}` / `smoke` / `deps[{name,kind,owned_by}]` / `covers` / `blocked_by`〔R-数据落 JSON〕
- [ ] 1.3 **`schema_version` 的消费行为**（**MUST NOT 只是留个位**）：缺失 → fail-closed；**高于本实现已知版本 → fail-closed**「skill 版本过旧，请升级」，**MUST NOT 尽力解析**〔R-数据落 JSON〕
- [ ] 1.4 schema 单测：无 PyYAML 环境正常读写 · 非法枚举 · `id` 重复 · **`schema_version` 缺失/未来值双向 fail-closed**

## 2. 机械层基座（并发 · 原子写 · 留痕）—— **面治：三条腿一起改**

- [ ] 2.1 **`openspec/` 写域单一锁**（`openspec/.sdflow-write.lock`，三 skill 共用）——`os.open(O_CREAT|O_EXCL)` 跨平台；锁文件记 **owner（UUID+PID+ts）**，释放前**核对 owner**，MUST NOT 删他人的锁〔R-并发〕
- [ ] 2.2 **腿 2：`sdflow-init/scripts/init.py` 的 `inject()` 补锁 + 原子写**（现为裸 `open(w)`，无锁无原子写 ⇒ 会静默吃掉 devenv 的注入）〔R-并发 · 面治〕
- [ ] 2.3 **⭐ 腿 3：`sdflow-architecture/scripts/sad_scaffold.py` 迁到共用锁**（现用 `.sad-scaffold.lock` 是**另一把锁**）+ **补 owner 核对**（现释放时不核 owner，`sad_scaffold.py:135`）——**前一版漏了这条腿，「三 skill 共锁」只有两条**〔codex 接地实证〕
- [ ] 2.4 **`atomic_write(path, text, mode=0o644)`**：`mkstemp` 唯一 tmp 名 + `os.replace`；**脚本类落地物传 `0o755`**（原 `sad_scaffold` 硬编码 0644 ⇒ 生成的 doctor 脚本**落盘即不可执行**）；覆盖既有文件时**保留原 mode**
- [ ] 2.5 **锁短持有**：MUST NOT 跨验证执行持有（`LOCK_STALE_SEC=120` vs 验证数分钟 ⇒ **活锁被判残留锁** ⇒ 提示删锁 ⇒ 两 session 同写）〔R-并发〕
- [ ] 2.6 **⭐ CAS 覆盖全部验证输入快照**（**不只 `status`**）：`verify-lane`/`confirm-lane` 读取时对 `status`+`method`+`source`+`smoke`+`deps` 取快照 digest，回写时**在锁内**重读比对，不一致 → 拒绝。**仅比对 `status` 会让旧验证给新命令盖章**（长跑期间另一 session 改了 `method` 而 `status` 未变）〔R-并发 · codex〕
- [ ] 2.7 **退出码一码一义** + 提供覆盖全部子命令的**退出码表**——不同失败原因（非法调用 / lane 不存在 / CAS 冲突 / 锁被占）MUST 有不同码；**MUST NOT** 让调用者退回解析 stderr 文本〔R-并发〕
- [ ] 2.8 `log` 子命令：append-only；`--line` 含换行符 → 拒绝
- [ ] 2.9 并发测试：**三 skill 两两并发不丢注入**（devenv‖init · devenv‖architecture · init‖architecture）· A 释放不删 B 的锁 · **CAS 拒绝陈旧回写（改 `method` 而非 `status`）** · 长跑期间锁未被持有

## 3. scaffold 子命令

- [ ] 3.1 `init`：preflight（无 `openspec/` → exit 3）+ **SAD 缺失显式降级**（写 `sad: missing`，MUST NOT 佯装）+ exit 4（continue/replan）+ 存量素材检出 → 归位模式〔R-preflight〕
- [ ] 3.2 `set-lane`：**只管 `planned` / `scaffolded` 两态**；`scaffolded` ⇒ `blocked_by` 非空；**`--status verified` 一律拒绝（exit 5）**〔R-执行者分工〕
- [ ] 3.3 `render`：从 `.devenv-lanes.json` 渲染命令表（`DO NOT EDIT` banner）；**行号动态生成供阅读、不作真相**
- [ ] 3.4 `inject`：`opsx-devenv` marker 幂等注入；MUST NOT 写 `opsx-init` 区块
- [ ] 3.5 **`inject` 实现 fence-aware**——MUST NOT 照抄 `init.py`（其 `:49-52` 注释明示非 fence-aware）。覆盖 CommonMark 全部 fence 变体（` ``` ` / `~~~` / 四 backtick / 缩进 fence）；孤儿 / 逆序 / 交错 → **fail-closed 报位置**
- [ ] 3.6 **`source` digest 锚**：按 `selector` 用 parser 重定位 target，比对 recipe digest；**MUST NOT 用行号存在性**（对任何长度 ≥N 的文件恒真 = 假绿）
- [ ] 3.7 **digest 的规范化规则**（**MUST 明确定义，不留给实现现场发挥**）：剥行首/行尾空白 + 纯空行；**MUST 保留 tab 缩进**（Make recipe 的 tab 有语法意义）；**MUST NOT 剥注释**〔R-数据落 JSON〕
- [ ] 3.8 **`append_makefile_target()`**：锁内「读 → 扫 target 名 → 补尾换行 → 以 tab 拼 recipe → 原子写」；**重名 → fail-closed**（脚本**只判名字碰撞**，**语义符不符归模型+人**，MUST NOT 假装机械）
- [ ] 3.9 **`doctor-gen` 子命令**：生成依赖自查脚本（`0o755`）+ 安装命令清单——**MUST NOT 替操作者安装**（R7 的落点；前一版 tasks 漏了此任务）
- [ ] 3.10 scaffold 测试：各退出码 · **`set-lane --status verified` 被拒** · render 幂等 · **inject 在含 marker 演示的 fence 语料上不劫持**（checkin **固定 fixture**，**MUST NOT 拿本仓活语料当 fixture**）· Makefile 追加三炸点 · **digest 规范化：改注释/改 tab 的行为符合规则**

## 4. 验证：两条通道（`verified` 的唯一产出者）

- [ ] 4.1 **`verify-lane` 子命令**（`executor: script` 通道）：脚本**自己 fork** 执行 `verification.method` 声明的命令，捕获 exit / 时长 / 输出摘要，**自行决定**写 `verified` 还是 `scaffolded+blocked_by`〔R-执行者分工〕
- [ ] 4.2 **`confirm-lane` 子命令**（`executor: human` 通道）：**只能从人门流程调用**，写入人确认的证据（`confirmed_what`）。**模型 MUST NOT 代替操作者调用**〔R-执行者分工〕
- [ ] 4.3 **执行证据原子落盘**：`at` / `at_commit`（HEAD SHA）/ `exit` / `output_digest` / **`method_digest`**——**无证据则冷审「诚实镜」在数据上无从查证**〔R-执行者分工〕
- [ ] 4.4 **⭐ `method_digest` 覆盖验证真正依赖的全部内容**：验证命令（**含 recipe body 展开**）+ smoke + **smoke 可达的 harness/fixture** + 依赖引用的外部文件（compose.yml）+ **lockfile**。**MUST NOT 只摘命令字符串**——改 fixture 让断言失效是 vacuous 的主要引入路径，只摘命令则纹丝不动〔codex〕
- [ ] 4.5 **⭐ `owned_by` 派生（非声明）**：只有**本次运行内 skill 自己调用过启动命令**的依赖才记 `skill`；**此前已在运行的一律 `operator`**。`owned_by: operator` → **MUST NOT stop**。**若 `owned_by` 是模型自填的裸声明，R1 红线的全部效力压在一个无独立信号的字段上**〔R-执行边界 · 对抗镜〕
- [ ] 4.6 **恢复保证**：改变机器状态的验证方案 `try/finally` 恢复；**超时 / SIGINT / 异常下恢复仍执行**；**恢复失败 = 独立失败状态**（响亮报告 + 写 devenv-log），不能只写普通 `blocked_by`
- [ ] 4.7 **超时杀进程树**：`start_new_session=True` + TERM→KILL 整棵进程组；默认超时 **300s，可按 lane 覆盖**，**实际用值写进 evidence**（便于事后复核"是不是超时太短误杀"）
- [ ] 4.8 **⭐ cleanup ledger 落盘**（`.devenv-cleanup.ledger`）：**资源创建成功后立即写入**（非函数返回时才写）——否则脚本被 **`SIGKILL`** 时 ledger 随进程蒸发，而 R3 要防的**正是**这种场景（`finally`/`SIGINT`/`SIGTERM` 对 SIGKILL 全部无效）。**skill 每次启动先扫描遗留条目**并回收或响亮报告〔对抗镜〕
- [ ] 4.9 **⭐ 最小环境 allowlist**（**主护栏**，取代"事后打码"）：子进程环境由 allowlist 构造（`PATH`/`HOME`/lane 显式声明的变量），**MUST NOT 继承 agent 的完整环境**——被执行的 recipe 或其下游脚本可把凭证**写进文件、发往网络**，**事后打码管不着**。落盘输出**额外**截断 + secret 正则打码，但 **MUST 标注为 best-effort、非保证**，并登记正则的已知盲区〔codex〕
- [ ] 4.10 **`kind: hardware` → `verify-lane` refuse** → 该泳道走 `executor: human`（指向 `embedded-test-sop`）。**诚实边界**：`kind` 无独立信号，**MUST NOT 佯装纯机械识别**，同时进 ③-pre 人门分类清单
- [ ] 4.11 **非 POSIX → `verify-lane` refuse**（ADR-11）：显式告知"本平台进程树杀灭未经验证，不做无证据的执行"，走 `executor: human`。**MUST NOT** 写一段从未在该平台执行过的代码〔R-执行边界〕
- [ ] 4.12 验证测试：**注入异常 → 断言恢复被调用** · `owned_by` 派生正确（预先在跑的 → `operator` → 拒停）· **`SIGKILL` 后下次启动扫到 ledger 并回收** · **子进程 env 不含 allowlist 外的变量** · 超时杀进程树（孤儿容器被回收）· **`set-lane --status verified` 被拒** · `confirm-lane` 落人门证据

## 5. lint 与其触发点

- [ ] 5.1 `devenv_lint.py` 诚实检查（**只查诚实，不查质量**）：① **`verification.method` 非空**（不允许"不知道怎么验"的泳道）② 状态与证据匹配 ③ **测试三层框架完整性** ④ **三层状态的强制附带项** ⑤ source digest 一致性（非行号）⑥ 指针不悬空 ⑦ 删源残留引用（**排除 `.devenv-backup/`**）⑧ 入口复述检测〔R-机械 lint〕
- [ ] 5.2 **⭐ 三层框架完整性检查**：`testing-strategy.md` 的 **unit/integration/e2e × 五槽**逐一存在且非空 → 缺任一 **fail-closed**〔R-测试策略框架〕
- [ ] 5.3 **⭐ 三层状态的强制附带项**：`不适用` ⇒ **必须有后果**（只写 `N/A` → 报错）· `人工` ⇒ **必须有"用户怎么做"**（只写「人工测试」→ 报错）· `已实现` ⇒ **`lanes[]` 中必须有对应泳道**（声称已实现却无泳道 = 文档在说谎）〔R-测试策略框架〕
- [ ] 5.4 诚实性断言：`verified` ⇒ 证据齐全未失效 ∧ **`blocked_by` 为空**（绿泳道挂着「本机无 X」= 文档说谎）；`scaffolded` ⇒ `blocked_by` 非空 ∧ **含可辨认的修复指引**（`TODO` → 报警）〔R-泳道三态 · DX〕
- [ ] 5.5 诚实通过码 `structure-ok-SEMANTICS-UNCHECKED` + lint 断言**带 E 编号注释**（scope-check 可机械核对）
- [ ] 5.6 **⭐ `sdflow-maintain` 集成**（`devenv_lint` 的**唯一触发点**）：其扫描调用 `devenv_lint`，报告未 verified 泳道 / 失效证据 / 空或敷衍的 `blocked_by`；无 `environments.md` → 跳过；`devenv_lint` 不可用 → **显式提示不静默**。**注**：maintain 现为四类**硬编码**扫描、**无插件挂点** ⇒ 本任务是**新增代码**〔M-1 · Q6〕
- [ ] 5.7 lint 测试：各条造坏输入 fail-closed · **「行还在、内容变了」被抓** · **三层缺一层被抓** · **`不适用` 未记后果被抓** · **`已实现` 无对应泳道被抓** · `blocked_by: TODO` 被抓 · `planned` 不误报

## 6. references

- [ ] 6.1 `quality-criteria.md`：E 判据全集 + 拆解表（三处投影唯一真相源）
- [ ] 6.2 `lane-patterns.md`：依赖形态四问 + 五格阶梯**判据**（非规格）+ 最小可用集 + 参考实例（标「实例，非规格」）+ 未覆盖形态兜底
- [ ] 6.3 **⭐ `verification-patterns.md`**（新增）：验证方法**参考实例**（标「实例，非规格」）+ **已知负面知识**——① **轮询式连接观测对瞬时连接漏检率 100%**（round-2 实验：5/5 全漏，把真穿过依赖的好 smoke 误判 vacuous）⇒ **不可作为判据** ② **proxy 计数零漏检但适用面 ⊆「skill 能控制依赖启动」** ③ **negative control 只证"耦合"不证"断言有效"，且对 testcontainers / 依赖内嵌 recipe 失效** ④ **`assert True` 任何外部插桩都堵不住**（要堵只有变异测试）〔R-验证方法〕
- [ ] 6.4 `boundary-rules.md`：切线表 + 归属判据 + 删源三处置 + `grep` 引用面判据
- [ ] 6.5 **`testing-strategy-template.md`**：**三层 × 五槽**强制框架（含 `不适用`/`人工`/`已实现` 三态的附带项模板）+ `environments-template.md`（十六槽）
- [ ] 6.6 `review-lenses.md`：冷审镜单——覆盖镜 / **⭐ 验证方法镜**（模型提的方法是否名副其实：强度有无夸大、盲区有无如实说出）/ **⭐ 分类镜**（`kind`/`owned_by`/`layer` 是否属实——**这些无独立信号却是机械层的输入，必须有一镜专查**）/ vacuous 镜 / 边界镜 / 诚实镜 / 删源镜；条目带 E 编号

## 7. SKILL.md 编排

- [ ] 7.1 frontmatter：`description` 含与 init 的分流判据句 + 两条前置声明
- [ ] 7.2 起手 A：preflight + 三模式分流 + SAD 降级话术
- [ ] 7.3 步骤 ①：事实采集 + **时序纪律**（先问后记，禁预填）+ **SAD 投影事实批量呈现一次确认**（MUST NOT 逐条问——那是把架构阶段问过的话再问一遍）〔R-事实采集 · DX〕
- [ ] 7.4 步骤 ①'（归位）：盘点 → 判归属 → **搬运表先确认** + 删源三处置 + **显著呈现「以下 N 个文件将被删除」**
- [ ] 7.5 **⭐ 删源护栏**：入口**一次性** `git status` 干净检查（manifest 写入**不重触发**）；逐文件校验 **HEAD 有效 / 已 tracked / 非 submodule / 非 symlink / digest 与人门确认时一致**；**backup manifest 入 git**（`.devenv-backup/`，**MUST NOT gitignore**——"可恢复"必须跨机器成立）；残留引用扫描**排除该目录**〔R-删源护栏 · codex〕
- [ ] 7.6 **⭐ 步骤 ②：测试三层框架 + 泳道 + 验证方法拍板**——三层各答五槽（模型研究推荐，人拍板）；泳道按依赖形态四问；**验证方法由模型提出（含强度与盲区自陈），人确认**〔R-测试策略框架 · R-验证方法〕
- [ ] 7.7 步骤 ③：落地物追加（追加者非拥有者；**v1 只支持行文本型入口**，CI **只生成独立新文件**，`package.json` 走 **Makefile 薄壳**）+ 归位模式 smoke **复用已有测试**
- [ ] 7.8 **⭐ touched-files 事务清单**：写入任何落地物**之前**记录（路径 · **原先是否存在** · 原内容 digest · 原 mode）〔R-③-pre 回退〕
- [ ] 7.9 **⭐ 步骤 ③-pre 人门（执行任何验证之前）**：① 新写落地物 diff 全文（recipe body + smoke）② **验证方法逐条确认**（含强度与盲区）③ **依赖分类清单过目**（`kind`/`owned_by`/`executor`——无独立信号，必须人看）④ 命令清单（recipe 展开）⑤ 「将改变机器状态」显著呈现。**呈现分级**：新写的全文展示；**仅登记的既有 target 只展示登记映射**（MUST NOT 要求人重读他自己写的、skill 不会改的代码）。**用人话，MUST NOT 直接抛内部字段名**〔R-冷审与人门 · DX〕
- [ ] 7.10 **⭐ ③-pre 否决 → 按 touched-files 清单逐项回退**：原先存在的 → 复原；**原先不存在的 → 删除**。**MUST NOT** 用 `git checkout --`（对 untracked **无效**，而"新写 smoke"是**主路径**）或**无路径限定的 `git clean`**（会误删操作者未 `git add` 的其他文件）〔R-③-pre 回退 · 对抗镜 · codex〕
- [ ] 7.11 步骤 ④：冷审（**MUST fresh 子代理**；宿主无原语 → 显式降级响亮留痕）+ 人门④（泳道复核 / 未 verified 逐条确认 / N/A 槽 / **`executor: human` 泳道 → `confirm-lane`** / **删源清单单独拎出**，不与常规议程同级）
- [ ] 7.12 步骤 ⑤：render + inject + **收尾逐条列出未 verified 泳道 + 整体判定 + 下一步怎么调用**（MUST NOT 让操作者猜）〔DX〕
- [ ] 7.13 留痕总则 + 状态迁移速查 + 模型档位（全强档）

## 8. 上下游 skill 改动

- [ ] 8.1 `sdflow-architecture/SKILL.md`：交棒话术改为**指向 `/sdflow-devenv`**（保留「不代写」边界 + 继续给 SAD 锚）+ description 加**过程轴分流句**〔A-1〕
- [ ] 8.2 **⭐ `sdflow-init/SKILL.md` description 加反向排除句**（「不管理项目的 dev/test 运行环境 / 依赖 / CI —— 那部分 → `/sdflow-devenv`」）——**词面碰撞（"初始化环境"）是双向的，只补一边不解决路由**〔R-触发分工 · DX〕
- [ ] 8.3 `sdflow-maintain`：见 5.6（**同一件事，此处不重复列**——前一版 5.5 与 8.3 重复描述）

## 9. 仓级集成

- [ ] 9.1 更新 `README.md` Skills 列表
- [ ] 9.2 更新 `CLAUDE.md`「两类 skill」分类（devenv 归数据类）
- [ ] 9.3 跑 `bash setup.sh` 验证双宿主装载

## 10. 验收

- [ ] 10.1 **SM-5**：`pytest sdflow-devenv/tests/` 全绿；lint 坏输入全 fail-closed；`set-lane --status verified` 被拒；`verification.method` 为空被拒
- [ ] 10.2 **⭐ SM-1（三层框架无留白）**：任一项目跑完，三层 × 五槽全部有内容；`不适用` 有后果 · `人工` 有步骤 · `已实现` 有对应泳道
- [ ] 10.3 **SM-3（新建）**：绿地项目产出完整三层框架 + ≥1 条 `verified` 泳道（`script` 或 `human` 均可）+ 待建清单。**诚实边界：零代码 greenfield 的 `verified` 数可为 0**，达标线为「三层框架完整 + 泳道表 + 待建清单」；**MUST NOT** 为凑 `verified` 造空跑测试
- [ ] 10.4 **SM-2（归位）**：在 **checkin 的 brownfield fixture** 上跑，删源集与搬运结果**确定性断言**
- [ ] 10.5 **SM-6**：digest 锚生效——造「行还在、内容变了」的坏输入被抓
- [ ] 10.6 **SM-4**：`sdflow-maintain` 扫描中 `devenv_lint` **被自动调用**，并在真实回归（`method_digest` 失配）上拦下
- [ ] 10.7 **SM-7（产品有效性）**：记录 clean checkout → 首条测试跑通的耗时 · 人工回答数 · 生成 diff 被保留的比例
- [ ] 10.8 **SM-8（不伤害）**：异常中断（超时 / SIGINT / **SIGKILL 后下次启动**）下恢复仍执行；`owned_by` 派生为 `operator` 的依赖被拒停；**子进程 env 不含 allowlist 外的变量**

## 11. 测试覆盖图〔TG-18〕

```
code path                          │ 测试类型        │ 用例要点
───────────────────────────────────┼────────────────┼────────────────────────────────────────
devenv_schema (JSON)               │ 单元            │ 无 PyYAML 正常读写 · 枚举越界
schema_version                     │ 单元            │ 缺失 → fail · **未来值 → fail（非尽力解析）**
───────────────────────────────────┼────────────────┼────────────────────────────────────────
openspec 写域单一锁 (三 skill)      │ 并发(多进程)    │ devenv‖init · devenv‖arch · init‖arch
                                   │                │ 不丢注入 · A 释放不删 B 的锁
**CAS (全部输入快照)**              │ 并发            │ **改 method 而非 status → 旧验证被拒回写**
atomic_write(mode=)                │ 单元            │ 脚本类落 0o755 · 覆盖时保留原 mode
锁短持有                            │ 并发            │ 长跑期间锁未被持有(不被误判残留)
退出码一码一义                      │ 单元            │ 各失败原因码不同 · 不需解析 stderr
───────────────────────────────────┼────────────────┼────────────────────────────────────────
set-lane --status verified         │ 单元            │ **一律 exit 5 拒绝**   ← 核心守卫
verify-lane (script 通道)          │ 集成            │ 亲自 fork 执行 · 证据字段齐全
confirm-lane (human 通道)          │ 单元            │ 落人门证据 · 模型不能代填
**method_digest 覆盖面**            │ 单元            │ **改 fixture/harness/lockfile → digest 失配**
**owned_by 派生**                   │ 集成            │ **预先在跑的依赖 → operator → 拒停**
**cleanup ledger 落盘**             │ 故障注入        │ **SIGKILL → 下次启动扫到并回收**
恢复路径                            │ 故障注入        │ 跑中抛异常 → 断言恢复被调用
超时杀进程树                        │ 集成            │ 孤儿容器被回收，不占端口
**最小环境 allowlist**              │ 单元            │ **子进程 env 不含 allowlist 外的变量**
非 POSIX refuse                    │ 单元(mock平台)  │ verify-lane refuse → 走 human 通道
───────────────────────────────────┼────────────────┼────────────────────────────────────────
source digest 锚                   │ 单元            │ **「行还在、内容变了」被抓**
digest 规范化                       │ 单元            │ 改注释/改 tab 的行为符合规则
append_makefile_target             │ 单元            │ 无尾换行 · tab · **重名 fail-closed(只判名)**
inject (fence-aware)               │ 单元(固定fixture)│ ``` / ~~~ / 四backtick / 缩进 fence
                                   │                │ 孤儿 / 逆序 / 交错 → fail-closed
                                   │                │ **MUST NOT 用本仓活语料当 fixture**
───────────────────────────────────┼────────────────┼────────────────────────────────────────
**三层框架完整性**                  │ 单元            │ **缺一层 → fail** · 五槽缺一 → fail
**三层状态附带项**                  │ 单元            │ **不适用无后果 → fail** · 人工无步骤 → fail
                                   │                │ **已实现无对应泳道 → fail**
devenv_lint 诚实性                  │ 单元            │ verified 残留 blocked_by 被抓
                                   │                │ blocked_by: TODO 被抓
sdflow-maintain 集成               │ 集成            │ **真实回归被拦下**（digest 失配）
───────────────────────────────────┼────────────────┼────────────────────────────────────────
**touched-files 回退**              │ 集成(临时 git 仓)│ **新写文件(untracked)被精确删除**
                                   │                │ **MUST NOT 用无路径限定 git clean**
                                   │                │ 既有文件被复原 · 人门期间手改 → 拒删
归位删源护栏                        │ 集成(临时 git 仓)│ untracked/symlink/submodule/digest 变 → 拒删
                                   │                │ backup manifest **入 git** 且可还原
归位端到端                          │ 集成(fixture)   │ **checkin 的 brownfield fixture**，确定性断言
───────────────────────────────────┴────────────────┴────────────────────────────────────────

无自动化覆盖（诚实登记）：
· SKILL.md 的编排纪律（时序 / 人门 / 冷审 / **R5 不重试** / **R7 不装依赖**）
  —— 模型行为，无确定性信号 → 归 spec-review + code-review
· **模型提的验证方法是否有效** —— ADR-0 的诚实边界，本就不归机械 → 归人门 + 冷审「验证方法镜」
· **`kind` / `layer` / `covers` 分类是否属实** —— 无独立信号 → 归人门分类清单 + 冷审「分类镜」
· **`assert True` 类语义恒真的 vacuous smoke** —— **任何外部插桩都堵不住**（要堵只有变异测试，判为太重）
  → 归冷审「vacuous 镜」。**MUST NOT 佯装机械层能堵**
· greenfield 端到端 → 归第 0 组上游试点（手动，SM-7 记录）
```
