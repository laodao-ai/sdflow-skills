# spec-review-report · absorb-gstack-autoplan

- **评审对象**:四件套 + decision-memo + 5 delta specs(评审起点盘面 fb0cbe7;Step1 产物落盘于 afcd956;本报告伴随 [spec-review-amendment] 修订)
- **宿主/档位**:host=claude;主审=opus(强档),领域/对抗=sonnet(中档),接地=haiku(弱档);voice=codex(gpt-5.6-sol)
- **镜 roster**:Step1 广审(autoplan 原生:CEO/Eng/DX 三相位 × Claude 子代理+codex 双声,UI 相位未命中跳过)+ 对抗镜×3(隐藏假设/失败模式/乐观边界)+ 接地镜×1;领域镜 0(TG-01/02/03/27 均未命中,无栈域清单适用);outside-voice=复用 autoplan codex 三声(guard reason_code=none)
- **合并池**:Claude 侧 16 + codex 侧 27 + 对抗 16 + 接地 6 → 去重合并为 **28 条 canonical findings**(采纳 17 / 需拍板 4 / 已裁掉 7,其中低置信一行带过区 0——所有低置信项均已升格核验或带理由裁掉)

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="adversarial,grounding" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-14,TG-18,TG-19,TG-22,TG-23,TG-24,TG-25" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="27" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="design-voice" -->

> Step1 native 佐证:autoplan 经 Skill 机制原生进主 session(preamble 实跑、restore point 落 `~/.gstack/projects/laodao-ai-sdflow-skills/feat-absorb-gstack-autoplan-autoplan-restore-20260809-123046.md`);3 次 `codex exec`(CEO/Eng/DX)均真跑 EXIT=0。详见 `gstack-review.md`(checkpoint afcd956)。
> outside-voice 复用:guard 三前置全过(来源 mode=native / fs-mtime 新鲜 / cross-model 锚 27 findings 可解析),**复用 autoplan outside voice 27 条、不重开 design-voice**(避双 codex)。站点记账:design-voice=复用未派;hr-tg=HR-TG∩=∅ 未派;dispatch manifest 无条目(本轮零 voice dispatch)。

---

## 一、决策登记区

### [自动决策](高置信,默认采纳,设计门可覆盖)

| # | 决策 | 理由 |
|---|------|------|
| AD-1 | gstack 1.61.0 升级提示:本轮不升级 | 评审中途换管线版本污染盘面 |
| AD-2 | autoplan premise gate 视为已过 | D1-D7 均带〔人 2026-08-09 确认〕锚,相位 B 已过人门,非模型代决 |
| AD-3 | restore point 只落 ~/.gstack,不向四件套 prepend gstack 注释 | openspec 产物洁净纪律 |
| AD-4 | autoplan 模式=SELECTIVE EXPANSION、DX 模式=DX POLISH | autoplan 覆写规则 |
| AD-5 | outside-voice 复用不重开(guard=none) | 确定性脚本判定,退出码 0 |
| AD-6 | **17 条确认级 findings 已直接落 [spec-review-amendment]**(M1-M4/M7/M10-M17/M19/M22/M24,清单见第三节) | 机械核验成立、修法唯一、不改人已拍板方向——按 Step4 amendment 职责落盘;设计门通读后可整体或逐条否决 |
| AD-7 | M7 验收口径改写为机械可判形式(grep 扩面+读码+dogfood),不再要求「未装 gstack 的干净机器」 | 本仓无此环境,字面不可判必然被自报顶替;改写保目标(依赖归零)不缩水,只换可判形式 |

### [需拍板](设计 HARD-GATE 逐条勾)

