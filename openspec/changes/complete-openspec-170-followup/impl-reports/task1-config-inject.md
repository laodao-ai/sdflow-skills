# Task 1: P2 config 层注入 archive guidance 与 Purpose 规则

## 改动摘要

- `sdflow-init/assets/workflow/config.template.yaml`（bundle 权威源，先改）：
  - `rules.specs` 列表末尾新增一条 Purpose 规则：`新能力 delta spec MUST 以 `## Purpose` 开头（≥50 字符）；1.7.0 archive 抬升此段进主 spec，缺则写 TBD 占位符`
  - 文件末尾（`metrics:` 段之前）新增 `operations.archive.guidance` 段，值为两条硬约束字符串：
    - `归档 MUST 走 openspec archive CLI（它同步 delta→openspec/specs/ + 更新 INDEX + 校验），禁手动 mv（漏 spec 同步）`
    - `archive 前 MUST 先 reconcile tasks.md 复选框（否则 CLI 报 N/M incomplete 警告 + verify 误判）`
- `openspec/config.yaml`（本仓实例，同步改）：
  - `rules.specs` 追加同一条 Purpose 规则（逐字一致）
  - 在 `impl-pipeline` 之后、`metrics:` 之前新增同一 `operations.archive.guidance` 段（逐字一致）
- 未改 `apply.guidance`（design.md D4：当前无需下沉的 apply 面硬约束，符合任务范围）
- `operations.archive.guidance` 在两个文件中均为 YAML 字符串数组（非字符串），已用 `python3 -c "import yaml; ..."` 实测两文件均可解析、类型为 `list`、长度为 2，符合 "guidance 形状须为字符串数组，否则 CLI 拒绝并打警告" 的约束

## 验收核对
- config.yaml 含 operations.archive.guidance 段：✅（实测 YAML 解析，`list` 长度 2）
- config.yaml rules.specs 含 Purpose 规则：✅（实测 YAML 解析命中）
- template 同步 operations 段和 Purpose 规则：✅
- template 与 config 的 operations 段和 Purpose 规则内容对齐：✅（`git diff` 逐行比对，两处新增文本完全一致）
