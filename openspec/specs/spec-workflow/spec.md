# spec-workflow Specification

## Purpose
把 spec 工作流三阶段（设计评审 / 代码评审 / 收尾归档）连续化的规范性行为固化为可验证需求：评审独立性由 fresh 子代理提供而非 `/clear`、评审决策登记进报告而非中途打断、阶段三过设计门后无人类阻塞门连续跑到 merge、verify 作为收尾终门须有可机验证据锚点、checkpoint 提交由显式收尾动作驱动、workflow bundle 改动须在权威源进行经部署下发。
## Requirements
### Requirement: 评审独立性由 fresh 子代理提供，不依赖会话重置

工作流 SHALL 通过 fresh-context 子代理 dispatch 获得评审独立性，MUST NOT 依赖 `/clear` 会话重置来隔离评审上下文，从而使评审阶段可连续自动运行。

#### Scenario: 设计评审无需先 /clear
- **WHEN** sdflow-spec-review 编排器在生成/grill 上下文之后运行
- **THEN** 它以 fresh 子代理 fan-out 领域镜/对抗镜/接地镜，主 session 无需先 `/clear`

#### Scenario: 代码评审无需先 /clear
- **WHEN** sdflow-code-review 编排器在 subagent-dev 实现之后运行
- **THEN** 它以 fresh 子代理 fan-out 各镜，主 session 无需先 `/clear`

### Requirement: 评审决策登记进报告，不中途打断

评审编排器 SHALL 把决策点（自动决策与需人拍板）连同选项、推荐、**决策后果**登记进评审报告，MUST NOT 在评审中途以 `AskUserQuestion` 打断，使一遍评审能自主跑到完成。

**决策后果 SHALL 按三镜展开**——系统镜（对系统本身：耦合 / 依赖 / 复杂度 / 可回退性）、用户镜（对最终用户使用：体验 / 可感知行为 / 干扰）、开发循环镜（对后续开发过程循环：心智负担 / 是否靠人 / 流程开销 / 复用性）——并 MUST 附**一句主次判定**（对当前这个决策，三镜哪个更重要、为何据此选定），MUST NOT 只罗列三镜后果而不判主次。触发深度 SHALL 分层：行为层每个决策都按三镜 + 主次分析；书面写入报告的三镜 + 主次 MUST 覆盖命中 TG-23（≥2 合理方案 / 非显然设计）的**方案选择**决策点，琐碎决策（无 ≥2 合理方案）SHALL NOT 被强制写满三镜段（避免样板税）。**「核验不了的事实」类决策点（Q2 事实核验）不属 TG-23，走「待核验证据 / 风险 / 默认处理」登记，不强制三镜**〔CV4：TG-23 定义仅 ≥2 方案，事实核验另类〕。

#### Scenario: sdflow-spec-review 遇到 ≥2 合理方案
- **WHEN** 某评审镜发现一个有 ≥2 合理方案的决策点（命中 TG-23）
- **THEN** 编排器把它写入 spec-review-report.md 决策登记区（选项 + 推荐 + 三面后果 + 主次判定）并继续，不中途弹 AskUserQuestion

#### Scenario: sdflow-code-review 自动选推荐项按三镜记理由
- **WHEN** 阶段三 code-review 按 T10 三级协议在 ≥2 方案中自动选定推荐项（有客观判据自动选 / 无则对抗镜复核 / 复核不过 defer；判据定义引主 spec T10 需求，本需求不重定义）
- **THEN** 记入 code-review-report.md 台账的理由 SHALL 按三镜 + 主次判定组织（与 spec-review 决策登记同口径），MUST NOT 只写一句主观理由

#### Scenario: 琐碎决策不被强制写满三镜
- **WHEN** 某决策点无 ≥2 合理方案（显然设计、单一可行路径）
- **THEN** 编排器 SHALL NOT 强制为其写满三面后果 + 主次判定段（书面三镜门只对命中 TG-23 的决策 MUST），避免样板噪声淹没报告

#### Scenario: 评审/grill 新发现工作走 fold-vs-defer 判据
- **WHEN** 评审 / grill 过程中发现当前 change 未覆盖的新需求或修复
- **THEN** 是否并入当前 change SHALL 按【对当前 change 工作的影响 + workflow 循环固定成本高】判——related 信号（紧耦合 / 一致性修复 / blast-radius 小）使其进入 fold 候选，候选再经**防吸积 AND 门（同 capability ∧ 高耦合 ∧ 低增量，三者皆满足）**才 fold 进当前 change、任一不满足则 defer 另开——此判定走三镜（开发循环镜通常主导），MUST NOT 反射式以「change 单一职责」教条拆分（拆 change 有一整轮循环固定成本）；判据成文于 BASE-18〔impl-review-fix F4/CV4：与 BASE-18 防吸积 AND 门口径一致，消除「任一即 fold」宽版二义〕

### Requirement: 阶段二产出单一合并报告

阶段二 SHALL 由 `sdflow-spec-review` 编排器串起 autoplan 与多镜评审并产出**单一** `spec-review-report.md`，MUST NOT 要求人工手动合并多份报告。**执行序 MUST 串行**〔T20〕：Step2 多镜 fan-out MUST 待 Step1 autoplan 完成并 checkpoint 之后启动，MUST NOT 与 Step1 并行——多镜的评审对象须包含 autoplan 的 `[gstack-amendment]` 改动；若历史运行已并行，Step3 裁决 MUST 对 autoplan amendment 做增量核对并在报告注明。

#### Scenario: 阶段二收尾
- **WHEN** autoplan 与 spec-review 镜均完成
- **THEN** 编排器输出一份已去重合并、含决策登记区的 spec-review-report.md，供设计 HARD-GATE 人工一次性评审

#### Scenario: 多镜等待 autoplan 先行
- **WHEN** sdflow-spec-review 执行 Step2 规划镜头时 Step1 autoplan 尚未 checkpoint
- **THEN** MUST 等待其完成后再 fan-out；MUST NOT 以"求快"并行化（评审对象缺 amendment = 丢失复审性质）

### Requirement: sdflow-code-review 为每次全跑的独立强制主审

阶段三的 `sdflow-code-review` MUST **每次必跑**、以独立冷视角作为强制代码评审主审（依据实测能抓真问题），MUST **恒产 code-review-report.md**，SHALL NOT 跳过代码评审、SHALL NOT 降级为「高风险才跑的残差抽查」（**默认开、仅机判无逻辑面才关**，非风险判断 gate-on）。深度按**两层**规则：

- **Step1（gstack/review：scope-drift + 计划完成度）MUST 每次必跑**，MUST NOT 因任何判定降级或跳过——既是便宜的评审地板，又是**验白名单形状诚实性的守卫**（自称无逻辑面的 diff 若偷藏逻辑改动，scope-drift 抓）。
- **Step2（多镜 fan-out：领域镜+对抗镜+历史镜+置信过滤+对抗裁决）MUST 对任何含行为/逻辑面的 change 每次全跑**；**仅当** change 的 diff **机判命中「无逻辑面白名单形状」**时可免 Step2（多镜结构上零产出）。免除 MUST 由 Step1 scope-drift 守卫：scope-drift 揭出隐藏逻辑 → 白名单判定作废 → Step2 照跑。

**无逻辑面白名单形状**（机判、post-diff、由确定性脚本判，MUST NOT 依作者自评）SHALL 仅含：①`diff 仅动代码内注释行（语言感知）或约定文档文件`——约定文档**扩展名锚定**：`VERSION` / `README·CHANGELOG·LICENSE·NOTICE`（无扩展或 `.md/.rst/.txt`）/ `.rst` / `docs/` 下 `.md·.rst·.txt`；**裸 `*.txt` 不算文档**（`requirements.txt`/`runtime.txt` 等依赖 pin 是 load-bearing，落 NOT）、**`docs/` 下 `.py` 等源码不算文档**（按代码判定）、**任意其他 `.md`（消费仓散落 markdown 可能承载行为）默认 NOT**；②`diff 仅新增 tests/ 下文件`（排除 import 副作用 `conftest.py`/`__init__.py`）；③版本常量收窄为 `VERSION`/`CHANGELOG`（代码里的 `API_VERSION`/`SCHEMA_VERSION` 无法机判是否切 code-path → NOT）。判器 MUST **语言感知**（按语言解析注释/块注释/多行字符串边界，MUST NOT 裸正则前缀）；MUST 应用**行为面路径豁免清单**——凡 diff 触及 workflow bundle 自身（`sdflow-init/assets/workflow/**`、编排/评审 `SKILL.md`、`ship_gate.py`、`route`/判器脚本、`workflow.md`）即 NOT 无逻辑面（**这些 markdown/脚本承载行为，非文档**），即便 diff 形状看似「仅动 markdown」；`tests/` 豁免 MUST 排除被生产码 import 的 test helper（如 `conftest.py`）；版本常量 MUST 整行匹配 `^\s*<IDENT>\s*=\s*<version-literal>\s*$` 且拒绝任何附加 token（防夹带 `API_VERSION`/`SCHEMA_VERSION` 等切 code-path 的 load-bearing 常量）。

#### Scenario: 有逻辑面的普通变更 Step2 多镜照跑
- **WHEN** 一个含逻辑改动的变更完成实现（不匹配任何白名单形状）
- **THEN** sdflow-code-review 的 Step1 与 Step2 多镜 fan-out 均 MUST 全跑，MUST NOT 因「routine/低风险」而免多镜

#### Scenario: 纯注释/文档 diff 免 Step2 但 Step1 恒跑
- **WHEN** 一个 diff 仅动注释/纯文档行（语言感知判定、且不触行为面路径清单）的变更
- **THEN** Step1（scope-drift+完成度）MUST 跑；确认无隐藏逻辑后 Step2 多镜可免（结构零产出），仍产 code-review-report.md

#### Scenario: scope-drift 揭穿伪装的白名单形状
- **WHEN** 某 change 自称「仅改注释」但 Step1 scope-drift 揭出顺手改了逻辑
- **THEN** 白名单判定 MUST 作废、Step2 多镜 MUST 照跑

#### Scenario: 改 bundle/SKILL/gate 自身即便是 markdown 也不免多镜
- **WHEN** 一个 diff 只改 `sdflow-code-review/SKILL.md` 或 `workflow.md` 一行指令（形状=仅动 markdown）
- **THEN** 判器 MUST 因行为面路径豁免清单判其 NOT 无逻辑面 → Step2 多镜照跑，MUST NOT 因「仅动 markdown」误免（bundle markdown 承载行为）

#### Scenario: load-bearing 版本常量不免多镜
- **WHEN** 一个 diff 改 `API_VERSION = 2` 或 `SCHEMA_VERSION`（切 code-path/契约）
- **THEN** 判器 MUST NOT 判其为白名单版本常量（其有 code-path 依赖）→ Step2 照跑

### Requirement: 阶段三过设计门后连续自动跑到 merge

阶段三 SHALL 在阶段二设计门之后无任何阻塞人类门地连续运行 `实现管线 → sdflow-code-review → sdflow-done`；实现管线为可选双轨——缺省 `writing-plans → subagent-dev`，或经 `impl-orchestration` 能力的手动路由（config 键 + 盘面 marker，缺省/非法值一律 superpowers）选择 `sdflow-implement 双模式（出 ticket → 执行）`；**编排层入口 = `/sdflow-ship`**（一次调用驱动 5.5→9，按「阶段三编排台账确定性」需求经 ship_gate 推进；手动逐步仍为合法 reference 路径）。管线选择 MUST NOT 引入模型自动判断，MUST NOT 新增人类门。实现管线内不可消解的 BLOCKED 停机属「defer-to-human 异常终态」而非人类门——与既有 BLOCKED_UPSTREAM 同构（停并上抛、人工再入口），不违背「无阻塞人类门」承诺（正常路径仍连续到 merge）〔spec-review-amendment F7〕。能修的自动修；**遇 ≥2 方案 MUST 按三级决策协议**〔T10，替换旧"有把握自动选"自评表述〕：①有客观判据（测试/断言/基准可判）→ 自动选并记理由；②无客观判据 → 派对抗镜复核推荐项，通过方自动选（复核记录进报告）；③复核不过或无从复核 → defer 进 buglist/todolist 并由 hand-off 引导另开 change 清理。MUST NOT 以自评置信（"有把握"）作为自动选定的唯一依据。修不了或需拍板的 MUST 进 buglist/todolist 延后。

#### Scenario: 修不了的问题延后而非阻塞

- **WHEN** sdflow-code-review 发现一个本 change 修不掉的问题
- **THEN** 它进 buglist/todolist(defer) 并写入 hand-off，流程继续跑到 sdflow-done，不设人类门阻塞

#### Scenario: 无客观判据的两方案走对抗复核

- **WHEN** 阶段三某步遇两个可行方案且无测试/断言可判优劣
- **THEN** 派对抗镜尝试证伪推荐方案：未被证伪 → 自动选并记复核记录；被证伪或复核无法开展 → defer，MUST NOT 凭"有把握"直接选

#### Scenario: 一次调用驱动到 merge 建议

- **WHEN** 对已过设计门的 change 调用 /sdflow-ship 且各步门禁全通过
- **THEN** 链依 gate 判定逐步推进至 sdflow-done 完成（含 merge 缺省语义），输出最终摘要；全程无 AskUserQuestion

#### Scenario: ship 零 git 写操作、merge 意图透传〔grill-amendment〕

- **WHEN** 用户以"跑到 merge 前停"类意图调用 /sdflow-ship
- **THEN** ship 将 opt-out 原样透传给 sdflow-done（merge 由 done 一处执行/跳过）；ship 自身 MUST NOT commit/merge/push，MUST NOT 自动 push（摘要提醒手动 push；toolkit 源仓附激活提示）

#### Scenario: 实现管线按手动确定值路由

- **WHEN** gate 判定 RUN_PLAN 且 config 键值为 `tickets`
- **THEN** ship 派发 sdflow-implement 出 ticket 模式；键缺省/非法/为 superpowers 时派发 writing-plans，行为与本变更前一致；CONTINUE_IMPL 一律按 plan 文件 marker 路由

### Requirement: verify 为收尾最终门，位于所有修复之后

`sdflow-done` 的 verify MUST 在本 change 全部修复之后运行作为最终完整性门，SHALL NOT 前移进 sdflow-code-review（否则修复后 verify 结果 stale）；verify 判 ✅ 的每条需求 MUST 附一个可机验证据锚点（测试名/commit/文件:行），无锚点的 ✅ MUST 降级为 gap。

#### Scenario: 修复后才 verify
- **WHEN** sdflow-code-review 及其修复循环全部完成
- **THEN** sdflow-done 先跑 verify（产 verify-report.md）再 archive

#### Scenario: 无证据锚点的 ✅ 降级为 gap
- **WHEN** verify 核对某条需求但找不到测试名/commit/文件:行等机验锚点
- **THEN** 该需求判为 gap（不得凭复选框或报告措辞判 ✅）

### Requirement: hand-off 交接产物替代人工核对清单

`sdflow-done` SHALL 在 verify 之后、archive 之前产出 `hand-off.md`（done/not-done + 延后项 + 下阶段建议）随归档留档，作为人类异步再入口与下个 cleanup change 的输入种子；MUST NOT 保留旧的人工核对清单 `code-review-verify.md`。

#### Scenario: 收尾产出 hand-off
- **WHEN** verify 通过
- **THEN** sdflow-done 生成 hand-off.md 并纳入归档

### Requirement: 每步提交由显式收尾动作驱动，不用 hook

工作流的 checkpoint 提交 MUST 由显式收尾动作（step prompt 追加指令 / 编排 skill 内置步）经共享脚本驱动，SHALL NOT 用 hook 驱动提交本身（hook 看不见逻辑步骤边界）；grill 多轮中途 MUST NOT 提交，仅收敛后一次。

#### Scenario: grill 收敛后才提交
- **WHEN** grill 多轮对话进行中
- **THEN** 不产生 checkpoint 提交；仅在 grill 收敛后一次性提交 design/ADR 更新

### Requirement: workflow bundle 改在权威源、经部署下发

workflow bundle（`workflow/*.md` / `trigger-catalog.md` / `spec-checklists/` / `code-checklists/` / review 机械层脚本（`tools/`）/ hooks / checkpoint 脚本）与自制 skill 的改动 MUST 在权威源（sdflow-skills 的 bundle 公共家与 skill 目录）进行，MUST NOT 只改消费仓副本。部署 SHALL **按内容性质分层**，而非整 bundle 复制：

- **规则**（`workflow/*.md` + `spec-checklists/` + `code-checklists/`）MUST **不再复制进消费仓**，改由 skills 从全局 canonical bundle 解析（见「规则解析 resolver」需求）。
- **review 机械层脚本**（`tools/` 下 `anchor_lint.py` / `lens_metric_emit.py` / `outside_voice_guard.py` / `hr_tg_intersect.py` / `review_disposition_check.py` / `trivial_shape.py` 等确定性脚本）SHALL 复制进消费仓 `openspec/workflow/tools/`（评审流程运行时依赖）。`tools/` 下 MUST NOT 再含任何 HTML 文档查看器资产（`engine.js` / `engine.css` / `vendor/` / `review-stub.html`）。**不再提供任何浏览器文档查看面**——`serve.sh` / `review.html` 及其查看器（`engine.*` / `vendor/` / `review-stub.html`）已从权威源整体移除；浏览 change / spec / roadmap 直接读 Markdown 文件。
- **退役部署文件自愈**：`sdflow-init` MUST 维护一份**退役部署文件名单**（含曾铺进消费仓 `openspec/` 根的 `serve.sh` + `review.html`）并在 `init/update` 每次运行时对其**签名门控删除**——仅当目标文件内容含该文件的 bundle 部署签名（`review.html` 含 `__OPENSPEC_PROJECT_NAME__`、`serve.sh` 含 `openspec-review-serve-`）时才删，MUST NOT 删除不含签名的用户同名文件（防误删）。删除幂等、存量安装自愈、fresh 安装 no-op；机制与退役 hook 反注册同构（承 adr/0022 精神：只删自己确知铺设过的文件，不猜用户文件内容）。`tools/` 下的查看器资产不入该名单——它们随 `tools/` 整删重拷（下方 `copy_bundle` 收敛语义）自动清除。
- **全局 Claude hook**（`~/.claude/hooks/` + 注册进 `~/.claude/settings.json`）集 SHALL = `{ff0-branch-guard}`（PreToolUse.Bash 的 FF-0 分支守卫）。`sdflow-init` MUST 维护一份**退役 hook 名单**并对其**反注册**（从 settings.json 各事件列表外科式摘除匹配条目 + 删除 `~/.claude/hooks/` 里的脚本，幂等、存量安装自愈、fresh 安装 no-op）；MUST NOT 只增不减而在存量安装留下指向已删脚本的孤儿注册。该反注册 SHALL 覆盖**两条更新路径**：① `sdflow-init init/update`（消费项目铺设路径，每次运行）；② `setup.sh`（工具链升级路径，装了 sdflow-skills 的机器经 `/sdflow-upgrade` 必跑、早于任何 `sdflow-init update`）。两路径 MUST 复用**同一** retire 逻辑（`init.py` 暴露独立 retire 子命令，`setup.sh` 调之），MUST NOT 各写一份。`setup.sh` 调用该步 SHALL **fail-safe**：解释器缺失或调用非零退出 MUST NOT 阻断 setup 安装（清理为尽力而为，非安装必要步）。fail-safe 构造 SHALL 以 `|| echo`/`|| true` 收尾〔A5〕——`set -e` 下仅 `command -v` 门控或 if-guard 不够（then-body 仍受 set -e，present-but-nonzero 会中止 setup）。解释器探测 SHALL `python3 || python`〔A6〕——MUST NOT 假设 `python3`（Windows/Git-Bash 常名 `python`，否则 Windows 机系统性漏 retire，T44 零收益）。全局 hook 的**安装侧**（`ensure_global_hooks` 装 ff0-branch-guard 等 PreToolUse.Bash 拦截钩子）MUST NOT 随之进 `setup.sh`〔grill-amendment·不对称原则〕——**清除主动伤害可 eager（retire 进 setup.sh），新增会拦截的能力须 opt-in（ensure 留 `sdflow-init init/update`，用户显式启用工作流时才装）**，MUST NOT 把拦截钩子推给仅安装 skill、不用 OpenSpec 的机器。
- **`checkpoint-commit.sh`** MUST 全局安装到 agent 中立的 canonical 根 `~/.sdflow/hack/`（**非** `~/.claude/hooks`——它是跨-agent bash 工具、非 Claude 事件 hook）、不再进消费仓 `hack/`。
- **`config.yaml` / `changes/` / `specs/`** 天然属仓，仍仓内。

消费仓的规则副本 SHALL 经 `sdflow-init update` 采纳最新（update 对规则为"停复制 + 陈旧遮蔽告警"，见「迁移」需求），MUST NOT 直接编辑部署副本。`sdflow-init` 的部署实现（`copy_bundle`）MUST 区分两种铺设模式：默认（消费仓）模式只拷 `tools/` 子树，且拷贝前若目的地 `tools/` 已存在 MUST 先整删再整拷（清后拷收敛），MUST NOT 用"存在则合并覆盖"语义（防上游删文件后消费仓残留孤儿文件）；`--dev` 整 bundle 刷新模式仅供 toolkit 源仓自身 dogfood 用，MUST 先校验 `--root` 解析后的真实路径等于本脚本所在 toolkit 仓根，不等则 MUST 拒绝执行（防误把整套规则灌进消费仓）。

#### Scenario: 修改 workflow 规则
- **WHEN** 需要修改 workflow.md
- **THEN** 改 sdflow-skills 权威源 `sdflow-init/assets/workflow/workflow.md`（不提根，仍是唯一权威源），消费仓经全局 canonical 自动跟随 released HEAD，不直接编辑消费仓副本

#### Scenario: 新 init 的消费仓不含规则副本
- **WHEN** 对一个新项目跑 `sdflow-init init`
- **THEN** 消费仓 `openspec/workflow/` 只含 `tools/`（仅机械层脚本，无 HTML 查看器资产），规则文件数 = 0；`checkpoint-commit.sh` 全局安装、不进仓 `hack/`；`openspec/` 根不含 `serve.sh` / `review.html`

#### Scenario: 消费仓 update 后 tools/ 收敛、不留孤儿文件
- **WHEN** 权威源 `assets/workflow/tools/` 删除了某个已废弃文件（如查看器 `engine.js`），消费仓随后跑 `update`
- **THEN** 消费仓 `openspec/workflow/tools/` 被整删重拷，废弃文件不再残留（MUST NOT 因 `dirs_exist_ok` 式合并覆盖而假装已同步）

#### Scenario: --dev 只许 toolkit 源仓自用
- **WHEN** 在某个消费仓（非 toolkit 源仓自身）误跑 `sdflow-init update --dev`
- **THEN** 脚本校验 `--root` 与 toolkit 仓根不一致，拒绝执行并报错，MUST NOT 把整套规则文件灌进该消费仓

#### Scenario: 退役查看器根锚文件在存量安装被清理自愈
- **WHEN** 某存量消费仓曾被铺过查看器（`openspec/serve.sh` + `openspec/review.html` 存在且含 bundle 部署签名），随后跑 `sdflow-init update`（或 `init`）
- **THEN** update 删除这两个根锚文件、`tools/` 下的查看器资产（`engine.js`/`engine.css`/`vendor/`/`review-stub.html`）随 `tools/` 整删重拷一并清除；此后该消费仓不再含任何查看器；对从未铺过查看器的 fresh 安装则全程 no-op

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

### Requirement: 债务池统一为 issues 结构且 INDEX 只生成

recorder 债务池 SHALL 统一为 `openspec/issues/{buglist,todolist}/` 结构，每个 item MUST 分**源change(provenance,不可变) / 批次(triage,可变) / status(生命周期)** 三维度记录；`issues/INDEX.md` MUST 只由 `reindex` 命令从各 dated 文件重建生成、禁止手改，SHALL NOT 成为独立的手维护真相源（杜绝第三漂移源）。

#### Scenario: reindex 从 dated 文件重建 INDEX
- **WHEN** 对 issues 池运行 `reindex`
- **THEN** 它从各 dated 文件（`buglist/` 按日、`todolist/` 按月）重建 `issues/INDEX.md`，摊清 open item × 批次并标出已闭合（终态）项，不读取也不信任任何手改的 INDEX 内容

#### Scenario: 三维度分家、status 回归干净
- **WHEN** 一个 item 被分诊到某清理批次
- **THEN** 批次写入独立的「批次」列，status 保持各 recorder 干净生命周期（bug: `OPEN→…→FIXED/WONTFIX`；todo: `OPEN→PROPOSED→DONE/WONTDO`）不被塞入批次，源change 维度保持不可变

### Requirement: 批次注册表与 reindex 被动同步状态

批次 SHALL 有第一类身份记录于 `issues/batches.md`（`PLANNED→IN_PROGRESS→DONE`，条目薄，批次 key = 清理 change 名）；每个 change 收尾时 sweep MUST 以 `源==本change` 为界只分诊本 change 新增的 OPEN 项入批次（源为空的孤儿项不归本次 sweep，交独立的通用 `--open-ungrouped` 清理流程处理）；`reindex` MUST 拿 item 池当 ground truth 同步批次状态——批次**成员数 ≥ 1 且全部进入各自 recorder 的终态集**（bug: `FIXED`/`WONTFIX`；todo: `DONE`/`WONTDO`，含 WONT\* 合法闭合）→ 批次判 `DONE`（0 成员批次 MUST 保持 `PLANNED`，防 vacuous-truth 假 DONE〔spec-review-amendment: D1〕），状态与成员不一致则标出纠正〔grill-amendment: B-Q1〕，MUST NOT 主动计算逾期或催办（改为被动摊清 + open 项下次清理自然纳入）。

#### Scenario: sweep 只分诊本 change 新增项
- **WHEN** 一个 change 在 sdflow-done 生成 hand-off 那步运行 sweep
- **THEN** 它把本 change 新增的 OPEN 项分诊入批次、在 `batches.md` 登记 `PLANNED`，并由 hand-off 引用；已在各自 change 分诊过的老项不被全量重诊

#### Scenario: reindex 同步批次状态且不主动催办
- **WHEN** 某批次的成员 item 全部进入终态集（`FIXED`/`WONTFIX`/`DONE`/`WONTDO`），但 `batches.md` 仍标 `PLANNED`/`IN_PROGRESS`
- **THEN** reindex 依 item 池把该批次同步为 DONE 并留完成日志；对未完成批次仅被动摊清 open×批次，MUST NOT 计算逾期或主动催办

#### Scenario: 0 成员批次不被 vacuous 判 DONE〔spec-review-amendment: D1〕
- **WHEN** 一个批次已 `batch add` 登记（PLANNED）但尚无任何 item 打上其批次 tag（成员数 = 0）
- **THEN** reindex MUST 保持该批次 `PLANNED`，MUST NOT 因"全部成员进终态集"对空集永真而判 DONE

### Requirement: 规则全局解析 resolver（本地优先 → 全局兜底 → 显式降级）

