# Task 2 实现报告：generation-process 收史 + ff-generation-constraints 外壳更新

## 环境说明（非任务内容，供追溯）

本 agent 的隔离 worktree（`.claude/worktrees/agent-aafdfca12e852ee7a`）起始分支
`worktree-agent-aafdfca12e852ee7a` 落在 `49aa4ee`，不含 `fix-workflow-bundle-staleness`
change 的任何产物（含 `impl-reports/task2-brief.md`）。核实该 worktree 分支是
`feat/fix-workflow-bundle-staleness`（HEAD=`27e29e6`）的纯祖先、无本地未提交改动后，
执行 `git merge feat/fix-workflow-bundle-staleness --ff-only`（快进合并，非重写历史）
把该 change 的四件套 + tickets.md + impl-reports 拉进本 worktree，随后按 brief 施工。

## 改动位点（before → after）

### 1. `sdflow-init/assets/workflow/generation-process.md`

**§二标题 + 表格**（:21，`[A8]`）：
- Before: `## 二、③ = 三种对话相位 + 四个 skill`，三行表（发散/`opsx:explore`、收敛/`brainstorming`、
  对抗压测/`grill-me`·`grill-with-docs`）+ 三节点 ASCII 图。
- After: `## 二、③ = 两个相位 + 两个 skill`，两行表（发散/`opsx:explore`、
  收敛+拷问+生成/`/sdflow-spec`）+ 两节点 ASCII 图，产物列写「四件套 + decision-memo.md + HARD-GATE」。

**§三整节**（`[A8]` 同批）：
- Before：完整保留「brainstorming vs grill」5 行对比表 + 结论段（约 12 行）。
- After：标题改为 `## 三、①② 固化后 ③ 收窄到 R 桶（历史论证见 workflow-history.md A5）`，
  正文压成 3 行指路段，指向 `workflow-history.md` A5；§四编号未重排（原本就没有依赖章节号的
  上下文，仅内容收窄）。

**§四流水线图**（`[A11]`）：
- 在 `/sdflow-spec` 产物行与 `HARD-GATE 批准` 行之间插入一行：
  `        ↓ /clear → /sdflow-spec-review（阶段二设计审）`
- 其余行（`opsx:explore` 起、`/sdflow-spec` 起、`HARD-GATE` 起、`/sdflow-ship` 起）逐字未动。

**§四自动触发规则 ②**（`[A12]`）：
- Before: `② 用户描述需求且判断需要开 change 时。`
- After: `② 用户描述需求且需要开 change 时。`
- 相邻的「模型 MUST NOT 自主判断『该开 change 了』」一行（presence 锚之一）未触碰。

**§六**（措辞替换）：
- Before: `**grill 落的产物回流标准**：ADR ↔ BASE-12、术语 ↔ BASE-09、代码核验 ↔ D-1。grill 是这些
  R 项的**对话执行器**。`
- After: `**拷问落的产物回流标准**：ADR ↔ BASE-12、术语 ↔ BASE-09、代码核验 ↔ D-1。`/sdflow-spec`
  相位 B 拷问是这些 R 项的**对话执行器**。`

### 2. `sdflow-init/assets/workflow/workflow-history.md`

新增 `### A5 · 「③ 生成过程」从三相位四 skill 收窄为两相位两 skill（sdflow-spec 吸收
brainstorming + grill）` 条目，承接 §三被移除的完整论证（三相位定义、grill 逐项命中的
标准/锚对比表、原结论段），并追加「后续演进」段说明 `/sdflow-spec` 如何把发散+对抗+生成
收进一个入口、拷问结构性前置于成文，以及本 change 据此现行化 §二/移史 §三 的因果链。

### 3. `sdflow-init/assets/workflow/ff-generation-constraints.md`

- 标题：`# opsx:ff 起手强制规范（前置动作 FF-0 + 生成硬约束 D-1~D-6）` →
  `# 生成起手强制规范（FF-0 + D-1~D-6）`
