# hand-off — mlh-p4-maintain-scan

> 收尾交接（verify PASS 之后、archive 之前产出）。异步人类再入口 + 下个 change 种子。
> 日期 2026-07-09。分支 `feat/mlh-p4-maintain-scan`。

## ✅ 完成了什么（锚点已复核存在）

`sdflow-maintain` 由纯 Markdown 编排类升为**数据类**（首个 `scripts/`+`tests/`），三类确定性 set-diff 从模型手做下沉为只读脚本 `maintain_scan.py`（fail-closed 反静默）：

- **R1 specs/rules ↔ INDEX 双向 set-diff**：链接路径 join（`_SPEC_LINK`/`_RULE_LINK`）+ fence-aware 托管块 token 剥离 + 四类判据（①结构行②a条目②b非-spec排除③坏target fail-closed）+ 限表格行防散文误纳 + M8 疑似 spec 误置告警。锚：`maintain_scan.py:parse_index_entries/split_managed_block`，测试 `test_new_unindexed_spec`/`test_managed_block_entries_not_stale`/`test_broken_link_target_fails`/`test_parse_index_entries_prose_link_not_indexed`。
- **R2 CLAUDE.md 过时引用**：改直查 fs 存在性（对齐 spec「已从文件系统删除」）+ 匹配契约排围栏/行内 code/占位符/泛指 + `.git` 精确剪枝（不误跳 `.github` 等）。锚：`scan_claude_refs`/`_iter_claude_files`，测试 `test_claude_ref_deleted_from_fs_and_index_reported`/`test_claude_dotgithub_not_pruned`。
- **R3 workflow bundle 陈旧遮蔽兜底扫描**：RULE_MARKERS + checkpoint 孤儿双分支。锚：`scan_stale_shadow`，测试 `test_stale_shadow_workflow_body`/`test_stale_shadow_checkpoint_orphan`。
- **R-guard 跨脚本一致性守卫**：`RULE_MARKERS == init.RULE_MARKERS`、`token == init.MARK_IDX[0].split()[1]`、加载 hard-fail 非 skip、端到端 fixture 护匹配逻辑。锚：`test_marker_consistency.py`。**闭合 todolist T17**（evidence f4c61b4/6ce74fc，T17 已置 DONE）。
- **R4 坏输入 fail-closed**：INDEX/specs 缺失非零、marker 不配对非零、三处 fence 未闭合非零、0 条合法退出 0、rules 可选空集。锚：`test_index_missing_nonzero`/`test_index_unclosed_fence_fails`/`test_zero_entries_index_is_ok_not_fail`。
- **R5 只读**：字节快照前后逐字节相等 + dogfood git 无变更。锚：`test_readonly_no_file_writes`。
- **SKILL.md 步骤 1-3 改调脚本** + 删陈旧遮蔽清单复述 + 退役「代码路径缺失」校验（proposal Non-Goal）；**分类文档三处订正**（CLAUDE.md 数据类名单 + 两类归属、README）。
- 测试 **38 passed**；本仓 **dogfood rc=0**、retro-report 不误报、只读守住。

## ⏳ 未完成 / 延后（批次 `mlh-p4-maintain-scan`，见 openspec/issues/batches.md + INDEX.md）

冷代码审 defer 1 项 + 前序已知残差，全部归入批次 `mlh-p4-maintain-scan`（sweep tagged T93/T94/T95/T96）：

- **T93**：`resolve-workflow.sh` bash 第 3 份 RULE_MARKERS 内联副本跨语言难同守——一致性守卫只覆盖两份 Python 副本，bash 漂移不被机验。（与已闭合的 T17 语义重叠但属扩展范围）
- **T94**：陈旧遮蔽告警文案第三处跨脚本复述 + checkpoint 孤儿路径——R-guard 不机验文案（文案守卫脆），maintain 抄 init 仅语义等价。
- **T95**：守卫测试可加 `importorskip` 兜底（sdflow-init 目录整体缺席场景更优雅降级；当前 path-assert 直接 fail）。
- **T96**（冷代码审 defer）：`_SPEC_LINK/_RULE_LINK` 正则 `[a-z0-9-]+` 与 scan_fs 目录名零字符集限制不对称——非规范命名（大写/下划线）spec/rule 被删且 INDEX 仍链接时静默漏报「已删未清理」。openspec 强制 kebab 故低概率，彻底修需 scan_fs 也检非规范命名。
- **verify Minor 残差**（不阻断）：散文化破坏型少读 A 不覆盖（H2 选项 A 只关③类，唯一补法 = N 对账，已 grill 否决）。

**无 ≥2 方案被延后的决策**：本 change 所有裁决均有客观判据（spec 文本 / design D2 / mutation 可判），按 T10 case① 自动选/自动修，无对抗镜复核待决项。

## ▶ 下一阶段建议

- **roadmap 回填**：`roadmap_writeback_draft.py` exit=3（未检测到 roadmap 关联标记）。但 change 名前缀 `mlh-p4` 疑属 **mechanical-layer-hardening 阶段4·4.B**（★组 T79）——若确属该 roadmap，请手动在 `openspec/roadmaps/mechanical-layer-hardening/` 回填本阶段完成状态与价值叙述。
- **清理 change 优先级**：T93/T94（跨语言/文案第三份副本同守）可与未来 `resolve-workflow.sh` 相关改动一起清；T95/T96 低优先，遇相关改动顺带。建议不单独为它们开 change（循环固定成本高于收益），并入下一次 sdflow-init/maintain 相关改动即可。
- **MLH 阶段4 剩余**：本 change（4.B ★组）落地后，4.D 小校验器组（4.D.1/2/4）与 ◐ 组（4.A/4.D.3，待 embedded 契约）仍待做——proposal Non-Goal 已声明不在本 change scope。
