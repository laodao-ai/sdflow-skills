## ADDED Requirements

<!-- 〔spec-review-amendment · adr/0015 + 第三轮精化 P-1..P-5〕最小核: 回填降摩擦助手, 机械搬运(定位到 phase)自动化、判断(勾哪几行/算不算完成)留人 -->

### Requirement: roadmap 回填降摩擦助手（定位到 phase 机械、勾哪几行判断留人）

`sdflow-done` 收尾（hand-off 那步，即第二步）SHALL 在检测到 change 关联某 roadmap 时，读**步2 已实现的确定性盘面**（`verify=PASS` frontmatter / tasks 完成态 / change 名 / feat 分支）生成 roadmap **回填草稿**（该 phase 的候选复选框行集 + task-log 完成总结骨架含机械锚）写进 `hand-off.md`，并提示人异步确认回填。

回填是**记录维护且完成判定含判断**（现状实证：人对照 `### 验收标准` 判），切分线精确落在「有无确定性信号」上：

- 助手 MUST 只自动化**有确定性信号的机械动作**：① 从 change 名前缀 `implement-{roadmap}-pN` 解析 roadmap+phase（兜底 marker，见下一 Requirement）；② 定位该 **phase** 的候选复选框**行集**（借现状 `- [ ] {id}` 格式）；③ 读步2 已实现盘面事实。
- 助手 MUST 把**无机械判据的动作留人确认**：这个 change 勾该 phase 里**哪几行**（phase 跨多 change 时 change→行是判断）/ 算不算满足 `### 验收标准` / 完成总结价值叙述 / 阶段状态 / 里程碑 / deferred。
- 助手 MUST NOT 产 per-行「建议勾」（那是判断，会渗回机械侧撞 adr/0015 切分）——只产**阶段级候选行集**供人挑。
- 助手 MUST NOT 无人干预直接机械改 roadmap；MUST NOT scaffold 预建 roadmap 复选框 / 写 change 产物文件（避开 openspec「文件存在=done」短路，C1）；MUST NOT 从二值复选框机械聚合阶段状态 enum / 推 deferred（C2，判断留人写散文）。

**时序锚清单（P-1）**：草稿机械锚 MUST 只含步2 **已实现事实**（verify=PASS / tasks 完成态 / change 名 / 分支 / pytest 数[有测试则从 verify-report 取、无则标 N/A]）。archive 路径（第三步，含 `{date}`）与 merge（第五步）在草稿生成时**尚不存在**，MUST 留占位「待归档后由人补」，MUST NOT 当确定性盘面预填（防跨零点日期漂移 + merge opt-out 后记一次未发生的 merge）。

**阶段三无 AskUserQuestion**——草稿走 hand-off 异步确认，MUST NOT 弹窗、MUST NOT 阻塞归档/merge。

#### Scenario: 复选框式 roadmap 关联时生成回填草稿进 hand-off
- **WHEN** change 经名前缀/marker 解析出 roadmap+phase，且目标 roadmap 为复选框式（`- [ ] {id}`）
- **THEN** 助手定位该 phase 的候选复选框行集 + 读步2 已实现盘面生成 task-log 完成总结骨架（含 change/verify 结论/pytest 数机械锚、archive/merge 留占位）写进 hand-off，提示人过目后判断勾哪几行 + 补判断项

#### Scenario: 定位到 phase 机械、勾哪几行判断留人
- **WHEN** 生成回填草稿
- **THEN** 助手机械定位到 phase 级候选行集（前缀确定性信号），MUST NOT 代判「这个 change 勾哪几行 / 算不算满足验收标准 / 阶段状态 / deferred」——这些由人在确认环节判定

#### Scenario: 时序——archive/merge 留占位不预填
- **WHEN** 草稿在 hand-off（第二步）生成，archive（第三步）与 merge（第五步）尚未发生
- **THEN** 草稿机械锚只填步2 已实现事实（verify/tasks/change 名/分支/pytest 数）；archive 路径与 merge 状态留占位「待归档后由人补」，MUST NOT 预填预测值

