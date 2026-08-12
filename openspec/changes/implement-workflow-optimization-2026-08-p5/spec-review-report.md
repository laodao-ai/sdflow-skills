# Spec Review Report · implement-workflow-optimization-2026-08-p5

- 评审日期：2026-08-12 · 宿主 host=claude（强档主审 + fan-out 子代理）
- 镜子审入场盘面：`5af3ff14689cb495481d0d684eae6b37d8dc47a1`（amendment 落盘后须 checkpoint，拍板锚以拍板时 HEAD 为准）
- 评审对象：proposal / design / specs（spec-authoring + spec-workflow 两 delta）/ tasks + decision-memo

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="broad,domain,adversarial,grounding" -->
<!-- sdflow:step1-broad-review v1 mode="subagent" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-18,TG-19,TG-22,TG-25,TG-28" -->
<!-- sdflow:outside-voice v1 site="design-voice" host="claude" runner="codex" reason_code="ok" findings="4" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="design-voice" -->

## 执行摘要

单批 dispatch 7 个派发点全部收齐：广审双镜（strategy / plan-eng，fresh 子代理）+ devex 领域镜
（TG-28 命中）+ 对抗镜 ×2（隐藏假设·乐观估计 / 失败模式·边界）+ 接地镜 + design-voice
（codex/gpt-5.6-sol，async·harness 后台，~6min，rc=0）。合并去重得 21 条（原始 findings 26 条），
机械引用核 `findings_ref_check.py` 18/18 `pass`（3 条裁掉项未入核，见已裁掉区）。

**裁决结果：16 条采纳（amendment 已全部落盘，标 `[spec-review-amendment]`）、2 条需拍板、3 条裁掉。**

最重的三条（均已修复）：

1. **计数缺口（高，4 镜收敛）**：仓内实为 **15** 个顶层 SKILL.md（`sdflow-devenv` 464 行、
   `sdflow-upstream-watch` 335 行在册），≤500 行者 8 个——proposal/tasks 全文按 14/7 规划，
   审计骨架会结构性漏掉一个 skill 且无后续机械检查能发现。已全文改 15/8。
2. **「一次一问」残留规范面（高，voice 独家）**：design 声称「无 bundle 下发面」，但
   `generation-process.md:75`（bundle 权威源）、`sdflow-spec/SKILL.md:161` 相位图、
   spec-workflow 主 spec「拷问协议不因触发方式改变」Scenario 三处规范面仍写「一次一问」，
   archive 后主 spec 将自相矛盾。已扩 De 消费面 + 新增 task 2.3 + spec-workflow delta 补
   MODIFIED Requirement。
3. **只拍链头的沉默批准漏洞（高，voice 独家）**：SA-03 允许「只拍链头」但未定义下游状态——
   整链推荐可能被默认为已批准，直通「人机共识达成」。已在 SA-03 加待拍板状态条款 + Scenario
   （与通则「MUST NOT 拿沉默当授权」同源）。

## 决策登记区

### [自动决策]（高置信裁决，amendment 已落盘，默认接受、人可覆盖）

