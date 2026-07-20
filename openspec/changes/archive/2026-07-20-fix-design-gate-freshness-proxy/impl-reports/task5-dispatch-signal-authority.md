# Task 5: implementer dispatch 携带信号权威归属声明

**R-ID:** IO-1 · **状态:** DONE

## 做了什么

### 1. `sdflow-implement/SKILL.md` — dispatch 契约新增信号权威表（必填槽）

在「每 ticket 派 fresh implementer」的 `dispatch prompt 必含：` 列表内新增一条 **🔴 信号权威表**
必填槽，**正面陈述**三个范畴的权威归属（表格形式：范畴 / 权威在哪 / 谁写），非禁令清单：

| 范畴 | 权威在哪 | 谁写 |
|---|---|---|
| 本票完成信号 | ① plan 内该 `### Task N:` 段验收复选框；② `checkpoint(<change>:task<N>-<slug>)` 标签 | 双轴审通过后由执行模式补打 |
| 本票工作产物 | 实现代码 / 测试 / `impl-reports/task<N>-<slug>.md` | implementer 自己写 |
| 设计意图 | `proposal.md` · `design.md` · `specs/` · `tasks.md` | 设计阶段已定稿，实现期非其作者；有问题走 `NEEDS_CONTEXT`/`BLOCKED` 上抛 |

表后附一段与 gate 消费面对齐的注记，并显式禁止声明 gate 并不读取的信号源。

### 2. fix 子代理 dispatch 同样必带

在「每 ticket 双轴审」节的三条通则传播块下追加一句：fix 轮次子代理同为 fresh context，dispatch
prompt MUST 原文携带该权威表（fix 同样 MUST NOT 自行勾框 / 打完成标签 / 改四件套）。

### 3. 缺席不得静默降级

新增「**权威表缺席不得静默降级**」段：缺席 MUST 显式停并报告，MUST NOT 以「gate 已兜住失鲜后果」
为由默默放行；本约束与 gate 侧失鲜判据**各自独立成立**（对应 ticket 的定位声明与 spec Scenario②）。

### 4. 机械守 `sdflow-implement/tests/test_dispatch_signal_authority.py`（新增，4 个用例）

按 `sdflow-ship/tests/test_skill_text.py` 的既有惯例写（读 SKILL.md 文本、只钉关键词在场，不重复
逻辑测试）。用例：权威表在 dispatch 必含槽内 / 表内容与 gate 判据一致 / fix dispatch 覆盖 /
缺席不静默降级。

> **文件名注意**：初版命名 `test_skill_text.py` 会与 `sdflow-ship/tests/test_skill_text.py`
> basename 冲突（tests 目录无 `__init__.py`，仓根 rootdir 全局收集时 pytest 报 import 冲突并中断
> 整个收集）。已改为唯一 basename `test_dispatch_signal_authority.py`。

## 权威表内容的依据（实读，非凭印象）

读 `sdflow-ship/scripts/ship_gate.py` 确认完成集为两通道并集：

- **checkpoint 标签通道**：`TAG_RE = re.compile(r"checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-")`
  （L831），行首字面前缀 `checkpoint(` 过滤 + `match` 位置锚定（L905）；窗口 = `{plan_first_sha}..HEAD`
  **加 sha 自身 subject**（L889-896），即 `[plan 首次提交 sha, HEAD]` 闭区间；命名空间须精确等于
  change（裸 `checkpoint(task<N>-` 旧格式向后兼容）。
- **复选框通道**：`_parse_plan`（L924）fence-aware 单遍扫描，按 `### Task <n>:` 分段绑定；
  `checkbox_done_ids` 取「段内有框且全勾」的号集（L951）。直读工作树。
- **设计域失鲜监视集**：文件头 D9 注释（L56-59）= 本 change 四件套路径 `proposal` / `design` /
  `tasks.md` / `specs/`。

权威表的两行归属与上述逐项对应，未声明任何 gate 不读取的信号源。

## 变异验证（实跑）

**变异 1** — 删除 dispatch 必含槽内的整个信号权威表块（1039 字符）：

```
FAILED test_dispatch_carries_signal_authority_table
FAILED test_authority_table_matches_gate_consumed_criteria
E   AssertionError: 设计工件 proposal.md 未在权威表中声明归属
2 failed, 2 passed
```

**变异 2** — 删除 fix dispatch 段与「缺席不得静默降级」段：

```
FAILED test_fix_dispatch_also_carries_authority_table
FAILED test_authority_table_absence_not_silently_degraded
2 failed, 2 passed
```

两次变异后均已还原，还原后 `4 passed`。

## 测试

- `pytest sdflow-implement/tests/` → **65 passed**
- `pytest`（仓根全套件）→ **2013 passed, 9 skipped, 3 xfailed**，无既有用例转红
- `python3 hack/sync_principles.py --check` → **✅ 20 个投放面全部与真相源一致**
  （改动全在 `sdflow:principles` 托管区块之外）

## 未做 / 边界

- 未触碰 `ship_gate.py`（本票不改 gate；机械失鲜防线在 Task 2）。
- 未触碰第三方实现 skill（superpowers `subagent-driven-development` / matt `implement`）——
  spec 明确本要求适用面限于本仓自有的 `sdflow-implement`。
- 权威表在场是**文本级**机械守；「dispatch 运行时是否真的把它复制进了 prompt」无确定性捕获路径
  （同三条通则传播纪律，属既有的诚实语义边界）。
