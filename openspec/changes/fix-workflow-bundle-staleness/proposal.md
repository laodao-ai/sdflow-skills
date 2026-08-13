# fix-workflow-bundle-staleness · Proposal

## Why

2026-08-13 对 workflow bundle（`sdflow-init/assets/workflow/`）全部 39 个 md 的逐文件审计发现三类失鲜：**两处正面矛盾**（`reference/README.md:18` 仍在传播被 P3c 否决的「sdflow-code-review 缩成高风险残差」旧结论；`spec-review.md:72`「进 AskUserQuestion」与 G2 决策登记区口径相抵）、**退役机制残留**（subagent-dev / writing-plans / 官方 code-review / `/clear` 旧口径）、**旧入口时代措辞**（brainstorming / opsx:ff / `/review` 消费方、TG·BASE 号段硬编码漂移）。bundle 是经全局 canonical 分发给所有消费仓的规则真相源——失鲜文案会被每个项目的 AI 侧当现行规则读取，矛盾口径直接误导执行。

## What Changes

- 两处正面矛盾按现行口径（P3c / G2）改写。
- 退役机制残留清理：`quality-layering.md` 的 subagent-dev、官方 code-review、`/clear +` 措辞；`spec-quality-base.md` 的 writing-plans 括注。
- `/review` 消费方统一改写为「sdflow-code-review（+ sdflow-implement Standards 轴必填槽）」（8 处：code-checklists 6 处 + trigger-catalog 1 处 + llm domain 1 处 `[spec-review-amendment A4：接地镜补 README:28]`）。
- `generation-process.md` 按 DOC-1 收史：§二改现行两工具表，§三整节移入 `workflow-history.md`（新增 A5），保住被 `test_canonical_entry_sync.py` 钉住的 §四措辞。
- `ff-generation-constraints.md` 外壳更新：标题、定位声明、调用方示例改 /sdflow-spec 语境；路径表述改 canonical 口径。
- 号段硬编码去上界（TG-01~24/28、BASE-01~28 共 5 处）——号段漂移已实证两次发生，删数字后无漂移面。
- `Spec_Quality_Collaboration.md` 加历史横幅；`Token_Saving_Strategies.md` 移出 bundle 至 `docs/`（个人使用笔记，非工作流资产）并加历史横幅；`PRD_vs_Spec.md` 另加顶部历史举例标注 `[spec-review-amendment A5/A6]`。
- `Spec_Quality_Methodology.md` 顶部加「L1 举例为历史工具名」标注。
- 同族面治：`index-section.md`（:10/:11/:12/:13/:18/:19，含第三处正面矛盾「去 /clear」）/ `config.template.yaml` / 本仓 `openspec/config.yaml`（手动同步，update 不覆盖 config）/ `reference/README.md` / `PRD_vs_Spec.md` 举例 / `quality-layering.md`:38 与 `docs/sdflow-fable5/02-module-reference.md`:160 号段 `[spec-review-amendment A1/A2/A3]`。

**不改**：任何规则语义、文件路径（Token_Saving 移出除外）、目录结构、机读块、`workflow.md` 正文、`WORKFLOW-GUIDE.md`（生成物）、`workflow-history.md` 既有条目（只增 A5）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无——纯文档措辞失鲜修正，不改变任何 spec 级行为；`.openspec.yaml` 已设 `skip_specs: true`。）

## Impact

- **改动面**：`sdflow-init/assets/workflow/` 下 12 个 md + `config.template.yaml` + `sdflow-init/assets/snippets/index-section.md` + 本仓 `openspec/config.yaml` + `docs/`（接收 Token_Saving_Strategies.md）+ `openspec/INDEX.md`（update 刷新）。
- **消费方**：所有已铺 bundle 的消费仓（下次 `sdflow-init update` / canonical 软链即时生效两条路径）；本仓 AI 侧（CLAUDE.md 引用的规则文件）。
- **技术栈触发**：不命中 TG-01/02/03（Markdown + 工具仓，无 backend/embedded/frontend 领域）；命中 TG-25 精神面（一处口径牵连一组文档）⇒ design 含全套 scope-check 表。
- **机械守卫**：`test_canonical_entry_sync.py`（generation-process §四措辞 presence + 退役短语 absence）、`gen_workflow_guide --check`、全仓 pytest `-W error`——均为改动的直接门禁。

## Success Metrics

1. **失鲜位点清零** — 基准：审计清单 D1-D9 共约 30 个位点 → 目标：0 残留 — 度量：按 decision-memo C4/C8 的 grep 命令复扫，命中数为 0。
2. **正面矛盾清零** — 基准：2 处（P3c / G2）→ 目标：0 — 度量：对读 `reference/README.md` ↔ `quality-layering.md` §五、`spec-review.md` §四点五 ↔ `workflow.md` G2，口径一致。
3. **机械门全绿** — 基准：改动前全仓 2649 passed → 目标：改动后全仓 pytest `-W error` 全绿 + `gen_workflow_guide --check` 绿 + `sync_principles --check` 绿 — 度量：命令退出码。

## Non-Goals

- 不重构 bundle 目录结构（不建 `rules/` 子目录）——假设：若结构真需重组，路径消费者横跨 4 种文件类型的迁移应独立成 change 评审，本次混入会掩盖文字修正的低风险性。
- 不改 `workflow.md` 正文与任何机读块（`lens-metric-enums` / `model-tier-defaults` 等）——假设：审计未发现其失鲜；若后续发现，另开 change。
- 不逐处改写 `Spec_Quality_Methodology.md` 的 5 处历史举例（仅顶部标注）——假设：L3 框架不受举例影响；若读者实证被误导，再升级为改写。
- 不在本次触发各消费仓的 `sdflow-init update`（发布边界既有节奏，merge 后由人择机执行）。

## Compliance

N/A——纯仓内文档变更，无 PII、无第三方数据、无合规约束。
