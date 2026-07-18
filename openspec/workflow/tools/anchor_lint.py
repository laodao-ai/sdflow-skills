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
    "<!-- sdflow:fanout-capability v1": "fanout-capability",   # add-codex-host-support：会话级探针锚，always-on 一致性 lint 判据源
    "<!-- sdflow:declared-sites v1": "declared-sites",         # async-outside-voice：本层「应有锚站点集」声明，per-site 完整性核判据源
}
_KV = re.compile(r'([^\s=]+)="([^"]*)"')                    # 受限 kv：key="value"
_FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})')               # CommonMark fence：0-3 空格 + ≥3 marker
_ENUM_BLOCK = re.compile(r'^ {0,3}(`{3,}|~{3,})lens-metric-enums\s*$')  # 机读块开启行

COUNT_FIELDS = ("findings", "采纳", "裁掉", "defer", "独立")
# add-codex-host-support：REQUIRED_FIELDS 插入 host（v2 锚行键升维；缺 host → 无从区分自审 vs 跨模型轮次）。
# site 仍不入必检（CF-补2：任意值合法、不纳越域自检）。
REQUIRED_FIELDS = ("layer", "lens", "host", "runner", "findings", "采纳", "裁掉", "defer", "独立", "sev")


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
    host = {x.strip() for x in kv.get("host", "").split(",") if x.strip()}          # add-codex-host-support
    runner = {x.strip() for x in kv.get("runner", "").split(",") if x.strip()}
    reason_code = {x.strip() for x in kv.get("reason_code", "").split(",") if x.strip()}  # add-codex-host-support
    sev_fmt = kv.get("sev-format", "").strip()              # 致N/高N/中N/低N
    if not (layer and lens and host and runner and reason_code and sev_fmt):
        raise EnumsError(f"lens-metric-enums 块解析空/缺项: {p}")
    # 由 sev-format 模板生成正则：N → \d+，其余字面
    sev_re = re.compile("^" + re.escape(sev_fmt).replace("N", r"\d+") + "$")
    return {"layer": layer, "lens": lens, "host": host, "runner": runner,
            "reason_code": reason_code, "sev_re": sev_re}


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


# =========================================================================================
# add-codex-host-support：合法组合矩阵（🔴 自审红线单一源）+ fan-out 一致性 lint（读 mirrors=）
# 两者 always-on、各自独立成函数、MUST NOT 接受 metrics_on 参数（照 check_hr_tg 先例，D11）——读真实性
# 信号非价值度量，与 metrics.enabled 解耦。枚举域从契约机读块读（load_enums），关系式判定逻辑本地重实现
# （GC-2：平铺 enums 块装不下 runner≠host/findings=0 等关系式谓词；outside_voice_guard 各自重实现，全笛卡尔
# golden 守一致，见 tasks 2.3/4.5）。**MUST NOT import/调 resolve-models.sh（ADR-1：anchor_lint 不判宿主，
# 只校验锚行自身内部一致性——host/runner/reason_code 都写在锚行里）。**
# =========================================================================================

OUTSIDE_VOICE_REQUIRED_FIELDS = ("host", "runner", "reason_code")  # D1：outside-voice 锚新增 KV 解析，reason_code 该锚必填
_DOWNGRADE_CODES = frozenset({"not-installed", "preflight-error", "timeout", "exec-error"})  # D2 同族 fallback 降级码集（钉死，含 preflight-error）
_NOEXEC_KNOWN_CODES = frozenset({"secret-hit", "fallback-unavailable"})                      # 无执行 · host∈{claude,codex}
_DUOS = frozenset({"claude", "codex"})                                                        # 两个真机队（谈跨模型的前提）


