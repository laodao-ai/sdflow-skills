# tasks —— `add-sdflow-devenv`

> **构建顺序 = 脑 → 手 → 记性**〔`07` §3 · 附录 **A28**〕。
> **⚠️ 顺序本身是设计的一部分**：把 `references/` 和 `SKILL.md` 排在机械基础设施后面，就是 A23/A28 的病灶本身
> （「全部力气花在机械可验的东西上，核心承诺零字」）。**A 层先行，不可颠倒。**
>
> checkpoint 格式：`~/.sdflow/hack/checkpoint-commit.sh task<N>-<slug> "<msg>"`

---

## 0. 前置

- [x] **设计重定基**——`docs/sad/07` 按 grill 九条决策（D1–D9）改写；附录 A23–A28 记否决理由
- [x] **ADR**——`adr/0021`（代价可见 > 机械拦截）· `adr/0022`（skill 只改不删）
- [x] **CONTEXT.md**——落术语：副驾 · 留白/待定 · 层（保真度刻度）· 层状态（投影）
- [x] **规则**——`openspec/rules/doc-authoring.md`（DOC-1）+ `spec-quality-base.md` BASE-30

## 1. ⭐ A 层（脑）—— skill 的全部价值

- [x] **`references/testing-framework.md`**（258 行）—— **三层 × 六槽提问清单**。核心承诺的唯一载体；`SKILL.md` 第 ② 步就是在跑它
  - 形态四问（决定项目有哪些真实边界）· 三层判据（保真度刻度）· 逐槽话术 + 判据 + 反模式 · ⑥ 槽（信心与盲区）
- [x] **`references/environments-template.md`**（十槽）—— **dev 搭建 + deploy 发布**的提问清单。点名最贵三槽：常见坑 · 回滚 · 构建副产物
- [x] **`references/lane-patterns.md`**（200 行）—— 五个形态格的阶梯原理。**它是 `testing-framework` 槽③④ 的附属，不是平行组件**〔A28〕
- [x] **`references/verification-patterns.md`**（181 行）—— **负面知识**：证伪过的验证方法（计数门槛 / negative control / 轮询观测 / proxy 计数）+ 「所有机械层同时失效」的真实案例
- [x] **`references/review-lenses.md`**（129 行）—— 冷审镜单。**vacuous 镜 + 盲区镜是心脏**
- [x] **`references/boundary-rules.md`**（92 行）—— 归位模式的归属判据 + 三种失效处置（**skill 无删除能力**）
- [x] **`SKILL.md`**（245 行）—— 五步编排 + 三模式 + 人门议程 + **五条红线**

## 2. B 层（手）—— 建造，不是评估

- [x] **`devenv_scaffold.py`**（490 行）
  - [x] `init` —— preflight + 模式分流（exit 3 无 openspec / exit 4 已存在）+ **铺 `environments.md` 十槽骨架** + SAD 缺失响亮降级
  - [x] `set-layer` / `set-lane` —— 写 JSON；**`set-lane --status verified` 拒绝（exit 5）**
  - [x] ⭐ **`verify-lane`** —— **亲自 fork 执行，拿真 exit code**。跑红 → `scaffolded` + `blocked_by`（**脚本退出码仍为 0**）· 超时如实记不确定性 · **捕获 make 自己打的 `overriding` warning**〔A24〕
  - [x] `confirm-lane` —— 人工验证，**如实标 `attested_by: human`**
  - [x] `render` —— `.devenv.json` → `testing-strategy.md`（**层状态从泳道投影**）
  - [x] `inject` —— `opsx-devenv` 托管块，幂等整块替换
- [x] **红线测试**：AST 扫描证明 **无 `unlink`/`rmtree`/`remove`**〔`adr/0022`〕· **不 `import re`**〔A21〕

## 3. C 层（记性）—— 够用就行

