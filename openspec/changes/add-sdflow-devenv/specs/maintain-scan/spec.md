## ADDED Requirements

### Requirement: devenv 健康度扫描——`devenv_lint` 的唯一触发点

`sdflow-maintain` 在扫描消费仓 `openspec/` 一致性时，若检出 `openspec/architecture/.devenv.json` 存在，**SHALL 调用 `devenv_lint`** 并把其结果**原样并入**扫描报告。

> **为什么这条必须存在（dogfood 自指坑）**：`add-sdflow-devenv` 把「**无门禁**——某些检查无任何自动触发点、全靠人记得跑」列为立项理由之一，而其 `devenv_lint` **原本自己也没有任何触发点**。
>
> 更要命的是：devenv 的**渐进 DoD** 允许泳道停在 `scaffolded`、槽停在 `⚠️ 待定`，而**防止它烂成僵尸文档的唯一措施就是「把代价摆到人眼前」**（`adr/0021`）——**若无人调用该 lint，该措施为空。**
> **「不强制完成」+「不检查未完成」= 名存实亡**，两者只能选一个。**本条是 devenv 选择「不强制完成」后必须配的那一半。**

报告 SHALL 包含（**逐条列出，MUST NOT 只给计数**）：

1. **代价横幅**——`⚠️ 本框架 N/M 格待定，尚不构成一份可用的测试策略` + 逐层列出待补的槽
2. **`environments.md` 的待定槽数**——并**点名最贵的三槽**（常见坑 · 回滚 · 构建副产物）
3. **未 `verified` 的泳道**（`planned` / `scaffolded`）及其 `blocked_by`
4. **敷衍的 `blocked_by`**（`TODO` / `环境问题` —— 它没告诉任何人下一步该干嘛）
5. **SAD contract 差集**（`covers` 未覆盖的）

---

**⚠️ 两条诚实边界，SHALL 显式登记，MUST NOT 佯装：**

**① 它是提醒，不是门禁**〔`adr/0021`〕
`devenv_lint` **退出码永远是 0**（除非数据坏了）。`sdflow-maintain` **MUST NOT** 把它渲染成一个「通过 / 不通过」的门。
它提供的是「**更响的提醒**」——**代价可见 > 机械拦截**。

**② 结构通过 ≠ 内容已审**
报告 **MUST NOT** 把 lint 的结果二次简化成「`verified` = ✓」式的绿色状态。
`verified` 的语义是 **`verified-at <sha>`**——**一次历史执行的记录，不是「当前状态的绿灯」**。业务代码一改，那个绿灯就在说谎。
**渲染 SHALL 原样带上 commit 锚与日期。**

---

**降级**：

| 情形 | 行为 |
|---|---|
| 消费仓无 `.devenv.json` | **跳过**本扫描项（非报错） |
| `devenv_lint` 不可用（未装 `sdflow-devenv`） | **显式提示**「检出 `.devenv.json` 但 `devenv_lint` 不可用，跳过健康度扫描」——**MUST NOT 静默略过** |

#### Scenario: 扫描逐条报出未 verified 泳道
- **WHEN** 消费仓存在 `.devenv.json`，其中两条泳道处于 `scaffolded`
- **THEN** 扫描报告**逐条**列出这两条泳道及其 `blocked_by`——**不只给「2 条未完成」这个计数**

#### Scenario: 代价横幅原样透传
- **WHEN** 三层框架有 12/15 格待定
- **THEN** 扫描报告含 `⚠️ 本框架 12/15 格待定，尚不构成一份可用的测试策略`

#### Scenario: 它是提醒不是门禁
- **WHEN** 三层框架十五格全待定
- **THEN** `sdflow-maintain` **报出来但不失败**——它没有硬拦截

#### Scenario: verified 不得渲染成无条件的绿
- **WHEN** 报告呈现一条 `verified` 泳道
- **THEN** 它带着 commit 锚与日期（`verified-at abc123f · 2026-07-14`），**MUST NOT** 呈现为「✓ 已通过」

#### Scenario: 无 .devenv.json 时跳过
- **WHEN** 消费仓不存在 `openspec/architecture/.devenv.json`
- **THEN** 跳过 devenv 健康度扫描，不报错

#### Scenario: devenv_lint 不可用时显式提示
- **WHEN** 消费仓存在 `.devenv.json` 但未安装 `sdflow-devenv`
- **THEN** 显式提示「检出 `.devenv.json` 但 `devenv_lint` 不可用，跳过健康度扫描」，**MUST NOT 静默略过**
