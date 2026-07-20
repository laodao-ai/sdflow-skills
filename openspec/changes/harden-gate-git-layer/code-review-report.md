---
ship-gate:
  code_review: pass
---

## code-review 报告 — harden-gate-git-layer

## 锚行区

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->
<!-- sdflow:hr-tg v1 hit="TG-17" declared="TG-17" evidence="ship_gate.py 是 merge 前唯一质量门，本 change 整体换掉其失鲜判定机制（反推锚→录锚、帧枚举→比内容、全阶段→限窗），被保护资产=门判定的有效性" -->
<!-- sdflow:declared-sites v1 declared="code-voice,hr-tg" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="4" truncated="true" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="2" truncated="false" -->

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="code-voice" findings="3" 采纳="1" 裁掉="1" defer="1" 独立="1" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="2" 采纳="1" 裁掉="0" defer="1" 独立="1" sev="致0/高0/中1/低0" -->

## 命中范围

- **栈**：backend·Python（stdlib-only 门禁脚本）。`domains/` 无 Python 专属清单（F13 降级）⇒ 判据 = `code-review-base.md` CR-01~09（语言无关）+ 仓根 `CLAUDE.md` 五条基准 + Fowler smell + DOC-1 + premise-verification。
- **diff base** = `d0b7f3c`（分支点 merge-base origin/main），代码面 13 文件 +2424/−1164；核心 `ship_gate.py` +896。
- **gstack/review（Step1，主 session 原生）**：scope-drift **零漂移**（所有改动在声明 scope 内：change 目录 + sdflow-ship + 三评审 SKILL + todolist + adr/0026 + CONTEXT.md）；完成度 6 票交付、gate 判 6/6，结构完整。
- **fan-out**：1 领域镜（opus 派 sonnet）+ 3 对抗镜（状态/错误路径/测试完整性，sonnet）+ 1 历史镜（haiku）+ 2 跨模型 outside-voice（code-voice / hr-tg → codex）。
- **HR-TG**：命中 TG-17（质量门完整性）。

## Findings（置信 ≥80）· 均已裁决

> **本轮实证冷层承重墙价值**：以下 F1–F4 全部是**跨 ticket 完整性/一致性缺口**——六轮双轴审各自在票内框里看不到，冷层全 diff 整体视角 + 跨模型 voice 抓出。多处独立收敛。

| # | 严重度 | 位置 | 问题 | 命中镜（独立收敛） | 裁决 |
|---|---|---|---|---|---|
| F1 | 中 | `ship_gate.py` 头注释 §104/L65/L22-25/main + `test_anchor_contract.py` 退化测试 | 头注释描述**已删的** `checkpoint(impl-review)` subject 豁免（Task3 换 ls-tree 已删）；契约声明「三报告各自必带 reviewed_sha」对 design 报告实为**窗口内**保证（A-1：plan 全勾后窗口关、锚校验活在 window-gated is_stale 里 ⇒ design 报告可缺锚过门）；main「捕获整个函数体」假注释（B-1：parse_args 在 try 外，SystemExit(2) 逸出）；`test_impl_review_exemption_token_bound` 退化成守 prose | 领域镜 + 历史镜 + 对抗A + 对抗B **四方收敛** | **已修**（注释订正三处 + 删退化测试）`bc748bc` |
| F2 | 中 | `ship_gate.py` code/verify RERUN_STALE emit（:1492/:1523） | ADR-4 要求 design/code/verify 三处 stale 都带 `reviewed_sha`，实际只 design 域带；code/verify 漏带（本地复现 `has reviewed_sha? False`），测试网也没网住 | 对抗镜 B | **已修**（两域补锚 + 测试 + 变异证明，编排层独立复变异 KeyError 双红确认）`bc748bc` |
| F3 | 中 | `ship_gate.py` 报告 read_text（:402 等 3 点） | `read_reviewed_sha`/`live_ship_gate_state` 报告读 `read_text` 不捕 `OSError`，PermissionError/TOCTOU 逸出退出码 1，脱契约集 {0,3,4,5,6}——同 Task2 UnicodeEncodeError 类、Task1 新增代码引入 | 跨模型 voice hr-tg | **已修**（抽 `_read_report_text` 面治 3 点 + 单元&端到端测试，编排层独立变异端到端 PermissionError 逸出确认）`bc748bc` |
| F4 | 中 | `sdflow-code-review/SKILL.md` 第五步 | 两段时序指令自相矛盾：第一条就「写报告」，两段提交在后 ⇒ 报告先落盘被 step1 `git add -A` 卷入「仅源码」修复提交，git status 检查在 step3 太晚 | 跨模型 voice code-voice | **已修**（重排编号步骤、报告写盘明确移到取锚后/report-only 提交前）`bc748bc` |

## 已裁掉 / defer（反静默压制，可审计）

- **V-1 归档终态绕过 reviewed_sha**（code-voice）→ **裁掉**：= design.md 已登记残余「归档终态盲区」（Q1 用户已裁定不做——verify 到 merge 间本无其他动作）。非新洞。
- **H-1 code 域排除整个 openspec/ 含真实工具**（hr-tg，`openspec/workflow/tools/*.py`、`serve.sh`）→ **defer T205**：大半是已登记残余「openspec/workflow 规则漂移不触发陈旧」，H-1 锐化到「可执行工具」；修法（递归比较、仅排除记账路径）非平凡且易重引入本 change 刻意消除的假阳，属独立面。头注释残余条目已锐化。
- **V-3 归档 `.strip()` 规范化前导空行**（code-voice）→ **defer T206（低）**：归档不可变 + 坏 frontmatter fail-safe 到 none + 目标态 producer 一律 prepend 首行。
- **对抗镜 C（测试完整性）无发现** → 强正面：独立 2 变异（design/code stale→fresh 各红 28/6，含 evil-merge/git-mv 等价）证守卫有效，本仓头号假绿形态（只调 helper 不经 is_stale）未复发。

## 修复 / defer 台账

- **自动修 4 项**（F1–F4）`[impl-review-fix]` → `bc748bc`；编排层对 F2/F3（行为改动）**独立复跑精确变异**确认守卫为真（非采信子代理自述）。
- **defer 3 项** → todolist T205（H-1）/ T206（V-3）；V-1 = 已登记残余不新记。
- 无 ≥2 方案需 T10 复核项。

## 结论

☑ **建议进 /sdflow-done**（verify → hand-off → archive → commit → merge）。
☑ defer 残差已入 todolist（T205/T206），hand-off 会引用。

> **人读结论**：冷独立主审全跑（5 镜 + 2 跨模型 voice），抓出 4 条六轮双轴审各自看不见的**跨 ticket 缺口**（F1–F4），全部当场修复并经编排层独立变异复核；2 条残余诚实登记 defer。机判锚见头部 frontmatter `ship-gate.code_review: pass`。
