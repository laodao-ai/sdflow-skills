# add-sdflow-spec · Tasks

> 任务 ↔ 需求双向追溯：每任务尾标 〔SA-xx〕；SA-01~SA-13 全部被至少一个任务覆盖。
> checkpoint slug 格式：`task<N>-<desc>`（含横杠，防 TAG_RE 不匹配）。
> **三阶段推进，阶段间有验收门** [spec-review-amendment · 设计门 Q1]——同一个 change 内，但**阶段二是否启用取决于阶段二自己的实测结果**，不预先押注。

---

# 阶段一 · 可靠性（无 subagent；生成由主 session 亲写 = D2 的薄编排形态）

## 1. canonical 规则单一源同步（P0 · 不可 defer）

- [ ] 1.1 `sdflow-init/assets/workflow/generation-process.md` §四推荐流水线加分支：已装 `sdflow-spec` 的仓走单入口；未装沿用 `explore→ff→grill` 〔SA-11〕
- [ ] 1.2 `sdflow-init/assets/workflow/workflow.md` §三关键设计决策 2（G1）加「阶段一→阶段二」具名例外 + 两条依据（cache 按模型隔离 / 产审错档）；**MUST NOT 写「主审需冷视角」**（已被 G1 正面回答）〔SA-09, SA-11〕
- [ ] 1.3 `sdflow-init/assets/workflow/reference/quality-layering.md` 的 G1 相关条目（`:107`、检查清单 `:117`）同步该例外 〔SA-11〕
- [ ] 1.4 改源后跑 `gen_workflow_guide.py` 重生成 `WORKFLOW-GUIDE.md`；核验其阶段一段落已随源更新 〔SA-11〕
- [ ] 1.5 `openspec/specs/spec-workflow/spec.md:968-994` 两条既有 Requirement 声明新入口与其共存/路由 〔SA-11〕
- [ ] 1.6 `sdflow-init/assets/snippets/claude-section.md:118` 归属修正（superpowers → Matt Pocock skills 集合 `~/.agents/skills`），跑托管刷新机制同步本仓区块（**MUST NOT 手改块内**）〔SA-11〕
- [ ] 1.7 机械核验：`grep -rn "explore.*ff.*grill" sdflow-init/assets/workflow/` 的每处命中都已带分支说明；`grep -rn "全流程不用" ` 命中处已带例外 〔SA-11〕

## 2. SKILL.md 管线本体（P0）

- [ ] 2.1 `sdflow-spec/SKILL.md` frontmatter（name/description 触发面、`disable-model-invocation: true`）+ 通则托管块（纳入 sync 投放面，跑 `--apply`/`--check`）〔SA-01〕
- [ ] 2.2 相位 A 澄清指令：grilling 节奏（一次一问/附推荐/事实自查）、CLI 起手上下文核查、**重入探测**（SA-13）、提前收束的**禁止清单**（跨模块依赖未查清 / ≥2 方案未给推荐 / 目标态写不出）〔SA-01, SA-02, SA-03, SA-13〕
- [ ] 2.3 相位 B 拷问指令：锚点纪要主 session 亲笔（对话内呈现，与决策纪要的关系见 design BASE-24）、承重约束优先攻击、**停止信号最小充分条件**（每条约束须有证据锚）、**增量落盘**（约束站稳即追加写 memo）、ADR/术语惰性提议钩子 〔SA-03, SA-04, SA-10〕
- [ ] 2.4 相位 B 收敛点五步序：①`git status --porcelain` 工作树前置检查（脏则 halt）②**FF-0 三分支判定**（保护分支建 / 本 change 分支跳过 / 其它 feature 分支 halt 问人；`checkout -b` 失败则 fallback `checkout`）③`openspec new change` ④memo 定稿（含身份字段）⑤checkpoint 〔SA-05, SA-09, SA-13〕
- [ ] 2.5 相位 C 生成指令：起手核 memo（存在 + 必填非空 + **身份匹配**）→ **显式强制阅读清单**（design 读 proposal；specs 读 proposal+design；tasks 读三者——**MUST NOT 写「依赖产物」**，CLI 报告 design 与 specs 互不依赖）→ 自调 `instructions --json` + **最小 schema 断言** → 临时文件+原子替换 + **路径 canonicalization/containment** → **写后核验 status（存在态）+ `validate --strict`（合格态）** 〔SA-05, SA-12〕
- [ ] 2.6 终审指令：纪要↔产物一致性 + **design↔specs 互相一致** + 中间态判据（「砍掉的候选+理由」完全消失才算判断性偏差）；**memo 不并入 design.md**，design 的 Decisions 只留指针 〔SA-04, SA-06〕
- [ ] 2.7 降级阶梯与诊断契约段：亲查/亲写阶梯 + **每条降级报告含 problem+cause+fix** + 外部检索退避与错误分类（429/5xx 一次带 jitter 重试；认证/schema 立即 fail-closed；确认替代路径不复用同一故障依赖）〔SA-08〕
- [ ] 2.8 出口序列段：原样贴 `/clear → 换档 → /sdflow-spec-review` + **只引两条理由**（cache 隔离 / 产审错档）；相位 checkpoint 节点 + **每次 checkpoint 前 `git status --porcelain` 核验** 〔SA-09〕
- [ ] 2.9 **体量控制**：降级阶梯表、ADR/术语最小模板、决策纪要字段 schema 外置到 `sdflow-spec/references/`；核验 SKILL.md 主体 `wc -l` ≤ 500 行 〔SA-01 · design D12〕