**Q1 · retro 墙钟归属修正(M5,高危)〔第一性原理复推后换推荐,产物已按推荐更新、待门确认〕** — DD1 退役中间 checkpoint 后,`stage_walltimes`「相邻差计入**前一**提交阶段」的现语义会让 spec-review 阶段墙钟塌缩;复推补充核验:`("sdflow-spec-generate","ff")` ⇒ **现口径下 Step1 广审墙钟本就误归 ff 阶段(既有错账)**。
- **A(推荐,已落 tasks 1.3 / DD5)**:改 `stage_walltimes` 为「计入**后一**提交阶段」(checkpoint=工作完成点)+ 新旧序列回归测试 + retro 报告统一重跑再生——同时修既有错账、保 DD1 单 checkpoint 零妥协成立、无需任何新标签。代价:49 归档 change 阶段数字向**正确值**统一重算(retro 为只读再生活文档)。崩溃恢复点损失按五问接受(概率低/影响=重跑镜/transcript 可捞)。
- **B(初版推荐,复推后证伪)**:镜收齐后落 `checkpoint(spec-review-dispatch)`——attribute-to-previous 语义下 generate→dispatch 区间(=全部镜工作)仍误归 ff,**修不了账**;「评审起点空 checkpoint」亦不可行(checkpoint-commit.sh 干净树跳过)。
- **C**:接受墙钟断代 + Risks 声明。
- **主次判定:开发循环镜主导**——retro 墙钟是本仓成本复盘唯一量化面;A 是唯一让账本变对的方案。

**Q2 · 镜定义同源机制(M6,高危,五声收敛)〔复推后换推荐,产物已按推荐更新、待门确认〕** — 核验:跨 SKILL prose 引用零先例、parity 脚本硬编码两文件、跨宿主路径无解析器 ⇒ 按 delta 原文实现必退化为「凭记忆复述」。
- **A(推荐,已落 tasks 2.5 / DD7 / roadmap delta)**:**模板注入**——真相源 `sdflow-init/assets/snippets/broad-mirrors.md`,经 sync_principles.py 扩展注入两 SKILL 的 `sdflow:broad-mirror-def` 托管块,`setup.sh --check` 门禁。已核验 sync_principles.py 结构单薄可扩(单行字面量 marker,基准 5 有界);注入=**事前预防**(只改 asset 一处),严格优于初版推荐的「复制+parity」(事后检测、仍需人工双改)与「prose 引用」(零守)。
- **B**:复制+parity 等值检查(初版推荐,降为备选)。
- **C**:prose 引用+接受漂移。
- **主次判定:开发循环镜主导**——通则块同款模式已在仓内跑通多时,边际成本最低。

**Q3 · 归档盲测(M8+M23,UC-2 用户挑战)〔复推后升级实验设计,产物已按推荐更新、待门确认〕** — 「事前 A/B 无基准」被证伪(20 份归档语料在);对抗镜 1 独家:C2 证据方向存疑(聚合 broad 独立率 33% 全镜种最低、n=2 均出自 Codex 腿)。
- **A(推荐,已落 tasks 6.5)**:盲测升级为**逐声边际贡献**实验——同一批归档语料分别单独跑 strategy / plan-eng / design-voice,测①旧 broad 独家高危召回 ②各声边际独家召回。同价回答两个问题:能力不缩水验证 + 「第二个同模型 persona 是否值得每轮付费」的证据基线(D1 双镜形态照拍板落地不动,数据说话后再议降声)。
- **B**:维持原拍板(仅 retro ≥10 轮事后复评,按归档日期分段)。
- 本项重议人已拍的「接受的边角」第 1 条——A 为推荐,人否决即回 B,不阻塞。

**Q4 · 恒跑成本异议(M9,UC-1 用户挑战,默认维持)** — codex-CEO 独家:spec-review 已占全流程墙钟 49%,本 change 把广审/领域/对抗/接地/voice 全恒跑并把 roadmap 升为恒跑三声,Success Metrics 无时延/token 维度;主张按边际价值配 review budget。**D1/D2 为人 2026-08-09 明确确认的方向,评审默认维持**;登记供人复核。备选=按 codex 主张重开分档讨论(不推荐——分档的存在理由「外部三连审贵」确已消失,budget 精细化属 12M 轨迹层,retro 复评即其入口)。

