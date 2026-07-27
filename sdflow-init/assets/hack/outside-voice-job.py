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
    另经 `SDFLOW_VOICE_RUNNER_PID_FILE` 下发 `<site>.runner.pid` 的绝对路径：helper MUST 在
    spawn runner 后**立即**（`$!` 可得的最早时刻，早于 `wait`）把 `OV_RUNNER_PID`
    （GNU timeout 自身 pid = 它 setpgid 出的那个独立进程组的 pgid）以**纯十进制**原子
    写入该文件 —— 它是 cleanup 核验「runner 子树是否已退出」的唯一直接信号
    （worker 自己的进程组圈不住 timeout 的独立组）。
    ⚠ pid 只有在 `&` 之后才存在 ⇒ 「spawn 之前落盘」在 shell 层不可能；`&` 与写入之间
    的窗口里被杀 ⇒ 文件缺席 ⇒ 消费侧 `probe_subtree` 退回判据 ⑤ 的盘面推断（terminal
    witness 在场即判 `exited`），**不是**退回 `unverifiable` —— 而该窄口里 helper 恰是
    被信号打死的 ⇒ ⑤ 会**误判 exited**、孤儿 runner 仍在计费。本 sidecar（判据 ④）就是
    为关这个口子而存在，它自己缺席时关不满：登记为已知窄口，MUST NOT 声称已消除。
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

  cleanup --run-dir <d> --site <s> [--cancel] [--timeout <n>] [--subtree-wait <f>]
    **identity-safe** 的单站点清理。任何破坏性调用（`claude stop` / `claude rm`）之前
    都**重新核验** canonical job id、repo、site 与 attempt identity 四项；任一项出现
    **矛盾** ⇒ 只告警、零破坏性调用（MUST NOT 猜测并操作其他 job）。
      · 终态（rc 已发布）且**已 collect** ⇒ 直接 `rm`；未 collect ⇒ 拒绝（`not-collected`）
      · 在飞站点 ⇒ 拒绝（`still-running`），除非显式 `--cancel`
      · LOST / `--cancel` ⇒ `stop` → **核验 worker 与 runner 子树已退出** → `rm`
        子树不可证 ⇒ `orphan-warning`：**不 rm**、`unknown_cost=true`、
        `fallback_allowed=false`（禁止叠加费用的自动 fallback）
      · roster 已无此 job ⇒ **照样先核验子树**（roster 干净 ≠ 进程死了）：已退出才是
        `absent`（幂等成功、放行 fallback）；未退出/不可证 ⇒ `orphan-warning`
    清理失败**不改写**已取得的 rc、不删除 run-dir 的本轮审计证据、不把已成功的
    findings 改判失败。`--subtree-wait` 是子树核验的有界轮询上限（默认 5 秒）。
    stdout: 单行 JSON {ok,state,stopped,removed,subtree,orphan_warning,unknown_cost,
            fallback_allowed,identity,…}
    state ∈ removed | stopped-removed | absent | not-collected | still-running |
            orphan-warning | identity-unverified | cleanup-failed
    exit 0=已清理/无需清理 | 1=未清理（看 orphan_warning） | 2=usage-error

  reconcile --run-dir <d> [--site <s>] [--subtree-wait <f>]
    **abandoned run 的显式恢复入口**。`--run-dir` 是必填的：整个脚本**没有**
    「找最新 run」的代码路径 —— 评审 session 整体丢失时 MUST NOT 扫描目录猜恢复目标。
    站点只从**本 run-dir 自己的** `<site>.job.json` / `<site>.reserve` 枚举，
    MUST NOT 从 supervisor roster 反向取站点（那会碰到未持有 metadata 的他人 job）。
    每站点：终态 → collect（结果不丢）→ cleanup rm；超 deadline 的活动 → stop/子树核验/rm；
    未到 deadline 的在飞 → 只报 pending 不动它；残留 reserve → `manual-cleanup-required`
    （unknown-cost：MUST NOT 自动重派、MUST NOT 删 reserve）。
    **站点集为空 MUST NOT 报绿**（`all([])` 为真）：`--site` 在本 run-dir 里没有对应站点
    ⇒ usage-error（敲错 site / 点错 run-dir 恰恰是成本未知的场景）；run-dir 内一个站点都
    没有 ⇒ `ok=false` + 显式 detail。
    stdout: 单行 JSON {ok,state,run_dir,sites:[…],orphan_warnings:[…],unknown_cost_sites:[…]}
    exit 0=全部无残留 | 1=有 orphan/unknown-cost/identity 未核验 | 2=usage-error

  install-manifest [--dir <d>]
    **安装步专用**（`setup.sh` 的最后一步调它，不给人手动调）：按同代成员算 sha256 并原子
    发布 `capability-manifest.json`。之所以是子命令而非 shell 里的一段 hash 计算：
    manifest 的口径（成员集 + generation 派生式）MUST 只有**一份**——写与验共用本文件的
    `compute_manifest()`，shell 侧抄第二份必然漂。缺文件 / 目录不可写 ⇒ 非零退出且不写半份。
    stdout: 单行 JSON（即 manifest 内容）                       exit 0=已写 | 1=失败

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

  🔴 `unknown_cost` / `orphan_warning`（调用方的 fallback 闸门，OVBG-03/OVBG-05）：
  `unknown_cost=true` ⇒ **MUST NOT 自动同族 fallback**——外部 job 可能仍在跑（已计费），
  再派一次就是双倍付费。它出现在两类站点上：
    · `RESERVED`（dispatch accepted 但 metadata 未发布，成本未知）
    · **一切 `LOST`**（rc 缺席 ⇒ 盘面上没有 terminal witness ⇒ 子树是否退出**未经核验**）
  解闸的**唯一**途径是 `cleanup` / `reconcile`：它们真去探进程树，核验通过（identity ✅ +
  子树确已退出 + stop/rm 成功）后返回 `fallback_allowed=true`。

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
# 〔OVBG-04〕spec 把后台通道的推理档位**写死 `--effort high`** ⇒ 合法集就是这一个值，
# 不是 CLI 自己支持的那 5 档、也不是原先随手放行的 3 档。dispatch 是整条链上 effort 的
# **唯一 producer**（`build_worker_command` → worker → `SDFLOW_VOICE_EFFORT` →
# `outside-voice.sh` 全程原样透传，没有第二个注入点）⇒ 钉在这里一处即钉住全链。
# 降档一律 fail-loud 拒绝，MUST NOT 静默改写成 high（静默改写 = 调用方以为发了 medium、
# 实际跑了 high，两边都察觉不到）。helper 侧 `${SDFLOW_VOICE_EFFORT:-high}` 的透传能力
# 保留不删 —— 宿主直调 `exec` 的同步路径用得上，那条路径不经本文件。
EFFORT_VALUES = ("high",)
RUNNER_VALUES = ("claude", "codex")
# v1 background transport 只在这两个已过 quoting/injection golden 的 POSIX 平台 ready。
SUPPORTED_SYS_PLATFORMS = ("darwin", "linux")

