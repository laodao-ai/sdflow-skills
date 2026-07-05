## MODIFIED Requirements

### Requirement: 阶段三编排台账确定性（ship_gate）

`sdflow-ship` 的步序推进 MUST 由确定性脚本 `ship_gate.py` 判定（**盘面即状态**：以 change 目录产物存在性与结论行为账本，MUST NOT 设可变 state 文件造第二真相源）；编排 skill MUST 在每步前后调用 gate 并遵其判定，MUST NOT 以 prose 记忆步序。gate MUST 只读（零副作用）、双输出（首行人读摘要 + JSON 机读）、以退出码承载门禁语义（0=可推进 / 3=拒绝起跑 / 4=上游 blocker / 5=verify FAIL / **6=UNKNOWN 判定不能**〔spec-review-amendment〕）；同一报告并存冲突锚行 MUST 判 UNKNOWN 点名冲突行，MUST NOT 猜优先级。机判锚点 MUST 为**模板写死的机器注释行**〔grill-amendment：自然语言结论行正则对真实存档全 miss，禁作锚点〕：设计门拍板 = `<!-- ship-gate: design-approved -->`；verify 结论 = `<!-- ship-gate: verify=PASS -->` / `verify=FAIL`；code-review 放行 = `<!-- ship-gate: code-review=pass -->` / `=blocked`。三个报告的生成模板（sdflow-spec-review 拍板回写约定 / sdflow-done verify 模板 / sdflow-code-review 报告格式）MUST 输出对应锚行；gate 以**行级字面查找**解析——逐行 `strip()` 后整行等值于锚字面、忽略 fenced code block（```）内的行；MUST NOT 用纯子串（否则报告正文对锚的**描述性提及**或代码块内文档示例会假命中，让门禁被非结论文本触发）〔gate-anchor-line-scoped B4〕。锚行集合在脚本头注释与各模板双向钉死同 change 演进（各模板 MUST 把锚写在独占一行）。**完成判据的两处加固**〔ship-gate-hardening-2〕：① checkpoint 任务标签 MUST 按 change 命名空间归属隔离（`checkpoint(<change>:task<N>-)`，gate 只认当前 change；裸标签向后兼容，详见下方「完成任务号按 change 命名空间隔离」Scenario 组）；② 复选框辅通道 MUST 按 `### Task <n>:` 分段绑定、MUST NOT 全局全勾放行所有 task（详见下方「复选框辅通道按 Task 分段绑定」Scenario 组）。

#### Scenario: 未过设计门拒绝起跑
- **WHEN** 对一个 spec-review-report.md 缺失或不含「设计门拍板」标记的 change 调用 /sdflow-ship
- **THEN** ship_gate 退出码 3（REFUSE_START），skill 停止并提示先完成设计门，MUST NOT 起跑任何阶段三步骤

#### Scenario: verify FAIL 停并上抛
- **WHEN** 链行进至 sdflow-done 后 verify-report.md 结论为 FAIL
- **THEN** gate 退出码 5，ship 停止、原样上抛缺口清单，MUST NOT 继续 archive/merge（任何一层评审覆盖不得无声蒸发）

#### Scenario: 前置产物缺失点名
- **WHEN** 某步产物缺失（如 code-review-report.md 不在）
- **THEN** gate 输出 next=对应 skill 与 missing 清单，编排按此推进；实现完成判据 MUST 以 **git 历史 checkpoint 任务标签为主锚**（plan 任务数 N 对 checkpoint 去重任务号集，齐 N 判完成〔grill-amendment〕；标签 MUST 按 change 命名空间归属过滤 `checkpoint(<change>:task<k>-`（裸 `checkpoint(task<k>-` 向后兼容），见下「命名空间隔离」Scenario 组〔ship-gate-hardening-2〕；**收集窗口 MUST 为含 superpowers-plan.md 首次提交自身的闭区间 `[sha, HEAD]`**——即 `git log <sha>..HEAD --no-merges` 加对 `<sha>` 自身 commit subject 的同规则解析；plan 与首个 task 锚同 commit（checkpoint `add -A` 携带未提交 plan 的合法盘面）时该 task MUST 计入，MUST NOT 漏数〔B1 修复，替换旧排他窗口表述〕；MUST NOT 全历史扫描——main 遗留标签会造成假齐 N〔spec-review-amendment 设计门拍板 Q2〕；plan 标题命中 0 → UNKNOWN；**重号 `### Task <n>:` 段 → UNKNOWN**〔ship-gate-hardening-2〕）、plan 复选框**按 `### Task <n>:` 段绑定**为辅（MUST NOT 全局全勾放行所有 task，见下「分段绑定」Scenario 组〔ship-gate-hardening-2〕），两通道皆不可判时 gate 判 UNKNOWN 停上抛，MUST NOT 猜测推进、MUST NOT 以 gitignored 的 SDD ledger 为判据

