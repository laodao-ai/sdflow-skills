---
ship-gate:
  code_review: pass
---
## code-review 报告 — harden-hr-tg-anchor-consistency

### 命中范围
栈：纯 Python stdlib 工具（无 go/embedded/frontend 领域清单命中 → 领域镜退 base CR-01~09）。diff base = merge-base(main,HEAD) = `2d3e2a3`（全分支）。trivial_shape = **NOT_EXEMPT**（有逻辑面：两工具 + config）→ 照常 fan-out。命中 TG：TG-18/19/22/23（∩ HR-TG = ∅）。
镜：Step1 广审（simulated——gstack/review 非本环境可用 skill，主 session 原生广审、显式标注非伪装）+ 领域镜(base) + 对抗×2 + 历史×1 + codex outside-voice(code-voice)。

<!-- sdflow:step1-broad-review v1 mode="simulated" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-18,TG-19,TG-22,TG-23" evidence="命中 TG-18(测试)/19(多需求)/22(假设)/23(≥2方案ADR)，∩HR-TG{04,06,07,08,09,16,17,26}=∅；纯 stdlib 校验器加固无运行期爆炸/数据损坏/安全泄漏面，无需领域 cross-model" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="none" findings="4" truncated="false" -->

### Findings（置信 ≥80）——**全为 parsing 严格性机械化留洞，同片一致性面，全 fold 修**

冷层承重墙再实证：本冷全分支层揪出 **7 条真 finding**（8 任务的每任务冷审均漏——per-task scope 盯不住跨切片的 parsing 面洞），全 CONFIRMED、全采纳、全 fold（`[impl-review-fix]` commit `b9d229e`，235 passed）。目标态基准：现状 catalog 无触发形态**不是**跳过理由，零妥协 fail-closed 是本 change 的目标。

