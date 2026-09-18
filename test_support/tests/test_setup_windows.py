"""Windows Git Bash integration coverage for the real setup.sh installer."""

import os
import subprocess
import shutil
import shlex
from pathlib import Path

import pytest

from test_support.windows import bash_executable, bash_path


REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def farm(tmp_path):
    """Run the entire installer against a tiny committed source and isolated HOME."""
    repo = tmp_path / "source"
    repo.mkdir()
    shutil.copy2(REPO / "setup.sh", repo / "setup.sh")
    (repo / "hack").mkdir()
    shutil.copy2(REPO / "hack" / "setup-dependencies.sh", repo / "hack" / "setup-dependencies.sh")
    for script in ("check_async_branch_parity.py", "check_tier_resolution_parity.py"):
        (repo / "hack" / script).write_text("# unrelated preflight fixture\n", encoding="utf-8")
    for name in ("alpha", "beta"):
        (repo / name).mkdir()
        (repo / name / "SKILL.md").write_text("original\n", encoding="utf-8")
    def git(*args):
        return subprocess.check_output(
            ["git", "-C", str(repo), *args], text=True,
            encoding="utf-8", errors="replace",
        ).strip()
    git("init", "-q")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.invalid")
    git("add", ".")
    git("commit", "-qm", "initial")
    home = tmp_path / "home"
    home.mkdir()
    def run(prefix=""):
        command = prefix + "\nexec bash " + shlex.quote(bash_path(repo / "setup.sh"))
        result = subprocess.run(
            [bash_executable(), "-c", command], cwd=repo,
            env=dict(os.environ, HOME=bash_path(home), USERPROFILE=str(home),
                     CLAUDE_CONFIG_DIR=str(home / ".claude"),
                     SDFLOW_HOME=bash_path(home / ".sdflow")),
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout
    return repo, home, git, run


@pytest.mark.skipif(os.name != "nt", reason="Windows copy installer coverage")
def test_incremental_commits_and_dirty_revert(farm):
    repo, home, git, run = farm
    run()
    alpha = home / ".codex/skills/alpha"
    beta = home / ".codex/skills/beta"
    # A local sentinel proves an unchanged target was not deleted/copied.
    (beta / "sentinel").write_text("keep")
    assert "unchanged (4)" in run()
    (repo / "alpha/SKILL.md").write_text("committed\n")
    git("add", ".")
    git("commit", "-qm", "alpha only")
    assert "unchanged (2)" in run()
    assert (beta / "sentinel").exists()
    assert (beta / ".sdflow-skills").read_text().strip() == git("rev-parse", "HEAD")
    (repo / "alpha/extra").write_text("dirty")
    run()
    assert (alpha / "extra").exists()
    assert (alpha / ".sdflow-skills").read_text().strip() == "unknown"
    (repo / "alpha/extra").unlink()
    run()
    assert not (alpha / "extra").exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows copy installer coverage")
@pytest.mark.parametrize("failure", ["copy", "marker", "swap", "rollback"])
def test_failed_replacement_and_recovery(farm, failure):
    repo, home, git, run = farm
    run()
    target = home / ".codex/skills/alpha"
    (repo / "alpha/SKILL.md").write_text("new\n")
    if failure == "marker":
        prefix = 'cp() { command cp "$@" || return; case "$*" in *alpha*/stage*) mkdir "${@: -1}/.sdflow-skills";; esac; }; export -f cp'
    elif failure == "copy":
        prefix = 'cp() { case "$*" in *alpha*/stage*) return 1;; esac; command cp "$@"; }; export -f cp'
    else:
        extra = '|*/backup' if failure == "rollback" else ''
        # Match the source, not the backup destination of the first rename.
        prefix = 'mv() { case "$2" in */stage' + extra + ') return 1;; esac; command mv "$@"; }; export -f mv'
    output = run(prefix)
    assert "skipped" in output
    if failure == "rollback":
        assert not target.exists()
        assert list(target.parent.glob(".sdflow-skills-alpha.*/backup/SKILL.md"))
    else:
        assert (target / "SKILL.md").read_text() == "original\n"
    run()
    assert (target / "SKILL.md").read_text() == "new\n"
    assert not list(target.parent.glob(".sdflow-skills-alpha.*"))


@pytest.mark.skipif(os.name != "nt", reason="Windows copy installer coverage")
def test_recovery_does_not_claim_foreign_transaction(farm):
    repo, home, git, run = farm
    transaction = home / ".codex/skills/.sdflow-skills-alpha.foreign"
    backup = transaction / "backup"
    backup.mkdir(parents=True)
    (transaction / "owner").write_text("alpha\n")
    (backup / "SKILL.md").write_text("foreign\n")
    # A matching transaction name and owner do not replace marker ownership.
    run()
    assert (backup / "SKILL.md").read_text() == "foreign\n"
    assert (home / ".codex/skills/alpha/SKILL.md").read_text() == "original\n"


def run_setup(tmp_path):
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = dict(os.environ, HOME=bash_path(home), USERPROFILE=str(home),
               CLAUDE_CONFIG_DIR=str(home / ".claude"),
               SDFLOW_HOME=bash_path(home / ".sdflow"))
    return subprocess.run(
        [bash_executable(), bash_path(REPO / "setup.sh")],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        encoding="utf-8",
        errors="replace",
    ), home


@pytest.mark.skipif(os.name != "nt", reason="Windows copy installer coverage")
def test_second_setup_skips_unchanged_owned_skills(tmp_path):
    first, home = run_setup(tmp_path)
    assert first.returncode == 0, first.stdout + first.stderr
    installed = home / ".codex" / "skills" / "sdflow-init"
    assert (installed / "SKILL.md").is_file()
    assert (installed / ".sdflow-skills").is_file()
    resolver = home / ".sdflow/hack/resolve-models.sh"
    assert resolver.read_bytes() == (REPO / "sdflow-init/assets/hack/resolve-models.sh").read_bytes()

    second, _ = run_setup(tmp_path)
    assert second.returncode == 0, second.stdout + second.stderr
    assert "unchanged" in second.stdout.lower()


@pytest.mark.skipif(os.name != "nt", reason="Windows copy installer coverage")
def test_setup_keeps_foreign_same_name_directory(tmp_path):
    home = tmp_path / "home"
    foreign = home / ".codex" / "skills" / "sdflow-init"
    foreign.mkdir(parents=True)
    (foreign / "foreign.txt").write_text("keep me", encoding="utf-8")

    result, _ = run_setup(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (foreign / "foreign.txt").read_text(encoding="utf-8") == "keep me"
    assert not (foreign / ".sdflow-skills").exists()
