"""superpowers 轨回归（harden-implement-review-loop Task5 · tasks.md §7.6，评审 C2 的 dogfood 盲区）。

本仓自身 `openspec/config.yaml` 是 `impl-pipeline: tickets`——源仓 dogfood 天然照不到
superpowers 轨这条分支。本文件用**独立的 fixture 仓**（`repo` fixture，与本仓无关的临时
git 仓）验证 Task5 引入的两处新行为在 superpowers 轨下不误伤：

1. `ship_gate` 第四道校验（收尾票）**不对 superpowers 轨的 plan 生效**——无论
   `openspec/config.yaml` 里 `impl-pipeline` 取什么值，gate 只凭**计划文件名**
   （`tickets.md` vs `superpowers-plan.md`）决定要不要校验收尾票；旧名 plan 即使完全没有
   收尾票，也照常按 CONTINUE_IMPL/RUN_PLAN 推进，不会被误判 UNKNOWN。
2. `sdflow-implement/scripts/impl_route.py` 的 config→pipeline 解析本身不受本 change 影响
   （本 change 未改 `impl_route.py` 的 config/marker 解析逻辑）——`route` CLI 对
   `impl-pipeline: superpowers` 的 fixture 仍正确解析出 `pipeline=superpowers`。

**MUST NOT 真去改本仓 `openspec/config.yaml`**——以下全部操作只发生在 `tmp_path`/`repo`
fixture 临时仓内。

`sdflow-done/SKILL.md` 的 verify「实现期聚合覆盖」需求判「不适用（非 tickets 轨）」是**指令
文本**（该 skill 无 `scripts/`、无自身测试套件，见 CLAUDE.md「带脚本+测试的 skill 仅这几个」
清单，`sdflow-done` 不在其中），不是可执行判定——对应的正确性核验是 `sdflow-done/SKILL.md`
§第一步 Verify 里那段「superpowers 轨：该需求判不适用……MUST NOT 判 gap」的文字是否存在、
措辞是否与本表述一致，留在 impl-report 里人工复核，本文件覆盖的是与之配套的**机械**半
（gate 侧不误伤）。
"""
import subprocess
import sys
from pathlib import Path

from conftest import commit_all, mkchange, head_sha, write_report
from test_gate_preflight import run_gate

_scripts_path = str(Path(__file__).parent.parent / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)
import ship_gate as _sg  # noqa: E402

_IMPL_ROUTE = str(Path(__file__).resolve().parents[2] / "sdflow-implement" / "scripts")

PLAN_NO_CLOSER = (
    "### Task 1: A\n**Blocked-by:** none\n- [ ] s\n"
    "### Task 2: B\n**Blocked-by:** 1\n- [ ] s\n"
)


def _write_superpowers_config(repo):
    cfg_dir = repo / "openspec"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "config.yaml").write_text("impl-pipeline: superpowers\n", encoding="utf-8")


def test_config_superpowers_route_resolves_superpowers(repo):
    """impl_route.py 的 config 解析不受本 change 影响：superpowers 值仍正确解析。"""
    _write_superpowers_config(repo)
    d = mkchange(repo)
    (d / "proposal.md").write_text("# p\n", encoding="utf-8")
    commit_all(repo, "seed (superpowers track)")
    r = subprocess.run(
        [sys.executable, str(Path(_IMPL_ROUTE) / "impl_route.py"),
         "route", "--root", str(repo), "--change", "demo"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0
    assert "pipeline=superpowers" in r.stdout


def test_gate_run_plan_unaffected_by_config_pipeline_value(repo):
    """gate 的 RUN_PLAN 判据（计划文件缺）与 config.yaml 的 impl-pipeline 取值无关
    （ship_gate.py 本就不读 config.yaml——本 change 未改这条既有边界）。"""
    _write_superpowers_config(repo)
    d = mkchange(repo)
    (d / "proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")
    commit_all(repo, "seed change artifacts")
    write_report(d, "spec-review-report.md", head_sha(repo),
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report (approved)")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_PLAN"
    assert "tickets.md" in js["reason"] and "superpowers-plan.md" in js["reason"]


def test_gate_old_name_plan_without_closer_advances_under_superpowers_config(repo):
    """superpowers 轨（config=superpowers + 旧名 plan、且完全没有收尾票）——gate 第四道校验
    grandfather 生效，CONTINUE_IMPL 正常推进，不因「缺收尾票」被误判 UNKNOWN。"""
    _write_superpowers_config(repo)
    d = mkchange(repo)
    (d / "proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")
    (d / "superpowers-plan.md").write_text(PLAN_NO_CLOSER, encoding="utf-8")
    commit_all(repo, "seed change artifacts (superpowers track)")
    write_report(d, "spec-review-report.md", head_sha(repo),
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report (approved)")
    commit_all(repo, "checkpoint(task1-foo): done A")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["1"]
    assert "grandfather" in js["reason"].lower()


def test_plan_closing_ticket_check_ignores_config_reads_filename_only(tmp_path):
    """单元层直证：`plan_closing_ticket_check` 不读 config/marker，只看文件名——即使目录里
    放了 `impl-pipeline: superpowers` 的 config.yaml，判据不变。"""
    cfg_dir = tmp_path / "openspec"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.yaml").write_text("impl-pipeline: superpowers\n", encoding="utf-8")
    d = mkchange(tmp_path)
    plan = d / "superpowers-plan.md"
    plan.write_text(PLAN_NO_CLOSER, encoding="utf-8")
    ok, note = _sg.plan_closing_ticket_check(plan)
    assert ok is True and "grandfather" in note.lower()
