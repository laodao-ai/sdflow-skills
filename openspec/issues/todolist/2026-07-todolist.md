# 2026-07 TODO

> 项目：<未注明>

## 状态总览

| ID | 模块 | 描述 | 类型 | 状态 | 时间 | 关联Change | 批次 |
|----|------|------|------|------|------|------------|------|
| T1 | `issues.py` | reindex 回显子进程 scan 的 problems 到 stderr（补齐独立跑 reindex 时表↔块不一致的可见性，D5 承诺） | 可观测性 | DONE | 2026-07-03 00:26 | issues-pool-batch-mgmt | issues-pool-hardening |
| T2 | `recorder` | 字段含 ｜ 破 markdown 表：统一转义或拒绝含 ｜ 的字段（module/summary/批次名等，防位置解析读错列的数据腐蚀，系统性） | 代码质量 | DONE | 2026-07-03 00:26 | issues-pool-batch-mgmt | issues-pool-hardening |
| T3 | `issues.py` | 加终态集跨脚本一致性守卫测试（issues.py TERMINAL_STATUSES ⊆ 对应 recorder STATUS_CODES，防未来改终态码漂移） | 代码质量 | DONE | 2026-07-03 00:26 | issues-pool-batch-mgmt | issues-pool-hardening |
| T4 | `issues.py` | batch add 加 --if-exists skip 幂等选项；batch rename 后自动 reindex（或 SKILL 提示 rename 后跑 reindex） | 功能增强 | DONE | 2026-07-03 00:26 | issues-pool-batch-mgmt | issues-pool-hardening |
| T5 | `recorder` | 补 WONTDO / 0成员人标IN_PROGRESS 分支测试；抽 _find_row_file 消除 triage 与 set-status 定位逻辑重复（4处） | 代码质量 | DONE | 2026-07-03 00:26 | issues-pool-batch-mgmt | issues-pool-hardening |
| T6 | `opsx-project-init/scripts/init.py` | 两个全局 hook 仅装 Claude 侧、Codex 会话静默不生效 | 基础设施 | PROPOSED | 2026-07-03 11:35 | minimize-repo-footprint | minimize-repo-footprint |
| T7 | `spec-review/SKILL.md + impl-review/SKILL.md` | 评审报告「决策登记区」改必填 section（无决策点也显式写无）+ 主审 checklist 加核验项 | 可观测性 | PROPOSED | 2026-07-03 13:57 | minimize-repo-footprint | minimize-repo-footprint |
| T8 | `impl-review/SKILL.md` | 置信过滤阈值 <80 跨模型不可比——阈值进 config 按档位调，或改判据为对抗镜复核 | 功能增强 | PROPOSED | 2026-07-03 13:58 | minimize-repo-footprint | minimize-repo-footprint |
| T9 | `workflow.md + trigger-catalog.md` | 「非平凡」给 TG 可判的硬定义，判「平凡」须在 ff 产物显式声明一行供设计门核 | 可观测性 | PROPOSED | 2026-07-03 14:08 | minimize-repo-footprint | minimize-repo-footprint |
| T10 | `workflow.md 决策4 + opsx-ship(待开)` | 阶段三「≥2 方案有把握自动选推荐」的判据脱离自评置信——改对抗镜复核推荐项，或缺把握一律 defer | 功能增强 | DONE | 2026-07-03 14:08 | minimize-repo-footprint | minimize-repo-footprint |
| T11 | `config.template.yaml + opsx-done/verify` | adr/0006 档位→模型映射落进 config.template.yaml（认领：opsx-ship 首选，footprint 顺带亦可） | 基础设施 | DONE | 2026-07-03 14:08 | minimize-repo-footprint | minimize-repo-footprint |
| T12 | `opsx-maintain / resolve-workflow.sh` | 全局侧陈旧可观测：canonical 指向的 commit hash/距上次 pull 天数一行提示（运行 checkout 长期未 pull 无感知） | 可观测性 | PROPOSED | 2026-07-03 14:38 | minimize-repo-footprint | minimize-repo-footprint |
| T13 | `opsx-project-init/tests/` | resolver/setup 测试断言补强：unreadable-pointer 补 stdout 空断言、root-missing 补 stderr 文案断言、--dev+init _die 补 subprocess 测试、setup idempotent 重跑补 hack 脚本/链目标断言 | 代码质量 | DONE | 2026-07-03 16:01 | minimize-repo-footprint | minimize-repo-footprint |
| T14 | `setup.sh` | Windows 指针分支补所有权检查（workflow-path 被异物占位时停手告警，同 Unix 分支） | 基础设施 | PROPOSED | 2026-07-03 16:01 | minimize-repo-footprint | minimize-repo-footprint |
| T15 | `opsx-project-init/scripts/init.py` | update --dev 时跳过陈旧遮蔽告警或换文案（dogfood 源仓每次 --dev 见两条误报⚠） | 代码质量 | PROPOSED | 2026-07-03 16:01 | minimize-repo-footprint | minimize-repo-footprint |
| T16 | `setup.sh` | install_sdflow 告警独立打印分支，不复用 skipped 数组（现输出中英文案叠加） | 代码质量 | PROPOSED | 2026-07-03 16:01 | minimize-repo-footprint | minimize-repo-footprint |
| T17 | `opsx-maintain/SKILL.md + init.py` | 陈旧遮蔽判据两处（RULE_MARKERS 常量 vs SKILL prose 复述）无同步机制，改常量会漂——考虑 opsx-maintain 兜底扫描改调脚本 | 基础设施 | PROPOSED | 2026-07-03 16:01 | minimize-repo-footprint | minimize-repo-footprint |
| T18 | `setup.sh install_into` | skills 软链切换（install_into 对既有软链 ln -snf）无指向变更提示——与 canonical 接管可见化(impl-review-fix)对齐 | 可观测性 | PROPOSED | 2026-07-03 16:18 | minimize-repo-footprint | minimize-repo-footprint |
| T19 | `workflow.md + generation-process.md（权威源）` | 重新评估 grill 轮的跳过条件（默认必跑？何种前提可跳？）——后续单独评估再定规则；唯一先行共识 = 跳过类判定必须显著呈现给用户 | 可观测性 | PROPOSED | 2026-07-03 17:38 | sdflow-rebrand | sdflow-rebrand |
| T20 | `spec-review/SKILL.md（现 sdflow-spec-review）` | 固化 spec-review 编排顺序：autoplan 先行落 amendment 后再 fan-out 多镜——顺序是设计性质（多镜复审 autoplan 改动）而非可并行的优化项 | 代码质量 | DONE | 2026-07-03 17:42 | sdflow-rebrand | sdflow-rebrand |
| T21 | `sdflow-init/scripts/init.py` | inject() 畸形态加固：多重复旧 marker 区块只修第一个 + _find_marker_line 的 text.index 在行内嵌相同 marker 文本时可能锚错位 | 代码质量 | DONE | 2026-07-03 21:10 | sdflow-rebrand | sdflow-init-hardening |
| T22 | `sdflow-init/scripts/init.py` | open().read() 统一改 with open()（-W error 下 19 个 PytestUnraisableExceptionWarning，pre-existing 模式） | 代码质量 | DONE | 2026-07-03 21:10 | sdflow-rebrand | sdflow-init-hardening |
| T23 | `setup.sh Windows copy 分支` | Windows 分支（IS_WINDOWS=1）marker 换写 .sdflow-skills 无直接测试（沙箱恒 Unix；名单判定函数已双向测试） | 代码质量 | PROPOSED | 2026-07-03 21:10 | sdflow-rebrand | sdflow-rebrand |
| T24 | `setup.sh install_into 软链分支` | install_into 对既有软链零所有权校验——同名异物软链被 ln -snf 无声覆盖（已复现）；需专门设计「何为自属目标」再修，与 T18（可见性）分立 | 基础设施 | PROPOSED | 2026-07-03 21:29 | sdflow-rebrand | sdflow-rebrand |
| T25 | `sdflow-spec-review/SKILL.md Step1 + sdflow-code-review Step1（gstack/review 同病）` | autoplan/gstack-review 原生流程被「子代理读 SKILL.md 模拟执行」替换——须修复为真实调用，或把模拟显式定义为降级模式并标注 | 代码质量 | DONE | 2026-07-03 23:57 | sdflow-ship | sdflow-ship |
| T26 | `sdflow-ship/SKILL.md` | 熔断重试计数脚本化方案探索（gate 零副作用约束下的计数下沉） | 功能增强 | DONE | 2026-07-04 02:40 | sdflow-ship | sdflow-ship |
| T27 | `openspec/workflow + resolve-workflow.sh` | workflow 规则在项目 openspec(/workflow) 下提供可参考副本（便于 @ 引用与复制 prompt）——须先消解与「仓内不留规则副本防 pin 遮蔽」拍板的冲突 | 基础设施 | PROPOSED | 2026-07-04 09:57 | minimize-repo-footprint | rec2-obs-readability |
| T28 | `sdflow-init/assets/workflow/workflow.md + 各编排 skill 收尾段` | 每阶段结束后按 workflow 给出下一阶段提示，并附完整可复制 prompt（用户可参考/复制，或选择后直接按该 prompt 执行） | 功能增强 | PROPOSED | 2026-07-04 10:51 | cross-model-outside-voice | rec2-obs-readability |
| T29 | `workflow 度量（ship_gate/checkpoint 时间戳 + 各编排 skill 报告）` | 记录每个 agent 花费时长 + workflow 各子阶段时长（spec-review、ship 的分层子阶段）+ 各阶段汇总 | 可观测性 | PROPOSED | 2026-07-04 11:57 | cross-model-outside-voice | rec2-obs-readability |
| T30 | `sdflow-init/assets/hack/outside-voice.sh + tests` | helper 健壮性小项×4（final review triage record-as-debt）：OV_MAX 非数值校验 / flag 缺值 shift 2 死循环护栏 / mktemp 返回值检查 / fake timeout stub 时序依赖 | 代码质量 | PROPOSED | 2026-07-04 12:46 | cross-model-outside-voice | cross-model-outside-voice |
| T31 | `outside-voice.sh + 两 SKILL 协议节 + setup.sh` | voice 层后续硬化池（code-review 多镜确认、本轮未修的 defer 项 ×8） | 代码质量 | PROPOSED | 2026-07-04 13:35 | cross-model-outside-voice | cross-model-outside-voice |
| T32 | `ship_gate.py` | 完成判据 checkpoint 任务号加 change 命名空间 | 代码质量 | DONE | 2026-07-04 16:50 | ship-gate-hardening | ship-gate-hardening |
| T33 | `ship_gate.py` | 新鲜度可选纳入工作树 dirty 状态 | 代码质量 | WONTDO | 2026-07-04 16:50 | ship-gate-hardening | ship-gate-hardening |
| T34 | `ship_gate.py` | 复选框辅通道按 Task 分段绑定 | 代码质量 | DONE | 2026-07-04 16:50 | ship-gate-hardening | ship-gate-hardening |
| T35 | `ship_gate.py` | 新鲜度可选纳入工作树 dirty 状态(T33 停置延续) | 代码质量 | DONE | 2026-07-04 20:22 | ship-gate-hardening-2 | ship-gate-hardening-2 |
| T36 | `sdflow-init/assets/workflow/workflow.md + sdflow-ship/SKILL.md` | checkpoint 派发指令文案收敛为单一真相源(broad-F2) | 代码质量 | DONE | 2026-07-04 20:22 | ship-gate-hardening-2 | ship-gate-hardening-2 |
| T37 | `openspec/changes/checkpoint-tag-single-source/specs/spec-workflow/spec.md:12` | delta spec Scenario prose 复述标签形状(<change>:task<号>-<slug>)——又一份需人工与 workflow.md/SKILL.md 保持一致的 doc 副本(M3 轻回声) | 代码质量 | DONE | 2026-07-05 09:55 | checkpoint-tag-single-source | checkpoint-tag-single-source |
| T38 | `openspec/changes/checkpoint-tag-single-source/specs/spec-workflow/spec.md:12` | spec Scenario 用词 <当前change> 易被误读为须用本 change 真实 slug,实现实际用任意占位 demo | 代码质量 | DONE | 2026-07-05 09:55 | checkpoint-tag-single-source | checkpoint-tag-single-source |
| T39 | `sdflow-ship/tests/test_producer_parser_contract.py:19` | 集成测试 run_producer 造文件名含冒号(f-demo:task1-slug.txt),NTFS 非法——Unix 跑绿,Windows CI 会误红 | 代码质量 | DONE | 2026-07-05 09:55 | checkpoint-tag-single-source |  |
| T40 | `sdflow-ship/tests/test_producer_parser_contract.py:27` | producer→parser 集成正例仅用单数字任务号(1),未覆盖多位数(如 12)group(2) 边界 | 代码质量 | DONE | 2026-07-05 09:55 | checkpoint-tag-single-source |  |
| T41 | `sdflow-spec-review/SKILL.md + sdflow-code-review/SKILL.md` | 评审结束输出一条可点击链接(报告路径→file:// 或网页视图)，点开即看结果，免手动找 report | 功能增强 | PROPOSED | 2026-07-05 11:26 | gate-anchor-line-scoped | rec2-obs-readability |
| T42 | `workflow bundle: generation-process.md / design-diagrams.md / 产物模版` | 文档除条目化描述(主给 AI/程序)外，尽量用多图+多表从多角度描述(给人看)；考虑人读层/机读层分离；不拘一问题一图表 | 功能增强 | PROPOSED | 2026-07-05 12:07 | gate-anchor-line-scoped | rec2-obs-readability |
| T43 | `sdflow-code-review/SKILL.md + sdflow-spec-review/SKILL.md（报告格式展示块）` | producer 模板展示的机器锚收紧为独占 bare line（现带反引号/同行尾注）——与真产报告一致，防未来报告照抄模板致 gate 行锚定不认锚（code-voice OV-code-1） | 代码质量 | DONE | 2026-07-05 13:41 | gate-anchor-line-scoped | gate-anchor-line-scoped |
| T44 | `sdflow-init/scripts/init.py + setup.sh` | 退役 hook 自愈(retire_hooks)未接进 toolkit 标准更新路径(setup.sh/README) | 基础设施 | DONE | 2026-07-05 16:09 | drop-per-dir-review-stub | drop-per-dir-review-stub |
| T45 | `sdflow-init/assets/workflow/tools/engine.js` | 根查看器缺 scoped 深链——恢复 /review.html#/changes/X/ hash 路由首屏 | 功能增强 | DONE | 2026-07-05 16:09 | drop-per-dir-review-stub | drop-per-dir-review-stub |
| T46 | `workflow bundle: spec-checklists/spec-quality-base.md(BASE-12) + workflow.md(G2) + sdflow-code-review/SKILL.md(Step4)` | 把「三镜决策框架(系统/用户/开发循环+定主次)」焊进 workflow，让决策分析不依赖私有记忆、跨 session/子代理稳定生效 | 功能增强 | DONE | 2026-07-05 17:26 | - |  |
| T47 | `sdflow-init/assets/workflow/tools/engine.js` | engine.js 深链逻辑零单测——抽 resolveInitialDir + bootstrap 分派为可注入 mock 的纯函数补单测(hash 边界/404回落/notice) | 代码质量 | PROPOSED | 2026-07-05 19:14 | review-tool-followups | review-tool-followups |
| T48 | `setup.sh + 全仓 python 调用点` | python3/python 探测无版本校验——可能落 Python2 致 init.py f-string 解析期报错；全仓(sdflow-*/init.py)系统性缺 sys.version_info 守卫 | 基础设施 | DONE | 2026-07-05 19:14 | review-tool-followups | sdflow-init-hardening |
| T49 | `sdflow-init/scripts/init.py:_deregister_hook_in_settings` | settings.json 原子写仍有并发 lost-update TOCTOU 窗口(两进程各基于旧内容读→写→os.replace，一次修改被静默覆盖) | 代码质量 | DONE | 2026-07-05 19:14 | review-tool-followups | sdflow-init-hardening |
| T50 | `sdflow-spec-review/SKILL.md 决策登记区 ASCII 框` | Q1 行加长(+三面后果+主次判定)后超边框宽度，右│视觉参差(cosmetic)；整框加宽须动6行、结构未破不影响语义 | 代码质量 | PROPOSED | 2026-07-05 21:08 | three-lens-decision-framework | rec2-obs-readability |
| T51 | `sdflow-done/SKILL.md commit步 + merge检查` | tracked 非-openspec 改动被 commit 步 git add -u 先提交、绕过 merge 前 untracked 硬检查的"停下问"——需 commit 步暂存策略与 merge 卫生检查对齐(gate-checkpoint-hardening SR-2 缩简版只覆盖 untracked,tracked 一路 defer) | 代码质量 | PROPOSED | 2026-07-05 22:43 | gate-checkpoint-hardening | gate-checkpoint-hardening |
| T52 | `sdflow-done/SKILL.md merge untracked 检查` | merge 前 untracked 检查现为机械"任何 ??→halt 人工triage"(CR-4);精确区分"本 change 新产 vs 既有 debris"需在分支切出点落 untracked baseline 快照再 diff,可减少既有 debris 的误停——脚本化探索 | 功能增强 | PROPOSED | 2026-07-05 23:15 | gate-checkpoint-hardening | gate-checkpoint-hardening |
| T53 | `workflow 度量 + sdflow-grill/spec-review/code-review` | 建立 review 价值度量机制:量化每轮评审(grill/spec-review/code-review 及各镜/层/codex-vs-claude)的价值——findings 产出数·采纳[impl-review-fix]/裁掉/defer 分桶·致命/高/中/低分布·独立(非重复)贡献;评审运行时落度量记录(泛化现有 voice 分桶+10次采纳率复评到全镜);据累积数据数据驱动决定各层/镜/触发条件的必要性(保留/降采样/收紧触发/淘汰低价值镜) | 功能增强 | DONE | 2026-07-05 23:36 | main | rec2-obs-readability |
| T54 | `workflow 度量 / grill amendment 存活率` | grill amendment-下游存活率 度量 | 可观测性 | PROPOSED | 2026-07-06 02:04 | workflow-metrics-loop | workflow-metrics-loop |
| T55 | `lens_metric_aggregate.py` | 聚合器易用性/健壮性观察(code-review X3/X4 defer,低危):glob 空表 vs archive 不存在无法区分;转义引号 site 值截断产生多余分组行(site 不校验已契约注明) | 代码质量 | PROPOSED | 2026-07-06 02:36 | workflow-metrics-loop | workflow-metrics-loop |
| T56 | `trivial_shape.py / workflow-cost-opt Leg1` | 判器残余(F6): tests/ 免多镜仅排 conftest/__init__,未盖 tests/plugins/* 等 import 副作用;更严可限 test_*.py。另 更宽有逻辑面轻量化已证不可做(diff前不可机判/HR-TG语义),留 roadmap design 放弃项 | 代码质量 | OPEN | 2026-07-06 13:44 | adaptive-workflow-routing |  |
| T57 | `workflow/model-tiers` | 档位矩阵新增「升级档」（更高档，延后） | 功能增强 | OPEN | 2026-07-06 15:24 | main |  |
| T58 | `sdflow-retro/lens_metric_aggregate` | fence-aware 只支持反引号 fence，不支持 CommonMark ~~~ tilde fence | 代码质量 | PROPOSED | 2026-07-06 20:16 | sdflow-retro | sdflow-retro |
| T59 | `sdflow-retro/retro_report+lens_metric_aggregate` | ≥10 待复评阈值 10 硬编码两处(surfacing_block + render_table)无共享常量 | 代码质量 | PROPOSED | 2026-07-06 20:16 | sdflow-retro | sdflow-retro |
| T60 | `sdflow-retro/retro_report` | _run_git 不检查 returncode，git 失败与真无提交不可区分 | 可观测性 | PROPOSED | 2026-07-06 20:16 | sdflow-retro | sdflow-retro |
| T61 | `sdflow-retro/retro_report` | build_report/surfacing_block 包 LMA.aggregate 的 except 是死防御(glob 缺目录不抛)+注释误导 | 代码质量 | PROPOSED | 2026-07-06 20:16 | sdflow-retro | sdflow-retro |
| T62 | `sdflow-retro/retro_report._run_git` | T60 留痕在系统性 git 损坏下无节流放大：seed_mass_shas 对每个 sha 调 _run_git，仓库整体损坏时每 commit rc≠0 各写一行 stderr，O(commits) 无去重无节流。低危(仅真故障下噪声非虚警;view-only不中断)。改法:同一 subcmd 失败去重,或 seed 循环 per-sha 失败聚合成一条 | 可观测性 | PROPOSED | 2026-07-06 21:08 | sdflow-retro-cleanup | sdflow-retro-cleanup |
| T63 | `sdflow-init/scripts/init.py:inject/_find_all_marker_lines` | inject 多块收敛须 fence-aware + start/end 配对校验（naive collapse 已回退） | 代码质量 | PROPOSED | 2026-07-06 22:32 | sdflow-init-hardening | sdflow-init-hardening |
| T64 | `sdflow-init/scripts/init.py:_atomic_write_settings` | settings.json 原子写 tmp 改唯一名（tempfile.mkstemp）关闭无锁降级路径撕裂 | 代码质量 | PROPOSED | 2026-07-06 22:32 | sdflow-init-hardening | sdflow-init-hardening |
| T65 | `sdflow-init/assets/workflow/tools/ship_gate.py + 报告模版` | gate 状态锚（家族①）迁 YAML frontmatter，根除 B4/B5 inline 歧义类 | 基础设施 | OPEN | 2026-07-07 09:34 | main |  |
| T66 | `cmd_scan(buglist/todolist) + cmd_batch_rename(issues)` | recorder 效率:cmd_scan 对同批行双切(OV-1 arity+OV-3 dup)可合一次循环; batch rename 跑两次 read_pool(4子进程scan)可优化 | 性能优化 | PROPOSED | 2026-07-07 13:03 | issues-pool-hardening | issues-pool-hardening |
| T67 | `cmd_add id 校验(buglist/todolist)` | 显式id前导零歧义:B007≠B7按字面共存不判重,语义同号两字面ID人工识别混淆(code-review对抗A置信55) | 代码质量 | PROPOSED | 2026-07-07 13:03 | issues-pool-hardening | issues-pool-hardening |
| T68 | `anchor_lint` | load_enums 契约 lens-metric-enums 块内若未来加裸 ``` 行会提前闭合致 EnumsError；当前块内容无裸 fence 未触发，fail-closed 安全侧 | 代码质量 | PROPOSED | 2026-07-07 16:57 | mlh-p2-anchor-lint | mlh-p2-anchor-lint |
| T69 | `sdflow-init/copy_bundle` | 缺 pin 消费仓 update 端到端交叉不变量测试（workflow.md/spec-checklists/code-checklists 原封不动、仅 tools+契约刷新） | 代码质量 | PROPOSED | 2026-07-07 16:57 | mlh-p2-anchor-lint | mlh-p2-anchor-lint |
| T70 | `init.py config-lint` | config_lint 的 _second_level_keys/块扫描仅识别两空格缩进，tab 缩进的 model-tiers 子键隐形→越域非法子键 fail-open 静默通过（对抗A实测复现，边缘 YAML） | 代码质量 | OPEN | 2026-07-07 20:30 | mlh-p3-determ-guards |  |
| T71 | `test_mirror_consistency.py` | _ast_no_doc 对剥 docstring 后空体函数坍塌：两个仅含 docstring 的同名 stub AST 相等→理论假过（当前 11+6 helper 均有真逻辑不可利用，加固可标记空体） | 代码质量 | OPEN | 2026-07-07 20:30 | mlh-p3-determ-guards |  |
| T72 | `issues.py batch lint` | batch 条目整行缺失 优先级:/计划: 字段（非空值而是整行删除）当前不校验（实现有意窄化到值语法层，对抗A确认为文档化边界）——考虑补结构完整性校验抓手改腐坏 | 功能增强 | OPEN | 2026-07-07 20:30 | mlh-p3-determ-guards |  |
| T73 | `anchor_lint.py + init.py config-lint` | metrics.enabled 两校验器均拒绝合法 YAML 行内注释(enabled: true # x)——当前一致的有意严格；若要容忍需两处同步改（防分歧），是设计级决定 | 功能增强 | OPEN | 2026-07-07 20:30 | mlh-p3-determ-guards |  |

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
| 状态 | DONE |

**关联文档**：`openspec/changes/sdflow-rebrand/design.md`

**动机**：幂等下不自然产生，仅手工粘贴畸形态（终审 triage：记债不阻塞）
> 2026-07 状态：PROPOSED → DONE（sdflow-init-hardening: _find_marker_line offset 修 misanchor; 多块 collapse 拆入 T63(fence-aware)）

---

## T22: open().read() 统一改 with open()（-W error 下 19 个 PytestUnraisableExceptionWarning，pre-existing 模式）

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-init/scripts/init.py` |
| 类型 | 代码质量 |
| 状态 | DONE |

**关联文档**：`openspec/changes/sdflow-rebrand/design.md`

**动机**：默认 -q 下 233 passed 无 warning；-W error 加严才暴露；修法机械（终审 triage）
> 2026-07 状态：PROPOSED → DONE（sdflow-init-hardening (merged 0ccf3ce)）

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
| 状态 | DONE |

**关联文档**：`openspec/changes/sdflow-ship/design.md`

**动机**：D5 熔断当前靠主 session prose 计数，弱模型可能忘计或混淆

**思路**：候选：checkpoint 标记 attempt / gate 输出含建议重试上限的结构化提示 / 宿主层计数——均需先解 D1 零副作用与计数落盘的矛盾
> 2026-07 状态：PROPOSED → DONE（gate-checkpoint-hardening (98f10b9)）

---

## T27: workflow 规则在项目 openspec(/workflow) 下提供可参考副本（便于 @ 引用与复制 prompt）——须先消解与「仓内不留规则副本防 pin 遮蔽」拍板的冲突

| 属性 | 值 |
|------|------|
| 模块 | `openspec/workflow + resolve-workflow.sh` |
| 类型 | 基础设施 |
| 状态 | PROPOSED |

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

**〔grill 调研定稿 2026-07-06，workflow-metrics-loop grill 派生 · [grill-amendment]〕**：
- **候选②（duration_ms）作废**——接地证实本 harness 的 Agent 工具只回子代理最终文本、**不暴露结构化 duration_ms**（全仓零捕获），且镜为并行 fan-out 无法按镜隔离墙钟、子代理自报不可靠 → per-镜/per-agent 耗时**无诚实数据源**，砍。原 workflow-metrics-loop change 已据此撤除 dur_s（见其 design ADR-3）。
- **采候选①（checkpoint 时间戳）为唯一数据源**，定标准：
  - **数据源**：`git log --format='%ct %s'` over change 的 checkpoint 序列；步类型解析 tag 前缀（`checkpoint(grill|spec-review|spec-review-autoplan|impl-review)` + `checkpoint(<change>:taskN-slug)` 用 ship_gate `TAG_RE`）。
  - **粒度**：阶段/层（**到不了镜**——同 Q1 因）。故 T29 答「该不该留这**层**」，workflow-metrics 答「该不该留这**镜**」（价值）；两者不同粒度，**不能相除成 per-镜 value/cost 比**。
  - **指标**：per-步类型墙钟 = 相邻 ct 差；聚合 = **N-change 均值**。
  - **人类门剔除**：`checkpoint(grill)` 类 + 报告含 `<!-- ship-gate: design-approved -->` 的区间 → **锚定**（非 subject 文本）单列「人类门时长」，绝不并进层成本。
  - **诚实声明（MUST）**：测的是**墙钟 elapsed 非计算成本**（含会话空闲，git 无法恢复纯计算）；**单 change 数不可信、只信聚合**；离群标记不平均。
  - **进程**：独立 change（数据源=git log，与 workflow-metrics 报告锚聚合器不同源）；归同一 ROADMAP `workflow-metrics-loop` 伞下，日后可共用一张 dashboard（两数据源一表）。

**备注**：内容上属 workflow-metrics-loop scope 的先行需求；提出于 cross-model-outside-voice ship 进行中。〔2026-07-06 更新〕已从 workflow-metrics-loop change 撤出**另立**——该 change 只做价值度量，T29 成本另开，标准见上。

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
| 状态 | DONE |

**关联文档**：`openspec/changes/ship-gate-hardening/design.md`

**动机**：完成锚 checkpoint(task<n>-) 无 change 归属,同分支交错跑两个 change 时同号任务可污染完成集(窗口下界 plan_first_sha 已部分缓解,非彻底)

**思路**：checkpoint 契约加 change slug/trailer 如 checkpoint(<change>:task1-) 或 sdflow-change: trailer,gate 只认当前 change;旧格式歧义时 UNKNOWN

**备注**：ship-gate-hardening 代码审 HR-TG code 镜发现,pre-existing 非本 change 引入
> 2026-07 状态：PROPOSED → DONE（ship-gate-hardening-2(archived 2026-07-04); ship_gate.py:231 [T32]命名组+test_gate_namespace.py）

---

## T33: 新鲜度可选纳入工作树 dirty 状态

| 属性 | 值 |
|------|------|
| 模块 | `ship_gate.py` |
| 类型 | 代码质量 |
| 状态 | WONTDO |

**关联文档**：`openspec/changes/ship-gate-hardening/design.md`

**动机**：is_stale 只看已提交盘面,verify/code-review 后工作树 staged/unstaged/untracked 的非 openspec 代码改动不触发 RERUN_STALE

**思路**：code scope 可选追加 git status --porcelain 分类;报告锚后存在 dirty 非 openspec 路径→RERUN_STALE/UNKNOWN。注:与「盘面即状态=committed 产物」设计张力,需先定性

**备注**：HR-TG code 镜发现,pre-existing
> 2026-07 状态：PROPOSED → WONTDO（延续为 T35(ship-gate-hardening-2 批次),同一 dirty 新鲜度想法,闭 T33 避免双计数）

---

## T34: 复选框辅通道按 Task 分段绑定

| 属性 | 值 |
|------|------|
| 模块 | `ship_gate.py` |
| 类型 | 代码质量 |
| 状态 | DONE |

**关联文档**：`openspec/changes/ship-gate-hardening/design.md`

**动机**：checkboxes_all 只看全文有无 - [x]/- [ ],一个全局勾选可放行所有 plan task,未按 ### Task <n>: 分段;与集合归属主锚并存时可能覆盖

**思路**：按 ### Task <n>: 分段解析,要求每个计划内 task 段都有完成标记,否则 checkbox fallback 不覆盖 checkpoint 集合归属

**备注**：HR-TG code 镜发现,pre-existing
> 2026-07 状态：PROPOSED → DONE（ship-gate-hardening-2(archived 2026-07-04); ship_gate.py:332 checkbox_done_ids/:345 plan_has_duplicate_task [T34]）

---

## T35: 新鲜度可选纳入工作树 dirty 状态(T33 停置延续)

| 属性 | 值 |
|------|------|
| 模块 | `ship_gate.py` |
| 类型 | 代码质量 |
| 状态 | DONE |

**关联文档**：`openspec/changes/ship-gate-hardening-2/design.md`

**动机**：is_stale 只看已提交盘面,verify/code-review 后工作树里的新代码不触发 RERUN_STALE

**思路**：先 grill 拍板 gate 该不该越过 committed 边界(与盘面即状态张力),再决定加 git status --porcelain 分类兜底

**备注**：design 已停置,需独立 change
> 2026-07 状态：PROPOSED → DONE（gate-checkpoint-hardening (98f10b9)）

---

## T36: checkpoint 派发指令文案收敛为单一真相源(broad-F2)

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-init/assets/workflow/workflow.md + sdflow-ship/SKILL.md` |
| 类型 | 代码质量 |
| 状态 | DONE |

**关联文档**：`openspec/changes/ship-gate-hardening-2/design.md`

**动机**：同一条 checkpoint-commit.sh 派发约定硬编码在 workflow.md 权威源+SKILL.md 两处独立维护,本轮实证会漏改一处(G1)

**思路**：workflow.md 权威定义,SKILL.md 用引用/参数化复述而非独立文案
> 2026-07 状态：PROPOSED → DONE（gate-checkpoint-hardening (98f10b9)）

---

## T37: delta spec Scenario prose 复述标签形状(<change>:task<号>-<slug>)——又一份需人工与 workflow.md/SKILL.md 保持一致的 doc 副本(M3 轻回声)

| 属性 | 值 |
|------|------|
| 模块 | `openspec/changes/checkpoint-tag-single-source/specs/spec-workflow/spec.md:12` |
| 类型 | 代码质量 |
| 状态 | DONE |

**关联文档**：`openspec/changes/checkpoint-tag-single-source/design.md`

**备注**：DF4(spec-review Round2)。轻于原 M3(测试已改真实脚本非抠文本),但仍是独立 doc 副本,Risks 未披露。择机收敛或至少披露。
> 2026-07 状态：PROPOSED → DONE（gate-checkpoint-hardening (98f10b9)）

---

## T38: spec Scenario 用词 <当前change> 易被误读为须用本 change 真实 slug,实现实际用任意占位 demo

| 属性 | 值 |
|------|------|
| 模块 | `openspec/changes/checkpoint-tag-single-source/specs/spec-workflow/spec.md:12` |
| 类型 | 代码质量 |
| 状态 | DONE |

**关联文档**：`openspec/changes/checkpoint-tag-single-source/design.md`

**备注**：DF5(spec-review Round2)。规范文本精确性,已实现故未爆雷。可改为明确占位任意 ns。
> 2026-07 状态：PROPOSED → DONE（gate-checkpoint-hardening (98f10b9)）

---

## T39: 集成测试 run_producer 造文件名含冒号(f-demo:task1-slug.txt),NTFS 非法——Unix 跑绿,Windows CI 会误红

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-ship/tests/test_producer_parser_contract.py:19` |
| 类型 | 代码质量 |
| 状态 | DONE |

**关联文档**：`openspec/changes/checkpoint-tag-single-source/design.md`

**备注**：DF6(spec-review Round2)。本测试层 Unix 取向,极低概率。若上 Windows CI 改固定占位文件名(文件名与契约无关,只需 porcelain 非空)。
> 2026-07 状态：OPEN → DONE（checkpoint-tag-single-source (code-review [impl-review-fix]: run_producer 改固定文件名 change.txt)）

---

## T40: producer→parser 集成正例仅用单数字任务号(1),未覆盖多位数(如 12)group(2) 边界

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-ship/tests/test_producer_parser_contract.py:27` |
| 类型 | 代码质量 |
| 状态 | DONE |

**关联文档**：`openspec/changes/checkpoint-tag-single-source/design.md`

**备注**：DF7(spec-review Round2)。非本 change 引入的新缺口,补一例多位数号增强边界覆盖。
> 2026-07 状态：OPEN → DONE（checkpoint-tag-single-source (code-review [impl-review-fix]: 加 test_kebab_namespace_multidigit_captures 覆盖多位数号)）

---

## T46: 把「三镜决策框架(系统/用户/开发循环+定主次)」焊进 workflow，让决策分析不依赖私有记忆、跨 session/子代理稳定生效

| 属性 | 值 |
|------|------|
| 模块 | `workflow bundle: spec-checklists/spec-quality-base.md(BASE-12) + workflow.md(G2) + sdflow-code-review/SKILL.md(Step4)` |
| 类型 | 功能增强 |
| 状态 | DONE |

**动机**：workflow bundle 是发布给其它项目/用户的产品，必须自包含，不能依赖某人的私有记忆(decision-three-lens-framework.md 是行为层真相源，但子代理跑评审时够不着、其它 checkout 也没有)。T46 = 把框架从私有记忆搬进发布的 workflow。

**思路**：grill 定稿五决策(2026-07-05)：①【形态×落点】增强现有 BASE-12「备选方案记录/ADR」原地改，不新增独立编号项(避双源/规则重叠)。②【强度×深度】分两层——行为层(记忆)每个决策都用；书面层(BASE-12)只在 TG-23(≥2合理方案/非显然设计)触发时 MUST 写三镜+主次，不下沉到琐碎决策。③【落点·候选③】除 BASE-12 外，也把三镜编码进 workflow.md G2 决策登记区格式：现「选项+推荐+两方后果」→「选项+推荐+三面后果(系统/用户/开发循环)+主次判定」。④【候选③另半】code-review SKILL.md Step4「≥2方案有把握自动选推荐(记理由)」的记理由 → 按三镜+主次，与 spec-review 登记一致、产品自包含。⑤【进程】走独立 OpenSpec change(带 spec delta 防漂移)，不裸改源；grill 成果直接喂四件套。三处落点：BASE-12 + workflow.md G2 + sdflow-code-review/SKILL.md Step4。

**备注**：触及的 spec 需求(delta 要改)：openspec/specs/spec-workflow/spec.md 第18行「评审决策登记进报告」(『各分支后果』→『三面后果+主次』)、第432/436行「outside-voice tension」(『两方观点+推荐+后果』同步)、BASE-12 质量门(标R,评审项)。真相源=记忆 decision-three-lens-framework.md。参考样例=review-tool-followups 的 ADR-0/1/2(已按三镜回填)。排序：review-tool-followups 先跑完再开本 change(用户拍板)。BASE-12 现文：『2-3方案对比(含最小可行+理想架构)；关键决策按ADR结构落盘：背景/候选方案/决策/理由/当前方案代价』——三镜挂进『候选方案』评估法+『理由』加主次判定行。
> 2026-07 状态：OPEN → DONE（three-lens-decision-framework (5de9ede)）

---

## T47: engine.js 深链逻辑零单测——抽 resolveInitialDir + bootstrap 分派为可注入 mock 的纯函数补单测(hash 边界/404回落/notice)

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-init/assets/workflow/tools/engine.js` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/review-tool-followups/design.md`

**备注**：code-review FB-1。现靠 verify-manual-t45 浏览器四态实测兜，无回归网。抽出 resolveInitialDir(已具名)用 URL/window stub 单测同源/跨源/畸形/空 hash；bootstrap 分支注入 loadDir/loadDoc/content mock 断言 404→INDEX+notice 恰一次。

---

## T48: python3/python 探测无版本校验——可能落 Python2 致 init.py f-string 解析期报错；全仓(sdflow-*/init.py)系统性缺 sys.version_info 守卫

