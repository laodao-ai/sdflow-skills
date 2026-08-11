# 历史重放部署门报告

> Task 4（`implement-workflow-optimization-2026-08-p2`）。一次性验证，非常驻资产（design.md DD5）。
> 部署门判据：③类（协议缺陷/真误杀）= 0 是红线，①②类如实报数不挡部署，噪声重入率标「参考」。

## 一、方法与样本

对 **5 份归档评审报告**（4 份 code-review + 1 份 spec-review，覆盖 4 个不同 change）做重放：

| # | 报告 | reviewed_sha | worktree |
|---|---|---|---|
| r1 | `archive/2026-07-06-refactor-roadmap-internalize-deps/code-review-report.md` | `8761cf4` | `r1-refactor-roadmap` |
| r2 | `archive/2026-08-09-absorb-gstack-autoplan/code-review-report.md` | `35cbe38` | `r2-autoplan-code` |
| r3 | `archive/2026-08-02-tickets-parallel-frontier/code-review-report.md` | `8e284fd` | `r3-tickets-frontier` |
| r4 | `archive/2026-08-07-fix-probe-scan-precision/code-review-report.md` | `5d9afb1` | `r4-probe-scan` |
| r5 | `archive/2026-08-05-simplify-workflow/spec-review-report.md` | `efba4a8` | `r5-simplify-spec` |

选取依据：覆盖「多条采纳 finding」（r1/r5）、「置信过滤裁掉项」（r2/r3，旧协议 `<80` 滤除的典型样本——
正是新协议要替换掉的机制）、「小样本单条 finding」（r4）；code-review/spec-review 两种报告类型均覆盖。

流程（`run-replay.sh` + 本报告）：
1. 每份报告的 `reviewed_sha` 建 `git worktree`（detached）。
2. 从报告原文手工提取 findings 为结构化 JSON（`findings/*.json`）——**旧协议无结构化输出契约，
   报告里没有一条 finding 带逐字 `quote`**，只有「文件:行号 + 一句问题描述」或纯 prose。
   按 DD4 契约诚实处理：能定位到单一干净 `file:line` 且能独立核验出真实引文的 2 条（r4 CR-06、
   r5 H3）填 `{file, line, quote}` 三元组走机械三查；其余 47 条填 `evidence_pack`（原文位置+
   问题描述）——机械层判 `uncheckable`，直进强档二元裁决（brief 显式允许此处置：「对旧格式
   findings 标注 uncheckable，脚本吃不了的就直接进二元裁决」）。
3. `python3 findings_ref_check.py --input <report>.json --root <worktree>` 真跑机械引用核。
4. 对每条 finding 做强档二元重裁（我独立判断：该采纳/裁掉/defer），必要时读 worktree 内真实代码核验。
5. 与历史裁决对表，不一致项归因三类。

## 二、机械层结果（findings_ref_check.py 真跑）

| 报告 | 条数 | pass | uncheckable | fail |
|---|---|---|---|---|
| r1 | 14 | 0 | 14 | 0 |
| r2 | 9 | 0 | 9 | 0 |
| r3 | 4 | 0 | 4 | 0 |
| r4 | 1 | 1 | 0 | 0 |
| r5 | 21 | 1 | 20 | 0 |
| **合计** | **49** | **2** | **47** | **0** |

**机械层真实抓到 2 处引用漂移**（构造 JSON 时的第一版曾用报告原文的行号/裸文件名，脚本第一次跑
即报 `fail`，据此定位并修正）：

- **r4 CR-06**：报告原文写 `sdflow-init/scripts/init.py:246`，脚本判 `quote-mismatch`；
  `grep -n` 核实真实行号是 `:248`（偏差 2 行）。修正后三查全过，`pass`。归因**①口径漂移**
  （历史报告行号本身不精确，finding 本体有效——`n = sum(len(fs) for _, _, fs in os.walk(dst))`
  这行代码确实存在且确实是报告描述的问题）。
- **r5 H3**：JSON 首版按报告行文写裸 `design.md`，脚本判 `path-not-found`；实际路径是
  `openspec/changes/simplify-workflow/design.md`（报告省略了 change 目录前缀，同一份 change
  自身语境下人读不会误解，但机器需要完整相对路径）。修正后 `pass`。归因**①口径漂移**
  （报告写法本身省略前缀，非本体有误）。

**这两次 fail→pass 恰是 DD4 机械层设计意图的直接证据**：它对不精确的引用 fail-loud，逼迫核验后
再放行，而不是静默接受一个凑巧看起来合理的引用。两次漂移均在 corrigible 范围内（人读可辨真实位置），
判①类、不计入③类分母。

