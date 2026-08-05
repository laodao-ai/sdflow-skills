# Task 4：workflow bundle 同步与安装链路生效 —— 实现记录

## 范围（tasks.md §4，4.1–4.5）

本票只改 `sdflow-init/assets/workflow/` 下 3 个 bundle 文件，跑一次 `setup.sh` 令改动经安装链路
生效到全局 canonical。无产品代码改动，无新增/修改测试文件（本票测试面见下方「核验」）。

## 4.1 · `ff-generation-constraints.md`：`wayfinder-resolved:` 前缀保留 + 加 legacy 标注

- 位置：`:46` 后新增一段（D10 拍板：规则本身**不删**，只加注）。
- 内容：声明 `sdflow-roadmap` 的三分支路由 / footage 落盘机制已随本 change 移除，新建 roadmap 包
  不再产生 `footage/`，本前缀不再有新的产出方；规则保留仅为消费仓**存量**（重构前生成）footage
  仍可能被溯源引用。
- 未删除任何既有文字，`git diff` 为纯新增（+5 行）。

## 4.2 · `workflow-history.md` 追加移除记录

- 新增 `### A4 · sdflow-roadmap 讨论层的 wayfinder 三分支路由已移除（2026-08-06）` 一节，紧随
  既有 A3（grill 瘦跑废除）之后，格式与既有条目一致（背景 + 理由/现状两段）。
- 内容涵盖：原三分支路由（explore / wayfinder 铺图 / office-hours）→ 内化为单一 memo 载体；
  `openspec/matt/` 套件随之整体移除（前提消解）；`wayfinder-resolved:` 前缀保留但 legacy 的结论
  与 4.1 呼应。

## 4.3 · `config.template.yaml` `:41` / `:51` 陈旧引用订正

**核查过程（落笔前先证伪，通则①）**：

1. `grep -n "wayfinder" sdflow-init/assets/workflow/ff-generation-constraints.md` 只命中
   `wayfinder-resolved:` 前缀那一处（4.1 改动处）——**「wayfinder→ff 衔接契约」章节确实不存在**。
2. `git log -S"wayfinder→ff 衔接契约" -- sdflow-init/assets/workflow/ff-generation-constraints.md`
   定位到该章节在更早的 `ab8f746 task4(simplify-workflow)` 提交中被**整段删除**（连同「逐区读 map /
   TG 判命中前置 / 回链」等具体机制说明一起删掉，只保留了「切片建议」小节里的前缀禁混用一句）。
   `config.template.yaml` 当时未同步，形成陈旧引用（即 spec-review-amendment SR-13 指出的问题）。
3. `grep -rn "wayfinder" sdflow-init/assets/workflow/*.md *.yaml` 确认 bundle 内再无任何「wayfinder
   map」结构的产出方描述——本 change 的 1.8 也把 sdflow-roadmap 侧的 map 结构整体删除。⇒ 目标态下
   「change 源于 wayfinder map」这个前提**不会再发生**（不是「存量少见」，是 producer 已不存在）。

**处置**：删除两条规则（`proposal:` 段一条、`design:` 段一条），不改写为指向别处——因为没有等价
替代目标可指。这是最小订正：既消除了指向不存在章节的死链接，也不留下描述已失效机制的说明文字
（该模板会被 `sdflow-init` 注入每个新建下游仓的 `config.yaml`，留着等于给新仓塞入永远不会命中的
死规则）。`git diff` 为纯删除（-2 行），未触碰同段其余行。

## 4.4 · dev checkout 跑 `setup.sh` + 单独跑 `sync_principles.py --check`

前置核实（编排层已告知，仍本地复核）：`~/.claude/skills/sdflow-roadmap` symlink 已指向本开发
checkout，故本机处于「知情临时指 dev」状态，跑 `setup.sh` 不改变该指向。

```
$ bash setup.sh
...
sdflow-skills v1.0.0-93-gcc41cb3-dirty ready → /Users/cheneyzhao/.claude/skills /Users/cheneyzhao/.codex/skills
  installed (39): ...
    ✓ workflow @ /Users/cheneyzhao/.sdflow — 接管：.../sdflow-init/assets/workflow → /Users/cheneyzhao/Documents/04-sdflow-skills/sdflow-init/assets/workflow
    ...
[sync_principles] ✅ 20 个投放面全部与真相源一致
[gen_workflow_guide] ✅ WORKFLOW-GUIDE.md 与单一源一致
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致
[tier-resolution-parity] ✅ 4 处宿主/档位解析核心段逐字节一致
[encoding-hygiene] ✅ 所有入口脚本均满足编码前导契约
```

