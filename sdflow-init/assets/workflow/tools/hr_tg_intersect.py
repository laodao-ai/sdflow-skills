#!/usr/bin/env python3
"""hr_tg_intersect — 确定性 HR-TG 交集校验器（mlh-p4·T81）。
吃「模型判好的命中 TG 集」作入参（--tg-set），与 HR-TG 子集（从 trigger-catalog 单一源读）求交，
输出带「依据模型判定」的结果（模型给的输入集显式可见供复审，不 emit 裸 none）+ 规范锚串。
纯 stdlib、无 subprocess、门控外置（不读 config）；坏输入 / 单一源损坏 fail-closed all-or-nothing。
〔spec-review Q-D·推翻 grill Q1〕命中哪些 TG 无确定性信号 = 判断归模型；脚本只做确定性交集 + 出锚。
HR-TG 清单 MUST 从 trigger-catalog 单一源读、MUST NOT 硬编码副本；catalog 路径由 --trigger-catalog 入参给、
MUST NOT 用 __file__ 推导（openspec/workflow/ 下无副本，会 fail-closed 空跑，A3）。承 4.C lens_metric_emit 形态。
declared/HR-TG 成员均须存在于「触发词目录」全集（M-new 存在性 + F7 内部一致），全集边界只取表行、
正文游离提及不纳入（F8）；任一校验失败 fail-closed all-or-nothing。"""
import argparse, re, sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from pathlib import Path

EXIT_OK, EXIT_FAIL = 0, 1

_TG_STRICT_RE = re.compile(r'^TG-\d+$')       # tg-set / 成员 token 逐 token 严格校验
_H12_RE = re.compile(r'^#{1,2}\s')            # level-1/2 标题（段边界；level-3 `### ` 不匹配）
_MEMBER_RE = re.compile(r'^\s*>\s*成员')       # `> 成员：...` 行（fence/引用前缀容忍空白）
_MEMBER_CONTENT_RE = re.compile(r'^\s*>\s*成员[：:]?\s*(.*)$')  # [impl-review-fix] F-A：抽成员行冒号后内容
_H3_SECTION_RE = re.compile(r'^##\s.*触发词目录')      # 「触发词目录」段标题定位（限 level-2，避开文档 H1 标题同名误匹配）
_TABLE_TG_RE = re.compile(r'^\s*\|\s*(TG-\d+)\s*\|')   # F8：段内表行首列 TG token；正文游离提及不匹配此形
_FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})')           # [impl-review-fix] F-C：CommonMark fence（同 anchor_lint 口径）


class EmitError(Exception):
    """坏输入 fail-closed（单一源缺失/损坏/无成员、tg-set 记号非法）。"""
    pass


def fence_outside_lines(text):
    """[impl-review-fix] F-C（同 anchor_lint.fence_outside_lines 口径，本地重实现——adr/0002 非 import 约定）
    产出非 fenced-block 行（CommonMark：0-3 空格缩进 + ≥3 同字符 marker 开合、闭合行 marker 后仅空白）。
    catalog 段/成员/表行解析先过此函数，段内围栏示例（``` | TG-88 | 仅示例 | ```）不得被当真纳入。"""
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


def _locate_unique_h12(lines, matches_fn, not_found_msg, ambiguous_msg):
    """[impl-review-fix] F-B：收集全部匹配 level-2 段标题行，恰好 1 个才返回其索引；
    0 个 / ≥2 个 → EmitError（fail-closed，MUST NOT 静默取首——同名标题会劫持段边界）。"""
    idxs = [i for i, ln in enumerate(lines) if matches_fn(ln)]
    if not idxs:
        raise EmitError(not_found_msg)
    if len(idxs) > 1:
        raise EmitError(ambiguous_msg)
    return idxs[0]


