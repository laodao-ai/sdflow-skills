# Tasks: sdflow-ship

> 真相源 = [proposal.md](./proposal.md) + [design.md](./design.md)（§三 gate 决策图 / §五 D1-D7）。全部未勾（ff 生成，实现在阶段三）。
> 需求 ID：**R-SS-1** 编排台账确定性（ADDED）· **R-SS-2** 模型档位映射（ADDED）· **R-SS-3** 阶段三连续+决策协议（MODIFIED）· **R-SS-4** 阶段二串行纪律（MODIFIED）。
> 机队锚定〔adr/0006〕：步序判定全脚本化（ship_gate.py + pytest），模型只执行 gate 判定与每步内部判断。

## 1. ship_gate.py（R-SS-1，先契约后实现，TDD）

- [ ] 1.1 契约头注释定死：D2 双输出（首行人读 + JSON{verdict,next,missing,reason}）、退出码 **0/3/4/5/6（6=UNKNOWN，独立语义不复用）**、**verdict×exit×next 输出契约表（含 SHIPPED/SKIP/UNKNOWN 全枚举）**〔spec-review-amendment D3〕、**D5 机器注释行锚点集**〔grill-amendment：`<!-- ship-gate: design-approved -->` / `verify=PASS|FAIL` / `code-review=pass|blocked`，字面查找非正则〕；头注释另声明两条已知不覆盖：openspec/workflow/ 规则漂移不触发陈旧、rebase 可伪造保鲜（接受并记录；实现禁用 --first-parent）〔spec-review-amendment D11〕；入参 `--change <name>` + `--root`；只读零副作用〔R-SS-1〕
- [ ] 1.4 〔grill-amendment 新增〕三个报告模板补 ship-gate 锚行：`sdflow-spec-review/SKILL.md` 拍板回写约定（**协议明确化：设计门拍板发生后主 session MUST 立即将 `design-approved` 锚行写入 spec-review-report.md——写入者=主 session、触发点=用户批准动作；ship_gate exit 3 提示文案含"若拍板已发生请补锚（显式越权留痕）"**〔spec-review-amendment D2，替代"拍板本就回写"的不成立假定〕）、`sdflow-done/SKILL.md` verify-report 模板（结论区落 `verify=PASS|FAIL` 行）、`sdflow-code-review/SKILL.md` 报告格式节（结论区落 `code-review=pass|blocked` 行）——与 ship_gate 头注释同组字面，单测断言双向一致〔R-SS-1〕
- [ ] 1.2 实现 §三决策图全逻辑：pre-flight（报告在+`design-approved` 锚行）→ 5.5 条件（proposal TG-02 标注 grep——**字面子串 "TG-02" 不含括号**，归档实例为全角 `〔TG-01：…〕`/`（TG-20）` 混用〔spec-review-amendment D10〕）→ 6/7（superpowers-plan 存在 + 完成判据〔grill-amendment Q2=B；窗口下界待 Q2 拍板〕：主锚 = git log `checkpoint(task<k>-` 去重任务号集 对 plan `### Task \d+:` 计数 N，**标题命中 0 → UNKNOWN**〔D7〕；辅 = 复选框全勾；皆不可判=UNKNOWN 停）→ 8（`code-review=pass|blocked` 锚行）→ 9（`verify=PASS|FAIL` 锚行）→ final（hand-off+archive+**分支已并判定：`git log {base}..HEAD` 为空或分支已删=已并、detached HEAD=UNKNOWN**〔D6〕）；**同一报告并存冲突锚行（如 PASS 与 FAIL 同在）→ UNKNOWN 点名冲突行**〔D4〕〔R-SS-1〕
- [ ] 1.3 pytest 全盘面态（tmp_path 构造 change 目录 + `git init` 提交序模拟）：未过门拒跑 / 拍板锚在则过 / TG-02 命中与否 / plan 缺→next=writing-plans / checkpoint 标签集不齐→继续实现（含勿重派任务号集输出）/ 双通道不可判→UNKNOWN / blocker→exit4 / verify FAIL→exit5 / PASS→next=done / 全通→SHIPPED / **D9 新鲜度四态：陈旧 FAIL→重验不卡死、陈旧 PASS→重跑不放行、无锚行产物→步进行中、报告后仅 openspec/ 提交→保鲜**；**新增态〔spec-review-amendment〕：多锚冲突→UNKNOWN〔D4〕、plan 标题命中 0→UNKNOWN〔D7〕、窗口污染态（main 遗留 task 标签 + merge 带入外部标签，待 Q2 拍板后按窗口规则断言——tmp_path 干净仓测不出，须构造历史污染 fixture）、design-approved 后大量非 openspec 提交仍保鲜（待 Q1 拍板后定稿反例断言）、未提交报告态（待 Q3）**；锚行字面断言〔R-SS-1〕
- [ ] 1.5 〔grill-amendment D9 新增〕gate 新鲜度实现：定位报告文件最后提交（`git log -1 --format=%H -- <path>`）→ 检查其后是否存在触及 `openspec/` 之外路径的提交（`git log <sha>..HEAD --name-only` 过滤）→ 陈旧/保鲜判定进 JSON 输出；`--amend`/rebase 改写不设防（头注释记录残余）〔R-SS-1〕