| 属性 | 值 |
|------|------|
| 模块 | `setup.sh + 全仓 python 调用点` |
| 类型 | 基础设施 |
| 状态 | DONE |

**关联文档**：`openspec/changes/review-tool-followups/design.md`

**备注**：code-review FB-5。非本 change 引入(既有系统性缺口)，故未在本 change 修。建议统一加最小版本守卫或探测 python3.x。
> 2026-07 状态：PROPOSED → DONE（sdflow-init-hardening (merged 0ccf3ce)）

---

## T49: settings.json 原子写仍有并发 lost-update TOCTOU 窗口(两进程各基于旧内容读→写→os.replace，一次修改被静默覆盖)

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-init/scripts/init.py:_deregister_hook_in_settings` |
| 类型 | 代码质量 |
| 状态 | DONE |

**关联文档**：`openspec/changes/review-tool-followups/design.md`

**备注**：code-review CV-2(置信40低)。temp+os.replace 已解撕裂JSON(本次目标)；lost-update 因 RETIRED 幂等下次重收敛、低影响。真解需文件锁，暂记不修。
> 2026-07 状态：PROPOSED → DONE（sdflow-init-hardening (merged 0ccf3ce)）

---

## T44: 退役 hook 自愈(retire_hooks)未接进 toolkit 标准更新路径(setup.sh/README)

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-init/scripts/init.py + setup.sh` |
| 类型 | 基础设施 |
| 状态 | DONE |