def classify_combo(host, runner, reason_code, findings):
    """把 outside-voice 锚的 (host, runner, reason_code, findings) 分类为**完整**类别（非仅「跨模型」布尔）：
      'cross-model'  合法跨模型第二意见：host,runner∈{claude,codex} ∧ runner≠host ∧ reason_code='ok'
      'same-family'  合法同族降级：runner==host ∧ reason_code∈降级码集
      'no-exec'      合法无执行：runner='none' ∧ findings==0 ∧ (host='unknown'∧rc='host-unknown' ∨ host∈{claude,codex}∧rc∈{secret-hit,fallback-unavailable})
      'self-review'  🔴 F6 红线：runner==host ∧ reason_code∉降级码集（同族行子句被违反，非并列规则）
      'illegal'      其余一切非法组合（catch-all；含 runner='unknown' 等在共享枚举域内却非法者）
    findings 为已解析的 int（不可解析/缺失 → None，no-exec 分支因 findings!=0 落 illegal，fail-closed）。
    **关系式逻辑本地重实现**（GC-2），供 anchor_lint 判自审 / outside_voice_guard 判可复用共用（各自重实现 + golden 守）。"""
    if runner == "none":
        # 无执行行：runner='none' 一律**非跨模型**（堵 C1：none≠host 恒真会把无执行误判跨模型）
        if findings == 0 and (
            (host == "unknown" and reason_code == "host-unknown")
            or (host in _DUOS and reason_code in _NOEXEC_KNOWN_CODES)
        ):
            return "no-exec"
        return "illegal"
    if host in _DUOS and runner in _DUOS:
        if runner == host:
            # 同族行：唯一分野是 reason_code 是否属降级码集；否则即自审假绿（F6）
            return "same-family" if reason_code in _DOWNGRADE_CODES else "self-review"
        # runner≠host 且双方均真机队 → 唯一合法「第二意见」须 reason_code='ok'
        return "cross-model" if reason_code == "ok" else "illegal"
    return "illegal"                                    # catch-all（显式 else，防 if/elif 漏 else 放行 runner='unknown' 等）


def check_legal_combo(report_text, enums):
    """🔴 合法组合矩阵 = 自审红线单一源（always-on，不接受 metrics_on）。**绑定到 `sdflow:outside-voice` 锚**
    （非 lens-metric 锚——lens-metric 锚无 reason_code，绑错会让红线静默永不触发=假绿，D1）。
    对每条 fence 外 outside-voice 锚：① 校验 host/runner/reason_code 必填（现状仅记存在性、零字段解析）；
    ② 域校验（host/runner/reason_code 越域 → out-of-enum）；③ classify_combo 分类，self-review/illegal 报错。
    诚实边界：矩阵只判**锚行自身内部一致性**（锚里的字段是否自洽），堵不住伪造（写 reason_code='ok' 谎称跨模型
    仍过——无 host 真伪的机械信号，语义残余）。"""
    v = []
    for ln in fence_outside_lines(report_text):
        if anchor_prefix(ln) != "outside-voice":
            continue
        anchor = ln.strip()[:80]
        # 🔴 严格解析 + 重复键 fail-closed（镜像 check_fanout_consistency）。parse_kv 末值胜会把
        # `runner="claude" … runner="codex"` 的**自审**（first-value=claude）误读为**跨模型放行**（last-value=codex），
        # 且 sdflow-retro 读 first-value、本脚本读 last-value → 同一锚两工具判定分裂。任何重复键 → dup-key
        # 违规并**在 classify_combo 之前跳过分类**（continue），MUST NOT 让末值胜的 kv 进矩阵。
        kv, dup = parse_kv_strict(ln)
        for dk in dup:
            v.append({"anchor": anchor, "field": dk, "kind": "dup-key"})
        if dup:
            continue
        missing = [f for f in OUTSIDE_VOICE_REQUIRED_FIELDS if f not in kv]
        for f in missing:
            v.append({"anchor": anchor, "field": f, "kind": "missing-field"})
        # 域校验（与 check_lens_metric 同口径）——runner='unknown' 虽在共享枚举域内、仍由下方矩阵 catch-all 拦
        if "host" in kv and kv["host"] not in enums["host"]:
            v.append({"anchor": anchor, "field": "host", "kind": "out-of-enum"})
        if "runner" in kv and kv["runner"] not in enums["runner"]:
            v.append({"anchor": anchor, "field": "runner", "kind": "out-of-enum"})
        if "reason_code" in kv and kv["reason_code"] not in enums["reason_code"]:
            v.append({"anchor": anchor, "field": "reason_code", "kind": "out-of-enum"})
        if missing:
            continue                                    # 字段不全无从分类，避免与 missing-field 双重噪声
        findings_raw = kv.get("findings")
        findings_val = int(findings_raw) if (findings_raw is not None and _NONNEG_INT.match(findings_raw)) else None
        cat = classify_combo(kv["host"], kv["runner"], kv["reason_code"], findings_val)
        if cat == "self-review":                        # 🔴 F6 红线
            v.append({"anchor": anchor, "field": "runner", "kind": "self-review"})
        elif cat == "illegal":
            v.append({"anchor": anchor, "field": "runner", "kind": "illegal-combo"})
    return v


