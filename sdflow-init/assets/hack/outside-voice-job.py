#!/usr/bin/env python3
"""outside-voice-job.py — Codex 宿主的 Claude outside-voice 后台作业 helper。

── 契约单一源（两份评审 SKILL 只引用本注释，不得转述细节）─────────────────────

本脚本**只编排后台生命周期**：它不 render prompt、不做 secret scan、不组装/接触
context 正文——那些一律仍归 `outside-voice.sh`（同目录、同代安装的既有权威实现）。
本脚本对 prompt 正文唯一的接触是**把 context 文件的绝对路径当 argv 传下去**。

  preflight [--json]
    无副作用能力探针（**MUST NOT** 创建 dummy job、MUST NOT 跑 `--bg --exec 'true'`）。
    stdout: 单行 JSON {"ok":bool,"reason_code":"ready"|"preflight-error","checks":{…}}
    stderr: 不通过时逐条 actionable 提示（升级 / 解禁策略 / 重跑 setup.sh）
    exit 0=ready | 1=preflight-error

  dispatch --run-dir <d> --site <s> --context-file <f> --repo-root <r>
           --runner claude --model <m> [--effort high] [--timeout 900]
    ① preflight（不通过即 5 秒级 fallback）→ ② `O_CREAT|O_EXCL` 建 `<site>.reserve`
    （**任何外部副作用之前**，同时机械核验同 site 唯一 + 本 run ≤2 slot）→
    ③ 在 monotonic 5 秒 deadline 内 `claude --bg --exec '<单条 shell 命令>'` →
    ④ 用 attempt nonce 在 `claude agents --all --json` 里核验**唯一** canonical job id →
    ⑤ 临时文件 + atomic rename 发布 `<site>.job.json`（0600）。
    stdout: 单行 JSON；失败时含 `state`（duplicate-site|slot-limit|unknown-cost|
            exec-error|preflight-error）与 `fallback_allowed`。
    exit 0=已派发 | 1=未派发（按 `fallback_allowed` 决定调用方能否立即同族 fallback）

  worker --run-dir <d> --site <s> --context-file <f> --repo-root <r>
         --runner <x> --model <m> --effort <e> --timeout <n>
         --attempt-nonce <hex> --run-id <id>
    **由 supervisor 在后台 shell 里执行，不给人手动调**。第一动作 = 把自身与 child 的
    stdout/stderr 直接重定向到 0600 的 `<site>.stdout`/`<site>.stderr`（在执行任何
    可携带 payload 的代码之前）；随后 started → child → terminal → rc 依序原子发布。
    exit 恒 0（真实结果一律经 `<site>.rc` 发布，MUST NOT 让 supervisor 的 job state
    充当结果通道）。

  version
    stdout: "outside-voice-job.py <ver>"                       exit 0

── 盘面即状态（ADR-2）───────────────────────────────────────────────────────────
本脚本**不持久化可变 status 字段**。`<site>.rc` 是唯一终态发布点；`claude agents` 的
`done/failed` 只提供 liveness，MUST NOT 决定 `ok`/`timeout`。status/await/collect 的
派生规则见 Task 2，本文件只负责把证据按 started → terminal → rc 的顺序原子放上盘面。
"""

import argparse
import hashlib
import json
import os
import re
import secrets
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

VERSION = "outside-voice-job.py 0.1.0"

SCHEMA_VERSION = 1

# `--bg --exec`、`--safe-mode` 与含 `--all`/`id`/`state` 的 agents JSON 的**共同**能力下限
# 〔design.md ADR-1 grill-amendment〕。版本只是必要条件，真实 dispatch 才是最终能力探针。
MIN_CLAUDE_VERSION = (2, 1, 169)

# 每轮每层实际 background voice 站点上限（design.md Non-Functional Requirements）。
MAX_SITES_PER_RUN = 2

# dispatch 的 monotonic deadline（秒）。超时 MUST 回收 spawn 进程树。
DISPATCH_DEADLINE_SECONDS = 5.0

# worker 启动的**独立**短 deadline（秒）：与 worker 自身的 timeout 分开，避免用 dispatch
# 时刻误杀排队中的合法 worker。只写进 job metadata 供 Task 2 的 status 派生消费。
STARTUP_DEADLINE_SECONDS = 5

