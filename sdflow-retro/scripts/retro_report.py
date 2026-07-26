import argparse
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict

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
        capture_output=True, text=True, errors="replace")
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
    ordered = sorted(_STAGE_RULES, key=lambda r: -len(r[0]))
    for candidate in (inner, tail):
        for prefix, stage in ordered:
            if candidate.startswith(prefix):
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

    Args:
        root: 项目根目录
        name: change 名称
        commits: 升序 commit list，每个包含 {"sha", "ts", "subject"}

    Returns:
        {"stages": {stage: minutes}, "total_min": float, "n_ckpt": int, "reorder_suspected": bool}
    """
    stages = {}
    reorder = False

    # 相邻提交差计入前一个提交的阶段
    for i in range(len(commits) - 1):
        cur, nxt = commits[i], commits[i + 1]
        delta_s = nxt["ts"] - cur["ts"]

        # 负数 → 钳 0 且标记 reorder
        if delta_s < 0:
            delta_s = 0
            reorder = True

        # 当前提交的阶段
        if is_archive_rename(root, cur["sha"], name):
            stage = "done"
        else:
            stage = map_stage(cur["subject"])

        # 累加到该阶段（秒转分钟）
        stages[stage] = stages.get(stage, 0.0) + delta_s / 60.0

    # 末提交若是 archive rename，单独标记 done 存在（无后继 Δ）
    if commits and is_archive_rename(root, commits[-1]["sha"], name):
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
    lines.append("| change | 总墙钟(min) | spec-rev Δ | impl Δ | code-rev Δ | done Δ | #ckpt | "
                 "spec_hr_tg | code_hr_tg | Σfindings | 采纳率 | 独立Σ | 状态 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for name, info, b, wt, val, hr in rows:
        status = "in-progress" if info["active"] and not info["archive_dir"] else "archived"
        note = "（边界不可解析）" if b["unresolved"] else ""
        rate = "无度量锚" if not val["has_anchor"] else f'{val["accept_rate"]}'
        # [impl-review-fix F3] num_bad 时行级追加 ⚠数值非法标记，与聚合③（render_table）
        # 对同一批坏锚的呈现口径一致——不能一张表打 flag、另一张悄悄看着正常。
        if val["has_anchor"] and val.get("num_bad"):
            rate += " ⚠数值非法"
        lines.append(f'| {name} | {wt["total_min"]}{note} | '
                     f'{_stage_col(wt, "spec-review")} | {_stage_col(wt, "impl")} | '
                     f'{_stage_col(wt, "code-review")} | {_stage_col(wt, "done")} | '
                     f'{wt["n_ckpt"]} | '
                     f'{hr["spec_hr_tg"]} | {hr["code_hr_tg"]} | '
                     f'{val["sum_findings"] if val["has_anchor"] else "—"} | {rate} | '
                     f'{val["sum_independent"] if val["has_anchor"] else "—"} | {status} |')
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
