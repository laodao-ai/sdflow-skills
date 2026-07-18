# spec-review-report · async-outside-voice

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->
<!-- sdflow:step1-broad-review v1 mode="simulated" -->
<!-- sdflow:hr-tg v1 hit="TG-09,TG-17,TG-26" declared="TG-09,TG-17,TG-26" evidence="async 多 voice+镜后台并发(TG-26)、voice 单站点状态机(TG-09)、出境 scan/承重墙不变承重声明(TG-17)" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="simulated-source" host="claude" runner="codex" reason_code="ok" findings="5" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="5" truncated="false" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="11" 采纳="11" 裁掉="0" defer="0" 独立="0" sev="致0/高4/中5/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="1" sev="致0/高2/中2/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="0" sev="致0/高2/中3/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="0" sev="致0/高1/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="0" sev="致0/高3/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="1" sev="致0/高3/中3/低0" -->

## 收敛口（决定性）

**不建议进设计 HARD-GATE。需一轮设计返修（把下列高危落进 design/tasks），再复审。**

方向对（Claude 宿主 async off-critical-path 是正解）。**原阻塞级 F-A 的「900s 够不着」半已被 spike 证伪**〔2026-07-18 边界 spike：`run_in_background` 后台任务跑满 **660s、跨过 600000ms 外层上限、exit 0**、ppid 全程 11092 稳定不 reparent——600ms 上限**不管**后台、900s 可达、harness 托管生命周期实证〕→ **F-A 降为高危**（剩「collect 通知模型 + exit code 传输」的设计精度，与 900s 数值无关，非机制重塑）。当前 = **0 阻塞 + 5 高危 + 7 中低**：机制可行，返修 = 把精度/分支/机械化缺口落进正文，非重做地基。dogfood 附记：两 codex voice 经 `run_in_background` 跑到完成、reason_code=ok（但均 <600s，未压到 900s 真实负载——见 F-L）。

**roster**（host=claude · opus/sonnet/haiku · subagents=available）：Step1 冷广审(simulated) + 领域镜 + 对抗镜×2 + 接地镜 + 跨模型 voice×2（design-voice/hr-tg，均 codex，均 reason_code=ok）。收敛度高（15 条合并 findings，仅 2 条单镜独占），跨模型 voice 独立贡献显著（hr-tg 独占 1 条 CRITICAL + 与 design-voice 共同锁定阻塞项）。

---

## 决策登记区

```
┌──────────────────────────────────────────────────────────────────┐
│ [已决/spike] Q1  F-A「900s 够不着」半已 spike 证伪（后台跑满 660s │
│              跨 600000ms 上限、exit 0）→ 900s 可达。剩「collect 通  │
│              知模型 + exit code 传输」= 设计精度、返修轮落，非拍板  │
│ [需拍板] Q2  F-B：900s 只该用于 Claude async；Codex sync + claude- │
│              降级同步「第三态」的 --timeout/外层超时配对未定义      │
│ [需拍板] Q3  F-C：anchor_lint 家族级、不核 per-site → 并发 2 站点  │
│              漏收一个仍判 CLEAN。「无锚=缺席」诚实但不可审计。是否 │
│              按基准①机械化（declared 站点集 vs 实落锚集）本 change  │
│              内 fold、还是 defer？                                  │
│ [需拍板] Q4  F-O：机械等值门 ADR-5 只有主张、无候选文本；且只借    │
│              sync_principles 的 --check（无 --apply 单一源）。是否  │
│              改用「单一源 snippet + 注入」（成本远低于全抽取）？    │
│ [自动决策] D1  F-E：ADR-6「line 101 inline」引文错（三镜独立收敛：  │
│              broad B2 + 接地 + 对抗2）→ 已按 [spec-review-amendment]│
│              修正引文为 line 96/80，「已解」降级为「读码强提示+自探 │
│              是实际防线」                                           │
│ [自动决策] D2  F-D 补 exit 2 进状态机 + collect 未知态 fail-safe   │
│              (→exec-error，MUST NOT 读作 ok)；D3 F-F --timeout 正整 │
│              数+上界校验(拒 0/负/越界)；D4 F-G per-run 不可变 context│
│              路径；D5 F-I dispatch 时 task_id 落盘；D6 F-K Success  │
│              Metrics 补 Codex efficacy=0 负向断言；D7 F-M 删 ADR-5  │
│              现状论陪衬；D8 F-N config 读取路径拍定「SKILL 直读     │
│              config.yaml（沿 metrics.enabled 先例 L179/206）」      │
│              —— 均低风险、默认采纳、返修轮一并落                    │
│ [已裁掉] （无）——15 条 findings 全部经对抗裁决存活，无静默丢弃     │
└──────────────────────────────────────────────────────────────────┘
```

