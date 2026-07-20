---
ship-gate:
  design_approved: true
---

# spec-review-report — fix-design-gate-freshness-proxy

2026-07-20 · 主 session 强档裁决 · host=claude

**设计门已拍板批准，2026-07-20。** 拍板内容：Q1 = 继续方案 A（内容等值判据）；`design.md` 上「零设计信息量」改动（注释 / 错别字 / 格式化 / 净零改动）**不做机械豁免**，维持 `checkpoint(impl-review)` 显式声明通道（Non-Goals 逐字不变）。Q2（DX 相位 codex-only）、Q3（对抗镜实跑 1 个）按推荐接受。方案 B（批准快照摘要）登记为目标架构，另开 change，前置未解项 = 尾流修订的重新盖章语义。

## 一句话结论

**问题真实、值得修；方案在本轮被换掉一次、又被收紧五处。建议进设计 HARD-GATE，但先拍 Q1（路线）。**

## Step 1 · autoplan 广审

<!-- sdflow:step1-broad-review v1 mode="native" -->

原生执行，产物落 `gstack-review.md`（含相位共识表、降级矩阵、跨相位主题、自动决策 AD-1~AD-5）。
**诚实登记**：DX 相位为 `codex-only`（未派 Claude subagent）；codex Eng 的第 1–4 条因编排失误被 `tail -60` 截断且未恢复，属本轮已知缺口，**非「无发现」**。

## Step 2 · 镜规划与 fan-out

<!-- sdflow:hr-tg v1 hit="none" declared="TG-12,TG-18,TG-19,TG-21,TG-22,TG-23" -->

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="adversarial,grounding" -->

**无领域镜**（防重叠 1.4：autoplan 已含 eng 视角，本 skill 不重复）。**对抗镜 1 个**（普通风险档位建议 2 个，本轮实跑 1 个 + codex 规范歧义专项一次，**如实记为 1**，见「已知缺口」）。接地镜 1 个。

<!-- sdflow:declared-sites v1 declared="design-voice" -->

<!-- sdflow:outside-voice v1 site="design-voice" guard="section-not-found" host="claude" runner="codex" reason_code="ok" findings="4" truncated="false" -->

reuse-guard 判 `section-not-found` → 按协议回落自跑。首次 dispatch 因 `SDFLOW_VOICE_RUNNER` 未跨 shell 存活而 rc=1，失败 run 目录按不可变纪律保留，换新 run-id 重跑成功（**本 session 第三次撞同一坑，已登记 T184**）。

## 决策登记区

### ✅ 已拍板（2026-07-20 设计门）

**Q1 → 继续 A。** 拍板依据：B 的「重新盖章」语义未解，落地即把「误报可重跑」换成「卡死无出口」；A 的历史轴表面本轮一次照全（可穷举，非无界语法面）；A 的内容轴三件（fence 感知 / `CHECKBOX_RE` 锚定 / 保真读取）是 B 将来也要写的，先做不白做。**注释豁免维持显式声明通道**——`design.md` 上零信息量改动照判失鲜是**已知且接受**的永久代价。**Q2 → 接受。Q3 → 接受。**

**〔SR-M〕计数说明**：Q1–Q3 是路线/流程拍板项，不在 findings 合并池内；本次拍板未翻改任何 finding 的采纳/裁掉去向 ⇒ 下方 lens-metric 四行**逐字维持 Step3 值**，非漏执行最终化。

### 🔴 需拍板（原文留档）

**Q1 — 路线：继续方案 A（内容判据），还是改走方案 B（批准快照 digest）？**

方案 A 经本轮收紧后，需要 9 件机械配套：sha 提取（动 BR-6 分帧格式）· 保真字节读取 + rc 显式判 · git raw 状态位/mode 资格 · merge 多 parent · fence 感知 · `CHECKBOX_RE` 锚定 · 位置对齐禁 LCS · 前后版双向缺失 · BR-7 优先级真值表。

方案 B（codex CEO 提的「目标架构」）：拍板时把四件套的规范化摘要写进 report frontmatter，gate 重算比对。**上述 9 件里的 4 件当场蒸发**（不走历史 ⇒ 无 sha 提取、无 merge parent、无 rename/mode、无 BR-6 交互）。

**我的推荐：继续 A。** 三条依据：

1. **B 要改的是拍板契约本身**（frontmatter schema + 谁在何时重新盖章），而本 change 的目的就是修这道门——在修门的 change 里同时改门的契约，是自举困局。
2. **A 的表面已被穷尽，不是发散。** 关键区分：第 1 轮 grill 评的是旧方案、第 2 轮 CEO 直接换了方案，**本轮是方案 A 的首轮深审**——9 条一次性出齐，是「一次照全」，不是「每轮补一个」。基准 5 的警号针对的是**无界**语法面；这里 git raw 状态码 × markdown 勾选框词法**都可穷举**，且仓内已有 5 个所需原语（`CHECKBOX_RE` / fence tracking / `run_git_rc` / `TAG_RE` / 分帧）。
3. **B 有一处未解**：合法尾流修订（impl-review 改 design.md）后 digest 必然改变，需要「被监管方重新盖章」——信任层级不比现状好。

**代价**：A 的实现量显著大于原估（tasks 从 5 组涨到 5 组+13 条新用例）。**备选**：B 作为**目标架构登记**，另开 change。

