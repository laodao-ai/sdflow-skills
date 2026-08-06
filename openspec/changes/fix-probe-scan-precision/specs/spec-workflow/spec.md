## RENAMED Requirements

- FROM: `### Requirement: 规则全局解析 resolver（本地优先 → 全局兜底 → 显式降级）`
- TO: `### Requirement: 规则全局解析 resolver（全局 canonical → 显式降级）`
- FROM: `### Requirement: 存量消费仓迁移不自动删、陈旧遮蔽须告警`
- TO: `### Requirement: 存量消费仓迁移不自动删、残留副本须告警`

## MODIFIED Requirements

### Requirement: 规则全局解析 resolver（全局 canonical → 显式降级）

skills（sdflow-spec-review / sdflow-code-review / sdflow-done / sdflow-buglist·todolist·issues / opsx-ship）读取 workflow 规则与 review 机械层脚本 MUST 走统一 resolver，其链路 SHALL 为**两步**：① 全局 canonical bundle；② 全局不可达/不完整 → **显式降级**通用评审并告警，MUST NOT 静默当"无此层"。

**MUST NOT 存在「仓内规则副本优先」这一步。** 仓内 `openspec/workflow/` 下无论有无规则文件本体（`workflow.md` / `spec-checklists/` / `code-checklists/`）或 `tools/`，**都 MUST NOT 影响解析结果**——规则与工具是全局单份共享资源，消费仓副本无任何生效路径（理由见 `adr/0039`：本地副本是分发链错位（skew）的唯一成因，取消它即消灭该类问题）。需要冻结规则版本的场景 SHALL 改用 `SDFLOW_HOME` 指向自备 canonical，MUST NOT 恢复仓内副本优先。

步①的 canonical 解析 MUST 平台无关回落：先试 `~/.sdflow/workflow/`（Unix 软链目录，透明），否则读 `~/.sdflow/workflow-path`（Windows 指针文件）取 bundle 路径。步②的"显式降级 + 告警"即 CONTEXT 术语『反静默守卫』的缺失面（见 `adr/0003`）。

〔model-baseline-amendment / `adr/0006`〕上述链路 MUST 由确定性脚本 **`~/.sdflow/hack/resolve-workflow.sh`** 实现（stdout = 规则根路径；全局缺失 → 非零退出 + stderr 固定告警文案）。skills MUST 通过调用该脚本解析规则路径，MUST NOT 把链路作为指令文本交由执行模型逐步照做（执行机队 = opus/sonnet/gpt-5.5 机队锚定，prose 协议在弱档模型上的失效形态 = 静默跳步）；调用方 MUST NOT 静默吞脚本非零退出码。

〔spec-review-amendment〕契约补强：脚本 MUST 支持 `--root <仓根>`（缺省 `git rev-parse --show-toplevel`）与 `${SDFLOW_HOME:-$HOME/.sdflow}` 环境覆盖（测试隔离，且为规则版本冻结的唯一受支持路径）；步① 命中后 MUST 做最小健全性检查（`workflow.md` 非空 + `spec-checklists/`、`code-checklists/` 两个清单目录均非空，`sane()` 判据，不过检按缺失处理）；调用方 MUST 先以 `[ -x ]` 判脚本自身存在——脚本缺失（未跑 setup）与步② bundle 缺失是**两个不同告警**，MUST NOT 混同。

〔impl-review-fix / 935eb42〕退出码与入参校验契约（**码位集不变，不新增码位**）：脚本 MUST 用 **exit 64** 标记用法错误——`--root` 缺值、`--root` 后紧跟形如 `-*` 的疑似 flag 值、未知参数，以及**默认 cwd 解析失败**（`git rev-parse --show-toplevel` 与 `pwd` 均失败，如 cwd 已被删除）且未显式传 `--root` 兜底的场景；MUST 用 **exit 2** 标记全局 bundle 不可达/不完整（步②降级）；MUST 用 **exit 0** 标记解析成功（此后**唯一**成功来源 = 全局 canonical）。`SDFLOW_HOME` MUST 校验为绝对路径，非绝对路径 MUST 告警并忽略该值（不参与解析，直接判全局不可达），MUST NOT 静默当相对路径拼接使用。

#### Scenario: 一切消费仓一律走全局 canonical
- **WHEN** 任一消费仓的 skill 要读 `workflow.md` 或调 `$RULES_ROOT/tools/anchor_lint.py`
- **THEN** resolver 直接解析全局 canonical bundle（`~/.sdflow/workflow/` 或 `workflow-path` 指针），stdout 为该路径；跟随运行 checkout 的 released HEAD

#### Scenario: 仓内残留规则副本不再影响解析
- **WHEN** 某存量消费仓 `openspec/workflow/` 下仍有全套规则副本（`workflow.md` + `spec-checklists/` + `code-checklists/`）与旧 `tools/`
- **THEN** resolver **忽略它们**，仍解析到全局 canonical；MUST NOT 因仓内有副本而返回仓内路径。该仓的评审此后使用全局规则与全局 tools

