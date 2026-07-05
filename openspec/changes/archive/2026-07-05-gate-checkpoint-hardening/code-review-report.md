## code-review 报告 — gate-checkpoint-hardening

<!-- sdflow:step1-broad-review v1 mode="simulated" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="命中 TG{19,23,25}，均不入 HR-TG 子集" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="" findings="3" truncated="false" -->

### 命中范围
- 代码 diff（相对 main）：110 insert / 13 del / 10 文件——`ship_gate.py`(2 纯函数+注释) · 5 SKILL.md · workflow.md · 3 test。
- 清单：CR-base（错误处理/资源/一致性）+ 本项目 gate/checkpoint 契约。gstack/review：scope-drift 无（一致性镜确认 diff 全可追溯 6 任务）。
- 镜：对抗镜（新逻辑）· 一致性镜（impl vs spec-review 定稿，**0 不符**）· codex code-voice。

### Findings（置信 ≥80，去重后 7 + 1 接受）

| CR | 严重 | 问题 | 证据 | 处置 |
|---|---|---|---|---|
| **CR-1** | 高 | 熔断锚集判据误杀 `RERUN_STALE`（进展信号=新鲜度刷新非锚变，pass→pass 被假熔断） | codex-C1；SKILL:29 | ✅ 自动修：按 verdict 分治（锚集限 STEP_IN_PROGRESS，RERUN_STALE 以"重跑后仍 stale"为准）[impl-review-fix] |
| **CR-2** | 中 | `breaker_no_progress` fail-safe 非对称——`after=None` 时非空 before 返 False=假放行 | 对抗-2；ship_gate.py:257 | ✅ 自动修：`before is None or after is None → True` + 测试 [impl-review-fix] |
| **CR-3** | 中 | TAG_RE 注释称格式含 `<slug>` 权威，但正则只到 `task(\d+)-` 不校验 slug | codex-C2；ship_gate.py:298/304 | ✅ 自动修：注释澄清 slug 建议非 parser 契约 [impl-review-fix] |
| **CR-4** | 中 | merge untracked"排除既有 debris"靠模型主观判断，违反"机械活交脚本" | codex-C3+对抗-3；done SKILL:250 | ✅ 自动修：改机械"任何 ??→halt 人工triage" [impl-review-fix]；精确 baseline 版 defer→T52 |
| **CR-5** | 低中 | `.gitignore` 忽略的文件逃过 untracked 检查（连 `??` 都不出现） | 对抗-4（实测 .outside-voice/） | ✅ 自动修：补边界声明 [impl-review-fix] |
| **CR-6** | 低 | untracked 检查 `git status --porcelain` 未加 `-c core.quotePath=false`（中文名 C-quote） | 对抗-5 | ✅ 自动修：加 quotePath 加固 [impl-review-fix] |
| CR-ADV-1 | 中高 | 熔断 helper 靠编排器 prose 调用、未进 `decide()`；忘调则无限循环复现 | 对抗-1 | **接受**（非新缺陷）：持久化下沉撞三红线〔spec-review SR-1 已登记〕，helper 从"prose 数数"降为"prose 调无状态比较"已是可及的最硬 |

### 已裁掉 / 抗住（反静默压制，可审计）
- 对抗镜「锚模板改动本身是修复非新问题」**抗住**（旧模板反引号/尾注会让 gate 精确匹配 miss，本次修对）。
- 对抗镜「before/after 皆空集判无进展」**抗住**（STEP_IN_PROGRESS 定义即"报告在无锚"，两空集是该态重跑未产出的真实反映，与既有语义一致）。
- 一致性镜 5/5 需求 ✅ impl 忠实落 spec-review 定稿，0 不符。
- **低观察（未修，记录）**：SKILL:29 "workflow.md §二/步骤6" 汉字数字命名空间可能被误读为"阶段二"——纯措辞、无机判依赖，低优先，未修。

### 修复 / defer 台账
- 自动修 6 项 [impl-review-fix]：CR-1~6（触及 ship_gate.py 代码+注释 / sdflow-ship SKILL / sdflow-done SKILL / spec delta / test_gate_breaker 新增 after=None 测试）。全仓 pytest 375 passed 零回归。
- defer 1 项：CR-4 精确 baseline 版（分支切出点 untracked 快照 diff）→ todolist **T52**。
- 接受 1 项：CR-ADV-1 熔断 prose 调用（撞三红线，spec-review 已登记的取舍）。
- voice 分桶：codex 采纳 3（C1→CR-1 / C2→CR-3 / C3→CR-4）/ 裁掉 0 / defer 0（C3 核心自动修+增强 defer）。

### 结论
□ 建议进 /sdflow-done（verify → hand-off → archive → commit → merge）。残差 T52 已入 todolist（hand-off 会引用）。

<!-- ship-gate: code-review=pass -->
