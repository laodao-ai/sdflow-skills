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

阶段三 SHALL 在阶段二设计门之后无任何阻塞人类门地连续运行 `writing-plans → subagent-dev → sdflow-code-review → sdflow-done`；**编排层入口 = `/sdflow-ship`**（一次调用驱动 5.5→9，按「阶段三编排台账确定性」需求经 ship_gate 推进；手动逐步仍为合法 reference 路径）。能修的自动修；**遇 ≥2 方案 MUST 按三级决策协议**〔T10，替换旧"有把握自动选"自评表述〕：①有客观判据（测试/断言/基准可判）→ 自动选并记理由；②无客观判据 → 派对抗镜复核推荐项，通过方自动选（复核记录进报告）；③复核不过或无从复核 → defer 进 buglist/todolist 并由 hand-off 引导另开 change 清理。MUST NOT 以自评置信（"有把握"）作为自动选定的唯一依据。修不了或需拍板的 MUST 进 buglist/todolist 延后。

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

workflow bundle（`workflow/*.md` / `trigger-catalog.md` / `spec-checklists/` / `code-checklists/` / review UI / hooks / checkpoint 脚本）与自制 skill 的改动 MUST 在权威源（sdflow-skills 的 bundle 公共家与 skill 目录）进行，MUST NOT 只改消费仓副本。部署 SHALL **按内容性质分层**，而非整 bundle 复制：

- **规则**（`workflow/*.md` + `spec-checklists/` + `code-checklists/`）MUST **不再复制进消费仓**，改由 skills 从全局 canonical bundle 解析（见「规则解析 resolver」需求）。
- **review UI 机械**（`tools/` + `serve.sh` + `review.html`）SHALL 仍复制进消费仓 `openspec/`（服务器根=openspec/ 约束逼留，尽量少）。review UI SHALL 以**根锚单一查看面**提供——`openspec/review.html` 起于全树（其 `location.pathname` 为根 → scope=""），经内置 INDEX/树在应用内浏览到任意 change/roadmap；MUST NOT 为每个 change 或 roadmap 生成独立的 `review.html` stub（既冗余于根锚，又违最小部署足迹 adr/0003）。**scoped 深链**〔grill-amendment；spec-review A1/A2/A3 加固〕：engine `bootstrap` SHALL 先读 `location.hash`——非空则作初始 scope 候选，经**同一 origin 检查**（`new URL(rawHash, origin)`，比较 `.origin === location.origin`）后**取其 `.pathname` 喂 scope**（A3：MUST 提取 `url.pathname`，非把 raw hash 原样喂——`#http://host/changes/X/` 同源但非 `/path` 形态；提取 pathname 顺带归一 `%2F` 编码）；深链范围 = **任意同源路径**（与 `navigate` 写 `#<path>` 契约一致，非仅 change/roadmap）。空 hash / 跨源（协议相对 `//host`）MUST 回落 `location.pathname`，MUST NOT 越界跳转；路径遍历由服务器根（openspec/）兜住。**陈旧深链 404**：MUST NOT 停在裸报错卡死；bootstrap MUST **自派发**（自 try/catch 调 loadDir/loadDoc，因 `navigate` 吞错不返信号）、404 走根 INDEX 路径（**MUST NOT 重调 bootstrap**——防同坏 hash 递归，回落前 `replaceState` 清 hash）、**显式提示**以**专用 DOM 节点在回落渲染之后注入**（MUST NOT `contentBody.innerHTML=`，否则被擦 → 提示静默蒸发，违反静默守卫）。〔恢复 `drop-per-dir-review-stub` 标注的可接受降级增强〕
- **全局 Claude hook**（`~/.claude/hooks/` + 注册进 `~/.claude/settings.json`）集 SHALL = `{ff0-branch-guard}`（PreToolUse.Bash 的 FF-0 分支守卫）。`sdflow-init` MUST 维护一份**退役 hook 名单**并对其**反注册**（从 settings.json 各事件列表外科式摘除匹配条目 + 删除 `~/.claude/hooks/` 里的脚本，幂等、存量安装自愈、fresh 安装 no-op）；MUST NOT 只增不减而在存量安装留下指向已删脚本的孤儿注册。该反注册 SHALL 覆盖**两条更新路径**：① `sdflow-init init/update`（消费项目铺设路径，每次运行）；② `setup.sh`（工具链升级路径，装了 sdflow-skills 的机器经 `/sdflow-upgrade` 必跑、早于任何 `sdflow-init update`）。两路径 MUST 复用**同一** retire 逻辑（`init.py` 暴露独立 retire 子命令，`setup.sh` 调之），MUST NOT 各写一份。`setup.sh` 调用该步 SHALL **fail-safe**：解释器缺失或调用非零退出 MUST NOT 阻断 setup 安装（清理为尽力而为，非安装必要步）。fail-safe 构造 SHALL 以 `|| echo`/`|| true` 收尾〔A5〕——`set -e` 下仅 `command -v` 门控或 if-guard 不够（then-body 仍受 set -e，present-but-nonzero 会中止 setup）。解释器探测 SHALL `python3 || python`〔A6〕——MUST NOT 假设 `python3`（Windows/Git-Bash 常名 `python`，否则 Windows 机系统性漏 retire，T44 零收益）。全局 hook 的**安装侧**（`ensure_global_hooks` 装 ff0-branch-guard 等 PreToolUse.Bash 拦截钩子）MUST NOT 随之进 `setup.sh`〔grill-amendment·不对称原则〕——**清除主动伤害可 eager（retire 进 setup.sh），新增会拦截的能力须 opt-in（ensure 留 `sdflow-init init/update`，用户显式启用工作流时才装）**，MUST NOT 把拦截钩子推给仅安装 skill、不用 OpenSpec 的机器。
- **`checkpoint-commit.sh`** MUST 全局安装到 agent 中立的 canonical 根 `~/.sdflow/hack/`（**非** `~/.claude/hooks`——它是跨-agent bash 工具、非 Claude 事件 hook）、不再进消费仓 `hack/`。
- **`config.yaml` / `changes/` / `specs/`** 天然属仓，仍仓内。

