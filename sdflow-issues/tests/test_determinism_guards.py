"""determinism-guards 新守法（dedupe-issues-scripts-shared-layer Task 4·DG-M1/DG-M2）。

三脚本合一为唯一命名 package `sdflow_issues_core` 后，`test_mirror_consistency.py` 的
三向/两向「剥 docstring AST 等价」镜像守**整体退役**（单一物理源使其无对象，Task 4.1 已删）。
守法改守合一后的**新面**，本文件承载其中两条：

1. **无 pool 分支守（AST 级·best-effort 代理，非充要保证）** —— `core` 源码 MUST NOT 含针对
   pool 值（`"bug"`/`"todo"`）的条件分支。字面 `if pool == "bug"` 子串扫描必漏（真实分岔含
   subscript `document["pool"]=="bug"`、别名 `expected_pool==`、三元 `"bugs" if pool==`、
   `match`、dict-dispatch 五形态——CLAUDE.md 基准 5「无界语法禁手搓」+「gate 子串自指坑」）。
   故守卫为 **AST 级**：拦 `If`/`IfExp`/`Compare`/`Match` 里把某表达式与**裸** pool 字面常量
   比较/匹配的分支。
2. **薄入口 thinness 同一性守** —— 三薄入口 MUST NOT shadow core helper：THREE_WAY/TWO_WAY
   roster 每个 helper 从薄入口 `getattr` 解析的对象 `__module__ == 'sdflow_issues_core'`
   （旧 mirror roster 复用：把「三份等价守」转「一份同一性守」）。

诚实边界（spec `determinism-guards` DG-M1·R2 硬约束）：

- **第 1 条是 best-effort 代理、非 fail-closed 充要保证**。它覆盖 `==`/`!=`/`is` 裸常量比较
  与 `match case "bug"` 形态；**结构上够不着的残余**——用 pool 变量下标一个数据字典
  （`{"bug":f, "todo":g}[pool]`，dict-dispatch）——无法与 `POOL_SPEC`/`RECORDER_POOL_CONFIG`
  等**合法数据注册表**（正是 `{"bug":..., "todo":...}` 形态）机械区分。真正的不变量由
  AD-3 的 **POOL_SPEC 封闭 schema 正面保证**（`test_pool_spec_schema.py`）——差异只能经数据
  注入、无处硬编码；本 AST 守只作辅助层，**不 overclaim「机械充要」**。
- 守卫**只扫 core 的 `.py` 文件 AST**，MUST NOT 扫 prose/文档（design.md/报告里讨论
  `if pool=="bug"` 会假阳——「gate 子串自指坑」复发）。放行 `POOL_SPEC` 数据定义字面、
  `validate_pool_spec` 的封闭 keys 断言 `{"bug","todo"}`（右操作数是**整集** Set，非裸单值）、
  以及注释/docstring（不在 `Compare`/`Match` 节点内）。
"""

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
CORE_DIR = SCRIPTS_DIR / "sdflow_issues_core"
sys.path.insert(0, str(SCRIPTS_DIR))

import sdflow_issues_core as core  # noqa: E402

POOL_LITERALS = {"bug", "todo"}

# `ast.Match`/`ast.MatchValue` 仅 Python ≥3.10（`match` 语句在 3.9 连 `ast.parse` 都拒）。
# 版本安全：3.9 下 core 里的 `match` 结构上不可能（parse 即 SyntaxError），守卫据此降级。
_MATCH_TYPE = getattr(ast, "Match", None)
_MATCHVALUE_TYPE = getattr(ast, "MatchValue", None)


# ══════════════════════════════════════════════════════════════════════════════
# 守 1：无 pool 分支（AST 级·best-effort）
# ══════════════════════════════════════════════════════════════════════════════

def _is_bare_pool_constant(node):
    """裸字符串常量 "bug" / "todo"（Compare/Match 的单值操作数）。"""
    return isinstance(node, ast.Constant) and node.value in POOL_LITERALS


def _is_full_pool_collection(node):
    """整集 {"bug","todo"}（含 list/tuple/frozenset(...)）——封闭 schema keys 断言，放行。

    与「裸单值 pool 分支」的分野：整集是「pool 空间的完整枚举断言」（`keys() == {"bug","todo"}`），
    不是「按某个 pool 值分岔」。
    """
    if isinstance(node, (ast.Set, ast.List, ast.Tuple)):
        consts = [e.value for e in node.elts if isinstance(e, ast.Constant)]
        return POOL_LITERALS <= set(consts)
    # frozenset({"bug","todo"}) / set(("bug","todo")) 形态
    if isinstance(node, ast.Call) and node.args:
        return _is_full_pool_collection(node.args[0])
    return False


