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
    runner/model/effort 经 `SDFLOW_VOICE_RUNNER` / `SDFLOW_VOICE_MODEL` /
    `SDFLOW_VOICE_EFFORT` **环境变量**下发（helper 的 `exec` 只吃 --context-file/--timeout）。
    exit 恒 0（真实结果一律经 `<site>.rc` 发布，MUST NOT 让 supervisor 的 job state
    充当结果通道）。

  status --run-dir <d> --site <s> [--timeout <n>]
    **纯派生**的当前归类：读盘面（job/started/terminal/rc）+ 一次 `claude agents` liveness 探针。
    **MUST NOT 在终态之前读 stdout**（半成品输出没有任何进 findings 池的通道）。
    stdout: 单行 JSON（见下方「派生输出」）
    exit 0=ok | 1=非 ok（含未终态） | 2=usage-error

  await --run-dir <d> --site <s> [--timeout <n>] [--max-wait <n>] [--poll-interval <f>]
    有界等待到终态。上界**不从 dispatch 时刻起算**：started sidecar 未发布时受**独立**的
    startup deadline 约束；已发布则为可信 `started_at` + timeout + 30 秒 grace。
    `--timeout` 缺省取 `job.json` 里 dispatch 当时记下的 `timeout_seconds`（即既有
    `outside-voice.async-timeout-seconds` 的值）；显式给出时同样受 1..3600 约束。
    liveness 探针**独立于 poll 节流**（每 5 秒最多一次，缓存复用）：盘面读是本地 stat，
    `claude agents` 是外部进程冷启动，MUST NOT 每轮 poll 都 spawn 一次。
    stdout: status 的同一份 JSON + `waited_seconds`
    exit 0=ok | 1=其他（含未终态） | 2=usage-error

  collect --run-dir <d> --site <s> [--timeout <n>]
    **幂等**收集：只在 rc 发布后读 stdout，核对 terminal witness 的 digest，
    首次收集把整份结果原子发布为 `<site>.collected.json`（**首写者胜**），
    重复 collect 原样回放该文件 ⇒ 输出与分类逐字节一致。
    幂等的边界是 **rc 已发布**：LOST / RESERVED 这类由非 durable 证据（liveness 探针、
    startup deadline）推出的终态**只返回、不落见证**——worker 可能只是慢，冻结它等于把
    一次已计费的 voice 永久丢弃；这类站点交 reconcile 处置。
    stdout: 单行 JSON（含 dispatched/started/terminal/collected 时刻、自然 duration、
            runner/model/effort、stdout digest/bytes/lines、stderr bytes/lines）
    exit 0=ok | 1=其他（含未终态） | 2=usage-error

  version
    stdout: "outside-voice-job.py <ver>"                       exit 0

── 盘面即状态（ADR-2）───────────────────────────────────────────────────────────
本脚本**不持久化可变 status 字段**。`<site>.rc` 是唯一终态发布点；`claude agents` 的
`done/failed` 只提供 liveness，MUST NOT 决定 `ok`/`timeout`。
（`<site>.collected.json` 不是可变 status：它是**首次 collect 的不可变见证**，
OVBG-02 要求 collect 幂等返回**首次** `collected_at` ⇒ 跨进程只能靠落盘。）

── 派生输出（status/await/collect 共用同一形状）─────────────────────────────────
  state ∈ MISSING | RESERVED | STARTING | RUNNING | SUCCEEDED | TIMED_OUT | FAILED |
          LOST | CORRUPT
  reason_code ∈ ok | timeout | secret-hit | exec-error | null（null = 未终态，不可收集）
  `ok` ⟺ reason_code == "ok" ⟺ exit 0。**任何 pending/lost/corrupt 组合恒不产出 ok。**

  ⚠️ **exit 2（usage-error）的 payload 不是这个形状**：入参本身非法（site 名 / run-dir /
  timeout 越界）时走 reject 形状 `{ok:false, state:"usage-error", reason_code:"exec-error",
  fallback_allowed:false, detail}` —— **没有 `terminal` / `rc` / 时刻等派生字段**。
  调用方 MUST 先看 exit code，MUST NOT 按 0|1 两分法直接读 `terminal`。
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

# attempt nonce 核验的**独立** grace（秒）—— MUST NOT 与 DISPATCH_DEADLINE_SECONDS 共用预算。
# 共用会让「dispatch 越慢、核验窗口越短」，极端下只轮询一次：一次 supervisor 注册延迟就把
# **成功的** dispatch 误判成 unknown-cost（fallback_allowed=false ⇒ 人工 reconcile 硬阻塞）。
# 超时被 SIGKILL 之后同样走这份 grace——那恰是注册最可能滞后的时刻，零 grace 会同时留下
# 一个孤儿付费 job 和一次 fallback 重付，正是 design.md「dispatch 后 metadata 前崩溃」要杀的形态。
NONCE_LOOKUP_GRACE_SECONDS = 5.0

# 单次 claude CLI 探针的上限（秒）：preflight 两条探针与 nonce 核验轮询共用同一口径。
# 本机实测 `claude --version` 0.06s、`claude agents --all --json` 0.17s ⇒ 5 秒已是极宽上限；
# 旧值 30 秒会让「5 秒级诚实降级」在 CLI 卡死时退化到 ~60 秒（preflight 两条串行）。
CLI_PROBE_TIMEOUT_SECONDS = 5

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
        proc = _run_cli([claude_bin, "--version"], timeout=CLI_PROBE_TIMEOUT_SECONDS)
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
        proc = _run_cli([claude_bin, "agents", "--all", "--json"], timeout=CLI_PROBE_TIMEOUT_SECONDS)
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

