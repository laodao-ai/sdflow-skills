# Tasks: matt-workflow-integration

> 需求 ID 缩写：impl-orchestration spec = R1 手动路由 · R2 出 ticket 模式 · R3 gate 契约兼容 ·
> R4 执行模式 · R5 双轴审 · R6 机制裁剪 · R7 试点回退；spec-workflow delta = W1 阶段三管线可选(MODIFIED) ·
> W2 三段分流+衔接契约 · W3 grill 瘦跑。
> TG-18 **命中（spec-review 翻转 F6）**：route/拓扑 helper pytest + golden-file 回归（4.3/2.3）；其余验证为逐任务人工核验点 + 4.x 实测演练。

## 1. sdflow-implement skill 主体（P0）

- [ ] 1.1 新建 `sdflow-implement/SKILL.md` 骨架：双模式定义与路由信号（RUN_PLAN→出 ticket、CONTINUE_IMPL(done_tasks)→执行，skill 内不自判模式）、出 ticket**落盘即返回**铁律、description 写明「由 /sdflow-ship 按 gate 判定编排调用；含出 ticket+执行双模式」收窄触发（暂不写 disable-model-invocation，见 4.1）；与 2.1 共享**模式派发字面契约**（Skill args 串式样在 SKILL.md 与 ship 链序两处一字不差——spec-review-amendment F4）〔R2, R4, R6〕验证：SKILL.md 无「出 ticket 后继续执行」路径；frontmatter 无 disable-model-invocation
- [ ] 1.2 出 ticket 模式契约：3-6 张 tracer-bullet 垂直切片（行为级、禁预写代码/文件路径）、显式 Blocked-by、expand–contract 宽重构例外〔T120〕、头部 Global Constraints 逐字节 + R-ID 标注、ticket 内验收复选框、外衣文件名 `superpowers-plan.md` + `### Task N:` 标题 + frontmatter `impl-pipeline: tickets` marker；删 quiz-the-user（粒度争议走 T10；design.md「切片建议」节为建议输入，D9）；出 ticket 收尾**显式 checkpoint**（plan 单独提交，建立 B1 窗口锚——grill-amendment，见 design D3）〔R2, R3〕验证：模板样例过 ship_gate 三道校验口径（标题可数、无未闭合 fence、无重号）；收尾步含 checkpoint-commit 命令原文
- [ ] 1.3 执行模式契约：frontier 串行（禁并行 implementer）、fresh implementer/ticket（TDD at pre-agreed seams + 定期 typecheck + 末尾全套件 + 完成信号**后置双写**：实现期提交不带 task 标签、审后由执行模式补打标签+勾框，resume 续审语义——spec-review-amendment F1/Q3 草案甲）、状态词表四值处置（NEEDS_CONTEXT 盘面自答边界：design/specs/ticket 文本，答不出 T10/停；BLOCKED 统一 halt envelope 停并上抛 + blocker 落盘 report file git-tracked〔F7〕；DONE_WITH_CONCERNS 同 DONE 进双轴审、concerns 逐字附两轴〔F7〕）、report file/review-package 文件交接〔T125〕、Reviewer ⚠️ cannot-verify 项编排层亲自消解（预算上界：>3 文件或盘面不可解 → 退回 implementer〔F7〕）〔R3, R4〕验证：implementer dispatch 模板含完成信号时序说明与 report 路径契约
- [ ] 1.4 每 ticket 双轴审：Standards（仓标准+smell 基线+ **code-checklists/domains/<命中栈> 经 resolve-workflow.sh 注入 = dispatch 模板必填槽**）∥ Spec（ticket 文本验收+R-ID），各 <400 词封顶；Critical/Important → fix 子代理 + re-review 环；Minor → todolist defer（JSON 显式带 `"change"` 字段，防误挂）〔R5〕验证：模板槽位为必填而非 prose 叮嘱；无 warm final whole-branch review 步〔R6〕
- [ ] 1.5 裁剪边界显式声明节：无 warm 终审（冷层承接）、无 ledger（gate resume 承接）、无 task-brief（ticket 即 brief）——写明「为何没有」防未来好心加回〔R6〕验证：三项均有一句去向说明

