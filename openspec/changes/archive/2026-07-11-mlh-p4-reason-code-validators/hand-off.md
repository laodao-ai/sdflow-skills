# Hand-off — mlh-p4-reason-code-validators

> 2026-07-11 · 阶段三（sdflow-ship）全自动链收尾。verify PASS（唯一终门，每 ✅ 附机验锚点）。

## ✅ 完成了什么（锚点已复核存在）

三个 reason_code 机械校验器落权威源 `sdflow-init/assets/workflow/tools/` + 回灌下游 `openspec/workflow/tools/`（逐字一致、下游无 tests/），190 passed `-W error` 0 warning：

- **outside_voice_guard.py**（T80/OVG）——六 reason_code 三前置归约（来源>新鲜度>结构），fs-mtime 直比判新鲜度（纯 stdlib 无 subprocess，AST 断言锁定）、排除评审产物自身，坏输入 all-or-nothing fail-closed。锚：`test_outside_voice_guard.py` 六枚举正例 + fail-closed 负例。
- **hr_tg_intersect.py**（T81/HRT）——模型传入 `--tg-set` ∩ HR-TG 子集，HR-TG 从 trigger-catalog 单一源读（非硬编码，`test_single_source_mutability` 证）、`--trigger-catalog` 入参非 `__file__` 推导，输出带「依据模型判定」不 emit 裸 none，单一源损坏 fail-closed。
- **review_disposition_check.py**（T82/RDC）——`## Review 处置` 小节 fence/注释结构感知存在+非空判定（禁裸子串「未处置」），输出 `-DISPOSITION-UNCHECKED` 显式点明逐条未核（信任边界归模型），文件不可读 fail-closed。负例夹具取真实 in-repo task-log。
- **anchor_lint.py check_hr_tg**——认 hr-tg 锚 `declared=` 字段（字段在场校验）。
- **三处 SKILL.md 接入**——sdflow-spec-review 接 OVG+HRT、sdflow-code-review 接 HRT、sdflow-roadmap 接 RDC + 逐条处置信任边界声明；手做 prose 已换调校验器，参数名与 argparse 逐一吻合。

**冷层代码审兑现承重墙价值**：循环内每票双轴审全绿，冷层独立抓出 2 条中危 fence-aware 假绿（各校验器次要解析路径未 fence-aware，主路径已验），当场 [impl-review-fix] 修复（6ef7d45 + 8f455c8，后者修正初版贪婪引入的假阴回归）+ 回归验证。codex 跨模型独家抓出 review_disposition_check 空 fence/未闭合注释假绿（domain/adversarial 未报，lens-metric 独立=1）。

## ⏳ 未完成 / 延后（批次 `mlh-p4-reason-code-validators`，见 openspec/issues/batches.md + INDEX.md）

冷层代码审 defer 的 5 项 hardening（均为改进/加固，非本 change 核心需求缺口）：

| ID | 项 | 严重度 | 备注 |
|---|---|---|---|
| **T137** | config `impl-pipeline: tickets` 翻键 blast radius | 中 | **⚠ 需用户意图裁断**——翻键注释"首个试点(mlh-p4)"误导：mlh-p4 已由 plan marker 自锁，翻键实际使 `scoped-test-per-task` 及所有未来 change 卷入 tickets 管线。仅 pilot→撤回翻键；仓级前向切换→改注释。可逆（config 随时可再翻）。 |
| T136 | anchor_lint 重算 hr-tg 交集堵手改绕过 cross-model | 高（codex）| 需定夺是否扩 anchor_lint 职责（越机械-presence 设计边界）|
| T138 | hr_tg_intersect 严格 CSV 解析（`,,`/宽松成员正则）| 中 | 坏输入静默正规化 |
| T139 | outside_voice_guard 双 step1 锚一致性 | 低 | 静默取首 |
| T140 | anchor_lint declared= 收紧向后兼容 | 低 | 旧格式锚重 lint 会 exit1（无活跃重 lint 路径）|

**裁掉 1 项**（已审计，code-review-report「已裁掉」区）：对抗A 报的 review_disposition_check 单行 `<!-- x --> y -->` 假绿——CommonMark 下尾随可见文本判 ok 正确，非真假绿。

**pilot caveat（tasks.md:51）**：本 change 作首个 tickets 试点跨 3 桶 + 叠 3 first-of-kind，判据①打折 + confounding；SHIPPED 后建议在 pilot 执行记录按 per-ticket 分别归桶（非跨桶整体归）。

**adr/0018（tasks.md:50）**：本 change 是形态首个真 ship + dogfood 验证，adr/0018 状态可考虑 Proposed→Accepted（洞察5）——留人异步确认。

## ▶ 下一阶段建议

- **优先处理 T137**（config blast radius）——merge 后 `impl-pipeline: tickets` 即在 main 全局生效，`scoped-test-per-task` 下次阶段三会走 tickets 管线。若非本意，尽早撤回翻键或改注释澄清。
- **T136（高）** 可与 T140 合并成一个 anchor_lint hardening cleanup change（都动 check_hr_tg / hr-tg 锚 schema）。
- **T138/T139** 属校验器输入健壮性，可并入同一 cleanup change 或延后。
- **roadmap 回填（手动）**：本 change 属 **mechanical-layer-hardening** roadmap 的 p4 阶段（reason_code 三校验器），但 change 未声明 roadmap 关联标记、名前缀 `mlh` 与 roadmap 目录名不匹配 → `roadmap_writeback_draft.py` 退现状(exit3)未产草稿。请手动到 `openspec/roadmaps/mechanical-layer-hardening/` 回填本阶段完成态 + 价值叙述。
