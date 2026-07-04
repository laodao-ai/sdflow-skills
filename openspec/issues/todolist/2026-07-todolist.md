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
| T10 | `workflow.md 决策4 + opsx-ship(待开)` | 阶段三「≥2 方案有把握自动选推荐」的判据脱离自评置信——改对抗镜复核推荐项，或缺把握一律 defer | 功能增强 | DONE | 2026-07-03 14:08 | minimize-repo-footprint | minimize-repo-footprint |
| T11 | `config.template.yaml + opsx-done/verify` | adr/0006 档位→模型映射落进 config.template.yaml（认领：opsx-ship 首选，footprint 顺带亦可） | 基础设施 | DONE | 2026-07-03 14:08 | minimize-repo-footprint | minimize-repo-footprint |
| T12 | `opsx-maintain / resolve-workflow.sh` | 全局侧陈旧可观测：canonical 指向的 commit hash/距上次 pull 天数一行提示（运行 checkout 长期未 pull 无感知） | 可观测性 | PROPOSED | 2026-07-03 14:38 | minimize-repo-footprint | minimize-repo-footprint |
| T13 | `opsx-project-init/tests/` | resolver/setup 测试断言补强：unreadable-pointer 补 stdout 空断言、root-missing 补 stderr 文案断言、--dev+init _die 补 subprocess 测试、setup idempotent 重跑补 hack 脚本/链目标断言 | 代码质量 | PROPOSED | 2026-07-03 16:01 | minimize-repo-footprint | minimize-repo-footprint |
| T14 | `setup.sh` | Windows 指针分支补所有权检查（workflow-path 被异物占位时停手告警，同 Unix 分支） | 基础设施 | PROPOSED | 2026-07-03 16:01 | minimize-repo-footprint | minimize-repo-footprint |
| T15 | `opsx-project-init/scripts/init.py` | update --dev 时跳过陈旧遮蔽告警或换文案（dogfood 源仓每次 --dev 见两条误报⚠） | 代码质量 | PROPOSED | 2026-07-03 16:01 | minimize-repo-footprint | minimize-repo-footprint |
| T16 | `setup.sh` | install_sdflow 告警独立打印分支，不复用 skipped 数组（现输出中英文案叠加） | 代码质量 | PROPOSED | 2026-07-03 16:01 | minimize-repo-footprint | minimize-repo-footprint |
| T17 | `opsx-maintain/SKILL.md + init.py` | 陈旧遮蔽判据两处（RULE_MARKERS 常量 vs SKILL prose 复述）无同步机制，改常量会漂——考虑 opsx-maintain 兜底扫描改调脚本 | 基础设施 | PROPOSED | 2026-07-03 16:01 | minimize-repo-footprint | minimize-repo-footprint |
| T18 | `setup.sh install_into` | skills 软链切换（install_into 对既有软链 ln -snf）无指向变更提示——与 canonical 接管可见化(impl-review-fix)对齐 | 可观测性 | PROPOSED | 2026-07-03 16:18 | minimize-repo-footprint | minimize-repo-footprint |
| T19 | `workflow.md + generation-process.md（权威源）` | 重新评估 grill 轮的跳过条件（默认必跑？何种前提可跳？）——后续单独评估再定规则；唯一先行共识 = 跳过类判定必须显著呈现给用户 | 可观测性 | PROPOSED | 2026-07-03 17:38 | sdflow-rebrand | sdflow-rebrand |
| T20 | `spec-review/SKILL.md（现 sdflow-spec-review）` | 固化 spec-review 编排顺序：autoplan 先行落 amendment 后再 fan-out 多镜——顺序是设计性质（多镜复审 autoplan 改动）而非可并行的优化项 | 代码质量 | DONE | 2026-07-03 17:42 | sdflow-rebrand | sdflow-rebrand |
| T21 | `sdflow-init/scripts/init.py` | inject() 畸形态加固：多重复旧 marker 区块只修第一个 + _find_marker_line 的 text.index 在行内嵌相同 marker 文本时可能锚错位 | 代码质量 | PROPOSED | 2026-07-03 21:10 | sdflow-rebrand | sdflow-rebrand |
| T22 | `sdflow-init/scripts/init.py` | open().read() 统一改 with open()（-W error 下 19 个 PytestUnraisableExceptionWarning，pre-existing 模式） | 代码质量 | PROPOSED | 2026-07-03 21:10 | sdflow-rebrand | sdflow-rebrand |
| T23 | `setup.sh Windows copy 分支` | Windows 分支（IS_WINDOWS=1）marker 换写 .sdflow-skills 无直接测试（沙箱恒 Unix；名单判定函数已双向测试） | 代码质量 | PROPOSED | 2026-07-03 21:10 | sdflow-rebrand | sdflow-rebrand |
| T24 | `setup.sh install_into 软链分支` | install_into 对既有软链零所有权校验——同名异物软链被 ln -snf 无声覆盖（已复现）；需专门设计「何为自属目标」再修，与 T18（可见性）分立 | 基础设施 | PROPOSED | 2026-07-03 21:29 | sdflow-rebrand | sdflow-rebrand |
| T25 | `sdflow-spec-review/SKILL.md Step1 + sdflow-code-review Step1（gstack/review 同病）` | autoplan/gstack-review 原生流程被「子代理读 SKILL.md 模拟执行」替换——须修复为真实调用，或把模拟显式定义为降级模式并标注 | 代码质量 | DONE | 2026-07-03 23:57 | sdflow-ship | sdflow-ship |
| T26 | `sdflow-ship/SKILL.md` | 熔断重试计数脚本化方案探索（gate 零副作用约束下的计数下沉） | 功能增强 | PROPOSED | 2026-07-04 02:40 | sdflow-ship | sdflow-ship |
| T27 | `openspec/workflow + resolve-workflow.sh` | workflow 规则在项目 openspec(/workflow) 下提供可参考副本（便于 @ 引用与复制 prompt）——须先消解与「仓内不留规则副本防 pin 遮蔽」拍板的冲突 | 基础设施 | OPEN | 2026-07-04 09:57 | minimize-repo-footprint |  |
| T28 | `sdflow-init/assets/workflow/workflow.md + 各编排 skill 收尾段` | 每阶段结束后按 workflow 给出下一阶段提示，并附完整可复制 prompt（用户可参考/复制，或选择后直接按该 prompt 执行） | 功能增强 | PROPOSED | 2026-07-04 10:51 | cross-model-outside-voice | cross-model-outside-voice |
| T29 | `workflow 度量（ship_gate/checkpoint 时间戳 + 各编排 skill 报告）` | 记录每个 agent 花费时长 + workflow 各子阶段时长（spec-review、ship 的分层子阶段）+ 各阶段汇总 | 可观测性 | PROPOSED | 2026-07-04 11:57 | cross-model-outside-voice | cross-model-outside-voice |
| T30 | `sdflow-init/assets/hack/outside-voice.sh + tests` | helper 健壮性小项×4（final review triage record-as-debt）：OV_MAX 非数值校验 / flag 缺值 shift 2 死循环护栏 / mktemp 返回值检查 / fake timeout stub 时序依赖 | 代码质量 | PROPOSED | 2026-07-04 12:46 | cross-model-outside-voice | cross-model-outside-voice |
| T31 | `outside-voice.sh + 两 SKILL 协议节 + setup.sh` | voice 层后续硬化池（code-review 多镜确认、本轮未修的 defer 项 ×8） | 代码质量 | PROPOSED | 2026-07-04 13:35 | cross-model-outside-voice | cross-model-outside-voice |
| T32 | `ship_gate.py` | 完成判据 checkpoint 任务号加 change 命名空间 | 代码质量 | OPEN | 2026-07-04 16:50 | ship-gate-hardening |  |
| T33 | `ship_gate.py` | 新鲜度可选纳入工作树 dirty 状态 | 代码质量 | OPEN | 2026-07-04 16:50 | ship-gate-hardening |  |
| T34 | `ship_gate.py` | 复选框辅通道按 Task 分段绑定 | 代码质量 | OPEN | 2026-07-04 16:50 | ship-gate-hardening |  |

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
| 状态 | DONE |

