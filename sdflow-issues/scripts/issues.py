#!/usr/bin/env python3
"""issues.py — sdflow-issues 的**跨池薄入口**（reindex / batch / sweep / rename）。

（dedupe-issues-scripts-shared-layer · adr/0027）issues 台账三脚本合一后，bug/todo/issues
共享的执行逻辑（frontmatter mechanics、recorder lock、路径解析、文档解析/渲染等）已上移唯一
共享源 `sdflow_issues_core`；本文件只保留 issues 独占的**跨池**命令：
  - `reindex`：从 dated 文件重建 `openspec/issues/INDEX.md` + 同步 `openspec/issues/batches.md` 状态
  - `batch add/set-status/rename/lint`：维护批次注册表
  - `sweep`：把某 change 的未分批非终态项一键分诊入批次

薄入口顶部 `sys.path.insert(...)`（AD-1）令 file-based 测试加载可解 package import。
"""

import argparse
from contextlib import contextmanager, redirect_stdout
import glob
import io
import json
import os
import re
import secrets
import shlex
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
try: sys.stdin.reconfigure(encoding="utf-8", errors="strict")
except Exception: pass
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sdflow_issues_core import *  # noqa: F401,F403  re-export 共享 helper（tests 按名 getattr 取用）
import sdflow_issues_core as _core
from sdflow_issues_core import (  # 显式取 underscore 前缀的共享 helper（`import *` 不带下划线名）
    _legacy_semantic_id_key,
    _validated_recorder_model,
    _render_recorder_document,
    _match_marker_line,
    _validate_unicode_scalar,
    _die,
    _reject_line_unsafe,
    _scan_legacy_block_range,  # 唯一命名 package 单一源的 legacy 块边界扫描（AD-3 pool-agnostic）
    _legacy_block_range,       # core 的中文格式化 sibling；本文件不调，仅经 re-export 供 thinness 守解析到 core
    LegacyBlockError,          # 扫描抛的结构化 sentinel（caller 各自格式化 fix 文案）
)


# ── 同目录 spawn 常量（AD-2） ─────────────────────────────────────────────────
# 三合一后 buglist.py / todolist.py 与本文件是**同一目录**的薄入口（sdflow-issues/scripts/），
# 不再是安装后的 sibling skill 目录。故按本脚本自身位置**同目录**定位它们；`reindex`/`sweep`
# 靠 `subprocess.run` 真跑这两个薄入口的 `scan --json` 契约（不 import 其内部函数）。
# `--root` 是完全独立的另一概念：目标项目根（存 openspec/issues/... 的仓库），不可混淆。
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BUGLIST_SCRIPT = os.path.join(SCRIPT_DIR, "buglist.py")
TODOLIST_SCRIPT = os.path.join(SCRIPT_DIR, "todolist.py")

# PRIORITIES：batch lint 的 `优先级:` 前导 token 集合——单一源 = core 的 BUG_STRATEGY 有序枚举。
PRIORITIES = list(BUG_STRATEGY.specific_values_ordered)


# ══════════════════════════════════════════════════════════════════════════════
# 跨池 rename snapshot / retag（issues 独占）
# ══════════════════════════════════════════════════════════════════════════════

def read_rename_snapshot(root, instrumentation=None):
    """Directly materialize the two-pool bytes snapshot used by batch rename.

    Every dated document is opened once and parsed once.  The returned document
    records retain the original bytes and parser spans/model so a caller can
    retag in memory and splice only the recorder namespace.
    """
    root = os.path.realpath(os.fspath(root))
    counters = instrumentation if instrumentation is not None else {"reads": {}, "parses": {}}
    counters.setdefault("reads", {})
    counters.setdefault("parses", {})
    pools = {
        pool: (f"{spec.issues_dir}/*.md", spec.legacy_dir_glob)
        for pool, spec in POOL_SPEC.items()
    }
    documents = []
    items = []
    problems = []
    semantic_occurrences = {}
    seen_paths = set()
    for pool, patterns in pools.items():
        for pattern in patterns:
            for path in sorted(glob.glob(os.path.join(root, pattern))):
                path = os.path.normpath(path)
                real = os.path.realpath(path)
                if real in seen_paths:
                    continue
                seen_paths.add(real)
                rel = os.path.relpath(path, root).replace(os.sep, "/")
                try:
                    with open(path, "rb") as stream:
                        raw = stream.read()
                    counters["reads"][rel] = counters["reads"].get(rel, 0) + 1
                    document = parse_recorder_document(raw, pool)
                    counters["parses"][rel] = counters["parses"].get(rel, 0) + 1
                except (OSError, ValueError) as exc:
                    message = str(exc)
                    detail = message[len("ERROR: "):] if message.startswith("ERROR: ") else message
                    raise ValueError(f"ERROR: file={path}: {detail}") from None
                record = dict(document)
                record.update({"pool": pool, "path": path, "file": rel})
                documents.append(record)
                problems.extend(f"{pool}:{rel}: {problem}" for problem in document["problems"])
                for item_id, original in document["effective_items"].items():
                    item = dict(original)
                    item.update({"id": item_id, "pool": pool, "file": rel})
                    items.append(item)
                    key = _legacy_semantic_id_key(item_id)
                    semantic_occurrences.setdefault(key, []).append((item_id, pool, rel))
    duplicates = {key: values for key, values in semantic_occurrences.items() if len(values) > 1}
    if duplicates:
        key, values = sorted(duplicates.items(), key=lambda pair: str(pair[0]))[0]
        rendered = ", ".join(f"{raw}@{pool}:{rel}" for raw, pool, rel in values)
        raise ValueError(f"ERROR: semantic ID 重复; cause: repository semantic ID conflict {key}: {rendered}; fix: resolve all aliases/pools before retry")
    return {"root": root, "documents": documents, "items": items, "problems": problems}


def _body_with_legacy_bug_markers(document, targets):
    """Wrap promoted legacy bug blocks without rewriting their bytes."""
    insertions = {}
    line_offsets = [0]
    for line in document["lines"]:
        line_offsets.append(line_offsets[-1] + len(line.encode("utf-8")))
    ranges = []
    for raw_id, canonical in targets:
        start, end = _rename_legacy_block_range(document, raw_id)
        ranges.append((start, end, canonical))
    for start, end, canonical in sorted(ranges):
        insertions.setdefault(line_offsets[start], []).append(
            f"<!-- sdflow-issue-block:start id={canonical} -->".encode("utf-8") + document["eol"]
        )
        insertions.setdefault(line_offsets[end], []).append(
            f"<!-- sdflow-issue-block:end id={canonical} -->".encode("utf-8") + document["eol"]
        )
    body = document["body"]
    rendered = []
    cursor = 0
    for offset in sorted(insertions):
        rendered.append(body[cursor:offset])
        rendered.extend(insertions[offset])
        cursor = offset
    rendered.append(body[cursor:])
    return b"".join(rendered)


def _canonical_from_legacy_key(key):
    return f"{key[0]}{key[1]}"


