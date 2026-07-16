<!-- sdflow:step1-broad-review v1 mode="degraded" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="none" reason_code="env-eperm-aborted" findings="0" truncated="false" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="不命中 TG-04/06/07/08/09/16/17/26；纯 markdown 规则措辞改动，无并发/数据/接口/安全边界" -->

# spec-review-report · scoped-test-per-task

## 执行降级声明（诚实留痕，非评审结论）

本轮 fan-out 冷镜层**因环境不可用**，已降级：
- **4 个冷镜子代理全部失败**：对抗镜×2 + 接地镜×1 报 `EPERM`（macOS TCC 对 `~/Documents` 的隔离——子代理进程无仓库文件访问权限，`dangerouslyDisableSandbox` 亦无效）；广审镜遇 API 连接错误。
- **autoplan 广审未原生跑**（`mode="degraded"`）；**codex outside-voice 未跑成**（`reason_code="env-eperm-aborted"`）。
- **替代**：主 session（有文件访问 + 全上下文）亲验预设的最尖锐攻击点。**独立性受损**（违 G1 fresh-子代理独立性）——此为环境所迫的显式降级，留痕供设计门复核「主 session 自审是否够冷」。

> 尽管冷镜层崩了，主 session 亲验仍独家挖出一个 **动摇 change 根基的 HIGH finding**——恰是 [[cold-code-review-load-bearing]] 的又一例证：核验 superpowers 原生 prompt 模板，暴露了 change 前提错误。

## 决策登记区

```
┌──────────────────────────────────────────────────────────────────────┐
│ [已拍板] Q1  选择 A：设计被否决，不进入实现                         │
└──────────────────────────────────────────────────────────────────────┘
```

**设计门结论（2026-07-16）**：用户同意以“设计被否决”归档。本 change 不进入实现，
5 个实现任务保持未完成；delta spec 不同步到主 `spec-workflow`，归档仅保留调查、设计与否决证据。

## HIGH-1〔主 session 亲验·置信高·严重度高〕：前提证伪 + 措辞传导链断裂

**核验证据（真实代码）：**
- `superpowers/…/subagent-driven-development/implementer-prompt.md:47-48`：implementer「iterating 时跑 focused test，**run the full suite once before committing**（commit 前跑一次全量套件）」。
- `…/task-reviewer-prompt.md:66-73`：reviewer 不重跑套件、按疑点跑 focused test、**禁 package-wide suite/race**；final whole-branch review 另跑一次。
- 综合：superpowers 原生 SDD 的真实测试节奏 = **每任务 implementer commit 前跑一次 full suite** + reviewer 不重跑 + final whole-branch review 再跑。

**推翻本 change 的两块前提：**
1. **「SDD 原生是每任务只跑 scoped、全量仅终审一次」= 错。** 原生 implementer **commit 前就跑 full suite**。本 change 想要的「每任务 scoped、全量仅终审」其实是**偏离/更激进于** superpowers 原生，而非「纠回原生」。proposal/design 通篇把它论证成「向 SDD 原生对齐」——前提不成立。
2. **workflow.md「每任务跑测试套件」不是偏差，而是与原生 implementer-prompt 一致。** 本 change 要「纠正」的东西，恰恰符合原生。

**传导链断裂（致命）：**
- 真正控制 implementer 测试行为的是 **superpowers SDD 的 `implementer-prompt.md` 模板**（commit 前 full suite）。
- 本 change 只改 `workflow.md` 步骤6/7 + `sdflow-ship/SKILL.md` RUN_PLAN 措辞。sdflow-ship 派「subagent-driven-development 自动执行」→ SDD 用**它自己的** implementer-prompt.md 派 implementer。
- **sdflow-ship 的措辞注入 ≠ implementer-prompt.md**。除非本 change 显式覆盖 implementer-prompt line 47，否则 implementer 照原生模板 commit 前跑 full suite → **措辞改了但行为不变，change 无效**。
- 本 change 的 design/tasks **完全没触及 implementer-prompt 层**——设计缺口。

**结论**：当前设计下本 change ①前提错误 ②传导链断裂 ③即便实现措辞改动也无实际效果。

## 建议去向（设计门拍板 Q1）

| 选项 | 内容 | 主 session 推荐度 |
|---|---|---|
| **A · 否决 change** | 承认「commit 前 full suite」是 superpowers 有意的 TDD 纪律（每 commit 全绿、防跨任务回归积累），非偏差；测试占比实证健康、执行时间非真痛点 | **推荐** |
| B · 重界定 scope | 若真要 scoped，改动面须扩到 SDD dispatch 覆盖 implementer-prompt 的测试节奏 → 偏离原生 TDD 纪律、跨任务回归推迟发现，收益（省时间）多半不值 | 不推荐 |

**收敛口：建议本 change 不进 HARD-GATE，退回重议（推荐选项 A 否决）。** 理由:前提被亲验证伪、传导链断裂、且原「测试占比=栈×TDD本性」的结论已足够——省全量回归执行时间不是真问题，反而会拆掉 superpowers「每 commit 全绿」的纪律。

## 已裁掉 / 未触及（环境降级下未能覆盖）

- 子代理预设的其余攻击点（scoped 边界模糊、下发漂移、scenario 可测性、终审延迟发现回归代价）**因 EPERM 未能由冷镜独立验证**——若设计门选择重议而非否决，须在可访问环境重跑冷镜补齐。
