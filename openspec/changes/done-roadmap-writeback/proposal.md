## Why

sdflow-done 收尾流水线对 **roadmap 文档包零触碰**。roadmap 驱动的分阶段 change 归档后，`roadmap.md` 复选框、`task-log.md` 完成总结、里程碑/阶段状态全靠**人工手动回填**——本会话刚为 lens-metric-emit（P4/4.C）手动补过一次，漏填就让下次判"下一步"读到陈旧状态。issues 侧早有 `§2.1 sweep` 自动化，roadmap 侧是**对称的缺口**。

> 〔grill-amendment · adr/0013〕本 proposal 经 grill 重构：以**目标态**为基准（非现状快照），把回写从「适配现状散文格式 + fail-closed」升级为「生成侧结构化 + best-effort 记录维护」。scope 从纯 Markdown 一步扩为 6 件。

## What Changes

- **关联锚契约**：roadmap 驱动 change 起手在 proposal 写机器锚 `<!-- roadmap: {name} phase: {PN} subtask: {id,...} -->`；done 回写 grep 它定位——**不解析自然语言引用**（措辞属概率空间，实证 2/6 proposal 全路径）。
- **生成侧结构化**（改 `sdflow-roadmap` 两模板）：roadmap **索引层**（子任务复选框、阶段状态 enum、task-log 机器锚）结构化，**叙述层**（目标/理由/完成总结叙述/里程碑句）留人读散文。结构化投入放 producer 侧摊销（生成一次、回写多次）。
- **sdflow-done 回写步**（第 3.5 步，archive 后 / commit 前）：读锚 → **best-effort 回写**（勾选 + 阶段状态 cell + 完成总结 + 里程碑），随第四步 `git add openspec/` 提交。
- **机械/判断切分**：勾选 + 阶段状态 = 脚本机械写；完成总结叙述 + 里程碑句 = 模型写、脚本校验机器锚（anchor_lint 式）。判断收窄到两处。
- **best-effort 三级 fail-safe**：全定位→全写；部分定位→回写能做的 + **降级标注**未做项（反静默）；完全无法解析→fail-closed 留人工。**全程不阻塞 archive/merge**（记录维护非正确性门）。
- **无关联静默跳过**：无锚 / 无 roadmap 的仓 → 行为零差异。
- **旧 2 roadmap 迁移**新格式（不背 dual-read）。
- **无 BREAKING**：条件触发，无关联零差异。issues 侧不动（§2.1 sweep）。

## Capabilities

### New Capabilities

（无——加需求到现有 spec-workflow。）

### Modified Capabilities

- `spec-workflow`: 新增三 Requirement——① roadmap 关联锚契约（producer 锚 + L1/L2 读锚）② sdflow-done 归档回写关联 roadmap（best-effort 三级 + 机械/判断切分）③ roadmap 生成索引层结构化（sdflow-roadmap 模板产状态 enum + 机器锚）。与既有「批次注册表与 reindex 被动同步」（issues sweep）为对称收尾回写契约。

## Impact

- **改 skill 本体**：`sdflow-done/SKILL.md`（第 3.5 步回写编排）+ `sdflow-roadmap/references/{roadmap,task-log}-template.md`（索引层结构化）。
- **新增脚本**：`roadmap-link`（起手写锚）+ 回写脚本（勾选 + 阶段状态机械写、机验锚校验）→ 归属 skill `scripts/` + `tests/`（本仓「改 scripts/ 必跑 tests/」红线）。
- **迁移**：现有 2 个 roadmap（`mechanical-layer-hardening` / `workflow-cost-optimization`）迁新格式。
- **外部影响方**：`sdflow-done`/`sdflow-roadmap` 经 symlink 铺给所有消费仓；条件触发 + fail-safe 保证无 roadmap 的仓零影响。改后跑 `setup.sh`。
- **领域**：不命中 backend / embedded / frontend。

## Success Metrics

- roadmap 驱动 change 归档后，其复选框已勾、task-log 有完成总结（带机器锚）、阶段状态 enum 已更新——无需手动回填。
- 部分定位失败时：回写能做的 + 未做项在 hand-off/摘要显式标注（不静默漏、不整体丢弃）。
- 无关联 change / 无 roadmap 仓：done 行为与现状零差异。
- 脚本坏输入（锚格式错 / roadmap 格式异常）→ fail-closed 非零退出，pytest 覆盖。

## Non-Goals

- 不碰 issues 回写（§2.1 sweep 已覆盖）。
- 不做 roadmap Review 处置对账（mlh 4.D.4，校验非回写）。
- 不**全** frontmatter 化 roadmap——只结构化索引层，叙述层留散文。
- 不背 dual-read——旧 2 roadmap 一次性迁移。
- 不跨 change 自动推断阶段总览——里程碑句判断留模型。

## Compliance

- 全局红线：脚本 fail-closed + pytest 覆盖坏输入非零退出；判断（完成总结叙述/里程碑句）显式留模型。
- 反静默守卫：回写未做项 MUST 降级标注，MUST NOT 静默。
- bundle 纪律：sdflow-done/sdflow-roadmap 是 skill 本体、非 workflow bundle；改后跑 `setup.sh`。
- 审查顺序：`/review` → push → `/code-review`。

## 需求优先级（TG-19）

- **P0** · 关联锚契约 + L1/L2 读锚（关联判定地基）+ best-effort fail-safe 不误写。
- **P0** · 生成侧索引层结构化（sdflow-roadmap 模板）——回写机械化的前提。
- **P0** · 勾选 + 阶段状态 cell 机械回写脚本。
- **P1** · task-log 完成总结（模型写叙述 + 机器锚校验）。
- **P1** · 里程碑句更新（判断步）+ 旧 2 roadmap 迁移。
- **P2** · `roadmap-link` 起手写锚脚本（辅助，人手写锚亦可 fallback）。

## 利益相关方与外部依赖（TG-20）

- **所有 sdflow-skills 消费仓**：`sdflow-done`/`sdflow-roadmap` 经 symlink 铺设；条件触发 + fail-safe 保证无 roadmap 的仓零影响（首要约束）。
- **sdflow-roadmap（本 change 改其生成格式）**：从「只被引用不改」翻为「纳入 scope」——`SKILL.md:195` 本预告 done 接 hook 自动化，配合非越界。
- **/sdflow-ship 链**：done 是链末端；回写步 MUST NOT 破坏 merge 缺省语义与 ship 透传。

## 假设（TG-22）

- **假设 1** · roadmap 驱动 change 起手会带关联锚（契约强制 + `roadmap-link` 辅助）。**失效**：漏锚 → 按无关联跳过 + hand-off 显式提示（反静默），非静默漏。
- **假设 2** · 一个 change 关联一个 roadmap 的一组明确子任务（锚 subtask 列表）。**失效**：多关联无法消歧 → 静默跳过（当无关联）。
- **假设 3** · 迁移后消费仓 roadmap 走新格式（索引层结构化）。**失效**：格式异常 → 回写 fail-closed 留人工（末级），不猜写。
