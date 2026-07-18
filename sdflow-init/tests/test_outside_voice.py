import os, stat, subprocess, textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
HELPER = REPO / "sdflow-init" / "assets" / "hack" / "outside-voice.sh"


def run(args, env=None, stdin=None, timeout=15):
    e = os.environ.copy()
    # host=unknown / runner 分叉相关测试要求 SDFLOW_VOICE_* 确定处于测试指定状态——防宿主 shell
    # 已 eval 过 resolve-models.sh 把这两个变量泄漏进 ambient 环境，污染"未设置"类断言。
    e.pop("SDFLOW_VOICE_RUNNER", None)
    e.pop("SDFLOW_VOICE_MODEL", None)
    if env:
        e.update(env)
    return subprocess.run(["bash", str(HELPER), *args],
                          capture_output=True, text=True, env=e, input=stdin,
                          timeout=timeout)


def _write_fake_timeout(bin_dir):
    """Fake timeout (on systems without GNU coreutils); supports the `-k N` prefix
    since production always invokes `"$OV_TIMEOUT_BIN" -k 10 "$tmo" ...` (A6)."""
    fake_timeout = bin_dir / "timeout"
    fake_timeout.write_text(textwrap.dedent("""\
        #!/usr/bin/env bash
        # Simple timeout stub: timeout [-k N] <seconds> <command> [args...]
        # (-k grace period accepted/discarded — stub kills immediately, same as before A6)
        # Backgrounding a job in a non-interactive/no-job-control shell defaults its stdin
        # to /dev/null unless explicitly redirected — buffer stdin to a temp file first so
        # the wrapped command still sees the real prompt (exposed by claude-path stdin-capture
        # assertions; codex path never asserted stdin content so this was latent before).
        if [ "$1" = "-k" ]; then shift 2; fi
        sec="$1"; shift
        stdin_tmp=$(mktemp)
        cat > "$stdin_tmp"
        "$@" < "$stdin_tmp" &
        pid=$!
        sleep_pid=""
        (sleep "$sec"; kill -9 "$pid" 2>/dev/null) &
        sleep_pid=$!
        wait "$pid" 2>/dev/null
        rc=$?
        kill -9 "$sleep_pid" 2>/dev/null
        rm -f "$stdin_tmp"
        [ "$rc" -eq 137 ] && exit 124  # killed by -9, treat as timeout
        exit "$rc"
        """))
    fake_timeout.chmod(fake_timeout.stat().st_mode | stat.S_IEXEC)


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
          secret_output) [ -n "$out" ] && printf 'finding: leaked AKIA%s\\n' AAAAAAAAAAAAAAAA > "$out"; exit 0 ;;
        esac
        """))
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)

    if with_timeout:
        _write_fake_timeout(bin_dir)

    return str(bin_dir)


def make_fake_claude(tmp_path, mode="ok", with_timeout=True):
    """PATH 前置的假 claude（反向 runner，host=codex 场景）。

    `claude -p --output-format text` 直接把最终答案写 stdout（不像 codex 需要
    `--output-last-message` 单独提取）——假二进制照此语义模拟：stdout 即最终消息。
    额外支持通过环境变量捕获调用留痕，供三旗承重墙 / 共用 render_prompt 断言：
      FAKE_CLAUDE_ARGS_FILE  — 收到的完整 argv（每行一个 token）
      FAKE_CLAUDE_STDIN_FILE — 收到的完整 stdin（即渲染后的 prompt）
      FAKE_CLAUDE_MARKER     — 被调用即落地一个空文件（用于断言"未被调用"）
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)

    fake = bin_dir / "claude"
    fake.write_text(textwrap.dedent("""\
        #!/usr/bin/env bash
        [ -n "${FAKE_CLAUDE_ARGS_FILE:-}" ] && printf '%s\\n' "$@" > "${FAKE_CLAUDE_ARGS_FILE}"
        [ -n "${FAKE_CLAUDE_MARKER:-}" ] && : > "$FAKE_CLAUDE_MARKER"
        if [ -n "${FAKE_CLAUDE_STDIN_FILE:-}" ]; then
          cat > "${FAKE_CLAUDE_STDIN_FILE}"
        else
          cat >/dev/null
        fi
        mode="${FAKE_CLAUDE_MODE:-ok}"
        case "$mode" in
          ok)    printf 'CLAUDE_FAKE_FINDINGS\\n'; exit 0 ;;
          err)   echo "claude auth error" >&2; exit 1 ;;
          hang)  sleep 30 ;;
          empty) exit 0 ;;
          err_with_output) echo "transient error" >&2; printf 'CLAUDE_PARTIAL\\n'; exit 1 ;;
          secret_output) printf 'finding: leaked AKIA%s\\n' AAAAAAAAAAAAAAAA; exit 0 ;;
        esac
        """))
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)

    if with_timeout:
        _write_fake_timeout(bin_dir)

    return str(bin_dir)


