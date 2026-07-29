"""test_batch_lint.py — `issues.py batch lint`（mlh-p3-determ-guards Task 3）。

背景（design.md 3.B②，spec 需求③，五镜订正 H1/H4）：`issues/batches.md` 的
`优先级:`/`计划:` 是人写行（Q3 grammar，reindex/batch 绝不覆写），历史上纯靠人肉审阅
是否符合 `P0-P4`/`—` 的前导 token 约定——`batch lint` 是这条约定的只读确定性守卫，
不改一个字节，只在发现语法违规时非零退出并指明批次/字段。

字段级豁免与校验规则（brief 逐字）：
  - 值 == `BATCH_PLACEHOLDER`（`<待填>`）→ 优先级/计划两字段均豁免（D5，合法的
    "未分诊/未填" 状态）。
  - 非占位 `优先级` → `re.match(r"^(P\\d|—)", v.strip())` 取前导 token，token 须
    ∈ `PRIORITIES ∪ {—}`；**匹配后剩余字符串不校验**（H4：`P1 ★` 裸后缀必须过，
    不能要求括号包裹或空后缀）。
  - 非占位 `计划` → 非空白即可。

本文件用 `_write_batches_md`（test_issues.py 同款 helper）手写 batches.md fixture
逐条覆盖坏/过两类样例，外加对仓库真实 `openspec/issues/batches.md` 的回归基线
（含 3 条 `优先级: <待填>` + 1 条 `P1 ★` + `—（已闭合）`），确保 lint 不会把真实
存量数据判假阳。
"""
import subprocess
import sys
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "scripts" / "issues.py")
REPO_ROOT = Path(__file__).parent.parent.parent


def _run_batch_lint(root):
    return subprocess.run(
        [sys.executable, SCRIPT, "--root", str(root), "batch", "lint"],
        capture_output=True, text=True,

        encoding="utf-8",
        errors="replace",)


def _batches_path(root):
    return Path(root) / "openspec" / "issues" / "batches.md"


def _write_batches_md_entry(root, key, priority, plan, title=None):
    """写一份只含单条目的 batches.md（含状态/成员生成行，凑齐真实 grammar 形状）。"""
    title = title or key
    lines = [
        "# Issues 批次注册表\n",
        "\n",
        f"### {key} — {title}\n",
        "状态: PLANNED\n",
        "成员: (生成)\n",
        f"优先级: {priority}\n",
        f"计划: {plan}\n",
        "\n",
    ]
    path = _batches_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


class TestBatchLintRejectsBadPriority:
    def test_non_placeholder_free_text_priority_is_rejected(self, tmp_path):
        _write_batches_md_entry(tmp_path, "b1", priority="高", plan="一句范围")
        proc = _run_batch_lint(tmp_path)
        assert proc.returncode != 0
        assert "b1" in proc.stderr
        assert "优先级" in proc.stderr

    def test_non_placeholder_invalid_token_priority_is_rejected(self, tmp_path):
        _write_batches_md_entry(tmp_path, "b2", priority="PX", plan="一句范围")
        proc = _run_batch_lint(tmp_path)
        assert proc.returncode != 0
        assert "b2" in proc.stderr
        assert "优先级" in proc.stderr

    def test_out_of_range_p_digit_is_rejected(self, tmp_path):
        """regex `P\\d` 本身允许 P0-P9，但 PRIORITIES 只定义到 P4——token 必须真的属于
        PRIORITIES 集合（不是仅仅"形如 P+数字"就放行），P7 须被拒。"""
        _write_batches_md_entry(tmp_path, "b3", priority="P7", plan="一句范围")
        proc = _run_batch_lint(tmp_path)
        assert proc.returncode != 0
        assert "b3" in proc.stderr

    def test_two_digit_p10_is_rejected(self, tmp_path):
        """[impl-review-fix] F3：`^(P\\d|—)` 只匹配 `P` + 一位数字就停——对 `P10`，
        正则会截断匹配出 `P1`（合法 token），P10 被误判通过。P10 不是任何合法优先级，
        必须被拒。"""
        _write_batches_md_entry(tmp_path, "b6", priority="P10", plan="一句范围")
        proc = _run_batch_lint(tmp_path)
        assert proc.returncode != 0
        assert "b6" in proc.stderr

    def test_two_digit_p40_is_rejected(self, tmp_path):
        """同上，`P40` 会被旧正则截断匹配成 `P4`（合法）而误判通过，必须被拒。"""
        _write_batches_md_entry(tmp_path, "b7", priority="P40", plan="一句范围")
        proc = _run_batch_lint(tmp_path)
        assert proc.returncode != 0
        assert "b7" in proc.stderr


