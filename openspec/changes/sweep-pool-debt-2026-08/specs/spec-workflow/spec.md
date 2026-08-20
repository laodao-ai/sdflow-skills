## ADDED Requirements

### Requirement: 阶段三编排台账确定性（ship_gate·内容锚）

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
- **THEN** gate 输出 next=对应 skill 与 missing 清单，编排按此推进；实现完成判据 MUST 以 **git 历史 checkpoint 任务标签为主锚**（plan 任务数 N 对 checkpoint 去重任务号集，齐 N 判完成〔grill-amendment〕；标签 MUST 按 change 命名空间归属过滤 `checkpoint(<change>:task<k>-`（裸 `checkpoint(task<k>-` 向后兼容），见下「命名空间隔离」Scenario 组〔ship-gate-hardening-2〕；**收集窗口 MUST 为含计划文件（`tickets.md`）首次提交自身的闭区间 `[sha, HEAD]`**——即 `git log <sha>..HEAD --no-merges` 加对 `<sha>` 自身 commit subject 的同规则解析；plan 与首个 task 锚同 commit（checkpoint `add -A` 携带未提交 plan 的合法盘面）时该 task MUST 计入，MUST NOT 漏数〔B1 修复，替换旧排他窗口表述〕；MUST NOT 全历史扫描——main 遗留标签会造成假齐 N〔spec-review-amendment 设计门拍板 Q2〕；plan 标题命中 0 → UNKNOWN；**重号 `### Task <n>:` 段 → UNKNOWN**〔ship-gate-hardening-2〕）、plan 复选框**按 `### Task <n>:` 段绑定**为辅（MUST NOT 全局全勾放行所有 task，见下「分段绑定」Scenario 组〔ship-gate-hardening-2〕），两通道皆不可判时 gate 判 UNKNOWN 停上抛，MUST NOT 猜测推进、MUST NOT 以 gitignored 的 SDD ledger 为判据

#### Scenario: plan 与首个 task 锚同 commit 不漏数〔B1〕
- **WHEN** `tickets.md` 的首次提交 commit 本身就是 `checkpoint(task1-<slug>)` 提交（plan 未单独提交、被首个 task 的 checkpoint `add -A` 一并携带入库）
- **THEN** gate 的完成任务号集 MUST 含 task1（窗口为含该 commit 自身的闭区间），plan 任务数 N 齐时 MUST NOT 输出 CONTINUE_IMPL 误报

#### Scenario: 陈旧 FAIL 不卡死 resume〔grill-amendment D9〕
- **WHEN** verify-report frontmatter 为 `verify: FAIL`，其提交之后存在触及 `openspec/` 之外路径的修复提交，用户重调 /sdflow-ship
- **THEN** gate 判该结论陈旧 → NEXT=重跑 sdflow-done（重验），MUST NOT 以陈旧 FAIL 退出卡死

#### Scenario: 干预后陈旧 PASS 不放行〔grill-amendment D9〕
- **WHEN** verify/code-review frontmatter 结论为 pass/PASS，但其后有人手改了 `openspec/` 之外的代码
- **THEN** gate 判受影响步结论陈旧 → 重跑该步，MUST NOT 让旧结论背书新代码直通 merge

#### Scenario: design-approved 不因实现提交失鲜〔spec-review-amendment 设计门拍板 Q1=B〕
- **WHEN** 设计门拍板（frontmatter `design_approved: true`）已落，实现期产生大量触及 `openspec/` 之外路径的提交（正常实现活动）
- **THEN** gate MUST 保持 design-approved 有效（新鲜度按结论分域：该结论仅当其后存在触及本 change **design 域监视集**路径的提交才失鲜须重审；监视集为 `proposal.md`/`design.md`/`specs/`——`tasks.md` 不在监视集内，其任何改动不触 design 域失鲜〔sweep-pool-debt D2〕），MUST NOT 因实现提交判其陈旧而 REFUSE_START（防实现期链自锁）

