# PRD 与 Spec 的关系

> 辨析两个文档的职责边界，说明在 OpenSpec 工作流中各自扮演的角色。

---

## 一、核心区别

| 维度 | PRD（产品需求文档） | Spec（技术规格文档） |
|------|-----------------|-----------------|
| **核心问题** | 做什么？为什么做？ | 怎么做？ |
| **视角** | 用户 / 业务 | 工程 |
| **作者** | PM（或 PM + Eng 协作） | Engineering |
| **产物** | 用户故事、成功指标、功能范围 | API 合约、数据模型、测试策略 |
| **典型读者** | 所有利益相关方 | 实现工程师 |
| **写作时机** | 编码前，确立方向 | PRD 对齐后，确立方案 |

**一句话原则：PRD 回答"值不值得做"，Spec 回答"怎么做"。**

---

## 二、在 OpenSpec 工作流中，PRD 角色谁在承担？

OpenSpec 的产出物本身已经包含了 mini-PRD 的等价功能：

```
opsx:ff 产出物
  ├── proposal.md   ← Why + What Changes + Impact = mini-PRD 骨架
  ├── design.md     ← 技术方案（How）
  ├── specs/*.md    ← 功能级技术 spec（How Detail）
  └── tasks.md      ← 实现任务清单

plan-ceo-review Phase 1（autoplan）
  └── 前提假设挑战、竞品对比、Dream State 映射 ← PRD 业务审查等价物
```

**结论**：`proposal.md` + `plan-ceo-review` 合起来是轻量 PRD 的功能等价物。不需要额外的独立 PRD 文件，但 proposal.md 必须写清楚"成功指标"。

---

## 三、什么情况下需要独立写 PRD？

| 情形 | PRD 必要性 | 理由 |
|------|-----------|------|
| 新产品 / 新功能线，需多方对齐 | **必须** | 没有共同的"为什么"，spec 写完方向可能就错了 |
| 技术基础设施（无用户感知） | 不需要 | 没有用户视角，proposal.md 就够 |
| 明确的用户需求反馈驱动 | 建议有 | 帮助量化成功指标，防止"做完没人用" |
| 单人项目 / 工程师即 PM | 可跳过 | proposal.md 写清目标和成功指标即可 |
| 多团队协作 / 跨系统影响 | **必须** | 利益相关方 sign-off 依赖 PRD |

---

## 四、对本项目（IoT 工具）的具体建议

仓库已有产品级 PRD（`docs/drafts/IoT_Device_Console_PRD_v1.md`、`BLE_Device_Configurator_*.md`）。

**功能级变更的正确流程：**

```
已有产品级 PRD
      ↓
新功能 idea
      ↓
opsx:ff（生成 proposal.md）
  ──── proposal.md 中的 Why 节引用 PRD 对应目标 ────
  ──── 必填：成功指标（阻塞级字段） ────
      ↓
plan-ceo-review 验证业务方向是否符合产品目标
      ↓
brainstorming 技术细化
      ↓
specs/*.md
```

---

## 五、proposal.md 中的"成功指标"字段（新增阻塞级要求）

`proposal.md` 的最大历史缺口是**没有成功指标**——导致 `plan-ceo-review` 的 Dream State 校验没有量化基准，实现完成后也无法判断"是否成功"。

**新增字段（在 Why 节后）：**

```markdown
## Success Metrics / 成功指标

<!-- 列出 1-3 个可量化的验收标准，说明"做完"是什么样子。 -->
<!-- 格式：指标描述 — 基准值 → 目标值 — 如何度量 -->

- 用户完成配网流程时间：当前 N/A → 目标 < 30 秒 — 用 E2E 测试计时
- 配置错误率：当前 ~15% → 目标 < 5% — 从错误日志统计
- 如果不能量化：至少写明"如何判断这个功能是成功的"
```

**"成功指标"设为阻塞级的理由：**

- 没有成功指标 = 做完也不知道对不对
- plan-ceo-review 的 Dream State 需要成功指标作为校准基准
- 强制在 proposal 阶段思考，而不是实现后再补，此时纠偏成本最低

---

## 六、最大风险：Spec 前没有 PRD 验证

**场景**：工程师拿到一个需求，直接 `opsx:ff` 生成 spec，然后按 spec 实现，最后发现用户根本不需要这个功能。

**根本原因**：proposal.md 的 "Why" 节通常是描述性的，没有可证伪的成功指标。

**防线建设：**

| 阶段 | 防线 | 强度 |
|------|------|------|
| opsx:ff | proposal.md 必须填成功指标 | 阻塞级（新增） |
| plan-ceo-review | Dream State 映射 + 前提假设挑战 | 已有，依赖成功指标 |
| 实现完成后 | 按成功指标 verify | 依赖前两项 |

---

*文档版本：2026-06-28*
*关联文档：`spec-checklists/`（spec 质量规则集）、`Spec_Quality_Collaboration.md`*
