import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).parents[2]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _snapshot_barrier_worker(root, command, ready, release, suffix=None):
    """Spawn-safe cooperative reader/writer used by true cross-process barriers."""
    module = load(f"barrier_{command}_{os.getpid()}", "sdflow-issues/scripts/buglist.py")
    target = Path(root) / "shared.md"
    with module.recorder_lock(root, command):
        snapshot = target.read_text(encoding="utf-8")
        ready.set()
        if not release.wait(15):
            raise RuntimeError("barrier release timeout")
        if suffix is not None:
            module.atomic_write(target, snapshot + suffix)


def _producer_barrier_worker(root, suffix, ready, release, result_path):
    """Fake sibling producer: report conflict or the exact bytes read after acquire."""
    module = load(f"producer_{suffix}_{os.getpid()}", "sdflow-issues/scripts/buglist.py")
    target = Path(root) / "dated.md"
    try:
        with module.recorder_lock(root, "add"):
            snapshot = target.read_text(encoding="utf-8")
            Path(result_path).write_text("acquired\n" + snapshot, encoding="utf-8")
            ready.set()
            if not release.wait(15):
                raise RuntimeError("producer release timeout")
            module.atomic_write(target, snapshot + suffix)
    except module.RecorderLockError as exc:
        Path(result_path).write_text("conflict\n" + str(exc), encoding="utf-8")
        ready.set()


@pytest.mark.parametrize("relative", [
    "sdflow-issues/scripts/buglist.py",
    "sdflow-issues/scripts/todolist.py",
    "sdflow-issues/scripts/issues.py",
])
def test_canonical_id_rejects_alias_and_unicode_digits(relative):
    module = load(relative.replace("/", "_"), relative)
    assert module.canonical_id("A7") == "A7"
    for invalid in ("A007", "A1٢", "A1２", "AA7", "a7"):
        with pytest.raises(ValueError, match="canonical ASCII"):
            module.canonical_id(invalid)


def test_repository_lock_is_exclusive_and_token_safe(tmp_path):
    module = load("bug_lock", "sdflow-issues/scripts/buglist.py")
    root = tmp_path
    (root / "openspec/issues").mkdir(parents=True)
    with module.recorder_lock(root, "sweep") as owner:
        with pytest.raises(module.RecorderLockError, match="lock occupied"):
            with module.recorder_lock(root, "add"):
                pass
        module._core._ACTIVE_RECORDER_TOKEN = owner.token
        module._core._ACTIVE_RECORDER_CHAIN = owner.chain
        participant_env = module.recorder_child_env("reindex")
        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setattr(os, "environ", participant_env)
            participant = module.validate_recorder_participant(root, owner.token, "reindex")
        assert participant.token == owner.token
        with pytest.raises(module.RecorderLockError):
            module.validate_recorder_participant(root, "forged", "reindex")
        with pytest.raises(module.RecorderLockError, match="not allowlisted"):
            module.validate_recorder_participant(root, owner.token, "shell")
        other = tmp_path / "other"
        (other / "openspec/issues").mkdir(parents=True)
        with pytest.raises(module.RecorderLockError, match="cross-repo"):
            module.validate_recorder_participant(other, owner.token, "scan")
        assert module.RECORDER_LOCK_ENV in participant_env
        assert module.RECORDER_LOCK_ENV not in module.recorder_child_env("git", token=False)
        module._core._ACTIVE_RECORDER_TOKEN = None
        module._core._ACTIVE_RECORDER_CHAIN = None
    assert not (root / "openspec/issues/.recorder.lock").exists()


def test_twenty_process_adds_are_unique_or_fail_loud(tmp_path):
    script = ROOT / "sdflow-issues/scripts/buglist.py"
    payload = tmp_path / "bug.json"
    payload.write_text(json.dumps({
        "module": "lock", "summary": "race", "priority": "P2", "phenomenon": "race",
    }))
    command = [sys.executable, str(script), "--root", str(tmp_path), "add", "--json", str(payload), "--prefix", "A"]
    processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(20)]
    results = [process.communicate(timeout=20) + (process.returncode,) for process in processes]
    successful = [json.loads(stdout)["id"] for stdout, _stderr, code in results if code == 0]
    failures = [stderr for _stdout, stderr, code in results if code != 0]
    assert successful
    assert len(successful) == len(set(successful))
    assert all("recorder lock occupied" in stderr for stderr in failures)
    assert not (tmp_path / "openspec/issues/.recorder.lock").exists()
    scan = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path), "scan", "--json"],
        capture_output=True, text=True,
    )
    assert scan.returncode == 0, scan.stderr
    assert {item["id"] for item in json.loads(scan.stdout)["bugs"]} == set(successful)