def _rename_legacy_block_range(document, raw_id):
    """Rename-path wrapper: delegate to the single-source scan, format English fix.

    The block boundary scan lives once in ``sdflow_issues_core._scan_legacy_block_range``
    (pool-agnostic, prose-free).  This wrapper is the issues-owned batch-rename
    caller: it catches the structured ``LegacyBlockError`` and emits the
    rename-path-specific English fix text ("rerun the original batch rename
    command"), matching issues' batch-rename error family.  The core sibling
    ``_legacy_block_range`` formats the same failures in Chinese via
    ``_frontmatter_error``; only the fix prose differs, never the scan.
    """
    try:
        return _scan_legacy_block_range(document, raw_id)
    except LegacyBlockError as exc:
        if exc.kind == "ambiguous":
            raise ValueError(
                f"ERROR: file={document['path']} legacy block 无法安全包裹; "
                f"cause: id={exc.raw_id} candidates={exc.candidates}; "
                "fix: repair to exactly one legacy block, then rerun the original batch rename command"
            ) from None
        raise ValueError(
            f"ERROR: file={document['path']} legacy marker collision; "
            f"cause: id={exc.raw_id} line={exc.line}; "
            "fix: remove or escape the preexisting marker, then rerun the original batch rename command"
        ) from None


def _reject_target_document_problems(document, target_ids):
    """Fail closed on target marker/ownership relations before any registry write."""
    if POOL_SPEC[document["pool"]].requires_block:
        frontmatter_keys = {
            _legacy_semantic_id_key(item_id)
            for item_id in (document["model"]["items"] if document["model"] else {})
        }
        # A pure-legacy promotion candidate owns its heading block.  Inspect it
        # before the document-wide structural summary so a preexisting complete
        # or partial marker cannot hide the target ID and collision line behind
        # a generic ``marker-only legacy`` diagnostic.
        for raw_id in target_ids:
            if _legacy_semantic_id_key(raw_id) not in frontmatter_keys:
                _rename_legacy_block_range(document, raw_id)
    structural = [
        problem for problem in document["problems"]
        if "marker" in problem or "frontmatter" in problem
    ]
    if structural:
        raise ValueError(
            f"ERROR: file={document['path']} marker/ownership 结构非法; "
            f"cause: {structural[0]}; fix: repair the target relation, then rerun the original batch rename command"
        )


def _reject_ambiguous_legacy_rows(snapshot, old_key, new_key):
    """Reject rows that cannot prove old/new batch truth; retain unrelated warnings."""
    for document in snapshot["documents"]:
        section = document["section"]
        if not section:
            continue
        specific_field, specific_values, status_values = RECORDER_POOL_CONFIG[document["pool"]]
        frontmatter_keys = {
            _legacy_semantic_id_key(item_id)
            for item_id in (document["model"]["items"] if document["model"] else {})
        }
        for index in range(section["rows_start"], section["rows_end"]):
            cells = [cell.strip() for cell in document["lines"][index].strip().strip("|").split("|")]
            raw_id = cells[0] if cells else "?"
            if _legacy_semantic_id_key(raw_id) in frontmatter_keys:
                continue
            if len(cells) not in (7, 8):
                harmless_trailing = (
                    len(cells) > 8
                    and _legacy_semantic_id_key(raw_id) is not None
                    and bool(cells[1].strip())
                    and bool(cells[2].strip())
                    and cells[3] in specific_values
                    and cells[4] in status_values
                    and old_key not in cells[8:]
                    and new_key not in cells[8:]
                )
                if not harmless_trailing:
                    raise ValueError(
                        f"ERROR: file={document['path']} legacy row batch truth ambiguous; "
                        f"cause: id={raw_id} line={index + 1} arity={len(cells)} cannot prove batch truth for {old_key!r}/{new_key!r}; "
                        "fix: repair the legacy row arity, then rerun the original batch rename command"
                    )
                continue
            if _legacy_semantic_id_key(raw_id) is None:
                raise ValueError(
                    f"ERROR: file={document['path']} legacy row ID invalid; cause: id={raw_id!r} line={index + 1}; "
                    "fix: repair the ASCII semantic ID, then rerun the original batch rename command"
                )
            if not cells[1].strip() or not cells[2].strip():
                raise ValueError(
                    f"ERROR: file={document['path']} legacy row required field empty; cause: id={raw_id} line={index + 1}; "
                    "fix: repair module/summary, then rerun the original batch rename command"
                )
            if cells[3] not in specific_values or cells[4] not in status_values:
                raise ValueError(
                    f"ERROR: file={document['path']} legacy row enum invalid; "
                    f"cause: id={raw_id} line={index + 1} {specific_field}={cells[3]!r} status={cells[4]!r}; "
                    "fix: repair the legacy enum, then rerun the original batch rename command"
                )


def _validate_rendered_rename_relation(document, model, body, canonical_ids):
    """Validate the already-parsed mutation components without a second document parse."""
    try:
        lines = body.decode("utf-8").splitlines(keepends=True)
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"ERROR: file={document['path']} rendered candidate encoding invalid; cause: {exc}; "
            "fix: repair the target bytes, then rerun the original batch rename command"
        ) from None
    marker_blocks, structural = marker_block_ranges(lines)
    if POOL_SPEC[document["pool"]].requires_block:
        for item_id in model["items"]:
            if item_id not in marker_blocks:
                structural.append(f"frontmatter item lacks marker block: {item_id}")
    for item_id in marker_blocks:
        if item_id not in model["items"]:
            structural.append(f"marker block lacks frontmatter item: {item_id}")
    for canonical in canonical_ids:
        if canonical not in model["items"]:
            structural.append(f"frontmatter item missing: {canonical}")
        if POOL_SPEC[document["pool"]].requires_block and canonical not in marker_blocks:
            structural.append(f"marker block missing: {canonical}")
    if structural:
        raise ValueError(
            f"ERROR: file={document['path']} rendered candidate relation invalid; "
            f"cause: {structural[0]}; fix: repair the target relation, then rerun the original batch rename command"
        )
    return body