### [已裁掉](反静默压制区——原始发现 + 裁掉理由,供人复核「裁得对不对」)

| # | 原始发现 | 来源 | 裁掉理由 |
|---|---------|------|---------|
| X1 | TG-28 应有 capability delta/spec-of-record | codex-Eng#9, codex-DX#4 | 已核验 absorb-gstack-review 先例:TG-27 同为 catalog 数据资产、无 spec 场景;trigger-catalog 自身即五层单一权威源,spec 化=复制触发定义(违 catalog 首约) |
| X2 | 单批 dispatch 丢「amend 先于下游镜」性质 | Claude-CEO F3 | premise 级错误已由相位 B 拷问+设计门前滤,残余概率低;Step3 合并裁决兜底;后果=偶发浪费非正确性(五问:概率低×影响小) |
| X3 | 接地镜 6 条「Critical:任务未实现」 | grounding | 5 条为实现前设计审的预期状态误报;第 6 条(retro 无 autoplan 标签逻辑)被证伪——`_STAGE_RULES` 前缀规则覆盖,`test_retro_report.py:129` 实跑绿 |
| X4 | 需消费仓清单/版本握手防 skew | codex-CEO#4 | 前提(消费仓持有 bundle 副本)已随 adr/0039 退役;M3 修正后 Unix 无持续 skew 窗口;Windows 残余已有「pull↔setup 间勿跑阶段三」既有纪律 |
| X5 | DX 被压扁为文本代理指标 | codex-CEO#6 | 收/不收判据=基准 1 机械/语义切分的有意设计(过程方法论依赖 ~/.gstack 生态,结构上不可吸收);可判性缺口由 M17(表式+UNVERIFIABLE+推导规则)补足 |
| X6 | 新增 `check_step1_broad_review` 机械校验 mode 枚举 | codex-Eng#3(部分) | guard 退役后 mode 无机械消费者(人读复盘用);新增 lint=加防御深度非目标范围,按④砍;诚实边界已写入 DD3(M24)。mirrors=/host=unknown 两处语义澄清已采纳 |
| X7 | roadmap `--timeout 300` 绕开 config 键不一致 | 对抗镜2 F6 | sync 分支恒 300 为 helper 既有契约(config 键限定 async 两路径);DD7 已补依据句(M19)。半驳回:指出「主路径用降级路径常量」的观感成立,已以文档化解 |
| X8 | rollback 后无 gstack 机器无法运行 | codex-Eng#6(后半) | 旧 SKILL 自带 mode="simulated" 降级路径,回退非死路;gstack 未卸载为 Non-Goal 明示 |

---

## 二、合并 findings 总表(canonical 28 条)

> 命中镜缩写:B=broad(autoplan 相位,标 Claude 侧相位名)、V=outside-voice(codex 三声复用)、A1/A2/A3=对抗镜、G=接地镜。置信=主 session 复核后置信(机械核验过的标「已核验」)。

