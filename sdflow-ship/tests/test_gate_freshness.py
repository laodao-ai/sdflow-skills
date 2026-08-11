import os
import re
import subprocess, sys
from pathlib import Path

import pytest

from conftest import commit_all, mkchange, head_sha, write_report
from test_gate_preflight import run_gate
from test_gate_impl_progress import approved_change, PLAN2, PLAN2_TICKETS, _sg
from test_gate_tail import impl_done

BASE = "openspec/changes/demo/"
TASKS_REL = BASE + "tasks.md"

def tail_ok(repo):
    # [mlh-p5 Task5] live 迁 frontmatter（原 inline 双锚，产出的 gate verdict 不变）
    d = impl_done(repo)
    (d / "code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: pass\n  reviewed_sha: {head_sha(repo)}\n---\n# 代码审报告\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        f"---\nship-gate:\n  verify: PASS\n  reviewed_sha: {head_sha(repo)}\n---\n# 验证报告\n", encoding="utf-8")
    commit_all(repo, "reports")
    return d

def touch_code(repo, name="src.py"):
    (repo / name).write_text("# code\n", encoding="utf-8")
    commit_all(repo, "code change")

def test_stale_pass_reruns_not_ship(repo):
    d = tail_ok(repo)
    # code-review-report.md 落盘的 reviewed_sha 锚是「报告写盘时的 HEAD」（tail_ok 内部先写文件
    # 再提交），非「tail_ok 返回后的当前 HEAD」（那已是 "reports" 提交本身）——故不用 head_sha(repo)，
    # 直接从已提交文件内容里读回真正写进去的锚值，避免用错时序的假通过。
    anchor_sha = re.search(r"reviewed_sha: (\S+)",
                           (d / "code-review-report.md").read_text(encoding="utf-8")).group(1)
    touch_code(repo)             # 报告后有 openspec/ 外提交
    _, js, _ = run_gate(repo)
    assert js["verdict"] == "RERUN_STALE" and js["next"] == "sdflow-code-review"
    assert js["freshness"] == "stale"  # [impl-review-fix] 裁决项7：freshness 键锚定
    # [impl-review-fix F2] ADR-4：三处 stale 的 emit 都须带 reviewed_sha；此前 code 域漏带。
    assert js["reviewed_sha"] == anchor_sha, \
        "code 域 RERUN_STALE 须带该报告自己的 reviewed_sha 锚（ADR-4），不是当前 HEAD"

def test_stale_fail_reruns_not_exit5(repo):
    d = impl_done(repo)
    anchor_sha = head_sha(repo)   # verify-report.md 的 reviewed_sha 锚（写报告时的 HEAD）
    # [mlh-p5 Task5] live 迁 frontmatter
    (d / "code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: pass\n  reviewed_sha: {anchor_sha}\n---\n# 代码审报告\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        f"---\nship-gate:\n  verify: FAIL\n  reviewed_sha: {anchor_sha}\n---\n# 验证报告\n", encoding="utf-8")
    commit_all(repo, "reports")
    touch_code(repo)             # FAIL 之后修了代码 → 重验不卡死
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RERUN_STALE" and js["next"] == "sdflow-done"
    # [impl-review-fix F2] ADR-4：verify 域 RERUN_STALE 同须带 reviewed_sha。
    assert js["reviewed_sha"] == anchor_sha, \
        "verify 域 RERUN_STALE 须带该报告自己的 reviewed_sha 锚（ADR-4），不是当前 HEAD"

def test_unclosed_verify_frontmatter_keeps_structural_hint(repo):
    # [impl-review-fix OV-2 → harden-gate-git-layer Task1 重新设计] 原用例名
    # test_stale_unclosed_verify_appends_hint，断言 verdict=RERUN_STALE 且 reason 含结构提示。
    # **承载的安全承诺不变**：verify-report 首行 --- 无闭合（parse 判 absent、无有效结论）时，
    # 「未见闭合」这条结构诊断 MUST NOT 被其它分支吞掉。
    # 变的是它落在哪个 verdict 上：新模型下 `reviewed_sha` 与结论字段同一次写入落盘，
    # ∴「无有效结论」⇒ 本就没有锚可读，若仍先求失鲜就会把这个合法中间态判成缺锚 UNKNOWN(6)。
    # gate 遂改为「先定结论、再求失鲜」（与 code-review 读点次序一致）⇒ 该形态落 STEP_IN_PROGRESS，
    # 结构提示由该分支自带的 hint 承载。措辞「结论陈旧」也不再被误加到无结论的报告上（OV-2 本意）。
    d = impl_done(repo)
    (d / "verify-report.md").write_text(
        "---\nship-gate:\n  verify: PASS\n无闭合横线，正文继续\n", encoding="utf-8")   # 首块无闭合 → absent
    commit_all(repo, "verify report (unclosed)")
    touch_code(repo)             # 外部提交 → 使 verify-report 陈旧
    (d / "code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: pass\n  reviewed_sha: {head_sha(repo)}\n---\n# 代码审报告\n", encoding="utf-8")
    commit_all(repo, "code-review report after external change → cr 新鲜")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS" and js["next"] == "sdflow-done"
    assert "未见闭合" in js["reason"]   # 结构提示未被任何先行分支吞掉（本用例的承重点）
    assert "陈旧" not in js["reason"]   # 无有效结论的报告不该被称「结论陈旧」（OV-2 本意）

def test_design_anchor_survives_impl_commits(repo):
    # Q1=B 断言①：实现提交不令 design-approved 失鲜
    approved_change(repo, plan=PLAN2_TICKETS)
    touch_code(repo)
    _, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL"   # 而非 REFUSE_START（链自锁反例）

def test_design_anchor_stale_on_design_edit(repo):
    # Q1=B 断言②：四件套被改 → design-approved 失鲜
    d = approved_change(repo, plan=PLAN2_TICKETS)
    (d / "design.md").write_text("# 拍板后又改了设计\n", encoding="utf-8")
    commit_all(repo, "edit design after approval")
    code, js, _ = run_gate(repo)
    assert code == 3 and "重审" in js["reason"]

def test_uncommitted_report_still_evaluated_by_its_own_anchor(repo):
    # [harden-gate-git-layer Task1 · ADR-1] 原用例名 test_uncommitted_report_is_fresh，
    # 断言 freshness == "uncommitted"。该语义随**反推锚**一并退役：旧实现只能从
    # `git log -1 -- <report>` 反推锚，报告没进过提交 ⇒ 推不出锚 ⇒ 只好特判 uncommitted。
    # 新实现的锚是报告自己录下的 `reviewed_sha`，**与报告有没有进过提交无关**——未提交的
    # 报告照样带得出有效锚，照常参与失鲜求值（Q3=A「人机同权、手写产物合法」由此保住：
    # 手写报告不被拒，只是同样要落锚）。故本用例改为验「未提交的报告仍经其自录锚正常求值」。
    d = impl_done(repo)
    # [mlh-p5 Task5] live 迁 frontmatter（未提交语义靠"从未进 commit"承载，与锚承载格式无关）
    (d / "code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: pass\n  reviewed_sha: {head_sha(repo)}\n---\n# 代码审报告\n", encoding="utf-8")
    (d / "hand-off.md").write_text("x", encoding="utf-8")
    arch = repo / "openspec" / "changes" / "archive" / "2026-07-04-demo"
    arch.mkdir(parents=True); (arch / "p.md").write_text("a", encoding="utf-8")
    commit_all(repo, "tail without verify report")
    # verify-report.md 只写盘，从未进入任何提交
    (d / "verify-report.md").write_text(
        f"---\nship-gate:\n  verify: PASS\n  reviewed_sha: {head_sha(repo)}\n---\n新一轮手写\n", encoding="utf-8")
    code, js, _ = run_gate(repo)
    # 〔H1〕active 存在 → RUN_VERIFY（非 SHIPPED）。未提交的 verify-report 携带指向当前
    # HEAD 的有效锚 ⇒ 正常求值、判 fresh（而非旧的特判 "uncommitted"），且**不**因
    # 「没进过提交」被判缺锚 UNKNOWN——人机同权保住。
    assert code == 0 and js["verdict"] == "RUN_VERIFY"
    assert js["freshness"] == "fresh"

def test_openspec_only_commits_keep_fresh(repo):
    d = tail_ok(repo)
    (d / "hand-off.md").write_text("x", encoding="utf-8")
    commit_all(repo, "handoff only touches openspec")   # 正常尾流不误伤
    _, js, _ = run_gate(repo)
    assert js["verdict"] in ("RUN_VERIFY", "SHIPPED")   # 不得 RERUN_STALE

def test_chinese_named_spec_edit_still_stale(repo):
    # 〔Adv-A / impl-review-fix〕core.quotePath: 拍板后改中文名 spec 路径 → 必须仍判失鲜
    # （git 默认 C-quote 非 ASCII 路径会让裸 startswith 失配 → 静默放行=假✅）
    d = approved_change(repo, plan=PLAN2_TICKETS)
    specs = d / "specs"
    specs.mkdir(exist_ok=True)
    (specs / "功能规格.md").write_text("拍板后偷改设计语义\n", encoding="utf-8")
    commit_all(repo, "docs: 改中文名 spec")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"   # 不因中文名放行

def test_cr_stale_verify_fresh_fail_carries_cr_note(repo):
    # F1 fix 轮：cr 陈旧 + verify 自身新鲜且 FAIL → VERIFY_FAIL 携带 cr 陈旧提示
    d = impl_done(repo)
    # [mlh-p5 Task5] live 迁 frontmatter
    (d / "code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: pass\n  reviewed_sha: {head_sha(repo)}\n---\n# 代码审报告\n", encoding="utf-8")
    commit_all(repo, "cr alone")
    touch_code(repo)             # 触及 src.py → cr 变陈旧
    (d / "verify-report.md").write_text(
        f"---\nship-gate:\n  verify: FAIL\n  reviewed_sha: {head_sha(repo)}\n---\n# 验证报告\n", encoding="utf-8")
    commit_all(repo, "verify alone")   # verify 本身新鲜（其后无提交）
    code, js, _ = run_gate(repo)
    assert code == 5 and js["verdict"] == "VERIFY_FAIL"
    assert js.get("cr_freshness") == "stale"
    assert "code-review 结论亦已陈旧" in js["reason"]

def _git(root, *args, check=True):
    return subprocess.run(["git", "-C", str(root), *args],
                          check=check, capture_output=True, text=True, encoding="utf-8", errors="replace")

def _head(repo):
    return _git(repo, "rev-parse", "HEAD").stdout.strip()

def _write_tasks(repo, data, name="tasks.md"):
    """原始字节写入 change 目录下的文件（不经文本层，保真测试用）。"""
    p = repo / "openspec" / "changes" / "demo" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return p

def _reanchor(repo, d):
    """把 design-approved 锚推到 HEAD（重提交 spec-review-report.md，它不在监视集内）。

    端到端用例必需：`_seed_tasks` 里**新建** tasks.md 的那一提交本身落在锚之后的窗口内，
    而「新建」形态不合格 ⇒ 该帧照判失鲜，会先于待测的翻转帧触发，把用例的结论理由换掉。
    """
    (d / "spec-review-report.md").write_text(
        f"---\nship-gate:\n  design_approved: true\n  reviewed_sha: {head_sha(repo)}\n---\n# 设计审报告 v2\n", encoding="utf-8")
    commit_all(repo, "re-approve design")

def _seed_tasks(repo, data=b"### Task 1: A\n- [ ] s\n"):
    """建一个已有 tasks.md 的 change，返回 (change_dir, 该提交 sha)。"""
    d = approved_change(repo, plan=PLAN2_TICKETS)
    _write_tasks(repo, data)
    commit_all(repo, "seed tasks.md")
    return d, _head(repo)



# ══════════════════════════════════════════════════════════════════════════
# [fix-design-gate-freshness-proxy Task2] 纯勾选框翻转不再撞门
#
# 判据 = 勾选框标记归一化后**逐行等值**（位置对齐，禁 LCS）。归一化只动
# task-list 行首那一个标记，且 fenced code block 内不参与。其余一切差异形态
# （措辞 / 空白 / 行尾 / 段落增删 / 行重排 / 字面量里的方括号）照判失鲜。
# ══════════════════════════════════════════════════════════════════════════

E = _sg._tasks_content_exempt


# ── ⑦a 正例：勾选框翻转（含反向、大写、缩进/空白原样保留）─────────────────

def test_content_exempt_forward_flip():
    assert E(b"### Task 1: A\n- [ ] s\n", b"### Task 1: A\n- [x] s\n") is True

def test_content_exempt_reverse_flip_is_symmetric():
    # 归一化对称：[x] 翻回 [ ] 同样豁免
    assert E(b"- [x] s\n", b"- [ ] s\n") is True

def test_content_exempt_uppercase_marker():
    assert E(b"- [ ] s\n", b"- [X] s\n") is True

def test_content_exempt_multi_line_partial_flip():
    before = b"### Task 1: A\n- [ ] a\n- [ ] b\n### Task 2: B\n- [ ] c\n"
    after  = b"### Task 1: A\n- [x] a\n- [ ] b\n### Task 2: B\n- [x] c\n"
    assert E(before, after) is True

def test_content_exempt_preserves_indent_and_spacing():
    # 归一化只替换标记本身：缩进、标记后空白、行内其余字符一律不触碰。
    # 两版缩进不同（其余全同）⇒ 必须失鲜——若归一化顺手 strip 了空白就会假绿。
    assert E(b"  - [ ] s\n", b"    - [x] s\n") is False
    # 反向：缩进一致时，带缩进的勾选行照样能豁免（不是靠「有缩进就拒」蒙对的）
    assert E(b"  - [ ] s\n", b"  - [x] s\n") is True


# ── ⑦b 负例：勾选框以外的一切差异 ───────────────────────────────────────

def test_content_stale_on_fenced_code_block_flip():
    # fence 内的 `- [ ]` 是代码/示例，不是任务状态 ⇒ 不参与归一化 ⇒ 失鲜
    before = b"# T\n\n```\n- [ ] sample\n```\n"
    after  = b"# T\n\n```\n- [x] sample\n```\n"
    assert E(before, after) is False

def test_content_stale_on_table_and_inline_code_literals():
    # 表格单元格 / 行内反引号里的标记：非行首 task marker ⇒ 不归一化 ⇒ 失鲜
    assert E(b"| a | [ ] |\n", b"| a | [x] |\n") is False
    assert E(b"\xe8\xaf\xb4\xe6\x98\x8e `[ ]` \xe6\xa0\xbc\xe5\xbc\x8f\n",
             b"\xe8\xaf\xb4\xe6\x98\x8e `[x]` \xe6\xa0\xbc\xe5\xbc\x8f\n") is False

def test_content_stale_on_prose_literal_marker():
    assert E(b"before [ ] after\n", b"before [x] after\n") is False

def test_content_stale_when_second_marker_on_same_line_flips_back():
    # 🔴 行首锚定的判别性构造：行首 task marker 正向翻、同行文档字面量反向翻。
    # 若归一化改成「全行替换所有标记」，两版会被抹成同一串 ⇒ 假绿放行。
    before = b"- [ ] \xe5\x86\x99 `[x]` \xe5\x88\xb0\xe6\x96\x87\xe6\xa1\xa3\n"
    after  = b"- [x] \xe5\x86\x99 `[ ]` \xe5\x88\xb0\xe6\x96\x87\xe6\xa1\xa3\n"
    assert E(before, after) is False

def test_content_stale_on_pure_line_reorder():
    # 🔴 零字符改动的纯行重排：LCS/difflib 下删除行与插入行逐字节相同 ⇒ 会被判等值。
    # 判据 MUST 按行号位置对齐比较。
    before = b"- [ ] a\n- [x] b\n"
    after  = b"- [x] b\n- [ ] a\n"
    assert sorted(before.split(b"\n")) == sorted(after.split(b"\n"))   # 前提：多重集相同
    assert E(before, after) is False

def test_content_stale_on_flip_plus_same_line_wording():
    assert E(b"- [ ] \xe5\x86\x99\xe6\x96\x87\xe6\xa1\xa3\n",
             b"- [x] \xe5\x86\x99\xe6\x96\x87\xe6\xa1\xa3\xef\xbc\x88\xe6\x94\xb9\xef\xbc\x89\n") is False

def test_content_stale_on_flip_plus_task_section_added():
    before = b"### Task 1: A\n- [ ] a\n"
    after  = b"### Task 1: A\n- [x] a\n### Task 2: B\n- [ ] b\n"
    assert E(before, after) is False

def test_content_stale_on_flip_plus_task_section_removed():
    before = b"### Task 1: A\n- [ ] a\n### Task 2: B\n- [ ] b\n"
    after  = b"### Task 1: A\n- [x] a\n"
    assert E(before, after) is False

def test_content_stale_on_whitespace_only_change():
    assert E(b"- [ ] s\n", b"- [ ]  s\n") is False
    assert E(b"### Task 1: A\n", b"###  Task 1: A\n") is False

def test_content_stale_on_crlf_and_trailing_newline_and_edge_whitespace():
    assert E(b"- [ ] s\n", b"- [ ] s\r\n") is False        # 行尾
    assert E(b"- [ ] s\n", b"- [ ] s") is False            # 末尾换行删除
    assert E(b"- [ ] s\n", b"- [ ] s\n\n") is False        # 末尾换行新增
    assert E(b"- [ ] s\n", b"  - [ ] s\n   ") is False     # 首尾空白

def test_content_stale_on_line_count_change_alone():
    assert E(b"- [ ] a\n- [ ] b\n", b"- [ ] a\n") is False

def test_content_exempt_conservative_on_unbalanced_fence():
    # 围栏未闭合 ⇒ 「哪些行在 fence 内」不可信 ⇒ 保守判失鲜（同 _line_scoped_hits 口径）
    assert E(b"```\n- [ ] s\n", b"```\n- [x] s\n") is False


# ── ⑦c 端到端：豁免只在监视集恰为 {tasks.md} 时成立 ─────────────────────

def test_e2e_flip_plus_design_edit_still_stale(repo):
    # 同一提交既纯勾选 tasks.md、又改 design.md ⇒ 照判失鲜（豁免资格三连之一）
    d, _ = _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _reanchor(repo, d)
    _write_tasks(repo, b"### Task 1: A\n- [x] s\n")
    (d / "design.md").write_text("# design changed\n", encoding="utf-8")
    commit_all(repo, "docs: 勾选 + 改设计")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"

def test_e2e_tasks_wording_change_still_stale(repo):
    # 勾选框以外的 tasks.md 改动（措辞）⇒ 照判失鲜
    d, _ = _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _reanchor(repo, d)
    _write_tasks(repo, b"### Task 1: A\n- [ ] s2\n")
    commit_all(repo, "docs: 改任务措辞")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"

def test_impl_review_subject_no_longer_buys_any_exemption(repo):
    """[harden-gate-git-layer Task3 · 5.15b] 原 test_e2e_br7_impl_review_subject_exemption_intact
    的**反转等价件**。承载的承诺变了方向、但仍是同一片面：豁免面 MUST NOT 由被监管方
    书写的 subject 决定。

    帧比较退役后 subject 这一维度整体消失（判定只看内容），∴ `checkpoint(impl-review)`
    这个显式越权口不再买得到任何豁免——这是 design.md ADR-3 登记在案的**行为收紧**，
    不是 bug。本例把该收紧钉死，防后人「顺手把 subject 豁免加回来」。
    """
    d = approved_change(repo, plan=PLAN2_TICKETS)
    (d / "design.md").write_text("v1\n", encoding="utf-8")
    commit_all(repo, "checkpoint(impl-review): 收尾修订")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


# ══════════════════════════════════════════════════════════════════════════
# [fix1 Important-1] 勾选框归一化的 fence 口径：`~~~` / 四 backtick 围栏
#
# 旧口径只认 ```：`~~~` 块内 task-list 形状行的**实质改动**被当成块外普通勾选翻转
# ⇒ 豁免误开（fail-open，放行未批准的设计改动）。修法 = 四个 fence 追踪点收敛到
# 单一源 fence_delim/FenceTracker，口径按 CommonMark 有界词法写全。
# ══════════════════════════════════════════════════════════════════════════

def test_content_stale_on_tilde_fenced_code_block_flip():
    # 🔴 Important-1 复现钉：删掉 `~~~` 支持 ⇒ 本例转红（返回 True = 假阳放行）
    assert E(b"~~~\n- [ ] s\n~~~\n", b"~~~\n- [x] s\n~~~\n") is False

def test_content_stale_on_four_backtick_fenced_flip():
    assert E(b"````\n- [ ] s\n````\n", b"````\n- [x] s\n````\n") is False

def test_content_stale_on_tilde_fence_with_info_string():
    assert E(b"~~~python\n- [ ] s\n~~~\n", b"~~~python\n- [x] s\n~~~\n") is False

def test_content_exempt_conservative_on_unbalanced_tilde_fence():
    # `~~~` 未闭合 ⇒ 保守判失鲜（同 ``` 口径）
    assert E(b"~~~\n- [ ] s\n", b"~~~\n- [x] s\n") is False

def test_content_exempt_conservative_when_cross_type_fence_cannot_close():
    # 异种围栏关不掉：~~~ 开、``` 关不上 ⇒ EOF 仍在块内 ⇒ 保守
    assert _sg._normalize_checkbox_lines(b"~~~\n- [ ] s\n```\n") is None

def test_content_exempt_conservative_when_shorter_fence_cannot_close():
    # 闭合符须 ≥ 开启符长度：``` 关不掉 ```` 开的块
    assert _sg._normalize_checkbox_lines(b"````\n- [ ] s\n```\n") is None

def test_normalize_still_works_outside_tilde_fence():
    # 反向证：`~~~` 块外的真勾选行照常归一化（不是靠「见 ~ 就全拒」蒙对的）
    assert E(b"~~~\ncode\n~~~\n- [ ] s\n", b"~~~\ncode\n~~~\n- [x] s\n") is True


# ── [fix1 Important-2] CHECKBOX_RE / CHECKBOX_BYTES_RE 单一源机械守 ──────────

def test_checkbox_re_bytes_derived_from_single_source():
    # 把「口径同源」从注释变成门：手抄一份字节副本并改口径 ⇒ 本例转红
    assert _sg.CHECKBOX_BYTES_RE.pattern == _sg.CHECKBOX_RE.pattern.encode()
    assert _sg.CHECKBOX_RE.pattern == _sg.CHECKBOX_RE_PATTERN

def test_checkbox_str_vs_bytes_nbsp_divergence_is_conservative():
    # 注释订正的机械锚：`\s` 在 str 模式认 Unicode 空白、bytes 模式只认 ASCII。
    # NBSP 缩进行 ⇒ str 版认、bytes 版不认 ⇒ 该行不被归一化 ⇒ 判失鲜（保守方向）。
    nbsp = " - [ ] s"
    assert _sg.CHECKBOX_RE.match(nbsp) is not None
    assert _sg.CHECKBOX_BYTES_RE.match(nbsp.encode("utf-8")) is None
    assert _sg.CHECKBOX_RE.match("\t- [ ] s") is not None
    assert _sg.CHECKBOX_BYTES_RE.match(b"\t- [ ] s") is not None
    assert E(" - [ ] s\n".encode(), " - [x] s\n".encode()) is False


def test_content_criterion_takes_only_content(repo):
    """机械锚：内容判据的入参只有前后两版内容——无 subject、无路径、无文件存在性。

    将来若有人往判据里塞 subject / 路径（把豁免面交回给被监管方书写的声明），本例转红。"""
    import inspect
    assert list(inspect.signature(_sg._tasks_content_exempt).parameters) == ["before", "after"]



# ── F3 归一化：CommonMark 缩进代码块 + HTML 注释块（第三、四支） ─────────────

def test_content_stale_on_indented_code_block_flip():
    # 🔴 四空格缩进代码块内的翻转此前被归一化 ⇒ 误判豁免（fail-open）
    before = b"# T\n\n    - [ ] sample\n"
    after = b"# T\n\n    - [x] sample\n"
    assert E(before, after) is False


def test_content_stale_on_tab_indented_code_block_flip():
    # tab 按 4 列制表位展开 ⇒ 同样落在缩进代码块口径内
    assert E(b"# T\n\n\t- [ ] s\n", b"# T\n\n\t- [x] s\n") is False


def test_content_stale_on_html_comment_block_flip():
    # 多行 HTML 注释块内的翻转 ⇒ 不归一化 ⇒ 失鲜
    before = b"# T\n\n<!--\n- [ ] s\n-->\n"
    after = b"# T\n\n<!--\n- [x] s\n-->\n"
    assert E(before, after) is False


def test_normalize_still_works_outside_indent_and_comment():
    # 反向证（判别性）：不是靠「见缩进/见注释就全拒」蒙对的——
    # 浅缩进（<4 列）与注释块**外**的真勾选行照常归一化。
    assert E(b"  - [ ] s\n", b"  - [x] s\n") is True
    assert E(b"<!-- c -->\n- [ ] s\n", b"<!-- c -->\n- [x] s\n") is True
    assert E(b"<!--\nx\n-->\n- [ ] s\n", b"<!--\nx\n-->\n- [x] s\n") is True


def test_html_comment_tracker_reports_line_start_state():
    t = _sg.HtmlCommentTracker()
    assert t.feed("<!-- open") is False        # 本行行首在注释外
    assert t.feed("- [ ] s") is True           # 已进注释
    assert t.feed("--> tail") is True          # 闭合行的行首仍在注释内
    assert t.feed("- [ ] s") is False          # 之后回到注释外


def test_indent_columns_tab_stop():
    assert _sg.indent_columns("   x") == 3 and _sg.is_indented_code_line("   x") is False
    assert _sg.indent_columns("    x") == 4 and _sg.is_indented_code_line("    x") is True
    assert _sg.indent_columns("\tx") == 4 and _sg.is_indented_code_line(b"\tx", is_bytes=True) is True


def test_fence_wins_over_comment_and_indent():
    # 围栏内的 `<!--` 不开注释、围栏内缩进行不另判——三者优先级固定，不互相污染
    assert E(b"```\n<!--\n```\n- [ ] s\n", b"```\n<!--\n```\n- [x] s\n") is True


# ── [impl-review-fix F4] 嵌套示例围栏：gate 侧回归（姊妹用例在 sdflow-implement） ──

def test_nested_example_fence_hides_pseudo_task_and_checkboxes():
    # 外层 ````markdown 内嵌 ```text 示例：内层 ``` 长度 3 < 开启符 4 且带 info string，
    # 关不掉外层 ⇒ 整块内容（伪 `### Task 9:` + 两个伪复选框）一律不可见。
    fx = Path(__file__).resolve().parent / "fixtures" / "tickets_plan_nested_fence.md"
    ids, boxes = _sg._parse_plan(fx.read_text(encoding="utf-8"))[:2]
    assert set(ids) == {"1", "2"}                       # 无伪 Task 9
    assert boxes["1"] == [True] and boxes["2"] == [False]   # 伪复选框未混入


# ══════════════════════════════════════════════════════════════════════════
# [harden-gate-git-layer Task3 · ADR-2] 比内容取代枚举
#
# 判据 = 锚侧与 HEAD 侧各跑一次 `git ls-tree -r -z <ref> -- <监视集>`，比较
# `path → (mode, type, oid)` **映射**。∴ 新增 / 删除 / 改名 / 修改 / mode / 类型
# 变更天然全覆盖，不需要枚举「哪些路径被碰过」，也不需要另做双侧并集。
#
# 🔴 本节全部经 **is_stale 公共入口 / run_gate 端到端**求值，MUST NOT 只直调内部
#   helper——本仓已有实证的假绿形态正是「只调 blob_pair 不走 is_stale」
#   （fix-design-gate-freshness-proxy 的 rename 用例，在真实洞存在时仍为绿）。
# ══════════════════════════════════════════════════════════════════════════

_ANCHOR_REL = BASE + "spec-review-report.md"

_PURE_FLIP = b"### Task 1: A\n- [x] s\n"          # 纯勾选翻转（零设计信息量）
_SEMANTIC = b"### Task 1: A retitled\n- [ ] s\n"  # 勾选框以外的语义改动（标题措辞）


def _approved_with_tasks(repo, data=b"### Task 1: A\n- [ ] s\n", plan=PLAN2_TICKETS):
    """建 change → 落 tasks.md → 重锚到「含 tasks.md 的盘面」。返回 change 目录。"""
    d = approved_change(repo, plan=plan)
    _write_tasks(repo, data)
    commit_all(repo, "seed tasks.md")
    _reanchor(repo, d)
    return d


def _design_stale(repo):
    """经公共入口求 design 域失鲜。"""
    return _sg.is_stale(repo, _ANCHOR_REL, "design", "demo")


# ── 5.1 监视集保住：实现期改源码 + 勾 tickets.md 复选框 ⇒ fresh ──────────────

def test_impl_source_edits_and_plan_checkbox_flip_keep_design_fresh(repo):
    """🔴 本 change 的**头号自噬风险**钉：判定收紧后若把监视集画大（如整个 change 目录、
    或整棵树），实现期的正常动作会立刻把设计门自锁死。

    实现期两个正常动作各来一次：① 改源码 ② 勾 `tickets.md` 的复选框
    （它是**实现计划**，不在 design 监视集内——监视集只有四件套与 specs/）。

    [remove-superpowers-pipeline Task2] 单名 resolver 下 `_approved_with_tasks` →
    `approved_change` 写盘的文件名是 `tickets.md`（原写旧名 `superpowers-plan.md`）——
    本用例的"勾选回填"须写同一个文件（模拟实现期原地编辑 plan），MUST 沿用该文件名，
    否则会凭空多出一份未消费的 `superpowers-plan.md`（resolver 只认 `tickets.md`，
    该文件会被静默忽略而非引发冲突，但测不到本用例要验的"勾选回填"场景）。
    """
    d = _approved_with_tasks(repo)
    (repo / "src.py").write_text("# impl\n", encoding="utf-8")
    (d / "tickets.md").write_text(
        PLAN2_TICKETS.replace("- [ ] s\n### Task 2", "- [x] s\n### Task 2", 1), encoding="utf-8")
    commit_all(repo, "checkpoint(task1-a): 实现 + 勾计划")
    assert _design_stale(repo) == (False, "fresh")
    code, js, _h = run_gate(repo)
    assert code == 0 and js["verdict"] == "CONTINUE_IMPL"


def test_impl_reports_and_tail_artifacts_keep_design_fresh(repo):
    """change 目录里的非四件套产物（impl-report / hand-off / 评审报告）不在监视集内。"""
    d = _approved_with_tasks(repo)
    (d / "impl-reports").mkdir(exist_ok=True)
    (d / "impl-reports" / "task1-x.md").write_text("# 实现报告\n", encoding="utf-8")
    (d / "hand-off.md").write_text("x\n", encoding="utf-8")
    commit_all(repo, "checkpoint(task1-a): 落实现报告")
    assert _design_stale(repo) == (False, "fresh")


# ── 5.2 勾选豁免常开、按内容切、不按阶段切 ────────────────────────────────

@pytest.mark.parametrize("plan,verdict", [
    (None, "RUN_PLAN"),               # 阶段①：实现计划尚未产出
    (PLAN2_TICKETS, "CONTINUE_IMPL"), # 阶段②：实现进行中
])
def test_pure_checkbox_flip_is_fresh_in_every_phase(repo, plan, verdict):
    """[ADR-3] 豁免 **MUST 常开、按内容切**——**MUST NOT 按阶段切**。

    勾选框的写入方是 agent 的自由行为、不是流程契约（本仓 20 个 checkpoint 提交碰过
    `tasks.md`，散在各阶段）⇒ 按阶段切会让非该阶段的正常勾选立刻假失鲜。
    两个阶段各验一次；同帧另带一份源码，贴 `git add -A` 的真实打包形态。
    """
    _approved_with_tasks(repo, plan=plan)
    _write_tasks(repo, b"### Task 1: A\n- [x] s\n")
    (repo / "src.py").write_text("# impl\n", encoding="utf-8")
    commit_all(repo, "docs: 勾选回填 + 实现")
    assert _design_stale(repo) == (False, "fresh")
    code, js, _h = run_gate(repo)
    # [fix1 M1] 断确切值，MUST NOT 用 `!= "REFUSE_START"`——UNKNOWN(6) 等异常出口
    # 也满足弱断言，会把「门崩了」读成「门放行了」。
    assert code == 0 and js["verdict"] == verdict


def test_checkbox_flip_across_many_commits_is_still_fresh(repo):
    """豁免按**内容**切、不按提交切：锚与 HEAD 之间隔多少次提交都不影响结论。
    （旧的逐帧求值下，任一中间帧不豁免即失鲜；内容比较只看两个端点。）"""
    _approved_with_tasks(repo, b"### Task 1: A\n- [ ] a\n- [ ] b\n")
    _write_tasks(repo, b"### Task 1: A\n- [x] a\n- [ ] b\n")
    commit_all(repo, "docs: 勾第一条")
    _write_tasks(repo, b"### Task 1: A\n- [x] a\n- [x] b\n")
    commit_all(repo, "docs: 勾第二条")
    assert _design_stale(repo) == (False, "fresh")


def test_tasks_change_beyond_checkbox_is_stale(repo):
    """差异超出复选框（措辞）⇒ 照判失鲜。"""
    _approved_with_tasks(repo)
    _write_tasks(repo, _SEMANTIC)
    commit_all(repo, "docs: 改任务措辞")
    assert _design_stale(repo) == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


def test_checkbox_flip_plus_design_edit_is_stale(repo):
    """豁免面**只**及于「差异仅在 tasks.md」：同帧还改了 design.md ⇒ 照判失鲜。"""
    d = _approved_with_tasks(repo)
    _write_tasks(repo, b"### Task 1: A\n- [x] s\n")
    (d / "design.md").write_text("# design changed\n", encoding="utf-8")
    commit_all(repo, "docs: 勾选 + 改设计")
    assert _design_stale(repo) == (True, "stale")


def _spy_blob_reads(monkeypatch):
    """打桩 `run_git_bytes`，记录所有 `cat-file blob` 调用（其余原样透传）。返回该记录 list。

    [fix1 F5] 单一源：三个「内容读取发生 / 未发生」类用例共用本 helper，
    MUST NOT 各自内联一份逐字相同的 spy（三份拷贝会漂移，且改 spy 口径时必漏其一）。
    """
    calls = []
    real = _sg.run_git_bytes

    def spy(root, *args):
        if args[:2] == ("cat-file", "blob"):
            calls.append(args)
        return real(root, *args)

    monkeypatch.setattr(_sg, "run_git_bytes", spy)
    return calls


def test_no_content_read_when_maps_are_equal(repo, monkeypatch):
    """分层判定的机械守：映射相等 ⇒ fresh，**0 次内容读取**。

    反向也钉住（下一条）：真需要判豁免时内容读取**必须**发生，否则本例退化成恒真断言。
    """
    _approved_with_tasks(repo)
    (repo / "src.py").write_text("# impl\n", encoding="utf-8")
    commit_all(repo, "checkpoint(task1-a): 只改源码")
    calls = _spy_blob_reads(monkeypatch)
    assert _design_stale(repo) == (False, "fresh")
    assert calls == []


def test_content_read_does_happen_when_only_tasks_differs(repo, monkeypatch):
    _approved_with_tasks(repo)
    _write_tasks(repo, b"### Task 1: A\n- [x] s\n")
    commit_all(repo, "docs: 勾选回填")
    calls = _spy_blob_reads(monkeypatch)
    assert _design_stale(repo) == (False, "fresh")
    assert len(calls) == 2          # 锚侧 + HEAD 侧各一次


# ── 5.4 把已批准产物换回锚之前的旧内容 ⇒ 失鲜 ─────────────────────────────

def test_revert_to_pre_anchor_content_is_stale(repo):
    """🔴 判别性最强的一格：HEAD 侧内容**曾经存在过**（就在锚之前），
    任何「这份内容在历史上出现过就算见过」的判据都会在此假绿。
    内容比较锚的是**被批准的那一份**，∴ 换回旧版同样是失鲜。
    """
    d = approved_change(repo, plan=PLAN2_TICKETS)
    (d / "design.md").write_text("v1 旧设计\n", encoding="utf-8")
    commit_all(repo, "design v1")
    (d / "design.md").write_text("v2 被批准的设计\n", encoding="utf-8")
    commit_all(repo, "design v2")
    _reanchor(repo, d)                                   # 锚 = v2
    (d / "design.md").write_text("v1 旧设计\n", encoding="utf-8")
    commit_all(repo, "merge: resolve 回 v1")
    assert _design_stale(repo) == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


# ── 5.5 无关的报告排版提交不移动锚（旧实现为参照物的对比测试）───────────────

def _legacy_report_last_sha(repo, rel):
    """**已退役**的反推式锚（`report_last_sha` 原样重建），仅供本节做参照物。

    [5.5 · design.md 已登记] 本条的变异手段与其余不同源：新实现里**没有反推逻辑可删**
    （锚是读出来的常量），而把 `report_last_sha` 复活回生产代码违反 Compliance
    （「MUST NOT 回退到 report_last_sha 或任何反推式锚」）。
    ∴ 改为「以旧实现为参照物做对比测试」——在测试里重建旧锚，证明两者在同一盘面上
    **给出相反结论**，从而证明新实现确实不是旧行为的换皮。
    """
    return _sg.run_git(repo, "log", "-1", "--format=%H", "--", rel)


def test_report_reformat_commit_does_not_move_anchor(repo):
    """排版提交顺带碰一下报告文件 ⇒ 锚 MUST NOT 前移，锚前的未审改动 MUST NOT 被埋掉。"""
    d = _approved_with_tasks(repo)
    (d / "design.md").write_text("拍板后偷改的设计\n", encoding="utf-8")
    commit_all(repo, "docs: 偷改设计")
    report = d / "spec-review-report.md"
    report.write_text(report.read_text(encoding="utf-8") + "\n<!-- CI 排版 -->\n",
                      encoding="utf-8")
    commit_all(repo, "chore: 报告排版（不动任何结论字段）")
    assert _design_stale(repo) == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


def test_legacy_reanchoring_implementation_would_have_judged_fresh(repo):
    """对比测试（5.5 的变异证明替代物）：**同一个盘面**下——

      · 旧的反推式锚 = 排版提交（被无声前移到偷改**之后**）⇒ 窗口内没有任何设计改动 ⇒ 判 fresh
      · 新的录锚      = 报告 frontmatter 里录下的那个 commit ⇒ 偷改在窗口内 ⇒ 判 stale

    两者结论相反 ⇒ 上一条用例的绿不可能是旧行为侥幸给出的。
    """
    d = _approved_with_tasks(repo)
    approved_sha = _sg.read_reviewed_sha(repo, _ANCHOR_REL)   # 报告 frontmatter 录下的锚
    (d / "design.md").write_text("拍板后偷改的设计\n", encoding="utf-8")
    commit_all(repo, "docs: 偷改设计")
    sneaked_sha = _head(repo)
    report = d / "spec-review-report.md"
    report.write_text(report.read_text(encoding="utf-8") + "\n<!-- CI 排版 -->\n",
                      encoding="utf-8")
    commit_all(repo, "chore: 报告排版")
    reformat_sha = _head(repo)

    legacy = _legacy_report_last_sha(repo, _ANCHOR_REL)
    assert legacy == reformat_sha and legacy != approved_sha        # 旧锚被前移
    assert _sg.read_reviewed_sha(repo, _ANCHOR_REL) == approved_sha  # 新锚推不动
    # 旧锚下窗口内的监视集内容毫无差异 ⇒ 旧实现在此判 fresh（偷改被埋在锚之前）
    specs = _sg.design_pathspecs(BASE)
    assert _sg.ls_tree_map(repo, legacy, specs) == _sg.ls_tree_map(repo, "HEAD", specs)
    assert sneaked_sha != reformat_sha
    # 新实现在同一盘面判 stale
    assert _design_stale(repo) == (True, "stale")


# ── 5.10 specs/ 子树：新增 / 删除 / rename（内容不变）三类各判失鲜 ──────────

def test_specs_added_file_is_stale(repo):
    d = approved_change(repo, plan=PLAN2_TICKETS)
    _reanchor(repo, d)
    specs = d / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "new.md").write_text("# 新增 delta\n", encoding="utf-8")
    commit_all(repo, "docs: 新增 delta spec")
    assert _design_stale(repo) == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


def test_specs_deleted_file_is_stale(repo):
    d = approved_change(repo, plan=PLAN2_TICKETS)
    specs = d / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "gone.md").write_text("# delta\n", encoding="utf-8")
    commit_all(repo, "docs: delta spec")
    _reanchor(repo, d)
    (specs / "gone.md").unlink()
    commit_all(repo, "chore: 删掉 delta spec")
    assert _design_stale(repo) == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


