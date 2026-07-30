# 阶段一入口的防绕过下沉到 project-local schema，但只能做到提示层

> 状态：**Accepted**（2026-07-31，`align-sdflow-spec-with-openspec-schema` 拷问阶段收敛，用户拍板）· 关联 change：`align-sdflow-spec-with-openspec-schema`

阶段一「产 spec 必须先经拷问」这条约束，此前**全靠指令层自律**：`CLAUDE.md` 与 `sdflow-init` 注入下游的托管区块里各有一句「模型 MUST NOT 自行选 `opsx:ff` 绕过拷问……判断需要开 change 时提示用户敲 `/sdflow-spec`」。它住在**另一个文件**里——而这套流程要防的失效模式恰恰包含「不会想到要去查它」。

openspec CLI 1.7.0 打开了一条 schema 层通道：`openspec schema fork <source> <name>` 产出 project-local schema 并**带出全部 `instruction` 全文**（`schema init` 出来的新 schema 其 `instruction` 为 `None`，只有 fork 带），而 1.7.0 的 Patch（PR #1405 / fixes #777）明确修掉了「官方 skill 内嵌的硬编码 spec-driven 套路会盖过 custom schema 的 instruction」——`propose` / `continue` / `ff` 三个工作流现在都会在 instruction 委派给某个 skill 时去调它。改 schema 的 instruction，约束就出现在模型**正在处理的任务载荷**里，而不是别处的禁令。

**关键事实（决定了这条路只能走到提示层）**：`sdflow-spec` 是全仓唯一 `disable-model-invocation: true` 的 skill（`sdflow-spec/SKILL.md:3`），**模型唤不起它**。这不是疏漏而是有意设计——相位 A/B 要与人一问一答，模型自动唤起等于模型自己跟自己拷问，正是该 skill 要防的失效。因此官方 ff 读到「invoke sdflow-spec」时无法执行该调用，委派的实际形态只能是**拦截 + 转人**：模型提示、人发起。

**第二个关键事实（决定了委派段必须可剥离）**：`sdflow-spec` 相位 C 的 C.3 步骤 1 本身就是 `openspec instructions <artifact> --json` 自取载荷。委派段若裸写进 instruction，读到「MUST NOT 自己写、去叫 `/sdflow-spec`」的正是 `/sdflow-spec` 自己——自指死锁。

## Considered Options

- **fork `spec-driven` 为 `sdflow-spec-driven`，改 instruction + 改依赖边，随 bundle 推下游（选中）**：委派段以 `<!-- sdflow:delegation:start -->` / `<!-- sdflow:delegation:end -->` 包裹置于原始 instruction 之前——官方 `ff`/`propose` 不认识这对标记、照读全文因而被拦截；`sdflow-spec` 认识它、在应用载荷前机械剥离，因而不自我劝退（剥离是确定性的字符串定界操作，符合「能机械化的优先机械化」）。同时把 `specs.requires` 改为 `[proposal, design]` 并**把 design 在本 fork 内转为无条件产物**——`sdflow-spec` C.2 本就无条件生成四件套，改后 schema 才反映真实流程，而非让 SKILL.md 去绕过 schema。代价 = 依赖 CLI 自标 experimental 的接口；fork 是快照，上游更新不自动跟且无机械门提醒。
- **去掉 `sdflow-spec` 的 `disable-model-invocation`，让委派真能调起来（砍掉）**：理由——该属性是有意设计，相位 A/B 需与人一问一答；放开等于让模型自己跟自己拷问，直接摧毁这个 skill 的核心价值。
- **只在本仓 dogfood、不推下游（砍掉）**：理由——那是**自加约束**（人从未提出这个限制）。实测证明下发成本极低：`config.yaml` 的 `schema:` 键即决定 `new change` 用哪个 schema（无需 `--schema` 标志），落地面就是 `config.template.yaml` 改一行 + schema 目录纳入 `copy_bundle` 托管刷新。且下游的指令层约束**更薄**——本仓干活时 `CLAUDE.md` 全文在场，下游只有托管区块里那一句——因而更需要 schema 层引流。
- **不做 schema 化，继续靠 `CLAUDE.md` + C.2 超集表（砍掉，但站得住）**：理由——这是个诚实的选项，`sdflow-spec` C.2 的写死超集表无条件正确、零 CLI 依赖，维护成本≈0。被否是因为防绕过会继续只住在别处的文件里。**须记录的是这笔账在拷问中变薄了**：立项时以「委派 = 自动回流（机械）+ 依赖图修密 = 纯机械收益」立起，实测后前者降为提示层、后者缩为「少一段文字 + 概念一致」（因拦截后产物实际总由 `sdflow-spec` 路径生成，而该路径用超集表，CLI 图密不密在实际产出路径上无影响）。人在知情此账的前提下仍选择走。
- **委派文案里写豁免条件（「若你正在执行 sdflow-spec 相位 C 则忽略本段」）（砍掉）**：理由——靠模型正确自我识别，而 fresh 子代理未必知道自己被谁编排；此处机械够得着（标记剥离），不该退到语义判断。
- **把委派放进 schema 的 `description` 字段靠字段分离天然隔开（砍掉）**：理由——官方明说 ff 读的是 `instruction`；且**无实测锚**（未验证 artifact 自身的 description 是否进 instructions 载荷），要走这条须先补测。

