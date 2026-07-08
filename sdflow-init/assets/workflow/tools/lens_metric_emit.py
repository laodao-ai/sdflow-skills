#!/usr/bin/env python3
"""lens_metric_emit — 确定性 lens-metric 锚 emitter（mlh-p4）。
吃 行键 roster + 结构化 findings，按契约折叠/归属/独立/sev-rollup 归约出合规锚行。
门控外置（不读 config）；坏输入 fail-closed all-or-nothing；禁 import yaml/aggregator/ship_gate/anchor_lint。"""
import argparse, json, re, sys
from pathlib import Path

EXIT_OK, EXIT_FAIL = 0, 1
VERDICTS = ("采纳", "裁掉", "defer")            # 本地常量豁免（ADR-11：输入独有、不写进锚、不与 anchor_lint 共享）
MANDATORY_LENS = ("broad", "outside-voice")     # 一致性测试守 == anchor_lint.MIN_LENS_ROWS（分叉①=B）
_SITE_BAD = re.compile(r'["\n\r]|-->|=')        # site 注入字符（C7）
_FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})')


class EmitError(Exception):
    pass


def _read_block_pairs(text, info_string):
    """fence-aware 读 fenced 块内 `k: v` 行为 (k,v) 对列表（重实现同 anchor_lint 口径，不 import）。"""
    open_re = re.compile(r'^ {0,3}(`{3,}|~{3,})' + re.escape(info_string) + r'\s*$')
    body, in_block, fc, fl = [], False, None, 0
    for ln in text.splitlines():
        if not in_block:
            m = open_re.match(ln)
            if m:
                in_block = True; fc = m.group(1)[0]; fl = len(m.group(1))
            continue
        c = _FENCE.match(ln)
        if c and c.group(1)[0] == fc and len(c.group(1)) >= fl and ln[c.end():].strip() == "":
            break
        body.append(ln)
    if not in_block:
        raise EmitError(f"契约缺 {info_string} 机读块")
    pairs = []
    for ln in body:
        if ":" in ln:
            k, v = ln.split(":", 1)
            pairs.append((k.strip(), v.strip()))
    return pairs


def load_enums(contract_path):
    try:
        text = Path(contract_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise EmitError(f"契约不可读: {e}")
    kv = dict(_read_block_pairs(text, "lens-metric-enums"))
    def _set(k): return {x.strip() for x in kv.get(k, "").split(",") if x.strip()}
    layer, lens, runner = _set("layer"), _set("lens"), _set("runner")
    sev_fmt = kv.get("sev-format", "").strip()
    if not (layer and lens and runner and sev_fmt):
        raise EmitError("lens-metric-enums 块解析空/缺项")
    sev_re = re.compile("^" + re.escape(sev_fmt).replace("N", r"\d+") + "$")
    sev_levels = tuple(re.findall(r'([^N/]+)N', sev_fmt))   # 致N/高N/中N/低N → ('致','高','中','低')
    return {"layer": layer, "lens": lens, "runner": runner, "sev_re": sev_re, "sev_levels": sev_levels}


def load_fold(contract_path, enums):
    text = Path(contract_path).read_text(encoding="utf-8")
    fold_map = {}
    for raw, canon in _read_block_pairs(text, "lens-metric-fold"):
        if raw in fold_map:
            raise EmitError(f"lens-metric-fold 重复 raw 键: {raw}")
        if canon not in enums["lens"]:
            raise EmitError(f"lens-metric-fold codomain 越 lens-enum: {raw}→{canon}")  # C3 自校验
        fold_map[raw] = canon
    return fold_map
