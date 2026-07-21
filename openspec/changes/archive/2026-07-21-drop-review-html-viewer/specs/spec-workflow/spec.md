# spec-workflow — delta（drop-review-html-viewer）

## MODIFIED Requirements

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

## REMOVED Requirements

（本 delta 不移除整条 Requirement——review UI 相关内容均为「workflow bundle 改在权威源、经部署下发」需求内的条款/场景，随该需求的 MODIFIED 一并更新。以下列出被删除的具体场景，供归档对码：）

- **场景「建 change 不再落每目录 review stub」** — REMOVED。**Reason**：查看器整体移除后，「每目录不落 stub」的约束失去载体（无任何查看面）。**Migration**：无——`openspec new change X` 本就不再落 `review.html`；查看变更直接读 `openspec/changes/X/` 下 Markdown。
- **场景「review UI 根锚 hash 深链落 scoped 首屏」〔T45〕** — REMOVED。**Reason**：查看器 engine 已删，无 hash 深链行为。**Migration**：无。
- **场景「空 hash 或跨源 hash 回落根锚全树」〔T45 安全〕** — REMOVED。**Reason**：同上，同源守卫随 engine 删除。**Migration**：无。
- **场景「陈旧深链 404 回落根锚并显形」〔T45·反静默守卫〕** — REMOVED。**Reason**：同上，404 回落逻辑随 engine 删除。**Migration**：无。