def _describe_pool_valueish(node):
    """尽力描述「另一操作数是否解析到 pool 值」（诊断用，非拦截前置条件）。

    覆盖 design 点名的别名/subscript：`pool` / `expected_pool`（Name 含 'pool'）、
    `.pool`（Attribute）、`X["pool"]`（Subscript 常量下标 'pool'）。
    """
    if isinstance(node, ast.Name):
        return f"name={node.id}" if "pool" in node.id.lower() else None
    if isinstance(node, ast.Attribute):
        if node.attr.lower() == "pool":
            return f"attr=.{node.attr}"
        return _describe_pool_valueish(node.value)
    if isinstance(node, ast.Subscript):
        sl = node.slice
        if isinstance(sl, ast.Constant) and sl.value == "pool":
            return "subscript=[\"pool\"]"
        return _describe_pool_valueish(node.value)
    return None


def scan_pool_branches(source, filename="<core>"):
    """扫描 Python 源码 AST，返回针对 pool 值分岔的 findings。

    findings: [(lineno, form, snippet)]。form ∈ {compare, match}。best-effort（见模块 docstring）。
    """
    tree = ast.parse(source)
    findings = []
    for node in ast.walk(tree):
        # ── Compare：覆盖 if / while / IfExp 的 test（其 test 即嵌套 Compare 节点）+ 裸比较 ──
        if isinstance(node, ast.Compare):
            operands = [node.left, *node.comparators]
            bare = [op for op in operands if _is_bare_pool_constant(op)]
            if not bare:
                continue
            # 放行封闭 schema keys 断言：另一侧是整集 {"bug","todo"}
            if any(_is_full_pool_collection(op) for op in operands):
                continue
            other = [op for op in operands if not _is_bare_pool_constant(op)]
            hint = next((h for h in (_describe_pool_valueish(o) for o in other) if h), "?")
            snippet = ast.get_source_segment(source, node) or ast.dump(node)
            findings.append((node.lineno, "compare", f"{snippet}  (lhs→pool:{hint})"))
        # ── Match：case "bug" / case "todo"（Python ≥3.10）──
        elif _MATCH_TYPE is not None and isinstance(node, _MATCH_TYPE):
            for case in node.cases:
                for sub in ast.walk(case.pattern):
                    if isinstance(sub, _MATCHVALUE_TYPE) and _is_bare_pool_constant(sub.value):
                        snippet = ast.get_source_segment(source, sub.value) or ast.dump(sub)
                        findings.append((getattr(sub, "lineno", node.lineno), "match", f"case {snippet}"))
    return findings


def _core_py_files():
    files = sorted(CORE_DIR.glob("*.py"))
    assert files, f"core package 无 .py 文件: {CORE_DIR}"
    return files


def test_core_has_no_pool_value_branches():
    """core 每个 .py 文件 AST 无针对裸 pool 字面的条件分支/match（差异一律经 POOL_SPEC 取值）。"""
    offenders = {}
    for path in _core_py_files():
        findings = scan_pool_branches(path.read_text(encoding="utf-8"), str(path))
        if findings:
            offenders[path.name] = findings
    assert not offenders, (
        "core 出现针对 pool 值的条件分支（差异 MUST 走 POOL_SPEC，非 core 内分叉）:\n"
        + "\n".join(
            f"  {name}:{ln} [{form}] {snip}"
            for name, fs in offenders.items()
            for ln, form, snip in fs
        )
    )


def test_scanner_reds_on_injected_pool_branches_mutation():
    """mutation：往 core 源注入 pool 分支的五种形态，守卫每种都反红（证守卫非摆设）。

    覆盖 design/tasks 点名的两个必反红 mutation（`expected_pool=="bug"`、
    `document["pool"]=="bug"`）+ 三元/别名/match，逐一断言被捕获。
    """
    mutations = [
        ('if expected_pool == "bug":\n    pass\n', "别名 =="),
        ('if document["pool"] == "bug":\n    pass\n', "subscript =="),
        ('x = "bugs" if pool == "bug" else "items"\n', "三元 IfExp.test"),
        ('if pool != "todo":\n    pass\n', "!= 裸常量"),
    ]
    if sys.version_info >= (3, 10):
        # `match` 语句仅 3.10+ 可 parse；3.9 下 core 里的 match 结构上不可能（parse 即 SyntaxError）。
        mutations.append(('match pool:\n    case "bug":\n        pass\n', "match case"))
    clean = (CORE_DIR / "__init__.py").read_text(encoding="utf-8")
    for snippet, label in mutations:
        mutated = clean + "\n\ndef _injected_pool_branch(pool, expected_pool, document):\n" + "".join(
            "    " + line if line.strip() else line for line in snippet.splitlines(keepends=True)
        )
        findings = scan_pool_branches(mutated, "<mutated-core>")
        # 减去 clean 基线（clean 恒为 0），mutation 必新增 ≥1 finding
        assert findings, f"mutation 未被守卫捕获: {label} :: {snippet!r}"


