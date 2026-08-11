---
schema_version: 1
change: implement-workflow-optimization-2026-08-p3
branch: feat/implement-workflow-optimization-2026-08-p3
generated_at: 2026-08-11T17:08:48+08:00
decision_hash: 3d90b8684a61
---

# 决策纪要 · implement-workflow-optimization-2026-08-p3

## 目标态

一次运行产出「四源（gstack / superpowers / matt 套件 / OpenSpec CLI）锚点以来可吸收项」的
delta 分诊报告，人拍板后经 recorder 入池——上游重看从全量成本变为增量成本，吸掉
T264/T245/T246/T267 四条散点。

## 拍板决策

- **D1 scope 边界 = 只建机制，四散点「一关三留」**（人 2026-08-11 确认，读法 A）——p3 交付
  watch 机制本身 + 跑通一轮真实分诊报告；T264（schema drift 检测）由 OpenSpec 采集器机械
  实现、p3 收尾关闭（DONE，evidence 指采集器）；T245/T246/T267 原地保留不实现内容，作为
  watch 首轮报告的分诊条目，人拍板「吸」的才各开后续 change。**砍掉的候选**：读法 B
  （p3 顺手实现部分散点内容，如 T267 python checklist）——change 范围膨胀、混不相干功能，
  且 T245/T246 共享「解除 D8 mid 档钉死」前置人工决定，不可顺手做。

- **D2 触发节奏 = 手动命令 + `/sdflow-upgrade` 末尾轻提醒**（人 2026-08-11 确认）——
  watch 由 `/sdflow-upstream-watch` 手动触发；`sdflow-upgrade` 收尾读本地锚文件 `last_run`
  时间戳，距今 > 30 天（默认，可配）打一行提醒，锚文件缺失静默跳过，提醒线零网络。
  **砍掉的候选**：纯手动（实证「从不重看」——三套件调研冻结 2026-07 无人回看）；
  挂 upgrade 自动跑（每次升级联网查四源，拖慢且网络失败污染升级体验）。

- **D3 上游观察面 = superpowers 盯 marketplace 仓、matt 盯上游全量**（人 2026-08-11 确认）——
  superpowers 观察 `anthropics/claude-plugins-official`（安装通道所见即所得，报出的 delta
  都真能升到）；matt 观察 mattpocock/skills HEAD 全量（新增 skill 本身就是可吸收项）+
  `.skill-lock.json` 已装项 hash 比对辅助；gstack / OpenSpec 无分叉（全仓 checkout / npm
  registry）。**砍掉的候选**：superpowers 盯作者原始仓（obra/superpowers，信号早几天但装
  不到、一源双倍噪声）；matt 只比对已装 6 项（漏掉整类「新增 skill」信号）。
  **关联背景**：用户同日拍板删除 `impl-pipeline: superpowers` 旧执行轨（已入池 T277，独立
  change 处理，不进本 change）——不影响 superpowers 作为**想法来源**留在观察面：插件日常
  在用，T245/T246 正是「吸它的机制想法进 tickets 管线」类条目。
- **D4 锚数据落点 = `openspec/upstream/`（主 session 自决，谨慎同事默认）**——
  `anchors.yaml`（四源锚 + `last_run`，脚本 owns 读写）+ `reports/<UTC日期>.md`（一次运行
  一份分诊报告，落盘 git 跟踪）。依据：与 `openspec/issues/`、`openspec/retro/` 同构（仓内
  数据类产物统一住 `openspec/` 下）；锚是**本仓吸收进度**的状态，不是机器状态，故不放
  `~/.sdflow/`。**砍掉的候选**：`~/.sdflow/upstream/`（机器级落点——同一锚会被多个
  checkout 共享，dev/runtime 双 checkout 纪律下会互相污染吸收进度）。
- **D5 报告形态与入池衔接（主 session 自决）**——报告按源分节，每条 delta 三分诊
  （吸收候选 / 观望 / 不吸）+ 一句对照理由（与本仓同类面对照）；首轮报告 seed 呈报
  T245/T246/T267（承 D1）；人拍板「吸」的条目由模型跑 recorder `add` 入池，**MUST 显式传
  `source_change`**（省略会误挂当前活跃 change，`issues_v2.py` add 契约 + T277 本 session
  实操验证）。watch 自身 MUST NOT 直接改池。
- **D6 skill 结构 = 标准数据类顶层 skill（主 session 自决）**——`sdflow-upstream-watch/`
  （SKILL.md + `scripts/` + `tests/`）：脚本 owns anchors/报告文件读写与四源采集（确定性），
  SKILL owns 分诊判断与编排；随 `setup.sh` 既有 `install_into` 路径安装（新增顶层 skill
  → 重跑 setup.sh 建链 + README「Skills 列表」同步）；`sdflow-upgrade/SKILL.md` 加 D2 提醒
  段（只读 `anchors.yaml` 的 `last_run`，缺失静默跳过）。

