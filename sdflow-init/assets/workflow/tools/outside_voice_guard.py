#!/usr/bin/env python3
"""outside_voice_guard — 确定性 outside-voice 复用守卫（mlh-p4·T80）。
读一份 spec-review 的 outside-voice 产物（gstack-review.md）+ 一个 change 目录，
按三前置（来源 mode / 新鲜度 fs-mtime / 结构 codex 段）按序归约出**唯一** reason_code（六枚举）。
纯 stdlib、无 subprocess、门控外置（不读 config）；坏输入 fail-closed all-or-nothing。
新鲜度用源文件 fs-mtime 直比〔spec-review Q-C：撤销 grill 的 git 反转、纯 fs-mtime〕，
排除评审产物自身（gstack-review.md / spec-review-report.md / .outside-voice/）。承 4.C lens_metric_emit 形态。"""
import argparse, re, sys
from pathlib import Path

EXIT_OK, EXIT_FAIL = 0, 1
REASON_CODES = ("none", "file-missing", "section-not-found",
                "zero-findings", "stale", "simulated-source")   # 本地常量豁免（ADR-11：输入独有、不写进锚、不跨模块共享）
VALID_MODES = ("native", "simulated")                           # step1-broad-review 锚 mode 枚举（我们的锚，严格 fail-closed）
SOURCE_FILES = ("proposal.md", "design.md", "tasks.md")         # + specs/** 递归；评审产物自身不在此列（inclusion allowlist 天然排除）

_S1_RE = re.compile(r'<!--\s*sdflow:step1-broad-review\s+v1\b(.*?)-->')
_OV_ANCHOR_RE = re.compile(r'<!--\s*sdflow:outside-voice\s+v1\b(.*?)-->')
_ATTR_RE = re.compile(r'(\w+)="([^"]*)"')
_CODEX_LABEL_RE = re.compile(r'\bcodex#(\d+)\b')                 # adr/0002 codex#N 标签约定（次选解析路径）


class EmitError(Exception):
    """坏输入 fail-closed（我们的锚缺失/mode 非枚举/单一源不可读；区别于外部 codex 段的 best-effort 降级）。"""
    pass


def parse_mode(text):
    """抓 step1-broad-review 锚 mode（我们的锚，严格）。锚缺失/缺 mode/mode 非枚举 → EmitError。"""
    m = _S1_RE.search(text)
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
    """best-effort 解析 codex findings 计数。返回 int（含 0）；解析不出任何 codex 段 → None（→ section-not-found）。
    codex 段外部所有（adr/0002:21），格式漂移不崩溃、fail-closed 到 None。"""
    total = None
    for m in _OV_ANCHOR_RE.finditer(text):
        attrs = dict(_ATTR_RE.findall(m.group(1)))
        if attrs.get("runner") != "codex":               # 仅 runner=codex 计入（claude-fallback 不算 codex 段）
            continue
        raw = attrs.get("findings")
        if raw is None or not raw.isdigit():
            continue                                      # 畸形 findings 属性：跳过（best-effort）
        total = (total or 0) + int(raw)
    if total is not None:
        return total
    labels = set(_CODEX_LABEL_RE.findall(text))           # 次选：adr/0002 codex#N 标签
    if labels:
        return len(labels)
    return None


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
    # ③结构（codex 段可解析否 / 条数）
    n = parse_codex_findings(text)
    if n is None:
        return "section-not-found"
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