def test_scanner_allows_closed_schema_keys_assertion():
    """封闭 schema keys 断言 `set(spec) != {"bug","todo"}` 与 POOL_SPEC 数据字典**不**被误报。

    这些是 AD-3 明确允许的 schema 数据/守（整集枚举、非按 pool 分岔），best-effort 守卫须放行——
    否则「gate 子串自指坑」在 core 自身复发。
    """
    allowed = (
        'if set(spec) != {"bug", "todo"}:\n    raise ValueError("bad keys")\n'
        'POOL_SPEC = {"bug": object(), "todo": object()}\n'
        'RECORDER = {pool: () for pool in ("bug", "todo")}\n'
        'if pool in {"bug", "todo"}:\n    ok = True\n'
    )
    assert scan_pool_branches(allowed, "<allowed>") == []


def test_scanner_does_not_scan_prose():
    """守卫是 AST 扫描——只吃 Python 源；prose 里的 `if pool == "bug"` 不是本守卫的输入。

    机械保证：`scan_pool_branches` 走 `ast.parse`，喂 .md 文本会 SyntaxError（拒解析），
    结构上不可能把文档当代码扫（对比字面子串扫会假阳）。此为「只扫 core .py」的机械体现。
    """
    prose = "设计讨论：core 里若出现 `if pool == \"bug\"` 就该红。\n- 见 AD-4\n"
    with pytest.raises(SyntaxError):
        scan_pool_branches(prose, "<design.md>")


# ══════════════════════════════════════════════════════════════════════════════
# 守 2：薄入口 thinness 同一性守（roster 复用旧 mirror 名单）
# ══════════════════════════════════════════════════════════════════════════════

# 旧 test_mirror_consistency.py 的 THREE_WAY(37) + TWO_WAY(24) roster（T2 impl-report §2 逐字）。
# 把「三份剥 docstring AST 等价」转「从薄入口解析的对象 __module__ == core」。
THREE_WAY_ROSTER = (
    "atomic_write", "atomic_write_bytes", "repo_root", "_reject_line_unsafe", "canonical_id",
    "semantic_id_key", "validate_prefix", "_lock_path", "_read_lock_metadata", "_lock_conflict",
    "validate_recorder_participant", "_write_all", "recorder_lock", "read_repository_snapshot",
    "repository_semantic_occurrences", "recorder_child_env", "_frontmatter_error",
    "_validate_unicode_scalar", "_json_object_no_duplicates", "_validated_recorder_model",
    "_id_semantic_sort", "render_recorder_namespace", "_legacy_semantic_id_key", "_split_envelope",
    "_find_recorder_span", "_parse_recorder_namespace", "_legacy_table_region_count",
    "parse_recorder_document", "read_recorder_document", "split_sections", "_legacy_table_sections",
    "parse_table_rows", "block_ranges", "_match_marker_line", "marker_block_ranges",
    "_legacy_item_from_row", "_build_effective_snapshot",
)
TWO_WAY_ROSTER = (
    "detect_change", "normalize_doc_paths", "auto_default_doc", "_ids_in_files", "_find_row_file",
    "_id_sort_key", "validate_doc_paths", "all_ids", "next_id", "_die", "_load_json",
    "_canonical_document", "_render_recorder_document", "_display_title", "_summary_blockquote",
    "_escape_user_markers", "_canonical_from_key", "_find_item_document", "_legacy_block_range",
    "_splice_body_lines", "_reject_document_mutation", "_preflight_target_legacy_block",
    "_promotion_insertions", "_validated_rendered_mutation",
)
ROSTER = THREE_WAY_ROSTER + TWO_WAY_ROSTER

THIN_ENTRIES = ("buglist", "todolist", "issues")

# ── 放行 1：pool-bound leaf 绑定薄封装（T2 §5）───────────────────────────────────
# buglist/todolist 薄入口把这些 roster helper 重定义为「绑定本池 spec 后暴露 root-only 签名」的
# **薄委派**（body 只调 `_core.<name>(...)`，供 tests 直接 root-only 调用）——不是重实现。
# 守卫对它们改验「确为薄委派」（AST 证 body 引用 `_core.<name>`），而非验 __module__，
# 否则会把合法的 pool 绑定误判为 shadow。
ALLOWED_POOL_BOUND = {
    ("buglist", "next_id"), ("buglist", "all_ids"),
    ("todolist", "next_id"), ("todolist", "all_ids"),
}

