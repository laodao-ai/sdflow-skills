#!/usr/bin/env python3
"""issues.py — 共享 issues 层脚本：跨 bug+todo 两池（Task 8：read + D9 冲突检测；
Task 9：reindex → issues/INDEX.md）。

背景（design.md §五 grill-amendment B-Q2）：`buglist.py`（sdflow-buglist）与
`todolist.py`（sdflow-todolist）是两个独立 skill 的独立脚本，各管自己一类
（add/scan/set-status/triage）。但 `reindex`/`batch` 是**跨 bug+todo**（join 两池 +
维护 `issues/INDEX.md`/`issues/batches.md`）——这类跨类型命令归本脚本独占，不塞进
per-type 脚本。

本文件现状：
  - `read_pool(root)`（Task 8）：子进程调 buglist.py/todolist.py 的 `scan --json`，
    join 成一份跨两池的 item 列表（每项打 `pool` 标记），join 后立即用
    `cross_pool_id_conflicts` 做 D9 防护网校验。
  - `cross_pool_id_conflicts(items)`（Task 8）：纯函数，检测同一 ID 是否跨池撞号。
  - `reindex`（Task 9 + Task 11）：`read_pool` → `generate_index_md` 纯函数重建
    `issues/INDEX.md`（首行 GENERATED banner + open item×批次物化板 + 已闭合摘要）
    → `atomic_write` 原子落盘。**禁读旧 INDEX**（D3，全量确定性重建）、**幂等**（D7）。
    随后 `sync_batches_md`（Task 11）拿同一份 item 池校验/回写 `issues/batches.md`
    的 `成员:`/`状态:` 两条生成行：D1 完成判据（成员数≥1 且全进各自 pool 终态集才
    判 DONE，0 成员显式排除、防 vacuous-truth 假 DONE）、Q3 不越权纠正（人标 DONE
    但成员未全终态 → 只追加 `⚠️ 不一致` 警告，不改人写的 `状态:` 值）、Q2 orphan
    报警（item 批次 tag 在 batches.md 无对应 key → stderr 报警，不新建 ghost 条目）。
  - `batch`（Task 10）：`issues/batches.md` 注册表 + `add`/`set-status`/`rename`
    三个子命令（Q2 grill-amendment）。`batches.md` 是**半手维护**注册表（Q3 字段级
    grammar）——`状态:`/`成员:` 是生成行（reindex/`batch set-status` 维护），
    `优先级:`/`计划:` 及其它是人写行，**解析/写入绝不覆写人写行**，只精确 patch
    目标生成行。`成员:` 行的内容同步（拿 item 池当 ground truth 填充）由 reindex 负责。
    `rename` 直接构造两池一次性 bytes snapshot，registry-first 写 `重命名自:` provenance，
    再以 canonical/overlay frontmatter retag；legacy table 永久只读。updated snapshot 直接
    传给 reindex，整个 rename 不调用 recorder `scan --json`、不重复读取 dated files。
  - `atomic_write`：与 buglist.py/todolist.py 同款原子写 helper，供落盘
    `issues/INDEX.md`/`issues/batches.md`/dated 文件（rename 同步）用。

**并发边界**：所有权威读写使用 `openspec/issues/.recorder.lock` 的 repository-wide
exclusive snapshot lock。顶层命令是 owner，复合命令仅向同 repo allowlist recorder
子进程转发高熵 token；participant 校验后加入同一锁域而不重复 acquire/release。锁是
cooperative protocol，不阻止编辑器、Git 或绕协议脚本；network/userspace FS 不受支持，
process-crash 后遗留锁必须按错误给出的精确路径人工 break-glass，禁止 TTL 自动偷锁。

用法见 `python issues.py --help`。
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
import tempfile
import time


# ── 兄弟脚本定位 ─────────────────────────────────────────────────────────────
# 按本脚本自身的文件位置（不是 --root / 目标项目根）定位 buglist.py/todolist.py：
# setup.sh 把仓库里的每个顶层 skill 目录（sdflow-buglist / sdflow-todolist /
# sdflow-issues ...）各自绝对 symlink 到 ~/.claude/skills/、~/.codex/skills/ 下，
# 三者在安装后仍是同级 sibling 目录，因此“sdflow-issues/scripts 的上两级”这个
# 相对关系在源码仓库和安装后的位置都成立。--root 是完全独立的另一个概念：它是
# *目标项目*（存 openspec/issues/... 的仓库）的根，两者不可混淆、不可互相替代。
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
BUGLIST_SCRIPT = os.path.join(SKILLS_ROOT, "sdflow-buglist", "scripts", "buglist.py")
TODOLIST_SCRIPT = os.path.join(SKILLS_ROOT, "sdflow-todolist", "scripts", "todolist.py")

CANONICAL_ID_RE = re.compile(r"^[A-Z][1-9][0-9]*$", re.ASCII)
UTF8_BOM = b"\xef\xbb\xbf"
RECORDER_POOL_CONFIG = {
    "bug": ("priority", {"P0", "P1", "P2", "P3", "P4"},
            {"OPEN", "VERIFIED", "PROPOSED", "IN_PROGRESS", "FIXED", "WONTFIX", "BLOCKED"}),
    "todo": ("type", {"性能优化", "可观测性", "代码质量", "功能增强", "基础设施"},
             {"OPEN", "PROPOSED", "DONE", "WONTDO"}),
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


def split_sections(lines):
    """返回 (head_end_idx, table_rows_range, body_start_idx)。
    head_end = 状态总览表分隔行后的位置；表行在 [rows_start, rows_end)。"""
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
    """返回 {id: (start, end)}，块从 '## {id}:' 到下一个 '---'/'## ' 或 EOF。"""
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
        "bug": ("openspec/issues/buglist/*.md", "openspec/buglists/*.md"),
        "todo": ("openspec/issues/todolist/*.md", "openspec/todolists/*.md"),
    }
    documents = []
    items = []
    problems = []
    semantic_occurrences = {}
    seen_paths = set()
    for pool, patterns in pools.items():
        for pattern in patterns:
            for path in sorted(glob.glob(os.path.join(root, pattern))):
                real = os.path.realpath(path)
                if real in seen_paths:
                    continue
                seen_paths.add(real)
                rel = os.path.relpath(path, root)
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


def _body_with_legacy_bug_markers(document, targets):
    """Wrap promoted legacy bug blocks without rewriting their bytes."""
    insertions = {}
    line_offsets = [0]
    for line in document["lines"]:
        line_offsets.append(line_offsets[-1] + len(line.encode("utf-8")))
    ranges = []
    for raw_id, canonical in targets:
        start, end = _legacy_block_range(document, raw_id)
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


def _legacy_block_range(document, raw_id):
    """Resolve exactly one semantic legacy block and reject marker collisions."""
    semantic_key = _legacy_semantic_id_key(raw_id)
    starts = []
    for index, line in enumerate(document["lines"]):
        match = re.match(r"##\s+([A-Z][0-9]+)\s*:", line, re.ASCII)
        if match and _legacy_semantic_id_key(match.group(1)) == semantic_key:
            starts.append(index)
    if len(starts) != 1:
        raise ValueError(
            f"ERROR: file={document['path']} legacy block 无法安全包裹; "
            f"cause: id={raw_id} candidates={len(starts)}; "
            "fix: repair to exactly one legacy block, then rerun the original batch rename command"
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
            raise ValueError(
                f"ERROR: file={document['path']} legacy marker collision; "
                f"cause: id={raw_id} line={index + 1}; "
                "fix: remove or escape the preexisting marker, then rerun the original batch rename command"
            )
    return start, end


def _reject_target_document_problems(document, target_ids):
    """Fail closed on target marker/ownership relations before any registry write."""
    if document["pool"] == "bug":
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
                _legacy_block_range(document, raw_id)
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
                # A row with more than eight cells is only demonstrably a
                # harmless trailing-cell extension when the canonical first
                # eight positions independently validate.  If enum/status are
                # shifted (the characteristic middle-cell insertion), the
                # apparent batch cell is not trustworthy even when neither
                # rename key appears literally anywhere in the row.
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
    if document["pool"] == "bug":
        for item_id in model["items"]:
            if item_id not in marker_blocks:
                structural.append(f"frontmatter item lacks marker block: {item_id}")
    for item_id in marker_blocks:
        if item_id not in model["items"]:
            structural.append(f"marker block lacks frontmatter item: {item_id}")
    for canonical in canonical_ids:
        if canonical not in model["items"]:
            structural.append(f"frontmatter item missing: {canonical}")
        if document["pool"] == "bug" and canonical not in marker_blocks:
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
            if document["pool"] == "bug" and key not in frontmatter_keys:
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


def atomic_write(path, text):
    """原子写：同目录临时文件写完整内容 → os.replace 原子换入。
    中途任何异常（含 os.replace 本身失败）都不会截断/损坏原文件——旧内容原样保留，
    临时文件在 finally 里清理，不留残留 .tmp。

    tempfile.mkstemp 固定以 0600 创建临时文件；os.replace 是纯 rename，目标会
    继承临时文件的权限。覆写已存在文件前必须把临时文件权限对齐回原文件的权限，
    否则已存在文件的权限会被静默从（例如）0644 收紧到 0600（对 group/other 变
    不可读）。原文件不存在（首次创建）时用 0o644 兜底。

    与 buglist.py / todolist.py 的同名函数逐字同款（Phase B 3 个脚本各自独立、
    不互相 import，故各自内联一份，见模块 docstring "子进程解耦"）。"""
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


# ── 路径与文件 ───────────────────────────────────────────────────────────────

def repo_root(start="."):
    """探测 git 仓库根；非 git 仓库（或 git 命令失败）退化为 `os.path.abspath(start)`。

    与 buglist.py / todolist.py 的同名函数逐字同款（Phase B 3 个脚本各自独立、不互相
    import，故各自内联一份，见模块 docstring "子进程解耦"）。修复 Critical fix carry-over：
    本脚本此前 4 个 cmd_* 直接用裸 `args.root`（默认 "."）拼路径，不像 buglist.py/todolist.py
    那样探测 git 根——从非仓库根的子目录调用时会把 `openspec/issues/...` 错误地写到 cwd 而非
    git 根，三脚本定位从此不一致。所有 cmd_* 现在统一先 `root = repo_root(args.root)` 再拼
    路径；`read_pool` 调 buglist.py/todolist.py 子进程时也把这个已 resolve 的 root 传下去
    （`--root`），保证跨三脚本落到同一个目录。"""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start, capture_output=True, text=True, check=True,
            env=recorder_child_env("git", token=False),
        )
        return out.stdout.strip()
    except Exception:
        return os.path.abspath(start)


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
    items_key = "bugs" if pool == "bug" else "items"
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
        if item[specific_field] not in specific_values:
            raise ValueError(f"ERROR: scan item[{index}].{specific_field} 枚举漂移; cause: {item[specific_field]!r}; fix: repair/reinstall the recorder producer and retry")
        if item["status"] not in status_values:
            raise ValueError(f"ERROR: scan item[{index}].status 枚举漂移; cause: {item['status']!r}; fix: repair/reinstall the recorder producer and retry")
    return data[items_key], data["problems"]


# ── 跨池 read ────────────────────────────────────────────────────────────────

def _scan_pool(script, root, pool, problems_out=None):
    """子进程调 `{script} --root {root} scan --json`，给每项打 `pool` 标记后返回列表。

    推荐子进程而非 import（brief 明确要求）：buglist.py / todolist.py 是两个独立 skill
    各自的执行核心，子进程调用只依赖它们的 CLI 契约（`scan --json` 的输出结构），不依赖
    其内部函数签名——两边各自演进互不牵连，也不会把共享层的 issues.py 变成两个 per-type
    脚本的隐式反向依赖源。

    `problems_out`（Task 5，T1）：可选的列表，非 None 时把子进程 `scan --json` 输出里的
    `problems`（表↔块不一致 / 重复 ID / OV-1 行 arity 异常等，per-type 脚本自己的一致性
    自检结果）原样 extend 进去。此前这里直接丢弃 `data["problems"]`——per-type 脚本测出的
    一致性问题永远到不了调用 `read_pool` 的 reindex，属静默蒸发。默认 `None`（不收集，
    行为与改动前一致）——只有显式传入列表的调用方（`cmd_reindex`）才会拿到这份信号，不
    改变 `read_pool`/`_scan_pool` 对既有调用方（如 `cmd_batch_rename`）的返回值形状。
    """
    kwargs = {"capture_output": True, "text": True}
    if _ACTIVE_RECORDER_TOKEN:
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
    # buglist.py 输出键是 "bugs"，todolist.py 输出键是 "items"（两脚本各自的命名，
    # 不统一——brief 明确提醒过这个坑，这里按 pool 分别取对应键）。
    out = []
    for item in raw_items:
        merged = dict(item)
        merged["pool"] = pool
        out.append(merged)
    return out


def cross_pool_id_conflicts(items):
    """检测 `items`（含 `id`/`pool` 字段的 dict 列表）里同一 ID 是否跨池撞号
    （即同时出现在 pool == 'bug' 和 pool == 'todo' 的项里）。

    正常情况下 B(bug)/T(todo) 前缀互斥、不会天然撞号——D9 已把这条前缀互斥升为显式规范
    条款（recorder 约定段）。本函数是那条规范的**防护网**：万一有人为/历史数据用了非标准
    前缀（例如显式传自定义 `id` 绕开默认前缀），撞号也不能被静默 join 掉。

    纯函数、只读，不修改入参；返回按字典序排序的冲突 ID 列表，无冲突返回 `[]`。
    """
    bug_ids = {it["id"] for it in items if it.get("pool") == "bug"}
    todo_ids = {it["id"] for it in items if it.get("pool") == "todo"}
    return sorted(bug_ids & todo_ids)


def read_pool(root, problems_out=None):
    """读跨两池（bug + todo）的 item 列表，join 结果里每项都带 `pool`（'bug' | 'todo'）
    标记，且至少含 `id`/`status`/`change`/`batch`/`pool` 五个字段（bug 池额外带
    priority/module/... 等 buglist 专属字段，todo 池额外带 type/module/... 等 todolist
    专属字段——字段是两边的并集，不做裁剪）。

    子进程调用 `buglist.py scan --json` + `todolist.py scan --json`（见 `_scan_pool`），
    两个结果 join 后立即跑 `cross_pool_id_conflicts` 做 D9 防护网校验：一旦检测到同一 ID
    跨池撞号，直接抛 `CrossPoolIDConflict`、**不静默 join**——调用方（reindex/batch，
    Task 9-11）不应该在数据已经撞号的情况下继续往下算 INDEX/batches。

    `problems_out`（Task 5，T1）：可选列表，非 None 时收集两池 `scan --json` 各自的
    `problems`（透传见 `_scan_pool`）。默认 `None`，返回值形状与改动前完全一致——
    `cmd_batch_rename` 等既有调用方无需改动。

    调用方必须已经是 recorder lock owner/participant；两个 scan 子进程校验同一 token，
    因而 join 对应同一个没有外部合规 writer 穿越的 repository snapshot。
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


