---
schema_version: 1
change: implement-workflow-optimization-2026-08-p5
branch: feat/implement-workflow-optimization-2026-08-p5
generated_at: 2026-08-12T15:38:07+08:00
decision_hash: 0a03512f44d0
---

# 决策纪要 · implement-workflow-optimization-2026-08-p5

## 目标态

压人类门与 context 成本：14 个 SKILL.md 考古层按 D1 界线清理（7 个超 500 行者重点）、
设计门报告拍板层补拍板三问并 anchor_lint 机验、sdflow-spec 提问分批条款固化、
T256 调研记录落盘（保持 OPEN，不实现）。

## 拍板决策

- **D1 T275 考古层界线：尽量删；确需保留者迁该 skill `references/` 旁文件（默认不加载），
  SKILL 正文末尾只留一行指针** — 依据：SKILL 触发时全文进 context，文末附录不省 token；
  `references/evolution-notes.md` 先例（sdflow-spec）默认不加载才真省。**砍掉的候选**：
  ① 同文件文末附录（人首选，经「token 不省」异议后改判）；② 三分保留制（(b) 指路锚
  /(c) 反面教训默认保留——被「尽量删除」的更强立场取代：逐条过删除测试，确需保留才迁）。
  人 2026-08-12 明确确认（Q1「同意」）。
- **D2 拍板三问只落设计门（spec-review 报告拍板层）** — 依据：设计 HARD-GATE 是全流程唯一
  人类门；code-review 无人门。**砍掉的候选**：两审都加（给无人读的报告加结构 = 样板税）。
  人 2026-08-12 明确确认（「同意」）。
- **D3 sdflow-spec 提问分批条款 fold 进本 change（呈现与拍板分离）** — 形态：修 A.1 + B.3——
  ① 互相独立且同主题的问题 MAY 一批问（≤4/批，对齐 AskUserQuestion 上限），每问仍必附推荐；
  ② **有依赖链的问题整链一起呈现**（链结构 + 前因后果 + 每环推荐，给出推荐的整链路径），
  人可一次拍整链或只拍链头；链头改判 ⇒ 下游按新前提重提（背景不重复）；仅当链头各选项
  导致完全不同的后续问题集（组合爆炸）时退回「只呈现链头 + 一句话预告各选项下游影响」。
  依据：本 change 拷问自身即实测样本——Q1 载体子问题因未随链头同呈现多耗一轮（先拍附录、
  异议 token、再改判）。**砍掉的候选**：① 不固化只当 session 习惯（下个 session 即失忆）；
  ② 依赖链一律串行（初版形态，被「拍链头时看不见下游影响」的实证推翻，人 2026-08-12
  提出修正）。人 2026-08-12 明确确认。

- **D4 T256 本 change 不实现，调研记录落盘、issue 保持 OPEN** — 依据：人 2026-08-12 拍板
  「不能只以当前 repo 状态判断——Claude 1M context 需求不迫切，Codex 仅 ~258K 可用、问题
  突出；先调研、先记录、本 change 不做」。调研已完成并追加进
  `openspec/issues/open/todo/T256.md`（2026-08-12 调研记录段）：双宿主均有 PreCompact
  机械落点（Codex hooks 引擎为新事实），未来方向推荐 merge 意图落盘化优先于 hook。
  **砍掉的候选**：WONTDO 纯关闭（被宿主不对称事实推翻——Codex 侧 auto-compact @90%
  是现实概率）。⚠️ roadmap 5.3 措辞（「评估收口→预判 WONTDO」）与本拍板有偏差，
  change 收尾回填 roadmap 时同步改为「调研记录 + 保持 OPEN」。

## 承重约束

- **C1 T256 的「只活在对话里」状态清单 = 仅 merge 意图** — 验证方式：读 ship SKILL 熔断
  条款与 merge 透传条款；**证据锚**：`sdflow-ship/SKILL.md:170`（熔断快照单 invocation
  持有 + fail-safe 快照缺失保守判无进展 + 「持久化下沉为长期 defer 项…撞三红线不做」明文）、
  `sdflow-ship/SKILL.md:162`（merge 意图从调用语透传）。
- **C2 T275 清理的机械爆破面 = 消费 SKILL.md 文本的测试** — 验证方式：全仓 grep；
  **证据锚**：`grep -rln 'SKILL\.md' hack/tests/*.py` 命中 11 个 + skill 侧 tests 命中 11 个
  文件（2026-08-12 命令输出）；另 `sdflow:principles` 托管块由 `hack/tests/test_sync_principles.py`
  机械守，清理 MUST NOT 触碰。
- **C3 anchor_lint 权威源可承载拍板层机验** — 验证方式：定位文件；**证据锚**：
  `sdflow-init/assets/workflow/tools/anchor_lint.py` 存在（D13 后消费仓无镜像，改权威源 +
  bundle 同步即全网生效）。
- **C5 Codex 宿主 compaction 现状（T256 调研的事实基座）** — 验证方式：本机 CLI 实查 +
  联网调研官方文档与权威技术文；**证据锚**：本机 `codex-cli 0.147.0`（`codex --version`
  2026-08-12 输出）+ hooks 面存在（`--dangerously-bypass-hook-trust` 旗标）；
  developers.openai.com/codex/hooks（事件表含 PreCompact/PostCompact/SessionStart
  source:"compact"）；getunblocked.com/blog/codex-context-window（400K 上限/~258K 可用/
  auto-compact 阈值钳 90%/压缩后回读 5 文件 50K 预算）。
- **C4 T101 残余缺口 = 拍板三问 + 拍板层机验（三层结构其余已由 adr/0041 交付）** —
  验证方式：对照 04 提案 §3.1 与 p4 归档报告实际结构；**证据锚**：
  `docs/sdflow-fable5/04-optimization-proposal.md:105-118`、
  `openspec/changes/archive/2026-08-12-implement-workflow-optimization-2026-08-p4/spec-review-report.md`
  （执行摘要/决策登记区/需拍板/自动决策/已裁掉/findings 总表结构俱在）。

## 接受的边角

- **分批提问的批内连带作废** — 概率低（分批仅限互相独立问题，误判独立性才发生）/影响小
  （当场撤回重问一句）/完美成本高（逐问依赖分析不值）；**为何接受**：D3 条款已把依赖链
  排除在分批之外，残余是误判边角。
- **T275 清理的 (a)删除/(c)保留 边界个案** — 逐条审计判断无确定性信号（语义残余），
  留档供人抽查；**为何接受**：机械爆破面（C2 的测试集）由全仓 pytest 兜底，语义面
  由审计留档 + code-review 冷层兜底，完美的机械判据不存在。
- **roadmap 5.3 措辞与 D4 拍板的偏差** — change 收尾回填时同步修正；**为何接受**：
  roadmap 是长期真相源但回填节奏按既有惯例在阶段收尾，中间态偏差窗口已在 D4 显式记录。

## 三镜代价

本次无 TG-23 命中（四条决策均为流程/编辑类，无大型方案选择；Q1 界线的载体选择已在 D1
记录依据与代价：references/ 旁文件默认不加载 vs 文末附录仍占 SKILL 加载 token）。
