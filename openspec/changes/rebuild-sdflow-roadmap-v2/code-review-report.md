---
ship-gate:
  code_review: pass
---

## code-review 报告 — rebuild-sdflow-roadmap-v2

> DIFF_BASE=`91a097c`（merge-base main..HEAD，matt-workflow-integration 归档后的 main），24 文件 +1460/-379，纯 Markdown。
> 结论（人读）：**pass**——29 条 canonical findings，24 采纳全部当场修复（12 高 9 中 3 低，零致命），3 裁掉（附理由），2 defer（T130 已在册 + T131 新登记）；修复后仓级 pytest 877 全绿（无脚本波及，冒烟）。

### 命中范围

- 栈：纯 Markdown 指令/模板/约定——domains 清单不命中；CR-01~09 **9/9 N/A**（清单镜逐条判定）；领域镜位由「spec R1-R7 → 落地全链一致性核对」承担。
- 镜配置：清单/一致性镜×1 + 对抗镜×2（编排指令运行期失效面 / 跨文件契约与遗漏）+ 历史镜×1 + outside-voice codex×2（code-voice 全量 diff + hr-tg）。
- trivial_shape：**NOT_EXEMPT**（behavior-path: sdflow-roadmap/SKILL.md）→ 全量 fan-out。
- gstack/review（Step1 并入·原生执行·G2 适配；Codex 侧由 Step2.5 outside-voice 承担避免双 codex）：**Scope Check: CLEAN**（24 文件全部映射 plan 7 任务或 change 过程产物；CONTEXT.md 为 grill 期词条+合并双保留；todolist 为 T129/T130 defer 登记）；**完成度 7/7**（checkpoint 标签齐；tasks 5.1-5.3 按 Q-C 前置②受控延后，非缺口——前置核验记录见 impl-notes）。
<!-- sdflow:step1-broad-review v1 mode="native" -->

- **HR-TG 判定：命中**（沿 spec-review 先例，diff 实证同两面）。
<!-- sdflow:hr-tg v1 hit="TG-06,TG-08" evidence="roadmap 包结构为 producer/回填助手/实施引用三方共享契约且 tracker doc 成为双 skill 共享约定源（模板-SKILL 多处口径矛盾实锤）；matt 套件跨 skill 运行时依赖未 pin（降级路径两处缺失实锤）" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="none" findings="5" truncated="true" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" runner="codex" reason_code="none" findings="6" truncated="false" -->

### Findings（置信 ≥80，全部已裁决；采纳项全部当场修复）

模板↔SKILL 契约矛盾群（hr-tg/code-voice/清单镜三源收敛，修复落 task-log/roadmap/memo/long-flow 模板 + tracker doc）：

| # | 严重度 | 问题 | 命中镜 | 处置 |
|---|---|---|---|---|
| F1 | 高 | task-log-template 无「Review 处置」骨架/包状态字段，SKILL 多处断言其存在（真空通过风险）| 清单镜+对抗B+hr-tg | 已修：模板补骨架+三态示例+`> 状态：ACTIVE|review-waived|未审待恢复`；SKILL ①「缺失视为未通过，先建后判」 |
| F2 | 高 | checklist ④ 越权逃生舱丢失（spec Scenario 授权的「带 N 张未决票结晶」在 SKILL 消失）+ 30 票归档 map 的 frontier 扫描盲区（归档=计数非全 resolve、旧 map 无 closed 标记、④只扫当前 map）| hr-tg+对抗A+清单镜 | 已修：④三层重写（全目录扫描/abandoned 留痕/越权留痕）+ 归档前核对+`Status: archived` |
| F3 | 高 | 阶段 0 日志与 checklist ②「每条完成记录关联 roadmap 阶段」天然冲突 | hr-tg | 已修：阶段 0 关联概览节声明式例外 |
| F4 | 高 | task-log 模板产出清单含 memo.md 路径——三件套引用考古层违例（规则 3）| hr-tg | 已修：清单去 memo，改注释声明 |
| F5 | 高 | roadmap 模板附录要求远期阶段填子任务数/估时/实施 change 名——反向打破近细远雾 | hr-tg | 已修：附录仅近期，远期雾区占位 |
| F6 | 高 | `implement-{name}-phase-N` 命名与回填解析器 `PREFIX_RE`（`-p<N>`）不兼容——新 roadmap 实施 change 将全部 NO_ASSOCIATION（已实测正则不匹配）| code-voice | 已修：SKILL+模板全改 `-p<N>` + 契约句 |
| F7 | 高 | Codex 降级长档路径与 memo 模板「短档专用、不叠加」自相矛盾 | code-voice | 已修：降级模式 memo 转必需长档考古层（例外态）双侧声明 |
| F8 | 高 | 票状态机不完整（仅 claimed/resolved；frontier 要求「未领取」、④要求无 open/claimed——open/abandoned 无定义）| code-voice+hr-tg | 已修：`open→claimed→resolved|abandoned` 四态，SKILL+tracker doc 逐字对齐 |

编排指令失效面群（对抗镜 A 独家 + 历史镜，修复全落 SKILL.md）：

