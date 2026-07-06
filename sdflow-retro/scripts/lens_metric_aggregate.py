#!/usr/bin/env python3
"""lens-metric 只读聚合器（盘面即状态·view-only）。
扫 archive/**/*-review-report.md 的 sdflow:lens-metric v1 锚 → 多列可排序表。
净新字段提取解析器；脚本内重实现 fence-aware 行级核（禁裸 split/substring、
禁跨 skill import ship_gate）。不写任何持久文件、不产合成价值分。契约见
sdflow-init/assets/workflow/lens-metric-contract.md。"""
import re
import sys
import argparse
from pathlib import Path
from collections import defaultdict

ANCHOR_PREFIX = "<!-- sdflow:lens-metric v1"
# [T59] 「出现轮数 ≥N 待复评」阈值单一源——render_table 与 retro_report.surfacing_block
# 共同引用（此前两处各硬编码 10，调整易改一处漏一处致 flag 口径漂移）。
REVIEW_ROUNDS_THRESHOLD = 10
LAYER_ENUM = {"spec-review", "code-review"}
LENS_ENUM = {"domain", "adversarial", "grounding", "history", "outside-voice", "broad"}
_KV = re.compile(r'([^\s=]+)="([^"]*)"')  # 受限 kv：key="value"，禁裸 split
_FENCE_OPEN = re.compile(r'^\s*(`{3,}|~{3,})')  # [impl-review-fix CF-4 / T58] 反引号或波浪号 fence，捕获确切标记


def _fence_aware_lines(text):
    """产出非 fenced-block 行。真实 CommonMark fence 语义：记录开启 fence 的
    标记字符（` 或 ~）与确切长度，收尾须遇到「同字符且长度 >= 开启长度」的 fence
    才闭合——故 4-反引号外层可安全嵌套 3-反引号内层示范锚（内层不会被误判为已跳出），
    且 ``` 与 ~~~ 互不闭合（T58：此前只认反引号，~~~ 代码块里的示范锚被误计入聚合）。
    [impl-review-fix CF-4 / T58]（本脚本内重实现，不跨 skill import）。"""
    fence = None  # None = 不在 fence 内；否则 (标记字符, 需匹配的最小闭合长度)
    for line in text.splitlines():
        m = _FENCE_OPEN.match(line)
        if fence is None:
            if m:
                marker = m.group(1)
                fence = (marker[0], len(marker))
                continue
            yield line
        else:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1]:
                fence = None
            continue


def parse_anchor(line):
    """从一行提取 lens-metric 字段 dict；非锚行返回 None。
    锚须独占行前缀（strip 后 startswith ANCHOR_PREFIX）——非行首匹配不误取。"""
    s = line.strip()
    if not s.startswith(ANCHOR_PREFIX):
        return None
    fields = {k: v for k, v in _KV.findall(s)}
    return fields or None


def parse_report(path):
    text = Path(path).read_text(encoding="utf-8")
    rows = []
    for line in _fence_aware_lines(text):
        f = parse_anchor(line)
        if f:
            rows.append(f)
    return rows


def aggregate(archive_root):
    """扫 archive/**/*-review-report.md；返回 (锚行 rows, 无锚 change 名 list,
    解析失败 change 名 list)。[impl-review-fix CF-2] 单个报告文件读取/解码失败
    （编码坏字节、IO 错误等）不拖垮全局聚合——单独 try/except，坏文件显式计入
    「解析失败」桶（不静默丢弃），其余报告照常聚合。
    [T61] 显式契约：archive_root 不是目录（缺失/被删/恰是文件）→ 返回空三元组。
    这把「缺 archive → 空」从 Path.glob 的偶然实现行为升成本函数的文档化契约，
    使 call site 无需再包不可达的防御性 try/except。"""
    if not Path(archive_root).is_dir():
        return [], [], []
    rows, no_anchor, parse_failed = [], [], []
    for report in sorted(Path(archive_root).glob("**/*-review-report.md")):
        try:
            rr = parse_report(report)
        except (OSError, UnicodeDecodeError, ValueError):
            parse_failed.append(report.parent.name)
            continue
        if rr:
            for f in rr:
                f["_change"] = report.parent.name
            rows.extend(rr)
        else:
            no_anchor.append(report.parent.name)
    return rows, no_anchor, parse_failed


def _int(v):
    """契约字段 int≥0。[impl-review-fix CF-5] 解析失败（如 "3.0" 这类浮点串）
    或负值均判「数值非法」——不静默吞成 0 装作正常，返回 (值, is_bad) 二元组，
    调用侧显式标记 flag，同 ⚠越域 口径不静默。"""
    try:
        n = int(v)
    except (TypeError, ValueError):
        return 0, True
    if n < 0:
        return n, True
    return n, False


