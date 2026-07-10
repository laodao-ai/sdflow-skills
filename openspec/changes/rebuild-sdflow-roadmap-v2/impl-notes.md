# impl-notes — rebuild-sdflow-roadmap-v2（归档材料）

## 4.1 wayfinding 最小实测（2026-07-11，演练 effort=drill-docs-site，阅后即删、本 notes 为存证）

从**真实 `/sdflow-roadmap` 调用起步**（演练议题自带起手显性信号：三阶段+跨天+三子系统），新 SKILL.md（task1 重写版，经 dev setup symlink 生效）驱动全程；路由判档自然发生、非预供目的地路径〔SR-16/E8〕。

| 步 | 操作/约定 | 判定 |
|---|---|---|
| 判定点① | gate-0 不足 + 起手显性信号 → 直入 wayfinder chart（对话显式陈述一行） | ✓ 路由对照表第 1 行命中 |
| 宿主中立探测 | 当前宿主 Claude：`ls ~/.claude/skills/wayfinder` 在场 | ✓ |
| tracker doc preflight | `openspec/matt/issue-tracker.md` + Wayfinding 小节在场 | ✓ |
| 命名权先定 | skill 定 `drill-docs-site` + 字面量调用语（完整 map 路径） | ✓ |
| 无雾预检 | 判有雾（生成器/迁移范围未定）才落盘建 map | ✓ |
| chart | map.md 含**持久字段**（Tracker root/Effort kind）+ 顶部路标行 + 2 票（02 Blocked by 01） | ✓ 落 `roadmaps/{name}/footage/`，未落 `openspec/matt/` |
| claim → resolve | 01 claim→resolved，Resolution 落票 + map 双写（勾框 + Decisions so far 追加） | ✓ |
| frontier | 01 resolved 后 next-ready = 02（Blocked by 解锁） | ✓ |
| 中断恢复 | 02 claim 后中断；「新会话」仅凭 map 路径进入：**从持久字段派生路径**（零语义判别）→ stale claim 追加中断注记后重认领 → 新建票 03 落字段派生根 | ✓ `openspec/matt/` 无误落 |
| 收尾 | 删演练目录 + `git diff openspec/CONTEXT.md openspec/adr/` 对基线**零增量**（演练噪声零 revert 需求）〔SR-4〕 | ✓ |

**方法说明（诚实边界）**：wayfinder chart 的 HITL 广度 grilling 全流程属 matt 套件自身行为（adr/0002 零改动、非本 change 交付面），演练中六操作（chart/child/blocking/frontier/claim/resolve）按 wayfinder SKILL.md + 本 change 改后的 tracker doc 约定**亲执行**，验证对象 = 本 change 新增约定（分流根/持久字段/路标行/再入/重认领/引用边界）的落盘正确性。全程零错位、零丢失。

**结论**：proposal 假设 1（wayfinding 六操作在本地 markdown tracker 上真实可跑）消解——PASS，无需降级 explore+memo，无需回炉 Task 1 措辞。

## 5.1-5.3 存量迁移前置核验与受控延后（Q-C 拍板，2026-07-11 核验）

- **前置①（包无进行中实施 change）**：`openspec list` 当前 active 仅 rebuild-sdflow-roadmap-v2 自身；wco 剩 P2/P3+Phase C 占位、mlh 剩 P4 残项+P6，均无在飞实施 change——①满足。
- **前置②（首个新流程 roadmap 已走通端到端）**：**不满足**——新流程（三件套直写）本 change 才落地，尚无任何真实 roadmap 包走通端到端（4.1 演练为 wayfinding 操作实测，非完整 roadmap 走通）。
- **处置**：按设计门 Q-C 拍板与 design Migration step3 前置，5.1（wco 迁移）/5.2（mlh 迁移）/5.3（总检）本轮 **MUST NOT 执行**，受控延后——非缺口，是拍板的时序约束。排期已登记 todolist（见 T129，显式挂本 change），触发条件 = 首个新流程 roadmap SHIPPED 且目标包无在飞 change；操作序列以 tasks.md 5.1-5.3 + design Migration step3 为准（全节清点表/考古注记四要素/编号不位移/清点表落盘随 commit/per 包 maintain_scan 全部继续有效）。

## 6.1 语境判读处置清单（全仓 grep「四件套」，见 task5 commit）

全仓 `grep -rn "四件套\|4 件套\|4件套" --include="*.md" .`（排除 `.git`）命中 **156** 处。逐命中判语境，分七档处理，合计 5+26+70+41+6+6+1+1 = **156**（核对一致）。

### A. 逐命中判读并改动（roadmap 语境，活文档）—— 5 处

