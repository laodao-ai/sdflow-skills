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


_OV_RUNNER_DOMAIN = frozenset({"claude", "codex", "none"})   # add-codex-host-support：outside-voice **行**(roster row) runner 域收紧
# （契约「跨模型性」段：outside-voice 锚 runner 恒 ∈{claude,codex,none}，不取 unknown——unknown 只属非-ov 普通镜行）
# roster 行的 "none" 表示"该轮无执行"（合法、必伴 findings=0）——但 hit 代表**实际报出的 finding**，只有 voice
# 真跑过才可能存在 hit，故 hit 级 runner 域 MUST NOT 含 "none"（复评 Critical：两处语义不同，不可共用同一常量，
# 否则 runner="none" 的 hit 会被接受、把零执行行的 findings/采纳/独立 顶到非零，破 spec「runner="none" 行恒全零」不变量）。
_OV_HIT_RUNNER_DOMAIN = frozenset({"claude", "codex"})        # add-codex-host-support fix：hit 级收紧，排除 "none"


class EmitError(Exception):
    pass


def _read_block_pairs(text, info_string):
    """fence-aware 读 fenced 块内 `k: v` 行为 (k,v) 对列表（重实现同 anchor_lint 口径，不 import）。"""
    open_re = re.compile(r'^ {0,3}(`{3,}|~{3,})' + re.escape(info_string) + r'\s*$')
    body, in_block, closed, fc, fl = [], False, False, None, 0
    for ln in text.splitlines():
        if not in_block:
            m = open_re.match(ln)
            if m:
                in_block = True; fc = m.group(1)[0]; fl = len(m.group(1))
            continue
        c = _FENCE.match(ln)
        if c and c.group(1)[0] == fc and len(c.group(1)) >= fl and ln[c.end():].strip() == "":
            closed = True
            break
        body.append(ln)
    if not in_block:
        raise EmitError(f"契约缺 {info_string} 机读块")
    if not closed:
        raise EmitError(f"{info_string} 块未闭合")
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
    layer, lens, host, runner = _set("layer"), _set("lens"), _set("host"), _set("runner")  # add-codex-host-support
    sev_fmt = kv.get("sev-format", "").strip()
    if not (layer and lens and host and runner and sev_fmt):
        raise EmitError("lens-metric-enums 块解析空/缺项")
    sev_re = re.compile("^" + re.escape(sev_fmt).replace("N", r"\d+") + "$")
    sev_levels = tuple(re.findall(r'([^N/]+)N', sev_fmt))   # 致N/高N/中N/低N → ('致','高','中','低')
    return {"layer": layer, "lens": lens, "host": host, "runner": runner,
            "sev_re": sev_re, "sev_levels": sev_levels}


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


def fold_hit(hit, host, enums, fold_map):
    """一个 hit → 行键 (lens, host, runner, site)〔add-codex-host-support：行键升维插入 host〕。
    恒等 pass-through；未知 raw fail-closed（不塞 broad）。
    非 outside-voice：runner 取当前 --host（主审自己的机队；host="unknown" 时 runner 同为 "unknown"，
    契约「unknown 仅合法于非-ov 普通镜行且 host=unknown」）；
    outside-voice：runner 显式来自 hit，域收紧至 {claude,codex}（既不取 unknown——矩阵约束，契约「跨模型性」段；
    也不取 none——hit 蕴含 voice 真跑过，"none"=无执行只对 roster 行合法，复评 Critical fix）。"""
    if not isinstance(hit, dict) or "raw" not in hit or not isinstance(hit["raw"], str):
        raise EmitError(f"hit 缺 raw/raw 非字符串: {hit!r}")
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
        if not isinstance(runner, str) or not isinstance(site, str):
            raise EmitError(f"outside-voice hit runner/site 非字符串: {hit!r}")
        if runner not in _OV_HIT_RUNNER_DOMAIN:
            raise EmitError(
                f"outside-voice hit runner 越域(须∈{sorted(_OV_HIT_RUNNER_DOMAIN)}): {runner!r}"
                f"——hit 不该 runner=\"none\"，hit 蕴含该 voice 真跑过（\"none\"=无执行只对 roster 行合法）"
            )
    else:
        runner, site = host, "—"                     # add-codex-host-support：非-ov runner 取当前 host（GC-8）
    if runner not in enums["runner"]:
        raise EmitError(f"runner 越域: {runner}")
    if _SITE_BAD.search(site):
        raise EmitError(f"site 含非法字符（注入）: {site!r}")  # C7 先类型后注入：非 str site 已在上方拦截，此处 site 恒为 str
    return (canon, host, runner, site)


