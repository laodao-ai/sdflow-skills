# workflow 机械层固化 任务日志

> 本文件按时间**倒序**记录 `roadmap.md` 中每个已完成子任务的状态、耗时、问题、调整。
>
> 相关文档（全部位于 `openspec/roadmaps/mechanical-layer-hardening/`）：
> - 需求综述：`requirements.md` · 整体设计：`design.md` · 实施路线图：`roadmap.md`

## 使用约定

每完成一个 roadmap.md 中的子任务（或子任务组），追加一条记录：

```markdown
## YYYY-MM-DD
### [阶段 X / 任务 X.Y.Z] <任务标题>
- **状态**: ✅ 完成 / ⚠️ 部分完成 / 🔄 已回滚 / ⏸ 暂停
- **实际耗时**: <N>h（估时 <M>h）
- **遇到的问题**: …
- **下一步**: …
- **备注**: …
```

**要记**：子任务状态变更、与设计预期不一致、需调整 roadmap/design/specs、跨阶段教训。
**不用记**：纯配置微调、机械执行、打字错误。
**粒度**：单次 1-3 条；日期倒序；大阶段完成补「阶段 N 完成总结」。

---

## Review 处置

> 阶段 3.5 交叉 review（`/autoplan` 或 plan-*-review）产出的每条 issue 在此登记，必须标注下列状态之一：
> - ✅ **采纳**：写明已在哪个文件哪一节改动
> - ❌ **拒绝**：写明拒绝理由（不得空白「不采纳」）
> - ⏭ **延后**：写明延后到哪个阶段 / 哪个后续变更
>
> **归档前人工复核项**：确认本小节**不存在「未处置」状态**的条目。

<!-- review issue 登记从这里开始 -->
**阶段 3.5 交叉 review：跑了独立冷镜（2026-07-07，用户选「跑独立冷镜冷审」）**

`/autoplan` 在本会话 Skill 面板未直接暴露 → 用 fresh-context 冷镜 agent（plan-eng-review 视角）把三件套作整体 plan 冷审。冷镜总判「可归档，须先订正 F1/F2 表述硬伤，不动两腿骨架」。7 条 finding 处置如下：

| # | 严重度 | 冷镜发现 | 处置 |
|---|---|---|---|
| F1 | 高 | anchor_lint 复用清单技术错配（度量锚变长 KV 走 `parse_anchor` 前缀匹配，非 `_line_scoped_hits` 定长整行）；且「P2 为 P5 补锚层机验」是假依赖（两套锚互不相干） | ✅ **采纳**：design §2 技术栈拆两行 + 决策 2 理由 + 候选表 P2；roadmap 2.A.1 + 阶段 5 前置注 + 附录 A 箭头 |
| F2 | 高 | dual-read 关闭条件未定义；归档 inline 锚不可变、`archived_verify_state` **永久**靠 `_line_scoped_hits` 读 →「删整套解析机器」高估，只能删 live 半场 | ✅ **采纳**：design 决策 6 加③非对称性 + §6.4 + §6.1 风险行；roadmap 目标行 + 5.B.1 + 5.C + 验收 + 附录 B |
| F3 | 中 | 8/11 helper 只在 buglist+todolist（issues.py 依 D4 不含表解析 helper）→ 3.A.1 拓扑写错 | ✅ **采纳**：design 决策 7 + 候选表 P3；roadmap 3.A.1 拆 3 向/2 向 |
| F4 | 中 | S1 ROI 门 go 阈值未定义，与「B4/B5 已两连发」有内部张力 | ✅ **采纳**：design §9 + roadmap 阶段 5 前置，锐化为显式阈值（B4/B5 已达线，GO 待 P2 完成或再出 1 例） |
| F5 | 低 | requirements 头部列 memo.md，违反「四件套不引用 memo」 | ✅ **采纳**：requirements 头部移除 memo 条目 |
| F6 | 低 | 「57 篇」精确数未核实（实测 review-report ~39） | ✅ **采纳**：软化为约数，并入 S1 起手核实前置（design §9 + roadmap 阶段 5 前置/5.B.1/验收） |
| F7 | 低 | P8 两子项（SOP 常量收割 / roadmap 处置对账）YAGNI 风险，但护栏（按痛点+留痕）到位 | ⏭ **延后**：阶段 4 起手时掂量收益<维护成本；护栏已在 roadmap 4.D/验收，无需现在改文档 |

- **未见问题维度**（冷镜背书）：scope 未越界、度量锚只补 lint 取舍站得住、反模式/D4 处理正确、并行 caveat 恰当、子任务粒度合理。
- **归档前复核**：本小节无「未处置」状态条目（F1-F6 采纳并已改文件、F7 显式延后）。

