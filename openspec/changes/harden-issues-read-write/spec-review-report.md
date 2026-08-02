# spec-review-report — harden-issues-read-write

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="none" declared="" evidence="本 change 不涉及安全/权限/迁移/API 变更" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->

## 评审摘要

**评审对象**：`openspec/changes/harden-issues-read-write/`（issues 台账读写路径加固 T231+B12）

**镜子配置**：领域镜×1（backend BE-04/BE-05）+ 对抗镜×2（隐藏假设 / 失败模式）+ 接地镜×1 + autoplan 广审（CEO 双声 Claude+Codex）+ 设计 outside-voice×1

**整体判定**：设计存在 3 处高严重度架构缺陷，**不建议原样进入实现**。核心问题是四件套统一遗漏了跨进程消费边界（`validate_scan_envelope`），且 D2 总项数守卫的度量方法量纲错误。需先修正 design/spec/tasks 再拍板。

---

## Findings（按严重度排序，去重合并后）

### R1 [高·5 镜收敛] `validate_scan_envelope` 是真正的 reindex 崩溃点，设计遗漏 consumer 侧

**问题**：design 和 spec 说在 `_build_effective_snapshot`（core 层）追加 `problems.append` 实现"显红不罢工"。但实际数据流是 core → 子进程 JSON → `validate_scan_envelope`（`issues.py:437-440`）**硬 raise ValueError** 拒绝 `status not in status_values`。只改 core 不改 consumer 边界 → spec 承诺的"`_scan_pool` 正常返回"无法兑现。且 `cmd_reindex`（`issues.py:637`）只 `except RuntimeError`，`ValueError` 不是其子类，会原样冒出 `SystemExit(2)` → reindex 整体中止，比现状的 `_die` 还难看。

**证据**：`issues.py:437-440`（硬 raise）、`issues.py:604-623`（`_reindex_core` 无对应 catch）、`issues.py:632-648`（`cmd_reindex` 只捕 `RuntimeError`）。T231 原票（`todolist/2026-07-todolist.md:2383`）已正确指出此处，design 反而丢失了线索。

**命中镜**：Codex-CEO 项 4、对抗镜 1 F1、对抗镜 2 F1、outside-voice 项 1（overlay 维度）

**建议**：[spec-review-amendment] `validate_scan_envelope` 的 status/specific_field 枚举检查需同步降级为 problems 收集 + 继续。Task 1 范围须扩大到 `issues.py`。

---

### R2 [高·5 镜收敛] D2 总项数守卫计数口径错误，guard 结构性偏松

**问题**：`generate_index_md`（`issues.py:530-581`）只把 open 项渲染为逐行表格，closed 项仅输出聚合摘要行（"共 N 项已闭合"）。tasks.md 2.1 指示"读旧 INDEX.md 计 `| T/B` 行数"只能数到 open 项。而 `new_count = len(items)` 是 open+closed 全量。量纲不一致 → `new_count` 系统性 ≥ `old_count`，guard 几乎永不触发。

**实测验证**（本仓）：`grep -c '^| [A-Z][0-9]* |' openspec/issues/INDEX.md` → 174（open），"共 113 项已闭合" → 总计 287，但行数法只数到 174。

**更致命的边界**：若所有项都是终态（open=0），行数法 old_count=0 → 被 spec 的"首次建"场景跳过校验 → 恰好在最该生效的状态下完全失能。

**命中镜**：Claude-CEO 项 1、Codex-CEO 项 1+2、领域镜 F-D2、对抗镜 1 F2、对抗镜 2 F2

**建议**：[spec-review-amendment] `_count_index_items` 必须同时解析 open 行数 + "共 N 项已闭合"聚合行的 N，或改用不依赖渲染产物反解析的可靠信号源。ID 超集检查（gstack F1 建议）也受同一盲区影响（closed ID 不在 INDEX），需二段式校验。

---

### R3 [高·3 镜收敛] C4 验证结论为假：sweep 调 triage，D3 会静默改变 sweep 行为

**问题**：decision-memo C4 断言"sweep 不经 triage，直接调 `set-status --to PROPOSED`"。但 `cmd_sweep`（`issues.py:1126-1132`）实际通过子进程调用 `triage` 子命令 → `_bug_triage`/`_todo_triage` → 正是 D3 要改的两个函数。D3 落地后 sweep 把非终态非 PROPOSED 项归入批次时**不再推进状态到 PROPOSED**——这个行为变化从未被评估。

**额外影响**：
- SKILL.md 三处（:392, :411, :495）描述了 triage 的 PROPOSED 推进行为 → 改后过期
- `__init__.py:2117` 的 `--help` 文案过期
- todo 池 `_todo_triage` 的 marker block 补建逻辑依赖 `history` 非空（= 状态变化），D3 后 `history` 恒为空 → marker-less 首次分批不再补建 marker block（对抗镜 2 F5）

