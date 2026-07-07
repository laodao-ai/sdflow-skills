## spec-review 报告 — mlh-p1-issues-sweep

> roadmap `mechanical-layer-hardening` 阶段 1（issues.py sweep 原子子命令）。数据类 skill 设计审。

### 命中范围
- **栈**：Python 数据类脚本（issues.py + buglist/todolist recorder + pytest）。领域清单命中 backend.md（BE-02/04/05）+ backend-go.md 可迁移（GO-03/04）。
- **镜**：领域镜(backend) · 对抗镜×2(幂等/过滤/状态 · fail-closed/错误路径/孤儿) · 接地镜(读码核验) · outside-voice(design-voice, codex 跨模型) · broad(step1，模拟——未跑原生 autoplan，跨模型广度由 codex outside-voice 覆盖)。
- **HR-TG 判定**：`hit="none"`——行为对齐既有幂等原语、可逆（reindex 确定性重建、triage 幂等）、无新增数据损坏/安全面（除已由守卫处理的空 change 项）。

<!-- sdflow:step1-broad-review v1 mode="simulated" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="sweep 包装既有幂等原语,可逆(reindex确定性重建),无新增数据损坏/安全面" -->

### 决策登记区

```
┌─────────────────────────────────────────────────────────────────┐
│ [自动决策] 高置信 correctness 修（5源多重命中+接地对码核验，已 amend）│
├─────────────────────────────────────────────────────────────────┤
│ D-a  空 --change "" 误纳孤儿(致命)→ 入口守卫非空+_reject_batch_key   │
│      _unsafe 先于写盘 [design D5, spec 场景3, tasks 1.4]            │
│ D-b  batch add 默认_die非跳过 → MUST 传 --if-exists skip           │
│      [design D2, spec ④, tasks 1.2/1.3]                           │
│ D-c  triage 子进程失败检测未指定 → 逐项查 returncode+失败模式表      │
│      [design D4, spec ③/场景4, tasks 1.6]                         │
│ D-d  scan 口径 --status OPEN→--open-ungrouped(非终态∧批次空单原语)   │
│      [design D3, spec ②/场景1]  ← 关联 Q1                          │
│ D-e  _scan_pool 硬编码无过滤+签名错 → 全子步走 subprocess CLI        │
│      [design D1] (同解 args-namespace AttributeError)             │
│ D-f  "原子"措辞误导 → 非原子/fail-closed/重跑收敛(对齐 rename D6)     │
│      +收敛论证+失败模式表 [design D4, spec, tasks 1.7]             │
│ D-g  D8 并发边界+reindex失败策略(vs rename warn-only)显式说明        │
│      [design D4/D6]                                               │
├─────────────────────────────────────────────────────────────────┤
│ [需拍板] Q1  scan 口径 --open-ungrouped 略改 proposal「行为保持」承诺 │
├─────────────────────────────────────────────────────────────────┤
│ [已裁掉] X1  codex「sweep 未实现」X2「done SKILL 未改」= 实现前预期   │
└─────────────────────────────────────────────────────────────────┘
```

**[需拍板] Q1：sweep 扫描口径 `--open-ungrouped` vs `--status OPEN`**
- **选项 A（推荐，已 amend）**：`scan --change X --open-ungrouped`（= 源==X ∧ 非终态 ∧ 批次空，单既有原语）。对齐 done §2.1 文档边界「非终态 ∧ 批次空」，补了原手循环 `--status OPEN` **漏掉的「批次空」过滤**，且纳入非 OPEN 的非终态项（VERIFIED/IN_PROGRESS/BLOCKED），triage 按其既有 `open_untriaged` 语义推进到 PROPOSED。
- **选项 B**：`scan --status OPEN --change X` + Python 补「批次空」过滤。逐字复刻原手循环（只 OPEN），但原命令本身漏了批次空过滤、且「非终态」措辞成死逻辑。
- **三面后果**：系统——A 用单原语消歧义、更少 Python 过滤代码；用户——A 会把 VERIFIED/IN_PROGRESS 项也扫进批次（若担心 IN_PROGRESS→PROPOSED 倒退，B 更保守）；开发循环——A 与 done SKILL 文档边界一致、可机验。
- **主次判定**：推荐 A——done SKILL 边界 prose 本就写「非终态∧批次空」，`--open-ungrouped` 是为此语义存在的既有原语；「行为保持」应理解为对齐文档边界而非复刻有 bug 的命令。**若你更看重「只碰 OPEN、不惊动 IN_PROGRESS」则选 B**（proposal 需相应改回严格复刻）。

### Findings（各镜，按严重度）