DEFAULT_TIMEOUT_SECONDS = 900
MIN_TIMEOUT_SECONDS = 1
MAX_TIMEOUT_SECONDS = 3600

HELPER_NAME = "outside-voice.sh"
MANIFEST_NAME = "capability-manifest.json"
# 同代安装快照的成员：job helper + shell helper + 所需 data file。任一漂移即 preflight
# fail-closed（design.md Failure Modes「helper/skill/data 安装 skew」）。
MANIFEST_ENTRIES = ("outside-voice-job.py", "outside-voice.sh", "skill-principles.md")

# `<site>` 直接参与文件名拼装 ⇒ 字符集 MUST 收紧（挡 `../` 越目录与 shell 元字符）。
SITE_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
# run-id 同样进 argv（且默认取自 run-dir basename）⇒ 同样收紧，别把「shlex 会 quote」
# 当成可以放任任意串的理由（quoting 是最后一道，不是唯一一道）。
RUN_ID_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
MODEL_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._:+-]{0,127}\Z")
EFFORT_VALUES = ("low", "medium", "high")
RUNNER_VALUES = ("claude", "codex")
# v1 background transport 只在这两个已过 quoting/injection golden 的 POSIX 平台 ready。
SUPPORTED_SYS_PLATFORMS = ("darwin", "linux")

JOB_DIR = os.path.dirname(os.path.abspath(__file__))


# ── 基础工具 ──────────────────────────────────────────────────────────────────

def utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_iso_plus(seconds):
    ts = datetime.now(timezone.utc).timestamp() + seconds
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(path, payload, mode=0o600):
    """临时文件 + atomic rename 发布 JSON —— 读者永远看不到半成品。"""
    path = str(path)
    directory = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".tmp-" + os.path.basename(path) + "-")
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        tmp = None
    finally:
        if tmp is not None and os.path.exists(tmp):
            os.unlink(tmp)
    return path


def emit(payload, stream=None):
    (stream or sys.stdout).write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


# ── capability manifest（同代安装快照）────────────────────────────────────────

def manifest_generation(entries):
    blob = json.dumps(entries, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def compute_manifest(directory, entries=MANIFEST_ENTRIES):
    digests = {}
    for name in entries:
        digests[name] = sha256_file(os.path.join(str(directory), name))
    return {
        "schema_version": SCHEMA_VERSION,
        "entries": digests,
        "generation": manifest_generation(digests),
    }


def write_manifest(directory, entries=MANIFEST_ENTRIES):
    """写出同代安装快照。由 setup.sh 的安装步与测试共用同一份计算，防两份口径漂移。"""
    payload = compute_manifest(directory, entries)
    atomic_write_json(os.path.join(str(directory), MANIFEST_NAME), payload, mode=0o644)
    return payload


def verify_manifest(directory=None):
    directory = str(directory or JOB_DIR)
    path = os.path.join(directory, MANIFEST_NAME)
    hint = "安装快照不一致——在运行 checkout 重跑 `bash setup.sh` 刷新 ~/.sdflow/hack/"
    if not os.path.isfile(path):
        return {"ok": False, "detail": "capability manifest 缺失: %s" % path, "hint": hint}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:
        return {"ok": False, "detail": "capability manifest 不可解析: %s" % exc, "hint": hint}
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        return {"ok": False, "detail": "capability manifest schema_version 不受支持", "hint": hint}
    entries = data.get("entries")
    if not isinstance(entries, dict):
        return {"ok": False, "detail": "capability manifest entries 形状非法", "hint": hint}
    if sorted(entries) != sorted(MANIFEST_ENTRIES):
        return {"ok": False,
                "detail": "capability manifest 成员集与本代不符: %s" % sorted(entries),
                "hint": hint}
    if data.get("generation") != manifest_generation(entries):
        return {"ok": False,
                "detail": "capability manifest generation 与 entries 不自洽（疑似手改）",
                "hint": hint}
    skew = []
    for name, expected in sorted(entries.items()):
        target = os.path.join(directory, name)
        if not os.path.isfile(target):
            skew.append("%s 缺失" % name)
            continue
        if sha256_file(target) != expected:
            skew.append("%s 内容与快照不符" % name)
    if skew:
        return {"ok": False, "detail": "安装 skew: " + "; ".join(skew), "hint": hint}
    return {"ok": True, "detail": "generation=%s" % data["generation"], "hint": ""}


# ── preflight 各项检查（全部无副作用）────────────────────────────────────────

def _run_cli(argv, timeout):
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)


