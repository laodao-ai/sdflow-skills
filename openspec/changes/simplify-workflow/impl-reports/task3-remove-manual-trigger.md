# Task 3 impl-report：解除 sdflow-spec 手动触发限制并删除旧 workflow prompts

## 改动

1. **`sdflow-spec/SKILL.md`**
   - 删除 frontmatter 行 `disable-model-invocation: true`。
   - description 末句「由人显式触发（`disable-model-invocation: true`）。Trigger with /sdflow-spec。」
     改为「Trigger with /sdflow-spec。」。
   - 全文 grep `disable-model-invocation|由人显式触发|只能人触发|人手动|唤不起` 复核，改动后无残留。

2. **删除三个旧步骤 prompt 文件**（`git rm`）：
   - `sdflow-init/assets/workflow/prompts/step2-ff.md`
   - `sdflow-init/assets/workflow/prompts/step3-grill.md`
   - `sdflow-init/assets/workflow/prompts/step5_5-embedded-sop.md`

3. **删除回归门测试**（`git rm`）：
   - `sdflow-init/tests/test_grill_handoff.py`

## 验收对照（tickets.md Task 3 复选框）

- [x] `sdflow-spec/SKILL.md` frontmatter 无 `disable-model-invocation: true`
- [x] `sdflow-spec/SKILL.md` description 无手动触发限制语言
- [x] `prompts/step2-ff.md`、`prompts/step3-grill.md`、`prompts/step5_5-embedded-sop.md` 已删除
- [x] `sdflow-init/tests/test_grill_handoff.py` 已删除

（本报告仅记录工作产物，不代表实现期打勾——tickets.md 复选框由双轴审通过后的执行模式补打，非
implementer 自行勾选。）

## 范围边界

- 本票不改 `sdflow-init/assets/workflow/workflow.md`、`generation-process.md` 等权威源文档里对
  分支 B / 四入口选择规则 / grill-with-docs 的引用——tickets.md 明确该项属 Task 4（Blocked-by:
  1,2,3）。同理不改 `CLAUDE.md`「旧入口 sunset 条件」段——属 Task 5（Blocked-by: 4）。
- 三个旧入口本身（`opsx:ff`、`opsx:explore`、`grill-with-docs`）不删除，符合 Global Constraints
  第 15 条（两个是 CLI 生成物、一个在仓外）——本票也未触碰它们的文件。
- `sdflow-init/assets/workflow/prompts/` 目录下未删除的文件（`step1-explore.md`、
  `step4-spec-review.md`、`step6-writing-plans.md`、`step7-subagent-dev.md`、
  `step8-code-review.md`、`step9-done.md`）保留不动——brief 只点名删三个。

## 已知遗留（留给 Task 4/5/6 处理，非本票 blocker）

- 全仓仍有对已删文件路径/`disable-model-invocation`字符串的引用（如
  `sdflow-init/assets/workflow/workflow.md` 提及 `step3-grill.md`、`CLAUDE.md` 引用
  `grill-with-docs` 手动触发段落），Task 6 的「残留引用扫描」步骤会核对；这些不在 Task 3 的
  Global Constraints 授权范围内，未主动改动。
- 未运行 `bash setup.sh`（该项由 Task 1 的 embedded-test-sop 删除引出，Task 6 会统一跑一次并核验
  `~/.claude/skills/` 无孤儿链接）；本票删除的是 `sdflow-init/assets/workflow/prompts/`（bundle
  内部资产，非顶层 skill 目录），setup.sh 不感知其存在，故不需要为本票单独跑。

## 测试

- 本票为纯删除/frontmatter 编辑，无新代码，未新增/修改测试。
- `/usr/bin/python3 -m pytest sdflow-init/tests/ -q`（含删除 `test_grill_handoff.py` 后的剩余套件）：
  **782 passed, 4 skipped in 193.82s**，exit code 0，无失败无残留报错。

## 工作目录说明

本次任务在独立 git worktree（`worktree-agent-ac0f3d9ce80ba64ce` 分支）中执行，该分支的 fork 点
（`2e159e4`）是 `feat/simplify-workflow` 的祖先且未被后续提交触碰过本票涉及的四个文件（已用
`git diff HEAD feat/simplify-workflow -- <paths>` 核实无差异），故本 worktree 上的改动可直接合并
回 `feat/simplify-workflow`，无冲突风险。
