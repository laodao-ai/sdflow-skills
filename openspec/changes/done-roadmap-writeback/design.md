# Design — done-roadmap-writeback

> 〔spec-review-amendment · adr/0015 + 第三轮精化〕**回填降摩擦助手：机械搬运自动化、判断留人**。机械回写骨架（起手锚 adr/0013 → 编号统一 → 归属镜像+scaffold adr/0014）经两轮 grill + 两轮 spec-review 全被揭穿——**C1**（scaffold 撞 openspec CLI「文件存在=done」短路产出链，源码证实）+ **C2**（阶段 enum deferred 无机器信号，不可机械）。**第三轮 spec-review 再精化切分线**（2 致命 + 3 高收敛于「切分线画错位置」）：**定位到 phase**（change 名前缀 `implement-{roadmap}-pN` 确定性信号 → 机械）、**勾哪几行/算不算完成**（无机械判据 → 判断留人）；时序锚去 archive/merge 预测值（P-1）、格式分形态 fail-loud（P-3）、异步闭环可见（P-4）、detection fence-aware 防自指（P-5）。完整档案见 `adr/0015`（含第三轮精化 P-1..P-5，supersede `adr/0013`+`adr/0014`）。

## Context

`sdflow-done` 收尾六步（接地核验一致）：`0 对账 → 1 verify → 2 hand-off(§2.1 sweep) → 3 archive → 4 commit → 5 merge → 6 摘要`。缺口：全流程对 `openspec/roadmaps/` 零触碰，靠人工回填。

**两轮 spec-review 两致命（否决机械回写）**：
- **C1**：`@fission-ai/openspec` CLI 判 artifact done **只看文件存在**（`artifactOutputExists` 定义于 `dist/core/artifact-graph/outputs.js` = `resolveArtifactOutputs(...).length>0`，`state.js` 仅 import+调用）〔spec-review-amendment · 接地事实修正〕，`apply: requires: [tasks]`。任何在 change 产物文件（tasks/proposal）上抢写的第二 producer（scaffold）会短路 opsx:ff 产出链。判定机制在官方 CLI、本仓改不了。
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

### D-2 定位 = 回填降摩擦助手（草稿 + 人确认，非自动回写）〔spec-review-amendment · 切分线重画 P-1/P-2/P-3/P-4〕

```
change 归档(done · hand-off 步=第二步)
   │  助手读【步2 已实现盘面·事实】: verify=PASS frontmatter + tasks完成态 + change名 + feat分支
   │  【预测/未来锚·非盘面】: archive路径(步3,含{date}) / merge(步5) → 留占位「待归档后人补」, 不预填  ◀ P-1 消 C-1
   ▼
定位关联(机械·确定性信号): change 名前缀 implement-{roadmap}-pN → 解析 roadmap+phase  ◀ P-2 消 C-2/C-14
   │  (兜底: change 内一行 marker `<!-- roadmap: {name}#{phase} -->`; 检测 fence-aware+行锚定  ◀ P-5 消 C-5)
   ▼
探测目标 roadmap 承载形态  ◀ P-3 消 C-3
   ├─ 复选框式(如 mlh `- [ ] 1.A.1`): 定位该 phase 的【候选复选框行集】(借现状格式, 不判勾哪几行)
   └─ 表格/散文式(如 wco `| ✅`): 不产复选框草稿, fail-loud 告知「非复选框格式、复选框回填请人工」
   ▼
生成回填草稿(进 hand-off) + task-log 完成总结骨架(两形态都产, 机械锚: change名/verify结论/archive占位/
   pytest数[经--pytest-count显式传入则填、缺省N/A——verify-report无契约计数字段, 不scrape散文避免第二
   真相源, [impl-review-fix]FIX-4订正旧措辞])
   │
   ▼  阶段三无门 → 不弹窗, 走 hand-off; 且 done 第六步摘要抬一行「⚠ roadmap {name} 回填待确认」使 merge 时点可见  ◀ P-4 消 C-4
人过目草稿: 判断算不算满足验收标准 → 勾哪几行 + 补价值叙述/阶段状态/deferred/里程碑 → 提交(同现状"回填对账"commit)
```

从「纯手写回填」降为「改助手草稿」——机械搬运（敲 change/verify/pytest 数、**定位到阶段的候选行集**）自动化，判断（**勾哪几行**、算不算完成、价值叙述）留人。

### D-3 机械/判断切分（切分线精确落在「有无确定性信号」上）〔spec-review-amendment P-2〕

| 动作 | 性质 | 依据 | 谁做 |
|---|---|---|---|
| 解析 change→roadmap+phase | **机械** | change 名前缀 `implement-{roadmap}-pN`（命名约定确定性编码双粒度）；兜底 marker | 助手 |
| 定位该 phase 的候选复选框**行集** | **机械** | 借现状 `- [ ] {id}` 格式 grep 该 phase 下行 | 助手 |
| 读 change 交付事实（verify=PASS/tasks 完成态/pytest 数/change 名） | **机械** | 步2 已实现盘面 | 助手 |
| 这个 change 勾该 phase 里**哪几行**（phase 跨多 change 时 change→行是判断） | **判断** | 无机械判据 | 人 |
| 算不算满足 `### 验收标准` / 价值叙述 / 阶段状态 / 里程碑 / deferred | **判断** | 语义条件 | 人 |

