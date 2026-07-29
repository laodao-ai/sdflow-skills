"""断言两个评审 SKILL 的 async host 调度段【逐字节相同】。

【守什么】
sdflow-spec-review / sdflow-code-review 各有一段 host 调度逻辑（内层超时解析、
后台能力自探、执行模式矩阵、哨兵 envelope、退出码判读、collect barrier、站点记账）。
这段是【站点无关】的 —— 两处必须逐字一致，否则一个宿主路径静默行为分叉
（如一侧早退落 timeout、另一侧不落），而这是 load-bearing 的正确性。
∴ 用 marker 圈定 + 机械等值门，一次封死漂移面（CLAUDE.md 基准 1 + 面治优先于点补）。

【圈外留什么】
站点枚举 / context 构造 / reuse-guard 门控 / declared-sites 计算 —— 两层这些部分
本就应当不同，圈进来会逼出假一致。

【圈内的两条隐含前提（显式记下，别做暗默假设）】
  (1) 圈内 MUST NOT 出现任一评审 SKILL 的文件名 / skill 名 —— 同一串字节要在两处
      【各自语义正确】，指代对方一律写「另一评审 SKILL」。本脚本机械守（FORBIDDEN_IN_SEGMENT
      —— 查【整段含两行 marker】，因为 start 行本身也参与比对、同样不许写死到某一侧）。
  (2) 段内出现的 `Step3` 在两侧都成立，是因为 sdflow-spec-review 与 sdflow-code-review
      的第三步【恰好同为「合并 / 裁决 barrier」】（code-review 第三步 = 置信过滤 + 综合 +
      对抗裁决，其「第二步半」已写「findings 进 Step3 合并池」）。
      🔴 这是站点无关性的【跨文件前提】—— 若将来任一侧重编步号（第三步不再是合并 barrier），
      本段即失效，必须同时重写两侧，而不是只改一侧再来放宽本门。

【语法面（基准 5：无界不手搓）】
只认两个 marker token，单行字面量匹配 —— 有界，∴ 可手写。
MUST NOT 演化成「解析 Markdown 结构」。

用法：
    python3 hack/check_async_branch_parity.py            # 查仓内两处（CI / pytest / setup.sh）
    python3 hack/check_async_branch_parity.py A.md B.md  # 查指定文件（测试用）
"""
import sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

SITES = [
    "sdflow-spec-review/SKILL.md",
    "sdflow-code-review/SKILL.md",
]

# 尾随空格是 token 边界：没有它，`<!-- sdflow:async-branch:startX ... -->` 这类
# 相邻 token 会被误认作 start（有界语法面 ∴ 边界要写死）。
START_LINE_PREFIX = "<!-- sdflow:async-branch:start "
END_LINE = "<!-- sdflow:async-branch:end -->"


def _is_start(line):
    """start 行 = 前缀（含 token 边界空格）+ 本行内闭合 `-->`。"""
    return line.startswith(START_LINE_PREFIX) and line.rstrip().endswith("-->")

# 圈内不许出现的字样（前提 (1)）—— 出现即说明这段被写死到了某一侧的语境里。
FORBIDDEN_IN_SEGMENT = [
    "sdflow-spec-review",
    "sdflow-code-review",
    "spec-review-report",
    "code-review-report",
]


class MarkerError(Exception):
    """marker 形态畸形 —— 明确报错，MUST NOT 静默放行（缺 marker ≠ 一致）。"""


def extract(path):
    """→ marker 段文本（含 start 行与 end 行本身）。

    start 行自身也参与比对：它承载「圈内该放什么」的口径，漂了同样是漂。
    """
    lines = Path(path).read_text(encoding="utf-8").splitlines(keepends=True)

    starts = [i for i, l in enumerate(lines) if _is_start(l)]
    ends = [i for i, l in enumerate(lines) if l.startswith(END_LINE)]

    if len(starts) != 1 or len(ends) != 1:
        raise MarkerError(
            f"{path}: 期望恰好 1 对 async-branch marker，实得 "
            f"start={len(starts)} end={len(ends)}")
    if ends[0] < starts[0]:
        raise MarkerError(f"{path}: end marker 出现在 start 之前")

    return "".join(lines[starts[0]:ends[0] + 1])


def interior(seg):
    """→ marker 段【去掉首尾 marker 行】后的正文。

    「段是否为空」的判据 MUST 落在正文上：整段永远含两行 marker，
    拿整段判空恒为假 —— 那是个永远不会触发的守卫（= 不存在的守卫）。
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
            print(f"[async-branch-parity] FAIL: {e}", file=sys.stderr)
            return 1

    ref_path, ref = segments[0]
    rc = 0

    # 空段判据逐段施加，不只查 segments[0]：当前两站点场景下字节等值已能兜住
    # （B 空而 A 非空必红），但站点数若变成 1 或 ≥3，只查 ref 就会漏。
    for p, seg in segments:
        if not interior(seg).strip():
            print(f"[async-branch-parity] FAIL: {p} 的 marker 段正文为空",
                  file=sys.stderr)
            rc = 1
    if rc:
        return rc

    for p, seg in segments[1:]:
        if seg != ref:
            print(f"[async-branch-parity] FAIL: async host 调度段已漂移 —— "
                  f"{ref_path} 与 {p} 不逐字节相同", file=sys.stderr)
            _print_first_diff(ref, seg)
            rc = 1

    for p, seg in segments:
        for bad in FORBIDDEN_IN_SEGMENT:
            if bad in seg:
                print(f"[async-branch-parity] FAIL: {p} 的 marker 段内出现 "
                      f"「{bad}」——圈内 MUST 站点无关，指代对方写「另一评审 SKILL」",
                      file=sys.stderr)
                rc = 1

    if rc == 0:
        print(f"[async-branch-parity] ✅ {len(segments)} 处 async host 调度段逐字节一致")
    else:
        print("   修：以一侧为准，把整段（含 marker 行）原样复制到另一侧", file=sys.stderr)
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
        print("[async-branch-parity] FAIL: 至少需要两个比对面", file=sys.stderr)
        return 1
    return compare(paths)


if __name__ == "__main__":
    sys.exit(main())