#### Scenario: plan 与首个 task 锚同 commit 不漏数〔B1〕
- **WHEN** superpowers-plan.md 的首次提交 commit 本身就是 `checkpoint(task1-<slug>)` 提交（plan 未单独提交、被首个 task 的 checkpoint `add -A` 一并携带入库）
- **THEN** gate 的完成任务号集 MUST 含 task1（窗口为含该 commit 自身的闭区间），plan 任务数 N 齐时 MUST NOT 输出 CONTINUE_IMPL 误报

#### Scenario: 陈旧 FAIL 不卡死 resume〔grill-amendment D9〕
- **WHEN** verify-report 带 FAIL 锚行，其提交之后存在触及 `openspec/` 之外路径的修复提交，用户重调 /sdflow-ship
- **THEN** gate 判该结论陈旧 → NEXT=重跑 sdflow-done（重验），MUST NOT 以陈旧 FAIL 退出卡死

#### Scenario: 干预后陈旧 PASS 不放行〔grill-amendment D9〕
- **WHEN** verify/code-review 锚行为 pass/PASS，但其后有人手改了 `openspec/` 之外的代码
- **THEN** gate 判受影响步结论陈旧 → 重跑该步，MUST NOT 让旧结论背书新代码直通 merge

#### Scenario: design-approved 不因实现提交失鲜〔spec-review-amendment 设计门拍板 Q1=B〕
- **WHEN** 设计门拍板锚行已落，实现期产生大量触及 `openspec/` 之外路径的提交（正常实现活动）
- **THEN** gate MUST 保持 design-approved 有效（新鲜度按锚分域：该锚仅当其后存在触及本 change 四件套路径的提交才失鲜须重审），MUST NOT 因实现提交判其陈旧而 REFUSE_START（防实现期链自锁）

#### Scenario: 阶段三合法尾流修订不失鲜〔B2〕
- **WHEN** design-approved 锚行已落，其后 sdflow-code-review 按工作流对 design.md/tasks.md 打 `[impl-review-fix]` 补丁并以 commit subject 闭合字面前缀 `checkpoint(impl-review)`（含右括号）提交（触及四件套路径）
- **THEN** gate 的 design 域新鲜度判定 MUST 豁免该类提交（不判拍板失鲜、不 REFUSE_START）；豁免面 MUST 仅限**精确式 `subject == "checkpoint(impl-review)" 或 subject 以 "checkpoint(impl-review):" 起始`**〔spec-review-amendment BR-7：裸闭合前缀 startswith 仍收 `checkpoint(impl-review)evil` 尾串垃圾，须精确式〕——`checkpoint(impl-review-fix)`/`checkpoint(impl-reviewX)`/`checkpoint(impl-review)evil` 等从不由 checkpoint 脚本合法产生的变体 MUST NOT 豁免（照判失鲜）；其他 subject 触及四件套照判失鲜（实现改设计须重审的既有语义不变）；豁免 MUST NOT 分析改动内容（只认 subject 不认 hunk），由此「经豁免的语义级四件套改动不经二次批准即随档 ship」属**已登记的接受取舍**〔grill Q2〕；伪造/手工 subject 绕过豁免属显式越权同权级（git 留痕可审计），MUST 在脚本头注释「已知不覆盖」中声明

