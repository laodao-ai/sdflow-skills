# Tasks: rebuild-sdflow-roadmap-v2

> 需求 ID 缩写（specs/roadmap-planning/spec.md）：R1 三件套直写 · R2 伸缩头部章 · R3 讨论分档路由 ·
> R4 footage 落盘与引用边界 · R5 review 分档 · R6 收尾 checklist · R7 近细远雾。
> TG-18 未命中（纯 Markdown 无自动化测试）——验证方式为逐任务标注的人工核验点。

## 1. skill 主体重写（P0）

- [x] 1.1 重写 `sdflow-roadmap/SKILL.md`：三件套产出与直写（去规则 4 change 壳，收尾 checklist 承接软门）、描述/frontmatter 同步「三件套」；存量四件套包**兼容模式**（续跑不报错不强迁，一行提示）+ requirements.md **逃生舱**（显式要求即遵从+头部注明非默认）+ 包生命周期 create/continue/replan（同名包不静默覆盖）〔R1, R6；spec-review-amendment SR-1/SR-3/SR-7〕验证：SKILL.md 全文无 requirements.md 产出指令、无 `opsx:new plan-` 流程；含收尾 checklist **五项**（Review 处置 / 引用完整含最小引用图判定+报行号 / footage+memo 不被引用 / wayfinder 闭环 frontier 空或显式放弃 / CONTEXT-adr 讨论期增量核对）+ 兼容/逃生舱/生命周期三段措辞在场
- [x] 1.2 SKILL.md 讨论层分档改造：双判据（起手显性信号→直入 wayfinder chart，destination=三件套定稿；起手不明→explore 起步 + 事中触发升级，去事前轮数预估〔grill-amendment〕）；事中触发承认口述/盘面双来源 + **压缩前 flush 进 memo（该场景 memo 转必需）**〔SR-5〕；memo 短档可选；无雾自降级退 explore 且广度 grill 要点转录不清零 + chart 未持久化预检〔SR-11〕；**宿主中立探测** + 消费仓 tracker doc preflight 校验（缺失 fail-closed 给初始化指引）〔SR-9/SR-10〕；讨论充分度 gate-0 沿用现行 5 项 checklist（:68-78）原样搬入并显示直接结晶依据一行〔SR-2，堵 D4/XD4〕；office-hours 保留为讨论层第三分支（野心信号→前置验证，与 review 分档共用信号词表；设计门 Q-D 已拍板〔D3〕）；wayfinder Task 票限定可行性验证 scope（规则 5 不实施边界）〔SR-16/E9〕验证：双判据表 + 降级路径全在场；判定结果显式陈述一行；**示例开场白→期望路由对照表**（≥4 例）作自检基准〔D12〕
- [x] 1.3 SKILL.md footage 规则：落盘位置、规则 3 扩展两段式（三件套不引用 `footage/`，也不引用包根 `memo.md`；memo 落位不迁〔grill-amendment Q2〕）、**命名权先定**（skill 定 kebab-case 名+完整 map 路径以字面量入调用语，wayfinder 命名步只精化）、**map 持久字段**（Tracker root / Effort kind，续跑只从字段派生）、map 顶部路标行、map 再入约定（归档 map-N 或单 map 分批，钉死一种）〔R4；SR-3/SR-21〕验证：与 tracker doc 分流规则口径一致；调用语模板含字面量路径
- [x] 1.4 SKILL.md review 分档 + 近细远雾章节：默认 plan-eng-review、野心信号才 autoplan；**调用语含「三件套视为整体 plan、主入口 roadmap.md」话术（存活验收）**〔SR-7/D5/A4〕；跳过仅限人类操作者显式授权、状态记 review-waived〔SR-7/XD2〕；显式覆盖默认分档遵从+记偏离理由〔SR-7/D7〕；review 依赖失败留「未审待恢复」〔SR-7/XD3〕；roadmap.md 近期 1-2 阶段五节全写（选择理由必写）、远期仅目标句+雾区备注（缺什么信息必写）、长周期依赖例外提前写前置节、frontier 到达补细+命中野心信号重判分档、前序子任务终局放弃视为已处置〔R5, R7；SR-8/SR-14〕验证：野心信号判据可观察（外部用户/变现/获客）；整体 plan 话术与五项 checklist 逐字在场；陷阱节同步更新

