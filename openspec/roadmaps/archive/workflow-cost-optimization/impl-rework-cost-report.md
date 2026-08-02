# 实现期返工成本实测报告（2026-07-31 · 三仓 7 天 16 change 采样）

> 包内独立报告，与 `tickets-pilot-log.md` 同级。三件套不引用；开 change 时作为输入引用本文件。
> 采样：`mqtt-console`、`zhws_ops_api`、本仓，2026-07-24 ~ 07-31，共 16 个 change。

## 结论

**主诉「测试花的时间是写代码的很多倍」成立，且普遍——但归因不是测试写太多。**

真正吞掉时间与 token 的是 **fix 返工轮次 × 每轮的固定开销**：每多一轮，聚合套件重跑一遍、
再产 N 份报告、再重打包一次全量 diff 喂给 reviewer。**轮次是乘数，所有固定开销都被它乘。**

轮次失控有一个高度集中的成因：**在无界语法面上手搓解析器当机械门**（CLAUDE.md 基准 5）。
这类票的 finding 每轮换一个语法角落，指纹每轮不同，导致熔断永不触发、补丁循环不收敛。

∴ 减法的目标是**轮次与每轮固定开销**，不是测试量。直接砍测试会砍错地方且伤质量。

**成本分两层，成因不同、修法不同：**

| 层 | 是什么 | 主因 | 对应章节 |
|---|---|---|---|
| **执行成本** | 跑测试的时间与 token | 全量运行次数绑定在 fix 轮次上 | 病灶 1–4 · 清单 ①–⑧ |
| **编写与维护成本** | 写测试、改测试、回访既有测试 | 四种成因混杂，**其中一种不该压缩** | 「测试编写与维护成本」节 · 清单 ⑨⑩ |

## 为什么这是结构性问题，不是调参问题

全量 e2e / 集成套件的**单次成本随项目复杂度单调上升**：用例数增长、被测面增长、
打包与启动开销增长（`mqtt-console` 已经是「每轮一次完整 `wails build` + 打包应用启动 + 88 次截图」）。

而当前机制把全量运行的**次数**绑定在 fix 轮次上（`SKILL.md:328-330`）。
于是总成本 = **单次成本（↑）× 运行次数（↑）——两个因子同时增长**。

∴ 把轮次从 15 压到 2 只是把爆炸推迟：等 e2e 单次进入十分钟量级，每个 change 仍要付两遍。
**「每轮全量重跑」这个设计本身不可持续**，要改的是耦合关系，不是数值。

**正确的耦合：全量运行次数与 change 挂钩（收口一次），与 fix 轮次彻底解耦。**
中间轮次一律只跑受影响子集——它们的结果本就不进最终报告，跑全量纯属烧掉。

这也决定了本清单的优先级：① 改耦合关系（结构性），④⑥ 压轮次（缓解性）。
**只做 ④⑥ 不做 ① 无法解决问题**，只是把同一条曲线的斜率放缓。

## 实测数据

### 总量（7 天窗口，`git log --numstat`）

| 仓 | 实现行 | 测试行 | 测试/实现 | impl-report 行 | **report/实现** |
|---|---|---|---|---|---|
| mqtt-console | 6,661 | 7,782 | 1.17x | 22,319 | **3.35x** |
| zhws_ops_api | 46,888 | 35,342 | 0.75x | 98,352 | **2.10x** |
| sdflow-skills | 7,009 | 14,136 | 2.02x | 38,180 | **5.45x** |

测试/实现 0.75–2.02x 属正常区间（栈 × change 类型决定）。
**异常项是 impl-report 证据文档——2.10x 至 5.45x，普遍严重，非个例。**

### 返工轮次分布（16 个 change）

| change | fix 轮 | 最深 | 跑测试痕迹 | 报告 md 行 | diff 包 |
|---|---|---|---|---|---|
| **align-sdflow-spec-with-openspec-schema** | **37** | **fix8** | **136** | 2,786 | — |
| standardize-dialog-layout | 15 | fix5 | 109 | 1,461 | 528KB |
| add-sdflow-spec | 13 | fix4 | 73 | 6,471 | — |
| fix-workspace-dialog-styling | 13 | fix6 | 39 | 1,433 | 268KB |
| manage-permission-catalog-items | 9 | fix4 | 34 | 1,206 | 508KB |
| harden-sdflow-spec-followups | 8 | fix5 | 33 | 548 | — |
| inject-config-dir | 7 | fix2 | 41 | 1,471 | 364KB |
| refactor-model-permission-modes | 7 | fix2 | 32 | 3,054 | 1,356KB |
| enable-codex-background-outside-voice | 7 | fix2 | 43 | 3,714 | 868KB |
| windows-store-parity | 6 | fix2 | 23 | 270 | 320KB |
| add-role-login-channel-and-default-perm | 6 | fix1 | 69 | 3,200 | — |
| harden-implement-review-loop | 4 | fix1 | 39 | 1,570 | 436KB |
| fix-windows-encoding-crash | 3 | fix1 | 16 | 478 | 132KB |
| fix-test-cleanup-fingerprint-integrity | 1 | fix1 | 8 | 2,110 | 368KB |
| collapse-perm-modes-to-role-matrix | **0** | — | **16** | 934 | 564KB |
| refine-device-auth-ui | **0** | — | **9** | 763 | — |

### 轮次是乘数 —— 直接实证

| fix 轮档 | change 数 | 跑测试痕迹（中位） |
|---|---|---|
| 0 轮 | 2 | **12.5** |
| 1–9 轮 | 11 | 34 |
| ≥13 轮 | 3 | **109** |

**fix 轮 = 0 的两个 change 只留下 9 / 16 次跑测试痕迹；fix 轮 ≥13 的三个是 73–136 次——差 8–15 倍。**

## 归因：四处机制病灶

### 病灶 1 — 单一盘面条款把全量重跑乘以轮次（`sdflow-implement/SKILL.md:328-330`）

