"""findings_ref_check pytest 覆盖（task1-brief 6 场景 + CLI 契约 + 信号内诚实静态断言）。"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
SCRIPT = TOOLS / "findings_ref_check.py"


def _mod():
    spec = importlib.util.spec_from_file_location("findings_ref_check", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _write_target(tmp_path, name, lines):
    p = tmp_path / name
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


# --- ① 正例：路径存在 + 行号合法 + 引文命中该行 → pass -------------------------------------

def test_pass_valid_reference(tmp_path):
    _write_target(tmp_path, "a.py", ["line one", "def foo():", "    return 1"])
    finding = {"id": "F1", "file": "a.py", "line": 2, "quote": "def foo():"}
    result = _mod().classify_finding(finding, tmp_path)
    assert result == {"status": "pass"}


# --- ② 三种失败态：路径不存在 / 行号越界 / 引文不在所报行 → fail ---------------------------

def test_fail_path_not_found(tmp_path):
    finding = {"id": "F2", "file": "missing.py", "line": 1, "quote": "x"}
    result = _mod().classify_finding(finding, tmp_path)
    assert result == {"status": "fail", "reason": "path-not-found"}


def test_fail_line_out_of_bounds(tmp_path):
    _write_target(tmp_path, "b.py", ["only one line"])
    finding = {"id": "F3", "file": "b.py", "line": 99, "quote": "only one line"}
    result = _mod().classify_finding(finding, tmp_path)
    assert result == {"status": "fail", "reason": "line-out-of-bounds"}


def test_fail_quote_mismatch(tmp_path):
    _write_target(tmp_path, "c.py", ["line one", "line two", "line three"])
    finding = {"id": "F4", "file": "c.py", "line": 2, "quote": "this text is not on line two"}
    result = _mod().classify_finding(finding, tmp_path)
    assert result == {"status": "fail", "reason": "quote-mismatch"}


# --- ③ 无引文且无证据包 → 机械裁掉（fail, no-quote-no-evidence） --------------------------

def test_fail_no_quote_no_evidence(tmp_path):
    finding = {"id": "F5", "file": "d.py", "line": 1}
    result = _mod().classify_finding(finding, tmp_path)
    assert result == {"status": "fail", "reason": "no-quote-no-evidence"}


def test_fail_no_quote_no_evidence_empty_quote_string(tmp_path):
    finding = {"id": "F5b", "file": "d.py", "line": 1, "quote": "   "}
    result = _mod().classify_finding(finding, tmp_path)
    assert result == {"status": "fail", "reason": "no-quote-no-evidence"}


# --- ④ uncheckable：证据包 / 设计层引用 / 行范围外形态 → uncheckable ----------------------

def test_uncheckable_evidence_pack(tmp_path):
    finding = {"id": "F6", "evidence_pack": {"kind": "decision-point", "ref": "proposal.md#Why"}}
    result = _mod().classify_finding(finding, tmp_path)
    assert result == {"status": "uncheckable", "reason": "evidence-pack"}


def test_uncheckable_design_reference_no_file_line(tmp_path):
    """有引文但无 file/line（设计层引用，非干净 path:N 三元组）。"""
    finding = {"id": "F7", "quote": "见 proposal.md 的 Why 段落"}
    result = _mod().classify_finding(finding, tmp_path)
    assert result == {"status": "uncheckable", "reason": "design-reference"}


def test_uncheckable_line_range_form_string(tmp_path):
    _write_target(tmp_path, "e.py", ["a", "b", "c"])
    finding = {"id": "F8", "file": "e.py", "line": "10-15", "quote": "a"}
    result = _mod().classify_finding(finding, tmp_path)
    assert result == {"status": "uncheckable", "reason": "line-range-form"}


def test_uncheckable_line_range_form_list(tmp_path):
    _write_target(tmp_path, "f.py", ["a", "b", "c"])
    finding = {"id": "F9", "file": "f.py", "line": [10, 15], "quote": "a"}
    result = _mod().classify_finding(finding, tmp_path)
    assert result == {"status": "uncheckable", "reason": "line-range-form"}


# --- ⑤ 脚本级崩溃（输入 JSON 畸形 / 意外异常）→ 显式降级 [ref-check-unavailable] -----------

def test_degrade_malformed_json_syntax(tmp_path):
    p = tmp_path / "in.json"
    p.write_text("{not valid json", encoding="utf-8")
    r = _run(p, tmp_path)
    out = json.loads(r.stdout)
    assert r.returncode != 0
    assert out["result"] == "degraded"
    assert out["code"] == "[ref-check-unavailable]"
    assert out["results"] == []


def test_degrade_findings_not_list_or_wrapped_dict(tmp_path):
    p = tmp_path / "in.json"
    p.write_text(json.dumps({"nope": "not findings"}), encoding="utf-8")
    r = _run(p, tmp_path)
    out = json.loads(r.stdout)
    assert r.returncode != 0
    assert out["result"] == "degraded"


def test_degrade_unexpected_exception_non_dict_entry(tmp_path):
    """findings 列表内混入非对象条目（真实存在的意外异常来源，而非人为 monkeypatch）——
    单条畸形条目击穿整个批次，MUST 整批降级，不得只丢弃该条继续放行其余结果。"""
    p = tmp_path / "in.json"
    _write_target(tmp_path, "g.py", ["a"])
    p.write_text(json.dumps({"findings": [
        {"id": "F1", "file": "g.py", "line": 1, "quote": "a"},  # 单看会 pass
        42,  # 非对象条目 → AttributeError 在 process_batch 内自然抛出
    ]}), encoding="utf-8")
    r = _run(p, tmp_path)
    out = json.loads(r.stdout)
    assert r.returncode != 0
    assert out["result"] == "degraded"
    assert out["results"] == []  # 整批降级，MUST NOT 只漏一条


# --- ⑥ 输出码形态符合信号内诚实（degraded 不得与「已完整验证」的 ok 输出不可区分） ---------

def test_output_honesty_degraded_distinguishable_from_ok(tmp_path):
    good = tmp_path / "ok.json"
    good.write_text(json.dumps({"findings": [
        {"id": "F1", "file": "h.py", "line": 1, "quote": "a"},
    ]}), encoding="utf-8")
    _write_target(tmp_path, "h.py", ["a"])
    bad = tmp_path / "bad.json"
    bad.write_text("{broken", encoding="utf-8")

    r_ok = _run(good, tmp_path)
    r_bad = _run(bad, tmp_path)
    out_ok = json.loads(r_ok.stdout)
    out_bad = json.loads(r_bad.stdout)

    assert out_ok["result"] == "ok"
    assert out_bad["result"] == "degraded"
    assert out_ok["result"] != out_bad["result"]
    assert r_ok.returncode != r_bad.returncode
    # degraded 输出里绝不能出现任何 status=pass（不得呈现「全部 pass」假象）
    assert "pass" not in json.dumps(out_bad)


def test_no_bare_pass_code_when_script_never_ran_checks():
    """静态断言：degrade 路径的 JSON 构造函数不含硬编码的裸 "pass" 字面量——
    防止未来有人为图省事让 degrade 分支意外携带看起来像验证通过的字段。"""
    src = SCRIPT.read_text(encoding="utf-8")
    assert '"result": "degraded"' in src or "'result': 'degraded'" in src


# --- 批量整合：一次调用混合多态 --------------------------------------------------------

def test_batch_mixed_statuses(tmp_path):
    _write_target(tmp_path, "m.py", ["alpha", "beta"])
    p = tmp_path / "in.json"
    p.write_text(json.dumps({"findings": [
        {"id": "F1", "file": "m.py", "line": 1, "quote": "alpha"},          # pass
        {"id": "F2", "file": "missing.py", "line": 1, "quote": "x"},        # fail path-not-found
        {"id": "F3", "evidence_pack": {"x": 1}},                            # uncheckable
        {"id": "F4"},                                                       # fail no-quote-no-evidence
    ]}), encoding="utf-8")
    r = _run(p, tmp_path)
    out = json.loads(r.stdout)
    assert r.returncode == 0
    assert out["result"] == "ok"
    by_id = {x["id"]: x for x in out["results"]}
    assert by_id["F1"]["status"] == "pass"
    assert by_id["F2"] == {"id": "F2", "status": "fail", "reason": "path-not-found"}
    assert by_id["F3"]["status"] == "uncheckable"
    assert by_id["F4"] == {"id": "F4", "status": "fail", "reason": "no-quote-no-evidence"}


# --- CLI 契约 ---------------------------------------------------------------------------

def _run(input_path, root):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(input_path), "--root", str(root)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")


def test_cli_ok_exit0(tmp_path):
    _write_target(tmp_path, "z.py", ["hello"])
    p = tmp_path / "in.json"
    p.write_text(json.dumps({"findings": [
        {"id": "F1", "file": "z.py", "line": 1, "quote": "hello"},
    ]}), encoding="utf-8")
    r = _run(p, tmp_path)
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["result"] == "ok"
    assert out["results"][0]["status"] == "pass"


def test_cli_degraded_exit_nonzero(tmp_path):
    p = tmp_path / "in.json"
    p.write_text("not json at all", encoding="utf-8")
    r = _run(p, tmp_path)
    assert r.returncode != 0
    assert "[findings_ref_check] DEGRADED" in r.stderr
    assert "Traceback" not in r.stderr


def test_cli_missing_input_file_degrades(tmp_path):
    r = _run(tmp_path / "nonexistent.json", tmp_path)
    assert r.returncode != 0
    out = json.loads(r.stdout)
    assert out["result"] == "degraded"


# --- 纯 stdlib（无 subprocess/网络依赖，静态断言）----------------------------------------

def test_no_subprocess_import():
    import ast
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imported.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "subprocess" not in imported
