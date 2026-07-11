## ADDED Requirements

### Requirement: 命中 TG 集与 HR-TG 子集求交

校验器 SHALL 从 proposal.md 头部声明区抽取命中 TG 集，与 HR-TG 子集求交，输出命中列表 + 规范锚串（引 HR-TG 章节）或 `none`。命中判定 SHALL 复用 `tg02_hit` 三防线（fence-aware、只扫首个 `## ` 前头部区、只认 strip 后 `startswith("〔TG")` 的声明行）。

#### Scenario: 命中 HR-TG 成员
- **WHEN** proposal 头部声明 `〔TG-04：…〕〔TG-16：…〕〔TG-19：…〕`
- **THEN** 输出 hit 列表 `[TG-04, TG-16]`（TG-19 不在 HR-TG 子集，剔除）+ 规范锚串

#### Scenario: 命中 TG 无一属 HR-TG
- **WHEN** proposal 头部仅声明 `〔TG-01〕〔TG-19〕`（均不在子集）
- **THEN** 输出 `none`，退出码 0

#### Scenario: 描述性提及不算命中
- **WHEN** proposal 正文（首个 `## ` 之后）或 fenced 代码块内出现 `TG-04` 字样、或否定句「TG-04 不命中」
- **THEN** 不计入命中 TG 集（与 tg02_hit 声明式口径一致）

### Requirement: HR-TG 清单从单一源读、禁硬编码

校验器 SHALL 从 `$RULES_ROOT/trigger-catalog.md` 的 `## 七、HR-TG 子集` 段 `> 成员：` 行 parse HR-TG 成员，MUST NOT 在脚本内硬编码成员副本——改单一源即改行为。

#### Scenario: 单一源变更即生效
- **WHEN** `trigger-catalog.md` 的 `> 成员：` 行增删某 TG 编号
- **THEN** 校验器求交结果随之变化，无需改脚本

#### Scenario: 单一源损坏 fail-closed
- **WHEN** `## 七、HR-TG` 段或 `> 成员：` 行缺失 / 不可读
- **THEN** 退出码非 0 + stderr 原因，MUST NOT 静默按空子集放行
