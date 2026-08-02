# openspec CLI 1.7.0 跟进 实施路线图

> 版本：v1（2026-07-30，相位 A 收敛）
>
> **精简 roadmap（单文件，非三件套）**——本包不含 `requirements.md` / `design.md` / `task-log.md`。
> 理由：本批只有 3 个 change + 2 个待拍板项，每个 change 的需求与设计由其自身四件套承载，
> 本文只负责**统摄 + 索引 + 保存已拍板决策与实测锚**。既有两个 roadmap（`mechanical-layer-hardening`
> / `workflow-cost-optimization`）是「两腿六阶段」量级，格式不必强行对齐。
>
> **本文的读者是未来某次 fresh context 的开工者**——所以实测锚一律写命令 + 实际输出，
> 不只写结论；不要求读者回溯本次对话。

## 背景

`@fission-ai/openspec` 升级到 **1.7.0**（本机已装，npm 最新亦为 1.7.0）。本批盘点这次升级
对本仓 skill 与 workflow bundle 的影响面，并切分为可逐步实施的 change。

---

## 已完成（分支 `chore/openspec-1.7.0-sync`）

| commit | 内容 | 验证 |
|---|---|---|
| `8ba0f10` | 同步 36 个 CLI 生成物（`.claude/` + `.codex/`，`generatedBy` 1.4.1→1.7.0）；新增 `/opsx:update` 与 `openspec-update-change`（1.6.0 引入，修订已有 change 的规划产物） | — |
| `1f4643c` | **P0 修复**：FF-0 守卫 change 名 grammar `^[a-z]` → `^[a-z0-9]` + 3 组测试 | 定点回滚验非恒真（旧式下 6 红，失败模式 `KeyError: 'permissionDecision'` 印证不执法）；全仓 2958 passed |

**P0 的成因**（同类问题的判例）：CLI 1.7.0 放开 change 名可含数字前缀（`100-add-feature` /
`00001-add-auth`，CHANGELOG #1435），而 `ff0-branch-guard.py` 持有的是**外部契约的本地副本**，
没跟着放宽 ⇒ 合法新形态抽不出名字 ⇒ 整条命令掉进 `command-unverifiable` 分支 ⇒ **守卫不执法**
（fail-open），保护分支静默失守。

grammar 对齐锚（CLI 1.7.0 实跑）：接受 `100` / `9` / `a1` / `1a-b` / `00001-add-auth` /
`100-add-feature`；拒绝 `add.foo`（只许小写字母数字连字符）/ `add--foo`（连续连字符）/
`add-`（尾连字符）/ `Add`（大写）/ `add_foo`（下划线）。

> ⚠️ **遗留动作**：hook 由 `sdflow-init/scripts/init.py:581` **copy** 安装（非 symlink），
> 本机 `~/.claude/hooks/ff0-branch-guard.py` 需同步才生效：
> ```bash
> cp sdflow-init/assets/hooks/ff0-branch-guard.py ~/.claude/hooks/ff0-branch-guard.py
> ```
> **不要**用 `init.py update` 代替——它会把 workflow 规则副本拷回仓内，形成 pin 遮蔽全局 canonical。

---

## 阶段切分

| # | change | 含 | 依赖 | 状态 |
|---|---|---|---|---|
| **P1** | sdflow-spec × openspec schema 契约面重整 | A1 A2 A3 **A4** · E1 E2 E3 | 无 | ✅ 已交付（本 change） |
| **P2** | prevention 层扩到 apply/archive | B1 B2 C2 | 无 | ✅ 已交付（change `complete-openspec-170-followup`） |
| **P3** | sdflow-done archive 现代化 | D1 D2 **D3** | 无 | ✅ 已交付（change `complete-openspec-170-followup`） |
| ~~Q1~~ | ~~是否采纳 `skip_specs`~~ | — | — | ✅ **已拍板：采纳**（见 D-3） |
| **Q2** | amendment 双向 coherence | F1 | — | ✅ 已拍板+已交付（change `complete-openspec-170-followup`） |

