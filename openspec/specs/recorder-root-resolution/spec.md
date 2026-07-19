# recorder-root-resolution Specification

## Purpose

三份 recorder（`sdflow-issues/scripts/issues.py`、`sdflow-buglist/scripts/buglist.py`、
`sdflow-todolist/scripts/todolist.py`）在把任何值当作「可写仓根」之前，MUST 证明该值确实是
调用起点所属仓库的**最近**根，而不是仅凭 `git rev-parse --show-toplevel` 的 stdout 形状（非空
/ 绝对路径 / 是目录）放行。本能力管辖仓根解析本身的 fail-closed 校验序列、单进程内的单点解析
边界、三份实现间的逐字一致性，以及与之配套的测试基础设施（cwd 副作用回归断言、reindex 假绿
防护）。

## Requirements

### Requirement: recorder 仓根解析对外部进程输出 fail-closed

recorder 的 `repo_root(start)` MUST 在把任何值当作可写仓根返回之前，证明它是**起点所属仓库的
最近根**；MUST NOT 把 `git rev-parse --show-toplevel` 的 stdout 直接当仓根返回，MUST NOT 仅凭
路径形状（非空 / 绝对 / 是目录）放行。

**校验序列（九步，按序；任一步不满足即 fail-closed）**：

1. **起点可信性**：MUST 在调用 git **之前**完成。
   - `start` 未指定（`--root` 默认 `None`）：起点 MUST 由 `os.getcwd()` 求得；其 `OSError`
     （`FileNotFoundError`——进程 cwd 已被删除；`PermissionError`——父目录权限被撤，两者同为
     `OSError` 子类）MUST 转为受控 `ValueError`。**MUST NOT 只捕 `FileNotFoundError`**——
     漏捕 `PermissionError` 会让它裸着逃出本函数，调用方的 `except ValueError` 接不住。
     **MUST NOT 用 `os.path.isdir(".")` 代替起点校验**——cwd 被删除后它仍返回 `True`，
     校验形同虚设。
   - `start` 显式传入：MUST 通过 `os.path.isdir(start)`，否则抛 `ValueError`。
   - 起点随后归一化为绝对路径（`start=None` 或非绝对路径时与 `os.getcwd()` 拼接）。
     MUST NOT 用 `os.path.normpath` 做 lexical 归一化——对 `symlink-to-subdir/..` 会算出
     symlink 自身的父目录，而非内核实际解析的目标父目录。
2. **环境净化**：调用 git 前 MUST 从子进程环境剔除仓库/工作树发现类变量：`GIT_DIR`、
   `GIT_WORK_TREE`、`GIT_COMMON_DIR`、`GIT_CEILING_DIRECTORIES`、`GIT_INDEX_FILE`、
   `GIT_DISCOVERY_ACROSS_FILESYSTEM`、`GIT_CONFIG_COUNT`、`GIT_CONFIG_GLOBAL`、
   `GIT_CONFIG_SYSTEM`，以及前缀 `GIT_CONFIG_KEY_*` / `GIT_CONFIG_VALUE_*`。
   MUST NOT 改为「剔除所有 `GIT_*` + 白名单」——`GIT_EXEC_PATH` 等执行类变量必须保留。
3. **调 git**：以 `cwd=start` 运行 `git rev-parse --show-toplevel`，**捕获 bytes、MUST NOT 用
   `text=True`**——`text=True` 等于「按 locale 编码 + strict 解码」，而 Windows 上 locale 常态
   是 cp1252、git 输出是 UTF-8，解码会在 subprocess 读管道的线程内失败并让 `out.stdout` 变
   `None`，下游 `.rstrip` 抛 `AttributeError` 而非 `ValueError`，裸传播成 traceback（POSIX 下
   非 UTF-8 文件名同理不保证可解码）。`TimeoutExpired` 单独 `raise ValueError`（超时不等于
   「不在仓库里」，MUST NOT 回落）；`OSError` / `CalledProcessError` 只记为「git 未给出答案」，
   裁决交步骤 5，MUST NOT 在此处 return/raise。
4. **最近仓根 marker 上溯**：独立于 git 的第二信源。从起点的 `realpath` 逐级向上找第一个
   `os.path.exists(<dir>/.git)` 为真的目录（判 `exists` 而非 `isdir`——linked worktree 与
   submodule 的 `.git` 是**文件**）。找不到则一路到文件系统根，记为「未找到」。