skills（sdflow-spec-review / sdflow-code-review / sdflow-done / sdflow-buglist·todolist·issues / opsx-ship〔待其 change 落地〕）读取 workflow 规则 MUST 走统一三步 resolver：① 仓内**有规则文件本体**（`workflow.md` / `spec-checklists/` / `code-checklists/`）→ 用本地；② 否则 → 全局 canonical bundle；③ 全局也缺 → **显式降级**通用评审并告警，MUST NOT 静默当"无此层"。步①的存在判据 MUST 查**规则文件本体**、MUST NOT 查 `openspec/workflow/` 目录（`tools/` 使该目录在每个仓恒存在，查目录会令每个消费仓误命中本地 pin）。步②的 canonical 解析 MUST 平台无关回落：先试 `~/.sdflow/workflow/`（Unix 软链目录，透明），否则读 `~/.sdflow/workflow-path`（Windows 指针文件）取 bundle 路径。步③的"显式降级 + 告警"即 CONTEXT 术语『反静默守卫』的缺失面（见 `adr/0003`）。

〔model-baseline-amendment / `adr/0006`〕上述三步链 MUST 由确定性脚本 **`~/.sdflow/hack/resolve-workflow.sh`** 实现（stdout = 规则根路径；全局缺失 → 非零退出 + stderr 固定告警文案）。skills MUST 通过调用该脚本解析规则路径，MUST NOT 把三步链作为指令文本交由执行模型逐步照做（执行机队 = opus/sonnet/gpt-5.5 机队锚定，prose 协议在弱档模型上的失效形态 = 静默跳步）；调用方 MUST NOT 静默吞脚本非零退出码。

〔spec-review-amendment〕契约补强：步① 判据粒度 MUST 为 **any-of**（三顶层单元任一存在即判本地 pin），部分残留时 MUST 输出专门告警（提示补齐或删净），MUST NOT 隐式选择 any/all 语义；脚本 MUST 支持 `--root <仓根>`（缺省 `git rev-parse --show-toplevel`）与 `${SDFLOW_HOME:-$HOME/.sdflow}` 环境覆盖（测试隔离）；步② 命中后 MUST 做最小健全性检查（`workflow.md` 非空 + `spec-checklists/`、`code-checklists/` 两个清单目录均非空，`sane()` 判据，不过检按缺失处理）；调用方 MUST 先以 `[ -x ]` 判脚本自身存在——脚本缺失（未跑 setup）与步③ bundle 缺失是**两个不同告警**，MUST NOT 混同。

〔impl-review-fix / 935eb42〕退出码与入参校验契约：脚本 MUST 用 **exit 64** 标记用法错误——`--root` 缺值、`--root` 后紧跟形如 `-*` 的疑似 flag 值、未知参数，以及**默认 cwd 解析失败**（`git rev-parse --show-toplevel` 与 `pwd` 均失败，如 cwd 已被删除）且未显式传 `--root` 兜底的场景；MUST 用 **exit 2** 标记全局 bundle 不可达/不完整（步③降级）；MUST 用 **exit 0** 标记解析成功（本地 pin 或全局 canonical）。`SDFLOW_HOME` MUST 校验为绝对路径，非绝对路径 MUST 告警并忽略该值（不参与步②解析，直接判全局不可达），MUST NOT 静默当相对路径拼接使用。

#### Scenario: 迁移期部分残留判 pin 且告警
- **WHEN** 某消费仓 `openspec/workflow/` 只残留 `spec-checklists/`（`workflow.md`、`code-checklists/` 已删）
- **THEN** resolver 按 any-of 判本地 pin（stdout=本地路径），同时 stderr 输出部分残留专门告警（补齐或删净）；MUST NOT 静默混合解析、MUST NOT 静默落全局

#### Scenario: 消费仓无本地规则副本走全局
- **WHEN** 一个消费仓 `openspec/workflow/` 只有 `tools/`、无规则文件，skill 要读 workflow.md
- **THEN** resolver 步① 未命中（有 tools/ 目录但无规则文件）→ 落步② 从全局 canonical bundle 解析，跟随 released HEAD

#### Scenario: toolkit 源仓与显式 pin 命中本地
- **WHEN** toolkit 源仓（自身有 `openspec/workflow/` 规则 dogfood 副本）或某消费仓显式保留了本地规则副本，skill 要读规则
- **THEN** resolver 步① 命中本地副本（无需任何"我是源仓"config flag——本地副本存在即声明），源仓 dogfood 吃在用端而非未发布编辑

#### Scenario: 全局缺失显式降级不静默
- **WHEN** 仓内无规则副本且全局 canonical bundle 也不可达
- **THEN** skill MUST 降级为通用评审并**显式告警**缺失，MUST NOT 静默当作"本项目无此评审层"

#### Scenario: canonical 解析平台回落
- **WHEN** skill 在 Windows 上解析全局 bundle（平台无软链）
- **THEN** 先试 `~/.sdflow/workflow/` 目录未果 → 回落读 `~/.sdflow/workflow-path` 指针取 bundle 路径；Unix 上则 `~/.sdflow/workflow/` 软链目录直接命中（透明）；平台判断发生在 `resolve-workflow.sh` 内，skill 不判平台

#### Scenario: resolver 由脚本执行而非模型 prose
- **WHEN** 任一 skill 在任一执行模型（opus / sonnet / gpt-5.5 等）上需要解析规则路径
- **THEN** 它调用 `~/.sdflow/hack/resolve-workflow.sh` 并使用其 stdout 路径；脚本非零退出时 skill 显式降级并转发脚本告警文案，不自行在指令内重实现三步链

#### Scenario: cwd 已被删除且未传 --root
- **WHEN** 调用方在一个已被删除的工作目录下调用脚本、且未显式传 `--root`
- **THEN** `git rev-parse --show-toplevel` 与 `pwd` 均解析失败，脚本以 **exit 64** 报用法错误并提示改用 `--root` 显式指定，MUST NOT 静默回退到某个猜测路径

#### Scenario: --root 后紧跟疑似 flag 值
- **WHEN** 调用方写成 `resolve-workflow.sh --root --explain`（漏填 `--root` 的值，误把下一个 flag 当值）
- **THEN** 脚本识别 `-*` 形态并以 **exit 64** 拒绝，MUST NOT 把 `--explain` 当路径字符串误吞

#### Scenario: SDFLOW_HOME 非绝对路径
- **WHEN** 环境变量 `SDFLOW_HOME` 被设为相对路径（如 `.sdflow`）
- **THEN** 脚本告警并忽略该值、直接判全局 canonical 不可达（落步③显式降级），MUST NOT 拿相对路径去拼目录再静默探测

### Requirement: 存量消费仓迁移不自动删、陈旧遮蔽须告警

`sdflow-init update` 对存量消费仓的规则副本 MUST 改为"停止复制"，MUST NOT 自动删除仓内既有规则文件（安全红线 + 免分辨源/消费仓 + 老仓平滑迁移）。当检测到仓内残留的旧规则文件**遮蔽**全局 canonical bundle 时，`sdflow-init` MUST **显式告警**（说明它遮蔽全局且不再被刷新，删=跟全局 / 留=显式 pin），MUST NOT 静默让其陈旧。此告警即 CONTEXT 术语『反静默守卫』的**陈旧遮蔽**变体（元原则清单已补“悄悄用了旧的”，见 `adr/0003`）。

〔spec-review-amendment / impl-review-fix 935eb42〕告警触发点 = **`init` 与 `update` 两种模式均内联检测**（同一判据函数：新项目 fresh init 自然零残留、零告警；老仓被误当新项目跑 `init` 时也不因模式不同而假绿放过残留）+ **`sdflow-maintain` 兜底扫描**（覆盖常年不跑 `init`/`update` 的仓）；检测范围 MUST 同时覆盖旧版仓内 `hack/checkpoint-commit.sh` **孤儿副本**（checkpoint 全局化后不再被任何机制刷新），并给对称提示（删=用全局 / 本地 workflow.md 副本仍引用它则勿删）。

#### Scenario: update 不删残留规则、给出遮蔽告警
- **WHEN** 一个 pre-change 的存量消费仓（已有 ≈28 规则副本）跑 `update`
- **THEN** update 只刷 `tools/`、保留旧规则文件不删，并告警"这些规则遮蔽全局且不再更新——删=跟全局最新 / 留=显式 pin"

#### Scenario: 老仓被误当新项目跑 init 同样告警
- **WHEN** 一个已有陈旧规则残留的存量仓被误跑了 `init`（而非 `update`）
- **THEN** 陈旧遮蔽检测同样触发（判据与 `update` 共用），MUST NOT 因跑的是 `init` 模式而假绿放过残留（B2-F3）

#### Scenario: 留旧副本仍能跑（pin 逃生口）
- **WHEN** 用户读到告警后选择保留本地规则副本
- **THEN** 该仓 resolver 步① 继续命中本地副本、照旧能跑（即显式 pin 行为），不因 change 而丢功能

### Requirement: skill 命名与品牌一致性

工具链自制 skill MUST 统一使用 `sdflow-` 前缀命名（目录名 = 安装名 = 斜杠命令名）；合一后台账类 skill 收敛为单一 `sdflow-issues`，`sdflow-buglist`/`sdflow-todolist` 已删除。

> `[spec-review-amendment]`（`dedupe-issues-scripts-shared-layer`）：原 requirement 的 sdflow- 前缀枚举含
> `sdflow-buglist`/`sdflow-todolist` 为独立 skill，且「sibling 脚本路径随名迁移」Scenario 假定 `issues.py` 上溯
> SKILLS_ROOT 后 join **sibling 目录** `sdflow-buglist`/`sdflow-todolist`。三 skill 合一为 `sdflow-issues`（`adr/0027`）后：
> ① 枚举中 `sdflow-buglist`/`sdflow-todolist` **删除**（并入 `sdflow-issues`）；② sibling-spawn 改为**同目录**定位。
> 命名规范其余部分（前缀约束、豁免名单、触发等价、trigger-map 留档）不变。

工具链自制 skill MUST 统一使用 `sdflow-` 前缀命名（目录名 = 安装名 = 斜杠命令名），按 RENAME-MAP（design §三）执行。
**RENAME-MAP 随本次台账合一更新**：原 map 中的 `sdflow-buglist`/`sdflow-todolist` **从 map 移除**（两 skill 删除、并入
`sdflow-issues`），map 台账项收敛为单一 `sdflow-issues`（owns 两池 + 跨池）；RENAME-MAP 其余项不变。
（注：RENAME-MAP 是那次改名 change 的映射子集、**非现役 skill census**——map 之后新增的 skill 如 `sdflow-architecture`/
`sdflow-devenv`/`sdflow-implement`/`sdflow-retro`/`sdflow-ship`/`sdflow-upgrade` 本就不在 map 内、不受本条约束。）
豁免保留名单 = `embedded-test-sop`（域技能）、
`openspec-upgrade`（升级外部 CLI）、`sdflow-upgrade`。主 spec 与功能性文件全文中的旧 skill 名 SHALL 随合一同步替换
（语义不变）；文档性历史记录（`adr/`、ROADMAP 历史行、CONTEXT 术语史、`changes/archive/`、`setup.sh` 的
`OUR_LEGACY_NAMES` 孤儿清理名单）MUST NOT 回改。各 SKILL.md 的 description MUST 触发等价：合并前分属两 skill 的触发
场景语句集（如「记一下这个 bug」「记个 TODO」）SHALL 全部保留、并入 `sdflow-issues` 单一触发面。

#### Scenario: 目录名与斜杠命令一致切换

- **WHEN** 合一完成并在运行 checkout 重跑 `setup.sh`
- **THEN** `~/.claude/skills/` 与 `~/.codex/skills/` 下存在 `sdflow-issues`、**不存在** `sdflow-buglist`/`sdflow-todolist`（旧名 dangling 链被孤儿清理收走，MUST NOT 残留）

#### Scenario: 触发等价不回退（并入单一触发面）

- **WHEN** 用户说出合并前即可触发某台账 skill 的语句（如「记一下这个 bug」「记个 TODO」）
- **THEN** 该语句仍触发 `sdflow-issues`（bug↔todo 分池分类由模型在 skill 内按「坏了没」判）；合并前两 skill 的触发短语集全部保留

#### Scenario: sibling 脚本路径改同目录

- **WHEN** `sdflow-issues` 的 `issues.py reindex`/`sweep` 需要子进程调用兄弟脚本
- **THEN** 它按**同目录**（`os.path.join(SCRIPT_DIR, "buglist.py")`）join 路径并成功调用，**MUST NOT** 再上溯 SKILLS_ROOT 后 join 已删除的 sibling 目录 `sdflow-buglist`/`sdflow-todolist`；`sdflow-done` 引用的脚本固定路径同为 `sdflow-issues/scripts/`

### Requirement: 安装器品牌标识与存量 marker 兼容

`setup.sh` MUST 以 `sdflow-skills v<VERSION>` 标识输出（`VERSION` 文件为版号真相源，起始 `0.9.0`）；Windows copy 模式的 marker 文件 MUST 新写为 `.sdflow-skills`，且所有权判定对存量 `.laodao-skills` marker 的兼容 MUST **以名单为界**〔spec-review-amendment D5〕：仅目录名 ∈ RENAME-MAP 旧名∪新名∪保留名单时识别为自属可刷新（源已亡则按孤儿清理），名单外一律视为非自属 skip，MUST NOT 全量兼容（防误伤 laodao 旧仓 misc 拷贝）。

#### Scenario: 存量 laodao marker 仍被识别为自属
- **WHEN** 某 Windows 机器上存在旧版安装的 skill 拷贝（含 `.laodao-skills` marker），重跑新版 `setup.sh`
- **THEN** 该拷贝被识别为自属 → 正常刷新并换写 `.sdflow-skills` marker；MUST NOT 走"非本工具产物"skip 分支

#### Scenario: 版本标识来自 VERSION 文件
- **WHEN** 运行 `bash setup.sh`
- **THEN** 摘要首行输出 `sdflow-skills v0.9.0`（或当前 VERSION 内容）；VERSION 缺失时显式 `vunknown`，MUST NOT 伪造版号

#### Scenario: marker 兼容以名单为界、不误伤他仓财产〔spec-review-amendment / autoplan F8〕
- **WHEN** Windows 机器上同时存在 laodao-skills 旧仓自装的 misc skill 拷贝（带 `.laodao-skills` marker，目录名不在 RENAME-MAP∪保留名单内）
- **THEN** sdflow 的 setup.sh 视其为**非自属** → skip 不刷不删；仅名单内目录的旧 marker 被识别为自属并迁移为 `.sdflow-skills`

### Requirement: 托管区块 marker 迁移兼容〔spec-review-amendment〕

`sdflow-init` 的托管区块注入（`inject()`）MUST 以**令牌行**（`opsx-init:start` / `opsx-init:rules:start` 等 token）定位既有区块，MUST NOT 依赖含 skill 名的 marker 全文精确匹配；改名后对含旧 marker 文案（"由 opsx-project-init 维护"）的存量消费仓执行 `update`，MUST **替换**原区块（新 marker 文案随之更新），MUST NOT 追加重复区块或使旧区块失管。

#### Scenario: 存量旧 marker 区块被替换而非重复追加
- **WHEN** 一个消费仓 CLAUDE.md 含旧 marker 文案的托管区块，跑新版 `sdflow-init update`
- **THEN** 该区块被原位替换为新名内容（token 定位命中），文件中托管区块数量仍为 1；MUST NOT 出现两个 opsx-init 区块并存

#### Scenario: 跨改名孤儿链真实可清
- **WHEN** 本机存在指向已改名目录的 dangling 自属软链，在 canonical checkout 重跑 `setup.sh`
- **THEN** 该链被 `cleanup_orphans` 枚举到并清除（枚举方式 MUST 覆盖 dangling 软链——尾斜杠 glob 不满足此要求）；新名链同轮建立

### Requirement: 阶段三编排台账确定性（ship_gate）

`sdflow-ship` 的步序推进 MUST 由确定性脚本 `ship_gate.py` 判定（**盘面即状态**：以 change 目录产物存在性与结论行为账本，MUST NOT 设可变 state 文件造第二真相源）；编排 skill MUST 在每步前后调用 gate 并遵其判定，MUST NOT 以 prose 记忆步序。gate MUST 只读（零副作用）、双输出（首行人读摘要 + JSON 机读）、以退出码承载门禁语义（0=可推进 / 3=拒绝起跑 / 4=上游 blocker / 5=verify FAIL / **6=UNKNOWN 判定不能**〔spec-review-amendment〕）；同一报告并存冲突结论 MUST 判 UNKNOWN 点名冲突，MUST NOT 猜优先级。

**机判结论的承载形态按报告位置分流（mlh-p5：去字符串化家族①，inline 锚 → frontmatter）**：

- **live 报告（`openspec/changes/{change}/*.md`）MUST 以报告 YAML frontmatter 承载结论状态**，schema 在 `ship-gate:` 顶层键下：设计门拍板 = `design_approved: true`（spec-review-report.md）；verify 结论 = `verify: PASS` / `verify: FAIL`（verify-report.md）；code-review 放行 = `code_review: pass` / `code_review: blocked`（code-review-report.md）。每报告 MUST 只落自己那一类字段。三报告的生成模板（sdflow-spec-review 拍板回写约定 / sdflow-done verify 模板 / sdflow-code-review 报告格式）MUST 在 frontmatter 输出对应字段。gate 对 live 报告 MUST 解析 frontmatter（`ship_gate.py` 自持的 frontmatter 解析路径）读结论：字段值 MUST 按严格枚举校验（`verify ∈ {PASS,FAIL}`、`code_review ∈ {pass,blocked}`、`design_approved` 为 bool）。**结论承载态按盘面精确分流两类，MUST NOT 混为一谈**〔mlh-p5-parser-cleanup 澄清〕：**(a) absent（无有效 frontmatter block / 顶层无 ship-gate 键）→ 既有无锚语义**（design→REFUSE_START、verify/code-review→步进行中；MUST NOT 静默当已过门）；**(b) 首块成立但内容坏（字段越域 / 同字段重复键 / 坏 YAML 语法 / tab 缩进 / 类型不符）→ fail-closed 判 UNKNOWN(6)**（歧义须人裁）。**「首行 `---` 无闭合（无第二个 `---`，首块不成立）」归 (a) absent，MUST NOT 归 (b) 坏**——无闭合 `---` 不构成 frontmatter block（与下方 A2「只认首块」的首块定义自洽），是正文/markdown 横线。**报告正文对锚字面的任何提及（描述句、对账清单、fenced code block 内示例，含独占一行）MUST NOT 参与 live 结论解析**——正文平面与状态平面分离，从根消除子串/prose-inline 混淆（gate-anchor-line-scoped B4/B5 根治）。
- **归档报告（`archive/<YYYY-MM-DD>-{change}/*.md`）MUST frontmatter + inline 双读**〔mlh-p5 grill G2；冷审 F2〕：归档 verify 态判定（`archived_verify_state`，经 `git show <base>:…` 读）MUST **frontmatter 优先、无则回退 inline**——因迁移后 `sdflow-done` **归档的**报告本身即 frontmatter 格式（新归档 = frontmatter），迁移前旧归档 = inline 锚。inline 读半场 MUST 以**行级字面查找** `<!-- ship-gate: verify=PASS -->` / `verify=FAIL` 解析（逐行 `strip()` 后整行等值、忽略 fenced code block、MUST NOT 用纯子串），且 MUST **永久保留**（旧归档只含 inline、改历史不可取）；frontmatter 读半场 MUST 认新归档的 `ship-gate.verify`。**MUST NOT 只读 inline**——否则迁移后新归档的 verify=PASS 判不出、SHIPPED 回归〔grill G2〕。

**解析半场退役边界（mlh-p5；mlh-p5-parser-cleanup 收尾）**：live 报告结论解析切 frontmatter 后，`_line_scoped_hits` 的 **live 报告读半场**（`anchors_in` 对 live 文件的行级 inline 锚解析）MUST 退役；**归档读的 inline 半场（`_line_scoped_hits`）MUST 永久保留** + **新增 frontmatter 读**——「删整套解析机器」订正为「删 live inline 读、保留归档 inline 读 + 加归档 frontmatter 读」。**退役后遗留的死符号（`anchors_in` / `pick_exclusive` 及仅供其用的 live inline 锚常量 `ANCHOR_DESIGN` / `ANCHOR_CR_PASS` / `ANCHOR_CR_BLOCKED`）MUST 物理删除**〔mlh-p5-parser-cleanup T75〕——「退役」= 从判定路径摘除 + 源码删除，MUST NOT 留 test-referenced 孤儿假装被覆盖；**`ANCHOR_VERIFY_PASS` / `ANCHOR_VERIFY_FAIL` 与 `_line_scoped_hits` MUST 保留**（归档 dual-read 现役真用，删之即归档 SHIPPED 回归）。

**过渡期渐进迁移（mlh-p5 grill G3）**：producer 未全迁的过渡期，gate 对 **live** 报告 MUST **frontmatter 优先、无 ship-gate 键则回退 inline**（已迁 producer 报告即刻正文免疫、未迁者 inline 兼容）；退役后（三 producer 全迁 + 测试全绿）live MUST 只读 frontmatter。过渡期未迁 producer 的正文假阳风险为**已登记短时取舍**（迁完即消，MUST NOT 因过渡期未根治而阻塞迁移）。

**〔spec-review-amendment〕迁移正确性五铁律（多镜冷审拦下 1 致命 + 3 高，MUST 全落）**：

- **A1（D1，致命）live 读点完整集合**：live 报告结论的 inline 读点 MUST 被识别为**完整集合**——`anchors_in`(design-approved) + **`pick_exclusive`×3**(verify 早检/终门、code-review) + peek `anchors_in`(verify=FAIL) + **`anchor_set`熔断 helper**。frontmatter 化/退役 MUST 覆盖全部读点，MUST NOT 只退役 `anchors_in`——否则 verify/code-review 迁 frontmatter 后 `pick_exclusive` 读不出 inline → 返回 None → STEP_IN_PROGRESS 永卡、无法 SHIPPED（3 类迁 2 类静默失效）；`anchor_set` 未迁则重跑后已写有效 frontmatter 结论被熔断误判无进展。实现起手 MUST 先产出「live 结论读点清单」。
- **A2（D2，高）frontmatter 只认文件首块**：手写解析器 MUST 只识别**文件第 1 行 `---`**（先去 BOM）起、到下一 `---` 止的**唯一首块**；正文任何 `---` markdown 横线 / `ship-gate:` 键 MUST NOT 参与解析（实测报告正文横线密布）。MUST 用 `splitlines()` 口径。MUST NOT 用「全文找首个 `---`/找下个 `---`」松散写法（否则正文横线块被当 frontmatter，B4/B5 复活且 fence-aware 失效）。**首块的成立以「有闭合 `---`」为前提**〔mlh-p5-parser-cleanup T74〕：首行是 `---` 但**无下一个 `---`** 时首块**不成立** → MUST 判 absent（无 frontmatter），MUST NOT 判坏 / fail-closed / UNKNOWN——此形态是正文以 markdown 横线开头，非「写坏的 frontmatter」；absent 在 live 各步均不放行（方向安全，见下「首行 `---` 无闭合判 absent」Scenario）。
- **A3（D3，高）坏≠无 + 退出码映射**：过渡期/归档回退**只**由「absent」触发；**首块成立后的解析失败 / 坏键 / 越域 MUST NOT 回退、直接 fail-closed**（三分支：有效键→用之 / **absent→回退 inline / 走无锚语义** / 首块成立但键坏→fail-closed）。**「absent」含两子形态**〔mlh-p5-parser-cleanup 细化；spec-review SC-1：用 (i)/(ii) 与坏子类的 ①-⑤ 及主体 (a)/(b) 三套标记区分，免阅读歧义〕：**(i)** 无有效首块 frontmatter（首行非 `---`；**或首行 `---` 但无闭合 = 首块不成立**）；**(ii)** 有首块但顶层无 `ship-gate:` 键——两者均走既有无锚语义 / 回退 inline，MUST NOT fail-closed。fail-closed 的退出码 MUST 按坏法确定映射、MUST NOT 用「停下**或**进行中」的歧义并存：越域/重复键/坏语法/类型不符/tab 缩进 → **UNKNOWN(exit 6)**（歧义须人裁、防 exit 0 重跑死循环）；纯缺字段(半成品) → 既有无锚语义（spec-review REFUSE_START(3) / verify·code-review STEP_IN_PROGRESS(0)）。
- **A4（D4，高）live 与归档 frontmatter 读共用同一严格核心**：MUST 新增**单一自持文本级 helper**（如 `parse_ship_gate_frontmatter_text(text)`），`anchors_in`/live 读与 `archived_verify_state`/`git show` 归档文本读**都调它**（复刻现 `_line_scoped_hits` 被两路共用的防漂移纪律）。归档 frontmatter 坏 → fail-safe `none`，MUST NOT 回退 inline 掩盖。**归档 frontmatter 有效 PASS 时 MUST NOT 再交叉扫 inline FAIL**（设计门 Q4 决：frontmatter 即真相）；「好 frontmatter=PASS 掩盖残留 inline=FAIL」盲区 MUST 在 `ship_gate.py`「已知不覆盖」登记（迁移后新归档无残留 inline，风险低）。
- **A5（D12）fail-closed 可观测**：fail-closed 判无有效状态时 `emit()` 的 reason MUST 携带**被拒字段名 + 失败类别**（语法/越域/重复键/类型），MUST NOT 只回「无有效状态」（adr/0006 可观测落地）；对应测试断言 reason 含缺陷标识。

**〔spec-review-amendment D5〕门禁语义等价性订正**：D5「门禁语义不变」MUST 精确表述为——冲突判定的**触发承载**从 inline「PASS/FAIL 行级并存」改为 frontmatter「同字段重复键」，语义等价性**仅在「歧义即不放行」这一层成立**；frontmatter 单 `verify:` 键物理上无法承载行级并存，live 侧不再有「PASS/FAIL 行级并存」触发（避免实现误在 frontmatter 复刻行级并存检测）。

**完成判据的两处加固**〔ship-gate-hardening-2，与锚承载形态正交、不受 mlh-p5 影响〕：① checkpoint 任务标签 MUST 按 change 命名空间归属隔离（`checkpoint(<change>:task<N>-)`，gate 只认当前 change；裸标签向后兼容，详见下方「完成任务号按 change 命名空间隔离」Scenario 组）；② 复选框辅通道 MUST 按 `### Task <n>:` 分段绑定、MUST NOT 全局全勾放行所有 task（详见下方「复选框辅通道按 Task 分段绑定」Scenario 组）。

#### Scenario: 未过设计门拒绝起跑
- **WHEN** 对一个 spec-review-report.md 缺失或 frontmatter 无 `design_approved: true` 的 change 调用 /sdflow-ship
- **THEN** ship_gate 退出码 3（REFUSE_START），skill 停止并提示先完成设计门，MUST NOT 起跑任何阶段三步骤

#### Scenario: verify FAIL 停并上抛
- **WHEN** 链行进至 sdflow-done 后 verify-report.md frontmatter 结论为 `verify: FAIL`
- **THEN** gate 退出码 5，ship 停止、原样上抛缺口清单，MUST NOT 继续 archive/merge（任何一层评审覆盖不得无声蒸发）

