# Hand-off：重构 sdflow-roadmap skill

## 状态

- **阶段**：sdflow-spec 相位 A 进行中，共识已基本形成，尚未进入相位 B
- **分支**：main（未建 change 分支）
- **无在途 change**

## 目标

重构 `sdflow-roadmap/SKILL.md`，将外部 skill 依赖的能力内化到 roadmap 自身，整体结构对齐 sdflow-spec 的三相位模式。

## 已确认的共识

### 1. 要消除的外部依赖（4 个 skill + 1 个基础设施）

| 外部依赖 | 当前用途 | 内化方式 |
|---------|---------|---------|
| **wayfinder** | 长档讨论持久化（map + 结构化票） | 用 memo.md 增量落盘替代；去掉整个分支 B |
| **grilling** | wayfinder 票内的方案拷问 | 内化为 Phase B 拷问（与 sdflow-spec 同构） |
| **domain-modeling** | wayfinder 票内的术语/ADR 建模 | 内化为 Phase B 术语澄清环节 |
| **office-hours** | 需求真实性前置验证（六问） | 按场景裁剪后融入 Phase B 拷问维度 |
| **matt tracker doc** | wayfinder 的 preflight 检查 | 随 wayfinder 一并删除 |

### 2. 保留不动的部分

- **review 层**：`/plan-eng-review`（默认）和 `/autoplan`（野心信号），有降级路径——**待确认是否也要内化或简化**（上一 session 未拍板）
- **结晶流程**：三件套（design/roadmap/task-log）直写到 `openspec/roadmaps/{name}/`
- **收尾 checklist**：保留 ①②③⑤，删 ④（wayfinder 闭环），⑤ 简化（不再依赖 wayfinder 基线记录）
- **产出模式**：create/continue/replan 生命周期、规则 1-5、命名规范、下游阶段实施

### 3. 重构后的三相位结构

```
Phase A  澄清
  吃透规模、识别目标、判定是否需要 roadmap
  gate-0 五项通过 → 跳过 B 直接结晶

Phase B  拷问（核心变更）
  7 维拷问（按信号裁剪，不是都跑）：
  ① 需求真实性（office-hours Q1 适配）
  ② 现状分析（office-hours Q2 适配）
  ③ 阶段划分压力测试（roadmap 原生）
  ④ 最小可行首阶段（office-hours Q4 适配）
  ⑤ 架构路线对比（office-hours Phase 4 适配）
  ⑥ 术语/概念澄清（原 domain-modeling）
  ⑦ 前提质疑（office-hours Phase 3 适配）
  
  按信号裁剪：
  ├─ 技术重构 → ②③④⑤⑦ 为主
  ├─ 新产品/新项目 → ①②④⑤⑥⑦ 全跑
  └─ 野心信号命中 → ① 加重（startup 味逼问）
  
  每条承重结论站稳即写 memo.md（增量落盘，同 sdflow-spec）

Phase C  结晶
  从 memo 一次性生成三件套
  design/roadmap/task-log
```

### 4. 讨论层简化

```
当前：三分支路由
├─ 分支 A：/opsx:explore
├─ 分支 B：wayfinder chart（长档）  ← 删
└─ 分支 C：/office-hours（野心验证） ← 内化

目标：二路径
├─ gate-0 通过 → 直接结晶
└─ gate-0 未通过 → Phase B 拷问 → 结晶
```

### 5. office-hours 的吸收细节

office-hours 的核心价值是拷问方法论（非独立 skill），可吸收的部件：
- **Phase 2A 六个逼问**：Q1-Q6，按 roadmap 场景裁剪（不全跑）
- **Phase 3 Premise Challenge**：前提质疑，直接作为拷问维度 ⑦
- **Phase 4 Alternatives Generation**：方案对比，作为拷问维度 ⑤
- **不吸收**：Phase 3.5 Cross-Model Second Opinion（review 层已有）、Builder Mode（roadmap 不需要）、Visual Design Exploration

## 待确认事项（下一 session 需拍板）

1. **review 层处理方式**：保留 `/plan-eng-review` + `/autoplan` 外部依赖（有降级）？还是也内化/简化？
2. **change 名**：建议 `refactor-roadmap-internalize-deps`

## 关键文件

- `sdflow-roadmap/SKILL.md`（635 行，主要改动目标）
- `sdflow-roadmap/references/`（模板文件，可能需要新增 memo 模板）
- `docs/external-dependencies.md`（本 session 已创建，需随重构更新）
- `CLAUDE.md`（引用了 sdflow-roadmap 的 wayfinder 相关内容，需同步更新）

## 参考资料（已读）

- `/Users/cheneyzhao/.claude/skills/office-hours/SKILL.md`（1698 行，六问方法论在 Phase 2A）
- `sdflow-spec/SKILL.md`（三相位结构的参照）
- 本 session 的 explore 讨论（依赖图分析、吸收策略、三相位映射）
