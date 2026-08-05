# Task 4: 重写 workflow bundle 核心文档为单轨线性流程 — impl-report

## 做了什么

### 1. `sdflow-init/assets/workflow/workflow.md`

- §一 流程图改为唯一线性路径：`opsx:explore(条件) → /sdflow-spec → /clear → sdflow-spec-review → HARD-GATE → /clear → /sdflow-ship[...]`，
  删除分支 A/B 两个 box、wayfinder chart 节点、embedded-test-sop 节点。
- §二 步骤表从 12 行（0/1/1b/2/3/4/5/5.5/6/7/8/9）精简到 8 行（1~8），删除旧分支 B 专属行
  （1b wayfinder、2 opsx:ff、3 grill-with-docs）与 5.5（embedded-test-sop）；步 5（原 writing-plans）
  的规则列改写为"缺省 tickets / 显式 superpowers 才走此行"，修正了它此前遗留的"必跑"过时措辞
  （Task 2 翻转缺省后这行本已不准确）。
- §三.2（G1）正文精简为设计里给定的那条规则（阶段内部不清 + 两处交界 SHALL 清 + 各自一句理由），
  完整推导移入新增的"附录 A：G1 完整分析"一节（DOC-1）。
- §三.9 删除 embedded-test-sop 引用。
- §五/§六 清理分支 A/B、wayfinder、grill 独立步骤等引用。
- §四对称表 "③过程→grill" 改为 "③过程→拷问"（拷问现内建于 sdflow-spec 相位 B，不再是独立 grill 步）。

### 2. `sdflow-init/assets/workflow/generation-process.md`

- §四重写为"推荐流水线（唯一入口）"：删除分支 A/B 双标题结构、四入口选择规则整节；
  流程图改为 `opsx:explore(条件) → /sdflow-spec → HARD-GATE → /sdflow-ship`。
- 新增"自动触发规则（explore → sdflow-spec）"子节，原文照抄 design.md D5 决策文本：
  人示意收敛（"开搞"/"做吧"/"开 change"）或用户描述需求即自动 invoke；模型 MUST NOT 自主判断
  "该开 change 了"；触发方式改变不影响相位 B 拷问协议。
- 新增"何时跳过 explore"子节（问题已清晰则直接进 sdflow-spec）。
- `project-local schema 的作用边界`节保留，措辞从"应提示人触发"改为"应按上方自动触发规则决定
  直接 invoke 或提示人触发"，与新自动触发能力对齐。
- §五 skill 表只保留 `/sdflow-spec` 与 `opsx:explore` 两行，删除 brainstorming / grill-me /
  grill-with-docs 三行（不再是流程内被引导的步骤；skill 本体未删，仅去除流程文档引导，符合
  Non-Goals）。
- 删除整节"grill-with-docs 路径适配"（该节纯是分支 B 专属技能的使用指南，随分支 B 一并退役）。
- §七（原§八）检查清单删除"分支 A 单入口 / 旧三步例外 / grill-with-docs 路径 / brainstorming 瘦跑"
  四项，改为围绕唯一入口 + 自动触发的三项检查。

### 3. `sdflow-init/assets/workflow/ff-generation-constraints.md`

- 删除整节"wayfinder→ff 衔接契约"（≈22 行，含 map 读取规则、TG 前置、回链锚格式）。
- "切片建议"节标题与正文改写：触发条件从"仓开 `impl-pipeline: tickets`"改为"仓走 tickets 管线——
  缺省即命中，除非显式 `impl-pipeline: superpowers`"，反映 Task 2 已翻转的缺省值。
- 保留"MUST NOT 使用 `wayfinder-resolved:` 前缀"这条约束（该前缀仍被 roadmap wayfinding 使用，
  措辞改为指向 `openspec/roadmaps/{name}/footage/`，不再依赖已删除的"上节"wayfinder→ff 契约）。
- FF-0 hook 说明行删除"分支 A"/"分支 A 与分支 B 同样受管辖"措辞，改为"所有入口无一绕得过"。
- D-1~D-6 定义表、约束集设计判据、附录 prompt 片段等 D 约束核心内容未改动（Non-Goals 明确不改）。

### 4. `hack/gen_workflow_guide.py` + `WORKFLOW-GUIDE.md`

- `STEP_FILES` 字典删除 `"2": "step2-ff"`、`"3": "step3-grill"`、`"5.5": "step5_5-embedded-sop"`
  三个已删除文件的映射；键重编号为 `{"1","3","5","6","7","8"}` 对齐新步骤表（`"2"` sdflow-spec 与
  `"4"` HARD-GATE 无独立 prompt 文件，沿用原有"无映射走 prompt_cell 文本"分支，不需要 dict 项）。