@pytest.mark.parametrize("relative", [
    "sdflow-issues/scripts/buglist.py",
    "sdflow-issues/scripts/todolist.py",
    "sdflow-issues/scripts/issues.py",
])
def test_lock_metadata_short_write_and_failure_cleanup(relative, tmp_path, monkeypatch):
    module = load("metadata_" + relative.replace("/", "_"), relative)
    lock = tmp_path / "openspec/issues/.recorder.lock"
    real_write = os.write
    calls = 0

    def short_once(fd, data):
        nonlocal calls
        calls += 1
        if calls == 1:
            return real_write(fd, data[:5])
        return real_write(fd, data)

    monkeypatch.setattr(module.os, "write", short_once)
    with module.recorder_lock(tmp_path, "scan"):
        assert lock.exists()
    assert calls >= 2
    assert not lock.exists()


@pytest.mark.parametrize("fault_name", ["fsync", "close"])
def test_lock_metadata_publish_faults_cleanup_own_inode(tmp_path, monkeypatch, fault_name):
    module = load("metadata_publish_" + fault_name, "sdflow-issues/scripts/buglist.py")
    lock = tmp_path / "openspec/issues/.recorder.lock"
    real_close = os.close
    calls = 0

    if fault_name == "fsync":
        monkeypatch.setattr(module.os, "fsync", lambda _fd: (_ for _ in ()).throw(OSError("fsync fault")))
    else:
        def close_once(fd):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("close fault")
            return real_close(fd)
        monkeypatch.setattr(module.os, "close", close_once)

    with pytest.raises(OSError, match=f"{fault_name} fault"):
        with module.recorder_lock(tmp_path, "scan"):
            pass
    assert not lock.exists()

    def fail_write(_fd, _data):
        raise OSError("metadata write failed")

    monkeypatch.setattr(module.os, "write", fail_write)
    with pytest.raises(OSError, match="metadata write failed"):
        with module.recorder_lock(tmp_path, "scan"):
            pass
    assert not lock.exists()


@pytest.mark.parametrize("relative,args", [
    ("sdflow-issues/scripts/buglist.py", ["scan", "--json"]),
    ("sdflow-issues/scripts/todolist.py", ["scan", "--json"]),
    ("sdflow-issues/scripts/issues.py", ["reindex"]),
])
def test_invalid_participant_env_falls_back_to_owner_or_conflict(relative, args, tmp_path):
    script = ROOT / relative
    env = dict(os.environ)
    env["SDFLOW_RECORDER_LOCK_TOKEN"] = "expired"
    env["SDFLOW_RECORDER_DELEGATION_CHAIN"] = json.dumps(["sweep", "scan"])
    owner = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path), *args],
        capture_output=True, text=True, env=env,
    )
    assert owner.returncode == 0, owner.stderr
    assert not (tmp_path / "openspec/issues/.recorder.lock").exists()

    lock_module = load("invalid_env_lock", "sdflow-issues/scripts/buglist.py")
    with lock_module.recorder_lock(tmp_path, "add"):
        conflict = subprocess.run(
            [sys.executable, str(script), "--root", str(tmp_path), *args],
            capture_output=True, text=True, env=env,
        )
    assert conflict.returncode != 0
    assert "recorder lock occupied" in conflict.stderr