## 3. 本仓规范与文档（P1）

- [ ] 3.1 本仓 CLAUDE.md/AGENTS.md **非托管区**新增：`sdflow-spec` 使用路径 + 出口序列 + **四入口选择规则**（默认走 `/sdflow-spec`；何时用旧三步的具体判据，不是「适用场景」四个字占位）〔SA-09〕
- [ ] 3.2 删 `CLAUDE.md:192`「投放面 | 15 个 SKILL.md」的硬编码数字，改由 `sync_principles.py` 自报；扫 `grep -rn "15 个"` **不加 `--include` 限定**清理同族残留 〔SA-07〕
- [ ] 3.3 README「Skills 列表」新增 sdflow-spec + 顶部可复制 Quick Start；重跑 `setup.sh` 验证双 runtime 可见 〔SA-01〕

## 4. 阶段一验证（P0）

- [ ] 4.1 机械层全量：`/usr/bin/python3 -m pytest` 仓根全绿；`setup.sh` 幂等重跑 〔SA-07〕
- [ ] 4.2 **memo grep 门**（会红的检查，非人工抽查）：新增用例断言 `decision-memo.md` 缺失或必填小节为空时判红 〔SA-04〕
- [ ] 4.3 **`openspec validate --strict` 纳入机械核验**：新增用例断言半截/结构不合法产物被判未完成（构造一份截断的 design.md 喂进去，MUST 红）〔SA-05〕
- [ ] 4.4 dogfood 演练（薄编排形态）：对一个真实需求跑通 A→B→C 全程，核验：B 不可跳过、纪要字段完整且含身份字段、增量落盘生效、四件套 status+validate 全过、终审记录、出口序列原样呈现、checkpoint 锚落盘 〔SA-01, SA-04, SA-05, SA-06, SA-09〕
- [ ] 4.5 **故障注入**（原计划完全缺失）：工作树脏 / 在其它 feature 分支 / 分支已存在 / memo 陈旧（branch 不符）/ CLI 缺失 / CLI schema 断言不过 —— 六种情形各验一次处置正确 〔SA-05, SA-08, SA-13〕
- [ ] 4.6 `/clear` 无损抽检：dogfood change 上 `/clear` 后冷读产物，确认决策 why（含砍掉候选）全部可得。**报告须标注「N=1 自评，非统计显著」** 〔SA-04〕

> ✅ **阶段一验收门**：4.1–4.6 全过 + canonical 五处同步完成 ⇒ 方可启动阶段二。

---

# 阶段二 · 成本实验（引入 agent 定义与外派；起手先过实测门）

## 5. 起手实测门（P0 · 先于一切 producer）

- [ ] 5.1 🔴 **GO/NO-GO 实测**：真派一次 `subagent_type: sdflow-researcher`（trivial 检索任务），核验**确实走了 agent 定义路径**（非 fallback）。**NO-GO 即红并停在阶段一**——MUST NOT 用「失败则改验 fallback」把门变成恒绿 〔SA-07〕
- [ ] 5.2 档位注入实测：核验派发的 `model` 参数收到的是具体模型 id（非字面变量名）；档位解析走既有四步加固协议（unset → `[ -x ]` 预检 → 捕获退出码 → eval 后校验）〔SA-07 · design D4〕

