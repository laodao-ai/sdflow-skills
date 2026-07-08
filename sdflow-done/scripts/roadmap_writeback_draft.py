#!/usr/bin/env python3
"""roadmap_writeback_draft.py — sdflow-done roadmap 回填降摩擦助手机械核.

机械搬运（定位到 phase + 盘面读 + 骨架拼），判断（勾哪几行/价值叙述）留人.
切分线: 定位到 phase = 机械（change 名前缀确定性信号）; 勾哪几行 = 判断留人.
stdlib-only, 确定性（无墙钟/随机）, fail-closed.
"""
import re

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
