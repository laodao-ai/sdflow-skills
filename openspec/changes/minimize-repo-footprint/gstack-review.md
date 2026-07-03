# GSTACK REVIEW REPORT — autoplan（广审）· minimize-repo-footprint

> 生成：2026-07-03 · /autoplan 自动决策模式（无人交互，全部 AskUserQuestion 以 6 决策原则自动裁决并记录）
> 评审对象：`proposal.md` / `design.md` / `tasks.md` / `specs/spec-workflow/spec.md`
> 决策背景：`adr/0003`（分层 + grill-amendment）· `adr/0005`（dev/runtime checkout 分离）· `adr/0006`（机队锚定）· `CONTEXT.md`
> 四镜执行：CEO ✅ · Design ⏭️（按 autoplan Phase 0 规则跳过，见决策 A2）· Eng ✅ · DX ✅
> 声部：Claude fresh 子代理 ×3（CEO/Eng/DX）+ Codex outside voice（跨模型，gpt 家族）——共 4 独立声部 + 主审接地读码
> 执行偏离清单见文末「Deviations」。

---

## Phase 0：Intake

- **计划摘要**：把 opsx-project-init 的部署模型从「整 bundle（34 文件）复制进每个消费仓」改为「按内容性质分层」：规则（≈29）全局唯一（`~/.sdflow/workflow` 软链 / `workflow-path` 指针 → `opsx-project-init/assets/workflow/`），review UI 机械（tools/ 5 文件 + serve.sh + review.html）留仓，checkpoint-commit.sh 与新增 resolve-workflow.sh 全局装 `~/.sdflow/hack/`；skills 读规则改调确定性 resolver 脚本；存量仓迁移「停复制 + 陈旧遮蔽告警 + 绝不自动删」。
- **UI scope 检测**：对三份计划文档 grep autoplan 规定的 UI 词表（component/screen/form/button/modal/layout/dashboard/sidebar/nav/dialog）＝ **0 命中** → 无 UI scope，Phase 2 按规则跳过。
- **DX scope 检测**：CLI / SKILL.md / install / setup / agent 等词大量命中，产品本身是开发者工具、AI agent 是一等用户 → **DX scope 成立**。
- **主审接地读码**（实际核验过的代码事实）：
  - `setup.sh`（symlink 安装、所有权判断 47-62 行、孤儿清理、Windows copy+marker）
  - `opsx-project-init/scripts/init.py`（copy_bundle:91 / copy_review_tool:98 / copy_hack:132 / handle_config:165 / ensure_global_hooks）
  - `hack/checkpoint-commit.sh` 与 `opsx-project-init/assets/hack/checkpoint-commit.sh`（双副本并存）
  - `opsx-project-init/assets/workflow/` 实际 34 文件（tools/ 5 个、规则 ≈29，**含 `config.template.yaml`**）
  - `opsx-project-init/assets/snippets/{index-section,claude-section}.md`、`assets/hooks/change-review-stub.py:52`
  - 全仓 SKILL.md 规则读点 grep：`spec-review`(3) / `impl-review`(4) / `opsx-project-init`(自身)；`opsx-done` / recorders / `opsx-maintain` = **0**
  - `opsx-project-init/tests/test_init.py` 现有断言；`openspec/workflow/workflow.md` `[checkpoint]` 约定实测在 **line 59**（tasks 写 line62，已漂）

---

## Findings 总表（四镜 + 双声部合并裁决后）

严重度：高=实现前必须修入计划 / 中=实现期须处理 / 低=文档或后续。置信为主审复核后值。

