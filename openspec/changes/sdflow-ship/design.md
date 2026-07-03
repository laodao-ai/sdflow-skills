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
        │         实现完成判据 = plan 内任务复选框全勾 ∨ SDD ledger 全 complete(存在才查)
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
- **门禁传播** = 从产物**结论行**机判（verify-report「结论：PASS/FAIL」、code-review-report 结论区、spec-review-report 拍板行）——沿用两轮实践已形成的报告格式约定，本 change 把它们升格为**机判锚点字面约定**（D5）。

## 四、组件拓扑（TG-14）

```
  sdflow-ship/SKILL.md ──每步前后调──▶ scripts/ship_gate.py（只读 change 目录,无副作用）
        │                                    │ stdout: JSON{verdict,next,missing,reason}+一行人读摘要
        │ chain（不取代）                     │ exit: 0=可推进 / 3=REFUSE_START / 4=BLOCKED / 5=VERIFY_FAIL
        ▼                                    ▼
  embedded-test-sop(条件) → writing-plans(→subagent-dev) → sdflow-code-review → sdflow-done(→merge)
        规则/清单经 resolve-workflow.sh；模型档位经 config.yaml model-tiers（T11，D4）
```

## 五、决策

- **D1 盘面即状态**〔TG-23〕：不设可变 state 文件——change 目录产物即台账（产物在=步完成）。备选"显式 .ship-state 文件"弃：第二真相源，与产物必然漂移（正是 INDEX reindex 教训的反面）。代价 = 结论行格式成为契约（D5 钉字面 + 单测锚定）。
- **D2 gate 双输出**〔OQ1 裁定〕：stdout 第一行人读摘要（弱模型可照抄进对话），第二行起 JSON（机读）；退出码承载门禁语义（0/3/4/5，见 §四）。
- **D3 T10 决策协议**（写进 sdflow-ship SKILL.md + workflow.md 决策 4）：阶段三遇 ≥2 方案——①客观判据可判（测试/断言/基准）→ 自动选 + 记理由；②无客观判据 → 派对抗镜复核推荐项，通过才自动选（复核记录进报告）；③复核不过/无从复核 → defer 进 todolist + hand-off。**禁"有把握"类自评置信作为唯一依据**。
- **D4 T11 model-tiers**：config.template.yaml 新段（强档：verify/对抗裁决/final 终审；中档：领域镜/生成/实现；弱档：纯机械步；各档 default: opus/sonnet/haiku）；四个编排 SKILL.md 模型节改"档位定义与映射见 config model-tiers（缺省 opus/sonnet/haiku）"——**内联缺省保底**，无段不失效（消费仓零硬依赖）。
- **D5 机判锚点字面约定**〔OQ2 裁定〕：拍板标记 = 报告含正则 `设计门拍板` 行；verify 结论 = `结论[：:]\s*(PASS|FAIL)`；code-review blocker = 结论区 `BLOCKED|真 blocker` 且无 `建议进 /sdflow-done`。约定写进 ship_gate.py 头注释 + 对应 SKILL.md 报告格式节（双向钉死），单测各态覆盖。
- **D6 T20 串行句**：sdflow-spec-review Step2 首句加"**MUST 待 Step1 checkpoint 完成后才 fan-out，禁止与 Step1 并行**（多镜评审对象须含 autoplan amendment）；若历史运行已并行，Step3 裁决须 diff autoplan amendment 增量核对并在报告注明"。
- **D7 起跑不越门**：REFUSE_START 是 ship 的硬前置（adr/0004 红线的机判化）；ship 自身绝不代拍设计门。

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
- [外部 skill 产物形态变化（superpowers-plan 复选框）] → gate 对 6/7 完成判据用"任务复选框全勾 ∨ SDD ledger"双通道；都缺 → 判 UNKNOWN 停上抛（不猜）。
- [ship 在消费仓跑但该仓无阶段三产物约定] → gate REFUSE_START 已兜（无 spec-review-report 即拒）；报错文案指引 workflow 步骤。
- [弱主模型无视 gate 判定继续跑] → SKILL.md 措辞禁止性（MUST follow gate verdict）+ verify 终门仍在链尾兜底；残余接受（机队锚定的已知边界）。

## Compliance

ship_gate 只读不写（无副作用）；不越 grill/设计门两个人类点（D7 机判化 adr/0004 红线）；门禁传播遵反静默元原则；无 DB/外部服务（D-2/TG-24 N/A）。