def test_specs_renamed_with_identical_content_is_stale(repo):
    """🔴 内容逐字节不变的纯改名：任何「逐文件比字节」的判据都会在此假绿
    （两侧各自枚举都能找到一份同样的字节）。映射比较看的是 **path → oid** 的对应，
    ∴ 路径动了就是不等。同时这也是旧枚举协议 rename 洞的等价件（5.15b）。
    """
    d = approved_change(repo, plan=PLAN2)
    specs = d / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "old.md").write_text("# delta\n", encoding="utf-8")
    commit_all(repo, "docs: delta spec")
    _reanchor(repo, d)
    _git(repo, "mv", BASE + "specs/old.md", BASE + "specs/new.md")
    commit_all(repo, "chore: 改名 delta spec（内容一字未动）")
    # 前提校准：两侧内容确实逐字节相同——否则本例退化成「内容变了」，测不出 rename 面
    before = _git(repo, "show", f"{_sg.read_reviewed_sha(repo, _ANCHOR_REL)}:{BASE}specs/old.md").stdout
    after = _git(repo, "show", f"HEAD:{BASE}specs/new.md").stdout
    assert before == after
    assert _design_stale(repo) == (True, "stale")


def test_specs_subtree_edit_is_stale(repo):
    d = approved_change(repo, plan=PLAN2)
    specs = d / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "s.md").write_text("# v1\n", encoding="utf-8")
    commit_all(repo, "docs: delta spec")
    _reanchor(repo, d)
    (specs / "s.md").write_text("# v2 偷改\n", encoding="utf-8")
    commit_all(repo, "docs: 改 delta spec")
    assert _design_stale(repo) == (True, "stale")