#### Scenario: tasks.md 改动不触 design 域失鲜〔sweep-pool-debt D2〕

design 域监视集 SHALL 为 `proposal.md` / `design.md` / `specs/`——`tasks.md` 不在集内。

- **WHEN** 设计门拍板已落，其后提交改动 `tasks.md`（勾选框翻转或任何实质内容改动，无论该提交是否同时触及监视集之外的路径）而不触及 `proposal.md` / `design.md` / `specs/` 中任一路径
- **THEN** gate MUST 判 design 域 fresh，MUST NOT 因 `tasks.md` 改动判失鲜或 REFUSE_START
- **AND** 同一提交触及 `proposal.md` / `design.md` / `specs/` 中任一路径时 MUST 照判失鲜（指纹不等即成立）
- **AND** 勾选框豁免的全部内容判据（标记归一化 / 行对齐比较 / 保真读取 / fence 锚定）随监视集调整**整体退役并物理删除**，MUST NOT 留 test-referenced 死代码；`tasks.md` 记录诚实性由收尾对账与代码审 scope 审计兜底，不再由本域承担

#### Scenario: 失鲜 REFUSE_START 须携带触发点与处置指引

- **WHEN** gate 因 design 域失鲜而 emit `REFUSE_START`
- **THEN** reason MUST 指明**触发失鲜的提交与文件**（至少一条 `<commit subject 或 sha>` + `<路径>`），并 MUST 携带**分类原因**（取值以判据实际分支为准，如：监视路径指纹差异 / 路径仅一侧存在 / 锚缺失 / 锚非法）；MUST NOT 只输出「结论陈旧」而不指明触发点
- **AND** 机读输出 MUST 与人读文案**同源**（同一份触发点数据的两个视图），MUST NOT 各自拼装而允许单侧漂移
- **AND** 默认处置指引 MUST 只推荐**重跑设计门**一条；**重锚脚本 MUST NOT 出现在默认处置指引中**〔sweep-pool-debt D9，承接原 `checkpoint(impl-review)` 同款约束〕——它是**显式越权口**（可让任意监视集语义改动不经二次批准随档 ship，脚本头注释「已知不覆盖」继续登记），写进常规失鲜的处置建议会把受控协议的组成步骤变成撞门者的自赦通道；其正确定位是 impl-review 提交协议的组成步骤（见下「阶段三合法尾流修订」Scenario），只在该协议文档中说明
- **AND** 该指引 MUST 为纯诊断输出，MUST NOT 改变退出码或失鲜判据本身

#### Scenario: 阶段三合法尾流修订经重锚协议不失鲜〔B2；sweep-pool-debt D9 改造〕
- **WHEN** 设计门拍板已落，其后 sdflow-code-review 按工作流对监视集文件（如 design.md）打 `[impl-review-fix]` 补丁提交（subject 仍约定为 `checkpoint(impl-review)`，供人读审计留痕），随后按协议跑写锚脚本刷新 spec-review-report 的锚字段（不改结论字段）并落盘提交
- **THEN** gate MUST 判 design 域 fresh（重锚后指纹等值自然成立）；gate 端 MUST NOT 保留任何 subject 豁免或内容豁免通道——失鲜判定 SHALL 为纯指纹等值、无逐提交豁免求值（原 BR-7 精确式 subject 豁免、变体真值表、内容/subject 豁免优先级消歧随之**整体退役并物理删除**）
- **AND** 修订提交后**未跑重锚** ⇒ 指纹不等 → REFUSE_START（fail-closed 方向安全：假阴误停非假阳放行），诊断点名差异路径与提交，补跑重锚即恢复
- **AND** 「手跑重锚脚本绕过二次批准」属显式越权同权级（锚字段变更随提交 git 留痕可审计，adr/0008 防御纵深立场不变），MUST 在写锚脚本头注释「已知不覆盖」中声明；MUST NOT 为此在 gate 端新增机械拦截

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
- **WHEN** 当前 change A 的 plan 号集 = {1, 2}，同一分支窗口内只有 A 的 `checkpoint(A:task1-…)`（task2 未完成），另一 change B 的 `checkpoint(B:task2-…)` 落进 A 的窗口（B 的号恰是 A 缺的 task2；触发本需 stacking——feat/A 上再建 change B；FF-0 三分支判定后该动作需人显式 ack 才放行，但守卫可绕过（ack / fail-open / 手工 git），故隔离仍必要，见 adr/0008）
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

