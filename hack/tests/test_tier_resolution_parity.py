"""守四个编排 SKILL 的「宿主/档位解析」核心段【逐字节相同】。

【为什么需要这个测试】
`sdflow-implement`/`sdflow-done`/`sdflow-code-review`/`sdflow-spec-review` 各自的第零步都要做
同一件事（清脏 unset → 预检 resolve-models.sh 可执行 → 捕获退出码后 eval → eval 后校验），这段
文本被【复制】进四个 SKILL.md。四份若漂——某个 skill 的档位解析会静默行为分叉（漏清脏 / 漏预检 /
把空值误判成 unknown），而这是 load-bearing 的正确性，不是风格问题。
—— CLAUDE.md 基准 1：能用「可固化规则 + 脚本」保证的一致性，MUST 机械化。
   复制是必要的（四个 SKILL 是独立分发单元），但复制【不能靠手】。

【语法面】
只认两个 marker token（start / end），单行字面量匹配，有界（基准 5）。
MUST NOT 演化成「解析 Markdown 结构」。
"""
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_tier_resolution_parity as P  # noqa: E402

REPO = Path(__file__).resolve().parents[2]


def _write(tmp_path, name, interior, *, start=P.START_LINE_PREFIX + "x -->",
           end=P.END_LINE):
    p = tmp_path / name
    p.write_text(f"head\n{start}\n{interior}{end}\nfoot\n", encoding="utf-8")
    return p


def _bare(tmp_path, name, body):
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


# ── 真仓状态 ────────────────────────────────────────────────────────────────

def test_repo_sites_are_byte_identical():
    """⭐ 四个编排 SKILL 的宿主/档位解析核心段逐字节一致——漂了就红。"""
    assert P.main([]) == 0


def test_all_four_sites_carry_the_markers():
    """四处 marker 都真的存在（不是「都没有 ∴ 都一致」的空绿）。"""
    assert len(P.SITES) == 4, "本票交付四个 skill 的核心段——site 枚举不应变多变少"
    for rel in P.SITES:
        text = (REPO / rel).read_text(encoding="utf-8")
        assert P.START_LINE_PREFIX in text, rel
        assert P.END_LINE in text, rel


def test_interior_is_non_empty():
    """段内正文不是空的——防「把内容删光换个空绿」。

    判据落在【去掉 marker 行后的正文】上：整段恒含两行 marker，拿整段判空恒真。
    """
    for rel in P.SITES:
        assert P.interior(P.extract(REPO / rel)).strip(), rel


def test_interior_names_no_orchestrating_skill():
    """圈内 MUST NOT 出现任一编排 SKILL 的名字——同一串字节要在四处【各自语义正确】。"""
    for rel in P.SITES:
        interior = P.extract(REPO / rel)
        for bad in P.FORBIDDEN_IN_SEGMENT:
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


def test_three_way_all_identical_is_green(tmp_path):
    """四站点场景的最小可行版本：≥2 个比对面全等仍绿（守 compare() 不是只两两比）。"""
    a = _write(tmp_path, "a.md", "x\n")
    b = _write(tmp_path, "b.md", "x\n")
    c = _write(tmp_path, "c.md", "x\n")
    assert P.compare([a, b, c]) == 0


def test_third_site_drift_is_red(tmp_path):
    """四站点核心断言：前两个一致不能掩盖第三个漂移——每一侧都要真的被比对。"""
    a = _write(tmp_path, "a.md", "x\n")
    b = _write(tmp_path, "b.md", "x\n")
    c = _write(tmp_path, "c.md", "y\n")
    assert P.compare([a, b, c]) == 1


def test_marker_line_text_drift_is_red(tmp_path):
    """marker 起始行自身的文字也参与比对——它承载「圈内放什么」的口径。"""
    a = _write(tmp_path, "a.md", "x\n", start=P.START_LINE_PREFIX + "AAA -->")
    b = _write(tmp_path, "b.md", "x\n", start=P.START_LINE_PREFIX + "BBB -->")
    assert P.compare([a, b]) == 1


# ── marker 形态错误：各自明确报错，MUST NOT 静默放行 ────────────────────────

def test_missing_markers_entirely_is_red(tmp_path):
    a = _write(tmp_path, "a.md", "x\n")
    b = _bare(tmp_path, "b.md", "no markers here\n")
    assert P.compare([a, b]) == 1


def test_start_without_end_is_red(tmp_path):
    a = _write(tmp_path, "a.md", "x\n")
    b = _bare(tmp_path, "b.md", f"{P.START_LINE_PREFIX}x -->\nx\n")
    assert P.compare([a, b]) == 1


