## RENAMED Requirements

- FROM: `### Requirement: 规则全局解析 resolver（本地优先 → 全局兜底 → 显式降级）`
- TO: `### Requirement: 规则全局解析 resolver（全局 canonical → 显式降级）`
- FROM: `### Requirement: 存量消费仓迁移不自动删、陈旧遮蔽须告警`
- TO: `### Requirement: 存量消费仓迁移不自动删、残留副本须告警`

## MODIFIED Requirements

### Requirement: 规则全局解析 resolver（全局 canonical → 显式降级）

skills（sdflow-spec-review / sdflow-code-review / sdflow-done / sdflow-buglist·todolist·issues / opsx-ship）读取 workflow 规则与 review 机械层脚本 MUST 走统一 resolver，其链路 SHALL 为**两步**：① 全局 canonical bundle；② 全局不可达/不完整 → **显式降级**通用评审并告警，MUST NOT 静默当"无此层"。

**MUST NOT 存在「仓内规则副本优先」这一步。** 在未显式设置 `SDFLOW_HOME` 覆盖的前提下〔F42〕，仓内 `openspec/workflow/` 下无论有无规则文件本体（`workflow.md` / `spec-checklists/` / `code-checklists/`）或 `tools/`，**都 MUST NOT 影响解析结果**——规则与工具是全局单份共享资源，消费仓副本对评审无生效路径（理由见 `adr/0039`：本地副本是 bundle 拷贝链 skew 的成因，取消它即消灭该类问题；`~/.sdflow/hack/` 拷贝链与 Windows SKILL 快照的失鲜面不在本条范围）。MUST NOT 通过恢复仓内副本优先来达成任何目的（含版本冻结）；本 spec **不提供「规则版本冻结」能力承诺**〔设计门 Q4〕——`SDFLOW_HOME` 保持其既有「测试隔离重定向」契约（见下），操作者自设该 env 属环境行为、自担后果。

步①的 canonical 解析 MUST 平台无关回落：先试 `~/.sdflow/workflow/`（Unix 软链目录，透明），否则读 `~/.sdflow/workflow-path`（Windows 指针文件）取 bundle 路径。步②的"显式降级 + 告警"即 CONTEXT 术语『反静默守卫』的缺失面（见 `adr/0003`）。

〔model-baseline-amendment / `adr/0006`〕上述链路 MUST 由确定性脚本 **`~/.sdflow/hack/resolve-workflow.sh`** 实现（stdout = 规则根路径；全局缺失 → 非零退出 + stderr 固定告警文案）。skills MUST 通过调用该脚本解析规则路径，MUST NOT 把链路作为指令文本交由执行模型逐步照做（执行机队 = opus/sonnet/gpt-5.5 机队锚定，prose 协议在弱档模型上的失效形态 = 静默跳步）；调用方 MUST NOT 静默吞脚本非零退出码。

〔spec-review-amendment〕契约补强：脚本 MUST 支持 `--root <仓根>`（缺省 `git rev-parse --show-toplevel`）与 `${SDFLOW_HOME:-$HOME/.sdflow}` 环境覆盖（**测试隔离契约**，`resolve-workflow.sh:8` 既有语义不变；非面向使用者的版本冻结承诺）；步① 命中后 MUST 做最小健全性检查（`workflow.md` 非空 + `spec-checklists/`、`code-checklists/` 两个清单目录均非空，`sane()` 判据，不过检按缺失处理）；调用方 MUST 先以 `[ -x ]` 判脚本自身存在——脚本缺失（未跑 setup）与步② bundle 缺失是**两个不同告警**，MUST NOT 混同。

〔impl-review-fix / 935eb42〕退出码与入参校验契约（**码位集不变，不新增码位**）：脚本 MUST 用 **exit 64** 标记用法错误——`--root` 缺值、`--root` 后紧跟形如 `-*` 的疑似 flag 值、未知参数，以及**默认 cwd 解析失败**（`git rev-parse --show-toplevel` 与 `pwd` 均失败，如 cwd 已被删除）且未显式传 `--root` 兜底的场景；MUST 用 **exit 2** 标记全局 bundle 不可达/不完整（步②降级）；MUST 用 **exit 0** 标记解析成功（此后**唯一**成功来源 = 全局 canonical）。`SDFLOW_HOME` MUST 校验为绝对路径，非绝对路径 MUST 告警并忽略该值（不参与解析，直接判全局不可达），MUST NOT 静默当相对路径拼接使用。