> 🔴 **单一盘面（[impl-review-fix FIX-4]）**：∴ **任何产品代码修复之后（fix 循环的每一轮），
> MUST 重跑全部已覆盖层**，MUST NOT 只重跑刚失败的那一层

条款要防的是假绿拼接（unit@A + integration@B 拼成「全部通过」），目标正当。

**但它过度实现了自己的目标。** 单一盘面真正要求的是「**最终报告里所有判通过的行锚同一 SHA**」；
「每轮都重跑」是该要求的**充分不必要条件**——中间轮次的结果不进最终报告，纯属烧掉。

**实践已自发绕开该条款并通过评审**：`standardize-dialog-layout` 的 fix5 报告明写
「本轮只改 production resolver 的同值绑定，没有修改 fixture/scenario/runner；
因此没有伪称重跑 88-case 全矩阵」，spec-review r4 判 PASS 并认可
「组合边界诚实且**与改动风险相称**」。⇒ **规则滞后于已被验证的实践。**

### 病灶 2 — `review-loop-breaker` 对「同根因换马甲」结构性失效（`SKILL.md:651-657`）

熔断身份键 = 「同文件 + 规范化问题指纹」，行号不计入（`:655`）。
该设计防住了行号漂移，但**没防住同一根因每轮换一个语法分支**：新分支 ⇒ 新指纹 ⇒
轮次计数清零 ⇒ 熔断（`:654` 的「连续 2 轮」）永不触发。

### 病灶 3 — 出票环节不拦「手搓解析器型验收标准」（`SKILL.md:270`）

出票模式对验收标准的全部约束只有「含验收标准复选框」「MUST NOT 预写实现代码或具体文件路径」。
**没有任何一条把 CLAUDE.md 基准 5（无界语法禁手搓）下沉到出票环节。**
于是「验收标准 = 手搓一个源码解析器」在出票那一刻就写进合同，后续轮次不可能收敛。

### 病灶 4 — `sdflow-code-review` 完全没有 fix 循环熔断

`sdflow-code-review/SKILL.md` 全文**无 loop-breaker 等价规则**（唯一的「无限循环」提及在 `:443`，
是 helper await 的 RESERVED 形态处置，与 fix 循环无关）。

**它连 implement 侧那个有缺陷的熔断都没有。** 最深的返工正发生在这一侧：
`align-sdflow-spec` 的三个镜各自跑到 `adversarial-fix7` / `domain-fix7` / `history-fix8`，
全程无任何轮次上限。

## 标本

### 标本 A：`align-sdflow-spec-with-openspec-schema` —— 手搓 YAML 解析器（最严重，fix8）

三个 code-review 镜的连续 finding，**R-ID 完全相同（CR-02 / CR-09）**，每轮只换一个 YAML 语法角落：

| 轮次 | finding |
|---|---|
| fix5 | A3 — 注释前缀后的 YAML document start 会被切成第二份文档 |
| fix6 | A4 — YAML directive 前插入 schema 会把合法配置拆成多文档 |
| fix7 | A5 — 合法的 `schema :`（带空格）被误判为缺键，update 写出重复 schema |

YAML 语法面无界（`---` document start、`%YAML` directive、注释、锚点、多文档、
键后空格……），**手搓解析器不可能穷举**。同一 R-ID 反复不消解，但因为每轮指纹不同，
病灶 2 的熔断从未触发；又因为病灶 4，code-review 侧根本没有上限。⇒ 跑到 fix8。

### 标本 B：`standardize-dialog-layout` Task 6 —— 手搓 JS 解析器

一张票产出 **14 份文档** + **206KB** 的 `task6-review-package.diff`（每轮重打包、每轮被两个 reviewer 读）。
`dialogButtons.static.test.js` 是手搓的 Svelte/JS 源码解析器：

| 轮次 | finding |
|---|---|
| r1 | 静态门把 `<select>` 误当 text-entry primitive |
| r2 | scanner 只匹配变量名 `event`/`e`，`evt.key !== 'Tab'` 可绕过 |
| r3 | `initialFocusResolver` 未与 production 机械绑定 |
| r4 | PASS |

**两个标本同型**：无界语法面（YAML / JS 源码）+ 手搓解析器当机械门 ⇒ 补丁循环不收敛。
即 CLAUDE.md 基准 5 警号的逐字复现——「**那不是还差最后一个 case，那是这个函数本来就不该存在**」。

### 界面验证测试的重跑次数（标本 B）

evidence root 唯一标识去重：native 矩阵 **≥4 次**、interactions **≥3 次**。

| evidence root | 规模 |
|---|---|
| `/tmp/mqtt-dialog-task6-native.Ewuj70` | 80/80 |
| `/tmp/mqtt-dialog-task6-native.eYNOzB` | 88/88 |
| `/tmp/mqtt-dialog-task6-native.vae6X3` / `.zHAUlg` | 11/11 quick ×2 |
| `/tmp/mqtt-dialog-task6-interactions.LBI6c0` / `.m6kQqA` / `.tubDsc` | 12/12 ×3 |

放大因素：**mqtt-console 未配置 `test-suites`**（`SKILL.md:313` 来源优先级 ①），
每轮由 implementer 自行判定，落到最保守的一条链：

```
make e2e-live && npm run test:e2e && npm run build && wails build \
  && verify-native-dialog-matrix.sh && verify-native-dialog-interactions.sh
```

**每一轮都含一次完整 `wails build` + 打包应用启动 + 88 次截图。**
quick 档（`TASK6_NATIVE_QUICK`）其实已存在于 `hack/verify-native-dialog-matrix.sh:85`，
只是没进 config、未制度化。

## 测试编写与维护成本（第二层）

前述病灶 1–4 治的是**执行成本**。「写测试、改测试、回访既有测试」是**另一层成本**，
成因不同，需分开处置。

### 实测：不是重写既有测试，是同一文件被反复回访

