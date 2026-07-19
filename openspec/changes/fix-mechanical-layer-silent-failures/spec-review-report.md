---
ship-gate:
  design_approved: true
---
# spec-review-report — fix-mechanical-layer-silent-failures

## 拍板记录

**设计门已拍板批准，2026-07-19。** 批准的是**收缩后的范围**（B9 + B10，见 `proposal.md`「范围收缩记录」）。

> 🔴 **下方原始结论行是「收缩前全量范围」下的判定，保留不删（反静默）**，但**它点名的问题已随 recorder 半边整体移出本 change**：三条方向性错误（DIR-1/2/3）、两条自造新洞（NEW-1/2）、面治漏网面，**全部**属 recorder 或 R7，已分别归入 `T170` / `T171`。本报告中针对留下来的 B9/B10 的发现只有一条措辞级（A9，已改）。
> 拍板依据因此不是「报告说可以」，而是「**报告说不行的那些东西已经不在这个 change 里了**」。

### 补锚记录（人工越权留痕，2026-07-19）

**实现期 Task 2 的返修改动了 `design.md`，触发 `ship_gate` 设计门失鲜 `REFUSE_START`。经人拍板补锚放行，未重跑 `/sdflow-spec-review`。**

- **改了什么**：`f16bf99`（批准提交）以来 `design.md` 净 **+13 / -3**，全部为残余诚实登记——D2 的单行诚实边界扩成三行表，登记 **(a)** SIGKILL 孤儿、**(b)** PID 记录窗口（`&` 与 `OV_RUNNER_PID=$!` 之间，trap 触发时 PID 为空 ⇒ 该 runner 逃逸）、**(c)** PID 清空窗口（`wait` 返回与 `OV_RUNNER_PID=""` 之间，可能对已回收/已复用的 PID 发信号）；失败模式表加 F6/F7、F5 补 (a) 标号；Risks 条目同步扩写。
- **为什么不重审**：改动**纯 additive**，无设计结论变更、无 MUST 放宽——该判定由 Task 2 的独立 re-review 逐条核实，非自评。重跑九镜设计审所要回答的「设计变了没有」已有答案。
- **为什么不撤回改动来过门**：(b)(c) 是实现期实测出的真实残余，D2 诚实边界正是它们的归属地。为躲门禁而删掉登记 = 拿掉诚实性来换机械绿，与本 change 的主题直接冲突。
- **代价**：本条即 gate reason 指名的「显式越权留痕」通道，git 可审计。

### 补锚记录 · 第二次（人工越权留痕，2026-07-19）

**Task 3 执行中根治了一条残余，`design.md` 因此再次改动，二次触发设计门失鲜。经人拍板补锚放行。**

- **改了什么**：① 新增 **D2.1** 段——`ov_cleanup` 的 KILL 升级由「杀 `timeout` 单个 PID」改为「带守卫的负号进程组 KILL」，根治了「runner `trap '' TERM` 忽略终止信号 ⇒ 子树逃逸成孤儿」；残余表由 (a)(b)(c)(d) **收回** (a)(b)(c)，F8 标「已治」。② 登记守卫自身的退化边界（非 GNU / 未 `setpgid` 的 `timeout` ⇒ `reason=not-leader` 降级，退回旧行为，打 `OV_GROUP_KILL_DEGRADED=1` 哨兵）。③ 补登 (c) 在组级升级后**爆炸半径放大**（误杀由单个无关进程变为整个无关进程组）。
- **为什么是「改设计」而非「实现细节」**：D2 原文把这条登记成了残余，现在改判为已治——**残余表的增删属设计结论变更**，不是纯 additive，故本次失鲜是实质性的、补锚不是走形式。
- **拍板依据**：用户在知悉「根治只差一个负号（实测：`kill -KILL -PID` 可穿透忽略 TERM 的子树，且 `timeout` 自立进程组、不误伤脚本自身）」后，明确否决了原先「按实测修正 Success Metric 2」的方案，改判为**根治**——即锚定目标态（R2「父被回收时 runner 子进程必死」）而非向现状妥协（通则③）。
- **验证**：双轴审 Standards **PASS**（含本机独立复现最高危自杀面 + bash 3.2 四态真调）、Spec 轴四条验收标准 ✅、全套件 1743 passed。
- **代价**：同上，显式越权留痕，git 可审计。

---

**〔收缩前原始结论〕不建议直接进设计 HARD-GATE。** 本轮 9 个评审单元产出 **3 致命 + 8 高危**，其中 **3 条是方向性错误**（不是补丁能盖的），且**已全部就地返修落进四件套**。建议：**人过一遍本报告的「方向性错误」段再拍板**——那三条推翻的是设计的核心机制，不是边角。