#### Scenario: 未提交报告视为 fresh〔spec-review-amendment 设计门拍板 Q3=A〕
- **WHEN** 某报告文件存在且含锚行，但从未 git 提交（`git log -1 -- <path>` 空输出）
- **THEN** gate MUST 视其为 fresh 并在 JSON 注明 `freshness=uncommitted`（人机同权：手写产物合法），MUST NOT 因无提交记录而判进行中或报错

#### Scenario: 无锚行产物 = 步进行中〔grill-amendment D9〕
- **WHEN** 某报告文件存在但不含任何 ship-gate 锚行（如中断的半成品）
- **THEN** gate 判该步进行中 → NEXT=重跑该步，MUST NOT 当作已完成

#### Scenario: 暂停后重调即续、人机同权〔grill-amendment D9〕
- **WHEN** 链中途停止（任意原因），期间用户手动完成了某步（如手跑 /sdflow-code-review 产出报告），之后重调 /sdflow-ship
- **THEN** gate 仅凭盘面推进（不辨产者），从下一缺口继续；实现中断场景 gate 输出已完成任务号集供 SDD 勿重派；ship MUST NOT 依赖任何跨步内存状态

#### Scenario: 条件步按 TG 判定
- **WHEN** change 的 proposal 未标注 TG-02（非嵌入式）
- **THEN** gate 对 step 5.5 输出 SKIP 并记录理由；命中 TG-02 时高风险/TG-18 细判归模型（每步内部判断，prose 允许域）

#### Scenario: 归档后识别 SHIPPED 终态〔B3 + D3 硬化〕
- **WHEN** change 的 active 目录 `openspec/changes/{change}/` 不存在，但归档目录 `archive/<YYYY-MM-DD>-{change}/`（发现经**纯 git 域** `git ls-tree HEAD ∪ ls-tree <base>` 列举 + `re.escape(change)` 套日期前缀 fullmatch，**MUST NOT 用文件系统 glob**〔H2/BR-4〕）**已存在于 base 树** 且该归档目录内 `verify-report.md` **含 `<!-- ship-gate: verify=PASS -->` 锚**〔H1/BR-2〕
- **THEN** gate MUST 输出 SHIPPED（exit 0），MUST NOT 按 active 路径找不到 spec-review-report.md 而误报「未过设计门」；该短路判定 MUST 位于设计门 pre-flight 与新鲜度检查之前；终态判据 MUST 为 change 域可达性（`git ls-tree <base>`）而非全局 `branch_state()`〔grill-amendment〕；发现 MUST 与判据同域（纯 git，工作树无关）——MUST NOT 用工作树 glob（否则跨分支查已并 change 会假 REFUSE、未跟踪垃圾目录会假 RUN_VERIFY）〔H2/BR-4〕；SHIPPED MUST 追读 archived verify=PASS 锚——MUST NOT 仅凭目录存在性放行（手工空壳归档目录不得假 SHIPPED）〔H1/BR-2〕；`--change` MUST 校验为 slug 或 `re.escape` 后匹配，MUST NOT 把用户输入当 glob 元字符〔H5/HRTG-4〕；base 无 main/master → UNKNOWN，detached HEAD 对 D3 判定无关（凭 base 树可达仍可 SHIPPED）〔H3/H4〕；active 存在时 final SHIPPED 的 archived 谓词 MUST 收紧，MUST NOT 被旧/同名 archive 触发〔H1/HRTG-1〕

#### Scenario: 完成判据按任务号集合归属，非基数〔B4〕
- **WHEN** plan 有 `### Task 1:`/`### Task 2:`（计划号集 {1,2}），实现窗口内出现 `checkpoint(task1-…)` 与一个**计划外**的 `checkpoint(task9-…)`（遗留/错号/merge 内提交），task2 从未完成
- **THEN** gate 的完成判据 MUST 按**任务号集合归属**（plan 号集 ⊆ 完成号集）判齐，MUST NOT 按基数 `len(done) < n` 判——否则计划外 task9 会顶替缺失的 task2 让 `len(done)=2=N` 假齐、误放行 RUN_CODE_REVIEW（活体复现的假✅）；此盘面 MUST 输出 CONTINUE_IMPL，`done_tasks` MUST 只报计划内已完成号（不含 9）

