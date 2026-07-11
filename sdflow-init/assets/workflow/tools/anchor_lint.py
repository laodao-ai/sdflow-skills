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
    except (OSError, UnicodeDecodeError) as e:  # [impl-review-fix] F4
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


def parse_kv_strict(line):
    """整行严格解析 key="value" 对，附带探测重复键（F2：防跨消费者分歧——本脚本 dict 推导末值胜，
    sdflow-retro 若取首会读到不同 hit=/declared=/evidence=，同一报告两处解读不一致）。
    返回 (kv, dup)：kv 与 parse_kv 同口径（末值胜，供 caller 续算用同一确定值，不因重复键崩）；
    dup 为重复出现的键名列表（每命中一次重复出现追加一次），空列表=无重复。本函数不 raise——
    重复键是否算 violation 由 caller 决定（check_hr_tg 用 collect-not-raise，就地转 dict）。"""
    seen, dup = {}, []
    for k, val in _KV.findall(line.strip()):
        if k in seen:
            dup.append(k)
        seen[k] = val
    return seen, dup


def anchor_prefix(line):
    s = line.strip()
    for pref, name in ANCHOR_PREFIXES.items():
        if s.startswith(pref):
            rest = s[len(pref):]                              # [impl-review-fix] F5 token 边界
            if rest == "" or rest[0].isspace() or rest.startswith("-->"):
                return name
    return None


class MetricsError(Exception):
    pass


_ENABLED = re.compile(r'^\s+enabled:\s*(true|false)\s*$')  # metrics 块内合法布尔（仅小写 true/false）


def read_metrics_enabled(root):
    """真四态：①文件不存在→False ②有文件无顶层 metrics: 块→False（消费仓常态放行）
    ③metrics: 块在但块内(至下一顶层键前)解不出合法 enabled: true|false→MetricsError(fail-closed)
    ④解出→bool。块边界=先定位 ^metrics: 再限范围到下一顶层键。"""
    cfg = Path(root) / "openspec" / "config.yaml"
    try:
        lines = cfg.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return False                                        # ①
    except (OSError, UnicodeDecodeError) as e:               # [impl-review-fix] F2 fail-open→fail-closed
        raise MetricsError(f"config 读取失败(非缺失): {e}")
    idx = next((i for i, ln in enumerate(lines) if ln.rstrip() == "metrics:" or ln.startswith("metrics:")), None)
    if idx is None:
        return False                                        # ②
    for ln in lines[idx + 1:]:                              # ③④ 块内至下一顶层键
        if ln.strip() == "" or ln.strip().startswith("#"):   # [impl-review-fix] F3 跳注释/空行
            continue
        if not ln.startswith((" ", "\t")):                    # 下一顶层键（非缩进）
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


HR_TG_REQUIRED_FIELDS = ("hit", "declared")  # mlh-p4 T81：declared= 承「依据模型判定」（adr/0018 输入可见）


# --- trigger-catalog 单一源解析（本地重实现，非 import hr_tg_intersect——仓内 adr/0002「非 import」约定；
#     口径逐字对齐 hr_tg_intersect.py 的 load_hr_tg_subset/load_all_tg_set，两份重实现的一致性
#     由 Task 6 F3 golden 测试机械兜底，此处不引入漂移风险自评） -----------------------------------

class EmitError(Exception):
    """trigger-catalog 单一源缺失/损坏 fail-closed（不静默按空集/WARN 降级放行）。"""
    pass


_TG_STRICT_RE = re.compile(r'^TG-\d+$')       # 逐 token 严格校验
_H12_RE = re.compile(r'^#{1,2}\s')            # level-1/2 标题（段边界；level-3 `### ` 不匹配）
_MEMBER_RE = re.compile(r'^\s*>\s*成员')       # `> 成员：...` 行（fence/引用前缀容忍空白）
_MEMBER_CONTENT_RE = re.compile(r'^\s*>\s*成员[：:]?\s*(.*)$')  # [impl-review-fix] F-A：抽成员行冒号后内容
_H3_SECTION_RE = re.compile(r'^##\s.*触发词目录')      # 「触发词目录」段标题定位（限 level-2）
_TABLE_TG_RE = re.compile(r'^\s*\|\s*(TG-\d+)\s*\|')   # 段内表行首列 TG token；正文游离提及不匹配此形