| # | 问题 | 严重度 | 置信 | 来源（共识度） | 自动决策 |
|---|---|---|---|---|---|
| F1 | **读点清单系统性缺口**：`config.template.yaml`（context/rules 的 `@openspec/workflow/...` 引用，opsx:ff/propose 生成期规则注入）、`snippets/index-section.md`（INDEX 托管表全部链到 `./workflow/*.md`）、`snippets/claude-section.md`（CLAUDE.md/AGENTS.md 托管块引用规则路径）三个**部署产物**在新 init 消费仓全部悬空——生成阶段质量层**静默蒸发**，正是反静默守卫要防的形态。计划只盘了 SKILL.md 读点 | **高** | 9 | 主审 + Codex#4（跨模型共识） | 采纳 A5：三个产物改写为指向全局解析/resolver，新增 task 3.4；不恢复复制 |
| F2 | **init 直接崩**：`init.py handle_config` 从消费仓部署副本读模板（`tmpl = openspec/workflow/config.template.yaml`，init.py:168）；copy_bundle 只拷 tools/ 后该路径不存在 → `shutil.copyfile` FileNotFoundError | **高** | 10 | 主审 + Codex#3（跨模型共识，10/10） | 采纳 A6：handle_config 改读 skill 自身 `BUNDLE_SRC`，模板不再落仓；补回归测试 |
| F3 | **dev checkout dogfood 吃陈旧规则**：update 停复制规则后，源仓 dogfood 副本 `openspec/workflow/`（34 文件）不再被刷新；「先改 assets、再 update 推下游」约定断裂，local-first 命中的是**旧**副本——今天两处已存在正常 dev/release 时间差，改后差距只会单调扩大且无告警 | **高** | 9 | 主审 + CEO 镜 + Codex#1（跨模型共识） | 采纳 A7：dev checkout 提供 `update --dev`（整 bundle 刷新 dogfood 副本）或发布前 drift-fail 断言，二选一进 design §五 + 新增 task 5.6 |
| F4 | **resolver 接口契约未定义**：①cwd/--root 假设（子代理 cwd 会复位）；②退出码表（脚本缺失 127 / 全局缺失 / 用法错不可区分——pull 后未重跑 setup 时，127 会被 SKILL.md 误当"步3 降级"，本地明明有规则也被降级成通用评审）；③"用输出路径读规则"的根路径→子路径拼接无 before/after 范例；④步3 告警**文案样例缺失**（迁移告警有范例，这条更高频反而没有） | **高** | 9 | Eng 镜(F1/F2) + DX 镜(F2/F6) + 主审（三方共识） | 采纳 A8：task 3.1 前置"接口契约"子任务：`--root`（缺省 `git rev-parse --show-toplevel`）、退出码表（0=成功/2=用法/3=全局缺失）、SKILL.md 调用点先 `[ -x ... ]` 判脚本存在（缺失→"重跑 setup.sh"专属文案，**不与步3 共用降级路径**）、路径拼接示例、步3 文案样例（问题+原因+修法） |
| F5 | **部分残留语义未定义**：步1 谓词对"仓里只剩部分规则文件"（如有 spec-checklists/ 无 code-checklists/）是 any 还是 all 未钉死；any→impl-review 错误落本地读不到文件也不落全局 | 中 | 8 | Eng 镜(F3) + Codex#5 + 主审（三方共识） | 采纳：钉死 any-of=pin（整体一致，不混层）+ resolver 检出部分残留时输出专门告警（"副本不完整，删净跟全局或补全 pin"）；补 spec Scenario + 5.3/5.4 测试 |
| F6 | **canonical 建链无所有权检查 + 劫持不可见**：`ln -snf` 在目标为**真实目录**时会把链接放进目录内而非替换 → `test -d` 恒真但读不到规则，静默坏；多 clone 各跑 setup 时 canonical 最后写者赢且 setup 摘要不提示指向变更 | 中 | 8 | Eng 镜(F4/F5) + DX 镜(F7) + 主审（三方共识） | 采纳 A9：复用 setup.sh 既有所有权判断模式（非我方软链→跳过+告警）；setup 写 canonical 前读旧目标，指向变更时打印"canonical 从 X 改指 Y"；init/update 时预检 `~/.sdflow` 就绪并提示 |
| F7 | **无"当前生效规则来源"诊断手段**（local pin / 全局 / 悬空软链 / 从未安装不可区分） | 中 | 8 | DX 镜(F4) + Eng 镜(F8) + 主审 | 采纳 A9：resolver 加 `--explain`（打印来源层与路径，`readlink` 区分悬空 vs 未建）；opsx-maintain 顺带报告一行规则来源 |
| F8 | **文档间陈旧/不一致**：①spec 已钉「update MUST 告警」，proposal 开放问题 4 / task 4.2 仍写"触发点待定"；②开放问题 3 已被实测超越（opsx-done/recorders SKILL.md 读点=0，真缺口是 F1 三处）；③task 2.3 写 line62，实测 line59（行号写死会漂，应改为 grep `[checkpoint]` 定位）；④CLAUDE.md「改 skill 源码无需重跑 setup」在本 change 后失效（hack 脚本是**拷贝**、canonical 需 setup 建立），但 5.5 的"若涉及"措辞很可能漏掉该句 | 中 | 9 | 主审 + Eng 镜(F6/F11) + DX 镜(F1) | 采纳：收敛开放问题 3/4；task 2.3 去行号改锚文本；task 5.5 从"若涉及"改为**必改清单**（含 CLAUDE.md 常用命令段的 setup 重跑触发条件 + "升级后首次须重跑 setup 建 canonical"） |
| F9 | **降级策略未按调用方分类**：「全局缺失→降级通用评审」对 review 类合理，但对 mutating/terminal 流（未来 opsx-ship 编排、verify/archive 若接入规则）继续跑通用规则不安全，应快败 | 中 | 7 | Codex#6（单声部但性质关键） | 采纳：spec R-MRF-2 加一句"降级仅限 review 类调用方；mutating/terminal 调用方 MUST 快败并转发告警"（当下实际读点均为 review 类，此为前瞻护栏） |
| F10 | **checkpoint 三副本无权威源钉死**：`assets/hack/`（copy_hack 源）、仓根 `hack/`（dogfood 副本）、`~/.sdflow/hack/`（新全局）并存；tasks 未选定唯一源与另两处去留 | 中 | 9 | 主审 + Codex#8（共识） | 采纳：权威源=`assets/hack/`，setup 从 assets 拷；task 2.2 补"仓根 hack/ 去留"显式决定（建议保留 dogfood 但在 workflow.md 注明全局路径为准）；测试断言安装内容与源一致 |
| F11 | **发布时序窗口**：运行 checkout `git pull` 后 SKILL.md（软链，即时生效）已是"调 resolver"新版，但 `~/.sdflow/hack/resolve-workflow.sh` 须 setup 才落位——窗口期内全机所有消费仓命中 F4 的 127 分支 | 中 | 8 | Eng 镜(F9/F10) + DX 镜(F1/F3) + 主审 | 采纳：F4 的 127 专属文案即兜底；tasks 顶部加一句发布纪律"三改动面（setup/init.py/SKILL.md）同一次落地，pull 后须 setup" |
| F12 | 规则跟全局 HEAD 而 tools/ 冻结在上次 update 时点 → 双速版本偏差无守卫；另 CEO 镜的"全局规则变更无感知"同根（内容变了没人提示） | 低 | 7 | Eng/CEO 镜 | 记录：不阻塞；todolist——canonical bundle 内容 hash 变更时 setup/resolver 打一次性提示 + tools 兼容性说明 |
| F13 | task 6.1（issues.py 落点）无验收判据且与 Phase B 交叉，属范围蠕变 | 低 | 8 | CEO 镜 + 主审 | 采纳：6.1 收窄为"只做决定并记录（design/ADR），不实施" |
| F14 | opsx-ship 尚不存在（adr/0004 规划中）却被列入 R-MRF-2/task 3.2 必扫清单；opsx-done/recorders 实测读点=0 | 低 | 9 | 主审 + Eng 镜(F11)（共识） | 采纳：措辞改为"现存读点=spec-review/impl-review（已实测）；opsx-ship 落地时按 R-MRF-2 接入" |
| F15 | Windows 细节两处未定：指针文件路径格式（Git Bash POSIX vs 原生）；`.sh` 调用方式（应写明 `bash ~/.sdflow/hack/...`） | 低 | 6 | Eng 镜(F7) + Codex#9（共识） | 采纳：task 1.2/3.1 补"指针内容 = setup 所在环境的可读绝对路径，调用统一 `bash <路径>`"约定 + 一条格式测试；不为此改 Python 实现（首个 Windows 用户出现前不扩） |
| F16 | ADR-0003 Considered Options 缺"全局 + 版本化 pin（lockfile 式）"中间态的评估记录（未进候选集≠评估后否掉） | 低 | 7 | CEO 镜(F2/F6) | 采纳（仅文档）：ADR 补记该选项与否决理由（当前单人/小规模，成本不值；pin 模型为二元这一限制一并显式记录）。**不重开决策**（A4） |