#### Scenario: 一切消费仓一律走全局 canonical
- **WHEN** 任一消费仓的 skill 要读 `workflow.md` 或调 `$RULES_ROOT/tools/anchor_lint.py`
- **THEN** resolver 直接解析全局 canonical bundle（`~/.sdflow/workflow/` 或 `workflow-path` 指针），stdout 为该路径；跟随运行 checkout 的 released HEAD

#### Scenario: 仓内残留规则副本不再影响解析
- **WHEN** 某存量消费仓 `openspec/workflow/` 下仍有全套规则副本（`workflow.md` + `spec-checklists/` + `code-checklists/`）与旧 `tools/`
- **THEN** resolver **忽略它们**，仍解析到全局 canonical；MUST NOT 因仓内有副本而返回仓内路径。该仓的评审此后使用全局规则与全局 tools

#### Scenario: SDFLOW_HOME 重定向保持测试隔离契约
- **WHEN** 测试（或知情操作者）设 `SDFLOW_HOME=<自备目录>`（其下含 `workflow/` 或 `workflow-path`）
- **THEN** resolver 从该处解析并同样过 `sane()`（既有测试隔离契约原样保留，开发期测试三层第 2 层依赖此路径）；这不构成「版本冻结」的规范承诺——需要不随全局翻动的规则集属操作者自担行为，且 MUST NOT 通过在仓内放规则副本达成该目的

#### Scenario: 全局缺失显式降级不静默
- **WHEN** 全局 canonical bundle 不可达
- **THEN** skill MUST 降级为通用评审并**显式告警**缺失，MUST NOT 静默当作"本项目无此评审层"

#### Scenario: canonical 解析平台回落
- **WHEN** skill 在 Windows 上解析全局 bundle（平台无软链）
- **THEN** 先试 `~/.sdflow/workflow/` 目录未果 → 回落读 `~/.sdflow/workflow-path` 指针取 bundle 路径；Unix 上则 `~/.sdflow/workflow/` 软链目录直接命中（透明）；平台判断发生在 `resolve-workflow.sh` 内，skill 不判平台

#### Scenario: resolver 由脚本执行而非模型 prose
- **WHEN** 任一 skill 在任一执行模型（opus / sonnet / gpt-5.5 等）上需要解析规则路径
- **THEN** 它调用 `~/.sdflow/hack/resolve-workflow.sh` 并使用其 stdout 路径；脚本非零退出时 skill 显式降级并转发脚本告警文案，不自行在指令内重实现链路

#### Scenario: cwd 已被删除且未传 --root
- **WHEN** 调用方在一个已被删除的工作目录下调用脚本、且未显式传 `--root`
- **THEN** `git rev-parse --show-toplevel` 与 `pwd` 均解析失败，脚本以 **exit 64** 报用法错误并提示改用 `--root` 显式指定，MUST NOT 静默回退到某个猜测路径

#### Scenario: --root 后紧跟疑似 flag 值
- **WHEN** 调用方写成 `resolve-workflow.sh --root --explain`（漏填 `--root` 的值，误把下一个 flag 当值）
- **THEN** 脚本识别 `-*` 形态并以 **exit 64** 拒绝，MUST NOT 把 `--explain` 当路径字符串误吞

#### Scenario: SDFLOW_HOME 非绝对路径
- **WHEN** 环境变量 `SDFLOW_HOME` 被设为相对路径（如 `.sdflow`）
- **THEN** 脚本告警并忽略该值、直接判全局 canonical 不可达（落步②显式降级），MUST NOT 拿相对路径去拼目录再静默探测

### Requirement: workflow bundle 改在权威源、经部署下发

workflow bundle（`workflow/*.md` / `trigger-catalog.md` / `spec-checklists/` / `code-checklists/` / review 机械层脚本（`tools/`）/ hooks / checkpoint 脚本）与自制 skill 的改动 MUST 在权威源（sdflow-skills 的 bundle 公共家与 skill 目录）进行，MUST NOT 只改消费仓副本。部署 SHALL **按内容性质分层**，而非整 bundle 复制：

