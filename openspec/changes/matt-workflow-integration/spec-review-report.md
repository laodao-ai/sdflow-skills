# spec-review-report — matt-workflow-integration

> 评审对象：四件套（grill 收敛后 dff6c95）。方法：Step1 autoplan 原生广审（CEO/Eng/DX 三 phase × Claude+codex 双声，46 条）→ Step2 对抗镜×2 + 接地镜×1 + HR-TG cross-model（16 条）→ Step3 主 session 合并去重对抗裁决（62 raw → 19 canonical）。全程 G2 无弹窗，决策登记制。

## Step1 广审（autoplan · native）

<!-- sdflow:step1-broad-review v1 mode="native" -->
原生执行佐证：codex 三声真实调用（session 019f4c16-…，99.7k/130.9k/72.8k tokens，exit 全 0）+ Claude 独立声 3 子代理。findings 全文与共识表见 [gstack-review.md](gstack-review.md)。**复用 autoplan outside voice 23 条**（守卫三关：native ✓ / 新鲜 ✓ / codex 段可解析 ✓）→ 不重开 design-voice。

## Step2 规划镜头与判定

- 领域镜 0（TG-01/02/03 无栈域命中）；对抗镜 2（角度=六声未覆盖面：T126/T127 契约内容、发布/并行运营）；接地镜 1。
- 接地镜：四件套全部代码事实（30+ 行锚）**零离异**；另证实 frontmatter 对 `_parse_plan` 惰性（外衣主张最小情形成立）。

<!-- sdflow:hr-tg v1 hit="TG-06,TG-08" evidence="plan 文件为 gate/skill/ship 三方共享契约（TG-06 弱）；新增 matt 套件跨 skill 运行时依赖且双上游未 pin（TG-08）" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" runner="codex" reason_code="-" findings="5" truncated="false" -->

## 合并裁决（19 canonical，反静默：无静默丢弃）

### 采纳（自动修，落 [spec-review-amendment]）