#### Scenario: live 报告 frontmatter 承载结论被正确解析〔mlh-p5〕
- **WHEN** live 的 spec-review-report.md / verify-report.md / code-review-report.md 各在 frontmatter 落 `ship-gate.design_approved: true` / `ship-gate.verify: PASS` / `ship-gate.code_review: pass`
- **THEN** gate MUST 从 frontmatter 读出对应结论并按既有门禁语义推进（design-approved→放行设计门、verify PASS→继续收尾、code_review pass→进 verify），MUST NOT 依赖正文任何 inline 文本

#### Scenario: live 报告正文提及锚字面不触发门禁〔mlh-p5：B4/B5 根治〕
- **WHEN** 某 live 报告 frontmatter **无** ship-gate 结论字段，但正文（描述句 / 对账清单 / fenced code block 内示例 / 独占一行）原样写出锚字面如 `<!-- ship-gate: design-approved -->` 或 `ship-gate.verify: PASS`
- **THEN** gate MUST 判该结论**未落**（live 只解析 frontmatter，正文平面不参与）——对 design-approved 而言此盘面 MUST 判 REFUSE_START（未过设计门），MUST NOT 因正文提及假过门越 adr/0004 红线；正文任意位置写出锚串 MUST NOT 影响任何门禁判定

#### Scenario: 首行 `---` 无闭合判 absent 不硬崩〔mlh-p5-parser-cleanup T74；grill Q3 措辞订正〕
- **WHEN** 某 live 报告首行是 `---`（去 BOM 后）但全文**无第二个 `---`**（首块不闭合——纯结构条件，**不问意图**：无论是正文以 markdown 横线分节开头，还是有意写 frontmatter 却漏写闭合 `---`）
- **THEN** `parse_ship_gate_frontmatter` MUST **仅依结构判 absent（`({}, None)`）**——首块无闭合即不成立、不构成 frontmatter block（与 A2「只认首块」定义自洽）；**MUST NOT 把「是否有意声明 ship-gate 状态」纳入判据**（parser 只看结构、看不见意图；意图属概率空间，纳入即违「盘面即状态」机判契约纪律）——无意的水平线与有意漏闭合的 frontmatter **同等**判 absent。gate MUST 走既有无锚语义（spec-review-report → REFUSE_START(3)；verify/code-review report → STEP_IN_PROGRESS(0)），**MUST NOT 判 UNKNOWN(exit 6) 硬崩一份干净报告**；「有意漏闭合」者走无锚语义（REFUSE_START/重跑）属**方向安全**（假阴漏判非假阳假过），与 `ship_gate.py` 已登记「false absent → 方向安全」及 adr/0011 目标态论证一致；MUST 有 pytest 用例断言此输入返回 `({}, None)` 而非任何坏类别。**SHOULD** 在 live emit reason 附一句**纯结构**诊断提示（「首行为 `---` 但未见闭合 `---`，已按正文处理；欲声明状态请补闭合行」）恢复 DX actionability〔spec-review Q1=A〕——提示 MUST 走 live 读点**上层独立结构判定**、MUST NOT 改 `parse_ship_gate_frontmatter` 返回签名（防波及 `anchor_set`/`archived_verify_state` 三调用方）、MUST NOT 改 verdict/退出码、MUST NOT 探测意图（纯结构 ≠ candidate② 的「下一行是否 `key:` 形态」，不重开自指免疫）

#### Scenario: live 报告 frontmatter 写坏 fail-closed〔mlh-p5：决策 6 + grill G4 攻击面；mlh-p5-parser-cleanup 收窄触发面〕
- **WHEN** 某 live 报告**有成立的首块 frontmatter（首行 `---` 且有闭合 `---`）**，但块内被 LLM 写坏——任一：① 顶层 `ship-gate:` 键**重复**或同字段（如 `verify:`）**重复键**；② tab 缩进 / 混合缩进；③ 字段值越域（`verify: MAYBE`）；④ 值类型不符（`design_approved: yes`/非 bool）；⑤ 顶层 `ship-gate:` 带非空内联标量值（`ship-gate: []`/`true`）
- **THEN** 手写 stdlib 解析器 MUST **fail-closed** 判「无有效状态」→ UNKNOWN(exit 6) 停下报告点名，MUST NOT 静默当已过门、MUST NOT 猜测意图；**重复键 MUST 显式判 UNKNOWN/无效，MUST NOT 静默取最后一个**（safe_load 的默认取后行为在门禁语境是危险假定，手写须显式判重）；上述每条坏输入 MUST 有 pytest 用例断言非零退出 / 判定不能。**注**〔mlh-p5-parser-cleanup〕：「首行 `---` 无闭合（首块不成立）」**不属**本 Scenario 的坏——它归 absent（见上「首行 `---` 无闭合判 absent」Scenario），本 fail-closed 触发面仅限「首块已成立、块内容坏」

#### Scenario: 过渡期 live 未迁 producer 回退 inline〔mlh-p5 grill G3〕
- **WHEN** 迁移过渡期，某 live 报告的 producer 尚未迁移（frontmatter 无 `ship-gate` 键）、正文仍含独占一行 inline 锚
- **THEN** gate 对 live MUST **frontmatter 优先、无键则回退 inline** 读识别该锚（渐进迁移、中间态可用）；已迁 producer（frontmatter 有 `ship-gate` 键）MUST 只认 frontmatter、**不回退** inline（正文即刻免疫）；退役后 live MUST 只读 frontmatter

#### Scenario: frontmatter 只认文件首块，正文横线/锚提及不参与〔spec-review-amendment A2/D2〕
- **WHEN** 某 live 报告 frontmatter 无 ship-gate 结论字段，但正文中部有 markdown 横线 `---`（报告正文常含多处）包夹的块内写了 `ship-gate:` 与 `verify: PASS`，或正文任意行提及 `ship-gate.verify: PASS`
- **THEN** 手写解析器 MUST 只从文件第 1 行 `---`（去 BOM 后）起的唯一首块取键，正文中部 `---` 块与其中 `ship-gate:` 键 MUST NOT 被识别为 frontmatter → 该报告判无结论（design-approved 场景 → REFUSE_START）；MUST NOT 因正文 `---` 横线密布而误把正文块当 frontmatter（否则 B4/B5 在 YAML 层复活、fence-aware 失效）

#### Scenario: 坏 frontmatter 按坏法映射确定退出码〔spec-review-amendment A3/D3〕
- **WHEN** live 报告 frontmatter **有成立首块且有 ship-gate 键**但坏——分两类：① 值越域(`verify: MAYBE`)/重复键/坏 YAML 语法/类型不符/tab 缩进；② 纯缺该报告应有的字段（半成品，键区存在但无对应结论字段）
- **THEN** 第 ① 类 MUST 判 **UNKNOWN(exit 6)**（歧义须人裁，MUST NOT 判 STEP_IN_PROGRESS(exit 0) 致 LLM 反复写坏成重跑死循环）；第 ② 类 MUST 落既有无锚语义（spec-review-report → REFUSE_START(3)；verify/code-review report → STEP_IN_PROGRESS(0)）；**MUST NOT** 用「停下报告**或**判该步进行中」的退出码歧义并存；过渡期第 ① 类（有键但坏）MUST NOT 回退 inline（坏≠无键）。**「首块不成立（无闭合 `---`）」不入本 Scenario 分类**——它归 absent（无键缺席态）走无锚语义〔mlh-p5-parser-cleanup〕

#### Scenario: frontmatter 同字段重复键判 UNKNOWN〔spec-review-amendment D5〕
- **WHEN** 某报告 frontmatter 顶层 `ship-gate:` 键重复，或其下 `verify:`/`code_review:` 同名字段出现多次（键分散、键间夹注释、跨缩进等干扰形）
- **THEN** 解析器 MUST 在块边界内**枚举全部同名键计数**、判 UNKNOWN(exit 6)，MUST NOT「见到第二个即覆盖」静默取最后一个（这是 frontmatter 时代表达「冲突结论」的唯一触发面，取代 inline 的 PASS/FAIL 行级并存，是 load-bearing 单点，须专门 pytest 覆盖干扰形）

#### Scenario: 归档旧 inline 锚 dual-read 永久兼容〔mlh-p5 冷审 F2〕
- **WHEN** gate 判某 change 终态，其归档目录 `archive/<date>-{change}/verify-report.md` 仅含旧格式 inline 锚 `<!-- ship-gate: verify=PASS -->`（归档于 mlh-p5 迁移前，无 frontmatter 状态）
- **THEN** `archived_verify_state` MUST 经 inline 行级读正确识别 verify=PASS → 支持 SHIPPED 判定，MUST NOT 因归档无 frontmatter 而判无状态；此 inline 归档读半场对既有 88 归档报告 MUST 保持 100% 兼容、MUST NOT 回归（`_line_scoped_hits` 与 `ANCHOR_VERIFY_PASS`/`ANCHOR_VERIFY_FAIL` MUST 保留，T75 清理 MUST NOT 波及）

#### Scenario: 归档漏闭合 frontmatter 目标态 fail-safe〔mlh-p5-parser-cleanup Q2；adr/0011〕
- **WHEN** 目标态某归档 verify-report（producer 迁后 = frontmatter-only、正文**无 inline 锚**）被 LLM prepend frontmatter 时**漏写闭合 `---`**（首行 `---` 无闭合），经 `git show <base>:…` 读出
- **THEN** `parse_ship_gate_frontmatter` MUST 返回 absent（首块不成立）→ `archived_verify_state` 回退 inline dual-read → 正文**无 inline 锚可扫** → 判 `none` → **不 SHIPPED**（fail-safe，与 live 侧漏闭合 REFUSE_START/重跑**同向安全**）；MUST NOT 因回退 inline 而误判 pass。**安全论证 MUST 锚 producer 契约 + 目标态**〔adr/0011〕，MUST NOT 以迁移现状（现存归档多 `#` 打头、无一触发）评估——迁移现状非稳态。初版担心的「回退 inline 判假 pass」需「首行 `---` 无闭合 × 正文独占一行 inline PASS 锚」杂交形态，**无 producer 会产出**（未来 producer 不写 inline、旧 producer 首行 `#`），须手工伪造归档 = 显式越权（`adr/0008`，git 可审计）→ MUST 登记 `ship_gate.py`「已知不覆盖」；MUST 有 pytest 覆盖此目标态归档形态断言 `none`

#### Scenario: 迁移后新归档 frontmatter 被归档读识别〔mlh-p5 grill G2〕
- **WHEN** gate 判某 change 终态，其归档目录 `archive/<date>-{change}/verify-report.md` 是**迁移后**格式——frontmatter `ship-gate.verify: PASS`、正文无 inline 锚（`sdflow-done` 已迁 producer 归档所得）
- **THEN** `archived_verify_state` MUST 经**归档 frontmatter 读**（frontmatter 优先）识别 verify=PASS → 支持 SHIPPED，MUST NOT 因归档无 inline 锚而判无状态；归档读 **MUST NOT 只读 inline**——否则迁移后所有新归档 SHIPPED 判定回归〔grill G2 证伪 design 原「归档纯 inline」〕

#### Scenario: 前置产物缺失点名
- **WHEN** 某步产物缺失（如 code-review-report.md 不在）
- **THEN** gate 输出 next=对应 skill 与 missing 清单，编排按此推进；实现完成判据 MUST 以 **git 历史 checkpoint 任务标签为主锚**（plan 任务数 N 对 checkpoint 去重任务号集，齐 N 判完成〔grill-amendment〕；标签 MUST 按 change 命名空间归属过滤 `checkpoint(<change>:task<k>-`（裸 `checkpoint(task<k>-` 向后兼容），见下「命名空间隔离」Scenario 组〔ship-gate-hardening-2〕；**收集窗口 MUST 为含 superpowers-plan.md 首次提交自身的闭区间 `[sha, HEAD]`**——即 `git log <sha>..HEAD --no-merges` 加对 `<sha>` 自身 commit subject 的同规则解析；plan 与首个 task 锚同 commit（checkpoint `add -A` 携带未提交 plan 的合法盘面）时该 task MUST 计入，MUST NOT 漏数〔B1 修复，替换旧排他窗口表述〕；MUST NOT 全历史扫描——main 遗留标签会造成假齐 N〔spec-review-amendment 设计门拍板 Q2〕；plan 标题命中 0 → UNKNOWN；**重号 `### Task <n>:` 段 → UNKNOWN**〔ship-gate-hardening-2〕）、plan 复选框**按 `### Task <n>:` 段绑定**为辅（MUST NOT 全局全勾放行所有 task，见下「分段绑定」Scenario 组〔ship-gate-hardening-2〕），两通道皆不可判时 gate 判 UNKNOWN 停上抛，MUST NOT 猜测推进、MUST NOT 以 gitignored 的 SDD ledger 为判据

#### Scenario: plan 与首个 task 锚同 commit 不漏数〔B1〕
- **WHEN** superpowers-plan.md 的首次提交 commit 本身就是 `checkpoint(task1-<slug>)` 提交（plan 未单独提交、被首个 task 的 checkpoint `add -A` 一并携带入库）
- **THEN** gate 的完成任务号集 MUST 含 task1（窗口为含该 commit 自身的闭区间），plan 任务数 N 齐时 MUST NOT 输出 CONTINUE_IMPL 误报

#### Scenario: 陈旧 FAIL 不卡死 resume〔grill-amendment D9〕
- **WHEN** verify-report frontmatter 为 `verify: FAIL`，其提交之后存在触及 `openspec/` 之外路径的修复提交，用户重调 /sdflow-ship
- **THEN** gate 判该结论陈旧 → NEXT=重跑 sdflow-done（重验），MUST NOT 以陈旧 FAIL 退出卡死

#### Scenario: 干预后陈旧 PASS 不放行〔grill-amendment D9〕
- **WHEN** verify/code-review frontmatter 结论为 pass/PASS，但其后有人手改了 `openspec/` 之外的代码
- **THEN** gate 判受影响步结论陈旧 → 重跑该步，MUST NOT 让旧结论背书新代码直通 merge

#### Scenario: design-approved 不因实现提交失鲜〔spec-review-amendment 设计门拍板 Q1=B〕
- **WHEN** 设计门拍板（frontmatter `design_approved: true`）已落，实现期产生大量触及 `openspec/` 之外路径的提交（正常实现活动）
- **THEN** gate MUST 保持 design-approved 有效（新鲜度按结论分域：该结论仅当其后存在触及本 change **design 域监视集**路径的提交才失鲜须重审；监视集为固定四件套，其内 `tasks.md` 的豁免条件由下方「纯勾选框翻转不失鲜」Scenario 组定义），MUST NOT 因实现提交判其陈旧而 REFUSE_START（防实现期链自锁）

#### Scenario: 纯勾选框翻转不失鲜〔spec-review-amendment〕

design 域监视集 SHALL 保持固定四件套不变。豁免 SHALL 仅覆盖**已证对 gate 零信息量**的唯一改动形态——`tasks.md` 的完成度复选框状态翻转。

- **WHEN** 设计门拍板已落，其后某提交**落在 design 域监视集内的触及路径集恰为 `{tasks.md}`**（该提交同时触及监视集**之外**的路径——源码、`impl-reports/` 等——**不影响**豁免资格；checkpoint 走 `git add -A`，真实完成提交必然打包源码，按整 commit 文件列表求值会令豁免永不触发），且 `tasks.md` 前后两版在勾选框状态归一化后**逐行等值**
- **THEN** gate MUST NOT 因该提交判 design-approved 失鲜
- **AND** 归一化 MUST **锚定到 task-list 行首语法位置**（复用既有 `CHECKBOX_RE` 口径），且 MUST **fence-aware**（fenced code block 内的标记不参与归一化，复用 `_line_scoped_hits` 的 fence 口径）——无锚定的整行子串替换会把表格、行内反引号、引用块、散文字面量里的 `[ ]` / `[x]` 一并归一化，令豁免面远超「完成度复选框」集合
- **AND** 比较 MUST 按**行位置**对齐（如 `zip`），MUST NOT 使用基于 LCS / diff 算法的行匹配——LCS 下纯行重排会把「删除行与插入行逐字节相同」判成等值，令任务顺序 / 依赖的实质变更直通
- **AND** 判定 MUST 保真读取：MUST NOT 复用会 `.strip()` / `text=True` 的 helper（吞首尾空白、末尾换行、CRLF、非 UTF-8 字节，四者各自可造假等值）；两侧内容读取 MUST 显式检查 returncode，任一侧失败 ⇒ **保守判失鲜**（双侧失败会得 `"" == ""` ⇒ 判等值 ⇒ 放行真实设计改动）
- **AND** MUST NOT 做语义 diff、MUST NOT 因上述 fence 锚定要求而扩展成完整 markdown 解析（fence 开合是单 boolean toggle，非解析器）
- **AND** 判定 MUST 逐提交独立求值，MUST NOT 依赖工作树状态或任何跨提交状态（承既有「新鲜度 committed-only」口径）

#### Scenario: 勾选框以外的一切 tasks.md 改动照判失鲜〔spec-review-amendment〕

- **WHEN** 某提交触及 `tasks.md`，且满足下列任一：① 勾选框标记之外的任何字符变化（措辞 / 缩进 / 空白 / 格式化 / 错别字）；② 新增或删除 `### Task <n>:` 段；③ 行的重排或移动；④ fenced code block / 表格 / 行内反引号 / 散文中的 `[ ]` `[x]` 字面量变化；⑤ 同一提交还触及 `proposal.md` / `design.md` / `specs/` 中任一路径；⑥ 前版或后版取不到（该提交中**新建**、**删除**或 `git mv` **迁走** `tasks.md`）；⑦ 该路径的 git 变更状态不是普通内容修改（rename / copy / 类型变更 / mode 变更——`chmod` 或 regular↔symlink 可令 blob 内容完全相同而被误判为「纯勾选」）
- **THEN** gate MUST 照判 design-approved 失鲜 → `REFUSE_START`
- **AND** 情形 ⑥⑦ MUST **保守判失鲜**——MUST NOT 因取不到某一版、或因内容恰好相同而当作等值放行；资格判定 MUST 读取 git raw 状态位与 mode，MUST NOT 仅凭 `--name-only` 的路径列表

#### Scenario: 内容豁免与既有 subject 豁免的优先级〔spec-review-amendment〕

内容豁免独立于 subject，与既有 BR-7「变体照判失鲜」存在判定重叠（如 `checkpoint(impl-review)evil` + 纯勾选提交），SHALL 由下述优先级消歧：

- **WHEN** 某帧同时可被「精确式 `checkpoint(impl-review)` subject 豁免」与「内容豁免」评估
- **THEN** 判定顺序 MUST 为：① subject 精确匹配 ⇒ **无条件豁免该帧**（既有语义逐字不变，MUST 在读取任何 blob **之前**短路）；② 否则进入内容豁免评估——**任何** subject（含 `checkpoint(impl-review)evil` 等变体）均可凭严格的纯勾选内容判据获豁免；③ 二者皆不满足 ⇒ 失鲜
- **AND** BR-7 的既有表述 MUST 理解为「变体**不因 subject** 获豁免」，MUST NOT 理解为「变体必然失鲜」——后者与本 Scenario 冲突且无唯一解
- **AND** MUST 有覆盖 `精确 / 变体 / 空 / 普通 subject × 纯勾选 / 语义改动` 的真值表测试

#### Scenario: 豁免面 MUST NOT 由被监管方书写的声明决定〔spec-review-amendment〕

- **WHEN** 设计判据在「内容等值」与「被监管方可书写的声明」（commit subject、某文件是否存在、工作树状态）之间取舍
- **THEN** 豁免判据 MUST 取自被比较的内容本身；MUST NOT 以 `superpowers-plan.md` 的存在性、或除既有 `checkpoint(impl-review)` 精确式之外的任何 subject 形态，作为 `tasks.md` 豁免的判据
- **AND** 既有 `checkpoint(impl-review)` 精确式 subject 豁免（BR-7）MUST 逐字保留、不受本条影响

#### Scenario: 失鲜 REFUSE_START 须携带触发点与处置指引

- **WHEN** gate 因 design 域失鲜而 emit `REFUSE_START`
- **THEN** reason MUST 指明**触发失鲜的提交与文件**（至少一条 `<commit subject 或 sha>` + `<路径>`），并 MUST 携带**分类原因**（混合路径 / 非勾选框变化 / 前后版缺失 / 状态不合格，取值以判据实际分支为准）；MUST NOT 只输出「结论陈旧」而不指明触发点
- **AND** 机读输出 MUST 与人读文案**同源**（同一份触发点数据的两个视图），MUST NOT 各自拼装而允许单侧漂移
- **AND** 默认处置指引 MUST 只推荐**重跑设计门**一条；`checkpoint(impl-review)` **MUST NOT** 出现在默认处置指引中〔spec-review-amendment 设计门拍板；impl-review-fix：本条原文与 ADR-2 改写后的口径冲突，系 spec-review 期改写 ADR-2 未扫残留引用所致，此处对齐〕——两条理由：① 它是**显式越权口**（让任意四件套语义改动不经二次批准随档 ship，`ship_gate.py` 头注释已声明为「已知不覆盖」），写进常规建议会把例外变成默认工作流；② 🔴 **它对撞门者无效**——豁免逐提交求值，已经触发失鲜的那个提交**不会**因为后补一个 `checkpoint(impl-review)` 提交而被追溯赦免，写进指引等于教人做一件不起作用的事。其正确定位是**事前、受控的 impl-review 提交协议**（用在会触发失鲜的那个提交自身上），只在该协议文档中说明
- **AND** 该指引 MUST 为纯诊断输出，MUST NOT 改变退出码或失鲜判据本身

#### Scenario: 阶段三合法尾流修订不失鲜〔B2〕
- **WHEN** 设计门拍板已落，其后 sdflow-code-review 按工作流对 design.md/tasks.md 打 `[impl-review-fix]` 补丁并以 commit subject 闭合字面前缀 `checkpoint(impl-review)`（含右括号）提交（触及四件套路径）
- **THEN** gate 的 design 域新鲜度判定 MUST 豁免该类提交（不判拍板失鲜、不 REFUSE_START）；豁免面 MUST 仅限**精确式 `subject == "checkpoint(impl-review)" 或 subject 以 "checkpoint(impl-review):" 起始`**〔spec-review-amendment BR-7：裸闭合前缀 startswith 仍收 `checkpoint(impl-review)evil` 尾串垃圾，须精确式〕——`checkpoint(impl-review-fix)`/`checkpoint(impl-reviewX)`/`checkpoint(impl-review)evil` 等从不由 checkpoint 脚本合法产生的变体 MUST NOT 豁免（照判失鲜）；其他 subject 触及四件套照判失鲜（实现改设计须重审的既有语义不变）；豁免 MUST NOT 分析改动内容（只认 subject 不认 hunk），由此「经豁免的语义级四件套改动不经二次批准即随档 ship」属**已登记的接受取舍**〔grill Q2〕；伪造/手工 subject 绕过豁免属显式越权同权级（git 留痕可审计），MUST 在脚本头注释「已知不覆盖」中声明

#### Scenario: 未提交报告视为 fresh〔spec-review-amendment 设计门拍板 Q3=A〕
- **WHEN** 某报告文件存在且 frontmatter 含结论字段，但从未 git 提交（`git log -1 -- <path>` 空输出）
- **THEN** gate MUST 视其为 fresh 并在 JSON 注明 `freshness=uncommitted`（人机同权：手写产物合法），MUST NOT 因无提交记录而判进行中或报错

#### Scenario: 无结论产物 = 步进行中〔grill-amendment D9；mlh-p5 改 frontmatter〕
- **WHEN** 某 live 报告文件存在但 frontmatter 不含任何 ship-gate 结论字段（如中断的半成品）
- **THEN** gate 判该步进行中 → NEXT=重跑该步，MUST NOT 当作已完成

#### Scenario: 暂停后重调即续、人机同权〔grill-amendment D9〕
- **WHEN** 链中途停止（任意原因），期间用户手动完成了某步（如手跑 /sdflow-code-review 产出报告），之后重调 /sdflow-ship
- **THEN** gate 仅凭盘面推进（不辨产者），从下一缺口继续；实现中断场景 gate 输出已完成任务号集供 SDD 勿重派；ship MUST NOT 依赖任何跨步内存状态

#### Scenario: 条件步按 TG 判定
- **WHEN** change 的 proposal 未标注 TG-02（非嵌入式）
- **THEN** gate 对 step 5.5 输出 SKIP 并记录理由；命中 TG-02 时高风险/TG-18 细判归模型（每步内部判断，prose 允许域）

#### Scenario: 归档后识别 SHIPPED 终态〔B3 + D3 硬化〕
- **WHEN** change 的 active 目录 `openspec/changes/{change}/` 不存在，但归档目录 `archive/<YYYY-MM-DD>-{change}/`（发现经**纯 git 域** `git ls-tree HEAD ∪ ls-tree <base>` 列举 + `re.escape(change)` 套日期前缀 fullmatch，**MUST NOT 用文件系统 glob**〔H2/BR-4〕）**已存在于 base 树** 且该归档目录内 `verify-report.md` **含 verify=PASS 结论（frontmatter `verify: PASS` 或归档旧 inline 锚 `<!-- ship-gate: verify=PASS -->`，dual-read）**〔H1/BR-2；mlh-p5 dual-read〕
- **THEN** gate MUST 输出 SHIPPED（exit 0），MUST NOT 按 active 路径找不到 spec-review-report.md 而误报「未过设计门」；该短路判定 MUST 位于设计门 pre-flight 与新鲜度检查之前；终态判据 MUST 为 change 域可达性（`git ls-tree <base>`）而非全局 `branch_state()`〔grill-amendment〕；发现 MUST 与判据同域（纯 git，工作树无关）——MUST NOT 用工作树 glob（否则跨分支查已并 change 会假 REFUSE、未跟踪垃圾目录会假 RUN_VERIFY）〔H2/BR-4〕；SHIPPED MUST 追读 archived verify=PASS 结论——MUST NOT 仅凭目录存在性放行（手工空壳归档目录不得假 SHIPPED）〔H1/BR-2〕；`--change` MUST 校验为 slug 或 `re.escape` 后匹配，MUST NOT 把用户输入当 glob 元字符〔H5/HRTG-4〕；base 无 main/master → UNKNOWN，detached HEAD 对 D3 判定无关（凭 base 树可达仍可 SHIPPED）〔H3/H4〕；active 存在时 final SHIPPED 的 archived 谓词 MUST 收紧，MUST NOT 被旧/同名 archive 触发〔H1/HRTG-1〕

#### Scenario: 完成判据按任务号集合归属，非基数〔B4〕
- **WHEN** plan 有 `### Task 1:`/`### Task 2:`（计划号集 {1,2}），实现窗口内出现 `checkpoint(task1-…)` 与一个**计划外**的 `checkpoint(task9-…)`（遗留/错号/merge 内提交），task2 从未完成
- **THEN** gate 的完成判据 MUST 按**任务号集合归属**（plan 号集 ⊆ 完成号集）判齐，MUST NOT 按基数 `len(done) < n` 判——否则计划外 task9 会顶替缺失的 task2 让 `len(done)=2=N` 假齐、误放行 RUN_CODE_REVIEW（活体复现的假✅）；此盘面 MUST 输出 CONTINUE_IMPL，`done_tasks` MUST 只报计划内已完成号（不含 9）

