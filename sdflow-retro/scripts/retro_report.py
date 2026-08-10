import argparse
import json
import os
import re
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lens_metric_aggregate as LMA  # 复用其 fence-aware 锚解析（parse_report + _int），不重实现

_DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-(.+)$")
_REPORT_NAMES = ("spec-review-report.md", "code-review-report.md")
_HRTG_RE = re.compile(r'<!--\s*sdflow:hr-tg\s+v1\s+hit="([^"]*)"')


def discover_changes(root):
    changes_dir = os.path.join(root, "openspec", "changes")
    archive_dir = os.path.join(changes_dir, "archive")
    out = {}
    if os.path.isdir(changes_dir):
        for name in os.listdir(changes_dir):
            p = os.path.join(changes_dir, name)
            if name == "archive" or not os.path.isdir(p):
                continue
            out.setdefault(name, {"active": False, "active_dir": None, "archive_dir": None})
            out[name]["active"] = True
            out[name]["active_dir"] = p
    if os.path.isdir(archive_dir):
        for entry in os.listdir(archive_dir):
            p = os.path.join(archive_dir, entry)
            if not os.path.isdir(p):
                continue
            m = _DATE_PREFIX.match(entry)
            name = m.group(1) if m else entry
            out.setdefault(name, {"active": False, "active_dir": None, "archive_dir": None})
            out[name]["archive_dir"] = p
    return out


