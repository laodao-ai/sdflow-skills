"""token-log.jsonl 快照采集契约（implement-workflow-optimization-2026-08-p1 · Task 3）。

真相源：`sdflow-init/assets/hack/token_snapshot.py` + 同目录 `checkpoint-commit.sh` 的接线
（`git status --porcelain` 判空 gate 之后、`git add -A` 之前）。见
`openspec/changes/implement-workflow-optimization-2026-08-p1/specs/token-snapshot-anchor/spec.md`。

【怎么跑】假 HOME（`tmp_path`）+ 假 repo 真跑 `bash checkpoint-commit.sh`：
- `~/.sdflow/hack/token_snapshot.py` 用软链指向本仓源文件，模拟 setup.sh 的部署形态
  （Unix 场景，符合 CLAUDE.md「hack/ 是拷贝非软链」的分发口径——测试用软链只是为了不用真跑
  setup.sh 就能验证部署后的调用路径，效果等价）。
- `~/.claude/projects/<munged-cwd>/<session>.jsonl` 手写伪造 transcript 行（不依赖真实会话）。
- change 目录用 `git init` 出的假 repo 里 `openspec/changes/<change>/` 手建。

不跑真实 `setup.sh`（机械层，零全局影响）——见 CLAUDE.md「开发期测试三层」第 1 层。
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

from test_support.windows import bash_executable, bash_path

if os.name == "nt":
    pytest.skip(
        "checkpoint-commit.sh / token_snapshot.py 铺设范围不含 Windows（CLAUDE.md：hack/ 不铺）",
        allow_module_level=True,
    )

REPO = Path(__file__).resolve().parents[2]
CHECKPOINT_SCRIPT = REPO / "sdflow-init" / "assets" / "hack" / "checkpoint-commit.sh"
TOKEN_SNAPSHOT_SRC = REPO / "sdflow-init" / "assets" / "hack" / "token_snapshot.py"
CANARY = "CANARY-TOKEN-SNAPSHOT-DO-NOT-LEAK-9f3a"


def _git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def _munge(repo):
    return str(repo.resolve()).replace("/", "-")


def _init_repo(tmp_path, branch="feat/demo-change", change="demo-change", name="repo"):
    """建一个假 repo，切到 `branch`，若给了 `change` 则同时建出对应 change 目录。"""
    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    _git(repo, "checkout", "-q", "-b", branch)
    if change:
        change_dir = repo / "openspec" / "changes" / change
        change_dir.mkdir(parents=True)
        (change_dir / ".keep").write_text("", encoding="utf-8")
    return repo


def _deploy_helper(home, script_text=None):
    """把 `~/.sdflow/hack/token_snapshot.py` 铺出来。`script_text` 给定时写一个替身脚本
    （用于模拟 helper 崩溃），否则软链回本仓真实源文件。
    """
    dest_dir = home / ".sdflow" / "hack"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "token_snapshot.py"
    if script_text is not None:
        dest.write_text(script_text, encoding="utf-8")
    else:
        os.symlink(str(TOKEN_SNAPSHOT_SRC), str(dest))


def _write_transcript(home, repo, session_id, lines):
    projects_dir = home / ".claude" / "projects" / _munge(repo)
    projects_dir.mkdir(parents=True, exist_ok=True)
    path = projects_dir / f"{session_id}.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for obj in lines:
            f.write(json.dumps(obj) + "\n")
    return path


def _assistant_msg(input_tokens=0, output_tokens=0, cache_read=0, cache_creation=0, extra=None):
    msg = {
        "role": "assistant",
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_input_tokens": cache_read,
            "cache_creation_input_tokens": cache_creation,
        },
    }
    if extra:
        msg.update(extra)
    return {"type": "assistant", "message": msg}


def _run_checkpoint(repo, home, step, desc=None, extra_env=None):
    env = dict(os.environ)
    env["HOME"] = str(home)
    env.pop("SDFLOW_HOME", None)
    if extra_env:
        env.update(extra_env)
    args = [bash_executable(), bash_path(CHECKPOINT_SCRIPT), step]
    if desc is not None:
        args.append(desc)
    return subprocess.run(args, cwd=str(repo), env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=60)


def _run_token_snapshot_directly(repo, home, step, extra_env=None):
    env = dict(os.environ)
    env["HOME"] = str(home)
    env.pop("SDFLOW_HOME", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["python3", str(TOKEN_SNAPSHOT_SRC), "--step", step],
        cwd=str(repo), env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=60,
    )


def _token_log_lines(repo, change):
    path = repo / "openspec" / "changes" / change / "token-log.jsonl"
    if not path.is_file():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _touch_untracked(repo, name="a.txt", content="hi"):
    (repo / name).write_text(content, encoding="utf-8")


class TestNormalCollection:
    def test_normal_collection_lands_in_same_commit(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        _deploy_helper(home)
        session = "abc12345-aaaa-bbbb-cccc-000000000001"
        _write_transcript(home, repo, session, [
            _assistant_msg(input_tokens=100, output_tokens=50, cache_read=10, cache_creation=5),
            _assistant_msg(input_tokens=200, output_tokens=75, cache_read=0, cache_creation=0),
        ])
        _touch_untracked(repo)

        r = _run_checkpoint(repo, home, "ff", "生成四件套",
                             extra_env={"CLAUDE_CODE_SESSION_ID": session})
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        row = lines[0]
        assert row["v"] == 1
        assert row["anchor"] is True
        assert row["reason"] == "ok"
        assert row["step"] == "ff"
        assert row["session"] == session
        assert row["host"] == "claude"
        assert row["usage"] == {
            "input": 300, "output": 125, "cache_read": 10, "cache_creation": 5, "messages": 2,
        }

        # 同一个 commit：token-log.jsonl 与业务改动一起入库
        show = _git(repo, "show", "--stat", "HEAD").stdout
        assert "token-log.jsonl" in show
        assert "a.txt" in show
        assert _git(repo, "rev-list", "--all", "--count").stdout.strip() == "1"

    def test_mtime_fallback_used_when_env_var_absent(self, tmp_path):
        """`$CLAUDE_CODE_SESSION_ID` 缺席 → 同目录 mtime 最新 jsonl 回退，仍判 anchor=true。"""
        home = tmp_path / "home"
        home.mkdir()
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        _deploy_helper(home)
        _write_transcript(home, repo, "old-session-0000", [_assistant_msg(input_tokens=1)])
        newest = _write_transcript(home, repo, "newest-session-1111",
                                    [_assistant_msg(input_tokens=42, output_tokens=7)])
        # 确保 mtime 排序稳定：newest 文件晚写入
        os.utime(newest, None)
        _touch_untracked(repo)

        env = dict(os.environ)
        env.pop("CLAUDE_CODE_SESSION_ID", None)
        r = _run_checkpoint(repo, home, "ff")
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["anchor"] is True
        assert lines[0]["session"] == "newest-session-1111"
        assert lines[0]["usage"]["input"] == 42


class TestNoTranscript:
    def test_no_transcript_writes_degraded_line(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        _deploy_helper(home)
        _touch_untracked(repo)

        r = _run_checkpoint(repo, home, "ff",
                             extra_env={"CLAUDE_CODE_SESSION_ID": "nonexistent-session-0000"})
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["anchor"] is False
        assert lines[0]["reason"] == "no-transcript"
        assert "usage" not in lines[0]
        # checkpoint 主功能不受影响
        assert _git(repo, "rev-list", "--all", "--count").stdout.strip() == "1"


class TestHelperAbsentOrCrashes:
    def test_helper_absent_checkpoint_still_commits(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        # 故意不部署 helper
        _touch_untracked(repo)

        r = _run_checkpoint(repo, home, "ff")
        assert r.returncode == 0, r.stdout + r.stderr
        assert _git(repo, "rev-list", "--all", "--count").stdout.strip() == "1"
        assert not (repo / "openspec" / "changes" / "demo-change" / "token-log.jsonl").exists()

    def test_helper_crash_checkpoint_still_commits(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        _deploy_helper(home, script_text="import sys\nsys.exit(1)\n")
        _touch_untracked(repo)

        r = _run_checkpoint(repo, home, "ff")
        assert r.returncode == 0, r.stdout + r.stderr
        assert _git(repo, "rev-list", "--all", "--count").stdout.strip() == "1"
        assert not (repo / "openspec" / "changes" / "demo-change" / "token-log.jsonl").exists()


class TestNoChangeDir:
    def test_protected_branch_writes_nothing(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        repo = _init_repo(tmp_path, branch="main", change=None)
        _deploy_helper(home)
        _write_transcript(home, repo, "sess-main-0000", [_assistant_msg(input_tokens=1)])
        _touch_untracked(repo)

        r = _run_checkpoint(repo, home, "ff",
                             extra_env={"CLAUDE_CODE_SESSION_ID": "sess-main-0000"})
        assert r.returncode == 0, r.stdout + r.stderr
        assert _git(repo, "rev-list", "--all", "--count").stdout.strip() == "1"
        # 无落点 = 零写入：连 openspec/changes/ 目录都不该被创建
        assert not (repo / "openspec" / "changes").exists()

    def test_feat_branch_without_change_dir_writes_nothing(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        repo = _init_repo(tmp_path, branch="feat/no-such-change", change=None)
        _deploy_helper(home)
        _write_transcript(home, repo, "sess-orphan-0000", [_assistant_msg(input_tokens=1)])
        _touch_untracked(repo)

        r = _run_checkpoint(repo, home, "ff",
                             extra_env={"CLAUDE_CODE_SESSION_ID": "sess-orphan-0000"})
        assert r.returncode == 0, r.stdout + r.stderr
        assert not (repo / "openspec" / "changes").exists()


class TestConsecutiveCheckpoints:
    def test_appends_monotonically_across_checkpoints(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        _deploy_helper(home)
        session = "sess-grow-0000"
        transcript = _write_transcript(home, repo, session, [
            _assistant_msg(input_tokens=10, output_tokens=5),
        ])
        _touch_untracked(repo, "a.txt")

        r1 = _run_checkpoint(repo, home, "ff", extra_env={"CLAUDE_CODE_SESSION_ID": session})
        assert r1.returncode == 0, r1.stdout + r1.stderr
        first_lines = _token_log_lines(repo, "demo-change")
        assert len(first_lines) == 1
        assert first_lines[0]["usage"]["input"] == 10

        # 模拟会话内 token 继续累积（session 累计值单调不减）
        with open(transcript, "a", encoding="utf-8") as f:
            f.write(json.dumps(_assistant_msg(input_tokens=20, output_tokens=10)) + "\n")
        _touch_untracked(repo, "b.txt")

        r2 = _run_checkpoint(repo, home, "spec-review",
                              extra_env={"CLAUDE_CODE_SESSION_ID": session})
        assert r2.returncode == 0, r2.stdout + r2.stderr

        all_lines = _token_log_lines(repo, "demo-change")
        assert len(all_lines) == 2
        # 先前行字节不变
        assert all_lines[0] == first_lines[0]
        assert all_lines[1]["step"] == "spec-review"
        assert all_lines[1]["usage"]["input"] == 30
        assert all_lines[1]["usage"]["input"] >= all_lines[0]["usage"]["input"]
        assert _git(repo, "rev-list", "--all", "--count").stdout.strip() == "2"


class TestCleanTreeNoOp:
    def test_clean_tree_with_helper_present_is_still_noop(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        _deploy_helper(home)
        session = "sess-clean-0000"
        _write_transcript(home, repo, session, [_assistant_msg(input_tokens=1)])
        # 工作树干净：change 目录里的 .keep 已被 `git add` 过一次? 不——尚未提交，git status
        # 非空（.keep 是新文件）。先提交一次让树变干净。
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "init")
        assert _git(repo, "status", "--porcelain").stdout.strip() == ""

        r = _run_checkpoint(repo, home, "ff", extra_env={"CLAUDE_CODE_SESSION_ID": session})
        assert r.returncode == 0, r.stdout + r.stderr
        assert "跳过" in r.stdout
        assert _git(repo, "rev-list", "--all", "--count").stdout.strip() == "1"  # 未新增 commit
        assert not (repo / "openspec" / "changes" / "demo-change" / "token-log.jsonl").exists()


class TestCanaryNoLeak:
    def test_canary_content_does_not_leak_into_output_surface(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        session = "sess-canary-0000"
        _write_transcript(home, repo, session, [
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "usage": {
                        "input_tokens": 5, "output_tokens": 3,
                        "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
                    },
                    "content": [
                        {"type": "text", "text": f"leaked text {CANARY}"},
                        {"type": "tool_use", "name": "Bash",
                         "input": {"command": f"echo {CANARY}"}},
                    ],
                },
            },
            {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [{"type": "tool_result", "content": f"tool output {CANARY}"}],
                },
            },
            {"type": "error", "error": {"message": f"boom {CANARY}"}},
        ])

        r = _run_token_snapshot_directly(repo, home, "ff",
                                         extra_env={"CLAUDE_CODE_SESSION_ID": session})
        assert r.returncode == 0
        assert CANARY not in r.stdout
        assert CANARY not in r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["anchor"] is True
        assert lines[0]["usage"]["input"] == 5
        raw = (repo / "openspec" / "changes" / "demo-change" / "token-log.jsonl").read_text(
            encoding="utf-8")
        assert CANARY not in raw
        # 输出面封闭：只有本 spec 列明的字段
        assert set(lines[0].keys()) <= {"v", "ts", "step", "session", "host", "anchor",
                                        "reason", "usage"}


class TestParseError:
    def test_malformed_json_line_degrades_to_parse_error(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        _deploy_helper(home)
        session = "sess-bad-json-0000"
        projects_dir = home / ".claude" / "projects" / _munge(repo)
        projects_dir.mkdir(parents=True)
        (projects_dir / f"{session}.jsonl").write_text(
            json.dumps(_assistant_msg(input_tokens=1)) + "\n"
            + "{this is not valid json\n",
            encoding="utf-8",
        )
        _touch_untracked(repo)

        r = _run_checkpoint(repo, home, "ff", extra_env={"CLAUDE_CODE_SESSION_ID": session})
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["anchor"] is False
        assert lines[0]["reason"] == "parse-error"
        assert "usage" not in lines[0]

    def test_negative_usage_count_degrades_to_parse_error(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        _deploy_helper(home)
        session = "sess-negative-0000"
        _write_transcript(home, repo, session, [_assistant_msg(input_tokens=-5)])
        _touch_untracked(repo)

        r = _run_checkpoint(repo, home, "ff", extra_env={"CLAUDE_CODE_SESSION_ID": session})
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["anchor"] is False
        assert lines[0]["reason"] == "parse-error"


class TestSessionIdGrammar:
    def test_path_traversal_session_id_is_rejected_and_falls_back(self, tmp_path):
        """恶意/畸形 session-id（含 `/`）MUST NOT 被拼进路径——退化为 mtime 回退或 no-transcript。"""
        home = tmp_path / "home"
        home.mkdir()
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        _deploy_helper(home)
        # 目录内没有任何合法 jsonl，只有恶意 session-id 指向仓外
        projects_dir = home / ".claude" / "projects" / _munge(repo)
        projects_dir.mkdir(parents=True)
        _touch_untracked(repo)

        malicious = "../../../../etc/passwd"
        r = _run_checkpoint(repo, home, "ff", extra_env={"CLAUDE_CODE_SESSION_ID": malicious})
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["anchor"] is False
        assert lines[0]["reason"] == "no-transcript"
        assert lines[0]["session"] == ""  # 未过文法校验，MUST NOT 回写进输出行
