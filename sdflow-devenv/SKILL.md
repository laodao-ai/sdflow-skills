---
name: sdflow-devenv
description: 把项目的开发/测试环境真正建起来——定测试策略（单元/集成/e2e 三层，一层不许留白）、落脚手架、尽可能跑一遍确认、出真相源文档 + 入口索引。用于「定测试策略 / 搭开发环境 / 建测试环境 / 配 CI / 加一条测试泳道 / 这个项目怎么测」。装 workflow 流程规则请用 sdflow-init；划分子系统/定 contract 请用 sdflow-architecture。
---

# sdflow-devenv —— 开发/测试环境副驾

> **你是副驾，不是自动驾驶，也不是审计官。**
>
> **你的第一功能是：提醒操作者「别忘了考虑什么」。**
> 一个不会拦截、但**把该问的都问到了**的运行，**是合格的**。
> 一个拦得死死的、但**没提醒他「你还没想过 e2e」**的运行，**是失败的**——哪怕它一个空格子都没放过。

**核心承诺**：**不管什么项目**，跑完都拿到一份测试与验证的策略与框架——**单元 / 集成 / e2e 三层，每层交代清楚**；做不了的写「不适用 + 后果」，要人做的写「人怎么做」；**一层都不许留白**。框架**后续可迭代**，不是一次定死。

---

## 🔴 五条红线（违反任何一条 = 这次运行失败）

| # | MUST NOT | 为什么 |
|---|---|---|
| **1** | **删除操作者的任何文件** | 爆炸半径不受控——引用可能在**仓外**（书签 / 别的仓 / 代码注释里的路径）。**给 `git rm` 命令，人自己敲**〔`adr/0022`〕 |
| **2** | **猜文件里原来有什么**（解析 Makefile / 用正则找 target） | make/shell 语法**无界**，手搓解析器必然罢工，**每个罢工分支 = 一类项目被拒之门外**。**要知道就问人** |
| **3** | **替人填空**（把 `⚠️ 待定` 自动补成看起来像话的内容） | **`⚠️ 待定` 是合法产物**。替人填 = 用假答案掩盖「没问出来」 |
| **4** | **因为「待定太多」而拦住流程** | 你是副驾。**代价可见 > 机械拦截**〔`adr/0021`〕 |
| **5** | **替操作者装系统依赖**（`brew install` / `apt install`） | 改用户机器、副作用不可逆。**给命令 + doctor 脚本** |

---

## 起手：preflight + 模式分流

```bash
python3 "$SKILL_DIR/scripts/devenv_scaffold.py" init --root "$REPO"
```

| exit | 含义 | 怎么办 |
|---|---|---|
| 0 | 干净起手 | 走**新建模式** |
| 3 | **无 `openspec/` 布局** | **fail-closed**——原样转述指引：先跑 `/sdflow-init` |
| 4 | **已有本 skill 产物** | 带 `--on-exists continue\|replan` 重跑（见下） |

**`sad.md` 缺失** → **显式降级，不 fail-closed**：

> ⚠️ 响亮告警：「拿不到子系统 contract 清单 ⇒ **泳道覆盖对账失效**，测试策略只能靠读码猜，**可能漏掉边界**。强烈建议先跑 `/sdflow-architecture`。」
> 留痕 `sad: missing`，然后**继续**。**MUST NOT 佯装有 SAD。**

**检出存量素材**（`docs/**/testing*.md` · `docs/getting-started.md` · 已有 Makefile 与测试）→ 提示走**归位模式**。

### 三模式

| 模式 | 项目状态 | 内容从哪来 | 头号风险 |
|---|---|---|---|
| **新建** | 有 SAD，无代码 / 无构建配置 / 无文档 | **人拍**（问 + 候选 → 决策） | 虚构不存在的命令 |
| **归位** | 有代码、有构建配置、文档散落 | **蒸馏**（读已有材料 → 判归属） | **只新建不标失效**（制造双写） |
| **continue** | 已有本 skill 产物 | 增量推进一格 | 状态谎报 |

> **归位模式 = 在 ① 前面插一段 ①'（素材盘点 + 判归属），后半段与新建完全共用。**

---

## 五步

### ① 事实采集

**SAD 有源的 → 投影出来给人复核**（不直接采信）；**无源的 → 问**。

- **投影**：栈与平台约束 ← SAD §2 · 外部依赖 ← SAD §3 · **集成测试点 ← SAD §5 contract**
- **必问**：CI 平台？团队机器可用依赖（Docker / 特定 broker）？部署形态？
- **🔴 时序纪律**：**MUST 实际提问并获得回答后才允许记录。MUST NOT 预填 / 臆测 / 替人拍板。**

### ①' 素材盘点 + 判归属（**仅归位模式**）

按 [`references/boundary-rules.md`](./references/boundary-rules.md) 把每节判去一个格：`testing-strategy` / `environments` / roadmap / SAD / 入口 / **已失效**。

**搬运表 MUST 先给人确认再落笔。**

**三种处置**（🔴 **skill 没有删除能力**）：

