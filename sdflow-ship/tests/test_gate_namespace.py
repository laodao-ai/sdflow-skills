"""〔ship-gate-hardening-2 T32〕checkpoint 任务号 change 命名空间隔离 + 向后兼容。
全部用**真实 git commit fixture**（非字符串 mock）——否则测不出 done_task_ids 的
startswith 硬前缀漏放宽洞（对抗镜 A-F1：命名标签会在 TAG_RE.match 前被整条跳过）。"""
from conftest import commit_all
from test_gate_preflight import run_gate
from test_gate_impl_progress import approved_change, PLAN2_TICKETS


def test_namespace_isolation_discriminating(repo):
    # 〔T32 判别性负例〕plan={1,2}，当前 change=demo 只有 demo:task1，另一 change
    # 的 other:task2（=demo 缺的 task2 号）落进同窗口 → 只计 demo:task1，MUST NOT 因
    # other:task2 顶替使 done={1,2} 假齐。用"B 的号=A 缺的号"方有区分力（同号 task1 无区分力）。
    approved_change(repo, plan=PLAN2_TICKETS)
    commit_all(repo, "checkpoint(demo:task1-a): A")
    commit_all(repo, "checkpoint(other:task2-b): 另一 change 的 task2 落窗口")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["1"]


def test_namespace_current_change_named_counts(repo):
    # 〔T32〕命名标签匹配当前 change → 计入 → 齐 → RUN_CODE_REVIEW
    approved_change(repo, plan=PLAN2_TICKETS)
    commit_all(repo, "checkpoint(demo:task1-a): A")
    commit_all(repo, "checkpoint(demo:task2-b): B")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"


def test_namespace_backward_compat_bare(repo):
    # 〔T32 向后兼容 A1〕全裸标签 → 窗口计入（= 升级前行为）→ 齐
    approved_change(repo, plan=PLAN2_TICKETS)
    commit_all(repo, "checkpoint(task1-a): A")
    commit_all(repo, "checkpoint(task2-b): B")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"


def test_namespace_mixed_bare_and_named(repo):
    # 〔T32〕裸 task1（A1 计入）+ 命名 demo:task2（匹配计入）→ 齐；
    # 混合窗口下当前 change 的两号都到位
    approved_change(repo, plan=PLAN2_TICKETS)
    commit_all(repo, "checkpoint(task1-a): 裸 A")
    commit_all(repo, "checkpoint(demo:task2-b): 命名 B")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"


def test_namespace_noncanonical_ns_degrades_safe(repo):
    # 〔code-review CR-F3〕命名组 [a-z0-9][a-z0-9-]* 不含大写/下划线（openspec 强制 kebab 名，
    # 此为防御性锁定）：非法 ns 的命名标签整体不匹配 TAG_RE → 该行不计入（假阴安全，
    # 绝非误归属给别的 change）。防后续修改无意打破成"误计入"。
    approved_change(repo, plan=PLAN2_TICKETS)
    commit_all(repo, "checkpoint(Demo:task1-a): 大写 ns（非法 kebab）")
    commit_all(repo, "checkpoint(task2-b): 裸 task2")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["2"]


def test_namespace_other_change_named_not_counted(repo):
    # 〔T32〕当前 demo 只完成 task1（命名），另一 change 的 other:task2 不计
    # → task2 未完 → CONTINUE_IMPL，done_tasks 只报 demo 的 1
    approved_change(repo, plan=PLAN2_TICKETS)
    commit_all(repo, "checkpoint(demo:task1-a): A")
    commit_all(repo, "checkpoint(other:task2-x): 不属 demo")
    commit_all(repo, "checkpoint(other:task1-y): 也不属 demo")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["1"]
