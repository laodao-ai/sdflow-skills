## code-review 报告 — sdflow-retro

> 阶段三代码评审（sdflow-code-review 编排，每次全跑·独立冷·强制主审）。diff base = `42efbc1`（origin/main merge-base）。
> Step1 gstack/review(native) + Step2 多镜(领域·python 数据类 / 对抗×2·边界引擎+解析健壮性 / 历史·聚合器迁移) + code-voice(codex)。

### 命中范围
- 栈：dev-tooling / python 数据类 skill（retro_report.py 414 行 + 迁入 lens_metric_aggregate.py）+ bundle 部署纪律 + SKILL/docs prose 级联。
- 清单：CR-01~09（base）+ python 数据类 skill 约定（CLAUDE.md：机械活交脚本、不变量别塞回模型）。
- **trivial_shape = NOT_EXEMPT**（有逻辑面 retro_report.py）→ 照常 fan-out。
- **HR-TG = none**（命中 TG{11,12,14,15,18,21,22,23} ∩ HR-TG 子集=∅；只读观测工具无运行期爆炸/数据损坏/安全面）。
- **gstack/review(Step1, native)**：scope-drift = 空（所有改动在 sdflow-retro/ + 计划级联清单内，无顺手多改）；完成度 = plan 13 任务全绿（ledger 实证）。

### ★核心冷审判定
**独立冷主审兑现 load-bearing 价值**——抓到一个 SDD 任务 review + dogfood 全都放过的**致命 bug（F1）**：归档 change 边界丢 pre-archive 历史，致本仓 **17/18 归档 change 假性"边界不可解析"**，聚合段只由 1 个在制品撑起——retro 核心承诺（跨 change 成本×价值复盘）对 94% 语料失效。三源收敛（对抗镜1 + codex code-voice + 部分领域镜）+ 实证坐实（ship-gate-hardening：实现算 1 条/unresolved，裸 pre-archive 路径本可捞 8 条）。已修，dogfood **K 17→2**（剩 2 为真 seed change）。同 `grill-not-skippable` 教训：dogfood"看着过"不等于真过，冷独立层不可跳。

---

### Findings（置信 ≥80，对抗裁决后）

| # | 严重度 | 位置 | 问题 | 命中镜 | 裁决 |
|---|---|---|---|---|---|
| **F1** | **致命** | retro_report.py:84 `boundary_for_change` | 归档 change `active_dir=None`→只查 archive 路径（git log 看不到 rename 前历史），从不查 design D1 本意的裸 pre-archive 路径 → 17/18 假不可解析，核心承诺击穿 | 对抗1+code-voice+域 | **已修[impl-review-fix]** 1d4eebc：查裸 `changes/<name>` ∪ archive 去重排序；反证测试修前FAIL修后PASS；dogfood K 17→2 |
| **F2** | 高 | retro_report.py:253 `_read_hr_hit` | 裸 open 无 try/except，chmod000/TOCTOU→PermissionError 冒泡崩整份报告（全脚本唯一违"不崩"口径的读取路径） | 域+对抗2 | **已修[impl-review-fix]** 060d008：try/except (OSError,UnicodeDecodeError)→"—" |
| **F3** | 高 | retro_report.py:227 `lens_value_for_change` | 丢弃 `_int` 的 is_bad，非法值(负/非数)静默污染 Σfindings/采纳率，与聚合③的 ⚠数值非法 口径矛盾 | 对抗2+code-voice | **已修[impl-review-fix]** 89b76b1：传播 num_bad + per-change 行级 ⚠数值非法 标记 |
| **F4** | 中 | retro_report.py:247 `_read_hr_hit` | hr-tg 读取非 fence-aware，反引号示范锚被当真读进列(fail-silent)，与 lens-metric 锚护栏不对称 | 域+code-voice | **已修[impl-review-fix]** 060d008：复用 `LMA._fence_aware_lines` 跳示范锚 |
| **F5** | 中 | retro_report.py:153 `is_archive_rename` | D+A 兜底 `name in p` 裸子串匹配，foo 误配 foo-2（F1 修后 pre-archive 全历史回来会引爆） | 对抗1 | **已修[impl-review-fix]** 1d4eebc：目录边界锚定正则 `\d{4}-..-..-{name}(/\|$)` |
| **F6** | 低-中 | retro_report.py:101 `_STAGE_RULES` | 缺 done-archive/done-verify/裸 gate 前缀→落 unknown 桶（F1 修后归档 done 阶段浮现一堆 unknown） | 对抗1 | **已修[impl-review-fix]** 1d4eebc：补 done-archive/done-verify→done、gate→spec-review |
| **F7** | 中 | retro_report.py:253 `_read_hr_hit` | 多锚 first-wins（实测 checkpoint-tag-single-source 报告有 2 条 hr-tg 锚），丢更权威的后续判定 | 对抗2 | **已修[impl-review-fix]** 060d008：续扫取最后一条=最终判定 |
| **F12** | 中 | retro_report.py:331 `build_report` | per-change 表漏 design.md:103 schema 承诺的阶段 Δ 列(spec-rev/impl/code-rev/done)，"卡在哪阶段"能力不可得 | 域 | **已修[impl-review-fix]** 89b76b1：补 4 阶段 Δ 列(F1 修后有真值,如 adaptive-routing spec-rev 83.8/impl 10.1/code-rev 3.0/done 0.5) |

