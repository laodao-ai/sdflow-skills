# Tasks: issues-pool-batch-mgmt（Phase B）

> 从归档 [ROADMAP.md](../archive/2026-07-02-streamline-workflow-automation/ROADMAP.md)「Phase B 待迁任务」迁入（原 tasks 编号 §5.\* + §3.3 + §8.2 + §8.5 括注在条目内）。
> 决策真相源 = umbrella design §8 / I1–I13。当前全部未勾（本 change 处 propose 阶段，实现在阶段三）。
> **spec-review 补强**：自动决策 D1–D9 已并入下列任务（标〔D\*〕，见 design §八）；**需拍板 Q1（迁移/ID 撞号）· Q2（批次命名/对账）· Q3（batches.md 格式契约+纠正语义）待设计门裁后再补对应任务**（见 [spec-review-report.md](./spec-review-report.md)）。

## 1. issues 结构标准（写进 recorder 约定段，I13 单一真相源）

- [x] 1.1 把 issues 结构标准写进 `buglist-recorder` / `todolist-recorder` 各自"约定速查"段（唯一真相源，不另起 rules 文件）〔I1/I13，原 §5.1〕
- [x] 1.2 标准内容含：目录结构 `issues/{buglist,todolist}/` + `INDEX.md` + `batches.md`；三维度 schema（源/批次/status）；状态词表；批次生命周期；sweep 协议；INDEX 生成规则；batches.md 格式；**B(bug)/T(todo) 前缀跨池互斥**为显式规范条款〔D9〕〔I1/I3/I11〕

## 2. recorder 脚本增强（buglist.py / todolist.py）

- [x] 2.1 路径默认 `openspec/buglists|todolists/` → `openspec/issues/{buglist,todolist}/`（buglist.py:143 `buglists_dir` / todolist.py:136 `todolists_dir`）〔I1/I9，原 §5.3〕
- [x] 2.2 表加 `批次` 列；源/批次/status 三维度分家；status 回归干净（不塞批次）；旧文件无 `批次` 列时兼容留空〔I3/I8，原 §5.2/§5.6〕
- [x] 2.3 `scan` 加维度 `--源 / --批次 / --open-ungrouped`（现状仅 `--status`）〔I4，原 §5.3〕
- [x] 2.4 加 `triage` 命令（给 OPEN 项赋批次 + 转 PROPOSED）〔I4/I9，原 §5.3〕

## 3. 共享 issues 层脚本（新增，独占跨 bug+todo 的 reindex / batch）〔grill-amendment: B-Q2〕

> B-Q2：`reindex`/`batch` 是**跨类型**命令（join 两池 + 维护 `INDEX.md`/`batches.md`），归**新增的共享 issues 层脚本**（`issues.py`，或薄 skill `issues-recorder`），不塞进 per-type 的 buglist.py/todolist.py（见 design §五）。物理落点（全局 vs 随 recorder）随 `minimize-repo-footprint` 一并定。

- [x] 3.0 新建共享 issues 层脚本 `issues.py`（读 `issues/buglist/` + `issues/todolist/` 两池；owns `issues/INDEX.md` + `issues/batches.md`）；写文件用 **temp + `os.replace` 原子写**〔D6〕；`INDEX.md` 首行加 `<!-- GENERATED ... DO NOT EDIT -->` banner〔D3〕；join 时**跨池 ID 前缀冲突检测**（B/T 撞号报错不静默）〔D9〕；失败模式按 design §8.1 处理（解析失败/orphan 批次 tag 报警不静默）〔D5〕
- [x] 3.1 `reindex` 命令 → 从各 dated 文件重建 `issues/INDEX.md`（**禁手改**；摊清 open item × 批次 + 标出已闭合〔终态〕项）〔I2，原 §5.4〕（Task 9：banner+原子写+open×批次板+已闭合摘要+幂等，已实现；批次状态同步见 3.2/Task 11）
- [x] 3.2 reindex **顺带同步批次状态**：拿 item 池当 ground truth——成员**全部进入各自终态集**（bug: `FIXED`/`WONTFIX`；todo: `DONE`/`WONTDO`）→ 批次判/标 `DONE`；状态与成员不一致 → 标出纠正（不静默信手写状态）。**不做逾期主动催办**〔I2/I12/B-Q1·grill-amendment，原 §5.4〕
- [x] 3.3 `issues/batches.md` 注册表 + `batch` 命令（add / set-status，跨 bug+todo，`PLANNED→IN_PROGRESS→DONE`，条目薄：名/状态/成员(生成)/优先级/一句范围/完成记录）〔I11，原 §5.5〕（Task 10：add/set-status/rename 三命令 + Q3 字段级 grammar 已实现；`成员:` 生成行的内容填充/orphan 报警留 Task 11 reindex）

