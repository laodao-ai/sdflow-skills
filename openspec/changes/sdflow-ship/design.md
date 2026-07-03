# 设计：sdflow-ship

> 决策真相源 = [`adr/0004`](../../adr/0004-opsx-ship-stage3-orchestrator.md)（窄 scope/门禁传播/meta-orchestrator）+ [`adr/0006`](../../adr/0006-execution-model-baseline-fleet-anchored.md) 约束(b)（确定性台账硬约束）+ [proposal.md](./proposal.md)。术语见 CONTEXT.md（**编排层连续 vs 设计层连续** / **verify 终门** / **假✅**）。

## 一、依赖与前置

- 依赖 `sdflow-rebrand`（已归档）：新 skill 名就位（chain 的对象 = sdflow-code-review/sdflow-done）；依赖 `minimize-repo-footprint`：resolver/canonical 就位（ship 读规则同走 resolver）。
- 真实激活模式沿 rebrand 先例：实现期沙箱验证，merge+push 后新会话 `/sdflow-upgrade` 拾取新 skill。
- T10/T11/T20 随本 change 落（批次 `minimize-repo-footprint` 的 T10/T11、批次 `sdflow-rebrand` 的 T20——完成后各自 set-status DONE 带 evidence）。

## 二、命中触发（TG）

| TG | 命中点 | 激活 |
|---|---|---|
| **TG-12** | 步序推进/门禁传播决策逻辑 | 决策图（§三） |
| **TG-14** | 新组件 ship_gate + skill chain 拓扑 | 组件图（§四）+ 组件清单（§六） |
| **TG-23** | 台账形态 ≥2 方案（盘面即状态 vs state 文件） | 决策记录 = 本文 D1（引 adr/0006，不新开 ADR） |
| **TG-21** | gate 输出形态 / 拍板标记字面 | §五 D2/D5 直接裁定 |

## 三、步序与门禁（决策图，TG-12——`ship_gate.py` 的确定性逻辑）

```
  /sdflow-ship {change}
        │
        ▼
  gate(pre-flight): spec-review-report.md 存在?
        │            └─ 含「设计门拍板」标记行?(D5 字面约定)
        │  任一否 → EXIT: REFUSE_START（"先过设计门"，不起跑）
        ▼
  gate(step 5.5): 条件判定输入 = proposal.md TG 命中表含 TG-02?
        │  ├─ 否 → SKIP(记录"非嵌入式不触发")
        │  └─ 是 → 模型判高风险/TG-18(prose,每步内部判断) → 跑 embedded-test-sop → 产物 {change}-sop.md
        ▼
  gate(step 6/7): superpowers-plan.md 存在? → 无 → NEXT=writing-plans(→subagent-dev 自动执行)
        │         实现完成判据〔grill-amendment，Q2=B——ff 原案两通道经实证双死：
        │         两份真实 plan 复选框 0 勾、SDD ledger gitignored 不可靠〕：
        │         主锚 = git log 的 checkpoint 任务标签——plan 数任务数 N(`### Task \d+:`)，
        │                收集 `checkpoint(task<k>-` 去重任务号集，齐 N 判完成
        │         辅通道 = plan 复选框全勾(兼容回勾型执行器)
        │         皆不可判 → UNKNOWN 停上抛；SDD ledger 移出判据(降为 controller 自用恢复图)
        ▼
  gate(step 8): code-review-report.md 存在?
        │  ├─ 无 → NEXT=sdflow-code-review
        │  └─ 有 → 结论区含「建议进 /sdflow-done」? 含「blocker」未解? 
        │          blocker → EXIT: BLOCKED_UPSTREAM(停并上抛,列 blocker)
        ▼
  gate(step 9): verify-report.md 存在?
        │  ├─ 无 → NEXT=sdflow-done
        │  └─ 有 → 「结论：PASS」? FAIL → EXIT: VERIFY_FAIL(停并上抛,引缺口清单)
        ▼
  gate(final): hand-off.md + archive 目录存在 + 分支已并 → EXIT: SHIPPED(输出摘要)