# --- async-outside-voice §3.5（F-C·G1/G4/G7）：declared-sites per-site 完整性机械核 -------------
# 家族级门（check_existence：报告有 ≥1 条 outside-voice 锚即过）不核 per-site ⇒ 放过「并发 2 站点
# 漏收一个」。本核补该盲区：报告落 `sdflow:declared-sites` 锚声明本层「**应有锚**站点集」，脚本
# ① 按公式重算期望集与之比对、② 与实落 `site=` 集比对，任一不等即红。
#
# 期望集 = 该层「恒有锚站点」∪「条件站点（条件成立时）」：
#   spec-review = {design-voice} ∪ {hr-tg | HR-TG∩≠∅}；code-review = {code-voice} ∪ {hr-tg | HR-TG∩≠∅}
# 🔴 MUST NOT 定义为「应 **dispatch** 的站点集」：design-voice 在复用态（reuse-guard reason_code=none、
#    未 dispatch）照样落锚，code-voice 是 always ⇒ 按 dispatch 定义会在最常见路径上假红。
# 🔴 MUST NOT 解析 `guard=`：该字段语义**站点相关**（design-voice 上 none=复用未派、hr-tg 上 none=
#    填充值已派），拿它承重即引入 site 特判。∴ 唯一动态输入 = HR-TG∩。
# 诚实边界：本核只读 `site=` 做站点集比对，**不修改** host/runner/reason_code 合法组合矩阵；
#   且只比对**集合**、不核 reason_code 新鲜度 ⇒ 抓不到「barrier 早退产生的假 timeout」（站点仍在
#   集合内、判绿）——该失效模式由 SKILL 侧正向 barrier 语义（timeout 只允许由实测 exit124 产生）守。
_LAYER_BASE_SITE = {"spec-review": "design-voice", "code-review": "code-voice"}
_SITE_VOCAB = frozenset({"design-voice", "code-voice", "hr-tg"})


def _parse_site_csv(raw):
    """CSV → site token 列表（同 _parse_tg_csv 口径：仅原始空串=空集；空 cell / 域外站点记号 → EmitError，
    调用侧就地转 violation，不外抛）。站点词表有界（三个）∴ 可枚举校验，非无界语法手搓。"""
    if raw == "":
        return []
    tokens = [t.strip() for t in raw.split(",")]
    for t in tokens:
        if t == "":
            raise EmitError(f"site CSV 含空 cell（前后/连续逗号），仅空串表空集: {raw!r}")
        if t not in _SITE_VOCAB:
            raise EmitError(f"site CSV 含域外站点记号（须 ∈ {sorted(_SITE_VOCAB)}）: {t!r}")
    return tokens


