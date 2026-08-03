## Purpose

单文件存储模型：每个 issue 一个 `.md` 文件，YAML frontmatter 为权威数据源，body 为自由格式描述。
`open/` 和 `closed/` 目录按状态分层，`INDEX.md` / `CLOSED.md` 为派生产物（`reindex` 再生）。

## ADDED Requirements

### Requirement: STOR-01 单文件存储格式

每个 issue SHALL 存储为独立的 `.md` 文件，文件名为 `{ID}.md`（如 `B25.md`、`T257.md`）。
文件内容 SHALL 由 YAML frontmatter（`---` 围栏）和自由格式 Markdown body 组成。

frontmatter 必填字段：`id`(str), `pool`(str ∈ {bug, todo}), `status`(str), `date`(str YYYY-MM-DD),
`module`(str), `summary`(str)。
可选字段：`priority`(str|null, bug only), `type`(str|null, todo only), `source_change`(str|null),
`resolved_by`(str|null), `closed_date`(str|null), `closed_reason`(str|null)。

脚本 SHALL 只读写 frontmatter，MUST NOT 解析 body 内容。

#### Scenario: 读取单文件 issue

- **WHEN** `read_issue("open/T257.md")` 被调用
- **THEN** 返回包含 frontmatter 全部字段的 dict + body 文本
- **AND** body 未被修改或解析

#### Scenario: 写入单文件 issue

- **WHEN** `write_issue(path, frontmatter, body)` 被调用
- **THEN** 目标文件为原子替换写入（.tmp + rename）
- **AND** frontmatter 字段顺序固定（id, pool, status, priority, type, date, source_change, module, summary, resolved_by, closed_date, closed_reason）

### Requirement: STOR-02 open/closed 目录分层

活跃 issue（非终态 status）SHALL 位于 `openspec/issues/open/` 目录。
已关闭 issue（终态 status）SHALL 位于 `openspec/issues/closed/` 目录。

终态定义：bug 池 = FIXED | WONTFIX；todo 池 = DONE | WONTDO。

`set-status` 命令将 status 改为终态时，SHALL 自动执行 `git mv open/{ID}.md closed/{ID}.md`。

#### Scenario: set-status 到终态自动移文件

- **WHEN** `issues.py set-status --id B7 --to FIXED --evidence "commit abc"` 执行
- **THEN** `open/B7.md` 的 frontmatter status 更新为 FIXED，closed_date 填当天
- **AND** 文件被 `git mv` 到 `closed/B7.md`

#### Scenario: set-status 到非终态不移文件

- **WHEN** `issues.py set-status --id T5 --to PROPOSED` 执行
- **THEN** `open/T5.md` 的 frontmatter status 更新为 PROPOSED
- **AND** 文件仍在 `open/` 目录

### Requirement: STOR-03 INDEX.md 和 CLOSED.md 为派生产物

`INDEX.md` SHALL 由 `reindex` 命令从 `open/` 目录全部 `.md` 文件的 frontmatter 再生。
`CLOSED.md` SHALL 由 `reindex` 命令从 `closed/` 目录全部 `.md` 文件的 frontmatter 再生。

两者 MUST NOT 被手工编辑——任何手工修改在下次 `reindex` 时被覆盖。

#### Scenario: reindex 生成完整索引

- **WHEN** `issues.py reindex` 执行
- **THEN** `INDEX.md` 包含 `open/` 中每个 issue 的一行表格记录，按 ID 排序
- **AND** `CLOSED.md` 包含 `closed/` 中每个 issue 的一行表格记录，按 ID 排序
- **AND** 表格列与 frontmatter 字段一一对应

### Requirement: STOR-04 ID 分配

bug 使用 B 前缀，todo 使用 T 前缀，各自独立编号。
`next-id` SHALL 扫描 `open/` + `closed/` 全部文件名，取对应前缀的 max(N)+1。

#### Scenario: next-id 跨目录扫描

- **WHEN** `open/` 有 T257.md，`closed/` 有 T260.md
- **THEN** `issues.py next-id --pool todo` 输出 `T261`

### Requirement: STOR-05 add 命令创建新 issue

`add` 命令 SHALL 接收 `--pool` 和 `--json` 参数，创建新 issue 文件到 `open/` 目录。

#### Scenario: 添加 bug

- **WHEN** `issues.py add --pool bug --json '{"module":"m","summary":"s","priority":"P1"}'` 执行
- **THEN** `open/B{next}.md` 被创建，frontmatter 含 `pool: bug`, `status: OPEN`, `priority: P1`

#### Scenario: 添加 todo

- **WHEN** `issues.py add --pool todo --json '{"module":"m","summary":"s","type":"基础设施"}'` 执行
- **THEN** `open/T{next}.md` 被创建，frontmatter 含 `pool: todo`, `status: OPEN`, `type: 基础设施`

### Requirement: STOR-06 set-status 校验

`set-status` SHALL 校验：
1. 终态 issue 不可再改 status（文件已在 closed/）
2. bug 的 FIXED 必须有 `--evidence`
3. WONTFIX/WONTDO 必须有 `--reason`
4. 终态词表按池校验（bug 不可 DONE，todo 不可 FIXED）

#### Scenario: 终态 issue 拒绝再改

- **WHEN** `issues.py set-status --id B7 --to OPEN` 执行，且 B7 已在 `closed/`
- **THEN** 命令以非零退出码失败，报错信息包含"终态"

#### Scenario: FIXED 缺 evidence 被拒

- **WHEN** `issues.py set-status --id B7 --to FIXED` 执行（未传 `--evidence`）
- **THEN** 命令以非零退出码失败

### Requirement: STOR-07 scan 命令

`scan` SHALL 默认扫描 `open/` 目录，支持 `--all` 扫描 open + closed。
支持 `--pool`, `--status`, `--json` 过滤和输出格式选项。

#### Scenario: 默认 scan 只看 open

- **WHEN** `issues.py scan` 执行
- **THEN** 只输出 `open/` 中的 issue

#### Scenario: scan --all 含 closed

- **WHEN** `issues.py scan --all` 执行
- **THEN** 输出 `open/` 和 `closed/` 中的全部 issue

#### Scenario: scan --json 输出

- **WHEN** `issues.py scan --json` 执行
- **THEN** 输出 JSON 列表，每项为 frontmatter 字段的 dict