# ── 5.18 / 5.7 缺失 ≠ 读失败；读失败 ≠ 内容为空 ───────────────────────────

@pytest.mark.parametrize("how", ["delete", "rename-away"])
def test_one_sided_missing_tasks_is_stale_not_a_read_failure(repo, monkeypatch, how):
    """[5.18] `tasks.md` 单侧缺失（被删 / rename 出监视集）⇒ **判 stale**。

    🔴 且 MUST NOT 呈现为读失败：存在性判定统一走 `ls-tree`（rc=0 + 不在结果里 = 缺失，
    与失败判然二分），`cat-file blob` 只在双侧均存在时才被调用。若让内容读取承担存在性
    判定，这里会走 rc=128 → 「检查仓完整性」的诊断，把「文件没了」误导成「仓坏了」。
    本例双向钉死：判定值 = stale，且内容读取**一次都没发生**。
    """
    d = _approved_with_tasks(repo)
    if how == "delete":
        (d / "tasks.md").unlink()
        commit_all(repo, "chore: 删掉 tasks.md")
    else:
        _git(repo, "mv", TASKS_REL, BASE + "tasks-renamed.md")
        commit_all(repo, "chore: 迁走 tasks.md")
    calls = _spy_blob_reads(monkeypatch)
    assert _design_stale(repo) == (True, "stale")
    assert calls == []                      # 未走内容读取 ⇒ 不可能被呈现成读失败
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"
    for misleading in ("完整性", "读取失败", "读失败", "UNKNOWN"):
        assert misleading not in js["reason"], js["reason"]


