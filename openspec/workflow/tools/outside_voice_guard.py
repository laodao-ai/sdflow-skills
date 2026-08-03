#!/usr/bin/env python3
"""outside_voice_guard — 确定性 outside-voice 复用守卫（mlh-p4·T80）。
读一份 spec-review 的 outside-voice 产物（gstack-review.md）+ 一个 change 目录，
按三前置（来源 mode / 新鲜度 fs-mtime / 结构 codex 段）按序归约出**唯一** reason_code（七枚举，
add-codex-host-support 新增 `same-family`：同族 fallback / 无执行段均不得复用）。
纯 stdlib、无 subprocess、门控外置（不读 config）；坏输入 fail-closed all-or-nothing。
新鲜度用源文件 fs-mtime 直比〔spec-review Q-C：撤销 grill 的 git 反转、纯 fs-mtime〕，
排除评审产物自身（gstack-review.md / spec-review-report.md / .outside-voice/）。承 4.C lens_metric_emit 形态。
add-codex-host-support：结构判改为引用「合法组合矩阵」的跨模型判定（`classify_combo`，本地重实现，
MUST NOT import anchor_lint——GC-2 边界锁），与 anchor_lint 的同名函数由全笛卡尔 golden 测试互相守一致
（tests/test_outside_voice_guard.py Step 5）。"""
import argparse, re, sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from pathlib import Path

EXIT_OK, EXIT_FAIL = 0, 1
REASON_CODES = ("none", "file-missing", "section-not-found", "zero-findings", "stale",
                 "simulated-source", "same-family")             # 本地常量豁免（ADR-11：输入独有、不写进锚、不跨模块共享）
VALID_MODES = ("native", "simulated")                           # step1-broad-review 锚 mode 枚举（我们的锚，严格 fail-closed）
SOURCE_FILES = ("proposal.md", "design.md", "tasks.md")         # + specs/** 递归；评审产物自身不在此列（inclusion allowlist 天然排除）

_S1_RE = re.compile(r'<!--\s*sdflow:step1-broad-review\s+v1\b(.*?)-->')
_OV_ANCHOR_RE = re.compile(r'<!--\s*sdflow:outside-voice\s+v1\b(.*?)-->')
_ATTR_RE = re.compile(r'(\w+)="([^"]*)"')
_FENCE_RE = re.compile(r'^ {0,3}(`{3,}|~{3,})')                 # CommonMark fence：0-3 空格缩进 + ≥3 同字符 marker


class EmitError(Exception):
    """坏输入 fail-closed（我们的锚缺失/mode 非枚举/单一源不可读；区别于外部 codex 段的 best-effort 降级）。"""
    pass


# =========================================================================================
# add-codex-host-support：合法组合矩阵——「跨模型」判定的本地重实现（GC-2：MUST NOT import anchor_lint，
# 关系式判定逻辑本文件内重实现；契约块只承载枚举域，不承载这些关系式谓词，见 lens-metric-contract.md
# 「跨模型性」段）。逻辑与 anchor_lint.classify_combo **逐条同构**——由全笛卡尔 golden 测试
# （tests/test_outside_voice_guard.py Step 5）互相守一致，任一漂移即红。
# =========================================================================================

_DOWNGRADE_CODES = frozenset({"not-installed", "preflight-error", "timeout", "exec-error"})  # 同族 fallback 降级码集
_NOEXEC_KNOWN_CODES = frozenset({"secret-hit", "fallback-unavailable"})                      # 无执行 · host∈{claude,codex}
_DUOS = frozenset({"claude", "codex"})                                                        # 两个真机队（谈跨模型的前提）


