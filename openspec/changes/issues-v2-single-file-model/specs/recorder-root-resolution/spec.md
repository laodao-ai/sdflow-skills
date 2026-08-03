## Purpose

`issues-v2-single-file-model` 把 issues 台账的三个薄入口（`issues.py`/`buglist.py`/`todolist.py`，
共享 `sdflow_issues_core` 包）合为单一入口 `issues_v2.py`（无共享包、无子进程 sibling 调用、无仓级
`.recorder.lock`）。本 delta 把仓根解析相关 Requirement 的「三薄入口」措辞与机制更新为「单入口」，
并移除随仓级锁一并消失的跨进程根分裂已知缺口（B15）——v2 单进程内直接完成 add/set-status/scan/
reindex，不再以 `--root` 拉子进程，B15 描述的失效路径已无载体。

## MODIFIED Requirements

### Requirement: recorder 仓根解析对外部进程输出 fail-closed

单一入口 `sdflow-issues/scripts/issues_v2.py` 在把任何值当作可写仓根前 MUST 证明其为调用起点所属
仓库最近根，校验失败 MUST NOT 产生任何目录/文件。

> `issues-v2-single-file-model`：三薄入口（`issues.py`/`buglist.py`/`todolist.py`）与共享
> `sdflow_issues_core` 包已被单一入口 `issues_v2.py` 取代——仓根解析逻辑内联进该单文件脚本，
> 不再有跨脚本共享包。**仓根解析的 fail-closed 校验序列、单点解析边界、语义一字不变**——本条为
> 单入口化后的地址更新，非逻辑变更。

`issues_v2.py` 的 `repo_root()` 在把任何值当作「可写仓根」之前，MUST 证明该值确实是调用起点所属
仓库的**最近**根，而不是仅凭 `git rev-parse --show-toplevel` 的 stdout 形状（非空 / 绝对路径 / 是
目录）放行。校验失败 MUST NOT 产生任何目录或文件，MUST NOT 以该值为前缀拼接任何写入路径。

#### Scenario: git 返回合法仓根

- **WHEN** `git rev-parse --show-toplevel` 以 rc=0 返回一个存在的绝对路径目录，且它是 `start` 的祖先或等于 `start`，并且是起点上溯到的最近仓库
- **THEN** `repo_root(start)` 返回其 `realpath`

### Requirement: 仓根在单次调用内只解析一次

`issues_v2.py` 的每个**进程**MUST 只解析一次仓根。`main()` 解析后写回 `args.root`，其余 `cmd_*`
函数 MUST 直接使用该已验证值，MUST NOT 再次调用 `repo_root()`。

> `issues-v2-single-file-model`：v1 版本此处记录了一条已知缺口（B15，跨进程根分裂——`_scan_pool`/
> `cmd_sweep` 以 `--root` 拉子进程时，子进程若因 `.git` 在两次解析间消失而解析出不同的根，
> `RecorderLockError` 会被父进程 `main()` 的 except 吞掉、回落 owner 模式静默写入错误根）。
> **该缺口随 v2 架构改造一并消解，非被修复**：`issues_v2.py` 不再以 `--root` 拉起任何子进程
> （`add`/`set-status`/`scan`/`reindex`/`next-id` 全部在同一进程内完成，唯一子进程调用是
> 直接执行 `git`/`git mv`/`git add` 本身，不是递归调用自己）；也不再有仓级 `.recorder.lock` /
> `RecorderLockError` / owner-participant 模式——单文件模型的并发保护是文件名级 `O_CREAT|O_EXCL`
> （见 `issues-v2-storage` 能力），不存在"父进程持锁、子进程重解析根"这条失效路径的前提。
> B15 描述的 Scenario 与其 `xfail(strict=True)` 机械锚已随之移除（`sdflow-issues/tests/` 已无
> 该用例，见 `test_repo_root_identity_issues.py`）。

**边界定义**：本要求的作用域是**进程**——`issues_v2.py` 单进程内完成全部命令处理，无需跨子进程
重申"每进程一次"的边界（v1 版本这里讨论的子进程重解析场景在 v2 不存在）。

#### Scenario: cmd_* 不再自行解析
- **WHEN** 任一 `cmd_*` 函数需要仓根
- **THEN** 它直接读取 `args.root`（已由 `main()` 解析并校验）
- **AND** `issues_v2.py` 的 `cmd_*` 函数体内 MUST NOT 出现 `repo_root(` 调用

### Requirement: fail-closed 校验单一物理源

`repo_root` 及其 fail-closed 校验序列 MUST 只有唯一物理源。

> `issues-v2-single-file-model`：v1 版本此处描述「三薄入口经同目录 `from sdflow_issues_core import`
> 获得同一实现、由 thinness 同一性守维持一致性」——该机制依赖存在多个薄入口 + 共享包的间接层。
> v2 把三入口与共享包合一为单一文件 `issues_v2.py`，`repo_root` 直接定义在该文件内，**连"薄入口
> import 共享包"这层间接都不存在**——不是"单一源 + 守卫维持一致"，而是物理上唯一实现、无第二份
> 可漂移的拷贝，一致性问题不再有意义（无从比较）。原「薄入口 thinness 同一性守」随之失去对象。

#### Scenario: 单一物理实现，无镜像可漂移

- **WHEN** 需要修改 `repo_root` 的 fail-closed 校验逻辑
- **THEN** 存在唯一物理编辑位置——`issues_v2.py` 内的 `repo_root()` 函数定义；不存在任何薄入口或
  共享包意义上的第二份实现需要保持同步

### Requirement: 坏 root 下的 reindex 不得静默通过派生字节校验

`issues_v2.py reindex` 在 root 解析结果不可用时 MUST NOT 出现「因为根本没访问目标目录、所以目标
文件字节未变」的假绿。针对派生字节保护的测试 MUST 在 reindex 实际写入目标目录时才可能通过。

> `issues-v2-single-file-model`：本条原引用 `batches.md` 作为 reindex 派生字节保护对象之一——v2
> 已砍批次机制，`batches.md` 不存在；`reindex` 的派生产物收窄为 `INDEX.md` + `CLOSED.md` 两个文件，
> 保护语义（root 不可用/坏 scan 输出时目标文件字节不变、无泄漏）不变，仅保护对象随目录结构调整。

#### Scenario: 变异验证——写入即变红
- **WHEN** 故意让 `reindex` 向 `tmp_path` 下的 `INDEX.md` / `CLOSED.md` 写入内容
- **THEN** 对应的派生字节保护测试失败（暴露"未真正写入却判通过"的假绿）

#### Scenario: 坏 root 下 reindex 不产生任何写入
- **WHEN** `repo_root` 解析失败（校验不通过）
- **THEN** `reindex` 命令 MUST NOT 对任何目录/文件产生写入或创建，`INDEX.md`/`CLOSED.md` 若已存在则字节保持不变
