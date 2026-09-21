"""Task 5（implement-optimize-codex-workflow-p2-pull）：假 HOME 安装矩阵 + 耗时实测。

【范围】ticket brief 交付行为 1 与 3（交付行为 2「三类在线验收」需要真实 Codex CLI 会话，
本机（Claude Code）无法在线产出，见 impl-reports/task5-install-verify.md 的归档样本段落，
该验收标准如实保持未完成）。

1. 假 HOME 真跑 `bash setup.sh`：断言 `~/.sdflow/hack/token_snapshot.py` /
   `outside-voice.sh` 是本次 change 加的新版（含 codex 分支 / `ov_collect_cli_usage`），
   且真实 `~/.claude`、`~/.codex`、`~/.sdflow` 三个全局目录未被本次测试触碰
   （沿用 `test_install_agents.py` 的 fake-HOME + 快照护栏模式）。
2. scratch 消费仓 `sdflow-init` update 二次无差异（`copy_bundle` 不铺 hack 脚本，
   该断言是通用 update 幂等回归，不特定于本 change 的 codex 采集内容）。
3. [e2e] 耗时实测：构造含 ≥10 子线程的假 Codex rollout 场景，真跑
   `token_snapshot.py --step <s>`，断言总耗时 < 10 秒硬 deadline 并打印实测数字
   （`pytest -s` 可见；具体数字贴在 impl-report）。

不跑真实 `setup.sh` 以外的全局路径——scratch 消费仓测试用 `run(root, "update")` 直接调用
`sdflow-init/scripts/init.py`（CLAUDE.md「开发期测试三层」第 1/2 层，零全局影响）。
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from test_support.windows import bash_executable, bash_path

if os.name == "nt":
    pytest.skip(
        "本文件的假 HOME + bash setup.sh 组合针对 Unix 软链/拷贝语义；"
        "Windows 分支（copy+marker）本机测不到，见 test_install_agents.py 同一诚实边界声明",
        allow_module_level=True,
    )

REPO = Path(__file__).resolve().parents[2]
SETUP = REPO / "setup.sh"
TOKEN_SNAPSHOT_SRC = REPO / "sdflow-init" / "assets" / "hack" / "token_snapshot.py"
OUTSIDE_VOICE_SRC = REPO / "sdflow-init" / "assets" / "hack" / "outside-voice.sh"

REAL_HOME = Path(os.path.expanduser("~"))
REAL_CLAUDE = REAL_HOME / ".claude"
REAL_CODEX = REAL_HOME / ".codex"
REAL_SDFLOW = REAL_HOME / ".sdflow"


# ---------------------------------------------------------------------------
# 1. 假 HOME 安装矩阵
# ---------------------------------------------------------------------------

def _snapshot_dir(path):
    """(相对路径 → 软链目标 / "<file>" / "<dir>") 的浅层快照；目录不存在 → None。

    只走一层（顶层条目），足以发现"新增/删除/软链目标改变"这类被测代码若误写真实 HOME
    会留下的痕迹；不递归内容字节（那些目录里躺着人机器上真实的技能/凭据，不应被本测试读取）。
    """
    if not path.is_dir():
        return None
    out = {}
    for p in sorted(path.iterdir()):
        if p.is_symlink():
            out[p.name] = ("symlink", os.readlink(p))
        elif p.is_dir():
            out[p.name] = ("dir", None)
        else:
            out[p.name] = ("file", None)
    return out


@pytest.fixture
def real_home_untouched_guard():
    """跑前后各拍一次真实 `~/.claude`、`~/.codex`、`~/.sdflow` 快照——任何一个被本测试
    动过就红。这是本用例矩阵存在的核心理由：假 HOME 场景下 `install_sdflow` /
    `install_into` 里任何一处不走 `$HOME` 的绝对路径都会在这里暴露。
    """
    before = {
        "claude": _snapshot_dir(REAL_CLAUDE),
        "codex": _snapshot_dir(REAL_CODEX),
        "sdflow": _snapshot_dir(REAL_SDFLOW),
    }
    yield
    after = {
        "claude": _snapshot_dir(REAL_CLAUDE),
        "codex": _snapshot_dir(REAL_CODEX),
        "sdflow": _snapshot_dir(REAL_SDFLOW),
    }
    assert after == before, (
        "真实 ~/.claude / ~/.codex / ~/.sdflow 被测试改动了 —— "
        "假 HOME 场景下 setup.sh 有不走 $HOME 的路径"
    )


def _run_setup_with_fake_home(home):
    env = dict(os.environ)
    env["HOME"] = str(home)
    env.pop("SDFLOW_HOME", None)  # 否则会写到真实 ~/.sdflow
    env.pop("CODEX_HOME", None)
    return subprocess.run(
        [bash_executable(), bash_path(SETUP)], cwd=str(REPO), env=env,
        capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace",
    )


class TestFakeHomeInstallMatrix:
    def test_v2_helpers_deployed_and_real_home_untouched(self, tmp_path, real_home_untouched_guard):
        home = tmp_path / "home"
        home.mkdir()

        r = _run_setup_with_fake_home(home)
        assert r.returncode == 0, r.stdout + r.stderr

        deployed_snapshot = home / ".sdflow" / "hack" / "token_snapshot.py"
        deployed_ov = home / ".sdflow" / "hack" / "outside-voice.sh"
        assert deployed_snapshot.is_file(), "token_snapshot.py 未装到假 ~/.sdflow/hack/"
        assert deployed_ov.is_file(), "outside-voice.sh 未装到假 ~/.sdflow/hack/"

        snapshot_text = deployed_snapshot.read_text(encoding="utf-8")
        ov_text = deployed_ov.read_text(encoding="utf-8")

        # 新版标志：codex 分支的私有函数名（源文件真相源同一批字符串，见 design.md）。
        for marker in (
            "_codex_collect_and_write", "_project_codex_rollout", "_project_cli_usage",
            "SCHEMA_VERSION_V2", "--cli-usage",
        ):
            assert marker in snapshot_text, f"部署的 token_snapshot.py 缺新版标志 {marker!r}"

        for marker in ("ov_collect_cli_usage", "--json"):
            assert marker in ov_text, f"部署的 outside-voice.sh 缺新版标志 {marker!r}"

        # 部署内容与源文件逐字节一致（拷贝，不是别的什么半吊子版本）。
        assert snapshot_text == TOKEN_SNAPSHOT_SRC.read_text(encoding="utf-8")
        assert ov_text == OUTSIDE_VOICE_SRC.read_text(encoding="utf-8")

    def test_idempotent_rerun_keeps_v2_helpers(self, tmp_path, real_home_untouched_guard):
        """重跑一次（模拟 pull 之后二次 setup）：新版仍在，且真实 HOME 依旧未被碰。"""
        home = tmp_path / "home"
        home.mkdir()
        r1 = _run_setup_with_fake_home(home)
        assert r1.returncode == 0, r1.stdout + r1.stderr
        r2 = _run_setup_with_fake_home(home)
        assert r2.returncode == 0, r2.stdout + r2.stderr

        deployed = home / ".sdflow" / "hack" / "token_snapshot.py"
        assert "_codex_collect_and_write" in deployed.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 2. scratch 消费仓 update 二次无差异
# ---------------------------------------------------------------------------

def _run_sdflow_init(root, mode, home):
    """在子进程里跑 `sdflow-init/scripts/init.py <mode> --root <root>`，
    `CLAUDE_CONFIG_DIR` 重定向到假 home，避免 `ensure_global_hooks()` 碰真实 `~/.claude`。
    """
    env = dict(os.environ)
    env["CLAUDE_CONFIG_DIR"] = str(home / ".claude")
    env.pop("HOME_OVERRIDE", None)
    script = REPO / "sdflow-init" / "scripts" / "init.py"
    return subprocess.run(
        [sys.executable, str(script), mode, "--root", str(root)],
        cwd=str(root), env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=60,
    )


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestScratchConsumerUpdateIdempotent:
    """`copy_bundle` 明写「hack 脚本不再铺进仓」（init.py `run()` 的 report 一行）——
    scratch 消费仓的 update 幂等性因此与本 change 的 codex 采集内容无关，是通用 update
    回归；ticket brief 交付行为 1 明确要求覆盖，一并做在这里。
    """

    def test_update_twice_produces_no_diff(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        repo = tmp_path / "consumer"
        repo.mkdir()
        _git(repo, "init", "-q")
        _git(repo, "config", "user.email", "t@t")
        _git(repo, "config", "user.name", "t")

        r_init = _run_sdflow_init(repo, "init", home)
        assert r_init.returncode == 0, r_init.stdout + r_init.stderr
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "init")

        r_update1 = _run_sdflow_init(repo, "update", home)
        assert r_update1.returncode == 0, r_update1.stdout + r_update1.stderr
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "update1", "--allow-empty")

        r_update2 = _run_sdflow_init(repo, "update", home)
        assert r_update2.returncode == 0, r_update2.stdout + r_update2.stderr

        status = _git(repo, "status", "--porcelain").stdout
        assert status.strip() == "", f"二次 update 产生了差异：\n{status}"


# ---------------------------------------------------------------------------
# 3. [e2e] helper 耗时实测（含 ≥10 子线程场景）
# ---------------------------------------------------------------------------

ROOT_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1"
NUM_CHILDREN = 12  # 验收要求 ≥10


def _row(rtype, payload, ts="2026-09-21T00:00:00.000Z"):
    return {"timestamp": ts, "ordinal": 0, "type": rtype, "payload": payload}


def _session_meta_row(thread_id, parent=None, branch=None, agent_path=None, depth=0):
    payload = {"id": thread_id, "session_id": thread_id, "cli_version": "0.155.0"}
    if parent is not None:
        payload["parent_thread_id"] = parent
    if branch is not None:
        payload["git"] = {"branch": branch}
    if agent_path is not None:
        payload["agent_path"] = agent_path
        payload["source"] = {"subagent": {"thread_spawn": {"depth": depth, "agent_path": agent_path}}}
    return _row("session_meta", payload)


_ZERO_USAGE = {
    "input_tokens": 0, "cached_input_tokens": 0, "cache_write_input_tokens": 0,
    "output_tokens": 0, "reasoning_output_tokens": 0, "total_tokens": 0,
}


def _token_usage_record_row(thread_id, turn_id, usage_overrides, ts="2026-09-21T00:00:02.000Z"):
    tu = dict(_ZERO_USAGE)
    tu.update(usage_overrides)
    return _row("token_usage_record", {
        "thread_id": thread_id, "turn_id": turn_id, "session_id": thread_id,
        "root_turn_id": turn_id, "response_id": "resp_x",
        "usage": tu, "turn_token_usage": tu, "thread_token_usage": tu,
    }, ts=ts)


def _item_completed_subagent_row(thread_id, turn_id, child_id, child_path):
    return _row("event_msg", {
        "type": "item_completed", "thread_id": thread_id, "turn_id": turn_id,
        "started_at_ms": 0, "completed_at_ms": 0,
        "item": {"type": "SubAgentActivity", "id": f"call_{child_id}", "kind": "started",
                  "agent_thread_id": child_id, "agent_path": child_path},
    })


def _write_rollout_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _rollout_path(codex_home, thread_id):
    d = codex_home / "sessions" / "2026" / "09" / "21"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"rollout-2026-09-21T00-00-00-{thread_id}.jsonl"


def _child_id(i):
    return f"cccccccc-{i:04d}-4ccc-8ccc-ccccccccccc1"


class TestHelperTimingWithChildren:
    """构造 root + 12 个子线程（design.md 非功能需求：单次 helper 调用 10 秒硬 deadline）。

    `token_snapshot.py --step <s>` 直接子进程调用（沿用 `test_token_snapshot.py` 的
    `_run_token_snapshot_directly` 模式），真实测量墙钟。
    """

    def test_twelve_children_within_deadline(self, tmp_path, capsys):
        home = tmp_path / "home"
        (home / ".sdflow" / "hack").mkdir(parents=True)
        os.symlink(str(TOKEN_SNAPSHOT_SRC), home / ".sdflow" / "hack" / "token_snapshot.py")

        repo = tmp_path / "repo"
        change_dir = repo / "openspec" / "changes" / "demo-change"
        change_dir.mkdir(parents=True)
        _git(repo, "init", "-q")
        _git(repo, "config", "user.email", "t@t")
        _git(repo, "config", "user.name", "t")
        _git(repo, "checkout", "-q", "-b", "feat/demo-change")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "init")

        codex_home = tmp_path / "codexhome"
        (codex_home / "sessions").mkdir(parents=True)

        child_ids = [_child_id(i) for i in range(NUM_CHILDREN)]
        root_rows = [
            _session_meta_row(ROOT_ID, branch="feat/demo-change"),
        ]
        for i, cid in enumerate(child_ids):
            root_rows.append(_item_completed_subagent_row(ROOT_ID, "turn1", cid, f"/root/task{i}"))
        root_rows.append(_token_usage_record_row(ROOT_ID, "turn1", {"input_tokens": 100}))
        _write_rollout_rows(_rollout_path(codex_home, ROOT_ID), root_rows)

        for cid in child_ids:
            child_rows = [
                _session_meta_row(cid, parent=ROOT_ID, branch="feat/demo-change",
                                   agent_path=f"/root/{cid}", depth=1),
                _token_usage_record_row(cid, "turn1", {"input_tokens": 10, "output_tokens": 5}),
            ]
            _write_rollout_rows(_rollout_path(codex_home, cid), child_rows)

        env = dict(os.environ)
        env["HOME"] = str(home)
        env.pop("SDFLOW_HOME", None)
        env["CLAUDECODE"] = ""
        env.pop("CLAUDECODE", None)
        env["CODEX_THREAD_ID"] = ROOT_ID
        env["CODEX_HOME"] = str(codex_home)

        start = time.monotonic()
        r = subprocess.run(
            ["python3", str(TOKEN_SNAPSHOT_SRC), "--step", "e2e-timing"],
            cwd=str(repo), env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=60,
        )
        elapsed = time.monotonic() - start

        assert r.returncode == 0, r.stdout + r.stderr

        log_path = change_dir / "token-log.jsonl"
        lines = [json.loads(l) for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        # root 1 行 + 12 个子线程各 1 行
        assert len(lines) == 1 + NUM_CHILDREN, f"期望 13 行，实得 {len(lines)}：{lines}"
        anchored = [l for l in lines if l.get("anchor") is True]
        assert len(anchored) == 1 + NUM_CHILDREN, f"期望全部 anchor=true：{lines}"

        with capsys.disabled():
            print(f"\n[e2e] token_snapshot.py --step e2e-timing "
                  f"(root + {NUM_CHILDREN} children) 实测耗时: {elapsed:.4f}s")

        assert elapsed < 10.0, f"超过 10 秒硬 deadline：{elapsed:.4f}s"
