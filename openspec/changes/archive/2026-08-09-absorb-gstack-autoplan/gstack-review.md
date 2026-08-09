# gstack-review · absorb-gstack-autoplan(Step1 广审 · autoplan 原生执行)

<!-- sdflow:step1-broad-review v1 mode="native" -->

> **native 侧信道佐证**:本轮 autoplan 经 Skill 机制原生进入主 session(preamble 真跑:BRANCH/REPO_MODE/SESSION_KIND 等状态实测输出;restore point 落盘 `~/.gstack/projects/laodao-ai-sdflow-skills/feat-absorb-gstack-autoplan-autoplan-restore-20260809-123046.md`);双声真实调用事实:**3 次 `codex exec`(CEO/Eng/DX 各一)均 EXIT=0 真跑**(gstack-codex-probe auth ok,timeout wrapper 540s),3 个 fresh Claude 子代理(CEO/Eng/DX)前台真派。UI scope 未命中 → Phase 2 (Design) 跳过。preamble 检出 `UPGRADE_AVAILABLE 1.60.2.0→1.61.0.0`,按 G2 自动决策「评审中途不升级 gstack」(避免管线版本中途漂移),登记入下方决策审计。

<!-- 下列三条为 autoplan 双声中 codex 侧的 outside-voice 锚(供复用守卫判定;site 为 autoplan 相位名) -->
<!-- sdflow:outside-voice v1 site="autoplan-ceo" guard="none" host="claude" runner="codex" reason_code="ok" findings="9" truncated="false" -->
<!-- sdflow:outside-voice v1 site="autoplan-eng" guard="none" host="claude" runner="codex" reason_code="ok" findings="9" truncated="false" -->
<!-- sdflow:outside-voice v1 site="autoplan-dx" guard="none" host="claude" runner="codex" reason_code="ok" findings="9" truncated="false" -->

## Phase 0/0.5 摘要

- 评审对象 = 四件套 + decision-memo + 4 delta specs(commit fb0cbe7 盘面)。
- Scope:UI=no(无渲染面词汇),DX=yes(产品即 skill/CLI 工具)⇒ 相位序列 CEO→Eng→DX。
- codex preflight:auth ok、版本无告警 ⇒ 三相位均双声(Claude 子代理 + codex exec)。
- 模式(autoplan 覆写):SELECTIVE EXPANSION。premise gate 按 G2 适配不弹窗——**四件套的 D1-D7 均带〔人 2026-08-09 明确确认〕锚,premise 实质已过人门**,登记为自动决策 AD-2。

## Phase 1 · CEO(strategy)

### 主 session Step 0 摘要(0A-0F)

- **0A premise**:「gstack 运行时依赖四问题(context 污染/路径错位/G2 冲突/第三方漂移)」成立——本轮 preamble 当场检出 gstack 1.61.0 升级提示,漂移风险为实时证据;「broad 能力承重」成立(retro/report.md:182,接地镜核验)。**C2(多声×跨模型=独立率来源)证据仅 n=2 且两条均出自 Codex 腿**——见 F2/C-2。
- **0B 复用**:anchor_lint broad token/mode 枚举先例/outside-voice.sh sync 分支/spec-quality-base 蒸馏,四处复用均经接地镜核验为真,无平行重建。
- **0C dream state**:CURRENT(第三方依赖+7.3k 行/轮)→ THIS PLAN(自持 3 声+devex 域)→ 12M IDEAL(按边际价值配置 review budget,retro 数据驱动 roster 调优)。方向朝向理想态;codex-CEO#3 的 budget 论点属 12M 理想层,本 change 的 retro 复评钩子即其入口。
- **0C-bis 备选**:memo 已列各决策砍掉候选;评审新识别一个未列候选「单广审 persona × 双模型」(F2),进决策登记。
- **0E temporal**:实现期将撞的四个决策点=fold 表 raw 口径(X-2)、retro 墙钟归属(X-4)、部署模型措辞(X-7)、6.4 验收口径(X-6)——全部在本轮前置暴露。
- **0F**:SELECTIVE EXPANSION 承诺不漂移;复杂度检查:改动面 >8 文件,但按基准 4「一个 change 一个完整阶段结果」,依赖归零的完整闭环不可再拆,不挑战。

### CEO 双声 findings

**CLAUDE SUBAGENT (CEO — strategic independence)**:F1 旧语料可回测(「事前 A/B 无基准」框架不成立,3-5 份归档盲测成本近零)· F2 C2 证据实指向跨模型腿而非 persona 数(n=2 均 autoplan-CEO-Codex;未评估「单 persona×双模型」候选)· F3 单批 dispatch 丢失「amend 先于下游镜」性质且 Risks 未讨论 · F4 「3 声 vs 6-7 声」口径混淆(broad 腿实为 2 替 6-7,design-voice 是本就存在的另一 lens)· F5 devex code 侧再入判据模糊(「实测需要再补」无阈值)。

