# sdflow 判据结构化跟踪（机械化覆盖仪表）

> **用途**：把 workflow 各阶段用到的**每一条判据**（"判什么、据什么定"）按机械化程度分类，作为**基准①（机械化优先 + 目标态）**的量化跟踪仪表——后续逐条推进「🟡可结构化 → 🟢已结构化」，并诚实标注「🔵可语义」残余。配套：结构见 [`workflow-map.md`](workflow-map.md)、方法见 [`design-methodology.md`](design-methodology.md)。
>
> **分类三档**：
> - 🟢 **已结构化**：脚本确定性产出/消费 + 退出码/锚承载判定。拆两半——**写锚点**（producer：谁 emit 结构化数据）· **用锚点**（consumer/gate：谁读它并据以门控）。
> - 🟡 **可结构化（候选）**：**有确定性信号**、但当前靠 prose/人/模型做——机械化目标（adr/0006(b) 点名）。
> - 🔵 **可语义（残余）**：**无确定性信号**，本质需模型/人判断（诚实边界，非弱点）。
>
> **口径**：一条判据可拆多档（如 HR-TG：「命中哪些 TG」🔵 + 「∩ 子集 + 出锚」🟢）。写/用锚点带 `file:line` 者引 workflow-map；未核实处标 `~`。v1 立于 2026-07-11，待逐阶段核校精化。

---

## 0. explore（无门）
| # | 判据 | 档 | 写锚点 | 用锚点 | 备注/去向 |
|---|---|---|---|---|---|
| 0.1 | 探索什么 / 何时结晶成 change | 🔵 | — | — | 纯发散判断 |

## 1. propose / ff（FF-0 + 生成约束）
| # | 判据 | 档 | 写锚点 | 用锚点 | 备注/去向 |
|---|---|---|---|---|---|
| 1.1 | 是否在 feature 分支（FF-0） | 🟢 | `git checkout -b feat/{change}` | FF-0 分支守卫 hook（PreToolUse·Bash，受保护分支拦 `openspec new`）| ff-generation-constraints |
| 1.2 | 命中哪些 TG（trigger-catalog） | 🔵 | — | — | 声明散落、无确定性信号 → 归模型（adr/0018 Q-D）|
| 1.3 | 给定 TG 集 → 激活哪些 D 约束/领域清单/图/模版槽 | 🟡 | — | 模型读 trigger-catalog 五列表 | 表是结构化单一源，但"据 TG 查表注入"当前靠模型；可脚本化成注入器 |
| 1.4 | proposal 四件套结构合法（Requirement ID / Scenario WHEN-THEN / ADDED-MODIFIED 分组 / task↔req 追溯）| 🟢 | proposal/design/specs/tasks | `openspec validate`（CLI）| 已有结构门 |
| 1.5 | D-5 Success Metrics 节在场（非空/非模版）| 🟡 | proposal Success Metrics 节 | 当前人/模型核 | 在场性可机械 lint（阻塞语义已定），未落脚本 |
| 1.6 | D-1 代码事实先 grep 再写（准确性）| 🟡 | — | 接地镜（spec-review 期）| "是否 grep 过"难机验；但"spec 代码事实 vs 真实代码"可脚本比对（接地镜半机械）|
| 1.7 | D-3 每处"不在范围"附可证伪假设 | 🔵 | — | — | 假设质量属判断 |

## 2. 人类门① 拷问（`/sdflow-spec` 相位 B）
| # | 判据 | 档 | 写锚点 | 用锚点 | 备注/去向 |
|---|---|---|---|---|---|
| 2.1 | 是否达成共识 / 分支死磕到底 | 🔵 | — | — | 对话岛，纯判断 |
| 2.2 | ADR 值不值得立（难逆/意外/真权衡三判据）| 🔵 | — | — | 判断 |

## 3. 人类门② 设计 HARD-GATE
| # | 判据 | 档 | 写锚点 | 用锚点 | 备注/去向 |
|---|---|---|---|---|---|
| 3.1 | 设计是否可过门（批准动作）| 🔵 | — | — | 人类唯一拍板 |
| 3.2 | 过门态机判（pre-flight）| 🟢 | `spec-review-report.md` frontmatter `ship-gate.design_approved: true`（spec-review 拍板回写）| `ship_gate.py`（absent→REFUSE_START(3)；`:20,289`）| **canonical 写/用锚点对** |

