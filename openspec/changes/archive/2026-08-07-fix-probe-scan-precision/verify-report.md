---
ship-gate:
  verify: PASS
  reviewed_sha: 8da461a741df638024db2fd8ce05d494de86d0d0
---

# Verify Report: fix-probe-scan-precision

**结论：PASS**

全仓 pytest 2476 passed / 10 skipped（既有跳过），`openspec validate` 绿。
四条反向锚均在场（2.3 副本忽略 / 2.5 sane 扩面 / 4.4 文案双断言 / 5.4 腿退役）。
概念词表 sweep 归零词全清、逐条判词均已处置或登记豁免。

## 逐需求核对表

| 需求/任务 | 代码出处 | 状态 |
|---|---|---|
| 1.1 删除 code-review SKILL skew 探测段 | `sdflow-code-review/SKILL.md` grep 命中 = 1（仅锚行自检合法引用） | PASS |
| 1.2 删除 spec-review SKILL skew 探测段 | `sdflow-spec-review/SKILL.md` grep 命中 = 1（同上） | PASS |
| 1.3 悬空指代清理 | 两 SKILL 档位解析步不再含「skew 探测」字样（grep 验证） | PASS |
| 1.4 退出码 2 降级分支保留 | 两 SKILL 仍含退出码 2 → 显式降级分支（`sdflow-code-review/SKILL.md:197` / `sdflow-spec-review/SKILL.md:172`） | PASS |
| 1.5 验收 grep 各文件 1 命中 | `grep -c` 各 = 1 | PASS |
| 1.6 单链表述 + parity 断言改写 | `hack/tests/test_async_branch_parity.py:461` 断言 `sdflow-init update not in seg`；两 SKILL 不含「两条分发链」 | PASS |
| 2.1 resolver 删步①（local pin） | `resolve-workflow.sh` 无 `LOCAL`/`has_wf`/`has_spec`/`local-pin`；头部注释「两步链」 | PASS |
| 2.2 退出码集/入参契约不变 | 头部契约注释保留 exit 0/2/64、`--root`/`--explain`/`SDFLOW_HOME` | PASS |
| 2.3 反向锚：仓内副本仍解析到 canonical | `test_resolve_workflow.py:106` `test_full_local_rule_copy_still_resolves_to_global_canonical` | PASS |
| 2.4 SDFLOW_HOME 测试隔离 | `test_resolve_workflow.py` 多用例覆盖 SDFLOW_HOME 路径 | PASS |
| 2.5 sane() 扩面 + 反向锚 | `test_resolve_workflow.py:132/141/151/160` 四个反向锚（缺 tools/空 tools/缺 contract/空 contract → exit 2） | PASS |
| 2.6 存量测试处置 | `test_init_contract_sync.py` 已删；`test_marker_consistency.py` 中 `test_resolve_workflow_bash_markers_match_python` 已删；`test_resolve_models.py` fixture 改用假 SDFLOW_HOME | PASS |
| 3.1 copy_bundle 只铺 GUIDE + makedirs | `init.py:228` `os.makedirs(dst, exist_ok=True)` + `:234-236` 只拷 GUIDE；无 `copytree` tools 调用 | PASS |
| 3.2 删 full/ignore_tools_tests/LOCAL_TOOL_CACHES | `init.py` 无 `ignore_tools_tests`/`LOCAL_TOOL_CACHES`/`full=` 参数 | PASS |
| 3.3 --dev 退役 tombstone | `init.py:1165-1170` 识别 `--dev` → fail-loud 提示 | PASS |
| 3.4 测试：只有 GUIDE + fresh init 不抛 | `test_init.py:107` `test_fresh_init_does_not_raise` | PASS |
| 3.5 存量测试处置 | `test_init_contract_sync.py` 已删；`test_init.py` 中 `TestBundleToolsOnly` 等已改写/删除 | PASS |
| 4.1 告警判据扩员 + 文案改写 | `init.py:305-307` `DEAD_RESIDUAL_MARKERS` 含 tools/contract | PASS |
| 4.2 checkpoint 孤儿告警 pin 措辞清理 | git diff 确认 pin 措辞已清理 | PASS |
| 4.3 maintain 兜底扫描同步 | `test_maintain_scan.py:220+` 反向锚 tools-only 残留 → 报死件 | PASS |
| 4.4 文案双断言 | `test_init.py:546-547` 不含 `显式 pin`/`遮蔽全局`；`test_maintain_scan.py:243-244` 同 | PASS |
| 5.1 ship_gate tools_spec 腿删除 | `ship_gate.py:953` 仅余退役注释，无比较代码 | PASS |
| 5.2 退役注释按仓型分写 | `ship_gate.py:954-959` toolkit 源仓/消费仓分开说明 | PASS |
| 5.3 正向锚：toolkit 源仓 tools 改 → stale | `test_gate_tools_leg_retirement.py` 含正向测试 | PASS |
| 5.4 反向锚：消费仓镜像改 → fresh | `test_gate_tools_leg_retirement.py:47` 反向锚 | PASS |
| 6.1 删 7 文件 | `openspec/workflow/` 只剩 `WORKFLOW-GUIDE.md`；`tools/` 目录已删 | PASS |
| 6.2 yq TARGETS 删 anchor_lint 镜像条目 | `test_yq_wrapper_consistency.py` 无 `anchor_lint` 镜像条目 | PASS |
| 6.3 encoding hygiene 排除分支删 | `check_encoding_hygiene.py` 无 `openspec/workflow/tools` 排除 | PASS |
| 6.4 托管块权威源订正 + update 刷新 | `claude-section.md` 无「规则副本则用之」；`CLAUDE.md` 托管块已刷新（grep 验证） | PASS |
| 6.5 CLAUDE.md 非托管区订正 | 测试三层第 2 层改为 SDFLOW_HOME；pin 逃生口移除；回滚节补三步 | PASS |
| 6.6 修法文案统一 | `lens_metric_emit.py:104`/`resolve-models.sh:74`/`sdflow-upgrade/SKILL.md` 均「回运行 checkout 跑 bash setup.sh」 | PASS |
| 6.7 docs 面 sweep | `docs/workflow-map.md`/`02-module-reference.md`/`sdflow-spec-review.md` 均无归零词 | PASS |
| 6.8 ADR 注记 + 0038 删除 + 0039 新落 | 0003/0005/0019/0036 均有 0039 指针注记；0038 已删；0039 含 6 个主要章节 | PASS |
| 6.9 CONTEXT.md skew 定义 | `CONTEXT.md:300-308` skew 术语定义在场 | PASS |
| 6.10 GUIDE 相对链接降级 | `WORKFLOW-GUIDE.md` 无相对链接（`./ff-generation`/`./reference`/`./workflow-history` 全清） | PASS |
| 6.11 记 todo | T271-T274 四条新建 | PASS |
| 7.1 全仓 pytest 绿 + 4 反向锚 | 2476 passed / 10 skipped；4 反向锚逐条确认在场 | PASS |
| 7.2 openspec validate 绿 | `Change 'fix-probe-scan-precision' is valid` | PASS |
| 7.6 概念词表 sweep | 归零词（local-pin/两条分发链/显式 pin/pin 遮蔽）全清或仅在豁免区（adr/0039/change 目录/决策纪要/历史 ADR 注记/负断言测试/已关 issue）；逐条判词（规则副本/sdflow-init update/openspec/workflow/tools）均为已处置上下文（描述新状态/退役注释/测试 docstring/已关 issue） | PASS |

## 缺口清单

无核心功能缺口。

**Minor 注记（不影响 PASS）**：

1. `openspec/specs/` 下的主 spec 文件（非 delta）仍含旧术语（`显式 pin`/`pin 遮蔽`），属预期——delta-spec 同步到主 spec 在 archive 阶段执行，当前分支尚未归档。
2. `openspec/roadmaps/archive/` 和 `openspec/issues/closed/` 中的历史引用保留原样，符合「不重写历史」原则。
3. `docs/design-methodology.md:61` 含「两条分发链」但仅在表格中引用本 change 的 design Risks 作为该词的展开来源，属于面向本 change 的指路，非遗留概念。
4. `hack/tests/test_async_branch_parity.py:457` 的「两条分发链」在测试 docstring 中作为变更说明（解释断言为什么改），非 SKILL 正文。
5. Tasks 7.3-7.5（三态真跑/全链路实跑/存量 pin 仓）为人工验证项，本次 verify 未覆盖（诚实边界：无法在自动 verify 中替代人工实跑）。
