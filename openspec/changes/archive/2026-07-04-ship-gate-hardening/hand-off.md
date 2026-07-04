# hand-off.md — ship-gate-hardening

> 阶段三收尾交接（verify 之后 / archive 之前）。异步人类再入口 + 下个 change 种子。

## ✅ 完成了什么（每条附机验锚点，已复核锚点存在性）

`ship_gate.py` 四缺陷 + D3 硬化 bundle 全落实，65 ship 测试 / 328 仓级全绿：

- **B1 窗口闭区间**（design D1）：`done_task_ids` 追加 `git log -1 --format=%s <sha>` 解析 sha 自身（窗口 `[sha,HEAD]`）→ plan 与 task1 同 commit 不漏数。锚：`test_plan_task1_same_commit_counts`。
- **B4 完成判据集合归属**（design D5 · 设计门 Q1 纳入）：`plan_task_ids` + `plan_ids ⊆ done_ids` 判齐（非基数）→ 计划外 task9 不顶替缺失 task2 的假✅。锚：`test_offplan_task_no_false_complete`。
- **B2 精确式豁免**（design D2）：`is_stale` design 域分帧遍历 + 精确式 `== "checkpoint(impl-review)" or startswith("checkpoint(impl-review):")`。锚：`test_impl_review_exempt_bare_and_colon` / `_evil_suffix_stale` / 空 subject / 交错帧 + token 契约 `test_impl_review_exemption_token_bound_to_code_review_step`。
- **B3 归档终态 + D3 硬化 H1-H6**（design D3 · 设计门 Q3 全采纳）：纯 git 域发现（`ls-tree HEAD∪base` + `re.escape` fullmatch）+ 追读 archived verify=PASS tri-state（空壳/冲突→UNKNOWN）+ `base_ref`(refs/heads/) + 移除 branch_state（detached 无关）+ final 路径收紧。锚：`test_gate_terminal.py` ×12。
- **代码审自动修 5 项 [impl-review-fix]**：core.quotePath=false（中文名路径假✅）+ errors=replace（GBK 崩溃）+ archived verify 冲突锚→UNKNOWN + base_ref refs/heads/ + evil-merge 记已知不覆盖。锚：`test_chinese_named_spec_edit_still_stale` / `test_archived_verify_conflict_unknown` / `test_gbk_archived_verify_no_crash`。

## ⏳ 未完成 / 延后

- **批次 `ship-gate-hardening`**（`openspec/issues/batches.md` + `openspec/issues/INDEX.md`，状态 PLANNED，成员 T32/T33/T34 均 PROPOSED）——**pre-existing 局限**，代码审 HR-TG code 镜发现、非本 change 引入：
  - **T32** 完成判据 checkpoint 任务号加 change 命名空间（同分支交错跑两 change 同号污染；窗口下界已部分缓解）
  - **T33** 新鲜度可选纳入工作树 dirty 状态（is_stale 只看 committed 盘面；与「盘面即状态」有张力，需先定性）
  - **T34** 复选框辅通道按 Task 分段绑定（checkboxes_all 全局粒度）
- **B2 取舍（设计门 Q2 维持）**：三声指出 B2 豁免凭 subject 前缀而非改动类型的 soundness 洞（语义级 design.md 改动经 impl-review 豁免会静默 ship）；设计门拍板**维持现取舍**（约定级安全边界 + 已登记窗口，见 `ship_gate.py` 头注释「已知不覆盖」）。若未来出现多个合法尾流写者或需强审计，再升级为改动类型分岔（design D2-b）。
- **Minor**：无核心缺口（verify PASS）。evil-merge、精确同名旧档、伪造 subject 均属已声明「已知不覆盖」的接受项。

## ▶ 下一阶段建议

- 批次 `ship-gate-hardening`（T32/T33/T34）优先级 **P2**——非阻塞、gate 现行为对绝大多数盘面正确；建议在下一个"gate 加固二批"清理 change 里一起清（T32 命名空间是其中最有价值的，能根治跨 change 污染）。T33 需先拍板"gate 要不要看工作树 dirty"（与盘面即状态张力）再动。
- 本 change 是 gate 自身 dogfood 的首个"改 gate 又用 gate 跑阶段三"闭环；下轮真实 change 的 ship 全程人工越权计数是 Success Metric 的活体度量点。
- 无 push（手动控制）；toolkit 源仓需 push 后新会话 `/sdflow-upgrade` 激活。
