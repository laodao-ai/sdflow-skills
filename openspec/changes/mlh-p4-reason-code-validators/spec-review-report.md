<!-- 设计门拍板后由主 session 写 ship-gate.design_approved（未拍板前无此 frontmatter）-->

# spec-review-report · mlh-p4-reason-code-validators

<!-- sdflow:step1-broad-review v1 mode="simulated" -->
> **Step1 广审模式说明**：本轮 autoplan 广审层由一个 fresh-context 广审子代理承担（未原生跑 autoplan skill，因本 change 是 workflow-infra 而非产品，autoplan 的 CEO/user 产品镜多不适用）——按 mode="simulated" 诚实标注（降级但适配）。outside-voice 由 fresh claude-fallback 子代理承担（runner="claude-fallback"，未走 codex helper）。

## 评审规模

5 个 fresh-context 冷镜并行：**广审**（eng/design/DX/交付）+ **对抗×2**（隐藏假设边界 / 失败模式系统冲突）+ **接地**（逐条核代码锚）+ **outside-voice**（退一步质疑立项/ROI/试点）。**结论：设计 direction（grill 收敛的 3 语义洞：假阴/假绿/假新鲜）方向正确；但 5 镜揭出 2 条立项级 + 2 条 design-direction + 1 条 ADR 早熟 + ~13 条实现落地修，共识度高。**

---

## 决策登记区

### [需拍板 Q-A · 立项/scope] 剔除 T82（review_disposition_check）？

**问题**：4/5 镜指 T82 净值薄到负。唯一真价值「防真空通过」**现状 prose 已覆盖**（`sdflow-roadmap/SKILL.md:346`「小节缺失视为不通过，MUST NOT 真空通过」）；机械化边际收益仅「防模型忘跑该 prose」，代价却是：① **子串陷阱是机械化自造的危害**（模型读 prose 本无此坑）② bundle 回灌开销 ③ 易误读的 `DISPOSITION-UNCHECKED` 码 ④ 不消除逐条对账手做（Non-Goal）。且 dogfood 负例括号变体/位置与真实 task-log 不符（洞察8，另一假绿）。

**推荐：剔除 T82，本 change 缩为 T80+T81**（两者都真替换 load-bearing 手做机械判定）。给 T82 真实触发条件（Review 处置格式统一后 / 出现真空通过实例后）再单起。
**三面后果**：系统=去掉一个净负机械层、少一处假绿面；用户（判赢人）=change scope 更聚焦、更好归桶；开发循环=少一份 bundle 回灌 + 少三处 T82 修。
**主次**：内在价值 > 凑 frontier；剔 T82 是主。

### [需拍板 Q-B · 试点选择] 本 change 还当首个 tickets 试点吗？

**问题（洞察3/4，最重）**：① **自指矛盾**——proposal.md:5「试点不影响设计」vs design.md:51 D4 留 T82 理由列「维持 3 票 frontier（试点目的）」：试点需求反向决定 scope、留薄票凑数，观测到的是人为编排非真实 3 宽独立 frontier。② **判据污染**——违 pilot-briefing.md:35「禁跨桶比较」（三成员跨 T80 重git/T81 中parser/T82 trivial 三桶，判据① impl 墙钟对照失效）；入场即 ~17 findings + 叠 3 个 first-of-kind（首试点+新 adr/0018+T80 首个 validator-subprocess），哨兵③无法区分「管线漏」vs「change 难产」。

**推荐：首个 tickets 试点换 T63 或 T89**（pilot-briefing 候选池，单文件解析、逻辑面集中、契约明确、天然单桶、有现成失败案例转 TDD seam）；本 change 剔 T82 后按内在价值走**既有 superpowers 管线**，或作为管线验稳后的第 2+ 试点。切断「试点需求↔设计 scope」耦合。
**三面后果**：系统=试点信号干净可归因；用户=判赢结论不被 change 难产污染；开发循环=本 change 少背「首试点」的额外约束（档位钉死 mid 等）。
**主次**：换试点对象 > 剔 T82 > 其余实现修（outside-voice 逐字）。

### [需拍板 Q-C · design] F1/T80-c dirty 检测反噬守卫复用主路径

**问题（广审 F1 + 对抗A T80-c 共识，高/高）**：grill Q3 的「工作树 dirty→fail-safe stale-dirty-tree」用了**错信号**——`git status --porcelain -- {change_dir}` 含 autoplan 本会话写进 change_dir 的 `gstack-review.md`（必然未提交）+ 活跃编辑期未提交的 proposal/design → guard **几乎恒** stale-dirty-tree → 拒绝复用 → spec-review 再跑 codex = **双 codex**，恰与守卫「避免双 codex」目的相反。
**推荐采纳修法**：dirty 只看**源文件**（proposal/design/tasks/specs）mtime 是否晚于产物 mtime、**排除评审产物本身**——即「产物产出后输入是否又被改动」，非「目录里有无任何未提交文件」。此修法比 grill Q3 更准（正确界定 staleness）。
**主次**：修 dirty 语义为源文件对比 > 保留全目录扫描。

