"""〔sweep-pool-debt D3/D4〕内容锚层：`reviewed_sha`（监视域 manifest 的 sha256，64-hex）+
`reviewed_manifest`（manifest 的 base64 编码）是失鲜判定的唯一真相源，双字段密码学互锁。

覆盖：缺失（missing）/ 格式非法（invalid，含旧 40-hex 格式锚）/ 与 manifest 不互证（invalid）/
结论在锚缺，外加两层校验的分层证据（语法级留在纯文本 parser、语义级在 `_read_anchor`）与
「反推锚已退役」「锚不再解析为任何 git 对象」。

口径：退出码类断言一律经 CLI 公共入口（`main()`）求值，不调内部 helper——
`fix-design-gate-freshness-proxy` 的 rename 用例即栽在「只调内部 helper，真洞存在时仍绿」。
"""
import base64
import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import commit_all, mkchange, head_sha, write_report, sg_frontmatter, fingerprint
from test_gate_preflight import run_gate
from test_gate_impl_progress import approved_change, PLAN2_TICKETS, _sg

GOOD_SHA = "0123456789abcdef0123456789abcdef01234567"   # 语法合法（40-hex，旧格式）——
                                                          # live 侧现在恰恰因为"是 40 位"而非法


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args],
                          check=True, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()


def _seeded(repo):
    """建一个「四件套已落盘提交」的仓，返回 (change 目录, 该提交 sha)。"""
    d = mkchange(repo)
    (d / "proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")
    (d / "design.md").write_text("# d\n", encoding="utf-8")
    commit_all(repo, "seed change artifacts")
    return d, head_sha(repo)


# ── 5.6a / 5.6d：锚缺失 ───────────────────────────────────────────────────

