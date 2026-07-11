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
from pathlib import Path

EXIT_OK, EXIT_FAIL = 0, 1

_TG_TOKEN_RE = re.compile(r'TG-\d+')          # 宽松抽取（忽略 **bold**/空格）
_TG_STRICT_RE = re.compile(r'^TG-\d+$')       # tg-set 逐 token 严格校验
_H12_RE = re.compile(r'^#{1,2}\s')            # level-1/2 标题（段边界；level-3 `### ` 不匹配）
_MEMBER_RE = re.compile(r'^\s*>\s*成员')       # `> 成员：...` 行（fence/引用前缀容忍空白）
_H3_SECTION_RE = re.compile(r'^##\s.*触发词目录')      # 「触发词目录」段标题定位（限 level-2，避开文档 H1 标题同名误匹配）
_TABLE_TG_RE = re.compile(r'^\s*\|\s*(TG-\d+)\s*\|')   # F8：段内表行首列 TG token；正文游离提及不匹配此形


class EmitError(Exception):
    """坏输入 fail-closed（单一源缺失/损坏/无成员、tg-set 记号非法）。"""
    pass


def load_hr_tg_subset(catalog_path):
    """从 trigger-catalog 的 `## …HR-TG…` 段 `> 成员：` 行 parse HR-TG 成员集。
    单一源缺失/不可读/无 HR-TG 段/段内无成员行/成员行无 TG 记号 → EmitError（不静默按空子集放行）。"""
    try:
        text = Path(catalog_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise EmitError(f"trigger-catalog 不可读: {e}")
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if _H12_RE.match(ln) and "HR-TG" in ln:      # 定位 HR-TG 段标题
            start = i
            break
    if start is None:
        raise EmitError("trigger-catalog 缺 `## …HR-TG…` 段（单一源损坏）")
    members = None
    for ln in lines[start + 1:]:
        if _H12_RE.match(ln):                         # 到下一 level-1/2 标题 = 段结束
            break
        if _MEMBER_RE.match(ln):
            members = _TG_TOKEN_RE.findall(ln)        # 段内 `> 成员：` 行才算数，不跨段借用
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
    只取该段内表行首列、逐 token 严格 fullmatch；正文游离提及（非表行）MUST NOT 纳入。
    段缺失 / 段内无表行 → EmitError（单一源损坏 fail-closed，不静默按空集放行）。"""
    try:
        text = Path(catalog_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise EmitError(f"trigger-catalog 不可读: {e}")
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if _H3_SECTION_RE.match(ln)), None)
    if start is None:
        raise EmitError("trigger-catalog 缺「触发词目录」段（M-new 全集单一源损坏）")
    full = set()
    for ln in lines[start + 1:]:
        if _H12_RE.match(ln):                          # 到下一 level-1/2 标题 = 段结束
            break
        mm = _TABLE_TG_RE.match(ln)
        if mm and _TG_STRICT_RE.match(mm.group(1)):     # 逐 token 严格 fullmatch，拒残留后缀
            full.add(mm.group(1))
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
