"""真实 CLI 测试使用项目根目录，运行产物放进 .test/，不改用户信任配置。

运行前需由用户信任项目根目录。普通离线测试继续使用自己的 tmp_path。
"""

import tempfile
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]


def pytest_collection_modifyitems(items):
    # 仓根 conftest 在每个用例 setup 前快照顶层条目；必须在 collection 阶段准备根目录。
    if any("real_cli_repo" in item.fixturenames for item in items):
        (REPO / ".test").mkdir(mode=0o700, exist_ok=True)


@pytest.fixture
def real_cli_repo():
    """固定工作区满足 CLI 信任前置，每轮新建目录避免并行或重复运行互相覆盖。"""
    scratch = REPO / ".test" / "outside-voice" / "codex-to-claude"
    scratch.mkdir(mode=0o700, parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix="run-", dir=scratch))
    ctx = run_dir / "design-voice-context.md"
    ctx.write_text("some evidence context\n", encoding="utf-8")
    # 保留运行证据供失败诊断；.test/ 整体 gitignored，不进入 checkpoint 提交。
    return {"root": REPO, "run_dir": run_dir, "ctx": ctx}
