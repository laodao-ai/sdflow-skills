---
name: sdflow-maintain
description: 扫描 openspec 目录状态，对比 INDEX.md，报告差异并修复。归档变更后、手动增删 spec 后、合并上游更新后使用。Trigger with /sdflow-maintain。
license: MIT
compatibility: 需要 openspec 目录结构（openspec/specs/、openspec/rules/、openspec/INDEX.md）。
metadata:
  author: opsx
  version: "1.0"
---

扫描 openspec 目录，对比 INDEX.md，报告差异，经确认后修复。

**触发时机**：归档变更后、手动增删 spec 后、合并上游更新后。

**步骤**

1-3. **调 maintain_scan.py 出只读差异报告**

   跑 `python3 sdflow-maintain/scripts/maintain_scan.py --root <仓根>`（缺省自动探测 git 根），
   得四类分节只读报告：**新增未索引** / **已删未清理**（specs/rules ↔ INDEX 托管块外双向 set-diff，
   链接路径 join）/ **过时引用**（CLAUDE.md 引用已删 spec/rule）/ **陈旧遮蔽**（workflow bundle 残留规则本体）。

   脚本纯读、fail-closed（坏输入非零退出 + stderr 明示，绝不半信半疑输出「一致」），零写文件。
   set-diff 判据（RULE_MARKERS / opsx-init:rules 托管块 token）canonical 见 `sdflow-init/scripts/init.py`，
   maintain_scan 保自包含副本经一致性守卫 pytest（`tests/test_marker_consistency.py`）机验同步。

   如果报告显示无差异，输出 "INDEX.md 与文件系统一致，无需更新"，**跳过步骤 4，直接执行步骤 5**（提示跑
   `/sdflow-retro` 复盘——与 INDEX 是否有差异无关，见下）。

4. **询问用户是否修复**

   显示报告后，使用 AskUserQuestion tool 询问用户是否执行修复。

   **如果用户确认**：
   - 新增未索引的条目：添加到 INDEX.md 对应主题分组表格
     - 对于新 spec：根据 spec 文件内容推断所属主题分组，无法推断时询问用户
     - 对于新 rule：添加到「设计强制规范」表格
   - 已删未清理的条目：从 INDEX.md 所有表格中移除
   - 修复后显示变更摘要："已更新 INDEX.md：+N -M"，**继续执行步骤 5**（提示跑 `/sdflow-retro`
     复盘——与 INDEX 是否修复无关，见下）。[impl-review-fix CF-3]

   **如果用户拒绝**：输出 "跳过修复"，**继续执行步骤 5**（提示跑 `/sdflow-retro` 复盘——与用户是否
   同意修复 INDEX 无关，见下）。

5. **提示跑 /sdflow-retro 复盘（薄指针）**

   本步与上面 INDEX 修复流程无关、无条件跑在**每次维护会话最后**（无论步骤 4 是否有修复）——
   聚合正主已迁 `/sdflow-retro`（`sdflow-retro/scripts/lens_metric_aggregate.py`），本步**不内联跑
   聚合器、不内联扫 flag、不内联呈现 surfacing 区块**，只在报告末尾显著提示：

   ```
   提示：跑 /sdflow-retro 看完整复盘（含度量待复评 N≥10 出现轮数的镜、成本×价值视角）。
   ```

   - **config 门控**：读 `openspec/config.yaml` 的 `metrics.enabled`——缺省或 `false` → 跳过本步（不提示）。
   - 无条件跟在归档/维护会话之后提示，**不丢失 cadence**——每次 `/sdflow-maintain` 跑完都会出现这行提示，
     而非只在检测到差异或某种阈值时才提示。
   - 具体聚合逻辑（读归档报告、算出现轮数/采纳率/独立率、判定 `≥10待复评`）已整体迁出本 skill，见
     `/sdflow-retro`；本步不重复实现，也不做任何判断——只做提醒。

**护栏**

- **禁止修改 CLAUDE.md** — 不管是根目录还是子目录的 CLAUDE.md，都只报告不修改
- **只修改 INDEX.md** — 修复范围严格限定在 `openspec/INDEX.md` 一个文件
- **所有修改必须经用户确认** — 不自动修复，先报告再询问
- **步骤 5（/sdflow-retro 提示）只读不写** — 不产生任何文件改动、不算作"修复"，不受上面「只修改
  INDEX.md」的例外覆盖；本步只提示，不做度量判断——判断与呈现交给 `/sdflow-retro`
