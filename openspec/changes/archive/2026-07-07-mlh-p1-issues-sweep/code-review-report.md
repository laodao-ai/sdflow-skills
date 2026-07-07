## code-review 报告 — mlh-p1-issues-sweep

### 命中范围
- **栈**：Python 数据类脚本（`sdflow-issues/scripts/issues.py` `cmd_sweep` + `tests/test_issues.py` TestSweep + `sdflow-done/SKILL.md` / `sdflow-issues/SKILL.md`）。清单 CR-01~09 + backend domain。
- **镜**：领域(backend) · 对抗×2(错误路径 · 并发/资源/边界) · 历史(blame) · code outside-voice(code-voice, codex 跨模型)。broad = Step1 gstack/review 原生。
- **HR-TG**：`hit="none"`（行为对齐既有幂等原语、可逆、无新增数据损坏面）。
- **Step1 gstack/review**：scope-drift 无（改动严格=plan scope）；完成度缺口 1（done SKILL 设计原则汇总段旧措辞，已修 F7）。

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="sweep 包装既有幂等原语,可逆,无新增数据损坏/安全面" -->

### Findings（置信 ≥80，全部已自动修 [impl-review-fix]）

| # | 严重度 | 问题 | 命中镜 | 证据 | 处置 |
|---|---|---|---|---|---|
| F1 | 中/高 | sweep 成功路径吞掉 scan 的 `problems` 字段 + reindex 的 stderr（problems 静默蒸发，重蹈 CR-4/FIX-4 已修类）| **codex+历史+对抗B（三源）** | issues.py:913(scan 忽略 problems) / :936-941(reindex 成功丢 stderr) | ✅ 已修：scan problems 非空回显 stderr（带 pool）+ reindex 成功路径透传 stderr；不改默认 exit（`--strict` enforcement = T2.5 defer）|
| F2 | 中 | 0 命中仍无条件 `batch add` → 0 成员僵尸 PLANNED 批次（reindex vacuous-truth 永不判 DONE，逐 change 累积）| 对抗B | issues.py:928-934(无 tagged 判断) + :623-625(0成员排除) | ✅ 已修：`if not tagged: return`（仅命中才 batch add/reindex）+ `test_sweep_zero_items` |
| F3 | Important | 「原子」措辞矛盾——help + SKILL 标题说「原子」，语义是「非原子」（跨 3 文件自相矛盾，误导调用方以为失败即回滚）| 领域 | issues.py help / done:123 / issues-SKILL:23/101/109 | ✅ 已修：全部改「一键封装/非原子/fail-closed/重跑收敛」，`atomic_write` 真原子写未动 |
| F4 | Important | scan + batch add 两条 fail-closed 分支缺测（4 步只测了 triage+reindex）| 领域+对抗A | test_issues.py TestSweep | ✅ 已修：补 `test_sweep_scan_fail_closed` + `test_sweep_batch_add_fail_closed` |
| F5 | 中 | raw `--change " chg"` 首尾空白被静默 strip 成别的 change（文档承诺含空白即拒）| codex | issues.py:895(strip 前无 raw 校验) | ✅ 已修：`raw != raw.strip()` 即 `_die` + `test_sweep_rejects_whitespace_change` |
| F6 | Minor | `test_sweep_reindex_fail_closed` fake stderr 含字面 "reindex" → 断言巧合过关，判别力弱 | 领域 | test_issues.py:1648 | ✅ 已修：fake stderr 改 "boom"，断言代码自身步标注 |
| F7 | 完成度 | done SKILL 设计原则汇总段(:287)仍描述旧手写 4 步循环 | Step1 gstack | sdflow-done/SKILL.md:287 | ✅ 已修：同步为 sweep 一键调用 |

### 已裁掉 / 既有注记（反静默压制，可审计，不静默丢）
- **[对抗A 4 角度全 refuted]** json.loads 解析安全（scan --json 纯 JSON）/ monkeypatch 元素级精确匹配（测试有效）/ batch add skip warning 不误判（只查 returncode）/ AND 语义 + root 空格 + 重跑收敛链 均核实成立——非真爆点，不计。
- **[对抗B/对抗A 低置信·既有非本 change 引入]** subprocess `text=True` 未显式 `encoding="utf-8"`（非 UTF-8 locale 下含中文字段可能 UnicodeDecodeError）——既有模式（`repo_root`/`_scan_pool`/`read_pool` 同款），触发窄，**一行带过留痕，不计本 change**（可另记 todolist 统一改）。
- **[对抗A 低置信·既有]** `SKILLS_ROOT` sibling 布局假设破裂 → FileNotFoundError 不经 _die——既有共享路径，非 sweep 新增，不计。
- **[历史镜]** sweep spawn-heavy（4+N 子进程）与 T66「subprocess 计数放大」同主题，但是 D4「逐项精确报失败点位」的**刻意取舍**，非缺陷——随 T66 记注即可。

### 修复 / defer 台账
- **自动修 7 项 [impl-review-fix]**（F1-F7，全部当场修 + 测试，commit 见 checkpoint）；新增测试 4 个（zero_items / scan_fail_closed / batch_add_fail_closed / rejects_whitespace_change），全套件 **102 passed**。
- **defer 0 项**（无 genuinely 拿不准的；既有非本 change 项一行带过留痕，未新建 buglist/todolist）。
- 无 ≥2 方案需 T10 复核（F1 的「透传 vs --strict」有客观判据：spec fail-closed 仅要求「子步非零退出」，problems 不触发非零→本次做「不吞可见」的最小反静默修，更强 `--strict` enforcement 明确归 roadmap T2.5，非本 change scope）。

### 度量锚（lens-metric，metrics.enabled=true）
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="none" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="2" sev="致0/高2/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="none" findings="5" 采纳="3" 裁掉="1" defer="1" 独立="1" sev="致0/高1/中2/低2" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="none" findings="2" 采纳="1" 裁掉="1" defer="0" 独立="0" sev="致0/高0/中1/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="code-voice" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="1" sev="致0/高1/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="claude" site="none" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中0/低1" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="ok" findings="2" truncated="false" -->

### 结论
5 源冷审（codex + 领域 + 对抗×2 + 历史）在实现上抓出 7 项真问题（**F1 problems 吞噬三源命中最关键**——反静默红线；F2 僵尸批次；措辞矛盾 + 测试缺口 + 首尾空白），全部当场自动修 [impl-review-fix] + 补 4 测试，102 passed。核心实现逻辑（4 步 fail-closed returncode、参数透传、守卫时序、幂等/收敛链）经多镜核对无误。

☑ **建议进 /sdflow-done**（verify → hand-off → archive → commit → merge）。

<!-- ship-gate: code-review=pass -->
