## MODIFIED Requirements

### Requirement: fail-closed 校验在三份 recorder 间逐字一致

`repo_root` 及其 fail-closed 校验序列 MUST 收敛为唯一物理源，三薄入口经同目录 package import 获得同一实现，一致性由「单一源 + thinness 同一性守」维持。

> `[spec-review-amendment]`（`dedupe-issues-scripts-shared-layer`）：原 requirement 以「三份 recorder 各自内联 `repo_root`、
> 由 `determinism-guards` 三向 AST 镜像断言守逐字一致」为前提。三 skill 合一为 `sdflow-issues`、共享逻辑收敛为唯一命名
> package `sdflow_issues_core`（`adr/0027`）后，`repo_root` 及其 fail-closed 校验序列**物理只剩一份**——三向 AST 镜像
> 断言失去对象、随 `determinism-guards` 的 `test_mirror_consistency.py` 一并退役。逐字一致从「事后拦漂移」升级为
> 「单一源结构上无从漂移」。

`repo_root` 及其 fail-closed 校验序列 MUST 收敛为**唯一物理源** `sdflow-issues/scripts/sdflow_issues_core/`（THREE_WAY
共享 helper），三薄入口（`buglist.py`/`todolist.py`/`issues.py`）经同目录 `from sdflow_issues_core import` 获得同一实现。
一致性 MUST 由「单一源 + 薄入口 thinness 同一性守（`repo_root` 从薄入口 `getattr` 解析对象 `__module__ == 'sdflow_issues_core'`，
未被 shadow）」维持；原「剥 docstring 后 `ast.dump` 三向相等」镜像断言 SHALL 删除（无对象）。fail-closed 校验的**语义**
（对外部进程输出证明最近仓根、失败不产生任何目录/文件）MUST NOT 因合一而改变。

#### Scenario: 单一源无镜像可漂移

- **WHEN** 需要修改 `repo_root` 的 fail-closed 校验逻辑
- **THEN** 存在唯一物理编辑源 `sdflow_issues_core`，无需在多份间保持同步；不存在承载 `repo_root` 的同名镜像函数对

#### Scenario: 薄入口未 shadow repo_root

- **WHEN** 检查三薄入口获取 `repo_root` 的方式
- **THEN** 经同目录 `from sdflow_issues_core import` 获得；`repo_root` 从薄入口解析对象 `__module__ == 'sdflow_issues_core'`，任一薄入口本地重定义即被 thinness 同一性守拦红

### Requirement: recorder 仓根解析对外部进程输出 fail-closed

三份 recorder 薄入口（均在 `sdflow-issues/scripts/`）在把任何值当作可写仓根前 MUST 证明其为调用起点所属仓库最近根，校验失败 MUST NOT 产生任何目录/文件。

> `[spec-review-amendment]`（`dedupe-issues-scripts-shared-layer`）：仅**路径引用**随合一同步——三 recorder 由分居
> `sdflow-buglist`/`sdflow-todolist`/`sdflow-issues` 三 skill 目录改为同居 `sdflow-issues/scripts/`（薄入口）+ 共享
> `sdflow_issues_core`（校验实现）。**仓根解析的 fail-closed 校验序列、单点解析边界、语义一字不变**——本条为地址更新，非逻辑变更。

三份 recorder 的薄入口（`sdflow-issues/scripts/issues.py`、`sdflow-issues/scripts/buglist.py`、
`sdflow-issues/scripts/todolist.py`）在把任何值当作「可写仓根」之前，MUST 证明该值确实是调用起点所属仓库的**最近**根，
而不是仅凭 `git rev-parse --show-toplevel` 的 stdout 形状（非空 / 绝对路径 / 是目录）放行。校验实现收敛于共享
`sdflow_issues_core` 的 `repo_root`。校验失败 MUST NOT 产生任何目录或文件，MUST NOT 以该值为前缀拼接任何写入路径。

本要求适用于三份 recorder 薄入口（均在 `sdflow-issues/scripts/`）：`issues.py`、`buglist.py`、`todolist.py`。

#### Scenario: git 返回合法仓根

- **WHEN** `git rev-parse --show-toplevel` 以 rc=0 返回一个存在的绝对路径目录，且它是 `start` 的祖先或等于 `start`，并且是起点上溯到的最近仓库
- **THEN** `repo_root(start)` 返回其 `realpath`
