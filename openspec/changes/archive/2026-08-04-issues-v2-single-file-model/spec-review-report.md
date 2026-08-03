---
ship-gate:
  design_approved: true
  reviewed_sha: 266f53f373a77249c12f897eb29f5ca00ed192ab
---

# Spec Review Report: issues-v2-single-file-model

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->
<!-- sdflow:hr-tg v1 hit="TG-09" declared="TG-05,TG-09,TG-14,TG-18,TG-23" evidence="issue 有多状态生命周期 OPEN→PROPOSED→终态，设计含状态机图和转换逻辑" -->

## 评审概况

- **Change**: issues-v2-single-file-model
- **分支**: feat/issues-v2-single-file-model
- **命中 TG**: TG-05（数据对象）、TG-09（状态机）、TG-14（重构组件）、TG-18（测试计划）、TG-23（方案选择）
- **HR-TG 命中**: TG-09
- **镜头配置**: autoplan 广审（CEO+Eng 双声） + 领域镜（base R 项） + 对抗镜×2 + 接地镜 + outside-voice×2（design-voice、hr-tg）
- **评审结论**: **不建议当前版本进入设计 HARD-GATE**——5 条 CRITICAL 阻塞级缺口需先回流修复

---

## CRITICAL Findings（阻塞级，不修不放行）

### CR-1. 并发锁丢弃——已修过一次的 bug 在 v2 静默复现

**问题**: `sdflow_issues_core` 的 `.recorder.lock`（ADR-0025）提供跨进程互斥，v2 design.md 通篇未提及锁的去留。`add`/`next-id` 的"扫文件名取 max+1 → 写文件"流程在无锁下，两个并发 `add` 会拿到同一 ID，后写者覆盖前写者——永久数据丢失，exit 0。

**证据**: T146（status: DONE）原文记录此 bug 在 v1 已被发现并修复（`O_CREAT+O_EXCL 仓级互斥`）。`sdflow_issues_core/__init__.py:373-485`。design.md/decision-memo 无任何 C 条目覆盖并发安全。

**命中镜**: CEO-E + Eng-C1 + 对抗②-F2 + domain-BASE-06（四面收敛）

**裁决**: **采纳**。置信高，四面独立命中，有 v1 修复记录为证。

**建议**: design.md 补并发安全段落（采用缩窄版锁 or 显式 decision-memo 接受风险+理由），specs 补并发 Scenario，tasks 补并发测试。

---

### CR-2. 迁移格式前提证伪——双格式共存需按 ID 去重（43% 数据风险）

**问题**: MIG-01 把 legacy 表格和 frontmatter overlay 定义为互斥的文件级格式。实测 `todolist/2026-07-todolist.md`（2853 行）同时含 152 行 legacy 表格 + 146 个 overlay 项，34 个 ID 两边都有（frontmatter 为权威，表格行是冻结快照）。迁移按文件级分派 → 124/287 ≈ 43% 的 issue 被静默丢弃或取到过期值。

**证据**: `_build_effective_snapshot`（`sdflow_issues_core/__init__.py:824-912`）明确实现了按 ID shadow 的逻辑。ADR-0025 §2 定义了这种 overlay 模型。buglist 目录也有 1 个混合文件（`2026-07-15-buglist.md`）。

**命中镜**: Eng-C3 + design-voice-#1 + 对抗②-F3 + domain-BASE-05（四面收敛）

**裁决**: **采纳**。置信高，定量证据明确。

**建议**: MIG-01 改为逐 item 去重（frontmatter 优先于 table row），复用现有 shadow 逻辑。补 Scenario 覆盖"同文件双格式共存"。

---

### CR-3. spec-workflow 元 spec 遗漏——全仓流水线规则 18 处硬编码 buglist/todolist

**问题**: `openspec/specs/spec-workflow/spec.md` 治理 `sdflow-implement`/`sdflow-code-review`/`sdflow-done`/`sdflow-ship` 全仓流水线，其中 L210（目录结构断言）、L222（batch/sweep MUST 级要求）、L333-334（调用 buglist.py 的 Scenario）、L95/L660（T10-choice defer 进 buglist/todolist）均在 v2 后失效。四件套 Impact/tasks 未列入此文件。