### [需拍板 Q-D · design] 爆点5+F5/爆点1 T81 输入源与锚落点（三镜共识）

**问题**：① **头部扫描漏真实声明**（对抗B 爆点5，自我演示）——泛化 tg02_hit 只扫 proposal 头部区，但真实 proposal 把 TG 声明在 **section 标题锚**（`## 需求优先级〔TG-19〕`），**本 change 自己的 proposal 就没有顶部 `〔TG〕` 行**（用括号 `（TG-01）`+design section 锚）→ dogfood 跑自身 proposal 得 `依据已声明:[]` 却实际命中 TG-08 → `依据` 恒空、D3 安全价值侵蚀。② **锚无落点**（广审 F5 + 对抗B 爆点1，高）——`依据已声明` 在既有 hr-tg 锚 schema（只 `hit`+`evidence`）无字段 → D3 诚实信号持久化时蒸发。
**选项**：(a) 扫 proposal 头部 **+ section 标题锚 `## …〔TG-NN〕`**（中间路，覆盖真实声明习惯）；(b) producer 侧（ff 生成约束）强制顶部 `〔TG〕` 声明行（改契约）；(c) 重新考虑 hr_tg 输入是否该由模型传判好的 TG 集（回 grill Q1 备选 A）。**均须配** 扩 hr-tg 锚加 `declared="TG-..|none"` 字段 + anchor_lint 认得。
**推荐**：(a)+扩锚——最小改动覆盖真实声明形态且不改 producer 契约；但 D3 根基（泛化 tg02_hit 够不够）需设计门定。
**主次**：先定输入源覆盖面（a/b/c）> 再扩锚落点（必做）。

### [需拍板 Q-E · ADR] adr/0018 降 Proposed？

**问题（洞察5，中高）**：adr/0018 随 grill checkpoint 以 **Accepted** 提交，却从**三个未写一行代码的样例**蒸馏，而 5 镜已证三形态落地全崩（依据无锚落点 / UNCHECKED 码 SKILL 断层 / fail-safe 反噬）——ADR 用「已理解后果」口吻记了「后果尚未理解」的东西。
**推荐**：adr/0018 降 **Proposed** + 加「落地可行性未证」caveat，待三形态至少一个真 ship+dogfood 验证后再升 Accepted。原则（不投射假信心）本身对、不否定。

### [自动决策] 实现落地修（设计门默认接受，实现期落）

| # | 修项 | 来源镜 | 严重 |
|---|---|---|---|
| A1 | tasks 5.2 pytest 路径改 `sdflow-init/assets/workflow/tools/tests/`（现指向不存在的下游 tests/，=验收门假绿）；5.1 明确「下游不含 tests/，一致核对仅脚本本体」 | 广审F2+对抗A B1（共识高） | 高 |
| A2 | T80 subprocess 用 `check=False`+手判 returncode，非零→EXIT_FAIL/保守 stale；补「非 git 仓/git 128」负例（CalledProcessError 不在样板 except 元组） | 对抗A T80-a | 中高 |
| A3 | tasks 钉 hr_tg 定位 trigger-catalog 路径机制（`--trigger-catalog` 由 SKILL 传 `$RULES_ROOT/trigger-catalog.md`；`openspec/workflow/` 无 trigger-catalog 副本、`__file__.parent.parent` 会炸）；dogfood 5.3 显式走 $RULES_ROOT | 对抗A H1 | 中高 |
| A4 | tasks 钉 T80「先 dirty 短路、后新鲜度」+ 空 git-log 输出行为（从未提交 change_dir → `int("")` ValueError） | 对抗A T80-b | 中 |
| A5 | T81 命中集 `sorted(set(...))` 确定序 + 输出串文法/分隔符声明（全角｜非机读则显式声明面向模型） | 对抗A T81-a | 中 |
| A6 | tasks 同步 `sdflow-spec-review/SKILL.md:180` guard 枚举加 `stale-dirty-tree` + 规定 script-code→guard= 映射；code-review:169 注明有意分叉（不加） | 广审F6+对抗A E1+对抗B 爆点3 | 中 |
| A7 | proposal Success Metric/Compliance 对 T82 打星降级（若保留）：「存在+非空机械化，逐条判定显式为模型信任边界」，别让 adr/0006「无残留手做」覆盖未落实半场 | 对抗B 爆点4 | 中 |
| A8 | spec.md:12「产物早于**传入的** change_mtime」改为脚本自取（D1 已反转自跑 git，spec 内部矛盾） | 广审F9 | 低 |
| A9 | 订正 `lens_metric_emit.py:9` 代码注释里残留的「ADR-11」豁免引用（design 已改引代码先例，但被引的那行注释自身仍写 ADR-11=自指） | 接地+广审F8 | 低 |
| A10 | roadmap.md:134「4.D.4 断言无未处置」回填注「机械层只保存在+非空，逐条归模型（见 mlh-p4 D4）」防 traceability 漂移 | 广审F7 | 低中 |
| A11 | 订正 design Compliance 误挂「T82 状态枚举锚 SKILL.md:312-316 单一源」（T82 根本不读状态枚举） | 对抗A E1 | 低 |
| A12 | T80 argparse `--change-dir`、T81/T82 CLI 入参契约补齐（对齐 T80 明确度） | 广审F4 | 低 |
| A13 | T82 非空判据可测定义（若保留）+ 负例夹具取两个真实 in-repo task-log（含「」/『』变体 + bullet/组头位置） | 广审+对抗A/B+洞察8（共识） | 中 |

