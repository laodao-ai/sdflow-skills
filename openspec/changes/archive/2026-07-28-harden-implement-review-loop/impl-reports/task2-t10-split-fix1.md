# Task 2 双轴审 fix1：审计漏记 + `planning-decisions.md` 缺口

状态：`DONE`

修复 `task2-t10-split.md` 双轴审的两条 Important 发现。本次不改 Group A/B 的规则文本本身
（`T10-choice`/`review-loop-breaker` 定名与②步 strong 档已在首轮全部到位），只补两处遗漏。

## finding 1：全仓复核未穷尽 — `sdflow-implement/SKILL.md:170`

重跑 `grep -rn "T10" .`（不带 `--include`），再逐行核对 §7.1 排除口径（Group A 15 / Group B 1 /
【不动】2 /【别名保留】1 /「其余命中」分析类），发现 `sdflow-implement/SKILL.md:170`（"出票模式
同样消费档位：全 ticket 语义一致性自扫遇到粒度争议时的 `T10-choice` 仲裁步要派 **strong** 对抗镜"）
未落入任何一类——非分析类文档，是规范性落点，但也不在 Group A 表内。

`git log --oneline -- sdflow-implement/SKILL.md` + `git show 9f6bcf22 --stat` 核实：该行由
**Task 1** commit `9f6bcf22`（"feat(sdflow-implement): 新增第零步宿主/档位解析 + 四 skill parity
守卫"）写入，写入时点早于本票（Task 2）对 `T10-choice` 的正式定名，但措辞已提前使用该名字——写入时
design.md 的 T10 scope-check 表尚未覆盖此行（该表拟定于本次改名落地之前），故 Task 2 起手 grep 建
「唯一口径」全景图时理应捕获此行、归入"已是目标态、无需改动"一类，但首轮报告漏记，属"断言穷尽核对、
实际输出未穷尽"（违 `premise-verification.md` + 通则①）。

**修法**：仅在 `task2-t10-split.md` §7.1 补一条【Task 1 提前正确使用】分类，说明该行现状即为目标
态、无需改动规则文本。重新核对 53 行过滤后命中（`t10_filtered.txt`，见下方核对记录），确认这是唯一
漏网命中，其余全部被既有五类覆盖，分类现已穷尽。**不改任何规则文本**——该行本身措辞已正确，不存在
可改动的缺陷。

## finding 2：delta 已 SHALL 的 `planning-decisions.md` 审计落点未实现

核实链：

- delta `openspec/changes/harden-implement-review-loop/specs/impl-orchestration/spec.md` 4 处
  （2 处 Requirement 正文 + 2 处 Scenario）SHALL 出票模式仲裁记录落
  `impl-reports/planning-decisions.md`；delta `specs/spec-workflow/spec.md` 同样要求。
- `grep -rn "planning-decisions" sdflow-implement/SKILL.md openspec/specs/` 首轮为零命中——未实现。
- `grep -n "planning-decisions" tasks.md` 亦为零命中——tasks.md 本身漏列，但 delta 已 SHALL，
  tasks.md 遗漏不构成豁免（通则③目标态判据）。

**三处编辑（措辞与 delta 逐字对齐）**：

1. `sdflow-implement/SKILL.md` 出票模式「起手检查」粒度争议处（原 :247–249 后）新增一段，逐字对齐
   delta `impl-orchestration/spec.md:104`：「**出票模式的仲裁记录 SHALL 有确定性审计落点**：写入
   `impl-reports/planning-decisions.md`（change 目录内、git-tracked，由出票落盘的同一次 checkpoint
   一并提交），行格式 = 「`T10-choice` 复核: <方案> | 对抗镜结论 <通过/证伪> | <理由(三镜+主次)>」
   ——出票模式无 code-review 报告产物，此前该仲裁结果**无处可落**〔spec-review-amendment M15〕。」
2. `sdflow-implement/SKILL.md` 出票收尾序列「全 ticket 语义一致性自扫」步（原 :325–329）句末追加
   delta `impl-orchestration/spec.md:116` 的原句：「仲裁记录同样落 `impl-reports/planning-decisions.md`。」