消费仓的规则副本 SHALL 经 `sdflow-init update` 采纳最新（update 对规则为"停复制 + 陈旧遮蔽告警"，见「迁移」需求），MUST NOT 直接编辑部署副本。`sdflow-init` 的部署实现（`copy_bundle`）MUST 区分两种铺设模式：默认（消费仓）模式只拷 `tools/` 子树，且拷贝前若目的地 `tools/` 已存在 MUST 先整删再整拷（清后拷收敛），MUST NOT 用"存在则合并覆盖"语义（防上游删文件后消费仓残留孤儿文件）；`--dev` 整 bundle 刷新模式仅供 toolkit 源仓自身 dogfood 用，MUST 先校验 `--root` 解析后的真实路径等于本脚本所在 toolkit 仓根，不等则 MUST 拒绝执行（防误把整套规则灌进消费仓）。

#### Scenario: 修改 workflow 规则
- **WHEN** 需要修改 workflow.md
- **THEN** 改 sdflow-skills 权威源 `sdflow-init/assets/workflow/workflow.md`（不提根，仍是唯一权威源），消费仓经全局 canonical 自动跟随 released HEAD，不直接编辑消费仓副本

#### Scenario: 新 init 的消费仓不含规则副本
- **WHEN** 对一个新项目跑 `sdflow-init init`
- **THEN** 消费仓 `openspec/workflow/` 只含 `tools/`（≈5 文件），规则文件数 = 0；`checkpoint-commit.sh` 全局安装、不进仓 `hack/`

#### Scenario: 消费仓 update 后 tools/ 收敛、不留孤儿文件
- **WHEN** 权威源 `assets/workflow/tools/` 删除了某个已废弃文件，消费仓随后跑 `update`
- **THEN** 消费仓 `openspec/workflow/tools/` 被整删重拷，废弃文件不再残留（MUST NOT 因 `dirs_exist_ok` 式合并覆盖而假装已同步）

#### Scenario: --dev 只许 toolkit 源仓自用
- **WHEN** 在某个消费仓（非 toolkit 源仓自身）误跑 `sdflow-init update --dev`
- **THEN** 脚本校验 `--root` 与 toolkit 仓根不一致，拒绝执行并报错，MUST NOT 把整套规则文件灌进该消费仓

#### Scenario: 建 change 不再落每目录 review stub
- **WHEN** 跑 `openspec new change X`（或经 `/opsx:ff` 等入口 scaffold 变更）
- **THEN** `openspec/changes/X/` 目录**不含** `review.html`；查看该变更改由根锚 `openspec/review.html` 起服务、经内置 INDEX/树浏览抵达（浏览能力不回退）

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

#### Scenario: review UI 根锚 hash 深链落 scoped 首屏〔T45·grill 宽目标〕
- **WHEN** 用户打开 `openspec/review.html#/changes/some-change/`（或任意同源路径如 `#/specs/spec-workflow/spec.md`、`#/INDEX.md`——与 `navigate` 写出的 hash 契约一致）
- **THEN** engine bootstrap 即以 hash 路径为初始 scope，首屏直接显示该视图（非全树 INDEX）；浏览到其它目录仍走既有 hash-based 导航

#### Scenario: 空 hash 或跨源 hash 回落根锚全树〔T45 安全·grill 同源守卫〕
- **WHEN** 打开 `review.html`（无 hash），或 hash 为跨源/协议相对值（如 `#//evil.com/x`）
- **THEN** engine 经同源守卫拒绝跨源 hash、回落 `location.pathname` 起于全树 scope=""，MUST NOT 越界 fetch 跨源资源；路径遍历（`#/etc/passwd`）由服务器根（openspec/）兜住返 404

#### Scenario: 陈旧深链 404 回落根锚并显形〔T45·grill Q3·反静默守卫〕
- **WHEN** 深链 hash 指向已归档/移动的目录（如 `#/changes/foo/` 而 foo 已移入 `changes/archive/`）→ fetch 404
- **THEN** engine MUST NOT 停在 `navigate` 裸报错致侧栏空、无🏠、卡死；SHALL 回落根 bootstrap（INDEX/全树，恢复完整导航）并**显式提示**「深链未找到（可能已归档）」，MUST NOT 静默把用户扔到别处（遵反静默守卫）

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

