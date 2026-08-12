# Proposal · implement-workflow-optimization-2026-08-p5

## Why

roadmap `workflow-optimization-2026-08` 阶段 5（人类门减负与 context 工程）：设计 HARD-GATE
是全流程唯一人类门，其拍板质量与 SKILL 加载的 context 成本是当前工作流的两处未收口成本面。
阶段 1–4 已全部归档，阶段 5 的三个雾区前置（T101/T102 重分诊、报告结构稳定、T275 界线拍板
路径）已于 2026-08-12 核清（roadmap 阶段 5 节），frontier 到达。

## What Changes

- **T275（主力）**：14 个 SKILL.md 落实 DOC-1（`openspec/rules/doc-authoring.md`）考古层
  审计清理，7 个超 500 行者重点（implement 821 / code-review 771 / roadmap 715 /
  spec-review 593 / done 567 / architecture 562 / spec 528 行，2026-08-12 实测）。
  界线 = decision-memo D1：尽量删；确需保留者迁该 skill `references/` 旁文件（默认不加载），
  正文末尾只留一行指针。`sdflow:principles` 托管块不动。
- **T101 残余**：spec-review 报告拍板层补「拍板三问」（①范围划界认不认 ②依赖/顺序认不认
  ③风险赌注与对策认不认）+ `anchor_lint` 拍板层存在性机验（新结构化锚）。只落设计门，
  code-review 不加（decision-memo D2）。改 `sdflow-init/assets/workflow/` 权威源 + bundle 同步。
- **提问分批条款**：sdflow-spec SKILL A.1/B.3 修订（decision-memo D3，呈现与拍板分离）：
  互相独立问题 MAY 分批（≤4/批，每问必附推荐）；依赖链整链呈现（链结构 + 每环推荐 +
  推荐整链路径），人可拍整链或链头；组合爆炸时退回链头 + 下游影响预告。
- **T256**：不实现。调研记录已落盘（`openspec/issues/open/todo/T256.md` 2026-08-12 段），
  issue 保持 OPEN（decision-memo D4：Codex 宿主 ~258K 可用 context 下问题真实，未来方向
  推荐 merge 意图落盘化优先于 PreCompact hook）。
- **收尾回填**：roadmap 阶段 5 的 5.3 措辞按 D4 修正（「评估收口」→「调研记录 + 保持 OPEN」），
  T101/T275 set-status。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `spec-authoring`：SA-03 相位 A/B 提问节奏 Requirement 变更——「一次只问一个问题」放宽为
  D3 的分批/整链呈现协议（spec-level 行为变更：拷问交互契约）。
- `spec-workflow`：设计门评审报告结构 Requirement 变更——拍板层新增拍板三问段 + 结构化锚，
  报告锚自检（anchor_lint）新增拍板层存在性检查（spec-level 行为变更：报告契约 + 机械校验面）。

## Impact

- **SKILL.md（14 个顶层 skill）**：正文考古层删除/外迁；新增若干 `references/evolution-notes.md`
  类旁文件。爆破面 = 消费 SKILL.md 文本的测试（hack/tests 11 个 + skill 侧 tests 11 个文件，
  memo C2），全仓 pytest 必须保持绿；`sync_principles.py --check` 门不受影响（托管块不动）。
- **workflow bundle 权威源**（`sdflow-init/assets/workflow/`）：spec-review 相关规则/清单中
  报告模版段 + `tools/anchor_lint.py` + 锚契约文档；经 `sdflow-init update` 下发消费仓。
- **sdflow-spec-review / sdflow-spec 两个 SKILL**：Step3 报告组装条款 / A.1+B.3 提问条款。
- **不碰**：ship_gate.py（B25/B26 门语义不变）、评审镜 roster、裁决协议（adr/0041 不动）、
  model/effort 分档链。
- 技术栈：Markdown + Python（pytest），不命中 backend/embedded/frontend 领域清单；
  命中 TG-28（devex：报告契约面 + lint 校验面变更，spec-review 侧激活 devex 镜）。

## Success Metrics

- 7 个超 500 行 SKILL.md 清理后行数显著下降（逐文件审计留档记录删/迁/留三数），
  14 个全部过 DOC-1 审计（删除测试：「只有读过上一版的人才需要的句子」正文归零）。
- anchor_lint 对含/缺拍板层锚的报告分别 PASS/FAIL（含负例测试）+ 对 p4 归档报告手工
  加段回放核验（时序注记：本 change 自身 spec-review 跑在实现**之前**、用旧版 SKILL，
  结构性无法 dogfood 三问——首个真实 dogfood = 本 change 之后的下一次设计审，挂
  hand-off 交接）。
- 全仓 pytest 绿（含新增 anchor_lint 测试与既有 SKILL 文本消费测试）。
- T101/T275 到达终态、T256 保持 OPEN 且调研记录在册。

## Non-Goals

- T256 的任何实现（PreCompact hook / merge 意图落盘化）——仅调研记录，实现留未来 change。
- SKILL.md 的语义重写/行为变更——T275 只删/迁考古层，不改指令语义（编辑动作，非重构）。
- code-review 报告加拍板三问（D2 砍掉：无人门的报告不加结构）。
- 评审镜 roster、裁决协议（adr/0041）、model/effort 分档的任何改动。
- `openspec/rules/doc-authoring.md`（DOC-1）本身的修订——D1 界线是其操作化，不改规则文本。

## 需求优先级（TG-19）

| 优先级 | 项 | 理由 |
|---|---|---|
| P0 | T275 考古层清理（7 个大 SKILL） | 主力交付物，context 成本直接受益 |
| P0 | 拍板三问 + anchor_lint 机验 | 人类门质量结构化，本 change 自审即 dogfood |
| P1 | sdflow-spec 分批条款 | 已有人工实测样本，条款成文即收益 |
| P1 | 其余 7 个 SKILL 审计（≤500 行者） | 审计必做，预期改动量小 |
| P2 | roadmap/issues 收尾回填 | 书记性，随 done 流程走 |

## 假设（TG-22）

| 假设 | 失效影响 |
|---|---|
| 考古层删/迁不改变 SKILL 行为语义（判据 = DOC-1 删除测试，逐条人可复核） | 失效 = 某 SKILL 执行行为变化；由审计留档 + 全仓 pytest + code-review 冷层三层兜；残余风险见 memo「接受的边角」 |
| `references/` 旁文件默认不加载对所有 skill 成立（Claude Code 只注入 SKILL.md 正文） | 失效 = 迁移不省 token；sdflow-spec 先例（`references/evolution-notes.md` 按需读）为证，若发现例外则该 skill 改为直接删除 |
| 拍板三问可在不破坏既有报告锚契约的前提下以新锚增量加入（既有 gate/lint 不认识的锚被忽略） | 失效 = 存量报告校验误伤；以 anchor_lint 负例测试 + 历史归档报告回放核验 |

## Compliance

N/A（本仓为本地工具链仓库，无外部合规约束；不涉敏感数据与信任边界变更）。
