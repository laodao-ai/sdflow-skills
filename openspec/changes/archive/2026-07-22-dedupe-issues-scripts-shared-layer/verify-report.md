---
ship-gate:
  verify: PASS
  reviewed_sha: abd64cf3183c1fdc83ddff34d164cd2ca67af238
---

# Verify Report — dedupe-issues-scripts-shared-layer

- **日期**：2026-07-22
- **change**：dedupe-issues-scripts-shared-layer
- **reviewed_sha**：`abd64cf3183c1fdc83ddff34d164cd2ca67af238`

## 结论：PASS

三脚本（buglist.py/todolist.py/issues.py）已合并为唯一命名 package `sdflow_issues_core` + 三薄入口；三 skill 合一为 `sdflow-issues`；旧目录已删；下游托管引用已同步；determinism-guards 守法已切换为「单一物理源 + AST 无 pool 分支守 + POOL_SPEC 封闭 schema + thinness 同一性守」。全套件 **2143 passed / 8 skipped / 3 xfailed / 0 failed**（从仓根 `/usr/bin/python3 -m pytest -q`，148s）。8 个 skip 全为平台条件（`skipif sys.platform != "win32"` 的 Windows 本地盘 smoke 等），**非因重构导致的 skip**。核心需求逐条落地，无核心缺口。

## 逐需求核对表

| 需求/任务 | 代码出处（文件:行 / 测试） | 状态 |
|---|---|---|
| SC-R1 三 skill 合一为 `sdflow-issues`（单 SKILL.md、单触发面） | `sdflow-issues/SKILL.md`（一份）；旧目录 `ls sdflow-buglist/sdflow-todolist` → No such file | ✅ |
| SC-R1 骑墙规则 + 误判代价登记 | `sdflow-issues/SKILL.md:115`「🔀 骑墙判定」段 + `:140`「⚠️ 已知代价：误判落错池不可机械恢复」 | ✅ |
| SC-R2 唯一命名 package `sdflow_issues_core`（非裸 `core`） | `sdflow-issues/scripts/sdflow_issues_core/__init__.py`（97815 B） | ✅ |
| SC-R2 封闭 schema `POOL_SPEC` + required 维（粒度/目录/legacy glob/字段/词表/终态/`DEFAULT_PREFIX`/scan 键） | `__init__.py:53 class PoolSpec`、`:88 POOL_SPEC_FIELDS`、`:112 POOL_SPEC`；`test_pool_spec_schema.py` 绿 | ✅ |
| SC-R2 `validate_pool_spec()` import 时 fail-closed | `__init__.py:146 def validate_pool_spec` + `:198 validate_pool_spec()`（模块级调用）；`test_pool_spec_schema.py` 绿 | ✅ |
| SC-R2/DG-M1 core 无 pool 值条件分支 + AST 守 | `test_determinism_guards.py`（AST 级守 + mutation test）绿 | ✅ |
| SC-R2/RR-M THREE_WAY helper（`repo_root` 等）单一物理源 | `__init__.py` 唯一实现；`test_repo_root_identity_{buglist,issues,todolist}.py` 绿 | ✅ |
| SC-R3 三薄入口迁入 `sdflow-issues/scripts/` + `sys.path.insert` + `from sdflow_issues_core import` | `buglist.py:18-22`、`todolist.py:18-20`、`issues.py`（同目录） | ✅ |
| SC-R3 旧 `sdflow-buglist/`·`sdflow-todolist/` 目录删除 | `ls` → No such file | ✅ |
| SC-R3/SW-M sibling-spawn 常量改同目录 | `issues.py:51 SCRIPT_DIR`、`:52 BUGLIST_SCRIPT`、`:53 TODOLIST_SCRIPT` = `os.path.join(SCRIPT_DIR, ...)` | ✅ |
| SC-R3 tests 迁入 `sdflow-issues/tests/` | `test_buglist.py`/`test_todolist.py`/`test_issues.py` 等 20 文件在 `sdflow-issues/tests/`，全绿 | ✅ |
| DG-M1 删 `test_mirror_consistency.py`（三向/两向 AST roster 无对象） | 文件不存在；guard 已重写 | ✅ |
| DG-M1 thinness 同一性守（`__module__ == 'sdflow_issues_core'`） | `test_determinism_guards.py` 绿 | ✅ |
| DG-M1 golden 诚实降级为接线守 | determinism-guards spec Scenario + `test_determinism_guards.py` 绿 | ✅ |
| DG-M2 `validate_scan_envelope` fail-closed / batch lint 只读 | `test_batch_lint.py`、`test_issues.py` 绿 | ✅ |
| DG-M2 无跨目录 import / 无 sys.path 污染（除入口自身 dir） | `test_determinism_guards.py` 绿 | ✅ |
| SC-R4 下游托管引用同步（README/CLAUDE/AGENTS/init/done/ship_gate/CI/安装测试） | `test_downstream_reference_guard.py` 绿（allowlist 外零命中） | ✅ |
| SC-R4 `test_sync_principles.py` 17→15 | `hack/tests/test_sync_principles.py:4,18` = 15；动态 SKILL 计数 = 15 | ✅ |
| SC-R4 机械引用守卫 test（allowlist） | `test_downstream_reference_guard.py:78,110` 绿 | ✅ |
| SC-R4 CI path-trigger + 测试调用改 `sdflow-issues` | `.github/workflows/windows-recorder-smoke.yml`；`test_setup_sdflow.py` 断言迁移 | ✅ |
| SC-R3/R5 CLI 逐命令行为等价（param 化留存测试） | `test_task6_cli_equivalence_harness.py` 绿（见 Minor T210 硬化 defer） | ✅ |
| SC-R3/R5 覆盖判据零回归门（非计数魔数） | `test_task6_coverage_gate.py` 绿 | ✅ |
| RR-M repo_root fail-closed 语义不变 | `test_repo_root_identity_*.py` 绿 | ✅ |
| SW-M RENAME-MAP 枚举 + sibling→同目录 场景 | change delta `specs/spec-workflow/spec.md`（archive 时同步主 spec，task 5.7） | ✅ |
| 全套件绿 | `/usr/bin/python3 -m pytest -q` → 2143 passed / 8 skipped / 3 xfailed / 0 failed | ✅ |
| 3.5 保留一份 `sdflow:principles` 托管块 | `sdflow-issues/SKILL.md:21 start` … `:91 end`（唯一块） | ✅ |