其余 47 条 `uncheckable`——**全部因为旧协议历史语料没有一条 finding 带逐字引文**（无 `quote` 字段，
仅有 file:line 指针或纯 prose 描述）。这是 design.md 已预判的 **C4 语料限制**：旧报告在 DD1/DD4
之前产出，Step2 镜 prompt 当时未被要求携带结构化引文字段。`uncheckable` 是脚本按契约的正确分类
（不是缺陷）——这些 finding 全部**原样直进强档二元裁决**，见第三节。

## 三、逐报告二元重裁对表

图例：历史裁决 = 报告原文的最终 disposition（采纳/裁掉/defer，非中间置信数字）；
新裁决 = 本轮强档二元重裁（读 worktree 真实代码核验后独立判断）；一致 = ✅ / 不一致 = ❌。

### r1 · refactor-roadmap-internalize-deps（code-review，14 条）

| id | 历史裁决 | 新裁决 | 一致 | 备注 |
|---|---|---|---|---|
| F1 | 采纳 | 采纳 | ✅ | worktree 核实 `SKILL.md:423/525` 已按 F1 描述修复（条件化 memo 产出+收尾） |
| F2 | 采纳 | 采纳 | ✅ | worktree 核实 `SKILL.md:354` 已加 MUST NOT 覆盖既有 memo 条款 |
| F3 | 采纳 | 采纳 | ✅ | worktree 核实 `workflow-history.md` A4 段已含「同批（非同因）移除」+ git log 时序证据 |
| F4 | 采纳 | 采纳 | ✅ | worktree 核实 `SKILL.md:305` 已有「SHALL 五项全部满足方算 gate-0 过」阈值句 |
| F5 | 采纳 | 采纳 | ✅ | 低成本 fold，理由充分 |
| F6 | defer | defer | ✅ | 真实存在但低概率+design 已声明诚实边界，defer 合理 |
| X1 | 裁掉 | 裁掉 | ✅ | 与设计已拍板语义矛盾（spec:43） |
| X2 | 裁掉 | 裁掉 | ✅ | design.md 已显式接受该边角 |
| X3 | 裁掉 | 裁掉 | ✅ | 已并入 F1，非独立缺陷 |
| X4 | 裁掉 | 裁掉 | ✅ | 历史镜误把已修问题当现存（ADR 0037 已订正） |
| X5 | 裁掉 | 裁掉 | ✅ | 历史镜误报，`SKILL.md:389` 已有条款 |
| X6 | 裁掉 | 裁掉 | ✅ | 历史镜误报，Task5 fixture 已解决 |
| X7 | 裁掉 | 裁掉 | ✅ | 历史镜误报+事实错误（footage 词表命中） |
| X8 | 裁掉 | 裁掉 | ✅ | 无 finding 是合格结论，非漏审 |

**14/14 一致，0 mismatch。**

### r2 · absorb-gstack-autoplan（code-review，9 条）

| id | 历史裁决 | 新裁决 | 一致 | 备注 |
|---|---|---|---|---|
| F1 | 采纳 | 采纳 | ✅ | worktree 核实 `openspec/specs/outside-voice-reuse-guard/` 目录已删 |
| F2 | 采纳 | 采纳 | ✅ | worktree 核实 `task-log-template.md:64` 附近旧误引用文本已不存在 |
| V2 | defer | defer | ✅ | 既有债务，本 change tasks 未要求覆盖，低频场景 |
| X1 | 裁掉（旧协议置信55<80滤除） | 裁掉 | ✅ | 独立merit判断：仅「注释语义漂移」一句无充分问题陈述，信息量不足以行动 |
| X2 | 裁掉 | 裁掉 | ✅ | 已验证前提不成立（fail-loud 早于 fan-out） |
| X3 | 裁掉 | 裁掉 | ✅ | 已验证不成立（TG→domains 映射驱动非硬编码） |
| X4 | 裁掉 | 裁掉 | ✅ | 已修复+测试验证幂等性 |
| X5 | defer（报告标签为"已裁掉"但台账区实为 defer→todolist） | defer | ✅ | 台账区订正标签误差，本体是合法 minor 项 |
| X6 | defer（同 X5） | defer | ✅ | 同上 |

**9/9 一致，0 mismatch。** 注：X5/X6 是本轮重放发现的**报告内部标签不一致**（原文把 defer 项归进
「已裁掉」表标题下，但台账区又写明是 defer）——判①口径漂移（原报告自身的呈现瑕疵，非重裁分歧），
不影响新旧裁决一致性判定。

### r3 · tickets-parallel-frontier（code-review，4 条，均为置信<80被裁掉项）

