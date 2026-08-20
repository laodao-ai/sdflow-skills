# add-sdflow-spec · Tasks

> 任务 ↔ 需求双向追溯：每任务尾标 〔SA-xx〕；SA-01~SA-14 全部被至少一个任务覆盖。
> checkpoint slug 格式：`task<N>-<desc>`（含横杠，防 TAG_RE 不匹配）。
> **三阶段推进，阶段间有验收门** [spec-review-amendment · 设计门 Q1]——同一个 change 内，但**阶段二是否启用取决于阶段二自己的实测结果**，不预先押注。

---

# 阶段一 · 可靠性（无 subagent；生成由主 session 亲写 = D2 的薄编排形态）

## 1. canonical 规则单一源同步（P0 · 不可 defer · 共七处）

- [x] 1.1 `sdflow-init/assets/workflow/generation-process.md` §四（`:51` 起）推荐流水线加分支：已装 `sdflow-spec` 的仓走单入口；未装沿用 `explore→ff→grill` 〔SA-11, SA-14〕
- [x] 1.2 `sdflow-init/assets/workflow/workflow.md` §三关键设计决策 2（G1）加「阶段一→阶段二」具名例外 + 两条依据（cache 按模型隔离 / 产审错档）；**MUST NOT 写「主审需冷视角」**（已被 G1 正面回答）〔SA-09, SA-11〕
- [x] 1.3 `sdflow-init/assets/workflow/reference/quality-layering.md`（G1 第二处载体，`:107` 与检查清单 `:117`）同步该例外。⚠️ 其措辞是「无 `/clear`（G1）」，与 workflow.md 字面不同，**MUST 单独处理，别指望一条 grep 同时命中两处** 〔SA-11〕
- [x] 1.4 改源后跑 `gen_workflow_guide.py` 重生成 `WORKFLOW-GUIDE.md`；核验其阶段一段落（`:16` 起）已随源更新 〔SA-11〕
- [x] 1.5 `openspec/specs/spec-workflow/spec.md:968-994` 两条既有 Requirement 声明新入口与其共存/路由 〔SA-11, SA-14〕
- [x] 1.6 `sdflow-init/assets/snippets/claude-section.md`：①`:118` 归属修正（superpowers → Matt Pocock skills 集合 `~/.agents/skills`）；②托管块内「🔴 **ff 之后是 grill，不是 spec-review**」条款显式处置（加分支或声明保留 + 理由，**MUST NOT 无人提及**）。跑托管刷新机制同步本仓区块（**MUST NOT 手改块内**）〔SA-11〕
- [x] 1.7 `sdflow-init/assets/workflow/ff-generation-constraints.md:17`：FF-0「已在 feature 分支 → 跳过（幂等）」弱判据改为 SA-05 的三分支判定；同步 `sdflow-init/assets/hooks/ff0-branch-guard.py`（`:23,70` 只挡 main/master）〔SA-05, SA-11〕
- [x] 1.8 **机械核验（锚点须打得中真实结构）**：`grep -c "opsx:explore" sdflow-init/assets/workflow/generation-process.md` 命中处附近须出现分支关键词；`grep -rn "全流程不用" sdflow-init/assets/workflow/workflow.md` 与 `grep -rn "无 \`/clear\`" sdflow-init/assets/workflow/reference/quality-layering.md` **各自**命中且带例外说明。⚠️ **MUST NOT 用 `explore.*ff.*grill` 这类单行正则**——§四是跨行 ASCII 图，该模式实测零命中，是个永远不会红的空判据〔窄复核订正〕〔SA-11〕

## 2. SKILL.md 管线本体（P0）

