# hr-tg-intersection-check Specification

## Purpose
TBD - created by archiving change mlh-p4-reason-code-validators. Update Purpose after archive.
## Requirements
### Requirement: 模型传入命中 TG 集与 HR-TG 子集求交〔spec-review Q-D·推翻 grill Q1〕

校验器 SHALL 吃**模型判好的命中 TG 集**作入参（不自扫 proposal 声明），与 HR-TG 子集求交，输出**带「依据模型判定」的**结果——`hit:[...]｜依据模型判定:[...]` + 规范锚串 或 `none｜依据模型判定:[...]`，把模型给的输入集显式暴露供复审（**不 emit 裸 `none`**，adr/0018）。

> 〔为何模型传入而非自扫声明〕grill Q1 曾选「泛化 tg02_hit 扫 proposal 头部声明」、否决「模型传入」；冷镜爆点5 证明前提为假——TG 声明散落且格式不一（proposal 括号 `（TG-01）` / design section 锚 `## …〔TG-08〕` / 顶部 `〔TG〕` 行不统一），头部扫描**捕不全**（本 change 的 TG-08 在 design.md、proposal 用括号 → 扫描得空集却实际命中 HR-TG 成员）。「命中哪些 TG」无确定性信号 = 判断归模型；脚本只做确定性的交集 + 锚。

#### Scenario: 命中 HR-TG 成员
- **WHEN** 模型传入命中集 `[TG-04, TG-16, TG-19]`
- **THEN** 输出 `hit:[TG-04,TG-16]｜依据模型判定:[TG-04,TG-16,TG-19]` + 规范锚串（TG-19 不属 HR-TG 故不在 hit、但在依据里可见）；命中集 `sorted(set(...))` 确定序

#### Scenario: 命中 TG 无一属 HR-TG
- **WHEN** 模型传入 `[TG-01, TG-19]`（均不在子集）
- **THEN** 输出 `none｜依据模型判定:[TG-01,TG-19]`，退出码 0

#### Scenario: 模型给的集为空
- **WHEN** 模型传入空集 `[]`
- **THEN** 输出 `none｜依据模型判定:[]`（依据可见，非静默 none）

### Requirement: HR-TG 清单从单一源读、禁硬编码

校验器 SHALL 从 `$RULES_ROOT/trigger-catalog.md` 的 `## 七、HR-TG 子集` 段 `> 成员：` 行 parse HR-TG 成员，MUST NOT 在脚本内硬编码成员副本——改单一源即改行为。trigger-catalog 路径 SHALL 由入参（`--trigger-catalog`，SKILL 供 `$RULES_ROOT/trigger-catalog.md`）给定，MUST NOT 用 `__file__.parent.parent` 推导（`openspec/workflow/` 下无 trigger-catalog 副本，会 fail-closed 空跑）〔spec-review A3〕。

#### Scenario: 单一源变更即生效
- **WHEN** `trigger-catalog.md` 的 `> 成员：` 行增删某 TG 编号
- **THEN** 校验器求交结果随之变化，无需改脚本

#### Scenario: 单一源损坏 fail-closed
- **WHEN** `## 七、HR-TG` 段或 `> 成员：` 行缺失 / 不可读
- **THEN** 退出码非 0 + stderr 原因，MUST NOT 静默按空子集放行

### Requirement: 命中 TG 集/成员行严格解析 + TG 存在性校验、畸形 fail-closed〔M3+M-new〕

校验器 SHALL 对 `--tg-set` 入参与 trigger-catalog `> 成员：` 行做**边界严格**解析：仅**原始空串**（`--tg-set ""`）表空集；CSV 出现空 cell / 纯空白 cell / 前导或尾随逗号 / 连续逗号（如 `TG-04,,TG-16`、单个 `,`）→ 非零退出 + stderr，MUST NOT 静默过滤空 cell 后返回合法列表。成员行 token SHALL 词边界锚定（整体形如 `TG-<数字>`），残余畸形 token（如 `TG-04x`）→ 非零退出，MUST NOT 用宽松子串抽取正规化为 `TG-04`。