def test_tasks_appearing_only_on_head_side_is_stale(repo):
    """反向单侧缺失：锚侧没有 tasks.md、HEAD 侧新增 ⇒ 同样判 stale
    （只枚举 HEAD 一侧或只枚举锚一侧的实现，各会漏掉其中一个方向）。"""
    d = approved_change(repo, plan=PLAN2)
    _reanchor(repo, d)
    _write_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    commit_all(repo, "docs: 新建 tasks.md")
    assert _design_stale(repo) == (True, "stale")


def test_ls_tree_read_failure_is_indeterminate_not_fresh(repo, monkeypatch):
    """[5.7] `ls-tree` 的 rc≠0 = 真读失败 ⇒ `GateIndeterminate`（→ UNKNOWN(6)），
    **MUST NOT** 当成空映射——两侧都失败会比出「空 == 空」⇒ 判 fresh ⇒ 放行一切改动。"""
    d = _approved_with_tasks(repo)
    (d / "design.md").write_text("偷改\n", encoding="utf-8")
    commit_all(repo, "docs: 偷改")
    # [fix1 F5] 原写法是个 lambda，闭包引用**下一行才赋值**的 `_real`——能跑通纯属
    # 「lambda 体到调用时才求值」的巧合，读起来是先用后定义。改成先取真值、再定义桩。
    real = _sg.run_git_bytes
    monkeypatch.setattr(_sg, "run_git_bytes", lambda root, *args:
                        (128, b"") if args[:1] == ("ls-tree",) else real(root, *args))
    with pytest.raises(_sg.GateIndeterminate) as ei:
        _design_stale(repo)
    assert ei.value.category == _sg.CAUSE_READ_FAILED