### 已裁掉（反静默压制，可审计）
- 无 reviewer finding 被判"不成立"裁掉——本轮所有存活 finding 均采信（修或 defer）。
- 历史镜 findings=0：group_key 抽取经实证 behavior-preserving（聚合器 19/19 仍绿），CF-1~7 前科修复全保留，迁移 import 路径正确——无前科重蹈，非"裁掉"而是真无问题。
- broad(scope-drift/完成度) findings=0：scope 无扩张、plan 13 任务全绿。tasks.md 是 grill 期原始 checkbox 清单（未随实现勾选）——非缺陷（plan 是实现真相源，gate 靠命名空间锚判完成非 checkbox），记 Minor 观察不计 finding。

### 修复 / defer 台账
- **自动修 8 项[impl-review-fix]**（3 commit，均反证真哨兵测试修前FAIL/修后PASS）：F1/F5/F6@1d4eebc（边界引擎）、F2/F4/F7@060d008（hr-tg 读取）、F3/F12@89b76b1（per-change 表）。
- **defer 4 项 → todolist**（低危/既有/design-accepted，hand-off 引用）：
  - T58 F8：fence-aware 只支持反引号不支持 `~~~` tilde（既有聚合器限制，非本 change 引入）
  - T59 F9：≥10 阈值硬编码两处无共享常量（同 group_key 漂移类，低危）
  - T60 F10：_run_git 无 returncode 检查，git 失败与无提交不可区分（design fail-open）
  - T61 F11：build_report/surfacing 包 aggregate 的 except 死防御(glob 缺目录不抛)+注释误导
- 无 T10 三级协议触发（无"≥2 方案无客观判据"的自动选——所有修复判据客观：F1 有 design D1 本意+实证、余均有反证哨兵测试）。

### 度量锚（lens-metric，metrics.enabled=true）
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="—" findings="5" 采纳="3" 裁掉="0" defer="2" 独立="1" sev="致0/高1/中2/低2" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="—" findings="8" 采纳="6" 裁掉="0" defer="2" 独立="3" sev="致1/高2/中3/低2" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="code-voice" findings="4" 采纳="3" 裁掉="0" defer="1" 独立="1" sev="致1/高1/中2/低0" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="命中 TG{11,12,14,15,18,21,22,23}，∩ HR-TG 子集{04,06,07,08,09,16,17,26}=∅；只读观测工具无运行期爆炸/数据损坏/安全面" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="none" findings="4" truncated="false" -->
<!-- sdflow:step1-broad-review v1 mode="native" -->

> 度量说明：adversarial 折叠 2 冷镜（边界引擎 + 解析健壮性）到 canonical lens；独立 = 唯一报过 ∧ 被采纳(修或 defer)。冷主审总 8 修 4 defer，致命 1(F1)/高 2(F2,F3)。

### 结论
- 独立冷主审抓到致命 F1（核心承诺击穿）+ 高危 F2/F3 + 5 中低危，全部 8 项自动修（反证真哨兵）、4 项 defer todolist。
- 全仓回归：**453 passed, 1 failed**（唯一失败 = `test_gate_anchor_scope.py::test_contract_archived_corpus_anchor_hits` pre-existing B5，main 亦红非本 change）。
- dogfood 复验：K 17→2、per-change 阶段 Δ 列有真值、hr-tg fence-aware/多锚正确、非法值标记——核心承诺恢复。
- 建议进 `/sdflow-done`（verify → hand-off → archive → commit → merge）。defer 残差已入 todolist（T58-T61，hand-off 引用）。

<!-- ship-gate: code-review=pass -->
