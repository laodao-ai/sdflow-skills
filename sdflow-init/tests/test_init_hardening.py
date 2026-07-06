"""sdflow-init-hardening 批（T21/T22/T48/T49）反证哨兵测试。
Run: python3 -m pytest sdflow-init/tests/test_init_hardening.py -v
"""
import json
import os
import re
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import init as init_mod

RETIRED = "change-review-stub.py"


def _write_settings(path, *names):
    """写一个含若干退役 hook 注册的 settings.json（各占一 event）。"""
    hooks = {}
    for i, name in enumerate(names):
        hooks[f"Event{i}"] = [{"matcher": "Bash", "hooks": [
            {"type": "command", "command": f'python3 "$HOME/.claude/hooks/{name}"'}]}]
    Path(path).write_text(json.dumps({"hooks": hooks}), encoding="utf-8")


# ── T49: settings.json 并发 lost-update 收窗 ──────────────────────

class TestT49ConcurrentLostUpdate:
    def test_deregister_blocks_while_external_lock_held(self, tmp_path):
        """T49: _deregister_hook_in_settings 须在 <settings>.lock 上取 LOCK_EX 串行化
        整个读-改-写-replace 临界区。外部（模拟另一进程）持排他锁时，它 MUST 阻塞等待
        （证明并发被串行化、杜绝 lost-update）；修前无锁 → 不阻塞立即完成 → FAIL。"""
        fcntl = pytest.importorskip("fcntl")
        settings = tmp_path / "settings.json"
        _write_settings(settings, RETIRED)
        lockpath = str(settings) + ".lock"
        fd = os.open(lockpath, os.O_CREAT | os.O_RDWR, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX)   # 外部持排他锁
        done = threading.Event()
        result = {}
        def worker():
            result["ret"] = init_mod._deregister_hook_in_settings(str(settings), RETIRED)
            done.set()
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        try:
            # 外部持锁期间 worker 应阻塞（未取到 LOCK_EX）
            assert not done.wait(timeout=0.6), \
                "外部持锁时 _deregister 未阻塞 → 无串行化，lost-update 窗口未收"
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        assert done.wait(timeout=3.0), "释放锁后 _deregister 仍未完成"
        assert result["ret"] is True
        assert RETIRED not in (tmp_path / "settings.json").read_text(encoding="utf-8")

    def test_normal_deregister_still_works_and_no_tmp_residue(self, tmp_path):
        """加锁后单进程 deregister 行为不变：摘除成功、JSON 合法、无 .tmp 残渣。"""
        settings = tmp_path / "settings.json"
        _write_settings(settings, RETIRED)
        assert init_mod._deregister_hook_in_settings(str(settings), RETIRED) is True
        json.loads(settings.read_text(encoding="utf-8"))       # 合法 = 未撕裂
        assert list(tmp_path.glob("*.tmp")) == []


# ── T22: open().read() 统一 with open() ──────────────────────────

class TestT22WithOpen:
    def test_no_bare_open_read_or_json_load_open_in_source(self):
        """T22: init.py 读侧不得有裸 `open(...).read()` / `json.load(open(...))`——
        文件句柄靠 GC 关，`-W error` 下爆 19 个 PytestUnraisableExceptionWarning。
        读侧一律 `with open() as f:`。写侧本已 with，不受影响。"""
        src = Path(init_mod.__file__).read_text(encoding="utf-8")
        bare_read = re.findall(r'(?<!with )\bopen\([^\n]*?\)\.read\(\)', src)
        load_open = re.findall(r'\bjson\.load\(open\(', src)
        assert bare_read == [] and load_open == [], \
            f"残留未用 with 的读侧 open：read={bare_read} json.load(open)={load_open}"


# ── T21: inject 畸形态加固 ────────────────────────────────────────

class TestT21InjectMalformed:
    START, END = init_mod.MARK_DOC
    TOKEN = "opsx-init:start"

    def test_find_marker_line_not_misanchored_by_inline_token(self):
        """T21: _find_marker_line 用逐行 offset 累加、非 text.index 子串查找——marker 串
        在**真 marker 行之前**以行内嵌入（非行首）出现时不得锚到那个 inline 位置。
        修前 `text.index(line)` 返回最早子串命中（inline 处）→ 锚错位。"""
        marker = self.START
        # 首行 "note: <marker>" 本身不是 marker 行（lstrip 后非 <!-- 起），但含 marker 子串；
        # 真 marker 行在其后。
        text = f"note: {marker}\n\n{marker}\n真内容\n{self.END}\n"
        loc = init_mod._find_marker_line(text, self.TOKEN)
        expected_start = text.index("\n\n") + 2          # 真 marker 行起点（第三行）
        assert loc == (expected_start, expected_start + len(marker) + 1), \
            "锚到了行内嵌入的 inline marker、非真 marker 行"

    def test_inject_collapses_multiple_stale_blocks(self, tmp_path):
        """T21: 文件含多个重复托管区块（手工粘贴畸形态）→ inject 须全部收敛为单块，
        非只替换第一个而遗留其余。修前 first-start..first-end 只动首块 → 次块残留。"""
        block = (f"{self.START}\n旧内容A\n{self.END}\n")
        f = tmp_path / "CLAUDE.md"
        f.write_text("# 头\n\n" + block + "\n中间用户内容\n\n" + block + "\n尾部\n",
                     encoding="utf-8")
        init_mod.inject(str(f), *init_mod.MARK_DOC, "新内容")
        text = f.read_text(encoding="utf-8")
        assert text.count("opsx-init:start") == 1, "多重复块未收敛为单块"
        assert "新内容" in text and "旧内容A" not in text
        assert "尾部" in text                              # 末尾用户内容保留