def retag_rename_snapshot(snapshot, old_key, new_key):
    """Return an updated in-memory snapshot and per-document rendered bytes."""
    _reject_ambiguous_legacy_rows(snapshot, old_key, new_key)
    updated_documents = []
    updated_items = []
    original_by_file = {}
    for item in snapshot["items"]:
        original_by_file.setdefault(item["file"], {})[item["id"]] = item
    for document in snapshot["documents"]:
        record = dict(document)
        original_items = original_by_file.get(document["file"], {})
        relation_target_ids = [
            item_id for item_id, item in original_items.items()
            if item.get("batch") in {old_key, new_key}
        ]
        target_ids = [item_id for item_id, item in original_items.items() if item.get("batch") == old_key]
        if relation_target_ids:
            _reject_target_document_problems(document, relation_target_ids)
        if not target_ids:
            record["rendered"] = document["raw"]
            updated_items.extend(dict(item) for item in original_items.values())
            updated_documents.append(record)
            continue
        old_model = document["model"]
        model = {
            "schema": 1,
            "pool": document["pool"],
            "mode": "overlay" if old_model is None else old_model["mode"],
            "items": {key: dict(value) for key, value in (old_model["items"].items() if old_model else ())},
        }
        frontmatter_keys = {_legacy_semantic_id_key(item_id) for item_id in model["items"]}
        marker_targets = []
        effective = {item_id: dict(item) for item_id, item in original_items.items()}
        for raw_id in target_ids:
            key = _legacy_semantic_id_key(raw_id)
            canonical = _canonical_from_legacy_key(key)
            promoted_item = effective.pop(raw_id)
            promoted_item["id"] = canonical
            promoted_item["batch"] = new_key
            effective[canonical] = promoted_item
            promoted = dict(promoted_item)
            promoted.pop("id", None)
            promoted.pop("pool", None)
            promoted.pop("file", None)
            model["items"][canonical] = promoted
            if POOL_SPEC[document["pool"]].requires_block and key not in frontmatter_keys:
                marker_targets.append((raw_id, canonical))
        body = _body_with_legacy_bug_markers(document, marker_targets) if marker_targets else document["body"]
        model = _validated_recorder_model(model)
        _validate_rendered_rename_relation(
            document, model, body,
            [_canonical_from_legacy_key(_legacy_semantic_id_key(item_id)) for item_id in target_ids],
        )
        rendered = _render_recorder_document(document, model, body)
        record.update({"model": model, "body": body, "effective_items": {
            item_id: {key: value for key, value in item.items() if key not in {"id", "pool", "file"}}
            for item_id, item in effective.items()
        }})
        record.update({"pool": document["pool"], "path": document["path"], "file": document["file"], "rendered": rendered})
        updated_items.extend(effective.values())
        updated_documents.append(record)
    return {
        "root": snapshot["root"],
        "documents": updated_documents,
        "items": updated_items,
        "problems": list(snapshot["problems"]),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 跨池 read（scan --json 子进程 join）
# ══════════════════════════════════════════════════════════════════════════════

class CrossPoolIDConflict(RuntimeError):
    """D9 防护网触发：同一 ID 同时出现在 bug 池与 todo 池。"""


class ReindexStageError(RuntimeError):
    def __init__(self, stage, cause):
        super().__init__(str(cause))
        self.stage = stage
        self.cause = cause


def validate_scan_envelope(payload, pool):
    """Validate the standalone recorder ``scan --json`` consumer contract."""
    if pool not in RECORDER_POOL_CONFIG:
        raise ValueError(f"ERROR: scan envelope pool 非法: {pool!r}; cause: unknown consumer pool; fix: use bug or todo")
    try:
        data = json.loads(payload)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"ERROR: scan JSON 非法; cause: {exc}; fix: repair/reinstall the recorder producer and retry") from None
    if not isinstance(data, dict):
        raise ValueError("ERROR: scan envelope 非法; cause: top-level must be object; fix: repair/reinstall the recorder producer and retry")
    items_key = POOL_SPEC[pool].scan_output_key
    if items_key not in data or not isinstance(data[items_key], list):
        raise ValueError(f"ERROR: scan envelope {items_key} 非法; cause: required list missing or wrong type; fix: repair/reinstall the recorder producer and retry")
    if "problems" not in data or not isinstance(data["problems"], list):
        raise ValueError("ERROR: scan envelope problems 非法; cause: required list missing or wrong type; fix: repair/reinstall the recorder producer and retry")
    if any(not isinstance(problem, str) for problem in data["problems"]):
        raise ValueError("ERROR: scan envelope problems 非法; cause: every problem must be string; fix: repair/reinstall the recorder producer and retry")
    specific_field, specific_values, status_values = RECORDER_POOL_CONFIG[pool]
    required = {"id", "module", "summary", specific_field, "status", "time", "change", "batch", "file"}
    for index, item in enumerate(data[items_key]):
        if not isinstance(item, dict) or not required <= set(item):
            missing = sorted(required - set(item)) if isinstance(item, dict) else sorted(required)
            raise ValueError(f"ERROR: scan item[{index}] 字段非法; cause: missing={missing}; fix: repair/reinstall the recorder producer and retry")
        if not isinstance(item["id"], str):
            raise ValueError(
                f"ERROR: scan item[{index}].id 类型非法; cause: expected string, got {type(item['id']).__name__}; "
                "fix: repair/reinstall the recorder producer and retry"
            )
        semantic_key = _legacy_semantic_id_key(item["id"])
        if semantic_key is None or semantic_key[1] < 1:
            raise ValueError(
                f"ERROR: scan item[{index}].id 非法; cause: expected ID with one ASCII uppercase prefix and positive ASCII digits, got {item['id']!r}; "
                "fix: repair/reinstall the recorder producer and retry"
            )
        for field in ("module", "summary", "time", "file", specific_field, "status"):
            if not isinstance(item[field], str) or (field == "file" and not item[field]):
                raise ValueError(f"ERROR: scan item[{index}].{field} 类型非法; cause: required non-empty string for file and string otherwise; fix: repair/reinstall the recorder producer and retry")
            try:
                _validate_unicode_scalar(item[field], field, item["id"])
            except ValueError as exc:
                raise ValueError(
                    f"ERROR: scan item[{index}].{field} 值域非法; cause: {exc}; "
                    "fix: repair/reinstall the recorder producer and retry"
                ) from None
        for field in ("module", "summary"):
            if not item[field].strip():
                raise ValueError(
                    f"ERROR: scan item[{index}].{field} 值域非法; cause: required string must contain a non-whitespace scalar; "
                    "fix: repair/reinstall the recorder producer and retry"
                )
        for field in ("change", "batch"):
            if item[field] is not None and (not isinstance(item[field], str) or item[field] == ""):
                raise ValueError(f"ERROR: scan item[{index}].{field} 类型非法; cause: expected non-empty string or null; fix: repair/reinstall the recorder producer and retry")
            if item[field] is not None:
                try:
                    _validate_unicode_scalar(item[field], field, item["id"])
                except ValueError as exc:
                    raise ValueError(
                        f"ERROR: scan item[{index}].{field} 值域非法; cause: {exc}; "
                        "fix: repair/reinstall the recorder producer and retry"
                    ) from None
        # harden-issues-read-write Task 1 (1b)：status/specific_field 枚举漂移不再硬 raise
        # 中止 reindex——降级为收进 problems + 继续，脏值项仍原样留在 items 里。
        if item[specific_field] not in specific_values:
            data["problems"].append(
                f"scan item[{index}].{specific_field} 枚举漂移: {item[specific_field]!r}"
            )
        if item["status"] not in status_values:
            data["problems"].append(
                f"scan item[{index}].status 枚举漂移: {item['status']!r}"
            )
    return data[items_key], data["problems"]


