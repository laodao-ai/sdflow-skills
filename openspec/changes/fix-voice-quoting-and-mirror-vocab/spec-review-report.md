---
ship-gate:
  design_approved: true
  reviewed_sha: 29e6110658e87da971579835c6c99467f6cc96f7
---

# spec-review-report: fix-voice-quoting-and-mirror-vocab

## 评审元数据

- **变更**：fix-voice-quoting-and-mirror-vocab（T164 路径引号 + T148 镜名扩展）
- **命中 TG**：TG-17（信任边界）、TG-18（测试计划）
- **镜头配置**：对抗镜 ×2 + 接地镜 ×1 + autoplan 广审（含 CEO 双声）
- **outside-voice**：design-voice（同族 fallback）+ hr-tg（同族 fallback）

<!-- sdflow:hr-tg v1 hit="TG-17" declared="TG-17,TG-18" evidence="T164 涉及 shell 命令路径注入修复（TG-17）" -->

### 子代理能力锚

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->

（本 change 无命中领域，领域镜 = 0；`domain` 计本次接地镜在接地义。实际 fan-out：接地镜 1 + 对抗镜 2 + design-voice 1 + hr-tg voice 1。）

### outside-voice

<!-- sdflow:outside-voice v1 site="design-voice" guard="section-not-found" host="claude" runner="claude" reason_code="exec-error" findings="3" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="claude" reason_code="exec-error" findings="5" truncated="false" -->

两站点均因 preflight 失败（harness 每次 Bash 调用是独立 shell，`$SDFLOW_VOICE_RUNNER` 不持久）回落同族 fallback。design-voice fallback 3 条 findings，hr-tg fallback 5 条有效 findings（含 2 条 INFO 排除）。

<!-- sdflow:declared-sites v1 declared="design-voice,hr-tg" -->

---

## Findings（去重合并，按严重度降序）

### 🔴 S1 [Critical] delta spec 标题不匹配主 spec，archive 必炸

**命中镜**：对抗镜2（独家）
**置信度**：高（已核验）

delta spec `specs/host-adaptive-execution/spec.md` 的 MODIFIED Requirement 标题写 `mirrors= 合法 token 集扩展为四值`，而主 spec `openspec/specs/host-adaptive-execution/spec.md` 对应的真实标题是 `子代理不可用时镜数如实降级（探针语义核验 + always-on 一致性 lint，逐镜留语义层）`。`openspec archive` 的 `buildUpdatedSpec` 按标题匹配，不匹配直接 throw。

且 delta 只含 3 条新 Scenario，未携带主 spec 现有的 ~7 条 Scenario → `findMissingCurrentScenarios` 二次命中。**双重必炸**。

tasks.md 3.3 的 `openspec validate` 不做主 spec 匹配校验，测不出此坑。

另：`workflow-metrics` 和 `spec-workflow` 两份 spec 的改动（tasks.md 2.4 第 2、3 项）完全没有 delta spec 文件——计划直接手改主 spec，绕开 delta → archive 流程，但未在 proposal/tasks 中显式声明此决策。

**建议**：① 修正 delta spec 标题 = 主 spec 原标题；② delta 必须携带修改后的完整 Requirement 文本（含全部现有 Scenario，仅扩展 token 集）；③ workflow-metrics / spec-workflow 的改法要么也建 delta，要么显式声明走直接改主 spec 并说明理由。

---

### 🟡 S2 [High] 测试覆盖图指错文件 + 验证命令覆盖不到

**命中镜**：对抗镜1 + 对抗镜2 + design-voice（3 镜收敛）
**置信度**：高

tasks.md「测试覆盖图（TG-18）」把 `_parse_mirrors()`/`check_fanout_consistency()` 的覆盖来源全部记成 `sdflow-init/tests/test_codex_subagent_authorization.py`，但该文件只做文档反漂移锁（断言 SKILL.md 文本中 token 集合），不调用解析函数。真正的功能单测在 `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py`——完全未被 design/tasks 提及。

Success Metric #4 / Task 3.1 指定 `pytest sdflow-init/tests/`，覆盖不到 `sdflow-init/assets/workflow/tools/tests/`。两者是独立目录树。

