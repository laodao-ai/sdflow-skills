"""FF-0 分支守卫 hook 的三分支判定（规则源 = workflow/ff-generation-constraints.md §FF-0）。

【为什么要有本文件】
FF-0 从「只挡 main/master」升成三分支判定后，**规则文本与 hook 实现是两处载体**——
文档改了、hook 没改，就是「人读到三分支、机器只挡两分支」的静默分叉。本文件把
hook 那一侧钉住；文档那一侧由 hack/tests/test_canonical_entry_sync.py 钉。

hook 契约：读 stdin 的 PreToolUse payload，deny 时往 stdout 打一份 JSON 决策；
放行时不打任何 JSON（exit 0）。故判据 = stdout 里有没有 `"permissionDecision": "deny"`。
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "assets" / "hooks" / "ff0-branch-guard.py"

# 人拍板「就地继续」的一次性哨兵（相对仓根）——与 hook 的 ACK_FILE 是同一个字面量。
ACK_REL = Path("openspec") / ".ff0-ack"


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True,
                   capture_output=True, text=True)


def ack(repo):
    """模拟人 `touch openspec/.ff0-ack`。"""
    (repo / ACK_REL).write_text("", encoding="utf-8")


def _make_repo(parent, name="proj"):
    """在 parent 下造一个最小 git 仓（停在 main）。名字可含空格 / shell 元字符。"""
    r = parent / name
    r.mkdir()
    (r / "openspec").mkdir()
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / "f.txt").write_text("x", encoding="utf-8")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "init")
    return r


@pytest.fixture
def repo(tmp_path):
    """一个最小 git 仓，默认停在 main 分支上。"""
    return _make_repo(tmp_path)


def hook_output(repo, command, tool="Bash"):
    """Run the public PreToolUse process seam and return its stdout JSON."""
    payload = {"tool_name": tool, "cwd": str(repo), "tool_input": {"command": command}}
    proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                          capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, f"hook 非零退出：{proc.stderr}"
    out = proc.stdout.strip()
    return json.loads(out) if out else {}


def run_hook(repo, command, tool="Bash"):
    """→ (denied: bool, reason: str)"""
    output = hook_output(repo, command, tool)
    if not output:
        return False, ""
    decision = output["hookSpecificOutput"]
    return decision["permissionDecision"] == "deny", decision["permissionDecisionReason"]


def assert_undecided_audit(output, reason_code):
    """The audit path is context-only: it must not make an allow/deny decision."""
    assert set(output) == {"hookSpecificOutput"}
    hook_result = output["hookSpecificOutput"]
    assert set(hook_result) == {"hookEventName", "additionalContext"}
    assert hook_result["hookEventName"] == "PreToolUse"
    assert reason_code in hook_result["additionalContext"]


# ── 分支①：保护分支 → deny ──────────────────────────────────────────────

def test_protected_branch_denies(repo):
    denied, reason = run_hook(repo, "openspec new change add-foo")
    assert denied
    assert "受保护分支" in reason


def test_compound_call_on_protected_branch_is_audited_without_decision(repo):
    assert_undecided_audit(
        hook_output(repo, "cd /tmp && openspec new change add-foo"),
        "cwd-ambiguous",
    )


# ── 分支②：已在 feat/{本 change} → 放行（真幂等）────────────────────────

def test_same_change_branch_allows(repo):
    _git(repo, "checkout", "-qb", "feat/add-foo")
    denied, _ = run_hook(repo, "openspec new change add-foo")
    assert not denied


@pytest.mark.parametrize("cmd", [
    "openspec new change 'add-foo'",
    'openspec new change "add-foo"',
    "openspec   new   change   add-foo --json",
    "\topenspec\tchange\tnew\t'add-foo'\t",
    'openspec change new --json "add-foo"',
])
def test_same_change_branch_allows_quoting_variants(repo, cmd):
    _git(repo, "checkout", "-qb", "feat/add-foo")
    denied, _ = run_hook(repo, cmd)
    assert not denied


# ── 分支③：其它 feature 分支 → deny（这一支是本次新增的，旧实现放行）──

def test_other_feature_branch_denies(repo):
    _git(repo, "checkout", "-qb", "feat/add-bar")
    denied, reason = run_hook(repo, "openspec new change add-foo")
    assert denied, "在别的 change 的 feature 分支上建新 change 必须 halt 问人（FF-0 三分支判定）"
    assert "add-bar" in reason and "add-foo" in reason
    # 逃生口要给出**可直接复制的那条命令**（人零思考成本），且带绝对路径（cwd 可能在子目录）
    assert f"touch {repo / ACK_REL}" in reason


def test_sentinel_allows_on_other_feature_branch(repo):
    """人 `touch` 了哨兵 ⇒ 分支③放行。"""
    _git(repo, "checkout", "-qb", "feat/add-bar")
    ack(repo)
    denied, _ = run_hook(repo, "openspec new change add-foo")
    assert not denied


def test_sentinel_is_one_shot(repo):
    """令牌用后即焚：放行一次后哨兵被删，第二次照常 deny。"""
    _git(repo, "checkout", "-qb", "feat/add-bar")
    ack(repo)
    denied, _ = run_hook(repo, "openspec new change add-foo")
    assert not denied
    assert not (repo / ACK_REL).exists(), "哨兵未被消费 ⇒ 令牌成了永久后门"
    denied, _ = run_hook(repo, "openspec new change add-foo")
    assert denied, "同一个哨兵放行了第二次"


def test_escape_hatch_command_in_deny_reason_is_itself_allowed(repo):
    """deny 文案给的逃生口命令 MUST NOT 被本 hook 自己 deny —— 否则唯一合规出路是死循环。

    PreToolUse 在命令**执行前**判定：写成一条 `touch <token> && openspec new change X`
    时，判定发生在 touch 之前 ⇒ 哨兵还不存在 ⇒ 本 hook 把这条命令连同 touch 一起 deny。
    故文案必须把逃生口拆成**两步**，且第一步（单独 touch）本身可放行。
    """
    _git(repo, "checkout", "-qb", "feat/add-bar")
    _, reason = run_hook(repo, "openspec new change add-foo")
    hatch = [ln.strip() for ln in reason.splitlines() if ln.strip().startswith("touch ")]
    assert hatch, "deny 文案里没有一条可直接复制的 touch 命令"
    for cmd in hatch:
        denied, _ = run_hook(repo, cmd)
        assert not denied, \
            f"deny 文案给出的逃生口命令本身会被本 hook deny（死循环）：{cmd!r}"


def test_two_step_escape_hatch_runs_end_to_end(repo):
    """真实跑一遍人的两步序列：① 单独 touch 放行 → ② 重跑放行 → ③ 同令牌再跑 deny。"""
    _git(repo, "checkout", "-qb", "feat/add-bar")
    _, reason = run_hook(repo, "openspec new change add-foo")
    touch_cmd = next(ln.strip() for ln in reason.splitlines()
                     if ln.strip().startswith("touch "))

    # ① 第一步：人敲 touch —— 不被拦
    denied, _ = run_hook(repo, touch_cmd)
    assert not denied, "第一步 touch 被 deny ⇒ 逃生口不可用"
    subprocess.run(touch_cmd, shell=True, check=True, cwd=repo)
    assert (repo / ACK_REL).exists(), f"文案给的 touch 命令没造出哨兵：{touch_cmd!r}"

    # ② 第二步：重跑创建命令 → 放行
    denied, _ = run_hook(repo, "openspec new change add-foo")
    assert not denied, "两步序列的第二步仍被 deny"

    # ③ 令牌用后即焚
    denied, _ = run_hook(repo, "openspec new change add-foo")
    assert denied


def test_stale_sentinel_expires_and_is_swept(repo):
    """残留令牌有**有界时效**：超窗即失效，且被顺手删除（不留常驻绕过口）。

    残留是真实场景：人若在自己的终端里敲 `openspec new change`（本 hook 根本不触发），
    哨兵永不被消费 —— 若无时效，它就是下一次任意分支③调用的静默放行口。
    """
    _git(repo, "checkout", "-qb", "feat/add-bar")
    ack(repo)
    stale = time.time() - 3600
    os.utime(repo / ACK_REL, (stale, stale))
    denied, _ = run_hook(repo, "openspec new change add-foo")
    assert denied, "过期哨兵仍然放行 —— 残留令牌成了常驻绕过口"
    assert not (repo / ACK_REL).exists(), \
        "过期哨兵未被顺手清掉 —— 它会一直留在盘上（且可能被 git add -A 提交入库）"


@pytest.mark.parametrize("skew_seconds, label", [
    (300, "略超窗（时钟回拨 5 分钟）"),
    (365 * 24 * 3600, "远未来（从备份恢复保留 mtime）"),
])
def test_future_mtime_sentinel_expires_and_is_swept(repo, skew_seconds, label):
    """**未来** mtime MUST NOT 恒新鲜 —— 时效判据必须是双边的。

    `(now - mtime) <= TTL` 是单边的：mtime 落在未来时该式恒真 ⇒ 哨兵永不过期，
    「10 分钟窗口」退回常驻后门。命中场景真实存在且不需要恶意：系统时钟回拨、
    从备份/归档恢复保留原 mtime、跨机器 rsync -t 带回一个更快的钟。
    判据 = `0 <= (now - mtime) <= TTL`。
    """
    _git(repo, "checkout", "-qb", "feat/add-bar")
    ack(repo)
    future = time.time() + skew_seconds
    os.utime(repo / ACK_REL, (future, future))
    denied, _ = run_hook(repo, "openspec new change add-foo")
    assert denied, f"未来 mtime（{label}）的哨兵仍然放行 —— 时效是单边比较，窗口形同虚设"
    assert not (repo / ACK_REL).exists(), \
        f"未来 mtime（{label}）的哨兵未被顺手清掉 —— 它会一直留在盘上放行每一次调用"


def test_sentinel_found_from_repo_subdirectory(repo):
    """人可能在子目录里跑命令 —— 哨兵锚仓根，不锚 cwd。"""
    _git(repo, "checkout", "-qb", "feat/add-bar")
    ack(repo)
    sub = repo / "openspec" / "changes"
    sub.mkdir(parents=True)
    denied, _ = run_hook(sub, "openspec new change add-foo")
    assert not denied


def test_undeletable_sentinel_does_not_allow(repo):
    """放行 ⇔ 成功消费。删不掉（此处：它是个目录）就不放行 —— 否则它不再是一次性的。"""
    _git(repo, "checkout", "-qb", "feat/add-bar")
    (repo / ACK_REL).mkdir()
    denied, _ = run_hook(repo, "openspec new change add-foo")
    assert denied


def test_mentioning_the_ack_in_non_direct_commands_is_audited_not_acked(repo):
    """逃生口 MUST NOT 从命令串里认 —— 命令串是无界的 shell 语法面（基准 5）。

    deny 文案把逃生口原样回传给模型 ⇒ 只要判据落在命令串上，模型顺手把它写进
    一句注释/说明就绕过，且「注释算不算」需要真解析 shell，补丁循环不收敛。
    哨兵文件把判据挪到**有界**的语义面（文件在不在），下列各式一律不是 ack。
    """
    _git(repo, "checkout", "-qb", "feat/add-bar")
    for cmd in (
        f"openspec new change add-foo # 人已 ack: touch {ACK_REL}",
        f"# 人已 ack: touch {ACK_REL}\nopenspec new change add-foo",
        f"echo '{ACK_REL}' && openspec new change add-foo",
        "SDFLOW_FF0_ACK=1 openspec new change add-foo",
        "openspec new change add-foo # note: SDFLOW_FF0_ACK=1 was discussed",
    ):
        assert_undecided_audit(hook_output(repo, cmd), "cwd-ambiguous")


# ── detached HEAD：不是分支，更不是「其它 feature 分支」→ fail-open ──────

def test_detached_head_fails_open(repo):
    """`git rev-parse --abbrev-ref HEAD` 在 detached HEAD 下返回字面量 `HEAD`。

    它非空、且不在受保护集里 ⇒ 若不特判就会落进分支③，提示「当前在 feature
    分支 `HEAD`」—— 一个不存在的分支。worktree / bisect / tag checkout 全命中。
    按本 hook 的 fail-open 纪律（探测不出可判定的分支就不挡人干活）应放行。
    """
    _git(repo, "checkout", "-qb", "feat/add-bar")
    _git(repo, "checkout", "-q", "--detach")
    denied, reason = run_hook(repo, "openspec new change add-foo")
    assert not denied, f"detached HEAD 被误判成 feature 分支并 deny：{reason}"


# ── 分支①的边界：受保护集 MUST 含【该仓真正的默认分支】，不止 main/master ──
#    misclassify 即等于开后门：分支①无逃生口、分支③有 ack。

def _set_origin_head(repo, branch):
    """本地伪造 `refs/remotes/origin/HEAD`（clone 时 git 自己写的就是它）。"""
    _git(repo, "symbolic-ref", "refs/remotes/origin/HEAD",
         f"refs/remotes/origin/{branch}")


def test_default_branch_from_origin_head_is_protected(repo):
    _git(repo, "checkout", "-qb", "trunk")
    _set_origin_head(repo, "trunk")
    denied, reason = run_hook(repo, "openspec new change add-foo")
    assert denied, "默认分支为 trunk 的仓里，trunk 就是分支①，必须 deny"
    assert "受保护分支" in reason


def test_default_branch_is_protected_even_with_human_ack(repo):
    """ack 是【分支③】的逃生口。它若在分支①也生效，FF-0 的核心不变量就被击穿。"""
    _git(repo, "checkout", "-qb", "trunk")
    _set_origin_head(repo, "trunk")
    ack(repo)
    denied, _ = run_hook(repo, "openspec new change add-foo")
    assert denied, "ack MUST NOT 让「在默认分支上建 change」放行"
    assert (repo / ACK_REL).exists(), \
        "分支①不该消费哨兵 —— 静默吃掉人的令牌会让下一次分支③的 ack 莫名失效"


def test_default_branch_from_init_default_branch_config_is_protected(repo):
    """本地 `git init` 出来的仓没有 origin/HEAD —— 退到 init.defaultBranch。"""
    _git(repo, "config", "init.defaultBranch", "develop")
    _git(repo, "checkout", "-qb", "develop")
    denied, reason = run_hook(repo, "openspec new change add-foo")
    assert denied and "受保护分支" in reason


def test_feature_branch_still_denies_when_default_branch_is_unusual(repo):
    """默认分支探测不改变分支③的判定（回归保护）。"""
    _git(repo, "checkout", "-qb", "trunk")
    _set_origin_head(repo, "trunk")
    _git(repo, "checkout", "-qb", "feat/add-bar")
    denied, reason = run_hook(repo, "openspec new change add-foo")
    assert denied and "feature 分支" in reason


# ── fail-open：守卫拿不准时不挡人干活 ───────────────────────────────────

def test_unparseable_change_name_is_audited_without_decision(repo):
    """取不到 change 名时 fail-open，但必须留下稳定审计原因。"""
    _git(repo, "checkout", "-qb", "feat/add-bar")
    assert_undecided_audit(
        hook_output(repo, 'openspec new change "$NAME"'),
        "change-name-unparseable",
    )


@pytest.mark.parametrize("cmd", [
    "openspec new change",
    "openspec new change --json",
    "openspec new change $NAME",
    "openspec new change $(printf add-foo)",
    "openspec new change `printf add-foo`",
    "openspec new change add-*",
    "openspec new change add-?",
    "openspec new change add-[ab]",
])
def test_dynamic_change_names_are_audited_without_expansion(repo, cmd):
    _git(repo, "checkout", "-qb", "feat/add-bar")
    assert_undecided_audit(hook_output(repo, cmd), "change-name-unparseable")


@pytest.mark.parametrize("name", [
    "--help",
    "-h",
    "Foo",
    "foo_bar",
    "foo.bar",
    "1foo",
    "foo-",
    "foo--bar",
])
def test_invalid_openspec_change_names_are_unparseable(repo, name):
    """Only OpenSpec's lowercase kebab-case change-name grammar is literal."""
    assert_undecided_audit(
        hook_output(repo, f"openspec new change {name}"),
        "change-name-unparseable",
    )


