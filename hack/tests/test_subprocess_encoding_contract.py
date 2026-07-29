"""Regression guard for the repository-wide text subprocess encoding contract."""
import ast
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]

TARGET_FILES = {
    "sdflow-devenv/scripts/devenv_scaffold.py": 2,
    "sdflow-done/scripts/roadmap_writeback_draft.py": 1,
    "sdflow-implement/scripts/impl_route.py": 1,
    "sdflow-init/assets/hack/outside-voice-job.py": 1,
    "sdflow-init/assets/hooks/ff0-branch-guard.py": 1,
    "sdflow-init/assets/workflow/tools/trivial_shape.py": 1,
    "sdflow-init/scripts/init.py": 1,
    "sdflow-issues/scripts/issues.py": 4,
    "sdflow-retro/scripts/retro_report.py": 1,
}


def _keyword_values(call):
    return {
        keyword.arg: keyword.value.value
        for keyword in call.keywords
        if keyword.arg is not None and isinstance(keyword.value, ast.Constant)
    }


def _is_text_mode(call):
    return _keyword_values(call).get("text") is True


def _is_subprocess_call(call):
    return (
        isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "subprocess"
        and call.func.attr == "run"
    )


def test_text_mode_subprocesses_declare_utf8_and_replace():
    """Every direct text subprocess site is locale-independent and loss-tolerant."""
    misses = []
    sites = 0
    for relative, expected_sites in TARGET_FILES.items():
        path = REPO / relative
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        file_sites = 0
        for call in ast.walk(tree):
            if not isinstance(call, ast.Call) or not _is_subprocess_call(call) or not _is_text_mode(call):
                continue
            sites += 1
            file_sites += 1
            values = _keyword_values(call)
            missing = [name for name, expected in (("encoding", "utf-8"), ("errors", "replace"))
                       if values.get(name) != expected]
            if missing:
                misses.append(f"{path.relative_to(REPO)}:{call.lineno}: {', '.join(missing)}")
        assert file_sites == expected_sites

    assert sites == 13
    assert not misses, "\n".join(misses)


def test_ship_gate_text_wrapper_is_hardened_without_touching_byte_reads():
    """Text helpers inherit kwargs at their single outlet; byte helper stays raw."""
    path = REPO / "sdflow-ship/scripts/ship_gate.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    text_branch = next(
        node for node in ast.walk(functions["_git_run"])
        if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == "text"
    )
    assignments = {
        statement.targets[0].slice.value: statement.value.value
        for statement in text_branch.body
        if (isinstance(statement, ast.Assign) and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Subscript)
                and isinstance(statement.targets[0].value, ast.Name)
                and statement.targets[0].value.id == "kwargs"
                and isinstance(statement.targets[0].slice, ast.Constant)
                and isinstance(statement.value, ast.Constant))
    }
    assert assignments["encoding"] == "utf-8"
    assert assignments["errors"] == "replace"

    byte_calls = [
        node for node in ast.walk(functions["run_git_bytes"])
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_git_run"
    ]
    assert len(byte_calls) == 1
    assert _keyword_values(byte_calls[0])["text"] is False
