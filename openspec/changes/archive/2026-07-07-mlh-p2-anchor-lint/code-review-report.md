# code-review 报告 — mlh-p2-anchor-lint

> 阶段三独立冷主审。Step1 broad（scope-drift+完成度）+ Step2 多镜（领域/对抗A/对抗B/历史）+ code outside-voice(codex)，主 session 强档对抗裁决 + 自动修。DIFF_BASE=`ca66d60`。

## 命中范围
- 栈：Python 工具脚本 + bundle markdown（无 backend·go/embedded/frontend 领域）→ 领域镜跑 CR base（CR-01~09）+ Python correctness。
- **trivial_shape = NOT_EXEMPT**（new-codepath + behavior-path anchor_lint.py/SKILL.md/契约）→ 全跑 fan-out。
- **HR-TG = none**（同 spec-review 判定）。
- gstack/review（Step1 broad）：scope-drift **干净**（19 文件均归入 7 任务组/change 元数据；test_init.py 改动为契约铺进的必要联动、非掩盖回归）；完成度：9/12 Scenario 全覆盖 + 3 处测试深度不足（见 F9/F10/F11）。

<!-- sdflow:hr-tg v1 hit="none" evidence="锚自检门错判最坏为评审报告假过/假阻，非运行期爆炸/数据损坏/安全泄漏，不入 HR-TG 子集" -->
<!-- sdflow:step1-broad-review v1 mode="simulated" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="ok" findings="3" truncated="false" -->

## Findings（置信 ≥80）

### 高
- **[高] F1 CR-02 空串字段绕过 → 假 CLEAN**〔领域镜+对抗A **独立收敛**，实测复现〕| `anchor_lint.py:169-178` | `check_lens_metric` 四字段用真值判断 `kv.get(f) and ...`，`layer=""` falsy 跳过枚举/layer==cli 检查，missing-field 又只判 key 在 → 空值锚判 CLEAN（计数字段风格不同、正确捕获）| 置信 95 | **已修[impl-review-fix]**：四处改存在性判断 `if "f" in kv and kv["f"] not in enum`。
- **[高] F2 config 读失败 fail-open**〔codex〕| `anchor_lint.py:112` | `read_metrics_enabled` 的 `except OSError: return False` 把 PermissionError/IO 错误当「文件缺失→false」放行 → 重开反静默口子 | 置信 88 | **已修[impl-review-fix]**：只 `FileNotFoundError→False`，其他 OSError→MetricsError→ERROR(2)。

### 中
- **[中] F3 config 顶层注释误判 → 假 ERROR**〔对抗A，实测合法 YAML〕| `anchor_lint.py:121` | `metrics:` 与 `enabled:` 间的 col-0 `#注释`行被 `_TOP_KEY` 当下一顶层键提前 break → MetricsError 阻断（模板本身习惯 key 前加注释）| 置信 85 | **已修[impl-review-fix]**：块边界跳过纯注释行 `ln.strip().startswith("#")` 与空行。
- **[中] F4 UnicodeDecodeError 未捕获**〔codex+领域镜收敛〕| `anchor_lint.py:39,112,192` | 报告/契约/config 读只捕 OSError，非 UTF-8 → traceback（退出码 1）破坏「human+JSON+exit2」接口 | 置信 85 | **已修[impl-review-fix]**：三处统一捕获 `(OSError, UnicodeDecodeError)` → ERROR(2)。
- **[中] F5 锚版本无 token 边界**〔codex+历史镜收敛〕| `anchor_lint.py:92` | `startswith("...v1")` 让 `v10`/`v1_corrupted` 误当 `v1` | 置信 82 | **已修[impl-review-fix]**：`anchor_prefix` 前缀后须紧跟空白或 `-->`（token 边界）。
- **[中] F6 spec-review SKILL:80 旧段残留重复**〔领域镜+broad+implementer 自陈 收敛〕| `sdflow-spec-review/SKILL.md:80` | line 79 已改调脚本，line 80 仍留旧 grep 时代「lens-metric 自检扩一类…config 门控」重复段（code-review SKILL 已整合干净）| 置信 90 | **已修[impl-review-fix]**：删 line 80 冗余段。
- **[中] F7 CR-09 `is None or True` 恒真断言**〔领域镜〕| `test_anchor_lint.py:38` | `X is None or True` 恒 True，无回归防护 | 置信 92 | **已修[impl-review-fix]**：改 `assert al.anchor_prefix(...) is None`。
- **[中] F8 design.md:139 roadmap 内部矛盾未同步**〔broad〕| `roadmaps/mechanical-layer-hardening/design.md:139` | task5.3 只改 §2 技术栈表(:56)+roadmap.md:61，§4 候选全表 P2 行(:139)仍写「复用…不重实现」→ 与 :56「重实现」自相矛盾 | 置信 88 | **已修[impl-review-fix]**：同步 :139。
- **[中] F9 Scenario12「数值一致性诚实边界」测试缺失**〔broad〕| `test_anchor_lint.py` | 实现正确不校验，但 tasks 3.6 承诺的守卫测试未落地 | 置信 80 | **已修[impl-review-fix]**：补 findings≠实收数→CLEAN 测试。
- **[中] F10 fence 核交叉断言未落地**〔对抗B+broad 收敛〕| `test_lens_metric_aggregate.py:321` | `test_dual_parser_cross_assert` 只断言 enum 相等、不覆盖 fence 核；design/tasks 承诺的两 `fence_*` 函数逐行等价断言未兑现（对抗B 实测两者当前等价，但无守卫防未来漂移）| 置信 80 | **已修[impl-review-fix]**：补 fence-core 8 边界用例逐行等价断言。

