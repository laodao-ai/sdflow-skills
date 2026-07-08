# sdflow 工作流全景图

> **盘面即状态**：一张表看全 sdflow OpenSpec 工作流——每个阶段由哪个 skill 编排、触发哪个确定性脚本门、产出携带什么 `frontmatter` 锚的产物，以及每个门检查哪些字段、判据与退出码是什么。
>
> 本文是 [`workflow-map.html`](workflow-map.html) 的 markdown 对应版（可 diff / tracked）。所有条目接地自源码并附 `file:line`；**视图文档，非真相源**——改源前先核对，源码变更后需同步本文。
>
> **叙事伴读**：想按「阶段故事」而非「字段速查」理解全流程 → [workflow-overview.md](workflow-overview.md)（人类向详解）· [workflow-console.html](workflow-console.html)（可视化控制台）。本文侧重结构化映射（字段 × 脚本 × 判据），那两份侧重流程叙事，互补不重叠。

**速览**：14 确定性脚本 · 3 报告 frontmatter 字段 · 4 类正文 v1 锚 · 12 ship_gate 裁决 · 2 人类门 · 判官 `ship_gate.py`（只读零副作用）。

---

## 1. 端到端管线

四层对应：**阶段 → 编排 skill → 脚本门/门禁 → 产物 + frontmatter 锚**。两个人类门之外，阶段三 `ship` 由 `ship_gate.py` 逐步驱动、无人类门（P3e）。

```
 阶段          编排 skill                    脚本门 / 门禁                        产物 + frontmatter 锚
════════════════════════════════════════════════════════════════════════════════════════════════════
 explore  ──▶  /opsx:explore                （无门）                              探索笔记
                   │
 propose  ──▶  /opsx:ff / :new    ──FF-0──▶ trigger-catalog TG 判定             proposal/design/specs/tasks
                   │                          git checkout -b feat/{change}
                   ▼
              ┏━━━━━━━━━━━━━━━┓
   人类门①    ┃  grill / 前提确认  ┃  ◀── ship 不跨此门 (adr/0004)
              ┗━━━━━━━━━━━━━━━┛
                   │
 spec-review ─▶ sdflow-spec-review  ──▶  anchor_lint.py --layer spec-review ✅#1  spec-review-report.md
  (设计审)    autoplan+领域/对抗/接地镜        outside-voice.sh · HR-TG cross-model    └─ frontmatter:
                   │                                                                    ship-gate.design_approved: true
                   ▼
              ┏━━━━━━━━━━━━━━━━━━━━━━┓
   人类门②    ┃  设计 HARD-GATE  design_approved:true  ┃ ◀═══ 唯一机判 pre-flight 锚
              ┗━━━━━━━━━━━━━━━━━━━━━━┛     REFUSE_START(3) 若未过门
                   │
   ══════════ 阶段三 ship（gate 驱动·无人类门 P3e）══════════════════════════════════════════
                   │      ┌──────────────────────────────────────────────────────┐
   sdflow-ship ────┤      │ 每步前后 MUST 调 ship_gate.py（盘面即状态·只读零副作用） │
  (meta-orch)      │      │ 步前:「NEXT 谁+前置缺啥」 步后:「产物落没+门禁结论」      │
                   │      └──────────────────────────────────────────────────────┘
                   │
     RUN_SOP(0)────▶ embedded-test-sop        tg02_hit (TG-02 声明式)             {change}-sop.md
     RUN_PLAN(0)───▶ writing-plans            TAG_RE checkpoint 契约              superpowers-plan.md
   CONTINUE_IMPL(0)▶ subagent-driven-dev      done_ids⊇plan_ids (集合归属)        checkpoint(task<N>-) 提交
                   │                          注入点B 即时修复闭环
 RUN_CODE_REVIEW(0)▶ sdflow-code-review  ──▶  anchor_lint --layer code-review ✅#2  code-review-report.md
                   │  置信<80过滤·T10自动裁    trivial_shape.py · outside-voice     └─ frontmatter:
                   │                          BLOCKED_UPSTREAM(4) 若 blocked          ship-gate.code_review: pass|blocked
     RUN_VERIFY(0)─▶ sdflow-done              verify=唯一终门(每✅须机验锚点)      verify-report.md
                   │  verify→handoff→archive   VERIFY_FAIL(5) 若核心缺口             └─ frontmatter:
                   │  →commit→merge            issues.py sweep · openspec archive     ship-gate.verify: PASS|FAIL
                   │                          merge 前 untracked 硬检查(SR-2)      hand-off.md
                   ▼
 archive+merge ──▶ (done 内 ff-only)          active 缺席+base可达+verify=PASS     archive/{date}-{change}/
                   │                          ══▶ SHIPPED(0)  │ 异常 ▶ UNKNOWN(6)
   ═══════════════════════════════════════════════════════════════════════════════════════
                   │
 retro ─────────▶ sdflow-retro (只读)         retro_report.py / lens_metric_agg    openspec/retro/report.md
                   │                          成本(墙钟)×价值(lens-metric锚)·只呈现
 maintain ──────▶ sdflow-maintain             扫目录 vs INDEX·AskUserQuestion 确认  openspec/INDEX.md (+N -M)
```