工具链自制 skill MUST 统一使用 `sdflow-` 前缀命名（目录名 = 安装名 = 斜杠命令名），按 RENAME-MAP（design §三）执行：`sdflow-init`、`sdflow-done`、`sdflow-maintain`、`sdflow-roadmap`、`sdflow-spec-review`、`sdflow-code-review`、`sdflow-buglist`、`sdflow-todolist`、`sdflow-issues`。豁免保留名单 = `embedded-test-sop`（域技能）、`openspec-upgrade`（升级外部 CLI）、`sdflow-upgrade`。改名 SHALL 用 `git mv`（保 blame 连续）；主 spec 与功能性文件全文中的旧 skill 名 SHALL 随更名同步替换（语义不变）；文档性历史记录（`adr/`、ROADMAP 历史行、CONTEXT 术语史、`changes/archive/`）MUST NOT 回改。改名后各 SKILL.md 的 description MUST 随新名重写且**触发等价**：原触发场景语句集 SHALL 全部保留（仅替换斜杠命令名与旧名指称），等价性以 `trigger-map.md` 对照表留档可审。

#### Scenario: 目录名与斜杠命令一致切换
- **WHEN** 改名完成并在运行 checkout 重跑 `setup.sh`
- **THEN** `~/.claude/skills/` 与 `~/.codex/skills/` 下只存在新名链（12 = 9 新 + 3 留）；旧名 dangling 链被孤儿清理收走，MUST NOT 残留

#### Scenario: 触发等价不回退
- **WHEN** 用户说出改名前即可触发某 skill 的语句（如"记一下这个 bug"）
- **THEN** 新 description 仍使该语句触发对应新名 skill（sdflow-buglist）；trigger-map.md 中该短语有对照行

#### Scenario: sibling 脚本路径随名迁移
- **WHEN** `sdflow-issues` 的 `issues.py reindex` 需要子进程调用兄弟脚本
- **THEN** 它按自身位置上溯 SKILLS_ROOT 后以**新目录名**（`sdflow-buglist`/`sdflow-todolist`）join 路径并成功调用；`sdflow-done` §2.1 的固定路径同为新名

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

`sdflow-ship` 的步序推进 MUST 由确定性脚本 `ship_gate.py` 判定（**盘面即状态**：以 change 目录产物存在性与结论行为账本，MUST NOT 设可变 state 文件造第二真相源）；编排 skill MUST 在每步前后调用 gate 并遵其判定，MUST NOT 以 prose 记忆步序。gate MUST 只读（零副作用）、双输出（首行人读摘要 + JSON 机读）、以退出码承载门禁语义（0=可推进 / 3=拒绝起跑 / 4=上游 blocker / 5=verify FAIL / **6=UNKNOWN 判定不能**〔spec-review-amendment〕）；同一报告并存冲突锚行 MUST 判 UNKNOWN 点名冲突行，MUST NOT 猜优先级。机判锚点 MUST 为**模板写死的机器注释行**〔grill-amendment：自然语言结论行正则对真实存档全 miss，禁作锚点〕：设计门拍板 = `<!-- ship-gate: design-approved -->`；verify 结论 = `<!-- ship-gate: verify=PASS -->` / `verify=FAIL`；code-review 放行 = `<!-- ship-gate: code-review=pass -->` / `=blocked`。三个报告的生成模板（sdflow-spec-review 拍板回写约定 / sdflow-done verify 模板 / sdflow-code-review 报告格式）MUST 输出对应锚行；gate 以**行级字面查找**解析——逐行 `strip()` 后整行等值于锚字面、忽略 fenced code block（```）内的行；MUST NOT 用纯子串（否则报告正文对锚的**描述性提及**或代码块内文档示例会假命中，让门禁被非结论文本触发）〔gate-anchor-line-scoped B4〕。锚行集合在脚本头注释与各模板双向钉死同 change 演进（各模板 MUST 把锚写在独占一行）。**完成判据的两处加固**〔ship-gate-hardening-2〕：① checkpoint 任务标签 MUST 按 change 命名空间归属隔离（`checkpoint(<change>:task<N>-)`，gate 只认当前 change；裸标签向后兼容，详见下方「完成任务号按 change 命名空间隔离」Scenario 组）；② 复选框辅通道 MUST 按 `### Task <n>:` 分段绑定、MUST NOT 全局全勾放行所有 task（详见下方「复选框辅通道按 Task 分段绑定」Scenario 组）。

#### Scenario: 未过设计门拒绝起跑
- **WHEN** 对一个 spec-review-report.md 缺失或不含「设计门拍板」标记的 change 调用 /sdflow-ship
- **THEN** ship_gate 退出码 3（REFUSE_START），skill 停止并提示先完成设计门，MUST NOT 起跑任何阶段三步骤

#### Scenario: verify FAIL 停并上抛
- **WHEN** 链行进至 sdflow-done 后 verify-report.md 结论为 FAIL
- **THEN** gate 退出码 5，ship 停止、原样上抛缺口清单，MUST NOT 继续 archive/merge（任何一层评审覆盖不得无声蒸发）