## 2. sdflow-ship skill（R-SS-3）

- [ ] 2.1 新建 `sdflow-ship/SKILL.md`：frontmatter（name/description 触发词：「ship 这个 change」「阶段三跑到 merge」「过完设计门了，跑起来」「/sdflow-ship」等——**只收含 change 语境短语，不收裸"ship/发布"，避让 gstack /ship 撞车**〔spec-review-amendment D9〕）；**同一 invocation 内同一步重跑一次仍无锚行 → UNKNOWN 上抛人工，禁无限静默循环**〔D5 熔断〕；正文 = chain 序列 + **每步前后 MUST 调 ship_gate 并遵判定**（禁 prose 步序）+ 门禁上抛话术（exit 3/4/5 各自的停法与转述格式）+ **D8 零 git 声明与 merge 意图透传句 + SHIPPED 摘要模板（含 push 提醒/toolkit 激活句）**〔grill-amendment〕+ 不越两人类点声明 + **D9 resume/暂停/人机同权节**（重调即续、gate 不辨产者、手改锚行=显式越权留痕、实现中断把已完成任务号集传 SDD 勿重派）〔R-SS-1/3〕
- [ ] 2.2 D3 决策协议节（T10 认领）：三级协议全文 + 「禁自评置信唯一依据」+ 复核记录进 code-review-report 的格式约定〔R-SS-3〕
- [ ] 2.3 权威源 `assets/workflow/workflow.md`：阶段三步骤表加编排入口行（`/sdflow-ship {change}` 一次驱动 5.5→9；手动逐步为 reference）；决策 4 按 D3 改写（去"有把握自动选"）；步 6 prompt 的"逐任务 checkpoint-commit"升格为**显式 `task<N>-` 标签约定**（gate 完成判据主锚，grill-amendment Q2=B）——**注入点钉死在 plan 生成层：writing-plans 派发 args 须要求 plan 每任务的 commit 步显式写 `checkpoint-commit.sh task<N>-<slug>`，由 implementer 子代理自己执行（SDD implementer 返回前已自行 commit，主 session 事后跑脚本必空转跳过；footprint/rebrand 先例已验证此注入路径可产出标签）**〔spec-review-amendment D1〕〔R-SS-3〕

## 3. model-tiers（R-SS-2，T11 认领）〔grill-amendment Q4=C：规则文件真相源 + config 覆盖〕

- [ ] 3.1 新建 `assets/workflow/model-tiers.md`（~20 行规则文件）：三档定义与职责清单（强档=verify/对抗裁决/final 终审；中档=领域镜/生成/实现；弱档=纯机械步）+ canonical 缺省（strong: opus / mid: sonnet / light: haiku）+ adr/0006(c) 机队锚定措辞；`snippets/index-section.md` 规则表加行（INDEX 经 update --dev 同步）〔R-SS-2〕
- [ ] 3.2 `assets/workflow/config.template.yaml` 加**可选覆盖段** `model-tiers`（注释：真相源=规则根 model-tiers.md，此段仅 per-repo 覆盖映射，缺省勿填）〔R-SS-2〕
- [ ] 3.3 四个编排 SKILL.md（sdflow-ship/done/spec-review/code-review）模型选择节改引用句：「档位与缺省见规则根 `model-tiers.md`（resolver 解析）；config.yaml model-tiers 段可覆盖」——**零内联模型名**；grep 断言**四文件全文**（非仅模型节）无裸模型名残留（引用句白名单）——sdflow-done 派发 prompt 内 `model: sonnet/haiku` 行（:61/:206 等）与 sdflow-code-review 模型表（:7/:30/:95 附近）均在断言面内〔spec-review-amendment D8〕〔R-SS-2〕

## 4. T20 顺路（R-SS-4）

- [ ] 4.1 `sdflow-spec-review/SKILL.md` Step2 首句加 MUST 串行句 + 历史并行补救句（design D6 全文）〔R-SS-4〕

## 5. 测试与断言

- [ ] 5.1 全量 `python3 -m pytest -q` 全绿无 warning（233 + ship_gate 新用例）
- [ ] 5.2 grep 断言：workflow.md 无"有把握自动选"旧句；四 SKILL.md 模型节引用 model-tiers；spec-review Step2 含 MUST 串行句——命令与输出留档 change 目录 `assert-log.md`

## 6. 文档收尾与债务闭环

- [ ] 6.1 README Skills 列表加 sdflow-ship 行；ROADMAP：`opsx-ship-orchestrator` 行更名 `sdflow-ship`（materialize 注记+状态推进）；`adr/0004` 按其自带条款加标题注记（"落地名 sdflow-ship，见 adr/0007 命名规范"一行，不改历史正文）
- [ ] 6.2 债务闭环：T10/T11 set-status DONE（evidence=本 change commit + 文件:行）、T20 set-status DONE（evidence 同）；reindex 刷新 INDEX/批次
- [ ] 6.3 `update --dev --root .` 同步 instance；hand-off 预置：真实激活 = merge+push 后新会话 `/sdflow-upgrade`（沿 rebrand 模式），首次真实 ship 演练建议挑批次 T21-T24 的收尾小 change 当试车对象
