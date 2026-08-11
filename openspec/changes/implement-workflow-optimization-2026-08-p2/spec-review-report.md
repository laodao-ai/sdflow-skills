---
ship-gate:
  design_approved: true
  reviewed_sha: 34fcfcb9d576d0690feba40a9a505d470423d8c6
---

# spec-review-report — implement-workflow-optimization-2026-08-p2

评审轮：2026-08-10 · host=claude · 强档主审（opus）· 单批 dispatch：广审双镜（strategy/plan-eng）+ devex 领域镜（TG-28）+ 对抗镜 ×3（高风险档：BREAKING 裁决地基改造）+ 接地镜 + design-voice（codex/gpt-5.6-sol）。

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="broad,domain,adversarial,grounding" -->
<!-- sdflow:step1-broad-review v1 mode="subagent" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-05,TG-14,TG-19,TG-21,TG-22,TG-23,TG-24,TG-28" -->
<!-- sdflow:outside-voice v1 site="design-voice" host="claude" runner="codex" reason_code="ok" findings="5" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="design-voice" -->

TG 命中：TG-05（新数据对象 mirror-dispositions.yaml）/ TG-14（新组件 findings_ref_check.py）/ TG-19/21/22/23/24 / TG-28（devex：SKILL 行为 BREAKING + contract 枚举 + bundle 推下游）。HR-TG∩ = ∅（脚本判定，依据模型判定集见锚行 declared）。领域镜栈判定：不命中 TG-01/02/03，唯一领域镜 = devex（spec-review-only domain）。

---

## 决策登记区

### [需拍板]

**Q1 · DD2「condition-not-met」无处落锚——本轮最高收敛 finding（6 源：strategy F1 / plan-eng F1 / devex F1 / 对抗镜B F1 / voice V2 / 接地镜⚠）**

- **问题**：DD2 与 spec-workflow spec Scenario 要求条件跳过的**普通镜**落锚 `runner="none" findings=0` 并带「成因 condition-not-met」，声称扩展「`runner="none"` 成因清单」。但该清单（host-unknown/secret-hit/fallback-unavailable）实为 `reason_code` 枚举，contract 明文「仅 `sdflow:outside-voice` 锚必填，`sdflow:lens-metric` 锚无此字段」（`lens-metric-contract.md:12`）；DD2 自己又砍掉了「新 reason_code 字段」候选；design Non-Goals 明文「不改 lens-metric 锚 schema」。三处文本互相矛盾，`condition-not-met` 机读落点不存在。
- **加重证据（voice V2 独家）**：现行 emitter 强制非 outside-voice 普通镜行 `runner==host`（`lens_metric_emit.py:146`、contract:80-81 约束①）——即便不带成因，跳过锚行 `runner="none"` 本身就会被 emitter **fail-closed 拒收**；`anchor_lint.py:508/820` 的普通镜行校验同样不识别。实施 1.4/3.2 时必然二选一违约。
- **选项 A（推荐）· 合法组合扩展、成因不进锚**：contract 约束① + emitter + anchor_lint 扩一条合法组合「普通镜行 `runner="none"` ∧ `findings=0`」（contract 升版本，枚举域不动）；`condition-not-met` **不作为锚字段**——跳过成因由 `mirror-dispositions.yaml` 的 `condition` 字段（机读）+ 报告一行散文承载；DD2/spec/tasks 1.4「扩成因清单」措辞整体改写；Non-Goals 改「不改 lens-metric 锚**字段集**（合法组合矩阵扩展除外）」。
- **选项 B · 新增 `cause` 可选字段**：lens-metric 锚真加字段（仅 `runner="none"` 时出现），anchor_lint/emitter/aggregate 全链同步识别，schema 升 v2。
- **三面后果**：系统镜——A 改动收敛在合法组合判定（emitter/lint 各一处）+ dispositions.yaml 已有 condition 字段复用，可回退；B 是真 schema 扩面，三个消费脚本全动，改动面 ~3 倍。用户镜——A 的跳过成因在 retro 注记与报告里可见，锚行少一个字段但审计链完整（锚存在性 + dispositions 条件 + 报告散文三层）；B 锚行自含成因，单点可读性略优。开发循环镜——A 不新增字段语义、心智负担最低；B 为一个恒定值（条件跳过是普通镜 runner=none 的唯一新成因）开一个字段，信息密度趋零。**主次判定**：开发循环镜为主——B 的字段唯一取值恒为 condition-not-met，等于把常量编码进 schema，A 以组合矩阵表达同一事实且面小 3 倍。
- **默认处理**：批准 A 则实施期改 DD2/spec/tasks 1.4 措辞 + contract/emitter/anchor_lint 三处（并入 commit A roster 面）。

