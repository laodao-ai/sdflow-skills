# Design — done-roadmap-writeback

> 〔spec-review-amendment · adr/0015〕**三轮收敛终局** = 「回填降摩擦助手：机械搬运自动化、判断留人」。机械回写骨架（起手锚 adr/0013 → 编号统一 → 归属镜像+scaffold adr/0014）经两轮 grill + 两轮 7 镜 spec-review 全被揭穿——**C1**（scaffold 撞 openspec CLI「文件存在=done」短路产出链，源码证实）+ **C2**（阶段 enum deferred 无机器信号、公式循环，不可机械）+ defer 重现原痛点 + ROI 失衡。现状实践核验锚定「**完成判定本质含判断**」（人对照验收标准判）。据此弃全部机械回写骨架，收敛为最小核。完整档案见 `adr/0015`（supersede `adr/0013`+`adr/0014`）。

## Context

`sdflow-done` 收尾六步（接地核验一致）：`0 对账 → 1 verify → 2 hand-off(§2.1 sweep) → 3 archive → 4 commit → 5 merge → 6 摘要`。缺口：全流程对 `openspec/roadmaps/` 零触碰，靠人工回填。

**两轮 spec-review 两致命（否决机械回写）**：
- **C1**：`@fission-ai/openspec` CLI 判 artifact done **只看文件存在**（`state.js:artifactOutputExists`），`apply: requires: [tasks]`。任何在 change 产物文件（tasks/proposal）上抢写的第二 producer（scaffold）会短路 opsx:ff 产出链。判定机制在官方 CLI、本仓改不了。
- **C2**：阶段 enum 公式 `全非deferred完成=delivered` 自身循环 + deferred 无机器信号（二值复选框 `[ ]` 无法区分「未做」vs「显式放弃」）——把规划判断当机械聚合，范畴错误。

**现状实践核验**（实地查 git/roadmap）：完成判定 = 人在 change 归档**后**读确定性盘面（merge/verify=PASS/归档进 base）+ 对照人写 `### 验收标准`（语义判断）→ **手动**勾复选框 + 写交付标注 + task-log 完成总结（commit「回填对账」）。**完成判定本质含判断，现状无机械判据**。

## Goals / Non-Goals

**Goals:**
- 降低现状「人工回填」摩擦：done 收尾读**确定性盘面**生成**回填草稿**（候选复选框 + task-log 完成总结骨架含机械锚），人异步确认回填。
- 切分清晰：**机械搬运**（盘面读取 + 骨架预填）自动化，**判断**（算不算完成/勾哪些/价值叙述/阶段状态/deferred）留人确认。

**Non-Goals（弃机械回写骨架，消 C1/C2）：**
- **MUST NOT** scaffold 双向预建（消 C1：不写 change 产物文件、不碰 opsx:ff done 判定）。
- **MUST NOT** 阶段状态 enum 机械聚合（消 C2：阶段状态/deferred 是判断，留人写散文）。
- **MUST NOT** 编号统一 / 归属镜像（消粒度失配：roadmap 复选框=change 级、tasks=实现分解，各保现状格式）。
- **MUST NOT** 强制 roadmap 机读化 / 存量迁移（判断留人不需机械镜像，roadmap 现状散文即可，助手适配）。
- 不碰 issues（§2.1 sweep）。不做 4.D.4 Review 对账。不改 opsx:ff。

## Decisions

### D-1 完成判定的盘面-判断切分（现状实证）

| 判定组成 | 性质 | 谁做 |
|---|---|---|
| 对应 change 是否归档/merge/verify=PASS | **确定性盘面**（机械可读，ship_gate 已用同款） | 助手读 |
| 是否满足该子任务 `### 验收标准` | **判断**（语义条件） | 人 |
| 复选框该不该勾 / 算不算 delivered / deferred | **判断** | 人 |

助手只自动化**盘面搬运**，判断留人——与现状（人对照验收标准回填）同边界，与 `lens-metric`（计数机械/分类判断）、`issues sweep`（triage 机械/归批判断）同构。

### D-2 定位 = 回填降摩擦助手（草稿 + 人确认，非自动回写）

```
change 归档(done)
   │  助手读确定性盘面: archive路径 + verify=PASS frontmatter + merge + tasks完成态 + 验证数字
   ▼
生成回填草稿(进 hand-off):
   ├─ 候选复选框行(定位 change 声明关联的 roadmap 子任务, 列出"建议勾")
   └─ task-log 完成总结骨架(预填机械锚: change名/merge/archive路径/pytest数 + 交付标注模板)
   │
   ▼  提示人异步确认(阶段三无门 → 不弹窗, 走 hand-off)
人过目草稿: 判断算不算满足验收标准 → 勾哪些 + 补价值叙述/阶段状态/deferred → 提交(同现状"回填对账"commit)
```

从「纯手写回填」降为「改助手草稿」——机械的搬运（敲 change/merge/archive/验证数字、定位复选框行）自动化，判断（算不算完成、价值叙述）留人。

### D-3 机械/判断切分

