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
- 绕开 `.setattr` 的补桩路径（直接赋 `issues_mod.subprocess.run = …`、
  `unittest.mock.patch`）——目前本目录零使用；门 A 不覆盖，新引入需扩门。
- 白名单条目的理由是否仍然成立（人读注记，非机械信号）。

**接收器判据为什么不认名字**（cr-fix2）：门 A 曾要求接收器是名字字面量 `monkeypatch`
（`func.value.id == "monkeypatch"`），于是对 `MonkeyPatch` 的**别名形式**完全失明——
`mp = monkeypatch` / `pytest.MonkeyPatch()` / `with pytest.MonkeyPatch.context() as mp`
写出来的 `mp.setattr(...)` 一律不进扫描，无条件替身畅通无阻（实测：退化站点写成
`mp.setattr(issues_mod.subprocess, "run", lambda *a, **k: scan(a[0]))` 后两道门 7 passed
全绿）。而这三种形式**本身就是** `monkeypatch.setattr`，上面的能力边界里却没登记这个洞
⇒ 读者会以为已覆盖。∴ 判据放宽为「**任意** `<expr>.setattr`，且实参指向 `subprocess.run`」：
`.setattr(<…>.subprocess, "run", …)` / `.setattr("<…>.subprocess.run", …)` 这个**形状**
已足够判别，不必绑定变量名。`test_gate_a_sees_monkeypatch_aliases` 把三种别名形式
钉成自检语料。
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
    ("test_repo_root_identity_buglist.py", "_fake_git_stdout"):
        "被测对象是 repo_root 对 git stdout 的解释；换掉 git 输出即断言本体。",
    ("test_repo_root_identity_buglist.py", "_forbid_subprocess"):
        "断言「起点校验发生在调 git 之前」——任何子进程都判失败即断言本体。",
    ("test_repo_root_identity_buglist.py", "test_timeout_raises_and_does_not_fall_back"):
        "注入 TimeoutExpired 并捕获 kwargs，验证超时不回落；劫持 git 即断言本体。",
    ("test_repo_root_identity_buglist.py", "test_timeout_with_real_hanging_git"):
        "全量透传、仅把 timeout 压到 1s 让真实 git shim 触发超时；非替身。",
    ("test_repo_root_identity_todolist.py", "_fake_git_stdout"):
        "被测对象是 repo_root 对 git stdout 的解释；换掉 git 输出即断言本体。",
    ("test_repo_root_identity_todolist.py", "_forbid_subprocess"):
        "断言「起点校验发生在调 git 之前」——任何子进程都判失败即断言本体。",
    ("test_repo_root_identity_todolist.py", "test_timeout_raises_and_does_not_fall_back"):
        "注入 TimeoutExpired 并捕获 kwargs，验证超时不回落；劫持 git 即断言本体。",
    ("test_repo_root_identity_todolist.py", "test_timeout_with_real_hanging_git"):
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
    """产出 (lineno, 最内层 def 名, 值节点) —— `path` 里所有 subprocess.run 补桩站点。"""
    return _iter_run_patch_sites_in_source(path.read_text(encoding="utf-8"))


def _iter_run_patch_sites_in_source(source):
    """同上，但吃源码串 —— 让门 A 的选择器本身可被自检用例直接喂样例（`ast` 只认源码，
    从文件读还是从串读没有语义差别，∴ 自检不必往 tests/ 里落一堆诱饵文件）。"""
    tree = ast.parse(source)
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
        # 接收器**刻意不判名字**（cat 模块 docstring「接收器判据为什么不认名字」）：
        # 认 `monkeypatch` 字面量会对 mp = monkeypatch / MonkeyPatch() /
        # MonkeyPatch.context() 三种别名形式全盲。下面的实参判据（目标模块名为
        # subprocess、属性为 "run"）已足够把 `.setattr` 收窄到补桩站点。
        # monkeypatch.setattr 有两种合法调用形式，两种都必须认——只认三参形式会让
        # 门 A 对 pytest 惯用的 2 参字符串形式完全失明（实测：变异后 7 passed 不红）。
        if len(node.args) == 3:
            target, attr, value = node.args
            if not (isinstance(attr, ast.Constant) and attr.value == "run"):
                continue
            if _module_of(target) != "subprocess":
                continue
        elif len(node.args) == 2:
            target, value = node.args
            if not (isinstance(target, ast.Constant) and isinstance(target.value, str)):
                continue
            if not target.value.endswith("subprocess.run"):
                continue
        else:
            continue
        yield node.lineno, enclosing(node.lineno), value


def _test_files():
    return sorted(p for p in TESTS_DIR.glob("test_*.py"))


#: 门 A 自检语料：接收器**不叫** `monkeypatch` 的合法 MonkeyPatch 用法。
#: 每条都是一个「无条件替身」的退化站点 —— 门 A MUST 看得见它们，且 MUST NOT 把裸
#: lambda 误认成工厂调用。判据一旦退回按名字认接收器，本组用例全红。
GATE_A_ALIAS_SAMPLES = {
    "别名绑定 mp = monkeypatch": (
        "def test_x(monkeypatch):\n"
        "    mp = monkeypatch\n"
        '    mp.setattr(issues_mod.subprocess, "run", lambda *a, **k: None)\n'
    ),
    "直接实例化 pytest.MonkeyPatch()": (
        "def test_x():\n"
        "    mp = pytest.MonkeyPatch()\n"
        '    mp.setattr(issues_mod.subprocess, "run", lambda *a, **k: None)\n'
    ),
    "上下文管理器 MonkeyPatch.context()": (
        "def test_x():\n"
        "    with pytest.MonkeyPatch.context() as mp:\n"
        '        mp.setattr(issues_mod.subprocess, "run", lambda *a, **k: None)\n'
    ),
    "别名 + 2 参字符串形式": (
        "def test_x():\n"
        "    with pytest.MonkeyPatch.context() as mp:\n"
        '        mp.setattr("issues.subprocess.run", lambda *a, **k: None)\n'
    ),
}


@pytest.mark.parametrize("label", sorted(GATE_A_ALIAS_SAMPLES))
def test_gate_a_sees_monkeypatch_aliases(label):
    """自检：接收器不叫 `monkeypatch` 时，门 A 仍然看得见该补桩站点。

    这是能力边界的**机械**兑现——docstring 声称门 A 覆盖 `monkeypatch.setattr`，
    而别名形式本身就是它；不钉住这一条，声称与实际会静默背离（实测退化路径：
    两道门 7 passed、本文件 91 passed 全绿，替身却已经无条件劫持 repo_root 的 git）。
    """
    sites = list(_iter_run_patch_sites_in_source(GATE_A_ALIAS_SAMPLES[label]))

    assert len(sites) == 1, (
        "%s：扫到 %d 个站点（期望 1）—— 门 A 对该别名形式失明，"
        "无条件替身可绕过整条纪律" % (label, len(sites))
    )
    _, owner, value = sites[0]
    assert owner == "test_x", (label, owner)
    is_factory_call = (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id in DISPATCH_FACTORIES
    )
    assert not is_factory_call, (
        "%s：样例是裸 lambda，MUST NOT 被认成分派工厂调用（否则门 A 判为合规）" % label
    )


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