> 2026-07 状态：PROPOSED → DONE（review-tool-followups）

---

## T45: 根查看器缺 scoped 深链——恢复 /review.html#/changes/X/ hash 路由首屏

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-init/assets/workflow/tools/engine.js` |
| 类型 | 功能增强 |
| 状态 | DONE |

> 2026-07 状态：PROPOSED → DONE（review-tool-followups）

---

## T50: Q1 行加长(+三面后果+主次判定)后超边框宽度，右│视觉参差(cosmetic)；整框加宽须动6行、结构未破不影响语义

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-spec-review/SKILL.md 决策登记区 ASCII 框` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/three-lens-decision-framework/design.md`

**动机**：code-review F5：cosmetic 对齐，不成比例故 defer

**思路**：缩短 Q1 行文案或整框加宽6行，二选一

---

## T43: producer 模板展示的机器锚收紧为独占 bare line（现带反引号/同行尾注）——与真产报告一致，防未来报告照抄模板致 gate 行锚定不认锚（code-voice OV-code-1）

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-code-review/SKILL.md + sdflow-spec-review/SKILL.md（报告格式展示块）` |
| 类型 | 代码质量 |
| 状态 | DONE |

> 2026-07 状态：PROPOSED → DONE（gate-checkpoint-hardening (98f10b9)）