---

<!-- 日志条目从这里开始，最新的放最上面 -->

## 2026-07-17

### [阶段 6 / P6] recorder machine index → versioned frontmatter 交付
- **状态**: ✅ 完成（change `mlh-p6-recorder-frontmatter`）
- **交付物**: Shared Frontmatter Envelope、canonical/overlay dual-reader、marker-framed prose、bug+todo 两池 semantic ID 唯一、exclusive snapshot/document lock、registry-first batch rename provenance 与 fail-closed retry。
- **迁移证据**: 仓内全量历史 corpus 按运行时枚举逐 item 对账关键字段，不固化动态总数；T85/T66/T67/T146 由真实 `todolist.py set-status` 提升为 overlay 并置 DONE，旧总览表 bytes 保持不变，`reindex --strict` 收敛。T2 保持 DONE，并追加 `mlh-p6-recorder-frontmatter（根治兑现）` 证据。
- **边界**: 本地 POSIX 自动验证；Windows 本地盘由可运行 smoke contract 覆盖，network FS、完整 power-loss durability 与非 cooperative writer TOCTOU 不承诺；process-crash lock 走人工 break-glass。
- **后续**: 仅 4.A/4.D.3 等 embedded producer 契约项继续等待真实 producer；不以当前缺样本缩小目标态。

## 2026-07-16

### [阶段 4 / 完成态对账] P4 ★组全部交付，P6 成为下一结构性端点
- **状态**: ✅ 完成态对账
- **实际耗时**: N/A（本条只做归档证据回写）
- **交付证据**: 4.C `lens_metric_emit` → `bd7c05f`；4.B `maintain_scan` → `569d393`；4.D.1/2/4 reason-code validators → `6326115`。对应 T78-T82 均已回写 DONE。
- **未完成边界**: 4.A `log_check`（T83）与 4.D.3 常量/TAG 收割（T84）仍等真实 embedded producer 契约，不以本仓当前缺样本否定目标态。
- **下一步**: 单开 T85/P6 recorder 索引→frontmatter change；端态 A、历史表只读 dual-read 与 fail-closed YAML 范式均已确定。

## 2026-07-08

### [阶段 4 / 任务 4.C] lens_metric_emit 确定性归约器交付（SHIPPED + ARCHIVED，merge `bd7c05f`）
- **状态**: ✅ 完成（change `implement-mechanical-layer-hardening-p4-lens-metric-emit`，archive `2026-07-08-implement-mechanical-layer-hardening-p4-lens-metric-emit`，merge main `bd7c05f`）
- **scope**: P4 ★ 组最高项 4.C——把 lens-metric 锚计数从主 session **手数**下沉为机械归约，直闭 requirements §1.2 痛点 #2「手数信任边界」。
- **交付物**:
  - `lens_metric_emit.py`（186 行纯 stdlib）：折叠 pass-through（`fold_hit`）+ 行键 `(lens,runner,site)` 归属/独立/sev-rollup（`reduce`）+ all-or-nothing fail-closed（`main`，坏第 N 条→零锚+非零退出）。
  - 契约单一源：`lens-metric-contract.md` 加 `lens-metric-fold` 机读块（折叠单一源，`load_fold` 自校验 codomain⊆lens）+ `lens-metric-input-schema` 机读块（emitter 输入权威 schema、bundle 可达）。
  - 四方单一源守卫：emitter/anchor_lint/aggregator/契约一致无漂移（`test_load_enums_equivalence`/`test_fold_codomain_subset_lens_enum`/`test_aggregator_enum_matches_contract`/`test_min_lens_rows_matches_anchor_lint`）。
  - 两审 SKILL 落锚步改调 emitter（构造 roster+findings → exit0 才落 → anchor_lint 自检；门控关不调；保留残余信任边界声明）：`sdflow-spec-review/SKILL.md:99`、`sdflow-code-review/SKILL.md:112`。