> 反静默压制：本轮无「裁掉」项。唯一被推翻的是**对抗镜2 自己的 1d 论断**（「render_prompt 一次性读入、TOCTOU 已闭」）——主审读码核定 **hr-tg 的 HV1 才对**（scan@L153 与 cat@L164 是对 live 文件的两次独立读，窗口窄但真实存在），故 F-G 判**成立**、非裁掉。

---

## Findings（按严重度，已合并去重；标注收敛镜 + 主审核定）

### 🟠 高危 F-A（原阻塞级 → spike 证伪「900s 够不着」半 → 降级）

**F-A — collect 机制对齐了错误的 harness 契约（通知驱动 vs 轮询）+ exit code 传输未定义**（「900s 撞 600000ms」半已 spike 证伪）
〔对抗镜1 · 领域镜 · 广审B1 · design-voice DV1/DV3 收敛；主审实测核定〕
- **通知非轮询**：本 harness 的 `run_in_background` 是**完成通知驱动**（"you will be notified when it completes — do not poll"；"long leading sleep blocked"）——**主审本轮亲历实证**：4 子代理 + 2 voice 完成都是 push 通知、从未轮询。design 通篇「Step3 轮询到终止」（ADR-3/序列图/tasks §3.1）是错的心智模型；且通知可能在 Step1/2 就到达（谁接？）或 Step3 时仍未到（无阻塞等待原语 → 模型自造轮询 → 成本暴涨）。design 零着墨这个「异步到达 vs 同步 checkpoint」错位。
- **600000ms 硬上限**：Bash 工具外层 timeout **上限 600000ms、缺省 120000ms**（主审工具 schema 核实）。内层 900s 需外层 ≥930000ms > 600000ms。若外层上限对 `run_in_background` 也生效（到期杀底层进程、只是不阻塞 turn）→ **900s 天花板永远够不着**，600s 先杀 = 本 change 要消灭的「外层杀内层」bug 从 330s 挪到 600s，不是修复。本轮 dogfood 两 voice 都 <600s 完成 → **无法证伪也无法证实** 900s 量级能否存活。
- **exit code 传输**（DV3）：collect 要按 0/1/3/124 分支，但 `run_in_background` 给的是**输出 + 完成信号**，退出码如何**可靠**取得未定义——主审本轮是靠 `echo EXEC_EXIT=$?` 塞进 stdout 文本才拿到，正是「从正文 parse 退出码」的脆法。
- **裁决**：① **已 spike 证伪**〔2026-07-18：后台任务跑满 660s、跨 600000ms 上限、exit 0、ppid 稳定不 reparent〕→ 600ms 上限不管后台、900s 可达、harness 托管生命周期成立。② + ③ **仍立**（与 900s 数值无关）：collect 须重写为通知驱动的具体工具调用序列（主审本轮亲历——6 后台活全是 push 通知、零轮询）；退出码须结构化 envelope 可靠传输、非正文 parse。∴ F-A 降**高危**：机制可行，剩设计精度，返修轮落，不再需要 gate 前 spike。

### 🟠 高危（返修轮 MUST 逐条处理）

**F-B — 900s 用错分支：Codex sync + claude-降级同步「第三态」超时配对未定义，会在本 change 自己的降级分支复现原 bug**
〔design-voice DV2 · hr-tg HV4 · 对抗镜2 2b 收敛〕
- spec.md L7-8 把 900s 绑 claude-async、Codex 保留外层 ≥330s；但 tasks §3.3 **无条件**要求 exec 传默认 900s。契约要求外层 ≥ 内层+30s：Codex 内层若 900s、外层仍 330s → 假超时；外层升 930s → 不再是「保持同步现状」。**更尖**：`$SDFLOW_HOST=claude` 但 `run_in_background` 自探失败 → 降级**同步**这个第三态，用哪个 --timeout / 外层？spec/design/tasks 全未定义 → 恰在「降级路径必须正确」这条 change 核心承诺上留空。
- **裁决**：CONFIRMED。900s SHALL 仅用于 Claude async；Codex sync 与 claude-capability-fallback-sync 用独立 sync 天花板（300s/外层≥330s），始终机械满足 outer≥inner+30s。做成执行模式矩阵。

