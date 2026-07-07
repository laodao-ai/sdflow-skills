# workflow 机械层固化 任务日志

> 本文件按时间**倒序**记录 `roadmap.md` 中每个已完成子任务的状态、耗时、问题、调整。
>
> 相关文档（全部位于 `openspec/roadmaps/mechanical-layer-hardening/`）：
> - 需求综述：`requirements.md` · 整体设计：`design.md` · 实施路线图：`roadmap.md`

## 使用约定

每完成一个 roadmap.md 中的子任务（或子任务组），追加一条记录：

```markdown
## YYYY-MM-DD
### [阶段 X / 任务 X.Y.Z] <任务标题>
- **状态**: ✅ 完成 / ⚠️ 部分完成 / 🔄 已回滚 / ⏸ 暂停
- **实际耗时**: <N>h（估时 <M>h）
- **遇到的问题**: …
- **下一步**: …
- **备注**: …
```

**要记**：子任务状态变更、与设计预期不一致、需调整 roadmap/design/specs、跨阶段教训。
**不用记**：纯配置微调、机械执行、打字错误。
**粒度**：单次 1-3 条；日期倒序；大阶段完成补「阶段 N 完成总结」。

---

## Review 处置

> 阶段 3.5 交叉 review（`/autoplan` 或 plan-*-review）产出的每条 issue 在此登记，必须标注下列状态之一：
> - ✅ **采纳**：写明已在哪个文件哪一节改动
> - ❌ **拒绝**：写明拒绝理由（不得空白「不采纳」）
> - ⏭ **延后**：写明延后到哪个阶段 / 哪个后续变更
>
> **归档前人工复核项**：确认本小节**不存在「未处置」状态**的条目。

<!-- review issue 登记从这里开始 -->
**阶段 3.5 交叉 review：跑了独立冷镜（2026-07-07，用户选「跑独立冷镜冷审」）**

`/autoplan` 在本会话 Skill 面板未直接暴露 → 用 fresh-context 冷镜 agent（plan-eng-review 视角）把三件套作整体 plan 冷审。冷镜总判「可归档，须先订正 F1/F2 表述硬伤，不动两腿骨架」。7 条 finding 处置如下：

| # | 严重度 | 冷镜发现 | 处置 |
|---|---|---|---|
| F1 | 高 | anchor_lint 复用清单技术错配（度量锚变长 KV 走 `parse_anchor` 前缀匹配，非 `_line_scoped_hits` 定长整行）；且「P2 为 P5 补锚层机验」是假依赖（两套锚互不相干） | ✅ **采纳**：design §2 技术栈拆两行 + 决策 2 理由 + 候选表 P2；roadmap 2.A.1 + 阶段 5 前置注 + 附录 A 箭头 |
| F2 | 高 | dual-read 关闭条件未定义；归档 inline 锚不可变、`archived_verify_state` **永久**靠 `_line_scoped_hits` 读 →「删整套解析机器」高估，只能删 live 半场 | ✅ **采纳**：design 决策 6 加③非对称性 + §6.4 + §6.1 风险行；roadmap 目标行 + 5.B.1 + 5.C + 验收 + 附录 B |
| F3 | 中 | 8/11 helper 只在 buglist+todolist（issues.py 依 D4 不含表解析 helper）→ 3.A.1 拓扑写错 | ✅ **采纳**：design 决策 7 + 候选表 P3；roadmap 3.A.1 拆 3 向/2 向 |
| F4 | 中 | S1 ROI 门 go 阈值未定义，与「B4/B5 已两连发」有内部张力 | ✅ **采纳**：design §9 + roadmap 阶段 5 前置，锐化为显式阈值（B4/B5 已达线，GO 待 P2 完成或再出 1 例） |
| F5 | 低 | requirements 头部列 memo.md，违反「四件套不引用 memo」 | ✅ **采纳**：requirements 头部移除 memo 条目 |
| F6 | 低 | 「57 篇」精确数未核实（实测 review-report ~39） | ✅ **采纳**：软化为约数，并入 S1 起手核实前置（design §9 + roadmap 阶段 5 前置/5.B.1/验收） |
| F7 | 低 | P8 两子项（SOP 常量收割 / roadmap 处置对账）YAGNI 风险，但护栏（按痛点+留痕）到位 | ⏭ **延后**：阶段 4 起手时掂量收益<维护成本；护栏已在 roadmap 4.D/验收，无需现在改文档 |

- **未见问题维度**（冷镜背书）：scope 未越界、度量锚只补 lint 取舍站得住、反模式/D4 处理正确、并行 caveat 恰当、子任务粒度合理。
- **归档前复核**：本小节无「未处置」状态条目（F1-F6 采纳并已改文件、F7 显式延后）。

