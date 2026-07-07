---
ship-gate:
  code_review: pass
---
## code-review 报告 — mlh-p5-gate-frontmatter

> 阶段三 whole-branch 独立冷主审。diff base `c0afc30`..`15351f0`（含 crfix）。分支 feat/mlh-p5-gate-frontmatter。
> **冷主审 load-bearing 第三次兑现**：per-task 审 + 设计审均漏的 2 个真解析 bug（嵌套字段假过门 / 坏标量回退）由 hr-tg codex 独家挖出，主 session 复现确认后修复。

### 命中范围

- 栈：Python 门禁脚本（ship_gate.py 手写 stdlib frontmatter 解析）+ 三 producer SKILL.md + pytest
- 清单：CR-01~09 base（正确性/错误处理/边界/资源/并发/可测/命名/一致性/安全）
- 行为面路径命中：ship_gate.py / SKILL.md → NOT_EXEMPT（trivial_shape），照常 fan-out
- gstack/review（Step1 broad·native）：scope-drift **CLEAN**（26 文件全在迁移意图内：ship_gate.py/tests/3 producer/artifacts/roadmap-sync，无越界）；完成度 **CLEAN**（8 checkpoint tag=7 Task+1 fix 全在史）；D1 半退役复核 decide() 内 0 anchors_in+0 pick_exclusive、archived `_line_scoped_hits` 保留；零 import yaml ✓

<!-- sdflow:step1-broad-review v1 mode="native" -->

- HR-TG 判定：命中 **TG-04（迁移：inline 锚→frontmatter 状态承载）+ TG-08（fail-closed：live 坏→UNKNOWN6/归档坏→none/absent→无锚语义）** → 单开领域专属 cross-model（codex），「找领域镜漏的」

<!-- sdflow:hr-tg v1 hit="TG-04,TG-08" evidence="inline锚迁frontmatter+手写解析器坏输入fail-closed退出码映射,迁移正确性/fail-closed完备性专属复核" -->

### Findings（置信 ≥80）

- [高·fail-OPEN] CR-01 正确性 | ship_gate.py parse_ship_gate_frontmatter | **ship-gate 嵌套字段假过门**：`ship-gate:\n  note:\n    design_approved: true` 被解析为 `{'design_approved': True}` → 假过设计门（parser 只查缩进+field∈FIELD_ENUMS，不管嵌套深度，违背 D2 一层标量 schema）| 置信 95（主 session 复现）| **已修[impl-review-fix]** 15351f0 FIX-1（仅认直接子键，深层嵌套跳过）
- [中高·fail-safe] CR-02 错误处理 | ship_gate.py 顶层键探测 | **坏标量值判 absent**：`ship-gate: []`/`ship-gate: true` 被判 absent（非 bad）→ 归档路径回退 inline，`ship-gate: []`+残留 inline PASS → 假 SHIPPED | 置信 90（复现）| **已修[impl-review-fix]** FIX-2（顶层 ship-gate 带非空标量值→bad-type，live UNKNOWN6/归档 none 不回退）
- [中·过激 fail-closed] CR-02 | ship_gate.py 解析循环 | **不支持 YAML `#` 注释**：块内独占注释行/值行尾注释→整块判 bad-type UNKNOWN，误崩合法报告（本 change 自己的 codex design-voice finding「手写 YAML 未定义 comment」裁决表未覆盖）| 置信 90 | **已修[impl-review-fix]** FIX-3（独占注释行跳过+值尾注释剥离）
- [低·观测性] CR-08 一致性 | ship_gate.py 顶层键探测 | tab 缩进顶层 `ship-gate:`→吞成 absent 而非 tab-indent 类别 | 置信 85 | **已修[impl-review-fix]** FIX-4
- [低·cosmetic] CR-07 命名 | ship_gate.py live_ship_gate_state(cr,"code-review") | label 连字符与字段名下划线不一致（仅错误文案用）+ `_line_scoped_hits` 过期注释称 anchors_in/pick_exclusive live「共用」（实已退役为 test-referenced 孤儿）| 置信 90 | **已修[impl-review-fix]** FIX-5

### 已裁掉（反静默压制，可审计）