#### Scenario: 归档但未并入 base = merge 收尾未完〔B3〕
- **WHEN** active 目录不存在、日期前缀 glob 命中 archive，但该归档目录**不在 base 树里**（archive commit 停在未并分支，`git ls-tree <base>` 空）
- **THEN** gate MUST 输出 RUN_VERIFY（next=sdflow-done）并在 reason 说明「已归档但分支未并，完成 merge 收尾」，MUST NOT 判 SHIPPED、MUST NOT 判 REFUSE_START

#### Scenario: change 不存在与未过设计门区分〔B3〕
- **WHEN** active 目录不存在、且日期前缀锚死 glob 在 archive 下无命中（change 名拼错或从未创建；后缀撞名的别的 change 归档因 glob 锚死日期段 MUST NOT 误命中）
- **THEN** gate MUST 输出 REFUSE_START 且 reason 为「change 不存在（active 与 archive 均无）」，MUST NOT 输出误导性的「未过设计门请补锚」提示；active 目录存在时同名历史归档 MUST NOT 干扰判定（active 优先）

#### Scenario: 完成任务号按 change 命名空间隔离〔T32/ship-gate-hardening-2〕
- **WHEN** 当前 change A 的 plan 号集 = {1, 2}，同一分支窗口内只有 A 的 `checkpoint(A:task1-…)`（task2 未完成），另一 change B 的 `checkpoint(B:task2-…)` 落进 A 的窗口（B 的号恰是 A 缺的 task2；触发本需 stacking——feat/A 上再建 change B，FF-0 不拦 feature 分支 stacking）
- **THEN** gate 对 A 判定时 MUST 只把 `checkpoint(A:task1-…)` 计入（`done_ids={1}`），MUST NOT 把 `checkpoint(B:task2-…)` 计入（命名空间 `<ns>` 严格 `==` 当前 change 才计；`foo` 与 `foo-bar` 精确互斥非前缀）；`plan_ids - done_ids = {2} ≠ ∅` → MUST 判 CONTINUE_IMPL 且 `done_tasks==["1"]`，MUST NOT 因 B 的 task2 顶替使 `done={1,2}` 假齐放行 RUN_CODE_REVIEW〔判别性负例（B 号=A 缺号）方能区分"只计当前"与"两个都计"，MUST NOT 用同号无区分力写法〕；解析 MUST 用可选命名空间捕获组 `checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-`，且 `done_task_ids` 的字面前缀过滤 MUST 同步放宽为 `startswith("checkpoint(")`（MUST NOT 保留 `startswith("checkpoint(task")`——否则命名标签在 `TAG_RE.match` 前被整条跳过、T32 静默失效）；回归覆盖 MUST 用真实 git commit fixture

#### Scenario: 旧无命名空间 checkpoint 标签向后兼容〔T32/ship-gate-hardening-2〕
- **WHEN** 一个 change 的实现窗口内任务 checkpoint 全为旧格式裸标签 `checkpoint(task<N>-<slug>)`（无 `<change>:` 前缀，gate 升级前已产生或进行中）
- **THEN** gate MUST 按既有窗口 `[plan_first_sha, HEAD]` 语义把裸标签计入该 change 完成号集（= 升级前行为），MUST NOT 因识别不到命名空间而丢弃或退出异常；该 change 完成判据结果 MUST 与本加固落地前逐字一致（既有 B1/B4 及全部裸格式回归测试不变）；归属取舍 MUST 向假阴（少计=多一次 CONTINUE_IMPL）安全倾斜、MUST NOT 引入假阳。「污染方用旧裸格式 stacking 进来 + 撞 plan 号」残留假✅ MUST 记入 `ship_gate.py` 头注释「已知不覆盖」，MUST NOT 用"每 change 独立分支纪律"作缓解（纪律成立则污染不可达、立论自否——见 adr/0008 防御纵深立场）

#### Scenario: 复选框全局单勾不放行未勾的其它 task〔T34/ship-gate-hardening-2〕
- **WHEN** plan 有 `### Task 1:`（段内 `- [x]` 全勾）与 `### Task 2:`（段内含未勾 `- [ ]`），且无任何 checkpoint 任务标签
- **THEN** gate 的复选框完成集 MUST 只含 task1（其段全勾），MUST NOT 因"全文存在 `- [x]`"或全局粒度把 task2 也判完成；`plan_ids - done_ids = {2} ≠ ∅` → MUST 判 CONTINUE_IMPL，MUST NOT 假齐放行；复选框识别 MUST 行锚定 `^\s*-\s+\[[ xX]\]`（非全文子串）且 MUST 忽略 fenced code block 内伪复选框

#### Scenario: 分段完成集与 checkpoint 主锚并集〔T34/ship-gate-hardening-2〕
- **WHEN** plan 有 task1/task2，task1 由 `checkpoint(<change>:task1-…)` 完成、task2 由其 `### Task 2:` 段内复选框全勾完成
- **THEN** gate MUST 把两通道完成号并集（`{1} ∪ {2} = {1,2}`）后判 `plan_ids ⊆ done_ids` 齐 → 进 code-review 门，MUST NOT 因两通道分立而漏判其一

#### Scenario: 代码块内伪复选框不算完成〔T34/ship-gate-hardening-2〕
- **WHEN** 某 `### Task <n>:` 段的真实清单行未勾（`- [ ]`），但该段的 fenced code block（```…```）内含 `- [x]` 示例文本
- **THEN** gate MUST NOT 把该 task 判为复选框完成（行锚定 + 忽略代码块），MUST 依真实未勾行判其未完成

#### Scenario: 重号 Task 段判 UNKNOWN〔T34/ship-gate-hardening-2〕
- **WHEN** plan 出现两个同号 `### Task 1:` 段，其一全勾（或有 checkpoint）、其二含未勾 `- [ ]`
- **THEN** gate MUST 判该 plan UNKNOWN（重号不可判），MUST NOT 因任一段全勾就把 task1 计入完成集而掩盖另一段未完成（`plan_task_ids` 的 `set` 折叠重号的假✅）

#### Scenario: 归档 verify 描述性提及不触发假 SHIPPED〔gate-anchor-line-scoped B4·SHIPPED 路径〕
- **WHEN** 归档目录的 `verify-report.md`（经 `git show <base>:…` 读出）正文**描述性提及** `<!-- ship-gate: verify=PASS -->`（内联句 / 代码块内文档示例）但**无独占一行的真 PASS 锚**、且 frontmatter 亦无 `verify: PASS`
- **THEN** `archived_verify_state` MUST 判其 verify 态为 `none`（非 `pass`），使归档终态短路 MUST NOT 输出假 SHIPPED——空壳 / 未验 / 仅描述性提及的归档目录 MUST 落 fail-safe（不 SHIPPED，请人工核验）；此归档 inline 判据 MUST 为行级整行等值 + 忽略 fenced code block（`_line_scoped_hits` 归档读半场），MUST NOT 保留裸子串路径

#### Scenario: 归档未闭合 fence 隔断互斥锚对不判假通过〔gate-anchor-line-scoped OV-2·设计门 Q1=A；mlh-p5 归档侧〕
- **WHEN** 某**归档** verify-report.md 的**互斥 inline 锚对**（verify `PASS`/`FAIL`）中正锚独占一行在 fenced code block 外、负锚独占一行落在**未闭合**（无配对收尾 ```）的 fence 内被吞
- **THEN** 归档读行级锚检测核心 MUST 回报**未闭合信号**，`archived_verify_state` 遇未闭合信号 MUST **保守判定**（`none` 不 SHIPPED），MUST NOT 因只见正锚而判 pass（否则从旧裸子串 conflict 语义回归为危险假阳）；此约束针对**归档读半场**（live 报告已迁 frontmatter，其冲突由 frontmatter 同字段重复键 → fail-closed 处理，不再经 fence 判据）

#### Scenario: TG-02 条件步检测用声明式匹配非裸子串〔gate-anchor-line-scoped ADR-6·dogfood〕
- **WHEN** 某 change 的 proposal **描述性提及** `TG-02`（反引号代码引用 / 否定句 `TG-01/02/03 均不命中` / 散文讨论），但**未以声明式头注** `〔TG-02：…〕` 标注该触发（即该 change 非嵌入式、不该跑 embedded-test-sop）
- **THEN** gate 的 TG-02 条件步检测（`tg02_hit`）MUST 判**未命中** → step 5.5 输出 SKIP，MUST NOT 因子串命中正文对 TG-02 的**文档性提及/示例声明串**而误判 RUN_SOP（嵌入式 SOP）；检测 MUST 限定在 proposal **头部声明区**（文件开头→首个 `## ` 标题前）找 `〔TG-02`〔A3，dogfood 二轮：整体子串含加冒号仍被正文示例串假阳〕，真嵌入式 change 的头部 `〔TG-02：…〕` 声明仍 MUST 正确命中 → RUN_SOP；头部未用括号声明的（非常规）embedded proposal 漏检为安全侧假阴（ff 强制头注括号格式故实际不发生），记 Non-Goals

### Requirement: 模型档位映射（model-tiers）

模型档位定义、职责清单与 canonical 缺省 MUST 以 workflow bundle 规则文件 **`model-tiers.md`** 为单一真相源（经 resolver 全局解析；强档=verify/对抗裁决/final 终审；中档=领域镜/生成/实现；弱档=纯机械步）〔grill-amendment：推翻"config 段真相源 + SKILL 内联缺省×4"——多处 copy 漂移面〕。**档位映射 MUST 按机队分列**〔add-codex-host-support〕：Claude 机队缺省 opus/sonnet/haiku、Codex 机队缺省 gpt-5.6-sol/gpt-5.6-terra/gpt-5.6-luna（机队锚定，adr/0006(c)——档位是相对执行机队的相对词，不绑单一产品线）。**当前机队 MUST 由 `resolve-models.sh` 按宿主正信号判定**（见能力 `host-adaptive-execution`），编排 skill MUST 引用其导出的 `SDFLOW_TIER_*` 变量。消费仓 `config.yaml` 的 `model-tiers` 段 MUST 仅作可选 per-repo **覆盖**，且 **MUST 按机队分键**〔add-codex-host-support · grill G4 · adr/0024〕：`model-tiers.{claude,codex}.{strong,mid,light}`，`resolve-models.sh` 按当前机队读对应段、无该段回落机队缺省；**扁平旧格式**（`model-tiers.strong: …`）MUST 兼容读作 **Claude 机队**覆盖（历史事实：存量覆盖皆写于 Claude-only 时期），MUST NOT 罢工、MUST NOT 在 Codex 宿主下把 Claude 机队的模型名（如 opus）用于 Codex 机队子代理。编排 skill（sdflow-ship/done/spec-review/code-review）的模型选择 MUST 以一句引用指向规则文件与覆盖段，MUST NOT 内联具体模型名。

#### Scenario: 消费仓无覆盖段用 canonical 缺省
- **WHEN** 消费仓 config.yaml 无 model-tiers 段，跑任一编排 skill
- **THEN** skill 按规则根 `model-tiers.md` 中**当前宿主所属机队**的 canonical 缺省档位运行，MUST NOT 报错、MUST NOT 静默降级门禁步模型

#### Scenario: verify 档位来自映射（覆盖优先）
- **WHEN** 消费仓 config.yaml model-tiers 段把强档覆盖为某模型
- **THEN** sdflow-done 的 verify 子代理按覆盖映射选模型；无覆盖时用规则文件中本机队的强档缺省，MUST NOT 落到弱档

#### Scenario: 同一门禁步在两宿主下各取本机队档位〔add-codex-host-support〕
- **WHEN** verify 步分别在 Claude 宿主与 Codex 宿主运行且无 per-repo 覆盖
- **THEN** 前者取 Claude 机队强档、后者取 Codex 机队强档；两者 MUST NOT 因宿主切换而降档（门禁步禁降档是硬约束）

### Requirement: 跨模型 outside voice 默认开、失败回落且非阻塞

sdflow-spec-review 与 sdflow-code-review SHALL 默认启用跨模型 outside voice（**另一个机队**的「找漏」第二意见）：sdflow-code-review 每次自带 code outside voice；sdflow-spec-review 复用 autoplan 产物中的 outside-voice findings（见反静默守卫 Requirement）。

**runner MUST 由宿主决定，MUST NOT 硬编码**〔add-codex-host-support〕：runner 恒为**当前宿主之外的另一个机队的强档**（Claude 宿主 → Codex；Codex 宿主 → Claude）。`preflight` MUST 探测**目标 runner 的 CLI**，而非固定探测 codex——固定探测 codex 会在 Codex 宿主下返回 ready 并导致 **codex 自审 codex**，是必须杜绝的假绿。是否启用由环境决定——目标 runner CLI 未安装即天然关停（工作层不设软 off-switch，〔grill-amendment Q3〕）；目标 runner 不可用（未装/未认证/报错/超时）时 MUST fallback 到同 prompt 的 fresh **同宿主**只读子代理，且该轮 `runner == host`（如实标为非跨模型）；宿主判不出（`host="unknown"`）时 MUST NOT 跑 voice（无从确定"另一个机队"）。一切失败均为 informational，MUST NOT 阻塞评审流程。

报告 outside-voice 留痕 MUST 使用模板写死的 v1 机器锚行（严格 KV、按调用位点复数化、guard/runner 正交）：`<!-- sdflow:outside-voice v1 site="…" guard="…" host="claude|codex|unknown" runner="claude|codex|none" reason_code="…" findings="N" truncated="…" -->`〔add-codex-host-support：新增 `host=`；`runner` 枚举收缩为机队家族 + `none`（spec-review-amendment D6：无执行轮次如 host-unknown/secret-hit 用 `runner="none"`，MUST NOT 任选家族伪造"谁执行"），**`claude-fallback` 废弃**——「跨模型性」自此为派生量、由 `host-adaptive-execution` 合法组合矩阵判定（`host,runner∈{claude,codex}∧runner≠host∧reason_code="ok"`），MUST NOT 再编码进枚举值、MUST NOT 简写为裸 `runner≠host`（被 `runner="none"` 击穿，spec-review-r2 C1）〕（确定性机判，不押自然语言；人类原因文本在锚行外）〔grill-amendment Q5 + spec-review-amendment 文法 v1〕；评审收尾步 MUST 机械自检锚行存在，缺失即报错〔spec-review-amendment〕。

#### Scenario: Claude 宿主下跑跨模型 voice
- **WHEN** sdflow-code-review 运行于 `host=claude` 且 codex preflight 返回 ready
- **THEN** 经共享 helper（`render-prompt` 同源拼接，exec 硬编码 `-s read-only --ephemeral`，最终消息经 `--output-last-message` 提取）调 codex（5min 封顶），findings 进合并池，锚行记 `host="claude" runner="codex"`

#### Scenario: Codex 宿主下跑跨模型 voice〔add-codex-host-support〕
- **WHEN** sdflow-code-review 运行于 `host=codex` 且 `claude` CLI preflight 返回 ready
- **THEN** 经**同一个** helper（同一 `render_prompt`/`secret_scan`/截断）调 `claude -p --model <Claude 强档> --output-format text --tools "Read,Grep,Glob" --strict-mcp-config --add-dir <repo_root>`〔spec-review-r3 C4：**只读全仓**（对称 codex `-C repo_root -s read-only`），三旗齐全（只读工具集 + MCP 隔离 + `--add-dir` 增量授权确保覆盖仓库）；非零工具、非 `--disallowedTools`/`--allowedTools`；见能力 host-adaptive-execution「出境安全」〕，findings 进合并池，锚行记 `host="codex" runner="claude" reason_code="ok"`

#### Scenario: 目标 runner 不可用回落同宿主子代理
- **WHEN** preflight 返回 not_installed（目标 runner 的 CLI 未装）
- **THEN** 以 `render-prompt` 输出的同一 prompt 派 fresh 同宿主只读子代理兜底，评审继续不中断，锚行记 `runner` 等于 `host` + `reason_code="not-installed"`（该轮非跨模型，如实可见）

#### Scenario: exec 超时与报错分别留痕〔spec-review-amendment：原合并场景拆分〕
- **WHEN** exec 超时（exit 124）或非零报错（exit 1，含 auth 失败，stderr 转发）
- **THEN** 分别以 `reason_code="timeout"` / `reason_code="exec-error"`（附 stderr 摘要于锚行外）回落同宿主子代理，两类可在报告中区分

#### Scenario: 无目标 runner 环境天然关停且留痕
- **WHEN** 运行环境未安装目标 runner 的 CLI
- **THEN** preflight 返回 not_installed，回落同宿主只读子代理并留痕，不存在需要另行关闭的软开关〔grill-amendment Q3〕

#### Scenario: 宿主判不出则不跑 voice〔add-codex-host-support〕
- **WHEN** `CLAUDECODE` 与 `CODEX_THREAD_ID` 两个正信号皆无（或同时存在，信号冲突）
- **THEN** 本轮 MUST NOT 跑 outside voice；锚行记 `host="unknown" runner="none" reason_code="host-unknown"`（D6）；报告显著标注本轮无跨模型第二意见，MUST NOT 任选一个 runner 跑了充作跨模型

### Requirement: outside-voice 复用挂反静默守卫
sdflow-spec-review 复用 autoplan 产出的 `gstack-review.md` outside-voice findings 时，SHALL 校验产物有效性，按序判定：①**来源**——`step1-broad-review` 锚行为 `simulated` 则产物一律视同无效（模拟广审可臆造格式合规的 codex 段，结构性检查挡不住）〔spec-review-amendment〕；②**新鲜度**——产物早于 change 最新改动视同缺失（guard=stale）〔spec-review-amendment〕；③**结构**——文件缺失 / 解析不出 codex 段（解析锚定 adr/0002 的 `codex#N` 标签约定）/ findings 为 0 条。任一不过 MUST 打印带原因码（file-missing / section-not-found / zero-findings / stale / simulated-source）的显式降级日志并回落自跑 codex 设计 outside voice，MUST NOT 静默当「本次无 voice」跑过；诱因为文件整体缺失时措辞 MUST 声明「仅补偿 outside-voice 切片，广审其余镜仍缺」〔spec-review-amendment〕。C2 复用的前提是 autoplan 每次都跑（P2b）；若 autoplan 未跑，spec-review MUST 自跑设计 outside voice。

#### Scenario: autoplan 产物有效则复用不重开
- **WHEN** `gstack-review.md` 来源为 native、晚于 change 最新改动、且解析出 ≥1 条 codex outside-voice finding
- **THEN** 直接纳入合并池，不重复调 codex（避免双 codex），报告记「复用 autoplan outside voice N 条」

#### Scenario: 产物缺失或 0 条触发守卫回落
- **WHEN** `gstack-review.md` 缺失 / 解析不出 codex 段 / codex findings 为 0 条
- **THEN** 打印带原因码的降级日志并自跑 codex 设计 voice，锚行记 guard 原因

#### Scenario: 模拟来源或过期产物不得复用〔spec-review-amendment〕
- **WHEN** `gstack-review.md` 的 step1 锚行为 `simulated`，或其内容早于 change 最新改动
- **THEN** 视同产物无效（guard=simulated-source / stale），回落自跑，MUST NOT 因其格式完整而复用

### Requirement: 高风险领域 cross-model 由 HR-TG 子集判定并留痕

两评审 skill 的规划镜头步 SHALL 顺带判定：本变更命中的 TG 集合 ∩ HR-TG 子集 {TG-04, TG-06, TG-07, TG-08, TG-09, TG-16, TG-17, TG-26} 是否非空；非空则单开领域专属 cross-model（聚焦命中的高风险域，「找领域镜漏的」）。判定结果无论正反 MUST 写入报告（可审计）。

机器锚行 SHALL 为 `<!-- sdflow:hr-tg v1 hit="…|none" declared="…" evidence="…" -->`〔grill-amendment Q1：回灌 declared= canonical〕，三字段语义分工：`hit=`/`declared=` 由 `hr_tg_intersect` 脚本 emit（`declared=` 承模型判定的完整命中集、canonical 必填，`hit=` = `declared ∩ HR-TG`），`evidence=` 为并存人读复核字段——`hit≠none` 时 MUST 给判据触发点且非空（哪处变更对应哪个 TG，30 秒可人工复核）。HR-TG 子集清单以 trigger-catalog 为单一源，SKILL 只引用 ID。

> 〔为何三字段〕`declared=`（脚本、机器可重算）与 `evidence=`（人手、给复核）正交并存：`declared` 使模型判定的完整命中集显式可见（adr/0018），`evidence` 承人读判据。mlh-p4 加 `declared=` 于码却未回灌本 requirement（仍写 evidence= 单字段），本次回灌统一。

#### Scenario: 命中 HR-TG 单开领域 cross-model
- **WHEN** 规划镜头判定命中 TG-08（外部依赖）
- **THEN** 单开一次领域 cross-model（codex，失败照常回落），报告记「命中 TG-08 → 已跑领域 cross-model」；锚 `hit=` 含 TG-08、`declared=` 含模型判定全集、`evidence=` 非空

#### Scenario: 未命中则不开且留痕
- **WHEN** 命中集 ∩ HR-TG = ∅
- **THEN** 不开领域 cross-model，报告记「HR-TG 判定：未命中」；锚 `hit="none"`、`declared=` 承模型判定集（可为空）

### Requirement: outside-voice tension 不静默采纳

outside voice 与主审分歧（tension）SHALL 中立并陈、标 TENSION：sdflow-spec-review 写入报告决策登记区（选项 + 推荐 + 两方视角 + **三面后果（系统 / 用户 / 开发循环）+ 主次判定**，设计 HARD-GATE 人一次性拍板）；sdflow-code-review 按 T10 三级协议自动裁决（有客观判据自动裁 / 无则派对抗镜复核 / 复核不过或无从复核则 defer 进 buglist/todolist + hand-off）并**按三镜 + 主次记理由**，MUST NOT 以自评置信（"有把握"）为自动裁决唯一依据〔impl-review-fix F1/CV2〕。outside voice 的建议 MUST NOT 被静默自动采纳（不直接改代码/设计而不留痕）。

**置信过滤豁免 SHALL 按合法组合矩阵的「跨模型」判定，MUST NOT 自写 `runner ≠ host` 或按 runner 枚举值硬编码**〔add-codex-host-support · spec-review-r2 C1〕：**矩阵判「跨模型」为真**（`host,runner 均∈{claude,codex} ∧ runner≠host ∧ reason_code="ok"`）的 outside-voice findings MUST NOT 经自评置信阈值（<80）预过滤——跨模型自评不可比、异见易被同族标尺误杀——一律直通对抗裁决，被裁掉的连理由落报告「已裁掉」区〔grill-amendment Q4〕；**其余**（同族 fallback `runner==host`、**及无执行 `runner="none"`**）照过同族置信滤（豁免理由对其不成立；`runner="none"` 的 findings 恒 0、豁免无意义）。

> 〔为何引用矩阵而非自写 `runner≠host`〕旧规则写死 `runner=codex` 豁免——该值在 Codex 宿主下恰恰是**自审**；而首轮改的 `runner ≠ host` 又被 `runner="none"` 击穿（`none≠host` 恒真 → 无执行轮被误豁免，spec-review-r2 C1）。∴ 判据 MUST 引用合法组合矩阵的单一「跨模型」判定，不在此重写关系式。

#### Scenario: 设计侧分歧进决策登记区
- **WHEN** outside voice 与 spec-review 主审对同一设计点结论相反
- **THEN** 报告决策登记区新增 TENSION 条目（两方观点 + 推荐 + 三面后果 + 主次判定），不中途 AskUserQuestion

#### Scenario: 代码侧分歧自动裁决或 defer
- **WHEN** outside voice 与 code-review 主审分歧且裁决无客观判据
- **THEN** defer 进 issues 池并写入 hand-off，不静默采纳任一方

#### Scenario: 低自评置信的跨模型 finding 不被预筛
- **WHEN** 某条 `runner ≠ host` 的 finding 自评置信低于 Step3 阈值（<80）
- **THEN** 该条仍进入对抗裁决（不被置信滤拦截）；若裁决不成立，连理由落报告「已裁掉」区

#### Scenario: 同族 fallback finding 照过同族滤
- **WHEN** 某条 `runner == host` 的 finding 自评置信低于阈值
- **THEN** 按同族 findings 常规处理（过滤规则一致），不享受跨模型豁免

#### Scenario: Codex 宿主下的 codex findings 不再误享豁免〔add-codex-host-support〕
- **WHEN** `host="codex"` 且某条 finding 的 `runner="codex"`（同族 fallback 产物）
- **THEN** 照过同族置信滤，MUST NOT 因 `runner` 值恰为 `codex` 而豁免（旧规则的假绿点）

### Requirement: 广审层原生执行，模拟必须显式标注降级
两评审 skill 的 Step1 广审（sdflow-spec-review 的 autoplan、sdflow-code-review 的 gstack /review）SHALL 由主 session 经 Skill 机制原生执行（其指令直接进主 session，非子代理读 SKILL.md 转述模拟）。原生执行完成后由主 session 汇总结论落盘 `gstack-review.md`（广审工具自身无「写任意路径」机制，落盘责任在编排方）〔spec-review-amendment〕。原生执行不可用时 MUST 降级为模拟广审，且报告与运行日志 MUST 显式标注「模拟广审（降级模式）」，MUST NOT 把模拟呈现为原生运行；报告 Step1 段 MUST 含 v1 机器锚行 `<!-- sdflow:step1-broad-review v1 mode="native|simulated" -->`，native 声明建议附侧信道佐证（如广审工具自身的运行痕迹）〔grill-amendment Q5 + spec-review-amendment〕。

#### Scenario: 正常路径原生执行 autoplan
- **WHEN** sdflow-spec-review Step1 启动且 autoplan skill 可用
- **THEN** 主 session 原生执行 autoplan（含其 preamble/telemetry/自动决策全流程），产出 `gstack-review.md`

#### Scenario: 原生不可用显式降级
- **WHEN** autoplan / gstack review skill 不可用（未安装等）
- **THEN** 以子代理模拟广审，报告显式标注「模拟广审（降级模式）」及原因

### Requirement: gstack 边界守恒——读产出物合法、依赖内部禁止
自制 outside-voice 机制（共享 helper、spec-review 回落自跑、code-review code voice）SHALL 只依赖 codex CLI 本身，MUST NOT 调用、复制或修改 gstack/superpowers 内部 bin、探针、config；gstack 自家 skill（autoplan / gstack review）的原生 outside voice 原样不动。读取 gstack 的产出物（如 `gstack-review.md`）合法，不属内部依赖。

#### Scenario: 实现不触碰 gstack 内部
- **WHEN** 本 change 实现完成
- **THEN** 变更 diff 不含任何 gstack 安装目录/内部文件；helper 源码 grep 不到 gstack 内部路径引用

#### Scenario: 无 codex 无 gstack 环境审查不中断
- **WHEN** 在既无 codex CLI 也无 gstack 的环境运行两评审 skill
- **THEN** outside voice 退化为 fresh-context Claude 子代理（独立性保留、丢跨模型），评审完整跑完

### Requirement: checkpoint 标签 producer→parser 契约测试

