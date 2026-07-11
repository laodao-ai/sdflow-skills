## ADDED Requirements

### Requirement: 命中 TG 集与 HR-TG 成员行严格解析、畸形 fail-closed〔T138〕

校验器 SHALL 对 `--tg-set` 入参与 trigger-catalog `> 成员：` 行做**边界严格**解析：仅**原始空串**（`--tg-set ""`）表空集；CSV 出现空 cell / 纯空白 cell / 前导或尾随逗号 / 连续逗号（如 `TG-04,,TG-16`、单个 `,`）→ 非零退出 + stderr，MUST NOT 静默过滤空 cell 后返回合法列表。成员行 token SHALL 词边界锚定（整体形如 `TG-<数字>`），残余畸形 token（如 `TG-04x`）→ 非零退出，MUST NOT 用宽松子串抽取正规化为 `TG-04`。

> 〔为何〕mlh-p4 后 `parse_tg_set` 以 `[t for t in tokens if t]` 静默过滤空 cell、成员抽取用宽松 `TG-\d+`——畸形被静默正规化而非 fail-closed，违 MLH 红线「坏输入断言非零退出」，可能掩盖模型侧记号错误（`declared=` 虽暴露但机械层本应挡）。

#### Scenario: tg-set 含空 cell 非零退出
- **WHEN** `--tg-set "TG-04,,TG-16"` 或 `--tg-set ","`（连续/前后逗号产生空 cell）
- **THEN** 非零退出 + stderr `[hr_tg_intersect] FAIL: <tg-set 空 cell 原因>`，MUST NOT 过滤空 cell 后当合法输入

#### Scenario: 原始空串仍表空集
- **WHEN** `--tg-set ""`（原始空串，非逗号产生的空 cell）
- **THEN** 输出 `none｜依据模型判定:[]`，退出码 0（保留合法空集入口）

#### Scenario: 成员行畸形 token fail-closed
- **WHEN** trigger-catalog `> 成员：` 行含 `TG-04x` 之类非词边界 token
- **THEN** 非零退出（单一源损坏），MUST NOT 宽松抽取为 `TG-04`
