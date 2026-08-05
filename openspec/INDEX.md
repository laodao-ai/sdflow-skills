# OpenSpec Index

本文件是当前仓库 OpenSpec 资产索引。

<!-- opsx-init:rules:start —— 由 sdflow-init 维护，勿手改本区块 -->
## OpenSpec 工作流规则（sdflow-init 维护）

> 本区块由 `sdflow-init` 维护——`openspec/workflow/` bundle 的规则索引。
> 新增/删 workflow 规则后重跑 `sdflow-init update`，或手动同步本表。

> 无本地规则副本的仓：下表文件位于全局 canonical `~/.sdflow/workflow/`，相对链接不可点，以文件名为准。

| 名称 | 文件 | 作用 |
|---|---|---|
| `workflow` | [workflow/workflow.md](./workflow/workflow.md) | 端到端流程总览（三阶段连续化）：生成(ff+grill)→设计审(sdflow-spec-review 编排器)→设计 GATE→实现+代码审+收尾(subagent-dev→sdflow-code-review→sdflow-done)；去 /clear、连续跑到 merge |
| `trigger-catalog` | [workflow/trigger-catalog.md](./workflow/trigger-catalog.md) | 「按内容条件触发」单一权威源 TG-01~24，驱动 约束/领域清单/画图/必填槽 四层 |
| `ff-generation-constraints` | [workflow/ff-generation-constraints.md](./workflow/ff-generation-constraints.md) | `opsx:ff` 起手强制：FF-0 开分支 + 生成硬约束 D-1~D-6 |
| `generation-process` | [workflow/generation-process.md](./workflow/generation-process.md) | 生成过程三相位：发散(explore)/收敛(brainstorming)/对抗压测(grill) |
| `design-diagrams` | [workflow/design-diagrams.md](./workflow/design-diagrams.md) | 设计/spec 阶段画哪些图、何时画、什么形态（C4 + 行为图，触发条件化） |
| `spec-review` | [workflow/spec-review.md](./workflow/spec-review.md) | spec 评审（Detection 层）：只做 prevention 残差，trigger 驱动 + 独立 + 读码核验 |
| `model-tiers` | [workflow/model-tiers.md](./workflow/model-tiers.md) | 模型档位映射（强/中/弱职责 + canonical 缺省 + config 覆盖语义） |

代码审规则集（`/sdflow-code-review` 用）：[workflow/code-checklists/](./workflow/code-checklists/)（base CR-01~09 + domains）。
说明类（可删不影响执行）：[workflow/reference/](./workflow/reference/)。
<!-- opsx-init:rules:end -->
### 设计规则

| 名称 | 文件 | 主题 |
|---|---|---|
| `doc-authoring` | [rules/doc-authoring.md](./rules/doc-authoring.md) | DOC-1：设计与决策文档正文只保留当前最终态；被否决方案、演进史和元教训移入附录，避免历史噪声误导后续实现与评审。 |
| `premise-verification` | [rules/premise-verification.md](./rules/premise-verification.md) | 写断言之前先验证其依赖的外部事实（落笔前证伪、引用即打开、改共享物先溯源、决策落文档前先验依赖、正反双向验证）。 |
| `file-format-convention` | [rules/file-format-convention.md](./rules/file-format-convention.md) | 文本文件编码统一 UTF-8、换行符统一 LF、尾行换行；`.editorconfig` + `.gitattributes` 双层保证。 |
| `script-punctuation-resilience` | [rules/script-punctuation-resilience.md](./rules/script-punctuation-resilience.md) | py/sh 脚本解析中文文档时的标点容错（中英文逗号/冒号/括号等变体同时匹配）。 |
| `context-exclusion` | [rules/context-exclusion.md](./rules/context-exclusion.md) | AI 上下文排除列表及理由（归档产物/impl-reports/草稿/缓存排除，活跃源码/spec/ADR 保留）。 |
| `question-discussion-convention` | [rules/question-discussion-convention.md](./rules/question-discussion-convention.md) | 禁 AskUserQuestion、多问题先总览再逐个讨论、编号格式。 |