| 文件:行 | 语境判定 | 动作 |
|---|---|---|
| `README.md:23` | roadmap 语境（sdflow-roadmap 一行说明） | 改：四件套→三件套 + 直写不经 change 壳表述 |
| `CLAUDE.md:79`（托管块外） | roadmap 语境（roadmap 文档包定义段） | 改：四件套→三件套 + 直写不经 `plan-{topic}` 壳 + **补结构性第二锚句**「roadmap 类 wayfinding 落 `openspec/roadmaps/{name}/footage/`（长讨论考古层；三件套不引用）」；存量两包保留「沿用存量四件套格式（迁移受控延后，Q-C）」一句，避免误导读者以为 wco/mlh 已是三件套 |
| `docs/sdflow-fable5/01-goals-and-rationale.md:153` | roadmap 语境（目标 vs 现状对照表「roadmap 制定」行） | 改：「四件套 + 交叉 review」→「三件套直写 + 分档 review」 |
| `docs/sdflow-fable5/02-module-reference.md:205` | roadmap 语境（4.6 节 sdflow-roadmap 定义本体，含 requirements/四件套/change 壳/3.5 步交叉 review 等全部旧口径） | 改：全段重写为三件套定义 + footage/memo 引用边界两段式 + 直写不经 change 壳 + review 按野心信号分档（默认 `/plan-eng-review`，野心信号 `/autoplan`）+ 存量四件套包兼容一句 |
| `docs/sdflow-fable5/04-optimization-proposal.md:185` | roadmap 语境（5.2 fog-of-war 建议条目引用「roadmap 四件套」指代文档包本身） | 改：「roadmap 四件套」→「roadmap 三件套」（仅术语替换；该建议条目本身是否已被本 change Task2 近细远雾实现，超出术语同步范畴，不在本节处置，留待后续 retro/复核） |

### B.「change 四件套」撞词语境（proposal/design/specs/tasks 之谓，或其他非 roadmap 之谓）—— 一律不触碰，26 处

判读依据：这些命中指代 OpenSpec change 产出的 proposal/design/specs/tasks 四件套（`opsx:ff` 产出契约、ship_gate 失鲜扫描域、autoplan/spec-review 审查对象等）、或与之衍生的历史记录条目，与本 change 的 roadmap 四件套→三件套语义无关，属 SR-6 撞词排除名单。

| 文件（命中行） | 语境判定 | 动作 |
|---|---|---|
| `docs/workflow-map.md:163` | change 四件套（ship_gate 失鲜扫描路径） | 排除-撞词 |
| `docs/workflow-overview.md:28,98,106,109,119,228,229`（7 处） | change 四件套（`opsx:ff` 产出契约 / autoplan 审查对象） | 排除-撞词 |
| `docs/workflow-skills/sdflow-done.md:15` | change 四件套（sdflow-done 输入契约） | 排除-撞词 |
| `docs/workflow-skills/grill-with-docs.md:18` | change 四件套（grill 调用时机） | 排除-撞词 |
| `docs/workflow-skills/sdflow-spec-review.md:19` | change 四件套（评审对象） | 排除-撞词 |
| `docs/workflow-skills/impl-pipeline-matt-vs-superpowers.md:67` | change 四件套（to-spec 冗余对比） | 排除-撞词 |
| `docs/sdflow-fable5/01-goals-and-rationale.md:26,38`（2 处） | change 四件套（OpenSpec 基座边界句 / opsx:ff mermaid 节点，:26 明确标注「change 四件套」） | 排除-撞词 |
| `docs/sdflow-fable5/04-optimization-proposal.md:125` | change 四件套（spec-kit 跨工件一致性对比，指 proposal/design/specs/tasks 一致性） | 排除-撞词 |
| `docs/sdflow-fable5/02-module-reference.md:83` | 第三义撞词——「编排器四件套详解」标题指 sdflow-ship/spec-review/code-review/done 四个编排器 skill（3.1-3.4 节），既非 roadmap 四件套也非 change 四件套 | 排除-撞词（第三义） |
| `docs/sdflow-fable5/02-module-reference.md:112` | change 四件套（ship_gate 失鲜分域描述） | 排除-撞词 |
| `openspec/specs/spec-workflow/spec.md:429,432,433`（3 处） | change 四件套（gate 失鲜/impl-review 豁免规则） | 排除-撞词 + **排除-红线**（任务书 MUST NOT 改 `spec-workflow/spec.md`） |
| `openspec/issues/consolidation-plan.md:61` | change 四件套（REC-1 批次 scope，且已标「✅已 ship，明细保留作历史记录」） | 排除-撞词 + 排除-历史记录 |
| `openspec/issues/buglist/2026-07-04-buglist.md:48,50,53`（3 处） | change 四件套（design-approved 失鲜判定的 bug 记录，状态 FIXED） | 排除-撞词 + 排除-历史记录 |
| `openspec/issues/todolist/2026-07-todolist.md:330,690`（2 处） | change 四件套（autoplan 改动核对 / grill 成果落盘，均状态 DONE） | 排除-撞词 + 排除-历史记录 |