## MODIFIED Requirements

### Requirement: 失鲜判定 MUST 直接比较内容，MUST NOT 从 git 管道推断路径变更

机械层 MUST NOT 使用下列任一方式判定「被审内容是否改变」：`git log --name-only`、`git diff-tree -m`、`git diff-tree --cc`、负向 pathspec、整棵树的 sha。这些方式已累计产出实测复现的缺陷（详见 `openspec/adr/0026`），且互为解药兼病灶、可被外部 config/env 翻转。

机械层 MUST 改为直接比较内容，且锚侧内容由报告 frontmatter 记录的**内容锚**承载〔sweep-pool-debt D3〕——`reviewed_manifest`（监视域 `path → (mode, type, oid)` 规范记录清单，按**原始 path 字节序**排序）+ `reviewed_sha`（manifest 规范字节流的 sha256，64 位 hex），比较不再解析任何 commit。**manifest 规范编码 MUST 字节保真**〔spec-review-amendment〕：记录取 `ls-tree -z` 原始 path 字节（git 合法路径可含 Tab / 换行 / 非 UTF-8 字节），frontmatter 存储用单行字节保真编码（如 base64 规范字节流），digest 对解码后原始字节计算；MUST NOT 依赖 YAML 文本行清单的转义/归一化承载 manifest（编码欠定义 ⇒ 同内容不同 digest 的假失鲜，或异路径折叠为同记录的假等值）；互证 = 解码字节流的 sha256 == `reviewed_sha`：

- **design 域** MUST 以 HEAD 侧重算的监视集 manifest 求 digest，与锚 digest 等值比较；不等即失鲜。监视集 SHALL 为 change 目录内 `proposal.md` / `design.md` / `specs/`（`tasks.md` 不在集内〔D2〕）。诊断 MUST 以锚 manifest 与 HEAD 侧枚举的差集点名路径（配 `git log -1 -- <路径>` 点名提交）。HEAD 侧枚举 MUST 完整覆盖监视集——「锚有而 HEAD 已删」「HEAD 新增」均体现为 manifest 差异，两方向均判失鲜，MUST NOT fail-open。
- **code 域** MUST 比较 `git ls-tree` 顶层条目映射（排除 `openspec` 条目后）的同构内容锚——锚值同为 manifest digest，gate MUST 以 HEAD 侧重算 digest 与锚等值比较，MUST NOT 将锚值作为 git ref 解析（与 design 域共用同一指纹实现）〔spec-review-amendment：现实现 code 分支以锚 sha 取 `ls_tree_map`，迁移 MUST 覆盖该分支，否则 verify/code-review 锚检查在新格式下恒 UNKNOWN〕。
- 失鲜判定 SHALL 为纯指纹等值，MUST NOT 保留任何按提交范围求值的豁免通道（合法尾流修订走 producer 重锚协议〔D9〕）。

#### Scenario: 实现期不得让设计门失鲜

- **WHEN** 设计门拍板后进入实现期，提交改动源码文件、把 `tickets.md` 验收复选框勾成 `- [x]`、或改动 `tasks.md` 的任何内容
- **THEN** gate MUST 判 design 域 fresh——源码、`tickets.md` 与 `tasks.md` 均不在 design 域监视集内
- **AND** **监视集是承重的**：任何令实现期提交使设计门失鲜的实现（如把整棵树纳入指纹）MUST 判为不合格

#### Scenario: `specs/` 子树的新增、删除与 rename 均判失鲜

