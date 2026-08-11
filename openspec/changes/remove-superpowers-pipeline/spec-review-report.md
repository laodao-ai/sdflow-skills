---
ship-gate:
  design_approved: true
  reviewed_sha: b4d887dcf98c4fcad9c3c382a4a2844d97628478
---

# spec-review-report · remove-superpowers-pipeline

评审日期 2026-08-11 · host=claude（强档 opus 主审 / 中档 sonnet 镜 / 弱档 haiku 接地）· 单批 dispatch 7 面（广审双镜 strategy/plan-eng + devex 领域镜 + 对抗镜 ×2 + 接地镜 + design-voice 跨模型）· 全部独立跑完，无降级。

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="broad,domain,adversarial,grounding" -->
<!-- sdflow:step1-broad-review v1 mode="subagent" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-14,TG-18,TG-19,TG-20,TG-22,TG-23,TG-28" -->
<!-- sdflow:outside-voice v1 site="design-voice" host="claude" runner="codex" reason_code="ok" findings="4" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="design-voice" -->

## 触发判定

命中 TG-14（`impl_route.py`/gate 组件切除重构——组件依赖图已验存在且为目标态）、TG-18（tasks 测试覆盖图已验存在）、TG-19（P0-P2 已填）、TG-20（下游消费仓利益相关方已填）、TG-22（假设列表已填）、TG-23（深/浅收口 ADR + 三镜代价已填）、TG-28（devex：CLI 子命令删除 + 消费方可见 config 键退役 + skill 调用契约变更 → 开 devex 领域镜）。不命中 TG-01/02/03 栈领域清单（Markdown + 工具脚本）。HR-TG ∩ = ∅（脚本判定，见上锚）→ 不开 hr-tg site。

图表验证（design-diagrams，只验不重画）：TG-14 组件依赖图 ✅ 存在且描绘目标态（带 ✂ 删除标记）；路由行为 v_old/v_new 对照表 ✅；TG-18 测试覆盖图 ✅（tasks.md 末）。无缺失/过时项。

## 机械引用核

合并去重后 15 条（4 组跨镜会合），全部走 `findings_ref_check.py`：**15/15 pass**，无 `[ref-check]` 机械裁掉项、无 uncheckable、无 degraded。

---

## 决策登记区

### [自动决策]（高置信采纳，默认接受可覆盖；对应 amendment 已落盘标 `[spec-review-amendment]`）

