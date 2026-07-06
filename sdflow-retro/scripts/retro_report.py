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
    return subprocess.run(
        ["git", "-C", root, "-c", "core.quotePath=false", *args],
        capture_output=True, text=True, errors="replace").stdout


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
    def _fetch(relpath):
        if not relpath:
            return []
        rel = os.path.relpath(relpath, root)
        cs = git_commits_for_path(root, rel)
        return [c for c in cs if c["sha"] not in seed_shas]
    commits = _fetch(info.get("active_dir"))
    if len(commits) == 0:
        commits = _fetch(info.get("archive_dir"))
    if len(commits) <= 1:
        return {"commits": commits, "unresolved": True,
                "note": f"边界不可解析（提交数={len(commits)}，seed/单步 change）"}
    return {"commits": commits, "unresolved": False, "note": ""}


# 最长前缀词表：按前缀长度降序尝试匹配 checkpoint(<inner>)
_STAGE_RULES = [
    ("impl-review", "code-review"),
    ("final-review", "code-review"),
    ("sdd-final-review", "code-review"),
    ("spec-review", "spec-review"),
    ("design-gate", "spec-review"),
    ("writing-plans", "impl"),
    ("model-baseline", "impl"),
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
    # 最长前缀匹配：规则按前缀长度降序
    for prefix, stage in sorted(_STAGE_RULES, key=lambda r: -len(r[0])):
        if inner.startswith(prefix):
            return stage
    if inner.endswith("-cross-review"):
        return "other"
    return "unknown"


def is_archive_rename(root, sha, name):
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
            if f"changes/{name}/" in src and "changes/archive/" in dst and dst.rstrip("/").find(name) != -1:
                return True
        if status == "D" and any(f"changes/{name}/" in p and "/archive/" not in p for p in paths):
            moved_out = True
        if status == "A" and any(f"changes/archive/" in p and name in p for p in paths):
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
    for a in anchors:
        layer = a.get("layer", "unknown")
        entry = by_layer.setdefault(layer, {"findings": 0, "采纳": 0, "独立": 0})
        f_val, _ = LMA._int(a.get("findings"))
        a_val, _ = LMA._int(a.get("采纳"))
        ind_val, _ = LMA._int(a.get("独立"))
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
    }


def _read_hr_hit(base, report_name):
    if not base:
        return "—"
    fp = os.path.join(base, report_name)
    if not os.path.isfile(fp):
        return "—"
    for line in open(fp, encoding="utf-8", errors="replace"):
        m = _HRTG_RE.search(line)
        if m:
            return m.group(1)
    return "—"


def hr_tg_flags(info):
    def pick(rn):
        for base in (info.get("active_dir"), info.get("archive_dir")):
            hit = _read_hr_hit(base, rn)
            if hit != "—":
                return hit
        return "—"
    return {"spec_hr_tg": pick("spec-review-report.md"),
            "code_hr_tg": pick("code-review-report.md")}


def surfacing_block(root):
    """D12：N≥10 待复评镜 surfacing 机械契约。扫 archive 的 lens-metric 锚，
    按 (layer,lens,runner,site) 分组计「出现轮数」（口径须与 lens_metric_aggregate.
    render_table 一致——直接复用同一分组键，不重复定义）；轮数≥10 的镜在报告顶部
    独立区块列出，固定前缀标记 `⚠️ 待复评:`（可机验，MUST NOT 仅用形容词）。
    无命中也必须输出固定行——防止「长期无命中」被静默省略成死列（同 hr-tg 空箱同理，
    grill-not-skippable 教训：跳过类判定不能不可见）。
    """
    archive_root = os.path.join(root, "openspec", "changes", "archive")
    counts = defaultdict(int)
    try:
        rows, _no_anchor, _parse_failed = LMA.aggregate(archive_root)
        for r in rows:
            counts[LMA.group_key(r)] += 1
    except (OSError, ValueError):
        pass  # archive 不存在/不可读 → 视同无样本，走「无命中」固定行，不崩报告
    flagged = [(k, c) for k, c in counts.items() if c >= 10]
    if not flagged:
        return "⚠️ 待复评: 无（所有镜出现轮数<10）"
    lines = ["⚠️ 待复评: 以下镜出现轮数≥10、只提示不判断不自动砍——人读后自行决定保留/降采样/淘汰:"]
    for (layer, lens, runner, site), c in sorted(flagged):
        lines.append(f"  - {lens}（layer={layer} runner={runner} site={site}，出现轮数 {c}）")
    return "\n".join(lines)


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

    lines = ["# 全项目 change 成本×价值复盘（view-only 再生）", "",
             f"> 覆盖 {N} change / 有真锚 {M} / 边界不可解析 {K}",
             "> 阶段墙钟为「阶段级 elapsed（含人读/拍板/生成时间）」口径（adr/0009），非纯 agent 耗时。",
             "", surfacing_block(root), ""]

    # per-change 表
    lines.append("## per-change 明细")
    lines.append("")
    lines.append("| change | 总墙钟(min) | #ckpt | spec_hr_tg | code_hr_tg | Σfindings | 采纳率 | 独立Σ | 状态 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for name, info, b, wt, val, hr in rows:
        status = "in-progress" if info["active"] and not info["archive_dir"] else "archived"
        note = "（边界不可解析）" if b["unresolved"] else ""
        rate = "无度量锚" if not val["has_anchor"] else f'{val["accept_rate"]}'
        lines.append(f'| {name} | {wt["total_min"]}{note} | {wt["n_ckpt"]} | '
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
    try:
        agg_rows, no_anchor, parse_failed = LMA.aggregate(archive_root)
        lines.append(LMA.render_table(agg_rows, no_anchor, parse_failed))
    except (OSError, ValueError) as e:
        lines.append(f"> 聚合③不可用（{e}）——archive 不存在或不可读，留空。")
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