| # | 严重度 | 问题 | 命中镜 | 处置 |
|---|---|---|---|---|
| F9 | 高 | grilling/domain-modeling 未装降级——design 失败模式表承诺、SKILL 零落地 | 对抗A | 已修：票内降级普通讨论句 |
| F11 | 高 | gate-0 五项全过直接结晶会短路 office-hours（五项不检验需求真实性）| 对抗A | 已修：结晶前仍查野心信号 |
| F14 | 高 | continue/replan「区分依据」零判据，全靠临场发挥 | 对抗A | 已修：启发式判据句 |
| F16 | 高 | checklist ②「最小引用图」无引用格式锚——报行号的机械感是虚假的 | 对抗A+清单镜 | 已修：「（见 design.md 决策 N）」锚点句式+模板示例注释 |
| F10 | 中 | 套件语义漂移检测缺失（design 承诺未落地）| 对抗A | 已修：漂移告警句 |
| F12 | 中 | office-hours 回流无再判据 | 对抗A | 已修：回流重走判定点①+显式陈述 |
| F13 | 中 | 长档+野心双信号并发无优先级、对照表无组合例 | 对抗A | 已修：office-hours 前置声明+对照表第 6 例 |
| F15 | 中 | replan 顺序不保护 task-log 历史（含刚落的重规划记录）| 对抗A | 已修：只可追加句 |
| F17 | 中 | checklist ⑤「本次讨论期间」无基线锚——长档跨 session 无从机械核对 | 对抗A | 已修：preflight 后记 CONTEXT/adr 基线入 map/task-log |
| F18 | 中 | checklist 对存量四件套/逃生舱包无条件分支（②头部章判定对 legacy 是范畴错误，被逼「硬卡 vs 违规跳过」二选一）| 对抗A | 已修：legacy 适配句+N/A 合法第三态 |
| F19 | 中 | tracker doc preflight 仅起手一次，二次 chart/续跑期损坏无检测 | 对抗A | 已修：新增票前轻量复验句 |
| F21 | 低 | SKILL 三分支含 office-hours 而 workflow.md 三段分流无之——职权面需显式区分 | 历史镜（独家）| 已修：office-hours 属 roadmap 讨论层专用、不进 mainflow 编排声明 |

文档一致性群：

| # | 严重度 | 问题 | 命中镜 | 处置 |
|---|---|---|---|---|
| F20 | 中 | proposal.md:71 + design.md:85 残留「只读 roadmap.md/task-log.md」——与 SR-19 修正后的假设 3 自相矛盾（代码实读已核：仅 roadmap.md）| 对抗B | 已修〔impl-review-fix 失鲜豁免通道，各一行〕 |
| F29 | 中 | long-flow-skill-paradigm 轮数分档表（<10/10-30/>30）与「禁事前轮数预估」硬禁令矛盾，旁注不足以阻止误用 | code-voice | 已修：表头+正上方「历史判据（已废弃）」显式标注 |
| F28 | 低 | roadmap 直写与 spec-workflow「wayfinder 收敛接 ff」衔接契约的豁免关系未在 SKILL 声明 | code-voice | 已修：结晶节边界句（两路径互斥不叠加）|
| F25 | 低 | spec delta 两处笔误（「旧 §5 验收总纲」实为旧 §6；「SKILL.md:265」实为 :272）——落地文件均正确，spec 自身引用错 | 清单镜 | 采纳：**归档 delta 对码同步时按码订正**（四件套失鲜保护，不在飞改；本行即 archive 子代理的指令锚）|

### 已裁掉（反静默压制，可审计）

- X1〔清单镜〕兼容提示语「四文件包」vs spec「四件套形态」措辞漂移——裁掉：提示语非契约字面，功能等价。
- X2〔对抗A-1.4〕explore↔wayfinder 升降级无抗震荡——裁掉：对抗镜自评低置信非爆点；无雾降级的「未持久化预检」已结构性抑制高频震荡，每次损耗仅一次 chart 开销。
- X3〔对抗B-5〕「路标行」（SKILL 节题）vs「去向说明」（spec 正文）同义词并用——裁掉：同节内两词互见自解释、纯术语无功能影响；归档 spec 同步时顺手统一。
- 置信 <80 滤除项：无（全部 findings 带 file:line 实证）。

### 修复 / defer 台账

- 自动修 **24** 项：SKILL.md 18 处（467→488 行）+ 模板/tracker doc 9 处 + proposal/design errata 2 行〔impl-review-fix〕+ F25 归档期指令锚。
- defer **2** 项：T130（ff-generation-constraints 边界句「四件套」→「三件套」，实施期已自发现登记，对抗 B 独立复核确认）、T131（workflow.md wayfinder 探测 Claude 单宿主，对抗 B 发现，新登记，均显式挂 change）。
- T10复核: 无「无客观判据的 ≥2 方案」项——修复均为 spec/design 承诺的落地补齐或矛盾消解，判据客观。
- 修复后验证：仓级 pytest 877 冒烟绿（无脚本改动）；SKILL↔tracker doc 状态机/持久字段/再入约定三处逐字复核一致；`phase-N` 活示例清零。

### 度量锚（lens-metric）

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="—" findings="18" 采纳="14" 裁掉="2" defer="2" 独立="11" sev="致0/高6/中8/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="—" findings="5" 采纳="4" 裁掉="1" defer="0" 独立="1" sev="致0/高3/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="code-voice" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="4" sev="致0/高3/中1/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="hr-tg" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="3" sev="致0/高6/中0/低0" -->

（emitter 确定性归约 exit 0 落锚；分类/roster/誊写准确性仍是主 session 信任边界。broad findings=0 为真实值——其价值在 scope/完成度守卫本轮 CLEAN；hr-tg 独立 3 全高危、code-voice 独立 4——跨模型双 site 本轮贡献显著。）

### 结论

☑ **建议进 /sdflow-done**（verify → hand-off → archive → commit → merge）。defer 残差 T129/T130/T131 已入 todolist（hand-off 引用）；F25 spec 笔误由 archive 子代理按码订正。