def classify_combo(host, runner, reason_code, findings):
    """把 (host, runner, reason_code, findings) 分类为**完整**类别（本地重实现，逻辑与
    anchor_lint.classify_combo 逐条同构）：
      'cross-model'  合法跨模型第二意见：host,runner∈{claude,codex} ∧ runner≠host ∧ reason_code='ok'
      'same-family'  合法同族降级：runner==host ∧ reason_code∈降级码集
      'no-exec'      合法无执行：runner='none' ∧ findings==0 ∧ (host='unknown'∧rc='host-unknown' ∨ host∈{claude,codex}∧rc∈{secret-hit,fallback-unavailable})
      'self-review'  runner==host ∧ reason_code∉降级码集（同族行子句被违反）
      'illegal'      其余一切非法组合（catch-all）
    findings 为已解析的 int（不可解析/缺失 → None）。"""
    if runner == "none":
        if findings == 0 and (
            (host == "unknown" and reason_code == "host-unknown")
            or (host in _DUOS and reason_code in _NOEXEC_KNOWN_CODES)
        ):
            return "no-exec"
        return "illegal"
    if host in _DUOS and runner in _DUOS:
        if runner == host:
            return "same-family" if reason_code in _DOWNGRADE_CODES else "self-review"
        return "cross-model" if reason_code == "ok" else "illegal"
    return "illegal"


def _fence_outside_lines(text):
    """产出 fence 外行（CommonMark：0-3 空格缩进 + ≥3 同字符 marker 成对开合，闭合行 marker 后仅空白）。
    口径与姊妹校验器 anchor_lint.fence_outside_lines / review_disposition_check._annotate_lines 一致——
    D5 铁律：跨模块口径本文件内重实现，MUST NOT import。防 fence 内的文档示例锚被误算（adr/0018 输出诚实）。"""
    fence = None
    for ln in text.splitlines():
        m = _FENCE_RE.match(ln)
        if fence is None:
            if m:
                fence = (m.group(1)[0], len(m.group(1))); continue
            yield ln
        else:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1] and ln[m.end():].strip() == "":
                fence = None
            continue


def _fence_outside_text(text):
    """fence 外行 join 回文本；锚为单行、join 保行完整，fenced 锚被整块剔除（不参与匹配）。"""
    return "\n".join(_fence_outside_lines(text))


def parse_mode(text):
    """抓 step1-broad-review 锚 mode（我们的锚，严格）。锚缺失/缺 mode/mode 非枚举 → EmitError。
    仅匹配 fence 外锚——fence 内的示例锚（文档演示）不得被取（与 parse_codex_findings 同口径）。"""
    m = _S1_RE.search(_fence_outside_text(text))
    if not m:
        raise EmitError("step1-broad-review 锚缺失或格式不符")
    mode = dict(_ATTR_RE.findall(m.group(1))).get("mode")
    if mode is None:
        raise EmitError("step1-broad-review 锚缺 mode 属性")
    if mode not in VALID_MODES:
        raise EmitError(f"mode 非枚举值（须 native|simulated）: {mode!r}")
    return mode


def source_max_mtime(change_dir):
    """源文件（proposal/design/tasks/specs/**）最大 fs-mtime；评审产物自身天然不在 allowlist。
    change_dir 缺失/非目录/无源文件 → EmitError（无法判新鲜度，fail-closed）。"""
    if not change_dir.is_dir():
        raise EmitError(f"change 目录不存在或非目录: {change_dir}")
    mtimes = []
    for name in SOURCE_FILES:
        p = change_dir / name
        if p.is_file():
            mtimes.append(p.stat().st_mtime)
    specs_dir = change_dir / "specs"
    if specs_dir.is_dir():
        for p in sorted(specs_dir.rglob("*")):
            if p.is_file():
                mtimes.append(p.stat().st_mtime)
    if not mtimes:
        raise EmitError(f"change 目录无源文件（proposal/design/tasks/specs）: {change_dir}")
    return max(mtimes)