## 4. spec-review（设计审）
| # | 判据 | 档 | 写锚点 | 用锚点 | 备注/去向 |
|---|---|---|---|---|---|
| 4.1 | 4 类 v1 锚存在 + lens-metric 字段/enum/sev/layer 合法 | 🟢 | 各镜 emit + `lens_metric_emit.py` | `anchor_lint.py --layer spec-review`（`:163`；1 违规/2 fail-closed）| 已结构化门 |
| 4.2 | 命中哪些 TG | 🔵 | — | — | 同 1.2 |
| 4.3 | 命中集 ∩ HR-TG 子集 + 出锚 | 🟢(深)| `hr_tg_intersect.py` → hr-tg 锚 `hit=/declared=/evidence=`（3字段 canonical）| ✅ `anchor_lint.check_hr_tg`（`:317`）: M2 重算 hit⟺declared∩HR-TG · M4 evidence在场 · M-new TG存在 · `_check_order_and_dup`（`:306`）numeric同序/拒重复 · `parse_kv_strict`（`:92`）整行拒重复键/未闭合/残留 · `load_hr_tg_subset`（`:221`）/`load_all_tg_set`（`:253`）F7子集/F8边界/fence-aware/段定位恰1 · 必需`--trigger-catalog`（`:438`）fail-closed · 跨文件 golden `test_hr_tg_cross_tool.py` | ✅ **ship `harden-hr-tg-anchor-consistency`（2026-07-11 merged 504ab4d）**：浅🟢→深🟢，仅 declared 正确性(4.4)留 🔵 |
| 4.4 | declared 是否=真命中集 | 🔵 | — | — | S1 残余（无信号，adr/0018）；✅ ship `harden-hr-tg-anchor-consistency` 后残余**已收窄**为纯此项（M2 机械化了"内部一致性"那半），档不变（诚实边界、非缺口）|
| 4.5 | outside-voice 复用前置（来源 mode/新鲜度/结构）| 🟢 | `outside_voice_guard.py` → reason_code | 编排据 reason_code 复用/回落 | mlh-p4 T80 |
| 4.5b | outside-voice **per-site 完整性**（该层应有锚的站点是否都落了锚）| 🟢 | 报告落 `declared-sites` 锚（`{design-voice\|code-voice} ∪ {hr-tg \| HR-TG∩≠∅}`）| ✅ `anchor_lint.check_declared_sites`：双向核「declared == 公式重算期望集」+「declared == 实落 `site=` 集」，补家族级门（≥1 条即过）的 per-site 盲区 ⇒ 并发 2 站点漏收一个不再判 CLEAN；复用 `fence_outside_lines` 口径（无裸 grep 二源、自指不假阳）| ✅ **ship `async-outside-voice`**：站点集按「**应有锚**」而非「应 dispatch」定义（复用态 design-voice 未派仍落锚、code-voice always，按 dispatch 定义必假红）；**强度边界**：反规避只在 hr-tg `declared=` 可信时成立（依赖 4.4 的 S1 残余）|
| 4.6 | 镜价值度量（findings/采纳/独立/sev）| 🟢 | `lens_metric_emit.py` → lens-metric 锚 | `/sdflow-retro` 聚合（`lens_metric_aggregate.py`）| 写此、用在 retro |
| 4.7 | finding 对抗裁决（采纳/裁掉/defer、是否真爆）| 🔵 | — | — | 主 session 强档判断 |
| 4.8 | finding 置信度（高/中/低）| 🔵 | — | — | 主观分级（可辅助不可机定）|
| 4.9 | 数值一致性（锚 findings=N vs 合并池实收）| 🟡 | — | — | 有信号（可交叉核数），当前主 session 信任边界、未机械守 |

## 5. ship·路由 + 判官（ship_gate 全程）
| # | 判据 | 档 | 写锚点 | 用锚点 | 备注/去向 |
|---|---|---|---|---|---|
| 5.1 | 下一步是谁（11 verdict 推导）| 🟢 | 盘面（四件套/三报告 frontmatter/checkpoint）| `ship_gate.py`（`:32-44`,`:647`；exit 0/3/4/5/6）| 阶段三判官核心 |
| 5.2 | 管线路由（config→marker→缺省）| 🟢 | `PIPELINE_RECEIPT`（route emit）+ plan frontmatter marker | `impl_route.py route`（回显+机判）| tickets/superpowers |
| 5.3 | 坏 frontmatter 分类（越域/重复键/bad-type/tab/absent）| 🟢 | — | `ship_gate.py:295-345`（live→UNKNOWN(6)/归档→fail-safe none）| — |
| 5.4 | 熔断无进展（STEP_IN_PROGRESS / RERUN_STALE）| 🟢 | 报告 frontmatter 状态集快照 | `ship_gate.py` `anchor_set`/`breaker_no_progress`（单 invocation 持有）| mlh-p5 |