def _locate_unique_h12(lines, matches_fn, not_found_msg, ambiguous_msg):
    """[impl-review-fix] F-B（同 hr_tg_intersect._locate_unique_h12 口径）：收集全部匹配 level-2
    段标题行，恰好 1 个才返回其索引；0 个 / ≥2 个 → EmitError（fail-closed，MUST NOT 静默取首——
    同名标题会劫持段边界）。"""
    idxs = [i for i, ln in enumerate(lines) if matches_fn(ln)]
    if not idxs:
        raise EmitError(not_found_msg)
    if len(idxs) > 1:
        raise EmitError(ambiguous_msg)
    return idxs[0]


def _parse_member_tokens(content):
    """[impl-review-fix] F-A（同 hr_tg_intersect._parse_member_tokens 口径）：成员行内容
    （`> 成员：` 后半段）→ 严格 TG token 列表。剥外层 `**...**` markdown 粗体包裹后按逗号 split，
    逐 token 须 fullmatch `TG-<数字>`；任一畸形 token 或空 → EmitError（fail-closed，不宽松正规化抽取）。"""
    content = content.strip()
    if content.startswith("**") and content.endswith("**") and len(content) >= 4:
        content = content[2:-2].strip()
    members = []
    for t in (t.strip() for t in content.split(",")):
        if not _TG_STRICT_RE.match(t):
            raise EmitError(f"HR-TG 成员行含非法 TG 记号（须 TG-<数字> 形）: {t!r}")
        members.append(t)
    return members


