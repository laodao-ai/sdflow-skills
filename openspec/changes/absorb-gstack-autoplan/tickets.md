---
impl-pipeline: tickets
---

## Global Constraints

- 广审镜两镜各自 prompt MUST 含:`{change_dir}` 路径、四条通则原文、职责清单、返回结构化 findings(问题/证据 file:line/置信/严重度/建议)、不 AskUserQuestion。base R 项划分写死在 SKILL 镜表(strategy=BASE-01/08/09/10/12/13/14/18/22/26/27/30; plan-eng=BASE-05/06/16/17/19/25/28; 默认规则:未列明 base R 项归 strategy)。base R 项归广审镜,domains/ R 项归领域镜。plan-eng prompt MUST 含防重叠语义补句(栈特定错误处理由领域镜负责)。
- `step1-broad-review` 锚 mode 枚举 MUST ∈ {subagent, main-session}。mode 值为主 session 自报,MUST NOT 声称有机械保证。
- `outside-voice` 锚的 `guard=` 字段从新锚文法移除;anchor_lint MUST NOT 解析该字段。
- fold 表直接替换(不共存):autoplan-ceo/design/eng/dx 四行 → strategy + plan-eng 两行。
- devex.md 条目 MUST 采用可判表式(`ID/触发条件/必需文本证据/PASS/FAIL/N.A`),无证据输出 UNVERIFIABLE,MUST NOT 脑补 PASS。
- 文档 sweep 范围 grep 归零口径:`grep -rn "autoplan\|gstack" sdflow-spec-review/SKILL.md sdflow-roadmap/SKILL.md sdflow-init/assets/workflow/`(排除 reference/)严格归零。DOC-1:正文即最终态,零残留。
- retro `stage_walltimes` 改为 attribute-to-next(checkpoint=工作完成点,区间归其完成点);`is_archive_rename` 判定对象由 cur 换 nxt。
- roadmap review 镜职责与 spec-review 广审镜**同源**——由 `sdflow-init/assets/snippets/broad-mirrors.md` 经注入脚本注入两 SKILL 的 `sdflow:broad-mirror-def` 托管块;`setup.sh --check` 门禁。
- roadmap voice: sync-only,site=`roadmap-voice`,前台 `--timeout 300`,外层 ≥330000ms,⑦ 表映射,失败同族 fallback 带时间预算,task-log 一行 runner/reason_code 留痕。
- 矩阵 golden 迁移:原 `test_outside_voice_guard.py` 全笛卡尔用例 MUST 迁移进 anchor_lint 测试侧,MUST NOT 随文件删除静默丢覆盖面。
- `anchor_lint.py` `_MIRRORS_UPGRADE_HINT` 失效指引修复:`sdflow-init update` → 「回运行 checkout 跑 `bash setup.sh`」。
- 归档报告旧锚(autoplan-* raw 名)不迁移,历史行降级可接受。

### Task 1: Bundle 机械层同步与 retro 归属修正

**Blocked-by:** none
**R-ID:** R-workflow-metrics, R-host-adaptive-execution, R-spec-workflow

Bundle 机械层资产全部对齐新结构,retro 归属语义修正,确保全仓 pytest 绿:

1. `lens-metric-contract.md` fold 块:将 `autoplan-ceo/design/eng/dx: broad` 四行替换为 `strategy: broad` + `plan-eng: broad`(直接替换不共存);散文段同步(「跨模型性」段 autoplan 例名换新 raw 名,双实现表述改为 anchor_lint 单实现)。
2. `anchor_lint` golden 测试补用例:spec-review 报告 `mirrors=` 含 `broad` token 的场景、`step1-broad-review` 锚 `mode="subagent"` 与 `mode="main-session"` 两枚举值(枚举常量零改动,只补用例覆盖新形态)。
3. `sdflow-retro` `stage_walltimes`:相邻提交差由 attribute-to-previous 改为 attribute-to-next;`is_archive_rename` 判定对象由 cur 换 nxt;修正 `("sdflow-spec-generate","ff")` 映射;补新旧序列回归测试(单 checkpoint 新序列 + 含 `spec-review-autoplan` 中间标签的历史序列);`openspec/retro/report.md` 重跑再生。
4. `anchor_lint.py` `_MIRRORS_UPGRADE_HINT` 失效指引修复:`sdflow-init update` → 「回运行 checkout 跑 `bash setup.sh`」。

