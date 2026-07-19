"""守 outside-voice.sh 的 runner 子进程生命周期〔R2 · design D2〕。

【为什么需要这个测试】
helper 原先【前台】跑 `timeout -k 10 <tmo> <runner> ...`。父进程被 SIGINT/SIGTERM/SIGHUP
回收时，bash 的 EXIT trap 确实会执行（workdir 被清了）——但 trap 里【没有子 PID 可杀】，
于是 timeout 及其整棵子树 reparent 到 PID 1，继续跑满内层超时、继续烧 API 调用额度。
这是一次典型的静默失效：调用方以为「取消了」，实际远端调用还在跑。

修法 = runner 后台启动 + 记 PID + wait 取码；清理函数先 TERM、宽限后 KILL 兜底，再删 workdir。

【诚实边界 —— 本测试【不】覆盖，也不该覆盖】
父进程被 **SIGKILL(-9)** 时 trap 根本不执行 ⇒ 孤儿【仍会存活】。这是 shell 层无解的残余，
不是实现疏漏。见 test_sigkill_residue_is_documented_not_claimed_solved：它锁的是
「文档如实登记该残余、且不声称已根治」，而不是「残余已消失」。

【测试接缝】
真 `timeout`（或 gtimeout）+ PATH 前置的假 runner。假 runner 把自己与孙进程的 PID 落盘，
外部发信号后按 PID 验尸——不依赖进程名匹配，也不依赖 ps 输出格式。

【为什么解释器要钉两档，不能只用 PATH 里的 `bash`】〔I2〕
helper 的 shebang 是 `#!/usr/bin/env bash` ⇒ 它在**用户 PATH 里的那个 bash** 上跑。
macOS 自带 `/bin/bash` 是 **3.2**（2007 年），而装了 homebrew 的开发机 PATH 里通常是
bash **5.x**——两者语义有实打实的差异（本轮就撞到一个：3.2 扫变量名不是 multibyte-aware，
`"$src，"` 会把全角逗号首字节吞进标识符 ⇒ `set -u` 下运行时罢工、清理逻辑整个不执行）。
只跑 PATH 里那一个 ⇒ 换台开发机就再也不走 3.2 路径，同类 bug 静默出厂。
这与本仓已记录的「Windows CI 跑 bash 脚本」教训同形：本地照不到、真 runner 才抓到。
∴ 两档都跑；两者指向同一个可执行文件时去重（别白跑一遍），`/bin/bash` 不存在的平台
（多数 Linux 发行版把 bash 装在 /usr/bin）**skip 而非 fail**。
"""
import os
import re
import shutil
import signal
import stat
import subprocess
import textwrap
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
HELPER = REPO / "sdflow-init" / "assets" / "hack" / "outside-voice.sh"

CONTEXT_PROBE = "UNIQUE_CONTEXT_BODY_中文正文_MUST_NOT_LEAK"

TIMEOUT_BIN = shutil.which("timeout") or shutil.which("gtimeout")
needs_real_timeout = pytest.mark.skipif(
    TIMEOUT_BIN is None,
    reason="需要真 timeout/gtimeout —— 假 stub 自己也会 background，验不出进程组级联",
)


def _bash_params():
    """→ [(label, path)]：系统 bash 与 PATH bash 两档，realpath 相同则去重〔I2〕。

    `/bin/bash` 总是作为一个 param 出现（即使不存在）——这样它在无 `/bin/bash` 的平台上
    是一条**可见的 skip**，而不是悄悄消失的一档（消失 = 又一个零信号静默降级）。
    """
    candidates = [("system", "/bin/bash"), ("path", shutil.which("bash"))]
    out, seen = [], set()
    for label, path in candidates:
        if path is None:
            continue
        real = os.path.realpath(path)
        if real in seen:
            continue
        seen.add(real)
        out.append((label, path))
    return out


BASH_PARAMS = _bash_params()


@pytest.fixture(params=BASH_PARAMS, ids=[f"{lbl}:{p}" for lbl, p in BASH_PARAMS])
def bash_bin(request):
    """跑 helper 用的 bash 解释器；缺失即 skip（Linux 上可能没有 /bin/bash）。"""
    _, path = request.param
    if not os.path.exists(path):
        pytest.skip(f"{path} 不存在（本平台无该 bash）")
    return path