def _hr_tg_intersect_nonempty(report_text, hr_tg_subset):
    """从报告里**唯一**一条 fence 外 hr-tg 锚重算 HR-TG∩ 是否非空（= declared ∩ HR-TG 子集 ≠ ∅）。
    重算而非读 hit=：hit 的内部一致性由 check_hr_tg 的 M2 独立守，此处走同一确定性口径不引二源。
    返回 (nonempty, err)；算不出一律 fail-closed 返回 err（MUST NOT 猜期望集）。"""
    # 识别口径 MUST 与 check_hr_tg 同源（_HR_TG_ANCHOR_FULL_RE 整行严格边界）——
    # 用 anchor_prefix 会形成第二识别源：今日两条路径对畸形锚都红、无假绿，但那是巧合不是保证。
    anchors = [ln.strip() for ln in fence_outside_lines(report_text)
               if _HR_TG_ANCHOR_FULL_RE.match(ln.strip())]
    if len(anchors) != 1:
        return None, ("hr-tg 锚缺失" if not anchors else f"hr-tg 锚非唯一（{len(anchors)} 条）")
    kv, dup = parse_kv_strict(anchors[0])
    if "declared" in dup:
        return None, "hr-tg 锚 declared= 重复键"
    if "declared" not in kv:
        return None, "hr-tg 锚缺 declared="
    if kv["declared"].strip() == "none":                     # F1 sentinel：空集须 ""，"none" 字面不可解析
        return None, 'hr-tg 锚 declared="none" 字面（空集应写 ""）'
    try:
        declared = _parse_tg_csv(kv["declared"])
    except EmitError as e:
        return None, f"hr-tg 锚 declared= 畸形: {e}"
    return bool({t for t in declared if t in hr_tg_subset}), None


def check_declared_sites(report_text, layer, hr_tg_subset):
    """per-site 完整性核（always-on，不受 metrics 门控——判据源锚由 SKILL 直接落）。
    fence 口径复用本文件 `fence_outside_lines`（MUST NOT 另起裸 grep：报告正文含模版/示例锚，
    裸 grep 必自指假阳，且形成 fence 口径二源）。"""
    v = []
    # ① 实落站点集：fence 外 outside-voice 锚的 site=
    actual = set()
    for ln in fence_outside_lines(report_text):
        if anchor_prefix(ln) != "outside-voice":
            continue
        anchor = ln.strip()[:80]
        kv, dup = parse_kv_strict(ln)
        if "site" in dup:                                    # 末值胜会让漏收站点被另一处 site= 顶替
            v.append({"anchor": anchor, "field": "site", "kind": "dup-key"})
            continue
        if "site" not in kv:
            v.append({"anchor": anchor, "field": "site", "kind": "missing-field"})
            continue
        site = kv["site"]
        if site in actual:              # 重复站点锚显式拦——直接查 actual，不另存一份 list
            v.append({"anchor": anchor, "field": "site", "kind": "duplicate-site-anchor"})
        actual.add(site)
    # ② declared-sites 锚（缺失/非唯一一律 fail-closed，MUST NOT 静默放行或取首）
    ds = [ln.strip() for ln in fence_outside_lines(report_text) if anchor_prefix(ln) == "declared-sites"]
    if not ds:
        v.append({"kind": "missing-declared-sites", "detail": "报告须落 sdflow:declared-sites 锚"})
        return v
    if len(ds) > 1:
        v.append({"kind": "multi-declared-sites", "detail": f"{len(ds)} 条 declared-sites 锚"})
        return v
    anchor = ds[0][:80]
    kv, dup = parse_kv_strict(ds[0])
    for dk in dup:
        v.append({"anchor": anchor, "field": dk, "kind": "dup-key"})
    if dup:
        return v
    if "declared" not in kv:
        v.append({"anchor": anchor, "field": "declared", "kind": "missing-field"})
        return v
    try:
        declared = _parse_site_csv(kv["declared"])
    except EmitError as e:
        # 保留 _parse_site_csv 区分的两种原因（空 cell / 域外站点记号），别吞成一句笼统的 malformed
        v.append({"anchor": anchor, "field": "declared", "kind": "malformed-site-csv",
                  "detail": str(e)})
        return v
    if len(declared) != len(set(declared)):
        v.append({"anchor": anchor, "field": "declared", "kind": "declared-sites-duplicate"})
    elif declared != sorted(declared):                       # canonical = 字典序（站点非数值 token）
        v.append({"anchor": anchor, "field": "declared", "kind": "declared-sites-not-canonical-order"})
    # ③ 公式重算期望集（唯一动态输入 = HR-TG∩）
    hit_nonempty, err = _hr_tg_intersect_nonempty(report_text, hr_tg_subset)
    if err is not None:
        v.append({"kind": "hr-tg-unresolved", "detail": err})
        return v
    expected = {_LAYER_BASE_SITE[layer]} | ({"hr-tg"} if hit_nonempty else set())
    if set(declared) != expected:
        # 🔴 反规避：只比 declared vs 实落 会被「同时缩 declared 又不落锚」两边自洽绕过；本条锚公式。
        # ⚠️ 强度边界（勿高估）：本条只在 hr-tg 锚的 `declared=` 可信时成立——该字段的**正确性**
        # 是 S1 语义残余（无确定性信号，adr/0018；`check_hr_tg` 只守其内部自洽）。∴ hr-tg
        # `declared=` 漏报真实命中的 TG + 不落 hr-tg 站点锚，仍可两边自洽通过本门。这是设计
        # 已登记的诚实边界，不是本门的漏洞——但读者 MUST NOT 把本条读成「无条件反规避」。
        v.append({"anchor": anchor, "field": "declared", "kind": "declared-not-expected",
                  "detail": f"declared={sorted(set(declared))} expected={sorted(expected)}"})
    # ④ declared ↔ 实落站点集比对（本票核心：并发 2 站点漏收一个 → site-missing-anchor）
    for s in sorted(set(declared) - actual):
        v.append({"kind": "site-missing-anchor", "detail": s})
    for s in sorted(actual - set(declared)):
        v.append({"kind": "site-unexpected-anchor", "detail": s})
    return v


