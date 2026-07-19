# Carry-forward — 双轴审裁定「不属当票、须由后续票承接」的发现

本文件是 tickets 管线内跨票传递的载体：某票双轴审报出的发现，若按 plan 的划分不属该票 scope，
**MUST NOT 静默丢弃**（反静默压制），登记于此并在承接票的 dispatch 中原文带上。

---

## CF-1 → Task 4：过宽 `subprocess.run` mock 是**面**，不是点

**来源**：Task 1 · Standards 轴 · Important
**发现者独立实测**（非采信自报）：全仓 **12 个同姿势站点**——
`sdflow-issues/tests/test_task4_rename_snapshot.py` 5 处 + `sdflow-issues/tests/test_issues.py` 7 处。

**内容**：这些用例整体替换 `issues_mod.subprocess.run`，会连带劫持被测函数之外的一切子进程调用，
其中就包括 `repo_root` 的 `git rev-parse`。当前后果是坏 JSON 被当仓根 `makedirs`（Task 1 实测的
再生链）；**Task 2 加固落地后，后果变成「凡走 `main()` 的用例都会撞进新的 fail-closed 分支」**——
不是一个用例，是十二个。

**为什么这条必须在 Task 4 被当面处理**：plan 的 Task 4 与 tasks.md 2.1 现在的口径都是
「修 `test_task4_rename_snapshot.py:149` 这一个用例」，是**点驱动**的。按 CLAUDE.md 基准 3
（面治优先于点补），正解是按 argv 分派做**面级**改造（只拦 recorder 那一次 scan 调用，
`git rev-parse` 透传真实行为），而非逐个补。

**⚠️ 反模式警告**：若 Task 4 只修 1 处、留 11 处，Task 2 的加固会以「11 个用例莫名变红」的形态
爆发在 Task 4 之后，且极易被误诊为「加固写错了」而去弱化 `repo_root` —— 那正是本 change 要防的
「拿现状反驳目标」。

---

## CF-2 → Task 6：R4 的达成锚在 Task 5，不在 Task 1

**来源**：Task 1 · Spec 轴 · Minor

**内容**：Task 1 的 `R-ID: R4` 标注过宽。R4「测试套件不得在当前工作目录留下副作用」的
Requirement 主体是**仓根单一份 `conftest.py` 的 autouse fixture 机械保证**，其三个 Scenario
（空目录跑套件条目数 0 / 全仓覆盖 / 泄漏被断言捕获）**无一被 Task 1 推进**——Task 1 清的是 R4
被违反后的历史产物，不是 R4 本身。

**Task 6 收口时的动作**：把 R4 的达成锚落在 **Task 5**；**MUST NOT** 因为 Task 1 的两个框已勾
就把 R4 读成已闭环。

---

## CF-3 → Task 6：`test_exec_claude_reverse_path_three_flags_golden` 的触发条件比记录的窄

**来源**：Task 1 · implementer 全量 pytest 观察

**内容**：该用例此前被记为「全量跑 FAILED / 单独跑 PASSED」的 order-dependent 缺陷
（proposal Non-Goals + tasks 4.5）。Task 1 的全量跑（1753 passed / 3 skipped / **0 failed**）
中它**没有失败** ⇒ 真实触发条件比「全量跑」更窄（可能与并发、机器负载或更早的某个用例相关）。

**Task 6 登记 buglist 时的动作**：如实写「触发条件未完全定位，已知一次全量跑未复现」，
**MUST NOT** 照抄「全量跑必红」这个已被证伪的描述。

---

## CF-4 → Task 3：`--root` 默认改 `None` 会**激活**一条裸 `OSError` 逃逸路径

**来源**：Task 2 · Standards 轴 · Minor（目标态导向发现）

**内容**：`repo_root` 步骤① 的 `start is None` 分支只捕 `FileNotFoundError`：

```python
try:
    start = os.getcwd()
except FileNotFoundError:
    raise ValueError(...) from None
```

`PermissionError`（父目录权限被撤）是 `OSError` 的另一子类，会**裸着逃出 `repo_root`**；
而三份 `main()` 只 `except ValueError` ⇒ 输出 **Traceback**，直接击穿 spec 的
「stderr MUST NOT 含 Traceback」承诺。

**当前不可达 ≠ 不用管**：argparse `--root` 默认仍是 `"."`，`start is None` 分支走不到。
**Task 3 落 tasks 1.2c（默认改 `None`）的那一刻，它就变成活路径。**