def reduce(roster, findings, layer, host, enums, fold_map):
    """全校验通过才产锚（all-or-nothing）：返回锚行 list；任一坏 → EmitError。
    add-codex-host-support：新增 host 单一源参数（本轮所有行共用），行键升维为 (lens,host,runner,site)。"""
    if layer not in enums["layer"]:
        raise EmitError(f"--layer 越域: {layer}")
    if host not in enums["host"]:
        raise EmitError(f"--host 越域: {host}")
    # 1) roster → 行键（去重 + 越域 + site 消毒 + MIN_LENS_ROWS）
    roster_keys, seen = [], set()
    for it in roster:
        if not isinstance(it, dict) or not {"lens","runner","site"} <= set(it):
            raise EmitError(f"roster 项缺字段: {it!r}")
        if not all(isinstance(it[k], str) for k in ("lens","runner","site")):
            raise EmitError(f"roster 字段类型非字符串: {it!r}")
        if it["lens"] not in enums["lens"]:
            raise EmitError(f"roster lens 越域: {it['lens']}")
        if it["runner"] not in enums["runner"]:
            raise EmitError(f"roster runner 越域: {it['runner']}")
        if _SITE_BAD.search(it["site"]):
            raise EmitError(f"roster site 注入: {it['site']!r}")
        if it["lens"] != "outside-voice":
            if it["runner"] != host or it["site"] != "—":            # Fix B：防幽灵行击穿强制行
                raise EmitError(f"非 outside-voice 行键必须 runner==--host({host!r}) 且 site=—: {it!r}")
        elif it["runner"] not in _OV_RUNNER_DOMAIN:
            raise EmitError(f"outside-voice 行键 runner 越域(须∈{sorted(_OV_RUNNER_DOMAIN)}): {it!r}")
        key = (it["lens"], host, it["runner"], it["site"])
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
        if sev is not None and sev not in enums["sev_levels"]:
            raise EmitError(f"finding sev 非法: {fd!r}")                # Fix A：任何 verdict 的非空 sev 都须合法
        if verdict == "采纳" and not sev:
            raise EmitError(f"采纳 finding 缺 sev: {fd!r}")             # C12
        keyset = {fold_hit(h, host, enums, fold_map) for h in hits}
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
    # 4) sev 不变量：Σsev == 采纳；runner="none" 行恒零执行不变量
    # 同函数内自防御（防未来重构打破锁步），当前结构下均不可达（fold_hit 已 fail-closed 拦 hit runner=none）、
    # 非跨模块校验——防御纵深：若未来 fold_hit 收紧被误改回，此处仍兜底拦住 runner=none 行累积非零计数（复评 Critical fix）。
    for k, c in counts.items():
        if sum(c["sev"].values()) != c["采纳"]:
            raise EmitError(f"sev rollup 不变量破: {k} Σsev≠采纳")
        if k[2] == "none" and c["findings"] != 0:
            raise EmitError(f"runner=\"none\" 行不变量破（该行本应零执行 findings=0）: {k} findings={c['findings']}")
    # 5) emit（确定序 = 行键排序）
    lines = []
    for k in sorted(roster_keys):
        c = counts[k]
        sev_str = "/".join(f"{lv}{c['sev'][lv]}" for lv in enums["sev_levels"])
        lines.append(
            f'<!-- sdflow:lens-metric v1 layer="{layer}" lens="{k[0]}" host="{k[1]}" runner="{k[2]}" '
            f'site="{k[3]}" findings="{c["findings"]}" 采纳="{c["采纳"]}" 裁掉="{c["裁掉"]}" '
            f'defer="{c["defer"]}" 独立="{c["独立"]}" sev="{sev_str}" -->'
        )
    return lines


def main(argv=None):
    # add-codex-host-support：allow_abbrev=False——否则 argparse 前缀缩写匹配会把 --laye 误吞成 --layer，
    # D12「if extras: fail-closed」拒多余/拼错参数就失去意义（缩写匹配比"未识别参数"更隐蔽地静默吞错）。
    ap = argparse.ArgumentParser(
        description="lens-metric 锚 emitter（确定性·fail-closed·门控外置）", allow_abbrev=False)
    ap.add_argument("--layer", required=True, choices=["spec-review", "code-review"])
    ap.add_argument("--input", required=True)
    ap.add_argument("--contract", default=None)
    # --host 故意不设 required=True/choices=——required/choices 越域时 argparse 自己 error()→exit(2) 崩栈，
    # 不是"可读错误消息报明原因"的受控降级（D4）。缺失/越域改在下方 try 内显式校验，走同一条 EmitError 路径。
    ap.add_argument("--host", default=None)
    args, extras = ap.parse_known_args(argv)
    if extras:                                              # D12：拒多余/拼错参数，MUST NOT 静默吞
        print(f"[lens_metric_emit] FAIL: 无法识别的参数（拼写错误或多余）: {extras}", file=sys.stderr)
        return EXIT_FAIL
    contract = args.contract or str(Path(__file__).resolve().parent.parent / "lens-metric-contract.md")
    try:
        # 复评 Minor fix：--host 校验须先于读 --input（更根本的缺失 MUST 先报，避免用户误把注意力
        # 花在一个"文件坏了"的次要错误上，而忽略了真正缺的 --host）。
        if args.host is None:                               # D4：缺 --host 受控 fail-closed，MUST NOT 默认填 claude
            raise EmitError(
                "缺少 --host 参数（须显式传 claude|codex|unknown 之一；"
                "无默认值——静默默认会把 Codex 宿主的轮次伪装成 Claude 宿主）")
        enums = load_enums(contract)
        if args.host not in enums["host"]:                  # D4：越域（含已废弃 claude-fallback）fail-closed
            raise EmitError(f"--host 取值越域: {args.host!r}（须 ∈ {sorted(enums['host'])}）")
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        fold_map = load_fold(contract, enums)
        if not isinstance(data, dict) or "roster" not in data or "findings" not in data:
            raise EmitError("输入缺 roster/findings 顶层键")
        if not isinstance(data["roster"], list) or not isinstance(data["findings"], list):
            raise EmitError("roster/findings 必须是数组")
        lines = reduce(data["roster"], data["findings"], args.layer, args.host, enums, fold_map)  # all-or-nothing
    except (EmitError, json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
        print(f"[lens_metric_emit] FAIL: {e}", file=sys.stderr)
        return EXIT_FAIL
    print("\n".join(lines))                                # 仅全校验过才输出（无部分锚）
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