- **WHEN** 锚之后在 `specs/` 下新增文件、删除文件、或 rename 文件（后者内容可完全不变）
- **THEN** gate MUST 判失鲜——三者均使监视集 manifest（含 path 维）与锚不等
- **AND** MUST 各有用例，且 MUST 经 `is_stale` 公共入口求值
- **AND** 某路径只在一侧存在 MUST 判失鲜，MUST NOT 混作「读取失败」处理——二者是不同的判定

#### Scenario: `tasks.md` 纯复选框翻转不失鲜（任何阶段）

- **WHEN** `tasks.md` 的复选框状态被翻转（不触及 `proposal.md` / `design.md` / `specs/`）
- **THEN** gate MUST 判 design 域 fresh，且与当前处于哪个阶段无关——`tasks.md` 不在监视集内，本结论不依赖任何内容判据〔sweep-pool-debt D2〕
- **AND** 原勾选框内容豁免判据（标记归一化 / 行位置对齐 / 保真读取 / fence 锚定）随监视集调整**整体退役并物理删除**，MUST NOT 留死代码

#### Scenario: 控制字符与非 UTF-8 路径下 manifest 稳定〔spec-review-amendment〕

- **WHEN** 监视域内存在含 Tab / 换行 / 非 UTF-8 字节的路径（git 合法路径域），或监视文件内容含 CRLF
- **THEN** 写锚与验锚两侧对同一盘面 MUST 得到字节相同的 manifest 与相同 digest（round-trip 无损）；不同路径 MUST NOT 折叠为同一 manifest 记录
- **AND** MUST 有 round-trip 用例覆盖 Tab、换行、非 UTF-8 路径与 CRLF 内容

#### Scenario: 合并把已批准产物换回锚前旧内容

- **WHEN** 锚记录之后的一次合并，使某监视文件在 HEAD 上的内容变回锚**之前**某祖先版本（该内容不由锚后任何提交引入，故任何逐提交枚举都看不到它）
- **THEN** gate MUST 判失鲜——指纹比较不依赖提交拓扑，HEAD 重算 digest 与锚不等即成立
- **AND** MUST 有用例，且 MUST 经 `is_stale` 公共入口求值

#### Scenario: 代码审后的源码改动 MUST 被 code 域捕获

- **WHEN** 代码审出具结论之后，源码经由 merge 提交中 resolve 引入改动，或经 `git mv` 从顶层迁入 `openspec/`
- **THEN** gate MUST 判 code 域失鲜——两者均使非 `openspec` 顶层条目集合改变
- **AND** 二者 MUST **各有**用例并附变异证明——它们是 code 域改用顶层条目比较后**唯一的正面收益证明**

#### Scenario: `openspec/` 内的记账不得让 code 域失鲜

- **WHEN** 代码审通过后，正常收尾流程写入 `verify-report.md`、或 archive 把 change 目录移入 `openspec/changes/archive/`——即改动全部落在 `openspec/` 之内
- **THEN** gate MUST 判 code 域 fresh
- **AND** 该域的比较粒度 MUST 能排除 `openspec/`：整棵树的 sha 比较 **MUST NOT** 被采用——它在上述正常流程的第一步即假阳（已实测）

### Requirement: 评审锚 MUST 由 producer 记录，MUST NOT 从提交历史反推

评审结论的锚 MUST 是评审时由**写锚脚本权威计算**并写入报告 frontmatter 的显式内容锚（`reviewed_sha`：监视域 manifest 的 sha256，64 位 hex；`reviewed_manifest`：manifest 行清单，与 digest 同批写入、密码学互锁）〔sweep-pool-debt D3/D4〕，MUST NOT 由「最后一次触碰报告文件路径的提交」之类的反推方式得出，MUST NOT 由 LLM 手写锚值。

反推式锚可被任何后续触碰该文件的提交无声前移，从而把锚前的未审改动埋在判定范围之外——该提交无需修改任何结论字段，在 `git log -p` 中与评审结论毫无关联，其隐蔽性不被「篡改结论字段留痕可审计」这一既有残余面覆盖。