# 〔宿主标识：dispatch 侧的**盘面锚**，不是自述〕
# efficacy 证据要回答「这一轮 voice 跑在哪个宿主的编排层里」。这个量**有确定性信号**
# （`resolve-models.sh` 判宿主用的就是这两个环境变量），而 **dispatch 恰好就跑在宿主
# 自己的 shell 里** ⇒ 这里读一次落进 job.json，整条链（status → collect → 证据）就有了
# 机械锚，不必再靠调用方 `--host` 自报（那正是 adr/0018 说的「无机械锚的 ✅」）。
# 判据与 `resolve-models.sh` 逐条同口径：**正信号**判定，MUST NOT「缺失即另一方」推断；
# 两个信号同时出现 = 冲突，落 unknown（MUST NOT 静默取其一）。
HOST_CLAUDE = "claude"
HOST_CODEX = "codex"
HOST_UNKNOWN = "unknown"


def detect_host(env=None):
    """→ "claude" | "codex" | "unknown"（与 `resolve-models.sh` 第 1 段同口径）。

    判不出一律 `unknown` —— 它在 efficacy 门里等价于「不是 codex」⇒ fail-closed。
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
    posix_shell = check_posix_shell()
    # 非 POSIX 宿主已由 capability gate 拒绝；继续调用 shutil.which() 会在测试模拟
    # sys.platform == "win32" 的 POSIX Python 上触发 Windows 专属 _winapi 路径。更重要的是，
    # 这条已拒绝的路径不应再探测外部 CLI。
    claude_bin = shutil.which("claude") if posix_shell["ok"] else None
    checks = {
        "posix-shell": posix_shell,
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
            fallback_allowed=False, **extra):
    """失败 payload 的唯一构造口。

    🔴 `fallback_allowed` 默认 **False**（fail-closed）：Global Constraint 是
    「成本未知时禁止再次 dispatch 或立即 fallback」——默认 True 与它反向，
    下一个新增的失败分支忘了传参就会**静默放行**一次可能的重复计费。
    现有调用点全部显式传值，翻默认不改任何现行行为，只改「忘了传」时的落点。
    """
    payload = {"ok": False, "reason_code": reason_code, "state": state,
               "fallback_allowed": fallback_allowed, "detail": message}
    payload.update(extra)
    return payload


def _no_control_chars(value):
    return "\n" not in value and "\r" not in value and "\0" not in value


def _same_path(a, b):
    try:
        return os.path.realpath(str(a)) == os.path.realpath(str(b))
    except OSError:
        return False


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
        return 1, _reject("effort 非法（后台通道按 OVBG-04 钉死 %s，MUST NOT 降档）: %r"
                          % ("|".join(EFFORT_VALUES), args.effort),
                          state="usage-error", fallback_allowed=False, site=site)
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
    comm_error = None
    stdout_text = ""
    stderr_text = ""
    rc = None
    try:
        proc = subprocess.Popen(
            [claude_bin, "--bg", "--exec", command],
            cwd=repo_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", start_new_session=True,
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
    except Exception as exc:
        # [impl-review-fix] communicate() 会抛的不止 TimeoutExpired（管道 OSError、
        # 解码失败……；`errors="replace"` 已消掉解码那一类，但 producer 是 research
        # preview，MUST NOT 假设剩下的都不会来）。让异常逃出本函数的后果是三重的：
        # reservation 不释放（该 site 永久占坑，只能人工 reconcile）、已 Popen 的进程树
        # 不回收（孤儿计费）、调用方拿不到那行带 fallback_allowed 的 JSON —— 「5 秒级
        # 诚实降级」在这条路径上退化成一次哑崩溃。收进下方同一出口，由「本次 attempt
        # 的 nonce 是否命中外部 job」决定 unknown-cost 还是 release+fallback。
        comm_error = str(exc)
        _kill_process_tree(proc)
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

    if timed_out or comm_error is not None or rc != 0:
        if timed_out:
            why = "dispatch 超过 monotonic %.0f 秒 deadline" % DISPATCH_DEADLINE_SECONDS
        elif comm_error is not None:
            why = "读取 claude --bg --exec 输出失败: %s" % comm_error
        else:
            why = "claude --bg --exec 非零退出 rc=%s" % rc
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
        "host": detect_host(),   # 盘面锚：dispatch 就跑在宿主 shell 里，见 detect_host 注释
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
        # effort 与 runner/model 同路下发。消费者**只有一个**：`outside-voice.sh` 的
        # **claude 分支**（1.5.0 起）`--effort "${SDFLOW_VOICE_EFFORT:-high}"`。
        # ∴ 断言要带主语——`runner=claude` 时 job.json 里记的 effort 才是真实下发并生效的值；
        # `runner=codex` 时 codex 分支**从不读这个变量**（档位不经本通道），它在 job.json 里
        # 仍是装饰值，MUST NOT 拿它当「codex 实际生效档位」的证据。
        env["SDFLOW_VOICE_EFFORT"] = args.effort
    # 🔴 runner pid sidecar 的落盘路径 —— cleanup 核验「runner 子树是否已退出」的**唯一直接
    # 信号**：worker 自己的进程组圈不住 GNU timeout 自建的那个独立组（见 probe_subtree 的
    # 判定地基）。缺这个信号时判定退回 `probe_subtree` 的判据 ⑤ 盘面推断 —— 无 terminal
    # witness 才判 unverifiable，有 terminal witness 则判 exited（helper 被 SIGKILL 那格是
    # **误判**，孤儿 runner 仍在计费）。∴ 接上本路径不是"锦上添花"，是把那格误判关掉。
    # 消费者 = `outside-voice.sh` 的 `ov_publish_runner_pid`（1.5.0 起）：spawn runner 后立即
    # 把 `OV_RUNNER_PID` 以纯十进制原子写入本路径（临时文件 + mv，0600）。
    env["SDFLOW_VOICE_RUNNER_PID_FILE"] = runner_pid_path(run_dir, site)
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
    "host", "runner", "model", "effort", "job_id", "dispatched_at",
    "startup_deadline_at", "timeout_seconds",
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


def probe_liveness(job_id, claude_bin=None, expect_cwd=None):
    """一次 `claude agents --all --json`，按 **id** 通道定位本 job 的 state。

    🔴 MUST 走 id 而非 name：真机实测 `state="done"` 的 background 条目**没有 `name` 字段**
    （Task 1 已独立核实）——只认 name 的探针会把每一个已完成的 job 报成 missing。
    任何取不到答案的情形一律返回 `unavailable`（探不到 ≠ 丢了，见 LIVENESS_TERMINAL 注释）。

    `expect_cwd`（= job metadata 的 repo_root）是 **repo 维度的重新核验**（OVBG-02）：
    id 命中但 cwd 指向另一个仓 ⇒ 那不是我们的 job。此时**降级为 `unavailable` 而非
    `missing`**：`missing` 属 LIVENESS_TERMINAL，会把一个还在飞的合法 worker 当场判 LOST；
    而 cwd 对不上只说明「这条探针没有判别力」，MUST NOT 拿它触发降级。
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
            if expect_cwd and item.get("cwd") and not _same_path(item["cwd"], expect_cwd):
                return LIVENESS_UNAVAILABLE
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
        # 子树退出未经核验时的可读告警（null = 无告警）。与 unknown_cost 同生同灭：
        # 调用方 gate 的是 unknown_cost，人读的是这一条。
        "orphan_warning": None,
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


