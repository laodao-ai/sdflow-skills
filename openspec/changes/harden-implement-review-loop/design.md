## Context

`sdflow-implement` 是阶段三 tickets 管线的执行编排器,由 `sdflow-ship` inline 调用。四处现状问题经拷问阶段与阶段二设计评审逐条查实(证据锚见 `decision-memo.md` C1-C9;评审 findings 见 `spec-review-report.md`):

1. **零档位声明,且是跨机队正确性缺口**——`sdflow-implement/SKILL.md` 全文 grep 不到 `model-tier`/`resolve-models` 任一命中(C1)。后果不止于架构不对称:`model-tiers` Requirement 明写"MUST NOT 在 Codex 宿主下把 Claude 机队的模型名用于 Codex 机队子代理",无第零步即拿不到本机队档位。
2. **`sdflow-done` 自身的第零步是已知不安全形态**——`sdflow-done/SKILL.md` 的 `### 0.4` 是**裸 `eval` 一行**,无清脏/预检/退出码捕获/eval 后校验,正是 `sdflow-code-review`/`sdflow-spec-review` 模板明文警告的 V1 陷阱("裸 `eval` 会被脚本缺失静默吞")。∴"逐字对齐三个姊妹"不成立——照 `done` 抄会把不安全形态传播成第四份。
3. **T10 标签遮蔽了真实的场景差异**——`sdflow-implement` 借用的"熔断仲裁"与其余落点的"≥2 方案自动选"触发条件本质不同(C8)。
4. **测试执行范围与实际覆盖脱节**——现有"结束前跑一次全套件"未分粒度;而链路里(`sdflow-implement`→`sdflow-code-review`→`sdflow-done`)没有任何一步执行"全部票完成后的聚合回归"(C3)。

另有一处命名遗留:tickets 轨产出的计划文件沿用 superpowers 轨的 `superpowers-plan.md`。

## Goals / Non-Goals

**Goals:**
- 给 `sdflow-implement` 补齐档位解析机制,四类子代理声明为 mid;**同时把 `sdflow-done` 的裸 `eval` 一并升级**,并用机械 parity 守卫锁住四份拷贝。
- 把 T10 按语义拆成两条**具名**独立规则(`T10-choice` / `review-loop-breaker`),消除"一个标签、两种触发条件"的隐患。
- 让每 feature ticket 的测试执行范围与"这一票该测什么"对齐,同时补上链路里缺失的聚合回归执行点。
- 把 `sdflow-implement` 补进 `spec-workflow` 的"模型档位映射"与 Codex 子代理授权两处清单。
- tickets 轨计划文件更名为 `tickets.md`。

**Non-Goals:** 详见 `proposal.md` Non-Goals 节。

## Decisions

完整依据/被砍候选/代价见 `decision-memo.md`,此处只列结论指针:

