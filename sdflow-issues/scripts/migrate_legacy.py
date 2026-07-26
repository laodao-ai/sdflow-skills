#!/usr/bin/env python3
"""Audit and repair historical issue values without rewriting legacy tables.

The legacy Markdown table remains byte-for-byte unchanged.  Only rows that the
current recorder schema cannot represent are promoted into the existing
``sdflow-issues`` frontmatter namespace.  Already-promoted items are also
normalized when an old optional-field placeholder survived in frontmatter.
Historical classifications are never guessed: callers must provide explicit
pool-scoped mappings for out-of-domain specific fields or statuses.
"""

import argparse
import hashlib
import io
import json
import os
import subprocess
import sys
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sdflow_issues_core import (  # noqa: E402
    POOL_SPEC,
    _canonical_from_key,
    _legacy_block_range,
    _legacy_semantic_id_key,
    _prepare_overlay_model,
    _render_recorder_document,
    _splice_body_lines,
    atomic_write_bytes,
    parse_recorder_document,
    read_repository_snapshot,
    recorder_lock,
    repo_root,
    repository_semantic_occurrences,
)


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ISSUES_SCRIPT = os.path.join(SCRIPT_DIR, "issues.py")
LEGACY_EMPTY_SENTINELS = {"", "-", "—"}


def _parse_mapping(raw, label):
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"ERROR: {label} 不是合法 JSON: {exc}") from None
    if not isinstance(value, dict):
        raise ValueError(f"ERROR: {label} 必须是按 pool 分组的 JSON object")
    normalized = {}
    for pool, mapping in value.items():
        if pool not in POOL_SPEC or not isinstance(mapping, dict):
            raise ValueError(f"ERROR: {label}.{pool} 必须是 bug/todo 下的 JSON object")
        normalized[pool] = {}
        for old, new in mapping.items():
            if not isinstance(old, str) or not old or not isinstance(new, str) or not new:
                raise ValueError(f"ERROR: {label}.{pool} 的映射键和值必须是非空 string")
            normalized[pool][old] = new
    return normalized


def _validate_mappings(specific_map, status_map):
    for pool, mapping in specific_map.items():
        allowed = POOL_SPEC[pool].specific_values
        for old, new in mapping.items():
            if new not in allowed:
                field = POOL_SPEC[pool].specific_field
                raise ValueError(
                    f"ERROR: specific mapping 越域: {pool}.{old!r}->{new!r}; "
                    f"{field} 只接受 {sorted(allowed)}"
                )
    for pool, mapping in status_map.items():
        allowed = POOL_SPEC[pool].status_values
        for old, new in mapping.items():
            if new not in allowed:
                raise ValueError(
                    f"ERROR: status mapping 越域: {pool}.{old!r}->{new!r}; "
                    f"status 只接受 {sorted(allowed)}"
                )


def _field_change(changes, field, old, new):
    if old != new:
        changes[field] = {"from": old, "to": new}


def _normalize_legacy_item(pool, raw_id, original, specific_map, status_map):
    spec = POOL_SPEC[pool]
    item = dict(original)
    changes = {}
    unresolved = []

    for field in ("change", "batch"):
        old = item.get(field)
        new = None if isinstance(old, str) and old in LEGACY_EMPTY_SENTINELS else old
        _field_change(changes, field, old, new)
        item[field] = new

    if item.get("time") is None:
        _field_change(changes, "time", None, "")
        item["time"] = ""

    specific_field = spec.specific_field
    specific_value = item.get(specific_field)
    if specific_value not in spec.specific_values:
        replacement = specific_map.get(pool, {}).get(specific_value)
        if replacement is None:
            unresolved.append({
                "field": specific_field,
                "value": specific_value,
                "allowed": sorted(spec.specific_values),
            })
        else:
            _field_change(changes, specific_field, specific_value, replacement)
            item[specific_field] = replacement

    status = item.get("status")
    if status not in spec.status_values:
        replacement = status_map.get(pool, {}).get(status)
        if replacement is None:
            unresolved.append({
                "field": "status",
                "value": status,
                "allowed": sorted(spec.status_values),
            })
        else:
            _field_change(changes, "status", status, replacement)
            item["status"] = replacement

    for field in ("module", "summary", "time"):
        value = item.get(field)
        if not isinstance(value, str) or (field != "time" and not value.strip()):
            unresolved.append({"field": field, "value": value, "allowed": "non-empty string"})

    canonical = _canonical_from_key(_legacy_semantic_id_key(raw_id))
    return canonical, item, changes, unresolved


