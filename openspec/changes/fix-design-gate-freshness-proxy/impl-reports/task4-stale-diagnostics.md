# Task 4 — 撞门者被告知撞在哪、下一步做什么（SW-1）

**范围**：`sdflow-ship/scripts/ship_gate.py` + `sdflow-ship/tests/test_gate_freshness.py`（新增 ⑨ 节）。
**不变量**：纯诊断——**零判定变化、零退出码变化**。既有 2009 例全绿，无一条断言被改动。

## 做了什么

### 1. `is_stale` 改结构化返回：`StaleResult`

`StaleResult` 是 **2-tuple 的子类**，额外挂一个 `trigger` 属性：

- 既有调用点与用例的 `stale, freshness = is_stale(...)`、`== (False, "fresh")` **逐字仍成立**——
  触发点是附加诊断物，不改判定值的形状。做成 3 字段 NamedTuple 会当场击穿这条契约，
  而本票是纯诊断票，不该从后门改既有形状。
- 另给 `.stale` / `.freshness` / `.trigger` 三个具名读法，新代码不必靠位置下标。

`code` 域的 `freshness` 取值字符串（`fresh` / `stale` / `uncommitted`）**逐字不变**，
且 code 域**不产触发点**（`trigger is None`）——本 change 只动 design 域。
下游读点已 grep 全仓核实：除 `ship_gate.py` 自身与 `test_gate_freshness.py` 外，
无第三方消费 `freshness` 值的代码（`sdflow-ship/SKILL.md` 只消费 `verdict` / `next` / `done_tasks`）。

### 2. 分类原因取自**实际分支**，不另拼一套

`design_frame_exempt` 拆成两层（单一源）：

- `design_frame_exempt_reason(...)` — 判据本体，返回**不豁免的分类原因**或 `None`（豁免）；
- `design_frame_exempt(...)` — 它的 bool 视图（既有用例照旧断言 `is True` / `is False`）。

四条取值就是判据里**已经存在**的四条保守回落分支，枚举全集落在 `STALE_CATEGORIES`：

| 取值 | 对应分支 | 人读标签 |
|---|---|---|
| `mixed-paths` | 帧内监视路径集 ≠ `{tasks.md}` | 帧内触及 tasks.md 以外的设计工件 |
| `content-changed` | 勾选框归一化后仍不等值 | tasks.md 出现勾选框以外的改动 |
| `blob-unreadable` | 形态合格但前/后版 blob 读取失败 | tasks.md 前后两版内容读取失败 |
| `shape-unfit` | 非普通内容修改（A/D/R/C/T/mode），或根提交 / parent 不可解析 | tasks.md 变更形态不合格 |

`blob-unreadable` 与 `shape-unfit` 此前被 `blob_pair` 的单一 `ok=False` 折叠掉了。
拆开只在**失败侧**多问一次形态闸门（诊断路径），常态热路径的 git 调用次数不变——
`test_non_exact_subject_does_reach_blob_read`（断言 `blob_pair` 恰被调 1 次）仍绿即为证。

### 3. 人读 / 机读双写，**同一数据源**

`is_stale` 在判失鲜处一次性构造 `trigger = {sha(短), subject, paths(排序), category}`：

- **机读**：`emit` 的 JSON 增 `stale_trigger` 对象，agent 直接取字段，免二次解析散文；
- **人读**：`_stale_trigger_hint(trigger)` 把**同一个 dict** 渲染成
  `；触发点：提交 <短sha> "<subject>" 触及 <路径>（<中文标签>）` 追加到 reason 尾部。

两侧不各拼各的——人读串是 dict 的一个渲染视图，漂移不可能单侧发生。

### 4. 默认处置只推荐重跑设计门

既有文案「（重跑 sdflow-spec-review 后重新拍板补锚）」**逐字保留**，
`checkpoint(impl-review)` **不出现**在人读 reason 与 JSON reason 中，并有机械守
（`test_default_disposition_recommends_rerun_design_gate_only` 双向断言 + 变异③转红）。

理由（已写进代码注释）：豁免**逐提交独立求值**，已经触发失鲜的那个提交不会因为
**后补**一个 `checkpoint(impl-review)` 提交而被追溯赦免——写进指引等于教撞门者做一件
不起作用的事，而它同时还是显式越权口。

## 判定等价性

`is_stale` 的 design 分支循环由

```
if subs - {"tasks.md"}: 失鲜
if subs and not design_frame_exempt(...): 失鲜
```

改写为「`subs` 为空则跳过，否则问 `design_frame_exempt_reason`」。等价：该函数首行即
`subs != {"tasks.md"} → "mixed-paths"`，与旧首条分支同集同序（且同样**不读任何 blob**）。
BR-7 精确式 subject 短路仍在读取任何 blob **之前**（⑧b 两例仍绿）；BR-6 护栏未动。

## 测试与变异验证

新增 ⑨ 节 7 例（`test_gate_freshness.py`）：四条分类各一例（三例走端到端 gate、
`blob-unreadable` 走 `is_stale` 直调 + `run_git_bytes` 替身）、默认处置文案守、
code 域取值不变 + 无触发点、二元组兼容性守。

TDD 顺序：先写 → 6 红（第 7 例 `default_disposition` 是回归守，本就绿）→ 实现转绿。

变异验证（每次改一处、跑 `test_gate_freshness.py`、随后还原）：

| 变异 | 结果 |
|---|---|
| ① 删掉触发点增强（emit 不附 `stale_trigger`、不拼人读串） | **3 红**：`..._mixed_paths` / `..._content_changed` / `..._shape_unfit` |
| ② 分类塌缩（`blob-unreadable` 并回 `shape-unfit`） | **1 红**：`..._blob_unreadable` |
| ③ 默认处置指引混入 `checkpoint(impl-review)` | **1 红**：`test_default_disposition_recommends_rerun_design_gate_only` |

三处变异三处不同的红，无一互相遮蔽。

**全量**：`sdflow-ship/tests/` 263 passed；仓根全套件 **2009 passed, 9 skipped, 3 xfailed**（124s）。
既有用例零转红、零断言改动。

## 遗留 / 待人裁

**本 change 的 spec delta 与本票要求存在一处正面冲突，我按票实现，未改 spec**
（实现期改 `specs/` 会触设计门失鲜）：

`specs/spec-workflow/spec.md` 的 `Scenario: 失鲜 REFUSE_START 须携带触发点与处置指引`
写的是「MUST 给出可操作的分支处置提示（真实设计变更 ⇒ 重跑设计门；阶段三合法尾流修订
⇒ 走 `checkpoint(impl-review)` subject 声明通道）」——即 **MUST 提** checkpoint 通道；
而本票的硬要求是该字符串 **MUST NOT** 出现在默认处置指引里。

按票实现，依据是票里给出的正确性论证（后补 checkpoint 提交对已触发失鲜的提交无追溯效力，
写进指引 = 教人白做）。**建议在 archive 前把该 Scenario 的括号内容改成「默认只推荐重跑
设计门；`checkpoint(impl-review)` 是显式越权口，且须在产生失鲜的那个提交上使用，
不能事后追补」**——由 `/sdflow-done` 的 delta 对码核验步或人工拍板处理。