def release_reservation(run_dir, site):
    """回收自己的 reserve —— **MUST NOT 让删除失败掀掉整个 dispatch**。

    调用方此刻正走在失败/降级路径上，唯一还要交付的东西就是 stdout 上那行带
    `fallback_allowed` 的 JSON。一个裸 `os.unlink` 的 traceback 会让 stdout 空掉，
    调用方读不到 `fallback_allowed`，于是一次本可立即同族 fallback 的失败变成哑失败。
    返回 True=已删除 / False=删除未成功（reserve 可能仍在盘上，留给 reconcile）。
    """
    try:
        os.unlink(reserve_path(run_dir, site))
        return True
    except OSError:
        return False


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
    """从 `backgrounded · <id> · <cmd>` 里取 short id（**仅作匹配线索，永不单独构成失败**）。

    权威 id 来自 `claude agents --all --json` 里唯一携带本次 attempt nonce 的条目；
    此处解析失败只是拿不到第二个信号（格式属 research preview，会漂）。解析**成功**时
    同样不作为失败判据——只并入 `find_jobs_by_nonce` 的匹配通道，最终仍由「命中是否唯一」
    这一条 fail-closed 判据决定；否则一次格式漂移解析出的垃圾 hex 就能否掉一次好 dispatch。
    """
    for line in (stdout_text or "").splitlines():
        idx = line.find("backgrounded")
        if idx < 0:
            continue
        match = re.search(r"\b([0-9a-f]{6,40})\b", line[idx + len("backgrounded"):])
        if match:
            return match.group(1)
    return None


def _job_matches_attempt(item, nonce, id_hint):
    """本次 attempt 的两条并列匹配通道：命令串带 nonce **或** id 等于本次 dispatch stdout 的 hint。

    🔴 契约约束（对真 CLI 实测）：`kind=background` 且 `state=working` 的条目里 `name` 承载
    完整命令串（故 nonce 可命中）；但 **`state=done` 的条目没有 `name` 字段**——极快失败的
    worker（如 helper 缺失，<1s 即终态）会让只认 `name` 的轮询扑空，从而把一次**真的已经
    产生的**外部 job 误判成「没产生」。故 id 通道 MUST 并列存在，不是冗余。
    """
    if not isinstance(item, dict) or item.get("kind") != "background":
        return False
    if nonce in str(item.get("name") or ""):
        return True
    return bool(id_hint) and str(item.get("id") or "") == id_hint


