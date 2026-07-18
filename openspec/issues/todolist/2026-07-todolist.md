---
sdflow-issues:
  schema: 1
  pool: todo
  mode: overlay
  items:
    T2: {"module":"`recorder`","summary":"字段含 ｜ 破 markdown 表：统一转义或拒绝含 ｜ 的字段（module/summary/批次名等，防位置解析读错列的数据腐蚀，系统性）","type":"代码质量","status":"DONE","time":"2026-07-03 00:26","change":"issues-pool-batch-mgmt","batch":"issues-pool-hardening"}
    T66: {"module":"`cmd_scan(buglist/todolist) + cmd_batch_rename(issues)`","summary":"recorder 效率:cmd_scan 对同批行双切(OV-1 arity+OV-3 dup)可合一次循环; batch rename 跑两次 read_pool(4子进程scan)可优化","type":"性能优化","status":"DONE","time":"2026-07-07 13:03","change":"issues-pool-hardening","batch":"issues-pool-hardening"}
    T67: {"module":"`cmd_add id 校验(buglist/todolist)`","summary":"显式id前导零歧义:B007≠B7按字面共存不判重,语义同号两字面ID人工识别混淆(code-review对抗A置信55)","type":"代码质量","status":"DONE","time":"2026-07-07 13:03","change":"issues-pool-hardening","batch":"issues-pool-hardening"}
    T85: {"module":"`roadmap mechanical-layer-hardening / recorder`","summary":"P6 recorder 索引→frontmatter（**端态 A 已定 2026-07-08**）：用户拍板根治(YAML 转义使 `｜` 腐蚀类结构上不可能)否决 B(治标·永久守脆弱表·手编辑洞)。约束①历史文档不迁使成本≈P5 dual-read 成熟范式(新写 frontmatter+历史表冻结只读)。实现=改 3 recorder 写路径+consumer dual-read 读+测试套,压轴排 ★P4 后。A 删写侧(`_reject_cell_unsafe`/`_render_item_table`/双写表半场),历史读 `parse_table_rows` 冻结保留。理由全档见 roadmap P6 端态块","type":"基础设施","status":"DONE","time":"2026-07-08 15:55","change":null,"batch":"mlh-p4-target-state"}
    T146: {"module":"`sdflow-skills 工具族`","summary":"扫描-max+1 无锁并发面统一：todolist.py/buglist.py 与 sad_scaffold 锁面方案对齐（O_CREAT+O_EXCL 仓级互斥）","type":"代码质量","status":"DONE","time":"2026-07-12 18:34","change":"add-sdflow-architecture","batch":"add-sdflow-architecture"}
    T153: {"module":"sdflow-buglist/scripts/buglist.py, sdflow-todolist/scripts/todolist.py","summary":"更新 triage mutation docstring，移除已退役表格双写描述，改为 effective ownership、promotion 与 marker history 语义","type":"代码质量","status":"DONE","time":"2026-07-17 12:06","change":"mlh-p6-recorder-frontmatter","batch":null}
    T154: {"module":"sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py","summary":"actual Windows local-disk smoke 未执行验证（SW-RI-2 recorder lock 兼容目标，deferred）","type":"基础设施","status":"DONE","time":"2026-07-17 16:14","change":"mlh-p6-recorder-frontmatter","batch":null}
    T155: {"module":".github/workflows/（全仓 -W error CI 门）","summary":"全仓 pytest -W error 常态化为持久 CI 守卫（防未来再引入未关闭文件/ResourceWarning 类存量债）","type":"基础设施","status":"OPEN","time":"2026-07-17 16:22","change":"mlh-p6-recorder-frontmatter","batch":null}
    T156: {"module":"sdflow-devenv（配 CI 载体层：SKILL.md + references/testing-framework.md）","summary":"sdflow-devenv 配 CI 的 P2 决策示范清一色 GitHub Actions、且未显式化「硬门/软门」降级边界——对「不管什么项目都能配」的承诺留了平台假设漏洞（用 workflow 的消费仓不一定在 GitHub）","type":"功能增强","status":"OPEN","time":"2026-07-17 19:53","change":"-","batch":null}
    T157: {"module":"openspec/changes/async-outside-voice","summary":"proposal.md:27 仍写旧 .outside-voice/<site>-context.md 形态，与 design/tasks 的 per-run 口径分叉；实现期改四件套触设计门失鲜，须在 archive 阶段一并校正","type":"代码质量","status":"OPEN","time":"2026-07-18 17:08","change":"async-outside-voice","batch":null}
    T158: {"module":"sdflow-spec-review + sdflow-code-review","summary":"run-id 新鲜度可机械化：manifest 存在性是确定性信号，宜加 anchor_lint 家族核而非永久留诚实边界","type":"基础设施","status":"OPEN","time":"2026-07-18 17:08","change":"async-outside-voice","batch":null}
    T159: {"module":"sdflow-spec-review + sdflow-code-review","summary":"协议节 HELPER=~/.sdflow/hack/outside-voice.sh 同属「shell 变量不跨调用存活」失效类，宜改字面路径","type":"代码质量","status":"OPEN","time":"2026-07-18 17:30","change":"async-outside-voice","batch":null}
    T160: {"module":"openspec/changes/async-outside-voice","summary":"3600 上界依据应回写 design ADR-3 免二源；DOC-1 理由入 SKILL 正文一条待设计门拍板","type":"代码质量","status":"OPEN","time":"2026-07-18 17:43","change":"async-outside-voice","batch":null}
    T161: {"module":"sdflow-spec-review + sdflow-code-review","summary":"等值门只覆盖 marker 段；圈外 preflight/fallback/锚行段两层也高度相似但漂了不会红","type":"基础设施","status":"OPEN","time":"2026-07-18 18:01","change":"async-outside-voice","batch":null}
    T162: {"module":"sdflow-spec-review / sdflow-code-review（outside-voice 调度层）","summary":"Codex 宿主方向的跨模型 voice efficacy=0：架构性无法离开关键路径，待 codex deferred_executor 稳定或外部 claude daemon 方案再议","type":"功能增强","status":"OPEN","time":"2026-07-18 18:46","change":"async-outside-voice","batch":null}
    T163: {"module":"sdflow-spec-review / sdflow-code-review + hack/check_async_branch_parity.py","summary":"async host 调度段的 DRY 全抽取：把 marker 段抽成单一源注入两 SKILL，替代当前「两份副本 + 机械等值门」","type":"代码质量","status":"OPEN","time":"2026-07-18 18:46","change":"async-outside-voice","batch":null}
    T164: {"module":"sdflow-spec-review / sdflow-code-review 的 async 调度段 ④ 命令形态（context 路径拼接）","summary":"outside-voice exec 的 --context-file 路径直接拼进 shell 命令且未加引号：路径含空格/shell 元字符时会参数拆分或执行非预期命令（跨模型 voice 独立提出，Task 5 报告 §10 第 2 条，本票未处理）","type":"基础设施","status":"OPEN","time":"2026-07-18 19:34","change":"async-outside-voice","batch":null}
    T165: {"module":"openspec/changes/async-outside-voice/specs（R1 Scenario 1）+ 两评审 SKILL 的 async 调度段","summary":"R1 Scenario 1 的 WHEN（voice 时长 > 外层同步窗口）在本 change 全程未被满足 ⇒ async 的收益面未获端到端实证；补证需要一次 voice 真实耗时 > 300s 的评审跑动","type":"基础设施","status":"OPEN","time":"2026-07-18 19:35","change":"async-outside-voice","batch":null}
    T166: {"module":"hack/check_async_branch_parity.py","summary":"end marker 边界未与 start 侧对称硬化；且尝试硬化时遇到无法解释的 extract 行为矛盾，需专门查","type":"代码质量","status":"OPEN","time":"2026-07-18 20:15","change":"async-outside-voice","batch":null}
    T167: {"module":"openspec/changes/async-outside-voice","summary":"【archive 阶段 MUST 做】四件套仍描述旧协议（裸哨兵/单条件 async），与代码审后的实现不自洽——delta spec 必须同步","type":"代码质量","status":"OPEN","time":"2026-07-18 20:24","change":"async-outside-voice","batch":null}