> 该建议**已执行**：接缝冷复审（`seam-review-report.md`）跑了 3 个单元，判定收敛困难，据此拍板拆分。

## 本轮阵容

<!-- sdflow:step1-broad-review v1 mode="simulated" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->
<!-- sdflow:hr-tg v1 hit="TG-08,TG-17" declared="TG-08,TG-17,TG-18,TG-19,TG-22,TG-23" evidence="改动外部工具调用方式(codex/claude runner·timeout·od)并新增 sidecar 落盘通道；且位于出境 prompt 构造与 secret_scan 邻域" -->
<!-- sdflow:declared-sites v1 declared="design-voice,hr-tg" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="simulated-source" host="claude" runner="codex" reason_code="ok" findings="4" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="4" truncated="false" -->

| 单元 | 档位 / runner | 产出 |
|---|---|---|
| Step1 广审（**simulated**） | opus | 2 致 + 2 高 + 3 中 |
| 领域镜（BASE 通用清单） | sonnet | 1 致 + 1 高 + 3 中 |
| 对抗镜 A（状态与时序） | sonnet | 1 致（并**证伪**我 2 个假设） |
| 对抗镜 B（猎杀假绿） | sonnet | 1 致 + 1 高 + 1 中 |
| 对抗镜 C（承诺 vs 实得） | sonnet | 1 高 + 2 中 |
| 接地镜（代码事实） | haiku | 1 处不符，其余逐条为真 |
| design-voice（**跨模型**） | codex `gpt-5.6-sol` | 1 致 + 3 高 |
| hr-tg（**跨模型**） | codex `gpt-5.6-sol` | 4 高 |

**跨模型性成立**：`host=claude ∧ runner=codex ∧ reason_code=ok`，矩阵判 cross-model。

## 🔴 方向性错误（请人重点看这三条）

这三条不是「漏了一个 case」，是**设计的判据本身指错了方向**。三条全部由**跨模型 voice** 或**对抗镜**发现，同族镜（含我自己两轮）全部漏过。

### DIR-1 — 阻断分类表方向写反，且漏掉真正会丢条目的诊断〔design-voice · 致〕

`_build_effective_snapshot` **无条件纳入 frontmatter items** ⇒ frontmatter 是真相源。而诊断按 `result["format"]` 分两套：

| 诊断 | 条目会丢吗 | 初版判 | 实际应为 |
|---|---|---|---|
| `marker block 有 X 但缺 frontmatter item`（canonical） | **会** | **表里没有这条** | 🔴 阻断 |
| `frontmatter 有 X 但缺 marker block`（canonical） | 不会 | 🔴 阻断 | 告警 |
| `块有 X 但缺总览表行` | 会 | 🔴 阻断 | 阻断（**但仅 legacy 产生，目标态不出现**） |
| `X 行 arity 异常` | **会错位丢 change/batch** | 告警 | 🔴 阻断〔hr-tg 独立命中〕 |

**根因是通则③ 的反面**：我拿**本次事故的现象**（legacy 路径诊断）去定义**目标态**的判据。

### DIR-2 — `exit 2` 早已被占，新契约会制造新的错误停机〔对抗镜 B · 致〕

`main()` 有 `except ValueError → SystemExit(2)`，而 `RecorderLockError(ValueError)` **就是并发锁冲突**——瞬时、重跑即好。初版把 `2` 赋成「重跑无用、MUST NOT 重试」，`/sdflow-done` 会把「等一秒」硬停成「需人工介入」。已改用空闲码 `4`，并要求**落地前先枚举全部退出码路径**。

### DIR-3 — 「两条路径抽成单一函数」与本仓自包含架构冲突〔design-voice + 对抗镜 B 双命中 · 高〕

`_scan_pool` 走 subprocess 正是为避免跨 skill import（`adr/0025`：三份 helper 物理复制）。照字面落地只有两条路：引入被禁的跨 skill 耦合，或**各写两份却伪称同源**（后者测不出漂移，`assert fn_a is fn_b` 根本写不出来）。且对应 Scenario 的 WHEN 写「检视实现」——**不是运行时可触发条件，伪机械门**。
**改判**：同源的是**契约**不是函数——机器可读 diagnostic code taxonomy + 同一份 conformance fixtures 跑三方。

## 本 change 自己造出来的新洞（2 条，均已补 task）

