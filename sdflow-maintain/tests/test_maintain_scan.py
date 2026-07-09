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


def test_broken_link_target_fails(tmp_path):
    # 判据③：块外表体行含链接语法 "](" 但 target 解析不出路径（空 target）→ fail-closed
    body = "| `x` | [x]() | y |"
    root = make_repo(tmp_path, specs=[], rules=[], index_body=body)
    with pytest.raises(ms.MaintainScanError):
        ms.run_scan(root)


def test_broken_link_target_unclosed_fails(tmp_path):
    # 判据③：未闭合链接语法（缺右括号）同样是 target 解析不出路径 → fail-closed
    body = "| `x` | [x](broken-link-no-close | y |"
    root = make_repo(tmp_path, specs=[], rules=[], index_body=body)
    with pytest.raises(ms.MaintainScanError):
        ms.run_scan(root)


def test_non_spec_link_still_excluded_not_fail(tmp_path):
    # ③ 不误伤 ②b：合法非-spec/rule 链接照常静默排除，不应被误判为「target 解析不出路径」
    body = "| `retro-report` | [retro/report.md](./retro/report.md) | x |"
    root = make_repo(tmp_path, specs=[], rules=[], index_body=body)
    r = _run(root)
    assert "retro-report" not in r
    assert "一致" in r


def test_managed_marker_unpaired_fails(tmp_path):
    # 只有 start 无 end → 结构不可信 → 非零退出（防假一致）
    idx = f"# I\n\n{MANAGED_START}\n| `x` | [rules/x.md](./rules/x.md) | y |\n"
    root = make_repo(tmp_path, specs=[], rules=[], index_body="")
    import pathlib
    pathlib.Path(root, "openspec", "INDEX.md").write_text(idx, encoding="utf-8")
    with pytest.raises(ms.MaintainScanError):
        ms.run_scan(root)


def test_claude_stale_ref_reported(tmp_path):
    # INDEX 列 gone（spec 类）但 fs 无 → gone 进已删集；CLAUDE.md 引 gone → 报
    body = "| `gone` | [specs/gone/spec.md](./specs/gone/spec.md) | x |"
    claude = "见 openspec/specs/gone/spec.md 的定义\n"
    root = make_repo(tmp_path, specs=[], rules=[], index_body=body, claude=claude)
    r = _run(root)
    assert "过时引用" in r and "gone" in r and "CLAUDE.md" in r


def test_claude_placeholder_generic_fence_not_reported(tmp_path):
    body = "| `gone` | [specs/gone/spec.md](./specs/gone/spec.md) | x |"
    claude = textwrap.dedent("""\
        占位: openspec/roadmaps/{name}/ 是活文档
        泛指: openspec/specs/ 目录
        ```
        围栏举例: openspec/specs/gone/spec.md
        ```
        """)
    root = make_repo(tmp_path, specs=[], rules=[], index_body=body, claude=claude)
    r = _run(root)
    # gone 仍是已删集，但 CLAUDE 里只有占位/泛指/围栏 → 不报 CLAUDE 过时引用
    assert "过时引用" not in r or "CLAUDE.md" not in r.split("过时引用")[1].split("陈旧遮蔽")[0]


def test_claude_unreadable_fails(tmp_path):
    # scan_claude_refs 的 except (OSError, UnicodeDecodeError): raise MaintainScanError
    # 无测试覆盖；用非法 UTF-8 字节（可移植，优于 chmod 000 在 root/CI 下不可靠）触发 UnicodeDecodeError。
    body = "| `gone` | [specs/gone/spec.md](./specs/gone/spec.md) | x |"
    root = make_repo(tmp_path, specs=[], rules=[], index_body=body)
    claude_path = os.path.join(root, "CLAUDE.md")
    with open(claude_path, "wb") as f:
        f.write(b"\xff\xfe bad bytes")
    with pytest.raises(ms.MaintainScanError):
        ms.run_scan(root)


def test_placeholder_in_specs_domain_not_reported(tmp_path):
    # 占位符 {name} 落在 specs/rules 匹配域内（非 test_claude_placeholder_generic_fence_not_reported
    # 用的 roadmaps 前缀，那个前缀本就不在 specs|rules 域，未真正验证剥除逻辑）。
    # 对照行（真实引用 openspec/specs/gone/spec.md）证明扫描确实在跑，只是占位符那行被排除。
    body = "| `gone` | [specs/gone/spec.md](./specs/gone/spec.md) | x |"
    claude = textwrap.dedent("""\
        见 openspec/specs/{name}/spec.md 模板
        见 openspec/specs/gone/spec.md 的定义
        """)
    root = make_repo(tmp_path, specs=[], rules=[], index_body=body, claude=claude)
    r = _run(root)
    assert "过时引用" in r and "gone" in r
    claude_section = r.split("过时引用")[1]
    # 占位符行（第1行）剥除后 "openspec/specs//spec.md" 不匹配 <name> 域 → 不应产生命中
    assert "CLAUDE.md:1:" not in claude_section
    # 对照：真实引用行（第2行）必须被报，证明扫描确实在工作
    assert "CLAUDE.md:2:" in claude_section


def test_stale_shadow_workflow_body(tmp_path):
    body = ""
    root = make_repo(tmp_path, specs=[], rules=[], index_body=body,
                     workflow=["workflow.md"])
    r = _run(root)
    assert "陈旧遮蔽" in r and "workflow.md" in r


def test_stale_shadow_only_tools_clean(tmp_path):
    root = make_repo(tmp_path, specs=[], rules=[], index_body="")
    wf = os.path.join(root, "openspec", "workflow", "tools")
    os.makedirs(wf)
    open(os.path.join(wf, "anchor_lint.py"), "w").write("x")
    r = _run(root)
    # 陈旧遮蔽节存在但无残留规则本体
    seg = r.split("陈旧遮蔽")[1]
    assert "workflow.md" not in seg and "spec-checklists" not in seg