| ID | 问题(一句) | 命中镜 | 置信 | 严重度 | 裁决→去向 |
|----|------------|--------|------|--------|-----------|
| M1 | spec 树退役面不完整:guard capability 无 REMOVED delta + spec-workflow 主 spec 三处(:701 广审原生执行/:715 gstack 边界守恒/:612 复用句/:176 工具枚举)+ host-adaptive 双实现 golden 条款 + contract 散文——归档后成自相矛盾正文,且 archive 机制结构上无法发现缺 delta | B(eng)+V+A1+A2+A3 | 已核验 | **Critical** | 采纳→已落 5 处 delta 修订([spec-review-amendment] 新增 `specs/outside-voice-reuse-guard/` REMOVED + spec-workflow 2×REMOVED/2×MODIFIED + host-adaptive 矩阵 MODIFIED)+ tasks 1.5/3.2/4.3 |
| M2 | 度量连续性声明错误:emitter 折叠后无 raw 维度,design:68「按 raw 名分行」与 memo 边角4「unknown raw 处置」均与代码相悖;D1 的 ≥10 轮复评兜底建立在错误前提上 | V+A2+A3 | 已核验 | Major | 采纳→design Risks 改写(接受盲区+按归档日期分段统计;memo 冻结不回改,以 design 为准) |
| M3 | 部署/升级模型措辞基于已退役架构(proposal:33/design:67/Migration5;anchor_lint:680 存量 hint 同病) | V+B(dx) | 已核验 | Major | 采纳→proposal/design/Migration 改写 + tasks 1.6(hint 修复 fold 入) |
| M4 | tasks 2.4「roster 行键 raw 名」schema-invalid;proposal/6.4「raw 名 broad 镜行」按 emitter 契约不可实现 | V+A1 | 已核验 | Major | 采纳→tasks 2.4/6.4 + proposal Success Metrics 改写 |
| M5 | 中间 checkpoint 退役双重代价:retro 墙钟归属塌缩 + 崩溃恢复点消失 | B(eng)+V | 已核验 | Major | **需拍板 Q1**(推荐保留改名 checkpoint) |
| M6 | DD7「引用不复制」机制未定义:零先例/parity 不覆盖/跨宿主路径无解析 | B(eng)+V+A1 | 高 | Major | **需拍板 Q2**(推荐同源复制+机械等值守) |
| M7 | 「未装 gstack 机器跑通」验收无任务且本仓不可判 | V+A3 | 高 | Major | 采纳→Success Metrics/6.4 改写为机械可判口径(AD-7) |
| M8 | 归档盲测可行,「事前无基准」被证伪 | B(ceo)+V | 高 | Major | **需拍板 Q3**(UC-2,默认维持原拍板,推荐采纳盲测任务) |
| M9 | 恒跑成本/分档退役质疑,Success Metrics 无成本维度 | V | 中 | 中 | **需拍板 Q4**(UC-1,默认维持 D1/D2) |
| M10 | 广审镜个体 spawn 失败无处置路径,「个体失败」与「0 findings」锚面同形 | A2+V | 高 | Major | 采纳→spec-workflow delta 新增 Scenario(重试一次→代做+显式标注) |
| M11 | main-session 降级双镜=同源单一意见,报告分栏呈现会误读为独立双检 | A2 | 高 | 中 | 采纳→spec-workflow delta 降级 Scenario 补同源声明义务 |
| M12 | roadmap fallback 子代理无时限:挂起时「未审待恢复」永远写不出来(既无状态也无阻塞) | A2 | 高 | Major | 采纳→roadmap delta 补 fallback 时间预算 + 双败 Scenario |
| M13 | doc sweep 漏 `docs/workflow-map.md`/`workflow-overview.md`;grep 验收范围窄于 sweep 声明 | B(eng)+A3 | 已核验 | 中 | 采纳→tasks 6.2 扩 + Success Metrics grep 扩面 |
| M14 | task 1.3 按字面为 no-op(前缀规则+测试现绿) | B(eng)+A2+G(反向) | 已核验 | 中 | 采纳→tasks 1.3 改写为「确认勿新增」 |
| M15 | DD2 base R 项划分不穷尽(BASE-08/09/18/22/26/30 无归属,BASE-30 为 18 镜事故元教训)+ 防重叠语义弱化(plan-eng 错误路径 vs BE-04/08) | B(dx)+A1 | 已核验 | Major | 采纳→DD2 补完整划分+默认规则+防重叠句 |
| M16 | DD6「Claude Code Skill DX 清单」出处声明与 gstack 真实 8 项清单不符(实为新作) | B(dx) | 已核验 | 中 | 采纳→DD6 改写出处 |
| M17 | devex.md 可判性无操作化(TTHW 无推导规则/需表式+UNVERIFIABLE);TG-28 措辞漏删改废+「配置面」歧义+本仓近恒命中未记录 | B(dx)+V | 高 | 中 | 采纳→DD6/tasks 4.1/4.2 补 |
| M18 | TG-28 应建 capability delta | V | 高 | 中 | 裁掉 X1(先例) |
| M19 | roadmap voice 细节簇:与双镜应重叠启动/task-log 排除理由未记/降级字样/300 依据 | V+A2 | 高 | 中 | 采纳→DD7+roadmap delta 补 |
| M20 | 单批丢 amend 前置性质 | B(ceo) | 中 | 低 | 裁掉 X2 |
| M21 | 「3 声 vs 6-7 声」口径混淆(broad 腿实为 2 替 6-7) | B(ceo) | 高 | 低 | 采纳→以本报告注记为准(memo 冻结);拍板阅读时按「broad 2 替 6-7 + design-voice 为本就存在的另一 lens」理解 |
| M22 | devex code 侧再入判据无阈值 | B(ceo) | 中 | 低 | 采纳→design Non-Goals 补阈值 |
| M23 | C2 证据链方向存疑(聚合 broad 独立率 33% 全镜种最低,n=2 均 Codex 腿) | A1 | 高 | 中 | defer→并入 Q3 拍板材料(不改冻结 memo) |
| M24 | mode 枚举无机械校验未声明;host=unknown 时 mode 取值未定义;mirrors=「实际 fan-out」与 main-session 计入 broad 语义抖动 | V | 已核验 | 中 | 采纳→DD3 补诚实边界+取值;(mirrors 措辞已由 host-adaptive delta 全文承载,语义=实际完成含合法降级) |
| M25 | 接地镜 6 条误报(5 预期态+1 被证伪) | G | 已核验 | 低 | 裁掉 X3 |
| M26 | 消费仓清单/握手 | V | 高 | 低 | 裁掉 X4(前提退役) |
| M27 | 同族降级应标 degraded | V | 高 | 低 | 采纳(并入 M19 的「降级」字样条款) |
| M28 | DX 压扁质疑 | V | 中 | 低 | 裁掉 X5 |

