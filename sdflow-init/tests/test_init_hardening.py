"""sdflow-init-hardening 批（T21/T22/T48/T49）反证哨兵测试。
Run: python3 -m pytest sdflow-init/tests/test_init_hardening.py -v
"""
import json
import os
import re
import subprocess
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

    def test_inject_single_block_replace_unchanged(self, tmp_path):
        """T21: 单块替换语义（经安全 offset finder）不变——既有 TestInjectMarkerMigration
        覆盖迁移，本测补一条正常单块替换 + 区块外内容保全。
        注：多重复块收敛（fence-aware + 配对校验）已 defer todolist（naive collapse 在本仓
        marker-示例满仓的场景会劫持注入/吞内容，见 code-review F1/F2），本轮不做。"""
        block = f"{self.START}\n旧内容\n{self.END}\n"
        f = tmp_path / "CLAUDE.md"
        f.write_text("# 头\n\n" + block + "\n尾部用户内容\n", encoding="utf-8")
        init_mod.inject(str(f), *init_mod.MARK_DOC, "新内容")
        text = f.read_text(encoding="utf-8")
        assert text.count("opsx-init:start") == 1
        assert "新内容" in text and "旧内容" not in text
        assert "尾部用户内容" in text


# ── T48: setup.sh python 探测版本校验 ────────────────────────────

class TestT48SetupVersionCheck:
    def test_setup_probe_rejects_non_py37(self, tmp_path):
        """T48: 探测落到非 Python3.7+（裸 `python` 是 py2）时须跳过、不喂 init.py
        （f-string 解析期崩）。修前探测块无版本校验 → 会喂 py2 → FAIL。
        本测复刻 setup.sh 探测块逻辑（另有 bind 测锁真文件）。"""
        fakebin = tmp_path / "bin"; fakebin.mkdir()
        py = fakebin / "python"
        # 假 py2：-c 版本校验退出 1（模拟 <3.7）；其它参数 echo RAN（若被误喂 init.py 可检测）
        py.write_text('#!/bin/sh\nif [ "$1" = "-c" ]; then exit 1; fi\necho RAN_$*\n')
        py.chmod(0o755)
        snippet = (
            '_py=""\n'
            'for _cand in python3 python; do\n'
            '  if command -v "$_cand" >/dev/null 2>&1 && "$_cand" -c '
            "'import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)' >/dev/null 2>&1; then\n"
            '    _py="$_cand"; break\n'
            '  fi\n'
            'done\n'
            'if [ -z "$_py" ]; then echo NOPY37\n'
            'else "$_py" /nonexistent retire-hooks; fi\n'
        )
        r = subprocess.run(["/bin/bash", "-c", snippet],
                           env={"PATH": str(fakebin)}, capture_output=True, text=True)
        assert "NOPY37" in r.stdout, "非 py3.7+ 未被版本校验拦下"
        assert "RAN_" not in r.stdout, "把 init.py 误喂给了 py2"

    def test_setup_probe_falls_back_to_valid_candidate(self, tmp_path):
        """T48/codex#4: python3 不合格但 python 合格时须 fallback 到 python（不止校验第一个）。"""
        fakebin = tmp_path / "bin"; fakebin.mkdir()
        # python3 = 假 py2（版本校验退出 1）；python = 合格 py3.7+（版本校验退出 0）
        (fakebin / "python3").write_text('#!/bin/sh\nif [ "$1" = "-c" ]; then exit 1; fi\necho RAN3_$*\n')
        (fakebin / "python").write_text('#!/bin/sh\nif [ "$1" = "-c" ]; then exit 0; fi\necho RANP_$*\n')
        (fakebin / "python3").chmod(0o755); (fakebin / "python").chmod(0o755)
        snippet = (
            '_py=""\n'
            'for _cand in python3 python; do\n'
            '  if command -v "$_cand" >/dev/null 2>&1 && "$_cand" -c '
            "'import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)' >/dev/null 2>&1; then\n"
            '    _py="$_cand"; break\n'
            '  fi\n'
            'done\n'
            'if [ -z "$_py" ]; then echo NOPY37\n'
            'else "$_py" retire-hooks; fi\n'
        )
        r = subprocess.run(["/bin/bash", "-c", snippet],
                           env={"PATH": str(fakebin)}, capture_output=True, text=True)
        assert "RANP_retire-hooks" in r.stdout, "python3 旧版时未 fallback 到合格 python"
        assert "NOPY37" not in r.stdout

    def test_setup_sh_has_version_check(self):
        """T48 bind: 绑真 setup.sh——探测块须含 3.7+ 版本校验构造，防漂移丢失。

        下限 3.7（不是 init.py 所需的 3.6）：同一个 `_py` 还要跑 outside-voice-job.py，
        而它用 `subprocess.run(capture_output=…)` —— 3.7 才有。"""
        root = Path(__file__).resolve().parents[2]
        text = (root / "setup.sh").read_text(encoding="utf-8")
        assert "version_info >= (3, 7)" in text, "setup.sh 探测块缺 3.7+ 版本校验"


