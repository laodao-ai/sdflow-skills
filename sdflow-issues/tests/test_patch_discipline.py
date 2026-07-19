"""机械守：`subprocess.run` 补桩纪律（基准 1 —— 不变量 MUST NOT 只靠散文守着）。

`harden-repo-root-fail-closed` 消除的假绿形态是「整体替换 `subprocess.run`」：它连带
劫持被测函数之外的一切子进程（尤其 `repo_root` 的 `git rev-parse`），用例看似通过，
实则被测逻辑根本没跑到目标目录。修复后这条纪律**只由 `conftest.make_dispatch_run` 的
docstring 用散文守着**——将来有人把分派工厂「简化」回整体替换，假绿会无声回归。
本模块把它固化成两道机械门。

## 判据设计（用 `ast`，MUST NOT 用 grep/正则 —— 基准 5）

- **门 A（站点形态）**：本目录每个 `monkeypatch.setattr(<…>.subprocess, "run", <value>)`
  站点，`<value>` MUST 是对分派工厂（`dispatch_run` / `scan_only_run` /
  `make_dispatch_run`）的调用；否则该站点 MUST 出现在 `INTENTIONAL_WHOLESALE_PATCHES`
  白名单里**并写明理由**。新增站点默认红 —— 豁免必须显式登记，不靠模式碰巧漏掉。
- **门 B（工厂本体）**：`conftest.make_dispatch_run` 的内层 `run` MUST 保留
  「条件分派 + `real_run(command, *args, **kwargs)` 兜底透传」结构。没有门 B，把工厂
  内部改成整体替换可以在**不动任何站点**的情况下让假绿全面回归（门 A 看到的调用形状
  没变）。

## 诚实的能力边界（守得住什么 / 守不住什么）

**守得住**：① 站点回退成裸 lambda / 局部 `fake_run` 函数；② 新增未登记的补桩站点；
③ 工厂本体被「简化」成无条件返回替身（透传分支消失）。

**守不住**（如实登记，不假装全覆盖）：
- 判据函数本身写错（如 `argv_contains()` 空 tokens ⇒ 恒真 ⇒ 等价整体替换）——
  这是**语义**正确性，无确定性信号，留给用例自身的断言与评审。
- 绕开 `monkeypatch.setattr` 的补桩路径（直接赋 `issues_mod.subprocess.run = …`、
  `unittest.mock.patch`）——目前本目录零使用；门 A 不覆盖，新引入需扩门。
- 白名单条目的理由是否仍然成立（人读注记，非机械信号）。
"""

import ast
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent

#: 分派工厂的合法名字（`conftest` 的 fixture 名 + 底层工厂名）。
DISPATCH_FACTORIES = {"dispatch_run", "scan_only_run", "make_dispatch_run"}

#: 显式豁免：(文件名, 词法上最内层的 def 名) → 理由。
#: 这些站点**整体替换是断言本体**，不是副作用——被测对象就是 `repo_root` 自己对 git
#: 的调用，改成分派形态会让用例失去测试对象。
INTENTIONAL_WHOLESALE_PATCHES = {
    ("test_issues.py", "test_falls_back_to_abspath_when_git_command_raises"):
        "被测对象是 repo_root 的 git 失败回落分支；劫持 git 即断言本体。",
    ("test_repo_root_identity_issues.py", "_fake_git_stdout"):
        "被测对象是 repo_root 对 git stdout 的解释；换掉 git 输出即断言本体。",
    ("test_repo_root_identity_issues.py", "_forbid_subprocess"):
        "断言「起点校验发生在调 git 之前」——任何子进程都判失败即断言本体。",
    ("test_repo_root_identity_issues.py", "test_timeout_raises_and_does_not_fall_back"):
        "注入 TimeoutExpired 并捕获 kwargs，验证超时不回落；劫持 git 即断言本体。",
    ("test_repo_root_identity_issues.py", "test_timeout_with_real_hanging_git"):
        "全量透传、仅把 timeout 压到 1s 让真实 git shim 触发超时；非替身。",
    ("test_task4_rename_snapshot.py",
     "test_batch_rename_uses_direct_snapshot_zero_recorder_scans_and_writes_provenance"):
        "observe_run 是全量透传的观察器（只记录 argv，不返回替身），无劫持面。",
}


