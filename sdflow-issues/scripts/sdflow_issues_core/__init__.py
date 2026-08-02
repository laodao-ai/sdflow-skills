"""sdflow_issues_core — issues 台账三脚本（buglist/todolist/issues 薄入口）的唯一共享逻辑源。

（dedupe-issues-scripts-shared-layer · adr/0027）三 skill 合一为 `sdflow-issues` 后，
bug/todo/issues 共享的执行逻辑收敛到本 package，作**唯一物理编辑源**；三薄入口
`from sdflow_issues_core import ...` 取用。**唯一命名**（非裸 `core`）避免全局
`sys.modules["core"]` 与别处同名模块碰撞（AD-1 / SC-R2）。

## 差异注入的两条正交轴（AD-3 / Q2）

1. **数据差异 → `POOL_SPEC`（封闭 schema）**：文件粒度、目录、legacy glob、特定字段、
   状态词表、终态集、ID 前缀、scan 输出键、pool 身份、是否强制建块——全部收敛为一张
   封闭 `PoolSpec` dataclass。共享逻辑按注入的 `PoolSpec` 取值；**MUST NOT** 在 core 源码里
   出现针对 pool 值（`"bug"`/`"todo"`）的条件分支，也 MUST NOT 从 argparse default / 硬编码
   常量引入新差异。新增差异维 = 改 `PoolSpec` 字段 **且** 同步 `POOL_SPEC_FIELDS`。
2. **不可数据化的控制流差异 → 命名 + 限定签名的策略钩子 `PoolStrategy`（Q2）**：某些
   orchestrator 逻辑（bug 详细块 vs todo 可选块、bug FIXED 门禁读块内根因 vs todo 无此门禁
   并惰性建 minimal 块、scan 排序/渲染、add 输出字段、CLI period 旗标名）证伪「差异全可参数化」
   ——保留为**封闭 dataclass `PoolStrategy` 的命名字段**（非塞进 POOL_SPEC 的任意 callable），
   每个 pool 一个实例（`BUG_STRATEGY`/`TODO_STRATEGY`），由薄入口**选取**（选取发生在薄入口，
   core 不按 pool 值选 strategy）。策略钩子例外逐个见 impl-report。

封闭性 + 关系正确性（`terminal_set ⊆ status_values`、keys 恰为 `{"bug","todo"}`）在
import 时 fail-closed 自校验（`validate_pool_spec()`）；与外部权威常量的逐值一致由
`tests/test_pool_spec_schema.py` 守。
"""

import argparse
from contextlib import contextmanager, redirect_stdout
from dataclasses import dataclass, field, fields
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
from typing import Callable


# ══════════════════════════════════════════════════════════════════════════════
# POOL_SPEC —— 封闭 schema（数据差异注入的唯一入口）
# ══════════════════════════════════════════════════════════════════════════════

class PoolSpecError(ValueError):
    """POOL_SPEC 封闭 schema / 关系正确性被破坏（缺维、越界 pool、终态越词表、非法值）。"""


@dataclass(frozen=True)
class PoolSpec:
    """一个 pool（bug 或 todo）的全部数据差异维——封闭 schema，required 维 = 字段全集。

    新增差异维 MUST 在此加字段 **并** 同步 `POOL_SPEC_FIELDS`；不得把差异硬编码进
    core 逻辑 / argparse default。字段全部为不可变值（`frozenset` 而非 `set`）。
    """

    # pool 身份（"bug"|"todo"）——共享逻辑用它给 model["pool"] 打标 / 定位本池文档，
    # 替代散落在 cmd_* 里的 "bug"/"todo" 字面 pool 分支（AD-3）。
    pool: str
    # 文件粒度：bug=日（file_for_date / today_str）；todo=月（file_for_month / this_month）
    date_granularity: str          # "day" | "month"
    file_stem: str                 # dated 文件干 + issues 子目录叶名："buglist" | "todolist"
    # 目录（相对 repo root 的 canonical issues 目录，对应 buglists_dir / todolists_dir）
    issues_dir: str                # "openspec/issues/buglist" | "openspec/issues/todolist"
    # legacy dir glob（过渡期 dual-read 的旧目录，对应 legacy_buglists_dir / legacy_todolists_dir）
    legacy_dir_glob: str           # "openspec/buglists/*.md" | "openspec/todolists/*.md"
    # 特定字段：字段名与其合法枚举成对
    specific_field: str            # "priority" | "type"
    specific_values: frozenset     # PRIORITIES | TYPE_TAGS
    # 状态词表
    status_values: frozenset
    # 终态集（MUST ⊆ status_values）
    terminal_set: frozenset
    # ID 前缀（canonical_id 空间隔离依赖它）
    default_prefix: str            # "B" | "T"
    # scan JSON envelope 的 item 数组键
    scan_output_key: str           # "bugs" | "items"
    # 是否强制每个 frontmatter item 都有 marker 详细块（bug=True 强制；todo=False 详细块可选）。
    # 替代 _build_effective_snapshot 里 `if expected_pool == "bug"` 的 pool 字面分支（AD-3）。
    requires_block: bool


# 差异维注册表 —— 「新增维必须改 schema」的机械化锚点。**手写字面**（MUST NOT 由
# fields(PoolSpec) 自动派生——自动派生会让下面的漂移守恒真、拦不住任何东西）。
POOL_SPEC_FIELDS = (
    "pool",
    "date_granularity",
    "file_stem",
    "issues_dir",
    "legacy_dir_glob",
    "specific_field",
    "specific_values",
    "status_values",
    "terminal_set",
    "default_prefix",
    "scan_output_key",
    "requires_block",
)


# [impl-review-fix] V3: specific 枚举的**有序**单一源。frozenset 无序、给人看的提示需有序，
# ∴ 有序 tuple 为唯一源：`POOL_SPEC.specific_values`（集合，cmd_add 判合法用）与
# `PoolStrategy.specific_values_ordered`（有序，提示/lint 用）**同源派生**，结构上不可能漂移
# （消除「add 收但 lint 拒 / 提示与规则不一致」，V3 双真相源）。
BUG_SPECIFIC_VALUES_ORDERED = ("P0", "P1", "P2", "P3", "P4")
TODO_SPECIFIC_VALUES_ORDERED = ("性能优化", "可观测性", "代码质量", "功能增强", "基础设施")


POOL_SPEC = {
    "bug": PoolSpec(
        pool="bug",
        date_granularity="day",
        file_stem="buglist",
        issues_dir="openspec/issues/buglist",
        legacy_dir_glob="openspec/buglists/*.md",
        specific_field="priority",
        specific_values=frozenset(BUG_SPECIFIC_VALUES_ORDERED),
        status_values=frozenset(
            {"OPEN", "VERIFIED", "PROPOSED", "IN_PROGRESS", "FIXED", "WONTFIX", "BLOCKED"}
        ),
        terminal_set=frozenset({"FIXED", "WONTFIX"}),
        default_prefix="B",
        scan_output_key="bugs",
        requires_block=True,
    ),
    "todo": PoolSpec(
        pool="todo",
        date_granularity="month",
        file_stem="todolist",
        issues_dir="openspec/issues/todolist",
        legacy_dir_glob="openspec/todolists/*.md",
        specific_field="type",
        specific_values=frozenset(TODO_SPECIFIC_VALUES_ORDERED),  # [impl-review-fix] V3 单一源
        status_values=frozenset({"OPEN", "PROPOSED", "DONE", "WONTDO"}),
        terminal_set=frozenset({"DONE", "WONTDO"}),
        default_prefix="T",
        scan_output_key="items",
        requires_block=False,
    ),
}


