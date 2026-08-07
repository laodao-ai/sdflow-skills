import importlib.util
import os
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
            # [impl-review-fix] 链接形态改为 rules/{n}.md（命中 _RULE_LINK），使
            # test_managed_block_entries_not_stale 真依赖 split_managed_block 的剥离——
            # 原 workflow/{n}.md 形态不命中 _SPEC_LINK/_RULE_LINK，split_managed_block
            # 换 no-op 该测试仍会过（假绿）。
            rows = "\n".join(
                f"| `{n}` | [rules/{n}.md](./rules/{n}.md) | x |"
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
    # 托管块内列 trigger-catalog，链接形态命中 _RULE_LINK（rules/trigger-catalog.md，无对应
    # rules/ 文件）。若 split_managed_block 未真正剥离该块，parse_index_entries 会把它计入
    # rules 集 → 因 fs 无对应文件而报「已删未清理」。MUST NOT 报，真依赖块被剥离（非假绿）。
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


def test_stale_shadow_lens_metric_contract_now_reports_dead_file(tmp_path):
    # [fix-probe-scan-precision task 4.1/4.3] 判据扩员：lens-metric-contract.md 残留同为死件。
    root = make_repo(tmp_path, specs=[], rules=[], index_body="")
    wf = os.path.join(root, "openspec", "workflow")
    os.makedirs(wf)
    with open(os.path.join(wf, "lens-metric-contract.md"), "w") as f:
        f.write("# contract\n")
    r = _run(root)
    seg = r.split("陈旧遮蔽")[1]
    assert "死件" in seg and "lens-metric-contract.md" in seg


def test_stale_shadow_message_wording_positive_and_negative(tmp_path):
    # [fix-probe-scan-precision task 4.4] 文案双断言：不含旧「显式 pin」/「遮蔽全局」措辞，
    # 含新死件关键词 + 前置条件提示 + 可复制删除命令。
    root = make_repo(tmp_path, specs=[], rules=[], index_body="",
                     workflow=["workflow.md"])
    import pathlib
    hack = pathlib.Path(root, "hack")
    hack.mkdir()
    (hack / "checkpoint-commit.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    r = _run(root)
    seg = r.split("陈旧遮蔽")[1]
    assert "显式 pin" not in seg
    assert "遮蔽全局" not in seg
    assert "死件" in seg
    assert "bash setup.sh" in seg
    assert "rm -rf" in seg and "rm -f" in seg


def test_stale_shadow_only_tools_now_reports_dead_file(tmp_path):
    # [fix-probe-scan-precision task 4.3] 断言反转：resolver 两步链取消仓内优先后，
    # tools/-only 残留（无 RULE_MARKERS 规则本体）本身即死件，SHALL 报死件告警——
    # 旧断言"只 tools 残留 = 干净"已随判据扩员成立前提消失。
    root = make_repo(tmp_path, specs=[], rules=[], index_body="")
    wf = os.path.join(root, "openspec", "workflow", "tools")
    os.makedirs(wf)
    with open(os.path.join(wf, "anchor_lint.py"), "w") as f:
        f.write("x")
    r = _run(root)
    seg = r.split("陈旧遮蔽")[1]
    assert "死件" in seg and "tools" in seg


def test_stale_shadow_present_not_reported_consistent(tmp_path):
    # 结构完好、set-diff 全空，但 workflow/ 残留规则副本 → 不应输出「一致，无差异」
    # （has_diff 须纳入 stale_shadow，否则「陈旧遮蔽」与「一致」自相矛盾）
    root = make_repo(tmp_path, specs=[], rules=[], index_body="",
                     workflow=["workflow.md"])
    r = _run(root)
    assert "一致，无差异" not in r


def test_index_missing_nonzero(tmp_path):
    root = make_repo(tmp_path, specs=["foo"], rules=[], index_body=None)  # 无 INDEX.md
    rc = ms.main(["--root", root])
    assert rc != 0


def test_specs_dir_missing_nonzero(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "openspec").mkdir()
    (tmp_path / "openspec" / "INDEX.md").write_text("# I\n", encoding="utf-8")
    rc = ms.main(["--root", str(tmp_path)])
    assert rc != 0


def test_zero_entries_index_is_ok_not_fail(tmp_path):
    # 结构完好、0 条 spec 条目 → 退出 0 + 全部报新增未索引（响亮，非 fail）
    root = make_repo(tmp_path, specs=["foo", "baz"], rules=[], index_body="")
    rc = ms.main(["--root", root])
    assert rc == 0
    r = _run(root)
    assert "foo" in r and "baz" in r


def test_rules_dir_missing_is_ok(tmp_path):
    body = "| `foo` | [specs/foo/spec.md](./specs/foo/spec.md) | x |"
    root = make_repo(tmp_path, specs=["foo"], rules=None, index_body=body)  # 无 rules/
    rc = ms.main(["--root", root])
    assert rc == 0


def _snapshot(root):
    """os.walk 收集 root 下全部文件的 {相对路径: 字节内容}，跳过 .git（make_repo 造的是
    mkdir 出的假 .git，本就无实质内容，但仍显式排除以稳妥）。用于只读不变量断言：
    脚本运行前后快照必须逐字节相等，否则说明脚本写/改了文件（真 load-bearing，
    不像原先依赖假 .git 令 `git status` 恒空的假绿写法）。"""
    snap = {}
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirnames:
            dirnames.remove(".git")
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            rel = os.path.relpath(fpath, root)
            with open(fpath, "rb") as f:
                snap[rel] = f.read()
    return snap


def test_readonly_no_file_writes(tmp_path):
    # bar 新增未索引、foo 已删未清理 —— 让 run_scan 有实际差异可报，而非空转
    root = make_repo(tmp_path, specs=["bar"], rules=[],
                     index_body="| `foo` | [specs/foo/spec.md](./specs/foo/spec.md) | x |")
    before = _snapshot(root)
    ms.run_scan(root)
    after = _snapshot(root)
    assert before == after


# [impl-review-fix] Fix-1: 三处 fence 状态机（split_managed_block / parse_index_entries /
# scan_claude_refs）未闭合 ``` fail-closed。以下三条测试各打一处；INDEX 侧两个函数共享同一份
# 输入行序列，数学上「split 干净通过」蕴含「喂给 parse_index_entries 的 body 围栏也balanced」
# （成对 marker 检测要求 marker 间围栏必为偶数次切换，偶+偶=偶），故 parse_index_entries 自身
# 兜底无法经完整 INDEX 文本间接逼出——用直接单测喂 body_lines 证明该层独立可达、非死代码。

def test_index_unclosed_fence_fails(tmp_path):
    # INDEX.md 含未闭合 ``` → split_managed_block 扫到文档尾 in_fence 仍 True → fail-closed
    # （防「未闭合围栏后内容被静默当围栏跳过 → 假一致」，design D2）。
    body = (
        "```\n未闭合围栏，其后内容本应可见\n"
        "| `foo` | [specs/foo/spec.md](./specs/foo/spec.md) | x |"
    )
    root = make_repo(tmp_path, specs=["foo"], rules=[], index_body=body)
    with pytest.raises(ms.MaintainScanError):
        ms.run_scan(root)
    rc = ms.main(["--root", root])
    assert rc != 0


def test_split_managed_block_unclosed_fence_fails():
    # split_managed_block 自身状态机 fail-closed——直接单测（见上方说明：经完整 INDEX 文本
    # 间接触发时会被 parse_index_entries 同样兜底，此分支需直调 split_managed_block 才能
    # 确保该层独立可达、非死代码；删 split 的 raise 时本测试 MUST 失败）。
    index_text = (
        "# INDEX\n"
        "\n"
        "```\n"
        "未闭合围栏，其后内容应被报错阻止处理\n"
    )
    with pytest.raises(ms.MaintainScanError):
        ms.split_managed_block(index_text)


def test_parse_index_entries_unclosed_fence_fails():
    # parse_index_entries 自身状态机同样兜底——直接单测（见上方说明：经完整 INDEX 文本
    # 间接触发时 split_managed_block 会先行拦截，此分支需直喂 body_lines 才能独立验证）。
    body_lines = [
        "| `foo` | [specs/foo/spec.md](./specs/foo/spec.md) | x |",
        "```",
        "未闭合围栏",
    ]
    with pytest.raises(ms.MaintainScanError):
        ms.parse_index_entries(body_lines)


def test_claude_unclosed_fence_fails(tmp_path):
    # 某 CLAUDE.md 含未闭合 ``` → scan_claude_refs 状态机同样 fail-closed
    body = "| `foo` | [specs/foo/spec.md](./specs/foo/spec.md) | x |"
    claude = "```\n未闭合围栏\n见 openspec/specs/foo/spec.md\n"
    root = make_repo(tmp_path, specs=["foo"], rules=[], index_body=body, claude=claude)
    with pytest.raises(ms.MaintainScanError):
        ms.run_scan(root)


def test_mgr_warns_not_consistent(tmp_path):
    # [impl-review-fix] Fix-2 + Fix-6②: mgr_warns（疑似 spec 条目误置托管块内，M8/D11）
    # MUST 纳入 has_diff 判定——把一条 specs 链接误放进 opsx-init:rules 托管块内、其余全一致，
    # 报告 MUST 出现该告警且 MUST NOT 同时输出「一致，无差异」（否则告警与「一致」自相矛盾）。
    idx = (
        f"# I\n\n{MANAGED_START}\n"
        "| `foo` | [specs/foo/spec.md](./specs/foo/spec.md) | x |\n"
        f"{MANAGED_END}\n"
    )
    root = make_repo(tmp_path, specs=[], rules=[], index_body="")
    import pathlib
    pathlib.Path(root, "openspec", "INDEX.md").write_text(idx, encoding="utf-8")
    r = _run(root)
    assert "疑似 spec 条目误置于 init 托管块内" in r
    assert "一致，无差异" not in r


def test_claude_ref_deleted_from_fs_and_index_reported(tmp_path):
    # [impl-review-fix] Fix-3: scan_claude_refs 判定改为直接核对 fs 是否存在，不再依赖
    # diff["stale"]（= INDEX 列但 fs 缺）。主用例：spec 早已从 fs **和** INDEX 都清理干净
    # （因此根本不在 stale 集里——stale = indexed - fs，indexed 里也没有它），但某 CLAUDE.md
    # 忘了同步、仍引用它 → 仍须报「过时引用」。旧实现基于 diff["stale"] 会漏报此例。
    root = make_repo(tmp_path, specs=[], rules=[], index_body="",
                     claude="见 openspec/specs/ghost/spec.md 的说明\n")
    r = _run(root)
    assert "过时引用" in r and "ghost" in r and "CLAUDE.md" in r


def test_claude_dir_walk_unreadable_fails(tmp_path, monkeypatch):
    # [impl-review-fix] Fix-5: os.walk 目录级不可读（权限异常等）也须 fail-closed，与文件级
    # open() 失败对称。用 monkeypatch 让 os.walk 的 onerror 回调确定性触发（不用 chmod 000——
    # root/CI 下不可靠）。
    body = "| `foo` | [specs/foo/spec.md](./specs/foo/spec.md) | x |"
    root = make_repo(tmp_path, specs=["foo"], rules=[], index_body=body)

    def fake_walk(top, onerror=None, **kwargs):
        if onerror is not None:
            onerror(OSError(13, "Permission denied", os.path.join(str(top), "blocked")))
        return iter([])

    monkeypatch.setattr(ms.os, "walk", fake_walk)
    with pytest.raises(ms.MaintainScanError):
        ms.run_scan(root)


def test_index_marker_inside_fence_not_treated_as_real(tmp_path):
    # [impl-review-fix] Fix-6①: fence-aware —— INDEX 托管块 marker 出现在 ``` 围栏内的示例中
    # （如文档讲解 marker 语法用的代码块）MUST NOT 被当真 marker：不应触发 marker 配对逻辑，
    # 块外的真实条目应正常参与 set-diff。
    idx = textwrap.dedent(f"""\
        # I

        以下是托管块 marker 的示例写法：
        ```
        {MANAGED_START}
        ```

        真实的 spec 索引：
        | `foo` | [specs/foo/spec.md](./specs/foo/spec.md) | x |
        """)
    root = make_repo(tmp_path, specs=["foo"], rules=[], index_body="")
    import pathlib
    pathlib.Path(root, "openspec", "INDEX.md").write_text(idx, encoding="utf-8")
    r = _run(root)
    # 若围栏内示例被误当真 start marker（无对应 end）会因 marker 不配对而 raise；
    # 正确行为是忽略它、正常识别块外 foo 条目、报告一致。
    assert "一致" in r


def test_stale_shadow_checkpoint_orphan(tmp_path):
    # [impl-review-fix] Fix-6③: 仓根 hack/checkpoint-commit.sh 孤儿副本（旧版仓内副本，
    # checkpoint 已全局化）→「陈旧遮蔽」节须报告该分支。
    root = make_repo(tmp_path, specs=[], rules=[], index_body="")
    import pathlib
    hack = pathlib.Path(root, "hack")
    hack.mkdir()
    (hack / "checkpoint-commit.sh").write_text("#!/bin/sh\necho old\n", encoding="utf-8")
    r = _run(root)
    assert "陈旧遮蔽" in r
    seg = r.split("陈旧遮蔽")[1]
    assert "checkpoint-commit.sh" in seg


# [impl-review-fix] 跨模型 outside-voice 审出 2 条：Fix-OV1（parse_index_entries 限定表格行，
# spec H3/D1 锚定）、Fix-OV2（_iter_claude_files 精确剪枝 .git，不误剪 .github 等）。

def test_parse_index_entries_prose_link_not_indexed(tmp_path):
    # Fix-OV1: 散文行（非表格行）里偶然出现的 spec 链接 MUST NOT 被当已索引——spec H3/D1
    # 要求「已列条目」锚在表格行链接目标路径模式。若仍按任意含 "](" 的行提取链接，本例会
    # 误把散文里的 [foo](./specs/foo/spec.md) 当已索引，掩盖真实「新增未索引 foo」。
    body = "见 [foo](./specs/foo/spec.md) 的相关说明，具体见正文，此行非表格行。"
    root = make_repo(tmp_path, specs=["foo"], rules=[], index_body=body)
    r = _run(root)
    assert "新增未索引" in r
    new_section = r.split("新增未索引")[1].split("已删未清理")[0]
    assert "foo" in new_section


def test_parse_index_entries_table_row_positive_regression(tmp_path):
    # 回归：既有表格行正例（真实索引形态）在限定表格行后仍正确入集、判一致。
    body = "| `foo` | [specs/foo/spec.md](./specs/foo/spec.md) | x |"
    root = make_repo(tmp_path, specs=["foo"], rules=[], index_body=body)
    r = _run(root)
    assert "一致" in r


def test_claude_dotgithub_not_pruned(tmp_path):
    # Fix-OV2: _iter_claude_files 须精确剪枝 ".git"（仅路径组件恰为 ".git" 的目录），不误剪
    # ".github" 等相似前缀目录。旧实现用子串 `os.sep + ".git" in dirpath` 判断，会把
    # .github/CLAUDE.md 静默跳过，违反 spec R2「扫描根 + 各子目录 CLAUDE.md」。
    body = "| `foo` | [specs/foo/spec.md](./specs/foo/spec.md) | x |"
    root = make_repo(tmp_path, specs=["foo"], rules=[], index_body=body)
    import pathlib
    ghdir = pathlib.Path(root, ".github")
    ghdir.mkdir()
    (ghdir / "CLAUDE.md").write_text("见 openspec/specs/gone/spec.md 的定义\n", encoding="utf-8")
    r = _run(root)
    assert "过时引用" in r
    section = r.split("过时引用")[1].split("陈旧遮蔽")[0]
    assert "gone" in section and ".github" in section


# ---------- devenv 健康度扫描（spec: maintain-scan —— 6 个 Scenario 逐条）----------
#
# 【为什么这一层是 load-bearing】：devenv_lint 【原本没有任何触发点】。
# 而 devenv 的渐进 DoD 允许泳道停在 scaffolded、槽停在「⚠️ 待定」——
# 防止它烂成僵尸文档的唯一措施就是「把代价摆到人眼前」（adr/0021）。
# **若无人调用该 lint，该措施为空。**「不强制完成」+「不检查未完成」= 名存实亡。

import json as _json


def _devenv_repo(tmp_path, data=None):
    """复用 make_repo 造最小一致仓（无差异），再铺 .devenv.json。

    刻意用「无差异」的仓：这样报告里出现「一致，无差异」，
    就能断言 devenv 的待定【没有】把 maintain 判成有差异（它是提醒，不是门禁）。
    """
    make_repo(tmp_path, specs=(), rules=[], index_body="# INDEX\n")
    arch = tmp_path / "openspec" / "architecture"
    arch.mkdir(parents=True, exist_ok=True)
    if data is not None:
        (arch / ".devenv.json").write_text(_json.dumps(data, ensure_ascii=False),
                                           encoding="utf-8")
    return tmp_path


def _blank_devenv():
    import sys as _s
    from pathlib import Path as _P
    _s.path.insert(0, str(_P(__file__).resolve().parents[2] / "sdflow-devenv" / "scripts"))
    import devenv_schema
    return devenv_schema.blank()


def test_scenario_no_devenv_json_is_skipped(tmp_path):
    """Scenario: 无 .devenv.json 时跳过 —— 不报错。"""
    _devenv_repo(tmp_path, data=None)
    assert ms.scan_devenv(str(tmp_path)) == ("absent", "")
    assert "devenv 健康度" not in ms.run_scan(str(tmp_path))


def test_scenario_cost_banner_passed_through_verbatim(tmp_path):
    """Scenario: 代价横幅原样透传（12/15 待定 → 报告里就是那句话）。"""
    d = _blank_devenv()
    for slot in ("how", "convention", "process"):
        d["layers"]["unit"][slot] = "已答"
    _devenv_repo(tmp_path, d)
    r = ms.run_scan(str(tmp_path))
    assert "⚠️ 本框架 12/15 格待定，尚不构成一份可用的测试策略" in r


def test_scenario_it_is_a_reminder_not_a_gate(tmp_path):
    """⭐ Scenario: 它是提醒不是门禁 —— 十五格全待定，maintain 仍不失败。

    devenv_lint 退出码永远是 0。把它渲染成「通过/不通过」，就是把「代价可见」
    做成了「机械拦截」——正是 devenv 整个设计要杀的东西（adr/0021）。
    """
    _devenv_repo(tmp_path, _blank_devenv())
    r = ms.run_scan(str(tmp_path))
    assert "15/15 格待定" in r
    assert "一致，无差异" in r          # ← devenv 的待定【没有】把 maintain 判成有差异
    assert "提醒，非门禁" in r


def test_scenario_unverified_lanes_listed_one_by_one(tmp_path):
    """Scenario: 逐条报出未 verified 泳道及其 blocked_by —— MUST NOT 只给计数。"""
    d = _blank_devenv()
    d["lanes"] = [
        {"id": "mqtt-real", "layer": "integration", "status": "scaffolded",
         "blocked_by": "本机无 mosquitto（brew install mosquitto 后 continue）",
         "verification": {"method": "make integration", "executor": "script"},
         "source": "4 个 realbroker tag 文件", "deps": []},
        {"id": "pkg-smoke", "layer": "e2e", "status": "scaffolded",
         "blocked_by": "打包冒烟脚本未建",
         "verification": {"method": "wails build", "executor": "human"},
         "source": "待建", "deps": []},
    ]
    d["layers"]["integration"]["lane_ids"] = ["mqtt-real"]
    d["layers"]["e2e"]["lane_ids"] = ["pkg-smoke"]
    _devenv_repo(tmp_path, d)
    r = ms.run_scan(str(tmp_path))
    assert "mqtt-real" in r and "本机无 mosquitto" in r      # 逐条，带 blocked_by
    assert "pkg-smoke" in r and "打包冒烟脚本未建" in r


def test_scenario_verified_keeps_its_commit_anchor(tmp_path):
    """⭐ Scenario: verified MUST NOT 渲染成无条件的绿 —— 原样带 commit 锚与日期。

    `verified` 的语义是 `verified-at <sha>`：**一次历史执行的记录，不是当前状态的绿灯**。
    业务代码一改，那个绿灯就在说谎。∴ maintain 【原样透传】lint 的文本，不重新渲染
    （重渲染必然丢锚）。
    """
    d = _blank_devenv()
    d["lanes"] = [{
        "id": "go-hermetic", "layer": "unit", "status": "verified",
        "verification": {"method": "go test ./...", "executor": "script",
                         "evidence": {"at_commit": "abc123f" + "0" * 33,
                                      "at_time": "2026-07-14T10:23:00Z",
                                      "exit": 0, "attested_by": "script"}},
        "source": "46 个 _test.go", "deps": []}]
    d["layers"]["unit"]["lane_ids"] = ["go-hermetic"]
    _devenv_repo(tmp_path, d)
    r = ms.run_scan(str(tmp_path))
    assert "abc123f" in r                     # commit 锚还在
    assert "2026-07-14" in r                  # 日期还在
    assert "✓ 已通过" not in r                 # 没有被二次简化成绿灯


def test_scenario_bad_data_reported_not_swallowed(tmp_path):
    """坏 .devenv.json ⇒ 报出来（lint 的唯一 fail-closed），但 maintain 本身不崩。"""
    _devenv_repo(tmp_path, data=None)
    (tmp_path / "openspec" / "architecture" / ".devenv.json").write_text(
        "{not json", encoding="utf-8")
    st, _ = ms.scan_devenv(str(tmp_path))
    assert st == "bad"
    assert "数据坏了" in ms.run_scan(str(tmp_path))


def test_scenario_devenv_lint_unavailable_is_reported_not_swallowed(tmp_path, monkeypatch):
    """Scenario: devenv_lint 不可用时【显式提示】—— MUST NOT 静默略过。

    静默略过 = 用户以为扫过了（而它根本没跑）。这跟「没有触发点」是同一种病：
    **一个看起来存在、实际不存在的检查。**
    """
    _devenv_repo(tmp_path, _blank_devenv())
    # 让 import devenv_lint 失败（模拟未装 sdflow-devenv）
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *a, **kw):
        if name == "devenv_lint":
            raise ImportError("模拟未装 sdflow-devenv")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.delitem(__import__("sys").modules, "devenv_lint", raising=False)

    st, _ = ms.scan_devenv(str(tmp_path))
    assert st == "unavailable"
    r = ms.run_scan(str(tmp_path))
    assert "devenv_lint` 不可用" in r and "跳过健康度扫描" in r     # 显式说了，没静默