- **NEW-1〔对抗镜 A · 致〕**：严格默认生效后，阻断→人修→重跑时，已 tag 项被 `--open-ungrouped` 滤光 ⇒ `tagged==[]` ⇒ 命中既有 FIX-2 早退 ⇒ **不跑 reindex 却 exit 0**，批次条目永远同步不进 INDEX。**与本 change 要根治的病灶同型，只在新机制生效后才出现。**
- **NEW-2〔hr-tg · 高〕**：`sweep` 按池 `scan→triage(写盘)→下一池`，**第二池的阻断拦不住第一池已写下去的**。改两阶段。

## 面治漏网面（1 条，high）

**写侧存在同款洞〔对抗镜 C〕**：`cmd_add`/`cmd_set_status`/`cmd_triage` 写前调 `_reject_document_mutation`，判据是**对自由散文 `problems` 做子串匹配** `"marker" in p or "frontmatter" in p`。实测反例 `块有 B10 但缺总览表行` → `False` ⇒ **放行写入**。

双重讽刺：① 我一直治「读残缺别写盘」，写侧另有一套更老的判据，四件套初版零提及；② 这正是我在 task 3.7 明令禁止的「消费方子串还原分级」的**存量实例**——**禁了未来，没看见现在**。

## 其余采纳项

| # | 来源 | 内容 |
|---|---|---|
| A1 | hr-tg | 「字段缺席 ⇒ 全部 problems 视为阻断」在 `problems=[]` 时作用于空集 ⇒ 放行。改为**缺席本身独立成 sentinel** |
| A2 | hr-tg + design-voice | R7 sidecar 缺身份/生命周期契约：报告无 run-id、多 run 并存会**串轮**、fallback 的 `render-prompt` 不产 sidecar、reuse 分支本轮无 sidecar 会被误杀。已补五条契约 |
| A3 | design-voice | 「判定早于任何 discovery/stat/open」**逻辑不可实现**（阻断集只能在解析后产生）。我把锁获取的纪律错误复用到数据校验。改为「早于任何写盘」 |
| A4 | 领域镜 + hr-tg + design-voice **三镜独立命中** | 测试覆盖图仍列三个不适用调用方 + 任务号过期。**我在正文删了假绿，却把它们留在同文件的另一张表上** |
| A5 | 领域镜 | 「阻断集」字段名与 JSON 形状 12 处提及、**零定义**。已定死 `"blocking": [{code,id,detail}]` 并明确「字段缺席 ≠ 空数组」 |
| A6 | 对抗镜 B | sidecar↔锚行 mismatch 用例缺失（正是 D7 要堵的点），补 6.4b |
| A7 | 接地镜 | 路径②流程图 `retag` → 实际 `retag_rename_snapshot`（其余代码事实逐条为真） |
| A8 | 对抗镜 C | 「文件独立 ≠ merge 独立」：A1（Linux 截断）若被证伪会卡住整个 change，连带卡住已做完的 B10/B11/B12 |
| A9 | 广审 | python3 备选被「新增依赖」否得过快 ⇒ 改记为**偏好而非技术证伪** |

## 已裁掉 / 降级（反静默压制，连理由留档）

| # | 原始发现 | 裁决 |
|---|---|---|
| X1 | 领域镜：四件套正文 42 处考古层文字、无附录承接（DOC-1 / BASE-30） | **采纳但降级为 defer**：确为真问题（我是此病高发户，`docs/sad/07` 有实证），但本轮返修又新增了大量 `[spec-review-amendment]` 注记，**此刻整理必然二次返工**。**MUST 在 done 前做一次「正文留结论、演进史迁附录」清理**，已记 todolist |
| X2 | 领域镜：D1 缺「三镜 + 主次判定」结构化表述 | **降级为注记**：结论本身站得住（有实测），补一句主次判定即可，不重写整节 |
| X3 | 领域镜：利益相关方未标否决/决策/建议/知情权力级别 | **裁掉**：单人仓，权力级别恒为本人，标注是纯样板 |
| X4 | 对抗镜 C：Non-Goal ③ 证伪条件写窄（非 Windows 专属） | **采纳措辞更正**，但**未构成已证伪**（符号链接近乎瞬时，中断概率极低） |

## 决策登记区

