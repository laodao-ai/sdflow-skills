"""[implement-workflow-optimization-2026-08-p4 Task3] B25/B26 机械门测试群。

① 锚存在门：`metrics.enabled=true` 时 code-review 报告须含 `layer="code-review"` 的
   lens-metric 锚 + `sdflow:ref-check` 结构化锚；spec-review 报告在 design 门同款只需
   `layer="spec-review"` 的 lens-metric 锚（无 ref-check 要求——那是 code-review 独有的
   Step3 引用核落盘信号）。`metrics.enabled` 缺省/false/config 文件不存在 = 放行；
   config 存在但不可解析（yq 非零退出，或值非法布尔）= fail-closed UNKNOWN(6)。
② defer 对账门：defer 台账表格「id」列每格须整格恰为单个 `T\\d+`/`B\\d+`，对应
   `openspec/issues/open/**/<id>.md` 文件系统存在且 frontmatter `source_change` 等于
   当前 change；台账行判别窄化——只认声明了 id 列的表格数据行，MUST NOT 全行子串搜索。

两门 verdict 均字面复用既有 `STEP_IN_PROGRESS`（Global Constraints 硬约束）。
"""
import sys
from pathlib import Path

import pytest

from conftest import commit_all, mkchange, head_sha, write_report
from test_gate_preflight import run_gate
from test_gate_tail import impl_done
from test_gate_impl_progress import PLAN2_TICKETS

_scripts_path = str(Path(__file__).resolve().parents[1] / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)
import ship_gate as _sg  # noqa: E402

# ── anchor_lint.py 的 `_metrics_enabled`：design.md scope-check 表要求与 ship_gate 的
# `metrics_enabled` 两处独立实现保持一致语义，见 test_metrics_enabled_parity_with_anchor_lint。
_repo_root = Path(__file__).resolve().parents[2]
_anchor_lint_dir = str(_repo_root / "sdflow-init" / "assets" / "workflow" / "tools")
if _anchor_lint_dir not in sys.path:
    sys.path.insert(0, _anchor_lint_dir)
import anchor_lint as _al  # noqa: E402


LENS_METRIC_CR = ('<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" '
                   'runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="1" 独立="0" '
                   'sev="致0/高0/中0/低0" -->')
LENS_METRIC_SR = ('<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" '
                   'runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" '
                   'sev="致0/高0/中0/低0" -->')
REF_CHECK = '<!-- sdflow:ref-check v1 status="clean" pass="0" fail="0" uncheckable="0" -->'


def write_config_metrics(root, value):
    """写 `openspec/config.yaml` 的 `metrics.enabled: <value>`（value 为已格式化好的 YAML
    字面量文本，如 `"true"`/`"false"`/`'"yes"'`）。"""
    d = root / "openspec"
    d.mkdir(parents=True, exist_ok=True)
    (d / "config.yaml").write_text(f"metrics:\n  enabled: {value}\n", encoding="utf-8")


def write_pool_file(root, pool, id_, source_change):
    """写一份最小 issues 池文件（frontmatter 逐字对齐 issues_v2.py 实产格式，见
    `openspec/issues/open/bug/B25.md` 真实样本）。"""
    p = root / "openspec" / "issues" / "open" / pool
    p.mkdir(parents=True, exist_ok=True)
    (p / f"{id_}.md").write_text(
        "---\n"
        f'id: "{id_}"\n'
        f'pool: "{pool}"\n'
        'status: "OPEN"\n'
        'priority: "P2"\n'
        f'source_change: "{source_change}"\n'
        'summary: "test"\n'
        "---\n",
        encoding="utf-8")


def impl_done_with_sr_anchor(repo):
    """同 `test_gate_tail.impl_done`，但 spec-review-report.md 携带
    `layer="spec-review"` 的 lens-metric 锚。metrics.enabled=true 时设计门本身也核验该锚
    （B25 同款①，对每次 decide() 调用都生效，非只在实现窗口）——本文件的用例聚焦
    code-review 层，若不带此锚，任何把 metrics 打开的测试都会先在设计门被拦下，
    够不着要测的 code-review 层两道新门。
    """
    d = mkchange(repo)
    (d / "proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")
    (d / "tickets.md").write_text(PLAN2_TICKETS, encoding="utf-8")
    commit_all(repo, "seed change artifacts")
    sha = head_sha(repo)
    write_report(d, "spec-review-report.md", sha,
                 body="# 设计审报告\n" + LENS_METRIC_SR + "\n", design_approved="true")
    commit_all(repo, "spec-review report (approved)")
    commit_all(repo, "checkpoint(task1-a): A")
    commit_all(repo, "checkpoint(task2-b): B")
    return d


