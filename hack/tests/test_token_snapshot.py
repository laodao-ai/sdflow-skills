"""token-log.jsonl 快照采集契约（implement-workflow-optimization-2026-08-p1 · Task 3；
宿主判定补丁见 implement-workflow-optimization-2026-08-p2 · Task 5）。

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

【宿主基线】`_run_checkpoint` / `_run_token_snapshot_directly` 默认注入 `CLAUDECODE=1` +
清空 `CODEX_THREAD_ID`（claude 宿主基线），使 host 分支测试**不依赖运行本测试套件的真实
环境是否恰好在 Claude Code 会话里跑**（Task 5 引入 `detect_host()` 前，`host` 字段被硬编码
`"claude"`，测试对宿主环境零依赖；引入后必须显式钉死基线，否则在无 `CLAUDECODE` 的 CI/裸
终端跑会因宿主判 unknown 而全体误入「跳过 mtime 回退」分支，产生与本机结果不一致的假象）。
`extra_env` 里某 key 的值传 `None` = 从基线里删除该 key（而非设为空串），供
`TestHostDetection` 显式切换/清空宿主信号。
"""
import builtins
import importlib
import json
import os
import subprocess
import sys
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


def _apply_host_baseline(env, extra_env):
    """claude 宿主基线（`CLAUDECODE=1` + 清空 `CODEX_THREAD_ID`），再叠加 `extra_env`。

    `extra_env` 某 key 值为 `None` ⇒ 从 env 里删除该 key（用于 `TestHostDetection` 显式
    清空 `CLAUDECODE` 或注入 `CODEX_THREAD_ID`）；其余 key 正常覆盖写入。
    """
    env["CLAUDECODE"] = "1"
    env.pop("CODEX_THREAD_ID", None)
    if extra_env:
        for k, v in extra_env.items():
            if v is None:
                env.pop(k, None)
            else:
                env[k] = v
    return env


def _run_checkpoint(repo, home, step, desc=None, extra_env=None):
    env = dict(os.environ)
    env["HOME"] = str(home)
    env.pop("SDFLOW_HOME", None)
    _apply_host_baseline(env, extra_env)
    args = [bash_executable(), bash_path(CHECKPOINT_SCRIPT), step]
    if desc is not None:
        args.append(desc)
    return subprocess.run(args, cwd=str(repo), env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=60)


def _run_token_snapshot_directly(repo, home, step, extra_env=None):
    env = dict(os.environ)
    env["HOME"] = str(home)
    env.pop("SDFLOW_HOME", None)
    _apply_host_baseline(env, extra_env)
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


# ---------------------------------------------------------------------------
# Codex rollout fixtures (implement-optimize-codex-workflow-p2-pull · Task 2)
# ---------------------------------------------------------------------------
ROOT_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1"
CHILD_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1"
CHILD2_ID = "cccccccc-cccc-4ccc-8ccc-ccccccccccc1"
CHILD3_ID = "dddddddd-dddd-4ddd-8ddd-ddddddddddd1"


def _codex_home(tmp_path, name="codexhome"):
    home = tmp_path / name
    (home / "sessions").mkdir(parents=True, exist_ok=True)
    return home


def _rollout_path(codex_home, thread_id, subdir="2026/09/21"):
    d = codex_home / "sessions" / subdir
    d.mkdir(parents=True, exist_ok=True)
    return d / f"rollout-2026-09-21T00-00-00-{thread_id}.jsonl"


def _row(rtype, payload, ts="2026-09-21T00:00:00.000Z"):
    return {"timestamp": ts, "ordinal": 0, "type": rtype, "payload": payload}


def _session_meta_row(thread_id, parent=None, cli_version="0.155.0", branch=None,
                       agent_path=None, depth=None, extra_payload=None):
    payload = {"id": thread_id, "session_id": thread_id, "cli_version": cli_version}
    if parent is not None:
        payload["parent_thread_id"] = parent
    if branch is not None:
        payload["git"] = {"branch": branch}
    if agent_path is not None or depth is not None:
        payload["agent_path"] = agent_path
        payload["source"] = {"subagent": {"thread_spawn": {
            "depth": depth if depth is not None else 0, "agent_path": agent_path,
        }}}
    if extra_payload:
        payload.update(extra_payload)
    return _row("session_meta", payload)


def _turn_context_row(turn_id, model, effort, ts="2026-09-21T00:00:01.000Z"):
    return _row("turn_context", {"turn_id": turn_id, "model": model, "effort": effort}, ts=ts)


def _task_started_row(turn_id, ts):
    return _row("event_msg", {"type": "task_started", "turn_id": turn_id}, ts=ts)


def _task_complete_row(turn_id, ts):
    return _row("event_msg", {"type": "task_complete", "turn_id": turn_id}, ts=ts)


_ZERO_USAGE = {
    "input_tokens": 0, "cached_input_tokens": 0, "cache_write_input_tokens": 0,
    "output_tokens": 0, "reasoning_output_tokens": 0, "total_tokens": 0,
}


def _token_usage_record_row(thread_id, turn_id, thread_usage,
                             ts="2026-09-21T00:00:02.000Z"):
    tu = dict(_ZERO_USAGE)
    tu.update(thread_usage)
    return _row("token_usage_record", {
        "thread_id": thread_id, "turn_id": turn_id, "session_id": thread_id,
        "root_turn_id": turn_id, "response_id": "resp_x",
        "usage": tu, "turn_token_usage": tu, "thread_token_usage": tu,
    }, ts=ts)


