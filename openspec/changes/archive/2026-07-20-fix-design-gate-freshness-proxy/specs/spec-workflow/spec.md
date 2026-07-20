## MODIFIED Requirements

### Requirement: 阶段三编排台账确定性（ship_gate）

`sdflow-ship` 的步序推进 MUST 由确定性脚本 `ship_gate.py` 判定（**盘面即状态**：以 change 目录产物存在性与结论行为账本，MUST NOT 设可变 state 文件造第二真相源）；编排 skill MUST 在每步前后调用 gate 并遵其判定，MUST NOT 以 prose 记忆步序。gate MUST 只读（零副作用）、双输出（首行人读摘要 + JSON 机读）、以退出码承载门禁语义（0=可推进 / 3=拒绝起跑 / 4=上游 blocker / 5=verify FAIL / **6=UNKNOWN 判定不能**〔spec-review-amendment〕）；同一报告并存冲突结论 MUST 判 UNKNOWN 点名冲突，MUST NOT 猜优先级。

**机判结论的承载形态按报告位置分流（mlh-p5：去字符串化家族①，inline 锚 → frontmatter）**：

- **live 报告（`openspec/changes/{change}/*.md`）MUST 以报告 YAML frontmatter 承载结论状态**，schema 在 `ship-gate:` 顶层键下：设计门拍板 = `design_approved: true`（spec-review-report.md）；verify 结论 = `verify: PASS` / `verify: FAIL`（verify-report.md）；code-review 放行 = `code_review: pass` / `code_review: blocked`（code-review-report.md）。每报告 MUST 只落自己那一类字段。三报告的生成模板（sdflow-spec-review 拍板回写约定 / sdflow-done verify 模板 / sdflow-code-review 报告格式）MUST 在 frontmatter 输出对应字段。gate 对 live 报告 MUST 解析 frontmatter（`ship_gate.py` 自持的 frontmatter 解析路径）读结论：字段值 MUST 按严格枚举校验（`verify ∈ {PASS,FAIL}`、`code_review ∈ {pass,blocked}`、`design_approved` 为 bool）。**结论承载态按盘面精确分流两类，MUST NOT 混为一谈**〔mlh-p5-parser-cleanup 澄清〕：**(a) absent（无有效 frontmatter block / 顶层无 ship-gate 键）→ 既有无锚语义**（design→REFUSE_START、verify/code-review→步进行中；MUST NOT 静默当已过门）；**(b) 首块成立但内容坏（字段越域 / 同字段重复键 / 坏 YAML 语法 / tab 缩进 / 类型不符）→ fail-closed 判 UNKNOWN(6)**（歧义须人裁）。**「首行 `---` 无闭合（无第二个 `---`，首块不成立）」归 (a) absent，MUST NOT 归 (b) 坏**——无闭合 `---` 不构成 frontmatter block（与下方 A2「只认首块」的首块定义自洽），是正文/markdown 横线。**报告正文对锚字面的任何提及（描述句、对账清单、fenced code block 内示例，含独占一行）MUST NOT 参与 live 结论解析**——正文平面与状态平面分离，从根消除子串/prose-inline 混淆（gate-anchor-line-scoped B4/B5 根治）。
- **归档报告（`archive/<YYYY-MM-DD>-{change}/*.md`）MUST frontmatter + inline 双读**〔mlh-p5 grill G2；冷审 F2〕：归档 verify 态判定（`archived_verify_state`，经 `git show <base>:…` 读）MUST **frontmatter 优先、无则回退 inline**——因迁移后 `sdflow-done` **归档的**报告本身即 frontmatter 格式（新归档 = frontmatter），迁移前旧归档 = inline 锚。inline 读半场 MUST 以**行级字面查找** `<!-- ship-gate: verify=PASS -->` / `verify=FAIL` 解析（逐行 `strip()` 后整行等值、忽略 fenced code block、MUST NOT 用纯子串），且 MUST **永久保留**（旧归档只含 inline、改历史不可取）；frontmatter 读半场 MUST 认新归档的 `ship-gate.verify`。**MUST NOT 只读 inline**——否则迁移后新归档的 verify=PASS 判不出、SHIPPED 回归〔grill G2〕。

**解析半场退役边界（mlh-p5；mlh-p5-parser-cleanup 收尾）**：live 报告结论解析切 frontmatter 后，`_line_scoped_hits` 的 **live 报告读半场**（`anchors_in` 对 live 文件的行级 inline 锚解析）MUST 退役；**归档读的 inline 半场（`_line_scoped_hits`）MUST 永久保留** + **新增 frontmatter 读**——「删整套解析机器」订正为「删 live inline 读、保留归档 inline 读 + 加归档 frontmatter 读」。**退役后遗留的死符号（`anchors_in` / `pick_exclusive` 及仅供其用的 live inline 锚常量 `ANCHOR_DESIGN` / `ANCHOR_CR_PASS` / `ANCHOR_CR_BLOCKED`）MUST 物理删除**〔mlh-p5-parser-cleanup T75〕——「退役」= 从判定路径摘除 + 源码删除，MUST NOT 留 test-referenced 孤儿假装被覆盖；**`ANCHOR_VERIFY_PASS` / `ANCHOR_VERIFY_FAIL` 与 `_line_scoped_hits` MUST 保留**（归档 dual-read 现役真用，删之即归档 SHIPPED 回归）。

