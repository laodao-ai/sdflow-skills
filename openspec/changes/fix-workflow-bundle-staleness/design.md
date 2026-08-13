# fix-workflow-bundle-staleness · Design

## Context

见 proposal.md「Why」。补充设计层现状约束：

- bundle 经三条路径被消费：① 全局 canonical 软链 `~/.sdflow/workflow/` → 运行 checkout（规则文件运行时读取）；② `init.py` 按名拷贝 `WORKFLOW-GUIDE.md` 进消费仓；③ `config.template.yaml` / `index-section.md` 经 init/update 注入消费仓。⇒ 改动只需落在 assets 权威源；本仓 `openspec/config.yaml` 是唯一要手动同步的实例（update 实证不覆盖 config）。
- 三个机械守卫钉住改动边界：`test_canonical_entry_sync.py`（generation-process §四措辞 presence + 退役短语 absence）、`gen_workflow_guide.py --check`（GUIDE ↔ workflow.md+prompts/ 一致）、全仓 pytest `-W error`。
- `WORKFLOW-GUIDE.md` 是生成物；`workflow.md` 与 `prompts/` 本次不动 ⇒ GUIDE 无需重生成（`--check` 兜底）。

## Goals / Non-Goals

**Goals（设计层边界）**：每处修改是「措辞替换 / 整节移史 / 加横幅 / 移文件」四种操作之一；不引入任何新机制、新文件（workflow-history A5 条目除外）、新路径。

**Non-Goals**：见 proposal.md「Non-Goals」；另加一条设计层排除——不为「号段漂移」新增机械守卫（去号段后无漂移面，守卫无对象；若未来恢复号段表述再议）。

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)（D1-D10）。

## Scope-Check 表（TG-25 / BASE-29：bundle 全套 md × 是否改 × 理由）

| 文件 | 改? | 内容 / 不改理由 |
|---|---|---|
| `workflow.md` | ✗ | 审计口径全部现行（G1/G2/P3c 源头文档） |
| `WORKFLOW-GUIDE.md` | ✗ | 生成物，源不动则不动（`--check` 守） |
| `workflow-history.md` | ✓ | 新增 A5（承接 generation-process §三 的 grill 论证考古） |
| `trigger-catalog.md` | ✓ | :108 `/review` → sdflow-code-review（D3） |
| `model-tiers.md` | ✗ | 机读块 + 表格均现行 |
| `lens-metric-contract.md` | ✗ | 机读契约现行；`claude-fallback 废弃` 为有意墓碑 |
| `design-diagrams.md` | ✗ | T42 刚扩展，口径现行 |
| `ff-generation-constraints.md` | ✓ | 标题/定位/调用示例改 sdflow-spec 语境 + canonical 路径（D5）；背景/历史节原位保留 |
| `generation-process.md` | ✓ | §二现行化（含 :21 标题行 `[spec-review-amendment A8]`）、§三移史、§六措辞（D4）；§四措辞逐字保留（评审 Q1/Q2 对 §四图与触发规则② 另有待拍板项，见 spec-review-report 决策登记区） |
| `spec-review.md` | ✓ | :72 AskUserQuestion→决策登记区（D1）、:29 删「/clear 后重审」、:91 brainstorming→生成期自检、:92 去 BASE 号段（D9/D6） |
| `spec-checklists/README.md` | ✓ | :62 `rules/` 错路径 → `../`、:64 R 落点措辞现行化（D9） |
| `spec-checklists/spec-quality-base.md` | ✓ | :37 writing-plans → 出 ticket（D2）；:7 来源行保留（provenance 非失鲜） |
| `spec-checklists/domains/*`（backend·go / devex / embedded·esp32·ml307c / frontend，7 个） | ✗ | 面扫零命中 |
| `code-checklists/README.md` | ✓ | :3,13,28,53,68（5 处 `[spec-review-amendment A4：+:28]`）`/review` → 现行消费方（D3） |
| `code-checklists/code-review-base.md` | ✓ | :3 同上（D3） |
| `code-checklists/domains/llm.md` | ✓ | :5 同上（D3） |
| `code-checklists/domains/*`（其余 5 个） | ✗ | 面扫零命中 |
| `prompts/step{1,4,5,8,9}-*.md` | ✗ | 与现行五步逐字对齐 |
| `reference/README.md` | ✓ | :6-8 部署观改 canonical、:17 删 Token_Saving 行、:18 quality-layering 描述改 P3c 口径（D1/D7/D9） |
| `reference/quality-layering.md` | ✓ | :25 `/clear +` 措辞、:42 官方 code-review 表行、:84 subagent-dev（D2）；:38 CR-01~09 去上界 `[spec-review-amendment A2]`；:14 出处标注保留 |
| `reference/scope-drift-diagnosis.md` | ✗ | 现行（:13「plan/review/code」为泛指） |
| `reference/Spec_Quality_Methodology.md` | ✓ | 顶部加 L1 历史举例标注（D8） |
| `reference/Spec_Quality_Collaboration.md` | ✓ | 顶部加历史横幅（D7） |
| `reference/PRD_vs_Spec.md` | ✓ | 4 处 opsx:ff 举例 → sdflow-spec（D9）+ 顶部历史举例标注（D8 同款）`[spec-review-amendment A5]` |
| `reference/Token_Saving_Strategies.md` | ✓ | git mv → `docs/`（D7）+ 移动后顶部历史横幅 `[spec-review-amendment A6]` |
| `sdflow-guide.html` | ✗ | 昨日新迁入，内容现行（非 md，列此为完备） |
| `config.template.yaml` | ✓ | :23-27 去号段 + 现行化 blurb（D6/D9） |
| —— bundle 外同族 —— | | |
| `snippets/index-section.md` | ✓ | 按内容定位改 :10/:11/:12/:13/:18/:19（D9/D6；`[spec-review-amendment A1]`——memo 原引 :13,15,16 行号错位勘误 + :10 的 ff+grill/subagent-dev/「去 /clear」第三矛盾、:12 opsx:ff blurb、:18/:19 号段一并纳入） |
| `docs/sdflow-fable5/02-module-reference.md` | ✓ | :160 `TG-01~26`（第三漂移值）去上界 `[spec-review-amendment A3]` |
| 本仓 `openspec/config.yaml` | ✓ | 与 template 同款行手动同步（D9） |
| 本仓 `openspec/INDEX.md` | ✓ | 由 `init.py update` 从 snippet 再生，不手改（**须在 index-section 修正后再跑 update**，否则失鲜行回灌 `[spec-review-amendment]`） |