def cr_body(*, anchors=True, defer_id=None, extra_table=False):
    parts = ["# code-review 报告\n"]
    if anchors:
        parts.append(LENS_METRIC_CR + "\n" + REF_CHECK + "\n")
    if defer_id:
        parts.append(
            "### 修复 / defer 台账\n"
            "| 类型 | id | 说明 |\n"
            "|---|---|---|\n"
            f"| defer | {defer_id} | 示例 defer 项，引用旧票 T105 仅作说明不参与对账 |\n")
    if extra_table:
        parts.append(
            "### Findings（已采纳）\n"
            "| 严重度 | 位置 | 说明 |\n"
            "|---|---|---|\n"
            "| 高 | a.go:1 | 提及旧票 T105 的说明不应被误抓 |\n")
    return "".join(parts)


# ══════════════════════ metrics_enabled 四态 ══════════════════════

def test_metrics_enabled_false_when_config_missing(tmp_path):
    assert _sg.metrics_enabled(tmp_path) is False


def test_metrics_enabled_false_when_metrics_block_absent(tmp_path):
    (tmp_path / "openspec").mkdir()
    (tmp_path / "openspec" / "config.yaml").write_text("other: 1\n", encoding="utf-8")
    assert _sg.metrics_enabled(tmp_path) is False


def test_metrics_enabled_false_when_enabled_key_absent(tmp_path):
    (tmp_path / "openspec").mkdir()
    (tmp_path / "openspec" / "config.yaml").write_text("metrics:\n  other: 1\n", encoding="utf-8")
    assert _sg.metrics_enabled(tmp_path) is False


def test_metrics_enabled_true(tmp_path):
    write_config_metrics(tmp_path, "true")
    assert _sg.metrics_enabled(tmp_path) is True


def test_metrics_enabled_explicit_false(tmp_path):
    write_config_metrics(tmp_path, "false")
    assert _sg.metrics_enabled(tmp_path) is False


def test_metrics_enabled_fail_closed_on_non_bool_value(tmp_path):
    write_config_metrics(tmp_path, '"yes"')
    with pytest.raises(_sg.GateIndeterminate) as exc:
        _sg.metrics_enabled(tmp_path)
    assert exc.value.category == _sg.CAUSE_CONFIG_UNPARSEABLE


def test_metrics_enabled_fail_closed_on_bad_yaml_syntax(tmp_path):
    (tmp_path / "openspec").mkdir()
    (tmp_path / "openspec" / "config.yaml").write_bytes(b"metrics:\n\tenabled: true\n")
    with pytest.raises(_sg.GateIndeterminate) as exc:
        _sg.metrics_enabled(tmp_path)
    assert exc.value.category == _sg.CAUSE_CONFIG_UNPARSEABLE


def test_metrics_enabled_parity_with_anchor_lint(tmp_path):
    """design.md scope-check 表：`ship_gate.metrics_enabled` 与
    `anchor_lint.py::_metrics_enabled` 是 metrics.enabled 四态语义的两处独立实现——
    改一处必查另一处。本测试对同一组 config.yaml 状态断言两者好态结果一致、坏态同拒绝。
    """
    root = tmp_path
    assert _sg.metrics_enabled(root) is _al._metrics_enabled(root) is False   # ①文件不存在
    (root / "openspec").mkdir()
    (root / "openspec" / "config.yaml").write_text("metrics:\n  other: 1\n", encoding="utf-8")
    assert _sg.metrics_enabled(root) is _al._metrics_enabled(root) is False   # ②键缺失
    for v, want in (("true", True), ("false", False)):
        (root / "openspec" / "config.yaml").write_text(f"metrics:\n  enabled: {v}\n", encoding="utf-8")
        assert _sg.metrics_enabled(root) is want                              # ④合法布尔
        assert _al._metrics_enabled(root) is want
    (root / "openspec" / "config.yaml").write_text('metrics:\n  enabled: "yes"\n', encoding="utf-8")
    with pytest.raises(Exception):
        _sg.metrics_enabled(root)                                             # ③坏值两者均拒
    with pytest.raises(Exception):
        _al._metrics_enabled(root)


# ══════════════════════ 锚检测（fence-aware）══════════════════════

def test_lens_metric_layer_present_matches_layer():
    assert _sg._lens_metric_layer_present(LENS_METRIC_CR, "code-review") is True
    assert _sg._lens_metric_layer_present(LENS_METRIC_CR, "spec-review") is False


def test_lens_metric_anchor_inside_fence_ignored():
    text = "正文无真锚\n```\n" + LENS_METRIC_CR + "\n```\n"
    assert _sg._lens_metric_layer_present(text, "code-review") is False


