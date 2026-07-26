"""FF-0 分支守卫 hook 的三分支判定（规则源 = workflow/ff-generation-constraints.md §FF-0）。

【为什么要有本文件】
FF-0 从「只挡 main/master」升成三分支判定后，**规则文本与 hook 实现是两处载体**——
文档改了、hook 没改，就是「人读到三分支、机器只挡两分支」的静默分叉。本文件把
hook 那一侧钉住；文档那一侧由 hack/tests/test_canonical_entry_sync.py 钉。

hook 契约：读 stdin 的 PreToolUse payload，deny 时往 stdout 打一份 JSON 决策；
放行时不打任何 JSON（exit 0）。故判据 = stdout 里有没有 `"permissionDecision": "deny"`。
"""
import json
import subprocess
import sys
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


@pytest.fixture
def repo(tmp_path):
    """一个最小 git 仓，默认停在 main 分支上。"""
    r = tmp_path / "proj"
    r.mkdir()
    (r / "openspec").mkdir()
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / "f.txt").write_text("x", encoding="utf-8")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "init")
    return r


def run_hook(repo, command, tool="Bash"):
    """→ (denied: bool, reason: str)"""
    payload = {"tool_name": tool, "cwd": str(repo), "tool_input": {"command": command}}
    proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                          capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, f"hook 非零退出：{proc.stderr}"
    out = proc.stdout.strip()
    if not out:
        return False, ""
    decision = json.loads(out)["hookSpecificOutput"]
    return decision["permissionDecision"] == "deny", decision["permissionDecisionReason"]


# ── 分支①：保护分支 → deny ──────────────────────────────────────────────

def test_protected_branch_denies(repo):
    denied, reason = run_hook(repo, "openspec new change add-foo")
    assert denied
    assert "受保护分支" in reason


# ── 分支②：已在 feat/{本 change} → 放行（真幂等）────────────────────────

def test_same_change_branch_allows(repo):
    _git(repo, "checkout", "-qb", "feat/add-foo")
    denied, _ = run_hook(repo, "openspec new change add-foo")
    assert not denied


@pytest.mark.parametrize("cmd", [
    "openspec new change 'add-foo'",
    'openspec new change "add-foo"',
    "openspec   new   change   add-foo --json",
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


def test_mentioning_the_ack_in_the_command_string_is_not_an_ack(repo):
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
        denied, _ = run_hook(repo, cmd)
        assert denied, f"命令串里提到逃生口不是 ack，不该放行：{cmd!r}"


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

def test_unparseable_change_name_fails_open(repo):
    """取不到 change 名 ⇒ 无从区分②③ ⇒ 放行（基准 5：不猜无界的 shell 语法）。"""
    _git(repo, "checkout", "-qb", "feat/add-bar")
    denied, _ = run_hook(repo, 'openspec new change "$NAME"')
    assert not denied


def test_unrelated_command_passes_through(repo):
    denied, _ = run_hook(repo, "ls -la")
    assert not denied


def test_non_bash_tool_passes_through(repo):
    denied, _ = run_hook(repo, "openspec new change add-foo", tool="Read")
    assert not denied


def test_outside_git_repo_fails_open(tmp_path):
    denied, _ = run_hook(tmp_path, "openspec new change add-foo")
    assert not denied