**过渡期渐进迁移（mlh-p5 grill G3）**：producer 未全迁的过渡期，gate 对 **live** 报告 MUST **frontmatter 优先、无 ship-gate 键则回退 inline**（已迁 producer 报告即刻正文免疫、未迁者 inline 兼容）；退役后（三 producer 全迁 + 测试全绿）live MUST 只读 frontmatter。过渡期未迁 producer 的正文假阳风险为**已登记短时取舍**（迁完即消，MUST NOT 因过渡期未根治而阻塞迁移）。

**〔spec-review-amendment〕迁移正确性五铁律（多镜冷审拦下 1 致命 + 3 高，MUST 全落）**：

- **A1（D1，致命）live 读点完整集合**：live 报告结论的 inline 读点 MUST 被识别为**完整集合**——`anchors_in`(design-approved) + **`pick_exclusive`×3**(verify 早检/终门、code-review) + peek `anchors_in`(verify=FAIL) + **`anchor_set`熔断 helper**。frontmatter 化/退役 MUST 覆盖全部读点，MUST NOT 只退役 `anchors_in`——否则 verify/code-review 迁 frontmatter 后 `pick_exclusive` 读不出 inline → 返回 None → STEP_IN_PROGRESS 永卡、无法 SHIPPED（3 类迁 2 类静默失效）；`anchor_set` 未迁则重跑后已写有效 frontmatter 结论被熔断误判无进展。实现起手 MUST 先产出「live 结论读点清单」。
- **A2（D2，高）frontmatter 只认文件首块**：手写解析器 MUST 只识别**文件第 1 行 `---`**（先去 BOM）起、到下一 `---` 止的**唯一首块**；正文任何 `---` markdown 横线 / `ship-gate:` 键 MUST NOT 参与解析（实测报告正文横线密布）。MUST 用 `splitlines()` 口径。MUST NOT 用「全文找首个 `---`/找下个 `---`」松散写法（否则正文横线块被当 frontmatter，B4/B5 复活且 fence-aware 失效）。**首块的成立以「有闭合 `---`」为前提**〔mlh-p5-parser-cleanup T74〕：首行是 `---` 但**无下一个 `---`** 时首块**不成立** → MUST 判 absent（无 frontmatter），MUST NOT 判坏 / fail-closed / UNKNOWN——此形态是正文以 markdown 横线开头，非「写坏的 frontmatter」；absent 在 live 各步均不放行（方向安全，见下「首行 `---` 无闭合判 absent」Scenario）。
- **A3（D3，高）坏≠无 + 退出码映射**：过渡期/归档回退**只**由「absent」触发；**首块成立后的解析失败 / 坏键 / 越域 MUST NOT 回退、直接 fail-closed**（三分支：有效键→用之 / **absent→回退 inline / 走无锚语义** / 首块成立但键坏→fail-closed）。**「absent」含两子形态**〔mlh-p5-parser-cleanup 细化；spec-review SC-1：用 (i)/(ii) 与坏子类的 ①-⑤ 及主体 (a)/(b) 三套标记区分，免阅读歧义〕：**(i)** 无有效首块 frontmatter（首行非 `---`；**或首行 `---` 但无闭合 = 首块不成立**）；**(ii)** 有首块但顶层无 `ship-gate:` 键——两者均走既有无锚语义 / 回退 inline，MUST NOT fail-closed。fail-closed 的退出码 MUST 按坏法确定映射、MUST NOT 用「停下**或**进行中」的歧义并存：越域/重复键/坏语法/类型不符/tab 缩进 → **UNKNOWN(exit 6)**（歧义须人裁、防 exit 0 重跑死循环）；纯缺字段(半成品) → 既有无锚语义（spec-review REFUSE_START(3) / verify·code-review STEP_IN_PROGRESS(0)）。
- **A4（D4，高）live 与归档 frontmatter 读共用同一严格核心**：MUST 新增**单一自持文本级 helper**（如 `parse_ship_gate_frontmatter_text(text)`），`anchors_in`/live 读与 `archived_verify_state`/`git show` 归档文本读**都调它**（复刻现 `_line_scoped_hits` 被两路共用的防漂移纪律）。归档 frontmatter 坏 → fail-safe `none`，MUST NOT 回退 inline 掩盖。**归档 frontmatter 有效 PASS 时 MUST NOT 再交叉扫 inline FAIL**（设计门 Q4 决：frontmatter 即真相）；「好 frontmatter=PASS 掩盖残留 inline=FAIL」盲区 MUST 在 `ship_gate.py`「已知不覆盖」登记（迁移后新归档无残留 inline，风险低）。
- **A5（D12）fail-closed 可观测**：fail-closed 判无有效状态时 `emit()` 的 reason MUST 携带**被拒字段名 + 失败类别**（语法/越域/重复键/类型），MUST NOT 只回「无有效状态」（adr/0006 可观测落地）；对应测试断言 reason 含缺陷标识。

**〔spec-review-amendment D5〕门禁语义等价性订正**：D5「门禁语义不变」MUST 精确表述为——冲突判定的**触发承载**从 inline「PASS/FAIL 行级并存」改为 frontmatter「同字段重复键」，语义等价性**仅在「歧义即不放行」这一层成立**；frontmatter 单 `verify:` 键物理上无法承载行级并存，live 侧不再有「PASS/FAIL 行级并存」触发（避免实现误在 frontmatter 复刻行级并存检测）。

