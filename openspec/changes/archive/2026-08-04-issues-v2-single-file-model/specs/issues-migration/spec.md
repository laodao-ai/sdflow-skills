## Purpose

独立迁移工具：将 v1 多条目格式（legacy 表格 + frontmatter overlay）一次性转换为 v2 单文件格式。
适用于所有使用 sdflow-issues 的项目仓，非本仓专用。

## ADDED Requirements

### Requirement: MIG-01 支持两种 v1 格式 + 逐 item 去重 [spec-review-amendment]

迁移工具 SHALL 解析两种旧格式，且 SHALL 按 item ID 去重（非逐文件二选一）：
1. **Legacy 表格格式**：无 `sdflow-issues:` frontmatter，issue 信息在 Markdown 表格行中
2. **Frontmatter overlay 格式**：有 `sdflow-issues: items:` YAML frontmatter + marker block

**同文件双格式共存时**（真实语料的多数情况）：先收集 legacy 表格行 → 再用 frontmatter overlay items 覆盖同 ID 条目（frontmatter 为权威源，表格行为冻结快照）。复用 `_build_effective_snapshot` 的 shadow 逻辑。

#### Scenario: 解析纯 legacy 表格格式

- **WHEN** 输入文件只有 Markdown 表格（无 `sdflow-issues:` frontmatter）
- **THEN** 从表格行提取 ID、module、summary、priority、status、change 等字段
- **AND** 从表格下方的 detail section 提取 body 内容

#### Scenario: 解析纯 frontmatter overlay 格式

- **WHEN** 输入文件有 `sdflow-issues: items:` frontmatter 且无 legacy 表格行
- **THEN** 从 frontmatter 提取字段，从 marker block 提取 body 内容

#### Scenario: 同文件双格式共存 + ID 冲突 [spec-review-amendment]

- **WHEN** 输入文件同时含 legacy 表格行和 frontmatter overlay 项，且 T67 在表格行中 status=PROPOSED、在 frontmatter 中 status=DONE
- **THEN** T67 取 frontmatter 值（status=DONE），legacy 表格行被忽略
- **AND** 统计报告中记录 shadowed ID 数量

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
- **THEN** 生成 `closed/B7.md`，frontmatter 含 `closed_date`（best-effort 从 body 状态变更行提取；提取不到则取文件日期，已知为近似值）[spec-review-amendment]

**迁移数据约束豁免** [spec-review-amendment]：迁移产出的文件不经过 `set-status` 命令，不受 STOR-06 的 evidence/reason 门禁约束——历史数据缺 evidence 或 reason 是已知事实，不阻塞迁移。

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

### Requirement: MIG-05 PLANNED 批次信息迁移 [spec-review-amendment]

迁移 SHALL 把 `batches.md` 中 PLANNED 状态批次的成员/优先级/计划文本搬入对应成员 issue 的 body。

#### Scenario: PLANNED 批次信息不丢失

- **WHEN** `batches.md` 含 PLANNED 批次 `harden-gate` 成员 `B1, B2, T30`
- **THEN** `B1.md`/`B2.md`/`T30.md` 的 body 追加 `> [迁移自批次 harden-gate] 原计划: {plan_text}`