def test_bash_matrix_is_not_empty():
    """自防呆：矩阵打空时下面所有用例会「全绿」地一条都不跑。"""
    assert BASH_PARAMS, "没解析到任何 bash 解释器 —— 生命周期用例形同虚设"


def _alive(pid: int) -> bool:
    """PID 是否仍存活。这些进程不是本测试的子进程 ⇒ 无僵尸干扰，signal 0 判据可信。"""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:      # 存在但不属于我们（本测试不会出现，保守当活着）
        return True
    return True


def _make_env(tmp_path, pidfile: Path, *, helper: Path = None):
    """PATH 前置一个假 codex：起一个长睡孙进程，把 (自身 PID, 孙 PID) 落盘后 wait。"""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    fake = bin_dir / "codex"
    fake.write_text(textwrap.dedent(f"""\
        #!/usr/bin/env bash
        cat >/dev/null            # 吞掉 prompt（stdin），证明后台化没把 stdin 变 /dev/null
        sleep 300 &
        child=$!
        printf '%s %s\\n' "$$" "$child" > "{pidfile}"
        wait "$child"
        """))
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)

    ctx = tmp_path / "ctx.md"
    ctx.write_text(f"context body\n{CONTEXT_PROBE}\nmore\n", encoding="utf-8")

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["SDFLOW_VOICE_RUNNER"] = "codex"
    env.pop("SDFLOW_VOICE_MODEL", None)
    return env, ctx


def _await_pids(pidfile: Path, proc, limit=20.0):
    """等假 runner 把 PID 落盘。"""
    deadline = time.time() + limit
    while time.time() < deadline:
        if pidfile.exists():
            parts = pidfile.read_text().split()
            if len(parts) == 2:
                return int(parts[0]), int(parts[1])
        assert proc.poll() is None, "helper 在 runner 起来之前就退了"
        time.sleep(0.05)
    raise AssertionError("假 runner 未在时限内落盘 PID")


