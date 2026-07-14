---
name: sdflow-maintain
description: 扫描 openspec 目录状态，对比 INDEX.md，报告差异并修复。归档变更后、手动增删 spec 后、合并上游更新后使用。Trigger with /sdflow-maintain。
license: MIT
compatibility: 需要 openspec 目录结构（openspec/specs/、openspec/rules/、openspec/INDEX.md）。
metadata:
  author: opsx
  version: "1.0"
---

<!-- sdflow:principles:start —— 真相源 sdflow-init/assets/hack/skill-principles.md，由 hack/sync_principles.py 注入，勿手改本区块 -->
## 🟢 三条通则（所有 sdflow skill 共用 · 违反即本次运行失败）

### ① 能查的自己查，能调研的自己调研

答案在**仓里 / 这台机器上 / 公开资料里** ⇒ **自己去拿**，查完**直接给结论**。
**MUST NOT 拿一个自己查得到的问题去占用人的注意力。**

❌「你们前端用什么测试框架？」（`package.json` 里写着）
❌「有没有 CI？」（`.github/workflows/` 看一眼）
❌「这个函数在哪调用？」（grep）

**给结论，不给过程**：「你们的集成测试是 `make integration`，我跑过了，绿」——
**而不是**「我看到 Makefile 里好像有个 integration target，你确认一下？」

### ② 不确定的方案，先调研再给推荐 —— **MUST NOT 甩开放题**

拿不准的时候，**MUST NOT 把几个选项原样丢给人**——那是**把调研的活布置给了人**。
正确动作：**先把能查的查了，带着「推荐 + 依据 + 代价 + 备选」进人门，人只负责拍板。**

> ❌「Windows 包怎么产出？（买台机器？GitHub Actions？还是 non-goal？）」——三个选项，零调研，零推荐
> ✅「**建议走 GitHub Actions 的 windows runner。** 依据：① 本仓已有 workflows ② 工具链官方支持
> ③ 公开仓免费。**代价**：签名要证书，首版只能出未签名包。**备选**：降为 non-goal（后果：Windows
> 用户没有可用产物）。**要不要这么定？**」

**⇒ ①② 合起来的三分判据**（每个问句先归一次类）：

| 答案在哪 | 动作 |
|---|---|
| 仓 / 机器 / 公开资料 | **自己查** → 给结论。**不问**（①） |
| 查得到候选与依据（选型 · 路线 · 工具） | **调研 → 推荐 + 依据 + 代价 + 备选 → 人拍板**（②） |
| **只在人脑子里**（偏好 · 踩过的坑 · 拍板权 · 组织约束） | **问** —— **注意力该全花在这里** |

> **人做的是拍板，不是替你做调研。**
> 人的注意力是唯一消耗掉就补不回来的资源：每问一个「你们用什么测试框架？」，
> 就挤掉一个「你上次被这个东西坑到是什么事？」——**而后者只有人知道。**

### ③ 以最终目标为准，MUST NOT 拿现状反驳目标

判断「该不该做 / 做到什么程度」**一律锚目标态**，**不受现有代码与设计的束缚**。

**MUST NOT** 用下面这些来论证「目标不该做 / 该缩水 / 可以妥协」：

- ❌「现在的代码不是这么写的」
- ❌「存量数据里没出现过这种情况」
- ❌「现状里这种情况很少见」
- ❌「现有设计不支持，所以改小一点」

> 迁移中「旧数据还没有新形态」是**必然**——拿它当风险基线，会把「**目标态才暴露的面**」
> 误判成「不存在」。这是**拿现状给目标松绑**。
>
> **正确的问法**：「**目标态下的 producer 会不会产出这种形态？**」
> **不是**：「现存文件里有没有？」

> 🔴 **评审类场景是本条的高发区**——评审时，**现状是唯一摆在眼前的东西**，
> 于是「它现在能跑 / 现在没出过事」极易被当成「它是对的 / 不用改」。
> **评审的基准是目标态，不是现状。**

### 🔴 传播纪律：**fan-out 子代理 / outside-voice MUST 原文带上这三条**

**子代理与 outside-voice 跑在 fresh context —— 它们看不见本文件。**

⇒ **每一个 fan-out 子代理的 prompt、每一份 outside-voice 的 context，MUST 把本区块
（`sdflow:principles` 从 `start` 到 `end`）原文整段复制进去。**
**MUST NOT 转述、MUST NOT 摘要、MUST NOT 只给指针。**

> **漏带的后果是确定的，不是概率的**：一个冷上下文的镜子，眼前只有现状，
> 它**必然**把「现在能跑」当成「是对的」，把「存量里没见过」当成「不会发生」——
> 而这正是 ③ 要杀的病。**冷是它的价值，也正是它的破绽。**

<!-- sdflow:principles:end -->

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