@pytest.mark.parametrize("relative", [
    "sdflow-issues/scripts/buglist.py",
    "sdflow-issues/scripts/todolist.py",
    "sdflow-issues/scripts/issues.py",
])
def test_delegation_graph_allows_nested_chain_and_rejects_escalation(relative, tmp_path, monkeypatch):
    module = load("delegation_" + relative.replace("/", "_"), relative)
    with module.recorder_lock(tmp_path, "sweep") as owner:
        module._core._ACTIVE_RECORDER_TOKEN = owner.token
        module._core._ACTIVE_RECORDER_CHAIN = owner.chain
        reindex_env = module.recorder_child_env("reindex")
        with monkeypatch.context() as nested:
            nested.setattr(os, "environ", reindex_env)
            reindex = module.validate_recorder_participant(tmp_path, owner.token, "reindex")
        module._core._ACTIVE_RECORDER_CHAIN = reindex.chain
        scan_env = module.recorder_child_env("scan")
        with monkeypatch.context() as nested:
            nested.setattr(os, "environ", scan_env)
            scan = module.validate_recorder_participant(tmp_path, owner.token, "scan")
        assert scan.chain == ("sweep", "reindex", "scan")

        module._core._ACTIVE_RECORDER_CHAIN = owner.chain
        with pytest.raises(module.RecorderLockError, match="delegation denied"):
            module.recorder_child_env("batch-rename")
        forged = dict(reindex_env)
        forged[module.RECORDER_DELEGATION_CHAIN_ENV] = json.dumps(["sweep", "batch-rename"])
        with monkeypatch.context() as nested:
            nested.setattr(os, "environ", forged)
            with pytest.raises(module.RecorderLockError, match="delegation"):
                module.validate_recorder_participant(tmp_path, owner.token, "batch-rename")
        forged[module.RECORDER_DELEGATION_CHAIN_ENV] = json.dumps(["sweep"])
        with monkeypatch.context() as nested:
            nested.setattr(os, "environ", forged)
            with pytest.raises(module.RecorderLockError, match="chain"):
                module.validate_recorder_participant(tmp_path, owner.token, "sweep")
        module._core._ACTIVE_RECORDER_TOKEN = None
        module._core._ACTIVE_RECORDER_CHAIN = None


@pytest.mark.parametrize("relative,result_key", [
    ("sdflow-issues/scripts/buglist.py", "bugs"),
    ("sdflow-issues/scripts/todolist.py", "items"),
])
def test_scan_json_serialization_happens_after_lock_release(relative, result_key, tmp_path, monkeypatch):
    module = load("render_" + relative.replace("/", "_"), relative)
    lock = tmp_path / "openspec/issues/.recorder.lock"
    real_dumps = module.json.dumps
    observed = []

    def guarded_dumps(value, *args, **kwargs):
        if isinstance(value, dict) and result_key in value:
            observed.append(lock.exists())
        return real_dumps(value, *args, **kwargs)

    monkeypatch.setattr(module.json, "dumps", guarded_dumps)
    monkeypatch.setattr(sys, "argv", ["recorder", "--root", str(tmp_path), "scan", "--json"])
    module.main()
    assert observed == [False]


def test_blocked_stdout_write_starts_after_lock_release(tmp_path, monkeypatch):
    module = load("blocked_stdout", "sdflow-issues/scripts/buglist.py")
    lock = tmp_path / "openspec/issues/.recorder.lock"
    writes = []

    class BlockingSink:
        def write(self, value):
            writes.append((value, lock.exists()))
            return len(value)

        def flush(self):
            return None

    monkeypatch.setattr(sys, "argv", ["recorder", "--root", str(tmp_path), "scan", "--json"])
    monkeypatch.setattr(sys, "stdout", BlockingSink())
    module.main()
    assert writes
    assert all(not held for _value, held in writes)


