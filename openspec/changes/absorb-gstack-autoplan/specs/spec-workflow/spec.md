## ADDED Requirements

### Requirement: 阶段二自持广审并单批 dispatch 产出单一合并报告

阶段二 SHALL 由 `sdflow-spec-review` 编排器把**自持广审镜**与多镜评审合并产出**单一** `spec-review-report.md`,MUST NOT 要求人工手动合并多份报告。

广审 SHALL 由两个恒跑 fresh 子代理承载——**strategy 镜**(计划级战略审:前提站得住吗/范围校准/长期轨迹/后悔场景,过 base 清单计划级 R 项)与 **plan-eng 镜**(计划级工程审:架构耦合/错误路径完备/测试计划/隐藏复杂度,过 base 清单工程 R 项);raw 名 `strategy`/`plan-eng`,canonical 折叠 `broad`。二者 SHALL 只返回结构化 findings,**MUST NOT 原地修订四件套**——amendment 统一在 Step3 裁决后落盘并标 `[spec-review-amendment]`。广审镜与领域镜的分工线:base 清单 R 项归广审镜,`domains/` 栈特定 R 项归领域镜。

全部镜(广审/领域/对抗/接地)SHALL **单批并行 dispatch**(能力探针在 dispatch 前恒跑一次,结果对全部镜共用)——旧「领域/对抗镜等待广审先行并 checkpoint」的串行纪律随 autoplan amendment 环节退役而废止,`checkpoint(spec-review-autoplan)` 标签停产(历史归档标签仍被 retro 解析识别)。

`step1-broad-review` 锚保留,mode SHALL ∈ `{subagent, main-session}`:`subagent` = 广审镜正常派发;`main-session` = 探针判 `subagents="unavailable"` 时主 session 亲做广审(恒跑守卫,MUST NOT 因子代理不可用而跳过广审层)。

#### Scenario: 阶段二收尾
- **WHEN** 全部镜与 outside-voice collect 完成
- **THEN** 编排器输出一份已去重合并、含决策登记区的 spec-review-report.md,供设计 HARD-GATE 人工一次性评审

#### Scenario: 单批并行 dispatch
- **WHEN** 编排器完成规划镜头(TG 判定、镜 roster、能力探针)
- **THEN** 广审镜/领域镜/对抗镜/接地镜 SHALL 在一条消息内并行派出,MUST NOT 为广审设置前置 checkpoint 或让其它镜等待广审完成

#### Scenario: 广审镜不修订盘面
- **WHEN** strategy 或 plan-eng 镜发现设计缺陷
- **THEN** 该发现作为结构化 findings(问题/证据/置信/严重度/建议)返回,进 Step3 合并池同池裁决;子代理 MUST NOT 直接编辑四件套

#### Scenario: 子代理不可用时广审降级不缺席
- **WHEN** 能力探针判 `subagents="unavailable"`
- **THEN** 广审由主 session 亲做,锚记 `mode="main-session"`,`mirrors=` 计入 `broad`(合法降级);MUST NOT 静默跳过广审层;报告广审段 SHALL 显式声明「strategy/plan-eng 本轮由主 session 单一上下文亲做,为同源单一意见、非独立双检」——MUST NOT 以两栏分列呈现造成「两次独立交叉确认」的误读〔spec-review-amendment M11:main-session 路径的独立性损失须显著可见〕

#### Scenario: 广审镜个体 spawn 失败不与零发现同形〔spec-review-amendment M10〕
- **WHEN** 探针判 `subagents="available"` 但某个广审镜(strategy 或 plan-eng)个体派发失败/超出编排方时间预算未返回/返回不可解析内容
- **THEN** 编排器 SHALL 重试一次;仍失败则该镜由主 session 亲做**该镜职责**并在报告显式标注「<镜名> 个体失败,主 session 代做(非独立)」;MUST NOT 以空 findings + `mode="subagent"` 冒充该镜已独立跑过——「个体失败代做」与「独立跑过且 0 发现」MUST 在报告正文可区分(锚行文法不区分此二态,为既有诚实边界,区分义务在正文层)