## 5b. ship·plan（tickets/superpowers）
| # | 判据 | 档 | 写锚点 | 用锚点 | 备注/去向 |
|---|---|---|---|---|---|
| 5b.1 | plan 是否缺 → RUN_PLAN | 🟢 | `tickets.md`（tickets 轨）/ `superpowers-plan.md`（superpowers 轨，D5/adr-0033）| `ship_gate`（共享 resolver 按序探测两名，双存在 fail-closed；plan 缺）| — |
| 5b.2 | checkpoint 完成标签契约 | 🟢 | `checkpoint({change}:task<N>-…)` commit | `ship_gate.py:492` `TAG_RE` | slug 须含横杠（memory）|
| 5b.3 | ticket 切片粒度 / Blocked-by 拓扑划分 | 🔵 | `Blocked-by:` 声明（写） | — | 划成几片=判断；拓扑解析=🟢下条 |
| 5b.4 | next-ready ticket（Blocked-by 拓扑 + done 集）| 🟢 | `Blocked-by:` | `impl_route.py frontier` | tickets 管线 |

## 5c. ship·实现
| # | 判据 | 档 | 写锚点 | 用锚点 | 备注/去向 |
|---|---|---|---|---|---|
| 5c.1 | 完成集（哪些 task 已完成）| 🟢 | checkpoint 标签 ∪ tasks.md 复选框 | `ship_gate` 集合归属（done⊇plan）| 双通道 |
| 5c.2 | implementer 状态（DONE/DONE_WITH_CONCERNS/NEEDS_CONTEXT/BLOCKED）| 🟡 | 状态词（结构化四值）| 编排据词分诊 | 词是结构化，词背后的判断🔵 |
| 5c.3 | 双轴审是否通过（Standards+Spec）| 🔵 | — | — | 判断（domain 清单命中🟢辅助）|
| 5c.4 | 双信号核对（复选框勾但查无标签→半态）| 🟢 | checkpoint 标签 | `git log grep` 逐 task 核 | sdflow-implement 契约 |

## 5d. ship·代码审
| # | 判据 | 档 | 写锚点 | 用锚点 | 备注/去向 |
|---|---|---|---|---|---|
| 5d.1 | 无逻辑面豁免（免多镜 fan-out）| 🟢 | — | `trivial_shape.py`（`:183`；0 EXEMPT/1 必跑/2 ERR）| — |
| 5d.2 | 4 类锚 + lens-metric 合法 | 🟢 | 各镜 + emit | `anchor_lint --layer code-review`（`:163`）| 已结构化门 |
| 5d.3 | HR-TG（同 4.3）| 🟢(深) | hr_tg_intersect | ✅ `anchor_lint.check_hr_tg`（`:317`，同 4.3 共用 M1/M2/M4/M-new/M-parse）| ✅ **ship `harden-hr-tg-anchor-consistency`**：浅🟢→深🟢 |
| 5d.4 | 置信过滤 <80 | 🟡 | — | 弱档子代理逐条打分 | 分数主观(🔵)，<80 切点机械(🟡)|
| 5d.5 | 对抗裁决 / T10 三级自动选 | 🔵 | — | — | 判断 |
| 5d.6 | 代码审结论机判 | 🟢 | `code-review-report.md` frontmatter `code_review: pass\|blocked` | `ship_gate`（blocked→BLOCKED_UPSTREAM(4)）| 写/用锚点对 |

## 5e. ship·收尾（done）
| # | 判据 | 档 | 写锚点 | 用锚点 | 备注/去向 |
|---|---|---|---|---|---|
| 5e.1 | verify PASS/FAIL（每 ✅ 须机验锚点）| 🔵 | `verify-report.md` frontmatter `verify: PASS\|FAIL`（写=🟢）| `ship_gate`（FAIL→VERIFY_FAIL(5)）| **判定🔵、承载🟢**：结论是模型判断，"每✅附锚点"是防假✅机制、非机械判 |
| 5e.2 | 复选框对账（tasks.md 勾选诚实）| 🔵 | tasks.md 复选框 | — | 对照验收标准=判断 |
| 5e.3 | issues sweep（本 change 未分诊 OPEN 项圈入批次）| 🟢 | buglist/todolist 项 | `issues.py sweep --change`（`:1156`）| 机械封装 |
| 5e.4 | merge 前 untracked 硬检查 | 🟢 | — | `git status --porcelain`（任何 `??`→halt）| SR-2 机械化 |
| 5e.5 | archive delta ↔ 真实代码核验 | 🔵 | — | — | 按代码改写需求=判断 |
| 5e.6 | roadmap 回填：定位 phase / 勾哪几行 | 🟢+🔵 | change 名前缀（定位=🟢）| `roadmap_writeback_draft.py` | 勾哪几行/算不算完成=🔵（memory 切分线）|

