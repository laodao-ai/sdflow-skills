# 2026-07 TODO

> 项目：<未注明>

## 状态总览

| ID | 模块 | 描述 | 类型 | 状态 | 时间 | 关联Change | 批次 |
|----|------|------|------|------|------|------------|------|
| T1 | `issues.py` | reindex 回显子进程 scan 的 problems 到 stderr（补齐独立跑 reindex 时表↔块不一致的可见性，D5 承诺） | 可观测性 | PROPOSED | 2026-07-03 00:26 | issues-pool-batch-mgmt | issues-pool-batch-mgmt |
| T2 | `recorder` | 字段含 ｜ 破 markdown 表：统一转义或拒绝含 ｜ 的字段（module/summary/批次名等，防位置解析读错列的数据腐蚀，系统性） | 代码质量 | PROPOSED | 2026-07-03 00:26 | issues-pool-batch-mgmt | issues-pool-batch-mgmt |
| T3 | `issues.py` | 加终态集跨脚本一致性守卫测试（issues.py TERMINAL_STATUSES ⊆ 对应 recorder STATUS_CODES，防未来改终态码漂移） | 代码质量 | PROPOSED | 2026-07-03 00:26 | issues-pool-batch-mgmt | issues-pool-batch-mgmt |
| T4 | `issues.py` | batch add 加 --if-exists skip 幂等选项；batch rename 后自动 reindex（或 SKILL 提示 rename 后跑 reindex） | 功能增强 | PROPOSED | 2026-07-03 00:26 | issues-pool-batch-mgmt | issues-pool-batch-mgmt |
| T5 | `recorder` | 补 WONTDO / 0成员人标IN_PROGRESS 分支测试；抽 _find_row_file 消除 triage 与 set-status 定位逻辑重复（4处） | 代码质量 | PROPOSED | 2026-07-03 00:26 | issues-pool-batch-mgmt | issues-pool-batch-mgmt |
| T6 | `opsx-project-init/scripts/init.py` | 两个全局 hook 仅装 Claude 侧、Codex 会话静默不生效 | 基础设施 | PROPOSED | 2026-07-03 11:35 | minimize-repo-footprint | minimize-repo-footprint |
| T7 | `spec-review/SKILL.md + impl-review/SKILL.md` | 评审报告「决策登记区」改必填 section（无决策点也显式写无）+ 主审 checklist 加核验项 | 可观测性 | PROPOSED | 2026-07-03 13:57 | minimize-repo-footprint | minimize-repo-footprint |
| T8 | `impl-review/SKILL.md` | 置信过滤阈值 <80 跨模型不可比——阈值进 config 按档位调，或改判据为对抗镜复核 | 功能增强 | PROPOSED | 2026-07-03 13:58 | minimize-repo-footprint | minimize-repo-footprint |
| T9 | `workflow.md + trigger-catalog.md` | 「非平凡」给 TG 可判的硬定义，判「平凡」须在 ff 产物显式声明一行供设计门核 | 可观测性 | PROPOSED | 2026-07-03 14:08 | minimize-repo-footprint | minimize-repo-footprint |
| T10 | `workflow.md 决策4 + opsx-ship(待开)` | 阶段三「≥2 方案有把握自动选推荐」的判据脱离自评置信——改对抗镜复核推荐项，或缺把握一律 defer | 功能增强 | PROPOSED | 2026-07-03 14:08 | minimize-repo-footprint | minimize-repo-footprint |
| T11 | `config.template.yaml + opsx-done/verify` | adr/0006 档位→模型映射落进 config.template.yaml（认领：opsx-ship 首选，footprint 顺带亦可） | 基础设施 | PROPOSED | 2026-07-03 14:08 | minimize-repo-footprint | minimize-repo-footprint |
| T12 | `opsx-maintain / resolve-workflow.sh` | 全局侧陈旧可观测：canonical 指向的 commit hash/距上次 pull 天数一行提示（运行 checkout 长期未 pull 无感知） | 可观测性 | PROPOSED | 2026-07-03 14:38 | minimize-repo-footprint | minimize-repo-footprint |
| T13 | `opsx-project-init/tests/` | resolver/setup 测试断言补强：unreadable-pointer 补 stdout 空断言、root-missing 补 stderr 文案断言、--dev+init _die 补 subprocess 测试、setup idempotent 重跑补 hack 脚本/链目标断言 | 代码质量 | PROPOSED | 2026-07-03 16:01 | minimize-repo-footprint | minimize-repo-footprint |
| T14 | `setup.sh` | Windows 指针分支补所有权检查（workflow-path 被异物占位时停手告警，同 Unix 分支） | 基础设施 | PROPOSED | 2026-07-03 16:01 | minimize-repo-footprint | minimize-repo-footprint |
| T15 | `opsx-project-init/scripts/init.py` | update --dev 时跳过陈旧遮蔽告警或换文案（dogfood 源仓每次 --dev 见两条误报⚠） | 代码质量 | PROPOSED | 2026-07-03 16:01 | minimize-repo-footprint | minimize-repo-footprint |
| T16 | `setup.sh` | install_sdflow 告警独立打印分支，不复用 skipped 数组（现输出中英文案叠加） | 代码质量 | PROPOSED | 2026-07-03 16:01 | minimize-repo-footprint | minimize-repo-footprint |
| T17 | `opsx-maintain/SKILL.md + init.py` | 陈旧遮蔽判据两处（RULE_MARKERS 常量 vs SKILL prose 复述）无同步机制，改常量会漂——考虑 opsx-maintain 兜底扫描改调脚本 | 基础设施 | PROPOSED | 2026-07-03 16:01 | minimize-repo-footprint | minimize-repo-footprint |
| T18 | `setup.sh install_into` | skills 软链切换（install_into 对既有软链 ln -snf）无指向变更提示——与 canonical 接管可见化(impl-review-fix)对齐 | 可观测性 | PROPOSED | 2026-07-03 16:18 | minimize-repo-footprint | minimize-repo-footprint |

