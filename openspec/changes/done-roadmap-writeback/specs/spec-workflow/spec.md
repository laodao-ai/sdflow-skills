## ADDED Requirements

<!-- 〔spec-review-amendment · adr/0014 + grill-amendment 第二轮〕归属镜像投影：roadmap 保规划粒度借格式, change 归属, 盘面镜像 -->

### Requirement: roadmap 归属镜像与关联判据

roadmap SHALL 保规划粒度（子任务 = 一次 change / 一个交付点）、**仅借鉴** tasks 的复选框 `- [ ]` + 层级编码 `N.X.Y` 格式使其机械可镜像，MUST NOT 下沉到 openspec tasks 实现步粒度。roadmap 驱动 change SHALL 通过归属锚 `<!-- roadmap: {name} subtasks: … -->` 声明归属的 roadmap 子任务（关联范围）+ tasks 顶层组借 roadmap 子任务号作归属标签。`sdflow-done` 关联判据 = L1 读 name 锚（关联哪个 roadmap）+ L2 锚 `subtasks`（归属范围）∩ tasks 归属组盘面完成态（哪些真做了），MUST NOT 靠起手锚当**完成**真相（锚只声明范围、完成看盘面）。tasks 顶层用 roadmap 式编号 `N.X.Y` 却无 name 锚 MUST lint fail-closed 拦、MUST NOT 静默跳过。

#### Scenario: 真相源为归档 tasks 完成态盘面
- **WHEN** 回写判定某 roadmap 子任务是否勾选
- **THEN** 依据 change tasks 归属组的复选框完成态（组全 `[x]`→勾），锚 `subtasks` 仅界定关联范围，MUST NOT 用锚声明当完成真相

#### Scenario: 实际勾选 = 归属范围 ∩ 盘面完成
- **WHEN** 归属锚声明 `subtasks: 4.D.1,4.D.2,4.D.4` 但 tasks 组 `## 4.D.4` 有 `[ ]`（defer）
- **THEN** 勾 roadmap `4.D.1`/`4.D.2`、`4.D.4` 保持 `[ ]`（范围内但盘面未完成），堵起手声明 ≠ 实际交付的误勾

#### Scenario: 漏 name 锚 fail-closed 非静默
- **WHEN** tasks 顶层组用 roadmap 式编号 `N.X.Y` 但无 `<!-- roadmap: {name} … -->` 锚
- **THEN** lint（起手）或 done（归档）MUST fail-closed 提示留人工，MUST NOT 当「无关联」静默跳过

#### Scenario: roadmap 保规划粒度仅借格式
- **WHEN** 生成/迁移 roadmap 索引层
- **THEN** 子任务复选框粒度 = change 级交付点、仅借 tasks 的 `- [ ]`+`N.X.Y` 格式，MUST NOT 塞入每个 change 的实现步分解（不下沉 tasks 粒度）

### Requirement: sdflow-done 归属镜像回写

`sdflow-done` SHALL 在 archive 之后、commit 之前**归属镜像**回写：扫 tasks 归属组（`## N.X.Y`）完成态 → 勾 roadmap 同号复选框（组全 `[x]`→勾、有 `[ ]`→不勾）+ 机械聚合阶段状态 enum + 追加 task-log 完成总结 + 按需更新里程碑句；产物随第四步 `git add openspec/` 提交。勾选 / 阶段 enum = 脚本机械（勾选行首锚定 `^- \[ \] {id}`）；完成总结叙述 / 里程碑句 = 模型写、脚本校验机器锚。回写 MUST NOT 阻塞 archive/merge；归属锚 subtasks 里某号在 roadmap 找不到同号复选框（roadmap 改号）MUST 降级标注落 task-log、MUST NOT 静默。

#### Scenario: 归属组全完成镜像勾选
- **WHEN** tasks 归属组 `## 4.D.1` 内复选框全 `[x]`
- **THEN** 勾 roadmap `4.D.1` 复选框（行首锚定，不误命中散文层 id 提及）

#### Scenario: defer 组不误勾
- **WHEN** tasks 归属组 `## 4.D.4` 内有 `[ ]`（实现期 defer）
- **THEN** roadmap `4.D.4` 复选框保持 `[ ]` 不勾（盘面兜底）

#### Scenario: 阶段状态 enum 机械聚合
- **WHEN** 更新阶段状态列
- **THEN** 脚本从该阶段全子任务复选框机械聚合（无完成=planned / 部分=in-progress / 全非deferred完成=delivered / 显式放弃=deferred），MUST NOT 靠模型判断

#### Scenario: 镜像不匹配降级标注
- **WHEN** 归属锚 subtasks 某号在 roadmap 找不到同号复选框
- **THEN** 降级标注「未能镜像：{subtask}」落 task-log（持久、随归档 commit），archive/merge 继续，MUST NOT 静默、MUST NOT 只落 stdout 摘要

#### Scenario: 完成总结机械/判断切分
- **WHEN** 写 task-log 完成总结（每 `(change,subtask)` 一条机器锚）
- **THEN** 叙述内容由模型写、脚本只校验机器锚在场且幂等；里程碑散文句由模型判断改（仅阶段状态跨阈值时），脚本不碰

### Requirement: roadmap 生成侧结构化与 change scaffold（双向）

`sdflow-roadmap` 生成的 roadmap SHALL 结构化索引层：子任务为借 tasks 复选框/编码格式的复选框（保规划粒度）+ 交付标注槽、概览表含阶段 `状态` enum 列（值集入单一机读契约）、task-log 条目含机器锚行；叙述层保留散文。`sdflow-roadmap` SHALL 提供 **change scaffold**：给定归属子任务（`--subtasks 4.D.1,4.D.2`）**双向机械生成**——roadmap 索引复选框（结构化格式）+ change tasks 顶层归属组骨架 + `<!-- roadmap: {name} subtasks: … -->` 锚 + proposal 引用，不靠人写对。存量 roadmap 一次性迁移新格式，MUST NOT 维护 dual-read。

#### Scenario: scaffold 双向机械生成
- **WHEN** 起 roadmap 驱动 change，`--subtasks 4.D.1,4.D.2`
- **THEN** scaffold 同源写 roadmap 索引复选框（结构化格式）+ change tasks 顶层归属组 `## 4.D.1`/`## 4.D.2` + 归属锚 + proposal 引用，三处机械产出、非人手写

#### Scenario: 概览表阶段状态 enum 列
- **WHEN** 生成/迁移 roadmap 概览表
- **THEN** 每阶段行含 `状态` 列、取值 ∈ 契约单一源 enum 集，回写脚本可机械聚合更新

#### Scenario: 旧 roadmap 迁移不 dual-read
- **WHEN** 存量 roadmap（旧散文格式）纳入回写
- **THEN** 一次性迁移到新索引层格式（概览表加 enum 列 + 子任务复选框借格式；不可映射的散文值如「端态A已定」显式补 enum 或标 legacy），回写只认新格式、MUST NOT 维护 dual-read
