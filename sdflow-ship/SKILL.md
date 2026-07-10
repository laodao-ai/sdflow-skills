---
name: sdflow-ship
description: 阶段三编排器——对已过设计门的 OpenSpec change 一次调用驱动 5.5→9（embedded-test-sop 条件 → 实现管线 → sdflow-code-review → sdflow-done→merge）。触发：「/sdflow-ship」「ship 这个 change」「阶段三跑到 merge」「过完设计门了，跑起来」。不含裸"ship"泛化触发。
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
- **决策协议（T10 三级，替换"有把握自动选"）**：阶段三遇 ≥2 方案——①有客观判据（测试/断言/基准可判）→ 自动选并按三镜 + 主次记理由；②无客观判据 → 派对抗镜复核推荐项，通过才自动选（复核记录写进该步报告）；③复核不过/无从复核 → defer 进 buglist/todolist + hand-off。**MUST NOT 以自评置信（"有把握"）作为自动选定的唯一依据。** 复核记录格式：写入该步 code-review-report.md 的「修复 / defer 台账」区，行格式 = 「T10复核: <方案> | 对抗镜结论 <通过/证伪> | <理由(三镜+主次)>」。
- 模型档位与缺省见规则根 `model-tiers.md`（经 ~/.sdflow/hack/resolve-workflow.sh 解析；config.yaml 的 model-tiers 段可覆盖映射）。

## 链序（gate 驱动，非记忆）

REFUSE_START(exit3)→停并转述 reason 两变体："未过设计门（若拍板已发生请人工补锚——显式越权留痕）"｜"change 不存在（active 与 archive 均无）——核对 change 名拼写"〔B3〕 ·
RUN_SOP→跑 embedded-test-sop（TG-18/高风险细判归模型） · RUN_PLAN→先跑 `python3 sdflow-implement/scripts/impl_route.py route --root "$(git rev-parse --show-toplevel)" --change {change}` 取 PIPELINE_RECEIPT（回显进对话）；`pipeline=tickets` → 按模式派发契约字面串派发 `sdflow-implement mode=tickets-plan change={change}`（ship 主 session inline 执行，MUST NOT 作为子代理派发）；`pipeline=superpowers` → superpowers:writing-plans（**派发 args MUST 要求 plan 每任务 commit 步按 workflow.md §二/步骤6 的格式规则（权威见 `ship_gate.py` `TAG_RE`〔T36〕）显式写 checkpoint-commit 命令，由 implementer 执行**——gate 主锚契约；gate 只认当前 change 标签、跨 change stacking 不污染〔T32〕）→ subagent-driven-development 自动执行；helper 非 0 退出（RouteStop，UNKNOWN 语义）→ 按 UNKNOWN 停上抛，不静默回退 · CONTINUE_IMPL→一律按 plan frontmatter marker 路由——本步 MUST 重新调用取 marker：`python3 sdflow-implement/scripts/impl_route.py route --root "$(git rev-parse --show-toplevel)" --change {change}`（与 RUN_PLAN 同款字面命令，同一 route CLI 调用取值，首跳 config 值不再参与；**零跨步内存状态**：本步 MUST 重新调用取 marker，禁止复用早前会话结果或人眼读 frontmatter）〔impl-review-fix〕；`marker=tickets` → 按模式派发契约字面串派发 `sdflow-implement mode=tickets-exec change={change} done_tasks={逗号分隔任务号|none}`（值取自 gate JSON `done_tasks`，原样透传不重算不猜测）；marker 缺席 → 把 JSON `done_tasks` 已完成任务号集传给 SDD dispatch **勿重派**（subagent-driven-development）；helper exit 6（marker 在但非法/重复/损坏，RouteStop）→ 按 UNKNOWN 停上抛，MUST NOT 静默回退旧管线（此判据对 RUN_PLAN 与 CONTINUE_IMPL 两处路由调用均适用）〔impl-review-fix〕；**试验期权威声明：「此二态 skill 路由以本链序为权威；gate JSON `next` 在此二态仍输出 writing-plans/subagent-dev，仅信息性（emit 串 Phase B 根治）。『照 next 跑』指令仅约束 RERUN_STALE/STEP_IN_PROGRESS。」**〔impl-review-fix〕 · RUN_CODE_REVIEW→/sdflow-code-review · BLOCKED_UPSTREAM(exit4)→停并原样上抛 blocker 清单 · RUN_VERIFY→/sdflow-done（透传 merge 意图） · VERIFY_FAIL(exit5)→停并原样上抛缺口清单 · RERUN_STALE→重跑 gate 指定步（目标步 = JSON `next` 字段值，动态非固定名——照 next 跑，勿凭摘要猜） · STEP_IN_PROGRESS→重跑该步（目标步 = JSON `next` 字段值，动态非固定名——照 next 跑，勿凭摘要猜）；**熔断判据（按 verdict 分治）**〔T26/SR-1；impl-review-fix CR-1〕：① **`STEP_IN_PROGRESS`**（报告在但无结论锚）→ 用锚行集合判据：同一 invocation 内重跑前后，以 `ship_gate.py` 无状态 helper `anchor_set(text)`/`breaker_no_progress(before, after)` 比较该步报告的 **ship-gate frontmatter 状态集合**〔mlh-p5 Task6 D11：判据迁 frontmatter 状态集，inline 锚已随 live 读点退役、不再参与进展判据〕（快照由编排器单 invocation 内持有作参数传入，helper 不落地、不跨 invocation），状态集无净变化即判无进展。② **`RERUN_STALE`**（报告有锚但陈旧）→ 进展信号是**新鲜度已刷新**（重跑后 gate 不再返回 `RERUN_STALE`），故其熔断以「重跑后 gate **仍**返回同一 `RERUN_STALE`」为准，**MUST NOT 用锚集不变误判**（stale 重跑常锚不变如 pass→pass，用锚集会假熔断误杀正常刷新）。任一判无进展 → 按 UNKNOWN 停上抛人工，禁无限静默循环；**HEAD 移动、文件修改时间戳变化 MUST NOT 作免疫信号**（修复类步几乎必产 commit，若把 HEAD 移动当"有进展"熔断永不触发）；**fail-safe：快照缺失（如 context 压缩丢失上一次记录）保守判无进展**，MUST NOT 默认放行再跑〔熔断〕（例外边界声明：重试判定是单 invocation 内的短时持有、非跨步状态记忆——与"禁 prose 记忆步序"红线不冲突〔adr/0006(b) 的步序判定已全部在 gate〕；持久化下沉为长期 defer 项见 todolist，撞三红线不做） · UNKNOWN(exit6)→停并转述 reason · SHIPPED→输出摘要。