def test_missing_anchor_is_unknown_and_names_the_field(repo):
    # 5.6d：结论字段在（design_approved: true）、锚字段缺 → UNKNOWN(6)，诊断点名缺的字段。
    d, _sha = _seeded(repo)
    write_report(d, "spec-review-report.md",       # sha=None ⇒ 不写任何锚字段
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report (no anchor)")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert "reviewed_sha" in js["reason"]
    assert js["cause_category"] == "anchor-missing"


def test_missing_manifest_only_is_unknown_and_names_the_field(repo):
    # 双字段互锁：只写 reviewed_sha、不写 reviewed_manifest ⇒ 同样判缺锚。
    d, sha = _seeded(repo)
    real_sha, _manifest = fingerprint(repo, sha, "design")
    write_report(d, "spec-review-report.md", real_sha, None,
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report (sha only, no manifest)")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert "reviewed_manifest" in js["reason"]
    assert js["cause_category"] == "anchor-missing"


def test_missing_anchor_does_not_fall_back_to_inferred_anchor(repo):
    # 5.6a 的承重半场：缺锚 MUST NOT 回退反推式锚。旧实现（report_last_sha）在这个盘面上
    # 能推出锚、判 fresh 并放行到 RUN_PLAN；新实现 MUST 是 UNKNOWN(6)。
    d, _sha = _seeded(repo)
    write_report(d, "spec-review-report.md",
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
    ("0123456789ABCDEF0123456789ABCDEF01234567", "大写 hex（非单一规范形，40 位）"),
    ("0123456789abcdef0123456789abcdef0123456", "39 位（差一位）"),
    ("0123456789abcdef0123456789abcdef012345678", "41 位（多一位）"),
    ("g123456789abcdef0123456789abcdef01234567", "含非 hex 字符（40 位）"),
]


@pytest.mark.parametrize("bad,why", BAD_SYNTAX, ids=[c[0][:12] for c in BAD_SYNTAX])
def test_syntactically_invalid_anchor_is_unknown(repo, bad, why):
    d, _sha = _seeded(repo)
    write_report(d, "spec-review-report.md", bad,
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report (bad anchor)")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN", f"{why} 竟未被拦下"
    # [fix1 · F2] 只断 code==6 太弱：missing 组已断了 cause_category，独缺本组，
    # 于是「生产路径拿到的是通用坏-frontmatter 措辞、无 anchor-invalid 专属诊断」（F1）从这里漏过去。
    assert js["cause_category"] == "anchor-invalid", f"{why} 未走 anchor-invalid 专属诊断"
    assert "64 位小写 hex" in js["reason"], f"{why} 缺该类专属可行动措辞"


@pytest.mark.parametrize("bad,why", BAD_SYNTAX, ids=[c[0][:12] for c in BAD_SYNTAX])
def test_syntax_layer_lives_in_the_pure_text_parser(bad, why):
    # 分层证据①：语法级校验 MUST 在纯文本函数里完成（live 读与归档 git-show 文本读共用），
    # 不依赖 root / git 调用。坏值 → (field, 'out-of-domain')。
    state, err = _sg.parse_ship_gate_frontmatter(
        sg_frontmatter(bad, design_approved="true"))
    assert state == {} and err == ("reviewed_sha", "out-of-domain"), f"{why} 未在语法层被拒"


def test_syntax_layer_accepts_full_lowercase_oid_both_lengths():
    # 〔DT-1 校验分层〕语法层放宽为「40 或 64 位小写 hex」——40-hex（旧归档格式）与
    # 64-hex（新内容锚格式）在**解析层**都合法，语义分流（"64 位是唯一 live 有效格式"）
    # 是 `_read_anchor` 的职责，不是这一层的。
    state40, err40 = _sg.parse_ship_gate_frontmatter(
        sg_frontmatter(GOOD_SHA, design_approved="true"))
    assert err40 is None and state40["reviewed_sha"] == GOOD_SHA
    assert state40["design_approved"] is True          # 与结论字段同层、同块解析出来

    sha64 = "a" * 64
    state64, err64 = _sg.parse_ship_gate_frontmatter(
        sg_frontmatter(sha64, design_approved="true"))
    assert err64 is None and state64["reviewed_sha"] == sha64


# ── 5.6c：语义级——live 侧要求 64-hex + manifest 互证（不再解析任何 git 对象）───

def test_old_format_40_hex_anchor_is_unknown_on_live(repo):
    # 〔sweep-pool-debt〕旧格式（40-hex commit-OID）锚在 live 侧判非法——不再尝试把它解析
    # 为 git 对象（该语义级检查已随内容锚整体删除），而是直接按"不是 64 位"拒绝。manifest
    # 字段须同时给出（任意语法合法值即可，不必真互证）——否则会先撞"锚缺失"，测不到这一格。
    d, sha = _seeded(repo)
    _real_sha, real_manifest = fingerprint(repo, sha, "design")
    write_report(d, "spec-review-report.md", GOOD_SHA, real_manifest,
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report (old 40-hex anchor)")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert js["cause_category"] == "anchor-invalid"
    assert "重跑写锚脚本" in js["reason"]


def test_manifest_not_matching_sha_is_unknown(repo):
    """双字段不互证（64-hex 语法合法，但与 reviewed_manifest 解码后的 sha256 对不上）
    ⇒ UNKNOWN(6)，anchor-invalid。"""
    d, sha = _seeded(repo)
    real_sha, real_manifest = fingerprint(repo, sha, "design")
    tampered_sha = ("0" if real_sha[0] != "0" else "1") + real_sha[1:]   # 翻一位
    write_report(d, "spec-review-report.md", tampered_sha, real_manifest,
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report (tampered anchor)")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert js["cause_category"] == "anchor-invalid"


def test_manifest_not_valid_base64_is_unknown(repo):
    d, sha = _seeded(repo)
    real_sha, _real_manifest = fingerprint(repo, sha, "design")
    write_report(d, "spec-review-report.md", real_sha, "not-base64-!!!",
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report (bad base64 manifest)")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert js["cause_category"] == "anchor-invalid"


def test_semantic_layer_reads_valid_anchor(repo):
    # 分层证据②：语义级在 `_read_anchor`（需 root，做互证）。正例返回锚本身。
    d, sha = _seeded(repo)
    real_sha, real_manifest = fingerprint(repo, sha, "design")
    write_report(d, "spec-review-report.md", real_sha, real_manifest,
                 body="# 设计审报告\n", design_approved="true")
    rel = "openspec/changes/demo/spec-review-report.md"
    assert _sg.read_reviewed_sha(repo, rel) == real_sha


@pytest.mark.parametrize("case", ["missing", "old-40-hex", "tampered"])
def test_semantic_layer_raises_typed_payload(repo, case):
    # GateIndeterminate MUST 携带结构化 payload：category 供 main() 机械分派。
    d, sha = _seeded(repo)
    real_sha, real_manifest = fingerprint(repo, sha, "design")
    if case == "missing":
        write_report(d, "spec-review-report.md",
                     body="# 设计审报告\n", design_approved="true")
        expected = "anchor-missing"
    elif case == "old-40-hex":
        write_report(d, "spec-review-report.md", GOOD_SHA, real_manifest,
                     body="# 设计审报告\n", design_approved="true")
        expected = "anchor-invalid"
    else:
        tampered = ("0" if real_sha[0] != "0" else "1") + real_sha[1:]
        write_report(d, "spec-review-report.md", tampered, real_manifest,
                     body="# 设计审报告\n", design_approved="true")
        expected = "anchor-invalid"
    rel = "openspec/changes/demo/spec-review-report.md"
    with pytest.raises(_sg.GateIndeterminate) as ei:
        _sg.read_reviewed_sha(repo, rel)
    assert ei.value.category == expected


def test_indeterminate_reasons_are_mutually_distinguishable():
    # 各类原因各给**各自可行动**的诊断——MUST NOT 用一句「git 调用失败」打天下。
    reasons = {c: _sg._indeterminate_reason(_sg.GateIndeterminate("x", c))
               for c in _sg._INDETERMINATE_ADVICE}
    assert len(set(reasons.values())) == len(reasons), "存在两类原因给出同一句诊断"
    assert len(reasons) >= 5


# ── code 域两个消费方各自覆盖（Compliance：两个消费方 MUST 各有覆盖）──────────

def test_code_review_report_missing_anchor_is_unknown(repo):
    from test_gate_tail import impl_done
    d = impl_done(repo)
    write_report(d, "code-review-report.md",
                 body="# 代码审报告\n", code_review="pass")
    commit_all(repo, "cr report (no anchor)")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN" and js["cause_category"] == "anchor-missing"


def test_verify_report_missing_anchor_is_unknown(repo):
    from test_gate_tail import impl_done
    d = impl_done(repo)
    sha, manifest = fingerprint(repo, head_sha(repo), "code")
    write_report(d, "code-review-report.md", sha, manifest,
                 body="# 代码审报告\n", code_review="pass")
    write_report(d, "verify-report.md",
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


def test_anchor_never_resolved_as_git_object():
    """〔sweep-pool-debt〕锚已从 commit-sha 把手改为内容 digest——`_read_anchor` 的实现
    MUST NOT 再调用 `cat-file -e ... ^{commit}` 之类把锚值当 git ref 解析的代码。"""
    src = inspect_source(_sg._read_anchor)
    assert "cat-file" not in src and "^{commit}" not in src


def inspect_source(fn):
    import inspect
    return inspect.getsource(fn)


def test_touching_the_report_does_not_move_the_anchor(repo):
    # 5.5 的核心不变量（本票半场）：锚是**录下来的常量**，任何后续提交顺带碰一下报告文件
    # 都推不动它。旧反推实现在此盘面上会把锚前移到「排版提交」，从而把锚前的设计改动埋掉。
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
    # 锚是内容指纹（64-hex），不是任何 commit 对象；仍可核验其对应"被批准盘面"的内容互证
    assert len(anchor) == 64


def test_fixture_third_stage_models_pre_approval_revision(repo):
    # 4.1b：三段模型（四件套 → 二次修订 → 报告）。锚含修订**之后** ⇒ 拍板即自洽，不失鲜。
    def revise(d):
        (d / "design.md").write_text("# 拍板前二次修订\n", encoding="utf-8")

    d = approved_change(repo, plan=PLAN2_TICKETS, revise=revise)
    subjects = _git(repo, "log", "--format=%s").splitlines()
    assert "pre-approval revision" in subjects
    code, js, _ = run_gate(repo)
    assert js["verdict"] != "REFUSE_START", "锚含二次修订却仍判失鲜"


def test_fixture_third_stage_can_express_adr7b_selflock(repo):
    # 4.1b 的存在理由：两段模型表达不出 ADR-7(b) 的自锁形态。锚指修订**之前**的提交
    # ⇒ 拍板刚完成、第一次跑 gate 就 REFUSE_START。
    def revise(d):
        (d / "design.md").write_text("# 拍板前二次修订（未单独落盘的等价形态）\n",
                                     encoding="utf-8")

    approved_change(repo, plan=PLAN2_TICKETS, revise=revise, anchor="pre-revision")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


# ══ [harden-gate-git-layer Task6 · ADR-7(b) · 测试 5.17] design 域拍板前二次修订，端到端 ══

def test_adr7b_second_revision_anchored_after_is_not_refused(repo):
    """[5.17 正例] 二次修订单独落盘、锚含修订的内容指纹 ⇒ 拍板后首次 gate 不被拒。"""
    def revise(d):
        (d / "design.md").write_text("# 拍板前二次修订（已单独落盘）\n", encoding="utf-8")

    approved_change(repo, plan=PLAN2_TICKETS, revise=revise, anchor="head")
    code, js, _ = run_gate(repo)
    assert js["verdict"] != "REFUSE_START", ("锚含二次修订却仍被拒", js)
    # 落在实现窗口（plan 在、无 checkpoint）→ CONTINUE_IMPL，正常推进
    assert js["verdict"] == "CONTINUE_IMPL", js


def test_adr7b_second_revision_anchored_before_self_locks(repo):
    """[5.17 变异证明] 让锚指向二次修订**之前**提交的内容指纹（模拟修订与 frontmatter
    回写落进同一次提交的错误时序）⇒ 修订落在锚之后、且在实现窗口内 ⇒ design 域失鲜 ⇒
    拍板刚完成、第一次跑 gate 就 REFUSE_START(exit 3)。"""
    def revise(d):
        (d / "design.md").write_text("# 拍板前二次修订（未单独落盘的等价形态）\n",
                                     encoding="utf-8")

    approved_change(repo, plan=PLAN2_TICKETS, revise=revise, anchor="pre-revision")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START", js
