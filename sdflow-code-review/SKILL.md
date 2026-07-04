---
name: sdflow-code-review
description: >
  阶段三「代码评审编排器」——**每次全跑·独立冷视角·强制主审**（非"高风险才跑的边际抽查"；实测能抓循环内被
  controller 说服放过的真问题）。主 session（强档）协调：Step1 并入 gstack/review（scope-drift + 计划
  完成度审计），Step2 fan-out 多个 fresh 子代理并行审本项目 code-checklists（领域镜 + 对抗镜 + 历史镜），
  Step3 置信过滤（<80 滤除）+ 对抗裁决，Step4 **能修的自动修**（标 [impl-review-fix]）、≥2 方案有把握自动
  选推荐（记理由）、修不了/拿不准的 defer 进 buglist/todolist，Step5 汇总**一份** code-review-report.md。
  **阶段三无人类门**——不 AskUserQuestion，自动修/自动裁/defer，残差交 hand-off 异步再入口。**不依赖 /clear**
  ——子代理 fresh context 即独立性。代码即 ground truth（无接地镜，换历史镜 + 置信过滤）。出报告标
  [impl-review-fix]。也可说"sdflow 代码审"。Trigger with /sdflow-code-review。
---

# sdflow-code-review — 阶段三代码评审编排器（每次全跑·独立冷·强制主审）

把 workflow 规则集的 `code-checklists/`（经 resolve-workflow.sh 解析，通用 base CR-01~09 + 领域 delta CR-*）操作化为一次
**连续跑的编排代码评审**：Step1 gstack/review（scope-drift + 完成度）→ Step2 并行多镜（本项目清单）→
Step3 置信过滤 + 对抗裁决 → Step4 自动修/defer → Step5 **一份** `code-review-report.md`。

> **定位升级（P3c，须知情）**：本 skill **不是**"高风险才跑的冷独立抽查、边际残差"——那是旧
> `quality-layering.md §五` 的结论，**已被否决**。sdflow-code-review 是**每次全跑的独立强制主审**：实测能抓出
> 生成循环内被 controller 说服放过的真问题。它把旧 `gstack/review`（scope-drift）+ 自制多镜清单审
> 合并成一个编排器，产出一份 `code-review-report.md`（取代旧 staff-review-report.md + impl-review-report.md 分裂）。

## 两条连续性铁律（阶段三自动流的前提）

- **不依赖 `/clear`（G1）**：评审 fan-out 到 fresh-context 子代理，独立性由"子代理冷上下文"给。主 session
  携带生成历史进裁决，接受一丝合成层偏置——但**反静默压制**焊死其边界（见 Step3）。
- **阶段三无人类门（P3e）**：过设计门后一口气跑到 merge，本 skill **不 AskUserQuestion**。**能修的当场修**、
  **≥2 方案有把握自动选推荐（记理由）**、**genuinely 拿不准的 defer**（进 buglist/todolist + hand-off 异步再入口）。
  与阶段二不同——阶段二决策高杠杆（错设计→白做）值一个门；阶段三已实现、残差可追踪可另修。

## 与注入点 B 的关系（2.4，**别把本 skill 优化掉**）

阶段三"领域审两遍"**不是重复**，两遍机制/职责不同——这是最反直觉、最该防后人"优化掉"的一条：

```
  第一遍: subagent-dev 终审 + 注入点B        第二遍: 本 skill（事后 sdflow-code-review）
  ────────────────────────────────────────────────────────────────
  时机   生成循环内                          全部实现完成后
  机制   命中即派 fix 子代理修 + re-review 闭环  出报告 → 编排器修（无 re-review 紧闭环）
  独立性 reviewer 冷,controller 热(在循环内)   完全冷独立(脱 controller)
  职责   即时修复确认(shift-left,便宜早修)    独立兜底网(实测能抓真问题)
```

- **注入点B 不可替代 = subagent-dev 的即时修复确认**（发现即派 fix 子代理修 + re-review 到 Approved，循环内闭环）。
- **本 skill 不可替代 = 独立冷视角 + 实测捕获**（抓循环内被 controller 说服放过的真问题）。撤任一个都留洞。

---

## 第零步：确认对象 + diff base + 读规则

1. 未指定变更则 `openspec list` 让用户确认。记 `{change_dir}` = `openspec/changes/{name}/`。
2. 确认代码已实现且在 feature 分支（`git branch --show-current`）。算 diff base：
   `git fetch origin <base> --quiet && DIFF_BASE=$(git merge-base origin/<base> HEAD)`。