**关联文档**：`openspec/adr/0006-execution-model-baseline-fleet-anchored.md`

**动机**：「有把握」是模型自报置信，与 T8 同病——机队降档后这是阶段三无人类门的最薄弱假设：弱模型高估把握→静默错选，决策登记有理由但无人拦（2026-07-03 整体评估 #2）

**思路**：择一：①推荐项须过对抗镜复核（独立子代理试证伪推荐方案）才可自动选；②收紧为「缺客观判据（测试/基准可判）一律 defer 进 todolist」——与证据锚点同思路，不信自述

**备注**：T7/T8 医的是评审侧，本条医决策侧的同构问题；建议随 opsx-ship change 一并落（其 design 正好要定阶段三决策协议）
> 2026-07 状态：PROPOSED → DONE（change sdflow-ship, 3d0b546; sdflow-ship/SKILL.md 决策协议节 + workflow.md 决策4）

---

## T11: adr/0006 档位→模型映射落进 config.template.yaml（认领：opsx-ship 首选，footprint 顺带亦可）

| 属性 | 值 |
|------|------|
| 模块 | `config.template.yaml + opsx-done/verify` |
| 类型 | 基础设施 |
| 状态 | DONE |

**关联文档**：`openspec/adr/0006-execution-model-baseline-fleet-anchored.md`

