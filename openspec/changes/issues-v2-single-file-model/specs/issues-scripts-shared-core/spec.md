## Purpose

记录三脚本合一为单个 `issues.py` 对原 `issues-scripts-shared-core` 能力的结构性变更：
`POOL_SPEC` 注入模式、三薄入口架构、`sdflow_issues_core` 共享包均被替代。

## REMOVED Requirements

### Requirement: 三 skill 合并为一个 `sdflow-issues`

本 requirement 的目标（三 skill 合一）已在先前 change 中完成。v2 进一步将三脚本入口合为单个
`issues.py`，该 requirement 的验收场景（只有一个 skill 目录与触发面）仍然成立，无需修改。

### Requirement: 共享逻辑收敛为唯一命名 package `sdflow_issues_core`，差异经封闭 schema `POOL_SPEC` 注入

v2 的 `issues.py` 是单文件脚本，不再需要 `sdflow_issues_core` 共享包和 `POOL_SPEC` 注入模式。
pool 差异（终态词表、特有字段）内联为脚本常量。

#### Scenario: sdflow_issues_core 包不再存在

- **WHEN** v2 部署完成后检查 `sdflow-issues/scripts/`
- **THEN** 不存在 `sdflow_issues_core/` 目录
- **AND** `issues.py` 为自包含单文件脚本

#### Scenario: buglist.py 和 todolist.py 入口不再存在

- **WHEN** v2 部署完成后检查 `sdflow-issues/scripts/`
- **THEN** 不存在 `buglist.py` 和 `todolist.py`