- **A1 多块 stale-first-block（adv-A 报 高）→ 裁为 document（T10）**：迁移把冲突检测从全文级降到首块级，若报告顶部残旧 PASS 块+下方新 FAIL 块只读首块。**adv-A 建议的「第二块→fail」被证伪**——会重开 history 镜确认已根治的自指陷阱（本仓报告正文讨论 ship-gate frontmatter、含 body 示例块；D2「只认首块」正为自指免疫）。触发极窄（需畸形双写+违反 producer MUST-overwrite+归档不可变手改）。裁决：**登记「已知不覆盖」+ test_second_frontmatter_block_ignored_by_design 钉死意图**，非 fix。
- **domain-F2 缩进一致性未校验（低）**：schema 单层标量无嵌套歧义，比预期宽容非缺陷，note-only。
- **domain-F3 / fallback-F4 文档卫生（tasks.md checkbox 未勾 / producer 示例排版不一致）**：sdflow-done 会对账 checkbox；排版不一致已有 test_producer_frontmatter_parseable 真抽取兜底，非代码缺陷。
- **A3 = domain-F1（连字符 typo 静默吞）重复命中**：与 FIX-3 注释支持/FIX-1 同域，合并计。
- 引号值 `verify: "PASS"`→out-of-domain（fallback-F1 部分）：有意的 enum 严格匹配，方向安全 → 登记「已知不覆盖」+ test_quoted_value_is_strict 钉死，非放宽。

### 修复 / defer 台账

- **自动修 5 组[impl-review-fix]**（commit 15351f0，主 session 独立复跑 11 项 parser 断言全闭合+零回归）：FIX-1 嵌套字段假过门 / FIX-2 坏标量→bad-type / FIX-3 YAML 注释 / FIX-4 tab 顶层键 / FIX-5 label+死代码注释订正。
- **document 3 条「已知不覆盖」[impl-review-fix]** FIX-6：A1 多块自指免疫权衡 / 引号值严格 / B3 归档 git-show encoding 不对称（pre-existing subprocess 惯例，超本 change scope 不改 subprocess，仅登记）。各配断言测试钉死意图。
- **T10 复核: A1「第二块→fail」方案 | 对抗镜结论 证伪（history 镜佐证会重开自指陷阱）| 理由：系统镜(D2 只认首块为自指免疫 load-bearing，本仓 dogfood 报告正文含 ship-gate 示例块)＞用户镜(误崩合法报告比漏检畸形双写更扰)＞开发镜(document 便宜诚实，fix 加 parser 复杂度+自指风险需另测)**。主次：主=保 D2 自指免疫，次=畸形双写触发窄且经 producer 纪律缓解。
- **defer 2 项 → todolist**：① A2 报告裸 `---` 首行（markdown HR 无闭合）→ 误 UNKNOWN（方向安全，未来鲁棒性）；② 死代码彻底清理（anchors_in/pick_exclusive/ANCHOR_DESIGN/ANCHOR_CR_* test-referenced 孤儿，Task6 有意保留，另开 cleanup 删函数+测试）。
- dogfood：`ship_gate.py --change mlh-p5-gate-frontmatter` → RUN_CODE_REVIEW exit 0，**不 REFUSE on itself**。

### 度量锚（lens-metric）

<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="—" findings="3" 采纳="0" 裁掉="3" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="—" findings="7" 采纳="5" 裁掉="1" defer="1" 独立="3" sev="致0/高0/中2/低3" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="claude-fallback" site="code-voice" findings="4" 采纳="2" 裁掉="1" defer="1" 独立="1" sev="致0/高0/中1/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="hr-tg" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="2" sev="致0/高1/中1/低0" -->

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="claude-fallback" reason_code="exec-error" findings="4" truncated="true" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" runner="codex" reason_code="none" findings="2" truncated="false" -->

> **cross-model 价值**：hr-tg codex 独立=2（高1/中1），独家挖出 2 个真 fail-open/fail-safe bug——per-task 冷审（scoped 单任务 diff）与设计审均漏。code-voice codex exit1(exec-error,非UTF8字节)→claude-fallback 复核印证。

### 结论

- ☑ 建议进 /sdflow-done（verify → hand-off → archive → commit → merge）
- ☑ defer 残差已入 todolist（hand-off 会引用）：A2 裸`---`首行 + 死代码彻底清理

（机判锚在报告**头部** frontmatter `ship-gate.code_review: pass`）