**命中镜**：领域镜 F-D1、对抗镜 1 F3、对抗镜 2 F4+F5、outside-voice 项 2

**建议**：[需拍板] 三选一：(a) 只在 `cmd_batch_add` 层做不碰 status，保留 triage 原行为；(b) 保留删 `open_untriaged`，但把 sweep 改走 `set-status` 而非 triage（新 task）；(c) 接受 sweep 行为变化 + 同步更新 SKILL.md 三处 + help 文案 + 补 sweep 端到端测试 + 处理 marker block 副作用。

---

### R4 [中·3 镜收敛] design/spec/tasks 引用不存在的函数名 `_scan_pool`

**问题**：三份文档统一引用 `_scan_pool` 的自检段（`__init__.py:842-887`），实际位于 `_build_effective_snapshot`（`__init__.py:826-901`）。`_scan_pool` 是 `issues.py:444` 的跨进程调用函数。

**命中镜**：接地镜、Claude-CEO 项 5、对抗镜 1 F1

**建议**：[spec-review-amendment] 统一改为 `_build_effective_snapshot`。

---

### R5 [中·3 镜收敛] SKILL.md / help 文案未同步更新

**问题**：D3 落地后，SKILL.md:392/411/495 和 `__init__.py:2117` 的 help 文案描述的 triage 行为不再存在。本 change 立意是消除撒谎，却会用新谎言替换旧谎言。

**命中镜**：对抗镜 1 F3、对抗镜 2 F4、outside-voice 项 2

**建议**：[spec-review-amendment] tasks.md 需新增文档同步任务（依赖 R3 拍板方向）。

---

### R6 [中·2 镜收敛] design §2 "需确认"悬问未闭环

**问题**：design.md §2 写"downstream 的 `generate_index_md` / `sync_batches_md` 是否会炸——需要确认"，decision-memo 写"Open Questions：无"。实际读码确认不会炸（`_is_terminal` 用 `.get` 兜底），但结论未回写 design。

**命中镜**：Claude-CEO 项 4、Codex-CEO 项 4

**建议**：[spec-review-amendment] design §2 改为已确认结论，去掉"需要确认"。

---

### R7 [低·1 镜] D1 代码 falsy 短路漏掉空字符串脏值

**问题**：design 给出的 `if item.get(sf) and item[sf] not in spec.specific_values` 在 `item[sf]` 为空字符串时跳过校验，与 spec.md Requirement 文本不一致（后者无"非空"限定）。

**命中镜**：对抗镜 1 F4

**建议**：[spec-review-amendment] 去掉 falsy 短路，或在 spec 里显式声明空值处理。

---

### R8 [中·1 镜] 新守卫与既有 D3（禁读旧 INDEX）架构决策冲突

**问题**：`generate_index_md` docstring 明确声明"禁读旧 INDEX（D3）"。Task 2 要求 `_reindex_core` 读旧 INDEX → 正是 R2 脆弱性的根源（渲染产物反解析）。四件套未提及此架构冲突。

**命中镜**：对抗镜 2 F3

**建议**：[需拍板] 如采纳 R2 的"换信号源"建议（不从 INDEX.md 反解析），此冲突自动消解。

---

### R9 [中·1 镜] todo 池 marker-less 首次分批不再补建 marker block

**问题**：`_todo_triage` 的 `elif history:` 分支在 D3 后恒为 False → marker block 不再补建。

**命中镜**：对抗镜 2 F5

**建议**：[spec-review-amendment] 若采纳 R3 方案 (c)，需评估此副作用并补测试。

---

### R10 [低·1 镜] 旧 INDEX 不可解析时降级路径未定义

**问题**：spec 未定义"旧 INDEX 存在但无法解析"的场景，可能把 reindex 从"自愈覆盖"变成"永久卡死"。

**命中镜**：对抗镜 2 F6

**建议**：spec 补场景——旧 INDEX 不可解析 → 跳过校验 + 记 problem 警告。

---

## 决策登记区

### [自动决策] D-auto-1: autoplan premise gate
本 change 的前提（三处诚实性缺陷 + 一个数据丢失 bug，来自实战报告）经双声验证成立，自动接受。

### [自动决策] D-auto-2: scope 判断
不扩大（blast radius 内无需扩展），不缩小。

### [自动决策] D-auto-3: Codex 项 3（显红不中止 vs 严格模式分离）
`reindex --strict` 已存在（`issues.py:647`），自动化可选传 `--strict`。接受当前设计。

### [自动决策] D-auto-4: Codex 项 6（triage 语义历史审计）
Non-Goals 已排除迁移，历史 PROPOSED 数据量小，影响低。接受不迁移。

### [需拍板] Q1: R3 — triage 解耦的影响半径

