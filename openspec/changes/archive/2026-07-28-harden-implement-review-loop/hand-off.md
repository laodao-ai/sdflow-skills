# hand-off — harden-implement-review-loop

> 异步人类再入口 + 下个 change 种子。完成判定以 `verify-report.md`（PASS）为权威；本文的「完成了什么」**逐条复核过锚点存在性**，未直接搬运 verify 的 ✅。

## ✅ 完成了什么

| 交付 | 证据锚（已复核存在） |
|---|---|
| 四个编排 skill 的「第零步：宿主/档位解析」四步（清脏→预检→捕获退出码→eval 后校验），四类子代理声明 mid 档 | `sdflow-implement/SKILL.md` 第零步段；`hack/check_tier_resolution_parity.py` 逐字节锁四份拷贝 |
| parity 守卫非恒真锚 | verify 独立变异实测：删任一步 4/4 变异 `rc=1`，baseline `rc=0` |
| `sdflow-done` 的裸 `eval` 升级为同一套四步 | `sdflow-done/SKILL.md` `### 0.4` 段 |
| T10 拆为 `T10-choice`（15 处规范性落点，②步升 strong）与 `review-loop-breaker`（独立成文、身份键跨轮稳定、三级互斥终态） | `openspec/adr/0031` + `openspec/CONTEXT.md` 术语条目；全仓 grep 复核 |
| 出票模式仲裁的确定性审计落点 | `impl-reports/planning-decisions.md`（含本 change 出票时点那条 ①档裁决的回填） |
| 共享 plan 文件名 resolver（探两名 / 双存在 fail-closed），gate 与 route import 同一份 | `ship_gate.py` 的 `PLAN_FILENAMES` / `resolve_plan_path`；`impl_route.py` sibling-import；`test_impl_route.py` 三条 `is` 身份断言 |
| tickets 轨计划文件名全量同步为 `tickets.md`（superpowers 轨保持旧名） | `openspec/adr/0033`；§7.3 全仓归因表 |
| 每票测试范围分层 + 强制「实现验证」收尾票 + 聚合套件发现契约 | `sdflow-implement/SKILL.md` 相应节；`openspec/adr/0032` |
| gate 第四道 plan 校验（仅新名触发，旧名 grandfather 并输出提示） | verify 独立实测四种形态：合格 / 无收尾票 / `Blocked-by` 缺号 / 旧名 grandfather |
| 收尾票聚合证据 | `impl-reports/task6-implementation-verification.md` 的三层 schema 行 |
| 全量套件与规格校验 | HEAD 复跑 `2927 passed / 11 skipped / 3 xfailed`；`openspec validate --strict` 通过 |

## ⏳ 未完成 / 延后

**批次 `harden-implement-review-loop`**（见 `openspec/issues/batches.md` 与 `openspec/issues/INDEX.md`），sweep 圈入 **13 项**：设计阶段 defer 的 T247–T255，加本轮新增的 T258–T261。其中本轮冷层代码审产出的三条值得优先看：

- **T259**〔跨模型 voice 独家〕`review-loop-breaker` 的①档可在**未修复**前提下关闭仍然成立的 Critical——D2b 的「互斥终态」修正只覆盖了②③档，①档留着旧形状。**本 change 内没修**：修它要改 delta spec 措辞，而实现期改四件套会触发 design 域失鲜。**这是本批次里唯一的逻辑正确性缺口，建议下个 change 优先清。**
- **T260** Codex 子代理授权段在 `CLAUDE.md` / `AGENTS.md` / `claude-section.md` 三处当前逐字节一致，但**无任何机械守卫**——漏改一处不会红，纯靠人记得。
- **T261** 两处 docstring/正文引用 `matt-workflow-integration/superpowers-plan.md` 已死链（该 change 早已归档到 `archive/2026-07-10-…`）。预存漂移，非本次引入。

**状态变更**：**T257** 判 `WONTDO` — 其标的（`plan_was_renamed` 与 `plan_first_sha` 的重复 git 调用）随该函数在冷层代码审中被整体删除而消失，evidence `5587d07`。

**verify 的 Minor 缺口（3 条，均不阻塞）**：

- **Minor-1（唯一实质项）**：Success Metric 1「跨机队正确性」**只做到机制层**。真 Codex 宿主内实证了 `resolve-models.sh` 解析出 codex 机队三档、零 Claude 专名，但**未实跑完整 `tickets-plan`**（会写 plan 文件、有触碰本 change 自身完成判据窗口锚的风险）。⇒「四类 dispatch 真派子代理时取到什么」仍未实证。`task6` 报告中「四条 Metric 全部有证据落点、无未验证项」的措辞**偏乐观，应读作「Metric 1 部分验证」**。
- **Minor-2**：收尾票证据锚 SHA `f22bc10` 早于 HEAD 两个提交——这正是 design 明写并接受的残余风险（收尾票是**实现期**门，不声称覆盖 code-review 之后的修复）；verify 已在 HEAD 复跑全绿，实际闭合。
- **Minor-3**：integration / e2e 记「未覆盖」——契约第③条要求的形态（缺层不罢工），非缺口。

## ▶ 下一阶段建议

1. **优先开一个清理 change 处理 T259** —— 它是本批次里唯一的**逻辑正确性**问题（其余是守卫缺失或文档漂移）。修法已经写清：①档的客观判据只能决定「已解决 / 仍成立」，已解决才关闭；仍成立则走 strong fixer + 仅复验一次，失败即 defer 并停。因为要动 delta/spec 措辞，必须独立成 change。
2. **T260 与 T261 可以搭同一个 change 一起清** —— 都是「一致性面」的活：T260 补机械守卫、T261 补归档路径前缀。与 T259 合并也行（都属本 change 的收尾残差），按 `change-scope-one-complete-stage-result` 判：若定位成「补齐 harden-implement-review-loop 留下的一致性与正确性残差」，三条同属一个完整阶段结果，可合并。
3. **Metric 1 的完整实证**（Minor-1）需要在 Codex 宿主下跑一次**完整的** `tickets-plan`。建议用一次性 fixture change 做，别拿真实在途 change 当靶子。
4. **roadmap**：无关联（`roadmap_writeback_draft.py` exit=3，非 roadmap 驱动 change），无需回填。

## ⚠️ scope drift（合并前请知悉）

本分支相对 `origin/main` 携带 **2 个与本 change 无关的提交**，将随合并一起进入 main：

- `0296ca0 checkpoint(workflow-rules): G1 收窄：撤回「全流程不用 /clear」的过度泛化，改为阶段内部禁、两处阶段交界 SHALL 清` —— 独立议题，含 `hack/tests/test_canonical_entry_sync.py` 的断言同步（45 行）。不在本 change 的 proposal Impact 清单内。
- `e5426e8 checkpoint(todolist): 记 T256：PreCompact 落盘调研` —— 该提交 subject **自述「挂 main，非本 change」**。

**未自动摘除的理由**：摘除需重写历史，而 `rebase` 会击穿归档报告里的 `reviewed_sha` 审计锚（本仓既有教训）。∴ 如实登记在此，让归档记录这两笔搭车，而非静默合并。**若不希望它们进 main，需在合并前人工处理。**
