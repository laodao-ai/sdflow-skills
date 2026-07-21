# tasks — dedupe-issues-scripts-shared-layer

> 需求 ID 溯源：`SC-R1`~`SC-R4` = `issues-scripts-shared-core` 四需求；`DG-M1`/`DG-M2` = `determinism-guards` 两 MODIFIED 需求。
> 复选框在 archive 阶段勾（实现期改 change 四件套会触失鲜门）。

## 1. 建共享源骨架 `core.py`

- [ ] 1.1 在 `sdflow-issues/scripts/` 建 `core.py` 骨架；定义 `POOL_SPEC` 数据结构（bug/todo 两 pool × 差异维：文件粒度/目录/字段/词表/终态集）〔SC-R2〕
- [ ] 1.2 把 THREE_WAY 共享 helper（`atomic_write`/`repo_root`/`canonical_id`/`recorder_lock`/frontmatter mechanics …）上移 `core.py`，作唯一物理源〔SC-R2〕
- [ ] 1.3 把 TWO_WAY 的 bug↔todo 镜像逻辑（table/block 解析、doc/ID/定位 helper）上移 `core.py`，差异点改读 `POOL_SPEC`〔SC-R2〕

## 2. 三薄入口壳化并迁入 `sdflow-issues/scripts/`

- [ ] 2.1 `buglist.py` 壳化：解析 args → 注入 bug `POOL_SPEC` → 调 `core`；迁入 `sdflow-issues/scripts/`，改同目录 `import core`〔SC-R2, SC-R3〕
- [ ] 2.2 `todolist.py` 壳化：注入 todo `POOL_SPEC` → 调 `core`；迁入并同目录 `import core`〔SC-R2, SC-R3〕
- [ ] 2.3 `issues.py` 迁入 `sdflow-issues/scripts/`（原地即幸存 skill），跨池 reindex/batch/sweep 逻辑改用 `import core` 取共享 helper；`_scan_pool` 子进程契约保持〔SC-R2, SC-R3〕
- [ ] 2.4 逐命令核验：`core` 源码无 `if pool == "bug"/"todo"` 分支（差异全走 `POOL_SPEC`）〔SC-R2, DG-M1〕

## 3. skill 合并（目录 + SKILL.md + 触发）

- [ ] 3.1 合并 `sdflow-buglist`/`sdflow-todolist` 两份 `SKILL.md` 正文并入 `sdflow-issues/SKILL.md`（一份覆盖两池 + 跨池，去重 133 行重复正文），触发短语聚合到一个触发面〔SC-R1〕
- [ ] 3.2 迁移 `sdflow-buglist/tests/` + `sdflow-todolist/tests/` 到 `sdflow-issues/tests/`，路径与 import 改指 `sdflow-issues/scripts/`〔SC-R3〕
- [ ] 3.3 删除 `sdflow-buglist/`、`sdflow-todolist/` 目录〔SC-R1〕
- [ ] 3.4 保留 `sdflow-issues` 的 `sdflow:principles` 托管块一份（合并后仍一份、不重复）〔SC-R1〕

## 4. determinism-guards 守法切换

- [ ] 4.1 删除 `test_mirror_consistency.py`（三向/两向 AST roster——单一物理源使其无对象）〔DG-M1〕
- [ ] 4.2 新增守法测试：`core` 源码扫描断言无 pool 条件分支 + `POOL_SPEC` 各 pool 各维取值完备（缺项即红）〔DG-M1〕
- [ ] 4.3 确认 `validate_scan_envelope`（scan consumer fail-closed）、direct-snapshot↔scan golden 等价、`config.yaml` lint、`batches.md` lint 四守随迁移继续绿、不受影响〔DG-M1, DG-M2〕
- [ ] 4.4 核验三薄入口经**同目录** `import core` 取共享逻辑，无跨目录 import / sys.path 注入〔DG-M2, SC-R3〕

## 5. 下游托管引用同步（AD-5，fail-closed）

- [ ] 5.1 `README.md` skills 列表 3→1；`CLAUDE.md`/`AGENTS.md` 配套 skill 表与数据类 skill 名单更新〔SC-R4〕
- [ ] 5.2 `sdflow-init/assets/snippets/claude-section.md` + `sdflow-init/assets/workflow/workflow.md` 的 buglist/todolist 引用更新（下游铺设面，改后须 `sdflow-init update` 推）〔SC-R4〕
- [ ] 5.3 `sdflow-done`/`sdflow-ship`(+`ship_gate.py`)/`sdflow-code-review` 里 buglist/todolist 脚本路径引用改指 `sdflow-issues`〔SC-R4〕
- [ ] 5.4 `hack/tests/test_sync_principles.py` 投放面计数 17→15（`sync_principles.py` 动态枚举自动少一个，仅改断言/docstring 常量）〔SC-R4〕
- [ ] 5.5 全仓检索确认：除 `openspec/changes/archive/` 外无活跃托管点仍引用 `sdflow-buglist`/`sdflow-todolist`〔SC-R4〕

## 6. 行为等价 + 回归验证

- [ ] 6.1 重构前后 CLI 逐命令行为等价快照（`add`/`scan --json`/`set-status`/`triage`/`reindex`/`batch`：stdout JSON + 落盘字节 + 退出码），差异仅路径前缀〔SC-R3〕
- [ ] 6.2 全仓 `pytest` 通过数 ≥ 603，无 FAILED、无因重构导致的 skip〔SC-R3〕
- [ ] 6.3 跑 `setup.sh`：确认建 `sdflow-issues` 链接、orphan 清理回收 `sdflow-buglist`/`sdflow-todolist` 旧链接〔SC-R1〕
