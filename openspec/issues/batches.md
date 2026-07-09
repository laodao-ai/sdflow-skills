# Issues 批次注册表

> 半手维护：`状态:`/`成员:` 由 `issues.py`（reindex / `batch set-status`）维护，其余字段（`优先级:`/`计划:` 等）人工填写——reindex/batch 只精确 patch 生成行，绝不覆写人写行（Q3）。

### issues-pool-hardening — issues-pool-batch-mgmt
状态: PLANNED
成员: (生成) T1, T2, T3, T4, T5, T66, T67
优先级: P2
计划: issues.py/recorder 健壮性：problems 回显·含｜字段转义防列腐蚀·终态集跨脚本守卫测试·batch 幂等选项·_find_row_file 抽取去重

### minimize-repo-footprint — minimize-repo-footprint
状态: PLANNED
成员: (生成) T10, T11, T12, T13, T14, T15, T16, T17, T18, T6, T7, T8, T9
优先级: P2（T10/T11 已 DONE）
计划: setup/resolver 观测与测试断言补强 + 全局 hook 双侧安装(Codex) + 评审决策区必填 section + 陈旧遮蔽文案/告警收敛

### sdflow-rebrand — sdflow-rebrand
状态: PLANNED
成员: (生成) T19, T20, T23, T24
优先级: P2（T20 已 DONE）
计划: grill 跳过条件规则化(T19) + Windows marker 分支测试(T23) + install_into 软链所有权校验(T24)。注：原 T21/T22（init.py inject/文件句柄）已挪入 sdflow-init-hardening（按 module 归位）

### sdflow-ship — sdflow-ship
状态: DONE
成员: (生成) T25, T26
优先级: P3（T25 已 DONE）
计划: gate 熔断重试计数脚本化探索（零副作用约束下的计数下沉）

### cross-model-outside-voice — cross-model-outside-voice
状态: PLANNED
成员: (生成) B1, B2, B3, T30, T31
优先级: P2（B1-B3 已 FIXED）
计划: voice 层硬化(余 T30/T31)：helper 健壮性×4·voice defer×8。注：T28(阶段提示+可复制prompt)/T29(时长记录)已按功能归 G6 挪入 rec2-obs-readability

### ship-gate-hardening — ship-gate-hardening
状态: DONE
成员: (生成) T32, T33, T34
优先级: —（已闭合）
计划: 已完成——T32(命名空间隔离)/T34(复选框分段绑定) 由 ship-gate-hardening-2 实现并 ship；T33(dirty 新鲜度) 延续为 T35、关 WONTDO

### ship-gate-hardening-2 — ship-gate-hardening-2
状态: DONE
成员: (生成) T35, T36
优先级: P3
计划: 新鲜度可选纳入工作树 dirty 状态(T33 停置延续) + checkpoint 派发指令文案收敛为单一真相源(broad-F2)

### checkpoint-tag-single-source — checkpoint-tag-single-source
状态: DONE
成员: (生成) B4, T37, T38
优先级: P1 ★
计划: anchors_in 子串→行级锚定修 B4（设计门假过的元 bug，本批最高优先） + delta spec Scenario 措辞澄清(标签形状 T37/占位符用词 T38)

### gate-anchor-line-scoped — gate-anchor-line-scoped
状态: DONE
成员: (生成) T43
优先级: P2（★ T43 前置）
计划: 已完成/分散——T43(producer 模板独占 bare line) 随 gate-checkpoint-hardening ship（98f10b9）；T41(可点击链接)/T42(人读多图) 已挪入 rec2-obs-readability（按功能归 G6）

### drop-per-dir-review-stub — drop-per-dir-review-stub
状态: DONE
成员: (生成) T44, T45
优先级: —（已闭合）
计划: 已完成——T44(退役 hook 自愈接进 setup.sh) + T45(engine.js scoped 深链恢复) 随 review-tool-followups ship（ab1ef45）

### review-tool-followups — review-tool-followups
状态: PLANNED
成员: (生成) T47
优先级: P3
计划: T47 engine.js 深链抽 resolveInitialDir+bootstrap 为可注入 mock 的纯函数补单测（深链逻辑现零单测，测试补强）。注：原 T48/T49（init.py python 守卫 / settings.json 并发）已挪入 sdflow-init-hardening（按 module 归位）