**CODEX SAYS (CEO — strategy challenge)**:C-1 度量口径断裂(emitter 折叠后 retro 无 raw 维度,design.md:68 声称不成立——主 session 已机械核验 lens_metric_emit.py:202/lens_metric_aggregate.py 证实)· C-2 3 声≈6-7 声是未验证核心假设,shadow-run 候选被过快否决 · C-3 解决的是依赖归属而非最大瓶颈(spec-review 占墙钟 49%),Success Metrics 无时延/token/逃逸率维度 · C-4 发布 skew 窗口无消费仓清单/握手(注:其部署模型前提被 Phase3 证伪,见 X-7 修正)· C-5 roadmap 分档退役的成本推论有偷换(供应商成本≠执行成本)· C-6 DX 被压扁为文本代理指标 · C-7 voice 失败路径同族降级仍可收尾,应标 degraded · C-8 「未装 gstack 跑通」验收无任务闭环 · C-9 roadmap 引用 spec-review SKILL 段落=隐式运行时接口。

```
CEO DUAL VOICES — CONSENSUS TABLE:
═══════════════════════════════════════════════════════════════
  Dimension                             Claude  Codex  Consensus
  ────────────────────────────────────  ──────  ─────  ─────────
  1. Premises valid?                    部分     挑战    DISAGREE(C2 证据强度)
  2. Right problem to solve?            yes     部分    DISAGREE(瓶颈 vs 依赖)
  3. Scope calibration correct?         yes*    挑战    DISAGREE(恒跑成本)
  4. Alternatives sufficiently explored? no      no     CONFIRMED-GAP(shadow-run/单persona双模型)
  5. Ecosystem risks covered?           yes     yes    CONFIRMED(ADR 0040 有意识取舍)
  6. 6-month trajectory sound?          部分     挑战    DISAGREE(度量连续性 C-1)
═══════════════════════════════════════════════════════════════
```

Sections 1-10(SELECTIVE EXPANSION 深度,主 session):architecture(§1)见 Phase 3;error/rescue(§2)——voice ⑦ 表、emitter fail-closed、retro unknown 桶均有名有主,GAP=roadmap voice 双败后的「未审待恢复」已在 delta spec 内闭合,无新 GAP;security(§3)——无新出境面,run 目录 gitignore 已核验,零 finding;data/UX(§4)——不适用(无 UI),检查了 findings 数据流(镜→合并池→裁决→锚)的 nil/empty 路径:空 findings 走 zero-findings 枚举,已定义;quality(§5)见 Phase 3;tests(§6)见 Phase 3;perf(§7)——单批并行墙钟=最慢镜,优于两段相加,codex-DX K-2 的可观察性另记;observability(§8)——lens-metric 锚 + manifest 审计面保留,GAP=X-4 墙钟归属;deploy(§9)——GAP=X-7 部署模型措辞;trajectory(§10)——reversibility 2/5(ADR 0040 自认难逆),知识集中度靠四件套+ADR 缓解。

## Phase 3 · Eng(plan-eng)

**CLAUDE SUBAGENT (eng — independent review)**:E1 `outside-voice-reuse-guard` capability 无 REMOVED delta(INDEX.md:54 仍指 1:1 映射)· E2 doc sweep 漏 `docs/workflow-map.md:34,169`、`docs/workflow-overview.md:123` · E3 DD7 跨 SKILL 引用无机械 drift 守(仓内已有 parity/模板两种先例,未记录为何不用)· E4 checkpoint 合并丢崩溃恢复点(DD1 只回答了时序依赖,未回答恢复点)· E5 task 1.3 或为 no-op(map_stage 前缀规则已覆盖,test_retro_report.py:129 现绿)。另核验四处「无 finding」:DD4 fold 替换手术面干净、C9/DD3 零脚本改动声明属实、guard 唯一调用点属实、.gitignore 递归覆盖属实。