# ── reindex → issues/INDEX.md（Task 9） ─────────────────────────────────────
# 批次状态同步（`issues/batches.md` 的 `成员:`/`状态:` 生成行）见本文件靠后的
# 「reindex → batches.md 状态同步（Task 11）」一节；`issues/batches.md` 注册表
# 本身（`batch add`/`set-status`/`rename`）见 Task 10。本节只做「从 dated 文件
# 重建 INDEX.md」这一半。

INDEX_BANNER = "<!-- GENERATED by issues.py reindex — DO NOT EDIT -->"

# 各 recorder 的终态集（design.md §4.1 B-Q1）：进入即"这条债不再挂着"。
# per-recorder 判定，不写死字面 "DONE"（对 bug 池不成立）——两池状态词表不同。
TERMINAL_STATUSES = {
    "bug": {"FIXED", "WONTFIX"},
    "todo": {"DONE", "WONTDO"},
}


def _is_terminal(item):
    """item 是否已进入其所属 pool 的终态集（FIXED/WONTFIX 之于 bug，DONE/WONTDO 之于 todo）。"""
    return item.get("status") in TERMINAL_STATUSES.get(item.get("pool"), set())


def _render_item_table(items):
    """把一组 item 渲染成 markdown 表（ID | Pool | Status | 关联Change），按 id 升序。
    纯函数、确定性排序——供 generate_index_md 幂等（D7）用。"""
    lines = [
        "| ID | Pool | Status | 关联Change |",
        "|----|------|--------|------------|",
    ]
    for it in sorted(items, key=lambda x: x["id"]):
        change = it.get("change") or "-"
        lines.append(f"| {it['id']} | {it['pool']} | {it['status']} | {change} |")
    return "\n".join(lines)


