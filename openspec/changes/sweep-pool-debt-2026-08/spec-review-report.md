# Spec Review Report · sweep-pool-debt-2026-08

- **评审对象**：`openspec/changes/sweep-pool-debt-2026-08/` 四件套（proposal / design / specs ×3 / tasks）+ decision-memo（参照）
- **日期**：2026-08-20 · **宿主**：claude · 主审强档，广审/领域/对抗中档，接地弱档
- **roster**：广审双镜（strategy / plan-eng）+ devex 领域镜（TG-28）+ 对抗镜 ×3（隐藏假设 / 失败模式 / 乐观估计与边界，高风险配置）+ 接地镜 ×1 + outside-voice ×2 站点（design-voice / hr-tg，跨模型 codex）。处置表（mirror-dispositions.yaml）本层 7 面全保留，无条件跳过镜。
- **dispatch 形态说明**：单批各镜互不依赖、均审同一盘面；因单条消息输出上限，Agent 派发拆为两条相邻消息（4+3），期间无任何盘面变更——语义等价于单批，如实记录。

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="broad,domain,adversarial,grounding" -->
<!-- sdflow:step1-broad-review v1 mode="subagent" -->
<!-- sdflow:hr-tg v1 hit="TG-17" declared="TG-05,TG-12,TG-14,TG-17,TG-18,TG-19,TG-23,TG-28" evidence="失鲜锚信任边界重划：锚值从 LLM 自报改脚本权威计算 + manifest/digest 防伪互锁 + 豁免通道改重锚协议（proposal What Changes T292 段）" -->
<!-- sdflow:declared-sites v1 declared="design-voice,hr-tg" -->
<!-- sdflow:outside-voice v1 site="design-voice" host="claude" runner="codex" reason_code="ok" findings="3" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" host="claude" runner="codex" reason_code="ok" findings="3" truncated="false" -->

> voice 执行注记：async·harness 分支（后台能力探针 PROBE_OK + 主 session 确证），内层 timeout 900s（config 未覆盖回落默认），run 目录 `.outside-voice/20260820T092837Z-sQyle2/`（dispatch-manifest.tsv 落盘），两站点 `.rc` sidecar 均为 `0`，stdout 直取 findings，无 stderr 转录。

---

## 拍板三问（决策登记区最顶端，人在设计 HARD-GATE 逐项勾选认/不认）

- **Q-scope 范围划界认不认？**
  自答：锚 proposal「Non-Goals」5 条（不做双读兼容·不动 gate 其余域·不动 18,000 门·不做时机机械捕获·不迁移 1.9.0 其他能力）——其中「不做双读兼容」经本轮评审**收窄为仅限 live 报告**（归档读点必须容忍旧 40-hex，见 D2/amendment），其余 4 条经查与目标一致。 [ ] 认  [ ] 不认
- **Q-deps 依赖/顺序认不认？**
  自答：锚 tasks 四票边界——原「票间无阻塞边、可任意顺序」被对抗镜证伪一处：票 1 落地后本 change 自身旧格式锚会令其余票 gate 自锁，已补 tasks 1.9（票 1 收尾重锚自身报告）作为顺序约束的替代救济；票 2 内部 DT-6 顺序（先本地收敛后改 CI）不变。 [ ] 认  [ ] 不认
- **Q-risk 风险赌注与对策认不认？**
  自答：锚 sdflow:hr-tg 的 hit=TG-17（信任边界重划）+ design Risks 表（本轮修订后 7 行）——最大赌注是 D2 fail-open 面（批准后实质改 tasks.md 无直接检测，旁路为完成度/偏离对账而非文本完整性检测，表述已收窄）与 D4/D9 诚实边界（时机自报、一致重算越权留痕，见 Q1 待拍板）。 [ ] 认  [ ] 不认

<!-- sdflow:gate-questions v1 q="scope,deps,risk" -->

---

## 决策登记区

### [自动决策]（高置信采纳，默认接受可覆盖；修订均已落盘标 `[spec-review-amendment]`）