- [x] 2.1 `sdflow-spec/SKILL.md` frontmatter（name/description 触发面、`disable-model-invocation: true`）+ 通则托管块（纳入 sync 投放面，跑 `--apply`/`--check`）〔SA-01〕
- [x] 2.2 相位 A 澄清指令：grilling 节奏（一次一问/附推荐/事实自查）、CLI 起手上下文核查、**重入探测**（SA-13）、提前收束的**禁止清单**（跨模块依赖未查清 / ≥2 方案未给推荐 / 目标态写不出）〔SA-01, SA-02, SA-03, SA-13〕
- [x] 2.3 **相位 B 起手三步**（前移，非收敛点）：①`git status --porcelain` 工作树前置检查（脏则 halt）②**FF-0 三分支判定**（保护分支建 / 本 change 分支跳过 / 其它 feature 分支 halt 问人；`checkout -b` 失败则 fallback `checkout`）③`openspec new change`（名由目标态定；**MUST NOT 暂定名后改名**——CLI 无 rename）〔SA-05, SA-13〕
- [x] 2.4 相位 B 拷问指令：锚点纪要主 session 亲笔（对话内呈现，与决策纪要的关系见 design BASE-24）、承重约束优先攻击、**停止信号最小充分条件**（每条约束须有证据锚）、**增量落盘**（约束站稳即追加写 memo 到 change 目录——落点由 2.3 保证）、ADR/术语惰性提议钩子 〔SA-03, SA-04, SA-10〕
- [x] 2.5 相位 B 收敛两步：④memo 定稿（补身份字段）⑤checkpoint 〔SA-04, SA-09〕
- [x] 2.6 相位 C 生成指令：起手核 memo（存在 + 必填非空 + **身份匹配**）→ **显式强制阅读清单**（design 读 proposal；specs 读 proposal+design；tasks 读三者——**MUST NOT 写「依赖产物」**，CLI 报告 design 与 specs 互不依赖）→ 自调 `instructions --json` + **最小 schema 断言** → 临时文件+原子替换 + **路径 canonicalization/containment** → **写后核验 status（存在态）+ `validate --strict`（合格态）** 〔SA-05, SA-12〕
- [x] 2.7 终审指令：纪要↔产物一致性 + **design↔specs 互相一致** + 中间态判据（「砍掉的候选+理由」完全消失才算判断性偏差）；**memo 不并入 design.md**，design 的 Decisions 只留指针 〔SA-04, SA-06〕
- [x] 2.8 降级阶梯与诊断契约段：亲查/亲写阶梯 + **每条降级报告含 problem+cause+fix** + 外部检索退避与错误分类（429/5xx 一次带 jitter 重试；认证/schema 立即 fail-closed；确认替代路径不复用同一故障依赖）〔SA-08〕
- [x] 2.9 出口序列段：原样贴 `/clear → 换档 → /sdflow-spec-review` + **只引两条理由**（cache 隔离 / 产审错档）；相位 checkpoint 节点 + **每次 checkpoint 前 `git status --porcelain` 核验** 〔SA-09〕
- [x] 2.10 **体量控制**：降级阶梯表、ADR/术语最小模板、决策纪要字段 schema 外置到 `sdflow-spec/references/`；核验 SKILL.md 主体 `wc -l` ≤ **600** 行 〔SA-01 · design D12〕

## 3. 本仓规范、入口规则与退役条件（P1）

- [x] 3.1 本仓 CLAUDE.md/AGENTS.md **非托管区**新增：`sdflow-spec` 使用路径 + 出口序列 + **SA-14 的四入口选择规则**（人读侧；AI 读侧由 1.1/1.5 承载）〔SA-09, SA-14〕
- [x] 3.2 删 `CLAUDE.md:192`「投放面 | 15 个 SKILL.md」的硬编码数字，改由 `sync_principles.py` 自报；扫 `grep -rn "15 个"` **不加 `--include` 限定**清理同族残留 〔SA-07〕
- [x] 3.3 README「Skills 列表」新增 sdflow-spec + 顶部可复制 Quick Start；重跑 `setup.sh` 验证双 runtime 可见 〔SA-01〕
- [x] 3.4 **旧入口 sunset 条件**〔窄复核订正：原挂在阶段三「阶段二达标才做」下，而阶段二失败恰是并存最久的分支 ⇒ 前移到阶段一〕：明确阈值（采用率 / 质量 / 成本），达标后 CLAUDE.md 与 canonical 不再推荐旧三步；**未达标则删除 `sdflow-spec`**。该条款**与阶段二成败无关，MUST 在阶段一落定** 〔SA-14 · proposal Non-Goals〕