| # | 主题 | 严重度 | 命中镜 | 裁决要点 |
|---|---|---|---|---|
| F1 | **完成信号语义与时序**：gate 双通道是并集（:744）「双写 MUST NOT 单边」不可执行；checkpoint/勾框在双轴审**前**落盘→resume 跳过未审 ticket；重号复活旧 checkpoint | 致 | eng×2+hr-tg | 完成信号后置方案见 Q3（需拍板方向），结构不可变（只可追加新号）成文 |
| F2 | **T126 契约无注入通道**：config.yaml rules 段与 workflow.md ff 调用行均不在任务清单（CLI 实证 `openspec instructions` 零 wayfinder 引用；FF-0 先例=调用方注入缺一不可） | 致 | 对抗镜A（独家） | 任务补 config rules + ff 调用行 + map 路径显式传递 |
| F4 | **模式派发与路由机械化**：ship→skill 模式派发无字面契约（1.1/2.1 无共享约定）；键/marker 读取应脚本化（stdlib enum reader + route helper）；**marker 在但非法 → 停（UNKNOWN 语义），MUST NOT 静默回退**（防两管线混跑） | 致 | dx+ceo-codex+eng×2+hr-tg | 脚本化恰强化用户「零自动判断」拍板（prose→脚本），Phase B 提前进 Phase A |
| F3a | 试点严谨性受控修补：PIPELINE_RECEIPT（读到的键值/管线/marker/plan sha）、样本计入前核对 marker、NEEDS_CONTEXT 停摆率观测、选样拒绝条件成文、Why 补 wco P0/P2 证伪证据引用、token 维度尽力采集 | 高 | ceo×2+dx×2 | 与 Q1 拍板独立，先行落地 |
| F5 | frontmatter 语法冻结：仅 `impl-pipeline` 单键、无注释/示例/第二块；边界 fixture 清单（header 内 Task 文本/悬空 fence/重复 marker） | 高 | eng×2+hr-tg | |
| F6 | **TG-18 判定翻转**：producer→parser 边界须 golden-file 回归测试（进 sdflow-ship/tests/，先例 test_producer_parser_contract）+ 路由矩阵测试；proposal「无自动化测试面」表述修正 | 高 | eng×2+ceo | |
| F7 | 停机语义补全：统一 halt envelope（错误码/ticket/证据/副作用/恢复步骤）；BLOCKED 须落盘持久（report file 进 change 目录 git-tracked）；DONE_WITH_CONCERNS 处置一句（concerns 附给双轴审）；cannot-verify 消解设预算上界（超 N 文件/盘面不可解→退回 implementer）；「连续到 merge vs BLOCKED 停」在 spec 显式化 | 高 | dx×2+ceo-codex+eng-codex | |
| F8 | Blocked-by 拓扑机械化：stdlib 拓扑 helper（解析 Blocked-by + done_tasks → next-ready），确定性信号归脚本 | 高 | eng×2 | |
| F9 | 发布/运营缺口：①发布窗口**反向**风险（ship 链序先生效、sdflow-implement 链接后建→调不存在 skill）缓解句；②tasks 补 6.3 **运行 checkout 重跑 setup 还原**（全局 symlink 污染，静默）；③真撞车点 = **INDEX.md 能力表追加**（两在飞 change 同表尾插入），§6 step5 靶子修正（CLAUDE.md 托管块实测不重叠）；④workflow-cost-optimization roadmap 补 Phase C 占位防孤儿承诺 | 高 | 对抗镜B（独家） | |
| F11 | T126/T127 内容修正：逐 ticket zoom 设上界（≤N 张全文、超出按相关性截断）+阶段一成本观测点；design 决策段**内联回链来源 ticket**（机械 grep 锚，同 R-ID 模式）供瘦跑判定；三段分流判据改**事中**（跨 session/跨天/已 /clear 即切换）非事前预估 | 高 | 对抗镜A+hr-tg | |
| F10a | 上游依赖校验强化：出 ticket 起手从「查目录存在」升级为查语义能力集；CLAUDE.md 发布边界补「既有 SKILL 路由新增 skill」方向句 | 中 | ceo×2+dx-codex+hr-tg | 全套 version pin/rollout manifest 见 F10b defer |
| F12 | 可观察性：SHIPPED 摘要模板加 pipeline 字段（scope-check 补行）；config 键「在但值错」回显一行（区分键缺席）；生成 plan 正文顶部 HTML 自解释注释 | 中 | dx×2 | |
| F13 | resolver/domains 清单失效路径：取不到时 Standards 轴 MUST NOT 假通过——显式停或记「未覆盖」 | 中 | hr-tg（独家） | |

### 决策登记区

**[需拍板 Q1] 试点实验严谨度档位（TENSION：codex 双声 vs 用户已有拍板）**
codex 主张冻结数字阈值+全协变量+受控配对（X1/X4/C2 引 wco roadmap 同类决策定过数字门槛纪律）；你在三镜设计会已拍板「定性无阈值」（n=3-5 假精度）。**推荐：维持定性拍板 + F3a 全部机械严谨性修补落地 + 判赢材料显式声明局限。** 三面后果——系统：receipt/retro 通道现成、增量小；用户：每试点 change 多看一眼 receipt；开发循环：不冻结阈值保灵活、Phase B 拍板须自律防叙事带偏。主次判定：主=开发循环镜（判赢产物服务 Phase B 决策）。选 codex 路线则试点成本显著上升。

**[需拍板 Q2] T126/T127 是否拆出独立 change（TENSION：codex 独判 vs 用户已拍板 fold）**
codex X8 判 scope creep 污染归因；但判赢指标全为阶段三口径，mainflow 改动不进指标——「污染归因」论点实际不成立（A 镜反而批评指标不覆盖阶段一）。新事实：F2 修复使 T126 工作量比预估大（+config rules+ff 调用行）。**推荐：维持 fold**（fold-vs-defer 既有判据：workflow 循环固定成本高；任务组/需求已天然分层，实施可独立回退）。三面——系统：同 bundle 一次下发；用户：一次设计门；开发循环：省一整轮评审循环。主次：主=开发循环镜。拆则每块各付一轮 ff→grill→spec-review。

