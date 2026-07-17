import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts/init.py"
SPEC = importlib.util.spec_from_file_location("sdflow_init_runtime", SCRIPT)
INIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INIT)
ENTRY = b"/openspec/issues/.recorder.lock\n"


def test_merge_runtime_gitignore_is_idempotent_and_preserves_bytes(tmp_path):
    target = tmp_path / ".gitignore"
    target.write_bytes(b"# user\r\ncustom/*\r\n")
    INIT.merge_runtime_gitignore(tmp_path, ENTRY)
    once = target.read_bytes()
    assert once == b"# user\r\ncustom/*\r\n/openspec/issues/.recorder.lock\n"
    INIT.merge_runtime_gitignore(tmp_path, ENTRY)
    assert target.read_bytes() == once


def test_merge_runtime_gitignore_rejects_duplicate_without_mutation(tmp_path):
    target = tmp_path / ".gitignore"
    original = ENTRY + b"keep\n" + ENTRY
    target.write_bytes(original)
    with pytest.raises(ValueError, match="重复"):
        INIT.merge_runtime_gitignore(tmp_path, ENTRY)
    assert target.read_bytes() == original
