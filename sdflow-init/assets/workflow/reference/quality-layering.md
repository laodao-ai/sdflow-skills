# 质量分层：Prevention / Inline Detection / Residual（shift-left）

> **定位**：回答"代码生成质量很高，后面还要那么多次 review 吗？"——不是砍 review，而是
> **把标准前移进生成期已有的审查口，消掉事后 review 的冗余**。与 [`spec-review.md`](../spec-review.md)
> §一（review 只做 prevention 焊不住的残差）同一条铁律，在**代码层**的展开。
> **〔P3c 校准〕"消冗余" ≠ "sdflow-code-review 变可选"**——见 §五：事后 sdflow-code-review **每次全跑**做独立强制主审，
> shift-left 消的是通用质量的重复查，不是 sdflow-code-review 本身。

---

## 一、生成期已经焊进三层 review（不是裸生成）

`superpowers:subagent-driven-development` 内部**自带**一条多层评审流水线（读其 SKILL + 模板得出）：

```
每任务:  implementer TDD + 自审 + commit
         → task-reviewer(fresh 子agent, "Do Not Trust the Report")出双判决: spec 合规 + 代码质量
         → Critical/Important 进 fix 循环, re-review 到 Approved
全任务后: final whole-branch reviewer(最强模型, fresh context)
```

**关键**：这些 reviewer 都是 **fresh-context 独立子 agent**。所以"独立性"——我们一直强调的卖点——
**生成期内部已经有了**。事后 `/clear + /sdflow-code-review` 再加的独立性只是"脱离 controller 的全冷独立"，边际收益。

## 二、但它们查的是**通用 rubric**，不是我们的领域清单

task-reviewer / final-reviewer 的检查项是 `clean separation / error handling / DRY / edge cases /
tests verify real behavior / architecture / security`——**纯通用**。它们**完全不碰**
`code-checklists/domains/` 的领域 CR-*（嵌入式看门狗/flash 寿命/ISR、芯片 AT 超时、并发锁序…）。

| 维度 | 生成期已做? | 事后 review 重复? |
|---|---|---|
| spec 合规（建的=要的） | ✅ task-reviewer Part 1 | Step1 自持 scope 审计 **部分重复** |
| 通用代码质量（CR-01~09 base） | ✅ 三层都查 | /sdflow-code-review base **大幅重复** |
| **领域规则（CR-EMB/ML307C/ESP32/GO）** | ❌ 通用 rubric 盲区 | **真残差** ← 唯一不可替代 |
| scope-drift / 计划完成度 | ⚠️ 部分 | Step1 自持 scope 审计补全 |
| 全冷独立（脱离 controller） | ❌ 终审仍 controller 裁决 | /sdflow-code-review 补，但边际 |
| PR 级 DB/API/Auth 改动 | ❌ | 官方 code-review |

**结论**：后置 review 的**通用质量部分是冗余**；真正残差只剩 **领域规则 + scope-drift + PR 风险 + 一点冷独立**。

## 三、机会：两个 shift-left 注入点（把标准前移进生成期）

`writing-plans` / `subagent-driven-development` **自带两个官方注入口**：

```
注入点 A:  plan 的 Global Constraints
           writing-plans 把 spec 的项目级约束逐字拷进每个任务，implementer + task-reviewer 都看得到
           → 既是 prevention（按约束写）又是逐任务 inline detection（每任务审 + fix 循环）
           ★ 我们的 spec 已被 /sdflow-spec-review 按 spec-checklists/domains 审过 → 好的 spec 自带领域约束
             → 自动流进 Global Constraints。这条已半通：保证 design 的领域约束确实进了 plan 即可。
           ⚠️ 边界：SKILL 明确反对往【逐任务】reviewer 塞【宽泛清单】（"global-constraints 要 verbatim
             绑定项，不是 rubric；宽 rubric 留给终审"）。故注入点 A 只塞【该任务相关的具体领域约束】（逐字）。

注入点 B:  final whole-branch reviewer 的 rubric  ← 最大杠杆
           subagent-driven-development 终审默认用 requesting-code-review 的【通用】模板；
           dispatch 时把 rubric 增强为「通用模板 + 命中栈的 code-checklists/domains/<栈>」
           → 领域审在循环内、终审一次做掉，而非事后再单独跑 /sdflow-code-review。
```