**[需拍板 Q3] F1 完成信号时序修复方案**
甲（推荐）：完成信号**后置**——implementer 实现期 checkpoint 不带 task 标签；双轴审+fix 环通过后由执行模式补打完成标签+勾框（审过才算 done；resume 发现「实现 commit 在、完成标签缺」→ 进入续审而非重实现）。乙：维持现时序 + 双写降格 SHOULD + 接受 resume 跳审风险靠冷层兜底。三面——系统：甲使 gate done 语义与「审过」对齐（完成判据真实性）；用户：无感；开发循环：甲多一段续跑判定逻辑。主次：主=系统镜。

**[自动决策]**（承 gstack-review AD1-AD5）
- AD6：F1-F13 采信为 spec-review-amendment（多镜收敛/实证/接地零离异）；F1 条款按 Q3 拍板方向二选一后定稿，先按甲落草案、乙为回退。
- AD7：codex「退回重写」总判不采纳为流程动作——可操作子项已全部拆入 F1-F14 逐条裁决，「重写 vs amend」差异在修补量非方向；登记供设计门复核。
- AD8：接地镜零离异 + E-verify（frontmatter 惰性证实）记录在案。
- AD9：复用 autoplan outside voice（三关全过），HR-TG 单开（site 不同）。

**[defer]**
- F3b 判赢方法论张力 → Q1；F14 拆 change → Q2。
- F10b version pin / rollout manifest 全套 → 超 Phase A scope，todolist 池（显式 change 字段）。
- B5 消费仓键不可发现（init update 不动 config，低危：缺省安全）→ todolist 池。

**[已裁掉]（反静默，原始发现+理由可审计）**
- X2「defer 机制转移成本」：defer→hand-off→清理 change 是 spec-workflow 既有全局结构（spec.md:81 原文），非本 change 引入或改变；重开率度量属 retro 全局议题。原始发现保留于 gstack-review.md。
- C7「删 quiz 弱化粒度检查」：D9 已经 grill 用户拍板收窄（MAY 切片建议节），C7 无新事实；残余关切被 F3a 选样拒绝条件+冷层哨兵吸收。

### 低置信项（一行带过，不静默滤除）
- A4 三段分流判据（置信中）已采纳入 F11；A5 map 路径迁移耦合（对抗镜A自证不成立，被 F2 吸收）；B1 窗口反向（置信高但危害受限于 tickets 已开仓）已入 F9。

## 度量锚（lens-metric，metrics.enabled=true）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="—" findings="4" 采纳="3" 裁掉="0" defer="1" 独立="2" sev="致1/高2/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="—" findings="12" 采纳="9" 裁掉="1" defer="2" 独立="0" sev="致2/高5/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="design-voice" findings="13" 采纳="9" 裁掉="1" defer="3" 独立="0" sev="致2/高5/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="hr-tg" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="1" sev="致2/高2/中2/低0" -->

（残余信任边界声明：分类归属/roster 完备性/hits 誊写准确为主 session 信任边界；采纳/裁掉/defer 为设计门拍板前临时裁决，拍板回写时最终化〔SR-M〕。）

## 修补执行

F1-F13 采纳项已落四件套，改动处标 `[spec-review-amendment]`；Q1-Q3 拍板后如翻改，随拍板回写调整。图（组件/序列/路由决策）核验存在且未过时——F1 若取方案甲，序列图完成信号时序需同步（已列入修补）。

## 收敛口

**建议进设计 HARD-GATE**：核心架构（单 skill 双模式/不 fork/gate 零改动外衣/手动路由）经 10 镜声无一推翻且接地零离异；62 条 findings 中可自动修项已修，剩 Q1/Q2/Q3 三项需你拍板（Q3 影响 spec 条款终稿）。拍板通过后按「拍板回写协议」写 frontmatter `ship-gate.design_approved: true` + lens-metric 最终化。