3. 规则根解析：`[ -x ~/.sdflow/hack/resolve-workflow.sh ]` 不成立 → 提示「resolve-workflow.sh 未安装——先在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh」并降级通用代码审；否则 `RULES_ROOT=$(~/.sdflow/hack/resolve-workflow.sh --root "$(git rev-parse --show-toplevel)")`——退出码 2 → 显式降级通用代码审并原样转发脚本 stderr 告警（绝不静默当"本项目无此评审层"）；成功 → 读 `$RULES_ROOT/code-checklists/README.md`（架构/选用）、`$RULES_ROOT/code-checklists/code-review-base.md`（CR-01~09）、`$RULES_ROOT/trigger-catalog.md`（触发）。禁止自行重实现三步链。

## 第一步：gstack/review 子步（并入·原生执行，scope-drift + 完成度）

- **原生执行〔T25·R5〕**：主 session 经 Skill 机制原生执行 gstack `/review` 全量流程（指令直接进主 session，MUST NOT 派子代理读其 SKILL.md 模拟；不因 prompt 措辞裁剪原生步骤），**必须含 scope-drift（顺手多改）与计划完成度缺口（建的=计划的?）**，结论纳入 Step3 合并池；报告 Step1 段写 v1 锚行 `<!-- sdflow:step1-broad-review v1 mode="native" -->`。
- **显式降级**：gstack/review 不可用 → 子代理模拟 + 显式日志（"scope/完成度审计层缺失 → 模拟降级"）+ 锚行 `mode="simulated"`，MUST NOT 伪装原生，**不静默跳过**。

## 第二步：规划镜头 + 并行 fan-out 子代理（本项目清单）

**规划镜头（主 session）**：按 `{change_dir}` 命中的 TG/栈定**领域镜**；按风险定**对抗镜**（普通 2 / 高风险 3）；
固定 1 个**历史镜**。linter/typechecker/编译器能抓的（导入/类型/格式/纯风格）不进任何镜——CI 会跑。

**fan-out（一条消息内全部派出，各子代理 fresh context、无用户交互、返回结构化 findings）**：

| 镜 | 数量 | 干什么 | 建议档位 |
|----|------|--------|-----------|
| **领域镜** | 每命中领域 1 个 | 读 `DIFF_BASE..HEAD` diff + 相关真实代码，逐条过 `code-review-base.md` CR-01~09 + `domains/<栈>` CR-* 项，列违反/存疑项（带 `file:line`） | 中档（判断） |
| **对抗镜** | 2-3 | 各从一个**不同角度**「证明这段代码运行期会爆」：并发竞态 / 资源泄漏 / 错误路径未覆盖。默认 refuted=true，找到爆点才记 | 中档（对抗推理） |
| **历史镜** | 1 | `git blame` 改动行 + 读历史 PR 评论：这块以前修过/revert 过吗？本次是否重蹈或忽略旧 review 意见 | 弱档（机械） |

> 每个子代理 prompt 必须自带：`{change_dir}` + diff 范围、负责的清单/角度、"返回结构化 findings（每条带：
> 问题 / CR 编号 / 证据 `file:line` / 严重度 / 建议），**不要 AskUserQuestion**"。
>
> 〔Phase C 补〕sdflow-code-review **自带 code outside voice**（跨模型 codex，always）+ 命中 HR-TG 单开领域 cross-model
> 属 Phase C（C3/C4）。Phase A 不实现跨模型镜。

## 第三步：置信过滤 + 综合 + 对抗裁决（主 session · 强档）

1. 汇总 gstack/review（Step1）+ 各镜 findings，**去重**（同一问题多镜命中合并）。
2. **置信过滤**（借官方 code-review rubric，可下放弱档子代理逐条打分）：每条打 0–100，**滤掉 <80**。
   明确滤除：CI 能抓的 / 纯 nitpick / 未改动行的既有问题 / 仅主观风格 / 已被注释显式抑制的。
3. **对抗裁决**：对每条存活 finding 判"是否真的运行期出问题"——对抗镜反驳 ≥ 多数成立则采信。
4. **反静默压制（escalate-not-drop，Q3 铁律）**：裁决对 reviewer finding **只能降级/批注、不得静默丢弃**；
   判"不成立"的连理由落入报告「已裁掉」区。<80 滤除项也**一行带过（可审计），不静默丢**（静默 = "全过了"的假象）。

## 第四步：自动修 / 自动裁 / defer（阶段三无人类门，P3e）

- **能修的自动修**：标 `[impl-review-fix]`，**不进延后池**。
- **≥2 方案有把握**：自动选推荐项（**记理由**入报告），不问人。
- **修不了 / genuinely 拿不准**：defer → 写 buglist（本 change 引入的代码 bug）/ todolist（改进/关注点），
  本 change 不处理，交 hand-off 引导另开清理 change。
