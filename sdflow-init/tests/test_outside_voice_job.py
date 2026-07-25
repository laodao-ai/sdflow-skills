"""outside-voice-job.py 的 Task 1 契约测试（preflight / reserve / dispatch / worker）。

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
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import textwrap
import time
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
    if mode == "nomatch":
        base["name"] = "some unrelated background command"
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

if "--bg" in argv:
    command = argv[argv.index("--exec") + 1] if "--exec" in argv else ""
    mode = os.environ.get("FAKE_CLAUDE_BG_MODE", "ok")
    job_id = os.environ.get("FAKE_CLAUDE_JOB_ID", uuid.uuid4().hex[:8])
    if mode == "fail":
        sys.stderr.write("dispatch refused\n")
        sys.exit(1)
    if os.environ.get("FAKE_CLAUDE_BG_WRITE_STATE", "1") == "1" and state_path:
        with open(state_path, "w", encoding="utf-8") as fh:
            json.dump({"id": job_id, "command": command, "cwd": os.getcwd()}, fh)
    if mode == "hang":
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
    sys.stdout.write("backgrounded · %s · %s\n" % (job_id, command))
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


# ── reservation（外部副作用之前的原子门）────────────────────────────────────────

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
    elapsed = time.monotonic() - started
    payload = _json_stdout(proc)
    assert proc.returncode == 0, proc.stderr
    assert payload["ok"] is True
    assert payload["job_id"] == "75d34378"
    assert payload["reason_code"] == "ok"
    assert elapsed < JOB.DISPATCH_DEADLINE_SECONDS + 10  # 进程启动开销宽放
    assert payload["dispatch_duration_seconds"] < JOB.DISPATCH_DEADLINE_SECONDS


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
    assert elapsed < 30, "monotonic 5 秒 deadline 未生效，实际 %.1fs" % elapsed
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
        assert payload["dispatch_duration_seconds"] < JOB.DISPATCH_DEADLINE_SECONDS
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
