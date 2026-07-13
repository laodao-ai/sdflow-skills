"""openspec/ 写域锁 + 原子写。

【三 skill 共用同一把锁】（spec: R-CONC）：devenv / sdflow-init / sdflow-architecture
写入面重叠（都注入 CLAUDE/AGENTS/README/INDEX）。各发一把锁 = 互斥性不可组合。
锁文件内容格式是【跨 skill 契约】—— 改它要同步改另外两个 skill + 契约测试。

【锁 MUST 短持有】：LOCK_STALE_SEC 是为亚秒级操作调的；验证可跑数分钟。
锁若跨验证持有 ⇒ 并发 session 把活锁判成残留锁 ⇒ 提示删锁 ⇒ 两 session 同写。
"""
import contextlib
import json
import os
import tempfile
import time
import uuid
from pathlib import Path

LOCK_REL = "openspec/.sdflow-write.lock"
LOCK_RETRIES = 20
LOCK_INTERVAL = 0.1
LOCK_STALE_SEC = 120


class LockBusy(Exception):
    """锁被占且未陈旧。"""


class LockStale(Exception):
    """锁疑似残留（mtime 超阈值）——提示人工删，不自动夺。"""


@contextlib.contextmanager
def write_lock(root, retries=LOCK_RETRIES, interval=LOCK_INTERVAL):
    root = Path(root)
    lockp = root / LOCK_REL
    lockp.parent.mkdir(parents=True, exist_ok=True)
    me = uuid.uuid4().hex
    rec = json.dumps({"owner": me, "pid": os.getpid(), "ts": time.time()})

    acquired = False
    for _ in range(retries):
        try:
            fd = os.open(str(lockp), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(rec)
            acquired = True
            break
        except FileExistsError:
            try:
                age = time.time() - lockp.stat().st_mtime
            except OSError:
                age = 0.0
            if age > LOCK_STALE_SEC:
                raise LockStale(
                    f"锁 mtime 超 {LOCK_STALE_SEC}s，疑似残留；"
                    f"若确认无并发进程，删除 {lockp} 后重试"
                )
            time.sleep(interval)
    if not acquired:
        raise LockBusy(f"另一 sdflow 写操作进行中；若确认无并发进程，删除 {lockp} 后重试")

    try:
        yield
    finally:
        # MUST NOT 删他人的锁：释放前核对 owner
        with contextlib.suppress(Exception):
            cur = json.loads(lockp.read_text(encoding="utf-8"))
            if cur.get("owner") == me:
                lockp.unlink()


def atomic_write(path, text, mode=None):
    """mkstemp 唯一 tmp 名 + os.replace。

    mode=None 且文件已存在 ⇒ 保留原 mode（不擅自改用户的权限位）
    mode=None 且文件不存在 ⇒ 0o644
    显式传 mode ⇒ 用它（脚本类落地物传 0o755）
    """
    path = Path(path)
    d = path.parent
    d.mkdir(parents=True, exist_ok=True)

    if mode is None:
        try:
            mode = path.stat().st_mode & 0o777
        except OSError:
            mode = 0o644

    fd, tmpname = tempfile.mkstemp(dir=str(d), prefix=path.name + ".", suffix=".tmp-devenv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.chmod(tmpname, mode)      # mkstemp 默认 0600
        os.replace(tmpname, str(path))
    except BaseException:
        # 【不能只捕 OSError】：f.write(text) 遇到无法 UTF-8 编码的内容（如孤立
        # 代理项）抛的是 UnicodeEncodeError（ValueError 子类，不是 OSError），
        # 只捕 OSError 会跳过清理、留下孤儿 tmp 文件。清理是无条件的。
        with contextlib.suppress(OSError):
            os.unlink(tmpname)
        raise