### 低
- **[低] F11 min-required-rows 正例/单缺分支未测**〔broad〕| `test_anchor_lint.py` | 只测「两者都缺」，缺「都在→过」「只缺一个」| 置信 78 | **已修[impl-review-fix]**：补正例+单缺分支。

## 已裁掉 / defer（反静默压制·可审计）

- **defer→todolist F12**〔对抗A 低·潜伏〕：`load_enums` 若契约 `lens-metric-enums` 块内**未来**加裸 ``` 行会提前闭合 → EnumsError（fail-closed 方向、非假 CLEAN）。当前块内容（4 行 key:value）不含裸 fence，未触发。**defer**：潜伏、fail-closed 安全侧、契约受控；加防护属过度工程，留 todolist 待契约真需嵌 fence 时处理。
- **defer→todolist F13**〔对抗B 低〕：无「pin 消费仓 update 后 workflow.md/spec-checklists/code-checklists 原封不动、仅 tools/+契约刷新」的端到端交叉不变量测试。各组件单测已覆盖（copy_bundle 契约同刷 + resolve pin 检测独立测），端到端组合缺。**defer**：低风险、组件已各测，留 todolist。
- **裁掉 X1**〔对抗B/领域镜 低〕：退出码 1 vs 2 在两审 SKILL 无差异化处理（均「非 0 即阻塞」）——**设计既定**（两种失败都该挡，1/2 只人读诊断区分），非缺陷、不改。
- **裁掉 X2**〔对抗B/领域镜 低〕：`_ENUM_BLOCK` marker 后不容空格的脆性——fail-closed（ERROR 而非假 CLEAN），可接受、不改。

## 修复 / defer 台账
- **自动修 11 项 [impl-review-fix]**（F1-F11）：均有客观判据（测试/实测复现），T10 协议①自动选，按对抗裁决采纳。
- **defer 2 项**（F12/F13）→ todolist（潜伏/端到端组合，低风险）。
- 无 ≥2 方案分歧项（修法唯一明确）。

## 度量锚（lens-metric，metrics.enabled=true）
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="claude" site="—" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="3" sev="致0/高0/中4/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="—" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="1" sev="致0/高1/中1/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="—" findings="5" 采纳="3" 裁掉="1" defer="1" 独立="2" sev="致0/高1/中2/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="code-voice" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="1" sev="致0/高1/中2/低0" -->

## 结论
- 冷层大丰收：**2 高**（F1 空串假 CLEAN、F2 config fail-open——F1 由领域镜+对抗A 独立复现，正是循环内被放过的真 bug）+ 8 中 + 1 低，全自动修；2 低 defer todolist。
- 冷主审再次证明 load-bearing（生成循环内 7 implementer 全绿、注入点 B 未抓到 F1 空串绕过）。
- 建议进 `/sdflow-done`。

<!-- ship-gate: code-review=pass -->
