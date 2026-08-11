"""[harden-gate-git-layer Task1 · ADR-1] 录锚层：`reviewed_sha` 是失鲜判定的唯一真相源。

覆盖 tasks 5.6a（缺失）/ 5.6b（格式非法）/ 5.6c（对象不存在或非 commit）/ 5.6d（结论在锚缺），
外加两层校验的分层证据（语法级留在纯文本 parser、语义级在 read_reviewed_sha）与「反推锚已退役」。

口径：退出码类断言一律经 CLI 公共入口（`main()`）求值，不调内部 helper——
`fix-design-gate-freshness-proxy` 的 rename 用例即栽在「只调内部 helper，真洞存在时仍绿」。
"""
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import commit_all, mkchange, head_sha, write_report, sg_frontmatter
from test_gate_preflight import run_gate
from test_gate_impl_progress import approved_change, PLAN2_TICKETS, _sg

GOOD_SHA = "0123456789abcdef0123456789abcdef01234567"   # 语法合法、语义上本仓解析不到


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args],
                          check=True, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()


def _seeded(repo):
    """建一个「四件套已落盘提交」的仓，返回 (change 目录, 被批准盘面的 sha)。"""
    d = mkchange(repo)
    (d / "proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")
    (d / "design.md").write_text("# d\n", encoding="utf-8")
    commit_all(repo, "seed change artifacts")
    return d, head_sha(repo)


# ── 5.6a / 5.6d：锚缺失 ───────────────────────────────────────────────────