**完成判据的两处加固**〔ship-gate-hardening-2，与锚承载形态正交、不受 mlh-p5 影响〕：① checkpoint 任务标签 MUST 按 change 命名空间归属隔离（`checkpoint(<change>:task<N>-)`，gate 只认当前 change；裸标签向后兼容，详见下方「完成任务号按 change 命名空间隔离」Scenario 组）；② 复选框辅通道 MUST 按 `### Task <n>:` 分段绑定、MUST NOT 全局全勾放行所有 task（详见下方「复选框辅通道按 Task 分段绑定」Scenario 组）。

#### Scenario: 未过设计门拒绝起跑
- **WHEN** 对一个 spec-review-report.md 缺失或 frontmatter 无 `design_approved: true` 的 change 调用 /sdflow-ship
- **THEN** ship_gate 退出码 3（REFUSE_START），skill 停止并提示先完成设计门，MUST NOT 起跑任何阶段三步骤

#### Scenario: verify FAIL 停并上抛
- **WHEN** 链行进至 sdflow-done 后 verify-report.md frontmatter 结论为 `verify: FAIL`
- **THEN** gate 退出码 5，ship 停止、原样上抛缺口清单，MUST NOT 继续 archive/merge（任何一层评审覆盖不得无声蒸发）

#### Scenario: live 报告 frontmatter 承载结论被正确解析〔mlh-p5〕
- **WHEN** live 的 spec-review-report.md / verify-report.md / code-review-report.md 各在 frontmatter 落 `ship-gate.design_approved: true` / `ship-gate.verify: PASS` / `ship-gate.code_review: pass`
- **THEN** gate MUST 从 frontmatter 读出对应结论并按既有门禁语义推进（design-approved→放行设计门、verify PASS→继续收尾、code_review pass→进 verify），MUST NOT 依赖正文任何 inline 文本

#### Scenario: live 报告正文提及锚字面不触发门禁〔mlh-p5：B4/B5 根治〕
- **WHEN** 某 live 报告 frontmatter **无** ship-gate 结论字段，但正文（描述句 / 对账清单 / fenced code block 内示例 / 独占一行）原样写出锚字面如 `<!-- ship-gate: design-approved -->` 或 `ship-gate.verify: PASS`
- **THEN** gate MUST 判该结论**未落**（live 只解析 frontmatter，正文平面不参与）——对 design-approved 而言此盘面 MUST 判 REFUSE_START（未过设计门），MUST NOT 因正文提及假过门越 adr/0004 红线；正文任意位置写出锚串 MUST NOT 影响任何门禁判定

#### Scenario: 首行 `---` 无闭合判 absent 不硬崩〔mlh-p5-parser-cleanup T74；grill Q3 措辞订正〕
- **WHEN** 某 live 报告首行是 `---`（去 BOM 后）但全文**无第二个 `---`**（首块不闭合——纯结构条件，**不问意图**：无论是正文以 markdown 横线分节开头，还是有意写 frontmatter 却漏写闭合 `---`）
- **THEN** `parse_ship_gate_frontmatter` MUST **仅依结构判 absent（`({}, None)`）**——首块无闭合即不成立、不构成 frontmatter block（与 A2「只认首块」定义自洽）；**MUST NOT 把「是否有意声明 ship-gate 状态」纳入判据**（parser 只看结构、看不见意图；意图属概率空间，纳入即违「盘面即状态」机判契约纪律）——无意的水平线与有意漏闭合的 frontmatter **同等**判 absent。gate MUST 走既有无锚语义（spec-review-report → REFUSE_START(3)；verify/code-review report → STEP_IN_PROGRESS(0)），**MUST NOT 判 UNKNOWN(exit 6) 硬崩一份干净报告**；「有意漏闭合」者走无锚语义（REFUSE_START/重跑）属**方向安全**（假阴漏判非假阳假过），与 `ship_gate.py` 已登记「false absent → 方向安全」及 adr/0011 目标态论证一致；MUST 有 pytest 用例断言此输入返回 `({}, None)` 而非任何坏类别。**SHOULD** 在 live emit reason 附一句**纯结构**诊断提示（「首行为 `---` 但未见闭合 `---`，已按正文处理；欲声明状态请补闭合行」）恢复 DX actionability〔spec-review Q1=A〕——提示 MUST 走 live 读点**上层独立结构判定**、MUST NOT 改 `parse_ship_gate_frontmatter` 返回签名（防波及 `anchor_set`/`archived_verify_state` 三调用方）、MUST NOT 改 verdict/退出码、MUST NOT 探测意图（纯结构 ≠ candidate② 的「下一行是否 `key:` 形态」，不重开自指免疫）