**CODEX SAYS (eng — architecture challenge)**:X-1 guard 删除违反现存 capability(outside-voice-reuse-guard 3 Requirements + host-adaptive-execution 双实现全笛卡尔 golden 条款 + lens-metric-contract 双实现散文)——须 REMOVED/MODIFIED delta + 契约措辞 + INDEX 任务 · X-2 tasks 2.4「roster 行键 raw 名」schema-invalid(emitter roster lens 越域拦截;两镜折叠同行键;6.4「raw 名 broad 镜行」不可实现)——主 session 已核验成立 · X-3 guard 死后 mode 枚举/降级真实性无机械约束 + mirrors= 语义抖动 · X-4 退役中间 checkpoint 破坏 retro 墙钟归属(相邻差计入前一提交阶段——主 session 已核验 stage_walltimes 成立)· X-5 backtest 前置(与 F1/C-2 三方收敛)· X-6 无 gstack 验收无任务 + rollback 措辞 · X-7 mixed-version 分析基于已退役部署模型(init.py:212 只铺 guide+schema;canonical 与 SKILL 同树同 setup 翻转)——主 session 已核验成立 · X-8 roadmap voice context 缺 task-log + 无 scratch 集成验收 · X-9 TG-28 无 capability delta(注:TG-27 先例同样无,主 session 核验 archive 后按先例处置,见裁决)。

```
ENG DUAL VOICES — CONSENSUS TABLE:
═══════════════════════════════════════════════════════════════
  Dimension                             Claude  Codex  Consensus
  ────────────────────────────────────  ──────  ─────  ─────────
  1. Architecture sound?                yes*    yes*   CONFIRMED(单批结构本身健全;耦合 E3/X-9 另记)
  2. Test coverage sufficient?          no      no     CONFIRMED-GAP(backtest/无gstack/roadmap 集成)
  3. Performance risks addressed?       yes     部分    (墙钟改善;可观察性缺口→DX)
  4. Security threats covered?          yes     yes    CONFIRMED(无新出境面)
  5. Error paths handled?               yes*    部分    DISAGREE(mode 枚举无机械守 X-3)
  6. Deployment risk manageable?        no      no     CONFIRMED-GAP(部署模型措辞错误 X-7/E-doc)
═══════════════════════════════════════════════════════════════
```

主 session Step 0(scope challenge):复用映射齐(0B);最小改动集=P0 闭环不可再拆(基准 4);复杂度检查触发(>8 文件)但为依赖归零的内聚交付物,不减;distribution=setup.sh/symlink 既有管线,无新 artifact。Section 3 (Test):覆盖表缺口=①归档盲测(X-5)②无 gstack 验收(X-6)③roadmap 链路集成验收(X-8)④fold 表新旧混态用例已有(1.1)。测试计划 artifact 已落 `~/.gstack/projects/laodao-ai-sdflow-skills/`(见 checkpoint)。

## Phase 3.5 · DX

**CLAUDE SUBAGENT (DX — independent review)**:D-1 design.md:67/proposal.md:33 的 skew 修复指引(`sdflow-init update`)与真实机制(全局 canonical + setup.sh)相反,emitter 错误文案反而是对的(与 X-7 收敛)· D-2 TG-28 触发条件 6 类 OR 粗于姊妹 TG,C4 自认「本仓轮轮命中」⇒ 条件触发收益在本仓不存在;「配置面」歧义 · D-3 DD2 base R 项划分不穷尽:BASE-08/09/18/22/26/30 无归属(BASE-30 恰是 18 镜漏审事故的元教训)· D-4 DD6「Claude Code Skill DX 清单」出处声明与 gstack 真实 8 项清单(AskUserQuestion/状态存储/渐进同意等)不匹配,实为 sdflow 新作而非蒸馏 · D-5 TTHW 数字档位失去 persona/竞品接地后无推导规则,恐成拍脑袋精确数 · D-6 无消费者迁移说明任务(DD6 自己引入「升级路径」标准)。

**CODEX SAYS (DX — developer experience challenge)**:K-1 升级/修复命令建立在退役部署模型上,且 anchor_lint.py:680 `_MIRRORS_UPGRADE_HINT` 现存同款失效指引(应一并修)· K-2 单批 dispatch 无操作者可观察性/逐镜失败/中断契约(建议:最简中断策略=「Step3 前不改盘面,整轮安全重跑」明写)· K-3 roadmap sync voice 未定与双镜的启动顺序,应重叠并行否则墙钟+330s · K-4 TG-28 应有 spec-of-record(同 X-9,按 TG-27 先例裁决)· K-5 devex.md 应采用 `ID/触发条件/必需证据/PASS/FAIL/N.A` 表式+`UNVERIFIABLE` 输出,TTHW 须定义 persona/起止/步数推导 · K-6 TG-28 措辞漏「重命名/废弃/删除」(最需要 DX 审的动作)· K-7 两个 Success Metric 无验收任务(同 X-6)+ 建议 3 份历史 change 预发布 backtest(同 X-5)· K-8 spec 删除缺口(同 X-1)· K-9 metric continuity + 墙钟归属(同 C-1/X-4;补充 lens_metric_aggregate.py:137 canonical 分组证据)。