5. **git 失败裁决**：仅当步骤 3 未给出答案时触发——
   - 步骤 4 找到了 marker（起点确实位于某个 git 仓库内，**含起点位于 `.git/` 目录内部**这类
     情形）⇒ **`raise ValueError`**（fail-closed，不是回落）。
   - 步骤 4 一层 marker 都没找到（真·非 git 仓库 / bare repo / git 不可用）⇒ 回落
     `os.path.abspath(start)`。
   > **回落判据是「上溯一层 marker 都找不到」，不是「git 退出码非 0」**：旧口径把整个非 0
   > 退出都归为回落，并枚举为「非 git 仓库 / git 不可用 / bare repo / `.git/` 目录内」——该
   > 枚举不完备，对 `detected dubious ownership`（`safe.directory`，rc=128）这类「确实在仓内、
   > git 仅仅拒绝作答」的情形是 **fail-open**：进程明明在仓内，旧实现却会回落返回起点自身
   > （往往是仓库子目录），下游 `makedirs` 就地造出第二套 `openspec/`。同理，**起点位于
   > `.git/` 目录内部**（如 `.git/hooks`）过去被当作「正常场景」回落，现在因步骤 4 能找到
   > 该仓的 marker 而改判 fail-closed——不再把 `.git/hooks` 当可写根返回。
6. **形状校验**：stdout 先按步骤 3 的 bytes 用 `os.fsdecode`（文件系统编码 +
   `surrogateescape`）解码，MUST NOT 用 `sys.getfilesystemencoding()` 手写等价实现——那只是
   把 `fsdecode` 的定义抄一遍、多一个漂移面。再以 `rstrip("\r\n")` 只剥行结束符（MUST NOT 用
   `strip()`——会删掉路径末尾的合法空格），结果 MUST 非空、`os.path.isabs`、`os.path.isdir`。
7. **祖先校验（主防线）**：`os.path.normcase(os.path.realpath(start))` MUST 位于
   `os.path.normcase(os.path.realpath(top))` 之内（相等或在其下）。比较 MUST 按**路径组件**
   进行（`os.path.commonpath` 或 `Path.is_relative_to`），MUST NOT 用裸字符串前缀匹配。
8. **worktree marker**：`top/.git` MUST 存在（`os.path.exists`，非 `isdir`——同步骤 4 的理由）。
   MUST 排在步骤 9 之前——步骤 9 依赖 `top_real` 已确认带 marker。
9. **最近根一致**：`os.path.normcase(marker_dir)`（步骤 4 独立上溯到的结果）MUST **严格等于**
   `os.path.normcase(os.path.realpath(top))`（git 返回、经步骤 7/8 校验过的结果）。步骤 7、8
   只证明「`top` 是 `start` 的祖先」且「`top` 自身是个仓库根」——**外层祖先仓库**两条都能通过
   （`core.worktree` 指向祖先仓 / PATH 上的 fake git 返回外层仓），于是数据会被写进比最近仓库
   更外层的仓库。只有本步能证明 git 返回的根就是**最近**的那个。删掉本步 = 该缺口静默回归。

校验失败 MUST NOT 产生任何目录或文件，MUST NOT 以该值为前缀拼接任何写入路径。

本要求适用于三份 recorder：`sdflow-issues/scripts/issues.py`、
`sdflow-buglist/scripts/buglist.py`、`sdflow-todolist/scripts/todolist.py`。

#### Scenario: git 返回合法仓根
- **WHEN** `git rev-parse --show-toplevel` 以 rc=0 返回一个存在的绝对路径目录，且它是 `start` 的祖先或等于 `start`，并且是起点上溯到的最近仓库
- **THEN** `repo_root(start)` 返回其 `realpath`
- **AND** 行为与本变更前一致

#### Scenario: core.worktree 在 .git/config 中重定向工作树到仓外目录（主防线用例）
- **WHEN** 仓库的 `.git/config` 含 `core.worktree = <仓外的既存目录>`，且进程环境中**没有任何**
      `GIT_*` 变量
- **THEN** `git rev-parse --show-toplevel` 以 rc=0 返回那个仓外目录，且它通过非空/`isabs`/`isdir`
      三项形状校验
- **AND** `repo_root(start)` 仍 MUST 抛 `ValueError`——由祖先校验（步骤 7）拦截
- **AND** 该仓外目录下 MUST NOT 被创建任何 `openspec/` 目录或文件

#### Scenario: core.worktree 重定向到祖先仓库（最近根一致用例）
- **WHEN** `.git/config` 的 `core.worktree` 指向 `start` 的某个**祖先目录**，且该祖先目录自身
      也是一个 git 仓库根（因此仍是 `start` 的祖先、也带 `.git` marker）
- **THEN** 祖先校验（步骤 7）与 worktree marker（步骤 8）均放行，但最近根一致（步骤 9）发现
      `marker_dir`（起点上溯到的最近 `.git`）与该祖先仓库不同
- **AND** `repo_root(start)` MUST 抛 `ValueError`
- **AND** 数据 MUST NOT 被写入该祖先仓库

#### Scenario: 起点位于仓库内但 git 拒绝作答（含 .git/ 内部与 safe.directory）
- **WHEN** 起点上溯能找到 `.git` marker（步骤 4 命中，包括起点本身就在 `.git/` 目录内部的
      情形），但 `git rev-parse --show-toplevel` 以非 0 退出（`detected dubious ownership` /
      `.git/` 目录内部的 "not a working tree" 等）或抛 `OSError`