| # | finding | 裁决理由 | 修订落点 |
|---|---|---|---|
| D1 | **F1（Critical，对抗镜1+design-voice 双命中）** 共享 fixture `approved_change` 硬写 `superpowers-plan.md`，63 处调用跨 7 个 gate 测试文件（test_gate_git_layer/freshness/namespace/impl_progress/tail/reviewed_sha/plan_resolver），全不在 memo C7 / tasks 退役名单——单名化后集体红 | 引文实核属实（test_gate_impl_progress.py:44）；这是实现期必然爆炸点，非概率 | tasks 2.2 + design Risks |
| D2 | **F2（High，对抗镜1）** `test_gate_closing_ticket.py:130,:160` 两条测试断言的正是要删的 grandfather 行为，design Risks 却把该文件整体当回归网 | 引文实核属实；「保留半场用例作回归网」表述需改为部分保留 | tasks 2.2 + design Risks |
| D3 | **F3（High，对抗镜1+design-voice 双命中）** `openspec/specs/yq-yaml-operations/spec.md` :61/:105/:142 三个 Scenario 描述被删行为（读 `impl-pipeline` 键、raise `RouteStop`），本 change 未开该能力 delta；三处不含 "superpowers" 字面串，Success Metrics 的 grep 判据扫不到 | 实核属实；归档后主 spec 将继续要求已删行为，是死 spec | proposal Modified Capabilities/Impact + 新增 `specs/yq-yaml-operations/spec.md` delta + tasks 4.5 |
| D4 | **F5（Medium，对抗镜1）** `ship_gate.py:1335` 紧贴 `PLAN_FILENAMES` 的说明注释块引用被删符号 `impl_route.resolve_pipeline`，design 只点名「文件头注释」 | 引文实核属实 | tasks 2.1 |
| D5 | **F6（Low，对抗镜1）** `CLAUDE.md:215` 非托管手写 prose「已开 `impl-pipeline: tickets` 的仓…」引用退役键，`sdflow-init update` 刷不到 | 实核属实（在托管区块之外） | tasks 5.4 |
| D6 | **F7（Medium，对抗镜2）** design Migration Plan 的窗口期描述机制不准：sdflow-ship/sdflow-implement 均为既存 symlink skill，`git pull` 即原子刷新 SKILL 与脚本；真实偏斜向量 = 长跑 session 已把旧 SKILL 读入 context、磁盘其间被 pull 更新。fail-loud 结论仍成立（route 缺席时 argparse 报 invalid choice、exit 2，响亮非静默） | 推演经读码证实；结论不变、机制表述改准 | design Migration Plan |
| D7 | **F9（Medium，对抗镜2+design-voice 双命中）** `docs/workflow-overview.md` / `workflow-map.md`(+html) / `workflow-console.html` / `criteria-mechanization-tracker.md` 自称「源码变更后需同步本文」的现役视图文档仍画旧路由，不在改动清单，也不落在 proposal 四类合法残留任何一类 | 实核属实；Success Metrics「仅剩合法残留」会因此判绿失真或实现期临时补——补齐是目标态完整性，非加宽 | tasks 5.5 + proposal Success Metrics |
| D8 | **F10（Medium，对抗镜2）** Success Metrics 第三条（ship 直连 e2e）是事后锚，本 change 内不可核验，与 sdflow-done「每 ✅ 需机械锚」纪律相撞 | 属实；处置 = verify-report 显式标注「事后锚，责任转交下一真实 change 首跑」而非留白/假绿 | tasks 5.3 注记 |
| D9 | **F11（Medium，strategy）** `sdflow-implement/SKILL.md:158`「与旧 writing-plans/subagent-dev 管线等价」比较句不在 tasks 3.2 四个具名短语覆盖内——具名短语式编辑必漏此类残句 | 引文实核属实；编辑指令升级为全文 grep 扫除式 | tasks 3.4（新增） |
| D10 | **F13（Low，plan-eng）** design 组件清单漏列 `openspec/INDEX.md`（tasks 4.4 已覆盖，纯清单完整性） | 属实 | design 组件清单 |
| D11 | **F14（High，devex）** `sdflow-implement/SKILL.md` 的 description frontmatter（触发条件唯一权威文本）显式锚定「仅当 config `impl-pipeline` 键取值为 tickets 时」，四件套未点名它为改动对象——键退役后该文案向读者暗示不存在的条件判断 | 引文实核属实（SKILL.md:7-8） | design 组件清单 + tasks 3.2 |

### [需拍板]（人工设计门勾选；每条已带推荐，人只拍板）

**Q1 · 单名 resolver 对遗留旧名文件的处置（F8，对抗镜2 + plan-eng 双命中，High/Medium）**
现设计：resolver 只探测 `tickets.md`，change 目录里若残留 `superpowers-plan.md`（历史上真实存在过的文件名），gate 视而不见 → 判 RUN_PLAN 重出票 → 双计划文件并存零提示。删掉的双存在 UNKNOWN 恰是防此类形态的唯一机械防线，且此边角未进 memo「接受的边角」清单（= 未被评估过，非评估后接受）。
- **选项 A（推荐）**：resolver 加一条低成本兜底——`tickets.md` 缺席 ∧ 存在 `superpowers-plan.md` ⇒ fail-closed 判 UNKNOWN + 提示人工清理（一个只读探测分支 + 一条测试）。
- **选项 B**：接受边角，在 design Risks/memo 显式登记。
- 三面后果：**系统镜**（主）——A 恢复「未识别形态就停」的 gate 既有纪律，分支只读、可随时删；B 在 fail-closed 体系里留一个静默通道。**用户镜**——A 真撞上时从「静默双文件」变「停下提示」；B 撞上时排障成本高。**开发循环镜**——A 多一条测试维护，极小。主次判定：系统镜为主（fail-closed 不变量完整性 > 极低概率的边角成本）。