### 阶段表

| # | 阶段 | 编排 skill | 脚本门 / 门禁 | ship_gate verdict（exit） | 产物 + frontmatter 字段 | anchor-lint |
|---|------|-----------|--------------|--------------------------|----------------------|-------------|
| 0 | explore | `/opsx:explore` | 无门 | —（不覆盖） | 探索笔记 | — |
| 1 | propose | `/opsx:new` `/opsx:ff` | FF-0 分支 + TG 判定 | — | proposal/design/specs/tasks | — |
| — | **人类门①** grill | （propose/explore 内） | 人类拍板 | ship 不跨（adr/0004） | grill 记录进正文 | — |
| 2 | **spec-review 设计审** | `sdflow-spec-review` | `anchor_lint --layer spec-review` ✅#1 · outside-voice · HR-TG | 未过 → **REFUSE_START(3)** | `spec-review-report.md` → `design_approved: true` + lens-metric 锚 | ✅ #1 |
| — | **人类门②** 设计 HARD-GATE | `sdflow-spec-review` 收敛口 | `design_approved: true`（机判锚） | REFUSE_START(3) 若未过 | 拍板后 prepend 头部 frontmatter | — |
| 3a | ship·条件 SOP | `embedded-test-sop` | `tg02_hit`（TG-02 声明式） | **RUN_SOP(0)** | `{change}-sop.md` | — |
| 3b | ship·plan | `superpowers:writing-plans` | `TAG_RE` checkpoint 契约 | **RUN_PLAN(0)** | `superpowers-plan.md` | — |
| 3c | ship·实现 | `subagent-driven-development` | 完成集 = checkpoint ∪ 复选框（集合归属） | **CONTINUE_IMPL(0)** | `checkpoint({change}:task<N>-…)` 提交 | — |
| 3d | ship·代码审 | `sdflow-code-review` | `anchor_lint --layer code-review` ✅#2 · `trivial_shape` · outside-voice | **RUN_CODE_REVIEW(0)**；blocked → **BLOCKED_UPSTREAM(4)** | `code-review-report.md` → `code_review: pass\|blocked` | ✅ #2 |
| 3e | ship·收尾 | `sdflow-done` | verify=唯一终门（每 ✅ 须机验锚点）· `issues.py sweep` · `openspec archive` · merge 前 untracked 硬检查 | **RUN_VERIFY(0)**；FAIL → **VERIFY_FAIL(5)**；陈旧 → **RERUN_STALE(0)** | `verify-report.md` → `verify: PASS\|FAIL` + `hand-off.md` | — |
| 4 | archive + merge | `sdflow-done`（内部） | `openspec archive` + ff-only | active 缺席+base可达+PASS → **SHIPPED(0)**；异常 → **UNKNOWN(6)** | `archive/{date}-{change}/` | — |
| 5a | retro 复盘 | `sdflow-retro`（只读） | `retro_report.py` / `lens_metric_aggregate.py` | 不受 ship_gate 管 | `openspec/retro/report.md`（D12 待复评区块） | — |
| 5b | maintain 一致性 | `sdflow-maintain` | 扫目录 vs INDEX · 改前 AskUserQuestion | 不受 ship_gate 管 | `openspec/INDEX.md`（+N −M） | — |

