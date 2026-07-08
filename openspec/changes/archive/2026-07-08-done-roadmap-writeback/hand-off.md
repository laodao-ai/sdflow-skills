# hand-off — done-roadmap-writeback

> verify PASS 后、archive 前产出（随归档留档）。给 sdflow-done 加 roadmap 回填降摩擦助手：done 收尾读盘面生成 roadmap 回填草稿进 hand-off，机械搬运（定位到 phase）自动化、判断（勾哪几行）留人。

## ✅ 完成了什么

- **机械核脚本** `sdflow-done/scripts/roadmap_writeback_draft.py`（263+行 stdlib，8 命名空间 checkpoint task1–8）：
  - 关联解析（`parse_prefix` change 名前缀 `implement-{roadmap}-pN` 主 + `detect_markers` fence-aware 兜底 + `resolve_association` 优先级 flag>marker>prefix）
  - 盘面读（`read_verify_state` verify 三态 good/absent/malformed + `read_tasks_completion`）
  - 形态探测（`probe_format` checkbox/table-prose）+ phase 候选行定位（`locate_phase_rows`）
  - 草稿拼装（`assemble_draft` 机械锚 + archive/merge **静态占位** P-1）
  - CLI `main` 退出码 0/2/3/4/5/6/7（坏输入三分 C-9 + BadRoadmapFlag）
- **测试** `sdflow-done/tests/test_roadmap_writeback_draft.py`：**48 passed 0 warning**（全仓 762 green）。覆盖前缀解析/fence-aware 自指防御/时序占位/形态分治/判断留人/优先级/坏输入三分/dogfood/确定性。
- **编排集成** `sdflow-done/SKILL.md`：§2.2 回填助手子步（hand-off 步）+ 第六步摘要抬一行（P-4 merge 时点可见）+ 设计原则「同位不同性」登记（C-7）。
- **dogfood live 验证 P-5 防自指**：§2.2 在本 change 自身跑 → `exit 3 NO_ASSOCIATION 退现状`（本 change 产物含 marker 串于散文/fence 内，fence-aware 正确判无关联、无假阳）。这正是 C-5「dogfood 自指坑」设计要防的——live 通过。
- **切分线重画（三轮收敛终局）**：定位到 phase=机械（前缀确定性信号）、勾哪几行=判断留人；archive/merge 留占位不预填（P-1）；格式分形态 fail-loud（P-3）；detection fence-aware（P-5）。档案见 `adr/0015`（P-1..P-5 精化块）。

**证据锚**：verify-report.md（ship-gate.verify PASS，逐需求核对表）；code-review-report.md（ship-gate.code_review pass，10 自动修 [impl-review-fix]）；spec-review-report.md（ship-gate.design_approved，三轮收敛）。

## ⏳ 未完成 / 延后

- **批次 `done-roadmap-writeback`**（§2.1 sweep，见 `openspec/issues/batches.md` + `openspec/issues/INDEX.md`）：本 change 代码审 defer 4 项 **T89–T92**（todolist）：
  - T89 [中] `probe_format` 全文扫描非限定 phase → 混合格式 roadmap 误判（现两存量 roadmap 各单一格式无触发）
  - T90 [中] frontmatter 与 ship_gate.py 全量 parity 缺口 BOM/tab/YAML注释（nested-key 已 FIX-3 修；本仓格式固定 dogfood-green，消费仓非规范输入才漂移）
  - T91 [低] PREFIX_RE 命名固有歧义（记边界）
  - T92 [Minor] test duplicate/bad-enum 无 ship-gate 包裹的路径保真（行为正确已验，FIX-3 已补专项测试）
- **tasks 4.1 条件未触发（scoped-out）**：关联约定落 sdflow-done SKILL §2.2 + spec（skill 自包含、软约定），未推 workflow bundle 规则；命名约定非强制门。跨仓强制则另开 change。
- **异步回填残差（C-4，已登记）**：roadmap 回填草稿产出即止、apply 由人异步、不保证——经 /sdflow-ship 全自动链人被支走时尤然；第六步摘要抬行降概率但不全消。

## ▶ 下一阶段建议

- **T89/T90 值得一个 cleanup change**（若 roadmap 格式将走向混合、或本脚本要铺消费仓）：probe_format 限定 phase + frontmatter 对齐 ship_gate 全量口径（复用而非重实现，消漂移）。优先级中——当前两存量 roadmap 单一格式、本仓 verify-report 格式固定，无即时触发。
- **T91/T92 低优**：注释记边界 + 测试保真，可随手并入任何 sdflow-done 相关 change。
- **首次真实 roadmap 驱动 change 归档时**（如下一个 `implement-{roadmap}-pN-*`）：§2.2 会首次产出真草稿（exit 0），验证复选框式定位 + 机械锚落 hand-off 的端到端体验；留意草稿质量与「勾哪几行」的人确认摩擦是否真降。