**P1/P2/P3 改文件集不相交，可并行**：P1 触 `sdflow-spec/SKILL.md` + `sdflow-init`（schema 下发）；
P2 触 `config.yaml` + `config.template.yaml`；P3 触 `sdflow-done/SKILL.md`。

---

## P1 · sdflow-spec × openspec schema 契约面重整（✅ 已交付）

**交付状态**：本 change 已完成 P1 范围；全量 `pytest` 因 Windows/Git Bash 环境长时间无输出，按用户批准未作为本 change 的放行证据。

**目标态一句话**：让 `sdflow-spec` 与 openspec CLI 1.7.0 的契约面对齐，并通过 project-local
schema 把它从「靠指令层自律才不被绕过的旁路」变成 **schema 层的默认路径**（含下游项目）。

**为什么 A 组与 E 组是一个 change**：两组改的是同一片区域——

```
sdflow-spec/SKILL.md
 ├ C.2 强制阅读清单（写死的超集表）   ← E2 让它退役
 ├ C.3 逐产物生成协议                ← A1 补 glob 分支、A3 收紧断言
 ├ C.4 写后核验                      ← A2 改用 existingOutputPaths
 └ 终审第 2 条（design↔specs 双向核）← E2 让它从「唯一防线」降为「兜底」
```

分开做会产生确定的白做：先在 change 1 加固「因为 CLI 依赖图不密、所以要写死超集」那段措辞，
紧接着 E2 把依赖图修密，该段当场退役。

### A 组 · 照 CLI 实际返回的形状改相位 C

#### A1 · glob artifact 的写入目标 🔴

**实测锚**：

```bash
openspec instructions specs --change X --json
#   → resolvedOutputPath = "<abs>/openspec/changes/X/specs/**/*.md"   ← 字面 glob，不是文件
openspec status --change X --json
#   → artifactPaths.specs.existingOutputPaths = []                    ← 真实文件在这（已展开）
```

官方 1.7.0 为此新增两处措辞（`openspec-update-change` / `openspec-ff-change`）：

> Do NOT write to `resolvedOutputPath`: for a glob artifact it is still the glob pattern, not a real file.
> If `resolvedOutputPath` is a glob, follow `instruction` to choose the concrete file path

**本仓暴露面**（`sdflow-spec/SKILL.md` C.3）：步骤 3「路径净化」的三道检查
（在 change 目录内 / 落 artifact allowlist / 无 symlink）**一道都拦不住**——字面 pattern
`specs/**/*.md` 恰好就在 allowlist 里；这三道是为防越权设计的，不是为防「目标根本不是文件」。
步骤 4「临时文件 → 原子替换」照字面执行 ⇒ 造出文件名含 `*` 的文件（macOS 上 `*` 合法）。

**诚实边界**：SKILL.md 是给模型读的**指令**、不是脚本，模型实跑时大概率会自己发现 glob 不能
当路径 ⇒ 这是**指令层的洞、不是必然触发的机械 bug**。但 C.3 通篇是「机械照做」文风
（原子替换 / fail-closed / MUST NOT 重试），恰恰最容易被字面执行。

**修法**：C.3 补 glob 分支——具体路径按 `instruction` 选；改写已有文件时目标取 `existingOutputPaths`。

#### A2 · 用 `existingOutputPaths` 替代自行 glob 🟡

C.4 的存在态判定、终审「读回全部四份」都要枚举 `specs/**` 下的实际文件，目前靠自己展开。
CLI 已给出展开结果（字段见 A1 实测锚）。

#### A3 · `dependencies` 的 schema 断言可收紧 🟢

**实测锚**——实际形状是 dict 列表，而 C.3 步骤 2 只断言了 `dependencies`(list)：

```json
[{"id":"proposal","done":true,"path":"proposal.md","description":"..."}]
```

#### A4 · `skipped` 态 🟡（**已拍板采纳，见 D-3**）