def check_posix_shell():
    if os.name != "posix":
        return {"ok": False,
                "detail": "os.name=%r" % os.name,
                "hint": "v1 后台通道只支持 POSIX 平台（darwin/linux）——其他平台一律同族 fallback"}
    if sys.platform not in SUPPORTED_SYS_PLATFORMS:
        return {"ok": False,
                "detail": "sys.platform=%r" % sys.platform,
                "hint": "v1 后台通道只支持 POSIX 平台（darwin/linux）——其他平台一律同族 fallback"}
    if not os.access("/bin/sh", os.X_OK):
        return {"ok": False,
                "detail": "/bin/sh 不可执行",
                "hint": "v1 后台通道要求可用的 POSIX shell（/bin/sh）"}
    return {"ok": True, "detail": "%s / /bin/sh" % sys.platform, "hint": ""}


def check_claude_version(claude_bin):
    hint = ("升级 Claude Code 到 %s 或更高（npm i -g @anthropic-ai/claude-code）——"
            "它是 `--bg --exec`、`--safe-mode` 与 agents JSON 的共同能力下限"
            % ".".join(str(x) for x in MIN_CLAUDE_VERSION))
    if not claude_bin:
        return {"ok": False, "detail": "PATH 上找不到 claude", "hint": hint}
    try:
        proc = _run_cli([claude_bin, "--version"], timeout=30)
    except Exception as exc:
        return {"ok": False, "detail": "claude --version 调用失败: %s" % exc, "hint": hint}
    if proc.returncode != 0:
        return {"ok": False, "detail": "claude --version 非零退出 rc=%d" % proc.returncode, "hint": hint}
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", proc.stdout or "")
    if not match:
        return {"ok": False, "detail": "claude --version 输出不可解析: %r" % (proc.stdout,), "hint": hint}
    found = tuple(int(x) for x in match.groups())
    if found < MIN_CLAUDE_VERSION:
        return {"ok": False,
                "detail": "claude %s < %s" % (".".join(str(x) for x in found),
                                              ".".join(str(x) for x in MIN_CLAUDE_VERSION)),
                "hint": hint}
    return {"ok": True, "detail": ".".join(str(x) for x in found), "hint": ""}


def check_agents_json(claude_bin):
    hint = ("`claude agents --all --json` 不可用——agent view 可能被 `disableAgentView` "
            "策略禁用；解除该策略（或改用同族 fallback）后重试")
    if not claude_bin:
        return {"ok": False, "detail": "PATH 上找不到 claude", "hint": hint}
    try:
        proc = _run_cli([claude_bin, "agents", "--all", "--json"], timeout=30)
    except Exception as exc:
        return {"ok": False, "detail": "agents --all --json 调用失败: %s" % exc, "hint": hint}
    if proc.returncode != 0:
        return {"ok": False,
                "detail": "agents --all --json 非零退出 rc=%d" % proc.returncode,
                "hint": hint}
    try:
        data = json.loads(proc.stdout)
    except Exception as exc:
        return {"ok": False, "detail": "agents JSON 不可解析: %s" % exc, "hint": hint}
    if not isinstance(data, list):
        return {"ok": False, "detail": "agents JSON 顶层不是 list: %s" % type(data).__name__, "hint": hint}
    return {"ok": True, "detail": "%d 个会话" % len(data), "hint": ""}


def run_preflight(job_dir=None):
    """无副作用能力探针。MUST NOT 创建 dummy job、MUST NOT 触发任何外部状态变更。"""
    job_dir = str(job_dir or JOB_DIR)
    claude_bin = shutil.which("claude")
    checks = {
        "posix-shell": check_posix_shell(),
        "claude-version": check_claude_version(claude_bin),
        "agents-json": check_agents_json(claude_bin),
        "capability-manifest": verify_manifest(job_dir),
    }
    ok = all(item["ok"] for item in checks.values())
    return {
        "ok": ok,
        "reason_code": "ready" if ok else "preflight-error",
        "claude_bin": claude_bin or "",
        "job_dir": job_dir,
        "checks": checks,
    }


