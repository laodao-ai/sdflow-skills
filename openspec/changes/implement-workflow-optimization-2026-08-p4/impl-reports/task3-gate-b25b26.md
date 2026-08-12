# Task 3 impl-report · ship_gate B25/B26 机械门

## 环境说明（worktree 与主干分叉）

本票在 worktree `agent-a59bfcdee757f5b25` 内执行；该 worktree 的分支基于
`feat/remove-superpowers-pipeline` 归档提交，而非 `feat/implement-workflow-optimization-2026-08-p4`
——`openspec/changes/implement-workflow-optimization-2026-08-p4/` 四件套在此 worktree 内不存在
（本文件与其所在目录为本票新建）。经核验：`git diff HEAD
feat/implement-workflow-optimization-2026-08-p4 -- sdflow-ship/scripts/ship_gate.py
sdflow-ship/tests/` 输出为空——本票唯一涉及的代码面（`ship_gate.py` + 其测试目录）在两分支间
字节相同，故本票所有改动直接在本 worktree 落地即可，无需切分支。design.md / specs / tickets.md
通过 `git show feat/implement-workflow-optimization-2026-08-p4:<path>` 与主 checkout 只读读取
（未修改，仅作为需求源）。**主 session 需知悉**：本报告与其目录当前只存在于本 worktree，
需按该 worktree 的正常收口流程并入目标分支。

## 做了什么

在 `sdflow-ship/scripts/ship_gate.py` 的既有两个报告消费点新增两道机械门：

### ① 锚存在门（B25）—— `metrics_enabled()` + `guard_report_anchors()`

- `metrics_enabled(root)`：读 `openspec/config.yaml` 的 `metrics.enabled`，四态：
  文件不存在→False；键缺失→False（yq default）；值非法布尔或 yq 解析失败→
  `GateIndeterminate`（fail-closed，main() 唯一映射点转 UNKNOWN(6) + problem/cause/fix）；
  合法布尔→该值。**先判文件存在性再调 `_yq()`**（`_yq()` 对缺文件裸 raise）。
- `guard_report_anchors(root, report_path, layer, *, require_ref_check)`：metrics 关闭时
  零开销放行（不读报告）；开启时校验报告（fence 外）含 `sdflow:lens-metric v1
  layer="<layer>"` 锚；code-review 层（`require_ref_check=True`）另需
  `sdflow:ref-check v1` 结构化锚（存在性门，不校验内部字段——字段级校验属
  `anchor_lint.py` 职责）。
- 接入两个消费点：
  - design 门读 `spec-review-report.md`（`decide()` 内 `design_ok` 确认之后）——
    `layer="spec-review"`，`require_ref_check=False`。此检查**不限于** RUN_PLAN/
    CONTINUE_IMPL 求值窗口，每次 `decide()` 调用都核验（报告内容完整性检查，
    与 git 域失鲜判定的求值窗口是独立判据）；失败指引显式提示「转换态」
    （metrics 在报告写就后才翻 true 的场景）。
  - step8 读 `code-review-report.md`（`cr_state == "pos"` 确认之后、`is_stale` 判定之前）——
    `layer="code-review"`，`require_ref_check=True`。

### ② defer 对账门（B26）—— 表格解析 + `guard_defer_ledger()`

- `_defer_ledger_id_cells(text)`：扫报告全文（fence 外）全部 GFM 表格（有界子集：
  仅认「每行首尾 pipe」形态，不追求覆盖转义 pipe 等第三方 markdown 变体——基准 5，
  只审自家 producer 产物），取表头列名（大小写/空白不敏感）=="id" 的那一列，产出
  每条数据行该列的原始单元格文本。**台账行判别窄化**：只对声明了 id 列的表格数据行
  生效——无 id 列的表格（如 Findings 表）、无 pipe 的散文（聚合摘要句）一律不产出，
  不做全行子串搜索。
- `guard_defer_ledger(root, change, report_path)`：逐个提取到的单元格校验：
  ① 整格须恰为单个 `T\d+`/`B\d+`；② 对应 `openspec/issues/open/**/<id>.md`
  **文件系统存在**（`Path.glob`，非 git 跟踪清单——门在 commit 前跑，池文件可能
  尚未 `git add`）；③ 池文件 frontmatter `source_change` 字段等于当前 change
  （读取见下方"踩坑"）。任一不满足 ⇒ 失败 reason，MUST NOT 判「有没有 defer」
  本身（无 id 列表格 = 零待对账项，直接放行，兼容旧散文台账）。
- 接入 step8（`cr_state == "pos"` 之后，紧随锚存在门）。

### 两门共用

- `_fence_outside_text_lines()`：复用单一源 `FenceTracker`（与 `_line_scoped_hits`/
  `_normalize_checkbox_lines`/`_parse_plan` 同口径），锚检测与表格解析均 fence-aware。
- verdict 一律字面复用既有 `STEP_IN_PROGRESS`，未新增 verdict 名。
- 新增 `CAUSE_CONFIG_UNPARSEABLE` + `_INDETERMINATE_ADVICE` 条目（沿用文件既有
  problem+cause+fix 单一映射点纪律）。

## 关键实现决策（design.md 未细化到字节级的部分，本票自行定案）

1. **`sdflow:ref-check` 锚的判定粒度**：只做存在性检查（`<!-- sdflow:ref-check v1`
   前缀命中），不解析 status=/pass=/fail=/uncheckable= 字段——design.md 明确
   「gate 检测该锚而非段标题/散文」，字段级校验是 anchor_lint 的既有职责
   （Task5 producer 侧尚未落该锚，字段格式由 Task5 定案）。