**三选一**（详见 R3 建议）：
- **(a)** 只在 `cmd_batch_add` 层做不碰 status，保留 triage 原行为
  - 系统镜：改动面最小，sweep/triage 行为不变，SKILL.md 不用改
  - 用户镜：batch add 和 triage 行为分离，triage 仍会推进状态
  - 开发循环镜：最简单，但 proposal 的"越权"判断只在 batch add 层解决
  - **主次判定：最小侵入，推荐**
- **(b)** 保留删 `open_untriaged`，sweep 改走 `set-status`
  - 新增 task，改动面扩大到 `cmd_sweep`
- **(c)** 接受 sweep 行为变化 + 全面同步
  - 影响最大，但彻底贯彻"归批次≠改状态"哲学

**推荐 (a)**，理由：proposal 的原始痛点是"batch add 时强推 status"，而非"triage 命令本身不该推进状态"。方案 (a) 精确修复痛点，不引入连锁改动。

### [需拍板] Q2: R2 — 总项数守卫的度量方法

**两选一**：
- **(a)** 修正 `_count_index_items`：同时解析 open 行数 + "共 N 项已闭合"聚合行的 N
  - 系统镜：依赖 INDEX.md 渲染格式稳定，与 D3"禁读旧 INDEX"有张力
  - **主次判定：快速修复，R8 冲突是已知代价**
- **(b)** 换信号源：上次 scan 的条目数写入旁路文件（如 `.reindex-baseline`）
  - 系统镜：与 D3 不冲突，不依赖渲染产物
  - 开发循环镜：新增一个状态文件的读写，略复杂
  - **主次判定：更干净但成本稍高**

**推荐 (a)**，理由：按基准④最简方案，INDEX.md 的 closed 聚合行格式由 `generate_index_md` 自己控制（同仓同文件），格式漂移概率极低。

### [需拍板] Q3: R12 — overlay 格式是否也需词表检查

outside-voice 指出 overlay 文档中已被 frontmatter 接管的 legacy 表行也可能有脏 status。

**推荐：不扩大**。overlay 格式的 frontmatter 有 YAML schema 校验（`_validated_rendered_mutation`），脏值进不来。legacy 表行被 `frontmatter_keys` 排除后不进 `effective_items`，不影响盘点数字。Non-Goals 明确排除了写入路径改造。

### [已裁掉] X1: INDEX/batches 双写无事务边界
领域镜 F-D4。裁掉理由：既有代码未触碰，reindex 幂等可重跑收敛。且在本 change scope 外。

### [已裁掉] X2: consumer 仓升级路径
Claude-CEO/Codex-CEO 共同指出。裁掉理由：不阻塞本 change，属 hand-off 建议。defer 到 hand-off.md。

### [已裁掉] X3: legacy 格式 sunset
Claude-CEO/Codex-CEO。裁掉理由：属 roadmap 级别决策，不在本 change scope。记 todolist。

---

## [spec-review-amendment] 四件套修订

基于 R1/R2/R4/R6/R7 的采纳裁决，以下修订需在拍板后落盘。R3/R5/R9 的修订方向依赖 Q1 拍板结果。

**待修订项**（拍板后执行）：
1. design.md §1：`_scan_pool` → `_build_effective_snapshot`，行号更正（R4）
2. design.md §2："需要确认"改为已确认结论（R6）
3. design.md 新增 §1.5：`validate_scan_envelope` 枚举检查同步降级（R1）
4. design.md §3：计数口径修正说明（R2，依赖 Q2 拍板方向）
5. spec.md Requirement 1：函数名更正 + 扩大到 `validate_scan_envelope`（R1+R4）
6. spec.md Requirement 2：计数口径修正（R2）
7. tasks.md：Task 1 范围扩大到 `issues.py`；Task 2 计数方法修正；新增 Task 5 文档同步（R5，依赖 Q1）
8. decision-memo C1：改动面扩大到 `issues.py` 的 `validate_scan_envelope`
9. decision-memo C4：修正验证文本（R3，依赖 Q1 拍板方向）

---

## 度量锚

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="9" 采纳="9" 裁掉="0" defer="0" 独立="4" sev="致0/高3/中4/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="5" 采纳="3" 裁掉="0" defer="2" 独立="0" sev="致0/高1/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="3" 采纳="2" 裁掉="1" defer="0" 独立="0" sev="致0/高2/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="7" 采纳="5" 裁掉="0" defer="2" 独立="0" sev="致0/高3/中2/低0" -->

## outside-voice 锚

<!-- sdflow:outside-voice v1 site="design-voice" guard="section-not-found" host="claude" runner="codex" reason_code="ok" findings="2" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="design-voice" -->

## 收敛建议

本报告发现 3 条高严重度架构缺陷（R1/R2/R3），均被 ≥3 个独立镜子收敛命中。**不建议原样拍板进入实现**。

建议流程：
1. 人工拍板 Q1/Q2/Q3 三个决策点
2. 据拍板结果执行上述 amendment
3. 拍板批准 → 进设计 HARD-GATE