## 承重约束

- **C1 四源 delta 均可机械采集（免认证、无 API 限流面）** — 验证方式：三条上游
  `git ls-remote` 实测可达（git 协议非 GitHub API）；npm registry `npm view` 实测；本地锚
  文件（`installed_plugins.json` / `.skill-lock.json` / git checkout / `openspec --version`）
  全部实查存在且含版本信号；**证据锚**：本 session 2026-08-11 命令输出——gstack 上游 HEAD
  `94993f7`（本地 `960c3a8`，首轮即有真 delta）、mattpocock/skills `84fdeff`、
  claude-plugins-official `920824c`、openspec 本地=registry=1.8.0
- **C2 matt 消费文档已移除，watch 无需处理 triage-labels 关系** — 验证方式：
  `openspec/matt/` 目录实查不存在；**证据锚**：`openspec/adr/0037`（matt 移除 + issue-tracker
  角色从未真正投入使用的实证）
- **C3 本地锚源文件形状已实查** — 验证方式：本 session 逐一打开——
  `~/.claude/plugins/installed_plugins.json`（per-plugin `version` + `gitCommitSha`，
  superpowers 6.2.0 / `6efe32c9`）、`~/.agents/.skill-lock.json`（per-skill `source` +
  `skillFolderHash` + 时间戳）、`~/.skills/gstack`（git checkout，origin=garrytan/gstack，
  HEAD `960c3a8` v1.60.2.0）、`openspec --version`=1.8.0；**证据锚**：2026-08-11 命令输出
  （task-log 阶段 3 起手调研可复查）
- **C4 recorder 入池契约** — 验证方式：`issues_v2.py add --help` 实查（`--json` 含
  `source_change` 可选字段）+ T277 本 session 实操（显式传 `source_change: main` 成功）；
  **证据锚**：`sdflow-issues/scripts/issues_v2.py` add 子命令 + `openspec/issues/open/todo/T277.md`
- **C5 机制骨架已过一轮独立设计门** — 验证方式：roadmap design 决策 3 含替代方案对比
  （并入 maintain / 维持手动 / 只做单源）+ 三镜代价 + 主次判定，且该 roadmap 三件套过
  strategy/plan-eng 双镜 + sync voice 评审（11 组 findings 全处置）；**证据锚**：
  `openspec/roadmaps/workflow-optimization-2026-08/design.md` 决策 3、同目录 task-log.md
  「Review 处置」小节

## 接受的边角

- **提醒阈值 30 天为拍脑袋起步值** — 概率（不合适）中 / 影响小（只是提醒早晚）/ 完美成本
  （推导「正确」阈值）无数据基础；**为何接受**：做成可配，错了改一个数。
- **superpowers 经 marketplace 晚于原始仓若干天** — 概率高 / 影响小（吸收本就非实时）/
  完美成本 = 双仓观察双倍噪声；**为何接受**：安装通道所见即所得更符合「报了就能吸」。
- **matt 全量观察噪声大** — 概率高 / 影响小（分诊压噪 + 人只看报告）/ 完美成本 = 预过滤
  规则维护；**为何接受**：漏「新增 skill」信号的代价大于多读几行报告。
- **无网 / 上游不可达时降级只报本地锚状态** — 概率低 / 影响小 / 完美成本高（离线镜像）；
  **为何接受**：如实标注降级即可，下轮补跑。
- **plugin cache 被 Claude Code 自动更新导致锚间前移** — 概率中 / 影响小（下轮运行照样
  看到累计 delta）；**为何接受**：watch 语义是「锚点以来」，非实时监控。

## 三镜代价

D2（触发节奏）与 D3（观察面）命中 TG-23（≥2 合理方案）：

- **D2**：系统镜——提醒段只读一个本地字段、锚缺失静默跳过，对 `sdflow-upgrade` 零网络零
  失败面，可整段删除回退；用户镜——upgrade 收尾多一行提示，无打断；开发循环镜——不引入
  新习惯，重看成本从「记得去看」降为「被动提醒」。**主次判定**：开发循环镜为主——机制
  价值全在对抗「从不重看」。
- **D3**：系统镜——单仓单锚（marketplace / mattpocock HEAD），采集器无双源合并逻辑；
  用户镜——报告条目均为「可立即吸收」项，无「装不到」的噪声；开发循环镜——matt 全量面
  换来新 skill 信号，分诊成本略增。**主次判定**：用户镜为主——报告的可信度（报了就能吸）
  决定人愿不愿意持续看它。