**结果**：spec delta 新增的两条 Scenario（`history token 被接受` / `dead-fanout-multi-mirror 覆盖 history token`）将**没有任何功能测试真正验证**，`pytest sdflow-init/tests/` 假绿通过。

**建议**：① 在 `test_anchor_lint.py` 补 `history` token 的 `_parse_mirrors` 接受用例 + `mirrors="domain,history"` 场景下 `dead-fanout-multi-mirror` 触发用例；② Task 3.1 改为 `pytest sdflow-init/` 或仓根裸 `pytest`。

---

### 🟡 S3 [High] task 2.3「删借用说明段落 L244-248」的删除范围会连带删掉 MUST 规范语句

**命中镜**：对抗镜2（独家）
**置信度**：高（已逐字核验 L244-249）

L244 开头是核心 MUST 语句 `mirrors= MUST 由本 skill 直接写本轮实际派出/独立完成的镜清单`，L245 是 token 集定义，L246-248 才是借用叙事。按字面执行「删 L244-248」会把规范语句和 token 集定义一并删掉。

**建议**：task 2.3 改为「重写 L244-248：保留 MUST 规范语句，token 集改为 `{domain,adversarial,history}`，删除借用叙事」。

---

### 🟡 S4 [High] design.md 安全分析的 change 名攻击面前提是假的

**命中镜**：对抗镜1 + HR-TG voice（2 镜收敛）
**置信度**：高（已核验 CLI 源码）

design.md 写 `change 名（用户输入，openspec new change 可能接受含空格的名称）`。实测 `@fission-ai/openspec@1.7.0` 的 `validateChangeName` 强制 kebab-case（`/^[a-z0-9]+(?:-[a-z0-9]+)*$/`），空格被硬性拒绝。本仓 `ff0-branch-guard.py` 也编码同一约束。

真实唯一的空格来源 = 仓根路径（如 macOS `/Users/First Last/`）。修法本身仍然正确，但安全论据不实。违反 `premise-verification.md`。

**建议**：删掉 change 名攻击面，收窄为仅 repo-root / 工作目录路径。

---

### 🔵 S5 [Medium] 反漂移锁测试循环需拆分

**命中镜**：对抗镜1 + 对抗镜2 + design-voice（3 镜收敛）
**置信度**：高

`test_mirrors_tokens_are_subset_of_anchor_lint_vocabulary` 用同一循环对两份 SKILL 断言同一字面串 `"domain,adversarial,grounding"`。T148 后 code-review 变 `history`、spec-review 保持 `grounding`——循环必须拆成按文件区分预期。

**建议**：task 2.5 明确写「拆分为两个断言路径，spec-review 期望 grounding、code-review 期望 history」。

---

### 🔵 S6 [Medium] T164 清单遗漏 marker 内人工恢复命令的路径占位符

**命中镜**：CEO Claude + HR-TG voice
**置信度**：高

async-branch marker 段内的 `cleanup --run-dir <d>` / `reconcile --run-dir <确切目录>` 占位符（code-review L448/465/466，spec-review 对应行）同样未加引号，不在 design 修改清单中。

**建议**：补进 task 1.1/1.2 清单。

---

### 🔵 S7 [Medium] 威胁模型措辞比实际防护范围更宽

**命中镜**：CEO Claude + Codex + HR-TG voice（3 镜收敛）
**置信度**：高

proposal/design 里「执行非预期命令」的措辞高估了双引号的防护——双引号防空格拆分和 glob 展开，不防 `$(...)` 命令替换。按基准④五问，残余可判定可接受（repo-root 正常不含 `$()`），但该判断必须写出来。

**建议**：明确只声称「防止空格导致的参数拆分」，加一句残留边界声明。

---

### 🔵 S8 [Medium] 借用文档测试断言「假通过」

**命中镜**：对抗镜1
**置信度**：中

`test_code_review_history_mirror_alias_honestly_documented` 的 5 条断言中，`"历史镜"` 和 `'lens="history"'` 在文件其他位置另有 ~9 处出现——删掉借用段落后这两条仍会通过。容易被简化处理成「删 3 条断言」而不是重写为验证新行为。

