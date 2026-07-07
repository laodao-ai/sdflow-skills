# spec-review-report — issues-pool-hardening

## 概要

- **对象**：`issues-pool-hardening`（G1，T1-T5 issues.py/recorder 健壮性合批），feat 分支。
- **广审层（Step1）**：grill-substituted（见 `gstack-review.md`）——design/eng 深度已由交互 grill 覆盖，CEO/DX 镜未跑（诚实缺口，内部工具低边际）。
- **多镜层（Step2）**：4 镜 fresh-context 并行——领域镜(backend) · 对抗镜 A(D1/T2) · 对抗镜 B(D2/D3/scope) · 接地镜(核验)。
- **outside-voice（cross-model）**：**已跑 design-voice（codex，exit 0）**〔设计门补跑 Q4〕——抓到同族 4 镜全漏的 3 个相邻腐蚀向量（OV-1/2/3），**全部 fold** 进本 change。跨家族补盲价值兑现。
- **裁决**：接地镜 10/10 主张全符合（0 事实错误）；同族/对抗镜合计抓出 **1 blocker + 2 硬设计缺口 + 若干完备性/措辞项**，全部经代码接地。**结论：不建议原样进 ship——需先过下方 3 个 [需拍板] + 应用 [自动决策] amendment，才达设计门放行。**

---

## 决策登记区

```
┌─ [需拍板] 设计门一次性拍板（reshape D2/D3，amendment 依赖其结果）──────────┐
│ Q1  D2 --strict 死 flag：本 change 零消费者                                 │
│ Q2  D3 match-or-error 语义黑洞 + placeholder 死胡同                         │
│ Q3  D3 auto-reindex 副作用面 + 失败排序未定义                              │
├─ [自动决策] 默认采纳（清晰改进，无备选；可覆盖）─────────────────────────┤
│ D-a 【BLOCKER】T2 守卫落点=输入端非 sink，且补全 triage/retag 写路径        │
│ D-b T3 守卫强化：并断 recorder 内联终态字面量、按 pool 索引               │
│ D-c spec 措辞订正：详细块含 `| 属性 | 值 |` 子表，非"纯 prose"            │
│ D-d design 措辞降级："需求=0"→"存量=0、未来罕见非零"（不翻 reject 决策）  │
│ D-e doc-sync 任务：rename 契约变更同步 SKILL.md（依赖 Q3）                │
│ D-f 接地订正：design 行号 357-361→359-363；T3 断言按 pool dict 索引        │
├─ [已裁掉] 反静默压制留痕─────────────────────────────────────────────────┤
│ X1  对抗A F5"set-status 回写卡死"——非活 bug（parse 在 re-join 前已切列）  │
│     裁掉理由：不成立为独立缺陷；但其证据佐证 D-a（sink 守卫是摆设）保留    │
└──────────────────────────────────────────────────────────────────────────┘
```

### Q1 — D2 `--strict` 在本 change 内是零消费者死 flag（对抗B B1 + 领域 F5b，2 镜）

D2 卖点"堵非交互 sweep 场景静默蒸发"，但唯一消费者（sdflow-done sweep 调 `--strict`）已 defer（T2.5）。grep 证实：`sdflow-done/SKILL.md:144` 裸调 reindex、无其它 hook/CI 调用点。→ 本 change ship 后 100% reindex 调用仍默认 exit 0，`--strict` 落地即死代码，D2 的 in-change 反静默价值**一分不兑现**。

- **选项 A**：把 T2.5（sweep 用 --strict）fold 进本 change——一行 SKILL.md 改动，flag 当场有消费者。**代价**：触 `sdflow-done/SKILL.md`（行为面 + 别 capability），破本 change scope 纪律。
- **选项 B**：诚实降级 D2 叙事——本 change 只交付 T1 stderr 回显（立即有效），`--strict` 明标"预置接口、本 change 无 enforcement 价值"，改 proposal/adr 措辞，别记成"已堵静默蒸发"。**保留死 flag**。
- **选项 C（推荐）**：**本 change 完全不加 `--strict`**——T1 只做 stderr 回显（原始 scope，立即有价值）；`--strict` + sweep 消费者**一起**放进 T2.5 follow-up（flag 与消费者同生同死，无死 flag、无虚假绿、守 scope、守 YAGNI）。
- **三面后果**：系统镜——C 最干净（无死代码、无 scope 破）；用户镜——三者对当前用户无差（都只多 stderr 回显）；开发循环镜——C 省一次"加了没人用的 flag 又要维护"的负担。**主次：推荐 C**（A 破 scope、B 留死 flag+需改叙事，C 两难全避）。

### Q2 — D3 `--if-exists skip` 的 match-or-error 是语义黑洞（对抗B B2 + 领域 F4，2 镜，接地证实）