**接地镜正面核验(15 项全过)**:anchor_lint broad token/dead-fanout 排除/step1 前缀匹配/guard= 不解析、TG-27 现最大编号且 28 未占用、SKILL 行号锚(426/404/193/275/470-493)、retro:182 数据、C2 两份归档报告签名、spec-quality-base 头注与 13 个 BASE 编号、domains 无 devex、fold 表四行现存、guard 唯一调用点、.gitignore 递归、ADR 0040+0002 指针、文档 sweep 目标存在、delta 锚名一致——四件套代码事实面**零虚引**。

---

## 三、已落盘 [spec-review-amendment] 清单(设计门通读对象)

1. `specs/outside-voice-reuse-guard/spec.md` **新增**(REMOVED ×3)。
2. `specs/spec-workflow/spec.md`:+REMOVED「广审层原生执行…」「gstack 边界守恒…」;+MODIFIED「跨模型 outside voice 默认开…」(复用句→恒自跑)「workflow bundle 改在权威源…」(工具枚举去 guard);ADDED Requirement 补 2 个 Scenario(M10 个体失败/M11 同源声明)。
3. `specs/host-adaptive-execution/spec.md`:+MODIFIED「锚行合法组合矩阵…」(双实现→anchor_lint 单实现,golden 收敛+迁移义务)。
4. `specs/roadmap-planning/spec.md`:voice 处置补重叠启动/fallback 时间预算/「降级」字样;+Scenario fallback 超预算双败。
5. `proposal.md`:Removed Capabilities 节、消费仓 Impact、P0 表述、Success Metrics 四条改写。
6. `design.md`:DD2(完整划分+默认+防重叠)、DD3(诚实边界+unknown 路径)、DD6(出处+表式+TG-28 措辞+近恒命中记录)、DD7(重叠启动/300 依据/task-log 理由/Q2 指针)、Risks 两条改写(M2/M3)、Migration 5、Non-Goals 再入阈值。
7. `tasks.md`:1.3 改写、+1.5/1.6、2.4 改写、+3.2、4.1/4.2/4.3 扩、任务组 5 加门、6.2 扩、6.4 对齐。