def _module_of(node):
    """`<x>.subprocess` / `subprocess` → 取属性链末段名，用于识别补桩目标。"""
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def _iter_run_patch_sites(path):
    """产出 (lineno, 最内层 def 名, 第三实参节点) —— 所有 subprocess.run 补桩站点。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    scope = []  # (def 名, end_lineno) 栈，用词法包含关系定位最内层 def

    def enclosing(lineno):
        names = [name for name, start, end in scope if start <= lineno <= end]
        return names[-1] if names else "<module>"

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            scope.append((node.name, node.lineno, node.end_lineno))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "setattr"):
            continue
        if not (isinstance(func.value, ast.Name) and func.value.id == "monkeypatch"):
            continue
        if len(node.args) != 3:
            continue
        target, attr, value = node.args
        if not (isinstance(attr, ast.Constant) and attr.value == "run"):
            continue
        if _module_of(target) != "subprocess":
            continue
        yield node.lineno, enclosing(node.lineno), value


def _test_files():
    return sorted(p for p in TESTS_DIR.glob("test_*.py"))


def test_patch_sites_exist_at_all():
    """自检：门 A 的扫描器真的找到了站点——否则「零违规」只是选择器写错了。"""
    total = sum(len(list(_iter_run_patch_sites(p))) for p in _test_files())
    assert total >= 10, f"扫到 {total} 个补桩站点，选择器可能失效"


@pytest.mark.parametrize("path", _test_files(), ids=lambda p: p.name)
def test_gate_a_every_subprocess_run_patch_goes_through_dispatch_factory(path):
    """门 A：补桩站点要么走分派工厂，要么在白名单里（带理由）。"""
    violations = []
    for lineno, owner, value in _iter_run_patch_sites(path):
        is_factory_call = (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id in DISPATCH_FACTORIES
        )
        if is_factory_call:
            continue
        key = (path.name, owner)
        if key in INTENTIONAL_WHOLESALE_PATCHES:
            assert INTENTIONAL_WHOLESALE_PATCHES[key].strip(), f"{key} 白名单条目缺理由"
            continue
        violations.append(f"{path.name}:{lineno} (in {owner})")

    assert not violations, (
        "整体替换 subprocess.run 会连带劫持被测函数之外的子进程（含 repo_root 的 "
        "git 探测），用例退化为假绿。请改用 conftest 的 dispatch_run / scan_only_run，"
        "或把该站点显式登记进 INTENTIONAL_WHOLESALE_PATCHES 并写明理由。违规站点："
        + ", ".join(violations)
    )


def test_gate_b_dispatch_factory_keeps_conditional_passthrough():
    """门 B：分派工厂本体保留「条件分派 + real_run 兜底透传」结构。

    没有门 B，把工厂内部改成无条件返回替身即可让假绿全面回归，而门 A 完全看不见
    （所有站点的调用形状没变）。
    """
    tree = ast.parse((TESTS_DIR / "conftest.py").read_text(encoding="utf-8"))
    factory = next(
        (n for n in tree.body
         if isinstance(n, ast.FunctionDef) and n.name == "make_dispatch_run"),
        None,
    )
    assert factory is not None, "conftest 缺 make_dispatch_run —— 分派补桩的单一源没了"

    captures_real_run = any(
        isinstance(stmt, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "real_run" for t in stmt.targets)
        for stmt in factory.body
    )
    assert captures_real_run, "make_dispatch_run MUST 先捕获真实 subprocess.run 为 real_run"

    inner = next(
        (n for n in factory.body if isinstance(n, ast.FunctionDef) and n.name == "run"),
        None,
    )
    assert inner is not None, "make_dispatch_run 内 MUST 定义替身函数 run"

    assert any(isinstance(stmt, ast.If) for stmt in inner.body), (
        "替身 run 里没有条件分派 —— 这就是被禁止的整体替换形态"
    )

    tail = inner.body[-1]
    passthrough = (
        isinstance(tail, ast.Return)
        and isinstance(tail.value, ast.Call)
        and isinstance(tail.value.func, ast.Name)
        and tail.value.func.id == "real_run"
        and any(isinstance(a, ast.Starred) for a in tail.value.args)
        and any(isinstance(k, ast.keyword) and k.arg is None for k in tail.value.keywords)
    )
    assert passthrough, (
        "替身 run 的兜底分支 MUST 是 `return real_run(command, *args, **kwargs)` —— "
        "透传分支消失 = 整体替换 = 假绿回归；且 *args/**kwargs 全透传（写死关键字签名"
        "会在位置传参时 TypeError）"
    )