ORPHAN_WARNING_TEMPLATE = (
    "%s —— worker 与 inner child 的子树是否退出**未经核验**，成本未知：MUST NOT 自动同族 "
    "fallback（会在一次已计费的 voice 上再叠一次）。先跑 "
    "`outside-voice-job.py cleanup --run-dir %s --site %s --cancel` "
    "（identity 核验 → stop → 子树终止核验 → rm）；核验通过后才可 fallback。")

# [impl-review-fix] 上面那条把人指向 `cleanup --cancel`，**只在 cleanup 真能受理时才成立**。
# 有两类状态它结构上受理不了：① 有 reservation 但无 job metadata（没有 identity 可核）；
# ② identity 核验出矛盾。这两类若仍发上面那条，人照做会拿回一模一样的拒绝——**指引在说谎**，
# 而且 ② 更荒唐：那句话本身就是 `cleanup --cancel` 打印出来的。
# 拒绝是对的（删 reserve = 把「可能已花一次」变成「确定花两次」），说谎的是指引 ⇒ 这条模板
# 给**真正可执行**的人工步骤，不给一个必然拒绝他的命令。
MANUAL_ONLY_WARNING_TEMPLATE = (
    "%s —— 子树是否退出**未经核验**，成本未知：MUST NOT 自动同族 fallback。"
    "⚠️ 本状态下 `cleanup --cancel` **受理不了**（无 identity 可核 / identity 有矛盾），"
    "跑它只会拿回同一条拒绝。人工步骤：① 看 %s 下的 `<site>.reserve`、`<site>.job.json`、"
    "`<site>.started.json`、`<site>.runner.pid` 取 attempt nonce 与 pid；"
    "② `claude agents --all --json` 里按该 nonce 找对应 job，确认无误后手动 "
    "`claude stop <id>` / `claude rm <id>`；③ 确认子树确已退出后，再手工删除 "
    "`%s/<site>.reserve` 解闸下一次 dispatch（site=%s）。")


def _lost(detail, run_dir, site, base):
    """LOST 的**唯一**构造口 —— 三条产生路径共用，别再各写各的。

    OVBG-03：「无法证明子树已退出时 SHALL 标记 unknown-cost/orphan-warning 并抑制自动
    fallback」。LOST 的定义就是 rc 缺席 ⇒ 盘面上没有 terminal witness ⇒ **纯派生阶段
    根本没有任何证据能证明子树已退出**。因此这里一律 fail-closed 翻 `unknown_cost`；
    解闸只能靠 cleanup/reconcile 真去探进程树（`probe_subtree`）。
    """
    payload = dict(base)
    payload["unknown_cost"] = True
    payload["orphan_warning"] = ORPHAN_WARNING_TEMPLATE % (detail, run_dir, site)
    return _status_payload(STATE_LOST, REASON_EXEC_ERROR, detail, **payload)


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
            reserved_detail = ("存在 reservation 但无 job metadata —— 成本未知，"
                               "只允许显式 reconcile/人工 cleanup")
            return _status_payload(
                STATE_RESERVED, None, reserved_detail, unknown_cost=True,
                orphan_warning=MANUAL_ONLY_WARNING_TEMPLATE % (
                    reserved_detail, run_dir_real, run_dir_real, site),
                **base)
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
        "attempt_nonce": job["attempt_nonce"], "host": job["host"],
        "runner": job["runner"],
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
        liveness = probe_liveness(job["job_id"], claude_bin=claude_bin,
                                  expect_cwd=job.get("repo_root"))
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
        return _lost(
            "supervisor job 已终结（state=%s）但 rc 缺席 —— 判 exec-error，"
            "MUST NOT 冒充 timeout" % liveness, run_dir_real, site, base)

    if started_kind != "ok":
        startup_deadline = parse_utc_iso(job["startup_deadline_at"])
        if startup_deadline is not None and now > startup_deadline:
            return _lost(
                "startup deadline（%s）已过仍无 started sidecar" % job["startup_deadline_at"],
                run_dir_real, site, base)
        return _status_payload(STATE_STARTING, None,
                               "已 dispatch，等待 worker 发布 started sidecar", **base)

    if started_epoch is not None and now > started_epoch + timeout_seconds + AWAIT_GRACE_SECONDS:
        return _lost(
            "自可信 started_at 起算已超过 timeout(%d)+grace(%d) 仍无 rc"
            % (timeout_seconds, AWAIT_GRACE_SECONDS), run_dir_real, site, base)
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


# ── 进程子树核验（cleanup / reconcile 专用；只读探针，无破坏性动作）───────────

SUBTREE_EXITED = "exited"
SUBTREE_ALIVE = "alive"
SUBTREE_UNVERIFIABLE = "unverifiable"

# 子树核验的有界轮询上限（秒）。stop 之后进程死透需要一点时间，但这不是无界等待。
SUBTREE_VERIFY_SECONDS = 5.0
SUBTREE_VERIFY_INTERVAL_SECONDS = 0.2


def _pid_alive(pid):
    """→ True 存活 / False **确定**不存在 / None 不可判定。

    三值而非布尔是关键：`PermissionError`（pid 已被别的用户复用）与「确定不存在」
    在语义上完全相反，压成布尔就会把「不知道」当成「已退出」，正是 OVBG-05 要杀的形态。
    """
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return None
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except (PermissionError, OSError):
        return None


def _pgid_alive(pgid):
    """整个进程组是否还有存活成员。三值语义同 `_pid_alive`。"""
    if isinstance(pgid, bool) or not isinstance(pgid, int) or pgid <= 0:
        return None
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except (PermissionError, OSError):
        return None


RUNNER_PID_SUFFIX = ".runner.pid"


def runner_pid_path(run_dir, site):
    return os.path.join(str(run_dir), site + RUNNER_PID_SUFFIX)


def read_runner_pid(run_dir, site):
    """读 `<site>.runner.pid` → (kind, pid, detail)，kind ∈ {"ok","corrupt","absent"}。

    盘面格式与 `<site>.rc` 同构：**纯十进制单值**，由 `outside-voice.sh` 在 spawn runner
    后**立即**（早于 `wait`）原子写入，内容 = `OV_RUNNER_PID`（GNU timeout 自身 pid，
    亦即它 setpgid 出的那个独立进程组的 pgid）。文件缺席 = 该窗口内 helper 被杀、或本次
    调用根本没接线（宿主直调 exec 不设 env）⇒ `"absent"` 本身**不构成任何一侧的证据**：
    调用方 `probe_subtree` 由此退回判据 ⑤ 的盘面推断（见那里登记的误判 exited 窄口），
    MUST NOT 把 `"absent"` 读成「runner 已退出」。

    为什么是裸 pid 文件而不是 JSON witness：这个文件由 shell 写，契约越小越不容易写错，
    而写错的代价是 cleanup 永久 fail-closed。identity 绑定来自**路径本身**——run-dir × site
    每次 attempt 唯一（同 site 重复 dispatch 是硬失败）；且两个误判方向都安全：串到别人的
    活 pid ⇒ 判 alive（fail-closed），pid 被复用 ⇒ 同样判 alive。
    """
    path = runner_pid_path(run_dir, site)
    if not os.path.isfile(path):
        return ("absent", None, "")
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
    except OSError as exc:
        return ("corrupt", None, "%s%s 不可读: %s" % (site, RUNNER_PID_SUFFIX, exc))
    text = raw.strip()
    if not re.match(r"\A\d+\Z", text) or int(text) <= 0:
        return ("corrupt", None,
                "%s%s 不是纯十进制正整数: %r" % (site, RUNNER_PID_SUFFIX, text[:64]))
    return ("ok", int(text), "")