#### Scenario: live 报告 frontmatter 写坏 fail-closed〔mlh-p5：决策 6 + grill G4 攻击面；mlh-p5-parser-cleanup 收窄触发面〕
- **WHEN** 某 live 报告**有成立的首块 frontmatter（首行 `---` 且有闭合 `---`）**，但块内被 LLM 写坏——任一：① 顶层 `ship-gate:` 键**重复**或同字段（如 `verify:`）**重复键**；② tab 缩进 / 混合缩进；③ 字段值越域（`verify: MAYBE`）；④ 值类型不符（`design_approved: yes`/非 bool）；⑤ 顶层 `ship-gate:` 带非空内联标量值（`ship-gate: []`/`true`）
- **THEN** 手写 stdlib 解析器 MUST **fail-closed** 判「无有效状态」→ UNKNOWN(exit 6) 停下报告点名，MUST NOT 静默当已过门、MUST NOT 猜测意图；**重复键 MUST 显式判 UNKNOWN/无效，MUST NOT 静默取最后一个**（safe_load 的默认取后行为在门禁语境是危险假定，手写须显式判重）；上述每条坏输入 MUST 有 pytest 用例断言非零退出 / 判定不能。**注**〔mlh-p5-parser-cleanup〕：「首行 `---` 无闭合（首块不成立）」**不属**本 Scenario 的坏——它归 absent（见上「首行 `---` 无闭合判 absent」Scenario），本 fail-closed 触发面仅限「首块已成立、块内容坏」

#### Scenario: 过渡期 live 未迁 producer 回退 inline〔mlh-p5 grill G3〕
- **WHEN** 迁移过渡期，某 live 报告的 producer 尚未迁移（frontmatter 无 `ship-gate` 键）、正文仍含独占一行 inline 锚
- **THEN** gate 对 live MUST **frontmatter 优先、无键则回退 inline** 读识别该锚（渐进迁移、中间态可用）；已迁 producer（frontmatter 有 `ship-gate` 键）MUST 只认 frontmatter、**不回退** inline（正文即刻免疫）；退役后 live MUST 只读 frontmatter

#### Scenario: frontmatter 只认文件首块，正文横线/锚提及不参与〔spec-review-amendment A2/D2〕
- **WHEN** 某 live 报告 frontmatter 无 ship-gate 结论字段，但正文中部有 markdown 横线 `---`（报告正文常含多处）包夹的块内写了 `ship-gate:` 与 `verify: PASS`，或正文任意行提及 `ship-gate.verify: PASS`
- **THEN** 手写解析器 MUST 只从文件第 1 行 `---`（去 BOM 后）起的唯一首块取键，正文中部 `---` 块与其中 `ship-gate:` 键 MUST NOT 被识别为 frontmatter → 该报告判无结论（design-approved 场景 → REFUSE_START）；MUST NOT 因正文 `---` 横线密布而误把正文块当 frontmatter（否则 B4/B5 在 YAML 层复活、fence-aware 失效）

#### Scenario: 坏 frontmatter 按坏法映射确定退出码〔spec-review-amendment A3/D3〕
- **WHEN** live 报告 frontmatter **有成立首块且有 ship-gate 键**但坏——分两类：① 值越域(`verify: MAYBE`)/重复键/坏 YAML 语法/类型不符/tab 缩进；② 纯缺该报告应有的字段（半成品，键区存在但无对应结论字段）
- **THEN** 第 ① 类 MUST 判 **UNKNOWN(exit 6)**（歧义须人裁，MUST NOT 判 STEP_IN_PROGRESS(exit 0) 致 LLM 反复写坏成重跑死循环）；第 ② 类 MUST 落既有无锚语义（spec-review-report → REFUSE_START(3)；verify/code-review report → STEP_IN_PROGRESS(0)）；**MUST NOT** 用「停下报告**或**判该步进行中」的退出码歧义并存；过渡期第 ① 类（有键但坏）MUST NOT 回退 inline（坏≠无键）。**「首块不成立（无闭合 `---`）」不入本 Scenario 分类**——它归 absent（无键缺席态）走无锚语义〔mlh-p5-parser-cleanup〕

#### Scenario: frontmatter 同字段重复键判 UNKNOWN〔spec-review-amendment D5〕
- **WHEN** 某报告 frontmatter 顶层 `ship-gate:` 键重复，或其下 `verify:`/`code_review:` 同名字段出现多次（键分散、键间夹注释、跨缩进等干扰形）
- **THEN** 解析器 MUST 在块边界内**枚举全部同名键计数**、判 UNKNOWN(exit 6)，MUST NOT「见到第二个即覆盖」静默取最后一个（这是 frontmatter 时代表达「冲突结论」的唯一触发面，取代 inline 的 PASS/FAIL 行级并存，是 load-bearing 单点，须专门 pytest 覆盖干扰形）

#### Scenario: 归档旧 inline 锚 dual-read 永久兼容〔mlh-p5 冷审 F2〕
- **WHEN** gate 判某 change 终态，其归档目录 `archive/<date>-{change}/verify-report.md` 仅含旧格式 inline 锚 `<!-- ship-gate: verify=PASS -->`（归档于 mlh-p5 迁移前，无 frontmatter 状态）
- **THEN** `archived_verify_state` MUST 经 inline 行级读正确识别 verify=PASS → 支持 SHIPPED 判定，MUST NOT 因归档无 frontmatter 而判无状态；此 inline 归档读半场对既有 88 归档报告 MUST 保持 100% 兼容、MUST NOT 回归（`_line_scoped_hits` 与 `ANCHOR_VERIFY_PASS`/`ANCHOR_VERIFY_FAIL` MUST 保留，T75 清理 MUST NOT 波及）

