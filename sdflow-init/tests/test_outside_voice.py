import os, stat, subprocess, textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HELPER = REPO / "sdflow-init" / "assets" / "hack" / "outside-voice.sh"


def run(args, env=None, stdin=None):
    e = os.environ.copy()
    if env:
        e.update(env)
    return subprocess.run(["bash", str(HELPER), *args],
                          capture_output=True, text=True, env=e, input=stdin)


def make_fake_codex(tmp_path, mode="ok"):
    """PATH 前置的假 codex；写 --output-last-message 文件，stdout 掺噪声。"""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    fake = bin_dir / "codex"
    fake.write_text(textwrap.dedent("""\
        #!/usr/bin/env bash
        mode="${FAKE_CODEX_MODE:-ok}"
        out=""
        prev=""
        for a in "$@"; do
          [ "$prev" = "--output-last-message" ] && out="$a"
          prev="$a"
        done
        cat >/dev/null
        case "$mode" in
          ok)    echo "noise: reasoning trace"; [ -n "$out" ] && printf 'FAKE_FINDINGS\\n' > "$out"; exit 0 ;;
          err)   echo "auth error: run codex login" >&2; exit 1 ;;
          hang)  sleep 30 ;;
          empty) exit 0 ;;
        esac
        """))
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    return str(bin_dir)


def path_without_codex():
    return "/usr/bin:/bin"  # 只留系统基础命令，肯定无 codex


def test_version():
    r = run(["version"])
    assert r.returncode == 0
    assert r.stdout.strip() == "outside-voice.sh 1.0.0"


def test_preflight_ready(tmp_path):
    bin_dir = make_fake_codex(tmp_path)
    r = run(["preflight"], env={"PATH": f"{bin_dir}:{path_without_codex()}"})
    assert r.returncode == 0
    assert r.stdout.strip() == "ready"


def test_preflight_not_installed():
    r = run(["preflight"], env={"PATH": path_without_codex()})
    assert r.returncode == 0
    assert r.stdout.strip() == "not_installed"


def test_unknown_subcommand_usage_exit2():
    r = run(["bogus"])
    assert r.returncode == 2
    assert "usage" in r.stderr