def group_key(r):
    """lens-metric 锚的分组键 (layer, lens, runner, site)——render_table 与
    下游 surfacing 共用，杜绝两处手写归一化漂移（尤其 lens 空串→"?"）。"""
    return (r.get("layer", "?"), r.get("lens", "") or "?",
            r.get("runner", "?"), r.get("site", "—"))


def render_table(rows, no_anchor, parse_failed=None):
    """多列可排序描述性表（无合成分）。按 (layer,lens,runner,site) 分组
    [impl-review-fix CF-1]（契约键含 runner——codex 与 claude-fallback 的
    outside-voice 需分行，不可合并）：
    出现轮数 · Σfindings · Σ采纳 · Σ裁掉 · Σdefer · Σ独立 · 采纳率 · 独立率 · flag。"""
    parse_failed = parse_failed or []
    grp = defaultdict(lambda: dict(轮=0, f=0, 采纳=0, 裁掉=0, defer=0, 独立=0,
                                    bad=False, num_bad=False))
    for r in rows:
        lens = r.get("lens", "")
        bad = (r.get("layer") not in LAYER_ENUM) or (lens not in LENS_ENUM)
        key = group_key(r)
        g = grp[key]
        g["轮"] += 1
        num_bad = False
        vals = {}
        for fld in ("findings", "采纳", "裁掉", "defer", "独立"):
            v, nb = _int(r.get(fld))
            vals[fld] = v
            num_bad = num_bad or nb
        g["f"] += vals["findings"]
        g["采纳"] += vals["采纳"]
        g["裁掉"] += vals["裁掉"]
        g["defer"] += vals["defer"]
        g["独立"] += vals["独立"]
        g["bad"] = g["bad"] or bad
        g["num_bad"] = g["num_bad"] or num_bad
    hdr = "| layer | lens | runner | site | 出现轮数 | Σfindings | Σ采纳 | Σ裁掉 | Σdefer | Σ独立 | 采纳率 | 独立率 | flag |"
    sep = "|" + "---|" * 13
    lines = [hdr, sep]
    for (layer, lens, runner, site), g in sorted(grp.items()):
        denom = g["采纳"] + g["裁掉"] + g["defer"]
        采纳率 = f"{g['采纳']/denom:.0%}" if denom else "—"
        独立率 = f"{g['独立']/g['f']:.0%}" if g["f"] else "—"
        flags = []
        if g["轮"] >= REVIEW_ROUNDS_THRESHOLD:
            flags.append(f"≥{REVIEW_ROUNDS_THRESHOLD}待复评")
        if g["bad"]:
            flags.append("⚠越域")
        if g["num_bad"]:
            flags.append("⚠数值非法")
        lines.append(f"| {layer} | {lens} | {runner} | {site} | {g['轮']} | {g['f']} | {g['采纳']} | "
                     f"{g['裁掉']} | {g['defer']} | {g['独立']} | {采纳率} | {独立率} | {' '.join(flags) or '—'} |")
    lines.append("")
    # [impl-review-fix CF-7] 「N 份」= 报告文件数（每 change 常含 spec/code 两份），
    # 非去重后的 change 数——同名 change 连续出现两次不是 bug，是 spec+code 两份报告；
    # 另附去重后 change 数供快速核对规模。
    lines.append(f"> 无锚样本 {len(no_anchor)} 份（旧格式,不纳入；份=报告文件数，"
                 f"每 change 常含 spec/code 两份，非 change 数；去重后 {len(set(no_anchor))} 个 change）: "
                 f"{', '.join(no_anchor) or '无'}")
    # [impl-review-fix CF-2] 解析失败桶显式呈现，不静默丢弃坏文件。
    lines.append(f"> 解析失败 {len(parse_failed)} 份（编码/IO 错误，已跳过未计入聚合，不拖垮全局）: "
                 f"{', '.join(parse_failed) or '无'}")
    lines.append("> 独立率跨轮不保证同口径（dedup 合并尺度可能漂移），复评时校验最近几轮尺度一致。")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="lens-metric 只读聚合器（view-only）")
    ap.add_argument("--root", default=".", help="仓根（含 openspec/changes/archive）")
    args = ap.parse_args(argv)
    archive = Path(args.root) / "openspec" / "changes" / "archive"
    rows, no_anchor, parse_failed = aggregate(archive)
    print(render_table(rows, no_anchor, parse_failed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