def _scan_pool(script, root, pool, problems_out=None):
    """子进程调 `{script} --root {root} scan --json`，给每项打 `pool` 标记后返回列表。

    推荐子进程而非 import：buglist.py / todolist.py 是薄入口，子进程调用只依赖它们的 CLI
    契约（`scan --json` 的输出结构），不依赖内部函数签名。

    `problems_out`：可选列表，非 None 时透传子进程 `scan --json` 输出里的 `problems`。
    """
    kwargs = {
        "capture_output": True,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
    }
    if _core._ACTIVE_RECORDER_TOKEN:
        kwargs["env"] = recorder_child_env("scan")
    proc = subprocess.run(
        [sys.executable, script, "--root", str(root), "scan", "--json"],
        **kwargs,
    )
    if proc.returncode != 0:
        if "repository semantic ID conflict" in proc.stderr:
            raise CrossPoolIDConflict(proc.stderr.strip())
        raise RuntimeError(
            f"{os.path.basename(script)} scan --json 失败（exit={proc.returncode}）：{proc.stderr}"
        )
    raw_items, scan_problems = validate_scan_envelope(proc.stdout, pool)
    if problems_out is not None:
        problems_out.extend(scan_problems)
    out = []
    for item in raw_items:
        merged = dict(item)
        merged["pool"] = pool
        out.append(merged)
    return out


def cross_pool_id_conflicts(items):
    """检测 `items`（含 `id`/`pool` 字段的 dict 列表）里同一 ID 是否跨池撞号
    （即同时出现在 pool == 'bug' 和 pool == 'todo' 的项里）。纯函数、只读。"""
    bug_ids = {it["id"] for it in items if it.get("pool") == "bug"}
    todo_ids = {it["id"] for it in items if it.get("pool") == "todo"}
    return sorted(bug_ids & todo_ids)


def read_pool(root, problems_out=None):
    """读跨两池（bug + todo）的 item 列表，join 结果里每项都带 `pool` 标记。

    子进程调用 `buglist.py scan --json` + `todolist.py scan --json`（见 `_scan_pool`），
    join 后立即跑 `cross_pool_id_conflicts` 做 D9 防护网校验，撞号即抛 `CrossPoolIDConflict`。
    """
    items = (
        _scan_pool(BUGLIST_SCRIPT, root, "bug", problems_out)
        + _scan_pool(TODOLIST_SCRIPT, root, "todo", problems_out)
    )
    conflicts = cross_pool_id_conflicts(items)
    if conflicts:
        raise CrossPoolIDConflict(
            "跨池 ID 冲突（D9 防护网触发，同一 ID 同时出现在 bug 池与 todo 池）："
            + ", ".join(conflicts)
        )
    return items


# ── reindex → issues/INDEX.md ────────────────────────────────────────────────

INDEX_BANNER = "<!-- GENERATED by issues.py reindex — DO NOT EDIT -->"


def _is_terminal(item):
    """item 是否已进入其所属 pool 的终态集（TERMINAL_STATUSES，从 POOL_SPEC 派生）。"""
    return item.get("status") in TERMINAL_STATUSES.get(item.get("pool"), set())


def _render_item_table(items):
    """把一组 item 渲染成 markdown 表（ID | Pool | Status | 关联Change），按 id 升序。"""
    lines = [
        "| ID | Pool | Status | 关联Change |",
        "|----|------|--------|------------|",
    ]
    for it in sorted(items, key=lambda x: x["id"]):
        change = it.get("change") or "-"
        lines.append(f"| {it['id']} | {it['pool']} | {it['status']} | {change} |")
    return "\n".join(lines)


def generate_index_md(items):
    """从 `read_pool` 返回的跨池 item 列表纯函数式生成 `issues/INDEX.md` 全文（含首行 banner）。
    **禁读旧 INDEX**（D3）——只以 `items` 为唯一输入源。幂等（D7）。"""
    open_items = [it for it in items if not _is_terminal(it)]
    closed_items = [it for it in items if _is_terminal(it)]

    groups = {}
    unbatched = []
    for it in open_items:
        batch = it.get("batch") or ""
        if batch:
            groups.setdefault(batch, []).append(it)
        else:
            unbatched.append(it)

    lines = [
        INDEX_BANNER,
        "",
        "# Issues Index",
        "",
        "> 本文件由 `issues.py reindex` 从 dated 文件"
        "（`issues/buglist/` + `issues/todolist/`）重建，请勿手改——"
        "手改内容会在下次 reindex 时被无条件覆盖。",
        "",
        "## Open 项（按批次）",
        "",
    ]

    if not groups and not unbatched:
        lines.append("（无 open 项）")
    else:
        for batch in sorted(groups):
            lines.append(f"### 批次：{batch}")
            lines.append("")
            lines.append(_render_item_table(groups[batch]))
            lines.append("")
        if unbatched:
            lines.append("### 未分组（批次为空）")
            lines.append("")
            lines.append(_render_item_table(unbatched))
            lines.append("")

    bug_closed = sum(1 for it in closed_items if it.get("pool") == "bug")
    todo_closed = sum(1 for it in closed_items if it.get("pool") == "todo")
    lines.append("## 已闭合（终态）摘要")
    lines.append("")
    lines.append(
        f"- 共 {len(closed_items)} 项已闭合（bug: {bug_closed}，todo: {todo_closed}）"
    )
    lines.append("")

    return "\n".join(lines)


def _reject_batch_line_unsafe(value, field):
    """`batches.md` 单行字段守卫；不是 legacy recorder table writer。"""
    if value is None:
        return
    if "|" in str(value) or "\n" in str(value) or "\r" in str(value):
        _die(f"字段 {field} 含非法字符（| 或换行），会破坏总览表列对齐：{value!r}")


def _reject_batch_key_unsafe(key):
    """batches.md header slug 守卫（OV-2）：拒空/纯空白、`|`/换行、` — ` em dash、首尾空白。"""
    if not str(key).strip():
        _die(f"batch key 不可为空/纯空白（会写出解析不回来的僵尸 header）：{key!r}")
    _reject_batch_line_unsafe(key, "batch key")
    if " — " in str(key) or str(key) != str(key).strip():
        _die(
            "batch key 非法（含 ' — ' em dash 分隔符，或首尾有空白），会破坏 "
            f"batches.md header（`### {{key}} — {{title}}`）解析：{key!r}"
        )


_INDEX_OPEN_ROW_RE = re.compile(r"^\|\s*[A-Z]\d+\s*\|")
_INDEX_CLOSED_SUMMARY_RE = re.compile(r"共\s*(\d+)\s*项已闭合")


