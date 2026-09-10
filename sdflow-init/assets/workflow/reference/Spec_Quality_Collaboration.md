# Spec 质量保证：brainstorming vs autoplan 协作分析

> **历史分析**：`brainstorming`（superpowers）与 `autoplan`（gstack）两个 skill 均已退役，现行工作流由
> `/sdflow-spec`（生成，含澄清/拷问/生成三相位）与 `sdflow-spec-review` / `sdflow-code-review`（评审
> 编排器）取代。本文保留作为历史设计脉络参考，不代表现行流程；下文举例与产物路径均为历史口径。

> 基于 superpowers 6.0.3 brainstorming skill 和 gstack autoplan skill 原始文档的对比分析。
> 目标：找出两者如何分工，确保 spec 达到**完整、准确、正确、可执行**四个标准。

---

## 一、两个 skill 的本质定位

| 维度 | `/brainstorming` | `/autoplan` |
|------|-----------------|------------|
| **模式** | 对话驱动，生成设计 | 批量审查，评估计划 |
| **输入** | 模糊想法 / opsx:ff 产出 | 已有 plan 文件 |
| **输出** | 经批准的设计文档 | 4 个视角的评审报告 + 决策审计 |
| **门禁** | HARD-GATE：设计未获批不写代码 | 前提假设门禁（用户必须确认） |
| **AI 多视角** | 单视角（当前 session） | 双声音：Claude 子 agent + Codex 独立审查 |
| **交互节奏** | 一次一问，逐步收敛 | 4 阶段批量，最后一个确认门 |
| **产物存放** | `docs/superpowers/specs/YYYY-MM-DD-*.md` | gstack 内部 + 计划文件原地更新 |
| **与 OpenSpec 关系** | 可直接对 design.md 原地更新 | 读取 plan 文件，与 OpenSpec 间接对接 |

---

## 二、两者对四个 Spec 质量标准的覆盖

### 2.1 质量标准定义

| 标准 | 含义 |
|------|------|
| **完整（Complete）** | 所有场景、边界、错误路径都有描述；无空白占位符 |
| **准确（Accurate）** | 代码事实（函数名/字段/API 路径）与实际代码一致；无凭记忆的假设 |
| **正确（Correct）** | 设计逻辑自洽；架构/数据流/安全边界无矛盾；经过工程视角验证 |
| **可执行（Executable）** | 验收标准可量化；任务可独立执行；无"TBD"和双义描述 |

### 2.2 覆盖矩阵

| 质量标准 | brainstorming 覆盖 | autoplan 覆盖 | 覆盖程度 |
|---------|------------------|--------------|--------|
| **完整** | ✅ spec self-review：placeholder 扫描、scope 检查；逐节获批 | ✅ CEO Phase：scope challenge、alternatives；Eng Phase：edge cases、error paths | 双重覆盖，角度不同 |
| **准确** | ⚠️ 无代码事实核验机制（只靠对话） | ⚠️ Eng Phase 要求读实际代码，但 plan 文件不强制 grep | **漏洞最大的一块** |
| **正确** | ✅ 2-3 方案对比；逐节用户确认；内部一致性检查 | ✅ CEO Phase：前提假设挑战；Eng Phase：架构 ASCII 图、失败模式注册表、安全边界 | autoplan 更深（双 AI 独立视角） |
| **可执行** | ✅ spec self-review：ambiguity check；用户 review gate | ✅ Eng Phase：test diagram、test plan artifact；任务清单聚合 | autoplan 更具体（产出物落盘） |

---

## 三、brainstorming 的结构检查层（可提取部分）

brainstorming 的 **Spec Self-Review** 是一个独立的 4 步机械检查，与对话生成过程正交：

```
Spec Self-Review（4 项）
├── 1. Placeholder 扫描 — TBD / TODO / 不完整 / 模糊需求
├── 2. 内部一致性 — 各节是否互相矛盾？架构与功能描述是否对齐？
├── 3. Scope 检查 — 是否聚焦到足以生成单个实现计划？
└── 4. 歧义检查 — 任何需求是否可以有两种解读？
```

**这 4 项是纯结构性检查，不依赖对话上下文，可以独立成 skill。**

在 OpenSpec 工作流中，生成 prompt 里已额外注入了：
> `先按 @openspec/checklist/spec-quality-checklist.md 阻塞级检查项逐一检查`

这说明 spec 结构自检和内容精炼已经被人为分层——**前者是门禁，后者是优化**。

### 可提取为 `/spec-check` skill 的场景

| 场景 | 是否适合用独立 skill |
|------|-------------------|
| opsx:ff 后快速扫描，决定是否需要 brainstorming | ✅ 适合，轻量无需对话 |
| 已有 design.md，人工修改后做质量验证 | ✅ 适合 |
| eng-review 前的入场条件检查 | ✅ 适合 |
| 对话中动态发现盲点 | ❌ 不适合，需要 brainstorming 的对话机制 |

---

## 四、autoplan 的 Eng Review 做了什么（与 plan-eng-review 一致）

autoplan Phase 3（Eng Review）产出物：

```
必须产出（artifacts on disk or in plan file）：
├── "NOT in scope" 节（明确排除项 + 理由）
├── "What already exists" 节（子问题 → 已有代码映射）
├── 架构 ASCII 依赖图（组件关系）
├── 测试覆盖图（code path → test 类型映射）
├── 测试计划文件（~/.gstack/projects/...）
├── 失败模式注册表（critical gap 标记）
├── CEO / Eng 双声音共识表
└── Completion Summary
```

