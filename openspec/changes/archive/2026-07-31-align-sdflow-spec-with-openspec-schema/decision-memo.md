---
schema_version: 1
change: align-sdflow-spec-with-openspec-schema
branch: feat/align-sdflow-spec-with-openspec-schema
generated_at: 2026-07-31T00:36:59+08:00
decision_hash: b151273f5d0a
---

# 决策纪要 · align-sdflow-spec-with-openspec-schema

> 状态：**相位 B 草稿**（`decision_hash` 留空 = 未定稿）。
> 上游背景与阶段切分见 [`openspec/roadmaps/openspec-1.7.0-followup/roadmap.md`](../../roadmaps/openspec-1.7.0-followup/roadmap.md)。

## 目标态

让 `sdflow-spec` 与 openspec CLI 1.7.0 的契约面对齐，并通过 project-local schema 把它从
「靠指令层自律才不被绕过的旁路」变成 **schema 层的默认路径**（含下游消费项目）。

## 拍板决策

> **D1 / D5 / D6 / D7 的共同理由已落成 ADR**：
> [`openspec/adr/0034-stage-one-entry-descends-to-project-local-schema.md`](../../adr/0034-stage-one-entry-descends-to-project-local-schema.md)
> （B.7 收敛前检查判定命中 ADR 三条件，人 2026-07-31 确认落盘）。

- **D1 采用 project-local schema（fork `spec-driven`），并随 bundle 推下游** — 依据：整批 10 条
  候选里只有这条改变 `sdflow-spec` 的**拓扑地位**，其余都是点状修补；下游的指令层约束比本仓更薄
  （本仓干活时 CLAUDE.md 全文在场，下游只有托管区块里一句「模型 MUST NOT 自行选 `opsx:ff`」），
  故下游更需要 schema 层引流。**砍掉的候选**：① 「只在本仓 dogfood 不推下游」——那是自加约束
  （通则③），且实测证明下发成本极低；② 「按 skill 边界切成两个 change」——E1 的价值只有铺到
  下游才兑现，拆开等于第一个 change 交付半成品。
- **D2 A 组（契约面对齐）与 E 组（schema 化）合并为一个 change** — 依据：两组改的是同一片区域
  （C.2 / C.3 / C.4 / 终审第 2 条）；分开做会产生确定的白做——先在前一个 change 加固「因为 CLI
  依赖图不密所以要写死超集」那段措辞，紧接着 E2 把依赖图修密，该段当场退役。
  **砍掉的候选**：分成两个 change 顺序做（代价：C.3 要改两次）。
- **D3 采纳 `skip_specs`** — 依据：**人 2026-07-30 明确拍板**，理由是开发中确实碰到过这种情况，
  **且是在项目 repo（下游消费项目）中**。**砍掉的候选**：不采纳（我原推荐，已被推翻）。
  🔴 推翻的原因是我**取样错了**：依据的是本仓 52 个归档 change 中只有 4 个无 specs delta
  （7.7%，其中 2 个还来自已废弃的 `plan-{topic}` 壳模式），但那是**源仓**数据——本仓是 skill 仓、
  指令即契约，几乎每个 change 都动契约；下游普通业务项目的纯重构 / 工具链 / 文档 change 占比高
  得多。拿 dogfood 分布估消费仓适用面 = dogfood 盲区。
- **D4 `skip_specs` 的判断发生在相位 B，相位 C 只认 CLI 自报的 `status`** — 依据：「够不够格声明
  标记」无确定性信号可锚，是纯语义判断；放进相位 C 会变成每个 change 都要过一次的自由裁量。
  **砍掉的候选**：让相位 C 自行判定某个 change 是否该 skip。
  〔判据写死到什么粒度**尚未定** —— 留给本相位继续拷问。〕