## REMOVED Requirements

### Requirement: 阶段二产出单一合并报告

**Reason**: 该 Requirement 的执行序条款(领域/对抗镜等待 Step1 autoplan checkpoint、接地镜与 autoplan 并行、amendment 后不补跑接地镜)整体建立在「autoplan 原生执行并原地产 `[gstack-amendment]`」之上;autoplan 退役(ADR 0040)后广审镜只回 findings、不修订盘面,串行时序的存在理由消失。

**Migration**: 由「阶段二自持广审并单批 dispatch 产出单一合并报告」Requirement 承接——单一合并报告与决策登记区语义原样保留,执行序由「两段 dispatch」改为「单批并行」,广审载体由 autoplan 改为 strategy/plan-eng 恒跑子代理。

### Requirement: outside-voice 复用挂反静默守卫

**Reason**: 复用对象 `gstack-review.md` 随 Step1 自持化(autoplan 原生执行退役)不复存在,三前置守卫(来源/新鲜度/结构)失去判定物;C2「复用避双 codex」的成本前提(autoplan 每轮自带 codex 声)同时消失。

**Migration**: 设计侧 outside voice(design-voice)恒自跑——原守卫回落路径转正,调用协议(helper/超时/锚行/fallback)不变;`outside_voice_guard.py` 及其测试删除;`outside-voice` 锚的 `guard=` 字段从新锚文法移除(anchor_lint 不解析该字段,归档旧锚不迁移、无兼容影响)。独立 capability `outside-voice-reuse-guard` 整体退役见其自身 REMOVED delta〔spec-review-amendment〕。

### Requirement: 广审层原生执行，模拟必须显式标注降级

**Reason**: 本 Requirement 全篇钉死「autoplan 原生执行 + `gstack-review.md` 落盘 + mode ∈ `native|simulated`」——autoplan 原生执行随 ADR 0040 整体退役,`gstack-review.md` 环节删除,mode 枚举换代。〔spec-review-amendment M1:原 delta 漏此条,归档后将与新 ADDED Requirement 直接矛盾〕

**Migration**: 由本 change ADDED 的「阶段二自持广审并单批 dispatch 产出单一合并报告」Requirement 承接:广审载体=strategy/plan-eng 恒跑子代理,`step1-broad-review` 锚保留、mode 枚举 `subagent|main-session`,降级路径(主 session 亲做)显式标注义务原样保留。

### Requirement: gstack 边界守恒——读产出物合法、依赖内部禁止

**Reason**: 本 Requirement 的约束对象是「自制 voice 机制与 gstack 并存」的世界(读 `gstack-review.md` 合法、不碰 gstack 内部);gstack 运行时依赖全退役(ADR 0040)后边界对象消失——不再有任何路径读取 gstack 产出物或毗邻其内部。〔spec-review-amendment M1〕

**Migration**: 无承接。「无 codex 无 gstack 环境审查不中断」Scenario 的语义由既有 outside-voice fallback 条款(同族 fresh 子代理降级)独立承载,不依赖本 Requirement。

## MODIFIED Requirements

### Requirement: 跨模型 outside voice 默认开、失败回落且非阻塞

sdflow-spec-review 与 sdflow-code-review SHALL 默认启用跨模型 outside voice(**另一个机队**的「找漏」第二意见):sdflow-code-review 每次自带 code outside voice;**sdflow-spec-review 每次自带 design outside voice(design-voice 恒自跑——autoplan 产物复用路径已随 ADR 0040 退役)**〔spec-review-amendment M1:原文「复用 autoplan 产物中的 outside-voice findings」失效〕。

