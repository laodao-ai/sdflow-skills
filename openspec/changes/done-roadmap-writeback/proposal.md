## Why

sdflow-done 收尾流水线对 **roadmap 文档包零触碰**。roadmap 驱动的分阶段 change 归档后，复选框 / task-log 完成总结 / 里程碑状态全靠**人工手动回填**（本会话刚为 lens-metric-emit=P4/4.C 手动补过一次，commit「回填对账」）。issues 侧早有 `§2.1 sweep`，roadmap 侧是对称缺口。

> 〔spec-review-amendment · adr/0015〕**三轮收敛终局**：机械回写骨架（起手锚 → 编号统一 → 归属镜像+scaffold）经两轮 spec-review 全被揭穿（C1 scaffold 撞 openspec「文件存在=done」短路产出链、C2 阶段 enum 不可机械、defer 回痛点、ROI 失衡）+ 现状实证「完成判定含判断」→ 收敛为**回填降摩擦助手**（机械搬运自动化、判断留人）。

## What Changes

- **回填降摩擦助手**：done 收尾读**确定性盘面**（archive 路径 / verify=PASS frontmatter / merge / tasks 完成态 / 验证数字）生成 roadmap **回填草稿**（候选复选框 + task-log 完成总结骨架含机械锚）写进 hand-off，提示人**异步确认回填**。从「纯手写回填」降为「改助手草稿」。
- **完成判定盘面-判断切分**（现状实证）：change 是否交付=确定性盘面（机械）；是否满足验收标准 / 算不算完成 / 勾哪些=判断（人）。助手只搬运盘面、**判断留人确认**。
- **弃机械回写骨架**：无 scaffold 双向（消 C1：不写 change 产物、不碰 opsx:ff done 判定）/ 无阶段 enum 机械聚合（消 C2：deferred 留人写散文）/ 无编号统一归属镜像（消粒度失配）/ 无强制 roadmap 机读化迁移（现状散文即可）。
- **关联轻量声明，漏=现状**：change 轻量标记 `<!-- roadmap: {name} -->`（或 done `--roadmap`）；未声明退回现状人工回填、**不 fail-closed 阻塞**（辅助非门）。
- **阶段三无门**：草稿走 hand-off 异步确认、不弹窗、不阻塞归档/merge。issues 不动。**无 BREAKING**。

## Capabilities

### New Capabilities
（无。）

### Modified Capabilities
- `spec-workflow`: 新增两 Requirement——① roadmap 回填降摩擦助手（done 收尾读盘面生成草稿进 hand-off、判断留人、不机械镜像）② roadmap 关联声明轻量、漏则退现状不阻塞。与 `§2.1 sweep`（issues 自动 triage）为对称收尾契约——但回填是**助人确认**（完成判定含判断），非无人干预。

## Impact

- **改**：`sdflow-done/SKILL.md`（hand-off 步加回填草稿生成 + 提示）+（可选）轻脚本读盘面拼骨架 → `scripts/`+`tests/`。
- **不改**：`sdflow-roadmap`（模板/生成侧不动）、**不迁移存量 roadmap**（现状散文格式即可）、不改 opsx:ff。
- 关联声明约定若入 workflow 规则 → 改 `sdflow-init/assets/workflow/` 再 update（bundle 纪律）；轻量非门。
- 外部影响方：sdflow-done 经 symlink 铺所有消费仓；无关联/无 roadmap 仓零差异（草稿不生成）。

## Success Metrics

- roadmap 驱动 change 归档后，hand-off 含回填草稿（候选复选框 + task-log 骨架含机械锚）——人过目补判断即可回填，省手敲 change/merge/archive/验证数字 + 定位复选框行。
- 无关联 change / 无 roadmap 仓：done 行为零差异（不生成草稿）。
- 判断（算不算完成/价值叙述/阶段状态/deferred）由人确认——助手不代判、不无人干预改 roadmap。
- 若加脚本：坏输入（盘面缺失/定位不到）→ fail-closed 非零退出或标「留人工」，pytest 覆盖。

## Non-Goals

- 不碰 issues 回写（§2.1 sweep）。不做 4.D.4 Review 对账。不改 opsx:ff。
- **不 scaffold 双向 / 不 enum 机械聚合 / 不编号统一归属镜像 / 不强制 roadmap 机读化迁移**（弃机械回写骨架，消 C1/C2/粒度失配/H4）。
- 不做无人干预自动回写（完成判定含判断，助手只搬运盘面、判断留人）。

## Compliance

- 全局红线：若加脚本 fail-closed + pytest 覆盖坏输入；判断（算不算完成/价值叙述/阶段状态）显式留人。
- 反静默：漏关联可提示（非静默假装无此层）；草稿定位不到标「留人工」。
- bundle 纪律：关联约定若入 workflow 规则改 assets/workflow 再 update；sdflow-done 改后跑 setup.sh。
- 审查顺序：`/review` → push → `/code-review`。

## 需求优先级（TG-19）

- **P0** · 回填草稿生成（读确定性盘面 → 候选复选框 + task-log 骨架含机械锚）。
- **P0** · sdflow-done 收尾提示步（检测关联 → 草稿进 hand-off、不阻塞）。
- **P1** · 关联声明轻量约定 + 漏则退现状不阻塞。
- **P2** · 未声明但疑似 roadmap 驱动的轻量提示。

## 利益相关方与外部依赖（TG-20）

- **所有 sdflow-skills 消费仓**：sdflow-done 经 symlink 铺设；无关联/无 roadmap 仓零差异。
- **不改 opsx:ff（官方）**：助手只读盘面 + 写 hand-off 草稿，不碰 change 产物文件（避 C1）。
- **/sdflow-ship 链**：done 是链末端；草稿走 hand-off 异步、不破坏 merge 缺省语义。

## 假设（TG-22）

- **假设 1** · change 归档时确定性盘面（archive 路径 / verify=PASS frontmatter / tasks 完成态）可读（done 第 0.3/1 步已产生）。**失效**：盘面缺 → 草稿标「盘面缺失、留人工」，不伪造。
- **假设 2** · 完成判定含判断（现状实证：人对照验收标准判），故助手生成草稿、人确认——**非无人干预**。**失效面**：若强求全自动 → 撞 C2（把判断当机械），本设计明确不做。
- **假设 3** · roadmap 现状散文格式够人读 + 助手草稿定位复选框（借现有 `- [ ] {id}` 格式）。**失效**：定位不到 → 标「留人工」，不猜写。
