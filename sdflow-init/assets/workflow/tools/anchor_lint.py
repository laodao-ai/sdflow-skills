#!/usr/bin/env python3
"""anchor_lint — 评审报告锚自检确定性门（mlh-p2-anchor-lint）。
盘面即状态：只读报告，退出码承载判定，双输出（human + JSON）。
    0=CLEAN  1=VIOLATION  2=ERROR(fail-closed)
枚举单一源 = 契约 lens-metric-contract.md 的 `lens-metric-enums` 机读块（同 workflow bundle）。
fence-aware 行级核脚本内重实现（禁跨 skill import lens_metric_aggregate/ship_gate——消费仓无 sdflow-retro）。"""
import argparse, json, re, sys
from pathlib import Path

EXIT_CLEAN, EXIT_VIOLATION, EXIT_ERROR = 0, 1, 2

ANCHOR_PREFIXES = {
    "<!-- sdflow:outside-voice v1": "outside-voice",
    "<!-- sdflow:hr-tg v1": "hr-tg",
    "<!-- sdflow:step1-broad-review v1": "step1-broad-review",
    "<!-- sdflow:lens-metric v1": "lens-metric",
}
_KV = re.compile(r'([^\s=]+)="([^"]*)"')                    # 受限 kv：key="value"
_FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})')               # CommonMark fence：0-3 空格 + ≥3 marker
_ENUM_BLOCK = re.compile(r'^ {0,3}(`{3,}|~{3,})lens-metric-enums\s*$')  # 机读块开启行

COUNT_FIELDS = ("findings", "采纳", "裁掉", "defer", "独立")
REQUIRED_FIELDS = ("layer", "lens", "runner", "findings", "采纳", "裁掉", "defer", "独立", "sev")


class EnumsError(Exception):
    pass


def _default_contract():
    return Path(__file__).resolve().parent.parent / "lens-metric-contract.md"


def load_enums(contract_path=None):
    """从契约 `lens-metric-enums` fenced 块读 layer/lens/runner 枚举 + sev-format 正则。
    块缺失/空/契约不可读 → EnumsError（调用侧 fail-closed，绝不回落硬编码）。"""
    p = Path(contract_path) if contract_path else _default_contract()
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        raise EnumsError(f"契约不可读: {p}: {e}")
    lines = text.splitlines()
    body, in_block, fence_char, fence_len = [], False, None, 0
    for ln in lines:
        if not in_block:
            m = _ENUM_BLOCK.match(ln)
            if m:
                in_block = True; fence_char = m.group(1)[0]; fence_len = len(m.group(1))
            continue
        c = _FENCE.match(ln)
        if c and c.group(1)[0] == fence_char and len(c.group(1)) >= fence_len and ln[c.end():].strip() == "":
            break                                           # 闭合
        body.append(ln)
    if not in_block:
        raise EnumsError(f"契约缺 lens-metric-enums 机读块: {p}")
    kv = {}
    for ln in body:
        if ":" in ln:
            k, v = ln.split(":", 1)
            kv[k.strip()] = v.strip()
    layer = {x.strip() for x in kv.get("layer", "").split(",") if x.strip()}
    lens = {x.strip() for x in kv.get("lens", "").split(",") if x.strip()}
    runner = {x.strip() for x in kv.get("runner", "").split(",") if x.strip()}
    sev_fmt = kv.get("sev-format", "").strip()              # 致N/高N/中N/低N
    if not (layer and lens and runner and sev_fmt):
        raise EnumsError(f"lens-metric-enums 块解析空/缺项: {p}")
    # 由 sev-format 模板生成正则：N → \d+，其余字面
    sev_re = re.compile("^" + re.escape(sev_fmt).replace("N", r"\d+") + "$")
    return {"layer": layer, "lens": lens, "runner": runner, "sev_re": sev_re}


def fence_outside_lines(text):
    """产出非 fenced-block 行（CommonMark：0-3 空格缩进 + ≥3 同字符 marker 开合、闭合行 marker 后仅空白）。"""
    fence = None
    for ln in text.splitlines():
        m = _FENCE.match(ln)
        if fence is None:
            if m:
                fence = (m.group(1)[0], len(m.group(1))); continue
            yield ln
        else:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1] and ln[m.end():].strip() == "":
                fence = None
            continue


def parse_kv(line):
    return {k: v for k, v in _KV.findall(line.strip())}


def anchor_prefix(line):
    s = line.strip()
    for pref, name in ANCHOR_PREFIXES.items():
        if s.startswith(pref):
            return name
    return None


class MetricsError(Exception):
    pass


_TOP_KEY = re.compile(r'^\S')                              # 顶层键：行首非空白
_ENABLED = re.compile(r'^\s+enabled:\s*(true|false)\s*$')  # metrics 块内合法布尔（仅小写 true/false）


def read_metrics_enabled(root):
    """真四态：①文件不存在→False ②有文件无顶层 metrics: 块→False（消费仓常态放行）
    ③metrics: 块在但块内(至下一顶层键前)解不出合法 enabled: true|false→MetricsError(fail-closed)
    ④解出→bool。块边界=先定位 ^metrics: 再限范围到下一顶层键。"""
    cfg = Path(root) / "openspec" / "config.yaml"
    try:
        lines = cfg.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False                                        # ①
    idx = next((i for i, ln in enumerate(lines) if ln.rstrip() == "metrics:" or ln.startswith("metrics:")), None)
    if idx is None:
        return False                                        # ②
    for ln in lines[idx + 1:]:                              # ③④ 块内至下一顶层键
        if _TOP_KEY.match(ln) and not ln.startswith(" "):
            break
        m = _ENABLED.match(ln)
        if m:
            return m.group(1) == "true"
    raise MetricsError("metrics: 块存在但解不出合法 enabled: true|false")


MANDATORY = ("outside-voice", "hr-tg", "step1-broad-review")
MIN_LENS_ROWS = ("broad", "outside-voice")


def check_existence(report_text, layer, metrics_on):
    outside = list(fence_outside_lines(report_text))
    present, lens_rows = set(), set()
    for ln in outside:
        name = anchor_prefix(ln)
        if name:
            present.add(name)
            if name == "lens-metric":
                lens_rows.add(parse_kv(ln).get("lens", ""))
    v = []
    for fam in MANDATORY:
        if fam not in present:
            v.append({"kind": "missing-anchor", "detail": fam})
    if metrics_on:
        if "lens-metric" not in present:
            v.append({"kind": "missing-anchor", "detail": "lens-metric (metrics.enabled)"})
        for need in MIN_LENS_ROWS:
            if need not in lens_rows:
                v.append({"kind": "missing-lens-row", "detail": need})
    return v
