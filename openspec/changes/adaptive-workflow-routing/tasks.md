# Tasks — adaptive-workflow-routing

> 变更性质：workflow bundle 规则（trigger-catalog/workflow.md）+ 各编排 SKILL 指令 + 一个新信号脚本（Python + pytest）+ lens-metric 度量扩维。
> 优先级承 proposal：P0=安全地基（地板/非平凡/声明门核）· P1=前向路由（信号脚本/阶段分支/推荐器）· P2=后向校准。
> 〔grill 全拍，2026-07-06〕三个原 OQ 已定：OQ1→D5 · OQ2 冷启动→D5 · OQ3→D6（code-review 两层切）。**无阻塞 OQ 剩余**；仅 OQ2′（校准复评节奏）非阻塞，实现期定。
> 每任务 commit 用 `bash ~/.sdflow/hack/checkpoint-commit.sh adaptive-workflow-routing:task<N>-<slug>`（命名空间格式）。

## 1. 安全地基（P0）

- [ ] 1.1 `trigger-catalog.md §7`：HR-TG 双向化语义（命中→升级不变；空集→放行轻量化资格）+ 新增成员 **TG-27（评审机制/gate契约/bundle自身变更）**，§三目录补 TG-27 定义行；§5.117 归属判定示范 [workflow-routing: 路由地板 HR-TG 双向化]
- [ ] 1.2 `workflow.md`：非平凡四谓词硬定义（P1 HR-TG命中 / P2 面超阈[结构信号为主+>100净行兜底] / P3 有开放决策 / P4 非 known-pattern，任一即非平凡）+ **P4 known-pattern 双来源**（白名单形状 ∨ 可核先例）+ 冷启动姿态 + 平凡声明格式（ff 产物一行、指明四谓词依据、P4 走先例须指名 change ID）[workflow-routing: 非平凡由四谓词硬定义 / 平凡声明显式且门核对齐脚本硬信号]
- [ ] 1.3b `trigger-catalog.md` 或 bundle 规则：登记「通用平凡形状白名单」起手三条（注释/文档-only · tests/-only · 版本常量-only），注明单一源 + 扩容即命中 TG-27 [workflow-routing: 非平凡由四谓词硬定义]
- [ ] 1.3 `workflow.md` + 设计门约定：平凡声明 vs 脚本 L0/L1 硬信号一致性门核（矛盾→拒、点名冲突项）；措辞对齐 adr/0004 红线不削弱 [spec-workflow: 设计门核平凡声明与脚本硬信号一致 / workflow-routing: 可审门核]

## 2. 前向路由（P1）

- [ ] 2.1 新建路由器脚本 `workflow/tools/route.py`（单一源）：确定性算四谓词——P1 HR-TG 命中集（§7 成员 + TG-27 path/content）、P2 面（跨模块/specs delta/新文件/净行>100）、P3 开放决策（grep OQ/决策登记/≥2方案）、P4 known-pattern（**白名单三形状机判** ∨ 指名先例存在性核）+ 输出下一步推荐/可复制 prompt——机械活交脚本，**无模型判断层**，MUST NOT 判语义残留（归 grill）[workflow-routing: 非平凡由四谓词硬定义 / 路由器为单一源脚本三层归口]
- [ ] 2.2 pytest 正例 + 反例矩阵：HR-TG 命中/空集分流；**改 gate/bundle 自身判 TG-27 命中**（防误判平凡）；**单文件微妙算法 HR-TG∅ 经 P4 仍判非平凡**；**新项目空 archive 注释-only 经白名单轻量化**；声称 known-pattern 但指不出可核先例判非平凡；面阈值边界（净行 100）；声明-硬信号矛盾检出 [workflow-routing: 非平凡由四谓词 / 门核]
- [ ] 2.3 `workflow.md` + 各编排 SKILL：每阶段 light/full 分支政策落地（grill 清晰度路由、spec-review HR-TG∅→autoplan-lite、superpowers 机械→inline TDD、done 恒跑）；**grill 跳过 MUST 显著呈现**（承 grill-not-skippable）[workflow-routing: 编排深度按阶段路由信号自适应]
- [ ] 2.4 `sdflow-code-review/SKILL.md`：落 D6 两层规则——Step1（gstack/review scope-drift+完成度）恒跑；Step2（多镜 fan-out）对有逻辑面 change 全跑、仅白名单机判无逻辑面形状免，且免除由 Step1 scope-drift 守卫（揭出隐藏逻辑→作废→照跑）；措辞明确「非只高风险才跑」[spec-workflow: sdflow-code-review 强制主审，两层深度按逻辑面自适应（MODIFIED）]
- [ ] 2.5 三层归口调用 route.py（吸收 T28）：①自有 orchestrator（spec-review/ship/code-review/done）入口 Step0 调 + 输出推荐；②`sdflow-init` 托管块（CLAUDE.md/AGENTS.md + assets 源）加一行「ff 后 MUST 跑 route.py」（**非改 opsx:ff**，升级安全）；③workflow.md 阶段表记人读兜底一句。推荐标「可人工覆盖」[workflow-routing: 路由器为单一源脚本三层归口]
- [ ] 2.6 pytest：route.py 推荐输出正确（平凡→建议轻量化+prompt / 非平凡→FULL）；`sdflow-init` 注入托管块新行的幂等断言（重跑不重复注入）[workflow-routing: 路由器为单一源脚本三层归口]

