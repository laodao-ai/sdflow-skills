"""熔断锚行集合判据（T26/SR-1）：判据 = 该步 ship-gate 锚行集合是否变化，
HEAD 移动/mtime 变化 MUST NOT 作免疫信号。anchor_set/breaker_no_progress 均为
纯函数/无状态 helper（无副作用、不落地文件），复用 _line_scoped_hits 的行级锚匹配语义。
"""
import importlib.util
from pathlib import Path

# 同 test_producer_parser_contract.py 的按文件路径 importlib 加载口径：
# 不用 sys.path.insert（避免污染全套件 sys.path/sys.modules），ship_gate.py 有
# __main__ 守卫，加载本身无副作用。
REPO = Path(__file__).resolve().parents[2]
_gate_path = REPO / "sdflow-ship" / "scripts" / "ship_gate.py"
_spec = importlib.util.spec_from_file_location("ship_gate", _gate_path)
_ship_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ship_gate)

anchor_set = _ship_gate.anchor_set
breaker_no_progress = _ship_gate.breaker_no_progress
ANCHOR_VERIFY_PASS = _ship_gate.ANCHOR_VERIFY_PASS
ANCHOR_VERIFY_FAIL = _ship_gate.ANCHOR_VERIFY_FAIL


def test_no_progress_when_anchor_set_unchanged():
    text = "# 报告\n结论：未过\n"
    before = anchor_set(text)
    after = anchor_set(text)
    assert breaker_no_progress(before, after) is True


def test_progress_when_new_anchor_added():
    before = anchor_set("# 报告\n结论：未过\n")
    after = anchor_set(f"# 报告\n结论：未过\n{ANCHOR_VERIFY_FAIL}\n")
    assert breaker_no_progress(before, after) is False


def test_failsafe_missing_snapshot():
    after = anchor_set(f"# 报告\n{ANCHOR_VERIFY_PASS}\n")
    assert breaker_no_progress(None, after) is True
