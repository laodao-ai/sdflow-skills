# 自制 skill 展开 · `sdflow-spec-review`

> 属 [工作流总览](../workflow-overview.md) 的展开。这是**阶段二设计审的主审编排器**（第 4 步）——
> 把 `autoplan` 广审 + 本项目多镜合成**一份** `spec-review-report.md`，交阶段二唯一人类门（设计 HARD-GATE）拍板。
>
> **一句话**：Step1 autoplan（广审，原生）→ Step2 并行多镜（领域/对抗/接地）→ Step3 对抗裁决 + 决策登记 → 一份报告。
> 取代旧「autoplan + spec-review 各出报告 + 人工手动合并」。

> **与外部黑盒的关系**：它**内部调度** [autoplan](./gstack-autoplan.md)（Step1）+ [outside-voice.sh](#4-内部调度的子-skill--子代理--脚本)（跨模型第二意见）。
> autoplan 的「建议式 vs 强制」见其文档；本文讲 **sdflow-spec-review 自身**的机械兜底与自觉纪律。

---

## 1. 位置与契约

| 维度 | 内容 |
|---|---|
| 谁调它 | 阶段二第 4 步；或 `/sdflow-ship` 的 pre-flight 之前（设计门属人类点，ship 不跨） |
| 进（输入） | `{change_dir}` 四件套（proposal/design/specs/tasks）+ 真实代码 |
| 出（产物） | `spec-review-report.md`（决策登记区 + 各镜 findings + 裁决 + lens-metric 度量锚〔config `metrics.enabled` 开时〕）；`gstack-review.md`（autoplan 落盘）；design/specs 改动标 `[spec-review-amendment]`；拍板**发生后**主 session 立即在报告头部 **prepend frontmatter 首块** `ship-gate:` → `design_approved: true`（`/sdflow-ship` pre-flight 唯一机判依据；旧 inline HTML 注释锚已退役，见 §2 两套锚分工） |
| 两条连续性铁律 | **G1** 不依赖 `/clear`（独立性靠子代理 fresh 上下文）；**G2** 中途不 AskUserQuestion（决策登记进报告，设计门一次拍板） |

---

## 2. 内部流程

```mermaid
flowchart TD
    S0["Step0 · 确认对象 + resolve-workflow.sh 解析规则根<br/>exit2 → 显式降级通用评审 + 转发 stderr（不静默）"]
    S1["Step1 · autoplan 广审（原生执行）<br/>主 session 落盘 gstack-review.md（mode=native 锚）→ 吃 findings"]
    OVG{"outside-voice 复用守卫（三前置）<br/>来源 native? · 新鲜? · 结构可解析?"}
    OVS["回落自跑 design-voice（outside-voice.sh）"]
    CP1["[checkpoint] spec-review-autoplan（P2c 第1次）"]
    S2["Step2 · 规划镜头 + 并行 fan-out<br/>领域镜 + 对抗镜×2~3 + 接地镜×1 + HR-TG cross-model"]
    S3["Step3 · 综合 + 对抗裁决 → 决策登记<br/>合并去重 · 反静默压制 · 置信分流 · anchor_lint 锚自检"]
    CP2["[checkpoint] spec-review（P2c 第2次）"]
    S4["Step4 · 产出 spec-review-report.md + 收敛口"]
    GATE{{"★设计 HARD-GATE（人类门，不在本 skill 内）"}}
    S0 --> S1 --> OVG
    OVG -->|三关全过| CP1
    OVG -->|任一不过| OVS --> CP1
    CP1 --> S2 --> S3 --> CP2 --> S4 --> GATE
    GATE -.拍板后.-> ANCH["主 session prepend frontmatter 首块<br/>ship-gate.design_approved: true"]
```

| 步 | 目标 | 注意事项 |
|---|---|---|
| 0 | 确认对象 + 解析规则根 | `resolve-workflow.sh` exit2 → **显式降级 + 转发 stderr**，绝不静默当「本项目无此层」 |
| 1 | autoplan 广审、吃 findings | **原生执行**（指令进主 session，禁派子代理转述）；主 session 汇总落盘 `gstack-review.md` 写 `mode="native"` 锚 + 侧信道佐证；**串行纪律 T20**：MUST 待本步 checkpoint 完成才 fan-out |
| 1·守卫 | 复用还是自跑 outside-voice | 三前置：①来源（simulated 视同无效）②新鲜度（早于最新改动视同缺失）③结构（解析不出 codex 段/0 条）。任一不过 → 打印原因码 + 回落自跑 design-voice |
| 2 | 规划并 fan-out 多镜 | **防重叠 1.4**：autoplan 已含 eng 镜 → 领域镜**不重复跑 eng**；HR-TG 命中单开领域 cross-model，写 v1 锚行 |
| 3 | 对抗裁决 + 决策登记 | **反静默压制**（Q3）：裁掉的 finding 连理由进「已裁掉」区；**置信分流**：高采信/中标需确认/低仍上抛一行，**不照搬 <80 数值一刀切**（设计漏掉代价高，优化召回）；**锚行自检（确定性脚本门）**：调 `$RULES_ROOT/tools/anchor_lint.py --layer spec-review --trigger-catalog $RULES_ROOT/trigger-catalog.md` 机验 4 类正文 v1 锚（step1-broad-review / hr-tg / outside-voice / lens-metric），exit 1=违规 / 2=fail-closed **均阻塞本步** |
| 4 | 出报告 + 拍板回写 | **度量锚**：config `metrics.enabled` 开时构造 roster+findings 调 `lens_metric_emit.py`——**exit 0 才**把其 stdout 落进报告，非 0 fail-closed **不落、禁手拼锚行顶替**；缺省/`false` → 不落锚、不调 emitter。拍板**发生后**主 session 立即在报告头部写 frontmatter `ship-gate:` → `design_approved: true`（已有首块则合并键入该块、不新开第二块，无则 prepend 新建；`/sdflow-ship` pre-flight 唯一机判依据） |

**决策登记区**：`[自动决策]`（默认接受可覆盖）/ `[需拍板]`（≥2 方案或核验不了的事实）/ `[已裁掉]`（原始发现 + 裁掉理由）/ `TENSION`（voice 与主审分歧，两方视角 + 推荐 + 后果）。

**两套锚分工（勿混述为一套）**：
①**正文 4 类 v1 锚**（step1-broad-review / hr-tg / outside-voice / lens-metric）归 `anchor_lint.py` 机验。**诚实拦截力**：此门只挡「同一会话内忘记跑这步」，**挡不住「整段跳过本步」**；`findings=N` 等数值与合并池实收数的一致性仍是**主 session 信任边界**、非机械可验——脚本不谎称保证数值正确。
②**ship-gate 机判锚**在报告头部 **frontmatter 首块**（`ship-gate:` → `design_approved: true|false`，严格 bool），归 `ship_gate.py` 读——只认文件首块、只认 `ship-gate:` 直接子键层；live 读坏 frontmatter fail-closed UNKNOWN(6)。旧 inline HTML 注释锚（`<!-- ship-gate: design-approved -->`）已随 mlh-p5 迁移**彻底退役**：live 与归档读半场均不再读（T75 已删该锚常量）；归档 dual-read 兜底仅保留给 verify 锚（verify-report.md），与 design_approved 无关。

**反馈回路免责**：本 skill 只落 lens-metric 锚——跨 change 归档后的锚聚合、按采纳率/独立率复评、显著性提示一律归 `/sdflow-retro`（只读聚合）；是否砍镜/降采样/收紧触发/淘汰某镜**永远人决**，本 skill 不自行判断或执行。

---

## 3. 镜头规划 + model

| 镜 | 数量 | 干什么 | 档位 |
|---|---|---|---|
| 主 session | 1 | 协调 / 对抗裁决 / 决策登记 / 出报告 | **强档**（门禁，弱档=假绿） |
| 领域镜 | 每命中领域 1 | 过 `spec-checklists/domains/<栈>` R 项 | 中档 |
| 对抗镜 | 2~3（高风险 3） | 各从一角度「证明 spec 实现期会爆」（隐藏假设/失败模式/乐观边界） | 中档 |
| 接地镜 | 1 | grep/读真实代码核验 spec 里所有代码事实 | 弱档 |

---

## 4. 内部调度的子 skill / 子代理 / 脚本

| 被调 | 类型 | 角色 / 契约 |
|---|---|---|
| [`autoplan`](./gstack-autoplan.md) | 原生执行（进主 session） | Step1 广审；其 eng 镜与本 skill 多镜不重复 |
| 领域/对抗/接地镜 | fresh-context 子代理 | 一条消息内全部派出，返回结构化 findings（问题/证据 file:line/置信/严重度/建议），**禁 AskUserQuestion** |
| `outside-voice.sh` | 确定性脚本（退出码契约） | runner 由 `resolve-models.sh` 判的宿主决定（Claude 宿主→codex，Codex 宿主→claude，MUST NOT 硬编码 codex）；preflight `ready`→目标 runner；exit0=findings（锚 `host="$SDFLOW_HOST" runner="$SDFLOW_VOICE_RUNNER" reason_code="ok"`，跨模型）、exit124→fallback（`timeout`）、exit3→拒发不 fallback（`secret-hit`，密钥）；畸形/非零→同宿主只读子代理 fallback（锚 `runner==host`，`claude-fallback` 枚举值已废弃） |
| `resolve-workflow.sh` | 脚本 | 两步链解析规则根（全局 canonical；本地 pin 分支已随 `adr/0039` 删除）；不硬编码 `openspec/workflow/` |
| `anchor_lint.py` | 确定性脚本（退出码契约） | Step3 出报告后锚自检（`--layer spec-review --trigger-catalog $RULES_ROOT/trigger-catalog.md`，后者为 M2/M-new 前提、必需参数）：机验 4 类正文 v1 锚存在性 + lens-metric 字段/枚举；0=CLEAN、1=违规、2=fail-closed，**非 0 阻塞本步** |
| `lens_metric_emit.py` | 确定性脚本（fail-closed） | Step4 度量锚 emitter（config `metrics.enabled` 门控，缺省/`false` 不调）；**exit 0 才**落其 stdout 进报告，非 0 不落、禁手拼锚行 |
| `checkpoint-commit.sh` | 脚本 | 步末过场提交（P2c 两次） |

---

## 5. 人类门

**全流程唯一人类门在本 skill 之后**——设计 HARD-GATE（用户过一份报告拍板）。本 skill 内部**中途不 AskUserQuestion**（G2）：撞到 ≥2 方案/核验不了的事实 → 写进决策登记区，继续跑完。人工设计门时一次性摊开选项 + 推荐 + 两方后果拍板。

---

## 6. ★ 本 workflow 注入的规则/prompt —— 建议式 vs 强制

**统一判据**见[总览 §8](../workflow-overview.md#8-外部-skill-的注入强制性建议式-vs-强制统一规律)。sdflow-spec-review 自己**既是被 workflow 约束的对象、又是往子镜注入的编排者**。它比外部 skill 多一层**机械兜底**（anchor_lint 锚自检、frontmatter 机判锚、lens_metric_emit、checkpoint 脚本）。

| 项 | 类型 | 靠什么 |
|---|---|---|
| **锚行自检**（Step3 调 `anchor_lint.py --layer spec-review`，exit 1=违规 / 2=fail-closed 均阻塞） | **强制（本 skill 内机械门）** | 确定性脚本机验 4 类正文 v1 锚——只挡「忘记跑这步」、挡不住「整段跳过」；`findings=N` 数值一致性仍是主 session 信任边界 |
| **拍板回写 frontmatter `design_approved: true`** | **强制（下游门读）** | `ship_gate` pre-flight 读报告头部 frontmatter 首块放行阶段三；不写=REFUSE_START(3)、坏 frontmatter=UNKNOWN(6) fail-closed |
| **lens-metric 度量锚 emitter**（`lens_metric_emit.py`） | **强制（fail-closed 脚本）+ config 门控** | `metrics.enabled` 缺省/`false` 不落不调；exit 0 才落 stdout，非 0 不落、禁手拼；roster 完备性/归类/誊写正确性仍是主 session 信任边界 |
| **反馈回路**（锚聚合 / 复评 / 砍镜降采样） | **不在本 skill 内** | 聚合归 `/sdflow-retro` 只读聚合；砍镜/降采样/收紧触发一律人决，本 skill 不自动执行 |
| **outside-voice.sh 调用契约** | **强制（退出码脚本）** | preflight/exec/exit 码确定性分支；密钥 exit3 拒发 |
| checkpoint 提交（P2c ×2） | **强制（脚本）** | `checkpoint-commit.sh` 固定 Conventional message |
| 「autoplan 原生执行、不派子代理转述」 | **半强制** | 报告写 `mode="native"` 锚 + 侧信道佐证；靠锚 + 主 session 遵从，非纯脚本 |
| **反静默压制**（escalate-not-drop） | **建议式（自觉纪律）** | 无脚本校验每条裁掉的都留了理由；靠主 session 遵从 SKILL.md 铁律 |
| **对抗裁决 / 置信分流 / 决策登记** | **建议式** | 强档主 session 判断，无机械校验；「不照搬 <80」也是纪律 |
| **model 档位选择**（主 session 强档等） | **建议式** | 无机制强制控制者真用强档；靠遵从 model-tiers |
| 防重叠 1.4 / 串行纪律 T20 | **建议式** | 靠主 session 遵从（T20 若历史并行，报告须注明——补偿式纪律） |

**结论**：sdflow-spec-review 的**流程完整性**由三道机械门兜底——**anchor_lint 锚自检**（漏跑某镜/outside-voice/度量锚会被脚本抓，但只挡「忘记跑」、挡不住「整段跳过」）、**frontmatter 机判锚**（不拍板回写 `design_approved: true` 不放行）、**checkpoint 脚本**；而**判断质量**（对抗裁决、反静默压制、置信分流、防重叠）是**自觉纪律**，靠强档主 session + SKILL.md 铁律，无逐条机械校验。这是刻意分工：**机械的交脚本焊死，判断的交强模型 + 下游门兜底**。

---

## 7. 小结

- 结构 = autoplan 广审 + 多镜 fan-out + 对抗裁决 → 一份报告 → 设计门拍板。
- **机械兜底**：anchor_lint 锚自检（4 类正文 v1 锚）、frontmatter `design_approved` 机判锚（下游 `ship_gate` 读）、lens_metric_emit fail-closed、outside-voice.sh 退出码、checkpoint 脚本。
- **自觉纪律**：反静默压制、对抗裁决、置信分流、防重叠、model 档位——靠强档主 session，无逐条校验。

---

*接地基线：2026-07-10 —— 对照 `sdflow-spec-review/SKILL.md`（第三步 anchor_lint 门 / 第四步 lens_metric_emit 与拍板回写 frontmatter）与 `sdflow-ship/scripts/ship_gate.py`（`FIELD_ENUMS` / `parse_ship_gate_frontmatter`）核实。ship-gate 机判锚已随 mlh-p5-gate-frontmatter（2026-07-07）迁至报告头部 frontmatter 首块，旧 inline HTML 注释锚彻底退役（归档 dual-read 兜底仅存 verify 锚半场，T75）。*