---
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
| T17 | `opsx-maintain/SKILL.md + init.py` | 陈旧遮蔽判据两处（RULE_MARKERS 常量 vs SKILL prose 复述）无同步机制，改常量会漂——考虑 opsx-maintain 兜底扫描改调脚本 | 基础设施 | DONE | 2026-07-03 16:01 | minimize-repo-footprint | minimize-repo-footprint |
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
| T58 | `sdflow-retro/lens_metric_aggregate` | fence-aware 只支持反引号 fence，不支持 CommonMark ~~~ tilde fence | 代码质量 | DONE | 2026-07-06 20:16 | sdflow-retro | sdflow-retro |
| T59 | `sdflow-retro/retro_report+lens_metric_aggregate` | ≥10 待复评阈值 10 硬编码两处(surfacing_block + render_table)无共享常量 | 代码质量 | DONE | 2026-07-06 20:16 | sdflow-retro | sdflow-retro |
| T60 | `sdflow-retro/retro_report` | _run_git 不检查 returncode，git 失败与真无提交不可区分 | 可观测性 | DONE | 2026-07-06 20:16 | sdflow-retro | sdflow-retro |
| T61 | `sdflow-retro/retro_report` | build_report/surfacing_block 包 LMA.aggregate 的 except 是死防御(glob 缺目录不抛)+注释误导 | 代码质量 | DONE | 2026-07-06 20:16 | sdflow-retro | sdflow-retro |
| T62 | `sdflow-retro/retro_report._run_git` | T60 留痕在系统性 git 损坏下无节流放大：seed_mass_shas 对每个 sha 调 _run_git，仓库整体损坏时每 commit rc≠0 各写一行 stderr，O(commits) 无去重无节流。低危(仅真故障下噪声非虚警;view-only不中断)。改法:同一 subcmd 失败去重,或 seed 循环 per-sha 失败聚合成一条 | 可观测性 | PROPOSED | 2026-07-06 21:08 | sdflow-retro-cleanup | sdflow-retro-cleanup |
| T63 | `sdflow-init/scripts/init.py:inject/_find_all_marker_lines` | inject 多块收敛须 fence-aware + start/end 配对校验（naive collapse 已回退） | 代码质量 | PROPOSED | 2026-07-06 22:32 | sdflow-init-hardening | sdflow-init-hardening |
| T64 | `sdflow-init/scripts/init.py:_atomic_write_settings` | settings.json 原子写 tmp 改唯一名（tempfile.mkstemp）关闭无锁降级路径撕裂 | 代码质量 | PROPOSED | 2026-07-06 22:32 | sdflow-init-hardening | sdflow-init-hardening |
| T65 | `sdflow-init/assets/workflow/tools/ship_gate.py + 报告模版` | gate 状态锚（家族①）迁 YAML frontmatter，根除 B4/B5 inline 歧义类 | 基础设施 | DONE | 2026-07-07 09:34 | main |  |
| T66 | `cmd_scan(buglist/todolist) + cmd_batch_rename(issues)` | recorder 效率:cmd_scan 对同批行双切(OV-1 arity+OV-3 dup)可合一次循环; batch rename 跑两次 read_pool(4子进程scan)可优化 | 性能优化 | PROPOSED | 2026-07-07 13:03 | issues-pool-hardening | issues-pool-hardening |
| T67 | `cmd_add id 校验(buglist/todolist)` | 显式id前导零歧义:B007≠B7按字面共存不判重,语义同号两字面ID人工识别混淆(code-review对抗A置信55) | 代码质量 | PROPOSED | 2026-07-07 13:03 | issues-pool-hardening | issues-pool-hardening |
| T68 | `anchor_lint` | load_enums 契约 lens-metric-enums 块内若未来加裸 ``` 行会提前闭合致 EnumsError；当前块内容无裸 fence 未触发，fail-closed 安全侧 | 代码质量 | PROPOSED | 2026-07-07 16:57 | mlh-p2-anchor-lint | mlh-p2-anchor-lint |
| T69 | `sdflow-init/copy_bundle` | 缺 pin 消费仓 update 端到端交叉不变量测试（workflow.md/spec-checklists/code-checklists 原封不动、仅 tools+契约刷新） | 代码质量 | PROPOSED | 2026-07-07 16:57 | mlh-p2-anchor-lint | mlh-p2-anchor-lint |
| T70 | `init.py config-lint` | config_lint 的 _second_level_keys/块扫描仅识别两空格缩进，tab 缩进的 model-tiers 子键隐形→越域非法子键 fail-open 静默通过（对抗A实测复现，边缘 YAML） | 代码质量 | PROPOSED | 2026-07-07 20:30 | mlh-p3-determ-guards | mlh-p3-determ-guards |
| T71 | `test_mirror_consistency.py` | _ast_no_doc 对剥 docstring 后空体函数坍塌：两个仅含 docstring 的同名 stub AST 相等→理论假过（当前 11+6 helper 均有真逻辑不可利用，加固可标记空体） | 代码质量 | PROPOSED | 2026-07-07 20:30 | mlh-p3-determ-guards | mlh-p3-determ-guards |
| T72 | `issues.py batch lint` | batch 条目整行缺失 优先级:/计划: 字段（非空值而是整行删除）当前不校验（实现有意窄化到值语法层，对抗A确认为文档化边界）——考虑补结构完整性校验抓手改腐坏 | 功能增强 | PROPOSED | 2026-07-07 20:30 | mlh-p3-determ-guards | mlh-p3-determ-guards |
| T73 | `anchor_lint.py + init.py config-lint` | metrics.enabled 两校验器均拒绝合法 YAML 行内注释(enabled: true # x)——当前一致的有意严格；若要容忍需两处同步改（防分歧），是设计级决定 | 功能增强 | PROPOSED | 2026-07-07 20:30 | mlh-p3-determ-guards | mlh-p3-determ-guards |
| T74 | `sdflow-ship` | ship_gate parser 裸---首行(无闭合)误判 unterminated 致 UNKNOWN | 代码质量 | DONE | 2026-07-08 00:34 | mlh-p5-gate-frontmatter | mlh-p5-gate-frontmatter |
| T75 | `sdflow-ship` | ship_gate 清理 live inline 死代码 anchors_in/pick_exclusive/ANCHOR_DESIGN/ANCHOR_CR_* | 代码质量 | DONE | 2026-07-08 00:34 | mlh-p5-gate-frontmatter | mlh-p5-gate-frontmatter |
| T76 | `ship_gate.py archived_verify_state` | 归档杂交盲区硬化后续（设计门已接受净负、登记为已知盲区）：冷代码审对抗镜给出比「仅手工伪造」更锋利的可达性论证——迁移半成品编辑残留独占行 inline PASS 锚、自指文档独占行引用（呼应 gate-substring-dogfood 自指坑）；建议未来加**非语义** lint/监控扫「归档 verify-report 首行 --- 无闭合」形态告警（不改 parser 语义、不重开设计门 adr/0004），据此复评「给归档侧特殊 fail-safe」ROI（design L121 当前选①绝） | 基础设施 | WONTDO | 2026-07-08 13:10 | mlh-p5-parser-cleanup | mechanical-layer-hardening |
| T77 | `openspec/specs/spec-workflow spec.md` | 「过渡期 live 未迁 producer 回退 inline」Scenario 迁移窗已闭（T75 删净 live inline 死码后 live 恒只读 frontmatter）——宜在未来 spec 维护中标为历史或收敛该 Scenario；其终态子句「退役后 live MUST 只读 frontmatter」已 governing、与代码无活跃冲突，纯整洁性（归档 dual-read 是另一独立 Scenario、正确保留） | 代码质量 | OPEN | 2026-07-08 13:10 | mlh-p5-parser-cleanup | mechanical-layer-hardening |
| T78 | `sdflow-code-review/spec-review SKILL + lens_metric_emit.py(新)` | P4·4.C lens-metric 数值一致性从模型手数下沉为脚本归约：吃已判结构化 findings(带命中镜集+裁决+sev)→机械归约计数+锚行；去重/对抗裁决留模型。闭合 requirements §1.2 痛点#2『手数信任边界』、adr/0006 硬约束——目标态该做(原按快照压为按需,已翻案) | 代码质量 | DONE | 2026-07-08 15:55 | - | mlh-p4-target-state |
| T79 | `sdflow-maintain + maintain_scan.py(新)` | P4·4.B maintain INDEX↔文件系统 set-diff 只读报告脚本化(+CLAUDE.md 过时引用+bundle 陈旧告警)；归哪组/是否修留人。纯机械集合求差、每次 maintain 都跑、dogfood 可测——目标态该做 | 代码质量 | DONE | 2026-07-08 15:55 | - | mlh-p4-target-state |
| T80 | `两审 outside-voice 小校验器(新)` | P4·4.D.1 outside-voice 复用守卫脚本化：锚 mode+时间戳+结构三判→reason_code 退出码 | 代码质量 | DONE | 2026-07-08 15:55 | - | mlh-p4-target-state |
| T81 | `两审 HR-TG 小校验器(新)` | P4·4.D.2 HR-TG 交集判定脚本化：TG 集∩HR-TG 子集→hit 列表/none+规范锚串，清单从 trigger-catalog 单一源读(tg02_hit 先例) | 代码质量 | DONE | 2026-07-08 15:55 | - | mlh-p4-target-state |
| T82 | `roadmap 对账小校验器(新)` | P4·4.D.4 roadmap task-log『Review 处置』对账脚本化：parse 小节断言无『未处置』状态 | 可观测性 | DONE | 2026-07-08 15:55 | - | mlh-p4-target-state |
| T83 | `embedded-test-sop + log_check.py(新)` | P4·4.A 串口日志规则判定脚本化：时间窗+must_contain/not/before+severity rollup 输出 PASS/FAIL，平台需人眼项留模型。目标态该做,正当排后——本仓无 embedded producer 契约可 dogfood,待真实 embedded 消费仓需求(producer 契约就绪度,非痛感) | 功能增强 | PROPOSED | 2026-07-08 15:55 | - | mlh-p4-target-state |
| T84 | `embedded-test-sop SOP模式A 小校验器(新)` | P4·4.D.3 SOP 模式A 源码常量/TAG 收割脚本化：正则 emit 常量表 name/值/来源:行。同 embedded 排后 | 功能增强 | PROPOSED | 2026-07-08 15:55 | - | mlh-p4-target-state |
| T85 | `roadmap mechanical-layer-hardening / recorder` | P6 recorder 索引→frontmatter（**端态 A 已定 2026-07-08**）：用户拍板根治(YAML 转义使 `｜` 腐蚀类结构上不可能)否决 B(治标·永久守脆弱表·手编辑洞)。约束①历史文档不迁使成本≈P5 dual-read 成熟范式(新写 frontmatter+历史表冻结只读)。实现=改 3 recorder 写路径+consumer dual-read 读+测试套,压轴排 ★P4 后。A 删写侧(`_reject_cell_unsafe`/`_render_item_table`/双写表半场),历史读 `parse_table_rows` 冻结保留。理由全档见 roadmap P6 端态块 | 基础设施 | PROPOSED | 2026-07-08 15:55 | - | mlh-p4-target-state |
| T86 | `anchor_lint.py load_enums` | 未闭合 fence 不 fail-closed（与 emitter _read_block_pairs 同盲区，本 change 已修 emitter 侧）——EOF 前无闭合围栏时静默把剩余全文当块体；契约受版本控制利用面低，但两侧同错致等价性测试假绿风险 | 代码质量 | PROPOSED | 2026-07-08 20:52 | implement-mechanical-layer-hardening-p4-lens-metric-emit | implement-mechanical-layer-hardening-p4-lens-metric-emit |
| T87 | `lens_metric_emit.py load_enums + anchor_lint.py` | lens-metric-enums 重复键静默后写覆盖（dict()），与 fold 块重复 raw 键 fail-closed 口径不一致；建议 enums 块也逐项拒绝重复 layer/lens/runner/sev-format 键 + 负例测试 | 代码质量 | PROPOSED | 2026-07-08 20:52 | implement-mechanical-layer-hardening-p4-lens-metric-emit | implement-mechanical-layer-hardening-p4-lens-metric-emit |
| T88 | `仓库 CI/pre-commit` | 无 CI/pre-commit → 单一源守卫测试（load_enums 等价/aggregator enum/MIN_LENS_ROWS 一致性）仅手动 pytest 生效，契约或硬编码常量漂移需下次跑测试才暴露、期间可正常提交合并 | 基础设施 | PROPOSED | 2026-07-08 20:52 | implement-mechanical-layer-hardening-p4-lens-metric-emit | implement-mechanical-layer-hardening-p4-lens-metric-emit |
| T89 | `roadmap_writeback_draft.py` | probe_format 全文扫描非限定 phase：混合格式 roadmap 会误判 checkbox，目标 phase 是表格式时不 fail-loud 反空匹配误诊断（修法:probe 增 phase 参数只扫该 phase 行段） | 代码质量 | PROPOSED | 2026-07-09 01:50 | done-roadmap-writeback | done-roadmap-writeback |
| T90 | `roadmap_writeback_draft.py` | frontmatter 解析与 ship_gate.py 全量 parity 缺口：BOM/tab缩进/YAML行尾注释未处理（nested-key 已 FIX-3 修） | 代码质量 | PROPOSED | 2026-07-09 01:50 | done-roadmap-writeback | done-roadmap-writeback |
| T91 | `roadmap_writeback_draft.py` | PREFIX_RE 贪婪 .+ 对含 -pN- 样式 roadmap 名/描述性尾缀的 change 名有命名固有歧义（取最后 -pN） | 代码质量 | PROPOSED | 2026-07-09 01:50 | done-roadmap-writeback | done-roadmap-writeback |
| T92 | `test_roadmap_writeback_draft.py` | test_verify_state_malformed_duplicate_key/bad_enum 无 ship-gate 包裹,FIX-3 后经无顶层 ship-gate 走 malformed 非经子路径 | 代码质量 | PROPOSED | 2026-07-09 01:50 | done-roadmap-writeback | done-roadmap-writeback |
| T93 | `resolve-workflow.sh` | bash 第3份 RULE_MARKERS 内联副本（resolve-workflow.sh）跨语言难与 init.py/maintain_scan.py 同守——一致性守卫只覆盖两份 Python 副本，bash 副本漂移不被机验 | 基础设施 | PROPOSED | 2026-07-09 13:36 | mlh-p4-maintain-scan | mlh-p4-maintain-scan |
| T94 | `maintain_scan.py + init.py` | 陈旧遮蔽告警文案第三处跨脚本复述 + checkpoint 孤儿路径：R-guard 不机验文案（文案守卫脆），maintain 抄 init 文案仅语义等价、漂移不被捕获——已知残差 | 代码质量 | PROPOSED | 2026-07-09 13:36 | mlh-p4-maintain-scan | mlh-p4-maintain-scan |
| T95 | `sdflow-maintain/tests/test_marker_consistency.py` | 守卫加载用 assert os.path.isfile + exec_module hard-fail；sdflow-init 目录整体缺席场景可加 importorskip 更优雅降级（当前 path-assert 直接 fail，defer 兜底优化） | 代码质量 | PROPOSED | 2026-07-09 13:36 | mlh-p4-maintain-scan | mlh-p4-maintain-scan |
| T96 | `maintain_scan.py _SPEC_LINK/_RULE_LINK` | 链接正则 [a-z0-9-]+ 与 scan_fs_specs/rules 目录名零字符集限制不对称：非规范命名(大写/下划线)的 spec/rule 被删且 INDEX 仍链接时，链接不命中正则→静默归②b排除→不进 stale→漏报已删未清理。openspec 强制 kebab 故低概率，彻底修需 scan_fs 也检非规范命名 | 代码质量 | PROPOSED | 2026-07-09 14:16 | mlh-p4-maintain-scan | mlh-p4-maintain-scan |
| T97 | `model-tiers` | 档位强制落地：镜 dispatch 显式带 model 参数，advisory→enforced（04 提案 §2.1） | 性能优化 | PROPOSED | 2026-07-10 16:54 | - | opt-p0 |
| T98 | `评审编排` | prompt 前缀缓存稳定化：子代理 prompt 组装序=稳定规则→半稳定→动态（04 提案 §2.2） | 性能优化 | PROPOSED | 2026-07-10 16:54 | - | opt-p0 |
| T99 | `code-review` | 确定性检查前置准入门：pytest/lint/typecheck 未绿不进 fan-out（04 提案 §2.3） | 性能优化 | PROPOSED | 2026-07-10 16:54 | - | opt-p0 |
| T100 | `workflow` | 微变更快速通道：全流程深度三档 micro/standard/deep 机判分层（04 提案 §2.4） | 功能增强 | PROPOSED | 2026-07-10 16:54 | - | opt-p0 |
| T101 | `spec-review` | 设计门报告三层摘要头+结构化拍板三问（04 提案 §3.1） | 功能增强 | PROPOSED | 2026-07-10 16:54 | - | opt-p0 |
| T102 | `评审编排` | 对抗镜措辞收紧：只报影响正确性/明示需求的 gap，其余标 optional（04 提案 §4.5） | 代码质量 | PROPOSED | 2026-07-10 16:54 | - | opt-p0 |
| T103 | `评审编排` | 每镜 effort scaling 预算+输出封顶：四要素 prompt 槽+1-2k 回传目标（04 提案 §2.5） | 性能优化 | PROPOSED | 2026-07-10 16:54 | - | opt-cost |
| T104 | `retro` | retro 补 token 维度量：checkpoint 落 token 快照锚+join（04 提案 §2.6） | 可观测性 | PROPOSED | 2026-07-10 16:54 | - | opt-cost |
| T105 | `model-tiers` | thinking/effort 预算按步分档：model-tiers 加第二维（04 提案 §2.7） | 性能优化 | PROPOSED | 2026-07-10 16:54 | - | opt-cost |
| T106 | `code-review` | 裁决二元化 pass/fail+critique 替代连续置信分，retro 收敛校准（04 提案 §4.1） | 代码质量 | PROPOSED | 2026-07-10 16:54 | - | opt-review-reliability |
| T107 | `评审编排` | 位置去偏：HIGH 级裁决换序重跑+fan-out 输入顺序打散（04 提案 §4.2） | 代码质量 | PROPOSED | 2026-07-10 16:54 | - | opt-review-reliability |
| T108 | `retro` | 镜价值指标升级 resolution rate+假阳模式沉淀回 checklist（04 提案 §4.3） | 可观测性 | PROPOSED | 2026-07-10 16:54 | - | opt-review-reliability |
| T109 | `code-checklists` | 测试大改=红旗 硬规则+intake diff 体积提示（04 提案 §4.4） | 代码质量 | PROPOSED | 2026-07-10 16:54 | - | opt-review-reliability |
| T110 | `bundle` | 明码自动决策原则清单 decision-principles.md，T10 第①级引用（04 提案 §5.6） | 功能增强 | PROPOSED | 2026-07-10 16:54 | - | opt-review-reliability |
| T111 | `outside-voice` | injection 前缀：发 codex 的 context 冠不读 skill 定义目录（04 提案 §4.7） | 代码质量 | PROPOSED | 2026-07-10 16:54 | - | opt-review-reliability |
| T112 | `评审编排` | 弱档 validator 复核层：置信过滤后复核 findings 引用真实性（04 提案 §4.6） | 代码质量 | PROPOSED | 2026-07-10 16:54 | - | opt-review-reliability |
| T113 | `评审编排` | HIGH 级终局裁决跨模型双栈：outside-voice 延伸到裁决层（04 提案 §4.6） | 代码质量 | PROPOSED | 2026-07-10 16:54 | - | opt-review-reliability |
| T114 | `bundle` | 规则条款元维护：条款触发证据扫描，零触发列待复评（04 提案 §6.3） | 可观测性 | PROPOSED | 2026-07-10 16:54 | - | opt-review-reliability |
| T115 | `bundle` | spec 模版增强：EARS 句式+三必填槽+测试 seam 决策槽（04 提案 §3.2/§3.3） | 功能增强 | PROPOSED | 2026-07-10 16:54 | - | opt-structure |
| T116 | `workflow` | 高危路径升级例外：HR-TG 类修复 defer-to-human 异步（04 提案 §3.5） | 功能增强 | PROPOSED | 2026-07-10 16:54 | - | opt-structure |
| T117 | `机械层` | 跨工件一致性检查 artifact_consistency.py 设计门前置（04 提案 §3.4） | 基础设施 | PROPOSED | 2026-07-10 16:54 | - | opt-structure |
| T118 | `writing-plans` | tasks 依赖 DAG 化+frontier 受限并行（保守试点）（04 提案 §5.1） | 功能增强 | PROPOSED | 2026-07-10 16:54 | - | matt-workflow-integration |
| T119 | `roadmap` | fog-of-war 进 roadmap 模版：远期阶段留雾区（04 提案 §5.2） | 功能增强 | PROPOSED | 2026-07-10 16:54 | - | opt-structure |
| T120 | `bundle` | expand-contract 宽重构协议进 bundle（04 提案 §5.3） | 功能增强 | PROPOSED | 2026-07-10 16:54 | - | matt-workflow-integration |
| T121 | `评审编排` | 大产物文件交接：镜报告超阈值写文件、返回只带路径（04 提案 §5.7） | 性能优化 | PROPOSED | 2026-07-10 16:54 | - | opt-structure |
| T122 | `skills` | done/ship/init 加 disable-model-invocation 触发层硬开关（04 提案 §5.4） | 功能增强 | PROPOSED | 2026-07-10 16:54 | - | opt-structure |
| T123 | `issues` | 动作抽象层：recorder tracker 后端可插拔，仅当需求出现（04 提案 §5.5） | 基础设施 | PROPOSED | 2026-07-10 16:54 | - | opt-structure |
| T124 | `bundle` | 规则注入策略分界落地：小而稳定且每镜必用的核心 rubric 运行时读一次全文贴入（可缓存稳定前缀），大部头/高频演进 delta 保持引用+anchor_lint；SKILL.md 禁静态内联不变（04 提案 §4.8，2026-07-10 拍板） | 功能增强 | PROPOSED | 2026-07-10 17:10 | - | opt-cost |
| T125 | `评审编排` | 议题：fan-out 子代理产物默认落临时文件、返回只带路径——动机是交接可靠性（防最终文本截断/结构化输出失配/compaction 丢失），比 T121（超阈值才写文件）更进一步；讨论点：默认落盘 vs 阈值触发、临时文件生命周期与清理、主审读文件的路径契约（2026-07-10 探索会提出） | 基础设施 | PROPOSED | 2026-07-10 17:47 | - | matt-workflow-integration |
| T126 | `bundle` | wayfinder→ff 衔接契约 + 主流程三段分流入口：清晰直接 ff / 单 session 模糊走 explore / 超单 session 大雾走 wayfinder；契约三条=ff 起手逐区读 map（Destination→proposal 动机+D-5、Decisions-so-far 逐行 zoom 决议全文防 make-reasonable-decisions 重决歪、Out-of-scope→D-3 假设）+ TG 判命中前置到 chart 写 map Notes + proposal 回链 map（2026-07-10 探索会，调研代理 file:line 已接地） | 功能增强 | PROPOSED | 2026-07-10 17:58 | - | matt-workflow-integration |
| T127 | `bundle` | grill 瘦跑规则：上游 wayfinder 已决分支引 resolution comment 快速核对即过、新生成/未决部分照常死磕——grill 对象是 ff 烘焙产物 vs 代码 ground truth，与 wayfinder grilling 票（生成前决策）非冗余、不可整跳（2026-07-10 探索会） | 功能增强 | PROPOSED | 2026-07-10 17:58 | - | matt-workflow-integration |
| T128 | `sdflow-implement` | impl_route.py PIPELINE_RECEIPT 的 marker 显示折叠：显式 `impl-pipeline: superpowers` 与无 frontmatter/无键的隐式缺省均显示 marker=none，路由行为等价但 receipt 可诊断性受损（F3a 判赢留档核对时无法分辨是否显式声明过）——需 read_plan_marker 返回值携带来源注记再区分显示（code-review defer，display-only 无路由风险） | 代码质量 | PROPOSED | 2026-07-11 01:37 | matt-workflow-integration | matt-workflow-integration |
| T129 | `sdflow-roadmap` | 存量 wco/mlh 两包 requirements.md 并入 design.md 迁移（tasks 5.1-5.3 受控延后项，Q-C 拍板前置②）——触发条件：首个新流程 roadmap SHIPPED 且目标包无在飞 change；操作序列以归档 change rebuild-sdflow-roadmap-v2 的 tasks.md 5.1-5.3 + design Migration step3 为准（全节清点表/考古注记四要素/头部章不占编号序列/清点表落盘随 commit/per 包 maintain_scan） | 代码质量 | PROPOSED | 2026-07-11 02:30 | rebuild-sdflow-roadmap-v2 | rebuild-sdflow-roadmap-v2 |
| T130 | `bundle` | ff-generation-constraints.md:43 衔接契约边界句「requirements/design/roadmap/task-log 四件套」→「三件套」术语同步——matt-workflow-integration Task7 写入时 rebuild-sdflow-roadmap-v2 未落地所致漂移；属 assets/workflow 权威源（rebuild change Compliance 声明零 assets 改动故未扫），一词修正独立小改，改后消费仓经 sdflow-init update 获得 | 代码质量 | PROPOSED | 2026-07-11 02:30 | rebuild-sdflow-roadmap-v2 | rebuild-sdflow-roadmap-v2 |
| T131 | `bundle` | workflow.md 阶段一 wayfinder 缺装探测硬编码 Claude 单宿主路径（~/.claude/skills/wayfinder）——未同步 sdflow-roadmap SKILL.md 本轮新增的宿主中立探测口径（按当前宿主 Claude/Codex 分别探测，MUST NOT 以 Claude 路径代理全局）；Codex 宿主跑 mainflow 阶段一会重犯同款误判。属 assets/workflow 权威源（rebuild change Compliance 零 assets 改动故未扫），改后经 sdflow-init update 分发 | 代码质量 | PROPOSED | 2026-07-11 02:55 | rebuild-sdflow-roadmap-v2 | rebuild-sdflow-roadmap-v2 |
| T132 | `openspec/workflow/ + sdflow-spec-review 起手 fail-closed 门` | grill 相位防静默跳过：spec-review 起手机械核验『grill 已收敛』信号（workflow.md:83 已强制的 grill checkpoint-commit，或 design.md 内补 <!-- sdflow:grill-done --> 锚），无信号→REFUSE_START 提示先跑 grill。grill 本身是人类对话岛不能自动跑，但『跑没跑』可机械断言——同 ship_gate 设计门新鲜度 fail-closed 先例，把判断从模型记性挪到脚本。属 mechanical-layer-hardening 家族。关联 T19（T19 定何时可跳；本条定跳了就机械拦）。信号载体（commit-tag vs design.md 锚）待其自身 design 定。 | 代码质量 | OPEN | 2026-07-11 08:59 | - |  |
| T133 | `grill 提示自动生成（sdflow-spec-review 门 / 阶段提示）` | 提示/触发 grill 时自动生成完整可复制 prompt，但须『脚手架完整+内容轻播种』校准：grill-with-docs=/grilling(relentless逐branch独立走设计树,一次一问,每问给推荐,事实自查决策抛人)+/domain-modeling。auto-prompt 只应含调用脚手架(change dir/全深度非wayfinder/MUST NOT skip/doc路径 adr→openspec/adr·术语→CONTEXT.md·INDEX/[grill-amendment]/收敛才提交)；MUST NOT 预装已分析的弱点清单+推荐(会 anchor+短路 grilling 独立发现盲点的核心价值,让它只 validate 我的结论而非找第6条)。至多给一句非绑定怀疑点并注明『非边界,去找我漏的』。关联 T132(grill 未跑 fail-closed 门,该门 REFUSE 时正好 emit 此 prompt)+T28(下一阶段附完整可复制 prompt)。 | 代码质量 | OPEN | 2026-07-11 09:14 | - |  |
| T134 | `domain-modeling / grill-with-docs 领域文档路径感知` | domain-modeling(grill-with-docs 内包)裸 SKILL.md 硬编码根 docs/adr/+CONTEXT.md，不读 openspec/matt/domain.md(setup-matt-pocock-skills 写的路径配置)——靠本 session CLAUDE.md ## Agent skills 块覆盖赢冲突，脆：skill-local 硬编码是强 pull,万一某次赢了就在根建 docs/adr/=第二真相源(正是 generation-process §六 警告的漂移)。硬化:让 domain-modeling domain.md-path-aware(或加 matt 包装),从根免掉每次 grill prompt 手塞路径重定向。未修前 grill prompt 保留 ADR→openspec/adr/ 重定向作 belt-and-suspenders(几字成本换掉冲突风险)。关联 T133(该重定向属 auto-prompt 脚手架,非分析 seed,不违 T133 校准)。 | 代码质量 | OPEN | 2026-07-11 09:31 | - |  |
| T135 | `sdflow-implement` | superpowers-plan.md 文件名硬编码在 ship_gate 契约里，tickets 管线被迫借壳穿这个误导性文件名——应参数化 | 代码质量 | OPEN | 2026-07-11 12:48 | - |  |
| T136 | `anchor_lint` | anchor_lint 只校验 hr-tg 锚字段在场、不重算交集——手改 hit=none/declared=TG-04 可绕过必开 cross-model（codex 冷审 high） | 基础设施 | PROPOSED | 2026-07-11 13:58 | mlh-p4-reason-code-validators | mlh-p4-reason-code-validators |
| T137 | `config.yaml` | impl-pipeline:tickets 翻键注释写'首个试点(mlh-p4)'误导——mlh-p4 已由 plan marker 自锁，翻键实际只影响 scoped-test-per-task 及未来 change（对抗镜 medium） | 基础设施 | DONE | 2026-07-11 13:58 | mlh-p4-reason-code-validators | mlh-p4-reason-code-validators |
| T138 | `hr_tg_intersect` | hr_tg parse_tg_set 静默吞空 token（'TG-04,,TG-16'/',' 都过）+ catalog 成员用宽松 TG-\d+（'TG-04x'→TG-04）（codex medium） | 代码质量 | PROPOSED | 2026-07-11 13:58 | mlh-p4-reason-code-validators | mlh-p4-reason-code-validators |
| T139 | `outside_voice_guard` | outside_voice_guard parse_mode 用 .search 取首个 step1 锚——native/simulated 双锚静默取前者，不校验数量/一致性（codex+对抗镜 low） | 代码质量 | PROPOSED | 2026-07-11 13:58 | mlh-p4-reason-code-validators | mlh-p4-reason-code-validators |
| T140 | `anchor_lint` | check_hr_tg 把 declared 列为 hr-tg 锚必填、无向后兼容——旧格式锚(hit=+evidence=无declared)重 lint 会 exit1（对抗镜 low） | 代码质量 | PROPOSED | 2026-07-11 13:58 | mlh-p4-reason-code-validators | mlh-p4-reason-code-validators |
| T141 | `workflow bundle (roadmap/ff/spec-review/implement/code-review)` | 把「拆分标准=一个change一个完整阶段结果」融入 workflow 三处触发 | 基础设施 | OPEN | 2026-07-11 16:11 | - |  |
| T142 | `docs/workflow-map.md` | workflow-map.md 广度刷新：补 mlh-p4 后 5 脚本 + hr-tg schema 回灌 | 基础设施 | OPEN | 2026-07-11 16:55 | - |  |
| T143 | `sdflow-architecture` | frozen-diff lint：frozen contract 有 diff 无新 ADR 关联报错（需 git 对比，超 v1 纯文件断言） | 功能增强 | PROPOSED | 2026-07-12 17:16 | add-sdflow-architecture | add-sdflow-architecture |
| T144 | `sdflow-architecture` | sad_schema 常量单向生成 JSON schema 工件（跨语言消费方出现时触发） | 基础设施 | PROPOSED | 2026-07-12 17:16 | add-sdflow-architecture | add-sdflow-architecture |
| T145 | `sdflow-roadmap` | 观察 description 追加 SAD 指路句后的触发精度（架构类查询是否误触 roadmap） | 可观测性 | PROPOSED | 2026-07-12 18:34 | add-sdflow-architecture | add-sdflow-architecture |
| T146 | `sdflow-skills 工具族` | 扫描-max+1 无锁并发面统一：todolist.py/buglist.py 与 sad_scaffold 锁面方案对齐（O_CREAT+O_EXCL 仓级互斥） | 代码质量 | PROPOSED | 2026-07-12 18:34 | add-sdflow-architecture | add-sdflow-architecture |
| T147 | `openspec/workflow/` | openspec/workflow/ 下 v1 孤儿 debris：lens-metric-contract.md（无 host/reason_code）+ tools/anchor_lint.py（REQUIRED_FIELDS 缺 host）/lens_metric_emit.py（无 --host）/outside_voice_guard.py（:93 仍 runner!="codex" 裸判）均为 add-codex-host-support 改前的 v1 旧副本——非 pin 遮蔽（resolve-workflow.sh 因本地缺 workflow.md/spec-checklists/code-checklists 三个 pin 判据文件，判定非本地 pin，runtime 恒走全局 canonical ~/.sdflow/workflow）；待本仓自身跑 sdflow-init update 或手动清空该目录 | 基础设施 | DONE | 2026-07-15 23:47 | - |  |
| T148 | `tools/anchor_lint.py` | anchor_lint._FANOUT_MIRRORS={domain,adversarial,grounding} 缺 code-review 真名 history；现 code-review 借用 grounding token 记历史镜（不污染 retro：聚合只读 lens-metric 锚不读 fanout-capability，lens-metric 用真 lens=history）。正修 = _FANOUT_MIRRORS 加 history + 同步 spec.md/design.md 三处 SHALL 条款——触已过三轮收敛的 spec 文本，需另开 change 走 spec-review（非本 change fold 范围） | 代码质量 | OPEN | 2026-07-15 23:47 | - |  |
| T149 | `sdflow-init/scripts/init.py` | lint_config 对 metrics.enabled 重复键无告警(true+false并存时valid恒True,anchor_lint取首值);未如parse_kv_strict收紧,潜在一致性盲点 | 代码质量 | PROPOSED | 2026-07-16 11:25 | add-codex-host-support | add-codex-host-support |
| T150 | `sdflow-init/assets/hack/outside-voice.sh` | preflight 只 command-v + timeout 检查,未按 ADR-6「真跑一次」补低成本真探针(CLI未认证/模型无效/参数不支持仍返回ready,失效漏到exec归exec-error) | 功能增强 | PROPOSED | 2026-07-16 11:25 | add-codex-host-support | add-codex-host-support |
| T151 | `sdflow-buglist/tests/test_mirror_consistency.py` | 扩展 recorder three-way parity guard，覆盖共享 lock 常量与 RecorderLockState/RecorderLockError 类型定义 | 代码质量 | OPEN | 2026-07-17 11:08 | mlh-p6-recorder-frontmatter |  |
| T152 | `openspec/changes/mlh-p6-recorder-frontmatter/impl-reports` | 规范实现报告的 git diff --check 记录：机械 review package 含原样 trailing whitespace 时显式写 exclude 命令与范围 | 代码质量 | OPEN | 2026-07-17 11:23 | mlh-p6-recorder-frontmatter |  |

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
| 状态 | DONE |

**关联文档**：`openspec/changes/sdflow-retro/design.md`

**动机**：code-review code-voice F8：_fence_aware_lines 只匹配 ``` 反引号 fence，~~~ 代码块里的示范 lens-metric/hr-tg 锚会被误计入聚合。既有聚合器限制（本 change 迁入前即有），非本 change 引入