## 6. agent 定义与托管机制（P0）

- [ ] 6.1 `sdflow-spec/agents/sdflow-researcher.md`：frontmatter（`model: inherit`、`effort: low`、tools 按 SA-12 S1/S2 处置）+ 正文角色纪律（结论+出处、材料不回传）+ **排他式 description** + 通则托管块占位 〔SA-07, SA-02, SA-12〕
- [ ] 6.2 `sdflow-spec/agents/sdflow-spec-writer.md`：frontmatter（`model: inherit`、`effort: medium`、`tools: Read, Glob, Grep, Bash, Write`）+ 正文（单产物生成、自调 `instructions`、读强制阅读清单、**遇未决判断返回结构化 blocker**、禁 AskUserQuestion）+ 排他式 description + 通则托管块占位 〔SA-07, SA-05, SA-02〕
- [ ] 6.3 SA-12 S1 落地：先实测 `tools` 的作用域参数语法（`Bash(git log:*)` 形态）；可用则收窄，不可用则在两个定义与 design 中如实改称「检索取向，`Bash` 非只读，属指令层非机械门」〔SA-12〕
- [ ] 6.4 SA-12 S2 落地：检索职责拆 `local-researcher`/`web-researcher`；外发查询接既有 secret scan（**复用** `host-adaptive-execution` 机制，MUST NOT 新造）〔SA-12〕
- [ ] 6.5 `hack/sync_principles.py`：新增 `AGENT_TARGETS`，用 **glob**（`sorted((REPO/"sdflow-spec"/"agents").glob("*.md"))`）发现、显式配 skill 味 `SOURCE`（**MUST NOT** 直接加进 `PROJECT_TARGETS`——那会注入项目味源）；跑 `--apply` 落块 〔SA-07〕
- [ ] 6.6 `hack/tests/test_sync_principles.py`：守卫覆盖 agents 文件；**新增定点用例**「往 `agents/` 放一个新 `.md` → `--check` 必红」（验证 glob 而非硬编码）；跑 `/usr/bin/python3 -m pytest hack/tests/` 全绿 〔SA-07〕
- [ ] 6.7 `setup.sh` 新写 `install_agents()`：Unix 逐文件 `ln -snf`；所有权守卫 = 只接管软链且 `readlink` 指向本仓，其余 skip 计入 `skipped[]`；**Windows 分支明写不铺 agents、走亲做路径并报一行** 〔SA-07〕
- [ ] 6.8 **`hack/tests/test_install_agents.py`（全仓首个 setup.sh 测试）**：`tmp_path` 当假 HOME 跑 `bash setup.sh`，断言 ①铺出软链且指向本仓 ②预置非本仓同名文件不被覆盖且进 `skipped[]` ③删源重跑清悬空链 ④重跑幂等 〔SA-07〕
- [ ] 6.9 SKILL.md dispatch 段改为 `subagent_type`（**MUST NOT** `agentType`）；agent 定义不可用时降级为**主 session 亲查/亲写**（MUST NOT 退通用子代理）〔SA-07, SA-08〕

## 7. 阶段二验证与 A/B 对照（P0）

- [ ] 7.1 机械层全量重跑：仓根 pytest 全绿（含 6.6/6.8 新用例）〔SA-07〕
- [ ] 7.2 **A/B 三路对照**：同一个**真实复杂 change**（非玩具需求）分别跑 legacy（旧三入口）/ thin（阶段一薄编排）/ subagent（阶段二），量**总** token、总美元、墙钟、人工返工量、阶段二 spec-review findings 数与采纳率。⏰ 8/31 前按 Sonnet 稳态价 $15/M 折算 〔SA-02 · proposal Success Metrics〕
- [ ] 7.3 **论证密度人工比对**（设计门 Q4 决议）：比对「纪要驱动的 design.md」vs「有完整拷问上下文的 design.md」的论证密度差距（砍掉候选的具体反例是否留存、承重约束的推导链是否完整），**而非只查字段填没填** 〔SA-02 · design D2〕
- [ ] 7.4 SA-12 S3/S4/S5 验证：网页内容中的指令性文本不被执行；`resolvedOutputPath` 越界/symlink 被拒；两个 agent 的 description 排他性生效 〔SA-12〕