def path_without_codex():
    return "/usr/bin:/bin"  # 只留系统基础命令，肯定无 codex/claude


def test_version():
    r = run(["version"])
    assert r.returncode == 0
    # 1.3.0：A1 反向 claude 路径补应用层读围栏（--settings permissions.deny）+ 输出侧 secret_scan。
    # 1.4.0：R1 截断 UTF-8 字符边界回扫（头/尾段各自合法）+ stderr 丢弃字节计数（观测性）。
    assert r.stdout.strip() == "outside-voice.sh 1.4.0"


# ── Step 1: preflight 探的是 $SDFLOW_VOICE_RUNNER 的 CLI，不是固定 codex ──────

def test_preflight_ready(tmp_path):
    bin_dir = make_fake_codex(tmp_path)
    r = run(["preflight"], env={"PATH": f"{bin_dir}:{path_without_codex()}",
                                 "SDFLOW_VOICE_RUNNER": "codex"})
    assert r.returncode == 0
    assert r.stdout.strip() == "ready"


def test_preflight_not_installed():
    r = run(["preflight"], env={"PATH": path_without_codex(), "SDFLOW_VOICE_RUNNER": "codex"})
    assert r.returncode == 0
    assert r.stdout.strip() == "not_installed"


def test_preflight_probes_target_runner_claude_when_ready(tmp_path):
    # 只有 claude 在 PATH（无 codex）；SDFLOW_VOICE_RUNNER=claude ⇒ preflight 探 claude
    bin_dir = make_fake_claude(tmp_path)
    r = run(["preflight"], env={"PATH": f"{bin_dir}:{path_without_codex()}",
                                 "SDFLOW_VOICE_RUNNER": "claude"})
    assert r.returncode == 0
    assert r.stdout.strip() == "ready"


def test_preflight_not_hardcoded_to_codex(tmp_path):
    # codex 在 PATH 上（对照组：若仍硬编码探 codex，这里会误报 ready）；
    # SDFLOW_VOICE_RUNNER=claude 但 claude 不在 PATH ⇒ 必须是 not_installed，
    # 证明 preflight 探的是目标 runner 而非"随便一个已知 CLI 存在"。
    bin_dir = make_fake_codex(tmp_path)
    r = run(["preflight"], env={"PATH": f"{bin_dir}:{path_without_codex()}",
                                 "SDFLOW_VOICE_RUNNER": "claude"})
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
            env={"PATH": f"{bin_dir}:{path_without_codex()}", "SDFLOW_VOICE_RUNNER": "codex",
                 "FAKE_CODEX_MODE": "ok"})
    assert r.returncode == 0
    assert r.stdout.strip() == "FAKE_FINDINGS"      # 只有最终消息
    assert "noise" not in r.stdout                   # CLI 噪声不进 findings 通道