- **规范增量**: NEW capability `lens-metric-emit`（`openspec/specs/lens-metric-emit/spec.md`）+ workflow-metrics MODIFIED（C19「计数归约机械化，分类正确性为残余信任边界」）。
- **grill**: 死磕 design 揭穿 2 处代码 vs 主张（aggregator 无折叠→折叠无代码单一源；anchor_lint 强制行不可从 findings 推）→ 共识根治：折叠机读化 + emitter 输入补 roster；**adr/0012** 新建。
- **冷层价值**: spec-review 8 源多镜（6 镜 + 2 codex 声 + 广审）→ 20+ findings 收敛 roster/fold/fail-closed 三类设计缺口（5 镜共识，codex+Claude 双命中 anchor_set 第三调用方）；code-review 8 源冷审 **F1 高危**（`check_lens_metric` truthy 取值让空串绕过校验→假 CLEAN，7 SDD implementer + 注入点 B 全放过 → 订正为存在性校验）+ 自动修 11 项。dogfood 闭环坐实：本 change 的 code-review 度量锚由刚建的 emitter 自身归约产出。
- **验证**: verify=PASS（opus 冷启 Do-Not-Trust）；`test_lens_metric_emit.py` **39 passed**、tools 全套件 **100 passed**、`-W error` 0 warning；端到端 `--layer spec-review` exit 0 出 6 行合规锚。
- **defer**: T86（anchor_lint 未闭合 fence 同盲区）/ T87（`lens-metric-enums` 重复键静默覆盖）/ T88（无 CI/pre-commit，单一源守卫仅手动 pytest 生效）→ 批次 `implement-mechanical-layer-hardening-p4-lens-metric-emit`（hand-off 建议 T86+T87 合一个「fence 解析硬化」cleanup change）。
- **下一步**: P4 剩余 ★ 项（4.B maintain_scan / 4.D.1/2/4 小守卫，批次 `mlh-p4-target-state`）；4.A/4.D.3 待 embedded 契约排后；P6/端态 A（T85）压轴。

### [P6 端态拍板] recorder 索引→frontmatter 端态决策 = A（根治），否决 B（治标）
- **状态**: ✅ 决策已定（实现未起，压轴排 ★P4 后；todolist T85）
- **决策**: **端态 A（迁 frontmatter）**——用户以「根治 + 达成目标」判据选定，否决端态 B（reject-over-restructure）。
- **判据（两条用户约束驱动）**:
  - **约束①「新规则只对新 workflow 文档有效、历史文档不管」** → A 的最大成本（就地改写 90 条活记录）**归零**，降为 P5 gate-frontmatter 已 ship 的成熟范式：新写 frontmatter + 历史表 dual-read 永久冻结只读、**零数据改写**。A 从「全 roadmap 最险」降到「P5 同级」。
  - **约束②「希望根治问题、达成目标」** → B 按定义**治标**（`_reject_cell_unsafe` 在脆弱 markdown 表基底上永久架守卫拦 `｜`，且只守脚本写、人手编辑绕过、arity 仅兜列数变化）；A **治本**（YAML 原生转义使 `｜` 腐蚀类结构上不可能，非被拦住）。要根治 → B 出局。
- **诚实边界**（免日后被 A scope 绊到）:
  - A **非**「删掉一切解析」：历史表读 `parse_table_rows` 冻结保留（同 P5 归档读半场）；A 删的是**写侧**（`_reject_cell_unsafe` 腐蚀守卫 + `_render_item_table` + 双写表半场）。
  - 「删整类解析机器」是非能 100% 兑现的字面目标；**根治的真实达成 = 未来腐蚀结构上不可能，A 100% 达成**。
  - 可查询基底（ADR 0010 触发器②）从「决胜条件」降为 A 的**附赠**——根治本身已判 A，不再需要「是否建数据工具」这个问。
- **ADR 0010 复核**: 原「defer / ROI 触发才起」判据 = 快照妥协（拿「现在腐蚀被 reject 堵死」反推不做），本次目标态复核**推翻**。
- **排期**: 改 3 recorder 写路径 + consumer dual-read 读 + 重写测试套；压轴排 ★ P4 之后（4.C 等 ROI 更清晰、隔离项先做）；落地复用 P5 fail-closed YAML + dual-read 范式。
- **下一步**: ★ P4 推进（4.C 先行）；P6/A 作 roadmap 终点 change，实现前单独 explore/design。

### [现状复核 / P4·P6] 缺口盘点：主干四阶段全交付，P4/P6 未做（附目标态重评触发）
- **状态**: ℹ️ 复核快照（非阶段交付，附录 D「遇计划外情况必记」义务）
- **触发**: 由 `docs/workflow-map.md`（接地现状全景）反查 roadmap/requirements 缺口。
- **实测核对**（脚本实存 + 复选框）:
  - **主干（Tier 1，已承诺+高 ROI）全绿**：P1 `issues.py sweep`、P2 `anchor_lint.py`、P3 `test_mirror_consistency`+`init.py config-lint`+`batch lint`、P5 `ship_gate.py` frontmatter parser（+尾巴 T74/T75）——脚本均在、复选框全勾、已 merge。
  - **P4（编排步下沉）7 子项全未建**：`log_check.py`(4.A)、`maintain_scan.py`(4.B)、`lens_metric_emit.py`(4.C)、4.D.1-4.D.4 小校验器——`find` 确认三脚本不存在，复选框全 `[ ]`。
  - **P6（recorder 索引→frontmatter）未建**：north-star，复选框 `[ ]`。