---

## T54: grill amendment-下游存活率 度量

| 属性 | 值 |
|------|------|
| 模块 | `workflow 度量 / grill amendment 存活率` |
| 类型 | 可观测性 |
| 状态 | PROPOSED |

**关联文档**：无（本项为独立探索）

**动机**：workflow-metrics-loop 初期设计（T29 为 checkpoint 成本度量）后续需评估 grill 层的价值。T29 之 grill amendment 派生项：候选指标是「[grill-amendment] 标签下游被采纳的条数」，但尚无口径定义（什么算"采纳"、用什么 ground truth、如何计数）、无数据源（[grill-amendment] tag 当前仅标记 defer item，未建 ID/追踪链路）。

**思路**：
- 问题界定：「口径未定义」——[grill-amendment] 标签的下游物料（buglist/todolist defer item、spec amendment）无统一 ID scheme 与链接机制，原始记录无追踪链路（现仅存 change 报告内的 deferred items 列表）。
- 数据悬而未决：裸数「amendment 条数」是误导指标（无法按采纳度/质量分层）。真实度量需先定义「价值」口径（采纳率、致命/高/中/低分布、独立贡献vs重复、与别镜的去重）。
- 归属：本条非本 change（workflow-metrics-loop）的工作，本 change 做的是价值度量 + 各镜产出聚合（成本维度是 T29 另立）。grill 存活率/价值度量待独立 change 评估。

