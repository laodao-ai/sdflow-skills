# harden-sdflow-spec-followups 交接

## ✅ 完成了什么

- FF-0 收敛为完整直接 literal grammar 才进入 payload `cwd` 三分支；其余非直接形态统一输出无权限决定的 `command-unverifiable` 审计。锚：`sdflow-init/assets/hooks/ff0-branch-guard.py:85-106,212-230,249-279`；`test_direct_literal_variants_enter_the_protected_branch_guard`、`test_non_direct_forms_emit_one_unverifiable_audit`。
- `sdflow-spec` 常驻入口已薄化到 16,972 Unicode 字符，同时保留三相位、终审、strict validate、两个 checkpoint 和出口序列；三类细节改为条件加载 reference。锚：`sdflow-spec/SKILL.md:157-180,450-465`；`test_entry_is_within_unicode_character_budget`、`test_resident_contract_tokens_have_substantive_semantics`。
- SA-01/06/15/16 与 FF-0 已同步主规格和逐票台账；T132 保持 OPEN、T239 保持 PROPOSED。锚：`hack/tests/test_harden_sdflow_spec_followup_closure.py:78-308`；focused `496 passed`。
- 本机 dogfood、全局 hook、Claude/Codex skill、workflow 和 settings 注册已刷新并机械比对一致。终门全量：`2847 passed, 11 skipped, 3 xfailed`；详见 `verify-report.md`。
- 代码审修复了归档后闭合测试的 live-path 硬编码；锚：`hack/tests/test_harden_sdflow_spec_followup_closure.py:17-55`、`test_change_root_resolver_survives_archive`。

## ⏳ 未完成 / 延后

- 核心缺口：无。
- Minor `T243`：reference 路由测试把非空链接标签格式收得过窄，不缺目标能力、不阻断归档；已由 issues sweep 归入批次 `harden-sdflow-spec-followups`，见 `openspec/issues/batches.md` 与 `openspec/issues/INDEX.md`。
- T132 的未来自动 gate 与 T239 的下游 rollout 明确不在本 change 范围，状态维持 OPEN / PROPOSED；本 change 只订正其输入契约和台账语义。
- 本轮没有被延后的多方案拍板项。

## ▶ 下一阶段建议

- T243 可在下一次触碰 resident-contract 测试时顺手处理，无需单独扩大为复杂机制。
- T132 与 T239 继续按各自独立 change 推进，不与 T243 混成一个清理批。
- Roadmap 回填助手 exit 3：`NO_ASSOCIATION`。本 change 未声明 roadmap 关联且名称前缀不匹配，因此没有回填草稿，也无需人工回填。