**F-C — anchor_lint 家族级不核 per-site → 并发 2 站点漏收一个仍判 CLEAN，「无锚=缺席」诚实但机械不可审计**
〔领域镜(核 anchor_lint.py) · hr-tg HV3 · 对抗镜2 2a 收敛；主审读码核定〕
- `anchor_lint.py:154/168-170` 仅家族级存在性（"outside-voice" 族有 ≥1 行即过），`site` 明确不校验（L26/595 CF-补2）。本 change 把「同 SKILL 内并发 design-voice+hr-tg」设为常态：一个 dispatch 后中止未 collect、另一个正常完成 → 报告只 1 条 outside-voice 锚 → **lint 判 CLEAN**。「合法跳过（reuse-guard/HR-TG 未命中）」与「派了但漏收」在报告上是同一个沉默信号，机械不可区分。诚实边界的唯一防线是 design L88 一句纯 prose「MUST 显式列站点↔task_id 映射」，零机械兜底。
- **基准① 判据**：两个 dispatch 门控条件（reuse-guard reason_code≠none、HR-TG∩≠∅）在 Step1/2 是**机械可算**事实；hr-tg 锚已有 `declared=`（模型声明 vs 机械核验，adr/0018）现成先例 → 这是「够得着却退化成纯语义」，**违反基准①**。
- **裁决**：CONFIRMED。Q3 拍：本 change 内 fold 一个「declared 应 dispatch 站点集 vs 实落锚集」的轻量机械核（可给 anchor_lint 加可选校验），还是 defer 立 todo。主审倾向 **fold**（承重正确性 + 够得着 + 有先例）。

**F-D — 状态机漏 exit 2 + collect 未知态无 fail-safe**
〔hr-tg HV3 · design-voice DV3；主审核定 outside-voice.sh:32 声明 exit 2〕
- helper 头注释 L32 明列 `2=用法错/文件不存在或不可读`，design 状态机（0/1/3/124）漏之。collect 对「task lookup 失败 / 退出码丢失 / 未知码」无 fail-safe 定义。
- **裁决**：CONFIRMED（低风险 fix，D2 自动决策）。补 exit 2；collect 未知态一律 →exec-error 保守降级，MUST NOT 读作 ok；仅整轮中止未产报告才允许无锚。

**F-E — ADR-6「line 101 inline」引文与实际不符，Q2「已解」证据强度被夸大**（三镜独立收敛）
〔广审 B2 · 接地镜 9b · 对抗镜2 4a〕
- 主审读码核定：ship line 101「主 session inline 执行」**绑在 `sdflow-implement mode=tickets-plan`**，非 `RUN_CODE_REVIEW→/sdflow-code-review`（后者裸跳转、无注记）。结论（code-review 主 session 内联跑）仍成立，但靠 line 96「ship 不直接派子代理」+ line 80「meta-orchestrator chain 现有 skill」的**通用**陈述，非逐字直接证据。
- **裁决**：CONFIRMED（**已 [spec-review-amendment] 修正**，见下）。「已解」→「读码强提示；1.3/2.1 自探是当前验证 A2 的实际防线、非兜底冗余」。

### 🟡 中危（返修轮 design 正文补齐）