**备注**：workflow-metrics-loop 伞下与 T29 并列的伴生项，记录为「后续需单独评估」的问题；优先级低于成本度量，先从数据源（追踪链路）和口径（定义价值）出发评估可行性。

---

## T53: 建立 review 价值度量机制:量化每轮评审(grill/spec-review/code-review 及各镜/层/codex-vs-claude)的价值——findings 产出数·采纳[impl-review-fix]/裁掉/defer 分桶·致命/高/中/低分布·独立(非重复)贡献;评审运行时落度量记录(泛化现有 voice 分桶+10次采纳率复评到全镜);据累积数据数据驱动决定各层/镜/触发条件的必要性(保留/降采样/收紧触发/淘汰低价值镜)

| 属性 | 值 |
|------|------|
| 模块 | `workflow 度量 + sdflow-grill/spec-review/code-review` |
| 类型 | 功能增强 |
| 状态 | DONE |

> 2026-07 状态：PROPOSED → DONE（workflow-metrics-loop (01092c5)）

---

## T57: 档位矩阵新增「升级档」（更高档，延后）

| 属性 | 值 |
|------|------|
| 模块 | `workflow/model-tiers` |
| 类型 | 功能增强 |
| 状态 | OPEN |

**动机**：model-tiers 3档×运行时矩阵之上可能需要一个更高档：超复杂问题升级到 Fable，或主力档动态升级（sonnet 主力→opus 应对超复杂需求）。当前无此需求。