> **注**：A7/A13 仅当 Q-A 决定保留 T82 才需；剔 T82 则连带消解。

### [已裁掉] 反静默压制留痕

| # | reviewer 原始发现 | 裁掉理由 |
|---|---|---|
| X1 | 「HR-TG 单一源 parse 脆性（成员行 `**bold**`、号段跳空会漏）」（对抗A/B 初疑） | **对抗B 实测证伪**：`re.findall(r'TG-\d\d', line)` 对相邻 `**` 免疫仍抽 8 个；TG-01…26 号段无跳空全两位数；引言行/复评注记行不含 `TG-\d\d`。残留仅 `\d\d` 在 TG-100+ 截断（当前 max 26，非议题）。非实现期爆点。 |

---

## 各镜 findings 摘要（详见决策区）

- **接地镜**：8 锚逐条核验**无硬 code-vs-claim 不符**（tg02_hit :495-519 / HR-TG 8 成员 / lens_metric 形态 / SKILL 锚 / roadmap :62/:312-316 / adr/0002:21 / adr/0018·0006(b)·0008·0016 / T33-35 全真）。唯 1 LOW = A9。
- **广审镜**：F1(dirty反噬,高)/F2(pytest假绿,高)/F5(锚蒸发,中高)/F3/F4/F6/F7/F8/F9。
- **对抗A**：B1(pytest,高)/T80-a(CalledProcessError,中高)/H1(trigger-catalog落位,中高)/T80-b/T80-c/T81-a/T82-a/E1/B2。
- **对抗B**：爆点1(锚蒸发,高)/爆点5(头部漏声明,高·自演示)/爆点2(T82非空矛盾,高)/爆点3(enum,中高)/爆点4(SuccessMetric,中)/Q1裁掉。
- **outside-voice**：洞察1/2(剔T82)/洞察3/4(换试点·最重)/洞察5(adr降Proposed)/洞察6(adr/0006过冲反闸)/洞察7(novelty stacking)/洞察8(dogfood格式)。

## 收敛口

**不建议直接进设计 HARD-GATE 批准放行**——5 镜共识指向本 change 需**结构性重估**（Q-A 剔 T82 + Q-B 换试点对象）而非仅打磨。建议人在设计门先裁 Q-A/Q-B（scope+试点），据结果决定：剔 T82 + 换试点 → 本 change 缩 T80+T81 走既有管线、修 Q-C/Q-D/Q-E + 自动决策；或坚持原 scope → 至少必修 Q-C/Q-D（design bug）+ A1/A2/A3（会真炸）再放行。**主次：Q-B（换试点）> Q-A（剔 T82）> Q-C/Q-D（design bug）> 自动决策。**

---

## 锚区（机读）

<!-- sdflow:hr-tg v1 hit="TG-08" evidence="design 失败模式表 TG-08 命中，TG-08 属 HR-TG 子集；领域 cross-model 覆盖折入对抗镜+outside-voice，失败模式/fail-closed 路径已密集审" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="simulated-source" runner="claude-fallback" reason_code="simulated-source" findings="7" truncated="false" -->

### 度量锚（lens-metric·metrics.enabled=true）

> 计数由 `lens_metric_emit.py` 从结构化 findings + roster 确定性归约（exit 0）。**残余信任边界**：分类（某 finding 归哪镜）+ roster 完备性 + findings 誊写准确仍是主 session 信任边界，emitter 只保证给定输入的确定性归约。设计门拍板后随最终裁决重算（SR-M，best-effort）。

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="—" findings="13" 采纳="12" 裁掉="1" defer="0" 独立="7" sev="致0/高4/中7/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="—" findings="8" 采纳="8" 裁掉="0" defer="0" 独立="2" sev="致0/高3/中2/低3" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="claude-fallback" site="design-voice" findings="7" 采纳="5" 裁掉="0" defer="2" 独立="4" sev="致0/高2/中3/低0" -->