**Q2 · `_yq` 删除还是保留（F4，对抗镜1 + design-voice 双命中，Medium；触碰用户已确认的 D2 保留名单，故上抛）**
实核：`_yq` 在 `impl_route.py` 仅有的两个调用点（`read_config_pipeline:197` / `read_plan_marker:266`）都在删除名单里，frontier/task-text 均不调用——memo D2/C7 的保留理由「tickets 基础设施」是**事实性错误**；真实保留成因只剩 `test_yq_wrapper_consistency.py` golden test 的成员表契约。
- **选项 A（推荐）**：随 route 半场一并删除 `_yq`（含仅为其服务的 import），`test_yq_wrapper_consistency.py` 成员表去 impl_route 条目——收口 change 不留零调用死代码（「一个 change = 一个完整阶段结果」）；yq delta（D3 已补）与此兼容。
- **选项 B**：保留 + 在 `_yq` 定义处注释「本文件内已无调用方，纯为 golden test 契约保留」（对抗镜1 原建议）。
- 三面后果：**系统镜**（主）——A 少一份 `_yq` 拷贝即少一个漂移面；B 留死代码 + 一条解释注释。**用户镜**——无感。**开发循环镜**——A 改 golden test 名单一行；B 未来读者仍会困惑一次。主次判定：系统镜为主。

**Q3 · adr/0033 加不加 Superseded-by 指针（F12，strategy，Medium；挑战 proposal Non-Goals 明文「不改既有 ADR 文本」，故上抛）**
仓内已有惯例：adr/0002 被 adr/0040 推翻时头部加了一行 `> **Superseded by [adr/0040]…**` 指针（正文逐字未动）——「加头部指针」与「历史记录照旧」在本仓先例里不矛盾。本 change 对 docs 加 obsolete 标注、对被完整推翻的 adr/0033 却零标注，内部不一致；后续读者读 0033 时其「选中方案」读起来仍像现行决策。
- **选项 A（推荐）**：adr/0033 头部加一行 Superseded-by 指针指向 adr/0042，0042 侧加一句 supersede 声明，两侧互指（对齐 adr/0002→0040 惯例）。
- **选项 B**：维持 Non-Goal 原样（adr/0042 单侧声明历史）。
- 三面后果：**系统镜**——无行为影响。**用户镜**（主）——A 防读者把已死决策当现行；B 读者需自行发现 0042。**开发循环镜**——A 两行成本。主次判定：用户镜（读者导航）为主。此条为 Non-Goals 范围调整，纯属人的拍板权。

**Q4 · 退役键要不要给下游一个废弃信号（F15，devex，Medium）**
`sdflow-init update` 保留消费仓 config 用户内容（init.py:570），`lint_config` 不校验退役键——异机仓若显式写着 `impl-pipeline: superpowers`，永远收不到「该键已失效」信号。proposal《假设》已做五问并接受（键退役使任意取值无行为差异）。
- **选项 A（推荐）**：接受现状，design Risks 补一句显式登记（零代码改动）——与通则③不加宽、④简化一致：提示价值仅限「人读困惑」，行为面零风险。
- **选项 B**：`lint_config` 加一条非阻塞提示「检测到已退役的顶层 impl-pipeline 键」（改 `sdflow-init/scripts/init.py` + 测试，改动面加宽到本 change 外的脚本）。
- 三面后果：**系统镜**（主）——B 加宽改动面 +1 脚本 +测试；A 零。**用户镜**——B 极低概率下有一次性提示收益。**开发循环镜**——B 多一处 lint 逻辑维护。主次判定：系统镜为主（不加宽 > 边角提示收益）。