## 三点五、如何注入 + 升级安全（绝不改插件）

**铁律：绝不编辑 superpowers 插件文件。** 注入发生在 **dispatch 时**，指令放**我们自己的仓**。

```
✗ 改 ~/.claude/plugins/cache/.../superpowers/<version>/skills/.../code-reviewer.md
   → 插件升级换版本目录(cache 里已有 5.1.0 / 6.0.3 两份)，改动被覆盖丢失
✓ 内容(code-checklists/) + 指令(workflow.md step prompt) 都在本仓 → 升级动不到
```

- **注入点 A（搭便车，零额外动作）**：`writing-plans` 本就把 spec 约束逐字拷进 plan 的
  Global Constraints，`task-reviewer` 自动可见。我们只需保证 design 的领域约束确实写进 plan，不碰插件。
- **注入点 B（在 step prompt 加一句）**：终审 dispatch 由 **controller（跑 skill 的主 session）组装**，
  `code-reviewer.md` 只是模板。在 `workflow.md` step-9 prompt 写「终审 dispatch 附
  `@openspec/workflow/code-checklists/domains/<命中栈>` 作额外 review lens」即可——SKILL 自己也说
  宽 rubric 属终审（逐任务才禁塞宽清单），是顺着设计做。

**升级安全三重保险**：① 内容+指令都在本仓，升级只换插件自己的版本目录；② 与 `config.yaml`
升级安全同构（定制在自己侧，不改上游包）；③ 指令按**行为**措辞（"凡跑终审就附清单"），
不绑死插件内部文件路径——未来插件重构终审，只要还有"终审"步，指令依旧成立。

## 四、与 spec 侧同构（同一个元模式）

```
        Prevention(建对)             Inline Detection(循环内抓)          Residual(冷,事后)
 spec:  config.yaml 结构+D 约束      grill / 生成对话                    sdflow-spec-review(validation+对抗+接地)
 code:  plan Global Constraints+TDD   逐任务双判审 + 终审(subagent-dev)    sdflow-code-review(领域+冷独立+scope)
                                      ↑ 把 code-checklists 注入 B ↑       ↓ 消通用质量冗余,非缩掉 sdflow-code-review ↓
```

设计侧用 config 固化结构/约束（prevention），让 sdflow-spec-review 只做残差；
代码侧把领域清单注入 plan 约束 + 终审 rubric（prevention + inline detection），让 sdflow-code-review 只做残差。
**同一手法，两层对称。**

## 五、对 workflow 的影响：sdflow-code-review 是每次全跑的独立强制主审（P3c）

> **〔grill-amendment / P3c〕** 本节早前据注入点 B 推出"事后 sdflow-code-review 缩成薄残差、高风险才跑冷独立抽查"——
> **此推论已被否决**。注入点 B 确实把领域审前移进生成循环（即时 fix+re-review 闭环），但那**不使事后
> sdflow-code-review 变边际**。

- **sdflow-code-review 每次全跑·独立冷·强制主审**：实测能抓出生成循环内被 hot controller 说服放过的真问题——这是
  shift-left 消不掉的价值（循环内 reviewer 冷、但 controller 热；事后 sdflow-code-review 完全脱 controller）。
- **注入点 B 与 sdflow-code-review 并存不是重复**（见 workflow.md §三.6 / design §7.2）：前者循环内即时闭环、便宜早修；
  后者事后独立兜底网。机制/职责不同，**别把任一个优化掉**。
- shift-left 消掉的是**通用质量的冗余**（CR base 三层已查），不是 sdflow-code-review 本身。sdflow-code-review 编排器
  Step1 自持 scope 审计（scope-drift + 完成度），Step2 并入领域镜 + 对抗镜 + 历史镜 + 置信过滤，合成一份 code-review-report.md。
