# Design — mlh-p1-issues-sweep

> roadmap 阶段 1 的实施设计。整体架构/立论权威源在 `openspec/roadmaps/mechanical-layer-hardening/design.md`（adr/0006 机械层固化 · 决策 5「脚本化候选切出判断」）。本文件只记本 change 自身落地取舍。
>
> **v2〔spec-review-amendment〕**：spec-review 5 源（codex + 接地 + 对抗A/B + backend 领域）冷审订正——空 change 守卫、`--if-exists skip`、`--open-ungrouped` 口径、全子步 subprocess CLI、非原子措辞、triage 失败检测。详见 `spec-review-report.md`。

## 1. sweep 组合既有原语（全走 subprocess CLI，不直调 cmd_*）

`sweep --change X` 是既有原语的**确定性拼装**。**全部子步走 subprocess CLI**〔spec-review-amendment：接地-F1/对抗A-F4/对抗B-B4〕——不直调 `cmd_batch_add`/`cmd_reindex`（它们依赖 argparse 填好的 args namespace，`getattr(args,"优先级")` 无默认值会 `AttributeError`；且 `_scan_pool` 硬编码 `scan --json` 无过滤参数），而是像 done 手循环那样调完整 CLI：

```
sweep --change X
  ├─ [守卫] X 非空 ∧ 过 _reject_batch_key_unsafe（拒 |/换行/em-dash ` — `/首尾空白）
  │         ——先于任何写盘〔对抗B-B1 致命 / backend-F3〕：否则 X="" 精确误纳孤儿、含 ` — ` 的 X 污染 N 项后才被拒
  ├─ subprocess: buglist.py  scan --change X --open-ungrouped --json  ┐ --open-ungrouped = 非终态 ∧ 批次空
  ├─ subprocess: todolist.py scan --change X --open-ungrouped --json  ┘ 〔口径修正：不用 --status OPEN，见 D3〕
  ├─ 逐项 subprocess: triage --id {id} --批次 X（bug→buglist.py / todo→todolist.py）
  │         每项查 returncode，非零即中止 + 报明「失败在第 i 项 / 哪个 pool / 已成功 tag 的 id」〔对抗B-B2/backend-F2〕
  ├─ subprocess: issues.py batch add X --if-exists skip   〔对抗A-F3/接地-F3：默认报错，必须 skip〕
  └─ subprocess: issues.py reindex
```

## 2. 决策

### D1：sweep 归 issues.py（跨池编排器），全子步走 subprocess CLI
**决策**：sweep 放 `issues.py`（跨 buglist+todolist 两池的编排器），**所有子步（scan/triage/batch add/reindex）走子脚本/自身的完整 CLI subprocess**，不直调 cmd_* 函数。
**理由**：符 D4 红线（三 recorder 无共享 import、绝不解析人写行）；避免直调 cmd_* 的 args-namespace 脆弱性（`getattr(args,"优先级")` 无默认 → AttributeError〔对抗A-F4〕）；与 done 手循环调 CLI 的形态一致，行为可比。CLI 天然带全参数（含 `--if-exists skip`）。

### D2：幂等 = triage 既有幂等 + `batch add --if-exists skip`，sweep 不另加状态
**决策**：sweep 幂等靠三层——① triage 既有幂等（已 PROPOSED/已终态 no-op，接地镜核验成立）；② `batch add` **必须传 `--if-exists skip`**（默认是 `_die` 报错，非跳过！接地-F3/对抗A-F3/对抗B-B3 三源命中）；③ reindex 确定性重建（幂等）。sweep 本身无状态、可重跑。
**理由**：不传 `--if-exists skip` → 第二次 sweep 到 batch add 步 `_die` exit 1 → 叠加 D4 fail-closed → 违反「幂等重跑 exit 0」场景。这是 load-bearing 细节，非措辞。

### D3：扫描口径用 `--open-ungrouped`（= 非终态 ∧ 批次空），非 `--status OPEN`
**决策**：sweep 扫描用 `scan --change X --open-ungrouped --json`——既有 flag 恰好实现「源==X ∧ 非终态 ∧ 批次空」（`buglist.py:659-661`），单原语一步到位，无需 Python 侧二次过滤。
**理由**〔口径修正，codex-3/接地-F2/对抗A-F1/backend-F4 五源全中〕：`--status OPEN` 是精确等值匹配、只圈 OPEN，**不等于**「非终态」（漏 VERIFIED/IN_PROGRESS/BLOCKED），且不过滤「批次空」。`--open-ungrouped` 才对齐 done SKILL 文档边界「非终态 ∧ 批次空」。**行为微调声明**〔需拍板 Q1〕：这比原手循环的 `--status OPEN` **更精确**（补了原命令漏的「批次空」过滤、纳入非 OPEN 非终态项）——proposal 的「行为保持」应理解为「对齐 done SKILL 的文档边界」，非逐字复刻有 bug 的原命令。triage 对纳入的非终态项按其既有 `open_untriaged` 语义推进到 PROPOSED（未分诊→分诊，triage 本有行为）。

