# spec-review-report — sdflow-ship

> 2026-07-04 · 编排：sdflow-spec-review（Step1 autoplan〔原生 Step0+前提门 / 模拟全量降附录，见 gstack-review.md〕→ Step2 串行四镜〔对抗×3 Sonnet + 接地×1 Haiku，T20 纪律：autoplan checkpoint 210fddf 之后 fan-out〕→ Step3 主 session 对抗裁决）。
> 评审对象：四件套 @ grill 收敛版（c1691e7）。合并池 = autoplan 正文 + 模拟附录（2C/8H/8M/7L/DR-1~4）+ 四镜 findings，已去重。

---

## 决策登记区

### [需拍板]（设计门勾选；均触及 grill 已拍板决策的修订，故不自动决）

- **Q1｜D9 新鲜度必须按锚分域，否则链自锁**（C1，三镜独立确证：模拟附录 + 对抗镜1 + 对抗镜2，置信高·CRITICAL）
  现设计"对每份门禁报告"套新鲜度 → 首个实现提交（必触 openspec/ 外路径）即令 design-approved 判陈旧 → REFUSE_START，实现期自 DoS 整条链。两案：
  **A** design-approved 完全豁免新鲜度（只查存在+锚行）——简单，但"拍板后设计又被改"检不出；
  **B（推荐）** 按锚分域：design-approved 仅对 `openspec/changes/{change}/` 四件套路径的后续改动失鲜；verify/code-review 锚维持"openspec/ 外路径"判据——既解自锁又保住"改设计须重审"。
  后果：选 A 少 ~10 行实现；选 B 语义完备。二者都需 tasks 1.3 补"design-approved 后大量非 openspec 提交仍保鲜"反例断言。

- **Q2｜checkpoint 标签窗口下界**（C2，对抗镜1 实证 main 现存 task1..task11 遗留 → 无窗口全历史扫描当场假"齐 N"跳步；tmp_path 沙箱测试结构上测不出，置信高·CRITICAL）
  **推荐**：窗口 = superpowers-plan.md 首次提交 sha，`git log <sha>..HEAD --no-merges` 内收集（--no-merges 焊掉"实现期 git merge main 把外部已归档 change 的标签带进窗口"的残留，对抗镜1 追加发现）。tasks 1.2/1.3 需补窗口态测试（含 merge 污染态）。

- **Q3｜报告存在但从未提交时的新鲜度**（对抗镜2 F2，置信中高·MED-HIGH）
  `git log -1 -- <path>` 空输出 → 无 sha 可用，行为未定义。两案：**A（推荐）** 视为 fresh（人机同权：手写产物合法；JSON 注明 `freshness=uncommitted`）；**B** 视为进行中（强迫先 checkpoint）。推荐 A——D9 已确立"gate 不辨产者"，B 会把合法手工干预挡在门外。

### [自动决策]（附理由，默认采纳、设计门可覆盖）

- **D1｜task<N>- 标签约定注入点 = plan 生成层**（对抗镜3 F1 裁决降级 HIGH→已解）：SDD implementer 返回前自行 commit，主 session 事后跑 checkpoint 必然空转——但 footprint/rebrand 两轮先例证明可行路径 = **writing-plans 派发 args + plan 每任务 commit 步显式写 `checkpoint-commit.sh task<N>-<slug>`，由 implementer 自己执行**。tasks 2.3 已写"升格为显式标签约定"，amendment 补钉注入点字样。
- **D2｜design-approved 回写协议明确化**（对抗镜3 F2 + 模拟 H5 合并）：现 sdflow-spec-review 拍板后无回写动作，D5"拍板本就回写"与现状不符。定：**拍板发生后主 session MUST 立即把锚行写入 spec-review-report.md**（tasks 1.4 落 SKILL 约定）；ship_gate exit 3 提示文案含"若拍板已发生请人工/主 session 补锚（显式越权留痕）"。
- **D3｜UNKNOWN 独立退出码 exit 6 + verdict×exit×next 输出契约表**（模拟 H3+H6 合并）：UNKNOWN 停上抛不能复用 0/3/4/5；tasks 1.1 补契约表（含 SHIPPED、SKIP 语义）。
- **D4｜同报告多锚冲突 = UNKNOWN 上抛**（对抗镜1 新发现·HIGH）：同文件并存 `verify=PASS` 与 `verify=FAIL`（追加式写入/人工残留）时不猜优先级，判 UNKNOWN 点名冲突行。
- **D5｜无锚重跑熔断**（对抗镜3 F4·MED）：同一 invocation 内同一步重跑一次仍无锚行 → UNKNOWN 上抛人工，不无限静默循环。
- **D6｜"分支已并"判定钉死**（对抗镜1·MED）：`git log {base}..HEAD` 为空 或 feature 分支已删除 → 已并；detached HEAD → UNKNOWN。tasks 1.2 落。
- **D7｜plan 标题匹配 0 → UNKNOWN**（对抗镜3 F3·MED）：`### Task \d+:` 命中 0 时显式 UNKNOWN（上游 writing-plans 模板已有 3 个缓存版本，格式会变）；design 风险表改述"N 提取仍强依赖上游标题格式"。
- **D8｜T11 断言面扩到全文件**（模拟 H1/H2）：sdflow-done 派发 prompt 里的 `model: sonnet/haiku` 行（:61/:206）不在"模型选择节"内——grep 断言范围 = 四 SKILL **全文**裸模型名（引用句白名单），非仅模型节；T10 协议同步落 sdflow-code-review 相关行（:7/:30/:95）。
- **D9｜触发词避让 gstack /ship**（模拟 H7）：description 只收"/sdflow-ship""ship 这个 change"类含 change 语境短语，不收裸"ship/发布"。
- **D10｜TG 标注 grep 用字面子串 "TG-02"**（接地镜）：归档 proposal 实际格式为 `〔TG-01：…〕`/`（TG-20）`混用全角括号——不含括号的子串匹配即可，tasks 1.2 注明。
- **D11｜D9 头注释声明两条已知不覆盖**（对抗镜2 F3 + rebase 措辞加强）：①openspec/workflow/ 规则漂移不触发陈旧（设计取舍）；②rebase 可"伪造保鲜"（比原措辞"漏检"更强，接受并记录）。
- **D12｜模拟附录 H4/H8 与 8M/7L 按附录建议随实现落地**（archive 后重入误诊→final 前先查 archive glob；演练对象=hand-off 预置 T21-T24 小 change；余项 MED/LOW 见 gstack-review.md 附录，实现时逐条勾）。