**Q2 · 「误杀率 = 0」红线大概率首轮撞线，追查后无关门判据（对抗镜C F3 + 对抗镜A F4）**

- **问题**：3-5 份报告的可核采纳 findings 量级实测为 60-200 条（单 change 最高 72 条采纳），强档重裁与历史裁决一致率哪怕 97-98%，期望误判 1-4 条 ≠ 0——红线在统计意义上大概率首轮不过；而「出现即逐条追查后才可部署」没有定义追查后**怎样算过门**（历史误标能否剔除分母？模型方差与协议缺陷怎么区分？），实质风险是卡死在 2.1/2.2 后被迫走文档外的「人工强行放行」。
- **推荐 · 三类归因关门法**：重裁不一致项逐条人工归因入三类——①历史误标/口径漂移（剔除分母，需在重放报告记归因证据）②模型方差（同一 finding 复裁一次，二次仍不一致才计入）③协议缺陷（真误杀）。**红线改为「③类 = 0」**；①②类如实报数不挡部署。误杀率语义不变（协议不得杀真金），假精确消除。
- **备选**：维持字面 = 0 + 允许人工放行留痕（后果：放行动作无判据可循，每次都是临场发明——正是补丁摞补丁的起点）。
- **三面后果**：系统镜——三类归因法多一层人工分类但流程可关闭、可审计；字面 0 则门的可判定性系于运气。用户镜——重放报告多一列归因，读感无碍。开发循环镜——三类法把「追查」从开放题变成检查单。**主次判定**：开发循环镜为主——部署门必须可关闭，不可关闭的门必然被绕过。
- **默认处理**：批准则写入 design DD5 + tasks 2.2 验收句。

**Q3 · grounding 镜降采样草案建议撤回（对抗镜C F1/F2 + 对抗镜A F2 + voice V3）**

- **问题**（三路独立攻击同一处置行）：① **判据不一致**——DD6 #3（broad scope 审计）以「守卫非产量逻辑」豁免，#10 grounding 同为核验/守卫类（机械读码核验 spec 代码事实）却按独立率产量逻辑砍，同表内同类角色双标，design 未论证差别。② **代理信号错位**——「delta 是否触碰已存在文件」是 diff 性质，「design 引用既有代码事实」是正文文本性质；纯新增文件 + 大段引用既有代码集成事实的 change（brownfield 常态）会系统性漏派，恰是 grounding 最该出手的场景。③ **统计上最站不住**——grounding 是 13 行里样本最大（80 findings）、独立率数字最稳（±1 finding 仅摆动 1.25pp）的行，反而被砍得最狠；样本薄的行（#2 broad 18 条、#4 history 21 条）±1-2 条即摆 5-11pp 却未标注方差。
- **推荐**：撤回 #10 降采样草案，grounding **恒跑**（本轮接地镜 23/24 全对且抓住 condition-not-met 待实施态，即为其守卫价值实证）；DD6 表 #10 依据改「守卫类，同 #3 豁免产量逻辑」。
- **备选**：保留降采样但判据改为「四件套文本 grep 命中既有文件路径/符号引用」（文本性质对文本判据，机械可判且无 ①② 两病）——代价：多一个 grep 谓词要定义与维护。
- **三面后果**：系统镜——恒跑零改动零风险；文本 grep 判据引入新谓词面。用户镜——恒跑每轮多一个弱档镜的等待（弱档，墙钟影响小）。开发循环镜——恒跑心智负担为零；grep 判据每次误判都要归因。**主次判定**：系统镜为主——降采样收益是省一个**弱档**镜（全 roster 最便宜的一个），为此付出判据维护 + 漏派风险，收支倒挂。
- **默认处理**：批准撤回则 DD6 表改一行，tasks 3.2 从降采样清单去掉 grounding。