def _print_preflight_hints(result, stream=None):
    stream = stream or sys.stderr
    for name, item in sorted(result["checks"].items()):
        if item["ok"]:
            continue
        stream.write("preflight 未通过 [%s]: %s\n" % (name, item["detail"]))
        if item.get("hint"):
            stream.write("  → %s\n" % item["hint"])


# ── reservation ───────────────────────────────────────────────────────────────

def reserve_path(run_dir, site):
    return os.path.join(str(run_dir), site + ".reserve")


def job_path(run_dir, site):
    return os.path.join(str(run_dir), site + ".job.json")


def classify_existing_reserve(run_dir, site):
    """已存在的 reserve 归类：有 job metadata = 重复派发；无 = unknown-cost。

    unknown-cost 的语义（design.md Sequence and Concurrency）：外部 dispatch 可能已被
    接受但 metadata 未发布 ⇒ 成本未知。此时 **MUST NOT 自动重派、MUST NOT 立即 fallback**
    （两者都会叠加一次模型费用），只允许显式 reconcile / 人工 cleanup（Task 3）。
    """
    if os.path.exists(job_path(run_dir, site)):
        return ("duplicate-site",
                "site=%s 在本 run 已有 job metadata —— 同 site 重复派发是硬失败" % site)
    return ("unknown-cost",
            "site=%s 存在残留 reserve 但无 job metadata（dispatch accepted 与 metadata "
            "发布之间可能已崩溃）—— 成本未知，只允许显式 reconcile/人工 cleanup" % site)


def acquire_reservation(run_dir, site, nonce, run_id):
    """`O_CREAT|O_EXCL` 建 reservation，并原子核验 slot 上限。

    返回 (ok, state, detail)。ok=False 时**不会**留下自己的 reserve。
    """
    path = reserve_path(run_dir, site)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "site": site,
        "run_id": run_id,
        "attempt_nonce": nonce,
        "created_at": utc_now_iso(),
        "dispatcher_pid": os.getpid(),
    }
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        state, detail = classify_existing_reserve(run_dir, site)
        return (False, state, detail)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    # slot 上限：先原子占坑、再数坑——超限就把自己的坑退回去（此刻尚无任何外部副作用）。
    held = sorted(name for name in os.listdir(str(run_dir)) if name.endswith(".reserve"))
    if len(held) > MAX_SITES_PER_RUN:
        os.unlink(path)
        return (False, "slot-limit",
                "本 run 已有 %d 个 reservation（上限 %d）——第三个不同 site 一律 fail-closed: %s"
                % (len(held) - 1, MAX_SITES_PER_RUN, ", ".join(held)))
    return (True, "reserved", path)


# ── dispatch ──────────────────────────────────────────────────────────────────

def _reject(message, state="usage-error", reason_code="preflight-error",
            fallback_allowed=True, **extra):
    payload = {"ok": False, "reason_code": reason_code, "state": state,
               "fallback_allowed": fallback_allowed, "detail": message}
    payload.update(extra)
    return payload


def _no_control_chars(value):
    return "\n" not in value and "\r" not in value and "\0" not in value


def _within(child, parent):
    child = os.path.realpath(child)
    parent = os.path.realpath(parent)
    return child == parent or child.startswith(parent + os.sep)


def build_worker_command(job_dir, run_dir, site, ctx, repo_root, runner, model,
                         effort, timeout, nonce, run_id):
    """组一条**唯一** shell command。

    只携带受校验的绝对路径、runner/model 与 timeout —— MUST NOT 携带 prompt 正文
    （context 只以路径形式出现，正文由 worker 下游的 outside-voice.sh 自己读）。
    v1 仅在已验证的 POSIX shell 上用 `shlex.join` quoting；未验证的平台由 preflight
    fail-closed，不在这里假装跨平台安全。
    """
    argv = [
        sys.executable,
        os.path.join(str(job_dir), "outside-voice-job.py"),
        "worker",
        "--run-dir", str(run_dir),
        "--site", site,
        "--context-file", str(ctx),
        "--repo-root", str(repo_root),
        "--runner", runner,
        "--model", model,
        "--effort", effort,
        "--timeout", str(timeout),
        "--attempt-nonce", nonce,
        "--run-id", run_id,
    ]
    for part in argv:
        if not _no_control_chars(part):
            raise ValueError("命令参数含换行/回车/NUL，拒绝组装: %r" % part)
    return shlex.join(argv)