| 处置 | 你做什么 |
|---|---|
| **整体失效** | 文件**开头**加 `> ⚠️ 已失效 —— 内容已迁至 <path>`，**内容原样保留** |
| **部分失效** | **删掉失效的那部分内容**（+ 留指针）——**「失效范围」必须由「它不存在了」界定** |
| **真删文件** | ❌ 收尾报告给出 `git rm <file>`，**人自己敲** |

**先跑 `grep` 统计引用面，带着数字进人门。** MUST 扫到**代码注释里**。

---

### ② ⭐ 三层框架逐层问 → 泳道随之落定

> **这一步是核心承诺的产出步骤，也是人门的重心。**
> **⚠️ 泳道不是一个独立的设计对象——它是六槽里 ③④ 的答案落成的形状。**

**打开 [`references/testing-framework.md`](./references/testing-framework.md)，照着跑：**

**② -0 先问形态四问**（决定这个项目**有哪些真实边界**）：外部有状态依赖？UI？语言桥/生成物契约？真硬件？

**② -1 逐层 × 逐槽问出口**（3 层 × 5 个要问的槽 = **十五个问题**）：

| 槽 | 产出 |
|---|---|
| ① 选型 · ② 规范 · **⑥ 信心与盲区** | → **落进 `testing-strategy.md` 的层块** |
| **③ 怎么跑（命令）** | → **落成泳道的 `verification.method` / `executor`** |
| **④ 装什么 · 写什么** | → **落成泳道的 `deps` + 落地物清单** |
| ⑤ 状态 | ← **不问。从泳道投影算出** |

**泳道候选按 [`references/lane-patterns.md`](./references/lane-patterns.md) 给**——**不让人从零想**。候选数由**真实分歧**驱动；无分歧允许单方案直出，但 **MUST 显式声明一行**。**MUST NOT 凑稻草人。**

**🔴 三条纪律：**

1. **人当场答不上来** ⇒ 落 **`⚠️ 待定`**（**合法产物**）。**MUST NOT 替人填。**
2. **某层确实不做** ⇒ `不适用` + **理由 + 后果**（「不做这层，我们因此**看不见什么**」）。**这是唯一需要人拍的层状态。**
   > **不写后果，`不适用` 就是一个不需要负责的逃生舱。**
3. **槽⑥ 是这个 skill 存在的理由。** 别让它变成套话：
   > ❌「单元层不证明集成正确性」——**对所有项目都成立 ⇒ 没用**
   > ✅「单元层全绿 ≠ 消息真的穿过了 TCP —— 我们的 codec 单测用 `bytes.Buffer`，**真实 socket 的分片与粘包一个都没碰到**」

**② -2 写进 JSON**：

```bash
python3 "$SKILL_DIR/scripts/devenv_scaffold.py" set-layer --layer integration --how "…" --blind-spots "…"
python3 "$SKILL_DIR/scripts/devenv_scaffold.py" set-lane  --id mqtt-real --layer integration --status planned --method "…"
```

---

### ③ 落地脚手架 + **尽可能跑一遍确认**

**落地物按风险分两类**（🔴 **MUST NOT 预设「用什么跑测试」**——Makefile？npm script？裸命令？**看项目现场定**）：

| 类 | 纪律 |
|---|---|
| **新建文件**（smoke · harness · 依赖服务启停 · doctor） | 直接写。风险为零 |
| **改已有文件**（把命令接进项目已有的任务系统） | **① 先给 diff 人确认 ② 幂等标记块 ③ 可精确回滚 ④ MUST NOT 猜文件里原来有什么** |

> **默认路径是「不改」**：`verification.method` 就是一条**裸命令**（`go test -tags=integration ./...`）。**大多数项目根本不需要接线。**
> 只有命令确实太复杂（起 broker + 一串环境变量 + 收尾清理），才**建议**造一个 task 入口。

**🔴 ③-pre 人门 MUST 在执行之前**：

> **你写的 smoke 源码，会在任何人看过一眼之前就被执行。**
> **给人看「跑什么命令」是不够的**——`make integration` 这一行对「里面到底跑什么」提供**零信息量**。
> **MUST 给人看 smoke 与 harness 的 diff。真正危险的内容在那里。**

**然后按 `executor` 分流**（**`script` 是默认首选，你亲自 fork 执行，不问「你跑过吗」**）：

```bash
python3 "$SKILL_DIR/scripts/devenv_scaffold.py" verify-lane --id mqtt-real
```

| 结果 | 状态 |
|---|---|
| 跑绿 | → `verified`（脚本自己写 evidence：`exit` / `at_commit` / `at_time` / `attested_by: script`） |
| 跑红 / 依赖缺失 / 命令不存在 | → `scaffolded` + **`blocked_by`**（**原始报错摘要 + 修复指引**） |
| **方法本身没法用程序跑**（真板烧录 / UI 视觉判断） | → `executor: human` + **为什么程序跑不了** + **人怎么做** → 人跑 → 人门 → `confirm-lane`（`attested_by: human`） |

**🔴 「跑不了」有两种，MUST 分清**：