def validate_pool_spec(spec=None):
    """校验一份 POOL_SPEC 映射的封闭性 + 关系正确性，违规抛 PoolSpecError（fail-closed）。"""
    if spec is None:
        spec = POOL_SPEC
    if set(spec) != {"bug", "todo"}:
        raise PoolSpecError(
            f"ERROR: POOL_SPEC keys 必须恰为 {{'bug','todo'}}，实际 {sorted(spec)}; "
            f"cause: 越界/缺失 pool key; fix: 只保留 bug/todo 两池"
        )
    registry = set(POOL_SPEC_FIELDS)
    schema_fields = {f.name for f in fields(PoolSpec)}
    if registry != schema_fields:
        raise PoolSpecError(
            f"ERROR: POOL_SPEC_FIELDS 注册表与 PoolSpec 字段全集不一致；"
            f"注册表独有 {registry - schema_fields}，schema 独有 {schema_fields - registry}; "
            f"cause: 新增/删除差异维只改了一处; fix: 同步改 PoolSpec 字段与 POOL_SPEC_FIELDS"
        )
    for pool, value in spec.items():
        if not isinstance(value, PoolSpec):
            raise PoolSpecError(
                f"ERROR: POOL_SPEC[{pool!r}] 不是 PoolSpec 实例（{type(value).__name__}）; "
                f"cause: 差异从封闭 schema 之外的裸值塞进; fix: 用 PoolSpec(...) 承载全部差异维"
            )
        if not value.terminal_set <= value.status_values:
            raise PoolSpecError(
                f"ERROR: POOL_SPEC[{pool!r}].terminal_set {set(value.terminal_set)} "
                f"⊄ status_values {set(value.status_values)}; "
                f"cause: 终态越出状态词表; fix: 终态集必须是状态词表子集"
            )
        # [impl-review-fix] V2: fail-closed 补漏——身份一致 + 关键维非空
        if value.pool != pool:
            raise PoolSpecError(
                f"ERROR: POOL_SPEC[{pool!r}].pool == {value.pool!r} 与 dict key 不符; "
                f"cause: 实例装错桶（key 与内嵌 pool 身份漂移）; fix: value.pool 必须 == 其 dict key"
            )
        for dim in ("issues_dir", "file_stem", "default_prefix", "legacy_dir_glob", "specific_field"):
            if not getattr(value, dim):
                raise PoolSpecError(
                    f"ERROR: POOL_SPEC[{pool!r}].{dim} 为空; "
                    f"cause: 字符串维缺省/空串（fail-open 洞：空目录/空前缀会静默落错位置）; "
                    f"fix: 每个字符串契约维必须非空"
                )
        for dim in ("specific_values", "status_values", "terminal_set"):
            if not getattr(value, dim):
                raise PoolSpecError(
                    f"ERROR: POOL_SPEC[{pool!r}].{dim} 为空集; "
                    f"cause: 枚举/状态/终态集空（fail-open 洞：空枚举令一切值合法或一切非法）; "
                    f"fix: 每个集合维必须非空"
                )
    return True


validate_pool_spec()


# ══════════════════════════════════════════════════════════════════════════════
# PoolStrategy —— 不可数据化控制流差异的封闭命名钩子（Q2；非 POOL_SPEC 的一部分）
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class PoolStrategy:
    """一个 pool 的**不可数据化**控制流差异，收敛为限定签名的命名钩子（Q2 例外，逐个见 impl-report）。

    与 POOL_SPEC 正交：POOL_SPEC 是纯数据（值），PoolStrategy 是命名策略函数（限定签名，
    非任意 callable 逃生口——它是封闭 dataclass 的具名字段，加钩子必须改 schema）。薄入口
    选取本池实例；core 不按 pool 值在 strategy 间选择。
    """

    # add：详细块构建（bug 恒非空；todo 视 motivation/approach/note/显式 doc 可能返回 ""）
    build_block: Callable
    # add：canonical 首块 header 文本（bug 用 source/date；todo 用 project/month）
    header: Callable
    # add：本池必填的**额外**字段（module/summary/specific_field 之外），bug=("phenomenon",)、todo=()
    add_required_extra: tuple
    # add：specific 字段非法时的错误标签 + 有序枚举（frozenset join 顺序不定，故有序值随策略走）
    specific_label: str
    specific_values_ordered: tuple
    # add：JSON payload 里承载的 source-like 单行字段名（bug="source"；todo="project"）
    source_field: str
    # add：记录时间 strftime 格式（bug "%H:%M"；todo "%Y-%m-%d %H:%M"）
    add_time_fmt: str
    # add：stdout JSON 输出 dict 构建（字段/顺序按 pool 各异）
    add_output: Callable
    # scan：排序键与单行渲染 + 空结果提示
    scan_sort_key: Callable
    scan_line: Callable
    scan_empty_msg: str
    # set-status / triage：控制流整体差异（bug 门禁读块内根因、todo 惰性 minimal 块）→ 整函数策略
    set_status: Callable
    triage: Callable
    # CLI：period 覆盖旗标（bug "--date"；todo "--month"）+ help 文案 + scan 是否有 --type 过滤
    period_flag: str
    period_help: str
    time_help: str
    add_help: str
    set_status_help: str
    scan_help: str
    scan_has_type_filter: bool
    description: str


# ══════════════════════════════════════════════════════════════════════════════
# 共享常量（pool-agnostic）+ pool 派生常量
# ══════════════════════════════════════════════════════════════════════════════

ID_RE = re.compile(r"\b([A-Z])([0-9]+)\b", re.ASCII)
CANONICAL_ID_RE = re.compile(r"^[A-Z][1-9][0-9]*$", re.ASCII)
UTF8_BOM = b"\xef\xbb\xbf"

# RECORDER_POOL_CONFIG 从 POOL_SPEC 派生（单一源）：(特定字段, 枚举 set, 状态词表 set)。
RECORDER_POOL_CONFIG = {
    pool: (spec.specific_field, set(spec.specific_values), set(spec.status_values))
    for pool, spec in POOL_SPEC.items()
}
# 各 pool 终态集（issues reindex 的 _is_terminal 用）——同样从 POOL_SPEC 派生。
TERMINAL_STATUSES = {pool: set(spec.terminal_set) for pool, spec in POOL_SPEC.items()}

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

# period 粒度 → 日期 strftime / dated 文件名日期段正则（按粒度值取，非 pool 字面分支）。
_GRANULARITY_FMT = {"day": "%Y-%m-%d", "month": "%Y-%m"}
_GRANULARITY_DATE_RE = {"day": r"[0-9]{4}-[0-9]{2}-[0-9]{2}", "month": r"[0-9]{4}-[0-9]{2}"}