def find_jobs_by_nonce(claude_bin, nonce, deadline_monotonic, id_hint=None):
    """轮询 agents JSON，找出**所有**属于本次 attempt 的 background job。

    nonce 由 `secrets.token_hex` 生成、只出现在本次下发命令里 ⇒ 它是「外部 job 是否
    真的产生了」这件事的**机械信号**（而不是靠 dispatch 自述成功）。id_hint 是同一次
    dispatch 自己 stdout 里的 short id，同属本次 attempt，作并列通道见 `_job_matches_attempt`。
    """
    matches = []
    while True:
        try:
            proc = _run_cli([claude_bin, "agents", "--all", "--json"], timeout=CLI_PROBE_TIMEOUT_SECONDS)
            data = json.loads(proc.stdout) if proc.returncode == 0 else []
        except Exception:
            data = []
        if isinstance(data, list):
            matches = [item for item in data if _job_matches_attempt(item, nonce, id_hint)]
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
        release_reservation(run_dir, site)
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
        release_reservation(run_dir, site)
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

    # 外部 job 是否真的产生了 —— 只认本次 attempt 在 agents JSON 里的机械命中。
    # 🔴 核验用**独立** grace（见 NONCE_LOOKUP_GRACE_SECONDS），两条分支同一口径：
    # 既不跟 dispatch 抢同一份 5 秒预算，超时被 kill 之后也不是零 grace。
    id_hint = _parse_job_id_hint(stdout_text)
    lookup_deadline = time.monotonic() + NONCE_LOOKUP_GRACE_SECONDS
    matches = find_jobs_by_nonce(claude_bin, nonce, lookup_deadline, id_hint=id_hint)

    # 🔴 duration MUST 覆盖到核验结束：它是「5 秒级诚实降级」对外唯一的可机读锚。
    # 若只算到 communicate 返回，这个数从构造上就 <DISPATCH_DEADLINE_SECONDS，
    # 任何拿它跟 deadline 比的断言都恒真——等于没有锚。
    duration = time.monotonic() - start

    if timed_out or rc != 0:
        why = ("dispatch 超过 monotonic %.0f 秒 deadline" % DISPATCH_DEADLINE_SECONDS
               if timed_out else "claude --bg --exec 非零退出 rc=%s" % rc)
        if matches:
            # 外部 job 已存在但本次没能完整发布 metadata ⇒ 成本未知，reserve 留给 reconcile。
            return 1, _reject(
                "%s，但已检出属于本次 attempt 的外部 job（%d 个）——成本未知，"
                "禁止自动重派、禁止立即 fallback，请用显式 reconcile 处理"
                % (why, len(matches)),
                state="unknown-cost", reason_code="exec-error", fallback_allowed=False,
                site=site, run_dir=run_dir, attempt_nonce=nonce,
                dispatch_duration_seconds=round(duration, 3),
                stderr_bytes=len(stderr_text or ""))
        # 尚未产生外部 job ⇒ 清理 reserve，允许 5 秒级同族 fallback。
        release_reservation(run_dir, site)
        return 1, _reject("%s；未检出任何属于本次 attempt 的外部 job，已回收 reservation" % why,
                          state="exec-error", reason_code="exec-error", fallback_allowed=True,
                          site=site, run_dir=run_dir,
                          dispatch_duration_seconds=round(duration, 3),
                          stderr_bytes=len(stderr_text or ""))

    # 唯一 fail-closed 判据 = 命中是否唯一（两条匹配通道并集之后仍须收敛到一个 job）。
    # stdout hint 只参与匹配、不再单独当「不一致」判死：它的格式属 research preview，
    # 一次漂移解出的垃圾 hex 若能否掉一次好 dispatch，就把 `_parse_job_id_hint` 的
    # 「解析不构成失败判据」写成了空话。
    if len(matches) != 1:
        return 1, _reject(
            "无法核验唯一 canonical job id：属于本次 attempt 的 background job 有 %d 个"
            % len(matches),
            state="unknown-cost", reason_code="exec-error", fallback_allowed=False,
            site=site, run_dir=run_dir, attempt_nonce=nonce,
            dispatch_duration_seconds=round(duration, 3))

    job = matches[0]
    job_id = str(job.get("id") or "")
    if not job_id:
        return 1, _reject("匹配到的 background job 无 id 字段", state="unknown-cost",
                          reason_code="exec-error", fallback_allowed=False, site=site)

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
    # 🔴 env 是 worker→helper 之间**唯一**的 runner/model/effort 通道（helper 的既有 `exec`
    # 契约只吃 --context-file / --timeout 两个 flag）⇒ 下面的 subprocess.call MUST 传 `env=env`。
    # 漏传 = helper 读不到 SDFLOW_VOICE_RUNNER（Codex 宿主的环境里本就没有它）⇒ 立即 exit 1
    # 「host=unknown」，整条后台通道对**真** voice dead on arrival，而 fake helper 全都不看 env、
    # 照样绿 —— 这条接缝的回归锚见 test_worker_passes_runner_model_effort_env_to_real_helper。
    env = os.environ.copy()
    env["SDFLOW_VOICE_RUNNER"] = args.runner
    if args.model:
        env["SDFLOW_VOICE_MODEL"] = args.model
    if args.effort:
        # effort 与 runner/model 同路下发，让 job.json 里记的 effort 是**真实下发值**而非装饰。
        # 注：把它变成 `--effort <e>` argv 属 outside-voice.sh 侧（Task 4）；本票不改该文件，
        # 故当前这一格是「已接线、下游尚未消费」——Task 4 接上即生效，无需再回头改 worker。
        env["SDFLOW_VOICE_EFFORT"] = args.effort
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
                env=env,
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


# ── status / await / collect：终态派生 ────────────────────────────────────────

# await 的固定 grace（秒）——design.md Non-Functional Requirements「await grace 固定 30 秒」。
# 它加在**可信 started_at** 之上，不是加在 dispatch 时刻上。
AWAIT_GRACE_SECONDS = 30

DEFAULT_POLL_INTERVAL_SECONDS = 0.5
MIN_POLL_INTERVAL_SECONDS = 0.05
MAX_POLL_INTERVAL_SECONDS = 5.0
# 单次 await 调用的外层上界上限：派生上界最坏 = timeout(≤3600) + grace(30)。
MAX_AWAIT_WAIT_SECONDS = MAX_TIMEOUT_SECONDS + AWAIT_GRACE_SECONDS

# 🔴 liveness 探针的**独立**节流间隔（秒）——与 poll 间隔解耦。
# 盘面读是本地 stat（便宜，按 poll-interval 走）；`claude agents --all --json` 是**外部
# 进程冷启动**（实测 ~0.17 秒，CLI 卡顿时吃满 CLI_PROBE_TIMEOUT_SECONDS）。若每轮都探，
# 一次上界 timeout(3600)+grace 的 await 能烧掉上千次 Node 冷启动。
# 代价：liveness 变化（job 突然消失）最多晚 5 秒被看见 —— 而 rc 一旦发布就**优先于**
# liveness 参与判定（ADR-2），所以这段陈旧窗口不会推迟任何真实终态的识别。
LIVENESS_PROBE_INTERVAL_SECONDS = 5.0

STATE_MISSING = "MISSING"
STATE_RESERVED = "RESERVED"
STATE_STARTING = "STARTING"
STATE_RUNNING = "RUNNING"
STATE_SUCCEEDED = "SUCCEEDED"
STATE_TIMED_OUT = "TIMED_OUT"
STATE_FAILED = "FAILED"
STATE_LOST = "LOST"
STATE_CORRUPT = "CORRUPT"

# 未终态集合：这三个状态**没有** reason_code（null），故永远不可能被误读成 `ok`。
PENDING_STATES = frozenset({STATE_RESERVED, STATE_STARTING, STATE_RUNNING})

REASON_OK = "ok"
REASON_TIMEOUT = "timeout"
REASON_SECRET_HIT = "secret-hit"
REASON_EXEC_ERROR = "exec-error"