**⇒ Task 3 MUST 在改 argparse 默认值的同一票内，把该 except 扩为 `OSError`**（三份同步），
并补一条负例。**MUST NOT** 以「现在触发不到」为由留到以后——那是拿现状反驳目标（通则③）。

---

## CF-5 → Task 3：tasks 1.3c 的 **CLI 层**断言待回补

**来源**：Task 2 · implementer Concern 2

**内容**：Task 2 只做到**函数层**（子进程直调 `repo_root()`）验证「cwd 被删 → 受控失败」。
CLI 层断言（`exit 2` + stderr 无 `Traceback`）走不到，因为 CLI 要进 `start=None` 分支的前提
正是 tasks 1.2c 的 argparse 默认值改 `None`——当前默认 `"."` ⇒ CLI 下 cwd 被删走的是
**显式起点分支**，测的不是目标 Scenario。

**⇒ Task 3 落 1.2c 后 MUST 回补这条 CLI 级断言**，否则该 Scenario 只有半条覆盖。
注意它与 CF-4 是**同一个分支被激活**带来的两件事，一并做。

---

## CF-6 → Task 6（tasks 4.6 Windows 泳道）：`commonpath` 跨盘符的可观测性降级

**来源**：Task 2 · implementer Concern 3

**内容**：祖先校验第⑤步用 `os.path.commonpath`（依 ADR-2 written decision 原样）。
**Windows 跨盘符**下 `commonpath` 会**自行抛 `ValueError("Paths don't have the same drive")`**。

- **行为仍正确**：`main()` 的 `except ValueError` 照样接住 → exit 2 + stderr，无 traceback ⇒ fail-closed 成立。
- **但可观测性降级**：该 `ValueError` 来自 stdlib，消息**不带** recorder 的 `ERROR: …; cause: …; fix: …` 格式。

**Windows 泳道 MUST 实测这一条**，**MUST NOT 用「理论上大概率能过」结案**（PV 规则 1）。
备选方案 `PurePath.is_relative_to`（spec 明列的另一选项，跨盘符返回 `False` 而非抛异常）
是对 ADR-2 written decision 的偏离，**若实测确认降级不可接受，须走设计门而非就地改**。

---

## CF-7 →（登记备查，本 change 不处置）`isdir` 的 TOCTOU 窗口

**来源**：Task 2 · implementer Concern 5

**内容**：步骤① `isdir(start)` 与步骤③ `subprocess.run(cwd=start)` 之间存在竞态窗口。
窗口内 start 被删 ⇒ `subprocess.run` 抛 `FileNotFoundError`（`OSError`）⇒ 落**回落分支**
返回 `abspath(start)`，而非 fail-closed。

属既有回落语义的边角，**spec 未要求处置**，Task 2 不擅自扩 scope 的判断正确。
Task 6 收尾时**记 todolist**（显式带 `change` 字段），不在本 change 内修。

---

## CF-8 →（无自动化锚，如实登记）`timeout=30` 的数值本身未被覆盖

**来源**：Task 2 · implementer Concern 4

**内容**：超时验证拆成两条——契约层（断言 `ValueError` + 不回落 + `subprocess.run` 确收正数
`timeout` kwarg）+ 真 PATH 注入 shim（`exec /bin/sleep 120`，外层 timeout 收窄到 1s 观察真实
`TimeoutExpired` 路径）。**未覆盖的残余 = 「30 这个数值本身」**，因为真等满 30s 会让每次跑
套件多 30s 墙钟。

这是**诚实的覆盖边界声明，非缺陷**。Task 6 收尾时在报告中如实呈现，
**MUST NOT** 宣称「超时面已全覆盖」。

> **踩坑记录（值得留档）**：该 shim 首版写 `sleep 120` 且把 `PATH` **整个替换**成 shim 目录
> ⇒ 连 `sleep` 本身都找不到、shell 退 127、走成**回落分支**、测试报 "DID NOT RAISE"。
> 改为 `exec /bin/sleep 120` + `PATH` **前置**（而非替换）才真的挂住。
> **若当时不查原因直接改断言，就会得到一个「测超时」但实际测的是「命令不存在」的假绿。**

---

## CF-9 → **设计门**（四件套需修订，本 change 实现期禁改）

Task 5 双轴审确认的 **spec/design 与实现的落差**——**全部是「实现对、文档措辞旧」，不是实现错**。
四件套在设计门拍板后被冻结（改动即触发 `ship_gate` 失鲜 REFUSE_START），故一律留到设计门一次性回写。