@pytest.mark.parametrize("cmd", [
    'openspec new change "add-"$NAME',
    'openspec new change "add"$NAME',
    "openspec new change 'add-'$(printf foo)",
    'openspec new change "add-"*',
])
def test_quoted_literal_prefix_with_dynamic_suffix_is_unparseable(repo, cmd):
    assert_undecided_audit(hook_output(repo, cmd), "change-name-unparseable")


@pytest.mark.parametrize("cmd", [
    "cd /tmp && openspec new change add-foo",
    "pushd /tmp; openspec new change add-foo",
    "env -C /tmp openspec new change add-foo",
    "bash -lc 'openspec new change add-foo'",
    "sudo openspec new change add-foo",
    "openspec new change add-foo && git status",
    "openspec new change add-foo\ngit status",
    "please run openspec new change add-foo",
    "echo openspec new change add-foo",
])
def test_non_direct_literal_forms_are_cwd_ambiguous(repo, cmd):
    assert_undecided_audit(hook_output(repo, cmd), "cwd-ambiguous")


def test_unrelated_command_passes_through(repo):
    denied, _ = run_hook(repo, "ls -la")
    assert not denied


def test_non_bash_tool_passes_through(repo):
    denied, _ = run_hook(repo, "openspec new change add-foo", tool="Read")
    assert not denied


