# Proposal — plan-workflow-cost-optimization

## Why

每轮 spec 工作流评审重、慢、贵，逼出「合批摊薄」反模式；但一个刚跑完的 dogfood 证明评审层 load-bearing、不能砍。需要一个**比单次 change 更大的规划层**统摄「不砍安全地降成本」这个跨多变更、多方向的程序。

## What Changes

- 产出 `openspec/roadmaps/workflow-cost-optimization/` roadmap 文档包（requirements/design/roadmap/task-log/memo 五件），把成本优化编排为**三腿四阶段**：Leg1 降范围（无逻辑面白名单免多镜）· Leg2 降墙钟（机械镜快档/流水线/后台）· Leg3 降轮次（相关合批+大扫除批）。
- 贯穿原则：**成本优化边界 = 逻辑面有无**。
- **本变更只产文档**（规划），实施由未来独立变更按阶段驱动。P1 已由在途 change `adaptive-workflow-routing` 承载。

## Capabilities

### New Capabilities
（无——本变更交付物是 roadmap 文档包，非 spec 能力）

### Modified Capabilities
（无）

## Impact

- 新增 `openspec/roadmaps/workflow-cost-optimization/`（长期真相源）。
- （建议）CLAUDE.md 补 roadmap 索引一行。
- 不改任何代码/规则/skill（纯规划）。
