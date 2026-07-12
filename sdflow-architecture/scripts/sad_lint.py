#!/usr/bin/env python3
"""sad_lint.py — SAD v1 结构断言（读侧，DEC-1 唯一消费 sad_schema，MUST NOT 另写解析器）。

CLI: sad_lint.py --root <消费仓根>（定位 openspec/architecture/sad.md）或 --sad <直接路径>
exit 码约定（DEC-5 输出诚实）：
  0 = 全过 —— stdout 首行 sad_schema.PASS_CODE + `假设计数: N` 行
  1 = 违规 —— 每条 `[sad_lint] {code}: {detail}` + `  next-step: {提示}`（独立收集全量，非首错即停），
      末尾仍有 `假设计数: N` 行
  2 = 坏输入（文件缺失 / frontmatter 损坏 / 枚举非法）—— stderr `[sad_lint] FAIL: {原因}`，
      stdout 不携带任何判定字样（与正常判定物理区分）

假设计数口径（两个数、两个用途，勿混）：
  - stdout `假设计数: N` —— 正文内联实扫**去重后**计数（body scan，供人快速核对规模）
  - assumption-cache-mismatch 的「实扫值」—— 附录表中处置为「未处置」的行数
    （与 sad_scaffold._recompute_assumptions_cache 同一口径，即 frontmatter assumptions_open 的真相定义）
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sad_schema  # noqa: E402  (共享解析源，DEC-1；本脚本只做消费方语义校验)


def _die(code, msg):
    print(f"[sad_lint] FAIL: {msg}", file=sys.stderr)
    sys.exit(code)


def _section_number(anchor):
    """`## 8. 横切概念` → `8`（detail 里指名哪节，供人定位）。"""
    return anchor[len("## "):].split(".", 1)[0].strip()


def _check_sections(sections, violations):
    for anchor in sad_schema.SECTION_ANCHORS:
        info = sections[anchor]
        non_empty = [(ln, l) for ln, l in info["body"] if l.strip()]
        if not info["present"] or not non_empty:
            violations.append(("missing-section", f"第{_section_number(anchor)}节缺失或正文全空：{anchor}"))
            continue
        first = non_empty[0][1].strip()
        if first.startswith("N/A") and not sad_schema.NA_RE.match(first):
            violations.append(("na-without-reason", f"{anchor} 首行 {first!r} 缺具体理由（须 `N/A — <理由>`）"))


def _check_assumptions(text, fm, violations):
    inline, rows = sad_schema.scan_assumptions(text)
    violations.extend(sad_schema.check_assumptions(text))
    cache = fm["assumptions_open"]
    recompute = sum(1 for _, d in rows if d == "未处置")
    if recompute != cache:
        violations.append((
            "assumption-cache-mismatch",
            f"实扫未处置数={recompute} ≠ 缓存 assumptions_open={cache}",
        ))
    return len(set(inline))


def _check_quality_attr_order(sections, violations):
    body = sections["## 1. 目标与质量属性"]["body"]
    non_empty = [(ln, l) for ln, l in body if l.strip()]
    if not non_empty:
        return  # 节缺失/全空已由 missing-section 覆盖，不重复报
    if non_empty[0][1].strip().startswith("N/A"):
        return  # 显式 N/A 豁免全序断言
    nums = []
    for _, l in non_empty:
        m = sad_schema.ORDERED_RE.match(l.strip())
        if m:
            nums.append(int(m.group(1)))
    if not nums or nums != list(range(1, len(nums) + 1)):
        violations.append((
            "quality-attr-order-broken",
            f"编号序列={nums} 非法——须非空且为 [1..N] 严格连续",
        ))


def _check_contract_invariants(text, status, violations):
    for ln, tag in sad_schema.scan_contract_tags(text):
        if tag not in sad_schema.CONTRACT_ENUM:
            violations.append(("contract-invariant-violation", f"未知 contract 标签 {tag!r}（line {ln}）"))
            continue
        if status in ("draft", "skeleton-ready") and tag in ("validated", "frozen"):
            violations.append((
                "contract-invariant-violation",
                f"status={status} 但 contract[{tag}]（line {ln}）——draft/skeleton-ready ⇒ contract∈{{planned,draft}}",
            ))
        if status == "validated" and tag == "draft":
            violations.append((
                "contract-invariant-violation",
                f"status=validated 但残留 contract[draft]（line {ln}）——须∈{{validated,frozen}}（planned 豁免）",
            ))


def _slice_section_present(text):
    return any(l.strip() == sad_schema.SLICE_ANCHOR for _, l in sad_schema.body_lines(text))


def _check_slice_branch(text, status, violations):
    present = _slice_section_present(text)
    if status == "skeleton-ready":
        if not present:
            violations.append(("slice-section-missing", "status=skeleton-ready 但缺「骨架切片建议」节"))
        else:
            pierce, subsys = set(sad_schema.scan_pierce_refs(text)), set(sad_schema.scan_subsystems(text))
            if pierce != subsys:
                violations.append((
                    "slice-pierce-set-mismatch",
                    f"穿越点集{sorted(pierce)} ≠ 第5节子系统集{sorted(subsys)}",
                ))
    elif status == "validated" and present:
        violations.append(("slice-section-stale", "status=validated 但仍残留「骨架切片建议」节"))


def lint_text(text):
    """返回 (violations, assumption_count)。violations 为 [(code, detail), ...]。"""
    violations = []
    fm = sad_schema.parse_frontmatter(text)

    if fm["sad_schema"] != sad_schema.SAD_SCHEMA_VERSION:
        violations.append((
            "schema-version-mismatch",
            f"SAD 声明 sad_schema={fm['sad_schema']} ≠ 脚本支持版本={sad_schema.SAD_SCHEMA_VERSION}",
        ))

    sections = sad_schema.scan_sections(text)
    _check_sections(sections, violations)
    n = _check_assumptions(text, fm, violations)
    _check_quality_attr_order(sections, violations)
    _check_contract_invariants(text, fm["sad_status"], violations)
    _check_slice_branch(text, fm["sad_status"], violations)

    return violations, n


def _resolve_path(args):
    if args.sad:
        return Path(args.sad)
    return Path(args.root).resolve() / sad_schema.SAD_REL_PATH


def build_parser():
    parser = argparse.ArgumentParser(prog="sad_lint.py")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--root", default=None, help="消费仓根，定位 openspec/architecture/sad.md")
    group.add_argument("--sad", default=None, help="直接指定 sad.md 路径")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    path = _resolve_path(args)
    if not path.is_file():
        if path.exists():
            _die(2, f"sad.md 不是常规文件：{path}")
        else:
            _die(2, f"sad.md 不存在：{path}")

    try:
        raw = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        _die(2, f"sad 文件不可读（非 UTF-8 或 IO 错误）: {e}")
        return 2  # 不可达，安抚静态检查
    text = raw.lstrip("﻿").replace("\r\n", "\n")

    try:
        violations, n = lint_text(text)
    except sad_schema.SadParseError as e:
        _die(2, str(e))
        return 2  # 不可达，安抚静态检查

    if not violations:
        print(sad_schema.PASS_CODE)
        print(f"假设计数: {n}")
        return 0

    for code, detail in violations:
        print(f"[sad_lint] {code}: {detail}")
        print(f"  next-step: {sad_schema.REASON_NEXT_STEP[code]}")
    print(f"假设计数: {n}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