- 运行 `python3 hack/gen_workflow_guide.py --write` 重新生成，`--check` 验证一致（见下方证据）。

### 5.（附带修复，非 brief 要求，但直接由本次编辑触发）`hack/tests/test_workflow_split.py`

跑测试时发现两个断言已随本次改动**理所当然地**过期，且完全在 workflow.md 自身范围内（未涉及
Task 5 owned 的 CLAUDE.md/claude-section.md/docs），按通则④"撞到相关 bug 立即 fold"就地修复：

- `test_prompts_are_not_inlined_back_into_the_table` 的 fingerprints 字典里有一条指向
  `prompts/step3-grill.md`——该文件已在 Task 3 被删除，测试本身会在 `Path.read_text()` 处报
  `FileNotFoundError`。删除这一条（保留 step6/step8 两条，回归覆盖仍然有效）。
- `test_table_stays_six_columns` 硬编码 `assert len(rows) >= 9`——新表只有 8 行（Task 4 的
  预期结果，不是缺陷），改为 `>= 6` 并加注释说明 8 行构成。

## 未做 / 有意搁置

`hack/tests/test_canonical_entry_sync.py` 里另有 **5 个测试仍红**，未在本 Task 修复：

- `test_generation_process_has_two_branches`
- `test_generation_process_states_entry_selection_rule`
- `test_generation_process_keeps_legacy_path_alive`
- `test_generated_guide_reflects_the_new_entry`
- `test_human_side_and_canonical_use_the_same_wording`

原因：这 5 个测试断言的是**被本 change 明确要求删除的旧内容**（"分支 A/分支 B"字样、四入口选择
规则、"旧三步仍是合法路径"、旧步骤 0 编号、以及要求 generation-process.md 与 `claude-section.md`
"同串"的跨文件断言）。其中最后一个（`test_human_side_and_canonical_use_the_same_wording`）直接
依赖 `sdflow-init/assets/snippets/claude-section.md` 的内容——该文件是 **Task 5** 的责任范围
（tickets.md Task 5："更新 `claude-section.md`：删分支 B/wayfinder/grill-with-docs/手动限制段落，
加 sdflow-spec 自动触发规则……"），Task 5 尚未执行，此刻去改这个测试等于在猜 Task 5 最终写法，
属于越界。其余 4 个纯测 generation-process.md/WORKFLOW-GUIDE.md 自身的旧措辞，本可以顺手删除，
但考虑到它们与 Task 5 要处理的 CLAUDE.md/docs 是**同一批"分支 A/B 残留引用扫描"**（tickets.md
Task 6 的验收项之一：`grep -rn "...分支 B..."` 残留扫描），留给 Task 5/6 一次性处理更不容易漏项，
故未动。**如实标注：这不是"忘了改"，是有意留给下游任务**。

## 证据

```
$ python3 hack/gen_workflow_guide.py --check
[gen_workflow_guide] ✅ WORKFLOW-GUIDE.md 与单一源一致

$ /usr/bin/python3 -m pytest hack/tests/test_workflow_split.py -q
5 passed in 0.01s

$ /usr/bin/python3 -m pytest hack/tests/test_workflow_split.py hack/tests/test_canonical_entry_sync.py \
    hack/tests/test_checkpoint_slug_coverage.py sdflow-init/tests/test_init.py -q
5 failed, 113 passed in 1.68s
# 5 failed = 上述"未做/有意搁置"里列出的 test_canonical_entry_sync.py 5 个用例，均属预期、待 Task 5 处理

$ grep -n "wayfinder\|分支 A\|分支A\|分支 B\|分支B\|embedded-test-sop\|RUN_SOP" \
    sdflow-init/assets/workflow/workflow.md sdflow-init/assets/workflow/generation-process.md \
    sdflow-init/assets/workflow/ff-generation-constraints.md
sdflow-init/assets/workflow/ff-generation-constraints.md:46:切片建议内容 MUST NOT 使用 `wayfinder-resolved:` 前缀——该前缀留给 roadmap wayfinding 效力范围内
# 唯一命中是有意保留的"MUST NOT 混用"警示行，不是残留引用
```

## 验收对照（tickets.md Task 4 复选框）

- [x] `workflow.md` 流程图为线性单轨，步骤表精简，G1 分析在附录
- [x] `generation-process.md` 为单入口描述，含 explore→sdflow-spec 自动衔接规则
- [x] `ff-generation-constraints.md` 无 wayfinder 衔接契约，切片建议反映缺省=tickets
- [x] `WORKFLOW-GUIDE.md` 已通过 `python3 hack/gen_workflow_guide.py --write` 重新生成

（复选框本身按纪律不在本报告代勾 tickets.md——由执行模式在双轴审通过后统一补打。）