- **D5 委派形态 = 拦截 + 转人（模型提示、人发起）** — 依据：**人 2026-07-31 明确拍板**
  「模型提示要调用 sdflow-spec，具体由人来发起」。fork 出的 instruction 写成 STOP 式文案：
  本产物必须经 `/sdflow-spec` 生成、**MUST NOT 自己写**、请提示用户敲该命令然后停止。
  **砍掉的候选**：① 去掉 `sdflow-spec` 的 `disable-model-invocation` 让委派真能调起来
  ——被 C10 排除（破坏核心设计：相位 A/B 需与人一问一答）；② 新建一个可被模型调用的薄 skill
  做中转——与本方案效果等价却多一个组件，按通则④否掉。
  **不设「用户已明确要求走旧三步」的放行分支**：决定权本就在人手里（模型只提示、人发起），
  模型侧无需额外例外口子。
- **D6 E2 取「改 `requires` + design 在本 fork 内转无条件产物」** — 依据：`sdflow-spec` C.2 本就
  无条件生成四件套 ⇒ design 在本流程中从来不是可选的；改后 schema **反映真实流程**，而非让
  SKILL.md 去绕过 schema（这正是本 change 的精髓：把「指令层的绕过」变成「schema 层的声明」）。
  **砍掉的候选**：① 只改 `requires` 不动 design 条件性——被 C11 排除（留一条靠模型遵守兜底指令
  才不死锁的边）；② 砍掉整个 E 组只做 A1-A4 + skip_specs——**这是个站得住的选项**，被否是因为
  防绕过会继续只靠 CLAUDE.md 那句话、C.2 超集表继续维护。
  🔴 **拍板时的诚实记录**：E 组的账在拷问中**变薄了**——立项时以「E1 自动回流（机械）+ E2 纯机械
  收益」立起，实测后 E1 降为提示层（C10）、E2 缩为「少一段文字 + 概念一致」（因 D5 拦截后产物
  实际总由 sdflow-spec 路径生成，而该路径用 C.2 超集表，CLI 图密不密在实际产出路径上无影响）。
  代价（experimental + 漂移 + 版本门 + 托管目录）未变。人在知情此账的前提下仍选 (a)。
  **降级路径明确**：config 改一行 + 删目录即回退。
- **D7 委派段用定界标记包裹，`sdflow-spec` 在应用载荷前机械剥离** — 依据：剥离是**确定性操作**
  （字符串定界），符合分析基准 1「能机械化的优先机械化」；且 C.3 本就因 A1（glob 分支）要改，
  边际成本低。形态：`<!-- sdflow:delegation:start -->` … `<!-- sdflow:delegation:end -->`
  包住 STOP 文案，置于原始 instruction **之前**。
  🔴 **标记名 MUST NOT 含 `gate`**〔B.7 收敛前检查抓出的术语冲突〕：`openspec/CONTEXT.md` 已把
  **gate** 确立为**正确性门**的专名（fail-closed、零容忍——见「记录维护回写 vs 正确性门」词条
  及 HARD-GATE / Verify Gate），而本段按 C10 是**提示层、非机械保证**。叫 `delegation-gate`
  会把它伪装成正确性门，正是本仓术语纪律要防的。官方 `ff`/`propose` 不认识这对标记 ⇒ 照读全文
  ⇒ 被拦截；`sdflow-spec` 认识 ⇒ 剥离后拿到干净原文 ⇒ 不自我劝退。
  **砍掉的候选**：① 文案里写豁免条件（「若你正在执行 sdflow-spec 相位 C 则忽略本段」）——靠模型
  正确自我识别，fresh 子代理未必知道自己被谁编排，而此处机械够得着，按基准 1 否掉；
  ② 把委派放进 schema 的 `description` 字段靠字段分离隔开——官方明说 ff 读的是 `instruction`，
  且**我无实测锚**（未验证 artifact 自身 description 是否进 instructions 载荷），要走须先补测。
  ⚠️ 标记是**新增的共享字符串**：改它 MUST 先 `grep -rn`（不加 `--include` 限定），本仓已有
  `sdflow:principles` 同款先例。剥离逻辑写在 SKILL.md 属**指令层**的机械操作（非脚本），
  MUST NOT 表述为脚本级保证。