```

- **每步前后各调一次 gate**：步前问"NEXT 是谁 + 前置缺什么"，步后问"产物落了吗 + 门禁结论"——模型不自行记忆步序（adr/0006(b)）。
- **门禁传播** = 从产物的**机器注释行**机判（`<!-- ship-gate: ... -->`，D5〔grill-amendment〕）——不押自然语言结论行（grill 取证已证其对真实存档全 miss）；三个报告模板随本 change 补锚行。

## 四、组件拓扑（TG-14）

```
  sdflow-ship/SKILL.md ──每步前后调──▶ scripts/ship_gate.py（只读 change 目录,无副作用）
        │                                    │ stdout: JSON{verdict,next,missing,reason}+一行人读摘要
        │ chain（不取代）                     │ exit: 0=可推进 / 3=REFUSE_START / 4=BLOCKED / 5=VERIFY_FAIL
        ▼                                    ▼
  embedded-test-sop(条件) → writing-plans(→subagent-dev) → sdflow-code-review → sdflow-done(→merge)
        规则/清单经 resolve-workflow.sh；模型档位经规则根 model-tiers.md（config.yaml 段可覆盖，T11，D4〔grill-amendment〕）
```

## 五、决策

- **D1 盘面即状态**〔TG-23〕：不设可变 state 文件——change 目录产物即台账（产物在=步完成）。备选"显式 .ship-state 文件"弃：第二真相源，与产物必然漂移（正是 INDEX reindex 教训的反面）。代价 = 结论行格式成为契约（D5 钉字面 + 单测锚定）。
- **D2 gate 双输出**〔OQ1 裁定〕：stdout 第一行人读摘要（弱模型可照抄进对话），第二行起 JSON（机读）；退出码承载门禁语义（0/3/4/5，见 §四）。
- **D3 T10 决策协议**（写进 sdflow-ship SKILL.md + workflow.md 决策 4）：阶段三遇 ≥2 方案——①客观判据可判（测试/断言/基准）→ 自动选 + 记理由；②无客观判据 → 派对抗镜复核推荐项，通过才自动选（复核记录进报告）；③复核不过/无从复核 → defer 进 todolist + hand-off。**禁"有把握"类自评置信作为唯一依据**。
- **D4 T11 model-tiers = bundle 规则文件 + config 覆盖**〔grill-amendment，Q4=C——推翻 ff 稿"内联缺省×4"：5 处同步面重蹈 copy 漂移债（T17 同病），且规则全局解析机制现成〕：新建 bundle 规则文件 `assets/workflow/model-tiers.md`（档位定义 + 职责清单〔强档：verify/对抗裁决/final 终审；中档：领域镜/生成/实现；弱档：纯机械步〕+ canonical 缺省 opus/sonnet/haiku + adr/0006(c) 措辞），经 resolver 全局解析为**单一真相源**；消费仓 `config.yaml` 的 `model-tiers` 段降为**可选 per-repo 覆盖**（template 注释指向规则文件）；四个编排 SKILL.md 各只留一句"档位与缺省见规则根 `model-tiers.md`；config.yaml model-tiers 段可覆盖映射"——**零内联模型名**。bundle 新增规则 → snippets/index-section.md 规则表 + INDEX 同步。
- **D5 机判锚点 = 机器注释行**〔grill-amendment，推翻 ff 稿的"结论行正则"——grill 取证：正则 `结论[：:]\s*(PASS|FAIL)` 对两份真实存档 `结论：**PASS**` 全 miss、`建议进 /sdflow-done` 对带反引号实档 miss，自然语言措辞漂移是已发生事实〕：三个报告各以**模板写死的 HTML 注释行**为唯一机判锚点，人读正文自由漂移：
  - `<!-- ship-gate: design-approved -->`（设计门拍板回写报告时随手落——拍板本就回写）
  - `<!-- ship-gate: verify=PASS -->` / `verify=FAIL`（sdflow-done 的 verify-report 模板固定输出）
  - `<!-- ship-gate: code-review=pass -->` / `=blocked`（sdflow-code-review 报告结论区模板）
  gate 解析降为 `grep -F`（零正则）；双向钉死 = 三个 SKILL.md 报告模板写死输出 ↔ ship_gate 头注释列同一组字面，单测断言。存量归档报告无此行——**不需兼容**（gate 只服务未来 change）。这是 opsx-init token 模式的复用（rebrand 已实证 token 抗文案漂移）。
- **D6 T20 串行句**：sdflow-spec-review Step2 首句加"**MUST 待 Step1 checkpoint 完成后才 fan-out，禁止与 Step1 并行**（多镜评审对象须含 autoplan amendment）；若历史运行已并行，Step3 裁决须 diff autoplan amendment 增量核对并在报告注明"。
- **D7 起跑不越门**：REFUSE_START 是 ship 的硬前置（adr/0004 红线的机判化）；ship 自身绝不代拍设计门。
- **D9 结论新鲜度 + resume/干预语义**〔grill-amendment，Q5/Q6=C〕：gate 对每份门禁报告加**新鲜度规则**——取该报告文件最后一次提交，其后**存在触及 `openspec/` 之外路径的提交** → 该步结论（PASS/FAIL/blocked 一律）判**陈旧** → NEXT=重跑该步；**产物存在但无锚行 = 步进行中** → 同样重跑。由此获得：①verify FAIL 修复后重调不卡死（FAIL 陈旧→重验）；②干预后旧 PASS 不背书新代码（假✅路径焊死）；③**人机同权**——gate 只认盘面不辨产者，人工手跑某步/手写产物同样被认，**手改锚行 = 显式越权通道**（git 留痕可审计）；④**暂停语义** = ship 零跨步内存状态，停即停、重调 `/sdflow-ship` 即续；实现中断的 resume 由 gate 输出已完成任务号集（checkpoint 标签），ship 传给 SDD dispatch 勿重派。正常尾流不误伤（archive/commit 只触 openspec/，PASS 保鲜）。**残余不设防**：`--amend`/rebase 历史改写可骗过时点法（单人仓 + 不 squash 惯例，接受并记录）。
- **D8 ship 零 git 写操作 + 意图透传**〔grill-amendment，Q3=A〕：git 单向操作只存在于 sdflow-done 一处——ship 全程不 commit/merge/push（各子 skill 的 checkpoint 归其自身；ship 无产物故无自身 checkpoint）；调用语中的 merge opt-out（"别合并/跑到 merge 前停"类）由 ship **原样透传**给 sdflow-done；push 维持用户手动，SHIPPED 摘要提醒（toolkit 源仓场景附"push 后新会话 /sdflow-upgrade"句）。与 gate 零副作用同构：ship = 纯编排读者。

## 六、组件清单（TG-14）

| 组件 | 动作 |
|---|---|
| `sdflow-ship/SKILL.md` | 新建：chain 序列 + 每步前后调 gate + D3 决策协议 + 门禁上抛话术 + checkpoint 约定 |
| `sdflow-ship/scripts/ship_gate.py` + `tests/` | 新建：§三逻辑 + D2 输出 + D5 锚点解析；pytest 全盘面态 |
| `config.template.yaml`（assets） | 加 `model-tiers` 段（D4） |
| `sdflow-done` / `sdflow-spec-review` / `sdflow-code-review` SKILL.md | 模型节引用 model-tiers（缺省保底）；spec-review 另加 D6 串行句 |
| `assets/workflow/workflow.md` | 阶段三步骤表加 `/sdflow-ship` 编排入口行 + 决策 4 按 D3 改写；instance 走 update --dev |
| README / ROADMAP / adr-0004 | 列表加行 / 行更名 sdflow-ship + 状态 / 标题与暂名句同步注记（其自带条款） |
| T10/T11/T20 | 完成后 set-status DONE 带 evidence（commit/文件:行） |

## 七、风险 → 缓解

- [结论行格式漂移致 gate 误判] → D5 双向钉死（脚本+SKILL 报告格式节）+ 单测断言字面；报告生成方与解析方同仓同 change 演进。
- [外部 skill 产物形态变化] → 〔grill-amendment〕完成判据主锚改为**本仓自有** checkpoint 标签约定（git 历史，durable）；〔spec-review-amendment D7 改述〕**主锚分子 N 的提取（plan `### Task \d+:` 标题计数）仍强依赖上游 writing-plans 模板格式（本地已见 3 个缓存版本），并非整体降级为辅**——缓解：标题命中 0 → 显式 UNKNOWN（不猜）；标签 `task<N>-` 前缀随本 change 升格为契约（**注入点=plan 生成层：writing-plans 派发 args 要求每任务 commit 步显式用 checkpoint 脚本，由 implementer 执行**〔D1〕，写进 workflow.md 步 6 prompt 与 sdflow-ship SKILL）；双通道皆不可判 → UNKNOWN 停上抛（不猜）。
- [ship 在消费仓跑但该仓无阶段三产物约定] → gate REFUSE_START 已兜（无 spec-review-report 即拒）；报错文案指引 workflow 步骤。
- [弱主模型无视 gate 判定继续跑] → SKILL.md 措辞禁止性（MUST follow gate verdict）+ verify 终门仍在链尾兜底；残余接受（机队锚定的已知边界）。

## Compliance

ship_gate 只读不写（无副作用）；不越 grill/设计门两个人类点（D7 机判化 adr/0004 红线）；门禁传播遵反静默元原则；无 DB/外部服务（D-2/TG-24 N/A）。