- **map 忠实度**: map 如实标 `log_check.py`「尚未建」、手数/双写/镜像守卫均呈现为「当前机制」，无谎报。顺手订正 map §4 一处编号刺（survey P5 vs 阶段5 撞号）。
- **⚠️ 重要转向（用户拍板）**: 原「P4/P6 按需/ROI 触发不做」的判据是**拿现状快照（现在不痛）反推目标不该做**——**已否决**。开发阶段应锚**目标态**（requirements §1.3 愿景 + adr/0006 硬约束：凡机械 prose 协议 MUST 脚本化/结构化）重评「该做未做 / 可不做」。
- **目标态重评结论**（已回填 roadmap P4/P6 前置的订正块）:
  - **★ 该做未做**（原被快照压住，翻案）: 4.C `lens_metric_emit`（**最高**，直闭 §1.2 痛点#2「手数信任边界」；anchor_lint 自认「不谎称保证数值正确」即洞未合的自供）· 4.B `maintain_scan`（纯机械 set-diff）· 4.D.1 · 4.D.2 · 4.D.4。
  - **◐ 该做·正当排后**（判据 = **producer 契约就绪度**，非痛感）: 4.A `log_check` · 4.D.3——本仓无 embedded producer 契约可 dogfood，待真实 embedded 消费仓需求。
  - **P6 端态取舍**（决策项，归人）: 端态 A（做 P6，删整类解析机器，独占实现愿景「整类解析机器可删」）vs 端态 B（reject-over-restructure，腐蚀不可能但永久维护解析机器+镜像守卫）。**fork 判据 = 「删机器」是硬目标还是仅达成「不腐蚀」的手段**；判可不做时依据须是「B 满足终极愿景」而非「现在不痛」。ADR 0010 的 B 选择需在此判据下复核是否快照妥协。
  - **真·可不做 = 无**（除非 P6 判为「手段」）。P4 从「按需 0/7」翻为「★5 该做 + ◐2 待契约」。
- **建议批次**: todolist `mlh-p4-target-state`（T78-T85，PLANNED，`openspec/issues/batches.md`）——T78-T84 = P4 脚本化候选，T85 = P6 端态决策。
- **下一步**: 用户就 P6 端态 A/B 拍板 → ★ 组按优先级 `/opsx:new implement-mechanical-layer-hardening-p4-<子项>`（4.C 先行）。

### [阶段 5 尾巴清理] P5 defer T74/T75 清结（mlh-p5-parser-cleanup → SHIPPED + ARCHIVED，merge `007b00d`）
- **状态**: ✅ SHIPPED + ARCHIVED——阶段5 完成总结遗留的 defer T74/T75 已单开 cleanup change 清结；`/sdflow-ship` 全链 gate 驱动跑通：plan → SDD(3 任务) → code-review → done → ff-merge main（`007b00d`）。
- **scope**: 清 `mlh-p5-gate-frontmatter` 收尾遗留的两条 P5 尾巴——**T74**（正确性 + spec 修订）：`parse_ship_gate_frontmatter` 首行 `---` 无闭合由 fail-closed `unterminated` 改判 `absent`（`({}, None)`），弥合「只认首块」与「写坏 fail-closed」两 Scenario 措辞张力、堵 live 对干净无闭合报告硬崩 UNKNOWN(6)；退役 `unterminated` 死类别；加 live 三读点纯结构诊断提示 `_unclosed_frontmatter_hint`（走上层独立结构判定，不改 parse 签名/verdict/退出码，不波及 anchor_set/archived 三调用方）。**T75**（纯机械清理）：删 Task6 退役后只剩 test 引用的孤儿符号 `anchors_in`/`pick_exclusive`/`ANCHOR_DESIGN`/`ANCHOR_CR_PASS`/`ANCHOR_CR_BLOCKED` + `ALL_ANCHORS` 收缩至 verify-only（**保留** `ANCHOR_VERIFY_PASS`/`ANCHOR_VERIFY_FAIL`/`_line_scoped_hits` 归档 dual-read 现役）；`test_gate_anchor_scope.py` 外科改写不整删。三项向后兼容。
- **冷审成果**: SDD 3 任务审全绿（Task1 1 轮 fix 修模块头契约 docstring「未闭合」措辞漂移——parse 改判后不再 UNKNOWN(6)）；whole-branch 冷主审（1 领域 + 2 对抗 + 1 历史 + codex outside-voice）——对抗镜 parse-edge **bit-复现**归档杂交盲区（首行`---`无闭合 × 正文独占 inline PASS 锚）UNKNOWN(6)→SHIPPED(0) 回归。**裁决**：核实 design.md L136（grill-amendment Q2 + spec-review BR-2）该形态已被**设计门显式识别 + 判净负 + 接受**（mitigation = 无 producer 产出 + 头注册登记 + 目标态回归测试俱在），实现忠实 → 阶段三不重开设计门（adr/0004）、不 block；冷镜新增可达性论证（迁移半成品编辑 / 自指文档，呼应 gate-substring-dogfood）defer 供未来复评。自动修 F2（verify stale 分支吞未闭合诊断 + 「结论陈旧」措辞失准）/F3（grep unterminated 命中测试注释、与 plan Step8 冲突）。
- **验证**: verify=PASS（opus 冷启 Do-Not-Trust，15 子项各附机验锚点）；`pytest -W error` **157 passed / 0 warning**；delta 同步 spec-workflow（`openspec validate` valid）。
- **defer**: T76（归档盲区**非语义** lint/监控硬化后续 + 复评「给归档侧特殊 fail-safe」ROI，design L121 当前选①绝）、T77（delta spec「过渡期回退 inline」Scenario 迁移窗已闭、宜标历史）→ todolist 批次 `mechanical-layer-hardening`。
- **commit 链**: `e1b03a6`(Task1 parse absent+unterminated 退役) → `36eed0a`(Task1fix 契约 docstring) → `b56f88b`(Task2 live hint+盲区登记) → `b472642`(Task3 删死符号+外科测试) → `f001c70`(code-review 自动修 F2/F3+报告) → `007b00d`(archive+spec 同步+merge main)。
- **下一步**: **P5（含尾巴）完全清结**。余 Leg1 P4（编排 SKILL 机械步下沉，按痛点排）+ Leg2 P6（recorder 索引，north-star 不排期，ROI 触发才起）；P6 起手时一并评估 T76 归档盲区 lint（低优先、设计门中立、可独立小 change）。

