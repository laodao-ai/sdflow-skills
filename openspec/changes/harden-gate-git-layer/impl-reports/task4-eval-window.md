# Task 4 · design 域失鲜只在实现窗口内求值，三个入口分别接入

**R-ID:** R1 · **Blocked-by:** 3 · **范围:** tasks 2.5 / 2.6 / 2.7 + 测试 5.3a–d
**不做:** code 域顶层条目比较（Task 5）、评审 SKILL 时序与文档收尾（Task 6）

## 消掉的中间态

Task 3 落地后 design 域仍**全阶段求值**，且 BR-7 subject 豁免已随帧遍历退役
⇒ **代码审期修订四件套会被判失鲜**（其 impl-report 已登记）。本票即来消掉它。

## 做了什么

### 2.5 控制流重排（`ship_gate.py`）

design 域失鲜原在 `decide()` 的 pre-flight 段**无条件求值**（旧 `:1263`，在 step 5.5 之前）。
现改为两个新函数构成的**单一实现点**：

- `guard_design_freshness(root, change, report)` —— 求值 + stale 时 `REFUSE_START`；fresh 直接返回。
- `emit_windowed(root, change, report, verdict, ...)` —— 先过闸门、再 emit 本分支判定。

旧位置**有意留空**并留注释：任何把检查加回该位置的改动都等于取消窗口限定（G4 变异即此形态）。

**为什么不能走「step 7 之后加一次检查」的捷径**（Compliance 明写、design ADR-3 明写）：
`RUN_SOP`(step 5.5) 与 `RUN_PLAN`(step 6) 在到达 step 7 之前就 `emit()`，而 `emit()` 内部是
`sys.exit()` —— 硬 early-return ⇒ 两条路径**完全逃出检查**，方向 fail-open。

### 2.6 三个入口各自接入

| 入口 | 调用点 | 用例 |
|---|---|---|
| `RUN_SOP` | step 5.5，TG-02 命中且 sop 产物缺 | 5.3a |
| `RUN_PLAN` | step 6，`superpowers-plan.md` 缺 | 5.3b |
| `CONTINUE_IMPL` | step 7，`plan_ids ⊄ done` | 5.3c |

窗口右边界 = **代码审报告出现**（非「最后一个任务打勾」）—— 以 design.md 为准，未自行推导。

### 2.7 失鲜诊断带出锚值 + 可执行差异命令〔ADR-4〕

- `emit` 的 `extra` 增 `reviewed_sha=<sha>`（撞门者不必先翻报告 frontmatter 抄）。
- reason 尾部拼 `核对差异：git diff <sha> HEAD -- <design_pathspecs 全集>`，可直接复制执行。
- 路径来源是 `design_pathspecs()` 这一**既有单一源**，与判定本体同源（不另立清单，防漂移）。
- **不与「MUST NOT 为凑诊断保留枚举通路」冲突**：`reviewed_sha` 是**录下来的常量**，
  读出来打印零推断成本；被禁的是从 git 管道**反推**触发点（`_stale_trigger_hint`，Task 3 已退役）。

## 测试（新增 5 个，全经 `run_gate` 子进程 = `main()`/`decide()` 公共入口）

落 `sdflow-ship/tests/test_gate_freshness.py`：

| 编号 | 用例 | 断言 |
|---|---|---|
| 5.3a | `test_window_run_sop_evaluates_design_freshness` | 前提校准走 RUN_SOP → 改 design.md → `REFUSE_START`(3) |
| 5.3b | `test_window_run_plan_evaluates_design_freshness` | 同上，RUN_PLAN 分支 |
| 5.3c | `test_window_continue_impl_evaluates_design_freshness` | 同上，CONTINUE_IMPL 分支 |
| 5.3d | `test_window_closed_during_code_review` | 窗口外（plan 全勾、无 cr 报告）改四件套 ⇒ 仍 `RUN_CODE_REVIEW` |
| 5.3d | `test_window_closed_during_wrapup` | 收尾期（cr+verify 均有结论）改四件套 ⇒ 仍 `RUN_VERIFY`，且不触 `RERUN_STALE` |

5.3a–c 共用 `_assert_windowed_refusal`，除 verdict/exit code 外另断言
`js["reviewed_sha"] == 锚` 与 `git diff <锚> HEAD -- ` 出现在 reason、且**监视集每个成员都在命令里**。

**三组独立性是构造出来的、不是假设的**：三个用例各自只穿过一个入口分支——
5.3a（tg02 命中 + 无 sop）够不着 RUN_PLAN/CONTINUE_IMPL；5.3b（tg02 不命中 + 无 plan）跳过 SOP 分支；
5.3c（有 plan + 有未完成任务）跳过前两者。变异结果（下表 G1–G3）实测确认。