### spec-workflow

| 名称 | 文件 | 主题 |
|---|---|---|
| `spec-workflow` | [specs/spec-workflow/spec.md](./specs/spec-workflow/spec.md) | spec 工作流三阶段（设计评审/代码评审/收尾归档）连续化的规范性行为：fresh 子代理替代 `/clear`、评审决策登记区、无人类门连续跑到 merge、verify 证据锚点、checkpoint 提交、bundle 权威源改动 |
| `host-adaptive-execution` | [specs/host-adaptive-execution/spec.md](./specs/host-adaptive-execution/spec.md) | 工作流跨 Claude/Codex 双宿主适配：`resolve-models.sh` 靠正信号判宿主（`CLAUDECODE=1`/`CODEX_THREAD_ID` 非空，两者皆无 fail-loud 落 `unknown`、不猜测）；outside voice 恒为另一机队强档（反向 `claude -p` 四旗只读全仓承重墙对称 codex）；两宿主 dispatch 均秒返（Claude-host harness `run_in_background`、Codex-host `claude --bg --exec` supervisor 后台 job）、内层 timeout 由 `outside-voice.async-timeout-seconds` 统一，能力不可用各自诚实同步/快速降级；`anchor_lint` 合法组合矩阵（跨模型/同族 fallback/无执行）为「跨模型性」唯一单一源，两工具各自重实现 + 全笛卡尔 golden 守漂移；出境安全三件套（secret_scan/FRAME/200KB 截断）两路径共用同一实现；模型档位按机队分列（`SDFLOW_TIER_*` 变量，eval 注入防护）；tools 陈旧探测 fail-loud 硬停在落锚之前；Codex 子代理不可用探针语义核验 + always-on 一致性 lint 缩 roster |
| `outside-voice-background-jobs` | [specs/outside-voice-background-jobs/spec.md](./specs/outside-voice-background-jobs/spec.md) | Codex 宿主跨模型 outside voice 经 Claude Code research-preview `claude --bg --exec` supervisor 托管为后台 job：per-site 独立 reservation/job/started/terminal/rc sidecar 原子发布、状态只从盘面不可变终态派生（`claude agents`/`logs` 仅作 liveness、MUST NOT 定状态）、barrier 有界 await（`outside-voice.async-timeout-seconds` 统一内层天花板）、复用 `outside-voice.sh exec` 四旗与出境安全三件套零降级、outer supervisor logs 不成第二出境面、终态 collect 后清理 supervisor roster 且失败可见（orphan warning）、abandoned run 只按显式 `reconcile --run-dir` 处理 |
| `workflow-metrics` | [specs/workflow-metrics/spec.md](./specs/workflow-metrics/spec.md) | 评审价值度量回路：`lens-metric v1` 结构化锚（layer/lens/runner/site 四元组）+ 只读可重生聚合（`sdflow-retro/scripts/lens_metric_aggregate.py`）+ per-镜数据驱动反馈，砍镜/降采样由人决不自动 |
| `lens-metric-emit` | [specs/lens-metric-emit/spec.md](./specs/lens-metric-emit/spec.md) | `lens_metric_emit.py`：从结构化 findings + 行键 roster 确定性归约出合规 `lens-metric` 锚行（折叠/归属/独立/sev-rollup 机械化，去重/裁决/定级仍归模型）；坏输入 fail-closed all-or-nothing，契约枚举/折叠单一源读取，不 import ship_gate/lens_metric_aggregate |
| `workflow-retro` | [specs/workflow-retro/spec.md](./specs/workflow-retro/spec.md) | `sdflow-retro` 只读再生全项目 change 成本×价值复盘：change 边界靠提交路径检测（非 tag 格式）、时间维仅到阶段级并诚实标注含人决策时间、价值维扫 active+archive 两源合并 spec/code 双报告锚、N≥10 待复评镜机械显著呈现、供数不供裁决 |
| `retro-report` | [retro/report.md](./retro/report.md)（`/sdflow-retro` 再生）| 全 change 成本×价值复盘活文档：git 提交阶段墙钟（成本维）+ lens-metric 锚聚合（价值维）合成 per-change 明细/阶段占比/成本双峰/per-镜价值表；view-only 再生，不做任何取舍决策 |
| `batch-triage` | [specs/batch-triage/spec.md](./specs/batch-triage/spec.md) | issues 池待处理项分诊三分类（相关合批/大扫除批/单开）：大扫除批硬边界（禁装逻辑面）+ issue 级 pre-diff fail-closed 判据（无自动兜底）+ 同类 Leg1 行为面路径守卫 + 聚合上限（MUST 有上限 + 生成物隔离）+ 一项一 commit 执行协议；本仓-local 不进 bundle |
| `determinism-guards` | [specs/determinism-guards/spec.md](./specs/determinism-guards/spec.md) | 机械层确定性守卫：`sdflow-issues` 三薄入口（`buglist.py`/`todolist.py`/`issues.py`）共享逻辑合一为唯一命名 package `sdflow_issues_core` 后，原三向/两向 AST 镜像一致性测试退役，改由「无 pool 分支守（AST 级）+ POOL_SPEC 封闭 schema 守 + 薄入口 thinness 同一性守」维持；`init.py config-lint`（手写 stdlib、条件化放行、fail-closed）、`issues.py batch lint`（优先级/计划占位符豁免 + 前导 token 后缀不校验）；direct↔scan golden 降级为「同源两 code-path 接线守」（不再宣称抓 rule 遗漏）；均只判机械可判的一致性/语法，不越权判内容 |
| `maintain-scan` | [specs/maintain-scan/spec.md](./specs/maintain-scan/spec.md) | `maintain_scan.py`：只读四类差异报告（specs/rules↔INDEX 双向 set-diff、CLAUDE.md 过时引用、workflow bundle 陈旧遮蔽告警、跨脚本判据一致性守卫）；INDEX 解析限表格行 + 链接目标路径 join-key、CLAUDE.md 引用改直查 fs 存在性、`.git` 精确剪枝、三处围栏未闭合 fail-closed（防假一致），零写文件，归组/是否修复留人 |
| `impl-orchestration` | [specs/impl-orchestration/spec.md](./specs/impl-orchestration/spec.md) | tickets 实现管线规范：手动路由三跳（config 键→plan marker→缺省 superpowers，零模型判断、损坏 marker fail-closed 停）、出 ticket 契约（tracer-bullet 垂直切片/Blocked-by/并行安全生成约束/外衣 `tickets.md`〔superpowers 轨保留 `superpowers-plan.md`，两名经共享 resolver 定位，双存在 fail-closed，D5/adr-0033〕/落盘即返回）、执行契约（frontier 宿主条件化受限并行〔Claude 宿主 worktree 隔离并行派发+逐票串行 merge，Codex/unknown 退化串行〕/后置双写+双信号核对/双轴审+注入点 B/halt envelope/文件交接）、机制裁剪边界（无 warm 终审/ledger/task-brief）、试点回退与熔断哨兵；ship_gate 零改动外衣兼容（adr/0017） |
| `roadmap-planning` | [specs/roadmap-planning/spec.md](./specs/roadmap-planning/spec.md) | `sdflow-roadmap` 分阶段规划工作流规范：三件套（design/roadmap/task-log）直写 `openspec/roadmaps/{name}/`（MUST NOT 走 OpenSpec 变更、MUST NOT 独立 requirements.md，存量四件套兼容）、design.md 需求与目标态伸缩头部章、与 sdflow-spec 同构的三相位结构（A 澄清 → B 七维拷问按 gate-0/商业化信号裁剪 + memo 增量落盘 → C 生成，第零步重入探测独立前置）、三态路由（gate-0 过∧无商业化信号直接生成 / gate-0 过∧信号命中裁剪到维度① / gate-0 未过按信号七维裁剪）、历史存档引用边界与存量 footage 冻结（memo 增量落盘 + 存量 footage 统称，三件套 MUST NOT 引用，存量包续跑兼容）、review 按商业化信号分档（plan-eng-review/autoplan）、收尾 checklist 四项软门、roadmap.md 近细远雾分层 |
| `hr-tg-intersection-check` | [specs/hr-tg-intersection-check/spec.md](./specs/hr-tg-intersection-check/spec.md) | `hr_tg_intersect.py`：吃模型判好的命中 TG 集（不自扫声明）与 HR-TG 子集求交，输出带「依据模型判定」的 `hit/none` + 规范锚（不 emit 裸 none，adr/0018）；HR-TG 清单从 trigger-catalog 单一源读（禁硬编码、禁 `__file__` 推导）；纯 stdlib、门控外置、坏输入/单一源损坏 fail-closed |
| `outside-voice-reuse-guard` | [specs/outside-voice-reuse-guard/spec.md](./specs/outside-voice-reuse-guard/spec.md) | `outside_voice_guard.py`：spec-review 复用 codex outside-voice 三前置（来源 mode/新鲜度 fs-mtime/结构 codex 段）按序归约唯一 reason_code（六枚举 none｜file-missing｜section-not-found｜zero-findings｜stale｜simulated-source）；新鲜度用源文件 fs-mtime 直比（排除评审产物自身）、纯 stdlib 无 subprocess、fence-aware 锚解析、坏输入 fail-closed |
| `outside-voice-exec-integrity` | [specs/outside-voice-exec-integrity/spec.md](./specs/outside-voice-exec-integrity/spec.md) | `outside-voice.sh`：截断切点 UTF-8 字符边界回扫（头段回退/尾段跳过 continuation 字节，只处理 UTF-8、不做通用编码嗅探）保证送出 prompt 恒合法；父进程被 SIGINT/TERM/HUP 回收时经组级 KILL 升级令 runner 子树随之终止（含自杀风险守卫与降级哨兵 `OV_GROUP_KILL_DEGRADED=1`）；诚实登记三类不可消除残余——父进程 SIGKILL 强杀（(a)）、PID 记录/回收窗口（(b)(c)）、以及高频×多类型混合信号风暴可整体击穿 trap 机制（D2.2 (d\*)，实测 67% 复现，登记为设计级残余、不宣称已根治） |
| `roadmap-review-reconcile` | [specs/roadmap-review-reconcile/spec.md](./specs/roadmap-review-reconcile/spec.md) | `review_disposition_check.py`：fence/结构感知断言 roadmap task-log `## Review 处置` 小节存在且非空，归约三枚举（section-missing｜section-empty｜section-ok-DISPOSITION-UNCHECKED）；不裸子串匹配「未处置」（防收尾声明句假阳）、逐条处置显式交模型（码尾缀 -DISPOSITION-UNCHECKED 防假绿）、坏输入 fail-closed |
| `architecture-design` | [specs/architecture-design/spec.md](./specs/architecture-design/spec.md) | `sdflow-architecture` 系统架构设计文档（SAD）编排规范：事实三问采集 fail-closed 锁 draft、十节骨架 + 重复锚/重名子系统检测、拆分规则集与反模式自检、假设/数值显影溯源（含畸形附录行检测）、文档状态机（`sad_scaffold.py` 唯一写路径，迁移前全量不变式复检 + 仓级互斥锁原子写）、冷走查（留痕存在性前置）与按信号升档、skeleton-ready 交棒切片建议节、ADR/术语分家落位、lint 结构通过≠语义核验诚实标注；空间轴能力，时间轴规划见 `roadmap-planning` |
| `devenv-provisioning` | [specs/devenv-provisioning/spec.md](./specs/devenv-provisioning/spec.md) | `sdflow-devenv` 过程轴环境搭建规范：三层（单元/集成/e2e）测试策略框架一层不许留白（结构骨架 fail-closed、内容留白只报不拦）、六槽逐层问（第⑤槽状态机械投影不问）、层状态由泳道**取最弱**投影（MUST NOT 手写，A29：一条绿不能染绿整层）、状态迁移证据只能由 `verify-lane`/`confirm-lane` 产出（`set-lane --status verified` 一律拒绝 exit 5）、执行「不伤害」边界（人门先行/超时/不 debug/不装依赖/不烧板）、落地物零解析 Makefile/shell（让工具自己判）、零删除能力、路径 containment 强制校验、数据模型零 digest 零封闭枚举（除 layer）、`testing-strategy.md`/`environments.md` 测试-非测试切线、lint 只报不拦代价可见、五步固定流程（核心承诺在②步）、冷审 vacuous 镜+盲区镜、独立 marker 注入、触发分工与 sdflow-init/roadmap/architecture 互不重叠 |
| `recorder-root-resolution` | [specs/recorder-root-resolution/spec.md](./specs/recorder-root-resolution/spec.md) | `sdflow-issues/scripts/` 下三薄入口（`issues.py`/`buglist.py`/`todolist.py`）`repo_root` 九步 fail-closed 校验序列（起点可信性→环境净化→调 git→最近 marker 上溯→git 失败裁决→形状校验→祖先校验→worktree marker→最近根一致）；回落判据是「上溯一层 marker 都找不到」而非「git rc≠0」；单进程内单点解析（`cmd_*` MUST NOT 重调）；三薄入口经共享 `sdflow_issues_core` 收敛为唯一物理源，一致性由「单一源 + thinness 同一性守」维持（原三向 AST 镜像断言已退役）；仓根 `conftest.py`+`pytest.ini` 两文件联合机械保证测试套件无 cwd 顶层副作用（hook wrapper 非 autouse fixture）；reindex 假绿防护。⚠️ 跨进程根分裂兜底当前不成立（B15，P1，`xfail(strict=True)` 锚死，修法待独立设计门） |
| `issues-scripts-shared-core` | [specs/issues-scripts-shared-core/spec.md](./specs/issues-scripts-shared-core/spec.md) | `sdflow-issues/scripts/sdflow_issues_core/` 唯一命名 package：三薄入口（`buglist.py`/`todolist.py`/`issues.py`）共享的执行逻辑单一物理源（`adr/0027`），承载 `repo_root`/pool 无关公共逻辑/`POOL_SPEC` 封闭 schema，薄入口经同目录 `from sdflow_issues_core import` 获得同一实现、禁 shadow |
| `spec-authoring` | [specs/spec-authoring/spec.md](./specs/spec-authoring/spec.md) | `sdflow-spec` 单一入口三相位管线（澄清/拷问/生成）取代原三分离入口（explore+ff+仓外 grill）：拷问前置为内建默认路径、决策纪要相位 B 内增量落盘、生成经 openspec CLI 完成态/合格态分开判定、终审核产物一致性；当前交付为**阶段一薄编排**（agent 定义外派因阶段二 A/B 验收门回退而未启用，保留为待激活资产） |
| `yq-yaml-operations` | [specs/yq-yaml-operations/spec.md](./specs/yq-yaml-operations/spec.md) | 7 个脚本（init.py/ship_gate.py/impl_route.py/anchor_lint.py×2/roadmap_writeback_draft.py/sad_schema.py）的 `config.yaml`/Markdown frontmatter YAML 子集解析统一委托外部 `mikefarah/yq` 二进制（adr/0036），业务判断留 Python 侧；`_yq()` 7 份内联封装由 golden test 守一致；记录在案的有界语法面例外——`init.py` schema 键读写（yq header-preprocess 数据丢失缺陷，保留既有正则）、`ship_gate.py` duplicate-key/tab-indent 预扫描、frontmatter 闭合性预扫描、`sad_schema.py` 行位置定位 |