**已裁掉 / 降级（反静默压制：连理由落档，供复核）**

- 〔裁掉〕CEO 镜 F1"痛点未量化，疑似架构洁癖，建议降级为 spike"——源仓 dogfood 时间差是 proposal 明写的一手观察，且本仓消费仓数量与漂移事实可由维护者直接确认，不构成阻塞前提；量化盘点作为实现期第一步顺手做（update 告警本身就会盘出残留数）即可，不值得为此挂起 change。
- 〔裁掉〕CEO 镜 F5"Windows 投入过早应砍"——与 proposal Stakeholders 明写的"双 agent + Unix/Windows 两平台兜"冲突，且 setup.sh **既有** Windows 分支（copy+marker），指针文件是维持既有平台承诺的最小增量，非投机性通用化。保留，但按 F15 收窄到约定+一条测试。
- 〔裁掉〕"resolver 每次 fork 有性能顾虑"——每次 skill 调用 O(个位数)，bash 冷启 <10ms，不成立。
- 〔裁掉〕"serve.sh/review.html 也应全局"——proposal Non-Goals 已显式拒绝，不重开。
- 〔降级→F16〕CEO 镜"规则版本化/回滚机制"——ADR-0003 已拍板接受失 pin + 留副本逃生口，重开违反既判力；只补 Considered Options 记录。
- 〔降级→F12〕CEO 镜 F3/F4"变更无感知 + 回滚手册"——单机个人场景下 blast radius 有限，hash 提示进 todolist，不阻塞。
- 〔登记→决策登记区〕Codex#2"legacy 仓永不迁移，应加显式 pin marker/宽限期"——与用户已拍板的"绝不自动删 + 留=pin（副本存在即声明）"方向相抵，且仅单声部提出（Claude 三镜均未挑战该方向），不构成 User Challenge。默认维持 ADR 方向；备选（pin marker 显式化）记入下方决策登记区供人工终审时一并过目。

---

## Phase 1：CEO 镜（策略与范围）

### 0A 前提拷问