grill 把 skip 收敛为 match-or-error 以避"静默吞字段"坑，但冷镜发现它有**自己的坑**：`cmd_batch_add` 用 `getattr(args,"优先级") or PLACEHOLDER`（issues.py:589）把"未传"与占位符塌缩；且 title/优先级/计划 是**架构明文"绝不解析的人写行"**（issues.py:27/458），根本无解析正则。→ ①首次 add 存 `优先级: <待填>`，再 `add key --优先级 P1` 想补填 → `P1≠<待填>` → `_die`，而**无 update 路径** → 逼手改 batches.md（正是本 skill 要消灭的）；②比较口径（trim/全角冒号 `：`/大小写）未定义，三实现三行为；③要比较就得解析"禁解析"的人写行，破架构契约。

- **选项 A**：match-or-error + placeholder 视为"未设" + 规范化口径 + 授权解析人写行例外。**最全但最重**，且破"绝不解析人写行"契约。
- **选项 B（推荐）**：放弃 match，改 **skip-with-warn**——`--if-exists skip` 遇已存在 key → no-op exit 0 + **stderr 警告"key 已存在，字段参数被忽略"**。无字段比较、无 placeholder 逻辑、无人写行解析、无死胡同；反静默由 warn 满足（且 skip 是 opt-in，忽略字段是其**声明语义**非隐蔽坑）。
- **选项 C**：T4 干脆不做 `--if-exists`，只保留 rename auto-reindex（幂等需求存疑就别硬上）。
- **三面后果**：系统镜——B 最简、零架构冲突；用户镜——B 的 warn 让"字段没生效"可见（不静默），要改字段走编辑/未来 update 命令；开发循环镜——B 免掉三实现三行为的口径战。**主次：推荐 B**（A 破契约+重、C 砍需求，B 达幂等又避全部黑洞）。

### Q3 — D3 auto-reindex 副作用面 + 失败排序未定义（对抗B B3，1 镜）

`rename` 末尾 auto-reindex = 调 `sync_batches_md` 遍历**全部**条目、可能把无关批次翻 DONE/追加 ⚠️；且失败排序漏洞：现序 校验→改 dated→写 batches.md→(auto-reindex)，若 auto-reindex 里 `read_pool` 抛错，dated+batches 已落盘但 INDEX 陈旧、命令 exit 非 0 → 调用方以为 rename 失败实则已改，且**恰好留下 auto-reindex 本要防的 INDEX 陈旧**。design 的"失败不触发"只覆盖写盘前失败。

- **选项 A（推荐）**：保留 auto-reindex 但**钉死失败语义**——reindex 异常吞掉只 warn（"rename 已生效，INDEX 未刷新，请手动 reindex"）、rename 本体 exit 0；并在 design 显式**承认** rename 触发全库批次状态同步这一扩大副作用面（这是 reindex 的固有性质）。
- **选项 B**：rename 只 patch old/new 两 key（不全量 reindex）——但 INDEX.md 派生自池、仍需 regen 才不陈旧，patch-only 不达 auto-reindex 目的（半解）。
- **三面后果**：系统镜——A 语义完整、B 留 INDEX 陈旧半解；用户镜——A 的 warn 让"改了但 INDEX 没刷"可见；开发循环镜——A 一次定义清失败路径。**主次：推荐 A**（B 不达目的）。

---

## 各镜 findings（去重后 canonical，带命中镜集）

| # | finding | 命中镜 | 置信 | 严重 | 处置 |
|---|---|---|---|---|---|
| C1 | **T2 守卫落点=输入端非 `" \| ".join(cells)` sink**（sink 在 parse 后、`\|` 已切走→永不 fire 假覆盖）；且补全 `cmd_triage`(cells[7]=batch, buglist:513/todolist:489) + `_retag_items_in_dated_files`(cells[7]=new_key, issues:681) 两条真·管道表 batch-key 写入；`batch add` 守的是 batches.md（错的面） | 领域F1 + 对抗A F1/F2 | 高 | **BLOCKER** | D-a 自动 |
| C2 | **D3 match "一致"语义黑洞**：placeholder 塌缩(issues:589)+死胡同+需解析禁解析人写行+口径未定义 | 对抗B B2 + 领域F4 | 高 | 高 | Q2 拍板 |
| C3 | **D2 --strict 零消费者死 flag**（sweep wiring defer，无其它非交互调用） | 对抗B B1 + 领域F5b | 高 | 中 | Q1 拍板 |
| C4 | **D3 auto-reindex 副作用面 + 失败排序未定义** | 对抗B B3 | 中 | 中 | Q3 拍板 |
| C5 | T3 守卫弱于自述：⊆ 断言抓不到 recorder 内联终态字面量漂移(buglist:507/579 三处硬编码 {FIXED,WONTFIX})；且 TERMINAL_STATUSES 是 per-pool dict 须按 pool 索引 | 领域F3 + 接地note | 中 | 中 | D-b 自动 |
| C6 | T2 守卫字段枚举不全：`time`/自定义 `id` 也进 row 未列（完备性） | 领域F2 | 中 | 低 | D-a 并入 |
| C7 | spec"详细块不受限"事实错：BLOCK_TMPL 含 `\| 属性 \| 值 \|` 子表(buglist:336)；`title` 换行→块头孤儿行且不在守卫集 | 对抗A F4 | 高(结构) | 低 | D-c 自动 |
| C8 | rename 契约变(auto-reindex)但 SKILL.md 未同步：`sdflow-issues/SKILL.md:90-91`"无副作用"将成事实错误 | 对抗B B4 | 高 | 低-中 | D-e 自动(依赖Q3) |
| C9 | "需求实测=0"过自信：本仓 pipe 相关 bug summary 未来含 `\|` 高概率 | 对抗A F3 | 中 | 低 | D-d 自动(措辞) |
| C10 | 接地：design 行号 357-361→实际 359-363（惯例真实、仅漂移） | 接地note | 高 | 微 | D-f 自动 |