_FANOUT_MIRRORS = frozenset({"domain", "adversarial", "grounding"})  # 可 fan-out 的 lens 类型（一致性 lint 去重计数域）
_SUBAGENTS_VALUES = frozenset({"available", "unavailable"})
_MIRRORS_SENTINEL = "—"                                  # 未 fan-out（host=unknown）


def _parse_mirrors(raw):
    """严格文法解析 `mirrors=`：返回 (tokens, err)。tokens 为去重后合法子集（`—` → 空 list 哨兵）；
    err ∈ {'missing','empty','empty-token','unknown-token','dup-token'} 或 None。fail-closed：MUST NOT 把
    缺/坏值静默滤成空集（否则 subagents='unavailable'+空 mirrors 又判 CLEAN、C2 空转复发）。"""
    if raw is None:
        return None, "missing"
    s = raw.strip()
    if s == _MIRRORS_SENTINEL:
        return [], None                                  # 未 fan-out，合法空
    if s == "":
        return None, "empty"
    tokens = [t.strip() for t in s.split(",")]
    for t in tokens:
        if t == "":
            return None, "empty-token"
        if t not in _FANOUT_MIRRORS:
            return None, "unknown-token"
    if len(tokens) != len(set(tokens)):
        return None, "dup-token"
    return tokens, None


