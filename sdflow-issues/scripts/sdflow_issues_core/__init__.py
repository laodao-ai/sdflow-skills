"""sdflow_issues_core — issues 台账三脚本（buglist/todolist/issues 薄入口）的唯一共享逻辑源。

（dedupe-issues-scripts-shared-layer · adr/0027）三 skill 合一为 `sdflow-issues` 后，
bug/todo/issues 共享的执行逻辑收敛到本 package，作**唯一物理编辑源**；三薄入口
`from sdflow_issues_core import ...` 取用。**唯一命名**（非裸 `core`）避免全局
`sys.modules["core"]` 与别处同名模块碰撞（AD-1 / SC-R2）。

本文件是 Task 1 的 FOUNDATION：只承载 **POOL_SPEC 封闭 schema + 其守卫底座**。
CLI 执行逻辑（THREE_WAY helper / TWO_WAY 镜像）由后续 Task 2 逐命令上移——此处**尚未**迁入。

## POOL_SPEC 是差异注入的唯一入口

bug↔todo 的一切差异（文件粒度、目录、legacy glob、特定字段、状态词表、终态集、
ID 前缀、scan 输出键）收敛为一张**封闭 schema** 参数表 `POOL_SPEC`。将来上移到 core 的
共享逻辑按注入的 `PoolSpec` 取值——**MUST NOT** 在 core 源码里出现针对 pool 值
（`"bug"`/`"todo"`）的条件分支，也 MUST NOT 从 argparse default / 硬编码常量 / 任意
callable 逃生口引入新差异。新增差异维 = 改 `PoolSpec` 字段 **且** 同步 `POOL_SPEC_FIELDS`
注册表（两处一起改，schema 漂移守拦住只改一处）。

封闭性 + 关系正确性（`terminal_set ⊆ status_values`、keys 恰为 `{"bug","todo"}`）在
import 时 fail-closed 自校验（`validate_pool_spec()`）；与外部权威常量
（`issues.RECORDER_POOL_CONFIG`）的逐值一致由 `tests/test_pool_spec_schema.py` 守。
"""

from dataclasses import dataclass, fields


class PoolSpecError(ValueError):
    """POOL_SPEC 封闭 schema / 关系正确性被破坏（缺维、越界 pool、终态越词表、非法值）。"""


@dataclass(frozen=True)
class PoolSpec:
    """一个 pool（bug 或 todo）的全部差异维——封闭 schema，required 维 = 字段全集。

    新增差异维 MUST 在此加字段 **并** 同步 `POOL_SPEC_FIELDS`；不得把差异硬编码进
    core 逻辑 / argparse default / callable。字段全部为不可变值（`frozenset` 而非
    `set`），差异不可被运行期改写。
    """

    # 文件粒度：bug=日（file_for_date / today_str）；todo=月（file_for_month / this_month）
    date_granularity: str          # "day" | "month"
    file_stem: str                 # dated 文件干 + issues 子目录叶名："buglist" | "todolist"
    # 目录（相对 repo root 的 canonical issues 目录，对应 buglists_dir / todolists_dir）
    issues_dir: str                # "openspec/issues/buglist" | "openspec/issues/todolist"
    # legacy dir glob（过渡期 dual-read 的旧目录，对应 legacy_buglists_dir / legacy_todolists_dir）
    legacy_dir_glob: str           # "openspec/buglists/*.md" | "openspec/todolists/*.md"
    # 特定字段：字段名与其合法枚举成对
    specific_field: str            # "priority" | "type"
    specific_values: frozenset     # PRIORITIES | TYPE_TAGS
    # 状态词表
    status_values: frozenset
    # 终态集（MUST ⊆ status_values）
    terminal_set: frozenset
    # ID 前缀（canonical_id 空间隔离依赖它）
    default_prefix: str            # "B" | "T"
    # scan JSON envelope 的 item 数组键
    scan_output_key: str           # "bugs" | "items"


# 差异维注册表 —— 「新增维必须改 schema」的机械化锚点。**手写字面**（MUST NOT 由
# fields(PoolSpec) 自动派生——自动派生会让下面的漂移守恒真、拦不住任何东西）：给 PoolSpec
# 加/删字段却漏改此处 ⇒ 注册表 ≠ 字段全集 ⇒ validate_pool_spec() import 时 fail-closed。
# 这把「引入一个新差异维」强制成一次自觉的两处编辑（另有 Task 4 的 AST 无分支守正面保证
# 差异确实走 POOL_SPEC、没从 core 硬编码后门漏进）。
POOL_SPEC_FIELDS = (
    "date_granularity",
    "file_stem",
    "issues_dir",
    "legacy_dir_glob",
    "specific_field",
    "specific_values",
    "status_values",
    "terminal_set",
    "default_prefix",
    "scan_output_key",
)