def test_missing_anchor_is_unknown_and_names_the_field(repo):
    # 5.6d：结论字段在（design_approved: true）、锚字段缺 → UNKNOWN(6)，诊断点名缺的是 reviewed_sha。
    d, _sha = _seeded(repo)
    write_report(d, "spec-review-report.md", None,       # sha=None ⇒ 不写 reviewed_sha
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report (no anchor)")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert "reviewed_sha" in js["reason"]
    assert js["cause_category"] == "anchor-missing"


def test_missing_anchor_does_not_fall_back_to_inferred_anchor(repo):
    # 5.6a 的承重半场：缺锚 MUST NOT 回退反推式锚。旧实现（report_last_sha）在这个盘面上
    # 能推出锚、判 fresh 并放行到 RUN_PLAN；新实现 MUST 是 UNKNOWN(6)。
    d, _sha = _seeded(repo)
    write_report(d, "spec-review-report.md", None,
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report (no anchor)")
    code, js, _ = run_gate(repo)
    assert js["verdict"] not in ("RUN_PLAN", "CONTINUE_IMPL"), \
        "缺锚竟被放行——存在回退到反推锚（或静默判 fresh）的通路"
    assert code == 6


# ── 5.6b：语法级非法 ──────────────────────────────────────────────────────

BAD_SYNTAX = [
    ("0123456", "缩写 SHA"),
    ("HEAD", "符号式 revision"),
    ("refs/heads/main", "ref 名"),
    ("0123456789ABCDEF0123456789ABCDEF01234567", "大写 hex（非单一规范形）"),
    ("0123456789abcdef0123456789abcdef0123456", "39 位（差一位）"),
    ("0123456789abcdef0123456789abcdef012345678", "41 位（多一位）"),
    ("g123456789abcdef0123456789abcdef01234567", "含非 hex 字符"),
]


@pytest.mark.parametrize("bad,why", BAD_SYNTAX, ids=[c[0][:12] for c in BAD_SYNTAX])
def test_syntactically_invalid_anchor_is_unknown(repo, bad, why):
    d, _sha = _seeded(repo)
    write_report(d, "spec-review-report.md", bad,
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report (bad anchor)")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN", f"{why} 竟未被拦下"
    # [fix1 · F2] 只断 code==6 太弱：missing / unresolvable 两组都断了 cause_category，独缺本组，
    # 于是「生产路径拿到的是通用坏-frontmatter 措辞、无 anchor-invalid 专属诊断」（F1）从这里漏过去。
    # anchor-invalid 原本唯一的强断言在直调内部 helper 的用例里——正是本文件开头口径要防的假绿形态。
    assert js["cause_category"] == "anchor-invalid", f"{why} 未走 anchor-invalid 专属诊断"
    assert "40 位小写 hex" in js["reason"], f"{why} 缺该类专属可行动措辞"


@pytest.mark.parametrize("bad,why", BAD_SYNTAX, ids=[c[0][:12] for c in BAD_SYNTAX])
def test_syntax_layer_lives_in_the_pure_text_parser(bad, why):
    # 分层证据①：语法级校验 MUST 在纯文本函数里完成（live 读与归档 git-show 文本读共用），
    # 不依赖 root / git 调用。坏值 → (field, 'out-of-domain')。
    state, err = _sg.parse_ship_gate_frontmatter(
        sg_frontmatter(bad, design_approved="true"))
    assert state == {} and err == ("reviewed_sha", "out-of-domain"), f"{why} 未在语法层被拒"


def test_syntax_layer_accepts_full_lowercase_oid():
    state, err = _sg.parse_ship_gate_frontmatter(
        sg_frontmatter(GOOD_SHA, design_approved="true"))
    assert err is None and state["reviewed_sha"] == GOOD_SHA
    assert state["design_approved"] is True          # 与结论字段同层、同块解析出来


# ── 5.6c：语义级——对象不存在 / 不是 commit ───────────────────────────────

def test_anchor_object_absent_is_unknown(repo):
    d, _sha = _seeded(repo)
    write_report(d, "spec-review-report.md", GOOD_SHA,   # 语法合法，本仓无此对象
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report (dangling anchor)")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert js["cause_category"] == "anchor-unresolvable"
    assert "force-push" in js["reason"]               # 该类的专属可行动措辞


@pytest.mark.parametrize("kind", ["blob", "tree"])
def test_anchor_pointing_at_non_commit_object_is_unknown(repo, kind):
    # 语法级放行（是真 40 位 OID）、语义级 MUST 拦下：`^{commit}` 后缀使 blob/tree 落进 rc≠0。
    d, _sha = _seeded(repo)
    if kind == "blob":
        oid = _git(repo, "hash-object", "-w", str(d / "proposal.md"))
    else:
        oid = _git(repo, "rev-parse", "HEAD^{tree}")
    assert len(oid) == 40
    write_report(d, "spec-review-report.md", oid,
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, f"spec-review report ({kind} anchor)")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert js["cause_category"] == "anchor-unresolvable"


def test_semantic_layer_reads_valid_anchor(repo):
    # 分层证据②：语义级在 read_reviewed_sha（需 root，做 git 调用）。正例返回锚本身。
    d, sha = _seeded(repo)
    write_report(d, "spec-review-report.md", sha,
                 body="# 设计审报告\n", design_approved="true")
    rel = "openspec/changes/demo/spec-review-report.md"
    assert _sg.read_reviewed_sha(repo, rel) == sha


@pytest.mark.parametrize("anchor,category", [
    (None, "anchor-missing"),
    ("HEAD", "anchor-invalid"),
    (GOOD_SHA, "anchor-unresolvable"),
])
def test_semantic_layer_raises_typed_payload(repo, anchor, category):
    # GateIndeterminate MUST 携带结构化 payload：category 供 main() 机械分派，三类各不相同。
    d, _sha = _seeded(repo)
    write_report(d, "spec-review-report.md", anchor,
                 body="# 设计审报告\n", design_approved="true")
    rel = "openspec/changes/demo/spec-review-report.md"
    with pytest.raises(_sg.GateIndeterminate) as ei:
        _sg.read_reviewed_sha(repo, rel)
    assert ei.value.category == category


def test_indeterminate_reasons_are_mutually_distinguishable():
    # 五类原因各给**各自可行动**的诊断——MUST NOT 用一句「git 调用失败」打天下。
    reasons = {c: _sg._indeterminate_reason(_sg.GateIndeterminate("x", c))
               for c in _sg._INDETERMINATE_ADVICE}
    assert len(set(reasons.values())) == len(reasons), "存在两类原因给出同一句诊断"
    assert len(reasons) >= 5


# ── code 域两个消费方各自覆盖（Compliance：两个消费方 MUST 各有覆盖）──────────

def test_code_review_report_missing_anchor_is_unknown(repo):
    from test_gate_tail import impl_done
    d = impl_done(repo)
    write_report(d, "code-review-report.md", None,
                 body="# 代码审报告\n", code_review="pass")
    commit_all(repo, "cr report (no anchor)")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN" and js["cause_category"] == "anchor-missing"


def test_verify_report_missing_anchor_is_unknown(repo):
    from test_gate_tail import impl_done
    d = impl_done(repo)
    write_report(d, "code-review-report.md", head_sha(repo),
                 body="# 代码审报告\n", code_review="pass")
    write_report(d, "verify-report.md", None,
                 body="# 验证报告\n", verify="PASS")
    commit_all(repo, "reports (verify without anchor)")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN" and js["cause_category"] == "anchor-missing"


# ── 反推锚已退役 ─────────────────────────────────────────────────────────

def test_inferred_anchor_helper_is_gone():
    assert not hasattr(_sg, "report_last_sha"), "反推锚 helper 仍在（退役未完成）"
    src = (Path(__file__).resolve().parents[1] / "scripts" / "ship_gate.py").read_text(
        encoding="utf-8")
    # 只允许出现在「已退役」的说明性注释里，不得有调用点（`report_last_sha(`）。
    assert "report_last_sha(" not in src, "仓内仍有 report_last_sha 调用点"


def test_touching_the_report_does_not_move_the_anchor(repo):
    # 5.5 的核心不变量（本票半场）：锚是**录下来的常量**，任何后续提交顺带碰一下报告文件
    # 都推不动它。旧反推实现在此盘面上会把锚前移到「排版提交」，从而把锚前的设计改动埋掉。
    # ⚠ 本条的变异手段与其余不同源：新实现里没有「反推逻辑」可删（复活 report_last_sha
    #   直接违反 Compliance），故以**旧实现为参照物**做对比——见 impl-report Task1 §变异证明。
    d = approved_change(repo, plan=PLAN2_TICKETS)
    (d / "design.md").write_text("# 拍板后偷改设计\n", encoding="utf-8")
    commit_all(repo, "docs: 改设计（未重审）")
    # 之后有人顺带给报告补了个空行（旧实现：锚前移到这一提交 ⇒ 上面那次改设计被埋掉）
    report = d / "spec-review-report.md"
    report.write_text(report.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    commit_all(repo, "docs: 报告排版")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START", "锚被后续触碰前移，埋掉了未审的设计改动"


# ── 测试基座：两段 / 三段提交模型（tasks 4.1 / 4.1b）─────────────────────

def test_fixture_two_stage_model_puts_artifacts_before_report(repo):
    d = approved_change(repo, plan=PLAN2_TICKETS)
    subjects = _git(repo, "log", "--format=%s").splitlines()
    assert subjects[0] == "spec-review report (approved)"       # 报告单独一段
    assert "seed change artifacts" in subjects                   # 四件套先落盘
    anchor = _sg.read_reviewed_sha(repo, "openspec/changes/demo/spec-review-report.md")
    # 锚指向的提交 MUST 已含被批准的四件套，且 MUST NOT 是报告那一提交
    assert anchor != head_sha(repo)
    assert _git(repo, "cat-file", "-t", anchor) == "commit"
    assert "proposal.md" in _git(repo, "ls-tree", "-r", "--name-only", anchor)


def test_fixture_third_stage_models_pre_approval_revision(repo):
    # 4.1b：三段模型（四件套 → 二次修订 → 报告）。锚指修订**之后** ⇒ 拍板即自洽，不失鲜。
    def revise(d):
        (d / "design.md").write_text("# 拍板前二次修订\n", encoding="utf-8")

    d = approved_change(repo, plan=PLAN2_TICKETS, revise=revise)
    subjects = _git(repo, "log", "--format=%s").splitlines()
    assert "pre-approval revision" in subjects
    code, js, _ = run_gate(repo)
    assert js["verdict"] != "REFUSE_START", "锚含二次修订却仍判失鲜"


def test_fixture_third_stage_can_express_adr7b_selflock(repo):
    # 4.1b 的存在理由：两段模型表达不出 ADR-7(b) 的自锁形态。锚指修订**之前**的提交
    # ⇒ 拍板刚完成、第一次跑 gate 就 REFUSE_START。本用例证明基座能构造出该盘面
    # （守 ADR-7(b) 的完整端到端用例属 5.17，在评审 SKILL 时序票内）。
    def revise(d):
        (d / "design.md").write_text("# 拍板前二次修订（未单独落盘的等价形态）\n",
                                     encoding="utf-8")

    approved_change(repo, plan=PLAN2_TICKETS, revise=revise, anchor="pre-revision")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


# ══ [harden-gate-git-layer Task6 · ADR-7(b) · 测试 5.17] design 域拍板前二次修订，端到端 ══
#
# Step3 checkpoint 之后、拍板回写之前再改 design.md（二次修订）。ADR-7(b) 时序把该修订
# **单独 checkpoint 提交**后再回写锚 ⇒ reviewed_sha 指向**包含**该修订的提交 ⇒ 拍板后首次
# gate 调用不被拒；反之（修订与回写落进同一提交，锚只能取修订前）⇒ 拍板刚完成即 REFUSE_START。
#
# 🔴 变异角色：下方 `_anchored_before_self_locks` 既是 ADR-7(b) 时序纪律的对照物，又是真实的
#   ship_gate design 域守卫变异体——它落在实现窗口（plan 在、无 checkpoint → CONTINUE_IMPL），
#   拆掉 design 域失鲜求值（emit_windowed / ls-tree 映射比较任一）后其 REFUSE_START 断言即转红。

def test_adr7b_second_revision_anchored_after_is_not_refused(repo):
    """[5.17 正例] 二次修订单独落盘、锚指含修订的提交 ⇒ 拍板后首次 gate 不被拒。"""
    def revise(d):
        (d / "design.md").write_text("# 拍板前二次修订（已单独落盘）\n", encoding="utf-8")

    approved_change(repo, plan=PLAN2_TICKETS, revise=revise, anchor="head")
    code, js, _ = run_gate(repo)
    assert js["verdict"] != "REFUSE_START", ("锚含二次修订却仍被拒", js)
    # 落在实现窗口（plan 在、无 checkpoint）→ CONTINUE_IMPL，正常推进
    assert js["verdict"] == "CONTINUE_IMPL", js


def test_adr7b_second_revision_anchored_before_self_locks(repo):
    """[5.17 变异证明] 让锚指向二次修订**之前**的提交（模拟修订与 frontmatter 回写落进同一
    次提交的错误时序）⇒ 修订落在锚之后、且在实现窗口内 ⇒ design 域失鲜 ⇒ 拍板刚完成、第一次
    跑 gate 就 REFUSE_START(exit 3)。本用例即「让锚指向改动前的提交 ⇒ 用例变红」的落地。"""
    def revise(d):
        (d / "design.md").write_text("# 拍板前二次修订（未单独落盘的等价形态）\n",
                                     encoding="utf-8")

    approved_change(repo, plan=PLAN2_TICKETS, revise=revise, anchor="pre-revision")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START", js
