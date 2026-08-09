# 设计图表规则（Design Diagrams）

> **定位**：规定**设计 / spec 阶段该画哪些图、何时画、什么形态**。是
> [`spec-checklists/spec-quality-base.md`](./spec-checklists/spec-quality-base.md) 中
> **BASE-19 图表完备性**的展开与强制细则，并把外部工程实践中「review 期强制画图」的检查点
> 从 review 期前移到设计期。项目无关、可复用。

---

## 一、为什么在设计期画，而非 review 期补（预防 > 事后检查）

```
  plan-eng-review 在 review 强制画图   = detection（亡羊补牢）
  把图槽位焊进 design 模版,设计时就画  = prevention（更省、更早）
  → eng-review 退化为「验证图存在 / 正确 / 未过时」,而非现场补画
```

## 二、图表分类（按"表达什么"）

| 类别 | 图 | 表达什么 |
|------|----|---------|
| **结构**（有哪些部件、怎么连，借 C4 分层） | Context | 系统 ↔ 外部用户 / 外系统 |
| | Container | 应用 / 服务 / DB / 队列 等部署单元 |
| | Component | 单容器内模块 / 职责 |
| | 依赖图 / 部署图 | 模块依赖、部署拓扑 |
| **行为**（怎么动、什么顺序、什么状态） | 序列图 | 跨组件交互时序（谁调谁、什么顺序） |
| | 状态机图 | 有生命周期的对象状态 + 转换（含异常转换） |
| | 数据流图 | 数据如何流动 / 转换（管道） |
| | 流程 / 决策图 | 复杂分支逻辑（decision tree） |
| **验证** | 测试覆盖图 | code path → 测试类型 映射 |

## 三、触发条件表（画哪些——命中才画，不全画）

> 不blanket-mandate，避免过载。每种图由设计实际内容触发：

| 触发条件 | 必画的图 |
|---------|---------|
| 任何非平凡变更 | 至少一张**组件 / 依赖图**（默认） |
| 跨 3+ 组件协作 | **序列图** |
| 对象有多状态生命周期（IDLE/RUNNING/ERROR…） | **状态机图**（含异常转换） |
| 数据经多步转换 / 管道 | **数据流图** |
| 复杂分支 / 决策逻辑 | **流程 / 决策图** |
| 新系统 / 大改架构 | **C4 Context + Container** |
| 有测试计划 | **测试覆盖图** |
| 并发 / 共享可变状态（TG-26） | **序列图**（竞态交互时序） |

## 四、形态：ASCII 优先

ASCII 图可 diff、随 repo 版本化、AI 直接产出、无需工具链——首选。
C4 仅借其**分层思路**（Context / Container / Component），渲染成 ASCII 即可，
**不引入** PlantUML / Structurizr / mermaid 等工具（除非项目已有约定）。

## 五、何时画（阶段分工）

| 阶段 | 画什么 |
|------|--------|
| **design.md** | 结构图（默认）+ 命中触发的行为图（序列 / 状态机 / 数据流 / 决策） |
| **writing-plans / tasks** | **测试覆盖图**（此时测试策略才具体，比 design 期更自然） |
| **eng-review** | 不新画——**验证**上述图存在、正确、与设计一致、未过时 |

## 六、design.md 模版的「## 设计图」区

```
  design.md
  └── ## 设计图
      ├── 组件 / 依赖图              （非平凡变更必有 —— BASE-19 默认槽）
      ├── 〔跨组件〕序列图           （条件）
      ├── 〔有状态机〕状态图          （条件，嵌入式复用 EMB-08）
      ├── 〔数据管道〕数据流图        （条件）
      └── 〔新系统〕C4 Context+Container（条件）

  tasks / plan 阶段
  └── 测试覆盖图                     （条件：有测试计划）
```

## 七、维护（图是交付物）

- 图随变更更新——**过时的图比没有图更糟**，会主动误导。
- 改动碰到附近的 ASCII 图（含代码注释里的），必须复查并在**同一次提交**更新。
- 评审中发现过时图，即使在本次范围外也要标记。

## 八、检查清单

- [ ] 非平凡变更是否至少有一张组件 / 依赖图？
- [ ] 跨 3+ 组件 → 是否有序列图？
- [ ] 有多状态对象 → 是否有状态机图（含异常转换）？
- [ ] 数据多步转换 → 是否有数据流图？
- [ ] 复杂分支 → 是否有决策 / 流程图？
- [ ] 新系统 / 大改 → 是否有 C4 Context + Container？
- [ ] 图是否为 ASCII、在 repo 内、与设计一致、未过时？
- [ ] 测试覆盖图是否在 writing-plans 阶段产出？

## 关联

- **BASE-19** 图表完备性（本规则是其展开；base 留维度，本规则给细则）
- 领域 T 项：嵌入式 **EMB-08** 状态机图、后端 **BE-01** v_old/v_new 对照（表形态）
- 外部工程实践中 review 期强制画图（序列 / 状态 / 数据流 + 测试覆盖图）的检查点，本规则将其前移到设计期

## 参考来源

- [C4 model — Diagrams](https://c4model.com/diagrams)
- [C4 Model 完整指南 (Miro)](https://miro.com/diagramming/c4-model-for-software-architecture/)
- [C4 Diagrams for Software Engineering 2026 (Cloudairy)](https://cloudairy.com/blog/c4-diagrams-software-engineering)

*规则集 v1 · 项目无关 · 配套 spec-checklists/*