## 缺口清单

### 核心缺口（FAIL）

无。

### Minor 缺口 / 显式 deferred（可接受）

- **T208**（OPEN·记 todolist）：`sdflow_issues_core` god-module 拆 cohesive 子模块 + 消 issues 自调用子进程 —— 任务 7.1 显式 defer，已占位。
- **T209**（OPEN·记 todolist）：`move --to-pool` 跨池搬运命令（误判落错池的机械恢复路径）—— 任务 7.2 显式 defer，已占位。
- **T210**（OPEN·记 todolist）：`test_task6_cli_equivalence_harness` 现为新实现 happy-path smoke（非 before/after 冻结 golden，旧脚本已删无法 live before/after）；等价性已由 T2 byte-identical smoke 证过。前向 test 硬化，冷审 defer，非本 change 阻断项。
- **T211**（OPEN·记 todolist）：`sdflow_issues_core` 委派 token/chain 为进程级共享全局；异常残留错误路径泄漏（F1）已修，in-process 多池并发/嵌套仍会串。冷审 defer，非本 change 阻断项。
- 主 spec（`openspec/specs/recorder-root-resolution/spec.md`、`spec-workflow/spec.md`）仍含旧 skill 名 —— **符合设计**：本 change 携 MODIFIED delta，主 spec 在 archive 阶段同步（delta-at-archive 纪律，task 5.7），非缺口。
- 8 个 skip 全为平台条件（Windows 本地盘 smoke `skipif sys.platform != "win32"` 等），非重构导致，符合 task 6.2「无因重构导致的 skip」。

---

PASS