**思路**：记录 fence marker 字符+长度，闭合要求同字符且长度足够；补 ~~~ 回归测试。retro 复用 parse_report 故连带受益

**备注**：defer 自 sdflow-retro code-review；既有既存问题非本 change 回归
> 2026-07 状态：PROPOSED → DONE（change sdflow-retro-cleanup; commit 094aeca）

---

## T59: ≥10 待复评阈值 10 硬编码两处(surfacing_block + render_table)无共享常量

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-retro/retro_report+lens_metric_aggregate` |
| 类型 | 代码质量 |
| 状态 | DONE |

**关联文档**：`openspec/changes/sdflow-retro/design.md`

**动机**：code-review 领域镜 F9：与刚 group_key 抽取根治的两处手写漂移同类风险，阈值调整易改一处漏一处致 surfacing/render_table flag 口径不一致

**思路**：抽共享常量如 REVIEW_WINDOW=10 到 lens_metric_aggregate，两处引用

**备注**：低危 defer 自 sdflow-retro code-review
> 2026-07 状态：PROPOSED → DONE（change sdflow-retro-cleanup; commit 1bea68b）

---

## T60: _run_git 不检查 returncode，git 失败与真无提交不可区分

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-retro/retro_report` |
| 类型 | 可观测性 |
| 状态 | DONE |