**两个人类门**：① grill（前提确认，ship 不跨，adr/0004 红线）；② 设计 HARD-GATE（`design_approved: true`，`/sdflow-ship` pre-flight 唯一机判锚）。**阶段三过设计门后无人类门（P3e）**——能修当场修、≥2 方案按 T10 三级协议自动选、拿不准 defer；`sdflow-done` verify 是去人类门后的唯一终门（强档 + Do-Not-Trust 冷启堵假 ✅）。

---

## 2. ship_gate 裁决 × 退出码

`ship_gate.py` 从盘面（committed 产物 + frontmatter 锚）确定性推导下一步。退出码承载门禁语义。契约表 `ship_gate.py:32-44`。

| verdict | exit | 含义 |
|---------|:----:|------|
| REFUSE_START | **3** | 未过设计门 / change 不存在 |
| RUN_SOP | 0 | TG-02 命中且 sop 缺 |
| RUN_PLAN | 0 | plan 缺 → writing-plans |
| CONTINUE_IMPL | 0 | plan 号集 ⊄ 完成集 |
| RUN_CODE_REVIEW | 0 | 代码审报告缺 |
| BLOCKED_UPSTREAM | **4** | `code_review = blocked` |
| RUN_VERIFY | 0 | verify 缺 / 待收尾 |
| VERIFY_FAIL | **5** | `verify = FAIL` 且未陈旧 |
| RERUN_STALE | 0 | 结论陈旧 → 重跑 `next` 步 |
| STEP_IN_PROGRESS | 0 | 报告在但无结论锚 |
| SHIPPED | 0 | 归档已并 base + verify=PASS |
| UNKNOWN | **6** | 多锚冲突 / 坏 frontmatter / 空壳归档 fail-safe |

退出码严重度：**0** 可推进 · **3/4** 拒绝/阻塞 · **5** verify 失败 · **6** 判定不能。

---

## 3. 报告 frontmatter 与正文锚

三份报告各落一个 `ship-gate.*` frontmatter 字段（下划线命名防连字符漂移，prepend 头部首块）；正文另有 4 类 v1 锚由 `anchor_lint` 机验。单一源 = `ship_gate.py` `FIELD_ENUMS` + `lens-metric-contract.md`。

### 3.1 frontmatter schema

| 字段 | 取值域 | 承载文件（producer） | 判断/说明 | file:line |
|------|--------|---------------------|-----------|-----------|
| `design_approved` | `true` \| `false`（严格 bool，`yes/1/True`→bad-type） | `spec-review-report.md`（sdflow-spec-review 拍板回写） | live pre-flight 唯一门；absent → REFUSE_START(3) | `ship_gate.py:20,289`; spec-review SKILL:108 |
| `verify` | `PASS` \| `FAIL`（大写，带引号 `"PASS"`→out-of-domain） | `verify-report.md`（sdflow-done verify 步） | 归档 PASS 是 SHIPPED 判据 | `ship_gate.py:21,291`; done SKILL:76 |
| `code_review` | `pass` \| `blocked`（小写） | `code-review-report.md`（sdflow-code-review） | blocked → BLOCKED_UPSTREAM(4) | `ship_gate.py:22,292`; code-review SKILL:165 |

**坏 frontmatter 分类**（live → UNKNOWN(6) fail-closed；归档不可变 → fail-safe `none`）：