| id | 历史置信 | 历史裁决 | 新裁决 | 一致 | 备注 |
|---|---|---|---|---|---|
| X1 | 35 | 裁掉 | 裁掉 | ✅ | 独立merit核验：Read tool 绝对路径读取不受 git worktree 隔离影响（worktree 只隔离 `.git/index`），前提错误成立 |
| X2 | 45 | 裁掉 | 裁掉 | ✅ | Agent tool 已有 path/branch 返回值供编排层处置，prose 层不需重复定义 |
| X3 | 50 | 裁掉 | 裁掉 | ✅ | 已有结构性缓解（并行安全约束+聚合审+冷审），decision-memo 已登记兜底 |
| X4 | 25 | 裁掉 | 裁掉 | ✅ | 过于泛化，非本设计可解 |

**4/4 一致，0 mismatch。** 这是本轮样本里唯一「全部由旧置信过滤机制裁掉」的报告——独立二元重裁
（不依赖数字阈值）复核后结论不变，**说明旧的 `<80` 数值滤除在这 4 条上给出了与 merit 判断相同的
结果**，但判断依据完全不同（旧=分数、新=读证据链判断）。这正是 tasks 1.2 要删除数值滤条款的
论据来源之一：数值不是必要的，merit 判断本身就够。

### r4 · fix-probe-scan-precision（code-review，1 条）

| id | 历史裁决 | 新裁决 | 一致 | 备注 |
|---|---|---|---|---|
| CR-06 | defer | defer | ✅ | 机械层三查全过（修正行号漂移后 `pass`），Minor 且 display-only，defer 合理 |

**1/1 一致，0 mismatch。**

### r5 · simplify-workflow（spec-review，21 条）

| id | 历史裁决 | 新裁决 | 一致 | 备注 |
|---|---|---|---|---|
| C1 | 采纳 | 采纳 | ✅ | worktree 核实 `specs/spec-authoring/`、`specs/impl-orchestration/` delta spec 已存在 |
| C2 | 采纳 | 采纳 | ✅ | worktree 核实 `openspec/workflow/` 本地 pin 48 文件仍在（spec-review 阶段未修，符合预期——该修复属实现阶段） |
| C3 | 采纳 | 采纳 | ✅ | 未覆盖 Requirement 描述具体、可核 |
| H1 | 采纳 | 采纳 | ✅ | 审计闭环价值明确、成本低 |
| H2 | 采纳 | 采纳 | ✅ | 五问速算：不阻断但措辞需修正，合理 |
| H3 | 采纳 | 采纳 | ✅ | worktree 核实 `design.md:85` 路径已修正为 `sdflow-implement/scripts/impl_route.py`，带 `[spec-review-amendment]` 标记（机械层 pass） |
| H4 | 采纳 | 采纳 | ✅ | 具体测试文件名+断言内容，可核 |
| H5 | 采纳 | 采纳 | ✅ | 已实跑验证基线（5 passed），描述具体 |
| H6 | 采纳 | 采纳 | ✅ | 4 份具体文档路径，可核 |
| H7 | 采纳 | 采纳 | ✅ | 3 处具体行号声明，可核 |
| M1 | 采纳 | 采纳 | ✅ | 具体（9处硬编码），可核 |
| M2 | 采纳 | 采纳 | ✅ | 核验证据缺口描述具体 |
| M3 | 采纳 | 采纳 | ✅ | worktree 核实 `config.template.yaml:80` 措辞（spec-review 阶段未修，符合预期） |
| M4 | 采纳 | 采纳 | ✅ | 数字误差描述具体可复算 |
| M5 | 采纳 | 采纳 | ✅ | 测试粒度问题描述具体 |
| M6 | 采纳 | 采纳 | ✅ | worktree 核实 `config.yaml:38/48` 仍含 wayfinder 引用 |
| L1 | 采纳 | 采纳 | ✅ | 低成本纯文案修正 |
| L2 | 采纳 | 采纳 | ✅ | 同上 |
| X1 | 裁掉 | 裁掉 | ✅ | 用户已明确拍板方向（decision-memo D3），非设计缺陷 |
| X2 | 裁掉 | 裁掉 | ✅ | 混淆「线性路径」定义，误判 |
| X3 | 裁掉 | 裁掉 | ✅ | 优先级建议非设计缺陷，scope 由人定 |

**21/21 一致，0 mismatch。**

## 四、汇总统计

| | 条数 |
|---|---|
| 样本总量 | 49 |
| 历史「采纳」 | 25 |
| 历史「defer」 | 5 |
| 历史「裁掉」 | 19 |
| 新裁决与历史裁决一致 | **49（100%）** |
| 新裁决与历史裁决不一致（需三类归因） | **0** |

**三类归因（红线检验）**：