def _run_until_killed(helper: Path, env, ctx: Path, sig: int, cwd: Path, pidfile: Path,
                      bash_bin: str):
    """起 helper → 等 runner 落盘 → 发 sig → 收尸。返回 (rc, stderr, runner_pid, grandchild_pid)。"""
    proc = subprocess.Popen(
        [bash_bin, str(helper), "exec", "--context-file", str(ctx), "--timeout", "300"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, cwd=str(cwd),
    )
    try:
        runner_pid, grandchild_pid = _await_pids(pidfile, proc)
        proc.send_signal(sig)
        out, err = proc.communicate(timeout=60)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.communicate()
    # 给内核/父进程回收留一点时间，再验尸（避免与 kill 的传递竞态）
    deadline = time.time() + 5.0
    while time.time() < deadline and (_alive(runner_pid) or _alive(grandchild_pid)):
        time.sleep(0.1)
    return proc.returncode, err, runner_pid, grandchild_pid


# ── ⭐ 核心：父被回收 ⇒ runner 子树必死 ────────────────────────────────────────

@needs_real_timeout
@pytest.mark.parametrize("sig,name", [
    (signal.SIGTERM, "TERM"),
    (signal.SIGINT, "INT"),
    (signal.SIGHUP, "HUP"),
])
def test_runner_subtree_dies_when_parent_is_signalled(tmp_path, sig, name, bash_bin):
    """⭐ 三个可捕获回收信号下，runner 及其孙进程都不得存活为 PID 1 的孤儿。

    孙进程一并断言，锁的是 design 已实测的那条前提：杀 timeout 会连带杀掉它自建
    进程组内的整棵子树 ⇒ helper 无需自管进程组。若该前提在某平台不成立，这里当场红。
    """
    pidfile = tmp_path / f"pids-{name}"
    env, ctx = _make_env(tmp_path, pidfile)
    rc, err, runner_pid, grandchild_pid = _run_until_killed(
        HELPER, env, ctx, sig, tmp_path, pidfile, bash_bin
    )
    assert not _alive(runner_pid), (
        f"R2 复发：helper 收到 {name} 后，runner PID={runner_pid} 仍存活（孤儿继续烧 API）"
    )
    assert not _alive(grandchild_pid), (
        f"runner 的孙进程 PID={grandchild_pid} 仍存活 —— 进程组级联前提不成立"
    )


def _make_env_runner_ignores_term(tmp_path, pidfile: Path):
    """同 `_make_env`，但假 runner 显式 `trap '' TERM` 忽略 TERM。

    〔F-新2 · fix-mechanical-layer-silent-failures〕`_make_env` 的假 runner 从不忽略
    TERM，∴「runner 主动忽略 SIGTERM 时，ov_cleanup 的 KILL 兜底 / timeout -k 升级
    能不能真的灭掉整棵子树」这条路径从未被验证过——这里补上。
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    fake = bin_dir / "codex"
    fake.write_text(textwrap.dedent(f"""\
        #!/usr/bin/env bash
        trap '' TERM             # 主动忽略 TERM —— 本用例要验的就是这条路径
        cat >/dev/null
        sleep 300 &
        child=$!
        printf '%s %s\\n' "$$" "$child" > "{pidfile}"
        wait "$child"
        """))
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)

    ctx = tmp_path / "ctx.md"
    ctx.write_text(f"context body\n{CONTEXT_PROBE}\nmore\n", encoding="utf-8")

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["SDFLOW_VOICE_RUNNER"] = "codex"
    env.pop("SDFLOW_VOICE_MODEL", None)
    return env, ctx


@needs_real_timeout
def test_runner_ignoring_term_survives_kill_escalation_documented_residual(tmp_path, bash_bin):
    """⭐〔F-新2〕假 runner 显式忽略 TERM 时，实测子树【存活】——这是一个真实、此前
    从未被验证过的残余，MUST NOT 被静默接受，已显式登记进 design.md D2 残余表第 (d) 条
    （见 test_term_ignoring_residual_is_documented_in_design 的机械锁）。

    【为什么会存活 —— 已用手工探针实测复现，非猜测】
    `OV_RUNNER_PID` 记的是【`timeout` 自身】的 PID（`"$ov_timeout_bin" ... codex ... &`
    之后 `$!`），不是 runner 的 PID。`ov_cleanup` 先对 `$OV_RUNNER_PID`（timeout）发
    TERM——timeout 收到后会转发给子进程组，但子进程主动 trap 忽略，不为所动；
    timeout 自己的 `-k 10` 升级窗口长达 10s，而 `ov_cleanup` 只等约 1s 就直接对
    `$OV_RUNNER_PID`（timeout 本身）发 SIGKILL——SIGKILL 不可捕获，timeout 被瞬间
    杀死，【来不及】跑到它自己那条会向子进程组转发 KILL 的升级逻辑。
    ⇒ runner 与其孙进程都不在 `$OV_RUNNER_PID` 之下（我们只杀了 timeout 这一个 PID，
    不是负 PID/进程组），二者 reparent 到 PID 1 继续存活。

    【诚实边界，不是待修复项】本用例只锁定「这是真的、且已如实记录」，不代表本次
    change 要修——修复需要改变 ov_cleanup 的信号投递目标（如改发进程组）或延长/去掉
    我们自己的抢跑升级窗口，超出「补测试缺口」的既定范围，留给后续 change。
    """
    pidfile = tmp_path / "pids-ignore-term"
    env, ctx = _make_env_runner_ignores_term(tmp_path, pidfile)
    rc, err, runner_pid, grandchild_pid = _run_until_killed(
        HELPER, env, ctx, signal.SIGTERM, tmp_path, pidfile, bash_bin
    )
    try:
        assert _alive(runner_pid) or _alive(grandchild_pid), (
            "残余 (d) 未复现：runner 忽略 TERM 时子树竟然被灭了 —— 若这是真的行为改进，"
            "须先证实（不同平台 timeout 语义可能不同），再回头把 design.md 的 (d) 条改成"
            "已解决，MUST NOT 只改这条断言"
        )
    finally:
        # 本用例故意验证的就是"会留下孤儿"——自己收拾干净，别污染开发机/CI
        for pid in (grandchild_pid, runner_pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass


def test_term_ignoring_residual_is_documented_in_design():
    """机械锁：design.md 的 D2 残余表 MUST 含第 (d) 条（runner 忽略 TERM 时子树存活），
    且全文 MUST NOT 出现越界断言——与 test_sigkill_residue_is_documented_not_claimed_solved
    同形（那条锁脚本注释，这条锁 design.md）。
    """
    design = (REPO / "openspec" / "changes" / "fix-mechanical-layer-silent-failures"
               / "design.md").read_text(encoding="utf-8")
    assert "(d)" in design, "design.md 的 D2 残余表未见第 (d) 条（runner 忽略 TERM 残余）"
    assert "忽略" in design and "TERM" in design, (
        "design.md 未见「runner 忽略 TERM」这条残余的具体描述"
    )
    for overclaim in ("已消除孤儿", "孤儿已消除", "已根治", "彻底解决", "完全避免孤儿"):
        assert overclaim not in design, f"design.md 越界断言（不得声称根治）: {overclaim}"


@needs_real_timeout
def test_cleanup_logs_the_terminated_runner_pid_without_context_body(tmp_path, bash_bin):
    """⭐ 清理路径在 stderr 留下可见痕迹（信号名 + 被终止的 PID），且不含 context 正文。

    「父被回收」必须在日志里看得见，而不是静默消失。同时 design 的可观测性约束：
    新增 stderr 内容 MUST NOT 含 context 正文（该内容未经出境扫描）。
    """
    pidfile = tmp_path / "pids-log"
    env, ctx = _make_env(tmp_path, pidfile)
    rc, err, _, _ = _run_until_killed(
        HELPER, env, ctx, signal.SIGTERM, tmp_path, pidfile, bash_bin
    )

    m = re.search(r"收到 TERM，终止 runner 子进程 PID=(\d+)", err)
    assert m, f"清理痕迹缺失，父被回收这件事静默消失了。stderr={err!r}"
    assert int(m.group(1)) > 0, err
    assert CONTEXT_PROBE not in err, f"stderr 泄漏 context 正文: {err!r}"
    assert "context body" not in err, f"stderr 泄漏 context 正文: {err!r}"


@needs_real_timeout
def test_mutation_no_op_cleanup_leaves_an_orphan(tmp_path, bash_bin):
    """⭐ 变异验证：把 kill 逻辑摘掉（还原成"只删 workdir"）⇒ 上面的验尸断言必须转红。

    没有这一条，「绿」可能只是因为测试环境恰好把整个进程组一起收了（例如信号发给了
    pgid 而非单个 PID），那样测试根本没在验 helper 自己的清理逻辑。
    """
    mutant = tmp_path / "outside-voice-mutant.sh"
    src = HELPER.read_text(encoding="utf-8")
    # 只摘掉 ov_cleanup 的杀子进程动作，保留删 workdir —— 精确还原「trap 里没有子 PID 可杀」的原病
    mutated = src.replace(
        'kill -TERM "$OV_RUNNER_PID" 2>/dev/null',
        ': # MUTANT: kill 摘除',
    ).replace(
        'kill -KILL "$OV_RUNNER_PID" 2>/dev/null',
        ': # MUTANT: kill 摘除',
    )
    assert mutated != src, "变异未生效 —— 源里的 kill 语句形态变了，本测试已失效，须同步更新"
    mutant.write_text(mutated, encoding="utf-8")
    mutant.chmod(0o755)

    pidfile = tmp_path / "pids-mutant"
    env, ctx = _make_env(tmp_path, pidfile)
    rc, err, runner_pid, grandchild_pid = _run_until_killed(
        mutant, env, ctx, signal.SIGTERM, tmp_path, pidfile, bash_bin
    )
    try:
        assert _alive(runner_pid) or _alive(grandchild_pid), (
            "变异体竟然也没留下孤儿 —— 说明验尸断言不是由 helper 的清理逻辑承重，测试不承重"
        )
    finally:
        # 变异体故意留下的孤儿：本测试自己收拾干净，别污染开发机
        for pid in (grandchild_pid, runner_pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass


# ── 退出码无回归 ────────────────────────────────────────────────────────────
#
# 后台 + wait 改造的最大风险是把 rc 弄丢/弄错（wait 的返回语义与前台不同）。
# helper 的对外契约：0=成功 · 124=超时 · 其他非零一律归一到 1。

def _fake_runner(tmp_path, body: str):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    fake = bin_dir / "codex"
    fake.write_text("#!/usr/bin/env bash\n" + textwrap.dedent(body))
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    ctx = tmp_path / "ctx.md"
    ctx.write_text("plain context\n", encoding="utf-8")
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["SDFLOW_VOICE_RUNNER"] = "codex"
    env.pop("SDFLOW_VOICE_MODEL", None)
    return env, ctx


def _exec(env, ctx, cwd, bash_bin, extra=()):
    return subprocess.run(
        [bash_bin, str(HELPER), "exec", "--context-file", str(ctx), *extra],
        capture_output=True, text=True, env=env, cwd=str(cwd), timeout=120,
    )


@needs_real_timeout
def test_exit_code_zero_passthrough_after_backgrounding(tmp_path, bash_bin):
    """成功路径：rc=0 + 最终消息原样出 stdout（后台化没把输出弄丢）。"""
    env, ctx = _fake_runner(tmp_path, """\
        out=""; prev=""
        for a in "$@"; do [ "$prev" = "--output-last-message" ] && out="$a"; prev="$a"; done
        cat >/dev/null
        printf 'FINDINGS_OK\\n' > "$out"
        exit 0
        """)
    r = _exec(env, ctx, tmp_path, bash_bin)
    assert r.returncode == 0, (r.returncode, r.stderr)
    assert "FINDINGS_OK" in r.stdout, r.stdout


@needs_real_timeout
def test_exit_code_124_timeout_passthrough_after_backgrounding(tmp_path, bash_bin):
    """⭐ 124 是【经 wait 透传】的：真 timeout 杀掉挂死 runner，helper 必须仍报 124。

    这条最容易被后台化改造弄坏——wait 对被信号杀死的作业返回 128+signum，
    而这里要的是 timeout 自己的退出码 124。
    """
    env, ctx = _fake_runner(tmp_path, "cat >/dev/null\nsleep 60\n")
    r = _exec(env, ctx, tmp_path, bash_bin, extra=["--timeout", "1"])
    assert r.returncode == 124, (r.returncode, r.stdout[:200], r.stderr[:400])


@needs_real_timeout
def test_other_nonzero_exit_code_still_maps_to_one(tmp_path, bash_bin):
    """其他非零码：契约是归一到 1（不是 7、也不是 128+n），且半成品按契约丢弃。

    假 runner 【写了】最终消息【又】非零退出 —— 走的是 helper 的「非零但已产出」分支。
    这么构造是为了让本用例承重：若 wait 的 rc 被改造弄丢（恒 0），helper 会把这份
    半成品当成功结果 cat 出去、exit 0 ⇒ 本用例当场红。
    （若 runner 什么都不写，rc 丢失后仍会因"输出为空"落到 exit 1，测试就测不出东西。）
    """
    env, ctx = _fake_runner(tmp_path, """\
        out=""; prev=""
        for a in "$@"; do [ "$prev" = "--output-last-message" ] && out="$a"; prev="$a"; done
        cat >/dev/null
        printf 'HALF_BAKED\\n' > "$out"
        echo 'runner boom' >&2
        exit 7
        """)
    r = _exec(env, ctx, tmp_path, bash_bin)
    assert r.returncode == 1, (r.returncode, r.stdout[:200], r.stderr[:400])
    assert "runner boom" in r.stderr, r.stderr
    assert "HALF_BAKED" not in r.stdout, f"半成品泄漏进 stdout: {r.stdout[:200]!r}"


# ── 诚实边界：SIGKILL 残余显式登记 ──────────────────────────────────────────

def test_sigkill_residue_is_documented_not_claimed_solved():
    """⭐ SIGKILL 残余 MUST 在实现里显式登记，且措辞 MUST NOT 声称孤儿已被根治。

    这是 design D2 的硬约束（adr/0018「不声称根治」）。机械守两件事：
      ① SIGKILL 残余在脚本注释里被点名，并说明 trap 在该信号下不执行；
      ② 全文不出现「孤儿已消除 / 已根治 / 彻底解决」这类越界断言。
    """
    src = HELPER.read_text(encoding="utf-8")
    assert "SIGKILL" in src, "SIGKILL 残余未在实现中登记"
    residue = [
        ln for ln in src.splitlines()
        if "SIGKILL" in ln and ("trap" in ln or "残余" in ln)
    ]
    assert residue, "SIGKILL 出现了，但没有说明它是 trap 够不着的已知残余"
    joined = "\n".join(src.splitlines())
    for overclaim in ("已消除孤儿", "孤儿已消除", "已根治", "彻底解决", "完全避免孤儿"):
        assert overclaim not in joined, f"越界断言（不得声称根治）: {overclaim}"