# 🔴 rc → reason_code 的**唯一**映射源，与两份评审 SKILL 调用协议 ⑦ 的同步分支同表
# （HAE-09：async dispatch 只改执行时机与托管方，reason_code 枚举语义 MUST 不变）。
# `3` 单列的理由是**行为差异而非美观**：secret-hit 意味着「本次 voice 拒发且不 fallback」，
# 若并入 exec-error，调用方会拿同一份已命中 secret 的 context 再派一次同族 fallback。
RC_TIMEOUT = 124
RC_SECRET_HIT = 3

# `claude agents --all --json` 的 state 值分档。**只有这一档能判定 job 已终结**；
# 其余（含 schema 漂移出的未知值）一律当「探不到」——探针无判别力 MUST NOT 触发降级，
# 否则一次 CLI 改名就把所有在飞的合法 worker 判成 LOST，整条通道退回 efficacy=0。
LIVENESS_TERMINAL = frozenset({"done", "failed", "stopped", "missing"})
LIVENESS_UNAVAILABLE = "unavailable"

# job.json 的必填字段：任一缺失即 CORRUPT（OVBG-02「元数据损坏不得猜成功」）。
JOB_REQUIRED_FIELDS = (
    "schema_version", "run_id", "site", "repo_root", "run_dir", "attempt_nonce",
    "runner", "model", "effort", "job_id", "dispatched_at", "startup_deadline_at",
    "timeout_seconds",
)


def parse_utc_iso(value):
    """`YYYY-MM-DDTHH:MM:SSZ` → epoch 秒；不可解析返回 None（调用方一律 fail-closed）。"""
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc).timestamp()
    except Exception:
        return None


def collected_path(run_dir, site):
    return os.path.join(str(run_dir), site + ".collected.json")


def stdout_stat_evidence(run_dir, site):
    """**只 stat 不读**：status 判「rc=0 时 stdout 是否非空」只需要大小。

    单列成函数是为了让「终态前有没有碰过 stdout」变成可 spy 的机械锚，
    而不是靠通读实现自证（见 test_status_never_reads_stdout_before_terminal）。
    """
    path = os.path.join(str(run_dir), site + ".stdout")
    if not os.path.isfile(path):
        return {"exists": False, "bytes": 0, "path": os.path.realpath(path)}
    try:
        size = os.path.getsize(path)
    except OSError:
        return {"exists": False, "bytes": 0, "path": os.path.realpath(path)}
    return {"exists": True, "bytes": size, "path": os.path.realpath(path)}


