# Issues 批次注册表

> 半手维护：`状态:`/`成员:` 由 `issues.py`（reindex / `batch set-status`）维护，其余字段（`优先级:`/`计划:` 等）人工填写——reindex/batch 只精确 patch 生成行，绝不覆写人写行（Q3）。

### issues-pool-batch-mgmt — issues-pool-batch-mgmt
状态: PLANNED
成员: (生成) T1, T2, T3, T4, T5
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
成员: (生成) T21, T22, T48, T49
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