| 类别 | 触发 |
|------|------|
| `out-of-domain` 越域 | 值不在 enum（含引号值） |
| `duplicate-key` 重复键 | 顶层 `ship-gate:` >1 次，或同字段重复 |
| `bad-type` | 顶层带内联标量/inline map；字段行无 `:`；bool 非规范 |
| `tab-indent` | 缩进含 `\t` |
| **absent**（非坏，走无锚语义） | 无首块 · 首行 `---` 无闭合 · 有 frontmatter 无 `ship-gate:` 键 · 嵌套子键 · 外来字段 |

> 仅认文件**首块**（去 BOM，第二块忽略）。`ship_gate.py:295-345`

### 3.2 报告正文 4 类 v1 锚

`anchor_lint` 机验：存在性 + 字段 + enum + `layer==--layer`。

| 锚 | 字段 | 取值域 |
|----|------|--------|
| `step1-broad-review` | `mode` | `native` \| `simulated` |
| `hr-tg` | `hit`, `evidence` | `hit="TG-xx,…"` \| `"none"`；`evidence`=判据触发点（命中必填） |
| `outside-voice` | `site`,`guard`,`runner`,`reason_code`,`findings`,`truncated` | `runner` ∈ `codex`\|`claude-fallback`；`guard` ∈ none\|file-missing\|section-not-found\|zero-findings\|stale\|simulated-source；`truncated` ∈ true\|false |
| `lens-metric` | `layer`,`lens`,`runner`,`site`,`findings`,`采纳`,`裁掉`,`defer`,`独立`,`sev` | 见下表（受 config `metrics.enabled` 门控） |

**lens-metric enum**（唯一源 = `lens-metric-contract.md`）：

| 字段 | 取值域 |
|------|--------|
| `layer` | `spec-review` \| `code-review`（== `--layer`） |
| `lens` | `domain` \| `adversarial` \| `grounding` \| `history` \| `outside-voice` \| `broad` |
| `runner` | `claude` \| `codex` \| `claude-fallback` |
| `site` | `code-voice` \| `hr-tg` \| `design-voice` \| `—`（仅 outside-voice 消歧，不入 lens enum） |
| `findings`/`采纳`/`裁掉`/`defer`/`独立` | int ≥ 0（独立 = 唯一报过 ∧ 被采纳，折叠到 lens 后计） |
| `sev` | `致N/高N/中N/低N`（四级定序，零也写 0，分隔恒 `/`，仅采纳项计入） |

---

## 4. 确定性脚本清单

14 个脚本（含 1 个计划未建）。**bundle** = 经 `sdflow-init update` 铺进消费仓 `openspec/workflow/tools/`；**skill-local** = 仅本仓 skill 目录、走 symlink。注意 `ship_gate.py` 是 skill-local（不随 bundle 回灌）。