> ✅ **阶段二验收门**：5.1 GO + 7.2 显示 subagent 路总成本与质量均不劣于 thin 路 ⇒ 保留外派并启动阶段三。
> ❌ 任一不达标 ⇒ **回退到阶段一薄编排形态**（D2 已声明其为合法交付形态），agent 定义作为未启用资产保留或删除，如实记入 hand-off。

---

# 阶段三 · 产品化（阶段二达标才做）

## 8. 分发与退役（P0）

- [ ] 8.1 全局 `~/.claude/agents/` 分发定案（设计门 Q3 决议）；design D3 已补反驳 `subagent-definitions-plan.md:303-308` 的理由，此处只需核验实际铺设行为与文档一致 〔SA-07〕
- [ ] 8.2 **旧入口 sunset 条件**：明确阈值（采用率 / 质量 / 成本），达标后 CLAUDE.md 与 canonical 文档不再推荐旧三步组合；未达标则删除 `sdflow-spec` 〔SA-11 · proposal Non-Goals〕
- [ ] 8.3 bundle 下游推广：`sdflow-init update` 把 canonical 改动推至消费项目；核验下游 `openspec/workflow/` 已获更新 〔SA-11〕
- [ ] 8.4 回滚演练：按 design Migration Plan 的正确顺序（先 uninstall agents → 再 revert → 重跑 setup）实跑一次，核验 `~/.claude/agents/` 无悬空软链残留 〔SA-07〕

## 9. 遗留登记（P2）

- [ ] 9.1 checkpoint 相位锚落地，核验 retro 的阶段一归因率提升（当前 `unknown` 桶占 56%）〔SA-09〕
- [ ] 9.2 未核项登记进 todolist：`disable-model-invocation` 在 Codex 宿主的语义（本仓已有该字段非直觉行为的实测：`archive/2026-07-10-matt-workflow-integration/impl-notes.md:3-14`）〔proposal Non-Goals〕
- [ ] 9.3 T132（spec-review 起手机械核验 grill 已收敛信号）—— 与本 change 不互斥、覆盖「人直接敲 `opsx:ff`」这条本 skill 够不着的路径，登记为后续独立工作 〔design D1〕

---

## 测试覆盖图〔TG-18〕

[spec-review-amendment：原覆盖图声称的覆盖超出任务实际提供的；本表逐格与任务对齐，**无机械覆盖的格子如实标注**]

| code path / 行为面 | 测试类型 | 任务 | 会红吗 |
|---|---|---|---|
| sync_principles 投放面（agents 块渲染 / 漂移 / **新增未纳入**） | pytest 机械守卫 | 6.6 | ✅ |
| setup.sh agents 铺设 / 不覆盖外部文件 / 孤儿清理 / 幂等 | pytest（假 HOME 实跑） | 6.8 | ✅ |
| `decision-memo.md` 存在 + 必填小节非空 | grep 门用例 | 4.2 | ✅ |
| 产物合格态（半截 / 结构不合法） | `openspec validate --strict` 用例 | 4.3 | ✅ |
| `subagent_type` 派发链路生效 | 实测门（GO/NO-GO） | 5.1 | ✅ |
| 档位注入为具体 id | 实测 | 5.2 | ✅ |
| 六种故障处置（脏树 / 错分支 / 分支已存在 / 陈旧 memo / CLI 缺失 / schema 不符） | 故障注入 | 4.5 | ✅ |
| SKILL.md 体量 ≤ 500 行 | `wc -l` 断言 | 2.9 | ✅ |
| canonical 五处同步 | grep 核验 | 1.7 | ✅ |
| 三相位管线行为（SA-01/03/06 的判断质量） | **dogfood 人核 · 无机械覆盖** | 4.4 | ❌ 人核 |
| 外派阈值遵守（SA-02） | **无验证 · 纯指令层**，靠阶段二 spec-review 兜 | — | ❌ |
| ADR/术语提议钩子（SA-10） | **无验证 · 纯指令层** | — | ❌ |
| 总成本方向（SA-02 外派是否划算） | A/B 三路实测（N=1 change） | 7.2 | ❌ 非统计显著 |
| 论证密度（纪要承载力） | 人工比对 | 7.3 | ❌ 人核 |
| SA-12 S3/S4/S5 安全面 | 行为验证 | 7.4 | 部分 |