- **规则**（`workflow/*.md` + `spec-checklists/` + `code-checklists/`）MUST **不再复制进消费仓**，改由 skills 从全局 canonical bundle 解析（见「规则解析 resolver」需求）。
- **review 机械层脚本**（`tools/` 下 `anchor_lint.py` / `lens_metric_emit.py` / `outside_voice_guard.py` / `hr_tg_intersect.py` / `review_disposition_check.py` / `trivial_shape.py` 等确定性脚本）MUST **不再复制进消费仓**，与规则同样由 skills 从全局 canonical bundle 解析（`$RULES_ROOT/tools/…`）。理由〔F49 限定〕：消费仓副本是 **bundle 拷贝链** skew 的成因（当前已知的主要 skew 来源），且它在 `global-canonical` 路径下从不被读取；取消复制即消灭**该类**问题（见 `adr/0039`）——该消除在完整 `git pull` + `bash setup.sh` 之后生效，不消灭 `~/.sdflow/hack/` 拷贝链与 Windows SKILL 快照的失鲜。`tools/` 下同样 MUST NOT 含任何 HTML 文档查看器资产（`engine.js` / `engine.css` / `vendor/` / `review-stub.html`）。**不再提供任何浏览器文档查看面**——`serve.sh` / `review.html` 及其查看器已从权威源整体移除；浏览 change / spec / roadmap 直接读 Markdown 文件。
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

### Requirement: 存量消费仓迁移不自动删、残留副本须告警

`sdflow-init update` 对存量消费仓的规则副本与 `tools/` 副本 MUST 改为"停止复制"，MUST NOT 自动删除仓内既有文件（安全红线 + 免分辨源/消费仓 + 老仓平滑迁移）。当检测到仓内残留的旧规则文件或旧 `tools/` 时，`sdflow-init` MUST **显式告警**，MUST NOT 静默留着。

**告警文案 SHALL 陈述带前置条件的死件语义而非「遮蔽全局」**〔F3：MUST NOT 用无条件绝对断言〕——resolver 取消仓内优先后（见「规则全局解析 resolver」需求），残留副本对评审不再有生效路径；但该表述 SHALL 带前置条件（「若刚 `git pull` 还没跑 `bash setup.sh`，先跑 setup 再判断」——部署窗口内旧 resolver 的步①仍在，副本仍生效）。文案 SHALL 明确：删 = 清理死件（推荐），并**附可直接复制的删除命令**（如 `rm -rf openspec/workflow/tools openspec/workflow/lens-metric-contract.md` + 告警列出的规则文件）/ 留 = 无害但无用；MUST NOT 沿用"留 = 显式 pin"的旧表述（pin 语义已取消，该表述会让用户以为副本仍在生效）。存量死件清理由人执行该命令完成，MUST NOT 新增一次性自动清删代码〔设计门 Q2〕。**检测判据 SHALL 扩员**：原 `RULE_MARKERS` 三项之外 SHALL 同时检测残留 `tools/` 目录与 `lens-metric-contract.md`（二者停铺后同为死件，只报规则本体会漏掉最大块的残留）。此告警即 CONTEXT 术语『反静默守卫』的**残留死件**变体（见 `adr/0003`、`adr/0039`）。

〔spec-review-amendment / impl-review-fix 935eb42〕告警触发点 = **`init` 与 `update` 两种模式均内联检测**（同一判据函数：新项目 fresh init 自然零残留、零告警；老仓被误当新项目跑 `init` 时也不因模式不同而假绿放过残留）+ **`sdflow-maintain` 兜底扫描**（覆盖常年不跑 `init`/`update` 的仓）；检测范围 MUST 同时覆盖旧版仓内 `hack/checkpoint-commit.sh` **孤儿副本**（checkpoint 全局化后不再被任何机制刷新），并给对称提示。

#### Scenario: update 不删残留、给出死件告警
- **WHEN** 一个 pre-change 的存量消费仓（有规则副本与 `tools/`）跑 `update`
- **THEN** update 只铺 `WORKFLOW-GUIDE.md`、保留旧文件不删，并告警"这些副本对评审已无生效路径（若刚 `git pull` 还没跑 `bash setup.sh`，先跑 setup 再判断），删=清理死件（附可复制命令）/ 留=无害但无用"；告警 SHALL 同时列出残留的 `tools/` 与 `lens-metric-contract.md`（判据扩员）；MUST NOT 输出"留=显式 pin"、MUST NOT 输出无前置条件的"已无任何生效路径"

