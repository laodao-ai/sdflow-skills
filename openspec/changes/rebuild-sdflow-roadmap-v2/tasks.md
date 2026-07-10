# Tasks: rebuild-sdflow-roadmap-v2

> 需求 ID 缩写（specs/roadmap-planning/spec.md）：R1 三件套直写 · R2 伸缩头部章 · R3 讨论分档路由 ·
> R4 footage 落盘与引用边界 · R5 review 分档 · R6 收尾 checklist · R7 近细远雾。
> TG-18 未命中（纯 Markdown 无自动化测试）——验证方式为逐任务标注的人工核验点。

## 1. skill 主体重写（P0）

- [ ] 1.1 重写 `sdflow-roadmap/SKILL.md`：三件套产出与直写（去规则 4 change 壳，收尾 checklist 承接软门）、描述/frontmatter 同步「三件套」〔R1, R6〕验证：SKILL.md 全文无 requirements.md 产出指令、无 `opsx:new plan-` 流程；含收尾 checklist 三项（Review 处置无未处置 / 引用完整 / footage 不被引用）
- [ ] 1.2 SKILL.md 讨论层分档改造：双判据（起手显性信号→直入 wayfinder chart，destination=三件套定稿；起手不明→explore 起步 + 事中触发升级，去事前轮数预估〔grill-amendment〕）；memo 短档可选；无雾自降级退 explore；wayfinder 缺装降级 explore+memo（显式提示）〔R3〕验证：双判据表 + 三条降级路径措辞在场，判定结果要求显式陈述一行
- [ ] 1.3 SKILL.md footage 规则：落盘位置、规则 3 扩展两段式（三件套不引用 `footage/`，也不引用包根 `memo.md`；memo 落位不迁〔grill-amendment Q2〕）、「roadmap 类 effort」判别双判据措辞（隶属声明 or 由本 skill 发起，D3 推荐定稿）〔R4〕验证：与 tracker doc 分流规则口径一致
- [ ] 1.4 SKILL.md review 分档 + 近细远雾章节：默认 plan-eng-review、野心信号才 autoplan、跳过留痕；roadmap.md 近期 1-2 阶段五节全写、远期仅目标句+雾区备注、frontier 到达补细〔R5, R7〕验证：野心信号判据可观察（外部用户/变现/获客）；陷阱节同步更新

## 2. 模板层（P0/P1）

- [ ] 2.1 删除 `references/requirements-template.md`；`design-template.md` 头部增设「需求与目标态」伸缩章骨架（工作流型三小节必填：痛点/目标态判据/Non-Goals 每条附可证伪假设；产品型追加受众/功能取舍，NFR 留占位注释）+ 导航块去 requirements〔R2〕验证：模板注释说明伸缩判据；grep references/ 无 requirements-template
- [ ] 2.2 `roadmap-template.md` 加近细远雾分层注释与远期阶段骨架（目标句+雾区备注示例）+ 导航块更新〔R7〕验证：模板远期阶段示例不含子任务/验收节
- [ ] 2.3 `task-log-template.md`（:20,:69 导航）与 `memo-template.md`（:23,:27,:117 定位改「短档可选、footage 语境」）更新〔R4〕验证：memo 模板明示长档由 footage 取代

## 3. 消费仓约定（P0）

- [ ] 3.1 `openspec/matt/issue-tracker.md` Wayfinding 小节：标题补英文别名「（Wayfinding operations）」；小节头加 `<root>` 条件分流（roadmap 类 effort → `openspec/roadmaps/{name}/footage/`，其余默认 `openspec/matt/<effort>/`）；6 条 bullet 改 `<root>` 表达；尾加边界声明（footage 不进 triage 扫描、三件套不引用 footage）〔R4〕验证：沿用现文件中文 bullet 风格；分流判据与 SKILL.md 1.3 口径一致
- [ ] 3.2 CLAUDE.md 双锚制〔grill-amendment Q4〕：① Agent skills 托管块 Issue tracker 一行补锚句（roadmap 类 wayfinding 落 footage/，就近可见，接受 setup 重跑同批覆盖）；② 块外结构性锚由 6.1 的 :79 段重写承载（setup 重跑碰不到）〔R4〕验证：两锚措辞与 tracker doc 一致；托管块其余不动

## 4. wayfinding 最小实测（P1，spec 假设消解）

- [ ] 4.1 建演练 effort（如 `openspec/roadmaps/_drill/footage/`）走全六操作：chart 建 map+2 票（含 1 条 Blocked by）→ claim → resolve 回写 Decisions-so-far → frontier 判定解锁 → 收尾删演练目录；结果记入本 change 归档材料〔R3, R4〕验证：六操作均按 tracker doc 新约定落盘无错位；失败则按 proposal 假设 1 记录降级并调整 1.2 措辞

## 5. 存量迁移（P2）

- [ ] 5.1 wco 包迁移：requirements.md 按**全节清点表**并入 design.md 头部章〔grill-amendment Q3：§1.3 愿景/§2 核心需求表/§3 Non-Goals/§5 验收总纲 → 并入；§4 受众 → 一句带过；默认并入、确认已被吸收才弃、弃必记去向〕→ 修补包内节级引用（design.md:62、roadmap.md:69 等，实施时 grep `requirements` 全量复核）→ 删 requirements.md → design.md 头部加考古注记〔R1, R2〕验证：包内 grep 无 requirements.md 活引用；清点表随迁移 commit 留痕；归档树不回改
- [ ] 5.2 mlh 包迁移：同 5.1 全节清点（§6 参考文档实施时按内容判并入/弃置；roadmap.md:110、task-log.md:63,98 等引用修补；task-log 历史条目按归档不可变惯例不回改，靠考古注记兜底）〔R1, R2〕验证：同上
- [ ] 5.3 迁移后跑 `python3 sdflow-maintain/scripts/maintain_scan.py` 确认链接扫描无新告警（roadmaps/ 前缀本静默排除，此步为防意外）〔R1〕验证：scan 输出零新增

## 6. 全仓表述同步（P2）

- [ ] 6.1 CLAUDE.md:79、README.md:22、docs/sdflow-fable5/02-module-reference.md:205 「四件套」→「三件套」+ 去壳/footage 表述；**:79 段重写须明确写入「roadmap 类 wayfinding 落 `roadmaps/{name}/footage/`」一句，作为托管块外结构性第二锚**〔grill-amendment Q4，与 3.2 双锚制配对〕；全仓 grep `四件套`/`4 件套` 复核余漏（docs/ 归档类调研文档按「历史快照不回改」原则仅在明显误导处加注）〔R1, R4〕验证：活文档零残留旧口径；:79 段含 footage 锚句
- [ ] 6.2 dev checkout 重跑 `bash setup.sh`（模板文件增删后防孤儿链接，adr/0005）；确认 `~/.claude/skills/sdflow-roadmap/` 与 `~/.codex/skills/sdflow-roadmap/` 内容随源即时生效〔R1〕验证：setup 输出无异常、无孤儿清理遗漏