## 4. 阶段一验证（P0）

- [x] 4.1 机械层全量：`/usr/bin/python3 -m pytest` 仓根全绿；`setup.sh` 幂等重跑 〔SA-07〕
- [x] 4.2 **memo grep 门**（会红）：新建 `hack/tests/test_decision_memo_gate.py`，断言 `decision-memo.md` 缺失或必填小节（拍板决策/承重约束）为空时判红 〔SA-04〕
- [x] 4.3 **`validate --strict` 纳入机械核验**：在 `hack/tests/test_decision_memo_gate.py` 同文件加用例，构造一份截断的 design.md 喂进 `openspec validate --strict`，断言 MUST 红 〔SA-05〕
  
  > ⚠️ **实况订正（archive 阶段随 delta 同步）**：`openspec validate --strict`（CLI 1.5.0）**只读 `specs/*/spec.md`** —— 截断的 `design.md` 恒判 valid（三方独立复现，`dist/core/validation/validator.js` 全文无 `design` 字样）。已交付的是**可达形态**：门锚在 delta spec（`test_truncated_spec_delta_is_caught_by_strict_validate`）+ `test_status_says_done_while_validate_says_red` 正面证明「存在态 ≠ 合格态」+ `test_validate_strict_only_covers_delta_specs` 把覆盖边界机械钉住。SA-05 措辞订正登记 **T232**。
- [x] 4.4 dogfood 演练（薄编排形态）：对**一个真实且有一定复杂度的需求**（非玩具；与 7.2 的样本要求同档）跑通 A→B→C 全程，核验：B 不可跳过、B 起手三步生效、纪要字段完整且含身份字段、增量落盘生效、四件套 status+validate 全过、终审记录、出口序列原样呈现、checkpoint 锚落盘 〔SA-01, SA-04, SA-05, SA-06, SA-09, SA-13〕
- [x] 4.5 **故障注入**：工作树脏 / 在其它 feature 分支 / 分支已存在 / memo 陈旧（branch 不符）/ CLI 缺失 / CLI schema 断言不过 —— 六种情形各验一次处置正确 〔SA-05, SA-08, SA-13〕
- [x] 4.6 `/clear` 无损抽检：dogfood change 上 `/clear` 后冷读产物，确认决策 why（含砍掉候选）全部可得。**报告须标注「N=1 自评，非统计显著」** 〔SA-04〕

> ✅ **阶段一验收门**：4.1–4.6 全过 + canonical 七处（1.1–1.8）同步完成 + 3.4 sunset 条件已落定 ⇒ 方可启动阶段二。

---

# 阶段二 · 成本实验（引入 agent 定义与外派；起手先过实测门）

## 5. 起手实测门（P0 · 先于一切 producer）

- [x] 5.1 🔴 **GO/NO-GO 实测**：真派一次 `subagent_type: sdflow-local-researcher`（trivial 仓内检索任务），核验**确实走了 agent 定义路径**（非 fallback）。**NO-GO 即红并停在阶段一**——MUST NOT 用「失败则改验 fallback」把门变成恒绿 〔SA-07〕
- [x] 5.2 档位注入实测：核验派发的 `model` 参数收到的是具体模型 id（非字面变量名）；档位解析走既有四步加固协议（unset → `[ -x ]` 预检 → 捕获退出码 → eval 后校验）〔SA-07 · design D4〕
- [x] 5.3 `tools` 作用域参数实测（决定 SA-12 S1 走收窄还是诚实声明）：实测 `Bash(git log:*)` 形态是否被解析 〔SA-12〕