- **D1 · C12 承重约束核验源选错（四镜独立收敛：plan-eng + 对抗镜①②③，置信 78–95）**——gate 端 `checkpoint(impl-review)` subject 豁免与 BR-7 真值表**代码已于先前 impl-review-fix change 物理删除**（`ship_gate.py:118-123` 退役注释 + `test_gate_freshness.py::test_impl_review_subject_no_longer_buys_any_exemption` 钉死回归）；memo C12 只读了滞后的 spec 原文。D9 方向不变，但实际工作量 = spec 死文字清理 + `sdflow-code-review` **新建**（非「补」）重锚协议。已修：design Context 订正条 + DT-7 + 票 1 措辞 + tasks 1.2/1.7 + spec delta REMOVED Migration 定性。
- **D2 · 归档 40-hex 锚会被新校验判坏 → SHIPPED 大面积回归（跨模型 voice 独家 critical，主审接地证实）**——design 原句「gate 不读归档」前提错误：`archived_verify_state`（ship_gate.py:460）经同一严格解析核读归档 verify 结论，`FIELD_VALIDATORS["reviewed_sha"]`（:1026）校验一切已识别字段；归档区 34 份 verify-report 携 40-hex 锚。已修：DT-1 + tasks 1.3/1.6 + spec delta 新增「归档报告旧 40-hex 锚不阻断 SHIPPED」Scenario（含变异证明用例要求）。
- **D3 · manifest 缺字节保真规范编码（双 voice 收敛）**——git 路径可含 Tab/换行/非 UTF-8，YAML 行清单编码欠定义 ⇒ 假失鲜/路径折叠。已修：DT-2 + tasks 1.1/1.6 + spec delta 编码条款 + 「控制字符与非 UTF-8 路径下 manifest 稳定」Scenario。
- **D4 · 自举自锁（对抗镜③独家）**——本 change 自身 spec-review-report 将以 40-hex 落锚，票 1 落地后其余票 gate 读旧锚判 UNKNOWN；「无旧报告存量」断言被实测证伪。已修：新增 tasks 1.9（票 1 收尾重锚自身报告）+ design Risks 行订正 + 票 1 切片描述。
- **D5 · code/verify 域比较机制未显式入任务（对抗镜①，主审读码证实 `ship_gate.py:950` 以锚 sha 作 git ref）**——已修：DT-2 补句 + tasks 1.1/1.2「两分支均改」+ spec delta code 域条款 + 测试覆盖图行。
- **D6 · anchor_writeback 只写锚与「结论+锚原子写入」Scenario 冲突（hr-tg voice）**——已修：DT-3 + tasks 1.5（`--set` 类接口一次调用落结论+锚）+ spec delta 原子写入 Scenario 补句。
- **D7 · CI 新步泳道条件（design-voice；DT-6 已有半句，tasks 缺）**——已修：tasks 2.4（复用同一 `if` 条件 + 更新 1.5.0 注释，后者亦对抗镜② F4）。
- **D8 · devex 文案缺口（DX-02/DX-05）**——五类 UNKNOWN 诊断 problem/cause/fix 三段 + SKILL 调脚本失败处置指引，已入 tasks 1.2/1.7 验收句。DX-04（废弃警告）判定为已被「锚非法→重跑写锚脚本」补救指引实质覆盖，不另做。
- **D9 · 数字口径订正（接地镜 + 对抗镜③）**——消费面 21 文件（漏 `openspec/specs/openspec-170-followup/spec.md` 与 `docs/workflow-skills/sdflow-spec-review.md`）、测试文件 11 非 10、可删面 ~100 行非 60–80。已修：proposal ×3 处 + tasks 1.6/1.8。
- **D10 · D2 缓解表述收窄（strategy）**——「两层旁路可捕」→ 完成度/偏离对账，非文本完整性检测。已修：design Risks 行。
- **D11 · ADR 落地形式（strategy）**——定为新增独立 ADR 文件 + adr/0026 头部 superseded-by 指针（仓惯例）。已修：tasks 1.8。
- **D13 · R1/R2 二次优化（主审复核轮，2026-08-20 人已同意折入）**——R1：「归档读点分流」改为**校验分层**（解析层 40|64 语法放宽 + 语义强制上移 live 读点；解析核不 fork，承 A4 共核，对存量零回归）；R2：写锚脚本**脏树守卫**（监视集未提交改动即拒写，ADR-7(b) 书面纪律机械化，D4 诚实边界收窄为「批准动作是否发生」）。已落 design DT-1/DT-3、tasks 1.3/1.5、spec delta（分层 AND + 脏树拒写 Scenario + 诚实边界收窄），单独 checkpoint（拍板前二次修订时序）。
- **D12 · 正向核验记录**：`import ship_gate` 零副作用可行（plan-eng 实测）；DT-1 命名对照满足 DX-03；memo C1/C3–C8/C11 及 design Context 全部行号接地镜逐条核实相符；`validate --archived` 实跑 61 passed / 17 failed 与 proposal 一致。