**runner MUST 由宿主决定，MUST NOT 硬编码**〔add-codex-host-support〕:runner 恒为**当前宿主之外的另一个机队的强档**(Claude 宿主 → Codex;Codex 宿主 → Claude)。`preflight` MUST 探测**目标 runner 的 CLI**,而非固定探测 codex——固定探测 codex 会在 Codex 宿主下返回 ready 并导致 **codex 自审 codex**,是必须杜绝的假绿。是否启用由环境决定——目标 runner CLI 未安装即天然关停(工作层不设软 off-switch,〔grill-amendment Q3〕);目标 runner 不可用(未装/未认证/报错/超时)时 MUST fallback 到同 prompt 的 fresh **同宿主**只读子代理,且该轮 `runner == host`(如实标为非跨模型);宿主判不出(`host="unknown"`)时 MUST NOT 跑 voice(无从确定"另一个机队")。一切失败均为 informational,MUST NOT 阻塞评审流程。

#### Scenario: spec-review 层 design-voice 恒自跑
- **WHEN** 一轮 sdflow-spec-review 进行至 outside-voice 环节
- **THEN** design-voice SHALL 无条件按调用协议自跑(无复用判定分支),站点集按 per-site 完整性声明落锚;失败按既有 fallback/锚行契约处理

### Requirement: workflow bundle 改在权威源、经部署下发

〔spec-review-amendment M1:仅一处改动——review 机械层脚本枚举中移除 `outside_voice_guard.py`(随 guard 退役);其余条文原样保留。〕

workflow bundle（`workflow/*.md` / `trigger-catalog.md` / `spec-checklists/` / `code-checklists/` / review 机械层脚本（`tools/`）/ hooks / checkpoint 脚本）与自制 skill 的改动 MUST 在权威源（sdflow-skills 的 bundle 公共家与 skill 目录）进行，MUST NOT 只改消费仓副本。部署 SHALL **按内容性质分层**，而非整 bundle 复制：

- **规则**（`workflow/*.md` + `spec-checklists/` + `code-checklists/`）MUST **不再复制进消费仓**，改由 skills 从全局 canonical bundle 解析（见「规则解析 resolver」需求）。
- **review 机械层脚本**（`tools/` 下 `anchor_lint.py` / `lens_metric_emit.py` / `hr_tg_intersect.py` / `review_disposition_check.py` / `trivial_shape.py` 等确定性脚本）MUST **不再复制进消费仓**，与规则同样由 skills 从全局 canonical bundle 解析（`$RULES_ROOT/tools/…`）。理由〔F49 限定〕：消费仓副本是 **bundle 拷贝链** skew 的成因（当前已知的主要 skew 来源），且它在 `global-canonical` 路径下从不被读取；取消复制即消灭**该类**问题（见 `adr/0039`）——该消除在完整 `git pull` + `bash setup.sh` 之后生效，不消灭 `~/.sdflow/hack/` 拷贝链与 Windows SKILL 快照的失鲜。`tools/` 下同样 MUST NOT 含任何 HTML 文档查看器资产（`engine.js` / `engine.css` / `vendor/` / `review-stub.html`）。**不再提供任何浏览器文档查看面**——`serve.sh` / `review.html` 及其查看器已从权威源整体移除；浏览 change / spec / roadmap 直接读 Markdown 文件。
- **人读手册 `WORKFLOW-GUIDE.md`** SHALL 仍复制进消费仓 `openspec/workflow/`——它**纯人读、不参与任何执行、不被任何脚本机读** ⇒ 结构上不可能 skew，陈旧无害；其价值正是「随仓走、不用跳文件」。它是消费仓 `openspec/workflow/` 下**唯一**的托管文件。

