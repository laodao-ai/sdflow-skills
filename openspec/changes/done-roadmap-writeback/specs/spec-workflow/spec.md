## ADDED Requirements

<!-- 〔spec-review-amendment · adr/0014〕编号统一投影链：真相源=归档tasks盘面, producer机械生成 -->

### Requirement: roadmap 编号统一与关联判据

roadmap 驱动 change 的 tasks.md 顶层组 SHALL 采用 roadmap 子任务号（`## 4.D.1`，与 roadmap 复选框同号）；`sdflow-done` 回写的关联判据 SHALL 为 L1 读 tasks 的 `<!-- roadmap: {name} -->` 锚（关联哪个 roadmap）+ L2 扫 tasks 顶层组完成态（哪些子任务、完成没），MUST NOT 靠起手锚固化的 subtask 集当勾选真相（起手 ≠ 归档实况、会致 defer 误勾）。tasks 顶层用 roadmap 式编号 `N.X.Y` 却无 `roadmap: {name}` 锚 MUST 由 lint fail-closed 拦、MUST NOT 静默跳过（编号形态是「roadmap 驱动 change」的机械可判信号）。

#### Scenario: 真相源为归档 tasks 完成态盘面
- **WHEN** 回写判定某 roadmap 子任务是否勾选
- **THEN** 依据 change tasks.md 同号顶层组的复选框完成态（组内全 `[x]`→勾），MUST NOT 依据起手锚声明的 subtask 集

#### Scenario: 漏 name 锚 fail-closed 非静默
- **WHEN** tasks.md 顶层组用 roadmap 式编号 `N.X.Y` 但无 `<!-- roadmap: {name} -->` 锚
- **THEN** lint（起手）或 done（归档）MUST fail-closed 提示留人工，MUST NOT 当「无关联」静默跳过

#### Scenario: 真无关联静默跳过
- **WHEN** tasks.md 无 roadmap 式编号且无 name 锚（普通非 roadmap 驱动 change）
- **THEN** 回写静默跳过，行为与现状零差异

### Requirement: sdflow-done 镜像回写关联 roadmap

`sdflow-done` SHALL 在 archive 之后、commit 之前**镜像**回写：扫 tasks 顶层 `## N.X.Y` 组完成态 → 勾 roadmap 同号复选框（组全 `[x]`→勾、有 `[ ]`→不勾）+ 机械聚合阶段状态 enum + 追加 task-log 完成总结 + 按需更新里程碑句；产物随第四步 `git add openspec/` 提交。勾选 / 阶段 enum = 脚本机械（勾选行首锚定 `^- \[ \] {id}`）；完成总结叙述 / 里程碑句 = 模型写、脚本校验机器锚。回写 MUST NOT 阻塞 archive/merge；镜像不上（roadmap 改号）MUST 降级标注落 task-log、MUST NOT 静默。

#### Scenario: 组全完成镜像勾选
- **WHEN** tasks 组 `## 4.D.1` 内复选框全 `[x]`
- **THEN** 勾 roadmap `4.D.1` 复选框（行首锚定，不误命中散文层 id 提及）

#### Scenario: defer 组不误勾
- **WHEN** tasks 组 `## 4.D.4` 内有 `[ ]`（实现期 defer）
- **THEN** roadmap `4.D.4` 复选框保持 `[ ]` 不勾，堵住起手声明 ≠ 实际交付的误勾

#### Scenario: 阶段状态 enum 机械聚合
- **WHEN** 更新阶段状态列
- **THEN** 脚本从该阶段全子任务复选框机械聚合（无完成=planned / 部分=in-progress / 全非deferred完成=delivered / 显式放弃=deferred），MUST NOT 靠模型判断

#### Scenario: 镜像不匹配降级标注
- **WHEN** name 锚有效但 tasks 组号在 roadmap 找不到同号复选框（roadmap 改号）
- **THEN** 降级标注「未能镜像：{subtask}」落 task-log（持久、随归档 commit），archive/merge 继续，MUST NOT 静默、MUST NOT 只落 stdout 摘要

#### Scenario: 完成总结机械/判断切分
- **WHEN** 写 task-log 完成总结（每 `(change,subtask)` 一条机器锚）
- **THEN** 叙述内容由模型写、脚本只校验机器锚在场且幂等；里程碑散文句由模型判断改（仅阶段状态跨阈值时），脚本不碰

### Requirement: roadmap 生成侧结构化与 change scaffold

`sdflow-roadmap` 生成的 roadmap SHALL 结构化索引层：子任务为带稳定号的复选框 + 交付标注槽、概览表含阶段 `状态` enum 列（`planned/in-progress/delivered/deferred`，值集纳入单一机读契约）、task-log 条目含机器锚行；叙述层（目标/理由/完成总结叙述/里程碑句）保留散文。`sdflow-roadmap` SHALL 提供 **change scaffold**（从 roadmap 指定子任务机械生成 change tasks.md 骨架：顶层组编号抄自 roadmap + `<!-- roadmap: {name} -->` 锚 + proposal 引用，不靠人写对）。存量 roadmap 一次性迁移新格式，MUST NOT 维护 dual-read。

#### Scenario: scaffold 机械生成 tasks 骨架
- **WHEN** 起 roadmap 驱动 change，指定 roadmap 子任务 `4.D.1,4.D.2`
- **THEN** scaffold 生成 tasks.md 顶层组 `## 4.D.1`/`## 4.D.2`（号抄自 roadmap）+ `<!-- roadmap: {name} -->` 锚 + proposal 引用，编号与锚均机械产出、非人手写

#### Scenario: 概览表阶段状态 enum 列
- **WHEN** 生成/迁移 roadmap 概览表
- **THEN** 每阶段行含 `状态` 列、取值 ∈ 契约单一源 enum 集，回写脚本可机械更新

#### Scenario: 旧 roadmap 迁移不 dual-read
- **WHEN** 存量 roadmap（旧散文格式）纳入回写
- **THEN** 一次性迁移到新索引层格式（概览表加 enum 列、不可映射的散文值如「端态A已定」显式补 enum 或标 legacy），回写只认新格式、MUST NOT 维护 dual-read
