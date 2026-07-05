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