#### Scenario: 归档漏闭合 frontmatter 目标态 fail-safe〔mlh-p5-parser-cleanup Q2；adr/0011〕
- **WHEN** 目标态某归档 verify-report（producer 迁后 = frontmatter-only、正文**无 inline 锚**）被 LLM prepend frontmatter 时**漏写闭合 `---`**（首行 `---` 无闭合），经 `git show <base>:…` 读出
- **THEN** `parse_ship_gate_frontmatter` MUST 返回 absent（首块不成立）→ `archived_verify_state` 回退 inline dual-read → 正文**无 inline 锚可扫** → 判 `none` → **不 SHIPPED**（fail-safe，与 live 侧漏闭合 REFUSE_START/重跑**同向安全**）；MUST NOT 因回退 inline 而误判 pass。**安全论证 MUST 锚 producer 契约 + 目标态**〔adr/0011〕，MUST NOT 以迁移现状（现存归档多 `#` 打头、无一触发）评估——迁移现状非稳态。初版担心的「回退 inline 判假 pass」需「首行 `---` 无闭合 × 正文独占一行 inline PASS 锚」杂交形态，**无 producer 会产出**（未来 producer 不写 inline、旧 producer 首行 `#`），须手工伪造归档 = 显式越权（`adr/0008`，git 可审计）→ MUST 登记 `ship_gate.py`「已知不覆盖」；MUST 有 pytest 覆盖此目标态归档形态断言 `none`

#### Scenario: 迁移后新归档 frontmatter 被归档读识别〔mlh-p5 grill G2〕
- **WHEN** gate 判某 change 终态，其归档目录 `archive/<date>-{change}/verify-report.md` 是**迁移后**格式——frontmatter `ship-gate.verify: PASS`、正文无 inline 锚（`sdflow-done` 已迁 producer 归档所得）
- **THEN** `archived_verify_state` MUST 经**归档 frontmatter 读**（frontmatter 优先）识别 verify=PASS → 支持 SHIPPED，MUST NOT 因归档无 inline 锚而判无状态；归档读 **MUST NOT 只读 inline**——否则迁移后所有新归档 SHIPPED 判定回归〔grill G2 证伪 design 原「归档纯 inline」〕

#### Scenario: 前置产物缺失点名
- **WHEN** 某步产物缺失（如 code-review-report.md 不在）
- **THEN** gate 输出 next=对应 skill 与 missing 清单，编排按此推进；实现完成判据 MUST 以 **git 历史 checkpoint 任务标签为主锚**（plan 任务数 N 对 checkpoint 去重任务号集，齐 N 判完成〔grill-amendment〕；标签 MUST 按 change 命名空间归属过滤 `checkpoint(<change>:task<k>-`（裸 `checkpoint(task<k>-` 向后兼容），见下「命名空间隔离」Scenario 组〔ship-gate-hardening-2〕；**收集窗口 MUST 为含 superpowers-plan.md 首次提交自身的闭区间 `[sha, HEAD]`**——即 `git log <sha>..HEAD --no-merges` 加对 `<sha>` 自身 commit subject 的同规则解析；plan 与首个 task 锚同 commit（checkpoint `add -A` 携带未提交 plan 的合法盘面）时该 task MUST 计入，MUST NOT 漏数〔B1 修复，替换旧排他窗口表述〕；MUST NOT 全历史扫描——main 遗留标签会造成假齐 N〔spec-review-amendment 设计门拍板 Q2〕；plan 标题命中 0 → UNKNOWN；**重号 `### Task <n>:` 段 → UNKNOWN**〔ship-gate-hardening-2〕）、plan 复选框**按 `### Task <n>:` 段绑定**为辅（MUST NOT 全局全勾放行所有 task，见下「分段绑定」Scenario 组〔ship-gate-hardening-2〕），两通道皆不可判时 gate 判 UNKNOWN 停上抛，MUST NOT 猜测推进、MUST NOT 以 gitignored 的 SDD ledger 为判据

#### Scenario: plan 与首个 task 锚同 commit 不漏数〔B1〕
- **WHEN** superpowers-plan.md 的首次提交 commit 本身就是 `checkpoint(task1-<slug>)` 提交（plan 未单独提交、被首个 task 的 checkpoint `add -A` 一并携带入库）
- **THEN** gate 的完成任务号集 MUST 含 task1（窗口为含该 commit 自身的闭区间），plan 任务数 N 齐时 MUST NOT 输出 CONTINUE_IMPL 误报

#### Scenario: 陈旧 FAIL 不卡死 resume〔grill-amendment D9〕
- **WHEN** verify-report frontmatter 为 `verify: FAIL`，其提交之后存在触及 `openspec/` 之外路径的修复提交，用户重调 /sdflow-ship
- **THEN** gate 判该结论陈旧 → NEXT=重跑 sdflow-done（重验），MUST NOT 以陈旧 FAIL 退出卡死

#### Scenario: 干预后陈旧 PASS 不放行〔grill-amendment D9〕
- **WHEN** verify/code-review frontmatter 结论为 pass/PASS，但其后有人手改了 `openspec/` 之外的代码
- **THEN** gate 判受影响步结论陈旧 → 重跑该步，MUST NOT 让旧结论背书新代码直通 merge

