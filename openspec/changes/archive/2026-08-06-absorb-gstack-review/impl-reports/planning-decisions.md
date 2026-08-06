# absorb-gstack-review — 出票期决策记录

## `T10-choice` 仲裁

`T10-choice` 复核: anchor_lint 合法 token 集常量名钉死为 `_MIRRORS_LEGAL`（Task 1 验收标准） | 对抗镜结论 未派（第①档：有客观判据，`design.md:106` 已逐字声明该名作为 SKILL 侧 skew 探测信号，非开放选择） | 理由(三镜+主次)：系统镜——Task 1 与 Task 3 并行落盘，若各自取名则 Task 3 写出的 skew 探测段探不到 Task 1 实际定义的常量，形成跨票静默断链（本 change 的高发面正是「新 SKILL × 旧 tools」skew，探测失效等于该防护归零）；开发循环镜——钉死一个已在设计里写明的名字零额外成本，事后靠 review 发现断链则要一整轮返工；用户镜——无可感知差异。**主次：系统镜为主**（跨票契约的确定性），开发循环镜次之。

## 切片划分依据

design.md 无「切片建议」节 ⇒ 自主出票。划分主轴 = **文件所有权互斥**（Claude 宿主并行 worktree
的正确性前提），而非 tasks.md 的 P0/P1/P2 分组：

- Task 1 = `tools/anchor_lint.py` + 其 golden 测试
- Task 2 = `lens-metric-contract.md` + `tools/lens_metric_emit.py` + 其测试
- Task 3 = `sdflow-code-review/SKILL.md`（tasks 1.1–1.4 + 2.5 的 SKILL 半 + 4.1 + 4.2 全部落此一文件）
- Task 4 = `code-checklists/*` + `trigger-catalog.md`
- Task 5 = `prompts/` + `workflow.md` + `quality-layering.md` + `docs/*` + `hack/tests/test_workflow_split.py`
- Task 6 = 收尾验证（预算外）

`tasks.md` 的 2.5（skew 探测）横跨三个文件，按文件所有权拆入 Task 1 / Task 2 / Task 3 三票，
各自持有自己那一半，无共享写入面。

**Blocked-by 拓扑**：1/2/3/4 无依赖（首批并行）；5 依赖 3（文档提法须与 SKILL 定下的提法一致，
并行会各写各的措辞）；6 依赖全部。

## 语义一致性自扫结果

跨票语义锚逐条核对，除上述常量名一处外无矛盾：

| 锚 | 生产票 | 消费票 | 状态 |
|---|---|---|---|
| `_MIRRORS_LEGAL` 常量名 | 1 | 3（skew 探测） | **已钉死**（见上仲裁） |
| `mode="subagent"` 枚举值 | 3 | 1（lint 通过用例） | 一致 |
| raw 名 `scope-audit` | 2 | 3（`hits[].raw`） | 一致 |
| `TG-27` / `domains/llm.md` | 4 | 3（领域镜选择段） | 一致 |
| 「自持 scope 审计」提法 | 3 | 5（docs 改述） | 已由 Blocked-by 5→3 串行保证 |

## 收尾票的 dogfood 分工（非缩水，是分工声明）

`tasks.md` 6.4 的实跑观测（跑一次 `/sdflow-code-review` 核验产出锚）**不由收尾票执行**——
收尾票 implementer 是子代理，无法再派子代理，跑不了多镜 fan-out。该观测由 ship 链序紧随的
code-review 步天然承担（收尾票先开全局窗口，那一步跑的就是本 change 的新 SKILL）。
收尾票只做开窗前置 + 待核锚清单落盘，并 MUST 在报告里显式声明未完成实跑观测。