def check_fanout_consistency(report_text):
    """🔴 fan-out always-on 一致性 lint（不接受 metrics_on）。**判据读 `sdflow:fanout-capability` 锚的
    `mirrors=`，MUST NOT 数 lens-metric 行**（C2：lens-metric 受 metrics 门控、默认消费仓零行 → 空转）。
    subagents='unavailable' 且 mirrors 中 ∈{domain,adversarial,grounding} 去重计数 >1 ⇒ dead-fanout-multi-mirror。
    严格文法 fail-closed：重复锚 / 重复 KV / subagents 空·未知·缺 / capability host 与报告 host 不一致 /
    mirrors 缺·空·未知 token·重复 token / host=codex 报告缺该锚 → 报错。
    诚实边界：只拦「机制死却报多镜」的**自相矛盾**，MUST NOT 声称拦住伪造——mirrors=/subagents= 仍主 session
    自报，写 available 或只列 1 镜即绕过（无机械交叉核验，残余留语义层）；且是否触发受 host 自报信任边界约束
    （谎报 host=claude 则不要求该锚，与 ADR-1 同根）。"""
    v = []
    outside = list(fence_outside_lines(report_text))
    report_hosts, cap_anchors = set(), []
    for ln in outside:
        name = anchor_prefix(ln)
        if name in ("outside-voice", "lens-metric"):
            h = parse_kv(ln).get("host")
            if h:
                report_hosts.add(h)
        elif name == "fanout-capability":
            cap_anchors.append(ln)
    # Minor #2 fail-closed：同一轮评审只有一个宿主（per-row host 单一源不变式，见 spec lens-metric-emit
    # 「--host 单一源、无 per-row host」）。报告出现 ≥2 个**不同的非-unknown** host = 真冲突 → 硬停。
    # 否则原 `len(report_hosts)==1 else None` 会让 report_host 塌成 None，missing-fanout-anchor /
    # fanout-host-mismatch 静默失效（畸形/伪造多 host 报告借此把 host=codex 缺锚偷渡过关）。
    # 去 unknown 后取真 host：{codex,unknown} 之类残余不冲突，但 report_host 仍取真 host（codex 仍要求探针锚）。
    real_hosts = {h for h in report_hosts if h != "unknown"}
    if len(real_hosts) > 1:
        v.append({"anchor": "report", "field": "host", "kind": "conflicting-report-host"})
        return v
    report_host = (next(iter(real_hosts)) if len(real_hosts) == 1
                   else next(iter(report_hosts)) if len(report_hosts) == 1 else None)
    if len(cap_anchors) > 1:                             # 每轮恰好一条
        v.append({"anchor": "fanout-capability", "kind": "duplicate-fanout-anchor"})
        return v
    if not cap_anchors:
        if report_host == "codex":                      # host=codex 缺锚不得绕过
            v.append({"anchor": "fanout-capability", "kind": "missing-fanout-anchor"})
        return v
    ln = cap_anchors[0]
    anchor = ln.strip()[:80]
    kv, dup = parse_kv_strict(ln)
    for dk in dup:
        v.append({"anchor": anchor, "field": dk, "kind": "dup-key"})
    if dup:
        return v                                        # 重复 KV → fail-closed（末值胜歧义）
    cap_host = kv.get("host")
    if cap_host is None:
        v.append({"anchor": anchor, "field": "host", "kind": "missing-field"})
    elif report_host is not None and cap_host != report_host:
        v.append({"anchor": anchor, "field": "host", "kind": "fanout-host-mismatch"})
    sub = kv.get("subagents")
    if sub not in _SUBAGENTS_VALUES:                    # 必填且严格 ∈{available,unavailable}；空/未知/缺 → fail-closed
        v.append({"anchor": anchor, "field": "subagents", "kind": "bad-subagents"})
        return v
    effective_host = cap_host or report_host
    mirrors_raw = kv.get("mirrors")
    if mirrors_raw is None:
        if effective_host == "codex":                   # host=codex 报告 mirrors= 必填
            v.append({"anchor": anchor, "field": "mirrors", "kind": "mirrors-missing"})
        return v                                        # host≠codex 无 mirrors：免探，无从跑镜数 lint
    tokens, err = _parse_mirrors(mirrors_raw)
    if err:
        v.append({"anchor": anchor, "field": "mirrors", "kind": f"mirrors-{err}"})
        return v                                        # fail-closed，不静默滤成空集
    if sub == "unavailable" and len(set(tokens) & _FANOUT_MIRRORS) > 1:
        v.append({"anchor": anchor, "kind": "dead-fanout-multi-mirror"})
    return v


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
        if "host" in kv and kv["host"] not in enums["host"]:  # add-codex-host-support：host 越域
            v.append({"anchor": ln.strip()[:80], "field": "host", "kind": "out-of-enum"})
        if "runner" in kv and kv["runner"] not in enums["runner"]:  # [impl-review-fix] F1
            v.append({"anchor": ln.strip()[:80], "field": "runner", "kind": "out-of-enum"})
        if "sev" in kv and not enums["sev_re"].match(kv["sev"]):  # [impl-review-fix] F1
            v.append({"anchor": ln.strip()[:80], "field": "sev", "kind": "bad-subformat"})
        for cf in COUNT_FIELDS:
            if cf in kv and not _NONNEG_INT.match(kv[cf]):
                v.append({"anchor": ln.strip()[:80], "field": cf, "kind": "not-nonneg-int"})
        # add-codex-host-support（Step 5）：普通镜（非-outside-voice）行 runner 与 host 绑定——
        # host∈{claude,codex} ⇒ 普通镜在本机跑，runner MUST==host（∴ 普通镜 MUST NOT runner='none'/跨机队/unknown）；
        # host='unknown' ⇒ runner MUST=='unknown'（契约：unknown 仅合法于非-outside-voice 普通镜行 ∧ host=unknown）。
        # outside-voice lens-metric 行的跨模型 runner≠host 是合法的，∴ 只校验非-outside-voice 行。site 不校验（CF-补2）。
        lens_v = kv.get("lens")
        if lens_v and lens_v != "outside-voice" and "host" in kv and "runner" in kv:
            host_v, runner_v = kv["host"], kv["runner"]
            expected = "unknown" if host_v == "unknown" else (host_v if host_v in _DUOS else None)
            if expected is not None and runner_v != expected:
                v.append({"anchor": ln.strip()[:80], "field": "runner", "kind": "ordinary-runner-host-mismatch"})
        # add-codex-host-support（B1）：outside-voice lens-metric 行的 runner≠host（跨模型）合法，故不套普通镜规则——
        # 但仍有三条结构不变量 MUST 守（此前完全脱离校验 ⇒ 手写/emitter-bypass 的矛盾锚汇入 retro 价值表）。
        # 不依赖 reason_code（lens-metric 锚无该字段），纯结构判定，与 emitter 侧 _OV_RUNNER_DOMAIN/零执行不变量对齐：
        elif lens_v == "outside-voice" and "host" in kv and "runner" in kv:
            host_v, runner_v = kv["host"], kv["runner"]
            findings_v = kv.get("findings")
            # ③ OV 行 runner 域收紧 ∈{claude,codex,none}，MUST NOT="unknown"（unknown 只属非-ov 普通镜行，契约「跨模型性」段）
            if runner_v == "unknown":
                v.append({"anchor": ln.strip()[:80], "field": "runner", "kind": "ov-runner-unknown"})
            # ② host="unknown"（本轮无 voice 目标）⇒ runner MUST="none"
            if host_v == "unknown" and runner_v != "none":
                v.append({"anchor": ln.strip()[:80], "field": "runner", "kind": "ov-unknown-host-runner"})
            # ① runner="none"（无执行）⇒ findings MUST=0（findings 非法值已由 not-nonneg-int 另报，此处只判合法正数）
            if runner_v == "none" and _NONNEG_INT.match(findings_v or "") and findings_v != "0":
                v.append({"anchor": ln.strip()[:80], "field": "findings", "kind": "ov-runner-none-nonzero-findings"})
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
    # add-codex-host-support：矩阵（自审红线）+ fan-out 一致性 lint always-on——读真实性信号，与 metrics 解耦，
    # 不受 metrics_on 门控（判据源 outside-voice/fanout-capability 锚由 SKILL 直接落、不经 emitter/lens-metric）。
    violations += check_legal_combo(report_text, enums)
    violations += check_fanout_consistency(report_text)
    # async-outside-voice §3.5：per-site 完整性核 always-on（同上，判据源锚由 SKILL 直接落、不经 emitter）
    violations += check_declared_sites(report_text, args.layer, hr_tg_subset)
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