**思路**：触发条件=出现单靠 strong(opus) 仍吃力的超复杂 change，或想让主力 session 跑更省 sonnet、仅超复杂步升 opus 时再设计。

**备注**：来源：explore 2026-07-06 P0+P2 深挖；关联 roadmap workflow-cost-optimization P2 档位矩阵（design D8）。

---

## T58: fence-aware 只支持反引号 fence，不支持 CommonMark ~~~ tilde fence

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-retro/lens_metric_aggregate` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/sdflow-retro/design.md`

**动机**：code-review code-voice F8：_fence_aware_lines 只匹配 ``` 反引号 fence，~~~ 代码块里的示范 lens-metric/hr-tg 锚会被误计入聚合。既有聚合器限制（本 change 迁入前即有），非本 change 引入

**思路**：记录 fence marker 字符+长度，闭合要求同字符且长度足够；补 ~~~ 回归测试。retro 复用 parse_report 故连带受益

**备注**：defer 自 sdflow-retro code-review；既有既存问题非本 change 回归

---

## T59: ≥10 待复评阈值 10 硬编码两处(surfacing_block + render_table)无共享常量

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-retro/retro_report+lens_metric_aggregate` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/sdflow-retro/design.md`

**动机**：code-review 领域镜 F9：与刚 group_key 抽取根治的两处手写漂移同类风险，阈值调整易改一处漏一处致 surfacing/render_table flag 口径不一致

**思路**：抽共享常量如 REVIEW_WINDOW=10 到 lens_metric_aggregate，两处引用

**备注**：低危 defer 自 sdflow-retro code-review

---

## T60: _run_git 不检查 returncode，git 失败与真无提交不可区分

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-retro/retro_report` |
| 类型 | 可观测性 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/sdflow-retro/design.md`

**动机**：code-review 领域镜+对抗镜2 F10：_run_git subprocess check=False，git 报错(权限/损坏仓/未安装)与该路径确 0 提交都产空 stdout，都归边界不可解析，无法诊断区分。设计偏 fail-open 风格

**思路**：可选：检查 returncode 非 0 时区分标记边界解析失败原因(git-error vs no-commits)，或至少 stderr 留痕

**备注**：低危 design-accepted defer 自 sdflow-retro code-review

---

## T61: build_report/surfacing_block 包 LMA.aggregate 的 except 是死防御(glob 缺目录不抛)+注释误导

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-retro/retro_report` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/sdflow-retro/design.md`

**动机**：code-review 对抗镜2 F11：Path.glob 对不存在/不可读目录静默返空不抛，该 try/except 分支不可达；注释描述archive不存在不崩 实际由 glob 行为达成非此 catch，易误导维护者

**思路**：改注释诚实说明，或改用 os.path.isdir 显式判空分支语义更直白

**备注**：极低危 defer 自 sdflow-retro code-review

---

## T13: resolver/setup 测试断言补强：unreadable-pointer 补 stdout 空断言、root-missing 补 stderr 文案断言、--dev+init _die 补 subprocess 测试、setup idempotent 重跑补 hack 脚本/链目标断言

| 属性 | 值 |
|------|------|
| 模块 | `opsx-project-init/tests/` |
| 类型 | 代码质量 |
| 状态 | DONE |

> 2026-07 状态：PROPOSED → DONE（sdflow-init/tests 补断言3子项已修(test_resolve_workflow.py 降级stdout空+--root缺值stderr文案; test_setup_sdflow.py idempotent_rerun 补链目标+hack脚本), pytest 28 passed; 第4子项(--dev _die subprocess)经查已被 test_init.py::test_dev_pointing_elsewhere_dies 覆盖,冗余未做; batch-triage dogfood 唯一候选平改, 详见 consolidation-plan.md §5.4）

---

## T65: gate 状态锚（家族①）迁 YAML frontmatter，根除 B4/B5 inline 歧义类

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-init/assets/workflow/tools/ship_gate.py + 报告模版` |
| 类型 | 基础设施 |
| 状态 | OPEN |