- **D8 下游切换前，机械补写在途 change 的 `.openspec.yaml`** — 依据：C13 把迁移风险收窄为
  「在途且无该文件」一处；补写是确定性操作（缺则补 `schema: spec-driven`、有则跳过，幂等），
  切换因此对在途工作**零影响**。🔴 **顺序不可颠倒——先补写、后切 config**：反过来则补写方
  读到的已是新 schema，写下去的值就是错的。
  **砍掉的候选**：① 只警告不补写（把机械活推给人，而人多半照提示补，不如直接补）；
  ② 不处理、赌下游切换时无在途 change（失败模式**静默**——`blocked` 不报错只是卡住，
  按通则④静默失败不该赌）。
- **D9 fork 出的 schema 名 = `sdflow-spec-driven`** — 依据：语义明确（它就是 spec-driven 的
  sdflow 定制版），且不与内置 `spec-driven` 撞名。
- **D10 `skip_specs` 的「够不够格」只写判据，不做机械门** — 依据：该判断**无确定性信号可锚**
  （「这个 change 有没有改变 spec 级行为」不存在可机械捕获的信号），按分析基准 1 属于机械够不着
  的**合法语义残余**；强行做门只会得到一个假绿的门。判据写进 bundle 供人读，判断发生在相位 B
  并落进 `decision-memo.md`（承 D4），相位 C 只认 CLI 自报的 `status`。
  ⚠️ **诚实边界**：这意味着「标记被滥用」没有机械防线，只有人读注记 + git 审计。

## 承重约束

- **C1 `instruction` 字段只有 `fork` 带，`schema init` 不带** — 验证方式：两条路径各生成一个
  schema 后读 `openspec instructions <artifact> --json`；**证据锚**：`schema init sdflow-test` 后
  `instructions design --json` 的 `instruction = None`；`schema fork spec-driven forked` 后
  `schema.yaml` 含 5 处 `instruction:`（行 9/62/226/286/346）。
  ⇒ **MUST 走 fork，MUST NOT 走 init**。
- **C2 schema 的 `requires` 边完全透传到 `openspec instructions`** — 验证方式：自定义 schema 里
  `design.requires = [specs]`，读其 instructions；**证据锚**：`dependencies = ['specs']`
  （内置 spec-driven 同一字段为 `[proposal]`）。⇒ E2「从根上修依赖图」成立。
- **C3 改后的 `instruction` 文案原样透传** — 验证方式：在 fork 出的 schema 的 proposal instruction
  首行插入 marker → `schema validate` → 建 change → 读 instructions；**证据锚**：
  `openspec schema validate forked` 报 `✓ valid`；`instructions proposal --json` 的 instruction
  首行 = `SDFLOW-DELEGATION-MARKER: 本产物 MUST 调 /sdflow-spec 生成…`。⇒ E1 成立。
- **C4 委派的可靠生效需 CLI ≥ 1.7.0** — 验证方式：读 CHANGELOG 版本分段；**证据锚**：
  PR #1405（fixes #777）位于 **1.7.0 的 Patch Changes** 段（`## Version 1.7.0` 在行 3，
  `## Version 1.6.0` 在行 254，该条在行 164）——「Custom schema instructions are no longer
  overridden by hard-coded spec-driven patterns」。⇒ 1.7.0 之前委派被硬编码套路**静默盖过**。
  🔴 且该 bug 的触发条件正是「custom schema 复用熟悉的 artifact 名」= 本 change 的 D 边界，
  ⇒ 在 <1.7.0 的下游上失效是**必然**而非概率 ⇒ 版本门 MUST 有。
- **C5 `config.yaml` 的 `schema:` 键即决定 `new change` 用哪个 schema** — 验证方式：写
  `schema: forked` 后裸跑 `openspec new change`；**证据锚**：输出 `Schema: forked`，无需 `--schema`
  标志。⇒ 下发面 = `config.template.yaml:17` 改一行 + schema 目录纳入 `copy_bundle`。
- **C6 `specs` 的 `resolvedOutputPath` 是字面 glob，不是文件路径** — 验证方式：读 specs 的
  instructions 与 status；**证据锚**：`resolvedOutputPath = "<abs>/…/specs/**/*.md"`；
  真实文件在 `artifactPaths.specs.existingOutputPaths`（已 glob 展开）。
  ⇒ C.3 步骤 3 的 allowlist **拦不住它**（字面 pattern 恰好落在 allowlist 内）。