- **退役部署文件自愈**：`sdflow-init` MUST 维护一份**退役部署文件名单**（含曾铺进消费仓 `openspec/` 根的 `serve.sh` + `review.html`）并在 `init/update` 每次运行时对其**签名门控删除**——仅当目标文件内容含该文件的 bundle 部署签名（`review.html` 含 `__OPENSPEC_PROJECT_NAME__`、`serve.sh` 含 `openspec-review-serve-`）时才删，MUST NOT 删除不含签名的用户同名文件（防误删）。删除幂等、存量安装自愈、fresh 安装 no-op；机制与退役 hook 反注册同构（承 adr/0022 精神：只删自己确知铺设过的文件，不猜用户文件内容）。`tools/` 下的查看器资产不入该名单〔F27 订正〕——目标实现**不再触碰**消费仓 `tools/`（停铺后无整删重拷动作），存量仓残留的查看器资产与其它 tools 死件同类：由残留告警提示、人执行告警附带的删除命令一并清除，MUST NOT 依赖不复存在的整删重拷路径。
- **全局 Claude hook**（`~/.claude/hooks/` + 注册进 `~/.claude/settings.json`）集 SHALL = `{ff0-branch-guard}`（PreToolUse.Bash 的 FF-0 分支守卫）。`sdflow-init` MUST 维护一份**退役 hook 名单**并对其**反注册**（从 settings.json 各事件列表外科式摘除匹配条目 + 删除 `~/.claude/hooks/` 里的脚本，幂等、存量安装自愈、fresh 安装 no-op）；MUST NOT 只增不减而在存量安装留下指向已删脚本的孤儿注册。该反注册 SHALL 覆盖**两条更新路径**：① `sdflow-init init/update`（消费项目铺设路径，每次运行）；② `setup.sh`（工具链升级路径，装了 sdflow-skills 的机器经 `/sdflow-upgrade` 必跑、早于任何 `sdflow-init update`）。两路径 MUST 复用**同一** retire 逻辑（`init.py` 暴露独立 retire 子命令，`setup.sh` 调之），MUST NOT 各写一份。`setup.sh` 调用该步 SHALL **fail-safe**：解释器缺失或调用非零退出 MUST NOT 阻断 setup 安装（清理为尽力而为，非安装必要步）。fail-safe 构造 SHALL 以 `|| echo`/`|| true` 收尾〔A5〕——`set -e` 下仅 `command -v` 门控或 if-guard 不够（then-body 仍受 set -e，present-but-nonzero 会中止 setup）。解释器探测 SHALL `python3 || python`〔A6〕——MUST NOT 假设 `python3`（Windows/Git-Bash 常名 `python`，否则 Windows 机系统性漏 retire，T44 零收益）。全局 hook 的**安装侧**（`ensure_global_hooks` 装 ff0-branch-guard 等 PreToolUse.Bash 拦截钩子）MUST NOT 随之进 `setup.sh`〔grill-amendment·不对称原则〕——**清除主动伤害可 eager（retire 进 setup.sh），新增会拦截的能力须 opt-in（ensure 留 `sdflow-init init/update`，用户显式启用工作流时才装）**，MUST NOT 把拦截钩子推给仅安装 skill、不用 OpenSpec 的机器。
- **`checkpoint-commit.sh`** MUST 全局安装到 agent 中立的 canonical 根 `~/.sdflow/hack/`（**非** `~/.claude/hooks`——它是跨-agent bash 工具、非 Claude 事件 hook）、不再进消费仓 `hack/`。
- **`config.yaml` / `changes/` / `specs/`** 天然属仓，仍仓内。

消费仓不再持有规则或 `tools/` 副本，故不存在「采纳最新」的动作；`sdflow-init update` 对 `openspec/workflow/` 的职责收缩为**只铺 `WORKFLOW-GUIDE.md`**（`openspec/schemas/` 的 project-local schema 下发不受本条影响，它是 openspec CLI 的读取对象、非 workflow 规则）。`copy_bundle` MUST NOT 再复制 `tools/` 或 `lens-metric-contract.md`；随之，**`--dev` 整 bundle 刷新模式 SHALL 退役**——其唯一用途是给 toolkit 源仓铺一份 dogfood instance，而源仓此后同样从全局 canonical 解析，无需本地 instance。存量消费仓内既有的 `tools/` 与规则副本 MUST NOT 被自动删除（安全红线，见「迁移」需求），仅由告警提示其已无生效路径。

#### Scenario: 修改 workflow 规则
- **WHEN** 需要修改 workflow.md
- **THEN** 改 sdflow-skills 权威源 `sdflow-init/assets/workflow/workflow.md`（不提根，仍是唯一权威源），消费仓经全局 canonical 自动跟随 released HEAD，不直接编辑消费仓副本

