# Task 3 impl report — 代码审 Step1 改为自持 scope 审计，全 SKILL 去 gstack 依赖

## 做了什么

只改了一个文件：`sdflow-code-review/SKILL.md`（596 → 652 行）。`git status --porcelain` 确认无其它文件被触碰。

- **Step1 完全重写**：不再"并入 gstack/review 原生执行"，改为恒跑一个 fresh 中档子代理（`$SDFLOW_TIER_MID`），
  以 `{change_dir}` 的 proposal/tasks/design + `DIFF_BASE..HEAD` diff 为确定性意图源，做 scope-drift + 完成度
  两轴审计。子代理不可用时降级主 session 亲做，报告显著标注自查偏置。
- **能力探针从 Step2 挪到 Step0**（与 tier-resolution 同位，第零步新增第 5 项），Step1 与 Step2 共用同一次
  判定结果，Step2 原处只留一句引用（不重复落锚）。
- **锚 mode 枚举**换成 `subagent|main-session`，旧值 `native|simulated` 归档不迁移。
- **mirrors 合法 token 集**在 SKILL 侧的所有落值/示例都加了 `broad`（三处：第零步能力探针落锚示例、报告格式
  子代理能力锚示例、mirrors 说明文字），dead-fanout 计数集措辞未动（那是 Task 1 anchor_lint.py 的职责，SKILL
  只是引用行为不改变计数集本身）。
- **skew 探测**从两条信号扩到四条（新增：contract `lens-metric-fold` 块含 `scope-audit:` 行；anchor_lint 支持
  `broad` mirrors token，探测信号点名 `_MIRRORS_LEGAL` 常量名），任一探不到仍沿用既有「硬停 + 提示先跑
  `sdflow-init update`」文案。
- **领域镜选择段**加了一行 `TG-27 → domains/llm.md`（与 TG-01→backend 同构）。
- **Step2 fan-out prompt 模板**追加 pre-emit 引文纪律全文（含非局部 finding 的可复核证据包替代路径，声明
  "产出纪律非机械门"）。
- **Step3 置信过滤**追加"既无引文又无证据包 ⇒ 置信上限 50 ⇒ 落已裁掉区一行留痕"的裁决规则，并把
  Suppressions 明确滤除类目扩了两条（阈值/常量不强制求注释；无害冗余助可读性不标）。
- **报告格式区**：`Step2「能力探针」` 的交叉引用改指第零步；命中范围行 `gstack/review: scope-drift/完成度
  结论` → `Step1 自持 scope 审计: scope-drift/完成度 结论`；度量锚区 broad 行标注改为
  `broad（Step1 自持 scope 审计）`并新增一段说明 `hits[].raw` 用 `scope-audit`、roster 行仍是 canonical
  `lens="broad"`。
- **"与 gstack/review、官方 code-review 的分工"表**整段改写为"与官方 code-review 的分工"（去掉 gstack
  列/行，保留官方 `/code-review` 弃用为独立 step 的既有内容——这部分与 gstack 无关，不属于本票删除范围）。
- 其余散落引用（描述段、intro 段、Step4 裁决计数段的"Step2 能力探针"交叉引用、Step3 汇总行）同步改述。

## 13 条验收标准逐条证据

1. **`grep -n "gstack" sdflow-code-review/SKILL.md` 无输出**
   ```
   $ grep -n "gstack" sdflow-code-review/SKILL.md
   （无输出，exit code 1）
   ```
   严格归零，未留任何"历史注记"豁免。

2. **Step1 描述为恒跑 fresh 中档子代理的 scope 审计，输入明列 proposal/tasks/design + diff，prompt 携带四条通则 + 不 AskUserQuestion**
   `SKILL.md:236-249`：
   > `## 第一步：自持 scope 审计（fresh 中档子代理，恒跑守卫）` …
   > `- **dispatch（复用上一步能力探针结果，MUST NOT 另探）**：… → 派一个 fresh 子代理（中档 $SDFLOW_TIER_MID）`
   > `- **输入**：{change_dir} 的 proposal.md（scope / Non-Goals）+ tasks.md + design.md + DIFF_BASE..HEAD diff（--stat + 全量）。prompt MUST 原文携带本 SKILL.md 顶部「四条通则」区块（sdflow:principles 从 start 到 end，整段复制，不转述、不摘要），MUST 声明「不要 AskUserQuestion，返回结构化 findings」。`

3. **审计两轴写明：scope-drift + 完成度五态，判定纪律逐条钉死**
   `SKILL.md:250-256`：scope-drift 段（出圈改动列 SCOPE-CREEP、Non-Goals 被实现算 creep）+ 完成度五态段
   （DONE 从严 / CHANGED 从宽 / UNVERIFIABLE 诚实 / PARTIAL=部分子项有证据 / NOT DONE=diff 内无任何相关证据），
   逐字对齐 design.md §1 与 spec-workflow spec 的判定纪律。

