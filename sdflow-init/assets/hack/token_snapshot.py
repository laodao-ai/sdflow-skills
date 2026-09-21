#!/usr/bin/env python3
"""token_snapshot.py — checkpoint 级 token 快照采集 helper。

由 `checkpoint-commit.sh` 在「本次确定要提交」的时机（判空 gate 之后、`git add -A` 之前）
同步调用：`python3 ~/.sdflow/hack/token_snapshot.py --step "$step" || true`。

契约（design.md §Decisions D1 / specs/token-snapshot-anchor/spec.md）：
- 宿主判定〔implement-workflow-optimization-2026-08-p2 Task 5〕：`detect_host()` 与
  `outside-voice-job.py` 同口径（`CLAUDECODE=1` → claude；`CODEX_THREAD_ID` 非空 → codex；
  两者同时出现 = 冲突 → unknown；均缺席 → unknown）。**非 claude 宿主（codex/unknown）
  MUST NOT 走 `~/.claude/projects/` 的 mtime 回退扫描**——直接落 `no-transcript` 降级行，
  不做任何目录 I/O（该目录本就不属于非 Claude 宿主，扫描它既无意义也是多余的信任假设）。
  `host` 字段如实写检测值（此前恒为 `"claude"` 的写法在多宿主场景下失实，随本次一并修正）。
- transcript 定位序（仅 claude 宿主）：`$CLAUDE_CODE_SESSION_ID`（session-id 先过文法校验才拼路径）
  精确命中 `~/.claude/projects/<munged-cwd>/<id>.jsonl` → 同目录 mtime 最新 jsonl 回退 → 无则
  `no-transcript` 降级行。munged-cwd = `os.getcwd()` 的 `/` → `-` 全量替换。
- usage 四计数（input / output / cache_read / cache_creation）+ messages 数为 session 累计值
  （逐 assistant message 的 `message.usage` 累加），MUST 校验非负整数，不过判 `parse-error`。
- change 目录由当前分支名 `feat/<change>` 解析，`openspec/changes/<change>/` 不存在则静默跳过
  （零写入，不落任何降级行——「无落点」与「有落点但采集失败」是两种不同状态）。
- 输出行字段封闭 schema（v1）：只写本文件 `_build_line` 组装的字段，MUST NOT 透传 transcript
  的对话内容 / 工具输入输出等任何其他内容。
- 追加写：整行 JSON 序列化后一次性 `O_APPEND` write（POSIX 本地文件系统单 write 原子）。
- 内部自设执行超时（10s，超时即放弃采集，等价于 parse-error 降级）——`|| true` 只防非零退出、
  防不住挂起，checkpoint 是同步调用链，一次 hang 会拖死整条编排流水线。
- 全程 try/except 到降级行；写侧失败（如落点不可写）静默吞掉，不得让 checkpoint 感知。

MUST NOT 直接改 `~/.sdflow/hack/` 里的部署副本——真相源固定在
`sdflow-init/assets/hack/token_snapshot.py`，经 `setup.sh` 分发。
"""
import sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

import argparse
import json
import os
import re
import signal
import subprocess
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
SCHEMA_VERSION_V2 = 2
TIMEOUT_SECONDS = 10
GIT_SUBPROCESS_TIMEOUT_SECONDS = 5
SESSION_ID_RE = re.compile(r"^[0-9a-fA-F-]+$")
UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
HOST_CLAUDE = "claude"
HOST_CODEX = "codex"
HOST_UNKNOWN = "unknown"
MAX_CODEX_DEPTH = 8

# v2 行封闭字段清单（design.md §数据模型；kind=root/child 用，kind=cli 不在本 change 范围）。
CODEX_LINE_KEYS = frozenset({
    "v", "ts", "step", "host", "runner", "kind", "session", "parent", "role",
    "depth", "model", "effort", "config_mixed", "cli_version", "usage_source",
    "branch_at_start", "usage", "turns", "duration_ms", "anchor", "reason",
})

# Codex TokenUsage 六计数：输出字段名 -> rollout 原始字段名（codex-rs protocol.rs 实查）。
_USAGE_KEY_MAP = {
    "input": "input_tokens",
    "cached_input": "cached_input_tokens",
    "cache_write_input": "cache_write_input_tokens",
    "output": "output_tokens",
    "reasoning_output": "reasoning_output_tokens",
    "total": "total_tokens",
}