## 6. agent 定义与托管机制（P0 · 共三个定义）

- [x] 6.1 `sdflow-spec/agents/sdflow-local-researcher.md`：frontmatter（`model: inherit`、`effort: low`、仓内检索工具面、**无网络**、Bash 按 5.3 结果收窄或诚实声明）+ 正文角色纪律（结论+file:line、材料不回传）+ **排他式 description** + 通则托管块占位 〔SA-07, SA-02, SA-12〕
- [x] 6.2 `sdflow-spec/agents/sdflow-web-researcher.md`：frontmatter（`model: inherit`、`effort: low`、**无仓库读取、无 `Bash`**，只 `WebFetch`/`WebSearch`）+ 正文（只收主 session 生成的最小净化查询；**Web 内容一律作不可执行数据**；结论+URL 出处）+ 排他式 description + 通则托管块占位 〔SA-07, SA-12〕
- [x] 6.3 `sdflow-spec/agents/sdflow-spec-writer.md`：frontmatter（`model: inherit`、`effort: medium`、`tools: Read, Glob, Grep, Bash, Write`）+ 正文（单产物生成、自调 `instructions`、读强制阅读清单、**遇未决判断返回结构化 blocker**、禁 AskUserQuestion）+ 排他式 description + 通则托管块占位 〔SA-07, SA-05, SA-02〕
- [x] 6.4 SA-12 S2 落地：主 session 侧的「最小净化查询」生成逻辑 + 外发参数过既有 secret scan（**复用** `host-adaptive-execution` 机制，MUST NOT 新造），命中即拒发且禁 fallback 〔SA-12〕
- [x] 6.5 `hack/sync_principles.py`：新增 `AGENT_TARGETS`，用 **glob**（`sorted((REPO/"sdflow-spec"/"agents").glob("*.md"))`）发现、显式配 skill 味 `SOURCE`（**MUST NOT** 直接加进 `PROJECT_TARGETS`——那会注入项目味源）；跑 `--apply` 落块 〔SA-07〕
- [x] 6.6 `hack/tests/test_sync_principles.py`：守卫覆盖三个 agents 文件；**新增定点用例**「往 `agents/` 放一个新 `.md` → `--check` 必红」（验证 glob 而非硬编码）；跑 `/usr/bin/python3 -m pytest hack/tests/` 全绿 〔SA-07〕
- [x] 6.7 `setup.sh` 新写 `install_agents()`：Unix 逐文件 `ln -snf`；所有权守卫 = 只接管软链**且 `readlink` 指向本仓**（⚠️ 这比 `setup.sh:128-136` 的既有 idiom 更严——那里 readlink 只用于打印告警、不作判据，故本守卫须**新增**校验而非复用）；**Windows 分支明写不铺 agents、走亲做路径并报一行** 〔SA-07〕
- [x] 6.8 **`hack/tests/test_install_agents.py`（全仓首个 setup.sh 测试）**：`tmp_path` 当假 HOME 跑 `bash setup.sh`，断言 ①三个定义各铺出软链且指向本仓 ②预置非本仓同名文件不被覆盖且进 `skipped[]` ③删源重跑清悬空链 ④重跑幂等 〔SA-07〕
- [x] 6.9 SKILL.md dispatch 段改为 `subagent_type`（**MUST NOT** `agentType`）；任一 agent 定义不可用时降级为**主 session 亲查/亲写**（MUST NOT 退通用子代理）〔SA-07, SA-08〕

## 7. 阶段二验证与 A/B 对照（P0）