def _count_index_items(index_path):
    """两段式解析旧 `INDEX.md` 的总项数（open 表格行数 + closed 聚合行的 N），供
    `_reindex_core` 写盘前的"总项数只增不减"守卫使用：

    - open：数 `_render_item_table` 渲染出的数据行（`| [A-Z]\\d+ | ... |`）——表头/分隔行
      不匹配该模式，安全跳过。
    - closed：`generate_index_md` 无条件写出的"共 N 项已闭合"聚合摘要行（即便 N=0 也写），
      正则未命中即视为该文件不是本工具生成的合法 INDEX.md。

    文件不存在、或 closed 聚合行缺失（格式损坏/非本工具生成）→ 返回 0（视为"无旧基线"，
    守卫据此跳过校验，不阻塞首次 reindex 或从损坏文件恢复）。"""
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return 0
    closed_match = _INDEX_CLOSED_SUMMARY_RE.search(content)
    if closed_match is None:
        return 0
    closed_count = int(closed_match.group(1))
    open_count = sum(
        1 for line in content.splitlines() if _INDEX_OPEN_ROW_RE.match(line.strip())
    )
    return open_count + closed_count


def _reindex_core(root, snapshot=None):
    """reindex 核心逻辑：`read_pool`（内含 D9 跨池 ID 冲突检测）→ `generate_index_md` 纯函数
    重建全文 → `atomic_write` 原子落盘 INDEX.md → `sync_batches_md`。返回 `(items, problems)`。

    写盘前先跑总项数只增不减守卫（`_count_index_items` 读旧 INDEX.md）：新扫描总项数低于
    旧总项数即拒绝覆盖（旧总项数为 0——含首次建、含旧文件不可解析——时跳过校验）。"""
    if snapshot is None:
        problems = []
        items = read_pool(root, problems)
    else:
        items = list(snapshot["items"])
        problems = list(snapshot.get("problems", []))
    index_path = os.path.join(root, "openspec", "issues", "INDEX.md")
    old_count = _count_index_items(index_path)
    new_count = len(items)
    if old_count > 0 and new_count < old_count:
        raise ReindexStageError(
            "count-guard",
            f"reindex 总项数只增不减守卫触发：旧 INDEX.md 共 {old_count} 项，"
            f"本次新扫描仅 {new_count} 项，拒绝覆盖（疑似误删 dated 文件或 scan 异常截断）",
        )
    content = generate_index_md(items)
    try:
        atomic_write(index_path, content)
    except Exception as exc:
        raise ReindexStageError("INDEX", exc) from None
    try:
        sync_batches_md(root, items)
    except Exception as exc:
        raise ReindexStageError("batches", exc) from None
    return items, problems


def _echo_problems(problems):
    """把 `_reindex_core` 返回的 problems 逐条回显到 stderr。"""
    for p in problems:
        print(p, file=sys.stderr)


def cmd_reindex(args):
    """重建 `issues/INDEX.md` + 同步 `issues/batches.md` 状态。"""
    root = args.root
    try:
        items, problems = _reindex_core(root)
    except RuntimeError as e:
        _die(str(e))
        return  # pragma: no cover

    index_path = os.path.join(root, "openspec", "issues", "INDEX.md")
    open_n = sum(1 for it in items if not _is_terminal(it))
    closed_n = len(items) - open_n
    print(f"reindex：已重建 {index_path}（open {open_n} 项，已闭合 {closed_n} 项）")

    _echo_problems(problems)
    if getattr(args, "strict", False) and problems:
        sys.exit(1)


# ── issues/batches.md 注册表 + batch 命令 ────────────────────────────────────

BATCH_STATUSES = ["PLANNED", "IN_PROGRESS", "DONE"]
BATCH_PLACEHOLDER = "<待填>"

_BATCH_HEADER_RE = re.compile(r"^### (?P<key>.+?) — (?P<title>.+?)\s*$")
_BATCH_STATUS_LINE_RE = re.compile(r"^状态[:：]\s*(.*)$")
_BATCH_MEMBERS_LINE_RE = re.compile(r"^成员[:：]\s*(.*)$")
_BATCH_WARN_LINE_RE = re.compile(r"^⚠️ 不一致:.*$")
_BATCH_RENAMED_FROM_LINE_RE = re.compile(r"^重命名自:\s*(.*)$")

BATCHES_MD_HEADER = (
    "# Issues 批次注册表\n"
    "\n"
    "> 半手维护：`状态:`/`成员:` 由 `issues.py`（reindex / `batch set-status`）维护，"
    "其余字段（`优先级:`/`计划:` 等）人工填写——reindex/batch 只精确 patch 生成行，"
    "绝不覆写人写行（Q3）。\n"
    "\n"
)


def batches_md_path(root):
    return os.path.join(root, "openspec", "issues", "batches.md")


def _read_batches_lines(path):
    """batches.md 不存在时视为空注册表（`[]`）。规范化尾随换行；读失败 fail-closed。"""
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError) as e:
        _die(f"batches.md 读取失败（编码或 IO 错误）：{path}: {e}")
    if lines and not lines[-1].endswith("\n"):
        lines[-1] = lines[-1] + "\n"
    return lines


def _find_batch_entry_range(lines, key):
    """在 `lines` 里定位 `key` 对应 entry 的行范围 `(header_idx, end_idx)`；未找到返回 None。"""
    header_idx = None
    for i, line in enumerate(lines):
        m = _BATCH_HEADER_RE.match(line.rstrip("\n"))
        if m and m.group("key") == key:
            header_idx = i
            break
    if header_idx is None:
        return None
    end_idx = len(lines)
    for j in range(header_idx + 1, len(lines)):
        if _BATCH_HEADER_RE.match(lines[j].rstrip("\n")):
            end_idx = j
            break
    return header_idx, end_idx


def _batch_entry_exists(lines, key):
    return _find_batch_entry_range(lines, key) is not None


def _batch_registry(lines):
    _preamble, entries = _split_batches_entries(lines) if lines else ([], [])
    registry = {}
    for key, entry_lines in entries:
        if key in registry:
            raise ValueError(f"ERROR: batches registry key 重复; cause: key={key}; fix: remove the duplicate header, then rerun the original command")
        provenance = []
        for line in entry_lines[1:]:
            match = _BATCH_RENAMED_FROM_LINE_RE.fullmatch(line.rstrip("\n"))
            if match:
                provenance.append(match.group(1))
        if len(provenance) > 1:
            raise ValueError(f"ERROR: batches registry provenance 重复; cause: key={key}; fix: retain exactly one machine-owned 重命名自 line, then retry")
        registry[key] = {"renamed_from": provenance[0] if provenance else None}
    return registry


def _rename_registry_lines(lines, old_key, new_key):
    rendered = list(lines)
    rng = _find_batch_entry_range(rendered, old_key)
    if rng is None:
        raise ValueError(f"ERROR: rename source batch 不存在; cause: old={old_key}; fix: verify the key and rerun the original command")
    header_idx, end_idx = rng
    match = _BATCH_HEADER_RE.match(rendered[header_idx].rstrip("\n"))
    rendered[header_idx] = f"### {new_key} — {match.group('title')}\n"
    provenance_indexes = [
        index for index in range(header_idx + 1, end_idx)
        if _BATCH_RENAMED_FROM_LINE_RE.fullmatch(rendered[index].rstrip("\n"))
    ]
    if len(provenance_indexes) > 1:
        raise ValueError(f"ERROR: batches registry provenance 重复; cause: key={old_key}; fix: retain exactly one machine-owned 重命名自 line, then retry")
    line = f"重命名自: {old_key}\n"
    if provenance_indexes:
        rendered[provenance_indexes[0]] = line
    else:
        rendered.insert(header_idx + 1, line)
    return rendered