### [自动决策]（默认采纳，设计门可覆盖；均已按下方 amendment 清单落进四件套）

- **D1（Critical·致）`findings_ref_check.py` 输入契约未定义、引用形态无界**（plan-eng F2 + 对抗镜A F1 + voice V1）——归档实抽样证伪「finding 引用总是干净 path:N」：7 条里 5 条为函数名冒号（`foo.py:read_verify_state`）/ 多行号（`ship_gate.py:238,260`）/ 设计层引用（"D1"、tasks 段落），无界文本面手搓解析即基准 5 反面教训复刻，且机械层无法区分「证据包」与「无引用」，会把合法的缺失类/跨文件类 finding 错杀进已裁掉区。**裁决**：采纳。修法（amendment 已落 DD4）：① Step2 各镜 findings 输出契约改为强制机读字段（`{file, line, quote}` 或 `evidence_pack`），脚本只吃结构化 JSON、不解析 markdown 散文；② 输出三态——pass / fail / **uncheckable（抽取不出干净三元组或为证据包/设计层引用 ⇒ 不裁，直进强档裁决）**；「无引文无证据包 = 机械裁掉」仅在结构化字段确认两者皆缺时触发。
- **D2（Important·高）引文子串核未绑定所报行号**（voice V4）——「单行引文为目标文件子串」可被任意合法行号 + 文件他处常见文本绕过，三查全绿。**裁决**：采纳。amendment：检查③ 改「引文命中所报行（或显式行范围内）」。
- **D3（Important·高）脚本级崩溃路径未定义**（对抗镜B F2 + plan-eng F4）——fail-open 静默放行未核验池（validator 防线整体失效无人知），fail-closed 击穿「MUST 恒产报告」。**裁决**：采纳。amendment（DD4）：脚本本体不可恢复错误 ⇒ **显式降级**——整批 findings 标 `[ref-check-unavailable]` 直进强档裁决 + 报告显著标注机械门未生效，MUST NOT 呈现「全部 pass」假象；补脚本级崩溃 pytest 场景。
- **D4（Important·高）history 镜「大规模改动」阈值零定义**（对抗镜A F3 + strategy F2）——spec Scenario 的 `N` 是占位符，「机械可判」名不副实（判据有确定性输入 ≠ 阈值已定）。**裁决**：采纳。amendment：tasks 3.2 加子句「给出 N 具体取值与判定命令（`git diff --numstat` 阈值 / `--diff-filter=R`），随 roster 段落盘」。
- **D5（Important·高）mirror-dispositions.yaml 解析手段未选型**（plan-eng F3）——仓内既有惯例「禁 import yaml、YAML 读取点收敛走 yq」（anchor_lint.py:7、adr/0036），retro_report.py 现无任何 yaml 消费面，直接 import yaml = 未声明第三方依赖 + 违背 fail-closed 语义收敛。**裁决**：采纳。amendment（DD1）：解析走 yq（同 anchor_lint `_yq()` idiom，承 adr/0036）。
- **D6（Important·高）D3 承诺的前瞻「方向性判据」设计相位未交付，Open Questions 误宣「无」**（对抗镜C F4）——decision-memo D3 明文「设计相位定宽松方向性判据」，design 只关了 proposal 三项，此第四项沉默漂移成 roadmap 残项。**裁决**：采纳。amendment：补 DD7——「连续 2 个 change 采纳率环比降 >10pp（对照 retro 基线）视为劣化信号，触发裁决协议归因复查」。
- **D7（Important·高）删 <80 滤后强档裁决输入无上界**（对抗镜B F3）——单场次历史最高 415 条 findings，validator 只杀引用失实类，「C4 实证净变化小」是拿现状语料论证目标态输入面（基准③味）；唯一兜底是事后 token 观察。**裁决**：采纳。amendment（Risks）：补「合并池 > 100 条时分批裁决（每批 ≤50，批间携带已裁清单防重复采纳），报告标注分批数」。
- **D8（Important·高）token_snapshot 在 codex 宿主的 done-final 会记错 transcript**（voice V5）——helper 硬编码 `HOST="claude"`（token_snapshot.py:40）且无 session id 时无条件取同 cwd mtime 最新 Claude transcript（:90），与主 spec「Codex 无本会话 transcript 落 anchor=false/no-transcript」冲突；done-final 新采集点扩大既有缺陷暴露面（fold 处理，不另开 change）。**裁决**：采纳。amendment：tasks 4.1 加子句「done-final 接线时补 host 判定：codex/unknown 宿主不走 Claude mtime fallback，直接落显式降级行 + 回归测试」。
- **D9（Minor·中）DD6 表统计诚实度两处**——① findings<30 的行独立率 ±1-2 条摆 5-11pp 未标注（对抗镜C F2）；② `disposition="淘汰"` 为 schema 合法值但四件套无一处定义淘汰的 roster 段落地动作（strategy F6，目标态 producer 会产出此形态）。**裁决**：采纳。amendment：DD6 加脚注「Σfindings<30 的行独立率仅作参考、不单独定论」；DD1 加一句「淘汰 = roster 段整段移除该镜派发逻辑，yaml 条目保留作历史注记」。
- **D10（Minor）文档一致性小修集**：① tasks 1.2「Step2 括注」实为 description 的 Step3 句、且应显式列出删「(<80 滤除)」（devex F2）；② Modified Capabilities 行补 BREAKING 标记（devex F3）；③ BASE-30 考古残句两处（design DD4「T112 原文写…升格为」、spec:78「旧规则假绿点…消灭」括注）删除（strategy F3）；④ proposal 成本估算段「弱档 validator」已被 DD4 机械脚本取代、adr/0041 同句括注过时——proposal 段更新 + tasks 5.1 加收尾同步句（对抗镜C F5）；⑤ token-snapshot-anchor delta 补已知边界一句「done 收尾跨 session 重试时 token 统计可能重复计入（view-only 精度边界）」（对抗镜B F5）。**裁决**：全部采纳，见 amendment 清单。

