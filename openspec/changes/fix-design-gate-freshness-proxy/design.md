## Context

`ship_gate.py` 的设计门用「拍板结论是否仍新鲜」保护一件事：**人的批准不被其后的设计改动无声作废**。它防的失效是——批准了 design v1，之后 design 改成 v2，实现照 v2 出货而 v2 从未被批准。

判据实现在 `is_stale(scope="design")`：取 `spec-review-report.md` 的末次提交 sha，扫 `sha..HEAD` 的每个提交帧，若 subject 非 `checkpoint(impl-review)` 且触及 `DESIGN_WATCHED_NAMES`（`proposal.md` / `design.md` / `tasks.md`）或 `specs/`，即判失鲜。

**路径是「设计内容变了」的代理信号，而这个代理是过近似。** 实现管线每完成一个任务就更新 `tasks.md` 的完成度复选框，该动作零设计内容，却与真实设计改动共用同一条路径判据。

已核实的两条事实（决定了修法形状）：

- **`tasks.md` 的复选框对 gate 是零信息量**：完成判据只读 `superpowers-plan.md` 的分段复选框与 `checkpoint(<change>:task<N>-<slug>)` 标签（`_parse_plan` + 完成判据窗口 `[plan 首次提交 sha, HEAD]`）。
- **`superpowers-plan.md` 落盘即完成信号权威转移点**：该文件的首次提交 sha 正是完成判据窗口的起点。

## Goals / Non-Goals

**Goals:**

- 消除「每完成一个任务撞一次 `REFUSE_START`」——恢复 adr/0004「过设计门后无人类门」的红线语义。
- 修法不依赖任何第三方实现 skill 的配合（superpowers / matt 均非本仓代码）。
- 判据保持**纯机械**：可确定性判定，不引入内容读取与解析。
- `proposal.md` / `design.md` / `specs/` 的保护强度**逐字不减**。

**Non-Goals:**

- **注释 / 措辞类改动的内容感知豁免。** `design.md` / `specs/` 上「澄清性注释」与「设计变更」之间无确定性信号——注释本身即设计沟通，implementer 读到即照做。做内容感知等于在无界语义面上开补丁循环（基准 5）。该面的既有正解是 `checkpoint(impl-review)` subject 声明式豁免。
- **勾选框级的内容 diff 豁免**（见 ADR-1 被否方案 B）。
- 改动 `code` 域失鲜判据（本 change 只动 `design` 域）。
- 为已归档 change 重放 gate。

## Decisions

### 判定流（目标态）

```
      提交 touches openspec/changes/{change}/<sub>
                     │
      subject == checkpoint(impl-review)[:…] ? ──yes──► 豁免（既有，不动）
                     │ no
                     ▼
         <sub> ∈ {proposal.md, design.md} 或 specs/* ? ──yes──► STALE
                     │ no
                     ▼
              <sub> == tasks.md ?
                     │ yes
                     ▼
        superpowers-plan.md 存在？
          ├── 是 ──► 不失鲜（权威已转移，tasks.md 出监视集）   ◄── 本 change 新增
          └── 否 ──► STALE（tasks.md 仍是唯一任务权威）
```

### ADR-1：监视集按**角色**分流，而非按**内容**豁免〔BASE-12〕

**决定**：`tasks.md` 的 design 域监视集成员资格由 `superpowers-plan.md` 的存在性决定。

**理由**：`tasks.md` 在 plan 落盘后不再被任何消费方当作权威——完成信号在 plan + checkpoint 标签，设计决策在 `design.md`（DOC-1 / BASE-12）。它此时是一份派生的、无人消费的清单。**继续监视它是一个过时的角色判断，修正它不是放松门禁。**

被否方案：