def test_ls_tree_unparsable_output_is_indeterminate(repo, monkeypatch):
    """协议外形态（无 `\\t` / 字段数不对）⇒ 看不清 ⇒ 不可判。
    MUST NOT 静默跳过该记录——跳过等于把一个真实条目从映射里抹掉（fail-open）。"""
    _approved_with_tasks(repo)
    monkeypatch.setattr(_sg, "run_git_bytes",
                        lambda root, *a: (0, b"garbage-without-tab\0"))
    with pytest.raises(_sg.GateIndeterminate) as ei:
        _design_stale(repo)
    assert ei.value.category == _sg.CAUSE_READ_FAILED


def test_blob_read_failure_on_both_sides_is_not_equal_content(repo, monkeypatch):
    """🔴 本 change 的头号自噬风险钉（design.md 明列）：两侧内容读取都失败、各返回空串，
    比较判「同」⇒ 假绿。∴ 内容读取 MUST 显式判 returncode 并上抛不可判，
    **MUST NOT** 把失败折成 `b""`。

    构造：映射差异恰在 tasks.md（走到内容读取），但 `cat-file blob` 恒失败。
    """
    _approved_with_tasks(repo)
    _write_tasks(repo, _SEMANTIC)              # 语义改动：若两侧读成 b"" 会被判等值而豁免
    commit_all(repo, "docs: 偷改 task 标题")
    real = _sg.run_git_bytes

    def blob_always_fails(root, *args):
        if args[:2] == ("cat-file", "blob"):
            return 128, b""
        return real(root, *args)

    monkeypatch.setattr(_sg, "run_git_bytes", blob_always_fails)
    with pytest.raises(_sg.GateIndeterminate) as ei:
        _design_stale(repo)
    assert ei.value.category == _sg.CAUSE_READ_FAILED


def test_blob_read_failure_on_one_side_is_indeterminate(repo, monkeypatch):
    _approved_with_tasks(repo)
    _write_tasks(repo, b"### Task 1: A\n- [x] s\n")
    commit_all(repo, "docs: 勾选回填")
    real = _sg.run_git_bytes
    anchor = _sg.read_reviewed_sha(repo, _ANCHOR_REL)

    def anchor_side_fails(root, *args):
        if args[:2] == ("cat-file", "blob") and args[2].startswith(anchor):
            return 128, b""
        return real(root, *args)

    monkeypatch.setattr(_sg, "run_git_bytes", anchor_side_fails)
    with pytest.raises(_sg.GateIndeterminate):
        _design_stale(repo)


@pytest.mark.skipif(os.name == "nt", reason="NTFS does not expose POSIX executable-bit changes")
def test_mode_only_change_on_tasks_is_stale(repo):
    """仅权限位变更：前后两版 blob 字节**完全相同**，纯内容判据必说「等值」
    ⇒ MUST 由映射层（含 mode）先拦下，否则状态位变更被静默放行。"""
    _git(repo, "config", "core.fileMode", "true")
    d = _approved_with_tasks(repo)
    (d / "tasks.md").chmod(0o755)
    commit_all(repo, "chmod +x tasks.md")
    # 前提校准：chmod 真进了 git（core.fileMode 关 ⇒ 本例失去区分力）
    raw = _git(repo, "diff", "--raw", _sg.read_reviewed_sha(repo, _ANCHOR_REL), "HEAD",
               "--", TASKS_REL).stdout
    assert raw.strip(), "前提校准：chmod 未被 git 记录（core.fileMode 关？）本例失去区分力"
    assert _design_stale(repo) == (True, "stale")


# ── 5.15b 承载「仍然生效」安全承诺的既有用例：内容比较版等价改写 ─────────────

def _merge_amended(repo, mutate, msg="merge side"):
    """造一个 merge 提交，其树由 mutate 决定（两个 parent 各自都没有这份内容）。

    `git merge --no-ff` 后 `git commit --amend -a` 保留双 parent，是构造 evil-merge
    的最短确定性路径（不依赖冲突解决的交互）。
    """
    _git(repo, "checkout", "-q", "-b", "side")
    (repo / "s.txt").write_text("s\n", encoding="utf-8")
    commit_all(repo, "side edit")
    _git(repo, "checkout", "-q", "main")
    (repo / "m.txt").write_text("m\n", encoding="utf-8")
    commit_all(repo, "main edit")
    _git(repo, "merge", "--no-ff", "-q", "-m", msg, "side")
    mutate()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--amend", "--no-edit")
    parents = _git(repo, "rev-list", "--parents", "-n", "1", "HEAD").stdout.split()
    assert len(parents) == 3, "构造失败：应为双 parent 的 merge 提交"


def test_evil_merge_design_edit_is_stale(repo):
    """[5.15b · 原 test_evil_merge_design_edit_is_stale] 改动**只存在于 merge 自身
    resolve 出的树**（两个 parent 都没有这份内容）。旧枚举协议对 merge 提交不输出任何
    文件 ⇒ 整帧被跳过 ⇒ 判 fresh。

    内容比较对拓扑完全不敏感（只看锚与 HEAD 两个端点的树），∴ 该承诺**依然生效**——
    改写成不依赖任何帧概念的等价形态。
    """
    d = _approved_with_tasks(repo)
    (d / "design.md").write_text("v1\n", encoding="utf-8")
    commit_all(repo, "seed design")
    _reanchor(repo, d)
    _merge_amended(repo, lambda: (d / "design.md").write_text("evil v2\n", encoding="utf-8"))
    assert _design_stale(repo) == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


def test_evil_merge_tasks_semantic_edit_is_stale(repo):
    """[5.15b · 原 test_evil_merge_tasks_semantic_edit_is_stale] 同一片面的 tasks.md 分支：
    merge 自身把 task 标题改了（非勾选框）⇒ 必须失鲜。"""
    _approved_with_tasks(repo)
    _merge_amended(repo, lambda: _write_tasks(repo, _SEMANTIC))
    assert _design_stale(repo) == (True, "stale")


def test_merge_pure_checkbox_flip_is_exempt_end_to_end(repo):
    """[5.15b · 原 test_merge_frame_pure_flip_is_exempt_end_to_end] 反向判别性：
    merge 自身只做纯勾选翻转 ⇒ 豁免真能生效，上一条的红不是靠「见 merge 就一刀切拒绝」蒙的。"""
    _approved_with_tasks(repo)
    _merge_amended(repo, lambda: _write_tasks(repo, b"### Task 1: A\n- [x] s\n"))
    assert _design_stale(repo) == (False, "fresh")
    code, js, _h = run_gate(repo)
    assert code == 0 and js["verdict"] == "CONTINUE_IMPL"


def test_git_mv_tasks_out_of_watched_set_is_stale(repo):
    """[5.15b · 原 test_git_mv_tasks_is_stale_end_to_end] `git mv` 把 tasks.md 迁出监视集
    ⇒ 失鲜。旧协议默认开 rename 检测、只输出目标路径 ⇒ 源路径看不到 ⇒ 判 fresh。
    （单侧缺失的诊断口径另由 5.18 钉住。）"""
    _approved_with_tasks(repo)
    _git(repo, "mv", TASKS_REL, BASE + "tasks-renamed.md")
    commit_all(repo, "chore: 迁走 tasks.md")
    assert _design_stale(repo) == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