- **D1**:四类子代理声明 mid,补第零步四步(清脏→预检→捕获退出码→eval 后校验)。**对齐目标 = 四步语义,不是逐字复制**〔spec-review-amendment Q5 拍板〕:三份现存模板本就不一致(`done` 是裸 eval;`code-review` 与 `spec-review` 四步文案相同但"本步第 N 项"交叉引用不同,那是**依文件本地结构派生的量**),`sdflow-implement` 又没有编号起手步骤列表 ⇒ 逐字照抄必产悬空引用。∴ 跨文件交叉引用一律改**具名锚点**("见预检步"),并新增 `hack/tests/test_tier_resolution_parity.py` 对归一化核心段做逐字节比对。
- **D1b**〔新增,Q4 拍板〕:`sdflow-done/SKILL.md` 的 `### 0.4` 一并升级为同一套四步。理由 = 同一片一致性面,且第四份拷贝正要生成,此刻修最便宜(基准 3 面治优先于点补)。
- **D2a**:`T10-choice`(Group A)②步升 strong,落点见下方 scope-check 表。**适用边界如实声明**〔spec-review-amendment H2/M16〕:本决策**没有**外部实证支撑——superpowers 的"fix-loop 第 4–5 轮换更强模型"讲的是**同一 task 反复修不好**,那是 Group B 语义,已移到 D2b 引用;`decision-memo` 原先把它挂在 D2a 名下、且标注的出处 C7 记的锚(串行派发 / per-task gate)与该论据无关。D2a 的真实理由只有一条:**②档历史触发频率极低(40 余份归档 change 里仅 1 次真实②档记录,且那次是 Group A),边际成本近零;收益侧同样无实证**——这是一个成本低、收益未证的低风险决策,不是被验证过的模式移植。
- **D2b**:`review-loop-breaker` 独立成文,不再出现"T10"字样,②步升 strong。**这一处才是 superpowers fix-loop 类比真正成立的地方。**两项机制修正〔spec-review-amendment H3/H4〕:
  - **身份键**:从"同 file:line + 同问题"改为"同文件 + 规范化问题指纹",**行号只作定位不作身份**——修复几乎必然移动行号,用行号当身份会让同一未解决问题被认成新 finding、轮次计数清零,`MUST NOT 无限循环` 兑现不了。
  - **互斥终态**:原三级处置只回答"finding 是否成立",而触发它的原因是"成立但连续修不掉" ⇒ 确认成立后既无新动作也无终态,可绕回原循环。改为三个互斥出口:不成立→关闭;成立且可修→strong 档 fixer 修复并**仅复验一次**;成立但不可修→进 buglist 并停。
- **D3**:每 feature ticket 测试范围收窄为"单元 + 本票 e2e 场景 + 本票 `Blocked-by` 链上模块的集成测试",MUST NOT 跑与本票无依赖关系的集成/e2e〔Q3 拍板:保留中间档,不用绝对禁令〕;出票模式新增不计入 3–6 预算的强制"实现验证"收尾 ticket。**收尾票的定位见下方专节。**
- **D3b**〔新增,Q6 拍板〕:"聚合套件"的发现方式**复用 `sdflow-devenv` 的既有答案**——**让工具自己回答,不解析构建文件**(基准 5)。见下方专节。
- **D4(不做)**:任务复杂度动态选 implementer 档位。
- **D5**〔新增,用户拍板〕:tickets 轨计划文件更名 `tickets.md`,superpowers 轨保持原名;gate/route 用共享 resolver 探两名,双存在 fail-closed。见 `adr/0033`。

## 收尾票的定位:实现期聚合回归门,不是最终完整性门

〔spec-review-amendment · Q2 拍板 · 回应评审 C1〕

评审 C1 指出:收尾票跑在 `sdflow-implement` 内(即 `sdflow-code-review` 及其自动修复循环**之前**),而 code-review 会改并提交源码却不重跑聚合套件,`sdflow-done` 的 verify 又只读证据不执行 ⇒ 终门引用的锚点相对最终代码不是最新的。

**拍板结论:维持现状的机制位置。** 定位澄清如下,四件套与 delta 一律按此措辞:

- 收尾票 = **实现期**聚合回归门。它回答的是"全部功能票实现完毕这一刻,聚合套件是否通过",**不声称**"最终代码通过聚合套件"。
- **既有 Requirement「verify 为收尾最终门,位于所有修复之后」未被触碰**:verify 仍在 `sdflow-done`、仍在所有修复之后,本 change 不修改它。收尾票不是 verify、不替代 verify、不前移 verify。
- code-review 之后的修复由 **code-review 自身的保障机制**覆盖(双轴/领域镜 + 置信过滤 + 对抗裁决 + 其自身的 fix 循环)。本 change 要解决的是**实现期间**的覆盖空洞,不是给 code-review 再加一层。
- **残余风险如实登记**:"收尾票锚点相对 code-review 修复而言不是最新"是**已知且接受**的,五问分析见 `decision-memo.md`「接受的边角」。
- **证据锚措辞 MUST 与该定位一致**:verify 引用该票时,锚的语义是"实现期聚合套件通过"而非"最终全量回归通过",MUST NOT 在 verify 报告里把它写成后者。