### C. 归档树 —— 不可变，70 处

| 文件（命中行） | 语境判定 | 动作 |
|---|---|---|
| `openspec/changes/archive/**/*.md`（70 处，遍布 17 个归档 change 目录，如 `2026-07-03-sdflow-ship`、`2026-07-04-ship-gate-hardening{,-2}`、`2026-07-05-gate-anchor-line-scoped`、`2026-07-07-mlh-p2/p5`、`2026-07-08-mlh-p5-parser-cleanup` 等） | change 四件套（ship-gate 失鲜/impl-review 豁免规则的历次实现记录、各 change 自身评审报告/proposal/design/tasks） | 排除-归档不可变；逐条通读未见「明显误导」需加注情形（均为 change-撞词或该 change 自身四件套的既成历史记录，不涉及 roadmap 术语） |

### D. 本 change 自身（`rebuild-sdflow-roadmap-v2/`）—— 红线，不触碰，41 处

| 文件（命中行） | 语境判定 | 动作 |
|---|---|---|
| `openspec/changes/rebuild-sdflow-roadmap-v2/{proposal.md,design.md,tasks.md,specs/roadmap-planning/spec.md,spec-review-report.md,gstack-review.md,superpowers-plan.md,impl-notes.md}`（41 处） | 本 change 自身四件套 / 评审报告 / plan / notes，描述的正是本次「四件套→三件套」变更本身，是叙事必需用词 | 排除-本 change 红线（任务书 MUST NOT 改 proposal/design/tasks/specs；spec-review-report/gstack-review/superpowers-plan/impl-notes 属过程材料不回改） |

### E. 存量 roadmap 包（Q-C 受控延后）—— 6 处

| 文件（命中行） | 语境判定 | 动作 |
|---|---|---|
| `openspec/roadmaps/workflow-cost-optimization/{requirements.md:11,task-log.md:63,memo.md:3}`（3 处） | roadmap 语境，但属存量四件套包 | 排除-存量包（Q-C 迁移受控延后，见 5.1-5.3 节） |
| `openspec/roadmaps/mechanical-layer-hardening/{requirements.md:14,task-log.md:48,memo.md:19}`（3 处） | roadmap 语境，但属存量四件套包 | 排除-存量包（Q-C） |

### F. 历史规划/备忘快照（非归档目录，但描述已定稿的过去规划）—— 6 处

| 文件（命中行） | 语境判定 | 动作 |
|---|---|---|
| `docs/superpowers/plans/2026-07-01-openspec-review-html-tool.md:1311,1335,1390,1395,1585`（5 处） | roadmap 语境（review-html-tool 工具设计里提及「roadmap 四件套生成完之后」触发时机），但该文件是 superpowers writing-plans 产出的历史实现计划快照（该工具从未落地实现，无对应脚本/skill） | 排除-历史快照：不回改（该 plan 未来若被真正实现，实现者需重新核对当时 roadmap 产出形态，不依赖本文措辞） |
| `sdflow-init/memo-review-html-tool.md:79` | roadmap 语境（同一工具的 memo 版本，同样描述「四件套生成完之后」触发时机），未实施 | 排除-历史快照：同上，未落地想法，不回改 |

### G. Task 2 范围内、措辞已正确（不属本任务处置）—— 1 处

| 文件（命中行） | 语境判定 | 动作 |
|---|---|---|
| `sdflow-roadmap/references/long-flow-skill-paradigm.md:113` | roadmap 语境，但为描述「四件套→三件套」历史转型本身的 HTML 注释（用引号分别指称新旧术语：`从"四件套"...收敛为"三件套"`），措辞已准确，且该文件属 Task 2（模板层）文件集 | 排除-已处理（Task 2 范围内、措辞本身已正确，无需改动） |

**自检结果**：A 类 5 处已改并复核（`grep -rn "四件套\|4 件套\|4件套" --include="*.md" .` 复跑，A 类命中位置均已消失，B/C/D/E/F/G 类命中依旧在场符合预期，无新增/漏改）；`git diff openspec/specs/spec-workflow/spec.md` 为空；CLAUDE.md 块外段（:78-83）含 footage 第二锚句「roadmap 类 wayfinding 落 `openspec/roadmaps/{name}/footage/`（长讨论考古层；三件套不引用）」。

## 6.2 双宿主 wayfinder 装载核验（task6 执行后补写）
