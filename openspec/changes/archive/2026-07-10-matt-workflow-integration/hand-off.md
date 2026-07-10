# hand-off — matt-workflow-integration（2026-07-11）

## ✅ 完成了什么（锚点已复核，非搬运 verify）

- **新 skill `sdflow-implement`（tickets 实现管线双模式）**：出 ticket（3-6 张垂直切片、expand–contract 例外、外衣 `superpowers-plan.md`、写盘→checkpoint→返回三步序）+ 执行（frontier 串行、fresh implementer、完成信号后置双写 + resume 双信号核对、双轴审+熔断、halt envelope、文件交接）。锚：`sdflow-implement/SKILL.md`（存在且过 code-review 12 项修补）；派发契约二串与 ship 链序逐字一致（grep 双向核对过）。
- **机械路由层**：`sdflow-implement/scripts/impl_route.py`（route 三跳 + PIPELINE_RECEIPT + frontier 拓扑；BOM/引号损坏/键变体/fence 全 fail-closed，与 ship_gate 解析口径对齐）。锚：`sdflow-implement/tests/test_impl_route.py` 61 用例全绿；跨脚本 golden 回归（`sdflow-ship/tests/test_tickets_plan_golden.py` + fixtures）6 用例绿；仓级 pytest 877。
- **ship 原地条件路由**：`sdflow-ship/SKILL.md` :29 两映射条件化 + 试验期权威声明 + SHIPPED pipeline 字段；**ship_gate.py 零改动**（锚：git log 该文件本分支零 commit）。
- **config 键**：`impl-pipeline` 可选注释段落 template + 本仓（config-lint CLEAN；开键回归实测放行）。本仓**未开键**——首个试点 change 时再翻。
- **T126/T127 mainflow 规则**（assets 权威源）：三段分流 + wayfinder 降级 + TG 前置（增强非转移）、grill 瘦跑句、ff 衔接契约（`wayfinder-resolved:` 机械锚）+ 切片建议独立条款 + 双注入通道（`openspec instructions` 实测含契约文本）。
- **实测消解两假设**：4.1 disable-model-invocation **阻断**（受控探测 + 自然实证双证）→ 维持不写旗标；4.2 出 ticket→gate→执行最小演练全链通过（gate 零 UNKNOWN，含 resume 续审语义与命名空间归属）。锚：`impl-notes.md`。
- **试点判赢材料**：`pilot-briefing.md`（候选 5 项 + 拒绝条件 + 三判据 + receipt 留档口径）；消费仓 10-michi 缺省路径验证（receipt=superpowers，零写入）；wco roadmap Phase C 占位。
- **代码审**：6 源 26 canonical → 21 修复〔impl-review-fix〕（1 致命：双信号核对缺失；7 高：fence 口径分歧/Blocked-by fail-open/BOM/损坏引号/CONTINUE_IMPL 第三态/F10a 假绿/落盘顺序陷阱）。锚：`code-review-report.md` + commit 677301e。

## ⏳ 未完成 / 延后

- **批次 `matt-workflow-integration`**（见 `openspec/issues/batches.md` / INDEX）：本 change defer 项已 sweep 入批——**T128**（impl_route receipt 的 marker 显示折叠，display-only）。
- **Phase B 毕业清理**（proposal Non-Goals 既定，不入池重复记）：默认翻转、gate emit 串根治（:724/:750）、终局文件名迁移（tickets.md）、活文档全量表述同步、validator 学新键。
- **6.3 后半（唯一 Minor 缺口，已排期）**：运行 checkout 还原全局 symlink——merge+push 后立即经 `/sdflow-upgrade` 执行 + `readlink ~/.claude/skills/sdflow-ship` 验证指回 `~/.skills/sdflow-skills`（本 session 已获用户授权自动执行；若中断，按 CLAUDE.md「发布边界」纪律手动补）。
- 延后决策：无 T10 悬案（本 change 阶段三全部裁决有客观判据）。

## ▶ 下一阶段建议

1. **首个试点 change**：从 `pilot-briefing.md` 候选池挑一（推荐 mlh-P4·4.B maintain_scan 或 T63——逻辑面清晰、中型）；本仓 config 开 `impl-pipeline: tickets`，走全链；SHIPPED 后先再生 retro 核对哨兵再选下一个。receipt 留档 + marker 核对入判赢集。
2. **串行线 2（rebuild-sdflow-roadmap-v2）**：实施时核对其 sdflow-roadmap/SKILL.md 讨论层判据与本 change workflow.md 三段分流措辞一致性（同源 F11；code-review X2 裁决）；归档期注意 openspec/INDEX.md specs 能力表尾与本 change 的追加冲突（后归档者先核表尾现状）。
3. 消费仓推广经 `sdflow-init update`（规则自动获得；config 键不注入存量仓，逐仓人工决定开关）。

Roadmap 回填：exit 3（非 roadmap 驱动 change，无草稿）——但本 change 为 wco roadmap 补了 Phase C 占位（受限并行 frontier，判赢硬前置），wco 的 Phase C 启动判据即本 change 试点判赢材料。
