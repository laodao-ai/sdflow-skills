import subprocess
from pathlib import Path

def test_retire_snippet_failsafe_under_set_e(tmp_path):
    """A5: set -e 下 python 非零退出仍不中止（尾 || echo 收尾）。"""
    fakebin = tmp_path / "bin"; fakebin.mkdir()
    py = fakebin / "python3"
    py.write_text("#!/bin/sh\nexit 1\n"); py.chmod(0o755)
    snippet = (
        'set -e\n'
        '_py=""\n'
        'command -v python3 >/dev/null 2>&1 && _py=python3\n'
        '[ -z "$_py" ] && command -v python >/dev/null 2>&1 && _py=python\n'
        'if [ -n "$_py" ]; then { "$_py" /nonexistent retire-hooks ; } || echo skipped; fi\n'
    )
    r = subprocess.run(["bash", "-c", snippet],
                       env={"PATH": f"{fakebin}:/usr/bin:/bin"},
                       capture_output=True, text=True)
    assert r.returncode == 0
    assert "skipped" in r.stdout

def test_retire_snippet_probes_python_when_no_python3(tmp_path):
    """A6: 只有 `python`（无 `python3`）时也能跑（Windows/Git-Bash 命名）。"""
    fakebin = tmp_path / "bin"; fakebin.mkdir()
    py = fakebin / "python"
    py.write_text("#!/bin/sh\necho RAN_$*\n"); py.chmod(0o755)
    snippet = (
        '_py=""\n'
        'command -v python3 >/dev/null 2>&1 && _py=python3\n'
        '[ -z "$_py" ] && command -v python >/dev/null 2>&1 && _py=python\n'
        'if [ -n "$_py" ]; then { "$_py" retire-hooks ; } || echo skipped; fi\n'
    )
    # 用绝对路径调用 bash：env PATH 只含 fakebin（无 /bin），若用字面量 "bash"
    # subprocess 自身就找不到解释器（与被测的 python3/python 探测逻辑无关）。
    r = subprocess.run(["/bin/bash", "-c", snippet],
                       env={"PATH": f"{fakebin}"},
                       capture_output=True, text=True)
    assert "RAN_retire-hooks" in r.stdout


def test_setup_sh_retire_block_binds_to_real_construct():
    """FB-4: 绑定真实 setup.sh——防有人改 retire 块丢掉 fail-safe 尾式/python 探测（上面手抄
    snippet 测的是副本、测不到 setup.sh 本身的漂移）。此测直接断言真文件含关键构造。"""
    root = Path(__file__).resolve().parents[2]
    text = (root / "setup.sh").read_text(encoding="utf-8")
    assert "retire-hooks" in text                     # 接线存在
    assert "|| echo" in text                          # A5 fail-safe 尾式
    # A6 python3/python 探测（T48 后升级为逐候选迭代 + 版本校验，取首个合格）
    assert "for _cand in python3 python" in text      # 候选迭代（含 python3 与 python）
    # 下限 3.7 而非 init.py 所需的 3.6：同一个 `$_py` 还要跑 outside-voice-job.py，
    # 而它用 `subprocess.run(capture_output=…)` —— 闸门取两个消费者的上确界。
    assert "version_info >= (3, 7)" in text            # T48 版本校验