| 前提 | 陈述/暗设 | 判定 |
|---|---|---|
| P-1 规则从不按仓定制（定制只在 config.yaml） | 陈述 | ✅ 成立——bundle 结构支持：领域差异走 config rules 选域清单，规则本体无仓际分叉 |
| P-2 latest-is-fine，失 pin 可接受 | 陈述且 ADR 拍板 + pin 逃生口 | ✅ 有意识取舍；CEO 镜指出其混淆"源头迭代快"与"消费方无版本安全"两命题——已以 F12（hash 提示）+ F16（限制显式记录）低成本对冲，不推翻 |
| P-3 「本机无外部消费者」（dev setup 临时劫持 canonical 无碍） | 陈述（adr/0005） | ⚠️ 前提真，但恢复动作靠人记得——F6 补可见性后闭合 |
| P-4 消费仓的规则读点已被完整枚举 | **暗设** | ❌ 不成立——SKILL.md 之外还有 config.yaml/@引用、INDEX 托管块、CLAUDE.md 托管块三处部署产物读点（F1，本审最大发现，跨模型共识） |
| P-5 弱档模型跑 prose 协议会静默跳步 | 陈述（adr/0006） | ✅ 成立且已脚本化应对；但"脚本怎么调"这层新 prose（拼接路径、判 127）同样要结构化——F4 即其应用 |

### 0B 既有代码杠杆 / What already exists

- `setup.sh` 已有幂等安装 + **所有权判断**（47-62 行）+ 孤儿清理 + Windows 分支——canonical 建链应**复用该模式**而非一行 `ln -snf`（F6 的修复来源）。
- `init.py` 已分 copy_bundle/copy_review_tool/copy_hack——分层部署是删代码+改源路径，非重写。
- `ensure_global_hook` 已示范"全局装 + 幂等"（借幂等部分，不进 settings.json）。
- `checkpoint-commit.sh` 无仓耦合，全局化零改动脚本本体。
- 复用判定：无重复造轮；resolver 是真空缺（现状 prose 读点散在 SKILL.md）。

### 0C Dream State

```
CURRENT                          THIS PLAN                        12-MONTH IDEAL
每消费仓 34 文件副本，        →  消费仓 ≈7 文件（tools+锚），   →  消费仓仅 openspec 本体；
update 显式采纳、易漂移           规则全局唯一跟 HEAD，             规则/工具全 resolver 化、
规则改动要逐仓推                  resolver 三步链 + 反静默守卫       来源可观测（--explain）
                                                                  + opsx-ship 编排层连续
```
方向与 12 个月理想一致（收敛真相源、机械活脚本化），无逆行。

### 0C-bis 替代方案表（对 ADR 三选项的复核）

| 方案 | 力度 | 风险 | 判定 |
|---|---|---|---|
| A 分层（选中）：规则全局 + tools 留仓 + hack 全局 | M | 中（迁移面广但有告警护栏） | ✅ 论证充分；tools 留仓省 serve.sh 重写属实 |
| B 维持全量复制 | S | 低 | 正确否掉：34 文件/仓 × N 仓漂移成本已被 dogfood 时间差实证 |
| C 纯激进（tools 也全局） | L | 高 | 正确否掉且留未来通道 |
| D（本审补挂）全局 + 版本化 pin（lockfile 式） | L | 中 | **未进过候选集**（F16）——补记 ADR；当前规模下否决合理，但须留痕 |

撤销提根（grill-amendment）实质是第五方案，论证成立——"唯一权威源"约定确实散在 SKILL.md×4/init.py/config.template/CHANGELOG，改动面属实；但 CEO 镜正确指出这是"藏住 smell 而非解决"——已按其建议把"assets 私有目录承载跨 skill 共享依赖"记入 Deferred/todolist，防共识流失。

### 0E 时序拷问（实现期第一天会撞的决定）

- HOUR 1：resolver 接口契约（F4）——现在钉死成本最低。
- HOUR 2-3：init.py 模板源路径（F2）——写第一个测试就撞。
- HOUR 4-5：三个 snippet/模板产物改写（F1）——不改则"新 init 仓跑通 opsx:ff"集成不了。
- HOUR 6+：dev checkout 同步机制（F3）——5.1 纪律段无机制支撑会写成空文。

### 6 维结论（CEO 镜原判 × 主审复核后）

| 维度 | CEO 镜 | 主审终判 | 说明 |
|---|---|---|---|
| 前提有效? | PARTIAL | PARTIAL | P-4 不成立（F1），余成立 |
| 对的问题? | PARTIAL | **YES** | dogfood 漂移是一手观察非洁癖；CEO 镜的量化诉求以"实现期顺手盘点"吸收 |
| 范围校准? | NO | **YES（修订后）** | F13 收窄 6.1、F15 收窄 Windows 后刚好；CEO 镜"该投未投"项已由 F4/F6/F7 补入 |
| 替代方案充分? | NO | PARTIAL | 方案 D 缺席属实（F16 补记）；不改变选型结论 |
| 外部风险覆盖? | NO | PARTIAL | F3/F4/F6 补护栏后主干闭合；blast-radius 感知进 todolist（F12） |
| 6 个月轨迹? | PARTIAL | YES | 与 opsx-ship / 机队锚定路线同向；返工点均已显形登记 |

---

## Phase 2：Design 镜 — 跳过（规则内跳过，非省略）