def _run_git(root, *args):
    # [T60] git 失败（returncode≠0）向 stderr 留痕——否则「git 报错」与「真无提交」
    # 都表现为空 stdout、静默不可区分（边界解析会把 git 故障误当无历史）。
    # 仍返回 stdout（失败时通常为空）以保持所有调用方契约不变。
    proc = subprocess.run(
        ["git", "-C", root, "-c", "core.quotePath=false", *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        sys.stderr.write(
            f"[sdflow-retro] git 失败 (rc={proc.returncode}): git {' '.join(args)}\n"
            f"  stderr: {proc.stderr.strip()}\n")
    return proc.stdout


def git_commits_for_path(root, relpath):
    out = _run_git(root, "log", "--format=%H%x00%ct%x00%s", "--", relpath)
    commits = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\x00")
        if len(parts) != 3:
            continue
        sha, ts, subject = parts
        try:
            commits.append({"sha": sha, "ts": int(ts), "subject": subject})
        except ValueError:
            continue
    commits.reverse()  # git log 默认逆序 → 升序
    return commits


def commit_change_dir_count(root, sha):
    out = _run_git(root, "show", "--name-only", "--format=", sha)
    dirs = set()
    for f in out.splitlines():
        m = re.match(r"openspec/changes/(?:archive/\d{4}-\d{2}-\d{2}-)?([^/]+)/", f)
        if m:
            dirs.add(m.group(1))
    return len(dirs)


def seed_mass_shas(root, threshold=3):
    out = _run_git(root, "log", "--format=%H")
    seed = set()
    for sha in out.split():
        if commit_change_dir_count(root, sha) >= threshold:
            seed.add(sha)
    return seed


def boundary_for_change(root, name, info, seed_shas):
    # [impl-review-fix] F1: 致命 bug 修复——归档 change 的 active_dir 在磁盘上已不存在（None），
    # 原实现只 _fetch(active_dir)(None→[]) 再兜底 archive_dir（archive 路径 git log 只看得到
    # rename 后的历史，看不到 rename 前的活动期提交），导致 17/18 归档 change 假性「边界不可解析」。
    # 修法：始终查裸 pre-archive 路径 openspec/changes/<name>（git log 对该 pathspec 历史性可达，
    # 不依赖该目录当前是否还在磁盘/HEAD 上——这是 design D1 的本意）∪ archive 路径（归档 rename
    # 提交只碰 archive 路径），按 sha 去重、按 ts 升序合并。
    def _fetch(relpath):
        if not relpath:
            return []
        cs = git_commits_for_path(root, relpath)
        return [c for c in cs if c["sha"] not in seed_shas]

    by_sha = {}
    for c in _fetch(f"openspec/changes/{name}"):
        by_sha.setdefault(c["sha"], c)
    archive_dir = info.get("archive_dir")
    if archive_dir:
        arel = os.path.relpath(archive_dir, root)
        for c in _fetch(arel):
            by_sha.setdefault(c["sha"], c)
    merged = sorted(by_sha.values(), key=lambda c: c["ts"])

    if len(merged) <= 1:
        return {"commits": merged, "unresolved": True,
                "note": f"边界不可解析（提交数={len(merged)}，seed/单步 change）"}
    return {"commits": merged, "unresolved": False, "note": ""}


# 最长前缀词表：按前缀长度降序尝试匹配 checkpoint(<inner>)
_STAGE_RULES = [
    ("impl-review", "code-review"),
    ("final-review", "code-review"),
    ("sdd-final-review", "code-review"),
    ("spec-review", "spec-review"),
    ("design-gate", "spec-review"),
    ("writing-plans", "impl"),
    ("model-baseline", "impl"),
    # [impl-review-fix] F6: 补前缀——本仓真实存在 checkpoint(done-archive)/checkpoint(done-verify)/
    # 裸 checkpoint(gate) 提交，原词表无匹配落 unknown 桶；F1 修复后归档 change 的 done 阶段提交
    # 会大量出现，须能正确归类。gate 归 spec-review 因 design-gate 已归 spec-review，裸 gate 同族。
    ("done-archive", "done"),
    ("done-verify", "done"),
    ("gate", "spec-review"),
    # `sdflow-` 前缀的 skill 名式 slug。**MUST 各自单列**——匹配是 `startswith`，
    # 「grill」不是 `sdflow-spec-grill` 的前缀，靠既有词表这一族全落 unknown（dogfood 实测）。
    # 相位 B（对抗拷问）同族于 grill；相位 C（生成四件套）同族于 ff（旧三入口里由 ff 承担同一产出）。
    # [impl-review-fix] F1（面治）：`sdflow-code-review`（仓内 3 次）/ `sdflow-spec-review`（1 次）
    # 与上两条**同形**，上一轮只补了 sdflow-spec-* 两条 ⇒ 一并补齐，别再留同族漏网格。
    ("sdflow-spec-grill", "grill"),
    ("sdflow-spec-generate", "ff"),
    ("sdflow-code-review", "code-review"),
    ("sdflow-spec-review", "spec-review"),
    ("grill", "grill"),
    ("ff", "ff"),
    ("propose", "other"),
    ("plan", "other"),
    ("roadmap", "other"),
    ("issues", "other"),
]
_CKPT_RE = re.compile(r"^checkpoint\(([^)]*)\)")

# [impl-review-fix fix2] F-B：tail 回退里，**短**规则按 token 匹配而非裸前缀匹配。
# `gate` / `ff` / `plan` 这三条是词不是前缀 —— 裸 startswith 会把 `gateway-refactor` /
# `ffmpeg-upgrade` / `planner` 静默吞进 spec-review / ff / other。4 是当前最短规则族的长度
# （`gate`/`plan` 4 字符、`ff` 2 字符），再长的规则（`grill` 起）自带足够特异性。
_TAIL_STRICT_MAXLEN = 4


def _prefix_hit(candidate, prefix, *, token_boundary):
    """`candidate` 是否命中规则 `prefix`；`token_boundary` 时短前缀须全等或后接 `-`。"""
    if not candidate.startswith(prefix):
        return False
    if token_boundary and len(prefix) <= _TAIL_STRICT_MAXLEN:
        rest = candidate[len(prefix):]
        return rest == "" or rest.startswith("-")
    return True


def map_stage(subject):
    m = _CKPT_RE.match(subject.strip())
    if not m:
        return "unknown"
    inner = m.group(1)
    # 命名空间任务标签 <change>:task<N>-... → impl
    tail = inner.split(":", 1)[1] if ":" in inner else inner
    if re.match(r"task\d+", tail) or tail.endswith("-impl"):
        return "impl"
    # 最长前缀匹配：规则按前缀长度降序。
    # 先拿整串 `inner` 试（保住 `<change>` 名本身就带阶段词的既有语义），
    # [impl-review-fix] F1：整串无命中 ⇒ **回退用剥掉命名空间的 `tail` 再试一次**。
    # 目标态 producer 就在产出 `checkpoint(<change>:<step>)`（`sdflow-implement/SKILL.md:287`
    # 明写 `checkpoint-commit.sh "<change>:plan"`），旧实现只在 task/-impl 两条判定里剥前缀，
    # 前缀匹配却拿整串比 ⇒ `<step>` 精确等于既有规则的 27 个 checkpoint 全落 unknown。
    # [impl-review-fix fix2] F-B：回退这一跳（且**仅**这一跳）要求短前缀落在 token 边界上，
    # 整串 `inner` 的匹配语义一字未动（change 名本身带阶段词的既有归类照旧）。
    ordered = sorted(_STAGE_RULES, key=lambda r: -len(r[0]))
    for candidate, token_boundary in ((inner, False), (tail, True)):
        for prefix, stage in ordered:
            if _prefix_hit(candidate, prefix, token_boundary=token_boundary):
                return stage
    if inner.endswith("-cross-review") or tail.endswith("-cross-review"):
        return "other"
    return "unknown"


def is_archive_rename(root, sha, name):
    # [impl-review-fix] F5: name in p 是裸子串匹配，foo 会误配 foo-2 的归档路径；
    # 改用目录边界锚定（archive/YYYY-MM-DD-<name>/ 或整段结尾），F1 修复后 pre-archive 全历史
    # 回归、跨 change 提交交集变多，这个雷会被引爆，故一并锚定。
    archive_pat = re.compile(rf"changes/archive/\d{{4}}-\d{{2}}-\d{{2}}-{re.escape(name)}(/|$)")
    out = _run_git(root, "show", "--name-status", "--format=", sha)
    moved_out = False
    into_archive = False
    for line in out.splitlines():
        if not line.strip():
            continue
        cols = line.split("\t")
        status = cols[0]
        paths = cols[1:]
        if status.startswith("R") and len(paths) == 2:
            src, dst = paths
            if f"changes/{name}/" in src and archive_pat.search(dst):
                return True
        if status == "D" and any(f"changes/{name}/" in p and "/archive/" not in p for p in paths):
            moved_out = True
        if status == "A" and any(archive_pat.search(p) for p in paths):
            into_archive = True
    return moved_out and into_archive


def stage_walltimes(root, name, commits):
    """
    计算相邻 commit 时间差累加到各阶段的墙钟数。

    [absorb-gstack-autoplan] attribute-to-next：checkpoint 语义 = 工作完成点，
    区间 [cur,nxt) 的墙钟归其**完成点** nxt 的阶段（不是起点 cur 的阶段）——修正既有错账：
    旧口径下 checkpoint(sdflow-spec-generate)→checkpoint(spec-review-autoplan) 区间因
    cur=sdflow-spec-generate 映射 stage="ff" 而把 Step1 广审墙钟误归 ff；新口径下该区间归
    nxt 的阶段（spec-review-autoplan→spec-review），归属正确。

    Args:
        root: 项目根目录
        name: change 名称
        commits: 升序 commit list，每个包含 {"sha", "ts", "subject"}

    Returns:
        {"stages": {stage: minutes}, "total_min": float, "n_ckpt": int, "reorder_suspected": bool}
    """
    stages = {}
    reorder = False

    # 相邻提交差计入后一个提交（完成点）的阶段
    for i in range(len(commits) - 1):
        cur, nxt = commits[i], commits[i + 1]
        delta_s = nxt["ts"] - cur["ts"]

        # 负数 → 钳 0 且标记 reorder
        if delta_s < 0:
            delta_s = 0
            reorder = True

        # 完成本区间的提交（nxt）的阶段
        if is_archive_rename(root, nxt["sha"], name):
            stage = "done"
        else:
            stage = map_stage(nxt["subject"])

        # 累加到该阶段（秒转分钟）
        stages[stage] = stages.get(stage, 0.0) + delta_s / 60.0

    # 首提交若是 archive rename，单独标记 done 存在（无前驱 Δ 可归属——对称于旧口径下
    # 末提交的等价边界情形，旧口径末提交从不作为 cur、新口径首提交从不作为 nxt）
    if commits and is_archive_rename(root, commits[0]["sha"], name):
        stages.setdefault("done", 0.0)

    total = sum(stages.values())
    return {
        "stages": stages,
        "total_min": round(total, 1),
        "n_ckpt": len(commits),
        "reorder_suspected": reorder
    }


def lens_value_for_change(info):
    """扫该 change 的 active_dir + archive_dir 两处 spec/code review 报告，
    复用 lens_metric_aggregate.parse_report（fence-aware）解析锚，按 layer 分归属。
    坏文件（IO/解码错误）fail-safe 跳过，不崩、不拖垮整体聚合——同 aggregate() 的处理口径。
    """
    anchors = []
    for base in (info.get("active_dir"), info.get("archive_dir")):
        if not base:
            continue
        for rn in _REPORT_NAMES:
            fp = os.path.join(base, rn)
            if os.path.isfile(fp):
                try:
                    anchors.extend(LMA.parse_report(fp))
                except (OSError, UnicodeDecodeError, ValueError):
                    continue

    by_layer = {}
    sum_f = sum_a = sum_ind = 0
    num_bad = False
    for a in anchors:
        layer = a.get("layer", "unknown")
        entry = by_layer.setdefault(layer, {"findings": 0, "采纳": 0, "独立": 0})
        # [impl-review-fix F3] 不再丢弃 is_bad——修前 `_, _ = LMA._int(...)` 三处静默
        # 吞掉非法值标记（负数契约非法 / 非数字串），导致同一批坏锚在聚合③
        # （render_table）打 ⚠数值非法、在这里（per-change 表数据源）却悄悄看起来
        # 正常，同源数据两张表互相矛盾。此处收集 is_bad，供 build_report 打 ⚠ 标记。
        f_val, f_bad = LMA._int(a.get("findings"))
        a_val, a_bad = LMA._int(a.get("采纳"))
        ind_val, ind_bad = LMA._int(a.get("独立"))
        num_bad = num_bad or f_bad or a_bad or ind_bad
        entry["findings"] += f_val
        entry["采纳"] += a_val
        entry["独立"] += ind_val
        sum_f += f_val
        sum_a += a_val
        sum_ind += ind_val

    rate = round(sum_a / sum_f, 2) if sum_f else None
    return {
        "has_anchor": bool(anchors),
        "by_layer": by_layer,
        "sum_findings": sum_f,
        "accept_rate": rate,
        "sum_independent": sum_ind,
        "num_bad": num_bad,
    }


# ============================ 聚合④ per-镜实修率（历史回算）============================
# [implement-workflow-optimization-2026-08-p1 task2] 从归档评审报告 finding 行机械提取
# fix-status（三态+未知）与 lens 归属（封闭关键词表，仅有界记号内查），按 (layer,lens)
# 聚合可判定/实修/未修/defer 计数。窄文法两轴均「宁缺毋假」——任一维度不可判定即入未知桶，
# MUST NOT 猜。复用 LMA._fence_aware_lines 滤围栏示范锚；不改 LMA 任何既有函数签名（只读
# 消费方）。真语料试算（task2.0，一次性脚本，非本文件）显示密度低（可判定样本多数 <5），
# 与 design.md 已接受的风险一致（"覆盖率低的镜标「参考」"）。

FIXRATE_MIN_SAMPLE = 5  # [T2] 阈值单一源：可判定数 < 此值标「参考」，不作砍留依据

_FR_NEEDLE = "已修[impl-review-fix]"
# defer 类标注：词边界 + 非紧跟 ="（防误命中 lens-metric 锚 `defer="N"` KV 字段——真实语料
# 实证：锚行含 `采纳="0"` `defer="0"` 等字段名，裸子串匹配会把锚行误判命中处置动词/裸串）。
_FR_DEFER_RE = re.compile(r'(?i)\bdefer\b(?!=")')
_FR_BARE = "impl-review-fix"
_FR_VERBS = ("已修", "采纳", "自动修")

# 镜关键词 → LMA.LENS_ENUM 同源 canonical 值；"域" 仅作"领域"别名（仅在有界记号内识别）；
# "outside-voice"/"voice" 是同一 canonical 值的两种拼写（非两个镜，不构成歧义）。
_FR_LENS_MAP = {
    "对抗": "adversarial", "领域": "domain", "域": "domain",
    "接地": "grounding", "历史": "history",
    "outside-voice": "outside-voice", "voice": "outside-voice",
    "广审": "broad",
}
_FR_LENS_KEYS = sorted(_FR_LENS_MAP, key=len, reverse=True)  # 长键优先（outside-voice 先于 voice，非必要但显式）

_FR_TABLE_ROW = re.compile(r'^\s*\|(.*)\|\s*$')
_FR_TABLE_SEP = re.compile(r'^\s*\|[\s:|-]+\|\s*$')
_FR_BRACKET = re.compile(r'〔([^〕]*)〕|【([^】]*)】')
_FR_SECTION_HDR = re.compile(r'^#{2,4}\s+')


def _fr_lens_hits(text):
    """text 内命中的 canonical lens 值去重集合（封闭关键词表，MUST NOT 猜）。"""
    return {_FR_LENS_MAP[kw] for kw in _FR_LENS_KEYS if kw in text}


def _fr_table_cols(lines, idx):
    """idx 指向疑似表格数据行；解析其所属表的表头，取「来源」列与「处置」列同位置 cell。
    返回 (来源cell_or_None, 处置cell_or_None, is_data_row)；非法/非表格/表头/分隔行本身
    → (None, None, False)。「处置」列存在是 not_fixed 分支的候选门（见 extract_fixrate_
    samples）——真语料试算证实：缺此门会把「决策登记区」〔〕散文标签、「已裁掉」表
    （用「裁掉理由」列非「处置」列）大量误判未修，双双被此结构信号排除。"""
    start = idx
    while start > 0 and _FR_TABLE_ROW.match(lines[start - 1]):
        start -= 1
    if start + 1 >= len(lines) or not _FR_TABLE_SEP.match(lines[start + 1]):
        return None, None, False
    if idx == start or idx == start + 1:
        return None, None, False
    header_cells = [c.strip().strip("*").strip() for c in lines[start].strip().strip("|").split("|")]
    src_idx = next((i for i, c in enumerate(header_cells) if "来源" in c), None)
    disp_idx = next((i for i, c in enumerate(header_cells) if "处置" in c), None)
    cur_cells = [c.strip() for c in lines[idx].strip().strip("|").split("|")]
    src_cell = cur_cells[src_idx] if src_idx is not None and src_idx < len(cur_cells) else None
    disp_cell = cur_cells[disp_idx] if disp_idx is not None and disp_idx < len(cur_cells) else None
    return src_cell, disp_cell, True


def _fr_classify_status(line):
    """fix-status 三态 + 未修兜底。[spec-review-amendment] 宁缺毋假方向修正：裸
    `impl-review-fix` 串或处置动词（已修/采纳/自动修）但不命中精确 needle → unknown_disposal
    （MUST NOT 判未修——语料实测 67% 变体不命中精确 needle，默认判未修会方向性压低实修率）。"""
    if _FR_NEEDLE in line:
        return "fixed"
    if _FR_DEFER_RE.search(line):
        return "defer"
    if _FR_BARE in line or any(v in line for v in _FR_VERBS):
        return "unknown_disposal"
    return "not_fixed"


def extract_fixrate_samples(text):
    """对单份报告文本逐行窄文法提取，产出 (lens_or_None, status) 元组 list。
    status ∈ {"fixed","defer","not_fixed","unknown_disposal"}；lens 由有界来源记号
    （表格「来源」列 cell + 全部〔…〕/【…】括号内容）解析，精确命中一个 canonical 值才
    非 None，零个或多个命中 → None（未知，不猜）。

    机械锚行（`<!-- sdflow:` 前缀）与 section 标题行（`##`/`###`/`####`）跳过——前者
    KV 字段名（`采纳=`/`defer=`）假阳命中处置动词/裸串，后者本身可能带裸 `impl-review-fix`
    字面量（如 "Findings（置信 ≥80，均已自动修 [impl-review-fix]）" 标题），均非 finding 行。

    候选门：① 行含处置信号（needle/defer/裸串/处置动词之一）——覆盖 bullet 与表格两种
    finding 形态；② 或行是「处置」列表格的数据行（结构信号，仅用于 not_fixed 分支候选，
    见 _fr_table_cols 注释）。二者皆不满足 → 不是候选，跳过（不计入未知，因为它压根
    不是 finding 行）。
    """
    out = []
    lines = list(LMA._fence_aware_lines(text))
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("<!-- sdflow:") or _FR_SECTION_HDR.match(s):
            continue
        regions = [(m.group(1) if m.group(1) is not None else m.group(2)) for m in _FR_BRACKET.finditer(line)]
        table_src = table_disp = None
        is_row = False
        if _FR_TABLE_ROW.match(line) and not _FR_TABLE_SEP.match(line):
            table_src, table_disp, is_row = _fr_table_cols(lines, i)
            if table_src is not None:
                regions.append(table_src)
        status = _fr_classify_status(line)
        has_disposal = status != "not_fixed"
        is_disposition_row = is_row and table_disp is not None
        if not has_disposal and not is_disposition_row:
            continue
        hits = _fr_lens_hits(" ".join(regions))
        lens = next(iter(hits)) if len(hits) == 1 else None
        out.append((lens, status))
    return out


def _change_has_fix_commit(root, name):
    """change 边界内是否存在 impl-review-fix 类修复 commit（commit subject 子串匹配，
    宽松/不精确——D2 拍板：commit 主键降为佐证 flag，不参与判定，仅展示）。查两条路径：
    裸 pre-archive 路径（历史性可达，同 boundary_for_change 的裸路径必查惯例）+ archive
    路径（磁盘枚举匹配 `*-<name>` 后缀，git pathspec 原生不支持 shell glob）。"""
    out = _run_git(root, "log", "--format=%s", "--", f"openspec/changes/{name}")
    if any(_FR_BARE in s for s in out.splitlines()):
        return True
    archive_dir = os.path.join(root, "openspec", "changes", "archive")
    if os.path.isdir(archive_dir):
        for entry in os.listdir(archive_dir):
            if entry.endswith(f"-{name}"):
                rel = os.path.relpath(os.path.join(archive_dir, entry), root)
                out = _run_git(root, "log", "--format=%s", "--", rel)
                if any(_FR_BARE in s for s in out.splitlines()):
                    return True
    return False


def fixrate_aggregate(root):
    """扫 archive 全部 `*-review-report.md`，跑窄文法回算，返回
    (rows: {(layer,lens): {"可判定":n,"实修":n,"未修":n,"defer":n,"未知":n,"佐证":bool}},
     lens_unknown: {layer: n})。

    两级未知桶：① lens 已解析但 fix-status 不可判（unknown_disposal）→ 计入该 (layer,lens)
    行自身的 "未知" 字段（我们知道是哪面镜，只是不知道修没修）；② lens 本身不可解析
    （0/2+ 命中或无有界记号）→ 计入 lens_unknown[layer]（跨该 layer 全部镜共享，无法
    归属到具体某面镜）。可判定 = 实修+未修+defer；覆盖率 = 可判定/(可判定+①的未知)。

    「佐证」flag：该 (layer,lens) 有 ≥1 贡献样本所属 change 的 git 历史含 impl-review-fix
    类修复 commit（懒惰求值 + 按 change 名缓存，避免 O(rows×changes) 重复 git 调用）。
    坏文件（IO/解码错误）fail-safe 跳过，不拖垮整体聚合——同 LMA.aggregate 的处理口径。
    """
    archive_root = os.path.join(root, "openspec", "changes", "archive")
    rows = defaultdict(lambda: {"可判定": 0, "实修": 0, "未修": 0, "defer": 0, "未知": 0, "佐证": False})
    lens_unknown = defaultdict(int)
    contributing = defaultdict(set)  # (layer,lens) -> {change_name,...}
    try:
        if not Path(archive_root).is_dir():
            return {}, {}
        reports = sorted(Path(archive_root).glob("**/*-review-report.md"))
    except OSError:
        return {}, {}

    for report in reports:
        if report.name == "code-review-report.md":
            layer = "code-review"
        elif report.name == "spec-review-report.md":
            layer = "spec-review"
        else:
            continue
        m = _DATE_PREFIX.match(report.parent.name)
        change_name = m.group(1) if m else report.parent.name
        try:
            text = report.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            continue
        for lens, status in extract_fixrate_samples(text):
            if lens is None:
                lens_unknown[layer] += 1
                continue
            key = (layer, lens)
            if status == "unknown_disposal":
                rows[key]["未知"] += 1
                continue
            rows[key]["可判定"] += 1
            if status == "fixed":
                rows[key]["实修"] += 1
            elif status == "defer":
                rows[key]["defer"] += 1
            elif status == "not_fixed":
                rows[key]["未修"] += 1
            contributing[key].add(change_name)

    fix_commit_cache = {}
    for key, names in contributing.items():
        for name in names:
            if name not in fix_commit_cache:
                fix_commit_cache[name] = _change_has_fix_commit(root, name)
            if fix_commit_cache[name]:
                rows[key]["佐证"] = True
                break
    return dict(rows), dict(lens_unknown)


def render_fixrate_table(rows, lens_unknown):
    """聚合④ per-镜实修率（历史回算）markdown 渲染。每镜可判定/未知/覆盖率三数 + 实修率
    （可判定<阈值标「参考」，MUST NOT 作砍留依据）+ 佐证 flag（不参与判定，纯展示）。"""
    lines = ["| layer | lens | 可判定 | 实修 | defer | 未修 | 未知(本镜) | 覆盖率 | 实修率 | 佐证 |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    if not rows:
        lines.append("| — | — | 0 | 0 | 0 | 0 | 0 | — | — | — |")
    for (layer, lens), d in sorted(rows.items()):
        denom = d["可判定"]
        covered_pool = denom + d["未知"]
        coverage = f"{denom / covered_pool:.0%}" if covered_pool else "—"
        rate = f"{d['实修'] / denom:.0%}" if denom else "—"
        if denom < FIXRATE_MIN_SAMPLE:
            rate += "（参考）"
        evid = "有 commit 佐证" if d["佐证"] else "—"
        lines.append(f"| {layer} | {lens} | {denom} | {d['实修']} | {d['defer']} | {d['未修']} | "
                     f"{d['未知']} | {coverage} | {rate} | {evid} |")
    lines.append("")
    layer_unk_str = ", ".join(f"{k}={v}" for k, v in sorted(lens_unknown.items())) or "无"
    lines.append(f"> 「未知(本镜)」= fix-status 不可判（裸 impl-review-fix/处置动词但不命中精确 "
                 f"needle）但 lens 已解析的样本，计入该镜自身；lens 本身不可解析（0/2+ 命中或无"
                 f"有界记号）的样本无法归属具体镜，按 layer 汇总另计：{layer_unk_str}。")
    lines.append(f"> 可判定 < {FIXRATE_MIN_SAMPLE}（单一源阈值）标「参考」，MUST NOT 作砍留依据；"
                 f"窄文法宁缺毋假，MUST NOT 为提覆盖率放宽文法猜测归属。")
    return "\n".join(lines)


def _read_hr_hit(base, report_name):
    """读单个报告文件的 hr-tg 锚。
    [impl-review-fix F2] 坏文件（权限拒绝/IO 错误）fail-safe 返回 "—"，不崩，
    同 lens_value_for_change 对同类坏文件的处理口径。
    [impl-review-fix F4] 复用 LMA._fence_aware_lines 过滤 fenced 示范锚（同 lens-metric
    锚享同等 fence 护栏，避免文档里反引号包裹的示范 hr-tg 锚被误读为真判定）。
    [impl-review-fix F7] 不遇首个锚即 return——续扫全文取最后一条命中，
    以应对同一报告内多条 hr-tg 锚（如广审判定 + 后续更权威判定）时取最终判定而非 first-wins。
    """
    if not base:
        return "—"
    fp = os.path.join(base, report_name)
    if not os.path.isfile(fp):
        return "—"
    try:
        with open(fp, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError):
        return "—"
    hit = "—"
    for line in LMA._fence_aware_lines(text):
        m = _HRTG_RE.search(line)
        if m:
            hit = m.group(1)
    return hit


def hr_tg_flags(info):
    def pick(rn):
        for base in (info.get("active_dir"), info.get("archive_dir")):
            hit = _read_hr_hit(base, rn)
            if hit != "—":
                return hit
        return "—"
    return {"spec_hr_tg": pick("spec-review-report.md"),
            "code_hr_tg": pick("code-review-report.md")}


def surfacing_counts(root):
    """扫 archive 的 lens-metric 锚，按 (layer,lens,host,runner,site) 分组计「出现
    轮数」〔add-codex-host-support:task5 升维加 host〕（口径与 lens_metric_aggregate.
    render_table 同源——复用 group_key，含其双代兼容读），返回 (counts, flagged, thr)。
    单一源：surfacing_block 的文本渲染与 build_report 顶部「一览」卡片的待复评镜
    计数都从此取，杜绝两处各算一遍出现漂移。
    """
    archive_root = os.path.join(root, "openspec", "changes", "archive")
    counts = defaultdict(int)
    # [T61] aggregate 已按显式契约处理缺失/非目录 archive（返空不抛），逐文件读错也在其内部
    # try/except 处理——故此处无需再包防御性 try/except（原 catch 不可达、注释误导已删）。
    rows, _no_anchor, _parse_failed = LMA.aggregate(archive_root)
    for r in rows:
        counts[LMA.group_key(r)] += 1
    thr = LMA.REVIEW_ROUNDS_THRESHOLD  # [T59] 与 render_table 共享同源阈值，不再本地硬编码 10
    flagged = [(k, c) for k, c in counts.items() if c >= thr]
    return counts, flagged, thr


def surfacing_block(root):
    """D12：待复评镜 surfacing 机械契约。扫 archive 的 lens-metric 锚，
    按 (layer,lens,host,runner,site) 分组计「出现轮数」〔add-codex-host-support:task5
    升维加 host〕（口径须与 lens_metric_aggregate.render_table 一致——直接复用同一
    分组键，不重复定义）；轮数 ≥ 阈值（`LMA.REVIEW_ROUNDS_THRESHOLD`，与 render_table
    同源，文档不写死字面量）的镜在报告顶部独立区块列出，固定前缀标记 `⚠️ 待复评:`
    （可机验，MUST NOT 仅用形容词）。无命中也必须输出固定行——防止「长期无命中」被
    静默省略成死列（同 hr-tg 空箱同理，grill-not-skippable 教训：跳过类判定不能不可见）。
    """
    counts, flagged, thr = surfacing_counts(root)
    if not flagged:
        return f"⚠️ 待复评: 无（所有镜出现轮数<{thr}）"
    lines = [f"⚠️ 待复评: 以下镜出现轮数≥{thr}、只提示不判断不自动砍——人读后自行决定保留/降采样/淘汰:"]
    for (layer, lens, host, runner, site), c in sorted(flagged):
        lines.append(f"  - {lens}（layer={layer} host={host} runner={runner} site={site}，出现轮数 {c}）")
    return "\n".join(lines)


def _stage_col(wt, stage):
    """[impl-review-fix F12] per-change 表阶段 Δ 列格式化——0 或缺失均显 "—"，
    非 0 时四舍五入 1 位小数，与其余 "—" 空箱口径一致（同 hr-tg/无度量锚同理）。"""
    v = wt["stages"].get(stage, 0)
    return round(v, 1) if v else "—"


# ============================ task4: per-change tokens 列（读 token-log.jsonl）============================
# [implement-workflow-optimization-2026-08-p1 task4] Δ 归属口径（读侧全局按 session 跨 change
# 分组差分，设计门 Q1 拍板=A）：token-log.jsonl 写侧只追加 session 累计 usage（token_snapshot.py
# 无状态、不做区间差分），Δ 完全由此处读侧算。逐行防御解析——无法解析/字段非法的行按
# anchor=false 等价处理并跳过，不中断该 change 及其余 change 的报告生成（design.md Risks
# 「token-log 单行损坏拖垮整仓报告」）。MUST NOT 合成四计数的总分（四者计价不同）。

_TOKEN_TS_FMTS = ("%Y-%m-%dT%H:%M:%S%z",)  # strptime("%z") 原生兼容 "+0800" 与 "+08:00" 两种偏移写法


def _parse_token_log_line(raw_line):
    """单行 token-log.jsonl → 规范化 dict，或 None（等价 anchor=false，逐行跳过不抛）。

    只接受 anchor=true 且 usage 四计数（input/output/cache_read/cache_creation）均为非负整数、
    session/step 非空字符串、ts 可解析的行；其余（anchor=false 降级行、坏 JSON、截断半行、
    字段缺失/类型错）一律返回 None——调用方据此过滤，不参与 Δ 计算，也不中断整行扫描。
    ts 用 `datetime.strptime(...,"%z")` 解析（非 `fromisoformat`）——真实生产者
    `token_snapshot.py` 用 `time.strftime("%Y-%m-%dT%H:%M:%S%z")` 产出「无冒号」偏移量
    （如 "+0800"），`fromisoformat` 在 Python<3.11 上无法解析该格式，会把真实数据全行
    误判 anchor=false（本仓当前活动 change 的真实 token-log.jsonl 已实测证实该格式）。
    """
    try:
        obj = json.loads(raw_line)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    if obj.get("anchor") is not True:
        return None
    session = obj.get("session")
    step = obj.get("step")
    ts_raw = obj.get("ts")
    if not isinstance(session, str) or not session:
        return None
    if not isinstance(step, str) or not step:
        return None
    if not isinstance(ts_raw, str) or not ts_raw:
        return None
    ts = None
    for fmt in _TOKEN_TS_FMTS:
        try:
            ts = datetime.strptime(ts_raw, fmt)
            break
        except Exception:
            continue
    if ts is None:
        return None
    usage = obj.get("usage")
    if not isinstance(usage, dict):
        return None
    counts = {}
    for dst, src in (("out", "output"), ("in", "input"),
                      ("cc", "cache_creation"), ("cr", "cache_read")):
        v = usage.get(src)
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            return None
        counts[dst] = v
    return {"session": session, "step": step, "ts": ts, "usage": counts}


def read_token_log(path):
    """读单个 token-log.jsonl，逐行防御解析；文件缺失/IO 错误 → 空列表（不崩、不中断调用方）。"""
    rows = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                row = _parse_token_log_line(line)
                if row is not None:
                    rows.append(row)
    except OSError:
        return []
    return rows


def compute_token_deltas(root, changes):
    """全局按 session 分组差分，返回 `{change_name: {"out","in","cc","cr"}}`（只含 ≥1 贡献行
    的 change；无 token-log 或全降级/全损坏的 change 不在返回 dict 中，调用方据此渲染「—」）。

    先按 change 名升序扫全部 change 目录（活动 + 归档）的 token-log.jsonl 读入全部合法行，
    同 session 的行全体按 ts 稳定排序（同 ts 时保留扫描顺序，即 change 名升序 + 文件内追加序，
    tie-break 确定性）；组内首行（该 session 的全局最早合法行）全额计入其所在 change，其余
    每行对同组内紧邻前一行差分（Δ 负值钳 0，防御 usage 非严格单调场景）、归属自身所在 change
    ——这天然实现「跨 change 同 session：后一文件首行对前一文件末行差分」（Q1=A），因为排序后
    两个文件的行在时间线上自然相邻，无需额外的「文件边界」特判。
    """
    all_rows = []
    for name, info in sorted(changes.items()):
        for base in (info.get("active_dir"), info.get("archive_dir")):
            if not base:
                continue
            path = os.path.join(base, "token-log.jsonl")
            for row in read_token_log(path):
                row = dict(row)
                row["change"] = name
                all_rows.append(row)

    groups = defaultdict(list)
    for row in all_rows:
        groups[row["session"]].append(row)

    deltas = defaultdict(lambda: {"out": 0, "in": 0, "cc": 0, "cr": 0})
    for rows in groups.values():
        ordered = sorted(rows, key=lambda r: r["ts"])
        prev = None
        for row in ordered:
            u = row["usage"]
            target = deltas[row["change"]]
            if prev is None:
                for k in target:
                    target[k] += u[k]
            else:
                pu = prev["usage"]
                for k in target:
                    target[k] += max(0, u[k] - pu[k])
            prev = row
    return dict(deltas)


_TOKEN_FOOTNOTE = ("> tokens 列：数值为各会话累计口径聚合，tickets 管线下多为独立短会话的首行"
                    "全额之和，非严格阶段增量。")


def _fmt_compact_count(n):
    """紧凑计数格式：≥1M 显 `X.XM`，≥1k 显 `X.Xk`（去掉多余的 `.0`），否则原样整数。"""
    if n >= 1_000_000:
        s = f"{n / 1_000_000:.1f}"
        return f"{s[:-2] if s.endswith('.0') else s}M"
    if n >= 1_000:
        s = f"{n / 1_000:.1f}"
        return f"{s[:-2] if s.endswith('.0') else s}k"
    return str(n)


def format_tokens_cell(d):
    """per-change 表 tokens 列单元格：四计数紧凑串，MUST NOT 合成总分；无数据显「—」。"""
    if not d:
        return "—"
    return (f"out {_fmt_compact_count(d['out'])} / in {_fmt_compact_count(d['in'])} / "
            f"cc {_fmt_compact_count(d['cc'])} / cr {_fmt_compact_count(d['cr'])}")


# ============================ 一览（语义化总结）============================
# 阶段/镜 内部键→中文可读名。仅影响顶部「一览」段的呈现，不改动下方明细表口径
# （明细表沿用内部键，便于与 lens-metric 锚逐字核对）。
STAGE_LABELS = {
    "spec-review": "设计审", "code-review": "代码审", "impl": "写实现",
    "grill": "grill 死磕", "ff": "ff 生成", "done": "收尾",
    "other": "其他", "unknown": "未归类",
}
LENS_LABELS = {
    "adversarial": "对抗", "domain": "领域", "broad": "广审",
    "grounding": "接地", "history": "历史", "outside-voice": "外部声音",
}


def _fmt_dur(minutes):
    """分钟→可读时长：≥60 分显 x.x hr；≥1 分显整数 min；亚分钟保留 1 位小数
    （不 round 成 "0 min" 骗人——0.2min 的 plan 桩 change 如实显 "0.2 min"）。"""
    if minutes >= 60:
        return f"{minutes / 60:.1f} hr"
    if minutes >= 1:
        return f"{round(minutes)} min"
    return f"{minutes:.1f} min"


def _top_mirror(agg_rows):
    """从原始锚行按聚合③同分组 (layer,lens,host,runner,site) 找 Σfindings 最大的
    一格〔add-codex-host-support:task5 升维加 host〕。与聚合③同口径（复用
    LMA.group_key/_int，含其双代兼容读），读者可在聚合③表逐行核对，不冒
    (layer,lens) 求和把 site="—" rollup 与 per-site 行双计的风险。
    返回 (label, findings, accept_rate_str) 或 None（无锚/全 0）。"""
    grp = defaultdict(lambda: {"f": 0, "采纳": 0, "裁掉": 0, "defer": 0})
    for r in agg_rows:
        g = grp[LMA.group_key(r)]
        for src, dst in (("findings", "f"), ("采纳", "采纳"),
                         ("裁掉", "裁掉"), ("defer", "defer")):
            v, _bad = LMA._int(r.get(src))
            g[dst] += v
    if not grp:
        return None
    (layer, lens, host, runner, site), g = max(grp.items(), key=lambda kv: kv[1]["f"])
    if g["f"] <= 0:
        return None
    denom = g["采纳"] + g["裁掉"] + g["defer"]
    rate = f"{g['采纳'] / denom:.0%}" if denom else "—"
    label = f"{STAGE_LABELS.get(layer, layer)}{LENS_LABELS.get(lens, lens)}镜"
    # [add-codex-host-support:task5] host 分组分开呈现（GC-9）——Codex 宿主前缀标注
    # （host≠claude 是本 change 新增的可能性，最值得显著呈现）；host=claude 时沿用
    # 既有 runner 后缀（如 outside-voice codex，历史行为不变，测试兼容）。
    if host not in ("claude", "?"):
        label += f"（{host}宿主/{runner}）"
    elif runner not in ("claude", "?"):
        label += f"（{runner}）"
    return label, g["f"], rate


def semantic_summary(N, M, stage_totals, cost_items, flagged_count, agg_rows):
    """确定性条件模板：把已算好的聚合组织成「## 一览」（精简指标卡 + 语义化中文段落）。

    **只呈现不决策**（本 skill 宪法）：只做数字的语言化复述与结构性对比
    （占几成 / 相差几倍 / 谁最多），绝不含因果归因或取舍建议——模板里不出现
    「说明 / 意味着 / 因此 / 所以 / 应 / 建议 / 该砍」等解读或决策词。指标卡只放
    纯计数（不放平均值：重尾双峰分布下平均会掩盖真相，与聚合②立意冲突）。
    全部分支确定性；无墙钟 / 无锚 / 单 change / 0 待复评 均有降级句，不崩。
    """
    grand = sum(stage_totals.values())
    total_cell = f"~{_fmt_dur(grand)}" if grand > 0 else "—"
    card = [
        "| 复盘 change | 总墙钟 | 有真锚 | 待复评镜 |",
        "|---|---|---|---|",
        f"| {N} | {total_cell} | {M} | {flagged_count} |",
    ]

    # 逐句确定性拼装，每句都是数字的描述性复述
    s1 = f"本轮复盘覆盖 **{N} 个 change**"
    if grand > 0:
        s1 += f"，累计评审墙钟约 **{_fmt_dur(grand)}**"
    s1 += (f"（其中 {M} 个带真实度量锚、可参与价值统计）。" if M
           else "（本轮无带真实度量锚的 change，价值维暂无数据）。")
    sents = [s1]

    if grand > 0:
        top = sorted(stage_totals.items(), key=lambda kv: -kv[1])[:2]
        top_str = "、".join(f"{STAGE_LABELS.get(s, s)} {m / grand:.0%}" for s, m in top)
        s2 = f"评审时间集中在 {top_str}"
        if len(top) == 2:
            s2 += f"（两者合计 {(top[0][1] + top[1][1]) / grand:.0%}）"
        sents.append(s2 + "。")

    valid = [(n, t) for n, t, unresolved in cost_items if t > 0 and not unresolved]
    if len(valid) >= 2:
        hi, lo = max(valid, key=lambda x: x[1]), min(valid, key=lambda x: x[1])
        s3 = (f"单个 change 耗时最重的是 {hi[0]}（约 {_fmt_dur(hi[1])}）、"
              f"最轻的是 {lo[0]}（{_fmt_dur(lo[1])}）")
        # 倍数仅在最轻 change 墙钟 ≥1min 时给：亚分钟 elapsed 是提交时间戳噪声，
        # 拿它当分母算出的倍数无意义（如 0.2min→3769 倍），如实略去不编造。
        if lo[1] >= 1 and hi[1] / lo[1] >= 2:
            s3 += f"，相差约 {round(hi[1] / lo[1])} 倍"
        sents.append(s3 + "。")
    elif len(valid) == 1:
        sents.append(f"仅 {valid[0][0]} 有可解析墙钟（约 {_fmt_dur(valid[0][1])}）。")

    tm = _top_mirror(agg_rows) if M else None
    if tm:
        label, findings, rate = tm
        sents.append(f"价值侧，出问题最多的是 {label}（{findings} 条，采纳率 {rate}）。")

    if flagged_count:
        sents.append(f"另有 {flagged_count} 面镜达到待复评轮数阈值，详见下方 ⚠️ 待复评区块。")

    return "\n".join(["## 一览", "", *card, "", "".join(sents), ""])


def build_report(root):
    """组装全项目 change 成本×价值复盘报告（view-only 再生，无持久状态）。

    顶部覆盖计数「覆盖 N change / 有真锚 M / 边界不可解析 K」——M 必须显性
    （避免样本量 N 被误当趋势看：实测常见 M << N）。per-change 表含 hr-tg 双列
    + in-progress 标记；聚合段①阶段占比②成本双峰③per-镜价值表（内嵌
    lens_metric_aggregate 的整表聚合输出，扫 archive）。
    """
    changes = discover_changes(root)
    seed = seed_mass_shas(root)
    rows, M, K = [], 0, 0
    stage_totals = {}
    for name, info in sorted(changes.items()):
        b = boundary_for_change(root, name, info, seed)
        wt = stage_walltimes(root, name, b["commits"]) if not b["unresolved"] else \
            {"stages": {}, "total_min": 0.0, "n_ckpt": len(b["commits"]), "reorder_suspected": False}
        val = lens_value_for_change(info)
        hr = hr_tg_flags(info)
        if val["has_anchor"]:
            M += 1
        if b["unresolved"]:
            K += 1
        for stage, minutes in wt["stages"].items():
            stage_totals[stage] = stage_totals.get(stage, 0.0) + minutes
        rows.append((name, info, b, wt, val, hr))
    N = len(changes)

    # 一览段入参（确定性）：待复评镜数与 surfacing_block 同源（surfacing_counts），
    # agg_rows 复用 LMA.aggregate（deterministic、幂等；archive 扫描是毫秒级，与
    # 聚合③各自独立调用不影响结果一致性）。
    _c, flagged, _thr = surfacing_counts(root)
    cost_items = [(nm, w["total_min"], bb["unresolved"]) for nm, _inf, bb, w, _v, _h in rows]
    summary_agg, _na, _pf = LMA.aggregate(os.path.join(root, "openspec", "changes", "archive"))
    summary_md = semantic_summary(N, M, stage_totals, cost_items, len(flagged), summary_agg)

    lines = ["# 全项目 change 成本×价值复盘（view-only 再生）", "",
             f"> 覆盖 {N} change / 有真锚 {M} / 边界不可解析 {K}",
             "> 阶段墙钟为「阶段级 elapsed（含人读/拍板/生成时间）」口径（adr/0009），非纯 agent 耗时。",
             "", surfacing_block(root), "", summary_md]

    # per-change 表
    lines.append("## per-change 明细")
    lines.append("")
    # [impl-review-fix F12] 补 design.md schema（约 103-105 行）承诺的 4 个阶段 Δ 列，
    # 插在 总墙钟 与 #ckpt 之间（对齐 design 列序）——F1 修复边界解析后 wt["stages"]
    # 现在对归档 change 有真实非零值，此列才变得有意义。
    # [task4] tokens 列（读 token-log.jsonl，Δ 归属见 compute_token_deltas）——插在 独立Σ 与
    # 状态 之间，紧邻其余度量列，状态列殿后。
    lines.append("| change | 总墙钟(min) | spec-rev Δ | impl Δ | code-rev Δ | done Δ | #ckpt | "
                 "spec_hr_tg | code_hr_tg | Σfindings | 采纳率 | 独立Σ | tokens | 状态 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    token_deltas = compute_token_deltas(root, changes)
    for name, info, b, wt, val, hr in rows:
        status = "in-progress" if info["active"] and not info["archive_dir"] else "archived"
        note = "（边界不可解析）" if b["unresolved"] else ""
        rate = "无度量锚" if not val["has_anchor"] else f'{val["accept_rate"]}'
        # [impl-review-fix F3] num_bad 时行级追加 ⚠数值非法标记，与聚合③（render_table）
        # 对同一批坏锚的呈现口径一致——不能一张表打 flag、另一张悄悄看着正常。
        if val["has_anchor"] and val.get("num_bad"):
            rate += " ⚠数值非法"
        tokens_cell = format_tokens_cell(token_deltas.get(name))
        lines.append(f'| {name} | {wt["total_min"]}{note} | '
                     f'{_stage_col(wt, "spec-review")} | {_stage_col(wt, "impl")} | '
                     f'{_stage_col(wt, "code-review")} | {_stage_col(wt, "done")} | '
                     f'{wt["n_ckpt"]} | '
                     f'{hr["spec_hr_tg"]} | {hr["code_hr_tg"]} | '
                     f'{val["sum_findings"] if val["has_anchor"] else "—"} | {rate} | '
                     f'{val["sum_independent"] if val["has_anchor"] else "—"} | {tokens_cell} | {status} |')
    lines.append("")
    lines.append(_TOKEN_FOOTNOTE)
    lines.append("")

    # 聚合①阶段占比
    lines.append("## 聚合① 阶段占比")
    lines.append("")
    grand_total = sum(stage_totals.values())
    if grand_total > 0:
        lines.append("| 阶段 | 墙钟(min) | 占比 |")
        lines.append("|---|---|---|")
        for stage, minutes in sorted(stage_totals.items(), key=lambda kv: -kv[1]):
            pct = f"{minutes / grand_total:.0%}"
            lines.append(f"| {stage} | {round(minutes, 1)} | {pct} |")
    else:
        lines.append("> 无可用阶段墙钟数据（全部边界不可解析或无 change）。")
    lines.append("")

    # 聚合②成本双峰：总墙钟 x vs code-review 占比 y
    lines.append("## 聚合② 成本双峰（总墙钟 x / code-review 占比% y）")
    lines.append("")
    lines.append("| change | 总墙钟(min) | code-review 占比 |")
    lines.append("|---|---|---|")
    for name, info, b, wt, val, hr in rows:
        total = wt["total_min"]
        cr = wt["stages"].get("code-review", 0.0)
        pct = f"{cr / total:.0%}" if total else "—"
        lines.append(f"| {name} | {total} | {pct} |")
    lines.append("")

    # 聚合③ per-镜价值表（内嵌 lens_metric_aggregate 整表聚合）
    lines.append("## 聚合③ per-镜价值表（lens-metric 聚合，扫 archive）")
    lines.append("")
    archive_root = os.path.join(root, "openspec", "changes", "archive")
    # [T61] 同上：aggregate 显式契约保证缺失/非目录 archive 返空不抛，render_table 对空
    # rows 产出仅含表头 + 空样本脚注的合法表——无需防御性 try/except（原 catch 不可达）。
    agg_rows, no_anchor, parse_failed = LMA.aggregate(archive_root)
    lines.append(LMA.render_table(agg_rows, no_anchor, parse_failed))
    lines.append("")

    # 聚合④ per-镜实修率（历史回算，窄文法扫 archive finding 行）
    lines.append("## 聚合④ per-镜实修率（历史回算）")
    lines.append("")
    fr_rows, fr_lens_unknown = fixrate_aggregate(root)
    lines.append(render_fixrate_table(fr_rows, fr_lens_unknown))
    lines.append("")

    return "\n".join(lines) + "\n"


def atomic_write(path, text):
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        try:
            mode = os.stat(path).st_mode & 0o777
        except FileNotFoundError:
            mode = 0o644
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)
    md = build_report(root)
    out = os.path.join(root, "openspec", "retro", "report.md")
    atomic_write(out, md)
    print(f"[sdflow-retro] 复盘报告已再生 → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