- **绝不 AskUserQuestion**（阶段三无人类门）。

## 第五步：产出 + 收敛口

- 写 `{change_dir}/code-review-report.md`（见下格式：命中范围 + Findings≥80 + 已裁掉区 + 裁决 + 修复/defer 台账）。
- 修复代码，改动处标 `[impl-review-fix]`。
- **checkpoint 提交**：产出报告 + 自动修复后 → `~/.sdflow/hack/checkpoint-commit.sh impl-review "多镜代码审 + 自动修 + 报告"`。
- **收敛口**：结尾一句——建议进 `/sdflow-done`（verify → hand-off → archive → commit → merge）。

---

## 报告格式（code-review-report.md）

```
## code-review 报告 — {change}
### 命中范围
  栈: backend·go / embedded·ml307c …   清单: CR-01~09 + CR-GO-* + …   gstack/review: scope-drift/完成度 结论
### Findings（置信 ≥80）
  [严重度] CR-04 资源泄漏 | file.go:42 | 错误路径未释放 conn | 置信 90 | 已修[impl-review-fix] / defer→buglist
### 已裁掉（反静默压制，可审计）
  X1  reviewer 原始发现 + 主 session 裁掉理由；<80 滤除项一行带过
### 修复 / defer 台账
  自动修 N 项[impl-review-fix]；自动选推荐 M 项(附理由)；defer K 项 → buglist/todolist
  T10复核: <方案> | 对抗镜结论 <通过/证伪> | <一句理由>   ← 无客观判据的 ≥2 方案自动选必附
### 结论
  □ 建议进 /sdflow-done   □ defer 残差已入 buglist/todolist（hand-off 会引用）

  结论区末行为机器锚行（ship-gate 契约，二选一）：
  <!-- ship-gate: code-review=pass -->   （建议进 /sdflow-done）
  <!-- ship-gate: code-review=blocked --> （存在未解 blocker）
```

## 模型选择（按本步性质，逐步定）

档位与缺省见规则根 `model-tiers.md`（经 `~/.sdflow/hack/resolve-workflow.sh` 解析；config.yaml 的 model-tiers 段可覆盖映射）。

```
  主 session（裁决 / 自动裁 / 出报告）        强档 ← 这是门禁,弱档=假绿
  领域镜 / 对抗镜（判断、对抗推理）           中档
  历史镜 / 置信过滤（git blame/打分，机械）   弱档
```

依据：评审是门禁，综合判断这层弱档会"看着过其实没深究"；机械读 blame/打分可下放弱档。
**不要**把综合判断委派给弱档子代理。阶段三无人类门（不 AskUserQuestion，自动修/裁/defer）。

## 与 gstack/review、官方 code-review 的分工（并入 vs 弃用）

| | gstack/review | 官方 /code-review | 本 skill（sdflow-code-review 编排器） |
|---|---|---|---|
| 现状 | **并入本 skill Step1** | **弃用为独立 step（P3d）** | 每次全跑·独立冷·强制主审 |
| 干什么 | scope-drift + 完成度审计 | 插件能力仅供历史镜/置信过滤**内部借用** | 清单逐条 + 对抗 + 置信过滤 + 合并出报告 |
| 决策 | 自动（纳入合并池） | 不再独立 gh 回帖 | 主 session 对抗裁决 + 自动修/裁/defer |

> P3d：官方 `/code-review` 不再作独立 step（subagent-dev production-readiness + 本 skill 已覆盖，
> 本地合并无需 gh 留痕）；但保留其插件能力供历史镜 / 置信过滤内部借用。

## 注意

- **每次全跑，非高风险才跑**（P3c；旧 quality-layering §五"缩成残差"结论已否决）。
- **置信过滤要可审计**：滤掉的 <80 项一行带过，不静默丢。
- **不重扫 CI 能抓的**：linter/typechecker/编译器范围内的不进镜。
- **代码即 ground truth**：直接读 diff 与真实代码，不设接地镜（与 sdflow-spec-review 的唯一结构差异，换历史镜 + 置信过滤）。
- checkpoint 脚本 = `~/.sdflow/hack/checkpoint-commit.sh`（setup.sh 全局安装）；缺失则先跑 setup，或退化为普通 `git add -A && git commit`。
- 项目无关：规则路径一律经 `~/.sdflow/hack/resolve-workflow.sh` 解析（本地 pin 或全局 canonical），不硬编码 `openspec/workflow/`。