## 2. 模板层（P0/P1）

- [x] 2.1 删除 `references/requirements-template.md`；`design-template.md` 头部增设「需求与目标态」伸缩章骨架（**无编号章名，不占 `## N.` 序列**〔SR-15〕；工作流型必填：痛点/目标态判据/**验收门槛槽**/Non-Goals 每条附可证伪假设；需求清单/优先级可选占位；产品型追加受众/功能取舍，NFR 留占位注释；混合/探索型兜底：判据允许具名占位不硬造〔SR-13〕）+ 导航块去 requirements〔R2〕验证：模板注释说明伸缩判据与兜底；grep references/ 无 requirements-template
- [x] 2.2 `roadmap-template.md` 加近细远雾分层注释与远期阶段骨架（目标句+「缺 X 信息」雾区备注示例；近期 1-2 选择理由槽；长周期依赖例外注释〔SR-14〕）+ 导航块更新〔R7〕验证：模板远期阶段示例不含子任务/验收节
- [x] 2.3 `task-log-template.md`（:20,:69 导航）、`memo-template.md`（:23,:27,:117 定位改「短档可选、footage 语境」+ 压缩前 flush 场景〔SR-5〕）与 `long-flow-skill-paradigm.md`（第 6 个模板文件，表述复核〔SR-19〕）更新〔R4〕验证：memo 模板明示长档由 footage 取代、flush 场景在场

## 3. 消费仓约定（P0）

- [x] 3.1 `openspec/matt/issue-tracker.md` Wayfinding 小节：标题补英文别名「（Wayfinding operations）」；小节头加 `<root>` 条件分流（roadmap 类 effort → `openspec/roadmaps/{name}/footage/`，判别=调用语字面量声明，其余默认 `openspec/matt/<effort>/`）；6 条 bullet 改 `<root>` 表达；加 **map 持久字段约定**（Tracker root/Effort kind，续跑从字段派生）、**stale claim 重认领规则**（中断票追加注记后可重认领）、**map 再入约定**〔SR-3/SR-16〕；尾加边界声明三条（footage 不进 triage 扫描、三件套不引用 footage、误落默认根的 wayfinder 票 MUST NOT 被 triage 贴五态/改 Status〔SR-17〕）〔R4〕验证：沿用现文件中文 bullet 风格；分流判据与 SKILL.md 1.3 口径一致
- [x] 3.2 CLAUDE.md 双锚制〔grill-amendment Q4〕：① Agent skills 托管块 Issue tracker 一行补锚句（roadmap 类 wayfinding 落 footage/，就近可见，接受 setup 重跑同批覆盖）；② 块外结构性锚由 6.1 的 :79 段重写承载（setup 重跑碰不到）〔R4〕验证：两锚措辞与 tracker doc 一致；托管块其余不动

## 4. wayfinding 最小实测（P1，spec 假设消解）

- [x] 4.1 演练 effort（如 `openspec/roadmaps/_drill/footage/`）——**从真实 `/sdflow-roadmap` 调用起步**（让路由判档自然发生，非预供目的地路径〔SR-16/E8〕）：①执行前记 `git diff --stat openspec/CONTEXT.md openspec/adr/` 基线〔SR-4/A2〕；②chart 建 map+2 票（含 1 条 Blocked by，核对 map 持久字段落盘）→ claim → resolve 回写 Decisions-so-far → frontier 判定解锁；③**模拟中断**：留一张 claimed 票开新会话续跑，验证 stale claim 重认领 + 新建票从 map 字段派生路径（不落回 matt/）〔SR-3/SR-16/XE1〕；④收尾删演练目录 + 核对 CONTEXT.md/adr 增量，演练噪声 revert〔SR-4〕；结果记入本 change 归档材料〔R3, R4〕验证：六操作+中断恢复均按新约定落盘无错位；失败则按 proposal 假设 1 记录降级并调整 1.2 措辞