POOL_SPEC = {
    "bug": PoolSpec(
        date_granularity="day",
        file_stem="buglist",
        issues_dir="openspec/issues/buglist",
        legacy_dir_glob="openspec/buglists/*.md",
        specific_field="priority",
        specific_values=frozenset({"P0", "P1", "P2", "P3", "P4"}),
        status_values=frozenset(
            {"OPEN", "VERIFIED", "PROPOSED", "IN_PROGRESS", "FIXED", "WONTFIX", "BLOCKED"}
        ),
        terminal_set=frozenset({"FIXED", "WONTFIX"}),
        default_prefix="B",
        scan_output_key="bugs",
    ),
    "todo": PoolSpec(
        date_granularity="month",
        file_stem="todolist",
        issues_dir="openspec/issues/todolist",
        legacy_dir_glob="openspec/todolists/*.md",
        specific_field="type",
        specific_values=frozenset({"性能优化", "可观测性", "代码质量", "功能增强", "基础设施"}),
        status_values=frozenset({"OPEN", "PROPOSED", "DONE", "WONTDO"}),
        terminal_set=frozenset({"DONE", "WONTDO"}),
        default_prefix="T",
        scan_output_key="items",
    ),
}


def validate_pool_spec(spec=None):
    """校验一份 POOL_SPEC 映射的封闭性 + 关系正确性，违规抛 PoolSpecError（fail-closed）。

    只做**数据面**的 intra-schema 校验（不触外部常量，避免与 issues.py 循环 import）：
      - keys 恰为 {"bug","todo"}（额外/缺失 pool key 即红）
      - 每个 pool 值是 PoolSpec 实例（非裸 dict 等逃生口）
      - 字段注册表 == PoolSpec 字段全集（新增维未同步 schema 即红）
      - terminal_set ⊆ status_values（终态不得越出状态词表）

    与 `RECORDER_POOL_CONFIG` / `TERMINAL_STATUSES` 现值的逐值一致由 tests 守（外部对照源）。
    """
    if spec is None:  # 避免可变模块级 dict 作默认参数；缺省即校验模块级 POOL_SPEC
        spec = POOL_SPEC
    if set(spec) != {"bug", "todo"}:
        raise PoolSpecError(
            f"ERROR: POOL_SPEC keys 必须恰为 {{'bug','todo'}}，实际 {sorted(spec)}; "
            f"cause: 越界/缺失 pool key; fix: 只保留 bug/todo 两池"
        )
    registry = set(POOL_SPEC_FIELDS)
    schema_fields = {f.name for f in fields(PoolSpec)}
    if registry != schema_fields:
        raise PoolSpecError(
            f"ERROR: POOL_SPEC_FIELDS 注册表与 PoolSpec 字段全集不一致；"
            f"注册表独有 {registry - schema_fields}，schema 独有 {schema_fields - registry}; "
            f"cause: 新增/删除差异维只改了一处; fix: 同步改 PoolSpec 字段与 POOL_SPEC_FIELDS"
        )
    for pool, value in spec.items():
        if not isinstance(value, PoolSpec):
            raise PoolSpecError(
                f"ERROR: POOL_SPEC[{pool!r}] 不是 PoolSpec 实例（{type(value).__name__}）; "
                f"cause: 差异从封闭 schema 之外的裸值塞进; fix: 用 PoolSpec(...) 承载全部差异维"
            )
        if not value.terminal_set <= value.status_values:
            raise PoolSpecError(
                f"ERROR: POOL_SPEC[{pool!r}].terminal_set {set(value.terminal_set)} "
                f"⊄ status_values {set(value.status_values)}; "
                f"cause: 终态越出状态词表; fix: 终态集必须是状态词表子集"
            )
    return True


# import 时 fail-closed 自校验：POOL_SPEC 一旦被改成非法形态，任何 import 本 package
# 的代码（含全部 CLI 薄入口与测试）当场炸——不给「装载后才发现」的窗口。
validate_pool_spec()