锚的语义是「**被批准 / 被放行的那个盘面的内容**」，而非「写报告的时刻」。

#### Scenario: 锚 MUST 指向被放行的提交，而非写报告的时刻

- **WHEN** 某评审步在出具结论的同一轮内还修改了它所审查的对象（如代码审的自动修复）
- **THEN** producer MUST 先提交该修改、再跑写锚脚本（脚本从已提交的 HEAD 盘面计算锚），最后单独提交报告；MUST NOT 让锚绑定不含该修改的更早盘面
- **AND** 否则报告落盘后判定立即失鲜（锚不含刚提交的修改），使该评审步每轮自锁
- **AND** MUST 有用例覆盖「该评审步的修复非空」这一情形

#### Scenario: 结论落盘前对被审对象的追加修订 MUST 先单独提交

- **WHEN** 评审结论已产出、但在写入结论字段与锚之前，被审对象又被实质修订（如人读评审报告后要求修改设计文档）
- **THEN** 该修订 MUST 先单独提交，之后才跑写锚脚本并写入结论字段
- **AND** MUST NOT 让该修订与结论字段的写入落进同一次提交——那会使锚绑定不含该修订的盘面，结论落盘后首次判定即失鲜，形成自锁
- **AND** MUST 有用例覆盖此路径，且其变异证明为「令锚绑定修订前的盘面 ⇒ 判定失鲜」

#### Scenario: 无关的报告排版提交不得移动锚

- **WHEN** 评审通过后，先有提交引入未经审查的监视域改动，再有一个与之无关的提交仅修改报告文件的排版（如补一个换行），且不改动任何结论字段与锚字段
- **THEN** gate MUST 仍判失鲜——锚为脚本记录值，不因报告文件被触碰而前移

#### Scenario: 锚值 MUST 由脚本计算，MUST NOT 手写〔sweep-pool-debt D4〕

- **WHEN** producer（任一评审 SKILL）需要把锚写进报告 frontmatter
- **THEN** MUST 调用写锚脚本完成计算与写入（原子替换），MUST NOT 让 LLM 手抄/手写锚值
- **AND** 写锚脚本与 gate 验锚 MUST 共用同一指纹实现（物理同源），MUST NOT 各自实现口径
- **AND** **诚实边界**〔spec-review-amendment R2 收窄〕：脚本保证锚**值**的正确性（消除手抄错值与不一致篡改），并机械拦截「监视集有未提交改动时写锚」（见「写锚时监视集脏 MUST 拒写」Scenario）；**「批准动作本身是否已发生」**仍由 producer 自报（无确定性信号），MUST NOT 将本条表述为完整时机的机械保证

#### Scenario: 锚缺失或非法时 fail-closed

- **WHEN** 报告 frontmatter 缺 `reviewed_sha`、其取值不是 64 位 sha256 hex、缺 `reviewed_manifest`、或 manifest 规范字节流的 sha256 与 `reviewed_sha` 不互证
- **THEN** gate MUST 判 `UNKNOWN`（exit 6），MUST NOT 回退到任何反推式锚、MUST NOT 判 fresh
- **AND** 格式与互证校验 MUST 为纯文本层（无需 git 调用），供 live 读与归档文本读共用
- **AND** reader 契约 MUST 与 producer 同批落地：只落 producer 会使新锚永不被读取，只落 reader 会使存量报告全部 fail-closed
- **AND** 存量旧格式锚（40 位 commit OID）的 **live** 报告 MUST 要求重跑写锚（结论字段随对应门的既有流程处置），MUST NOT 为兼容而实现双读；归档报告不可变、无法重跑，其处置见下「归档报告旧 40-hex 锚不阻断 SHIPPED」Scenario〔spec-review-amendment〕

#### Scenario: 归档报告旧 40-hex 锚不阻断 SHIPPED〔spec-review-amendment〕