### three-lens-decision-framework — three-lens-decision-framework
状态: PLANNED
成员: (生成)
优先级: P3
计划: 已完成/分散——three-lens-decision-framework change 已 ship（5de9ede）；残差 T50(cosmetic 决策区边框) 已挪入 rec2-obs-readability（按功能归 G6）

### sdflow-init-hardening — sdflow-init-hardening
状态: PLANNED
成员: (生成) T21, T22, T48, T49, T63, T64
优先级: P2
计划: sdflow-init/scripts/init.py 健壮性（同文件、fold-vs-defer 三条齐）：主=T49 settings.json 原子写并发 lost-update TOCTOU 收窗（silent 覆盖、数据丢失面）；次=T21 inject() marker 锚错位/多旧块只修首个 · T22 open().read()→with open() 清 19 Unraisable · T48 python3/python 探测加 sys.version_info 守卫（低概率 Python2）

### gate-checkpoint-hardening — gate-checkpoint-hardening
状态: PLANNED
成员: (生成) T51, T52
优先级: P3
计划: gate/checkpoint 硬化残差: T51 tracked 非-openspec 改动被 commit 步 git add -u 先提交绕过 merge untracked 检查(需 commit 步暂存策略对齐) + T52 merge untracked 精确 baseline 快照 diff(减少既有 debris 误停)

### rec2-obs-readability — rec2-obs-readability
状态: PLANNED
成员: (生成) T27, T28, T29, T41, T42, T50, T53
优先级: P3
计划: REC-2 观测 & 人读体验(=G6，跨批重切): T27 仓内规则可参考副本 · T28 阶段结束提示+可复制 prompt · T29 各 agent/子阶段时长记录 · T41 评审报告可点击链接 · T42 人读层多图多表 · T50 spec-review 决策区边框 cosmetic · **T53 review 价值度量机制(数据驱动决定各评审层/镜/触发的必要性)**。主次: T27-T42/T50 多为 polish(用户镜)、骨架稳后带；**★T53 例外——数据驱动基建(开发循环镜)，量化各层价值后可反过来重定评审架构(降采样/收紧触发/淘汰低价值镜)，价值高于其余、宜先动**。与 T29(时长)、sdflow-code-review 现有 voice 分桶+10次采纳率复评同源，可一并设计。

### workflow-metrics-loop — workflow-metrics-loop
状态: PLANNED
成员: (生成) T54, T55
优先级: P3
计划: workflow 度量基建：T29 成本度量（checkpoint 时间戳+各编排 skill 报告）+ T54 grill amendment 存活率度量（后续独立评估，口径/数据源待定）

### sdflow-retro — sdflow-retro
状态: PLANNED
成员: (生成) T58, T59, T60, T61
优先级: P3
计划: retro 脚本硬化残差（defer 自 sdflow-retro，非阻塞）：T58 tilde `~~~` fence 支持·T59 待复评阈值 10 硬编码两处提共享常量·T60 _run_git returncode 检查（区分 git 失败 vs 真无提交）·T61 死 except 清理 + 注释订正。

### sdflow-retro-cleanup — sdflow-retro-cleanup
状态: PLANNED
成员: (生成) T62
优先级: P3
计划: T62 _run_git 系统性 git 损坏下失败节流去重（同一 subcmd 失败去重 / per-sha 聚合成一条）；低危·view-only 不中断，仅真故障下降噪。