## 6. archive + merge
| # | 判据 | 档 | 写锚点 | 用锚点 | 备注/去向 |
|---|---|---|---|---|---|
| 6.1 | SHIPPED（active 缺席 + base 可达 + verify=PASS）| 🟢 | 归档路径 + verify 锚 | `ship_gate`（→SHIPPED(0)/UNKNOWN(6)）| — |
| 6.2 | ff-only 可行 | 🟢 | — | `git merge --ff-only`（分叉→停）| — |
| 6.3 | delta 同步进主 specs | 🟡 | — | `openspec archive` CLI（happy）/ 手动 fallback（中文遗留）| CLI 机械，遗留 spec 手动同步=半判断 |

## 7. retro / maintain（不受 ship_gate 管）
| # | 判据 | 档 | 写锚点 | 用锚点 | 备注/去向 |
|---|---|---|---|---|---|
| 7.1 | 阶段墙钟 × 镜价值聚合 | 🟢 | checkpoint 时间戳 + lens-metric 锚 | `retro_report.py` / `lens_metric_aggregate.py`（只呈现）| 只读 |
| 7.2 | 砍镜复评触发（轮数≥10 ∧ 独立率<20% ∧ 采纳率<50% 连 2 窗）| 🟢 | lens-metric 锚 | 聚合器机械显著提示 | 触发🟢、保留/淘汰决策🔵 |
| 7.3 | 是否保留/降采样/淘汰某镜 | 🔵 | — | — | 人决（评审架构取舍）|
| 7.4 | INDEX vs 文件系统 set-diff | 🟢 | — | `maintain_scan.py`（只读报告）| — |
| 7.5 | 孤儿项归哪组 / 是否修 | 🔵 | — | AskUserQuestion | 分诊判断 |

---

## 覆盖小结（v1 粗计，待精校）

| 档 | 计数（约）| 典型 |
|---|---|---|
| 🟢 已结构化 | ~20 | ship_gate 全链 · anchor_lint · frontmatter 三门 · hr_tg_intersect/outside_voice_guard · trivial_shape · frontier · issues sweep · untracked 检查 |
| 🟡 可结构化（候选）| ~7 | 1.3 TG→约束注入器 · 1.5 Success Metrics 在场 lint · 1.6/4.9 数值/接地半机械 · 5d.4 置信切点 · 6.3 遗留 spec 同步 |
| 🔵 可语义（残余）| ~17 | 命中哪些 TG(1.2/4.2) · declared 正确性(4.4 S1) · verify 结论(5e.1) · 各对抗裁决/置信 · ADR 值不值 · 砍镜取舍 |

**跟踪法**：后续每推进一条 🟡→🟢，本表更新该行档位 + 补写/用锚点 `file:line`；🔵 项保持诚实标注、不强行机械化（避免假绿）。目标态 = 所有**有确定性信号**的判据（🟡）逐步清零进 🟢，🔵 稳定收敛为真残余。**上表计数为当前 shipped 态**——不含下方 ⏳pending 项（未 ship 不提前记账，守本表自身诚实纪律）。

### ✅ 已落实（shipped）

| change | 影响行 | 落地效果 |
|---|---|---|
| `harden-hr-tg-anchor-consistency`（2026-07-11 merged `504ab4d`）| **4.3 / 5d.3** hr-tg 用锚点 浅🟢→深🟢 · **4.4** S1 残余收窄为纯"declared 正确性" | anchor_lint.check_hr_tg（`:317`）从"仅字段在场"升 M2 重算 hit⟺declared∩HR-TG + M-new TG存在 + M4 evidence在场 + M-parse 整行严格拒重复键/未闭合/残留 + numeric同序/去重 + catalog内部一致(F7)/边界(F8)/fence-aware + 段定位恰1 fail-closed + 跨文件 golden；冷层 code-review fold 修 7 条 parsing 面洞（成员严格/段歧义/fence/锚边界/序/独立错误收集/doc） |

> **自指教训**：本表 v1 曾把此 change 的加深当既成事实写进 4.3——违反"未 ship 别提前记🟢"纪律（假绿）。经历 pending→ship 后翻实的完整周期（2026-07-11 merged）。这正是 tracker 的价值：连它自己都得守机械化诚实——先记 pending、ship 后凭 merged commit + file:line 翻实。

*v1 接地自 workflow-map.md + 各 SKILL.md + 脚本；写/用锚点 file:line 引 workflow-map（其 §4 脚本清单本身待刷新，见 T142）。逐阶段核校后升 v2。*