**致命**
- **[对抗B-B1] 空 `--change ""` 精确误纳孤儿** | 证据 buglist.py:655/todolist.py:620(falsy 短路) + 源=="" 配孤儿 | 高置信 | **采纳 D-a**：argparse required 只查 present 不查 empty → 空 change 使孤儿被 triage 进空批次、状态被改（数据腐蚀），且随后 batch add "" 被拒留半成品。

**高**
- **[接地-F3/对抗A-F3/对抗B-B3] batch add 默认报错非跳过** | 证据 issues.py:698-706(默认_die,仅 --if-exists skip 才 no-op) | 高置信 | **采纳 D-b**：不传 skip → 幂等重跑 exit1 顶穿 fail-closed，破「重跑 exit0」场景。三源命中。
- **[对抗B-B2/backend-F2/F5] triage 子进程失败检测未指定+测试没覆盖** | 证据 issues.py:140-147(_scan_pool 有检测,triage 循环是新代码无同款) | 中高置信 | **采纳 D-c**：逐项查 returncode + 失败模式表 + tasks 补 triage 失败/收敛测试。

**中**
- **[codex-3/接地-F2/对抗A-F1/backend-F4] scan 口径 --status OPEN vs 非终态不自洽** | 证据 buglist.py:653-661 | 高置信 | **采纳 D-d**（Q1）：5 源全中，改 --open-ungrouped。
- **[接地-F1/对抗B-B4/对抗A-F4] _scan_pool 硬编码 scan --json 无过滤 + 伪代码签名错(pool=bug/todo 非输出键)** | 证据 issues.py:140-142,151-153 | 高置信 | **采纳 D-e**：全子步 subprocess CLI（带全参数），不直调 cmd_*。
- **[对抗B-B5/backend-F1/对抗A-F5] "原子"措辞误导，实为非原子多步写、靠重跑收敛** | 证据 issues.py:816-819(rename D6 先例) | 高置信 | **采纳 D-f**：措辞对齐 rename D6 + 收敛论证。
- **[对抗A-F4] 直调 cmd_batch_add 需完整 args namespace，getattr(优先级)无默认→AttributeError** | 证据 issues.py:694 | 中置信 | **采纳**（并入 D-e：subprocess CLI 免此坑）。
- **[对抗A-F2] triage 对 VERIFIED/IN_PROGRESS/BLOCKED 是推进(→PROPOSED)非 no-op** | 证据 buglist.py:543-544 | 中置信 | **采纳（批注）**：这是 triage 既有语义（未分诊开放态→分诊），非 sweep 引入；D3 已声明 --open-ungrouped 纳入这些项由 triage 既有行为处理。若视 IN_PROGRESS→PROPOSED 为倒退顾虑 → Q1 选 B。

**低**
- **[对抗B-B6] D8 并发边界未复述（sweep 写窗口更长）** | **采纳 D-g**（design D6 补串行边界声明）。
- **[backend-F6] reindex 失败策略与 rename warn-only 相悖** | **采纳 D-g**（design D4 补取舍理由：sweep 闭环语义故末步 fail-closed）。

### 已裁掉（反静默压制，可审计）
- **X1 [codex-1 critical] sweep 未实现** — spec-review 是**实现前**设计门，sweep 未实现是预期状态（实现在 ship 阶段 SDD），非设计缺陷。裁掉。
- **X2 [codex-2 high] done SKILL §2.1 未替换** — 即 tasks 2.1，实现期做，非设计缺陷。裁掉。
- **[对抗A angle-2] 已在别批次的项被跳过是正确行为**（对抗镜自证 refuted）——非 finding，不计。

### 度量锚（lens-metric，metrics.enabled=true）
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" runner="claude" site="none" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中5/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="none" findings="11" 采纳="9" 裁掉="2" defer="0" 独立="2" sev="致1/高2/中4/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="none" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="0" sev="致0/高1/中1/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="design-voice" findings="3" 采纳="1" 裁掉="2" defer="0" 独立="0" sev="致1/高1/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="none" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="ok" findings="3" truncated="false" -->

### 结论
冷审在「trivial」change 上抓出 **1 致命 + 2 高 + 4 中**真设计硬伤（空 change 孤儿腐蚀、batch add 幂等破产、triage 失败吞错、口径不自洽等），全部 amend 到 design/spec/tasks（标 `[spec-review-amendment]`）。设计现已实现就绪。

□ **建议进设计 HARD-GATE**：请拍板 Q1（scan 口径，推荐 A=--open-ungrouped）→ 批准后进 `/sdflow-ship`（SDD 实现 → code-review → done → merge）。