@pytest.mark.skipif(os.name == "nt", reason="Win32 filenames cannot contain tab characters")
def test_spec_path_with_tab_is_stale(repo):
    """[5.15b · 原 test_spec_path_with_tab_is_stale] 含 Tab 的路径：旧的文本行协议按行切 +
    C-quote 包裹 ⇒ 逃出监视集。新口径靠 `-z`（关掉 C-quote）+ 按**首个 `\\t`** 切分 +
    path 保持原始字节，∴ 该承诺依然生效。"""
    d = _approved_with_tasks(repo)
    specs = d / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "we\tird.md").write_text("delta\n", encoding="utf-8")
    commit_all(repo, "docs: 加一份带 Tab 文件名的 delta spec")
    assert _design_stale(repo) == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


@pytest.mark.skipif(os.name == "nt", reason="Win32 filenames cannot contain tab characters")
def test_ls_tree_keeps_tab_path_raw_and_unquoted(repo):
    """机械守 `-z` 协议本身：路径原样进映射键——无 C-quote 包裹、不按 Tab 拆碎。
    删掉 `-z` ⇒ git 会把这条路径 C-quote 成 `"...we\\tird.md"` ⇒ 本例转红。"""
    d = _approved_with_tasks(repo)
    (d / "specs").mkdir(parents=True, exist_ok=True)
    (d / "specs" / "we\tird.md").write_text("x\n", encoding="utf-8")
    commit_all(repo, "tab path")
    entries = _sg.ls_tree_map(repo, "HEAD", _sg.design_pathspecs(BASE))
    key = (BASE + "specs/we\tird.md").encode("utf-8")
    assert key in entries
    assert not any(k.startswith(b'"') for k in entries)


def test_chinese_named_spec_edit_still_stale(repo):
    """[5.15b · 原 test_chinese_named_spec_edit_still_stale] 非 ASCII 路径同一片面
    （C-quote ⇒ 裸 startswith 失配 ⇒ 静默放行 = 假✅）。本项目中文文件名密集，realistic。"""
    d = _approved_with_tasks(repo)
    specs = d / "specs"
    specs.mkdir(exist_ok=True)
    (specs / "功能规格.md").write_text("拍板后偷改设计语义\n", encoding="utf-8")
    commit_all(repo, "docs: 改中文名 spec")
    assert _design_stale(repo) == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


# ── 保留复用件仍在场且有真实调用点（tasks 2.9）─────────────────────────────

def test_retained_helpers_are_still_wired_into_production_path(repo, monkeypatch):
    """[tasks 2.9] `DESIGN_WATCHED_NAMES` / `_tasks_content_exempt` /
    `_normalize_checkbox_lines` 是退役后仅有的三处**保留复用**件。

    🔴 「声明保留」不等于「还在用」——本 change 前一轮就出过「保留却成了孤儿」的问题。
    ∴ 本例不只断言它们存在，而是断言它们**在生产路径上被真调到**。
    """
    import inspect
    src = inspect.getsource(_sg.is_stale)
    assert "design_pathspecs" in src and "_tasks_content_exempt" in src
    assert "DESIGN_WATCHED_NAMES" in inspect.getsource(_sg.design_pathspecs)
    assert "_normalize_checkbox_lines" in inspect.getsource(_sg._tasks_content_exempt)
    # 监视集成员逐字在场（少一个 = 那类产物被偷改后不再失鲜）
    assert set(_sg.DESIGN_WATCHED_NAMES) == {"proposal.md", "design.md", "tasks.md"}
    assert _sg.design_pathspecs(BASE) == [
        BASE + "proposal.md", BASE + "design.md", BASE + "tasks.md", BASE + "specs/"]
    # 真调到：勾选豁免必须活着（替身为恒 False ⇒ 纯翻转也失鲜）
    _approved_with_tasks(repo)
    _write_tasks(repo, b"### Task 1: A\n- [x] s\n")
    commit_all(repo, "docs: 勾选回填")
    monkeypatch.setattr(_sg, "_tasks_content_exempt", lambda b, a: False)
    assert _design_stale(repo) == (True, "stale")
    monkeypatch.undo()                    # 复原后必须变回 fresh（证明替身真被调到）
    assert _design_stale(repo) == (False, "fresh")


def test_retired_frame_comparison_cluster_leaves_no_dangling_reference():
    """[tasks 2.8] 帧比较整簇退役后**仓内无悬空引用与孤儿代码**。

    逐一列名（design.md 组件清单的退役行），任一残留即红——防「删了函数、
    调用点还在」或「函数留着没人调」两种半途状态。
    """
    retired = ["frame_touched_paths", "design_frame_exempt", "design_frame_exempt_reason",
               "commit_parents", "_parent_path_status", "_plain_content_modification",
               "_plain_modification_from_raw", "blob_pair", "design_watched_subs",
               "STALE_CATEGORIES", "_stale_trigger_hint", "StaleResult"]
    for name in retired:
        assert not hasattr(_sg, name), f"退役件仍在模块里：{name}"
    src = Path(_sg.__file__).read_text(encoding="utf-8")
    code_lines = [ln for ln in src.splitlines() if not ln.lstrip().startswith("#")]
    body = "\n".join(code_lines)
    for name in retired:
        assert name not in body, f"退役件在代码行里仍被引用：{name}"
    # 触发点诊断整体退役（ADR-4）：JSON 侧不再有 stale_trigger 键
    assert "stale_trigger" not in body


def test_stale_verdict_carries_no_trigger_payload(repo):
    """[ADR-4] 退役的可观察面：失鲜输出不再携带 `stale_trigger`。
    （锚值可见性由 Task4 的 `emit` 补 `reviewed_sha` 承担，不靠枚举通路。）"""
    d = _approved_with_tasks(repo)
    (d / "design.md").write_text("偷改\n", encoding="utf-8")
    commit_all(repo, "docs: 偷改设计")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"
    assert "stale_trigger" not in js


# ══════════════════════════════════════════════════════════════════════════
# [fix1] 双轴审第 1 轮返修的三条守卫（F1 退出码契约 / F2 gitlink 诊断 / F3 基座隔离）
# ══════════════════════════════════════════════════════════════════════════

# ── F1：`--change` 的非 UTF-8 字节 MUST NOT 把退出码打出契约集 ────────────────
#
# `--change` 经 argv 由 CPython 以 **surrogateescape** 解码 ⇒ 非 UTF-8 字节变 lone
# surrogate。`is_stale` 里 `(base + "tasks.md").encode("utf-8")` 对它抛
# `UnicodeEncodeError`，而 `main()` 只捕 `GateIndeterminate` ⇒ 异常逸出 ⇒ 退出码 1。
# 正解 = `os.fsencode`（argv 解码的逆运算，与 git 吐的原始路径字节天然同口径）。

_NON_UTF8_CHANGE = b"br\xffken".decode("utf-8", "surrogateescape")  # lone surrogate `\udcff`
EXIT_CONTRACT = {0, 3, 4, 5, 6}


def test_non_utf8_change_reaches_design_branch_without_escaping(repo, monkeypatch):
    """🔴 判别性最强的一格：**真的走到** `tasks.md` 路径编码那一行。

    只用真实文件系统构造进不了这一格——APFS/HFS+ 拒绝非 UTF-8 文件名（实测
    `[Errno 92] Illegal byte sequence`），故在此把两侧映射直接摆好，让 `is_stale`
    公共入口从 `base` 拼出那个含 surrogate 的路径去查表。旧实现在此抛
    `UnicodeEncodeError`（不是 `GateIndeterminate`）⇒ 逸出 `main()` 的捕获面。
    """
    _approved_with_tasks(repo)
    base = f"openspec/changes/{_NON_UTF8_CHANGE}/"
    tasks_key = os.fsencode(base + "tasks.md")
    anchor_map = {tasks_key: (b"100644", b"blob", b"a" * 40)}
    head_map = {tasks_key: (b"100644", b"blob", b"b" * 40)}
    maps = iter([anchor_map, head_map])
    monkeypatch.setattr(_sg, "ls_tree_map", lambda root, ref, specs: next(maps))
    monkeypatch.setattr(_sg, "read_blob_bytes", lambda root, ref, path, label:
                        _PURE_FLIP if ref == "HEAD" else b"### Task 1: A\n- [ ] s\n")
    # 纯勾选翻转 ⇒ fresh。关键在于「算得出结论」而非抛 UnicodeEncodeError。
    assert _sg.is_stale(repo, _ANCHOR_REL, "design", _NON_UTF8_CHANGE) == (False, "fresh")


@pytest.mark.skipif(os.name == "nt", reason="Windows argv is Unicode and cannot carry raw non-UTF-8 bytes")
def test_non_utf8_change_exit_code_stays_in_contract_set(repo):
    """端到端补位：非 UTF-8 的 `--change` 经 `main()` 求值，退出码 MUST 落在契约集内。

    ⚠ 诚实边界：本机文件系统拒绝该名字的目录 ⇒ 本例走的是 `decide()` 的归档短路半场，
    **够不到** design 域的路径编码那一行（那一格由上一条覆盖）。它钉的是另一件事：
    argv 里的非 UTF-8 字节在**任何**一步都不得逸出成退出码 1。
    """
    mkchange(repo)
    commit_all(repo, "seed")
    code, js, _h = run_gate(repo, change=_NON_UTF8_CHANGE)
    assert code in EXIT_CONTRACT, f"退出码 {code} 落在契约集 {EXIT_CONTRACT} 之外"
    assert js.get("verdict")            # 有结构化输出，不是裸崩


# ── F2：gitlink 形态的 tasks.md ⇒ 判 stale，且诊断 MUST NOT 说「仓坏了」──────

def _replace_tasks_with_gitlink(repo, commit_oid, msg):
    """把 `tasks.md` 换成 gitlink 条目（`160000 commit <oid>`）并提交。

    用 `update-index --cacheinfo` 而非真建 submodule：确定性、零网络、零 .gitmodules。
    工作树里的同名文件先删掉——否则后续 `git add -A` 会把它作为 blob 重新加回来。
    """
    p = repo / TASKS_REL
    if p.exists():
        p.unlink()
    _git(repo, "rm", "-q", "--cached", "--ignore-unmatch", TASKS_REL)
    _git(repo, "update-index", "--add", "--cacheinfo",
         f"160000,{commit_oid},{TASKS_REL}")
    _git(repo, "commit", "-q", "-m", msg)


