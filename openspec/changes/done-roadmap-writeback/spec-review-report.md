# Spec Review Report — done-roadmap-writeback（第二轮）

> 阶段二设计评审 · 第二轮（审第二轮 grill 重构后的**归属镜像投影**骨架）。7 路冷审：广审(broad·simulated) + 对抗×3(adversarial) + 接地(grounding) + 哲学(domain) + outside-voice(claude-fallback·codex usage limit 回落)。

<!-- sdflow:step1-broad-review v1 mode="simulated" -->

## 概要

新骨架对第一轮 Q1（锚无闭环）/Q2（误勾）**有真实结构性解决**（对抗1、哲学镜均认可"归属镜像/盘面即状态"核心站得住），但第二轮 7 镜收敛到**更深的方向性问题**——两个致命 + 一串高危 + 一个 ROI 根因，且其中一条由**官方 CLI 源码证实**（非推理）：

- **producer 机械生成链第一环（scaffold↔opsx:ff）用源码证实是结构性冲突**，非"细节待补"。
- **阶段 enum 公式在起点就不可机械实现**（deferred 无信号）。
- **scaffold 双向预建被多镜判为过度工程**，且未真正消除"靠人写对"（只挪位置）。
- **defer 常见模式下 roadmap 复选框永停 `[ ]`——原痛点换皮重现**。
- **ROI 根本失衡**：投入两轮 grill + 两轮 7 镜 spec-review + scaffold/lint/迁移，对应消除的是"一次几分钟手工勾框"，全仓仅 2 roadmap、频率个位数。

**这轮结论：不建议进设计门批准原全量设计，核心指向大幅简化（scaffold 存废是关键拍板）。**

---

## 决策登记区

```
┌──────────────────────────────────────────────────────────────────┐
│ [需拍板] Q1  scaffold 双向预建：存废 / 改 done create-or-update（致命根因·多镜） │
│ [需拍板] Q2  阶段 enum "deferred" 公式循环、缺机器信号（致命）        │
│ [需拍板] Q3  defer 重现原痛点 + scope/ROI 最小可行版（高·根因）       │
│ [自动决策] D1-D9  修法已定，设计门默认接受（详见下）                  │
│ [已裁掉]  无（findings 均成立；对抗1 纠正主 session 一处 prompt 框架，记录）│
└──────────────────────────────────────────────────────────────────┘
```

### [需拍板] Q1 — scaffold 双向预建：存废 / 改 done create-or-update（致命根因）

**命中镜**：对抗1[致命·源码] + outside-voice[高] + 广审[中·CEO] + 对抗3[高] + 哲学[Minor]（5 镜共识）。

**问题（三条收敛到一个根因——scaffold 双向预建）**：
- **C1 [致命·源码证实]**：`@fission-ai/openspec` CLI 的 `detectCompleted`（`state.js:11-30`）判 artifact "done" **只看文件存在、不看内容**；`tasks` 是依赖链末端、`apply` 门槛=tasks done。**scaffold 抢先写 tasks.md 空骨架 → opsx:ff 判 tasks/proposal 已完成 → 静默跳过 proposal/specs/design 生成**（产出链短路）。proposal 也在碰撞半径（scaffold 写引用 → proposal 判 done → specs/design 基于残缺 proposal）。这是 producer 链第一环的结构冲突，**用官方源码证伪、非推测**。
- **H1**：scaffold 双向预建 roadmap 复选框的**必要性未论证**——Success Metrics 无一条要求"change 进行中 roadmap 可见在途"。且 scaffold 未真正消除"靠人写对"：`--subtasks` 参数仍 100% 靠人敲，选错（4.D.1 打成 4.D.2）lint 不查、done 按错范围静默镜像——**与被否决的 adr/0013 本质同构，只挪位置**（forget-anchor → wrong-param）。
- **H2**：scaffold 预建单向不可逆 → change 废弃不走 done 留"看似在途实已死"孤儿复选框；两 change 认领同号 → 谁先 done 谁生效、另一个静默吞。
- **H5**：scaffold 起手就写 roadmap.md 概览表（新开手写 pipe-table 写路径）——**与本 roadmap 自己 P6 立项要治的 markdown 表 `｜` 腐蚀直接矛盾**，且损坏的是跨阶段规划真相源。

