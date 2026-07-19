## ADDED Requirements

### Requirement: recorder 仓根解析对外部进程输出 fail-closed

recorder 的 `repo_root(start)` MUST 在把任何值当作可写仓根返回之前，证明它是**起点所属仓库的根**；
MUST NOT 把 `git rev-parse --show-toplevel` 的 stdout 直接当仓根返回，MUST NOT 仅凭路径形状
（非空 / 绝对 / 是目录）放行。

**校验序列**（按序，任一不满足即 fail-closed）：

1. **起点可信性**：MUST 在调用 git **之前**完成。
   - `start` 未指定（`--root` 默认 `None`）：起点 MUST 由 `os.getcwd()` 求得；其
     `FileNotFoundError`（进程 cwd 已被删除）MUST 转为受控 `ValueError`。
     **MUST NOT 用 `os.path.isdir(".")` 代替**——cwd 被删除后它仍返回 `True`，校验形同虚设，
     而随后的 `os.path.abspath(".")` 会在回落分支内部抛 `FileNotFoundError` 并裸传播成 traceback。
   - `start` 显式传入：MUST 通过 `os.path.isdir(start)`，否则抛 `ValueError`。
2. **环境净化**：调用 git 前 MUST 从子进程环境剔除仓库/工作树发现类变量：`GIT_DIR`、
   `GIT_WORK_TREE`、`GIT_COMMON_DIR`、`GIT_CEILING_DIRECTORIES`、`GIT_INDEX_FILE`、
   `GIT_DISCOVERY_ACROSS_FILESYSTEM`、`GIT_CONFIG_COUNT`、`GIT_CONFIG_GLOBAL`、
   `GIT_CONFIG_SYSTEM`，以及前缀 `GIT_CONFIG_KEY_*` / `GIT_CONFIG_VALUE_*`。
   MUST NOT 改为「剔除所有 `GIT_*` + 白名单」——`GIT_EXEC_PATH` 等执行类变量必须保留。
3. **形状校验**：stdout 以 `rstrip("\r\n")` 只剥行结束符（MUST NOT 用 `strip()`——会删掉路径
   末尾的合法空格），结果 MUST 非空、`os.path.isabs`、`os.path.isdir`。
4. **祖先校验（主防线）**：`os.path.normcase(os.path.realpath(start))` MUST 位于
   `os.path.normcase(os.path.realpath(top))` 之内（相等或在其下）。比较 MUST 按**路径组件**
   进行（`os.path.commonpath` 或 `Path.is_relative_to`），MUST NOT 用裸字符串前缀匹配。
5. **worktree marker**：`top/.git` MUST 存在。判定 MUST 用 `os.path.exists` 而非
   `os.path.isdir`——linked worktree 与 submodule 下 `.git` 是**文件**。

**祖先校验（第 4 步）是主防线，环境净化（第 2 步）是纵深防御**：`core.worktree` 是写在
`.git/config` 里的 **on-disk** 重定向，剔除环境变量对它零效果，而形状校验（第 3 步）会放行——
删除第 4 步会让该缺口静默回归。

**回落 vs fail-closed 的分界**：git 抛 `OSError` 或以非 0 退出（非 git 仓库、git 不可用、
bare repo、`.git/` 目录内）是**正常场景**，MUST 返回 `os.path.abspath(start)`；其余一切
（超时、rc=0 但校验不过）MUST 抛 `ValueError`，由三份 `main()` 既有的 `except ValueError`
出口转为 stderr 诊断 + exit code 2，MUST NOT 退化回落。

校验失败 MUST NOT 产生任何目录或文件，MUST NOT 以该值为前缀拼接任何写入路径。

本要求适用于三份 recorder：`sdflow-issues/scripts/issues.py`、
`sdflow-buglist/scripts/buglist.py`、`sdflow-todolist/scripts/todolist.py`。