## 2026-07-08

### [阶段 5 完成总结] gate 状态锚 inline→frontmatter 迁移 Task1-7 交付（SHIPPED + ARCHIVED，Leg2 S1）
- **状态**: ✅ SHIPPED + ARCHIVED（SDD Task1-7 全绿 → `/sdflow-code-review` 多镜代码审（3 对抗+领域+历史，codex hr-tg/code-voice 独家挖 2 真 bug：嵌套字段假过门 / 坏标量回退）自动修 5 组 → `/sdflow-done` verify=PASS → **change `mlh-p5-gate-frontmatter` 已 archive + merge main（`1b069a7`）**；delta 同步 spec-workflow（ship-gate 锚 inline→frontmatter）。defer T74/T75 入批次 `mlh-p5-gate-frontmatter`）
- **scope**: ship-gate 状态锚从报告正文 inline HTML 注释迁到报告 YAML frontmatter——`ship_gate.py` **live 侧改为纯 frontmatter 读**（inline 解析半场退役：`anchors_in`/`pick_exclusive`×3/peek/`anchor_set`熔断 helper 全迁）；**归档侧 dual-read 永久保留**（frontmatter 优先→无则回退 inline，旧归档不回归）。三 producer（`sdflow-spec-review` 拍板回写 / `sdflow-done` verify 模板 / `sdflow-code-review` 报告格式）头部改写 frontmatter 写入，正文保留人读结论行。属家族① Leg2（去字符串化）S1 交付。
- **冷审成果**: spec-review 并行六镜（领域+对抗×3+接地+codex）拦下 **1 致命+3 高**（D1 live 读点不止 `anchors_in`，须覆盖 `pick_exclusive`×3/peek/`anchor_set`全集合；D2 手写解析器首块锚定契约；D3 坏≠无键退出码映射；D4 live/归档共用严格 helper 防漂移）全采纳，落 spec-review-amendment 转 Task0 必办项。实现期 SDD 内跨任务冷审又抓 **1 Critical**（Task4：spec-review/done frontmatter 模板脱离列表缩进列 0 对齐导致解析器读不出，`e01e28f` 修复：模板顶格旁注 + 契约测试改为从真实 SKILL.md 抽取 fence 喂 parser，防 strip 抹列信息假绿）。
- **验证**: 全仓 `pytest` 662 passed；dogfood CLEAN（gate 读自身报告 frontmatter 不 REFUSE-on-self，`test_live_body_mention_immune` 等正文免疫测试覆盖 B4/B5 根治）。
- **F6 归档锚精确篇数订正**: design/roadmap 阶段估算「88 文件/168 锚行」经本轮 `grep -rlE '<!-- ship-gate:' openspec/changes/archive/` 实测为 **85 文件/153 锚行**（design 数字混入 3 处 prose 反引号提及，非真实 HTML 注释锚）；已回填 roadmap 阶段 5 前置区，差值不改变 Task1-7 迁移范围。
- **commit 链**: `7100e03`(Task1 解析器) → `209341b`(Task2 live dual-read) → `4f6b53d`(Task3 archived dual-read) → `a836b90`(Task4 producer 迁移) → `e01e28f`(Task4fix 冷审 Critical 修复) → `8cb50d7`(Task5 测试迁移) → `66da7ca`(Task6 退役 live inline) → 本条(Task7 roadmap/task-log 同步)。
- **下一步**: ✅ 收尾已完成（code-review + done + archive + merge `1b069a7`）。**Leg1（P1-P3）+ Leg2 S1（P5）均已交付**；余 Leg1 P4（编排 SKILL 机械步下沉，按痛点排）+ Leg2 S2（recorder 索引，阶段 6）north-star 不排期，ROI 触发才起。defer T74/T75（ship_gate parser 裸 `---` 首行误判 / live inline 死代码清理）非阻塞，批次 `mlh-p5-gate-frontmatter` 择期单开 cleanup 清。