def test_end_without_start_is_red(tmp_path):
    a = _write(tmp_path, "a.md", "x\n")
    b = _bare(tmp_path, "b.md", f"x\n{P.END_LINE}\n")
    assert P.compare([a, b]) == 1


def test_two_marker_pairs_is_red(tmp_path):
    """出现两对 marker → 报错，MUST NOT 取第一对静默放行。"""
    a = _write(tmp_path, "a.md", "x\n")
    dup = (f"{P.START_LINE_PREFIX}x -->\nx\n{P.END_LINE}\n"
           f"{P.START_LINE_PREFIX}x -->\nx\n{P.END_LINE}\n")
    b = _bare(tmp_path, "b.md", dup)
    assert P.compare([a, b]) == 1


def test_end_before_start_raises(tmp_path):
    """end 在 start 之前 → MUST 抛 MarkerError（而不是「碰巧因为段不等而红」）。"""
    b = _bare(tmp_path, "b.md", f"{P.END_LINE}\nx\n{P.START_LINE_PREFIX}x -->\n")
    with pytest.raises(P.MarkerError):
        P.extract(b)


def test_end_before_start_is_red(tmp_path):
    a = _write(tmp_path, "a.md", "x\n")
    b = _bare(tmp_path, "b.md", f"{P.END_LINE}\nx\n{P.START_LINE_PREFIX}x -->\n")
    assert P.compare([a, b]) == 1


# ── 合成用例：圈内站点名（FORBIDDEN_IN_SEGMENT）────────────────────────────

@pytest.mark.parametrize("bad", P.FORBIDDEN_IN_SEGMENT)
def test_forbidden_token_in_interior_is_red(tmp_path, bad):
    """两侧内容【完全相同】但段内写死了某一侧的语境→仍 MUST 红。"""
    body = f"派给 {bad} 处理\n"
    a = _write(tmp_path, "a.md", body)
    b = _write(tmp_path, "b.md", body)
    assert P.compare([a, b]) == 1


def test_clean_interior_with_neutral_wording_is_green(tmp_path):
    """对照组：改写成中性措辞即绿——证上条红的原因就是那个 token。"""
    body = "派给对应 skill 处理\n"
    a = _write(tmp_path, "a.md", body)
    b = _write(tmp_path, "b.md", body)
    assert P.compare([a, b]) == 0


# ── 合成用例：空段 ─────────────────────────────────────────────────────────

def test_empty_interior_is_red(tmp_path):
    a = _write(tmp_path, "a.md", "")
    b = _write(tmp_path, "b.md", "")
    assert P.compare([a, b]) == 1


def test_whitespace_only_interior_is_red(tmp_path):
    a = _write(tmp_path, "a.md", "   \n\n")
    b = _write(tmp_path, "b.md", "   \n\n")
    assert P.compare([a, b]) == 1


# ── start marker token 边界 ────────────────────────────────────────────────

def test_start_prefix_requires_token_boundary(tmp_path):
    """`...:startX -->` 不是 start——无 token 边界会误认相邻 token。"""
    b = _bare(tmp_path, "b.md",
              f"<!-- sdflow:tier-resolution:startX -->\nx\n{P.END_LINE}\n")
    with pytest.raises(P.MarkerError):
        P.extract(b)


def test_start_line_must_close_on_same_line(tmp_path):
    b = _bare(tmp_path, "b.md",
              f"{P.START_LINE_PREFIX}未闭合\nx\n{P.END_LINE}\n")
    with pytest.raises(P.MarkerError):
        P.extract(b)


def test_extract_raises_on_malformed(tmp_path):
    b = _bare(tmp_path, "b.md", "nothing\n")
    with pytest.raises(P.MarkerError):
        P.extract(b)


# ── CLI 契约 ───────────────────────────────────────────────────────────────

