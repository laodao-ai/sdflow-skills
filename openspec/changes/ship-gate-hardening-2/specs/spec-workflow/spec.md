## ADDED Requirements

### Requirement: 完成判据任务号按 change 命名空间隔离

`ship_gate.py` 的实现完成判据在收集 `checkpoint(task<N>-)` 完成号集时 MUST 按 change 归属隔离，以根治同一 feature 分支上交错推进两个 change 时同号任务互相污染完成集导致的假齐（假✅）。checkpoint 任务提交的 change 命名空间 MUST 编码于 commit subject 的步名内（`checkpoint(<change>:task<N>-<slug>)`，`<change>` 为 openspec kebab-case slug），由 `sdflow-ship` 的 RUN_PLAN → writing-plans 派发 args 统一注入；`checkpoint-commit.sh` producer MUST NOT 因此改动（逐字插值步名）。gate 解析 MUST 用可选命名空间捕获组（`checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-`）：**命名空间标签**（捕获到 `<ns>`）MUST 仅当 `<ns>` 等于当前 change 才计入完成号集；**裸标签**（无 `<ns>`，旧格式）MUST 保留既有窗口 `[plan_first_sha, HEAD]` 计入语义以向后兼容（proposal A1），MUST NOT 因新格式而丢弃或崩溃。归属规则的取舍 MUST 向假阴（少计=多一次 CONTINUE_IMPL）安全倾斜，MUST NOT 引入新的假阳（假齐放行）。既有 B4 集合归属（`plan_ids ⊆ done_ids`）判据 MUST 叠加于本隔离之上、语义不变。「两个都用旧裸格式的 change 同窗口交错且撞 plan 号」的残留假✅ MUST 在 `ship_gate.py` 头注释「已知不覆盖」中声明（本次不根治，属 Non-Goal）。

#### Scenario: 跨 change 命名空间标签不互相计入〔T32〕
- **WHEN** 当前 change A 的 plan 号集 = {1, 2}，同一分支窗口内只有 A 的 `checkpoint(A:task1-…)`（task2 未完成），另一 change B 的 `checkpoint(B:task2-…)` 落进 A 的窗口（B 的号恰是 A 缺的 task2）
- **THEN** gate 对 A 判定时 MUST 只把 `checkpoint(A:task1-…)` 计入（`done_ids={1}`），MUST NOT 把 `checkpoint(B:task2-…)` 计入（命名空间不匹配即排除）；`plan_ids - done_ids = {2} ≠ ∅` → MUST 判 CONTINUE_IMPL 且 `done_tasks==["1"]`，MUST NOT 因 B 的 task2 顶替使 `done={1,2}` 假齐放行 RUN_CODE_REVIEW〔此判别性负例（B 的号=A 缺的号）方能区分"只计当前"与"两个都计"，MUST NOT 用同号 task1 的无区分力写法〕

#### Scenario: 旧无命名空间 checkpoint 标签向后兼容〔T32〕
- **WHEN** 一个 change 的实现窗口内任务 checkpoint 全为旧格式裸标签 `checkpoint(task<N>-<slug>)`（无 `<change>:` 前缀，gate 升级前已产生或进行中）
- **THEN** gate MUST 按既有窗口语义把裸标签计入该 change 完成号集（= 升级前行为），MUST NOT 因识别不到命名空间而丢弃这些完成号或退出异常；该 change 的完成判据结果 MUST 与本 change 落地前逐字一致（无回归）

### Requirement: 复选框辅通道按 Task 分段绑定

`ship_gate.py` 完成判据的复选框辅通道 MUST 按 plan 的 `### Task <n>:` 分段绑定到对应 task 号，MUST NOT 以全文全局粒度（"全文无任何 `- [ ]`"）一次放行所有 plan task。某 task 号计入复选框完成集 当且仅当**其 `### Task <n>:` 段内**存在复选框且全部已勾（段内无 `- [ ]` 且至少一个 `- [x]`）。复选框识别 MUST **行锚定**（`^\s*-\s+\[[ xX]\]`，非全文子串）且 MUST **忽略 fenced code block（```…```）内的伪复选框**，MUST NOT 把代码块/散文里的 `- [x]` 当完成入口。若同一 task 号对应**多个** `### Task <n>:` 段（plan 手改/复制粘贴），MUST 判该 plan UNKNOWN（`set` 折叠重号会掩盖"一段全勾一段未勾"的假✅），MUST NOT 任一段全勾即计入。复选框完成集 MUST 与 checkpoint 主锚完成集按号并集后再过 B4 集合归属（`done_ids = checkpoint_done ∪ checkbox_done`；`done_in_plan = done_ids & plan_ids`）。既有「plan 未提交（`plan_first_sha` 空）且全 plan 无任何复选框 → UNKNOWN 双通道皆不可判」分支 MUST 保留；段内无复选框的 task MUST 仅凭 checkpoint 主锚判定，MUST NOT 因分段而新增假阳。

#### Scenario: 全局单勾不放行未勾的其它 task〔T34〕
- **WHEN** plan 有 `### Task 1:`（段内 `- [x]` 全勾）与 `### Task 2:`（段内含未勾 `- [ ]`），且无任何 checkpoint 任务标签
- **THEN** gate 的复选框完成集 MUST 只含 task1（其段全勾），MUST NOT 因"全文存在 `- [x]`"或按全局粒度把 task2 也判为完成；`plan_ids - done_ids = {2} ≠ ∅` → MUST 判 CONTINUE_IMPL，MUST NOT 假齐放行 RUN_CODE_REVIEW

#### Scenario: 分段完成集与 checkpoint 主锚并集〔T34〕
- **WHEN** plan 有 task1/task2，task1 由 `checkpoint(<change>:task1-…)` 完成、task2 由其 `### Task 2:` 段内复选框全勾完成
- **THEN** gate MUST 把两通道完成号并集（`{1} ∪ {2} = {1,2}`）后判 `plan_ids ⊆ done_ids` 齐 → 进 code-review 门，MUST NOT 因两通道分立而漏判其一

#### Scenario: 代码块内伪复选框不算完成〔T34/codex#4〕
- **WHEN** 某 `### Task <n>:` 段的真实清单行未勾（`- [ ]`），但该段的 fenced code block（```…```）内含 `- [x]` 示例文本
- **THEN** gate MUST NOT 把该 task 判为复选框完成（行锚定 + 忽略代码块），MUST 依真实未勾行判其未完成

#### Scenario: 重号 Task 段判 UNKNOWN〔T34/codex#3〕
- **WHEN** plan 出现两个同号 `### Task 1:` 段，其一全勾（或有 checkpoint）、其二含未勾 `- [ ]`
- **THEN** gate MUST 判该 plan UNKNOWN（重号不可判），MUST NOT 因任一段全勾就把 task1 计入完成集而掩盖另一段未完成（`set` 折叠重号的假✅）
