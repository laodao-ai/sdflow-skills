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
- **勾选框以外的任何内容变化的豁免**——措辞、格式化、错别字、缩进一律照判失鲜〔spec-review-amendment：原文此处误把已被 ADR-1 采纳的方案列为 Non-Goal，系部分改写留下的自相矛盾〕。
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
  本帧落在 design 域监视集内的路径集 == {tasks.md} ? ──no──► STALE
        （🔴 不是整个 commit 的文件列表——checkpoint 走 add -A，
          真实完成提交必然打包源码；按整 commit 求值 ⇒ 豁免永不触发）
                     │ yes
                     ▼
   前后两版差异行，勾选框标记归一化后逐行等值？          ◄── 本 change 新增
          ├── 是 ──► 不失鲜（纯完成度更新，已证零信息量）
          └── 否 ──► STALE（任何非勾选框改动照判）
```

### ADR-1：只豁免**勾选框状态翻转**这一个已证零信息量的改动形态〔BASE-12〕

**决定**：design 域失鲜判定中，一个提交若**只**触及 `tasks.md`，且该文件前后两版的**全部差异行**在把 `[ ]` / `[x]` / `[X]` 归一化后**逐行等值**，则不判失鲜；其余一切情形照判失鲜。监视集**保持固定四件套不变**。

**理由**：勾选框状态是**唯一被证明对 gate 零信息量**的改动形态（A2：完成判据只读 plan 分段复选框 + checkpoint 标签）。豁免面精确等于已证零信息量的那个集合——**不多一寸**。

判据有界：行级等值比较，非解析器，基准 5 不咬（穷举得完：一行要么只差勾选框标记，要么不是）。且**不可伪造**——判据取自内容本身，不取自被监管方书写的任何声明（subject / 文件存在性皆属后者）。

被否方案：

| 方案 | 否决理由 |
|---|---|
| **A. 监视集按角色分流**（`superpowers-plan.md` 存在 ⇒ `tasks.md` 退出监视集） | **两个 CEO 独立镜共同证伪**〔spec-review-amendment〕。① **豁免面远超已证范围**：A2 只证明「gate 的完成判据不读 `tasks.md`」，不证明「任务范围 / 顺序 / 验收项 / 依赖已失去权威」；角色分流把前者偷换成后者，令 plan 落盘后**追加整个 `### Task N+1:` 段**（实打实的范围扩大）也静默放行。② **钥匙可由正常生命周期获得，非蓄意伪造**：design v1 批准 → plan v1 落盘 → design 改 v2 重审 → **plan v1 仍在** ⇒ 豁免持续有效。grill 阶段把它归入「可伪造钥匙桶」的判断**基于一个错误前提**（以为需要手造 plan），据此不成立。③ **工作树即可翻转历史判定**：存在性若用 `Path.is_file()`，一个未提交甚至 untracked 的 plan 就能让**已提交**的 `tasks.md` 改动追溯获豁免——与脚本「新鲜度只看 committed 盘面」的声明直接冲突。 |
| **C. 仅补 dispatch 契约禁令** | 需要控制我们不拥有的 agent。且经核实 `sdflow-implement` 与 superpowers SDD **均不写** `tasks.md`（见 proposal A1 修订），该契约警告的是一个它们本就不犯的错。作为主修法不成立，降为辅助（ADR-3）。 |
| **D. 扩大 subject 豁免**（把实现期 checkpoint subject 一并豁免） | subject 由被监管方自己书写，扩大它等于把门的判据交给被判者。与 BR-7 的收紧方向相反。 |
| **E. 复用 `TAG_RE`**（subject 匹配 `checkpoint(<change>:task<N>-` ∧ 仅触及 `tasks.md` ⇒ 豁免）〔spec-review-amendment，CEO 镜提出的第 5 案〕 | 比 A 窄得多、零新增机制，是本表里最接近采纳线的备选。**仍否**：判据落在 subject 上 ⇒ 与 D 同属「钥匙由被判者书写」，而本方案的内容判据不依赖任何声明。**代价对比**：E 需要写入方正确打标签才生效（agent 自由行为下的裸 commit 不受保护，问题复发）；本方案对**任何** subject 的纯勾选提交都生效。 |

**求值口径**：判据只比对 `tasks.md` 在该提交前后的两版内容，**逐提交独立求值**，不依赖任何跨提交状态、不依赖工作树。**MUST NOT** 做语义 diff、**MUST NOT** 扩展到勾选框以外的任何差异形态（措辞、格式化、错别字一律照判失鲜——见 Non-Goals）。