## 4. sweep 接入 opsx-done + workflow.md

- [x] 4.1 `opsx-done` 加 **issues sweep 步**（`scan --status OPEN --change {本change}`〔D4：显式传 --change，不靠 detect_change 猜〕 → 分诊入批次 → `batches.md`(PLANNED) → **末尾运行 `reindex` 刷新 INDEX**〔D3〕 → hand-off 引用）；**以 `源==本change` 为界只诊本 change 新增项**，源为空孤儿不归本次 sweep（交通用 `--open-ungrouped` 清理流程，见 design §4.2）〔I5/I6/B-Q3/D3/D4，原 §3.3〕
- [x] 4.2 去掉 `opsx-done` SKILL 里 Phase A 留的〔Phase B 补〕占位，落地正式 sweep 步
- [x] 4.3 `workflow.md` **追加 sweep 步引用**（ROADMAP 约束1：B 增量改 workflow.md 一次，不碰 A 骨架/不预写 C）

## 5. review UI + 验证 + 迁移影响

- [x] 5.1 review UI（`workflow/tools/engine.js`、`review.html`）读 `issues/` 新路径（可选改读 `INDEX.md`）〔I10，原 §5.7〕（**no-op**：engine.js 是通用 markdown 树浏览器，无 `buglists/todolists/issues` 硬编码路径——`issues/` 存在后天然可浏览、`issues/INDEX.md` 作 markdown 渲染即可，无需改代码。计划明确"无硬编码则跳过并注明"）
- [x] 5.2 **一致性自检**：`reindex` 生成的 `INDEX.md` 与 dated 文件 + `batches.md` 三处一致（表↔块↔INDEX 自检）〔原 §8.2〕
- [x] 5.3 脚本测试更新/新增：per-type（新路径、批次列兼容、scan 新维度、triage）+ 共享 `issues.py`（reindex 含终态集批次同步、batch、跨两池 join）
- [x] 5.4 其它使用 laodao-skills 项目的迁移影响已确认（OQ3）〔原 §8.5〕

## 6. 收尾同步

- [x] 6.1 本仓 `openspec/INDEX.md` 若有规则/计数变更则同步（CLAUDE.md 硬性要求）
- [ ] 6.2 spec delta 2 条 Requirement 归档时并入 `openspec/specs/spec-workflow/`（opsx-done archive 步做）

## 7. Q1–Q3 裁决落地〔spec-review-amendment · provisional，待设计门确认〕

- [x] 7.1 **Q1 迁移加固**：`next_id`/`scan` 过渡期 **dual-read**（新 `issues/` + 旧 `buglists|todolists/` 都扫再取 max）；跨路径 **ID 撞号检测**（同 ID 报错）；proposal 记硬切风险〔Q1〕
- [x] 7.2 **Q2 批次命名保守化**：sweep 永远新建 1 批次 key=本change、禁跨 change 合并；`batch` 加 `rename`；reindex 对 orphan 批次 tag 显式报警不静默生成 ghost〔Q2〕（Task 10 已交付 `batch rename`——改 batches.md key + 同步 item 池两池的批次 tag；sweep 新建规则〔4.1〕与 reindex orphan 报警〔Task 11〕仍待）
- [x] 7.3 **Q3 batches.md grammar**：定字段级 grammar（生成行〔状态/成员〕vs 人写行〔计划/优先级/范围〕+ 分隔）；reindex 只 patch 生成行、绝不覆写人写行；"纠正"只追加警告标注、不越权改人写状态值〔Q3〕（Task 10 已定字段级 grammar 并在 `batch set-status`/`rename` 落实"只精确 patch 生成行、绝不覆写人写行"；reindex 对 `成员:` 的 patch + 纠正标注留 Task 11）
- [x] 7.4 三条若设计门被改选项，同步 design §8.2 + 本节任务