**Q2 — DX 相位 `codex-only`（未派 Claude subagent）是否接受？** 推荐接受（codex 已出 3 条具体发现，边际收益低）。**Q3 — 对抗镜实跑 1 个（建议 2 个）是否接受？** 推荐接受（本轮 findings 已达 21 条、收敛明显）。

### 自动决策

| # | 决策 | 依据 |
|---|---|---|
| D1 | 方案 A「监视集角色分流」→ 换为内容等值判据 | 两路 CEO **独立**证伪：豁免面远超已证范围、钥匙由正常生命周期可得（非蓄意伪造）、工作树可翻转历史判定 |
| D2 | 「非 BREAKING」→ 改判为门禁放松 | 对门而言扩大准入面即安全语义变更，原论证方向反了 |
| D3 | A1 → A1′（写入方 = agent 自由行为，非 SKILL 契约） | 接地镜核实 13 项代码事实全属实：`sdflow-implement` 只读、superpowers SDD 无 `tasks.md` |
| D4 | 归一化须 fence-aware + `CHECKBOX_RE` 锚定 | 三源收敛；且仓内已有两处同类护栏（`_line_scoped_hits` / `_parse_plan`），原 Compliance 条款字面把已知解法堵死 |
| D5 | 比较须位置对齐，禁 LCS | 双源收敛；LCS 下纯重排的删除行与插入行逐字节相同 |
| D6 | 读取须保真 + `run_git_rc` 显式判 rc | 双侧失败得 `""=="" ` ⇒ 判等值 ⇒ **放行真实设计改动**（唯一能让 gate 完全失效的路径） |
| D7 | 「只触及 tasks.md」限定为 **design 域监视集内**的路径集 | 按整 commit 求值 ⇒ 豁免永不触发（checkpoint 走 `add -A`）⇒ P0 白做，且全部用例仍绿 |
| D8 | 默认处置指引**移除** `checkpoint(impl-review)` | 它对撞门者**无效**（逐提交求值，后补不追溯赦免），且把越权口产品化 |
| D9 | 补 BR-7 优先级真值表 | 内容豁免独立于 subject，与 BR-7「变体照判失鲜」无唯一解 |
| D10 | 不做注释/措辞的内容感知豁免（维持 Non-Goal） | 无界语义面，补丁循环不收敛（基准 5） |

### 已裁掉（反静默压制 · 连理由留档）

| # | 原始发现 | 裁掉理由 |
|---|---|---|
| X1 | 多提交串联绕过豁免 | 对抗镜自证否：逐提交独立求值，任一帧不满足即整体失鲜，无「先垫后洗」空间 |
| X2 | 同提交夹带域外源码绕过 | 域外路径本就不在 design 域循环内，是分域机制既有语义，非本 change 引入 |
| X3 | 夹带 change 目录下的新文件（如 `notes.md`） | 会让「监视集内路径集 == {tasks.md}」判假 → 落回失鲜。安全。**但表述缺口已采纳**（D7 已消歧） |

## Findings（21 条采纳，按严重度）

**致命 5**：① `run_git` 不可用于内容比较（`text=True`/`.strip()`/rc 折叠，四条各自可造假等值）② rename/mode/类型变更无资格规则（chmod、regular↔symlink 令 blob 相同）③ 打包提交下 P0 白做且测试全绿 ④ 四件套自相矛盾（4 处引用已否决方案 + 1 处悬空 Scenario 交叉引用）⑤ 原方案豁免面远超已证范围。

**高 7**：merge 前版未定义（BR-6 禁 `--no-merges`、帧格式无 sha）· BR-7 判定冲突无唯一解 · fence/表格/行内/散文盲区 · 行重排（对齐算法未钉死）· 测试无判别力 · `checkpoint` 指引无效且产品化越权口 · A1 举证不实。

**中 7 / 低 2**：`is_stale` 需结构化返回且 code 域 `freshness` 取值须锁定 · 后版缺失未处理 · 归一化未锚定 · Non-Goals 自相矛盾 · Why 段仍基于证伪前提 · 升级路径三态未分（Unix symlink / Windows copy / 宿主缓存）· 非 BREAKING 判反 · 4.4 判别力弱（字典序致 `design.md` 先命中）· 4.7 变异覆盖不全。

## 度量锚

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="6" 采纳="3" 裁掉="3" defer="0" 独立="0" sev="致0/高2/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="19" 采纳="19" 裁掉="0" defer="0" 独立="13" sev="致5/高7/中5/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致1/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="2" sev="致2/高1/中3/低0" -->

**信任边界声明**：数值一致性（`findings`/`采纳`/`独立` 是否与合并池实收数吻合）是主 session 信任边界、非机械可验；emitter 只保证给定输入的确定性归约。分类正确性与 roster 完备性同理。

## 元观察

**本轮 21 条里有 4 条是我这轮 amendment 自己造的**——部分改写留下的自相矛盾（Non-Goals 与 ADR-1 打架、Why 段与假设表打架、两处「只触及」口径打架、悬空 Scenario 引用）。全部由**后续镜**抓出，无一由我自查发现。

这印证一条已知模式：**返工在接缝处引入新洞**。方法论上的含义是——大改方案后，不能只评审「新方案对不对」，还必须扫一遍「旧方案的残留引用」。本轮是靠镜多兜住的，不是靠流程兜住的。

## 收敛口

**建议进设计 HARD-GATE。** 拍板项：Q1（路线，推荐继续 A）· Q2（DX codex-only，推荐接受）· Q3（对抗镜 1 个，推荐接受）。