**证据**: `spec-workflow/spec.md:95,210,222,333-334,660` 直接引用 buglist/todolist。比 gstack F/H2 指出的 determinism-guards/recorder-root-resolution 更致命——后者是 issues 领域自己的 spec，前者是全仓流水线的元规则。

**命中镜**: 对抗①-F1（独家发现）

**裁决**: **采纳**。置信高，直接读到冲突文本。

**建议**: 补 spec-workflow 的 MODIFIED delta + CONTEXT.md 同步。tasks 增补对应任务。

---

### CR-4. CI workflow 硬编码即将被删的测试——合并当天 CI 红

**问题**: `.github/workflows/windows-recorder-smoke.yml:67` 硬编码 `sdflow-issues/tests/test_task2_windows_local_fs_smoke.py`。tasks 5.3 + 3.3 会删此文件 → push 后 pytest 报 `file not found`，exit ≠ 0 → CI 红 → 分支保护规则拦死所有后续 PR。

**证据**: `.github/workflows/windows-recorder-smoke.yml:67`。四件套无任何提及 CI workflow。

**命中镜**: 对抗①-F2（独家发现）

**裁决**: **采纳**。置信高，首日必炸，机械可验。

**建议**: tasks 补任务——更新或退役此 CI workflow。若 v2 不保留并发保护则整体退役并说明理由。

---

### CR-5. YAML 序列化无转义策略——真实语料会截断

**问题**: design.md 只写"YAML frontmatter"未指定序列化实现。当前 `sdflow_issues_core` 不用 PyYAML（`grep -rln "import yaml"` 只命中测试），靠 JSON 单行塞值绕开 YAML 转义。v2 若用 plain scalar 写 summary，真实语料中的 `# `（YAML 注释符）和 `: `（mapping 分隔符）会截断或腐蚀数据。

**证据**: T73 summary 含 `true # x`（`# ` 前有空格）→ 读回时 `# x)——...` 被判为注释丢弃。语料中另有 3 处含 `# `、3 处含裸 `: `。且 ADR-0025 明确 Rejected PyYAML（零依赖约束）。

**命中镜**: 对抗②-F1（独家发现）

**裁决**: **采纳**。置信高，语料实锤。

**建议**: design.md 明确序列化策略（沿用零依赖 + 手写有界子集 → 值一律加引号，或采用 YAML safe_dump + 加依赖任务）。decision-memo 补 C 条目。

---

## HIGH Findings

### H-1. sdflow-done sweep 替换方案不足——三项能力丢失 + 现状描述错误

**问题**: design.md 称 sweep 是"两次 scan"，实际是复合操作 `issues.py sweep --change`（lock + triage + batch add + reindex）。v2 的替代 `scan --json` 丢失：① `--change` 作用域过滤、② 批次幂等重跑、③ hand-off 批次引用。且 STOR-07 的 `scan` 不支持 `--source-change` 过滤。

**命中镜**: Eng-H1 + design-voice-#2 + 对抗①-F3 + 对抗②-F4（四面收敛）

**裁决**: **采纳**。需设计 sweep 替代方案，不能简化为"换调用路径"。

### H-2. determinism-guards / recorder-root-resolution / spec-workflow 三份 spec 未打 delta

**命中镜**: CEO-F + Eng-H2 + 对抗①-F1 + domain-BASE-08（四面收敛）

**裁决**: **采纳**。合并 CR-3 处理，补三份 spec 的 MODIFIED/REMOVED delta。

### H-3. evidence 参数无落点——frontmatter 无字段、流程无写入步骤

**问题**: STOR-06 强制 FIXED 必须 `--evidence`，但 C7 schema 无 evidence 字段，set-status 流程五步无一步把 evidence 写到任何位置。

**命中镜**: HR-TG-#1（独家发现）

**裁决**: **采纳**。补 evidence 落点（追加至 body 或补 schema 字段）。

### H-4. todo DONE 门禁静默消失

**问题**: v1 SKILL.md 要求 todo DONE 必须 `--evidence`，v2 STOR-06 只要求 bug FIXED 必须 evidence。decision-memo 未记录此行为回退。

**命中镜**: HR-TG-#2（独家发现）