- **C7 `skip_specs` 是零 delta change 的唯一合法出口** — 验证方式：造零 delta change 跑
  `validate --strict --type change`；**证据锚**：`✗ [ERROR] Change must have at least one delta`，
  且报错原文自指该标记（"set skip_specs: true … instead"）。有 marker 后：specs 的 status
  由 `ready` 变 `skipped`、tasks 的 `missingDeps` 由含 specs 变为仅 `["design"]`、validate 通过。
- **C8 `openspec schema *` 全系列自报 experimental** — **证据锚**：`openspec schema --help` 输出
  `Manage workflow schemas [experimental]`；`schema validate` 亦打印 `Note: Schema commands are
  experimental and may change.` ⇒ 接口可能变，是本方案主要风险面。
- **C9 hook / bundle 脚本是 copy 安装、非 symlink** — **证据锚**：`sdflow-init/scripts/init.py:581`
  `install_hook()` 把脚本拷进 `~/.claude/hooks/`。⇒ 改 `assets/` 下脚本后必须重装才生效
  （本 change 若动 `assets/hooks/` 或新增下发物，验收步 MUST 含重装）。
- **C10 🔴 `sdflow-spec` 模型唤不起——委派 MUST NOT 表述为「自动回流」** — 验证方式：读其
  frontmatter + 全仓 grep；**证据锚**：`sdflow-spec/SKILL.md:3` 为 `disable-model-invocation: true`，
  且 `grep -l "disable-model-invocation" */SKILL.md` **全仓只此一个**。
  ⇒ 官方 ff/propose 读到「invoke sdflow-spec」时**无法执行该调用**。
  🔴 **这部分证伪了 E1 的原始价值主张**：委派的实际效果不是「走哪条路都被自动导回来」，
  而是「把防绕过约束从**另一个文件的规定**（CLAUDE.md / 托管区块）挪进**模型当前正在读的任务
  载荷**」。后者仍是实质改善（instruction 是必读项、措辞可写 MUST），但**是提示层的加强，
  不是机械保证**——MUST NOT 在 proposal / design 里声称自动化。
  ⚠️ 该属性是**有意设计**：相位 A/B 要与人一问一答，模型自动唤起 = 模型自己跟自己拷问，
  正是本 skill 要防的失效。⇒ 「去掉 `disable-model-invocation`」不是可选项。
- **C11 🔴 改 `specs.requires` 含 `design` ⇒ design 由「条件产物」变为 specs 的硬前置** —
  验证方式：fork 后把 `specs.requires` 改为 `[proposal, design]`，建 change 只写 proposal，读 status；
  **证据锚**：`specs status=blocked missingDeps=['design']`，`nextSteps` 提示先写 design；
  而内置 `spec-driven` 的 design instruction 原文是 `When to include design.md (create only if
  any apply):` ⇒ **它本是可选的**。
  官方对该状态只有**指令层**兜底（ff：`Dependencies are enablers, not gates: if a required
  artifact is still blocked only because you skipped a conditional dependency, write it anyway`）
  ——**不是机械保证**。
  ⇒ E2 若只改 `requires` 而不动 design 的条件性，就是在 schema 里制造一个「靠模型遵守兜底指令
  才不死锁」的边。**MUST 配套把 design 在本 fork 内改为无条件产物**（`sdflow-spec` C.2 本就
  无条件生成四件套，改后 schema 才与真实流程一致）。
- **C12 🔴 委派段会被 `sdflow-spec` 自己读到 —— 自指死锁面** — 验证方式：读 C.3 协议；
  **证据锚**：`sdflow-spec/SKILL.md` C.3 步骤 1 = 「自取载荷（MUST NOT 由旁人转述）：
  `openspec instructions <artifact> --change "<name>" --json`」；步骤 2 把 `instruction`(str)
  列为必需字段。官方 1.7.0 ff 亦声明 instruction 是 `the authoritative guidance, even for
  familiar artifact names`。
  ⇒ 相位 C 生成每一份产物前都会读到 D5 那段「MUST NOT 自己写、去叫 `/sdflow-spec`」——
  **而它就是 `/sdflow-spec`**。
  ⚠️ **诚实定级**：C.3 明文要求「作为生成约束应用」的是 `context` / `rules` 两个字段，
  `instruction` 只被断言存在、未明文要求遵守 ⇒ 这是**高概率风险，不是确定性死锁**。
  但概率高（instruction 是载荷主体且官方定义为 authoritative）、影响大（相位 C 卡死或
  自我劝退）、防御成本低 ⇒ 按通则④该防。