def test_cli_exits_nonzero_on_drift(tmp_path):
    a = _write(tmp_path, "a.md", "x\n")
    b = _write(tmp_path, "b.md", "y\n")
    r = subprocess.run(
        [sys.executable, str(REPO / "hack" / "check_tier_resolution_parity.py"),
         str(a), str(b)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode != 0


def test_cli_exits_zero_on_repo():
    r = subprocess.run(
        [sys.executable, str(REPO / "hack" / "check_tier_resolution_parity.py")],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stdout + r.stderr


def test_setup_sh_runs_the_gate():
    """门必须真被跑到——「存在但没人跑的门」= 不存在的门。"""
    assert "check_tier_resolution_parity.py" in (REPO / "setup.sh").read_text(
        encoding="utf-8")


def test_cli_requires_at_least_two_paths(tmp_path):
    a = _write(tmp_path, "a.md", "x\n")
    r = subprocess.run(
        [sys.executable, str(REPO / "hack" / "check_tier_resolution_parity.py"),
         str(a)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode != 0


# ══════════════════════════════════════════════════════════════════════════════
# 段内内容契约（harden-implement-review-loop Task 1）
#
# 等值门只保证「四侧一样」，不保证「一样的那份是对的」。本节是段内**内容**的
# golden：四类清脏变量、fail-loud 硬停措辞、host 空值/unknown 分家判据——MUST NOT
# 只查 SITES[0] 再靠等值门推其余三侧（等值门若被误删，这里就成了盲区）。
# ══════════════════════════════════════════════════════════════════════════════

def _segments():
    return [(rel, P.interior(P.extract(REPO / rel))) for rel in P.SITES]


def test_unset_clears_all_six_vars():
    """(a) 步 MUST 清脏全部六个变量——漏一个就可能拿上一轮的脏值继续跑。"""
    needle = ("先 `unset SDFLOW_HOST SDFLOW_TIER_STRONG SDFLOW_TIER_MID "
              "SDFLOW_TIER_LIGHT SDFLOW_VOICE_RUNNER SDFLOW_VOICE_MODEL` 清脏")
    for rel, seg in _segments():
        assert needle in seg, f"{rel}: 清脏步骤缺失或变量集不全"


def test_precheck_fails_loud_before_continuing():
    """(b) 步：resolver 不可执行 MUST fail-loud 硬停，MUST NOT 继续。"""
    for rel, seg in _segments():
        assert "`[ -x ~/.sdflow/hack/resolve-models.sh ]` 预检" in seg, rel
        assert "fail-loud 硬停本轮工作" in seg, rel
        assert "MUST NOT 继续" in seg, rel


def test_nonzero_exit_halts_before_eval():
    """(c) 步：退出码非 0 MUST fail-loud 硬停，不得继续 eval 一个失败的输出。"""
    for rel, seg in _segments():
        assert "退出码非 0 → fail-loud 硬停" in seg, rel


def test_eval_own_exit_code_is_checked():
    """[impl-review-fix FIX-3] (c) 步：`eval` **自身**的退出码 MUST 立即捕获并检查。

    delta `impl-orchestration/spec.md` 的失败清单第 ② 项是「非零退出**或输出无法 eval**」
    ——只检 resolver 的退出码只做了前半。反例（跨模型 outside-voice 实测构造）：resolver 输出
    **先**设好合法的 host/tiers、**再**跟一条非法命令 ⇒ `eval` 退出码 127，而 (d) 的变量校验
    全 PASS ⇒ 放行一份被截断的解析结果。
    """
    for rel, seg in _segments():
        assert '`eval "$MODELS_ENV"; EVAL_RC=$?`' in seg, f"{rel}: 未捕获 eval 自身退出码"
        assert "**`eval` 自身的退出码 MUST 立即捕获并检查**" in seg, rel
        assert "`EVAL_RC` 非 0 → **fail-loud 硬停**" in seg, rel
        assert "MUST NOT 带着半成品环境继续做 (d) 的变量校验" in seg, rel


def test_empty_host_and_unknown_are_reported_differently():
    """🔴 核心正确性：host 空值 MUST NOT 被吸进 host=unknown 处置——两种失败分开报。"""
    for rel, seg in _segments():
        assert "空值 MUST NOT 回落当 `host=unknown` 处置" in seg, rel
        assert "取到空值 = resolver 根本没跑成" in seg, rel
        assert "unknown = 跑成但判不出宿主、空 = 工具没装没跑成" in seg, rel


def test_tier_required_only_when_host_known():
    """(d) 步：host≠unknown 时才要求三档非空——unknown 本身是合法枚举值。"""
    for rel, seg in _segments():
        assert "host≠unknown 时三 `$SDFLOW_TIER_*` MUST 非空" in seg, rel
        assert "MUST 精确 ∈ {claude,codex,unknown} 且非空" in seg, rel


def test_honest_boundary_declared_not_mechanical_gate():
    """诚实边界：unset/eval/校验是对主 session 的指令，MUST NOT 声称机械门。"""
    for rel, seg in _segments():
        assert "**诚实边界**" in seg, rel
        assert "MUST NOT 声称机械门" in seg, rel


def test_eval_happens_exactly_once_per_round():
    """本轮全程只 eval 一次——后续取值一律读同一次导出的环境变量，不得各自重判宿主。"""
    for rel, seg in _segments():
        assert "本轮全程只 eval 这一次" in seg, rel
        assert "MUST NOT 各自重判宿主" in seg, rel