def generate_index_md(items):
    """从 `read_pool` 返回的跨池 item 列表纯函数式生成 `issues/INDEX.md` 全文（含首行
    banner）。**禁读旧 INDEX**（D3）——只以 `items` 为唯一输入源，不看磁盘上已有内容。

    正文 = open item（非终态）× 批次的物化板：
      - 有批次的 open 项按批次分组（批次名升序），组内按 id 升序；
      - 批次为空的 open 项单列一组「未分组」，排在所有具名批次之后；
      - 已闭合（终态）项不逐条列出，只计数摘要（含 pool 拆分）。

    **幂等（D7）**：不写入时间戳/随机序等致每次不同的内容；分组键、组内排序全部确定性
    （批次名字典序、item id 字典序），故相同 `items` 两次调用逐字节输出相同。
    """
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


def _die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def _reject_batch_line_unsafe(value, field):
    """`batches.md` 单行字段守卫；不是 legacy recorder table writer。

    batch registry 仍是 Markdown 单行协议，因此拒绝 ASCII pipe 与换行；dated recorder
    frontmatter writer 不调用本 helper。"""
    if value is None:
        return
    if "|" in str(value) or "\n" in str(value) or "\r" in str(value):
        _die(f"字段 {field} 含非法字符（| 或换行），会破坏总览表列对齐：{value!r}")


def _reject_line_unsafe(value, field):
    if value is None:
        return
    if any(char in str(value) for char in ("\r", "\n", "\0")):
        _frontmatter_error(
            f"字段 {field} 非法", f"CR/LF/NUL 不能写入 Markdown 单行结构：{value!r}",
            f"为 {field} 提供不含 CR/LF/NUL 的单行值后重试",
        )