| 方案 | 否决理由 |
|---|---|
| **B. 勾选框内容 diff 豁免**（比对前后 blob，仅 `[ ]`↔`[x]` 差异则豁免） | 语义正确且有界（行级等值比较，非解析器），但**仍需读取内容**，且只解决勾选框这一个点——同一过近似的其他表现面（纯格式化、错别字）会逐个回来要补丁。角色分流一次覆盖 `tasks.md` 的**全部**改动形态，且代码更少。 |
| **C. 仅补 dispatch 契约禁令**（告知 implementer 不要碰 `tasks.md`） | 需要控制我们不拥有的 agent——superpowers 与 matt 的实现循环均非本仓代码。作为唯一修法结构上不成立，降为 P2 辅助（见 ADR-3）。 |
| **D. 扩大 subject 豁免**（把实现期 checkpoint subject 一并豁免） | 与 BR-7 的收紧方向相反。subject 由被监管方自己书写，扩大它等于把门的判据交给被判者，是真正的开洞。 |

**求值时点**〔grill-amendment〕：plan 存在性按 **gate 运行当下**求值，**不逐帧回溯**。由此存在一条通道——设计门后先改 `tasks.md`（真设计内容）撞 `REFUSE_START`，再手写提交一个 `superpowers-plan.md`，该次改动即追溯性获豁免。**该通道归入既有的「可伪造豁免钥匙」桶**：与「伪造 `checkpoint(impl-review)` subject 绕过豁免」同权级（显式越权、git 留痕可审计），MUST 在脚本头注释「已知不覆盖」中声明。**不为它引入逐帧祖先判定**——收益是挡住一个需要蓄意手造 plan 的路径，代价是判据复杂度与一处新的口径漂移面，不划算。

**代价（显式接受）**：plan 存在后，若有人**真的**把设计决策写进 `tasks.md`，该改动不再触发失鲜。接受依据：`design.md` 与 `specs/` 仍全程受监视，而工作流契约本就规定设计决策落 `design.md`（DOC-1）；`tasks.md` 按定义是任务清单。此为**目标态契约下的合法收窄**，非「现状里很少见」式的松绑。

### ADR-2：失鲜 reason 携带触发点，但不改判据

**决定**：`REFUSE_START` 的 design 失鲜 reason 输出触发提交与文件，并给两条分支处置提示。

**理由**：撞门者（人或 agent）当前只能看到「结论陈旧」，无从判断该重跑设计门还是该改自己的行为。指引出现的时机正好是它被需要的那一刻——这是把规则送到会读它的地方，而不是写在事后才会被读到的文档里。

**边界**：纯诊断，不参与判定，不改退出码。

### ADR-3：dispatch 契约补信号权威表，且明确其防线定位

**决定**：`sdflow-implement` 的 implementer / fix dispatch prompt 携带信号权威表（正面陈述归属，非禁令清单）。

**理由**：正面陈述挡的是整个范畴，禁令只挡列举到的越界形态。

**定位声明（防后人误读）**：本项**不是**失鲜问题的防线——机械防线在 ADR-1。它解决的是另一件事：本仓自有管线不应写脏设计工件。两者各自独立成立，**MUST NOT** 因 ADR-1 已兜住失鲜后果而认为本项可省。

## Risks / Trade-offs

| 风险 | 评估 | 处置 |
|---|---|---|
| 判据分流后，既有 `checkpoint(impl-review)` 豁免路径回归 | 两条判据在同一函数内相邻，改动易误伤 | 既有豁免用例（含 BR-7 的 `checkpoint(impl-review)evil` 负例）MUST 全部保持绿，作为回归锚 |
| plan 存在性判定的路径口径与完成判据不一致 | 若两处对「plan 在哪」口径不同，会出现 gate 自相矛盾 | 存在性判定 MUST 复用完成判据侧同一 plan 路径构造，MUST NOT 另写一份路径拼接 |
| 消费仓未升级即认为已修复 | 分发经 `setup.sh` 软链，需 `/sdflow-upgrade` | hand-off 显著声明生效条件 |
| 「设计决策写进 tasks.md」的漏网面 | 见 ADR-1 代价，已显式接受 | 登记为已知取舍，不再另设补丁 |

## Compliance

- 判据 MUST 为存在性检查，MUST NOT 读取或 diff 任何文件内容。
- `proposal.md` / `design.md` / `specs/` 的失鲜口径 MUST 逐字不变。
- 既有 `checkpoint(impl-review)` 精确式豁免（BR-7）MUST 不受本 change 影响。
- 新增判据分支 MUST 有变异验证：删掉该分支，对应用例 MUST 转红。