- **WHEN** 某归档目录 `verify-report.md` frontmatter 含 `verify: PASS` 且携旧格式 `reviewed_sha`（40 位 commit OID，归档于本迁移前；归档不可变，无法重锚）
- **THEN** `archived_verify_state` MUST 识别 `verify: PASS` → 支持 SHIPPED；归档读点对 `reviewed_sha` / `reviewed_manifest` 的值格式与互证 MUST NOT 参与「坏 frontmatter」判定（归档只消费 `verify` 结论）——MUST NOT 因旧锚字段令存量归档报告（现 34 份携 40-hex 锚）整体判 `none` 而致 SHIPPED 大面积回归
- **AND** live 读点不受本条影响：live 的 64-hex + 互证校验照常 fail-closed
- **AND** 实现形态 SHALL 为**校验分层**〔spec-review-amendment R1〕：解析层对 `reviewed_sha` 只做语法校验（40 或 64 位小写 hex）、`reviewed_manifest` 做单行 base64 语法校验，解析核 MUST NOT 为归档 fork 出模式参数（承 A4 共核纪律）；64-hex 与 manifest 互证的语义强制 MUST 只落在 live 锚读取层
- **AND** MUST 有归档 fixture 用例（40-hex `reviewed_sha` + `verify: PASS` → SHIPPED），其变异证明 = 令归档读点也执行 64-hex 值校验 ⇒ 用例变红

#### Scenario: 结论字段与锚 MUST 原子写入

- **WHEN** producer 写入评审结论字段（如 `design_approved`）与锚字段
- **THEN** 二者 MUST 在同一次文件写入中落盘——写锚脚本 MUST 支持同批写入结论字段，producer 以一次脚本调用同时落结论+锚（单次原子替换）；MUST NOT 先手写结论字段、再调脚本补锚〔spec-review-amendment：脚本只写锚字段的形态与本条正面冲突〕
- **AND** 否则中断可产生「结论字段已在、锚缺失」的中间态：该态下结论字段判定通过、锚读取却 fail-closed，撞门者得不到「缺的是哪个字段」的指引

### Requirement: 内容比较 MUST 区分读失败与内容为空

枚举监视集或读取判定输入时，MUST 显式判定 git 调用的返回码，MUST NOT 让失败的调用因返回空结果而被当作合法的空内容参与比较。内容锚方案下锚侧不再发起 git 调用〔sweep-pool-debt D3〕，本要求约束 **HEAD 侧枚举**与 gate 其余读点。

#### Scenario: 读取失败保守判失鲜

- **WHEN** HEAD 侧枚举监视集（如 `git ls-tree`）以非零退出返回（仓损坏、权限不足等）
- **THEN** gate MUST 保守判失鲜或 `UNKNOWN`，MUST NOT 以空 manifest 求 digest 参与比较——空集的 digest 是一个合法值，失败折叠为空集会与「真空监视域」的锚假等值（fail-open）
- **AND** MUST 有用例，且 MUST 附变异证明——删除该 returncode 判定 ⇒ 用例变红

#### Scenario: 存在性判定 MUST 由能区分「缺失」与「失败」的原语承担

- **WHEN** 需要判断某监视路径在 HEAD 侧是否存在
- **THEN** MUST 使用「路径不存在时正常退出并返回空结果」的枚举原语，使「缺失」与「调用失败」在返回码上判然二分
- **AND** 监视清单内的文件在 HEAD 侧被删除或迁出监视集 ⇒ 体现为 manifest 差异判失鲜，诊断 MUST NOT 呈现为读取失败
- **AND** MUST 有用例覆盖该判别

#### Scenario: 写锚时空监视域 MUST 拒绝落锚

- **WHEN** 写锚脚本枚举监视域得到空集（如 change 目录缺 `proposal.md` / `design.md`）或枚举调用失败
- **THEN** 脚本 MUST fail-loud 拒绝写入，MUST NOT 落一个空集 digest 锚——空集锚会使后续「监视域从无到有」的变化被误判，且掩盖枚举失败

#### Scenario: 写锚时监视集脏 MUST 拒写〔spec-review-amendment R2〕

