"""真实 CLI 测试使用项目根目录，运行产物放进 .test/，不改用户信任配置。

运行前需由用户信任项目根目录；未信任时（如发布快照、使用者新 clone）显式 skip。
普通离线测试继续使用自己的 tmp_path。
"""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]


def pytest_collection_modifyitems(items):
    # 仓根 conftest 在每个用例 setup 前快照顶层条目；必须在 collection 阶段准备根目录。
    if any("real_cli_repo" in item.fixturenames for item in items):
        (REPO / ".test").mkdir(mode=0o700, exist_ok=True)


def _skip_if_workspace_untrusted():
    """信任与否让 claude 自己回答：跑一条无模型的 `--bg --exec true`，报未信任即 skip。"""
    claude = shutil.which("claude")
    probe = subprocess.run(
        [claude, "--bg", "--exec", "true"],
        capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace",
        cwd=REPO)
    if probe.returncode != 0 and "not trusted" in probe.stderr:
        pytest.skip(f"项目根未被 claude 信任（{REPO}）：在该目录跑一次 `claude` 接受信任提示后重跑")
    match = re.search(r"backgrounded\W+([0-9a-f]{6,40})\b", probe.stdout or "")
    if match:
        subprocess.run([claude, "rm", match.group(1)], capture_output=True, timeout=60, cwd=REPO)


@pytest.fixture(autouse=True)
def _isolate_claude_config_dir(request, monkeypatch, tmp_path_factory):
    """init.run() 无条件调 ensure_global_hooks()，未设 CLAUDE_CONFIG_DIR 时落到真实 ~/.claude。

    默认把它指向每用例独立的临时目录；用例自己 setenv/delenv 可覆盖。
    用 real_cli_repo 的用例不重定向：真 CLI 要读真实配置里的工作区信任，且这些用例不调 init.run。
    """
    if "real_cli_repo" in request.fixturenames:
        return
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path_factory.mktemp("claude-config")))


@pytest.fixture
def real_cli_repo():
    """固定工作区满足 CLI 信任前置，每轮新建目录避免并行或重复运行互相覆盖。"""
    _skip_if_workspace_untrusted()
    scratch = REPO / ".test" / "outside-voice" / "codex-to-claude"
    scratch.mkdir(mode=0o700, parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix="run-", dir=scratch))
    ctx = run_dir / "design-voice-context.md"
    ctx.write_text("some evidence context\n", encoding="utf-8")
    # 保留运行证据供失败诊断；.test/ 整体 gitignored，不进入 checkpoint 提交。
    return {"root": REPO, "run_dir": run_dir, "ctx": ctx}