## 3. 后向校准（P2）

- [ ] 3.1 `lens-metric` 契约 + `lens_metric_aggregate.py`：扩路由决策维度（各阶段 FULL/LIGHT/SKIP、平凡判定、HR-TG 命中集、LIGHT 逃逸/FULL 空产出事后信号）；复用 fence-aware 行级锚 + 只读口径、承 config 门控 [workflow-metrics: 路由决策价值纳入度量维度]
- [ ] 3.2 pytest：路由决策维度聚合正例（LIGHT 逃逸样本可呈现、FULL 空产出率可算）[workflow-metrics: 路由决策价值纳入度量维度]
- [ ] 3.3 `/sdflow-maintain` 收尾检查步 + workflow-metrics delta：路由判松/判紧候选 `N≥复评窗口` 机械显著提示（只提示不判断、不自动调）；冷启动兜底按 D5（保守默认+白名单暖机）；**复评节奏（OQ2′）按首批数据体感定** [workflow-metrics: 路由校准复用 per-镜复评窗口且供数不供裁决 / workflow-routing: 后向校准]

## 4. 收编 issues + delta 复核 + 部署

- [ ] 4.1 issues sweep：T9（非平凡定义）→ 关联本 change 标 DONE；T28（阶段推荐）→ DONE；T19（grill 跳过条件）→ 按 OQ 结论部分闭合/留档 [/sdflow-todolist]
- [ ] 4.2 按代码实况核三 spec delta（workflow-routing/spec-workflow/workflow-metrics）与落点措辞一致；`openspec validate adaptive-workflow-routing` 通过 [全需求]
- [ ] 4.3 开发 checkout 跑 `bash setup.sh`（改 assets/workflow 才让全局 canonical 生效、测得到）；hand-off 记「merge 后 push→运行 checkout /sdflow-upgrade 激活」[spec-workflow: bundle 权威源]

## 测试覆盖图（TG-18）

| code path | 测试类型 | 用例 |
|---|---|---|
| L0 HR-TG 命中判定（含 TG-27 path/content） | 单元·正+反例 | 2.2：命中/空集/改 gate 判 TG-27 |
| 平凡声明 vs 硬信号矛盾检出 | 单元·反例 | 2.2：声明平凡但脚本命中 |
| 变更面阈值/先例判定 | 单元·边界 | 2.2：面阈值/无先例 |
| 路由决策维度聚合 | 单元·正例 | 3.2：LIGHT 逃逸/FULL 空产出 |
| 阶段分支/推荐器（指令） | 人工·SKILL 走查 | 无自动化（Markdown 编排类） |
