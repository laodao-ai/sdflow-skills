"""锚检测行锚定 + fence-aware（B4）：anchors_in / _line_scoped_hits。"""
import importlib.util
import json
import sys
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


def test_pick_exclusive_unbalanced_unknown(tmp_path, capsys):
    # 正锚在 fence 外 + 未闭合 ``` + 负锚在内被吞 → 不得判 pass，须 UNKNOWN
    # [impl-review-fix 修B/对抗镜2-F1] 仅断言 exit code == EXIT_UNKNOWN 不足以区分分支：
    # 两锚并存的 conflict 分支同样退出 EXIT_UNKNOWN。须同时断言 emit 的 JSON reason
    # 含"未闭合 fence"，确认真正命中的是 unbalanced 分支而非 conflict 分支。
    f = tmp_path / "verify-report.md"
    f.write_text(f"{VPASS}\n```\n{VFAIL}\n", encoding="utf-8")   # ``` 未闭合
    with pytest.raises(SystemExit) as e:
        _sg.pick_exclusive(f, VPASS, VFAIL, "verify")
    assert e.value.code == _sg.EXIT_UNKNOWN
    out = capsys.readouterr().out
    last_line = out.strip().splitlines()[-1]
    reason = json.loads(last_line)["reason"]
    assert "未闭合 fence" in reason


def test_archived_unbalanced_none(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "t"); _git(tmp_path, "config", "user.email", "t@t")
    d = tmp_path / "openspec" / "changes" / "archive" / "2026-07-05-demo"
    d.mkdir(parents=True)
    (d / "verify-report.md").write_text(f"{VPASS}\n```\n{VFAIL}\n", encoding="utf-8")
    _git(tmp_path, "add", "-A"); _git(tmp_path, "commit", "-q", "-m", "unb")
    assert _sg.archived_verify_state(tmp_path, "main", "2026-07-05-demo") == "none"


GATE = REPO / "sdflow-ship" / "scripts" / "ship_gate.py"


def _run_gate(root, change="demo"):
    r = subprocess.run([sys.executable, str(GATE), "--change", change, "--root", str(root)],
                       capture_output=True, text=True)
    lines = r.stdout.strip().splitlines()
    return r.returncode, (json.loads(lines[-1]) if lines else {})


def test_decide_b4_board_refuse_start(tmp_path):
    # B4 盘面：spec-review-report 仅描述性提及 design-approved（无独占锚）→ REFUSE_START
    from conftest import mkchange, commit_all
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "t"); _git(tmp_path, "config", "user.email", "t@t")
    d = mkchange(tmp_path, "demo")
    d.joinpath("proposal.md").write_text("〔TG-25：契约〕\n", encoding="utf-8")   # 非嵌入式，避免 RUN_SOP
    d.joinpath("spec-review-report.md").write_text(
        f"拍板后才写 `{DESIGN}`（当前未获批）。\n", encoding="utf-8")
    commit_all(tmp_path, "seed")
    code, js = _run_gate(tmp_path)
    assert code == 3 and js["verdict"] == "REFUSE_START"


def test_contract_archived_corpus_anchor_hits():
    # 契约：归档真实报告语料的独占锚行 → _line_scoped_hits 命中（防模板假设静默失效）
    # 样本源 = 归档 corpus（实证 15/15 独占顶格），非 SKILL 展示块
    archive = REPO / "openspec" / "changes" / "archive"
    samples = list(archive.glob("*/spec-review-report.md")) + \
              list(archive.glob("*/verify-report.md")) + \
              list(archive.glob("*/code-review-report.md"))
    assert samples, "无归档报告语料"
    # [impl-review-fix 修C/对抗镜2-F2] 空转兜底：若语料存在但无一篇含任何已知锚子串，
    # 内层断言全程不执行，测试会"假绿"（看似通过实则未验证任何东西）。加计数器兜底。
    checked = 0
    for f in samples:
        text = f.read_text(encoding="utf-8", errors="replace")
        for anc in _sg.ALL_ANCHORS:
            if anc in text:   # 该报告含此锚（子串层）
                checked += 1
                hits, _ = _sg._line_scoped_hits(text, [anc])
                assert anc in hits, f"{f.name} 的真锚 {anc} 行级判据下漏检——模板锚未独占一行?"
    assert checked > 0, "契约测试未匹配到任何真锚，可能已空转"
