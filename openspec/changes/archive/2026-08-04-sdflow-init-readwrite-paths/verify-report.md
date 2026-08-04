---
ship-gate:
  verify: PASS
  reviewed_sha: 6f3930afe17063bd2b95f995f051bc9f7e9b9895
---

# Verify Report — sdflow-init-readwrite-paths

**日期**: 2026-08-04
**Change**: sdflow-init-readwrite-paths
**结论**: **PASS**（附 1 条 minor 缺口）

## 逐需求核对表

### Task 1: T64 · `_atomic_write_settings()` mkstemp 唯一名

| 子项 | 要求 | 判定 | 证据锚 |
|---|---|---|---|
| 1.1 | 改用 `tempfile.mkstemp`，失败时 `os.unlink` 清理残留 | PASS | `sdflow-init/scripts/init.py:975` — `tempfile.mkstemp(prefix=".settings-", dir=...)` 在外层 `try` 内；内层 `except BaseException` 走 `os.unlink(tmp)` |
| 1.2 | 测试 tmp 文件名非固定 | PASS | `sdflow-init/tests/test_init.py:990` — `TestAtomicWriteSettingsMkstemp::test_tmp_file_uses_mkstemp_prefix`：spy `os.replace` 源路径前缀断言 `.settings-` |
| 1.3 | 测试 mkstemp 失败返回 False | PASS | `sdflow-init/tests/test_init.py:1007` — `test_mkstemp_oserror_returns_false`：monkeypatch `tempfile.mkstemp` 抛 `OSError("disk full")`，断言返回 `False` |

### Task 2: T149 · `lint_config()` 顶层重复键检测

| 子项 | 要求 | 判定 | 证据锚 |
|---|---|---|---|
| 2.1 | 新增 `_detect_duplicate_top_keys()` | PASS | `sdflow-init/scripts/init.py:723` — 行级扫描，`encoding="utf-8-sig"`，`except (OSError, UnicodeDecodeError)` |
| 2.2 | `lint_config()` 中调用，重复键追加 reason | PASS | `sdflow-init/scripts/init.py:756` — 在 `_yq()` 前调用，reason 含 `"config.yaml 顶层键重复: ..."` |
| 2.3 | 测试：重复顶层键 → 非空 reason | PASS | `sdflow-init/tests/test_config_lint.py:439` — `TestDuplicateTopKeys::test_duplicate_top_key_detected` |
| 2.4 | 测试：非 UTF-8 不裸抛 | PASS | `sdflow-init/tests/test_config_lint.py:450` — `test_non_utf8_no_crash`：写 `b"\xff\xfe"` 字节，断言无 Traceback |
| 2.5 | 测试：BOM 首键正确识别 | PASS | `sdflow-init/tests/test_config_lint.py:457` — `test_bom_first_key_detected`：`utf-8-sig` 编码写入，断言检测到重复 |

### Task 3: T6 · `ensure_global_hooks()` Codex 降级告警

| 子项 | 要求 | 判定 | 证据锚 |
|---|---|---|---|
| 3.1 | 检测 `~/.codex/` 存在时追加告警行 | PASS | `sdflow-init/scripts/init.py:914` — `os.path.isdir(codex_home)` 条件追加含 `⚠` 的告警行 |
| 3.2 | 测试：存在 → 有告警；不存在 → 无告警 | PASS | `sdflow-init/tests/test_init.py:1017` — `test_codex_dir_present_shows_warning` + `test_init.py:1026` — `test_codex_dir_absent_no_warning` |

### Task 4: 收尾

| 子项 | 要求 | 判定 | 证据锚 |
|---|---|---|---|
| 4.1 | 全量 pytest 跑绿 | PASS | 本次亲跑 @ `6f3930a`：`109 passed, 1 skipped, 0 failed`（1 skipped 为既有 Windows fcntl 降级，与本 change 无关） |
| 4.2 | 关闭 T64、T149、T6 | **GAP (minor)** | 三个 issue 均仍在 `openspec/issues/open/todo/`，status=PROPOSED，未 set-status DONE + evidence |

## Tickets 轨聚合覆盖

- impl-pipeline: tickets
- impl-reports 齐全：task1-brief / task2-brief / task3-brief / task4-verify-aggregate
- task4-verify-aggregate 单元层 SHA `d639e63` 对应 git log 中 task3 checkpoint commit，109 passed 0 failed，与本次亲跑一致

## 缺口清单

1. **[minor] Task 4.2**: T64/T149/T6 三个 issue 未从 open 移至 closed、未 set-status DONE。这是 issue tracker 元数据同步，不影响功能实现。可在 `/sdflow-done` 归档前由 `/sdflow-issues` 一并完成。

## 判定

**PASS** — 全部核心功能需求（T64 mkstemp、T149 重复键检测、T6 Codex 告警）均已实现并有测试覆盖，pytest 全绿。唯一缺口为 issue tracker 状态未同步（minor，不阻塞 ship）。
