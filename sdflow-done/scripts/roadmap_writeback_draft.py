#!/usr/bin/env python3
"""roadmap_writeback_draft.py — sdflow-done roadmap 回填降摩擦助手机械核.

机械搬运（定位到 phase + 盘面读 + 骨架拼），判断（勾哪几行/价值叙述）留人.
切分线: 定位到 phase = 机械（change 名前缀确定性信号）; 勾哪几行 = 判断留人.
stdlib-only, 确定性（无墙钟/随机）, fail-closed.
"""
import argparse
import re
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from pathlib import Path

# change 名前缀 implement-{roadmap}-pN-* ; roadmap 可含横杠, -p\d+ 作定界, 可选尾缀
PREFIX_RE = re.compile(r"^implement-(?P<roadmap>.+)-p(?P<phase>\d+)(?:-.+)?$")


def parse_prefix(change_name):
    """implement-{roadmap}-pN-* → (roadmap, phase); 不符返回 None."""
    m = PREFIX_RE.match(change_name.strip())
    if not m:
        return None
    return (m.group("roadmap"), m.group("phase"))


# marker 整行匹配: <!-- roadmap: {name}#{phase} -->  (name=小写字母数字横杠, phase=数字)
MARKER_RE = re.compile(
    r"^<!--\s*roadmap:\s*(?P<roadmap>[a-z0-9][a-z0-9-]*)#(?P<phase>\d+)\s*-->$"
)


# [impl-review-fix] FIX-1: CommonMark fence 判定, 抄 anchor_lint._FENCE 口径
# 0-3 空格缩进 + ≥3 同字符(` 或 ~) marker; 闭合行须同字符且长度≥开启长度.
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def strip_code_fences(text):
    """去掉 ``` / ~~~ 围栏码块内容(CommonMark fence-aware), 使其中 marker 不被检测.
    [impl-review-fix] FIX-1: 不再用 lstrip()(会吞任意缩进、误判 4+ 空格缩进反引号为 fence);
    改判 0-3 空格缩进 + 记录开启定界符字符/长度, 只有同字符且长度≥开启长度的行才闭合
    (``` 与 ~~~ 混用不会互相提前关闭).
    返回 (stripped_text, unclosed): unclosed=True 表示末态仍在 fence 内(未闭合围栏,
    反静默信号——调用方 MUST 提示人工核对, 不静默漏检 marker)."""
    out = []
    fence = None  # (char, length) | None
    for line in text.splitlines():
        m = _FENCE.match(line)
        if fence is None:
            if m:
                fence = (m.group(1)[0], len(m.group(1)))
                continue
            out.append(line)
        else:
            if (m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1]
                    and line[m.end():].strip() == ""):
                fence = None
            continue
    return "\n".join(out), fence is not None


def detect_markers(text):
    """fence-aware + 行锚定 + 独占一行的 marker 检测(P-5 防自指). 向后兼容:
    只返回 markers 列表(忽略未闭合围栏信号); 需要该信号用 detect_markers_ex."""
    markers, _unclosed = detect_markers_ex(text)
    return markers


def detect_markers_ex(text):
    """同 detect_markers, 但返回 (markers, unclosed_fence_bool)（FIX-1 新增信号出口）.
    fence 内/缩进码块/行内 code/散文行一律忽略."""
    result = []
    stripped_text, unclosed = strip_code_fences(text)
    for line in stripped_text.splitlines():
        if line.startswith("    ") or line.startswith("\t"):
            continue  # markdown 缩进码块
        stripped = line.strip()
        m = MARKER_RE.match(stripped)  # 整行匹配 → 散文/行内 code 不命中
        if m:
            result.append((m.group("roadmap"), m.group("phase")))
    return result, unclosed


FLAG_RE = re.compile(r"^(?P<roadmap>[a-z0-9][a-z0-9-]*)#(?P<phase>\d+)$")


class BadRoadmapFlag(Exception):
    """[impl-review-fix] FIX-2: --roadmap 显式覆写但不符 FLAG_RE 格式.
    调用方 MUST NOT 静默 fallback 到 marker/prefix（T10 裁决：尊重用户显式覆写意图，
    格式错就是错，不该悄悄改用别的关联）——main() 捕获后走独立退出码 7。"""
    pass


