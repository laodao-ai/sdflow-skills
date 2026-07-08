## Why

sdflow-done 收尾流水线对 **roadmap 文档包零触碰**。roadmap 驱动的分阶段 change 归档后，复选框 / task-log 完成总结 / 里程碑状态全靠**人工手动回填**（本会话刚为 lens-metric-emit=P4/4.C 手动补过一次，commit「回填对账」）。issues 侧早有 `§2.1 sweep`，roadmap 侧是对称缺口。

> 〔spec-review-amendment · adr/0015〕**三轮收敛终局**：机械回写骨架（起手锚 → 编号统一 → 归属镜像+scaffold）经两轮 spec-review 全被揭穿（C1 scaffold 撞 openspec「文件存在=done」短路产出链、C2 阶段 enum 不可机械、defer 回痛点、ROI 失衡）+ 现状实证「完成判定含判断」→ 收敛为**回填降摩擦助手**（机械搬运自动化、判断留人）。

## What Changes

- **回填降摩擦助手**：done 收尾（hand-off 步）读**步2 已实现盘面**（verify=PASS frontmatter / tasks 完成态 / change 名 / 分支 / pytest 数[有则取]）生成 roadmap **回填草稿**（该 phase 候选复选框行集 + task-log 完成总结骨架含机械锚，archive/merge 留占位）写进 hand-off，提示人**异步确认回填**。从「纯手写回填」降为「改助手草稿」。
- **切分线：定位到 phase 机械、勾哪几行判断**〔第三轮精化〕：解析 change→roadmap+phase（**change 名前缀 `implement-{roadmap}-pN` 确定性信号**）+ 定位该 phase 候选行集=机械；这个 change 勾**哪几行** / 算不算满足验收标准 / 价值叙述 / 阶段状态 / deferred=判断留人。助手只产阶段级候选行集，**MUST NOT 产 per-行建议勾**。
- **时序锚收窄**（消 C-1）：archive 路径(步3,含日期)/merge(步5) 在草稿生成(步2)时**尚不存在**，留占位「待归档后人补」，MUST NOT 当盘面预填（防日期漂 + 记未发生的 merge）。
- **格式分形态 fail-loud**（消 C-3）：两存量 roadmap 格式实测分裂（mlh 复选框式 / wco 表格式）；复选框式→定位候选行，表格/散文式→**fail-loud 告知人工**（非静默退现状）。
- **弃机械回写骨架**：无 scaffold 双向（消 C1）/ 无阶段 enum 机械聚合（消 C2）/ 无编号统一归属镜像（消粒度失配）/ 无强制 roadmap 机读化迁移（现状散文即可）。
- **关联 change 名前缀为主、marker 兜底、fence-aware**（消 C-5 自指 + C-14 chicken-egg）：前缀解析为主（无需人手标）+ marker `<!-- roadmap: {name}#{phase} -->` 兜底（检测 fence-aware+行锚定+排除自身讨论区）+ `--roadmap` 覆写；未声明退现状**不 fail-closed 阻塞**，疑似驱动 SHOULD 提示。
- **异步闭环可见**（消 C-4）：草稿进 hand-off **且** done 第六步摘要抬一行「回填待确认」使 merge 时点可见；显式登记「产草稿即止、不保证 apply」残差。
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

- roadmap 驱动 change（`implement-{roadmap}-pN` 命名）归档后，hand-off 含回填草稿（该 phase 候选行集 + task-log 骨架含机械锚）+ 第六步摘要抬一行——人过目补判断即可回填，省手敲 change/verify/pytest 数 + 定位到 phase 的候选行集。
- 无关联 change / 无 roadmap 仓 / marker 仅在 fence 内：done 行为零差异（不生成草稿，fence-aware 不误检测）。
- 判断（勾哪几行/算不算完成/价值叙述/阶段状态/deferred）由人确认——助手定位到 phase（机械）、不代判勾哪几行、不无人干预改 roadmap。
- 若加脚本：坏输入**三分**（absent 留人工 / malformed fail-closed 标畸形 / verify≠PASS 不出完成候选）→ 非零退出或标「留人工」，pytest 覆盖（含 fence 内不误检测）。