#### Scenario: 前置产物缺失点名
- **WHEN** 某步产物缺失（如 code-review-report.md 不在）
- **THEN** gate 输出 next=对应 skill 与 missing 清单，编排按此推进；实现完成判据 MUST 以 **git 历史 checkpoint 任务标签为主锚**（plan 任务数 N 对 checkpoint 去重任务号集，齐 N 判完成〔grill-amendment〕；标签 MUST 按 change 命名空间归属过滤 `checkpoint(<change>:task<k>-`（裸 `checkpoint(task<k>-` 向后兼容），见下「命名空间隔离」Scenario 组〔ship-gate-hardening-2〕；**收集窗口 MUST 为含 superpowers-plan.md 首次提交自身的闭区间 `[sha, HEAD]`**——即 `git log <sha>..HEAD --no-merges` 加对 `<sha>` 自身 commit subject 的同规则解析；plan 与首个 task 锚同 commit（checkpoint `add -A` 携带未提交 plan 的合法盘面）时该 task MUST 计入，MUST NOT 漏数〔B1 修复，替换旧排他窗口表述〕；MUST NOT 全历史扫描——main 遗留标签会造成假齐 N〔spec-review-amendment 设计门拍板 Q2〕；plan 标题命中 0 → UNKNOWN；**重号 `### Task <n>:` 段 → UNKNOWN**〔ship-gate-hardening-2〕）、plan 复选框**按 `### Task <n>:` 段绑定**为辅（MUST NOT 全局全勾放行所有 task，见下「分段绑定」Scenario 组〔ship-gate-hardening-2〕），两通道皆不可判时 gate 判 UNKNOWN 停上抛，MUST NOT 猜测推进、MUST NOT 以 gitignored 的 SDD ledger 为判据

#### Scenario: plan 与首个 task 锚同 commit 不漏数〔B1〕
- **WHEN** superpowers-plan.md 的首次提交 commit 本身就是 `checkpoint(task1-<slug>)` 提交（plan 未单独提交、被首个 task 的 checkpoint `add -A` 一并携带入库）
- **THEN** gate 的完成任务号集 MUST 含 task1（窗口为含该 commit 自身的闭区间），plan 任务数 N 齐时 MUST NOT 输出 CONTINUE_IMPL 误报

#### Scenario: 陈旧 FAIL 不卡死 resume〔grill-amendment D9〕
- **WHEN** verify-report 带 FAIL 锚行，其提交之后存在触及 `openspec/` 之外路径的修复提交，用户重调 /sdflow-ship
- **THEN** gate 判该结论陈旧 → NEXT=重跑 sdflow-done（重验），MUST NOT 以陈旧 FAIL 退出卡死

#### Scenario: 干预后陈旧 PASS 不放行〔grill-amendment D9〕
- **WHEN** verify/code-review 锚行为 pass/PASS，但其后有人手改了 `openspec/` 之外的代码
- **THEN** gate 判受影响步结论陈旧 → 重跑该步，MUST NOT 让旧结论背书新代码直通 merge

#### Scenario: design-approved 不因实现提交失鲜〔spec-review-amendment 设计门拍板 Q1=B〕
- **WHEN** 设计门拍板锚行已落，实现期产生大量触及 `openspec/` 之外路径的提交（正常实现活动）
- **THEN** gate MUST 保持 design-approved 有效（新鲜度按锚分域：该锚仅当其后存在触及本 change 四件套路径的提交才失鲜须重审），MUST NOT 因实现提交判其陈旧而 REFUSE_START（防实现期链自锁）

#### Scenario: 阶段三合法尾流修订不失鲜〔B2〕
- **WHEN** design-approved 锚行已落，其后 sdflow-code-review 按工作流对 design.md/tasks.md 打 `[impl-review-fix]` 补丁并以 commit subject 闭合字面前缀 `checkpoint(impl-review)`（含右括号）提交（触及四件套路径）
- **THEN** gate 的 design 域新鲜度判定 MUST 豁免该类提交（不判拍板失鲜、不 REFUSE_START）；豁免面 MUST 仅限**精确式 `subject == "checkpoint(impl-review)" 或 subject 以 "checkpoint(impl-review):" 起始`**〔spec-review-amendment BR-7：裸闭合前缀 startswith 仍收 `checkpoint(impl-review)evil` 尾串垃圾，须精确式〕——`checkpoint(impl-review-fix)`/`checkpoint(impl-reviewX)`/`checkpoint(impl-review)evil` 等从不由 checkpoint 脚本合法产生的变体 MUST NOT 豁免（照判失鲜）；其他 subject 触及四件套照判失鲜（实现改设计须重审的既有语义不变）；豁免 MUST NOT 分析改动内容（只认 subject 不认 hunk），由此「经豁免的语义级四件套改动不经二次批准即随档 ship」属**已登记的接受取舍**〔grill Q2〕；伪造/手工 subject 绕过豁免属显式越权同权级（git 留痕可审计），MUST 在脚本头注释「已知不覆盖」中声明

#### Scenario: 未提交报告视为 fresh〔spec-review-amendment 设计门拍板 Q3=A〕
- **WHEN** 某报告文件存在且含锚行，但从未 git 提交（`git log -1 -- <path>` 空输出）
- **THEN** gate MUST 视其为 fresh 并在 JSON 注明 `freshness=uncommitted`（人机同权：手写产物合法），MUST NOT 因无提交记录而判进行中或报错

