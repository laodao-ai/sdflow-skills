#!/usr/bin/env python3
"""roadmap_writeback_draft.py — sdflow-done roadmap 回填降摩擦助手机械核.

机械搬运（定位到 phase + 盘面读 + 骨架拼），判断（勾哪几行/价值叙述）留人.
切分线: 定位到 phase = 机械（change 名前缀确定性信号）; 勾哪几行 = 判断留人.
stdlib-only, 确定性（无墙钟/随机）, fail-closed.
"""
import re
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


def strip_code_fences(text):
    """去掉 ``` / ~~~ 围栏码块内容, 使其中 marker 不被检测."""
    out = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def detect_markers(text):
    """fence-aware + 行锚定 + 独占一行的 marker 检测(P-5 防自指).
    返回 [(roadmap, phase), ...]; fence 内/缩进码块/行内 code/散文行一律忽略."""
    result = []
    for line in strip_code_fences(text).splitlines():
        if line.startswith("    ") or line.startswith("\t"):
            continue  # markdown 缩进码块
        stripped = line.strip()
        m = MARKER_RE.match(stripped)  # 整行匹配 → 散文/行内 code 不命中
        if m:
            result.append((m.group("roadmap"), m.group("phase")))
    return result


FLAG_RE = re.compile(r"^(?P<roadmap>[a-z0-9][a-z0-9-]*)#(?P<phase>\d+)$")


def resolve_association(change_name, proposal_text, tasks_text, flag=None):
    """优先级 flag > marker > prefix; 多通道不一致 warn. 无信号返回 None."""
    candidates = {}  # source -> (roadmap, phase)
    prefix = parse_prefix(change_name)
    if prefix:
        candidates["prefix"] = prefix
    markers = detect_markers(proposal_text) + detect_markers(tasks_text)
    if markers:
        candidates["marker"] = markers[0]
    if flag:
        fm = FLAG_RE.match(flag.strip())
        if fm:
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
    return {
        "roadmap": chosen[0],
        "phase": chosen[1],
        "source": chosen_source,
        "warnings": warnings,
    }


def read_verify_state(change_dir):
    """读 verify-report.md 的 ship-gate frontmatter verify 字段.
    返回 (state, value): state ∈ {good, absent, malformed}.
    absent=文件缺/无首块 frontmatter; malformed=未闭合/无 verify/重复键/坏枚举."""
    path = Path(change_dir) / "verify-report.md"
    if not path.exists():
        return ("absent", None)
    lines = path.read_text(encoding="utf-8").splitlines()
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
    vals = [m.group(1) for m in (re.match(r"^\s*verify:\s*(\S+)\s*$", ln) for ln in fm) if m]
    if len(vals) != 1:
        return ("malformed", None)  # 0=无字段, >1=重复键
    if vals[0] not in ("PASS", "FAIL"):
        return ("malformed", None)  # 坏枚举
    return ("good", vals[0])


def read_tasks_completion(change_dir):
    """tasks.md 复选框 (done, total)."""
    path = Path(change_dir) / "tasks.md"
    if not path.exists():
        return (0, 0)
    done = total = 0
    for line in path.read_text(encoding="utf-8").splitlines():
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
