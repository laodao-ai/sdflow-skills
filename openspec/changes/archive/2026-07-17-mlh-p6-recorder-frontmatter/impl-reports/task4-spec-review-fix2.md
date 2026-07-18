# Task 4 Fix 2 Spec Compliance Re-review

结论：**PASS**（Critical 0 / Important 0 / Minor 0）。固定范围 `94057a3..8169aeb`；固定审包 `task4-review-fix2-package.diff` 与 `git diff --binary 94057a3..8169aeb` byte-identical，SHA-256 均为 `8181fdab9ef0bb9728a2457b2f73ca54997eef8678a7ff6ec6dcf64eaa7e96f7`。

## Fix 1 剩余发现闭环

### 1. unreliable legacy arity 在 registry 写前 fatal — PASS

- `_reject_ambiguous_legacy_rows()` 不再以 old/new 字面是否出现作为唯一判据。7/8 列按既有兼容 grammar 检查 ID、required field、pool-specific enum 与 status；超过 8 列只在标准前八列独立可判且 trailing cells 不含 old/new 时保留为 nonfatal，短行、enum/status 错位、中间插 cell、target key 落入 trailing cells 均在 `cmd_batch_rename()` 的 preflight 阶段拒绝。
- 真实 CLI 回归覆盖“无 old/new 字面的中间插 cell”：exit 2、无 traceback、诊断含 `stage=preflight` 与原 `batch rename batch-old batch-new`，registry/dated/INDEX bytes 全不变。可判的 unrelated trailing-cell arity problem 仍回显并沿用默认成功语义，没有把批准的 nonfatal 边界缩掉。
- overlay 中被 frontmatter semantic owner shadow 的冻结 legacy row继续不参与当前 batch 真值推断，符合历史 row 只读、不覆盖 current frontmatter truth 的迁移语义。

### 2. provenance retry 对 `{old,new}` owned target 统一 relation preflight — PASS

- `retag_rename_snapshot()` 先从原 snapshot 取 `batch in {old_key,new_key}` 的 `relation_target_ids`，无论该文件是否仍有 old item，都在任何 registry/dated/INDEX/batches 写入前执行 marker/frontmatter relation gate；因此 all-new 不再因 `target_ids` 为空绕过门禁。
- all-new / mixed × canonical / overlay / pure-legacy 六类非法 target 均由真实 CLI 回归覆盖并保持 registry、全部 dated 文件与 INDEX bytes 不变；合法 provenance-matched all-old、mixed、all-new 盘面连续执行原命令两次均收敛，mode 保持 `retry` 且最终 items/INDEX 全为 new key。
- first、orphan、double-key、old/new 均缺失、unknown/mismatched source 的既有分类矩阵保持通过；fix2 未把 retry 扩成无 provenance 的静默吸收。

### 3. scan ID contract 与三段式 fatal diagnostic — PASS

- `validate_scan_envelope()` 在 semantic parse 前显式要求 string ID。`null`、number、list、object 均变成带 `scan item[0].id`、`ERROR: ...; cause: ...; fix: ...` 的受控 `ValueError`；真实 `reindex` 为 exit 2、无 traceback，且 INDEX/batches bytes 不变。
- 合法 pure-legacy ASCII alias `A007` 仍被 consumer 接受并保留 raw spelling，rename/promotion 才 canonicalize 为 `A7`；Arabic-Indic、mixed digits、多 prefix、小写和缺数字继续 fail-closed。修复没有把兼容读半场错误收紧成只接受 canonical spelling。

### 4. pure-legacy marker collision 定位诊断 — PASS

- target pure-legacy bug 先走 candidate-aware `_legacy_block_range()`，后走 document-wide structural gate。候选块内完整 marker pair 或 partial marker 都由同一条错误点名 target file、`id=B1`、实际 `line=` 与 `legacy marker collision`，外层恢复诊断补 `stage=preflight` 和原命令。
- 两类真实 CLI 回归均断言 nonzero、无 traceback，并确认 registry/dated/INDEX bytes 不变；通用 `marker-only legacy` 不再抢先吞掉 target ID/line。

## Task 4 全体 acceptance / tasks 4.1–4.5 对账

| 条款 | 结论 | 证据 |
|---|---|---|
| Acceptance 1 / 4.1–4.3：direct two-pool bytes snapshot | PASS | `read_rename_snapshot()` 直接 binary read 两池；每 dated 文件 read=1/parse=1，per-pool recorder scan=0；retag 后 `_reindex_core(snapshot=updated)` 不重读两池。 |
| Acceptance 2 / 4.4：registry-first provenance matrix | PASS | first、all-old/mixed/all-new retry、preexisting-new orphan、double key、两 key 皆无及 unknown/mismatched provenance 均有确定性矩阵；非法盘面 preflight 无写，合法 retry 幂等收敛。 |
| Acceptance 3 / 4.1、4.3：canonical/overlay/legacy retag + bytes preservation | PASS | bug/todo × canonical/pure-legacy/overlay 与 recorder producer contract 对齐；legacy row 不 patch，overlay frozen body/row 不变，BOM/CRLF/foreign sibling namespace 在 recorder span 外保真，updated snapshot 与派生输出一致。 |
| Acceptance 4 / 4.5：strict standalone scan envelope | PASS | 坏 JSON、缺键、容器错型、缺 file、ID/type/spelling、enum、nonblank/null/Unicode scalar 漂移均在覆盖 INDEX/batches 前 fatal；合法 `A007` 兼容保留。 |
| Acceptance 5 / 4.4–4.5：fault/retry/nonfatal boundary | PASS | registry、dated、INDEX、batches 四阶段 fault 均 nonzero，诊断含 stage + 原命令；解除 fault 后原命令收敛。只有与 retag 无关且 item 仍可判的 legacy problem 走回显 + 默认成功，target relation、batch 真值与所有写失败均不再 warning-only success。 |

## Verification

- `uv run --with pytest pytest -q sdflow-issues/tests/test_task4_rename_snapshot.py sdflow-buglist/tests/test_mirror_consistency.py -W error` → `98 passed`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error` → `437 passed, 1 skipped`（Windows-only）。
- `uv run --with pytest pytest -q` → `1611 passed, 1 skipped`。
- `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` → valid。
- `python3 hack/sync_principles.py --check` → `20` 个投放面一致。
- `git diff --check 94057a3..8169aeb` → PASS。

四项 fix1 遗留均已按目标态闭合，且 Task 4 的 snapshot、provenance、bytes、strict envelope、fault/retry 与 fatal/nonfatal 边界没有缩水。Spec 轴允许进入 Task 4 checkpoint。
