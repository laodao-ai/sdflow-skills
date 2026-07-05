# spec-workflow delta — gate-checkpoint-hardening

## ADDED Requirements

### Requirement: checkpoint 标签契约单一真相源与模板样例一致性

checkpoint 任务标签形状（`checkpoint(<change>:task<N>-<slug>)`）的**权威定义 MUST 唯一落在 `checkpoint-commit.sh` 契约（头注释 + `--help`）**；其他载体（`workflow.md` 派发指令、`sdflow-ship`/`sdflow-code-review` SKILL、本 spec 的 Scenario）MUST 以**引用式**指向该契约，MUST NOT 各自复述完整格式串（复述 = doc 副本，改标签形状时会漂）。文档/spec 中标签的占位符 MUST 用无歧义写法（如 `<change-slug>`），MUST NOT 用易被误读为"须填真实 slug"的写法（如 `<当前change>`）——占位符语义 = 任意 demo 值。凡**展示机器锚样例**的模板 MUST 把锚写成独占 bare line（无反引号包裹、无同行尾注），与真产报告一致（对齐既有「各模板 MUST 把锚写在独占一行」需求），防未来报告照抄模板致 gate 行级锚解析假命中/漏命中。

#### Scenario: 改标签形状只改一处
- **WHEN** 需调整 checkpoint 标签形状（如加字段）
- **THEN** 仅改 `checkpoint-commit.sh` 契约一处；`workflow.md`/SKILL/spec 因引用式而无需同步改，MUST NOT 存在第二份需手工对齐的完整格式串

#### Scenario: 占位符不被误读为真实 slug
- **WHEN** 实现者读 spec/doc 中的 checkpoint 标签示例
- **THEN** 占位符写法（`<change-slug>` 等）明示其为任意占位 demo，MUST NOT 让人误以为示例里的字面串是必须照填的本 change 真实 slug

#### Scenario: 模板锚样例为独占 bare line
- **WHEN** 任一模板/文档展示 `<!-- ship-gate: ... -->` 或 checkpoint 标签机器锚样例
- **THEN** 该样例锚独占一行、无反引号/尾注；照抄该模板产出的真报告，其锚行能被 gate 的行级字面查找正确解析（不因装饰字符落入误判）

### Requirement: gate 新鲜度判定不纳入工作树 dirty 状态

`ship_gate.py` 的产物新鲜度判定 MUST 只依据**已提交盘面**（committed 产物与结论锚行），MUST NOT 将工作树 staged/unstaged/untracked 的非-openspec 改动纳入判定——与"盘面即状态 = committed 产物"地基一致〔T33/T35 定夺〕。`sdflow-ship` 编排器 MAY 在收尾以**非门禁软提示**告知"工作树存在未提交改动、gate 判定不含它们"，该提示 MUST NOT 改变 gate 的推进/拒绝语义。

#### Scenario: 工作树 dirty 不改变 gate 判定
- **WHEN** gate 运行时工作树含未提交的非-openspec 代码改动，而已提交盘面满足推进条件
- **THEN** gate 照常判可推进（committed-only），MUST NOT 因工作树 dirty 判失鲜或拒绝；如有软提示则仅信息性、不影响退出码

### Requirement: gate 熔断重试计数为编排器短时职责，不持久化下沉

阶段三熔断（同一 invocation 内同一步同步重跑一次仍无锚行 → 按 UNKNOWN 停上抛）的**重试计数 MUST 由编排器在单 invocation 内短时持有**，MUST NOT 持久化为跨 turn / 跨步状态——持久化会撞"ship 零跨步状态"〔D9〕与"盘面即状态 / gate 零副作用"〔adr/0006〕三条红线（"重跑无新产物"本质无盘面差异，gate 无法零副作用地区分首跑 vs 重跑）〔T26 定夺：已探索，结论=不下沉〕。

#### Scenario: 熔断计数不落持久状态
- **WHEN** 同一 invocation 内某步重跑一次仍无锚行
- **THEN** 编排器以单 invocation 短时计数触发熔断（判 UNKNOWN 停上抛人工），MUST NOT 写任何跨步/跨 turn 的计数状态文件；跨 invocation 重调 `/sdflow-ship` 时计数不延续（与"停即停、重调即续"一致）
