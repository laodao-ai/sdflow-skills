"""守两个评审 SKILL 的 async host 调度段【逐字节相同】。

【为什么需要这个测试】
async 分支被【复制】进 sdflow-spec-review / sdflow-code-review 两个 SKILL.md。
两份若漂 —— 一个宿主路径会静默行为分叉（退出码判读 / barrier 语义 / 降级口径不一致），
而这是 load-bearing 的正确性，不是风格问题。
—— CLAUDE.md 基准 1：能用「可固化规则 + 脚本」保证的一致性，MUST 机械化。
   复制是必要的（两个 SKILL 是独立分发单元），但复制【不能靠手】。

【语法面】
只认两个 marker token（start / end），单行字面量匹配，有界（基准 5）。
MUST NOT 演化成「解析 Markdown 结构」。
"""
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_async_branch_parity as P  # noqa: E402

REPO = Path(__file__).resolve().parents[2]


def _write(tmp_path, name, interior, *, start=P.START_LINE_PREFIX + " x -->",
           end=P.END_LINE):
    p = tmp_path / name
    p.write_text(f"head\n{start}\n{interior}{end}\nfoot\n", encoding="utf-8")
    return p


# ── 真仓状态 ────────────────────────────────────────────────────────────────

def test_repo_sites_are_byte_identical():
    """⭐ 两个评审 SKILL 的 marker 段逐字节一致 —— 漂了就红。"""
    assert P.main([]) == 0


def test_both_sites_carry_the_markers():
    """两处 marker 都真的存在（不是「都没有 ∴ 都一致」的空绿）。"""
    for rel in P.SITES:
        text = (REPO / rel).read_text(encoding="utf-8")
        assert P.START_LINE_PREFIX in text, rel
        assert P.END_LINE in text, rel


def test_interior_is_non_empty():
    """段内正文不是空的 —— 防「把内容删光换个空绿」。

    判据落在【去掉 marker 行后的正文】上：整段恒含两行 marker，拿整段判空恒真。
    """
    for rel in P.SITES:
        assert P.interior(P.extract(REPO / rel)).strip(), rel


def test_interior_names_no_review_skill():
    """圈内 MUST NOT 出现任一评审 SKILL 的文件名 / skill 名（Task 2 约定）。

    同一串字节要在两处【各自语义正确】，∴ 指代对方一律写「另一评审 SKILL」。
    """
    for rel in P.SITES:
        interior = P.extract(REPO / rel)
        for bad in P.FORBIDDEN_IN_INTERIOR:
            assert bad not in interior, f"{rel} 段内出现 {bad}"


# ── 漂移检测 ────────────────────────────────────────────────────────────────

def test_one_byte_difference_is_red(tmp_path):
    a = _write(tmp_path, "a.md", "line one\nline two\n")
    b = _write(tmp_path, "b.md", "line one\nline twO\n")
    assert P.compare([a, b]) == 1


def test_identical_is_green(tmp_path):
    a = _write(tmp_path, "a.md", "line one\nline two\n")
    b = _write(tmp_path, "b.md", "line one\nline two\n")
    assert P.compare([a, b]) == 0


def test_marker_line_text_drift_is_red(tmp_path):
    """marker 起始行自身的文字也参与比对 —— 它承载「圈内放什么」的口径。"""
    a = _write(tmp_path, "a.md", "x\n", start=P.START_LINE_PREFIX + " AAA -->")
    b = _write(tmp_path, "b.md", "x\n", start=P.START_LINE_PREFIX + " BBB -->")
    assert P.compare([a, b]) == 1


# ── marker 形态错误：各自明确报错，MUST NOT 静默放行 ────────────────────────

def _bare(tmp_path, name, body):
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def test_missing_markers_entirely_is_red(tmp_path):
    a = _write(tmp_path, "a.md", "x\n")
    b = _bare(tmp_path, "b.md", "no markers here\n")
    assert P.compare([a, b]) == 1


def test_start_without_end_is_red(tmp_path):
    a = _write(tmp_path, "a.md", "x\n")
    b = _bare(tmp_path, "b.md", f"{P.START_LINE_PREFIX} x -->\nx\n")
    assert P.compare([a, b]) == 1


def test_end_without_start_is_red(tmp_path):
    a = _write(tmp_path, "a.md", "x\n")
    b = _bare(tmp_path, "b.md", f"x\n{P.END_LINE}\n")
    assert P.compare([a, b]) == 1


def test_two_marker_pairs_is_red(tmp_path):
    """出现两对 marker → 报错，MUST NOT 取第一对静默放行。"""
    a = _write(tmp_path, "a.md", "x\n")
    dup = (f"{P.START_LINE_PREFIX} x -->\nx\n{P.END_LINE}\n"
           f"{P.START_LINE_PREFIX} x -->\nx\n{P.END_LINE}\n")
    b = _bare(tmp_path, "b.md", dup)
    assert P.compare([a, b]) == 1