---

## T6: 两个全局 hook 仅装 Claude 侧、Codex 会话静默不生效

| 属性 | 值 |
|------|------|
| 模块 | `opsx-project-init/scripts/init.py` |
| 类型 | 基础设施 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/minimize-repo-footprint/design.md`

**动机**：ff0-branch-guard.py / change-review-stub.py 只装 ~/.claude/hooks + 注册 ~/.claude/settings.json（Claude 事件 hook 机制）；~/.codex/hooks 不存在、Codex 无此机制，故 Codex 跑 workflow 时两 guard 静默不生效

**思路**：评估：给 Codex 等价机制，或 Codex 侧显式降级告警（对齐反静默守卫）

**备注**：来源 minimize-repo-footprint grill 2026-07-03，超该 change 范围故另办

---

## T7: 评审报告「决策登记区」改必填 section（无决策点也显式写无）+ 主审 checklist 加核验项

| 属性 | 值 |
|------|------|
| 模块 | `spec-review/SKILL.md + impl-review/SKILL.md` |
| 类型 | 可观测性 |
| 状态 | PROPOSED |

**关联文档**：`openspec/adr/0006-execution-model-baseline-fleet-anchored.md`

**动机**：执行机队锚定 opus/sonnet/gpt-5.5（adr/0006）后，G2「不弹窗、写决策登记区」是纯 prose 纪律——弱档模型易 silent pick（默默选推荐继续），设计门看不到该拍的板，且无痕迹

**思路**：报告模板把决策登记区设为必填 section（模版结构逼显形，与反静默守卫同构）；spec-review/impl-review 主审 checklist 各加一条「决策登记区存在且非空（至少显式写：本次无决策点）」核验项

**备注**：涉及两个 SKILL.md 的报告模板段；属 prose 纪律→结构模版的升格（adr/0006 约束 b）

---

## T8: 置信过滤阈值 <80 跨模型不可比——阈值进 config 按档位调，或改判据为对抗镜复核

| 属性 | 值 |
|------|------|
| 模块 | `impl-review/SKILL.md` |
| 类型 | 功能增强 |
| 状态 | PROPOSED |

**关联文档**：`openspec/adr/0006-execution-model-baseline-fleet-anchored.md`

**动机**：置信数值跨模型不可比（sonnet 打分偏高且噪声大 vs opus）；机队混编后写死 <80 会导致不同执行模型下过滤强度漂移（弱模型高分虚标→漏滤，或反向过滤过狠）

**思路**：两个方向择一：①阈值进消费仓 config.yaml 按模型档位映射调；②过滤判据从「自报置信数值」改为「对抗镜复核不通过才滤」（不信自报分，信独立复核）——倾向②，与证据锚点同思路（不信模型自述）

**备注**：涉及 impl-review SKILL.md Step3 置信过滤段；实施时走 change 落地

---

## T9: 「非平凡」给 TG 可判的硬定义，判「平凡」须在 ff 产物显式声明一行供设计门核

| 属性 | 值 |
|------|------|
| 模块 | `workflow.md + trigger-catalog.md` |
| 类型 | 可观测性 |
| 状态 | PROPOSED |

**关联文档**：`openspec/adr/0006-execution-model-baseline-fleet-anchored.md`

**动机**：grill/spec-review 的触发条件「非平凡」未定义，判定者=主 session 模型，属运行时动态分类——弱主模型误判「平凡」会静默跳过 grill+spec-review，整条防线输入未压测且无痕迹（静默形态，2026-07-03 整体评估 #1）

**思路**：①「平凡」下硬定义（如：未命中任何 TG ∧ 预估 diff < N 文件）写进 trigger-catalog；②凡判「平凡」须在 ff 产物里显式声明一行（声明进产物=可核，与反静默守卫同构），人在设计门顺手核验

**备注**：与 CLAUDE.md「误分类风险只在运行时动态路由才有」原则同源

---

## T10: 阶段三「≥2 方案有把握自动选推荐」的判据脱离自评置信——改对抗镜复核推荐项，或缺把握一律 defer

| 属性 | 值 |
|------|------|
| 模块 | `workflow.md 决策4 + opsx-ship(待开)` |
| 类型 | 功能增强 |
| 状态 | PROPOSED |

**关联文档**：`openspec/adr/0006-execution-model-baseline-fleet-anchored.md`

**动机**：「有把握」是模型自报置信，与 T8 同病——机队降档后这是阶段三无人类门的最薄弱假设：弱模型高估把握→静默错选，决策登记有理由但无人拦（2026-07-03 整体评估 #2）

**思路**：择一：①推荐项须过对抗镜复核（独立子代理试证伪推荐方案）才可自动选；②收紧为「缺客观判据（测试/基准可判）一律 defer 进 todolist」——与证据锚点同思路，不信自述

**备注**：T7/T8 医的是评审侧，本条医决策侧的同构问题；建议随 opsx-ship change 一并落（其 design 正好要定阶段三决策协议）

---

## T11: adr/0006 档位→模型映射落进 config.template.yaml（认领：opsx-ship 首选，footprint 顺带亦可）

| 属性 | 值 |
|------|------|
| 模块 | `config.template.yaml + opsx-done/verify` |
| 类型 | 基础设施 |
| 状态 | PROPOSED |

**关联文档**：`openspec/adr/0006-execution-model-baseline-fleet-anchored.md`

**动机**：adr/0006(c) 定了「强/弱=相对机队档位、映射放消费仓 config.yaml」，但无 change 认领——verify「用强模型」在消费仓层面仍是不可执行措辞（2026-07-03 整体评估 #4）

**思路**：config.template.yaml 加 model-tiers 段（强档=verify/对抗裁决/final 终审、中档=领域镜/生成、弱档=纯机械步 + 各档默认模型名）；opsx-done verify 与各编排 skill 读此段选模型

**备注**：小活；opsx-ship 的 design 需逐步指定模型档，是最自然认领方（footprint 的 config 非目标仅限「不重排契约」，加段不冲突）

---

## T12: 全局侧陈旧可观测：canonical 指向的 commit hash/距上次 pull 天数一行提示（运行 checkout 长期未 pull 无感知）

| 属性 | 值 |
|------|------|
| 模块 | `opsx-maintain / resolve-workflow.sh` |
| 类型 | 可观测性 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/minimize-repo-footprint/spec-review-report.md`

