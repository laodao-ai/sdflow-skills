## MODIFIED Requirements

### Requirement: 共享逻辑一致性由「单一源 + 无 pool 分支 + POOL_SPEC 完备」守护

> `[grill-amendment]`（`dedupe-issues-scripts-shared-layer`）：原 requirement「recorder 镜像 helper 由『剥 docstring 后 AST 等价』一致性测试守护」以「三 skill 各自内联、独立分发」为前提（D4：`MUST NOT 抽公共运行时模块`）。三 skill 合一为 `sdflow-issues`、撤销独立分发前提后（`adr/0027`），**镜像 AST 守失去对象**——共享逻辑物理上只剩一份 `core.py`，没有多份需要保持等价。守法据此重写。

三条 CLI（`buglist.py`/`todolist.py`/`issues.py` 薄入口）共享的执行逻辑收敛为**唯一物理源** `sdflow-issues/scripts/core.py` 后，一致性 MUST 由以下机械守卫维持（`test_mirror_consistency.py` 的三向/两向 AST roster 测试 SHALL 删除——单一物理源使其无对象）：

- `core.py` 源码 MUST NOT 含 `if pool == "bug"/"todo"` 式的 pool 条件分支（源码扫描断言）；差异一律来自注入的 `POOL_SPEC`。
- `POOL_SPEC` MUST 对每个 pool（bug/todo）的每个差异维（文件粒度 / 目录 / 特定字段 / 状态词表 / 终态集）提供取值，**缺项即红**。
- `issues.py` 的 `validate_scan_envelope`（scan JSON consumer 校验）继续以坏 JSON / 缺键 / 错型 / 缺 `file` 的 contract tests 守护，producer 缺 `bugs|items`/`problems` 时 MUST **fail-closed**，MUST NOT 以 `.get(..., [])`/falsey fallback 继续。
- `issues.py` direct rename snapshot 与 recorder `scan --json` 的 golden 语义等价（同一 canonical/pure-legacy/overlay fixture）继续守护——合一后二者为**同一实现内的两条 code path**，行为等价随「603 零回归」保持；任一方漏掉 lexical/marker/overlay/ID rule 时测试失败。

`PRIORITIES` 等非函数常量继续走独立值相等断言（bug/todo 两 pool 的取值），不塞进函数 source harness。

#### Scenario: core 含 pool 条件分支

- **WHEN** `core.py` 源码出现 `if pool == "bug"/"todo"` 式的 pool 名条件分支
- **THEN** 一致性测试失败并指明分支位置（差异 MUST 走 `POOL_SPEC`，非 core 内分叉）

#### Scenario: POOL_SPEC 取值缺项

- **WHEN** 校验 `POOL_SPEC`，某 pool 的某差异维（粒度/目录/字段/词表/终态集）无取值
- **THEN** 测试失败并指明缺失的 pool 与维度

#### Scenario: scan JSON consumer validator 不默认空池

- **WHEN** producer JSON 缺 `bugs|items`/`problems`、类型错误或 item 缺 `file`
- **THEN** `validate_scan_envelope` 要求 issues fail-closed，MUST NOT 以 `.get(..., [])`/falsey fallback 继续

#### Scenario: direct snapshot 与 scan 语义漂移

- **WHEN** 同一 canonical/pure-legacy/overlay fixture 分别经 issues direct snapshot 与 `scan --json` contract 解析
- **THEN** effective items/problems 按 semantic key 完全等价，issues 结果另带 raw bytes/spans；任一方漏掉 lexical/marker/overlay/ID rule 时测试失败

### Requirement: 确定性守卫不越权、不判内容

> `[grill-amendment]`（`dedupe-issues-scripts-shared-layer`）：原 requirement 含「一致性测试 MUST NOT 引入跨 recorder import」——该条为保「三 skill 独立分发」而设。合一后共享逻辑经**同一 skill 内同目录 `import core`** 获得（`adr/0027` 的目标架构，非违规）；跨目录 import / sys.path 注入仍禁（合一后根本不需要）。「守卫不判内容」与「batch lint 只读不覆写」不变。

本 capability 的所有守卫 MUST 只判机械可判的一致性/语法，MUST NOT 判内容合理性（`core` 逻辑该不该改、优先级填什么值、计划写什么）——那是人的判断。共享逻辑经**同一 skill 内同目录 `import core`** 获得；MUST NOT 引入跨 skill 目录 import 或 sys.path 注入。`batch lint` MUST NOT 覆写人写行（D4 只读校验）。

#### Scenario: 脚本不做内容判断

- **WHEN** `core` 内容被有意修改、或优先级填了合法但语义存疑的值
- **THEN** 守卫通过（不越权评判内容对错），内容判断留给人/模型

#### Scenario: 共享逻辑经同目录 import、不跨目录

- **WHEN** 检查三个薄入口获取共享逻辑的方式
- **THEN** 经同一 `sdflow-issues/scripts/` 目录内 `import core` 获得；不存在跨 skill 目录 import 或 sys.path 注入