- [x] **`devenv_schema.py`**（283 行）—— **一份 `.devenv.json`**（layers + lanes）
  - [x] 只拦**结构与枚举**（人看不见的）；**内容完整性移交 lint**（人一眼看得见的）
  - [x] **`⚠️ 待定` 合法**——十五格全待定亦过 schema〔`adr/0021`〕
  - [x] **层状态 = 投影**（`layer_status()`），**MUST NOT 手写**〔A25〕
  - [x] **删封闭枚举**：`LANE_KINDS` / `DEP_KINDS` / `source.kind` 全废〔A24〕。`layer` 是唯一保留的（核心承诺的骨架）
  - [x] **零 digest / 零锁 / 零 make 知识**〔A21 · A23〕
- [x] **`devenv_paths.py`**（84 行）—— containment（**路径穿越是人看不见的 ⇒ 必须拦**）
- [x] **`devenv_lint.py`**（191 行）—— **只报不拦，永远 exit 0**
  - [x] 代价横幅 · `environments.md` 待定计数（**固定字符串计数，非解析结构**）· 未 verified 泳道逐条 · 敷衍 `blocked_by` · `covers` 差集
  - [x] 唯一 fail-closed：**坏 JSON**（人看不见 —— 渲染不出来只剩空白文档）

## 4. 测试

- [x] **107 tests green**（`test_schema` / `test_scaffold` / `test_lint` / `test_paths`）
- [x] **端到端手跑通**：init → 逐槽问 → 泳道 → `verify-lane` 真跑 → render → lint

## 5. 上下游 skill 改动

- [x] **`sdflow-architecture`**：description 加过程轴分流句（「建 dev/test 环境 / 定测试策略 → `/sdflow-devenv`」）；交棒话术从「给模板路径」改为**指向下游 skill**（spec: `architecture-design`）
  > ✅ description 加过程轴分流句 + §5.3 交棒改指 `/sdflow-devenv`（原只给模板路径）。
- [x] **`sdflow-maintain`**：检出 `.devenv.json` → 调 `devenv_lint`，**原样并入报告**（spec: `maintain-scan`）
  > ✅ `scan_devenv()` 原样透传 lint 报告（不重渲染 ⇒ commit 锚不丢）；**不计入 any_diff**（提醒非门禁）；6 个 Scenario 逐条有测试。
  - **⚠️ 它是 devenv「不强制完成」的另一半**——不强制完成 + 不检查未完成 = 名存实亡

## 6. 仓级集成

- [x] `setup.sh` 重跑——`sdflow-devenv/` 现有 `SKILL.md`，装进 `~/.claude/skills/` 与 `~/.codex/skills/`
- [x] README「Skills 列表」加 `sdflow-devenv`
- [x] `CLAUDE.md` 的「数据类 skill」清单加 `sdflow-devenv`（它有 scripts + tests）

## 7. ⭐ 首个真实试点（验收兼路线证伪）

- [x] **在一个真项目上跑一遍**（候选：`mqtt-console` —— 它是本设计的接地样本，六泳道横跨三运行时）
- [x] **验 A-8**：「模型能不能为三层提出**像样的**验证方法」——**这个前提至今零实证**
- [x] **验核心承诺**：产出的 `testing-strategy.md` 是否**每层交代清楚、一层不留白**
- [x] **验 ⑥ 槽**：「这层看不见什么」写出来的是**套话**，还是**这个项目特有的那句**
- [x] 试点结论回灌 `references/`（未覆盖的形态 → 补格；证伪的方法 → 记入 `verification-patterns.md`）
  > 回填 2026-08-20：核验 commit `fb165c3 checkpoint(add-sdflow-devenv:task7-pilot)` 已把 mqtt-console 试点结论回灌 `sdflow-devenv/references/verification-patterns.md`（含「残留 session 泄漏探针」「MQTT 3.1.1 CONNACK 规定」等真实证伪案例）与 `testing-framework.md`，此前的「未做」注记已过期。

## 8. 收尾

`/sdflow-code-review`（远程 PR）（已作废，非勾选项）
  > ⏭ **按用户明示跳过** —— 直接走 `/sdflow-done`（verify 仍为唯一终门）。（回填 2026-08-20：确未执行，改写为无复选框说明段，非过门假勾）
- [x] `/sdflow-done` —— verify → archive → commit → merge
