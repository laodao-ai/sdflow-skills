"""Codex 宿主跨模型 voice 的**真实 efficacy 证据**确定性检查器。

【为什么要有它】
tasks.md 6.1/6.2/6.3〔OVBG-01, OVBG-03, HAE-08, HAE-09〕把「Codex efficacy=0 能不能关掉」
钉成三条门。这三条如果由模型自述「我跑过了、都绿了」，就是 adr/0018 说的那种**无机械锚的 ✅**。
∴ 证据本身落成一份**结构化 JSON**，判定归本脚本，模型只负责把证据生出来。

【三条门（逐条对应 tasks.md）】
  G1〔6.1〕该层**全部 declared 站点**取得 host="codex" runner="claude" reason_code="ok"。
       —— 「全部」是双向集合相等：declared ⊆ 实落 且 实落 ⊆ declared。
          单向包含会放过「少收一个站点」（HAE-09「per-site 完整性机械可审」正是这条）。
  G2〔6.2〕**至少一个**站点的**自然耗时 > 300 秒**且 model=opus / effort=high / reason_code=ok。
       —— 300 是旧同步天花板；`>` 是严格大于（等于 300 证不出「跨过」）。
          sleep/shim 与无模型命令由 G3 的 digest/字节数与 model/effort 字段挡（见下）。
  G3〔6.1 末句〕字段**可机读**：四个时刻可解析且单调、duration 与 (terminal-started) 自洽、
       stdout digest 是 64 位十六进制且 stdout 非空。

【第四条：证据里 MUST NOT 有 context / stderr 正文】
tasks.md 6.1 明写「不含 context/stderr 的结构化 efficacy 证据」。**这条要机械成立，靠的不是
「我没写进去」，而是 schema 白名单**：
  · 顶层与 site 的 key 集合 MUST **精确等于**白名单（多一个 key 即红）⇒ 没有 `stderr_text`
    这种字段可塞；
  · 任何字符串值 MUST 无换行、且长度 ≤ MAX_STRING_LEN ⇒ 没法把正文塞进某个合法字段。
stderr 只允许以 `stderr_bytes` / `stderr_lines` 两个**计数**出现（OVBG-04 的写出面约束）。

【语法面（基准 5：无界不手搓）】
输入是 **JSON**（`json.load` 由 stdlib 解释，不手搓解析器）；本脚本只做**结构断言**。
MUST NOT 演化成「从 Markdown 报告里正则抠证据」—— Markdown 是无界语法面。
∴ 证据的单一源是那个 `.json` 文件，报告引用它的路径。

【host 是**盘面派生**的，不是自报】
`host` 由 `outside-voice-job.py dispatch` 在**它自己所在的宿主 shell 里**读出来
（`CLAUDECODE=1` / `CODEX_THREAD_ID`，与 `resolve-models.sh` 判宿主同口径），落进
`<site>.job.json`，再由 status/collect 原样透传到 `<site>.collected.json`。
∴ 本脚本的 `emit` **从 witness 里读 host**，**没有** `--host` 入参 —— 决胜门 MUST NOT
靠调用方自报（那正是 adr/0018 说的「无机械锚的 ✅」，也正是本 change 要消灭的东西）。
旧格式 witness 没有 `host` ⇒ 搬 None ⇒ verify 报红，**fail-closed，MUST NOT 回落到自报**。

【诚实边界（MUST NOT 声称机械保证的部分）】
`declared_sites` **不是**本脚本能从盘面派生的：它是「这一层**应该**有哪些锚」，权威在评审
报告的锚行 / 编排层的实际调用，而 run-dir 只知道「实际 dispatch 了哪些」——拿实落集当
declared 集会让「漏收站点」自动自洽（HAE-09 要杀的正是这个）。∴ 它是**必填 CLI 入参**，
谁跑谁负责；本脚本机械守的是「一旦声明了，就必须处处自洽且达标」。

🔴 **`check` 不是防伪门 —— 它只核 evidence.json 的内部自洽性，不回查 run-dir。**
`verify()` 校 schema / key 白名单 / 时序单调 / duration 自洽 / digest 形状与去重，**全部只读
传进来的那一个文件**：它从不打开 `<site>.collected.json` 去对 job_id、attempt_nonce、
stdout_sha256。∴ **一份手写的、结构合规的 JSON 能让三条门全过**（`check` exit 0）——
已实测复现。安全性完全建立在「evidence.json 来自本脚本 `emit`」这个**流程约定**上，
而 `emit` 与 `check` 由同一方背靠背执行 ⇒ 这道门挡的是**手抄失误**，不是**自报为真**。
拿它当「模型说跑过了 ⇒ 机械证实跑过了」用，就又造出一个 adr/0018 的「无机械锚的 ✅」，
只是外壳换成了 sha256。**加固（给 `check` 补 `--run-dir` 逐站点交叉核验）挂在 T225**：
那张票会产出第一份真实 run-dir，届时新绑定能对着真证物验，而不是只对着自造 fixture。

用法：
    # 从 run-dir 的 <site>.collected.json 机械生成证据（避免手抄 collect 输出）
    python3 hack/check_codex_efficacy_evidence.py emit \
        --run-dir <d> --layer spec-review \
        --repo <name> --change <name> --declared-sites design-voice,hr-tg \
        --out <evidence.json>

    # 判定
    python3 hack/check_codex_efficacy_evidence.py check --evidence <evidence.json>

退出码：0=通过 | 1=不通过（逐条原因写 stderr） | 2=用法错 / 输入不可读
"""
import argparse
import json
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1

