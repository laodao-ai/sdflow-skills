## ADDED Requirements

<!-- 〔spec-review-amendment · adr/0015〕最小核: 回填降摩擦助手, 机械搬运自动化、判断留人 -->

### Requirement: roadmap 回填降摩擦助手（判断留人）

`sdflow-done` 收尾（hand-off 那步）SHALL 在检测到 change 关联某 roadmap 时，读**确定性盘面**（archive 路径 / verify=PASS frontmatter / merge / tasks 完成态 / 验证数字）生成 roadmap **回填草稿**（候选复选框 + task-log 完成总结骨架含机械锚）写进 `hand-off.md`，并提示人异步确认回填。回填是**记录维护且完成判定含判断**（现状实证：人对照 `### 验收标准` 判），故助手 MUST 只自动化**机械搬运**（盘面读取 + 骨架预填），**判断留人确认**（算不算满足验收标准 / 勾哪些复选框 / 完成总结价值叙述 / 阶段状态 / deferred）。助手 MUST NOT 无人干预直接机械改 roadmap；MUST NOT scaffold 预建 roadmap 复选框 / 写 change 产物文件（避开 openspec「文件存在=done」短路，C1）；MUST NOT 从二值复选框机械聚合阶段状态 enum / 推 deferred（C2，判断留人写散文）。阶段三无 AskUserQuestion——草稿走 hand-off 异步确认，MUST NOT 弹窗、MUST NOT 阻塞归档/merge。

#### Scenario: 关联时生成回填草稿进 hand-off
- **WHEN** change 声明关联某 roadmap 且已归档（archive 路径 + verify=PASS 盘面可读）
- **THEN** 助手读盘面生成回填草稿（候选复选框 + task-log 完成总结骨架含 change/merge/archive/验证数字机械锚）写进 hand-off，提示人过目后回填

#### Scenario: 判断留人、助手不代判
- **WHEN** 生成回填草稿
- **THEN** 助手 MUST NOT 直接机械改 roadmap 复选框 / 不机械聚合阶段状态 enum / 不推 deferred；「算不算满足验收标准、勾哪些、价值叙述、阶段状态、deferred」由人在确认环节判定

#### Scenario: 不碰 change 产物文件（避 C1）
- **WHEN** 助手运行
- **THEN** MUST NOT 写 change 的 tasks.md/proposal.md 等产物文件（避免第二 producer 触发 openspec「文件存在=done」短路 opsx:ff 产出链）；只读盘面 + 写 hand-off 草稿

#### Scenario: 阶段三无门、不阻塞
- **WHEN** 回填草稿生成
- **THEN** 草稿进 hand-off 供人异步确认，done 流程继续（不弹窗、不阻塞归档/merge）

### Requirement: roadmap 关联声明轻量、漏则退现状

change 声明关联 roadmap SHALL 用轻量标记（`proposal.md`/`tasks.md` 中一行 `<!-- roadmap: {name} -->`，或调用 done 时指定 `--roadmap {name}`）；`sdflow-done` 检测到则生成回填草稿。未声明关联 MUST 退回现状（人全手工回填）、MUST NOT fail-closed 阻塞归档（回填助手是辅助、非正确性门）；MAY 对「未声明但疑似 roadmap 驱动」轻量提示，MUST NOT 强制。

#### Scenario: 轻量声明触发草稿
- **WHEN** change 含 `<!-- roadmap: {name} -->` 标记或 done 传 `--roadmap`
- **THEN** 助手据此定位 roadmap 生成回填草稿

#### Scenario: 未声明退回现状不阻塞
- **WHEN** change 无关联声明（普通 change 或漏标）
- **THEN** 回填草稿不生成、done 行为与现状零差异；MUST NOT fail-closed 阻塞（可 MAY 轻量提示疑似关联）
