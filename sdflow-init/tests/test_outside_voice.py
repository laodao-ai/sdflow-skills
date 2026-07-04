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


def test_render_frame_and_delimiters(tmp_path):
    ctx = tmp_path / "ctx.md"
    ctx.write_text("some diff content\n")
    r = run(["render-prompt", "--context-file", str(ctx)])
    assert r.returncode == 0
    assert "找它【漏了】什么" in r.stdout
    assert "BEGIN UNTRUSTED CONTEXT" in r.stdout
    assert "END UNTRUSTED CONTEXT" in r.stdout
    assert "some diff content" in r.stdout
    assert "OV_TRUNCATED=false" in r.stderr


def test_render_truncation(tmp_path):
    ctx = tmp_path / "big.md"
    ctx.write_text("A" * 4000)
    r = run(["render-prompt", "--context-file", str(ctx)],
            env={"OV_MAX_CONTEXT_BYTES": "1000"})
    assert r.returncode == 0
    assert "TRUNCATED" in r.stdout
    assert "OV_TRUNCATED=true" in r.stderr


def test_render_secret_hit_exit3(tmp_path):
    ctx = tmp_path / "leak.md"
    ctx.write_text("key=AKIA" + "A" * 16 + "\n")
    r = run(["render-prompt", "--context-file", str(ctx)])
    assert r.returncode == 3
    assert "secret-hit" in r.stderr


def test_render_missing_file_exit2(tmp_path):
    r = run(["render-prompt", "--context-file", str(tmp_path / "nope.md")])
    assert r.returncode == 2
