# Task 4 Spec Compliance Review — single-snapshot rename / provenance / fail-closed reindex

结论：**FAIL**（4 个 Important；无 Critical）。固定范围 `d2f9f85..b6242b8`；机械审包 `task4-review-package.diff` 与 `git diff d2f9f85 b6242b8` byte-identical，SHA-256 均为 `ee7acad08becb9a408cf3b233e094d5a093c19f94b29d3e773a3ccdc0fd09475`。

## Critical

无。

## Important

### I1 — direct rename 绕过 recorder mutation 的 marker/relation fail-closed gate

- **位置**：`sdflow-issues/scripts/issues.py:868-923`，尤其 `:906-915`。`retag_rename_snapshot()` 直接渲染并返回 bytes，只检查 legacy bug 是否存在一个按 raw ID 命中的 `legacy_blocks` 条目；它没有执行 bug/todo writer 已有的 `_reject_document_mutation()`、semantic-unique legacy block/collision preflight，也没有对 rendered candidate 重新 parse 后拒绝 target structural problem。
- **违反条款**：`tasks.md` 4.1（issues 需具备等价 relation helpers，pure legacy promotion 不得猜写）、4.5（只有与 retag 无关且 item 仍可判的 legacy problem 才能继续）；`specs/spec-workflow/spec.md` SW-RI-1（marker ownership/partial-promotion conflict fatal）及 legacy block collision/无法安全包裹场景；Task 4 acceptance 3。
- **可复现证据**：构造 canonical bug `B1(batch=old)` 但正文无 B1 marker，`parse_recorder_document()` 给出 `frontmatter 有 B1 但缺 marker block`；当前 `retag_rename_snapshot()` 仍返回 `batch=new`，对其 `rendered` 再 parse 后同一 structural problem 仍存在。真实命令会在 registry-first 之后写下该无效 dated document，并可继续生成派生物。legacy block 内预存 marker、semantic alias 多候选等路径同样没有等价 preflight。
- **修复**：在 registry 写入前完成全 snapshot target-aware preflight：复用/镜像 `_reject_document_mutation`、`_legacy_block_range`/marker collision 与 rendered-candidate relation 校验；target canonical/overlay 缺 marker、target legacy block 缺失/多候选/预存 marker 必须作为 fatal。只把明确与 target retag 无关的 legacy arity/block problem保留为可观测 nonfatal。增加 canonical、overlay、pure-legacy 三类拒写回归，断言 registry/dated/INDEX/batches 全部 bytes 不变。

### I2 — strict scan consumer 错拒合法 pure-legacy raw ID，破坏 reindex 兼容性

- **位置**：`sdflow-issues/scripts/issues.py:1027-1043`，具体 `:1033` 无条件调用 `canonical_id()`。
- **违反条款**：proposal `What Changes` 对孤立 legacy raw ID 的兼容语义（首次 mutation 后才 canonicalize）；`specs/spec-workflow/spec.md` 的 pure-legacy dual-read / raw alias promotion 场景；`tasks.md` 4.5；Global Constraints“历史 item 仍可操作”。
- **可复现证据**：bug/todo producer 对尚未 promotion 的合法 legacy row `A007` 会在 `scan --json` 保持输出 `id=A007`；把该合法 envelope 交给 `validate_scan_envelope()`，当前实现以 `ID is not canonical ASCII spelling` 拒绝。于是独立 `issues.py reindex` 会把可读历史盘面误判为 consumer protocol drift。
- **修复**：consumer ID 合同需区分“canonical frontmatter ID”与“合法 legacy scan ID”。对 producer envelope 使用 ASCII-only legacy semantic validator（允许单字母大写 + ASCII digits/leading zero，但继续拒绝 Unicode digits、小写、多字母、空号），保留原 raw ID 以维持 scan/CLI 兼容；promotion/rename 后仍由 writer 输出 canonical ID。补 pure-legacy `A007` reindex 成功、rename 后 `A7`、Unicode/mixed digits 失败的端到端测试。

### I3 — consumer envelope 未执行 schema 的非空/null 值域，坏协议仍会覆盖派生物

- **位置**：`sdflow-issues/scripts/issues.py:1027-1043`，具体 `:1034-1039` 只检查大部分字段为 string，未检查 `module/summary` 至少含一个非 whitespace scalar，也允许 `change/batch == ""`。
- **违反条款**：`specs/spec-workflow/spec.md` SW-RI-1 schema（`module/summary` 非空；`change/batch` 无值必须为 null、空串非法）、SW-RI-3 strict consumer envelope（字段类型和值域与 schema 一致，写 INDEX/batches 前 fail-closed）；`tasks.md` 4.5；Task 4 acceptance 4。
- **可复现证据**：`validate_scan_envelope()` 当前分别接受 `module=""`、`summary="   "`、`change=""`、`batch=""`。这些 payload 会继续进入 `_reindex_core()`，从而违反“consumer drift 在覆盖 INDEX/batches 前 nonzero”。现有 contract tests只覆盖坏 JSON、缺键、容器错型、缺 file 与 enum drift，未覆盖这些 schema 值域。
- **修复**：集中实现 item-level schema validator：`module/summary` 必须至少一个非 whitespace Unicode scalar，`change/batch` 只能是 null 或非空 string（与 frontmatter reader 的空串规则一致），并保留现有 pool-specific enum、status、file、ID 检查。为 bug/todo 两种 envelope 各加派生物 bytes-preservation 测试。