class TestBatchLintRejectsBlankPlan:
    def test_non_placeholder_blank_plan_is_rejected(self, tmp_path):
        _write_batches_md_entry(tmp_path, "b4", priority="P1", plan="")
        proc = _run_batch_lint(tmp_path)
        assert proc.returncode != 0
        assert "b4" in proc.stderr
        assert "计划" in proc.stderr

    def test_non_placeholder_whitespace_only_plan_is_rejected(self, tmp_path):
        _write_batches_md_entry(tmp_path, "b5", priority="P1", plan="   ")
        proc = _run_batch_lint(tmp_path)
        assert proc.returncode != 0
        assert "b5" in proc.stderr


class TestBatchLintAcceptsGroundedGoodSamples:
    """样例逐字取自真实 `openspec/issues/batches.md` 现存条目（避免臆造 grammar）。"""

    def test_priority_with_parenthetical_suffix_passes(self, tmp_path):
        _write_batches_md_entry(
            tmp_path, "good1", priority="P2（T10/T11 已 DONE）", plan="一句范围"
        )
        proc = _run_batch_lint(tmp_path)
        assert proc.returncode == 0, proc.stderr

    def test_emdash_with_parenthetical_suffix_passes(self, tmp_path):
        _write_batches_md_entry(tmp_path, "good2", priority="—（已闭合）", plan="一句范围")
        proc = _run_batch_lint(tmp_path)
        assert proc.returncode == 0, proc.stderr

    def test_bare_star_suffix_not_parenthetical_passes(self, tmp_path):
        """H4 关键订正：`P1 ★` 是裸后缀（非括号包裹），前导 token 匹配后剩余绝不校验，
        必须通过——若误用形如 `^(P\\d|—)(（.*）)?$` 的更严格正则会误杀这条真实样例。"""
        _write_batches_md_entry(tmp_path, "good3", priority="P1 ★", plan="一句范围")
        proc = _run_batch_lint(tmp_path)
        assert proc.returncode == 0, proc.stderr

    def test_placeholder_priority_is_exempt(self, tmp_path):
        """D5：优先级也豁免占位符（此前误判只豁免计划，五镜订正 H1 补齐）。"""
        _write_batches_md_entry(tmp_path, "good4", priority="<待填>", plan="一句范围")
        proc = _run_batch_lint(tmp_path)
        assert proc.returncode == 0, proc.stderr

    def test_placeholder_plan_is_exempt(self, tmp_path):
        _write_batches_md_entry(tmp_path, "good5", priority="P1", plan="<待填>")
        proc = _run_batch_lint(tmp_path)
        assert proc.returncode == 0, proc.stderr

    def test_both_fields_placeholder_is_exempt(self, tmp_path):
        _write_batches_md_entry(tmp_path, "good6", priority="<待填>", plan="<待填>")
        proc = _run_batch_lint(tmp_path)
        assert proc.returncode == 0, proc.stderr


class TestBatchLintRegressionOnRealBatchesMd:
    """回归基线：仓库自身真实 `openspec/issues/batches.md` 全部现存条目（19 条，含 3 条
    `优先级: <待填>` + 1 条 `P1 ★` + 2 条 `—（已闭合）`）必须全部通过——lint 规则
    不能把已知合法的存量数据判假阳。"""

    def test_real_batches_md_all_entries_pass(self):
        proc = _run_batch_lint(REPO_ROOT)
        assert proc.returncode == 0, proc.stderr


class TestBatchLintMissingBatchesMdFailsClosed:
    """[impl-review-fix] F1：设计的失败模式表要求 batches.md 缺失 → 报告 + 非零退出。
    此前 `cmd_batch_lint` 经 `_read_batches_lines` 的 missing→[] 语义把"文件不存在"
    静默判成"0 条批次全部通过"、exit 0——本用例复现该假阳并锁死修复后的 fail-closed 行为。"""

    def test_missing_batches_md_nonzero_with_reason(self, tmp_path):
        # tmp_path 下无 openspec/issues/batches.md，也无 openspec/ 目录本身
        proc = _run_batch_lint(tmp_path)
        assert proc.returncode != 0
        assert "batches.md" in proc.stderr


class TestBatchLintNonUtf8BatchesMdFailsClosedCleanly:
    """[impl-review-fix] F2：`_read_batches_lines` 的 `open()/readlines()` 此前无编码错误
    守卫——非 UTF-8 batches.md 会让 `batch lint` 以裸 `UnicodeDecodeError` traceback 崩溃，
    而非干净的 reason + 非零退出。"""

    def test_non_utf8_batches_md_clean_reason_nonzero(self, tmp_path):
        path = _batches_path(tmp_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"# Issues \xe6\xb3\xa8\xe5\x86\x8c\xe8\xa1\xa8\n\xff\xfe bad bytes \n")
        proc = _run_batch_lint(tmp_path)
        assert proc.returncode != 0
        assert "Traceback" not in proc.stderr
        assert "batches.md" in proc.stderr