```
DX DUAL VOICES — CONSENSUS TABLE:
═══════════════════════════════════════════════════════════════
  Dimension                             Claude  Codex  Consensus
  ────────────────────────────────────  ──────  ─────  ─────────
  1. Getting started(操作者链路)          yes*    no     DISAGREE(K-2 可观察性)
  2. 触发/命名 guessable?                部分     部分    CONFIRMED-GAP(TG-28 措辞 D-2/K-6)
  3. Error messages actionable?         no      no     CONFIRMED-GAP(D-1/K-1 指引错误)
  4. 清单可判性(devex.md)?               部分     no     CONFIRMED-GAP(D-5/K-5 推导规则)
  5. Upgrade path safe?                 no      no     CONFIRMED-GAP(D-6/K-1)
  6. 环境/工具整合                        yes     yes    CONFIRMED(既有 setup 管线)
═══════════════════════════════════════════════════════════════
```

DX Scorecard(对 plan 文本,DX POLISH 模式):Getting Started 7/10(单批简化+guard 树删除为净改善,K-2 缺口)· API/触发面 6/10(TG-28 措辞)· 错误信息 5/10(修复指引反向)· 文档 6/10(迁移说明缺)· 升级 5/10 · 环境 8/10 · 社区 N/A(仓内工作流)· 度量回路 4/10(C-1/X-4)。TTHW 概念对本 plan 不直接适用(操作者=既有用户),以「单轮评审墙钟与中断恢复」替代评估。

## Cross-Phase Themes(≥2 相位独立命中,高置信信号)

- **T-A 部署/升级模型措辞错误**:X-7 + D-1 + K-1(+C-4 的前提修正)——四声独立命中,且 anchor_lint 存量 hint 同病。
- **T-B 度量连续性断裂**:C-1 + K-9 + F1 关联——emitter/aggregate 双侧机械核验成立。
- **T-C guard 退役 spec 面不完整**:E1 + X-1 + K-8。
- **T-D 能力等价性应前置盲测**:F1 + C-2 + X-5 + K-7——四声收敛,「事前无基准」框架被证伪。
- **T-E 中间 checkpoint 退役的双重代价**:E4(恢复点)+ X-4/K-9(墙钟归属)。
- **T-F TG-28/devex 可判性**:D-2/D-5 + K-5/K-6(+X-9/K-4 spec 化,按先例另裁)。

## Decision Audit Trail(autoplan 自动决策)

| # | Phase | Decision | Class | Principle | Rationale |
|---|-------|----------|-------|-----------|-----------|
| AD-1 | preamble | gstack 1.61.0 升级提示:本轮不升级 | Mechanical | P3 | 评审中途换管线版本会污染本轮盘面 |
| AD-2 | Phase1 | premise gate 视为已过 | Mechanical | — | D1-D7 均带人确认锚(相位 B 拷问),非模型代决 |
| AD-3 | Phase0 | restore point 只落 ~/.gstack,不往四件套 prepend 注释 | Mechanical | P5 | 四件套受 checkpoint/git 保护,gstack 注释会污染 openspec 产物 |
| AD-4 | Phase1 | C-3(按边际价值配 budget)不展开为本 change 范围 | Taste→登记 | P6/③ | 属 12M 轨迹层;恒跑 D1/D2 为人已确认方向,评审不得代改 |
| AD-5 | Phase3.5 | DX 模式=DX POLISH | Mechanical | autoplan 覆写 | — |

**User Challenges(双模型合流、但与人已确认方向相抵的项——一律不自动采纳,进最终报告决策区)**:UC-1 恒跑成本/分档退役质疑(C-3/C-5,人已确认 D1/D2,默认维持人的方向)· UC-2 backtest 前置(F1/C-2/X-5/K-7,与「接受的边角」既有拍板相抵,信息增量=「无基准」前提被证伪)。

## Completion Summary(CEO/Eng/DX 三相位)

Phase1:Codex 9 concerns / Claude 5 issues / consensus 2 CONFIRMED 4 DISAGREE。Phase2:skipped(no UI scope)。Phase3:Codex 9 / Claude 5 / consensus 4 CONFIRMED-或-GAP 1 DISAGREE。Phase3.5:Codex 9 / Claude 6 / DX overall 5.8/10。双声降级矩阵:三相位均 codex+subagent 全跑,无降级。findings 合计:Claude 侧 16 条,codex 侧 27 条(相位间重复未去重,去重合并在 Step3 主报告)。