def test_ref_check_present_and_fence_ignored():
    assert _sg._ref_check_present(REF_CHECK) is True
    assert _sg._ref_check_present("```\n" + REF_CHECK + "\n```\n") is False


# ══════════════════════ defer 台账提取（窄化 + fence-aware）══════════════════════

def test_defer_ledger_extracts_id_column_only():
    text = cr_body(anchors=False, defer_id="T900")
    assert _sg._defer_ledger_id_cells(text) == ["T900"]


def test_defer_ledger_description_column_old_id_not_extracted():
    # id 列含真实新 id，说明列提及旧票 T105——只应抓到 id 列那一个。
    text = cr_body(anchors=False, defer_id="B26")
    assert _sg._defer_ledger_id_cells(text) == ["B26"]


def test_defer_ledger_table_without_id_column_not_scanned():
    # Findings 表无 id 列，即便内容提及票号也不落入台账提取。
    text = cr_body(anchors=False, extra_table=True)
    assert _sg._defer_ledger_id_cells(text) == []


def test_defer_ledger_aggregate_summary_sentence_no_pipe_ignored():
    text = "### 修复 / defer 台账\n自动修 2 项[impl-review-fix]；defer 1 项 → buglist/todolist\n"
    assert _sg._defer_ledger_id_cells(text) == []


def test_defer_ledger_fenced_table_ignored():
    text = ("### 修复 / defer 台账\n无实际 defer\n```\n| 类型 | id | 说明 |\n|---|---|---|\n"
            "| defer | T999 | 围栏内锚样例 |\n```\n")
    assert _sg._defer_ledger_id_cells(text) == []


def test_defer_ledger_malformed_id_cell_extracted_as_is():
    text = ("### 修复 / defer 台账\n| 类型 | id | 说明 |\n|---|---|---|\n"
            "| defer | 已入 todolist | 无真实 id |\n")
    assert _sg._defer_ledger_id_cells(text) == ["已入 todolist"]


# ══════════════════════ CLI 端到端：锚存在门（code-review 层）══════════════════════

def test_cr_pass_through_when_config_file_entirely_missing(repo):
    # 台账窄化/config 缺文件双向坑之一：不写 openspec/config.yaml，report 无任何度量锚，
    # 且无 defer 台账——本门须放行（不因缺锚被拦），推进到 RUN_VERIFY。
    d = impl_done(repo)
    write_report(d, "code-review-report.md", head_sha(repo),
                 body=cr_body(anchors=False), code_review="pass")
    commit_all(repo, "cr")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RUN_VERIFY"


def test_cr_pass_through_when_metrics_default_false(repo):
    write_config_metrics(repo, "false")
    d = impl_done(repo)
    write_report(d, "code-review-report.md", head_sha(repo),
                 body=cr_body(anchors=False), code_review="pass")
    commit_all(repo, "cr")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RUN_VERIFY"


def test_cr_blocked_when_metrics_on_and_anchors_missing(repo):
    write_config_metrics(repo, "true")
    d = impl_done_with_sr_anchor(repo)
    write_report(d, "code-review-report.md", head_sha(repo),
                 body=cr_body(anchors=False), code_review="pass")
    commit_all(repo, "cr")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS" and js["next"] == "sdflow-code-review"
    assert "lens-metric" in js["reason"] and "ref-check" in js["reason"]


def test_cr_blocked_when_metrics_on_and_only_ref_check_missing(repo):
    write_config_metrics(repo, "true")
    d = impl_done_with_sr_anchor(repo)
    body = "# code-review 报告\n" + LENS_METRIC_CR + "\n"
    write_report(d, "code-review-report.md", head_sha(repo), body=body, code_review="pass")
    commit_all(repo, "cr")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS"
    assert "sdflow:ref-check" in js["reason"] and "sdflow:lens-metric" not in js["reason"]


def test_cr_fail_closed_when_metrics_unparseable(repo):
    write_config_metrics(repo, '"maybe"')
    d = impl_done(repo)
    write_report(d, "code-review-report.md", head_sha(repo),
                 body=cr_body(anchors=False), code_review="pass")
    commit_all(repo, "cr")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert js["cause_category"] == "config-unparseable"


def test_cr_passes_when_metrics_on_and_anchors_present(repo):
    write_config_metrics(repo, "true")
    d = impl_done_with_sr_anchor(repo)
    write_report(d, "code-review-report.md", head_sha(repo),
                 body=cr_body(anchors=True), code_review="pass")
    commit_all(repo, "cr")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RUN_VERIFY"