4. **产出含逐 task 五态表 + 负向态 findings，明写不勾 tasks.md、不替代 verify 终审、复审一轮纳入 scope-drift**
   `SKILL.md:257-263`：
   > `- **输出**：① **逐 task 五态表**（每 task 一行：状态 + 一句证据引用；DONE/CHANGED 也在列，非仅负向态…）；② 结构化 findings（…）→ 进 Step3 合并池…`
   > `**与 verify 关系钉死**：本审计 MUST NOT 勾改 tasks.md 复选框、MUST NOT 替代 sdflow-done verify 终审（verify 为最终权威）；Step4 自动修后的「复审一轮」SHALL 把 scope-drift 维度纳入复审范围…`

5. **能力探针段落位于第零步（与档位解析同位），Step1/Step2 共用同一次探针结果，`fanout-capability` 锚每轮恰一条**
   `SKILL.md:198-234`：第零步第 4 项是宿主/档位解析（tier-resolution 托管块），紧接第 5 项即
   `**能力探针（本轮恰好一次，与档位解析同位，Step1 与 Step2 共用同一次结果）**`，含
   `**本轮恰一次，MUST NOT 为 Step1 另探落第二条锚**：Step1…与 Step2…共用本步判定的同一次结果` 一句。
   落锚示例仍是"每轮恰好一条"（`<!-- sdflow:fanout-capability v1 … -->`），未新增第二条锚。

6. **并行边界写明：EXEMPT 候选形状下 Step2 免除判定阻塞等 Step1 结果，非白名单形状才并行**
   Step1 段 `SKILL.md:243-246`：
   > `**并行边界**〔spec-review-amendment：时序钉死〕：diff 命中 Step2 前置 trivial_shape 白名单形状（EXEMPT 候选）时，Step2 的免除判定 MUST **阻塞等待本步结果收齐后**才可定案…；diff 非白名单形状（Step2 反正要 fan-out）时，本步 MAY 与 Step2 fan-out 并行派发，结果同在 Step3 barrier 前收齐。`
   Step2 前置段 `SKILL.md:278-280` 同步呼应：`**免除判定 MUST 阻塞等待 Step1（scope 审计）结果收齐**…2=ERROR → 照常 fan-out（保守，此时 Step1 MAY 与本步 fan-out 并行）`。

7. **降级分支写明主 session 亲做 + 报告显著标注「⚠️ scope 审计降级（存在自查偏置）」；恒跑守卫语义保留**
   `SKILL.md:264-267`：
   > `- **降级**：能力探针判 subagents="unavailable" ⇒ 主 session 亲做同一审计协议，报告**显著标注**「⚠️ scope 审计降级（主 session 亲做，存在自查偏置）」。`
   > `- **恒跑守卫**：trivial_shape 判 EXEMPT 时本步照跑；审计一旦揭出隐藏逻辑 ⇒ EXEMPT 作废、Step2 照跑（见上「并行边界」）。`

8. **锚 mode 枚举为 `subagent|main-session`**
   `SKILL.md:268-270`：
   ```
   $ grep -n 'mode="subagent|main-session"' sdflow-code-review/SKILL.md
   268:- **锚**：报告 Step1 段写 v1 锚行 `<!-- sdflow:step1-broad-review v1 mode="subagent|main-session" -->`——
   ```

9. **报告格式区：mirrors 说明含 broad token；lens-metric 的 `hits[].raw` 用 scope-audit，roster 行仍写 canonical `lens="broad"`**
   `SKILL.md:595`（子代理能力锚示例）：`mirrors="domain,adversarial,history,broad|—"`。
   `SKILL.md:605-608`（度量锚区）：
   > `broad（Step1 自持 scope 审计）` … `**broad 行**：findings[].hits[].raw 用原始镜名 scope-audit（folded 到 canonical lens="broad"）；roster 行仍为 canonical {lens:"broad", runner:"<host>", site:—}——raw 名只出现在 hits[].raw，lens= 字段本身恒为折叠后的 broad。`

10. **领域镜选择段含一行 `TG-27 → domains/llm.md`**
    `SKILL.md:285`：
    ```
    $ grep -n "TG-27 → domains/llm.md" sdflow-code-review/SKILL.md
    285:**TG-27 → domains/llm.md**（代码消费 LLM/agent 产出并持久化/执行/外呼，与 TG-01→backend 同构）——命中即选该领域清单叠加。
    ```