def test_reader_writer_barrier_is_bidirectional_across_processes(tmp_path):
    ctx = multiprocessing.get_context("spawn")
    script = ROOT / "sdflow-issues/scripts/buglist.py"
    payload = tmp_path / "bug.json"
    payload.write_text(json.dumps({"module": "m", "summary": "barrier", "priority": "P2", "phenomenon": "x"}))
    shared = tmp_path / "shared.md"
    shared.write_text("base\n", encoding="utf-8")

    ready = ctx.Event()
    release = ctx.Event()
    reader = ctx.Process(target=_snapshot_barrier_worker, args=(str(tmp_path), "scan", ready, release))
    reader.start()
    assert ready.wait(15)
    writer_conflict = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path), "add", "--json", str(payload)],
        capture_output=True, text=True,
    )
    assert writer_conflict.returncode != 0
    assert "recorder lock occupied" in writer_conflict.stderr
    release.set()
    reader.join(15)
    assert reader.exitcode == 0
    writer_after_release = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path), "add", "--json", str(payload)],
        capture_output=True, text=True,
    )
    assert writer_after_release.returncode == 0, writer_after_release.stderr

    ready = ctx.Event()
    release = ctx.Event()
    writer = ctx.Process(target=_snapshot_barrier_worker, args=(str(tmp_path), "add", ready, release, "writer\n"))
    writer.start()
    assert ready.wait(15)
    reader_conflict = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path), "scan", "--json"],
        capture_output=True, text=True,
    )
    assert reader_conflict.returncode != 0
    assert "recorder lock occupied" in reader_conflict.stderr
    release.set()
    writer.join(15)
    assert writer.exitcode == 0
    reader_after_release = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path), "scan", "--json"],
        capture_output=True, text=True,
    )
    assert reader_after_release.returncode == 0, reader_after_release.stderr
    assert shared.read_text(encoding="utf-8") == "base\nwriter\n"


def test_next_id_release_does_not_reserve_number(tmp_path):
    script = ROOT / "sdflow-issues/scripts/buglist.py"
    suggestion = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path), "next-id", "--prefix", "A"],
        capture_output=True, text=True,
    )
    assert suggestion.returncode == 0
    assert suggestion.stdout.strip() == "A1"
    payload = tmp_path / "bug.json"
    payload.write_text(json.dumps({"module": "m", "summary": "race", "priority": "P2", "phenomenon": "x"}))
    winner = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path), "add", "--json", str(payload), "--prefix", "A"],
        capture_output=True, text=True,
    )
    assert winner.returncode == 0, winner.stderr
    explicit = tmp_path / "explicit.json"
    explicit.write_text(json.dumps({"id": "A1", "module": "m", "summary": "late", "priority": "P2", "phenomenon": "x"}))
    loser = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path), "add", "--json", str(explicit)],
        capture_output=True, text=True,
    )
    assert loser.returncode != 0
    assert "semantic ID" in loser.stderr


def test_two_cooperative_namespace_producers_use_cross_process_barrier(tmp_path):
    ctx = multiprocessing.get_context("spawn")
    target = tmp_path / "dated.md"
    target.write_text("---\nbase: 1\n---\n")
    ready_a, release_a = ctx.Event(), ctx.Event()
    result_a = tmp_path / "producer-a.result"
    producer_a = ctx.Process(
        target=_producer_barrier_worker,
        args=(str(tmp_path), "producer-a: 1\n", ready_a, release_a, str(result_a)),
    )
    producer_a.start()
    assert ready_a.wait(15)

    ready_conflict, release_conflict = ctx.Event(), ctx.Event()
    release_conflict.set()
    result_conflict = tmp_path / "producer-b-conflict.result"
    producer_b_conflict = ctx.Process(
        target=_producer_barrier_worker,
        args=(str(tmp_path), "producer-b: 1\n", ready_conflict, release_conflict, str(result_conflict)),
    )
    producer_b_conflict.start()
    assert ready_conflict.wait(15)
    producer_b_conflict.join(15)
    assert producer_b_conflict.exitcode == 0
    assert result_conflict.read_text(encoding="utf-8").startswith("conflict\n")

    release_a.set()
    producer_a.join(15)
    assert producer_a.exitcode == 0

    ready_b, release_b = ctx.Event(), ctx.Event()
    release_b.set()
    result_b = tmp_path / "producer-b.result"
    producer_b = ctx.Process(
        target=_producer_barrier_worker,
        args=(str(tmp_path), "producer-b: 1\n", ready_b, release_b, str(result_b)),
    )
    producer_b.start()
    assert ready_b.wait(15)
    producer_b.join(15)
    assert producer_b.exitcode == 0
    observed_b = result_b.read_text(encoding="utf-8")
    assert observed_b.startswith("acquired\n")
    assert "producer-a: 1\n" in observed_b
    assert target.read_text().endswith("producer-a: 1\nproducer-b: 1\n")