| ID | 严重 | 镜 | 问题 | 证据 file:line | 处置 |
|---|---|---|---|---|---|
| F-A | 高 | codex(独立) | `load_hr_tg_subset` 成员行 `> 成员：` 仍宽松 `_TG_TOKEN_RE.findall`，`TG-04x`→`TG-04`（§1.2 成员严格未落地，与全集表行 fullmatch 不一致） | hr_tg_intersect.py:49 | 已修·剥 `**`+逐 token fullmatch 拒畸形 fail-closed[impl-review-fix] |
| F-B | 高 | 对抗B(独立) | `_H3_SECTION_RE` 子串+`next()`取首→更早的含"触发词目录"字样 level-2 标题**劫持段边界**（fail-open，全集污染无信号）；两侧共享，F3 golden 结构性失明 | hr_tg_intersect.py:20,71 · anchor_lint.py:190,238 | 已修·收集全部匹配标题，恰 1 个才继续，0/≥2→EmitError fail-closed[impl-review-fix] |
| F-C | 中 | 对抗B(独立) | catalog 解析非 fence-aware（`check_hr_tg` 却是），段内 ``` 代码块示例表行 `\| TG-88 \|` 被当真成员/全集 | hr_tg_intersect.py:load_all_tg_set · anchor_lint.py:load_* | 已修·两侧 catalog 文本先过 fence 剔除再扫[impl-review-fix] |
| F-D | 高 | codex(独立) | F2「整行严格解析」只拒重复键，**未拒未闭合注释/未消费残留**（delta spec:27 M-parse 明令）；`<!-- …hit="none" declared="" trailing`（无 `-->`）零违规 | anchor_lint.py:92,284 | 已修·`_HR_TG_ANCHOR_FULL_RE` 整行边界匹配拒未闭合/残留→violation[impl-review-fix] |
| F-E | 中 | codex(独立) | lint 对 declared/hit `sorted(set())` 后比，**未验 numeric 同序/重复元素**（spec:29 M2「逐元素一致·同一 numeric 序」）；`hit="TG-16,TG-04"` 乱序、`hit="TG-04,TG-04"` 重复均过 | anchor_lint.py:317 | 已修·`_check_order_and_dup` 比原始序列拒乱序/重复元素（S1 未破）[impl-review-fix] |
| F-F | 中 | 领域(独立) | 单 try/except 吞掉——`declared="…TG-77(全集外)" hit="…,,…(畸形)"` 只报 malformed，declared 的 tg-not-in-catalog 被吞（F9 collect-not-raise 非真逐项） | anchor_lint.py:294(check_hr_tg) | 已修·declared/hit 各独立 try/except，一侧畸形不吞另一侧 violation[impl-review-fix] |
| F-G | 低 | codex(独立) | `docs/workflow-skills/sdflow-spec-review.md:52,84` 描述性表格单元仅 `--layer spec-review`，操作 now 需 `--trigger-catalog`（描述失准） | sdflow-spec-review.md:52,84 | 已修·补 `--trigger-catalog` 描述（+code-review.md 同步）[impl-review-fix] |

顺带清 `load_all_tg_set` 一处永真死代码（`_TG_STRICT_RE` 对 `_TABLE_TG_RE` 捕获组，Task2 审留的 Minor）[impl-review-fix]。

### 已裁掉（反静默压制，可审计）
- **无裁掉项**——7 条 reviewer findings 全 CONFIRMED（含实测复现）、全采纳。
- **对抗镜A（错误路径角度）** findings=0：F9/F7/必需参数/M2 边界/fence-aware 五面经 11 组恶意 CLI 模糊测试 + 真实 catalog 实跑，**未找到爆点**（负向核验，非 finding）——但对抗B 从**不同角度**（坏输入穿透）抓到 F-B/F-C，印证多对抗镜分角度的价值。
- **历史镜** findings=0：F1（declared="none"→""）spec bug 正确吸收、F2 跨消费者分歧消除、adr/0018 诚实边界未破，历史无重蹈（负向核验）。
- **codex4 TENSION 裁决**（Task7 审 vs codex）：核实 `sdflow-spec-review.md:52/84` 是**摘要表格描述单元**（非用户复制的可执行命令）——Task7「无完整调用串」属实；但 codex 有理（描述后半失准）→ 按 F12「防文档失真」低危 fold（补描述、不推翻 Task7）。两视角均登记，非静默采纳一方。

### 修复 / defer 台账
- **自动修 7 项**（F-A~F-G）+ 死代码清理 1 处，全 `[impl-review-fix]` commit `b9d229e`；**defer 0**。
- **无 ≥2 方案 T10 复核**（7 条均有客观判据：spec 明令 / 实测复现 / fail-closed 目标态，修法确定，无需对抗镜复核推荐）。
- **dogfood 回归核验**（主 session 亲验，防 fixture 漏真实数据回归）：① 真实 trigger-catalog 恰 1 个 `## 三、触发词目录` → F-B fail-closed 前提成立无误伤；② hr_tg_intersect 真实 catalog 收紧后仍 `hit:[TG-04,TG-16]` exit0；③ anchor_lint 对本 change 真实 spec-review-report.md → **CLEAN** exit0（收紧后真实锚不误违规）；④ S1 负例 `test_m2_consistent_but_wrong_still_passes` + F3 golden 三断言线全绿；⑤ 下游副本 `openspec/workflow/tools/` 两文件 diff 空。

### 度量锚（lens-metric，config metrics.enabled=true）
<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="—" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="2" sev="致0/高1/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="code-voice" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="4" sev="致0/高2/中1/低1" -->

> 冷层承重实证：7 条全为热层（8 任务每任务冷审）**漏的跨切片 parsing 面洞**——per-task scope 各审各任务、盯不住"成员行/段边界/fence/锚边界/序/错误收集"这条贯穿两文件的一致性面。outside-voice(codex 跨模型)独家 4 条、对抗B(坏输入角度)独家 2 条、领域(base 清单)独家 1 条，无一由前序每任务审抓出。印证 sdflow-code-review = 每次全跑的独立冷主审（非"高风险才跑的边际抽查"），且多对抗镜分角度（A 错误路径 vs B 坏输入穿透）互补。

### 结论
- ☑ **建议进 /sdflow-done**（verify → hand-off → archive → commit → merge）：7 条冷层 finding 全 fold 修（`[impl-review-fix]` b9d229e）、235 passed、dogfood 真实数据无回归、S1/F3 绿、下游副本同步。
- ☑ defer 残差 = **0**（无入 buglist/todolist）。
- 机判锚见头部 frontmatter `ship-gate.code_review: pass`。
