# hand-off — mlh-p5-gate-frontmatter

> 机械层固化阶段 5（Leg2 去字符串化家族①）：ship-gate 状态锚 report-body inline HTML 注释 → report YAML frontmatter。
> 收尾于 2026-07-08。verify PASS，已归档合并。

## ✅ 完成了什么（每条附机验锚，非搬运 verify）

- **手写 stdlib frontmatter 解析核心** `parse_ship_gate_frontmatter(text)→(state,error)`：只认文件首块（去 BOM/CRLF/splitlines）、顶层 `ship-gate:` 列 0、一层标量枚举校验、重复键计数、坏输入分类。零 import yaml（`test_no_import_yaml` ast 断言 + 源码 grep）。commit 7100e03。
- **live 4 类读点全 dual-read→退役为 frontmatter-only**（D1 致命范围）：design/verify 早检+终门/code-review/peek 五站点统一 `live_ship_gate_state`；`decide()` 内 anchors_in/pick_exclusive 调用数 = 0（grep 证）。commit 209341b（dual-read）+ 66da7ca（退役）。
- **归档 dual-read 永久保留**（F2）：`archived_verify_state` frontmatter 优先→absent 回退 inline `_line_scoped_hits`，坏→fail-safe none，Q4 不交叉扫。commit 4f6b53d。
- **三 producer SKILL 迁 frontmatter 写侧**（spec-review 拍板/done verify/code-review）：头部 prepend、列 0 可解析、下划线字段名。`test_producer_frontmatter_parseable`（真从 SKILL.md 抽取喂 parser）。commit a836b90 + fix e01e28f。
- **契约测试盘面迁移**：21 处 live fixture→frontmatter，归档 fixture 留 inline，正文免疫测试，anchor_set 熔断迁 frozenset 状态集合。commit 8cb50d7 + 66da7ca。
- **自身报告迁 frontmatter + dogfood 闭环**：gate 读出本 change 自身 code_review=pass / design_approved=true 推进，不 REFUSE on itself（端到端验证迁移）。commit 66da7ca。
- **冷主审 5 组自动修**（commit 15351f0，主 session 复现 11 断言闭合）：嵌套字段假过门(fail-OPEN)/坏标量回退(fail-safe 缺口)/YAML 注释/tab 顶层键/label+死代码注释。
- 全仓回归 672 passed（sdflow-ship 154）。roadmap F6 实测归档锚 85 文件/153 锚行订正。commit 45b0c41。

## ⏳ 未完成 / 延后（批次 `mlh-p5-gate-frontmatter`，见 openspec/issues/batches.md + INDEX.md）

- **T74**（代码质量）：ship_gate parser 裸 `---` 首行（markdown HR 无闭合）误判 unterminated→live UNKNOWN(6)，把干净无锚报告误崩。方向安全（当前语料不触发，报告均以 `#` 开头），未来鲁棒性：首行 `---` 无闭合可判 absent 而非 bad。
- **T75**（代码质量）：彻底清理 live inline 死代码——`anchors_in`/`pick_exclusive`/`ANCHOR_DESIGN`/`ANCHOR_CR_PASS`/`ANCHOR_CR_BLOCKED` 已成 test-referenced 孤儿（Task6 只从 decide() 摘调用未删本体）；`ANCHOR_VERIFY_PASS`/`FAIL` 仍被 archived_verify_state 真用**勿删**。另开 cleanup change 删死函数 + 对应测试。
- **已知不覆盖（登记于 ship_gate.py 头注释，非缺口·有意权衡）**：① A1 多块 stale-first-block——D2「只认首块」为自指免疫（本仓报告正文讨论 ship-gate frontmatter 含 body 示例块）有意牺牲全文冲突检测，MUST NOT 改「第二块→fail」（会重开自指陷阱）；② 引号值 `verify: "PASS"`→out-of-domain（enum 严格）；③ 归档 git-show 无显式 encoding（pre-existing subprocess 惯例）。均配断言测试钉死意图。

## ▶ 下一阶段建议

- **Leg2 家族② 待规划**：roadmap mechanical-layer-hardening 若有家族②（其余去字符串化目标）→ 下一 change。查 roadmap.md 阶段 6+。
- **T75 死代码清理优先级中**：可并入下一个碰 ship_gate.py 的 change 顺手清（删函数 + test_gate_anchor_scope 对应用例），或独立小 cleanup change。T74 低（robustness 边角，方向安全）。
- **cross-model 价值信号**：本轮 hr-tg codex 独立挖出 2 个真 bug（per-task 冷审 + 设计审均漏）——HR-TG cross-model 层 load-bearing，勿优化掉；lens-metric 锚已落，跨 change 由 /sdflow-retro 聚合复评。
