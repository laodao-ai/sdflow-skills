"""outside-voice-job.py 的契约测试
（preflight / reserve / dispatch / worker / status / await / collect / cleanup / reconcile）。

TDD 接缝（先定后写）——两处公共边界，测试只打这两处，不打内部实现：

  ① **子命令 CLI 契约**：`preflight` / `dispatch` / `worker` 的 argv、stdout 上的
     单行 JSON（`ok` / `reason_code` / `state` / `fallback_allowed` / `job_id` …）、
     退出码与 stderr 上的 actionable 提示。
  ② **sidecar 文件契约**：`<site>.reserve` / `<site>.job.json` / `<site>.started.json` /
     `<site>.terminal.json` / `<site>.stdout` / `<site>.stderr` / `<site>.rc` 的
     存在时序、原子发布、权限与字段。

单测一律用 **fake `claude` 可执行** 与 **fake `outside-voice.sh` 替身**，MUST NOT 真调模型。
唯一一条真机集成用例（跨 shell 存活）在文件末尾，缺 `claude` / 版本不足时 skip 并给出理由。
"""

import hashlib
import importlib.util
import itertools
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import textwrap
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
ASSETS = REPO / "sdflow-init" / "assets" / "hack"
JOB_PY = ASSETS / "outside-voice-job.py"
HELPER_SH = ASSETS / "outside-voice.sh"
PRINCIPLES = ASSETS / "skill-principles.md"

_SPEC = importlib.util.spec_from_file_location("sdflow_outside_voice_job", JOB_PY)
JOB = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(JOB)


# ── fake claude ────────────────────────────────────────────────────────────────
# 一个可配置的 `claude` 替身：记录每次 argv、按环境变量决定 --version / agents /
# --bg --exec 三条路径的行为。所有测试对「外部副作用是否发生」的判定都落在它的
# 调用日志上（而不是模型的自述），故它是本文件的机械锚底座。
FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json, os, subprocess, sys, time, uuid

argv = sys.argv[1:]
log = os.environ.get("FAKE_CLAUDE_LOG")
if log:
    entry = {"argv": argv}
    snap = os.environ.get("FAKE_CLAUDE_SNAPSHOT_DIR")
    if snap and os.path.isdir(snap):
        entry["entries"] = sorted(os.listdir(snap))
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")

state_path = os.environ.get("FAKE_CLAUDE_STATE", "")