### [需拍板]

- **Q1 · TENSION：锚的防伪强度定位（hr-tg voice vs 主审）**——voice 视角：写锚无来源证明，producer 可在未审盘面跑脚本或一致重算两字段得到互证且 fresh 的锚，建议受保护 CI/签名 attestation 验签。主审视角：「一致重算 = 手跑重锚」已按 adr/0008 显式越权留痕定位（git 可审计，DT-7/spec 已登记「已知不覆盖」），D4 诚实边界亦明言只堵值错不堵时机；引入签名/CI 验签超出本 change 目标（通则④：低概率 · 单人仓 · 完美成本高）。**推荐**：维持现设计，但把 memo D4「脚本堵值错/伪造」的「伪造」一词理解收窄为「不一致篡改」（互锁堵不一致篡改与手抄错，不堵一致重算）——此收窄已隐含于 spec 诚实边界句，无需再改文件；signing 机制不做。三面后果——系统镜：维持 = 零新依赖、可回退性不变；signing = 新信任根 + CI 耦合。用户镜：维持 = 越权可审计不可阻断；signing = 单人仓无实际对手模型。开发循环镜：维持 = 零流程新开销；signing = 每次拍板多一道链路。**主次判定**：开发循环镜为主（单人工具仓，威胁模型是自误非对手），维持现设计。 [ ] 按推荐  [ ] 采 voice 方案
- **Q2 · memo 更正的处置**——本轮对 memo C2/C12/D4 的事实错误均以 design.md 订正条覆盖（memo 保留原文作历史记录，design 为准）。若您希望 memo 本体同步订正（decision-memo 是相位 C 生成的单一源，未来重新生成四件套时会再读它），请在拍板时说明，随二次修订一并落。 [ ] memo 保留原样（design 订正为准）  [ ] memo 本体同步订正

### [已裁掉]（反静默压制，可审计）

- **X1 [ref-check] · 接地镜 ID-2（C9 表述）**——机械核 quote-mismatch（主审转录行号误差）；对抗裁决亦不成立：C9 是「现状承重约束」的准确快照，T290 本就是要改它，无需改写。
- **X2 · plan-eng PE-3（BASE-25 组件清单缺表）**——镜自判通则④可接受，主审同意：组件 ≤4 且切片建议 + Impact 已隐式枚举，本量级不补表。
- **X3 [ref-check] · strategy F2（票 1 体量记录）**——机械核 quote-mismatch（主审转录误差）；内容为记录性（design 已如实承认票 1 最大且论证不可拆），无修改动作。原始建议（实现期若 diff 过大按 1.1–1.8 分段 checkpoint）留此供实现者参考。
- **X4 · 对抗镜③ #5（回滚粒度依赖 merge 策略）**——低概率低影响（镜自评 60）：done 默认 ff/no-ff 单点合并语义 + 仓内已有「rebase 击穿审计锚」先例纪律；不改设计，done 阶段照既有纪律执行即可。

