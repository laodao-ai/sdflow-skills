#!/usr/bin/env python3
"""todolist.py — 自动记录/回写/扫描 todolist 的确定性兜底脚本。

skill `sdflow-todolist` 的执行核心。收集优化想法/技术债/改进等**非缺陷**项，
作为后续排期的收集池。与 buglist 的差异：每月一文件、T 前缀、按类型而非优先级、
详细块可选（轻量优先）、无根因/修复方案、状态码 OPEN/PROPOSED/DONE/WONTDO。

把"判断"留给模型（值不值得记、归哪类、要不要写动机/思路），把"确定性且易错"的部分
交给本脚本：全局 T-ID 自增、canonical/overlay 写入、legacy 表只读 promotion、DONE 门禁
（必带 change/commit 证据）、WONTDO 门禁（必带理由）、扫描 + 一致性自检。

文件布局（约定，自包含，不依赖外部 rule）：
  <root>/openspec/issues/todolist/YYYY-MM-todolist.md
  结构 = versioned frontmatter 索引 → marker-framed 人读详情/历史（可选）

用法见 `python todolist.py --help`。dated 文件落盘经 bytes atomic replace；新 writer 不写
Markdown 总览表或可变 status/batch prose 副本。
"""

import argparse
from contextlib import contextmanager, redirect_stdout
import datetime
import glob
import io
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import time


def atomic_write(path, text):
    """原子写：同目录临时文件写完整内容 → os.replace 原子换入。
    中途任何异常（含 os.replace 本身失败）都不会截断/损坏原文件——旧内容原样保留，
    临时文件在 finally 里清理，不留残留 .tmp。

    tempfile.mkstemp 固定以 0600 创建临时文件；os.replace 是纯 rename，目标会
    继承临时文件的权限。覆写已存在文件前必须把临时文件权限对齐回原文件的权限，
    否则已存在文件的权限会被静默从（例如）0644 收紧到 0600（对 group/other 变
    不可读）。原文件不存在（首次创建）时用 0o644 兜底。"""
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        try:
            mode = os.stat(path).st_mode & 0o777
        except FileNotFoundError:
            mode = 0o644
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def atomic_write_bytes(path, data):
    """原子替换 dated recorder bytes，且保持既有 POSIX mode bits。"""
    if not isinstance(data, bytes):
        raise TypeError("atomic_write_bytes data must be bytes")
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        try:
            mode = os.stat(path).st_mode & 0o777
        except FileNotFoundError:
            mode = 0o644
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

STATUS_CODES = ["OPEN", "PROPOSED", "DONE", "WONTDO"]
TYPE_TAGS = ["性能优化", "可观测性", "代码质量", "功能增强", "基础设施"]
DEFAULT_PREFIX = "T"
ID_RE = re.compile(r"\b([A-Z])([0-9]+)\b", re.ASCII)
CANONICAL_ID_RE = re.compile(r"^[A-Z][1-9][0-9]*$", re.ASCII)
UTF8_BOM = b"\xef\xbb\xbf"
RECORDER_POOL_CONFIG = {
    "bug": ("priority", {"P0", "P1", "P2", "P3", "P4"},
            {"OPEN", "VERIFIED", "PROPOSED", "IN_PROGRESS", "FIXED", "WONTFIX", "BLOCKED"}),
    "todo": ("type", set(TYPE_TAGS), set(STATUS_CODES)),
}

RECORDER_LOCK_ENV = "SDFLOW_RECORDER_LOCK_TOKEN"
RECORDER_DELEGATION_CHAIN_ENV = "SDFLOW_RECORDER_DELEGATION_CHAIN"
_ACTIVE_RECORDER_TOKEN = None
_ACTIVE_RECORDER_CHAIN = None
RECORDER_PARTICIPANT_ALLOWLIST = {
    "scan", "next-id", "add", "set-status", "triage", "reindex", "sweep",
    "batch-lint", "batch-add", "batch-set-status", "batch-rename",
}
RECORDER_DELEGATION_GRAPH = {
    "sweep": {"scan", "triage", "batch-add", "reindex"},
    "reindex": {"scan"},
    "batch-rename": {"scan"},
}


class RecorderLockError(ValueError):
    pass


class RecorderLockState:
    def __init__(self, path, token, participant=False, identity=None, chain=()):
        self.path = path
        self.token = token
        self.participant = participant
        self.identity = identity
        self.chain = tuple(chain)


def canonical_id(value):
    if not isinstance(value, str) or not CANONICAL_ID_RE.fullmatch(value):
        raise ValueError(f"ERROR: ID is not canonical ASCII spelling: {value!r}; cause: expected [A-Z][1-9][0-9]*; fix: use e.g. A7")
    return value


def semantic_id_key(value, allow_legacy=False):
    pattern = r"([A-Z])([0-9]+)" if allow_legacy else r"([A-Z])([1-9][0-9]*)"
    match = re.fullmatch(pattern, value, re.ASCII) if isinstance(value, str) else None
    if not match:
        raise ValueError(f"ERROR: ID is not canonical ASCII spelling: {value!r}; cause: invalid semantic ID; fix: use one ASCII uppercase prefix and ASCII digits")
    return match.group(1), int(match.group(2))


def validate_prefix(prefix):
    if not isinstance(prefix, str) or not re.fullmatch(r"[A-Z]", prefix, re.ASCII):
        raise ValueError(f"ERROR: prefix is not one ASCII uppercase letter: {prefix!r}; cause: invalid prefix; fix: use A-Z")
    return prefix


def _lock_path(root):
    return os.path.join(os.path.realpath(os.fspath(root)), "openspec", "issues", ".recorder.lock")


def _read_lock_metadata(path):
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
        value = json.loads(raw.decode("utf-8"))
        required = {"repo", "pid", "command", "started", "token"}
        return value if isinstance(value, dict) and required <= set(value) else None
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def _lock_conflict(path, metadata=None):
    if metadata:
        owner = f"pid={metadata.get('pid')} command={metadata.get('command')} started={metadata.get('started')}"
        cause = f"lock occupied by {owner}"
    else:
        cause = "lock occupied; owner metadata unavailable/initializing"
    return RecorderLockError(
        f"ERROR: recorder lock occupied at {path}; cause: {cause}; fix: stop all recorder processes for this repo, remove exactly {path}, then retry"
    )


def validate_recorder_participant(root, token, command):
    root = os.path.realpath(os.fspath(root))
    path = _lock_path(root)
    if command not in RECORDER_PARTICIPANT_ALLOWLIST:
        raise RecorderLockError(f"ERROR: participant command not allowlisted: {command}; cause: delegation denied; fix: invoke it as a top-level owner")
    metadata = _read_lock_metadata(path)
    if not metadata or metadata.get("repo") != root or not secrets.compare_digest(str(metadata.get("token", "")), str(token)):
        raise RecorderLockError(f"ERROR: invalid recorder participant for {path}; cause: missing, forged, expired, or cross-repo token; fix: invoke as a top-level owner")
    try:
        chain_value = json.loads(os.environ.get(RECORDER_DELEGATION_CHAIN_ENV, ""))
    except json.JSONDecodeError:
        chain_value = None
    if not isinstance(chain_value, list) or len(chain_value) < 2 or any(not isinstance(item, str) for item in chain_value):
        raise RecorderLockError("ERROR: recorder delegation chain missing or malformed; cause: participant capability is incomplete; fix: invoke through an allowlisted recorder parent")
    chain = tuple(chain_value)
    if chain[0] != metadata.get("command") or chain[-1] != command:
        raise RecorderLockError("ERROR: recorder delegation chain mismatch; cause: owner/child command does not match capability; fix: invoke through the current composite command graph")
    for parent, child in zip(chain, chain[1:]):
        if child not in RECORDER_DELEGATION_GRAPH.get(parent, set()):
            raise RecorderLockError(f"ERROR: recorder delegation denied: {parent} -> {child}; cause: edge is outside the current composite call graph; fix: invoke the child as a top-level owner")
    return RecorderLockState(path, token, participant=True, chain=chain)


def _write_all(fd, data):
    view = memoryview(data)
    offset = 0
    while offset < len(view):
        written = os.write(fd, view[offset:])
        if written <= 0:
            raise OSError("recorder lock metadata write made no progress")
        offset += written