- [x] fold 表四行替换为两行,fold 散文与注记同步
- [x] anchor_lint golden 补 broad mirrors 与 step1 mode 两枚举用例
- [x] retro stage_walltimes attribute-to-next 实现 + is_archive_rename 判定对象翻转
- [x] retro 新旧序列回归测试通过
- [x] retro report.md 重跑再生(49 归档 change 新口径)
- [x] _MIRRORS_UPGRADE_HINT 指引修复
- [x] 全仓 `/usr/bin/python3 -m pytest` 绿

### Task 2: spec-review SKILL 重写与同源注入机制

**Blocked-by:** 1
**R-ID:** R-spec-workflow, R-host-adaptive-execution

spec-review SKILL 的 Step1/Step2 合并为单批 dispatch + 锚枚举换值 + guard 环节删除 + 同源注入机制建立:

1. `sdflow-spec-review/SKILL.md` 重写:删两段 dispatch 时序图与 T20 分治条款;新镜表加 strategy/plan-eng 行(职责清单=DD2 base R 项划分,含防重叠语义补句);删「与 autoplan 的分工」表与「防重叠 1.4」条款。
2. `step1-broad-review` 锚 mode 枚举 `native|simulated` → `subagent|main-session`;`subagents="unavailable"` 时广审主 session 亲做描述;mode 诚实边界声明。
3. Step1 的 autoplan 原生执行/gstack-review.md 落盘/outside_voice_guard 调用/checkpoint(spec-review-autoplan) 四环节删除;design-voice 恒自跑(回落路径转正);`guard=` 字段从 outside-voice 锚文法移除。
4. lens-metric 落锚指引同步:roster 恒一行 `lens="broad"`,两广审 hits raw=strategy/plan-eng 经 fold 折叠;报告模板段落更新。
5. 广审镜定义真相源:`sdflow-init/assets/snippets/broad-mirrors.md` 新建;`hack/sync_principles.py` 扩展(或同构小脚本)注入 `sdflow-spec-review/SKILL.md` 与 `sdflow-roadmap/SKILL.md` 的 `sdflow:broad-mirror-def` 托管块;`setup.sh --check` 门禁。
6. bundle 规则文档行为面改写:`spec-review.md`(L2 表 autoplan 行、瘦跑注记)、`workflow.md` 阶段二步骤表、`reference/quality-layering.md` 广审载体改述。

- [ ] spec-review SKILL 中 autoplan/gstack 引用归零(grep 验证)
- [ ] 单批 dispatch 结构(strategy/plan-eng/领域/对抗/接地一条消息并行)描述完整
- [ ] step1-broad-review 锚 mode 枚举为 subagent|main-session
- [ ] guard 调用/gstack-review.md/checkpoint(spec-review-autoplan) 环节已删
- [ ] broad-mirrors.md 真相源创建 + 注入脚本扩展 + setup.sh --check 门禁
- [ ] spec-review.md/workflow.md/quality-layering.md 规则文档同步
- [ ] lens-metric roster/模板更新

### Task 3: 守卫脚本退役与矩阵 golden 迁移

**Blocked-by:** 1,2
**R-ID:** R-outside-voice-reuse-guard, R-host-adaptive-execution

守卫脚本删除 + 矩阵全笛卡尔 golden 迁移到 anchor_lint 单工具测试:

1. 原 `test_outside_voice_guard.py` Step 5 跨工具全笛卡尔用例迁移/改造进 anchor_lint 测试侧(枚举域仍读契约机读块,分类逐条断言符合矩阵定义)——**在 guard 文件删除之前完成迁移**。
2. 删除 `sdflow-init/assets/workflow/tools/outside_voice_guard.py` 及其 tests。
3. 全仓 `/usr/bin/python3 -m pytest` 绿。

