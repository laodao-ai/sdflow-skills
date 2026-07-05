# Hand-off — three-lens-decision-framework (T46)

> verify 之后 / archive 之前产出。异步人类再入口 + 下个 change 种子。

## ✅ 完成了什么（每条附机验锚点）

把「三镜决策框架（系统/用户/开发循环 + 定主次）」+「fold-vs-defer scope-triage 判据」焊进 workflow 权威源与自制 skill 的 **6 落点**，跨落点口径统一，spec delta 同步：

- **① BASE-12**（`spec-quality-base.md:31`）：候选方案挂三镜评估 + 理由补主次判定行 + TG-23 触发 MUST。
- **② workflow.md G2**（`workflow.md:72/83`）：决策登记「两方后果」→「三面后果(系统/用户/开发循环)+主次判定」（canonical 基准）；`grep 两方后果` 全空。
- **③ code-review SKILL**（`SKILL.md:7/29/95/142-143`）：记理由按三镜+主次 + **「有把握自动选」对齐 T10 三级协议**（照 ship:23 canonical）；主动指令全清。
- **④ spec-review SKILL**（`SKILL.md:8/77/89`）：决策登记区/tension/格式块→三面后果+主次；事实核验 carve-out（不强制三镜）。
- **⑤ ship SKILL**（`SKILL.md:23`）：T10 台账「理由(三镜+主次)」与 code-review 同步。
- **⑥ BASE-18**（`spec-quality-base.md:42`）：fold-vs-defer 判据 + 防吸积 AND 门（同 capability∧高耦合∧低增量）。
- **spec delta**（`specs/spec-workflow/spec.md`）：两 MODIFIED 需求（决策登记后果字段 + tension）+ 3 新 scenario；`openspec validate` valid。

verify 结论 **PASS**（`verify-report.md`，含 `ship-gate: verify=PASS`）；commit 链 `ab6a775..HEAD`（task1-7 + impl-review）。

**层层加值实证**：codex outside-voice + spec-review 完整性镜把落点集从 3 校准到 6（漏了 spec-review SKILL 执行入口 + ship 台账副本）；code-review 阶段 codex+一致性+对抗+历史四镜再抓 4 项跨落点漂移（delta tension 残留「有把握」/ T10 step① 三处未齐 / 事实核验误套三镜 / BASE-18 宽严矛盾），全部自动修。两个实现子代理各自独立捕获计划的 over-broad grep 门 bug（有把握/两方视角）。

## ⏳ 未完成 / 延后

**批次 `three-lens-decision-framework`**（`openspec/issues/batches.md` + `openspec/issues/INDEX.md`，PLANNED）：
- **T50**（todolist，代码质量）：spec-review 决策登记区 ASCII 框 Q1 行加长后超边框宽度（cosmetic，结构未破不影响语义）；整框加宽须动 6 行、不成比例故 defer。
- **F3（docs/ 镜像刷新）**：`docs/workflow-overview.md` / `docs/workflow-skills/sdflow-spec-review.md` 等仍带旧「两方后果/两方视角」措辞，非权威源、量大，延后另 change 刷（Out of Scope 已声明）。
- **X2（trigger-catalog「≥2 合理方案」判例）**：可选优化，降 TG-23 漏判漂移，defer。

**延后的 ≥2 方案决策**：无遗留（Q1「有把握→T10」在设计门拍板 A 已纳入本 change；fold-vs-defer 判据 fold 进本 change）。

## ▶ 下一阶段建议

- **本 change 已 merge、两治理成果已持久化**（记忆 `decision-three-lens-framework` + `change-fold-vs-defer-cycle-cost`）——三镜框架 + fold-vs-defer 判据现跨 session/子代理/checkout 自包含生效。
- **消费仓生效**：其它用 workflow bundle 的项目需在该仓跑 `sdflow-init update` 拿最新 tools/（规则经全局 canonical 自动跟随）。
- **建议清理 change**（低优先，可合批）：docs/ 镜像刷新（F3）+ trigger-catalog 判例（X2）+ T50 cosmetic——三者同属「三镜框架收尾残差」，可一个 change 一起清（正是 fold-vs-defer 判据的应用：related+低影响→合批）。
- **运行 checkout 还原**：合并 push 后新会话跑 `/sdflow-upgrade`，把全局 canonical 从本开发 checkout 还原回运行 checkout。
