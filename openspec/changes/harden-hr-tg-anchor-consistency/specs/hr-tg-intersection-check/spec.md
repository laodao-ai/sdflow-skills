## ADDED Requirements

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