#### Scenario: 归档但未并入 base = merge 收尾未完〔B3〕
- **WHEN** active 目录不存在、日期前缀 glob 命中 archive，但该归档目录**不在 base 树里**（archive commit 停在未并分支，`git ls-tree <base>` 空）
- **THEN** gate MUST 输出 RUN_VERIFY（next=sdflow-done）并在 reason 说明「已归档但分支未并，完成 merge 收尾」，MUST NOT 判 SHIPPED、MUST NOT 判 REFUSE_START

#### Scenario: change 不存在与未过设计门区分〔B3〕
- **WHEN** active 目录不存在、且日期前缀锚死 glob 在 archive 下无命中（change 名拼错或从未创建；后缀撞名的别的 change 归档因 glob 锚死日期段 MUST NOT 误命中）
- **THEN** gate MUST 输出 REFUSE_START 且 reason 为「change 不存在（active 与 archive 均无）」，MUST NOT 输出误导性的「未过设计门请补锚」提示；active 目录存在时同名历史归档 MUST NOT 干扰判定（active 优先）

#### Scenario: 完成任务号按 change 命名空间隔离〔T32/ship-gate-hardening-2〕
- **WHEN** 当前 change A 的 plan 号集 = {1, 2}，同一分支窗口内只有 A 的 `checkpoint(A:task1-…)`（task2 未完成），另一 change B 的 `checkpoint(B:task2-…)` 落进 A 的窗口（B 的号恰是 A 缺的 task2；触发本需 stacking——feat/A 上再建 change B，FF-0 不拦 feature 分支 stacking）
- **THEN** gate 对 A 判定时 MUST 只把 `checkpoint(A:task1-…)` 计入（`done_ids={1}`），MUST NOT 把 `checkpoint(B:task2-…)` 计入（命名空间 `<ns>` 严格 `==` 当前 change 才计；`foo` 与 `foo-bar` 精确互斥非前缀）；`plan_ids - done_ids = {2} ≠ ∅` → MUST 判 CONTINUE_IMPL 且 `done_tasks==["1"]`，MUST NOT 因 B 的 task2 顶替使 `done={1,2}` 假齐放行 RUN_CODE_REVIEW〔判别性负例（B 号=A 缺号）方能区分"只计当前"与"两个都计"，MUST NOT 用同号无区分力写法〕；解析 MUST 用可选命名空间捕获组 `checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-`，且 `done_task_ids` 的字面前缀过滤 MUST 同步放宽为 `startswith("checkpoint(")`（MUST NOT 保留 `startswith("checkpoint(task")`——否则命名标签在 `TAG_RE.match` 前被整条跳过、T32 静默失效）；回归覆盖 MUST 用真实 git commit fixture

#### Scenario: 旧无命名空间 checkpoint 标签向后兼容〔T32/ship-gate-hardening-2〕
- **WHEN** 一个 change 的实现窗口内任务 checkpoint 全为旧格式裸标签 `checkpoint(task<N>-<slug>)`（无 `<change>:` 前缀，gate 升级前已产生或进行中）
- **THEN** gate MUST 按既有窗口 `[plan_first_sha, HEAD]` 语义把裸标签计入该 change 完成号集（= 升级前行为），MUST NOT 因识别不到命名空间而丢弃或退出异常；该 change 完成判据结果 MUST 与本加固落地前逐字一致（既有 B1/B4 及全部裸格式回归测试不变）；归属取舍 MUST 向假阴（少计=多一次 CONTINUE_IMPL）安全倾斜、MUST NOT 引入假阳。「污染方用旧裸格式 stacking 进来 + 撞 plan 号」残留假✅ MUST 记入 `ship_gate.py` 头注释「已知不覆盖」，MUST NOT 用"每 change 独立分支纪律"作缓解（纪律成立则污染不可达、立论自否——见 adr/0008 防御纵深立场）