**裁决**: **采纳**。确认是有意删除还是遗漏，补 decision-memo 条目。

### H-5. git mv 对未 git add 的文件 fatal 失败（已实测复现）

**问题**: `add` 流程无 `git add` 步骤 → `add` 后立即 `set-status --to FIXED` → `git mv` fatal exit 128。

**命中镜**: HR-TG-#3 + 对抗①-F4（独立实测复现）+ Eng-C2

**裁决**: **采纳**。add 流程补 `git add`，set-status 补非 git 降级。

### H-6. batch PLANNED 数据无撤离出口——34 条人工判断记录裸删

**命中镜**: CEO-A/B + 对抗②-F5（三面收敛）

**裁决**: **采纳**。tasks 补撤离任务（迁移进 issue body 或存档）。

### H-7. 测试清理过猛——格式无关不变量测试误删

**问题**: tasks 5.3 一刀切删旧测试，但仓根解析、Windows 编码、覆盖率门禁测试与存储格式正交。

**命中镜**: CEO-G + Eng-H3 + domain-BASE-01

**裁决**: **采纳**。5.3 拆分：格式耦合删 / 格式无关改造保留。

### H-8. 消费方清单不全

**漏项**: AGENTS.md、sdflow-init/assets/snippets/claude-section.md、openspec/CONTEXT.md、spec-workflow/spec.md。

**命中镜**: Eng-H4 + 对抗①-F1 + domain-BASE-01

**裁决**: **采纳**。补进 Impact/tasks。

### H-9. change→resolved_by 字段映射语义不可靠

**问题**: B23 的 `change: main` 但真正修复者是 `fix-windows-encoding-crash`。131 个终态 issue 中仅 60% 有可提取的变更日期。

**命中镜**: design-voice-#3（独家发现）

**裁决**: **采纳**。改为 body 提取优先 + change 字段兜底 + 统计报告分桶。

### H-10. 无 Alternatives Considered / ADR 三镜分析

**命中镜**: CEO-D + domain-BASE-12

**裁决**: **采纳**。decision-memo 补候选方案对照（至少含维持现状+优化 vs 单文件模型）。

---

## MEDIUM Findings

### M-1. closed_date 来自 body 自由文本，非结构化保证

对抗②-F6 修正了 Eng-C4：v1 确实在 body 里追加状态变更行（`_build_effective_snapshot` 有 blockquote 模式），但不是 schema 级字段。design.md 应明确这是已知不精确的近似值。**裁决**: 采纳，降级处理（改措辞 + 记 known limitation）。

### M-2. git mv 与原子写顺序制造崩溃窗口

HR-TG-#4。step 4 做 git mv → step 5 写 frontmatter → 中间被杀 → closed/ 里文件 status 仍是旧值。**裁决**: 采纳，design 指定操作顺序。

### M-3. reopen 与 STOR-02 不变量冲突

HR-TG-#5。手动 git mv 回 open/ 不改 status → 不变量破坏。**裁决**: 采纳，spec 补声明"reopen 时 MUST 同时改 status"或 reindex 补位置↔状态一致性检测。

### M-4. migrate 绕过 STOR-06 证据/理由门禁

HR-TG-#6。迁移产出的 WONTFIX/FIXED 文件可能缺 reason/evidence。**裁决**: 采纳，spec 补迁移数据的显式豁免声明或回填步骤。

### M-5. frontmatter 解析器策略未定

对抗①-F5。ADR-0025 明确 reject PyYAML（零依赖），design.md 未延续此决策。**裁决**: 采纳，decision-memo 补条目。

### M-6. SKILL.md 565 行重写被低估为一条任务

Eng-M2。tasks 4.1 压缩过度，建议拆分。**裁决**: 采纳，建议拆分。

### M-7. 时序可执行性三处阻塞

domain-BASE-27。第 1 小时撞锁去留空白、第 2-3 小时撞双格式去重、第 4-5 小时撞消费方漏项。**裁决**: 上述 CR/H 修复后此项自然消解。

---

## 已裁掉（反静默压制）