- **WHEN** 写锚脚本运行时监视集路径存在未提交改动（`git status --porcelain -- <监视集>` 非空）
- **THEN** 脚本 MUST fail-loud 拒写并提示「先提交修订再写锚」——锚取自 HEAD，脏树写锚 = 锚绑不含在场修订的盘面，结论落盘后首次判定即失鲜自锁（原「二次修订 MUST 先单独落盘」书面纪律由此收进机械层）
- **AND** 逃生口（如 `--allow-dirty`）若提供 MUST 为显式越权留痕形态，MUST NOT 成为默认路径
- **AND** MUST 有用例：脏监视集 → 非零退出不写入；干净树 → 正常写入

### Requirement: gate 的 git 调用失败 MUST 落在退出码契约集内，且不受外部态影响

`ship_gate.py` 对外承诺的退出码集为 `{0, 3, 4, 5, 6}`。调用 git 时的任何环境级失败 MUST 被映射进该集合，MUST NOT 以未捕获异常逸出使退出码变成解释器默认值。

git 子进程 MUST 中和一切能改变判定输入的外部可控态：配置面经 `-c` 显式覆盖，环境面清理 `GIT_*` 环境变量。MUST NOT 以「当前实现碰巧没用到那些开关」作为免于中和的理由。

#### Scenario: git 不可用或不可执行

- **WHEN** `git` 不在 `PATH` 上、不可执行、或为无效可执行格式，`subprocess.run` 抛出 `OSError` 家族异常（含 `FileNotFoundError`、`PermissionError`）
- **THEN** gate MUST 捕获并映射为 `UNKNOWN`（exit 6），输出可读诊断；MUST NOT 让异常冒泡产生 traceback 与 exit 1
- **AND** 该捕获 MUST 覆盖**全部** git 调用 helper，且 MUST 对每个 helper **各有**验证——`main()` 首次 git 调用失败即退出，单一端到端用例只能覆盖其中一个

#### Scenario: git 调用挂起

- **WHEN** 某次 git 调用长时间不返回
- **THEN** 该调用 MUST 有超时上界，超时 MUST 映射为 `UNKNOWN`（exit 6）
- **AND** 超时值 MUST 对本仓正常规模的本地元数据查询留足余量

#### Scenario: 失败原因 MUST 可区分且可行动

- **WHEN** gate 因任一环境级失败判 `UNKNOWN`
- **THEN** 诊断 MUST 区分「git 不可用」「调用超时」「锚缺失」「锚非法」「读取失败」五类，各给出对应的补救指引——「锚非法」（`reviewed_sha` 非 64 位 sha256 hex、或 manifest 与 digest 不互证；语法与一致性级、无需 git 调用即可判）的补救 = 重跑写锚脚本〔sweep-pool-debt D3/D4〕；原「锚指向对象不存在或非 commit」类随内容锚**整体退役**（锚不再解析任何 git 对象），其判定分支与诊断文案 MUST 物理删除，MUST NOT 留死分支
- **AND** MUST NOT 以单一通用文案覆盖全部类别——各类的补救动作互不相同，而 `UNKNOWN` 在上游链序中的处置是「停并转述该诊断」

#### Scenario: 环境变量不得改变判定输入

- **WHEN** 调用方环境中存在影响 git 路径匹配或 diff 行为的变量（如 `GIT_ICASE_PATHSPECS`）
- **THEN** gate 的 git 子进程 MUST 不继承该类变量，判定结果 MUST 与该变量是否设置无关
- **AND** 环境清理 MUST 以排除法实现（剔除 `GIT_` 前缀键），MUST NOT 以白名单方式只保留少数变量——后者会在部分平台上漏掉进程创建所必需的系统变量
- **AND** MUST 有用例：在设置该类变量的环境下判定结论与未设置时一致，且非 `GIT_*` 的环境变量原样透传

### Requirement: sdflow-code-review 自动修复后的复审边界与硬上限