def _kill_process_tree(proc):
    """回收 spawn 进程树：proc 以 start_new_session=True 起，故它就是组长。"""
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
    try:
        proc.wait(timeout=5)
    except Exception:
        pass


def _parse_job_id_hint(stdout_text):
    """从 `backgrounded · <id> · <cmd>` 里取 short id（**仅作交叉核验线索**）。

    权威 id 来自 `claude agents --all --json` 里唯一携带本次 attempt nonce 的条目；
    此处解析失败只是拿不到第二个信号，不构成失败判据（格式属 research preview，会漂）。
    """
    for line in (stdout_text or "").splitlines():
        idx = line.find("backgrounded")
        if idx < 0:
            continue
        match = re.search(r"\b([0-9a-f]{6,40})\b", line[idx + len("backgrounded"):])
        if match:
            return match.group(1)
    return None


def find_jobs_by_nonce(claude_bin, nonce, deadline_monotonic):
    """轮询 agents JSON，找出**所有**命令串里携带本次 attempt nonce 的 background job。

    nonce 由 `secrets.token_hex` 生成、只出现在本次下发命令里 ⇒ 它是「外部 job 是否
    真的产生了」这件事的**机械信号**（而不是靠 dispatch 自述成功）。
    """
    matches = []
    while True:
        try:
            proc = _run_cli([claude_bin, "agents", "--all", "--json"], timeout=30)
            data = json.loads(proc.stdout) if proc.returncode == 0 else []
        except Exception:
            data = []
        if isinstance(data, list):
            matches = [item for item in data
                       if isinstance(item, dict)
                       and item.get("kind") == "background"
                       and nonce in str(item.get("name") or "")]
        if matches or time.monotonic() >= deadline_monotonic:
            return matches
        time.sleep(0.2)