def test_gitlink_tasks_is_stale_without_repo_corruption_diagnosis(repo):
    """🔴 `ls-tree -r` **会**输出 gitlink（已实测）⇒ 豁免闸门只校 `mode/type` 两侧相等
    是不够的，MUST 另校 `type == blob`。

    否则两侧同为 `160000 commit`、oid 不同时会落进豁免分支 → `cat-file blob` rc=128
    → UNKNOWN(6)，诊断说「该路径已确认存在，故此为真读失败（仓损坏 / 权限）」——
    把「tasks.md 变成了 submodule」讲成「仓坏了」，正是 `read_blob_bytes` docstring
    自己禁止的误导口径。方向虽 fail-closed，但会把撞门者送错方向。
    """
    d = _approved_with_tasks(repo)
    oid1 = _head(repo)
    _replace_tasks_with_gitlink(repo, oid1, "chore: tasks.md 变 gitlink")
    _reanchor(repo, d)                       # 锚侧也是 gitlink ⇒ 两侧 mode/type 相等
    oid2 = _head(repo)
    assert oid1 != oid2
    _replace_tasks_with_gitlink(repo, oid2, "chore: gitlink 指向变更")
    # 前提校准：两侧确实都被 ls-tree 列成 commit 类型（否则本例失去区分力）
    entry = _sg.ls_tree_map(repo, "HEAD", _sg.design_pathspecs(BASE))[os.fsencode(TASKS_REL)]
    assert entry[1] == b"commit", f"前提校准失败：ls-tree 未输出 gitlink（{entry}）"

    assert _design_stale(repo) == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"
    for misleading in ("完整性", "读取失败", "读失败", "仓损坏", "UNKNOWN"):
        assert misleading not in js["reason"], js["reason"]


# ── F3：测试基座 MUST NOT 让判定输入受这台机器的 gitconfig 摆布 ──────────────