| 脚本 | 阶段 | 触发 skill | 检查字段/输入 | 判据 & 退出码 | 分发 | file:line |
|------|------|-----------|--------------|--------------|------|-----------|
| **ship_gate.py** | ship（全程判官） | sdflow-ship | 四件套路径 · plan 号集 · 三报告 frontmatter · checkpoint/复选框完成集 · 归档 verify 锚 | 顺序门链；**0** 推进 / **3** REFUSE / **4** BLOCKED / **5** VFAIL / **6** UNKNOWN | skill-local | `:32-44`,`:647` |
| **anchor_lint.py** | spec-review / code-review | 两审 | 报告文本 + `--layer`；4 类锚 + lens-metric 字段/enum/sev/计数 | fence-aware 行级；**0** CLEAN / **1** 违规 / **2** fail-closed | bundle | `:138`,`:163` |
| **trivial_shape.py** | code-review（Step2 前） | sdflow-code-review | `git diff` 形状 · 行为面路径清单 · 文档扩展名 | 保守偏 NOT_EXEMPT；**0** EXEMPT / **1** 必跑 / **2** ERR→必跑 | bundle | `:183` |
| **lens_metric_aggregate.py** | retro | sdflow-retro（import） | 归档 lens-metric 锚 · layer/lens enum · 五计数 | fence-aware 聚合，view-only（0） | skill-local | `:50`,`:70` |
| **retro_report.py** | retro | sdflow-retro | git 历史（墙钟）· checkpoint→stage 映射 · lens-metric/hr-tg 锚 | 成本×价值 join，只呈现不决策（0） | skill-local | `:146`,`:356` |
| **init.py**（config-lint mode） | setup / maintain | sdflow-init | `config.yaml`：schema · rules(4 子键) · model-tiers ⊆{strong,mid,light} · metrics.enabled ∈{true,false} | fail-closed（条件块缺→放行）；**0** / **1** 违规 | skill-local | `:295`,`:351` |
| **issues.py** | done 收尾 / maintain | sdflow-issues（done sweep 调） | 两池 item(id/status/change/batch) · batches.md · 跨池撞号 | reindex 全量重建 INDEX(幂等) · sweep 非原子可重跑；`_die`→1 | skill-local | `:244`,`:1156` |
| **buglist.py** | 全阶段（记 bug） | sdflow-buglist | STATUS · B-ID 自增 · 表↔块一致 | FIXED 必带 evidence+根因；WONTFIX 必带理由；`_die`→1 | skill-local | `:56`,`:481` |
| **todolist.py** | 全阶段（记债/优化） | sdflow-todolist | STATUS · T-ID 自增 · 表↔块一致 | DONE 必带关联 change/commit；`_die`→1 | skill-local | `:56`,`:336` |
| **test_mirror_consistency.py** | maintain / CI | pytest（守卫） | 三脚本同名 helper 源码 → 剥 docstring 后 `ast.dump` 等价 | 仅真实逻辑分叉拉红（THREE_WAY 6 + TWO_WAY） | skill-local | `:41`,`:87` |
| **resolve-workflow.sh** | setup（规则根解析） | 各 skill 前置 | `--root`；本地 pin vs 全局 canonical bundle | **0** 成功 / **2** 降级 / **64** 用法 | bundle/hack | `:5-7`,`:69` |
| **outside-voice.sh** | spec-review / code-review | 两审 outside-voice 镜 | `--context-file` · secret_scan · codex read-only · timeout 300 | preflight/exec；**0** / **1** err / **3** secret / **124** timeout | bundle/hack | `:5-15`,`:45` |
| **checkpoint-commit.sh** | 全阶段（过场提交） | 各编排 skill | `<step>`+描述 · `git status --porcelain` · 固定 message | 无变更静默跳过；**0** / **2** 用法/非仓 | bundle/hack | `:7-20`,`:39` |
| **log_check.py** | （计划未建） | 拟 embedded-test-sop | 拟：`--log serial.log --rules *.yaml` · 时间窗 · must_contain/not/before · severity rollup | **尚未建**（roadmap mechanical-layer-hardening 阶段4 P5 候选，按需排） | 拟 bundle | roadmap:118 |

---

## 5. issues · config · checkpoint 结构化字段

recorder 数据类脚本 owns 的结构化字段：总览表 ↔ 详细块双写一致由脚本守，状态终态有门禁。

### buglist（`buglist.py:56`）
- **总览表**：`ID · 模块 · 问题摘要 · 优先级 · 状态 · 时间 · 关联Change · 批次`
- **详细块**：现象 · 根因 · 修复方案 · 影响范围
- **STATUS**：`OPEN · VERIFIED · PROPOSED · IN_PROGRESS · FIXED* · WONTFIX* · BLOCKED`（`*` = 终态）
- **优先级**：`P0–P4`
- **门禁**：FIXED 必带 evidence+根因；WONTFIX 必带理由

### todolist（`todolist.py:56`）
- **总览表**：`ID · 模块 · 描述 · 类型 · 状态 · 时间 · 关联Change · 批次`
- **详细块**：动机 · 思路 · 备注（可选，轻量优先）
- **STATUS**：`OPEN · PROPOSED · DONE* · WONTDO*`
- **类型**：性能优化 · 可观测性 · 代码质量 · 功能增强 · 基础设施
- **门禁**：DONE 必带关联 change/commit