- 定位声明：`本规范是 /opsx:ff 起手强制项的唯一权威定义源` →
  `本规范是 /sdflow-spec（或 /opsx:ff 直呼）起手强制项的唯一权威定义源`（保留「或 /opsx:ff 直呼」）
- 「调用方引用方式」注入示例：`/opsx:ff {change}。按 @openspec/workflow/ff-generation-constraints.md
  注入：` → `/sdflow-spec {change}（或 /opsx:ff 直呼）。按
  ~/.sdflow/workflow/ff-generation-constraints.md 注入：`
- 「正模式」代码块注释：`# 所有调用方：按 @openspec/workflow/ff-generation-constraints.md 注入 D-x`
  → `# 所有调用方：按 ~/.sdflow/workflow/ff-generation-constraints.md 注入 D-x`
- 背景节（约束集设计判据由来、D-5 漂移史）与文末「历史」节**原样未动**，符合 D5 要求。
- FF-0 定义（:14）、hook 硬强制段（:29）已原本同时列出 `/opsx:ff` 与 `/sdflow-spec` 两个入口
  （事实性枚举，非「定位声明/调用方示例」），brief 未要求改动，未触碰。

`~/.sdflow/workflow/` 路径写法核对自本仓其余 canonical 引用惯例（`workflow.md` / `WORKFLOW-GUIDE.md`
均用 `~/.sdflow/workflow/...`），未凭空发明新表述。

## pytest 结果

```
$ /usr/bin/python3 -m pytest hack/tests/test_canonical_entry_sync.py -v
8 passed in 0.01s
```

presence 六子串（`推荐流水线`+`唯一入口`、`模型 SHALL 在以下情形自动 invoke`+`/sdflow-spec`、
`模型 MUST NOT 自主判断`+`该开 change 了`）均落在未改动的原行（:21 表头行的替代行「四、推荐流水线」
未变、:62/:66 未变），逐字保留确认通过。

全仓回归：

```
$ /usr/bin/python3 -m pytest
2649 passed, 10 skipped in 380.30s
```

无新增失败，无退化。

## Concerns

1. **§二 ASCII 图与表格一并现行化，略超出 brief 字面「改现行两工具表」的最小范围**——brief
   原句只提「两工具表」，但设计表 design.md:33 的口径是「§二现行化」（整节），且该 ASCII 图与
   紧邻的表格描述同一件事（三相位→两相位），若只改表格不改图会在同一小节内自相矛盾（图仍画
   `brainstorming`/`grill-with-docs` 三节点）。判断这是「措辞替换」操作的自然延伸，非新增范围，
   已一并现行化。
2. 本 worktree 起始未携带该 change 的产物，通过 `git merge --ff-only` 从
   `feat/fix-workflow-bundle-staleness` 拉取后才能读到 `task2-brief.md`——过程细节记在本报告
   开头供追溯，未对 change 内容做任何选择性改动。
3. 施工过程中观察到一次自动生成的 commit（`1330076 Task 2: generation-process 收史 +
   ff-constraints 外壳更新`），非我本人主动执行 `git commit`——推测是仓库自带的 checkpoint 钩子
   在 Edit 后自动落盘；未打任何 checkpoint 完成标签、未勾选 tickets.md/tasks.md 复选框，符合
   "implementer MUST NOT 自行勾框或打完成标签" 的边界。

## 验收对照（brief 内自带的验收项，供双轴审核对，非本人勾选）

- `generation-process.md` §二/§三/§六按 D4 改写完毕 —— 已完成，见上「改动位点」
- §四流水线图正确插入阶段二行，其余行未变 —— 已完成，diff 仅新增一行
- §四 ② 已删「判断」二字，其余措辞未变 —— 已完成
- `pytest hack/tests/test_canonical_entry_sync.py` 全绿（presence 六子串保留）—— 8 passed
- `workflow-history.md` A5 条目已新增 —— 已完成
- `ff-generation-constraints.md` 按 D5 更新完毕，背景/历史节未动 —— 已完成