- **THEN** `repo_root(start)` MUST 抛 `ValueError`（步骤 5 fail-closed），MUST NOT 回落
- **AND** MUST NOT 把该起点（如 `.git/hooks`）当作可写仓根返回

#### Scenario: GIT_DIR / GIT_WORK_TREE 环境变量重定向
- **WHEN** 进程环境设置 `GIT_DIR` 与 `GIT_WORK_TREE` 指向另一个仓库
- **THEN** 环境净化使 git 忽略它们并返回真实仓根，`repo_root(start)` 正常返回
- **AND** 即便环境净化被绕过（例如将来新增未被剔除的等价变量），祖先校验仍 MUST 拦截指向仓外的结果

#### Scenario: linked worktree 与 submodule
- **WHEN** `start` 位于 `git worktree add` 创建的 linked worktree 内，或位于 submodule 内
      （两种情况下 `top/.git` 均为**文件**而非目录）
- **THEN** `repo_root(start)` 正常返回该 worktree / submodule 自己的根
- **AND** MUST NOT 因 `.git` 不是目录而误判失败

#### Scenario: 起点不是既存目录
- **WHEN** 显式传入的 `--root` 指向不存在的路径或非目录
- **THEN** `repo_root(start)` 在调用 git **之前**抛 `ValueError`
- **AND** 该路径 MUST NOT 被创建

#### Scenario: 进程当前工作目录在运行期被删除
- **WHEN** 未指定 `--root`，且进程的 cwd 在调用前已被外部删除或其父目录权限被撤
      （此时 `os.path.isdir(".")` 仍返回 `True`，而 `os.getcwd()` 抛 `OSError`——
      `FileNotFoundError` 或 `PermissionError`）
- **THEN** `repo_root()` 抛受控 `ValueError`，CLI 层表现为 exit 2 + stderr 诊断
- **AND** stderr MUST NOT 含 `Traceback`

#### Scenario: git 探测超时
- **WHEN** `git rev-parse --show-toplevel` 超过设定的 timeout 未返回（如仓库位于失联的网络文件系统）
- **THEN** `repo_root(start)` 抛 `ValueError`，MUST NOT 回落——超时不等于「不在仓库里」，
      回落会把数据写到错误位置

#### Scenario: git 返回非目录字符串
- **WHEN** `git rev-parse --show-toplevel` 以 rc=0 返回一个不是既存目录的字符串
      （例如被污染的多行输出、JSON 片段、已删除的路径）
- **THEN** `repo_root(start)` 抛 `ValueError`，诊断信息含被拒值（截断）与修复指引
- **AND** 经 CLI 调用时进程以 exit code 2 结束，诊断落 stderr
- **AND** 进程结束后，以该字符串为首段的路径下**不存在**任何目录或文件

#### Scenario: 坏值恰好匹配 cwd 下的既存目录
- **WHEN** `git rev-parse --show-toplevel` 以 rc=0 返回一个相对路径，且该相对路径在当前
      工作目录下恰好对应一个真实存在的目录
- **THEN** `repo_root(start)` 仍抛 `ValueError`（`os.path.isabs` 判据拦截）
- **AND** 该行为与进程的当前工作目录无关

#### Scenario: git 返回空输出
- **WHEN** `git rev-parse --show-toplevel` 以 rc=0 返回空串或纯空白
- **THEN** `repo_root(start)` 抛 `ValueError`

#### Scenario: git 命令失败且起点确实不在任何仓库内
- **WHEN** `git rev-parse --show-toplevel` 抛 `OSError` 或以非 0 退出，且从起点向上一层都
      找不到 `.git` marker（真·非 git 仓库 / bare repo 外部 / git 不可用）
- **THEN** `repo_root(start)` 返回 `os.path.abspath(start)`
- **AND** 行为与本变更前一致，非 git 仓库下的 recorder 命令仍正常完成

#### Scenario: 抛出点在调用方的异常出口内
- **WHEN** 三份 recorder 的 `main()` 执行 `args.root = repo_root(args.root)`
- **THEN** 该调用位于捕获 `ValueError` 的 try 块内，异常被转为 stderr 诊断 + exit 2，
      而非裸 traceback

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

本要求的实现 MUST 在三份 recorder 中逐字同款落地，使
`openspec/specs/determinism-guards/spec.md` 要求的「剥 docstring 后 `ast.dump` 相等」三向
镜像断言继续成立。MUST NOT 只修改其中一份或两份。

#### Scenario: 镜像守护校验
- **WHEN** 运行 determinism-guards 的 recorder 镜像 helper 一致性测试
- **THEN** `repo_root` 的三向 AST 等价断言通过

#### Scenario: 单份漂移被拦截
- **WHEN** 仅在一份 recorder 中修改 `repo_root` 的校验逻辑
- **THEN** 镜像一致性测试失败，指出 `repo_root` 三向不等价

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