# 逐行子串预筛——只有含这些标记之一的行才值得 json.loads（design.md 非功能需求）。
_CODEX_LINE_MARKERS = (
    "session_meta", "turn_context", "task_started", "task_complete",
    "token_usage_record", "token_count", "item_completed",
)

_ISO_TS_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?Z?$"
)


def detect_host(env=None):
    """→ "claude" | "codex" | "unknown"——与 `outside-voice-job.py:detect_host()` 同口径。

    正信号判定，MUST NOT「缺失即另一方」推断；两个信号同时出现 = 冲突，落 unknown
    （MUST NOT 静默取其一）。判不出一律 unknown，non-claude 宿主一律不碰
    `~/.claude/projects/`（见模块 docstring）。
    """
    env = os.environ if env is None else env
    claude_sig = env.get("CLAUDECODE") == "1"
    codex_sig = bool(env.get("CODEX_THREAD_ID"))
    if claude_sig and codex_sig:
        return HOST_UNKNOWN
    if claude_sig:
        return HOST_CLAUDE
    if codex_sig:
        return HOST_CODEX
    return HOST_UNKNOWN


class _Timeout(Exception):
    """内部 SIGALRM 超时信号的哨兵异常（POSIX only）。"""


def _install_timeout(seconds):
    """POSIX 上装一个 SIGALRM 硬超时；Windows 无 SIGALRM，静默降级为无硬超时。

    该降级是已记录的边角（Windows 上 checkpoint-commit.sh 本身也不在铺设范围内，
    见仓库 CLAUDE.md「Windows 不铺 hack/」），MUST NOT 为它手搓跨平台信号模拟。
    """
    if not hasattr(signal, "SIGALRM"):
        return None

    def _handler(signum, frame):
        raise _Timeout()

    old = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    return old


def _cancel_timeout(old):
    if not hasattr(signal, "SIGALRM"):
        return
    signal.alarm(0)
    if old is not None:
        signal.signal(signal.SIGALRM, old)


def _munge_cwd(cwd):
    """`os.getcwd()` 的 `/` → `-` 全量替换（含开头的 `/`），对齐宿主 `~/.claude/projects/` 布局。"""
    return cwd.replace("/", "-")


def _valid_session_id(session_id):
    """basename 且匹配 `^[0-9a-fA-F-]+$` 才允许拼路径——防路径拼接逃逸（如 `../../etc`）。"""
    if not session_id:
        return False
    if session_id != os.path.basename(session_id):
        return False
    return bool(SESSION_ID_RE.match(session_id))