def resolve_association(change_name, proposal_text, tasks_text, flag=None):
    """优先级 flag > marker > prefix; 多通道不一致 warn. 无信号返回 None.
    flag 非空但不匹配 FLAG_RE → 抛 BadRoadmapFlag（FIX-2，不静默 fallback）."""
    candidates = {}  # source -> (roadmap, phase)
    prefix = parse_prefix(change_name)
    if prefix:
        candidates["prefix"] = prefix
    # [impl-review-fix] FIX-1: 消费 detect_markers_ex 的 unclosed 信号
    proposal_markers, proposal_unclosed = detect_markers_ex(proposal_text)
    tasks_markers, tasks_unclosed = detect_markers_ex(tasks_text)
    markers = proposal_markers + tasks_markers
    unclosed = proposal_unclosed or tasks_unclosed
    # [impl-review-fix] FIX-5: 同源(proposal+tasks 合并后)多个不同 marker → 取首条但 warn, 不静默
    unique_markers = list(dict.fromkeys(markers))
    multi_marker_warning = None
    if unique_markers:
        candidates["marker"] = unique_markers[0]
        if len(unique_markers) > 1:
            multi_marker_warning = (
                "同源多 marker 不一致: %s，取首条 %s#%s，请人工核对"
                % (
                    ", ".join("%s#%s" % (r, ph) for r, ph in unique_markers),
                    unique_markers[0][0], unique_markers[0][1],
                )
            )
    if flag:
        fm = FLAG_RE.match(flag.strip())
        if not fm:
            raise BadRoadmapFlag(flag)  # [impl-review-fix] FIX-2
        candidates["flag"] = (fm.group("roadmap"), fm.group("phase"))
    if not candidates:
        return None
    for source in ("flag", "marker", "prefix"):
        if source in candidates:
            chosen_source = source
            break
    chosen = candidates[chosen_source]
    warnings = []
    for source, val in candidates.items():
        if val != chosen:
            warnings.append(
                "关联不一致: %s=%s#%s vs 采纳 %s=%s#%s"
                % (source, val[0], val[1], chosen_source, chosen[0], chosen[1])
            )
    if multi_marker_warning:
        warnings.append(multi_marker_warning)  # [impl-review-fix] FIX-5
    if unclosed:
        warnings.append(
            "检测到未闭合代码围栏，marker 检测可能不完整，请人工核对"
        )  # [impl-review-fix] FIX-1
    return {
        "roadmap": chosen[0],
        "phase": chosen[1],
        "source": chosen_source,
        "warnings": warnings,
    }


def read_verify_state(change_dir):
    """读 verify-report.md 首块 frontmatter 里**顶层 ship-gate: 的直接子键** verify.
    返回 (state, value): state ∈ {good, absent, malformed}.
    absent=文件缺/无首块 frontmatter; malformed=未闭合/无顶层 ship-gate 块/该块下无
    verify 直接子键/重复键/坏枚举/文件不可读(FIX-6).
    [impl-review-fix] FIX-3: 不再用宽松 `^\\s*verify:` 扫全块(会误采纳嵌套非 ship-gate
    直接子键的 verify, 如 `note:\\n  verify: PASS`)——只认顶层 ship-gate: 块、且缩进
    恰为其直接子键层的 verify 行(更深嵌套/其它顶层键下的 verify 一律不采纳)."""
    path = Path(change_dir) / "verify-report.md"
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ("absent", None)
    except (OSError, UnicodeDecodeError) as e:  # [impl-review-fix] FIX-6
        sys.stderr.write("VERIFY_REPORT_UNREADABLE %s: %s\n" % (path, e))
        return ("malformed", None)
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ("absent", None)
    fm, closed = [], False
    for line in lines[1:]:
        if line.strip() == "---":
            closed = True
            break
        fm.append(line)
    if not closed:
        return ("malformed", None)
    gate_idx = None
    for i, ln in enumerate(fm):
        if re.match(r"^ship-gate:\s*$", ln):
            gate_idx = i
            break
    if gate_idx is None:
        return ("malformed", None)  # 无顶层 ship-gate 块 → 不采纳任何嵌套 verify
    child_indent = None
    block = []
    for ln in fm[gate_idx + 1:]:
        if ln.strip() == "":
            continue
        indent = len(ln) - len(ln.lstrip(" "))
        if indent == 0:
            break  # 遇到下一个顶层键, ship-gate 块结束
        if child_indent is None:
            child_indent = indent
        if indent == child_indent:
            block.append(ln)  # 只收直接子键层; 更深嵌套(如 note.verify)忽略
    vals = [m.group(1) for m in (re.match(r"^\s*verify:\s*(\S+)\s*$", ln) for ln in block) if m]
    if len(vals) != 1:
        return ("malformed", None)  # 0=无字段, >1=重复键
    if vals[0] not in ("PASS", "FAIL"):
        return ("malformed", None)  # 坏枚举
    return ("good", vals[0])