- **C13 change 的 schema 钉在自己的 `.openspec.yaml` 上；缺该文件才跟 config 走** —
  验证方式：分别用 `--schema` 显式指定、靠 config 默认、以及无 schema 键三种方式建 change，
  再切 config 后读 status；**证据锚**：① 靠 config 默认建的 `default-schema-test/.openspec.yaml`
  内容为 `schema: forked`（⇒ **只要 config 有 `schema:` 键，新建 change 都自动钉死**）；
  ② 早期无该文件的 `100-numeric-test`，切 config 到 `forked` 后 `status` 报
  `schemaName = forked` 且 `specs` 由 `ready` 变 `blocked`——**被按新 schema 重新解读**；
  ③ 本仓 52 个归档 change 中 **45 个有** `.openspec.yaml`、7 个（早期）无；
  ④ 本仓当前唯一在途 change 记的是 `schema: spec-driven`。
  ⇒ **迁移风险面收窄为一处**：切换时刻**在途且无 `.openspec.yaml`** 的 change。
  归档件不受影响（CLI 不再 status/validate 它们）；本仓无此情况，**下游可能有**。
- **C14 fork 的 `generates` 路径也 MUST 与内置一致，不只是 artifact id** — 验证方式：读 C.3
  路径净化条款；**证据锚**：`sdflow-spec/SKILL.md` C.3 步骤 3 的 allowlist 是**硬编码字面量**
  ——`proposal.md` / `design.md` / `tasks.md` / `specs/**/*.md`。
  ⇒ D1 边界 2「保留四个 artifact id 不变」**不足**：若 fork 改了任一 `generates` 路径，
  路径净化会当场 fail-closed 拒写。边界 2 MUST 扩为「id 与 `generates` 路径**都**保持不变」。

## 接受的边角

- **fork 快照漂移无机械门** — 上游 `spec-driven` 的 instruction / 模板日后更新，本仓 fork 不会
  自动跟，且没有任何东西提醒它落后。概率：中（上游活跃）；影响：小（fork 停在旧版 = 退化到今天
  的状态，不会更糟）；完美成本：要做「上游 schema 指纹比对」的机械门，成本远高于收益。
  **为何接受**：通则④——影响可控且降级安全，记 todo 而非现在解决。

## 三镜代价

**命中 TG-23**（本 change 含难逆转的架构选择：引入 project-local schema 并推下游）。

- **系统镜**：新增 `openspec/schemas/<name>/` 一个托管目录 + 一条 CLI 版本门；本仓与所有下游从
  内置 `spec-driven` 切到 fork 副本，**回退需改 config 一行 + 删目录**（可逆）。依赖 CLI
  experimental 接口（C8）。收益：`sdflow-spec` 的 C.2 写死超集表可退役，终审第 2 条降为兜底。
- **用户镜**：走 `/sdflow-spec` 的路径**无感**；变的是走 `/opsx:ff` 的人会被 instruction 委派
  导回 sdflow-spec。下游 CLI <1.7.0 时静默降级为今天的行为（fail-loud 报一行）。
- **开发循环镜**：多一份要维护的 fork（漂移成本见「接受的边角」），但它与 `tools/` 同构地纳入
  `copy_bundle` 托管刷新，纪律一致（改源 → `sdflow-init update` 推下游，禁止只改下游）。

**主次判定**：**系统镜为主**——本 change 的核心是把「防绕过」从指令层下沉到 schema 层，
以及把 CLI 依赖图缺陷从根上修掉；用户镜与开发循环镜的变化都是它的派生。