def _reject_batch_key_unsafe(key):
    """batches.md header slug 守卫（OV-2）：header 行是 `### {key} — {title}`
    （`_BATCH_HEADER_RE`，em dash U+2014 前后各一空格作分隔符）。`_reject_batch_line_unsafe`
    只挡 `|`/换行——不够，因为 key 本身若含 ` — ` 分隔符，会被 `_BATCH_HEADER_RE` 的
    非贪婪匹配切坏：例如 key="a — b" 写成 header 后，解析出的 key 变成 "a"、
    title 变成 "b"，原始完整 key 从此在 batches.md 里再也匹配不到——`_find_batch_entry_range`
    找不到它，等于这条注册从写入的那一刻起就是个读不回来的僵尸条目。首尾空白同理：
    `_BATCH_HEADER_RE` 用 `\\s*$` 吃掉尾部空白，写入时 key 有尾随空格、读回解析出的
    key 却没有，两次查找同一"逻辑 key"会得到不同结果。

    MUST 用于 `cmd_batch_add` 的 `key`、`cmd_batch_rename` 的 `new_key`（写 header 的
    唯一两处入口）。

    [impl-review-fix] FIX-3（领域 F1 PoC）：空/纯空白 key 此前会绕过下面的
    `str(key) != str(key).strip()` 检查——对空字符串 `""`，`"".strip()` 仍是 `""`，
    两侧相等，检查恒为 False，空 key 被放行。放行后写出的 header 是
    `###  — title`（key 位置是空白），`_BATCH_HEADER_RE` 的 `(?P<key>.+?)` 要求至少
    一个字符，永远无法从这个 header 解析回 key——这条注册从写入的那一刻起就是个
    读不回来的僵尸条目。必须在做首尾空白比较之前，先单独拒绝空/纯空白 key。"""
    if not str(key).strip():
        _die(f"batch key 不可为空/纯空白（会写出解析不回来的僵尸 header）：{key!r}")
    _reject_batch_line_unsafe(key, "batch key")
    if " — " in str(key) or str(key) != str(key).strip():
        _die(
            "batch key 非法（含 ' — ' em dash 分隔符，或首尾有空白），会破坏 "
            f"batches.md header（`### {{key}} — {{title}}`）解析：{key!r}"
        )


def _reindex_core(root, snapshot=None):
    """reindex 核心逻辑（无 CLI 层退出码/文案语义）：`read_pool`（内含 D9 跨池 ID 冲突
    检测，冲突即抛 `CrossPoolIDConflict`；子进程失败抛 `RuntimeError`——本函数**不捕获、
    直接向上抛**，退出码/报错文案由调用方决定）→ `generate_index_md` 纯函数重建全文 →
    `atomic_write` 原子落盘 INDEX.md → `sync_batches_md`（Task 11：拿同一份 `items` 当
    ground truth 同步 batches.md 每批的 `成员:`/`状态:` 生成行）。
    **禁读旧 INDEX.md**（D3）：全量确定性重建，不与磁盘上旧内容比较/合并。

    返回 `(items, problems)`：`items` 供调用方统计 open/closed 计数，`problems` 是两池
    `scan --json` 各自的一致性自检结果（透传自 `read_pool`）。

    两个调用方：
      - `cmd_reindex`（CLI `reindex` 子命令）：捕获 `RuntimeError` 走 `_die`（exit 1），
        并按 `--strict` 决定 problems 是否收紧退出码。
      - `cmd_batch_rename`：传入 direct updated snapshot；INDEX/batches 任一失败均由调用方
        以 stage + 原命令恢复信息 fail-closed，直到全部派生输出收敛才允许成功。
    """
    if snapshot is None:
        problems = []
        items = read_pool(root, problems)
    else:
        items = list(snapshot["items"])
        problems = list(snapshot.get("problems", []))
    content = generate_index_md(items)
    index_path = os.path.join(root, "openspec", "issues", "INDEX.md")
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
    """把 `_reindex_core` 返回的 problems（两池 `scan --json` 透传的一致性自检结果，
    如表↔块不一致 / 重复 ID / OV-1 行 arity 异常）逐条回显到 stderr。

    [impl-review-fix] FIX-4：从 `cmd_reindex` 抽出，供 `cmd_batch_rename` 的 auto-reindex
    共用——此前 auto-reindex 只 `try: _reindex_core(root)` 丢弃返回值，reindex 成功但
    problems 非空时 rename 完全不吐这个信号（静默蒸发），必须复用同一段回显逻辑。"""
    for p in problems:
        print(p, file=sys.stderr)


def cmd_reindex(args):
    """重建 `issues/INDEX.md` + 同步 `issues/batches.md` 状态（Task 9 + Task 11 两部分）。

    核心逻辑见 `_reindex_core`；本函数只负责 CLI 层：捕获 `RuntimeError`（跨池 ID 冲突/
    子进程失败）走 `_die`（exit 1，不生成半截 INDEX、也不碰 batches.md），成功后打印摘要，
    并按 `--strict` 决定 problems 是否收紧退出码。

    T1（Task 5）：两池 `problems` 此前被 `_scan_pool` 静默丢弃——per-type 脚本测出的
    一致性问题（表↔块不一致等）永远到不了这里，reindex 看着"成功"却完全不知道底层
    数据已经腐蚀。现在 reindex 结束后把非空 `problems` 逐条回显到 stderr（**默认仍
    exit 0**——reindex 本身该做的事（重建 INDEX/同步 batches）已经做完，且这类
    "低置信度默认不阻断"的口径与本 change 别处一致；只有显式传 `--strict` 时，存在
    problems 才让本次调用以非 0 退出，供想要强门禁的调用方（如 CI）选择性收紧。
    `--strict` 目前是预置接口，本 change 内无消费者主动传它。
    """
    root = repo_root(args.root)
    try:
        items, problems = _reindex_core(root)
    except RuntimeError as e:
        _die(str(e))
        return  # pragma: no cover（_die 已 sys.exit(1)，此行只安抚静态分析）

    index_path = os.path.join(root, "openspec", "issues", "INDEX.md")
    open_n = sum(1 for it in items if not _is_terminal(it))
    closed_n = len(items) - open_n
    print(f"reindex：已重建 {index_path}（open {open_n} 项，已闭合 {closed_n} 项）")

    _echo_problems(problems)
    if getattr(args, "strict", False) and problems:
        sys.exit(1)


