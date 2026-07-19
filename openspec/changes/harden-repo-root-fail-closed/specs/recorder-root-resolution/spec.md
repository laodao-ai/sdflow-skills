## ADDED Requirements

### Requirement: recorder 仓根解析对外部进程输出 fail-closed

recorder 的 `repo_root(start)` MUST 按「git 是否履行契约」分流处理，MUST NOT 把
`git rev-parse --show-toplevel` 的 stdout 直接当仓根返回：

- **git 抛异常或以非 0 退出**（非 git 仓库、git 不可用）——正常场景，MUST 返回
  `os.path.abspath(start)`。
- **git 以 rc=0 退出且 stdout 非空、`os.path.isabs` 与 `os.path.isdir` 均为真**——
  MUST 返回该路径。
- **git 以 rc=0 退出但 stdout 为空或非绝对路径或非既存目录**——git 违反自身契约，
  MUST 抛 `ValueError`（由三份 `main()` 既有的 `except ValueError` 出口转为 stderr 诊断
  + exit code 2），MUST NOT 退化回落。

绝对路径校验 MUST 与目录校验**同时**成立：`os.path.isdir` 对相对路径按当前工作目录解析，
单用它会让「恰好在 cwd 下存在同名目录」的坏值通过校验。

校验失败 MUST NOT 产生任何目录或文件，MUST NOT 以该值为前缀拼接任何写入路径。

本要求适用于三份 recorder：`sdflow-issues/scripts/issues.py`、
`sdflow-buglist/scripts/buglist.py`、`sdflow-todolist/scripts/todolist.py`。

#### Scenario: git 返回合法仓根
- **WHEN** `git rev-parse --show-toplevel` 以 rc=0 返回一个存在的绝对路径目录
- **THEN** `repo_root(start)` 返回该路径（strip 尾部换行后）
- **AND** 行为与本变更前一致

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