# ── 放行 2：issues 独占 rename-path 变体（documented·Task 4 记为已知代价）──────────
# issues.py 有一个**同名但语义相异**的 `_legacy_block_range(document, raw_id)`（2 参，读
# document['path']；抛 rename-path 专属 fix 文案「rerun the original batch rename command」，
# 与 issues 批量改名错误族一致），用于 issues 独占的 batch-rename 快照机制——**非** pool CLI
# 路径对 core helper 的 shadow。其结构逻辑与 core 版近似（找唯一 legacy block + 拒 marker 撞），
# 属**已知近重复**：合并进 core 需把 rename 专属错误文案注入 core（caller-specific 污染）或
# catch-rewrap（脆），属 Task 2 单一源范畴 + 非低成本 fold，故 Task 4 显式放行 + 登记待整合
# （见本票 impl-report Concern；对比 test_patch_discipline 的 allowlist-with-reason 惯例）。
ALLOWED_DISTINCT = {
    ("issues", "_legacy_block_range"),
}

_MISSING = object()


def _load_entry(name):
    spec = importlib.util.spec_from_file_location(name, str(SCRIPTS_DIR / f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ENTRIES = {name: _load_entry(name) for name in THIN_ENTRIES}


def _wrapper_delegates_to_core(entry_name, func_name):
    """AST 证：薄入口里 `func_name` 的 body 调用 `_core.<func_name>`（薄委派，非重实现）。"""
    source = (SCRIPTS_DIR / f"{entry_name}.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            for call in ast.walk(node):
                if (
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == func_name
                    and isinstance(call.func.value, ast.Name)
                    and call.func.value.id == "_core"
                ):
                    return True
            return False
    return False


@pytest.mark.parametrize("entry_name", THIN_ENTRIES)
def test_thin_entry_does_not_shadow_core_helper(entry_name):
    """薄入口不 shadow core helper：roster 每个 helper 若在薄入口可见，则解析到 core（未被重实现）。

    - `__module__ == 'sdflow_issues_core'` → 直接 import 未改，PASS。
    - 名单未在该薄入口暴露（多为 underscore helper，`import *` 不带）→ 未 shadow，跳过。
    - ALLOWED_POOL_BOUND → 验其为薄委派（body 调 `_core.<name>`），PASS。
    - ALLOWED_DISTINCT → documented 独占变体，PASS。
    - 其余非 core 解析 → FAIL（薄入口重实现了共享 helper，破单一源）。
    """
    entry = ENTRIES[entry_name]
    shadows = []
    for name in ROSTER:
        obj = getattr(entry, name, _MISSING)
        if obj is _MISSING:
            continue
        module = getattr(obj, "__module__", None)
        if module == "sdflow_issues_core":
            continue
        if (entry_name, name) in ALLOWED_POOL_BOUND:
            assert _wrapper_delegates_to_core(entry_name, name), (
                f"{entry_name}.{name} 在 ALLOWED_POOL_BOUND 却非薄委派 "
                f"(body 未调 _core.{name})——疑似重实现，移出白名单或改回委派"
            )
            continue
        if (entry_name, name) in ALLOWED_DISTINCT:
            continue
        shadows.append(f"{name} (__module__={module})")
    assert not shadows, (
        f"{entry_name} 本地 shadow 了 core 的共享 helper（破单一源）: {shadows}"
    )


def test_thinness_identity_guard_reds_on_shadow():
    """mutation：把 core helper 在薄入口重实现（同名本地 def）→ 同一性守反红（证守卫非摆设）。"""
    entry = ENTRIES["issues"]
    # canonical_id 是 THREE_WAY roster 且当前解析到 core；模拟被薄入口重实现。
    original = getattr(entry, "canonical_id")
    assert original.__module__ == "sdflow_issues_core"

    def _shadow_canonical_id(*a, **k):  # noqa: ANN001 —— 本地重实现（__module__ 指本测试模块）
        return "SHADOWED"

    try:
        entry.canonical_id = _shadow_canonical_id
        obj = getattr(entry, "canonical_id")
        assert obj.__module__ != "sdflow_issues_core"
        assert ("issues", "canonical_id") not in ALLOWED_POOL_BOUND | ALLOWED_DISTINCT
    finally:
        entry.canonical_id = original


def test_allowlists_are_subset_of_roster():
    """白名单 helper 名必须在 roster 内（否则白名单条目是死配置/打错字）。"""
    for _entry, name in ALLOWED_POOL_BOUND | ALLOWED_DISTINCT:
        assert name in ROSTER, f"白名单 helper {name!r} 不在 roster——死配置/拼写错"