### [已裁掉]

（无——15 条合并 finding 全部采纳或上抛，机械引用核也无裁掉项。反静默压制无适用对象。）

### 拍板记录（设计门）

**设计门已拍板批准，日期 2026-08-11。** Q1-Q4 均批选项 A：Q1=resolver 遗留旧名 fail-closed 兜底、Q2=`_yq` 随 route 半场删除（golden test 成员表同步）、Q3=adr/0033↔0042 Superseded-by 互指、Q4=接受现状 + design Risks 显式登记。四条 defer 项终裁转采纳（15/15 采纳、0 裁掉）。对应二次修订已按 ADR-7(b) 单独 checkpoint（`b4d887dcf98c4fcad9c3c382a4a2844d97628478`，即 frontmatter `reviewed_sha` 指向的被批准盘面）。

---

## 各镜 findings 与裁决

| ID | 命中镜 | 严重度 | 置信 | 一句话 | 裁决 |
|---|---|---|---|---|---|
| F1 | 对抗镜1 + design-voice | Critical | 高 | `approved_change` fixture 旧名硬编码，63 处 ×7 文件不在退役名单 | 采纳 → D1 |
| F2 | 对抗镜1 | High | 高 | closing_ticket 两条 grandfather 测试须退役，design 误当整体回归网 | 采纳 → D2 |
| F3 | 对抗镜1 + design-voice | High | 高 | yq-yaml-operations 主 spec 3 Scenario 成死 spec，grep 判据盲区 | 采纳 → D3 |
| F4 | 对抗镜1 + design-voice | Medium | 高 | `_yq` 保留理由是事实错误（调用方全在删除名单） | 上抛 → Q2 |
| F5 | 对抗镜1 | Medium | 高 | ship_gate.py:1335 注释引用被删符号 `resolve_pipeline` | 采纳 → D4 |
| F6 | 对抗镜1 | Low | 中 | CLAUDE.md:215 非托管 prose 引用退役键 | 采纳 → D5 |
| F7 | 对抗镜2 | Medium | 中 | Migration Plan 窗口机制描述不准（真实向量 = 长跑 session 缓存旧 SKILL） | 采纳 → D6 |
| F8 | 对抗镜2 + plan-eng | High | 高 | 遗留旧名文件被单名 resolver 静默忽略，唯一机械防线被删且未登记 | 上抛 → Q1 |
| F9 | 对抗镜2 + design-voice | Medium | 高 | 4 份现役视图文档仍画旧路由，不在任何清单 | 采纳 → D7 |
| F10 | 对抗镜2 | Medium | 高 | Success Metrics 第三条本 change 内不可核验（事后锚），须显式标注 | 采纳 → D8 |
| F11 | strategy | Medium | 中 | SKILL.md:158 比较句在具名短语编辑覆盖之外 | 采纳 → D9 |
| F12 | strategy | Medium | 高 | adr/0033 零标注与 adr/0002→0040 惯例及本 change docs 处置不一致 | 上抛 → Q3 |
| F13 | plan-eng | Low | 高 | design 组件清单漏 `openspec/INDEX.md` | 采纳 → D10 |
| F14 | devex | High | 高 | sdflow-implement description frontmatter 锚定退役键，未列为改动对象 | 采纳 → D11 |
| F15 | devex | Medium | 高 | 退役键无任何下游废弃信号点（update 保留用户 config、lint 不查） | 上抛 → Q4 |

**接地镜**：0 不符项——四件套全部代码事实（19 个符号、memo 行号锚及排他性断言、7 个测试文件、6 份 bundle 资产、specs/ADR/docs 引用）核验相符。唯一注记：memo C8 的 `:144` 行号指「试验期外衣文件名」Requirement（实起于 `openspec/specs/impl-orchestration/spec.md:142`），行号微漂、指称无歧义，不改文档。