### [已裁掉]（反静默压制：原始发现 + 裁掉理由，供设计门复核）

- **X1**（对抗镜B F4）mirror-dispositions.yaml 手误炸整份 retro 报告，建议 pre-commit lint。**裁掉理由**：fail-loud 正是 DD1 设计意图（adr/0016 宁红勿静默）；消费方为只读非阻塞工具，爆炸半径止于「下次手工跑报告被拦」；pre-commit lint 属防御深度加宽（通则④——概率低、影响小、既有 fail-loud 已兜）。
- **X2**（strategy F4）DD1/DD4 列 ≥2 候选未写三镜+主次判定。**裁掉理由**：两者为 D2 已定方向下的实现形态收口，非 TG-23 级选型；援引 BASE-12「琐碎决策不强制——避样板税」豁免（D2 本体已在 decision-memo 写满三镜）。
- **X3**（strategy F5）成本估算无美元区间。**裁掉理由**：本仓评审 LLM 用量走订阅制，无按次计费口径，token 倍数量级为既有惯例（strategy 镜自己置信亦标低-中并预判此豁免）。
- **X4**（plan-eng F5，低置信一行上抛不滤）组件图未画 spec-review 人门分岔与 DD5 重放支线——文字已完整，图为速览辅助，不修（设计门若认为值得可要求补）。