## 2026-07-07

### [阶段 5 起手决策 / ROI 门结论] P5 gate 锚→frontmatter 立项（GO 变体 a）
- **状态**: ▶ 已拍板起手（尚未开 change；本条为立项决策留痕）
- **触发**: `/opsx:explore` 复盘「更新 roadmap 进展 + 下一步」——核对发现 P5 两大前置已双双落到利好侧。
- **ROI 门结论（显式阈值，冷审 F4）**: 取 **GO 变体 a**——「立项待 P2 完成即启」。P2（`e43460c`）已交付即满足，**不等**变体 b 的新一例同类 gate 假过/假红事故。依据：B4/B5 子串/prose-inline 混淆两连发已达立项线、B5 自认非根治；痛点实证充分，无需再攒事故。变体 b 保留为 P5 中途受阻时的回退确证依据。
- **前置核实落定**:
  - `ship_gate.py` 铺设路径 = **仅 `sdflow-ship/scripts/`、走 skill symlink，非 bundle 回灌消费仓**（survey 实测）→ 迁移**不触** `sdflow-init update` 回灌链、消费仓 tools/ 侧零改动 → 爆炸半径较 roadmap 撰写时预估**大降**。
  - 阶段 2 与 S1 gate 锚**不相干**（冷审 F1），仅顺序结果，非锚层前置。
- **起手第一步（残留核实项，不阻立项）**: 精核归档 inline 锚**精确篇数**（「57」约数、冷审实测 review-report ~39，以起手实测为准，F6）——决定 dual-read 归档读半场的语料范围。
- **scope 边界重申**: 家族① gate 锚迁 frontmatter；`_line_scoped_hits` **仅删 live 报告解析半场**，**归档读半场永久保留**（归档不可变，冷审 F2）；gate 消费侧 dual-read + 写坏 YAML fail-closed。
- **下一步**: 退出 explore → `/opsx:new implement-mechanical-layer-hardening-p5-gate-frontmatter`（proposal 引本 roadmap 阶段 5，design 复用 `design.md`，规范增量落 spec-workflow「ship-gate 锚契约 MODIFIED」）。

## 2026-07-07
### [阶段 2 完成总结] anchor-lint 产出侧校验器已交付（mlh-p2-anchor-lint → e43460c）
- **状态**: ✅ 完成（归档 `openspec/changes/archive/2026-07-07-mlh-p2-anchor-lint/`，merge main e43460c，未 push 时点后由本轮维护一并 push）
- **交付物**:
  - `sdflow-init/assets/workflow/tools/anchor_lint.py`（新，`--report --layer [--root]`，退出码 0=CLEAN/1=VIOLATION/2=ERROR，双输出 human+JSON，纯 stdlib）+ `tools/tests/test_anchor_lint.py`。
  - `lens-metric-contract.md` 加 `## 机读取值域` + ```lens-metric-enums``` 机读块（消费脚本单一源，anchor_lint 用 `__file__` 相对定位读取，绝不回落硬编码）。
  - `init.py copy_bundle` 刷 tools/ 时一并刷 sibling 契约（防本地 pin 部署错配，设计门 Q1 fold）+ `sdflow-init/tests/test_init_contract_sync.py`。
  - `lens_metric_aggregate` tests 加 aggregator↔契约 enum 一致性 + 双解析器交叉断言（grill 拍板）。
  - spec-review Step3 / code-review Step5 自检步接 `anchor_lint`；保留「数值一致性仍是主 session 信任边界」诚实声明。
