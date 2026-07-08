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

## 2026-07-08

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
