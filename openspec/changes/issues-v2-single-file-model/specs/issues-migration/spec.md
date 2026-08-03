## Purpose

独立迁移工具：将 v1 多条目格式（legacy 表格 + frontmatter overlay）一次性转换为 v2 单文件格式。
适用于所有使用 sdflow-issues 的项目仓，非本仓专用。

## ADDED Requirements

### Requirement: MIG-01 支持两种 v1 格式

迁移工具 SHALL 解析两种旧格式：
1. **Legacy 表格格式**：无 `sdflow-issues:` frontmatter，issue 信息在 Markdown 表格行中
2. **Frontmatter overlay 格式**：有 `sdflow-issues: items:` YAML frontmatter + marker block

#### Scenario: 解析 legacy 表格格式

- **WHEN** 输入文件只有 Markdown 表格（无 `sdflow-issues:` frontmatter）
- **THEN** 从表格行提取 ID、module、summary、priority、status、change 等字段
- **AND** 从表格下方的 detail section 提取 body 内容

#### Scenario: 解析 frontmatter overlay 格式

- **WHEN** 输入文件有 `sdflow-issues: items:` frontmatter
- **THEN** 从 frontmatter 提取字段，从 marker block 提取 body 内容

### Requirement: MIG-02 输出 v2 单文件

迁移 SHALL 为每个 issue 生成一个 v2 格式的 `.md` 文件：
- 活跃 issue → `open/{ID}.md`
- 已关闭 issue → `closed/{ID}.md`

字段映射见 design.md 的字段映射表。

#### Scenario: 活跃 issue 迁到 open/

- **WHEN** 源文件含 status=OPEN 的 T257
- **THEN** 生成 `open/T257.md`，frontmatter 含 v2 schema 全部必填字段

#### Scenario: 已关闭 issue 迁到 closed/

- **WHEN** 源文件含 status=FIXED 的 B7
- **THEN** 生成 `closed/B7.md`，frontmatter 含 `closed_date`（从状态变更历史提取）

### Requirement: MIG-03 幂等与安全

迁移 SHALL 幂等执行：已存在的目标文件按 ID 判重并跳过。
迁移 SHALL NOT 删除源文件——由用户确认后手动清理。

#### Scenario: 重复执行不覆盖

- **WHEN** `closed/B1.md` 已存在，再次执行 migrate
- **THEN** B1 被跳过，已有文件不被覆盖
- **AND** 统计报告中 B1 计入 skipped

### Requirement: MIG-04 迁移完成后自动 reindex

迁移完成后 SHALL 自动调用 `reindex` 生成 INDEX.md 和 CLOSED.md。

#### Scenario: 迁移后索引完整

- **WHEN** migrate 完成
- **THEN** INDEX.md 列出 open/ 中全部 issue
- **AND** CLOSED.md 列出 closed/ 中全部 issue