C.2 强制阅读表与 C.3 逐产物循环都要认这个态——CLI 规定声明了 marker 的 change 其 specs 文件
**MUST NOT 存在**，而 `sdflow-spec` 现在会**无条件生成** specs，随后 `validate` 会因
「marker 与 delta 同时存在」报错。

**实测锚**（声明 `skip_specs: true` 于 change 的 `.openspec.yaml` 后）：

```
                          无 marker              有 marker
specs 的 status:          ready                  skipped      ← 且其文件 MUST NOT 存在
tasks 的 missingDeps:     （被 specs 挡）         ["design"]   ← specs 从阻塞边上摘掉
validate --strict:        ✗ ERROR「无 delta」     通过
```

无 marker 时 `validate` 的报错原文自己就指向这个标记：

> If this change intentionally modifies no specs (pure refactor, tooling, docs),
> set "skip_specs: true" in the change's .openspec.yaml instead.

⇒ 标记不是「可选的便利」，而是**零 delta change 的唯一合法出口**：要么写 delta，要么声明标记。

**修法**：C.3 逐产物循环遇 `status: "skipped"` ⇒ 跳过该产物且 **MUST NOT 创建文件**；
C.2 的强制阅读表在 specs 被跳过时，`tasks` 那一行的必读集相应去掉 `specs/**`。
🔴 **判据只取 CLI 自报的 `status`，MUST NOT 由模型自行判断某个 change 够不够格 skip**
——那是无确定性信号的语义判断，写进相位 C 会变成每个 change 都要过一次的自由裁量。
「够不够格」由**人在相位 B 拍板**并落进 `decision-memo.md`，相位 C 只认既成事实。

### E 组 · project-local schema

> `openspec schema *` 全系列 CLI 自报 `[experimental]`（"Schema commands are experimental and
> may change"）——这是本组的主要风险面。

#### E1 · `instruction` 委派：把官方入口引流回 sdflow-spec 🔴

**官方依据**（1.7.0 Patch，PR #1405 / fixes #777）——这是官方**有意支持**的用法：

> **Custom schema instructions are no longer overridden by hard-coded spec-driven patterns** …
> the `propose`, `continue`, and `ff` workflows direct the agent — both in the artifact-creation
> step and in the guidelines — to invoke a skill when the instruction delegates artifact creation
> to one, verifying the artifact exists afterward

**端到端实测锚**：

```bash
openspec schema fork spec-driven <name>     # → schema.yaml 带出全部 5 处 instruction 全文
#   ↓ 在 proposal 的 instruction 首行插入 marker
openspec schema validate <name>             # → ✓ Schema '<name>' is valid
openspec new change X --schema <name>
openspec instructions proposal --change X --json
#   → instruction 首行 = "SDFLOW-DELEGATION-MARKER: 本产物 MUST 调 /sdflow-spec 生成…"  ✅ 原样透传
```

**价值**：CLAUDE.md 现在靠一句纯指令层约束挡绕过——「模型 MUST NOT 自行选 `opsx:ff` 绕过拷问」。
改 schema instruction 后，走 `/opsx:ff` 的模型会**在载荷里**读到委派 ⇒ 从「靠自律」变成
「走哪条路都被导回来」。

🔴 **必须走 `fork`，不能走 `init`**：`schema init` 生成的 schema **没有 `instruction` 字段**
（实测 `instruction = None`），只有 `fork` 带。顺带发现：若真用了无 instruction 的 schema，
`sdflow-spec` C.3 步骤 2 会 **fail-closed 中止**（它把 `instruction`(str) 列为必需字段）。

**仍未验**：① 委派在 Codex 宿主下是否成立；② 与 sdflow-spec 自身相位 B 前置是否形成环
（ff → 委派 → sdflow-spec → 相位 C 又调 instructions）。

#### E2 · CLI 依赖图缺陷可**从根上**修掉 🔴

**实测锚**——`schema.yaml` 的 `requires` 边完全透传到 `openspec instructions`：

