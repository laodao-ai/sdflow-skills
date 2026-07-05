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
LAYER_ENUM = {"spec-review", "code-review"}
LENS_ENUM = {"domain", "adversarial", "grounding", "history", "outside-voice", "broad"}
_KV = re.compile(r'([^\s=]+)="([^"]*)"')  # 受限 kv：key="value"，禁裸 split
_FENCE_OPEN = re.compile(r'^\s*(`{3,})')  # [impl-review-fix CF-4] 捕获反引号确切长度


def _fence_aware_lines(text):
    """产出非 fenced-block 行。真实 CommonMark fence 语义：记录开启 fence 的
    确切反引号长度，收尾须遇到 >= 该长度的同字符 fence 才闭合——故 4-反引号外层
    可安全嵌套 3-反引号内层示范锚（内层不会被误判为已跳出）。
    [impl-review-fix CF-4]（本脚本内重实现，不跨 skill import）。"""
    fence_len = None  # None = 不在 fence 内；否则为需要匹配的最小闭合长度
    for line in text.splitlines():
        m = _FENCE_OPEN.match(line)
        if fence_len is None:
            if m:
                fence_len = len(m.group(1))
                continue
            yield line
        else:
            if m and len(m.group(1)) >= fence_len:
                fence_len = None
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
    「解析失败」桶（不静默丢弃），其余报告照常聚合。"""
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
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def render_table(rows, no_anchor):
    """多列可排序描述性表（无合成分）。按 (layer,lens,site) 分组：
    出现轮数 · Σfindings · Σ采纳 · Σ裁掉 · Σdefer · Σ独立 · 采纳率 · 独立率 · flag。"""
    grp = defaultdict(lambda: dict(轮=0, f=0, 采纳=0, 裁掉=0, defer=0, 独立=0, bad=False))
    for r in rows:
        lens = r.get("lens", "")
        bad = (r.get("layer") not in LAYER_ENUM) or (lens not in LENS_ENUM)
        key = (r.get("layer", "?"), lens or "?", r.get("site", "—"))
        g = grp[key]
        g["轮"] += 1
        g["f"] += _int(r.get("findings"))
        g["采纳"] += _int(r.get("采纳"))
        g["裁掉"] += _int(r.get("裁掉"))
        g["defer"] += _int(r.get("defer"))
        g["独立"] += _int(r.get("独立"))
        g["bad"] = g["bad"] or bad
    hdr = "| layer | lens | site | 出现轮数 | Σfindings | Σ采纳 | Σ裁掉 | Σdefer | Σ独立 | 采纳率 | 独立率 | flag |"
    sep = "|" + "---|" * 12
    lines = [hdr, sep]
    for (layer, lens, site), g in sorted(grp.items()):
        denom = g["采纳"] + g["裁掉"] + g["defer"]
        采纳率 = f"{g['采纳']/denom:.0%}" if denom else "—"
        独立率 = f"{g['独立']/g['f']:.0%}" if g["f"] else "—"
        flags = []
        if g["轮"] >= 10:
            flags.append("≥10待复评")
        if g["bad"]:
            flags.append("⚠越域")
        lines.append(f"| {layer} | {lens} | {site} | {g['轮']} | {g['f']} | {g['采纳']} | "
                     f"{g['裁掉']} | {g['defer']} | {g['独立']} | {采纳率} | {独立率} | {' '.join(flags) or '—'} |")
    lines.append("")
    lines.append(f"> 无锚样本 {len(no_anchor)} 份（旧格式,不纳入）: {', '.join(no_anchor) or '无'}")
    lines.append("> 独立率跨轮不保证同口径（dedup 合并尺度可能漂移），复评时校验最近几轮尺度一致。")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="lens-metric 只读聚合器（view-only）")
    ap.add_argument("--root", default=".", help="仓根（含 openspec/changes/archive）")
    args = ap.parse_args(argv)
    archive = Path(args.root) / "openspec" / "changes" / "archive"
    rows, no_anchor = aggregate(archive)
    print(render_table(rows, no_anchor))
    return 0


if __name__ == "__main__":
    sys.exit(main())
