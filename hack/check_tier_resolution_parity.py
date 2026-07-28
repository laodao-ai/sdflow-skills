"""断言四个编排 SKILL 的「宿主/档位解析」核心段【逐字节相同】。

【守什么】
`sdflow-implement`/`sdflow-done`/`sdflow-code-review`/`sdflow-spec-review` 四个 SKILL.md 各自在
第零步做同一件事：清脏 unset → 预检 `resolve-models.sh` 可执行 → 捕获退出码后 eval → eval 后校验
`$SDFLOW_HOST`/`$SDFLOW_TIER_*`。这段机制性文本【站点无关】——四处必须逐字一致，否则某个 skill
的档位解析会静默漂出一套不同的失败语义（如漏了空值/unknown 分家、或漏了清脏步骤），而这是
load-bearing 的正确性，不是风格问题。∴ 用 marker 圈定 + 机械等值门，一次封死漂移面
（CLAUDE.md 基准 1 + 面治优先于点补，仿 `check_async_branch_parity.py`）。

【圈外留什么】
每个 skill 引出该段的标题/编号（"3."/"4."/"### 0.4"/`## 第零步`）、host=unknown 后是硬停还是
缩 roster（sdflow-implement 硬停，code-review/spec-review 缩 roster——两者不同构，design H10 明写）、
能力探针协议细节、8 类失败的 problem/cause/fix 表——这些本就应当因 skill 而异，圈进来会逼出假一致
（design：「对齐目标为四步语义，MUST NOT 要求与任一姊妹 skill 逐字相同」）。

【语法面（基准 5：无界不手搓）】
只认两个 marker token，单行字面量匹配——有界，∴ 可手写。MUST NOT 演化成「解析 Markdown 结构」。

用法：
    python3 hack/check_tier_resolution_parity.py            # 查仓内四处（CI / pytest / setup.sh）
    python3 hack/check_tier_resolution_parity.py A.md B.md   # 查指定文件（测试用，≥2 个）
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

SITES = [
    "sdflow-implement/SKILL.md",
    "sdflow-done/SKILL.md",
    "sdflow-code-review/SKILL.md",
    "sdflow-spec-review/SKILL.md",
]

# 尾随空格是 token 边界：没有它，`<!-- sdflow:tier-resolution:startX ... -->` 这类
# 相邻 token 会被误认作 start（有界语法面 ∴ 边界要写死）。
START_LINE_PREFIX = "<!-- sdflow:tier-resolution:start "
END_LINE = "<!-- sdflow:tier-resolution:end -->"

# 圈内不许出现的字样——出现即说明这段被写死到了某一侧的语境里（四站点无关性前提）。
FORBIDDEN_IN_SEGMENT = [
    "sdflow-implement",
    "sdflow-done",
    "sdflow-code-review",
    "sdflow-spec-review",
]


def _is_start(line):
    """start 行 = 前缀（含 token 边界空格）+ 本行内闭合 `-->`。"""
    return line.startswith(START_LINE_PREFIX) and line.rstrip().endswith("-->")


class MarkerError(Exception):
    """marker 形态畸形——明确报错，MUST NOT 静默放行（缺 marker ≠ 一致）。"""


def extract(path):
    """→ marker 段文本（含 start 行与 end 行本身）。

    start 行自身也参与比对：它承载「圈内该放什么」的口径，漂了同样是漂。
    """
    lines = Path(path).read_text(encoding="utf-8").splitlines(keepends=True)

    starts = [i for i, l in enumerate(lines) if _is_start(l)]
    ends = [i for i, l in enumerate(lines) if l.startswith(END_LINE)]

    if len(starts) != 1 or len(ends) != 1:
        raise MarkerError(
            f"{path}: 期望恰好 1 对 tier-resolution marker，实得 "
            f"start={len(starts)} end={len(ends)}")
    if ends[0] < starts[0]:
        raise MarkerError(f"{path}: end marker 出现在 start 之前")

    return "".join(lines[starts[0]:ends[0] + 1])


def interior(seg):
    """→ marker 段【去掉首尾 marker 行】后的正文。

    「段是否为空」的判据 MUST 落在正文上：整段永远含两行 marker，
    拿整段判空恒为假——那是个永远不会触发的守卫（= 不存在的守卫）。
    """
    lines = seg.splitlines(keepends=True)
    return "".join(lines[1:-1])


def compare(paths):
    """→ 0 绿 / 1 红。红时把原因写 stderr。"""
    segments = []
    for p in paths:
        try:
            segments.append((p, extract(p)))
        except MarkerError as e:
            print(f"[tier-resolution-parity] FAIL: {e}", file=sys.stderr)
            return 1

    ref_path, ref = segments[0]
    rc = 0

    # 空段判据逐段施加，不只查 segments[0]。
    for p, seg in segments:
        if not interior(seg).strip():
            print(f"[tier-resolution-parity] FAIL: {p} 的 marker 段正文为空",
                  file=sys.stderr)
            rc = 1
    if rc:
        return rc

    for p, seg in segments[1:]:
        if seg != ref:
            print(f"[tier-resolution-parity] FAIL: 宿主/档位解析核心段已漂移—— "
                  f"{ref_path} 与 {p} 不逐字节相同", file=sys.stderr)
            _print_first_diff(ref, seg)
            rc = 1

    for p, seg in segments:
        for bad in FORBIDDEN_IN_SEGMENT:
            if bad in seg:
                print(f"[tier-resolution-parity] FAIL: {p} 的 marker 段内出现 "
                      f"「{bad}」——圈内 MUST 站点无关", file=sys.stderr)
                rc = 1

    if rc == 0:
        print(f"[tier-resolution-parity] ✅ {len(segments)} 处宿主/档位解析核心段逐字节一致")
    else:
        print("   修：以一侧为准，把整段（含 marker 行）原样复制到其余各侧", file=sys.stderr)
    return rc


def _print_first_diff(a, b):
    la, lb = a.splitlines(), b.splitlines()
    for i in range(max(len(la), len(lb))):
        x = la[i] if i < len(la) else "<段已结束>"
        y = lb[i] if i < len(lb) else "<段已结束>"
        if x != y:
            print(f"   首个不同在段内第 {i + 1} 行：", file=sys.stderr)
            print(f"     A: {x}", file=sys.stderr)
            print(f"     B: {y}", file=sys.stderr)
            return


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    paths = [Path(a) for a in argv] if argv else [REPO / s for s in SITES]
    if len(paths) < 2:
        print("[tier-resolution-parity] FAIL: 至少需要两个比对面", file=sys.stderr)
        return 1
    return compare(paths)


if __name__ == "__main__":
    sys.exit(main())