- **规范增量**: spec-workflow +1 ADDED 需求（锚自检由确定性脚本判定）+ 14 Scenario。
- **冷层两度兑现价值**（生成循环内放过、独立冷镜挖出）:
  - spec-review **H1**（三收敛高危）: metrics 门控原设计会让 100% 消费仓每轮评审假阻塞（源仓 config `metrics.enabled=true` 掩盖 dogfood 测不出）→ 订正为真四态（无块→放行）。已记 memory `dogfood-blind-spot-source-config`。
  - spec-review **H3**: design 与 roadmap「复用不重实现」矛盾 → 调和为脚本内重实现（跨 skill import 在消费仓 break）。
  - code-review **F1**（高危，领域镜+对抗A 独立复现）: `check_lens_metric` truthy 取值让空串字段绕过校验→假 CLEAN，7 个绿 SDD implementer + 注入点B 全放过 → 订正为存在性校验。
- **实际耗时**: 全流程 ~2h（opsx:ff → grill 3 决 → spec-review 5 冷镜+codex → SDD 7 任务 242 passed → code-review 6 冷镜+codex 自动修 11 项 → done verify PASS → archive → merge）。
- **defer**: T68/T69 → batch `mlh-p2-anchor-lint`（hand-off 引用）。
- **下一步**: 进阶段 3（确定性守卫补全）。

### [阶段 1 完成总结] issues.py sweep 原子子命令已交付（mlh-p1-issues-sweep → ca66d60）
- **状态**: ✅ 完成（归档 `openspec/changes/archive/2026-07-07-mlh-p1-issues-sweep/`，merge main ca66d60）
- **交付物**: `issues.py sweep --change X` 原子子命令（内部 scan 两池 → 按 change 过滤 → 逐项 triage → batch add → reindex，幂等）+ 测试；`sdflow-done/SKILL.md` §2.1 手循环 4 步 prose 收成一行命令（保留「孤儿项不归本 sweep」边界声明）。
- **规范增量**: spec-workflow +1 ADDED（issues sweep 原子子命令）。
- **冷层价值**: 设计评审 5 镜抓 4 条硬伤（空 change 孤儿致命 / batch add 报错 / triage 缺位 / scan 口径歧义）全订正；code-review 冷审 auto-fix 7 项（reindex-problems 吞、原子措辞矛盾、失败路径无测）。
- **备注**: P1 交付时未即时登记本日志，本轮维护补记（真相以归档为准）。

## 2026-07-07
### [阶段 2 / mlh-p2-anchor-lint spec-review] 「复用→重实现」调和（H3/BASE-08）
- spec-review 领域镜 BASE-08 抓出 design 决策与 roadmap「复用不重实现」正面矛盾。裁决：遵 F1 实质（变长 KV 前缀匹配、不用 _line_scoped_hits），但因跨 skill import 在消费仓 break，实现为脚本内重实现同款逻辑。已改 roadmap.md 2.A.1 + design.md §2 技术栈行。

## 2026-07-07

### [阶段 3 / mlh-p3-determ-guards] 确定性守卫补全 P3 交付（SHIPPED）
- **状态**: ✅ 已交付（change `mlh-p3-determ-guards`，archive `2026-07-07-mlh-p3-determ-guards`，merge `a6a2adc`）
- **scope**: 3.A recorder 镜像 helper 一致性测试 + 3.B config/batch lint 合批（低耦合低增量，按 batch-triage 判据合批）。纯增测/校验器、零行为改动、零 SKILL.md 改动。
- **契约订正（grill Path B）**: A2「三份 byte-identical」实测证伪——9/11 helper 仅 docstring 合法分化。契约由 byte 全等改锁**剥 docstring 后 AST 等价**；2 个逻辑等价异写（split_sections/block_ranges）顺手归一到 buglist 写法（零回归）。
- **新 capability**: `determinism-guards`（4 需求，openspec/specs/determinism-guards/spec.md）——未来 P4 机械层下沉可扩展本 capability。
- **冷主审兑现 load-bearing**: SDD 4 任务审全绿；whole-branch 冷主审（领域+对抗×2+历史+codex OV）抓 5 真 bug 全自动修——F1 致命（batch lint 缺 batches.md fail-open 报全过，违设计失败模式表）/ F2 高（UnicodeDecodeError 裸 traceback 双处，历史镜实证重蹈 mlh-p2 `8f1d2bc` anchor_lint 已修的坑）/ F5 高（守卫漏 6 byte-identical helper，design「11 完整」证伪→TWO_WAY 8→14、总覆盖 17）/ F3 中（正则过匹配 P10→收紧 `^(P[0-4](?!\d)|—)`）/ 测试缺口低。裁 F4（paradigm-consistent）；defer T70-73 → 批次 `mlh-p3-determ-guards`。
- **验证**: verify=PASS（opus 冷启 Do-Not-Trust，实跑 4 目录 396 / 全仓 627，真实数据零假阳，坏输入非零，validate 5/5）。
- **Leg1 进度**: P1（ca66d60）/ P2（e43460c）/ **P3（a6a2adc）全交付**；余 P4（按需排）+ Leg2 P5-P6（north-star）。
- **下一步**: 视痛点决定是否起 P4（编排 SKILL 机械步下沉）；defer 批次 T70-73 择期单开 cleanup 清（非阻塞）。

