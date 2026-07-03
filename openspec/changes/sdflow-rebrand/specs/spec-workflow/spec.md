# spec-workflow Specification (delta)

> 本 delta = `sdflow-rebrand`：skill 全量更名（9 改 3 留）+ 品牌收拢的规范化。
> 决策真相源 = [proposal.md](../../proposal.md) + [design.md](../../design.md)（RENAME-MAP 唯一数据源）+ 待落 `adr/0007`。

## ADDED Requirements

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

`setup.sh` MUST 以 `sdflow-skills v<VERSION>` 标识输出（`VERSION` 文件为版号真相源，起始 `0.9.0`）；Windows copy 模式的 marker 文件 MUST 新写为 `.sdflow-skills`，且所有权判定 MUST **永久兼容**存量 `.laodao-skills` marker（识别为自属可刷新，MUST NOT 判为异物拒绝接管或误删）。

#### Scenario: 存量 laodao marker 仍被识别为自属
- **WHEN** 某 Windows 机器上存在旧版安装的 skill 拷贝（含 `.laodao-skills` marker），重跑新版 `setup.sh`
- **THEN** 该拷贝被识别为自属 → 正常刷新并换写 `.sdflow-skills` marker；MUST NOT 走"非本工具产物"skip 分支

#### Scenario: 版本标识来自 VERSION 文件
- **WHEN** 运行 `bash setup.sh`
- **THEN** 摘要首行输出 `sdflow-skills v0.9.0`（或当前 VERSION 内容）；VERSION 缺失时显式 `vunknown`，MUST NOT 伪造版号

## MODIFIED Requirements

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
