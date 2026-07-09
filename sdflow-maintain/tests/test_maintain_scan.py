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