@pytest.mark.parametrize("key,want", [("core.autocrlf", "false"), ("core.fileMode", "true")])
def test_repo_fixture_pins_byte_and_mode_semantics(repo, key, want):
    """[F3] `repo` fixture MUST 钉死这两项——用例的判别力直接建在它们上：

    · `core.autocrlf=true`（Windows 安装默认）⇒ 回环时 LF↔CRLF 被悄悄改字节，
      而「纯复选框翻转」类用例依赖 `tasks.md` 的**字节原样回环**；
    · `core.fileMode=false`（部分文件系统上 git 自动置）⇒ chmod 进不了 git，
      `test_mode_only_change_on_tasks_is_stale` 失去区分力。

    旧的退役用例曾各自显式补偿这两项，**补偿随退役一并消失** ⇒ 上移到基座、按面治。
    锚目标态：消费机上两种取值都存在，「我这台机器上没事」不构成保证。
    """
    got = subprocess.run(["git", "-C", str(repo), "config", "--get", key],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
    assert got == want, f"{key}={got!r}，基座未钉死（期望 {want!r}）"


# ══ [harden-gate-git-layer Task4 · ADR-3 · tasks 2.5/2.6/2.7 · 测试 5.3b/c/d] 求值窗口 ══
#
# 判据只在它保护的风险真实存在的阶段求值：design 域失鲜保护的是「照着一份已经变了的设计
# 继续建」，该风险**只在实现期存在**。∴ 两个「进入实现期」的入口 MUST 各自求值（5.3b–c），
# 窗口之外（代码审期 / 收尾期）MUST NOT 求值（5.3d）。
#
# 🔴 **两组 MUST 各自独立**：两个用例分别只穿过一个入口分支——
#   5.3b：无 plan ⇒ 只到 RUN_PLAN
#   5.3c：有 plan + 有未完成任务 ⇒ 跳过前者，只到 CONTINUE_IMPL
# ∴ 拆掉任一入口的 `emit_windowed` 包装，**只有对应的那一个用例变红**（变异独立性已实测，
# 结果见 impl-reports/task4-eval-window.md）。写成共享同一条触发路径的两个用例会「两个一起
# 红或一个都不红」，那样的「两组独立」是假的（期望集取错范畴）。

def _anchor_of(d):
    """从 spec-review-report.md 的 frontmatter 读出锚（= gate 会拿来比的那个 sha）。"""
    for line in (d / "spec-review-report.md").read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("reviewed_sha:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError("报告里没有 reviewed_sha 锚")

def _revise_design(d, repo, text="# 拍板后改了设计\n"):
    (d / "design.md").write_text(text, encoding="utf-8")
    commit_all(repo, "revise design artifacts")

def _assert_windowed_refusal(repo, d):
    """窗口内失鲜的共同断言：REFUSE_START(3) + 锚值可见 + 可直接执行的差异比较命令〔ADR-4 / 2.7〕。"""
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START", js
    sha = _anchor_of(d)
    assert js["reviewed_sha"] == sha, "锚值 MUST 出现在 emit 的 extra 里（撞门者不必去翻 frontmatter）"
    assert f"git diff {sha} HEAD -- " in js["reason"], js["reason"]
    # 命令 MUST 覆盖整个监视集（否则「一条命令即得」不成立）
    for p in _sg.design_pathspecs(BASE):
        assert p in js["reason"], f"差异命令漏了监视集成员 {p}"

# ── 5.3b RUN_PLAN 分支 ───────────────────────────────────────────────

def test_window_run_plan_evaluates_design_freshness(repo):
    d = approved_change(repo)                     # 无 plan ⇒ 判定停在 RUN_PLAN
    assert run_gate(repo)[1]["verdict"] == "RUN_PLAN"
    _revise_design(d, repo)
    _assert_windowed_refusal(repo, d)

# ── 5.3c CONTINUE_IMPL 分支 ──────────────────────────────────────────

def test_window_continue_impl_evaluates_design_freshness(repo):
    d = approved_change(repo, plan=PLAN2_TICKETS)  # plan 在、任务未完 ⇒ CONTINUE_IMPL
    assert run_gate(repo)[1]["verdict"] == "CONTINUE_IMPL"
    _revise_design(d, repo)
    _assert_windowed_refusal(repo, d)

# ── 5.3d 窗口之外：代码审期 / 收尾期修订四件套 MUST NOT 判 design 失鲜 ──

def test_window_closed_during_code_review(repo):
    """代码审期修订四件套 ⇒ 不判 design 失鲜。

    全仓 14 个 `checkpoint(impl-review)` 提交改过四件套，`opsx:verify` step 7 亦明文允许
    「revise design.md to match reality」⇒ 全阶段求值会把这 14 类情形全部误拦，产出纯噪声。
    """
    d = impl_done(repo)                            # plan 全勾、无 cr 报告 ⇒ 窗口右边界之外
    assert run_gate(repo)[1]["verdict"] == "RUN_CODE_REVIEW"
    _revise_design(d, repo)
    code, js, _h = run_gate(repo)
    assert js["verdict"] != "REFUSE_START", f"窗口外仍判 design 失鲜：{js}"
    assert code == 0 and js["verdict"] == "RUN_CODE_REVIEW", js

def test_window_closed_during_wrapup(repo):
    """收尾期（cr + verify 均已出结论）修订四件套 ⇒ 不判 design 失鲜。"""
    d = tail_ok(repo)
    assert run_gate(repo)[1]["verdict"] == "RUN_VERIFY"
    _revise_design(d, repo)
    code, js, _h = run_gate(repo)
    assert js["verdict"] != "REFUSE_START", f"窗口外仍判 design 失鲜：{js}"
    # 四件套是 openspec/ 内路径 ⇒ code 域顶层条目不变 ⇒ 也不该触 RERUN_STALE
    assert code == 0 and js["verdict"] == "RUN_VERIFY", js


# ══ [harden-gate-git-layer Task5 · ADR-2 · tasks 2.3 · 测试 5.11a/5.11b/5.12] code 域 ══
#
# 判据 = 锚与 HEAD 各跑一次**非递归** `git ls-tree`，取**仓库顶层条目**的浅层快照
# （`path→(mode,type,oid)` 映射），排除 `openspec` 记账条目后求等值。相等 ⇒ fresh，不等 ⇒ stale。
# tree 条目的 oid 递归摘要整棵子树 ⇒ 顶层某目录内任意深度的源码改动都翻转其顶层 tree oid、被捕获。
#
# 🔴 本节全部经 **is_stale 公共入口 / run_gate 端到端**求值（MUST NOT 只直调内部 helper）。
#   两个消费方各有覆盖：`code-review-report`（5.11a e2e，next=sdflow-code-review）与
#   `verify-report`（5.11b e2e，next=sdflow-done）各自走一次 stale 路径。
#
# 收益证明（5.11a/5.11b）= 本域改判据**唯一的正面收益**：merge 引入的源码改动、把源码 git mv
#   进记账目录，都不再从判定逃逸。各附「删掉守卫即变红」的变异证明（见 impl-report）。
# ══════════════════════════════════════════════════════════════════════════

_CR_REL = BASE + "code-review-report.md"
_VF_REL = BASE + "verify-report.md"


def _code_stale(repo, rel):
    """经公共入口求 code 域失鲜（rel = 两个消费方之一的报告相对路径）。"""
    return _sg.is_stale(repo, rel, "code", "demo")


def _anchor_code_reports(repo, d, sha, verify="PASS"):
    """写 code-review-report + verify-report，`reviewed_sha` 指向 sha（被代码审/验证批准的
    盘面），并提交。verify 取 PASS（e2e 走 code-review-report 消费方）或 FAIL（走 verify-report
    消费方——verify=FAIL 时 step8 的 cr-stale 让位、判定落到 step9 的 verify 读点）。"""
    (d / "code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: pass\n  reviewed_sha: {sha}\n---\n# 代码审报告\n",
        encoding="utf-8")
    (d / "verify-report.md").write_text(
        f"---\nship-gate:\n  verify: {verify}\n  reviewed_sha: {sha}\n---\n# 验证报告\n",
        encoding="utf-8")
    commit_all(repo, "code/verify 报告锚基线")


def _evil_merge_toplevel(repo, mutate, msg="evil merge resolve 出顶层源码"):
    """两个 parent 都**只碰 openspec/**（不引入顶层源码），merge 提交自身 resolve 出顶层改动。

    ∴ 顶层源码改动**仅存在于 merge 树**——旧 `--name-only` 提交遍历对 merge 不产 diff 会
    整帧漏掉（design.md 登记的「code 域 evil-merge 漏检」）；顶层条目映射比较只看锚与 HEAD
    两端的树、对拓扑完全不敏感 ⇒ 必抓。这是 5.11a 相对旧实现的判别性收益。
    """
    _git(repo, "checkout", "-q", "-b", "side")
    (repo / "openspec" / "changes" / "demo" / "note-side.md").write_text("s\n", encoding="utf-8")
    commit_all(repo, "side: 仅 openspec 记账")
    _git(repo, "checkout", "-q", "main")
    (repo / "openspec" / "changes" / "demo" / "note-main.md").write_text("m\n", encoding="utf-8")
    commit_all(repo, "main: 仅 openspec 记账")
    _git(repo, "merge", "--no-ff", "-q", "-m", msg, "side")
    mutate()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--amend", "--no-edit")
    parents = _git(repo, "rev-list", "--parents", "-n", "1", "HEAD").stdout.split()
    assert len(parents) == 3, "构造失败：应为双 parent 的 merge 提交"


# ── 5.11a：代码审后经 merge 提交 resolve 引入源码改动 ⇒ stale ─────────────────

def test_code_domain_merge_introduces_source_change_is_stale(repo):
    """[5.11a] merge 提交自身 resolve 出顶层源码 `resolved.py`（两 parent 都没有它）⇒
    该源码从未过代码审 ⇒ code 域必须判失鲜。经 `code-review-report` 消费方端到端求值。

    变异证明（G1 · 收益守卫）：把 code 分支改成恒 `return False, "fresh"` ⇒ 本例转红。"""
    d = impl_done(repo)
    baseline = head_sha(repo)                 # 代码审通过的基线（尚无顶层源码）
    _anchor_code_reports(repo, d, baseline, verify="PASS")
    _evil_merge_toplevel(
        repo, lambda: (repo / "resolved.py").write_text("# merge 里冒出来的源码\n", encoding="utf-8"))
    # 公共入口：code-review-report 消费方判 stale
    assert _code_stale(repo, _CR_REL) == (True, "stale")
    # 端到端：cr 消费方 → RERUN_STALE 重审（next=sdflow-code-review）
    code, js, _h = run_gate(repo)
    assert code == 0 and js["verdict"] == "RERUN_STALE" and js["next"] == "sdflow-code-review", js
    assert js["freshness"] == "stale"


# ── 5.11b：把源码改名迁进记账目录 ⇒ stale ────────────────────────────────────

def test_code_domain_git_mv_source_into_openspec_is_stale(repo):
    """[5.11b] `git mv` 把顶层源码 `src.py` 搬进 `openspec/`（记账目录）⇒ 顶层条目 `src.py`
    消失、映射不等 ⇒ 失鲜。迁入的目标落在被排除的 openspec 内，但**离开源顶层这一侧**仍暴露。
    经 `verify-report` 消费方端到端求值（verify=FAIL ⇒ 判定落到 step9 的 verify 读点）。

    变异证明（G1 · 收益守卫）：把 code 分支改成恒 `return False, "fresh"` ⇒ 本例转红。"""
    d = impl_done(repo)
    (repo / "src.py").write_text("# 已过代码审的顶层源码\n", encoding="utf-8")
    commit_all(repo, "seed 顶层源码进基线")
    baseline = head_sha(repo)
    _anchor_code_reports(repo, d, baseline, verify="FAIL")
    _git(repo, "mv", "src.py", BASE + "stashed-src.py")     # 源码搬进记账目录
    commit_all(repo, "chore: 把源码 git mv 进 openspec")
    # 公共入口：verify-report 消费方判 stale
    assert _code_stale(repo, _VF_REL) == (True, "stale")
    # 端到端：verify 消费方 → RERUN_STALE（next=sdflow-done）
    code, js, _h = run_gate(repo)
    assert code == 0 and js["verdict"] == "RERUN_STALE" and js["next"] == "sdflow-done", js
    assert js["freshness"] == "stale"


# ── 5.12：记账目录内部正常写入仍判新鲜 + 两个消费方各经公共入口求值 ────────────

def test_code_domain_openspec_accounting_writes_stay_fresh(repo):
    """[5.12] 排除 `openspec` 条目后，记账目录内部的一切正常写入都不动其余顶层条目 ⇒ fresh。
    覆盖两类记账写：① 写 verify-report（`_anchor_code_reports` 那一次提交本身即是）
    ② 归档移动目录（openspec 内部重排：新建 archive 子目录 + 落副本）。
    两个消费方（`code-review-report` / `verify-report`）各经 is_stale 公共入口求 fresh。

    变异证明：
      · G2（排除 openspec 条目）：不排除 ⇒ 记账写改了 openspec 顶层 tree oid ⇒ 映射不等 ⇒
        本例转红（误判 stale）。
      · G3（`recursive=False` 浅层）：改 `recursive=True` ⇒ openspec 子树内的文件以
        `openspec/...` 路径逐条进映射、不被 `!= b"openspec"` 排除 ⇒ 记账写即失鲜 ⇒ 本例转红。"""
    d = impl_done(repo)
    (repo / "src.py").write_text("# 顶层源码（证明排除后仍有非空顶层可比）\n", encoding="utf-8")
    commit_all(repo, "seed 顶层源码")
    baseline = head_sha(repo)
    _anchor_code_reports(repo, d, baseline, verify="PASS")   # 记账写①：落 cr/verify 报告
    # 记账写②：模拟归档移动目录（openspec 内部重排）+ hand-off
    (d / "hand-off.md").write_text("交接\n", encoding="utf-8")
    arch = repo / "openspec" / "changes" / "archive" / "2026-07-21-demo"
    arch.mkdir(parents=True)
    (arch / "proposal.md").write_text("归档副本\n", encoding="utf-8")
    commit_all(repo, "openspec 记账：hand-off + 归档目录")
    # 两个消费方各经公共入口求值，均 fresh（openspec 顶层 tree 变了但被排除，src.py 未动）
    assert _code_stale(repo, _CR_REL) == (False, "fresh")
    assert _code_stale(repo, _VF_REL) == (False, "fresh")


def test_code_domain_excludes_openspec_by_entry_name_not_pathspec(repo):
    """[tasks 2.3 机械守] 排除口径 = Python 侧按顶层条目名 `!= b"openspec"`，**非**负向
    pathspec。锚与 HEAD 顶层映射只差一个 `openspec` 条目时 ⇒ 排除后等值 ⇒ fresh；
    同一构造若换成整树 sha 或不排除 openspec 则会误判 stale（这两条错误路径 design.md 已实测证伪）。"""
    d = impl_done(repo)
    (repo / "src.py").write_text("# v1\n", encoding="utf-8")
    commit_all(repo, "seed 顶层源码")
    baseline = head_sha(repo)
    _anchor_code_reports(repo, d, baseline, verify="PASS")
    # 锚与 HEAD 的顶层映射：src.py 两侧同 oid，唯 openspec 条目 oid 不同（报告写入所致）
    anchor_top = _sg.ls_tree_map(repo, baseline, recursive=False)
    head_top = _sg.ls_tree_map(repo, "HEAD", recursive=False)
    assert anchor_top[b"openspec"] != head_top[b"openspec"], "前提校准：openspec 顶层 tree 确实变了"
    assert anchor_top[b"src.py"] == head_top[b"src.py"], "前提校准：src.py 未动"
    # 排除 openspec 后两侧等值 ⇒ fresh（是 openspec 条目的变化被排除掉，不是整树相等）
    assert _code_stale(repo, _CR_REL) == (False, "fresh")


# ══ [harden-gate-git-layer Task6 · ADR-7(a) · 测试 5.13] code-review 自动修复非空，两段提交时序 ══
#
# 锚记的是「被代码审放行的那份源码盘面」，而自动修复改的正是源码盘面。SKILL 的两段时序
# （修复先单独落盘 → 锚指该提交 → 报告单独落盘）令 code 域相对自己刚写下的锚保持 fresh；
# 单段时序（修复与报告同一次提交）则锚只能取修复前 HEAD ⇒ 相对自己立刻自锁。
#
# 🔴 变异形态说明（impl-report 详载）：本对用例是 ADR-7(a) 时序纪律的端到端守卫。SKILL 侧
#   无 ship_gate 代码可删，故以「单段时序对照」承担变异角色（同 5.5 的对比测试范式）；
#   但下方的自锁用例**同时**是真实的 ship_gate code 域守卫变异体——把 code 分支改成恒
#   `return False, "fresh"`，其 stale 断言即转红。两个角色同一用例承担。
# ══════════════════════════════════════════════════════════════════════════

def test_code_review_autofix_two_stage_commit_does_not_self_stale(repo):
    """[5.13 · ADR-7(a) 正例] 自动修复非空时，两段提交时序令 code 域相对自己的锚 fresh。"""
    d = impl_done(repo)
    (repo / "src.py").write_text("# 被代码审的源码 v1\n", encoding="utf-8")
    commit_all(repo, "seed 顶层源码进代码审基线")
    # ① 自动修复先单独提交（改的是源码盘面）
    (repo / "src.py").write_text("# 自动修复后 [impl-review-fix]\n", encoding="utf-8")
    commit_all(repo, "checkpoint(impl-review): 多镜代码审自动修复")
    fix_sha = head_sha(repo)                  # ② 锚指修复提交
    # ③ 报告单独提交，reviewed_sha = fix_sha（report-only 只动 openspec 顶层条目）
    _anchor_code_reports(repo, d, fix_sha, verify="PASS")
    # 两段时序：report-only 提交不动 src.py 顶层条目 ⇒ 两个消费方相对自己的锚均 fresh
    assert _code_stale(repo, _CR_REL) == (False, "fresh")
    assert _code_stale(repo, _VF_REL) == (False, "fresh")
    # 端到端：verify=PASS + active 存在 ⇒ RUN_VERIFY 收尾，绝不自锁成 RERUN_STALE
    code, js, _h = run_gate(repo)
    assert code == 0 and js["verdict"] != "RERUN_STALE", js


def test_code_review_single_stage_commit_would_self_lock(repo):
    """[5.13 变异对照 · ADR-7(a)] 时序退回单段（修复与报告塞进同一次提交）⇒ 锚只能取修复
    **前**的 HEAD ⇒ 修复落盘后源码顶层条目已变 ⇒ code 域相对自己的锚立刻失鲜（自锁）。
    这正是 ADR-7(a) 要消灭的形态；上一个用例证明两段时序修好它。
    双重变异角色：把 code 分支改成恒 `return False,"fresh"`，本例 stale 断言亦转红。"""
    d = impl_done(repo)
    (repo / "src.py").write_text("# 被代码审的源码 v1\n", encoding="utf-8")
    commit_all(repo, "seed 顶层源码进代码审基线")
    pre_fix = head_sha(repo)                   # 锚指修复**前**（单段时序的错误锚）
    # 单段：自动修复 + 报告同一次提交（_anchor_code_reports 内 git add -A 一并收编 src.py 改动）
    (repo / "src.py").write_text("# 自动修复后 [impl-review-fix]\n", encoding="utf-8")
    _anchor_code_reports(repo, d, pre_fix, verify="PASS")
    assert _code_stale(repo, _CR_REL) == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 0 and js["verdict"] == "RERUN_STALE" and js["next"] == "sdflow-code-review", js
    assert js["freshness"] == "stale"