def classify_batch_rename(registry, items, old_key, new_key):
    """Classify a registry-first rename as a first run or a proven retry."""
    old_exists = old_key in registry
    new_exists = new_key in registry
    if old_exists and new_exists:
        raise ValueError(f"ERROR: rename registry 双 key 同时存在; cause: old={old_key} new={new_key}; fix: resolve the registry conflict, then rerun the original command")
    if old_exists:
        orphan_ids = [item.get("id", "?") for item in items if item.get("batch") == new_key]
        if orphan_ids:
            raise ValueError(f"ERROR: rename target orphan items; cause: new={new_key} referenced before registry rename by {','.join(orphan_ids)}; fix: repair orphan tags, then rerun the original command")
        return "first"
    if not new_exists:
        raise ValueError(f"ERROR: rename source batch 不存在; cause: old={old_key} new={new_key}; fix: check the source key and rerun the original command")
    provenance = registry[new_key].get("renamed_from") if isinstance(registry[new_key], dict) else None
    if provenance != old_key:
        raise ValueError(f"ERROR: rename unknown source; cause: target={new_key} provenance={provenance!r} expected={old_key!r}; fix: do not absorb this target; verify the original command and registry provenance")
    return "retry"


def _rename_recovery_error(stage, root, old_key, new_key, cause):
    command = " ".join(shlex.quote(part) for part in (
        sys.executable, os.path.abspath(__file__), "--root", root,
        "batch", "rename", old_key, new_key,
    ))
    return ValueError(
        f"ERROR: batch rename stage={stage} failed; cause: {cause}; "
        f"fix: rerun the original command to converge: {command}"
    )


def _split_batches_entries(lines):
    """把 batches.md 全文行切成 `(preamble_lines, entries)`。纯定位/切片。"""
    header_positions = [
        i for i, line in enumerate(lines) if _BATCH_HEADER_RE.match(line.rstrip("\n"))
    ]
    preamble = lines[: header_positions[0]] if header_positions else list(lines)
    entries = []
    for idx, hpos in enumerate(header_positions):
        end = header_positions[idx + 1] if idx + 1 < len(header_positions) else len(lines)
        key = _BATCH_HEADER_RE.match(lines[hpos].rstrip("\n")).group("key")
        entries.append((key, lines[hpos:end]))
    return preamble, entries


def _sync_one_entry(entry_lines, member_ids, is_complete):
    """纯函数：同步一个 batches.md 条目的 `状态:`/`成员:` 生成行 + `⚠️ 不一致` 警告行。"""
    lines = [l for l in entry_lines if not _BATCH_WARN_LINE_RE.match(l.rstrip("\n"))]
    member_ids_sorted = sorted(member_ids)

    status_idx, status_val = None, None
    for i, l in enumerate(lines):
        m = _BATCH_STATUS_LINE_RE.match(l.rstrip("\n"))
        if m:
            status_idx, status_val = i, m.group(1).strip()
            break

    members_idx = None
    for i, l in enumerate(lines):
        if _BATCH_MEMBERS_LINE_RE.match(l.rstrip("\n")):
            members_idx = i
            break

    members_line = "成员: (生成)" + (
        (" " + ", ".join(member_ids_sorted)) if member_ids_sorted else ""
    ) + "\n"
    if members_idx is not None:
        lines[members_idx] = members_line
    else:
        lines.insert((status_idx + 1) if status_idx is not None else 1, members_line)

    need_warning = False
    if is_complete:
        if status_idx is not None:
            lines[status_idx] = "状态: DONE\n"
        else:
            lines.insert(1, "状态: DONE\n")
    elif status_val == "DONE":
        need_warning = True

    if need_warning:
        detail = ", ".join(member_ids_sorted) if member_ids_sorted else "0 名成员"
        warn_line = (
            f"⚠️ 不一致: 状态标记为 DONE，但成员未全部进入终态（当前成员：{detail}）——"
            "reindex 不会自动纠正 状态: 的值（不越权），请人工核实后用 `batch "
            "set-status` 改回或补完成员状态\n"
        )
        end = len(lines)
        while end > 0 and lines[end - 1].strip() == "":
            end -= 1
        lines.insert(end, warn_line)

    return lines


def sync_batches_md(root, items):
    """reindex 第二部分：拿 `items` 当 ground truth 同步 `issues/batches.md` 每批生成行。"""
    path = batches_md_path(root)
    lines = _read_batches_lines(path)
    preamble, entries = _split_batches_entries(lines) if lines else ([], [])
    known_keys = {key for key, _ in entries}

    by_batch = {}
    for it in items:
        batch = it.get("batch") or ""
        if batch:
            by_batch.setdefault(batch, []).append(it)

    for key in sorted(by_batch):
        if key not in known_keys:
            member_ids = sorted(it["id"] for it in by_batch[key])
            print(
                f"reindex: 警告（orphan，Q2）：批次 '{key}' 被 {len(member_ids)} 个 "
                f"item 引用（{', '.join(member_ids)}），但 issues/batches.md 未注册"
                "该 key——不会新建 ghost 条目，请用 `batch add` 补注册该 key，或修正"
                "对应 item 的批次 tag。",
                file=sys.stderr,
            )

    if not entries:
        return

    new_lines = list(preamble)
    for key, entry_lines in entries:
        members = by_batch.get(key, [])
        member_ids = [it["id"] for it in members]
        is_complete = len(members) >= 1 and all(_is_terminal(it) for it in members)
        new_lines.extend(_sync_one_entry(entry_lines, member_ids, is_complete))

    atomic_write(path, "".join(new_lines))


# ── batch lint ───────────────────────────────────────────────────────────────

_BATCH_PRIORITY_LINE_RE = re.compile(r"^优先级[:：]\s*(.*)$")
_BATCH_PLAN_LINE_RE = re.compile(r"^计划[:：]\s*(.*)$")
_BATCH_PRIORITY_PREFIX_RE = re.compile(r"^(P[0-4](?!\d)|—)")


def _find_batch_field_value(entry_lines, field_re):
    """在一个 batches.md 条目里找第一处匹配 `field_re` 的行，返回捕获组（已 strip）；无则 None。"""
    for line in entry_lines:
        m = field_re.match(line.rstrip("\n"))
        if m:
            return m.group(1).strip()
    return None


def _lint_priority_field(value):
    """校验非占位 `优先级:` 值是否合法；合法返回 None，非法返回违规原因文案。"""
    m = _BATCH_PRIORITY_PREFIX_RE.match(value.strip())
    token = m.group(1) if m else None
    if token is None or token not in PRIORITIES + ["—"]:
        return (
            f"前导 token 须 ∈ {{{', '.join(PRIORITIES)}, —}}（匹配后剩余字符串不校验，"
            f"如 'P1 ★'/'P2（说明）' 均合法）：{value!r}"
        )
    return None


