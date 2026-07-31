from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "sdflow-spec" / "SKILL.md"


def _text():
    return SKILL.read_text(encoding="utf-8").replace(" ", "")


def test_phase_c_consumes_dependency_objects_and_has_schema_fallback():
    text = _text()
    assert "dependencies`MUST是对象列表" in text
    assert "图已覆盖" in text
    assert "写死超集" in text
    assert "图不足" in text
    assert "proposal.md`+`design.md`+`specs/**" in text


def test_phase_c_strips_delegation_before_applying_instruction():
    text = _text()
    assert "sdflow:delegation:start" in text
    assert "sdflow:delegation:end" in text
    assert "应用载荷前" in text
    assert "不成对则fail-closed" in text
    assert "fail-closed" in text


def test_phase_c_handles_glob_existing_outputs_and_skipped_status():
    text = _text()
    assert "existingOutputPaths" in text
    assert "为glob" in text
    assert "具体`specs/" in text
    assert "status`为`skipped" in text
    assert "MUSTNOT创建任何对应文件" in text
    assert "依赖阅读清单移除该artifact" in text


def test_final_review_keeps_design_specs_bidirectional_check():
    text = _text()
    assert "design↔specs" in text
    assert "双向" in text or "互相一致" in text