| 仓 | 测试 +增 / −删 | 删/增比 | 被改 ≥3 次的测试文件 | 最高回访 |
|---|---|---|---|---|
| mqtt-console | +6,524 / −1,258 | 0.19 | 16 | 12 次 |
| zhws_ops_api | +26,913 / −8,429 | 0.31 | 55 | 9 次 |
| sdflow-skills | +13,007 / −1,129 | 0.09 | 23 | 15 次 |

删/增比 0.09–0.31 ⇒ **测试基本是单调新增，并非大规模重写既有测试**。
成本集中在**回访次数**：`test_ff0_branch_guard.py` 15 次、`test_outside_voice_job.py` 15 次、
`dialogButtons.static.test.js` 12 次、`App.menuName.dom.test.js` 12 次。

### 四种成因（修法不同，其中一种不该压缩）

| 类 | 症状 | 成因 | 处置 |
|---|---|---|---|
| **1 · 手搓解析器补分支** | 同一测试文件每 20 分钟补一个新分类分支 | 病灶 3（无界语法面） | 清单 ⑤ 已覆盖 |
| **2 · 测试有效性返修** | 事后发现测试恒真/假绿，回去修 | red-before-green 未覆盖「补断言」场景 | **清单 ⑨** |
| **3 · 正常红绿循环** | 逐个边界补测试 | 功能本身有真实复杂度 | **不该压缩** |
| **4 · 跨 change 回访** | 同一集成测试被多个 change 改 | **需求演进**（已向用户确认） | **不可避免，不在优化范围** |

**第 1 类标本**——`sdflow-init/tests/test_ff0_branch_guard.py`，2026-07-27 一天内 6 次连续 fix：

```
12:27 harden FF-0 command boundary
12:45 收紧 FF-0 名称分类
13:00 tighten ff0 command classification
13:17 classify adjacent quoted change fragments
13:35 classify undecided ff0 commands
13:56 generalize FF-0 dynamic markers
```

这是**第三个手搓解析器标本**（解析 shell 命令，语法面无界），与标本 A（YAML）、标本 B（JS）同型。

**第 2 类标本**——`test_outside_voice_job.py` 的 commit 原文：
「让『宣称的机械锚』真的会红」「补三条恒真锚」「修正一处过度声明的测试名」。
测试写完后事后才发现无效，回头返修。
根因：`SKILL.md:509` 的 red-before-green 表述为「**先写失败测试**，再写刚好够通过的代码」
——这是**新写测试**的场景；**往既有测试补断言时该纪律没有被执行**。

**第 3 类标本**——`App.menuName.dom.test.js` 在 2026-07-29 的 8 次 fix：
代际锁、身份重置、关闭时机、名称透传……均为 workspace 重命名状态机的真实边界缺陷。
**这是 TDD 在正常工作，压缩它等于伤质量**（通则③：不缩水）。

**第 4 类标本**——`perm_modes_consumer_test.go` 被 5 个 change 修改
（`refactor-model-permission-modes` → `add-role-login-channel` →
`collapse-perm-modes-to-role-matrix` → `refine-device-auth-ui`）。
初判疑似 change 拆分过碎，**经向用户确认为需求本身在演进**
⇒ 属需求驱动的必然成本，**不归因于流程，也不列入本清单**。

### 横切发现：测试只增不减，没有删除/合并机制

删/增比 0.09 意味着测试近乎纯累积。而 Standards 轴的 Fowler 清单（含 Duplicated Code、
Speculative Generality）虽措辞通用，**从未明说覆盖测试文件**——实践中没有任何一步
审过「这些测试是否冗余」。

这直接接上「为什么这是结构性问题」一节：**测试单调累积 ⇒ 全量套件单次成本单调上升**。
不给累积装闸，清单 ① 的收益会被逐步吃回去。

## 手搓解析器的制度性根因（本仓）

YAML 那个（标本 A）在本仓**不是失误，是两条架构约束叠加的必然后果**。

### 本仓手搓解析的格式全清单

| 格式 | 处数 | 有界性 | 判定 |
|---|---|---|---|
| **Markdown fence** | **12 处**（6 脚本 × bundle/仓内各一份） | 有界（CommonMark 变体可穷举） | ✅ 合规，但**重复 12 份且已漂移 1 份** |
| **Markdown 结构**（表格行 / 标题 / 有序列表 / 引用块 / 链接） | `anchor_lint` 13 · `sad_schema` 10 · `maintain_scan` 5 · `hr_tg_intersect` 7 | 有界 | ✅ 合规，但各脚本各写各的 |
| **YAML**（`config.yaml` / frontmatter） | **5 份** | **无界**（人手写） | ❌ 标本 A，跑到 fix8 |
| sdflow 自有锚（`<!-- sdflow:... -->`） | `anchor_lint` · `retro_report` | 有界（**自己是 producer**） | ✅ 可控 |
| checkpoint commit subject | `retro_report` · `ship_gate` | 有界（**自己是 producer**） | ✅ 可控 |
| shell 命令 | `ff0-branch-guard` | **真无界** | ✅ **已修对**，见下「参照实现」 |

**两个待治面**：① YAML（无界，需收窄子集）；② Markdown fence/结构（有界但重复十余份，需收敛单一源）。

### fence 面已核验：等价且有机械守，**不列入待治**

12 份重复曾被疑为漂移面，逐份核验结论为**否**：

- **5 份逻辑字面等价**（`anchor_lint` / `hr_tg_intersect` / `outside_voice_guard` /
  `review_disposition_check` / `roadmap_writeback_draft`）——同样的
  `fence = (m.group(1)[0], len(m.group(1)))`，同样的闭合判据
  `m.group(1)[0]==fence[0] and len(...)>=fence[1] and ln[m.end():].strip()==""`。
- **第 6 份是有意声明的不同子集**：`sad_schema.py:70-73` 的 docstring 明写
  「CommonMark **语义子集**（A1）：开启行 = lstrip 后 ≥3 个同字符」，
  带 `[impl-review-fix] A1` 标记，属评审后的有意选择，**非漂移**。