# ── 三条门的常量（改动即改契约，别在别处复制第二份）─────────────────────────
MIN_NATURAL_DURATION_SECONDS = 300.0   # 旧同步天花板；G2 要求**严格大于**
REQUIRED_HOST = "codex"
REQUIRED_RUNNER = "claude"
REQUIRED_REASON_CODE = "ok"
REQUIRED_MODEL = "opus"
REQUIRED_EFFORT = "high"

# duration 与 (terminal_at - started_at) 的允许偏差：两端时刻是秒级 ISO 串，
# 而 duration 由 helper 用同两个值算出并 round(…, 3) ⇒ 1 秒容差足够，且不足以
# 掩盖「把 200 秒写成 400 秒」这种量级的伪造。
DURATION_CONSISTENCY_TOLERANCE_SECONDS = 1.0

# 字符串值的硬上界 —— 与 key 白名单一起构成「证据里塞不进正文」的机械保证。
MAX_STRING_LEN = 256

TOP_LEVEL_KEYS = frozenset({
    "schema_version", "layer", "repo", "change", "run_id", "host",
    "declared_sites", "sites",
})

SITE_KEYS = frozenset({
    "site", "host", "runner", "model", "effort", "reason_code",
    "job_id", "attempt_nonce",
    "dispatched_at", "started_at", "terminal_at", "collected_at",
    "duration_seconds",
    "stdout_sha256", "stdout_bytes", "stdout_lines",
    "stderr_bytes", "stderr_lines",
})

# 四个时刻的先后次序（G3 的单调性）。
TIME_FIELDS = ("dispatched_at", "started_at", "terminal_at", "collected_at")

SHA256_RE = re.compile(r"\A[0-9a-f]{64}\Z")
ISO_RE = re.compile(r"\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")

LAYERS = ("spec-review", "code-review")


class EvidenceError(Exception):
    """输入不可读 / 不是 JSON —— 与「判定不通过」分开（前者 exit 2、后者 exit 1）。"""


# ── 判定 ────────────────────────────────────────────────────────────────────

def _parse_iso(value):
    """→ epoch 秒；不合形返回 None（调用方负责报错，MUST NOT 静默当 0）。"""
    if not isinstance(value, str) or not ISO_RE.match(value):
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc).timestamp()


def _check_scalars(node, where, failures):
    """递归查「字符串无换行且不超长」—— 证据里塞不进 context / stderr 正文。"""
    if isinstance(node, str):
        if "\n" in node or "\r" in node:
            failures.append(f"{where}: 字符串含换行 —— 证据 MUST NOT 携带正文")
        elif len(node) > MAX_STRING_LEN:
            failures.append(
                f"{where}: 字符串长度 {len(node)} > {MAX_STRING_LEN} —— "
                f"证据 MUST NOT 携带正文")
    elif isinstance(node, dict):
        for k, v in node.items():
            _check_scalars(v, f"{where}.{k}", failures)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _check_scalars(v, f"{where}[{i}]", failures)