**关联文档**：`openspec/changes/sdflow-retro/design.md`

**动机**：code-review 领域镜+对抗镜2 F10：_run_git subprocess check=False，git 报错(权限/损坏仓/未安装)与该路径确 0 提交都产空 stdout，都归边界不可解析，无法诊断区分。设计偏 fail-open 风格

**思路**：可选：检查 returncode 非 0 时区分标记边界解析失败原因(git-error vs no-commits)，或至少 stderr 留痕

**备注**：低危 design-accepted defer 自 sdflow-retro code-review
> 2026-07 状态：PROPOSED → DONE（change sdflow-retro-cleanup; commit 4e71708）

---

## T61: build_report/surfacing_block 包 LMA.aggregate 的 except 是死防御(glob 缺目录不抛)+注释误导

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-retro/retro_report` |
| 类型 | 代码质量 |
| 状态 | DONE |

**关联文档**：`openspec/changes/sdflow-retro/design.md`

**动机**：code-review 对抗镜2 F11：Path.glob 对不存在/不可读目录静默返空不抛，该 try/except 分支不可达；注释描述archive不存在不崩 实际由 glob 行为达成非此 catch，易误导维护者

**思路**：改注释诚实说明，或改用 os.path.isdir 显式判空分支语义更直白

**备注**：极低危 defer 自 sdflow-retro code-review
> 2026-07 状态：PROPOSED → DONE（change sdflow-retro-cleanup; commit 9c2c72e）

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
| 状态 | DONE |

**动机**：B4/B5 同根：ship-gate 状态锚（design-approved/verify=PASS|FAIL/code-review=pass|blocked）inline 嵌在报告正文，逼 gate 用 fence-aware+独占行+line-scoped 一整套解析去区分『真标记 vs 正文提及』。B5 的聚合不变量补丁是在旧架构里绕过，非根治。状态若在 frontmatter（结构化数据），正文再怎么提及锚串都不会被误当标记，整类 bug 从根消失，且可删掉那套解析机器。

**思路**：scope 严格收窄到家族①（gate 状态判据）——家族③逐条 inline tag（[impl-review-fix]/〔TG-N〕/task<N>/item ID，位置相关）和家族④模版槽位占位（<待填>等）明确留 inline，不搬。须评估三处风险：①bundle 爆炸半径（ship_gate.py+报告模版+生产者 SKILL.md 全在 assets/workflow/ 铺下游 → 改权威源+sdflow-init update 回灌所有消费仓，高仪式单开 change，行为面路径硬排除、绝不 fold/sweep）；②LLM 产报告写坏 YAML → safe_load 抛的兜底策略（比缺 inline 锚更糙的失败面）；③57 篇归档报告是 inline 锚 → gate/corpus 的兼容窗口/dual-read。

**备注**：够格作为 workflow-cost-optimization roadmap 的一个阶段（与『评审机器复杂度』直接相关）。动机证据=buglist B4/B5。别在清理惯性里反应式开工——正式评估 ROI（inline 锚这套是否会反复出同类 bug）后再决定做不做。
> 2026-07 状态：OPEN → DONE（changes mlh-p5-gate-frontmatter + mlh-p5-parser-cleanup）

---

## T1: reindex 回显子进程 scan 的 problems 到 stderr（补齐独立跑 reindex 时表↔块不一致的可见性，D5 承诺）

| 属性 | 值 |
|------|------|
| 模块 | `issues.py` |
| 类型 | 可观测性 |
| 状态 | DONE |

> 2026-07 状态：PROPOSED → DONE（issues-pool-hardening 实现(SDD 10任务+code-review 6 fix), 全仓552 passed）

---

<!-- sdflow-issue-block:start id=T2 -->
## T2: 字段含 ｜ 破 markdown 表：统一转义或拒绝含 ｜ 的字段（module/summary/批次名等，防位置解析读错列的数据腐蚀，系统性）

| 属性 | 值 |
|------|------|
| 模块 | `recorder` |
| 类型 | 代码质量 |
| 状态 | DONE |

> 2026-07 状态：PROPOSED → DONE（issues-pool-hardening 实现(SDD 10任务+code-review 6 fix), 全仓552 passed）

> 2026-07 状态：DONE → DONE（mlh-p6-recorder-frontmatter（根治兑现））
<!-- sdflow-issue-block:end id=T2 -->
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

---

## T74: ship_gate parser 裸---首行(无闭合)误判 unterminated 致 UNKNOWN

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-ship` |
| 类型 | 代码质量 |
| 状态 | DONE |