# ── issues/batches.md 注册表 + batch 命令（Task 10，Q2 rename / Q3 字段级 grammar） ──
#
# batches.md 每批一条，字段级 grammar（Q3 spec-review-amendment 裁决）：
#
#   ### {key} — {title}
#   状态: PLANNED            ← 生成行（reindex / `batch set-status` 维护）
#   成员: (生成) B1, T2      ← 生成行（`batch add` 建空占位；内容同步由 reindex 维护，见 Task 11）
#   优先级: P1               ← 人写行（reindex/batch 绝不覆写）
#   计划: 一句范围           ← 人写行（同上）
#
# 「生成行」= `状态:`/`成员:` 这两个固定前缀；「人写行」= 其它任意行（`优先级:`/`计划:`
# 只是本任务默认写入的两个人写字段，条目里额外追加的其它人写行同样原样保留——本节所有
# 解析/写入函数都按"整条 entry = 一段连续行"处理，只精确定位要 patch 的那一行，不touch
# 该 entry 范围内除目标行以外的任何字符。

BATCH_STATUSES = ["PLANNED", "IN_PROGRESS", "DONE"]
BATCH_PLACEHOLDER = "<待填>"  # 与 buglist.py `_has_rootcause` 的 <待分析> 同款占位符风格

# `优先级:` 人写字段的合法前导 token 集合（Task 3，mlh-p3-determ-guards）：与
# buglist.py:57 同款字面量（一致性由 test_mirror_consistency.py 的
# `test_priorities_constant_consistency` 值相等断言守，非跨 import——D4 红线禁止
# 三脚本互相 import，各自内联一份）。`batch lint` 用它校验 `优先级:` 字段前导 token。
PRIORITIES = ["P0", "P1", "P2", "P3", "P4"]

# entry 头：`### {key} — {title}`（key/title 间用 em dash " — " 分隔，字面量，非正则元字符）
_BATCH_HEADER_RE = re.compile(r"^### (?P<key>.+?) — (?P<title>.+?)\s*$")
# 冒号兼容全角 `：`（Task 10 carry-over）：人手改 batches.md 很容易在中文输入法下敲成全角
# 冒号——若只认半角，解析会判定"整条目缺 状态: 行"，进而在别处插一条新的半角状态行，
# 把原来的全角行晾成永不会再被读到的僵尸行。放宽正则兼容两种冒号后，两者都能被找到、
# 定位、精确 patch（写回时统一改写成半角，起到顺手规范化的效果），不会产生僵尸行。
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
    """batches.md 不存在时视为空注册表（`[]`），供 add 首次建文件时走同一套逻辑。

    规范化尾随换行（Critical fix）：`batches.md` 是半手维护文件，文件末尾缺尾随换行
    很常见——`readlines()` 会让最后一行不以 `\\n` 结尾。本文件下游多处对 `lines` 做
    `lines.insert(...)` 兜底插入（`_sync_one_entry` 的成员行/状态行/⚠️ 警告行缺失
    插入、`cmd_batch_set_status` 的状态行缺失插入），这些插入都假定“每一行都独立
    以 `\\n` 结尾”。若最后一行缺换行，插入的新行会在 `"".join()` 落盘时直接粘连到
    该行文本后面——不仅覆写/腐蚀人写行（违反 Q3 不覆写人写行），且粘连后的 ⚠️ 行不再
    以 `⚠️ 不一致:` 开头，`_BATCH_WARN_LINE_RE` 认不出它，导致下次 reindex 的“先剥旧
    ⚠️”识别不到、每跑一次 reindex 再插一条新 ⚠️——破幂等，数据腐蚀不自愈。

    所有下游函数（`_split_batches_entries`/`_find_batch_entry_range`/`sync_batches_md`/
    `cmd_batch_add`/`cmd_batch_set_status`/`cmd_batch_rename`）都经由本函数读取
    `batches.md`，故在此单点补齐是覆盖面最全、最不易遗漏未来新增插入点的实现：只有
    整个文件的最后一行可能缺换行（`readlines()` 对其余每一行都保证以 `\\n` 结尾），
    在此统一补上后，下游任何位置的 `lines.insert(...)` 都不会再粘连到前一行。

    [impl-review-fix] F2：`open()/readlines()` 此前无编码错误守卫——非 UTF-8
    batches.md（存在但内容损坏/编码不对）会让本函数抛出未捕获的 `UnicodeDecodeError`，
    以裸 traceback 一路冒泡到调用方（`batch lint`/`batch add`/`sync_batches_md` 等，
    均是 CLI 入口路径）。改为 `open`+`readlines` 整体包一层 try，`(OSError,
    UnicodeDecodeError)` 一律走 `_die`（干净 reason + 非零退出），不再裸崩。**不改**
    缺失文件的 `[]` 语义（上面 `os.path.exists` 分支原样保留，`cmd_batch_add` 首次建
    文件依赖它）——只加固"文件存在但读不出"这一种此前完全没守住的失败模式。
    """
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
    """在 `lines`（batches.md 全文按行切片）里定位 `key` 对应 entry 的行范围。

    返回 `(header_idx, end_idx)`：entry 占 `lines[header_idx:end_idx]`（含 header 行，
    不含下一个 entry 的 header 行/EOF）。`key` 未找到返回 `None`。

    纯定位、不修改 `lines`——所有写操作都在调用方按需精确替换/插入某一行，其余行
    （含同一 entry 内的人写行、以及其它 entry 的全部内容）原样保留在 `lines` 里。
    """
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


# ── reindex → batches.md 状态同步（Task 11） ─────────────────────────────────
# reindex 除了重建 issues/INDEX.md（Task 9），还拿 item 池当 ground truth 同步
# batches.md 每批的 `成员:`/`状态:` 两条生成行——这一节实现那一半（`sync_batches_md`，
# 被 `cmd_reindex` 调用）。

# 批次完成判据（D1）：成员数 ≥1 且全部进入各自 pool 的终态集（TERMINAL_STATUSES，
# 含 WONT* 是合法闭合）。0 成员显式被 `len(members) >= 1` 排除——对空集，"全部成员
# 都终态" 是全称量词的 vacuous truth（永真），若不显式排除会把刚建、还没人挂上去的
# 空批次误判成"已完成"，这正是 D1 要焊死的假 DONE。