- [x] 7.1 机械层全量重跑：仓根 pytest 全绿（含 6.6/6.8 新用例）〔SA-07〕
- [x] 7.2 **A/B 三路对照**：同一个**真实复杂 change**（非玩具需求）分别跑 legacy（旧三入口）/ thin（阶段一薄编排）/ subagent（阶段二），量**总** token、总美元、墙钟、人工返工量、阶段二 spec-review findings 数与采纳率。⏰ 8/31 前按 Sonnet 稳态价 $15/M 折算 〔SA-02 · proposal Success Metrics〕
- [x] 7.3 **论证密度人工比对**（设计门 Q4 决议）：比对「纪要驱动的 design.md」vs「有完整拷问上下文的 design.md」的论证密度差距（砍掉候选的具体反例是否留存、承重约束的推导链是否完整），**而非只查字段填没填** 〔SA-02 · design D2〕
- [x] 7.4 SA-12 S3/S4/S5 验证：网页内容中的指令性文本不被执行；`resolvedOutputPath` 越界/symlink 被拒；三个 agent 的 description 排他性生效 〔SA-12〕

> ✅ **阶段二验收门**：5.1 GO ∧ **7.4 全过（安全前提，不达标不得进阶段三，即便成本达标）**〔窄复核补〕 ∧ 7.2 显示 subagent 路总成本与质量均不劣于 thin 路 ⇒ 保留外派并启动阶段三。
> ❌ 任一不达标 ⇒ **回退到阶段一薄编排形态**（D2 已声明其为合法交付形态），agent 定义作为未启用资产保留或删除，如实记入 hand-off。**注意：3.4 的 sunset 条件已在阶段一落定，不受本门影响。**

---

# 阶段三 · 产品化（阶段二达标才做）

## 8. 分发与推广（P0）

- [x] 8.1 全局 `~/.claude/agents/` 分发定案（设计门 Q3 决议）；design D3 已补反驳 `subagent-definitions-plan.md:303-308` 的理由，此处只需核验实际铺设行为与文档一致 〔SA-07〕
- [x] 8.2 bundle 下游推广：`sdflow-init update` 把 canonical 七处改动推至消费项目；核验下游 `openspec/workflow/` 已获更新 〔SA-11〕
  
  > 回填 2026-08-20：`T239` 已于 2026-08 关闭为 **DONE**（"canonical bundle 已推给下游消费项目（`sdflow-init update` 已跑）；`add-sdflow-spec` 已 merge"），当时登记的残余已补做完成。
- [x] 8.3 回滚演练：按 design Migration Plan 的正确顺序（① 仍在新版 installer 上删除 `sdflow-spec/agents/` 源目录 + 重跑 setup 触发孤儿清理 → ② 再 revert → ③ 重跑 setup；`setup.sh` 无 uninstall 分支）实跑一次（正反两向对照），核验 `~/.claude/agents/` 无悬空软链残留 〔SA-07〕
- [x] 8.4 按 3.4 已落定的阈值判定旧入口是否进入 sunset；达标则更新 CLAUDE.md 与 canonical 的推荐措辞 〔SA-14〕

> ✅ **阶段三验收门**〔窄复核补：原阶段三无完成定义〕：8.1–8.4 全过 + 下游至少一个消费项目实跑 `sdflow-init update` 后阶段一流程可用 ⇒ 本 change 可进 `/sdflow-done`。
> ❌ **回退分支**〔T241 · 归档前订正：原阶段三验收门只有 ✅ 分支，回退形态下「可进 `/sdflow-done`」在票面无书面出处〕：阶段二 A/B 验收门已判**回退**（`impl-reports/task5-ab-comparison.md`）⇒ 8.2 按票面条件句不执行（见其下 ⛔ 注记），本 change 以**阶段一薄编排形态**交付；下游推广（bundle 七处 canonical 推消费项目）登记为独立后续项 **T239**（何时/由谁/怎么推，见 `hand-off.md`）。8.1/8.3/8.4 仍需全过（不受阶段二回退影响，见各自 SA 锚点）。此分支 ⇒ 本 change 同样可进 `/sdflow-done`。

