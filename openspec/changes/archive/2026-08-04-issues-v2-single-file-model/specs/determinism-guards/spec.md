## Purpose

`issues-v2-single-file-model` 把 issues 台账从「三薄入口 + 共享 `sdflow_issues_core` 包 + `POOL_SPEC`
注入 + `batches.md` 批次注册表」的 v1 架构改造为单文件模型（单一入口 `issues_v2.py`，pool 差异内联
为脚本常量，无批次机制）。本 delta 移除三条随该架构一并消解、失去校验对象的机械守卫 Requirement；
本 capability 内与 issues 台账无关的 `config.yaml` 结构 lint Requirement 不受影响，不在本 delta 内。

## REMOVED Requirements

### Requirement: recorder 镜像 helper 由「剥 docstring 后 AST 等价」一致性测试守护

**Reason**：本 Requirement 守护的对象是共享包 `sdflow_issues_core`（含 `POOL_SPEC` 封闭 schema、
无 pool 分支的 AST 级扫描、薄入口 thinness 同一性守、`direct↔scan golden` 接线守）。
`issues-v2-single-file-model` 把三薄入口（`issues.py`/`buglist.py`/`todolist.py`）与
`sdflow_issues_core` 包一并替换为单一文件 `issues_v2.py`——pool 差异（终态词表、特有字段）内联为
脚本内常量，不再有跨脚本共享包，也不再有需要经 `POOL_SPEC` 注入的分岔点。本 Requirement 列出的
全部机械守卫（AST 级无 pool 分支扫描、`POOL_SPEC` 完备性守、thinness 同一性守、golden 接线守）均
失去校验对象。

**Migration**：无等价机制需要移植——单文件脚本内联少量池差异常量（如 `POOL_PREFIX`/
`STATUS_VALUES`/`TERMINAL_STATUSES`），一致性由「唯一物理源、无第二份实现」这一结构事实保证，
不需要机械守卫代为维持（无对象可比较即无漂移可能）。`validate_scan_envelope` 一类的 producer/
consumer contract 校验语义在 v2 由 `issues-v2-storage` 能力的 STOR-07（`scan` 命令）覆盖。

### Requirement: batches.md 人写字段由 fail-closed grammar lint 校验

**Reason**：`issues.py batch lint` 子命令与其校验对象 `openspec/issues/batches.md` 均随批次机制
一并砍除——`issues-v2-single-file-model` 的单文件模型不再有「批次」这一维度（PLANNED 批次的计划
文本在迁移时已搬入对应 issue 的 body，见 `issues-migration` 能力），没有 `batches.md` 文件、没有
`优先级:`/`计划:` 人写字段需要校验。

**Migration**：无——`batches.md` 文件本身不存在于 v2 目录结构（`openspec/issues/{open,closed}/` +
`INDEX.md` + `CLOSED.md`），无字段、无 grammar 需要 lint。

### Requirement: 确定性守卫不越权、不破 D4 隔离

**Reason**：本 Requirement 的两条约束（「共享逻辑经同目录 `from sdflow_issues_core import` 获得，
不跨目录 import」「`batch lint` 不覆写人写行」）分别锚定于已被移除的 `sdflow_issues_core` 共享包
与已被移除的 `batches.md`/`batch lint`。两个约束对象均不存在，Requirement 本身失去锚点。

**Migration**：无——单文件脚本 `issues_v2.py` 不存在跨模块 import 边界需要守卫（无共享包可越权
import）；`set-status` 对 body 的操作语义（只追加状态变更历史、MUST NOT 覆写已有内容）已在
`issues-v2-storage` 能力的 STOR-06（`set-status` 校验）内以正面 Requirement 的形式承接，不需要
本条这类"不越权"式的否定式约束。