def test_exec_error_exit1_stderr_forwarded(tmp_path):
    bin_dir = make_fake_codex(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}", "SDFLOW_VOICE_RUNNER": "codex",
                 "FAKE_CODEX_MODE": "err"})
    assert r.returncode == 1
    assert "auth error" in r.stderr


def test_exec_timeout_124(tmp_path):
    bin_dir = make_fake_codex(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx), "--timeout", "1"],
            env={"PATH": f"{bin_dir}:{path_without_codex()}", "SDFLOW_VOICE_RUNNER": "codex",
                 "FAKE_CODEX_MODE": "hang"})
    assert r.returncode == 124


def test_exec_missing_codex_maps_exit1(tmp_path):
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": path_without_codex(), "SDFLOW_VOICE_RUNNER": "codex"})
    assert r.returncode == 1                         # 127 归一到 1，确定性映射


def test_exec_empty_final_message_exit1(tmp_path):
    bin_dir = make_fake_codex(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}", "SDFLOW_VOICE_RUNNER": "codex",
                 "FAKE_CODEX_MODE": "empty"})
    assert r.returncode == 1
    assert "最终消息为空" in r.stderr


def test_exec_secret_hit_exit3(tmp_path):
    bin_dir = make_fake_codex(tmp_path)
    ctx = tmp_path / "leak.md"; ctx.write_text("key=AKIA" + "A" * 16 + "\n")
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}", "SDFLOW_VOICE_RUNNER": "codex"})
    assert r.returncode == 3
    assert "secret-hit" in r.stderr


# ── A1: 输出侧 secret_scan —— runner 回传 findings 含密钥形状 → 拦下、exit 3、不进 findings 通道 ──
# （防注入成功后经【返回通道】exfil：入境 secret_scan 只扫 context，出境不扫 = 原样带出）
def test_exec_output_side_secret_scan_codex_exit3(tmp_path):
    bin_dir = make_fake_codex(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")   # context 干净，密钥来自 runner 回传
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}", "SDFLOW_VOICE_RUNNER": "codex",
                 "FAKE_CODEX_MODE": "secret_output"})
    assert r.returncode == 3
    assert "AKIA" not in r.stdout            # 密钥 MUST NOT 进 findings 通道
    assert "secret-hit" in r.stderr


def test_exec_output_side_secret_scan_claude_exit3(tmp_path):
    bin_dir = make_fake_claude(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}",
                 "SDFLOW_VOICE_RUNNER": "claude", "SDFLOW_VOICE_MODEL": "x",
                 "FAKE_CLAUDE_MODE": "secret_output"})
    assert r.returncode == 3
    assert "AKIA" not in r.stdout
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
                env={"PATH": f"{bin_dir}:{path_without_codex()}", "SDFLOW_VOICE_RUNNER": "codex"})
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
            env={"PATH": f"{bin_dir}:{path_without_codex()}", "SDFLOW_VOICE_RUNNER": "codex",
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
    r = run(["preflight"], env={"PATH": path, "SDFLOW_VOICE_RUNNER": "codex"})
    assert r.returncode == 0
    assert r.stdout.strip() == "missing-deps"


def test_preflight_missing_deps_claude_runner(tmp_path):
    # Step 6：missing-deps 判据（CLI 在但 timeout/gtimeout 缺）对目标 runner=claude 同样成立
    # ——outside-voice.sh 只负责正确返回 stdout 契约值；把 missing-deps 映射为锚
    # reason_code="preflight-error" 是调用方 SKILL 的事（Task 8 scope，见 header 契约注释）。
    bin_dir = make_fake_claude(tmp_path, with_timeout=False)
    path = f"{bin_dir}:/usr/bin:/bin"
    if _system_has_timeout_on(path):
        pytest.skip("system timeout/gtimeout present on PATH; cannot exercise missing-deps branch")
    r = run(["preflight"], env={"PATH": path, "SDFLOW_VOICE_RUNNER": "claude"})
    assert r.returncode == 0
    assert r.stdout.strip() == "missing-deps"


def test_exec_missing_timeout_bin_exit1(tmp_path):
    bin_dir = make_fake_codex(tmp_path, with_timeout=False)
    path = f"{bin_dir}:/usr/bin:/bin"
    if _system_has_timeout_on(path):
        pytest.skip("system timeout/gtimeout present on PATH; cannot exercise missing-deps branch")
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx)], env={"PATH": path, "SDFLOW_VOICE_RUNNER": "codex"})
    assert r.returncode == 1
    assert "timeout/gtimeout 未安装" in r.stderr