## 2. ship 接入 + config 键（P0）

- [ ] 2.1 `sdflow-ship/SKILL.md`：:3 description 实现段表述管线中性化；:29 链序 RUN_PLAN/CONTINUE_IMPL 改条件路由（首跳读 config 键、续跑读 plan marker、缺省/非法/无 marker 一律 superpowers）+ 试验期权威声明「此二态 skill 路由以链序为权威，gate next 串仅信息性」〔R1, W1〕验证：路由三跳全为确定值判断，无「模型判断哪个管线合适」类措辞；其余链序段零改动
- [ ] 2.2 `sdflow-init/assets/workflow/config.template.yaml` + 本仓 `openspec/config.yaml`：增 impl-pipeline 可选键注释段（沿 model-tiers 覆盖段风格：缺省勿填、留空即 superpowers）〔R1〕验证：`python3 sdflow-init/scripts/init.py` lint_config 对含/不含该键的 config 均放行（init.py:295-299 不拒未知顶层键，回归确认）；键不注入存量仓
- [ ] 2.3 路由与 frontier 机械层〔spec-review-amendment F4/F8〕：`sdflow-implement/scripts/` 增 stdlib-only route helper（config 键 enum 读取 + marker 解析 + **非法/重复 marker → 停**）与 Blocked-by 拓扑 helper（next-ready 计算）+ pytest（路由矩阵：缺失/空/合法/非法/重复/引号值；拓扑：环/自环/缺依赖）；PIPELINE_RECEIPT 一行输出〔R1, R4〕验证：tests 全绿；helper 零依赖、不读不改 ship_gate.py

## 3. mainflow 规则（P1，全部改 assets 权威源）

- [ ] 3.1 `sdflow-init/assets/workflow/workflow.md` 阶段一：图（:13-21）与 explore 行（:68）改三段分流（清晰→ff / 单 session 模糊→explore / 超单 session 大雾→wayfinder chart），含 wayfinder 缺装→explore 显式降级〔W2〕验证：三档判据**事中可观察**（已跨 session/跨天/经历 /clear 仍未收敛才切 wayfinder——spec-review-amendment F11，禁「事前预估轮数」措辞）
- [ ] 3.2 `sdflow-init/assets/workflow/ff-generation-constraints.md`：增 wayfinder→ff 衔接契约节（条件 = change 源于 wayfinder map）——ff 起手逐区读 map（Destination→proposal 动机+D-5；Decisions-so-far **逐 ticket zoom 决议全文**；Out-of-scope→D-3）+ TG 判命中前置 chart 写 map Notes + proposal 回链 map；另增**独立**切片建议条款（条件 = 仓 `impl-pipeline: tickets`：design 决策区 MAY 含切片建议节，出 ticket 消费语义 = 建议非契约——D9 grill 拍板，勿与 wayfinder 节混条件）；**注入通道双落〔spec-review-amendment F2〕**：`openspec/config.yaml` `rules:` 段增契约规则文本 + workflow.md ff 调用行（:69）显式携带 map 路径（FF-0 先例=仅写约束文件不构成注入）；zoom 上界 ≤8 张 + design 决策段内联回链来源 ticket（机械 grep 锚）写进契约文本〔F11〕〔W2〕验证：与 rebuild-sdflow-roadmap-v2 的「roadmap 结晶不经 ff」边界互不侵入（D6）；两条款条件互不渗漏；`openspec instructions` 实测输出含新规则文本
- [ ] 3.3 workflow.md grill 行（:70）派发 prompt 增瘦跑措辞：已决分支引 resolution 快速核对即过、新生成/未决照常死磕、MUST NOT 整跳〔W3〕验证：瘦跑仅限有 resolved ticket 对应的分支；无上游决议时全深度口径原样
- [ ] 3.4 workflow.md 阶段三行（:34/:74-75）加 config 键脚注（不改默认口径）；:82/:117 及 `sdflow-init/assets/snippets/claude-section.md:13` 禁 /clear 句并列 sdflow-implement，随后刷新本仓 CLAUDE.md 托管块（经 sdflow-maintain/init update 通道，勿手改托管块内部）〔W1, R4〕验证：grep 托管块与 assets 源一致