**推荐 = 去掉 scaffold 双向预建，改 done 时 create-or-update**（outside-voice①源码级论证）：
- 归属信息只写进 change tasks 的归属锚（`subtasks`），**roadmap 复选框推迟到 done 镜像时按锚 create-or-update**（而非 scaffold 预建 + done update-only）。
- **一举消除**：C1（scaffold 不写 tasks/proposal → 不触发 opsx:ff 短路）+ H1（不预建）+ H2（roadmap 复选框永远 done 单点生成、无孤儿）+ H5（少一次早写）+ 双向原子性。
- 三镜后果：**系统镜**——roadmap 复选框单点生成，无第二真相源/无预建孤儿；**用户镜**——起 change 摩擦更小（不跑 scaffold）；**开发循环镜**——scope 砍一个 producer 能力（scaffold 双向）。**主次**：主=消除第一环结构冲突（C1 致命）；次=损失"在途可见性"（Success Metrics 本就不要求，可接受）。
- 残留：关联仍靠 lint（tasks 用 roadmap 编号无 name 锚 → 拦）+ 归属锚（人写或 opsx:ff 后轻量补，**只碰 change tasks/锚、不碰 roadmap**）。

### [需拍板] Q2 — 阶段 enum "deferred" 公式循环、缺机器信号（致命）

**命中镜**：对抗2[致命] + 哲学[Major]（2 镜共识）。

**问题**：聚合公式 `全非deferred完成=delivered / 显式放弃=deferred`（design.md:81）**自身循环**——delivered 要先知道哪些 deferred，但 deferred 是输出；且**全文档无处定义"显式放弃"如何从二值复选框 `[ ]`/`[x]` 机械读出**（`[ ]` 未做 vs 已弃渲染相同）。真实数据：P4 的 4.A/4.D.3 是◐排后（`[ ]`），P4 全 ★ 项交付后 enum **永卡 in-progress、到不了 delivered**。spec 说"MUST NOT 靠模型判断"，但 deferred 判据源缺失 → 要么退化模型判断（违 MUST）、要么死枚举值。

**推荐**：① 补**行级机器信号**（子任务行加 `<!-- status: deferred -->` 锚/专用 checkbox 变体，纳入生成侧结构化契约、与 enum 值集同单一源）；或 ② **砍 deferred enum**（只 planned/in-progress/delivered，"排后/放弃"靠叙述层散文，不进机械 enum）。推荐 ②（更简，deferred 本就是规划判断、不该硬塞机械聚合），系统镜=enum 只承载可机械判的三态，判断态留叙述层。

### [需拍板] Q3 — defer 重现原痛点 + scope/ROI 最小可行版（高·根因）

**命中镜**：对抗3[高] + 对抗2[互证] + outside-voice[中·ROI] + 广审[高·Q3未落地]。

**问题**：
- **H3 defer 回痛点**：组内任何 `[ ]` → roadmap 复选框永不勾（刚性）。"核心做了 + 测试 defer 进 todolist、verify PASS 正常归档"这种**常见模式**下，roadmap 永停 `[ ]`、无补触发路径（回写只 archive-time 一次）= "永久假过期"——**正是本 change 想消灭的手动回填痛点换皮重现**。
- **R1 ROI 失衡**：触发仅"一次几分钟手工"，投入两轮 grill + 两轮 7 镜 + scaffold/lint/迁移/dogfood；2 roadmap、频率个位数。上一轮 Q3 推荐的"最小可行版"未落地（design 全量、三项并 P0、未记裁决）。

**推荐 = 最小可行版 + defer 语义修**：
- **scope 砍到最小可行**：`lint（漏锚 fail-closed）+ done create-or-update 盘面镜像`（Q1 推荐）两件核心先上，**砍掉 scaffold 双向 + 生成侧模板预建 + 暂缓旧 2 roadmap 迁移**（待真实第 3 个 roadmap 或频率上升再做）。
- **defer 语义**：组内 defer → 该子任务复选框走"部分勾 + 降级标注"（区分"整组未做"vs"核心做了尾巴 defer"），或以 change verify 完成 + tasks 完成态综合判——避免"永久假过期"。
- 主次：主=先验证价值再投入（ROI）；次=在途可见性/生成侧结构化暂缓（可增量补）。

