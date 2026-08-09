---
schema_version: 1
change: absorb-gstack-autoplan
branch: feat/absorb-gstack-autoplan
generated_at: 2026-08-09T12:09:00+08:00
decision_hash: a964423ec8af
---

# 决策纪要 · absorb-gstack-autoplan

## 目标态

sdflow-spec-review 与 sdflow-roadmap 的评审链路全自持:gstack(autoplan + 四个 plan-review 子 skill)运行时依赖归零,广审/DX 能力不缩水。

## 拍板决策

- **D1 广审镜拆 2 + 跨模型声转正(共 3 声)** — strategy 镜(CEO 高度:前提/范围/长期轨迹/后悔场景)+ plan-eng 镜(计划级工程审:架构耦合/错误路径/测试计划/隐藏复杂度),均中档 fresh 子代理、恒跑;design-voice(codex)恒自跑补双模型维度。依据:C2(视角分离×双模型是旧 broad 独立率的来源);**砍掉的候选**:单广审镜(视角稀释,被 C2 证据反对)、三恒跑镜含 DX(放弃 TG 条件触发收益,过重)。兜底:broad 锚照落,`/sdflow-retro` ≥10 轮复评盯采纳率/独立率。〔人 2026-08-09 明确确认〕
- **D2 roadmap 侧:恒跑双镜 + 判定点②(商业化分档)退役 + sync-only outside voice 直接加** — review 执行体换为同一套 strategy/plan-eng 镜(恒跑,分档存在理由=autoplan 贵,已消失);review 契约(C7)原样保留;**跨模型声不丢**:挂 `outside-voice.sh` 的 **sync 分支**(前台 exec --timeout 300、⑦ 表映射、同族 fallback),不移植 async 段(不碰 dispatch manifest/collect barrier/两 SKILL 等值门),findings 进 task-log「Review 处置」,不接 anchor_lint/lens-metric(roadmap 本无度量锚)。依据:roadmap 低频×高杠杆,恰是 codex 调用最值的点 + sync 分支成本仅十几行指令;**砍掉的候选**:①codex 声记 todo 延后(被人当场纠正——成本估算错在把 async 协议当必需)②保留商业化分档(分档理由已消失,技术 roadmap 也需要前提拷问)。〔人 2026-08-09 明确确认恒跑双镜+分档退役;voice 直接加为人 2026-08-09 主动要求〕

- **D3 Step1 自持化:autoplan 原生执行退役** — 锚名 `step1-broad-review` 保留,mode 枚举 `native|simulated` → `subagent|main-session`(比照 code-review 先例,`sdflow-code-review/SKILL.md:275`);gstack-review.md 落盘环节随之退役。依据:探索已证的四个结构性问题(context 污染 ~7300 行/轮、`~/.gstack/` 路径语义错位、AskUserQuestion 门与 G2 冲突、第三方漂移 v1.60.2 活跃演进);**砍掉的候选**:继续复用 autoplan(上述四问题无法在复用态下解决)。〔人 2026-08-09 "go" 确认探索结论〕
- **D4 DX → 新 TG +「devex」领域,走既有领域镜机制;Design 视角归 TG-03(frontend)** — 新 TG 触发条件≈「变更新增/修改 developer-facing 交付面(CLI/公共 API/SDK/skill/配置面/错误信息)」,**不入 HR-TG**(不满足「运行期爆炸/数据损坏/安全泄漏」判据);新建 `spec-checklists/domains/devex.md`(蒸馏 plan-devex-review:TTHW 分档/错误信息 problem+cause+fix/命名可猜性/Claude Code Skill DX 清单);frontend.md 增补 litmus/AI-slop 精华为可选项。依据:C4+C5;**砍掉的候选**:DX 进广审镜恒跑(丢条件触发,消费仓白付成本)、广审镜整体条件触发(CEO 是 altitude 非 domain,任何 change 都有前提/范围问题)。〔人 2026-08-09 明确确认「DX 沿用 TG 机制」〕
- **D5 C2 复用路径 + `outside_voice_guard.py` 退役,design-voice 恒自跑** — 原回落路径转正;守卫脚本及其测试删除。依据:C6 + 复用对象(gstack-review.md)随 D3 消失;成本不升反降(autoplan 每轮 2-3 次 codex → 1 次 design-voice)。**砍掉的候选**:保留 guard 改判其它来源(无别的来源可判)。〔随 D3 联动,人 "go" 确认〕
- **D6 机械消费点同步 + 验收口径(比照 absorb-gstack-review)** — lens-metric fold 表 `autoplan-ceo/design/eng/dx→broad` 四行替换为新 raw 名(strategy/plan-eng→broad);ADR 0002 处置(见 ADR 提议);`docs/workflow-skills/gstack-autoplan.md` 降级为非运行时参考;`CONTEXT.md:29`「镜」词条 autoplan 例句、`spec-review.md:62,94`、workflow.md/WORKFLOW-GUIDE/external-dependencies.md 等文档面 sweep。**验收**:`grep -rn "autoplan\|gstack" sdflow-spec-review/SKILL.md sdflow-roadmap/SKILL.md` 归零(DOC-1 严格口径);未装 gstack 机器全流程无降级日志;全仓 pytest 绿;dogfood 本 change 自身评审出新锚。归档报告旧锚不迁移(先例同款)。〔人 "go" 确认探索结论〕