- **助手机械预填草稿**：从确定性盘面读 change 交付事实（archive 路径 / verify=PASS / merge / tasks 完成态 / pytest 数）→ 生成候选复选框列表 + task-log 完成总结骨架（机械锚 + 标注模板）。
- **人确认/补**：算不算满足验收标准、勾哪些复选框、完成总结价值叙述（grill/冷审价值/defer）、阶段状态散文、里程碑句、deferred 判定——**全是判断，草稿只提供骨架不代人判**。

### D-4 触发与时机（阶段三无人类门约束）

- sdflow-done 收尾（hand-off 那步）检测 change 关联 roadmap → 回填草稿写进 **hand-off**（随归档留档），提示「检测到关联 roadmap {name}，回填草稿见下，请过目后回填 roadmap」。
- **阶段三无 AskUserQuestion**：草稿进 hand-off 让人**异步**确认，**不弹窗、不阻塞**归档/merge（同现状：人本就在归档后独立回填）。
- 人异步过目 hand-off 草稿 → 确认判断 → 回填 roadmap（独立 commit，同现状实践）。

### D-5 关联（轻量声明，漏=现状不阻塞）

- change 声明关联 roadmap：轻量标记（proposal/tasks 里一行 `<!-- roadmap: {name} -->`，或人在调 done 时指定 `--roadmap`）。
- done 检测到 → 生成草稿；**未声明 = 退回现状**（人全手工回填），**不 fail-closed 阻塞**（辅助非正确性门），可轻量提示、不强制。
- **不 scaffold 机械生成关联**（不碰 opsx:ff，消 C1）。

### D-6 弃什么（消 C1/C2/粒度/H4）

| 弃 | 消除的 spec-review 问题 |
|---|---|
| scaffold 双向预建 | C1（不写 change 产物 → 不撞 openspec done 判定）+ H2 孤儿认领 + H5 早写冲突 |
| 阶段 enum 机械聚合 | C2（deferred 留人写散文，不硬塞机械 enum） |
| 编号统一 / 归属镜像 | 粒度失配（roadmap/tasks 各保现状格式） |
| 强制 roadmap 机读化 / 存量迁移 | H4（roadmap 现状散文即可，助手适配、人读） |
| best-effort 三级机械镜像 | 完成判定含判断（现状实证），机械镜像越界 |

### D-7 组件清单（最小）

1. **回填草稿生成**（读确定性盘面 → 候选复选框 + task-log 完成总结骨架含机械锚）——机械部分可轻脚本辅助（读 archive/verify frontmatter/tasks 完成态、拼骨架），判断留人。
2. **sdflow-done 收尾提示步**（hand-off 那步：检测关联 → 草稿进 hand-off + 提示人回填）。
3. **关联声明约定**（change 轻量标记 `<!-- roadmap: {name} -->` 或 done `--roadmap`）+ 可选轻量提示（未声明但疑似 roadmap 驱动）。

**无** scaffold / enum 聚合 / 编号统一 / 迁移 / 生成侧模板大改。

## Risks / Trade-offs

- **[人仍需确认回填、非全自动]** → 这是设计取向（完成判定含判断，现状实证），非缺陷；助手把摩擦从「纯手写」降到「改草稿」，判断本就该人做。
- **[漏声明关联 → 退回现状手工]** → 记录维护非门，可接受；轻量提示降漏率、不 fail-closed。
- **[草稿定位复选框不准]** → 草稿是给人过目的、人会改，非机械直写 roadmap；定位不到就标「未定位到，请人工勾」。
- **[ROI]** → scope 从 6 件砍到「草稿生成 + done 提示步」，配得上「降低手工回填摩擦」体量。

## Migration Plan

- 改 `sdflow-done/SKILL.md`（hand-off 步加回填草稿生成 + 提示）+（可选）轻脚本读盘面拼骨架 + `tests/`。**不改 sdflow-roadmap 模板、不迁移存量 roadmap**（现状散文格式即可）。跑 `setup.sh`。
- 关联声明约定若入 workflow 规则 → 改 `sdflow-init/assets/workflow/` 再 update（bundle 纪律）；但轻量、非机械门。
- 回退：叠加提示步，删除即回现状。
- dogfood：本 change 无关联 → 跳过；构造带关联标记的场景验证草稿生成。

## Open Questions

- **草稿生成是脚本还是 done 子代理指令**：机械锚（archive/verify/pytest 数）可脚本读；「组织草稿」含轻判断——倾向轻脚本拼机械骨架 + done 子代理补，或纯 done 指令步（判断留人本就在人确认环节）。
- **关联标记落点**：proposal/tasks 里 `<!-- roadmap: {name} -->` vs done `--roadmap` 参数——倾向前者（change 自身盘面）+ 后者兜底。

## Compliance

- 全局红线：若加脚本 fail-closed + pytest 覆盖坏输入；判断（算不算完成/价值叙述/阶段状态）显式留人。
- 反静默：漏关联可提示（非静默假装无此层）；草稿定位不到标「留人工」。
- 完成判定盘面-判断切分（adr/0015）：助手只搬运盘面、不代人判断。
- bundle 纪律：关联约定若入 workflow 规则改 assets/workflow 再 update；sdflow-done 改后跑 setup.sh。
- 审查顺序：`/review` → push → `/code-review`。