autoplan Phase 0 UI-scope 检测 = 0 命中，review UI 文件仅被搬运、内容不改。按「Phase 2 conditional — skip if no UI scope」跳过（决策 A2）。唯一 UI 相邻残差（告警文案的信息设计）归 DX 镜承载（F4 文案样例、F5 告警列文件清单 + "pin"加括注），未蒸发。

---

## Phase 3：Eng 镜（架构 / 边缘 / 测试 / 性能）

### Section 1 架构（ASCII 依赖图，含本审发现的遗漏边）

```
                     ┌─ 运行 checkout（canonical 锚点）─────────────┐
   setup.sh ──建──▶  │ ~/.sdflow/workflow ─软链→ assets/workflow/  │
     │               │ ~/.sdflow/workflow-path (Win 指针)          │
     ├──拷──▶        │ ~/.sdflow/hack/{checkpoint,resolve-workflow}│
     │               └─────────────────────────────────────────────┘
     │                          ▲ 步2 解析
 skills (SKILL.md, symlink 装)  │
     └─▶ resolve-workflow.sh ───┤ 步1: 仓内规则文件本体?
                                │ 步3: 全局也缺 → 非零退出+固定告警
 init.py ──只拷 tools/──▶ 消费仓 openspec/workflow/tools/
        ──serve.sh/review.html─▶ 消费仓 openspec/
        ──❌不再拷──▶ 规则 / hack/
 【遗漏边 F1】config.yaml(@规则路径)·INDEX 托管块·CLAUDE.md 托管块 ──▶ 悬空
 【断裂边 F2】init.py handle_config ──读──▶ 消费仓 workflow/config.template.yaml
 【无守卫边 F3】dev checkout openspec/workflow/ ◀─?同步?─ assets/workflow/
 【时序边 F11】git pull(SKILL.md 即时新) ≠ setup(resolver 落位) 窗口
```

- 组件边界总体干净：resolver 单入口、canonical 单间接层、bundle 权威源不动。
- 单点：canonical 软链（F6）与 resolver 脚本（F4/F11）。
- 隐藏复杂度（Eng 镜实证）：①"查规则文件不查目录"看似一行 `test -f`，实际含 any/all、部分残留、按 skill 类型差异三重判定（F5）；②平台判断在 setup 与 resolver 两脚本各写一份，无同步提醒（进 task 3.1 备注）；③canonical 所有权是 setup.sh 已解决过的同构问题，勿重踩（F6）。

### Section 2 代码质量

- checkpoint 三副本问题（F10）；`workflow.md` 行号锚（F8③）；resolve-workflow.sh 的**仓内源码落点未指定**（建议与 checkpoint 同居 `assets/hack/`，随 setup 装）——并入 F4 接口子任务。
- hack 脚本 Unix 侧"拷贝 vs 软链"与仓内"改源即时生效"心智不一致（Eng 镜 F6）——拷贝是 grill 有意选择（exec 位根治），保留拷贝，但文档例外须写明（并入 F8④）。

### Section 3 测试审（覆盖图）

```
CODE PATHS                                         覆盖(tasks 5.2-5.4)
resolve-workflow.sh
 ├─ 步1 完整本地副本命中                              [✅ 5.3]
 ├─ 步1 部分残留（any-of + 专门告警）                  [GAP → F5，补]
 ├─ 本地与全局同时存在 → 严格 local 短路断言            [GAP → 补显式断言]
 ├─ 步2 软链命中 / 指针命中                            [✅ 5.3 ×2]
 ├─ 指针/软链悬空（repo 被移动删除）→ 区分性诊断        [GAP → F7，补]
 ├─ 步3 缺失 = 非零退出 + 告警文案断言                  [✅ 5.3]
 ├─ 非项目根 cwd / --root 推导                         [GAP → F4，接口定后补]
 └─ Windows 指针路径格式                               [GAP → F15，补]
init.py
 ├─ init 后 workflow/ 只含 tools/、规则=0              [✅ 5.2]
 ├─ config.template 不落仓后 init 仍能生成 config       [GAP → F2 回归测试，必须]
 ├─ update 停复制规则 + 残留不删 + 告警                 [✅ 5.4]
 ├─ 干净 post-change 仓跑 update 不误触发告警（假阳性）  [GAP → 补]
 └─ update 对 tools/ 仍刷新（不因本地有 workflow.md 跳过）[GAP → 补显式断言]
setup.sh
 ├─ canonical 幂等 / 所有权冲突跳过+告警 / 指向变更提示   [GAP → F6，至少手测清单]
 └─ ~/.sdflow/hack 两脚本 exec 位 + 内容与 assets 源一致  [GAP → F10，补]
集成
 └─ 新 init 消费仓（无规则副本）跑通 spec-review 规则解析  [GAP → 成功指标2 的 verify 锚点，建议列入]
```
现 tasks 覆盖 7/17 路径；GAP 已逐条并入 F2/F4/F5/F6/F7/F10/F15 修订。

### Section 4 性能

resolver 每调用 1 fork + ≤3 stat，软链透明；无 N+1/缓存需求。**无问题**（已核数量级）。

### 失败模式登记表