def _check_site_shape(site, idx, failures):
    """G3 的逐字段形状 + G1 的三元组。→ site 名（拿不到时返回 None）。"""
    where = f"sites[{idx}]"
    if not isinstance(site, dict):
        failures.append(f"{where}: 不是对象")
        return None

    extra = set(site) - SITE_KEYS
    missing = SITE_KEYS - set(site)
    if extra:
        failures.append(f"{where}: 出现白名单外的 key {sorted(extra)} —— "
                        f"证据 schema 是封闭集合（防 stderr/context 夹带）")
    if missing:
        failures.append(f"{where}: 缺字段 {sorted(missing)}")
    if extra or missing:
        return site.get("site") if isinstance(site.get("site"), str) else None

    name = site["site"]
    if not isinstance(name, str) or not name:
        failures.append(f"{where}.site: MUST 为非空字符串")
        return None
    where = f"site[{name}]"

    # G1：三元组
    for field, expected in (("host", REQUIRED_HOST),
                            ("runner", REQUIRED_RUNNER),
                            ("reason_code", REQUIRED_REASON_CODE)):
        if site[field] != expected:
            failures.append(
                f"{where}.{field}={site[field]!r} ≠ {expected!r} —— "
                f"G1 要求该层每个站点都是可信跨模型成功")

    for field in ("model", "effort", "job_id", "attempt_nonce"):
        if not isinstance(site[field], str) or not site[field]:
            failures.append(f"{where}.{field}: MUST 为非空字符串")

    # G3：四个时刻可解析且单调
    epochs = {}
    for field in TIME_FIELDS:
        epoch = _parse_iso(site[field])
        if epoch is None:
            failures.append(
                f"{where}.{field}={site[field]!r}: MUST 为 YYYY-MM-DDTHH:MM:SSZ")
        epochs[field] = epoch
    for a, b in zip(TIME_FIELDS, TIME_FIELDS[1:]):
        if epochs[a] is not None and epochs[b] is not None and epochs[a] > epochs[b]:
            failures.append(f"{where}: 时刻次序颠倒 {a}({site[a]}) > {b}({site[b]})")

    # G3：duration 是正数且与 (terminal - started) 自洽
    duration = site["duration_seconds"]
    if isinstance(duration, bool) or not isinstance(duration, (int, float)):
        failures.append(f"{where}.duration_seconds: MUST 为数字")
    elif duration <= 0:
        failures.append(f"{where}.duration_seconds={duration}: MUST > 0")
    elif epochs["started_at"] is not None and epochs["terminal_at"] is not None:
        span = epochs["terminal_at"] - epochs["started_at"]
        if abs(duration - span) > DURATION_CONSISTENCY_TOLERANCE_SECONDS:
            failures.append(
                f"{where}.duration_seconds={duration} 与 "
                f"terminal_at-started_at={span} 不自洽（容差 "
                f"{DURATION_CONSISTENCY_TOLERANCE_SECONDS}s）")

    # G3：stdout digest 与字节数 —— 成功站点的 stdout MUST 非空（rc=0+空 stdout 早被
    # helper 判 exec-error，这里是证据层的第二道）。
    if not isinstance(site["stdout_sha256"], str) or \
            not SHA256_RE.match(site["stdout_sha256"] or ""):
        failures.append(f"{where}.stdout_sha256: MUST 为 64 位小写十六进制")
    for field, floor in (("stdout_bytes", 1), ("stdout_lines", 1),
                         ("stderr_bytes", 0), ("stderr_lines", 0)):
        value = site[field]
        if isinstance(value, bool) or not isinstance(value, int):
            failures.append(f"{where}.{field}: MUST 为整数")
        elif value < floor:
            failures.append(f"{where}.{field}={value}: MUST ≥ {floor}")
    return name


def crossed_ceiling(site):
    """该站点是否**自然跨过了旧同步天花板**（G2 的谓词）。

    **成功摘要行也 MUST 用这一个谓词** —— 摘要是人会直接引用的证据句，若它只看
    duration、不看 model/effort/reason_code，就会把一个 sonnet 站点列进
    「自然 >300s 的站点」，把 G2 的结论说得比实际宽。判据只此一份。
    """
    if not isinstance(site, dict):
        return False
    duration = site.get("duration_seconds")
    return (isinstance(duration, (int, float))
            and not isinstance(duration, bool)
            and duration > MIN_NATURAL_DURATION_SECONDS
            and site.get("model") == REQUIRED_MODEL
            and site.get("effort") == REQUIRED_EFFORT
            and site.get("reason_code") == REQUIRED_REASON_CODE
            and site.get("runner") == REQUIRED_RUNNER)