def probe_runner_pid(pid):
    """runner 本体与它自建的那个进程组，任一还有活口即 alive。→ 三值 verdict。

    两个探针都问：`OV_RUNNER_PID == 其 pgid` 只在 **GNU timeout 在场**时成立；timeout 缺席
    （helper 直接跑 runner）时该 pid 不是组长，`killpg` 打的是别的组 —— 那只可能**多**判
    一次 alive（fail-closed 方向），MUST NOT 反过来用它判 exited。
    """
    pid_state = _pid_alive(pid)
    group_state = _pgid_alive(pid)
    if pid_state is True or group_state is True:
        return SUBTREE_ALIVE
    if pid_state is False and group_state is False:
        return SUBTREE_EXITED
    return SUBTREE_UNVERIFIABLE


def probe_subtree(run_dir, site, job):
    """核验 **worker 与 runner** 的进程子树是否确已退出。→ (verdict, detail)

    verdict ∈ exited | alive | unverifiable。**「不可证」不等于「已退出」**——
    OVBG-05 要求「子树终止不可证时落 orphan warning 并抑制自动 fallback」。

    🔴 判定的地基：**worker 自己的进程组圈不住真正烧额度的那棵子树。**
    `outside-voice.sh` 用 GNU timeout 跑 runner，而 timeout 会 `setpgid` 把自己放进
    **独立进程组**（该组 PGID 恒等于 timeout 自身 PID —— 见 outside-voice.sh 的组级 KILL
    守卫注释，本机 gtimeout 实测同）。∴ worker 组空了**推不出** runner 已死：worker 被
    SIGKILL 时 bash trap 不执行，孤儿 timeout/claude 整棵留在另一个组里继续计费，而
    `killpg(worker_pgid, 0)` 照样报 `ProcessLookupError`。
    **组探针只用来判 alive，永不用来判 exited。**

    判定顺序（每一步都要有确定性信号，无信号即降级为 unverifiable）：
      ① started witness 里的 worker identity —— 没有它就没有可核验的对象。
      ② worker pid 本体：存活 ⇒ alive；不可判定 ⇒ unverifiable。
      ③ worker 是组长且组内仍有活口 ⇒ alive（未换组的后代还在跑）。
      ④ `<site>.runner.pid`（helper 在 spawn runner **后**立即落盘，早于 `wait`；pid 在
         `&` 之前不存在，"spawn 前落盘"在 shell 层不可能）—— **唯一能直接回答「runner
         子树是否退出」的信号**：alive ⇒ alive；确定不存在 ⇒ exited；不可判定 / 文件损坏
         ⇒ unverifiable（信号在场就以它为准，MUST NOT 再退回 ⑤ 的推断）。
      ⑤ 该信号缺席 ⇒ 退到盘面推断：terminal witness 存在 ⟺ worker 自己走到了发布点，而
         `subprocess.call` 是**同步**的 ⇒ 走到那里意味着 helper 已退出、其 `wait` 已回收
         runner ⇒ exited。**残余**：helper 若是被 SIGKILL 打死的（trap 不执行），
         `subprocess.call` 同样返回、witness 同样发布，而孤儿 runner 仍活着 —— 这个窄口
         只能由 ④ 的直接信号关掉。
      ⑥ 两个信号都没有 ⇒ unverifiable。
    """
    started_kind, started, detail = load_witness(
        run_dir, site, ".started.json", job, "started_at")
    if started_kind != "ok":
        return (SUBTREE_UNVERIFIABLE,
                "无可核验的 started witness（%s）—— 子树是否退出不可证"
                % (detail or "sidecar 缺失"))
    worker = started.get("worker")
    if not isinstance(worker, dict):
        return (SUBTREE_UNVERIFIABLE,
                "started witness 未记录 worker process identity —— 子树是否退出不可证")
    pid = worker.get("pid")
    pgid = worker.get("pgid")

    alive = _pid_alive(pid)
    if alive is True:
        return (SUBTREE_ALIVE, "worker pid=%s 仍存活" % (pid,))
    if alive is None:
        return (SUBTREE_UNVERIFIABLE, "worker pid=%r 的存活性不可判定" % (pid,))

    if pgid == pid and _pgid_alive(pgid) is True:
        return (SUBTREE_ALIVE,
                "worker pid=%s 已退出，但其进程组 pgid=%s 内仍有存活进程"
                "（未换组的后代未随之退出）" % (pid, pgid))

    runner_kind, runner_pid, runner_detail = read_runner_pid(run_dir, site)
    if runner_kind == "corrupt":
        return (SUBTREE_UNVERIFIABLE,
                "runner pid sidecar 损坏（%s）—— runner 子树是否退出不可证" % runner_detail)
    if runner_kind == "ok":
        verdict = probe_runner_pid(runner_pid)
        if verdict == SUBTREE_ALIVE:
            return (SUBTREE_ALIVE,
                    "worker pid=%s 已退出，但 runner pid=%s（及其进程组）仍存活"
                    "—— 孤儿 runner 仍在计费" % (pid, runner_pid))
        if verdict == SUBTREE_EXITED:
            return (SUBTREE_EXITED,
                    "worker pid=%s 与 runner pid=%s（及其进程组）均已不存在"
                    % (pid, runner_pid))
        return (SUBTREE_UNVERIFIABLE,
                "runner pid=%s 的存活性不可判定 —— 子树是否退出不可证" % (runner_pid,))

    terminal_kind, _, _ = load_witness(run_dir, site, ".terminal.json", job, "terminal_at")
    if terminal_kind == "ok":
        return (SUBTREE_EXITED,
                "worker pid=%s 已发布 terminal witness 后退出 ⇒ helper 已同步返回、其 wait "
                "已回收 runner" % (pid,))
    return (SUBTREE_UNVERIFIABLE,
            "worker pid=%s 已不在，但既无 %s%s（runner 的直接信号）也无 terminal witness"
            "（worker 组 pgid=%r 为空**不**构成 runner 已退出的证据）⇒ 子树是否退出不可证"
            % (pid, site, RUNNER_PID_SUFFIX, pgid))


def wait_subtree_exited(run_dir, site, job, max_wait=SUBTREE_VERIFY_SECONDS):
    """有界轮询到「已退出」。alive 会等（进程正在死），unverifiable 立即返回（等不来信号）。"""
    deadline = time.monotonic() + max(0.0, max_wait)
    while True:
        verdict, detail = probe_subtree(run_dir, site, job)
        if verdict != SUBTREE_ALIVE or time.monotonic() >= deadline:
            return (verdict, detail)
        time.sleep(SUBTREE_VERIFY_INTERVAL_SECONDS)


