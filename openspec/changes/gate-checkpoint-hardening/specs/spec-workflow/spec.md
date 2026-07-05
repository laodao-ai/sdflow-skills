# spec-workflow delta — gate-checkpoint-hardening

## ADDED Requirements

### Requirement: checkpoint 标签契约单一真相源与模板样例一致性

checkpoint 任务标签形状（`checkpoint(<change>:task<N>-<slug>)`）的**格式权威 MUST 唯一落在 `ship_gate.py` 的 TAG_RE 解析器**（enforcing parser，MUST 带 canonical-shape 头注释说明规范形状），并由 `test_producer_parser_contract.py` 钉死 producer↔parser 一致；**`checkpoint-commit.sh` 为 format-agnostic 透传（只裹 `checkpoint($step)`、不认识 task 格式），MUST NOT 被引作格式源**。「plan 每任务 commit 步 MUST 用命名空间标签」这条**工作流规则** MUST 就地留 `workflow.md` 一处（含格式串一次并标"形状由 TAG_RE 执行/契约测试钉死"），`sdflow-ship`/`sdflow-code-review` SKILL、本 spec 的 Scenario MUST 以**引用式**指向，MUST NOT 各自复述完整格式串（复述 = doc 副本，会漂）。文档/spec 中标签占位符 MUST 用无歧义写法（如 `<change-slug>`），MUST NOT 用易被误读为"须填真实 slug"的写法（如 `<当前change>`）——占位符语义 = 任意 demo 值。凡**展示 ship-gate 机器锚样例**（`<!-- ship-gate: X -->`）的模板 MUST 把锚写成独占 bare line（无反引号包裹、无同行尾注），与真产报告一致（对齐既有「各模板 MUST 把锚写在独占一行」需求），防报告照抄模板致 gate 行级锚 `strip()≠字面` 漏判/假命中。**人读格式串防漂移**〔spec-review-amendment SR-4〕：workflow.md 保留的人读格式串（贴"权威见 TAG_RE"标签）是文本、非技术约束——MUST 有一道**机械钩子**兜底（`TAG_RE` 定义旁的显式 checklist 项「改此正则前先搜 workflow.md 格式串同步」，或一条弱校验测试断言 workflow.md 该行与 TAG_RE 语义不漂），MUST NOT 仅靠"非权威"标签这一人肉记忆。

#### Scenario: 改标签格式只改一处
- **WHEN** 需调整 checkpoint 标签格式
- **THEN** 格式权威在 TAG_RE，改它一处 + `test_producer_parser_contract.py` 守卫；`workflow.md` 规则一处、SKILL/spec 引用式，MUST NOT 存在第二份需手工对齐的完整格式串；MUST NOT 因 `checkpoint-commit.sh` 被误当格式源而在其 `--help` 复制一份权威格式定义

#### Scenario: 占位符不被误读为真实 slug
- **WHEN** 实现者读 spec/doc 中的 checkpoint 标签示例
- **THEN** 占位符写法（`<change-slug>` 等）明示其为任意占位 demo，MUST NOT 让人误以为示例里的字面串是必须照填的本 change 真实 slug

#### Scenario: ship-gate 锚模板为独占 bare line
- **WHEN** 任一 SKILL 模板展示 `<!-- ship-gate: ... -->` 锚样例（如 design-approved / verify / code-review）
- **THEN** 该样例锚独占一行、无反引号包裹、无同行尾注；照抄该模板产出的真报告，其锚行 `strip()` 后整行等值于锚字面，能被 gate 的行级字面查找正确解析（不因装饰字符或尾注致漏判）

### Requirement: gate 新鲜度判定不纳入工作树 dirty 状态

`ship_gate.py` 的产物新鲜度判定 MUST 只依据**已提交盘面**（committed 产物与结论锚行），MUST NOT 将工作树 staged/unstaged/untracked 的非-openspec 改动纳入判定——与"盘面即状态 = committed 产物"地基一致〔T33/T35 定夺〕。`sdflow-ship` 编排器 MAY 在收尾以**非门禁软提示**告知"工作树存在未提交改动、gate 判定不含它们"，该提示 MUST NOT 改变 gate 的推进/拒绝语义。**merge 边界硬检查（缩简版）**〔spec-review-amendment SR-2〕：`sdflow-done` 的 merge 步 MUST 在 merge 前检查工作树是否存在**本 change 分支生命周期内新产生的未追踪（untracked）文件**——存在则 **MUST 以 halt+报告（非交互）方式停下并上抛人工**（防"未追踪工作经 checkout+ff-merge 存活于磁盘却从未进 base git 历史 → 看似还在、实际从未 ship 进 base"）；此"停"MUST 复用 sdflow-done 既有的非交互 halt 惯用法（如"ff 不可行→停下报告"），**MUST NOT 引入阶段三中途 AskUserQuestion**（守既有"阶段三全程无 AskUserQuestion / 无人类阻塞门"MUST）。判据 MUST 排除仓库既有 debris（仅圈分支内新产 untracked）。此检查落 `sdflow-done`（merge 卫生前提），MUST NOT 上移进 gate（不污染盘面即状态）。**范围边界**：tracked 非-openspec 改动被 commit 步 `git add -u` 先行提交的一路〔codex-2〕本 change 不处理，defer todolist。

#### Scenario: 工作树 dirty 不改变 gate 判定
- **WHEN** gate 运行时工作树含未提交的非-openspec 代码改动，而已提交盘面满足推进条件
- **THEN** gate 照常判可推进（committed-only），MUST NOT 因工作树 dirty 判失鲜或拒绝；如有软提示则仅信息性、不影响退出码

