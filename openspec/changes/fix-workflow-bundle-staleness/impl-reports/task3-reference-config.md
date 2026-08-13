# Task 3 实现报告：reference 处置 + 同族面治 + config 同步

## 背景说明：ticket brief 文件不存在

主 prompt 要求先 Read `impl-reports/task3-brief.md`，但该文件在 `feat/fix-workflow-bundle-staleness`
分支上不存在（此 change 未走"每票单独 brief 文件"的产出形态，出 ticket 阶段直接把四张票落在
`tickets.md` 单文件里）。已改为 Read `tickets.md` 的「Task 3」小节作为等价 ticket 文本源，并交叉核对
`decision-memo.md`（D6/D7/D8/D9）、`design.md`（A1/A3/A5/A6 定位表行）、`spec-review-report.md`
（A1/A3/A5/A6 的详细定性与位点）三份产物，确认无遗漏、无臆造。

另注：本次 worktree 起初未包含该分支内容（`git log` 显示落在 main 的 `49aa4ee`，`feat/...` 分支领先
9 个 commit），已 `git merge --ff-only feat/fix-workflow-bundle-staleness` 拉平后才能看到 tickets.md /
design.md / spec-review-report.md 等产物文件。

## 改动位点 before → after

### 1. `sdflow-init/assets/workflow/reference/Spec_Quality_Collaboration.md`（顶部历史横幅，D7）

标题下方新增一段历史横幅：说明 `brainstorming`/`autoplan` 均已退役，现行对应
`/sdflow-spec` + `sdflow-spec-review`/`sdflow-code-review`，本文仅供历史设计脉络参考。原有第二段
"基于 superpowers 6.0.3 ... 对比分析" 原样保留（不改写正文内容，符合 D7"不移动"决策——
`reference/README.md:15` 已标注"历史分析"、`spec-review.md:34` 的引用继续有效）。

### 2. `sdflow-init/assets/workflow/reference/Spec_Quality_Methodology.md`（L1 历史举例标注，D8）

在三层关系 ASCII 图（L3/L2/L1）之后插入一行标注：L1 举例 `brainstorming/autoplan` 为历史工具名，
现行对应 `/sdflow-spec` 与 `sdflow-spec-review`/`sdflow-code-review`。**仅此一处标注，未逐处改写正文
5 处历史举例**（通则④最简方案 + memo D8 明文"逐处改写成本高、举例在框架语境里无害"）。

### 3. `Token_Saving_Strategies.md` git mv + 历史横幅（D7 + A6）

- `git mv sdflow-init/assets/workflow/reference/Token_Saving_Strategies.md docs/Token_Saving_Strategies.md`
  （git 记录为 rename，非删除重建；`git status` 确认 `RM` 标记，见下方"git mv 结果"）。
- 移动后顶部新增历史横幅："个人历史笔记（superpowers 时代），不代表现行工作流，与当前 spec 质量机器
  无关，纯使用提示存档"，正文其余部分（关闭 hook/plugin、`/clear` 用法等具体技巧）不改写。
- **未处理**：`reference/README.md:17` 引用该文件的行——设计表格已明确该行属 Task 1（`spec-review.md`
  等核心规则文件 + `reference/README.md` 三处修正）的位点清单，非本票范围，留给 Task 1 的实现者处理。

### 4. `PRD_vs_Spec.md` 4 处 opsx:ff → sdflow-spec + 顶部历史标注（A5）

- `:27`（原）代码块标题 `opsx:ff 产出物` → `/sdflow-spec 产出物`
- `:64`（原）`opsx:ff（生成 proposal.md）` → `/sdflow-spec（生成 proposal.md）`
- `:104`（原）"直接 `opsx:ff` 生成 spec" → "直接 `/sdflow-spec` 生成 spec"
- `:112`（原）风险防线表格行首列 `opsx:ff` → `/sdflow-spec`
- 顶部新增"历史举例标注"横幅：`plan-ceo-review`/`brainstorming` 为历史工具名，现行对应
  `sdflow-spec-review` 与 `/sdflow-spec` 拷问相位；说明 opsx:ff 已改指且仍兼容 `opsx:ff` 直呼。
  **未逐处改写**文中 `plan-ceo-review`/`autoplan`/`brainstorming` 其余 6 处历史举例
  （`:33/37/68/70/79/97/113`）——按 spec-review-report A5 定性"处置 = D8 同款顶部历史举例标注（不逐处
  改写，通则④）"。

### 5. `config.template.yaml`:23-27 号段去上界 + blurb 现行化（D6/D9）

- `:23` `TG-01~24` → `TG-NN`
- `:24` `BASE-01~28` → `BASE-NN`
- `:27` `生成过程（explore/brainstorming/grill 三相位）` → `生成过程：explore 发散 + /sdflow-spec（澄清→拷问→生成三相位）`
- `:25/:26`（design-diagrams.md / ff-generation-constraints.md 两行）未改——不在 ticket 位点清单内，且
  内容本身无号段/退役措辞问题。

### 6. `sdflow-init/assets/snippets/index-section.md` 按内容定位改 6 行（A1）

ticket 引用的行号 `:10/:11/:12/:13/:18/:19` 与当前文件真实内容完全对应（未见 spec-review-report A1 所述
的"memo 原引 :13,15,16 行号错位"问题——那是 memo 与更早版本文件的错位，出 ticket 阶段已按 A1 修正为
真实行号，实测与本次读到的文件一致）：