def stdout_read_evidence(run_dir, site):
    """**真正读 stdout 正文的唯一入口** —— MUST 只在 rc 已发布后调用（collect 专用）。"""
    path = os.path.join(str(run_dir), site + ".stdout")
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        return {"ok": False, "detail": "stdout 不可读: %s" % exc}
    lines = data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
    return {"ok": True, "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data), "lines": lines, "path": os.path.realpath(path)}


def stderr_stat_evidence(run_dir, site):
    """stderr **只出结构化计数**：它绕过出境 secret scan，正文 MUST NOT 进入任何 tracked 产物。"""
    path = os.path.join(str(run_dir), site + ".stderr")
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        return {"bytes": 0, "lines": 0}
    lines = data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
    return {"bytes": len(data), "lines": lines}


def load_job_metadata(run_dir, site):
    """→ (kind, data, detail)，kind ∈ {"ok","corrupt","absent"}。"""
    path = job_path(run_dir, site)
    if not os.path.isfile(path):
        return ("absent", None, "job metadata 不存在: %s" % path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:
        return ("corrupt", None, "job metadata 不可解析: %s" % exc)
    if not isinstance(data, dict):
        return ("corrupt", None, "job metadata 顶层不是 object")
    if data.get("schema_version") != SCHEMA_VERSION:
        return ("corrupt", data,
                "job metadata schema_version 不受支持（schema drift）: %r"
                % (data.get("schema_version"),))
    missing = [name for name in JOB_REQUIRED_FIELDS
               if data.get(name) in (None, "")]
    if missing:
        return ("corrupt", data, "job metadata 缺字段: %s" % ", ".join(missing))
    if data.get("site") != site:
        return ("corrupt", data,
                "job metadata site 与请求不符: %r ≠ %r" % (data.get("site"), site))
    if os.path.realpath(str(data.get("run_dir"))) != os.path.realpath(str(run_dir)):
        return ("corrupt", data,
                "job metadata run_dir 与请求不符: %r" % (data.get("run_dir"),))
    timeout = data.get("timeout_seconds")
    if isinstance(timeout, bool) or not isinstance(timeout, int) \
            or not (MIN_TIMEOUT_SECONDS <= timeout <= MAX_TIMEOUT_SECONDS):
        return ("corrupt", data,
                "job metadata timeout_seconds 非整或越界（合法 %d..%d）: %r"
                % (MIN_TIMEOUT_SECONDS, MAX_TIMEOUT_SECONDS, timeout))
    for field in ("dispatched_at", "startup_deadline_at"):
        if parse_utc_iso(data.get(field)) is None:
            return ("corrupt", data, "job metadata %s 时刻不可解析: %r" % (field, data.get(field)))
    return ("ok", data, "")


def load_witness(run_dir, site, suffix, job, time_field):
    """读 started/terminal witness 并**重新核验 identity**（site / run_id / attempt nonce）。

    → (kind, data, detail)，kind ∈ {"ok","corrupt","absent"}。
    identity 核不过 ⇒ corrupt：上一轮遗留或被换过的 witness MUST NOT 当本次结果采信。
    """
    path = os.path.join(str(run_dir), site + suffix)
    if not os.path.isfile(path):
        return ("absent", None, "")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:
        return ("corrupt", None, "%s%s 不可解析: %s" % (site, suffix, exc))
    if not isinstance(data, dict):
        return ("corrupt", None, "%s%s 顶层不是 object" % (site, suffix))
    if data.get("schema_version") != SCHEMA_VERSION:
        return ("corrupt", data, "%s%s schema_version 不受支持" % (site, suffix))
    for field, expected in (("site", site), ("run_id", job.get("run_id")),
                            ("attempt_nonce", job.get("attempt_nonce"))):
        if data.get(field) != expected:
            return ("corrupt", data,
                    "%s%s 的 %s 与本次 attempt 不符: %r ≠ %r"
                    % (site, suffix, field, data.get(field), expected))
    if parse_utc_iso(data.get(time_field)) is None:
        return ("corrupt", data, "%s%s 的 %s 不可解析" % (site, suffix, time_field))
    return ("ok", data, "")


def read_rc(run_dir, site):
    """→ (present, value_or_None, raw)。value 为 None 表示「rc 已发布但不是纯十进制」。"""
    path = os.path.join(str(run_dir), site + ".rc")
    if not os.path.isfile(path):
        return (False, None, None)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
    except OSError as exc:
        return (True, None, "<unreadable: %s>" % exc)
    text = raw.strip()
    if not re.match(r"\A\d+\Z", text):
        return (True, None, raw)
    return (True, int(text), raw)


def probe_liveness(job_id, claude_bin=None):
    """一次 `claude agents --all --json`，按 **id** 通道定位本 job 的 state。

    🔴 MUST 走 id 而非 name：真机实测 `state="done"` 的 background 条目**没有 `name` 字段**
    （Task 1 已独立核实）——只认 name 的探针会把每一个已完成的 job 报成 missing。
    任何取不到答案的情形一律返回 `unavailable`（探不到 ≠ 丢了，见 LIVENESS_TERMINAL 注释）。
    """
    claude_bin = claude_bin or shutil.which("claude")
    if not claude_bin or not job_id:
        return LIVENESS_UNAVAILABLE
    try:
        proc = _run_cli([claude_bin, "agents", "--all", "--json"],
                        timeout=CLI_PROBE_TIMEOUT_SECONDS)
        if proc.returncode != 0:
            return LIVENESS_UNAVAILABLE
        data = json.loads(proc.stdout)
    except Exception:
        return LIVENESS_UNAVAILABLE
    if not isinstance(data, list):
        return LIVENESS_UNAVAILABLE
    for item in data:
        if isinstance(item, dict) and str(item.get("id") or "") == str(job_id):
            state = str(item.get("state") or "").strip().lower()
            return state or LIVENESS_UNAVAILABLE
    return "missing"


def _status_payload(state, reason_code, detail, **extra):
    payload = {
        "ok": reason_code == REASON_OK,
        "state": state,
        "terminal": state not in PENDING_STATES,
        "reason_code": reason_code,
        "detail": detail,
        "unknown_cost": False,
        "liveness": None,
        "rc": None,
        "run_id": None,
        "job_id": None,
        "attempt_nonce": None,
        "runner": None,
        "model": None,
        "effort": None,
        "dispatched_at": None,
        "started_at": None,
        "terminal_at": None,
        "startup_deadline_at": None,
        "deadline_at": None,
        "timeout_seconds": None,
        "stdout_bytes": None,
        "stdout_sha256": None,
    }
    payload.update(extra)
    return payload


def derive_status(run_dir, site, liveness=None, now=None, claude_bin=None,
                  timeout_override=None, _rechecked=False):
    """从盘面 + liveness **纯派生**当前归类。不写任何文件、不做任何破坏性动作。

    判定顺序是契约（不是风格）：
      ① job metadata（坏 ⇒ CORRUPT，**此时不看 rc、不碰 stdout**——元数据损坏不得猜成功）
      ② rc（终态发布点。一旦存在，liveness 完全不参与判定，ADR-2）
      ③ witness identity（rc 在而 terminal witness 缺失/对不上 ⇒ CORRUPT）
      ④ liveness 终态且无 rc ⇒ LOST（不等满 timeout，OVBG-03）
      ⑤ 时间上界：无 started ⇒ **独立**的 startup deadline；有 started ⇒
         可信 started_at + timeout + grace
    """
    now = time.time() if now is None else now
    run_dir_real = os.path.realpath(str(run_dir))
    base = {"site": site, "run_dir": run_dir_real}

    if not os.path.isdir(run_dir_real):
        return _status_payload(STATE_MISSING, REASON_EXEC_ERROR,
                               "run-dir 不存在: %s" % run_dir_real, **base)

    kind, job, detail = load_job_metadata(run_dir_real, site)
    if kind == "corrupt":
        return _status_payload(STATE_CORRUPT, REASON_EXEC_ERROR, detail, **base)
    if kind == "absent":
        if os.path.isfile(reserve_path(run_dir_real, site)):
            return _status_payload(
                STATE_RESERVED, None,
                "存在 reservation 但无 job metadata —— 成本未知，只允许显式 reconcile/人工 cleanup",
                unknown_cost=True, **base)
        return _status_payload(STATE_MISSING, REASON_EXEC_ERROR, detail, **base)

    timeout_seconds = timeout_override if timeout_override is not None \
        else job["timeout_seconds"]
    started_kind, started, started_detail = load_witness(
        run_dir_real, site, ".started.json", job, "started_at")
    terminal_kind, terminal, terminal_detail = load_witness(
        run_dir_real, site, ".terminal.json", job, "terminal_at")
    started_at = started.get("started_at") if started_kind == "ok" else None
    terminal_at = terminal.get("terminal_at") if terminal_kind == "ok" else None
    base.update({
        "run_id": job["run_id"], "job_id": job["job_id"],
        "attempt_nonce": job["attempt_nonce"], "runner": job["runner"],
        "model": job["model"], "effort": job["effort"],
        "dispatched_at": job["dispatched_at"],
        "startup_deadline_at": job["startup_deadline_at"],
        "started_at": started_at, "terminal_at": terminal_at,
        "timeout_seconds": timeout_seconds,
    })
    started_epoch = parse_utc_iso(started_at)
    if started_epoch is not None:
        base["deadline_at"] = datetime.fromtimestamp(
            started_epoch + timeout_seconds + AWAIT_GRACE_SECONDS,
            timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if started_kind == "corrupt":
        return _status_payload(STATE_CORRUPT, REASON_EXEC_ERROR, started_detail, **base)
    if terminal_kind == "corrupt":
        return _status_payload(STATE_CORRUPT, REASON_EXEC_ERROR, terminal_detail, **base)

    rc_present, rc_value, rc_raw = read_rc(run_dir_real, site)
    if rc_present:
        if rc_value is None:
            return _status_payload(STATE_CORRUPT, REASON_EXEC_ERROR,
                                   "rc 内容非纯十进制: %r" % (rc_raw,), **base)
        base["rc"] = rc_value
        if terminal_kind != "ok":
            # worker 的发布顺序是 terminal witness → rc（Task 1 的顺序锚）⇒ 缺 witness
            # 意味着证据链断了，MUST NOT 只凭一个 rc 数字就把 stdout 放进 findings 池。
            return _status_payload(STATE_CORRUPT, REASON_EXEC_ERROR,
                                   "rc 已发布但缺少可核验的 terminal witness", **base)
        base["stdout_sha256"] = terminal.get("stdout_sha256")
        evidence = stdout_stat_evidence(run_dir_real, site)   # stat，不读正文
        base["stdout_bytes"] = evidence["bytes"]
        if rc_value == 0:
            if evidence["bytes"] > 0:
                return _status_payload(STATE_SUCCEEDED, REASON_OK, "rc=0 且 stdout 非空", **base)
            return _status_payload(STATE_CORRUPT, REASON_EXEC_ERROR,
                                   "rc=0 但 stdout 为空 —— 不得猜成功", **base)
        if rc_value == RC_TIMEOUT:
            return _status_payload(STATE_TIMED_OUT, REASON_TIMEOUT,
                                   "内层 timeout 实际写出 rc=124", **base)
        if rc_value == RC_SECRET_HIT:
            return _status_payload(STATE_FAILED, REASON_SECRET_HIT,
                                   "helper 出境 secret scan 命中（rc=3），本次 voice 拒发", **base)
        return _status_payload(STATE_FAILED, REASON_EXEC_ERROR,
                               "helper 非零退出 rc=%d" % rc_value, **base)

    if liveness is None:
        liveness = probe_liveness(job["job_id"], claude_bin=claude_bin)
    base["liveness"] = liveness
    if liveness in LIVENESS_TERMINAL:
        # 极窄竞态：worker 先发布 rc 再退出，但文件可见性可能滞后于 agent state 翻转
        # ⇒ 判 LOST 前再看一眼 rc。**只重入一次**（`_rechecked`）：rc 若在 isfile 与
        # read_rc 之间消失，无界重入会打满栈（且 RecursionError 会被 parse_utc_iso 的
        # `except Exception` 吞掉，静默降级成 CORRUPT）。
        if not _rechecked and os.path.isfile(os.path.join(run_dir_real, site + ".rc")):
            return derive_status(run_dir_real, site, liveness=liveness, now=now,
                                 claude_bin=claude_bin, timeout_override=timeout_override,
                                 _rechecked=True)
        return _status_payload(
            STATE_LOST, REASON_EXEC_ERROR,
            "supervisor job 已终结（state=%s）但 rc 缺席 —— 判 exec-error，"
            "MUST NOT 冒充 timeout" % liveness, **base)

    if started_kind != "ok":
        startup_deadline = parse_utc_iso(job["startup_deadline_at"])
        if startup_deadline is not None and now > startup_deadline:
            return _status_payload(
                STATE_LOST, REASON_EXEC_ERROR,
                "startup deadline（%s）已过仍无 started sidecar" % job["startup_deadline_at"],
                **base)
        return _status_payload(STATE_STARTING, None,
                               "已 dispatch，等待 worker 发布 started sidecar", **base)

    if started_epoch is not None and now > started_epoch + timeout_seconds + AWAIT_GRACE_SECONDS:
        return _status_payload(
            STATE_LOST, REASON_EXEC_ERROR,
            "自可信 started_at 起算已超过 timeout(%d)+grace(%d) 仍无 rc"
            % (timeout_seconds, AWAIT_GRACE_SECONDS), **base)
    return _status_payload(STATE_RUNNING, None, "worker 在飞，未到终态", **base)


# ── collect（幂等）─────────────────────────────────────────────────────────────

def _first_writer_wins_json(path, payload, mode=0o600):
    """原子发布且**首写者胜**：已存在则原样保留（幂等的落盘基石）。

    用「temp 全量写完 → `os.link`」而不是 `os.replace`：link 在目标已存在时失败，
    于是「先到者定终身」，且读者看到的一定是**写完之后**的完整文件。
    """
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
        try:
            os.link(tmp, path)
        except FileExistsError:
            pass
        except OSError:
            # 文件系统不支持 hard link ⇒ 退到「不存在才落」（窗口极窄，方向仍是首写者胜）
            if not os.path.exists(path):
                os.replace(tmp, path)
                tmp = None
    finally:
        if tmp is not None and os.path.exists(tmp):
            os.unlink(tmp)
    return path


def load_collected(run_dir, site, job):
    """读回首次 collect 见证并核验 identity。→ (kind, data, detail)。"""
    path = collected_path(run_dir, site)
    if not os.path.isfile(path):
        return ("absent", None, "")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:
        return ("corrupt", None, "collected witness 不可解析: %s" % exc)
    if not isinstance(data, dict):
        return ("corrupt", None, "collected witness 顶层不是 object")
    for field, expected in (("schema_version", SCHEMA_VERSION), ("site", site),
                            ("run_id", job.get("run_id")),
                            ("attempt_nonce", job.get("attempt_nonce"))):
        if data.get(field) != expected:
            return ("corrupt", data,
                    "collected witness 的 %s 与本次 attempt 不符: %r ≠ %r"
                    % (field, data.get(field), expected))
    return ("ok", data, "")


def build_collect_payload(status):
    """把终态 status 补成 collect 结果：collected_at、自然 duration、stdout digest 核验。"""
    payload = dict(status)
    payload["schema_version"] = SCHEMA_VERSION
    payload["collected_at"] = utc_now_iso()
    started_epoch = parse_utc_iso(status.get("started_at"))
    terminal_epoch = parse_utc_iso(status.get("terminal_at"))
    payload["duration_seconds"] = round(terminal_epoch - started_epoch, 3) \
        if (started_epoch is not None and terminal_epoch is not None) else None
    stderr_evidence = stderr_stat_evidence(status["run_dir"], status["site"])
    payload["stderr_bytes"] = stderr_evidence["bytes"]
    payload["stderr_lines"] = stderr_evidence["lines"]
    payload["stdout_lines"] = None

    if status.get("rc") is None:
        return payload
    # rc 已发布才读 stdout（OVBG-02：collect 只在 rc 发布后读取 stdout）
    evidence = stdout_read_evidence(status["run_dir"], status["site"])
    if not evidence.get("ok"):
        payload.update({"ok": False, "state": STATE_CORRUPT, "terminal": True,
                        "reason_code": REASON_EXEC_ERROR, "detail": evidence["detail"]})
        return payload
    payload["stdout_bytes"] = evidence["bytes"]
    payload["stdout_lines"] = evidence["lines"]
    witness_digest = status.get("stdout_sha256")
    if witness_digest and witness_digest != evidence["sha256"]:
        payload.update({
            "ok": False, "state": STATE_CORRUPT, "terminal": True,
            "reason_code": REASON_EXEC_ERROR,
            "detail": "stdout digest 与 terminal witness 不符（证据被改动）: %s ≠ %s"
                      % (evidence["sha256"], witness_digest)})
        return payload
    payload["stdout_sha256"] = evidence["sha256"]
    if payload["reason_code"] == REASON_OK:
        # 只有可信成功的 stdout 才给出路径 —— 它是唯一进 findings 池的通道。
        payload["stdout_path"] = evidence["path"]
    return payload


# ── 子命令入口 ────────────────────────────────────────────────────────────────

def _validate_site_args(args):
    """三个只读子命令共享的入参校验。→ 错误 payload 或 None。"""
    site = args.site or ""
    if not SITE_RE.match(site):
        return _reject("site 名非法（只允许 [A-Za-z0-9._-]，且不得以 . - 开头）: %r" % site,
                       state="usage-error", reason_code=REASON_EXEC_ERROR,
                       fallback_allowed=False, site=site)
    if not _no_control_chars(args.run_dir or "") or not os.path.isabs(args.run_dir or ""):
        return _reject("run-dir MUST 为不含换行/NUL 的绝对路径: %r" % (args.run_dir,),
                       state="usage-error", reason_code=REASON_EXEC_ERROR,
                       fallback_allowed=False, site=site)
    timeout = getattr(args, "timeout", None)
    if timeout is not None and not (MIN_TIMEOUT_SECONDS <= timeout <= MAX_TIMEOUT_SECONDS):
        # 复用 dispatch 的同一组常量（= 既有 outside-voice.async-timeout-seconds 的取值域），
        # MUST NOT 在这里新造第二份范围口径。
        return _reject("timeout 越界（合法 %d..%d）: %d"
                       % (MIN_TIMEOUT_SECONDS, MAX_TIMEOUT_SECONDS, timeout),
                       state="usage-error", reason_code=REASON_EXEC_ERROR,
                       fallback_allowed=False, site=site)
    return None


def cmd_status(args):
    bad = _validate_site_args(args)
    if bad is not None:
        return 2, bad
    payload = derive_status(args.run_dir, args.site, timeout_override=args.timeout)
    return (0 if payload["ok"] else 1), payload


def cmd_await(args):
    bad = _validate_site_args(args)
    if bad is not None:
        return 2, bad
    poll = min(max(args.poll_interval, MIN_POLL_INTERVAL_SECONDS), MAX_POLL_INTERVAL_SECONDS)
    max_wait = args.max_wait
    if max_wait is not None and not (0 < max_wait <= MAX_AWAIT_WAIT_SECONDS):
        return 2, _reject("max-wait 越界（合法 0<v≤%d）: %r" % (MAX_AWAIT_WAIT_SECONDS, max_wait),
                          state="usage-error", reason_code=REASON_EXEC_ERROR,
                          fallback_allowed=False, site=args.site)
    started = time.monotonic()
    # liveness 探针独立节流：盘面按 poll 间隔读，`claude agents` 最多每
    # LIVENESS_PROBE_INTERVAL_SECONDS 一次（缓存上次结果喂给派生函数）。
    cached_liveness = None
    cached_at = None
    while True:
        if cached_at is None \
                or time.monotonic() - cached_at >= LIVENESS_PROBE_INTERVAL_SECONDS:
            liveness = None                      # None ⇒ 由 derive_status 真探一次
        else:
            liveness = cached_liveness
        payload = derive_status(args.run_dir, args.site, liveness=liveness,
                                timeout_override=args.timeout)
        if liveness is None and payload["liveness"] is not None:
            # payload["liveness"] 非 None ⟺ 本轮真的走到了探针分支（rc 已发布 /
            # 元数据坏 的早退路径不探，也不该刷新缓存时刻）。
            cached_liveness = payload["liveness"]
            cached_at = time.monotonic()
        waited = time.monotonic() - started
        # 终态 / RESERVED（unknown-cost，永远不会自行到达终态，交 reconcile）/ 外层 max-wait
        # 到点 —— 三者之外一律继续等：MUST NOT 因为「等久了」就落 timeout。
        if payload["terminal"] or payload["state"] == STATE_RESERVED:
            break
        if max_wait is not None and waited >= max_wait:
            break
        time.sleep(poll)
    payload["waited_seconds"] = round(time.monotonic() - started, 3)
    return (0 if payload["ok"] else 1), payload


def cmd_collect(args):
    bad = _validate_site_args(args)
    if bad is not None:
        return 2, bad
    run_dir = os.path.realpath(args.run_dir)
    site = args.site
    kind, job, detail = load_job_metadata(run_dir, site)
    if kind == "ok":
        stored_kind, stored, stored_detail = load_collected(run_dir, site, job)
        if stored_kind == "corrupt":
            return 1, _status_payload(STATE_CORRUPT, REASON_EXEC_ERROR, stored_detail,
                                      site=site, run_dir=run_dir)
        if stored_kind == "ok":
            # 幂等：首次收集的结论就是终局，原样回放（含首次 collected_at）。
            return (0 if stored.get("ok") else 1), stored

    status = derive_status(run_dir, site, timeout_override=args.timeout)
    if not status["terminal"]:
        # 未终态 ⇒ 不落 collected witness、不读 stdout、reason_code 恒为 null。
        return 1, status
    payload = build_collect_payload(status)
    # 🔴 只有 **rc 已发布**的终态才冻结成不可变见证。
    # 幂等的边界是 design.md 的 Global Constraint：「terminal **rc** 之后 collect 幂等」。
    # LOST / RESERVED 也是 terminal，但它们由**非 durable 证据**推出（liveness 探针、
    # startup deadline）——worker 可能只是慢，随后仍会发布 rc + 真实 findings。
    # 把它们落成见证 = 把一次**已经计费**的 voice 永久丢弃（二次 collect 只会原样回放
    # LOST）。无 rc 的终态一律**只返回、不落盘**，交 reconcile 处置。
    if kind == "ok" and status.get("rc") is not None:
        _first_writer_wins_json(collected_path(run_dir, site), payload)
        stored_kind, stored, _ = load_collected(run_dir, site, job)
        if stored_kind == "ok":
            payload = stored
    return (0 if payload["ok"] else 1), payload


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

    def add_site_only(p):
        p.add_argument("--run-dir", required=True)
        p.add_argument("--site", required=True)
        # 缺省 None = 「用 job.json 里 dispatch 当时记下的 timeout_seconds」，
        # 即既有 `outside-voice.async-timeout-seconds` 的值 —— 本 helper 不另解析 config。
        p.add_argument("--timeout", type=int, default=None)

    add_site_only(sub.add_parser("status"))

    awaiter = sub.add_parser("await")
    add_site_only(awaiter)
    awaiter.add_argument("--max-wait", type=float, default=None)
    awaiter.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL_SECONDS)

    add_site_only(sub.add_parser("collect"))

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
    if args.command in ("status", "await", "collect"):
        code, payload = {"status": cmd_status, "await": cmd_await,
                         "collect": cmd_collect}[args.command](args)
        emit(payload)
        return code
    parser.print_usage(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