11. **skew 探测段追加两个新信号（contract `scope-audit:` 行；anchor_lint 支持 broad token），任一探不到沿用既有硬停文案**
    `SKILL.md:234`（第零步第 6 项，原第 5 项挪号）：探测信号从两条扩到四条——
    > `③ $RULES_ROOT/lens-metric-contract.md 的 lens-metric-fold 机读块内含 scope-audit: 行（新 SKILL × 旧 contract 方向——本 change 引入）；④ python3 "$RULES_ROOT/tools/anchor_lint.py" --help 的输出或源码 grep 到 broad mirrors token 支持（等价信号：_MIRRORS_LEGAL 常量行含 broad）`
    结尾仍是「任一探不到（陈旧）⇒ …硬停本次评审…提示「tools 陈旧，请先跑 sdflow-init update 再重跑评审」」——文案未变。

12. **Step2 子代理 prompt 模板含引文纪律全文，声明产出纪律非机械门**
    `SKILL.md:307-313`（fan-out prompt 块追加段）：
    > `**🔴 pre-emit 引文纪律（产出纪律非机械门，C9）**：每条 finding MUST 引出触发它的具体代码行原文（file:line + 逐字引文）；**非局部 finding**…SHALL 以**「可复核证据包」**替代单行引文…；**两者皆无 ⇒ 该条自报置信 MUST ≤50**。本纪律仅约束 Step2 各镜的代码 finding，不作用于 Step1 scope 审计的任务级证据。**诚实边界**：引文真实性无机械核验（子代理自报），本条是产出纪律非机械门，MUST NOT 声称机械保证。`

13. **`sdflow:principles` / `sdflow:tier-resolution` / `sdflow:async-branch` 托管区块字节级未变**
    用 Python 逐块提取比对旧版（`feat/absorb-gstack-review` 分支上未改前的 SKILL.md）与改后版本：
    ```
    sdflow:principles IDENTICAL 4076 4076
    sdflow:tier-resolution IDENTICAL 1800 1800
    sdflow:async-branch IDENTICAL 14295 14295
    ```
    （提取正则 `<!-- {name}:start.*?-->.*?<!-- {name}:end.*?-->`，长度与内容逐字节相等。）

## Suppressions 两条扩展（额外核对，属 AC 里的裁决规则一部分）

`SKILL.md:324`：
> `明确滤除：CI 能抓的 / 纯 nitpick / 未改动行的既有问题 / 仅主观风格 / 已被注释显式抑制的 / **阈值或常量取值不强制求注释**（调参即腐，Suppressions 扩） / **无害冗余、有助可读性的不标**（Suppressions 扩）。`

## 跑过的测试

```
$ /usr/bin/python3 -m pytest hack/tests/test_sync_principles.py hack/tests/test_tier_resolution_parity.py -q
..................................................                       [100%]
50 passed in 0.16s

$ /usr/bin/python3 -m pytest hack/tests/test_async_branch_parity.py hack/tests/test_checkpoint_slug_coverage.py -q
............................................                             [100%]
44 passed in 0.10s
```

这两组是本票唯一可能受影响的自动化测试面（分别守 `sdflow:principles`/`sdflow:tier-resolution` 托管块与
`sdflow:async-branch` marker 的跨 SKILL 一致性、以及 checkpoint slug 用例计数）。本票是纯 Markdown 指令编辑，
无脚本改动，故 TDD 红→绿循环不适用（tickets.md Global Constraints 已声明）。全仓聚合套件跑通属 Task 6 收尾职责，
不在本票范围内——已单独起了一次全仓 `pytest` 在后台跑（未等待其结束，因其结果不影响本票 13 条验收标准的
真伪，且该聚合验证是 Task 6 的显式职责）。

## 未做 / 越界声明

- 未改 `sdflow-init/assets/workflow/` 下任何文件（trigger-catalog.md、code-checklists、
  lens-metric-contract.md、tools/anchor_lint.py、tools/lens_metric_emit.py、prompts/step8-code-review.md）
  ——分属 Task 1/Task 2/Task 4/Task 5，本票按文件所有权边界只改了 `sdflow-code-review/SKILL.md`。
- 未勾 `tickets.md` 的复选框，未改四件套（proposal/design/specs/tasks.md）。
- 报告中引用的 `_MIRRORS_LEGAL` 常量名、`scope-audit:` fold 行是 Task 1/Task 2 的产物——本票只按跨票钉死的
  命名在 SKILL.md 里写探测信号描述，未验证这两个符号在当前 worktree 里是否已存在（Task 1/2 与本票并行，
  互不可见彼此改动，此为 tickets.md 已声明的已知前提）。

## Concerns

无。13 条验收标准逐条有 grep/引文证据；托管区块字节级校验通过；相关自动化测试全绿。