- **D7 立 ADR 0040「gstack 运行时依赖全退役」,supersede adr/0002** — 三条件齐:难逆转(方向性,回头与已删资产冲突)+ 缺上下文意外(0002 正文仍声明复用合法)+ 真实权衡(省 codex vs 控漂移,含两次部分内化的演进链)。已落盘 `openspec/adr/0040-*.md` + 0002 头部 superseded 指针。**砍掉的候选**:只改 0002 正文不立新条(演进链与新权衡塞不进旧条目,违背留档惯例)。〔人 2026-08-09 明确确认〕

## 承重约束

- **C9 anchor_lint 对 step1 锚只验存在性(前缀匹配),mode 枚举换值零脚本改动** — 验证方式:读脚本;**证据锚**:`sdflow-init/assets/workflow/tools/anchor_lint.py:73,203`
- **C10 outside-voice.sh sync 分支自足,roadmap 挂 voice 无需移植 async 段** — 验证方式:读协议;**证据锚**:`sdflow-spec-review/SKILL.md:426`(sync 行:内层 300、外层 ≥330000ms,当场取退出码)+ `:404` 注(等值门只钉 `sdflow:async-branch` marker 段,sync-only 不触发)
- **C1 broad(广审)镜价值真实,吸收 MUST 保能力不缩水** — 验证方式:retro 聚合 + 归档报告抽样;**证据锚**:`openspec/retro/report.md:182`(spec-review broad 20 轮 166 findings 采纳率 90% 独立率 33%)
- **C2 旧 broad 的高独立率主要来自多声结构(CEO/Eng/DX 视角 × Claude 子代理+Codex 双模型),非清单本身** — 验证方式:抽样归档报告命中镜签名;**证据锚**:`openspec/changes/archive/2026-08-05-harden-outside-voice-scripts/spec-review-report.md:63,71`(两条 broad 独家均出自 autoplan-CEO-Codex)+ `archive/2026-08-07-fix-probe-scan-precision/spec-review-report.md:47`(6 声结构,broad 36 条 34 独立)
- **C3 spec-quality-base 已蒸馏 CEO/Eng 两镜的核心方法论,checklist 吸收量小** — 验证方式:头注声明 + 逐条对照;**证据锚**:`sdflow-init/assets/workflow/spec-checklists/spec-quality-base.md:7`(来源含 GStack plan-ceo/eng-review),BASE-12↔CEO 0C-bis、BASE-27↔CEO 0E、BASE-06↔CEO Section2、BASE-01/05↔Eng scope challenge
- **C4 devex 是 spec-checklists 唯一真空领域** — 验证方式:目录清点;**证据锚**:`ls sdflow-init/assets/workflow/spec-checklists/domains/` 仅 backend/backend-go/embedded×3/frontend,无 devex;而本仓产品即 skill/CLI,autoplan 的 DX phase 在本仓轮轮命中(`archive/2026-08-07-fix-probe-scan-precision/spec-review-report.md:131` A3「DX 阶段执行」)
- **C5 TG 机制「A. 技术栈」组即领域镜开关,新增 TG 即可挂 devex 领域镜,机制零新增** — 验证方式:读 trigger-catalog;**证据锚**:`sdflow-init/assets/workflow/trigger-catalog.md:42-47`(TG-01/02/03/27 → domains 映射;TG-27 为 absorb-gstack-review 新增领域 TG 的先例)
- **C6 design-voice 自跑回落路径已存在且完善,C2 复用死后转正零新建** — 验证方式:读 SKILL;**证据锚**:`sdflow-spec-review/SKILL.md:193`(guard 非 none 时回落自跑 design outside voice,协议完整)
- **C7 roadmap 的 review 契约(整体 plan 声明/未审待恢复阻塞收尾/处置四态)与 review 执行体解耦,可换体不动契约** — 验证方式:读 SKILL;**证据锚**:`sdflow-roadmap/SKILL.md:470-493`(契约条款均不引用 autoplan 内部,仅引用「review skill」)
- **C8 absorb-gstack-review 先例模式可复制(自持子代理+清单吸收+机械消费点同步+grep 归零验收)** — 验证方式:读归档 proposal;**证据锚**:`openspec/changes/archive/2026-08-06-absorb-gstack-review/proposal.md`(全文已读,含机械消费点清单与验收口径)

## 接受的边角

- **新广审结构(3 声)与旧 broad(6-7 声)能力等价性事前不可证** — 概率:中(声数减半);影响:中(独立发现或降,但 adversarial/domain/grounding 各镜仍在,设计门人审兜底);完美成本:高(事前 A/B 无基准);**为何接受**:retro 既有 ≥10 轮复评机制(broad 锚照落)是低成本事后兜底,掉了再加声——通则④次优解。
- **roadmap voice 无度量锚,效果不可量化** — roadmap 本无 lens-metric 体系;为一次性 review 建锚体系完美成本过高;**为何接受**:findings 进「Review 处置」四态留痕已够审计。
- **devex 清单蒸馏自 gstack v1.60.2 快照,上游后续演进不再自动跟进** — 自持的固有代价,先例(code-checklists 吸收)同款;**为何接受**:清单进本仓后按本仓 retro 数据演进,优于跟第三方漂移。
- **归档报告旧锚(autoplan-* raw 名)不迁移** — 先例同款;retro 聚合器对旧 raw 名经 fold 表仍可解析(fold 行替换后旧名从 fold 表消失 → 聚合器按 unknown raw 处置,历史行降级可接受)。

## 三镜代价

D1(广审镜形状)与 D2(roadmap 处置)命中 TG-23,三镜已在对话 Q1/Q2 展开并记入各决策条目;两处主次判定一致:**开发循环镜主导**——评审是门禁,视角质量与流程简化优先于单子代理边际成本。其余决策(D3-D6)为先例复制/机制沿用,无 ≥2 合理方案,不强制三镜。