def test_end_before_start_raises(tmp_path):
    """end 在 start 之前 → MUST 抛 MarkerError（而不是「碰巧因为段不等而红」）。

    直接打在 extract 上：走 compare 时「返回空段 ∴ 不等 ∴ 红」会掩盖守卫被删。
    """
    b = _bare(tmp_path, "b.md", f"{P.END_LINE}\nx\n{P.START_LINE_PREFIX} x -->\n")
    with pytest.raises(P.MarkerError):
        P.extract(b)


def test_end_before_start_is_red(tmp_path):
    a = _write(tmp_path, "a.md", "x\n")
    b = _bare(tmp_path, "b.md", f"{P.END_LINE}\nx\n{P.START_LINE_PREFIX} x -->\n")
    assert P.compare([a, b]) == 1


# ── 合成用例：圈内站点名（FORBIDDEN_IN_INTERIOR）────────────────────────────

@pytest.mark.parametrize("bad", P.FORBIDDEN_IN_INTERIOR)
def test_forbidden_token_in_interior_is_red(tmp_path, bad):
    """两侧内容【完全相同】但段内写死了某一侧的语境 → 仍 MUST 红。

    等值门本身拦不住这种（两边一样嘛），靠 FORBIDDEN_IN_INTERIOR 那条分支。
    ∴ 用例必须走 compare()，否则那条分支从未被执行（真仓恰好干净）。
    """
    body = f"派给 {bad} 处理\n"
    a = _write(tmp_path, "a.md", body)
    b = _write(tmp_path, "b.md", body)
    assert P.compare([a, b]) == 1


def test_clean_interior_with_neutral_wording_is_green(tmp_path):
    """对照组：改写成「另一评审 SKILL」即绿 —— 证上条红的原因就是那个 token。"""
    body = "派给另一评审 SKILL 处理\n"
    a = _write(tmp_path, "a.md", body)
    b = _write(tmp_path, "b.md", body)
    assert P.compare([a, b]) == 0


# ── 合成用例：空段 ─────────────────────────────────────────────────────────

def test_empty_interior_is_red(tmp_path):
    """两侧 marker 都在、正文都被删光 → 「都空 ∴ 都一致」MUST NOT 判绿。"""
    a = _write(tmp_path, "a.md", "")
    b = _write(tmp_path, "b.md", "")
    assert P.compare([a, b]) == 1


def test_whitespace_only_interior_is_red(tmp_path):
    """只剩空白也算空 —— 别用一行空格绕过。"""
    a = _write(tmp_path, "a.md", "   \n\n")
    b = _write(tmp_path, "b.md", "   \n\n")
    assert P.compare([a, b]) == 1


# ── start marker token 边界 ────────────────────────────────────────────────

def test_start_prefix_requires_token_boundary(tmp_path):
    """`...:startX -->` 不是 start —— 无 token 边界会误认相邻 token。"""
    b = _bare(tmp_path, "b.md",
              f"<!-- sdflow:async-branch:startX -->\nx\n{P.END_LINE}\n")
    with pytest.raises(P.MarkerError):
        P.extract(b)


def test_start_line_must_close_on_same_line(tmp_path):
    """start 行本行内必须闭合 `-->` —— 半截行不算 marker。"""
    b = _bare(tmp_path, "b.md",
              f"{P.START_LINE_PREFIX}未闭合\nx\n{P.END_LINE}\n")
    with pytest.raises(P.MarkerError):
        P.extract(b)


def test_extract_raises_on_malformed(tmp_path):
    b = _bare(tmp_path, "b.md", "nothing\n")
    try:
        P.extract(b)
    except P.MarkerError:
        return
    raise AssertionError("畸形 marker 必须抛 MarkerError，不得静默返回")


# ── CLI 契约 ───────────────────────────────────────────────────────────────

def test_cli_exits_nonzero_on_drift(tmp_path):
    a = _write(tmp_path, "a.md", "x\n")
    b = _write(tmp_path, "b.md", "y\n")
    r = subprocess.run(
        [sys.executable, str(REPO / "hack" / "check_async_branch_parity.py"),
         str(a), str(b)],
        capture_output=True, text=True, encoding="utf-8")
    assert r.returncode != 0


def test_cli_exits_zero_on_repo():
    r = subprocess.run(
        [sys.executable, str(REPO / "hack" / "check_async_branch_parity.py")],
        capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stdout + r.stderr


def test_setup_sh_runs_the_gate():
    """门必须真被跑到 —— 「存在但没人跑的门」= 不存在的门。"""
    assert "check_async_branch_parity.py" in (REPO / "setup.sh").read_text(
        encoding="utf-8")
