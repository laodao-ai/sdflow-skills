import json, os, sys, time
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from devenv_lock import write_lock, atomic_write, LOCK_REL, LockBusy


def _mkroot(tmp_path):
    (tmp_path / "openspec").mkdir()
    return tmp_path


def test_lock_file_format_is_contract(tmp_path):
    root = _mkroot(tmp_path)
    with write_lock(root):
        raw = (root / LOCK_REL).read_text()
        rec = json.loads(raw)
        assert set(rec) == {"owner", "pid", "ts"}
        assert isinstance(rec["owner"], str) and len(rec["owner"]) == 32
        assert rec["pid"] == os.getpid()
        assert isinstance(rec["ts"], float)


def test_lock_released_on_exit(tmp_path):
    root = _mkroot(tmp_path)
    with write_lock(root):
        assert (root / LOCK_REL).exists()
    assert not (root / LOCK_REL).exists()


def test_lock_released_on_exception(tmp_path):
    root = _mkroot(tmp_path)
    with pytest.raises(ValueError):
        with write_lock(root):
            raise ValueError("boom")
    assert not (root / LOCK_REL).exists()


def test_second_acquire_busy(tmp_path):
    root = _mkroot(tmp_path)
    with write_lock(root):
        with pytest.raises(LockBusy):
            with write_lock(root, retries=1, interval=0.01):
                pass


def test_does_not_delete_foreign_lock(tmp_path):
    """A 释放时 MUST NOT 删掉 B 的锁 —— owner 不符就不删。"""
    root = _mkroot(tmp_path)
    lp = root / LOCK_REL
    try:
        with write_lock(root):
            # 模拟：锁被别人抢走并改写（owner 变了）
            lp.write_text(json.dumps({"owner": "f" * 32, "pid": 99999, "ts": time.time()}))
    except Exception:
        pass
    # 别人的锁必须还在
    assert lp.exists()
    assert json.loads(lp.read_text())["owner"] == "f" * 32


def test_atomic_write_mode_755(tmp_path):
    p = tmp_path / "doctor.sh"
    atomic_write(p, "#!/bin/sh\necho ok\n", mode=0o755)
    assert p.read_text().startswith("#!/bin/sh")
    assert oct(p.stat().st_mode)[-3:] == "755"


def test_atomic_write_default_644(tmp_path):
    p = tmp_path / "notes.md"
    atomic_write(p, "hi\n")
    assert oct(p.stat().st_mode)[-3:] == "644"


def test_atomic_write_preserves_existing_mode(tmp_path):
    p = tmp_path / "existing.sh"
    p.write_text("old\n")
    os.chmod(p, 0o700)
    atomic_write(p, "new\n")          # 不传 mode ⇒ 保留原 mode
    assert p.read_text() == "new\n"
    assert oct(p.stat().st_mode)[-3:] == "700"


def test_atomic_write_leaves_no_tmp_on_success(tmp_path):
    p = tmp_path / "x.md"
    atomic_write(p, "x\n")
    leftovers = [f for f in tmp_path.iterdir() if ".tmp-" in f.name]
    assert leftovers == []


# ---------------------------------------------------------------------------
# 以下为需求书基线之外、任务说明书("并发是这个任务的核心")显式要求补充的用例：
# 真实多进程抢锁 / 陈旧锁判定与"崩溃后不永久卡死" / atomic_write 中途失败原子性。
# ---------------------------------------------------------------------------

import subprocess

import devenv_lock

SCRIPTS_DIR = str(Path(__file__).resolve().parents[1] / "scripts")


def test_stale_lock_raises_and_recovers_after_manual_delete(tmp_path, monkeypatch):
    """陈旧锁（mtime 超阈值，模拟持锁进程崩溃未释放）→ raise LockStale，
    不会无限等待/永久卡死；人工删除残留锁后下一次获取照常成功。"""
    root = _mkroot(tmp_path)
    lockp = root / LOCK_REL
    lockp.parent.mkdir(parents=True, exist_ok=True)
    # 模拟崩溃残留：写一把锁但不释放，mtime 拨到很久以前
    lockp.write_text(json.dumps({"owner": "d" * 32, "pid": 424242, "ts": time.time() - 999}))
    old = time.time() - 999
    os.utime(lockp, (old, old))

    monkeypatch.setattr(devenv_lock, "LOCK_STALE_SEC", 0.01)

    with pytest.raises(devenv_lock.LockStale):
        with write_lock(root, retries=3, interval=0.01):
            pass  # 不会走到这里

    # 不会永久卡死：残留锁仍在（未被自动抢），但人工删除后立刻可正常获取
    assert lockp.exists()
    lockp.unlink()
    with write_lock(root):
        assert lockp.exists()
    assert not lockp.exists()


def test_concurrent_processes_only_one_acquires_lock(tmp_path):
    """真实多进程抢锁：两个独立 OS 进程同时抢同一把锁，只有一个拿到。"""
    root = _mkroot(tmp_path)

    hold_code = f"""
import sys, time
sys.path.insert(0, {SCRIPTS_DIR!r})
from devenv_lock import write_lock
with write_lock({str(root)!r}, retries=100, interval=0.02):
    time.sleep(1.0)
print("HELD_OK")
"""
    try_code = f"""
import sys, time
sys.path.insert(0, {SCRIPTS_DIR!r})
from devenv_lock import write_lock, LockBusy
time.sleep(0.3)
try:
    with write_lock({str(root)!r}, retries=5, interval=0.05):
        print("GOT_LOCK_UNEXPECTED")
except LockBusy:
    print("BUSY_AS_EXPECTED")
"""
    p1 = subprocess.Popen([sys.executable, "-c", hold_code], stdout=subprocess.PIPE, text=True)
    p2 = subprocess.Popen([sys.executable, "-c", try_code], stdout=subprocess.PIPE, text=True)
    out1, _ = p1.communicate(timeout=15)
    out2, _ = p2.communicate(timeout=15)

    assert "HELD_OK" in out1
    assert "BUSY_AS_EXPECTED" in out2
    assert not (root / LOCK_REL).exists()  # 持锁进程退出时已释放


def test_atomic_write_no_partial_file_on_replace_failure(tmp_path, monkeypatch):
    """atomic_write 中途失败（os.replace 抛异常）不留半个文件：
    原文件内容不受影响，tmp 文件被清理，不落地新内容。"""
    p = tmp_path / "y.md"
    p.write_text("original\n")
    os.chmod(p, 0o644)

    def boom(*a, **k):
        raise OSError("simulated mid-write failure")

    monkeypatch.setattr(devenv_lock.os, "replace", boom)

    with pytest.raises(OSError):
        atomic_write(p, "new content that should never land\n")

    assert p.read_text() == "original\n"
    leftovers = [f for f in tmp_path.iterdir() if ".tmp-" in f.name]
    assert leftovers == []


def test_atomic_write_non_utf8_leaves_no_orphan_tmp(tmp_path):
    """f.write 抛 UnicodeEncodeError（非 OSError）时也必须清掉 tmp 文件。

    孤立代理项 \\ud800 无法 UTF-8 编码 —— 若清理分支只捕 OSError，
    这里会留下一个孤儿 .tmp-devenv。
    """
    target = tmp_path / "out.json"
    with pytest.raises(UnicodeEncodeError):
        atomic_write(target, "\ud800")
    assert not target.exists()
    assert list(tmp_path.glob("*.tmp-devenv")) == []