#### Scenario: 新 init 的消费仓只含人读手册
- **WHEN** 对一个新项目跑 `sdflow-init init`
- **THEN** 消费仓 `openspec/workflow/` 下**只有 `WORKFLOW-GUIDE.md`**（规则文件数 = 0、`tools/` 不存在、`lens-metric-contract.md` 不存在）；`checkpoint-commit.sh` 全局安装、不进仓 `hack/`；`openspec/` 根不含 `serve.sh` / `review.html`

#### Scenario: 退役查看器根锚文件在存量安装被清理自愈
- **WHEN** 某存量消费仓曾被铺过查看器（`openspec/serve.sh` + `openspec/review.html` 存在且含 bundle 部署签名），随后跑 `sdflow-init update`（或 `init`）
- **THEN** update 删除这两个根锚文件（签名门控路径不变）；`tools/` 下的存量查看器资产（`engine.js`/`engine.css`/`vendor/`/`review-stub.html`）不被自动触碰〔F27：停铺后无整删重拷路径〕，与其它 tools 死件一并由残留告警提示、人按告警附带命令清除；对从未铺过查看器的 fresh 安装则全程 no-op

#### Scenario: 用户同名文件不被签名门控删除误伤
- **WHEN** 消费仓 `openspec/` 根存在用户自建的 `serve.sh`（内容不含 `openspec-review-serve-` 签名），随后跑 `sdflow-init update`
- **THEN** 退役清理**跳过**该文件（签名不匹配），用户的 `serve.sh` 原样保留，MUST NOT 因文件名相同而误删

#### Scenario: 退役 hook 在存量安装被反注册自愈
- **WHEN** 某存量安装曾装过 `change-review-stub.py`（`~/.claude/hooks/` 有脚本、`settings.json` PostToolUse.Bash 有其注册条目），随后跑 `sdflow-init update`
- **THEN** update 从 `settings.json` 外科式摘除该 hook 的注册条目（保留用户其余 hook）、删除 `~/.claude/hooks/change-review-stub.py`；此后每次 Bash 调用不再触发指向已删脚本的失败 hook；对从未装过该 hook 的 fresh 安装则全程 no-op、零告警

#### Scenario: 工具链升级路径 setup.sh 亦触发退役 hook 自愈〔T44〕
- **WHEN** 装了 sdflow-skills 的机器留有存量 `~/.claude/hooks/change-review-stub.py`（及其 settings.json 注册），随后走 `/sdflow-upgrade`（`git pull` + `bash setup.sh`）而**尚未**在任何消费项目跑 `sdflow-init update`
- **THEN** `setup.sh` 在 canonical/hack 刷新后调用 `init.py` 的 retire 子命令，复用同一 `retire_hooks()` 摘注册 + 删脚本；升级完成即自愈，无需等下一次 `sdflow-init update`；对无残留的机器则该步 no-op

#### Scenario: setup.sh 缺 python3 时 retire 步 fail-safe 不阻断安装〔T44 边界〕
- **WHEN** 在无 `python3`（或 `python3` 调用非零退出）的环境跑 `bash setup.sh`
- **THEN** retire 步被跳过并打印提示，`setup.sh` 的 skills 软链 / canonical 刷新照常完成、退出码不因 retire 失败而非零；退役 hook 清理留待有 python3 的路径（`sdflow-init update` 或下次可用的 setup）兜底

#### Scenario: setup.sh 只 eager 清退役、不推安装侧拦截钩子〔T44·grill 不对称原则〕
- **WHEN** 某机器仅为别的 skill 装了 sdflow-skills（跑过 `setup.sh`）、**从未**在任何项目跑 `sdflow-init init/update`
- **THEN** `setup.sh` 已 eager retire 掉存量死 hook（对谁都是主动伤害）；但 `~/.claude/hooks/` **不含** ff0-branch-guard（安装侧 PreToolUse.Bash 拦截钩子未被 `setup.sh` 推送）——ff0 仅在该机器显式 `sdflow-init init/update` 启用工作流时才装，MUST NOT 由 `setup.sh` 塞给不用 OpenSpec 的机器