def test_outside_git_repo_fails_open(tmp_path):
    denied, _ = run_hook(tmp_path, "openspec new change add-foo")
    assert not denied


# ── 多次创建调用：只看**第一个**匹配 = 前置文本可绕过 [impl-review-fix] ──────

def test_second_creation_call_behind_a_decoy_is_denied(repo):
    """🔴 复现（代码审 F2）：只 `search()` 第一个匹配 ⇒ 前置一段文本即绕过。

    payload 在 `feat/add-sdflow-spec` 上跑：第一处匹配是 `echo` 后面那段（名字 = 当前
    change ⇒ 判成分支②幂等放行），而 Bash 真正会执行的第二条创建的是**另一个** change。
    实测旧实现：无 deny 输出、exit 0，第二个 change 直接落在本 change 的分支上（stacking）。
    修法**不是**解析 shell（无界面，基准 5）——只是把「取第一个匹配」改成「枚举全部有界
    匹配并要求一致」，判据仍是同一条有界正则。
    """
    _git(repo, "checkout", "-qb", "feat/add-sdflow-spec")
    denied, reason = run_hook(
        repo,
        "echo openspec new change add-sdflow-spec; openspec new change unrelated-change",
    )
    assert denied, "前置诱饵让第二条创建命令静默放行 —— FF-0 三分支判定被绕过"
    assert "unrelated-change" in reason