### [自动决策]（设计门默认接受，可覆盖）

- **D1 补回 round-1 丢失的 fail-closed 分支**〔哲学 Major，点驱动修补遗漏面〕：spec-review-1 D1"有 name 锚但解析不到 roadmap 目录 → fail-closed 留人工、非静默"，第二轮重写 D-7 时**丢了**——补回 + spec Scenario + 测试（反静默口子回归）。
- **D2 组边界 fence-aware 解析**〔对抗3〕：归属组完成态扫描 MUST fence-aware（组内 fenced code block 含 `- [ ] 示例` 会误判，MEMORY `gate-substring-detection-dogfood` 同款坑）；定义组结束边界。
- **D3 迁移异质分治**〔对抗2/广审/接地〕：`workflow-cost-optimization` **无复选框/无编号/纯散文**——"同上迁移"是假动作，须单独设计（甚至不迁）；mlh 自身 `1.A.x`=实现步 vs `4.D.x`=change 级，**编号粒度已不统一**，迁移前先做粒度审计。
- **D4 概览表写路径硬化**〔对抗2〕：MUST 复用 `sdflow-issues` 已硬化的表原语（`_reject_cell_unsafe`/表解析）或 fail-closed，**MUST NOT 新开裸手写 pipe-table 写路径**（重蹈 P6 治的腐蚀）。
- **D5 归属锚完整性校验**〔对抗3/outside-voice〕：lint MUST 校验锚 `subtasks` **覆盖 tasks 全部 `## N.X.Y` 组**（非只存在性）——防"存在于 tasks 但游离锚外的组静默漏镜像"。
- **D6 空归属组断言**〔广审〕：镜像脚本对归属组 MUST 断言 ≥1 复选框才判"全 `[x]`"（防 vacuous-truth 误勾）。
- **D7 里程碑句阈值机械化**〔哲学〕：触发 = 本轮聚合 enum ≠ task-log 最近锚记录的 enum（机械对比），只把"写什么内容"留模型（防"要不要写"也变判断）。
- **D8 spec/单一源补全**〔对抗1/哲学〕：spec 补"子任务号不存在 fail-closed" Scenario；锚格式/编号正则纳入同一机读契约（不止 enum 值集）；task-log 插入点锚定（防误落 Review 处置区，`task-log.md:33` vs `:55` 双相似 marker）；辅助任务归属从 Open Question 升 Decision。
- **D9 措辞精确**〔哲学/outside-voice〕："不靠人写对"改"不靠人写对锚的**语法/落点**"——**选哪些子任务是规划判断、不可也不该机械化**（同选哪个阶段动手），别让"机械生成"盖过这条边界。

### [对抗裁决细化] outside-voice/对抗1 纠正主 session 一处框架

主 session 派对抗镜时 prompt 用了"scaffold 换汤不换药"框架——对抗1 精确纠正：本轮 tasks 2.1"子任务号不存在 fail-closed"是从"零校验→有校验"的**实质改进**，非同构复现；残余是"**锚内容对不对（选对子任务号）**"未兜底，这是不可机械化的规划判断（哲学镜 D9 同源）。记录以正视听，非裁掉任何 finding。

---

## 各镜 findings 汇总