## 5. 存量迁移（P2）

- [ ] 5.1 wco 包迁移（**前置：包无进行中实施 change + 首个新流程 roadmap 已走通〔SR-15，Q-C 拍板确认〕**）：requirements.md 按**全节清点表**并入 design.md 头部章（**无编号章名不占 `## N.` 序列**〔SR-15/B6〕；grill-amendment Q3：§1.3 愿景/§2 核心需求表/§3 Non-Goals/§5 验收总纲 → 并入；§4 受众 → 一句带过；默认并入、确认已被吸收才弃、弃必记去向）→ 修补包内**前向结构引用**（design.md:62、roadmap.md:69 等，实施时 grep `requirements` 全量复核；task-log 历史 DID 条目保留不回改〔SR-15/E6〕）→ 删 requirements.md → design.md 头部加**考古注记四要素**（旧路径/迁移日期+commit/见 git/「旧 §X→现位置」映射表〔SR-15/XE6/XD10〕）→ **立即跑 `maintain_scan.py`**〔SR-15/B7〕〔R1, R2〕验证：包内 grep 无 requirements.md 活前向引用；**清点表落盘为文件随 commit 提交**（非仅 message）；design 编号序列零位移；归档树不回改（**受控延后**：Q-C 拍板前置②「首个新流程 roadmap 已走通端到端」未满足——非缺口；排期 T129，触发条件与操作序列见 impl-notes §5.1-5.3）
- [ ] 5.2 mlh 包迁移：同 5.1 全流程（§6 参考文档实施时按内容判并入/弃置；roadmap.md:110、task-log.md:63,98 等前向引用修补）〔R1, R2〕验证：同上（**受控延后**：Q-C 拍板前置②「首个新流程 roadmap 已走通端到端」未满足——非缺口；排期 T129，触发条件与操作序列见 impl-notes §5.1-5.3）
- [ ] 5.3 两包迁移后总检 `python3 sdflow-maintain/scripts/maintain_scan.py`（每包已各跑一次，此为终态复核；roadmaps/ 前缀本静默排除，防意外）〔R1〕验证：scan 输出零新增（**受控延后**：Q-C 拍板前置②「首个新流程 roadmap 已走通端到端」未满足——非缺口；排期 T129，触发条件与操作序列见 impl-notes §5.1-5.3）

## 6. 全仓表述同步（P2）

- [x] 6.1 CLAUDE.md:79、README.md:22、docs/sdflow-fable5/{01-goals-and-rationale.md:153〔SR-6 补漏〕,02-module-reference.md:205} 「四件套」→「三件套」+ 去壳/footage 表述；**:79 段重写须明确写入「roadmap 类 wayfinding 落 `roadmaps/{name}/footage/`」一句，作为托管块外结构性第二锚**〔grill-amendment Q4，与 3.2 双锚制配对〕；全仓 grep `四件套`/`4 件套` **逐命中判语境**——「change 四件套」语境（proposal/design/specs/tasks 之谓，如 `openspec/specs/spec-workflow/spec.md:420-424` 活规范）**MUST NOT 触碰**〔SR-6/E1，排除名单见 design scope-check 表〕；docs/ 归档类调研文档按「历史快照不回改」原则仅在明显误导处加注〔R1, R4〕验证：活文档零残留旧口径（roadmap 语境）；:79 段含 footage 锚句；spec-workflow/spec.md 零改动
- [x] 6.2 dev checkout 重跑 `bash setup.sh`（模板文件增删后防孤儿链接，adr/0005）；确认 `~/.claude/skills/sdflow-roadmap/` 与 `~/.codex/skills/sdflow-roadmap/` 内容随源即时生效；**核验两宿主 wayfinder 装载现状并与 SKILL.md 宿主中立探测措辞一致**（接地实测 Codex 侧无 wayfinder → 降级路径将常驻，措辞如实〔SR-9/XE5〕）〔R1〕验证：setup 输出无异常、无孤儿清理遗漏；双宿主探测行为与失败模式表一致
