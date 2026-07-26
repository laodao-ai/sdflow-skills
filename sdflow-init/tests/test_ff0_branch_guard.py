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


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True,
                   capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    """一个最小 git 仓，默认停在 main 分支上。"""
    r = tmp_path / "proj"
    r.mkdir()
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
    assert "SDFLOW_FF0_ACK=1" in reason  # 人拍板「就地继续」的逃生口要写在提示里


def test_other_feature_branch_with_human_ack_allows(repo):
    _git(repo, "checkout", "-qb", "feat/add-bar")
    denied, _ = run_hook(repo, "SDFLOW_FF0_ACK=1 openspec new change add-foo")
    assert not denied


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