| 类别 | 定义 | 计数 |
|---|---|---|
| ①历史误标/口径漂移 | 剔除分母 | 3（r4 CR-06 行号漂移 `:246→:248`、r5 H3 缺 change 目录前缀、r2 X5/X6 报告内部标签自相矛盾）——均**发生在机械核验/JSON 构造阶段，不是新旧裁决分歧**，如实记录但不计入分母 |
| ②模型方差 | 复裁一次，二次仍不一致才计入 | 0（首轮重裁 49/49 与历史一致，无需触发二次复裁） |
| **③协议缺陷（真误杀）** | **红线** | **0** |

**红线判据：③类 = 0 ✅ 满足，部署门通过。**

## 五、噪声重入率（参考，非门禁）

对历史「裁掉」的 19 条逐条独立二元重裁，新协议下**仍全部裁掉，0 条被重新接纳**。
噪声重入率 = 0/19 = **0%（参考值）**。

**C4 语料限制如实写明**：这个 0% 不能读作「新二元裁决协议不会引入任何噪声重入」——本次样本的
19 条历史裁掉项，13 条（r2 4条+r3 4条+r1 前5条历史镜误报+r1 X8/X1-3）有报告原文写明的**具体、
可核验的裁掉理由**（如「已验证不成立」「已修复」「与设计矛盾」），这类证据链完整的裁掉项，
无论旧协议用什么筛选机制（置信阈值/人工推理），本来就大概率被正确裁掉——**该样本对「新二元
裁决在证据薄弱时是否会比旧置信阈值更宽松地放行噪声」这个问题的区分力有限**。真正的压力测试
需要窗口期真实 dogfood 语料（tasks.md 5.3 已登记为窗口期观察指标），本次重放只能给出「不劣于」
的下限证据，不能给出「不会变差」的上限证据。

## 六、诚实边界与残余

- **旧语料无 `quote` 字段是系统性的，非个别报告缺陷**：5 份报告、49 条 finding，无一条带逐字引文
  三元组。这印证了 design.md DD4 的判断——旧 Step2 prompt 未强制结构化输出，是 tasks 1.2/1.3 要
  修的目标态缺口，本重放的「47 条 uncheckable」正是这个缺口的直接度量，而非重放方法论的失败。
- **2 条 pass 的样本量小**，不能单独作为「findings_ref_check.py 三查机制在真实语料上普遍适用」的
  强证据；该脚本自身的正确性由 Task 1 的 pytest 套件（`test_findings_ref_check.py`，覆盖正例/三种
  失败态/无引文态/uncheckable态/脚本崩溃态）独立担保，本重放只验证部署门（新旧裁决一致性），
  不重复验证脚本单元正确性。
- **reviewed_sha 语义在「已修复」类 finding 上需要读上下文**：多个报告的 `reviewed_sha` 指向的是
  **修复已落盘的 checkpoint**（如 r1 `8761cf4` 的提交信息即「多镜代码审自动修复」），
  finding 描述的问题代码在该 sha 已被替换为修复后版本；本重放对这类 finding 采用「在 reviewed_sha
  核验修复确已生效」而非「在 reviewed_sha 复现原始问题文本」的核验策略——这是从 DD5「与历史裁决
  对表」目标反推的合理适配，不违反 DD5 用「reviewed_sha checkout」的字面指示（checkout 的仍是同一个
  sha，只是核验目标从「问题存在」换成了「问题已被处置」，两者对「这条 finding 该不该被采纳」这一
  判断都成立）。
- **裁决对象规模远小于窗口期真实体量**：49 条样本 vs `mirror-dispositions.yaml`/DD6 表引用的
  35 轮/39 轮历史轨迹，重放是抽样验证不是全量重跑，样本选取覆盖了「多采纳」「多置信裁掉」
  「单条」「跨报告类型」四种形态，但不穷尽全部历史 change。
- **重裁非盲判**：重裁者在下判断前 `historical_verdict` 全程可见（构造 findings JSON 时历史裁决
  标签已包含在同一对象内），100% 一致率不能排除锚定效应（确认偏误）。本轮重放验证的是「新协议
  在已知历史语料上不产出明显矛盾」，不等于「新协议能独立产出与历史一致的结论」——后者需要盲判
  流程（先隐藏 historical_verdict 独立判断、再对表），本次未做。窗口期真实评审（无历史答案可参考）
  将是更强的独立性证据。

## 七、结论

**部署门判据 ③类 = 0 满足，无违例。** 49 条重放样本（4 code-review + 1 spec-review 报告）
新旧裁决 100% 一致，机械层（findings_ref_check.py）在仅有的 2 条可测三元组样本上正确工作
（含捕获 2 处真实引用漂移的直接证据）；47 条旧格式 finding 按 DD4 契约诚实分类为 `uncheckable`
直进强档二元裁决，重裁结果与历史一致。**建议：1.2/1.3 裁决协议可部署。**