checkpoint 任务标签由 `checkpoint-commit.sh`（producer，把首参包成 commit subject，**format-agnostic：不认识 task 格式，仅执行包裹动作、非格式源**）铸造、由 `ship_gate.py` 的 `TAG_RE`（parser，**格式形状的权威**）解析；这条 producer→parser 链 MUST 有机械绑定测试守卫，SHALL NOT 依赖对文档占位符文本的比对（文档是人读占位符、非机器解析对象）。测试 MUST 调用**真实脚本**产出 subject 再喂 parser，使 producer 包裹逻辑或 parser 正则任一漂移即令测试失败。此为纯防漂移加固，`TAG_RE` 与 `checkpoint-commit.sh` 的行为 MUST 逐字不变。**文档/spec 中展示的标签形状 MUST 标注为样例（权威形状见 TAG_RE），占位符 MUST 用无歧义写法 `<change-slug>`，MUST NOT 用易被误读为"须填真实 slug"的 `<当前change>`**〔T37/T38〕。

#### Scenario: 真实脚本产出的 subject 被 parser 正确识别

- **WHEN** 契约测试在临时 git repo 中以命名空间形式的首参调用真实 `checkpoint-commit.sh`（首参 = `<change-slug>:task<号>-<slug>` 形态，此处为样例占位符、权威形状见 TAG_RE）
- **THEN** 测试 MUST 读回该次 commit 的 subject 并断言 `ship_gate.py` 的 `TAG_RE.match` 成功、捕获组分别等于该 change 名与该任务号；MUST 用真实脚本调用与真实 git commit（MUST NOT 用手写字符串 mock subject——否则放过 producer 包裹漂移）

#### Scenario: 裸格式经真实脚本产出仍被识别且命名空间组为空

- **WHEN** 契约测试以裸形式首参（`task<号>-<slug>`，无命名空间前缀）调用真实 `checkpoint-commit.sh`
- **THEN** 测试 MUST 断言 `TAG_RE.match` 成功、命名空间捕获组为 `None`、任务号捕获组正确——固定裸格式向后兼容在 producer→parser 链上的实际行为

### Requirement: TAG_RE 负例矩阵

`TAG_RE` 的正确性 MUST 由一组 **MUST NOT match** 的负例断言守卫，SHALL NOT 仅以单个 happy 正例（match + 捕获正确）覆盖——单正例对正则放松无区分力（已实证：尾 dash 变可选 / 命名空间允许大写 / 编号可空 三类放松在仅有正例时均静默保绿）。负例集 MUST 至少覆盖这三类已知放险。

#### Scenario: 已知放松类被负例矩阵挡住

- **WHEN** 负例矩阵对一组畸形 subject 断言 `TAG_RE.match`
- **THEN** 对"无尾 dash"（如 `checkpoint(task1slug)`）、"大写命名空间"（如 `checkpoint(DEMO:task1-)`）、"编号位非数字或为空"（如 `checkpoint(task-1-)`）三类，`TAG_RE.match` MUST 返回 `None`；使 `TAG_RE` 被无意放松时至少一条负例转红、MUST NOT 因只有 happy 正例而静默保绿

### Requirement: checkpoint 标签契约单一真相源与模板样例一致性

checkpoint 任务标签形状（`checkpoint(<change>:task<N>-<slug>)`）的**格式权威 MUST 唯一落在 `ship_gate.py` 的 TAG_RE 解析器**（enforcing parser，MUST 带 canonical-shape 头注释说明规范形状），并由 `test_producer_parser_contract.py` 钉死 producer↔parser 一致；**`checkpoint-commit.sh` 为 format-agnostic 透传（只裹 `checkpoint($step)`、不认识 task 格式），MUST NOT 被引作格式源**。「plan 每任务 commit 步 MUST 用命名空间标签」这条**工作流规则** MUST 就地留 `workflow.md` 一处（含格式串一次并标"形状由 TAG_RE 执行/契约测试钉死"），`sdflow-ship`/`sdflow-code-review` SKILL、本 spec 的 Scenario MUST 以**引用式**指向，MUST NOT 各自复述完整格式串（复述 = doc 副本，会漂）。文档/spec 中标签占位符 MUST 用无歧义写法（如 `<change-slug>`），MUST NOT 用易被误读为"须填真实 slug"的写法（如 `<当前change>`）——占位符语义 = 任意 demo 值。凡**展示 ship-gate 机器锚样例**（`<!-- ship-gate: X -->`）的模板 MUST 把锚写成独占 bare line（无反引号包裹、无同行尾注），与真产报告一致（对齐既有「各模板 MUST 把锚写在独占一行」需求），防报告照抄模板致 gate 行级锚 `strip()≠字面` 漏判/假命中。**人读格式串防漂移**〔spec-review-amendment SR-4〕：workflow.md 保留的人读格式串（贴"权威见 TAG_RE"标签）是文本、非技术约束——MUST 有一道**机械钩子**兜底（`TAG_RE` 定义旁的显式 checklist 项「改此正则前先搜 workflow.md 格式串同步」，或一条弱校验测试断言 workflow.md 该行与 TAG_RE 语义不漂），MUST NOT 仅靠"非权威"标签这一人肉记忆。

#### Scenario: 改标签格式只改一处
- **WHEN** 需调整 checkpoint 标签格式
- **THEN** 格式权威在 TAG_RE，改它一处 + `test_producer_parser_contract.py` 守卫；`workflow.md` 规则一处、SKILL/spec 引用式，MUST NOT 存在第二份需手工对齐的完整格式串；MUST NOT 因 `checkpoint-commit.sh` 被误当格式源而在其 `--help` 复制一份权威格式定义

#### Scenario: 占位符不被误读为真实 slug
- **WHEN** 实现者读 spec/doc 中的 checkpoint 标签示例
- **THEN** 占位符写法（`<change-slug>` 等）明示其为任意占位 demo，MUST NOT 让人误以为示例里的字面串是必须照填的本 change 真实 slug

#### Scenario: ship-gate 锚模板为独占 bare line
- **WHEN** 任一 SKILL 模板展示 `<!-- ship-gate: ... -->` 锚样例（如 design-approved / verify / code-review）
- **THEN** 该样例锚独占一行、无反引号包裹、无同行尾注；照抄该模板产出的真报告，其锚行 `strip()` 后整行等值于锚字面，能被 gate 的行级字面查找正确解析（不因装饰字符或尾注致漏判）

### Requirement: gate 新鲜度判定不纳入工作树 dirty 状态

`ship_gate.py` 的产物新鲜度判定 MUST 只依据**已提交盘面**（committed 产物与结论锚行），MUST NOT 将工作树 staged/unstaged/untracked 的非-openspec 改动纳入判定——与"盘面即状态 = committed 产物"地基一致〔T33/T35 定夺〕。`sdflow-ship` 编排器 MAY 在收尾以**非门禁软提示**告知"工作树存在未提交改动、gate 判定不含它们"，该提示 MUST NOT 改变 gate 的推进/拒绝语义。**merge 边界硬检查（缩简版）**〔spec-review-amendment SR-2〕：`sdflow-done` 的 merge 步 MUST 在 merge 前检查工作树是否存在**本 change 分支生命周期内新产生的未追踪（untracked）文件**——存在则 **MUST 以 halt+报告（非交互）方式停下并上抛人工**（防"未追踪工作经 checkout+ff-merge 存活于磁盘却从未进 base git 历史 → 看似还在、实际从未 ship 进 base"）；此"停"MUST 复用 sdflow-done 既有的非交互 halt 惯用法（如"ff 不可行→停下报告"），**MUST NOT 引入阶段三中途 AskUserQuestion**（守既有"阶段三全程无 AskUserQuestion / 无人类阻塞门"MUST）。判据 MUST 排除仓库既有 debris（仅圈分支内新产 untracked）。此检查落 `sdflow-done`（merge 卫生前提），MUST NOT 上移进 gate（不污染盘面即状态）。**范围边界**：tracked 非-openspec 改动被 commit 步 `git add -u` 先行提交的一路〔codex-2〕本 change 不处理，defer todolist。

#### Scenario: 工作树 dirty 不改变 gate 判定
- **WHEN** gate 运行时工作树含未提交的非-openspec 代码改动，而已提交盘面满足推进条件
- **THEN** gate 照常判可推进（committed-only），MUST NOT 因工作树 dirty 判失鲜或拒绝；如有软提示则仅信息性、不影响退出码

#### Scenario: merge 前 untracked 硬检查以 halt 上抛
- **WHEN** `sdflow-done` 到 merge 步时工作树有本 change 分支内新产生的未追踪文件
- **THEN** merge 步以非交互 halt+报告停下、上抛人工先处理（commit 或确认无关），MUST NOT 静默 ff-merge、MUST NOT 用 AskUserQuestion 中途问；判据排除仓库既有 debris；仅当无此类 untracked（或人工处理后重入）才 merge

### Requirement: gate 熔断重试计数为编排器短时职责，不持久化下沉

阶段三熔断（同一 invocation 内同一步重跑一次仍无进展 → 按 UNKNOWN 停上抛）的**重试判定 MUST 由编排器在单 invocation 内短时持有**，MUST NOT 持久化为跨 turn / 跨步状态——持久化会撞"ship 零跨步状态"〔D9〕与"盘面即状态 / gate 零副作用"〔adr/0006〕三条红线〔T26 定夺：持久化不下沉〕。**触发判据 MUST 以「该步 ship-gate 锚行集合是否变化」为准**〔spec-review-amendment SR-1：原"HEAD 未移动+报告 mtime/sha 未变"判据被证失效——HEAD 移动是 OR 逃逸口（修复类步几乎必产 commit → HEAD 动即判"有进展"→ 熔断永不触发、无限循环复现），mtime/sha 亦弱信号〕：重跑一步前后，比较该步报告的**锚行集合**（复用 gate 的 `_line_scoped_hits`/`anchors_in` 语义，即 gate 真正关心的结论锚）——锚行集合无净变化即判无进展、停上抛人工；`HEAD` 移动与否、文件 mtime 变化与否 MUST NOT 作为免疫信号。此比较 MUST 做成**无状态比较（gate 子命令 / 小脚本）**：两次锚行快照由编排器在单 invocation 内持有、作参数传入，helper 不落地任何文件、不跨 invocation 持久化（故不撞 D9；复议了原被误否决的候选 C），且可 CI 断言。**fail-safe**：**任一快照缺失**（before 或 after，如 context 压缩丢记录、或重跑后报告不存在/不可读）MUST 保守判"无进展"（停上抛），MUST NOT 默认放行再跑〔impl-review-fix CR-2：非对称 fail-safe 会让 after 缺失时假放行〕。**判据按 verdict 分治**〔impl-review-fix CR-1〕：锚行集合判据**仅适用 `STEP_IN_PROGRESS`**（报告在但无结论锚，进展信号=锚出现）；**`RERUN_STALE`**（报告有锚但陈旧，进展信号=新鲜度刷新、锚常不变如 pass→pass）的熔断 MUST 以「重跑后 gate 仍返回同一 `RERUN_STALE`」为准，MUST NOT 用锚集不变误判（否则正常刷新被假熔断误杀）。SOP/plan/impl 等非单一报告步不适用〔codex-5〕。

#### Scenario: 熔断触发靠锚行集合变化而非 HEAD/mtime
- **WHEN** 同一 invocation 内某有锚报告步重跑，重跑后该步报告的 ship-gate 锚行集合与重跑前相同（即便期间 HEAD 因修复 commit 前移、或报告 mtime 变化）
- **THEN** 编排器判无进展、触发熔断（UNKNOWN 停上抛人工）；MUST NOT 因 HEAD 已移动或 mtime 已变而判"有进展"放行；比较经无状态 helper（快照作参数），MUST NOT 写任何跨步/跨 turn 状态文件；快照缺失时保守判无进展；跨 invocation 重调 `/sdflow-ship` 时判定不延续

### Requirement: 评审每镜落度量锚为生产者义务，取代 voice 分桶 prose