**动机**：B4/B5 同根：ship-gate 状态锚（design-approved/verify=PASS|FAIL/code-review=pass|blocked）inline 嵌在报告正文，逼 gate 用 fence-aware+独占行+line-scoped 一整套解析去区分『真标记 vs 正文提及』。B5 的聚合不变量补丁是在旧架构里绕过，非根治。状态若在 frontmatter（结构化数据），正文再怎么提及锚串都不会被误当标记，整类 bug 从根消失，且可删掉那套解析机器。

**思路**：scope 严格收窄到家族①（gate 状态判据）——家族③逐条 inline tag（[impl-review-fix]/〔TG-N〕/task<N>/item ID，位置相关）和家族④模版槽位占位（<待填>等）明确留 inline，不搬。须评估三处风险：①bundle 爆炸半径（ship_gate.py+报告模版+生产者 SKILL.md 全在 assets/workflow/ 铺下游 → 改权威源+sdflow-init update 回灌所有消费仓，高仪式单开 change，行为面路径硬排除、绝不 fold/sweep）；②LLM 产报告写坏 YAML → safe_load 抛的兜底策略（比缺 inline 锚更糙的失败面）；③57 篇归档报告是 inline 锚 → gate/corpus 的兼容窗口/dual-read。

**备注**：够格作为 workflow-cost-optimization roadmap 的一个阶段（与『评审机器复杂度』直接相关）。动机证据=buglist B4/B5。别在清理惯性里反应式开工——正式评估 ROI（inline 锚这套是否会反复出同类 bug）后再决定做不做。