## 聚合套件的发现契约(D3b)

〔Q6 拍板:复用 `sdflow-devenv` 的答案〕

`sdflow-implement` 要铺给**任意**下游项目,而"单元+集成+e2e 聚合套件"此前无契约。**MUST NOT 解析 Makefile / package.json 去找 target**——那是 `add-sdflow-devenv` 已经付过学费的路(脚本 562→119 行、7 个 fail-closed 罢工分支,`docs/sad/07` 附录 A21;基准 5)。契约:

1. **命令来源优先级**:① `openspec/config.yaml` 的 `test-suites.{unit,integration,e2e}` 显式配置;② 缺失则由收尾票的 implementer 从仓内既有约定(CI 配置、README、`devenv` 三层框架产物)判定并**在票报告里写明命令原文与判定依据**。
2. **"能不能跑"由工具自己判**:候选命令**真跑一遍**看退出码,MUST NOT 靠解析构建文件预判 target 是否存在。
3. **缺层不罢工**:仓内确无集成层或 e2e 层时,该层记「未覆盖(本仓无此层)」并附判定依据,**MUST NOT** fail-closed 停机——`sdflow-implement` 的承诺是"不管什么项目都能跑完实现管线",每个罢工分支都在背叛它。
4. **证据 schema(确定性,可机验)**:收尾票报告 MUST 含每层一行:`<层> | <命令原文> | <退出码> | <测试时 git rev-parse HEAD>`;未覆盖层写 `<层> | — | 未覆盖 | <依据>`。
5. **失败分类**:退出码非 0 时 MUST 分四类处置——① 本 change 引入的回归 → 进 fix 循环;② 仓内既有红测(改动前即红,用 base SHA 复跑确认) → 记录并放行,不阻塞;③ flaky(同命令复跑一次即绿) → 记录并放行;④ 环境故障(依赖缺失/网络) → halt envelope 停并上抛。**Standards 轴 MUST 核验修复方式未靠加 skip、改测试配置、删除或弱化断言蒙混过关**(原措辞只禁"删除或弱化断言",挡不住加 skip)〔spec-review-amendment H9〕。

## 收尾票与普通票的执行契约差异

〔spec-review-amendment H9〕普通票强制 red-before-green 逐 slice 实现,而聚合套件一次绿则无 red、无 diff。∴ 收尾票 MUST 显式豁免/定制三点:

- **豁免 red-before-green**:该票不写产品代码,验收物是**证据**不是 diff。
- **证据落 report file,不依赖 commit**:`checkpoint-commit.sh` 在干净树上直接成功退出、不建 commit ⇒ "引用该票自身 commit"可能根本没有 commit。∴ 主证据锚 = 该票的 impl-report 文件路径 + 其内的 SHA 三元组;commit 存在时附之,不存在不判缺。
- **R-ID 归属**:该票 `R-ID: all`,语义为"覆盖本 change 全部需求的聚合验证",Spec 轴据此核验而非逐条溯源〔spec-review-amendment M6〕。

## T10 scope-check(统一计数口径)

〔spec-review-amendment M1/M2/M4〕**"落点"的定义**:一处**规范性** T10 引用(grep 命中行为单位,一行含一处算一处)。规范性 = skill 指令 / bundle 规则 / spec / 承载定义的文档;**不含**分析类与历史记录类文档。此前 proposal「4 处」/design「6 个、其余 5 处」/Success Metrics「6 个、其余 4 处」/设计图「9 处」/`adr/0031`「等 5 处」五种口径互不一致,以本表为唯一口径。

**"T10" 保留为历史别名**:新增两条具名规则,CONTEXT.md 术语表登记别名关系 ⇒ 分析类文档提及"T10 三级协议"不算陈旧,无需扫改。