def read_tasks_completion(change_dir):
    """tasks.md 复选框 (done, total)."""
    path = Path(change_dir) / "tasks.md"
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return (0, 0)
    except (OSError, UnicodeDecodeError) as e:  # [impl-review-fix] FIX-6
        sys.stderr.write("TASKS_MD_UNREADABLE %s: %s\n" % (path, e))
        return (0, 0)
    done = total = 0
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("- [x]") or s.startswith("- [X]"):
            done += 1
            total += 1
        elif s.startswith("- [ ]"):
            total += 1
    return (done, total)


def probe_format(roadmap_text):
    """任一行以 `- [ ]`/`- [x]` 开头 → checkbox; 否则 table-prose(P-3)."""
    for line in roadmap_text.splitlines():
        if re.match(r"^- \[[ xX]\]", line):
            return "checkbox"
    return "table-prose"


def locate_phase_rows(roadmap_text, phase):
    """该 phase(N.*) 下未勾 `- [ ]` 候选行(整行原样); 只 checkbox 式.
    只定位到 phase 行集(机械), 不判勾哪几行(留人)."""
    pat = re.compile(r"^- \[ \] " + re.escape(phase) + r"\.")
    return [ln.rstrip() for ln in roadmap_text.splitlines() if pat.match(ln)]


def assemble_draft(assoc, verify_value, tasks_done, tasks_total, change_name,
                   branch, fmt, candidate_rows, pytest_count=None):
    """拼 hand-off 回填草稿. 机械锚只填步2 已实现事实; archive/merge 静态占位(P-1).
    只列候选行集(机械), 勾哪几行/价值叙述留人(P-2)."""
    roadmap, phase = assoc["roadmap"], assoc["phase"]
    pytest_str = str(pytest_count) if pytest_count is not None else "N/A（纯 Markdown 或未采集）"
    lines = [
        "### ▶ roadmap 回填草稿（%s#%s，关联来源: %s）" % (roadmap, phase, assoc["source"]),
        "",
        "> 助手机械搬运（定位到 phase + 盘面锚），**判断留人**：勾哪几行 / 算不算满足验收标准 / 价值叙述 / 阶段状态 / deferred。",
    ]
    for w in assoc.get("warnings", []):
        lines.append("> ⚠ %s" % w)
    lines += [
        "",
        "**机械锚（步2 已实现事实）**：",
        "- change: `%s`" % change_name,
        "- verify: %s" % verify_value,
        "- tasks 完成态: %d/%d" % (tasks_done, tasks_total),
        "- 分支: `%s`" % branch,
        "- pytest: %s" % pytest_str,
        "- archive 路径: `<待归档后由人补>`  ◀ P-1 预测值不预填",
        "- merge: `<待 merge 后由人补>`",
        "",
    ]
    if fmt == "checkbox":
        if candidate_rows:
            lines.append("**候选复选框行集（phase %s，请人判断勾哪几行）**：" % phase)
            lines.extend(candidate_rows)
        else:
            lines.append("**候选复选框**：phase %s 下未定位到未勾复选框行——请人工核对。" % phase)
    else:
        lines.append("**⚠ fail-loud**：目标 roadmap 为非复选框格式（表格/散文式），助手不产复选框草稿——复选框/状态回填请人工。")
    lines += [
        "",
        "**task-log 完成总结骨架（价值叙述留人补）**：",
        "- [%s] %s#%s：<一句交付摘要，人补> — verify %s, %d/%d tasks, merge `<待补>`"
        % (change_name, roadmap, phase, verify_value, tasks_done, tasks_total),
        "  - 价值（grill/冷审/defer/耗时）：<人补>",
    ]
    return "\n".join(lines)