def cmd_dispatch(args):
    job_dir = JOB_DIR
    site = args.site or ""
    if not SITE_RE.match(site):
        return 1, _reject("site 名非法（只允许 [A-Za-z0-9._-]，且不得以 . - 开头）: %r" % site,
                          state="usage-error", fallback_allowed=False, site=site)
    if not MODEL_RE.match(args.model or ""):
        return 1, _reject("model 名非法: %r" % (args.model,), state="usage-error",
                          fallback_allowed=False, site=site)
    if args.effort not in EFFORT_VALUES:
        return 1, _reject("effort 非法: %r" % (args.effort,), state="usage-error",
                          fallback_allowed=False, site=site)
    if args.runner not in RUNNER_VALUES:
        return 1, _reject("runner 非法: %r" % (args.runner,), state="usage-error",
                          fallback_allowed=False, site=site)
    if not (MIN_TIMEOUT_SECONDS <= args.timeout <= MAX_TIMEOUT_SECONDS):
        return 1, _reject("timeout 越界（合法 %d..%d）: %d"
                          % (MIN_TIMEOUT_SECONDS, MAX_TIMEOUT_SECONDS, args.timeout),
                          state="usage-error", fallback_allowed=False, site=site)

    run_dir = os.path.realpath(args.run_dir)
    repo_root = os.path.realpath(args.repo_root)
    ctx = os.path.realpath(args.context_file)
    for label, path in (("run-dir", args.run_dir), ("repo-root", args.repo_root),
                        ("context-file", args.context_file)):
        if not _no_control_chars(path):
            return 1, _reject("%s 路径含换行/NUL: %r" % (label, path), state="usage-error",
                              fallback_allowed=False, site=site)
        if not os.path.isabs(path):
            return 1, _reject("%s MUST 为绝对路径: %r" % (label, path), state="usage-error",
                              fallback_allowed=False, site=site)
    if not os.path.isdir(run_dir):
        return 1, _reject("run-dir 不存在: %s" % run_dir, state="usage-error",
                          fallback_allowed=False, site=site)
    if not os.path.isfile(ctx) or not os.access(ctx, os.R_OK):
        return 1, _reject("context-file 不存在或不可读: %s" % ctx, state="usage-error",
                          fallback_allowed=False, site=site)
    if not _within(run_dir, repo_root):
        return 1, _reject("run-dir 越出 repo root: %s ⊄ %s" % (run_dir, repo_root),
                          state="usage-error", fallback_allowed=False, site=site)
    if not _within(ctx, repo_root):
        return 1, _reject("context-file 越出 repo root: %s ⊄ %s" % (ctx, repo_root),
                          state="usage-error", fallback_allowed=False, site=site)

    run_id = args.run_id or os.path.basename(run_dir)
    if not RUN_ID_RE.match(run_id):
        return 1, _reject("run-id 非法（只允许 [A-Za-z0-9._-]）: %r" % run_id,
                          state="usage-error", fallback_allowed=False, site=site)

    pre = run_preflight(job_dir)
    if not pre["ok"]:
        _print_preflight_hints(pre)
        return 1, _reject("preflight 未通过——不发起后台派发，立即同族 fallback",
                          state="preflight-error", reason_code="preflight-error",
                          fallback_allowed=True, site=site, checks=pre["checks"])
    claude_bin = pre["claude_bin"]

    nonce = secrets.token_hex(16)
    ok, state, detail = acquire_reservation(run_dir, site, nonce, run_id)
    if not ok:
        # duplicate-site / slot-limit / unknown-cost 一律是硬失败：MUST NOT 靠 fallback
        # 把「可能已经花掉的一次模型调用」再花第二次。
        return 1, _reject(detail, state=state, reason_code="exec-error",
                          fallback_allowed=False, site=site)

    try:
        command = build_worker_command(job_dir, run_dir, site, ctx, repo_root, args.runner,
                                       args.model, args.effort, args.timeout, nonce, run_id)
    except ValueError as exc:
        os.unlink(reserve_path(run_dir, site))
        return 1, _reject(str(exc), state="usage-error", fallback_allowed=False, site=site)

    dispatched_at = utc_now_iso()
    startup_deadline_at = utc_iso_plus(STARTUP_DEADLINE_SECONDS)
    start = time.monotonic()
    deadline = start + DISPATCH_DEADLINE_SECONDS
    timed_out = False
    stdout_text = ""
    stderr_text = ""
    rc = None
    try:
        proc = subprocess.Popen(
            [claude_bin, "--bg", "--exec", command],
            cwd=repo_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, start_new_session=True,
        )
    except Exception as exc:
        os.unlink(reserve_path(run_dir, site))
        return 1, _reject("claude --bg --exec 无法启动: %s" % exc, state="exec-error",
                          reason_code="exec-error", fallback_allowed=True, site=site)
    try:
        stdout_text, stderr_text = proc.communicate(timeout=max(0.05, deadline - time.monotonic()))
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_process_tree(proc)
        try:
            stdout_text, stderr_text = proc.communicate(timeout=5)
        except Exception:
            stdout_text, stderr_text = "", ""
    duration = time.monotonic() - start

    # 外部 job 是否真的产生了 —— 只认 attempt nonce 在 agents JSON 里的机械命中。
    lookup_deadline = deadline if not timed_out else time.monotonic()
    matches = find_jobs_by_nonce(claude_bin, nonce, lookup_deadline)

    if timed_out or rc != 0:
        why = ("dispatch 超过 monotonic %.0f 秒 deadline" % DISPATCH_DEADLINE_SECONDS
               if timed_out else "claude --bg --exec 非零退出 rc=%s" % rc)
        if matches:
            # 外部 job 已存在但本次没能完整发布 metadata ⇒ 成本未知，reserve 留给 reconcile。
            return 1, _reject(
                "%s，但已检出携带本次 attempt nonce 的外部 job（%d 个）——成本未知，"
                "禁止自动重派、禁止立即 fallback，请用显式 reconcile 处理"
                % (why, len(matches)),
                state="unknown-cost", reason_code="exec-error", fallback_allowed=False,
                site=site, run_dir=run_dir, attempt_nonce=nonce,
                dispatch_duration_seconds=round(duration, 3),
                stderr_bytes=len(stderr_text or ""))
        # 尚未产生外部 job ⇒ 清理 reserve，允许 5 秒级同族 fallback。
        try:
            os.unlink(reserve_path(run_dir, site))
        except OSError:
            pass
        return 1, _reject("%s；未检出任何携带本次 attempt nonce 的外部 job，已回收 reservation" % why,
                          state="exec-error", reason_code="exec-error", fallback_allowed=True,
                          site=site, run_dir=run_dir,
                          dispatch_duration_seconds=round(duration, 3),
                          stderr_bytes=len(stderr_text or ""))

    if len(matches) != 1:
        return 1, _reject(
            "无法核验唯一 canonical job id：携带本次 attempt nonce 的 background job 有 %d 个"
            % len(matches),
            state="unknown-cost", reason_code="exec-error", fallback_allowed=False,
            site=site, run_dir=run_dir, attempt_nonce=nonce,
            dispatch_duration_seconds=round(duration, 3))

    job = matches[0]
    job_id = str(job.get("id") or "")
    if not job_id:
        return 1, _reject("匹配到的 background job 无 id 字段", state="unknown-cost",
                          reason_code="exec-error", fallback_allowed=False, site=site)
    hint = _parse_job_id_hint(stdout_text)
    if hint and hint != job_id:
        return 1, _reject(
            "canonical job id 交叉核验不一致：dispatch stdout=%s，agents JSON=%s" % (hint, job_id),
            state="unknown-cost", reason_code="exec-error", fallback_allowed=False, site=site)

    metadata = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "site": site,
        "repo_root": repo_root,
        "run_dir": run_dir,
        "context_file": ctx,
        "attempt_nonce": nonce,
        "runner": args.runner,
        "model": args.model,
        "effort": args.effort,
        "platform": os.name,
        "sys_platform": sys.platform,
        "job_id": job_id,
        "session_id": job.get("sessionId"),
        "dispatched_at": dispatched_at,
        "startup_deadline_at": startup_deadline_at,
        "timeout_seconds": args.timeout,
        "command_sha256": hashlib.sha256(command.encode("utf-8")).hexdigest(),
        "job_helper_version": VERSION,
        "dispatch_duration_seconds": round(duration, 3),
    }
    atomic_write_json(job_path(run_dir, site), metadata, mode=0o600)

    return 0, {
        "ok": True,
        "reason_code": "ok",
        "state": "dispatched",
        "site": site,
        "run_dir": run_dir,
        "run_id": run_id,
        "job_id": job_id,
        "session_id": job.get("sessionId"),
        "attempt_nonce": nonce,
        "dispatched_at": dispatched_at,
        "dispatch_duration_seconds": round(duration, 3),
        "timeout_seconds": args.timeout,
        "runner": args.runner,
        "model": args.model,
        "effort": args.effort,
    }