**【Group A · `T10-choice`(≥2 方案自动选)——15 处,②步统一加 strong】**

| # | 落点 | 性质 |
|---|---|---|
| 1 | `sdflow-init/assets/workflow/workflow.md:106` | canonical 定义 |
| 2 | `sdflow-ship/SKILL.md:164` | 复述(含台账行格式) |
| 3–5 | `sdflow-code-review/SKILL.md:7, 170, 283` | frontmatter description + 概述 + ②步展开 |
| 6 | `sdflow-code-review/SKILL.md:526` | 台账行格式 |
| 7–8 | `openspec/specs/spec-workflow/spec.md:83, 638` | ②步(`:83` 另补回丢失的"按三镜+主次") |
| 9 | `openspec/specs/impl-orchestration/spec.md:27` | 出票模式·粒度争议 |
| 10–11 | `sdflow-implement/SKILL.md:203, 271` | 出票模式·粒度争议 |
| 12–13 | `sdflow-implement/SKILL.md:282, 545` | 一致性自扫·矛盾裁决(规则 + 出处说明) |
| 14 | `sdflow-init/assets/workflow/ff-generation-constraints.md:68` | 切片粒度争议 **〔M1 补漏〕** |
| 15 | `docs/workflow-overview.md:257` | 人读**并列定义**(非指针,②步未声明 strong) **〔M1 补漏〕** |

**【别名保留 · 不编辑——1 处】**

- `openspec/specs/spec-workflow/spec.md:29` —— 「判据定义引主 spec T10 需求,本需求不重定义」。它属 Requirement「评审决策登记进报告,不中途打断」,**该 Requirement 与本 change 其余改动无关**;为一处别名改名把整条无关 Requirement 拉进 delta(MODIFIED 是整段替换)代价明显大于收益,而"T10"已保留为历史别名、指针仍解析得到 ⇒ **不编辑**(通则④)。

**【Group B · `review-loop-breaker`(熔断仲裁)——1 处,脱钩 + ②步加 strong】**

- `sdflow-implement/SKILL.md:491` —— 不再提"T10"

**【不动 · 仅引用尾部处置,未提②步——2 处】**

- `sdflow-implement/SKILL.md:372`、`openspec/specs/impl-orchestration/spec.md:60` —— "走 T10(defer 或停)"
- 🔴 **delta MUST 原样保留这两处的 "T10" 字样**〔spec-review-amendment H6〕:MODIFIED Requirement 归档是**整段替换**,首版 delta 把 `:60` 改成了"按 defer 或停处理",T10 被静默删除,与本表【不动】自相矛盾。
- 〔回应 M11〕按 `CONTEXT.md:299` 的术语澄清,这两处其实属**第三类场景**(问题问出来了但盘面查不到答案,天然跳过①②直取③),严格说也该脱钩。但给第三类场景命名与定义属**加宽**(通则③),本次不做,已记 todo。

**【本 change 自产,需同步——2 处】**〔spec-review-amendment M4〕

- `openspec/CONTEXT.md:299` —— 术语条目改为登记两条具名规则 + "T10"别名关系。
- `openspec/adr/0031` —— 已 Accepted,**正文不改**,仅追加一行指向具名规则与本表。

## ADR 判定

〔spec-review-amendment H15:此前只有 D2b 开了 ADR,D1/D3 同样满足判据却既没开也没记"为何不需要"〕

| 决策 | 难逆转 | 缺上下文会意外 | 有真实权衡 | 判定 |
|---|---|---|---|---|
| D1/D1b(档位解析 + 修 done) | 否(纯文本,可 revert) | 否 | 弱(四步形态无争议) | **不开** |
| D2a/D2b(T10 拆分) | 是 | 是 | 是 | 已开 `adr/0031` |
| D3/D3b(收尾票 + 聚合契约) | **是**(改变阶段三执行形状) | **是** | **是**(执行点位置、缺层处置) | **开 `adr/0032`** |
| D5(计划文件名分轨) | 是(下游 plan 文件已落盘) | 是 | 是(两文件名 vs 一个) | **开 `adr/0033`** |