- [ ] 矩阵全笛卡尔 golden 已迁移到 anchor_lint 测试(含 mutation/边界)
- [ ] outside_voice_guard.py + tests 已删除
- [ ] 全仓 pytest 绿(guard 残留引用归零)

### Task 4: DX 吸收与 roadmap 侧重写

**Blocked-by:** 2
**R-ID:** R-roadmap-planning, R-spec-workflow

DX 领域清单新建 + roadmap review 节重写(镜定义同源注入已在 Task 2 建立):

1. `trigger-catalog.md` 新增 TG-28(developer-facing 交付面触发条件,领域列 devex,spec-review-only,不入 HR-TG)。
2. 新建 `spec-checklists/domains/devex.md`:可判表式条目(TTHW 分档含文本推导规则/错误信息三件套/命名可猜性/默认值/渐进式披露/升级路径/Claude Code Skill DX 清单)。
3. `spec-checklists/domains/frontend.md` 增补 design 镜 litmus/AI-slop 精华 R 项。
4. `sdflow-roadmap/SKILL.md` review 节重写:判定点②(商业化分档)删除;判定留痕总则三判定点改两;恒跑 strategy/plan-eng 双镜(镜职责经 2.5 同源注入托管块承载);失败处置改述(未审待恢复语义不变)。
5. Roadmap sync-only outside voice 接入:site=roadmap-voice,context=design.md Decisions+roadmap.md(>200KB 收敛),run 目录 `.outside-voice/<run-id>/`,前台 --timeout 300 外层 ≥330000ms,⑦ 表映射,失败同族 fallback 带时间预算,task-log 一行 runner/reason_code 留痕。
6. `openspec/INDEX.md` 同步:devex.md 行新增;移除 outside-voice-reuse-guard capability 行与 outside_voice_guard.py 工具行。

- [ ] TG-28 已加入 trigger-catalog.md
- [ ] devex.md 创建且条目为可判表式
- [ ] frontend.md litmus/AI-slop 条目已增补
- [ ] roadmap SKILL 中 autoplan/gstack 引用归零(grep 验证)
- [ ] roadmap review 恒跑双镜 + sync voice 描述完整
- [ ] INDEX.md 同步(新增 devex + 移除 guard 相关行)

### Task 5: 文档 sweep 与验收

**Blocked-by:** 1,2,3,4
**R-ID:** R-spec-workflow, R-workflow-metrics

全面文档 sweep + 验收 + 盲测:

1. 文档面 sweep:`openspec/CONTEXT.md`「镜」词条 autoplan 例句改述;`docs/workflow-skills/gstack-autoplan.md` 降级为非运行时参考;`docs/workflow-skills/sdflow-spec-review.md` 同步;`docs/external-dependencies.md` §5/§8;`WORKFLOW-GUIDE.md`(assets 权威源侧);README(如涉及);`docs/workflow-map.md`(:34 流程描述、:169 guard 工具行);`docs/workflow-overview.md`(:123 CP1 checkpoint 节点)。
2. 关闭 T268(resolved_by=absorb-gstack-autoplan)。
3. 归档盲测(逐声边际贡献):选 3-5 份含 broad 独家 findings 的归档 change,分别单独跑 strategy/plan-eng/design-voice 三声,测旧 broad 独家高危召回率与各声边际独家召回;盲测报告随 change 归档。
4. 最终验收:`grep -rn "autoplan\|gstack" sdflow-spec-review/SKILL.md sdflow-roadmap/SKILL.md sdflow-init/assets/workflow/`(排除 reference/)归零 + 读码确认两 SKILL 无条件调用 gstack 分支;全仓 pytest 绿。

- [ ] CONTEXT.md/docs/workflow-skills/WORKFLOW-GUIDE/external-dependencies/workflow-map/workflow-overview 全部 sweep 完成
- [ ] T268 已关闭
- [ ] 盲测报告落盘(3-5 份归档 change × 3 声)
- [ ] grep 验收归零
- [ ] 全仓 pytest 绿

### Task 6: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4,5
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落 `impl-reports/task6-verification.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

- [ ] 单元测试证据齐全并通过
- [ ] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