# ── B8: non-zero exit with a non-empty last-message is surfaced, not silently discarded ──

def test_exec_err_with_partial_output_exit1(tmp_path):
    bin_dir = make_fake_codex(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}", "SDFLOW_VOICE_RUNNER": "codex",
                 "FAKE_CODEX_MODE": "err_with_output"})
    assert r.returncode == 1
    assert "已产出最终消息" in r.stderr


# ═══════════════════════════════════════════════════════════════════════════
# add-codex-host-support Task 7: outside-voice 去硬编码
# ═══════════════════════════════════════════════════════════════════════════

# ── Step 3/4: 反向 claude 路径 —— 共用 secret_scan/render_prompt + 三旗承重墙 ──

def test_exec_claude_reverse_path_shares_render_prompt(tmp_path):
    """GC-4：反向路径 MUST NOT 另起炉灶组装 prompt —— 断言 claude 收到的 stdin 就是
    同一个 render_prompt 的输出（FRAME + UNTRUSTED CONTEXT 硬分隔 + 原始内容）。"""
    bin_dir = make_fake_claude(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("some diff content for claude reverse path\n")
    stdin_capture = tmp_path / "claude-stdin.txt"
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}",
                 "SDFLOW_VOICE_RUNNER": "claude", "SDFLOW_VOICE_MODEL": "claude-strong-placeholder",
                 "FAKE_CLAUDE_STDIN_FILE": str(stdin_capture)})
    assert r.returncode == 0
    prompt = stdin_capture.read_text()
    assert "找它【漏了】什么" in prompt
    assert "BEGIN UNTRUSTED CONTEXT" in prompt
    assert "END UNTRUSTED CONTEXT" in prompt
    assert "some diff content for claude reverse path" in prompt


def test_exec_claude_reverse_path_three_flags_golden(tmp_path):
    """🔒 GC-5 安全承重墙：反向 claude exec 行 MUST 三旗齐全，MUST NOT 漂移。"""
    bin_dir = make_fake_claude(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    args_file = tmp_path / "claude-args.txt"
    repo_root = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                capture_output=True, text=True).stdout.strip()
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}",
                 "SDFLOW_VOICE_RUNNER": "claude", "SDFLOW_VOICE_MODEL": "claude-strong-placeholder",
                 "FAKE_CLAUDE_ARGS_FILE": str(args_file)})
    assert r.returncode == 0
    argv = args_file.read_text().splitlines()

    # 正向：四旗齐全且取值正确（三旗 + A1 读围栏 --settings）
    assert "--tools" in argv
    assert argv[argv.index("--tools") + 1] == "Read,Grep,Glob"
    assert "--strict-mcp-config" in argv
    assert "--add-dir" in argv
    assert argv[argv.index("--add-dir") + 1] == repo_root
    assert "-p" in argv
    assert "--model" in argv
    assert argv[argv.index("--model") + 1] == "claude-strong-placeholder"
    assert "--output-format" in argv
    assert argv[argv.index("--output-format") + 1] == "text"
    # A1 第四旗：--settings 读围栏（permissions.deny 挡凭证库路径，应用层读边界）
    assert "--settings" in argv, "A1 读围栏缺失：反向路径 MUST 带 --settings permissions.deny"
    fence = argv[argv.index("--settings") + 1]
    assert '"deny"' in fence
    for pat in (".ssh", ".aws", "id_rsa"):
        assert pat in fence, f"读围栏缺凭证库模式 {pat}"

    # 负向：MUST NOT 出现非只读工具 / 零工具 / denylist / allowlist
    joined = " ".join(argv)
    for forbidden in ("Write", "Bash", "WebFetch", "--disallowedTools", "--allowedTools"):
        assert forbidden not in joined, f"反向路径承重墙回归：出现 {forbidden!r}"
    assert argv[argv.index("--tools") + 1] != ""  # MUST NOT --tools "" 零工具


