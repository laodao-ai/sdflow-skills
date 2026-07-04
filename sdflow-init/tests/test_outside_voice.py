import os, stat, subprocess, textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
HELPER = REPO / "sdflow-init" / "assets" / "hack" / "outside-voice.sh"


def run(args, env=None, stdin=None, timeout=15):
    e = os.environ.copy()
    if env:
        e.update(env)
    return subprocess.run(["bash", str(HELPER), *args],
                          capture_output=True, text=True, env=e, input=stdin,
                          timeout=timeout)


def make_fake_codex(tmp_path, mode="ok", with_timeout=True):
    """PATH 前置的假 codex；写 --output-last-message 文件，stdout 掺噪声。

    with_timeout=False 时不放假 timeout（用于测 timeout/gtimeout 缺失分支，
    调用方须自行把 PATH 收窄到确无系统 timeout 的范围）。
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)

    # Fake codex
    fake = bin_dir / "codex"
    fake.write_text(textwrap.dedent("""\
        #!/usr/bin/env bash
        # 留痕：若设了 FAKE_CODEX_MARKER，被调用即落地一个空文件（用于断言"未被调用"）
        [ -n "${FAKE_CODEX_MARKER:-}" ] && : > "$FAKE_CODEX_MARKER"
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
          err_with_output) echo "transient error" >&2; [ -n "$out" ] && printf 'FAKE_PARTIAL\\n' > "$out"; exit 1 ;;
        esac
        """))
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)

    if with_timeout:
        # Fake timeout (on systems without GNU coreutils); supports the `-k N` prefix
        # since production always invokes `"$OV_TIMEOUT_BIN" -k 10 "$tmo" ...` (A6).
        fake_timeout = bin_dir / "timeout"
        fake_timeout.write_text(textwrap.dedent("""\
            #!/usr/bin/env bash
            # Simple timeout stub: timeout [-k N] <seconds> <command> [args...]
            # (-k grace period accepted/discarded — stub kills immediately, same as before A6)
            if [ "$1" = "-k" ]; then shift 2; fi
            sec="$1"; shift
            "$@" &
            pid=$!
            sleep_pid=""
            (sleep "$sec"; kill -9 "$pid" 2>/dev/null) &
            sleep_pid=$!
            wait "$pid" 2>/dev/null
            rc=$?
            kill -9 "$sleep_pid" 2>/dev/null
            [ "$rc" -eq 137 ] && exit 124  # killed by -9, treat as timeout
            exit "$rc"
            """))
        fake_timeout.chmod(fake_timeout.stat().st_mode | stat.S_IEXEC)

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


def test_exec_ok_clean_stdout(tmp_path):
    bin_dir = make_fake_codex(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}", "FAKE_CODEX_MODE": "ok"})
    assert r.returncode == 0
    assert r.stdout.strip() == "FAKE_FINDINGS"      # 只有最终消息
    assert "noise" not in r.stdout                   # CLI 噪声不进 findings 通道


def test_exec_error_exit1_stderr_forwarded(tmp_path):
    bin_dir = make_fake_codex(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}", "FAKE_CODEX_MODE": "err"})
    assert r.returncode == 1
    assert "auth error" in r.stderr


def test_exec_timeout_124(tmp_path):
    bin_dir = make_fake_codex(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx), "--timeout", "1"],
            env={"PATH": f"{bin_dir}:{path_without_codex()}", "FAKE_CODEX_MODE": "hang"})
    assert r.returncode == 124


def test_exec_missing_codex_maps_exit1(tmp_path):
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx)], env={"PATH": path_without_codex()})
    assert r.returncode == 1                         # 127 归一到 1，确定性映射


def test_exec_empty_final_message_exit1(tmp_path):
    bin_dir = make_fake_codex(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}", "FAKE_CODEX_MODE": "empty"})
    assert r.returncode == 1
    assert "最终消息为空" in r.stderr


def test_exec_secret_hit_exit3(tmp_path):
    bin_dir = make_fake_codex(tmp_path)
    ctx = tmp_path / "leak.md"; ctx.write_text("key=AKIA" + "A" * 16 + "\n")
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}"})
    assert r.returncode == 3
    assert "secret-hit" in r.stderr


# ── B1: secret_scan regex additions [impl-review-fix] ──────────────────────

def test_render_secret_hit_pem_exit3(tmp_path):
    ctx = tmp_path / "leak.md"
    ctx.write_text("-----BEGIN RSA PRIVATE KEY-----\nMIIBogIBAAJ...\n-----END RSA PRIVATE KEY-----\n")
    r = run(["render-prompt", "--context-file", str(ctx)])
    assert r.returncode == 3
    assert "secret-hit" in r.stderr


def test_render_secret_hit_ghp_exit3(tmp_path):
    ctx = tmp_path / "leak.md"
    ctx.write_text("token=ghp_" + "A" * 36 + "\n")
    r = run(["render-prompt", "--context-file", str(ctx)])
    assert r.returncode == 3
    assert "secret-hit" in r.stderr


def test_render_secret_hit_xoxb_exit3(tmp_path):
    ctx = tmp_path / "leak.md"
    ctx.write_text("token=xoxb-" + "1" * 12 + "\n")
    r = run(["render-prompt", "--context-file", str(ctx)])
    assert r.returncode == 3
    assert "secret-hit" in r.stderr


def test_render_secret_hit_sk_ant_exit3(tmp_path):
    ctx = tmp_path / "leak.md"
    ctx.write_text("key=sk-ant-" + "A" * 24 + "\n")
    r = run(["render-prompt", "--context-file", str(ctx)])
    assert r.returncode == 3
    assert "secret-hit" in r.stderr


# ── B2: usage negatives (arg-parsing guards) [impl-review-fix] ─────────────

def test_usage_render_prompt_no_args_exit2():
    r = run(["render-prompt"])
    assert r.returncode == 2


def test_usage_exec_timeout_non_numeric_exit2(tmp_path):
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx), "--timeout", "abc"])
    assert r.returncode == 2


def test_usage_render_prompt_bogus_flag_exit2():
    r = run(["render-prompt", "--bogus", "x"])
    assert r.returncode == 2


def test_usage_exec_context_file_missing_value_exit2():
    # --context-file as the last token, no value following: MUST NOT hang
    # (locks the `[ $# -ge 2 ] || usage` guard before `shift 2`; run() also
    # has its own subprocess timeout as a second line of defense).
    r = run(["exec", "--context-file"])
    assert r.returncode == 2


# ── B3: unreadable context file [impl-review-fix] ──────────────────────────

def _skip_if_root():
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        pytest.skip("running as root bypasses file permission bits")


def test_render_unreadable_ctx_exit2(tmp_path):
    _skip_if_root()
    ctx = tmp_path / "secret.md"
    ctx.write_text("data\n")
    ctx.chmod(0o000)
    try:
        r = run(["render-prompt", "--context-file", str(ctx)])
        assert r.returncode == 2
    finally:
        ctx.chmod(0o644)


def test_exec_unreadable_ctx_exit2(tmp_path):
    _skip_if_root()
    bin_dir = make_fake_codex(tmp_path)
    ctx = tmp_path / "secret.md"
    ctx.write_text("data\n")
    ctx.chmod(0o000)
    try:
        r = run(["exec", "--context-file", str(ctx)],
                env={"PATH": f"{bin_dir}:{path_without_codex()}"})
        assert r.returncode == 2
        assert "context file" in r.stderr
    finally:
        ctx.chmod(0o644)


# ── B4: OV_MAX_CONTEXT_BYTES validation [impl-review-fix] ──────────────────

def test_ov_max_context_bytes_invalid_non_numeric_falls_back(tmp_path):
    ctx = tmp_path / "ctx.md"; ctx.write_text("hello\n")
    r = run(["render-prompt", "--context-file", str(ctx)],
            env={"OV_MAX_CONTEXT_BYTES": "abc"})
    assert r.returncode == 0
    assert "回落默认" in r.stderr


def test_ov_max_context_bytes_invalid_zero_falls_back(tmp_path):
    ctx = tmp_path / "ctx.md"; ctx.write_text("hello\n")
    r = run(["render-prompt", "--context-file", str(ctx)],
            env={"OV_MAX_CONTEXT_BYTES": "0"})
    assert r.returncode == 0
    assert "回落默认" in r.stderr


# ── B5: missing ctx short-circuits before codex is ever invoked ────────────

def test_exec_missing_ctx_codex_not_invoked(tmp_path):
    bin_dir = make_fake_codex(tmp_path)
    marker = tmp_path / "codex-invoked.marker"
    ctx = tmp_path / "nope.md"  # never created
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}",
                 "FAKE_CODEX_MARKER": str(marker)})
    assert r.returncode == 2
    assert not marker.exists()


# ── B6/B7: timeout/gtimeout portability [impl-review-fix] ──────────────────

def _system_has_timeout_on(path):
    r = subprocess.run(["bash", "-c", "command -v timeout || command -v gtimeout"],
                        env={**os.environ, "PATH": path}, capture_output=True, text=True)
    return r.returncode == 0


def test_preflight_missing_deps(tmp_path):
    bin_dir = make_fake_codex(tmp_path, with_timeout=False)
    path = f"{bin_dir}:/usr/bin:/bin"
    if _system_has_timeout_on(path):
        pytest.skip("system timeout/gtimeout present on PATH; cannot exercise missing-deps branch")
    r = run(["preflight"], env={"PATH": path})
    assert r.returncode == 0
    assert r.stdout.strip() == "missing-deps"


def test_exec_missing_timeout_bin_exit1(tmp_path):
    bin_dir = make_fake_codex(tmp_path, with_timeout=False)
    path = f"{bin_dir}:/usr/bin:/bin"
    if _system_has_timeout_on(path):
        pytest.skip("system timeout/gtimeout present on PATH; cannot exercise missing-deps branch")
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx)], env={"PATH": path})
    assert r.returncode == 1
    assert "timeout/gtimeout 未安装" in r.stderr


# ── B8: non-zero exit with a non-empty last-message is surfaced, not silently discarded ──

def test_exec_err_with_partial_output_exit1(tmp_path):
    bin_dir = make_fake_codex(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}", "FAKE_CODEX_MODE": "err_with_output"})
    assert r.returncode == 1
    assert "已产出最终消息" in r.stderr