#### Scenario: merge 前 untracked 硬检查以 halt 上抛
- **WHEN** `sdflow-done` 到 merge 步时工作树有本 change 分支内新产生的未追踪文件
- **THEN** merge 步以非交互 halt+报告停下、上抛人工先处理（commit 或确认无关），MUST NOT 静默 ff-merge、MUST NOT 用 AskUserQuestion 中途问；判据排除仓库既有 debris；仅当无此类 untracked（或人工处理后重入）才 merge

### Requirement: gate 熔断重试计数为编排器短时职责，不持久化下沉

阶段三熔断（同一 invocation 内同一步重跑一次仍无进展 → 按 UNKNOWN 停上抛）的**重试判定 MUST 由编排器在单 invocation 内短时持有**，MUST NOT 持久化为跨 turn / 跨步状态——持久化会撞"ship 零跨步状态"〔D9〕与"盘面即状态 / gate 零副作用"〔adr/0006〕三条红线〔T26 定夺：持久化不下沉〕。**触发判据 MUST 以「该步 ship-gate 锚行集合是否变化」为准**〔spec-review-amendment SR-1：原"HEAD 未移动+报告 mtime/sha 未变"判据被证失效——HEAD 移动是 OR 逃逸口（修复类步几乎必产 commit → HEAD 动即判"有进展"→ 熔断永不触发、无限循环复现），mtime/sha 亦弱信号〕：重跑一步前后，比较该步报告的**锚行集合**（复用 gate 的 `_line_scoped_hits`/`anchors_in` 语义，即 gate 真正关心的结论锚）——锚行集合无净变化即判无进展、停上抛人工；`HEAD` 移动与否、文件 mtime 变化与否 MUST NOT 作为免疫信号。此比较 MUST 做成**无状态比较（gate 子命令 / 小脚本）**：两次锚行快照由编排器在单 invocation 内持有、作参数传入，helper 不落地任何文件、不跨 invocation 持久化（故不撞 D9；复议了原被误否决的候选 C），且可 CI 断言。**fail-safe**：快照缺失（无法确认是否首跑，如 context 压缩）时 MUST 保守判"无进展"（停上抛），MUST NOT 默认放行再跑。判据仅适用于**有锚报告的步**（`STEP_IN_PROGRESS`/`RERUN_STALE`）；SOP/plan/impl 等非单一报告步不适用〔SR/codex-5〕。

#### Scenario: 熔断触发靠锚行集合变化而非 HEAD/mtime
- **WHEN** 同一 invocation 内某有锚报告步重跑，重跑后该步报告的 ship-gate 锚行集合与重跑前相同（即便期间 HEAD 因修复 commit 前移、或报告 mtime 变化）
- **THEN** 编排器判无进展、触发熔断（UNKNOWN 停上抛人工）；MUST NOT 因 HEAD 已移动或 mtime 已变而判"有进展"放行；比较经无状态 helper（快照作参数），MUST NOT 写任何跨步/跨 turn 状态文件；快照缺失时保守判无进展；跨 invocation 重调 `/sdflow-ship` 时判定不延续

## MODIFIED Requirements

> 〔spec-review-amendment SR-3〕T37/T38 改的是既有主 spec 需求文本（非新增），须走 MODIFIED、不能只靠 ADDED——否则 `openspec archive` 只追加不改旧文本、517 行 `<当前change>` 不会被同步。

### Requirement: checkpoint 标签 producer→parser 契约测试

checkpoint 任务标签由 `checkpoint-commit.sh`（producer，把首参包成 commit subject，**format-agnostic：不认识 task 格式，仅执行包裹动作、非格式源**）铸造、由 `ship_gate.py` 的 `TAG_RE`（parser，**格式形状的权威**）解析；这条 producer→parser 链 MUST 有机械绑定测试守卫，SHALL NOT 依赖对文档占位符文本的比对（文档是人读占位符、非机器解析对象）。测试 MUST 调用**真实脚本**产出 subject 再喂 parser，使 producer 包裹逻辑或 parser 正则任一漂移即令测试失败。此为纯防漂移加固，`TAG_RE` 与 `checkpoint-commit.sh` 的行为 MUST 逐字不变。**文档/spec 中展示的标签形状 MUST 标注为样例（权威形状见 TAG_RE），占位符 MUST 用无歧义写法 `<change-slug>`，MUST NOT 用易被误读为"须填真实 slug"的 `<当前change>`**〔T37/T38〕。

#### Scenario: 真实脚本产出的 subject 被 parser 正确识别

- **WHEN** 契约测试在临时 git repo 中以命名空间形式的首参调用真实 `checkpoint-commit.sh`（首参 = `<change-slug>:task<号>-<slug>` 形态，此处为样例占位符、权威形状见 TAG_RE）
- **THEN** 测试 MUST 读回该次 commit 的 subject 并断言 `ship_gate.py` 的 `TAG_RE.match` 成功、捕获组分别等于该 change 名与该任务号；MUST 用真实脚本调用与真实 git commit（MUST NOT 用手写字符串 mock subject——否则放过 producer 包裹漂移）

#### Scenario: 裸格式经真实脚本产出仍被识别且命名空间组为空

- **WHEN** 契约测试以裸形式首参（`task<号>-<slug>`，无命名空间前缀）调用真实 `checkpoint-commit.sh`
- **THEN** 测试 MUST 断言 `TAG_RE.match` 成功、命名空间捕获组为 `None`、任务号捕获组正确——固定裸格式向后兼容在 producer→parser 链上的实际行为
