import json, subprocess, sys
from pathlib import Path
from conftest import commit_all, mkchange

GATE = Path(__file__).resolve().parents[1] / "scripts" / "ship_gate.py"

def run_gate(root, change="demo"):
    r = subprocess.run([sys.executable, str(GATE), "--change", change,
                        "--root", str(root)], capture_output=True, text=True)
    lines = r.stdout.strip().splitlines()
    payload = json.loads(lines[-1]) if lines else {}
    return r.returncode, payload, lines[0] if lines else ""

def test_refuse_when_report_missing(repo):
    mkchange(repo); commit_all(repo, "seed")
    code, js, human = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"
    assert "补锚" in js["reason"]  # exit3 文案含人工补锚指引（D2）

def test_refuse_when_anchor_missing(repo):
    d = mkchange(repo)
    (d / "spec-review-report.md").write_text("# 报告\n结论：通过\n", encoding="utf-8")
    commit_all(repo, "seed")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"

def test_pass_gate_when_anchor_present(repo):
    d = mkchange(repo)
    (d / "spec-review-report.md").write_text(
        "# 报告\n<!-- ship-gate: design-approved -->\n", encoding="utf-8")
    commit_all(repo, "seed")
    code, js, human = run_gate(repo)
    assert code == 0 and js["verdict"] != "REFUSE_START"
    assert human.startswith("[ship-gate]")  # D2 首行人读

def test_verify_conflict_anchors_unknown(repo):
    d = mkchange(repo)
    (d / "spec-review-report.md").write_text(
        "<!-- ship-gate: design-approved -->\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        "<!-- ship-gate: verify=PASS -->\n<!-- ship-gate: verify=FAIL -->\n",
        encoding="utf-8")
    commit_all(repo, "seed")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert "verify" in js["reason"]
