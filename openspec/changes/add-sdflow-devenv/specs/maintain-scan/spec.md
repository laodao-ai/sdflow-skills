## ADDED Requirements

### Requirement: devenv 健康度扫描——`devenv_lint` 的唯一触发点〔设计门 Q6=A · CEO-2〕

`sdflow-maintain` 在扫描消费仓 `openspec/` 一致性时，若检出 `openspec/architecture/environments.md` 存在，**SHALL 调用 `devenv_lint`** 并把其结果并入扫描报告。

报告 SHALL 包含：

1. **未 `verified` 的泳道清单**（`planned` / `scaffolded`）及其 `blocked_by`——**逐条列出，MUST NOT 只给计数**
2. **失配的 source digest**（人改了 Makefile recipe 使 `verified` 泳道的验证证据失效）
3. **空 `blocked_by` 的 `scaffolded` 泳道**（诚实性违规）
4. **残留 `blocked_by` 的 `verified` 泳道**（绿泳道挂着「本机无 X」= 文档在说谎）

> **为什么这条必须存在（dogfood 自指坑）**：`add-sdflow-devenv` 把「无门禁——某些检查无任何自动触发点、全靠人记得跑」列为立项理由之一，而其 `devenv_lint` 原本**自己也没有任何触发点**。
>
> 更致命的是：devenv 的「渐进 DoD」允许泳道停在 `scaffolded`，而**防止它烂成僵尸文档的唯一措施就是「lint 复述未完成清单」**——若无人调用该 lint，该措施为空。**「不强制完成」+「不检查未完成」= 名存实亡**，两者只能选一个。本条是 devenv 选择「不强制完成」后**必须**配的那一半。

**诚实边界（MUST 显式登记，MUST NOT 佯装）**：`sdflow-maintain` 是**人主动跑**的 ⇒ 本条提供的是「**更响的提醒**」而非**硬门禁**（无 `ship_gate` 式硬拦截）。是否再加硬拦截 → `add-sdflow-devenv` proposal 的 Q-5。

**降级**：消费仓无 `environments.md` ⇒ 本扫描项**跳过**（非报错）；`devenv_lint` 不可用（未装 `sdflow-devenv`）⇒ **显式提示**「检出 environments.md 但 devenv_lint 不可用，跳过健康度扫描」，**MUST NOT 静默略过**。

#### Scenario: 扫描报出未 verified 泳道
- **WHEN** 消费仓存在 `environments.md`，其中两条泳道处于 `scaffolded`
- **THEN** `sdflow-maintain` 的扫描报告逐条列出这两条泳道及其 `blocked_by`

#### Scenario: 拦下真实回归
- **WHEN** 操作者修改了某 `verified` 泳道对应的 Makefile recipe，使其 source digest 失配
- **THEN** 扫描报出该泳道验证证据失效，要求重跑 `verify-lane`

#### Scenario: 无 environments.md 时跳过
- **WHEN** 消费仓不存在 `openspec/architecture/environments.md`
- **THEN** 跳过 devenv 健康度扫描，不报错

#### Scenario: devenv_lint 不可用时显式提示
- **WHEN** 消费仓存在 `environments.md` 但未安装 `sdflow-devenv`
- **THEN** 显式提示「检出 environments.md 但 devenv_lint 不可用，跳过健康度扫描」，MUST NOT 静默略过
