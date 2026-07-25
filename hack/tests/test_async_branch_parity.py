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


# ── 合成用例：圈内站点名（FORBIDDEN_IN_SEGMENT）────────────────────────────

@pytest.mark.parametrize("bad", P.FORBIDDEN_IN_SEGMENT)
def test_forbidden_token_in_interior_is_red(tmp_path, bad):
    """两侧内容【完全相同】但段内写死了某一侧的语境 → 仍 MUST 红。

    等值门本身拦不住这种（两边一样嘛），靠 FORBIDDEN_IN_SEGMENT 那条分支。
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


# ══════════════════════════════════════════════════════════════════════════════
# 段内内容契约（enable-codex-background-outside-voice Task 5）
#
# 等值门只保证「两侧一样」，不保证「一样的那份是对的」。本节是段内**内容**的
# golden：一条负向（Codex 同步 300 秒兼容分支已删除）+ 若干条正向（后台通道的调用
# 协议、fallback 闸门、既有不变量）。两侧逐条各断言一次 —— MUST NOT 只查 SITES[0]
# 再靠等值门推另一侧（等值门若被误删，这里就成了单侧盲区）。
# ══════════════════════════════════════════════════════════════════════════════

def _segments():
    return [(rel, P.interior(P.extract(REPO / rel))) for rel in P.SITES]


def _matrix_rows(seg):
    """段内的表格行（有界语法面：只认「trim 后以 | 开头」，MUST NOT 解析 Markdown 结构）。"""
    return [l for l in seg.splitlines() if l.lstrip().startswith("|")]


def test_codex_sync_300s_compat_branch_is_deleted():
    """🔴 负向 golden：执行模式矩阵里 MUST NOT 再有「codex ⇒ 同步 300 秒」那一行。

    该分支已知 efficacy=0（HAE-08 grill-amendment 明写「不得以尽力兼容旧版为由恢复」）。
    判据落在**矩阵行**上：codex 的行里既不许出现 `sync`，也不许出现同步档的 300 秒。
    """
    for rel, seg in _segments():
        for row in _matrix_rows(seg):
            if "codex" not in row:
                continue
            # 先摘掉 `async` 再找 `sync`：`async` 本身含 `sync` 子串，不摘会把
            # 「codex 走 async」误判成「codex 走 sync」（假红，且方向正好相反）。
            assert "sync" not in row.replace("async", ""), \
                f"{rel}: codex 行仍写着 sync —— {row}"
            assert "300" not in row, f"{rel}: codex 行仍带同步 300 秒档 —— {row}"


def test_codex_branch_goes_through_the_background_job_helper():
    """正向：Codex 分支 MUST 调 job helper 的四个子命令，MUST NOT 自己拼 `claude --bg`。"""
    for rel, seg in _segments():
        assert "outside-voice-job.py" in seg, rel
        for sub in ("dispatch", "await", "collect", "cleanup"):
            assert sub in seg, f"{rel}: 段内未出现子命令 {sub}"


def test_codex_branch_gates_auto_fallback_on_unknown_cost():
    """🔴 Task 3 交接 C1：`unknown_cost=true` ⇒ MUST NOT 自动同族 fallback，改报 orphan + cleanup。"""
    for rel, seg in _segments():
        assert "unknown_cost" in seg, rel
        assert "cleanup --run-dir" in seg and "--cancel" in seg, rel
        assert "fallback_allowed" in seg, rel


def test_skill_side_timeout_clamp_is_retained():
    """🔴 Task 2 交接：越界 config MUST 回落默认 900（**不** fail-closed 罢工）。

    job helper 对越界 `--timeout` 是硬拒绝 ⇒ 若 SKILL 侧的 clamp 被删，config 打错一个字
    就从「回落默认」变成「usage-error 罢工」。
    """
    for rel, seg in _segments():
        assert "回落默认 `900`" in seg, rel
        assert "MUST NOT fail-closed 罢工" in seg, rel


def test_barrier_invariants_survive():
    """既有不变量（HAE-09）：RUNNING 不早退、timeout 只由真实 124 产生、回收后不重派。"""
    for rel, seg in _segments():
        assert "MUST NOT 自造轮询循环" in seg, rel
        assert "只允许由实际" in seg and "124" in seg, rel
        assert "MUST NOT 重" in seg, rel                     # 外层回收后不重新 dispatch


def test_stderr_never_reaches_findings_or_the_tracked_report():
    for rel, seg in _segments():
        assert "stderr" in seg
        assert "MUST NOT 逐字转录" in seg, rel


def test_usage_notes_cover_version_policy_preview_and_platform_boundary():
    """使用说明四项 + 两条不可互相替代的分发链。"""
    for rel, seg in _segments():
        assert "2.1.169" in seg, rel
        assert "disableAgentView" in seg, rel
        assert "research preview" in seg or "research-preview" in seg, rel
        assert "POSIX" in seg, rel
        assert "setup.sh" in seg and "sdflow-init update" in seg, rel


# ── marker 段外：dispatch manifest 与锚行契约（两侧各自断言）──────────────────

def test_dispatch_manifest_records_job_id_and_attempt_nonce():
    """Codex 后台 dispatch 的 job id / site / attempt nonce MUST 落 dispatch manifest。"""
    for rel in P.SITES:
        text = (REPO / rel).read_text(encoding="utf-8")
        line = [l for l in text.splitlines() if "dispatch-manifest.tsv" in l and "printf" in l]
        assert line, rel
        joined = "\n".join(line)
        assert "attempt_nonce" in joined or "<attempt-nonce>" in joined, f"{rel}: {joined}"
        assert "job_id" in joined or "<job-id>" in joined, f"{rel}: {joined}"


def test_anchor_line_reason_code_enum_is_unchanged():
    """锚行契约与 `reason_code` 枚举 MUST 保持不变（HAE-09）。"""
    enum = ('reason_code="ok|not-installed|preflight-error|timeout|exec-error|'
            'host-unknown|secret-hit|fallback-unavailable"')
    for rel in P.SITES:
        assert enum in (REPO / rel).read_text(encoding="utf-8"), rel