## 改动面与门禁关系图

```
  assets/workflow/*.md ────┬──▶ 全局 canonical ~/.sdflow/workflow/（软链，pull 即生效）
  （12 个 md 措辞修改）     ├──▶ test_canonical_entry_sync.py   ◀─ 守 generation-process §四
                           └──▶ 全仓 pytest -W error
  assets/workflow/config.template.yaml ──▶ 消费仓 config（新铺/合并时）
  assets/snippets/index-section.md ──▶ init.py update ──▶ 本仓+消费仓 INDEX.md 托管区块
  本仓 openspec/config.yaml ──（手动同步，update 不覆盖）
  workflow.md + prompts/（不动）──▶ gen_workflow_guide --check ──▶ WORKFLOW-GUIDE.md（不动）
  reference/Token_Saving_Strategies.md ──git mv──▶ docs/（唯一引用行同步删除）
```

## Risks / Trade-offs

- [`test_canonical_entry_sync` 红：§二/§三改写误伤 §四 presence 措辞] → 改写前后 grep 四短语仍在；absence 清单（「分支 A」等）本次不引入。
- [`gen_workflow_guide --check` 红：误动 workflow.md] → 本次 workflow.md 零编辑；收尾门跑 `--check` 兜底。
- [config.yaml 手动同步遗漏 → 本仓与 template 分叉] → 收尾用 diff 对照 template 对应行；该分叉只影响本仓 AI 读侧文案，无机械后果。
- [generation-process §三移史后编号空洞] → 保 §四编号不重排（`workflow.md:60` 外部锚），正文留一行指路 A5；已记 memo「接受的边角」。
- [消费仓在 update 前继续读旧文案] → 发布边界既有节奏，非本次引入；merge 后由人择机 update（proposal Non-Goals）。

## Migration Plan

1. 按 scope-check 表逐文件修改（纯文本编辑 + 1 次 `git mv`）。
2. 收尾门：`sync_principles --check` → `gen_workflow_guide --check` → `python3 sdflow-init/scripts/init.py update --root .`（刷 INDEX/GUIDE 镜像）→ 全仓 `/usr/bin/python3 -m pytest -W error`。
3. 复扫 Success Metrics 1/2 的 grep 清单，确认 0 残留。
4. 发布：merge 后 push → 运行 checkout `git pull` + `setup.sh`（canonical 即时生效）→ 各消费仓 `sdflow-init update` 由人择机。

**回滚**：单 change revert 即整体复原（纯文本 + 一次 git mv，无状态迁移）。

## Open Questions

（无——可延后的未知均不存在；全部决策已在 memo 拍板。）

## Compliance

遵守 `openspec/rules/doc-authoring.md`（DOC-1：本 change 即其执行——正文只留现行态，考古入 workflow-history/横幅标注）与 `openspec/rules/premise-verification.md`（全部断言带 memo C1-C9 证据锚）。无豁免项。