| # | 原始发现 | 裁掉理由 |
|---|---------|---------|
| X-1 | 接地镜：287 数字不符（声称 163） | **证伪**——接地镜未能正确计数两种格式。实测 B1-B23(23) + T1-T264(264) = 287，与 proposal 吻合 |
| X-2 | 接地镜：脚本未实现/目录未迁移等 2-6 | **范畴错误**——这是设计审（阶段二），不是代码审。design 描述的是目标态，当然尚未实现 |
| X-3 | Eng-L1：POOL_SPEC 单源纪律应保持 | **降级为 best-practice**——v2 schema 更简单，内联常量风险低 |
| X-4 | Eng-L2：frontmatter re-write byte stability | **降级为 nice-to-have**——当前用例不强依赖 byte-identity |

---

## 决策登记区

### 自动决策

| # | 决策 | 分类 | 理由 |
|---|------|------|------|
| D1 | CR-1~5 全部采纳为阻塞级 | Mechanical | 四面以上收敛 + 有实证/语料/实测证据 |
| D2 | H-1~10 全部采纳 | Mechanical | 各自有 ≥2 面独立命中 |
| D3 | M-1~7 全部采纳但不阻塞 | Mechanical | 可在 CR/H 修复时顺带处理 |
| D4 | gstack-review.md 的 autoplan 自动决策（D1-D4）纳入 | Mechanical | 已验证与多镜结论一致 |

### 需拍板

| # | 问题 | 选项 |
|---|------|------|
| Q1 | 并发锁去留（CR-1）| A) 移植缩窄版锁（推荐，成本低，消灭已知 bug 类） B) 显式接受风险（记 decision-memo，限定单写者场景） |
| Q2 | todo DONE 是否保留 evidence 门禁（H-4）| A) 保留（与 v1 一致） B) 显式移除（补 decision-memo 理由） |
| Q3 | YAML 序列化策略（CR-5）| A) 手写有界子集 + 值一律加引号（推荐，零依赖） B) 引入 PyYAML |
| Q4 | sdflow-done sweep 替代方案（H-1）| A) scan 补 `--source-change` 过滤 + hand-off 改为列 ID（推荐，简单） B) 保留简化版 sweep 命令 |

---

## Outside-Voice 锚

<!-- sdflow:outside-voice v1 site="design-voice" guard="file-missing" host="claude" runner="claude" reason_code="exec-error" findings="3" truncated="false" -->

design-voice（同族 fallback，reason_code=exec-error）：3 条 findings（迁移格式检测 CRITICAL + sweep 能力丢失 CRITICAL + resolved_by 语义不可靠 HIGH）。仅补偿 outside-voice 切片，广审其余镜仍由 autoplan 覆盖。

<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="claude" reason_code="exec-error" findings="6" truncated="false" -->

hr-tg（同族 fallback，reason_code=exec-error，HR-TG∩={TG-09}）：6 条 findings（evidence 落点缺失 CRITICAL + todo DONE 门禁 HIGH + git mv 未 tracked HIGH + 操作顺序 MEDIUM + reopen 不变量 MEDIUM + migrate 绕过门禁 MEDIUM）。

<!-- sdflow:declared-sites v1 declared="design-voice,hr-tg" -->

## Lens Metrics

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="12" 采纳="12" 裁掉="0" defer="0" 独立="4" sev="致5/高5/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="11" 采纳="11" 裁掉="0" defer="0" 独立="1" sev="致2/高7/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="0" sev="致2/高4/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="claude" site="design-voice" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="claude" site="hr-tg" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="5" sev="致0/高3/中3/低0" -->

---

## 收敛建议

**不建议当前版本直接进入设计 HARD-GATE**。5 条 CRITICAL 中：
- CR-1（并发锁）和 CR-5（YAML 转义）需要 design.md 新增段落 + decision-memo 条目
- CR-2（迁移去重）需要重写 MIG-01 的解析策略和 Scenario
- CR-3（spec-workflow）和 CR-4（CI workflow）需要扩充 Impact/tasks

建议：先按 CR-1~5 + H-1~10 修改四件套 → 窄复核 → 再拍板进设计门。

---

**设计门已拍板批准，日期 2026-08-03。** CR-1~5 和 H-1~10 已回流修改四件套（commit 266f53f，标 `[spec-review-amendment]`），Q1~Q4 均按推荐方案裁定。