#### Scenario: 无锚行产物 = 步进行中〔grill-amendment D9〕
- **WHEN** 某报告文件存在但不含任何 ship-gate 锚行（如中断的半成品）
- **THEN** gate 判该步进行中 → NEXT=重跑该步，MUST NOT 当作已完成

#### Scenario: 暂停后重调即续、人机同权〔grill-amendment D9〕
- **WHEN** 链中途停止（任意原因），期间用户手动完成了某步（如手跑 /sdflow-code-review 产出报告），之后重调 /sdflow-ship
- **THEN** gate 仅凭盘面推进（不辨产者），从下一缺口继续；实现中断场景 gate 输出已完成任务号集供 SDD 勿重派；ship MUST NOT 依赖任何跨步内存状态

#### Scenario: 条件步按 TG 判定
- **WHEN** change 的 proposal 未标注 TG-02（非嵌入式）
- **THEN** gate 对 step 5.5 输出 SKIP 并记录理由；命中 TG-02 时高风险/TG-18 细判归模型（每步内部判断，prose 允许域）

#### Scenario: 归档后识别 SHIPPED 终态〔B3 + D3 硬化〕
- **WHEN** change 的 active 目录 `openspec/changes/{change}/` 不存在，但归档目录 `archive/<YYYY-MM-DD>-{change}/`（发现经**纯 git 域** `git ls-tree HEAD ∪ ls-tree <base>` 列举 + `re.escape(change)` 套日期前缀 fullmatch，**MUST NOT 用文件系统 glob**〔H2/BR-4〕）**已存在于 base 树** 且该归档目录内 `verify-report.md` **含 `<!-- ship-gate: verify=PASS -->` 锚**〔H1/BR-2〕
- **THEN** gate MUST 输出 SHIPPED（exit 0），MUST NOT 按 active 路径找不到 spec-review-report.md 而误报「未过设计门」；该短路判定 MUST 位于设计门 pre-flight 与新鲜度检查之前；终态判据 MUST 为 change 域可达性（`git ls-tree <base>`）而非全局 `branch_state()`〔grill-amendment〕；发现 MUST 与判据同域（纯 git，工作树无关）——MUST NOT 用工作树 glob（否则跨分支查已并 change 会假 REFUSE、未跟踪垃圾目录会假 RUN_VERIFY）〔H2/BR-4〕；SHIPPED MUST 追读 archived verify=PASS 锚——MUST NOT 仅凭目录存在性放行（手工空壳归档目录不得假 SHIPPED）〔H1/BR-2〕；`--change` MUST 校验为 slug 或 `re.escape` 后匹配，MUST NOT 把用户输入当 glob 元字符〔H5/HRTG-4〕；base 无 main/master → UNKNOWN，detached HEAD 对 D3 判定无关（凭 base 树可达仍可 SHIPPED）〔H3/H4〕；active 存在时 final SHIPPED 的 archived 谓词 MUST 收紧，MUST NOT 被旧/同名 archive 触发〔H1/HRTG-1〕

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

#### Scenario: 描述性锚提及不触发门禁〔gate-anchor-line-scoped B4〕
- **WHEN** 某报告（如 spec-review-report.md）正文含机判锚字面（`<!-- ship-gate: design-approved -->` 等）但**非独占一行**——内联在描述句中（前后有其它字符 / 行内反引号包裹）、或独占一行但位于 fenced code block（```）内作文档示例，且结论区**无**独占一行的真锚
- **THEN** gate 的锚检测 MUST 判该锚**未命中**（返回集合不含它）——描述性提及 / 文档示例 MUST NOT 触发对应门禁；对 design-approved 而言此盘面 MUST 判 REFUSE_START（未过设计门），MUST NOT 因子串命中假过设计门越过 adr/0004 红线〔活体复现：checkpoint-tag-single-source 报告仅含描述句即被首跑假放行 RUN_PLAN〕；行级判据 MUST 保留多命中语义——`verify=PASS` 与 `verify=FAIL` 各独占一行并存时 MUST 仍各自命中以触发 UNKNOWN 冲突判定，MUST NOT 因行级收紧而漏返冲突锚；锚检测的两处解析点（读文件的 `anchors_in` 与读 git-show 文本的 `archived_verify_state`）MUST 共用同一行级判据，MUST NOT 只收紧其一

#### Scenario: 归档 verify 描述性提及不触发假 SHIPPED〔gate-anchor-line-scoped B4·SHIPPED 路径〕
- **WHEN** 归档目录的 `verify-report.md`（经 `git show <base>:…` 读出）正文**描述性提及** `<!-- ship-gate: verify=PASS -->`（内联句 / 代码块内文档示例）但**无独占一行的真 PASS 锚**
- **THEN** `archived_verify_state` MUST 判其 verify 态为 `none`（非 `pass`），使归档终态短路 MUST NOT 输出假 SHIPPED——空壳 / 未验 / 仅描述性提及的归档目录 MUST 落 fail-safe（不 SHIPPED，请人工核验）；此判据 MUST 与 `anchors_in` 同为行级整行等值 + 忽略 fenced code block（同一 `_line_scoped_hits` 核心），MUST NOT 保留裸子串路径

#### Scenario: 未闭合 fence 隔断互斥锚对不判假通过〔gate-anchor-line-scoped OV-2·设计门 Q1=A〕
- **WHEN** 某报告的**互斥锚对**（verify `PASS`/`FAIL` 或 code-review `pass`/`blocked`）中正锚独占一行在 fenced code block 外、负锚独占一行落在**未闭合**（无配对收尾 ```）的 fence 内被吞
- **THEN** 行级锚检测核心 MUST 回报**未闭合信号**，互斥锚对消费方（`pick_exclusive` / `archived_verify_state`）遇未闭合信号 MUST **保守判定**（`pick_exclusive`→UNKNOWN 点名「未闭合 fence 隔断互斥锚」；`archived_verify_state`→`none` 不 SHIPPED），MUST NOT 因只见正锚而判 pass（否则从旧裸子串的 conflict 语义回归为危险假阳）；单锚判定（`anchors_in` 查 design-approved，无互斥对）不受此约束——未闭合吞唯一锚 = 空命中 = REFUSE_START，方向为安全侧假阴