### [进度核对] 实施侧全阶段未开工确认（防误判固化）
- **状态**: ℹ️ 进度快照 · ⚠️ **已被上方阶段 1/2 完成总结取代**（本条为规划刚落时的历史快照，P1/P2 现已交付；保留供追溯，勿据此判「未开工」）
- **当前进度**: 除阶段 0（规划，见下条）外，**Leg1 的 P1-P4、Leg2 的 P5-P6 全部未开工**——无任何 `implement-mechanical-layer-hardening-p*` change 存在。〔订正：P1（ca66d60）、P2（e43460c）已交付；余 P3-P4、P5-P6 待做〕
- **plan change 状态**: 承载本 roadmap 的 `plan-mechanical-layer-hardening` **仍活跃、未归档**（分支 `feat/plan-mechanical-layer-hardening`）；阶段 3.5 交叉 review + 归档尚未走。
- **易混点固化（勿误记为阶段交付）**: `issues-pool-hardening`（2026-07-07 已归档）**不是** P3 或 P6 的交付——roadmap P6 前置已把它定位成「通往 S2 的**低成本前置桥**（reject 把腐蚀类堵死）」；它早于本 roadmap 撰写，P3/P6 的 scope 已是「扣掉 issues-pool-hardening 之后剩下的」。故 recorder 一致性测试（P3.A）、config/batch lint（P3.B）、家族②迁移（P6）**均仍待做**。
- **下一步**: 走阶段 3.5（`/autoplan` 交叉 review → 处置登记）→ 归档 plan change → `/opsx:new implement-mechanical-layer-hardening-p1-issues-sweep` 进阶段 1。

### [阶段 0 / 规划] workflow 机械层固化 roadmap 文档包产出完成

- **状态**: ✅ 完成
- **实际耗时**: ~1.5h（含 3 镜并行 survey + 两次 scope 拍板）
- **产出**:
  - `openspec/roadmaps/mechanical-layer-hardening/requirements.md` — 需求综述（两腿 × adr/0006 根契约）
  - `openspec/roadmaps/mechanical-layer-hardening/design.md` — 整体设计（7 决策 + 候选全表 + Q&A 已决议）
  - `openspec/roadmaps/mechanical-layer-hardening/roadmap.md` — 实施路线图（6 阶段 × Leg1 脚本化优先 / Leg2 就绪度分级）
  - `openspec/roadmaps/mechanical-layer-hardening/task-log.md` — 任务日志（本文件）
  - `openspec/roadmaps/mechanical-layer-hardening/memo.md` — 讨论备忘（survey 综合 + 两次拍板考古）
  - `openspec/changes/plan-mechanical-layer-hardening/` — SDD 变更盒子（承载本次规划，待归档）
- **关键决策回顾**（完整档案见 `design.md` §3 和 §8）:
  - Q1：新建 roadmap + 就绪度分级（S1 就绪 / S2 north-star）。
  - Q2：拓宽成双腿（脚本化 + 去字符串化），改名「机械层固化」，Leg1 脚本化优先。
  - 两腿同归 adr/0006 硬约束；家族①② 迁 frontmatter、家族③④ 留 inline、度量锚只补 lint。
- **计划外发现（survey 实测）**:
  - ⚠️ **ship_gate.py 只在 `sdflow-ship/scripts/`，不在 T65 假设的 bundle 路径** `assets/workflow/tools/` → S1「bundle 爆炸半径」风险可能被高估。已登记为阶段 5 前置核实项。
  - 不存在一处把家族①②③④ 全枚举的块——① ③ ④ 在 T65 备注，② 在 ADR 0010。四家族是拼合的。
- **下一步**:
  - 阶段 3.5：跑 `/autoplan`（把三件套作整体 plan）交叉 review → 处置登记本文件「Review 处置」区。
  - 归档 `plan-mechanical-layer-hardening`。
  - 未来：`/opsx:new implement-mechanical-layer-hardening-p1-issues-sweep` 进阶段 1。
- **备注**:
  - S1 前置一道 ROI 评估门（inline 锚这套是否反复出同类 bug，现数据点 B4/B5）；S2 north-star 不排期，ROI 触发才起。