## 变异证明（按守卫计数）

harness 落 scratchpad（一次性），每个变异体**先过 `ast.parse` 确认能运行**再跑测试
—— 防上一票踩过的「多行布尔里删一行产生 SyntaxError、变红只是语法错误、零判别力」。
全部变异用**语义替换**（换调用/加调用/删参数），无一处依赖删行。

| # | 守卫 | 变异手段 | 变红用例 | 判别力 |
|---|---|---|---|---|
| G1 | `RUN_SOP` 入口接入 | `emit_windowed(...)` → `emit(...)` | **仅** `..._run_sop_...` | ✅ 单点 |
| G2 | `RUN_PLAN` 入口接入 | 同上 | **仅** `..._run_plan_...` | ✅ 单点 |
| G3 | `CONTINUE_IMPL` 入口接入 | 同上 | **仅** `..._continue_impl_...` | ✅ 单点 |
| G4 | 窗口限定本身 | 在旧位置加回无条件 `guard_design_freshness(...)` | `..._closed_during_code_review` + `..._closed_during_wrapup` | ✅ 恰两条 |
| G5 | 锚值可见〔ADR-4〕 | 从 `emit` 删 `reviewed_sha=sha` | 5.3a/b/c 三条 | ✅ |
| G6 | 差异命令〔2.7〕 | reason 的 `核对差异：git diff …` 换空串 | 5.3a/b/c 三条 | ✅ |
| G0 | 对照（不变异） | — | 无 | ✅ 基线绿 |

G1–G3 各自只红一条 = **「三分支各自接入、各自无旁路」被证成**，而非「三个一起红或一个都不红」
（后者说明期望集取错范畴，Task 2 踩过）。
G4 只红窗口外两条、不动 G1–G3 的三条 = 窗口的**两个方向都有守卫**（内不漏、外不误拦）。

**MUST NOT 以「用例存在且为绿」充当证明** —— 以上七行全部实际跑过，输出见执行记录。

## 回归

- `sdflow-ship/tests/` = **317 → 322 passed**（新增 5 条，零既有用例失败、零删除）。
- 仓根全套件 = `2074 passed, 9 skipped, 3 xfailed`。基线为 `2070 passed, 8 skipped, 3 xfailed`
  ⇒ passed+skipped 由 2078 增至 2083，**恰好 +5 = 本票新增用例数**；passed/skipped 的
  1 例位移是 `sdflow-init` 那条 ramdisk 满盘用例的环境敏感浮动（基线说明已注明 8/9 间浮动），与本票无关。

## Compliance 自查（本票相关条目）

- ✅ design 域失鲜**只在实现窗口内**求值，且**分别覆盖** `RUN_SOP`/`RUN_PLAN`/`CONTINUE_IMPL` 三分支；
  **未**走「只在 step 7 后加一次检查」的捷径（G4 反向证明该形态会被测出）。
- ✅ **未**引入语义分诊层或任何重锚逃生口 —— 窗口内不设旁路，撞门正解是重审。
- ✅ `emit` 输出 `reviewed_sha`；**未**为凑诊断保留任何路径枚举通路。
- ✅ 新增用例全经公共入口（`run_gate` 子进程 → `main()` → `decide()` → `is_stale`），无直调内部 helper。
- ✅ 每条新增守卫各附一次「删掉即变红」的变异证明，且变异体经语法校验确认可运行。
- ✅ `ship_gate.py` 保持零第三方依赖；本票新增路径的退出码只取 `3`（`REFUSE_START`），在契约集内。
- ✅ 监视集未动（Task 3 的 `is_stale` 原样复用），实现期改源码 / 勾 plan 复选框仍不失鲜
  （既有 `test_design_anchor_survives_impl_commits` 等用例继续绿）。

## 遗留 / 交棒

- **行为收紧已生效**：实现期「边写边改设计纠偏」今后撞 `REFUSE_START`（design ADR-3 明写为有意为之）。
  tasks 6.4③ 要求在 hand-off 显式登记，属 Task 6 范围，本票未做。
- **窗口右边界的间隙**（「实现刚完成」与「代码审进行中」盘面不可区分）是 design 已登记的残余面，
  本票未试图关闭 —— 关它需引入新盘面信号，与本 change 的简化方向相悖。
- tasks 6.2（`sdflow-ship/SKILL.md` 补窗口行为边界一句）依赖本票行为，属 Task 6。