# ── identity 重新核验（**每一次破坏性调用之前**）──────────────────────────────

IDENTITY_OK = "ok"
IDENTITY_FAIL = "fail"
IDENTITY_UNAVAILABLE = "unavailable"
IDENTITY_ABSENT = "absent"

# roster 条目的 `name` 承载完整 worker 命令串（Task 1 真机实测）。从中反查 site 与
# attempt nonce 是**交叉**核验：盘面自证之外的第二个独立信号源。
NAME_SITE_RE = re.compile(r"--site\s+(\S+)")
NAME_NONCE_RE = re.compile(r"\b[0-9a-f]{32}\b")


def load_roster(claude_bin=None):
    """→ (entries | None, detail)。None = roster 不可得（**探不到 ≠ 不存在**）。"""
    claude_bin = claude_bin or shutil.which("claude")
    if not claude_bin:
        return (None, "PATH 上找不到 claude")
    try:
        proc = _run_cli([claude_bin, "agents", "--all", "--json"],
                        timeout=CLI_PROBE_TIMEOUT_SECONDS)
    except Exception as exc:
        return (None, "agents --all --json 调用失败: %s" % exc)
    if proc.returncode != 0:
        return (None, "agents --all --json 非零退出 rc=%d" % proc.returncode)
    try:
        data = json.loads(proc.stdout)
    except Exception as exc:
        return (None, "agents JSON 不可解析: %s" % exc)
    if not isinstance(data, list):
        return (None, "agents JSON 顶层不是 list")
    return (data, "")


def _check(status, detail):
    return {"status": status, "detail": detail}


def verify_identity(run_dir, site, job, roster):
    """破坏性操作前重新核验 canonical id / repo / site / attempt identity 四项。

    → {"ok":bool, "entry":dict|None, "checks":{…}, "detail":str}

    🔴 判据是「**有没有矛盾**」，不是「有没有全部拿到肯定答案」：
    真机上 `state="done"` 的条目**没有 `name` 字段**（Task 1 实测），若要求四项都
    positively verified，正常完成的 job 就永远 rm 不掉——那会把「不猜目标」写成
    「什么也别做」。故 `unavailable`（信号缺席）不阻塞，`fail`（信号相互矛盾）一票否决。
    """
    checks = {}
    job_id = str(job.get("job_id") or "")
    entry = None

    if not job_id:
        checks["canonical-id"] = _check(IDENTITY_FAIL, "job metadata 无 canonical job id")
    elif roster is None:
        checks["canonical-id"] = _check(IDENTITY_UNAVAILABLE,
                                        "supervisor roster 不可得，无法重新核验 job id")
    else:
        hits = [item for item in roster
                if isinstance(item, dict) and str(item.get("id") or "") == job_id]
        if len(hits) > 1:
            checks["canonical-id"] = _check(
                IDENTITY_FAIL, "canonical job id=%s 在 roster 里命中 %d 个条目（不唯一）"
                               % (job_id, len(hits)))
        elif not hits:
            checks["canonical-id"] = _check(IDENTITY_ABSENT,
                                            "supervisor roster 已无 job id=%s" % job_id)
        else:
            entry = hits[0]
            checks["canonical-id"] = _check(IDENTITY_OK, "job id=%s 唯一命中" % job_id)

    entry_cwd = (entry or {}).get("cwd")
    if entry is None:
        checks["repo"] = _check(IDENTITY_UNAVAILABLE, "无 roster 条目可比对 repo")
    elif not entry_cwd:
        checks["repo"] = _check(IDENTITY_UNAVAILABLE, "roster 条目无 cwd 字段")
    elif not _same_path(entry_cwd, job.get("repo_root")):
        checks["repo"] = _check(IDENTITY_FAIL,
                                "roster 条目的 cwd 与本 job 的 repo_root 不符: %r ≠ %r"
                                % (entry_cwd, job.get("repo_root")))
    else:
        checks["repo"] = _check(IDENTITY_OK, "cwd == repo_root")

    name = str((entry or {}).get("name") or "")
    sites_in_name = NAME_SITE_RE.findall(name)
    if job.get("site") != site:
        checks["site"] = _check(IDENTITY_FAIL, "job metadata 的 site 与请求不符")
    elif not sites_in_name:
        checks["site"] = _check(IDENTITY_UNAVAILABLE,
                                "roster 条目无可用于交叉核验 site 的命令串")
    elif site not in sites_in_name:
        checks["site"] = _check(IDENTITY_FAIL,
                                "roster 命令串里的 site=%r 与本次请求 %r 不符"
                                % (sites_in_name, site))
    else:
        checks["site"] = _check(IDENTITY_OK, "命令串里的 --site 与本次请求一致")

    nonce = str(job.get("attempt_nonce") or "")
    attempt_detail = []
    attempt_status = IDENTITY_OK
    for suffix, field in ((".started.json", "started_at"), (".terminal.json", "terminal_at")):
        kind, _, why = load_witness(run_dir, site, suffix, job, field)
        if kind == "corrupt":
            attempt_status = IDENTITY_FAIL
            attempt_detail.append(why)
    stored_kind, _, stored_why = load_collected(run_dir, site, job)
    if stored_kind == "corrupt":
        attempt_status = IDENTITY_FAIL
        attempt_detail.append(stored_why)
    nonces_in_name = NAME_NONCE_RE.findall(name)
    if attempt_status != IDENTITY_FAIL:
        if nonces_in_name and nonce not in nonces_in_name:
            attempt_status = IDENTITY_FAIL
            attempt_detail.append("roster 命令串携带的 attempt nonce 与本 job 不符")
        elif not nonces_in_name:
            attempt_status = IDENTITY_UNAVAILABLE
            attempt_detail.append("roster 条目无可用于交叉核验 attempt nonce 的命令串")
        else:
            attempt_detail.append("盘面 witness 与 roster 命令串的 attempt nonce 一致")
    checks["attempt"] = _check(attempt_status, "; ".join(attempt_detail))

    failed = sorted(name_ for name_, item in checks.items() if item["status"] == IDENTITY_FAIL)
    ok = not failed and checks["canonical-id"]["status"] == IDENTITY_OK
    if failed:
        detail = "identity 核验矛盾: " + "; ".join(
            "%s(%s)" % (n, checks[n]["detail"]) for n in failed)
    elif checks["canonical-id"]["status"] == IDENTITY_ABSENT:
        detail = checks["canonical-id"]["detail"]
    elif checks["canonical-id"]["status"] == IDENTITY_UNAVAILABLE:
        detail = checks["canonical-id"]["detail"]
    else:
        detail = "canonical id / repo / site / attempt 四项无矛盾"
    return {"ok": ok, "entry": entry, "checks": checks, "detail": detail}


# ── cleanup ───────────────────────────────────────────────────────────────────

