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

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass


class MaintainScanError(Exception):
    """坏输入 / 无法可靠完成扫描。main() 捕获 → stderr → 非零退出（fail-closed）。"""


def find_repo_root(start):
    """从 start 向上找含 .git 的目录（含 linked worktree 的 .git 文件），返回其绝对路径；找不到 raise MaintainScanError。"""
    try:
        cur = os.path.abspath(start)
    except OSError:
        raise MaintainScanError(f"仓根探测起点不可达（从 {start}）") from None
    while True:
        if os.path.exists(os.path.join(cur, ".git")):
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
    [impl-review-fix] 候选行 MUST 先限定为 markdown 表格行（spec H3/D1：「已列条目」锚在
    表格行链接目标路径模式）——`line.lstrip().startswith("|")` 且有表格 cell 结构（含 ≥2 个
    `|`）才参与下方四类判据；非表格行（散文如「见 [foo](./specs/foo/spec.md)」、正文段落）
    一律跳过、不参与 set-diff、也不触发③ fail-closed（防止散文里的偶然 spec 链接被误当
    「已索引」，掩盖真实新增未索引条目）。表头分隔行 `|---|---|` 无链接语法，落①自然跳过，
    不用特判。
    四类判据（H2/Q1=A，现限定表格行内）：①无链接语法的结构行（表头/分隔）跳过 ②a specs/rules
    条目入集 ②b 非-spec/rule 链接（retro-report 等）静默排除 ③有链接语法但 target 解析不出
    路径 → fail-closed（防假一致：链接语法存活但抽不出 target，说明正则/输入有意外形态，
    宁可拒绝输出也不当①静默放过）。"""
    specs, rules = set(), set()
    in_fence = False
    for line in body_lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = line.lstrip()
        if not (stripped.startswith("|") and stripped.count("|") >= 2):
            continue  # 非表格行（散文/正文），跳过不参与判据、不 fail
        if "](" not in line:
            continue  # ① 结构行（表头/分隔，无链接语法），跳过不 fail
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

    for dirpath, dirnames, files in os.walk(root, onerror=_onerror):
        # [impl-review-fix] 精确剪枝 .git：只剔除路径组件恰为 ".git" 的目录，原子串判断
        # `os.sep + ".git" in dirpath` 误匹配 ".github"/".gitlab"/".gitea" 等目录，导致其下
        # CLAUDE.md 被静默跳过（违反 spec R2「扫描根 + 各子目录 CLAUDE.md」）。
        dirnames[:] = [d for d in dirnames if d != ".git"]
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
            with open(path, encoding="utf-8") as f:
                text = f.read()
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
        with open(p, encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError) as e:
        raise MaintainScanError(f"INDEX.md 不可读: {e}")


# ---------- devenv 健康度（spec: maintain-scan）----------
#
# 【为什么这一节必须存在（dogfood 自指坑）】
# add-sdflow-devenv 把「无门禁——某些检查没有任何自动触发点、全靠人记得跑」列为立项理由之一，
# 而它的 devenv_lint 【原本自己也没有任何触发点】。
#
# 更要命的是：devenv 的渐进 DoD 允许泳道停在 scaffolded、槽停在 `⚠️ 待定`，而防止它烂成
# 僵尸文档的【唯一措施就是把代价摆到人眼前】（adr/0021）——若无人调用该 lint，该措施为空。
# **「不强制完成」+「不检查未完成」= 名存实亡，两者只能选一个。**
# 本节是 devenv 选择「不强制完成」后必须配的那一半。

DEVENV_REL = os.path.join("openspec", "architecture", ".devenv.json")


def scan_devenv(root):
    """→ (状态, 文本)。状态 ∈ {absent, unavailable, bad, ok}

    absent      消费仓无 .devenv.json          ⇒ 跳过（非报错）
    unavailable 有 .devenv.json 但未装 sdflow-devenv ⇒ 【显式提示】，MUST NOT 静默略过
    bad         数据坏了（lint 的唯一 fail-closed）
    ok          text = lint 报告【原样】

    🔴 **原样透传，MUST NOT 重新渲染**：spec 明禁把 lint 结果二次简化成「verified = ✓」式的
       绿色状态——`verified` 的语义是 `verified-at <sha>`（一次历史执行的记录，不是当前绿灯）。
       重渲染必然丢掉 commit 锚。所以这里【一个字都不改】地并进报告。
    """
    if not os.path.isfile(os.path.join(root, DEVENV_REL)):
        return "absent", ""

    sib = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       os.pardir, "sdflow-devenv", "scripts")
    sib = os.path.normpath(sib)
    if sib not in sys.path:
        sys.path.insert(0, sib)
    try:
        import devenv_lint
    except ImportError:
        return "unavailable", ""

    ok, text = devenv_lint.render(root)
    return ("ok" if ok else "bad"), text


def run_scan(root):
    fs = {"spec": scan_fs_specs(root), "rule": scan_fs_rules(root)}
    body, mgr_warns = split_managed_block(_read_index(root))
    indexed = parse_index_entries(body)
    diff = set_diff(fs, indexed)
    # [impl-review-fix] scan_claude_refs 改吃 fs 集合直查存在性，不再吃 INDEX stale 集
    claude_refs = scan_claude_refs(root, fs["spec"], fs["rule"])
    stale_shadow = scan_stale_shadow(root)
    devenv = scan_devenv(root)
    return build_report(diff, mgr_warns, claude_refs=claude_refs, stale_shadow=stale_shadow,
                        devenv=devenv)


def build_report(diff, mgr_warns, claude_refs, stale_shadow, devenv=("absent", "")):
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

    # devenv 健康度 —— 🔴 【MUST NOT 进 any_diff】：它是【提醒】，不是【门禁】（adr/0021）。
    # devenv_lint 的退出码永远是 0（除非数据坏了）；把它渲染成「通过/不通过」就是把
    # 「代价可见」做成了「机械拦截」，正是 devenv 整个设计要杀的东西。
    st, text = devenv
    if st != "absent":
        lines.append("")
        lines.append("## devenv 健康度（提醒，非门禁 —— adr/0021）")
        if st == "unavailable":
            lines.append("- ⚠️ 检出 `.devenv.json` 但 `devenv_lint` 不可用（未装 sdflow-devenv），"
                         "跳过健康度扫描")
        elif st == "bad":
            lines.append(f"- ⚠️ `.devenv.json` 数据坏了：{text}")
        else:
            # 【原样】并入 —— 一个字都不改（commit 锚、待定横幅、blocked_by 全带着）
            lines += ["", text]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="sdflow-maintain 确定性只读差异报告（fail-closed）")
    ap.add_argument("--root", default=None, help="仓根，缺省自动探测 git 根")
    args = ap.parse_args(argv)
    try:
        try:
            cwd = os.getcwd()
        except OSError:
            raise MaintainScanError("进程当前工作目录已不存在或不可访问") from None
        root = args.root or find_repo_root(cwd)
        report = run_scan(root)
    except MaintainScanError as e:
        print(f"[maintain_scan] ERROR {e}", file=sys.stderr)
        return 2
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