#### Scenario: git 返回合法仓根
- **WHEN** `git rev-parse --show-toplevel` 以 rc=0 返回一个存在的绝对路径目录，且它是 `start` 的祖先或等于 `start`
- **THEN** `repo_root(start)` 返回其 `realpath`
- **AND** 行为与本变更前一致

#### Scenario: core.worktree 在 .git/config 中重定向工作树（主防线用例）
- **WHEN** 仓库的 `.git/config` 含 `core.worktree = <仓外的既存目录>`，且进程环境中**没有任何**
      `GIT_*` 变量
- **THEN** `git rev-parse --show-toplevel` 以 rc=0 返回那个仓外目录，且它通过非空/`isabs`/`isdir`
      三项形状校验
- **AND** `repo_root(start)` 仍 MUST 抛 `ValueError`——由祖先校验拦截
- **AND** 该仓外目录下 MUST NOT 被创建任何 `openspec/` 目录或文件

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
- **WHEN** 未指定 `--root`，且进程的 cwd 在调用前已被外部删除
      （此时 `os.path.isdir(".")` 仍返回 `True`，而 `os.getcwd()` 抛 `FileNotFoundError`）
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

#### Scenario: git 命令失败
- **WHEN** `git rev-parse --show-toplevel` 抛异常或以非 0 退出（非 git 仓库、git 不可用等）
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
该跨进程二次解析的风险由 `validate_recorder_participant` 的 path/token 绑定兜底
（子进程若解析出不同的根，其 `_lock_path` 处无锁文件 ⇒ `RecorderLockError` 响亮失败），
**此依赖 MUST 有测试锚定**，不得因「看起来与 token 校验重复」而被简化掉。

**理由不是省一次子进程**：`repo_root()` 的校验是**逐次独立**的，不保证两次解析得到同一个仓。
`git rev-parse --show-toplevel` 会沿目录树向上搜索，若两次解析之间目标目录失去自己的 `.git`
（`git worktree prune` / 误删 / fixture 清理），第二次会静默爬升到**外层祖先仓库**——两次都
rc=0、都通过全部校验，但锁建在一个根上、数据写进另一个根。

#### Scenario: cmd_* 不再自行解析
- **WHEN** 任一 `cmd_*` 函数需要仓根
- **THEN** 它直接读取 `args.root`（已由 `main()` 解析并校验）
- **AND** 三份 recorder 的 `cmd_*` 函数体内 MUST NOT 出现 `repo_root(` 调用

#### Scenario: 锁与写入锚定同一个根
- **WHEN** 一次 `reindex` / `batch` 类命令在**同一进程内**持锁期间执行写入
- **THEN** `recorder_lock` 记录的 `repo` 与实际写入路径 MUST 源自同一次解析结果

#### Scenario: 子进程解析出不同的根时响亮失败
- **WHEN** 父进程持锁并以 `--root` 拉起子进程，而子进程重解析得到**不同**的根
      （两次解析之间目标失去 `.git`）
- **THEN** 子进程 MUST 以 `RecorderLockError` 失败，MUST NOT 静默写入其自行解析出的根

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

本仓任一 pytest 用例 MUST NOT 在当前工作目录留下新增条目（文件或目录）；测试产生的一切落盘物
MUST 位于 `tmp_path` 等 pytest 托管的临时路径下。

该约束 MUST 由**仓根单一份 `conftest.py`** 的 autouse fixture 机械保证，覆盖仓内全部测试套件。
MUST NOT 在各 skill 的 `tests/` 下复制多份同款 conftest——重复副本不在
`determinism-guards` 的 AST 镜像 roster 内，无守护即会漂移。

#### Scenario: 干净目录跑任一套件
- **WHEN** 在一个空目录中运行 `pytest <任一 skill>/tests/`
- **THEN** 套件结束后该目录的条目数仍为 0（`.pytest_cache` 等 pytest 自身产物除外）

#### Scenario: 覆盖面为全仓而非仅 recorder
- **WHEN** 运行仓内任意 skill 的测试套件
- **THEN** cwd 副作用断言均生效，无需该 skill 自行注册或复制 conftest

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