def _lint_plan_field(value):
    """校验非占位 `计划:` 值是否合法；合法返回 None，非法返回违规原因文案。"""
    if not value.strip():
        return f"非占位时不可为空白：{value!r}"
    return None


def _lint_one_entry(entry_lines):
    """校验单个 batches.md 条目的 `优先级:`/`计划:` 字段，返回违规列表；无违规返回 `[]`。"""
    violations = []
    priority = _find_batch_field_value(entry_lines, _BATCH_PRIORITY_LINE_RE)
    if priority is not None and priority != BATCH_PLACEHOLDER:
        reason = _lint_priority_field(priority)
        if reason:
            violations.append(("优先级", priority, reason))

    plan = _find_batch_field_value(entry_lines, _BATCH_PLAN_LINE_RE)
    if plan is not None and plan != BATCH_PLACEHOLDER:
        reason = _lint_plan_field(plan)
        if reason:
            violations.append(("计划", plan, reason))

    return violations


def cmd_batch_lint(args):
    """`batch lint`：只读校验 `issues/batches.md` 全部条目的 `优先级:`/`计划:` 字段语法。"""
    _render_batch_lint(_batch_lint_snapshot(args))


def _batch_lint_snapshot(args):
    root = args.root
    path = batches_md_path(root)
    if not os.path.exists(path):
        return {"error": f"batches.md 不存在，无法校验：{path}", "problems": (), "count": 0}
    lines = _read_batches_lines(path)
    _, entries = _split_batches_entries(lines) if lines else ([], [])

    problems = []
    for key, entry_lines in entries:
        for field, value, reason in _lint_one_entry(entry_lines):
            problems.append(f"批次 '{key}' 字段 {field} 非法：{reason}")

    return {"error": None, "problems": tuple(problems), "count": len(entries)}


def _render_batch_lint(snapshot):
    if snapshot["error"]:
        print("ERROR: " + snapshot["error"], file=sys.stderr)
        raise SystemExit(1)
    if snapshot["problems"]:
        for p in snapshot["problems"]:
            print("ERROR: " + p, file=sys.stderr)
        raise SystemExit(1)

    print(f"batch lint：{snapshot['count']} 条批次全部通过（优先级/计划字段语法校验）")


def cmd_batch_add(args):
    """`batch add {key}`：新建 PLANNED 条目，成员空；人写字段按参数写，缺省留占位。"""
    root = args.root
    _reject_batch_key_unsafe(args.key)
    _reject_batch_line_unsafe(args.title, "title")
    _reject_batch_line_unsafe(getattr(args, "优先级"), "优先级")
    _reject_batch_line_unsafe(getattr(args, "计划"), "计划")
    path = batches_md_path(root)
    lines = _read_batches_lines(path)
    if _batch_entry_exists(lines, args.key):
        if getattr(args, "if_exists", None) == "skip":
            print(
                f"batch add: 批次 key 已存在，--if-exists skip：no-op，字段参数被忽略："
                f"{args.key}",
                file=sys.stderr,
            )
            return
        _die(f"批次 key 已存在：{args.key}（add 不覆写已有条目；改状态用 set-status，改名用 rename）")

    title = args.title or args.key
    priority = getattr(args, "优先级") or BATCH_PLACEHOLDER
    plan = getattr(args, "计划") or BATCH_PLACEHOLDER

    entry_lines = [
        f"### {args.key} — {title}\n",
        "状态: PLANNED\n",
        "成员: (生成)\n",
        f"优先级: {priority}\n",
        f"计划: {plan}\n",
    ]

    if not lines:
        lines = [BATCHES_MD_HEADER]
    elif lines[-1].strip() != "":
        lines.append("\n")
    lines.extend(entry_lines)
    lines.append("\n")

    atomic_write(path, "".join(lines))
    print(json.dumps({"key": args.key, "title": title, "status": "PLANNED"}, ensure_ascii=False))


def cmd_batch_set_status(args):
    """`batch set-status {key} {S}`：只改该条目的 `状态:` 生成行，绝不动人写行（Q3）。"""
    root = args.root
    if args.status not in BATCH_STATUSES:
        _die(f"批次状态非法：{args.status}（应为 {'/'.join(BATCH_STATUSES)}）")

    path = batches_md_path(root)
    lines = _read_batches_lines(path)
    rng = _find_batch_entry_range(lines, args.key)
    if rng is None:
        _die(f"未找到批次 key：{args.key}")
    header_idx, end_idx = rng

    status_idx = None
    for i in range(header_idx + 1, end_idx):
        if _BATCH_STATUS_LINE_RE.match(lines[i].rstrip("\n")):
            status_idx = i
            break

    old_status = None
    if status_idx is not None:
        old_status = _BATCH_STATUS_LINE_RE.match(lines[status_idx].rstrip("\n")).group(1).strip()
        lines[status_idx] = f"状态: {args.status}\n"
    else:
        lines.insert(header_idx + 1, f"状态: {args.status}\n")

    atomic_write(path, "".join(lines))
    print(json.dumps(
        {"key": args.key, "old_status": old_status, "new_status": args.status}, ensure_ascii=False
    ))


def cmd_batch_rename(args):
    """Registry-first, retryable, direct-snapshot cross-pool batch rename."""
    root = args.root
    old_key, new_key = args.old, args.new
    _reject_batch_key_unsafe(new_key)
    if old_key == new_key:
        raise ValueError("ERROR: batch rename source 与 target 相同; cause: no rename can be proven; fix: choose a different target key")

    path = batches_md_path(root)
    lines = _read_batches_lines(path)
    try:
        registry = _batch_registry(lines)
        snapshot = read_rename_snapshot(root)
        state = classify_batch_rename(registry, snapshot["items"], old_key, new_key)
        updated = retag_rename_snapshot(snapshot, old_key, new_key)
    except Exception as exc:
        if isinstance(exc, ValueError) and str(exc).startswith("ERROR: batch rename stage="):
            raise
        raise _rename_recovery_error("preflight", root, old_key, new_key, exc) from None

    if state == "first":
        try:
            atomic_write(path, "".join(_rename_registry_lines(lines, old_key, new_key)))
        except Exception as exc:
            raise _rename_recovery_error("registry", root, old_key, new_key, exc) from None

    changed = 0
    for before, after in zip(snapshot["documents"], updated["documents"]):
        if after["rendered"] == before["raw"]:
            continue
        changed += sum(
            1 for item in snapshot["items"]
            if item["file"] == before["file"] and item.get("batch") == old_key
        )
        try:
            atomic_write_bytes(after["path"], after["rendered"])
        except Exception as exc:
            stage = f"dated:{after['file']}"
            raise _rename_recovery_error(stage, root, old_key, new_key, exc) from None

    try:
        _items, problems = _reindex_core(root, snapshot=updated)
    except ReindexStageError as exc:
        raise _rename_recovery_error(exc.stage, root, old_key, new_key, exc.cause) from None
    except Exception as exc:
        raise _rename_recovery_error("reindex", root, old_key, new_key, exc) from None
    _echo_problems(problems)
    print(json.dumps(
        {"old_key": old_key, "new_key": new_key, "items_changed": changed, "mode": state},
        ensure_ascii=False,
    ))


