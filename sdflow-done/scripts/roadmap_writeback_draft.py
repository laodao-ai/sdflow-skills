#!/usr/bin/env python3
"""roadmap_writeback_draft.py — sdflow-done roadmap 回填降摩擦助手机械核.

机械搬运（定位到 phase + 盘面读 + 骨架拼），判断（勾哪几行/价值叙述）留人.
切分线: 定位到 phase = 机械（change 名前缀确定性信号）; 勾哪几行 = 判断留人.
stdlib-only, 确定性（无墙钟/随机）, fail-closed.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from pathlib import Path


# ────────────────────────────── yq(mikefarah) subprocess 薄封装 ──────────────────────────
# [shared-yaml-subset-parser] `read_verify_state` 的 frontmatter **取值**核心委托给外部
# yq 二进制（同 git 的外部二进制先例），MUST NOT `import yaml`（零依赖不变量）。本文件自己
# 内联一份 `_yq()`（各脚本各自内联，不跨脚本 import，见 sdflow-ship/scripts/ship_gate.py
# 同名函数的姊妹实现）。
#
# 【yq 已知局限，实测确认（本机 yq v4.53.3）】`--front-matter=extract` 对没有第二个 `---`
# 的文件，会把首行 `---` 之后的**全部内容**当同一份 YAML 文档处理——若该内容恰好是合法
# YAML（如本文件的 verify-report.md 片段 `ship-gate:\n  verify: PASS\n`），yq **不报错**、
# 静默判定"解析成功"。这与 `read_verify_state` 的既有契约（未闭合 frontmatter → malformed）
# 不兼容，故调 yq **之前**先做一次顶格 `---` 闭合性文本预扫描（`read_verify_state` 内联，
# 非 YAML 解析，只是字面定界符定位——同 sad_schema.frontmatter_end 的定位性质）。
_yq_bin = None  # 进程内缓存


def _yq(expression, file, *, front_matter=False, in_place=False, default=None):
    """yq(mikefarah) subprocess 薄封装（design.md §1 参考实现 + F3 多文档防御，
    对齐 ship_gate.py/impl_route.py/init.py 的加固版）。

    [R7/F2] exit≠0 恒 raise RuntimeError（不吞、不因 default 静默）——「键不存在」（exit 0 +
    stdout=null，走 default）与「解析失败」（exit≠0，含 yq 未安装/身份不对/文件不可读/语法
    错误）是两条不同分支。
    [F6] 身份校验：`--version` 输出须含 `mikefarah`，拒 kislyuk/yq（jq 语法不兼容）。
    [F10] `encoding="utf-8", errors="replace"`——Windows 默认 GBK/cp936 会破坏非 ASCII 内容。
    [F3] 多文档防御：stdout 含一个以上 JSON 值（疑似多文档 YAML）→ raise，不静默只取第一个。
    [R5/F4] frontmatter 模式下、调用方传了非 None 的 `default`（意味着期望 dict 形状）时，
    校验解出的顶层结构须为 dict，非 dict → 视为坏块，返回 default（不静默当作合法标量）。
    本文件唯一调用点查询叶子标量 `.ship-gate.verify`（default=None），此分支实际不触发，
    保留是为了与其余脚本 `_yq()` 的参考签名一致（Task 5 golden test 的比对面）。
    """
    global _yq_bin
    if _yq_bin is None:
        yq = shutil.which("yq")
        if not yq:
            raise RuntimeError(
                "yq 未安装。安装方式：\n"
                "  macOS:   brew install yq\n"
                "  Windows: winget install --id MikeFarah.yq\n"
                "  Linux:   snap install yq")
        vr = subprocess.run([yq, "--version"], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
        if "mikefarah" not in vr.stdout:
            raise RuntimeError(
                "检测到的 yq 不是 mikefarah/yq（可能是 kislyuk/yq）。\n"
                "  请卸载后安装正确版本：\n"
                "  macOS:   brew install yq\n"
                "  Windows: winget install --id MikeFarah.yq\n"
                "  Linux:   snap install yq")
        _yq_bin = yq
    cmd = [_yq_bin]
    if front_matter:
        cmd += [f"--front-matter={'process' if in_place else 'extract'}"]
    if in_place:
        cmd.append("-i")
    else:
        cmd += ["-o", "json"]
    cmd += [expression, str(file)]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"yq failed on {file}: {r.stderr.strip()}")
    if in_place:
        return None
    raw = r.stdout.strip()
    if not raw or raw == "null":
        return default
    decoder = json.JSONDecoder()
    parsed, idx = decoder.raw_decode(raw)
    if raw[idx:].strip():
        raise RuntimeError(f"yq 输出多个 JSON 值（疑似多文档 YAML，不支持）: {raw[:200]!r}")
    if front_matter and not in_place and default is not None:
        if not isinstance(parsed, dict):
            return default
    return parsed

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
    verify 直接子键/坏枚举/文件不可读(FIX-6).

    [shared-yaml-subset-parser] YAML **取值**核心委托给 `_yq()`（design.md 决定），
    Python 侧保留：① frontmatter 闭合性文本预扫描 ② ship-gate 块内 verify 重复键
    预扫描（yq 对重复键静默取最后值，不加预扫描会 fail-open）③ PASS/FAIL 枚举校验。
    """
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
    # 顶格 `---` 闭合性预扫描
    closed = any(ln.strip() == "---" for ln in lines[1:])
    if not closed:
        return ("malformed", None)
    # [impl-review-fix] 重复键预扫描：yq 对重复键静默取最后值，需在 yq 之前拦截。
    # 只扫 frontmatter 块内 ship-gate: 块的直接子键 verify:
    _in_fm = False
    _in_shipgate = False
    _verify_count = 0
    for ln in lines:
        stripped = ln.strip()
        if stripped == "---":
            if not _in_fm:
                _in_fm = True
                continue
            else:
                break
        if not _in_fm:
            continue
        if ln.startswith("ship-gate:"):
            _in_shipgate = True
            continue
        if _in_shipgate:
            if ln and not ln[0].isspace():
                _in_shipgate = False
                continue
            if ln.startswith("  verify:") and not ln.startswith("    "):
                _verify_count += 1
    if _verify_count > 1:
        return ("malformed", None)
    try:
        verify_value = _yq(".ship-gate.verify", path, front_matter=True, default=None)
    except RuntimeError as e:
        sys.stderr.write("VERIFY_REPORT_MALFORMED %s: %s\n" % (path, e))
        return ("malformed", None)
    if verify_value not in ("PASS", "FAIL"):
        return ("malformed", None)
    return ("good", verify_value)


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