2. **defer 台账表格的 id 列判据 = 表头单元格 == "id"（大小写/空白不敏感）**：
   spec-workflow delta 只规定"专用 id 列、单元格全部内容 = 单个 id"，未给出列名
   字面——本票选最直白的约定（列名恰为 "id"）并在代码注释中显式记录，供 Task5
   （SKILL 报告模板改写，Blocked-by 含本票）对齐。
3. **`_pool_source_change` 用 `_yq(".", front_matter=True)` 取整份 frontmatter
   再 `.get()`，而非 `_yq(".source_change", front_matter=True)` 直接取子字段**：
   踩坑记录见下方"过程中的坑"。
4. **两道新门在 `decide()` 内的插入位置**：设计门检查放在 `design_ok` 确认之后、
   `emit_windowed` 求值窗口逻辑之前（内容完整性检查与失鲜求值窗口是独立判据，
   不应共享窗口限定）；code-review 两门放在 `cr_state == "pos"` 确认之后、
   `is_stale` 判定之前（报告本身不完整比它是否陈旧更基础）。

## 过程中的坑（有实证价值，记录避免下次重踩）

**`_yq()` 的 `front_matter=True` 校验耦合了调用方假设**：`_yq()` 内部对
`front_matter=True` 有一道校验——`if front_matter and not isinstance(parsed, dict):
raise RuntimeError(...)`。这道校验是为其唯一既有调用方 `parse_ship_gate_frontmatter`
（表达式恒为 `.` 或 `."ship-gate"`，取整块/整子树，恒应为 dict）写的。我最初写
`_pool_source_change` 时用表达式 `.source_change`（取单个标量字段）复用同一
`front_matter=True` 通道，结果每次都撞上这道 dict 校验而 raise——因为提取出的
是字符串而非 dict。用测试（`test_defer_gate_blocked_when_source_change_mismatched`）
实跑才发现（`source_change` 读出来恒为 `None`，而非期望的池文件真实值）。
修法：表达式改回 `.`（取整份 frontmatter dict），在 Python 侧 `.get("source_change")`。
这是「落笔前先证伪」的一个实例——直接 `git diff` + 真跑测试才捞出，而非凭读代码猜对。

## 测试

新增 `sdflow-ship/tests/test_gate_report_anchors.py`，32 个用例，覆盖 tickets.md
Task3 的全部 8 条验收复选框 + 测试矩阵要求：

- `metrics_enabled` 四态（文件缺失/键缺失/true/false/坏值 fail-closed/坏 YAML 语法 fail-closed）
- **`test_metrics_enabled_parity_with_anchor_lint`**：design.md scope-check 表
  「`anchor_lint.py::_metrics_enabled` ↔ ship_gate B25 门新读取点……改一处必查
  另一处 + 一致性测试」的落地——对同一组 config.yaml 状态断言两处独立实现
  好态结果一致、坏态同拒绝。
- 锚检测（lens-metric layer 匹配 / fence 内锚样例不触发 / ref-check 存在性 + fence）
- defer 台账提取（窄化：id 列独立提取、无 id 列表格不扫、聚合摘要句无 pipe 不触发、
  fence 内表格不触发、malformed id 原样产出交调用方判定）
- CLI 端到端（`run_gate` subprocess，覆盖 code-review 层 + design 层两个消费点）：
  config 缺省/false/文件不存在=放行、开启+缺锚=拦截（区分仅缺 ref-check 的场景）、
  坏值=fail-closed（UNKNOWN + cause_category）、锚齐全=放行；defer 门有效 id+池文件
  存在+change 匹配=放行、id 非法=拦截、池文件缺失=拦截、change 不符=拦截、
  **池文件未 commit（仅写盘）=仍放行**（验证"文件系统存在性非 git 跟踪清单"）、
  描述列旧票号不误抓=放行。

结果：`/usr/bin/python3 -m pytest sdflow-ship/tests/ -q` → **372 passed**
（既有 340 个用例零回归 + 新增 32 个全绿）。

全仓 `/usr/bin/python3 -m pytest -q`（跑于本 worktree，覆盖全部 skill 的测试群，
432.59s）：**2591 passed, 1 failed, 10 skipped**。唯一失败
`sdflow-init/tests/test_outside_voice_job.py::
test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret` 与本票无关——
它是 outside-voice 异步 job 的真机对照组测试（真拉起 `claude --bg --exec` 后轮询
`claude logs <id>`，60s 超时内本沙箱环境未见回显），核验 `git status --short` 确认
本票**未触碰** `sdflow-init/` 任何文件（改动面仅 `sdflow-ship/scripts/ship_gate.py` +
`sdflow-ship/tests/test_gate_report_anchors.py`），该失败与本票代码无因果关系，属
沙箱环境对真机 `claude` CLI 后台任务日志的既有不确定性，本票不负责修复（超出
Task3 scope：ship_gate B25/B26 机械门）。

## Concerns / 已知边界

- **`sdflow:ref-check` 锚的产出侧（Task5）尚未实现**——本票只实现消费侧（存在性
  检测）。Task5 Blocked-by 含 Task3，届时若产出格式与 `_ref_check_present()` 假设
  的前缀 `<!-- sdflow:ref-check v1` 不一致，需回来对齐（低风险：前缀是本仓
  `sdflow:*` 锚族的统一约定，Task5 大概率照抄）。
- **defer 台账 id 列列名约定（"id"）为本票选定**，非 design.md/spec 逐字指定
  （见"关键实现决策②"）——Task5 改写 SKILL 报告模板时须采用同一列名，已在代码
  注释显式记录供对齐。
- **`_defer_ledger_id_cells` 的表格解析是有界子集**（不支持转义 pipe `\|`、
  不支持无首尾 pipe 的表格变体）——仅覆盖本仓 producer 会实际产出的形态，
  基准 5 范围内的有意简化，非疏漏。