def _item_completed_subagent_row(thread_id, turn_id, child_id, kind="started",
                                  child_path="/root/task1"):
    return _row("event_msg", {
        "type": "item_completed", "thread_id": thread_id, "turn_id": turn_id,
        "started_at_ms": 0, "completed_at_ms": 0,
        "item": {"type": "SubAgentActivity", "id": "call_1", "kind": kind,
                  "agent_thread_id": child_id, "agent_path": child_path},
    })


def _write_rollout_rows(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _codex_extra_env(codex_home, thread_id):
    return {"CLAUDECODE": None, "CODEX_THREAD_ID": thread_id,
            "CODEX_HOME": str(codex_home)}


def _import_token_snapshot_module():
    """直接 import 源模块（用于需要 monkeypatch 内部函数的白盒测试，如 SIGALRM 场景）。"""
    src_dir = str(TOKEN_SNAPSHOT_SRC.parent)
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    if "token_snapshot" in sys.modules:
        return importlib.reload(sys.modules["token_snapshot"])
    return importlib.import_module("token_snapshot")


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


class TestHostDetection:
    """implement-workflow-optimization-2026-08-p2 · Task 5：codex/unknown 宿主 MUST NOT 走
    Claude transcript mtime 回退——即便回退目录里摆着一份完全合法、能命中的 transcript，
    非 claude 宿主也必须直接落 `no-transcript` 降级行，不得读到它。`host` 字段如实写检测值
    （而非历史上恒为 `"claude"` 的写法）。
    """

    def test_codex_host_skips_mtime_fallback_even_with_matching_transcript(self, tmp_path):
        """implement-optimize-codex-workflow-p2-pull Task 2.1 起，codex 宿主不再走
        「见到 codex 就一律 no-transcript」的旧 v1 兜底——`CODEX_THREAD_ID` 非空但文法不合
        （非 UUID）→ `invalid-thread-id`（v2）。不论新旧行为，本测试的核心断言不变：
        codex 宿主是「主动不看」`~/.claude` 的 mtime 回退目录，不是「碰巧没找到」。
        """
        home = tmp_path / "home"
        home.mkdir()
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        _deploy_helper(home)
        # mtime 回退目录里摆一份完全合法、会被 claude 宿主命中的 transcript——
        # 用来证明 codex 宿主是「主动不看」，不是「碰巧没找到」。
        _write_transcript(home, repo, "would-be-picked-0000",
                           [_assistant_msg(input_tokens=99, output_tokens=1)])
        _touch_untracked(repo)

        r = _run_checkpoint(repo, home, "ff", extra_env={
            "CLAUDECODE": None, "CODEX_THREAD_ID": "codex-thread-abc123",
        })
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["v"] == 2
        assert lines[0]["anchor"] is False
        assert lines[0]["reason"] == "invalid-thread-id"
        assert lines[0]["host"] == "codex"
        assert lines[0]["runner"] == "codex"
        assert lines[0]["usage"] is None
        assert lines[0]["session"] == ""

    def test_unknown_host_skips_mtime_fallback_when_no_signal_present(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        _deploy_helper(home)
        _write_transcript(home, repo, "would-be-picked-1111",
                           [_assistant_msg(input_tokens=7)])
        _touch_untracked(repo)

        r = _run_checkpoint(repo, home, "ff", extra_env={"CLAUDECODE": None})
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["anchor"] is False
        assert lines[0]["reason"] == "no-transcript"
        assert lines[0]["host"] == "unknown"

    def test_conflicting_host_signals_fall_to_unknown_and_skip_fallback(self, tmp_path):
        """两个宿主信号同时出现 = 冲突，MUST NOT 静默取其一——落 unknown，同样不碰 mtime 回退。"""
        home = tmp_path / "home"
        home.mkdir()
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        _deploy_helper(home)
        _write_transcript(home, repo, "would-be-picked-2222",
                           [_assistant_msg(input_tokens=3)])
        _touch_untracked(repo)

        r = _run_checkpoint(repo, home, "ff",
                             extra_env={"CODEX_THREAD_ID": "codex-thread-conflict"})
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["anchor"] is False
        assert lines[0]["reason"] == "no-transcript"
        assert lines[0]["host"] == "unknown"

    def test_claude_host_baseline_still_reports_host_claude(self, tmp_path):
        """基线场景（本文件默认注入的 claude 宿主）：host 字段如实写 "claude"，行为不变。"""
        home = tmp_path / "home"
        home.mkdir()
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        _deploy_helper(home)
        session = "sess-claude-baseline-0000"
        _write_transcript(home, repo, session, [_assistant_msg(input_tokens=11)])
        _touch_untracked(repo)

        r = _run_checkpoint(repo, home, "ff", extra_env={"CLAUDE_CODE_SESSION_ID": session})
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["anchor"] is True
        assert lines[0]["host"] == "claude"
        assert lines[0]["usage"]["input"] == 11


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


CODEX_LINE_KEYS_UNDER_TEST = {
    "v", "ts", "step", "host", "runner", "kind", "session", "parent", "role",
    "depth", "model", "effort", "config_mixed", "cli_version", "usage_source",
    "branch_at_start", "usage", "turns", "duration_ms", "anchor", "reason",
}


class TestCodexRootProjection:
    """implement-optimize-codex-workflow-p2-pull · Task 2.1/2.2：codex 分支根线程投影。"""

    def test_root_only_ok_line_full_projection(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home = _codex_home(tmp_path)
        rows = [
            _session_meta_row(ROOT_ID, branch="feat/demo-change"),
            _turn_context_row("turn-1", "gpt-5.6", "high"),
            _task_started_row("turn-1", "2026-09-21T00:00:00.000Z"),
            _task_complete_row("turn-1", "2026-09-21T00:00:01.500Z"),
            _token_usage_record_row(ROOT_ID, "turn-1", {
                "input_tokens": 100, "cached_input_tokens": 10,
                "output_tokens": 20, "reasoning_output_tokens": 5, "total_tokens": 135,
            }),
        ]
        _write_rollout_rows(_rollout_path(codex_home, ROOT_ID), rows)

        r = _run_token_snapshot_directly(repo, tmp_path / "home", "ff",
                                          extra_env=_codex_extra_env(codex_home, ROOT_ID))
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        row = lines[0]
        assert row["v"] == 2
        assert row["host"] == "codex"
        assert row["runner"] == "codex"
        assert row["kind"] == "root"
        assert row["session"] == ROOT_ID
        assert row["parent"] is None
        assert row["role"] is None
        assert row["depth"] == 0
        assert row["model"] == "gpt-5.6"
        assert row["effort"] == "high"
        assert row["config_mixed"] is False
        assert row["cli_version"] == "0.155.0"
        assert row["branch_at_start"] == "feat/demo-change"
        assert row["usage_source"] == "token_usage_record"
        assert row["usage"] == {
            "input": 100, "cached_input": 10, "cache_write_input": 0,
            "output": 20, "reasoning_output": 5, "total": 135,
        }
        assert row["turns"] == 1
        assert row["duration_ms"] == 1500
        assert row["anchor"] is True
        assert row["reason"] == "ok"

    def test_config_mixed_flagged_when_model_or_effort_changes_within_thread(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home = _codex_home(tmp_path)
        rows = [
            _session_meta_row(ROOT_ID, branch="feat/demo-change"),
            _turn_context_row("turn-1", "gpt-5.6", "high", ts="2026-09-21T00:00:00.100Z"),
            _turn_context_row("turn-2", "gpt-5.6", "medium", ts="2026-09-21T00:00:02.100Z"),
        ]
        _write_rollout_rows(_rollout_path(codex_home, ROOT_ID), rows)

        r = _run_token_snapshot_directly(repo, tmp_path / "home", "ff",
                                          extra_env=_codex_extra_env(codex_home, ROOT_ID))
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert lines[0]["config_mixed"] is True
        assert lines[0]["effort"] == "medium"  # 取最后一个 turn_context 的值

    def test_token_count_info_used_as_fallback_usage_source(self, tmp_path):
        """无 `token_usage_record` 时退回 `token_count.info.total_token_usage`
        （双轴审 Finding 2：此前所有 usage 测试只走 token_usage_record 分支，无覆盖）。"""
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home = _codex_home(tmp_path)
        rows = [
            _session_meta_row(ROOT_ID, branch="feat/demo-change"),
            _turn_context_row("turn-1", "gpt-5.6", "high"),
            _task_started_row("turn-1", "2026-09-21T00:00:00.000Z"),
            _task_complete_row("turn-1", "2026-09-21T00:00:01.500Z"),
            _row("event_msg", {"type": "token_count", "info": {"total_token_usage": {
                "input_tokens": 100, "cached_input_tokens": 10,
                "output_tokens": 20, "reasoning_output_tokens": 5, "total_tokens": 135,
            }}}),
        ]
        _write_rollout_rows(_rollout_path(codex_home, ROOT_ID), rows)

        r = _run_token_snapshot_directly(repo, tmp_path / "home", "ff",
                                          extra_env=_codex_extra_env(codex_home, ROOT_ID))
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        row = lines[0]
        assert row["usage_source"] == "token_count"
        assert row["usage"] == {
            "input": 100, "cached_input": 10, "cache_write_input": None,
            "output": 20, "reasoning_output": 5, "total": 135,
        }
        assert row["anchor"] is True
        assert row["reason"] == "ok"


class TestCodexChildEnumeration:
    """implement-optimize-codex-workflow-p2-pull · Task 2.1：子线程零扫描枚举。"""

    def test_root_and_child_both_appended_in_traversal_order(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home = _codex_home(tmp_path)
        _write_rollout_rows(_rollout_path(codex_home, ROOT_ID), [
            _session_meta_row(ROOT_ID, branch="feat/demo-change"),
            _item_completed_subagent_row(ROOT_ID, "turn-r", CHILD_ID, child_path="/root/task1"),
        ])
        _write_rollout_rows(_rollout_path(codex_home, CHILD_ID), [
            _session_meta_row(CHILD_ID, parent=ROOT_ID, branch="feat/demo-change",
                              agent_path="/root/task1", depth=1),
        ])

        r = _run_token_snapshot_directly(repo, tmp_path / "home", "ff",
                                          extra_env=_codex_extra_env(codex_home, ROOT_ID))
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 2
        assert lines[0]["kind"] == "root"
        assert lines[0]["session"] == ROOT_ID
        assert lines[1]["kind"] == "child"
        assert lines[1]["session"] == CHILD_ID
        assert lines[1]["parent"] == ROOT_ID
        assert lines[1]["role"] == "/root/task1"
        assert lines[1]["depth"] == 1
        # 未提供 usage 事件的两个线程都应显式降级、非猜测
        assert lines[0]["reason"] == "no-usage-events"
        assert lines[1]["reason"] == "no-usage-events"

    def test_interacted_activity_referencing_parent_is_not_treated_as_new_child(self, tmp_path):
        """`kind=interacted` 的 SubAgentActivity（子线程回指父线程）MUST NOT 被当成新子线程
        入队——只有 `kind=started` 才是真正的「本线程新增了一个子代理」（codex-rs
        SubAgentActivityKind：Started/Interacted/Interrupted/Completed，仅 Started 代表新建）。
        """
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home = _codex_home(tmp_path)
        _write_rollout_rows(_rollout_path(codex_home, ROOT_ID), [
            _session_meta_row(ROOT_ID, branch="feat/demo-change"),
            _item_completed_subagent_row(ROOT_ID, "turn-r", CHILD_ID, kind="interacted",
                                          child_path="/root"),
        ])
        # CHILD_ID 故意不建 rollout 文件——如果代码误把 interacted 当子线程入队，会产出
        # 一行 thread-not-found；本测试断言只有 root 一行。

        r = _run_token_snapshot_directly(repo, tmp_path / "home", "ff",
                                          extra_env=_codex_extra_env(codex_home, ROOT_ID))
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["session"] == ROOT_ID


class TestCodexFailureModes:
    """implement-optimize-codex-workflow-p2-pull · Task 2.1：reason 枚举覆盖。"""

    def test_thread_not_found_when_no_rollout_matches(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home = _codex_home(tmp_path)  # sessions/ 目录存在，但没有任何 rollout 文件

        r = _run_token_snapshot_directly(repo, tmp_path / "home", "ff",
                                          extra_env=_codex_extra_env(codex_home, ROOT_ID))
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["anchor"] is False
        assert lines[0]["reason"] == "thread-not-found"
        assert lines[0]["session"] == ROOT_ID  # 文法已过校验，如实记录
        assert lines[0]["usage"] is None

    def test_thread_not_found_when_multiple_rollouts_match(self, tmp_path):
        """多命中 MUST NOT 猜——取 0 行，直接判 `thread-not-found`。"""
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home = _codex_home(tmp_path)
        _write_rollout_rows(_rollout_path(codex_home, ROOT_ID, subdir="2026/09/20"),
                             [_session_meta_row(ROOT_ID, branch="feat/demo-change")])
        _write_rollout_rows(_rollout_path(codex_home, ROOT_ID, subdir="2026/09/21"),
                             [_session_meta_row(ROOT_ID, branch="feat/demo-change")])

        r = _run_token_snapshot_directly(repo, tmp_path / "home", "ff",
                                          extra_env=_codex_extra_env(codex_home, ROOT_ID))
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["reason"] == "thread-not-found"

    def test_no_codex_home_sessions_dir_is_thread_not_found(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home = tmp_path / "no-such-codex-home"  # 目录整体不存在

        r = _run_token_snapshot_directly(repo, tmp_path / "home", "ff",
                                          extra_env=_codex_extra_env(codex_home, ROOT_ID))
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["reason"] == "thread-not-found"

    def test_no_usage_events_reason_when_no_usage_record_present(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home = _codex_home(tmp_path)
        _write_rollout_rows(_rollout_path(codex_home, ROOT_ID), [
            _session_meta_row(ROOT_ID, branch="feat/demo-change"),
            _turn_context_row("turn-1", "gpt-5.6", "high"),
            _task_started_row("turn-1", "2026-09-21T00:00:00.000Z"),
            _task_complete_row("turn-1", "2026-09-21T00:00:01.000Z"),
        ])

        r = _run_token_snapshot_directly(repo, tmp_path / "home", "ff",
                                          extra_env=_codex_extra_env(codex_home, ROOT_ID))
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        row = lines[0]
        assert row["anchor"] is False
        assert row["reason"] == "no-usage-events"
        assert row["usage"] is None
        # 其他字段照记，不因缺 usage 而一并降级
        assert row["model"] == "gpt-5.6"
        assert row["turns"] == 1
        assert row["duration_ms"] == 1000

    def test_negative_usage_count_degrades_whole_thread_to_parse_error(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home = _codex_home(tmp_path)
        _write_rollout_rows(_rollout_path(codex_home, ROOT_ID), [
            _session_meta_row(ROOT_ID, branch="feat/demo-change"),
            _token_usage_record_row(ROOT_ID, "turn-1", {"input_tokens": -5}),
        ])

        r = _run_token_snapshot_directly(repo, tmp_path / "home", "ff",
                                          extra_env=_codex_extra_env(codex_home, ROOT_ID))
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["anchor"] is False
        assert lines[0]["reason"] == "parse-error"
        assert lines[0]["usage"] is None

    def test_malformed_json_line_degrades_thread_to_parse_error(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home = _codex_home(tmp_path)
        path = _rollout_path(codex_home, ROOT_ID)
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(_session_meta_row(ROOT_ID, branch="feat/demo-change")) + "\n")
            f.write('{"type": "token_usage_record", this is not valid json\n')

        r = _run_token_snapshot_directly(repo, tmp_path / "home", "ff",
                                          extra_env=_codex_extra_env(codex_home, ROOT_ID))
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["reason"] == "parse-error"

    def test_depth_exceeded_never_opens_the_over_limit_thread_file(self, tmp_path):
        """深度链 root(0)→c1(1)→…→c8(8) 正常投影；c9(9) 超限——超限线程 MUST NOT 被打开
        （本测试故意不为 c9 建 rollout 文件；若代码误开它，会得到 thread-not-found 而非
        depth-exceeded，断言即可区分两者）。
        """
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home = _codex_home(tmp_path)
        chain = [f"{i:08x}-0000-4000-8000-000000000000" for i in range(10)]
        for i in range(9):  # chain[0..8] 建文件；chain[9] 故意不建
            rows = [_session_meta_row(chain[i],
                                       parent=chain[i - 1] if i > 0 else None,
                                       branch="feat/demo-change",
                                       agent_path=f"/root/task{i}" if i > 0 else None,
                                       depth=i if i > 0 else None)]
            rows.append(_item_completed_subagent_row(chain[i], "turn-x", chain[i + 1],
                                                       child_path=f"/root/task{i + 1}"))
            _write_rollout_rows(_rollout_path(codex_home, chain[i]), rows)

        r = _run_token_snapshot_directly(repo, tmp_path / "home", "ff",
                                          extra_env=_codex_extra_env(codex_home, chain[0]))
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 10
        by_session = {l["session"]: l for l in lines}
        for i in range(9):
            assert by_session[chain[i]]["reason"] == "no-usage-events"
            assert by_session[chain[i]]["depth"] == i
        assert by_session[chain[9]]["reason"] == "depth-exceeded"
        assert by_session[chain[9]]["depth"] == 9
        assert by_session[chain[9]]["anchor"] is False


class TestCodexSymlinkEscape:
    """implement-optimize-codex-workflow-p2-pull · Task 2 双轴审 Finding 1：
    `_locate_codex_rollout` 的 symlink 逃逸拒绝此前零测试覆盖。"""

    def _make_escape_fixture(self, tmp_path):
        codex_home = _codex_home(tmp_path)
        sessions_root = codex_home / "sessions"
        outside_dir = tmp_path / "outside-sessions-root"
        outside_dir.mkdir()
        outside_target = outside_dir / f"secret-{ROOT_ID}.jsonl"
        _write_rollout_rows(outside_target, [
            _session_meta_row(ROOT_ID, branch="feat/demo-change"),
            _token_usage_record_row(ROOT_ID, "turn-1", {"input_tokens": 5, "total_tokens": 5}),
        ])
        link_dir = sessions_root / "2026" / "09" / "21"
        link_dir.mkdir(parents=True, exist_ok=True)
        symlink_path = link_dir / f"rollout-2026-09-21T00-00-00-{ROOT_ID}.jsonl"
        symlink_path.symlink_to(outside_target)
        return codex_home, sessions_root

    def test_locate_codex_rollout_rejects_symlink_escaping_sessions_root(self, tmp_path):
        ts_mod = _import_token_snapshot_module()
        _, sessions_root = self._make_escape_fixture(tmp_path)

        result = ts_mod._locate_codex_rollout(sessions_root, ROOT_ID)
        assert result is None

    def test_symlink_escape_end_to_end_writes_thread_not_found(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home, _ = self._make_escape_fixture(tmp_path)

        r = _run_token_snapshot_directly(repo, tmp_path / "home", "ff",
                                          extra_env=_codex_extra_env(codex_home, ROOT_ID))
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["reason"] == "thread-not-found"
        assert lines[0]["usage"] is None


class TestCodexSigalrmMidTraversal:
    """implement-optimize-codex-workflow-p2-pull · Task 2.1/2.4：总 deadline 超时——
    已组装完的行照写，尚未处理（含正在处理）的线程各写一行 `timeout`。
    """

    def test_timeout_at_second_child_writes_prior_ok_lines_and_marks_rest_timeout(
            self, tmp_path, monkeypatch):
        ts_mod = _import_token_snapshot_module()
        codex_home = _codex_home(tmp_path)
        _write_rollout_rows(_rollout_path(codex_home, ROOT_ID), [
            _session_meta_row(ROOT_ID, branch="feat/demo-change"),
            _item_completed_subagent_row(ROOT_ID, "turn-r", CHILD_ID, child_path="/root/task1"),
            _item_completed_subagent_row(ROOT_ID, "turn-r", CHILD2_ID, child_path="/root/task2"),
            _item_completed_subagent_row(ROOT_ID, "turn-r", CHILD3_ID, child_path="/root/task3"),
        ])
        _write_rollout_rows(_rollout_path(codex_home, CHILD_ID),
                             [_session_meta_row(CHILD_ID, parent=ROOT_ID,
                                                 branch="feat/demo-change")])
        _write_rollout_rows(_rollout_path(codex_home, CHILD2_ID),
                             [_session_meta_row(CHILD2_ID, parent=ROOT_ID,
                                                 branch="feat/demo-change")])
        _write_rollout_rows(_rollout_path(codex_home, CHILD3_ID),
                             [_session_meta_row(CHILD3_ID, parent=ROOT_ID,
                                                 branch="feat/demo-change")])

        real_project = ts_mod._project_codex_rollout

        def fake_project(path, own_id):
            if own_id == CHILD2_ID:
                raise ts_mod._Timeout()
            return real_project(path, own_id)

        monkeypatch.setattr(ts_mod, "_project_codex_rollout", fake_project)
        monkeypatch.setenv("CODEX_HOME", str(codex_home))
        monkeypatch.setenv("CODEX_THREAD_ID", ROOT_ID)
        monkeypatch.delenv("CLAUDECODE", raising=False)

        log_path = tmp_path / "token-log.jsonl"
        ts_mod._codex_collect_and_write("ff", log_path)

        lines = [json.loads(l) for l in log_path.read_text(encoding="utf-8").splitlines()]
        by_session = {l["session"]: l for l in lines}
        assert len(lines) == 4
        assert by_session[ROOT_ID]["reason"] == "no-usage-events"
        assert by_session[CHILD_ID]["reason"] == "no-usage-events"  # 前序行：已落盘
        assert by_session[CHILD2_ID]["reason"] == "timeout"  # 第 2 个子线程：SIGALRM 命中处
        assert by_session[CHILD3_ID]["reason"] == "timeout"  # 后续线程：仍在队列中，一并写 timeout


class TestCodexCanaryNoLeak:
    """implement-optimize-codex-workflow-p2-pull · Task 2.4：canary 零外泄 + 封闭键集合。"""

    def test_canary_content_does_not_leak_and_keys_are_closed(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home = _codex_home(tmp_path)
        canary = "CANARY-CODEX-ROLLOUT-DO-NOT-LEAK-7c1e"
        rows = [
            _session_meta_row(ROOT_ID, branch="feat/demo-change",
                               extra_payload={
                                   "cwd": f"/tmp/{canary}",
                                   "agent_nickname": canary,
                                   "base_instructions": {"text": f"leaked {canary}"},
                               }),
            _turn_context_row("turn-1", "gpt-5.6", "high"),
            _task_started_row("turn-1", "2026-09-21T00:00:00.000Z"),
            _task_complete_row("turn-1", "2026-09-21T00:00:01.000Z"),
            _token_usage_record_row(ROOT_ID, "turn-1", {"input_tokens": 5, "total_tokens": 5}),
        ]
        _write_rollout_rows(_rollout_path(codex_home, ROOT_ID), rows)
        # 同目录一份完全无关的 rollout——用来证明它未被打开/解析（不属于本线程链）。
        unrelated_id = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeee1"
        _write_rollout_rows(_rollout_path(codex_home, unrelated_id), [
            _row("session_meta", {"id": unrelated_id, "session_id": unrelated_id,
                                   "cwd": f"/tmp/unrelated-{canary}-should-not-be-read"}),
        ])

        r = _run_token_snapshot_directly(repo, tmp_path / "home", "ff",
                                          extra_env=_codex_extra_env(codex_home, ROOT_ID))
        assert r.returncode == 0
        assert canary not in r.stdout
        assert canary not in r.stderr

        raw = (repo / "openspec" / "changes" / "demo-change" / "token-log.jsonl").read_text(
            encoding="utf-8")
        assert canary not in raw

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1  # 无关 rollout 未产出任何行——未被枚举、未被打开
        assert set(lines[0].keys()) == CODEX_LINE_KEYS_UNDER_TEST

    def test_open_calls_never_touch_unrelated_rollout_file(self, tmp_path, monkeypatch):
        """双轴审 Finding 3：上面的"行数=1"是间接证据。这里用 monkeypatch 直接记录
        实际被 `open()` 的路径集合，断言无关 rollout 文件的路径从未出现在其中
        （须在同进程内跑——`_run_token_snapshot_directly` 走 subprocess，monkeypatch
        跨不了进程边界）。"""
        ts_mod = _import_token_snapshot_module()
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home = _codex_home(tmp_path)
        root_rollout = _rollout_path(codex_home, ROOT_ID)
        _write_rollout_rows(root_rollout, [
            _session_meta_row(ROOT_ID, branch="feat/demo-change"),
            _token_usage_record_row(ROOT_ID, "turn-1", {"input_tokens": 5, "total_tokens": 5}),
        ])
        unrelated_id = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeee2"
        unrelated_rollout = _rollout_path(codex_home, unrelated_id)
        _write_rollout_rows(unrelated_rollout, [
            _row("session_meta", {"id": unrelated_id, "session_id": unrelated_id}),
        ])

        opened_paths = []
        real_open = builtins.open

        def recording_open(file, *args, **kwargs):
            try:
                opened_paths.append(str(Path(file).resolve()))
            except Exception:
                opened_paths.append(str(file))
            return real_open(file, *args, **kwargs)

        monkeypatch.setattr(ts_mod, "open", recording_open, raising=False)
        monkeypatch.chdir(repo)
        monkeypatch.setenv("HOME", str(tmp_path / "home"))
        monkeypatch.setenv("CODEX_HOME", str(codex_home))
        monkeypatch.setenv("CODEX_THREAD_ID", ROOT_ID)
        monkeypatch.delenv("CLAUDECODE", raising=False)
        monkeypatch.delenv("SDFLOW_HOME", raising=False)

        rc = ts_mod.main(["--step", "ff"])
        assert rc == 0

        assert str(root_rollout.resolve()) in opened_paths
        assert str(unrelated_rollout.resolve()) not in opened_paths


class TestCodexChangeStartWiring:
    """implement-optimize-codex-workflow-p2-pull · Task 2.3：`--step change-start` 无额外 Git 依赖。"""

    def test_change_start_step_adds_no_extra_git_subprocess_calls(self, tmp_path, monkeypatch):
        ts_mod = _import_token_snapshot_module()
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home = _codex_home(tmp_path)
        _write_rollout_rows(_rollout_path(codex_home, ROOT_ID),
                             [_session_meta_row(ROOT_ID, branch="feat/demo-change")])

        monkeypatch.chdir(repo)
        monkeypatch.setenv("CODEX_HOME", str(codex_home))
        monkeypatch.setenv("CODEX_THREAD_ID", ROOT_ID)
        monkeypatch.delenv("CLAUDECODE", raising=False)

        calls = []
        real_run = ts_mod.subprocess.run

        def counting_run(*args, **kwargs):
            calls.append(args)
            return real_run(*args, **kwargs)

        monkeypatch.setattr(ts_mod.subprocess, "run", counting_run)

        rc = ts_mod.main(["--step", "change-start"])
        assert rc == 0
        # `_resolve_change_dir` 的既有两次 git 调用（symbolic-ref + rev-parse show-toplevel）
        # 之外，codex 分支 MUST NOT 再新增任何 subprocess 调用（design.md D9）。
        assert len(calls) == 2

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["step"] == "change-start"
        assert lines[0]["reason"] == "no-usage-events"

    def test_skill_md_invokes_change_start_after_openspec_new_change(self):
        skill_md = (REPO / "sdflow-spec" / "SKILL.md").read_text(encoding="utf-8")
        anchor = 'openspec new change "<name>"'
        assert anchor in skill_md
        after = skill_md.split(anchor, 1)[1]
        assert "token_snapshot.py --step change-start || true" in after[:2000]


class TestCodexMultiLevelChildEnumeration:
    """implement-optimize-codex-workflow-p2-pull · Task 3.1：三层链路 depth/parent/role
    全部如实记录（补 Task 2 既有覆盖的第 3 层断言——之前的多层夹具只断言到 depth=1/9，
    未在同一条链上核对 depth=2 的 parent/role）。
    """

    def test_three_level_chain_records_depth_parent_role_at_every_level(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home = _codex_home(tmp_path)
        grandchild_id = "ffffffff-ffff-4fff-8fff-fffffffffff1"
        _write_rollout_rows(_rollout_path(codex_home, ROOT_ID), [
            _session_meta_row(ROOT_ID, branch="feat/demo-change"),
            _item_completed_subagent_row(ROOT_ID, "turn-r", CHILD_ID, child_path="/root/task1"),
        ])
        _write_rollout_rows(_rollout_path(codex_home, CHILD_ID), [
            _session_meta_row(CHILD_ID, parent=ROOT_ID, branch="feat/demo-change",
                              agent_path="/root/task1", depth=1),
            _item_completed_subagent_row(CHILD_ID, "turn-c", grandchild_id,
                                          child_path="/root/task1_sub1"),
        ])
        _write_rollout_rows(_rollout_path(codex_home, grandchild_id), [
            _session_meta_row(grandchild_id, parent=CHILD_ID, branch="feat/demo-change",
                              agent_path="/root/task1_sub1", depth=2),
        ])

        r = _run_token_snapshot_directly(repo, tmp_path / "home", "ff",
                                          extra_env=_codex_extra_env(codex_home, ROOT_ID))
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        by_session = {l["session"]: l for l in lines}
        assert len(lines) == 3
        assert by_session[ROOT_ID]["kind"] == "root"
        assert by_session[ROOT_ID]["depth"] == 0
        assert by_session[ROOT_ID]["parent"] is None
        assert by_session[CHILD_ID]["kind"] == "child"
        assert by_session[CHILD_ID]["depth"] == 1
        assert by_session[CHILD_ID]["parent"] == ROOT_ID
        assert by_session[CHILD_ID]["role"] == "/root/task1"
        assert by_session[grandchild_id]["kind"] == "child"
        assert by_session[grandchild_id]["depth"] == 2
        assert by_session[grandchild_id]["parent"] == CHILD_ID
        assert by_session[grandchild_id]["role"] == "/root/task1_sub1"


# ---------------------------------------------------------------------------
# outside-voice `--cli-usage` 子入口（Task 3.2；design.md TSA-04）
# ---------------------------------------------------------------------------

def _run_cli_usage_directly(repo, home, jsonl_path, extra_env=None):
    env = dict(os.environ)
    env["HOME"] = str(home)
    env.pop("SDFLOW_HOME", None)
    _apply_host_baseline(env, extra_env)
    return subprocess.run(
        ["python3", str(TOKEN_SNAPSHOT_SRC), "--cli-usage", str(jsonl_path)],
        cwd=str(repo), env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=60,
    )


def _write_jsonl(path, objs):
    with open(path, "w", encoding="utf-8") as f:
        for o in objs:
            if isinstance(o, str):
                f.write(o + "\n")
            else:
                f.write(json.dumps(o, ensure_ascii=False) + "\n")


CLI_THREAD_ID = "sample-cli-thread"
_CLI_USAGE_FIVE_COUNT = {
    "input_tokens": 20905, "cached_input_tokens": 9984, "cache_write_input_tokens": 0,
    "output_tokens": 5, "reasoning_output_tokens": 0,
}


class TestCliUsageSubcommand:
    """implement-optimize-codex-workflow-p2-pull · Task 3.2：`--cli-usage <jsonl>` 子入口。"""

    def test_normal_call_writes_one_anchored_cli_line(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        jsonl = tmp_path / "cli.log"
        _write_jsonl(jsonl, [
            {"type": "thread.started", "thread_id": CLI_THREAD_ID},
            {"type": "turn.started"},
            {"type": "turn.completed", "usage": _CLI_USAGE_FIVE_COUNT},
        ])

        r = _run_cli_usage_directly(repo, tmp_path / "home", jsonl)
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        row = lines[0]
        assert row["v"] == 2
        assert row["kind"] == "cli"
        assert row["anchor"] is True
        assert row["reason"] == "ok"
        assert row["session"] == CLI_THREAD_ID
        assert row["role"] == "outside-voice"
        assert row["usage_source"] == "cli"
        # 来源未提供 total ⇒ null，MUST NOT 派生（D2）
        assert row["usage"] == {
            "input": 20905, "cached_input": 9984, "cache_write_input": 0,
            "output": 5, "reasoning_output": 0, "total": None,
        }
        # host = 本进程判定的实际宿主（claude 基线），runner 恒为 codex（TSA-04/HAE-02）
        assert row["host"] == "claude"
        assert row["runner"] == "codex"

    def test_turn_failed_with_usage_is_anchored(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        jsonl = tmp_path / "cli.log"
        _write_jsonl(jsonl, [
            {"type": "thread.started", "thread_id": CLI_THREAD_ID},
            {"type": "turn.failed", "usage": _CLI_USAGE_FIVE_COUNT},
        ])

        r = _run_cli_usage_directly(repo, tmp_path / "home", jsonl)
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["anchor"] is True
        assert lines[0]["reason"] == "ok"

    def test_unparseable_jsonl_degrades_to_parse_error(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        jsonl = tmp_path / "cli.log"
        _write_jsonl(jsonl, ["not json at all", "still not json"])

        r = _run_cli_usage_directly(repo, tmp_path / "home", jsonl)
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["kind"] == "cli"
        assert lines[0]["anchor"] is False
        assert lines[0]["reason"] == "parse-error"
        assert lines[0]["usage"] is None

    def test_non_json_lines_interleaved_are_skipped_not_fatal(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        jsonl = tmp_path / "cli.log"
        _write_jsonl(jsonl, [
            "codex startup banner (not json)",
            {"type": "thread.started", "thread_id": CLI_THREAD_ID},
            "reasoning trace noise",
            {"type": "turn.completed", "usage": _CLI_USAGE_FIVE_COUNT},
        ])

        r = _run_cli_usage_directly(repo, tmp_path / "home", jsonl)
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["anchor"] is True
        assert lines[0]["session"] == CLI_THREAD_ID

    def test_negative_usage_count_degrades_to_parse_error(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        jsonl = tmp_path / "cli.log"
        _write_jsonl(jsonl, [
            {"type": "thread.started", "thread_id": CLI_THREAD_ID},
            {"type": "turn.completed", "usage": {**_CLI_USAGE_FIVE_COUNT, "input_tokens": -1}},
        ])

        r = _run_cli_usage_directly(repo, tmp_path / "home", jsonl)
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["anchor"] is False
        assert lines[0]["reason"] == "parse-error"

    def test_no_active_change_writes_nothing(self, tmp_path):
        """cwd 不在 `feat/<change>` 分支或 change 目录不存在 ⇒ 零写入（同 `--step` 路径契约）。"""
        repo = _init_repo(tmp_path, branch="main", change=None)
        jsonl = tmp_path / "cli.log"
        _write_jsonl(jsonl, [
            {"type": "thread.started", "thread_id": CLI_THREAD_ID},
            {"type": "turn.completed", "usage": _CLI_USAGE_FIVE_COUNT},
        ])

        r = _run_cli_usage_directly(repo, tmp_path / "home", jsonl)
        assert r.returncode == 0, r.stdout + r.stderr
        assert not (repo / "openspec").exists() or not list(
            (repo / "openspec").rglob("token-log.jsonl"))

    def test_missing_jsonl_file_degrades_to_parse_error_without_crashing(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        jsonl = tmp_path / "does-not-exist.log"

        r = _run_cli_usage_directly(repo, tmp_path / "home", jsonl)
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 1
        assert lines[0]["reason"] == "parse-error"

    def test_closed_key_set_matches_root_child_lines(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        jsonl = tmp_path / "cli.log"
        _write_jsonl(jsonl, [
            {"type": "thread.started", "thread_id": CLI_THREAD_ID},
            {"type": "turn.completed", "usage": _CLI_USAGE_FIVE_COUNT},
        ])

        r = _run_cli_usage_directly(repo, tmp_path / "home", jsonl)
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert set(lines[0].keys()) == CODEX_LINE_KEYS_UNDER_TEST


class TestDoneFinalCodexRegression:
    """implement-optimize-codex-workflow-p2-pull · Task 3.4：`--step done-final` 在 Codex 宿主下
    与既有 checkpoint 路径同形（无独立分支），写根 + 子线程行；单线程失败不挡其余行。
    """

    def test_done_final_step_writes_root_and_child_lines(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home = _codex_home(tmp_path)
        _write_rollout_rows(_rollout_path(codex_home, ROOT_ID), [
            _session_meta_row(ROOT_ID, branch="feat/demo-change"),
            _item_completed_subagent_row(ROOT_ID, "turn-r", CHILD_ID, child_path="/root/task1"),
            _token_usage_record_row(ROOT_ID, "turn-1", {"input_tokens": 3, "total_tokens": 3}),
        ])
        _write_rollout_rows(_rollout_path(codex_home, CHILD_ID), [
            _session_meta_row(CHILD_ID, parent=ROOT_ID, branch="feat/demo-change",
                              agent_path="/root/task1", depth=1),
            _token_usage_record_row(CHILD_ID, "turn-1", {"input_tokens": 7, "total_tokens": 7}),
        ])

        r = _run_token_snapshot_directly(repo, tmp_path / "home", "done-final",
                                          extra_env=_codex_extra_env(codex_home, ROOT_ID))
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        assert len(lines) == 2
        by_session = {l["session"]: l for l in lines}
        assert by_session[ROOT_ID]["step"] == "done-final"
        assert by_session[ROOT_ID]["kind"] == "root"
        assert by_session[ROOT_ID]["anchor"] is True
        assert by_session[CHILD_ID]["step"] == "done-final"
        assert by_session[CHILD_ID]["kind"] == "child"
        assert by_session[CHILD_ID]["anchor"] is True

    def test_done_final_child_thread_not_found_does_not_block_root_line(self, tmp_path):
        repo = _init_repo(tmp_path, branch="feat/demo-change", change="demo-change")
        codex_home = _codex_home(tmp_path)
        _write_rollout_rows(_rollout_path(codex_home, ROOT_ID), [
            _session_meta_row(ROOT_ID, branch="feat/demo-change"),
            _item_completed_subagent_row(ROOT_ID, "turn-r", CHILD_ID, child_path="/root/task1"),
            _token_usage_record_row(ROOT_ID, "turn-1", {"input_tokens": 3, "total_tokens": 3}),
        ])
        # CHILD_ID 故意不建 rollout 文件——降级不挡根线程行、不挡收尾。

        r = _run_token_snapshot_directly(repo, tmp_path / "home", "done-final",
                                          extra_env=_codex_extra_env(codex_home, ROOT_ID))
        assert r.returncode == 0, r.stdout + r.stderr

        lines = _token_log_lines(repo, "demo-change")
        by_session = {l["session"]: l for l in lines}
        assert by_session[ROOT_ID]["anchor"] is True
        assert by_session[CHILD_ID]["reason"] == "thread-not-found"
        assert by_session[CHILD_ID]["anchor"] is False
