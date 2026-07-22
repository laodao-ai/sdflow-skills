## MODIFIED Requirements

### Requirement: recorder 镜像 helper 由「剥 docstring 后 AST 等价」一致性测试守护

> `[grill-amendment]`（`dedupe-issues-scripts-shared-layer`）：原 requirement「recorder 镜像 helper 由『剥 docstring 后 AST 等价』一致性测试守护」以「三 skill 各自内联、独立分发」为前提（D4：`MUST NOT 抽公共运行时模块`）。三 skill 合一为 `sdflow-issues`、撤销独立分发前提后（`adr/0027`），**镜像 AST 守失去对象**——共享逻辑物理上只剩一份（唯一命名 package `sdflow_issues_core`），没有多份需要保持等价。守法据此重写。

三条 CLI（`buglist.py`/`todolist.py`/`issues.py` 薄入口）共享的执行逻辑收敛为**唯一命名 package** `sdflow-issues/scripts/sdflow_issues_core/` 后，一致性 MUST 由以下机械守卫维持（`test_mirror_consistency.py` 的三向/两向 AST roster 测试 SHALL 删除——单一物理源使其无对象）：

- **无 pool 分支守（AST 级·best-effort 代理，非充要保证）**：`core` 源码 MUST NOT 含针对 pool 值的条件分支。守卫 **MUST NOT** 用字面 `if pool == "bug"` 子串扫描（真实分岔含 `document["pool"]=="bug"` subscript、`expected_pool==` 别名、`"bugs" if pool==` 三元、`match`、dict-dispatch 五形态，字面扫必漏）；MUST 为 **AST 级**——拦 `If`/`IfExp`/`Match`/`Compare` 右操作数 ∈ `{"bug","todo"}` 且左操作数解析到 pool 值（含别名），配 mutation test 证守卫对 `expected_pool=="bug"`/`document["pool"]=="bug"` 反红。spec MUST 诚实声明此扫描为 **best-effort 代理、非 fail-closed 充要保证**（真正不变量由下条 POOL_SPEC 封闭 schema 正面保证）。
- **POOL_SPEC 封闭 schema 完备 + 关系正确性守**：`POOL_SPEC` MUST 为封闭 schema，required 维缺项即红（含文件粒度/目录/legacy glob/特定字段/状态词表/终态集/`DEFAULT_PREFIX`/scan 输出键）；且 `terminal_set ⊆ 状态词表`、值与 `RECORDER_POOL_CONFIG` 一致（非只 non-None）；`POOL_SPEC.keys()` fail-closed `== {"bug","todo"}` 或 consumer roster 从同一 registry 派生。
- **薄入口 thinness 同一性守**：THREE_WAY/TWO_WAY 名单每个 helper 从薄入口 `getattr` 解析对象 `__module__ == 'sdflow_issues_core'`（未被 shadow）。
- `issues.py` 的 `validate_scan_envelope`（scan JSON consumer 校验）继续以坏 JSON / 缺键 / 错型 / 缺 `file` 的 contract tests 守护，producer 缺 `bugs|items`/`problems` 时 MUST **fail-closed**。
- **direct↔scan golden 降级为接线守（非 rule-omission 守）**：合一后 `issues.py` direct snapshot 与 `scan --json` 是**同源两 code-path**（跑同一 `core` parser）⇒「一方漏 rule」结构上不可能、golden 自比自己 = tautology。∴ golden 降级为守「同源两 code-path 的接线正确性（envelope 组装/字段投影）」，**MUST NOT** 再宣称「任一方漏 lexical/marker/overlay/ID rule → 失败」（该能力已由「core 是 rule 单一源」结构事实取代）；若需真 rule-完整性守，须 core-parse vs **外部 golden fixture**。

`PRIORITIES` 等非函数常量继续走独立值相等断言（bug/todo 两 pool 的取值），不塞进函数 source harness。

#### Scenario: core 含 pool 条件分支（任意形态）