**动机**：adr/0006(c) 定了「强/弱=相对机队档位、映射放消费仓 config.yaml」，但无 change 认领——verify「用强模型」在消费仓层面仍是不可执行措辞（2026-07-03 整体评估 #4）

**思路**：config.template.yaml 加 model-tiers 段（强档=verify/对抗裁决/final 终审、中档=领域镜/生成、弱档=纯机械步 + 各档默认模型名）；opsx-done verify 与各编排 skill 读此段选模型

**备注**：小活；opsx-ship 的 design 需逐步指定模型档，是最自然认领方（footprint 的 config 非目标仅限「不重排契约」，加段不冲突）
> 2026-07 状态：PROPOSED → DONE（change sdflow-ship, 3d0b546; assets/workflow/model-tiers.md + config.template.yaml 覆盖段 + 四 SKILL 引用句）

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

---

## T19: 重新评估 grill 轮的跳过条件（默认必跑？何种前提可跳？）——后续单独评估再定规则；唯一先行共识 = 跳过类判定必须显著呈现给用户

| 属性 | 值 |
|------|------|
| 模块 | `workflow.md + generation-process.md（权威源）` |
| 类型 | 可观测性 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/sdflow-rebrand/design.md`

**动机**：sdflow-rebrand 起手时主 session 以「explore 已履行对话岛职能」为由跳过 grill，声明埋在长消息末尾用户未看到——用户重估：grill 是对 explore 结论的二次审视（隔步回头死磕），与 explore 现场拍板不可互相折叠，不能轻易跳过；本次 Detection 层（接地镜/对抗镜）抓到的 sweep 面漏洞即 grill 缺席的代价旁证

**思路**：**待评估，勿当定案**。候选思路（评估时的输入而非结论）：①默认必跑，可跳前提硬条件化（如 explore 同轮逐项拍板 + 无新增术语 + ADR 已排 + 用户明示可跳）；②跳过判定进 spec-review-report 决策登记区单列供设计门勾选；③与 T9（非平凡硬定义）同族同批评估。最终规则以该次评估结论为准

**备注**：用户反馈原话：grill 很重要，是对前面 explore 讨论结果的再次审视，不能轻易跳过；本次 change 放行

---

## T20: 固化 spec-review 编排顺序：autoplan 先行落 amendment 后再 fan-out 多镜——顺序是设计性质（多镜复审 autoplan 改动）而非可并行的优化项

| 属性 | 值 |
|------|------|
| 模块 | `spec-review/SKILL.md（现 sdflow-spec-review）` |
| 类型 | 代码质量 |
| 状态 | DONE |

**关联文档**：`openspec/changes/sdflow-rebrand/design.md`

**动机**：SKILL.md 本为 Step1→Step2 串行，但主 session 两轮实际执行均将 autoplan 与多镜并行化求快——若 autoplan 对 proposal/design/specs 落 [gstack-amendment]，并行导致多镜审的是改动前快照，丢失「后续镜复审 autoplan 修改、抓修改后不一致」的设计性质（用户 2026-07-03 指出）

**思路**：①SKILL.md Step2 开头显式加一句「MUST 待 Step1 checkpoint 完成后才 fan-out；禁止与 Step1 并行——多镜的评审对象须含 autoplan amendment」（把隐含顺序变禁止性措辞，防执行者优化掉）；②补一条执行纪律：若确已并行（历史运行），Step3 裁决须 diff autoplan 的 amendment 并对照镜 findings 做增量核对、在报告注明

**备注**：本轮（sdflow-rebrand）已按 ②的补救路径处理：autoplan 返回后核其是否改动四件套，有改动则在裁决步增量核对并写进报告
> 2026-07 状态：PROPOSED → DONE（change sdflow-ship, 3d0b546; sdflow-spec-review/SKILL.md Step2 串行句）

---

## T21: inject() 畸形态加固：多重复旧 marker 区块只修第一个 + _find_marker_line 的 text.index 在行内嵌相同 marker 文本时可能锚错位

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-init/scripts/init.py` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/sdflow-rebrand/design.md`

**动机**：幂等下不自然产生，仅手工粘贴畸形态（终审 triage：记债不阻塞）

---

## T22: open().read() 统一改 with open()（-W error 下 19 个 PytestUnraisableExceptionWarning，pre-existing 模式）

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-init/scripts/init.py` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/sdflow-rebrand/design.md`

**动机**：默认 -q 下 233 passed 无 warning；-W error 加严才暴露；修法机械（终审 triage）

---

## T23: Windows 分支（IS_WINDOWS=1）marker 换写 .sdflow-skills 无直接测试（沙箱恒 Unix；名单判定函数已双向测试）

| 属性 | 值 |
|------|------|
| 模块 | `setup.sh Windows copy 分支` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/sdflow-rebrand/design.md`