**已核无发现清单**（各镜自报）：strategy——BASE-01/09/10/12/13/14/18/22/26/27；plan-eng——BASE-05/16/17/19/28；devex——DX-01/02/03 判 N/A 或已覆盖；对抗镜1——保留半场依赖闭包零依赖被删符号（`EXIT_ROUTE_STOP` 两半场共用、须保留，已确认无误删迹象）、C1/C5 重验为真；对抗镜2——归档路径与计划文件名无关（SHIPPED 短路读 verify-report）、delta REMOVED/ADDED 换名与主 specs 现行标题逐字比对无撞名无孤儿、回滚混合态无超出已登记风险的新爆点。

**outside-voice（跨模型 codex · gpt-5.6-sol）**：4 条 findings 全数与镜池同池裁决——3 条采纳（F1/F3/F9 会合）、1 条上抛（F4→Q2）。无 tension（voice 与主审无分歧项）。voice 对 F4 的建议（删除）与对抗镜1 的建议（保留+注释）不同向，已作为 Q2 的 A/B 两选项如实并列。

## lens-metric（metrics.enabled=true，emitter exit 0；拍板回写时随终裁更新〔SR-M〕）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="10" 采纳="10" 裁掉="0" defer="0" 独立="5" sev="致1/高3/中5/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="3" sev="致0/高1/中2/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="2" sev="致0/高1/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="0" sev="致1/高1/中2/低0" -->

（拍板终裁版〔SR-M〕：Q1-Q4 四条 defer 项经设计门批 A 全部转采纳，emitter 以终裁 verdicts 重算覆盖草稿值。）

残余信任边界声明（照契约）：分类正确性、roster 完备性、findings 誊写准确仍是主 session 信任边界；emitter 只保证给定输入的确定性归约。`findings=N` 与合并池实收数的数值一致性同为信任边界，非机械可验。本 skill 只落锚不聚合；复评/淘汰一律 `/sdflow-retro` 聚合后人决。

## amendment 摘要（改动处均标 `[spec-review-amendment]`）

- **proposal.md**：Modified Capabilities + Impact 增 `yq-yaml-operations`（D3）；测试面 bullet 增 fixture 迁移与 closing_ticket 部分退役（D1/D2）；Success Metrics 增视图文档收口判据（D7）。
- **design.md**：组件清单增 `openspec/INDEX.md` 行（D10）、sdflow-implement 行点名 description frontmatter（D11）、ship_gate 行纳入 :1329-1335 注释块（D4）、测试群行纳入 fixture 迁移（D1/D2）、docs 行扩为 5 份（D7）；Risks 修 closing_ticket 表述（D2）；Migration Plan 第 2 步改述真实偏斜向量（D6）。
- **tasks.md**：2.1/2.2 扩（D1/D2/D4）；新增 3.4 grep 扫除式收口（D9，覆盖 SKILL.md:158 与同类残句）；新增 4.5 yq delta 归档同步核验（D3，R11）；5.3 verify 事后锚标注（D8）；新增 5.4 CLAUDE.md:215 手工项（D5）、5.5 视图文档同步（D7）。
- **specs/yq-yaml-operations/spec.md**：新建 delta（D3）——R3/R5/R6 走 REMOVED + 换名 ADDED（与本 change 既有惯例一致），各删一个 impl-pipeline Scenario。

## 收敛口

**建议进设计 HARD-GATE**：11 条采纳项 amendment 已落盘，无 blocker 级未决项；Q1-Q4 均带推荐，人拍板即可（Q1/Q2 若批 A 会引入小幅 scope 调整——resolver 兜底分支与 `_yq` 删除——批后需按拍板回写协议把二次修订单独 checkpoint 再落锚）。批准 → `/clear` → `/sdflow-ship`。

> **已执行**：设计门批准（见上「拍板记录」），Q1-Q4 二次修订落盘于 `b4d887d`，frontmatter 机判锚已回写。下一步：`/clear` → `/sdflow-ship`。
