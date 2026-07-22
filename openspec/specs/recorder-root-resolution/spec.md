# recorder-root-resolution Specification

## Purpose

三份 recorder 薄入口（`sdflow-issues/scripts/issues.py`、`sdflow-issues/scripts/buglist.py`、
`sdflow-issues/scripts/todolist.py`，均在同一 `sdflow-issues/scripts/` 目录下）在把任何值当作
「可写仓根」之前，MUST 证明该值确实是调用起点所属仓库的**最近**根，而不是仅凭
`git rev-parse --show-toplevel` 的 stdout 形状（非空 / 绝对路径 / 是目录）放行。本能力管辖仓根
解析本身的 fail-closed 校验序列、单进程内的单点解析边界、三薄入口经共享 `sdflow_issues_core`
获得同一实现的一致性，以及与之配套的测试基础设施（cwd 副作用回归断言、reindex 假绿防护）。
## Requirements
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

### Requirement: 仓根在单次调用内只解析一次

recorder 的每个**进程**MUST 只解析一次仓根。`main()` 解析后写回 `args.root`，其余
`cmd_*` 函数 MUST 直接使用该已验证值，MUST NOT 再次调用 `repo_root()`。

**边界定义**：本要求的作用域是**进程**，不是逻辑命令。`_scan_pool` / `cmd_sweep` 以
`--root <已解析值>` 拉起的子进程，其自身 `main()` 仍会解析一次——跨进程看是「每进程一次」。

**理由不是省一次子进程**：`repo_root()` 的校验是**逐次独立**的，不保证两次解析得到同一个仓。
`git rev-parse --show-toplevel` 会沿目录树向上搜索，若两次解析之间目标目录失去自己的 `.git`
（`git worktree prune` / 误删 / fixture 清理），第二次会静默爬升到**外层祖先仓库**——两次都
rc=0、都通过全部校验，但锁建在一个根上、数据写进另一个根。

**⚠️ 已知缺口（B15，P1，跨进程根分裂）**：本要求原意由 `validate_recorder_participant` 的
path/token 绑定在跨进程层面兜底——子进程若解析出与父进程持锁时不同的根，理应在其 `_lock_path`
处因无锁文件而以 `RecorderLockError` 响亮失败。**该兜底当前不成立**：三份 recorder 的
`main()`（`issues.py:194` / `buglist.py:207` / `todolist.py:207`）捕到
`RecorderLockError` 后会**回落到 owner 模式**，根分裂的子进程转而在自己解析出的外层根
**静默 `makedirs` 并以 rc=0 退出**——双向独立复现（implementer 实测 + 双轴审 Spec 轴各一次）。
影响面非边角：`issues.py` 有 6 处生产代码以 `--root` 拉子进程（sweep / auto-reindex /
batch add / per-type，见 B15 完整站点列表）。已知修法（B15 记录）——新增
`SDFLOW_RECORDER_LOCK_ROOT` 环境变量、由 `recorder_child_env` 下传父进程 `realpath`、
`recorder_lock` 判「变量存在且与本进程解析根不同 ⇒ 响亮失败」——因涉及三份同步 + AST 镜像
+ 触及 lock 相关 spec，须走独立设计门，不在 `harden-repo-root-fail-closed` 内 fold。测试套件
已就该缺口留有 `xfail(strict=True)` 机械锚：一旦此缺口被堵上而该锚仍标 xfail，测试会以
XPASS 形式判红，逼迫锚随修复一起摘除。

#### Scenario: cmd_* 不再自行解析
- **WHEN** 任一 `cmd_*` 函数需要仓根
- **THEN** 它直接读取 `args.root`（已由 `main()` 解析并校验）
- **AND** 三份 recorder 的 `cmd_*` 函数体内 MUST NOT 出现 `repo_root(` 调用

#### Scenario: 锁与写入锚定同一个根
- **WHEN** 一次 `reindex` / `batch` 类命令在**同一进程内**持锁期间执行写入
- **THEN** `recorder_lock` 记录的 `repo` 与实际写入路径 MUST 源自同一次解析结果

#### Scenario: 子进程解析出不同的根时响亮失败〔已知缺口，见 B15，当前不成立〕
- **WHEN** 父进程持锁并以 `--root` 拉起子进程，而子进程重解析得到**不同**的根
      （两次解析之间目标失去 `.git`）
- **THEN**（目标态）子进程 MUST 以 `RecorderLockError` 失败，MUST NOT 静默写入其自行解析出的根
- **AND**（当前实况，B15）`RecorderLockError` 被子进程 `main()` 的 except 吞掉、回落 owner
      模式，子进程在其自行解析出的外层根**静默 `makedirs` + rc=0** —— 本 Scenario 由
      `xfail(strict=True)` 机械锚死，堵上 B15 前 MUST NOT 从本 spec 移除该锚定意图

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

### Requirement: 测试套件不得在当前工作目录留下副作用

本仓任一 pytest 用例 MUST NOT 在当前工作目录**新增顶层条目**（文件或目录）。**诚实边界**：
本约束不覆盖既存条目的内容改写、条目删除、新增条目**内部**的子目录变化，也不覆盖用例内部
`monkeypatch.chdir` 之后对**新** cwd 的写入——这些面无确定性的通用判据，不在本断言口径内。

