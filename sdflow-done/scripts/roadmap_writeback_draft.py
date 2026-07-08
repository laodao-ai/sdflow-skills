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