def load_hr_tg_subset(catalog_path):
    """（同 hr_tg_intersect.load_hr_tg_subset 口径）从 trigger-catalog 的 `## …HR-TG…` 段
    `> 成员：` 行 parse HR-TG 成员集。单一源缺失/不可读/无 HR-TG 段/段内无成员行/成员行无 TG 记号/
    畸形 token/段标题歧义 → EmitError（不静默按空子集放行，不静默取首劫持段边界）。"""
    try:
        text = Path(catalog_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise EmitError(f"trigger-catalog 不可读: {e}")
    lines = list(fence_outside_lines(text))       # [impl-review-fix] F-C：段内围栏行先剔除（复用本文件既有函数）
    start = _locate_unique_h12(
        lines, lambda ln: bool(_H12_RE.match(ln)) and "HR-TG" in ln,
        "trigger-catalog 缺 `## …HR-TG…` 段（单一源损坏）",
        "trigger-catalog 「HR-TG」段标题歧义（同名标题多处匹配，单一源损坏，fail-closed 拒静默取首）")
    members = None
    for ln in lines[start + 1:]:
        if _H12_RE.match(ln):                         # 到下一 level-1/2 标题 = 段结束
            break
        if _MEMBER_RE.match(ln):
            m = _MEMBER_CONTENT_RE.match(ln)
            members = _parse_member_tokens(m.group(1) if m else "")  # [impl-review-fix] F-A：严格抽取
            break
    if members is None:
        raise EmitError("HR-TG 段缺 `> 成员：` 行（单一源损坏）")
    if not members:
        raise EmitError("HR-TG `> 成员：` 行无 TG 成员（单一源损坏，不静默空子集）")
    hr_tg_set = set(members)
    all_tg = load_all_tg_set(catalog_path)            # F7：HR-TG 成员须 ⊆ 触发词目录全集（catalog 内部一致）
    if not hr_tg_set <= all_tg:
        raise EmitError("HR-TG 成员含「触发词目录」全集外 TG（F7 内部不一致，单一源损坏）")
    return hr_tg_set


def load_all_tg_set(catalog_path):
    """（同 hr_tg_intersect.load_all_tg_set 口径）从 trigger-catalog「触发词目录」段的表行
    `| TG-NN | ... |` parse 全 TG 集（M-new，F8 边界钉死）：只取该段内表行首列、逐 token 严格
    fullmatch；正文游离提及（非表行）MUST NOT 纳入，段内围栏示例表行（F-C）MUST NOT 纳入。
    段缺失/段内无表行/段标题歧义（F-B）→ EmitError（单一源损坏 fail-closed，不静默按空集放行）。"""
    try:
        text = Path(catalog_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise EmitError(f"trigger-catalog 不可读: {e}")
    lines = list(fence_outside_lines(text))       # [impl-review-fix] F-C：段内围栏行先剔除（复用本文件既有函数）
    start = _locate_unique_h12(
        lines, lambda ln: bool(_H3_SECTION_RE.match(ln)),
        "trigger-catalog 缺「触发词目录」段（M-new 全集单一源损坏）",
        "trigger-catalog 「触发词目录」段标题歧义（同名标题多处匹配，单一源损坏，fail-closed 拒静默取首）")
    full = set()
    for ln in lines[start + 1:]:
        if _H12_RE.match(ln):                          # 到下一 level-1/2 标题 = 段结束
            break
        mm = _TABLE_TG_RE.match(ln)
        if mm:                                          # [impl-review-fix] 顺带清死代码：捕获组结构本身即 TG-\d+ fullmatch
            full.add(mm.group(1))
    if not full:
        raise EmitError("「触发词目录」段无 `| TG-NN |` 表行（M-new 全集单一源损坏）")
    return full


def _parse_tg_csv(raw):
    """（同 hr_tg_intersect.parse_tg_set 口径，本地重实现——adr/0002 非 import 约定）CSV → token 列表。
    仅原始空串 = 空集；split 后出现空/纯空白 cell（前后/连续逗号）或非法 TG 记号（须 TG-<数字>）
    → EmitError（fail-closed；调用侧 check_hr_tg 用 F9 collect-not-raise 就地转 violation，不外抛）。"""
    if raw == "":
        return []
    tokens = [t.strip() for t in raw.split(",")]
    for t in tokens:
        if t == "":
            raise EmitError(f"CSV 含空 cell（前后/连续逗号），仅空串表空集: {raw!r}")
        if not _TG_STRICT_RE.match(t):
            raise EmitError(f"CSV 含非法 TG 记号（须 TG-<数字>）: {t!r}")
    return tokens


_HR_TG_ANCHOR_FULL_RE = re.compile(r'^<!--\s*sdflow:hr-tg\s+v1(.*)-->\s*$')  # [impl-review-fix] F-D：整行严格边界


def _numeric_key(t):
    return int(t[3:])


def _canonicalize(tokens):
    """去重 + 数值序（brief 接口明令的 canonical 序，emit 侧 render 产出即此形）。"""
    return sorted(set(tokens), key=_numeric_key)


def _check_order_and_dup(v, anchor, field, tokens):
    """[impl-review-fix] F-E：校验 tokens 的原始解析序列（非 set）——重复元素 → `<field>-duplicate`；
    去重后（保留首次出现序）≠ canonical numeric 序 → `<field>-not-canonical-order`。
    重复与乱序独立判定：重复时暂不重复报乱序（去重后天然与自身 canonical 一致时不重复噪声）。"""
    if len(tokens) != len(set(tokens)):
        v.append({"anchor": anchor, "field": field, "kind": f"{field}-duplicate"})
    dedup_preserve_order = list(dict.fromkeys(tokens))
    if dedup_preserve_order != _canonicalize(tokens):
        v.append({"anchor": anchor, "field": field, "kind": f"{field}-not-canonical-order"})


def check_hr_tg(report_text, hr_tg_subset, all_tg_set):
    """校验 fence 外真 hr-tg 锚：F-D 整行须严格匹配 `<!-- sdflow:hr-tg v1 ... -->` 边界（未闭合注释 /
    `-->` 后尾随残留 → malformed-anchor/unterminated-anchor，不继续解析该行 kv）；F2 整行严格解析拒
    重复键（同键出现 ≥2 次，如 hit= 写两遍 → dup-key violation；防跨消费者分歧——本脚本末值胜，
    sdflow-retro 若取首会读到不同字段值，同一报告两处解读不一致）；M1 hit=/declared= 两字段在场；
    F-E hit=/declared= 的原始解析序列须无重复元素、且去重后 = canonical 数值序（乱序/重复元素各自
    独立 violation：hit-not-canonical-order/hit-duplicate、declared-not-canonical-order/declared-duplicate）；
    M2 重算 hit == declared∩HR-TG（数值序逐元素比较，none⟺空交集）；M4 hit≠none(空) ⟹ evidence= 在场
    且 strip 后非空；M-new declared/hit 每 TG ∈ all_tg_set（trigger-catalog 全集，M-new lint 侧）；
    F1 sentinel（declared 空集须 ""、hit 空须 "none"，写反 → violation，仍尽力降级续算不中断其余校验）。
    F-F：declared 侧与 hit 侧解析/校验各自独立 try/except——一侧 CSV 畸形不吞另一侧已可判定的 violation
    （M-new/F-E 校验仅在该侧成功 parse 时进行；M2/M4 需两侧皆成功才比较，任一侧失败则跳过，不臆造）。
    诚实边界（S1）：M2 只堵内部一致性（hit 与 declared∩HR-TG 是否自洽），堵不住「declared 本身
    是否=真命中集」（无确定性信号，语义残余）——一致但错的锚 MUST 通过，MUST NOT 加强为 tamper-proof。
    F9 collect-not-raise：CSV 解析畸形（非 TG-<数字> token / 空 cell）、以及 F2 重复键，均就地转
    violation dict（kind=malformed-tg-csv / dup-key），MUST NOT raise 外抛（护 human + JSON 双输出
    不中断）。"""
    v = []
    for ln in fence_outside_lines(report_text):
        if anchor_prefix(ln) != "hr-tg":
            continue
        anchor = ln.strip()[:80]
        m = _HR_TG_ANCHOR_FULL_RE.match(ln.strip())   # [impl-review-fix] F-D：整行边界严格校验
        if not m:
            kind = "unterminated-anchor" if "-->" not in ln else "malformed-anchor"
            v.append({"anchor": anchor, "field": "anchor", "kind": kind})
            continue
        kv, dup_keys = parse_kv_strict(m.group(1))
        for dk in dup_keys:
            v.append({"anchor": anchor, "field": dk, "kind": "dup-key"})
        for f in HR_TG_REQUIRED_FIELDS:
            if f not in kv:
                v.append({"anchor": anchor, "field": f, "kind": "missing-field"})
        if "hit" not in kv or "declared" not in kv:
            continue
        hit_raw, decl_raw = kv["hit"], kv["declared"]

        # [impl-review-fix] F-F：declared 侧独立 try/except——hit 侧畸形不吞 declared 侧已判定 violation
        declared = None
        try:
            # F1 sentinel：declared 空集须 ""（非 "none"）；"none" 字面不可解析为 CSV，
            # 违规照记但降级按空集续算，避免同根因被误记成 malformed-tg-csv 掩盖真实 kind。
            if decl_raw == "none":
                v.append({"anchor": anchor, "field": "declared", "kind": "declared-none-literal"})
                declared = []
            else:
                declared = _parse_tg_csv(decl_raw)
        except EmitError:
            v.append({"anchor": anchor, "field": "declared", "kind": "malformed-tg-csv"})
        if declared is not None:
            for t in set(declared):
                if t not in all_tg_set:                                    # M-new
                    v.append({"anchor": anchor, "field": "declared", "kind": "tg-not-in-catalog"})
            _check_order_and_dup(v, anchor, "declared", declared)          # F-E

        # [impl-review-fix] F-F：hit 侧独立 try/except——declared 侧畸形不吞 hit 侧已判定 violation
        actual = None
        try:
            # F1 sentinel：hit 空须 "none"（非 ""）；"" 本身是合法空 CSV，可续算，仅额外记违规。
            if hit_raw == "":
                v.append({"anchor": anchor, "field": "hit", "kind": "hit-empty-not-none"})
                actual = []
            elif hit_raw == "none":
                actual = []
            else:
                actual = _parse_tg_csv(hit_raw)
        except EmitError:
            v.append({"anchor": anchor, "field": "hit", "kind": "malformed-tg-csv"})
        if actual is not None:
            for t in set(actual):
                if t not in all_tg_set:                                    # M-new
                    v.append({"anchor": anchor, "field": "hit", "kind": "tg-not-in-catalog"})
            _check_order_and_dup(v, anchor, "hit", actual)                 # F-E

        if declared is not None and actual is not None:
            # M2：重算 expect_hits = declared ∩ HR-TG，与锚里 hit= 逐元素同序（数值序）比较
            expect_hits = sorted({t for t in declared if t in hr_tg_subset}, key=_numeric_key)
            actual_sorted = sorted(set(actual), key=_numeric_key)
            if actual_sorted != expect_hits:
                v.append({"anchor": anchor, "field": "hit", "kind": "hit-declared-mismatch"})
            # M4：hit≠none(空) ⟹ evidence= 在场且 strip 后非空（按锚上实际 hit 声明门控，非按 expect_hits——
            # 即便 M2 判 mismatch，只要锚声明了非空 hit，仍要求 evidence，两者独立校验）
            if actual_sorted and kv.get("evidence", "").strip() == "":
                v.append({"anchor": anchor, "field": "evidence", "kind": "evidence-missing"})
    return v


_NONNEG_INT = re.compile(r'^\d+$')


def check_lens_metric(report_text, cli_layer, enums):
    """校验 fence 外真 lens-metric 锚的字段完整性/枚举归属/layer==--layer/sev 子格式/五计数 int≥0。
    `site` 字段 MUST NOT 校验（契约 CF-补2，任意值合法）。数值一致性（findings vs 实收数）不校验（脚本不兜）。"""
    v = []
    for ln in fence_outside_lines(report_text):
        if anchor_prefix(ln) != "lens-metric":
            continue
        kv = parse_kv(ln)
        for f in REQUIRED_FIELDS:
            if f not in kv:
                v.append({"anchor": ln.strip()[:80], "field": f, "kind": "missing-field"})
        if "layer" in kv and kv["layer"] not in enums["layer"]:  # [impl-review-fix] F1 存在性判断，空串落违规
            v.append({"anchor": ln.strip()[:80], "field": "layer", "kind": "out-of-enum"})
        if "layer" in kv and kv["layer"] != cli_layer:  # [impl-review-fix] F1
            v.append({"anchor": ln.strip()[:80], "field": "layer", "kind": "layer-ne-cli"})
        if "lens" in kv and kv["lens"] not in enums["lens"]:  # [impl-review-fix] F1
            v.append({"anchor": ln.strip()[:80], "field": "lens", "kind": "out-of-enum"})
        if "runner" in kv and kv["runner"] not in enums["runner"]:  # [impl-review-fix] F1
            v.append({"anchor": ln.strip()[:80], "field": "runner", "kind": "out-of-enum"})
        if "sev" in kv and not enums["sev_re"].match(kv["sev"]):  # [impl-review-fix] F1
            v.append({"anchor": ln.strip()[:80], "field": "sev", "kind": "bad-subformat"})
        for cf in COUNT_FIELDS:
            if cf in kv and not _NONNEG_INT.match(kv[cf]):
                v.append({"anchor": ln.strip()[:80], "field": cf, "kind": "not-nonneg-int"})
    return v


def main(argv=None):
    ap = argparse.ArgumentParser(description="评审报告锚自检门（确定性·fail-closed）")
    ap.add_argument("--report", required=True)
    ap.add_argument("--layer", required=True, choices=["spec-review", "code-review"])
    ap.add_argument("--trigger-catalog", required=True,
                    help="HR-TG 单一源（trigger-catalog.md），M2/M-new 前提；必需，缺传→fail-closed，MUST NOT WARN 降级放行")
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    # 1) 读报告（fail-closed）
    try:
        report_text = Path(args.report).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:  # [impl-review-fix] F4
        print(f"[anchor_lint] ERROR 读不到报告: {args.report}: {e}", file=sys.stderr)
        print(json.dumps({"result": "ERROR", "reason": "report-unreadable"}, ensure_ascii=False))
        return EXIT_ERROR
    # 2) 读枚举 + metrics（fail-closed）
    try:
        enums = load_enums()
    except EnumsError as e:
        print(f"[anchor_lint] ERROR 契约枚举: {e}", file=sys.stderr)
        print(json.dumps({"result": "ERROR", "reason": "enums"}, ensure_ascii=False))
        return EXIT_ERROR
    try:
        metrics_on = read_metrics_enabled(args.root)
    except MetricsError as e:
        print(f"[anchor_lint] ERROR config metrics 块坏: {e}", file=sys.stderr)
        print(json.dumps({"result": "ERROR", "reason": "metrics-block-bad"}, ensure_ascii=False))
        return EXIT_ERROR
    # 3) 读 trigger-catalog 单一源（fail-closed，本地重实现——见文件上方注释）
    try:
        hr_tg_subset = load_hr_tg_subset(args.trigger_catalog)
        all_tg_set = load_all_tg_set(args.trigger_catalog)
    except EmitError as e:
        print(f"[anchor_lint] ERROR trigger-catalog: {e}", file=sys.stderr)
        print(json.dumps({"result": "ERROR", "reason": "catalog-bad"}, ensure_ascii=False))
        return EXIT_ERROR
    # 4) 校验
    violations = check_existence(report_text, args.layer, metrics_on)
    violations += check_hr_tg(report_text, hr_tg_subset, all_tg_set)  # hr-tg 恒必有锚，字段校验不受 metrics 门控
    if metrics_on:
        violations += check_lens_metric(report_text, args.layer, enums)
    if violations:
        for x in violations:
            print(f"[anchor_lint] VIOLATION {x}", file=sys.stderr)
        print(json.dumps({"result": "VIOLATION", "violations": violations}, ensure_ascii=False))
        return EXIT_VIOLATION
    print("[anchor_lint] CLEAN", file=sys.stderr)
    print(json.dumps({"result": "CLEAN"}, ensure_ascii=False))
    return EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main())