def claude_job_action(claude_bin, action, job_id):
    """`claude stop|rm <id>` —— **只**接受一个已核验过的 canonical id。→ (rc|None, detail)。"""
    if not claude_bin:
        return (None, "PATH 上找不到 claude，无法执行 %s" % action)
    try:
        proc = _run_cli([claude_bin, action, job_id], timeout=CLI_PROBE_TIMEOUT_SECONDS)
    except Exception as exc:
        return (None, "claude %s 调用失败: %s" % (action, exc))
    if proc.returncode != 0:
        return (proc.returncode,
                "claude %s 非零退出 rc=%d: %s"
                % (action, proc.returncode, (proc.stderr or "").strip()[:200]))
    return (0, "")


def _cleanup_payload(state, ok, detail, **extra):
    payload = {
        "ok": ok, "state": state, "detail": detail,
        "site": None, "run_dir": None, "job_id": None,
        "stopped": False, "removed": False,
        "subtree": None, "orphan_warning": None,
        "unknown_cost": False, "fallback_allowed": False,
        "identity": None,
    }
    payload.update(extra)
    return payload


def run_cleanup(run_dir, site, cancel=False, timeout_override=None, claude_bin=None,
                subtree_wait=SUBTREE_VERIFY_SECONDS):
    """identity-safe 的单站点清理。**不写、不删 run-dir 里的任何文件。**

    这个函数唯一的破坏性动作是对 `claude stop|rm` 传一个**已重新核验过**的 canonical id；
    run-dir 是本轮的审计证据，清理成功与否都原样保留（OVBG-05）。
    """
    run_dir = os.path.realpath(str(run_dir))
    claude_bin = claude_bin or shutil.which("claude")
    base = {"site": site, "run_dir": run_dir}

    kind, job, detail = load_job_metadata(run_dir, site)
    if kind != "ok":
        # 没有 job metadata = 没有 identity 可核 ⇒ 只告警。残留 reserve 更是成本未知：
        # 删掉它就等于放行下一次 dispatch，把「可能已花掉一次」变成「确定花两次」。
        reserved = os.path.isfile(reserve_path(run_dir, site))
        why = ("存在 reservation 但无 job metadata（dispatch accepted 与 metadata 发布之间"
               "可能已崩溃）" if reserved else detail)
        # [impl-review-fix] 这里 MUST NOT 用 ORPHAN_WARNING_TEMPLATE —— 它的正文是
        # 「请跑 cleanup --cancel」，而**本分支就是 cleanup 的拒绝分支**：照它做的人会
        # 原地打转，拿到同一句话。拒绝本身是对的（见上方注释），说谎的是指引。
        # 故这条路径给**真正可执行**的人工步骤，不给一个必然拒绝他的命令。
        return _cleanup_payload(
            "identity-unverified", False,
            "无法核验 job identity（%s）—— 只告警，MUST NOT 猜测并操作其他 job" % why,
            unknown_cost=True,
            orphan_warning=MANUAL_ONLY_WARNING_TEMPLATE % (why, run_dir, run_dir, site),
            **base)

    base["job_id"] = job["job_id"]
    status = derive_status(run_dir, site, timeout_override=timeout_override,
                           claude_bin=claude_bin)
    roster, roster_detail = load_roster(claude_bin)
    ident = verify_identity(run_dir, site, job, roster)
    base["identity"] = ident
    id_status = ident["checks"]["canonical-id"]["status"]

    if not ident["ok"]:
        if id_status == IDENTITY_ABSENT:
            # 🔴 roster 干净**不等于**进程死了：`missing` liveness（roster 无此条目）正是
            # LOST 的主要产生路径（`derive_status`），此处若无条件返回成功，一个仍在计费的
            # worker 就会被报成干净通过、并放行自动 fallback 再叠一次 —— OVBG-05/OVBG-03
            # 要杀的正是这个形态。roster 无条目 ⇒ 无 job 可 stop/rm，但子树仍 MUST 核验。
            verdict, verdict_detail = probe_subtree(run_dir, site, job)
            base["subtree"] = verdict
            if verdict == SUBTREE_EXITED:
                return _cleanup_payload(
                    "absent", True,
                    "supervisor roster 已无此 job 且子树已确认退出，无需清理（%s）"
                    % verdict_detail,
                    fallback_allowed=True, **base)
            return _cleanup_payload(
                "orphan-warning", False,
                "supervisor roster 已无此 job，但子树终止不可证（%s）—— MUST NOT 声称已清理"
                % verdict_detail,
                unknown_cost=True,
                orphan_warning="supervisor roster 已无 job id=%s，但 worker/runner 子树"
                               "仍未证退出（%s）；需人工核查并终止，其间 MUST NOT 自动 "
                               "fallback（会在一次可能仍在计费的 voice 上再叠一次）"
                               % (job["job_id"], verdict_detail), **base)
        return _cleanup_payload(
            "identity-unverified", False,
            "identity 核验未通过（%s）—— 只告警，MUST NOT stop/rm 任何 job" % ident["detail"],
            unknown_cost=True,
            orphan_warning=MANUAL_ONLY_WARNING_TEMPLATE % (
                ident["detail"], run_dir, run_dir, site), **base)

    collected_ok = load_collected(run_dir, site, job)[0] == "ok"
    rc_published = status.get("rc") is not None

    if rc_published:
        # OVBG-05：terminal 结果**已 collect 后**才清理 supervisor roster。
        if not collected_ok:
            return _cleanup_payload(
                "not-collected", False,
                "terminal 结果（state=%s）尚未 collect —— MUST 先 collect 再清理 roster"
                % status["state"], **base)
        # 🔴 这里的 `subtree` 是**留痕，不是闸门**：rc 已发布 ⇒ 这次 voice 的额度已经花完，
        # 而 fallback 的意义是「重试一次没拿到结果的 voice」——已 collect 的终态不存在
        # 「再叠一次费用」的问题。故本分支照常 rm 并放行 fallback，探针值只写进 payload
        # 供人工审计（真在这里发现 alive，说明 helper 是被 SIGKILL 打死的，见 probe_subtree ⑤）。
        subtree, subtree_detail = probe_subtree(run_dir, site, job)
        base["subtree"] = subtree
        rc, why = claude_job_action(claude_bin, "rm", job["job_id"])
        if rc != 0:
            return _cleanup_payload(
                "cleanup-failed", False, "rm 失败: %s" % why,
                orphan_warning="supervisor roster 可能仍残留 job id=%s（%s）—— "
                               "MUST NOT 静默声称已清理，请人工处理；已取得的 rc 与本轮"
                               "审计证据未被改动" % (job["job_id"], why), **base)
        # [impl-review-fix] rm 之后 roster 里就没有这个 job 了 —— 那是**追踪它的最后一个
        # 句柄**。若此刻子树并未核验为已退出，本次清理留下的是一个既没人管、也没人看得见
        # 的进程。上面的计费论证（rc 已发布 ⇒ 额度已花完 ⇒ fallback 不重复计费）依然成立，
        # 故闸门不变、fallback 照放；但「已从 roster 移除」MUST NOT 被读成「已经清理干净」。
        if subtree != SUBTREE_EXITED:
            return _cleanup_payload(
                "removed", True,
                "已 collect 的终态 job 已从 supervisor roster 移除",
                removed=True, fallback_allowed=True,
                orphan_warning="job id=%s 已从 roster 移除，但其子树**未核验为已退出**"
                               "（subtree=%s：%s）—— roster 句柄已随 rm 消失，若确有残留"
                               "进程需人工按 %s 下的 <site>.runner.pid / <site>.started.json "
                               "自行核查。本轮 rc 与审计证据未被改动。"
                               % (job["job_id"], subtree, subtree_detail, run_dir), **base)
        return _cleanup_payload("removed", True,
                                "已 collect 的终态 job 已从 supervisor roster 移除",
                                removed=True, fallback_allowed=True, **base)

    # 闸门按 PENDING_STATES 划，不是按 `!= LOST` 划：LOST 之外还有**终态但无 rc** 的形态
    # （witness 损坏的 CORRUPT）。用 `!= LOST` 会把它报成「站点仍在飞」——一句假话，
    # 且它永远等不到 rc，等于把一个该清理的 job 永久挂起。
    if status["state"] in PENDING_STATES and not cancel:
        return _cleanup_payload(
            "still-running", False,
            "站点仍在飞（state=%s）—— 需显式 --cancel 才做破坏性清理" % status["state"], **base)

    # 取消 / 失联路径：stop → 核验子树已退出 → rm（顺序是 OVBG-05 的契约）
    rc, why = claude_job_action(claude_bin, "stop", job["job_id"])
    if rc != 0:
        return _cleanup_payload(
            "cleanup-failed", False, "stop 失败: %s" % why, unknown_cost=True,
            orphan_warning="stop 失败，job id=%s 可能仍在运行（%s）—— MUST NOT 静默声称"
                           "已清理，MUST NOT 自动 fallback 叠加费用" % (job["job_id"], why),
            **base)
    base["stopped"] = True

    verdict, verdict_detail = wait_subtree_exited(run_dir, site, job, max_wait=subtree_wait)
    base["subtree"] = verdict
    if verdict != SUBTREE_EXITED:
        return _cleanup_payload(
            "orphan-warning", False,
            "stop 已发出，但子树终止不可证（%s）—— MUST NOT rm 后声称完成" % verdict_detail,
            unknown_cost=True,
            orphan_warning="stop 之后仍无法证明 worker/inner child 子树已退出（%s）；"
                           "job id=%s 需人工核查并终止，其间 MUST NOT 自动 fallback"
                           % (verdict_detail, job["job_id"]), **base)

    # stop 与核验之间 worker 可能刚好发布了 rc ⇒ 结果不能丢，先 collect 再来清。
    after = derive_status(run_dir, site, timeout_override=timeout_override,
                          claude_bin=claude_bin)
    if after.get("rc") is not None and load_collected(run_dir, site, job)[0] != "ok":
        return _cleanup_payload(
            "not-collected", False,
            "stop 之后检出已发布的 rc（state=%s）—— MUST 先 collect 再清理 roster"
            % after["state"], **base)

    roster2, _ = load_roster(claude_bin)
    ident2 = verify_identity(run_dir, site, job, roster2)
    base["identity"] = ident2
    if not ident2["ok"] and ident2["checks"]["canonical-id"]["status"] != IDENTITY_ABSENT:
        return _cleanup_payload(
            "identity-unverified", False,
            "rm 前重新核验未通过（%s）—— 只告警，MUST NOT rm" % ident2["detail"],
            unknown_cost=True,
            orphan_warning=MANUAL_ONLY_WARNING_TEMPLATE % (
                ident2["detail"], run_dir, run_dir, site), **base)

    rc, why = claude_job_action(claude_bin, "rm", job["job_id"])
    if rc != 0:
        return _cleanup_payload(
            "cleanup-failed", False, "rm 失败: %s" % why,
            orphan_warning="子树已确认退出，但 roster 可能仍残留 job id=%s（%s）"
                           % (job["job_id"], why), **base)
    return _cleanup_payload(
        "stopped-removed", True,
        "identity 已核验、子树已确认退出、supervisor job 已移除（%s）" % verdict_detail,
        removed=True, fallback_allowed=True, **base)


