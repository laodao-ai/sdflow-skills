---
ship-gate:
  design_approved: true
  reviewed_sha: cc703f552b918f903621a043917171309badba2a
---

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:fanout-capability v1 host="codex" subagents="available" mirrors="adversarial,grounding" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-12,TG-14,TG-15,TG-18,TG-19" evidence="复杂 FF-0 决策、skill/reference 重构、新 codepath、测试计划与多需求均不属于 trigger-catalog 的 HR-TG 子集" -->
<!-- sdflow:declared-sites v1 declared="design-voice" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="same-family" host="codex" runner="none" reason_code="fallback-unavailable" findings="0" truncated="false" -->

# Spec Review Report · harden-sdflow-spec-followups

**设计门已拍板批准，日期 2026-07-27。** 用户在审阅“四条通则五问 + 单一 `command-unverifiable`”方案后明确回复 `go`；两次规格 checkpoint 将该方案逐字落入四件套，窄复核未改变目标或行为。机判锚见头部 `ship-gate`，批准盘面为 `cc703f552b918f903621a043917171309badba2a`。lens-metric 已按窄复核的最终裁决重算。

## 结论

建议 **APPROVE（以本报告 amendments 为准）**。首轮评审找到 7 个有效缺口；本次简化方案的窄复核另找到 2 个中等缺口，均已回填 proposal/design/tasks/delta specs/decision memo，scoped re-review 双镜 PASS。T132 仅订正未来 gate 输入并保持 OPEN，T239 保持独立 rollout，不发生静默扩面。

本轮没有 domain 镜：change 是 Markdown/Python/Bash workflow 与 hook，不命中 backend/frontend/embedded 领域清单。风险按普通档运行 2 个对抗镜 + 1 个接地镜。Codex capability probe 实际派出并收到 `PROBE_OK`，因此 `subagents=available`；该事实由主 session 观察并落锚，无可信机械捕获路径，不能把它宣称成机械门。

## Step 1 · Native autoplan 广审

<!-- sdflow:step1-broad-review v1 mode="native" -->

原生执行 CEO → Engineering → DevEx，因无 UI scope 跳过 Design phase。侧信道证据：autoplan 生成了 restore/current plan 文件，主 session 汇总到 `gstack-review.md`，并形成 checkpoint `460070d`。

广审提出 6 个 finding：FF-0 的负向黑名单无法证明 cwd、T132 scope 冲突、resident-contract 可留空壳、台账缺 closure matrix、安装验收不可判定、稳定 reason code 缺失。其自动决策全部进入合并池。

### Outside voice 降级

helper preflight 成功（Claude Code `2.1.220`、capability manifest/agents/POSIX 均 ready），但 dispatch 使用了相对 `run-dir`，helper 在启动外部作业前返回：`state=usage-error`、`reason_code=preflight-error`、`fallback_allowed=false`、detail=`run-dir MUST 为绝对路径`。本轮该站点无 `dispatch-manifest.tsv`，只有 context 文件；按防重复计费纪律未重派、未启动同族 fallback。`outside_voice_guard.py` 对 `gstack-review.md` 返回 `same-family`，因此本报告如实落 `runner=none` / `fallback-unavailable` / findings=0；不能宣称获得跨模型第二意见。

## Step 2 · 多镜 findings

### F1 · FF-0 的 trust boundary 需正向有限证明（高，采纳）

- 来源：autoplan + 两个对抗镜。
- 证据：原 `design.md` D1 要求“命令不包含任何可能改变工作目录的结构”，同时禁止 shell 解析；现 hook 对整串 `NEW_CHANGE_RE.search()` 后直接用 payload `cwd`。
- 失败场景：`pushd`、`env -C`、wrapper、compound、前后散文/decoy 都能绕过有限黑名单或触发错仓执法。
- 修订：`[spec-review-amendment]` 改为完整匹配的单条直接 literal allowlist；其他命中创建字样的形态统一只给带 `command-unverifiable` 的 context，无 permission decision；保留多调用 stacking deny 与原三分支/ack，不再推测细分原因。

### F2 · T132 的“前置订正”与“实现 gate”互相冲突（高，采纳）

- 来源：autoplan + 两个对抗镜 + 接地镜。
- 证据：decision memo C1 只纳入 T132 前置订正，原 tasks 2.3 与 SA-15 却要求门消费信号；仓内当前没有 T132 `REFUSE_START` consumer。
- 修订：`[spec-review-amendment]` 本 change 只订正 T132/T234 的 A/B 输入契约与台账，明确不得实现/关闭 T132。A 候选信号为有效 memo + `checkpoint(sdflow-spec-grill)`；B 候选信号为 `checkpoint(grill)` 或未来 gate 明确认可的锚。

### F3 · 薄入口门可保留空壳标题而丢执行语义（高，采纳）

- 来源：autoplan + scope 对抗镜。
- 证据：原 SA-14 只要求必驻标题和 reference 存在。
- 修订：`[spec-review-amendment]` 增加 resident-contract token map：frontmatter、Phase 0/A/B/C、C.1 四判、终审、strict validate、两个 checkpoint、出口三步与每个 reference 的加载条件/相对路径。

### F4 · 台账没有逐票完成定义（中，采纳）

- 来源：autoplan + scope 对抗镜。
- 修订：`[spec-review-amendment]` 增加 closure matrix 与逐 ID 测试：T232/238/240/241 只在归档证据复核后关闭；T233–237/242 只在本 change 实现+测试后关闭；T234 在输入订正后关闭；T132/T239 不得关闭。