## Non-Goals

- 不碰 issues 回写（§2.1 sweep）。不做 4.D.4 Review 对账。不改 opsx:ff。
- **不 scaffold 双向 / 不 enum 机械聚合 / 不编号统一归属镜像 / 不强制 roadmap 机读化迁移**（弃机械回写骨架，消 C1/C2/粒度失配/H4）。
- 不做无人干预自动回写（完成判定含判断，助手只搬运盘面、判断留人）。

## Compliance

- 全局红线：若加脚本 fail-closed + pytest 覆盖坏输入**三分**（absent/malformed/verify≠PASS，C-9）；判断（算不算完成/勾哪几行/价值叙述/阶段状态）显式留人。
- 反静默：漏关联 **SHOULD** 提示（C-12，非静默假装无此层）；草稿定位不到/非复选框格式 fail-loud 标「留人工」；双通道不一致 warn。
- detection fail-closed（C-5）：marker 检测 fence-aware + 行锚定 + 排除 change 自身讨论区（防自指假阳）。
- 盘面即状态（C-1）：archive/merge 预测值不当盘面预填，留占位待人补。
- bundle 纪律：关联约定若入 workflow 规则改 assets/workflow 再 update；sdflow-done 改后跑 setup.sh。
- 审查顺序：`/review` → push → `/code-review`。

## 需求优先级（TG-19）

- **P0** · 关联解析（change 名前缀 `implement-{roadmap}-pN` 主 + marker 兜底 fence-aware）+ 回填草稿生成（定位 phase 候选行集 + task-log 骨架含机械锚，archive/merge 占位）。
- **P0** · sdflow-done 收尾提示步（检测关联 → 草稿进 hand-off、第六步摘要抬一行、不阻塞）。
- **P1** · 格式分形态 fail-loud + 漏则退现状不阻塞 + 双通道优先级/warn。
- **P2** · 未声明但疑似 roadmap 驱动的轻量提示（SHOULD）。

## 利益相关方与外部依赖（TG-20）

- **所有 sdflow-skills 消费仓**：sdflow-done 经 symlink 铺设；无关联/无 roadmap 仓零差异。
- **不改 opsx:ff（官方）**：助手只读盘面 + 写 hand-off 草稿，不碰 change 产物文件（避 C1）。
- **/sdflow-ship 链**：done 是链末端；草稿走 hand-off 异步、不破坏 merge 缺省语义；ship 全自动链下第六步摘要行是回填可见的唯一信号（C-4 残差登记）。`--roadmap` 经 ship 不透传（仅 in-file 前缀/marker 通道存活），故前缀/marker 为主。

## 假设（TG-22）

- **假设 1（时序精化）** · 草稿在 hand-off（步2）生成时，**只有** verify=PASS frontmatter（步1）/ tasks 完成态（步0.3）/ change 名 / 分支可读；archive 路径（步3）/ merge（步5）**尚不存在**——留占位不预填（P-1）。**失效**：步2 盘面缺 → 草稿标「盘面缺失、留人工」，不伪造。
- **假设 2** · 完成判定含判断（现状实证：人对照验收标准判），故助手定位到 phase（机械）、生成草稿、人确认勾哪几行——**非无人干预**。**失效面**：若强求全自动定位到行 → 撞 C2/判断渗机械侧，本设计明确不做。
- **假设 3（格式分裂已实证）** · 存量 roadmap 格式**不统一**（mlh 复选框式 grep 54 / wco 表格式 grep 0）——助手 MUST 探测形态：复选框式借 `- [ ] {id}` 定位、表格/散文式 **fail-loud 留人工**（P-3），不假设统一格式、不静默退现状。
- **假设 4（关联信号）** · roadmap 驱动 change 遵 `implement-{roadmap}-pN-*` 命名（确定性编码 roadmap+phase）。**失效**：命名不符 → marker 兜底；均无 → 退现状 + 疑似驱动 SHOULD 提示。