**TG 存在性〔M-new〕**：校验器 SHALL 校验 `--tg-set` 传入的每个 TG **存在于 trigger-catalog 定义的全 TG 集**，不存在的 TG（合法 shape 但 catalog 无定义，如 `TG-99`、`TG-1`）→ 非零退出 + stderr，MUST NOT 当"非 HR-TG 成员"静默丢出 hit。

**全 TG 集解析边界钉死〔spec-review F8〕**：全 TG 集 SHALL 只从 `## 三、触发词目录` 段到下一 level-1/2 标题之间、行首 `fullmatch` `^\s*\|\s*TG-\d+\s*\|` 的**表行**取（trigger-catalog 正文别处有游离 TG 提及如「命中 TG-01」「参见 TG-99 草案」，MUST NOT blind 全文 `findall` 纳入全集——否则未来正文举例一个不存在 TG 会被静默扩进全集、反削 M-new）。成员/tg-set token SHALL 逐个 `fullmatch` `^TG-\d+$` 且拒未消费残留（`TG-04.0`/`TG-04-removed` 词边界后有残留 → 非零退出，非宽松 `findall` 抽出 `TG-04`）。

**catalog 内部一致〔spec-review F7〕**：加载 catalog 时 SHALL 断言 `HR-TG 成员集 ⊆ 全 TG 集`，成员行含全集外 TG（单一源内部损坏）→ 所有调用 fail-closed。

> 〔为何〕mlh-p4 后 `parse_tg_set` 以 `[t for t in tokens if t]` 静默过滤空 cell、成员抽取用宽松 `TG-\d+`，且**只校验 TG shape、不校验存在**——畸形被静默正规化而非 fail-closed，违 MLH 红线；尤其 TG 手误（`TG-16`→`TG-1`，合法 shape 但不存在）会与 HR-TG 求交时当"非成员"**静默丢出 hit → 漏一个 HR-TG 命中、不开领域 cross-model**。catalog 全 TG 集有确定性信号（单一源），MUST 机械化拦截。

#### Scenario: tg-set 含空 cell 非零退出
- **WHEN** `--tg-set "TG-04,,TG-16"` 或 `--tg-set ","`（连续/前后逗号产生空 cell）
- **THEN** 非零退出 + stderr `[hr_tg_intersect] FAIL: <tg-set 空 cell 原因>`，MUST NOT 过滤空 cell 后当合法输入

#### Scenario: 原始空串仍表空集
- **WHEN** `--tg-set ""`（原始空串，非逗号产生的空 cell）
- **THEN** 输出 `none｜依据模型判定:[]`，退出码 0（保留合法空集入口）

#### Scenario: 成员行畸形 token fail-closed
- **WHEN** trigger-catalog `> 成员：` 行含 `TG-04x` 之类非词边界 token
- **THEN** 非零退出（单一源损坏），MUST NOT 宽松抽取为 `TG-04`

#### Scenario: 不存在的 TG fail-closed〔M-new〕
- **WHEN** `--tg-set "TG-16,TG-99"`（TG-99 shape 合法但 catalog 无定义）
- **THEN** 非零退出 + stderr（TG 未定义），MUST NOT 静默把 TG-99 当"非 HR-TG 成员"丢弃

#### Scenario: 手误 TG 不被静默丢出 hit〔M-new〕
- **WHEN** 模型欲传 `TG-16`（HR-TG 成员）却手误为 `TG-1`（不存在）
- **THEN** 非零退出，暴露手误——MUST NOT 求交时当"非成员"静默丢、漏掉本应命中的 HR-TG 项

#### Scenario: 正文游离 TG 不进全集〔F8 边界〕
- **WHEN** trigger-catalog 正文（非 `## 三` 表行）出现「参见 TG-99」之类游离提及
- **THEN** 全 TG 集解析 MUST NOT 纳入 TG-99（只取 `## 三` 段 `| TG-NN |` 表行）；后续 `declared="TG-99"` 仍被 M-new 判不存在

#### Scenario: 残留后缀 token fail-closed〔F8 fullmatch〕
- **WHEN** 成员行或 tg-set 含 `TG-04.0` / `TG-04-removed`（`TG-04` 后有未消费残留）
- **THEN** 非零退出，MUST NOT 宽松抽出 `TG-04`