- **已有机械守**：`outside_voice_guard.py:10` 记载「与 `anchor_lint` 的同名函数
  由**全笛卡尔 golden 测试**互相守一致」。

⇒ 按通则④（低概率 · 影响小 · 已有机械守），**MUST NOT 为它开工**。
**⑪ 的范围据此收窄为只治 YAML 一面。**

### 参照实现：`ff0-branch-guard.py`（无界面的正确处置，已收敛）

该 hook 面对的是**真无界**的 shell 命令语法，而它的 docstring 明确记载了正确解法：

> wrapper / 目录切换 / compound / 换行 / 散文与动态名均 **fail-open**，但输出无决策
> additionalContext 审计；**不解析 shell**，不设 permissionDecision。

即：**只认单条 literal 创建 grammar，界外一律不猜**（此处界外处置取 fail-open，
因为它是守卫 hook，fail-closed 会阻断正常工作；`config.yaml` 解析场景则应取 fail-loud）。

`test_ff0_branch_guard.py` 的 15 次回访中，2026-07-27 的 6 次连续 fix
**正是把它从「试图解析 shell」改造成上述形态的过程**——属**重构成本，非补丁螺旋**，
且已收敛。⇒ 它是 ⑪ 的参照实现，**不是病例**。

### 根因：零依赖不变量 × GC-2 边界锁

| 约束 | 原文出处 | 后果 |
|---|---|---|
| **零依赖不变量** | `init.py:534`「MUST NOT import yaml——本脚本被 symlink 进消费仓，消费仓多数无 PyYAML」；`ship_gate.py:893`「手写 stdlib，不 import yaml——保零依赖不变量」 | 不能用 PyYAML |
| **GC-2 边界锁** | `outside_voice_guard.py:10`「MUST NOT import anchor_lint——GC-2 边界锁，与 anchor_lint 的同名函数由全笛卡尔 golden 测试互相守一致」 | 脚本之间不能互相 import |

两条叠加 ⇒ **同一格式的解析必须在 N 个脚本里各写一份，只能靠 golden 测试守一致。**

实测重复实现（非测试文件）：

| 脚本 | 解析动作处数 |
|---|---|
| `sdflow-init/scripts/init.py` | 17 |
| `sdflow-ship/scripts/ship_gate.py` | 16 |
| `sdflow-implement/scripts/impl_route.py` | 14 |
| `lens_metric_emit.py`（bundle + 仓内两份） | 各 4 |

每个脚本各补各的语法分支，一个补了另一个没补 ⇒ **每轮 review 都能在某个脚本里挖到新分支**。
这是标本 A 跑到 fix8 的制度性成因，**不是某次实现的疏忽**。

### 解法：收窄输入面，而非提升解析能力

**MUST NOT 的方向**：写一个更完整的 YAML 解析器（无界语法面，基准 5 明禁）。
**正确方向**：把输入面**从无界收窄为有界**，并对界外输入 fail-loud。

1. **明确声明支持的子集**（键值、嵌套映射、注释、字符串标量），写成规格；
2. **界外构造一律 fail-loud**——多文档 `---`、`%YAML` directive、锚点 `&`/`*`、流式 `{}`
   ⇒ 报错并告知「config.yaml 用了不支持的 YAML 构造 X，请改写成 Y」，
   **MUST NOT 猜测、MUST NOT 静默误判**；
3. **单一源 + 机械生成分发**，绕开 GC-2 边界锁——复用本仓既有成熟范式
   （`hack/sync_principles.py` 的「单一源 + `--apply` 生成 + `--check` 门禁」）。

这样输入面就**从无界变有界**——不是假装界外不存在，而是明确拒绝界外输入。
基准 5 明说「**有界 ⇒ 可手写解析**」，该设计因此合规。

标本 A 的三条 finding 在新设计下的归宿：

| 原 finding（fix5–fix7） | 新设计下 |
|---|---|
| 注释前缀后的 document start 被切成第二份文档 | 报错：不支持多文档 |
| `%YAML` directive 前插入 schema 把配置拆成多文档 | 报错：不支持 directive |
| 合法的 `schema :`（带空格）被误判为缺键 | 属子集内，一次做对 |

**三条中两条从「要修的解析 bug」变成「一条明确的错误提示」，第三条一次做对。**

### 标本 B（mqtt-console 手搓 JS/Svelte 解析器）—— 性质与标本 A 完全不同

`frontend/src/lib/shell/dialogButtons.static.test.js` 共 **300 行**，全部由正则拼装：

