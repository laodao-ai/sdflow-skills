#!/usr/bin/env python3
"""maintain_scan.py — sdflow-maintain 的确定性只读差异报告核心。

扫 openspec/specs|rules ↔ INDEX.md（托管块外）双向 set-diff、CLAUDE.md 过时引用、
workflow bundle 陈旧遮蔽，产出四类分节只读报告。纯读、fail-closed、零写文件。
判断（归组/是否修复）留 SKILL 步骤 4；判据 canonical 见 init.py，本文件保自包含副本
+ 一致性守卫测试机验（见 tests/test_marker_consistency.py）。
"""
import argparse
import os
import re
import sys


class MaintainScanError(Exception):
    """坏输入 / 无法可靠完成扫描。main() 捕获 → stderr → 非零退出（fail-closed）。"""


def find_repo_root(start):
    """从 start 向上找含 .git 的目录，返回其绝对路径；找不到 raise MaintainScanError。"""
    cur = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(cur, ".git")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            raise MaintainScanError(f"未找到 git 仓根（从 {start} 向上）")
        cur = parent


MANAGED_TOKEN_START = "opsx-init:rules:start"
MANAGED_TOKEN_END = "opsx-init:rules:end"

# 链接目标路径 join-key（H3/D1）：只纳 specs/{name}/spec.md 与 rules/{name}.md
_SPEC_LINK = re.compile(r"specs/([a-z0-9-]+)/spec\.md")
_RULE_LINK = re.compile(r"rules/([a-z0-9-]+)\.md")
_ANY_LINK = re.compile(r"\]\(([^)]+)\)")  # markdown 链接 target


def scan_fs_specs(root):
    d = os.path.join(root, "openspec", "specs")
    if not os.path.isdir(d):
        raise MaintainScanError("openspec/specs/ 缺失")
    return {
        name for name in os.listdir(d)
        if os.path.isfile(os.path.join(d, name, "spec.md"))
    }


def scan_fs_rules(root):
    d = os.path.join(root, "openspec", "rules")
    if not os.path.isdir(d):
        return set()  # rules/ 可选，缺失=合法空集
    return {
        f[:-3] for f in os.listdir(d)
        if f.endswith(".md") and os.path.isfile(os.path.join(d, f))
    }


def _is_marker_line(line, token):
    """fence-aware 由调用方处理；此处判「含 token ∧ lstrip 后以 <!-- 起」（镜像 init.py）。"""
    return token in line and line.lstrip().startswith("<!--")


def split_managed_block(index_text):
    """fence-aware 剥 opsx-init:rules 托管块，返回 (块外行列表, 告警列表)。
    marker 不配对 → MaintainScanError（畸形托管块不静默当边界，接 D2）。
    块内探到 specs/*/spec.md 模式 → 告警（M8/D11 堵审计无人区）。"""
    lines = index_text.splitlines()
    in_fence = False
    start_idx = end_idx = None
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if start_idx is None and _is_marker_line(line, MANAGED_TOKEN_START):
            start_idx = i
        elif start_idx is not None and end_idx is None and _is_marker_line(line, MANAGED_TOKEN_END):
            end_idx = i
    if in_fence:
        # [impl-review-fix] 围栏未闭合 fail-closed：奇偶取反状态机若无兜底，未闭合 ``` 会让
        # 其后全部内容被静默当围栏跳过 → 假「一致」（design D2 防假一致方向）。
        raise MaintainScanError(
            "INDEX.md 围栏未闭合（```），结构不可信，拒绝输出（防假一致）"
        )
    warnings = []
    if (start_idx is None) != (end_idx is None):
        raise MaintainScanError("INDEX 托管块 marker 不配对（只有 start 或只有 end），结构不可信")
    if start_idx is not None and end_idx is not None:
        if end_idx < start_idx:
            raise MaintainScanError("INDEX 托管块 marker 顺序错乱（end 在 start 前）")
        block = lines[start_idx:end_idx + 1]
        if any(_SPEC_LINK.search(b) for b in block):
            warnings.append("⚠ 疑似 spec 条目误置于 init 托管块内（应在块外索引）")
        body = lines[:start_idx] + lines[end_idx + 1:]
    else:
        body = lines
    return body, warnings