# ── 冷 code-review 折叠修：ensure_global_hook 对称硬化（F-B 崩溃守卫 / F-C 锁+原子）──

class TestEnsureGlobalHookHardening:
    def _spec(self, src):
        return {"name": "myhook.py", "src": str(src), "event": "PreToolUse",
                "matcher": "Bash", "cmd": 'python3 "$HOME/.claude/hooks/myhook.py"'}

    def test_malformed_settings_does_not_crash(self, tmp_path, monkeypatch):
        """F-B: 畸形 settings（非 dict entry / 非 str command，用户/三方工具可写）注册路径
        不得裸崩——原 `entry.get`/`h.get`/`name in (...or"")` 会 AttributeError/TypeError
        （与 _deregister 的 CR-F1 守卫不对称）。实证坐实过。"""
        home = tmp_path / "home"; (home / "hooks").mkdir(parents=True)
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        src = tmp_path / "myhook.py"; src.write_text("x\n", encoding="utf-8")
        (home / "settings.json").write_text(json.dumps({"hooks": {"PreToolUse": [
            "not-a-dict-entry",
            {"matcher": "Bash", "hooks": [{"type": "command", "command": 123}]},
        ]}}), encoding="utf-8")
        msg = init_mod.ensure_global_hook(self._spec(src))   # 不抛
        assert "已注册" in msg or "已就位" in msg or "已" in msg

    def test_register_acquires_exclusive_lock(self, tmp_path, monkeypatch):
        """F-C: register 路径也须在 <settings>.lock 上串行化——外部持锁时 ensure 阻塞。
        修前 register 裸读写不持锁 → 与 deregister 并发 lost-update。"""
        fcntl = pytest.importorskip("fcntl")
        home = tmp_path / "home"; (home / "hooks").mkdir(parents=True)
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        src = tmp_path / "myhook.py"; src.write_text("x\n", encoding="utf-8")
        settings = home / "settings.json"
        settings.write_text(json.dumps({"hooks": {}}), encoding="utf-8")
        fd = os.open(str(settings) + ".lock", os.O_CREAT | os.O_RDWR, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX)
        done = threading.Event()
        def worker():
            init_mod.ensure_global_hook(self._spec(src)); done.set()
        t = threading.Thread(target=worker, daemon=True); t.start()
        try:
            assert not done.wait(timeout=0.6), "外部持锁时 register 未阻塞 → 未串行化"
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN); os.close(fd)
        assert done.wait(timeout=3.0)
        data = json.loads(settings.read_text(encoding="utf-8"))
        assert "myhook.py" in json.dumps(data)

    def test_register_write_atomic_no_tmp_residue(self, tmp_path, monkeypatch):
        """F-C: register 写走 tmp+os.replace（原子），成功后无 .tmp 残渣。"""
        home = tmp_path / "home"; (home / "hooks").mkdir(parents=True)
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        src = tmp_path / "myhook.py"; src.write_text("x\n", encoding="utf-8")
        init_mod.ensure_global_hook(self._spec(src))
        data = json.loads((home / "settings.json").read_text(encoding="utf-8"))   # 合法=未撕裂
        assert "myhook.py" in json.dumps(data)
        assert list(home.glob("*.tmp")) == []
