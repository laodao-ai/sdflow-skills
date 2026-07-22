# Code-review fix1 — dedupe-issues-scripts-shared-layer

分支级冷代码审 5 条发现的自动修实现报告。改动处均标注释 `[impl-review-fix]`。
未勾任何复选框、未打 checkpoint、未改 proposal/design/specs/tasks。

## 等价 oracle 结果

仓根全套件（`/usr/bin/python3 -m pytest -q`）：

```
2137 passed, 8 skipped, 3 xfailed in 148.80s (0:02:28)
```

与 oracle（2137 passed）一致——F1 纯正确性修复（happy-path 行为不变、只补错误路径复位），
F3/F4/F5 为守卫加强/平台健壮性，现状仍全绿。

---

## [F1·高·CONFIRMED] recorder 委派 token 复位不在 try/finally

**修法**：`sdflow-issues/scripts/issues.py` `main()`（约 :1214-1227）——把 core 委派单例全局
`_ACTIVE_RECORDER_TOKEN`/`_ACTIVE_RECORDER_CHAIN` 的 set → `args.func(args)` → reset 三步中，
将 `args.func(args)` 包进 `try`，两个复位移入 `finally`，无条件复位为 `None`（不依赖 `args.func`
正常返回）。set 的原条件/值不变。

**防御**：`sdflow-issues/tests/conftest.py` 加 `autouse` fixture `_reset_recorder_delegation_globals`，
每个测试后无条件复位 `sdflow_issues_core._ACTIVE_RECORDER_TOKEN`/`_ACTIVE_RECORDER_CHAIN = None`，
消除测试靠执行顺序侥幸绿。

**复现已消解证据**：
- 修后跑 `main()` 的 `_die` 错误路径（`batch set-status nonexistent-key DONE` → SystemExit(1)），
  同进程读回 `core._ACTIVE_RECORDER_TOKEN` / `_ACTIVE_RECORDER_CHAIN` 均为 `None`
  （实测输出 `post-main token: None chain: None`）——finally 经错误路径仍复位。
- 对照证：把 core 全局置为脏 token（`stale-token-abc` / `batch-set-status -> scan`）后调
  `validate_recorder_participant` → 抛 `RecorderLockError: invalid recorder participant`
  （旧代码错误路径正会留此脏值）；复位为 `None` 后不再产生泄漏的委派状态。

## [F3·高·CONFIRMED] node-id baseline「冻结」是假的（可游戏化）

**修法**：`sdflow-issues/tests/test_task6_coverage_gate.py` `test_baseline_is_frozen_and_nonempty`
把软下限 `>= 2000` 换为钉死精确值 + 文件 sha256：

- `_BASELINE_EXPECT_COUNT = 2093`（baseline 非注释非空行数，实测）
- `_BASELINE_EXPECT_SHA256 = "b08c60d536f456db6d9f1ad3b233f2c832da3f3e71327a4cc52a0f0aacc2e3ec"`
  （`hashlib.sha256(BASELINE.read_bytes())`，实测）

断言 `len == 精确值` + `sha256 == 钉死值` + 原有 `ALLOWLIST_DELETED <= baseline`。注释说明
baseline 是冻结契约、任何改动必过本断言 = 强制显式改常量经审查。加 `import hashlib`。

**钉死加强证据**：把 `_BASELINE_EXPECT_COUNT` 改 9999 后测试反红
（`baseline node 数变动: 期望 9999, 实得 2093`），证精确值门有效（删条目使总数跌离 2093 即被抓，
不再靠软下限逃逸）。

## [F4·中·CONFIRMED] thinness 守把 missing helper 当成功

**修法**：`sdflow-issues/tests/test_determinism_guards.py` 为三薄入口定义显式
**expected-export roster**（`EXPECTED_EXPORTS`，从当前真实导出集钉死）：

- `buglist` / `todolist`（`_BUGTODO_EXPECTED`，各 24 个）：22 个解析到 core 的公共 helper +
  pool-bound 薄委派 `all_ids` / `next_id`（`__module__` 指本入口，属 `ALLOWED_POOL_BOUND`）。
- `issues`（`_ISSUES_EXPECTED`，33 个）：`_BUGTODO_EXPECTED` ∪ 9 个 issues.py re-export 的
  underscore helper（`_reject_line_unsafe`、`_validate_unicode_scalar`、`_validated_recorder_model`、
  `_legacy_semantic_id_key`、`_match_marker_line`、`_die`、`_render_recorder_document`、
  `_legacy_block_range`、`_scan_legacy_block_range`）。

守卫 `test_thin_entry_does_not_shadow_core_helper` 改为遍历 `EXPECTED_EXPORTS[entry_name]`（非全
ROSTER）：`_MISSING` 不再静默 `continue` 而是收进 `missing` → 断言 `not missing`（缺失即红）；
再走原有 identity / ALLOWED_POOL_BOUND / ALLOWED_DISTINCT 判定。确不导出的 underscore-内部 helper
（`import *` 不带）显式不在名单（显式移除，非 missing 跳过掩盖）。加冗余锚：`EXPECTED_EXPORTS`
各集 MUST ⊆ ROSTER（拼写错/死配置当场红）。

**加强证据**：从 `buglist` 入口删 `detect_change` 后守卫反红
（`buglist 未导出预期共享 helper（从薄入口删 = 破单一源/静默回归）: ['detect_change']`），
证「删薄入口 roster helper 不反红」的假绿已消除。

## [F5·中·历史遗留本次迁入 core] detect_change subprocess text 无 utf-8

**修法**：`sdflow-issues/scripts/sdflow_issues_core/__init__.py` `detect_change()`（约 :1025 的
`git rev-parse --abbrev-ref HEAD`）`subprocess.run` 加 `encoding="utf-8"`（该站点用 `text=True`
且读 `out.stdout.strip()`，Windows 非 UTF-8 locale 下按平台默认编码解码可能崩）。

**面治核查**：core 内另一处 git `subprocess.run`（:933 `git rev-parse --show-toplevel`）用
`capture_output=True` **不带** `text=True`（bytes 模式，无文本解码环节），无此风险，无需改。
core 内无其它 `text=True` 的 git subprocess 缺 encoding。

---

## 汇总

| 发现 | 文件 | 状态 |
|---|---|---|
| F1 | `sdflow-issues/scripts/issues.py` + `tests/conftest.py` | 已修（try/finally + autouse 复位） |
| F3 | `sdflow-issues/tests/test_task6_coverage_gate.py` | 已修（钉死 2093 + sha256） |
| F4 | `sdflow-issues/tests/test_determinism_guards.py` | 已修（expected-export roster + 缺失即红） |
| F5 | `sdflow-issues/scripts/sdflow_issues_core/__init__.py` | 已修（encoding="utf-8"） |

全套件 2137 passed / 8 skipped / 3 xfailed，全绿。