**关键**：定位到 **phase 级**（有确定性信号 → 机械），勾 **哪几行 / 算不算完成**（无机械判据 → 判断）。助手只产阶段级候选行集，**MUST NOT 产 per-行「建议勾」**（那是判断，会渗回机械侧撞 adr/0015 切分）。

### D-4 触发与时机（阶段三无人类门约束）〔spec-review-amendment P-1/P-4〕

- sdflow-done 收尾（hand-off=第二步）检测 change 关联 roadmap → 回填草稿写进 **hand-off**，提示「检测到关联 roadmap {name}#{phase}，回填草稿见下，请过目后回填」。
- **时序锚清单（P-1 消 C-1）**：草稿机械锚**只含步2 已实现事实**（verify=PASS/tasks 完成态/change 名/分支）；archive 路径(步3)、merge(步5) 此刻**尚不存在**，`盘面即状态` 下不是状态是预测——留占位「待归档后由人补」，**MUST NOT 当确定性盘面预填**（防跨零点日期漂 + merge opt-out 后记一次没发生的 merge）。
- **异步闭环可见（P-4 消 C-4）**：草稿进 hand-off **且** done 第六步摘要抬一行「⚠ roadmap {name} 回填草稿待人确认(见 hand-off)」——使其在 **merge 时点可见**（不只冻结进归档）；经 `/sdflow-ship` 全自动链人被支走时，摘要行是唯一可见信号。design 显式登记残差：**产草稿即止、apply 由人异步、不保证**（MAY 落 todolist 一条，非强制）。
- **阶段三无 AskUserQuestion**：草稿让人异步确认，不弹窗、不阻塞归档/merge。

### D-5 关联（change 名前缀为主·marker 兜底·漏=现状不阻塞）〔spec-review-amendment P-2/P-5·D1 C-6/C-12〕

- **主通道**：change 名前缀 `implement-{roadmap}-pN-*` **确定性解析** roadmap+phase（命名约定已编码、无需人手标 → 消 C-14 采纳 chicken-egg）。
- **兜底通道**：change 内一行 marker `<!-- roadmap: {name}#{phase} -->`（前缀不符命名约定时）；直调 done 可 `--roadmap {name}#{phase}` 覆写。**优先级**：`--roadmap` 参数 > marker > change 名前缀；不一致 → **warn**（反静默）。
- **detection fail-closed（P-5 消 C-5）**：marker 检测 MUST **fence-aware**（跳过 code fence/行内 code）+ **行锚定**（标记独占一行）+ **排除 change 自身讨论区**——防本 change 8 处产物字面含 marker 串致朴素子串检测假阳（MEMORY「gate 子串检测 dogfood 自指坑」同型）。
- **未声明 + 前缀不符 = 退回现状**（人全手工回填），**不 fail-closed 阻塞**（辅助非正确性门）；对「疑似 roadmap 驱动却无信号」→ hand-off 留一行提示（**SHOULD**，反静默升级，C-12），使「无草稿」与「判定无关联」可区分。
- **不 scaffold 机械生成关联**（不碰 opsx:ff，消 C1）。

### D-6 弃什么（消 C1/C2/粒度/H4）

| 弃 | 消除的 spec-review 问题 |
|---|---|
| scaffold 双向预建 | C1（不写 change 产物 → 不撞 openspec done 判定）+ H2 孤儿认领 + H5 早写冲突 |
| 阶段 enum 机械聚合 | C2（deferred 留人写散文，不硬塞机械 enum） |
| 编号统一 / 归属镜像 | 粒度失配（roadmap/tasks 各保现状格式） |
| 强制 roadmap 机读化 / 存量迁移 | H4（roadmap 现状散文即可，助手适配、人读） |
| best-effort 三级机械镜像 | 完成判定含判断（现状实证），机械镜像越界 |

### D-7 组件清单（最小）〔spec-review-amendment 精化〕

