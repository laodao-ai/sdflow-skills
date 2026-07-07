# hand-off — mlh-p2-anchor-lint

> roadmap「机械层固化」阶段 2（Leg1 高频门禁）。verify 之后 / archive 之前产出，随归档留档。

## ✅ 完成了什么（每条附机验锚点）

- **anchor_lint.py 确定性锚自检门**（`sdflow-init/assets/workflow/tools/anchor_lint.py`）：把两审 SKILL 的手工「grep 四类锚 + 肉眼核 enum」降为脚本门。退出码 0/1/2、双输出、纯 stdlib、脚本内重实现 fence 核（禁跨 skill import）。锚点：`test_anchor_lint.py` 全绿（242 passed 全量含此）。
- **契约 `lens-metric-enums` 机读块**（`lens-metric-contract.md:19-24`）作枚举机读单一源；aggregator 一致性 + 双解析器交叉断言（`test_aggregator_enum_matches_contract`/`test_dual_parser_cross_assert`/`test_fence_core_cross_equivalence`）。
- **copy_bundle 契约同刷**（`init.py:159-163`）防本地 pin 部署错配；`test_copy_bundle_refreshes_contract`。
- **两审 SKILL 自检步接脚本 + 保留数值一致性诚实边界**（spec-review:79 / code-review:118-125）；dogfood exit=0 CLEAN。
- **roadmap 复用→重实现调和**（design.md:56+:139 / roadmap.md:61 / task-log.md）。
- spec-workflow +1 ADDED 需求（锚自检由确定性脚本判定）+ 12 Scenario。
- verify PASS（`verify-report.md`，`ship-gate: verify=PASS`）。

## ⏳ 未完成 / 延后

- **批次 `mlh-p2-anchor-lint`**（见 `openspec/issues/batches.md` + `openspec/issues/INDEX.md`），成员 T68/T69（code-review defer）：
  - **T68**：`load_enums` 契约块内若未来加裸 ``` 行会提前闭合致 EnumsError（潜伏、fail-closed 安全侧、契约受控，加防护属过度工程）。
  - **T69**：缺 pin 消费仓 update 端到端交叉不变量测试（各组件已单测，端到端组合缺）。
- **无 ≥2 方案延后决策**（本 change 所有决策修法唯一明确；grill Q1-Q3 + spec-review Q1/Q2 均已拍板）。
- **verify Minor（可接受）**：roadmap 高层就绪表（roadmap.md:15/:54/:85）仍用「复用现成纯函数」描述就绪度/ROI——非技术 import 断言，真正的技术矛盾点（:56/:139）已调和，就绪度措辞可后续统一。

## ▶ 下一阶段建议

- **roadmap 阶段 3（P3 确定性守卫补全）**：3.A recorder 镜像 helper 一致性测试（`inspect.getsource` 源码级相等，3向/2向拓扑）+ 3.B config/batches lint。就绪、纯增测/校验器、独立可交付。3.A+3.B 可合批（同 cap「确定性守卫」）。
- 清 T68/T69 建议**并入 P3**（P3 本就是「确定性守卫」主题，T69 的端到端 pin 测试天然属之；T68 潜伏低优先，可 P3 顺带或继续 defer）。
- 阶段 5（gate 锚 frontmatter）ROI 门：本 change 是其顺序前置（Leg1 先行），非锚层依赖——阶段 5 起手仍须过显式 ROI 门 + 核 ship_gate 铺设路径。