def load_state():
    try:
        with open(state_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


if argv[:1] == ["--version"]:
    sys.stdout.write(os.environ.get("FAKE_CLAUDE_VERSION", "2.1.220 (Claude Code)") + "\n")
    sys.exit(0)

if argv[:1] == ["agents"]:
    mode = os.environ.get("FAKE_CLAUDE_AGENTS_MODE", "from-state")
    if mode == "disabled":
        sys.stderr.write("agent view is disabled by policy (disableAgentView)\n")
        sys.exit(1)
    if mode == "notjson":
        sys.stdout.write("not json at all\n")
        sys.exit(0)
    if mode == "notlist":
        sys.stdout.write('{"sessions": []}\n')
        sys.exit(0)
    if mode == "empty":
        sys.stdout.write("[]\n")
        sys.exit(0)
    if mode == "fixed":
        # Task 2：由测试直接给定整份 roster JSON（liveness 维度的注入点）。
        sys.stdout.write(os.environ.get("FAKE_CLAUDE_FIXED", "[]") + "\n")
        sys.exit(0)
    st = load_state()
    if not st:
        sys.stdout.write("[]\n")
        sys.exit(0)
    base = {
        "id": st["id"],
        "cwd": st.get("cwd", os.getcwd()),
        "kind": "background",
        "startedAt": 1784974140034,
        "sessionId": st["id"] + "-f13f-4c83-9bda-92067348905b",
        "state": "working",
        "name": st["command"],
    }
    if mode == "done-noname":
        # 真 CLI 实测约束：kind=background 且 state=done 的条目**没有 name 字段**
        # （极快失败的 worker 会走到这里）⇒ 只认 name 的核验会扑空。
        base.pop("name", None)
        base["state"] = "done"
        sys.stdout.write(json.dumps([base]) + "\n")
        sys.exit(0)
    if mode == "nomatch":
        # 「本次 attempt 没有产生任何 job」⇒ name 与 id 两条通道都必须不命中
        # （id 也要换掉：dispatch 自己 stdout 里的 short id 是并列匹配通道）。
        base["name"] = "some unrelated background command"
        base["id"] = "0000dead"
        sys.stdout.write(json.dumps([base]) + "\n")
        sys.exit(0)
    if mode == "duplicate":
        second = dict(base)
        second["id"] = "dead" + st["id"][4:]
        second["sessionId"] = second["id"] + "-0000-0000-0000-000000000000"
        sys.stdout.write(json.dumps([base, second]) + "\n")
        sys.exit(0)
    sys.stdout.write(json.dumps([base]) + "\n")
    sys.exit(0)

if argv[:1] in (["stop"], ["rm"]):
    # Task 3：破坏性子命令替身。目标 id 一律进调用日志 ⇒ 「有没有对某个 id 动过手」
    # 是日志上的机械事实，而不是实现自述。
    action = argv[0]
    mode = os.environ.get("FAKE_CLAUDE_%s_MODE" % action.upper(), "ok")
    if mode == "fail":
        sys.stderr.write("%s failed: supervisor unreachable\n" % action)
        sys.exit(1)
    if action == "stop":
        victim = os.environ.get("FAKE_CLAUDE_STOP_KILLS_PID", "")
        if victim:
            try:
                os.kill(int(victim), 9)
            except Exception:
                pass
    sys.stdout.write("%s %s ok\n" % (action, argv[1] if len(argv) > 1 else ""))
    sys.exit(0)

if "--bg" in argv:
    command = argv[argv.index("--exec") + 1] if "--exec" in argv else ""
    mode = os.environ.get("FAKE_CLAUDE_BG_MODE", "ok")
    job_id = os.environ.get("FAKE_CLAUDE_JOB_ID", uuid.uuid4().hex[:8])
    if mode == "fail":
        sys.stderr.write("dispatch refused\n")
        sys.exit(1)
    if os.environ.get("FAKE_CLAUDE_BG_WRITE_STATE", "1") == "1" and state_path:
        payload = json.dumps({"id": job_id, "command": command, "cwd": os.getcwd()})
        # supervisor 注册滞后：job 已被接受（已计费），但要过 D 秒才进 agents roster。
        # 用独立 session 的 detached 进程写，才能在 dispatch 回收 spawn 进程树之后仍然发生。
        delay = float(os.environ.get("FAKE_CLAUDE_BG_STATE_DELAY", "0") or 0)
        if delay > 0:
            subprocess.Popen(
                [sys.executable, "-c",
                 "import sys,time;time.sleep(float(sys.argv[1]));"
                 "open(sys.argv[2],'w',encoding='utf-8').write(sys.argv[3])",
                 str(delay), state_path, payload],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, start_new_session=True)
        else:
            with open(state_path, "w", encoding="utf-8") as fh:
                fh.write(payload)
    if mode == "hang":
        if os.environ.get("FAKE_CLAUDE_HANG_CHILD", "1") == "1":
            child = subprocess.Popen(["sleep", "60"])
            pid_file = os.environ.get("FAKE_CLAUDE_PID_FILE")
            if pid_file:
                with open(pid_file, "w", encoding="utf-8") as fh:
                    json.dump({"self": os.getpid(), "child": child.pid}, fh)
        time.sleep(60)
        sys.exit(0)
    if mode == "run":
        subprocess.Popen(command, shell=True, start_new_session=True)
    sys.stdout.write("Starting background service…\n")
    # `backgrounded · <id> · <cmd>` 是 research preview 格式；FAKE_CLAUDE_BG_HINT_ID
    # 用来模拟它漂移成一个与 canonical id 不同的值。
    hint_id = os.environ.get("FAKE_CLAUDE_BG_HINT_ID") or job_id
    sys.stdout.write("backgrounded · %s · %s\n" % (hint_id, command))
    sys.exit(0)

sys.stderr.write("fake claude: unhandled argv %r\n" % (argv,))
sys.exit(2)
'''

# fake outside-voice.sh —— 只认 `exec --context-file <f> --timeout <n>` 这一条既有契约，
# 不调任何模型；行为由环境变量 FAKE_HELPER_* 驱动。
FAKE_HELPER = r'''#!/usr/bin/env bash
set -u
# 证明「started sidecar 在 child 起跑之前已发布」：child 自己看盘面，把结论写进 stdout。
if [ -n "${FAKE_HELPER_STARTED_PROBE:-}" ]; then
  if [ -f "$FAKE_HELPER_STARTED_PROBE" ]; then
    echo "STARTED_SIDECAR_VISIBLE=yes"
  else
    echo "STARTED_SIDECAR_VISIBLE=no"
  fi
fi
# worker→helper 的 runner/model/effort 只有 env 一条通道 ⇒ 把收到的值原样回显，
# 让「env 是否真的传到了 child」变成 stdout 上的机械锚（而不是靠实现自述）。
echo "ENV_RUNNER=${SDFLOW_VOICE_RUNNER:-<unset>}"
echo "ENV_MODEL=${SDFLOW_VOICE_MODEL:-<unset>}"
echo "ENV_EFFORT=${SDFLOW_VOICE_EFFORT:-<unset>}"
echo "ENV_RUNNER_PID_FILE=${SDFLOW_VOICE_RUNNER_PID_FILE:-<unset>}"
echo "fake-helper-stdout ${FAKE_HELPER_MARKER:-none}"
echo "fake-helper-stderr" >&2
sleep "${FAKE_HELPER_SLEEP:-0}"
exit "${FAKE_HELPER_RC:-0}"
'''


def _write_exec(path, body):
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return path


@pytest.fixture
def job_home(tmp_path):
    """一个「已安装」形态的 hack 目录：job helper + shell helper + data file + manifest。"""
    home = tmp_path / "hack"
    home.mkdir()
    shutil.copy2(JOB_PY, home / "outside-voice-job.py")
    shutil.copy2(HELPER_SH, home / "outside-voice.sh")
    shutil.copy2(PRINCIPLES, home / "skill-principles.md")
    JOB.write_manifest(home)
    return home


@pytest.fixture
def fake_job_home(tmp_path):
    """同上，但 shell helper 换成无模型替身（worker / 集成 smoke 用）。"""
    home = tmp_path / "hack-fake"
    home.mkdir()
    shutil.copy2(JOB_PY, home / "outside-voice-job.py")
    _write_exec(home / "outside-voice.sh", FAKE_HELPER)
    shutil.copy2(PRINCIPLES, home / "skill-principles.md")
    JOB.write_manifest(home)
    return home


@pytest.fixture
def repo(tmp_path):
    """一个最小仓：repo_root / run_dir / context 文件。"""
    root = tmp_path / "repo"
    run_dir = root / "openspec" / "changes" / "c1" / ".outside-voice" / "20260724T020000Z-Ab12Cd"
    run_dir.mkdir(parents=True)
    ctx = run_dir / "design-voice-context.md"
    ctx.write_text("some evidence context\n", encoding="utf-8")
    return {"root": root, "run_dir": run_dir, "ctx": ctx}


@pytest.fixture
def fake_claude(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_exec(bin_dir / "claude", FAKE_CLAUDE)
    return {
        "bin_dir": bin_dir,
        "log": tmp_path / "claude-invocations.jsonl",
        "state": tmp_path / "claude-state.json",
    }


def _env(fake_claude, extra=None, run_dir=None):
    env = os.environ.copy()
    env.pop("SDFLOW_VOICE_RUNNER", None)
    env.pop("SDFLOW_VOICE_MODEL", None)
    env["PATH"] = str(fake_claude["bin_dir"]) + os.pathsep + env["PATH"]
    env["FAKE_CLAUDE_LOG"] = str(fake_claude["log"])
    env["FAKE_CLAUDE_STATE"] = str(fake_claude["state"])
    if run_dir is not None:
        env["FAKE_CLAUDE_SNAPSHOT_DIR"] = str(run_dir)
    if extra:
        env.update({k: str(v) for k, v in extra.items()})
    return env


def _invocations(fake_claude):
    if not fake_claude["log"].exists():
        return []
    return [json.loads(line) for line in fake_claude["log"].read_text(encoding="utf-8").splitlines() if line.strip()]


def _bg_invocations(fake_claude):
    return [i for i in _invocations(fake_claude) if "--bg" in i["argv"] or "--exec" in i["argv"]]


def _run_job(job_home, args, env, timeout=60, cwd=None):
    return subprocess.run(
        [sys.executable, str(job_home / "outside-voice-job.py"), *args],
        capture_output=True, text=True, env=env, timeout=timeout,
        cwd=str(cwd) if cwd else None,
    )


def _json_stdout(proc):
    assert proc.stdout.strip(), "stdout 为空；stderr=%s" % proc.stderr
    return json.loads(proc.stdout.strip().splitlines()[-1])


def _dispatch_args(repo, job_home, site="design-voice", **over):
    args = [
        "dispatch",
        "--run-dir", str(repo["run_dir"]),
        "--site", site,
        "--context-file", str(repo["ctx"]),
        "--repo-root", str(repo["root"]),
        "--runner", "claude",
        "--model", "opus",
        "--effort", "high",
        "--timeout", "900",
    ]
    for key, value in over.items():
        flag = "--" + key.replace("_", "-")
        idx = args.index(flag)
        args[idx + 1] = str(value)
    return args


# ── preflight ─────────────────────────────────────────────────────────────────

def test_preflight_ready_on_supported_version_and_agents_json(job_home, fake_claude):
    proc = _run_job(job_home, ["preflight"], _env(fake_claude))
    payload = _json_stdout(proc)
    assert proc.returncode == 0, proc.stderr
    assert payload["ok"] is True
    assert payload["reason_code"] == "ready"
    assert payload["checks"]["claude-version"]["ok"] is True
    assert payload["checks"]["agents-json"]["ok"] is True
    assert payload["checks"]["capability-manifest"]["ok"] is True
    assert payload["checks"]["posix-shell"]["ok"] is True


def test_preflight_has_no_external_side_effect_and_never_runs_bg_exec(job_home, fake_claude, repo):
    before_home = sorted(p.name for p in job_home.iterdir())
    before_run = sorted(p.name for p in repo["run_dir"].iterdir())

    proc = _run_job(job_home, ["preflight"], _env(fake_claude, run_dir=repo["run_dir"]))

    assert proc.returncode == 0, proc.stderr
    # 负向 golden：任何一次 claude 调用都不得带 --bg / --exec
    for inv in _invocations(fake_claude):
        assert "--bg" not in inv["argv"], inv
        assert "--exec" not in inv["argv"], inv
        assert "true" not in inv["argv"], inv
    # 无 dummy job：fake claude 的 state 文件只由 --bg 分支写
    assert not fake_claude["state"].exists()
    # 无任何落盘副作用
    assert sorted(p.name for p in job_home.iterdir()) == before_home
    assert sorted(p.name for p in repo["run_dir"].iterdir()) == before_run


def test_preflight_fails_closed_on_old_claude_version(job_home, fake_claude):
    env = _env(fake_claude, {"FAKE_CLAUDE_VERSION": "2.1.168 (Claude Code)"})
    proc = _run_job(job_home, ["preflight"], env)
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["ok"] is False
    assert payload["reason_code"] == "preflight-error"
    assert payload["checks"]["claude-version"]["ok"] is False
    assert "2.1.169" in proc.stderr
    assert "升级" in proc.stderr or "upgrade" in proc.stderr.lower()


def test_preflight_fails_closed_when_agent_view_disabled_by_policy(job_home, fake_claude):
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "disabled"})
    proc = _run_job(job_home, ["preflight"], env)
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["checks"]["agents-json"]["ok"] is False
    assert "disableAgentView" in proc.stderr


def test_preflight_fails_closed_when_agents_json_top_level_is_not_a_list(job_home, fake_claude):
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "notlist"})
    proc = _run_job(job_home, ["preflight"], env)
    assert proc.returncode == 1
    assert _json_stdout(proc)["checks"]["agents-json"]["ok"] is False


def test_preflight_fails_closed_on_non_posix_platform(monkeypatch, job_home):
    monkeypatch.setattr(JOB.os, "name", "nt")
    result = JOB.check_posix_shell()
    assert result["ok"] is False
    assert "POSIX" in result["hint"]


def test_preflight_fails_closed_on_capability_manifest_skew(job_home, fake_claude):
    (job_home / "outside-voice.sh").write_text("# tampered\n", encoding="utf-8")
    proc = _run_job(job_home, ["preflight"], _env(fake_claude))
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["checks"]["capability-manifest"]["ok"] is False
    assert "outside-voice.sh" in json.dumps(payload, ensure_ascii=False)
    assert "setup.sh" in proc.stderr


def test_preflight_fails_closed_on_missing_capability_manifest(job_home, fake_claude):
    (job_home / JOB.MANIFEST_NAME).unlink()
    proc = _run_job(job_home, ["preflight"], _env(fake_claude))
    assert proc.returncode == 1
    assert _json_stdout(proc)["checks"]["capability-manifest"]["ok"] is False
    assert "setup.sh" in proc.stderr


def test_preflight_fails_closed_when_manifest_generation_hand_edited(job_home, fake_claude):
    path = job_home / JOB.MANIFEST_NAME
    data = json.loads(path.read_text(encoding="utf-8"))
    data["entries"]["outside-voice.sh"] = "0" * 64
    path.write_text(json.dumps(data), encoding="utf-8")
    proc = _run_job(job_home, ["preflight"], _env(fake_claude))
    assert proc.returncode == 1
    detail = json.dumps(_json_stdout(proc), ensure_ascii=False)
    assert "generation" in detail


def test_preflight_cli_probes_are_bounded_by_a_short_timeout(monkeypatch, job_home):
    """preflight 的两条 CLI 探针本身不在任何 deadline 内 ⇒ 它们各自的 timeout 就是上界。

    30 秒会让「5 秒级失败」在 CLI 卡死时退化到 ~60 秒（两条串行）。
    本机实测 `claude --version` 0.06s、`agents --all --json` 0.17s ⇒ 5 秒已极宽。
    """
    seen = []

    class _Proc:
        def __init__(self, stdout):
            self.returncode = 0
            self.stdout = stdout
            self.stderr = ""

    def spy(argv, timeout):
        seen.append(timeout)
        return _Proc("2.1.220 (Claude Code)\n" if argv[1:] == ["--version"] else "[]\n")

    monkeypatch.setattr(JOB, "_run_cli", spy)
    monkeypatch.setattr(JOB.shutil, "which", lambda name: "/usr/bin/" + name)
    result = JOB.run_preflight(job_home)
    assert result["ok"] is True, result
    assert len(seen) == 2, seen
    assert all(t <= 5 for t in seen), seen


# ── reservation（外部副作用之前的原子门）────────────────────────────────────────

def test_release_reservation_never_raises_when_reserve_is_already_gone(tmp_path):
    """降级路径上唯一还要交付的是 stdout 那行 JSON —— 清理失败 MUST NOT 掀掉它。

    裸 `os.unlink` 的 traceback 会让 stdout 空掉，调用方读不到 `fallback_allowed`，
    一次本可立即同族 fallback 的失败就变成哑失败。
    """
    assert JOB.release_reservation(tmp_path, "ghost") is False
    path = Path(JOB.reserve_path(tmp_path, "real"))
    path.write_text("{}", encoding="utf-8")
    assert JOB.release_reservation(tmp_path, "real") is True
    assert not path.exists()



def test_reservation_exists_before_any_external_dispatch(job_home, fake_claude, repo):
    env = _env(fake_claude, run_dir=repo["run_dir"])
    proc = _run_job(job_home, _dispatch_args(repo, job_home), env)
    assert proc.returncode == 0, proc.stderr
    bg = _bg_invocations(fake_claude)
    assert len(bg) == 1
    assert "design-voice.reserve" in bg[0]["entries"], bg[0]


def test_duplicate_site_is_rejected_before_external_side_effect(job_home, fake_claude, repo):
    (repo["run_dir"] / "design-voice.reserve").write_text("{}", encoding="utf-8")
    (repo["run_dir"] / "design-voice.job.json").write_text("{}", encoding="utf-8")
    proc = _run_job(job_home, _dispatch_args(repo, job_home), _env(fake_claude))
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["state"] == "duplicate-site"
    assert payload["fallback_allowed"] is False
    assert _bg_invocations(fake_claude) == []


def test_third_distinct_site_is_rejected_before_external_side_effect(job_home, fake_claude, repo):
    for site in ("design-voice", "hr-tg"):
        (repo["run_dir"] / (site + ".reserve")).write_text("{}", encoding="utf-8")
        (repo["run_dir"] / (site + ".job.json")).write_text("{}", encoding="utf-8")
    proc = _run_job(job_home, _dispatch_args(repo, job_home, site="third-voice"), _env(fake_claude))
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["state"] == "slot-limit"
    assert payload["fallback_allowed"] is False
    assert _bg_invocations(fake_claude) == []
    # 自己的 reserve 必须被回收，不留第三个坑
    assert not (repo["run_dir"] / "third-voice.reserve").exists()


def test_residual_reserve_without_metadata_is_unknown_cost(job_home, fake_claude, repo):
    (repo["run_dir"] / "design-voice.reserve").write_text("{}", encoding="utf-8")
    proc = _run_job(job_home, _dispatch_args(repo, job_home), _env(fake_claude))
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["state"] == "unknown-cost"
    assert payload["fallback_allowed"] is False  # 禁止立即 fallback（防双倍计费）
    assert _bg_invocations(fake_claude) == []    # 禁止自动重派
    assert (repo["run_dir"] / "design-voice.reserve").exists()  # 证据保留给 reconcile


# ── dispatch ──────────────────────────────────────────────────────────────────

def test_dispatch_returns_within_monotonic_deadline_with_verified_job_id(job_home, fake_claude, repo):
    env = _env(fake_claude, {"FAKE_CLAUDE_JOB_ID": "75d34378"})
    started = time.monotonic()
    proc = _run_job(job_home, _dispatch_args(repo, job_home), env)
    elapsed = time.monotonic() - started   # 真实墙钟——不回读被测自己写的字段
    payload = _json_stdout(proc)
    assert proc.returncode == 0, proc.stderr
    assert payload["ok"] is True
    assert payload["job_id"] == "75d34378"
    assert payload["reason_code"] == "ok"
    # 成功路径 MUST NOT 把核验 grace 耗满：job 一进 roster 就立刻返回。
    assert elapsed < JOB.DISPATCH_DEADLINE_SECONDS + JOB.NONCE_LOOKUP_GRACE_SECONDS, elapsed
    assert payload["dispatch_duration_seconds"] <= elapsed


def test_dispatch_duration_covers_nonce_verification_not_just_the_spawn(job_home, fake_claude, repo):
    """`dispatch_duration_seconds` MUST 覆盖到 nonce 核验结束。

    只算到 `communicate()` 返回的话，这个值从构造上就 <DISPATCH_DEADLINE_SECONDS，
    任何拿它跟 deadline 比较的断言都恒真 ⇒「5 秒级诚实降级」等于没有机械锚。
    这里让 CLI 秒退（rc!=0）、roster 恒空：墙钟里剩下的全部就是那段有界核验 grace。
    """
    env = _env(fake_claude, {"FAKE_CLAUDE_BG_MODE": "fail", "FAKE_CLAUDE_AGENTS_MODE": "empty"})
    started = time.monotonic()
    proc = _run_job(job_home, _dispatch_args(repo, job_home), env, timeout=60)
    elapsed = time.monotonic() - started
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    duration = payload["dispatch_duration_seconds"]
    assert duration >= JOB.NONCE_LOOKUP_GRACE_SECONDS * 0.8, (duration, elapsed)
    assert duration <= elapsed, (duration, elapsed)
    # 有界：整段诚实降级仍在「spawn deadline + 核验 grace」的预算内
    assert elapsed < JOB.DISPATCH_DEADLINE_SECONDS + JOB.NONCE_LOOKUP_GRACE_SECONDS + 10, elapsed


def test_dispatch_writes_job_metadata_atomically_with_required_fields(job_home, fake_claude, repo):
    env = _env(fake_claude, {"FAKE_CLAUDE_JOB_ID": "75d34378"})
    proc = _run_job(job_home, _dispatch_args(repo, job_home), env)
    assert proc.returncode == 0, proc.stderr
    meta_path = repo["run_dir"] / "design-voice.job.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    for field in ("schema_version", "run_id", "site", "repo_root", "attempt_nonce",
                  "runner", "model", "effort", "platform", "job_id", "session_id",
                  "dispatched_at", "startup_deadline_at", "timeout_seconds", "command_sha256"):
        assert field in meta, field
    assert meta["schema_version"] == JOB.SCHEMA_VERSION
    assert meta["run_id"] == repo["run_dir"].name
    assert meta["site"] == "design-voice"
    assert meta["repo_root"] == str(repo["root"].resolve())
    assert meta["runner"] == "claude"
    assert meta["model"] == "opus"
    assert meta["effort"] == "high"
    assert meta["platform"] == "posix"
    assert meta["timeout_seconds"] == 900
    assert re.match(r"\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z", meta["dispatched_at"])
    assert stat.S_IMODE(meta_path.stat().st_mode) == 0o600
    # 命令摘要必须是真实下发命令的 sha256（不是自述）
    command = _bg_invocations(fake_claude)[0]["argv"][-1]
    assert meta["command_sha256"] == hashlib.sha256(command.encode("utf-8")).hexdigest()
    # 原子发布：不得残留临时文件
    assert [p.name for p in repo["run_dir"].glob(".tmp-*")] == []


def test_dispatch_command_is_single_shell_quoted_worker_invocation(job_home, fake_claude, repo):
    env = _env(fake_claude)
    proc = _run_job(job_home, _dispatch_args(repo, job_home), env)
    assert proc.returncode == 0, proc.stderr
    command = _bg_invocations(fake_claude)[0]["argv"][-1]
    parts = shlex.split(command)
    assert parts[1] == str(job_home / "outside-voice-job.py")
    assert parts[2] == "worker"
    assert "--run-dir" in parts and str(repo["run_dir"].resolve()) in parts
    assert "--site" in parts and "design-voice" in parts
    assert "--timeout" in parts and "900" in parts
    assert "\n" not in command and "\0" not in command
    # 只带受校验的路径 / runner / model / timeout —— MUST NOT 携带 context 正文
    assert "some evidence context" not in command


def test_dispatch_reclaims_process_tree_and_reserve_when_deadline_expires(job_home, fake_claude, repo, tmp_path):
    pid_file = tmp_path / "hang-pids.json"
    env = _env(fake_claude, {
        "FAKE_CLAUDE_BG_MODE": "hang",
        "FAKE_CLAUDE_BG_WRITE_STATE": "0",   # 未产生外部 job
        "FAKE_CLAUDE_AGENTS_MODE": "empty",
        "FAKE_CLAUDE_PID_FILE": pid_file,
    })
    started = time.monotonic()
    proc = _run_job(job_home, _dispatch_args(repo, job_home), env, timeout=60)
    elapsed = time.monotonic() - started
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["reason_code"] == "exec-error"
    assert payload["fallback_allowed"] is True
    # 上界 = spawn deadline + kill 后收流 + 核验 grace，全部有界
    assert elapsed < JOB.DISPATCH_DEADLINE_SECONDS + 5 + JOB.NONCE_LOOKUP_GRACE_SECONDS + 10, \
        "monotonic deadline 未生效，实际 %.1fs" % elapsed
    # 尚未产生外部 job 的 reserve 必须清理
    assert not (repo["run_dir"] / "design-voice.reserve").exists()
    # spawn 进程树被回收
    pids = json.loads(pid_file.read_text(encoding="utf-8"))
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        alive = [p for p in (pids["self"], pids["child"]) if _pid_alive(p)]
        if not alive:
            break
        time.sleep(0.1)
    assert not [p for p in (pids["self"], pids["child"]) if _pid_alive(p)], pids


def _pid_alive(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def test_dispatch_deadline_with_external_job_present_is_unknown_cost(job_home, fake_claude, repo, tmp_path):
    env = _env(fake_claude, {
        "FAKE_CLAUDE_BG_MODE": "hang",
        "FAKE_CLAUDE_BG_WRITE_STATE": "1",   # 外部 job 已产生
        "FAKE_CLAUDE_PID_FILE": tmp_path / "pids.json",
    })
    proc = _run_job(job_home, _dispatch_args(repo, job_home), env, timeout=60)
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["state"] == "unknown-cost"
    assert payload["fallback_allowed"] is False
    assert (repo["run_dir"] / "design-voice.reserve").exists()
    assert not (repo["run_dir"] / "design-voice.job.json").exists()


def test_dispatch_grants_bounded_grace_when_job_registers_after_the_kill(job_home, fake_claude, repo):
    """超时被 SIGKILL 之后，nonce 核验 MUST 仍有**独立**的有界 grace。

    5 秒 deadline 到点，正是 supervisor 注册最可能滞后的时刻。零 grace（只轮询一次）
    会把一个**已经产生、已经计费**的 job 判成「没产生」⇒ 清掉 reserve + 允许 fallback，
    同时留下孤儿付费 job 和一次重付——恰是 OVBG-02 要杀的形态。
    这里 job 在 kill 之后才进 roster：正确行为是 unknown-cost + 禁 fallback + 留 reserve。
    """
    env = _env(fake_claude, {
        "FAKE_CLAUDE_BG_MODE": "hang",
        "FAKE_CLAUDE_BG_WRITE_STATE": "1",
        "FAKE_CLAUDE_HANG_CHILD": "0",      # 不留持有管道的孙子进程，kill 后立即收流
        "FAKE_CLAUDE_BG_STATE_DELAY": "7",  # > 5 秒 deadline ⇒ 注册必然落在 kill 之后
    })
    started = time.monotonic()
    proc = _run_job(job_home, _dispatch_args(repo, job_home), env, timeout=90)
    elapsed = time.monotonic() - started
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["state"] == "unknown-cost", payload
    assert payload["fallback_allowed"] is False, payload
    assert (repo["run_dir"] / "design-voice.reserve").exists()   # 证据留给 reconcile
    assert not (repo["run_dir"] / "design-voice.job.json").exists()
    # grace 是有界的，不是无限等
    assert elapsed < JOB.DISPATCH_DEADLINE_SECONDS + 5 + JOB.NONCE_LOOKUP_GRACE_SECONDS + 10, elapsed


def test_dispatch_verifies_attempt_by_job_id_when_done_entry_has_no_name(job_home, fake_claude, repo):
    """`state=done` 的 background 条目**没有 name** ⇒ 只认 name 的核验会扑空。

    极快失败的 worker（helper 缺失，<1s 即终态）就落在这一格：job 真的产生了，
    却被判成「没产生」。故 dispatch stdout 的 short id 必须是**并列**匹配通道。
    """
    env = _env(fake_claude, {
        "FAKE_CLAUDE_JOB_ID": "75d34378",
        "FAKE_CLAUDE_AGENTS_MODE": "done-noname",
    })
    proc = _run_job(job_home, _dispatch_args(repo, job_home), env, timeout=60)
    payload = _json_stdout(proc)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert payload["job_id"] == "75d34378"
    assert (repo["run_dir"] / "design-voice.job.json").exists()


def test_dispatch_is_not_blocked_by_a_drifted_backgrounded_stdout_format(job_home, fake_claude, repo):
    """stdout 的 short id 只是**匹配线索**，MUST NOT 单独构成失败判据。

    `backgrounded · <id> · <cmd>` 属 research preview 格式；一次漂移解出的垃圾 hex
    若能否掉一次好 dispatch，`_parse_job_id_hint` 的「解析不构成失败判据」就是空话。
    这里 nonce 通道唯一命中，核验应照常通过。
    """
    env = _env(fake_claude, {
        "FAKE_CLAUDE_JOB_ID": "75d34378",
        "FAKE_CLAUDE_BG_HINT_ID": "0badc0de",   # 与 canonical id 不一致的漂移值
    })
    proc = _run_job(job_home, _dispatch_args(repo, job_home), env, timeout=60)
    payload = _json_stdout(proc)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert payload["job_id"] == "75d34378"


def test_dispatch_fails_closed_when_canonical_job_id_is_not_unique(job_home, fake_claude, repo):
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "duplicate"})
    proc = _run_job(job_home, _dispatch_args(repo, job_home), env)
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["state"] == "unknown-cost"
    assert payload["fallback_allowed"] is False


def test_dispatch_fails_closed_when_no_job_carries_the_attempt_nonce(job_home, fake_claude, repo):
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "nomatch"})
    proc = _run_job(job_home, _dispatch_args(repo, job_home), env)
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["state"] == "unknown-cost"
    assert not (repo["run_dir"] / "design-voice.job.json").exists()


def test_dispatch_fails_closed_and_frees_reserve_when_cli_refuses(job_home, fake_claude, repo):
    env = _env(fake_claude, {"FAKE_CLAUDE_BG_MODE": "fail", "FAKE_CLAUDE_AGENTS_MODE": "empty"})
    proc = _run_job(job_home, _dispatch_args(repo, job_home), env)
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["reason_code"] == "exec-error"
    assert payload["fallback_allowed"] is True
    assert not (repo["run_dir"] / "design-voice.reserve").exists()


def test_dispatch_fails_closed_when_preflight_not_ready(job_home, fake_claude, repo):
    env = _env(fake_claude, {"FAKE_CLAUDE_VERSION": "2.1.100 (Claude Code)"})
    proc = _run_job(job_home, _dispatch_args(repo, job_home), env)
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["reason_code"] == "preflight-error"
    assert payload["fallback_allowed"] is True
    assert _bg_invocations(fake_claude) == []
    assert not (repo["run_dir"] / "design-voice.reserve").exists()


@pytest.mark.parametrize("timeout", ["0", "3601", "abc"])
def test_dispatch_rejects_out_of_range_timeout(job_home, fake_claude, repo, timeout):
    proc = _run_job(job_home, _dispatch_args(repo, job_home, timeout=timeout), _env(fake_claude))
    assert proc.returncode != 0
    assert _bg_invocations(fake_claude) == []


@pytest.mark.parametrize("effort", ["low", "medium", "xhigh", ""])
def test_dispatch_only_ever_dispatches_effort_high(job_home, fake_claude, repo, effort):
    """🔒 OVBG-04：spec 把后台通道的推理档位**写死 `--effort high`**。

    dispatch 是这条链上 effort 的**唯一 producer**（`build_worker_command` → worker →
    `SDFLOW_VOICE_EFFORT` → `outside-voice.sh` 全程原样透传，没有第二个注入点）⇒ 钉在
    这里一处，整条链就只可能跑 high。降档一律 **fail-loud 拒绝**，MUST NOT 静默改写成
    high——静默改写会让「调用方以为发了 medium、实际跑了 high」两边都察觉不到。
    helper 侧 `${SDFLOW_VOICE_EFFORT:-high}` 的透传能力**保留不删**（宿主直调 exec 用）。
    """
    proc = _run_job(job_home, _dispatch_args(repo, job_home, effort=effort), _env(fake_claude))
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["ok"] is False
    assert payload["state"] == "usage-error", payload
    assert _bg_invocations(fake_claude) == [], "非 high 的档位 MUST 在任何外部派发之前被拒"
    assert not (repo["run_dir"] / "design-voice.reserve").exists()


def test_dispatch_accepts_effort_high_and_hands_it_down_verbatim(job_home, fake_claude, repo):
    """正向对照：唯一放行的档位真的被原样传进 worker 命令（拒绝不是靠"全拒"实现的）。"""
    proc = _run_job(job_home, _dispatch_args(repo, job_home, effort="high"), _env(fake_claude))
    payload = _json_stdout(proc)
    assert proc.returncode == 0, proc.stderr
    assert payload["ok"] is True
    command = _bg_invocations(fake_claude)[0]["argv"][-1]
    parts = shlex.split(command)
    assert parts[parts.index("--effort") + 1] == "high", command


@pytest.mark.parametrize("site", ["../escape", "a/b", "with space", ""])
def test_dispatch_rejects_unsafe_site_names(job_home, fake_claude, repo, site):
    proc = _run_job(job_home, _dispatch_args(repo, job_home, site=site), _env(fake_claude))
    assert proc.returncode != 0
    assert _bg_invocations(fake_claude) == []


@pytest.mark.parametrize("run_id", ["bad;rm -rf /", "with space", "../up"])
def test_dispatch_rejects_unsafe_run_ids(job_home, fake_claude, repo, run_id):
    args = _dispatch_args(repo, job_home) + ["--run-id", run_id]
    proc = _run_job(job_home, args, _env(fake_claude))
    assert proc.returncode != 0
    assert _bg_invocations(fake_claude) == []
    assert not (repo["run_dir"] / "design-voice.reserve").exists()


def test_dispatch_rejects_context_file_outside_repo_root(job_home, fake_claude, repo, tmp_path):
    outside = tmp_path / "outside-context.md"
    outside.write_text("x\n", encoding="utf-8")
    args = _dispatch_args(repo, job_home)
    args[args.index("--context-file") + 1] = str(outside)
    proc = _run_job(job_home, args, _env(fake_claude))
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["ok"] is False
    assert _bg_invocations(fake_claude) == []


# ── worker ────────────────────────────────────────────────────────────────────

def _worker_args(repo, site="design-voice", nonce="nonce-abc", timeout=30):
    return [
        "worker",
        "--run-dir", str(repo["run_dir"]),
        "--site", site,
        "--context-file", str(repo["ctx"]),
        "--repo-root", str(repo["root"]),
        "--runner", "claude",
        "--model", "opus",
        "--effort", "high",
        "--timeout", str(timeout),
        "--attempt-nonce", nonce,
        "--run-id", repo["run_dir"].name,
    ]


def test_worker_publishes_started_then_terminal_then_rc(fake_job_home, repo):
    env = os.environ.copy()
    env["FAKE_HELPER_MARKER"] = "hello"
    env["FAKE_HELPER_STARTED_PROBE"] = str(repo["run_dir"] / "design-voice.started.json")
    proc = _run_job(fake_job_home, _worker_args(repo), env, timeout=60)
    assert proc.returncode == 0, proc.stderr

    started = json.loads((repo["run_dir"] / "design-voice.started.json").read_text(encoding="utf-8"))
    assert started["attempt_nonce"] == "nonce-abc"
    assert re.match(r"\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z", started["started_at"])
    assert started["worker"]["pid"] > 0
    assert "pgid" in started["worker"] and "ppid" in started["worker"]

    stdout_text = (repo["run_dir"] / "design-voice.stdout").read_text(encoding="utf-8")
    assert "fake-helper-stdout hello" in stdout_text
    # child 起跑时 started sidecar 必须已在盘面上（发布顺序的机械锚，非自述）
    assert "STARTED_SIDECAR_VISIBLE=yes" in stdout_text

    terminal = json.loads((repo["run_dir"] / "design-voice.terminal.json").read_text(encoding="utf-8"))
    assert terminal["attempt_nonce"] == "nonce-abc"
    assert terminal["stdout_sha256"] == hashlib.sha256(
        (repo["run_dir"] / "design-voice.stdout").read_bytes()).hexdigest()
    assert re.match(r"\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z", terminal["terminal_at"])

    rc_path = repo["run_dir"] / "design-voice.rc"
    assert rc_path.read_text(encoding="utf-8") == "0"
    assert (repo["run_dir"] / "design-voice.stderr").read_text(encoding="utf-8").strip() == "fake-helper-stderr"


def test_worker_passes_runner_model_effort_env_to_helper(fake_job_home, repo):
    """worker→helper 的 runner/model/effort **只有 env 一条通道** ⇒ 必须真的传到 child。

    这条锚同时守 C1（`subprocess.call` 漏 `env=`）与 I2（effort 被记进 job.json 却从未下发）。
    调用方 env 里刻意不含这三个变量：child 若拿到值，就只可能来自 worker 显式构造的 env。
    """
    env = os.environ.copy()
    for name in ("SDFLOW_VOICE_RUNNER", "SDFLOW_VOICE_MODEL", "SDFLOW_VOICE_EFFORT"):
        env.pop(name, None)
    args = _worker_args(repo)
    args[args.index("--effort") + 1] = "medium"
    proc = _run_job(fake_job_home, args, env, timeout=60)
    assert proc.returncode == 0, proc.stderr
    stdout_text = (repo["run_dir"] / "design-voice.stdout").read_text(encoding="utf-8")
    assert "ENV_RUNNER=claude" in stdout_text, stdout_text
    assert "ENV_MODEL=opus" in stdout_text, stdout_text
    assert "ENV_EFFORT=medium" in stdout_text, stdout_text


def test_worker_hands_the_runner_pid_file_path_down_to_the_helper(fake_job_home, repo):
    """🔴 跨票交接锚（Task 4 的落点）：worker MUST 把 `<site>.runner.pid` 的绝对路径经
    `SDFLOW_VOICE_RUNNER_PID_FILE` 下发给 helper。

    helper 在 spawn runner 前把 `OV_RUNNER_PID` 写进这个文件后，`probe_subtree` 才有
    「runner 子树是否退出」的直接信号 —— 否则组长分支只能永久 fail-closed 判 unverifiable
    （worker 自己的进程组圈不住 GNU timeout 自建的独立组）。
    """
    env = os.environ.copy()
    env.pop("SDFLOW_VOICE_RUNNER_PID_FILE", None)
    proc = _run_job(fake_job_home, _worker_args(repo), env, timeout=60)
    assert proc.returncode == 0, proc.stderr
    stdout_text = (repo["run_dir"] / "design-voice.stdout").read_text(encoding="utf-8")
    expected = str(repo["run_dir"] / "design-voice.runner.pid")
    assert ("ENV_RUNNER_PID_FILE=" + expected) in stdout_text, stdout_text


def test_worker_env_reaches_the_real_shell_helper(job_home, repo):
    """C1 接缝锚：让 worker 调**仓内真的** `outside-voice.sh`（不调模型）。

    全部既有 worker 用例都走 FAKE_HELPER（完全不看 env）⇒ 漏传 `env=` 也能全绿。
    这里用真 helper 的两条**早期**拒绝路径做判别器（本机实测，见 fix 报告）：
      · runner 未送达 ⇒ stderr "SDFLOW_VOICE_RUNNER 未设置"、rc=1
      · runner 送达但值非法 ⇒ stderr "未知 SDFLOW_VOICE_RUNNER: <值>"、rc=1
      · runner+model 都送达、context 不存在 ⇒ stderr "context file not found"、rc=2
    三者互斥且都在任何模型调用之前返回。
    """
    base_env = os.environ.copy()
    for name in ("SDFLOW_VOICE_RUNNER", "SDFLOW_VOICE_MODEL", "SDFLOW_VOICE_EFFORT"):
        base_env.pop(name, None)

    # ① runner 通道
    args = _worker_args(repo, site="runner-probe")
    args[args.index("--runner") + 1] = "bogus-runner"
    proc = _run_job(job_home, args, base_env, timeout=60)
    assert proc.returncode == 0, proc.stderr
    err = (repo["run_dir"] / "runner-probe.stderr").read_text(encoding="utf-8")
    assert "SDFLOW_VOICE_RUNNER 未设置" not in err, err
    assert "未知 SDFLOW_VOICE_RUNNER: bogus-runner" in err, err
    assert (repo["run_dir"] / "runner-probe.rc").read_text(encoding="utf-8") == "1"

    # ② model 通道（runner=claude 时 helper 强制要求 SDFLOW_VOICE_MODEL 非空）
    args = _worker_args(repo, site="model-probe")
    args[args.index("--context-file") + 1] = str(repo["run_dir"] / "no-such-context.md")
    proc = _run_job(job_home, args, base_env, timeout=60)
    assert proc.returncode == 0, proc.stderr
    err = (repo["run_dir"] / "model-probe.stderr").read_text(encoding="utf-8")
    assert "SDFLOW_VOICE_RUNNER 未设置" not in err, err
    assert "SDFLOW_VOICE_MODEL 未设置" not in err, err
    assert "context file not found" in err, err
    assert (repo["run_dir"] / "model-probe.rc").read_text(encoding="utf-8") == "2"


def test_worker_output_files_are_0600(fake_job_home, repo):
    proc = _run_job(fake_job_home, _worker_args(repo), os.environ.copy(), timeout=60)
    assert proc.returncode == 0, proc.stderr
    for name in ("design-voice.stdout", "design-voice.stderr", "design-voice.rc",
                 "design-voice.started.json", "design-voice.terminal.json"):
        mode = stat.S_IMODE((repo["run_dir"] / name).stat().st_mode)
        assert mode == 0o600, (name, oct(mode))


def test_worker_redirects_own_and_child_streams_before_running_payload(fake_job_home, repo):
    """worker 自身与 child 的 stdout/stderr 都不得回流到 supervisor transcript。"""
    proc = _run_job(fake_job_home, _worker_args(repo), os.environ.copy(), timeout=60)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == ""
    assert proc.stderr == ""
    assert "fake-helper-stdout" in (repo["run_dir"] / "design-voice.stdout").read_text(encoding="utf-8")


def test_worker_publishes_pure_decimal_rc_for_helper_timeout(fake_job_home, repo):
    env = os.environ.copy()
    env["FAKE_HELPER_RC"] = "124"
    proc = _run_job(fake_job_home, _worker_args(repo), env, timeout=60)
    assert proc.returncode == 0, proc.stderr
    rc_text = (repo["run_dir"] / "design-voice.rc").read_text(encoding="utf-8")
    assert rc_text == "124"
    assert re.match(r"\A\d+\Z", rc_text)


def test_worker_publishes_rc_even_when_shell_helper_is_missing(fake_job_home, repo):
    (fake_job_home / "outside-voice.sh").unlink()
    proc = _run_job(fake_job_home, _worker_args(repo), os.environ.copy(), timeout=60)
    rc_path = repo["run_dir"] / "design-voice.rc"
    assert rc_path.exists(), (proc.stdout, proc.stderr)
    assert re.match(r"\A\d+\Z", rc_path.read_text(encoding="utf-8"))
    assert rc_path.read_text(encoding="utf-8") != "0"
    assert (repo["run_dir"] / "design-voice.terminal.json").exists()


def test_worker_publish_order_is_terminal_witness_then_rc(monkeypatch, tmp_path):
    """rc 是终态发布点 ⇒ terminal witness MUST 先落盘（模块级顺序锚）。"""
    order = []
    real_atomic = JOB.atomic_write_json

    def spy_json(path, payload, mode=0o600):
        order.append(("json", Path(path).name))
        return real_atomic(path, payload, mode)

    real_rc = JOB.publish_rc

    def spy_rc(run_dir, site, rc):
        order.append(("rc", "%s.rc" % site))
        return real_rc(run_dir, site, rc)

    monkeypatch.setattr(JOB, "atomic_write_json", spy_json)
    monkeypatch.setattr(JOB, "publish_rc", spy_rc)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "s.stdout").write_bytes(b"out")
    (run_dir / "s.stderr").write_bytes(b"err")
    JOB.publish_terminal(run_dir, "s", "nonce", "run-1", 7)
    assert order == [("json", "s.terminal.json"), ("rc", "s.rc")]
    assert (run_dir / "s.rc").read_text(encoding="utf-8") == "7"


# ── dispatch → worker 全链（离线，无真 claude）────────────────────────────────

def test_dispatch_to_worker_lifecycle_offline(fake_job_home, fake_claude, repo):
    """fake claude 的 `run` 模式真执行下发命令 ⇒ 验 dispatch 组的命令串确实可跑通 worker。"""
    env = _env(fake_claude, {
        "FAKE_CLAUDE_BG_MODE": "run",
        "FAKE_CLAUDE_JOB_ID": "abc12345",
        "FAKE_HELPER_MARKER": "offline",
    })
    proc = _run_job(fake_job_home, _dispatch_args(repo, fake_job_home), env)
    assert proc.returncode == 0, proc.stderr
    rc_path = repo["run_dir"] / "design-voice.rc"
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline and not rc_path.exists():
        time.sleep(0.2)
    assert rc_path.exists(), "worker 未发布 rc"
    assert rc_path.read_text(encoding="utf-8") == "0"
    assert "fake-helper-stdout offline" in (repo["run_dir"] / "design-voice.stdout").read_text(encoding="utf-8")
    meta = json.loads((repo["run_dir"] / "design-voice.job.json").read_text(encoding="utf-8"))
    started = json.loads((repo["run_dir"] / "design-voice.started.json").read_text(encoding="utf-8"))
    assert started["attempt_nonce"] == meta["attempt_nonce"]


# ── 真机集成：跨 shell 存活（无模型 job）──────────────────────────────────────

def _real_claude_reason():
    claude = shutil.which("claude")
    if not claude:
        return "需要本机安装的 claude CLI（真实 --bg --exec supervisor 跨 shell 存活证明）"
    try:
        out = subprocess.run([claude, "--version"], capture_output=True, text=True, timeout=30)
    except Exception as exc:  # pragma: no cover - 环境异常
        return "claude --version 不可用: %s" % exc
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", out.stdout or "")
    if not match:
        return "claude --version 输出无法解析: %r" % (out.stdout,)
    if tuple(int(x) for x in match.groups()) < JOB.MIN_CLAUDE_VERSION:
        return "claude 版本低于 %s" % ".".join(str(x) for x in JOB.MIN_CLAUDE_VERSION)
    return None


_REAL_CLAUDE_SKIP = _real_claude_reason()


@pytest.mark.skipif(_REAL_CLAUDE_SKIP is not None, reason=_REAL_CLAUDE_SKIP or "")
def test_background_worker_survives_dispatching_shell_exit(fake_job_home, repo):
    """真 `claude --bg --exec`：发起 shell 退出后，无模型 worker 仍跑到终态。"""
    env = os.environ.copy()
    env["FAKE_HELPER_MARKER"] = "cross-shell"
    env["FAKE_HELPER_SLEEP"] = "6"      # 明显长于 dispatch 调用本身
    started = time.monotonic()
    proc = _run_job(fake_job_home, _dispatch_args(repo, fake_job_home), env, timeout=60)
    dispatch_elapsed = time.monotonic() - started
    payload = _json_stdout(proc)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    job_id = payload["job_id"]
    try:
        assert dispatch_elapsed < 20, "dispatch 用时 %.1fs" % dispatch_elapsed
        # duration 现在覆盖到 nonce 核验结束 ⇒ 上界是 spawn deadline + 核验 grace
        assert payload["dispatch_duration_seconds"] < (
            JOB.DISPATCH_DEADLINE_SECONDS + JOB.NONCE_LOOKUP_GRACE_SECONDS)
        # 发起 shell（上面的 subprocess）已经退出；worker 由 supervisor 托管继续跑
        rc_path = repo["run_dir"] / "design-voice.rc"
        assert not rc_path.exists(), "worker 在发起 shell 退出前就终态了，证不出跨 shell 存活"
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline and not rc_path.exists():
            time.sleep(0.5)
        assert rc_path.exists(), "worker 未在 120s 内发布 rc"
        assert rc_path.read_text(encoding="utf-8") == "0"
        assert "fake-helper-stdout cross-shell" in (
            repo["run_dir"] / "design-voice.stdout").read_text(encoding="utf-8")
        assert (repo["run_dir"] / "design-voice.started.json").exists()
        assert (repo["run_dir"] / "design-voice.terminal.json").exists()
    finally:
        subprocess.run([shutil.which("claude"), "rm", job_id],
                       capture_output=True, text=True, timeout=60)


# ══════════════════════════════════════════════════════════════════════════════
# Task 2：终态派生的 status / await / collect
#
# TDD 接缝（先定后写，测试只打这两处）：
#   ③ **子命令 CLI 契约**：`status` / `await` / `collect` 的 argv、stdout 上的单行 JSON
#      （`ok` / `state` / `terminal` / `reason_code` / 时刻 / duration / runner/model/effort /
#      stdout digest）与退出码（0 ⟺ `ok` 为真）。
#   ④ **派生纯函数契约**：`JOB.derive_status(run_dir, site, liveness=…, now=…)` ——
#      rc × liveness × 元数据的笛卡尔归类在此逐组合钉死；CLI 只是它的薄壳，
#      `test_status_cli_is_a_thin_shell_over_derive_status` 把二者绑住，防第二份实现。
# ══════════════════════════════════════════════════════════════════════════════

RC_KINDS = ("absent", "rc0_nonempty", "rc0_empty", "rc124", "rc3", "rc_other", "rc_bad")
LIVENESS_KINDS = ("working", "done", "failed", "stopped", "missing", "unavailable")
META_KINDS = ("complete", "missing-field", "schema-drift")


def _expected_classification(rc_kind, liveness, meta_kind):
    """期望表**逐条抄自 spec**，MUST NOT 从实现回读（否则等于用实现证明实现）。

    · OVBG-02：`.rc` 不存在且 agent working = RUNNING；`.rc=0` 且 stdout 非空 = SUCCEEDED；
      `.rc=124` = TIMED_OUT；其他退出码 = FAILED；terminal agent 无 `.rc` = LOST。
    · OVBG-02「元数据损坏不得猜成功」：job JSON 缺字段 / rc 非纯十进制 / rc=0 但 stdout 为空
      → `exec-error`。
    · HAE-09「锚契约与 reason_code 枚举语义不变」⇒ 沿用两份评审 SKILL ⑦ 的同一张 rc 表：
      `3` = `secret-hit`（该码**不允许**同族 fallback，若并入 exec-error 会让调用方拿同一份
      命中 secret 的 context 再派一次，正是 OVBG-04 要杀的形态）。
    """
    if meta_kind != "complete":
        return ("CORRUPT", "exec-error")
    if rc_kind == "rc_bad":
        return ("CORRUPT", "exec-error")
    if rc_kind == "rc0_nonempty":
        return ("SUCCEEDED", "ok")
    if rc_kind == "rc0_empty":
        return ("CORRUPT", "exec-error")
    if rc_kind == "rc124":
        return ("TIMED_OUT", "timeout")
    if rc_kind == "rc3":
        return ("FAILED", "secret-hit")
    if rc_kind == "rc_other":
        return ("FAILED", "exec-error")
    if liveness in ("done", "failed", "stopped", "missing"):
        return ("LOST", "exec-error")
    return ("RUNNING", None)


_RC_TEXT = {"rc0_nonempty": "0", "rc0_empty": "0", "rc124": "124", "rc3": "3",
            "rc_other": "7", "rc_bad": "oops"}


def _iso(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _seed_site(run_dir, site="design-voice", *, meta="complete", rc_kind="absent",
               now=None, dispatched_ago=2.0, started_ago=1.0, timeout_seconds=900,
               startup_deadline_ago=None, job_id="75d34378", nonce="n0nce7777",
               write_job=True, write_started=True, write_terminal=None,
               stdout=b"outside voice findings\n", stderr=b"fake-stderr\n",
               terminal_digest=None, run_id=None, nonce_in_witness=None,
               worker_pid=4242, worker_pgid=None, repo_root=None, runner_pid=None):
    """把一个站点的盘面摆成指定形态。返回写下的 job metadata（dict 或 None）。

    盘面即状态 ⇒ 所有用例的输入都是「run dir 里有哪些文件、内容是什么」，
    不通过任何可变 status 字段注入。
    """
    run_dir = Path(run_dir)
    now = time.time() if now is None else now
    run_id = run_id or run_dir.name
    witness_nonce = nonce if nonce_in_witness is None else nonce_in_witness
    meta_payload = None
    if write_job:
        startup_at = (now - startup_deadline_ago) if startup_deadline_ago is not None \
            else (now - dispatched_ago + JOB.STARTUP_DEADLINE_SECONDS)
        meta_payload = {
            "schema_version": JOB.SCHEMA_VERSION,
            "run_id": run_id,
            "site": site,
            "repo_root": str(repo_root) if repo_root is not None else (
                str(Path(run_dir).parents[3].resolve()) if len(Path(run_dir).parents) > 3
                else str(run_dir.resolve())),
            "run_dir": str(run_dir.resolve()),
            "context_file": str((run_dir / (site + "-context.md")).resolve()),
            "attempt_nonce": nonce,
            "runner": "claude", "model": "opus", "effort": "high",
            "platform": "posix", "sys_platform": sys.platform,
            "job_id": job_id, "session_id": job_id + "-sess",
            "dispatched_at": _iso(now - dispatched_ago),
            "startup_deadline_at": _iso(startup_at),
            "timeout_seconds": timeout_seconds,
            "command_sha256": "0" * 64,
            "job_helper_version": JOB.VERSION,
            "dispatch_duration_seconds": 0.4,
        }
        if meta == "missing-field":
            meta_payload.pop("attempt_nonce")
        elif meta == "schema-drift":
            meta_payload["schema_version"] = JOB.SCHEMA_VERSION + 1
        JOB.atomic_write_json(JOB.job_path(run_dir, site), meta_payload)

    if write_started:
        JOB.atomic_write_json(run_dir / (site + ".started.json"), {
            "schema_version": JOB.SCHEMA_VERSION, "site": site, "run_id": run_id,
            "attempt_nonce": witness_nonce, "started_at": _iso(now - started_ago),
            "worker": {"pid": worker_pid, "ppid": 1,
                       "pgid": worker_pid if worker_pgid is None else worker_pgid,
                       "sid": worker_pid, "executable": sys.executable},
        })

    if runner_pid is not None:
        # Task 4 的 helper 在 spawn runner 前落的直接信号（纯十进制 `OV_RUNNER_PID`）。
        (run_dir / (site + JOB.RUNNER_PID_SUFFIX)).write_text(
            str(runner_pid), encoding="utf-8")

    if rc_kind != "absent":
        payload = b"" if rc_kind == "rc0_empty" else stdout
        (run_dir / (site + ".stdout")).write_bytes(payload)
        (run_dir / (site + ".stderr")).write_bytes(stderr)
        if write_terminal is not False:
            JOB.atomic_write_json(run_dir / (site + ".terminal.json"), {
                "schema_version": JOB.SCHEMA_VERSION, "site": site, "run_id": run_id,
                "attempt_nonce": witness_nonce, "terminal_at": _iso(now - 0.2),
                "stdout_sha256": terminal_digest or hashlib.sha256(payload).hexdigest(),
                "stdout_bytes": len(payload), "stderr_bytes": len(stderr),
            })
        (run_dir / (site + ".rc")).write_text(_RC_TEXT[rc_kind], encoding="utf-8")
    elif write_terminal:
        JOB.atomic_write_json(run_dir / (site + ".terminal.json"), {
            "schema_version": JOB.SCHEMA_VERSION, "site": site, "run_id": run_id,
            "attempt_nonce": witness_nonce, "terminal_at": _iso(now),
            "stdout_sha256": None, "stdout_bytes": 0, "stderr_bytes": 0,
        })
    return meta_payload


# ── ④ 派生纯函数：rc × liveness × 元数据 的**逐组合**归类 ─────────────────────

@pytest.mark.parametrize("rc_kind,liveness,meta_kind",
                         list(itertools.product(RC_KINDS, LIVENESS_KINDS, META_KINDS)))
def test_status_cartesian_classification(tmp_path, rc_kind, liveness, meta_kind):
    """rc 维度 × liveness 维度 × 元数据维度**逐组合**有确定性归类。

    参数化而非挑 happy path：本票的核心验收标准就是这张笛卡尔表。
    """
    run_dir = tmp_path / "20260725T000000Z-Zz99"
    run_dir.mkdir()
    now = time.time()
    _seed_site(run_dir, meta=meta_kind, rc_kind=rc_kind, now=now)
    payload = JOB.derive_status(run_dir, "design-voice", liveness=liveness, now=now)
    exp_state, exp_reason = _expected_classification(rc_kind, liveness, meta_kind)
    assert payload["state"] == exp_state, payload
    assert payload["reason_code"] == exp_reason, payload
    assert payload["terminal"] is (exp_state not in ("RESERVED", "STARTING", "RUNNING")), payload
    assert payload["ok"] is (exp_reason == "ok"), payload


def test_no_pending_lost_or_corrupt_combination_ever_yields_ok(tmp_path):
    """机械断言：全笛卡尔里「非 rc=0+非空 stdout」的组合产生 `reason_code="ok"` 的**数量为 0**。

    这是 design.md Non-Functional Requirements 的那条硬指标，MUST 是遍历断言而非 prose。
    """
    offenders = []
    ok_count = 0
    now = time.time()
    for idx, (rc_kind, liveness, meta_kind) in enumerate(
            itertools.product(RC_KINDS, LIVENESS_KINDS, META_KINDS)):
        run_dir = tmp_path / ("run-%03d" % idx)
        run_dir.mkdir()
        _seed_site(run_dir, meta=meta_kind, rc_kind=rc_kind, now=now)
        payload = JOB.derive_status(run_dir, "design-voice", liveness=liveness, now=now)
        legit = (meta_kind == "complete" and rc_kind == "rc0_nonempty")
        if payload["reason_code"] == "ok":
            ok_count += 1
            if not legit:
                offenders.append((rc_kind, liveness, meta_kind, payload["state"]))
    assert offenders == [], offenders
    # 正向对照：合法组合确实产出了 ok（否则「0 个 ok」可能只是因为**没有任何** ok）
    assert ok_count == len(LIVENESS_KINDS), ok_count


def test_liveness_never_overrides_a_published_rc(tmp_path):
    """ADR-2：`claude agents` 的 done/failed 只提供 liveness，MUST NOT 决定 ok/timeout。"""
    now = time.time()
    seen = set()
    for liveness in LIVENESS_KINDS:
        run_dir = tmp_path / ("rc-vs-%s" % liveness)
        run_dir.mkdir()
        _seed_site(run_dir, rc_kind="rc0_nonempty", now=now)
        payload = JOB.derive_status(run_dir, "design-voice", liveness=liveness, now=now)
        seen.add((payload["state"], payload["reason_code"]))
        assert payload["liveness"] is None, payload  # 终态站点根本不必探 liveness
    assert seen == {("SUCCEEDED", "ok")}, seen


def test_rc_recheck_before_declaring_lost_is_bounded_to_one_retry(monkeypatch, tmp_path):
    """判 LOST 前的「再看一眼 rc」是**一次性**的，MUST NOT 变成自递归。

    构造 rc 文件存在（`isfile` 为真）但读取口报「不存在」的错位——真实成因是
    rc 在 isfile 与 read 之间被移走。无界重入时这里直接 RecursionError。
    """
    run_dir = tmp_path / "20260725T190000Z-Rec001"
    run_dir.mkdir()
    now = time.time()
    _seed_site(run_dir, rc_kind="rc0_nonempty", now=now)
    monkeypatch.setattr(JOB, "read_rc", lambda *a, **k: (False, None, None))
    payload = JOB.derive_status(run_dir, "design-voice", liveness="done", now=now)
    assert (payload["state"], payload["reason_code"]) == ("LOST", "exec-error"), payload


# ── 终态前不读 stdout（机械锚：对读取口的 spy）────────────────────────────────

def test_status_never_reads_stdout_before_terminal(monkeypatch, tmp_path):
    """终态（rc 发布）之前 MUST NOT 读 stdout —— 半成品输出不得有任何进 findings 的路径。"""
    calls = []
    monkeypatch.setattr(JOB, "stdout_read_evidence",
                        lambda *a, **k: calls.append(("read", a)) or {})
    monkeypatch.setattr(JOB, "stdout_stat_evidence",
                        lambda *a, **k: calls.append(("stat", a)) or {"bytes": 0, "exists": False})
    for liveness in LIVENESS_KINDS:
        run_dir = tmp_path / ("pending-%s" % liveness)
        run_dir.mkdir()
        _seed_site(run_dir, rc_kind="absent")
        (run_dir / "design-voice.stdout").write_bytes(b"HALF WRITTEN FINDINGS\n")
        JOB.derive_status(run_dir, "design-voice", liveness=liveness)
    assert calls == [], calls


def test_status_stats_stdout_size_but_never_reads_its_content(monkeypatch, tmp_path):
    """终态后 status 只需要「stdout 是否非空」⇒ stat 即可，MUST NOT 把正文读进来。"""
    reads = []
    monkeypatch.setattr(JOB, "stdout_read_evidence", lambda *a, **k: reads.append(a) or {})
    run_dir = tmp_path / "terminal"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="rc0_nonempty")
    payload = JOB.derive_status(run_dir, "design-voice", liveness="done")
    assert payload["state"] == "SUCCEEDED"
    assert reads == [], reads


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0,
                    reason="root 绕过文件权限，chmod 000 的负向探针在 root 下无判别力")
def test_status_of_a_running_site_survives_an_unreadable_stdout(tmp_path):
    """独立于 spy 的第二条锚：stdout 完全读不动时，未终态站点的归类照常成立。"""
    run_dir = tmp_path / "unreadable"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent")
    out = run_dir / "design-voice.stdout"
    out.write_bytes(b"HALF WRITTEN\n")
    out.chmod(0o000)
    try:
        payload = JOB.derive_status(run_dir, "design-voice", liveness="working")
        assert (payload["state"], payload["reason_code"]) == ("RUNNING", None), payload
    finally:
        out.chmod(0o600)


# ── 独立的 startup deadline vs 从可信 started_at 起算的 worker 上界 ──────────

def test_startup_deadline_is_independent_of_the_worker_deadline(tmp_path):
    """started sidecar 未发布 ⇒ 只受**独立**的 startup deadline 约束（非 worker timeout）。"""
    now = time.time()
    fresh = tmp_path / "fresh"
    fresh.mkdir()
    _seed_site(fresh, rc_kind="absent", write_started=False, now=now,
               startup_deadline_ago=-3)          # startup deadline 还在未来
    assert JOB.derive_status(fresh, "design-voice", liveness="working", now=now)["state"] == "STARTING"

    stale = tmp_path / "stale"
    stale.mkdir()
    _seed_site(stale, rc_kind="absent", write_started=False, now=now,
               startup_deadline_ago=1)           # startup deadline 已过
    payload = JOB.derive_status(stale, "design-voice", liveness="working", now=now)
    assert (payload["state"], payload["reason_code"]) == ("LOST", "exec-error"), payload


def test_worker_upper_bound_counts_from_trusted_started_at_plus_grace(tmp_path):
    """worker 上界 = 可信 `started_at` + timeout + 30 秒 grace，**不是**从 dispatch 时刻起算。

    排队 300 秒才启动的合法 worker：若从 dispatch 时刻起算，它在 timeout 到点时就被误杀；
    从 started_at 起算则仍在预算内。这里 dispatch 已过 400 秒、started 才过 10 秒、timeout=60。
    """
    now = time.time()
    queued = tmp_path / "queued"
    queued.mkdir()
    _seed_site(queued, rc_kind="absent", now=now, dispatched_ago=400, started_ago=10,
               timeout_seconds=60)
    payload = JOB.derive_status(queued, "design-voice", liveness="working", now=now)
    assert (payload["state"], payload["reason_code"]) == ("RUNNING", None), payload

    # 恰好越过 started_at + timeout + grace 才归 LOST（且**不是** timeout）
    over = tmp_path / "over"
    over.mkdir()
    _seed_site(over, rc_kind="absent", now=now, dispatched_ago=400,
               started_ago=60 + JOB.AWAIT_GRACE_SECONDS + 1, timeout_seconds=60)
    payload = JOB.derive_status(over, "design-voice", liveness="working", now=now)
    assert (payload["state"], payload["reason_code"]) == ("LOST", "exec-error"), payload
    assert payload["reason_code"] != "timeout"


def test_deadline_uses_the_timeout_override_when_given(tmp_path):
    now = time.time()
    run_dir = tmp_path / "override"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent", now=now, started_ago=100, timeout_seconds=900)
    assert JOB.derive_status(run_dir, "design-voice", liveness="working", now=now,
                             timeout_override=1)["state"] == "LOST"
    assert JOB.derive_status(run_dir, "design-voice", liveness="working", now=now,
                             timeout_override=900)["state"] == "RUNNING"


def test_liveness_probe_failure_does_not_declare_the_worker_lost(tmp_path):
    """探针本身取不到答案 ≠ job 丢了 —— 无判别力的探针 MUST NOT 触发降级。"""
    now = time.time()
    run_dir = tmp_path / "probe-down"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent", now=now)
    payload = JOB.derive_status(run_dir, "design-voice", liveness="unavailable", now=now)
    assert (payload["state"], payload["reason_code"]) == ("RUNNING", None), payload


def test_unknown_agent_state_is_inconclusive_not_terminal(tmp_path):
    """agents JSON 的 state 枚举漂移 ⇒ 保守当「探不到」，MUST NOT 当成 job 已终态而误降级。"""
    now = time.time()
    run_dir = tmp_path / "drift"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent", now=now)
    payload = JOB.derive_status(run_dir, "design-voice", liveness="hibernating", now=now)
    assert (payload["state"], payload["reason_code"]) == ("RUNNING", None), payload


def test_reserve_without_job_metadata_is_reserved_and_never_collectable(tmp_path):
    run_dir = tmp_path / "reserved"
    run_dir.mkdir()
    (run_dir / "design-voice.reserve").write_text("{}", encoding="utf-8")
    payload = JOB.derive_status(run_dir, "design-voice", liveness="working")
    assert payload["state"] == "RESERVED"
    assert payload["reason_code"] is None
    assert payload["terminal"] is False
    assert payload["unknown_cost"] is True


def test_site_with_nothing_on_disk_is_exec_error_never_ok(tmp_path):
    run_dir = tmp_path / "nothing"
    run_dir.mkdir()
    payload = JOB.derive_status(run_dir, "design-voice", liveness="missing")
    assert (payload["state"], payload["reason_code"]) == ("MISSING", "exec-error"), payload


def test_terminal_rc_without_a_terminal_witness_is_corrupt(tmp_path):
    run_dir = tmp_path / "no-witness"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="rc0_nonempty", write_terminal=False)
    payload = JOB.derive_status(run_dir, "design-voice", liveness="done")
    assert (payload["state"], payload["reason_code"]) == ("CORRUPT", "exec-error"), payload


def test_witness_attempt_nonce_mismatch_is_corrupt(tmp_path):
    """上一轮遗留的 witness 混进本轮 run dir ⇒ identity 核不过，MUST NOT 当本次结果采信。"""
    run_dir = tmp_path / "stale-witness"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="rc0_nonempty", nonce_in_witness="someone-elses-nonce")
    payload = JOB.derive_status(run_dir, "design-voice", liveness="done")
    assert (payload["state"], payload["reason_code"]) == ("CORRUPT", "exec-error"), payload


# ── ③ CLI 契约 ────────────────────────────────────────────────────────────────

def _fixed_roster(job_id="75d34378", state="working", cwd=None):
    """单条 roster 条目。`cwd=None` ⇒ **不带 cwd 键**（repo 维度「探不到」而非「不符」）。

    默认省略 cwd 是刻意的：这些用例只在钉 rc × liveness 的归类，不该顺带把
    repo 交叉核验也一起断言掉。带 cwd 的正/负向锚单列在 Task 3 段。
    """
    entry = {"id": job_id, "kind": "background", "startedAt": 1784974140034,
             "sessionId": job_id + "-sess", "state": state}
    if cwd is not None:
        entry["cwd"] = cwd
    if state != "done":
        entry["name"] = "python3 outside-voice-job.py worker …"
    return json.dumps([entry])


def _site_args(cmd, run_dir, site="design-voice", *extra):
    return [cmd, "--run-dir", str(run_dir), "--site", site, *extra]


def test_status_cli_emits_single_line_json_for_a_running_site(job_home, fake_claude, tmp_path):
    run_dir = tmp_path / "20260725T010000Z-Cli001"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent")
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _fixed_roster()})
    started = time.monotonic()
    proc = _run_job(job_home, _site_args("status", run_dir), env)
    elapsed = time.monotonic() - started
    payload = _json_stdout(proc)
    assert proc.returncode == 1                       # 非 ok ⇒ 非零；分类看 JSON
    assert proc.stdout.strip().count("\n") == 0       # 单行 JSON
    assert payload["state"] == "RUNNING"
    assert payload["reason_code"] is None
    assert payload["terminal"] is False
    assert payload["liveness"] == "working"
    assert payload["job_id"] == "75d34378"
    assert elapsed < 5, elapsed                        # 单次 status 查询 ≤5 秒（NFR）


@pytest.mark.parametrize("rc_kind", RC_KINDS)
@pytest.mark.parametrize("meta_kind", META_KINDS)
def test_status_cli_is_a_thin_shell_over_derive_status(job_home, fake_claude, tmp_path,
                                                       rc_kind, meta_kind):
    """CLI 与派生函数 MUST 同一个真相源——否则笛卡尔表只证明了那个没人调用的函数。"""
    run_dir = tmp_path / "20260725T020000Z-Thin01"
    run_dir.mkdir()
    _seed_site(run_dir, meta=meta_kind, rc_kind=rc_kind)
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _fixed_roster()})
    proc = _run_job(job_home, _site_args("status", run_dir), env)
    cli = _json_stdout(proc)
    direct = JOB.derive_status(run_dir, "design-voice", liveness="working")
    assert cli == direct, (cli, direct)
    assert proc.returncode == (0 if cli["ok"] else 1)


@pytest.mark.parametrize("agent_state,expected", [
    ("working", "RUNNING"), ("done", "LOST"), ("failed", "LOST"), ("stopped", "LOST"),
])
def test_status_cli_maps_real_agent_states_through_the_id_channel(job_home, fake_claude,
                                                                  tmp_path, agent_state, expected):
    """liveness 走 **id** 通道匹配：`state="done"` 的条目没有 `name`（真机实测，Task 1）。"""
    run_dir = tmp_path / "20260725T030000Z-Live01"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent")
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _fixed_roster(state=agent_state)})
    payload = _json_stdout(_run_job(job_home, _site_args("status", run_dir), env))
    assert payload["state"] == expected, payload
    assert payload["liveness"] == agent_state
    assert payload["reason_code"] != "timeout"


def test_status_cli_reports_missing_when_job_id_absent_from_roster(job_home, fake_claude, tmp_path):
    run_dir = tmp_path / "20260725T040000Z-Miss01"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent")
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "empty"})
    payload = _json_stdout(_run_job(job_home, _site_args("status", run_dir), env))
    assert payload["liveness"] == "missing"
    assert (payload["state"], payload["reason_code"]) == ("LOST", "exec-error"), payload


def test_status_cli_treats_unreachable_agents_cli_as_inconclusive(job_home, fake_claude, tmp_path):
    run_dir = tmp_path / "20260725T050000Z-Down01"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent")
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "disabled"})
    payload = _json_stdout(_run_job(job_home, _site_args("status", run_dir), env))
    assert payload["liveness"] == "unavailable"
    assert (payload["state"], payload["reason_code"]) == ("RUNNING", None), payload


# ── collect ───────────────────────────────────────────────────────────────────

def test_collect_returns_structured_machine_readable_evidence(job_home, fake_claude, tmp_path):
    run_dir = tmp_path / "20260725T060000Z-Col001"
    run_dir.mkdir()
    now = time.time()
    _seed_site(run_dir, rc_kind="rc0_nonempty", now=now, dispatched_ago=930, started_ago=920)
    proc = _run_job(job_home, _site_args("collect", run_dir), _env(fake_claude))
    payload = _json_stdout(proc)
    assert proc.returncode == 0, proc.stderr
    assert payload["ok"] is True
    assert payload["reason_code"] == "ok"
    assert payload["state"] == "SUCCEEDED"
    for field in ("dispatched_at", "started_at", "terminal_at", "collected_at",
                  "duration_seconds", "runner", "model", "effort", "stdout_sha256",
                  "stdout_bytes", "stdout_lines", "stderr_bytes", "rc", "job_id",
                  "attempt_nonce", "timeout_seconds"):
        assert field in payload and payload[field] is not None, field
    assert payload["runner"] == "claude"
    assert payload["model"] == "opus"
    assert payload["effort"] == "high"
    assert payload["rc"] == 0
    # 自然耗时 = terminal_at − started_at（不是墙钟外壳，也不是 dispatch 起算）
    assert 900 < payload["duration_seconds"] < 940, payload["duration_seconds"]
    assert payload["stdout_sha256"] == hashlib.sha256(
        (run_dir / "design-voice.stdout").read_bytes()).hexdigest()
    assert payload["stdout_path"] == str((run_dir / "design-voice.stdout").resolve())
    # stderr 只出结构化计数，MUST NOT 转录正文
    assert "fake-stderr" not in json.dumps(payload, ensure_ascii=False)
    assert payload["stderr_bytes"] == len(b"fake-stderr\n")


def test_collect_is_idempotent_byte_for_byte(job_home, fake_claude, tmp_path):
    run_dir = tmp_path / "20260725T070000Z-Idem01"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="rc0_nonempty")
    first = _run_job(job_home, _site_args("collect", run_dir), _env(fake_claude))
    time.sleep(1.1)                                  # 保证「重算」会得到不同的 collected_at
    second = _run_job(job_home, _site_args("collect", run_dir), _env(fake_claude))
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout, (first.stdout, second.stdout)
    assert json.loads(first.stdout)["collected_at"] == json.loads(second.stdout)["collected_at"]


def test_collect_before_terminal_is_not_ok_and_leaks_no_partial_output(job_home, fake_claude,
                                                                       tmp_path):
    """「起了没收」MUST NOT 读作成功——未终态站点没有任何进 findings 的通道。

    ⚠️ 命名边界（反向变异实测）：本条**不是**「有没有读过 stdout」的判别器——把读取
    提前到 rc 判定之前，本条照样绿。「终态前不读」的锚是
    `test_status_never_reads_stdout_before_terminal`（对读取口的 spy）。
    本条守的是**出口**：未终态时 collect 不给 stdout_path、不落 collected witness、
    不把半成品正文带进自己的 stdout。
    """
    run_dir = tmp_path / "20260725T080000Z-Early1"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent")
    (run_dir / "design-voice.stdout").write_bytes(b"PARTIAL FINDINGS: looks fine!\n")
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _fixed_roster()})
    proc = _run_job(job_home, _site_args("collect", run_dir), env)
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["ok"] is False
    assert payload["reason_code"] is None
    assert payload["state"] == "RUNNING"
    assert "PARTIAL FINDINGS" not in proc.stdout
    assert "stdout_path" not in payload
    assert not (run_dir / "design-voice.collected.json").exists()


@pytest.mark.parametrize("rc_kind,reason", [
    ("rc124", "timeout"), ("rc3", "secret-hit"), ("rc_other", "exec-error"),
    ("rc_bad", "exec-error"), ("rc0_empty", "exec-error"),
])
def test_collect_rc_to_reason_code_table(job_home, fake_claude, tmp_path, rc_kind, reason):
    run_dir = tmp_path / "20260725T090000Z-Rc0001"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind=rc_kind)
    proc = _run_job(job_home, _site_args("collect", run_dir), _env(fake_claude))
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["reason_code"] == reason, payload
    assert "stdout_path" not in payload            # 非 ok ⇒ 输出不得进 findings 池


def test_collect_detects_a_stdout_digest_mismatch(job_home, fake_claude, tmp_path):
    """terminal witness 的 digest 与实际 stdout 不符 ⇒ 证据被动过，fail-closed。"""
    run_dir = tmp_path / "20260725T100000Z-Dig001"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="rc0_nonempty", terminal_digest="f" * 64)
    proc = _run_job(job_home, _site_args("collect", run_dir), _env(fake_claude))
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert (payload["state"], payload["reason_code"]) == ("CORRUPT", "exec-error"), payload


def test_collect_does_not_freeze_a_lost_verdict_reached_before_rc_was_published(
        job_home, fake_claude, tmp_path):
    """LOST 是**非 durable 证据**推出的终态 ⇒ MUST NOT 被 collected witness 冻结。

    幂等的边界是 design.md 的 Global Constraint：「**terminal rc 之后** collect 幂等」。
    rc 之前的终态（LOST / RESERVED）只是「此刻探不到」，把它落成不可变见证，
    等于把一次**已经计费**的 voice 在 worker 真跑完之前就永久丢弃。
    """
    run_dir = tmp_path / "20260725T113000Z-Lost01"
    run_dir.mkdir()
    now = time.time()
    # startup deadline 已过 + 无 started sidecar ⇒ 第一次 collect 判 LOST
    _seed_site(run_dir, rc_kind="absent", now=now, write_started=False,
               startup_deadline_ago=5)
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _fixed_roster()})
    first = _run_job(job_home, _site_args("collect", run_dir), env)
    first_payload = _json_stdout(first)
    assert first.returncode == 1
    assert (first_payload["state"], first_payload["reason_code"]) == ("LOST", "exec-error"), \
        first_payload
    assert not (run_dir / "design-voice.collected.json").exists(), \
        "rc 尚未发布的 LOST 判定 MUST NOT 落成不可变见证"

    # worker 其实只是慢：随后真正发布 started → terminal → rc=0 + 真实 findings
    _seed_site(run_dir, rc_kind="rc0_nonempty", now=time.time(), write_job=False,
               stdout=b"REAL FINDINGS: the voice did land\n")
    second = _run_job(job_home, _site_args("collect", run_dir), env)
    second_payload = _json_stdout(second)
    assert second.returncode == 0, second.stdout
    assert (second_payload["state"], second_payload["reason_code"]) == ("SUCCEEDED", "ok"), \
        second_payload
    assert second_payload["stdout_path"] == str((run_dir / "design-voice.stdout").resolve())
    assert second_payload["stdout_sha256"] == hashlib.sha256(
        b"REAL FINDINGS: the voice did land\n").hexdigest()
    # 真终态（rc 已发布）之后才冻结 —— 幂等仍然成立
    assert (run_dir / "design-voice.collected.json").exists()
    third = _run_job(job_home, _site_args("collect", run_dir), env)
    assert third.stdout == second.stdout


def test_collect_refuses_to_reuse_a_collected_witness_from_another_attempt(job_home, fake_claude,
                                                                          tmp_path):
    run_dir = tmp_path / "20260725T110000Z-Wit001"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="rc0_nonempty")
    JOB.atomic_write_json(run_dir / "design-voice.collected.json", {
        "schema_version": JOB.SCHEMA_VERSION, "site": "design-voice",
        "run_id": run_dir.name, "attempt_nonce": "not-this-attempt",
        "ok": True, "reason_code": "ok", "state": "SUCCEEDED",
    })
    proc = _run_job(job_home, _site_args("collect", run_dir), _env(fake_claude))
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["reason_code"] == "exec-error", payload


# ── await ─────────────────────────────────────────────────────────────────────

def test_await_waits_for_a_real_rc_and_never_early_timeouts(job_home, fake_claude, tmp_path):
    """站点仍 RUNNING 时有界 await 不早退、不落 timeout（HAE-09 的 barrier 语义）。"""
    run_dir = tmp_path / "20260725T120000Z-Awa001"
    run_dir.mkdir()
    now = time.time()
    _seed_site(run_dir, rc_kind="absent", now=now, timeout_seconds=60)

    def publish_later():
        time.sleep(1.5)
        _seed_site(run_dir, rc_kind="rc0_nonempty", now=time.time(), write_job=False,
                   write_started=False)

    worker = threading.Thread(target=publish_later)
    worker.start()
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _fixed_roster()})
    started = time.monotonic()
    proc = _run_job(job_home, _site_args("await", run_dir, "design-voice",
                                         "--poll-interval", "0.2"), env, timeout=60)
    elapsed = time.monotonic() - started
    worker.join()
    payload = _json_stdout(proc)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert payload["reason_code"] == "ok", payload
    assert elapsed >= 1.4, elapsed                    # 真的等到了 rc，而不是早退
    assert payload["waited_seconds"] >= 1.4, payload


def test_await_exhausting_max_wait_stays_running_and_is_not_timeout(job_home, fake_claude, tmp_path):
    run_dir = tmp_path / "20260725T130000Z-Awa002"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent", timeout_seconds=900)
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _fixed_roster()})
    started = time.monotonic()
    proc = _run_job(job_home, _site_args("await", run_dir, "design-voice",
                                         "--max-wait", "1", "--poll-interval", "0.2"),
                    env, timeout=60)
    elapsed = time.monotonic() - started
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["state"] == "RUNNING", payload
    assert payload["reason_code"] is None, payload    # 🔴 MUST NOT 落 timeout
    assert payload["terminal"] is False
    assert 1 <= elapsed < 20, elapsed


def test_await_declares_lost_after_started_plus_timeout_plus_grace(job_home, fake_claude, tmp_path):
    run_dir = tmp_path / "20260725T140000Z-Awa003"
    run_dir.mkdir()
    now = time.time()
    _seed_site(run_dir, rc_kind="absent", now=now, dispatched_ago=1000,
               started_ago=1 + JOB.AWAIT_GRACE_SECONDS + 1, timeout_seconds=1)
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _fixed_roster()})
    started = time.monotonic()
    proc = _run_job(job_home, _site_args("await", run_dir, "design-voice",
                                         "--poll-interval", "0.2"), env, timeout=60)
    elapsed = time.monotonic() - started
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert (payload["state"], payload["reason_code"]) == ("LOST", "exec-error"), payload
    assert elapsed < 20, elapsed                      # 有界：不等满 900 秒


def test_await_returns_immediately_when_the_job_is_gone(job_home, fake_claude, tmp_path):
    """supervisor/job 丢失不是 timeout，且 MUST NOT 等满 timeout。"""
    run_dir = tmp_path / "20260725T150000Z-Awa004"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent", timeout_seconds=900)
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "empty"})
    started = time.monotonic()
    proc = _run_job(job_home, _site_args("await", run_dir, "design-voice"), env, timeout=60)
    elapsed = time.monotonic() - started
    payload = _json_stdout(proc)
    assert (payload["state"], payload["reason_code"]) == ("LOST", "exec-error"), payload
    assert payload["reason_code"] != "timeout"
    assert elapsed < 20, elapsed


def test_await_on_a_bare_reservation_does_not_spin_forever(job_home, fake_claude, tmp_path):
    """RESERVED（unknown-cost）永远不会自行到达终态 ⇒ 有界 await MUST 立即返回交给 reconcile。"""
    run_dir = tmp_path / "20260725T160000Z-Awa005"
    run_dir.mkdir()
    (run_dir / "design-voice.reserve").write_text("{}", encoding="utf-8")
    started = time.monotonic()
    proc = _run_job(job_home, _site_args("await", run_dir), _env(fake_claude), timeout=60)
    elapsed = time.monotonic() - started
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["state"] == "RESERVED"
    assert payload["unknown_cost"] is True
    assert elapsed < 20, elapsed


def test_await_throttles_the_liveness_probe_far_below_the_poll_rate(job_home, fake_claude,
                                                                    tmp_path):
    """盘面读（本地 stat）可以 0.5 秒一轮，但 `claude agents` 是**外部进程冷启动**。

    每轮都 spawn 一次 ⇒ 上界 timeout(3600)+grace 的 await 能烧掉数千次 Node 冷启动
    （每次实测 0.17 秒，CLI 卡顿时吃满 5 秒探针超时）。**探针 MUST 独立节流**：
    盘面照常密集轮询，liveness 复用上次结果。
    """
    run_dir = tmp_path / "20260725T171500Z-Thr001"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent", timeout_seconds=900)
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _fixed_roster()})
    proc = _run_job(job_home, _site_args("await", run_dir, "design-voice",
                                         "--max-wait", "1.2", "--poll-interval", "0.05"),
                    env, timeout=60)
    payload = _json_stdout(proc)
    assert payload["state"] == "RUNNING", payload
    assert payload["liveness"] == "working", payload      # 仍然真的探过，不是假绿
    probes = [i for i in _invocations(fake_claude) if i["argv"][:1] == ["agents"]]
    polls = payload["waited_seconds"] / 0.05
    assert polls >= 10, polls                              # 盘面确实密集轮询过
    assert len(probes) * 4 < polls, (len(probes), polls)   # 探针远少于轮询次数
    assert len(probes) <= 1 + payload["waited_seconds"] / JOB.LIVENESS_PROBE_INTERVAL_SECONDS + 1, \
        (len(probes), payload["waited_seconds"])
    assert JOB.LIVENESS_PROBE_INTERVAL_SECONDS >= 5


@pytest.mark.parametrize("timeout", ["0", "3601", "abc", "-1"])
def test_await_rejects_out_of_range_timeout(job_home, fake_claude, tmp_path, timeout):
    """超时上限复用既有 async timeout 配置项的合法范围 1..3600（越界即拒）。"""
    run_dir = tmp_path / "20260725T170000Z-Awa006"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent")
    proc = _run_job(job_home, _site_args("await", run_dir, "design-voice",
                                         "--timeout", timeout), _env(fake_claude), timeout=60)
    assert proc.returncode != 0


def test_await_default_upper_bound_comes_from_job_metadata_timeout(job_home, fake_claude, tmp_path):
    """默认上界取 dispatch 时记进 job.json 的 `timeout_seconds`（= 既有 async 配置项的值），
    MUST NOT 在本 helper 里另造一份 config 解析。"""
    run_dir = tmp_path / "20260725T180000Z-Awa007"
    run_dir.mkdir()
    now = time.time()
    _seed_site(run_dir, rc_kind="absent", now=now, dispatched_ago=1000, started_ago=940,
               timeout_seconds=JOB.DEFAULT_TIMEOUT_SECONDS)
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _fixed_roster()})
    # started_ago=940 > 900+30 ⇒ 默认上界（900）已越，立即 LOST
    payload = _json_stdout(_run_job(job_home, _site_args("await", run_dir), env, timeout=60))
    assert (payload["state"], payload["reason_code"]) == ("LOST", "exec-error"), payload
    assert payload["timeout_seconds"] == JOB.DEFAULT_TIMEOUT_SECONDS


@pytest.mark.parametrize("cmd", ["status", "await", "collect"])
def test_readonly_usage_error_exits_2_and_is_documented_in_the_contract_source(
        job_home, fake_claude, tmp_path, cmd):
    """三个只读子命令的 usage-error 走 **exit 2** 且 payload 是 reject 形状（**无 `terminal` 键**）。

    模块 docstring 自称「契约单一源（两份评审 SKILL 只引用本注释）」⇒ 它漏写 exit 2
    就是契约与实现不符：调用方会按「0|1」两分法把 2 当成「非 ok 的正常分类」，
    再去读一个根本不存在的 `terminal`。
    """
    run_dir = tmp_path / ("20260725T200000Z-Usg-" + cmd)
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent")
    proc = _run_job(job_home, _site_args(cmd, run_dir, "design-voice", "--timeout", "9999"),
                    _env(fake_claude), timeout=60)
    payload = _json_stdout(proc)
    assert proc.returncode == 2, (proc.returncode, proc.stdout)
    assert payload["state"] == "usage-error", payload
    assert payload["ok"] is False
    assert "terminal" not in payload, payload
    assert JOB.__doc__.count("2=usage-error") >= 3, "契约单一源 MUST 逐子命令写明 exit 2"


def test_default_timeout_and_range_are_the_single_shared_constants():
    """默认 900、范围 1..3600 —— 与 dispatch 共用同一组常量，不新增第二份口径。"""
    assert JOB.DEFAULT_TIMEOUT_SECONDS == 900
    assert (JOB.MIN_TIMEOUT_SECONDS, JOB.MAX_TIMEOUT_SECONDS) == (1, 3600)
    assert JOB.AWAIT_GRACE_SECONDS == 30


# ── dispatch → worker → await → collect 全链（离线，无真 claude）──────────────

def test_dispatch_worker_await_collect_end_to_end_offline(fake_job_home, fake_claude, repo):
    """本票的端到端接缝：Task 1 真写出来的盘面，MUST 能被 Task 2 的 await/collect 认。"""
    env = _env(fake_claude, {
        "FAKE_CLAUDE_BG_MODE": "run",
        "FAKE_CLAUDE_JOB_ID": "abc12345",
        "FAKE_HELPER_MARKER": "e2e",
        "FAKE_HELPER_SLEEP": "1",
    })
    proc = _run_job(fake_job_home, _dispatch_args(repo, fake_job_home), env)
    assert proc.returncode == 0, proc.stderr

    awaited = _json_stdout(_run_job(fake_job_home,
                                    _site_args("await", repo["run_dir"], "design-voice",
                                               "--poll-interval", "0.2"),
                                    env, timeout=120))
    assert awaited["reason_code"] == "ok", awaited
    collected = _json_stdout(_run_job(fake_job_home,
                                      _site_args("collect", repo["run_dir"]), env, timeout=60))
    assert collected["ok"] is True, collected
    assert collected["runner"] == "claude" and collected["model"] == "opus"
    assert collected["effort"] == "high"
    assert collected["duration_seconds"] >= 0
    assert collected["stdout_sha256"] == hashlib.sha256(
        (repo["run_dir"] / "design-voice.stdout").read_bytes()).hexdigest()


# ══════════════════════════════════════════════════════════════════════════════
# Task 3：中断恢复与 identity-safe 清理（OVBG-03 / OVBG-05）
#
# TDD 接缝（先定后写，测试只打这三处）：
#   ⑤ **子命令 CLI 契约**：`cleanup` / `reconcile` 的 argv、stdout 单行 JSON
#      （`state` / `stopped` / `removed` / `subtree` / `orphan_warning` /
#      `unknown_cost` / `fallback_allowed` / `identity`）与退出码。
#   ⑥ **进程子树核验纯函数契约**：`JOB.probe_subtree(run_dir, site, job)` 的三值判定
#      （exited / alive / unverifiable）与两个 syscall 探针 `_pid_alive` / `_pgid_alive`。
#   ⑦ **破坏性调用的负向锚**：identity 核不过时，fake `claude` 的调用日志里
#      **零** `stop` / `rm` —— 「不猜目标」是日志上的机械事实，不是实现自述。
# ══════════════════════════════════════════════════════════════════════════════


def _roster(*entries):
    """按需拼 roster：只写给定的键，`None` 表示**该键不存在**（真 CLI 的 done 条目无 name）。"""
    out = []
    for item in entries:
        entry = {"id": item["id"], "kind": item.get("kind", "background"),
                 "startedAt": 1784974140034, "sessionId": item["id"] + "-sess",
                 "state": item.get("state", "working")}
        for key in ("cwd", "name"):
            if item.get(key) is not None:
                entry[key] = item[key]
        out.append(entry)
    return json.dumps(out)


def _worker_name(site="design-voice", nonce="0" * 32):
    """真 roster 条目的 `name` 承载完整 worker 命令串（Task 1 已实测）。"""
    return ("/usr/bin/python3 /x/outside-voice-job.py worker --run-dir /x/run "
            "--site %s --context-file /x/ctx.md --repo-root /x --runner claude "
            "--model opus --effort high --timeout 900 --attempt-nonce %s --run-id r1"
            % (site, nonce))


def _detached_sleeper(seconds=30):
    """起一个**被 init 收养**的真进程 → 返回 pid。

    收养是关键：它被杀之后立刻被 init 回收，不会以 zombie 形态继续让
    `os.kill(pid, 0)` 成功 —— 否则「子树已退出」的探针会被僵尸骗过去。
    """
    out = subprocess.run(["sh", "-c", "sleep %d >/dev/null 2>&1 & echo $!" % seconds],
                         capture_output=True, text=True, timeout=10)
    return int(out.stdout.strip())


def _dead_pid():
    """拿一个**确定已不存在**的 pid（起一个立刻退出的被收养进程，等它消失）。"""
    pid = _detached_sleeper(0)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return pid
        except PermissionError:            # pid 已被别人复用 ⇒ 换一个
            break
        time.sleep(0.02)
    pytest.skip("拿不到一个确定已死的 pid（本机 pid 回绕过快）")


def _destructive(fake_claude):
    """fake `claude` 日志里所有 `stop` / `rm` 调用的 (action, target) 序列。"""
    return [(i["argv"][0], i["argv"][1] if len(i["argv"]) > 1 else None)
            for i in _invocations(fake_claude) if i["argv"][:1] in (["stop"], ["rm"])]


# ── 交接①：LOST 路径 MUST 翻 unknown_cost / orphan_warning ────────────────────

def test_every_lost_verdict_flags_unknown_cost_and_an_orphan_warning(tmp_path):
    """三条 LOST 产生路径**无一例外**都要翻 `unknown_cost` + `orphan_warning`。

    OVBG-03：「无法证明子树已退出时 SHALL 标记 unknown-cost/orphan-warning 并抑制自动
    fallback」。LOST 的定义就是「rc 缺席」⇒ 盘面上根本没有 terminal witness ⇒
    子树是否退出**未经核验**。此时若照常同族 fallback，就是在一次已计费的 voice 之上
    再叠一次费用。核验只能由 cleanup/reconcile（会真探进程树）来做。
    """
    now = time.time()
    cases = {}

    # ① liveness 终态且无 rc
    a = tmp_path / "lost-liveness"
    a.mkdir()
    _seed_site(a, rc_kind="absent", now=now)
    cases["liveness-terminal"] = JOB.derive_status(a, "design-voice", liveness="done", now=now)

    # ② startup deadline 已过且无 started sidecar
    b = tmp_path / "lost-startup"
    b.mkdir()
    _seed_site(b, rc_kind="absent", now=now, write_started=False, startup_deadline_ago=5)
    cases["startup-deadline"] = JOB.derive_status(b, "design-voice", liveness="working", now=now)

    # ③ 可信 started_at + timeout + grace 已过且无 rc
    c = tmp_path / "lost-deadline"
    c.mkdir()
    _seed_site(c, rc_kind="absent", now=now, dispatched_ago=1000,
               started_ago=1 + JOB.AWAIT_GRACE_SECONDS + 5, timeout_seconds=1)
    cases["started-plus-grace"] = JOB.derive_status(c, "design-voice", liveness="working", now=now)

    for label, payload in cases.items():
        assert payload["state"] == "LOST", (label, payload)
        assert payload["unknown_cost"] is True, (label, payload)
        assert payload["orphan_warning"], (label, payload)
        assert "cleanup" in payload["orphan_warning"], (label, payload)


def test_states_other_than_lost_and_reserved_never_raise_a_false_orphan_warning(tmp_path):
    """正向对照：真终态（rc 已发布）与在飞状态 MUST NOT 被顺手标成 orphan。

    没有这一条，「LOST 翻 unknown_cost」可以靠「所有状态都翻」来假绿，
    而那会把每一次正常成功也变成「禁止 fallback」。
    """
    now = time.time()
    expected = {"rc0_nonempty": "SUCCEEDED", "rc124": "TIMED_OUT",
                "rc3": "FAILED", "rc_other": "FAILED"}
    for rc_kind, state in expected.items():
        run_dir = tmp_path / ("clean-" + rc_kind)
        run_dir.mkdir()
        _seed_site(run_dir, rc_kind=rc_kind, now=now)
        payload = JOB.derive_status(run_dir, "design-voice", liveness="done", now=now)
        assert payload["state"] == state, payload
        assert payload["unknown_cost"] is False, payload
        assert payload["orphan_warning"] is None, payload

    running = tmp_path / "clean-running"
    running.mkdir()
    _seed_site(running, rc_kind="absent", now=now)
    payload = JOB.derive_status(running, "design-voice", liveness="working", now=now)
    assert (payload["state"], payload["unknown_cost"], payload["orphan_warning"]) \
        == ("RUNNING", False, None), payload


# ── 外层 await 被回收后的恢复（不丢结果、不重派）──────────────────────────────

def test_reclaimed_await_recovers_by_collect_without_a_second_dispatch(
        fake_job_home, fake_claude, repo):
    """外层 await 被回收 ⇒ 同一 run-dir/站点重新 collect 即可拿回结果，且**不重派**。

    机械锚是 fake `claude` 的调用日志：整个恢复过程里 `--bg --exec` 的次数恒为 1。
    """
    env = _env(fake_claude, {
        "FAKE_CLAUDE_BG_MODE": "run",
        "FAKE_CLAUDE_JOB_ID": "abc12345",
        "FAKE_HELPER_MARKER": "reclaimed",
        "FAKE_HELPER_SLEEP": "2",
    })
    dispatched = _json_stdout(_run_job(fake_job_home, _dispatch_args(repo, fake_job_home), env))
    assert dispatched["ok"] is True, dispatched

    # 外层 shell 只等了很短一会儿就被回收
    reclaimed = _json_stdout(_run_job(
        fake_job_home,
        _site_args("await", repo["run_dir"], "design-voice", "--max-wait", "0.3",
                   "--poll-interval", "0.1"),
        env, timeout=60))
    assert reclaimed["terminal"] is False, reclaimed

    # worker 由 supervisor 托管继续跑到终态
    rc_path = repo["run_dir"] / "design-voice.rc"
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline and not rc_path.exists():
        time.sleep(0.2)
    assert rc_path.exists()

    recovered = _json_stdout(_run_job(fake_job_home,
                                      _site_args("collect", repo["run_dir"]), env, timeout=60))
    assert recovered["ok"] is True, recovered
    assert recovered["state"] == "SUCCEEDED", recovered
    assert "fake-helper-stdout reclaimed" in (repo["run_dir"] / "design-voice.stdout").read_text(
        encoding="utf-8")
    assert len(_bg_invocations(fake_claude)) == 1, _bg_invocations(fake_claude)


def test_status_liveness_probe_degrades_when_the_roster_entry_belongs_to_another_repo(
        job_home, fake_claude, tmp_path):
    """id 命中但 repo 对不上 ⇒ 那不是我们的 job，liveness 降级为「探不到」。

    降到 `unavailable` 而不是 `missing` 是刻意的：`missing` 会立刻把一个**还在飞的**
    合法 worker 判成 LOST。探针无判别力 MUST NOT 触发降级（与 LIVENESS_TERMINAL 同口径）。
    """
    run_dir = tmp_path / "20260726T010000Z-Rep001"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent", repo_root=str(tmp_path / "repo-A"))
    env = _env(fake_claude, {
        "FAKE_CLAUDE_AGENTS_MODE": "fixed",
        "FAKE_CLAUDE_FIXED": _roster({"id": "75d34378", "cwd": str(tmp_path / "repo-B"),
                                      "name": _worker_name()}),
    })
    payload = _json_stdout(_run_job(job_home, _site_args("status", run_dir), env))
    assert payload["state"] == "RUNNING", payload
    assert payload["liveness"] == "unavailable", payload


def test_status_liveness_accepts_a_roster_entry_whose_cwd_matches_repo_root(
        job_home, fake_claude, tmp_path):
    """正向对照：repo 对得上就照常取 state（否则上一条可以靠「永远 unavailable」假绿）。"""
    run_dir = tmp_path / "20260726T011000Z-Rep002"
    run_dir.mkdir()
    repo_root = tmp_path / "repo-A"
    repo_root.mkdir()
    _seed_site(run_dir, rc_kind="absent", repo_root=str(repo_root))
    env = _env(fake_claude, {
        "FAKE_CLAUDE_AGENTS_MODE": "fixed",
        "FAKE_CLAUDE_FIXED": _roster({"id": "75d34378", "cwd": str(repo_root),
                                      "name": _worker_name()}),
    })
    payload = _json_stdout(_run_job(job_home, _site_args("status", run_dir), env))
    assert (payload["state"], payload["liveness"]) == ("RUNNING", "working"), payload


# ── ⑥ 子树核验纯函数 ──────────────────────────────────────────────────────────

def test_pid_and_pgid_probes_answer_from_the_real_kernel():
    """两个 syscall 探针对真进程给真答案（三值：True / False / None）。"""
    assert JOB._pid_alive(os.getpid()) is True
    alive = _detached_sleeper(30)
    try:
        assert JOB._pid_alive(alive) is True
    finally:
        os.kill(alive, 9)
    assert JOB._pid_alive(_dead_pid()) is False
    assert JOB._pid_alive(0) is None
    assert JOB._pid_alive(-1) is None
    assert JOB._pid_alive("nope") is None
    assert JOB._pgid_alive(os.getpgid(0)) is True
    assert JOB._pgid_alive("nope") is None


def test_probe_subtree_calls_a_live_worker_alive(tmp_path):
    run_dir = tmp_path / "sub-alive"
    run_dir.mkdir()
    pid = _detached_sleeper(30)
    try:
        job = _seed_site(run_dir, rc_kind="absent", worker_pid=pid)
        verdict, detail = JOB.probe_subtree(run_dir, "design-voice", job)
    finally:
        os.kill(pid, 9)
    assert verdict == JOB.SUBTREE_ALIVE, (verdict, detail)


def _group_escaping_worker(tmp_path, seconds=60):
    """真起一对进程：**组长** worker + 一个换组逃逸的 runner。→ (leader_pid, runner_pid)

    这就是 GNU timeout 在真机上的形态（`outside-voice.sh` 的组级 KILL 守卫注释即据此写成：
    timeout 会 setpgid 把自己放进独立进程组，PGID 恒等于它自己的 PID）⇒ 杀掉 worker 之后
    worker 组空了，而真正烧额度的 runner 整棵还活着。
    """
    timeout_bin = shutil.which("gtimeout") or shutil.which("timeout")
    if not timeout_bin:
        pytest.skip("本机没有 GNU timeout/gtimeout，摆不出真实的换组子进程")
    script = Path(tmp_path) / "escaping-worker.py"
    marker = Path(tmp_path) / "escaping-worker.pids"
    script.write_text(textwrap.dedent("""
        import os, subprocess, sys, time
        os.setpgrp()                       # worker 自建进程组（组长 = 自己）
        p = subprocess.Popen([sys.argv[1], sys.argv[2], "sleep", sys.argv[2]],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.3)                    # 等 timeout 完成它自己的 setpgid
        with open(sys.argv[3], "w") as fh:
            fh.write("%d %d" % (os.getpid(), p.pid))
        time.sleep(int(sys.argv[2]))
    """), encoding="utf-8")
    cmd = " ".join(shlex.quote(x) for x in
                   [sys.executable, str(script), timeout_bin, str(seconds), str(marker)])
    # 后台 + 孤儿化：被 init 收养，杀掉后立刻回收，不会留 zombie 骗过 `kill(pid, 0)`。
    subprocess.run(["sh", "-c", cmd + " >/dev/null 2>&1 &"], timeout=15)
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        text = marker.read_text(encoding="utf-8").strip() if marker.is_file() else ""
        if len(text.split()) == 2:
            return tuple(int(x) for x in text.split())
        time.sleep(0.05)
    pytest.skip("换组子进程没能在 15 秒内摆出来")


def test_probe_subtree_will_not_call_a_dead_group_leader_exited_when_a_child_escaped(tmp_path):
    """🔴 真机复现的假阳：**worker 组空了 ≠ runner 已死。**

    GNU timeout 把自己（连同 claude）setpgid 进独立进程组 ⇒ worker 被杀之后
    `killpg(worker_pgid, 0)` 报 ProcessLookupError，而真正烧额度的那棵子树还活着。
    没有 `<site>.runner.pid` 这个直接信号时，组长分支 MUST fail-closed 判 unverifiable；
    信号在场则 MUST 以它为准判 alive。
    """
    run_dir = tmp_path / "sub-escaped"
    run_dir.mkdir()
    leader, runner = _group_escaping_worker(tmp_path)
    try:
        assert os.getpgid(leader) == leader, "worker 必须是组长，否则复现的不是这条分支"
        assert os.getpgid(runner) != leader, "runner 必须真的换了组（前提，不是假设）"
        os.kill(leader, 9)
        deadline = time.monotonic() + 10
        while JOB._pid_alive(leader) is not False and time.monotonic() < deadline:
            time.sleep(0.02)
        assert JOB._pid_alive(leader) is False, "组长确已消失"
        assert JOB._pgid_alive(leader) is False, "🔴 组也空了 —— 这正是那个骗人的信号"
        assert JOB._pid_alive(runner) is True, "而 runner 仍在跑、仍在计费"

        job = _seed_site(run_dir, rc_kind="absent", worker_pid=leader, worker_pgid=leader)
        without_signal = JOB.probe_subtree(run_dir, "design-voice", job)

        (run_dir / ("design-voice" + JOB.RUNNER_PID_SUFFIX)).write_text(
            str(runner), encoding="utf-8")
        with_signal = JOB.probe_subtree(run_dir, "design-voice", job)
    finally:
        for pid in (runner, leader):
            for killer in (os.killpg, os.kill):
                try:
                    killer(pid, 9)
                except OSError:
                    pass
    assert without_signal[0] == JOB.SUBTREE_UNVERIFIABLE, without_signal
    assert with_signal[0] == JOB.SUBTREE_ALIVE, with_signal


def test_probe_subtree_is_unverifiable_for_a_dead_group_leader_without_a_runner_signal(tmp_path):
    """组探针**只判 alive，不判 exited**：组空了推不出 runner 已退出（见上一条的真机复现）。"""
    run_dir = tmp_path / "sub-exited"
    run_dir.mkdir()
    pid = _dead_pid()
    job = _seed_site(run_dir, rc_kind="absent", worker_pid=pid, worker_pgid=pid)
    verdict, detail = JOB.probe_subtree(run_dir, "design-voice", job)
    assert verdict == JOB.SUBTREE_UNVERIFIABLE, (verdict, detail)

    # 同一形态 + runner 的直接信号（已死）⇒ 才可判已退出
    job2 = _seed_site(run_dir, "hr-tg", rc_kind="absent", worker_pid=pid, worker_pgid=pid,
                      runner_pid=_dead_pid())
    verdict2, detail2 = JOB.probe_subtree(run_dir, "hr-tg", job2)
    assert verdict2 == JOB.SUBTREE_EXITED, (verdict2, detail2)


def test_probe_subtree_answers_from_the_runner_pid_sidecar_before_the_disk_inference(tmp_path):
    """runner 的直接信号在场 ⇒ 以它为准，MUST NOT 退回 terminal witness 的推断。

    terminal witness 只证明「helper 同步返回了」——helper 被 SIGKILL 时它同样发布，
    而孤儿 runner 仍活着。那个窄口只能靠这个信号关掉。
    """
    run_dir = tmp_path / "sub-sidecar"
    run_dir.mkdir()
    dead = _dead_pid()
    alive = _detached_sleeper(30)
    try:
        job = _seed_site(run_dir, rc_kind="rc0_nonempty", worker_pid=dead, worker_pgid=dead,
                         runner_pid=alive)
        verdict, detail = JOB.probe_subtree(run_dir, "design-voice", job)
    finally:
        os.kill(alive, 9)
    assert verdict == JOB.SUBTREE_ALIVE, (verdict, detail)


def test_probe_subtree_is_unverifiable_when_the_runner_pid_sidecar_is_corrupt(tmp_path):
    """坏信号 ≠ 无信号：损坏的 sidecar MUST fail-closed，MUST NOT 静默退回弱推断。"""
    run_dir = tmp_path / "sub-badsidecar"
    run_dir.mkdir()
    dead = _dead_pid()
    job = _seed_site(run_dir, rc_kind="rc0_nonempty", worker_pid=dead, worker_pgid=dead)
    (run_dir / ("design-voice" + JOB.RUNNER_PID_SUFFIX)).write_text("not-a-pid\n",
                                                                   encoding="utf-8")
    verdict, detail = JOB.probe_subtree(run_dir, "design-voice", job)
    assert verdict == JOB.SUBTREE_UNVERIFIABLE, (verdict, detail)


def test_probe_subtree_is_unverifiable_without_a_started_witness(tmp_path):
    """没有 started witness ⇒ 根本没有可核验的 process identity ⇒ **不可证**，不是「已退出」。"""
    run_dir = tmp_path / "sub-nowitness"
    run_dir.mkdir()
    job = _seed_site(run_dir, rc_kind="absent", write_started=False)
    verdict, detail = JOB.probe_subtree(run_dir, "design-voice", job)
    assert verdict == JOB.SUBTREE_UNVERIFIABLE, (verdict, detail)


def test_probe_subtree_will_not_call_a_shared_process_group_exited(tmp_path):
    """worker 不是组长（pgid 与 supervisor 共用）⇒ killpg 探针无判别力。

    此时若没有 terminal witness 证明 worker 自己走到了发布点（`subprocess.call` 是同步的，
    走到那里意味着 inner child 已被 wait 回收），inner child 是否退出**不可证**。
    """
    run_dir = tmp_path / "sub-shared-group"
    run_dir.mkdir()
    dead = _dead_pid()
    job = _seed_site(run_dir, rc_kind="absent", worker_pid=dead, worker_pgid=os.getpgid(0),
                     write_terminal=False)
    verdict, detail = JOB.probe_subtree(run_dir, "design-voice", job)
    assert verdict == JOB.SUBTREE_UNVERIFIABLE, (verdict, detail)

    # 同一形态 + terminal witness ⇒ worker 自己走完了发布点 ⇒ 可判已退出
    job2 = _seed_site(run_dir, "hr-tg", rc_kind="absent", worker_pid=dead,
                      worker_pgid=os.getpgid(0), write_terminal=True)
    verdict2, detail2 = JOB.probe_subtree(run_dir, "hr-tg", job2)
    assert verdict2 == JOB.SUBTREE_EXITED, (verdict2, detail2)


def test_probe_subtree_reports_alive_when_the_group_still_holds_a_child(monkeypatch, tmp_path):
    """worker 本体已退但组内仍有存活进程（inner child 未随之退出）⇒ ALIVE。

    这一格用 monkeypatch 造：真实构造「组长已死但组还在」需要一个仍以死者 pid 为 pgid 的
    活进程，本机无法确定性摆出来。两个 syscall 探针本身由
    `test_pid_and_pgid_probes_answer_from_the_real_kernel` 对真内核钉死，此处只钉判定逻辑。
    """
    run_dir = tmp_path / "sub-group-alive"
    run_dir.mkdir()
    job = _seed_site(run_dir, rc_kind="absent", worker_pid=999001, worker_pgid=999001)
    monkeypatch.setattr(JOB, "_pid_alive", lambda pid: False)
    monkeypatch.setattr(JOB, "_pgid_alive", lambda pgid: True)
    verdict, detail = JOB.probe_subtree(run_dir, "design-voice", job)
    assert verdict == JOB.SUBTREE_ALIVE, (verdict, detail)


# ── cleanup：identity 核不过 ⇒ 只告警，零破坏性调用 ──────────────────────────

def _cleanup_args(run_dir, site="design-voice", *extra):
    return ["cleanup", "--run-dir", str(run_dir), "--site", site, *extra]


@pytest.mark.parametrize("label,roster_entries,seed_over", [
    ("repo-mismatch",
     [{"id": "75d34378", "cwd": "/somewhere/else", "name": _worker_name()}], {}),
    ("duplicate-id",
     [{"id": "75d34378", "name": _worker_name()},
      {"id": "75d34378", "name": _worker_name()}], {}),
    ("another-site",
     [{"id": "75d34378", "name": _worker_name(site="hr-tg")}], {}),
    ("another-attempt-nonce",
     [{"id": "75d34378", "name": _worker_name(nonce="f" * 32)}], {}),
    ("witness-from-another-attempt",
     [{"id": "75d34378", "name": _worker_name()}],
     {"nonce_in_witness": "someone-elses-nonce"}),
])
def test_cleanup_refuses_every_destructive_call_when_identity_does_not_verify(
        job_home, fake_claude, tmp_path, label, roster_entries, seed_over):
    """🔴 负向锚：identity 四项任一**矛盾** ⇒ 只告警，MUST NOT stop/rm 任何 job。

    判据落在 fake `claude` 的调用日志上（零 stop、零 rm），而不是 payload 的自述。
    """
    run_dir = tmp_path / ("20260726T02-" + label)
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="rc0_nonempty", nonce="0" * 32, **seed_over)
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _roster(*roster_entries)})
    proc = _run_job(job_home, _cleanup_args(run_dir, "design-voice", "--cancel",
                                            "--subtree-wait", "0.2"), env)
    payload = _json_stdout(proc)
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert payload["state"] == "identity-unverified", payload
    assert payload["removed"] is False and payload["stopped"] is False, payload
    assert _destructive(fake_claude) == [], _destructive(fake_claude)


def test_cleanup_on_a_bare_reservation_only_warns_and_touches_nothing(
        job_home, fake_claude, tmp_path):
    """残留 reserve（dispatch accepted 但 metadata 未发布）⇒ 无 identity 可核 ⇒ 只告警。

    MUST NOT 删 reserve：删掉就等于放行下一次 dispatch，把一次成本未知的调用变成双倍计费。
    """
    run_dir = tmp_path / "20260726T030000Z-Res001"
    run_dir.mkdir()
    (run_dir / "design-voice.reserve").write_text("{}", encoding="utf-8")
    proc = _run_job(job_home, _cleanup_args(run_dir), _env(fake_claude))
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["state"] == "identity-unverified", payload
    assert payload["unknown_cost"] is True, payload
    assert payload["orphan_warning"], payload
    assert (run_dir / "design-voice.reserve").exists()
    assert _destructive(fake_claude) == []


# ── cleanup：先 collect 才允许清理 roster ─────────────────────────────────────

def test_cleanup_refuses_to_remove_a_terminal_site_before_it_was_collected(
        job_home, fake_claude, tmp_path):
    """OVBG-05：「每个 terminal job **在结果已 collect 后** SHALL 调用 claude rm」。

    先 rm 再 collect 没有直接坏处，但 roster 一旦清掉，任何「这次到底跑没跑」的
    交叉核验就只剩盘面单证；顺序是 spec 明写的，且这是唯一能机械守住它的位置。
    """
    run_dir = tmp_path / "20260726T040000Z-Ord001"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="rc0_nonempty", nonce="0" * 32)
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _roster(
                                 {"id": "75d34378", "state": "done"})})
    proc = _run_job(job_home, _cleanup_args(run_dir), env)
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["state"] == "not-collected", payload
    assert _destructive(fake_claude) == []


def test_cleanup_removes_a_collected_terminal_site_from_the_roster(
        job_home, fake_claude, tmp_path):
    """交接②：terminal 且已 collect 过的 job 可直接 `rm`（无需 stop）。"""
    run_dir = tmp_path / "20260726T041000Z-Ord002"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="rc0_nonempty", nonce="0" * 32)
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _roster(
                                 {"id": "75d34378", "state": "done"})})
    collected = _json_stdout(_run_job(job_home, _site_args("collect", run_dir), env))
    assert collected["ok"] is True, collected

    proc = _run_job(job_home, _cleanup_args(run_dir), env)
    payload = _json_stdout(proc)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert payload["state"] == "removed", payload
    assert (payload["removed"], payload["stopped"]) == (True, False), payload
    assert _destructive(fake_claude) == [("rm", "75d34378")], _destructive(fake_claude)


def test_cleanup_is_idempotent_when_the_roster_no_longer_lists_the_job(
        job_home, fake_claude, tmp_path):
    """OVBG-05「正常 collect 后无活动残留」：roster 已无此 job **且子树已证退出** ⇒ no-op。

    「已证退出」是这条幂等的前提，不是修饰：解闸（`fallback_allowed`）只能建立在核验上。
    """
    run_dir = tmp_path / "20260726T042000Z-Ord003"
    run_dir.mkdir()
    dead = _dead_pid()
    _seed_site(run_dir, rc_kind="rc0_nonempty", nonce="0" * 32,
               worker_pid=dead, worker_pgid=dead, runner_pid=_dead_pid())
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "empty"})
    _run_job(job_home, _site_args("collect", run_dir), env)
    proc = _run_job(job_home, _cleanup_args(run_dir), env)
    payload = _json_stdout(proc)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert payload["state"] == "absent", payload
    assert payload["subtree"] == JOB.SUBTREE_EXITED, payload
    assert payload["fallback_allowed"] is True, payload
    assert payload["unknown_cost"] is False, payload
    assert _destructive(fake_claude) == []


def test_cleanup_still_verifies_the_subtree_when_the_roster_no_longer_lists_the_job(
        job_home, fake_claude, tmp_path):
    """🔴 roster 干净 ≠ 进程死了。

    `missing` liveness（roster 无此条目）正是 **LOST 的主要产生路径**（`derive_status`）。
    这一分支若无条件返回成功，一个仍在跑、已计费的 worker 就被报成干净通过，且自动同族
    fallback 会在它头上再叠一次 —— OVBG-05 与 OVBG-03 直接违反。
    """
    run_dir = tmp_path / "20260726T042500Z-Ord005"
    run_dir.mkdir()
    pid = _detached_sleeper(60)
    try:
        _seed_site(run_dir, rc_kind="absent", nonce="0" * 32,
                   worker_pid=pid, worker_pgid=pid)
        env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "empty"})
        proc = _run_job(job_home,
                        _cleanup_args(run_dir, "design-voice", "--subtree-wait", "0.3"),
                        env, timeout=60)
    finally:
        os.kill(pid, 9)
    payload = _json_stdout(proc)
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert payload["state"] == "orphan-warning", payload
    assert payload["subtree"] == JOB.SUBTREE_ALIVE, payload
    assert payload["unknown_cost"] is True, payload
    assert payload["fallback_allowed"] is False, payload
    assert payload["orphan_warning"], payload
    assert _destructive(fake_claude) == []


def test_cleanup_refuses_to_touch_a_site_that_is_still_running_without_cancel(
        job_home, fake_claude, tmp_path):
    run_dir = tmp_path / "20260726T043000Z-Ord004"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent", nonce="0" * 32)
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _roster(
                                 {"id": "75d34378", "name": _worker_name()})})
    proc = _run_job(job_home, _cleanup_args(run_dir), env)
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["state"] == "still-running", payload
    assert _destructive(fake_claude) == []


# ── cleanup 取消路径：stop → 核验子树 → rm ───────────────────────────────────

def test_cleanup_cancel_order_is_stop_then_subtree_verification_then_rm(
        job_home, fake_claude, tmp_path):
    """取消路径的**顺序**是契约：`stop` 必须早于 `rm`，且中间夹一次真的子树核验。

    fake `claude stop` 真的把 worker 进程杀掉 ⇒ 「子树已退出」不是摆拍，是内核的答案。
    """
    run_dir = tmp_path / "20260726T050000Z-Can001"
    run_dir.mkdir()
    pid = _detached_sleeper(60)
    try:
        # runner 早已收摊（sidecar 记的 pid 确定不存在）⇒ 只等 worker 本体被 stop 打掉。
        _seed_site(run_dir, rc_kind="absent", nonce="0" * 32, worker_pid=pid, worker_pgid=pid,
                   runner_pid=_dead_pid())
        env = _env(fake_claude, {
            "FAKE_CLAUDE_AGENTS_MODE": "fixed",
            "FAKE_CLAUDE_FIXED": _roster({"id": "75d34378", "name": _worker_name()}),
            "FAKE_CLAUDE_STOP_KILLS_PID": str(pid),
        })
        proc = _run_job(job_home, _cleanup_args(run_dir, "design-voice", "--cancel",
                                                "--subtree-wait", "5"), env, timeout=60)
    finally:
        try:
            os.kill(pid, 9)
        except OSError:
            pass
    payload = _json_stdout(proc)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert payload["state"] == "stopped-removed", payload
    assert (payload["stopped"], payload["removed"]) == (True, True), payload
    assert payload["subtree"] == JOB.SUBTREE_EXITED, payload
    assert payload["orphan_warning"] is None, payload
    assert payload["fallback_allowed"] is True, payload
    assert _destructive(fake_claude) == [("stop", "75d34378"), ("rm", "75d34378")], \
        _destructive(fake_claude)


def test_cleanup_leaves_an_orphan_warning_and_skips_rm_when_the_subtree_survives_stop(
        job_home, fake_claude, tmp_path):
    """🔴 stop 之后子树仍存活 ⇒ orphan warning，**不 rm**、不声称完成、抑制自动 fallback。

    「rm 之后声称已清理」正是 OVBG-05 要杀的形态：roster 干净了，进程还在烧钱。
    """
    run_dir = tmp_path / "20260726T051000Z-Can002"
    run_dir.mkdir()
    pid = _detached_sleeper(60)
    try:
        _seed_site(run_dir, rc_kind="absent", nonce="0" * 32, worker_pid=pid, worker_pgid=pid)
        env = _env(fake_claude, {
            "FAKE_CLAUDE_AGENTS_MODE": "fixed",
            "FAKE_CLAUDE_FIXED": _roster({"id": "75d34378", "name": _worker_name()}),
        })
        proc = _run_job(job_home, _cleanup_args(run_dir, "design-voice", "--cancel",
                                                "--subtree-wait", "0.4"), env, timeout=60)
    finally:
        os.kill(pid, 9)
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["state"] == "orphan-warning", payload
    assert (payload["stopped"], payload["removed"]) == (True, False), payload
    assert payload["subtree"] == JOB.SUBTREE_ALIVE, payload
    assert payload["unknown_cost"] is True, payload
    assert payload["fallback_allowed"] is False, payload
    assert str(pid) in payload["orphan_warning"], payload
    assert _destructive(fake_claude) == [("stop", "75d34378")], _destructive(fake_claude)


def test_cleanup_leaves_an_orphan_warning_when_the_subtree_exit_cannot_be_proven(
        job_home, fake_claude, tmp_path):
    """不可证 ≠ 已退出：没有 started witness 就没有 process identity ⇒ 同样 orphan warning。"""
    run_dir = tmp_path / "20260726T052000Z-Can003"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent", nonce="0" * 32, write_started=False,
               startup_deadline_ago=5)
    env = _env(fake_claude, {
        "FAKE_CLAUDE_AGENTS_MODE": "fixed",
        "FAKE_CLAUDE_FIXED": _roster({"id": "75d34378", "name": _worker_name()}),
    })
    proc = _run_job(job_home, _cleanup_args(run_dir, "design-voice", "--subtree-wait", "0.2"),
                    env, timeout=60)
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["state"] == "orphan-warning", payload
    assert payload["subtree"] == JOB.SUBTREE_UNVERIFIABLE, payload
    assert payload["removed"] is False, payload
    assert payload["unknown_cost"] is True, payload
    assert _destructive(fake_claude) == [("stop", "75d34378")], _destructive(fake_claude)


def test_cleanup_does_not_rm_when_stop_itself_failed(job_home, fake_claude, tmp_path):
    """stop 失败 ⇒ cleanup warning + job id 供人工处理，MUST NOT 静默声称已清理。"""
    run_dir = tmp_path / "20260726T053000Z-Can004"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent", nonce="0" * 32, write_started=False,
               startup_deadline_ago=5)
    env = _env(fake_claude, {
        "FAKE_CLAUDE_AGENTS_MODE": "fixed",
        "FAKE_CLAUDE_FIXED": _roster({"id": "75d34378", "name": _worker_name()}),
        "FAKE_CLAUDE_STOP_MODE": "fail",
    })
    proc = _run_job(job_home, _cleanup_args(run_dir, "design-voice", "--subtree-wait", "0.2"),
                    env, timeout=60)
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["state"] == "cleanup-failed", payload
    assert "75d34378" in payload["orphan_warning"], payload
    assert _destructive(fake_claude) == [("stop", "75d34378")], _destructive(fake_claude)


def test_cleanup_failure_never_rewrites_the_rc_or_deletes_run_dir_evidence(
        job_home, fake_claude, tmp_path):
    """OVBG-05：清理失败 MUST NOT 改写已取得的 rc、MUST NOT 删本轮审计证据、
    MUST NOT 把已成功的 findings 改判失败。"""
    run_dir = tmp_path / "20260726T060000Z-Fail01"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="rc0_nonempty", nonce="0" * 32)
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _roster(
                                 {"id": "75d34378", "state": "done"}),
                             "FAKE_CLAUDE_RM_MODE": "fail"})
    collected = _json_stdout(_run_job(job_home, _site_args("collect", run_dir), env))
    assert collected["ok"] is True

    before = {p.name: p.read_bytes() for p in run_dir.iterdir()}
    proc = _run_job(job_home, _cleanup_args(run_dir), env)
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["state"] == "cleanup-failed", payload
    assert "75d34378" in payload["orphan_warning"], payload
    after = {p.name: p.read_bytes() for p in run_dir.iterdir()}
    assert after == before, "清理失败 MUST NOT 改动 run-dir 里的任何审计证据"

    # 已成功的 findings 不因清理失败改判
    again = _json_stdout(_run_job(job_home, _site_args("collect", run_dir), env))
    assert (again["ok"], again["state"]) == (True, "SUCCEEDED"), again


# ── reconcile：只按显式 identity，绝不猜目标 ─────────────────────────────────

def test_reconcile_requires_an_explicit_run_dir(job_home, fake_claude):
    """🔴 「禁止扫描最新目录」的第一道机械闸：没有 `--run-dir` 根本无从下手。"""
    proc = _run_job(job_home, ["reconcile"], _env(fake_claude))
    assert proc.returncode == 2, (proc.returncode, proc.stdout, proc.stderr)
    assert _destructive(fake_claude) == []


def test_reconcile_never_reaches_into_a_sibling_or_newer_run_dir(
        job_home, fake_claude, tmp_path):
    """🔴 评审 session 整体丢失时只处理**被显式点名**的那个 run-dir。

    摆两个同级 run dir（被点名的旧 run + 更新的 run），断言更新那个 run 的 job id
    在整条调用日志里**一次都没出现过**——「不扫描最新目录」是日志上的事实。

    🔴 两个 run 的**站点名刻意不同**：同名会让「扫了父目录」与「没扫」产出同一份
    站点集合（set 去重），断言就失去判别力——本用例正是靠站点集合把这条路照出来的。
    """
    abandoned = tmp_path / "20260726T070000Z-Aband1"
    newest = tmp_path / "20260726T090000Z-Newest"
    abandoned.mkdir()
    newest.mkdir()
    _seed_site(abandoned, "design-voice", rc_kind="rc0_nonempty", nonce="0" * 32,
               job_id="aaaa1111")
    _seed_site(newest, "hr-tg", rc_kind="rc0_nonempty", nonce="0" * 32, job_id="bbbb2222")
    env = _env(fake_claude, {
        "FAKE_CLAUDE_AGENTS_MODE": "fixed",
        "FAKE_CLAUDE_FIXED": _roster({"id": "aaaa1111", "state": "done"},
                                     {"id": "bbbb2222", "state": "done"}),
    })
    proc = _run_job(job_home, ["reconcile", "--run-dir", str(abandoned)], env, timeout=60)
    payload = _json_stdout(proc)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert [s["site"] for s in payload["sites"]] == ["design-voice"], payload
    assert _destructive(fake_claude) == [("rm", "aaaa1111")], _destructive(fake_claude)
    assert "bbbb2222" not in json.dumps(_invocations(fake_claude))
    assert not (newest / "hr-tg.collected.json").exists(), \
        "未被点名的 run-dir MUST NOT 被碰"


def test_reconcile_ignores_supervisor_jobs_it_holds_no_metadata_for(
        job_home, fake_claude, tmp_path):
    """roster 里有别人的 job ⇒ MUST NOT 扫描或清理未持有 metadata 的 Claude job。"""
    run_dir = tmp_path / "20260726T071000Z-Own001"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="rc0_nonempty", nonce="0" * 32, job_id="aaaa1111")
    env = _env(fake_claude, {
        "FAKE_CLAUDE_AGENTS_MODE": "fixed",
        "FAKE_CLAUDE_FIXED": _roster({"id": "aaaa1111", "state": "done"},
                                     {"id": "cccc3333", "state": "working",
                                      "name": "someone else's job"},
                                     {"id": "dddd4444", "state": "failed"}),
    })
    proc = _run_job(job_home, ["reconcile", "--run-dir", str(run_dir)], env, timeout=60)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert _destructive(fake_claude) == [("rm", "aaaa1111")], _destructive(fake_claude)


def test_reconcile_collects_a_terminal_site_then_removes_it(job_home, fake_claude, tmp_path):
    """abandoned run 的终态站点：先 collect（结果不丢）再 rm（roster 不留活动残留）。"""
    run_dir = tmp_path / "20260726T072000Z-Rec001"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="rc0_nonempty", nonce="0" * 32)
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _roster(
                                 {"id": "75d34378", "state": "done"})})
    proc = _run_job(job_home, ["reconcile", "--run-dir", str(run_dir)], env, timeout=60)
    payload = _json_stdout(proc)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    site = payload["sites"][0]
    assert (site["state"], site["reason_code"]) == ("SUCCEEDED", "ok"), site
    assert (site["collected"], site["removed"]) == (True, True), site
    assert (run_dir / "design-voice.collected.json").exists()
    assert _destructive(fake_claude) == [("rm", "75d34378")]


def test_reconcile_recovers_a_result_that_landed_after_a_lost_verdict(
        job_home, fake_claude, tmp_path):
    """交接③：先前被判 LOST 的站点，若 worker 后来真发布了 rc，reconcile MUST 拿到真结果。

    这是 Task 2「无 rc 的终态不再冻结」留给本票去修正的那个面。
    """
    run_dir = tmp_path / "20260726T073000Z-Rec002"
    run_dir.mkdir()
    now = time.time()
    _seed_site(run_dir, rc_kind="absent", nonce="0" * 32, now=now, write_started=False,
               startup_deadline_ago=5)
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _roster(
                                 {"id": "75d34378", "name": _worker_name()})})
    lost = _json_stdout(_run_job(job_home, _site_args("collect", run_dir), env))
    assert lost["state"] == "LOST", lost
    assert not (run_dir / "design-voice.collected.json").exists()

    # worker 其实只是慢，随后真发布了 started → terminal → rc=0
    _seed_site(run_dir, rc_kind="rc0_nonempty", now=time.time(), write_job=False,
               nonce="0" * 32, stdout=b"REAL FINDINGS after a LOST verdict\n")
    proc = _run_job(job_home, ["reconcile", "--run-dir", str(run_dir)], env, timeout=60)
    payload = _json_stdout(proc)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    site = payload["sites"][0]
    assert (site["state"], site["reason_code"]) == ("SUCCEEDED", "ok"), site
    stored = json.loads((run_dir / "design-voice.collected.json").read_text(encoding="utf-8"))
    assert stored["stdout_sha256"] == hashlib.sha256(
        b"REAL FINDINGS after a LOST verdict\n").hexdigest()


def test_reconcile_leaves_a_bare_reservation_to_manual_cleanup(job_home, fake_claude, tmp_path):
    """unknown-cost 的残留 reserve：报出来交人工，MUST NOT 自动重派、MUST NOT 删证据。"""
    run_dir = tmp_path / "20260726T074000Z-Rec003"
    run_dir.mkdir()
    (run_dir / "design-voice.reserve").write_text("{}", encoding="utf-8")
    proc = _run_job(job_home, ["reconcile", "--run-dir", str(run_dir)],
                    _env(fake_claude), timeout=60)
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["ok"] is False, payload
    site = payload["sites"][0]
    assert site["site"] == "design-voice", site
    assert site["action"] == "manual-cleanup-required", site
    assert site["unknown_cost"] is True, site
    assert payload["unknown_cost_sites"] == ["design-voice"], payload
    assert (run_dir / "design-voice.reserve").exists()
    assert _destructive(fake_claude) == []
    assert _bg_invocations(fake_claude) == []


def test_reconcile_does_not_stop_a_site_that_is_still_legitimately_running(
        job_home, fake_claude, tmp_path):
    """未到 deadline 的在飞站点 ⇒ 只报 pending，MUST NOT stop（那会杀掉一次已计费的 voice）。"""
    run_dir = tmp_path / "20260726T075000Z-Rec004"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent", nonce="0" * 32, timeout_seconds=900)
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _roster(
                                 {"id": "75d34378", "name": _worker_name()})})
    proc = _run_job(job_home, ["reconcile", "--run-dir", str(run_dir)], env, timeout=60)
    payload = _json_stdout(proc)
    site = payload["sites"][0]
    assert site["state"] == "RUNNING", site
    assert site["action"] == "pending", site
    assert _destructive(fake_claude) == []


def test_reconcile_stops_and_removes_a_lost_site_whose_subtree_is_proven_dead(
        job_home, fake_claude, tmp_path):
    """超 deadline 的活动 ⇒ stop → 子树终止核验 → rm，三步齐全才算清理完成。"""
    run_dir = tmp_path / "20260726T076000Z-Rec005"
    run_dir.mkdir()
    now = time.time()
    dead = _dead_pid()
    _seed_site(run_dir, rc_kind="absent", nonce="0" * 32, now=now, dispatched_ago=1000,
               started_ago=1 + JOB.AWAIT_GRACE_SECONDS + 5, timeout_seconds=1,
               worker_pid=dead, worker_pgid=dead, runner_pid=_dead_pid())
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _roster(
                                 {"id": "75d34378", "name": _worker_name()})})
    proc = _run_job(job_home, ["reconcile", "--run-dir", str(run_dir),
                               "--subtree-wait", "0.5"], env, timeout=60)
    payload = _json_stdout(proc)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    site = payload["sites"][0]
    assert site["state"] == "LOST", site
    assert (site["stopped"], site["removed"]) == (True, True), site
    assert site["orphan_warning"] is None, site
    assert _destructive(fake_claude) == [("stop", "75d34378"), ("rm", "75d34378")]


def test_reconcile_reports_an_orphan_warning_and_exits_nonzero(job_home, fake_claude, tmp_path):
    """子树不可证 ⇒ 整份 reconcile 报告 ok=false + orphan_warnings 列表，退出码非零。"""
    run_dir = tmp_path / "20260726T077000Z-Rec006"
    run_dir.mkdir()
    _seed_site(run_dir, rc_kind="absent", nonce="0" * 32, write_started=False,
               startup_deadline_ago=5)
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _roster(
                                 {"id": "75d34378", "name": _worker_name()})})
    proc = _run_job(job_home, ["reconcile", "--run-dir", str(run_dir),
                               "--subtree-wait", "0.2"], env, timeout=60)
    payload = _json_stdout(proc)
    assert proc.returncode == 1
    assert payload["ok"] is False, payload
    assert payload["orphan_warnings"], payload
    assert payload["sites"][0]["removed"] is False, payload


def test_reconcile_will_not_report_a_site_clean_when_the_roster_dropped_a_live_worker(
        job_home, fake_claude, tmp_path):
    """🔴 LOST 的**主要**产生路径就是 roster 里没有这条 job（`probe_liveness` → missing）。

    真起一个活 worker、roster 空 ⇒ reconcile MUST 落 orphan warning + unknown_cost + 非零
    退出，MUST NOT 报成干净通过（那等于放行 fallback 在一次仍在计费的 voice 上再叠一次）。
    """
    run_dir = tmp_path / "20260726T078500Z-Rec009"
    run_dir.mkdir()
    pid = _detached_sleeper(60)
    try:
        _seed_site(run_dir, rc_kind="absent", nonce="0" * 32, worker_pid=pid, worker_pgid=pid)
        env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "empty"})
        proc = _run_job(job_home, ["reconcile", "--run-dir", str(run_dir),
                                   "--subtree-wait", "0.3"], env, timeout=60)
    finally:
        os.kill(pid, 9)
    payload = _json_stdout(proc)
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert payload["ok"] is False, payload
    site = payload["sites"][0]
    assert site["state"] == "LOST", site
    assert site["action"] == "orphan-warning", site
    assert site["unknown_cost"] is True and site["orphan_warning"], site
    assert payload["orphan_warnings"] == ["design-voice"], payload
    assert payload["unknown_cost_sites"] == ["design-voice"], payload
    assert _destructive(fake_claude) == []


def test_reconcile_rejects_a_site_the_run_dir_does_not_hold(job_home, fake_claude, tmp_path):
    """🔴 `--site` 未命中 ⇒ usage-error，MUST NOT 拿 `all([]) == True` 渲染一份绿报告。

    敲错 site / 点错 run-dir 恰恰是**成本未知**的场景：那时给操作者「一切正常」，
    等于把一个可能仍在计费的 run 判成已收摊。
    """
    run_dir = tmp_path / "20260726T078600Z-Rec010"
    run_dir.mkdir()
    _seed_site(run_dir, "design-voice", rc_kind="rc0_nonempty", nonce="0" * 32)
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "empty"})
    proc = _run_job(job_home, ["reconcile", "--run-dir", str(run_dir), "--site", "hr-tg"],
                    env, timeout=60)
    payload = _json_stdout(proc)
    assert proc.returncode == 2, (proc.stdout, proc.stderr)
    assert payload["ok"] is False, payload
    assert payload["state"] == "usage-error", payload
    assert payload["sites"] == [], payload
    assert _destructive(fake_claude) == []


def test_reconcile_does_not_report_an_empty_run_dir_as_all_clear(
        job_home, fake_claude, tmp_path):
    """站点集为空 ⇒ `ok=false` + 显式 detail：没有可核对的站点**不等于**没有残留。"""
    run_dir = tmp_path / "20260726T078700Z-Rec011"
    run_dir.mkdir()
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "empty"})
    proc = _run_job(job_home, ["reconcile", "--run-dir", str(run_dir)], env, timeout=60)
    payload = _json_stdout(proc)
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert payload["ok"] is False, payload
    assert payload["sites"] == [], payload
    assert payload["detail"], payload
    assert _destructive(fake_claude) == []


def test_reconcile_handles_both_sites_of_a_two_site_run(job_home, fake_claude, tmp_path):
    """一个 run 最多两个站点 ⇒ reconcile MUST 把**两个**都处理掉，别只做第一个。"""
    run_dir = tmp_path / "20260726T078000Z-Rec007"
    run_dir.mkdir()
    _seed_site(run_dir, "design-voice", rc_kind="rc0_nonempty", nonce="0" * 32,
               job_id="aaaa1111")
    _seed_site(run_dir, "hr-tg", rc_kind="rc124", nonce="0" * 32, job_id="bbbb2222")
    env = _env(fake_claude, {
        "FAKE_CLAUDE_AGENTS_MODE": "fixed",
        "FAKE_CLAUDE_FIXED": _roster({"id": "aaaa1111", "state": "done"},
                                     {"id": "bbbb2222", "state": "done"}),
    })
    proc = _run_job(job_home, ["reconcile", "--run-dir", str(run_dir)], env, timeout=60)
    payload = _json_stdout(proc)
    assert [s["site"] for s in payload["sites"]] == ["design-voice", "hr-tg"], payload
    assert {s["state"] for s in payload["sites"]} == {"SUCCEEDED", "TIMED_OUT"}, payload
    assert sorted(_destructive(fake_claude)) == [("rm", "aaaa1111"), ("rm", "bbbb2222")]


def test_contract_docstring_documents_cleanup_reconcile_and_the_orphan_fields():
    """模块 docstring 自称「契约单一源（两份评审 SKILL 只引用本注释）」⇒ 新子命令与
    新字段漏写就是契约与实现不符：Task 5 会照着它去 gate `unknown_cost`。"""
    doc = JOB.__doc__
    for token in ("cleanup", "reconcile", "unknown_cost", "orphan_warning",
                  "--subtree-wait", "--cancel"):
        assert token in doc, token
    assert doc.count("2=usage-error") >= 5, "契约单一源 MUST 逐子命令写明 exit 2"


def test_reconcile_treats_a_terminal_but_rc_less_corrupt_site_as_cleanup_not_pending(
        job_home, fake_claude, tmp_path):
    """终态但无可用 rc 的形态不止 LOST：rc 不可解析的 CORRUPT 同样永远等不到 rc。

    把清理闸门写成 `state != LOST` 会把它报成「站点仍在飞」——一句假话，且那个 job
    会被永久挂起（既不清理也永远等不到终态）。闸门 MUST 按「是不是 pending」划。

    构造用**非纯十进制 rc**（identity 全部干净、witness 齐全，只是 rc 不可用）：
    这样闸门走的确实是「pending 与否」，而不是被更靠前的 identity 闸挡住。
    """
    run_dir = tmp_path / "20260726T079000Z-Rec008"
    run_dir.mkdir()
    dead = _dead_pid()
    _seed_site(run_dir, rc_kind="rc_bad", nonce="0" * 32,
               worker_pid=dead, worker_pgid=dead)
    env = _env(fake_claude, {"FAKE_CLAUDE_AGENTS_MODE": "fixed",
                             "FAKE_CLAUDE_FIXED": _roster(
                                 {"id": "75d34378", "name": _worker_name()})})
    proc = _run_job(job_home, ["reconcile", "--run-dir", str(run_dir),
                               "--subtree-wait", "0.5"], env, timeout=60)
    payload = _json_stdout(proc)
    site = payload["sites"][0]
    assert site["state"] == "CORRUPT", site
    assert site["action"] != "still-running", site       # 🔴 它永远等不到 rc
    assert site["action"] == "stopped-removed", site
    assert (site["stopped"], site["removed"]) == (True, True), site
    assert _destructive(fake_claude) == [("stop", "75d34378"), ("rm", "75d34378")]
    # 清理不动审计证据：坏 rc 原样留在盘上
    assert (run_dir / "design-voice.rc").read_text(encoding="utf-8") == "oops"


# ══════════════════════════════════════════════════════════════════════════════
# Task 4：runner 隔离加固与出境面封堵（OVBG-04）
#
# TDD 接缝（沿用本文件既有两处，不新造）：
#   ② **sidecar 文件契约**：新增 `<site>.runner.pid` —— 由 `outside-voice.sh` 生产、
#      本脚本的 `read_runner_pid` / `probe_subtree` 消费。跨文件接缝 MUST 端到端验一次：
#      两侧各自单测全绿、中间那根线没接上，是 Task 1 的 C1（worker 漏传 env）刚栽过的形态。
#   ① **CLI 契约**：注入 / 越界输入 MUST 在任何外部副作用之前被拒。
# ══════════════════════════════════════════════════════════════════════════════

_FAKE_RUNNER = """#!/usr/bin/env bash
# 极简 runner 替身（不调模型）：claude -p --output-format text 的 stdout 即最终消息。
cat >/dev/null
sleep "${FAKE_RUNNER_SLEEP:-0}"
printf 'CROSS_FILE_FINDINGS\\n'
exit 0
"""

_FAKE_TIMEOUT = """#!/usr/bin/env bash
# timeout 替身：只吃 `-k N <sec> <cmd...>`，把自己的 pid 记下来供比对
# （生产里 OV_RUNNER_PID 记的就是 timeout 自身的 pid）。
[ -n "${FAKE_TIMEOUT_PID_FILE:-}" ] && echo $$ > "${FAKE_TIMEOUT_PID_FILE}"
if [ "$1" = "-k" ]; then shift 2; fi
shift
stdin_tmp=$(mktemp)
cat > "$stdin_tmp"
"$@" < "$stdin_tmp"
rc=$?
rm -f "$stdin_tmp"
exit "$rc"
"""


@pytest.fixture
def fake_runner_bin(tmp_path):
    """PATH 前置目录：假 claude runner + 假 timeout（供**真** outside-voice.sh 使用）。"""
    bin_dir = tmp_path / "runner-bin"
    bin_dir.mkdir()
    _write_exec(bin_dir / "claude", _FAKE_RUNNER)
    _write_exec(bin_dir / "timeout", _FAKE_TIMEOUT)
    return bin_dir


def test_real_helper_publishes_the_runner_pid_this_module_consumes(job_home, repo, fake_runner_bin,
                                                                   tmp_path):
    """🔴 跨票交接 A 的端到端锚：worker 下发 → **真** helper 落盘 → 本模块解析成功。

    两侧此前各自绿着，中间那根线却是断的：worker 早就 export 了
    `SDFLOW_VOICE_RUNNER_PID_FILE`，`read_runner_pid` 也早就写好，但 `outside-voice.sh`
    从不写这个文件 ⇒ 消费侧恒走 `absent`。这条用例是唯一能照出那段断线的形状。
    """
    timeout_pid_file = tmp_path / "timeout-self.pid"
    env = os.environ.copy()
    env["PATH"] = str(fake_runner_bin) + os.pathsep + env["PATH"]
    env["FAKE_TIMEOUT_PID_FILE"] = str(timeout_pid_file)
    proc = _run_job(job_home, _worker_args(repo), env, timeout=120)
    assert proc.returncode == 0, proc.stderr
    assert (repo["run_dir"] / "design-voice.rc").read_text(encoding="utf-8") == "0", \
        (repo["run_dir"] / "design-voice.stderr").read_text(encoding="utf-8")

    kind, pid, detail = JOB.read_runner_pid(repo["run_dir"], "design-voice")
    assert kind == "ok", (kind, detail)
    assert pid == int(timeout_pid_file.read_text(encoding="utf-8").strip()), \
        "落盘的不是 runner（timeout）自己的 pid"
    sidecar = repo["run_dir"] / ("design-voice" + JOB.RUNNER_PID_SUFFIX)
    assert stat.S_IMODE(sidecar.stat().st_mode) == 0o600


def test_the_published_runner_pid_unblocks_the_subtree_verdict(job_home, repo, fake_runner_bin):
    """交接 A 的**后果**锚：有了这个信号，`probe_subtree` 才能判 `exited`。

    判别器刻意把 terminal witness 删掉 —— 否则 ⑤ 的盘面推断会替 ④ 把结论"蒙对"，
    这条用例就退化成证不出交接是否兑现的空断言。
    没有它、且**本用例这种无 terminal witness 的形态**下：verdict 恒 `unverifiable`
    ⇒ `cleanup --cancel` 永不解闸同族 fallback。（有 terminal witness 时缺 ④ 不会卡住，
    而是走 ⑤ 判 `exited` —— 那条路在 helper 被 SIGKILL 时会误判，见 `probe_subtree` ⑤ 的
    残余登记。两种坏结果不同：这里是卡死，那里是漏放。）
    """
    env = os.environ.copy()
    env["PATH"] = str(fake_runner_bin) + os.pathsep + env["PATH"]
    proc = _run_job(job_home, _worker_args(repo), env, timeout=120)
    assert proc.returncode == 0, proc.stderr
    job = json.loads(json.dumps({
        "site": "design-voice", "run_id": repo["run_dir"].name, "attempt_nonce": "nonce-abc",
    }))
    (repo["run_dir"] / "design-voice.terminal.json").unlink()
    verdict, detail = JOB.probe_subtree(repo["run_dir"], "design-voice", job)
    assert verdict == JOB.SUBTREE_EXITED, (verdict, detail)
    assert "runner pid" in detail


def test_helper_writes_no_runner_pid_when_the_worker_did_not_ask_for_one(job_home, repo,
                                                                        fake_runner_bin):
    """不走后台通道的直调 exec 没有这个变量 ⇒ helper MUST 零副作用。

    主语校正：本用例 runner=claude ⟺ 宿主是 **Codex**（runner 恒为宿主之外的机队）。
    """
    env = os.environ.copy()
    env["PATH"] = str(fake_runner_bin) + os.pathsep + env["PATH"]
    env["SDFLOW_VOICE_RUNNER"] = "claude"
    env["SDFLOW_VOICE_MODEL"] = "opus"
    env.pop("SDFLOW_VOICE_RUNNER_PID_FILE", None)
    proc = subprocess.run(["bash", str(job_home / "outside-voice.sh"), "exec",
                           "--context-file", str(repo["ctx"])],
                          capture_output=True, text=True, env=env, timeout=120)
    assert proc.returncode == 0, proc.stderr
    assert not list(repo["run_dir"].glob("*" + JOB.RUNNER_PID_SUFFIX))


# ── 注入与越界：外部副作用之前一律拒绝 ────────────────────────────────────────

@pytest.mark.parametrize("bad", ["ctx\nfile.md", "ctx\rfile.md", "ctx\0file.md"])
def test_build_worker_command_refuses_control_characters(tmp_path, bad):
    """NUL / 换行 / 回车 MUST 在**组装命令之前**拒绝——quoting 之后再发现就晚了。"""
    with pytest.raises(ValueError):
        JOB.build_worker_command(str(tmp_path), str(tmp_path), "design-voice", bad,
                                 str(tmp_path), "claude", "opus", "high", 900,
                                 "n0nce", "run-1")


def test_dispatch_rejects_a_newline_in_a_path_before_any_external_side_effect(
        job_home, fake_claude, repo):
    ctx = repo["run_dir"] / "line\nbreak.md"
    args = _dispatch_args(repo, job_home)
    args[args.index("--context-file") + 1] = str(ctx)
    proc = _run_job(job_home, args, _env(fake_claude))
    assert proc.returncode != 0
    assert _bg_invocations(fake_claude) == []
    assert not (repo["run_dir"] / "design-voice.reserve").exists()


def test_dispatch_rejects_a_run_dir_outside_the_repo_root(job_home, fake_claude, repo, tmp_path):
    """run-dir 越界与 context-file 越界是同一片面 —— 只补一处就是点补。"""
    outside = tmp_path / "elsewhere" / ".outside-voice" / "run-x"
    outside.mkdir(parents=True)
    args = _dispatch_args(repo, job_home)
    args[args.index("--run-dir") + 1] = str(outside)
    proc = _run_job(job_home, args, _env(fake_claude))
    assert proc.returncode != 0
    assert _bg_invocations(fake_claude) == []
    assert not list(outside.glob("*.reserve"))


def test_shell_metacharacters_in_paths_cannot_rewrite_the_dispatched_command(
        job_home, fake_claude, repo, tmp_path):
    """让 **shell 自己** 回答「这条命令会被切成哪些词」（基准 5：无界语法面别手搓解析器）。

    做法：把生产真正下发的那条命令串原样接在 `printf '%s\\n'` 后面交给 bash。
    quoting 若被击穿，`; touch PWNED` 就会作为一条**独立命令**执行 —— PWNED 是否出现
    是内核事实，不是我们对 quoting 的信念。
    """
    hostile = repo["run_dir"] / "x; touch PWNED $(touch PWNED2) `touch PWNED3`"
    hostile.mkdir()
    ctx = hostile / "ctx.md"
    ctx.write_text("hostile evidence\n", encoding="utf-8")
    args = _dispatch_args(repo, job_home)
    args[args.index("--context-file") + 1] = str(ctx)
    proc = _run_job(job_home, args, _env(fake_claude))
    assert proc.returncode == 0, proc.stderr
    command = _bg_invocations(fake_claude)[0]["argv"][-1]

    probe = subprocess.run(["bash", "-c", "printf '%s\\n' " + command],
                           capture_output=True, text=True, cwd=str(tmp_path), timeout=30)
    assert probe.returncode == 0, probe.stderr
    tokens = probe.stdout.splitlines()
    assert str(ctx) in tokens, tokens
    assert tokens.count("worker") == 1
    for pwned in ("PWNED", "PWNED2", "PWNED3"):
        assert not (tmp_path / pwned).exists(), "quoting 被击穿：%s 被真的执行了" % pwned
        assert not (Path.cwd() / pwned).exists()


def test_failed_collect_reports_stderr_counts_but_never_its_text(job_home, fake_claude, tmp_path):
    """**失败**站点的 stderr 同样只出计数 —— 既有锚只覆盖 rc=0 那格。

    失败路径才是 stderr 真正装满东西（runner 报错原文、可能夹带路径与片段）的那一格，
    而它恰恰也是最容易被"顺手贴进报告帮助排查"的一格。
    """
    run_dir = tmp_path / "run-stderr-fail"
    run_dir.mkdir()
    canary = "STDERR_CANARY_" + "M4X"
    _seed_site(run_dir, rc_kind="rc_other")
    (run_dir / "design-voice.stderr").write_text(canary + "\n", encoding="utf-8")
    proc = _run_job(job_home, _site_args("collect", run_dir), _env(fake_claude))
    payload = _json_stdout(proc)
    assert payload["reason_code"] == "exec-error"
    assert canary not in json.dumps(payload, ensure_ascii=False), payload
    assert payload["stderr_bytes"] == len((canary + "\n").encode("utf-8"))
    assert payload["stderr_lines"] == 1
    assert canary not in proc.stdout and canary not in proc.stderr


# ── 真机 canary：supervisor transcript / state 不得成为第二条出境面 ────────────

_CANARY_HELPER = r'''#!/usr/bin/env bash
set -u
# 故意把 context 正文原样吐向 stdout **和** stderr —— 模拟「worker 的输出里什么都有」。
# 若 worker 没有在执行任何可携带 payload 的代码之前完成重定向，这些内容就会流进
# outer supervisor 的 transcript（`claude logs <id>` 可读），成为一条绕过出境
# secret scan 的旁路出境面。
ctx=""
prev=""
for a in "$@"; do
  [ "$prev" = "--context-file" ] && ctx="$a"
  prev="$a"
done
if [ -n "$ctx" ] && [ -r "$ctx" ]; then
  cat "$ctx"
  cat "$ctx" >&2
fi
sleep "${FAKE_HELPER_SLEEP:-0}"
exit 0
'''


@pytest.mark.skipif(_REAL_CLAUDE_SKIP is not None, reason=_REAL_CLAUDE_SKIP or "")
def test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret(tmp_path, repo):
    """🔴 OVBG-04 出境面封堵的真机锚：`claude logs <id>` 与 agents state 都不得含 payload。

    口径（Task 1 双轴审已实测确立）：`claude agents --all --json` 的 `name` 字段承载
    **完整 worker 命令串**，其中含 run-dir / context 文件的绝对**路径**——
    **路径不是 payload**，不判红；判红的是 context 正文、（半截）stdout、stderr 与假密钥。

    🔴 判别器有效性靠**对照组**，不靠 rc=0：本机实测 `claude logs <worker-id>` 输出为
    **空**。空既可能是"重定向奏效"，也可能是"`claude logs` 本来就不捕获 background 命令
    的输出" —— 两者不可区分。故先跑一条不做任何重定向的裸 `--bg --exec`，确认它的
    stdout/stderr **确实**会出现在 transcript 里；对照组不成立时本用例 MUST 立即失败，
    MUST NOT 让一条无判别力的断言冒充证据。
    """
    claude = shutil.which("claude")
    control_canary = "CONTROL_TRANSCRIPT_CANARY_A1B2"
    control = subprocess.run(
        [claude, "--bg", "--exec",
         "printf '%s\\n' " + control_canary + "; printf '%s\\n' " + control_canary + "-ERR >&2"],
        capture_output=True, text=True, timeout=60)
    assert control.returncode == 0, control.stderr
    control_id = JOB._parse_job_id_hint(control.stdout)
    assert control_id, control.stdout
    try:
        control_logs = ""
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            got = subprocess.run([claude, "logs", control_id],
                                 capture_output=True, text=True, timeout=60)
            control_logs = got.stdout + got.stderr
            if control_canary in control_logs:
                break
            time.sleep(0.5)
        assert control_canary in control_logs, (
            "对照组：裸 --bg --exec 的输出未出现在 `claude logs` 里 ⇒ 本探针对"
            "「worker 是否重定向」无判别力，下面的断言不构成证据\n%r" % control_logs[:800])
        assert control_canary + "-ERR" in control_logs, "对照组：stderr 未进 transcript"
    finally:
        subprocess.run([claude, "rm", control_id], capture_output=True, text=True, timeout=60)

    home = tmp_path / "hack-canary"
    home.mkdir()
    shutil.copy2(JOB_PY, home / "outside-voice-job.py")
    _write_exec(home / "outside-voice.sh", _CANARY_HELPER)
    shutil.copy2(PRINCIPLES, home / "skill-principles.md")
    JOB.write_manifest(home)

    ctx_canary = "CTX_BODY_CANARY_5F2A9"
    secret_canary = "AKIA" + "Q" * 16          # 形状即密钥，内容是自造的假货
    repo["ctx"].write_text("%s\naws_key=%s\n" % (ctx_canary, secret_canary), encoding="utf-8")

    env = os.environ.copy()
    env["FAKE_HELPER_SLEEP"] = "3"
    proc = _run_job(home, _dispatch_args(repo, home), env, timeout=60)
    payload = _json_stdout(proc)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    job_id = payload["job_id"]
    try:
        rc_path = repo["run_dir"] / "design-voice.rc"
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline and not rc_path.exists():
            time.sleep(0.5)
        assert rc_path.exists(), "worker 未在 120s 内发布 rc"
        # 前提核实：canary 确实走过了 worker 的输出流（否则本用例什么都没测）
        assert ctx_canary in (repo["run_dir"] / "design-voice.stdout").read_text(encoding="utf-8")
        assert ctx_canary in (repo["run_dir"] / "design-voice.stderr").read_text(encoding="utf-8")

        logs = subprocess.run([claude, "logs", job_id], capture_output=True, text=True, timeout=60)
        assert logs.returncode == 0, (logs.stdout, logs.stderr)
        roster = subprocess.run([claude, "agents", "--all", "--json"],
                                capture_output=True, text=True, timeout=60)
        assert roster.returncode == 0, roster.stderr
        surface = logs.stdout + logs.stderr + roster.stdout
        assert ctx_canary not in surface, "context 正文进了 supervisor transcript/state"
        assert secret_canary not in surface, "假密钥进了 supervisor transcript/state"
        # 路径出现在 roster 的 name 里是**既有且已知**的结构化事实，不判红
        assert str(repo["ctx"]) in roster.stdout or job_id in roster.stdout
    finally:
        subprocess.run([claude, "rm", job_id], capture_output=True, text=True, timeout=60)


@pytest.mark.parametrize("attr,value", [("name", "nt"), ("platform", "win32"),
                                        ("platform", "aix")])
def test_non_posix_platforms_fail_closed_all_the_way_up_to_preflight(monkeypatch, job_home,
                                                                     attr, value):
    """三条非 POSIX 形态各自 fail-closed，且 MUST 一路顶到 `run_preflight` 的 ok=False。

    既有锚只打 `os.name`，而 `check_posix_shell` 有**两个**并列判据（`os.name` 与
    `sys.platform`）——只补被点穿的那一处是点补。dispatch 在任何外部副作用之前调
    `run_preflight`，故这一层红即整条通道红。
    """
    if attr == "name":
        monkeypatch.setattr(JOB.os, "name", value)
    else:
        monkeypatch.setattr(JOB.sys, "platform", value)
    assert JOB.check_posix_shell()["ok"] is False
    result = JOB.run_preflight(job_home)
    assert result["ok"] is False
    assert result["reason_code"] == "preflight-error"
    assert result["checks"]["posix-shell"]["ok"] is False