| 失败模式 | 有测试? | 有守卫? | 用户可见? | 判定 |
|---|---|---|---|---|
| 全局 bundle 缺失 | ✅5.3 | ✅步3 告警 | 显式 | OK |
| 残留旧规则遮蔽 | ✅5.4 | ✅update 告警 | 显式 | OK |
| resolver 脚本缺失(127) | ❌ | ❌（误入步3 路径） | 误导性降级 | **F4/F11 critical gap** |
| 部分残留 | ❌ | ❌ | 静默错根 | **F5 须修** |
| config/INDEX/CLAUDE 读点悬空 | ❌ | ❌ | 生成期静默失守 | **F1 critical gap** |
| init 模板路径断 | ❌ | ❌ | init 崩（显式但必现） | **F2 须修** |
| canonical 被真实目录占位 / 被 dev 劫持 | ❌ | ❌ | 静默 | **F6 须修** |
| dev dogfood 吃陈旧规则 | ❌ | ❌ | 静默 | **F3 须修** |

（静默类 F1/F3/F5/F6 与本仓反静默元原则正面冲突，是 must-fix 定级依据。）

---

## Phase 3.5：DX 镜

- **TTHW（新消费仓从零到首次 spec-review 跑通）**：乐观路径改前≈改后（init→ff→spec-review 3 步，setup 顺路建 canonical）；**现实路径**（环境未就绪/升级未重跑 setup）从确定 3 步劣化为 5+ 步排障循环——F4（127 专属文案）+ F6（init 预检）+ F7（--explain）三补丁即为把现实路径拉回确定性的最小集（DX 镜与主审共识）。
- Pass 1 起步 8/10：setup 单命令幂等好形态；扣隐性全局态无自检（F7 补后 9）。
- Pass 2 错误信息 6/10：步3 文案只有约束无样例（F4④）；陈旧遮蔽告警应列具体残留文件清单 + "pin"首现加括注（F5 并入）。
- Pass 3 CLI 一致性 7/10：命名风格一致；退出码语义未定（F4②）。
- Pass 4 文档 6/10：F1 三个部署产物即消费仓文档面；F8④ CLAUDE.md 触发条件失效句必改；5.5 应指定落点（README 开发章节 + CLAUDE.md），非"托管区块措辞"泛指。
- Pass 5 升级路径 7/10：存量仓 opt-in 迁移成熟；toolkit 自身升级时序（F11）缺说明。
- Pass 6 心智模型 6/10：消费仓用户对三层拓扑透明（设计得当）；维护者侧"改规则 local-first 生效、改 skill 却要 setup-from-dev"反直觉，靠 F3 机制 + 5.1 纪律段落位。
- Pass 7 AI-agent-as-user 8/10："跑脚本、用路径、非零降级转发文案"对弱档无歧义（adr/0006 正确应用）；补 127 分支与拼接示例（F4）后 9。
- Pass 8 逃生口 9/10：pin=留副本，显式零配置。

DX 总分 **7/10**（F4/F5/F6/F7/F8 落地后预计 8.5+）。

---

## 双声部共识表

| 维度 | Claude 镜（3×fresh） | Codex | 共识 |
|---|---|---|---|
| 读点枚举完整性（F1/F2） | Eng 镜部分命中（F11 实扫读点）；主审全命中 | #3/#4 独立命中（conf 9-10） | **CONFIRMED——最高优先修** |
| dev dogfood 陈旧（F3） | CEO/主审命中 | #1 独立命中（conf 9） | **CONFIRMED** |
| resolver 接口/127/部分残留（F4/F5） | Eng F1/F2/F3 + DX F2/F6 | #5 命中部分残留 | **CONFIRMED** |
| canonical 所有权/劫持（F6） | Eng F4/F5 + DX F7 | 未提 | Claude 侧三声部一致，采纳 |
| 迁移模型（永不删=永久 pin） | 三镜均未挑战 | #2 建议 pin marker（conf 9） | **DISAGREE → 决策登记区** |
| 降级按调用方分类（F9） | 未提 | #6（conf 8） | 单声部关键项，采纳为前瞻护栏 |
| Windows 投入 | CEO 镜建议砍 | #9 建议收窄不砍 | DISAGREE → 主审裁：保留但收窄（F15），理由见已裁掉区 |
| 版本化 pin 选项缺席 | CEO F2（conf 8） | 未提（但 #2 同源） | 补记 ADR（F16），不重开决策 |

跨相位主题（2+ 相位独立出现，高置信信号）：
- **"反静默守卫自身留了静默窗口"**（F1 生成期蒸发 / F4 127 误降级 / F6 目录占位假命中 / F3 陈旧 dogfood）——四处同构，出现在 CEO/Eng/DX/Codex 全部声部。本 change 的核心卖点恰是反静默，修复集应作为一个主题统一验收。
- **"prose 协议下沉而非消失"**（F4 拼接示例 / 步3 文案 / 平台判断双实现）——adr/0006 的脚本化把三步链结构化了，但"怎么调脚本"这层新 prose 须同样钉死。