```
自定义 schema 里 design.requires = [specs]
  → openspec instructions design --json 的 dependencies = ['specs']   ✅
（内置 spec-driven 是 design.requires = [proposal]）
```

这正是 `sdflow-spec` C.2 用「**写死的超集表**」在绕的那个洞：

> 实跑核验：`design.dependencies` 与 `specs.dependencies` 都只有 `[proposal]` ⇒
> **specs 生成步根本不会读 design.md**，而 design↔specs 矛盾没有任何其它环节会发现

fork 后把 `specs.requires` 改成 `[proposal, design]`（或反向）⇒ CLI 自己的图就密了
⇒ C.2 的写死超集表**可以退役**，终审第 2 条从「唯一防线」降为「兜底」。

> 📌 **留证**：CLI **1.7.0 至今仍未修**这个依赖图缺陷——实测 `specs.dependencies` 依然只有
> `[proposal]`，即官方路径的 specs 生成步**仍然不会读 design.md**。

#### E3 · 已知代价

- **fork = 快照**：上游 `spec-driven` 的 instruction/模板日后更新，本仓 fork **不会自动跟**，
  要手动 rebase，且**没有机械门提醒它漂了**（→ 遗留 todo）。
- **experimental**：CLI 自标，接口可能变。

### P1 的四条边界（已拍板，见 D-1/D-2）

1. **随 bundle 推下游** —— schema 目录纳入 `copy_bundle` 托管刷新（与 `tools/` 同构：
   源在 `sdflow-init/assets/`，下游整删重拷，**禁止在下游手改**）。
   落地面极小：`config.template.yaml:17` 的 `schema: spec-driven` 改一行即可
   （**实测**：`config.yaml` 的 `schema:` 键即决定 `new change` 用哪个 schema，无需 `--schema` 标志）。
   **下游比本仓更需要**：本仓干活时 CLAUDE.md 全文在场；下游只有托管区块里那一句约束。
2. fork **保留 `proposal/specs/design/tasks` 四个 artifact id 不变**——`sdflow-spec` 通篇硬编码
   四件套名，同名才对得上。
3. **CLI 版本门 ≥1.7.0**，不满足则不铺 schema、config 保持 `spec-driven`、fail-loud 报一行。
   🔴 **硬依据**：E1 引的 PR #1405 属 **1.7.0**；在此之前官方 skill 里嵌的硬编码 spec-driven
   套路会**盖过** custom schema 的 instruction ⇒ 委派**静默失效**（不报错）。且该 bug 的触发
   条件正是「custom schema 复用了熟悉的 artifact 名」= 边界 2 ⇒ 在 <1.7.0 的下游上失效是
   **必然**而非概率。降级安全——退回今天的状态，不会更糟。
4. 排在其它阶段之前（P1 即本次）。

---

## P2 · prevention 层扩到 apply/archive

### B1 · `operations.{apply,archive}.guidance` 🟡

**实测锚**（1.6.0 引入，形状为**字符串数组**，写成字符串会被拒并打警告
`Guidance for operation 'apply' must be an array of strings, ignoring this operation's guidance`）：

```yaml
operations:
  apply:   { guidance: ["..."] }
  archive: { guidance: ["..."] }
```
→ `openspec instructions apply|archive --change X --json` 返回 `operationGuidance: [...]`

**注入面的形状变化**：

```
现状:  config.rules{proposal, specs, design, tasks}   ← 阶段一，任何路径都读得到
       apply / archive 面                             ← 无 config 通道
         └ 约束只活在 sdflow-done/SKILL.md 里
           ⇒ 走官方 /opsx:archive 时，这些约束完全不在场

1.7.0: 同上 + operations.{apply,archive}.guidance     ← 阶段三也有了固化通道
```

`sdflow-done` 中这几条硬约束目前只在走 sdflow-done 这条路时生效，值得下沉：

