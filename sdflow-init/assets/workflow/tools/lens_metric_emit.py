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


def fold_hit(hit, enums, fold_map):
    """一个 hit → 行键 (lens, runner, site)。恒等 pass-through；未知 raw fail-closed（不塞 broad）。"""
    if not isinstance(hit, dict) or "raw" not in hit:
        raise EmitError(f"hit 缺 raw: {hit!r}")
    raw = hit["raw"]
    if raw in enums["lens"]:
        canon = raw                                  # 恒等 pass-through（ADR-7）
    elif raw in fold_map:
        canon = fold_map[raw]
    else:
        raise EmitError(f"未知 raw 镜名无折叠映射: {raw}")  # SR-E 不静默塞 broad
    if canon == "outside-voice":
        runner, site = hit.get("runner"), hit.get("site")
        if runner is None or site is None:
            raise EmitError(f"outside-voice hit 缺 runner/site: {hit!r}")
    else:
        runner, site = "claude", "—"
    if runner not in enums["runner"]:
        raise EmitError(f"runner 越域: {runner}")
    if isinstance(site, str) and _SITE_BAD.search(site):
        raise EmitError(f"site 含非法字符（注入）: {site!r}")  # C7
    return (canon, runner, site)


def reduce(roster, findings, layer, enums, fold_map):
    """全校验通过才产锚（all-or-nothing）：返回锚行 list；任一坏 → EmitError。"""
    if layer not in enums["layer"]:
        raise EmitError(f"--layer 越域: {layer}")
    # 1) roster → 行键（去重 + 越域 + site 消毒 + MIN_LENS_ROWS）
    roster_keys, seen = [], set()
    for it in roster:
        if not isinstance(it, dict) or not {"lens","runner","site"} <= set(it):
            raise EmitError(f"roster 项缺字段: {it!r}")
        if it["lens"] not in enums["lens"]:
            raise EmitError(f"roster lens 越域: {it['lens']}")
        if it["runner"] not in enums["runner"]:
            raise EmitError(f"roster runner 越域: {it['runner']}")
        if _SITE_BAD.search(it["site"]):
            raise EmitError(f"roster site 注入: {it['site']!r}")
        key = (it["lens"], it["runner"], it["site"])
        if key in seen:
            raise EmitError(f"roster 重复行键: {key}")
        seen.add(key); roster_keys.append(key)
    roster_lenses = {k[0] for k in roster_keys}
    for need in MANDATORY_LENS:                          # 被调即视 metrics-on
        if need not in roster_lenses:
            raise EmitError(f"roster 缺强制行 lens={need}（MIN_LENS_ROWS）")
    # 2) 累加器
    counts = {k: {"findings":0,"采纳":0,"裁掉":0,"defer":0,"独立":0,
                  "sev":{lv:0 for lv in enums["sev_levels"]}} for k in roster_keys}
    # 3) 逐 finding
    for fd in findings:
        if not isinstance(fd, dict) or "hits" not in fd or "verdict" not in fd:
            raise EmitError(f"finding 缺 hits/verdict: {fd!r}")
        hits = fd["hits"]
        if not isinstance(hits, list) or not hits:
            raise EmitError(f"finding hits 空/非数组: {fd!r}")           # C11
        verdict = fd["verdict"]
        if verdict not in VERDICTS:
            raise EmitError(f"verdict 越域: {verdict}")
        sev = fd.get("sev")
        if verdict == "采纳" and (not sev or sev not in enums["sev_levels"]):
            raise EmitError(f"采纳 finding 缺/非法 sev: {fd!r}")         # C12
        keyset = {fold_hit(h, enums, fold_map) for h in hits}
        for k in keyset:
            if k not in counts:
                raise EmitError(f"finding 命中行 {k} 不在 roster")       # C4 反方向
        for k in keyset:
            counts[k]["findings"] += 1
            counts[k][verdict] += 1
            if verdict == "采纳":
                counts[k]["sev"][sev] += 1
        if len(keyset) == 1 and verdict == "采纳":
            counts[next(iter(keyset))]["独立"] += 1
    # 4) sev 不变量：Σsev == 采纳
    for k, c in counts.items():
        if sum(c["sev"].values()) != c["采纳"]:
            raise EmitError(f"sev rollup 不变量破: {k} Σsev≠采纳")
    # 5) emit（确定序 = 行键排序）
    lines = []
    for k in sorted(roster_keys):
        c = counts[k]
        sev_str = "/".join(f"{lv}{c['sev'][lv]}" for lv in enums["sev_levels"])
        lines.append(
            f'<!-- sdflow:lens-metric v1 layer="{layer}" lens="{k[0]}" runner="{k[1]}" '
            f'site="{k[2]}" findings="{c["findings"]}" 采纳="{c["采纳"]}" 裁掉="{c["裁掉"]}" '
            f'defer="{c["defer"]}" 独立="{c["独立"]}" sev="{sev_str}" -->'
        )
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description="lens-metric 锚 emitter（确定性·fail-closed·门控外置）")
    ap.add_argument("--layer", required=True, choices=["spec-review", "code-review"])
    ap.add_argument("--input", required=True)
    ap.add_argument("--contract", default=None)
    args = ap.parse_args(argv)
    contract = args.contract or str(Path(__file__).resolve().parent.parent / "lens-metric-contract.md")
    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        enums = load_enums(contract)
        fold_map = load_fold(contract, enums)
        if not isinstance(data, dict) or "roster" not in data or "findings" not in data:
            raise EmitError("输入缺 roster/findings 顶层键")
        if not isinstance(data["roster"], list) or not isinstance(data["findings"], list):
            raise EmitError("roster/findings 必须是数组")
        lines = reduce(data["roster"], data["findings"], args.layer, enums, fold_map)  # all-or-nothing
    except (EmitError, json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
        print(f"[lens_metric_emit] FAIL: {e}", file=sys.stderr)
        return EXIT_FAIL
    print("\n".join(lines))                                # 仅全校验过才输出（无部分锚）
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