## 决策登记区（人工终审时一并过目）

| 议题 | 默认（本审已按此走） | 备选 | 两方后果 |
|---|---|---|---|
| 迁移模型：留副本即 pin（隐式）vs 显式 pin marker + 残留宽限告警（Codex#2） | **维持 ADR：留=pin，绝不自动删**，update 每次告警即持续提醒 | 加 `.workflow-pin` marker：无 marker 的残留在 resolver 运行时也告警 | 默认：老仓可能"告警疲劳"后永久滞留旧规则，但零迁移强制、安全红线干净。备选：迁移完成度高，但引入新文件约定 + 违背"副本存在即声明"的既定语义。推荐维持默认（单人场景告警可达性足够），若消费仓规模化再启用备选 |

---

## 决策日志 / Decision Audit Trail

| # | 阶段 | 决策 | 分类 | 原则 | 理由 | 被拒选项 |
|---|---|---|---|---|---|---|
| A1 | Phase 0 | 评审目标 = change 目录四件套 | Mechanical | P6 | 父任务显式指定 | — |
| A2 | Phase 0 | 跳过 Design 镜 | Mechanical | P3 | UI 词表 0 命中，autoplan 明文条件；残差归 DX | 强跑 7 passes（全 N/A） |
| A3 | Phase 1 | CEO 模式 = HOLD SCOPE | Taste | P5+P3 | 部署模型重构（refactor→HOLD 是 CEO skill 自身 default）；已 explore+grill+model-baseline 三轮收敛 | SELECTIVE EXPANSION |
| A4 | Phase 1 | 不重开"规则版本化/回滚" | Mechanical | P6 | ADR-0003 既判 + pin 逃生口在；只补 Considered Options 记录（F16） | 加版本化机制 |
| A5 | Phase 3 | F1 修复 = 三部署产物改写指向全局解析 | Taste | P1+P5 | 恢复复制与 change 目标自斥；改写三产物是完整修 | 部分规则回退复制 |
| A6 | Phase 3 | F2 修复 = handle_config 改读 BUNDLE_SRC | Mechanical | P5 | 一行源路径改动，顺向消灭一个部署副本 | 模板继续落仓 |
| A7 | Phase 3 | F3 = dev checkout `update --dev` 整 bundle 刷新（或发布前 drift-fail 断言），倾向前者 | Taste | P5 | 保住"先改 assets"单向流（与 CLAUDE.md 约定一致），机制兜底而非纪律兜底；软链方案 Windows dev 不成立 | ①反向流"先改 openspec/workflow 再回灌"（易漏回灌）②纯纪律段 |
| A8 | Phase 3 | F4 = 接口契约前置子任务（--root/退出码表/127 专属文案/拼接示例/步3 文案样例） | Mechanical | P1 | 0E 时序拷问 HOUR-1 项，现在钉成本最低；Eng+DX+主审三方共识 | 留给实现期 |
| A9 | Phase 3.5 | F6/F7 = 复用 setup 所有权模式 + 指向变更提示 + init 预检 + resolver --explain；不做独立 doctor skill | Taste | P3+P5 | 几行输出解决 90% 可见性；doctor 是新面积 | 独立 opsx-doctor |
| A10 | Phase 3 | F9 = spec 加"降级仅限 review 类，mutating/terminal 快败" | Mechanical | P1 | Codex 单声部但性质是安全护栏，成本一句话 | 忽略（等 opsx-ship 再说） |
| A11 | Phase 3 | F10 = 权威源钉 assets/hack，仓根 hack/ 去留显式决定 | Mechanical | P4 | 三副本即三漂移点，DRY | 维持含混 |
| A12 | 汇总 | F12/F16 转 todolist/ADR 补记；F13 收窄 6.1；F14/F15 改措辞收窄 | Mechanical | P3+P6 | 均非本 change 失败模式主干 | 扩进本 change |
| A13 | 汇总 | Codex#2 迁移模型质疑 → 决策登记区（不采纳为默认） | Taste | P6 | 与用户既定方向相抵且仅单声部；用户在人工终审有最终裁量 | 直接采纳 pin marker |

**User Challenge 核查**：无——没有任何"双模型一致要求推翻用户既定方向"的项（Codex#2 仅单声部；CEO 镜量化质疑已裁掉并留理由）。前提门（Premise gate）产物 = 0A 表，P-4 判不成立但属补任务而非改方向。

---

## NOT in scope（复核 proposal Non-Goals + 本审新增）

- 纯激进（tools 全局 + 重写 serve.sh）——ADR 拒绝理由仍成立。
- 按仓 pin 转默认 / 规则版本化——既判（A4/F16 仅补记录）。
- 移无关 skill（≈17）——切分正确。
- 改 config.yaml 契约结构——F1 修复只改 context/rules 段内路径措辞，不动键结构，不违反此 Non-Goal。
- issues.py 实施（F13 收窄后只留决策）。
- opsx-ship 接入（F14，随其自身 change）。
- 独立 doctor 命令（A9 拒绝，--explain 覆盖）。

## Deferred（建议转 todolist）