与 brainstorming 的 Spec Self-Review 相比：

| 层次 | brainstorming | autoplan Eng Phase |
|------|--------------|-------------------|
| **粒度** | spec 文档级（结构、占位符、歧义） | 系统级（架构、测试、安全、性能） |
| **视角** | 同 session 单一视角 | Claude 子 agent + Codex 双独立视角 |
| **深度** | 4 项机械检查 | 4 个 section，每节必须读实际代码 |
| **产出** | inline fix，无落盘文件 | artifacts on disk（测试计划、注册表） |

---

## 五、协作模式：如何确保 spec 完整、准确、正确、可执行

### 5.1 当前工作流的协作点

```
/opsx:ff
    ↓ 生成骨架（proposal + design + specs + tasks）
    │
    ├─ [快速路径 S 级]
    │   /brainstorming（可选）→ 结构检查 + 内容精炼
    │       ↓
    │   人工审阅 → /opsx:apply
    │
    └─ [标准路径 M 级]
        /brainstorming（必须）→ spec-quality-checklist 阻塞检查 → 内容精炼
            ↓
        /clear（安全点 A）
            ↓
        /plan-eng-review 或 /autoplan
        → Eng Review：架构/测试/安全/失败模式（保证 Correct + Executable）
```

### 5.2 四个标准的责任归属

```
完整（Complete）
  ├── 主责：brainstorming（对话驱动逐节确认）
  └── 补充：autoplan CEO Phase（scope challenge，发现遗漏场景）

准确（Accurate）
  ├── 主责：opsx:ff D-1 约束（代码事实 grep 再写入）
  └── 补充：autoplan Eng Phase（读实际代码，不凭记忆）
  ⚠️  brainstorming 和 autoplan 均无强制 grep 验证机制
       → 该标准主要靠 /opsx:ff 的 D-1 约束保证，而非 review 环节

正确（Correct）
  ├── 主责：autoplan Eng Phase（双 AI 视角，架构图，失败模式）
  └── 补充：brainstorming（2-3 方案对比，前提假设挑战）

可执行（Executable）
  ├── 主责：brainstorming spec self-review（ambiguity check）
  ├── 补充：autoplan Eng Phase（test plan artifact，任务聚合）
  └── 门禁：spec-quality-checklist（验收标准可验收性检查）
```

### 5.3 协作序列建议

```
阶段 1：生成（opsx:ff）
  → 通过 D-1 约束保证代码事实准确性（Accurate）

阶段 2：结构检查（brainstorming 第一层 or 独立 /spec-check）
  → 消除占位符、歧义、scope 过大（Complete + Executable 基础）
  → 人工确认方向

阶段 3：内容精炼（brainstorming 第二层 or 对话讨论）
  → 2-3 方案探索、盲点发现（Complete 深度 + Correct 初步）
  → HARD-GATE：设计批准后才继续

阶段 4：工程审查（plan-eng-review 或 autoplan Eng Phase）
  → 双 AI 视角验证架构、测试、安全（Correct 深度 + Executable 系统级）
  → 产出物落盘，不依赖记忆
```

---

## 六、是否应该提取独立的 `/spec-check` skill？

### 支持提取

- brainstorming 的 Spec Self-Review 是纯机械检查，与对话无依赖
- OpenSpec 工作流中，spec-quality-checklist 已在 brainstorming prompt 中注入，说明这两层已被人为分开
- S 级路径跳过 brainstorming 时，spec 结构检查没有兜底
- 可作为 opsx:ff → eng-review 之间的快速门禁

### 反对提取

- brainstorming 的结构自检和内容审查是连续的——修完占位符后立刻进入盲点探索，上下文没有中断
- 单独提取后，用户需要记住"先跑 /spec-check 再跑 /brainstorming"，增加心智负担
- openspec 的 spec-quality-checklist 已经承担了这个角色（在 brainstorming prompt 里注入）

### 结论

**不需要单独新建 skill，但需要明确分层使用现有工具：**

| 检查类型 | 当前工具 | 使用时机 |
|---------|---------|--------|
| 结构自检（占位符/歧义/scope） | `spec-quality-checklist.md` + brainstorming 第一层 | opsx:ff 后，eng-review 前 |
| 内容精炼（盲点/方案对比/对话） | brainstorming 第二层（`Spec self-review` 后的 `User reviews spec?`） | 结构自检通过后 |
| 工程审查（架构/测试/安全） | plan-eng-review 或 autoplan Eng Phase | /clear 后 |
| 代码事实验证（grep first） | opsx:ff D-1 约束 | spec 写入时，而非 review 时 |

---

## 七、最大漏洞：Accurate 标准没有 review 环节保障

当前工作流中，**"准确"是唯一没有 review 环节保障的标准**。

brainstorming 和 autoplan 都无法在 review 时验证 spec 中的代码事实（函数名/字段/路径）是否真实存在。

现有防线：
- opsx:ff 的 D-1 约束：写 design.md 时 grep 验证再写入
- plan-eng-review 的 "如有不确定的技术事实…使用 AskUserQuestion" 触发词

缺口：
- brainstorming 在讨论中产生的技术细节无强制验证
- autoplan 的 Claude 子 agent 和 Codex 都只读 plan 文件，不 grep 代码库

**补救方向：** opsx:ff 的 D-1 约束是主防线，必须在初始生成时执行，而不是指望 review 补救。

---

*文档版本：2026-06-28*
*基于 superpowers 6.0.3 brainstorming / gstack autoplan*
