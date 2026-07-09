import importlib.util
import os
import subprocess
import sys
import textwrap

import pytest

SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts", "maintain_scan.py",
)


def _load():
    spec = importlib.util.spec_from_file_location("maintain_scan", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ms = _load()

MANAGED_START = "<!-- opsx-init:rules:start —— 由 sdflow-init 维护，勿手改本区块 -->"
MANAGED_END = "<!-- opsx-init:rules:end -->"


def make_repo(tmp_path, specs=(), rules=None, index_body=None,
              claude=None, workflow=(), managed_entries=(), has_git=True):
    """造最小 openspec 仓：specs=spec 名列表；rules=None 表示不建 rules/ 目录（可选目录缺失）,
    []/列表表示建目录并放对应 .md；index_body=None 表示不建 INDEX.md（缺失场景）。"""
    root = tmp_path
    if has_git:
        (root / ".git").mkdir()
    osp = root / "openspec"
    osp.mkdir()
    (osp / "specs").mkdir()
    for name in specs:
        d = osp / "specs" / name
        d.mkdir()
        (d / "spec.md").write_text("# spec\n", encoding="utf-8")
    if rules is not None:
        (osp / "rules").mkdir()
        for name in rules:
            (osp / "rules" / f"{name}.md").write_text("# rule\n", encoding="utf-8")
    if index_body is not None:
        managed = ""
        if managed_entries:
            rows = "\n".join(
                f"| `{n}` | [workflow/{n}.md](./workflow/{n}.md) | x |"
                for n in managed_entries
            )
            managed = f"{MANAGED_START}\n{rows}\n{MANAGED_END}\n"
        (osp / "INDEX.md").write_text(
            f"# OpenSpec Index\n\n{managed}{index_body}\n", encoding="utf-8"
        )
    if claude is not None:
        (root / "CLAUDE.md").write_text(claude, encoding="utf-8")
    if workflow:
        wf = osp / "workflow"
        wf.mkdir()
        for f in workflow:
            (wf / f).write_text("x\n", encoding="utf-8")
    return str(root)


def test_error_type_exists():
    assert issubclass(ms.MaintainScanError, Exception)


def test_missing_git_root_raises(tmp_path):
    with pytest.raises(ms.MaintainScanError):
        ms.find_repo_root(str(tmp_path))


def _run(root):
    return ms.run_scan(root)


def test_new_unindexed_spec(tmp_path):
    root = make_repo(tmp_path, specs=["foo"], rules=[], index_body="")
    r = _run(root)
    assert "新增未索引" in r and "foo" in r


def test_stale_indexed_rule(tmp_path):
    body = "| `bar` | [rules/bar.md](./rules/bar.md) | x |"
    root = make_repo(tmp_path, specs=[], rules=[], index_body=body)
    r = _run(root)
    assert "已删未清理" in r and "bar" in r


def test_fully_consistent(tmp_path):
    body = "| `foo` | [specs/foo/spec.md](./specs/foo/spec.md) | x |"
    root = make_repo(tmp_path, specs=["foo"], rules=[], index_body=body)
    r = _run(root)
    assert "一致" in r


def test_managed_block_entries_not_stale(tmp_path):
    # 托管块内列 trigger-catalog（无对应 rules/rule 文件），MUST NOT 报「已删未清理」
    root = make_repo(tmp_path, specs=[], rules=[], index_body="",
                     managed_entries=["trigger-catalog"])
    r = _run(root)
    assert "trigger-catalog" not in r


def test_non_spec_link_row_excluded(tmp_path):
    # retro-report → retro/report.md 既非 specs 也非 rules，MUST NOT 参与 set-diff
    body = "| `retro-report` | [retro/report.md](./retro/report.md) | x |"
    root = make_repo(tmp_path, specs=[], rules=[], index_body=body)
    r = _run(root)
    assert "retro-report" not in r
    assert "已删未清理" not in r or "无" in r


def test_managed_marker_unpaired_fails(tmp_path):
    # 只有 start 无 end → 结构不可信 → 非零退出（防假一致）
    idx = f"# I\n\n{MANAGED_START}\n| `x` | [rules/x.md](./rules/x.md) | y |\n"
    root = make_repo(tmp_path, specs=[], rules=[], index_body="")
    import pathlib
    pathlib.Path(root, "openspec", "INDEX.md").write_text(idx, encoding="utf-8")
    with pytest.raises(ms.MaintainScanError):
        ms.run_scan(root)
