## Why

sdflow-done 收尾流水线对 **roadmap 文档包零触碰**。roadmap 驱动的分阶段 change 归档后，复选框 / task-log 完成总结 / 里程碑状态全靠**人工手动回填**（本会话刚为 lens-metric-emit=P4/4.C 手动补过一次）。issues 侧早有 `§2.1 sweep` 自动化，roadmap 侧是**对称缺口**。

> 〔spec-review-amendment · adr/0014〕本 change 经 grill + 7 镜 spec-review + 两次目标态纠正，骨架从「起手锚 best-effort」重构为「**编号统一 + producer 机械生成投影链**」——根因是起手锚 producer 契约无机械闭环（靠人写对锚 = adr/0006 静默跳步）+ 致命误勾。

## What Changes

- **编号统一投影**：roadmap 子任务号（`4.D.1`）= 唯一编号；roadmap 驱动 change 的 tasks.md 顶层组采用之（`## 4.D.1`）。done 归档**镜像** tasks 组完成态 → roadmap 同号复选框（组全 `[x]`→勾、defer 组 `[ ]` 不勾）。**真相源 = 归档实况盘面（tasks 完成态，第 0.3 步已对账），非起手锚快照**。
- **producer 机械生成投影链**：roadmap 结构化生成 → change **scaffold**（从 roadmap 抄编号 + 机械写 `roadmap: {name}` 锚 + proposal 引用）→ 实现勾 tasks → 镜像回写。每环机械、不靠人写对。
- **关联判据**：L1 = tasks 的 `<!-- roadmap: {name} -->` 锚（scaffold 写）；漏锚兜底 **lint**（tasks 用 roadmap 式编号 `N.X.Y` 却无 name 锚 → **fail-closed 拦，非静默**）。L2 = 扫 tasks 组完成态（盘面，不靠锚 subtask）。
- **回写机械/判断切分**：镜像勾选（行首锚定）+ 阶段状态 enum **机械聚合**（从复选框）= 脚本；完成总结叙述 + 里程碑句 = 模型。真判断仅两处。
- **生成侧结构化**（sdflow-roadmap 两模板）：子任务号 + 阶段状态 enum 列 + task-log 机器锚。
- **fail-safe**：漏锚（有编号无 name）fail-closed 非静默；镜像不匹配（roadmap 改号）→ 降级标注落 task-log；全程不阻塞 archive/merge。
- 旧 2 roadmap 迁移新格式（不 dual-read）。issues 不动（§2.1 sweep）。**无 BREAKING**（无关联零差异）。

## Capabilities

### New Capabilities

（无——加需求到现有 spec-workflow。）

### Modified Capabilities

- `spec-workflow`: 新增三 Requirement——① roadmap 编号统一与关联判据（tasks 采用 roadmap 子任务号 + L1 name 锚 + 漏锚 lint）② sdflow-done 镜像回写（tasks 完成态 → roadmap，机械镜像 + 判断切分）③ roadmap 生成侧结构化与 change scaffold（producer 机械生成）。与既有「批次注册表与 reindex 被动同步」（issues sweep）为对称收尾回写契约。

## Impact

- **改 skill 本体**：`sdflow-done/SKILL.md`（3.5 镜像步，并入 archive 中档子代理）+ `sdflow-roadmap/SKILL.md` + `references/{roadmap,task-log}-template.md`（索引层结构化）+ scaffold 子命令。
- **新增脚本**：change scaffold + 回写（镜像勾选/阶段 enum 聚合/机器锚校验）+ 关联 lint → `scripts/` + `tests/`（改 scripts 必跑 tests 红线）。
- **workflow 规则**：关联锚/编号约定改 `sdflow-init/assets/workflow/`（权威源）再 `sdflow-init update` 推下游（bundle dogfooding 红线），**不只改仓内 openspec/workflow/**。
- **迁移** 2 roadmap（mechanical-layer-hardening / workflow-cost-optimization）。
- **外部影响方**：sdflow-done/sdflow-roadmap 经 symlink 铺所有消费仓；条件触发 + fail-safe 保无 roadmap 仓零差异。
- **不改 opsx:ff**（官方）——scaffold 作其外的本仓 producer 环。

## Success Metrics

- roadmap 驱动 change 归档后，roadmap 复选框**镜像** tasks 完成态（defer 项不误勾）、阶段 enum 机械更新、task-log 完成总结带机器锚——无需手动回填。
- 漏 name 锚（有 roadmap 编号）→ lint/done **fail-closed 提示、非静默**。
- 无关联 change / 无 roadmap 仓：done 行为零差异。
- scaffold/回写/lint 坏输入 → fail-closed 非零退出，pytest 覆盖。
- **正路径经一次真实全链 dogfood**（scaffold→实现→镜像），非仅 fixture（补 spec-review Q3）。

## Non-Goals

- 不碰 issues 回写（§2.1 sweep）。不做 roadmap Review 处置对账（4.D.4）。
- 不改 opsx:ff（官方）——scaffold 外挂。
- 不全 frontmatter 化 roadmap（叙述层留散文）。不背 dual-read。
- 暂不做阶段状态 enum 漂移对账（人工编辑 roadmap 后回读校验）——显式记风险接受 + todolist，不留白。

## Compliance

- 全局红线：脚本 fail-closed + pytest 覆盖坏输入非零退出；判断（完成总结/里程碑句）显式留模型。
- 反静默：漏锚 fail-closed 非静默；降级标注落 task-log。
- 目标态论证正解：producer 契约机械保证（scaffold），非「人遵守 prose MUST」（adr/0014）。
- bundle 纪律：workflow 规则改 assets/workflow 再 update；skill 本体改后跑 setup.sh。
- 审查顺序：`/review` → push → `/code-review`。

## 需求优先级（TG-19）

- **P0** · 编号统一 + L1 name 锚 + 漏锚 lint（关联判据地基，机械闭环）。
- **P0** · done 镜像回写（tasks 完成态 → roadmap，机械镜像勾选 + 阶段 enum 聚合）。
- **P0** · change scaffold（producer 机械生成 tasks 编号 + 锚，闭合"靠人写对"）。
- **P1** · 生成侧模板结构化 + task-log 完成总结（模型叙述 + 机器锚）。
- **P1** · 里程碑句更新 + 旧 2 roadmap 迁移。
- **P2** · 阶段 enum 漂移对账（backlog）。

## 利益相关方与外部依赖（TG-20）

- **所有 sdflow-skills 消费仓**：sdflow-done/sdflow-roadmap 经 symlink 铺设；条件触发 + fail-safe 保无 roadmap 仓零影响。
- **opsx:ff（官方，不改）**：scaffold 作其外/后的本仓 producer 环，不侵入。
- **/sdflow-ship 链**：done 是链末端；镜像回写 MUST NOT 破坏 merge 缺省语义。

## 假设（TG-22）

- **假设 1** · roadmap 驱动 change 的 tasks.md 由 scaffold **机械生成**（编号抄自 roadmap、name 锚自动写），非靠人写对。**失效**（跳过 scaffold 手写）：漏 name 锚 → lint fail-closed 拦（编号形态可判），非静默。
- **假设 2** · change tasks 组完成态是归档时的可信盘面（done 第 0.3 步对账保证）。**失效**：对账缺失 → 沿用 done 现有复选框对账门。
- **假设 3** · roadmap 子任务号在 change 生命周期内稳定（scaffold 后 roadmap 不重排该 change 关联子任务号）。**失效**：roadmap 改号 → 镜像不上 → 降级标注留人工（残余 best-effort）。