def _split_batches_entries(lines):
    """把 batches.md 全文行切成 `(preamble_lines, entries)`；`entries` 是
    `[(key, entry_lines), ...]`（保持文件原有顺序），每个 `entry_lines` 含该条目的
    header 行 + 随后所有行（含尾部空行，直到下一个 entry header 或 EOF）。

    纯定位/切片，不修改 `lines`——与 `_find_batch_entry_range`（单 key 查找）同款
    定位逻辑，这里一次性切出全部条目，供 `sync_batches_md` 逐条 patch 用。
    """
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
    """纯函数：给定一个 batches.md 条目的原始行列表 + 该批当前成员 id 列表（按批次 tag
    从 item 池聚合而来）+ D1 完成判据结果，返回同步后的新行列表。

    只碰 `状态:`/`成员:` 两条生成行 + `⚠️ 不一致` 警告行，条目内其它任何人写行
    （`优先级:`/`计划:`/... 及 header 本身）原样保留、相对顺序不变（Q3 grammar）。

    - 先无条件剥掉旧的 `⚠️ 不一致` 行（若有）——下面按当前判据重新决定是否追加，
      两次调用同样输入必产生同样输出，不会累积重复警告（幂等）。
    - `成员:` 行整行重写为 `成员: (生成) id1, id2 ...`（id 升序；0 成员写
      `成员: (生成)` 不带尾巴）；缺失该行时插在 `状态:` 行之后（Task 10 的 `add`
      保证必有此行，这里只是防御式兜底，不代表预期路径）。
    - `状态:` 行：`is_complete` 为真 → 强制改写成 `DONE`——这是 reindex 唯一会写的
      值（PLANNED→IN_PROGRESS 是 `batch set-status` 的人工权限，reindex 只推
      →DONE，不碰其它值）。`is_complete` 为假时**绝不改这个值**，哪怕它当前就是
      `DONE`——那种"人标 DONE 但成员未全终态"的场景只触发下面的 ⚠️ 追加，不越权
      纠正（Q3）。
    """
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
    """reindex 第二部分（Task 11）：拿 `items`（`read_pool` 结果）当 ground truth，
    同步 `issues/batches.md` 每批的 `成员:`/`状态:` 两条生成行。

    - 按批次 tag（`items` 里的 `batch` 字段，忽略空批次）聚合成员，重写每个已注册
      条目的 `成员:` 行。
    - D1 完成判据：成员数 ≥1 且全部进入各自 pool 终态集 → `状态:` 同步为 `DONE`；
      0 成员的批次显式排除在判据外（防 vacuous-truth 假 DONE），`状态:` 原样保留
      （reindex 不写 PLANNED/IN_PROGRESS，那是 `batch set-status` 的人工权限）。
    - Q3 不越权纠正：条目当前 `状态: DONE` 但成员未全终态 → 不改 `状态:` 值，只在
      条目尾部追加 `⚠️ 不一致` 警告（幂等：下次 reindex 会先移除旧警告再按当前
      判据重新决定是否追加，不累积）。
    - Q2/D5 orphan：item 的批次 tag 在 batches.md 里没有对应已注册 key → 不新建
      该 key 的 ghost 条目，只在 stderr 显式报警（`batches.md` 完全不存在时，
      所有带批次 tag 的 item 都会被判定 orphan）。

    该函数只在 batches.md 已有至少一条注册条目时才会写回文件（没有条目可 patch
    时不创建/改动 batches.md 本身——那是 `batch add` 的职责）；orphan 检测不受
    此限制，始终执行。
    """
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


# ── batch lint（Task 3，mlh-p3-determ-guards） ──────────────────────────────
# 只读语法校验 `issues/batches.md` 每条目的 `优先级:`/`计划:` 两个人写字段（Q3
# grammar）——不解析语义（不判断该批次是否"真该是"P1 还是 P2），只守字段的语法形状：
# `优先级:` 前导 token 须 ∈ `PRIORITIES ∪ {—}`，`计划:` 非占位时须非空白。
# 复用 `_split_batches_entries`（逐条切分，Task 11 已有）——不重新解析 batches.md。

_BATCH_PRIORITY_LINE_RE = re.compile(r"^优先级[:：]\s*(.*)$")
_BATCH_PLAN_LINE_RE = re.compile(r"^计划[:：]\s*(.*)$")
# 前导 token 提取：`P` + PRIORITIES 定义域内一位数字（0-4，且后面不可再跟数字），或
# em dash（U+2014，"已闭合/无需分级"的合法记法）。只取前导 token、**匹配后剩余字符串
# 不校验**（H4 订正：`P1 ★` 裸后缀须过，不能要求括号包裹或空后缀）——是否属于 PRIORITIES
# 集合的最终判断仍在 `_lint_priority_field` 里做（单数字越界值如 P5-P9 仍会落到那里
# 被拒）。
# [impl-review-fix] F3：此前 `P\d` 只匹配一位数字就停——对 `P10`/`P40` 这类两位数，
# 正则会截断匹配出 `P1`/`P4`（合法 token），P10/P40 被误判通过（P10/P40 不是任何合法
# 优先级）。改为 `P[0-4](?!\d)`：用负向前瞻 `(?!\d)` 排除"匹配到的数字后面还紧跟着
# 数字"的情况，两位数及以上（P10/P40/P50…）一律在此处就不匹配前导 token，落入
# `_lint_priority_field` 的 `token is None` 分支被拒，不会被截断误判。
_BATCH_PRIORITY_PREFIX_RE = re.compile(r"^(P[0-4](?!\d)|—)")


def _find_batch_field_value(entry_lines, field_re):
    """在一个 batches.md 条目的原始行列表里找第一处匹配 `field_re` 的行，返回其捕获组
    （已 strip）；条目内没有该字段行时返回 `None`（区分"字段存在但为空"与"字段整行
    缺失"两种状态，供调用方各自判定是否要报违规）。"""
    for line in entry_lines:
        m = field_re.match(line.rstrip("\n"))
        if m:
            return m.group(1).strip()
    return None