---

<!-- 日志条目从这里开始，最新的放最上面 -->

## 2026-07-07
### [阶段 2 / mlh-p2-anchor-lint spec-review] 「复用→重实现」调和（H3/BASE-08）
- spec-review 领域镜 BASE-08 抓出 design 决策与 roadmap「复用不重实现」正面矛盾。裁决：遵 F1 实质（变长 KV 前缀匹配、不用 _line_scoped_hits），但因跨 skill import 在消费仓 break，实现为脚本内重实现同款逻辑。已改 roadmap.md 2.A.1 + design.md §2 技术栈行。

## 2026-07-07

### [进度核对] 实施侧全阶段未开工确认（防误判固化）
- **状态**: ℹ️ 进度快照（非阶段交付，仅登记当前真相，防将来重复核对时误判）
- **当前进度**: 除阶段 0（规划，见下条）外，**Leg1 的 P1-P4、Leg2 的 P5-P6 全部未开工**——无任何 `implement-mechanical-layer-hardening-p*` change 存在。
- **plan change 状态**: 承载本 roadmap 的 `plan-mechanical-layer-hardening` **仍活跃、未归档**（分支 `feat/plan-mechanical-layer-hardening`）；阶段 3.5 交叉 review + 归档尚未走。
- **易混点固化（勿误记为阶段交付）**: `issues-pool-hardening`（2026-07-07 已归档）**不是** P3 或 P6 的交付——roadmap P6 前置已把它定位成「通往 S2 的**低成本前置桥**（reject 把腐蚀类堵死）」；它早于本 roadmap 撰写，P3/P6 的 scope 已是「扣掉 issues-pool-hardening 之后剩下的」。故 recorder 一致性测试（P3.A）、config/batch lint（P3.B）、家族②迁移（P6）**均仍待做**。
- **下一步**: 走阶段 3.5（`/autoplan` 交叉 review → 处置登记）→ 归档 plan change → `/opsx:new implement-mechanical-layer-hardening-p1-issues-sweep` 进阶段 1。

### [阶段 0 / 规划] workflow 机械层固化 roadmap 文档包产出完成

- **状态**: ✅ 完成
- **实际耗时**: ~1.5h（含 3 镜并行 survey + 两次 scope 拍板）
- **产出**:
  - `openspec/roadmaps/mechanical-layer-hardening/requirements.md` — 需求综述（两腿 × adr/0006 根契约）
  - `openspec/roadmaps/mechanical-layer-hardening/design.md` — 整体设计（7 决策 + 候选全表 + Q&A 已决议）
  - `openspec/roadmaps/mechanical-layer-hardening/roadmap.md` — 实施路线图（6 阶段 × Leg1 脚本化优先 / Leg2 就绪度分级）
  - `openspec/roadmaps/mechanical-layer-hardening/task-log.md` — 任务日志（本文件）
  - `openspec/roadmaps/mechanical-layer-hardening/memo.md` — 讨论备忘（survey 综合 + 两次拍板考古）
  - `openspec/changes/plan-mechanical-layer-hardening/` — SDD 变更盒子（承载本次规划，待归档）
- **关键决策回顾**（完整档案见 `design.md` §3 和 §8）:
  - Q1：新建 roadmap + 就绪度分级（S1 就绪 / S2 north-star）。
  - Q2：拓宽成双腿（脚本化 + 去字符串化），改名「机械层固化」，Leg1 脚本化优先。
  - 两腿同归 adr/0006 硬约束；家族①② 迁 frontmatter、家族③④ 留 inline、度量锚只补 lint。
- **计划外发现（survey 实测）**:
  - ⚠️ **ship_gate.py 只在 `sdflow-ship/scripts/`，不在 T65 假设的 bundle 路径** `assets/workflow/tools/` → S1「bundle 爆炸半径」风险可能被高估。已登记为阶段 5 前置核实项。
  - 不存在一处把家族①②③④ 全枚举的块——① ③ ④ 在 T65 备注，② 在 ADR 0010。四家族是拼合的。
- **下一步**:
  - 阶段 3.5：跑 `/autoplan`（把三件套作整体 plan）交叉 review → 处置登记本文件「Review 处置」区。
  - 归档 `plan-mechanical-layer-hardening`。
  - 未来：`/opsx:new implement-mechanical-layer-hardening-p1-issues-sweep` 进阶段 1。
- **备注**:
  - S1 前置一道 ROI 评估门（inline 锚这套是否反复出同类 bug，现数据点 B4/B5）；S2 north-star 不排期，ROI 触发才起。