**建议**：新测试应断言 `mirrors=` 字面串含 `history`、且旧借用措辞不再出现。

---

### ⚪ S9 [Low] anchor_lint.py:702 docstring 硬编码未纳入修改清单

**命中镜**：对抗镜1 + design-voice
**置信度**：高

`check_fanout_consistency()` 的 docstring 写死 `{domain,adversarial,grounding}`，design.md 清单未覆盖。DOC-1 项。

**建议**：task 2.1 顺手同步 L702 docstring。

---

### ⚪ S10 [Low] T148 前提叙述精度

**命中镜**：Codex CEO + 对抗镜2 未爆点确认
**置信度**：中

当前 `_parse_mirrors()` 已先以 `unknown-token` 拒绝 `history`，到不了 `check_fanout_consistency()` 的 count 逻辑。proposal 说的「漏算」技术上不精确——更准确是「拒于门外」。

**建议**：修正 proposal/design 叙述。

---

### ⚪ S11 [Low] codex-host dispatch 行漏列 `--context-file`

**命中镜**：HR-TG voice
**置信度**：中

design.md `--context-file <f>` 行号列 `436,496 / 432,492`，但 codex-host dispatch 行（L443/439）也含 `--context-file <f>` 未被表格覆盖。

**建议**：按模式全局替换则不受影响，但表格应补上或注明按模式替换。

---

## 决策登记区

### [自动决策]

- **D1**：Codex 建议拆分两项为独立 change → 按项目 fold-vs-defer 准则维持合一（P3，改动文件高度重叠）
- **D2**：Codex concern fallback 行 marker 内外矛盾 → tasks.md 1.4 已正确标注 marker 外独立改，design 分两表，不矛盾
- **D3**：对抗镜1 F5 面治缺口（marker 外 outside_voice_guard/anchor_lint 调用行的 `{change_dir}` 未引号）→ 本 change scope = async 调度段 + mkdir，其他行虽同类但属不同功能段，按基准④记 todo 不扩范围

### [已拍板]

- **Q1**：三份 spec 统一走直接改主 spec（Q1-B）。**已批准**，2026-08-03。

### [已裁掉]

- **X1**：Codex「Bundling is justified only by editing overlap, which is weak」→ 裁掉。理由：项目 fold-vs-defer 准则明确支持改动文件高度重叠时合 change，且 T164/T148 改动无依赖冲突。
- **X2**：对抗镜1 F5「面治缺口——同文件 marker 外的 {change_dir} 路径」→ 裁掉。理由：本 change scope = async 调度段 + mkdir，marker 外其他功能段的路径引号属不同功能上下文，按基准④记 todo 不扩范围。

---

## 收敛意见

**建议进设计 HARD-GATE**，但有 1 个 Critical + 3 个 High 需先修正：

1. **S1 [Critical]**：delta spec 标题不匹配 → 必须修正后才能拍板（或改走直接改主 spec，见 Q1）
2. **S2 [High]**：补 `test_anchor_lint.py` 功能测试 + 修正验证命令
3. **S3 [High]**：重写 task 2.3 描述（保留 MUST 语句，不是整段删）
4. **S4 [High]**：修正 design.md 安全分析前提

建议人工在设计 HARD-GATE 一次性过报告拍板。S5-S11 均可在实现期顺手处理，不阻塞拍板。

---

## 度量锚（lens-metric）

<!-- sdflow:step1-broad-review v1 mode="native" -->

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="8" 采纳="8" 裁掉="0" defer="0" 独立="4" sev="致1/高3/中2/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中1/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="claude" site="design-voice" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="0" sev="致0/高1/中1/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="claude" site="hr-tg" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="1" sev="致0/高1/中1/低2" -->

> 本轮最高价值 = 对抗镜（8 findings 全采纳，4 独立，含 1 致命——delta spec 标题不匹配必炸 archive）。
> outside-voice hr-tg 贡献 4 条含 1 独立（change 名攻击面前提证伪）。接地镜 0 findings（所有代码事实核验通过）。
> 保留信任边界声明：findings 数与合并池实收数的数值一致性是主 session 信任边界，非机械可验。