#### Scenario: TG-02 条件步检测用声明式匹配非裸子串〔gate-anchor-line-scoped ADR-6·dogfood〕
- **WHEN** 某 change 的 proposal **描述性提及** `TG-02`（反引号代码引用 / 否定句 `TG-01/02/03 均不命中` / 散文讨论），但**未以声明式头注** `〔TG-02：…〕` 标注该触发（即该 change 非嵌入式、不该跑 embedded-test-sop）
- **THEN** gate 的 TG-02 条件步检测（`tg02_hit`）MUST 判**未命中** → step 5.5 输出 SKIP，MUST NOT 因子串命中正文对 TG-02 的**文档性提及/示例声明串**而误判 RUN_SOP（嵌入式 SOP）；检测 MUST 限定在 proposal **头部声明区**（文件开头→首个 `## ` 标题前）找 `〔TG-02`〔A3，dogfood 二轮：整体子串含加冒号仍被正文示例串假阳〕，真嵌入式 change 的头部 `〔TG-02：…〕` 声明仍 MUST 正确命中 → RUN_SOP；头部未用括号声明的（非常规）embedded proposal 漏检为安全侧假阴（ff 强制头注括号格式故实际不发生），记 Non-Goals

### Requirement: 模型档位映射（model-tiers）

模型档位定义、职责清单与 canonical 缺省 MUST 以 workflow bundle 规则文件 **`model-tiers.md`** 为单一真相源（经 resolver 全局解析；强档=verify/对抗裁决/final 终审；中档=领域镜/生成/实现；弱档=纯机械步；缺省 opus/sonnet/haiku）〔grill-amendment：推翻"config 段真相源 + SKILL 内联缺省×4"——多处 copy 漂移面〕；消费仓 `config.yaml` 的 `model-tiers` 段 MUST 仅作可选 per-repo **覆盖**；编排 skill（sdflow-ship/done/spec-review/code-review）的模型选择 MUST 以一句引用指向规则文件与覆盖段，MUST NOT 内联具体模型名（机队锚定，adr/0006(c)）。

#### Scenario: 消费仓无覆盖段用 canonical 缺省
- **WHEN** 消费仓 config.yaml 无 model-tiers 段，跑任一编排 skill
- **THEN** skill 按规则根 `model-tiers.md` 的 canonical 缺省档位运行，MUST NOT 报错、MUST NOT 静默降级门禁步模型

#### Scenario: verify 档位来自映射（覆盖优先）
- **WHEN** 消费仓 config.yaml model-tiers 段把强档覆盖为某模型
- **THEN** sdflow-done 的 verify 子代理按覆盖映射选模型；无覆盖时用规则文件强档缺省，MUST NOT 落到弱档

### Requirement: 跨模型 outside voice 默认开、失败回落且非阻塞
sdflow-spec-review 与 sdflow-code-review SHALL 默认启用跨模型 outside voice（codex/GPT 家族「找漏」第二意见）：sdflow-code-review 每次自带 code outside voice；sdflow-spec-review 复用 autoplan 产物中的 outside-voice findings（见反静默守卫 Requirement）。是否启用由环境决定——codex CLI 未安装即天然关停（工作流层不设软 off-switch，〔grill-amendment Q3〕）；codex 不可用（未装/未认证/报错/超时）时 MUST fallback 到同 prompt 的 fresh Claude 子代理；一切失败均为 informational，MUST NOT 阻塞评审流程。报告 outside-voice 留痕 MUST 使用模板写死的 v1 机器锚行（严格 KV、按调用位点复数化、guard/runner 正交）：`<!-- sdflow:outside-voice v1 site="…" guard="…" runner="codex|claude-fallback" reason_code="…" findings="N" truncated="…" -->`（确定性机判，不押自然语言；人类原因文本在锚行外）〔grill-amendment Q5 + spec-review-amendment 文法 v1〕；评审收尾步 MUST 机械自检锚行存在，缺失即报错〔spec-review-amendment〕。