- 「归档**必须**走 `openspec archive` CLI，禁手动 `mv`」（漏 delta→specs 同步）
- 「archive 前先 reconcile `tasks.md` 复选框」（否则 N/M incomplete 警告 + verify 误判）

命中分析基准 1（能固化的优先固化）+ `sdflow-spec-review` 自身定位（「只审 prevention 焊不住的
残差」）——把残差往回压一格。

### B2 · 下发面

`sdflow-init/assets/workflow/config.template.yaml` 当前**无** `operations` 段（已 grep 确认）。
B1 若做，模版须同步才能推给下游。

### C2 · delta spec 的 `## Purpose` 🟢

**文档锚**（CHANGELOG #1431）：1.7.0 起新能力 delta 若以 `## Purpose` 开头，`archive` 会把它抬进
新建的主 spec；否则写 `TBD - created by archiving change <name>...` 占位符。carried Purpose
< 50 字符会被 `validate --strict` 警告「too brief」。

**修法**：`openspec/config.yaml` 的 `rules.specs` 加一条，同步进 `config.template.yaml`。

---

## P3 · sdflow-done archive 现代化

### D1 · 改读 `--json` 的 `warnings[]` 🟢

**文档锚**（CHANGELOG #1437）：1.7.0 的 `archive --json` 新增可选 `warnings` 数组。
`sdflow-done/SKILL.md:375` 现在是 `openspec archive {name} -y 2>&1 | tail -30` 靠文本判断。

### D2 · fallback 阶梯可瘦身 🟢

**文档锚**（同上）：1.7.0 修掉了「REMOVED 的需求已从主 spec 消失 → archive 直接 abort」
（现在 warn + 按已应用处理 + 报 applied-only 总数）。`sdflow-done` 那条「`--skip-specs` + 手动
六步同步」的退路，**触发原因之一已经消失**。

同批还修了：delta 里非 `### Requirement:` 的分隔标题不再被当幽灵需求告警；
`## REMOVED Requirements` 不再被报「缺 scenario」；symlink 化的 `specs/<cap>/spec.md` 不再被
静默丢弃。

### D3 · archive 侧认 `skipped` 态 🟡（**因 D-3 新增**）

`skip_specs` 采纳后，归档一个声明了标记的 change 时**没有 delta 可同步**。`sdflow-done` 的
archive 步（含「归档必须走 CLI 以同步 delta→主 specs」那条硬约束、以及 `--skip-specs` 手动
六步 fallback）需要认这个态，**MUST NOT 把「没有 delta」判成异常**。

---

## 待拍板

### Q2 · `[spec-review-amendment]` 的双向 coherence ❓

**仓内锚**：`sdflow-spec-review/SKILL.md:283` 全部内容就一句——

> 据此更新 design/specs，改动处标 `[spec-review-amendment]`

两个缺口：① 没有任何 coherence 保证；② 只提 design/specs，**proposal / tasks 不在话里**。

官方 `/opsx:update`（1.6.0 引入）的核心原则正是这个缺口的形状：

> an edit to a later artifact may require revising an earlier one, **not only the other way
> around**. Build order is a useful reading order, **not a constraint on which artifacts may
> be revised**.

评审最常见的 finding 恰恰是这个方向：多镜在 design 里挖出问题，而根因在 proposal 的
Non-Goals 划错了。

**修法倾向**：借**原则**，不直接调 `/opsx:update`——后者不知道本仓的 checkpoint / `reviewed_sha`
时序契约（ADR-7(b)「二次修订必须单独落盘再回写锚」），会打架。

> 📌 `sdflow-spec` 终审第 2 条已独立发现同一洞见的**局部版**（design↔specs 互不依赖 ⇒
> 其矛盾无人发现）。官方那句是它的泛化。

---

## 明确不做

| 项 | 理由 |
|---|---|
| stores（`--store` / `defaultStore`） | 本仓与下游都在仓内 `openspec/`，收益≈0。官方生成物里的「Store selection」段是 CLI 自铺的，不用管 |
| CodeArts / Hermes / ZCode 三个新宿主 | 无关 |
| `openspec init --no-animation` | 无关 |