def test_exec_claude_secret_hit_exit3_no_fallback(tmp_path):
    """🔒 GC-5：secret 命中时反向路径也 exit 3 拒发，且 MUST NOT fallback（claude 从未被调用）。"""
    bin_dir = make_fake_claude(tmp_path)
    ctx = tmp_path / "leak.md"; ctx.write_text("key=AKIA" + "A" * 16 + "\n")
    marker = tmp_path / "claude-invoked.marker"
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}",
                 "SDFLOW_VOICE_RUNNER": "claude", "SDFLOW_VOICE_MODEL": "x",
                 "FAKE_CLAUDE_MARKER": str(marker)})
    assert r.returncode == 3
    assert "secret-hit" in r.stderr
    assert not marker.exists()  # 未 fallback：claude 二进制从未被执行


def test_secret_scan_stderr_redacted_render_prompt(tmp_path):
    """D8 脱敏：stderr 只出规则类型 + 行号，MUST NOT 打印命中原行/匹配值。"""
    ctx = tmp_path / "leak.md"
    secret_value = "AKIA" + "B" * 16
    ctx.write_text(f"aws_key={secret_value}\n")
    r = run(["render-prompt", "--context-file", str(ctx)])
    assert r.returncode == 3
    assert "secret-hit" in r.stderr
    assert secret_value not in r.stderr
    assert secret_value not in r.stdout
    assert "aws-akid" in r.stderr           # 规则类型仍可见（可诊断）
    assert "行=1" in r.stderr or ":1" in r.stderr  # 行号仍可见


def test_secret_scan_stderr_redacted_exec_path(tmp_path):
    """D8 脱敏对 exec 路径同样成立（两路径共用同一 secret_scan）。"""
    bin_dir = make_fake_codex(tmp_path)
    secret_value = "ghp_" + "C" * 36
    ctx = tmp_path / "leak.md"; ctx.write_text(f"token={secret_value}\n")
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}", "SDFLOW_VOICE_RUNNER": "codex"})
    assert r.returncode == 3
    assert secret_value not in r.stdout
    assert secret_value not in r.stderr


def test_secret_scan_multiple_rule_types_all_reported_redacted(tmp_path):
    ctx = tmp_path / "leak.md"
    ctx.write_text("a=" + "AKIA" + "D" * 16 + "\nb=" + "ghp_" + "E" * 36 + "\n")
    r = run(["render-prompt", "--context-file", str(ctx)])
    assert r.returncode == 3
    assert "aws-akid" in r.stderr
    assert "github-pat" in r.stderr


# ── claude 路径与 codex 路径行为对称（F1/F2/F3/F1b 等失败模式，parity） ────

def test_exec_claude_ok_clean_stdout(tmp_path):
    bin_dir = make_fake_claude(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}",
                 "SDFLOW_VOICE_RUNNER": "claude", "SDFLOW_VOICE_MODEL": "x",
                 "FAKE_CLAUDE_MODE": "ok"})
    assert r.returncode == 0
    assert r.stdout.strip() == "CLAUDE_FAKE_FINDINGS"


def test_exec_claude_error_exit1_stderr_forwarded(tmp_path):
    bin_dir = make_fake_claude(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}",
                 "SDFLOW_VOICE_RUNNER": "claude", "SDFLOW_VOICE_MODEL": "x",
                 "FAKE_CLAUDE_MODE": "err"})
    assert r.returncode == 1
    assert "claude auth error" in r.stderr


