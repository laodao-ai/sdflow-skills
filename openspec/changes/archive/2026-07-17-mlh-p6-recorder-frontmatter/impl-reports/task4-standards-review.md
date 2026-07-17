# Task 4 Standards Compliance Review

结论：**BLOCKED**

- 固定审包：`impl-reports/task4-review-package.diff`（SHA-256 `ee7acad08becb9a408cf3b233e094d5a093c19f94b29d3e773a3ccdc0fd09475`）
- 固定范围：`d2f9f85e2037c27c35463b139bf75b3a991ccffe..b6242b8e247638255a56cbb6638c69a5464aab88`
- Findings：Critical 1 / Important 2 / Minor 0
- 门禁：存在 Critical/Important，Task 4 不可通过 standards review。

## Checklist 适用性

workflow root 为 `/Users/cheneyzhao/.sdflow/workflow`。已检查 `code-checklists/README.md`、`code-review-base.md` 与 `domains/` 注册表；本变更是 Python CLI + Markdown/frontmatter 数据管道，现有领域 delta 仅覆盖 backend、backend-go、embedded、embedded-ml307c、embedded-esp32，**领域清单未覆盖**。本次依据仓库规范、通用 CR-01~09、`superpowers-plan.md` Global Constraints/Task 4，以及 `SW-RI-1`、`SW-RI-3`、`SW-RI-4`、`DG-RI-1` 目标态审查。

## Findings

### Critical C1 — legacy rename promotion 未执行 marker collision / 唯一 block 的写前门禁

- 位置：`sdflow-issues/scripts/issues.py:835`、`sdflow-issues/scripts/issues.py:842`、`sdflow-issues/scripts/issues.py:906`
- 证据：`_body_with_legacy_bug_markers()` 只判断 `raw_id` 是否存在于 `document["legacy_blocks"]`，随后直接插入外围 marker；它没有像 recorder writer 的 `_legacy_block_range()` 一样，逐行拒绝候选块内任一精确 marker，也无法发现被 `block_ranges()` 字典折叠掉的同 ID 多候选块。`retag_rename_snapshot()` 随后把该结果作为合法 updated snapshot 交给写盘与 reindex。
- 可复现结果：构造 batch-old 的 pure-legacy `B1`，其唯一 prose block 内预存 `<!-- sdflow-issue-block:start id=B9 -->`。执行真实 `batch rename batch-old batch-new` 返回 `0`，stdout 报 `items_changed=1`；dated 文件同时保留内层 `B9` start marker并新增外围 `B1` markers。紧接着 `reindex --strict` 才以 `marker 嵌套：B1 → B9` 返回非零。也就是说 mutation 已经把目标文件写成违反新格式 marker invariant 的盘面，并误报 rename 成功。
- 目标态依据：`spec-workflow/spec.md:22`、`:70-72` 要求 promotion 在任何写盘前扫描候选 legacy block，任一精确 marker 或 block ownership 歧义必须 fail-closed；`tasks.md:31`、`:34-35` 要求 pure legacy overlay promotion 永不猜测改写，影响 retag 判定的 fatal problem 不得 warning-only success；Global Constraints 要求历史 writer fail-closed。
- 修复：在 `issues.py` 增加/复用与 per-pool recorder 行为等价的 strict legacy candidate resolver：按 semantic ID 计算候选 heading，要求恰好一个范围，并在该范围逐行调用 `_match_marker_line()`；任何预存 marker、重复候选或边界歧义都在 registry 写入前抛三段式错误。`_body_with_legacy_bug_markers()` 只能消费这个已验证 range。补真实 CLI 回归：preexisting start/end marker、重复同 ID block 各自 nonzero，registry/dated/INDEX/batches 四者 bytes 均不变，诊断含 `stage=preflight` 与可复制原命令。

### Important I1 — scan envelope validator 未覆盖 recorder schema 的非空/空值 canonical 约束