## 4. 实测（P1，消解假设）

- [ ] 4.1 disable-model-invocation harness 语义实测：临时 skill 设旗标 → 主 session Skill tool 调用是否被阻断，结果记入本 change 归档材料；若不阻断可选补旗标，若阻断维持不写（假设表②）验证：结论一句 + 依据
- [ ] 4.2 出 ticket→gate→执行最小演练：对演练 change（或试点首 change 前半）跑 出 ticket 落盘 → `ship_gate.py` 返回经三道校验的 CONTINUE_IMPL（done_tasks=∅）→ 执行一 ticket → 双写完成信号 → gate done_tasks 正确携带该 ticket 号〔R2, R3, R4〕验证：全程 gate 零改动零 UNKNOWN；失败则按假设表①降级并回炉 1.2/1.3
- [ ] 4.3 golden-file 回归测试〔spec-review-amendment F6/F5〕：committed 样例 ticket plan（frontmatter 单键 + 3 张 ticket + 验收框）进 `sdflow-ship/tests/`，断言 plan_task_ids/plan_unbalanced_fence/plan_has_duplicate_task/checkbox_done_ids 干净解析 + 边界 fixtures（header 内 Task 文本 / 悬空 fence / 重复 marker → 各按预期判）〔R3〕验证：pytest 全绿（先例 = test_producer_parser_contract）

## 5. 试点与判赢材料（P2）

- [ ] 5.1 试点选样与判赢通道：登记 3-5 个有逻辑面中型试点 change 候选（排除纯文档/琐碎类）；判据三条（retro impl Δ 方向下降 / 冷层 Critical 与 verify FAIL 不升 / 哨兵不恶化）与对照分桶口径写入 hand-off 判赢材料位；试验期 implementer 档位钉死 mid；**补〔spec-review-amendment F3a/F9〕**：PIPELINE_RECEIPT 留档与样本 marker 核对（误路由剔样）、NEEDS_CONTEXT 停摆率与阶段一上下文成本观测、每试点 SHIPPED 后先再生 retro 再选下一个、workflow-cost-optimization roadmap 补 Phase C 占位（目标句+雾区）〔R7〕验证：判据为定性人读、无数字阈值；receipt 与 retro 节奏写进判赢材料位
- [ ] 5.2 ≥1 消费仓缺省路径验证：不开键的消费仓跑一次阶段三，行为与本变更前一致（dogfood 盲区）〔R1, R7〕验证：该仓 RUN_PLAN 仍派 writing-plans

## 6. 同步与发布（P2）

- [ ] 6.1 README「Skills 列表」增 sdflow-implement 行（编排类）；docs/ 历史快照不回改，活文档全量表述同步显式留 Phase B（在 hand-off 记明）验证：README 与顶层目录一致
- [ ] 6.2 dev checkout 重跑 `bash setup.sh`（新增顶层 skill 建链接，adr/0005）；确认 `~/.claude/skills/sdflow-implement/` 与 `~/.codex/skills/sdflow-implement/` 生效；发布边界按 push→运行 checkout pull→立即 setup 纪律执行 验证：setup 输出无异常、无孤儿
- [ ] 6.3 测后还原与发布窗口〔spec-review-amendment F9/B1/B2〕：运行 checkout（~/.skills/sdflow-skills）重跑 `bash setup.sh` 还原全局 symlink（adr/0005 协议下半场）；CLAUDE.md 发布边界补「既有 SKILL 路由新增 skill」反向窗口句（pull 后链序即生效、新 skill 链接须 setup 后才存在）验证：`readlink ~/.claude/skills/sdflow-ship` 指回运行 checkout