**第二轮(人指示「按第一性原理复推优化」后追加,均标注「设计门确认后执行」)**:tasks 1.3 重写为 retro 归属语义修正(Q1-A)、+tasks 2.5 镜定义模板注入 + 5.1 措辞(Q2-A)、+tasks 6.5 逐声边际盲测(Q3-A)、DD5/DD7 与 roadmap delta「MUST NOT 复制两份」句同步。Q1-Q3 的推荐方案已直接落进产物(人要求),**门上仍可整体或逐条否决**——否决即回退对应条目至备选。Q4 无改动。**decision-memo.md 为相位 B 冻结产物,一律未动**——其边角 4/C2/D1 口径的勘误以 design Risks 修订与本报告 M2/M21/M23 为准。

## 四、度量锚(lens-metric,metrics.enabled=true;门前草稿值,拍板回写时最终化〔SR-M〕)

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="13" 采纳="11" 裁掉="0" defer="2" 独立="2" sev="致1/高6/中4/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="13" 采纳="9" 裁掉="1" defer="3" 独立="3" sev="致1/高2/中4/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="6" 采纳="0" 裁掉="6" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="17" 采纳="9" 裁掉="4" defer="4" 独立="1" sev="致1/高5/中3/低0" -->

**信任边界声明**:分类正确性(finding 归哪个 lens)、roster 完备性、findings JSON 誊写准确仍是主 session 信任边界;emitter 只保证给定输入的确定性归约。本轮归属约定:autoplan 各相位 Claude 子代理 → raw `autoplan-ceo/eng/dx`(fold→broad);autoplan codex 三声(经 guard 复用为本轮 design-voice)→ outside-voice/design-voice 行;对抗镜 1/2/3 → raw `对抗镜N`(fold→adversarial)。`findings=N` 与合并池数值一致性为主 session 信任边界、非机械可验。

## 五、诚实边界与残余

- 探针:host=claude 免探恒 available;`mirrors="adversarial,grounding"` 为本轮实际 fan-out 镜(broad 经 autoplan 原生执行、非 fan-out 子代理,不入 mirrors)。
- 本报告 `guard=` 字段仍按现行锚文法落(本 change 实现后新文法才移除)。
- 领域镜 0:栈判定(markdown workflow 资产 + Python 工具)不命中 backend/embedded/frontend/llm 任一 domains 清单——非降级,是「只审命中的」。
- cross-model voice 未独立重跑(复用 autoplan 三声):三声 context=各相位 prompt 而非「proposal What Changes + design Decisions 全文」的标准 design-voice 摘录——覆盖面更宽(含 DX/Eng 角),但非逐字标准协议;守卫判定合法复用,如实登记此差异。

## 六、收敛口

**建议:带 Q1-Q4 进设计 HARD-GATE。** M1(Critical)与全部确认级 Major 已修订落盘;Q1-Q3 经第一性原理复推后,推荐方案(retro 归属修正/模板注入/逐声盲测)已按人指示落进产物、门上确认或否决即可;Q4 默认维持人方向。拍板批准即无遗留改动,直接按拍板回写协议落 `ship-gate` frontmatter(注意:若拍板前再改四件套,须先单独 checkpoint 再回写锚——ADR-7(b))。

**流程纪律提醒**:本轮评审对象含评审自身落盘的 amendment(镜子审的是 fb0cbe7 起点盘面;amendment 为裁决产物、非镜审对象)——拍板时通读第三节清单即等价于窄复核增量;若人要求二次修订,按 1.7b 先单独 checkpoint 再回写 `reviewed_sha`。