# ── reconcile（abandoned run 的**显式**恢复入口）──────────────────────────────

def discover_sites(run_dir):
    """站点名**只**从本 run-dir 自己的 metadata 枚举。

    🔴 这里没有、也 MUST NOT 有任何「找最新 run」的代码路径：评审 session 整体丢失后，
    唯一合法的恢复目标是操作者显式点名的 run-dir（OVBG-03/OVBG-05）。
    同理 MUST NOT 从 supervisor roster 反向取站点——那会碰到未持有 metadata 的他人 job。
    """
    sites = set()
    try:
        names = os.listdir(str(run_dir))
    except OSError:
        return []
    for name in names:
        for suffix in (".job.json", ".reserve"):
            if name.endswith(suffix):
                candidate = name[: -len(suffix)]
                if SITE_RE.match(candidate):
                    sites.add(candidate)
    return sorted(sites)


def reconcile_site(run_dir, site, claude_bin=None, subtree_wait=SUBTREE_VERIFY_SECONDS):
    """单站点恢复：结果先落袋（collect），再决定清不清理。→ 一条 site 记录。"""
    record = {"site": site, "state": None, "reason_code": None, "job_id": None,
              "ok": False, "action": "none", "collected": False,
              "stopped": False, "removed": False, "unknown_cost": False,
              "orphan_warning": None, "detail": ""}

    kind, job, detail = load_job_metadata(run_dir, site)
    if kind != "ok":
        if os.path.isfile(reserve_path(run_dir, site)):
            status = derive_status(run_dir, site, claude_bin=claude_bin)
            record.update({
                "state": status["state"], "action": "manual-cleanup-required",
                "unknown_cost": True, "orphan_warning": status["orphan_warning"],
                "detail": status["detail"]})
            return record
        record.update({"state": STATE_MISSING, "detail": detail})
        return record

    record["job_id"] = job["job_id"]
    status = derive_status(run_dir, site, claude_bin=claude_bin)

    # ① 结果先落袋：rc 已发布就 collect（幂等）。交接③——先前被判 LOST 的站点若
    #    worker 后来真发布了 rc，这一步就把真结果取回来，不会被旧的 LOST 判定挡住。
    if status.get("rc") is not None:
        _, status = run_collect(run_dir, site)
        record["collected"] = os.path.isfile(collected_path(run_dir, site))

    record.update({"state": status["state"], "reason_code": status.get("reason_code"),
                   "detail": status.get("detail", "")})

    if status["state"] in PENDING_STATES:
        # 未到 deadline 的在飞站点 MUST NOT 被 stop —— 那会杀掉一次已计费的 voice。
        record.update({"ok": True, "action": "pending"})
        return record

    cleanup = run_cleanup(run_dir, site, cancel=False, claude_bin=claude_bin,
                          subtree_wait=subtree_wait)
    record.update({
        "stopped": cleanup["stopped"], "removed": cleanup["removed"],
        "unknown_cost": cleanup["unknown_cost"],
        "orphan_warning": cleanup["orphan_warning"],
        "action": cleanup["state"],
        "detail": "%s | cleanup: %s" % (record["detail"], cleanup["detail"]),
    })
    record["ok"] = cleanup["ok"]
    return record