| # | 源 finding | 严重度 | 裁决与 amendment |
|---|---|---|---|
| D1 | M1 计数 14→15（strategy F1 + 对抗镜B F01 + voice + 接地镜，`proposal.md:12`） | 高 | proposal 4 处、tasks 3.1/3.3、design 组件图全部改 15/8，名单以 `find` 实测为准 |
| D2 | M2 「一次一问」残留面（voice 独家，`design.md:52`「无 bundle 下发面」证伪） | 高 | design De 重写（三处消费面显式列出）；tasks 新增 2.3；spec-workflow delta 补 MODIFIED「阶段一入口」Requirement 同步 Scenario 措辞 |
| D3 | M3 只拍链头缺 pending 状态（voice 独家，`specs/spec-authoring/spec.md:12`） | 高 | SA-03 依赖链 bullet 补「下游保持待拍板、沉默不是授权」+ 新增 Scenario |
| D4 | M4 layer 分治实现模式未拍板（对抗镜A A1/A2，`design.md:39`） | 中 | design Db 拍板：新函数 MUST 带 `layer` 参数按 `check_declared_sites` 模式分支；MUST NOT 复用 `check_existence`/`MANDATORY`（layer 死参陷阱）；tasks 1.1 同步强制措辞 |
| D5 | M5 重复锚未定义（plan-eng PE-1 + 对抗镜B F02，`specs/spec-workflow/spec.md:17`） | 中 | delta 补「重复拍板层锚被拦」Scenario（fail-closed，沿 `duplicate-fanout-anchor` 先例）；tasks 1.2 加负例 |
| D6 | M6 锚存在 ≠ 三问正文存在（voice，`specs/spec-workflow/spec.md:14`） | 中 | 机验声明收窄为「拍板层**声明锚**机验」，三问正文属 SKILL 模版契约 + 人读层，诚实边界显式写进 delta 与 design Db；不加正文机验（prose 解析违背基准 5） |
| D7 | M7 「行数显著下降」乐观估计（对抗镜A A3 + plan-eng PE-4，`proposal.md:57`；A3 实测三大 SKILL 考古层关键词命中仅个位数） | 中 | Success Metrics 改为「删/迁/留三数留档、净变化以 audit 实测为准，零/小改动同样合法」，不预设幅度 |
| D8 | M10 lint 报错文案三件套职责（devex DX02-1，`specs/spec-workflow/spec.md:26`） | 中 | lint 沿用既有 `[anchor_lint] VIOLATION` 结构化格式；problem/cause/fix 转译由 SKILL 自检步承担，tasks 1.3 补强制句 |
| D9 | M9 三流「互相独立」与共享编辑文件张力（strategy F2 + 对抗镜B F05，`design.md:6`） | 低 | design Context 补「语义独立」限定 + 同会话顺序执行纪律（1.3/2.1 先于同文件的 3.2） |
| D10 | M12 「无版本 skew 窗口」作用域（对抗镜A A5 + devex DX04-1，`design.md:92`） | 低 | 限定为「本仓项目侧」+ 引 D13/adr0039；消费仓窗口为既有架构通性（旧 SKILL + 旧 lint 自洽不误伤） |
| D11 | M13 roadmap 5.2 「Step3」过时措辞（strategy F3，`roadmap.md:345`） | 低 | tasks 4.1 顺带修 Step3→Step4 |
| D12 | M14 缺 `q=` 属性边界（plan-eng PE-2，`tasks.md:11`） | 低 | delta q 变异 Scenario 扩「缺 q= 属性」；tasks 1.2 负例 4→6 组 |
| D13 | M15 GQ 短 ID 不可 grep（plan-eng PE-3，`tasks.md:3`） | 低 | spec-workflow delta Requirement 标题加 `GQ` 前缀，与 SA-03 惯例一致 |
| D14 | M16 SA-03 不设迁移文案的判断未写明（devex DX04-2，`design.md:51`） | 低 | design De 补显式判断句（symlink 单点分发、无版本共存态） |
| D15 | M17 `sync_principles --check` 时机滞后（对抗镜B F04，`tasks.md:37`） | 低 | 挪进逐文件循环（成本≈0，归因窗口从 15 文件收窄到 1） |
| D16 | M18 测试路径前缀缺失（接地镜 GD-003，`design.md:82`） | 低 | design scope-check 表 / tasks 1.2 补全 `sdflow-init/assets/workflow/` 前缀 |

### [需拍板]（设计 HARD-GATE 时勾选）

**Q1 · TG-23 命中判定张力（strategy F4，`decision-memo.md:85`，中）**
memo 自判「本次无 TG-23 命中」，但 D1–D4 每条都列有「砍掉的候选」，字面满足「≥2 合理方案」
触发条件；尤其 D3（分批/整链呈现协议）有真实的三镜权衡（交互体验/认知负担/组合爆炸退化）。
- **选项 A（推荐）**：memo 补 D3 三镜简表（系统镜：无代码耦合、纯 SKILL 条款可回退；用户镜：
  减少往返轮次、拍链头可见下游影响；开发循环镜：条款固化免每 session 重训——主次判定：用户镜
  主导，本决策为交互协议）。成本 ≈ 5 分钟，论据 memo 已有、只差归类成表。