按 tasks.md 4.4 明文要求，`setup.sh` 内 `sync_principles.py --check` 那一处是 `if ! …; then echo
"⚠️…"; fi`（非 fail-closed，警告可能淹没在大段输出里），故**单独**再跑一次看 exit code：

```
$ python3 hack/sync_principles.py --check
[sync_principles] ✅ 20 个投放面全部与真相源一致
$ echo $?
0
```

**exit code = 0**。本票未改任何 SKILL.md，principles 托管块本就不受影响；此步是安装链路的完整性
核验，非「本票引入了 principles 漂移」。

### 安装链路指向核对（如实贴出）

```
$ ls -l ~/.sdflow/workflow
lrwxr-xr-x ... /Users/cheneyzhao/.sdflow/workflow -> /Users/cheneyzhao/Documents/04-sdflow-skills/sdflow-init/assets/workflow

$ ls -l ~/.claude/skills/sdflow-roadmap
lrwxr-xr-x ... /Users/cheneyzhao/.claude/skills/sdflow-roadmap -> /Users/cheneyzhao/Documents/04-sdflow-skills/sdflow-roadmap
```

两条 symlink 均指向本开发 checkout（`/Users/cheneyzhao/Documents/04-sdflow-skills`），未指向任何
奇怪路径；本机当前全局 canonical = 改动后的 bundle 版本。

## 4.5 · hand-off 项（本票不执行）

按 tasks.md 明文：4.5（合并后在运行 checkout `~/.skills/sdflow-skills` 重跑 `setup.sh` /
`/sdflow-upgrade` 还原）是**合并后**才能执行的步骤，**本票 MUST NOT 执行**。特此记录：

> 🔴 **待办（hand-off 给合并后步骤）**：本 change 合并进 `main` 后，须在运行 checkout
> `~/.skills/sdflow-skills` 执行 `git pull` + `bash setup.sh`（或 `/sdflow-upgrade`），使
> `~/.sdflow/workflow` 与 `~/.claude/skills/sdflow-roadmap` 等全局 symlink 从当前「临时指向本开发
> checkout」状态还原为指向运行 checkout——这是 CLAUDE.md「dev/runtime checkout 纪律」的标准收尾，
> 本票未执行、不代表遗漏。

## 核验清单（逐项对应 tickets.md 验收复选框）

| # | 验收动作 | 结果 |
|---|---|---|
| 4.1 | `wayfinder-resolved:` 前缀规则保留且加 legacy 标注 | ✅ 规则原文零改动，纯新增一段 legacy 说明 |
| 4.2 | `workflow-history.md` 追加一条 wayfinder 路径移除记录 | ✅ 新增 A4 节 |
| 4.3 | `config.template.yaml` `:41`/`:51` 陈旧引用订正 | ✅ 两条死引用规则已删除（无等价替代目标可指） |
| 4.4 | dev checkout 跑 `setup.sh`，单独跑 `sync_principles.py --check` exit 0 | ✅ 见上方命令输出，exit code 0 |
| 4.5 | 合并后 hand-off 项已记录、未在本票执行 | ✅ 见上节 |

## 三个特殊约束逐条自查

1. **4.4 验收动作独立跑 `--check` 看 exit code**——已照做，未依赖 `setup.sh` 输出里的告警行。
2. **4.5 是 hand-off 项，本票不执行**——已确认未在本机对 `~/.skills/sdflow-skills` 做任何操作。
3. **`wayfinder-resolved:` 前缀规则本身保留**（D10）——4.1 的 diff 是纯新增，未删除/未改写原有
   前缀禁混用规则的任何一个字。

## 未触碰范围确认

`git status --porcelain` 显示本次改动只涉及 3 个 bundle 文件（另有编排层预先落盘的
`task4-brief.md` 一并入本次提交，属 ticket 可见性前置产物、非本票工作内容）；未改动任何
`.py` 文件；未改动 `proposal.md` / `design.md` / `tasks.md` / `specs/`；未勾选 `tickets.md`
复选框；未打 `checkpoint(...)` 标签。