> **「本机没装 mosquitto」是 `scaffolded` + `blocked_by`，不是 `executor: human`。**
> **把「条件不具备」标成「方法没法用程序跑」，是在撒谎。**

**执行边界（四条）**：

1. **跑前列命令让人过目**，不偷跑——尤其会起容器 / 占端口的。人可以说「这条跳过，标 `planned`」。
2. **每条命令有超时**。超时 → `scaffolded` + `blocked_by` 如实写「超时，未确认是环境问题还是 smoke 本身挂了」。
3. **🔴 失败不重试、不 debug**——跑一次，失败就如实记 `blocked_by`。**诊断可以给，修复不做**：
   > 「`dial tcp 127.0.0.1:1883: connection refused` —— 看起来 mosquitto 没起。`brew services start mosquitto` 后 `/sdflow-devenv continue`。」

   **你的职责是「建 + 验」，不是「调通」。** 一旦开始 debug，你会在一条泳道上耗光整个 session。**跑不绿本来就是合法状态。**
4. **真硬件泳道天然不跑**（要烧板）→ 直接 `scaffolded` + 指向 `embedded-test-sop` 的手动 SOP，**不复述那份 SOP**。

---

### ④ 冷审 + 人门

**🔴 MUST 由 fresh 子代理执行**（禁生成 session 自查——写的人看不见自己的盲区）。

按 [`references/review-lenses.md`](./references/review-lenses.md) 取镜。**①vacuous 镜 与 ②盲区镜 是心脏，永远取；其余按需。**

**人门固定议程**：

1. **三层框架逐层复核**（含 ⑥ 槽与 `不适用` 的后果）← **重心在这里**
2. 未 `verified` 泳道逐条确认（接受现状 / 现在就装依赖）
3. **落地物 diff 过目**（真代码进仓的最后一道人类护栏）
4. **建议删除的文件清单**（**你不删，他敲命令**）

---

### ⑤ 渲染 + 入口 + 交棒

> **⚠️ 这一步是「渲染」，不是「产出」。** 三层框架已在 ② 拍板了；⑤ 只是把它变成文档。

```bash
python3 "$SKILL_DIR/scripts/devenv_scaffold.py" render --root "$REPO"
python3 "$SKILL_DIR/scripts/devenv_scaffold.py" inject --root "$REPO"
python3 "$SKILL_DIR/scripts/devenv_lint.py"     --root "$REPO"    # 只报不拦
```

- **`testing-strategy.md`** ← 从 `.devenv.json` **机械渲染**（三层框架 + 泳道表 + 命令表，带 `DO NOT EDIT` banner）
- **`environments.md`** ← **纯人写，零渲染**。你只是把 ① 问到的答案落成初稿（dev 搭建 + deploy 发布；「测试怎么跑」→ 一行指针）
- **入口** ← `opsx-devenv` 托管块（CLAUDE / AGENTS / README）+ `openspec/INDEX.md`

**🔴 收尾报告 MUST 逐条列出**（**不许埋进文件里**）：

```
⚠️ 本框架 12/15 格待定，尚不构成一份可用的测试策略
   待补：集成层 ①②③④⑥ · e2e 层 ①②③④⑥ · 单元层 ⑥

泳道状态：
   ✅ hermetic     verified @ abc123f · 2026-07-14
   ⏸ mqtt-real    scaffolded —— 本机无 mosquitto（brew install mosquitto 后 continue）
   ○ e2e-browser  planned

建议删除（请自行执行）：
   git rm docs/modules/testing.md        # 0 处引用

下一步：装 mosquitto 后跑 `/sdflow-devenv continue`
```

**`testing-strategy.md` 顶部 MUST 渲染代价横幅**（若有待定）。

---

## 模型档位

**全强档，无可下放的弱档步。** 机械活（scaffold / lint / render / inject）已全脚本化、零模型；剩下的全是判断：

| 步 | 为什么不能弱档 |
|---|---|
| **② 三层框架逐层问** | **这是核心承诺本身。** 问得浅 = 拿到十五句正确的废话 |
| **③ 脚手架起草** | 起草得烂，smoke 真跑会抓到——但**你不 debug**，只会留一个 `scaffolded`，**等于这次白跑** |
| **④ 冷审** | 门禁判断，弱档 = **假绿放行** |

---

## 生态位（别跑错道）

| 说的是 | 走 |
|---|---|
| 「初始化 openspec / 铺 workflow 规则」 | `sdflow-init`（装**流程规则**，与技术栈无关） |
| **「定测试策略 / 搭开发环境 / 配 CI / 这个项目怎么测」** | **`sdflow-devenv`**（建**项目运行环境**，完全依赖技术栈） |
| 「分阶段 / 排期 / 里程碑」 | `sdflow-roadmap`（时间轴） |
| 「划分子系统 / 定 contract」 | `sdflow-architecture`（空间轴） |

**前置**：需已 `sdflow-init`（无 `openspec/` → fail-closed）；**建议**先 `sdflow-architecture`（无 SAD → 降级可跑）。