def _merge_insertions(target, source):
    for index, values in source.items():
        target.setdefault(index, []).extend(values)


def _render_document_migration(record, targets):
    document = record["document"]
    pool = record["pool"]
    path = record["path"]
    spec = POOL_SPEC[pool]
    model = dict(document["model"] or {
        "schema": 1,
        "pool": pool,
        "mode": "overlay",
        "items": {},
    })
    model["items"] = dict(model["items"])
    insertions = {}
    marker_required = set()

    for target in targets:
        raw_id = target["raw_id"]
        canonical = target["id"]
        item = target["item"]
        model = _prepare_overlay_model(
            {**document, "model": model}, pool, canonical, item
        )
        has_legacy_block = target["source"] == "legacy" and any(
            _legacy_semantic_id_key(candidate) == _legacy_semantic_id_key(raw_id)
            for candidate in document["legacy_blocks"]
        )
        if target["source"] == "legacy" and (has_legacy_block or spec.requires_block):
            start, end = _legacy_block_range(document, raw_id, path)
            eol = document["eol"]
            _merge_insertions(insertions, {
                start: (f"<!-- sdflow-issue-block:start id={canonical} -->".encode("ascii") + eol,),
                end: (f"<!-- sdflow-issue-block:end id={canonical} -->".encode("ascii") + eol,),
            })
            marker_required.add(canonical)

    body = _splice_body_lines(document, insertions)
    rendered = _render_recorder_document(document, model, body)
    candidate = parse_recorder_document(rendered, pool)
    structural = [
        problem for problem in candidate["problems"]
        if "marker" in problem or "frontmatter" in problem
    ]
    for target in targets:
        if target["id"] not in candidate["model"]["items"]:
            structural.append(f"frontmatter item 缺失：{target['id']}")
    for canonical in marker_required:
        if canonical not in candidate["marker_blocks"]:
            structural.append(f"marker block 缺失：{canonical}")
    if structural:
        raise ValueError(
            f"ERROR: file={path} rendered candidate 关系自检失败; "
            f"cause: {structural[0]}; fix: 拒绝写入并修正迁移逻辑"
        )
    return rendered


def build_migration(root, specific_map=None, status_map=None):
    specific_map = specific_map or {}
    status_map = status_map or {}
    _validate_mappings(specific_map, status_map)
    snapshot = read_repository_snapshot(root)
    repository_semantic_occurrences(root, snapshot)

    changes = []
    unresolved = []
    document_records = []
    targets_by_path = {}
    records_by_path = {}
    affected_paths = set()

    for pool, path, rel, document in snapshot:
        record = {"pool": pool, "path": path, "file": rel, "document": document}
        records_by_path[path] = record
        frontmatter_keys = {
            _legacy_semantic_id_key(item_id)
            for item_id in (document["model"]["items"] if document["model"] else {})
        }
        for raw_id, original in document["effective_items"].items():
            source = (
                "frontmatter"
                if _legacy_semantic_id_key(raw_id) in frontmatter_keys
                else "legacy"
            )
            canonical, item, field_changes, item_unresolved = _normalize_legacy_item(
                pool, raw_id, original, specific_map, status_map
            )
            if not field_changes and not item_unresolved:
                continue
            affected_paths.add(path)
            entry = {
                "pool": pool,
                "file": rel.replace(os.sep, "/"),
                "id": canonical,
                "raw_id": raw_id,
                "source": source,
                "fields": field_changes,
            }
            changes.append(entry)
            for problem in item_unresolved:
                unresolved.append({**entry, **problem})
            if not item_unresolved:
                targets_by_path.setdefault(path, []).append({
                    "id": canonical,
                    "raw_id": raw_id,
                    "source": source,
                    "item": item,
                })

    if not unresolved:
        for path in sorted(targets_by_path):
            record = records_by_path[path]
            rendered = _render_document_migration(record, targets_by_path[path])
            raw = record["document"]["raw"]
            document_records.append({
                "path": path,
                "file": record["file"].replace(os.sep, "/"),
                "before_sha256": hashlib.sha256(raw).hexdigest(),
                "after_sha256": hashlib.sha256(rendered).hexdigest(),
                "raw": raw,
                "rendered": rendered,
            })

    return {
        "root": root,
        "items_changed": len(changes),
        "files_changed": len(affected_paths),
        "changes": sorted(changes, key=lambda value: (value["file"], value["id"])),
        "unresolved": sorted(
            unresolved,
            key=lambda value: (value["file"], value["id"], value["field"]),
        ),
        "documents": document_records,
    }


