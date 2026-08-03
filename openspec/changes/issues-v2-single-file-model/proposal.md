## Why

当前 issues 管理采用按日期/按月分组的多条目大文件模型（10 个 buglist + 1 个 todolist），一个文件内混合
多个 issue 的 frontmatter 和 Markdown block。这导致：
1. **操作效率低**——修改一个 issue 需要在大文件中定位 frontmatter 行 + marker block，脚本需维护行级
   精确解析和双写一致性（frontmatter ↔ block 同步），复杂度高且容易出错
2. **三脚本冗余**——`buglist.py`/`todolist.py`/`issues.py` 三入口 + `sdflow_issues_core` 共享包，
   大量镜像代码，改一处要同步多处
3. **batch 机制鸡肋**——设计用于规划 issue 的实现批次，但实际使用中被 roadmap 替代，徒增字段和 triage 流程

## What Changes

- **BREAKING**: 存储格式从多条目大文件改为一个 issue 一个 `.md` 文件（`open/` + `closed/` 两目录）
- **BREAKING**: `buglist.py` + `todolist.py` + `issues.py` 三脚本合并为单个 `issues.py`
- **BREAKING**: 砍掉 `batch` 字段和 `triage` / `sweep` 命令
- `change` 字段拆分为 `source_change`（发现来源）+ `resolved_by`（修复方，关闭时填）
- `INDEX.md` / `CLOSED.md` 变为派生物（`reindex` 命令再生），不再是手工维护的权威源
- `set-status` 到终态时自动 `git mv` 从 `open/` 到 `closed/`
- 新增 `migrate` 命令：独立迁移工具，供所有项目仓一次性从 v1 转 v2
- `sdflow-done` 的 sweep 调用同步改为 v2 接口

## Capabilities

### New Capabilities
- `issues-v2-storage`: 单文件存储模型（一个 issue 一个 .md，frontmatter 为权威源，open/closed 目录分层）
- `issues-migration`: 独立迁移工具，从 v1 多条目格式转换为 v2 单文件格式，支持 legacy 表格和 frontmatter overlay 两种旧格式

### Modified Capabilities
- `issues-scripts-shared-core`: 三脚本合一为单个 `issues.py`，砍掉 `POOL_SPEC` 注入模式和三薄入口架构

## Impact

- **sdflow-issues/scripts/**：`buglist.py`、`todolist.py`、`sdflow_issues_core/` 全部替换为新 `issues.py`
- **sdflow-issues/SKILL.md**：触发路由、命令示例、数据模型文档全面更新
- **sdflow-done/SKILL.md**：§2.1 重写（sweep→scan + hand-off 改列 ID）[spec-review-amendment]
- **sdflow-issues/tests/**：全部重写（现有测试与旧格式深度耦合）；格式无关的不变量测试（仓根解析、Windows 编码、覆盖率门禁）改造后保留 [spec-review-amendment]
- **openspec/issues/**：目录结构重组（`buglist/` + `todolist/` → `open/` + `closed/`）
- **hack/tests/**：引用 `todolist.py` 的测试需同步更新（`test_harden_sdflow_spec_followup_closure.py` 等）
- **CLAUDE.md / README.md**：命令示例和路径引用更新
- **AGENTS.md**：issues 路径引用更新 [spec-review-amendment]
- **sdflow-init/assets/snippets/claude-section.md**：issues 路径引用更新（推给消费仓的模版）[spec-review-amendment]
- **openspec/CONTEXT.md**：领域术语更新 [spec-review-amendment]
- **openspec/specs/spec-workflow/spec.md**：补 MODIFIED delta（batch/sweep/buglist.py 硬编码断言）[spec-review-amendment]
- **openspec/specs/determinism-guards/spec.md**：补 MODIFIED/REMOVED delta [spec-review-amendment]
- **openspec/specs/recorder-root-resolution/spec.md**：补 MODIFIED delta [spec-review-amendment]
- **.github/workflows/windows-recorder-smoke.yml**：更新硬编码测试路径 [spec-review-amendment]

## Success Metrics

1. 全部 287 个 issue 成功迁移到 v2 格式，`reindex` 后 INDEX.md/CLOSED.md 内容完整
2. `issues.py` 的 `add` / `set-status` / `scan` / `reindex` / `next-id` 命令通过测试
3. `migrate` 命令在本仓库和至少一个消费仓上跑通
4. sdflow-done 的 sweep 能正确调用 v2 接口
5. 全仓 pytest 绿

## Non-Goals

- 不做 Web UI 或数据库后端（继续纯文件管理）
- 不做跨仓 issue 关联（每个仓独立管理）
- 不提供 reopen 命令（极低频场景，手动 `git mv` 足够）
- 不保留旧格式兼容读取（迁移工具一次性转换）

## Compliance

N/A
