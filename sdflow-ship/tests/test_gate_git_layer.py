"""[harden-gate-git-layer Task2 · tasks 3.1–3.6 / 5.8 / 5.9a-c] git 调用层：
环境级失败一律落在退出码契约集 `{0,3,4,5,6}` 内，且五类原因各给可行动诊断；
判定输入不受外部环境变量摆布（denylist 清理），非 `GIT_*` 变量原样透传。

口径：
- 退出码类断言经 CLI 公共入口（`main()` / 子进程跑脚本）求值。Compliance 对 5.9a–c 显式豁免
  「必须经 `is_stale`」（触发点可在其调用范围外，如仓根解析、D3 短路），但**不豁免公共入口**——
  故每类失败除三个 helper 各自的独立验证外，另有一条走 `main()` 的端到端用例。
- 「git 不可用」用**真实**手段构造（PATH 里没有 git / git 不可执行），不靠打桩；
  超时另有真实 fake-git 端到端用例（POSIX），跨平台的三组独立验证走注入。
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import commit_all, mkchange
from test_gate_impl_progress import approved_change, PLAN2, _sg

GATE = Path(__file__).resolve().parents[1] / "scripts" / "ship_gate.py"
CONTRACT_EXITS = {0, 3, 4, 5, 6}

# [fix1 M2] 起子进程的整片写法（非只 subprocess.run）——单出口守卫按此面数。
SPAWN_RE = re.compile(r"subprocess\.(?:run|Popen|call|check_call|check_output)\(|os\.system\(")

HELPERS = [
    ("run_git", lambda root: _sg.run_git(root, "rev-parse", "HEAD")),
    ("run_git_rc", lambda root: _sg.run_git_rc(root, "rev-parse", "HEAD")),
    ("run_git_bytes", lambda root: _sg.run_git_bytes(root, "cat-file", "-t", "HEAD")),
]


# ── 构造手段 ────────────────────────────────────────────────────────────

# ⚠ 三者都是**函数而非 fixture**：它们一旦生效，连 conftest 里建仓用的真 git 也没了
# ⇒ 盘面必须先建好、再让 git 消失。写成 fixture 会在 setup 阶段抢先生效（实测：
# `approved_change` 当场 FileNotFoundError，用例是红的但红在建仓、不在被测面）。

def _drop_git_from_path(tmp_path, monkeypatch):
    """PATH 指向一个没有 git 的空目录 ⇒ 子进程启动抛 FileNotFoundError（真实 OSError）。"""
    empty = tmp_path / "empty-bin"
    empty.mkdir(exist_ok=True)
    monkeypatch.setenv("PATH", str(empty))
    return empty


def _shadow_git_with_unexecutable(tmp_path, monkeypatch):
    """PATH 首位有一个存在但不可执行的 git ⇒ PermissionError（OSError 的另一子类）。"""
    binder = tmp_path / "bad-bin"
    binder.mkdir(exist_ok=True)
    (binder / "git").write_text("not executable\n", encoding="utf-8")
    (binder / "git").chmod(0o644)
    # PATH 只留这一处：POSIX 的 exec 搜索会**跳过不可执行项继续往后找**，
    # 追加在真 PATH 前面时找到的仍是真 git（实测），构造不出 PermissionError。
    monkeypatch.setenv("PATH", str(binder))
    return binder


def _shadow_git_with_sleeper(tmp_path, monkeypatch):
    """PATH 首位放一个恒睡眠的 fake git + 把上界压到 1s ⇒ 真实 TimeoutExpired。

    `sleep` 走绝对路径：fake git 的 PATH 里若只剩 shadow 目录，`sleep` 会 command-not-found
    而秒退 —— 用例照样「不抛异常」，但红的原因与被测面无关（已实测踩过）。
    """
    binder = tmp_path / "slow-bin"
    binder.mkdir(exist_ok=True)
    (binder / "git").write_text("#!/bin/sh\nexec /bin/sleep 20\n", encoding="utf-8")
    (binder / "git").chmod(0o755)
    monkeypatch.setenv("PATH", f"{binder}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setattr(_sg, "GIT_TIMEOUT_SECONDS", 1)
    return binder


def _inject_timeout(monkeypatch):
    def fake_run(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, kw.get("timeout"))
    monkeypatch.setattr(_sg.subprocess, "run", fake_run)


def run_gate_env(root, extra_env=None, change="demo", cwd=None):
    env = os.environ.copy()
    env.update(extra_env or {})
    argv = [sys.executable, str(GATE), "--change", change]
    if root is not None:
        argv += ["--root", str(root)]
    r = subprocess.run(argv, capture_output=True, text=True, env=env, cwd=cwd)
    lines = r.stdout.strip().splitlines()
    return r.returncode, (json.loads(lines[-1]) if lines else {}), r.stderr


# ── 5.9a：OSError × 三个 helper 各自验证 ────────────────────────────────

@pytest.mark.parametrize("name,call", HELPERS, ids=[h[0] for h in HELPERS])
def test_oserror_is_controlled_per_helper(repo, tmp_path, monkeypatch, name, call):
    _drop_git_from_path(tmp_path, monkeypatch)
    with pytest.raises(_sg.GateIndeterminate) as ei:
        call(repo)
    assert ei.value.category == _sg.CAUSE_GIT_UNAVAILABLE, f"{name} 未把 OSError 收敛为受控结果"


@pytest.mark.skipif(os.name != "posix", reason="chmod 权限位语义仅 POSIX 成立")
@pytest.mark.parametrize("name,call", HELPERS, ids=[h[0] for h in HELPERS])
def test_permission_error_is_controlled_per_helper(repo, tmp_path, monkeypatch, name, call):
    # OSError 不止 FileNotFoundError：git 存在但不可执行（权限不足）同样 MUST 受控。
    _shadow_git_with_unexecutable(tmp_path, monkeypatch)
    with pytest.raises(_sg.GateIndeterminate) as ei:
        call(repo)
    assert ei.value.category == _sg.CAUSE_GIT_UNAVAILABLE, f"{name} 未把 PermissionError 收敛"


# ── 5.9b：超时 × 三个 helper 各自验证 ──────────────────────────────────

@pytest.mark.parametrize("name,call", HELPERS, ids=[h[0] for h in HELPERS])
def test_timeout_is_controlled_per_helper(repo, monkeypatch, name, call):
    _inject_timeout(monkeypatch)
    with pytest.raises(_sg.GateIndeterminate) as ei:
        call(repo)
    assert ei.value.category == _sg.CAUSE_GIT_TIMEOUT, f"{name} 未把超时收敛为受控结果"


@pytest.mark.skipif(os.name != "posix", reason="fake git 用 sh 脚本，仅 POSIX")
@pytest.mark.parametrize("name,call", HELPERS, ids=[h[0] for h in HELPERS])
def test_real_hang_times_out_per_helper(repo, tmp_path, monkeypatch, name, call):
    # 不打桩的真实挂起：证明 timeout 参数确实传到了 subprocess（注入式用例证不了这一点）。
    _shadow_git_with_sleeper(tmp_path, monkeypatch)
    with pytest.raises(_sg.GateIndeterminate) as ei:
        call(repo)
    assert ei.value.category == _sg.CAUSE_GIT_TIMEOUT, f"{name} 无上界，会无限等待"


@pytest.mark.parametrize("name,call", HELPERS, ids=[h[0] for h in HELPERS])
def test_timeout_bound_is_the_shared_constant(repo, monkeypatch, name, call):
    # 上界 MUST 是同一个常量（三处各写各的字面量 = 必然漂移）。
    seen = {}
    real = _sg.subprocess.run

    def spy(cmd, **kw):
        seen["timeout"] = kw.get("timeout")
        return real(cmd, **kw)

    monkeypatch.setattr(_sg.subprocess, "run", spy)
    call(repo)
    # [fix1 M3] 只断言「用的是那个常量」，MUST NOT 把 30 再硬编码进来——那正是 T194 刚消灭的
    # 漂移同形（改常量即红，且报错文案「未使用统一上界」误导）。值本身另立一条断言。
    assert seen["timeout"] == _sg.GIT_TIMEOUT_SECONDS, f"{name} 未使用统一上界"


def test_shared_timeout_constant_value():
    # 上界的**值**另守一条：改动它是有意决策（须同步头注释的数量级论证），不该只在别处顺带变红。
    assert _sg.GIT_TIMEOUT_SECONDS == 30


# ── 5.9c：顶层入口映射 + 五类诊断可区分 ────────────────────────────────

def test_main_maps_git_unavailable_to_unknown(repo, tmp_path, monkeypatch, capsys):
    approved_change(repo, plan=PLAN2)      # 盘面先建好，再让 git 消失
    _drop_git_from_path(tmp_path, monkeypatch)
    with pytest.raises(SystemExit) as ex:
        _sg.main(["--change", "demo", "--root", str(repo)])
    assert ex.value.code == _sg.EXIT_UNKNOWN
    js = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert js["verdict"] == "UNKNOWN" and js["cause_category"] == "git-unavailable"
    assert "PATH" in js["reason"]


def test_main_maps_git_unavailable_during_repo_root_resolution(repo, tmp_path, capsys,
                                                               monkeypatch):
    # 仓根解析（`--root` 缺省 → `rev-parse --show-toplevel`）**本身是一次 git 调用**。
    # 它若落在 try 之外，最常见的失败（git 不在 PATH）会从第一行逸出成退出码 1，
    # 绕过为它准备的整套诊断——守卫写了但主路径够不着，是本仓有实证的假绿形态。
    approved_change(repo, plan=PLAN2)
    monkeypatch.chdir(repo)
    _drop_git_from_path(tmp_path, monkeypatch)
    with pytest.raises(SystemExit) as ex:
        _sg.main(["--change", "demo"])
    assert ex.value.code == _sg.EXIT_UNKNOWN
    js = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert js["cause_category"] == "git-unavailable"


def test_main_maps_timeout_to_unknown(repo, monkeypatch, capsys):
    approved_change(repo, plan=PLAN2)
    _inject_timeout(monkeypatch)
    with pytest.raises(SystemExit) as ex:
        _sg.main(["--change", "demo", "--root", str(repo)])
    assert ex.value.code == _sg.EXIT_UNKNOWN
    js = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert js["cause_category"] == "git-timeout"
    assert f">{_sg.GIT_TIMEOUT_SECONDS}s" in js["reason"], "超时诊断未给出上界数量级"


def test_exit_code_stays_in_contract_under_git_failures(repo, tmp_path):
    # 端到端（真跑脚本）：环境级失败 MUST NOT 逸出成 Python 默认退出码 1。
    approved_change(repo, plan=PLAN2)
    empty = tmp_path / "empty-bin"
    empty.mkdir(exist_ok=True)
    code, js, _err = run_gate_env(repo, {"PATH": str(empty)})
    assert code in CONTRACT_EXITS, f"退出码 {code} 逸出契约集"
    assert code == _sg.EXIT_UNKNOWN and js["cause_category"] == "git-unavailable"


def test_five_causes_give_distinguishable_advice():
    # 五类原因的补救动作完全不同 ⇒ MUST NOT 用一句「git 调用失败」打天下。
    cats = [_sg.CAUSE_GIT_UNAVAILABLE, _sg.CAUSE_GIT_TIMEOUT, _sg.CAUSE_ANCHOR_MISSING,
            _sg.CAUSE_ANCHOR_INVALID, _sg.CAUSE_ANCHOR_UNRESOLVABLE, _sg.CAUSE_READ_FAILED]
    reasons = {c: _sg._indeterminate_reason(_sg.GateIndeterminate("x", c)) for c in cats}
    assert len(set(reasons.values())) == len(cats), "存在两类原因给出同一句诊断"
    # 各自点名了各自的补救动作（不是同一句话换个词）
    assert "安装 git" in reasons[_sg.CAUSE_GIT_UNAVAILABLE]
    assert "文件系统" in reasons[_sg.CAUSE_GIT_TIMEOUT]
    assert "重跑对应评审补锚" in reasons[_sg.CAUSE_ANCHOR_MISSING]
    assert "40 位小写 hex" in reasons[_sg.CAUSE_ANCHOR_INVALID]
    assert "force-push" in reasons[_sg.CAUSE_ANCHOR_UNRESOLVABLE]
    assert "仓完整性" in reasons[_sg.CAUSE_READ_FAILED]


def test_timeout_advice_interpolates_the_constant():
    # [T194] 文案里的秒数 MUST 来自常量插值，MUST NOT 硬编码——否则改上界即产生漂移。
    src = GATE.read_text(encoding="utf-8")
    assert ">30s" not in src, "advice 里仍有硬编码的 >30s 字面量（T194 未消）"
    assert f">{_sg.GIT_TIMEOUT_SECONDS}s" in _sg._INDETERMINATE_ADVICE[_sg.CAUSE_GIT_TIMEOUT]


# ── 5.8：外部环境态中和（denylist）────────────────────────────────────

POLLUTED = {
    "GIT_ICASE_PATHSPECS": "1",          # 缺陷 8：pathspec 大小写不敏感 → 真实代码目录被误排除
    "GIT_DIR": "/nonexistent/poison.git",  # 指向别的仓 ⇒ 未清理时 -C 被架空
    "GIT_WORK_TREE": "/nonexistent/tree",
    "GIT_INDEX_FILE": "/nonexistent/index",
    "GIT_CONFIG_GLOBAL": "/nonexistent/gitconfig",
    "GIT_LITERAL_PATHSPECS": "1",
}


def _polluted_repo_config(repo):
    # 缺陷 7 的 config 半场：diff.ignoreSubmodules=all 与判定同片面。
    subprocess.run(["git", "-C", str(repo), "config", "diff.ignoreSubmodules", "all"],
                   check=True, capture_output=True)


@pytest.mark.parametrize("scenario", ["fresh", "stale"])
def test_verdict_is_identical_under_polluted_git_env(repo, scenario):
    d = approved_change(repo, plan=PLAN2)
    if scenario == "stale":
        (d / "design.md").write_text("# 拍板后偷改设计\n", encoding="utf-8")
        commit_all(repo, "docs: 改设计（未重审）")
    clean_code, clean_js, _ = run_gate_env(repo)
    _polluted_repo_config(repo)
    dirty_code, dirty_js, _ = run_gate_env(repo, POLLUTED)
    assert (dirty_code, dirty_js["verdict"]) == (clean_code, clean_js["verdict"]), \
        "判定结论被外部 git 环境变量 / 配置改变了"
    assert dirty_code in CONTRACT_EXITS


def test_git_prefixed_vars_are_stripped_from_subprocess_env(repo, monkeypatch):
    # 直接观测面：GIT_DIR 若未被剔除，`-C repo rev-parse --show-toplevel` 会被架空到别处
    # （或直接 fatal）。清理生效 ⇒ 仍解析出 repo 自己。
    monkeypatch.setenv("GIT_DIR", str(repo / "nonexistent.git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(repo / "nonexistent-tree"))
    out = _sg.run_git(repo, "rev-parse", "--show-toplevel")
    assert out and Path(out).resolve() == repo.resolve(), "GIT_* 未被剔除，判定输入被外部架空"


def test_non_git_prefixed_vars_pass_through(repo, monkeypatch):
    # denylist 的另一半（allowlist 会在此变红）：非 GIT_ 前缀变量 MUST 原样透传。
    # 探针取 PAGER —— git 读它决定 GIT_PAGER，是「环境变量真的到了子进程」的**行为级**
    # 证据，而非对 helper 内部实现的断言。
    # [fix1 F1] 旧探针用 XDG_CONFIG_HOME 指一份 global gitconfig 反证透传——那条探针本身
    # 就是 F1 的洞（它证明的正是「外部 global config 真被 git 读到」）。global config 已被
    # 本进程禁读，故改用一个**不经 config 面**的环境变量探针，透传口径不减。
    monkeypatch.setenv("PAGER", "pass-through-probe")
    rc, out = _sg.run_git_rc(repo, "var", "GIT_PAGER")
    assert (rc, out) == (0, "pass-through-probe"), "非 GIT_ 前缀环境变量未透传给子进程"


# ── [fix1 F1] 环境面另一半：global / system gitconfig MUST 不可改变判定 ────────

GBK_SUBJECT = "主题中文"


def _poison_global_gitconfig(tmp_path, monkeypatch=None):
    """把 HOME / XDG_CONFIG_HOME 指到一份被污染的 global gitconfig（非 GIT_ 前缀通道）。

    `i18n.logOutputEncoding=GBK` 会让 `git log --format=%s` 以 GBK 输出 subject，而 subject
    正是 `done_task_ids` 的判定输入；`log.showSignature` 同片面。返回可喂给子进程的 env 增量。
    """
    home = tmp_path / "poison-home"
    (home / "git").mkdir(parents=True, exist_ok=True)
    body = "[i18n]\n\tlogOutputEncoding = GBK\n[log]\n\tshowSignature = true\n"
    (home / ".gitconfig").write_text(body, encoding="utf-8")       # $HOME/.gitconfig
    (home / "git" / "config").write_text(body, encoding="utf-8")   # $XDG_CONFIG_HOME/git/config
    extra = {"HOME": str(home), "XDG_CONFIG_HOME": str(home)}
    if monkeypatch is not None:
        for k, v in extra.items():
            monkeypatch.setenv(k, v)
    return extra


def test_global_gitconfig_cannot_alter_judgment_input(repo, tmp_path, monkeypatch):
    # 判定输入级（评审方实测同形）：污染前后 subject MUST 逐字相同。
    # 未加固时实测为 `主题中文` → `����`（GBK 字节按 replace 解码）。
    commit_all(repo, GBK_SUBJECT)
    clean = _sg.run_git(repo, "log", "-1", "--format=%s")
    assert clean == GBK_SUBJECT, "前提不成立：干净环境下就没读到预期 subject"
    _poison_global_gitconfig(tmp_path, monkeypatch)
    assert _sg.run_git(repo, "log", "-1", "--format=%s") == GBK_SUBJECT, \
        "global gitconfig 翻转了判定输入（HOME/XDG 是非 GIT_ 前缀通道，denylist 拦不住）"


@pytest.mark.parametrize("scenario", ["fresh", "stale"])
def test_verdict_is_identical_under_polluted_global_config(repo, tmp_path, scenario):
    # 判定结论级（端到端跑脚本，含 HOME/XDG 经子进程 env 传入）：MUST 与干净环境一致。
    d = approved_change(repo, plan=PLAN2)
    if scenario == "stale":
        (d / "design.md").write_text("# 拍板后偷改设计\n", encoding="utf-8")
        commit_all(repo, "docs: 改设计（未重审）")
    clean_code, clean_js, _ = run_gate_env(repo)
    dirty_code, dirty_js, _ = run_gate_env(repo, _poison_global_gitconfig(tmp_path))
    assert (dirty_code, dirty_js["verdict"]) == (clean_code, clean_js["verdict"]), \
        "判定结论被外部 global gitconfig 改变了"
    assert dirty_code in CONTRACT_EXITS


def test_config_files_are_neutralized_in_child_env():
    # 口径守卫：两个禁读键 MUST 在**剔除之后**回填（先剔后填的顺序错了就等于没填）。
    env = _sg._git_env()
    assert env.get("GIT_CONFIG_GLOBAL") == os.devnull
    assert env.get("GIT_CONFIG_SYSTEM") == os.devnull


def test_env_is_a_denylist_not_an_allowlist(monkeypatch):
    # Windows 上 allowlist 会漏 SYSTEMROOT/COMSPEC 致子进程启动失败（本地 macOS 照不出），
    # 故在此机械守住口径：任意自定义键 MUST 在，且**只有** GIT_ 前缀键被剔除。
    monkeypatch.setenv("SDFLOW_PROBE", "kept")
    monkeypatch.setenv("GIT_PROBE", "dropped")
    # [fix1 F1] 外部传进来的 GIT_CONFIG_GLOBAL 同样 MUST 先被剔掉（再由本进程写死），
    # 否则「回填」会退化成「沿用外部值」——那正是本次要封的通道。
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/nonexistent/attacker.gitconfig")
    env = _sg._git_env()
    assert env.get("SDFLOW_PROBE") == "kept"
    assert "GIT_PROBE" not in env
    assert env["GIT_CONFIG_GLOBAL"] == os.devnull, "外部 GIT_CONFIG_GLOBAL 未被本进程覆盖"
    injected = {"GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM"}
    dropped = {k for k in os.environ if k not in env}
    assert dropped == {k for k in os.environ if k.startswith("GIT_")} - injected, \
        "剔除面不等于 GIT_ 前缀集（allowlist 化或漏剔）"


# ── 3.4：加固面单一出口 ────────────────────────────────────────────────

def test_all_git_calls_go_through_the_single_hardened_entry():
    # 加固（timeout + env 清理 + 失败映射）靠单出口保证；新增裸子进程调用点
    # = 一条没被加固的通路。允许出现的只有 `_git_run` 内那一处。
    # [fix1 M2] 只数 `subprocess.run(` 是点补：`Popen` / `call` / `check_output` / `os.system`
    # 同样能起子进程且同样绕过加固，面治 MUST 一次覆盖整片写法。
    src = GATE.read_text(encoding="utf-8")
    spawns = SPAWN_RE.findall(src)
    assert spawns == ["subprocess.run("], f"存在绕过 _git_run 的裸子进程调用点：{spawns}"