| 簇 | finding | 命中镜 | sev | 裁决 |
|---|---|---|---|---|
| **C1** | scaffold 抢写 tasks/proposal → opsx:ff 文件存在性判 done 短路产出链（**CLI 源码证实**） | 对抗1(独)/广审 | 致 | Q1 |
| **C2** | 阶段 enum deferred 公式循环 + 无机器信号 | 对抗2/哲学 | 致 | Q2 |
| **H1** | scaffold 双向预建必要性未论证 + 没消除"靠人写对"（只挪位置） | outside-voice/广审/对抗1/哲学 | 高 | Q1 |
| **H2** | 归属锚存在性非完整性门禁 + 孤儿认领/作废 change 无回收 | 对抗3/outside-voice | 高 | Q1/D5 |
| **H3** | defer 常见模式 roadmap 永停[ ]=原痛点换皮重现 | 对抗3/对抗2 | 高 | Q3 |
| **H4** | 旧 2 roadmap 异质"同上迁移"假动作 + mlh 自身编号粒度已不统一 | 对抗2/广审/接地 | 高 | D3 |
| **H5** | 概览表新开手写 pipe-table 写路径 vs 本 roadmap P6 治腐蚀矛盾 | 对抗2 | 高 | D4/Q1 |
| **H6** | round-1 fail-closed 分支第二轮重写丢失（反静默回归） | 哲学(独) | 高 | D1 |
| **R1** | ROI 失衡：过度工程 vs 一次几分钟手工 | outside-voice/广审 | 高 | Q3 |
| **M1-M10** | 单子任务功能组vs归属标签/组边界fence/空组vacuous/lint假阳/多分支冲突/scaffold绕review/里程碑阈值/辅助任务归属/task-log marker/spec缺Scenario | 对抗×3/广审/domain/ov | 中 | D2/D5/D6/D7/D8 |
| **L1-L3** | 单一源锚正则/复选框antidrift/多roadmap关联 | 哲学/对抗2 | 低 | D8 |
| **接地** | 6 事实一致；2 缺口=已知迁移映射（就绪度≠enum、wco无状态列） | grounding | — | 并入 D3 |

---

## 度量锚（lens-metric v1）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="—" findings="14" 采纳="14" 裁掉="0" defer="0" 独立="9" sev="致2/高5/中6/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="1" sev="致1/高3/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" runner="claude" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="4" sev="致1/高2/中1/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="claude-fallback" site="design-voice" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="1" sev="致0/高3/中2/低0" -->

<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="claude-fallback" reason_code="exec-error" findings="5" truncated="false" -->

<!-- sdflow:hr-tg v1 hit="none" evidence="命中 TG-12/14/18/19/20/22/23 均不在 HR-TG 子集；文档回写编排、误写可 git 回退，非运行期爆炸/数据损坏难回退类" -->

> **codex 降级留痕**：本轮 codex outside-voice 命中 usage limit（exit 0 但输出空 + stderr 报错）→ 反静默守卫回落自跑 claude-fallback（runner="claude-fallback"、reason_code="exec-error"）；跨家族盲区本轮缺失、以同家族 fresh-context 补偿。
> **残余信任边界**：findings 分类/roster 完备/JSON 誊写仍是主 session 信任边界；`采纳/裁掉` 为拍板前临时值，拍板时最终化（SR-M）。

---

## 收敛口

**不建议进设计 HARD-GATE 批准原全量设计。** 第二轮 7 镜抓 **2 致命 + 7 高**（对抗镜独立贡献 9，含一条 CLI 源码级致命），且核心是**方向性问题非收尾缺口**：

1. **先决 Q1**（scaffold 存废）——推荐**去掉 scaffold 双向预建、改 done create-or-update**，一举消除 C1（源码证实的第一环结构冲突）+ H1/H2/H5。这是最大简化杠杆。
2. **决 Q2**（enum deferred）——推荐砍 deferred enum、留三态机械值。
3. **决 Q3**（defer 回痛点 + ROI）——推荐**最小可行版**（lint + done create-or-update 镜像两件核心先上，砍 scaffold/生成侧预建/暂缓迁移），defer 语义修避免"永久假过期"。
4. Q1-Q3 定向后 D1-D9 作 amendment 落。

**元信号（诚实呈现）**：本 change 经**两轮 grill + 两轮 spec-review**，每轮都揭穿当前骨架的一个根本问题（起手锚无闭环 → 编号统一粒度失配 → 归属镜像 scaffold 结构冲突 + enum 不可实现 + defer 回痛点）。叠加 R1 的 ROI 失衡——**这强烈提示：要么大幅简化到最小可行版（lint + done 镜像），要么重新评估"这个自动化是否值得此投入"**。冷层反复 load-bearing 地拦下过度工程，本身是设计该收敛的信号。

<!-- 设计门拍板后：主 session 在此文件头部 prepend frontmatter ship-gate.design_approved=true（拍板前不写；本轮明确不建议直接批准） -->