`sdflow-spec-review` 与 `sdflow-code-review` 编排器 SHALL 在 Step3 裁决后为每个参与镜（`domain`/`adversarial`/`grounding`（spec-review）/`history`（code-review）/`outside-voice`/**`broad`**）落一行 `sdflow:lens-metric v1` 锚（契约见 `workflow-metrics` 能力），其中 code-review 现有的 `voice分桶` 自由 prose 行 SHALL 被 outside-voice 镜的 `lens-metric` 锚**吸收取代**（grep 报告 MUST NOT 再有残留自由文本分桶）。度量锚 SHALL 为旁路记录：其有无 MUST NOT 改变 findings 的采纳与否或评审的推进/拒绝结论。

〔spec-review-amendment SR-L〕`broad` 行的 `findings/采纳/独立` 口径 = 主 session 汇总 `gstack-review.md` **去重后**计入（非各子声原始条数总和）；code-review 的 Step1 `gstack/review` 与 spec-review 的 Step1 autoplan 均折叠为 `layer=<层> lens=broad`。

〔spec-review-amendment SR-M〕**spec-review 度量锚在设计门拍板后最终化**：spec-review 的 `采纳/裁掉/defer` 因中置信项在设计 HARD-GATE 由人翻改，其 `lens-metric` 锚 SHALL 在**拍板回写协议**执行时（与 `<!-- ship-gate: design-approved -->` 同步）最终确定/重算，反映门后最终裁决，MUST NOT 用 Step3 pre-gate 的临时裁决充当最终采纳率（code-review 阶段三无人类门、Step3 即最终，无此步）。

〔spec-review-amendment SR-G · 决策门 Q2=A 已定〕**度量落锚受 config 门控，消费仓默认关**：落锚义务 SHALL 受 `config.yaml` 的度量开关门控——**源仓（sdflow-skills，高频 dogfood）默认 on，消费仓默认 off**；关闭时两 SKILL SHALL NOT 落 `lens-metric` 锚、缺锚 SHALL NOT 触发阻塞（低频小仓零收益期不背记账+硬阻塞成本）。bundle 基础设施 MUST NOT 把「仅高频仓用得上」的义务无条件硬铺给所有下游。

#### Scenario: 消费仓默认关闭度量不阻塞
- **WHEN** 一个消费仓（config 度量开关未显式开启）跑 code-review
- **THEN** 两 SKILL SHALL NOT 落 `lens-metric` 锚、缺锚自检 SHALL NOT 报错阻塞（度量对该仓关闭）；源仓开关默认 on 则照常落锚+自检

#### Scenario: code-review 落锚并消除 voice 分桶 prose
- **WHEN** 一轮 code-review 完成裁决
- **THEN** 报告 SHALL 为 `domain`/`adversarial`/`history`/`outside-voice`/**`broad`(gstack/review)** 各落一行 `lens-metric` 锚，且 SHALL NOT 再含 `voice分桶: codex 采纳x/裁掉y...` 自由 prose 行〔spec-review-amendment SR-L：显式列 broad〕

#### Scenario: spec-review 落锚
- **WHEN** 一轮 spec-review 完成裁决
- **THEN** 报告 SHALL 为领域镜/对抗镜/接地镜/outside-voice/broad 各落一行 `lens-metric` 锚

#### Scenario: 度量锚为旁路不改判定
- **WHEN** 度量锚落锚失败或字段缺失被自检拦截
- **THEN** 拦截的是**报告完整性**（机械失职），SHALL NOT 反向改写已裁决 findings 的采纳结论——锚是旁路观测，非评审判定输入

### Requirement: reindex 一致性问题可观测且不阻断重建

`issues.py reindex` SHALL 把子进程 `scan` 报出的 index↔block 一致性 problems **回显到 stderr**（逐条带 pool / 文件定位），使独立跑 reindex 时的不一致对用户可见。**默认**：非致命 problems（如 legacy 表 arity、孤儿/缺失 prose block）非空 MUST NOT 使 reindex 失败——INDEX SHALL 照常从所有可判 item 确定性重建、退出码为 0。reindex SHALL 提供 **`--strict`** 选项：problems 非空时以非 0 退出，供非交互调用/收尾门 enforcement。**致命错误**（文件不可读、`sdflow-issues` namespace 在场但 schema/JSON/枚举/ID 损坏、跨文件语义重复 ID）无论是否 `--strict` 均 MUST 非零退出且不得写新 INDEX/batches snapshot。

读侧盘面完整性 SHALL 按格式分流：legacy table 继续校验 8/7 列 arity；canonical/overlay 校验严格 frontmatter schema。overlay 内 frontmatter shadow 同文件 legacy ID 是合法迁移语义，不得误报重复；同一 canonical ID 出现在不同文件仍为致命冲突。reindex 的 INDEX 与 batches 同步 MUST 使用同一份已校验 snapshot，MUST NOT 在两份输出间重新读取形成不一致时点。

#### Scenario: problems 回显 stderr 但不阻断 INDEX 重建
- **WHEN** 池中某 dated 文件存在非致命 index↔block 不一致，运行默认 `issues.py reindex`
- **THEN** 每条 problem 逐条出现在 stderr（含 pool/文件定位），INDEX 仍从可判 snapshot 完整重建，退出码为 0

#### Scenario: 独立跑 reindex 时不一致不再静默
- **WHEN** 不经独立 `scan`、直接运行 reindex，且池中存在非致命一致性问题
- **THEN** 用户从 stderr 看到具体问题，而不是静默重建或吞掉 problems

#### Scenario: --strict 下 problems 非空即非零
- **WHEN** 以 `reindex --strict` 运行且池中存在非致命 problems
- **THEN** problems 回显后以非 0 退出；同一数据下默认 reindex 仍 exit 0 并生成 INDEX

#### Scenario: malformed recorder namespace 始终致命
- **WHEN** 任一 dated 文件的首块含 `sdflow-issues` 但 schema、JSON、字段或枚举损坏
- **THEN** reindex 无论是否 `--strict` 都非零退出并保持既有 INDEX/batches 逐字节不变，MUST NOT 以 legacy table 或部分 item 重建

#### Scenario: legacy arity 检查永久保留在历史读半场
- **WHEN** legacy table 某行不是 7/8 列且文件无有效 recorder namespace
- **THEN** scan 把该行作为带定位的 problem 回显；默认/strict 语义分别保持非阻断/阻断，MUST NOT 因新写已迁 frontmatter 而删除历史 arity 检查

#### Scenario: overlay shadow 不制造假重复 problem
- **WHEN** 同一 overlay 文件中 frontmatter item 与 frozen legacy row ID 相同
- **THEN** reindex 使用 frontmatter 当前值且不产生 duplicate problem；若相同 canonical ID 位于另一文件，则致命失败

### Requirement: issues sweep 原子子命令（机械活脚本化）

`issues.py` SHALL 提供 `sweep --change X` 子命令，把 `sdflow-done` 收尾的 issues 分诊从「模型手跑 4 步 bash 循环」固化为一次**确定性、非原子、fail-closed、可重跑收敛**的操作（roadmap `mechanical-layer-hardening` 阶段 1，兑现 adr/0006「机械 prose 协议 MUST 脚本化」）。

sweep 的所有子步 SHALL 走 subprocess CLI（不直调 cmd_* 函数，避 args-namespace 脆弱性），依次：① **入口守卫**——`args.change` 非空（`strip()` 后非空）且过 `_reject_batch_key_unsafe`（拒 `|`/换行/` — `/首尾空白），**MUST 先于任何写盘**（否则空 change 精确误纳孤儿、含 ` — ` 的 change 污染项后才被拒）；② 子进程 `scan --change X --open-ungrouped --json` 扫 buglist + todolist 两池（`--open-ungrouped` = 源==X ∧ 非终态 ∧ 批次空，单原语，MUST NOT 用 `--status OPEN`——后者只精确匹配 OPEN、漏非终态、不过滤批次空）；③ 逐项子进程 `triage --id {id} --批次 X`（bug 走 buglist.py、todo 走 todolist.py），每项 MUST 查子进程 returncode、非零即中止；④ `issues.py batch add X --if-exists skip`（MUST 带 `--if-exists skip`——默认对已存在 key 是 `_die` 报错，不带则幂等重跑破产）；⑤ `issues.py reindex`。

sweep SHALL 幂等——靠 ① triage 既有幂等（已 PROPOSED / 已终态 no-op）+ ② `batch add --if-exists skip`（已存在 key no-op）+ ③ reindex 确定性重建；sweep 自身无状态、可安全重跑。sweep SHALL 只圈 `源==X` 的项，**空 `--change` MUST 被入口守卫拒绝**（防 `源==""` 误纳源为空的孤儿项）；孤儿项（源="")在合法非空 change 下天然不匹配、不纳入。sweep SHALL fail-closed 且**非原子**——任一子步（scan / 某项 triage / batch add / reindex）非零退出时，sweep 整体 MUST 以非零退出、stderr 报明**失败步 + 失败点位**（第 i 项 / 哪个 pool / 已成功 tag 的 id 列表），MUST NOT 静默继续。sweep 的部分失败 SHALL **重跑收敛**——已 tag 项在重跑时被 `--open-ungrouped` 的「批次空」过滤排除、未 tag 项补做、batch add 补建、reindex 收敛到完成。

`sdflow-done/SKILL.md` §2.1 sweep 子步 SHALL 调 `issues.py sweep --change {本change}` 取代手写 4 步循环，保留「孤儿项不归本 sweep」「显式传 --change 不靠 detect_change 猜」边界声明。

#### Scenario: sweep 用 --open-ungrouped 口径扫全非终态未分批项
- **WHEN** 池中有 `源==X ∧ 批次空` 的项，状态含 OPEN 与 VERIFIED/IN_PROGRESS/BLOCKED（非终态非 OPEN）
- **THEN** sweep MUST 经 `scan --change X --open-ungrouped` 把这些非终态未分批项**全部**纳入 triage（不因 `--status OPEN` 漏掉非 OPEN 的非终态项）；已在别的批次（批次非空）的项 MUST NOT 被 clobber

#### Scenario: 幂等重跑退出码 0（batch add --if-exists skip）
- **WHEN** 对同一 change X 连跑两次 `sweep --change X`
- **THEN** 第二次 SHALL 无副作用（triage no-op、`batch add --if-exists skip` no-op、reindex 幂等）、退出码 0；MUST NOT 因 batch add 遇已存在 key 而 `_die` 非零退出

#### Scenario: 空 change 被入口守卫拒绝（防孤儿误纳入）
- **WHEN** 跑 `sweep --change ""`（或仅空白 / 含 ` — `/`|`/换行的 change）
- **THEN** sweep MUST 在任何写盘前 `_die` 非零退出；孤儿项（源="")MUST NOT 被 triage 进任何批次

#### Scenario: 某项 triage 失败 fail-closed 且重跑收敛
- **WHEN** sweep 逐项 triage 时第 i 项子进程非零退出
- **THEN** sweep MUST 整体非零退出、stderr 报明失败点位（第 i 项/pool/已 tag 的 id）；前 i-1 项已 tag 但 batches.md 未建/INDEX 未刷；重跑同一 sweep SHALL 收敛（已 tag 项被批次空过滤排除、剩余补做）

### Requirement: 评审报告锚自检由确定性脚本判定

spec-review Step3 / code-review Step5 的**评审报告锚自检**（四类 v1 锚存在性 + `sdflow:lens-metric` 字段/枚举/子格式合法性）MUST 由确定性脚本 `anchor_lint` 判定，MUST NOT 作为 prose 协议交执行模型手 grep + 肉眼核枚举（与 `resolve-workflow.sh`、`ship_gate.py`、`trivial_shape.py` 同族——机械协议脚本化，adr/0006）。脚本 MUST 只读、双输出（human 行 + JSON 机读）、以退出码承载判定（0=干净 / 非零=违规或脚本自身错误）；编排 SKILL MUST 调该脚本并遵其退出码，MUST NOT 静默吞非零退出。

脚本 MUST 校验：①四类锚存在性——`sdflow:outside-voice`、`sdflow:hr-tg`、`sdflow:step1-broad-review` 恒须存在，`sdflow:lens-metric` 受 `config.yaml metrics.enabled` 门控（关闭或 config 未配置 metrics 时缺此类 MUST NOT 阻塞；config 存在且 `metrics:` 块在但值非法 → fail-closed，见下 Scenario）；metrics 启用时 lens-metric 不止「≥1 条」——`lens="broad"` 与 `lens="outside-voice"` 各 MUST 至少一行（两者恒跑），缺即违规；其余 per-lens 完整性属主 session 信任边界。②`sdflow:lens-metric` 锚的字段校验——`layer`/`lens`/`runner` 枚举域、`sev` 子格式（`致N/高N/中N/低N`）、且 `layer` MUST 等于 CLI `--layer`（防错层度量锚漏网）、五计数字段 `findings`/`采纳`/`裁掉`/`defer`/`独立` MUST 为十进制非负整数。枚举取值域 MUST 从 `lens-metric-contract.md` 的 `lens-metric-enums` 机读块单一权威源读取而 MUST NOT 在脚本内复制清单。脚本 MUST 沿用 fence-aware 行级纪律（跳 fenced code block、锚独占行前缀匹配、受限 kv 解析），在脚本内重实现该纪律（与 `lens_metric_aggregate` 平行、同纪律、MUST NOT 跨 skill import）而 MUST NOT 用 `ship_gate` 的定长整行原语（匹配不了变长度量锚）。契约 `lens-metric-enums` 机读块 SHALL 为 layer/lens/runner/sev 的机读单一源，任何消费该枚举者（`anchor_lint` 运行时读、`lens_metric_aggregate` 硬编码）MUST NOT 与之漂移，一致性 SHALL 由测试守卫。**契约机读块 SHALL 与消费它的 `tools/` 脚本同批部署下发**（`sdflow-init` 刷新 `tools/` 时一并刷新 `lens-metric-contract.md`），使本地 pin 消费仓 MUST NOT 出现「新脚本 + 旧契约无块」的永久 fail-closed 错配。

`sdflow:lens-metric` 的 `site` 字段 MUST NOT 纳入越域自检——任意取值只多一个分组行、MUST NOT 触发报错（契约 CF-补2：仅 `layer`/`lens`/`runner`/`sev` 受自检约束）。锚行 `findings=N` 与合并池实收数的**数值一致性**MUST 显式声明为主 session 信任边界、**非机械可验**（主 session 自做去重又写锚、自核无独立性）——脚本 MUST NOT 谎称能机械保证数值正确，机械层只兜「存在 + 枚举域 + sev 子格式」。

#### Scenario: 干净报告自检通过

- **WHEN** 一份评审报告含全部恒须四类锚、且所有 `lens-metric` 锚字段齐全、枚举在域、`sev` 子格式合法，`anchor_lint --report <path> --layer <spec-review|code-review>` 运行
- **THEN** 脚本 SHALL 以退出码 0 返回、无违规输出；SKILL 自检步据此放行

#### Scenario: 缺恒须锚自检阻塞

- **WHEN** 报告缺失 `sdflow:outside-voice` / `sdflow:hr-tg` / `sdflow:step1-broad-review` 中任一恒须锚
- **THEN** 脚本 SHALL 以非零退出码返回并点名缺失锚类，SKILL 自检步 SHALL 报错阻塞，MUST NOT 静默放行

#### Scenario: lens-metric 越域枚举或缺字段或坏 sev 子格式被拦

- **WHEN** 某 `sdflow:lens-metric` 锚的 `layer`/`lens`/`runner` 取值越出枚举域、或缺任一必填字段、或 `sev` 不符 `致N/高N/中N/低N` 子格式
- **THEN** 脚本 SHALL 非零退出并点名违规锚与字段；枚举取值域 SHALL 从 `lens-metric-contract.md` 读取判定，MUST NOT 在脚本内复制枚举清单形成第二真相源

#### Scenario: site 任意取值不报错

- **WHEN** 某 `sdflow:lens-metric` 锚的 `site` 取一个不在常见集 {code-voice, hr-tg, design-voice, —} 内的值，但 `layer`/`lens`/`runner`/`sev` 均合法
- **THEN** 脚本 SHALL 判该锚合法（退出码不因 site 值而非零）——site 仅分组消歧、不纳入越域自检（契约 CF-补2）

#### Scenario: config 缺失或未配置 metrics 块时缺 lens-metric 锚不阻塞

- **WHEN** 下列之一：`config.yaml` 文件不存在；或文件存在但**无顶层 `metrics:` 块**（该键从未声明——消费仓常态，`sdflow-init update` 从不为已存在 config 注入新顶层键）。报告不含任何 `sdflow:lens-metric` 锚，四类恒须锚（除 lens-metric）齐全
- **THEN** 脚本 SHALL 判 `enabled=false` 并以退出码 0 返回——lens-metric 一类整体不校验不阻塞。**「无 `metrics:` 块」与「文件缺失」同属放行分支**（消费仓默认 false），MUST NOT 因未配置 metrics 而 ERROR 阻塞（否则 100% 未配置 metrics 的消费仓每轮评审假阻塞）

#### Scenario: metrics 块存在但值非法 fail-closed

- **WHEN** `config.yaml` 存在且有顶层 `metrics:` 块，但该块内（至下一顶层键前）**解不出合法 `enabled: true|false`**（拼错 / 非法布尔拼写 / 结构损坏）
- **THEN** 脚本 SHALL 以非零退出码（ERROR）返回、拒绝认证——MUST NOT 因 config 读取静默失败而悄悄跳过整类 lens-metric 校验（反静默）。「坏」严格限于**块在但值非法**；块**不在**走上一 Scenario 放行。块边界判定 MUST 先定位 `metrics:` 行再限范围至下一顶层键（防多段 config 误配对）

#### Scenario: metrics 启用时缺 broad 或 outside-voice 度量行被拦

- **WHEN** `metrics.enabled` 为 true，报告含若干 `sdflow:lens-metric` 锚但**缺 `lens="broad"` 或缺 `lens="outside-voice"` 行**（两者对应恒跑的 Step1 广审与 outside-voice）
- **THEN** 脚本 SHALL 非零退出并点名缺失 lens——metrics 启用时这两行为最小必有行；其余 per-lens（domain/adversarial/grounding）完整性 SHALL 属主 session 信任边界、脚本不强制（报告机读不出「本轮跑了哪些镜」）

#### Scenario: lens-metric 行内 layer 与 CLI --layer 不符被拦

- **WHEN** `anchor_lint --layer code-review` 运行，但某 fence 外 `sdflow:lens-metric` 锚的 `layer="spec-review"`（错层，如从另一 layer 报告误贴）
- **THEN** 脚本 SHALL 非零退出并点名错层锚——fence 外真 lens-metric 锚的 `layer` MUST 等于 CLI `--layer`，MUST NOT 仅因 `layer` 在枚举域内就放过错层锚

#### Scenario: 计数字段非非负整数被拦

- **WHEN** 某 `sdflow:lens-metric` 锚的 `findings`/`采纳`/`裁掉`/`defer`/`独立` 任一取负数 / 浮点串 / 空串 / 中文数字等非十进制非负整数值
- **THEN** 脚本 SHALL 非零退出并点名违规字段——五计数字段 MUST 校验为十进制非负整数，前置拦截坏值进聚合（不依赖下游 aggregator `_int` 兜底）

#### Scenario: fenced code block 内示范锚不被当真锚

- **WHEN** 报告在 ``` fence 内含 `sdflow:lens-metric v1` 等锚字面作语法示范，且 fence 外无对应真锚
- **THEN** 脚本 SHALL 判该 fence 内锚为示范（非真锚、不计入存在性、不参与枚举校验）——沿用 fence-aware 行级纪律，MUST NOT 因 fence 内示范锚假命中或假报枚举违规

#### Scenario: 脚本读不到报告或自身错误 fail-closed

- **WHEN** `--report` 指向的文件不存在 / 不可读，或 `lens-metric-contract.md` 无法定位、或找不到 `lens-metric-enums` 机读块、或块解析出空枚举
- **THEN** 脚本 SHALL 以非零退出码返回（fail-closed，判「无法确证干净」），MUST NOT 以退出码 0 假装自检通过、MUST NOT 回落脚本内硬编码枚举兜底（否则第二真相源复活）

#### Scenario: 枚举单一源一致性由测试守卫

- **WHEN** `lens_metric_aggregate.py` 硬编码的 `LAYER_ENUM`/`LENS_ENUM` 与契约 `lens-metric-enums` 机读块的 `layer`/`lens` 集不一致（有人改契约块未同步 aggregator，或反之）
- **THEN** 一致性测试 SHALL 失败——契约机读块为单一权威源，消费该枚举的脚本 MUST NOT 与之漂移；该测试 MUST NOT 跨 skill import（自带极简契约块解析），且 SHALL 对同一真实契约 fixture 交叉断言其 mini-parser 与 `anchor_lint` 解析路径输出相等（降低两独立解析器边界分歧造成的假绿）

#### Scenario: 机读契约与 tools 脚本同批部署防 pin 错配

- **WHEN** 本地 pin 消费仓（RULES_ROOT 落本地冻结规则集）经 `sdflow-init update` 刷新 `openspec/workflow/tools/`（含新版 `anchor_lint.py` 需读机读块）
- **THEN** 同一 update SHALL 一并刷新 sibling `lens-metric-contract.md`（含 `lens-metric-enums` 块）——契约为 `tools/anchor_lint.py` 运行时机读依赖，MUST NOT 只刷脚本不刷契约而致 pin 仓「新脚本 + 旧契约无块」永久 fail-closed；常态 tools-only 非 pin 消费仓 RULES_ROOT 落 canonical 全树、契约恒有块、不受此约束

#### Scenario: 数值一致性诚实声明为信任边界

- **WHEN** 某 `sdflow:lens-metric` 锚的 `findings=N` 与该镜合并池实收数不符
- **THEN** 脚本 SHALL NOT 声称能检出该不一致（`findings=N` vs 实收数属主 session 信任边界、非机械可验）；SKILL 自检步 SHALL 保留「数值一致性是主 session 职责、脚本不谎称机验」的诚实声明，MUST NOT 因接了脚本而删除该边界声明

### Requirement: roadmap 回填降摩擦助手（定位到 phase 机械、勾哪几行判断留人）

`sdflow-done` 收尾（hand-off 那步，即第二步）SHALL 在检测到 change 关联某 roadmap 时，读**步2 已实现的确定性盘面**（`verify=PASS` frontmatter / tasks 完成态 / change 名 / feat 分支）生成 roadmap **回填草稿**（该 phase 的候选复选框行集 + task-log 完成总结骨架含机械锚）写进 `hand-off.md`，并提示人异步确认回填。

回填是**记录维护且完成判定含判断**（现状实证：人对照 `### 验收标准` 判），切分线精确落在「有无确定性信号」上：

- 助手 MUST 只自动化**有确定性信号的机械动作**：① 从 change 名前缀 `implement-{roadmap}-pN` 解析 roadmap+phase（兜底 marker，见下一 Requirement）；② 定位该 **phase** 的候选复选框**行集**（借现状 `- [ ] {id}` 格式）；③ 读步2 已实现盘面事实。
- 助手 MUST 把**无机械判据的动作留人确认**：这个 change 勾该 phase 里**哪几行**（phase 跨多 change 时 change→行是判断）/ 算不算满足 `### 验收标准` / 完成总结价值叙述 / 阶段状态 / 里程碑 / deferred。
- 助手 MUST NOT 产 per-行「建议勾」（那是判断，会渗回机械侧撞 adr/0015 切分）——只产**阶段级候选行集**供人挑。
- 助手 MUST NOT 无人干预直接机械改 roadmap；MUST NOT scaffold 预建 roadmap 复选框 / 写 change 产物文件（避开 openspec「文件存在=done」短路，C1）；MUST NOT 从二值复选框机械聚合阶段状态 enum / 推 deferred（C2，判断留人写散文）。

**时序锚清单（P-1）**：草稿机械锚 MUST 只含步2 **已实现事实**（verify=PASS / tasks 完成态 / change 名 / 分支 / pytest 数[经 `--pytest-count` 显式传入则填、缺省 N/A（verify-report 无契约计数字段，不 scrape 散文避免第二真相源）]〔impl-review-fix FIX-4：订正与实现不符的旧措辞"有测试则从 verify-report 取"——脚本从未从 verify-report 抽取过 pytest 数，`--pytest-count` 是唯一 wiring〕）。archive 路径（第三步，含 `{date}`）与 merge（第五步）在草稿生成时**尚不存在**，MUST 留占位「待归档后由人补」，MUST NOT 当确定性盘面预填（防跨零点日期漂移 + merge opt-out 后记一次未发生的 merge）。

**阶段三无 AskUserQuestion**——草稿走 hand-off 异步确认，MUST NOT 弹窗、MUST NOT 阻塞归档/merge。

#### Scenario: 复选框式 roadmap 关联时生成回填草稿进 hand-off
- **WHEN** change 经名前缀/marker 解析出 roadmap+phase，且目标 roadmap 为复选框式（`- [ ] {id}`）
- **THEN** 助手定位该 phase 的候选复选框行集 + 读步2 已实现盘面生成 task-log 完成总结骨架（含 change/verify 结论/pytest 数机械锚、archive/merge 留占位）写进 hand-off，提示人过目后判断勾哪几行 + 补判断项

#### Scenario: 定位到 phase 机械、勾哪几行判断留人
- **WHEN** 生成回填草稿
- **THEN** 助手机械定位到 phase 级候选行集（前缀确定性信号），MUST NOT 代判「这个 change 勾哪几行 / 算不算满足验收标准 / 阶段状态 / deferred」——这些由人在确认环节判定

#### Scenario: 时序——archive/merge 留占位不预填
- **WHEN** 草稿在 hand-off（第二步）生成，archive（第三步）与 merge（第五步）尚未发生
- **THEN** 草稿机械锚只填步2 已实现事实（verify/tasks/change 名/分支/pytest 数）；archive 路径与 merge 状态留占位「待归档后由人补」，MUST NOT 预填预测值

#### Scenario: 非复选框格式 fail-loud 留人工（形态分治 P-3）
- **WHEN** 目标 roadmap 为表格/散文式（无 `- [ ]` 复选框，如 `| ✅` 概览表 + 状态散文）
- **THEN** 助手 MUST NOT 产复选框草稿，MUST fail-loud 在 hand-off 告知「roadmap {name} 为非复选框格式、复选框回填请人工」（反静默，非静默退现状）；task-log 完成总结骨架仍产

#### Scenario: 不碰 change 产物文件（避 C1）
- **WHEN** 助手运行
- **THEN** MUST NOT 写 change 的 tasks.md/proposal.md 等产物文件（避免第二 producer 触发 openspec「文件存在=done」短路 opsx:ff 产出链）；只读盘面 + 写 hand-off 草稿

#### Scenario: 阶段三无门、异步闭环可见（P-4）
- **WHEN** 回填草稿生成
- **THEN** 草稿进 hand-off 供人异步确认，done 流程继续（不弹窗、不阻塞归档/merge）；**且** done 第六步摘要抬一行「⚠ roadmap {name} 回填草稿待人确认（见 hand-off）」使其在 merge 时点可见（不只冻结进归档）；design 显式登记「产草稿即止、apply 由人异步、不保证」残差

### Requirement: roadmap 关联解析（change 名前缀为主、marker 兜底、fence-aware、漏则退现状）

change 与 roadmap 的关联 SHALL 优先由 **change 名前缀 `implement-{roadmap}-pN-*` 确定性解析**（命名约定已编码 roadmap+phase 双粒度，无需人手标记）；前缀不符命名约定时用兜底标记（`proposal.md`/`tasks.md` 中独占一行 `<!-- roadmap: {name}#{phase} -->`），或调用 done 时 `--roadmap {name}#{phase}` 覆写。优先级 SHALL 为 `--roadmap` > marker > 名前缀；多通道值不一致 MUST warn（反静默）。

marker 检测 MUST **fence-aware**（跳过 code fence/行内 code）+ **行锚定**（标记独占一行、非嵌散文/引用）+ **排除 change 自身讨论区**——防 change 产物字面含 marker 串致朴素子串检测假阳（`done-roadmap-writeback` 自身即 8 处含该串，MEMORY「gate 子串检测 dogfood 自指坑」同型）。

未声明关联且名前缀不符 MUST 退回现状（人全手工回填）、MUST NOT fail-closed 阻塞归档（回填助手是辅助、非正确性门）；对「未声明但疑似 roadmap 驱动」（如分支名/change 名近似 roadmap 目录名）**SHOULD** 在 hand-off 留一行提示，使「无草稿」与「助手判定无关联」可区分（反静默 C-12）。

#### Scenario: change 名前缀确定性解析（主通道）
- **WHEN** change 名匹配 `implement-{roadmap}-pN-*`
- **THEN** 助手确定性解析出 roadmap+phase 触发草稿生成，无需人手标记（消采纳 chicken-egg）

#### Scenario: marker 兜底 + fence-aware 防自指
- **WHEN** change 名不符前缀约定，但 `proposal.md`/`tasks.md` 有独占一行的 `<!-- roadmap: {name}#{phase} -->`（非 code fence/散文内）
- **THEN** 助手据此定位；若 marker 串仅出现在 code fence/行内 code/散文引用中（如本 change 讨论自身），fence-aware 检测 MUST 跳过、判无关联

#### Scenario: 双通道不一致 warn
- **WHEN** `--roadmap`、marker、名前缀解析出的 roadmap/phase 不一致
- **THEN** 按 `--roadmap` > marker > 名前缀取值并 warn（反静默，不静默取默认）

#### Scenario: 未声明退回现状不阻塞
- **WHEN** change 无关联声明且名前缀不符（普通 change 或漏标）
- **THEN** 回填草稿不生成、done 行为与现状零差异；MUST NOT fail-closed 阻塞；对疑似 roadmap 驱动 SHOULD 留一行提示

### Requirement: 阶段一讨论按雾量三段分流并约定 wayfinder→ff 衔接契约

阶段一入口 SHALL 按讨论雾量三分：问题清晰 → 直接 `opsx:ff`；单 session 可收敛的模糊 → `/opsx:explore`；**事中判定**超单 session（讨论已跨 session/跨天、或经历 /clear/压缩仍未收敛）→ 切换 wayfinder chart 铺图逐 ticket 决议〔spec-review-amendment F11：事前「预估轮数」不可观测，判据改事中触发〕。wayfinder 收敛后接 ff SHALL 遵守衔接契约三条：① ff 起手逐区读 map——Destination 喂 proposal 动机与 Success Metrics（D-5）、Decisions-so-far 逐 ticket zoom 到决议全文（MUST NOT 只读 map 摘要行，防 ff「prefer making reasonable decisions」对已决项重新决歪；zoom SHALL 设上界：≤8 张展开全文，超出按与本 change 相关性截断并在 proposal 注明〔F11〕）、Out-of-scope 喂 Non-Goals 可证伪假设（D-3）；② TG 判命中 SHALL 前置到 chart 阶段写入 map Notes；③ proposal SHALL 回链 map 供溯源，且 ff 写 design 决策段时源自已决 ticket 的 SHALL 内联回链该 ticket（机械可 grep 锚，同 R-ID 标注模式）〔F11〕。契约生效 SHALL 依赖双注入通道同步落地：`openspec/config.yaml` `rules:` 段规则文本 + workflow.md ff 调用行显式携带 map 路径——仅写入约束文件不构成注入（FF-0 先例）〔spec-review-amendment F2〕。

#### Scenario: 大雾讨论走 wayfinder 后 ff 不重决已决项

- **WHEN** 某议题经 wayfinder 多 ticket 决议收敛、随后触发 opsx:ff
- **THEN** ff 生成的 design 决策与 map Decisions-so-far 指向的决议全文一致；已决项不出现「合理重新决策」的偏移

#### Scenario: 清晰问题不强制前置讨论

- **WHEN** 需求边界与方案在触发时已清晰
- **THEN** 直接 opsx:ff，不强制 explore/wayfinder 仪式

### Requirement: grill 对上游已决分支瘦跑

grill（阶段一对抗压测步）SHALL 对上游 wayfinder 已决分支瘦跑：引用该 ticket resolution 快速核对（决议是否仍与代码 ground truth 一致）即过，MUST NOT 对已决内容重复全深度死磕；ff 新生成或未经上游决议的部分 SHALL 照常全深度死磕。瘦跑判定 SHALL 锚定 design 决策段的内联 ticket 回链（见衔接契约③）——无回链锚的分支 MUST 按全深度死磕，MUST NOT 以语义模糊匹配定「已决」〔spec-review-amendment F11〕。grill 对象是 ff 烘焙产物 vs 代码 ground truth，与 wayfinder grilling ticket（生成前决策拷问）非冗余，MUST NOT 因上游已跑 grilling 而整跳 grill。

#### Scenario: 已决分支快速核对

- **WHEN** grill 遇到 design.md 中某决策、其在 map 有对应 resolved ticket
- **THEN** 引 resolution 核对决议与代码事实仍一致后放行该分支，转入未决分支死磕

#### Scenario: 无上游决议时不瘦跑

- **WHEN** change 未经 wayfinder（直接 ff 或仅 explore）
- **THEN** grill 按既有全深度口径执行，无瘦跑路径

### Requirement: anchor_lint 机械化 hr-tg 锚一致性面治（M1/M2/M4/M-new，零妥协）〔grill 目标态导向〕

`anchor_lint` 校验 `sdflow:hr-tg` 锚时 SHALL 把可确定性校验的一致性一次机械化到位、全 fail-closed，MUST NOT 停留在字段在场检查、MUST NOT 留 WARN 降级/迁移旁路等妥协：

- **`--trigger-catalog` 必需**：校验 hr-tg 锚 SHALL 要求 `--trigger-catalog`，未传 → 非零退出（fail-closed），MUST NOT 降级为「仅字段在场 + WARN 放行」（WARN 放行 = fail-open，M2/M4/M-new 静默没跑而报告过关，架空本门）。
- **sentinel 约定〔spec-review F1〕**：`declared=` 是 TG CSV，空集用 **`declared=""`**（非 `"none"`，与现 emitter/测试 `test_hr_tg_none_with_declared_ok` 一致）；`none` 仅是 `hit=` 的空集哨兵。`declared="none"` 或 `hit=""` 属畸形 → 违规。
- **M-parse 整行严格解析〔spec-review F2〕**：校验器 SHALL 对 hr-tg 锚整行严格解析，**拒绝重复键**（同锚出现两个 `hit=`/`declared=`/`evidence=` → 违规）、未闭合注释、未消费残留——防「lint 用 dict 末值胜、`sdflow-retro._HRTG_RE` 取首个 `hit`」的跨消费者相反结论（`hit="none" hit="TG-04" …`）。
- **M1 declared= 硬必填**：每个 fence 外 hr-tg 锚 MUST 含 `declared=`，缺失 → 违规、非零退出。MUST NOT 内建任何常驻 grace 或 `--allow-legacy` 迁移旁路——归档旧报告不被任何流程重 lint（无需旁路）。
- **M2 hit⟺declared∩HR-TG 重算**：重算 `declared ∩ HR-TG 子集`（复用 `hr_tg_intersect` 成员解析 + 严格 tg-set 解析、单一源读成员，**同一 numeric 序**），要求锚 `hit=` 与之逐元素一致（`hit=none` ⟺ 空交集），不一致 / `declared` 畸形 / `hit` 畸形 → 违规。
- **M4 evidence= 在场性**：`hit≠none` 时 MUST 含 `evidence=` 且 **strip 后非空**（`evidence="   "` 纯空白 → 违规），缺/空 → 违规。
- **M-new TG 存在性 + catalog 内部一致**：`declared=`/`hit=` 的每个 TG MUST 存在于 trigger-catalog 定义的全 TG 集（同 `hr_tg_intersect` 出锚侧口径），不存在 → 违规；**且加载 catalog 时 SHALL 断言 `HR-TG 成员集 ⊆ 全 TG 集`〔spec-review F7〕**，成员行含全集外 TG（单一源内部损坏）→ 所有调用 fail-closed。
- **错误处理契约〔spec-review F9〕**：新增校验（M1–M4/M-parse/M-new）遇畸形字段 MUST **就地转 violation dict**（沿 `anchor_lint` collect-not-raise 约定，如 `check_lens_metric`），MUST NOT 照搬 `hr_tg_intersect` 的 `raise EmitError` 风格——否则 `main()` 无 try 包裹会让未捕获异常污染 stdout、破坏「双输出（human + JSON）」契约。

校验器 MUST NOT 校验 `declared` 本身是否为「真命中集」——「命中哪些 TG」无确定性信号（adr/0018），属语义残余（模型判定 + `evidence=` 人读 + git 审计）。M2 堵「手改单字段 `hit=none declared=TG-04` 内部矛盾」，**堵不住**「同改 hit+declared 一致但错」；实现与文档 MUST NOT 宣称使 hr-tg 锚 tamper-proof——此为完整机械化后剩下的合法机械/语义边界，非缺口、非妥协（S1 仍靠 evidence 人读 + git 审计兜底，非可放松环节）。

#### Scenario: 未传 trigger-catalog fail-closed（零妥协）
- **WHEN** 调用 `anchor_lint` 校验含 hr-tg 锚的报告但未传 `--trigger-catalog`
- **THEN** 非零退出 + stderr，MUST NOT 降级 WARN 放行

#### Scenario: 锚缺 declared 违规（M1，无 grace/旁路）
- **WHEN** fence 外 hr-tg 锚含 `hit=`/`evidence=` 但无 `declared=`
- **THEN** 判违规、非零退出（`missing-field`）；无 `--allow-legacy` 之类豁免

#### Scenario: declared 含不存在的 TG 违规（M-new）
- **WHEN** 锚 `declared="TG-99"`（shape 合法但 catalog 无定义）
- **THEN** 判违规（TG 未定义），非零退出

#### Scenario: hit 与 declared∩HR-TG 一致（M2）
- **WHEN** 锚 `hit="TG-04" declared="TG-04,TG-19"`，HR-TG 含 TG-04 不含 TG-19，`--trigger-catalog` 已传
- **THEN** 重算 `{TG-04}` 与 hit 一致，判通过

#### Scenario: 手改单字段内部不一致判违规（M2）
- **WHEN** 锚 `hit="none" declared="TG-04"`（TG-04∈HR-TG），`--trigger-catalog` 已传
- **THEN** 重算 `{TG-04}` ≠ `hit=none`，判违规（`hit-declared-mismatch`）

#### Scenario: 同改两字段一致但错——不宣称能挡（诚实边界）
- **WHEN** 锚 `hit="none" declared=""`，而真实命中含某 HR-TG 成员（declared 已被篡改为空）
- **THEN** 重算一致（空∩HR-TG=空），判通过——不校验 declared 正确性，此为已声明的语义残余边界；S1 仍靠 evidence 人读 + git 审计

#### Scenario: declared="none" 或 hit="" 畸形违规〔F1 sentinel〕
- **WHEN** 锚 `declared="none"`（应为 `""`）或 `hit=""`（应为 `none`）
- **THEN** 判违规——`none` 仅 hit 空集哨兵、`""` 仅 declared 空集

#### Scenario: 重复键违规〔F2 M-parse〕
- **WHEN** 锚 `hit="none" hit="TG-04" declared="TG-04" evidence="x"`（重复 `hit=`）
- **THEN** 判违规——拒重复键，防 lint（末值胜）与 retro（取首个）得相反结论

#### Scenario: catalog 内部损坏 fail-closed〔F7〕
- **WHEN** trigger-catalog 的 HR-TG `> 成员：` 行含全 TG 集（A–G 表）之外的 TG
- **THEN** 加载即所有调用 fail-closed（HR-TG ⊄ 全集 = 单一源内部损坏）

#### Scenario: hit≠none 缺/空白 evidence 判违规（M4）
- **WHEN** 锚 `hit="TG-04" declared="TG-04"` 但 `evidence=` 缺 / `""` / `"   "`（纯空白）
- **THEN** 判违规（`evidence-missing`，strip 后判空）

### Requirement: recorder frontmatter 索引与 legacy overlay dual-read

issues recorder（`buglist.py` / `todolist.py` / `issues.py`）SHALL 以 versioned `sdflow-issues` frontmatter namespace 作为新写机器索引的唯一真相源；索引 SHALL 保存 `module/summary/status/time/change/batch` 及 bug 专属 `priority` 或 todo 专属 `type`，并以 file-level `schema/pool/mode` 声明版本、池类型与 `canonical|overlay` 模式。frontmatter SHALL 使用文档化的 YAML-compatible 严格子集：`items` 下每个 canonical ID 对应一个单行 JSON object，使字符串中的 ASCII `|`、换行与 Unicode 由 JSON 无损转义；recorder MUST NOT 为这些索引字段继续写 Markdown 总览表 row，也 MUST NOT 因 `|`/换行拒绝合法值。

`[grill-amendment]` 所有索引 string SHALL 只含 Unicode scalar values，孤立 surrogate `U+D800..U+DFFF` 在任何写盘前按 ID+field 拒绝。renderer SHALL 使用 `ensure_ascii=False` 保留普通 Unicode，并把 U+0085/U+2028/U+2029 定向写成 JSON `\u0085`/`\u2028`/`\u2029`；CR/LF/tab/C0 由 stdlib JSON escaping。parser SHALL 拒绝 recorder 子树中的 raw NEL/LS/PS，接受其 escaped form 并还原原 code point。实现 MUST NOT 做 Unicode normalization，逐字段 round-trip SHALL 保持原 code points。

`[grill-amendment]` v1 renderer SHALL 产生唯一 canonical bytes：顶层键顺序 `schema,pool,mode,items`；item 按 `(ASCII prefix, decimal integer)` semantic key 排序；bug object 字段顺序 `module,summary,priority,status,time,change,batch`，todo 为 `module,summary,type,status,time,change,batch`，所有字段显式存在。`change/batch` 无值只允许 JSON `null`；writer SHALL 把输入 `""` 规范化为 null，reader SHALL 拒绝 frontmatter 中非 canonical 空字符串。`module/summary` SHALL 至少含一个非-whitespace scalar，但 MUST 保留原始前后空白/code points。空 map 只允许 `items: {}`，裸 `items:` 非法。reader MAY 接受 item 任意物理顺序，writer mutation SHALL 在自有 namespace 内 semantic-sort；render→render 必须 byte-identical。

`[grill-amendment]` 仅位于 byte 0 或紧随 UTF-8 BOM、且 opener/closer `---` 各自独占一行的 frontmatter block SHALL 是共享 envelope；正文中后续 `---` MUST NOT 被扫描或提升为 envelope。recorder SHALL 只拥有唯一的顶层 `sdflow-issues` 子树，内部键保持 `schema/pool/mode/items`，MUST NOT 展平为多个 `sdflow-issues-*` 顶层键，也 MUST NOT 接管共享 `sdflow` 父树或整个 envelope。reader SHALL 把 namespace 外内容视为其它 producer 所有的 opaque bytes；writer SHALL 以 byte-level splice 只插入/替换 recorder 子树，并逐字节保留其它顶层条目、注释、空行、顺序、标量样式、BOM、既有 EOL 及 frontmatter 外正文。重复 namespace、namespace 拼写/边界有歧义或窄 scanner 无法安全定位时 SHALL fail-closed，且原文件不得改变。

`[spec-review-amendment]` shared envelope v1 SHALL 只接受如下 lexical profile：每个顶层 entry 以 column 0 的无引号 ASCII key `[A-Za-z0-9][A-Za-z0-9_-]*:` 开始；同一物理行可带 value/comment，后续 value bytes 只能为空行、column-0 comment 或至少一个 ASCII space 缩进的 continuation，tab 禁止。column-0 空行/comment 是 producer-neutral separator，不属于 recorder span；recorder 自有子树内部则必须是无空行/comment 的 canonical form。entry span 在下一条合法 column-0 entry 或 closer 前结束。外部 entry 的 indented block/quoted scalar 与多行 flow value MAY 作为 opaque bytes 跳过；顶层 quoted/explicit/complex key、sequence、directive、`...`、未缩进 continuation、回到 column 0 的 flow continuation、tab或其它无法按该 profile 分段的构造 SHALL fail-closed。形似 quoted/explicit `sdflow-issues` 或 key/colon 变体 SHALL 作为 ownership ambiguity 拒绝，不得按 namespace absent 回退 legacy。

已有 envelope 的 recorder 子树 SHALL 沿用 opener 的 LF/CRLF；无 envelope 的 legacy 文件 SHALL 在 BOM 后或 byte 0 插入，并沿用正文首个 LF/CRLF，无 EOL 时使用 LF；新建 canonical 文件 SHALL 使用 UTF-8、无 BOM、LF。UTF-16 BOM、非法 UTF-8、lone CR、delimiter 缺失换行或无法安全判定 EOL SHALL fail-closed，MUST NOT 通过普通 text-mode round-trip 规范化整篇文件。

`[grill-amendment]` dated recorder 文件 SHALL 使用专用 bytes pipeline：一次 binary read 产生 raw bytes，document parser 从中返回 model、byte spans 与 EOL，namespace renderer 返回 bytes，最终由 `atomic_write_bytes` 同目录临时写 + mode bits 对齐 + `os.replace`。实现 MUST NOT 为保真先 text-read 再 binary reread，也 MUST NOT decode/encode namespace 外全文。完全生成的 INDEX/batches MAY 继续使用 text `atomic_write`。内容保真不承诺 inode、mtime、xattr 或 ACL 保留。

reader SHALL 只认文件起点成立的 frontmatter block：`sdflow-issues` namespace 缺失时读 legacy Markdown 表；namespace 存在时 MUST 严格校验 schema、pool、mode、缩进、重复键、ID、字段集合/类型与枚举。namespace 在场但任一校验失败 SHALL fail-closed 非零退出并点名文件/reason，MUST NOT 回退 legacy 表。`[grill-amendment]` mode 必须与 recorder legacy 状态总览区域互证：canonical 要求区域计数=0，overlay 要求=1；namespace 缺失的 legacy 也要求=1。区域缺失/重复或 mode mismatch 是 fatal，不得自动修 mode/删表/隐藏 items。验证通过后 `mode=canonical` SHALL 只以 frontmatter items 为索引；`mode=overlay` SHALL 按 semantic ID 合并同文件 legacy rows 与 frontmatter items，同 semantic ID 时 frontmatter 是唯一当前值，legacy row 仅作不可写 snapshot。`[spec-review-amendment]` relation validation SHALL 按 effective owner 分区：frontmatter-owned ID 只过 strict schema/canonical marker 规则，不进入 legacy 表↔块/status 检查；未 promotion legacy ID 继续旧规则；marker ownership 冲突、marker-only legacy、同 semantic key 多个 frontmatter key及跨文件/跨 pool 重复均 fatal。overlay 区域内 row arity 问题仍走既有 problems 分层。跨文件/跨 pool 重复 ID仍为错误。

新格式 prose 块 SHALL 只承载人读详情与 append-only 变更历史，MUST NOT 再复制 `status/batch` 等可变机器状态。历史表与历史属性表 MUST NOT 被任何新 writer 修改；对 legacy item 的 mutation SHALL 把完整当前索引提升进同文件 overlay，再更新 overlay。`[grill-amendment]` canonical/overlay 新 block SHALL 由独占行 `<!-- sdflow-issue-block:start id={canonical-id} -->` / `<!-- sdflow-issue-block:end id={canonical-id} -->` 成对定界；marker 必须同 ID、不可嵌套、每 ID 至多一块。新格式 reader MUST 只按 marker 定位 block，MUST NOT 回退 heading/`---` heuristic；后者只服务 legacy block。精确 marker 独占行是保留语法，renderer SHALL HTML-escape 用户 prose 中的同形行，其它 heading/separator/fence SHALL 作为普通 prose。`[spec-review-amendment]` promotion 在任何写盘前 SHALL 扫描待包裹 legacy block；内部已有任一精确 marker grammar 独占行时必须 fail-closed 并报告 block/line，MUST NOT 原样保留后再包外围 marker而制造嵌套/错配盘面。

`[spec-review-amendment]` producer `scan --json` 与 `issues.py` consumer 的 envelope 是稳定 fail-closed contract：bug 输出必须有 list `bugs` + list `problems`，todo 必须有 list `items` + list `problems`；item 必须包含对应 pool 全部 index fields 以及 string `id/file`，字段类型/枚举与本 schema 一致。坏 JSON、缺键、错误类型或缺 `file` SHALL non-zero，且既有 INDEX/batches 不变；consumer MUST NOT 以缺键默认 `[]`。

`[spec-review-amendment]` 本 change 新增的 fatal diagnostics SHALL 统一写 stderr，保持 JSON stdout 无污染，并采用可断言三段式 `ERROR: <problem>; cause: <cause>; fix: <action>`；涉及文件/ID/field/lock/rename stage 时必须带对应定位，fix 必须给可复制的重试/恢复动作。该文本格式不新增 machine error-code/diagnostic JSON API。

block heading SHALL 保持 `## {canonical-id}: {display-title}`，但不参与 identity；显式 `title` 必须通过拒绝 CR/LF/NUL 的窄 line-safety，缺省 display title 则由 `summary` 连续空白折叠成一个 ASCII space 后确定性派生。完整 summary SHALL 逐物理行加 `> ` 前缀作为新建 block 的 blockquote 人读投影，MUST NOT 从 prose 反解析成机器状态；promotion 包裹既有 block 时 MUST NOT 为补投影而改写其内部。bug 新 item SHALL 建 marker block；todo 轻量 item MAY 无 block，首次追加历史时 SHALL 建 marker-framed minimal block。写入其它 Markdown 单行结构位的 source/project/history note 仍 MUST 经窄 line-safety 校验或等价安全渲染；`batches.md` 的 batch key slug 契约（拒空白、首尾空白、`|`、换行、` — `）保持不变。

#### Scenario: 新 canonical 文件无损写入特殊字符
- **WHEN** 在不存在的目标 dated 文件中新增 item，且 `module` 或 `summary` 含 ASCII `|`、换行与 Unicode
- **THEN** recorder 创建 `mode=canonical` 的 v1 frontmatter，将 item 仅写入 `items`，随后 `scan --json` 逐字段返回原值；`[grill-amendment]` 若该 pool/payload 建立 prose block，则 heading 使用单行 display title、完整 summary 以逐行 blockquote 展示；todo 轻量项无 block 仍合法；文件中 MUST NOT 出现该 item 的 Markdown 总览表 row，也 MUST NOT 触发旧 table-cell reject

#### Scenario: YAML line-break code point 定向转义 `[grill-amendment]`
- **WHEN** 任一索引 string 含 U+0085、U+2028 或 U+2029
- **THEN** frontmatter item 物理上仍为单行，对应 code point 以 `\u0085`/`\u2028`/`\u2029` 出现；scan JSON 还原原字符且不做 normalization

#### Scenario: raw line separator 与孤立 surrogate fail-closed `[grill-amendment]`
- **WHEN** recorder 子树含 raw NEL/LS/PS，或 add/overlay promotion 的任一 string 经 JSON escape 输入后包含孤立 surrogate
- **THEN** parse/render 在业务写盘前非零失败，stderr 含文件或 ID+field+code point；MUST NOT 等到 UTF-8 encode 才抛无定位异常

#### Scenario: item permutation 收敛为唯一 bytes `[grill-amendment]`
- **WHEN** 两个语义相同 model 以不同插入顺序包含 `A10/A2/B1`，或 reader 读到手工乱序 namespace 后执行合法 mutation
- **THEN** renderer 都按 `A2,A10,B1` 输出相同 bytes，object 字段按 pool 固定顺序；第二次 render 不再产生 diff

#### Scenario: optional null 与 empty map canonical form `[grill-amendment]`
- **WHEN** writer 输入 change/batch 空串或 model items 为空
- **THEN** 输出分别为 JSON `null` 与 `items: {}`；reader 遇到 frontmatter `change:""`、`batch:""` 或裸 `items:` 时 fail-closed 并点名字段

#### Scenario: required prose index string 不是空白壳 `[grill-amendment]`
- **WHEN** module 或 summary 只含 spaces/tabs/newlines，但类型仍为 string
- **THEN** writer/reader 以 required-nonblank 错误拒绝；若至少有一个非-whitespace scalar，则保留原始前后空白且 round-trip 不 trim

#### Scenario: 多行 summary 不能注入 prose block `[grill-amendment]`
- **WHEN** 未提供显式 `title`，且 summary 含换行、空白序列、`## B999: fake`、`---` 与 `|`
- **THEN** heading 中只出现空白折叠后的单行 display title；完整 summary 的每个物理行都带 blockquote 前缀，新格式 block parser 只认成对 marker 并仍只发现真实 item ID，`scan --json` 返回原始 summary

#### Scenario: 显式 title 仍受单行结构约束 `[grill-amendment]`
- **WHEN** payload 显式提供含 CR、LF 或 NUL 的 `title`
- **THEN** add 在任何文件创建或写入前非零拒绝；合法单行 title 可含 `|`，且只作为 display title、不进入 frontmatter 机器索引

#### Scenario: 向 legacy dated 文件新增 item
- **WHEN** 当前日/月 dated 文件只有 legacy Markdown 表，升级后的 recorder 新增一个 item
- **THEN** recorder 在同文件首部建立 `mode=overlay` 并把新 item 写入 frontmatter，同时追加其 prose 块；原表逐字节不变且无该新 item 行，dual-read 返回 legacy rows 与新 item 的并集

#### Scenario: legacy item mutation 提升为 overlay
- **WHEN** `set-status`、`triage` 或 `batch rename` 更新一个只存在于 legacy 表的未终态 item
- **THEN** writer 从 legacy row 构造完整 v1 item 写入同文件 overlay；`[grill-amendment]` 唯一可判的既有 block 只在外围插入同 ID marker，内部 bytes、legacy row 与属性表保持原样，再施加更新并把状态历史追加到 end marker 前；reader 对同 ID 只返回 overlay 当前值

#### Scenario: legacy block 预存 marker 时 promotion 拒绝 `[spec-review-amendment]`
- **WHEN** 唯一可判的 legacy block 内已含任一精确 `sdflow-issue-block:start/end` 独占行
- **THEN** promotion 在 frontmatter/外围 marker/历史任一写盘前 fail-closed，stderr 点名 file/legacy ID/line 与 marker collision；原文件逐字节不变，MUST NOT 通过再包一层制造嵌套或错配 marker

#### Scenario: promotion 后不再依赖 legacy block heuristic `[grill-amendment]`
- **WHEN** 某 legacy item 已成功 promotion 并原位套 marker，随后再次执行 status/triage mutation
- **THEN** writer 只用成对 marker 定位和追加，不再按 heading/`---` 搜索该 item；marker 内原 legacy prose 可自由含这些文本

#### Scenario: legacy block 无法安全包裹 `[grill-amendment]`
- **WHEN** 待 promotion 的 bug 缺 prose block、同 ID 有多个候选块或 legacy heuristic 无法唯一确定边界
- **THEN** mutation 在 frontmatter/marker/历史任一写盘前 fail-closed 并列出 evidence；MUST NOT 猜边界或另建同 ID continuation block

#### Scenario: 无 block legacy todo promotion `[grill-amendment]`
- **WHEN** 待 promotion 的 legacy todo 合法地没有详情块，且 mutation 需要追加历史
- **THEN** writer 写入 overlay item 并创建唯一 marker-framed minimal block；不得制造第二个无 marker 同 ID block

#### Scenario: namespace 在场但损坏不回退
- **WHEN** 文件首块含 `sdflow-issues`，但出现未知 schema、pool/path 不符、非法 mode、tab/缩进错误、重复 ID/JSON key、缺字段、类型或枚举越域任一情况
- **THEN** `scan` 与依赖它的 reindex/mutation MUST 非零失败并在 stderr 点名文件与 reason，MUST NOT 回退表格或挑最后一个重复值继续

#### Scenario: canonical 声明不能隐藏 legacy 表 `[grill-amendment]`
- **WHEN** namespace 声明 `mode=canonical`，但文档仍能定位 recorder legacy 状态总览区域
- **THEN** scan/mutation 以 mode-structure mismatch fatal，报告声明 mode 与区域计数；MUST NOT 忽略旧表后返回较少 items

#### Scenario: overlay 必须有唯一 legacy 总览区域 `[grill-amendment]`
- **WHEN** namespace 声明 `mode=overlay`，但 legacy 状态总览区域缺失或重复
- **THEN** scan/mutation fatal 且不自动改成 canonical或挑一个区域；若区域唯一但内部有坏 row，坏 row 仍按 legacy arity problem 处理

#### Scenario: 无 recorder namespace 的历史文件继续可读
- **WHEN** dated 文件无 frontmatter，或首块只有与 recorder 无关的其它 namespace，且含合法 legacy 总览表
- **THEN** reader 按 legacy parser 返回与升级前相同的 item 字段；不得把无关 frontmatter 当损坏的 recorder namespace

#### Scenario: 向共享 envelope 注入 recorder namespace `[grill-amendment]`
- **WHEN** legacy dated 文件的首个 frontmatter 已含其它工具的键、注释、空行或 block scalar，但不含 `sdflow-issues`
- **THEN** writer 在同一 envelope 插入唯一顶层 `sdflow-issues` overlay；namespace 外 frontmatter 与 Markdown 正文逐字节不变，随后 reader 合并 overlay 与 legacy rows

#### Scenario: shared envelope lexical profile 接受与拒绝 `[spec-review-amendment]`
- **WHEN** 外部 namespace 使用合法 column-0 ASCII key，value 由 same-line bytes 或 space-indented block/quoted/flow continuation 组成
- **THEN** scanner 以 byte span 跳过并原样保留；若改为 quoted/explicit/complex top-level key、top-level sequence/directive、tab、未缩进 continuation或 column-0 multiline flow continuation，则 scan/mutation fail-closed 并点名 lexical category，原 bytes 不变

#### Scenario: BOM 与 CRLF 在 namespace splice 外保真 `[grill-amendment]`
- **WHEN** dated 文件以 UTF-8 BOM + CRLF frontmatter 开头，外部 namespace、正文及末尾换行含可识别的 byte fixture
- **THEN** recorder mutation 只改变 `sdflow-issues` byte range，新子树使用 CRLF；BOM 与所有 range 外 bytes 完全相同

#### Scenario: dated 文件单次 binary I/O `[grill-amendment]`
- **WHEN** scan 或 mutation 处理一个含共享 envelope 的 dated 文件
- **THEN** instrumentation 显示该文件只被 binary read 一次，parser/renderer 以 byte spans 复用该 buffer；不存在 text-mode read、二次保真 reread或 namespace 外全文 re-encode

#### Scenario: bytes atomic replace 保留 mode bits `[grill-amendment]`
- **WHEN** `atomic_write_bytes` 更新一个既有 0640 dated 文件，或首次创建新文件
- **THEN** replace 后既有文件仍为 0640、新文件为 0644；注入 write/chmod/replace 异常时旧 bytes/mode 不变且临时文件按既有清理契约处理

#### Scenario: 正文分隔线不是 frontmatter `[grill-amendment]`
- **WHEN** 文件 byte 0 不是 `---`，但正文稍后出现独占行 `---` 及形似 `sdflow-issues:` 的 prose
- **THEN** reader 不把该段识别为 envelope；若文件有合法 legacy table 则按 legacy 读取，writer 需要 overlay 时只在 byte 0 或 BOM 后新增真正 envelope

#### Scenario: 不支持的编码或 EOL fail-closed `[grill-amendment]`
- **WHEN** 文件含 UTF-16 BOM、非法 UTF-8、lone CR、frontmatter delimiter 无行终止或无法安全判定 EOL
- **THEN** scan/mutation 非零并报告 encoding/EOL reason；mutation 前后原始 bytes 完全一致

#### Scenario: 更新 recorder 子树不改写相邻 namespace `[grill-amendment]`
- **WHEN** canonical/overlay 文件的共享 envelope 同时含 `sdflow-issues` 与其它顶层 namespace，且 recorder mutation 成功
- **THEN** writer 只替换 `sdflow-issues` 子树；比较写前写后时，子树外 byte ranges 完全相同

#### Scenario: namespace 所有权或 splice 边界有歧义 `[grill-amendment]`
- **WHEN** 首个 envelope 含重复 `sdflow-issues`、非标准拼写造成同名歧义，或使用窄 scanner 无法无歧义界定的结构
- **THEN** reader/mutation 非零失败并报告文件与 reason；mutation MUST NOT 重写、规范化或截断该文件

#### Scenario: overlay shadow 不算重复 ID
- **WHEN** `mode=overlay` 文件的 frontmatter 与同文件 legacy 表都有 ID `T85`
- **THEN** reader 以 frontmatter `T85` 为当前值且不报告重复；若另一个 dated 文件也出现语义相同 ID，则仍 MUST 报跨文件重复

#### Scenario: overlay relation validation 按 owner 分区 `[spec-review-amendment]`
- **WHEN** overlay 含 frontmatter-only bug + canonical marker block，另有未 promotion legacy item + legacy block
- **THEN** 前者只做 frontmatter/marker relation，MUST NOT 因 legacy table 无该 literal ID 误报“块有 ID 但表无行”；后者继续 legacy 表↔块/status 检查；同一 marker 被两个 semantic owner 认领则 fatal

#### Scenario: 新 prose 不再复制可变状态
- **WHEN** 新格式 item 经 `set-status` 或 `triage` 更新
- **THEN** writer 只更新 frontmatter 索引并按需追加人读历史，不搜索/改写 prose 中的状态或批次副本；scan 的当前状态只来自索引

#### Scenario: 自由 prose 不制造新格式 block boundary `[grill-amendment]`
- **WHEN** phenomenon/rootcause/fix/impact/motivation/approach/note/optional 或人工 prose 含独占行 `---`、`## B12: fake` 与 fenced code
- **THEN** 新格式 parser 只按外围成对 marker 确定原 block，以上内容不截断或新增 block；若用户内容含精确 marker grammar 的独占行，renderer 将其 HTML-escape

#### Scenario: marker 损坏可观察且不回退 `[grill-amendment]`
- **WHEN** canonical/overlay prose 出现 marker 缺对、start/end ID 不同、嵌套或同 ID 重复 block
- **THEN** scan 产生带文件/ID/reason 的 problem，`reindex --strict` 非零；reader MUST NOT 用 heading heuristic 猜测修复边界

#### Scenario: todo 轻量项首次创建历史 block `[grill-amendment]`
- **WHEN** canonical todo item 起初没有 prose block，随后 `set-status` 需要追加历史
- **THEN** writer 创建成对 marker 的 minimal block 后追加历史；缺块在此前不算 problem，bug 新 item 缺 marker block 仍算 problem

#### Scenario: scan JSON consumer protocol 损坏 fail-closed `[spec-review-amendment]`
- **WHEN** recorder 子进程返回坏 JSON、缺 `bugs|items`/`problems`、任一键非 list，或 item 缺 `id/file`/pool 必需字段
- **THEN** `issues.py` 在生成/覆盖 INDEX/batches 前非零失败，stderr 点名 producer + key/type；MUST NOT 将缺键解释为空池或产生数据视图丢失

<!-- REQ: SW-RI-2 -->

### Requirement: recorder ID 语义唯一与仓级并发写安全

`[grill-amendment]` `[spec-review-amendment]` bug/todo 新写 ID SHALL 统一符合 ASCII `[A-Z][1-9][0-9]*`，默认 prefix 分别为 `B`/`T`，公开的自定义 `--prefix` 保持兼容且只接受一个 ASCII 大写字母。matcher MUST 使用 ASCII 字符类/`re.ASCII`，不得让 `\d` 接受 Arabic-Indic、fullwidth 或其它 Unicode decimal digit。ID 的语义身份由 ASCII 大写 prefix + 十进制数字值决定，不包含 pool；reader MUST 把 `A007`/`A7` 等同号异形视作冲突并 fail-closed，writer MUST 只接受 canonical spelling。ID SHALL 在 bug+todo 两池仓级全局唯一；显式 ID 查重、自动 max+1 分配与 `next-id --prefix X` 的计算 MUST 在同一个 snapshot lock 内读取两池全集，MUST NOT 只扫当前 pool。`next-id` 命令只提供 advisory 值，不构成 reservation。

`[spec-review-amendment]` legacy reader MAY 保留孤立 ASCII raw spelling `A007` 作为定位 alias；mutation 仅在同文件确有该 raw legacy row 且 semantic key 唯一时接受该 alias。promotion SHALL 写 canonical frontmatter key/marker `A7`，overlay shadow 按 semantic key，成功 mutation 与后续 scan 返回 canonical ID；未触碰 pure-legacy scan 仍返回 raw ID。无 raw legacy alias 的非 canonical 用户输入必须拒绝。

所有会形成权威仓级 snapshot 或修改 dated 文件、`issues/INDEX.md`、`issues/batches.md` 的 recorder 命令 MUST 以 `O_CREAT|O_EXCL` 获取仓级 exclusive snapshot lock `openspec/issues/.recorder.lock`。`[spec-review-amendment]` 除 pure argument validation 与 `repo_root` 解析外，owner 必须在任何影响结果的 discovery/glob/list/exists/stat/open 前 acquire，participant 必须先校验 token；只读命令 SHALL 持有到全部输入已发现、读取、解析、校验并固化成不再访问文件的内存 snapshot，随后先释放再格式化/输出；mutation SHALL 持有到最后一次原子替换完成。两类命令均在正常/异常退出的 `finally` 路径释放。至少包含 bug/todo `scan`、`next-id`、add/set-status/triage，以及 issues reindex/sweep、`batch lint/add/set-status/rename`。锁内容 SHALL 记录 repo、PID、命令、开始时间与高熵 capability token。锁冲突 MUST 在任何业务 snapshot/写盘前立即非零失败并显示 owner，但 MUST NOT 显示 token；实现 MUST NOT 等待、自动按 TTL 偷锁或忽略冲突。目标文件落盘 MUST 继续使用同目录唯一临时文件 + `os.replace`，写前异常不得改变旧文件。

`[grill-amendment]` lock 只提供 cooperative isolation，MUST NOT 声称可阻止不遵守协议的编辑器/脚本/Git 修改。`sdflow-init` SHALL 以 `sdflow-init/assets/snippets/runtime-gitignore.txt` 为 canonical source，并由 `init.py::run()` 的 init/update 两路调用 planned `merge_runtime_gitignore()`，向消费仓根 `.gitignore` 幂等合并 `/openspec/issues/.recorder.lock`；已有一条时 byte-noop，缺项时仅追加完整行，重复条目时 fail-closed 不擅删用户内容，其它 ignore bytes 必须保留。本仓 `.gitignore` SHALL 同步 dogfood。当前不存在的 canonical ignore 资产与 merge path 必须由本 change 新增。

`[spec-review-amendment]` guarantee matrix SHALL 明示：macOS/Linux 本地 filesystem 是自动 release gate，mode bits 只在 POSIX 保证；Windows 本地 filesystem 是必须执行 smoke 的兼容目标，sharing violation 等失败须 non-zero 且旧文件不变；NFS/SMB/FUSE 等 network/userspace filesystem unsupported。`os.replace` 只承诺本地文件系统上的 process exception/crash 边界；未执行完整 file+directory fsync protocol，power-loss durability 非本 change 承诺。

`[grill-amendment]` 顶层 snapshot/mutating CLI SHALL 是唯一 lock owner；它启动的 recorder 子进程 SHALL 通过专用环境变量接收 token，只有在 token 与当前锁文件匹配时才作为 participant 进入同一锁域。participant MUST NOT 再次 acquire 或 release；`[spec-review-amendment]` 已验证 participant 仅可向 allowlist 内、同 repo、当前复合调用图需要的 recorder 子进程原样转发该 token，其它 subprocess env 必须剥离 token；缺失/不匹配、跨 repo、非 allowlist 或越级委派均不得进入 participant core。非 owner 直接调用仍须正常竞争锁或 fail-closed，MUST NOT 绕过互斥。owner 释放前 MUST 对当前路径 identity 与 token 作 best-effort 终检，只能删除仍观察为自己的锁；普通 path API 无 compare-and-unlink，终检后的外部替换 race 明确不在 cooperative 保证内。`O_EXCL` 创建成功后即视为 occupied；竞争者读到空白/部分 metadata 时仍须失败，不得据此偷锁。独立 reader MUST 真正 acquire；仅在读取前后检查 lock 是否存在不满足 snapshot 隔离。

`[spec-review-amendment]` 共享 envelope 的所有**合规** producer 若会 mutation 同一 dated document，MUST 加入同一 `.recorder.lock` document lock protocol，即使它不拥有 `sdflow-issues`；所有权按 namespace 分离，mutation 协调按整文件 replace 共享。非合规外部 writer 绕锁后，recorder 不承诺以额外 reread/CAS 检出其变化；这种 lost-update race 明确属于 cooperative residual boundary，MUST NOT 用“byte splice”夸大为跨任意 producer 安全。

#### Scenario: 显式前导零 ID 被拒
- **WHEN** `add` 收到显式 `A007`，无论池中是否已存在 `A7`
- **THEN** writer 在写盘前以 canonical ID 错误拒绝；若 legacy corpus 已同时存在两种 spelling，scan MUST 报语义重复并拒绝 reindex

#### Scenario: Unicode decimal digit 不是 canonical ID `[spec-review-amendment]`
- **WHEN** reader/writer/marker 遇到 Arabic-Indic、fullwidth 或与 ASCII 混合的数字 spelling，例如 `A1٢`、`A1２`
- **THEN** 在 semantic key/int conversion 前以 non-ASCII-ID 错误拒绝，不 normalization、不与 `A12` 静默归并

#### Scenario: 孤立 legacy 前导零 ID promotion `[spec-review-amendment]`
- **WHEN** pure-legacy 文件仅有 raw `A007` 且仓内无 semantic `A7` 冲突，调用 `set-status A007`
- **THEN** raw row/旧 block bytes 保留，overlay key 与 marker 写 `A7`，成功 JSON 及后续 scan 返回 `A7`；同文件 shadow 以 semantic key 合并且不产生两个 item

#### Scenario: 自定义 prefix 保持兼容 `[grill-amendment]`
- **WHEN** bug 或 todo 调用 `next-id/add --prefix A`，且仓级两池不存在对应冲突
- **THEN** writer 分配 canonical `A<n>`，CLI/JSON shape 与默认 B/T 相同；小写、多字母或空 prefix 在业务读取/写盘前非零拒绝

#### Scenario: 自定义 ID 跨 pool 冲突 `[grill-amendment]`
- **WHEN** bug 池已存在语义 ID `A7`，todo add 尝试显式 `A7`、自动 `--prefix A` 或 legacy 中出现 `A007`
- **THEN** 显式/legacy 路径 fail-closed 并列出两池位置；自动分配在锁内跳过该 semantic key 选择下一可用 canonical ID，MUST NOT 因 pool 不同放行重复

#### Scenario: 并发 add 不产生重复或丢写
- **WHEN** 20 个进程并发向同一仓库 recorder 执行自动 ID 的 `add`
- **THEN** 同一时刻至多一个 writer 持锁；成功写入的 ID 全部唯一，冲突进程均显式非零且可重试，最终文件无 lost update、半写或重复 ID

#### Scenario: 锁冲突在读改写前失败
- **WHEN** `.recorder.lock` 已由另一写命令持有
- **THEN** 当前 mutation 在读取可变 snapshot/分配 ID/创建文件之前失败，stderr 含 lock path 与 owner PID/command/time，任何目标文件逐字节不变

#### Scenario: sweep 子进程加入父命令锁域 `[grill-amendment]`
- **WHEN** `issues.py sweep` 已持有 owner lock，并依次启动 bug/todo triage、batch add 与 reindex 子进程
- **THEN** 每个 mutating 子进程校验继承 token 后以 participant 身份执行，不发生嵌套抢锁；从 sweep 首次 scan 到最终 reindex 之间，任何外部 writer 均 fail-fast

#### Scenario: participant 受控嵌套委派 `[spec-review-amendment]`
- **WHEN** `sweep → issues reindex → bug/todo scan` 形成两层 recorder subprocess，或 participant 启动非 allowlist 外部命令
- **THEN** 内层 allowlist scan 原样校验同一 token 后加入且不自锁；外部命令环境无 token；跨 repo/伪造/越级委派在业务读取前失败

#### Scenario: 伪造或过期 participant token 被拒 `[grill-amendment]`
- **WHEN** 子进程收到缺失、过期或与当前 lock file 不一致的 participant token
- **THEN** 子进程 MUST NOT 进入锁内 mutation core；它按顶层调用正常 acquire，若锁已存在则在业务读写前失败

#### Scenario: owner 不误删替代锁 `[grill-amendment]`
- **WHEN** owner 持锁期间 lock file 被人工删除，且另一 writer 随后建立了不同 token 的新锁
- **THEN** 若替换在 release identity/token 终检前可观察，旧 owner保留新锁并显式报告 ownership lost；诊断同时声明终检与 unlink 之间的非 cooperative 替换不具备原子 compare-and-unlink 保证

#### Scenario: 竞争者撞上 metadata 初始化窗口 `[grill-amendment]`
- **WHEN** owner 已通过 `O_EXCL` 创建 lock file，但 metadata 尚为空或只写入一部分时另一 writer 竞争
- **THEN** 竞争者仍立即非零失败，可报告 metadata unavailable/initializing；MUST NOT 删除、覆盖或绕过该锁

#### Scenario: 写入异常保持旧文件
- **WHEN** render、临时文件写入或 `os.replace` 前注入异常
- **THEN** 命令非零退出，原目标文件逐字节不变，正常异常路径清理临时文件并释放本进程持有的 lock

#### Scenario: crash stale lock fail-loud
- **WHEN** writer 被不可捕获终止而遗留 `.recorder.lock`
- **THEN** 后续权威读写 MUST fail-loud，按 `ERROR: problem; cause; fix` 显示 repo/path/PID/command/start/metadata state 与可复制恢复步骤；MUST NOT 自动删除可能仍属活进程的 lock

#### Scenario: metadata 前 crash 的 break-glass `[spec-review-amendment]`
- **WHEN** owner 在 `O_EXCL` 成功后、完整 metadata 写入前 crash，留下空白或部分 lock
- **THEN** 后续命令保守拒绝并明确无法核验单一 owner；fix 要求先停止该 repo 全部 recorder owner/participants、再删除精确 lock path并重跑，MUST NOT 只凭空 metadata 猜 stale

#### Scenario: next-id 不承诺预留
- **WHEN** 调用者先执行 `next-id`，随后另一进程抢先成功 add 同一建议号码
- **THEN** `next-id` 的计算 snapshot 在持锁期间一致，但释放即失效；前一调用者的后续 add 在新锁内查重时重新自动分配或对显式冲突非零失败，MUST NOT 覆盖既有 item

#### Scenario: 独立 scan 不读取跨文件写中间态 `[grill-amendment]`
- **WHEN** batch rename owner 已改写部分 dated files 但尚未完成 registry/reindex，此时另一个独立 `scan --json` 启动
- **THEN** scan 在读取任一业务文件前因 snapshot lock 冲突非零失败；MUST NOT 返回一半 old、一半 new 的成功 JSON

#### Scenario: reader 先持锁时 writer 不穿越 `[grill-amendment]`
- **WHEN** 独立 scan 已 acquire snapshot lock 并正在读取多文件，另一 writer 启动
- **THEN** writer 在任何业务读取/写盘前 fail-fast；scan 返回的成功 snapshot 对应无 writer 穿越的锁内时点

#### Scenario: 慢输出不延长只读锁 `[grill-amendment]`
- **WHEN** scan 已完成全部读取/解析/校验并固化内存 snapshot，但 stdout consumer 阻塞其 JSON 格式化或写出
- **THEN** scan 在输出前已 token-safe release；另一命令可 acquire，且 scan 最终输出仍只来自已固化 snapshot、不再访问业务文件

#### Scenario: runtime lock ignore 幂等注入 `[grill-amendment]`
- **WHEN** `sdflow-init` 对缺少、已有或已含 recorder lock 条目的消费仓 `.gitignore` 连续执行 init/update
- **THEN** `/openspec/issues/.recorder.lock` 恰好存在一次，其它用户规则逐字节保留；持锁期间 `git status --short` 不显示该 runtime lock

#### Scenario: 平台与 durability 边界可验证 `[spec-review-amendment]`
- **WHEN** 在 POSIX local FS 跑全套、Windows local FS 跑 acquire/conflict/replace/cleanup smoke，或用户查阅 network FS/power-loss 支持说明
- **THEN** POSIX mode/atomic tests 与 Windows smoke 通过；Windows sharing failure 保留旧文件；文档明确 network FS unsupported、power-loss durability 未承诺，MUST NOT 用“跨平台原子”笼统覆盖这些层级

#### Scenario: cooperative lock 不夸大保证 `[grill-amendment]`
- **WHEN** 外部编辑器或未采用 recorder lock 的脚本在 owner 持锁时直接改写 issue 文件
- **THEN** recorder 不承诺拦截该写入；文档/诊断明确保证仅覆盖遵守协议的 CLI，并在后续 parse/validation 尽可能 fail-loud

#### Scenario: 两个 namespace producer 不互相覆盖 `[spec-review-amendment]`
- **WHEN** recorder 与另一个合规 producer 并发更新同一 dated document 的不同顶层 namespace
- **THEN** 二者竞争同一 document lock，至多一个先写、后者 acquire 后从最新 bytes 读取并保留前者更新；测试与文档同时声明绕锁 producer 的并发 replace 不在保证内

<!-- REQ: SW-RI-3 -->

### Requirement: recorder 单次解析与 batch rename snapshot 复用

`scan` SHALL 对每个 dated 文件至多执行一次文件读取与一次 document parse，并从同一 parse result 完成 frontmatter/legacy merge、ID/字段校验、block relation 与 JSON 输出；MUST NOT 为 arity、重复 ID、rows、blocks 分别重复切分同一文件。`[spec-review-amendment]` `issues.py batch rename` SHALL 由自包含 `read_rename_snapshot()` 直接对两池每个 dated 文件执行一次 binary read/parse，snapshot 携带 raw bytes/spans/model/effective items/problems；MUST NOT 先经 `scan --json` 读取后再为 retag 二次打开同一文件。retag SHALL 更新内存 model并以原 raw buffer splice，再把 updated items 传给 reindex 核心生成 INDEX/batches；整个 rename 每 dated 文件 read=1/parse=1，per-pool `scan --json`=0，reindex 不再读取两池。该约束不把多文件 rename 宣称为事务；`[grill-amendment]` rename 只有在 dated files、batch key、INDEX 与 batches 派生状态全部收敛后才可 exit 0，任一步失败均非零并允许原命令按有 provenance 的当前盘面识别阶段后重试。

`[spec-review-amendment]` recorder `scan --json` 是跨脚本 fail-closed contract：bug envelope 必须含 list `bugs` + list `problems`，todo 必须含 list `items` + list `problems`；每个 item 必须含 `id,module,summary,status,time,change,batch,file` 及 pool-specific `priority|type`，类型和值域与 schema 一致。`issues.py` 消费者遇坏 JSON、缺键、错误类型或缺 `file` 必须在写 INDEX/batches 前 non-zero，MUST NOT 以默认空 list 掩盖 partial install/protocol drift。

`[spec-review-amendment]` rename 首次执行 SHALL 先验证 old registry 存在、new 不存在且无 item 已引用未注册 new；随后原子把 registry header 改成 new，并在 target entry 写/替换 machine-owned `重命名自: old`，再 retag dated files、reindex。重试只有在 new entry 的 provenance 精确匹配 old 时才允许 old registry 缺失；该状态下全 old、old/new 混合或全 new items 都继续收敛。无匹配 provenance 的 `old missing/new exists` 必须保持未知 source 非零，MUST NOT 把误输或 orphan items 吸收成成功 rename。

#### Scenario: scan 每文件一次解析
- **WHEN** 一个 dated 文件同时包含 overlay、legacy table 与 prose blocks，运行 `scan --json`
- **THEN** instrumentation 显示该文件 open/read=1、document parse=1，输出仍完成 shadow merge、legacy arity、ID 与 block 检查

#### Scenario: batch rename 每池只扫描一次
- **WHEN** `batch rename old new` 同时命中 bug 与 todo 多个 dated 文件并成功触发 reindex
- **THEN** `issues.py` 对每个 dated 文件 binary read/parse 各一次，bug/todo `scan --json` 调用均为 0；reindex 使用 retag 后 snapshot 生成输出且 namespace 外 bytes 保真

#### Scenario: rename 中途失败可重跑收敛
- **WHEN** batch rename 在若干 dated 文件成功后、后续文件或 batches/INDEX 写入失败
- **THEN** 命令非零并点名失败位置；重跑从 dual-read 当前 snapshot 继续，把剩余 item、batch key、INDEX 与成员状态收敛一致，MUST NOT 因复用 snapshot 掩盖部分完成态，MUST NOT 在 reindex 失败时只 warning 后 exit 0

#### Scenario: batch key 已改名但派生输出未收敛 `[grill-amendment]`
- **WHEN** 重试 `batch rename old new` 时 registry 已无 `old`、已有 `new` 且 target entry 精确记录 `重命名自: old`，items 为全 old、old/new 混合或全 new
- **THEN** 命令把盘面识别为已开始的同一次 rename，retag 仍为 old 的 items 并补跑 reindex；完全收敛后 exit 0，失败仍非零

#### Scenario: retry 不静默合并冲突 batch `[grill-amendment]`
- **WHEN** `old` 与 `new` registry entry 同时存在，或 registry 仅有 `new` 但 provenance 缺失/不匹配，或首次执行前已有 item 引用未注册 new
- **THEN** 命令 fail-closed，列出 registry/provenance/item 证据，不 retag、不 merge、不写派生输出

#### Scenario: rename 的非致命 problems 不冒充写失败 `[spec-review-amendment]`
- **WHEN** rename snapshot 含与 batch retag 无关、仍可判 item 的 legacy 非致命 block/arity problem，且全部 target outputs 成功收敛
- **THEN** problem 回显 stderr但沿用默认 reindex 语义可 exit 0；任何影响 item/batch 判定的 fatal problem、dated/registry/INDEX/batches 写失败均 non-zero，MUST NOT warning-only success

### Requirement: 判据 MUST 只在其保护的风险真实存在的阶段求值

失鲜判据 MUST 只在其保护的风险真实存在的阶段求值，MUST NOT 全阶段求值后再为「合法 churn 阶段」补造豁免或逃生口。

design 域失鲜保护的风险是「照着一份已经变了的设计继续建」——该风险只在实现期存在。∴ design 域失鲜 MUST 只在阶段三起手至实现完成期间求值；进入代码审后 MUST NOT 再求值。

阶段判定 MUST 在失鲜判定**之前**完成。二者无循环依赖：阶段只取决于盘面上存在哪些产物，不取决于失鲜结论。

#### Scenario: 代码审期与 done 期不求值 design 域失鲜

- **WHEN** 流程已进入代码审期或 done 期，此时对四件套的修订发生（如 `[impl-review-fix]` 修订，或 verify 的 design adherence 检查判定「revise design.md to match reality」）
- **THEN** gate MUST NOT 因该修订判 design 域失鲜——这些修订是工作流明文允许的动作，且在本仓历史上是常态而非偶发
- **AND** MUST 有用例锁死此方向

#### Scenario: 实现窗口的三个分支各自受保护

- **WHEN** 盘面处于 `RUN_SOP`、`RUN_PLAN`、`CONTINUE_IMPL` 三者中的**任意一个**，且 design 域监视集内容与锚版本不等值
- **THEN** gate MUST 判失鲜
- **AND** 三个分支 MUST **各有**用例——它们是三处独立的提前返回点，只在其中最后一个之后加检查会使前两个完全逃出判定（方向为 fail-open）
- **AND** MUST NOT 提供任何「分诊后重锚」「按 commit subject 豁免」之类的旁路

#### Scenario: 实现期的四件套实质修订被拦下并逼回重审

- **WHEN** 在实现窗口内，四件套被实质修订（差异不止于复选框状态）
- **THEN** gate MUST 判失鲜，撞门者 MUST 走「重审 → 重新拍板」的正规流程
- **AND** 这是**有意的行为收紧**——该模式在本仓历史上出现过，本判据将其逼回正规流程，MUST NOT 被后续维护者当作缺陷而放宽

### Requirement: 失鲜判定 MUST 直接比较内容，MUST NOT 从 git 管道推断路径变更

机械层 MUST NOT 使用下列任一方式判定「被审内容是否改变」：`git log --name-only`、`git diff-tree -m`、`git diff-tree --cc`、负向 pathspec、整棵树的 sha。这些方式已累计产出实测复现的缺陷（详见 `openspec/adr/0026`），且互为解药兼病灶、可被外部 config/env 翻转。

机械层 MUST 改为直接比较内容：

- **design 域** MUST 对锚与 HEAD 各枚举一次监视集，比较 `path → (mode, type, oid)` **映射**；映射不等即失鲜。
  MUST NOT 只枚举单侧——只枚举 HEAD 侧会漏掉「锚有而 HEAD 已删」的路径，只枚举锚侧会漏掉「HEAD 新增」的路径，两者方向均为 fail-open。
- **code 域** MUST 比较 `git ls-tree` 的顶层条目（排除 `openspec` 条目后）。

复选框豁免 MUST 常开、按**内容**切，MUST NOT 按阶段切——`tasks.md` 复选框的写入方是不受阶段约束的自由行为，按阶段切会立即产生假失鲜。

#### Scenario: 实现期不得让设计门失鲜

- **WHEN** 设计门拍板后进入实现期，提交改动源码文件，并把 `superpowers-plan.md` 中该 ticket 的验收复选框由 `- [ ]` 勾成 `- [x]`
- **THEN** gate MUST 判 design 域 fresh——源码与 `superpowers-plan.md` 均不在 design 域监视集内
- **AND** **监视集是承重的**：任何令实现期提交使设计门失鲜的实现（如裸 `reviewed_sha == HEAD` 比较）MUST 判为不合格

#### Scenario: `specs/` 子树的新增、删除与 rename 均判失鲜

- **WHEN** 锚之后在 `specs/` 下新增文件、删除文件、或 rename 文件（后者内容可完全不变）
- **THEN** gate MUST 判失鲜——三者均使 `path → (mode, type, oid)` 映射不等
- **AND** MUST 各有用例，且 MUST 经 `is_stale` 公共入口求值
- **AND** 某路径只在一侧存在 MUST 判失鲜，MUST NOT 混作「读取失败」处理——二者是不同的判定

#### Scenario: `tasks.md` 纯复选框翻转不失鲜（任何阶段）

- **WHEN** `tasks.md` 的内容差异在复选框标记归一化后逐行等值
- **THEN** gate MUST 判 fresh，且该豁免 MUST 与当前处于哪个阶段无关
- **AND** 差异超出复选框状态时 MUST 照常判失鲜
- **AND** 豁免生效前 MUST 先确认锚与 HEAD 两侧该路径 mode/type 相等且均为 `blob`——mode 变更（如 chmod）
  或 type 变更（如 regular↔symlink、或伪装成 gitlink 的子模块指针）即使内容归一化后相等也 MUST 判失鲜，
  MUST NOT 因内容比较通过而放过状态位变更（该收紧防的是「合法豁免通道」被状态位伪装绕过）

#### Scenario: 合并把已批准产物换回锚前旧内容

- **WHEN** 锚提交之后的一次合并，使某监视文件在 HEAD 上的内容变回锚**之前**某祖先版本（该内容不由锚后任何提交引入，故任何逐提交枚举都看不到它）
- **THEN** gate MUST 判失鲜——内容比较不依赖提交拓扑，锚与 HEAD 的映射不等即成立
- **AND** MUST 有用例，且 MUST 经 `is_stale` 公共入口求值

#### Scenario: 代码审后的源码改动 MUST 被 code 域捕获

- **WHEN** 代码审出具结论之后，源码经由 merge 提交中 resolve 引入改动，或经 `git mv` 从顶层迁入 `openspec/`
- **THEN** gate MUST 判 code 域失鲜——两者均使非 `openspec` 顶层条目集合改变
- **AND** 二者 MUST **各有**用例并附变异证明——它们是 code 域改用顶层条目比较后**唯一的正面收益证明**

#### Scenario: `openspec/` 内的记账不得让 code 域失鲜

- **WHEN** 代码审通过后，正常收尾流程写入 `verify-report.md`、或 archive 把 change 目录移入 `openspec/changes/archive/`——即改动全部落在 `openspec/` 之内
- **THEN** gate MUST 判 code 域 fresh
- **AND** 该域的比较粒度 MUST 能排除 `openspec/`：整棵树的 sha 比较 **MUST NOT** 被采用——它在上述正常流程的第一步即假阳（已实测）

### Requirement: 评审锚 MUST 由 producer 记录，MUST NOT 从提交历史反推

评审结论的锚 MUST 是评审时由 producer 写入报告 frontmatter 的显式提交标识（`reviewed_sha`），MUST NOT 由「最后一次触碰报告文件路径的提交」之类的反推方式得出。

反推式锚可被任何后续触碰该文件的提交无声前移，从而把锚前的未审改动埋在判定范围之外——该提交无需修改任何结论字段，在 `git log -p` 中与评审结论毫无关联，其隐蔽性不被「篡改结论字段留痕可审计」这一既有残余面覆盖。

锚的语义是「**被批准 / 被放行的那个盘面**」，而非「写报告的时刻」。

#### Scenario: 锚 MUST 指向被放行的提交，而非写报告的时刻

- **WHEN** 某评审步在出具结论的同一轮内还修改了它所审查的对象（如代码审的自动修复）
- **THEN** producer MUST 先提交该修改、令锚指向该提交，再单独提交报告；MUST NOT 让锚指向不含该修改的更早提交
- **AND** 否则报告落盘后判定立即失鲜（锚不含刚提交的修改），使该评审步每轮自锁
- **AND** MUST 有用例覆盖「该评审步的修复非空」这一情形

#### Scenario: 结论落盘前对被审对象的追加修订 MUST 先单独提交

- **WHEN** 评审结论已产出、但在写入结论字段与锚之前，被审对象又被实质修订（如人读评审报告后要求修改设计文档）
- **THEN** 该修订 MUST 先单独提交、取得其提交标识后，才写入结论字段与 `reviewed_sha`
- **AND** MUST NOT 让该修订与结论字段的写入落进同一次提交——那会使锚指向不含该修订的更早提交，结论落盘后首次判定即失鲜，形成自锁
- **AND** MUST 有用例覆盖此路径，且其变异证明为「令锚指向修订前的提交 ⇒ 判定失鲜」

#### Scenario: 无关的报告排版提交不得移动锚

- **WHEN** 评审通过后，先有提交引入未经审查的源码改动，再有一个与之无关的提交仅修改报告文件的排版（如补一个换行），且不改动任何结论字段
- **THEN** gate MUST 仍判失鲜——锚为 producer 记录值，不因报告文件被触碰而前移

#### Scenario: 锚缺失或非法时 fail-closed

- **WHEN** 报告 frontmatter 缺 `reviewed_sha`、其取值不是完整 40 位 OID、或该对象在仓中不存在 / 不是 commit 对象
- **THEN** gate MUST 判 `UNKNOWN`（exit 6），MUST NOT 回退到任何反推式锚、MUST NOT 判 fresh
- **AND** 格式校验（语法级）与对象存在性校验（语义级，需 git 调用）MUST 分层实现——前者所在的解析函数为纯文本函数，供 live 读与归档文本读共用
- **AND** reader 契约 MUST 与 producer 同批落地：只落 producer 会使新锚永不被读取，只落 reader 会使存量报告全部 fail-closed
- **AND** 存量无 `reviewed_sha` 的报告 MUST 要求重审一次，MUST NOT 为兼容而静默回退

#### Scenario: 结论字段与锚 MUST 原子写入

- **WHEN** producer 写入评审结论字段（如 `design_approved`）与 `reviewed_sha`
- **THEN** 二者 MUST 在同一次文件写入中落盘
- **AND** 否则中断可产生「结论字段已在、锚缺失」的中间态：该态下结论字段判定通过、锚读取却 fail-closed，撞门者得不到「缺的是哪个字段」的指引

### Requirement: 内容比较 MUST 区分读失败与内容为空

比较两个版本的文件内容时，MUST 显式判定读取操作的返回码，MUST NOT 让两次失败的读取因各自返回空结果而比较相等。

此为「非零退出被折叠成空结果」这一失效模式在新实现上的复现面——同一模式已在旧实现的 `run_git` 上造成 fail-open，且在本 change 的验证 fixture 中再次出现（两侧读取均失败、比较判等值、结论假绿）。

#### Scenario: 读取失败保守判失鲜

- **WHEN** 取锚版本或 HEAD 版本的内容时，git 以非零退出返回（对象不存在、仓损坏、权限不足等）
- **THEN** gate MUST 保守判失鲜或 `UNKNOWN`，MUST NOT 因两侧均为空结果而判等值
- **AND** MUST 有用例，且 MUST 附变异证明——删除该 returncode 判定 ⇒ 用例变红

#### Scenario: 存在性判定 MUST 由能区分「缺失」与「失败」的原语承担

- **WHEN** 需要判断某监视路径在锚或 HEAD 一侧是否存在
- **THEN** MUST 使用「路径不存在时正常退出并返回空结果」的枚举原语，使「缺失」与「调用失败」在返回码上判然二分
- **AND** MUST NOT 让「路径不存在与仓损坏返回同一退出码」的取内容原语承担存在性判定——那会使被删除或迁走的监视文件被误诊为读取失败，向撞门者给出错误的补救指引
- **AND** 取内容的调用 MUST 只在存在性已确认之后发生，其非零退出方可一律视为真实读取失败
- **AND** MUST 有用例：监视清单内的文件在一侧被删除或迁出监视集 ⇒ 判失鲜，且诊断不呈现为读取失败

### Requirement: gate 的 git 调用失败 MUST 落在退出码契约集内，且不受外部态影响

`ship_gate.py` 对外承诺的退出码集为 `{0, 3, 4, 5, 6}`。调用 git 时的任何环境级失败 MUST 被映射进该集合，MUST NOT 以未捕获异常逸出使退出码变成解释器默认值。

git 子进程 MUST 中和一切能改变判定输入的外部可控态：配置面经 `-c` 显式覆盖，环境面清理 `GIT_*` 环境变量。MUST NOT 以「当前实现碰巧没用到那些开关」作为免于中和的理由。

#### Scenario: git 不可用或不可执行

- **WHEN** `git` 不在 `PATH` 上、不可执行、或为无效可执行格式，`subprocess.run` 抛出 `OSError` 家族异常（含 `FileNotFoundError`、`PermissionError`）
- **THEN** gate MUST 捕获并映射为 `UNKNOWN`（exit 6），输出可读诊断；MUST NOT 让异常冒泡产生 traceback 与 exit 1
- **AND** 该捕获 MUST 覆盖**全部** git 调用 helper，且 MUST 对每个 helper **各有**验证——`main()` 首次 git 调用失败即退出，单一端到端用例只能覆盖其中一个

#### Scenario: git 调用挂起

- **WHEN** 某次 git 调用长时间不返回
- **THEN** 该调用 MUST 有超时上界，超时 MUST 映射为 `UNKNOWN`（exit 6）
- **AND** 超时值 MUST 对本仓正常规模的本地元数据查询留足余量

#### Scenario: 失败原因 MUST 可区分且可行动

- **WHEN** gate 因任一环境级失败判 `UNKNOWN`
- **THEN** 诊断 MUST 区分「git 不可用」「调用超时」「锚缺失」「锚非法」「锚指向对象不存在或非 commit」「读取失败」
  六类，各给出对应的补救指引——「锚非法」（`reviewed_sha` 语法非法：缩写 SHA / `HEAD` / 坏 hex，语法级、
  无需 git 调用即可判）与「锚指向对象不存在或非 commit」（对象在仓中确实不存在、或存在但是 blob/tree 而非
  commit，语义级、需 git 调用）MUST 分列两类而非合一——前者补救是人工订正为完整 40 位 hex，
  后者补救是排查是否 force-push 改写了历史，两者补救动作不同
- **AND** MUST NOT 以单一通用文案覆盖全部六类——六者的补救动作互不相同，而 `UNKNOWN` 在上游链序中的处置是「停并转述该诊断」

#### Scenario: 环境变量不得改变判定输入

- **WHEN** 调用方环境中存在影响 git 路径匹配或 diff 行为的变量（如 `GIT_ICASE_PATHSPECS`）
- **THEN** gate 的 git 子进程 MUST 不继承该类变量，判定结果 MUST 与该变量是否设置无关
- **AND** 环境清理 MUST 以排除法实现（剔除 `GIT_` 前缀键），MUST NOT 以白名单方式只保留少数变量——后者会在部分平台上漏掉进程创建所必需的系统变量
- **AND** MUST 有用例：在设置该类变量的环境下判定结论与未设置时一致，且非 `GIT_*` 的环境变量原样透传

