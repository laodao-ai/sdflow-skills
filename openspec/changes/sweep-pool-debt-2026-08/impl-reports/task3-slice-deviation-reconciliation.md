# Task 3 impl-report：切片偏离对账接线（IO1）

## 做了什么

`sdflow-code-review/SKILL.md` 第一步（自持 scope 审计）：

1. **输入清单**加 `impl-reports/planning-decisions.md`（若存在，出票期「切片偏离: …」审计行）——
   紧跟在 proposal.md / tasks.md / design.md 之后，与 `DIFF_BASE..HEAD` diff 并列为审计输入。
2. 新增独立小节「**切片偏离对账**」（置于「输入」与「审计两轴」之间），标注来源
   〔impl-orchestration ADDED Requirement「切片偏离审计行 SHALL 被代码审 scope 审计对账消费」，
   sweep-pool-debt D6〕，三分支：
   - **无申报输入可对账（降级不中断）** —— design.md 无「切片建议」节，或
     `planning-decisions.md` 不存在 / 无「切片偏离」行 → 记「无偏离申报可对账」，按既有
     scope-drift 流程继续，MUST NOT 因该输入缺席报错中断。
   - **已申报核对** —— `planning-decisions.md` 含「切片偏离: …」行 → 逐条核对申报内容
     （增/删/合并票、改阻塞边、改切片边界）与实际 diff 是否相符；申报了未做、或做的超出申报
     ⇒ 以 finding 上报。
   - **静默偏离上报** —— diff 显示实际出票偏离了 design.md「切片建议」草图，但
     `planning-decisions.md` 无对应「切片偏离: …」申报行 ⇒ 以 finding 上报，MUST NOT 因
     「出票期对抗镜已复核」而略过——对抗镜只见申报面，不见未申报面。

未新增 finding 类型分类——沿用既有 `SCOPE-CREEP` 类（切片偏离是计划层 scope-drift 的一种表现，
基准④简化：新分类不带来额外可操作信息，Step3/Step5 现有的 `SCOPE-CREEP` 处理路径已够用）。

## 验收自查（无自动化测试，纯指令层改动）

`sdflow-code-review` 是纯 Markdown 编排类 skill（CLAUDE.md 明列：无 `scripts/`、无自动化测试）。
自查按「逻辑三分支完整性」+「与 delta spec Scenario 措辞对齐」两维核验：

| brief 复选项 | 状态 | 证据 |
|---|---|---|
| Step1 输入清单加 `impl-reports/planning-decisions.md` 切片偏离行 | ✅ | `sdflow-code-review/SKILL.md:245-247`（新增一行输入） |
| 对账逻辑三分支：静默偏离上报 / 已申报核对 / 无输入降级不中断 | ✅ | `SKILL.md:249-260`（三个子项逐条对应） |

逐 Scenario 对齐核验（`specs/impl-orchestration/spec.md`）：

1. **「静默偏离被 Step1 对账捕获」** —— spec 要求「出票实际偏离了 design.md『切片建议』草图
   但无对应『切片偏离: …』行 ⇒ 上报为 finding，MUST NOT 因对抗镜已复核而略过」。SKILL.md 「静默
   偏离上报」分支逐字呼应这两个条件（无申报行 + MUST NOT 因对抗镜已复核而略过），措辞与理由
   （「对抗镜只见申报面，不见未申报面」）与 spec Scenario 原句一致。
2. **「已申报偏离与 diff 核对」** —— spec 要求「核对每条申报是否与实际 diff 相符；不符（申报了
   未做、或做的超出申报）同样上报」。SKILL.md「已申报核对」分支逐字覆盖：核对对象列了四种切片
   偏离形态（增/删/合并票、改阻塞边、改切片边界，取自 `planning-decisions.md` 现有措辞），不符
   判据（未做/超出申报）与 spec 原句一致。
3. **「无申报输入时对账降级不中断」** —— spec 要求「design.md 无『切片建议』节，或
   `planning-decisions.md` 不存在/无该行 ⇒ 记录『无偏离申报可对账』，按既有流程继续，MUST NOT
   报错中断」。SKILL.md「无申报输入可对账（降级不中断）」分支三个触发条件与记录文案
   （「无偏离申报可对账」）均与 spec 原句逐字一致。

三分支互斥完整：覆盖「无输入」「有输入且核对通过/不通过」「无输入但 diff 有偏离（静默）」四种
组合中的三种命名分支——「有输入且核对通过」隐含在「已申报核对」分支内（核对相符则不产生 finding，
无需单独列支）。未发现 Scenario 与实现措辞的语义缺口。

## 并行安全

按 brief「执行说明」，本票与票 1（impl-review 重锚协议段）均改 `sdflow-code-review/SKILL.md`
但改动不同小节（本票动「第一步：自持 scope 审计」内的输入清单+新增小节；票 1 动 impl-review
重锚协议相关段）。本 worktree 未包含票 1 的改动（各票独立 worktree，尚未合并），故本次编辑未见
到票 1 内容、也未触碰任何非 Step1 范围的文本。

## 票外发现

无。