#### Scenario: 复选框全局单勾不放行未勾的其它 task〔T34/ship-gate-hardening-2〕
- **WHEN** plan 有 `### Task 1:`（段内 `- [x]` 全勾）与 `### Task 2:`（段内含未勾 `- [ ]`），且无任何 checkpoint 任务标签
- **THEN** gate 的复选框完成集 MUST 只含 task1（其段全勾），MUST NOT 因"全文存在 `- [x]`"或全局粒度把 task2 也判完成；`plan_ids - done_ids = {2} ≠ ∅` → MUST 判 CONTINUE_IMPL，MUST NOT 假齐放行；复选框识别 MUST 行锚定 `^\s*-\s+\[[ xX]\]`（非全文子串）且 MUST 忽略 fenced code block 内伪复选框

#### Scenario: 分段完成集与 checkpoint 主锚并集〔T34/ship-gate-hardening-2〕
- **WHEN** plan 有 task1/task2，task1 由 `checkpoint(<change>:task1-…)` 完成、task2 由其 `### Task 2:` 段内复选框全勾完成
- **THEN** gate MUST 把两通道完成号并集（`{1} ∪ {2} = {1,2}`）后判 `plan_ids ⊆ done_ids` 齐 → 进 code-review 门，MUST NOT 因两通道分立而漏判其一

#### Scenario: 代码块内伪复选框不算完成〔T34/ship-gate-hardening-2〕
- **WHEN** 某 `### Task <n>:` 段的真实清单行未勾（`- [ ]`），但该段的 fenced code block（```…```）内含 `- [x]` 示例文本
- **THEN** gate MUST NOT 把该 task 判为复选框完成（行锚定 + 忽略代码块），MUST 依真实未勾行判其未完成

#### Scenario: 重号 Task 段判 UNKNOWN〔T34/ship-gate-hardening-2〕
- **WHEN** plan 出现两个同号 `### Task 1:` 段，其一全勾（或有 checkpoint）、其二含未勾 `- [ ]`
- **THEN** gate MUST 判该 plan UNKNOWN（重号不可判），MUST NOT 因任一段全勾就把 task1 计入完成集而掩盖另一段未完成（`plan_task_ids` 的 `set` 折叠重号的假✅）

#### Scenario: 描述性锚提及不触发门禁〔gate-anchor-line-scoped B4〕
- **WHEN** 某报告（如 spec-review-report.md）正文含机判锚字面（`<!-- ship-gate: design-approved -->` 等）但**非独占一行**——内联在描述句中（前后有其它字符 / 行内反引号包裹）、或独占一行但位于 fenced code block（```）内作文档示例，且结论区**无**独占一行的真锚
- **THEN** gate 的锚检测 MUST 判该锚**未命中**（返回集合不含它）——描述性提及 / 文档示例 MUST NOT 触发对应门禁；对 design-approved 而言此盘面 MUST 判 REFUSE_START（未过设计门），MUST NOT 因子串命中假过设计门越过 adr/0004 红线〔活体复现：checkpoint-tag-single-source 报告仅含描述句即被首跑假放行 RUN_PLAN〕；行级判据 MUST 保留多命中语义——`verify=PASS` 与 `verify=FAIL` 各独占一行并存时 MUST 仍各自命中以触发 UNKNOWN 冲突判定，MUST NOT 因行级收紧而漏返冲突锚；锚检测的两处解析点（读文件的 `anchors_in` 与读 git-show 文本的 `archived_verify_state`）MUST 共用同一行级判据，MUST NOT 只收紧其一

#### Scenario: 归档 verify 描述性提及不触发假 SHIPPED〔gate-anchor-line-scoped B4·SHIPPED 路径〕
- **WHEN** 归档目录的 `verify-report.md`（经 `git show <base>:…` 读出）正文**描述性提及** `<!-- ship-gate: verify=PASS -->`（内联句 / 代码块内文档示例）但**无独占一行的真 PASS 锚**
- **THEN** `archived_verify_state` MUST 判其 verify 态为 `none`（非 `pass`），使归档终态短路 MUST NOT 输出假 SHIPPED——空壳 / 未验 / 仅描述性提及的归档目录 MUST 落 fail-safe（不 SHIPPED，请人工核验）；此判据 MUST 与 `anchors_in` 同为行级整行等值 + 忽略 fenced code block（同一 `_line_scoped_hits` 核心），MUST NOT 保留裸子串路径