### D4：非原子 + fail-closed + 重跑收敛（措辞对齐 rename D6，非「原子」）
**决策**：sweep 是**非原子**多步多文件写（逐项 triage 各自 atomic_write），语义 = `cmd_batch_rename` 的 D6「非原子 / fail-closed / 重跑收敛」，**不是真原子**〔对抗B-B5/backend-F1/对抗A-F5〕。任一子步非零退出 → sweep 整体非零退出 + stderr 报明**失败步 + 失败点位（第 i 项/哪个 pool/已 tag 的 id 列表）**，不静默继续。
**收敛性论证**：triage 单次 atomic_write 无半行腐蚀；重跑时已 tag 项被 `--open-ungrouped` 的「批次空」过滤排除、未 tag 项补做、batch add 补建、reindex 收敛——**故半途失败后重跑 sweep 收敛到完成**（前提 = D2 的 `--if-exists skip` 成立，否则「成功后重跑」永 exit 1）。
**失败模式表（backend-F2）**：

| 失败步 | 检测 | 半盘面 | 重跑收敛 |
|---|---|---|---|
| scan 非零 | subprocess returncode | 无写盘 | 是（无副作用） |
| 第 i 项 triage 非零 | 逐项查 returncode | 前 i-1 项已 tag | 是（已 tag 项被批次空过滤排除） |
| batch add 非零 | returncode（非 skip 情形） | N 项已 tag、X 未注册 | 视原因（key 合法则是；key 恒被拒则永卡，故 D1 前置守卫 X）|
| reindex 非零 | returncode | 全 tag、X 已注册、INDEX 未刷 | 是（重跑仅补 reindex）|

**与 rename 的 reindex 失败策略差异**〔backend-F6〕：rename 对 reindex 失败是 warn-only+exit0（增量修改、写盘已完成不反噬）；sweep 是**fail-closed**（末步 reindex 失败也判整体失败）——取舍理由：sweep 是「一次分诊闭环」语义，INDEX 未刷=闭环未完成，宁可响亮失败让调用方（done sweep 步）重跑，也不留「triage 完但 INDEX 陈旧」的静默不一致。

### D5：入口守卫 `--change` 先于任何写盘（致命项 B1）
**决策**：cmd_sweep **第一步**（scan 之前、任何写盘之前）：`if not args.change.strip(): _die(...)` + `_reject_batch_key_unsafe(args.change)`（拒 `|`/换行/` — `/首尾空白）。
**理由**〔对抗B-B1 致命 / backend-F3〕：`--change ""` 因 argparse `required` 只查 present 不查 empty + 两池 scan `if args.change:` falsy 短路不过滤 + sweep `源==""` 恰配孤儿 → 把 D3 明令不纳入的孤儿项 triage 进空批次、状态被改（数据腐蚀）；含 ` — ` 的 X 会先污染 N 项 tag、后到 batch add 才被拒（留半成品孤儿）。守卫必须**前置于写盘**，fail-closed。

### D6：并发边界沿用 D8，写窗口更长〔对抗B-B6〕
sweep 沿用 issues.py D8 串行假设（无锁），但写窗口比单命令长（N 次 triage 写 + batch add + reindex）。调用方（done sweep 步）MUST 串行、勿与手动 triage 交叉；并发焊接归 TG-26/Phase C（本 change 不做，显式声明边界）。

## 3. 判断 vs 机械的切分（roadmap 决策 5）
- **脚本 own（机械）**：守卫 X + scan(`--open-ungrouped`) + 逐项 triage(查 returncode) + batch add(`--if-exists skip`) + reindex 的确定性拼装 + 幂等 + fail-closed。
- **保留给模型/人**：调用方决定「对哪个 change 跑 sweep」（给 `--change` 名）；sweep 本身无判断部分（SKILL 自认「纯机械 bash」）。

## 4. 权威源
- roadmap：`openspec/roadmaps/mechanical-layer-hardening/roadmap.md` §阶段 1
- sweep 现协议（被替换的手循环）：`sdflow-done/SKILL.md` §2.1
- 既有原语：`_reject_batch_key_unsafe`(issues.py:324) · buglist/todolist `scan --open-ungrouped` · `triage` · `batch add --if-exists skip`(issues.py:906) · `cmd_reindex`
- 冷审裁决：`spec-review-report.md`