1. **关联解析**：change 名前缀 `implement-{roadmap}-pN` 确定性解析（主）+ marker `<!-- roadmap: {name}#{phase} -->` 兜底（fence-aware 检测）+ `--roadmap` 覆写。
2. **回填草稿生成**（定位 phase 候选行集 + 读步2 已实现盘面 → task-log 完成总结骨架含机械锚；archive/merge 留占位）——机械部分可轻脚本辅助（前缀解析/形态探测/grep phase 行/读 verify frontmatter/拼骨架），判断留人。
3. **形态探测**（复选框式 → 定位候选行；表格/散文式 → fail-loud 留人工）。
4. **sdflow-done 收尾提示步**（hand-off 步：检测关联 → 草稿进 hand-off + 提示）+ **第六步摘要抬一行**（回填待确认，merge 时点可见）。

**无** scaffold / enum 聚合 / 编号统一 / 迁移 / 生成侧模板大改。

## Risks / Trade-offs

- **[人仍需确认勾哪几行、非全自动]** → 设计取向（完成判定含判断，现状实证），非缺陷；助手定位到 phase 候选行集、判断本就该人做。
- **[漏声明关联 → 退回现状手工]** → 记录维护非门，可接受；change 名前缀主通道大幅降漏率（命名约定即触发）、疑似驱动 SHOULD 提示、不 fail-closed。
- **[草稿定位不准 / 非复选框格式]** → 草稿给人过目、人会改；复选框式定位不到标「留人工」，表格/散文式 fail-loud 告知（P-3），非机械直写 roadmap。
- **[异步草稿没人 apply（残差·C-4）]** → 已知残差，非全消：第六步摘要抬一行使 merge 时点可见（降概率），但经 ship 全自动链人被支走时仍可能滞留——**显式登记「产草稿即止、不保证 apply」**，MAY 落 todolist；不宣称降摩擦却假装闭环。
- **[ROI]** → scope 从 6 件砍到「关联解析 + 草稿生成 + done 提示步」，配得上「降低手工回填摩擦」体量。

## Migration Plan

- 改 `sdflow-done/SKILL.md`（hand-off 步加回填草稿生成 + 提示）+（可选）轻脚本读盘面拼骨架 + `tests/`。**不改 sdflow-roadmap 模板、不迁移存量 roadmap**（现状散文格式即可）。跑 `setup.sh`。
- 关联声明约定若入 workflow 规则 → 改 `sdflow-init/assets/workflow/` 再 update（bundle 纪律）；但轻量、非机械门。
- 回退：叠加提示步，删除即回现状。
- dogfood：本 change 名非 `implement-*` 前缀、marker 串仅在 code fence/散文内（fence-aware 检测应跳过）→ 应判**无关联跳过**（验证 P-5 防自指）；另构造 `implement-{roadmap}-pN` 命名 fixture 验证前缀解析 + 复选框式/表格式两形态。

## Open Questions〔spec-review-amendment：定位归属/关联落点已解，余一条〕

- **草稿生成是脚本还是 done 子代理指令**：机械部分（前缀解析/形态探测/grep phase 行/读 verify frontmatter）确定性、可脚本；「组织草稿」含轻判断——倾向轻脚本拼机械骨架 + done 指令步补，或纯 done 指令步。**若纯指令步**：坏输入契约（P-3 三分：absent/malformed/verify≠PASS）须写成与载体无关的可判定行为规范 + 场景核对锚（C-9），使指令步路径也有坏输入防线。
- ~~关联标记落点~~ **已解（P-2/D-5）**：change 名前缀 `implement-{roadmap}-pN` 主 + marker `#{phase}` 兜底 + `--roadmap` 覆写。
- ~~定位哪些复选框是机械还是判断~~ **已解（P-2/D-3）**：定位到 phase=机械（前缀确定性信号）、勾哪几行=判断（无机械判据）。

## Compliance

- 全局红线：若加脚本 fail-closed + pytest 覆盖坏输入（三分 absent/malformed/verify≠PASS，C-9）；判断（算不算完成/勾哪几行/价值叙述/阶段状态）显式留人。
- 反静默：漏关联 **SHOULD** 提示（C-12，非静默假装无此层）；草稿定位不到/非复选框格式 fail-loud 标「留人工」（P-3）；双通道不一致 warn。
- 完成判定盘面-判断切分（adr/0015 + 第三轮精化）：助手定位到 phase（机械）、勾哪几行留人（判断）；archive/merge 预测值不当盘面预填（P-1）。
- detection fail-closed（P-5）：marker 检测 fence-aware + 行锚定 + 排除自身讨论区。
- bundle 纪律：关联约定若入 workflow 规则改 assets/workflow 再 update；sdflow-done 改后跑 setup.sh。
- 审查顺序：`/review` → push → `/code-review`。