## resume / 暂停 / 人机同权〔D9〕

- **停即停、重调即续**：ship 零跨步内存状态，任何时刻中断后重调 `/sdflow-ship {change}`，gate 从盘面推导缺口继续。
- **gate 不辨产者**：期间人工手跑某步（如手跑 /sdflow-code-review）产出的报告同样被认；手改锚行 = 显式越权通道（git 留痕可审计）。
- 实现中断的 resume：gate 输出已完成任务号集 → 传 SDD 勿重派。
- **工作树 dirty 软提示（非门禁）**〔T33/T35 定夺〕：gate 新鲜度判定 committed-only，不看工作树 staged/unstaged/untracked 的非 openspec 改动〔见 `ship_gate.py` 注释〕。收尾（SHIPPED）或 resume 续跑前，MAY 检查一次工作树（`git status --porcelain`，排除 `openspec/` 路径）——若存在未提交的非-openspec 改动，在摘要末尾附加一行提示"工作树有未提交改动，gate 判定不含它们"；此提示**仅信息性**，MUST NOT 改变 gate 的退出码或推进/拒绝结论。

## SHIPPED 摘要模板

`pipeline` 字段来源〔impl-review-fix〕：若本次调用内未曾回显 PIPELINE_RECEIPT（如 resume 直接
落在 `RUN_CODE_REVIEW`/`RUN_VERIFY` 等后段），生成摘要前先补跑一次上述 route 命令取 pipeline
值，**MUST NOT** 猜测或留占位。

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/sdflow-ship 完成 — {change}
  链: [sop|SKIP] → plan+impl({n}/{n} 任务, pipeline={superpowers|tickets}) → code-review(pass) → done(verify PASS, merged)
  ⏸ 未 push（手动控制）。toolkit 源仓：push 后新会话跑 /sdflow-upgrade 激活。
  [若工作树有未提交的非-openspec 改动] 提示：工作树有未提交改动，gate 判定不含它们（非门禁，仅信息性）。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