@pytest.mark.parametrize("cmd", [
    "openspec new change add-foo && openspec new change add-bar",
    "openspec new change add-bar; openspec new change add-foo",
    "openspec new change 'add-foo' | tee /dev/null; openspec new change \"add-bar\"",
])
def test_multiple_distinct_change_names_are_denied(repo, cmd):
    """一条命令里出现**多个不同** change 名 ⇒ 直接 deny 并要求拆成独立调用。

    连当前分支就叫 `feat/add-foo` 的幂等形态也不放行：放行判据是「**全部**匹配都等于
    当前 change」，只要还有第二个名字，这一次调用就不是幂等的。
    """
    _git(repo, "checkout", "-qb", "feat/add-foo")
    denied, reason = run_hook(repo, cmd)
    assert denied, f"多个 change 名居然放行：{cmd!r}"
    assert "拆" in reason


def test_repeated_identical_change_names_are_stacking_denied(repo):
    """多处创建调用必须拆开，即使名字一致也不例外。"""
    _git(repo, "checkout", "-qb", "feat/add-foo")
    denied, reason = run_hook(repo, "openspec new change add-foo || openspec new change add-foo")
    assert denied
    assert "stacking" in reason


def test_stacking_deny_precedes_cwd_ambiguity(repo):
    output = hook_output(
        repo,
        "cd /tmp && openspec new change add-foo; openspec change new add-bar",
    )
    decision = output["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    assert "stacking" in decision["permissionDecisionReason"]
    assert "additionalContext" not in decision


def test_multiple_calls_with_an_unreadable_name_are_denied(repo):
    """多处创建调用但只读得出一部分名字 ⇒ deny（**单次**调用认不出仍 fail-open）。

    `$(...)`/变量展开的那一处压根匹配不上有界正则 ⇒ 若沿用「只看读得出的那些」，
    读不出的那一条就是一个与 F2 同形的绕过口。判据是**两个有界计数**之差，
    MUST NOT 演化成解析 shell。
    """
    _git(repo, "checkout", "-qb", "feat/add-foo")
    denied, reason = run_hook(
        repo, "openspec new change add-foo; openspec new change $(cat /tmp/n)")
    assert denied, "读不出名字的第二条创建调用被静默放行"
    assert "拆" in reason


# ── deny 文案里的 touch 命令必须经 shell quoting [impl-review-fix] ───────────

@pytest.mark.parametrize("dirname", [
    "pro j",                       # 空格：不 quote 时 touch 会造出两个错文件
    "pro;j $(id) &x",              # shell 元字符：复制执行还会**额外产生命令**
])
def test_escape_hatch_command_is_shell_quoted(tmp_path, dirname):
    """🔴 复现（代码审 F7）：仓库路径含空格/元字符时，deny 文案给的 `touch` 不可用。

    端到端跑一遍人的动作：把文案里那条 touch 原样丢给 shell，必须**恰好**造出哨兵，
    且哨兵随后真的能放行一次。旧实现（裸 f-string 拼路径）在这两种路径下：
    空格 ⇒ 造出两个错文件、哨兵不存在；元字符 ⇒ `$(id)` 被展开、`&` 起后台命令。
    """
    repo = _make_repo(tmp_path, dirname)
    _git(repo, "checkout", "-qb", "feat/add-bar")
    _, reason = run_hook(repo, "openspec new change add-foo")
    touch_cmd = next(ln.strip() for ln in reason.splitlines()
                     if ln.strip().startswith("touch "))

    before = set(os.listdir(repo / "openspec"))
    subprocess.run(touch_cmd, shell=True, check=True, cwd=str(repo), timeout=30)
    assert (repo / ACK_REL).is_file(), \
        f"文案给的 touch 命令没造出哨兵（路径未经 quoting）：{touch_cmd!r}"
    assert set(os.listdir(repo / "openspec")) - before == {".ff0-ack"}, \
        f"touch 命令造出了预期之外的文件（路径被 shell 拆词）：{touch_cmd!r}"

    denied, _ = run_hook(repo, "openspec new change add-foo")
    assert not denied, "哨兵造出来了却没放行"
