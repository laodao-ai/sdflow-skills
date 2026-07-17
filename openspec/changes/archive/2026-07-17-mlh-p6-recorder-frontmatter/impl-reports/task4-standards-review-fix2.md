# Task 4 Standards Compliance Review — Fix 2

结论：**PASS**

- 固定 fix 审包：`impl-reports/task4-review-fix2-package.diff`（SHA-256 `8181fdab9ef0bb9728a2457b2f73ca54997eef8678a7ff6ec6dcf64eaa7e96f7`）
- 固定范围：`94057a3..8169aeb`；审包与 `git diff --binary 94057a3..8169aeb` byte-identical
- Findings：Critical 0 / Important 0 / Minor 0
- 门禁：原审与 fix1 双轴剩余的四项 finding 已全部闭合，Task 4 Standards 轴通过。

## Checklist 适用性

workflow root 为 `/Users/cheneyzhao/.sdflow/workflow`。已复核 `code-checklists/code-review-base.md`、`code-checklists/README.md` 与 `domains/` 注册表；当前领域 delta 仅覆盖 backend、backend-go、embedded、embedded-ml307c、embedded-esp32，本变更是 Python CLI + Markdown/frontmatter 数据管道，**领域清单未覆盖**。本轮依据通用 CR-01~09、Task 4/Global Constraints、`SW-RI-1`、`SW-RI-3`、`SW-RI-4`、`DG-RI-1` 及原/fix1 双轴 findings 独立复审。

## fix1 剩余 findings 闭环

### 1. unreliable arity 在 registry 写前 fatal — PASS

- `_reject_ambiguous_legacy_rows()` 不再以 old/new 字面出现推断 row 可判性。非 7/8 列只有在首八个标准位置分别通过 semantic ID、required field、pool enum/status 校验，且尾随 cells 不含 old/new 时，才作为可证明的 trailing-cell warning 继续。
- 中间插 cell 即使最终 cell 是无关 batch，也会因 enum/status 列位错移在 preflight 阶段拒绝；target key 藏在尾随 cell 同样拒绝。frontmatter shadow 的冻结 legacy row 仍以 effective owner 分区，不反向覆盖 frontmatter batch 真值。
- 真实 CLI 回归断言 `stage=preflight`、原命令、无 traceback，且 registry/dated/INDEX bytes 全不变；允许的无害尾随 warning 仍回显并保持默认成功语义。

### 2. all-new/mixed `{old,new}` 三 ownership relation preflight — PASS

- `retag_rename_snapshot()` 现在以 `batch in {old_key,new_key}` 构造 relation target，而非只看仍需 retag 的 old-side item；因此 provenance-matched all-old、mixed、all-new retry 均在任何写盘前执行 target relation gate。
- canonical 缺 marker、overlay ownership/relation 非法、pure-legacy candidate 内 marker collision 三种 ownership 形态均由 all-new/mixed 矩阵覆盖，失败时 registry/dated/INDEX 不变；合法 all-old/mixed/all-new 连续两次原命令仍幂等收敛。

### 3. scan ID 错型走受控三段式、无 traceback — PASS

- `validate_scan_envelope()` 在 semantic parser 前显式要求 `item[index].id` 为 string；`null`、integer、list、object 均抛含字段定位的 `ValueError`，诊断具备 `ERROR / cause / fix` 三段。
- CLI `main()` 错误边界回归确认 exit 2、stderr 无 `Traceback`，且既有 INDEX/batches bytes 不变；合法 legacy alias 与 malformed/Unicode digit 的既有边界未放宽。

### 4. marker collision 点名 target ID / file / line — PASS

- pure-legacy bug target 先走 candidate-aware `_legacy_block_range()`，再走 document-wide structural summary；完整 marker pair 与 partial marker 都不会再被通用 `marker-only legacy` 诊断抢先。
- 真实 CLI 回归确认错误含 target `id=B1`、dated file、实际 `line=`、`stage=preflight` 与可复制原命令，且 registry/dated/INDEX bytes 不变。

## Task 4 acceptance 与通用门禁复核

| 条款 | 结论 | 证据 |
|---|---|---|
| dated read/parse=1、per-pool scan=0、snapshot reindex reuse | **PASS** | direct snapshot 与 instrumentation/call-count tests 保持通过；`_reindex_core(snapshot=...)` 不回读 producer。 |
| registry-first provenance 与 first/all-old/mixed/all-new/orphan/double-key/unknown-source | **PASS** | fix2 补齐 new-side target relation，合法 retry 矩阵连续重跑收敛。 |
| canonical/overlay/legacy retag 与 bytes preservation | **PASS** | overlay frozen row/body、pure-legacy row、BOM/CRLF/foreign namespace 既有覆盖全绿；非法 target 写前拒绝。 |
| strict scan consumer fail-closed | **PASS** | 坏 JSON、缺键、错型、缺 file、enum/schema/ID drift 均在派生写前受控失败。 |
| 四阶段 fault + nonfatal boundary | **PASS** | registry/dated/INDEX/batches fault 继续 nonzero、含 stage+原命令并可重跑；只有可证明不影响 batch 真值的 legacy warning 默认成功。 |
| generic reindex gate | **PASS** | 默认逐条回显可判 legacy problems 并成功，`--strict` 非零；frontmatter/ID/consumer fatal 不因 rename 修复而降级。 |
| CR-01/02/09 | **PASS** | 新错误路径在写前失败、诊断带恢复上下文；新增回归覆盖函数边界与真实 CLI、bytes unchanged、retry/idempotence，且无外部时序依赖。 |

## 验证

- `uv run --with pytest pytest -q sdflow-issues/tests/test_task4_rename_snapshot.py sdflow-buglist/tests/test_mirror_consistency.py -W error` → `98 passed`
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error` → `437 passed, 1 skipped`（Windows-only）
- `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` → valid
- `python3 hack/sync_principles.py --check` → `20` 个投放面一致
- `git diff --check 94057a3..8169aeb` → PASS
- 固定审包 byte comparison → MATCH

未发现新的 Critical、Important 或 Minor；Standards 轴可进入 Task 4 checkpoint。