- **选项 B**：维持原判，在 memo「三镜代价」处加强一句论证（D3 属流程节奏类、候选间无架构性
  分岔，故不视为 TG-23 的「非显然设计选择」）。
- 三面后果：系统镜——两选项均无代码影响；用户镜——A 多一段可读决策档案，B 保持 memo 紧凑；
  开发循环镜——A 为后续同类交互决策立范式，B 零成本。**主次判定：开发循环镜主导（memo 是
  长期决策档案），推荐 A。**
- ⚠️ memo 是人已确认的拍板记录，评审不代改——勾选后由实现期或收尾回填补写。

**Q2 · 「references/ 默认不加载」未验 Codex 侧（对抗镜A A4，`proposal.md:89`，中）**
该假设的验证依据（sdflow-spec 先例）只覆盖 Claude Code；本仓 skills 同时 symlink 进
`~/.codex/skills/`，四件套无一句 Codex 侧调研，T275 的 token 收益在 Codex 宿主下未验证。
- **选项 A（推荐）**：tasks 3.1 后补一步低成本 spot-check——Codex 会话触发一个已有
  `references/` 的 skill，观察 context 是否包含旁文件（一次性 ≈5 分钟）。若例外成立，按
  proposal 既有失效路径处置（该 skill 改直接删除）。
- **选项 B**：不加验证步，接受 proposal 假设表既有失效防御（发现例外 → 改删除）——收益缩水
  风险留给实现期自然暴露。
- 三面后果：系统镜——两选项均不改架构；用户镜——A 提前确认双宿主收益，B 有 Codex 侧收益
  落空的迟发现风险；开发循环镜——A 增一次性 5 分钟，B 零成本但可能返工。**主次判定：
  用户镜（token 收益是本 change 的核心目标）主导，推荐 A。**

### [已裁掉]（反静默压制，可审计）

| # | 原始发现 | 裁掉理由 |
|---|---|---|
| X1 | 接地镜 GD-002（高）：roadmap 路径应为 `roadmaps/archive/workflow-cost-optimization/` | **主 session 核验裁掉**：四件套实引 `workflow-optimization-2026-08`（`proposal.md:5`，目录真实存在）；`workflow-cost-optimization` 是主 session dispatch prompt 的诱导错误，非四件套缺陷 |
| X2 | 接地镜 GD-001 名单部分：15 个含 `benchmark`、缺 `sdflow-devenv` | **主 session 核验裁掉**：`find` 亲验名单含 devenv/upstream-watch、无 benchmark——接地镜计数正确但名单幻觉；计数结论已并入 D1 |
| X3 | 对抗镜B F03（低）：fence-aware 不覆盖行内单反引号 code span | **out-of-scope**：既有六类锚共享口径、行为一致，改动属系统级另开（通则③不加宽）；对抗镜自评「记录性质，非本 change 独有」 |

## 各镜 findings 摘要

- **strategy 广审镜**（4 条：F1 高→D1 / F2 中→D9 / F3 低→D11 / F4 中→Q1）；BASE-01/08/09/10/13/14/18/22/26/27/30 余项 PASS。
- **plan-eng 广审镜**（4 条：PE-1 中→D5 / PE-2 低→D12 / PE-3 低→D13 / PE-4 低→并入 D7）；BASE-05/16/17/19/25/28 余项 PASS（已核 anchor_lint 三处行号引用与 14 个行数声明全部属实）。
- **devex 领域镜**（TG-28）：DX02-1 中→D8 / DX04-1 中→并入 D10 / DX04-2 低→D14；DX-01 N/A、DX-03/DX-05 PASS（新锚命名遵先例、报告插入点与既有格式相容、迁移指针行降级路径清晰）。
- **对抗镜 A（隐藏假设/乐观估计）**：A1 高→D4 / A2 中→并入 D4 / A3 中高→D7 / A4 中→Q2 / A5 低中→并入 D10；REFUTE-FAILED ×4（未知锚被静默跳过✓、22 测试计数✓、行数声明✓、不回扫归档✓）。
- **对抗镜 B（失败模式/边界）**：F01 高→D1 / F02 中→D5 / F03 低→X3 / F04 低→D15 / F05 低→D9；REFUTE-FAILED ×7（含：DOC-1 删除测试对「教训即判据」段落可操作不误删——抽查 `sdflow-done/SKILL.md` 踩坑表 6 行全部与正文既有规则重复；layer 枚举 argparse 二值封闭；p4 回放插入点良定义；「链头改判重提 vs 背景不重复」两条款作用对象不同非冲突；「组合爆炸」无确定性信号属合法语义残差）。
- **接地镜**：19 项代码事实核验 16✅（含 memo C1–C5 全部证据锚、7 个 SKILL 行数逐一吻合、anchor_lint 三处行号、evolution-notes 先例、p4 归档报告、T256 调研段、DOC-1 规则），2❌ 1⚠️ → D1/D16/X1/X2。
- **design-voice（codex/gpt-5.6-sol，跨模型合法：host=claude ∧ runner=codex ∧ reason_code=ok）**：4 条全部采纳（D1/D2/D3/D6），其中 3 条独家（D2/D3/D6）——本轮独立贡献最高的单一视角。无 tension（与主审无分歧项）。