---

## 各镜 findings 摘要

| 镜 | 回传 | 采纳 | 要点 |
|---|---|---|---|
| strategy（broad） | 3 | 2 | D2 缓解表述收窄；ADR 形式；票 1 体量（记录） |
| plan-eng（broad） | 2+1 正向 | 1 | **C12 核验源选错（首发）**；import 可行性正向核验 |
| devex 领域镜 | 4+2 N/A | 2 | DX-02 诊断文案、DX-05 失败处置指引；DX-04 部分覆盖不另做 |
| 对抗镜①（隐藏假设） | 2 | 2 | C12（收敛）；**code/verify 域 git-ref 解析假设（独家）** |
| 对抗镜②（失败模式） | 4 | 3 | C12 双重根因（协议无处可补）；spec/代码漂移定性；CI 注释 |
| 对抗镜③（乐观估计） | 5 | 4 | **自举自锁（独家 critical）**；可删面/测试数/消费面数字 |
| 接地镜 | 2 + 12 项相符 | 1 | C2 计数差；其余承重约束全数核实成立 |
| design-voice（跨模型） | 3 | 3 | **归档 SHIPPED 回归（独家 critical，已接地证实）**；manifest 编码；CI 泳道 |
| hr-tg voice（跨模型） | 3 | 2+1 defer | manifest 编码（收敛）；结论/锚原子写冲突；防伪定位 → Q1 |

置信分流说明：本层不设数值门槛；低置信项（X3/X4 类）一行带过上抛，未静默滤除。

**机械引用核**（`findings_ref_check.py`，20 条输入）：10 pass / 8 uncheckable（evidence_pack 形态，直进对抗裁决）/ 2 fail（X1/X3，标 `[ref-check]`）。

---

## 度量锚（lens-metric · config metrics.enabled=true；采纳/裁掉/defer 为设计门拍板前临时裁决，拍板回写时最终化〔SR-M〕）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="6" 采纳="5" 裁掉="1" defer="0" 独立="3" sev="致0/高3/中0/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="5" 采纳="3" 裁掉="2" defer="0" 独立="2" sev="致0/高1/中0/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="2" 采纳="1" 裁掉="1" defer="0" 独立="0" sev="致0/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="2" sev="致1/高1/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="3" 采纳="2" 裁掉="0" defer="1" 独立="1" sev="致0/高1/中1/低0" -->

> 残余信任边界声明：分类正确性、roster 完备性、findings 誊写准确仍是主 session 信任边界；emitter 只保证给定输入的确定性归约。`findings=N` 与合并池实收数的数值一致性同为信任边界，非机械可验。本 skill 只落锚不聚合，复评归 `/sdflow-retro`。

---

## 图表核验（design-diagrams）

design.md 含锚流对照表（TG-04 模版）+ v_old/v_new ASCII 流程图，与修订后决策一致（本轮为其补一条 v_old 定性脚注）；tasks.md 含测试覆盖图（TG-18，本轮扩两行）。无缺失/过时图。

## 收敛口（1.6）

**建议进设计 HARD-GATE**：三条 critical（归档 SHIPPED 回归 / C12 前提失实 / 自举自锁）与两条 high（manifest 编码 / code 域分支）均已按修订落盘四件套，方向层无未闭合缺口；待人拍板项仅 Q1（防伪定位，推荐维持现设计）与 Q2（memo 是否同步订正）。批准后按拍板回写协议落 `ship-gate.design_approved` frontmatter（本轮修订已在报告前落盘，属评审内 amendment，非「拍板前二次修订」——但**若您在拍板前再要求任何四件套改动**，须先单独 checkpoint 该改动再回写锚〔ADR-7(b)〕）→ `/clear` → `/sdflow-ship`。

*拍板记录区：（设计门拍板后由主 session 补一行人读结论 + frontmatter 机判锚）*