#### Scenario: design-approved 不因实现提交失鲜〔spec-review-amendment 设计门拍板 Q1=B〕
- **WHEN** 设计门拍板（frontmatter `design_approved: true`）已落，实现期产生大量触及 `openspec/` 之外路径的提交（正常实现活动）
- **THEN** gate MUST 保持 design-approved 有效（新鲜度按结论分域：该结论仅当其后存在触及本 change **design 域监视集**路径的提交才失鲜须重审；监视集为固定四件套，其内 `tasks.md` 的豁免条件由下方「纯勾选框翻转不失鲜」Scenario 组定义），MUST NOT 因实现提交判其陈旧而 REFUSE_START（防实现期链自锁）

#### Scenario: 纯勾选框翻转不失鲜〔spec-review-amendment〕

design 域监视集 SHALL 保持固定四件套不变。豁免 SHALL 仅覆盖**已证对 gate 零信息量**的唯一改动形态——`tasks.md` 的完成度复选框状态翻转。

- **WHEN** 设计门拍板已落，其后某提交**落在 design 域监视集内的触及路径集恰为 `{tasks.md}`**（该提交同时触及监视集**之外**的路径——源码、`impl-reports/` 等——**不影响**豁免资格；checkpoint 走 `git add -A`，真实完成提交必然打包源码，按整 commit 文件列表求值会令豁免永不触发），且 `tasks.md` 前后两版在勾选框状态归一化后**逐行等值**
- **THEN** gate MUST NOT 因该提交判 design-approved 失鲜
- **AND** 归一化 MUST **锚定到 task-list 行首语法位置**（复用既有 `CHECKBOX_RE` 口径），且 MUST **fence-aware**（fenced code block 内的标记不参与归一化，复用 `_line_scoped_hits` 的 fence 口径）——无锚定的整行子串替换会把表格、行内反引号、引用块、散文字面量里的 `[ ]` / `[x]` 一并归一化，令豁免面远超「完成度复选框」集合
- **AND** 比较 MUST 按**行位置**对齐（如 `zip`），MUST NOT 使用基于 LCS / diff 算法的行匹配——LCS 下纯行重排会把「删除行与插入行逐字节相同」判成等值，令任务顺序 / 依赖的实质变更直通
- **AND** 判定 MUST 保真读取：MUST NOT 复用会 `.strip()` / `text=True` 的 helper（吞首尾空白、末尾换行、CRLF、非 UTF-8 字节，四者各自可造假等值）；两侧内容读取 MUST 显式检查 returncode，任一侧失败 ⇒ **保守判失鲜**（双侧失败会得 `"" == ""` ⇒ 判等值 ⇒ 放行真实设计改动）
- **AND** MUST NOT 做语义 diff、MUST NOT 因上述 fence 锚定要求而扩展成完整 markdown 解析（fence 开合是单 boolean toggle，非解析器）
- **AND** 判定 MUST 逐提交独立求值，MUST NOT 依赖工作树状态或任何跨提交状态（承既有「新鲜度 committed-only」口径）

#### Scenario: 勾选框以外的一切 tasks.md 改动照判失鲜〔spec-review-amendment〕

- **WHEN** 某提交触及 `tasks.md`，且满足下列任一：① 勾选框标记之外的任何字符变化（措辞 / 缩进 / 空白 / 格式化 / 错别字）；② 新增或删除 `### Task <n>:` 段；③ 行的重排或移动；④ fenced code block / 表格 / 行内反引号 / 散文中的 `[ ]` `[x]` 字面量变化；⑤ 同一提交还触及 `proposal.md` / `design.md` / `specs/` 中任一路径；⑥ 前版或后版取不到（该提交中**新建**、**删除**或 `git mv` **迁走** `tasks.md`）；⑦ 该路径的 git 变更状态不是普通内容修改（rename / copy / 类型变更 / mode 变更——`chmod` 或 regular↔symlink 可令 blob 内容完全相同而被误判为「纯勾选」）
- **THEN** gate MUST 照判 design-approved 失鲜 → `REFUSE_START`
- **AND** 情形 ⑥⑦ MUST **保守判失鲜**——MUST NOT 因取不到某一版、或因内容恰好相同而当作等值放行；资格判定 MUST 读取 git raw 状态位与 mode，MUST NOT 仅凭 `--name-only` 的路径列表

#### Scenario: 内容豁免与既有 subject 豁免的优先级〔spec-review-amendment〕

内容豁免独立于 subject，与既有 BR-7「变体照判失鲜」存在判定重叠（如 `checkpoint(impl-review)evil` + 纯勾选提交），SHALL 由下述优先级消歧：

- **WHEN** 某帧同时可被「精确式 `checkpoint(impl-review)` subject 豁免」与「内容豁免」评估
- **THEN** 判定顺序 MUST 为：① subject 精确匹配 ⇒ **无条件豁免该帧**（既有语义逐字不变，MUST 在读取任何 blob **之前**短路）；② 否则进入内容豁免评估——**任何** subject（含 `checkpoint(impl-review)evil` 等变体）均可凭严格的纯勾选内容判据获豁免；③ 二者皆不满足 ⇒ 失鲜
- **AND** BR-7 的既有表述 MUST 理解为「变体**不因 subject** 获豁免」，MUST NOT 理解为「变体必然失鲜」——后者与本 Scenario 冲突且无唯一解
- **AND** MUST 有覆盖 `精确 / 变体 / 空 / 普通 subject × 纯勾选 / 语义改动` 的真值表测试

