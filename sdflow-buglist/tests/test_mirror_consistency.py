"""test_mirror_consistency.py — recorder 镜像 helper 一致性守卫（mlh-p3-determ-guards Task 1）。

背景（design D2/D6，grill Path B 定夺）：`sdflow-buglist/scripts/buglist.py`、
`sdflow-todolist/scripts/todolist.py`、`sdflow-issues/scripts/issues.py` 是三个独立
skill 各自的执行核心，D4 红线禁止互相 import（子进程解耦，各自内联一份共享 helper）。
这意味着这些 helper 的"一致性"完全靠人肉记得同步改三处——本文件是这条纪律的确定性
守卫：契约 = **剥 docstring 后 AST 等价**（非逐字节相同）。docstring/注释差异是合法
漂移（三份脚本各自记录了不同的上下文，如 issues.atomic_write 多一段"子进程解耦"注记），
只有 AST 不等（=真实逻辑分叉）才判定为漂移、拉红。

三份脚本用 `importlib.util.spec_from_file_location` 各自独立加载 module（不 import
包，避免给测试引入 D4 明确禁止的跨 skill 耦合）——只读断言源码，不建立任何 import 依赖。
"""

import ast
import importlib.util
import inspect
import os
import textwrap

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BUGLIST_PATH = os.path.join(REPO_ROOT, "sdflow-buglist", "scripts", "buglist.py")
TODOLIST_PATH = os.path.join(REPO_ROOT, "sdflow-todolist", "scripts", "todolist.py")
ISSUES_PATH = os.path.join(REPO_ROOT, "sdflow-issues", "scripts", "issues.py")


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUG = _load_module("_mirror_buglist", BUGLIST_PATH)
TODO = _load_module("_mirror_todolist", TODOLIST_PATH)
ISS = _load_module("_mirror_issues", ISSUES_PATH)


def _ast_no_doc(fn):
    """`fn` 的源码 → dedent → parse → 剥掉函数体首个 docstring 表达式（若有）→ ast.dump。

    docstring 差异（三份脚本各自记录了不同的上下文注记）是合法漂移，不该让一致性测试
    假红；只有剥掉 docstring 之后 AST 仍不等，才是真实的逻辑分叉。
    """
    src = textwrap.dedent(inspect.getsource(fn))
    tree = ast.parse(src)
    func_node = tree.body[0]
    body = func_node.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    func_node.body = body
    return ast.dump(func_node)


# 3 份 recorder（buglist/todolist/issues）都各自持有的 helper（D4 红线：不互相 import，
# 各自内联一份）。issues.py 不含表解析类 helper（它不直接读写 dated 文件的表/块结构，
# 只经子进程调用 buglist.py/todolist.py 的 `scan --json`），故这些 helper 只在
# buglist/todolist 两份之间镜像，见下面 TWO_WAY。
THREE_WAY = ["atomic_write", "repo_root", "_reject_cell_unsafe"]

# 只在 buglist.py / todolist.py 两份之间镜像的表/块解析 helper（issues.py 不含，
# 断言范围明确不含 issues——见模块 docstring）。
TWO_WAY = [
    "detect_change", "normalize_doc_paths", "auto_default_doc",
    "split_sections", "parse_table_rows", "block_ranges",
    "_ids_in_files", "_find_row_file",
]


def test_three_way_mirror_consistency():
    """THREE_WAY helper 在 buglist/todolist/issues 三份脚本里剥 docstring 后 AST 必须
    逐字等价——三者独立维护同一段逻辑，任一处偷改都必须让本测试拉红。"""
    for name in THREE_WAY:
        bug_ast = _ast_no_doc(getattr(BUG, name))
        todo_ast = _ast_no_doc(getattr(TODO, name))
        iss_ast = _ast_no_doc(getattr(ISS, name))
        mismatched = []
        if bug_ast != todo_ast:
            mismatched.append("buglist≠todolist")
        if bug_ast != iss_ast:
            mismatched.append("buglist≠issues")
        if todo_ast != iss_ast:
            mismatched.append("todolist≠issues")
        assert bug_ast == todo_ast == iss_ast, (
            f"helper {name!r} 三份 recorder AST（剥 docstring 后）不等价：{', '.join(mismatched)}"
        )


def test_two_way_mirror_consistency():
    """TWO_WAY helper 只在 buglist/todolist 两份脚本里剥 docstring 后 AST 必须等价
    （issues.py 不含表解析类 helper，断言范围不含 issues——见模块 docstring）。"""
    for name in TWO_WAY:
        bug_ast = _ast_no_doc(getattr(BUG, name))
        todo_ast = _ast_no_doc(getattr(TODO, name))
        assert bug_ast == todo_ast, (
            f"helper {name!r} buglist/todolist 两份 recorder AST（剥 docstring 后）不等价"
        )


def test_docstring_diff_ok():
    """现存三份 helper 的 docstring 本就互不相同（例如 issues.atomic_write 比 buglist/
    todolist 多一段"与…同名函数逐字同款"的子进程解耦注记）——一致性测试仍应通过，因为
    守的是行为（AST），不是字面（含 docstring 的源码文本）。"""
    for name in THREE_WAY:
        bug_src = textwrap.dedent(inspect.getsource(getattr(BUG, name)))
        iss_src = textwrap.dedent(inspect.getsource(getattr(ISS, name)))
        assert inspect.getdoc(getattr(BUG, name)) != inspect.getdoc(getattr(ISS, name)) or (
            bug_src != iss_src
        ), f"helper {name!r} 预期 docstring/源码文本存在差异（用于验证本测试确实容忍字面差异）"
    # 即便字面不同，_ast_no_doc 比对必须仍然通过（不因 docstring 差异假红）。
    for name in THREE_WAY:
        assert _ast_no_doc(getattr(BUG, name)) == _ast_no_doc(getattr(ISS, name))


def test_logic_drift_is_caught():
    """守卫抓真漂移、非 no-op：临时构造一对『docstring 相同、逻辑不同』的函数，断言
    `_ast_no_doc` 比对报不等——证明本守卫真的在比较逻辑（AST），会对真实的逻辑分叉拉红，
    不是一个永远返回 True 的空判断。"""

    def helper_a():
        """same docstring"""
        return 1 + 1

    def helper_b():
        """same docstring"""
        return 1 + 2

    assert _ast_no_doc(helper_a) != _ast_no_doc(helper_b)


def test_helper_deletion_is_not_silently_swallowed():
    """helper 删除证伪（spec 需求① scenario·L1）：比对代码必须用直接属性访问
    `getattr(m, f)`——上面 `test_three_way_mirror_consistency` / `test_two_way_mirror_consistency`
    均未用 try/except 包裹 getattr 调用，某 recorder 若删除/改名了某个镜像 helper，
    `getattr` 会抛 `AttributeError`，测试直接因异常失败（红），不会被静默跳过。

    本用例独立复现这条约束：直接对一个确定不存在的属性名调用 getattr（不带 default），
    断言抛出 AttributeError——用于锁死"删除即报错"这条契约本身没有被后续修改悄悄
    改成 try/except 吞掉的防御式写法。

    MUST 锁死的约束：全文件任何 THREE_WAY/TWO_WAY 的 getattr(module, name) 调用都
    不得包一层 try/except AttributeError（那样会把"helper 被删"这个信号静默吞掉，
    退化成一个测不出任何东西的空跑）。
    """
    import pytest

    with pytest.raises(AttributeError):
        getattr(BUG, "_this_helper_does_not_exist_and_never_should")