| # | 落差 | 事实 | 处置 |
|---|---|---|---|
| **a** | `spec.md:157-158` 仍写「测试产生的**一切落盘物** MUST 位于 `tmp_path`」 | design **D6 已决议**收窄为「禁止新增 cwd **顶层条目**」，决议**没落到 spec 正文** ⇒ **spec 目前宣称了实现不覆盖的东西** | 回写 spec 正文到 D6 的收窄口径 |
| **b** | `spec.md:160` + **ADR-3 标题/决策** + `tasks.md 3.1` 均写「由仓根单一份 conftest 的 **autouse fixture** 机械保证」 | 实现用的是 `pytest_runtest_{setup,call,teardown}` **hook wrapper**。理由充分且技术上更优——**autouse fixture 的 teardown 抛异常会被记成「passed + teardown error」，摘要行写 `1 passed`，泄漏降级成脚注**；照 spec 字面实现反而制造假绿 | 回写三处措辞为 hook wrapper，并记录「为什么不是 autouse fixture」 |
| **c** | **ADR-3 的覆盖机制表述失准**：写「pytest 沿祖先目录收集 conftest ⇒ 仓根一份天然覆盖」 | **漏了前置条件**：conftest 收集止于 `confcutdir`，其默认值 = `rootdir`。本仓此前无 ini ⇒ 从仓外跑 `pytest /abs/<skill>/tests/` 时 rootdir 塌缩、**仓根 conftest 根本不被收集**。双向变异实证：无 `pytest.ini` 时注入泄漏 `1 passed`（假绿），有则 `1 failed` | ADR-3 补 `confcutdir` 前置条件；**「代价」段从一个根级文件改为两个**（`conftest.py` + `pytest.ini`，**缺一即失效**） |
| **d** | `tasks.md 4.4` 要改的 CLAUDE.md 那句「没有根级 pytest 配置」 | 被新增的 `pytest.ini` **正面证伪**，且改法要扩到**两个**根级文件 | Task 6 执行 4.4 时按两文件表述 |
| **e** | ADR-3 自称基线「**12 个** skill + hack 各自跑完均 0 残留」 | 实测是 **11 个**（10 skill + hack；`sdflow-retro` 无 `tests/`）。plan 的 Task 5 验收框沿用了这个错数 | 订正为 11 |

> **共同性质**：这些不是「实现没做到」，而是**实现在执行过程中把设计的一条隐含前提证伪了**，
> 文档尚未追上。**MUST NOT** 在收尾时把它们描述成「已全部达成」。

### CF-9 补充（Task 6 双轴审新增）

| # | 落差 | 处置 |
|---|---|---|
| **f** | **回写项 (a) 有一个隐式依赖未被点出**：Task 6 新增的 Windows 用例 `_second_drive_probe` 在**盘符根**建目录（`tmp_path` 之外），与**现行** `spec.md:157-158` 字面的「一切落盘物 MUST 位于 `tmp_path`」相抵 | 回写 (a) 时 MUST 一并说明：收窄到「禁止新增 cwd 顶层条目」之后，该 probe 才不违规。**(a) 不是纯措辞订正，它有既存用例依赖** |
| **g** | `outside-voice.sh` 排除论证的**残余分类偏轻** | 报告归为纯「质量面 / evidence 相关性失效」，但坏值会把只读 agent 引到**另一棵树**取证，而出境 `secret_scan` 按 B13 在失败通道上 fail-open ⇒ 兼有**机密性邻接**面。**不改排除结论**（`repo_root` 不扩大读面，codex `-s read-only` 本就可读全盘），仅须在 Non-Goals 措辞补一句 |

### ⚠️ 全套件数字不是确定性锚（Task 6 双轴审实测）

`1870 passed / 9 skipped` 与 `1871 passed / 8 skipped` **两种结果都会出现**——
浮动源是 `test_outside_voice_child_lifecycle.py:436`（信号风暴复现率环境敏感，用例 docstring 自陈）。

**恒定量**：`failed == 0`、`xfailed == 3`。

⚠️ **`passed + skipped` 的总数会随本 change 自己新增用例而变**——登记时是 `1879`，代码审 fix 轮次
新增 24 例后为 `1903`。**它不是恒定量，MUST NOT 当锚**（把它写死 = 造一个必然假红的门）。
要锚就只锚 `failed == 0` 与 `xfailed == 3`。

⇒ **MUST NOT 把「1870/9」写成机械锚**（那会造出一个每隔几轮就假红的门）。要锚就锚上面三个恒定量。