## 设计图

```
出票模式 frontier 依赖图(新增收尾 ticket 位置)
〔spec-review-amendment:首版图把 sdflow-done verify 直接画在收尾票之后,
  省略了中间的 sdflow-code-review 及其修复循环 —— 那正是评审 C1 所指的
  失鲜路径,被图掩盖了。现补全,并标出接受的残余风险。〕

  Task 1 ──┐
  Task 2 ──┼─Blocked-by──▶ Task N(实现验证,收尾)
  Task 3 ──┘                  │
  (功能票,3-6张,           跑聚合套件(单元+集成+e2e)
   各自:单元 + 本票 e2e     + 标准 implementer/双轴审/fix 循环
   + Blocked-by 链上集成)    → 证据 = <层>|<命令>|<退出码>|<SHA>
                              │
                              ▼
                    sdflow-code-review(冷层主审)
                    ├─ 会自动修改并提交源码
                    └─ ✗ 不重跑聚合套件
                       ⚠️ 残余风险:收尾票锚点相对此处修复不是最新
                          —— 已知、接受,由 code-review 自身保障机制覆盖
                          (见「收尾票的定位」节与 decision-memo 接受的边角)
                              │
                              ▼
                    sdflow-done verify(最终门,位置不变)
                    引用收尾票 impl-report 为「实现期聚合覆盖」证据锚,
                    不扩张自身职责;该锚**按管线条件化**(见下)
```

## Risks / Trade-offs

〔spec-review-amendment Q1:维持一个 change,但 D3 的风险敞口单独成节,让其评审带宽可见〕

### D3 风险敞口(本 change 行为风险量级最高的一块)

- **[Critical-adjacent] 聚合回归只覆盖非默认轨,而 verify 锚点是无条件的**〔评审 C2〕:canonical 缺省是 `writing-plans → subagent-dev`,收尾票只由 tickets 轨产出。若 `sdflow-done` 无条件要求该锚,**默认轨的仓既没有聚合回归、又会被这条锚判出假 gap**。
  **→ Mitigation(必须实现,非可选)**:该 verify 锚 **MUST 按管线条件化**——仅当本 change 走 tickets 轨时才要求;superpowers 轨下该需求判"不适用",MUST NOT 判 gap。
  **→ dogfood 盲区自曝**:本仓 `openspec/config.yaml` 是 `impl-pipeline: tickets`,源仓自测**照不到**这个洞。tasks 里为此单列一条 superpowers 轨的验证。
- **[Risk] "最后一票"无拓扑/gate 机械保证**〔评审 H12〕:`frontier` 只服从显式 `Blocked-by`、不理解"验证票必须最后";`ship_gate` 不检查其唯一性/位置/全依赖 ⇒ 验证票可能提前执行或缺失而无人发现。
  **→ Mitigation**:`ship_gate` 加**第四道 plan 校验**(tickets 轨:MUST 恰含一张收尾票,且其 `Blocked-by` ⊇ 全部功能票号)。这不是加宽——D3 的核心承诺是"链路里必有聚合回归执行点",无机械守则承诺不成立。
- **[Risk] "不计入 3–6 预算"正在掏空票数约束**:已有 expand–contract 迁移批次 + 收尾票**两个后门**。**→ 本次接受**(记 todo:改为约束总执行单元或总 frontier 成本)。
- **[Risk] 跨票 e2e/集成回归的发现时间推迟到末尾聚合票**。**→ Mitigation**:Q3 保留的中间档(`Blocked-by` 链上模块集成测试可跑)把一部分跨票问题拉回当票;排查范围有界(仅本 change 3-6 张票的 commit 集合);收尾票复用完整 fix 循环。
- **[Risk] 验证票修复工作量 ex-ante 不可控**〔评审 L2〕。**→ Mitigation**:显式接上既有逃生阀——plan 结构不可变、只能**追加新号**(F1),修复量超单票容量时按该机制追加。