BRANCH_PREFIX_RE = re.compile(r"^[a-z]+/")

_ISSUE_MARKER_LINE_RE = re.compile(
    r"^<!-- sdflow-issue-block:(start|end) id=([A-Z][1-9][0-9]*) -->[ \t]*$", re.ASCII
)


class RecorderLockError(ValueError):
    pass


class RecorderLockState:
    def __init__(self, path, token, participant=False, identity=None, chain=()):
        self.path = path
        self.token = token
        self.participant = participant
        self.identity = identity
        self.chain = tuple(chain)


# ══════════════════════════════════════════════════════════════════════════════
# THREE_WAY 共享 helper（原三脚本各自内联，现唯一物理源）
# ══════════════════════════════════════════════════════════════════════════════

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
    # 每池两条 glob：新目录 + legacy 目录，均从 POOL_SPEC 派生（单一源）。
    pool_patterns = {
        pool: (f"{spec.issues_dir}/*.md", spec.legacy_dir_glob)
        for pool, spec in POOL_SPEC.items()
    }
    snapshot = []
    seen_paths = set()
    for pool, patterns in pool_patterns.items():
        for pattern in patterns:
            for path in sorted(glob.glob(os.path.join(root, pattern))):
                path = os.path.normpath(path)
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
    fields_ = {"module", "summary", specific_field, "status", "time", "change", "batch"}
    normalized = {"schema": 1, "pool": pool, "mode": model["mode"], "items": {}}
    semantic_ids = set()
    for item_id, original in model["items"].items():
        if not isinstance(item_id, str) or not CANONICAL_ID_RE.fullmatch(item_id):
            _frontmatter_error(f"ID 非 canonical ASCII spelling", repr(item_id))
        semantic_key = (item_id[0], int(item_id[1:]))
        if semantic_key in semantic_ids:
            _frontmatter_error("semantic ID 重复", item_id)
        semantic_ids.add(semantic_key)
        if not isinstance(original, dict) or set(original) != fields_:
            got = sorted(original) if isinstance(original, dict) else type(original).__name__
            _frontmatter_error(f"{item_id} 字段集合非法", f"expected={sorted(fields_)} got={got}")
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
    spec = POOL_SPEC[expected_pool]
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
        if spec.requires_block:
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
        if spec.requires_block and item_id not in legacy_blocks:
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
    # harden-issues-read-write Task 1 (1a)：读取路径两层词表校验的 core 层——status /
    # specific_field（priority|type）越出 POOL_SPEC 词表时只记 problem，不 raise、不丢项
    # （脏值项仍留在 effective_items 里，交上层 reindex/scan 显红而非整体崩溃）。
    for item_id, item in effective_items.items():
        if item["status"] not in spec.status_values:
            problems.append(
                f"{item_id}: status {item['status']!r} 不在词表 {sorted(spec.status_values)}"
            )
        if item[spec.specific_field] not in spec.specific_values:
            problems.append(
                f"{item_id}: {spec.specific_field} {item[spec.specific_field]!r} "
                f"不在词表 {sorted(spec.specific_values)}"
            )
    result.update({
        "effective_items": effective_items,
        "effective_occurrences": occurrences,
        "problems": problems,
    })
    return result


# ── 路径与文件 ───────────────────────────────────────────────────────────────

def repo_root(start=None):
    """探测并**证明**起点所属 git 仓库的根；非 git 仓库（或 git 命令失败）退化为
    `os.path.abspath(start)`。

    **单点解析（ADR-5）**：本函数在一个进程内 MUST 只被调用一次——`main()` 调它并把结果
    写回 `args.root`，其余 `cmd_*` / `_*_snapshot` 一律直接用 `root = args.root`，
    MUST NOT 再调本函数。理由不是省一次子进程：本函数的校验逐次独立，两次解析之间目标若
    失去 `.git`，第二次会静默爬升到外层祖先仓库（两次都 rc=0、都过全部校验），于是锁建在
    一个根、数据写进另一个根。子进程以 `--root <已解析值>` 拉起时会各自再解析一次——
    「一次」的边界是**进程**，不是逻辑命令。

    契约（本函数可能抛异常，调用方 MUST 在捕获 `ValueError` 的 try 内调用）：
    返回值在被当作可写仓根之前，必须被证明是**起点所属仓库的【最近】仓库的根**。判据依次为
    起点可信性 → 环境净化 → 调 git → 最近 marker 上溯 → git 失败裁决 → 形状校验 →
    祖先校验 → worktree marker → 最近根一致；任一步不满足即 `raise ValueError`。

    **回落的判据是「上溯一层 `.git` 都没找到」，不是「git 退出码非 0」。** 旧契约把整个
    非 0 退出归为回落，其枚举（非 git 仓库 / git 不可用 / bare repo / `.git/` 目录内）
    **不完备，正是 fail-open 的成因**：`safe.directory`（dubious ownership）、损坏的
    `.git/config` 同样以 128 退出，而进程确实在仓内。故 git 失败且上溯**找得到** marker
    ⇒ `raise`；只有一层都找不到才回落。超时同样**不回落**。

    最近根一致（末步）堵另一个方向：git 成功且返回值确是起点的祖先，但那是**外层祖先
    仓库**（core.worktree 指向祖先仓 / PATH 上的 fake git）——祖先校验与 worktree marker
    会双双放行，只有「上溯到的第一个 marker 严格等于 git 返回的根」能证明它是**最近**的。
    """
    # 环境净化清单（ADR-6）：MUST 保持为函数体内的局部常量。
    discovery_env = (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_CEILING_DIRECTORIES",
        "GIT_INDEX_FILE", "GIT_DISCOVERY_ACROSS_FILESYSTEM",
        "GIT_CONFIG_COUNT", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM",
    )
    discovery_env_prefixes = ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")
    if start is not None and not os.path.isdir(start):
        raise ValueError(
            "ERROR: 仓根探测起点不是既存目录: " + ascii(start)[:200]
            + "; cause: 显式指定的起点路径不存在或不是目录; "
            "fix: 指定一个既存目录作为起点"
        )
    if start is None or not os.path.isabs(start):
        try:
            cwd = os.getcwd()
        except OSError:
            raise ValueError(
                "ERROR: 无法确定仓根探测起点; cause: 进程当前工作目录已不存在或不可访问; "
                "fix: 切换到一个既存目录后重试，或显式指定一个绝对路径作为起点"
            ) from None
        start = cwd if start is None else os.path.join(cwd, start)
    env = recorder_child_env("git", token=False)
    for name in [
        n for n in env
        if n in discovery_env or n.startswith(discovery_env_prefixes)
    ]:
        env.pop(name, None)
    git_timeout = 30
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start, capture_output=True, check=True,
            env=env, timeout=git_timeout,
        )
    except subprocess.TimeoutExpired:
        raise ValueError(
            "ERROR: 仓根探测超时; cause: git rev-parse --show-toplevel 在 "
            + str(git_timeout) + " 秒内未返回; "
            "fix: 确认该目录所在文件系统未挂起（网络盘/自动挂载卷最常见），"
            "再在该目录手动跑 git rev-parse --show-toplevel 看是否同样卡住"
        ) from None
    except (OSError, subprocess.CalledProcessError):
        out = None
    start_real = os.path.realpath(start)
    marker_dir = None
    probe = start_real
    while True:
        if os.path.exists(os.path.join(probe, ".git")):
            marker_dir = probe
            break
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent
    if out is None:
        if marker_dir is not None:
            raise ValueError(
                "ERROR: 起点位于 git 仓库内但 git 拒绝作答: " + ascii(start_real)[:200]
                + "; cause: 上溯找到 .git marker，而 git rev-parse --show-toplevel 以非 0 退出"
                "（dubious ownership / 配置损坏 / git 不可用等）; "
                "fix: 在该目录手动跑 git rev-parse --show-toplevel 看完整报错；"
                "若是 dubious ownership 则 git config --global --add safe.directory <仓根>"
            )
        return os.path.abspath(start)
    top = os.fsdecode(out.stdout).rstrip("\r\n")
    if not top or not os.path.isabs(top) or not os.path.isdir(top):
        raise ValueError(
            "ERROR: git 返回的仓根不可用: " + ascii(top)[:200]
            + "; cause: git rev-parse --show-toplevel 的输出不是既存的绝对路径目录; "
            "fix: 在该起点手动跑 git rev-parse --show-toplevel 比对输出，"
            "并用 which -a git 确认 PATH 上的 git 未被 wrapper 替换"
        )
    top_real = os.path.realpath(top)
    try:
        common = os.path.commonpath([
            os.path.normcase(start_real), os.path.normcase(top_real),
        ])
    except ValueError:
        raise ValueError(
            "ERROR: 无法比较 git 返回的仓根与探测起点: " + ascii(top)[:200]
            + "; cause: 两者不在同一个路径根下（如 Windows 跨盘符），无公共前缀可比; "
            "fix: 检查 .git/config 的 core.worktree 是否把工作树指到了另一个盘符，"
            "并清除 GIT_WORK_TREE / GIT_DIR 等重定向后重试"
        ) from None
    if common != os.path.normcase(top_real):
        raise ValueError(
            "ERROR: git 返回的仓根不包含探测起点: " + ascii(top)[:200]
            + "; cause: 工作树被 core.worktree 或环境变量重定向到起点之外; "
            "fix: 清除 .git/config 的 core.worktree 与 GIT_* 重定向后重试"
        )
    if not os.path.exists(os.path.join(top_real, ".git")):
        raise ValueError(
            "ERROR: git 返回的仓根缺少 .git: " + ascii(top)[:200]
            + "; cause: 该目录不带 worktree marker，不是一个仓库根; "
            "fix: 确认 .git/config 的 core.worktree 未指向非仓库目录，"
            "并用 which -a git 确认 PATH 上的 git 未被 wrapper 替换"
        )
    if os.path.normcase(marker_dir) != os.path.normcase(top_real):
        raise ValueError(
            "ERROR: git 返回的仓根不是起点所属的最近仓库: " + ascii(top)[:200]
            + "; cause: 自起点上溯遇到的第一个 .git 位于 " + ascii(marker_dir)[:200]
            + "，git 却返回了更外层的仓库（core.worktree 指向祖先仓 / git 被替换）; "
            "fix: 清除 .git/config 的 core.worktree 重定向，"
            "并用 which -a git 确认 PATH 上的 git 未被 wrapper 替换"
        )
    return top_real


