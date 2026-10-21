"""setup.sh 把 hack 脚本装进 ~/.sdflow/hack/ 必须原子（T31 ⑧）。

非原子 `cp` 覆盖正在被调用的脚本时，调用方可能读到半截文件。
要求：先拷到同目录临时文件，再 `mv` 覆盖；拷失败时旧文件保持原样，失败进 skipped 汇总。

怎么测：假 HOME 真跑 `bash setup.sh`，PATH 前置一个 `cp` 垫片，记录每次 cp 的目标路径。
不碰真实 HOME。
"""
import os
import subprocess
from pathlib import Path

import pytest

from test_support.windows import bash_executable, bash_path

if os.name == "nt":
    pytest.skip("setup.sh 的 Unix 安装路径", allow_module_level=True)

REPO = Path(__file__).resolve().parents[2]
SETUP = REPO / "setup.sh"
HACK_SRC = REPO / "sdflow-init" / "assets" / "hack"


def _shim_dir(tmp_path, fail_marker=""):
    """cp 垫片：把目标（最后一个参数）追加到日志；目标含 fail_marker 时失败。"""
    d = tmp_path / "shim"
    d.mkdir()
    log = tmp_path / "cp.log"
    real_cp = subprocess.run(["/bin/sh", "-c", "command -v cp"], capture_output=True,
                             text=True, encoding="utf-8", errors="replace").stdout.strip()
    (d / "cp").write_text(
        "#!/bin/sh\n"
        'for a in "$@"; do last="$a"; done\n'
        f'echo "$last" >> "{log}"\n'
        f'if [ -n "{fail_marker}" ]; then case "$last" in *"{fail_marker}"*) exit 1;; esac; fi\n'
        f'exec "{real_cp}" "$@"\n',
        encoding="utf-8",
    )
    (d / "cp").chmod(0o755)
    return d, log


def _run_setup(home, shim):
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["PATH"] = f"{shim}{os.pathsep}{env['PATH']}"
    env.pop("SDFLOW_HOME", None)
    return subprocess.run([bash_executable(), bash_path(SETUP)], cwd=str(REPO), env=env,
                          capture_output=True, text=True, timeout=300,
                          encoding="utf-8", errors="replace")


def test_hack_files_are_never_copied_directly_onto_the_final_path(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    shim, log = _shim_dir(tmp_path)
    r = _run_setup(home, shim)
    assert r.returncode == 0, r.stdout + r.stderr

    hack = home / ".sdflow" / "hack"
    direct = [line for line in log.read_text(encoding="utf-8").splitlines()
              if Path(line).parent == hack
              and Path(line).suffix in (".sh", ".py", ".md")
              and not Path(line).name.startswith(".")]
    assert not direct, f"cp 直接写最终路径（非原子）: {direct}"

    # 终态：内容与源一致，无临时文件残留，脚本带执行位
    for src in sorted(HACK_SRC.glob("*.sh")):
        dest = hack / src.name
        assert dest.read_bytes() == src.read_bytes()
        assert os.access(dest, os.X_OK)
    leftovers = [p.name for p in hack.iterdir() if p.name.startswith(".") and ".tmp" in p.name]
    assert not leftovers, leftovers


def test_failed_copy_keeps_old_file_intact_and_reports_skipped(tmp_path):
    home = tmp_path / "home"
    hack = home / ".sdflow" / "hack"
    hack.mkdir(parents=True)
    old = hack / "outside-voice.sh"
    old.write_text("#!/bin/sh\n# OLD COMPLETE VERSION\n", encoding="utf-8")

    shim, _ = _shim_dir(tmp_path, fail_marker="outside-voice.sh")
    r = _run_setup(home, shim)
    assert r.returncode == 0, r.stdout + r.stderr

    assert old.read_text(encoding="utf-8") == "#!/bin/sh\n# OLD COMPLETE VERSION\n"
    assert "hack/outside-voice.sh" in r.stdout and "装不上" in r.stdout
    leftovers = [p.name for p in hack.iterdir() if p.name.startswith(".") and ".tmp" in p.name]
    assert not leftovers, leftovers