def parse_index_entries(body_lines):
    """链接路径 join：只纳 specs/{name}/spec.md（spec 类）/ rules/{name}.md（rule 类）。
    四类判据（H2/Q1=A）：①无链接语法的结构行（表头/分隔/散文）跳过 ②a specs/rules 条目入集
    ②b 非-spec/rule 链接（retro-report 等）静默排除 ③有链接语法但 target 解析不出路径 → fail-closed
    （防假一致：链接语法存活但抽不出 target，说明正则/输入有意外形态，宁可拒绝输出也不当①静默放过）。"""
    specs, rules = set(), set()
    in_fence = False
    for line in body_lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if "](" not in line:
            continue  # ① 结构行（无链接语法：表头/分隔/散文），跳过不 fail
        links = _ANY_LINK.findall(line)
        if not links:
            # ③ 有链接开启子串 "](" 但正则抽不出 target（如空 target `[x]()`、未闭合 `[x](`）
            # → 真少读，fail-closed，拒绝在不完整信息下输出报告（防假一致）
            raise MaintainScanError(
                "INDEX 表体链接语法存活但 target 解析不出路径，拒绝输出（防假一致）: "
                f"{line!r}"
            )
        for target in links:
            sm = _SPEC_LINK.search(target)
            rm = _RULE_LINK.search(target)
            if sm:
                specs.add(sm.group(1))
            elif rm:
                rules.add(rm.group(1))
            # ②b 非-spec/rule 链接（retro/report.md, roadmaps/…）静默排除
    if in_fence:
        # [impl-review-fix] 围栏未闭合 fail-closed（同 split_managed_block，防假一致）
        raise MaintainScanError(
            "INDEX.md 表体围栏未闭合（```），结构不可信，拒绝输出（防假一致）"
        )
    return {"spec": specs, "rule": rules}


# 引用匹配契约（M1/D4）：openspec/(specs|rules)/<name>(/|.md)，<name> ∈ [a-z0-9-]+
# [impl-review-fix] 捕获组同时留住 specs/rules 类型（原正则用非捕获组丢弃类型信息），
# 使调用方能按类型分别核对对应 fs 目录，而非依赖 INDEX diff 的 stale 集。
_REF = re.compile(r"openspec/(specs|rules)/([a-z0-9-]+)(?:/|\.md)")
# 占位符：花括号 token（{name} 等）
_PLACEHOLDER = re.compile(r"\{[a-z0-9_-]+\}")


def _iter_claude_files(root):
    def _onerror(err):
        # [impl-review-fix] 目录级不可读 fail-closed：os.walk 默认 onerror=None 会静默跳过
        # 不可读子目录；传回调使目录级不可读也非零退出（对称文件级 open 失败）。
        raise MaintainScanError(f"目录扫描失败（不可读或其他 OSError）: {err.filename}: {err}")

    for dirpath, _dirs, files in os.walk(root, onerror=_onerror):
        if os.sep + ".git" in dirpath:
            continue
        if "CLAUDE.md" in files:
            yield os.path.join(dirpath, "CLAUDE.md")


def scan_claude_refs(root, fs_specs, fs_rules):
    """扫根+子目录 CLAUDE.md，报引用了已从文件系统删除的 spec/rule 路径的位置。
    [impl-review-fix] 判定改为直接核对 fs 是否存在该 spec/rule（对齐 spec R2「已从文件
    系统删除」原文语义），不再依赖 INDEX stale 集（= INDEX 列但 fs 缺）——旧判据漏掉最
    常见用例：spec 已归档、fs+INDEX 都清了、CLAUDE.md 忘同步。
    排除：代码围栏/行内 code、占位符 {name}、泛指路径（无具体 <name>）。"""
    hits = []
    for path in _iter_claude_files(root):
        try:
            text = open(path, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError) as e:
            raise MaintainScanError(f"CLAUDE.md 不可读: {path}: {e}")
        in_fence = False
        for lineno, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            # 剥行内 code 段再匹配（排除 `...` 内提及）
            stripped = re.sub(r"`[^`]*`", "", line)
            stripped = _PLACEHOLDER.sub("", stripped)
            for kind, name in _REF.findall(stripped):
                exists = name in (fs_specs if kind == "specs" else fs_rules)
                if not exists:
                    rel = os.path.relpath(path, root)
                    hits.append(f"{rel}:{lineno}: {name}")
        if in_fence:
            # [impl-review-fix] 围栏未闭合 fail-closed（同 INDEX 侧两处，防假一致）
            rel = os.path.relpath(path, root)
            raise MaintainScanError(
                f"CLAUDE.md 围栏未闭合（```），结构不可信，拒绝输出（防假一致）: {rel}"
            )
    return hits