## Consequences

- **本仓与所有下游从内置 `spec-driven` 切到 fork 副本**。回滚 = config 改一行 + 删 `openspec/schemas/` 目录；但推给下游后需**逐仓**改回，逆转成本随下游数量线性增长。
- **fork 是快照，且漂移无机械门**：上游 `spec-driven` 的 instruction / 模板日后更新不会自动跟，也没有任何东西提醒它落后。已作为遗留 todo 记入 `openspec/roadmaps/openspec-1.7.0-followup/roadmap.md`，本次不解决（影响可控——fork 停在旧版 = 退化到今天的状态，不会更糟）。
- **CLI 版本门 ≥1.7.0 是硬要求**：1.7.0 之前官方 skill 内嵌的硬编码套路会**静默盖过** custom schema 的 instruction，且该 bug 的触发条件正是「custom schema 复用了熟悉的 artifact 名」——而保留同名 artifact id 恰是本决策的必要边界（见下条）⇒ 在 <1.7.0 的下游上委派失效是**必然**而非概率。`sdflow-init` 不满足版本时不铺 schema、config 保持 `spec-driven`、fail-loud 报一行；降级安全（退回今天的状态）。
- **fork MUST 保留四个 artifact id **与** `generates` 路径不变**：`sdflow-spec` C.3 步骤 3 的路径净化 allowlist 是**硬编码字面量**（`proposal.md` / `design.md` / `tasks.md` / `specs/**/*.md`），任一 `generates` 路径改动都会让写入被 fail-closed 拒绝。这也意味着官方那条「do NOT branch on hardcoded artifact names，custom schemas must work unchanged」的债在本决策落地后当场到期——缓解手段就是这条同名边界。
- **迁移顺序不可颠倒：先补写、后切 config**。change 的 schema 钉在自己的 `.openspec.yaml` 上，缺该文件才跟 config 走；实测中一个无该文件的旧 change 在 config 切换后被按新 schema 重新解读，`specs` 由 `ready` 变 `blocked`（失败模式**静默**——不报错，只是卡住）。故 `sdflow-init` 在切 config **之前**扫 `openspec/changes/*/`，给缺 `.openspec.yaml` 的在途 change 补写 `schema: spec-driven`（幂等）。反过来做则补写方读到的已是新 schema，写下去的值就是错的。归档件不受影响（CLI 不再 status/validate 它们）。
- **委派标记名 MUST NOT 含 `gate`**：`openspec/CONTEXT.md` 已把 **gate** 确立为**正确性门**的专名（fail-closed、零容忍），而委派段是提示层、非机械保证。叫 `delegation-gate` 会把它伪装成正确性门。标记本身是**新增的共享字符串**，改它须先 `grep -rn`（不加 `--include` 限定），同 `sdflow:principles` 先例。
- **`sdflow-spec` C.2 的写死超集表可以退役**，终审第 2 条（design↔specs 双向核对）从「唯一防线」降为「兜底」——因为 fork 后 CLI 自己的依赖图已经密了。
- **对「委派真的会被遵守」不得作机械声称**：它是提示层加强（约束从别处的文件搬进模型必读的载荷），不是机械保证。proposal / design / SKILL.md 里 MUST NOT 表述为「自动回流」或「走哪条路都被导回来」。