低置信一行带过（可审计不静默丢）：plan-eng PE-4（置信 45，已并入 D7）、devex DX04-2（置信 50，已采纳 D14）、对抗镜A A5（置信 45，已并入 D10）——均随高置信同主题条目一并处置，无独立裁决遗留。

## 图与结构验证（design-diagrams）

- TG-18 测试覆盖图：tasks.md 在场，已随 D12 更新（4→6 组负例）✅
- 组件/依赖图：design.md 在场，已随 D1 更新（14×→15×）✅
- TG-25/BASE-29 scope-check 表：在场，已随 D16 补路径前缀 ✅
- 无缺失/过时图；本 change 无状态机/时序交互变更，不新增图。

## 度量锚（lens-metric · 草稿值，拍板回写时最终化〔SR-M〕）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="9" 采纳="7" 裁掉="1" defer="1" 独立="2" sev="致0/高1/中3/低3" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="8" 采纳="7" 裁掉="0" defer="1" 独立="3" sev="致0/高1/中2/低4" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="2" sev="致0/高0/中1/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="4" 采纳="2" 裁掉="2" defer="0" 独立="1" sev="致0/高1/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="3" sev="致0/高3/中1/低0" -->

（emitter `lens_metric_emit.py` exit 0 产出；分类正确性 / roster 完备性 / findings 誊写准确
仍是主 session 信任边界。defer 计数对应 Q1/Q2，拍板后按最终去向原地更新覆盖。）

## 信任边界与诚实声明

- 能力探针：host=claude 免探恒 available；`mirrors=` 为实际派出清单（6 子代理 + 1 voice），
  「机制活但主 session 自代镜」类假绿无机械守（§0.0 残余语义层）。
- `findings=N` 与合并池实收数的数值一致性是主 session 信任边界，非机械可验。
- voice stderr 未过出境 secret_scan：本报告只转录结构化字段（rc=0、findings=4、
  truncated=false），未搬运任何 stderr 文本。
- 站点↔任务记账：design-voice → 后台任务（`dispatch-manifest.tsv` 已落
  `.outside-voice/20260812T074951Z-kkwN8D/`，attempt_nonce=none，claude-host）；hr-tg 站点
  HR-TG∩=∅ 未派（declared-sites 公式一致）。

## 收敛口

**建议进设计 HARD-GATE**：16 条 amendment 已落盘且无一触及 memo 拍板决策本体（D1–D4 原样），
两条需拍板项（Q1/Q2）均为低成本增补、不阻塞主线。人过本报告勾 Q1/Q2 → 批准 → 拍板回写
（`ship-gate.design_approved` + `reviewed_sha` 同次写入报告头部 frontmatter；本报告与
amendment 属拍板前盘面变更，MUST 先 checkpoint 提交、以该提交 sha 为 `reviewed_sha`）。

## 拍板记录（人读行，拍板后回填）

- [ ] 设计门拍板：＿＿＿＿（日期 / 结论 / Q1、Q2 勾选结果）