**动机**：终审弱锚注记：R-SR-2 换写 Scenario 的 Windows 侧只有共享函数级锚点

---

## T24: install_into 对既有软链零所有权校验——同名异物软链被 ln -snf 无声覆盖（已复现）；需专门设计「何为自属目标」再修，与 T18（可见性）分立

| 属性 | 值 |
|------|------|
| 模块 | `setup.sh install_into 软链分支` |
| 类型 | 基础设施 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/sdflow-rebrand/code-review-report.md`

**动机**：impl-review 断言盲区镜实证：异物 basename 撞本仓 skill 名时被静默吃掉，违反「绝不动非自属产物」红线；属未改动行既有行为（laodao→sdflow 迁移曾依赖该替换语义），加严校验会破坏 dev↔runtime 切换——设计权衡后再修，勿被 T18 的「加提示」方案掩盖

**思路**：设计判据候选：readlink 目标路径含已知 checkout 家族 / 目标 basename ∈ OUR_LEGACY_NAMES / marker 同源；配套测试须含「同名异物软链」态（现测试网空白）

---

## T25: autoplan/gstack-review 原生流程被「子代理读 SKILL.md 模拟执行」替换——须修复为真实调用，或把模拟显式定义为降级模式并标注

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-spec-review/SKILL.md Step1 + sdflow-code-review Step1（gstack/review 同病）` |
| 类型 | 代码质量 |
| 状态 | DONE |

**关联文档**：`openspec/changes/sdflow-ship/design.md`

**动机**：SKILL 自述「autoplan 跑自己的流程，prompt 不注入」，但编排实际把它下放为 general-purpose 子代理照本模拟：两轮真实运行均自报偏离（gstack 原生 preamble/telemetry/交互决策未运行、降级自审）——广审层质量与原生不等价，且当前呈现方式把模拟当原生（违反静默守卫精神）；用户 2026-07-03 指出

**思路**：**方向已拍板（用户 2026-07-03：希望发挥 autoplan 本身的能力）**：①为主——主 session 经 Skill 机制原生执行 autoplan（其指令直接进主 session，非子代理转述），与 T20 串行序天然兼容；③仅作 fallback 且必须显式标注「模拟广审（降级模式）」；②调研 gstack headless 路径作补充。sdflow-code-review 的 Step1 gstack/review 同构问题一并按此方向修。sdflow-ship 评审轮已当场切换原生执行（先例）

**备注**：本轮 sdflow-ship 评审进行中：Step1 已按现状（模拟）在跑，报告将显式标注降级而非伪装原生
> 2026-07 状态：PROPOSED → DONE（change cross-model-outside-voice tasks §2 (task5/task6/task7 checkpoints)）

---

## T26: 熔断重试计数脚本化方案探索（gate 零副作用约束下的计数下沉）

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-ship/SKILL.md` |
| 类型 | 功能增强 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/sdflow-ship/design.md`

**动机**：D5 熔断当前靠主 session prose 计数，弱模型可能忘计或混淆