- `:10` workflow 行：`生成(ff+grill)` → `/sdflow-spec 生成`；`subagent-dev→sdflow-code-review→sdflow-done`
  → `实现(sdflow-implement)+代码审(sdflow-code-review)+收尾(sdflow-done)`（去掉已退役的 subagent-dev，
  tickets 唯一管线现由 sdflow-implement 承担实现）；`去 /clear、连续跑到 merge`（被
  `workflow.md:134` 明文否决的过度泛化，第三处正面矛盾）→ `阶段内部不用 /clear，仅两处阶段交界用
  （G1），连续跑到 merge`（措辞取自 workflow.md:85 G1 原文）
- `:11` `TG-01~28` → `TG-NN`（去号段上界）
- `:12` ff-generation-constraints blurb：`opsx:ff 起手强制` → `生成起手强制...（/sdflow-spec 调用，或
  opsx:ff 直呼）`（与 D5 现行化后的 ff-generation-constraints.md 外壳口径同步）
- `:13` generation-process blurb：`发散(explore)/收敛(brainstorming)/对抗压测(grill)` →
  `发散(explore) + /sdflow-spec（澄清→拷问→生成三相位）`（与 config.template.yaml:27 同款措辞，D9 同族
  面治）
- `:18` `BASE-01~30` → `BASE-NN`
- `:19` `CR-01~09` → `CR-NN`

### 7. `docs/sdflow-fable5/02-module-reference.md:160` 号段去上界（A3）

`TG-01~26`（三份文档并存的第三个漂移值：24/26/28）→ `TG-NN`。

### 8. `openspec/config.yaml` 与 template 同款行手动同步（D9）

对照结果：`openspec/config.yaml:7-11` 与 `config.template.yaml:23-27` 的 5 行内容（trigger-catalog /
spec-checklists / design-diagrams / ff-generation-constraints / generation-process 五行说明）已逐字
一致（`design-diagrams.md` 与 `ff-generation-constraints.md` 两行本就相同未改，其余 3 行同步为
`TG-NN` / `BASE-NN` / 现行化 generation-process 措辞）。两文件间**唯一存在的差异行**是
"spec 质量规则集见 openspec/workflow/" 一句——template 多一段 "（无本地副本时为 ~/.sdflow/workflow/，
下同）"，这是 template 面向"新项目可能有本地副本"场景的通用措辞，本仓 `config.yaml` 无本地副本恒定
成立（sdflow-init 源仓自身即 canonical 权威源），此差异为既有设计，非本次引入，未改动。

## git mv 结果

```
$ git status --short | head -3
RM sdflow-init/assets/workflow/reference/Token_Saving_Strategies.md -> docs/Token_Saving_Strategies.md
```

Rename 被 git 正确识别（R 标记），历史随 rename 保留，非删除重建。

## config.yaml 与 template 对照结果

已用 `sed -n` 分别打印两文件对应行人工比对，5 条共用行逐字一致（详见上文第 8 点）。未发现分叉。

## 完整变更文件清单

```
$ git status --short
RM sdflow-init/assets/workflow/reference/Token_Saving_Strategies.md -> docs/Token_Saving_Strategies.md
 M docs/sdflow-fable5/02-module-reference.md
 M openspec/config.yaml
 M sdflow-init/assets/snippets/index-section.md
 M sdflow-init/assets/workflow/config.template.yaml
 M sdflow-init/assets/workflow/reference/PRD_vs_Spec.md
 M sdflow-init/assets/workflow/reference/Spec_Quality_Collaboration.md
 M sdflow-init/assets/workflow/reference/Spec_Quality_Methodology.md
```

8 个改动位点全部完成（Task 3 验收清单 7 项逐一核对如下）：

- [x] reference 三文件横幅/标注均已添加（Collaboration 历史横幅 / Methodology L1 标注 / Token_Saving 移动后横幅）
- [x] `Token_Saving_Strategies.md` 已 git mv 至 `docs/` 且有历史横幅
- [x] `PRD_vs_Spec.md` 4 处 opsx:ff 已改 + 顶部标注已加
- [x] `index-section.md` 6 行全部按 A1 修正
- [x] `config.template.yaml` 号段去上界 + blurb 现行化
- [x] `openspec/config.yaml` 与 template 同款行一致（diff 对照，见上）
- [x] `docs/sdflow-fable5/02-module-reference.md`:160 号段已改

## TDD / 验证

本票是纯文本编辑 + 一次 git mv，无产品代码逻辑，无可跑的单元测试。验证手段：

1. `git status --short` 确认 `Token_Saving_Strategies.md` 以 `RM`（rename）而非 `D`+`A` 呈现——git mv 成功。
2. `git diff` 全量人工核对 8 个改动文件的最终 diff（已附于本报告"改动位点"节的对照描述）——每处均命中
   ticket 指定的行/位点，未越界改动 ticket 未列的行。
3. `grep -n "opsx:ff" PRD_vs_Spec.md` 确认全文仅剩本次新增的"历史举例标注"横幅里提及 opsx:ff（说明性
   引用，非需替换的正文用法），4 处正文 opsx:ff 已全部替换。

## Concerns / 未处理项（明确留给其他票）

- `reference/README.md:17`（Token_Saving 引用行删除）与 `:18`（quality-layering 描述改 P3c 口径）—
  design.md 位点表把这两处归入 Task 1 范围（"P3c/G2 两处正面矛盾按现行口径改写"及 README 相关行），
  Task 3 ticket 未列出，未动。若 Task 1 未处理，`reference/README.md:17` 会短暂指向一个已不存在的路径
  （`reference/Token_Saving_Strategies.md` 已 git mv 走），需在 Task 4 收尾门核验时确认 Task 1 已同步
  处理，否则会是一个新的死链接（本票不越界代做，如实标注供 Task 4 核验）。
- `PRD_vs_Spec.md` 文末 `:119` 的 `关联文档：Spec_Quality_Collaboration.md` 引用未改——该引用本身仍
  有效（Collaboration.md 未移动，只加了顶部横幅），无需修正。
