# task-log.md 模板（任务日志 — DID）

用途：按时间倒序记录 `roadmap.md` 中每个已完成子任务的实际状态、耗时、问题、调整。是 roadmap 产出后唯一一份"活着的"文件（其他三件相对稳定）。

使用方法：把本模板内容 Write 到 `openspec/roadmaps/<name>/task-log.md` 作为初始文件。第一条日志记录 roadmap 文档包产出本身（作为阶段 0 / 规划的完成标记）。

**关键原则**：
- **倒序**（最新在最上面，符合"最近工作最易看到"的阅读习惯）
- 不记录琐碎动作（配置微调、参数调整、打字错误）
- 遇到计划外情况必须记（决策调整、规范扩展、风险暴露）
- 大阶段完成时追加"阶段 N 完成总结"作为里程碑

---

# <项目名> 任务日志

> 本文件按时间**倒序**记录 `roadmap.md` 中每个已完成子任务的状态、耗时、问题、调整。
>
> 相关文档（全部位于 `openspec/roadmaps/<name>/` 下）：
> - 需求综述：`requirements.md`
> - 整体设计：`design.md`
> - 实施路线图：`roadmap.md`

## 使用约定

每完成一个 roadmap.md 中的子任务（或子任务组），追加一条记录：

```markdown
## YYYY-MM-DD

### [阶段 X / 任务 X.Y.Z] <任务标题>
- **状态**: ✅ 完成 / ⚠️ 部分完成 / 🔄 已回滚 / ⏸ 暂停
- **实际耗时**: <N>h（估时 <M>h）
- **遇到的问题**:
  - …
- **下一步**:
  - …
- **备注**:
  - …
```

**什么时候要记**：
- 子任务状态变更（开始、完成、回滚、暂停）
- 遇到与设计预期不一致的情况
- 发现需要调整 `roadmap.md`、`design.md` 或 OpenSpec specs
- 跨阶段的经验教训

**什么时候不用记**：
- 纯配置微调（如改某个字号、超时参数）
- 不涉及决策的机械执行
- 明显的打字错误修复

**记录粒度建议**：
- 单次 1-3 条为宜，不追求每条子任务都记
- 日期倒序排列（最新的在最上面），每天最多一个 `## YYYY-MM-DD` 标题
- 大阶段完成时补一条"阶段 N 完成总结"作为里程碑节点

---

<!-- 日志条目从这里开始，最新的放最上面 -->

## YYYY-MM-DD

### [阶段 0 / 规划] <项目名> roadmap 文档包产出完成

- **状态**: ✅ 完成
- **实际耗时**: ~<N>h（含讨论）
- **产出**:
  - `openspec/roadmaps/<name>/requirements.md` — 需求综述
  - `openspec/roadmaps/<name>/design.md` — 整体设计（含架构决策 + Q&A 已决议）
  - `openspec/roadmaps/<name>/roadmap.md` — 实施路线图（<N> 阶段 × <M> 子任务）
  - `openspec/roadmaps/<name>/task-log.md` — 任务日志（本文件）
  - `openspec/roadmaps/<name>/memo.md` — 讨论备忘（可选，不被四件套引用）
  - `openspec/changes/archive/<date>-<change-name>/` — SDD 变更盒子（已归档）
- **关键决策回顾**（完整档案见 `design.md` §3 和 §10）:
  - <决策 1 一句话>
  - <决策 2 一句话>
  - <决策 N 一句话>
- **下一步**:
  - `/opsx:new implement-<roadmap-name>-phase-1` 开新变更进入阶段 1 实施
- **备注**:
  - <任何特殊情况、取舍、承诺>