**思路**：候选：checkpoint 标记 attempt / gate 输出含建议重试上限的结构化提示 / 宿主层计数——均需先解 D1 零副作用与计数落盘的矛盾

---

## T27: workflow 规则在项目 openspec(/workflow) 下提供可参考副本（便于 @ 引用与复制 prompt）——须先消解与「仓内不留规则副本防 pin 遮蔽」拍板的冲突

| 属性 | 值 |
|------|------|
| 模块 | `openspec/workflow + resolve-workflow.sh` |
| 类型 | 基础设施 |
| 状态 | OPEN |

**关联文档**：`openspec/adr/0003-deploy-footprint-global-rules-minimal-repo-copy.md`

**动机**：用户 2026-07-04 提出：规则移全局 canonical（~/.sdflow/workflow/）后，项目内无法用 @ 直接引用规则文件，参考与复制 prompt 不便

**思路**：与 minimize-repo-footprint 拍板（勿把规则拷回仓内，副本会被 resolver 判 pin 遮蔽全局）正面相抵，落地前需设计消解方案，候选：①只读 reference 拷贝且标注/改造 resolver 不识别为 pin ②仓内 symlink 指向 ~/.sdflow/workflow（@ 可达且不算副本，需验证 resolver 行为）③resolve-workflow.sh 加打印路径/内容子命令满足复制 prompt 诉求

**备注**：提出于 cross-model-outside-voice 会话，内容上属 minimize-repo-footprint 后续

---

## T28: 每阶段结束后按 workflow 给出下一阶段提示，并附完整可复制 prompt（用户可参考/复制，或选择后直接按该 prompt 执行）

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-init/assets/workflow/workflow.md + 各编排 skill 收尾段` |
| 类型 | 功能增强 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/cross-model-outside-voice/spec-review-report.md`

**动机**：用户 2026-07-04 提出：阶段收尾时只说「下一步是 X」不够——应给出下一阶段的完整 prompt 文本，便于用户核对将要发生什么、复制到别处用，或确认后原样执行

**思路**：候选落点：①workflow.md 阶段表每步附「标准起手 prompt」栏（单一源）；②各编排 skill（sdflow-spec-review/sdflow-code-review/sdflow-done/sdflow-ship）收敛口输出模板加「下一步完整 prompt」区块；③与 hand-off.md 的 next-stage advice 段合流。注意与 T27（规则可参考副本）同属「把工作流内部知识显性给用户」一族

**备注**：提出于 cross-model-outside-voice spec-review 进行中；属 workflow bundle 级改进，非本 change scope

---

## T29: 记录每个 agent 花费时长 + workflow 各子阶段时长（spec-review、ship 的分层子阶段）+ 各阶段汇总

| 属性 | 值 |
|------|------|
| 模块 | `workflow 度量（ship_gate/checkpoint 时间戳 + 各编排 skill 报告）` |
| 类型 | 可观测性 |
| 状态 | PROPOSED |

**关联文档**：`openspec/ROADMAP.md`

**动机**：用户 2026-07-04 提出：想知道时间花在哪——每个子代理耗时、spec-review/ship 内部每个子步耗时、阶段级汇总，为流程优化与「哪层值不值得留」供数

**思路**：候选：①盘面即状态路线——checkpoint commit 时间戳序列已是天然步级时长锚（零新状态，写个汇总脚本 git log --format 即可推各步耗时）；②子代理耗时——harness 已在 Agent 结果里带 duration_ms/usage，编排 skill 收尾时抄进报告锚行（如 v1 锚行加 duration_s 字段）；③阶段汇总——并入 workflow-metrics-loop（ROADMAP 待开，只读报告产物聚合）。与 T28（阶段收尾提示）同族：都是把工作流内部信息显性化。**〔用户补充 2026-07-04〕等待人工确认/暂停的时间须单列并可剔除**——纯 commit 时间差会把人类门等待（设计门拍板、grill 对话、会话中断）算进步时长，失真；候选判据：人类门/交互步（grill、设计门、AskUserQuestion 区间）打独立锚或按步类型白名单剔除，报「工作时长」与「墙钟时长」两列

**备注**：内容上属 workflow-metrics-loop scope 的先行需求；提出于 cross-model-outside-voice ship 进行中

---