### [已裁掉]（反静默压制，可审计）

- **X1** 接地镜"model-tiers 段缺失/与 T11 不符"——该段正是本 change 待建产物（tasks 3.1/3.2），非缺陷。
- **X2** 对抗镜1"第五退出语义"探查——未发现独立新语义，SHIPPED/UNKNOWN 已由 D3 契约表覆盖。
- **X3** 对抗镜2 已验证排除的五方向（merge --name-only 默认遍历祖先不漏检〔实现禁用 --first-parent，随 D11 头注释记一句〕、报告 rename/shallow clone 影响面窄、消费仓布局=Q1 同源、重跑连环两轮内收敛非死循环、--amend 残余已声明）——留档不进任务。

---

## 各镜 findings 摘要（全文见各镜返回与 gstack-review.md 附录）

| 镜 | 关键发现 | 处置 |
|---|---|---|
| autoplan（正文+模拟附录） | C1/C2 CRITICAL；H1-H8；8M/7L；DR-1~4 | C1→Q1、C2→Q2、H3+H6→D3、H5→D2、H1/H2→D8、H7→D9、H4/H8→D12 |
| 对抗镜1（盘面态穷尽） | C1/C2 独立确证+实证；多锚冲突 HIGH；merge 窗口残留 MED；分支已并未钉 MED | →D4、Q2（--no-merges）、D6 |
| 对抗镜2（D9 边界） | F1=C1 三次确证；未提交报告 sha 空 MED-HIGH；规则漂移不计陈旧 | →Q1、Q3、D11 |
| 对抗镜3（契约接缝） | SDD 抢先 commit 主锚失效 HIGH；design-approved 写入者未定义；N 提取依赖上游格式；无锚重跑无熔断 | →D1（历史先例裁决）、D2、D7、D5 |
| 接地镜（代码事实） | 7 项核验 6✅；checkpoint 格式/plan 标题/三 SKILL 锚点/resolver 退出码/“结论：**PASS**”实锚均证实 | 支撑 D1/D10；X1 |

置信分流：以上全部为高/中高置信；低置信项无（各镜均自带排除清单）。
图（design-diagrams）：design §三 gate 决策图存在且与 tasks 1.2 一致，但需按 Q1/Q2/D3-D7 拍板结果更新——标记"待拍板后修订"，不重画。

## 结论

四件套骨架（盘面即状态、机器锚行、零 git、透传）经三方独立攻击后站住；**两条 CRITICAL（Q1 链自锁、Q2 假齐 N）必须在实现前拍板修订**，其余 12 条自动决策已回流 tasks/design（标 [spec-review-amendment]）。
**收敛口**：建议进设计 HARD-GATE——请勾选 Q1（推荐 B）、Q2（推荐 sha+--no-merges）、Q3（推荐 A）；批准后即可 writing-plans。

---

## 设计门拍板记录（2026-07-04）

用户拍板：**Q1 = B**（新鲜度按锚分域）· **Q2 = 同意**（窗口 = plan 首提交 sha + `--no-merges`）· **Q3 = A**（未提交报告视为 fresh，`freshness=uncommitted`）。
已回流定稿：design.md（决策图窗口 / §四 exit 6 / D5 回写协议 / D9 分域重写 / 风险表改述）+ specs delta（exit 6 + 多锚冲突句、窗口 MUST、Q1/Q3 新增两 Scenario）+ tasks.md（1.1-1.5、2.1、2.3、3.3 全部占位定稿），均标 `[spec-review-amendment]`。

<!-- ship-gate: design-approved -->