def verify(evidence):
    """→ 失败原因列表（空 = 三条门全过）。"""
    failures = []
    if not isinstance(evidence, dict):
        return ["证据顶层不是对象"]

    extra = set(evidence) - TOP_LEVEL_KEYS
    missing = TOP_LEVEL_KEYS - set(evidence)
    if extra:
        failures.append(f"顶层出现白名单外的 key {sorted(extra)} —— "
                        f"证据 schema 是封闭集合（防 stderr/context 夹带）")
    if missing:
        failures.append(f"顶层缺字段 {sorted(missing)}")
    if missing:
        return failures

    _check_scalars(evidence, "evidence", failures)

    if evidence["schema_version"] != SCHEMA_VERSION:
        failures.append(f"schema_version={evidence['schema_version']!r} "
                        f"≠ {SCHEMA_VERSION}")
    if evidence["host"] != REQUIRED_HOST:
        failures.append(f"host={evidence['host']!r} ≠ {REQUIRED_HOST!r} —— "
                        f"本证据只对 Codex 宿主有意义")
    if evidence["layer"] not in LAYERS:
        failures.append(f"layer={evidence['layer']!r} MUST ∈ {list(LAYERS)}")
    for field in ("repo", "change", "run_id"):
        if not isinstance(evidence[field], str) or not evidence[field]:
            failures.append(f"{field}: MUST 为非空字符串")

    declared = evidence["declared_sites"]
    if not isinstance(declared, list) or not declared or \
            not all(isinstance(s, str) and s for s in declared):
        failures.append("declared_sites: MUST 为非空的字符串列表 —— "
                        "空集会让 G1 的 all() 恒真（空集假绿）")
        declared = []
    elif len(set(declared)) != len(declared):
        failures.append(f"declared_sites 有重复项: {declared}")

    sites = evidence["sites"]
    if not isinstance(sites, list) or not sites:
        failures.append("sites: MUST 为非空列表")
        return failures

    names = []
    for idx, site in enumerate(sites):
        name = _check_site_shape(site, idx, failures)
        if name is not None:
            names.append(name)
    if len(set(names)) != len(names):
        failures.append(f"sites 有重复站点: {names}")

    # per-site 完整性：**站点名不同还不够，身份也 MUST 各不相同**。
    # 把同一份 witness 复制成 N 个站点名（job_id / attempt_nonce / stdout digest 全相同）
    # 只需改一个字段就能伪造出「整层都成功了」—— 这是 HAE-09「漏收站点」的镜像形态：
    # 前者少一个真站点，后者多 N-1 个假站点，而单看站点名两者都自洽。
    for field, label in (("job_id", "canonical job id"),
                         ("attempt_nonce", "attempt nonce"),
                         ("stdout_sha256", "stdout digest")):
        values = [s[field] for s in sites
                  if isinstance(s, dict) and isinstance(s.get(field), str)]
        if len(set(values)) != len(values):
            dupes = sorted({v for v in values if values.count(v) > 1})
            failures.append(
                f"sites 的 {field} 有重复（{label}）: {dupes} —— "
                f"不同站点 MUST 是不同的真实 attempt，"
                f"同一份 witness 换个站点名复制 N 份不构成 per-site 完整性")

    # G1 的「全部」= 双向集合相等（单向包含会放过漏收站点）
    if declared and set(names) != set(declared):
        only_declared = sorted(set(declared) - set(names))
        only_present = sorted(set(names) - set(declared))
        failures.append(
            f"declared_sites 与实落证据站点集不等: "
            f"只在 declared={only_declared} / 只在证据={only_present}")

    # G2：至少一个自然 >300 秒的强模型成功站点
    if not any(crossed_ceiling(s) for s in sites):
        failures.append(
            f"G2 未达标：没有任何站点满足「自然 duration > "
            f"{MIN_NATURAL_DURATION_SECONDS}s ∧ model={REQUIRED_MODEL} ∧ "
            f"effort={REQUIRED_EFFORT} ∧ runner={REQUIRED_RUNNER} ∧ "
            f"reason_code={REQUIRED_REASON_CODE}」—— "
            f"未证明跨过旧同步天花板，MUST NOT 关闭 efficacy 缺口")
    return failures


# ── 证据生成（从 run-dir 的 collected witness 机械派生）──────────────────────

def _load_collected(run_dir, site):
    path = Path(run_dir) / f"{site}.collected.json"
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise EvidenceError(f"读不到 {path}: {e}")
    try:
        return json.loads(raw)
    except ValueError as e:
        raise EvidenceError(f"{path} 不是合法 JSON: {e}")