- **WHEN** `core` 源码出现针对 pool 值（`"bug"`/`"todo"`）的条件分支（`if`/`IfExp`/`match`/subscript/别名/dict-dispatch 任一形态）
- **THEN** AST 级一致性测试失败并指明分支位置（差异 MUST 走 `POOL_SPEC`，非 core 内分叉）

#### Scenario: POOL_SPEC 缺维 / 值错 / 额外 pool

- **WHEN** 校验 `POOL_SPEC`：某 required 维无取值、或 `terminal_set ⊄ 状态词表`、或 `keys() ≠ {"bug","todo"}`
- **THEN** 测试失败并指明具体缺维/错值/越界 pool

#### Scenario: 薄入口 shadow core helper

- **WHEN** 某薄入口本地重定义了 THREE_WAY/TWO_WAY 名单里的共享 helper（shadow `sdflow_issues_core` 版本）
- **THEN** 同一性守失败（该 helper 从薄入口解析的 `__module__ ≠ 'sdflow_issues_core'`）

#### Scenario: direct↔scan golden 不再宣称抓 rule 遗漏

- **WHEN** 合一后审 golden 测试的守护语义
- **THEN** 它守「同源两 code-path 接线正确」，MUST NOT 宣称「任一方漏 rule → 失败」（同源自比、tautology）

#### Scenario: scan JSON consumer validator 不默认空池

- **WHEN** producer JSON 缺 `bugs|items`/`problems`、类型错误或 item 缺 `file`
- **THEN** `validate_scan_envelope` 要求 issues fail-closed，MUST NOT 以 `.get(..., [])`/falsey fallback 继续

#### Scenario: direct snapshot 与 scan 语义漂移

- **WHEN** 同一 canonical/pure-legacy/overlay fixture 分别经 issues direct snapshot 与 `scan --json` contract 解析
- **THEN** effective items/problems 按 semantic key 完全等价，issues 结果另带 raw bytes/spans（**同源两 code-path 的接线/投影正确性守**）
- **注（AD-4/R6 诚实降级）**：direct 与 scan 现同源自 core parser，故本守 **MUST NOT 宣称**「任一方漏某 lexical/marker/overlay/ID rule → 失败」——同源自比 = tautology、结构上不可能一方漏而另一方不漏；真 rule-完整性须 core-parse vs **外部** golden fixture（非 core 自比 core），本 change 未含该外部锚。与本 capability 上文「direct↔scan golden 不再宣称抓 rule 遗漏」Scenario 一致

### Requirement: 确定性守卫不越权、不破 D4 隔离

> `[grill-amendment]`（`dedupe-issues-scripts-shared-layer`）：原 requirement 含「一致性测试 MUST NOT 引入跨 recorder import」——该条为保「三 skill 独立分发」而设。合一后共享逻辑经**同一 skill 内同目录 `from sdflow_issues_core import`** 获得（`adr/0027` 的目标架构，非违规）；跨目录 import / sys.path 注入仍禁（合一后根本不需要）。「守卫不判内容」与「batch lint 只读不覆写」不变。

本 capability 的所有守卫 MUST 只判机械可判的一致性/语法，MUST NOT 判内容合理性（`core` 逻辑该不该改、优先级填什么值、计划写什么）——那是人的判断。共享逻辑经**同一 skill 内同目录 `from sdflow_issues_core import`** 获得；MUST NOT 引入跨 skill 目录 import 或 sys.path 注入。`batch lint` MUST NOT 覆写人写行（D4 只读校验）。

#### Scenario: 脚本不做内容判断

- **WHEN** `core` 内容被有意修改、或优先级填了合法但语义存疑的值
- **THEN** 守卫通过（不越权评判内容对错），内容判断留给人/模型

#### Scenario: 共享逻辑经同目录 import、不跨目录

- **WHEN** 检查三个薄入口获取共享逻辑的方式
- **THEN** 经同一 `sdflow-issues/scripts/` 目录内 `from sdflow_issues_core import` 获得（唯一命名 package）；不存在跨 skill 目录 import 或 sys.path 注入（除薄入口自身 dir 的 `sys.path.insert`）
