# 把三镜决策框架焊进 workflow 源头（T46）

## Why

「三镜决策框架（系统镜 / 用户镜 / 开发循环镜 + 定主次）」当前**只活在私有记忆** `decision-three-lens-framework.md`（行为层真相源）。但：

- **子代理够不着**：sdflow-spec-review / sdflow-code-review 的评审镜是 fresh-context 子代理，不继承主 session 记忆——它们做决策登记 / 自动裁决时看不到这套框架。
- **其它 checkout / 用户没有**：workflow bundle 是**发布给其它项目和用户的产品**，必须自包含；依赖某人机器上的私有记忆 = 换台机器 / 换个用户就退化。

T46 = 把框架从私有记忆**搬进发布的 workflow bundle**，让「决策必按三镜 + 定主次」跨 session / 子代理 / checkout 稳定生效——**书面层（bundle 内 TG-23 触发的决策）不再依赖运行者的私有记忆**即可生效〔spec-review F4/CV3：行为层每决策纪律仍系于记忆真相源，本 change 只令书面层自包含，不作绝对化承诺〕。

## What Changes

**六处落点**（均在权威源 `sdflow-init/assets/workflow/` 与自制 skill，非消费仓副本）〔落点集经 spec-review 完整性镜穷举校准：原列 3 处漏了 spec-review SKILL 与 ship SKILL 台账副本；第 6 处为设计门追加的 scope-triage 判据〕：

1. **`spec-checklists/spec-quality-base.md` BASE-12**（书面层）：三镜评估法挂进「候选方案」、主次判定行挂进「理由」；**仅 TG-23（≥2 合理方案 / 非显然设计）触发时 MUST 写**，不下沉到琐碎决策。（三镜为**新挂入** ADR 结构，非替换旧串。）
2. **`workflow.md` G2 决策登记区**（行 72 设计门 + 行 83 G2）：登记格式「选项 + 推荐 + 两方后果」→「选项 + 推荐 + **三面后果（系统 / 用户 / 开发循环）+ 主次判定**」。
3. **`sdflow-code-review/SKILL.md` Step 4**（含 frontmatter 行 7-8 / 导语行 30 / Step4 行 96 / 台账行 143-144）：自动选推荐的「记理由」→ 按**三镜 + 主次**记；**并顺手把陈旧散文「≥2 方案有把握自动选」对齐到 T10 三级协议**〔Q1 采 A：T10 早已是既定行为（ship:23 / 主spec:48 / workflow.md:84 / 本文件台账:144 均 T10），96 的「有把握」是漏改残留、且与自身台账:144 自相矛盾；对齐=纯一致性修复、非行为变更，照 ship:23 canonical 措辞抄〕。
4. **`sdflow-spec-review/SKILL.md`**〔spec-review F1/CV1 补齐的第 4 落点〕（frontmatter 行 8 / 正文行 24 / TENSION 行 77 / 决策登记区格式块行 89）：内联硬编码的「两方后果 / 两方视角 + 后果 / 各自后果」→ 三面后果 + 主次判定。**它是产出决策登记区的实际执行入口，不改则归档后主 spec 与发布产品自相矛盾。**
5. **`sdflow-ship/SKILL.md`（行 23 T10 台账）**〔spec-review 完整性镜补齐的第 5 落点〕：与 `sdflow-code-review/SKILL.md:144` 同串的 T10 台账格式副本，随 code-review 台账同步补主次判定，防权威源内部两处台账不一致。
6. **`spec-checklists/spec-quality-base.md` BASE-18 分解检查**〔设计门追加：fold-vs-defer scope-triage 判据〕：补「过程中新发现的需求/修复，并入当前 change vs 另开」的判据——按对当前 change 影响 + **workflow 循环固定成本高**判，related + 低影响（紧耦合/同 capability/一致性修复/blast-radius 小）→ fold；真独立/扩容大/需自身设计审查 → defer 另开。此判定走三镜、开发循环镜主导。**这是三镜框架在 scope 决策上的专用应用，与主题同 capability，故 fold 进 T46（用它自己的判据判它自己）。**

**spec delta（防漂移锚）**：`spec-workflow/spec.md` 两条行为需求同步——「评审决策登记进报告」的后果字段 + 「outside-voice tension」的 TENSION 条目格式，从「各分支后果 / 两方视角」→「三面后果 + 主次判定」。

**分层强度**：行为层（私有记忆保留，仍是行为真相源）每个决策都用；书面层（bundle）只在 TG-23 触发时 MUST——避免样板税。

## Capabilities

- **Modified**: `spec-workflow` — 评审决策登记 / outside-voice tension 的决策后果格式升级为三面后果 + 主次判定。

## Priority

P2（治理层增强，非阻塞）。改动传导进此后**每个**决策的登记与裁决口径，故走独立 change + spec delta 留审计与防漂移锚（不裸改源）。

## Out of Scope

- **不改行为层记忆**：`decision-three-lens-framework.md` 仍是行为真相源，本 change 只做「私有记忆 → 发布 bundle」的搬运与锚定。
- **不重写既有 ADR**：review-tool-followups 的 ADR-0/1/2 已按三镜回填，作参考样例，不动。
- **不新增独立规则文件 / 编号项**：三镜挂进 BASE-12 现有槽（见 design ADR-1），不建 `three-lens.md` 或 BASE-30（避双源）。
- **docs/ 可视化镜像延后**〔spec-review F3〕：`docs/workflow-overview.md` / `docs/workflow-skills/sdflow-spec-review.md` 等镜像仍带旧「两方后果 / 两方视角」措辞，本 change **不刷**（非权威源、量大），显式声明延后另 change 刷，不静默留漂移。

> 〔Q1 采 A 后，「有把握」→ T10 对齐**已纳入本 change**（落点③），不再 defer。〕
