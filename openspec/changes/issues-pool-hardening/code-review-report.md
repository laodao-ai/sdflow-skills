## code-review 报告 — issues-pool-hardening

### 命中范围
- **栈**：backend·python（数据类 recorder 脚本）。**清单**：CR-01~09（base）。
- **trivial_shape**：NOT_EXEMPT（recorder logic-line + SKILL.md behavior-path）→ 照常 fan-out。
- **gstack/review Step1（scope-drift + 完成度）**：**无漂移**——diff 只碰 3 recorder `.py` + tests + 3 SKILL.md + 本 change openspec 产物，未碰 `assets/workflow/`、无无关文件；10 SDD 任务全提交、完成度齐。
- **镜**：领域×1 + 对抗×2（guard-bypass / refactor-honesty）+ 历史×1 + code outside-voice(codex)。
- **whole-branch 冷主审兑现 grill-not-skippable/cold-review-load-bearing**：SDD 逐任务审全绿，但冷主审 + codex 抓出 **6 个真 bug**（多经 PoC 复现），全自动修。

### Findings（置信 ≥80，均已自动修 [impl-review-fix]）

| # | 严重 | CR | 问题 | 证据 | 命中镜 | 置信 | 处置 |
|---|---|---|---|---|---|---|---|
| CR-1 | **高** | CR-02/07 | `cmd_set_status` 的 `evidence`/`reason`/`date`/`month` 未挂守卫 → 块注入；**静默变体**：reason 含独立 `---` 行 → `block_ranges()` 截断真实块、`scan` 返回 `problems:[]` 完全绕过自检（引用 markdown/diff 极易触发） | `buglist.py:450+`/`todolist.py:430+`（PoC×2 复现） | 对抗A | 99 | **FIX-1**：evidence/reason/date/month 补 `_reject_cell_unsafe`（拒换行即杀两 PoC） |
| CR-2 | **高** | CR-02 | scan 重复 ID 检测**逐文件**、漏跨文件同 ID（跨日/跨月 `B1`/`T1`）——ID 应全池唯一，跨文件重复正是要报的腐蚀 | `buglist.py:566+`（PoC，2 镜共证） | code-voice + 对抗A | 92 | **FIX-2**：改跨全池 list_files 聚合计数 |
| CR-3 | 中 | CR-02 | `_reject_batch_key_unsafe` 漏防**空字符串 key**（`""==""` .strip() 恒 False）→ header `###  — title` 永不可解析=僵尸条目；`batch add ""`/`rename real ""` 静默腐蚀 | `issues.py:337`（PoC） | 领域 | 92 | **FIX-3**：补拒空/纯空白 key |
| CR-4 | 中 | CR-02/07 | `batch rename` auto-reindex **丢弃 `(items,problems)` 返回值**——reindex 成功但 problems 非空时不吐信号（换入口复现静默蒸发）；失败文案无条件说"INDEX 未刷新"不准 | `issues.py:834+`（PoC） | 领域 + 对抗B | 95 | **FIX-4**：解包 problems + `_echo_problems` 回显（cmd_reindex 共用）；文案改不断言 INDEX 态 |
| CR-5 | 中 | CR-02 | `batch add` 的 `优先级`/`计划` 单行写 batches.md 未拒换行 → 可注入伪造 `### … — …` 批次 header | `issues.py`（codex） | code-voice | 85 | **FIX-5**：优先级/计划 补 `_reject_cell_unsafe` |
| CR-6 | 中 | CR-02 | `cmd_add` 的 `title`（进块头 `## id: title`）/`source` 未挂守卫——**C7 spec-review amendment 未兑现** | `buglist.py`（领域F4） | 领域 | 88 | **FIX-6**：title/source 补守卫（兑现 C7） |

### 已裁掉 / 核验为 clean（反静默压制，可审计）

- **对抗B 大量核验为 clean**：`--strict` 诚实性成立（6 处文档一致，无夸大兑现）· `_reindex_core` 抽取逐行 behavior-preserving 无回归 · 三 recorder 镜像除池 token 外逐字节一致无漂移 · scan arity 无误报（`split_sections` 按位置排除表头/分隔行，真实数据 exit 0 零 problems）· skip-with-warn 符声明。
- **历史镜 clean**：6 项核对确认实现兑现 spec-review amendment，无重蹈历史坑、无违背 ADR/CONTEXT 约定（盘面即状态/终态集/三维度分家/绝不解析人写行）。
- **对抗A 核验 clean**：em-dash 变体（en-dash/裸 U+2014 无空格）不匹配 header 正则不构成绕过 · Tab/U+2028/U+2029（readlines 只认 \n\r）非结构性风险。
- **<80 滤除**：无（本轮 findings 均 ≥80）。

### 修复 / defer 台账
- **自动修 6 项 [impl-review-fix]**（commit `54105d5` 五项 + `e2036f5` FIX-6）；全 TDD 先复现后修，git stash 验证 19 新测试修前全红。全仓 **552 passed** 无回归。
- **defer**（非缺陷/低优先，进 todolist，hand-off 引用）：
  - 对抗B-F2：`except Exception` 偏宽不分数据一致性 vs 基础设施故障（磁盘满/权限）——**design.md/D2 明确拍板取舍**，非缺陷，记注不改。
  - 效率×2（领域F3 cmd_scan 双切同行 / 对抗B-F3 rename 两次 read_pool）→ todolist。
  - 对抗A 低：显式 id 前导零歧义（`B007`≠`B7` 共存，人工识别混淆，置信 55）→ todolist。
- **无 ≥2 方案自动选**（6 项均单一正确修法）。

### 度量锚（lens-metric，metrics.enabled=true）
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="native" site="scope-drift" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="backend" findings="4" 采纳="3" 裁掉="0" defer="1" 独立="2" sev="致0/高0/中3/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="guard-bypass" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="1" sev="致0/高2/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="refactor-honesty" findings="3" 采纳="1" 裁掉="0" defer="2" 独立="0" sev="致0/高0/中1/低2" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="git-blame" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="code-voice" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="1" sev="致0/高1/中1/低0" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="数据类 recorder 脚本改动，无运行期爆炸/难回退面命中 HR-TG 子集" -->

### 结论
6 个真 bug 全自动修、552 全绿、defer 残差记 todolist。建议进 `/sdflow-done`（verify → hand-off → archive → commit → merge）。

<!-- ship-gate: code-review=pass -->