## 9. 遗留登记（P2 · 与阶段二/三成败无关，阶段一即可执行）

〔窄复核订正：原挂在阶段三下，会随阶段二失败一起搁浅〕

- [x] 9.1 checkpoint 相位锚落地，核验 retro 的阶段一归因率提升（当前 `unknown` 桶占 56%，`openspec/retro/report.md:74`）〔SA-09〕
- [x] 9.2 未核项登记进 todolist：`disable-model-invocation` 在 Codex 宿主的语义（本仓已有该字段非直觉行为的实测：`archive/2026-07-10-matt-workflow-integration/impl-notes.md:3-14`）〔proposal Non-Goals〕
- [x] 9.3 T132（spec-review 起手机械核验 grill 已收敛信号）—— 与本 change 不互斥、覆盖「人直接敲 `opsx:ff`」这条本 skill 够不着的路径，登记为后续独立工作 〔design D1〕

---

## 测试覆盖图〔TG-18〕

[spec-review-amendment：原覆盖图声称的覆盖超出任务实际提供的；本表逐格与任务对齐，**无机械覆盖的格子如实标注**。窄复核订正了 canonical 一行的过度承诺]

| code path / 行为面 | 测试类型 | 任务 | 会红吗 |
|---|---|---|---|
| sync_principles 投放面（agents 块渲染 / 漂移 / **新增未纳入**） | pytest 机械守卫 | 6.6 | ✅ |
| setup.sh agents 铺设 / 不覆盖外部文件 / 孤儿清理 / 幂等 | pytest（假 HOME 实跑） | 6.8 | ✅ |
| `decision-memo.md` 存在 + 必填小节非空 | pytest grep 门（`test_decision_memo_gate.py`） | 4.2 | ✅ |
| 产物合格态（半截 / 结构不合法） | pytest + `openspec validate --strict` | 4.3 | ✅ |
| `subagent_type` 派发链路生效 | 实测门（GO/NO-GO） | 5.1 | ✅ |
| 档位注入为具体 id | 实测 | 5.2 | ✅ |
| `tools` 作用域参数是否可用 | 实测 | 5.3 | ✅ |
| 六种故障处置（脏树 / 错分支 / 分支已存在 / 陈旧 memo / CLI 缺失 / schema 不符） | 故障注入 | 4.5 | ✅ |
| SKILL.md 体量 ≤ 600 行 | `wc -l` 断言 | 2.10 | ✅ |
| canonical **workflow.md 与 quality-layering.md 两处**的 G1 例外 | grep 核验（各自独立模式） | 1.8 | ✅ |
| canonical 其余五处（generation-process / WORKFLOW-GUIDE / spec-workflow / claude-section / ff-generation-constraints） | **人核** —— 结构为跨行 ASCII 图或语义条款，无可靠单行锚点 | 1.1,1.4–1.7 | ❌ 人核 |
| 三相位管线行为（SA-01/03/06 的判断质量） | **dogfood 人核 · 无机械覆盖** | 4.4 | ❌ 人核 |
| 外派阈值遵守（SA-02） | **无验证 · 纯指令层**，靠阶段二 spec-review 兜 | — | ❌ |
| ADR/术语提议钩子（SA-10） | **无验证 · 纯指令层** | — | ❌ |
| 入口选择规则（SA-14） | **无验证 · 纯指令层**（人读侧 3.1 / AI 读侧 1.1+1.5 各落一份） | 3.1,1.1,1.5 | ❌ |
| 总成本方向（SA-02 外派是否划算） | A/B 三路实测（N=1 change） | 7.2 | ❌ 非统计显著 |
| 论证密度（纪要承载力） | 人工比对 | 7.3 | ❌ 人核 |
| SA-12 S3/S4/S5 安全面 | 行为验证 | 7.4 | 部分 |