def _lint_priority_field(value):
    """校验非占位 `优先级:` 值是否合法；合法返回 `None`，非法返回违规原因文案。

    豁免：`value == BATCH_PLACEHOLDER`（`<待填>`）——D5/H1，优先级与计划两字段
    同等豁免占位符，合法的"未分诊/未填"状态。调用方须在调本函数前自行判断占位符
    豁免（本函数只管非占位值的语法）。
    """
    m = _BATCH_PRIORITY_PREFIX_RE.match(value.strip())
    token = m.group(1) if m else None
    if token is None or token not in PRIORITIES + ["—"]:
        return (
            f"前导 token 须 ∈ {{{', '.join(PRIORITIES)}, —}}（匹配后剩余字符串不校验，"
            f"如 'P1 ★'/'P2（说明）' 均合法）：{value!r}"
        )
    return None


def _lint_plan_field(value):
    """校验非占位 `计划:` 值是否合法；合法返回 `None`，非法返回违规原因文案。
    豁免同 `_lint_priority_field`：`value == BATCH_PLACEHOLDER` 时调用方不应调本函数。
    """
    if not value.strip():
        return f"非占位时不可为空白：{value!r}"
    return None


def _lint_one_entry(entry_lines):
    """校验单个 batches.md 条目的 `优先级:`/`计划:` 字段，返回违规列表
    `[(field_label, value, reason), ...]`；无违规返回 `[]`。

    字段整行缺失（`_find_batch_field_value` 返回 `None`）不算违规——本命令只做
    "值存在时的语法校验"，不校验字段是否必须存在（`batch add` 保证新建条目必有
    这两行且缺省写占位符，理论上不会缺失；手改/损坏文件的缺失字段场景不在本命令
    职责范围，属另一类结构完整性检查）。
    """
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
    """`batch lint`：只读校验 `issues/batches.md` 全部条目的 `优先级:`/`计划:` 字段语法
    （Q3 grammar 的人写字段）。fail-closed：任一条目任一字段违规 → 非零退出并逐条指明
    "批次 key + 字段 + 原因 + 原始值"，不覆写/不修改 batches.md 任何字节（纯读）。
    全部通过 → exit 0 并打印校验条目数摘要。

    复用 `_split_batches_entries`（Task 11 已有的逐条切分逻辑）——不重新解析
    batches.md、不引入第二套 header/entry 定位规则。

    [impl-review-fix] F1：设计的失败模式表要求 batches.md 缺失 → 报告 + 非零退出。
    此前直接调 `_read_batches_lines`（返回 `[]`）→ `entries` 为空 → 循环 0 次跑完 →
    打印 "0 条批次全部通过"、exit 0——文件缺失被静默判成"全部通过"的假阳。`_read_batches_lines`
    的 missing→[] 语义本身不能改（`cmd_batch_add` 首次建文件依赖它），故在本命令入口单独
    显式探测文件是否存在，缺失即 `_die`（非零退出 + 明确 reason），仿 `lint_config` 报告
    config.yaml 缺失的做法。
    """
    _render_batch_lint(_batch_lint_snapshot(args))


def _batch_lint_snapshot(args):
    root = repo_root(args.root)
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
    """`batch add {key}`：新建 PLANNED 条目，成员空；人写字段按参数写，缺省留占位
    （`BATCH_PLACEHOLDER`，不是空字符串——占位和"确实填了空值"要能区分）。

    已存在同 key，默认 → 报错（非 no-op）：add 是"新建"语义，撞号多半是误操作，报错比
    静默跳过更安全——静默 no-op 会让调用方以为参数（title/优先级/计划）已生效，实际全被
    忽略，是更隐蔽的坑。

    `--if-exists skip`（Task 7，T4，opt-in）：显式传入时改为 skip-with-warn——已存在
    同 key → no-op（exit 0）+ stderr 警告，**字段参数被忽略**。刻意**不做字段比较**、
    不解析人写行去判断"是否真无变化"（match-or-error 方案已被 spec-review 否掉：
    `优先级`/`计划` 缺省会写 `BATCH_PLACEHOLDER`，重跑时传具体值 vs 已有占位符，
    "相等"判据在语义上就是死胡同——占位符从不代表"用户确认过的空值"）。忽略字段是
    这条 opt-in 分支的声明语义，不是缺陷；不想忽略字段就不要传 `--if-exists skip`。
    """
    root = repo_root(args.root)
    _reject_batch_key_unsafe(args.key)
    _reject_batch_line_unsafe(args.title, "title")
    # [impl-review-fix] FIX-5（CV-2 codex PoC）：优先级/计划此前原样写进
    # `f"优先级: {priority}\n"`/`f"计划: {plan}\n"` 单行，未挂守卫——含换行的值能在
    # batches.md 里注入一整条伪造的 `### … — …` header 行，被 `_BATCH_HEADER_RE` 当成
    # 一个新批次条目解析出来。挂在原始入口参数（写盘前）上，拒 `|`/换行。
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
    """`batch set-status {key} {S}`：只改该条目的 `状态:` 生成行，绝不动人写行（Q3）
    或 `成员:` 生成行（那是 reindex/Task 11 的职责，本命令不碰）。
    """
    root = repo_root(args.root)
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
        # 防御式兜底：条目缺 `状态:` 生成行（理论上 add 必写，这里只防手造/损坏的 batches.md）。
        # 只在 header 后插一行，不碰任何既有人写行的位置。
        lines.insert(header_idx + 1, f"状态: {args.status}\n")

    atomic_write(path, "".join(lines))
    print(json.dumps(
        {"key": args.key, "old_status": old_status, "new_status": args.status}, ensure_ascii=False
    ))


def cmd_batch_rename(args):
    """Registry-first, retryable, direct-snapshot cross-pool batch rename."""
    root = repo_root(args.root)
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


# ── sweep（Task 1，roadmap 阶段 1）────────────────────────────────────────────
# `sweep --change X`：把 sdflow-done §2.1 收尾的 issues 分诊从"模型手跑 4 步 bash
# 循环"固化为一次确定性、非原子、fail-closed、可重跑收敛的操作（design.md D1-D6）。
# 全部子步走 subprocess CLI（scan --open-ungrouped / triage / batch add --if-exists
# skip / reindex），不直调 cmd_*（避 args-namespace 脆弱性 + `_scan_pool` 硬编码无
# 过滤参数）。

