# Tasks: sdflow-ship

> 真相源 = [proposal.md](./proposal.md) + [design.md](./design.md)（§三 gate 决策图 / §五 D1-D7）。全部未勾（ff 生成，实现在阶段三）。
> 需求 ID：**R-SS-1** 编排台账确定性（ADDED）· **R-SS-2** 模型档位映射（ADDED）· **R-SS-3** 阶段三连续+决策协议（MODIFIED）· **R-SS-4** 阶段二串行纪律（MODIFIED）。
> 机队锚定〔adr/0006〕：步序判定全脚本化（ship_gate.py + pytest），模型只执行 gate 判定与每步内部判断。

## 1. ship_gate.py（R-SS-1，先契约后实现，TDD）

- [ ] 1.1 契约头注释定死：D2 双输出（首行人读 + JSON{verdict,next,missing,reason}）、退出码 0/3/4/5、**D5 机器注释行锚点集**〔grill-amendment：`<!-- ship-gate: design-approved -->` / `verify=PASS|FAIL` / `code-review=pass|blocked`，字面查找非正则〕；入参 `--change <name>` + `--root`；只读零副作用〔R-SS-1〕
- [ ] 1.4 〔grill-amendment 新增〕三个报告模板补 ship-gate 锚行：`sdflow-spec-review/SKILL.md` 拍板回写约定（设计门拍板落 `design-approved` 行）、`sdflow-done/SKILL.md` verify-report 模板（结论区落 `verify=PASS|FAIL` 行）、`sdflow-code-review/SKILL.md` 报告格式节（结论区落 `code-review=pass|blocked` 行）——与 ship_gate 头注释同组字面，单测断言双向一致〔R-SS-1〕
- [ ] 1.2 实现 §三决策图全逻辑：pre-flight（报告在+`design-approved` 锚行）→ 5.5 条件（proposal TG-02 标注 grep）→ 6/7（superpowers-plan 存在 + 完成判据〔grill-amendment Q2=B〕：主锚 = git log `checkpoint(task<k>-` 去重任务号集 对 plan `### Task \d+:` 计数 N；辅 = 复选框全勾；皆不可判=UNKNOWN 停）→ 8（`code-review=pass|blocked` 锚行）→ 9（`verify=PASS|FAIL` 锚行）→ final（hand-off+archive+分支态）〔R-SS-1〕
- [ ] 1.3 pytest 全盘面态（tmp_path 构造 change 目录 + `git init` 提交序模拟）：未过门拒跑 / 拍板锚在则过 / TG-02 命中与否 / plan 缺→next=writing-plans / checkpoint 标签集不齐→继续实现（含勿重派任务号集输出）/ 双通道不可判→UNKNOWN / blocker→exit4 / verify FAIL→exit5 / PASS→next=done / 全通→SHIPPED / **D9 新鲜度四态：陈旧 FAIL→重验不卡死、陈旧 PASS→重跑不放行、无锚行产物→步进行中、报告后仅 openspec/ 提交→保鲜**；锚行字面断言〔R-SS-1〕
- [ ] 1.5 〔grill-amendment D9 新增〕gate 新鲜度实现：定位报告文件最后提交（`git log -1 --format=%H -- <path>`）→ 检查其后是否存在触及 `openspec/` 之外路径的提交（`git log <sha>..HEAD --name-only` 过滤）→ 陈旧/保鲜判定进 JSON 输出；`--amend`/rebase 改写不设防（头注释记录残余）〔R-SS-1〕

## 2. sdflow-ship skill（R-SS-3）

- [ ] 2.1 新建 `sdflow-ship/SKILL.md`：frontmatter（name/description 触发词：「ship 这个 change」「阶段三跑到 merge」「过完设计门了，跑起来」「/sdflow-ship」等）；正文 = chain 序列 + **每步前后 MUST 调 ship_gate 并遵判定**（禁 prose 步序）+ 门禁上抛话术（exit 3/4/5 各自的停法与转述格式）+ **D8 零 git 声明与 merge 意图透传句 + SHIPPED 摘要模板（含 push 提醒/toolkit 激活句）**〔grill-amendment〕+ 不越两人类点声明 + **D9 resume/暂停/人机同权节**（重调即续、gate 不辨产者、手改锚行=显式越权留痕、实现中断把已完成任务号集传 SDD 勿重派）〔R-SS-1/3〕
- [ ] 2.2 D3 决策协议节（T10 认领）：三级协议全文 + 「禁自评置信唯一依据」+ 复核记录进 code-review-report 的格式约定〔R-SS-3〕
- [ ] 2.3 权威源 `assets/workflow/workflow.md`：阶段三步骤表加编排入口行（`/sdflow-ship {change}` 一次驱动 5.5→9；手动逐步为 reference）；决策 4 按 D3 改写（去"有把握自动选"）；步 6 prompt 的"逐任务 checkpoint-commit"升格为**显式 `task<N>-` 标签约定**（gate 完成判据主锚，grill-amendment Q2=B）〔R-SS-3〕

## 3. model-tiers（R-SS-2，T11 认领）〔grill-amendment Q4=C：规则文件真相源 + config 覆盖〕

- [ ] 3.1 新建 `assets/workflow/model-tiers.md`（~20 行规则文件）：三档定义与职责清单（强档=verify/对抗裁决/final 终审；中档=领域镜/生成/实现；弱档=纯机械步）+ canonical 缺省（strong: opus / mid: sonnet / light: haiku）+ adr/0006(c) 机队锚定措辞；`snippets/index-section.md` 规则表加行（INDEX 经 update --dev 同步）〔R-SS-2〕
- [ ] 3.2 `assets/workflow/config.template.yaml` 加**可选覆盖段** `model-tiers`（注释：真相源=规则根 model-tiers.md，此段仅 per-repo 覆盖映射，缺省勿填）〔R-SS-2〕
- [ ] 3.3 四个编排 SKILL.md（sdflow-ship/done/spec-review/code-review）模型选择节改引用句：「档位与缺省见规则根 `model-tiers.md`（resolver 解析）；config.yaml model-tiers 段可覆盖」——**零内联模型名**；grep 断言四文件模型节无裸模型名残留（引用句除外）〔R-SS-2〕

## 4. T20 顺路（R-SS-4）

- [ ] 4.1 `sdflow-spec-review/SKILL.md` Step2 首句加 MUST 串行句 + 历史并行补救句（design D6 全文）〔R-SS-4〕

## 5. 测试与断言

- [ ] 5.1 全量 `python3 -m pytest -q` 全绿无 warning（233 + ship_gate 新用例）
- [ ] 5.2 grep 断言：workflow.md 无"有把握自动选"旧句；四 SKILL.md 模型节引用 model-tiers；spec-review Step2 含 MUST 串行句——命令与输出留档 change 目录 `assert-log.md`

## 6. 文档收尾与债务闭环

- [ ] 6.1 README Skills 列表加 sdflow-ship 行；ROADMAP：`opsx-ship-orchestrator` 行更名 `sdflow-ship`（materialize 注记+状态推进）；`adr/0004` 按其自带条款加标题注记（"落地名 sdflow-ship，见 adr/0007 命名规范"一行，不改历史正文）
- [ ] 6.2 债务闭环：T10/T11 set-status DONE（evidence=本 change commit + 文件:行）、T20 set-status DONE（evidence 同）；reindex 刷新 INDEX/批次
- [ ] 6.3 `update --dev --root .` 同步 instance；hand-off 预置：真实激活 = merge+push 后新会话 `/sdflow-upgrade`（沿 rebrand 模式），首次真实 ship 演练建议挑批次 T21-T24 的收尾小 change 当试车对象