# ── worker ────────────────────────────────────────────────────────────────────

def publish_started(run_dir, site, nonce, run_id):
    payload = {
        "schema_version": SCHEMA_VERSION,
        "site": site,
        "run_id": run_id,
        "attempt_nonce": nonce,
        "started_at": utc_now_iso(),
        "worker": {
            "pid": os.getpid(),
            "ppid": os.getppid(),
            "pgid": os.getpgid(0),
            "sid": os.getsid(0),
            "executable": sys.executable,
        },
    }
    atomic_write_json(os.path.join(str(run_dir), site + ".started.json"), payload, mode=0o600)
    return payload


def publish_rc(run_dir, site, rc):
    """rc 是**唯一终态发布点** ⇒ 临时文件 + atomic rename，且恒为纯十进制。"""
    path = os.path.join(str(run_dir), site + ".rc")
    fd, tmp = tempfile.mkstemp(dir=str(run_dir), prefix=".tmp-" + site + ".rc-")
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("%d" % rc)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        tmp = None
    finally:
        if tmp is not None and os.path.exists(tmp):
            os.unlink(tmp)
    return path


def publish_terminal(run_dir, site, nonce, run_id, rc):
    """先写 terminal witness，**再**原子发布 rc —— 顺序是契约，不是风格。

    collect 只在 rc 出现后才读 stdout；若 rc 先于 witness 落盘，就会出现「已判终态却
    没有可核验的 digest」的窗口，等于把半成品放进 findings 池的门开了一条缝。
    """
    stdout_path = os.path.join(str(run_dir), site + ".stdout")
    stderr_path = os.path.join(str(run_dir), site + ".stderr")
    digest = sha256_file(stdout_path) if os.path.isfile(stdout_path) else None
    payload = {
        "schema_version": SCHEMA_VERSION,
        "site": site,
        "run_id": run_id,
        "attempt_nonce": nonce,
        "terminal_at": utc_now_iso(),
        "stdout_sha256": digest,
        "stdout_bytes": os.path.getsize(stdout_path) if os.path.isfile(stdout_path) else 0,
        "stderr_bytes": os.path.getsize(stderr_path) if os.path.isfile(stderr_path) else 0,
    }
    atomic_write_json(os.path.join(str(run_dir), site + ".terminal.json"), payload, mode=0o600)
    publish_rc(run_dir, site, rc)
    return payload


