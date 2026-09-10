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
from pathlib import Path

SCHEMA_VERSION = 1
TIMEOUT_SECONDS = 10
GIT_SUBPROCESS_TIMEOUT_SECONDS = 5
SESSION_ID_RE = re.compile(r"^[0-9a-fA-F-]+$")
HOST_CLAUDE = "claude"
HOST_CODEX = "codex"
HOST_UNKNOWN = "unknown"


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


def main(argv=None):
    parser = argparse.ArgumentParser(prog="token_snapshot.py")
    parser.add_argument("--step", required=True)
    args = parser.parse_args(argv)

    change_dir = _resolve_change_dir(os.getcwd())
    if change_dir is None:
        return 0  # 无落点，静默跳过——不写任何文件、不写任何降级行

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