#### Scenario: 需要冻结规则版本改用 SDFLOW_HOME
- **WHEN** 某仓或某次测试需要一份不随全局翻动的规则集
- **THEN** 调用方设 `SDFLOW_HOME=<自备目录>`（其下含 `workflow/` 或 `workflow-path`），resolver 从该处解析并同样过 `sane()`；MUST NOT 通过在仓内放规则副本达成该目的

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
- **review 机械层脚本**（`tools/` 下 `anchor_lint.py` / `lens_metric_emit.py` / `outside_voice_guard.py` / `hr_tg_intersect.py` / `review_disposition_check.py` / `trivial_shape.py` 等确定性脚本）MUST **不再复制进消费仓**，与规则同样由 skills 从全局 canonical bundle 解析（`$RULES_ROOT/tools/…`）。理由：消费仓副本是 skew 的**唯一**成因，而它在 `global-canonical` 路径下从不被读取；取消复制即消灭该类问题（见 `adr/0039`）。`tools/` 下同样 MUST NOT 含任何 HTML 文档查看器资产（`engine.js` / `engine.css` / `vendor/` / `review-stub.html`）。**不再提供任何浏览器文档查看面**——`serve.sh` / `review.html` 及其查看器已从权威源整体移除；浏览 change / spec / roadmap 直接读 Markdown 文件。
- **人读手册 `WORKFLOW-GUIDE.md`** SHALL 仍复制进消费仓 `openspec/workflow/`——它**纯人读、不参与任何执行、不被任何脚本机读** ⇒ 结构上不可能 skew，陈旧无害；其价值正是「随仓走、不用跳文件」。它是消费仓 `openspec/workflow/` 下**唯一**的托管文件。

- **退役部署文件自愈**：`sdflow-init` MUST 维护一份**退役部署文件名单**（含曾铺进消费仓 `openspec/` 根的 `serve.sh` + `review.html`）并在 `init/update` 每次运行时对其**签名门控删除**——仅当目标文件内容含该文件的 bundle 部署签名（`review.html` 含 `__OPENSPEC_PROJECT_NAME__`、`serve.sh` 含 `openspec-review-serve-`）时才删，MUST NOT 删除不含签名的用户同名文件（防误删）。删除幂等、存量安装自愈、fresh 安装 no-op；机制与退役 hook 反注册同构（承 adr/0022 精神：只删自己确知铺设过的文件，不猜用户文件内容）。`tools/` 下的查看器资产不入该名单——它们随 `tools/` 整删重拷（下方 `copy_bundle` 收敛语义）自动清除。
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

### Requirement: 存量消费仓迁移不自动删、残留副本须告警

`sdflow-init update` 对存量消费仓的规则副本与 `tools/` 副本 MUST 改为"停止复制"，MUST NOT 自动删除仓内既有文件（安全红线 + 免分辨源/消费仓 + 老仓平滑迁移）。当检测到仓内残留的旧规则文件或旧 `tools/` 时，`sdflow-init` MUST **显式告警**，MUST NOT 静默留着。

**告警文案 SHALL 陈述「已无生效路径」而非「遮蔽全局」**——resolver 取消仓内优先后（见「规则全局解析 resolver」需求），残留副本**不再遮蔽任何东西，也不再被任何路径读取**，它是纯死件。文案 SHALL 明确：删 = 清理死件（推荐）/ 留 = 无害但无用；MUST NOT 沿用"留 = 显式 pin"的旧表述（pin 语义已取消，该表述会让用户以为副本仍在生效）。此告警即 CONTEXT 术语『反静默守卫』的**残留死件**变体（见 `adr/0003`、`adr/0039`）。

〔spec-review-amendment / impl-review-fix 935eb42〕告警触发点 = **`init` 与 `update` 两种模式均内联检测**（同一判据函数：新项目 fresh init 自然零残留、零告警；老仓被误当新项目跑 `init` 时也不因模式不同而假绿放过残留）+ **`sdflow-maintain` 兜底扫描**（覆盖常年不跑 `init`/`update` 的仓）；检测范围 MUST 同时覆盖旧版仓内 `hack/checkpoint-commit.sh` **孤儿副本**（checkpoint 全局化后不再被任何机制刷新），并给对称提示。

#### Scenario: update 不删残留、给出死件告警
- **WHEN** 一个 pre-change 的存量消费仓（有规则副本与 `tools/`）跑 `update`
- **THEN** update 只铺 `WORKFLOW-GUIDE.md`、保留旧文件不删，并告警"这些副本已无任何生效路径（评审一律走全局），删=清理死件 / 留=无害但无用"；MUST NOT 输出"留=显式 pin"

#### Scenario: 老仓被误当新项目跑 init 同样告警
- **WHEN** 一个已有陈旧残留的存量仓被误跑了 `init`（而非 `update`）
- **THEN** 残留检测同样触发（判据与 `update` 共用），MUST NOT 因跑的是 `init` 模式而假绿放过残留（B2-F3）

#### Scenario: 留旧副本不再改变评审行为
- **WHEN** 用户读到告警后选择保留本地规则副本
- **THEN** 该仓评审**仍使用全局规则与全局 tools**（resolver 无仓内优先步），保留副本既不改变行为也不带来风险；MUST NOT 因副本存在而回到旧的本地解析路径