#### Scenario: 豁免面 MUST NOT 由被监管方书写的声明决定〔spec-review-amendment〕

- **WHEN** 设计判据在「内容等值」与「被监管方可书写的声明」（commit subject、某文件是否存在、工作树状态）之间取舍
- **THEN** 豁免判据 MUST 取自被比较的内容本身；MUST NOT 以 `superpowers-plan.md` 的存在性、或除既有 `checkpoint(impl-review)` 精确式之外的任何 subject 形态，作为 `tasks.md` 豁免的判据
- **AND** 既有 `checkpoint(impl-review)` 精确式 subject 豁免（BR-7）MUST 逐字保留、不受本条影响

#### Scenario: 失鲜 REFUSE_START 须携带触发点与处置指引

- **WHEN** gate 因 design 域失鲜而 emit `REFUSE_START`
- **THEN** reason MUST 指明**触发失鲜的提交与文件**（至少一条 `<commit subject 或 sha>` + `<路径>`），并 MUST 携带**分类原因**（混合路径 / 非勾选框变化 / 前后版缺失 / 状态不合格，取值以判据实际分支为准）；MUST NOT 只输出「结论陈旧」而不指明触发点
- **AND** 机读输出 MUST 与人读文案**同源**（同一份触发点数据的两个视图），MUST NOT 各自拼装而允许单侧漂移
- **AND** 默认处置指引 MUST 只推荐**重跑设计门**一条；`checkpoint(impl-review)` **MUST NOT** 出现在默认处置指引中〔spec-review-amendment 设计门拍板；impl-review-fix：本条原文与 ADR-2 改写后的口径冲突，系 spec-review 期改写 ADR-2 未扫残留引用所致，此处对齐〕——两条理由：① 它是**显式越权口**（让任意四件套语义改动不经二次批准随档 ship，`ship_gate.py` 头注释已声明为「已知不覆盖」），写进常规建议会把例外变成默认工作流；② 🔴 **它对撞门者无效**——豁免逐提交求值，已经触发失鲜的那个提交**不会**因为后补一个 `checkpoint(impl-review)` 提交而被追溯赦免，写进指引等于教人做一件不起作用的事。其正确定位是**事前、受控的 impl-review 提交协议**（用在会触发失鲜的那个提交自身上），只在该协议文档中说明
- **AND** 该指引 MUST 为纯诊断输出，MUST NOT 改变退出码或失鲜判据本身

#### Scenario: 阶段三合法尾流修订不失鲜〔B2〕
- **WHEN** 设计门拍板已落，其后 sdflow-code-review 按工作流对 design.md/tasks.md 打 `[impl-review-fix]` 补丁并以 commit subject 闭合字面前缀 `checkpoint(impl-review)`（含右括号）提交（触及四件套路径）
- **THEN** gate 的 design 域新鲜度判定 MUST 豁免该类提交（不判拍板失鲜、不 REFUSE_START）；豁免面 MUST 仅限**精确式 `subject == "checkpoint(impl-review)" 或 subject 以 "checkpoint(impl-review):" 起始`**〔spec-review-amendment BR-7：裸闭合前缀 startswith 仍收 `checkpoint(impl-review)evil` 尾串垃圾，须精确式〕——`checkpoint(impl-review-fix)`/`checkpoint(impl-reviewX)`/`checkpoint(impl-review)evil` 等从不由 checkpoint 脚本合法产生的变体 MUST NOT 豁免（照判失鲜）；其他 subject 触及四件套照判失鲜（实现改设计须重审的既有语义不变）；豁免 MUST NOT 分析改动内容（只认 subject 不认 hunk），由此「经豁免的语义级四件套改动不经二次批准即随档 ship」属**已登记的接受取舍**〔grill Q2〕；伪造/手工 subject 绕过豁免属显式越权同权级（git 留痕可审计），MUST 在脚本头注释「已知不覆盖」中声明

#### Scenario: 未提交报告视为 fresh〔spec-review-amendment 设计门拍板 Q3=A〕
- **WHEN** 某报告文件存在且 frontmatter 含结论字段，但从未 git 提交（`git log -1 -- <path>` 空输出）
- **THEN** gate MUST 视其为 fresh 并在 JSON 注明 `freshness=uncommitted`（人机同权：手写产物合法），MUST NOT 因无提交记录而判进行中或报错

#### Scenario: 无结论产物 = 步进行中〔grill-amendment D9；mlh-p5 改 frontmatter〕
- **WHEN** 某 live 报告文件存在但 frontmatter 不含任何 ship-gate 结论字段（如中断的半成品）
- **THEN** gate 判该步进行中 → NEXT=重跑该步，MUST NOT 当作已完成

#### Scenario: 暂停后重调即续、人机同权〔grill-amendment D9〕
- **WHEN** 链中途停止（任意原因），期间用户手动完成了某步（如手跑 /sdflow-code-review 产出报告），之后重调 /sdflow-ship
- **THEN** gate 仅凭盘面推进（不辨产者），从下一缺口继续；实现中断场景 gate 输出已完成任务号集供 SDD 勿重派；ship MUST NOT 依赖任何跨步内存状态

