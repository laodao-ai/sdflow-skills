> Requirement 追溯（specs/maintain-scan/spec.md）：
> - R1 = specs/rules ↔ INDEX 双向 set-diff
> - R2 = CLAUDE.md 过时引用扫描
> - R3 = workflow bundle 陈旧遮蔽兜底扫描
> - R4 = 坏输入 fail-closed（重锚防假『一致』，grill A4）
> - R5 = 只读且可观测
> - R-guard = 跨脚本共享判据一致性守卫（grill A2/A3）

## 1. 数据类化骨架

- [ ] 1.1 建 `sdflow-maintain/scripts/` + `sdflow-maintain/tests/` 目录；`maintain_scan.py` 模块骨架：`main(argv=None)` + `sys.exit(main())`、typed `MaintainScanError`、`--root` 参数（默认探测 git 根）。〔D5/D6〕
- [ ] 1.2 建 `tests/test_maintain_scan.py` 骨架 + tmp 仓夹具（造 `openspec/specs|rules|INDEX.md` 最小结构的 helper）。〔TG-18〕

## 2. specs/rules ↔ INDEX 双向 set-diff（R1，含托管块排除）

- [ ] 2.1 扫 `openspec/specs/*/spec.md` + `openspec/rules/*.md`（rules/ 可选，缺失按空集）→ 当前 spec/rule 名集合。〔R1，grill A1〕
- [ ] 2.2 解析 `INDEX.md` 表格行 → 已列 spec/rule 名集合；**MUST 排除 `opsx-init:rules:start..end` 托管块**（marker 界定）。〔R1，D7 grill A3〕
- [ ] 2.3 双向 set-diff：新增未索引（fs−INDEX）/ 已删未清理（INDEX−fs），分 spec/rule 类。〔R1〕
- [ ] 2.4 测试：新 spec 未索引 / INDEX 列已删 rule / 完全一致 / **托管块内条目不被误当已删** 四场景，断言分类正确 + 退出 0。〔R1〕

## 3. CLAUDE.md 过时引用扫描（R2）

- [ ] 3.1 扫根 + 子目录 `CLAUDE.md`，检出引用已删 spec/rule 路径的位置（文件+行号）。〔R2〕
- [ ] 3.2 测试：CLAUDE.md 引已删 spec → 报告列文件+行号+条目名 / 全存在 → 该小节空。〔R2〕

## 4. workflow bundle 陈旧遮蔽兜底扫描（R3，canonical-in-init）

- [ ] 4.1 maintain_scan 保 `RULE_MARKERS` 副本（canonical=`init.py`）+ `hack/checkpoint-commit.sh` 孤儿检查；扫 `openspec/workflow/` 残留规则本体。〔R3，D4 grill A2〕
- [ ] 4.2 命中输出与 `sdflow-init` `stale_shadow_warnings` 同款告警文案（遮蔽全局/pin 二选提示）。〔R3〕
- [ ] 4.3 测试：workflow 下残留 `workflow.md` → 报告陈旧遮蔽 / 仅剩 `tools/` → 空。〔R3〕

## 4b. 跨脚本共享判据一致性守卫（R-guard，grill A2/A3）

- [ ] 4b.1 一致性守卫 pytest：断言 `maintain_scan.RULE_MARKERS == init.RULE_MARKERS`（不等即 fail，闭 T17）。〔R-guard〕
- [ ] 4b.2 一致性守卫 pytest：断言 maintain_scan 用的 `opsx-init:rules` marker == `init.MARK_IDX`。〔R-guard，D7〕
- [ ] 4b.3 记 todolist：`resolve-workflow.sh` bash 第 3 份 RULE_MARKERS 副本跨语言难同守 → defer（本 change 不扩 scope）。

## 5. 坏输入 fail-closed——重锚防假『一致』（R4，grill A4）

- [ ] 5.1 INDEX 缺失 → 非零退出 + stderr 明示；不输出「一致」误判。〔R4〕
- [ ] 5.2 INDEX 结构不可信（骨架缺失/托管 marker 不配对/行畸形无法确信）→ 非零退出，报「结构不可信拒绝输出一致」。〔R4，D2 防假一致〕
- [ ] 5.3 INDEX 读到 0 条 spec 条目（结构完好）→ **退出 0**，响亮报全部新增未索引（**非** fail）。〔R4，grill A4〕
- [ ] 5.4 specs/ 缺失 → 非零；rules/ 缺失（可选）→ 退出 0 按空集。〔R4，grill A1〕
- [ ] 5.5 测试：5.1/5.2 断言非零 + stderr（负例）；5.3 断言 0 + 全新报告；5.4 断言 specs/ 缺失非零、rules/ 缺失为 0。〔R4〕

## 6. 只读 + 可观测报告（R5）

- [ ] 6.1 报告四类分节渲染（新增未索引/已删未清理/过时引用/陈旧遮蔽），人可读、条目具体。〔R5〕
- [ ] 6.2 全程零写文件断言。〔R5〕
- [ ] 6.3 测试：多类差异并存 → 四类分节齐 / 运行后 `git status` 无变更（纯读）。〔R5〕

## 7. SKILL.md 集成 + 单一源收敛

- [ ] 7.1 改 `sdflow-maintain/SKILL.md` 步骤 1-3：prose 手做改为「调 `maintain_scan.py` 出只读差异报告」；保留步骤 4（模型判断是否修复 INDEX）步骤 5（提示 retro）。〔D1〕
- [ ] 7.2 SKILL.md 陈旧遮蔽 prose 改为「判据 canonical=`init.py:RULE_MARKERS`，maintain_scan 副本经一致性守卫机验」，删清单复述（闭 T17）。〔D4 grill A2〕
- [ ] 7.3 更新 CLAUDE.md「带脚本+测试的 skill 仅这几个」名单加入 `sdflow-maintain`（数据类化后一致性）。

## 8. 验收

- [ ] 8.1 `pytest sdflow-maintain/tests/` 全绿；坏输入负例确认非零退出。〔R1-R5〕
- [ ] 8.2 dogfood：在本仓根跑 `python3 sdflow-maintain/scripts/maintain_scan.py --root .`，人核报告与实际一致，`git status` 无变更。〔R5〕

### 测试覆盖图（TG-18）

| code path | 测试类型 | 用例 |
|---|---|---|
| set-diff（fs↔INDEX） | 单元·正例 | 2.4（新增/已删/一致三态） |
| CLAUDE.md 过时引用 | 单元·正例 | 3.2 |
| 陈旧遮蔽判据 | 单元·正例 | 4.3 |
| 坏输入 fail-closed | 单元·负例 | 5.4（INDEX 缺失/畸形/目录缺失 → 非零） |
| 只读不变量 | 单元·不变量 | 6.3（git status 无变更） |
| 端到端 | dogfood | 8.2（本仓真跑） |
