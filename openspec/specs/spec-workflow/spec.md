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

阶段二 SHALL 由 `sdflow-spec-review` 编排器串起 autoplan 与 sdflow-spec-review 并产出**单一** `spec-review-report.md`，MUST NOT 要求人工手动合并多份报告。

#### Scenario: 阶段二收尾
- **WHEN** autoplan 与 sdflow-spec-review 镜均完成
- **THEN** 编排器输出一份已去重合并、含决策登记区的 spec-review-report.md，供设计 HARD-GATE 人工一次性评审

### Requirement: sdflow-code-review 为每次全跑的独立强制主审

阶段三的 `sdflow-code-review` MUST 每次全跑、以独立冷视角作为强制代码评审主审（依据实测能抓真问题），SHALL NOT 因 subagent-dev 内部已评审而降级为高风险才跑的残差抽查。

#### Scenario: 普通变更也跑 sdflow-code-review
- **WHEN** 一个非高风险变更完成实现
- **THEN** sdflow-code-review 编排器仍全跑（领域镜+对抗镜+历史镜+置信过滤+scope-drift），产出 code-review-report.md

### Requirement: 阶段三过设计门后连续自动跑到 merge

阶段三 SHALL 在阶段二设计门之后无任何阻塞人类门地连续运行 `writing-plans → subagent-dev → sdflow-code-review → sdflow-done`；能修的自动修，修不了或需拍板的 MUST 进 buglist/todolist 延后并由 hand-off 引导另开 change 清理。

#### Scenario: 修不了的问题延后而非阻塞
- **WHEN** sdflow-code-review 发现一个本 change 修不掉的问题
- **THEN** 它进 buglist/todolist(defer) 并写入 hand-off，流程继续跑到 sdflow-done，不设人类门阻塞

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