@contextmanager
def recorder_lock(root, command):
    root = os.path.realpath(os.fspath(root))
    if RECORDER_LOCK_ENV in os.environ:
        inherited = os.environ.get(RECORDER_LOCK_ENV, "")
        try:
            participant = validate_recorder_participant(root, inherited, command)
        except RecorderLockError:
            participant = None
        if participant is not None:
            yield participant
            return
    path = _lock_path(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    token = secrets.token_hex(32)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise _lock_conflict(path, _read_lock_metadata(path))
    state = None
    metadata_published = False
    try:
        stat = os.fstat(fd)
        state = RecorderLockState(path, token, identity=(stat.st_dev, stat.st_ino), chain=(command,))
        metadata = {"repo": root, "pid": os.getpid(), "command": command, "started": time.time(), "token": token}
        _write_all(fd, json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        os.fsync(fd)
        os.close(fd)
        fd = None
        metadata_published = True
        yield state
    finally:
        active_error = sys.exc_info()[0] is not None
        close_error = None
        if fd is not None:
            try:
                os.close(fd)
            except OSError as exc:
                close_error = exc
        if state is not None:
            try:
                path_stat = os.stat(path)
                identity = (path_stat.st_dev, path_stat.st_ino)
            except FileNotFoundError:
                identity = None
            current = _read_lock_metadata(path) if metadata_published else None
            owns_identity = identity == state.identity
            owns_token = current is not None and secrets.compare_digest(str(current.get("token", "")), token)
            if owns_identity and (not metadata_published or owns_token):
                os.unlink(path)
            elif identity is not None:
                raise RecorderLockError(f"ERROR: recorder lock ownership lost at {path}; cause: identity/token changed; fix: preserve the replacement lock and inspect its owner")
        if close_error is not None and not active_error:
            raise close_error


def read_repository_snapshot(root):
    root = os.path.realpath(os.fspath(root))
    pools = {
        "bug": ("openspec/issues/buglist/*.md", "openspec/buglists/*.md"),
        "todo": ("openspec/issues/todolist/*.md", "openspec/todolists/*.md"),
    }
    snapshot = []
    seen_paths = set()
    for pool, patterns in pools.items():
        for pattern in patterns:
            for path in sorted(glob.glob(os.path.join(root, pattern))):
                real = os.path.realpath(path)
                if real in seen_paths:
                    continue
                seen_paths.add(real)
                document = read_recorder_document(path, pool)
                rel = os.path.relpath(path, root)
                snapshot.append((pool, path, rel, document))
    return snapshot


def repository_semantic_occurrences(root, snapshot=None):
    snapshot = read_repository_snapshot(root) if snapshot is None else snapshot
    occurrences = []
    for pool, _path, rel, document in snapshot:
        occurrences.extend((key, raw_id, pool, rel) for key, raw_id in document["effective_occurrences"])
    by_key = {}
    for key, raw_id, pool, rel in occurrences:
        by_key.setdefault(key, []).append((raw_id, pool, rel))
    duplicates = {key: places for key, places in by_key.items() if len(places) > 1}
    if duplicates:
        key, places = sorted(duplicates.items())[0]
        rendered = ", ".join(f"{raw}@{pool}:{rel}" for raw, pool, rel in places)
        raise ValueError(f"ERROR: semantic ID 重复; cause: repository semantic ID conflict {key}: {rendered}; fix: resolve all aliases/pools before retry")
    return by_key


def recorder_child_env(command, token=None):
    if token is None:
        token = _ACTIVE_RECORDER_TOKEN
    env = dict(os.environ)
    env.pop(RECORDER_LOCK_ENV, None)
    env.pop(RECORDER_DELEGATION_CHAIN_ENV, None)
    if token:
        if command not in RECORDER_PARTICIPANT_ALLOWLIST:
            raise RecorderLockError(f"ERROR: child command not allowlisted: {command}; cause: token forwarding denied; fix: run without participant capability")
        chain = _ACTIVE_RECORDER_CHAIN
        if not chain or command not in RECORDER_DELEGATION_GRAPH.get(chain[-1], set()):
            parent = chain[-1] if chain else "<missing>"
            raise RecorderLockError(f"ERROR: recorder delegation denied: {parent} -> {command}; cause: edge is outside the current composite call graph; fix: invoke the child as a top-level owner")
        env[RECORDER_LOCK_ENV] = token
        env[RECORDER_DELEGATION_CHAIN_ENV] = json.dumps([*chain, command], separators=(",", ":"))
    return env


def _frontmatter_error(problem, cause, fix="修正 recorder frontmatter 后重试"):
    raise ValueError(f"ERROR: {problem}; cause: {cause}; fix: {fix}")


def _validate_unicode_scalar(value, field, item_id="?"):
    if not isinstance(value, str):
        _frontmatter_error(f"{item_id}.{field} 类型非法", "必须是 string")
    for char in value:
        codepoint = ord(char)
        if 0xD800 <= codepoint <= 0xDFFF:
            _frontmatter_error(
                f"{item_id}.{field} 含孤立 surrogate U+{codepoint:04X}",
                "索引只接受 Unicode scalar values",
            )


def _json_object_no_duplicates(text, item_id):
    def pairs_hook(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                _frontmatter_error(f"{item_id} JSON key 重复", key)
            result[key] = value
        return result

    try:
        value = json.loads(text, object_pairs_hook=pairs_hook)
    except json.JSONDecodeError as exc:
        _frontmatter_error(f"{item_id} JSON 非法", str(exc))
    if not isinstance(value, dict):
        _frontmatter_error(f"{item_id} item 非法", "必须是 JSON object")
    return value


def _validated_recorder_model(model, normalize_empty=False):
    if not isinstance(model, dict) or set(model) != {"schema", "pool", "mode", "items"}:
        _frontmatter_error("recorder schema 非法", "顶层必须精确包含 schema/pool/mode/items")
    if type(model["schema"]) is not int or model["schema"] != 1:
        _frontmatter_error("recorder schema 非法", f"仅支持 schema=1，收到 {model['schema']!r}")
    pool = model["pool"]
    if pool not in RECORDER_POOL_CONFIG:
        _frontmatter_error("recorder pool 非法", repr(pool))
    if model["mode"] not in {"canonical", "overlay"}:
        _frontmatter_error("recorder mode 非法", repr(model["mode"]))
    if not isinstance(model["items"], dict):
        _frontmatter_error("recorder items 非法", "必须是 map")
    specific_field, specific_values, status_values = RECORDER_POOL_CONFIG[pool]
    fields = {"module", "summary", specific_field, "status", "time", "change", "batch"}
    normalized = {"schema": 1, "pool": pool, "mode": model["mode"], "items": {}}
    semantic_ids = set()
    for item_id, original in model["items"].items():
        if not isinstance(item_id, str) or not CANONICAL_ID_RE.fullmatch(item_id):
            _frontmatter_error(f"ID 非 canonical ASCII spelling", repr(item_id))
        semantic_key = (item_id[0], int(item_id[1:]))
        if semantic_key in semantic_ids:
            _frontmatter_error("semantic ID 重复", item_id)
        semantic_ids.add(semantic_key)
        if not isinstance(original, dict) or set(original) != fields:
            got = sorted(original) if isinstance(original, dict) else type(original).__name__
            _frontmatter_error(f"{item_id} 字段集合非法", f"expected={sorted(fields)} got={got}")
        item = dict(original)
        for field in ("module", "summary", "time"):
            _validate_unicode_scalar(item[field], field, item_id)
        if not item["module"].strip() or not item["summary"].strip():
            _frontmatter_error(f"{item_id} required string 为空", "module/summary 必须含非空白 scalar")
        for field in ("change", "batch"):
            if normalize_empty and item[field] == "":
                item[field] = None
            if item[field] is not None:
                _validate_unicode_scalar(item[field], field, item_id)
                if item[field] == "":
                    _frontmatter_error(f"{item_id}.{field} 非 canonical empty", "必须写 JSON null")
        _validate_unicode_scalar(item[specific_field], specific_field, item_id)
        _validate_unicode_scalar(item["status"], "status", item_id)
        if item[specific_field] not in specific_values:
            _frontmatter_error(f"{item_id}.{specific_field} 枚举越域", repr(item[specific_field]))
        if item["status"] not in status_values:
            _frontmatter_error(f"{item_id}.status 枚举越域", repr(item["status"]))
        normalized["items"][item_id] = item
    return normalized


def _id_semantic_sort(item_id):
    return item_id[0], int(item_id[1:])


def _legacy_semantic_id_key(item_id):
    match = re.fullmatch(r"([A-Z])([0-9]+)", item_id, re.ASCII)
    return (match.group(1), int(match.group(2))) if match else None


def render_recorder_namespace(model, eol=b"\n"):
    if eol not in {b"\n", b"\r\n"}:
        _frontmatter_error("EOL 非法", repr(eol))
    model = _validated_recorder_model(model, normalize_empty=True)
    specific_field = RECORDER_POOL_CONFIG[model["pool"]][0]
    order = ("module", "summary", specific_field, "status", "time", "change", "batch")
    lines = [
        "sdflow-issues:",
        "  schema: 1",
        f"  pool: {model['pool']}",
        f"  mode: {model['mode']}",
    ]
    if not model["items"]:
        lines.append("  items: {}")
    else:
        lines.append("  items:")
        for item_id in sorted(model["items"], key=_id_semantic_sort):
            item = model["items"][item_id]
            ordered = {field: item[field] for field in order}
            payload = json.dumps(ordered, ensure_ascii=False, separators=(",", ":"))
            payload = payload.replace("\u0085", "\\u0085").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
            lines.append(f"    {item_id}: {payload}")
    return eol.join(line.encode("utf-8") for line in lines) + eol


def _split_envelope(raw):
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        _frontmatter_error("encoding 非法", "UTF-16 BOM 不受支持")
    bom = UTF8_BOM if raw.startswith(UTF8_BOM) else b""
    content = raw[len(bom):]
    if b"\r" in content.replace(b"\r\n", b""):
        _frontmatter_error("EOL 非法", "发现 lone CR")
    try:
        content.decode("utf-8")
    except UnicodeDecodeError as exc:
        _frontmatter_error("encoding 非法", str(exc))
    if not content.startswith(b"---\n") and not content.startswith(b"---\r\n"):
        return bom, None, raw[len(bom):], b"\r\n" if b"\r\n" in content else b"\n"
    eol = b"\r\n" if content.startswith(b"---\r\n") else b"\n"
    marker = eol + b"---" + eol
    close = content.find(marker, 3)
    if close < 0:
        _frontmatter_error("frontmatter envelope 非法", "closer 缺失或无行终止")
    start = 3 + len(eol)
    envelope = content[start:close + len(eol)]
    body = content[close + len(marker):]
    return bom, envelope, body, eol


def _find_recorder_span(envelope, eol):
    if envelope is None:
        return None
    lines = envelope.splitlines(keepends=True)
    starts = []
    offset = 0
    active_entry = False
    for index, raw_line in enumerate(lines):
        line = raw_line[:-len(eol)] if raw_line.endswith(eol) else raw_line
        if b"\t" in line:
            _frontmatter_error("shared envelope lexical profile 非法", "tab")
        if line.startswith(b" ") and not active_entry and b"sdflow-issues" in line:
            _frontmatter_error("namespace ownership 歧义", line.decode("utf-8", "replace"))
        match = re.match(rb"^([A-Za-z0-9][A-Za-z0-9_-]*):(.*)$", line)
        if match:
            starts.append((index, offset, match.group(1).decode("ascii")))
            active_entry = True
        elif (not line.startswith((b" ", b"#")) and re.match(
                rb"^(?:['\"]sdflow-issues['\"]|\?\s*sdflow-issues|sdflow-issues\s+:)", line)):
            _frontmatter_error("namespace ownership 歧义", line.decode("utf-8", "replace"))
        elif line.startswith(b" ") and not active_entry:
            _frontmatter_error("shared envelope lexical profile 非法", "orphan indented continuation")
        elif line and not line.startswith((b" ", b"#")):
            _frontmatter_error("shared envelope lexical profile 非法", line.decode("utf-8", "replace"))
        offset += len(raw_line)
    recorder = [entry for entry in starts if entry[2] == "sdflow-issues"]
    if len(recorder) > 1:
        _frontmatter_error("namespace 重复", "sdflow-issues")
    if not recorder:
        return None
    _, start, _ = recorder[0]
    following = [entry[1] for entry in starts if entry[1] > start]
    end = min(following) if following else len(envelope)
    while end > start:
        previous_start = envelope.rfind(eol, start, end - len(eol))
        previous_start = start if previous_start < 0 else previous_start + len(eol)
        previous = envelope[previous_start:end]
        if previous.strip() and not previous.lstrip().startswith(b"#"):
            break
        end = previous_start
    return start, end


def _parse_recorder_namespace(namespace, eol):
    if any(char in namespace.decode("utf-8") for char in ("\u0085", "\u2028", "\u2029")):
        _frontmatter_error("recorder namespace 含 raw Unicode line break", "必须使用 JSON escape")
    lines = namespace.decode("utf-8").splitlines()
    if len(lines) < 5 or lines[0] != "sdflow-issues:":
        _frontmatter_error("recorder namespace 非法", "header/字段不完整")
    expected_prefixes = ("  schema: ", "  pool: ", "  mode: ")
    if any(not lines[index + 1].startswith(prefix) for index, prefix in enumerate(expected_prefixes)):
        _frontmatter_error("recorder namespace 非 canonical", "schema/pool/mode 顺序或缩进错误")
    if lines[1] != "  schema: 1":
        _frontmatter_error("recorder schema 非法", lines[1])
    pool = lines[2][len("  pool: "):]
    mode = lines[3][len("  mode: "):]
    if lines[4] == "  items: {}":
        if len(lines) != 5:
            _frontmatter_error("recorder items 非法", "empty map 后存在额外内容")
        items = {}
    elif lines[4] == "  items:":
        if len(lines) == 5:
            _frontmatter_error("recorder items 非法", "空 map 必须写 items: {}，裸 items: 禁止")
        items = {}
        for line in lines[5:]:
            match = re.fullmatch(r"    ([A-Z][1-9][0-9]*): (\{.*\})", line)
            if not match:
                _frontmatter_error("recorder item 行非法", line)
            item_id = match.group(1)
            if item_id in items:
                _frontmatter_error("recorder ID 重复", item_id)
            items[item_id] = _json_object_no_duplicates(match.group(2), item_id)
    else:
        _frontmatter_error("recorder items 非法", "必须是 items: 或 items: {}")
    return _validated_recorder_model({"schema": 1, "pool": pool, "mode": mode, "items": items})


def _legacy_table_region_count(body):
    return len(_legacy_table_sections(body.decode("utf-8").splitlines(keepends=True)))


def parse_recorder_document(raw, expected_pool):
    if not isinstance(raw, bytes):
        _frontmatter_error("document 输入非法", "必须是 bytes")
    bom, envelope, body, eol = _split_envelope(raw)
    span = _find_recorder_span(envelope, eol)
    if span is None:
        count = _legacy_table_region_count(body)
        if count != 1:
            _frontmatter_error("legacy 总览区域非法", f"count={count}")
        result = {"format": "legacy", "model": None, "raw": raw, "body": body,
                  "eol": eol, "bom": bom, "envelope": envelope, "namespace_span": None}
    else:
        start, end = span
        namespace = envelope[start:end]
        model = _parse_recorder_namespace(namespace, eol)
        if model["pool"] != expected_pool:
            _frontmatter_error("recorder pool/path 不符", f"expected={expected_pool} actual={model['pool']}")
        count = _legacy_table_region_count(body)
        expected_count = 0 if model["mode"] == "canonical" else 1
        if count != expected_count:
            _frontmatter_error("mode-structure mismatch", f"mode={model['mode']} legacy_regions={count}")
        result = {"format": model["mode"], "model": model, "raw": raw, "body": body,
                  "eol": eol, "bom": bom, "envelope": envelope,
                  "namespace_span": (start, end)}
    lines = body.decode("utf-8").splitlines(keepends=True)
    section = split_sections(lines)
    result.update({
        "lines": lines,
        "section": section,
        "rows": parse_table_rows(lines, section) if section else {},
        "legacy_blocks": block_ranges(lines),
    })
    result["marker_blocks"], result["marker_problems"] = marker_block_ranges(lines)
    return _build_effective_snapshot(result, expected_pool)


def read_recorder_document(path, expected_pool):
    try:
        with open(path, "rb") as stream:
            raw = stream.read()
        return parse_recorder_document(raw, expected_pool)
    except ValueError as exc:
        message = str(exc)
        detail = message[len("ERROR: "):] if message.startswith("ERROR: ") else message
        raise ValueError(f"ERROR: file={path}: {detail}") from None


# ── 路径与文件 ───────────────────────────────────────────────────────────────

def repo_root(start="."):
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start, capture_output=True, text=True, check=True,
            env=recorder_child_env("git", token=False),
        )
        return out.stdout.strip()
    except Exception:
        return os.path.abspath(start)


BRANCH_PREFIX_RE = re.compile(r"^[a-z]+/")


def detect_change(root):
    """自动探测当前所处 OpenSpec change 名，供 add 时记录来源（可被 --json 里的 change 覆盖）。
    优先级：openspec/changes/ 下唯一未归档目录 → git branch 名去前缀 → 空字符串（多 change 并行/
    无法判断时交给模型显式传 change，不瞎猜）。"""
    changes_dir = os.path.join(root, "openspec", "changes")
    dirs = []
    if os.path.isdir(changes_dir):
        dirs = sorted(
            d for d in os.listdir(changes_dir)
            if d != "archive" and os.path.isdir(os.path.join(changes_dir, d))
        )
    if len(dirs) == 1:
        return dirs[0]
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root, capture_output=True, text=True, check=True,
            env=recorder_child_env("git", token=False),
        )
        branch = out.stdout.strip()
    except Exception:
        branch = ""
    candidate = BRANCH_PREFIX_RE.sub("", branch) if branch else ""
    if candidate and (not dirs or candidate in dirs):
        return candidate
    return ""


# ── 关联文档 doc ─────────────────────────────────────────────────────────────

def normalize_doc_paths(doc):
    """把 add 时传入的 doc 字段（str / list[str] / 空）归一化为 list[str]，
    每项保证以 'openspec/' 开头（缺前缀则补）。不强制要求 .md 结尾——
    非 .md 路径仍会被记录，只是不会被 review 工具的 linkify 正则识别为可点击链接
    （该正则只认 `openspec/...同.md` 结尾的反引号内联代码）。"""
    if not doc:
        return []
    items = [doc] if isinstance(doc, str) else list(doc)
    out = []
    for item in items:
        item = (item or "").strip()
        if not item:
            continue
        if not item.startswith("openspec/"):
            item = "openspec/" + item.lstrip("/")
        out.append(item)
    return out


def validate_doc_paths(root, docs):
    """软校验：文档路径（相对 root）不存在只打 stderr 警告，不阻断记录——
    这个功能的目的是鼓励关联文档，不是做门禁。"""
    for d in docs:
        if not os.path.isfile(os.path.join(root, d)):
            print(f"WARNING: 关联文档路径不存在：{d}", file=sys.stderr)


def auto_default_doc(root, change):
    """change 已知但显式 doc 为空时，尽力探测关联文档，按优先级：
    1) openspec/changes/{change}/design.md
    2) openspec/changes/{change}/proposal.md
    3) openspec/changes/archive/*-{change}/design.md（glob，归档目录名前缀是不可预测的日期）
    4) 同上但 proposal.md
    归档层的歧义检查只做一次、在“目录”这一级：先看 `*-{change}` 这个 glob 命中几个归档目录——
    不是恰好 1 个就整层跳过（design.md/proposal.md 都不试），不能因为其中一个目录碰巧只有
    proposal.md 就把它当成唯一匹配悄悄采用（那样目录本身仍是歧义的）。只有 glob 恰好命中 1 个
    目录时，才在该目录内按 design.md → proposal.md 的优先级取值。
    全部落空则返回 []（best-effort，不是必须项）。仅在调用方没有显式传 doc 时才应调用本函数，
    不覆盖显式值。"""
    if not change:
        return []
    for name in ("design.md", "proposal.md"):
        candidate = os.path.join("openspec", "changes", change, name)
        if os.path.isfile(os.path.join(root, candidate)):
            return [candidate.replace(os.sep, "/")]
    archive_pattern = os.path.join(root, "openspec", "changes", "archive", f"*-{change}")
    archive_dirs = [d for d in glob.glob(archive_pattern) if os.path.isdir(d)]
    if len(archive_dirs) == 1:
        archive_dir = archive_dirs[0]
        for name in ("design.md", "proposal.md"):
            candidate = os.path.join(archive_dir, name)
            if os.path.isfile(candidate):
                rel = os.path.relpath(candidate, root)
                return [rel.replace(os.sep, "/")]
    return []


def todolists_dir(root):
    return os.path.join(root, "openspec", "issues", "todolist")


def legacy_todolists_dir(root):
    return os.path.join(root, "openspec", "todolists")


def _dated_dirs(root):
    """新在前（写落新），旧只读兼容——过渡期 dual-read 两目录（Phase B Q1 加固，镜像 buglist）。
    下游只 update 未迁移旧数据时，若 next_id 只看新目录会从 T1 重数、撞旧目录已有的号；
    扫两目录取并集 max+1 规避这个撞号风险。"""
    return [todolists_dir(root), legacy_todolists_dir(root)]


def list_files(root):
    out = []
    for d in _dated_dirs(root):  # 新在前（目录序），不可对拼接后的全路径整体 sorted
        if os.path.isdir(d):
            files = [
                os.path.join(d, f) for f in os.listdir(d)
                if re.match(r"[0-9]{4}-[0-9]{2}-todolist\.md$", f, re.ASCII)
            ]
            out += sorted(files)  # 各目录内部按文件名（=月份）排序
    return out


def this_month(override=None):
    if override:
        return override
    return datetime.date.today().strftime("%Y-%m")


def file_for_month(root, month):
    return os.path.join(todolists_dir(root), f"{month}-todolist.md")


HEADER_TMPL = """# {month} TODO

> 项目：{project}
"""


def ensure_file(root, month, project):
    path = file_for_month(root, month)
    return path


def _reject_line_unsafe(value, field):
    if value is None:
        return
    if any(char in str(value) for char in ("\r", "\n", "\0")):
        _frontmatter_error(
            f"字段 {field} 非法", f"CR/LF/NUL 不能写入 Markdown 单行结构：{value!r}",
            f"为 {field} 提供不含 CR/LF/NUL 的单行值后重试",
        )


def _display_title(summary, title=None):
    if title is not None:
        _reject_line_unsafe(title, "title")
        return str(title)
    return re.sub(r"\s+", " ", summary).strip()


def _summary_blockquote(summary):
    return "\n".join(f"> {line}" for line in re.split(r"\r\n|\r|\n", summary))


def _escape_user_markers(value):
    lines = re.split(r"\r\n|\r|\n", str(value))
    return "\n".join(
        line.replace("<!--", "&lt;!--").replace("-->", "--&gt;")
        if _match_marker_line(line) else line
        for line in lines
    )


def _canonical_document(model, body, eol=b"\n"):
    return b"---" + eol + render_recorder_namespace(model, eol) + b"---" + eol + body


def _render_recorder_document(document, model, body):
    eol = document["eol"]
    namespace = render_recorder_namespace(model, eol)
    envelope = document["envelope"]
    if envelope is None:
        return document["bom"] + b"---" + eol + namespace + b"---" + eol + body
    span = document["namespace_span"]
    if span is None:
        separator = b"" if not envelope or envelope.endswith(eol) else eol
        envelope = envelope + separator + namespace
    else:
        envelope = envelope[:span[0]] + namespace + envelope[span[1]:]
    return document["bom"] + b"---" + eol + envelope + b"---" + eol + body


# ── ID 扫描 ──────────────────────────────────────────────────────────────────

def _ids_in_files(paths, prefix=None):
    ids = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            for line in f:
                # 只认状态总览表里的行（以 | 开头且第二列是 ID）
                m = re.match(r"\|\s*([A-Z][0-9]+)\s*\|", line, re.ASCII)
                if m:
                    pid = m.group(1)
                    if prefix is None or pid.startswith(prefix):
                        ids.append(pid)
    return ids


def all_ids(root, prefix=None):
    return _ids_in_files(list_files(root), prefix)


def next_id(root, prefix=DEFAULT_PREFIX, semantic=None):
    prefix = validate_prefix(prefix)
    semantic = repository_semantic_occurrences(root) if semantic is None else semantic
    nums = [number for (item_prefix, number) in semantic if item_prefix == prefix]
    n = (max(nums) + 1) if nums else 1
    while (prefix, n) in semantic:
        n += 1
    return f"{prefix}{n}"


def _id_sort_key(pid):
    m = ID_RE.match(pid)
    return (m.group(1), int(m.group(2))) if m else (pid, 0)


def id_conflicts(root):
    """跨路径 ID 冲突检测（Phase B Q1 加固，镜像 buglist）：同一 ID 若同时出现在新
    `openspec/issues/todolist/` 和旧 `openspec/todolists/` 两处，说明过渡期内新旧数据可能已经
    手工/脚本各自分配过号，存在撞号风险。只读、不阻断——调用方（CLI）自行决定打印警告还是忽略。"""
    new_dir, old_dir = todolists_dir(root), legacy_todolists_dir(root)
    new_files = [p for p in list_files(root) if os.path.dirname(p) == new_dir]
    old_files = [p for p in list_files(root) if os.path.dirname(p) == old_dir]
    new_ids = set(_ids_in_files(new_files))
    old_ids = set(_ids_in_files(old_files))
    return sorted(new_ids & old_ids, key=_id_sort_key)


# ── 表 / 块 解析 ─────────────────────────────────────────────────────────────

def split_sections(lines):
    sections = _legacy_table_sections(lines)
    return sections[0] if sections else None


def _legacy_table_sections(lines):
    sections = []
    fence = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        marker = re.match(r"^(```+|~~~+)", stripped)
        if marker:
            token = marker.group(1)[0]
            if fence is None:
                fence = token
            elif token == fence:
                fence = None
            continue
        if fence is not None or not re.match(r"^##\s+状态总览(?:\s|（|$)", line):
            continue
        table_hdr = None
        for candidate in range(index + 1, min(len(lines), index + 6)):
            candidate_line = lines[candidate]
            if not candidate_line.strip() or candidate_line.lstrip().startswith("<!--"):
                continue
            if re.match(r"\|\s*ID\s*\|", candidate_line):
                table_hdr = candidate
            break
        if table_hdr is None:
            continue
        rows_start = table_hdr + 2
        rows_end = rows_start
        while rows_end < len(lines) and lines[rows_end].lstrip().startswith("|"):
            rows_end += 1
        sections.append({"table_hdr": table_hdr, "rows_start": rows_start, "rows_end": rows_end})
    return sections


def parse_table_rows(lines, sec):
    rows = {}
    for i in range(sec["rows_start"], sec["rows_end"]):
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        if len(cells) >= 5:
            rows[cells[0]] = {"line": i, "cells": cells}
    return rows


def block_ranges(lines):
    out = {}
    starts = []
    for i, ln in enumerate(lines):
        m = re.match(r"##\s+([A-Z][0-9]+)\s*:", ln, re.ASCII)
        if m:
            starts.append((i, m.group(1)))
    for idx, (i, bid) in enumerate(starts):
        end = len(lines)
        for j in range(i + 1, len(lines)):
            if lines[j].strip() == "---" or re.match(r"##\s+[A-Z][0-9]+\s*:", lines[j], re.ASCII):
                end = j
                break
        out[bid] = (i, end)
    return out


_ISSUE_MARKER_LINE_RE = re.compile(
    r"^<!-- sdflow-issue-block:(start|end) id=([A-Z][1-9][0-9]*) -->[ \t]*$", re.ASCII
)


def _match_marker_line(line):
    return _ISSUE_MARKER_LINE_RE.fullmatch(line.rstrip("\r\n"))


def marker_block_ranges(lines):
    """解析新格式成对 marker；返回 (ranges, problems)，不回退 heading heuristic。"""
    ranges, problems = {}, []
    active = None
    for index, line in enumerate(lines):
        marker = _match_marker_line(line)
        if marker and marker.group(1) == "start":
            item_id = marker.group(2)
            if active is not None:
                problems.append(f"marker 嵌套：{active[0]} → {item_id}（line {index + 1}）")
            elif item_id in ranges:
                problems.append(f"marker block 重复：{item_id}（line {index + 1}）")
            else:
                active = (item_id, index)
        elif marker:
            item_id = marker.group(2)
            if active is None:
                problems.append(f"orphan end marker：{item_id}（line {index + 1}）")
            elif active[0] != item_id:
                problems.append(
                    f"marker ID 错配：start={active[0]} end={item_id}（line {index + 1}）"
                )
                active = None
            else:
                ranges[item_id] = (active[1], index + 1)
                active = None
    if active is not None:
        problems.append(f"marker 缺 end：{active[0]}（line {active[1] + 1}）")
    return ranges, problems


def _legacy_item_from_row(item_id, info, pool):
    cells = info["cells"]
    specific_field = RECORDER_POOL_CONFIG[pool][0]
    return {
        "module": cells[1],
        "summary": cells[2],
        specific_field: cells[3],
        "status": cells[4],
        "time": cells[5] if len(cells) > 5 else None,
        "change": cells[6] if len(cells) > 6 and cells[6] != "-" else None,
        "batch": cells[7] if len(cells) > 7 and cells[7] else None,
    }


def _build_effective_snapshot(result, expected_pool):
    lines = result["lines"]
    section = result["section"]
    rows = result["rows"]
    legacy_blocks = result["legacy_blocks"]
    marker_blocks = result["marker_blocks"]
    frontmatter_items = result["model"]["items"] if result["model"] else {}
    frontmatter_keys = {_legacy_semantic_id_key(item_id) for item_id in frontmatter_items}
    problems = list(result["marker_problems"])
    raw_ids = []
    if section:
        for index in range(section["rows_start"], section["rows_end"]):
            cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
            raw_id = cells[0] if cells else "?"
            raw_ids.append(raw_id)
            if len(cells) not in (7, 8):
                problems.append(f"{raw_id} 行 arity 异常：{len(cells)} 列（应 8/7）")
    invalid_ids = [raw_id for raw_id in raw_ids if _legacy_semantic_id_key(raw_id) is None]
    if invalid_ids:
        _frontmatter_error("non-ASCII ID", repr(invalid_ids[0]))
    occurrences = [
        (_legacy_semantic_id_key(raw_id) or ("raw", raw_id), raw_id)
        for raw_id in raw_ids
        if _legacy_semantic_id_key(raw_id) not in frontmatter_keys
    ]
    occurrences.extend((_legacy_semantic_id_key(item_id), item_id) for item_id in frontmatter_items)
    by_key = {}
    for semantic_key, raw_id in occurrences:
        by_key.setdefault(semantic_key, []).append(raw_id)
    duplicates = {key: ids for key, ids in by_key.items() if len(ids) > 1}
    if duplicates:
        key, ids = sorted(duplicates.items(), key=lambda entry: str(entry[0]))[0]
        _frontmatter_error("semantic ID 重复", f"key={key} ids={','.join(ids)}")
    if result["format"] == "legacy":
        for item_id in marker_blocks:
            problems.append(f"marker-only legacy：{item_id}")
    else:
        if expected_pool == "bug":
            for item_id in frontmatter_items:
                if item_id not in marker_blocks:
                    problems.append(f"frontmatter 有 {item_id} 但缺 marker block")
        for item_id in marker_blocks:
            if item_id not in frontmatter_items:
                problems.append(f"marker block 有 {item_id} 但缺 frontmatter item")
    legacy_owned = {
        item_id: info for item_id, info in rows.items()
        if _legacy_semantic_id_key(item_id) not in frontmatter_keys
    }
    for item_id in legacy_owned:
        if expected_pool == "bug" and item_id not in legacy_blocks:
            problems.append(f"表有 {item_id} 但缺详细块")
    for item_id in legacy_blocks:
        if item_id not in rows and result["format"] == "legacy":
            problems.append(f"块有 {item_id} 但缺总览表行")
    for item_id, info in legacy_owned.items():
        if item_id not in legacy_blocks:
            continue
        start, end = legacy_blocks[item_id]
        block_status = next((match.group(1) for line in lines[start:end]
                             if (match := re.match(r"\|\s*状态\s*\|\s*(\w+)", line))), None)
        if block_status and block_status != info["cells"][4]:
            problems.append(
                f"{item_id} 状态不一致（表={info['cells'][4]} 块={block_status}）"
            )
    effective_items = {
        item_id: _legacy_item_from_row(item_id, info, expected_pool)
        for item_id, info in legacy_owned.items()
    }
    effective_items.update(frontmatter_items)
    result.update({
        "effective_items": effective_items,
        "effective_occurrences": occurrences,
        "problems": problems,
    })
    return result


def _find_row_file(root, item_id):
    """定位含 item_id 的状态总览表行所在的月度文件（T5：从 `cmd_set_status`/
    `cmd_triage` 抽出——两处遍历 `list_files` 找含该 ID 表行的逻辑逐字相同，
    镜像 buglist.py 的同名 helper，各自模块内抽、不跨 recorder 共享，D4）。
    返回 (path, lines, sec, rows)；找不到则 `_die` 退出（沿用两处原有的错误文案），
    调用方无需再自行判空。"""
    for path in list_files(root):
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        sec = split_sections(lines)
        rows = parse_table_rows(lines, sec) if sec else {}
        if item_id in rows:
            return path, lines, sec, rows
    _die(f"未找到 ID：{item_id}")


def _canonical_from_key(key):
    return f"{key[0]}{key[1]}"


def _find_item_document(root, requested_id, pool):
    key = semantic_id_key(requested_id, allow_legacy=True)
    canonical = _canonical_from_key(key)
    noncanonical_request = requested_id != canonical
    found = []
    snapshot = read_repository_snapshot(root)
    repository_semantic_occurrences(root, snapshot)
    for candidate_pool, candidate, _rel, document in snapshot:
        if candidate_pool != pool:
            continue
        for raw_id, item in document["effective_items"].items():
            if _legacy_semantic_id_key(raw_id) == key:
                if noncanonical_request and not (
                        raw_id == requested_id
                        and raw_id in document["rows"]
                        and not (document["model"] and canonical in document["model"]["items"])):
                    continue
                found.append((candidate, document, raw_id, dict(item)))
    if not found:
        _die(f"未找到 ID：{requested_id}")
    if len(found) != 1:
        _die(f"ID 定位歧义：{requested_id}（命中 {len(found)} 处）")
    return found[0]


def _legacy_block_range(document, raw_id, path):
    starts = []
    key = _legacy_semantic_id_key(raw_id)
    for index, line in enumerate(document["lines"]):
        match = re.match(r"##\s+([A-Z][0-9]+)\s*:", line, re.ASCII)
        if match and _legacy_semantic_id_key(match.group(1)) == key:
            starts.append(index)
    if len(starts) != 1:
        _frontmatter_error(
            f"file={path} legacy block 无法安全包裹",
            f"id={raw_id} candidates={len(starts)}",
            "修正为唯一 legacy block 后重试",
        )
    start = starts[0]
    end = len(document["lines"])
    for index in range(start + 1, len(document["lines"])):
        line = document["lines"][index]
        if line.strip() == "---" or re.match(r"##\s+[A-Z][0-9]+\s*:", line, re.ASCII):
            end = index
            break
    for index in range(start, end):
        if _match_marker_line(document["lines"][index]):
            _frontmatter_error(
                f"file={path} legacy marker collision",
                f"id={raw_id} line={index + 1}",
                "删除或转义候选块内预存 marker 后重试",
            )
    return start, end


def _splice_body_lines(document, insertions):
    rendered = []
    for index, line in enumerate(document["lines"]):
        rendered.extend(insertions.get(index, ()))
        rendered.append(line.encode("utf-8"))
    rendered.extend(insertions.get(len(document["lines"]), ()))
    return b"".join(rendered)


def _reject_document_mutation(document, path):
    structural = [
        problem for problem in document["problems"]
        if "marker" in problem or "frontmatter" in problem
    ]
    if structural:
        _frontmatter_error(
            f"file={path} marker/ownership 结构非法", structural[0], "修正结构后重试",
        )


def _preflight_target_legacy_block(document, raw_id, path):
    canonical = _canonical_from_key(_legacy_semantic_id_key(raw_id))
    if document["model"] and canonical in document["model"]["items"]:
        return
    candidates = [raw for raw in document["legacy_blocks"]
                  if _legacy_semantic_id_key(raw) == _legacy_semantic_id_key(raw_id)]
    if candidates:
        _legacy_block_range(document, raw_id, path)


def _promotion_insertions(document, raw_id, canonical, path, item, history, require_block):
    eol = document["eol"]
    candidates = [raw for raw in document["legacy_blocks"]
                  if _legacy_semantic_id_key(raw) == _legacy_semantic_id_key(raw_id)]
    if candidates or require_block:
        b_start, b_end = _legacy_block_range(document, raw_id, path)
        boundary = ()
        if b_end and not document["lines"][b_end - 1].endswith(("\n", "\r")):
            boundary = (eol,)
        return {
            b_start: (f"<!-- sdflow-issue-block:start id={canonical} -->".encode("ascii") + eol,),
            b_end: (*boundary, *history,
                    f"<!-- sdflow-issue-block:end id={canonical} -->".encode("ascii") + eol),
        }
    minimal = (
        eol + f"<!-- sdflow-issue-block:start id={canonical} -->".encode("ascii") + eol
        + f"## {canonical}: {_display_title(item['summary'])}".encode("utf-8") + eol
        + _summary_blockquote(item["summary"]).encode("utf-8") + eol
        + b"".join(history)
        + f"<!-- sdflow-issue-block:end id={canonical} -->".encode("ascii") + eol
    )
    return {len(document["lines"]): (minimal,)}


def _validated_rendered_mutation(rendered, pool, canonical, require_marker, path):
    candidate = parse_recorder_document(rendered, pool)
    structural = [
        problem for problem in candidate["problems"]
        if "marker" in problem or "frontmatter" in problem
    ]
    if canonical not in candidate["model"]["items"]:
        structural.append(f"frontmatter item 缺失：{canonical}")
    if require_marker and canonical not in candidate["marker_blocks"]:
        structural.append(f"marker block 缺失：{canonical}")
    if structural:
        _frontmatter_error(
            f"file={path} rendered candidate 关系自检失败", structural[0], "拒绝写入并修正渲染逻辑",
        )
    return rendered


def cmd_next_id(args):
    _render_next_id(_next_id_snapshot(args))


def _next_id_snapshot(args):
    root = repo_root(args.root)
    conflicts = id_conflicts(root)
    try:
        value = next_id(root, args.prefix)
        error = None
    except ValueError as exc:
        value = None
        error = exc
    return conflicts, value, error


def _render_next_id(snapshot):
    conflicts, value, error = snapshot
    if conflicts:
        print(
            f"WARNING: 检测到跨路径 ID 冲突（新 openspec/issues/todolist/ 与旧 openspec/todolists/ "
            f"都存在）：{', '.join(conflicts)}——建议尽快把旧路径数据迁移到新路径",
            file=sys.stderr,
        )
    if error is not None:
        raise error
    print(value)


# ── add ──────────────────────────────────────────────────────────────────────

def cmd_add(args):
    root = repo_root(args.root)
    data = _load_json(args.json)
    for req in ("module", "summary", "type"):
        if not data.get(req):
            _die(f"缺少必填字段：{req}")
    if data["type"] not in TYPE_TAGS:
        _die(f"类型非法：{data['type']}（应为 {'/'.join(TYPE_TAGS)}）")
    status = data.get("status", "OPEN")
    if status not in STATUS_CODES:
        _die(f"状态码非法：{status}")

    month = this_month(args.month)
    validate_prefix(args.prefix)
    snapshot = read_repository_snapshot(root)
    semantic = repository_semantic_occurrences(root, snapshot)
    explicit_id = data.get("id") is not None
    tid = canonical_id(data["id"]) if explicit_id else next_id(root, args.prefix, semantic)
    # OV-3 守卫（镜像 buglist.py）：显式传 id 时才校验（next_id 自动生成的号必然合法、必然
    # 不重，不需要重复查）。语法用单字母前缀 `[A-Z]\d+` 全量 fullmatch，不借用带 `\b` 的 ID_RE。
    # 必须是单字母前缀（不是 `[A-Z]+\d+`）：代码库对 ID 的识别全部只认单字母——
    # `_ids_in_files` 的 `\| *([A-Z]\d+) *\|`、`ID_RE = \b([A-Z])(\d+)\b`、block_ranges 均如此，
    # 若语法校验放行多字母前缀（如 "TT12"），all_ids() 根本认不出它，查重形同虚设
    # （两次 add 同一个 "TT12" 都会静默通过），且它会破坏 block_ranges 的正则匹配。
    # 先判 isinstance(str)：id 若是 JSON 数字等非字符串，直接 fullmatch 会抛裸 TypeError，
    # 破坏 _die 的 ERROR: 契约，须在此优雅拒绝。
    # 查重用 all_ids(root)：此刻新文件/新行还未落盘（ensure_file 在下面），all_ids 看到的是
    # 落盘前的既有全集，不会把本次正在 add 的 id 算进去，语义正确。
    if explicit_id and semantic_id_key(tid) in semantic:
        places = semantic[semantic_id_key(tid)]
        _die(f"显式 id 与仓级既有 semantic ID 重复：{tid} at {places}")
    time_str = args.time or datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    change = data.get("change") or detect_change(root)

    _reject_line_unsafe(data.get("title"), "title")
    _reject_line_unsafe(data.get("project"), "project")

    explicit_docs = normalize_doc_paths(data.get("doc"))
    docs = explicit_docs
    if not docs:
        docs = auto_default_doc(root, change)  # 显式 doc 优先；仅在为空时才尝试自动关联
    validate_doc_paths(root, docs)

    path = ensure_file(root, month, data.get("project"))
    block = _build_block(tid, data, status, docs, explicit_docs)
    item = {
        "module": data["module"], "summary": data["summary"], "type": data["type"],
        "status": status, "time": time_str, "change": change or None,
        "batch": data.get("batch") or None,
    }
    if os.path.exists(path):
        document = next(document for pool, candidate, _rel, document in snapshot
                        if pool == "todo" and os.path.realpath(candidate) == os.path.realpath(path))
        _reject_document_mutation(document, path)
        model = dict(document["model"] or {
            "schema": 1, "pool": "todo", "mode": "overlay", "items": {},
        })
        model["items"] = dict(model["items"])
        model["items"][tid] = item
        body = document["body"] + block.encode("utf-8").replace(b"\n", document["eol"])
        rendered = _render_recorder_document(document, model, body)
    else:
        project = data.get("project") or "<未注明>"
        body = HEADER_TMPL.format(month=month, project=project).encode("utf-8")
        if block:
            body += block.encode("utf-8")
        model = {"schema": 1, "pool": "todo", "mode": "canonical", "items": {tid: item}}
        rendered = _canonical_document(model, body)
    rendered = _validated_rendered_mutation(rendered, "todo", tid, bool(block), path)
    atomic_write_bytes(path, rendered)
    print(json.dumps({"id": tid, "file": os.path.relpath(path, root), "status": status,
                      "block": bool(block), "time": time_str, "change": change or None},
                     ensure_ascii=False))


def _build_block(tid, data, status, docs=None, explicit_docs=None):
    """是否建块 只看：motivation/approach/note 任一非空，或调用方显式传了 doc
    （explicit_docs 非空）。auto-default 探测到的 doc（docs 里有、explicit_docs 里没有）不参与这个
    判断——它只在块因为其它理由已经要建时，用来丰富该块的『关联文档』行；如果块本不该建，
    auto-default 的结果在这里被静默丢弃，条目仍保持轻量（只记一行）。"""
    docs = docs or []
    explicit_docs = explicit_docs or []
    parts = {k: data.get(k, "").strip() for k in ("motivation", "approach", "note")}
    if not any(parts.values()) and not explicit_docs:
        return ""  # 简单项：不建块（auto-default 的 doc 不单独触发建块）
    title = _display_title(data["summary"], data.get("title"))
    b = f"\n<!-- sdflow-issue-block:start id={tid} -->\n## {tid}: {title}\n"
    b += _summary_blockquote(data["summary"]) + "\n"
    if docs:
        b += "\n**关联文档**：" + "、".join(f"`{d}`" for d in docs) + "\n"
    if parts["motivation"]:
        b += f"\n**动机**：{_escape_user_markers(parts['motivation'])}\n"
    if parts["approach"]:
        b += f"\n**思路**：{_escape_user_markers(parts['approach'])}\n"
    if parts["note"]:
        b += f"\n**备注**：{_escape_user_markers(parts['note'])}\n"
    return b + f"<!-- sdflow-issue-block:end id={tid} -->\n"


# ── set-status ───────────────────────────────────────────────────────────────

def cmd_set_status(args):
    root = repo_root(args.root)
    new = args.to
    if new not in STATUS_CODES:
        _die(f"状态码非法：{new}")

    _reject_line_unsafe(args.evidence, "evidence")
    _reject_line_unsafe(args.reason, "reason")
    _reject_line_unsafe(args.month, "month")

    path, document, raw_id, item = _find_item_document(root, args.id, "todo")
    _preflight_target_legacy_block(document, raw_id, path)
    _reject_document_mutation(document, path)
    canonical = _canonical_from_key(_legacy_semantic_id_key(raw_id))

    # 门禁
    if new == "DONE" and not args.evidence:
        _die("置为 DONE 必须提供 --evidence（关联的 change 名或 commit hash）")
    if new == "WONTDO" and not args.reason:
        _die("置为 WONTDO 必须提供 --reason（放弃的理由）")

    old = item["status"]
    note = args.evidence or args.reason or ""
    hist = f"> {this_month(args.month)} 状态：{old} → {new}" + (f"（{note}）" if note else "")
    eol = document["eol"]
    history = hist.encode("utf-8") + eol
    item["status"] = new
    model = dict(document["model"] or {
        "schema": 1, "pool": "todo", "mode": "overlay", "items": {},
    })
    model["items"] = dict(model["items"])
    model["items"][canonical] = item
    insertions = {}
    frontmatter_owned = bool(document["model"] and canonical in document["model"]["items"])
    if not frontmatter_owned:
        insertions = _promotion_insertions(
            document, raw_id, canonical, path, item, (history,), False,
        )
    elif canonical in document["marker_blocks"]:
        _b_start, b_end = document["marker_blocks"][canonical]
        insertions = {b_end - 1: (history,)}
    else:
        minimal = (
            eol + f"<!-- sdflow-issue-block:start id={canonical} -->".encode("ascii") + eol
            + f"## {canonical}: {_display_title(item['summary'])}".encode("utf-8") + eol
            + _summary_blockquote(item["summary"]).encode("utf-8") + eol
            + history
            + f"<!-- sdflow-issue-block:end id={canonical} -->".encode("ascii") + eol
        )
        insertions = {len(document["lines"]): (minimal,)}
    body = _splice_body_lines(document, insertions)
    rendered = _render_recorder_document(document, model, body)
    atomic_write_bytes(path, _validated_rendered_mutation(
        rendered, "todo", canonical, True, path,
    ))
    print(json.dumps({"id": canonical, "old": old, "new": new,
                      "file": os.path.relpath(path, root)}, ensure_ascii=False))


def _minimal_block(tid, cells, status, hist):
    title = cells[2]
    return (f"\n---\n\n## {tid}: {title}\n\n"
            f"| 属性 | 值 |\n|------|------|\n"
            f"| 模块 | {cells[1]} |\n| 类型 | {cells[3]} |\n| 状态 | {status} |\n\n{hist}")


# ── triage ───────────────────────────────────────────────────────────────────

def cmd_triage(args):
    """给指定 item 赋批次 + 把状态从『未分诊开放态』推进到 PROPOSED（幂等，D7）。
    镜像 buglist.py 的 cmd_triage；差异只在 todolist 自己的 STATUS_CODES（终态 DONE/WONTDO）。

    定位 item：复用 set-status 的查找逻辑（遍历 list_files 找含该 ID 的表行）。
    状态处理（推导自 STATUS_CODES，不硬编码字面集合，镜像 cmd_scan 的 nonterminal 推导）：
      - 未分诊开放态 = STATUS_CODES 减 {PROPOSED} 减终态{DONE, WONTDO} → 即 {OPEN} → 置 PROPOSED。
      - 已是 PROPOSED → 不改状态（no-op，幂等）。
      - 已是终态（DONE/WONTDO）→ 不改状态（不把终态倒回 PROPOSED）。
    批次列（表行末列，第 8 列 / cells[7]）无条件写入，与 status 是否变化无关；
    旧格式行（无批次列）先补齐到 8 列再写，不越界。不报错（除 ID 未找到，沿用 set-status 的门禁）。
    块可选：状态若变化且块存在则同步块的『状态』行；块不存在不强制建块（triage 不写批次/历史进块）。
    """
    root = repo_root(args.root)
    batch = getattr(args, "批次")

    path, document, raw_id, item = _find_item_document(root, args.id, "todo")
    _preflight_target_legacy_block(document, raw_id, path)
    _reject_document_mutation(document, path)
    canonical = _canonical_from_key(_legacy_semantic_id_key(raw_id))
    old_status = item["status"]
    open_untriaged = set(STATUS_CODES) - {"DONE", "WONTDO", "PROPOSED"}
    new_status = "PROPOSED" if old_status in open_untriaged else old_status
    item["status"] = new_status
    item["batch"] = batch or None
    model = dict(document["model"] or {
        "schema": 1, "pool": "todo", "mode": "overlay", "items": {},
    })
    model["items"] = dict(model["items"])
    model["items"][canonical] = item
    eol = document["eol"]
    history = ()
    if new_status != old_status:
        history = (
            f"> {this_month()} 状态：{old_status} → {new_status}".encode("utf-8") + eol,
        )
    frontmatter_owned = bool(document["model"] and canonical in document["model"]["items"])
    if not frontmatter_owned:
        insertions = _promotion_insertions(
            document, raw_id, canonical, path, item, history, False,
        )
    elif canonical in document["marker_blocks"]:
        _b_start, b_end = document["marker_blocks"][canonical]
        insertions = {b_end - 1: history} if history else {}
    elif history:
        minimal = (
            eol + f"<!-- sdflow-issue-block:start id={canonical} -->".encode("ascii") + eol
            + f"## {canonical}: {_display_title(item['summary'])}".encode("utf-8") + eol
            + _summary_blockquote(item["summary"]).encode("utf-8") + eol
            + b"".join(history)
            + f"<!-- sdflow-issue-block:end id={canonical} -->".encode("ascii") + eol
        )
        insertions = {len(document["lines"]): (minimal,)}
    else:
        insertions = {}
    body = _splice_body_lines(document, insertions)
    rendered = _render_recorder_document(document, model, body)
    require_marker = not frontmatter_owned or canonical in document["marker_blocks"] or bool(history)
    atomic_write_bytes(path, _validated_rendered_mutation(
        rendered, "todo", canonical, require_marker, path,
    ))
    print(json.dumps({"id": canonical, "old_status": old_status, "new_status": new_status,
                      "batch": batch, "file": os.path.relpath(path, root)}, ensure_ascii=False))


# ── scan ─────────────────────────────────────────────────────────────────────

def _scan_snapshot(args):
    root = repo_root(args.root)
    items, problems = [], []
    # [impl-review-fix] FIX-2（CV-1+A-F2 双镜 PoC，镜像 buglist.py）：重复 ID 检测必须是
    # 全池（跨全部 dated 文件）唯一性检查——T-ID 语义上应全局唯一，不只是"单文件内不重复"。
    # 此前 Counter 在下面循环体内逐文件重建，只测得出单文件内重复，漏检跨文件同 ID
    # （例如 2026-01-todolist.md 与 2026-02-todolist.md 都出现 T1）。改为收集
    # `(id, 所在文件)` 全量列表、循环结束后统一在全池维度计数。
    raw_id_locations = []  # [(semantic_key, raw_id, rel_path), ...]
    snapshot = read_repository_snapshot(root)
    repository_semantic_occurrences(root, snapshot)
    for pool, path, rel, document in snapshot:
        if pool != "todo":
            continue
        problems.extend(f"{rel}: {problem}" for problem in document["problems"])
        for bid, item in document["effective_items"].items():
            items.append({"id": bid, **item, "file": rel})
        raw_id_locations.extend(
            (semantic_key, raw_id, rel)
            for semantic_key, raw_id in document["effective_occurrences"]
        )

    # [impl-review-fix] FIX-2：全池维度统一计数重复 ID（覆盖同文件内重复 + 跨文件重复）。
    dup_locations = {}
    for semantic_key, raw_id, rel in raw_id_locations:
        dup_locations.setdefault(semantic_key, []).append((raw_id, rel))
    duplicates = {key: locations for key, locations in dup_locations.items() if len(locations) > 1}
    if duplicates:
        key, locations = sorted(duplicates.items(), key=lambda entry: str(entry[0]))[0]
        rendered = ", ".join(f"{raw_id}@{rel}" for raw_id, rel in locations)
        _frontmatter_error("semantic ID 重复", f"key={key} locations={rendered}")

    if args.status:
        items = [b for b in items if b["status"] == args.status]
    if args.type:
        items = [b for b in items if b["type"] == args.type]
    if args.change:
        items = [b for b in items if b["change"] == args.change]
    if getattr(args, "批次", None):
        items = [b for b in items if b.get("batch") == getattr(args, "批次")]
    if args.open_ungrouped:
        # todolist 的非终态集与 buglist 不同：STATUS_CODES 只有 OPEN/PROPOSED/DONE/WONTDO，
        # 终态是 DONE/WONTDO，不能硬套 buglist 的 5 值非终态集。
        nonterminal = set(STATUS_CODES) - {"DONE", "WONTDO"}
        items = [b for b in items if b["status"] in nonterminal and not b.get("batch")]
    return {"items": tuple(items), "problems": tuple(problems)}


def _render_scan(snapshot, args):
    items = snapshot["items"]
    problems = snapshot["problems"]
    if args.json:
        print(json.dumps({"items": list(items), "problems": list(problems)}, ensure_ascii=False, indent=2))
        return
    if not items:
        print("（无匹配 TODO）")
    for b in sorted(items, key=lambda x: (x["status"], x["id"])):
        print(f"{b['id']:<5} {b['status']:<10} {b['type']:<8} {b['module']:<24} {b['summary']}")
    if problems:
        print("\n⚠️ 一致性问题：")
        for p in problems:
            print("  - " + p)
    else:
        print("\n✓ 表↔块一致")


def cmd_scan(args):
    _render_scan(_scan_snapshot(args), args)


# ── 工具 ─────────────────────────────────────────────────────────────────────

def _load_json(src):
    if src in (None, "-"):
        return json.load(sys.stdin)
    with open(src, encoding="utf-8") as f:
        return json.load(f)


def _die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def main():
    p = argparse.ArgumentParser(description="自动记录/回写/扫描 todolist")
    p.add_argument("--root", default=".", help="仓库根（默认自动探测 git 根）")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("next-id", help="打印两池 snapshot 的下一个全局 ID（advisory，不预留）")
    s.add_argument("--prefix", default=DEFAULT_PREFIX)
    s.set_defaults(func=cmd_next_id)

    s = sub.add_parser("add", help="新增 TODO（JSON 输入，stdin 或 --json 文件）")
    s.add_argument("--json", help="JSON 文件路径；缺省读 stdin")
    s.add_argument("--prefix", default=DEFAULT_PREFIX)
    s.add_argument("--month", help="覆盖月份 YYYY-MM（默认本月）")
    s.add_argument("--time", help="覆盖记录时间 YYYY-MM-DD HH:MM（默认当前时刻）")
    s.set_defaults(func=cmd_add)

    s = sub.add_parser("set-status", help="更新 frontmatter 状态（门禁 + marker 历史留痕）")
    s.add_argument("--id", required=True)
    s.add_argument("--to", required=True, help="目标状态码")
    s.add_argument("--evidence", help="change 名 / commit hash（DONE 必填）")
    s.add_argument("--reason", help="WONTDO 理由（WONTDO 必填）")
    s.add_argument("--month", help="覆盖月份")
    s.set_defaults(func=cmd_set_status)

    s = sub.add_parser("triage", help="赋批次 + 未分诊开放态→PROPOSED（幂等，D7）")
    s.add_argument("--id", required=True)
    s.add_argument("--批次", dest="批次", required=True, help="批次名（清理 change 名）")
    s.set_defaults(func=cmd_triage)

    s = sub.add_parser("scan", help="列出 TODO + dual-reader/marker 一致性自检")
    s.add_argument("--status", help="按状态码过滤")
    s.add_argument("--type", help="按类型过滤")
    s.add_argument("--change", help="按关联 change（来源）过滤")
    s.add_argument("--批次", dest="批次", help="按批次过滤")
    s.add_argument("--open-ungrouped", dest="open_ungrouped", action="store_true",
                    help="非终态（STATUS_CODES 减 DONE/WONTDO）且未分批的 TODO")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_scan)

    args = p.parse_args()
    try:
        if hasattr(args, "prefix"):
            validate_prefix(args.prefix)
        args.root = repo_root(args.root)
        if args.cmd in {"scan", "next-id"}:
            with recorder_lock(args.root, args.cmd):
                snapshot = _scan_snapshot(args) if args.cmd == "scan" else _next_id_snapshot(args)
            if args.cmd == "scan":
                _render_scan(snapshot, args)
            else:
                _render_next_id(snapshot)
        else:
            output = io.StringIO()
            with recorder_lock(args.root, args.cmd), redirect_stdout(output):
                args.func(args)
            sys.stdout.write(output.getvalue())
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