`sdflow-code-review` 的 Step4 自动修复**改的正是被审的源码盘面**，而报告锚（`reviewed_sha` 内容锚）绑定的是修复后的盘面——**那份修复本身未经任何镜审查**。该缺口 SHALL 由一轮受限复审闭合，且该复审 SHALL 有硬上限。

- **自动修复发生后 SHALL 复审一轮**：范围 SHALL 限定为**本轮修复 diff**，MUST NOT 重审全量分支 diff。
- **硬上限 = 1 轮**〔adr/0035〕：该轮复审若仍报出 Critical/Important，**SHALL NOT 自发进入第三轮**——全部 defer 进 buglist，并在 `code-review-report.md` 显式标注「复审上限已达，N 项残差已 defer」。
- **无自动修复时不触发本复审**（无源码改动 ⇒ 锚经写锚脚本取当前被审基线盘面，本就自洽）。
- 残差的兜底责任在 `sdflow-done` 的 verify（位于所有修复之后）与 issues 池的异步再入口，**MUST NOT** 靠延长本循环来兜。

**表述一致性 SHALL 被维持**：`sdflow-implement` 与 `sdflow-code-review` 两侧关于「code-review 是否存在 fix 循环」的描述 SHALL 一致——本需求确立的形态是「**存在，且硬上限 1 轮**」。任一侧 MUST NOT 出现「无 re-review 闭环」这类与之相反的表述。

**诚实边界**：本需求是**指令层约束**，由编排器自报遵守；`ship_gate` 不为复审轮数新增机械门。MUST NOT 将其表述为机械保证。

#### Scenario: 自动修复后复审一轮且只审修复 diff

- **WHEN** Step4 产生了自动修复并完成「仅源码」的 checkpoint 提交
- **THEN** SHALL 派一轮复审，其输入 diff 范围为该修复提交本身，MUST NOT 重新打包整个分支 diff

#### Scenario: 复审仍有 Important 时 defer 而非再审

- **WHEN** 复审轮报出 2 条 Important
- **THEN** 该 2 条 SHALL defer 进 buglist，`code-review-report.md` 标注「复审上限已达，2 项残差已 defer」；MUST NOT 派第三轮复审或再次自动修复

#### Scenario: 无自动修复时不触发复审

- **WHEN** 某次 code-review 的 Step4 无任何可自动修复项
- **THEN** SHALL NOT 触发本复审轮，报告锚经写锚脚本取被审基线盘面（该 HEAD 时点的内容锚）

#### Scenario: 两侧表述不得相反

- **WHEN** 有人在 `sdflow-code-review/SKILL.md` 写下「无 re-review 紧闭环」而 `sdflow-implement/SKILL.md` 同时称其有「fix 循环」
- **THEN** 该状态 SHALL 判为违反本需求——两侧 SHALL 统一表述为「存在复审循环，硬上限 1 轮」

## REMOVED Requirements

### Requirement: 阶段三编排台账确定性（ship_gate）

**Reason**: 失鲜锚迁移为内容锚（manifest + digest，sweep-pool-debt D2/D3/D9）后，本 Requirement 的「勾选框以外的一切 tasks.md 改动照判失鲜」等场景与目标态行为正面矛盾，而场景级删除无 delta 通道，故整块退役、由 ADDED 的「阶段三编排台账确定性（ship_gate·内容锚）」原位取代。

**Migration**: 未变场景原文全部迁入 ADDED 块；变更点 = design 域监视集移出 `tasks.md`（D2）、勾选框内容豁免与 `checkpoint(impl-review)` subject 豁免通道退役改 producer 重锚协议（D9）、REFUSE_START 诊断分类按指纹判据更新。消费方（`ship_gate.py` 与其测试）随本 change 票 1 同批迁移。〔spec-review-amendment 定性订正〕subject 豁免通道的 **gate 端代码已于先前 impl-review-fix change 物理删除**（本 spec 原文对其的描述是滞后死文字）——该部分变更点实为 spec 文本追认代码现状 + producer 重锚协议**新建**，非 gate 行为变更；勾框内容豁免的代码仍在、随票 1 真删。