- F12：canonical bundle 内容 hash 变更一次性提示 + 规则/tools 双速偏差兼容说明。
- CEO 镜 F7：`opsx-project-init/assets/workflow` 作为跨 skill 共享依赖挂靠单一 skill 目录的提根债（含否决理由），防共识流失。
- resolver `--explain` 输出接入 opsx-done verify 报告作"规则来源"证据锚点（与 verify 联动，超本 change）。
- 全局规则改坏后的快速判断/回滚操作手册（CEO 镜 F4，单机场景低优）。

---

## 声部原文要点（全文见各子代理产出，此处为审计摘录）

- **Codex outside voice（9 条）**：#3 init.py config.template 断链（conf 10）、#4 snippets/config 断链（conf 9）、#1 dev dogfood 源错位（conf 9）、#2 迁移永久 pin（conf 9→决策登记）、#5 部分残留（conf 8）、#6 降级分类（conf 8）、#7 checkpoint PATH（已由 task 2.3 单点约定吸收，主审核验 `[checkpoint]` 定义行即调用真相源）、#8 checkpoint 双源（→F10）、#9 Windows bash 调用（→F15）。
- **Claude CEO 镜（7 条 + 6 维表）**：痛点量化（裁掉留理由）、版本化 pin 选项缺席（→F16）、latest-is-fine 命题混淆（→F12 对冲）、blast radius 手册（→Deferred）、Windows 过早（裁掉留理由）、二元 pin 限制显式化（→F16）、提根 smell 入债（→Deferred）。
- **Claude Eng 镜（11 条）**：接口契约（→F4）、127 不可区分（→F4）、部分残留（→F5）、canonical 所有权（→F6）、劫持无提示（→F6）、hack 拷贝心智例外（→F8④）、Windows 路径格式（→F15）、悬空诊断（→F7）、pull/setup 窗口（→F11）、发布顺序纪律（→F11）、读点实扫证伪清单（→F14）。另证实：本机生效 skills 来自 `~/.skills/laodao-skills` 运行 checkout（adr/0005 物理隔离实际生效）。
- **Claude DX 镜（8 条 + TTHW 表）**：CLAUDE.md setup 触发条件失效（→F8④）、步3 文案样例缺失（→F4④）、init 预检（→F6）、--explain（→F7）、告警列文件+pin 括注（→F5）、拼接示例（→F4③）、~/.sdflow 占用兜底（→F6）、文档落点绑定（→F8）。

---

## Deviations（无人环境执行偏离，全部显形）

1. AskUserQuestion 全部自动决策（父任务明令禁交互）。两个"永不自动决"例外的处理：①Premise gate → 0A 表完整产出，P-4 不成立仅追加任务、不改用户方向；②User Challenge → 核查为零（见决策日志尾注），Codex#2 以决策登记区形式留给人工终审。
2. gstack 遥测 / review-log / restore-point / brain 等宿主副作用步骤未执行（本审不改计划文件本体，产出为本报告单文件；per adr/0002 不依赖 gstack 内部机制）。
3. Codex 四相位声部合并为一次全域 outside voice（成本控制）；Claude 子代理按相位独立（CEO/Eng/DX 各一，fresh context），独立性保持。
4. plan-ceo-review 11-section 深审与 plan-devex-review 0A-0G 交互步按 autoplan skip-list 精神合并：与 Eng 镜重叠节由 Phase 3 承载，策略专属节（0A-0F/6 维）完整执行；DX 0A 人物画像以"维护者/消费仓/执行 agent 三类用户"推断替代交互确认。
5. Design 镜按 autoplan 自身条件规则跳过（非偏离，A2 重申显形）。
6. 报告落点 = 本文件（父任务指定）；Decision Audit Trail 亦落本文件而非 plan file。
7. plan-eng-review 的 test-plan artifact / TODOS.md / JSONL 聚合等 gstack 宿主产物以本报告对应章节（测试覆盖图 / Deferred 区）替代，未写 `~/.gstack/`。

## VERDICT

**方向通过，实现前须按本报告修订计划**。分层 + resolver 脚本化的选型经四声部检验成立（无一声部挑战选型本身）；但计划存在三处高严重度断裂——F1（三个部署产物读点悬空，生成期质量层静默蒸发）、F2（init 必现崩溃）、F3（源仓 dogfood 陈旧化无机制）——以及一组同构的"反静默守卫自身静默窗口"（F4-F7）。全部修复均已折成具体 task 修订（新增 3.4/5.6、扩 3.1 接口契约、收窄 6.1、5.5 改必改清单），无一项要求推翻既有 ADR 决策。

- 修订完成判据：F1-F11 各自的 task 落点在 tasks.md 可见；F5/F9 补入 spec Scenario/条款；F16 补入 ADR-0003 Considered Options。
- 决策登记区 1 项（迁移 pin 显式化）留人工设计 HARD-GATE 终审拍板。

**UNRESOLVED DECISIONS:**
- 迁移模型是否引入显式 pin marker（Codex#2，默认=维持 ADR"留副本即 pin"，见决策登记区）