## T30: helper 健壮性小项×4（final review triage record-as-debt）：OV_MAX 非数值校验 / flag 缺值 shift 2 死循环护栏 / mktemp 返回值检查 / fake timeout stub 时序依赖

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-init/assets/hack/outside-voice.sh + tests` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/cross-model-outside-voice/superpowers-plan.md`

**动机**：cross-model-outside-voice final whole-branch review（opus）triage：四项均不在 SKILL 驱动的真实执行路径上（默认值合法/协议恒传路径/极端环境），judged record-as-debt 非 must-fix；其中 flag 缺值已实测复现挂死（真实流程不可达）

**思路**：一次小清理：①OV_MAX_CONTEXT_BYTES 数值校验否则回落默认；②while 参数解析对缺值 flag 直接 usage exit 2；③mktemp 失败即 die；④fake timeout stub 换确定性信号同步

---

## T31: voice 层后续硬化池（code-review 多镜确认、本轮未修的 defer 项 ×8）

| 属性 | 值 |
|------|------|
| 模块 | `outside-voice.sh + 两 SKILL 协议节 + setup.sh` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/cross-model-outside-voice/code-review-report.md`

**动机**：cross-model-outside-voice 代码审（8 镜 + 双 codex voice + fallback）确认的真实但非阻塞项，本轮已修 21 项后的残差

**思路**：①协议节 18 行在两 SKILL 逐字重复→下沉 bundle 单一源文件；②cap/timeout 校准——实测 185KB context 致 codex 300s 超时（本轮 code-voice 实证），需 OV_MAX 与 timeout 匹配调参或分片；③同 change 并行评审 context 文件互踩（固定命名无锁）→ 加运行 ID 后缀或 flock；④调用方 voice stdout 落点规范空白（/tmp 固定名并发覆盖）；⑤父进程被杀后 timeout/codex 孤儿存活（进程组治理）；⑥UNTRUSTED CONTEXT 分隔符可被内容伪造→nonce 化（frame 措辞缓解已加）；⑦UTF-8 字节截断切碎多字节字符；⑧setup.sh cp 覆盖运行中脚本非原子→tmp+mv；另：codex -s read-only 沙箱边界黑盒验证（能否读 -C 外/执行 shell）

---

## T32: 完成判据 checkpoint 任务号加 change 命名空间

| 属性 | 值 |
|------|------|
| 模块 | `ship_gate.py` |
| 类型 | 代码质量 |
| 状态 | OPEN |

**关联文档**：`openspec/changes/ship-gate-hardening/design.md`

**动机**：完成锚 checkpoint(task<n>-) 无 change 归属,同分支交错跑两个 change 时同号任务可污染完成集(窗口下界 plan_first_sha 已部分缓解,非彻底)

**思路**：checkpoint 契约加 change slug/trailer 如 checkpoint(<change>:task1-) 或 sdflow-change: trailer,gate 只认当前 change;旧格式歧义时 UNKNOWN

**备注**：ship-gate-hardening 代码审 HR-TG code 镜发现,pre-existing 非本 change 引入

---

## T33: 新鲜度可选纳入工作树 dirty 状态

| 属性 | 值 |
|------|------|
| 模块 | `ship_gate.py` |
| 类型 | 代码质量 |
| 状态 | OPEN |

**关联文档**：`openspec/changes/ship-gate-hardening/design.md`

**动机**：is_stale 只看已提交盘面,verify/code-review 后工作树 staged/unstaged/untracked 的非 openspec 代码改动不触发 RERUN_STALE

**思路**：code scope 可选追加 git status --porcelain 分类;报告锚后存在 dirty 非 openspec 路径→RERUN_STALE/UNKNOWN。注:与「盘面即状态=committed 产物」设计张力,需先定性

**备注**：HR-TG code 镜发现,pre-existing

---

## T34: 复选框辅通道按 Task 分段绑定

| 属性 | 值 |
|------|------|
| 模块 | `ship_gate.py` |
| 类型 | 代码质量 |
| 状态 | OPEN |

**关联文档**：`openspec/changes/ship-gate-hardening/design.md`

**动机**：checkboxes_all 只看全文有无 - [x]/- [ ],一个全局勾选可放行所有 plan task,未按 ### Task <n>: 分段;与集合归属主锚并存时可能覆盖

**思路**：按 ### Task <n>: 分段解析,要求每个计划内 task 段都有完成标记,否则 checkbox fallback 不覆盖 checkpoint 集合归属

**备注**：HR-TG code 镜发现,pre-existing