def test_exec_claude_timeout_124(tmp_path):
    bin_dir = make_fake_claude(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx), "--timeout", "1"],
            env={"PATH": f"{bin_dir}:{path_without_codex()}",
                 "SDFLOW_VOICE_RUNNER": "claude", "SDFLOW_VOICE_MODEL": "x",
                 "FAKE_CLAUDE_MODE": "hang"})
    assert r.returncode == 124


def test_exec_claude_empty_final_message_exit1(tmp_path):
    bin_dir = make_fake_claude(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}",
                 "SDFLOW_VOICE_RUNNER": "claude", "SDFLOW_VOICE_MODEL": "x",
                 "FAKE_CLAUDE_MODE": "empty"})
    assert r.returncode == 1
    assert "最终消息为空" in r.stderr


def test_exec_claude_err_with_partial_output_exit1(tmp_path):
    bin_dir = make_fake_claude(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}",
                 "SDFLOW_VOICE_RUNNER": "claude", "SDFLOW_VOICE_MODEL": "x",
                 "FAKE_CLAUDE_MODE": "err_with_output"})
    assert r.returncode == 1
    assert "已产出最终消息" in r.stderr


def test_exec_claude_missing_model_fail_loud(tmp_path):
    """SDFLOW_VOICE_MODEL 未设置时 claude 反向路径不可构造 --model，MUST fail-loud 且不 fallback。"""
    bin_dir = make_fake_claude(tmp_path)
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    marker = tmp_path / "claude-invoked.marker"
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}",
                 "SDFLOW_VOICE_RUNNER": "claude",
                 "FAKE_CLAUDE_MARKER": str(marker)})
    assert r.returncode == 1
    assert "SDFLOW_VOICE_MODEL" in r.stderr
    assert not marker.exists()


def test_exec_unknown_runner_value_exit1(tmp_path):
    bin_dir = make_fake_claude(tmp_path)  # 只需要它的假 timeout；claude 二进制本身用不到
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}", "SDFLOW_VOICE_RUNNER": "bogus-runner"})
    assert r.returncode == 1
    assert "bogus-runner" in r.stderr


# ── Step 7: host=unknown（$SDFLOW_VOICE_RUNNER 空/未设）⇒ 不跑 voice，fail-loud ──

def test_preflight_host_unknown_unset_fail_loud(tmp_path):
    bin_dir = make_fake_codex(tmp_path)  # CLI 存在与否不重要——runner 本身未确定
    r = run(["preflight"], env={"PATH": f"{bin_dir}:{path_without_codex()}"})
    assert r.returncode == 1
    assert "SDFLOW_VOICE_RUNNER" in r.stderr
    assert r.stdout.strip() == ""  # MUST NOT 落 not_installed/missing-deps/ready 混淆调用方


def test_preflight_host_unknown_empty_string_fail_loud():
    r = run(["preflight"], env={"SDFLOW_VOICE_RUNNER": ""})
    assert r.returncode == 1
    assert "SDFLOW_VOICE_RUNNER" in r.stderr


def test_exec_host_unknown_fail_loud_no_runner_invoked(tmp_path):
    bin_dir = make_fake_codex(tmp_path)
    marker = tmp_path / "codex-invoked.marker"
    ctx = tmp_path / "ctx.md"; ctx.write_text("diff\n")
    r = run(["exec", "--context-file", str(ctx)],
            env={"PATH": f"{bin_dir}:{path_without_codex()}", "FAKE_CODEX_MARKER": str(marker)})
    assert r.returncode == 1
    assert "SDFLOW_VOICE_RUNNER" in r.stderr
    assert not marker.exists()  # host=unknown ⇒ 不跑 voice，MUST NOT 任选 runner 跑了充作跨模型