### mlh-p2-anchor-lint — mlh-p2-anchor-lint
状态: PLANNED
成员: (生成) T68, T69
优先级: P3
计划: anchor-lint defer（非阻塞，fail-closed 安全侧）：T68 load_enums 的 lens-metric-enums 块内若未来加裸 ``` 行会提前闭合致 EnumsError（当前块内容无裸 fence 未触发）·T69 补 pin 消费仓 update 端到端交叉不变量测试（workflow.md/spec-checklists/code-checklists 原封不动、仅 tools+契约刷新）。

### mlh-p3-determ-guards — mlh-p3-determ-guards
状态: PLANNED
成员: (生成) T70, T71, T72, T73
优先级: P3
计划: 确定性守卫边缘残差（defer，多为文档化边界/理论假过）：T70 config_lint tab 缩进子键隐形→越域非法子键 fail-open（边缘 YAML）·T71 _ast_no_doc 对剥 docstring 后空体函数坍塌理论假过（当前 helper 均有真逻辑不可利用）·T72 batch lint 整行缺 优先级:/计划: 字段不校验（值语法层有意窄化）·T73 metrics.enabled 两校验器均拒绝合法行内注释（一致的有意严格，若容忍须两处同步改，设计级决定）。

### mlh-p5-gate-frontmatter — mlh-p5-gate-frontmatter
状态: PLANNED
成员: (生成) T74, T75
优先级: P3
计划: ship_gate parser 健壮性 + 死代码清理（defer 自 mlh-p5-gate-frontmatter，非阻塞）：T74 裸 `---` 首行无闭合误判 unterminated 致 UNKNOWN·T75 清 live inline 死代码 anchors_in/pick_exclusive/ANCHOR_DESIGN/ANCHOR_CR_*。择期单开 cleanup change。

### mechanical-layer-hardening — 机械层固化（adr/0006：脚本化 + 去字符串化）
状态: PLANNED
成员: (生成) T76, T77
优先级: P2（原口语「中」归一化到 P 级；冷审残差 defer，非关键）
计划: roadmap mechanical-layer-hardening 各阶段冷审残差 defer 归集（T76 归档盲区硬化/T77 spec 整洁性等）

### mlh-p4-target-state — mechanical-layer-hardening P4/P6 目标态重评
状态: PLANNED
成员: (生成) T78, T79, T80, T81, T82, T83, T84, T85
优先级: P1（4.B 最高〔4.C 已交付〕· 4.D.* 次 · 4.A/4.D.3 待 embedded 契约 · T85=P6 端态 A 已定·压轴排 P4 后）
计划: 目标态重评 P4 脚本化候选 + P6 端态决策。✅已交付:T78(4.C lens-metric 手数归约,闭合 §1.2 痛点#2 —— change implement-mechanical-layer-hardening-p4-lens-metric-emit / bd7c05f);★该做未做〔explore 拍板 A·2 change：① T79(4.B maintain set-diff)块头单开 · ② T80/T81/T82(4.D.1/2/4 小守卫)三合一;4.B 先〕;◐该做待 embedded 契约:T83(4.A log_check)·T84(4.D.3);端态已定:T85(P6=端态 A 迁 frontmatter 根治,否决 B 治标;约束①历史不迁使成本≈P5 dual-read;压轴排 P4 后)。判据=目标态(§1.3+adr/0006)+根治,非现状快照

### implement-mechanical-layer-hardening-p4-lens-metric-emit — implement-mechanical-layer-hardening-p4-lens-metric-emit
状态: PLANNED
成员: (生成) T86, T87, T88
优先级: P3
计划: lens-metric-emit 契约健壮性 defer（非阻塞）：T86 anchor_lint load_enums 未闭合 fence 不 fail-closed（与 emitter _read_block_pairs 同盲区，本 change 已修 emitter 侧）·T87 enums 块重复键静默后写覆盖，与 fold 块 fail-closed 口径统一（逐项拒重复 + 负例测试）·T88 无 CI/pre-commit → 单一源守卫测试仅手动 pytest 生效（契约/常量漂移下次跑测试才暴露）。

### done-roadmap-writeback — done-roadmap-writeback
状态: PLANNED
成员: (生成) T89, T90, T91, T92
优先级: P3
计划: roadmap_writeback_draft 健壮性 defer（非阻塞）：T89 probe_format 全文扫描非限定 phase（混合格式误判 checkbox；修法 probe 增 phase 参数只扫该 phase 行段）·T90 frontmatter 解析与 ship_gate.py parity 缺口 BOM/tab 缩进/YAML 行尾注释（nested-key 已 FIX-3 修）·T91 PREFIX_RE 贪婪 `.+` 对含 -pN- 样式 change 名命名固有歧义·T92 test_verify_state_malformed_* 无 ship-gate 包裹。

### mlh-p4-maintain-scan — mlh-p4-maintain-scan
状态: PLANNED
成员: (生成) T93, T94, T95, T96
优先级: <待填>
计划: <待填>

