## ADDED Requirements

<!-- 〔grill-amendment · adr/0013〕关联锚契约 + best-effort 回写 + 生成侧索引层结构化 -->

### Requirement: roadmap 关联锚契约

roadmap 驱动的 change SHALL 在起手时于 `proposal.md` 写一行机器关联锚 `<!-- roadmap: {name} phase: {PN} subtask: {id,...} -->`；`sdflow-done` 回写步 MUST 以该锚（grep `{name}` 定位 `openspec/roadmaps/{name}/`、读 `{subtask}` 逗号列表定位子任务）作关联判据的**确定性单一源**，MUST NOT 解析 proposal 自然语言引用推断关联（措辞属概率空间）。无锚 MUST 按无关联静默跳过（producer 违约 fail-safe）。

#### Scenario: 有锚时读锚字段定位
- **WHEN** change proposal 含关联锚且 `name` 对应 `openspec/roadmaps/{name}/` 存在
- **THEN** 回写步读锚 `name` 定位 roadmap、读 `subtask` 列表定位子任务，MUST NOT 解析 proposal 自然语言引用

#### Scenario: 无锚静默跳过
- **WHEN** change proposal 不含关联锚（普通非 roadmap 驱动 change）
- **THEN** 回写步按无关联静默跳过，行为与现状零差异、不告警

#### Scenario: 起手写锚有确定性手段
- **WHEN** roadmap 驱动 change 起手需写关联锚
- **THEN** 提供确定性写锚手段（`roadmap-link` 脚本机械拼锚 / 起手规范），锚格式机读、幂等、格式非法 fail-closed

### Requirement: sdflow-done 归档回写关联 roadmap（best-effort 记录维护）

`sdflow-done` SHALL 在 archive 之后、Git Commit 之前新增回写步：勾对应子任务复选框、更新阶段状态 enum、追加 `task-log.md` 完成总结、按需更新里程碑；回写产物 MUST 随第四步 `git add openspec/` 一并提交、MUST NOT 引入 merge 后额外提交。回写是**记录维护非正确性门**，MUST 按 best-effort 三级：全定位成功→全回写；部分定位成功→回写能做的 + 降级标注未做项；完全无法解析格式→fail-closed 留人工。回写 MUST NOT 阻塞 archive/merge，但未做项 MUST NOT 静默（写入 hand-off + 最终摘要）。勾选 / 阶段状态 = 脚本机械写；完成总结叙述 / 里程碑句 = 模型写、脚本只校验机器锚在场。

#### Scenario: 全定位成功全回写
- **WHEN** 锚 `subtask` 全部在 roadmap 定位到复选框行
- **THEN** 勾全部子任务、更新阶段状态 enum cell、追加 task-log 完成总结（含机器锚，用 change 名 + archive 路径追溯、**不写 merge hash**）、按需更新里程碑，随归档提交

#### Scenario: 部分定位 best-effort 加降级标注
- **WHEN** 锚 `subtask` 有部分在 roadmap 定位不到
- **THEN** 回写能定位的子任务，未定位项在 task-log/最终摘要显式降级标注「未能自动回写：{subtask}」；MUST NOT 因部分失败整体不写、MUST NOT 静默、MUST NOT 阻塞归档/merge

#### Scenario: 完全无法解析 fail-closed
- **WHEN** 关联 roadmap 索引层结构缺失/损坏、完全无法解析
- **THEN** 回写 fail-closed 不写任何内容、显著提示留人工，archive/merge 继续执行

#### Scenario: 完成总结机械/判断切分
- **WHEN** 写 task-log 完成总结
- **THEN** 叙述内容由模型写、脚本只校验机器锚（change/subtask/archive/status）在场且幂等，MUST NOT 由脚本产叙述内容；里程碑散文句由模型判断改、脚本不碰

### Requirement: roadmap 生成索引层结构化

`sdflow-roadmap` 生成的 roadmap SHALL 分**索引层**（机器消费）与**叙述层**（人读）：概览表 MUST 含阶段 `状态` enum 列（`planned`/`in-progress`/`delivered`/`deferred`）、子任务 MUST 为带稳定 id 的复选框 + 固定交付标注槽、task-log 条目 MUST 含机器锚行；叙述层（目标/设计理由/完成总结叙述/里程碑句）MUST 保留散文、MUST NOT 全 frontmatter 化。存量 roadmap MUST 一次性迁移到新格式，回写只认新格式、MUST NOT 维护 dual-read。

#### Scenario: 概览表阶段状态 enum
- **WHEN** 生成 roadmap 概览表
- **THEN** 每阶段行含 `状态` 列、取值 ∈ {planned,in-progress,delivered,deferred}，回写脚本可机械更新该 cell

#### Scenario: task-log 机器锚幂等
- **WHEN** 回写向 task-log 追加完成总结
- **THEN** 条目含机器锚行 `<!-- roadmap-writeback: change=… subtask=… archive=… status=… -->`；重跑认锚幂等、不重复追加

#### Scenario: 旧 roadmap 迁移不 dual-read
- **WHEN** 存量 roadmap（旧散文格式）纳入回写
- **THEN** 一次性迁移到新索引层格式（无损、内容不丢），回写只认新格式，MUST NOT 维护新旧 dual-read