#### Scenario: 非复选框格式 fail-loud 留人工（形态分治 P-3）
- **WHEN** 目标 roadmap 为表格/散文式（无 `- [ ]` 复选框，如 `| ✅` 概览表 + 状态散文）
- **THEN** 助手 MUST NOT 产复选框草稿，MUST fail-loud 在 hand-off 告知「roadmap {name} 为非复选框格式、复选框回填请人工」（反静默，非静默退现状）；task-log 完成总结骨架仍产

#### Scenario: 不碰 change 产物文件（避 C1）
- **WHEN** 助手运行
- **THEN** MUST NOT 写 change 的 tasks.md/proposal.md 等产物文件（避免第二 producer 触发 openspec「文件存在=done」短路 opsx:ff 产出链）；只读盘面 + 写 hand-off 草稿

#### Scenario: 阶段三无门、异步闭环可见（P-4）
- **WHEN** 回填草稿生成
- **THEN** 草稿进 hand-off 供人异步确认，done 流程继续（不弹窗、不阻塞归档/merge）；**且** done 第六步摘要抬一行「⚠ roadmap {name} 回填草稿待人确认（见 hand-off）」使其在 merge 时点可见（不只冻结进归档）；design 显式登记「产草稿即止、apply 由人异步、不保证」残差

### Requirement: roadmap 关联解析（change 名前缀为主、marker 兜底、fence-aware、漏则退现状）

change 与 roadmap 的关联 SHALL 优先由 **change 名前缀 `implement-{roadmap}-pN-*` 确定性解析**（命名约定已编码 roadmap+phase 双粒度，无需人手标记）；前缀不符命名约定时用兜底标记（`proposal.md`/`tasks.md` 中独占一行 `<!-- roadmap: {name}#{phase} -->`），或调用 done 时 `--roadmap {name}#{phase}` 覆写。优先级 SHALL 为 `--roadmap` > marker > 名前缀；多通道值不一致 MUST warn（反静默）。

marker 检测 MUST **fence-aware**（跳过 code fence/行内 code）+ **行锚定**（标记独占一行、非嵌散文/引用）+ **排除 change 自身讨论区**——防 change 产物字面含 marker 串致朴素子串检测假阳（`done-roadmap-writeback` 自身即 8 处含该串，MEMORY「gate 子串检测 dogfood 自指坑」同型）。

未声明关联且名前缀不符 MUST 退回现状（人全手工回填）、MUST NOT fail-closed 阻塞归档（回填助手是辅助、非正确性门）；对「未声明但疑似 roadmap 驱动」（如分支名/change 名近似 roadmap 目录名）**SHOULD** 在 hand-off 留一行提示，使「无草稿」与「助手判定无关联」可区分（反静默 C-12）。

#### Scenario: change 名前缀确定性解析（主通道）
- **WHEN** change 名匹配 `implement-{roadmap}-pN-*`
- **THEN** 助手确定性解析出 roadmap+phase 触发草稿生成，无需人手标记（消采纳 chicken-egg）

#### Scenario: marker 兜底 + fence-aware 防自指
- **WHEN** change 名不符前缀约定，但 `proposal.md`/`tasks.md` 有独占一行的 `<!-- roadmap: {name}#{phase} -->`（非 code fence/散文内）
- **THEN** 助手据此定位；若 marker 串仅出现在 code fence/行内 code/散文引用中（如本 change 讨论自身），fence-aware 检测 MUST 跳过、判无关联

#### Scenario: 双通道不一致 warn
- **WHEN** `--roadmap`、marker、名前缀解析出的 roadmap/phase 不一致
- **THEN** 按 `--roadmap` > marker > 名前缀取值并 warn（反静默，不静默取默认）

#### Scenario: 未声明退回现状不阻塞
- **WHEN** change 无关联声明且名前缀不符（普通 change 或漏标）
- **THEN** 回填草稿不生成、done 行为与现状零差异；MUST NOT fail-closed 阻塞；对疑似 roadmap 驱动 SHOULD 留一行提示
