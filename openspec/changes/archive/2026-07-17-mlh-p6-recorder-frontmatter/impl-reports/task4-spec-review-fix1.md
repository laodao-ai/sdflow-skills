# Task 4 Fix 1 Spec Compliance Review

结论：**FAIL**（Important 1 / Minor 1；无 Critical）。固定范围 `b899792..8ed9bc2`；固定审包 `task4-review-fix1-package.diff` 与 `git diff --binary b899792..8ed9bc2` byte-identical，SHA-256 均为 `dfb4ec7ed87a5a29a6f74e49a3cde3ad233e5dd501c7ca50cfdb23ff2da44695`。

## Critical

无。

## Important

### I1 — all-new retry 绕过 target relation preflight，仍可 warning-only success

- **位置**：`sdflow-issues/scripts/issues.py:997-1008`、`:1051`、`:2097-2103`、`:2125-2135`。`retag_rename_snapshot()` 只把 `batch == old_key` 的 item 放入 `target_ids`；document 在 all-new retry 中没有 old item便直接跳过 `_reject_target_document_problems()`。原 snapshot 的 marker/frontmatter relation problems 随后只进入 `_reindex_core(snapshot=updated)` 的默认 nonfatal problems 路径，最终被回显但命令仍 exit 0。
- **违反目标态**：Task 4 acceptance 2/5 与 `tasks.md` 4.4 要求 provenance-matched 的全 old、混合、全 new retry均收敛且 fatal problem 不得 warning-only success；4.5 与 `specs/spec-workflow/spec.md` SW-RI-1/SW-RI-3 要求 marker ownership/frontmatter relation 冲突 fatal，只有与 retag 无关且 item 仍可判的 legacy arity/block problem 可继续。全 new 只是 crash-cut/retry 阶段，不是解除 target invariant 的依据。
- **独立复现**：registry 仅有 `batch-new` 且 `重命名自: batch-old`，canonical bug `B1.batch=batch-new` 但正文缺 B1 marker；执行真实 `cmd_batch_rename(old=batch-old,new=batch-new)` 先回显 `frontmatter 有 B1 但缺 marker block`，随后仍输出 `{"items_changed":0,"mode":"retry"}` 并成功返回。也就是已知 target relation 非法仍被当成完全收敛。
- **修复要求**：preflight target 集合必须按 rename state 覆盖 `batch in {old_key,new_key}` 的 provenance-owned items；至少对 canonical/overlay target 的全 old、混合、全 new盘面统一执行 relation fatal gate，并保持 registry/dated/INDEX/batches 在 preflight failure 时 bytes 不变。补 all-new canonical missing-marker、all-new overlay ownership conflict及 mixed new-side invalid relation 回归；合法全 new retry仍 exit 0。

## Minor

### M1 — consumer 的非字符串 ID 走裸 `TypeError`，未满足三段式诊断契约

`validate_scan_envelope()` 在 `sdflow-issues/scripts/issues.py:1162` 先把 `item["id"]` 传入 regex；例如 producer 返回 `id=7` 时抛 `TypeError: expected string or bytes-like object`，而不是 `ValueError` 三段式 `ERROR/cause/fix`。安全性仍 fail-closed 且派生物未写，因此不升级为 Important；建议在 semantic parse 前显式校验 `id` 为 string并补 contract test。

## 原双轴 C/I 修复对账

| 原 finding / Task 4 条款 | 结论 | 证据 |
|---|---|---|
| Spec I1 / Standards C1：target marker/relation preflight | **PARTIAL** | old-side canonical/overlay missing marker、pure-legacy marker collision/重复 candidate 已在 registry 写前拒绝且 bytes 不变；all-new/mixed 的 new-side target仍漏检（本报告 I1）。 |
| Spec I2：合法 pure-legacy `A007` | **PASS** | consumer 接受 positive ASCII legacy alias，拒绝 Unicode/mixed digits/非法 spelling；promotion 输出 canonical `A7`。 |
| Spec I3 / Standards I1：schema 值域 | **PASS** | bug/todo 均拒绝 whitespace-only `module/summary`、空串 `change/batch`，并在派生物写前保持 INDEX/batches bytes；Unicode scalar 校验已对齐。 |
| Spec I4：arity 的 target/new-orphan 真值与 nonfatal boundary | **PASS** | old/new 出现在歧义 row 时 preflight fatal；被 frontmatter shadow 的冻结 row 不覆盖 current truth；与 old/new 无关且仍可判的 arity problem回显后成功。 |
| Standards I2 / DG-RI-1：canonical/pure-legacy/overlay × bug/todo parity | **PASS** | 六形态 direct snapshot 与各 producer scan contract 对齐；overlay bug/todo retag保持 legacy body/row bytes，updated snapshot直接供 reindex，read/parse=1，且 command 主路径 scan subprocess=0。 |
| Acceptance 1：two-pool direct bytes snapshot / call count / snapshot reuse | **PASS** | 每 dated 文件 read/parse=1，per-pool recorder scan=0，reindex使用 supplied snapshot。 |
| Acceptance 2：registry/provenance 状态矩阵 | **PARTIAL** | first/retry/orphan/double-key/unknown-source 分类通过；all-new retry 的 fatal relation gate未闭合（I1）。 |
| Acceptance 3：canonical/overlay/legacy retag 与 bytes preservation | **PASS（合法盘面）** | legacy row不 patch；BOM/CRLF/foreign namespace及 overlay frozen bytes保持。非法 all-new target仍由 I1 阻断结论。 |
| Acceptance 4：strict scan envelope | **PASS（功能门禁）** | 坏 JSON/缺键/错型/缺 file/enum/schema 值域均在派生物前 nonzero；M1仅是 ID 错型诊断格式缺口。 |
| Acceptance 5：四阶段 fault + nonfatal boundary | **PARTIAL** | registry/dated/INDEX/batches fault均 nonzero、含 stage+原命令且重跑收敛；all-new target fatal problem仍被 warning-only success（I1）。 |

## Verification

- `uv run --with pytest pytest -q sdflow-issues/tests/test_task4_rename_snapshot.py -W error` → `72 passed`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/test_mirror_consistency.py sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error` → `418 passed, 1 skipped`（Windows-only）。
- `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` → valid。
- `python3 hack/sync_principles.py --check` → `20` 个投放面一致。
- `git diff --check b899792..8ed9bc2` → PASS。
- 独立只读 PoC：provenance-matched all-new canonical missing-marker盘面回显 relation problem 后仍成功返回；numeric scan ID 触发裸 `TypeError`。

测试全绿不构成 Spec PASS：I1 直接违反 all-new retry 的 fail-closed/完全收敛目标态。修复后需重新 Spec review。
