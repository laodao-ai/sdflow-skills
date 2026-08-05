"""tickets 外衣 golden-file 回归：fixtures/tickets_plan_*.md（模拟真实出 ticket 产物）
过 ship_gate 既有三道校验（fence-aware 解析 / 标题重号 / 复选框双通道）——钉住 sdflow-implement
出 ticket 模式产出的「试验期外衣」形状与 gate 既有契约始终兼容（matt-workflow-integration Task 5，
design F5/F1）。gate 零改动铁律：若断言与 gate 实际行为不符，改 fixture 不改 ship_gate.py。"""
import importlib.util
from pathlib import Path

# 同 test_producer_parser_contract.py 的 import 先例：importlib 按文件路径显式加载，
# 不碰 sys.path / sys.modules，避免仓根 pytest 发现同名 scripts/ship_gate.py 时的模块复用隐患。
REPO = Path(__file__).resolve().parents[2]
_gate_path = REPO / "sdflow-ship" / "scripts" / "ship_gate.py"
_spec = importlib.util.spec_from_file_location("ship_gate", _gate_path)
_ship_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ship_gate)  # ship_gate.py 有 __main__ 守卫，加载无副作用

plan_task_ids = _ship_gate.plan_task_ids
plan_unbalanced_fence = _ship_gate.plan_unbalanced_fence
plan_has_duplicate_task = _ship_gate.plan_has_duplicate_task
checkbox_done_ids = _ship_gate.checkbox_done_ids

FIXTURES = Path(__file__).parent / "fixtures"
GOLDEN = FIXTURES / "tickets_plan_golden.md"
FENCE_DANGLING = FIXTURES / "tickets_plan_fence_dangling.md"
FENCED_HEADER = FIXTURES / "tickets_plan_fenced_header.md"


def test_golden_task_ids():
    # 4 张 ticket（### Task 1/2/3/4:），含收尾票（T250）；frontmatter 的 `impl-pipeline: tickets`
    # 单键行不匹配 TASK_TITLE_RE，不产生幻影任务号。
    assert plan_task_ids(GOLDEN) == {"1", "2", "3", "4"}


def test_golden_no_unbalanced_fence():
    assert plan_unbalanced_fence(GOLDEN) is False


def test_golden_no_duplicate_task():
    assert plan_has_duplicate_task(GOLDEN) is False


def test_golden_checkbox_done_ids():
    # Task 1 两项验收复选框全勾 [x] → 计入完成集；Task 2/3 未勾 → 不计入。
    # frontmatter 行（无 `- [ ]` 形状）不产生幻影完成号。
    assert checkbox_done_ids(GOLDEN) == {"1"}


def test_fenced_header_does_not_leak_task_id():
    # fence 内的伪 `### Task 9:` 标题对 fence-aware 解析不可见，不应污染任务号集。
    task_ids = plan_task_ids(FENCED_HEADER)
    assert "9" not in task_ids
    assert task_ids == {"1", "2", "3"}


def test_golden_closing_ticket_blocked_by_all(tmp_path):
    """T250：收尾票 Blocked-by 列出全部前置票号。"""
    text = GOLDEN.read_text(encoding="utf-8")
    import re
    blocked_by_lines = re.findall(r"\*\*Blocked-by:\*\*\s*(.+)", text)
    # 最后一张（Task 4）的 Blocked-by 须包含所有前置票号
    last_blocked = blocked_by_lines[-1]
    for tid in ("1", "2", "3"):
        assert tid in last_blocked, f"收尾票 Blocked-by 未包含 Task {tid}"


def test_golden_closing_ticket_rid_all():
    """T250：收尾票 R-ID 为 all。"""
    text = GOLDEN.read_text(encoding="utf-8")
    import re
    rid_lines = re.findall(r"\*\*R-ID:\*\*\s*(.+)", text)
    assert rid_lines[-1].strip() == "all"


def test_fence_dangling_detected_unbalanced():
    # EOF 前有一个未闭合的 ``` 围栏 → fail-safe UNKNOWN 判据依据的悬空围栏检测须命中。
    assert plan_unbalanced_fence(FENCE_DANGLING) is True