---

## T1: reindex 回显子进程 scan 的 problems 到 stderr（补齐独立跑 reindex 时表↔块不一致的可见性，D5 承诺）

| 属性 | 值 |
|------|------|
| 模块 | `issues.py` |
| 类型 | 可观测性 |
| 状态 | DONE |

> 2026-07 状态：PROPOSED → DONE（issues-pool-hardening 实现(SDD 10任务+code-review 6 fix), 全仓552 passed）

---

## T2: 字段含 ｜ 破 markdown 表：统一转义或拒绝含 ｜ 的字段（module/summary/批次名等，防位置解析读错列的数据腐蚀，系统性）

| 属性 | 值 |
|------|------|
| 模块 | `recorder` |
| 类型 | 代码质量 |
| 状态 | DONE |

> 2026-07 状态：PROPOSED → DONE（issues-pool-hardening 实现(SDD 10任务+code-review 6 fix), 全仓552 passed）

---

## T3: 加终态集跨脚本一致性守卫测试（issues.py TERMINAL_STATUSES ⊆ 对应 recorder STATUS_CODES，防未来改终态码漂移）

| 属性 | 值 |
|------|------|
| 模块 | `issues.py` |
| 类型 | 代码质量 |
| 状态 | DONE |

> 2026-07 状态：PROPOSED → DONE（issues-pool-hardening 实现(SDD 10任务+code-review 6 fix), 全仓552 passed）

---

## T4: batch add 加 --if-exists skip 幂等选项；batch rename 后自动 reindex（或 SKILL 提示 rename 后跑 reindex）

| 属性 | 值 |
|------|------|
| 模块 | `issues.py` |
| 类型 | 功能增强 |
| 状态 | DONE |

> 2026-07 状态：PROPOSED → DONE（issues-pool-hardening 实现(SDD 10任务+code-review 6 fix), 全仓552 passed）

---

## T5: 补 WONTDO / 0成员人标IN_PROGRESS 分支测试；抽 _find_row_file 消除 triage 与 set-status 定位逻辑重复（4处）

| 属性 | 值 |
|------|------|
| 模块 | `recorder` |
| 类型 | 代码质量 |
| 状态 | DONE |

> 2026-07 状态：PROPOSED → DONE（issues-pool-hardening 实现(SDD 10任务+code-review 6 fix), 全仓552 passed）

---

## T68: load_enums 契约 lens-metric-enums 块内若未来加裸 ``` 行会提前闭合致 EnumsError；当前块内容无裸 fence 未触发，fail-closed 安全侧

| 属性 | 值 |
|------|------|
| 模块 | `anchor_lint` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/mlh-p2-anchor-lint/design.md`

**动机**：code-review 对抗A F12 defer：潜伏、契约受控，加防护属过度工程

**思路**：契约真需嵌 fence 时再处理（如块解析忽略 info-string 非 lens-metric-enums 的 fence）

---

## T69: 缺 pin 消费仓 update 端到端交叉不变量测试（workflow.md/spec-checklists/code-checklists 原封不动、仅 tools+契约刷新）

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-init/copy_bundle` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/mlh-p2-anchor-lint/design.md`

**动机**：code-review 对抗B F13 defer：各组件已单测，端到端组合缺

**思路**：补一条组合测试固化该不变量
