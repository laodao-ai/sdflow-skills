"""[fix-probe-scan-precision task5 · C14 · adr/0039] `tools_spec` 比较腿退役的正向/反向锚。

`is_stale(scope="code")` 原有两条腿：① 顶层条目浅层快照比较（排除 `openspec`）；
② 已删除的 `tools_spec` 腿（`openspec/workflow/tools/` 递归比较）。C14 论证：①已覆盖
toolkit 源仓的权威源改动（权威源位于顶层条目 `sdflow-init` 之下，任意深度改动都翻转该
顶层条目 tree oid）；消费仓镜像已随本 change 停止铺设（D13）、本仓残留亦已删除
（tasks 6.1），故「直接改镜像」这个②腿本要抓的动作已不可能发生。

本文件补两条反向工程验证测试（tasks 5.3/5.4），MUST NOT 省略——防止「删腿后行为其实
变了」被误判为无害重构。
"""
from conftest import commit_all, mkchange, head_sha, write_report, fingerprint
from test_gate_impl_progress import _sg


def _anchor_review_report(repo, d):
    """落一份带内容锚的 code-review-report.md（锚 = 写盘时 HEAD 上的 code 域指纹），提交。"""
    sha, manifest = fingerprint(repo, head_sha(repo), "code")
    write_report(d, "code-review-report.md", sha=sha, manifest=manifest, code_review="pass")
    commit_all(repo, "code-review-report")
    return sha


def test_forward_anchor_toolkit_source_change_is_still_stale(repo):
    """5.3 正向锚：改 `sdflow-init/assets/workflow/tools/`（toolkit 权威源）下文件后，
    判定仍为 stale——证明该路径由顶层腿覆盖，不依赖已删的 `tools_spec` 腿。"""
    d = mkchange(repo)
    (d / "proposal.md").write_text("# p\n", encoding="utf-8")
    tools_dir = repo / "sdflow-init" / "assets" / "workflow" / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    (tools_dir / "anchor_lint.py").write_text("# v1\n", encoding="utf-8")
    commit_all(repo, "seed change + toolkit tools source")

    _anchor_review_report(repo, d)

    (tools_dir / "anchor_lint.py").write_text("# v2 changed\n", encoding="utf-8")
    commit_all(repo, "change toolkit tools source")

    rel = str((d / "code-review-report.md").relative_to(repo))
    stale, freshness = _sg.is_stale(repo, rel, "code", "demo")
    assert (stale, freshness) == (True, "stale"), \
        "toolkit 源仓改权威源 MUST 仍判 stale（顶层腿覆盖，C14）"


def test_reverse_anchor_consumer_mirror_change_alone_is_fresh(repo):
    """5.4 反向锚（MUST NOT 省略）：fixture 仓在 `openspec/workflow/tools/`（消费仓镜像
    路径）下造/改一个文件，其余不动 → 判 fresh——证明 `tools_spec` 腿真已退役
    （留着旧腿则本用例必红：旧腿会因该路径下内容变化而判 stale）。"""
    d = mkchange(repo)
    (d / "proposal.md").write_text("# p\n", encoding="utf-8")
    commit_all(repo, "seed change")

    _anchor_review_report(repo, d)

    mirror_dir = repo / "openspec" / "workflow" / "tools"
    mirror_dir.mkdir(parents=True, exist_ok=True)
    (mirror_dir / "anchor_lint.py").write_text("# mirror edit\n", encoding="utf-8")
    commit_all(repo, "touch consumer mirror only (openspec/ 整体被顶层腿排除)")

    rel = str((d / "code-review-report.md").relative_to(repo))
    stale, freshness = _sg.is_stale(repo, rel, "code", "demo")
    assert (stale, freshness) == (False, "fresh"), \
        "仅改消费仓镜像 MUST 判 fresh（tools_spec 腿已退役，openspec/ 整体被顶层腿排除）"
