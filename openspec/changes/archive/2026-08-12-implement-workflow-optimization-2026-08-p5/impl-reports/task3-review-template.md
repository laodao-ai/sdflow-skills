# Task 3 实现报告 · sdflow-spec-review 报告模版三问小节 + 锚行

对应 `tasks.md` 1.3（Requirement: GQ）。任务简介见
`impl-reports/task3-brief.md`；design 精确措辞见 `design.md` Da/Db；
spec 精确措辞见 `specs/spec-workflow/spec.md` Requirement「GQ 设计门报告拍板三问」。

## 前置确认

`git log --oneline -- sdflow-init/assets/workflow/tools/anchor_lint.py` 显示
task 1.1（`ANCHOR_PREFIXES` + `check_gate_questions()`）与 task 1.2（七组契约测试）
已由前序 commit `5b8e8e88 feat(anchor_lint): gate-questions 拍板层机验检查 + 七组契约测试`
完成——`sdflow-init/assets/workflow/tools/anchor_lint.py:686-717` 已实现
`check_gate_questions(report_text, layer, findings)`，`ANCHOR_PREFIXES`（line 77）已登记
`"<!-- sdflow:gate-questions v1"`。本 Task 3 仅涉及 SKILL.md 报告模版层，不触碰
`anchor_lint.py`。

## 改动

只改 `sdflow-spec-review/SKILL.md`（1 file, +19/-2）：

1. **决策登记区顶部新增「拍板三问」小节模版**（`sdflow-spec-review/SKILL.md:356-378`，
   紧接原「报告决策登记区格式」标题，置于既有决策登记区 ASCII 框**之前**）：
   - 三行固定问题：`Q-scope`（范围划界，锚 proposal Non-Goals/Out-of-scope）、
     `Q-deps`（依赖/顺序，锚 tasks 任务边界与 Blocked-by）、`Q-risk`（风险赌注，锚
     `sdflow:hr-tg` 的 hit/declared + 对策条目）——措辞与顺序逐字对齐
     spec.md GQ Requirement 与 design Da。
   - 每问 = 问题 + 「自答：锚 XXX——<一句话，指回证据位置>」+ 人勾选位
     `[ ] 认  [ ] 不认`。
   - 紧邻小节放锚行 `<!-- sdflow:gate-questions v1 q="scope,deps,risk" -->`
     （独占一行，fence 外），随后原样保留既有决策登记区框（自动决策/需拍板/已裁掉）。
   - 框外补三句说明：三问只落 spec-review 报告、code-review MUST NOT 要求含；
     锚行位置与去重纪律；机验声明收窄（锚存在 + q 值逐字，三问正文在场与否无机械保证）。
2. **锚行自检步（`SKILL.md:350`）补充 gate-questions 纳入说明** + **problem/cause/fix
   转译**（`SKILL.md:351`，新增子条目）：
   - 主句「脚本机验四类 v1 锚存在性」后加括注：layer=spec-review 时另加
     `gate-questions` 拍板层声明锚，恒须、不受 `metrics.enabled` 门控（design Db）——
     避免遗留「四类」表述在新锚加入后失真。
   - 新增子条目：lint 本身仍输出既有 `[anchor_lint] VIOLATION` 结构化格式
     （`missing-gate-questions` / `duplicate-gate-questions-anchor` / `missing-field` /
     `q-value-mismatch`），本条在 SKILL 层补充人读 problem/cause/fix 转译，fix 明确指回
     「报告决策登记区格式」的「拍板三问」小节模版位置。

## grep 同步核对（design scope-check 表逐行）

用 `~/.sdflow/hack/resolve-workflow.sh` 解析出的 canonical 根（本机指向运行 checkout
`~/.skills/sdflow-skills`）与本仓开发 checkout 的 `sdflow-init/assets/workflow/` 两处均
grep 了 `决策登记区|报告模版|spec-review-report|需拍板|拍板|gate-questions|自动决策|已裁掉`：

- `spec-review.md`、`workflow.md`、`WORKFLOW-GUIDE.md`、`trigger-catalog.md`、
  `reference/Spec_Quality_Methodology.md` 命中的均为**泛引用**（如「决策登记进报告」
  「决策登记区已摊开选项」一类流程性提及）或与本次改动无关的其他 ASCII 框（trigger
  catalog 目录导览框、方法论三层关系框），**均非「决策登记区/报告结构」的完整模版复述**。
- 结论：**bundle 内无第二处需要同步的报告结构描述**——`anchor_lint.py` 内新增的
  `check_gate_questions` 头注释（task 1.1 已含）是唯一另一处提及 gate-questions 的
  bundle 文件，且其内容是机验逻辑注释，非报告结构模版，语义与 SKILL.md 模版一致
  （均指向「决策登记区顶部、紧邻三问小节」），无需改动。

## 验证

- `python3 hack/sync_principles.py --check` → `✅ 28 个投放面全部与真相源一致` —
  `sdflow:principles` 托管块未被触碰。
- `python -m pytest hack/tests/ -q`：374 passed, 8 failed, 8 skipped, 1 deselected。
  8 个失败（`test_render_review_prefix.py` 7 个 + `test_check_dependencies.py` 1 个）
  经 `git stash` 验证为**本机 Windows 环境预存问题**（`SDFLOW_HOME 非绝对路径`
  path 处理 + PATH 探测未剔除已装 yq），**与本次 SKILL.md 文本改动无关**——stash 后
  同一组测试同样失败（`8 failed, 6 passed`，`test_render_review_prefix.py` 单文件跑）。
  本次改动引入 0 个新失败。

## 验收自评

- [x] 三问小节模版加入 Step4 报告条款（决策登记区顶部）——`SKILL.md:356-378`
- [x] 锚行加入（紧邻三问小节）——`SKILL.md:368`
- [x] 自检步报错文案含 problem/cause/fix 指引——`SKILL.md:351`
- [x] bundle 内规则文件报告结构描述已同步（确认无需同步，见上「grep 同步核对」）

## 备注

- 未触碰 `anchor_lint.py`（task 1.1/1.2 已由前序 commit 完成，超出本票范围）。
- 未改动决策登记区既有 ASCII 框内容（自动决策/需拍板/已裁掉三态原样保留），符合
  design「拍板三问是增量锚，不改变既有锚检查语义」的边界。
- 本轴（Standards）自审：Markdown-only 改动，无代码路径；未引入新终端/脚本行为。