#### Scenario: 条件步按 TG 判定
- **WHEN** change 的 proposal 未标注 TG-02（非嵌入式）
- **THEN** gate 对 step 5.5 输出 SKIP 并记录理由；命中 TG-02 时高风险/TG-18 细判归模型（每步内部判断，prose 允许域）

#### Scenario: 归档后识别 SHIPPED 终态〔B3 + D3 硬化〕
- **WHEN** change 的 active 目录 `openspec/changes/{change}/` 不存在，但归档目录 `archive/<YYYY-MM-DD>-{change}/`（发现经**纯 git 域** `git ls-tree HEAD ∪ ls-tree <base>` 列举 + `re.escape(change)` 套日期前缀 fullmatch，**MUST NOT 用文件系统 glob**〔H2/BR-4〕）**已存在于 base 树** 且该归档目录内 `verify-report.md` **含 verify=PASS 结论（frontmatter `verify: PASS` 或归档旧 inline 锚 `<!-- ship-gate: verify=PASS -->`，dual-read）**〔H1/BR-2；mlh-p5 dual-read〕
- **THEN** gate MUST 输出 SHIPPED（exit 0），MUST NOT 按 active 路径找不到 spec-review-report.md 而误报「未过设计门」；该短路判定 MUST 位于设计门 pre-flight 与新鲜度检查之前；终态判据 MUST 为 change 域可达性（`git ls-tree <base>`）而非全局 `branch_state()`〔grill-amendment〕；发现 MUST 与判据同域（纯 git，工作树无关）——MUST NOT 用工作树 glob（否则跨分支查已并 change 会假 REFUSE、未跟踪垃圾目录会假 RUN_VERIFY）〔H2/BR-4〕；SHIPPED MUST 追读 archived verify=PASS 结论——MUST NOT 仅凭目录存在性放行（手工空壳归档目录不得假 SHIPPED）〔H1/BR-2〕；`--change` MUST 校验为 slug 或 `re.escape` 后匹配，MUST NOT 把用户输入当 glob 元字符〔H5/HRTG-4〕；base 无 main/master → UNKNOWN，detached HEAD 对 D3 判定无关（凭 base 树可达仍可 SHIPPED）〔H3/H4〕；active 存在时 final SHIPPED 的 archived 谓词 MUST 收紧，MUST NOT 被旧/同名 archive 触发〔H1/HRTG-1〕

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

#### Scenario: 归档 verify 描述性提及不触发假 SHIPPED〔gate-anchor-line-scoped B4·SHIPPED 路径〕
- **WHEN** 归档目录的 `verify-report.md`（经 `git show <base>:…` 读出）正文**描述性提及** `<!-- ship-gate: verify=PASS -->`（内联句 / 代码块内文档示例）但**无独占一行的真 PASS 锚**、且 frontmatter 亦无 `verify: PASS`
- **THEN** `archived_verify_state` MUST 判其 verify 态为 `none`（非 `pass`），使归档终态短路 MUST NOT 输出假 SHIPPED——空壳 / 未验 / 仅描述性提及的归档目录 MUST 落 fail-safe（不 SHIPPED，请人工核验）；此归档 inline 判据 MUST 为行级整行等值 + 忽略 fenced code block（`_line_scoped_hits` 归档读半场），MUST NOT 保留裸子串路径

#### Scenario: 归档未闭合 fence 隔断互斥锚对不判假通过〔gate-anchor-line-scoped OV-2·设计门 Q1=A；mlh-p5 归档侧〕
- **WHEN** 某**归档** verify-report.md 的**互斥 inline 锚对**（verify `PASS`/`FAIL`）中正锚独占一行在 fenced code block 外、负锚独占一行落在**未闭合**（无配对收尾 ```）的 fence 内被吞
- **THEN** 归档读行级锚检测核心 MUST 回报**未闭合信号**，`archived_verify_state` 遇未闭合信号 MUST **保守判定**（`none` 不 SHIPPED），MUST NOT 因只见正锚而判 pass（否则从旧裸子串 conflict 语义回归为危险假阳）；此约束针对**归档读半场**（live 报告已迁 frontmatter，其冲突由 frontmatter 同字段重复键 → fail-closed 处理，不再经 fence 判据）

#### Scenario: TG-02 条件步检测用声明式匹配非裸子串〔gate-anchor-line-scoped ADR-6·dogfood〕
- **WHEN** 某 change 的 proposal **描述性提及** `TG-02`（反引号代码引用 / 否定句 `TG-01/02/03 均不命中` / 散文讨论），但**未以声明式头注** `〔TG-02：…〕` 标注该触发（即该 change 非嵌入式、不该跑 embedded-test-sop）
- **THEN** gate 的 TG-02 条件步检测（`tg02_hit`）MUST 判**未命中** → step 5.5 输出 SKIP，MUST NOT 因子串命中正文对 TG-02 的**文档性提及/示例声明串**而误判 RUN_SOP（嵌入式 SOP）；检测 MUST 限定在 proposal **头部声明区**（文件开头→首个 `## ` 标题前）找 `〔TG-02`〔A3，dogfood 二轮：整体子串含加冒号仍被正文示例串假阳〕，真嵌入式 change 的头部 `〔TG-02：…〕` 声明仍 MUST 正确命中 → RUN_SOP；头部未用括号声明的（非常规）embedded proposal 漏检为安全侧假阴（ff 强制头注括号格式故实际不发生），记 Non-Goals