def detect_change(root):
    """自动探测当前所处 OpenSpec change 名，供 add 时记录来源（可被 --json 里的 change 覆盖）。
    优先级：openspec/changes/ 下唯一未归档目录 → git branch 名去前缀 → 空字符串。"""
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
            # [impl-review-fix] F5: text=True 须显式 encoding="utf-8"——Windows 非 UTF-8
            # locale 下 git 输出按平台默认编码解码可能崩（已知 Windows CI 陷阱）。
            cwd=root, capture_output=True, text=True, check=True, encoding="utf-8",
            errors="replace",
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
    每项保证以 'openspec/' 开头（缺前缀则补）。"""
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
    """软校验：文档路径（相对 root）不存在只打 stderr 警告，不阻断记录。"""
    for d in docs:
        if not os.path.isfile(os.path.join(root, d)):
            print(f"WARNING: 关联文档路径不存在：{d}", file=sys.stderr)


def auto_default_doc(root, change):
    """change 已知但显式 doc 为空时，尽力探测关联文档（design.md → proposal.md → archive/*）。"""
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
                rel = os.path.relpath(candidate, root).replace(os.sep, "/")
                return [rel.replace(os.sep, "/")]
    return []


def render_doc_block(docs):
    """渲染详细块里的『关联文档』行；docs 为空则返回空串（不插入该行）。"""
    if not docs:
        return ""
    return "\n**关联文档**：" + "、".join(f"`{d}`" for d in docs) + "\n"


# ── pool 派生的路径 / 文件 / ID 扫描（差异经 POOL_SPEC 注入）─────────────────────

def dated_dir(root, spec):
    return os.path.join(root, *spec.issues_dir.split("/"))


def legacy_dir(root, spec):
    return os.path.join(root, *os.path.dirname(spec.legacy_dir_glob).split("/"))


def _dated_dirs(root, spec):
    """新在前（写落新），旧只读兼容——过渡期 dual-read 两目录（Phase B Q1 加固）。"""
    return [dated_dir(root, spec), legacy_dir(root, spec)]


def list_files(root, spec):
    out = []
    pattern = re.compile(
        rf"{_GRANULARITY_DATE_RE[spec.date_granularity]}-{spec.file_stem}\.md$", re.ASCII
    )
    for d in _dated_dirs(root, spec):  # 新在前（目录序），不可对拼接后的全路径整体 sorted
        if os.path.isdir(d):
            files = [
                os.path.join(d, f) for f in os.listdir(d)
                if pattern.match(f)
            ]
            out += sorted(files)  # 各目录内部按文件名（=日期/月份）排序
    return out


def _period_str(spec, override=None):
    if override:
        return override
    return datetime.date.today().strftime(_GRANULARITY_FMT[spec.date_granularity])


def file_for_period(root, spec, period):
    return os.path.join(dated_dir(root, spec), f"{period}-{spec.file_stem}.md")


def ensure_file(root, spec, period):
    return file_for_period(root, spec, period)


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


def _ids_in_files(paths, prefix=None):
    ids = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"\|\s*([A-Z][0-9]+)\s*\|", line, re.ASCII)
                if m:
                    pid = m.group(1)
                    if prefix is None or pid.startswith(prefix):
                        ids.append(pid)
    return ids


def all_ids(root, spec, prefix=None):
    return _ids_in_files(list_files(root, spec), prefix)


def next_id(root, prefix, semantic=None):
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


def id_conflicts(root, spec):
    """跨路径 ID 冲突检测（Phase B Q1 加固）：同一 ID 同时出现在新旧两目录，存在撞号风险。
    只读、不阻断——调用方（CLI）自行决定打印警告还是忽略。"""
    new_dir, old_dir = dated_dir(root, spec), legacy_dir(root, spec)
    new_files = [p for p in list_files(root, spec) if os.path.dirname(p) == new_dir]
    old_files = [p for p in list_files(root, spec) if os.path.dirname(p) == old_dir]
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


def _find_row_file(root, item_id, spec):
    """定位含 item_id 的状态总览表行所在的 dated 文件。找不到则 `_die` 退出。"""
    for path in list_files(root, spec):
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


class LegacyBlockError(Exception):
    """Structured sentinel raised by the single-source legacy block scan.

    Carries only structured data (never caller-facing prose): ``kind`` is
    ``"ambiguous"`` (the semantic ID resolved to != 1 heading block) or
    ``"collision"`` (a preexisting marker line sits inside the resolved block).
    Each caller catches this and formats its own pool/language-appropriate fix
    message, so the scan itself stays pool-agnostic and prose-free (AD-3/Q2).
    """

    def __init__(self, kind, raw_id, *, candidates=None, line=None):
        super().__init__(kind)
        self.kind = kind
        self.raw_id = raw_id
        self.candidates = candidates
        self.line = line


def _scan_legacy_block_range(document, raw_id):
    """Pool-agnostic single source for the legacy block boundary scan.

    Resolve exactly one semantic legacy heading block for ``raw_id`` and reject a
    preexisting marker collision inside it, returning ``(start, end)`` line
    indices.  On failure raises :class:`LegacyBlockError` with structured data
    (no prose) — callers translate it into their own fix message.  This is the
    only copy of the scan algorithm; both ``_legacy_block_range`` (core, Chinese
    ``_frontmatter_error``) and issues' ``_rename_legacy_block_range`` (English
    rename-path ``ValueError``) delegate here.
    """
    starts = []
    key = _legacy_semantic_id_key(raw_id)
    for index, line in enumerate(document["lines"]):
        match = re.match(r"##\s+([A-Z][0-9]+)\s*:", line, re.ASCII)
        if match and _legacy_semantic_id_key(match.group(1)) == key:
            starts.append(index)
    if len(starts) != 1:
        raise LegacyBlockError("ambiguous", raw_id, candidates=len(starts))
    start = starts[0]
    end = len(document["lines"])
    for index in range(start + 1, len(document["lines"])):
        line = document["lines"][index]
        if line.strip() == "---" or re.match(r"##\s+[A-Z][0-9]+\s*:", line, re.ASCII):
            end = index
            break
    for index in range(start, end):
        if _match_marker_line(document["lines"][index]):
            raise LegacyBlockError("collision", raw_id, line=index + 1)
    return start, end


def _legacy_block_range(document, raw_id, path):
    try:
        return _scan_legacy_block_range(document, raw_id)
    except LegacyBlockError as exc:
        if exc.kind == "ambiguous":
            _frontmatter_error(
                f"file={path} legacy block 无法安全包裹",
                f"id={exc.raw_id} candidates={exc.candidates}",
                "修正为唯一 legacy block 后重试",
            )
        _frontmatter_error(
            f"file={path} legacy marker collision",
            f"id={exc.raw_id} line={exc.line}",
            "删除或转义候选块内预存 marker 后重试",
        )


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


def _minimal_marker_block(canonical, item, eol, history):
    """承重的 marker 契约：惰性建的 minimal `sdflow-issue-block` 6 行字节块
    （start 标记 / 二级标题 / summary 引用 / 历史 / end 标记）。history 为**已拼接的字节**
    （调用方对 tuple 形态先 `b"".join(...)`）。三处促升路径共用此单一源——格式一变只改此处。"""
    return (
        eol + f"<!-- sdflow-issue-block:start id={canonical} -->".encode("ascii") + eol
        + f"## {canonical}: {_display_title(item['summary'])}".encode("utf-8") + eol
        + _summary_blockquote(item["summary"]).encode("utf-8") + eol
        + history
        + f"<!-- sdflow-issue-block:end id={canonical} -->".encode("ascii") + eol
    )


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
    minimal = _minimal_marker_block(canonical, item, eol, b"".join(history))
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


def _prepare_overlay_model(document, pool, canonical, item):
    """pool-agnostic 公共写头：拷贝既有 overlay model（无则建 minimal overlay 骨架），
    深拷 items 后置入更新后的 item。差异经参数 pool/canonical/item 注入，无 pool 值分支。"""
    model = dict(document["model"] or {
        "schema": 1, "pool": pool, "mode": "overlay", "items": {},
    })
    model["items"] = dict(model["items"])
    model["items"][canonical] = item
    return model


def _commit_mutation(document, model, insertions, path, pool, canonical, require_marker, output):
    """pool-agnostic 公共写尾：splice → render → 关系自检 → 原子落盘 → stdout JSON。
    output 为调用方预建的结果 dict（各命令语义不同，此处只负责序列化打印）。"""
    body = _splice_body_lines(document, insertions)
    rendered = _render_recorder_document(document, model, body)
    atomic_write_bytes(path, _validated_rendered_mutation(
        rendered, pool, canonical, require_marker, path,
    ))
    print(json.dumps(output, ensure_ascii=False))


# ── 工具 ─────────────────────────────────────────────────────────────────────

def _load_json(src):
    if src in (None, "-"):
        return json.load(sys.stdin)
    with open(src, encoding="utf-8") as f:
        return json.load(f)


def _as_list(fix):
    if fix is None:
        return "- <待补充>"
    if isinstance(fix, list):
        return "\n".join(f"- {x}" for x in fix)
    return str(fix)


def _die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# 策略钩子实现（bug / todo）—— Q2 不可数据化控制流残余，命名函数（逐个见 impl-report）
# ══════════════════════════════════════════════════════════════════════════════

BUG_HEADER_TMPL = """# {date} Buglist

> 来源：{source}
> 创建日期：{date}
"""

TODO_HEADER_TMPL = """# {month} TODO

> 项目：{project}
"""


def _bug_build_block(spec, item_id, data, docs, explicit_docs):
    """bug 详细块（恒非空）：现象/根因/修复方案/影响范围 + optional。返回 markdown str。"""
    title = _display_title(data["summary"], data.get("title"))
    body = f"\n<!-- sdflow-issue-block:start id={item_id} -->\n"
    body += f"## {item_id}: {title}\n"
    body += _summary_blockquote(data["summary"]) + "\n"
    doc_block = render_doc_block(docs)
    if doc_block:
        body += doc_block
    body += f"\n**现象**：{_escape_user_markers(data['phenomenon'])}\n"
    body += f"\n**根因**：{_escape_user_markers(data.get('rootcause', '').strip() or '<待分析>')}\n"
    body += f"\n**修复方案**：\n{_escape_user_markers(_as_list(data.get('fix')))}\n"
    body += f"\n**影响范围**：{_escape_user_markers(data.get('impact', '<待评估>'))}\n"
    for key, value in (data.get("optional") or {}).items():
        body += f"\n**{_escape_user_markers(key)}**：{_escape_user_markers(value)}\n"
    body += f"<!-- sdflow-issue-block:end id={item_id} -->\n"
    return body


def _todo_build_block(spec, item_id, data, docs, explicit_docs):
    """todo 可选块：仅当 motivation/approach/note 任一非空或有显式 doc 才建；否则返回 ""。"""
    docs = docs or []
    explicit_docs = explicit_docs or []
    parts = {k: data.get(k, "").strip() for k in ("motivation", "approach", "note")}
    if not any(parts.values()) and not explicit_docs:
        return ""
    title = _display_title(data["summary"], data.get("title"))
    b = f"\n<!-- sdflow-issue-block:start id={item_id} -->\n## {item_id}: {title}\n"
    b += _summary_blockquote(data["summary"]) + "\n"
    b += render_doc_block(docs)
    if parts["motivation"]:
        b += f"\n**动机**：{_escape_user_markers(parts['motivation'])}\n"
    if parts["approach"]:
        b += f"\n**思路**：{_escape_user_markers(parts['approach'])}\n"
    if parts["note"]:
        b += f"\n**备注**：{_escape_user_markers(parts['note'])}\n"
    return b + f"<!-- sdflow-issue-block:end id={item_id} -->\n"


def _bug_header(spec, period, data):
    source = data.get("source") or "<未注明>"
    _reject_line_unsafe(source, "source")
    return BUG_HEADER_TMPL.format(date=period, source=source)


def _todo_header(spec, period, data):
    project = data.get("project") or "<未注明>"
    return TODO_HEADER_TMPL.format(month=period, project=project)


def _bug_add_output(item_id, rel, status, time_str, change, block):
    return {"id": item_id, "file": rel, "status": status,
            "time": time_str, "change": change or None}


def _todo_add_output(item_id, rel, status, time_str, change, block):
    return {"id": item_id, "file": rel, "status": status, "block": bool(block),
            "time": time_str, "change": change or None}


def _bug_scan_line(b):
    return f"{b['id']:<5} {b['priority']} {b['status']:<12} {b['module']:<24} {b['summary']}"


def _todo_scan_line(b):
    return f"{b['id']:<5} {b['status']:<10} {b['type']:<8} {b['module']:<24} {b['summary']}"


def _has_rootcause(lines, start, end):
    for i in range(start, end):
        m = re.match(r"\*\*根因\*\*：(.*)", lines[i].strip())
        if m:
            val = m.group(1).strip()
            return bool(val) and not re.fullmatch(r"<.*>", val)
    return False


def _todo_minimal_block(tid, cells, status, hist):
    title = cells[2]
    return (f"\n---\n\n## {tid}: {title}\n\n"
            f"| 属性 | 值 |\n|------|------|\n"
            f"| 模块 | {cells[1]} |\n| 类型 | {cells[3]} |\n| 状态 | {status} |\n\n{hist}")


def _bug_set_status(args, spec):
    root = args.root
    new = args.to
    if new not in spec.status_values:
        _die(f"状态码非法：{new}")

    _reject_line_unsafe(args.evidence, "evidence")
    _reject_line_unsafe(args.reason, "reason")
    _reject_line_unsafe(args.period, "date")

    path, document, raw_id, item = _find_item_document(root, args.id, spec.pool)
    _preflight_target_legacy_block(document, raw_id, path)
    _reject_document_mutation(document, path)
    canonical = _canonical_from_key(_legacy_semantic_id_key(raw_id))
    old = item["status"]
    frontmatter_owned = bool(document["model"] and canonical in document["model"]["items"])
    if not frontmatter_owned:
        b_start, b_end = _legacy_block_range(document, raw_id, path)
    else:
        if canonical not in document["marker_blocks"]:
            _frontmatter_error(
                f"file={path} marker block 缺失", f"id={canonical}", "修正 marker 后重试",
            )
        b_start, b_end = document["marker_blocks"][canonical]

    if new == "FIXED":
        if not args.evidence:
            _die("置为 FIXED 必须提供 --evidence（commit hash 或 change 名）")
        if not _has_rootcause(document["lines"], b_start, b_end):
            _die("置为 FIXED 前必须先补全『根因』（当前为空/占位符）")
    if new == "WONTFIX" and not args.reason:
        _die("置为 WONTFIX 必须提供 --reason（不修的理由）")

    note = args.evidence or args.reason or ""
    hist = f"> {_period_str(spec, args.period)} 状态：{old} → {new}" + (f"（{note}）" if note else "")
    eol = document["eol"]
    history = hist.encode("utf-8") + eol
    item["status"] = new
    model = _prepare_overlay_model(document, spec.pool, canonical, item)
    if not frontmatter_owned:
        insertions = _promotion_insertions(
            document, raw_id, canonical, path, item, (history,), True,
        )
    else:
        insertions = {b_end - 1: (history,)}
    _commit_mutation(
        document, model, insertions, path, spec.pool, canonical, True,
        {"id": canonical, "old": old, "new": new, "file": os.path.relpath(path, root).replace(os.sep, "/")},
    )


def _todo_set_status(args, spec):
    root = args.root
    new = args.to
    if new not in spec.status_values:
        _die(f"状态码非法：{new}")

    _reject_line_unsafe(args.evidence, "evidence")
    _reject_line_unsafe(args.reason, "reason")
    _reject_line_unsafe(args.period, "month")

    path, document, raw_id, item = _find_item_document(root, args.id, spec.pool)
    _preflight_target_legacy_block(document, raw_id, path)
    _reject_document_mutation(document, path)
    canonical = _canonical_from_key(_legacy_semantic_id_key(raw_id))

    if new == "DONE" and not args.evidence:
        _die("置为 DONE 必须提供 --evidence（关联的 change 名或 commit hash）")
    if new == "WONTDO" and not args.reason:
        _die("置为 WONTDO 必须提供 --reason（放弃的理由）")

    note = args.evidence or args.reason or ""
    old = item["status"]
    hist = f"> {_period_str(spec, args.period)} 状态：{old} → {new}" + (f"（{note}）" if note else "")
    eol = document["eol"]
    history = hist.encode("utf-8") + eol
    item["status"] = new
    model = _prepare_overlay_model(document, spec.pool, canonical, item)
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
        minimal = _minimal_marker_block(canonical, item, eol, history)
        insertions = {len(document["lines"]): (minimal,)}
    _commit_mutation(
        document, model, insertions, path, spec.pool, canonical, True,
        {"id": canonical, "old": old, "new": new, "file": os.path.relpath(path, root).replace(os.sep, "/")},
    )


def _bug_triage(args, spec, promote=True):
    root = args.root
    batch = getattr(args, "批次")

    path, document, raw_id, item = _find_item_document(root, args.id, spec.pool)
    _preflight_target_legacy_block(document, raw_id, path)
    _reject_document_mutation(document, path)
    canonical = _canonical_from_key(_legacy_semantic_id_key(raw_id))
    old_status = item["status"]
    if promote:
        open_untriaged = set(spec.status_values) - set(spec.terminal_set) - {"PROPOSED"}
        new_status = "PROPOSED" if old_status in open_untriaged else old_status
    else:
        new_status = old_status
    item["status"] = new_status
    item["batch"] = batch or None
    model = _prepare_overlay_model(document, spec.pool, canonical, item)
    eol = document["eol"]
    history = ()
    if new_status != old_status:
        history = (
            f"> {_period_str(spec)} 状态：{old_status} → {new_status}".encode("utf-8") + eol,
        )
    frontmatter_owned = bool(document["model"] and canonical in document["model"]["items"])
    if not frontmatter_owned:
        insertions = _promotion_insertions(
            document, raw_id, canonical, path, item, history, True,
        )
    else:
        if canonical not in document["marker_blocks"]:
            _frontmatter_error(
                f"file={path} marker block 缺失", f"id={canonical}", "修正 marker 后重试",
            )
        _b_start, b_end = document["marker_blocks"][canonical]
        insertions = {b_end - 1: history} if history else {}
    _commit_mutation(
        document, model, insertions, path, spec.pool, canonical, True,
        {"id": canonical, "old_status": old_status, "new_status": new_status,
         "batch": batch, "file": os.path.relpath(path, root).replace(os.sep, "/")},
    )


def _todo_triage(args, spec, promote=True):
    root = args.root
    batch = getattr(args, "批次")

    path, document, raw_id, item = _find_item_document(root, args.id, spec.pool)
    _preflight_target_legacy_block(document, raw_id, path)
    _reject_document_mutation(document, path)
    canonical = _canonical_from_key(_legacy_semantic_id_key(raw_id))
    old_status = item["status"]
    if promote:
        open_untriaged = set(spec.status_values) - set(spec.terminal_set) - {"PROPOSED"}
        new_status = "PROPOSED" if old_status in open_untriaged else old_status
    else:
        new_status = old_status
    item["status"] = new_status
    item["batch"] = batch or None
    model = _prepare_overlay_model(document, spec.pool, canonical, item)
    eol = document["eol"]
    history = ()
    if new_status != old_status:
        history = (
            f"> {_period_str(spec)} 状态：{old_status} → {new_status}".encode("utf-8") + eol,
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
        minimal = _minimal_marker_block(canonical, item, eol, b"".join(history))
        insertions = {len(document["lines"]): (minimal,)}
    else:
        insertions = {}
    require_marker = not frontmatter_owned or canonical in document["marker_blocks"] or bool(history)
    _commit_mutation(
        document, model, insertions, path, spec.pool, canonical, require_marker,
        {"id": canonical, "old_status": old_status, "new_status": new_status,
         "batch": batch, "file": os.path.relpath(path, root).replace(os.sep, "/")},
    )


BUG_STRATEGY = PoolStrategy(
    build_block=_bug_build_block,
    header=_bug_header,
    add_required_extra=("phenomenon",),
    specific_label="优先级",
    specific_values_ordered=BUG_SPECIFIC_VALUES_ORDERED,  # [impl-review-fix] V3 单一源
    source_field="source",
    add_time_fmt="%H:%M",
    add_output=_bug_add_output,
    scan_sort_key=lambda x: (x["priority"], x["id"]),
    scan_line=_bug_scan_line,
    scan_empty_msg="（无匹配 bug）",
    set_status=_bug_set_status,
    triage=_bug_triage,
    period_flag="--date",
    period_help="覆盖日期 YYYY-MM-DD（默认今天）",
    time_help="覆盖记录时间 HH:MM（默认当前时刻）",
    add_help="新增 bug（JSON 输入，stdin 或 --json 文件）",
    set_status_help="更新 frontmatter 状态（门禁 + 追加历史）",
    scan_help="列出 bug + dual-reader/marker 一致性自检",
    scan_has_type_filter=False,
    description="自动记录/回写/扫描 buglist",
)

TODO_STRATEGY = PoolStrategy(
    build_block=_todo_build_block,
    header=_todo_header,
    add_required_extra=(),
    specific_label="类型",
    specific_values_ordered=TODO_SPECIFIC_VALUES_ORDERED,  # [impl-review-fix] V3 单一源
    source_field="project",
    add_time_fmt="%Y-%m-%d %H:%M",
    add_output=_todo_add_output,
    scan_sort_key=lambda x: (x["status"], x["id"]),
    scan_line=_todo_scan_line,
    scan_empty_msg="（无匹配 TODO）",
    set_status=_todo_set_status,
    triage=_todo_triage,
    period_flag="--month",
    period_help="覆盖月份 YYYY-MM（默认本月）",
    time_help="覆盖记录时间 YYYY-MM-DD HH:MM（默认当前时刻）",
    add_help="新增 TODO（JSON 输入，stdin 或 --json 文件）",
    set_status_help="更新 frontmatter 状态（门禁 + marker 历史留痕）",
    scan_help="列出 TODO + dual-reader/marker 一致性自检",
    scan_has_type_filter=True,
    description="自动记录/回写/扫描 todolist",
)


# ══════════════════════════════════════════════════════════════════════════════
# 共享命令 skeleton（差异经 spec + strat 注入，core 无 pool 字面分支）
# ══════════════════════════════════════════════════════════════════════════════

def cmd_next_id(args, spec, strat):
    _render_next_id(_next_id_snapshot(args, spec), spec)


def _next_id_snapshot(args, spec):
    root = args.root
    conflicts = id_conflicts(root, spec)
    try:
        value = next_id(root, args.prefix)
        error = None
    except ValueError as exc:
        value = None
        error = exc
    return conflicts, value, error


def _render_next_id(snapshot, spec):
    conflicts, value, error = snapshot
    if conflicts:
        legacy = os.path.dirname(spec.legacy_dir_glob)
        print(
            f"WARNING: 检测到跨路径 ID 冲突（新 {spec.issues_dir}/ 与旧 {legacy}/ "
            f"都存在）：{', '.join(conflicts)}——建议尽快把旧路径数据迁移到新路径",
            file=sys.stderr,
        )
    if error is not None:
        raise error
    print(value)


def cmd_add(args, spec, strat):
    root = args.root
    data = _load_json(args.json)
    required = ("module", "summary", spec.specific_field) + strat.add_required_extra
    for req in required:
        if not data.get(req):
            _die(f"缺少必填字段：{req}")
    if data[spec.specific_field] not in spec.specific_values:
        _die(f"{strat.specific_label}非法：{data[spec.specific_field]}"
             f"（应为 {'/'.join(strat.specific_values_ordered)}）")
    status = data.get("status", "OPEN")
    if status not in spec.status_values:
        _die(f"状态码非法：{status}")

    period = _period_str(spec, args.period)
    validate_prefix(args.prefix)
    snapshot = read_repository_snapshot(root)
    semantic = repository_semantic_occurrences(root, snapshot)
    explicit_id = data.get("id") is not None
    iid = canonical_id(data["id"]) if explicit_id else next_id(root, args.prefix, semantic)
    if explicit_id and semantic_id_key(iid) in semantic:
        places = semantic[semantic_id_key(iid)]
        _die(f"显式 id 与仓级既有 semantic ID 重复：{iid} at {places}")
    time_str = args.time or datetime.datetime.now().strftime(strat.add_time_fmt)
    change = data.get("change") or detect_change(root)

    _reject_line_unsafe(data.get("title"), "title")
    _reject_line_unsafe(data.get(strat.source_field), strat.source_field)

    explicit_docs = normalize_doc_paths(data.get("doc"))
    docs = explicit_docs
    if not docs:
        docs = auto_default_doc(root, change)  # 显式 doc 优先；仅在为空时才尝试自动关联
    validate_doc_paths(root, docs)

    path = ensure_file(root, spec, period)
    item = {
        "module": data["module"], "summary": data["summary"],
        spec.specific_field: data[spec.specific_field],
        "status": status, "time": time_str, "change": change or None,
        "batch": data.get("batch") or None,
    }
    block = strat.build_block(spec, iid, data, docs, explicit_docs)
    if os.path.exists(path):
        document = next(document for pool, candidate, _rel, document in snapshot
                        if pool == spec.pool and os.path.realpath(candidate) == os.path.realpath(path))
        _reject_document_mutation(document, path)
        model = dict(document["model"] or {
            "schema": 1, "pool": spec.pool, "mode": "overlay", "items": {},
        })
        model["items"] = dict(model["items"])
        model["items"][iid] = item
        body = document["body"] + block.encode("utf-8").replace(b"\n", document["eol"])
        rendered = _render_recorder_document(document, model, body)
    else:
        model = {"schema": 1, "pool": spec.pool, "mode": "canonical", "items": {iid: item}}
        body = (strat.header(spec, period, data) + block).encode("utf-8")
        rendered = _canonical_document(model, body)
    require_marker = spec.requires_block or bool(block)
    rendered = _validated_rendered_mutation(rendered, spec.pool, iid, require_marker, path)
    atomic_write_bytes(path, rendered)
    print(json.dumps(strat.add_output(iid, os.path.relpath(path, root).replace(os.sep, "/"), status, time_str, change, block),
                     ensure_ascii=False))


def _scan_snapshot(args, spec, strat):
    root = args.root
    items = []
    problems = []
    raw_id_locations = []
    snapshot = read_repository_snapshot(root)
    repository_semantic_occurrences(root, snapshot)
    for pool, path, rel, document in snapshot:
        if pool != spec.pool:
            continue
        public_rel = rel.replace(os.sep, "/")
        problems.extend(f"{public_rel}: {problem}" for problem in document["problems"])
        for bid, item in document["effective_items"].items():
            items.append({"id": bid, **item, "file": public_rel})
        raw_id_locations.extend(
            (semantic_key, raw_id, public_rel)
            for semantic_key, raw_id in document["effective_occurrences"]
        )

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
    if getattr(args, "type", None):
        items = [b for b in items if b[spec.specific_field] == args.type]
    if args.change:
        items = [b for b in items if b["change"] == args.change]
    if getattr(args, "批次", None):
        items = [b for b in items if b.get("batch") == getattr(args, "批次")]
    if args.open_ungrouped:
        nonterminal = set(spec.status_values) - set(spec.terminal_set)
        items = [b for b in items if b["status"] in nonterminal and not b.get("batch")]
    return {spec.scan_output_key: tuple(items), "problems": tuple(problems)}


def _render_scan(snapshot, args, spec, strat):
    items = snapshot[spec.scan_output_key]
    problems = snapshot["problems"]
    if args.json:
        print(json.dumps({spec.scan_output_key: list(items), "problems": list(problems)},
                         ensure_ascii=False, indent=2))
        return
    if not items:
        print(strat.scan_empty_msg)
    for b in sorted(items, key=strat.scan_sort_key):
        print(strat.scan_line(b))
    if problems:
        print("\n⚠️ 一致性问题：")
        for p in problems:
            print("  - " + p)
    else:
        print("\n✓ frontmatter/marker/legacy 关系一致")


def cmd_scan(args, spec, strat):
    _render_scan(_scan_snapshot(args, spec, strat), args, spec, strat)


def _cmd_set_status(args, spec, strat):
    strat.set_status(args, spec)


def _cmd_triage(args, spec, strat):
    strat.triage(args, spec, promote=not args.batch_only)


# ══════════════════════════════════════════════════════════════════════════════
# CLI 装配 —— 薄入口注入 spec+strat 后调 run_cli
# ══════════════════════════════════════════════════════════════════════════════

def build_parser(spec, strat):
    p = argparse.ArgumentParser(description=strat.description)
    p.add_argument("--root", default=None, help="仓库根（默认自动探测 git 根）")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("next-id", help="打印两池 snapshot 的下一个全局 ID（advisory，不预留）")
    s.add_argument("--prefix", default=spec.default_prefix)
    s.set_defaults(func=cmd_next_id)

    s = sub.add_parser("add", help=strat.add_help)
    s.add_argument("--json", help="JSON 文件路径；缺省读 stdin")
    s.add_argument("--prefix", default=spec.default_prefix)
    s.add_argument(strat.period_flag, dest="period", help=strat.period_help)
    s.add_argument("--time", help=strat.time_help)
    s.set_defaults(func=cmd_add)

    s = sub.add_parser("set-status", help=strat.set_status_help)
    s.add_argument("--id", required=True)
    s.add_argument("--to", required=True, help="目标状态码")
    s.add_argument("--evidence", help="commit hash / change 名（终态必填）")
    s.add_argument("--reason", help="WONTFIX/WONTDO 理由（必填）")
    s.add_argument(strat.period_flag, dest="period", help="覆盖 period")
    s.set_defaults(func=_cmd_set_status)

    s = sub.add_parser("triage", help="赋批次 + 未分诊开放态→PROPOSED（幂等，D7）")
    s.add_argument("--id", required=True)
    s.add_argument("--批次", dest="批次", required=True, help="批次名（清理 change 名）")
    s.add_argument("--batch-only", dest="batch_only", action="store_true",
                   help="只赋批次，跳过未分诊开放态→PROPOSED 的状态推进（供 sweep 复用）")
    s.set_defaults(func=_cmd_triage)

    s = sub.add_parser("scan", help=strat.scan_help)
    s.add_argument("--status", help="按状态码过滤")
    if strat.scan_has_type_filter:
        s.add_argument("--type", help="按类型过滤")
    s.add_argument("--change", help="按关联 change（来源）过滤")
    s.add_argument("--批次", dest="批次", help="按批次过滤")
    s.add_argument("--open-ungrouped", dest="open_ungrouped", action="store_true",
                    help="非终态且未分批的项")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_scan)
    return p


def run_cli(spec, strat, argv=None):
    p = build_parser(spec, strat)
    args = p.parse_args(argv)
    try:
        if hasattr(args, "prefix"):
            validate_prefix(args.prefix)
        args.root = repo_root(args.root)
        if args.cmd in {"scan", "next-id"}:
            with recorder_lock(args.root, args.cmd):
                snapshot = _scan_snapshot(args, spec, strat) if args.cmd == "scan" else _next_id_snapshot(args, spec)
            if args.cmd == "scan":
                _render_scan(snapshot, args, spec, strat)
            else:
                _render_next_id(snapshot, spec)
        else:
            output = io.StringIO()
            with recorder_lock(args.root, args.cmd), redirect_stdout(output):
                args.func(args, spec, strat)
            sys.stdout.write(output.getvalue())
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None