#### Scenario: codex 就绪时跑跨模型 voice
- **WHEN** sdflow-code-review 运行且 codex preflight 返回 ready
- **THEN** 经共享 helper（`render-prompt` 同源拼接，exec 硬编码 `-s read-only --ephemeral`，最终消息经 `--output-last-message` 提取）调 codex（5min 封顶），findings 进合并池，锚行记 `runner="codex"`〔spec-review-amendment〕

#### Scenario: codex 不可用回落 Claude 子代理
- **WHEN** preflight 返回 not_installed
- **THEN** 以 `render-prompt` 输出的同一 prompt 派 fresh Claude 子代理兜底，评审继续不中断，锚行记 `runner="claude-fallback" reason_code="not-installed"`

#### Scenario: exec 超时与报错分别留痕〔spec-review-amendment：原合并场景拆分〕
- **WHEN** exec 超时（exit 124）或非零报错（exit 1，含 auth 失败，stderr 转发）
- **THEN** 分别以 `reason_code="timeout"` / `reason_code="exec-error"`（附 stderr 摘要于锚行外）回落子代理，两类可在报告中区分

#### Scenario: 无 codex 环境天然关停且留痕
- **WHEN** 运行环境未安装 codex CLI
- **THEN** preflight 返回 not_installed，回落 Claude 子代理并留痕，不存在需要另行关闭的软开关〔grill-amendment Q3〕

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
两评审 skill 的规划镜头步 SHALL 顺带判定：本变更命中的 TG 集合 ∩ HR-TG 子集 {TG-04, TG-06, TG-07, TG-08, TG-09, TG-16, TG-17, TG-26} 是否非空；非空则单开领域专属 cross-model（聚焦命中的高风险域，「找领域镜漏的」）。判定结果无论正反 MUST 写入报告（可审计）且 MUST 含 v1 机器锚行 `<!-- sdflow:hr-tg v1 hit="…|none" evidence="…" -->`，命中时 evidence 字段 MUST 给出判据触发点（哪处变更对应哪个 TG，30 秒可人工复核——判定本身是 prose 产物，无核验层则误判无人接住）〔grill-amendment Q5 + spec-review-amendment〕；HR-TG 子集清单以 trigger-catalog 为单一源，SKILL 只引用 ID。

#### Scenario: 命中 HR-TG 单开领域 cross-model
- **WHEN** 规划镜头判定命中 TG-08（外部依赖）
- **THEN** 单开一次领域 cross-model（codex，失败照常回落），报告记「命中 TG-08 → 已跑领域 cross-model」

#### Scenario: 未命中则不开且留痕
- **WHEN** 命中集 ∩ HR-TG = ∅
- **THEN** 不开领域 cross-model，报告记「HR-TG 判定：未命中」

### Requirement: outside-voice tension 不静默采纳

outside voice 与主审分歧（tension）SHALL 中立并陈、标 TENSION：sdflow-spec-review 写入报告决策登记区（选项 + 推荐 + 两方视角 + **三面后果（系统 / 用户 / 开发循环）+ 主次判定**，设计 HARD-GATE 人一次性拍板）；sdflow-code-review 按 T10 三级协议自动裁决（有客观判据自动裁 / 无则派对抗镜复核 / 复核不过或无从复核则 defer 进 buglist/todolist + hand-off）并**按三镜 + 主次记理由**，MUST NOT 以自评置信（"有把握"）为自动裁决唯一依据〔impl-review-fix F1/CV2：与 T10 三处 skill + 本需求 scenario 对齐，勿把已淘汰的「有把握」措辞焊回权威 spec〕。outside voice 的建议 MUST NOT 被静默自动采纳（不直接改代码/设计而不留痕）。**`runner=codex`** 的 outside-voice findings MUST NOT 经自评置信阈值（<80）预过滤——跨模型自评不可比、异见易被同族标尺误杀——一律直通对抗裁决，被裁掉的连理由落报告「已裁掉」区〔grill-amendment Q4〕；`runner=claude-fallback` 的 findings 属同族产物，照过同族置信滤（豁免理由对其不成立）〔spec-review-amendment〕。

#### Scenario: 设计侧分歧进决策登记区
- **WHEN** codex voice 与 spec-review 主审对同一设计点结论相反
- **THEN** 报告决策登记区新增 TENSION 条目（两方观点 + 推荐 + 三面后果 + 主次判定），不中途 AskUserQuestion

#### Scenario: 代码侧分歧自动裁决或 defer
- **WHEN** codex voice 与 code-review 主审分歧且裁决无客观判据
- **THEN** defer 进 issues 池并写入 hand-off，不静默采纳任一方

#### Scenario: 低自评置信的 codex finding 不被预筛
- **WHEN** 某条 `runner=codex` 的 finding 自评置信低于 Step3 阈值（<80）
- **THEN** 该条仍进入对抗裁决（不被置信滤拦截）；若裁决不成立，连理由落报告「已裁掉」区

#### Scenario: fallback finding 照过同族滤〔spec-review-amendment〕
- **WHEN** 某条 `runner=claude-fallback` 的 finding 自评置信低于阈值
- **THEN** 按同族 findings 常规处理（过滤规则一致），不享受跨模型豁免

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

### Requirement: 总览表 row 字段 table-cell-safe（写时 reject 守盘面完整性）

