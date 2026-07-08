"""熔断状态集合判据（T26/SR-1；mlh-p5 Task6 D11）：判据 = 该步 ship-gate **frontmatter
状态集合**是否变化，HEAD 移动/mtime 变化 MUST NOT 作免疫信号。inline 锚已随 live 读点退役，
不再参与熔断进展判据。anchor_set/breaker_no_progress 均为纯函数/无状态 helper（无副作用、
不落地文件），复用 parse_ship_gate_frontmatter 的 frontmatter 状态解析（与 live 读点单核一致）。
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

_FM_VERIFY_PASS = "---\nship-gate:\n  verify: PASS\n---\n# 报告\n"
_FM_VERIFY_FAIL = "---\nship-gate:\n  verify: FAIL\n---\n# 报告\n"


def test_no_progress_when_state_set_unchanged():
    text = "# 报告\n结论：未过\n"           # 无 frontmatter → 状态集空
    before = anchor_set(text)
    after = anchor_set(text)
    assert before == frozenset() and after == frozenset()
    assert breaker_no_progress(before, after) is True


def test_progress_when_new_frontmatter_state_added():
    # [mlh-p5 Task6 D11] before 无 frontmatter 状态、after 仅 frontmatter verify: PASS
    # → 状态集有净变化 → breaker 判有进展（False）。这是迁 frontmatter 状态集判据的核心正例。
    before = anchor_set("# 报告\n结论：未过\n")            # 无状态 → 空集
    after = anchor_set(_FM_VERIFY_PASS)                    # {('verify','PASS')}
    assert before == frozenset() and after == frozenset({("verify", "PASS")})
    assert breaker_no_progress(before, after) is False


def test_inline_anchor_ignored_by_state_set():
    # [mlh-p5 Task6 D11] anchor_set 迁 frontmatter 后，正文 inline 锚不再计入状态集——
    # 两份文本 inline 锚不同（一份加了 FAIL 反锚）但均无 frontmatter 状态 → 状态集皆空 →
    # 判无进展（熔断不被正文残留 inline 锚欺骗，与 live 读点退役 inline 一致）。
    before = anchor_set(f"# 报告\n{ANCHOR_VERIFY_PASS}\n")
    after = anchor_set(f"# 报告\n{ANCHOR_VERIFY_PASS}\n{ANCHOR_VERIFY_FAIL}\n")
    assert before == frozenset() and after == frozenset()
    assert breaker_no_progress(before, after) is True


def test_progress_when_state_value_changes():
    # frontmatter 状态值翻转（PASS→FAIL）也是净变化 → 判有进展。
    before = anchor_set(_FM_VERIFY_PASS)
    after = anchor_set(_FM_VERIFY_FAIL)
    assert before != after
    assert breaker_no_progress(before, after) is False


def test_failsafe_missing_snapshot():
    after = anchor_set(_FM_VERIFY_PASS)
    assert breaker_no_progress(None, after) is True


def test_failsafe_missing_after_snapshot():
    # [impl-review-fix CR-2] after=None（重跑后报告不存在/不可读）同样保守判无进展，
    # 防非空 before + after=None 被误判"有进展"假放行。
    before = anchor_set(_FM_VERIFY_PASS)
    assert breaker_no_progress(before, None) is True
    assert breaker_no_progress(None, None) is True


def test_bad_frontmatter_empty_state():
    # [mlh-p5 Task6 D11] 坏 frontmatter（duplicate-key）→ anchor_set 保守返空集
    # （无净变化倾向判无进展，不因坏结构假造进展信号）。
    bad = "---\nship-gate:\n  verify: PASS\n  verify: FAIL\n---\n# 报告\n"
    assert anchor_set(bad) == frozenset()


def test_anchor_set_absent_on_unclosed_frontmatter():
    # [T74/BR-1] 钉死「挪格子不改熔断进展判据」：首行 --- 无第二个 --- 改判 absent 后，
    # anchor_set 仍返回空集（与旧 unterminated 行为一致），防未来重构 anchor_set 短路时无声失守。
    assert anchor_set("---\nship-gate:\n  verify: PASS\n") == frozenset()