### I4 — arity problem 不分“仍可判”与“影响 batch 判定”，可绕过 orphan/unknown-source gate

- **位置**：`sdflow-issues/scripts/issues.py:805-817` 收集所有 parser problems；`:868-923` 原样携带；`:1941-1948` 在 provenance classification 前不做 fatal/nonfatal 分层。`_legacy_item_from_row()`（`:626-637`）对任意 `len(cells) >= 5` 按固定位置取值，即使额外 `|` 已使字段错位。
- **违反条款**：`tasks.md` 4.4、4.5；`specs/spec-workflow/spec.md` SW-RI-3“只有与 retag 无关、仍可判 item 的 legacy 非致命 problem 可成功；任何影响 item/batch 判定的 fatal problem 必须 nonzero”；Task 4 acceptance 2、5 及非致命 legacy problems 默认语义。
- **可复现证据**：9 列 legacy row `B1` 的真实末列为 `target-new`，但 summary 中额外 `|` 使当前 parser 得到 `priority=injected,status=P2,...,batch=chg`，只记录 `B1 行 arity 异常：9 列`。随后 `classify_batch_rename({target-old}, ..., target-old, target-new)` 返回 `first`，没有发现 preexisting new orphan；命令可 registry-first 改名后 exit 0，却未证明 item/batch 真值收敛。
- **修复**：在 rename preflight 为 legacy problem 建明确分类。7 列历史无 batch可按既有兼容语义判定；列错位、缺少判定字段、非法 enum/ID 或任何无法可靠证明 old/new 归属的 row 必须 fatal，并在 registry 写入前给 file/row/stage/original-command。保留“非目标、字段仍可可靠判定”的 block/arity problem 回显 + 默认成功语义；增加 target old、隐藏 new orphan、unrelated nonfatal 三组测试。

## Minor

无。

## Acceptance / tasks 对账

| 条款 | 结论 | 证据 |
|---|---|---|
| Acceptance 1 / 4.1–4.3：direct two-pool bytes snapshot；dated read/parse=1；scan=0；updated snapshot reindex | **PARTIAL** | 主路径与计数测试成立；但 relation 等价与 target mutation preflight 缺失（I1），4.3 要求的 overlay + nonempty-problems golden equivalence 也未形成完整覆盖。 |
| Acceptance 2 / 4.4：registry-first provenance；first/all-old/mixed/all-new retry/orphan/double-key/unknown source | **PARTIAL** | 正常矩阵实现正确；歧义 arity 可隐藏 new orphan 并误分类 first（I4）。 |
| Acceptance 3 / 4.1、4.3：canonical/overlay/legacy retag；legacy row/BOM/CRLF/sibling namespace 保真 | **PARTIAL** | bytes splice 与 frozen row 主路径成立；target marker/relation 异常仍会被写入（I1）。 |
| Acceptance 4 / 4.5：strict consumer envelope 在派生物前 fail-closed | **PARTIAL** | 坏 JSON/缺键/容器错型/缺 file/enum 已守住；合法 legacy alias 被误拒（I2），schema 非空/null 值域被漏放（I3）。 |
| Acceptance 5 / 4.4–4.5：registry/dated/INDEX/batches 四阶段 nonzero + stage + original command + rerun convergence；legacy nonfatal 默认语义 | **PARTIAL** | 四阶段 failure 包装与重跑主路径成立；problem 分层过宽，影响 batch 判定的 arity 仍可成功（I4）。 |

## Verification

- `uv run --with pytest pytest -q sdflow-buglist/tests/test_mirror_consistency.py sdflow-issues/tests/test_task4_rename_snapshot.py -W error` → `43 passed`。
- `uv run --with pytest pytest -q sdflow-issues/tests/ -W error` → `154 passed`。
- `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` → valid。
- `git diff --check d2f9f85 b6242b8` → PASS。
- 独立只读函数 probe 复现：missing-marker retag 后仍输出 invalid relation；pure-legacy `A007` consumer 被误拒；四种非法 schema 值被接受；9 列 row 隐藏 target-new orphan 后被分类为 `first`。

测试全绿不构成 PASS：上述四项均直接违反 Task 4 的 fail-closed/兼容性目标态，修复并补齐回归后需重新 Spec review。
