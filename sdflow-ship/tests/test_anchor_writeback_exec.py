"""执行级单测：直接调用 `anchor_writeback.main()`（非文本层字符串断言）。

`test_anchor_contract.py` 只做文本层契约（SKILL.md 是否指示调用脚本），此前**无任何测试
真跑过** `anchor_writeback.main()` 本身——本文件补齐 brief 第 8 条 MUST 的执行级覆盖：
正例写入 round-trip、脏树守卫、`--allow-dirty` 逃生口、空监视域拒写、`--set` 同批原子写。
"""
import base64
import hashlib
import sys
from pathlib import Path

import pytest

from conftest import commit_all, mkchange

REPO = Path(__file__).resolve().parents[2]
_scripts = str(REPO / "sdflow-ship" / "scripts")
if _scripts not in sys.path:
    sys.path.insert(0, _scripts)
import anchor_writeback as aw  # noqa: E402
import ship_gate as sg  # noqa: E402


def _write_design_change(repo, name="demo"):
    d = mkchange(repo, name)
    (d / "proposal.md").write_text("# proposal\n", encoding="utf-8")
    (d / "design.md").write_text("# design\n", encoding="utf-8")
    (d / "spec-review-report.md").write_text("# report\n", encoding="utf-8")
    return d


def _read_state(path):
    text = path.read_text(encoding="utf-8")
    state, err = sg.parse_ship_gate_frontmatter(text)
    assert err is None, f"frontmatter 解析失败：{err}"
    return state


def test_clean_tree_write_anchor_roundtrip(repo):
    d = _write_design_change(repo)
    commit_all(repo, "seed change")
    aw.main(["--root", str(repo), "--change", "demo",
             "--report", "spec-review-report.md", "--domain", "design"])
    state = _read_state(d / "spec-review-report.md")
    assert "reviewed_sha" in state and len(state["reviewed_sha"]) == 64
    assert "reviewed_manifest" in state
    manifest_bytes = base64.b64decode(state["reviewed_manifest"])
    assert hashlib.sha256(manifest_bytes).hexdigest() == state["reviewed_sha"]


def test_dirty_watch_set_rejects_write(repo, capsys):
    d = _write_design_change(repo)
    commit_all(repo, "seed change")
    (d / "design.md").write_text("# design changed uncommitted\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        aw.main(["--root", str(repo), "--change", "demo",
                 "--report", "spec-review-report.md", "--domain", "design"])
    assert exc.value.code != 0
    assert "未提交改动" in capsys.readouterr().err
    # 报告文件未被改写（拒写是真拒写，非"写了坏值"）
    assert "reviewed_sha" not in (d / "spec-review-report.md").read_text(encoding="utf-8")


def test_allow_dirty_escape_hatch_permits_write(repo):
    d = _write_design_change(repo)
    commit_all(repo, "seed change")
    (d / "design.md").write_text("# design changed uncommitted\n", encoding="utf-8")
    aw.main(["--root", str(repo), "--change", "demo",
             "--report", "spec-review-report.md", "--domain", "design", "--allow-dirty"])
    state = _read_state(d / "spec-review-report.md")
    assert "reviewed_sha" in state and len(state["reviewed_sha"]) == 64


def test_empty_watch_domain_rejects_write(repo, capsys):
    # 仓内只有 openspec/ 一个顶层条目：--domain code 排除 openspec 后监视域为空集。
    d = mkchange(repo)
    (d / "spec-review-report.md").write_text("# report\n", encoding="utf-8")
    commit_all(repo, "seed change, only openspec at top level")
    with pytest.raises(SystemExit) as exc:
        aw.main(["--root", str(repo), "--change", "demo",
                 "--report", "spec-review-report.md", "--domain", "code"])
    assert exc.value.code != 0
    assert "空集" in capsys.readouterr().err


def test_set_flag_writes_conclusion_and_anchor_atomically(repo):
    d = _write_design_change(repo)
    commit_all(repo, "seed change")
    aw.main(["--root", str(repo), "--change", "demo",
             "--report", "spec-review-report.md", "--domain", "design",
             "--set", "design_approved=true"])
    state = _read_state(d / "spec-review-report.md")
    assert state.get("design_approved") is True
    assert "reviewed_sha" in state and len(state["reviewed_sha"]) == 64
    assert "reviewed_manifest" in state