# ══════════════════════ CLI 端到端：锚存在门（spec-review/design 门）══════════════════════

def test_design_gate_pass_through_when_metrics_off(repo):
    d = mkchange(repo)
    commit_all(repo, "seed")
    write_report(d, "spec-review-report.md", head_sha(repo),
                 body="# 报告\n", design_approved="true")
    commit_all(repo, "sr")
    code, js, _ = run_gate(repo)
    assert js["verdict"] != "REFUSE_START"   # 过设计门（未被本门牵连拦下）


def test_design_gate_blocked_when_metrics_on_and_anchor_missing(repo):
    write_config_metrics(repo, "true")
    d = mkchange(repo)
    commit_all(repo, "seed")
    write_report(d, "spec-review-report.md", head_sha(repo),
                 body="# 报告\n", design_approved="true")
    commit_all(repo, "sr")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS" and js["next"] == "sdflow-spec-review"
    assert "转换态" in js["reason"] or "重跑" in js["reason"]


def test_design_gate_passes_when_metrics_on_and_anchor_present(repo):
    write_config_metrics(repo, "true")
    d = mkchange(repo)
    commit_all(repo, "seed")
    body = "# 报告\n" + LENS_METRIC_SR + "\n"
    write_report(d, "spec-review-report.md", head_sha(repo), body=body, design_approved="true")
    commit_all(repo, "sr")
    code, js, _ = run_gate(repo)
    assert js["verdict"] not in ("REFUSE_START", "STEP_IN_PROGRESS")


# ══════════════════════ CLI 端到端：defer 对账门 ══════════════════════

def test_defer_gate_passes_with_valid_id_and_pool_file(repo):
    d = impl_done(repo)
    write_pool_file(repo, "todo", "T900", "demo")
    write_report(d, "code-review-report.md", head_sha(repo),
                 body=cr_body(anchors=False, defer_id="T900"), code_review="pass")
    commit_all(repo, "cr")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RUN_VERIFY"


def test_defer_gate_blocked_when_id_missing(repo):
    d = impl_done(repo)
    body = ("# code-review 报告\n### 修复 / defer 台账\n| 类型 | id | 说明 |\n|---|---|---|\n"
            "| defer | 已入 todolist | 无真实 id |\n")
    write_report(d, "code-review-report.md", head_sha(repo), body=body, code_review="pass")
    commit_all(repo, "cr")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS" and js["next"] == "sdflow-code-review"
    assert "id 列内容非法" in js["reason"]


def test_defer_gate_blocked_when_pool_file_missing(repo):
    d = impl_done(repo)
    write_report(d, "code-review-report.md", head_sha(repo),
                 body=cr_body(anchors=False, defer_id="T901"), code_review="pass")
    commit_all(repo, "cr")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS"
    assert "文件系统不存在" in js["reason"]


def test_defer_gate_blocked_when_source_change_mismatched(repo):
    d = impl_done(repo)
    write_pool_file(repo, "todo", "T902", "some-other-change")
    write_report(d, "code-review-report.md", head_sha(repo),
                 body=cr_body(anchors=False, defer_id="T902"), code_review="pass")
    commit_all(repo, "cr")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS"
    assert "some-other-change" in js["reason"]


def test_defer_gate_passes_when_pool_file_uncommitted(repo):
    # B26 用文件系统存在性判定，MUST NOT 走 git 跟踪清单——池文件写盘但不 add/commit 也应通过。
    # 🔴 `commit_all` 内部 `git add -A`，若在其之前写池文件会被顺手一并提交、测不出「未跟踪」
    # 这个分支——池文件须落在**最后一次** commit_all **之后**，run_gate 执行时才是真未跟踪。
    d = impl_done(repo)
    write_report(d, "code-review-report.md", head_sha(repo),
                 body=cr_body(anchors=False, defer_id="B900"), code_review="pass")
    commit_all(repo, "cr")   # 报告已提交；池文件此刻尚不存在
    write_pool_file(repo, "bug", "B900", "demo")   # 写盘后不再 commit_all——工作树未跟踪文件
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RUN_VERIFY"


def test_defer_gate_ignores_description_column_old_ticket_reference(repo):
    # 台账窄化负例：id 列合法，说明列提及旧票 T105——不应被误抓进对账（若误抓，T105 池文件
    # 不存在或 source_change 不符会导致本该通过的用例被误拦）。
    d = impl_done(repo)
    write_pool_file(repo, "todo", "T903", "demo")
    write_report(d, "code-review-report.md", head_sha(repo),
                 body=cr_body(anchors=False, defer_id="T903"), code_review="pass")
    commit_all(repo, "cr")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RUN_VERIFY"
