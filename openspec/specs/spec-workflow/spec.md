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

评审编排器 SHALL 把决策点（自动决策与需人拍板）连同选项、推荐、各分支后果登记进评审报告，MUST NOT 在评审中途以 `AskUserQuestion` 打断，使一遍评审能自主跑到完成。

#### Scenario: sdflow-spec-review 遇到 ≥2 合理方案
- **WHEN** 某评审镜发现一个有 ≥2 合理方案或核验不了的事实的决策点
- **THEN** 编排器把它写入 spec-review-report.md 决策登记区并继续，不中途弹 AskUserQuestion

### Requirement: 阶段二产出单一合并报告

阶段二 SHALL 由 `sdflow-spec-review` 编排器串起 autoplan 与多镜评审并产出**单一** `spec-review-report.md`，MUST NOT 要求人工手动合并多份报告。**执行序 MUST 串行**〔T20〕：Step2 多镜 fan-out MUST 待 Step1 autoplan 完成并 checkpoint 之后启动，MUST NOT 与 Step1 并行——多镜的评审对象须包含 autoplan 的 `[gstack-amendment]` 改动；若历史运行已并行，Step3 裁决 MUST 对 autoplan amendment 做增量核对并在报告注明。

#### Scenario: 阶段二收尾
- **WHEN** autoplan 与 spec-review 镜均完成
- **THEN** 编排器输出一份已去重合并、含决策登记区的 spec-review-report.md，供设计 HARD-GATE 人工一次性评审

#### Scenario: 多镜等待 autoplan 先行
- **WHEN** sdflow-spec-review 执行 Step2 规划镜头时 Step1 autoplan 尚未 checkpoint
- **THEN** MUST 等待其完成后再 fan-out；MUST NOT 以"求快"并行化（评审对象缺 amendment = 丢失复审性质）

### Requirement: sdflow-code-review 为每次全跑的独立强制主审

阶段三的 `sdflow-code-review` MUST 每次全跑、以独立冷视角作为强制代码评审主审（依据实测能抓真问题），SHALL NOT 因 subagent-dev 内部已评审而降级为高风险才跑的残差抽查。

#### Scenario: 普通变更也跑 sdflow-code-review
- **WHEN** 一个非高风险变更完成实现
- **THEN** sdflow-code-review 编排器仍全跑（领域镜+对抗镜+历史镜+置信过滤+scope-drift），产出 code-review-report.md

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
- **review UI 机械**（`tools/` + `serve.sh` + `review.html`）SHALL 仍复制进消费仓 `openspec/`（服务器根=openspec/ 约束逼留，尽量少）。
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

`sdflow-ship` 的步序推进 MUST 由确定性脚本 `ship_gate.py` 判定（**盘面即状态**：以 change 目录产物存在性与结论行为账本，MUST NOT 设可变 state 文件造第二真相源）；编排 skill MUST 在每步前后调用 gate 并遵其判定，MUST NOT 以 prose 记忆步序。gate MUST 只读（零副作用）、双输出（首行人读摘要 + JSON 机读）、以退出码承载门禁语义（0=可推进 / 3=拒绝起跑 / 4=上游 blocker / 5=verify FAIL / **6=UNKNOWN 判定不能**〔spec-review-amendment〕）；同一报告并存冲突锚行 MUST 判 UNKNOWN 点名冲突行，MUST NOT 猜优先级。机判锚点 MUST 为**模板写死的机器注释行**〔grill-amendment：自然语言结论行正则对真实存档全 miss，禁作锚点〕：设计门拍板 = `<!-- ship-gate: design-approved -->`；verify 结论 = `<!-- ship-gate: verify=PASS -->` / `verify=FAIL`；code-review 放行 = `<!-- ship-gate: code-review=pass -->` / `=blocked`。三个报告的生成模板（sdflow-spec-review 拍板回写约定 / sdflow-done verify 模板 / sdflow-code-review 报告格式）MUST 输出对应锚行；gate 以字面查找（非正则）解析，锚行集合在脚本头注释与各模板双向钉死同 change 演进。

#### Scenario: 未过设计门拒绝起跑
- **WHEN** 对一个 spec-review-report.md 缺失或不含「设计门拍板」标记的 change 调用 /sdflow-ship
- **THEN** ship_gate 退出码 3（REFUSE_START），skill 停止并提示先完成设计门，MUST NOT 起跑任何阶段三步骤

#### Scenario: verify FAIL 停并上抛
- **WHEN** 链行进至 sdflow-done 后 verify-report.md 结论为 FAIL
- **THEN** gate 退出码 5，ship 停止、原样上抛缺口清单，MUST NOT 继续 archive/merge（任何一层评审覆盖不得无声蒸发）

#### Scenario: 前置产物缺失点名
- **WHEN** 某步产物缺失（如 code-review-report.md 不在）
- **THEN** gate 输出 next=对应 skill 与 missing 清单，编排按此推进；实现完成判据 MUST 以 **git 历史 checkpoint 任务标签为主锚**（plan 任务数 N 对 `checkpoint(task<k>-` 去重任务号集，齐 N 判完成〔grill-amendment〕；**收集窗口 MUST 为含 superpowers-plan.md 首次提交自身的闭区间 `[sha, HEAD]`**——即 `git log <sha>..HEAD --no-merges` 加对 `<sha>` 自身 commit subject 的同规则解析；plan 与首个 task 锚同 commit（checkpoint `add -A` 携带未提交 plan 的合法盘面）时该 task MUST 计入，MUST NOT 漏数〔B1 修复，替换旧排他窗口表述〕；MUST NOT 全历史扫描——main 遗留标签会造成假齐 N〔spec-review-amendment 设计门拍板 Q2〕；plan 标题命中 0 → UNKNOWN）、plan 复选框全勾为辅，两通道皆不可判时 gate 判 UNKNOWN 停上抛，MUST NOT 猜测推进、MUST NOT 以 gitignored 的 SDD ledger 为判据

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
outside voice 与主审分歧（tension）SHALL 中立并陈、标 TENSION：sdflow-spec-review 写入报告决策登记区（选项 + 推荐 + 两方视角，设计 HARD-GATE 人一次性拍板）；sdflow-code-review 有把握则自动裁决并记理由、拿不准则 defer 进 buglist/todolist + hand-off。outside voice 的建议 MUST NOT 被静默自动采纳（不直接改代码/设计而不留痕）。**`runner=codex`** 的 outside-voice findings MUST NOT 经自评置信阈值（<80）预过滤——跨模型自评不可比、异见易被同族标尺误杀——一律直通对抗裁决，被裁掉的连理由落报告「已裁掉」区〔grill-amendment Q4〕；`runner=claude-fallback` 的 findings 属同族产物，照过同族置信滤（豁免理由对其不成立）〔spec-review-amendment〕。

#### Scenario: 设计侧分歧进决策登记区
- **WHEN** codex voice 与 spec-review 主审对同一设计点结论相反
- **THEN** 报告决策登记区新增 TENSION 条目（两方观点 + 推荐 + 后果），不中途 AskUserQuestion

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