#### Scenario: 老仓被误当新项目跑 init 同样告警
- **WHEN** 一个已有陈旧残留的存量仓被误跑了 `init`（而非 `update`）
- **THEN** 残留检测同样触发（判据与 `update` 共用），MUST NOT 因跑的是 `init` 模式而假绿放过残留（B2-F3）

#### Scenario: 留旧副本不再改变评审行为
- **WHEN** 用户读到告警后选择保留本地规则副本
- **THEN** 该仓评审**仍使用全局规则与全局 tools**（resolver 无仓内优先步），保留副本既不改变行为也不带来风险；MUST NOT 因副本存在而回到旧的本地解析路径

### Requirement: 评审报告锚自检由确定性脚本判定

spec-review Step3 / code-review Step5 的**评审报告锚自检**（四类 v1 锚存在性 + `sdflow:lens-metric` 字段/枚举/子格式合法性）MUST 由确定性脚本 `anchor_lint` 判定，MUST NOT 作为 prose 协议交执行模型手 grep + 肉眼核枚举（与 `resolve-workflow.sh`、`ship_gate.py`、`trivial_shape.py` 同族——机械协议脚本化，adr/0006）。脚本 MUST 只读、双输出（human 行 + JSON 机读）、以退出码承载判定（0=干净 / 非零=违规或脚本自身错误）；编排 SKILL MUST 调该脚本并遵其退出码，MUST NOT 静默吞非零退出。

脚本 MUST 校验：①四类锚存在性——`sdflow:outside-voice`、`sdflow:hr-tg`、`sdflow:step1-broad-review` 恒须存在，`sdflow:lens-metric` 受 `config.yaml metrics.enabled` 门控（关闭或 config 未配置 metrics 时缺此类 MUST NOT 阻塞；config 存在且 `metrics:` 块在但值非法 → fail-closed，见下 Scenario）；metrics 启用时 lens-metric 不止「≥1 条」——`lens="broad"` 与 `lens="outside-voice"` 各 MUST 至少一行（两者恒跑），缺即违规；其余 per-lens 完整性属主 session 信任边界。②`sdflow:lens-metric` 锚的字段校验——`layer`/`lens`/`runner` 枚举域、`sev` 子格式（`致N/高N/中N/低N`）、且 `layer` MUST 等于 CLI `--layer`（防错层度量锚漏网）、五计数字段 `findings`/`采纳`/`裁掉`/`defer`/`独立` MUST 为十进制非负整数。枚举取值域 MUST 从 `lens-metric-contract.md` 的 `lens-metric-enums` 机读块单一权威源读取而 MUST NOT 在脚本内复制清单。脚本 MUST 沿用 fence-aware 行级纪律（跳 fenced code block、锚独占行前缀匹配、受限 kv 解析），在脚本内重实现该纪律（与 `lens_metric_aggregate` 平行、同纪律、MUST NOT 跨 skill import）而 MUST NOT 用 `ship_gate` 的定长整行原语（匹配不了变长度量锚）。契约 `lens-metric-enums` 机读块 SHALL 为 layer/lens/runner/sev 的机读单一源，任何消费该枚举者（`anchor_lint` 运行时读、`lens_metric_aggregate` 硬编码）MUST NOT 与之漂移，一致性 SHALL 由测试守卫。**契约机读块与消费它的 `tools/` 脚本同驻全局 canonical bundle**〔本 change：取消消费仓部署后无「下发」动作〕——二者的同代性由单一运行 checkout 的文件树保证（`git pull` 一次同时变），MUST NOT 再以「同批部署下发」为同代性机制；「新脚本 + 旧契约无块」的错配形态随消费仓副本取消而不可达。

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
- **THEN** 脚本 SHALL 非零退出并点名缺失 lens——metrics 启用时这两行为最小必有行；其余 per-lens（domain/adversarial/grounding/history）完整性 SHALL 属主 session 信任边界、脚本不强制（报告机读不出「本轮跑了哪些镜」）

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

#### Scenario: 数值一致性诚实声明为信任边界

- **WHEN** 某 `sdflow:lens-metric` 锚的 `findings=N` 与该镜合并池实收数不符
- **THEN** 脚本 SHALL NOT 声称能检出该不一致（`findings=N` vs 实收数属主 session 信任边界、非机械可验）；SKILL 自检步 SHALL 保留「数值一致性是主 session 职责、脚本不谎称机验」的诚实声明，MUST NOT 因接了脚本而删除该边界声明