**动机**：陈旧遮蔽告警只管本地侧残留；运行 checkout remote 正确但长期未 pull 时，所有跟 HEAD 的消费仓一起吃旧规则且无任何感知（spec-review A1-P7 / autoplan #12，超本 change 范围）

**思路**：resolve-workflow.sh --explain 或 opsx-maintain 输出一行：canonical → <commit hash> (<N> 天未更新)；不做强告警，只做可观测

**备注**：spec-review 2026-07-03 上抛区转记；与 T8/T10 同属机制健壮性批次候选

---

## T14: Windows 指针分支补所有权检查（workflow-path 被异物占位时停手告警，同 Unix 分支）

| 属性 | 值 |
|------|------|
| 模块 | `setup.sh` |
| 类型 | 基础设施 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/minimize-repo-footprint/design.md`

**动机**：task 1.2 声明「同 1.1 所有权检查」但实现无条件覆盖写；异物真实目录占位时 set -e 无文案中断（终审 Important#2 降债：Unix 不受影响、Windows 场景罕见）

---

## T18: skills 软链切换（install_into 对既有软链 ln -snf）无指向变更提示——与 canonical 接管可见化(impl-review-fix)对齐

| 属性 | 值 |
|------|------|
| 模块 | `setup.sh install_into` |
| 类型 | 可观测性 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/minimize-repo-footprint/design.md`

**动机**：多 checkout 场景 skills 链被静默改指（对抗镜 B2-F1 后半）；历史行为、迁移依赖，仅缺可见性

**思路**：install_into 在替换目标不同的既有软链时输出一行 接管：旧→新（同 install_sdflow 已修样式）