def parse_codex_findings(text):
    """best-effort 解析可复用的 outside-voice findings 计数。返回三态之一：
      int（含 0）           — 至少一条 cross-model 锚且其 findings 可解析；值为这些**可解析** findings 之和。
                              cross-model 锚 findings 畸形/缺失（不可解析）⇒ 不贡献计数（C1：MUST NOT 退去
                              扫无关 codex#N prose 标签补位——那会把正文一句 "codex#1" 当可复用、静默跳过
                              重跑跨模型评审、击穿本 guard 防假复用的唯一职责）；若无任何可解析 cross-model
                              findings ⇒ 落 None（不复用、回落重跑）。
      "same-family"（字符串哨兵） — 无可复用 cross-model findings，但存在 ≥1 条被矩阵分类为 same-family/
                              no-exec/self-review 的锚（同族 fallback / 无执行 / 自审——均非跨模型第二意见）
      None                  — 无任何可复用信号（无锚 / 仅 illegal 锚 best-effort 跳过 / cross-model 锚 findings
                              全畸形 / 仅 codex#N prose 标签）→ section-not-found。**prose 标签 MUST NOT 构成
                              可复用资格**（add-codex-host-support Step 6+C1：labels 不再是任何复用路径的旁路）。
    `host`/`reason_code` 缺失字段按 v1 兼容读（GC-9：MUST NOT 因缺字段 fail-closed 罢工，旧产物依然可复用）：
    无 `host=` → `host="claude"`；无 `reason_code=` → `reason_code="ok"`。
    仅匹配 fence 外锚——fence 内的文档示例锚不得计入（否则 outside-voice 层被静默当有效复用跳过，违 adr/0018）。"""
    text = _fence_outside_text(text)
    cross_total = None            # 已确认的可解析 cross-model 锚 findings 之和（无则保持 None）
    same_family_found = False     # 是否存在 same-family/no-exec/self-review 锚（非跨模型，但可辨识的合法态）
    for m in _OV_ANCHOR_RE.finditer(text):
        attrs = dict(_ATTR_RE.findall(m.group(1)))
        runner = attrs.get("runner")
        if runner is None:
            continue                                      # runner 缺失：无从分类，best-effort 跳过
        host = attrs.get("host", "claude")                # v1 兼容：无 host= → claude（GC-9）
        reason_code = attrs.get("reason_code", "ok")       # v1 兼容：无 reason_code= → ok（GC-9）
        raw = attrs.get("findings")
        findings_val = int(raw) if (raw is not None and raw.isascii() and raw.isdigit()) else None
        cat = classify_combo(host, runner, reason_code, findings_val)
        if cat == "cross-model":
            if findings_val is not None:                   # findings 畸形的 cross-model 锚不贡献计数（C1：不复用、回落）
                cross_total = (cross_total or 0) + findings_val
        elif cat in ("same-family", "no-exec", "self-review"):
            same_family_found = True                       # illegal 不计入任何一侧（畸形/垃圾，best-effort 跳过）
    if cross_total is not None:
        return cross_total
    if same_family_found:
        return "same-family"
    return None                                             # 无锚/仅 illegal 锚/findings 畸形/仅 prose 标签 → section-not-found


def classify(review_path, change_dir):
    """三前置按序（来源 > 新鲜度 > 结构）归约 → 唯一 reason_code。坏输入 → EmitError。"""
    # 产物存在性（file-missing 是合法判定，不需 change_dir）
    if not review_path.exists():
        return "file-missing"
    if not review_path.is_file():
        raise EmitError(f"产物路径非普通文件: {review_path}")
    try:
        text = review_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise EmitError(f"产物不可读: {e}")
    # ①来源（mode；simulated 视同无效）
    if parse_mode(text) == "simulated":
        return "simulated-source"
    # ②新鲜度（fs-mtime 直比；产物早于源文件最大 mtime → stale。此处才需 change_dir）
    if review_path.stat().st_mtime < source_max_mtime(change_dir):
        return "stale"
    # ③结构（矩阵判「跨模型」可解析否 / 条数；same-family = 同族 fallback / 无执行段，MUST NOT 复用）
    n = parse_codex_findings(text)
    if n is None:
        return "section-not-found"
    if n == "same-family":
        return "same-family"
    if n == 0:
        return "zero-findings"
    return "none"


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="outside-voice 复用守卫（确定性·纯 stdlib·fail-closed·门控外置）")
    ap.add_argument("--review-path", required=True, help="outside-voice 产物路径（gstack-review.md）")
    ap.add_argument("--change-dir", required=True, help="change 目录（openspec/changes/<name>/）")
    args = ap.parse_args(argv)
    try:
        code = classify(Path(args.review_path), Path(args.change_dir))
    except EmitError as e:
        print(f"[outside_voice_guard] FAIL: {e}", file=sys.stderr)   # 坏输入：stderr FAIL、无 stdout
        return EXIT_FAIL
    print(code)                                                       # reason_code 落 stdout（含 none）
    return EXIT_OK if code == "none" else EXIT_FAIL                   # none=可复用 exit0；其余=非零（stdout 载码，区别于 stderr FAIL）


if __name__ == "__main__":
    sys.exit(main())