### 其余

- **[Risk]** Standards/Spec reviewer 自判 severity,mid 档可能误判。**→** 下游 `sdflow-code-review` 冷层完全独立重审,不依赖 implement 阶段的 severity 标签。
- **[Risk] Codex 宿主下 `sdflow-implement` 不 fan-out 就跑不了任何 ticket**〔评审 H10/H11〕——与 `sdflow-code-review`"不 fan-out 只缩 roster"的降级路径**不同构**。**→ 处置**:`host=unknown`、或 Codex 宿主下能力探针判子代理不可用 ⇒ **fail-loud 硬停**并提示在受支持宿主下运行,MUST NOT 用空档位或默认值继续派发。
- **[Risk] 改名的在途窗口**:已落盘 `superpowers-plan.md` 的在途 tickets 轨 change,升级后 gate 仍能按 resolver 找到旧名文件继续跑(向后兼容),但**两个文件同时存在 ⇒ fail-closed UNKNOWN**。**→** Migration Plan 写明处置。

## Migration Plan

〔spec-review-amendment H5:首版写"跑 `sdflow-init update` 后生效"——**渠道错误**〕

- **分发渠道按资产类型分列**:
  - **skill 本体**(`sdflow-implement`/`sdflow-done`/`sdflow-ship`/`sdflow-code-review` 的 `SKILL.md`)与**脚本**(`ship_gate.py`/`impl_route.py`)走 **`setup.sh`**:运行 checkout `git pull` → **立即** `bash setup.sh`。Unix 为绝对路径 symlink(改源即时生效),Windows 为 copy。
  - **workflow bundle 规则**(`assets/workflow/*`)走 `sdflow-init update` 推下游。
  - 🔴 **skew 窗口**:第零步 fail-hard 依赖 `resolve-models.sh`(装在 `~/.sdflow/hack/`,由 `setup.sh` 拷贝,**`sdflow-init update` 不装**)。只跑 `update` 不跑 `setup.sh` ⇒ "新指令 + 缺 helper" ⇒ 第零步硬停。发布边界 = push(开发)→ pull(运行)→ **立即** setup。
- **已在途 plan 的兼容性**〔spec-review-amendment M17:首版把强制票降成"若需要,手动补一张",与"强制"自相矛盾,且无人负责识别〕:
  - **谁负责识别**:`ship_gate` 第四道校验只对**本次改动生效后新出的** plan 生效——判据 = plan 文件名。`tickets.md` ⇒ 必须含收尾票;`superpowers-plan.md`(旧名,tickets 轨在途) ⇒ **grandfather,不校验收尾票**,gate 输出一行提示"在途 plan 未含收尾票(grandfathered)"。
  - **何时必须补**:不必须。在途 plan 按既有"追加新号"机制(F1)**可选**补一张;不补则该 change 的聚合覆盖需求由 verify 判"不适用(在途 grandfather)",MUST NOT 判 gap。
  - **两名并存**:`tickets.md` 与 `superpowers-plan.md` 同时存在 ⇒ gate fail-closed UNKNOWN(不猜),提示人工删掉其一。
- **回滚**:revert 本次 commit 集合 + 运行 checkout 重跑 `setup.sh`。delta spec 归档回滚由 `openspec archive` 既有机制处理。**改名的回滚**:revert 后 gate resolver 一并回退,已按新名落盘的在途 plan 需手工改回旧名(记在 `adr/0033` 的 Consequences)。

## Open Questions

无。阶段二设计评审的 Q1–Q6 已由人在设计 HARD-GATE 拍板,结论已落入上文与 `decision-memo.md`。

## Compliance

N/A——纯指令文本、delta spec 与确定性脚本/测试,不涉及数据合规、隐私或安全边界变化。