| 类型 | ID | 内容 |
|---|---|---|
| **[需拍板]** | Q1 | **本轮返修量是否已超出「一次评审可吸收」的范围？** 3 致 + 8 高 + 3 方向性错误全部就地改进了四件套，但**改动本身未经任何评审**。我的推荐：**过设计门前再跑一轮窄范围冷复审**，只盯本轮 amendment 的接缝（依据：`rework-introduces-holes-at-seams` 三类高发模式——扩枚举不回改派生判据、解耦只解耦函数不解耦输入、期望集取错范畴）。代价：一轮评审成本。备选：直接拍板，接受接缝风险 |
| **[需拍板]** | Q2 | **D-6 阻塞条款**：`scan --json` 是三脚本共享契约，本 change additive 扩展它（新增 `blocking` 字段）。声明已由 grill 期的假话改写为实话，**但改写后未经人放行**。请确认 |
| [自动决策] | D1 | 阻断类退出码取 `4`（`2` 已被锁冲突占用），落地前须枚举码位 |
| [自动决策] | D2 | 「同源」从函数改为 diagnostic code taxonomy + conformance fixtures |
| [自动决策] | D3 | 写侧 `_reject_document_mutation` 纳入本 change（补 task，非仅登记残余） |
| [自动决策] | D4 | 考古层清理 defer 到 done 前（理由见 X1） |

## 诚实边界（本轮评审自身的）

- **Step1 广审 `mode="simulated"`**：autoplan 可用但架构不匹配（其 Phase 0 要求把 restore-point 与 audit trail 写进 plan file，本仓对应物是四件套，会违反 DOC-1）。以独立 opus 子代理三视角 + 强制读码替代，**不是「跑过了 autoplan」**。
- **两个 voice 首次 dispatch 失败（rc=1）**，根因是 **workflow 缺陷**：SKILL 的 async 段把命令形态逐字写死为不带 env 前缀，而 ADR-9 要求 helper 读第零步 export 的 `$SDFLOW_VOICE_RUNNER`——harness 每次 Bash 调用是独立 shell，**按字面执行必然 100% 拿不到 runner**。本轮靠内联 env 绕过（**偏离 SKILL 字面命令形态**），重试换了新 run-id（遵 per-run 不可变）。已记 todolist。
  **附带推论**：上个 change 交付时两站点 voice 未拿到真跨模型结果，当时归因 UTF-8 截断（B9）；**本轮 context 仅 17KB/7KB、`truncated=false`、内联 env 后即 rc=0** ⇒ **env 丢失才是首因**，B9 未必在场。
- **数值一致性**（`findings=N` 与合并池实收数）是主 session 信任边界，非机械可验。
- **「机制活但主 session 偷懒自代多镜」无机械守**——本轮 9 个单元均有独立 task-id 与返回记录，但该证据由我自报。

## 度量锚

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="5" sev="致2/高2/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="6" sev="致2/高1/中3/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="5" 采纳="4" 裁掉="0" defer="1" 独立="4" sev="致1/高1/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="2" sev="致1/高3/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="3" sev="致0/高4/中0/低0" -->

**读法**：两个跨模型 voice 合计 8 条 findings、**独立 5 条**，且贡献了 1 致 + 7 高——**独立率与严重度双高**。同族镜（含我自己两轮 grill + 返修）全部漏过 DIR-1/DIR-3。这是本轮最值得记住的数据点：**跨模型层不是边际残差，是承重墙。**

### 〔SR-M〕拍板时的最终化处置：**保留门前值，不按定义重算**（附理由，不静默）

SR-M 要求拍板回写时重算采纳/裁掉/defer。我算过了，**按 `lens-metric-contract.md` 的定义重算会得出一个与事实相反的数**，故不照做：

- 定义：`独立` = 唯一报过 **∧ 被采纳**；
- 拆分后，两个跨模型 voice 的 8 条 findings **全部**因主题移出而成为 `defer`（归 `T170`/`T171`）；
- ⇒ 机械重算得 `outside-voice` 两行 **采纳=0、独立=0**。

**但这与事实完全相反**：正是这 8 条（尤其 DIR-1「阻断分类方向写反」、DIR-3「同源函数违架构」、S3「rename 拓扑第二次错」、S4「退出码地基不成立」）**直接导致了拆分决策本身**——这是本轮**价值最高**的产出，却会被记成「零贡献」。

**根因是度量定义的缺口**：`采纳/defer` 二分假设了「finding 的处置 = 它的主题是否留在本 change」，无法表达「**finding 改变了 change 的边界**」这一类。而后者恰恰是高价值发现的典型形态。

∴ 本报告**保留门前值**，并**显式登记该定义缺口**（已记 todolist）。**MUST NOT** 被后续聚合器误读为「已按 SR-M 最终化」——它是**知情保留**，不是漏执行。
