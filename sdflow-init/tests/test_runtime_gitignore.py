import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts/init.py"
SPEC = importlib.util.spec_from_file_location("sdflow_init_runtime", SCRIPT)
INIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INIT)
ENTRY = b"/openspec/issues/.recorder.lock\n"


def _stub_run_dependencies(monkeypatch):
    monkeypatch.setattr(INIT, "ensure_dirs", lambda _root: [])
    monkeypatch.setattr(INIT, "copy_bundle", lambda _root, full=False: ("workflow", 0))
    monkeypatch.setattr(INIT, "ensure_global_hooks", lambda: "")
    monkeypatch.setattr(INIT, "retire_hooks", lambda: "")
    monkeypatch.setattr(INIT, "retire_deploy_files", lambda _root: "")
    monkeypatch.setattr(INIT, "stale_shadow_warnings", lambda _root: [])
    monkeypatch.setattr(INIT, "handle_config", lambda _root, _mode: ("unchanged", "noop"))
    monkeypatch.setattr(INIT, "inject", lambda *_args, **_kwargs: "noop")
    monkeypatch.setattr(INIT, "read_snippet", lambda _name: "")


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


def test_merge_runtime_gitignore_write_and_replace_faults_preserve_original(tmp_path, monkeypatch):
    target = tmp_path / ".gitignore"
    original = b"# user\nkeep/**\n"
    target.write_bytes(original)

    real_fdopen = INIT.os.fdopen

    class BrokenWriter:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def write(self, _data):
            raise OSError("write fault")

    monkeypatch.setattr(INIT.os, "fdopen", lambda fd, mode: (INIT.os.close(fd), BrokenWriter())[1])
    with pytest.raises(OSError, match="write fault"):
        INIT.merge_runtime_gitignore(tmp_path, ENTRY)
    assert target.read_bytes() == original
    assert not list(tmp_path.glob("*.tmp"))

    monkeypatch.setattr(INIT.os, "fdopen", real_fdopen)
    monkeypatch.setattr(INIT.os, "replace", lambda *_args: (_ for _ in ()).throw(OSError("replace fault")))
    with pytest.raises(OSError, match="replace fault"):
        INIT.merge_runtime_gitignore(tmp_path, ENTRY)
    assert target.read_bytes() == original
    assert not list(tmp_path.glob("*.tmp"))


def test_merge_runtime_gitignore_local_filesystem_replace_contract(tmp_path):
    target = tmp_path / ".gitignore"
    target.write_bytes(b"user\n")
    INIT.merge_runtime_gitignore(tmp_path, ENTRY)
    assert target.read_bytes() == b"user\n" + ENTRY
    assert not list(tmp_path.glob("*.tmp"))


def test_merge_runtime_gitignore_replaces_only_after_temp_handle_closed(tmp_path, monkeypatch):
    """Windows-compatible local-FS contract: replace sees a closed temp handle.

    The current release gate runs on macOS/Linux local FS; Windows local-disk CI can
    execute this same test without POSIX mode-bit assertions. Network/user-space FS
    and power-loss durability remain outside this contract.
    """
    target = tmp_path / ".gitignore"
    target.write_bytes(b"user\n")
    real_replace = INIT.os.replace
    observed = []

    def checked_replace(source, destination):
        probe = INIT.os.open(source, INIT.os.O_RDWR)
        INIT.os.close(probe)
        observed.append((source, destination))
        real_replace(source, destination)

    monkeypatch.setattr(INIT.os, "replace", checked_replace)
    INIT.merge_runtime_gitignore(tmp_path, ENTRY)
    assert len(observed) == 1
    assert target.read_bytes() == b"user\n" + ENTRY


@pytest.mark.parametrize("mode", ["init", "update"])
@pytest.mark.parametrize("case", ["missing", "existing", "user-bytes", "duplicate"])
def test_run_init_and_update_use_canonical_runtime_merge(mode, case, tmp_path, monkeypatch):
    _stub_run_dependencies(monkeypatch)
    if mode == "update":
        (tmp_path / "openspec").mkdir()
    target = tmp_path / ".gitignore"
    if case == "existing":
        target.write_bytes(b"user\r\n" + ENTRY)
    elif case == "user-bytes":
        target.write_bytes(b"# user\r\ncustom/**\r\n")
    elif case == "duplicate":
        target.write_bytes(ENTRY + b"keep\n" + ENTRY)

    canonical = (Path(INIT.SNIPPETS) / "runtime-gitignore.txt").read_bytes()
    calls = []
    real_merge = INIT.merge_runtime_gitignore

    def observed_merge(root, snippet):
        calls.append(snippet)
        return real_merge(root, snippet)

    monkeypatch.setattr(INIT, "merge_runtime_gitignore", observed_merge)
    if case == "duplicate":
        original = target.read_bytes()
        with pytest.raises(SystemExit):
            INIT.run(str(tmp_path), mode)
        assert target.read_bytes() == original
    else:
        INIT.run(str(tmp_path), mode)
        result = target.read_bytes()
        assert result.splitlines().count(ENTRY.rstrip(b"\n")) == 1
        if case == "existing":
            assert result == b"user\r\n" + ENTRY
        elif case == "user-bytes":
            assert result == b"# user\r\ncustom/**\r\n" + ENTRY
    assert calls == [canonical]