MIXED_HOST = "mixed"


def emit(run_dir, layer, repo, change, declared_sites):
    """→ 证据 dict。**只搬 collect 已经落盘的字段，不新造事实。**

    缺字段一律原样搬 None ⇒ 由 verify 报出来，MUST NOT 在这里兜底成好看的默认值。

    `host` 也一样从 witness 搬（dispatch 在宿主 shell 里读出、经 job.json → collect 透传）。
    **没有 `--host` 入参可以覆盖它。** 各站点 host 不一致 ⇒ 顶层落 `MIXED_HOST`，由 verify
    判红；旧格式 witness 无该字段 ⇒ None ⇒ 同样判红（fail-closed）。
    """
    sites = []
    run_id = None
    for name in declared_sites:
        data = _load_collected(run_dir, name)
        run_id = run_id or data.get("run_id")
        sites.append({k: data.get(k) for k in sorted(SITE_KEYS)})
    hosts = {s["host"] for s in sites}
    host = hosts.pop() if len(hosts) == 1 else MIXED_HOST
    return {
        "schema_version": SCHEMA_VERSION,
        "layer": layer,
        "repo": repo,
        "change": change,
        "run_id": run_id,
        "host": host,
        "declared_sites": list(declared_sites),
        "sites": sites,
    }


# ── CLI ─────────────────────────────────────────────────────────────────────

def _split_sites(raw):
    return [s.strip() for s in raw.split(",") if s.strip()]


def build_parser():
    parser = argparse.ArgumentParser(
        prog="check_codex_efficacy_evidence.py",
        description="Codex 宿主跨模型 voice 真实 efficacy 证据的确定性检查器")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="判定一份证据是否满足三条门")
    p_check.add_argument("--evidence", required=True)

    p_emit = sub.add_parser("emit", help="从 run-dir 的 collected witness 生成证据")
    p_emit.add_argument("--run-dir", required=True)
    # 有意**没有** `--host`：宿主是盘面派生量（dispatch 在宿主 shell 里读、经 job.json →
    # collect 透传到 witness）。留一个自报入参就等于给决胜门留了后门。
    p_emit.add_argument("--layer", required=True)
    p_emit.add_argument("--repo", required=True)
    p_emit.add_argument("--change", required=True)
    p_emit.add_argument("--declared-sites", required=True,
                        help="逗号分隔；是「本层应有锚的站点集」，不是「实际 dispatch 集」")
    p_emit.add_argument("--out", required=True)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.command == "emit":
        declared = _split_sites(args.declared_sites)
        if not declared:
            print("[efficacy] FAIL: --declared-sites 解析为空集 —— "
                  "空集会让门恒真", file=sys.stderr)
            return 2
        try:
            evidence = emit(args.run_dir, args.layer,
                            args.repo, args.change, declared)
        except EvidenceError as e:
            print(f"[efficacy] FAIL: {e}", file=sys.stderr)
            return 2
        Path(args.out).write_text(
            json.dumps(evidence, indent=2, sort_keys=True,
                       ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[efficacy] 已写出证据 {args.out}（{len(evidence['sites'])} 站点）")
        return 0

    try:
        raw = Path(args.evidence).read_text(encoding="utf-8")
    except OSError as e:
        print(f"[efficacy] FAIL: 读不到证据文件 {args.evidence}: {e}",
              file=sys.stderr)
        return 2
    try:
        evidence = json.loads(raw)
    except ValueError as e:
        print(f"[efficacy] FAIL: 证据不是合法 JSON: {e}", file=sys.stderr)
        return 2

    failures = verify(evidence)
    if failures:
        print(f"[efficacy] ❌ 未通过（{len(failures)} 条）：", file=sys.stderr)
        for f in failures:
            print(f"   · {f}", file=sys.stderr)
        print("   ⇒ tasks.md 6.3：保留 T162 并如实记录，MUST NOT 以编排 smoke 假绿",
              file=sys.stderr)
        return 1

    crossed = [s["site"] for s in evidence["sites"] if crossed_ceiling(s)]
    print(f"[efficacy] ✅ 三条门全过 —— layer={evidence['layer']} "
          f"host={evidence['host']} 站点 {len(evidence['sites'])}/"
          f"{len(evidence['declared_sites'])} 全 ok；"
          f"自然 >{MIN_NATURAL_DURATION_SECONDS:.0f}s 的站点: {crossed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