- 位置：`sdflow-issues/scripts/issues.py:1028-1039`
- 证据：`validate_scan_envelope()` 只检查 `module/summary/time` 是 `str`，只检查 `change/batch` 是 `str|null`。实测它接受 `module="   "`、`summary="\t\n"`、`change=""`、`batch=""`；这些值均违反同文件 `_validated_recorder_model()` 的 schema 规则，但会作为有效 producer snapshot 进入 reindex。
- 目标态依据：`spec-workflow/spec.md:10` 要求 `module/summary` 至少一个非空白 scalar，`change/batch` 无值只能是 JSON `null`；`:24`、`:280` 要求 consumer 对 item 字段类型和值域按 recorder schema fail-closed，并在写 INDEX/batches 前拒绝协议漂移；Task 4 的 scan envelope 门禁不能只覆盖枚举与基础类型。
- 修复：把 consumer item validation 对齐 recorder schema：验证所有 string 为 Unicode scalar、`module/summary` nonblank、`change/batch` 为 `null` 或非空 string，并保持 `id/file` 与 pool-specific enum 校验。为 bug/todo 两池增加上述四类负例，断言 `_reindex_core()` 抛错且既有 INDEX/batches bytes 不变。

### Important I2 — DG-RI-1 要求的 overlay parity / retag 契约没有回归覆盖

- 位置：`sdflow-issues/tests/test_task4_rename_snapshot.py:256`、`sdflow-issues/tests/test_task4_rename_snapshot.py:306`
- 证据：direct snapshot parity 测试名与 fixture 仅覆盖 canonical bug + pure-legacy todo；rename cutover 测试仅覆盖 canonical bug，retag bytes 测试仅覆盖 pure legacy。没有以同一 overlay fixture 对比 `issues.py::read_rename_snapshot()` 与 recorder `scan --json` contract，也没有覆盖 overlay retag 后 frozen legacy row、frontmatter current value、marker/body bytes 与 reindex snapshot 的一致性。
- 目标态依据：`determinism-guards/spec.md:8`、`:24-26` 明确要求 canonical/pure-legacy/overlay 同 fixture 的 golden equivalence；`tasks.md:31-33` 要求 canonical/overlay/legacy retag 与 overlay/legacy 混合 bytes-preservation/call-count；CR-09 要求新数据流的关键错误与迁移形态有确定性测试。
- 修复：把 parity 测试参数化为 canonical、pure-legacy、overlay，分别覆盖 bug/todo；为 overlay batch-old item 执行真实 rename，断言 legacy row/prose/sibling namespace bytes 不变、只更新 recorder frontmatter、`scan --json` 与 updated snapshot 字段一致、每文件 read/parse=1、scan subprocess=0、reindex 不重读。

## 已核对通过的目标态行为

- `read_rename_snapshot()` 直接 binary read 两池，定向 instrumentation 覆盖每文件 read=1/parse=1；rename 路径 recorder scan=0，`_reindex_core(snapshot=...)` 不调用 `read_pool()`。
- registry-first 分类覆盖 first、provenance 精确匹配的全 old/混合/全 new retry，以及双 key、两者皆无、provenance 缺失/不匹配、preexisting new orphan 的 fail-closed。
- canonical 与已覆盖的 pure-legacy 路径不 patch legacy table row；BOM/CRLF/external sibling 的已覆盖 fixture保持 recorder span 外 bytes。
- registry、dated、INDEX、batches 四阶段 fault injection 均验证 nonzero、`stage=`、原命令与解除 fault 后重试收敛。
- generic `reindex` 默认 problems 可观测但 exit 0、`--strict` problems 非空时 nonzero 的既有门禁未放宽；全 recorder 套件相关 strict tests 通过。

## 验证

- `uv run --with pytest pytest -q sdflow-buglist/tests/test_mirror_consistency.py sdflow-issues/tests/test_task4_rename_snapshot.py -W error` → `43 passed`
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error` → `382 passed, 1 skipped`
- `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` → valid
- `git diff --check d2f9f85..b6242b8` → PASS
- 额外只读 PoC：marker collision rename → `returncode=0`，随后 `reindex --strict` → `returncode=1`；scan envelope schema PoC 的 whitespace-only `module/summary` 与 empty-string `change/batch` 均被错误接受。