## 不必跟进的官方新措辞（留证，防止日后以「跟进上游」名义拉齐）

| 官方 1.7.0 新增 | 为什么本仓不需要 |
|---|---|
| 必产集要走 `requires` 传递闭包 | `sdflow-spec` **硬编码**四件套完整集（C.2 表），不做推导，无从漏 |
| 「`status` 只判文件存在性，`done` ≠ 依赖已存在」 | C.4 早写了，还引了 CLI 源码行号 `dist/core/artifact-graph/state.js:25-29` |
| 「依赖要从磁盘重读，别用对话记忆」 | C.2 用**写死的超集**覆盖，且刻意不信 CLI 依赖图 |

⚠️ 上表第 2、3 行**不因 E 组而失效**（`status` 仍只判文件存在性、依赖仍要从磁盘重读）；
只有第 1 行与 C.2 的写死超集表会因 E2 而部分退役。

**要认的债**：官方新说「do NOT branch on hardcoded artifact names，custom schemas must work
unchanged」，而 `sdflow-spec` 全是硬编码。这是**有意的窄化**（只服务 spec-driven schema），
不是漏——但 **P1 一旦落地，本仓自己就成了「用自定义 schema 的项目」**，这笔债当场到期。
缓解 = P1 边界 2（fork 保留同名 artifact id）。

## 遗留 todo（不在本批解决）

- **fork 漂移无机械门**：上游 `spec-driven` 更新时，没有任何东西提醒本仓的 fork 已经落后；本 change
  只记录边界，不实现检测或自动 rebase（见 todolist T264）。

---

## 附录 · 决策记录

### D-1 · E 组走，且随 bundle 推下游（2026-07-30 人确认）

四条边界见「P1 的四条边界」。

**演进**：最初推荐「只在本仓 dogfood、不推下游」，被人当场指出那是**自加约束**（通则③：
人没提的限制别自己发明），撤销。实测证成本极低（config 一个键 + 一个目录，`sdflow-init`
本就在管 config 与 bundle 刷新），且下游的指令层约束更薄、更需要 schema 层引流。

### D-2 · A 组与 E 组合并为一个 change（2026-07-30 人确认）

理由见「P1 · 为什么 A 组与 E 组是一个 change」。

**否掉的第三种切法**：按 skill 边界切（`sdflow-spec` 一个 change、`sdflow-init` 的下发 + 版本门
一个 change）。否掉理由：E1 的价值只有铺到下游才兑现，拆开等于第一个 change 交付一个半成品。

### D-3 · 采纳 `skip_specs`（2026-07-30 人拍板）

**人给的依据**：开发过程中确实碰到过这种情况，**且是在项目 repo（下游消费项目）中**。

⇒ A4 进入 P1 范围，D3 进入 P3 范围。

🔴 **取样盲区（本决策最重要的一条经验）**：我最初推荐「不采纳」，依据是本仓 52 个归档 change
里只有 4 个无 specs delta（7.7%，其中 2 个还来自已废弃的 `plan-{topic}` 壳模式）——**但那是
本仓的数据**。本仓是 skill 仓，「指令即契约」，几乎每个 change 都动契约；**下游是普通业务项目，
纯重构 / 工具链 / 文档类 change 的占比本就高得多**。拿源仓 dogfood 分布去估消费仓的适用面，
是典型的 dogfood 盲区。

**落地含义**：`skip_specs` 的主要受益方在**下游**，因此它与 E 组走同一条路——相关规则须随
bundle 下发，而不是只在本仓生效。

**未定的形态**（留给 P1 相位 B 拷问）：「够不够格声明标记」的判据要不要写死进 bundle、
写到什么粒度。已定的只有一条边界（见 A4）：相位 C **只认 CLI 自报的 `status`**，
不做自由裁量；判断发生在相位 B 并落进 `decision-memo.md`。