# ── sweep ─────────────────────────────────────────────────────────────────────

def cmd_sweep(args):
    """把某 change 的未分批非终态项一键分诊入批次（非原子、fail-closed、可重跑收敛）。"""
    root = args.root
    raw_change = args.change or ""
    if raw_change != raw_change.strip():
        _die(f"sweep --change 首尾不可有空白（不静默 strip，防误纳）：{raw_change!r}")
    change = raw_change
    if not change:
        _die("sweep --change 不可为空（防空 change 误纳孤儿）")
    _reject_batch_key_unsafe(change)

    tagged = []
    for script, pool, idkey in (
        (BUGLIST_SCRIPT, "bug", "bugs"),
        (TODOLIST_SCRIPT, "todo", "items"),
    ):
        proc = subprocess.run(
            [sys.executable, script, "--root", root, "scan",
             "--change", change, "--open-ungrouped", "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=recorder_child_env("scan"),
        )
        if proc.returncode != 0:
            _die(f"sweep: {pool} scan 失败 (rc={proc.returncode}): {proc.stderr.strip()}")
        data = json.loads(proc.stdout)
        for p in (data.get("problems") or []):
            print(f"sweep: {pool} scan problems: {p}", file=sys.stderr)
        items = data.get(idkey, [])
        for it in items:
            iid = it["id"]
            tp = subprocess.run(
                [sys.executable, script, "--root", root, "triage",
                 "--id", iid, "--批次", change],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=recorder_child_env("triage"),
            )
            if tp.returncode != 0:
                _die(
                    f"sweep: triage 失败于 {pool} 第 {iid} 项 (rc={tp.returncode})；"
                    f"已 tag={tagged}: {tp.stderr.strip()}"
                )
            tagged.append(iid)

    if not tagged:
        print(f"sweep {change}: tagged 0 项，无匹配项，跳过 batch add/reindex")
        return

    ba = subprocess.run(
        [sys.executable, __file__, "--root", root, "batch", "add",
         change, "--if-exists", "skip"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=recorder_child_env("batch-add"),
    )
    if ba.returncode != 0:
        _die(f"sweep: batch add 失败 (rc={ba.returncode}): {ba.stderr.strip()}")

    ri = subprocess.run(
        [sys.executable, __file__, "--root", root, "reindex"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=recorder_child_env("reindex"),
    )
    if ri.returncode != 0:
        _die(f"sweep: reindex 失败 (rc={ri.returncode}): {ri.stderr.strip()}")
    elif ri.stderr.strip():
        print(ri.stderr, end="" if ri.stderr.endswith("\n") else "\n", file=sys.stderr)

    print(f"sweep {change}: tagged {len(tagged)} 项 {tagged}")


def main():
    p = argparse.ArgumentParser(
        description="共享 issues 层：跨 bug+todo 的 reindex / batch"
    )
    p.add_argument("--root", default=None, help="目标项目根（存 openspec/issues/... 的仓库；默认自动探测 git 根）")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("reindex", help="重建 issues/INDEX.md（open×批次板）+ 同步 issues/batches.md 状态")
    s.add_argument(
        "--strict", action="store_true",
        help="两池一致性自检有 problems 时以非 0 退出（默认：problems 回显 stderr 但 exit 0）",
    )
    s.set_defaults(func=cmd_reindex)

    batch_p = sub.add_parser("batch", help="issues/batches.md 注册表操作（add/set-status/rename）")
    batch_sub = batch_p.add_subparsers(dest="batch_action", required=True)

    sa = batch_sub.add_parser("add", help="新建批次条目（状态=PLANNED，成员空，人写字段按参数写/缺省留占位）")
    sa.add_argument("key")
    sa.add_argument("--title", help="批次标题（缺省=key）")
    sa.add_argument("--优先级", dest="优先级", help="人写字段，缺省留占位")
    sa.add_argument("--计划", dest="计划", help="人写字段（一句范围），缺省留占位")
    sa.add_argument(
        "--if-exists", dest="if_exists", choices=["skip"], default=None,
        help="key 已存在时的行为，默认报错；skip = no-op + stderr 警告，忽略本次字段参数",
    )
    sa.set_defaults(func=cmd_batch_add)

    ss = batch_sub.add_parser("set-status", help="改批次状态（只精确 patch `状态:` 生成行，不动人写行）")
    ss.add_argument("key")
    ss.add_argument("status", choices=BATCH_STATUSES)
    ss.set_defaults(func=cmd_batch_set_status)

    sr = batch_sub.add_parser(
        "rename",
        help="registry-first 改批次 key + snapshot retag/reindex；失败后重跑原命令收敛",
    )
    sr.add_argument("old")
    sr.add_argument("new")
    sr.set_defaults(func=cmd_batch_rename)

    sl = batch_sub.add_parser(
        "lint",
        help="只读校验全部批次的 优先级:/计划: 人写字段语法（占位符豁免，fail-closed）",
    )
    sl.set_defaults(func=cmd_batch_lint)

    sw = sub.add_parser(
        "sweep",
        help="一键封装（非原子、fail-closed、可重跑收敛）：把本 change 未分批非终态项分诊"
             "入批次（scan --open-ungrouped → triage → batch add --if-exists skip → reindex）",
    )
    sw.add_argument("--change", required=True, help="本 change 名（不可为空，防误纳孤儿）")
    sw.set_defaults(func=cmd_sweep)

    args = p.parse_args()
    command = f"batch-{args.batch_action}" if args.cmd == "batch" else args.cmd
    try:
        args.root = repo_root(args.root)
        if command == "batch-lint":
            with recorder_lock(args.root, command):
                snapshot = _batch_lint_snapshot(args)
            _render_batch_lint(snapshot)
        else:
            output = io.StringIO()
            with recorder_lock(args.root, command) as lock_state, redirect_stdout(output):
                args._recorder_token = lock_state.token
                # 委派状态存于共享源 core（recorder_child_env 从 core 读取当前 token/chain）。
                # [impl-review-fix] F1: token/chain 复位 MUST 走 finally——core 是进程内单例模块
                # 全局，三入口合并后共用一个 core；错误路径（_die→SystemExit / args.func 抛异常）
                # 若跳过复位，脏 token 泄漏给同进程后续任何直调 read_pool/_scan_pool，
                # 触发 RecorderLockError: delegation denied（根本没碰目标仓）。
                _core._ACTIVE_RECORDER_TOKEN = lock_state.token
                _core._ACTIVE_RECORDER_CHAIN = lock_state.chain
                try:
                    args.func(args)
                finally:
                    _core._ACTIVE_RECORDER_TOKEN = None
                    _core._ACTIVE_RECORDER_CHAIN = None
            sys.stdout.write(output.getvalue())
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