issues 池 recorder（`buglist.py` / `todolist.py` / `issues.py`）以 markdown 表存状态总览（「盘面即状态」的盘面），其行按 `|` 切列。recorder SHALL 保证：**任何把字段写入总览管道表 row 的写路径**，字段含 ASCII `|` **或**换行（会致列错位 / 整行截断而腐蚀盘面）时 MUST 拒绝写入（`_die` 报清晰错误，复用既有 priority/status 非法即拒的写时校验惯例），MUST NOT 静默转义或替换。**写路径须全覆盖**〔spec-review-amendment C1〕：不止 `add`——`triage`（写 batch 列）、`rename`（retag 成员的 new_key 列）同样把字段写进管道表，MUST 一并守；`batch add` 写的 `batches.md` batch key MUST 同样拒 `|`/换行（防含腐蚀字符的 key 经 triage/retag 流入管道表）。校验 MUST 施于**各命令入口的原始用户参数**，MUST NOT 施于行拼接 sink（`" | ".join(cells)` 在 split 之后、`|` 已被切走，挂 sink 永不触发 = 假覆盖）。详细块 prose 字段（现象/根因/修复）不受此约束（非 `|` 分隔）；但块专用 `title` 进块头 `## id: title`，其**换行**MUST 一并守（防块头孤儿行）〔C7〕。**batch key 是 slug〔spec-review-amendment OV-2〕**：`batches.md` header `### {key} — {title}` 用 ` — ` 作分隔，故 batch key MUST 过 slug 校验（拒 `|`、换行、` — `、首尾空白），施于 `batch add`/`triage --批次`/`rename new_key` 三处。**自定义 `id`〔OV-3〕**：显式传入的 `id` MUST 符合 ID 语法（`ID_RE`）且不与既有 ID 重复（`parse_table_rows` 按 ID 建 dict、重复即静默丢行），否则 `_die`；`scan` MUST 报告同池重复 ID。此为写时 fail-closed 守卫，非事后解析补救。

#### Scenario: 字段含 `|` 或换行被写时拒绝

- **WHEN** 记录或回写一条 item，其 `summary` / `module` / `change` / batch key 含 ASCII `|` 或换行
- **THEN** recorder 以清晰错误拒绝写入（`_die`），不产生任何列错位 / 行截断的腐蚀盘面，并提示改写

#### Scenario: triage / rename 写路径同样被守（非只 add）

- **WHEN** `triage` 给 item 打一个含 `|`/换行 的批次名，或 `rename` 把批次改成含 `|`/换行 的 new_key
- **THEN** recorder 在这两条写路径同样 `_die` 拒绝（不只 `add`），管道表 `cells[7]` 不被腐蚀

#### Scenario: 详细块 prose 不受 table-cell-safe 约束

- **WHEN** 一条 item 的详细块字段（现象 / 根因 / 修复等 prose）含 `|` 或换行
- **THEN** 正常写入（详细块非 `|` 分隔表、无腐蚀风险），不被拒绝

### Requirement: reindex 一致性问题可观测且不阻断重建

`issues.py reindex` SHALL 把子进程 `scan` 报出的表↔块一致性 problems **回显到 stderr**（逐条带 pool / 文件定位），使独立跑 reindex 时的不一致对用户可见（兑现 D5 承诺）。**默认**：problems 非空 MUST NOT 使 reindex 失败——INDEX SHALL 照常确定性重建、退出码为 0（不因一个坏块阻断整池刷新）。reindex SHALL 提供 **`--strict`** 选项：problems 非空时以**非 0 退出码**结束，供非交互调用 / 收尾门做 enforcement——防非交互场景（sweep / hook / CI）stderr 被吞 + 默认 exit 0 致一致性问题**静默蒸发**（反静默元原则）。**致命错误**（无法读取文件等）无论是否 `--strict` 仍以非 0 退出（与一致性警示分层）。**读侧盘面完整性〔spec-review-amendment OV-1〕**：`scan` MUST 校验总览行 arity（当前 8 列 / 旧格式 7 列之外一律入 `problems`）——否则无块坏行的列错位腐蚀不进 `problems`、reindex 回显与 `--strict` 皆抓不到（T2 写侧防之外须有读侧检测，二者合成完整盘面完整性）。

#### Scenario: problems 回显 stderr 但不阻断 INDEX 重建

- **WHEN** 池中某 dated 文件存在表↔块不一致，运行 `issues.py reindex`
- **THEN** 每条 problem 逐条出现在 stderr（含 pool / 文件定位），INDEX 仍被完整重建，退出码为 0

#### Scenario: 独立跑 reindex 时不一致不再静默

- **WHEN** 不经 `scan`、直接运行 `reindex`，且池中存在表↔块不一致项
- **THEN** 用户从 stderr 看到具体不一致项（而非静默重建、不一致被吞）

#### Scenario: --strict 下 problems 非空即非 0 退出

- **WHEN** 以 `reindex --strict` 运行且池中存在表↔块不一致项
- **THEN** problems 回显 stderr 后以**非 0 退出码**结束（供非交互 / 收尾门 enforcement）；同一不一致下默认（无 `--strict`）仍 exit 0、INDEX 照常重建

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