- **F-F** 〔DV5·HV4〕 config `--timeout` 无正整数/上界校验（helper 允许 `--timeout 0` = 无天花板 → 破坏「≤天花板保证终止」）。→ 校验正整数、受 harness 上限约束、0/负/越界/解析失败回落默认。
- **F-G** 〔hr-tg HV1；主审读码核定〕固定路径 context 的 scan(L153)→cat(L164) 两次独立读，中间被覆盖 → 未扫描内容进跨模型 prompt（**绕 secret_scan**）。窗口窄但真实；async 孤儿延长跨会话可达性。→ per-run 不可变路径 `<run-id>/<site>-context.md`，scan+render 对同一快照。
- **F-H** 〔广审B3·对抗2 1c·HV5；主审核定 L202 trap 仅 EXIT〕`trap … EXIT` 不含 INT/TERM → SIGKILL 泄漏 workdir（含全量 prompt.md=proposal/diff）在 /tmp；900s 天花板**三倍化**该暴露窗。+ 孤儿跑完未 collect 的 **完整 token 浪费**。Security/Cost 均未覆盖。+ HV5：`timeout -k 10` = 终止后再 10s 宽限，墙钟到 900s ≠ 已 terminal，deadline 应定义为「terminal 可 collect」非裸墙钟。
- **F-I** 〔对抗1·领域〕站点↔task_id 记账无落盘证据 →「派了丢了」与「合法不派」不可事后区分（审计盲区，非假绿）。→ dispatch 时 task_id 追加写 context/manifest。
- **F-J** 〔对抗1·领域〕§4.1 验收（「reason_code=ok + 无≥330s 阻塞」）可被一次侥幸 <600s 完成的运行伪造通过、不约束轮询次数/墙钟、未强制近天花板场景。→ 加严：约束调用次数、强制近天花板、记录 Step2 fan-out 墙钟 vs voice 完成时刻（校准重叠红利）。
- **F-K** 〔广审B4·对抗2 4b〕Why 引 Codex 3/3 timeout 作最触目动机，Success Metrics 只覆盖 Claude、「Codex 仍 efficacy=0」只在 Non-Goals → 只读 Why+Metrics 易误判「已解」。→ Success Metrics 补负向断言。
- **F-L** 〔对抗2 1b·领域6·广审B6·DV1〕A1 spike **仓内无可审计证据**（git log 仅 2 次文档 checkpoint）、**时长未知**、且只验「进程存活」非「harness 输出文件生命周期」。ADR-1「难点全消失」把未验假设当陈述。→ 返修 spike 覆盖 900s 量级 + 输出文件 TTL/权限/清理归属。

### ⚪ 低危

- **F-M** 〔广审B5〕ADR-5「两 SKILL 本就各有一份（既有重复）」是「拿现状撑决策」，贴近通则③禁止项 → 删陪衬，只留「抽取需新建 include 机制=越 scope」（**D7 已列自动决策**）。
- **F-N** 〔广审B7·对抗1·接地〕config 读取路径可现在拍板：仓内 `metrics.enabled` 是 SKILL 直读 config.yaml（L179/206），两 SKILL 各选不同路径会让等值门首跑即红 → 拍定「SKILL 直读」（**D8**）。
- **F-O**（列 Q4 需拍板）〔对抗2 3a/3b·领域4〕机械等值门：领域镜已核**当前两 SKILL 该节确实字节相同（除 site= 行）**（正面），但 ADR-5 无候选 marker 文本验证「站点无关段能否圈干净」（撞基准5「圈太小没守住/圈太大永红」历史教训），且只借 sync_principles 的 `--check`、无 `--apply` 单一源（每次改要人工同步两份）。「单一源 snippet+注入」成本远低于被 defer 的全抽取。→ Q4 拍。

---

## dogfood 实证附记（本轮评审即在验证本 change 的目标态）

本轮主 session 用 `run_in_background` 并发跑 2 个 codex voice（design-voice/hr-tg）+ 4 子代理镜，主 session 全程无阻塞——**ADR-1「voice 移出关键路径、与镜工作重叠」在 Claude 宿主上成立**，两 voice 均 exit 0、reason_code=ok、拿到真跨模型 findings。**但**：两 voice 均在 <600s 完成（context ~2-3KB，非真实评审的 10KB+ 大负载），故**未触及 F-A 的核心未知**（900s 量级能否存活过 600000ms 外层上限）——这恰是 F-L「smoke 绿≠真实负载绿」的活样本：本轮 dogfood 绿，不代表目标态（长负载 voice）绿。

## 与既有工件

Step1 广审 `gstack-review.md`（B1-B7，commit 5116c7a）已入本报告合并池。**本报告 findings 尚未回灌 design/tasks**（除 F-E 的 ADR-6 引文已 [spec-review-amendment] 修正）——F-A 阻塞项可能重塑机制（若 run_in_background 不豁免 600s 上限，天花板/collect 都要改），故其余 amendment 留返修轮、待 Q1-Q4 拍板后一并落，避免在待重塑的机制上做局部优化（DOC-1 + 基准）。