### F5 · `setup.sh` 不安装 FF-0 hook（高，采纳）

- 来源：autoplan + scope 对抗镜 + 接地镜。
- 证据：`ensure_global_hooks()` 只在 `sdflow-init/scripts/init.py` 的 init/update 路径执行；`setup.sh` 只铺 skills、agents 与 `~/.sdflow` bundle/hack，且某些目标不可写时会 skipped 但整体 exit 0。
- 修订：`[spec-review-amendment]` Migration/Task 4.2 加 `python3 sdflow-init/scripts/init.py update --root . --dev`，再跑 `setup.sh`；逐项比对 hook 字节/settings 注册、skill symlink 或 Windows 内容/hash，相关 skipped 判失败。

### F6 · 决策纪要 C1 漏列 T232（中，采纳）

- 来源：接地镜独立 finding。
- 证据：proposal/tasks 明确处理 T232，但 memo 原 C1 从 T233 起列。
- 修订：`[spec-review-amendment]` C1 改为 T232–T238、T240–T242，并重算 `decision_hash`。

### F7 · 命中 TG 的模板物证缺失（高，采纳）

- 来源：主 session 触发目录核对。
- 证据：TG-12/14/15/18/19 分别要求决策图、组件清单、失败模式/可观测性、测试覆盖图与 P0/P1/P2；原四件套未完整提供。
- 修订：`[spec-review-amendment]` proposal 增 Requirement Priorities；design 增 FF-0 决策图、Components、Failure Modes and Observability；tasks 增 Test Coverage Map。

## 窄复核 · FF-0 单一未判定原因码

评审对象先为 `be4052274cc28cf72ccc9ac17537b2c3d94ca22e`，修订增量为 `cc703f552b918f903621a043917171309badba2a`。Codex capability probe 实际派出并收到 `PROBE_OK`；随后运行 1 个 fresh 对抗镜和 1 个 fresh 接地镜。该能力事实由主 session 观察，无可信机械捕获路径。

### F8 · 实施任务未明确迁移 canonical-entry 旧断言（中，采纳）

- 来源：对抗镜独立 finding。
- 证据：`hack/tests/test_canonical_entry_sync.py` 与 `sdflow-init/tests/test_ff0_branch_guard.py` 仍逐类断言旧原因码；原任务没有点名迁移这两份测试或删除分类器。
- 修订：Task 1 明确删除 `undecided_reason`、动态 marker、双分支说明及仅为旧分类存在的正则；点名同步两份测试，保留 `CHANGE_NAME_RE` 的 stacking 用途。

### F9 · “无运行时消费者”表述忽略 hook 内部自消费（中，采纳）

- 来源：接地镜独立 finding。
- 证据：当前 hook 用 `reason_code` 选择两段说明文案，虽无 hook 外部或跨阶段消费者，但仍存在内部消费。
- 修订：design/decision memo 改为“无 hook 外部或跨阶段消费者”，并明确实现时一并删除内部分类器与条件说明。

scoped re-review 结论：F8、F9 与流程图中的泛化 `reason_code` 均 **ADDRESSED**；未发现新的高/中严重度 breakage。严格 OpenSpec 校验、decision memo hash 门与 diff whitespace 检查通过。

## 决策登记与 disposition

| 决策 | 处置 | 依据 |
|---|---|---|
| FF-0 正向直接调用 allowlist | 采纳 | 能证明进入 cwd-bound decision 的条件，避免无界黑名单 |
| T132 只订正输入、保持 OPEN | 采纳 | 对齐用户批准的源仓 follow-up 范围，阻止静默扩面 |
| resident-contract token map | 采纳 | 字符门之外守住执行语义 |
| 单一 stable reason code `command-unverifiable` | 采纳 | 守住可审计性，同时不为相同权限行为维护无消费者的 shell 组合分类矩阵 |
| closure matrix | 采纳 | 逐票完成定义，避免“schema 绿即闭环” |
| `init.py update --dev` + `setup.sh` 双链验证 | 采纳 | 两条分发链职责不同，不能互相替代 |
| T132 gate 实现 | defer | 独立 OPEN 事项；本 change 明令不得实现/关闭 |
| T239 下游 rollout | defer | 用户明确排除；继续作为独立后续 |

无 finding 被裁掉；两个 defer 是已声明 non-goal，不是未处理的本 change 缺口。

## 三镜代价

本次 TG 集不含 TG-23，因此不触发完整三镜方案决策书。主次判定：系统镜以不在错仓执法为主；用户镜接受复杂命令只得到“未判定”提示；开发循环镜用有限 grammar 与表驱动测试换取更低维护负担。

## Metrics

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="codex" runner="codex" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="1" sev="致0/高4/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="codex" runner="codex" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="1" sev="致0/高5/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="codex" runner="codex" site="—" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="2" sev="致0/高2/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="codex" runner="none" site="design-voice" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->

度量由 `lens_metric_emit.py` 对结构化 roster/findings 归约。残余信任边界：finding 去重、镜头分类、severity、roster 完备性与 JSON 誊写由主 session 判断；emitter 只证明给定输入的确定性归约。

## HARD-GATE 建议

设计 HARD-GATE 已批准；下一步进入 writing-plans / 阶段三连续实现。