def _locate_transcript(projects_dir):
    """返回 `(path, reason)`；成功时 `reason=None`，找不到时 `path=None, reason="no-transcript"`。"""
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if _valid_session_id(session_id):
        candidate = projects_dir / f"{session_id}.jsonl"
        if candidate.is_file():
            return candidate, None
    if projects_dir.is_dir():
        candidates = sorted(
            (p for p in projects_dir.iterdir() if p.is_file() and p.suffix == ".jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if candidates:
            return candidates[0], None
    return None, "no-transcript"


def _git_output(cwd, *args):
    """跑一次 git 子命令，成功返回 stripped stdout，任何失败（非零退出/超时/异常）返回 None。"""
    try:
        r = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True,
            timeout=GIT_SUBPROCESS_TIMEOUT_SECONDS, encoding="utf-8", errors="replace",
        )
    except Exception:
        return None
    if r.returncode != 0:
        return None
    return r.stdout.strip()


def _resolve_change_dir(cwd):
    """从当前分支名 `feat/<change>` 解析 change 目录；解析不出或目录不存在 → None（静默跳过）。

    分支名用 `symbolic-ref --short HEAD`（非 `rev-parse --abbrev-ref HEAD`）——后者在**零提交**
    的 unborn 分支上会打印 `HEAD` 到 stdout 的同时仍以非零退出（"ambiguous argument 'HEAD'"），
    前者对 unborn 分支返回正确的分支名且退出码为 0；detached HEAD 下两者都以非零退出，
    语义一致（不是分支 ⇒ 无落点）。
    """
    branch = _git_output(cwd, "symbolic-ref", "--short", "HEAD")
    if not branch or not branch.startswith("feat/"):
        return None
    change = branch[len("feat/"):]
    if not change:
        return None
    toplevel = _git_output(cwd, "rev-parse", "--show-toplevel")
    if not toplevel:
        return None
    change_dir = Path(toplevel) / "openspec" / "changes" / change
    if not change_dir.is_dir():
        return None
    return change_dir


def _non_negative_int(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    return None


def _accumulate_usage(path):
    """逐行解析 transcript，累加 assistant message 的 usage 四计数与 message 数。

    任一行 JSON 语法损坏，或 usage 计数校验不过（非非负整数）⇒ 整体判 parse-error（返回 None）
    ——宁缺毋假，MUST NOT 在部分损坏时仍产出一个「看起来正常」但被低估的累计值。
    非 assistant / 无 usage 字段的行是transcript 的正常组成部分，非损坏，照常跳过不计数。
    """
    totals = {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0, "messages": 0}
    try:
        with open(path, "r", encoding="utf-8", errors="strict") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    return None
                if not isinstance(obj, dict):
                    continue
                msg = obj.get("message")
                if not isinstance(msg, dict):
                    continue
                if msg.get("role") != "assistant":
                    continue
                usage = msg.get("usage")
                if not isinstance(usage, dict):
                    continue
                inp = _non_negative_int(usage.get("input_tokens", 0))
                out = _non_negative_int(usage.get("output_tokens", 0))
                cr = _non_negative_int(usage.get("cache_read_input_tokens", 0))
                cc = _non_negative_int(usage.get("cache_creation_input_tokens", 0))
                if None in (inp, out, cr, cc):
                    return None
                totals["input"] += inp
                totals["output"] += out
                totals["cache_read"] += cr
                totals["cache_creation"] += cc
                totals["messages"] += 1
    except Exception:
        return None
    return totals


def _build_line(step, session_id, anchor, reason, usage, host):
    """封闭 schema：只这些字段，MUST NOT 透传任何 transcript 原始内容。"""
    line = {
        "v": SCHEMA_VERSION,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "step": step,
        "session": session_id or "",
        "host": host,
        "anchor": bool(anchor),
        "reason": reason,
    }
    if usage is not None:
        line["usage"] = usage
    return line


def _append_line(path, obj):
    """整行 buffer 后单次 `O_APPEND` write（POSIX 本地文件系统单 write 原子）。"""
    payload = (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")
    fd = os.open(str(path), os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    try:
        os.write(fd, payload)
    finally:
        os.close(fd)


def _collect(step):
    """判定宿主 → （仅 claude 宿主）定位 transcript → 累加 usage → 组装一行。
    全程不 raise（内部已 try/except 到降级行）；唯一允许上抛的是 `_Timeout`
    （由外层的 SIGALRM handler 触发，代表已超出执行时限）。

    非 claude 宿主（codex/unknown）直接落 `no-transcript` 降级行，MUST NOT 触碰
    `~/.claude/projects/`——那个目录语义上不属于非 Claude 宿主，扫描它既拿不到
    真实数据也是多余的信任假设。
    """
    host = detect_host()
    if host != HOST_CLAUDE:
        return _build_line(step, "", False, "no-transcript", None, host)

    cwd = os.getcwd()
    munged = _munge_cwd(cwd)
    projects_dir = Path(os.path.expanduser("~")) / ".claude" / "projects" / munged
    transcript, reason = _locate_transcript(projects_dir)

    if transcript is None:
        env_session = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
        session_for_line = env_session if _valid_session_id(env_session) else ""
        return _build_line(step, session_for_line, False, reason, None, host)

    session_for_line = transcript.stem
    usage = _accumulate_usage(transcript)
    if usage is None:
        return _build_line(step, session_for_line, False, "parse-error", None, host)
    return _build_line(step, session_for_line, True, "ok", usage, host)


def _valid_uuid(value):
    """标准 UUID 文法（8-4-4-4-12 十六进制）——先过此关才允许拼路径 / 递归入队。"""
    return isinstance(value, str) and bool(UUID_RE.match(value))


def _parse_iso_ts(value):
    """rollout 行顶层 `timestamp`（ISO8601，含毫秒，`Z` 结尾）→ 毫秒 epoch；解析不出返回 None。"""
    if not isinstance(value, str):
        return None
    m = _ISO_TS_RE.match(value)
    if not m:
        return None
    y, mo, d, h, mi, s, frac = m.groups()
    try:
        dt = datetime(int(y), int(mo), int(d), int(h), int(mi), int(s), tzinfo=timezone.utc)
    except Exception:
        return None
    ms = int(dt.timestamp() * 1000)
    if frac:
        ms += int(round(float("0." + frac) * 1000))
    return ms


def _codex_sessions_root(env=None):
    """`$CODEX_HOME/sessions`（非空时）否则 `~/.codex/sessions`（design.md §安全与数据保护）。"""
    env = os.environ if env is None else env
    codex_home = env.get("CODEX_HOME")
    base = Path(codex_home) if codex_home else Path(os.path.expanduser("~")) / ".codex"
    return base / "sessions"


def _locate_codex_rollout(sessions_root, thread_id):
    """精确 glob `rollout-*-<thread_id>.jsonl`；0/多命中或 symlink 逃逸 sessions 根 → `None`。

    `thread_id` 调用方必须已过 `_valid_uuid` 校验——本函数不再重复校验（防路径拼接逃逸的
    唯一关口是调用方，见 TSA-05）。
    """
    try:
        if not sessions_root.is_dir():
            return None
        root_resolved = sessions_root.resolve()
        matches = sorted(sessions_root.glob(f"**/rollout-*-{thread_id}.jsonl"))
    except Exception:
        return None
    if len(matches) != 1:
        return None
    try:
        resolved = matches[0].resolve()
        resolved.relative_to(root_resolved)
    except (Exception, ValueError):
        return None
    if not resolved.is_file():
        return None
    return resolved


def _extract_usage(raw):
    """Codex 六计数原始字典 → 输出六键；来源缺键为 `None`（不派生），值非法（负数/布尔）抛出。

    调用方捕获抛出的异常并整体降级该线程为 `parse-error`——单个非法计数不能产出一个
    "看起来正常但被低估"的 usage（与 v1 `_accumulate_usage` 同一纪律）。
    """
    if not isinstance(raw, dict):
        return None
    out = {}
    for out_key, raw_key in _USAGE_KEY_MAP.items():
        if raw_key not in raw:
            out[out_key] = None
            continue
        v = _non_negative_int(raw[raw_key])
        if v is None:
            raise ValueError(f"invalid usage count: {raw_key}")
        out[out_key] = v
    return out


def _project_codex_rollout(path, own_id):
    """逐行流式投影单个 rollout 文件；返回字段字典，`parse_error=True` 表示该线程整体降级。

    `_Timeout` 原样上抛（由外层 SIGALRM handler 触发）；其余任何异常在本函数内吞掉、
    转译为 `parse_error=True`——与 v1 `_accumulate_usage` 同一「宁缺毋假」纪律。
    """
    result = {
        "parse_error": False, "session_meta_seen": False,
        "parent": None, "role": None, "depth": 0,
        "cli_version": None, "branch_at_start": None,
        "model": None, "effort": None, "config_mixed": False,
        "turns": 0, "duration_ms": None,
        "usage": None, "usage_source": None, "children": [],
    }
    task_started_ts = {}
    duration_sum = 0
    duration_any = False
    seen_children = set()
    last_model = None
    last_effort = None
    model_set = False
    effort_set = False
    try:
        with open(path, "r", encoding="utf-8", errors="strict") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or not any(marker in line for marker in _CODEX_LINE_MARKERS):
                    continue
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    continue
                rtype = obj.get("type")
                payload = obj.get("payload")

                if rtype == "session_meta":
                    if not isinstance(payload, dict) or payload.get("id") != own_id:
                        raise ValueError("session_meta identity mismatch or malformed")
                    result["session_meta_seen"] = True
                    result["parent"] = payload.get("parent_thread_id")
                    role = payload.get("agent_path")
                    depth = 0
                    source = payload.get("source")
                    if isinstance(source, dict):
                        spawn = source.get("subagent", {})
                        spawn = spawn.get("thread_spawn", {}) if isinstance(spawn, dict) else {}
                        if isinstance(spawn, dict):
                            d = spawn.get("depth")
                            if isinstance(d, int) and not isinstance(d, bool) and d >= 0:
                                depth = d
                            if role is None:
                                role = spawn.get("agent_path")
                    result["role"] = role
                    result["depth"] = depth
                    result["cli_version"] = payload.get("cli_version")
                    git = payload.get("git")
                    if isinstance(git, dict):
                        result["branch_at_start"] = git.get("branch")

                elif rtype == "turn_context":
                    if not isinstance(payload, dict):
                        raise ValueError("turn_context malformed")
                    m = payload.get("model")
                    e = payload.get("effort")
                    if (model_set and m != last_model) or (effort_set and e != last_effort):
                        result["config_mixed"] = True
                    last_model, last_effort = m, e
                    model_set = effort_set = True

                elif rtype == "event_msg":
                    if not isinstance(payload, dict):
                        raise ValueError("event_msg malformed")
                    etype = payload.get("type")
                    if etype == "task_started":
                        turn_id = payload.get("turn_id")
                        ts = _parse_iso_ts(obj.get("timestamp"))
                        if turn_id is not None and ts is not None:
                            task_started_ts[turn_id] = ts
                    elif etype == "task_complete":
                        result["turns"] += 1
                        turn_id = payload.get("turn_id")
                        ts = _parse_iso_ts(obj.get("timestamp"))
                        start_ts = task_started_ts.pop(turn_id, None) if turn_id is not None else None
                        if ts is not None and start_ts is not None and ts >= start_ts:
                            duration_sum += ts - start_ts
                            duration_any = True
                    elif etype == "item_completed":
                        item = payload.get("item")
                        if (isinstance(item, dict) and item.get("type") == "SubAgentActivity"
                                and item.get("kind") == "started"):
                            cid = item.get("agent_thread_id")
                            if _valid_uuid(cid) and cid not in seen_children:
                                seen_children.add(cid)
                                result["children"].append(cid)
                    elif etype == "token_count":
                        info = payload.get("info")
                        if isinstance(info, dict):
                            usage = _extract_usage(info.get("total_token_usage"))
                            if usage is not None:
                                result["usage"] = usage
                                result["usage_source"] = "token_count"

                elif rtype == "token_usage_record":
                    if not isinstance(payload, dict):
                        raise ValueError("token_usage_record malformed")
                    if payload.get("thread_id") == own_id:
                        usage = _extract_usage(payload.get("thread_token_usage"))
                        if usage is not None:
                            result["usage"] = usage
                            result["usage_source"] = "token_usage_record"
    except _Timeout:
        raise
    except Exception:
        result["parse_error"] = True
        return result

    result["model"] = last_model
    result["effort"] = last_effort
    if duration_any:
        result["duration_ms"] = duration_sum
    if not result["session_meta_seen"]:
        result["parse_error"] = True
    return result


def _build_codex_line(step, kind, session, reason, projected=None, host=HOST_CODEX, runner=HOST_CODEX):
    """v2 封闭 schema（design.md §数据模型）。字段值来自 `projected`（缺失即 `None`，MUST NOT 派生）。

    `host`/`runner` 默认 codex/codex（root/child 调用点不传，行为不变）；`kind=cli` 调用点显式传入
    `host=detect_host()`（实际编排宿主）、`runner=HOST_CODEX`（TSA-04/HAE-02：cli 行记录的是
    「哪个宿主经 outside-voice 调用了 Codex」，不是「本进程判定的宿主」）。
    """
    p = projected or {}
    return {
        "v": SCHEMA_VERSION_V2,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "step": step,
        "host": host,
        "runner": runner,
        "kind": kind,
        "session": session or "",
        "parent": p.get("parent"),
        "role": p.get("role"),
        "depth": p.get("depth", 0),
        "model": p.get("model"),
        "effort": p.get("effort"),
        "config_mixed": bool(p.get("config_mixed", False)),
        "cli_version": p.get("cli_version"),
        "usage_source": p.get("usage_source"),
        "branch_at_start": p.get("branch_at_start"),
        "usage": p.get("usage"),
        "turns": p.get("turns", 0),
        "duration_ms": p.get("duration_ms"),
        "anchor": reason == "ok",
        "reason": reason,
    }


def _finalize_codex_line(step, kind, tid, projected):
    if projected.get("parse_error"):
        reason = "parse-error"
    elif projected.get("usage") is None:
        reason = "no-usage-events"
    else:
        reason = "ok"
    return _build_codex_line(step, kind, tid, reason, projected=projected)


# ── outside-voice `--cli-usage` 子入口（design.md TSA-04 / spec-review-amendment D4/D13）──
STEP_CLI_USAGE = "outside-voice"
ROLE_CLI_USAGE = "outside-voice"
_CLI_USAGE_LINE_MARKERS = ("thread.started", "turn.completed", "turn.failed")


def _project_cli_usage(jsonl_path):
    """逐行解析 `codex exec --json` 的 stdout（outside-voice cli.log）。

    非 JSON 行 / 非对象一律跳过（TSA-04：「非 JSON 行跳过」，不是失败）。`thread.started.thread_id`
    取首次出现的值作为 `session`。`turn.completed` / `turn.failed` 的 `usage` 视为该 turn 的累计值，
    同 R5 纪律取末条不求和；出现非法计数（负数/布尔）⇒ 整体降级（返回 `None`），与 rollout 投影同一
    「宁缺毋假」纪律。返回 `None` 时调用方落 `reason=parse-error`（无独立的 `no-usage-events`——
    outside-voice 只是一次性调用，没有 usage 就是没有可用信号，见 design.md 失败模式表）。
    """
    session = None
    usage = None
    turns = 0
    try:
        with open(jsonl_path, "r", encoding="utf-8", errors="strict") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or not any(m in line for m in _CLI_USAGE_LINE_MARKERS):
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue  # 非 JSON 行跳过——TSA-04 明文契约，不是失败
                if not isinstance(obj, dict):
                    continue
                etype = obj.get("type")
                if etype == "thread.started":
                    if session is None:
                        tid = obj.get("thread_id")
                        if isinstance(tid, str) and tid:
                            session = tid
                elif etype in ("turn.completed", "turn.failed"):
                    turns += 1
                    u = _extract_usage(obj.get("usage"))
                    if u is not None:
                        usage = u
    except Exception:
        return None
    if session is None or usage is None:
        return None
    return {"session": session, "usage": usage, "turns": turns}


def _build_cli_usage_line(jsonl_path):
    """组装一行 `kind=cli`；`host` 为本进程判定的实际宿主（TSA-04：「Claude 宿主经 outside-voice
    调 Codex」场景 `host=claude runner=codex`），失败一律降级为 `anchor=false reason=parse-error`。
    """
    host = detect_host()
    try:
        projected = _project_cli_usage(jsonl_path)
    except Exception:
        projected = None
    if projected is None:
        return _build_codex_line(STEP_CLI_USAGE, "cli", "", "parse-error",
                                  projected={"role": ROLE_CLI_USAGE}, host=host, runner=HOST_CODEX)
    return _build_codex_line(
        STEP_CLI_USAGE, "cli", projected["session"], "ok",
        projected={
            "role": ROLE_CLI_USAGE,
            "usage": projected["usage"],
            "usage_source": "cli",
            "turns": projected["turns"],
        },
        host=host, runner=HOST_CODEX,
    )


def _cli_usage_entry(jsonl_path):
    """`--cli-usage <jsonl>` 子入口：无活动 change 落点则静默跳过（零写入），
    否则组装一行并 append。全程不 raise——与 `--step` 路径同一「MUST NOT 让调用方感知失败」契约。
    """
    change_dir = _resolve_change_dir(os.getcwd())
    if change_dir is None:
        return 0

    old_handler = _install_timeout(TIMEOUT_SECONDS)
    try:
        line = _build_cli_usage_line(jsonl_path)
    except _Timeout:
        line = _build_codex_line(STEP_CLI_USAGE, "cli", "", "parse-error",
                                  projected={"role": ROLE_CLI_USAGE}, host=detect_host(), runner=HOST_CODEX)
    except Exception:
        line = _build_codex_line(STEP_CLI_USAGE, "cli", "", "parse-error",
                                  projected={"role": ROLE_CLI_USAGE}, host=detect_host(), runner=HOST_CODEX)
    finally:
        _cancel_timeout(old_handler)

    try:
        _append_line(change_dir / "token-log.jsonl", line)
    except Exception:
        pass
    return 0


def _codex_collect_and_write(step, token_log_path):
    """codex 宿主：根线程定位 → BFS 枚举子线程 → 逐线程投影，组装完即 append。

    全程不 raise（内部吞掉一切异常，含 `_Timeout`）——与 v1 `_collect` 同一契约，main() 的
    Claude/unknown 路径完全不感知本函数存在。10 秒总 deadline 由外层 SIGALRM 覆盖；命中时
    已 append 的行保留，尚未处理（含正在处理）的线程各写一行 `reason=timeout`。
    """
    def _write(obj):
        try:
            _append_line(token_log_path, obj)
        except Exception:
            pass

    try:
        thread_id_env = os.environ.get("CODEX_THREAD_ID", "")
        if not _valid_uuid(thread_id_env):
            _write(_build_codex_line(step, "root", "", "invalid-thread-id"))
            return

        sessions_root = _codex_sessions_root()
        queue = deque([{"id": thread_id_env, "kind": "root", "depth": 0}])
        visited = set()

        while queue:
            item = queue.popleft()
            tid = item["id"]
            if tid in visited:
                continue
            visited.add(tid)

            if item["depth"] > MAX_CODEX_DEPTH:
                _write(_build_codex_line(step, item["kind"], tid, "depth-exceeded",
                                          projected={"depth": item["depth"]}))
                continue

            try:
                rollout_path = _locate_codex_rollout(sessions_root, tid)
                if rollout_path is None:
                    _write(_build_codex_line(step, item["kind"], tid, "thread-not-found"))
                    continue
                projected = _project_codex_rollout(rollout_path, tid)
            except _Timeout:
                _write(_build_codex_line(step, item["kind"], tid, "timeout"))
                while queue:
                    rest = queue.popleft()
                    _write(_build_codex_line(step, rest["kind"], rest["id"], "timeout"))
                return

            _write(_finalize_codex_line(step, item["kind"], tid, projected))

            if not projected.get("parse_error"):
                for child_id in projected.get("children", []):
                    if child_id not in visited:
                        queue.append({"id": child_id, "kind": "child", "depth": item["depth"] + 1})
    except _Timeout:
        _write(_build_codex_line(step, "root", "", "timeout"))
    except Exception:
        _write(_build_codex_line(step, "root", "", "parse-error"))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="token_snapshot.py")
    parser.add_argument("--step")
    parser.add_argument("--cli-usage", metavar="JSONL_PATH",
                         help="outside-voice 子入口：解析 codex exec --json 的 stdout 写一行 kind=cli")
    args = parser.parse_args(argv)

    if args.cli_usage:
        # 与 --step 路径互斥、自成一体：无 --step 概念，落点仍是当前 cwd 解析出的活动 change。
        return _cli_usage_entry(args.cli_usage)
    if not args.step:
        parser.error("--step is required unless --cli-usage is given")

    change_dir = _resolve_change_dir(os.getcwd())
    if change_dir is None:
        return 0  # 无落点，静默跳过——不写任何文件、不写任何降级行

    if detect_host() == HOST_CODEX:
        # codex 分支自成一体：自己的 SIGALRM 窗口、自己的逐线程 append，完全不碰
        # 下面 claude/unknown 路径的既有代码（--step 接口与该路径行为逐字节不变）。
        old_handler = _install_timeout(TIMEOUT_SECONDS)
        try:
            _codex_collect_and_write(args.step, change_dir / "token-log.jsonl")
        finally:
            _cancel_timeout(old_handler)
        return 0

    old_handler = _install_timeout(TIMEOUT_SECONDS)
    try:
        line = _collect(args.step)
    except _Timeout:
        line = _build_line(args.step, "", False, "parse-error", None, detect_host())
    except Exception:
        line = _build_line(args.step, "", False, "parse-error", None, detect_host())
    finally:
        _cancel_timeout(old_handler)

    try:
        _append_line(change_dir / "token-log.jsonl", line)
    except Exception:
        pass  # 写侧失败静默吞掉——MUST NOT 让 checkpoint 感知采集失败
    return 0


if __name__ == "__main__":
    sys.exit(main())