---

## 各镜 findings 与裁决汇总

| 镜（raw） | 档位 | findings | 采纳 | 裁掉 | defer(需拍板) | 独家贡献 |
|---|---|---|---|---|---|---|
| strategy | sonnet | 6 | 4（D4 共、D9② D10③ 独） | 2（X2 X3） | 1（Q1 共） | 淘汰态缺口、考古残句 |
| plan-eng | sonnet | 5 | 3（D1 共、D3 共、D5 独） | 1（X4） | 1（Q1 共） | yq 选型分叉 |
| 领域镜 devex | sonnet | 3 | 2（D10①② 独） | 0 | 1（Q1 共） | tasks 1.2 定位错、BREAKING 可发现性 |
| 对抗镜1（隐藏假设） | sonnet | 4 | 2（D1 共·归档实证、D4 共） | 0 | 2（Q2 共、Q3 共） | 归档抽样证伪 path:N 前提 |
| 对抗镜2（失败模式） | sonnet | 5 | 3（D3 共、D7 独、D10⑤ 独） | 1（X1） | 1（Q1 共） | anchor_lint 代码级证据、输入无上界 |
| 对抗镜3（乐观估计） | sonnet | 5 | 3（D6 独、D9① 独、D10④ 独） | 0 | 2（Q2 主报、Q3 主报） | 独立率敏感性亲算、0 红线统计不可达 |
| 接地镜 | haiku | 2（提醒） | 0 | 0 | 1（Q1 共·⚠注记） | 23/24 代码事实全核实（无造假引用） |
| design-voice（codex） | gpt-5.6-sol | 5 | 3（D2 独、D8 独、D1 共） | 0 | 2（Q1 共·emitter 拒收独家证据、Q3 共） | emitter fail-closed 拒收路径、codex 宿主 transcript 错记 |

**对抗裁决说明**：Q1 六源收敛 + 代码级证据（contract 明文 / emitter 约束① / anchor_lint 注释）确证为真实 schema 矛盾，非措辞问题。D1 由归档报告实抽样支撑（对抗镜A 真开过 archive），置信高。voice 与主审无 tension 项——5 条 voice findings 与同族镜全部同向或独家补充，无分歧需登记。低置信项仅 X4，一行上抛未滤。

**接地镜结论**：四件套所有代码事实引用（SKILL 行号、LMA 五元组键、阈值 10、token_snapshot 接口、contract 字段、三份归档报告、adr/0036/0016/0041）**全部真实存在且位置准确**，premise-verification 无违反。

## 度量锚（metrics.enabled=true）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="12" 采纳="8" 裁掉="1" defer="3" 独立="5" sev="致1/高4/中2/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="10" 采纳="6" 裁掉="3" defer="1" 独立="3" sev="致1/高3/中1/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="3" 采纳="2" 裁掉="0" defer="1" 独立="2" sev="致0/高0/中0/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="1" 采纳="0" 裁掉="0" defer="1" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="5" 采纳="3" 裁掉="0" defer="2" 独立="2" sev="致1/高2/中0/低0" -->

> 残余信任边界（契约声明保留）：分类归属正确性、roster 完备性、findings JSON 誊写准确仍是主 session 信任边界；emitter 只保证给定输入的确定性归约。采纳/裁掉/defer 为设计门拍板前的临时裁决，拍板回写时最终确定〔SR-M〕。

## 收敛口

**建议：先落 Q1-Q3 拍板与自动决策 amendments（已应用），再进设计 HARD-GATE。** 四件套骨架健康（接地全绿、premise 无造假、Non-Goals/假设/回滚完备），但 Q1 是真实 schema 矛盾、D1 是 P0 关键路径上的输入契约缺失——两者不定案，commit A/B 实现期必返工。拍板 Q1-Q3 后本报告条件性支持进入 HARD-GATE → 批准 → `/sdflow-ship`。