该约束 MUST 由仓根**两个文件联合**机械保证，缺一即失效：

1. `conftest.py`——挂 `pytest_runtest_setup` / `pytest_runtest_call` / `pytest_runtest_teardown`
   三个 **hook wrapper**（`@pytest.hookimpl(wrapper=True)`），比对每个用例运行前后的 cwd
   顶层条目集，新增条目即失败并报出条目名。**MUST NOT 用 autouse fixture 实现**：autouse
   fixture 的 teardown 阶段若抛异常，pytest 会将该用例计为「passed + teardown error」，
   摘要行仍写 `1 passed`——泄漏被降级成脚注，观测不到真失败。hook wrapper 在 `call` 与
   `teardown` 两个阶段各查一次：`call` 阶段查是为了让失败落在货真价实的 `1 failed`（而非
   等到 `teardown` 才查、被同一降级问题反噬）。
2. `pytest.ini`（仅含 `[pytest]` 段 + `minversion = 8.0`）——把 `rootdir` 钉死在仓根。
   pytest 的 conftest 收集止于 `confcutdir`，其默认值就是 `rootdir`；没有任何 ini 文件时
   `rootdir` 是推断出来的，从仓根 cwd 跑会碰巧推对，但从仓外以绝对路径跑
   `pytest /abs/<skill>/tests/` 时 `rootdir` 会塌缩成 `<skill>/tests` 本身，仓根 `conftest.py`
   **根本不会被收集**，断言静默失效（双向变异实测确认：无 `pytest.ini` 时注入泄漏得
   `1 passed` 假绿，有则 `1 failed`）。`minversion = 8.0` 是同一职责的完整性前提，而非无关
   配置——`wrapper=True` 形式是 pytest 8+ 才有的协议，7.x 下 conftest 收集本身会报错。

MUST NOT 在各 skill 的 `tests/` 下复制多份同款文件——重复副本不在 `determinism-guards` 的
AST 镜像 roster 内，无守护即会漂移。

**收窄口径的既存依赖**：收窄为「禁止新增 cwd **顶层**条目」（而非早先「一切落盘物 MUST 位于
`tmp_path`」的更宽表述）是 Windows 泳道跨盘符探测用例（`_second_drive_probe`）合规存在的
前提——该用例在**另一盘符的根目录**（`tmp_path` 之外）建目录，但不落在当前工作目录的顶层，
故不违反本约束。

#### Scenario: 干净目录跑任一套件
- **WHEN** 在一个空目录中运行 `pytest <任一 skill>/tests/`
- **THEN** 套件结束后该目录的顶层条目数仍为 0（`.pytest_cache` 等 pytest 自身产物除外）

#### Scenario: 覆盖面为全仓而非仅 recorder
- **WHEN** 运行仓内任意 skill 的测试套件
- **THEN** cwd 副作用断言均生效，无需该 skill 自行注册或复制 conftest / ini
- **AND** 该覆盖依赖仓根 `pytest.ini` 把 `rootdir` 钉在仓根——缺失该文件时从仓外以绝对路径
      调用会使覆盖静默失效

#### Scenario: 泄漏被回归断言捕获
- **WHEN** 某个测试用例在工作目录下创建了目录或文件
- **THEN** 回归断言失败，并报出泄漏的条目名

### Requirement: 坏 root 下的 reindex 不得静默通过派生字节校验

`issues.py reindex` 在 root 解析结果不可用时 MUST NOT 出现「因为根本没访问目标目录、
所以目标文件字节未变」的假绿。针对派生字节保护的测试 MUST 在 reindex 实际写入目标目录时
才可能通过。

#### Scenario: 变异验证——写入即变红
- **WHEN** 故意让 reindex 向 `tmp_path` 下的 `INDEX.md` / `batches.md` 写入内容
- **THEN** `test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes` 失败

#### Scenario: 坏 scan 输出被受控拒绝且不误伤派生字节
- **WHEN** 子进程 `scan --json` 返回 `id` 为非字符串（`None` / 数字 / 列表 / 字典）的条目
- **AND** root 解析未被该 mock 污染（即 `repo_root` 得到真实的 `tmp_path`）
- **THEN** 进程以 exit code 2 结束，stderr 以 `ERROR: ` 开头并含 `scan item[0].id`、
      `; cause:`、`; fix:`，且不含 `Traceback`
- **AND** `tmp_path` 下的 `INDEX.md` 与 `batches.md` 字节保持不变
- **AND** 工作目录下未新增任何条目

#### Scenario: 拒绝理由必须可区分
- **WHEN** 测试断言 reindex 因坏 scan id 而失败
- **THEN** 断言 MUST 校验 stderr 的具体诊断内容（`scan item[0].id`），
      MUST NOT 仅凭 exit code 2 判定通过——坏 root 与坏 scan id 都会产生 exit 2，
      仅看退出码无法区分「测中了目标」与「在更早的关口就崩了」