RULE_MARKERS = ("workflow.md", "spec-checklists", "code-checklists")


def scan_stale_shadow(root):
    """周期性兜底：openspec/workflow/ 残留规则本体 → 遮蔽全局 canonical。仅报告，绝不删。
    canonical 判据 = init.py:RULE_MARKERS（本副本经一致性守卫测试机验，见 test_marker_consistency）。"""
    warns = []
    wf = os.path.join(root, "openspec", "workflow")
    found = [m for m in RULE_MARKERS if os.path.exists(os.path.join(wf, m))]
    if found:
        warns.append(
            "⚠ openspec/workflow/ 残留规则副本（" + "、".join(found)
            + "）——遮蔽全局 bundle 且不再被 update 刷新："
            "想跟全局最新→手动删净；想 pin 这一版→留着（显式逃生口）")
    if os.path.isfile(os.path.join(root, "hack", "checkpoint-commit.sh")):
        warns.append(
            "⚠ hack/checkpoint-commit.sh 为旧版仓内副本（checkpoint 已全局化 → ~/.sdflow/hack/）："
            "删=用全局；若保留本地 workflow.md 副本（pin）且其仍引用仓内路径→勿删")
    return warns


def set_diff(fs, indexed):
    return {
        "new": {k: fs[k] - indexed[k] for k in ("spec", "rule")},
        "stale": {k: indexed[k] - fs[k] for k in ("spec", "rule")},
    }


def _read_index(root):
    p = os.path.join(root, "openspec", "INDEX.md")
    if not os.path.isfile(p):
        raise MaintainScanError("openspec/INDEX.md 缺失")
    try:
        return open(p, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError) as e:
        raise MaintainScanError(f"INDEX.md 不可读: {e}")


def run_scan(root):
    fs = {"spec": scan_fs_specs(root), "rule": scan_fs_rules(root)}
    body, mgr_warns = split_managed_block(_read_index(root))
    indexed = parse_index_entries(body)
    diff = set_diff(fs, indexed)
    # [impl-review-fix] scan_claude_refs 改吃 fs 集合直查存在性，不再吃 INDEX stale 集
    claude_refs = scan_claude_refs(root, fs["spec"], fs["rule"])
    stale_shadow = scan_stale_shadow(root)
    return build_report(diff, mgr_warns, claude_refs=claude_refs, stale_shadow=stale_shadow)


def build_report(diff, mgr_warns, claude_refs, stale_shadow):
    lines = ["# maintain_scan 差异报告", ""]
    any_diff = (
        any(diff[k][t] for k in ("new", "stale") for t in ("spec", "rule"))
        or bool(claude_refs) or bool(stale_shadow) or bool(mgr_warns)
        # [impl-review-fix] mgr_warns（疑似 spec 误置托管块内等）纳入 has_diff 判定，
        # 否则该告警会与「一致，无差异」并存，自相矛盾。
    )
    lines.append("## 新增未索引")
    new_entries = [(t, n) for t in ("spec", "rule") for n in sorted(diff["new"][t])]
    for t, n in new_entries:
        lines.append(f"- {n}（{t}）")
    if not new_entries:
        lines.append("- 无")  # [impl-review-fix] 空节占位，对齐「过时引用」「陈旧遮蔽」写法
    lines.append("## 已删未清理")
    stale_entries = [(t, n) for t in ("spec", "rule") for n in sorted(diff["stale"][t])]
    for t, n in stale_entries:
        lines.append(f"- {n}（{t}）")
    if not stale_entries:
        lines.append("- 无")  # [impl-review-fix] 空节占位
    lines.append("## 过时引用")
    for ref in claude_refs:
        lines.append(f"- {ref}")
    if not claude_refs:
        lines.append("- 无")
    lines.append("## 陈旧遮蔽（workflow bundle）")
    for w in stale_shadow:
        lines.append(f"- {w}")
    if not stale_shadow:
        lines.append("- 无")
    if not any_diff:
        lines.append("")
        lines.append("一致，无差异")
    for w in mgr_warns:
        lines.append(w)
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="sdflow-maintain 确定性只读差异报告（fail-closed）")
    ap.add_argument("--root", default=None, help="仓根，缺省自动探测 git 根")
    args = ap.parse_args(argv)
    try:
        root = args.root or find_repo_root(os.getcwd())
        report = run_scan(root)
    except MaintainScanError as e:
        print(f"[maintain_scan] ERROR {e}", file=sys.stderr)
        return 2
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