**关联文档**：`openspec/changes/mlh-p5-gate-frontmatter/design.md`

**备注**：code-review defer(A2,方向安全): 报告以裸 --- 开头且全文无第二个 --- 时 parse_ship_gate_frontmatter 判 unterminated→live UNKNOWN(6)误崩干净无锚报告。当前语料不触发(均以#开头)。未来鲁棒性:首行---无闭合判 absent 而非 bad。
> 2026-07 状态：PROPOSED → DONE（change mlh-p5-parser-cleanup; commit e1b03a6）

---

## T75: ship_gate 清理 live inline 死代码 anchors_in/pick_exclusive/ANCHOR_DESIGN/ANCHOR_CR_*

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-ship` |
| 类型 | 代码质量 |
| 状态 | DONE |

**关联文档**：`openspec/changes/mlh-p5-gate-frontmatter/design.md`

**备注**：code-review defer(fallback-F2): Task6 退役只从 decide() 摘调用,函数本体+ANCHOR_DESIGN/ANCHOR_CR_PASS/ANCHOR_CR_BLOCKED 成 test-referenced 孤儿。ANCHOR_VERIFY_PASS/FAIL 仍被 archived_verify_state 真用勿删。另开 cleanup 删死函数+测试。
> 2026-07 状态：PROPOSED → DONE（change mlh-p5-parser-cleanup; commit b472642）

---

## T76: 归档杂交盲区硬化后续（设计门已接受净负、登记为已知盲区）：冷代码审对抗镜给出比「仅手工伪造」更锋利的可达性论证——迁移半成品编辑残留独占行 inline PASS 锚、自指文档独占行引用（呼应 gate-substring-dogfood 自指坑）；建议未来加**非语义** lint/监控扫「归档 verify-report 首行 --- 无闭合」形态告警（不改 parser 语义、不重开设计门 adr/0004），据此复评「给归档侧特殊 fail-safe」ROI（design L121 当前选①绝）

| 属性 | 值 |
|------|------|
| 模块 | `ship_gate.py archived_verify_state` |
| 类型 | 基础设施 |
| 状态 | WONTDO |

> 2026-07 状态：OPEN → WONTDO（已复评(explore 2026-07-08)：①绝 HOLD 且被迁移完成强化。冷代码审对抗镜给的最锋利可达路径「迁移半成品编辑残留独占行 inline PASS 锚」是【迁移窗专属】论据——T75 删净 live inline 死码、三 producer 全迁后迁移窗已闭，无待迁 producer 即无半成品可残留，该路径失效。稳态下要凑齐「首行 --- 无闭合 × 正文独占行 inline PASS」杂交形态只能人手伪造 git-committed 畸形归档=adr/0008 显式越权(git 可审计)。非语义 monitor 三点不成立：(1)稳态恒零命中=纯仪式(producer 只写 frontmatter 不产②)；(2)非安全边界——有 git 写权的越权者能同样手改绕过，adr/0008 立场=git 写靠历史审计非运行时防；(3)开发循环镜主导判主次，系统镜给 monitor 的「外部无漂移」一分被压过。已在位 mitigation(头注册 ship_gate.py:118-123 + 目标态回归测试 test_archived_unclosed_*)足够。未来 P6 等新迁移窗的 insurance 价值由「目标态回归测试 per 迁移」成熟模式兜底(P5 即如此)，不需常驻 monitor。故 ①绝 不建 monitor，无代码产出。）

---

## T86: 未闭合 fence 不 fail-closed（与 emitter _read_block_pairs 同盲区，本 change 已修 emitter 侧）——EOF 前无闭合围栏时静默把剩余全文当块体；契约受版本控制利用面低，但两侧同错致等价性测试假绿风险

| 属性 | 值 |
|------|------|
| 模块 | `anchor_lint.py load_enums` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/implement-mechanical-layer-hardening-p4-lens-metric-emit/design.md`

**备注**：code-review CR-D1；平行 CR-C3（emitter 侧已修）

---

## T87: lens-metric-enums 重复键静默后写覆盖（dict()），与 fold 块重复 raw 键 fail-closed 口径不一致；建议 enums 块也逐项拒绝重复 layer/lens/runner/sev-format 键 + 负例测试

| 属性 | 值 |
|------|------|
| 模块 | `lens_metric_emit.py load_enums + anchor_lint.py` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/implement-mechanical-layer-hardening-p4-lens-metric-emit/design.md`

**备注**：code-review CR-D2

---

## T88: 无 CI/pre-commit → 单一源守卫测试（load_enums 等价/aggregator enum/MIN_LENS_ROWS 一致性）仅手动 pytest 生效，契约或硬编码常量漂移需下次跑测试才暴露、期间可正常提交合并

| 属性 | 值 |
|------|------|
| 模块 | `仓库 CI/pre-commit` |
| 类型 | 基础设施 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/implement-mechanical-layer-hardening-p4-lens-metric-emit/design.md`

**备注**：code-review CR-D3（治理层）

---

## T89: probe_format 全文扫描非限定 phase：混合格式 roadmap 会误判 checkbox，目标 phase 是表格式时不 fail-loud 反空匹配误诊断（修法:probe 增 phase 参数只扫该 phase 行段）

| 属性 | 值 |
|------|------|
| 模块 | `roadmap_writeback_draft.py` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/done-roadmap-writeback/design.md`

**备注**：code-review defer(D2 中)。现两存量 roadmap 各单一格式无触发

---

## T90: frontmatter 解析与 ship_gate.py 全量 parity 缺口：BOM/tab缩进/YAML行尾注释未处理（nested-key 已 FIX-3 修）

| 属性 | 值 |
|------|------|
| 模块 | `roadmap_writeback_draft.py` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/done-roadmap-writeback/design.md`

**备注**：code-review defer(H2#2/4/5·H3 中)。本仓 verify-report 格式固定 dogfood-green;消费仓非规范输入可能漂移。修法:对齐 ship_gate parse_ship_gate_frontmatter 全量口径+补边界测试

---

## T91: PREFIX_RE 贪婪 .+ 对含 -pN- 样式 roadmap 名/描述性尾缀的 change 名有命名固有歧义（取最后 -pN）

| 属性 | 值 |
|------|------|
| 模块 | `roadmap_writeback_draft.py` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/done-roadmap-writeback/design.md`

**备注**：code-review defer(D5 低)。命名规范固有无法纯字符串消歧,机制已按贪婪取最后合理处理;建议脚本注释显式记边界

---

## T92: test_verify_state_malformed_duplicate_key/bad_enum 无 ship-gate 包裹,FIX-3 后经无顶层 ship-gate 走 malformed 非经子路径

| 属性 | 值 |
|------|------|
| 模块 | `test_roadmap_writeback_draft.py` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/done-roadmap-writeback/design.md`

**备注**：code-review Minor。行为正确(均→malformed 已验),FIX-3 已补 ship-gate 专项测试;可将两旧测试包进 ship-gate 测真子路径

---

## T78: P4·4.C lens-metric 数值一致性从模型手数下沉为脚本归约：吃已判结构化 findings(带命中镜集+裁决+sev)→机械归约计数+锚行；去重/对抗裁决留模型。闭合 requirements §1.2 痛点#2『手数信任边界』、adr/0006 硬约束——目标态该做(原按快照压为按需,已翻案)

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-code-review/spec-review SKILL + lens_metric_emit.py(新)` |
| 类型 | 代码质量 |
| 状态 | DONE |

> 2026-07 状态：PROPOSED → DONE（implement-mechanical-layer-hardening-p4-lens-metric-emit / bd7c05f（4.C lens_metric_emit.py 交付））

---

## T17: 陈旧遮蔽判据两处（RULE_MARKERS 常量 vs SKILL prose 复述）无同步机制，改常量会漂——考虑 opsx-maintain 兜底扫描改调脚本

| 属性 | 值 |
|------|------|
| 模块 | `opsx-maintain/SKILL.md + init.py` |
| 类型 | 基础设施 |
| 状态 | DONE |

> 2026-07 状态：PROPOSED → DONE（mlh-p4-maintain-scan：maintain_scan.py 脚本化陈旧遮蔽判据 + test_marker_consistency.py 一致性守卫机验 RULE_MARKERS/token 与 init.py 相等（f4c61b4/6ce74fc），闭合改常量会漂的风险）

---

## T135: tickets 管线 plan 文件名不应硬编码为 superpowers-plan.md

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-implement` |
| 类型 | 代码质量 |
| 状态 | OPEN |

**动机**：ship_gate.py 把 superpowers-plan.md 作为唯一识别的完成判据契约文件名；tickets 管线（sdflow-implement）为复用零改动的 gate，被迫把 ticket 也写进 superpowers-plan.md（借壳）。文件名与实际管线（tickets）语义不符，对读者误导；gate 与两条管线三处对该文件名的依赖是隐式耦合。

**思路**：把 plan 文件名从 gate 硬编码提为可配置/可发现（按 frontmatter marker 或 config 决定文件名，或 gate 扫描 openspec/changes/{change}/ 下带 impl-pipeline frontmatter 的任一 *.md）。属 ship 链序注释里的『emit 串 Phase B 根治』范畴。改动须同步 ship_gate.py TAG_RE/解析、impl_route.py、sdflow-implement/sdflow-ship 三处文档，保持向后兼容既有 superpowers-plan.md。

---

## T136: anchor_lint 重算 hr-tg 交集以堵手改绕过 cross-model

| 属性 | 值 |
|------|------|
| 模块 | `anchor_lint` |
| 类型 | 基础设施 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/mlh-p4-reason-code-validators/design.md`

**动机**：codex 跨模型冷审：check_hr_tg 只断言 hit/declared 字段存在、接受任意值。正常流 hit 与 declared 都由 hr_tg_intersect.py 一次 emit 不会漂移，但手改报告写 hit=none declared=TG-04（TG-04 属 HR-TG）能通过 lint、静默跳过必开的领域 cross-model。属手改越权通道(git 留痕)的加固缺口。

**思路**：让 anchor_lint 接 --trigger-catalog 路径，严格解析 declared、重算 declared∩HR-TG、要求 hit 与结果完全一致，并拒重复/畸形 hr-tg 锚。注意这是把 anchor_lint 从'字段在场校验'扩到'重算校验'，越出本 change 的机械-presence 设计边界，需先定夺是否愿意扩 anchor_lint 职责（adr/0018 机械/判断切分）。

---

## T137: config impl-pipeline 翻键 blast radius 与注释不符，需定夺全局切换 vs 仅试点

| 属性 | 值 |
|------|------|
| 模块 | `config.yaml` |
| 类型 | 基础设施 |
| 状态 | DONE |

**关联文档**：`openspec/changes/mlh-p4-reason-code-validators/design.md`

**动机**：对抗镜冷审实证：mlh-p4 的 superpowers-plan.md 已含 impl-pipeline:tickets frontmatter marker，impl_route marker 优先于 config，故翻键对 mlh-p4 冗余；真正被 config=tickets 卷入的是无 plan 的 scoped-test-per-task（实跑 route 得 pipeline=tickets）及所有未来 change。注释'首个试点(mlh-p4)'主动误导读者以为仅 mlh-p4 受影响；CLAUDE.md 记的 pull→setup 反向窗口风险随全局键放大到每个未锁 change。

**思路**：定夺意图：①若仅 pilot mlh-p4→config 键应保持注释态（mlh-p4 已自锁无需全局键），撤回翻键；②若确为仓级前向切换→改注释去掉误导性单-change 框定、明确 scoped-test-per-task 及后续全部 change 入 tickets。属需用户意图裁断项，hand-off 提请人决。
> 2026-07 状态：PROPOSED → DONE（582b2ee（撤回 impl-pipeline:tickets 翻键，选项①））

---

## T138: hr_tg_intersect 收紧坏输入解析（空 token/前后逗号/宽松成员正则）

| 属性 | 值 |
|------|------|
| 模块 | `hr_tg_intersect` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/mlh-p4-reason-code-validators/design.md`

**动机**：codex 冷审：声称坏输入 fail-closed，实际 parse_tg_set 过滤空 token 后 'TG-04,,TG-16' 返合法列表、单个 ',' 视作空集；catalog 成员抽取用宽松 TG-\d+ 令 'TG-04x' 被当 TG-04。畸形被静默正规化而非 fail-closed，可能掩盖模型侧记号错误（declared= 虽暴露但机械层不挡）。

**思路**：仅允许原始空串表示空集；CSV 出现空单元/前后逗号即 EmitError；成员行改边界严格 token 解析，残余/畸形文本 fail-closed。

---

## T139: outside_voice_guard 双 step1 锚一致性校验

| 属性 | 值 |
|------|------|
| 模块 | `outside_voice_guard` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/mlh-p4-reason-code-validators/design.md`

**动机**：codex+对抗镜冷审：规范可能写入两个同源 step1-broad-review 锚，parse_mode 只 .search 取第一个，双锚(native 在前 simulated 在后)静默取 native 忽略 simulated。属构造性/低概率（单锚是常态），但违'数量与 mode 一致否则 fail-closed'的稳健取向。

**思路**：收集所有 fence 外 step1 锚，要求数量与 mode 一致（或至少多锚 mode 冲突时 fail-closed），不静默取首个。

---

## T140: anchor_lint declared= 必填收紧的向后兼容/迁移

| 属性 | 值 |
|------|------|
| 模块 | `anchor_lint` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/mlh-p4-reason-code-validators/design.md`

**动机**：对抗镜冷审：check_hr_tg 令 declared 成必填字段，是对 hr-tg 锚 schema 的破坏性收紧无 grace。现存两个活跃 change 的 spec-review-report 带旧格式锚(hit=+evidence=无declared)，若被重 lint(--layer spec-review)会 exit1 阻塞。仅 low：实测无既有流程重 lint spec-review-report.md(code-review 只 lint code-review-report.md、done/verify 不重跑)，属过渡残留非活跃阻塞路径；转 consumer 仓若有旧报告落在重 lint 路径会硬失败。

**思路**：评估是否给 declared 一个迁移 grace（缺失降级警告而非硬失败），或确认旧报告不会被重 lint 后接受现状。

---

## T141: 融入 change 拆分标准进 workflow（三处触发）

| 属性 | 值 |
|------|------|
| 模块 | `workflow bundle (roadmap/ff/spec-review/implement/code-review)` |
| 类型 | 基础设施 |
| 状态 | OPEN |

**动机**：标准已入 memory[[change-scope-one-complete-stage-result]]+CLAUDE.md，但只约束我；进 bundle 才对所有跑此流程者生效。碎片化是「反复对现状提疑问+给妥协方案」的根因（grill hr-tg 实证：allow-legacy/grace/WARN 全是碎片化产物）。

**思路**：单一源 reference/change-decomposition-standard.md（4规则+why），三处引用不复制：①roadmap 拆分（sdflow-roadmap：每 phase/change=完整阶段结果，别拆散别混）②ff 定 change spec（ff-generation-constraints 切片建议+scope 内聚约束、spec-checklists BASE-18 分解检查、workflow.md:83 grill 调用 prompt 加 scope 内聚镜）③执行中发现（sdflow-spec-review/implement/code-review：相关 bug/todo 立即 fold，仅无关或缺失依赖模块才 defer+PLACEHOLDER+todolist blocked-on-missing-module 标签）。自指：本身作一个完整 change 一次做完、不拆碎、不混。

---

## T142: workflow-map.md 广度刷新（补 5 脚本 + hr-tg 三字段）

| 属性 | 值 |
|------|------|
| 模块 | `docs/workflow-map.md` |
| 类型 | 基础设施 |
| 状态 | OPEN |

**动机**：map 接地自 mlh-p5-parser-cleanup(mlh-p4 之前)已过时：§4「14 脚本」缺 hr_tg_intersect/outside_voice_guard/review_disposition_check/lens_metric_emit/maintain_scan；§3.2 hr-tg 锚仍写 hit+evidence 2 字段(应 hit+declared+evidence)。hr-tg schema 回灌那半由 harden-hr-tg-anchor-consistency 的 F12 局部处理，但补 5 脚本是独立广度刷新。

**思路**：按标准另开：不 fold 进 hr-tg change(基准②不混做)。随下次 map 维护统一刷 §4 脚本清单(14→19)+§3.2 hr-tg 三字段+§6 skew 风险展开。参考 docs/design-methodology.md §3 delta 表。

---

## T143: frozen-diff lint：frozen contract 有 diff 无新 ADR 关联报错（需 git 对比，超 v1 纯文件断言）

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-architecture` |
| 类型 | 功能增强 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/add-sdflow-architecture/design.md`

**动机**：design 状态机节目标态遗留

---

## T144: sad_schema 常量单向生成 JSON schema 工件（跨语言消费方出现时触发）

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-architecture` |
| 类型 | 基础设施 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/add-sdflow-architecture/design.md`

**动机**：DEC-1 被否备选的证伪条件登记

---

## T145: 观察 description 追加 SAD 指路句后的触发精度（架构类查询是否误触 roadmap）

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-roadmap` |
| 类型 | 可观测性 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/add-sdflow-architecture/design.md`

**动机**：code-review 对抗镜 held 项：路由语义无法本环境机械验证，试点期人工留意

---

<!-- sdflow-issue-block:start id=T146 -->
## T146: 扫描-max+1 无锁并发面统一：todolist.py/buglist.py 与 sad_scaffold 锁面方案对齐（O_CREAT+O_EXCL 仓级互斥）

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-skills 工具族` |
| 类型 | 代码质量 |
| 状态 | PROPOSED |

**关联文档**：`openspec/changes/add-sdflow-architecture/design.md`

**动机**：code-review T10 对抗复核确认老债与新 skill 同模式；sad_scaffold 已修（ce9b037 B8），姊妹脚本待统一

**备注**：老债非本 change 引入，per fold-vs-defer 判据合规 defer

> 2026-07 状态：PROPOSED → DONE（mlh-p6-recorder-frontmatter）
<!-- sdflow-issue-block:end id=T146 -->
---

## T79: P4·4.B maintain INDEX↔文件系统 set-diff 只读报告脚本化(+CLAUDE.md 过时引用+bundle 陈旧告警)；归哪组/是否修留人。纯机械集合求差、每次 maintain 都跑、dogfood 可测——目标态该做

| 属性 | 值 |
|------|------|
| 模块 | `sdflow-maintain + maintain_scan.py(新)` |
| 类型 | 代码质量 |
| 状态 | DONE |

> 2026-07 状态：PROPOSED → DONE（change mlh-p4-maintain-scan）

---

## T80: P4·4.D.1 outside-voice 复用守卫脚本化：锚 mode+时间戳+结构三判→reason_code 退出码

| 属性 | 值 |
|------|------|
| 模块 | `两审 outside-voice 小校验器(新)` |
| 类型 | 代码质量 |
| 状态 | DONE |

> 2026-07 状态：PROPOSED → DONE（change mlh-p4-reason-code-validators）

---

## T81: P4·4.D.2 HR-TG 交集判定脚本化：TG 集∩HR-TG 子集→hit 列表/none+规范锚串，清单从 trigger-catalog 单一源读(tg02_hit 先例)

| 属性 | 值 |
|------|------|
| 模块 | `两审 HR-TG 小校验器(新)` |
| 类型 | 代码质量 |
| 状态 | DONE |

> 2026-07 状态：PROPOSED → DONE（change mlh-p4-reason-code-validators）

---

## T82: P4·4.D.4 roadmap task-log『Review 处置』对账脚本化：parse 小节断言无『未处置』状态

| 属性 | 值 |
|------|------|
| 模块 | `roadmap 对账小校验器(新)` |
| 类型 | 可观测性 |
| 状态 | DONE |

> 2026-07 状态：PROPOSED → DONE（change mlh-p4-reason-code-validators）

---

## T147: openspec/workflow/ 下 v1 孤儿 debris：lens-metric-contract.md（无 host/reason_code）+ tools/anchor_lint.py（REQUIRED_FIELDS 缺 host）/lens_metric_emit.py（无 --host）/outside_voice_guard.py（:93 仍 runner!="codex" 裸判）均为 add-codex-host-support 改前的 v1 旧副本——非 pin 遮蔽（resolve-workflow.sh 因本地缺 workflow.md/spec-checklists/code-checklists 三个 pin 判据文件，判定非本地 pin，runtime 恒走全局 canonical ~/.sdflow/workflow）；待本仓自身跑 sdflow-init update 或手动清空该目录

| 属性 | 值 |
|------|------|
| 模块 | `openspec/workflow/` |
| 类型 | 基础设施 |
| 状态 | DONE |

> 2026-07 状态：OPEN → DONE（change add-codex-host-support; canonical tools sync 2026-07-16）

<!-- sdflow-issue-block:start id=T85 -->
## T85: P6 recorder 索引→frontmatter（**端态 A 已定 2026-07-08**）：用户拍板根治(YAML 转义使 `｜` 腐蚀类结构上不可能)否决 B(治标·永久守脆弱表·手编辑洞)。约束①历史文档不迁使成本≈P5 dual-read 成熟范式(新写 frontmatter+历史表冻结只读)。实现=改 3 recorder 写路径+consumer dual-read 读+测试套,压轴排 ★P4 后。A 删写侧(`_reject_cell_unsafe`/`_render_item_table`/双写表半场),历史读 `parse_table_rows` 冻结保留。理由全档见 roadmap P6 端态块
> P6 recorder 索引→frontmatter（**端态 A 已定 2026-07-08**）：用户拍板根治(YAML 转义使 `｜` 腐蚀类结构上不可能)否决 B(治标·永久守脆弱表·手编辑洞)。约束①历史文档不迁使成本≈P5 dual-read 成熟范式(新写 frontmatter+历史表冻结只读)。实现=改 3 recorder 写路径+consumer dual-read 读+测试套,压轴排 ★P4 后。A 删写侧(`_reject_cell_unsafe`/`_render_item_table`/双写表半场),历史读 `parse_table_rows` 冻结保留。理由全档见 roadmap P6 端态块
> 2026-07 状态：PROPOSED → DONE（mlh-p6-recorder-frontmatter）
<!-- sdflow-issue-block:end id=T85 -->

<!-- sdflow-issue-block:start id=T66 -->
## T66: recorder 效率:cmd_scan 对同批行双切(OV-1 arity+OV-3 dup)可合一次循环; batch rename 跑两次 read_pool(4子进程scan)可优化
> recorder 效率:cmd_scan 对同批行双切(OV-1 arity+OV-3 dup)可合一次循环; batch rename 跑两次 read_pool(4子进程scan)可优化
> 2026-07 状态：PROPOSED → DONE（mlh-p6-recorder-frontmatter）
<!-- sdflow-issue-block:end id=T66 -->

<!-- sdflow-issue-block:start id=T67 -->
## T67: 显式id前导零歧义:B007≠B7按字面共存不判重,语义同号两字面ID人工识别混淆(code-review对抗A置信55)
> 显式id前导零歧义:B007≠B7按字面共存不判重,语义同号两字面ID人工识别混淆(code-review对抗A置信55)
> 2026-07 状态：PROPOSED → DONE（mlh-p6-recorder-frontmatter）
<!-- sdflow-issue-block:end id=T67 -->

<!-- sdflow-issue-block:start id=T154 -->
## T154: actual Windows local-disk smoke 未执行验证（SW-RI-2 recorder lock 兼容目标，deferred）
> actual Windows local-disk smoke 未执行验证（SW-RI-2 recorder lock 兼容目标，deferred）

**关联文档**：`openspec/changes/mlh-p6-recorder-frontmatter/verify-report.md`

**动机**：SW-RI-2 把 Windows local FS 的 acquire/conflict/participant/replace/cleanup + setup copy 设为必须 smoke 的兼容目标；当前只有测试与 workflow 定义，macOS 上为 2 skipped，没有任何 Windows runner 执行锚，无法证明 Windows 行为通过（release blocker）

**思路**：在真 Windows 本地盘跑 `py -m pytest -q sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py -W error` 取无 skip 的 pass 锚；推荐走 GitHub Actions windows-latest（.github/workflows/windows-recorder-smoke.yml 已就绪，push branch 触发即可拿 run URL/commit/log）

**备注**：关联 change 显式传，勿让脚本误挂到其它活跃 change；取到 run URL 后回填 verify-report 并重跑 sdflow-done verify
> 2026-07 状态：OPEN → DONE（windows-latest run 29568476168 / commit ba004e1: 2 passed 无 skip）
<!-- sdflow-issue-block:end id=T154 -->

<!-- sdflow-issue-block:start id=T155 -->
## T155: 全仓 pytest -W error 常态化为持久 CI 守卫（防未来再引入未关闭文件/ResourceWarning 类存量债）
> 全仓 pytest -W error 常态化为持久 CI 守卫（防未来再引入未关闭文件/ResourceWarning 类存量债）

**关联文档**：`openspec/changes/mlh-p6-recorder-frontmatter/design.md`

**动机**：mlh-p6 tasks 7.3 是本仓第一次把 -W error 挂到全仓级别，一次暴露 4 处潜伏 7 天的 pre-existing 未关闭文件债；根因是历史所有 Change 的 -W error 只挂各自 scope 定向套件、全仓从无常态 -W error 门（.github/workflows/ 现仅有 Windows smoke、无任何全仓 pytest CI）。只修站点是点治，未立守卫则同类债会再潜伏到下一个偶然全仓跑 -W error 的 Change 才暴露。

**思路**：另开独立 hardening change：把全仓 pytest -W error 常态化为持久 CI 门（GitHub Actions job 或等价机制），设计触发条件、matrix、-W error 策略与覆盖范围，及与现有 windows-recorder-smoke.yml 的关系。属 mechanical-layer-hardening roadmap 同宗（机械层固化：一致性面焊死）。

**备注**：本条为 mlh-p6 收尾 fold 决策的 B 半（A 半=修 4 站点已 fold 进 mlh-p6 tasks 7.5）；本条明确不 fold、另开 change。change 字段填 mlh-p6 仅表 provenance（冒出地），不表示属于 mlh-p6 scope。
<!-- sdflow-issue-block:end id=T155 -->

<!-- sdflow-issue-block:start id=T153 -->
## T153: 更新 triage mutation docstring，移除已退役表格双写描述，改为 effective ownership、promotion 与 marker history 语义
> 更新 triage mutation docstring，移除已退役表格双写描述，改为 effective ownership、promotion 与 marker history 语义
> 2026-07 状态：OPEN → DONE（commit 27b77a7 (mlh-p6 fold): cmd_triage docstring 改为 frontmatter 批次/promotion/marker 语义）
<!-- sdflow-issue-block:end id=T153 -->

<!-- sdflow-issue-block:start id=T156 -->
## T156: sdflow-devenv 配 CI 的 P2 决策示范清一色 GitHub Actions、且未显式化「硬门/软门」降级边界——对「不管什么项目都能配」的承诺留了平台假设漏洞（用 workflow 的消费仓不一定在 GitHub）
> sdflow-devenv 配 CI 的 P2 决策示范清一色 GitHub Actions、且未显式化「硬门/软门」降级边界——对「不管什么项目都能配」的承诺留了平台假设漏洞（用 workflow 的消费仓不一定在 GitHub）

**动机**：sdflow-devenv 承诺「不管什么项目都能配 CI」（SKILL.md:3），地基本身已对——testing-framework.md:159-160 已确立「CI 只调本地同一条命令」＝平台无关；environments-template.md:253 亦承认「无 CI/纯本地门禁」为合法态。缺的不是原则而是两处：① 配 CI 的 P2 决策示范清一色 GitHub Actions（SKILL.md:29、references/testing-framework.md:84），无 GitLab/Gitea/自建 server/纯本地 hook 的对应模板 → 把模型与用户默认往 GitHub 引，下游非 GitHub 项目落不了地；② 未显式化「拦截强度分层」，用户会误以为门到处焊死、实则纯客户端 hook 可 --no-verify 绕过。

**思路**：另开独立增强（能力级，走自己的设计门，不并入 mlh-p6 / 本仓 T155）。两处补齐：(a) CI 载体模板按 git remote 探测分流——github→.github/workflows、gitlab→.gitlab-ci.yml、gitea/forgejo→.gitea/workflows、都不是/纯本地→pre-push hook 兜底；各载体只调 repo 内单一命令入口（make ci 或 hack/ci-check.sh），跑什么（如全仓 pytest -W error）是唯一真相源、载体只是薄适配（承 testing-framework.md:160）。(b) 把「拦截强度分层」写进 P2 决策清单并诚实标降级：平台原生 CI required-check / 服务端 pre-receive = 硬门（fail-closed，绕不过）；客户端 pre-push = 软门（可 --no-verify 绕，靠自觉+review 兜）；无 = 手动（sdflow-done verify 跑一次）。

**备注**：来源=mlh-p6 收尾「建全仓 -W error CI 门」设计问答的平台无关化延伸；用户拍板 (a)——本仓 T155 先走 GitHub Actions，本项留待 sdflow-devenv 独立增强。关联本仓 CI 门 T155。锚：sdflow-devenv/SKILL.md:3/:29、references/testing-framework.md:84/:159-160、references/environments-template.md:253/:283。
<!-- sdflow-issue-block:end id=T156 -->

<!-- sdflow-issue-block:start id=T162 -->
## T162: Codex 宿主方向的跨模型 voice efficacy=0：架构性无法离开关键路径，待 codex deferred_executor 稳定或外部 claude daemon 方案再议
> Codex 宿主方向的跨模型 voice efficacy=0：架构性无法离开关键路径，待 codex deferred_executor 稳定或外部 claude daemon 方案再议

**关联文档**：`openspec/changes/async-outside-voice/design.md`

**动机**：本 change 的 async 化只在 Claude 宿主成立（run_in_background 为 harness 原语）。Codex 宿主每条 shell 命令返回即回收该命令 spawn 的一切进程（nohup+setsid 皆秒死，spike 实证），无生产级后台原语 ⇒ Codex 方向的长跨模型 voice 架构性无法离开关键路径，只能同步阻塞 300s。add-codex-host-support 归档实测亦显示反向 claude -p outside-voice 在真实负载（300s + 10KB context）下全 timeout 回落同族、efficacy=0。∴ Codex 宿主上 outside-voice 的实际价值当前为零，但机制仍在跑、仍在花 300s。

**备注**：来源=async-outside-voice tasks.md §5.1（scope 外记账）。关联记忆锚：codex-reaps-spawned-processes-per-command、codex-a3-efficacy-real-load-timeout。本 change 已在 design Non-Goal 显式排除该项。
<!-- sdflow-issue-block:end id=T162 -->

<!-- sdflow-issue-block:start id=T163 -->
## T163: async host 调度段的 DRY 全抽取：把 marker 段抽成单一源注入两 SKILL，替代当前「两份副本 + 机械等值门」
> async host 调度段的 DRY 全抽取：把 marker 段抽成单一源注入两 SKILL，替代当前「两份副本 + 机械等值门」

**关联文档**：`openspec/changes/async-outside-voice/design.md`

**动机**：本 change §2.2 落的是「两份字节相同的副本 + check_async_branch_parity.py 机械等值门」——漂移会被当场拦红（已实证绿），故正确性已守住。但仍是两份副本：改一处必须同步改另一处，改动成本 ×2，且新增第三个消费方（如未来 codex 分支、或第三个评审层）时成本线性增长。等值门只保证「两份一致」，不消除「有两份」。

**备注**：来源=async-outside-voice tasks.md §5.2（明示超本 change scope、另立 change）。当前等值门已守漂移 ⇒ 本项是成本优化而非正确性修复，优先级可低。锚：hack/check_async_branch_parity.py、hack/sync_principles.py（idiom 先例）、两 SKILL 的 sdflow:async-branch marker。
<!-- sdflow-issue-block:end id=T163 -->