def public_report(migration, mode, reindex=None):
    report = {
        "mode": mode,
        "root": migration["root"],
        "items_changed": migration["items_changed"],
        "files_changed": migration["files_changed"],
        "changes": migration["changes"],
        "unresolved": migration["unresolved"],
    }
    if reindex is not None:
        report["reindex"] = reindex
    return report


def apply_migration(migration):
    if migration["unresolved"]:
        first = migration["unresolved"][0]
        raise ValueError(
            f"ERROR: migration plan 尚有 {len(migration['unresolved'])} 个未解析字段; "
            f"first={first['file']}:{first['id']}.{first['field']}={first['value']!r}; "
            "fix: 通过 --specific-map-json/--status-map-json 提供显式映射后重试"
        )
    for document in migration["documents"]:
        with open(document["path"], "rb") as stream:
            current = stream.read()
        current_hash = hashlib.sha256(current).hexdigest()
        if current_hash != document["before_sha256"]:
            raise ValueError(
                f"ERROR: file={document['path']} 在 preflight 后发生变化; "
                f"cause: expected sha256={document['before_sha256']} actual={current_hash}; "
                "fix: 重新运行 audit/apply"
            )
    for document in migration["documents"]:
        atomic_write_bytes(document["path"], document["rendered"])


def run_reindex(root):
    proc = subprocess.run(
        [sys.executable, ISSUES_SCRIPT, "--root", root, "reindex"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        raise ValueError(
            f"ERROR: legacy migration 已写入，但 reindex 失败 (rc={proc.returncode}); "
            f"cause: {proc.stderr.strip() or proc.stdout.strip()}; "
            "fix: 修正报告的问题后重跑同一 apply 命令"
        )
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    return {"status": "ok", "stdout": proc.stdout.strip()}


def main():
    parser = argparse.ArgumentParser(
        description="审计/迁移不符合当前 schema 的 legacy issues 行（旧表永久只读）"
    )
    parser.add_argument("--root", default=None, help="目标项目根；默认自动探测 git 根")
    parser.add_argument(
        "--specific-map-json",
        default="{}",
        help='pool-scoped 旧特定字段映射，例如 {"todo":{"技术债":"代码质量"}}',
    )
    parser.add_argument(
        "--status-map-json",
        default="{}",
        help='pool-scoped 旧状态映射，例如 {"todo":{"wontfix":"WONTDO"}}',
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("audit", help="只读输出迁移计划；存在 unresolved 也不写盘")
    apply_parser = sub.add_parser("apply", help="全量 preflight 后写 same-file overlay")
    apply_parser.add_argument(
        "--no-reindex", action="store_true", help="迁移后不自动重建 INDEX/batches（测试/诊断用）"
    )
    args = parser.parse_args()

    try:
        root = repo_root(args.root)
        specific_map = _parse_mapping(args.specific_map_json, "--specific-map-json")
        status_map = _parse_mapping(args.status_map_json, "--status-map-json")
        output = io.StringIO()
        with recorder_lock(root, "migrate-legacy"), redirect_stdout(output):
            migration = build_migration(root, specific_map, status_map)
            if args.command == "apply":
                apply_migration(migration)
        if output.getvalue():
            sys.stderr.write(output.getvalue())

        reindex = None
        if args.command == "apply" and not args.no_reindex:
            reindex = run_reindex(root)
        print(json.dumps(
            public_report(migration, args.command, reindex),
            ensure_ascii=False,
            indent=2,
        ))
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