**接地镜净结果**：10/10 代码事实主张全符合、0 不符（解析器三行、_die 惯例、cmd_batch_add docstring、TERMINAL_STATUSES/STATUS_CODES、_find_row_file 不存在、镜像+文件模式、cmd_batch_set_status 异构、0 occurrence、spec delta 挂靠点、reindex 现丢弃 problems）——**spec 的代码事实层零幻觉**。

**已裁掉（X1）**：对抗A F5"set-status 回写遇旧裸 `|` 卡死"——parse 在 re-join 之前已切列，不成立为活 bug；但其分析正面佐证 C1（sink 守卫是摆设），证据保留。

---

## lens-metric 度量锚（metrics.enabled=true；pre-gate 草稿值，SR-M 拍板时最终化）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="grill-substituted" site="design" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低3" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" runner="claude" site="backend" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="1" sev="致0/高1/中2/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="d1-t2" findings="5" 采纳="4" 裁掉="1" defer="0" 独立="2" sev="致0/高1/中0/低3" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="d2-d3-scope" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="2" sev="致0/高1/中2/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="code-facts" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="数据类工具脚本改动，无运行期爆炸/数据损坏难回退面命中 HR-TG 子集" -->

<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="ok" findings="3" truncated="false" -->

**outside-voice(codex) 3 findings（全 fold）**：
- **OV-1（高）**：`scan` 只验 `len>=5` 按固定列位读→无块坏行列错位不进 `problems`、`--strict` 也抓不到 → 加 scan 行 arity 校验（读侧盘面完整性）。
- **OV-2（高）**：batch key 只守 `|`/换行不够——`batches.md` header ` — ` 分隔，key 含 ` — ` 被切坏 → batch key slug 校验（拒 ` — `/首尾空白）三处复用。
- **OV-3（中）**：自定义 `id` 缺语法+查重（`parse_table_rows` 按 ID dict 重复静默丢行）→ `id` 须 `ID_RE.fullmatch`+不重复，scan 报重复 ID。

---

## 收敛口

**不建议原样进设计 HARD-GATE 放行**。冷镜（补 grill 非冷盲区）抓到 1 个 blocker（C1，D1 守卫落点错位会让旗舰修复落空）+ 2 个需 reshape D2/D3 的硬设计缺口（Q2/Q3）+ 1 个诚实性问题（Q1）。**请在设计门一次性拍 Q1/Q2/Q3**（推荐 C/B/A）；拍板后我应用全部 [自动决策] amendment（C1/C5/C7 等，标 `[spec-review-amendment]`）+ 按 Q 结果 reshape D2/D3，再重跑 `validate --strict` → 写 `design-approved` 锚。

---

## 拍板记录（设计 HARD-GATE，2026-07-07）

用户在设计门一次性拍板 + 补跑 design-voice。结果：

- **Q1 = B**：保留 `--strict` 作 T2.5 follow-up 预置接口（后面只需 wire+检查、不重做）；配诚实降级叙事——本 change 内 `--strict` 无消费者、不记作"已堵静默蒸发"（proposal/design/adr 已订正）。
- **Q2 = B**：`--if-exists skip` 改 **skip-with-warn**（no-op + stderr 警告字段被忽略），弃 match-or-error（避 placeholder 死胡同 + 禁解析人写行）。
- **Q3 = A**：`rename` auto-reindex 异常吞-warn + rename exit 0 + 承认全库副作用面。
- **OV-1 = fold**：`scan` 加行 arity 检测（读侧盘面完整性）纳入本 change。

**已应用 amendment（标 `[spec-review-amendment]`）**：C1(BLOCKER 守卫落点+全写路径) · C5(T3 内联字面量) · C7(块子表/title) · C8(doc-sync) · C9(措辞降级) · C10(行号) · OV-1/OV-2/OV-3。design/specs/tasks/proposal/adr 全同步，`openspec validate --strict` 通过。

**lens-metric（SR-M 最终化）**：所有 finding 均采纳（fold/amend），0 裁掉设计缺陷（X1 非缺陷）、0 defer——pre-gate 草稿锚的采纳数即最终值。

**放行**：blocker(C1) 已修、3 硬缺口(Q2/Q3/OV-1) 已 reshape、cross-model 补盲已 fold。设计门通过。

<!-- ship-gate: design-approved -->

> follow-up（不在本 change，交 hand-off）：T2.5 = `sdflow-done` sweep 用 `reindex --strict`（触 SKILL.md 行为面）；roadmap「去字符串化机器状态层」（Path B + T65）。
