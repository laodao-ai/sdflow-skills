---
name: sdflow-ship
description: 阶段三编排器——对已过设计门的 OpenSpec change 一次调用驱动 5.5→9（embedded-test-sop 条件 → writing-plans/subagent-dev → sdflow-code-review → sdflow-done→merge）。触发：「/sdflow-ship」「ship 这个 change」「阶段三跑到 merge」「过完设计门了，跑起来」。不含裸"ship"泛化触发。
---

# sdflow-ship — 阶段三编排器（盘面即状态）

一次调用把已过设计门的 change 从 5.5 驱动到 merge 建议。**meta-orchestrator：chain 现有 skill、不取代**；窄 scope 不越两个人类点（不跨 grill、不跨设计门——过门后才起跑，adr/0004 红线）。

## 铁律

- **每步前后 MUST 调 ship_gate 并遵其判定，禁止以 prose 记忆步序**〔adr/0006(b)〕：
  ```bash
  python3 ~/.claude/skills/sdflow-ship/scripts/ship_gate.py --change {change} --root "$(git rev-parse --show-toplevel)"
  ```
  路径缺失时按 sibling 约定兜底：`python3 ~/.codex/skills/sdflow-ship/scripts/ship_gate.py --change {change} --root "$(git rev-parse --show-toplevel)"`，
  再兜底仓内路径 `sdflow-ship/scripts/ship_gate.py`（相对仓根，即 `python3 sdflow-ship/scripts/ship_gate.py --change {change} --root "$(git rev-parse --show-toplevel)"`），三处均找不到才停下问用户。
  <!-- [impl-review-fix] 裁决项10：兜底句原用省略号"…"，改写全三处显式路径，防止照抄时脑补错命令 -->
  步前问"NEXT 是谁 + 前置缺什么"，步后问"产物落了吗 + 门禁结论"。首行人读摘要照抄进对话，JSON 供判定。
- **ship 零 git 写操作〔D8〕**：全程不 commit/merge/push（各子 skill 的 checkpoint 归其自身；ship 无产物故无自身 checkpoint）；**不自动 push**。
- **merge 意图透传**：调用语含 merge opt-out 意图时，ship 归一化为 sdflow-done 词表短语（如「不要 merge」「skip merge」）转述给 done——勿原样转述词表外措辞（git 单向操作只在 done 一处）。
  <!-- [impl-review-fix] 裁决项10：原"原样转述"允许词表外自由措辞传给 done，改为归一化到 done 认识的固定词表短语 -->
- **决策协议（T10 三级，替换"有把握自动选"）**：阶段三遇 ≥2 方案——①有客观判据（测试/断言/基准可判）→ 自动选并记理由；②无客观判据 → 派对抗镜复核推荐项，通过才自动选（复核记录写进该步报告）；③复核不过/无从复核 → defer 进 buglist/todolist + hand-off。**MUST NOT 以自评置信（"有把握"）作为自动选定的唯一依据。** 复核记录格式：写入该步 code-review-report.md 的「修复 / defer 台账」区，行格式 = 「T10复核: <方案> | 对抗镜结论 <通过/证伪> | <一句理由>」。
- 模型档位与缺省见规则根 `model-tiers.md`（经 ~/.sdflow/hack/resolve-workflow.sh 解析；config.yaml 的 model-tiers 段可覆盖映射）。

## 链序（gate 驱动，非记忆）

REFUSE_START(exit3)→停并转述 reason 两变体："未过设计门（若拍板已发生请人工补锚——显式越权留痕）"｜"change 不存在（active 与 archive 均无）——核对 change 名拼写"〔B3〕 ·
RUN_SOP→跑 embedded-test-sop（TG-18/高风险细判归模型） · RUN_PLAN→superpowers:writing-plans（**派发 args MUST 要求 plan 每任务 commit 步显式用 `checkpoint-commit.sh <change>:task<N>-<slug>`（命名空间格式，`<change>`=本 change slug），由 implementer 执行**——gate 主锚契约；gate 只认当前 change 标签、跨 change stacking 不污染〔T32〕，裸 `task<N>-` 向后兼容）→ subagent-driven-development 自动执行 · CONTINUE_IMPL→把 JSON `done_tasks` 已完成任务号集传给 SDD dispatch **勿重派** · RUN_CODE_REVIEW→/sdflow-code-review · BLOCKED_UPSTREAM(exit4)→停并原样上抛 blocker 清单 · RUN_VERIFY→/sdflow-done（透传 merge 意图） · VERIFY_FAIL(exit5)→停并原样上抛缺口清单 · RERUN_STALE→重跑 gate 指定步（目标步 = JSON `next` 字段值，动态非固定名——照 next 跑，勿凭摘要猜） · STEP_IN_PROGRESS→重跑该步（目标步 = JSON `next` 字段值，动态非固定名——照 next 跑，勿凭摘要猜）；**同一 invocation 内同一步重跑一次仍无锚行 → 按 UNKNOWN 停上抛人工，禁无限静默循环**〔熔断〕（例外边界声明：重试计数是单 invocation 内的短时计数、非跨步状态记忆——与"禁 prose 记忆步序"红线不冲突〔adr/0006(b) 的步序判定已全部在 gate〕；计数脚本化为长期项见 todolist） · UNKNOWN(exit6)→停并转述 reason · SHIPPED→输出摘要。

## resume / 暂停 / 人机同权〔D9〕

- **停即停、重调即续**：ship 零跨步内存状态，任何时刻中断后重调 `/sdflow-ship {change}`，gate 从盘面推导缺口继续。
- **gate 不辨产者**：期间人工手跑某步（如手跑 /sdflow-code-review）产出的报告同样被认；手改锚行 = 显式越权通道（git 留痕可审计）。
- 实现中断的 resume：gate 输出已完成任务号集 → 传 SDD 勿重派。

## SHIPPED 摘要模板

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/sdflow-ship 完成 — {change}
  链: [sop|SKIP] → plan+impl({n}/{n} 任务) → code-review(pass) → done(verify PASS, merged)
  ⏸ 未 push（手动控制）。toolkit 源仓：push 后新会话跑 /sdflow-upgrade 激活。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