def cmd_worker(args):
    run_dir = args.run_dir
    site = args.site
    if not SITE_RE.match(site or ""):
        sys.stderr.write("worker: site 名非法: %r\n" % (site,))
        return 2, None
    if not os.path.isdir(run_dir):
        sys.stderr.write("worker: run-dir 不存在: %s\n" % run_dir)
        return 2, None

    # 🔴 第一动作：在执行**任何**可携带 payload 的代码之前完成重定向。
    # 目的不是省事，是不让原始输出流经 outer supervisor 的 transcript
    # （`claude logs <id>` 可读）——那是一条未经出境 secret scan 的旁路出境面。
    out_fd = os.open(os.path.join(run_dir, site + ".stdout"),
                     os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    err_fd = os.open(os.path.join(run_dir, site + ".stderr"),
                     os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass
    os.dup2(out_fd, 1)
    os.dup2(err_fd, 2)
    os.close(out_fd)
    os.close(err_fd)

    publish_started(run_dir, site, args.attempt_nonce, args.run_id)

    helper = os.path.join(JOB_DIR, HELPER_NAME)
    env = os.environ.copy()
    env["SDFLOW_VOICE_RUNNER"] = args.runner
    if args.model:
        env["SDFLOW_VOICE_MODEL"] = args.model
    rc = 127
    try:
        if not os.path.isfile(helper):
            sys.stderr.write("worker: shell helper 缺失: %s\n" % helper)
        else:
            rc = subprocess.call(
                ["bash", helper, "exec", "--context-file", args.context_file,
                 "--timeout", str(args.timeout)],
                cwd=args.repo_root if os.path.isdir(args.repo_root) else None,
                stdin=subprocess.DEVNULL,
            )
    except Exception as exc:
        sys.stderr.write("worker: helper 启动失败: %s\n" % exc)
        rc = 126
    # 被信号杀死时 subprocess 返回负数；按 shell 惯例归一成 128+signum，保证 rc 恒为纯十进制。
    if rc < 0:
        rc = 128 + (-rc)
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass
    publish_terminal(run_dir, site, args.attempt_nonce, args.run_id, rc)
    return 0, None


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(prog="outside-voice-job.py", add_help=True)
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("version")
    sub.add_parser("preflight")

    def add_common(p):
        p.add_argument("--run-dir", required=True)
        p.add_argument("--site", required=True)
        p.add_argument("--context-file", required=True)
        p.add_argument("--repo-root", required=True)
        p.add_argument("--runner", default="claude")
        p.add_argument("--model", default="")
        p.add_argument("--effort", default="high")
        p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
        p.add_argument("--run-id", default="")

    dispatch = sub.add_parser("dispatch")
    add_common(dispatch)

    worker = sub.add_parser("worker")
    add_common(worker)
    worker.add_argument("--attempt-nonce", required=True)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "version":
        sys.stdout.write(VERSION + "\n")
        return 0
    if args.command == "preflight":
        result = run_preflight()
        emit(result)
        if not result["ok"]:
            _print_preflight_hints(result)
            return 1
        return 0
    if args.command == "dispatch":
        code, payload = cmd_dispatch(args)
        if payload is not None:
            emit(payload)
        return code
    if args.command == "worker":
        code, _ = cmd_worker(args)
        return code
    parser.print_usage(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