def test_real_sweep_reindex_scan_nested_delegation(tmp_path):
    bug_dir = tmp_path / "openspec/issues/buglist"
    bug_dir.mkdir(parents=True)
    (bug_dir / "2026-01-01-buglist.md").write_text(
        "# 2026-01-01 Buglist\n\n"
        "> 来源：test\n> 创建日期：2026-01-01\n\n"
        "## 状态总览\n\n"
        "| ID | 模块 | 问题摘要 | 优先级 | 状态 | 时间 | 关联Change | 批次 |\n"
        "|----|------|----------|--------|------|------|------------|------|\n"
        "| B1 | `m` | nested | P2 | OPEN | 10:00 | nested-change |  |\n\n"
        "---\n\n## B1: nested\n\n| 属性 | 值 |\n|------|------|\n"
        "| 状态 | OPEN |\n\n**根因**：fixture rootcause\n"
    )
    script = ROOT / "sdflow-issues/scripts/issues.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path), "sweep", "--change", "nested-change"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "tagged 1" in proc.stdout
    assert (tmp_path / "openspec/issues/INDEX.md").exists()
    assert not (tmp_path / "openspec/issues/.recorder.lock").exists()


def test_cli_writer_fault_releases_lock_and_preserves_target(tmp_path, monkeypatch):
    module = load("cli_writer_fault", "sdflow-issues/scripts/buglist.py")
    payload = tmp_path / "bug.json"
    payload.write_text(json.dumps({"module": "m", "summary": "fault", "priority": "P2", "phenomenon": "x"}))
    target = tmp_path / "openspec/issues/buglist/2026-01-01-buglist.md"

    def fail_write(_path, _text):
        raise OSError("writer fault")

    monkeypatch.setattr(module._core, "atomic_write_bytes", fail_write)
    monkeypatch.setattr(sys, "argv", [
        "buglist", "--root", str(tmp_path), "add", "--json", str(payload),
        "--date", "2026-01-01",
    ])
    with pytest.raises(OSError, match="writer fault"):
        module.main()
    assert not target.exists()
    assert not (tmp_path / "openspec/issues/.recorder.lock").exists()


def test_partial_lock_and_ownership_lost_are_fail_closed(tmp_path):
    module = load("bug_lock_faults", "sdflow-issues/scripts/buglist.py")
    lock = tmp_path / "openspec/issues/.recorder.lock"
    lock.parent.mkdir(parents=True)
    lock.write_bytes(b"")
    with pytest.raises(module.RecorderLockError, match="metadata unavailable"):
        with module.recorder_lock(tmp_path, "scan"):
            pass
    lock.unlink()
    replacement = {"repo": os.path.realpath(tmp_path), "pid": 999, "command": "add", "started": 0, "token": "replacement"}
    with pytest.raises(module.RecorderLockError, match="ownership lost"):
        with module.recorder_lock(tmp_path, "scan"):
            lock.unlink()
            lock.write_text(json.dumps(replacement))
    assert json.loads(lock.read_text())["token"] == "replacement"


def test_custom_prefix_is_repository_wide_across_pools(tmp_path):
    bug_script = ROOT / "sdflow-issues/scripts/buglist.py"
    todo_script = ROOT / "sdflow-issues/scripts/todolist.py"
    bug = tmp_path / "bug.json"
    todo = tmp_path / "todo.json"
    bug.write_text(json.dumps({"id": "A1", "module": "m", "summary": "bug", "priority": "P2", "phenomenon": "x"}))
    todo.write_text(json.dumps({"id": "A1", "module": "m", "summary": "todo", "type": "代码质量"}))
    first = subprocess.run([sys.executable, bug_script, "--root", tmp_path, "add", "--json", bug], capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    second = subprocess.run([sys.executable, todo_script, "--root", tmp_path, "add", "--json", todo], capture_output=True, text=True)
    assert second.returncode != 0
    assert "仓级既有 semantic ID 重复" in second.stderr