def _reconcile_payload(run_dir, records, detail, ok=None, state=None):
    warnings = [r["site"] for r in records if r["orphan_warning"]]
    unknown = [r["site"] for r in records if r["unknown_cost"]]
    if ok is None:
        ok = all(r["ok"] for r in records) and not warnings and not unknown
    return {
        "ok": ok,
        "state": state,
        "run_dir": run_dir,
        "sites": records,
        "orphan_warnings": warnings,
        "unknown_cost_sites": unknown,
        "detail": detail,
    }


def run_reconcile(run_dir, only_site=None, claude_bin=None,
                  subtree_wait=SUBTREE_VERIFY_SECONDS):
    """→ reconcile 报告。**站点集为空 MUST NOT 报绿**（见下方两个空集分支）。"""
    run_dir = os.path.realpath(str(run_dir))
    claude_bin = claude_bin or shutil.which("claude")
    sites = discover_sites(run_dir)
    if only_site is not None:
        matched = [s for s in sites if s == only_site]
        if not matched:
            # 🔴 点名的站点不在这个 run-dir 里 ⇒ usage-error，MUST NOT 报「一切正常」：
            # 操作者恢复 abandoned run 时敲错 site / 点错 run-dir 正是**成本未知**的场景，
            # 而 `all([])` 为真会把它渲染成一份干净的绿报告。
            return _reconcile_payload(
                run_dir, [],
                "run-dir 内没有名为 %r 的站点（本 run 自己持有 metadata/reserve 的站点: %s）"
                "—— 请核对 --site 与 --run-dir" % (only_site, sites or "无"),
                ok=False, state="usage-error")
        sites = matched
    records = [reconcile_site(run_dir, site, claude_bin=claude_bin,
                              subtree_wait=subtree_wait)
               for site in sites]
    if not records:
        return _reconcile_payload(
            run_dir, [],
            "run-dir 内没有任何本 run 自己持有 metadata/reserve 的站点 —— 没有可核对的站点"
            "**不等于**没有残留：请确认 --run-dir 点对了", ok=False)
    return _reconcile_payload(
        run_dir, records,
        "reconcile 只处理显式点名的 run-dir 内、本 run 自己持有 metadata 的站点")


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
    return run_collect(args.run_dir, args.site, timeout_override=args.timeout)


def run_collect(run_dir, site, timeout_override=None):
    """collect 的核心（CLI 与 reconcile 共用同一条实现路径，MUST NOT 长出第二份）。"""
    run_dir = os.path.realpath(str(run_dir))
    kind, job, detail = load_job_metadata(run_dir, site)
    if kind == "ok":
        stored_kind, stored, stored_detail = load_collected(run_dir, site, job)
        if stored_kind == "corrupt":
            return 1, _status_payload(STATE_CORRUPT, REASON_EXEC_ERROR, stored_detail,
                                      site=site, run_dir=run_dir)
        if stored_kind == "ok":
            # 幂等：首次收集的结论就是终局，原样回放（含首次 collected_at）。
            return (0 if stored.get("ok") else 1), stored

    status = derive_status(run_dir, site, timeout_override=timeout_override)
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


def cmd_cleanup(args):
    bad = _validate_site_args(args)
    if bad is not None:
        return 2, bad
    if not (0 < args.subtree_wait <= MAX_TIMEOUT_SECONDS):
        return 2, _reject("subtree-wait 越界（合法 0<v≤%d）: %r"
                          % (MAX_TIMEOUT_SECONDS, args.subtree_wait),
                          state="usage-error", reason_code=REASON_EXEC_ERROR,
                          fallback_allowed=False, site=args.site)
    payload = run_cleanup(args.run_dir, args.site, cancel=args.cancel,
                          timeout_override=args.timeout, subtree_wait=args.subtree_wait)
    return (0 if payload["ok"] else 1), payload


def cmd_reconcile(args):
    run_dir = args.run_dir or ""
    if not _no_control_chars(run_dir) or not os.path.isabs(run_dir):
        return 2, _reject("run-dir MUST 为不含换行/NUL 的绝对路径: %r" % (run_dir,),
                          state="usage-error", reason_code=REASON_EXEC_ERROR,
                          fallback_allowed=False)
    if not os.path.isdir(run_dir):
        # 🔴 显式点名的 run-dir 不存在就是 usage-error —— MUST NOT 退而求其次去找别的 run。
        return 2, _reject("run-dir 不存在: %s" % run_dir, state="usage-error",
                          reason_code=REASON_EXEC_ERROR, fallback_allowed=False)
    if args.site is not None and not SITE_RE.match(args.site):
        return 2, _reject("site 名非法: %r" % (args.site,), state="usage-error",
                          reason_code=REASON_EXEC_ERROR, fallback_allowed=False)
    if not (0 < args.subtree_wait <= MAX_TIMEOUT_SECONDS):
        return 2, _reject("subtree-wait 越界（合法 0<v≤%d）: %r"
                          % (MAX_TIMEOUT_SECONDS, args.subtree_wait),
                          state="usage-error", reason_code=REASON_EXEC_ERROR,
                          fallback_allowed=False)
    payload = run_reconcile(run_dir, only_site=args.site, subtree_wait=args.subtree_wait)
    if payload.get("state") == "usage-error":
        return 2, payload
    return (0 if payload["ok"] else 1), payload


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(prog="outside-voice-job.py", add_help=True)
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("version")
    sub.add_parser("preflight")

    manifest_writer = sub.add_parser("install-manifest")
    # 缺省 = 本文件所在目录（安装态即 ~/.sdflow/hack）——安装步无须知道路径口径。
    manifest_writer.add_argument("--dir", default=None)

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

    cleanup = sub.add_parser("cleanup")
    add_site_only(cleanup)
    cleanup.add_argument("--cancel", action="store_true")
    cleanup.add_argument("--subtree-wait", type=float, default=SUBTREE_VERIFY_SECONDS)

    reconcile = sub.add_parser("reconcile")
    # 🔴 `--run-dir` required=True 是「禁止扫描最新目录」的第一道机械闸：
    # 没有默认值、没有「找最近一个 run」的兜底，恢复目标只能由操作者显式点名。
    reconcile.add_argument("--run-dir", required=True)
    reconcile.add_argument("--site", default=None)
    reconcile.add_argument("--subtree-wait", type=float, default=SUBTREE_VERIFY_SECONDS)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "version":
        sys.stdout.write(VERSION + "\n")
        return 0
    if args.command == "install-manifest":
        try:
            payload = write_manifest(args.dir or JOB_DIR)
        except OSError as exc:
            # 半份快照比没有快照更危险 ⇒ 失败一律非零退出、什么都不留（atomic_write_json
            # 走 temp+rename，故这里不会留下半截文件）。
            sys.stderr.write("install-manifest 失败: %s\n" % exc)
            return 1
        emit(payload)
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
    if args.command in ("status", "await", "collect", "cleanup", "reconcile"):
        code, payload = {"status": cmd_status, "await": cmd_await,
                         "collect": cmd_collect, "cleanup": cmd_cleanup,
                         "reconcile": cmd_reconcile}[args.command](args)
        emit(payload)
        return code
    parser.print_usage(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