**代价（显式接受）**：一个提交若在勾选框之外还改了 `tasks.md` 的哪怕一个字，即照判失鲜。这会让「顺手改了个错别字 + 勾了框」的提交仍撞门。**接受**：这是 fail-closed 方向的误报，代价是重跑一次设计门，而非放行未批准内容；且诊断指引（ADR-2）会直接告诉撞门者原因。

### ADR-2：失鲜 reason 携带**结构化**触发点，默认处置**只有一条**

**决定**：`REFUSE_START` 的 design 失鲜 reason 输出结构化触发点——短 sha、subject、路径、**分类原因**（混合路径 / 非勾选框变化 / 前后版缺失 / 状态不合格），并在 JSON 同步这些字段（供 agent 直接取用，免二次解析 prose）。**默认处置只推荐「重跑设计门」一条。**

**MUST NOT 把 `checkpoint(impl-review)` 写进默认处置指引**〔spec-review-amendment〕。两个理由，第二个是决定性的：

1. 它是一个**显式越权口**——该 subject 让任意四件套语义改动不经二次批准随档 ship（`ship_gate.py` 头注释已声明为「已知不覆盖」）。把逃生口写进常规处置建议，会把例外变成默认工作流。
2. 🔴 **它对撞门者根本无效**——豁免是**逐提交**求值：已经触发失鲜的那个提交不会因为**后补**一个 `checkpoint(impl-review)` 提交而被追溯赦免。写进指引等于教人去做一件不起作用的事。

`checkpoint(impl-review)` 的正确定位是**事前、受控的 impl-review 提交协议**，只在该协议文档里说明，并明示「后补 checkpoint 不解除当前拒绝」。

**理由**：撞门者当前只能看到「结论陈旧」，无从判断下一步。指引出现的时机正好是它被需要的那一刻。

**边界**：纯诊断，不参与判定，不改退出码。**实现注意**：`is_stale` 现返回 `(stale, freshness)`，要携带触发点须改为结构化返回（如 `StaleResult(stale, freshness, trigger)`），且 code 域的 `freshness` 字符串取值 MUST 逐字不变（code-review / verify 读点依赖它）。

### ADR-3：dispatch 契约补信号权威表，且明确其防线定位

**决定**：`sdflow-implement` 的 implementer / fix dispatch prompt 携带信号权威表（正面陈述归属，非禁令清单）。

**理由**：正面陈述挡的是整个范畴，禁令只挡列举到的越界形态。

**定位声明（防后人误读）**：本项**不是**失鲜问题的防线——机械防线在 ADR-1。它解决的是另一件事：本仓自有管线不应写脏设计工件。两者各自独立成立，**MUST NOT** 因 ADR-1 已兜住失鲜后果而认为本项可省。

## Risks / Trade-offs

| 风险 | 评估 | 处置 |
|---|---|---|
| 判据分流后，既有 `checkpoint(impl-review)` 豁免路径回归 | 两条判据在同一函数内相邻，改动易误伤 | 既有豁免用例（含 BR-7 的 `checkpoint(impl-review)evil` 负例）MUST 全部保持绿，作为回归锚 |
| 归一化实现把非勾选框差异误判为等值 | 归一化过宽（如连带吞掉缩进/空白）会把真实改动放行 | 归一化 MUST 仅替换勾选框标记本身，MUST NOT 触碰缩进 / 空白 / 其余字符；须有「缩进变化 ⇒ 失鲜」负例 |
| 取前后两版内容的 git 调用引入新失败面 | `git show <sha>^:path` 在首提交 / 文件新增时无前版 | 前版不存在（文件在该提交中新建）⇒ **保守判失鲜**，MUST NOT 当作等值放行 |
| 消费仓未升级即认为已修复 | 分发经 `setup.sh` 软链，需 `/sdflow-upgrade` | hand-off 显著声明生效条件 |
| 「设计决策写进 tasks.md」的漏网面 | 见 ADR-1 代价，已显式接受 | 登记为已知取舍，不再另设补丁 |

## Compliance

- 判据 MUST 限于**行级等值比较**（勾选框标记归一化后逐行比对）；**MUST NOT** 做语义 diff、**MUST NOT** 解析 markdown 结构、**MUST NOT** 把豁免面扩到勾选框以外的任何差异形态〔spec-review-amendment〕。
- 豁免 MUST 仅在提交**只触及 `tasks.md`** 时成立；同一提交若还触及其他被监视路径，照判失鲜。
- 判据 MUST 逐提交独立求值，MUST NOT 依赖工作树状态或任何跨提交状态。
- `proposal.md` / `design.md` / `specs/` 的失鲜口径 MUST 逐字不变。
- 既有 `checkpoint(impl-review)` 精确式豁免（BR-7）MUST 不受本 change 影响。
- 新增判据分支 MUST 有变异验证：删掉该分支，对应用例 MUST 转红。