def _parse_member_tokens(content):
    """[impl-review-fix] F-A：成员行内容（`> 成员：` 后半段）→ 严格 TG token 列表。
    剥外层 `**...**` markdown 粗体包裹后按逗号 split，逐 token 须 fullmatch `TG-<数字>`；
    任一畸形 token（如 TG-99x/TG-99-removed 形）或空 → EmitError（fail-closed，不宽松正规化抽取）。"""
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
    """从 trigger-catalog 的 `## …HR-TG…` 段 `> 成员：` 行 parse HR-TG 成员集。
    单一源缺失/不可读/无 HR-TG 段/段内无成员行/成员行无 TG 记号/畸形 token/段标题歧义
    → EmitError（不静默按空子集放行，不静默取首劫持段边界）。"""
    try:
        text = Path(catalog_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise EmitError(f"trigger-catalog 不可读: {e}")
    lines = list(fence_outside_lines(text))            # [impl-review-fix] F-C：段内围栏行先剔除
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
    """从 trigger-catalog「触发词目录」段的表行 `| TG-NN | ... |` parse 全 TG 集（M-new，F8 边界钉死）：
    只取该段内表行首列、逐 token 严格 fullmatch；正文游离提及（非表行）MUST NOT 纳入，段内围栏
    示例表行（F-C）MUST NOT 纳入。段缺失 / 段内无表行 / 段标题歧义（F-B）→ EmitError（单一源损坏
    fail-closed，不静默按空集放行）。"""
    try:
        text = Path(catalog_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise EmitError(f"trigger-catalog 不可读: {e}")
    lines = list(fence_outside_lines(text))            # [impl-review-fix] F-C：段内围栏行先剔除
    start = _locate_unique_h12(
        lines, lambda ln: bool(_H3_SECTION_RE.match(ln)),
        "trigger-catalog 缺「触发词目录」段（M-new 全集单一源损坏）",
        "trigger-catalog 「触发词目录」段标题歧义（同名标题多处匹配，单一源损坏，fail-closed 拒静默取首）")
    full = set()
    for ln in lines[start + 1:]:
        if _H12_RE.match(ln):                          # 到下一 level-1/2 标题 = 段结束
            break
        mm = _TABLE_TG_RE.match(ln)
        if mm:                                          # [impl-review-fix] 顺带清死代码：_TABLE_TG_RE 捕获组
            full.add(mm.group(1))                        # 结构本身即 TG-\d+ fullmatch，外层再判恒真
    if not full:
        raise EmitError("「触发词目录」段无 `| TG-NN |` 表行（M-new 全集单一源损坏）")
    return full


def parse_tg_set(raw):
    """--tg-set CSV → token 列表（原样、含重复，序化留给 intersect）。
    仅原始空串 = 空集；split 后出现空/纯空白 cell（前后/连续逗号）→ EmitError（M3 fail-closed）。
    任一 token 不形如 TG-<数字> → EmitError（坏输入 fail-closed）。"""
    if raw == "":
        return []
    tokens = [t.strip() for t in raw.split(",")]
    for t in tokens:
        if t == "":
            raise EmitError(f"tg-set 含空 cell（前后/连续逗号），仅空串表空集: {raw!r}")
        if not _TG_STRICT_RE.match(t):
            raise EmitError(f"tg-set 含非法 TG 记号（须 TG-<数字>）: {t!r}")
    return tokens


def _sort_key(t):
    return int(t[3:])                                 # "TG-" 后数字，数值序（非字典序）


def _dedup_sorted(tokens):
    return sorted(set(tokens), key=_sort_key)         # sorted(set(...)) 确定序


def intersect(declared_tokens, hr_tg_subset):
    """(命中集, 依据集) = (declared ∩ HR-TG 子集, declared)，均 dedup + 确定序。"""
    declared = _dedup_sorted(declared_tokens)
    hits = _dedup_sorted([t for t in set(declared_tokens) if t in hr_tg_subset])
    return hits, declared


def render(hits, declared):
    """两行输出：结果行（依据模型判定可见，不裸 none）+ 规范 hr-tg 锚串（扩 declared= 字段）。"""
    declared_csv = ",".join(declared)
    if hits:
        hit_csv = ",".join(hits)
        result = f"hit:[{hit_csv}]｜依据模型判定:[{declared_csv}]"
        anchor = f'<!-- sdflow:hr-tg v1 hit="{hit_csv}" declared="{declared_csv}" -->'
    else:
        result = f"none｜依据模型判定:[{declared_csv}]"
        anchor = f'<!-- sdflow:hr-tg v1 hit="none" declared="{declared_csv}" -->'
    return result + "\n" + anchor


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="HR-TG 交集校验器（确定性·纯 stdlib·fail-closed·门控外置）")
    ap.add_argument("--tg-set", required=True,
                    help="模型判好的命中 TG 集，逗号分隔（空集传空串）")
    ap.add_argument("--trigger-catalog", required=True,
                    help="$RULES_ROOT/trigger-catalog.md 路径（HR-TG 单一源，禁 __file__ 推导）")
    args = ap.parse_args(argv)
    try:
        hr_tg = load_hr_tg_subset(Path(args.trigger_catalog))   # 单一源先读（损坏即 fail-closed；含 F7 内部一致校验）
        declared_tokens = parse_tg_set(args.tg_set)
        all_tg = load_all_tg_set(Path(args.trigger_catalog))    # M-new：declared 存在性校验用全集
        for t in set(declared_tokens):
            if t not in all_tg:
                raise EmitError(f"declared 含「触发词目录」全集外 TG（不存在，M-new）: {t}")
        hits, declared = intersect(declared_tokens, hr_tg)
        out = render(hits, declared)                            # all-or-nothing：全过才产出
    except EmitError as e:
        print(f"[hr_tg_intersect] FAIL: {e}", file=sys.stderr)  # 坏输入：stderr FAIL、无 stdout
        return EXIT_FAIL
    print(out)                                                  # hit/none 均为合法判定 → EXIT_OK
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
