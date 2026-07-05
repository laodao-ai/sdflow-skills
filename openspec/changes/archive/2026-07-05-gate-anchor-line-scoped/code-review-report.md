## code-review 报告 — gate-anchor-line-scoped

> 阶段三代码审（每次全跑·独立冷·强制主审），兼 SDD 最终整支主审。DIFF_BASE=9ef69c1→HEAD。实现：ship_gate.py 三处子串检测收紧（anchors_in/archived_verify_state 行锚定+fence-aware、pick_exclusive/archived 未闭合fence保守、tg02_hit 头部区域）+ sdflow-ship/tests 新增/增补。

### 命中范围
- 栈：纯 Python gate 脚本 + pytest（**无领域栈命中**——非 backend·go/embedded/frontend）。清单：CR base 01~09（错误路径/边界/资源/契约维度）。
- gstack/review（Step1 原生）：**scope 无漂移**（diff 恰为 plan 指定的 `_line_scoped_hits`/`anchors_in`/`archived_verify_state`/`pick_exclusive`/`tg02_hit` + 测试，无顺手多改）；**完成度**=ADR-1~6 全落（Task1-6 + 2 轮 dogfood fix）。
- 镜阵：领域镜 0（无栈）· 对抗镜 2 · 历史镜 1 · code outside-voice(codex) 1。

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="纯内部 gate 逻辑，不涉 DB/API/并发/信任边界/状态机，HR-TG 子集无一命中" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="" findings="2" truncated="false" -->

### Findings（置信 ≥80）

- **[中高] CR-04/边界 · tg02_hit 头部扫描非 fence-aware** | `ship_gate.py:277-291`（旧） | 对抗镜1 脚本实测：头部区 fenced 块内 `## ` 行被裸循环误当边界 `break`→真 `〔TG-02：` 声明落头部外→**假阴：嵌入式 change 漏跑强制 embedded-test-sop（安全边界失效）**；反向 fenced 示例 `〔TG-02：` 被当真声明→假阳。与同文件 `_line_scoped_hits`/`_parse_plan` 的 fence-aware 不一致=遗漏非取舍。置信 95 | **已修[impl-review-fix]**：改 fence-aware 单遍 + 声明行匹配（`s.startswith("〔TG") and "〔TG-02" in s`）+ 3 回归测试。
- **[中] CR-09/契约 · tg02 头部子串 vs 声明行** | codex OV-code-2 | 头部区**描述性**提及 `〔TG-02`（如"技术栈…均不命中"行、反引号提及）仍假阳。置信 88（codex 豁免数值滤） | **已修[impl-review-fix]**：并入上条——声明行 `startswith("〔TG")` 排除描述散文。
- **[中] CR-07/测试 · unbalanced 单测退出码巧合弱哨兵** | `test_gate_anchor_scope.py` `test_pick_exclusive_unbalanced_unknown` | 对抗镜2 实测：旧实现子串两锚命中→conflict→EXIT_UNKNOWN，新→unbalanced→EXIT_UNKNOWN，**同码**，不构成新旧翻转证据（但仍拦内部回归）。置信 85 | **已修[impl-review-fix]**：加 capsys 断言 emit reason 含"未闭合 fence"，区分 unbalanced vs conflict 分支。
- **[中低] CR-07/测试 · 契约测试无空转兜底** | `test_gate_anchor_scope.py` `test_contract_archived_corpus_anchor_hits` | 归档语料若未来无锚→内层 `if anc in text` 全 False→静默空转通过（正是它自称要防的"模板假设静默失效"）。置信 82 | **已修[impl-review-fix]**：加 `checked>0` 计数兜底。

### 已裁掉（反静默压制，可审计）
- **X1 codex OV-code-1（high→降级 defer）** producer 模板（sdflow-spec-review/code-review SKILL）仍展示非独占锚（反引号/尾注）→ 虑新行锚定下报告不认锚。**裁决**：真报告实证干净（15/15 归档报告锚独占顶格；模板展示形 ≠ 真产报告），且 Task5 已加契约测试钉归档语料。**非本 change 代码缺陷**——残差=SKILL 文档展示形收紧（cross-cutting 文档 hygiene）→ **defer todolist**（见台账），非阻断。
- X2 对抗镜1 疑"decide 早检 vs 迟检分裂"→ 实测证伪（decide 先跑 pick_exclusive，未闭合在此 emit UNKNOWN，单锚 peek 不可达 unbalanced 输入）。裁掉。
- X3 对抗镜2 疑"code-review pass/blocked 对无 unbalanced 专测"→ pick_exclusive 通用函数逻辑共享，VPASS/VFAIL 测已覆盖行为；低风险，不强制补（可 defer 但价值低，略）。

### 修复 / defer 台账
- **自动修 4 项[impl-review-fix]**（一个 fix 子代理带全清单）：tg02 fence-aware+声明行（安全相关，含 3 回归测试）· unbalanced 断言 reason · 契约空转兜底。仓级 **368 绿**、gate RUN_CODE_REVIEW。
- **defer 1 项 → todolist**：codex OV-code-1 = producer SKILL 模板锚展示形收紧（把 sdflow-code-review/spec-review SKILL 的展示锚改独占 bare line）；本 change 正交（改的是 gate parser、非 producer 文档），hand-off 引导。
- **voice 分桶〔M4〕**：codex 采纳 1[impl-review-fix, OV-code-2]/裁掉 0/defer 1[OV-code-1]。fallback 0。
- **历史镜**：历史一致、无重蹈（T32/T34/CR-F1/ADR-5/ADR-6/H1 全对标）。

### 结论
- ☑ 建议进 /sdflow-done（verify → hand-off → archive → commit → merge）。
- defer 残差（OV-code-1 SKILL 模板）hand-off 会引用，另行处理。
- **独立冷主审价值印证**（P3c）：抓到 SDD 逐任务审 + 主 session 都漏的 tg02 fence-aware 安全 bug（假阴嵌入式漏 SOP）。

<!-- ship-gate: code-review=pass -->