def _safe_read_text(path):
    """[impl-review-fix] FIX-6: 缺失按空串(既有语义); OSError/UnicodeDecodeError 兜底
    也按空串处理(不裸 traceback)、stderr 记原因供人核对——调用侧(probe_format/marker
    检测等)对空串的 fail-closed/fail-loud 行为已覆盖, 不需要额外状态位。"""
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        sys.stderr.write("FILE_UNREADABLE %s: %s\n" % (path, e))
        return ""


def _git_branch(root):
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True,
            encoding="utf-8", errors="replace")
        return out.stdout.strip()
    except Exception:
        return "<unknown>"


def main(argv=None):
    p = argparse.ArgumentParser(description="roadmap 回填降摩擦助手机械核")
    p.add_argument("--change", required=True)
    p.add_argument("--root", default=".")
    p.add_argument("--roadmap", default=None, help="{name}#{phase} 覆写(优先级最高)")
    p.add_argument("--branch", default=None)
    p.add_argument("--pytest-count", type=int, default=None)
    args = p.parse_args(argv)

    root = Path(args.root)
    change_dir = root / "openspec" / "changes" / args.change
    if not change_dir.exists():
        sys.stderr.write("CHANGE_DIR_MISSING %s\n" % change_dir)
        return 2

    proposal = change_dir / "proposal.md"
    tasks = change_dir / "tasks.md"
    proposal_text = _safe_read_text(proposal)  # [impl-review-fix] FIX-6
    tasks_text = _safe_read_text(tasks)  # [impl-review-fix] FIX-6

    try:
        assoc = resolve_association(args.change, proposal_text, tasks_text, args.roadmap)
    except BadRoadmapFlag as e:  # [impl-review-fix] FIX-2: 不静默 fallback, 独立退出码
        sys.stderr.write(
            "BAD_ROADMAP_FLAG --roadmap 格式不符 %s，未产草稿，请修正\n" % e
        )
        return 7
    if assoc is None:
        sys.stderr.write("NO_ASSOCIATION 未声明关联且名前缀不符 → 退现状(不产草稿)\n")
        return 3

    state, verify_value = read_verify_state(change_dir)
    if state == "absent":
        sys.stderr.write("BOARD_ABSENT verify-report 缺/无 frontmatter → 留人工\n")
        return 4
    if state == "malformed":
        sys.stderr.write("BOARD_MALFORMED verify frontmatter 畸形 → fail-closed 留人工\n")
        return 5
    if verify_value != "PASS":
        sys.stderr.write("VERIFY_NOT_PASS verify=%s → 不出完成候选\n" % verify_value)
        return 6

    roadmap_path = root / "openspec" / "roadmaps" / assoc["roadmap"] / "roadmap.md"
    if not roadmap_path.exists():
        sys.stderr.write("ROADMAP_MISSING %s → 留人工\n" % roadmap_path)
        return 4
    roadmap_text = _safe_read_text(roadmap_path)  # [impl-review-fix] FIX-6
    fmt = probe_format(roadmap_text)
    rows = locate_phase_rows(roadmap_text, assoc["phase"]) if fmt == "checkbox" else []

    tasks_done, tasks_total = read_tasks_completion(change_dir)
    branch = args.branch or _git_branch(root)
    draft = assemble_draft(assoc, verify_value, tasks_done, tasks_total,
                           args.change, branch, fmt, rows, args.pytest_count)
    sys.stdout.write(draft + "\n")
    for w in assoc["warnings"]:
        sys.stderr.write("WARN %s\n" % w)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