### batches.md（`issues.py:437`）
- **标题**：`### {key} — {title}`（key 禁 `|` / 换行 / ` — ` / 首尾空白）
- **状态**（生成行）：`PLANNED · IN_PROGRESS · DONE`
- **成员**（生成行）：`(生成) B1, T2…`（reindex 同步）
- **优先级**（人写）：`P0–P4 | — | <待填>`（batch lint 校验前导 token）
- **计划**（人写）：非占位须非空白

### config.yaml（`init.py:295`）
| 顶层键 | 必填性 | 约束 |
|--------|-------|------|
| `schema` | 无条件必填 | 存在即可 |
| `rules` | 无条件必填 | 含 `proposal`/`specs`/`design`/`tasks` 四子键 |
| `model-tiers` | 条件（存在才校验） | 子键 ⊆ `{strong, mid, light}` |
| `metrics` | 条件 | `enabled` ∈ `{true, false}` |

> 手写 stdlib 行扫描（**禁 import yaml**，消费仓无 PyYAML），坏结构给可读 reason 而非 traceback。

### checkpoint 提交 subject（`ship_gate.py:492` `TAG_RE`）
```
checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-
```
- ✅ 合法：`checkpoint(task3-add-parser)`（裸格式）· `checkpoint(mlh-p5:task12-frontmatter)`（带 namespace，仅 `ns==change` 计入）
- ❌ 非法：`checkpoint(task1)`（缺 `-`）· `checkpoint(MLH:task1)`（大写 ns）· `checkpoint(impl-review)`（缺 `task`，且是失鲜豁免专用 subject）
- 约束：subject 须行首 `startswith("checkpoint(")`；slug（`-` 后）是约定，TAG_RE 不校验

---

## 6. 分发链 · fail-closed 家族 · 重实现守卫

- **两条分发链**：**bundle** = `assets/workflow/tools/` → `~/.sdflow/workflow` → 消费仓 `openspec/workflow/tools/`（anchor_lint / trivial_shape）；**skill-local** = skill 目录整体软链进 `~/.skills`。`ship_gate.py` 属后者——**不随 bundle 回灌消费仓**。

- **fence-aware 三处独立重实现**（禁跨 skill import，消费仓无 sdflow-retro）：`anchor_lint.fence_outside_lines` · `lens_metric_aggregate._fence_aware_lines` · `ship_gate._line_scoped_hits`，各自实现 CommonMark fence 语义。

- **recorder 三镜像守卫**：buglist / todolist / issues 的公共 helper 是人肉同步的三份重实现，靠 `test_mirror_consistency` 剥-docstring-AST-等价守卫防漂移（THREE_WAY 6 + TWO_WAY）。

- **fail-closed 家族**：anchor_lint(enums 缺→2) · trivial_shape(git 失败→2 当必跑) · resolve-workflow(bundle 半坏→2 降级) · config-lint(不可读→违规) · ship_gate(坏 frontmatter→6)。判定不能宁可保守，不假阳/假过。

- **anchor_lint 诚实拦截力**：由**同一落锚的主 session 自跑**、非独立外部门——只挡「同会话内忘记跑这步」，挡不住「整段跳过」。数值一致性（findings/采纳/独立）是主 session 信任边界、非机械可验。

- **规则解析纪律**：三编排 skill 运行时经 `resolve-workflow.sh` 解析 RULES_ROOT（本地 pin 或全局 canonical），不硬编码 `openspec/workflow/`；退出码 2 → 显式降级并转发 stderr，绝不静默。

---

*接地自 sdflow-skills @ `feat/mlh-p5-parser-cleanup`。关键源：`ship_gate.py`（:32-44 契约表 · :647 decide）· `anchor_lint.py` · `trivial_shape.py` · 三编排 `SKILL.md` · `lens-metric-contract.md`。所有字段/判据/退出码均附 `file:line`，改源前先核对本文。*