```js
withoutComments()  →  replace(/<!--[\s\S]*?-->/g, '')            // 字符串内含 <!-- 即误剥
footer 块提取      →  /{#snippet footer\(\)}[\s\S]*?{\/snippet}/  // 嵌套 snippet 即错配
resolver 查找      →  new RegExp(`function\\s+${name}\\s*\\(`)    // 箭头函数 / 方法简写 / export 形式全漏
属性解析           →  tag.match(/\bclass\s*=\s*(['"])([\s\S]*?)\1/)
```

**而该项目 `package.json` 已依赖 `"svelte": "^5.56.4"`**，Svelte 官方导出 `parse()`
（`import { parse } from 'svelte/compiler'`）⇒ **零新增依赖即可取得真 AST**。

r2 的 finding「scanner 只匹配变量名 `event`/`e`，`evt.key !== 'Tab'` 可绕过」
在 AST 遍历下**根本不成立**——事件参数叫什么无关紧要，判据是 `IfStatement` 的结构。

**两个标本的成因与解法互不通用**：

| 标本 | 成因 | 解法 |
|---|---|---|
| **A**（本仓 YAML） | 零依赖不变量**禁止** `import yaml`，被迫手搓 | 收窄子集 + 界外 fail-loud（⑪） |
| **B**（mqtt-console JS/Svelte） | **无任何约束**，权威解析器已在依赖内，纯属未想到 | 直接改用 `svelte/compiler` 的 `parse()`（⑬） |

**残余语义仍合法**：AST 能把绝大多数正则猜测变成结构查询，
但「resolver 是否指向同一 canonical identity」这类跨文件一致性判断仍是语义层——
按基准 1，那是「机械真够不着的残余」，属合法划分，不是弱点。

### 与 `sdflow-devenv` 的分工（两条独立项，不可混为一谈）

- **本仓（清单 ⑪）**：病灶是「零依赖 × 边界锁」这一**架构约束**，
  不是「不知道该用什么工具」。解法即上述收窄子集 + 单一源生成。
- **下游项目（清单 ⑫）**：多数没有零依赖约束，直接 `import yaml` 即可。
  它们需要的是一张**手段对照表**，而 `sdflow-devenv/references/verification-patterns.md`
  已经是同构的负面知识库（❌ 测试计数门槛、❌ negative control、❌ 轮询式连接观测），
  是该对照表的天然载体。

## 与 P0 基线的口径校准（2026-07-31，⑧ 分桶调研收口）

P0 收口结论（`roadmap.md:68`、`design.md:58`、`task-log.md:43`）记录的 18-change 聚合阶段占比：

> spec-review **43%** / impl **29%** / ff 11% / grill 6% / code-review 5% / done 0%

本报告的实测数据为 **impl 67–77% / spec-review 6–14%**，初看与 P0 倒挂。
经三仓分桶验证（`sdflow-retro` 49 change + mqtt-console / zhws_ops_api checkpoint 时间戳），
**倒挂的成因是口径不同，P0 基线在可度量口径内未被推翻**：

| 口径 | 度量 | impl 占比 | spec-review 占比 |
|---|---|---|---|
| P0（retro elapsed，含人类门） | 阶段墙钟 | 29% | 43% |
| 本报告（活跃墙钟，剔除 >90min 间隔） | 编码活跃时段 | 67–77% | 6–14% |
| ⑧ 验证（retro elapsed，tickets 管线 8 change） | 阶段墙钟 | **23%** (P50=20%) | **36%** |

差异成因：
1. **口径不同**：本报告剔除 >90min 人类间隔后 spec-review（人类门主导）被压缩、impl 膨胀——这是同一现实的两个投影，不矛盾。
2. **度量维度不同**：报告 §「实测数据」的 impl/test/report **行数比** 67–77% 不是阶段墙钟比，是 `--numstat` 代码行产出比。行数口径下 impl-report 证据文档（2.10–5.45x）是真实异常，但它说的是「每行实现代码附带多少行报告」，不是「impl 阶段占总墙钟多少」。

**结论（三条，详见 `task-log.md` 同日条目）**：
1. P0 基线未倒挂——roadmap 优先级不需要重排，D11「墙钟真杠杆归 Leg3」不变。
2. 返工乘数效应**仓内差异显著**：sdflow-skills fix 均=12.0（手搓解析器）、mqtt-console 10.2（界面验证重链）、zhws_ops_api 3.8（最健康，2/6 零返工）——病因在特定仓的特定机制，非管线本身的缺陷。
3. 消费仓 retro 盲区（评审阶段不落 checkpoint）不影响本清单效果——①②④⑤⑥⑨ 在 SKILL.md 层面改动，对三仓等效生效。

## 改动清单

| # | 改动 | 位置 | 性质 | 预期收益 |
|---|---|---|---|---|
| ① | 单一盘面：每轮全量 → 收口一次全量 | `sdflow-implement/SKILL.md:328-330` | 承重条款 | 全量重跑 `N×` → `1×` |
| ② | `test-suites` 支持成本分档（quick/full） | `SKILL.md:313-322` + 各仓 `config.yaml` | 契约扩展 | 每票与中间轮改跑 quick |
| ③ | `review-package.diff` 增量化 | `SKILL.md:583` | 局部 | 直接省 token（最大 1,356KB → 本轮 delta） |
| ④ | `review-loop-breaker` 补与指纹无关的硬上限 | `SKILL.md:651-657` | 承重条款 | 从源头压轮次 |
| ⑤ | 出票闸门：禁手搓解析器型验收标准 | `SKILL.md:270` 附近 | 承重条款 | 消除不收敛票的成因 |
| ⑥ | **`sdflow-code-review` 补 fix 循环熔断** | `sdflow-code-review/SKILL.md` | 承重条款 | 该侧现为零上限，fix8 即出于此 |
| ⑦ | mqtt-console 补 `test-suites` 配置 | 该仓 `openspec/config.yaml` | 纯配置 | 消除每轮重判 + 固化 quick 档 |
| ⑧ | `sdflow-retro` 按管线代际分桶重跑 | 本仓 | 调研 | 确认 P0 基线是否需重排 |
| ⑨ | red-before-green 扩展到「往既有测试补断言」 | `sdflow-implement/SKILL.md:509` | 契约扩展 | 消除第 2 类（测试有效性返修） |
| ⑩ | Standards 轴明确覆盖测试文件的冗余检查 | `SKILL.md:610` 附近 | prompt 扩展 | 给测试单调累积装闸 |
| ⑪ | **本仓：共享子集解析器 + 界外 fail-loud** | `init.py` / `ship_gate.py` / `impl_route.py` / `lens_metric_emit.py` | 架构 | 消除 5 份重复实现各补各分支 |
| ⑫ | `sdflow-devenv` 加「格式解析手段对照表」 | `sdflow-devenv/references/verification-patterns.md` | 知识库扩展 | 给下游项目前置正确手段 |
| ⑬ | mqtt-console 静态门改用 `svelte/compiler` 的 `parse()` | `frontend/src/lib/shell/dialogButtons.static.test.js` | 换手段 | 300 行正则 → AST 查询，零新增依赖 |

### ① 单一盘面：每轮全量 → 收口一次全量

> **原则（本清单的核心）**：全量运行次数与 **change** 挂钩，与 **fix 轮次** 解耦。
> 这是唯一一条改耦合关系的改动，其余各条都只是压轮次——**不做这条，问题只会推迟发生**。

- **中间 fix 轮**：只跑受影响层 + 上轮失败层；结果**仅供诊断，不作证据**（报告中标注为诊断行）。
- **收口时**（双轴审判 PASS、打完成标签前）：跑一次全量，报告中所有判「通过」的行锚同一最终 SHA。
- **语义零损失**——单一盘面本就只约束最终报告的通过行同盘面，该改动不触碰这一点。
- **代价**（三镜）：系统镜——中间轮窄跑可能漏回归，但收口全量必然抓到，无净损失；
  用户镜——无感；开发循环镜——中间轮不必等全量，反馈更快。
- **反例仍须挡住**：`unit@A → integration@B` 拼接式「全部通过」依旧非法。

### ② `test-suites` 成本分档

`test-suites.{unit,integration,e2e}` 每层可选配 `quick` / `full` 两条命令
（只配一条时视为两档同命令，向后兼容）。中间轮与普通功能票跑 `quick`，收尾票跑 `full`。

### ③ `review-package.diff` 增量化

fix 轮只打包 `上轮SHA..HEAD`。reviewer 需要全量上下文时自行读文件
（符合 `SKILL.md:517`「大产物走文件交接，不进 prompt/返回值」的既有原则）。

### ④ / ⑥ 熔断硬上限（两侧同构）

在现有判据之外增加一条**与指纹无关的上限**：同一文件累计被 Critical/Important finding
命中 ≥3 轮 ⇒ 无论指纹是否相同一律熔断，升 strong 档仲裁
「**这个门本身该不该存在**」（而非继续仲裁单条 finding 是否成立）。

- `sdflow-implement`（④）：叠加在既有 `review-loop-breaker` 上。
- `sdflow-code-review`（⑥）：该侧目前**无任何熔断**，需新建规则；建议与 implement 侧同构，
  避免两套语义。
- **代价**：可能对真·不同问题提前熔断；但处置是升档复核而非直接放过，风险低。

### ⑤ 出票闸门

在出票模式的验收标准约束中加一条：验收标准若要求「扫描源码 / 识别写法指纹 /
静态门拒绝某种代码形态」，MUST 先判该语法面能否穷举——
- **有界**（如 CommonMark fence 变体）⇒ 可写解析器；
- **无界**（通用编程语言源码、YAML、make、shell）⇒ **MUST NOT** 写成机械门，
  改为「让工具自己回答」（真跑一遍看行为），或降级为 best-effort 展示且不作判定依据。

即把 CLAUDE.md 基准 5 从设计/评审环节下沉到**出票**环节。
三个标本（YAML / JS / shell 命令解析器）都会被这道闸门拦下。

### ⑨ red-before-green 扩展到「补断言」场景

现表述（`SKILL.md:509`）为「**先写失败测试**，再写刚好够通过的代码」——只覆盖新写测试。
扩展为：**往既有测试补一条断言时，同样 MUST 先确认它会红**
（当场故意破坏被测点，看断言是否失败）。

- **成本**：一次聚焦运行，秒级。
- **收益**：消掉事后才发现恒真锚、再回头返修的整轮工作（第 2 类）。
- 与既有实践一致——恒真锚的判定方法本就是「定点删门 → 必须红」，
  本条只是把它从**事后 review 的发现手段**前移为**写入时的当场自检**。

### ⑩ Standards 轴覆盖测试冗余

在 Standards 轴的 dispatch 范围中明确：Fowler 清单的 **Duplicated Code** 与
**Speculative Generality** 同样适用于**测试文件**——重复的测试形状应合并，
为想象中的需求预写的测试应删除。

- **代价**：Standards 轴 prompt 略增；有误删有效测试的风险，故限定为
  **报告为 finding 交由裁决**，MUST NOT 由 reviewer 直接删测试。
- **必要性**：这是目前唯一能遏制「测试单调累积 → 全量成本单调上升」的机制。

### ⑪ 本仓：共享子集解析器 + 界外 fail-loud

详见「手搓解析器的制度性根因」节。三个执行要点：

1. **子集规格先行**——先写「支持哪些 YAML 构造」的规格，再写实现；规格即测试的期望集。
2. **界外 fail-loud，不猜**——错误信息 MUST 指名不支持的构造并给改写建议。
3. **单一源 + `--check` 门禁分发**——套用 `hack/sync_principles.py` 既有范式绕开 GC-2 边界锁。

- **代价**（三镜）：系统镜——新增一个单一源 + 一道同步门禁，但换掉 5 份各自漂移的实现，净降；
  用户镜——配置里用了界外构造的人会**看到明确报错而非被静默误判**，是改善；
  开发循环镜——一次投入，消除「每轮 review 在某个脚本里挖到新分支」的常态。
- **主次**：系统镜为主——这是把 N 份脆弱实现收敛成 1 份受规格约束的实现。
- ⚠️ **不得借机放宽零依赖不变量**：该不变量支撑「symlink 进任意消费仓」的承诺，
  与本条无关，MUST NOT 顺手改动（通则③：不加宽）。

### ⑫ `sdflow-devenv` 格式解析手段对照表

在 `references/verification-patterns.md`（现有负面知识库）中增补一张对照表，
并由 devenv 在初始化时扫描项目实际用到的结构化文件格式，把适用行写进真相源文档：

| 情形 | 手段 |
|---|---|
| 有标准库（JSON / TOML 3.11+ / Python `ast`） | 直接用库 |
| 有权威第三方库且项目可依赖（YAML → PyYAML） | 用库 |
| 工具自身即权威（Makefile / shell） | 让工具跑一遍（`make -n` / `bash -n`） |
| 都没有 | 收窄子集 + 界外 fail-loud |

- **边界**：本条服务**下游项目**（多数无零依赖约束，直接用库即可），
  **不解决本仓病灶**（本仓走 ⑪）。两条独立，MUST NOT 混为一条。

### ⑬ mqtt-console 静态门改用官方 AST

详见「标本 B」节。`import { parse } from 'svelte/compiler'`（已在依赖内，零新增）
取代 300 行正则拼装。

- **收益**：r1–r3 三轮 finding（select 误分类 / inverse-guard 绕过 / resolver 未绑定）
  中的前两条在 AST 下不成立，第三条降为一次性的语义断言。
- **代价**（三镜）：系统镜——测试依赖 Svelte 编译器的 AST 形状，
  大版本升级时可能需跟随调整（但远优于跟随任意 Svelte 语法写法）；
  用户镜——无感；开发循环镜——从「每轮补一个语法分支」变为一次性投入。
- **主次**：开发循环镜为主。
- **保留语义残余**：跨文件 canonical identity 一致性仍由语义断言承担，不强求机械化。

## 「每轮全量重跑」条款实际未被执行 —— 一个实证

调研期间在本仓 `main` 上发现 **8 个既有红测**（`sdflow-init/tests/test_runtime_gitignore.py`）：

```
TypeError: <lambda>() got an unexpected keyword argument 'include_schema'
TypeError: <lambda>() got an unexpected keyword argument 'schema'
```

成因：`align-sdflow-spec-with-openspec-schema` 给 `copy_bundle` / `handle_config`
新增了关键字参数，而该测试的 monkeypatch stub 签名没跟上。

**关键点：那个 change 跑了 37 个 fix 轮、深至 fix8，仍然漏掉了它。**

推论——**`SKILL.md:328-330` 的「每轮全量重跑」在实践中并未真正执行**：
若曾有任何一轮真跑过全仓 pytest，该回归必然当场暴露。
它成本太高，实际执行时被隐性打了折（implementer 只跑自己判定的"受影响层"，
而 `test_runtime_gitignore.py` 测的是 gitignore 合并、不在 schema 改动的显性影响面内）。

**这对清单 ① 是正面支持，不是反驳**：

| | 现状 | ① 之后 |
|---|---|---|
| 条款要求 | N 轮 × 全量 | 1 次全量（收口） |
| 实际执行 | **打折的 N 轮**（本例即漏） | 1 次**真**全量 + 证据 schema 锚 SHA |

**要求 N 次而实际执行打折，不如明确要求 1 次并真的验证它。**
⇒ ① MUST 与 ②（`test-suites` 显式配置）同批落地：收口那一次全量必须有
**确定性的命令来源**，不能再由 implementer 每次临时判定范围。

（该回归已在本轮直接修复，见「落地分组 · 已完成」。）

## 落地分组

### ✅ 已完成（change `curb-rework-loop-cost`，2026-07-31 merge `c558109`）

| 项 | 交付物 | 承载 |
|---|---|---|
| ① | 单一盘面→中间轮/收口轮分离（`sdflow-implement/SKILL.md` 第 7 条） | change |
| ② | test-suites 成本分档 quick/full（聚合套件发现契约 + config.template.yaml + devenv 发现能力） | change |
| ③ | review-package fix 轮增量化（上轮已审 SHA..HEAD） | change |
| ④ | 熔断硬上限（判据 b 同文件≥3 轮 + subsume + 全 change 窗口 + breaker-ledger） | change |
| ⑤ | 出票语法面有界性闸门（含伪装形态 + 回指对照表） | change |
| ⑥ | code-review 复审边界（硬上限 1 轮 + 文档分叉消除） | change |
| ⑨ | red-before-green 扩展到补/改断言 | change |
| ⑩ | Standards 轴覆盖测试文件冗余检查 | 报告期间直接修 |
| ⑫ | 格式解析手段对照表（verification-patterns.md §8） | change |
| ⑧ | P0 基线口径校准（三仓分桶分析，确认未倒挂） | 调研，见上节 |
| — | sdflow-init/tests 签名漂移回归修复（8 failed → 0） | 报告期间直接修 |

### 剩余（未开）

| 项 | 内容 | 位置 | 优先级 |
|---|---|---|---|
| ⑪ | 共享子集 YAML 解析器 + 界外 fail-loud | 本仓 5 个脚本 | 中（独立 change，blast radius 大） |
| ⑦ | mqtt-console 补 `test-suites` 配置 | 该仓 config.yaml | 中（② 落地后的消费端，5 分钟） |
| ⑬ | mqtt-console 静态门改用 `svelte/compiler` 的 `parse()` | 该仓测试文件 | 低 |
| — | 格式解析手段体检工具（`sdflow-devenv` 子命令） | 本仓 | 低（依赖 ⑫ 已落地） |

### 其他仓（建议，由用户自行处理）

#### mqtt-console

**A · 补 `test-suites` 配置（⑦）** —— `openspec/config.yaml` 顶层新增：

```yaml
test-suites:
  unit:
    quick: cd frontend && npm test -- --run
    full:  cd frontend && npm test -- --run
  e2e:
    quick: cd frontend && npx playwright test src/tests-e2e/
    full:  make e2e-live && cd frontend && npm run test:e2e && npm run build
           && wails build && hack/verify-native-dialog-matrix.sh
           && hack/verify-native-dialog-interactions.sh
```

要点：把已存在但未制度化的 `TASK6_NATIVE_QUICK`（`hack/verify-native-dialog-matrix.sh:85`）
接到 `quick` 档；**含 `wails build` 的重链只留在 `full`**。
收益：implementer 不再每轮临时判定范围，且中间轮不会误跑打包链。
（`quick`/`full` 双档需本仓 ② 落地后才被消费；在此之前配置无害且向后兼容。）

**B · 静态门改用官方 AST（⑬）** ——
`frontend/src/lib/shell/dialogButtons.static.test.js`（300 行正则）改为：

```js
import { parse } from 'svelte/compiler'   // svelte@^5.56.4 已在 devDependencies，零新增依赖
```

替换掉 `withoutComments()` 的注释正则剥离、`{#snippet footer(){...}}` 的块提取、
`function\s+${name}\s*\(` 的 resolver 查找、`class\s*=\s*(['"])(...)\1` 的属性解析。
保留跨文件 canonical identity 一致性作为语义断言（合法残余，勿强求机械化）。

#### zhws_ops_api

**无需专项修复。** 它是三仓中最健康的：最近两个 change（`collapse-perm-modes-to-role-matrix`、
`refine-device-auth-ui`）**fix 轮 = 0**，跑测试痕迹仅 16 / 9，report/实现比 2.10x（三仓最低）。
其 `perm_modes_consumer_test.go` 被 5 个 change 回访已确认为**需求演进**，非流程问题。

它会**被动受益**于本仓 ①②④⑤⑥⑨ 的落地，不需要仓内改动。

## 工具：如何避免此类问题重复发生

三层，**只有第三层是机械的**——前两层是指令层约束，由执行方自报，这是诚实边界。

### 第一层 · 前置：devenv 初始化时写入「格式解析手段对照表」（⑫）

项目建立测试环境时就把手段定下来，而不是等实现期临时决定。
对照表见清单 ⑫。落点 `sdflow-devenv/references/verification-patterns.md`
（现有负面知识库，同构）。

### 第二层 · 拦截：出票闸门（⑤）

验收标准若要求「扫描源码 / 识别写法指纹 / 静态门拒绝某种代码形态」，
出票时即判该语法面能否穷举，无界则不得写成机械门。

### 第三层 · 检测：格式解析手段体检（新工具，`sdflow-devenv` 子命令）

扫项目里所有脚本与测试，输出一张**体检表**：

| 文件 | 正则密度 | 疑似解析的格式 | 该格式的推荐手段 | 项目是否已有该依赖 |
|---|---|---|---|---|
| `dialogButtons.static.test.js` | 40+ | `.svelte` 源码 | `svelte/compiler` 的 `parse()` | ✅ `svelte@5.56.4` |

**最后一列是这个工具的全部价值**——mqtt-console 那个案例里，
「权威解析器已在依赖内」这个事实一直存在，只是没人看见。

三条设计约束（缺一即退化为它要治的那个病）：

1. 🔴 **它是体检报告，不是门**——只提示、不拦截、不 fail-closed。假阳无害，
   符合基准 5 的降级判据（「给人看的展示允许 best-effort」）。
2. 🔴 **它自己 MUST NOT 解析被检文件的语法**——只统计正则数量 + 匹配格式标志性
   token（``` / `---` / `<!--` / `{#snippet` / `^\|`）+ 读依赖清单
   （`package.json` / `pyproject.toml` / `go.mod`）。**一旦它开始解析，
   它就成了下一个手搓解析器。**
3. **推荐手段来自第一层的对照表**——单一源，不在工具里重复维护一份判据。

## 附录 · 数据口径与复现

### 口径

- **文件分类正则**：`REPORT` = 路径含 `impl-report`/`impl-blocker`；
  `TEST` = 路径含 `tests?/`、`__tests__/`、`e2e/`，或文件名匹配 `test_*`、
  `*_test.{go,py,ts,js}`、`*.{test,spec}.{ts,tsx,js,jsx}`、`conftest.py`；
  `DOC` = 含 `openspec/`、`docs/` 或 `.md` 结尾；其余 `IMPL`。
- **行数** = 增 + 删（`--numstat` 两列之和），反映改动工作量而非净增。
- **fix 轮** = `impl-reports/` 下匹配 `fix\d+\.md$` 的文件数；**最深** = 其中最大轮次号。
- **跑测试痕迹** = 报告正文中匹配 `\d+/\d+ (PASS|passed|通过)` 或
  `pytest|npm test|go test|playwright test|make test|make e2e|wails build` 的行数。
  这是**相对指标**（用于横向对比 change 间的量级差），不等于套件实际执行次数。
- **活跃墙钟** = 相邻 commit 时间差之和，单个间隔 >90min 截顶为 90min
  （与 P0 的含人类门 elapsed 口径**不同**）。
- **删/增比** = 测试文件的删除行 ÷ 新增行。接近 0 ⇒ 纯累积；接近 1 ⇒ 在重写既有测试。
- **回访次数** = 同一测试文件在窗口内被 commit touch 的次数（`git log -- <file>` 计数）。

### 已知局限

- **「每 fix 轮对应一次全量重跑」是条款推导**（`SKILL.md:328-330` 的 MUST），
  非逐轮实测；实测支撑是「跑测试痕迹」随 fix 轮档位从 12.5 → 34 → 109 单调上升。
- 界面验证测试的重跑次数由 evidence root 唯一标识去重得出，是**下界**——
  报告未引用的中途运行不可见。
- **单次运行耗时无直接记录，且不打算补测**——本清单不采用定量验收门。理由见
  「为什么这是结构性问题」：待优化量（全量套件单次成本）本身随项目复杂度单调上升，
  任何此刻测出的秒数都会过期，拿它当阈值只会催生一轮很快失效的调参。
  验收改用**结构判据**：全量运行次数是否与 fix 轮次解耦（每 change 收口一次）。
- 阶段占比的倒挂涉及口径差异（见「对 P0 基线的改写」），不足以单独推翻 P0。

### 复现命令

```bash
# 代码量分类统计
git -C <repo> log --since "7 days ago" --numstat --pretty=format:@@%h

# 返工轮次分布
ls <change>/impl-reports/ | grep -cE 'fix[0-9]+\.md$'
ls <change>/impl-reports/ | grep -oE 'fix[0-9]+' | grep -oE '[0-9]+' | sort -n | tail -1

# 界面验证测试重跑次数
grep -rh "/tmp/mqtt-dialog" <change>/impl-reports/*.md | sort -u
```
