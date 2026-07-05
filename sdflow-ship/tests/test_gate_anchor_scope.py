"""锚检测行锚定 + fence-aware（B4）：anchors_in / _line_scoped_hits。"""
import importlib.util
from pathlib import Path
import subprocess
import pytest

REPO = Path(__file__).resolve().parents[2]
_gate_path = REPO / "sdflow-ship" / "scripts" / "ship_gate.py"
_spec = importlib.util.spec_from_file_location("ship_gate", _gate_path)
_sg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sg)   # __main__ 守卫，加载无副作用

DESIGN = "<!-- ship-gate: design-approved -->"
VPASS = "<!-- ship-gate: verify=PASS -->"
VFAIL = "<!-- ship-gate: verify=FAIL -->"


def _git(root, *a):
    subprocess.run(["git", "-C", str(root), *a], check=True, capture_output=True, text=True)


def test_inline_mention_not_hit(tmp_path):
    # B4 活体复现：锚内联在描述句中（行内反引号），非独占一行 → 不命中
    f = tmp_path / "spec-review-report.md"
    f.write_text(f"拍板后才写 `{DESIGN}`（当前未获批）。\n", encoding="utf-8")
    assert _sg.anchors_in(f, [DESIGN]) == []


def test_fenced_anchor_not_hit(tmp_path):
    # 锚独占一行但在 ``` 代码块内作文档示例 → 不命中（ADR-2）
    f = tmp_path / "spec-review-report.md"
    f.write_text(f"结论区\n```\n{DESIGN}\n```\n正文无真锚\n", encoding="utf-8")
    assert _sg.anchors_in(f, [DESIGN]) == []


def test_standalone_anchor_hit(tmp_path):
    # 独占一行的真锚（前后可有空白）→ 命中
    f = tmp_path / "spec-review-report.md"
    f.write_text(f"结论\n\n   {DESIGN}   \n", encoding="utf-8")
    assert _sg.anchors_in(f, [DESIGN]) == [DESIGN]


def test_conflict_multi_hit(tmp_path):
    # PASS 与 FAIL 各独占一行并存 → 两者皆命中（保 ADR-3 多命中）
    f = tmp_path / "verify-report.md"
    f.write_text(f"{VPASS}\n{VFAIL}\n", encoding="utf-8")
    got = _sg.anchors_in(f, [VPASS, VFAIL])
    assert VPASS in got and VFAIL in got


def test_core_descriptive_pass_not_hit():
    # 核心单元：描述性提及 PASS 的文本 → hits 不含 PASS
    text = f"归档说明：曾写过 `{VPASS}` 但后撤。\n```\n{VPASS}\n```\n"
    hits, unbalanced = _sg._line_scoped_hits(text, [VPASS, VFAIL])
    assert VPASS not in hits


def test_archived_descriptive_pass_none(tmp_path):
    # 端到端：git fixture，归档 verify-report 仅描述性提及 PASS（无真锚）→ archived_verify_state 判 none
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "t"); _git(tmp_path, "config", "user.email", "t@t")
    d = tmp_path / "openspec" / "changes" / "archive" / "2026-07-05-demo"
    d.mkdir(parents=True)
    (d / "verify-report.md").write_text(f"结论待定；模板锚示例：`{VPASS}`。\n", encoding="utf-8")
    _git(tmp_path, "add", "-A"); _git(tmp_path, "commit", "-q", "-m", "arch")
    assert _sg.archived_verify_state(tmp_path, "main", "2026-07-05-demo") == "none"


def test_archived_true_pass_and_conflict(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "t"); _git(tmp_path, "config", "user.email", "t@t")
    d = tmp_path / "openspec" / "changes" / "archive" / "2026-07-05-demo"
    d.mkdir(parents=True)
    (d / "verify-report.md").write_text(f"{VPASS}\n", encoding="utf-8")
    _git(tmp_path, "add", "-A"); _git(tmp_path, "commit", "-q", "-m", "pass")
    assert _sg.archived_verify_state(tmp_path, "main", "2026-07-05-demo") == "pass"
    (d / "verify-report.md").write_text(f"{VPASS}\n{VFAIL}\n", encoding="utf-8")
    _git(tmp_path, "add", "-A"); _git(tmp_path, "commit", "-q", "-m", "conflict")
    assert _sg.archived_verify_state(tmp_path, "main", "2026-07-05-demo") == "conflict"


def test_pick_exclusive_unbalanced_unknown(tmp_path):
    # 正锚在 fence 外 + 未闭合 ``` + 负锚在内被吞 → 不得判 pass，须 UNKNOWN
    f = tmp_path / "verify-report.md"
    f.write_text(f"{VPASS}\n```\n{VFAIL}\n", encoding="utf-8")   # ``` 未闭合
    with pytest.raises(SystemExit) as e:
        _sg.pick_exclusive(f, VPASS, VFAIL, "verify")
    assert e.value.code == _sg.EXIT_UNKNOWN


def test_archived_unbalanced_none(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "t"); _git(tmp_path, "config", "user.email", "t@t")
    d = tmp_path / "openspec" / "changes" / "archive" / "2026-07-05-demo"
    d.mkdir(parents=True)
    (d / "verify-report.md").write_text(f"{VPASS}\n```\n{VFAIL}\n", encoding="utf-8")
    _git(tmp_path, "add", "-A"); _git(tmp_path, "commit", "-q", "-m", "unb")
    assert _sg.archived_verify_state(tmp_path, "main", "2026-07-05-demo") == "none"