3. `openspec/specs/spec-workflow/spec.md`「阶段三过设计门后连续自动跑到 merge」Requirement ②步括号
   内，从「（复核记录进报告）」补为「（复核记录进报告；出票模式无报告产物时落
   `impl-reports/planning-decisions.md`）」，与 delta 该句逐字一致。

`tasks.md` 属锁定文件（design/proposal/tasks/specs 四件套改动会触发 ship_gate design 域失鲜），
本票 MUST NOT 改动，故其漏列不在本次修复范围内——留给编排层裁决是否需要另开 todo 补记 tasks.md
本身的完整性（不属本 fix 子代理职权）。

## 附带动作：`planning-decisions.md` 回填

新建 `openspec/changes/harden-implement-review-loop/impl-reports/planning-decisions.md`，按上面
新落地的行格式回填本 change 出票时点已发生但当时无处可落的一条 ①档裁决（Task 1 的 Codex 实跑验收项
"MUST NOT 以本 change 为目标"约束）。核实该约束原文已存在于 `superpowers-plan.md:117` 与
`impl-reports/task1-brief.md:21`（逐字比对一致），确认回填内容非杜撰，是对已发生决策的补记。文件头
注明该条为回填、后续出票实时写入。

## 一致性核对（全仓 grep 重跑）

```
$ grep -rn "T10" . | grep -v "/\.git/" > t10_grep_full.txt   # 489 行
$ grep -rn "T10" . | grep -v "/\.git/" \
    | grep -v "openspec/changes/harden-implement-review-loop/" \
    | grep -v "openspec/changes/archive/" | grep -v "openspec/issues/" \
    | grep -v "openspec/ROADMAP.md" | grep -vE "T10:[0-9]|T10[0-9]" > t10_filtered.txt   # 53 行
```

53 行逐条比对 §7.1 五类（Group A 15 / Group B 2 行 / 不动 2 / 别名保留 1 / 其余命中 32）+
本次新增的【Task 1 提前正确使用】1 行 = 53，账目吻合，无第二处漏网。

```
$ grep -n "planning-decisions" sdflow-implement/SKILL.md openspec/specs/spec-workflow/spec.md \
    openspec/specs/impl-orchestration/spec.md
sdflow-implement/SKILL.md:250:  ...
sdflow-implement/SKILL.md:...:  仲裁记录同样落 `impl-reports/planning-decisions.md`。
openspec/specs/spec-workflow/spec.md:83:...出票模式无报告产物时落 `impl-reports/planning-decisions.md`...
```

三处均已落地（`impl-orchestration/spec.md` 本身是主 spec，未在本次编辑范围内——delta 已对齐的是
`sdflow-implement/SKILL.md` 与 `spec-workflow/spec.md` 两个消费面；`impl-orchestration/spec.md`
的三处 SHALL/Scenario 本身就是 delta 定义，归档时会经 `sdflow-done` 的 delta-sync 流程写回主
spec，不属本次 fix 子代理的编辑范围）。

## 测试执行

未新增可执行逻辑，仅指令文本改动。跑受影响面 + 全量回归：

```
$ /usr/bin/python3 -m pytest -q
2893 passed, 11 skipped, 3 xfailed in 286.47s (0:04:46)
```

计数与 Task 2 报告记录的基线（同为 2893 passed / 11 skipped / 3 xfailed）完全一致，零回归。

未新增/删除任何断言字符串被测试硬编码的文本，`grep -rln` 核对 `复核推荐切分方案`/`扫描干净则不留痕`/
`无 quiz-the-user` 在任何 `*.py` 测试文件中均无命中，无需同步测试。

## 完成信号

本次提交不带 `task2-` 标签、不勾 plan 复选框（后置双写时序，由双轴审通过后补打）。

## 未做/裁剪的部分

无。两条 finding 的修法与附带动作均已完成。`tasks.md` 本身漏列 `planning-decisions.md` 条目一事
超出本 fix 子代理职权（tasks.md 锁定），已在上方明确指出，留待编排层裁决。
