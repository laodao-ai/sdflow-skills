# 质量分层：Prevention / Inline Detection / Residual（shift-left）

> **定位**：回答"代码生成质量很高，后面还要那么多次 review 吗？"——不是砍 review，而是
> **把标准前移进生成期已有的审查口，消掉事后 review 的冗余**。与 [`spec-review.md`](../spec-review.md)
> §一（review 只做 prevention 焊不住的残差）同一条铁律，在**代码层**的展开。
> **〔P3c 校准〕"消冗余" ≠ "sdflow-code-review 变可选"**——见 §五：事后 sdflow-code-review **每次全跑**做独立强制主审，
> shift-left 消的是通用质量的重复查，不是 sdflow-code-review 本身。

---

## 一、生成期已经焊进 review（不是裸生成）

`sdflow-implement`（tickets 轨，阶段三唯一实现管线）内部**自带**一条评审流水线——设计脉络借鉴自
已退役的 superpowers `subagent-driven-development`（reviewer 模板 / pre-flight 冲突扫描，见其自身
`SKILL.md` 附录 B 出处说明），机制现况：

```
每 ticket:  implementer TDD + 自审 + commit
            → 双轴审(fresh 子agent×2, "Do Not Trust the Report") 并行出双判决: Standards 轴 + Spec 轴
            → Critical/Important 进 fix 循环, re-review 到 Approved
出票收尾:   全 ticket 语义一致性自扫(T10-choice 无人类门自主裁决，取代原版"批量呈给人拍板")
```

**关键**：这些 reviewer 都是 **fresh-context 独立子 agent**。所以"独立性"——我们一直强调的卖点——
**生成期内部已经有了**。事后 sdflow-code-review（独立编排器 + fresh 子代理 fan-out）再加的独立性只是"脱离 controller 的全冷独立"，边际收益。

## 二、但它们查的是**通用 rubric**，不是我们的领域清单

双轴审 Standards 轴的基线检查项是 `clean separation / error handling / DRY / edge cases /
tests verify real behavior / architecture / security`——**通用部分**注入 Fowler smell 基线；
`code-checklists/domains/` 的领域 CR-*（嵌入式看门狗/flash 寿命/ISR、芯片 AT 超时、并发锁序…）作为
Standards 轴 dispatch 模板**必填槽**已前移进循环（见 `sdflow-implement/SKILL.md`「每 ticket 双轴审」节），
不再是通用 rubric 盲区。

| 维度 | 生成期已做? | 事后 review 重复? |
|---|---|---|
| spec 合规（建的=要的） | ✅ Spec 轴 | Step1 自持 scope 审计 **部分重复** |
| 通用代码质量（CR base） | ✅ Standards 轴 | /sdflow-code-review base **大幅重复** |
| **领域规则（CR-EMB/ML307C/ESP32/GO）** | ✅ Standards 轴必填槽已注入 | **冷独立兜底**（见下方 P3c，非"唯一残差"） |
| scope-drift / 计划完成度 | ⚠️ 部分 | Step1 自持 scope 审计补全 |
| 全冷独立（脱离 controller） | ❌ 双轴审仍 implementer/controller 同轮次 | /sdflow-code-review 补，但边际 |
| PR 级 DB/API/Auth 改动 | ❌ | sdflow-code-review |

**结论**：后置 review 的**通用质量部分是冗余**；真正残差只剩 **领域规则 + scope-drift + PR 风险 + 一点冷独立**。

## 四、与 spec 侧同构（同一个元模式）  <!-- §三已退役（remove-superpowers-pipeline），编号保留供外部引用 -->

```
        Prevention(建对)             Inline Detection(循环内抓)          Residual(冷,事后)
 spec:  config.yaml 结构+D 约束      grill / 生成对话                    sdflow-spec-review(validation+对抗+接地)
 code:  plan Global Constraints+TDD   逐任务双判审                        sdflow-code-review(领域+冷独立+scope)
                                                                        ↓ 消通用质量冗余,非缩掉 sdflow-code-review ↓
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
- **逐任务双判审与 sdflow-code-review 并存不是重复**（见 workflow.md §三.6 / design §7.2）：前者循环内即时闭环、便宜早修；
  后者事后独立兜底网。机制/职责不同，**别把任一个优化掉**。
- shift-left 消掉的是**通用质量的冗余**（CR base 三层已查），不是 sdflow-code-review 本身。sdflow-code-review 编排器
  Step1 自持 scope 审计（scope-drift + 完成度），Step2 并入领域镜 + 对抗镜 + 历史镜，Step3 机械引用核 + 二元裁决，合成一份 code-review-report.md。
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
  - **边界**：仅这两处**阶段交界**。**阶段内部一律禁 `/clear`**——阶段二内部、阶段三内部（含 sdflow-implement
    调度期间、code-review→done 交接）；阶段三内部需控上下文用 **`/compact` 而非 `/clear`**（merge 意图不在盘上、`VERIFY_FAIL` 恢复要重建理解，
    而 done 的 verify 本就是冷子代理）。

TG 驱动的是**领域镜的选取 + outside voice 是否走 cross-model**（命中 HR-TG 才单开领域 cross-model），
**不是"sdflow-code-review 跑不跑"**——sdflow-code-review 每次都跑。

*方法论 v2（P3c：sdflow-code-review 每次全跑强制主审）· 项目无关 · 配套 spec-review.md（设计侧残差）/ code-checklists/（领域清单）/ workflow.md（编排）*