def cmd_sweep(args):
    """入口守卫（先于任何写盘）→ 逐池 `scan --change X --open-ungrouped --json`
    （= 源==X ∧ 非终态 ∧ 批次空，D3）→ 逐项 `triage --id --批次 X`（查 returncode，
    非零即 fail-closed 报点位，D4/D5）→ 0 命中直接返回，不建僵尸批次条目
    （[impl-review-fix] FIX-2）→ `batch add X --if-exists skip`（D2 幂等）→
    `reindex`（末步也 fail-closed；rename 同样以 provenance + 原命令重跑契约 fail-closed，D4）。

    [impl-review-fix] FIX-5：`--change` 首尾若有空白，此前被静默 `.strip()` 后当合法
    change 使用（例如 `" chg"` 悄悄变成 `"chg"`）——但配套文档承诺"含空白即拒"，静默
    纠正违反契约、也让调用方误以为原始参数被原样接受。改为：先比较原始参数与其 strip
    结果是否相同，不同则 fail-closed（先于任何写盘），不再静默改写用户输入。
    """
    root = repo_root(args.root)
    raw_change = args.change or ""
    # [impl-review-fix] FIX-5：首尾空白 fail-closed，不静默 strip 后放行。
    if raw_change != raw_change.strip():
        _die(f"sweep --change 首尾不可有空白（不静默 strip，防误纳）：{raw_change!r}")
    change = raw_change
    if not change:
        _die("sweep --change 不可为空（防空 change 误纳孤儿）")
    _reject_batch_key_unsafe(change)  # 拒 |/换行/ — /首尾空白，先于任何写盘（D5）

    tagged = []  # 已成功 tag 的 id（失败时报点位用）
    for script, pool, idkey in (
        (BUGLIST_SCRIPT, "bug", "bugs"),
        (TODOLIST_SCRIPT, "todo", "items"),
    ):
        proc = subprocess.run(
            [sys.executable, script, "--root", root, "scan",
             "--change", change, "--open-ungrouped", "--json"],
            capture_output=True, text=True, env=recorder_child_env("scan"),
        )
        if proc.returncode != 0:
            _die(f"sweep: {pool} scan 失败 (rc={proc.returncode}): {proc.stderr.strip()}")
        data = json.loads(proc.stdout)
        # [impl-review-fix] FIX-1：此前只取 idkey，`problems`（per-type 脚本自身的一致性
        # 自检信号，如表↔块不一致/重复 ID/OV-1 行 arity 异常）被静默丢弃——重蹈
        # CR-4/FIX-4 修过的"problems 静默蒸发"坑。非空即回显 stderr（带 pool 标注），
        # **不收紧退出码**（更强的 `reindex --strict` enforcement 是延后的 roadmap T2.5）。
        for p in (data.get("problems") or []):
            print(f"sweep: {pool} scan problems: {p}", file=sys.stderr)
        items = data.get(idkey, [])
        for it in items:
            iid = it["id"]
            tp = subprocess.run(
                [sys.executable, script, "--root", root, "triage",
                 "--id", iid, "--批次", change],
                capture_output=True, text=True, env=recorder_child_env("triage"),
            )
            if tp.returncode != 0:
                _die(
                    f"sweep: triage 失败于 {pool} 第 {iid} 项 (rc={tp.returncode})；"
                    f"已 tag={tagged}: {tp.stderr.strip()}"
                )
            tagged.append(iid)

    # [impl-review-fix] FIX-2：0 命中（tagged 为空）时此前仍无条件建批次条目——0 成员的
    # 批次因 D1 vacuous-truth 排除永远不会被 reindex 判 DONE，逐 change 累积僵尸 PLANNED
    # 条目。改为仅当确有命中项时才建批次/刷新 INDEX；0 命中直接返回，不写盘。
    if not tagged:
        print(f"sweep {change}: tagged 0 项，无匹配项，跳过 batch add/reindex")
        return

    ba = subprocess.run(
        [sys.executable, __file__, "--root", root, "batch", "add",
         change, "--if-exists", "skip"],
        capture_output=True, text=True, env=recorder_child_env("batch-add"),
    )
    if ba.returncode != 0:
        _die(f"sweep: batch add 失败 (rc={ba.returncode}): {ba.stderr.strip()}")

    ri = subprocess.run(
        [sys.executable, __file__, "--root", root, "reindex"],
        capture_output=True, text=True, env=recorder_child_env("reindex"),
    )
    if ri.returncode != 0:
        _die(f"sweep: reindex 失败 (rc={ri.returncode}): {ri.stderr.strip()}")
    # [impl-review-fix] FIX-1：reindex 成功路径此前丢弃 `ri.stderr`——reindex 子进程内部
    # `_echo_problems` 写的 problems 回显（两池一致性自检信号）到这里被整体静默蒸发。
    # 非空即透传到本进程 stderr。
    elif ri.stderr.strip():
        print(ri.stderr, end="" if ri.stderr.endswith("\n") else "\n", file=sys.stderr)

    print(f"sweep {change}: tagged {len(tagged)} 项 {tagged}")


def main():
    global _ACTIVE_RECORDER_TOKEN, _ACTIVE_RECORDER_CHAIN
    p = argparse.ArgumentParser(
        description="共享 issues 层：跨 bug+todo 的 reindex / batch"
    )
    p.add_argument("--root", default=".", help="目标项目根（存 openspec/issues/... 的仓库）")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("reindex", help="重建 issues/INDEX.md（open×批次板）+ 同步 issues/batches.md 状态")
    s.add_argument(
        "--strict", action="store_true",
        help="两池一致性自检有 problems（表↔块不一致/OV-1 行 arity 异常等）时以非 0 退出"
             "（默认不加此参数：problems 仍回显到 stderr，但 exit 0）",
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
        # [impl-review-fix] FIX-3：原措辞"原子分诊"误导——本命令是多子步 subprocess 顺序
        # 调用（scan→triage→batch add→reindex），非原子（无跨子步事务），fail-closed +
        # 失败后重跑收敛，改为准确措辞。
        help="一键封装（非原子、fail-closed、可重跑收敛）：把本 change 未分批非终态项分诊"
             "入批次（scan --open-ungrouped → triage → batch add --if-exists skip → "
             "reindex，全子步 subprocess CLI）",
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
                _ACTIVE_RECORDER_TOKEN = lock_state.token
                _ACTIVE_RECORDER_CHAIN = lock_state.chain
                args.func(args)
                _ACTIVE_RECORDER_TOKEN = None
                _ACTIVE_RECORDER_CHAIN = None
            sys.stdout.write(output.getvalue())
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