- **无 `/clear`（G1）**：独立性由评审 fan-out 的 fresh 子代理给，不由 `/clear` 给。
  - 🔴 **本条的射程仅限「评审独立性」，MUST NOT 据此推出「全流程不用 `/clear`」**——`/clear` 还有本条谈不到的其它作用（见下面两处交界例外的理由）。
  - 🔴 **具名例外（两处，均在阶段交界：一处是 `/sdflow-spec` 的出口，一处是 `/sdflow-ship` 的入口）**：
    - **`/sdflow-spec` 的「阶段一→阶段二」交界**——出口序列 `/clear` → 换档 → `/sdflow-spec-review` 里那次 `/clear` 是**允许的**。
      **理由两条，都在 G1 的论证范围之外**：① **cache 按模型隔离**（拖着阶段一旧上下文切档 = 全价重付）；
      ② **产 / 审错档纪律**（阶段一产出档 ≠ 阶段二评审档，换档才是真实动因）。
    - **设计门 →「阶段三」交界**（`/sdflow-ship` 之前）——**理由三条，同样在 G1 射程之外**：① **盘面纪律**（阶段三「零跨步内存状态」，
      `NEEDS_CONTEXT` MUST 仅从盘面自答；热编排器会拿对话记忆替代盘面，而 **fresh 子代理防不住这一条**——implementer 冷、回答它的编排器热）；
      ② **产物自足性检验**（冷启动是对四件套/tickets 够不够用的真实检验，热 session 会无声补上、缺口永不暴露）；③ **去作者偏置**。
      **代价**：编排器需重读 SKILL 与产物，且 MUST 在调 `/sdflow-ship` 时重述 merge 意图（不在盘上）。
    本节这条 G1 谈的是**独立性**，成本 / 档位 / 盘面纪律 / 自足性都不在其射程内 ⇒ 两处例外均不与之矛盾。
  - 🔴 **MUST NOT 拿「主审裁决需要冷视角」当任一处例外的理由**——本节上面几行已正面回答过它
    （事后 sdflow-code-review 的冷来自**独立编排器 + fresh 子代理 fan-out**，不来自 `/clear`）。
  - **边界**：仅这两处**阶段交界**。**阶段内部一律禁 `/clear`**——阶段二内部、阶段三内部（含 subagent-dev / sdflow-implement
    调度期间、code-review→done 交接）；阶段三内部需控上下文用 **`/compact` 而非 `/clear`**（merge 意图不在盘上、`VERIFY_FAIL` 恢复要重建理解，
    而 done 的 verify 本就是冷子代理）。

TG 驱动的是**领域镜的选取 + outside voice 是否走 cross-model**（命中 HR-TG 才单开领域 cross-model），
**不是"sdflow-code-review 跑不跑"**——sdflow-code-review 每次都跑。

## 六、检查清单（用 superpowers 跑实现时）

- [ ] design 的领域约束是否确实进了 plan 的 **Global Constraints**（注入点 A）？
- [ ] 终审 dispatch 是否把 rubric 增强为 **通用模板 + 命中栈 code-checklists/domains**（注入点 B）？
- [ ] sdflow-code-review 是否**每次全跑**（P3c 独立冷强制主审，非高风险才跑）？Step1 自持 scope 审计的 scope-drift + 完成度？
- [ ] 是否**没有**在**阶段内部**依赖 `/clear`（G1：fresh 子代理即独立性；子 agent 调度中禁清）？
      **例外 = 两处阶段交界**：① `/sdflow-spec` 的阶段一→阶段二那一次（理由 = cache 按模型隔离 + 产/审错档）；
      ② 设计门→阶段三那一次（理由 = 盘面纪律 + 产物自足性检验 + 去作者偏置）。两处**都不是**「主审需冷视角」。

*方法论 v2（P3c：sdflow-code-review 每次全跑强制主审）· 项目无关 · 配套 spec-review.md（设计侧残差）/ code-checklists/（领域清单）/ workflow.md（编排）*
