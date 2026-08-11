# Design · implement-workflow-optimization-2026-08-p3

## Context

动机见 [proposal.md](./proposal.md) Why。现状约束（只列解释方案所需）：

- 四源在本机的锚源形状各异（均已实查，memo C1/C3）：gstack 有完整 git checkout；
  superpowers 只有 plugin cache + `installed_plugins.json` 元数据；matt 套件只有
  `.skill-lock.json`（无 git）；OpenSpec 是 npm 全局包 + 本仓 schema fork
  （`sdflow-init/assets/schemas/sdflow-spec-driven/`，上游对照物 =
  `$(npm root -g)/@fission-ai/openspec/schemas/spec-driven/`，本 session 实查两侧同构：
  `schema.yaml` + `templates/{proposal,design,spec,tasks}.md`）。
- 本仓机械层既有约定：YAML 读写走 `yq`（`retro_report.py` 先例 + `yq-yaml-operations`
  spec）；Python 入口脚本须带 4 行 UTF-8 reconfigure 前导；测试沙盒化零全局影响
  （开发期测试三层第 1 层）。
- `sdflow-upgrade/SKILL.md` 现为四步结构（pull → setup → 展示 → 提示），提醒段追加为第 5 步。

## Goals / Non-Goals

**Goals**（设计层边界，proposal 范围之外不重述）：

- 机械层「零解析上游内容」：delta 事实全部由 git / npm / sha256 自己回答
  （`ls-remote`、`log`、`npm view`、整文件 digest），不手搓任何上游格式解析器（基准 5）。
- 锚推进与报告产出绑定：anchors 只由脚本写，advance 以**报告路径 + facts 路径**双参数绑定本轮
  （报告存在 + 报告文本包含 facts 全部 commit sha 的零解析校验）[spec-review-amendment]
  ——不存在「锚走了、报告没了/报告是别轮的/报告漏转录」的静默丢轮。
- 采集失败按源降级、fail-loud、不互相传染：单源不可达/格式漂移只降级该源节。

**Non-Goals**：

- 不缓存上游内容做离线全文 diff（报告给指针：commit 列表 + 变更路径，人要细看点开上游）。
- 不做跨机同步锚（锚是本仓 git 跟踪文件，随 push/pull 自然同步）。

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)。

以下为 memo 之下的实现级技术选择：

- **TD1 单脚本双子命令**：`scripts/upstream_watch.py` 提供 `collect`（采集四源 delta 事实，
  输出 JSON facts 文件到 `openspec/upstream/.facts/<UTC时间戳>.json`，`.gitignore` 该目录
  [spec-review-amendment]）与 `advance`（接收**报告路径 + facts 路径**双参数：校验报告存在、
  报告文本包含 facts 中每源全部 commit sha〔零解析子串检查，防漏转录后锚照推〕后，把 anchors
  推进到 **facts 记录的观测值**——advance 自身禁止发起任何网络 / git 查询，消 collect/advance
  时序窗口丢 delta [spec-review-amendment]——并更新 `last_run`）。**degraded 源锚不推进**：只推进
  `status=ok` 且观测值完整的源，degraded 源 anchor 逐字保留，报告标注下轮重试同一窗口
  [spec-review-amendment]。**起手守卫**：两子命令检测 cwd 为 sdflow-skills 仓（git remote 判定），
  非本仓 fail-loud 退出（proposal A4）[spec-review-amendment]。为什么不是每源一个脚本：
  四采集器共享锚读写与降级语义，拆开徒增入口与测试面；源间隔离用函数级 try/except 实现。
  全部外部子进程统一数字化超时（单点常量，默认 60s/次调用），超时按该源 degraded 处置
  [spec-review-amendment]。
- **TD2 无本地 checkout 的仓用 blobless bare 克隆缓存**：matt / marketplace 两仓需要
  「锚..HEAD 的 commit 列表 + 变更路径」，`ls-remote` 只给 HEAD ⇒
  `git clone --filter=blob:none --bare` 到 `~/.cache/sdflow-upstream/<source>.git`
  （已存在则 `fetch`；fetch 失败 → 删缓存目录重 clone 一次自愈，再失败才 degraded、原因文案带
  缓存路径 [spec-review-amendment]）。**matt** 取 `git log --name-only 锚..HEAD`。
  **superpowers 不用路径过滤**〔评审双对抗镜实查坐实：marketplace 仓不 vendor 插件内容，
  `plugins/superpowers` 路径不存在，路径过滤永远返回空〕⇒ 改为追踪
  `.claude-plugin/marketplace.json` 中 superpowers 条目的 `source.sha` 字段：
  `git log 锚..HEAD -- .claude-plugin/marketplace.json` 圈定该文件变更的 commit，逐次读该 JSON
  字段比对（有界 JSON 字段提取，基准 5 合规），delta = sha 引用变化序列（指向 obra/superpowers
  的被打包 commit）[spec-review-amendment]。**三个 git 源取 log 前先
  `git merge-base --is-ancestor 锚 HEAD`**：非祖先（上游 force-push 历史重写）→ 该源 degraded
  「上游历史疑似被重写，锚失效」，防 exit 0 假成功 [spec-review-amendment]。为什么不用 GitHub API：
  限流 + 认证面（memo C1 特意选 git 协议）；为什么缓存放 `~/.cache` 不放仓内：
  这是可再生缓存非状态，机器级合理，删了自动重建。gstack 直接用既有 checkout
  `git fetch origin` + `log 锚..FETCH_HEAD`（fetch 只动 remote-tracking refs，无工作树影响）。
- **TD3 schema drift = 整文件 sha256 对比**：fork 目录 vs 上游安装目录逐文件 digest，
  报 changed/added/removed 文件清单（T264 的机械实现）。零解析（基准 5 A21 同款）；
  「变化意味着什么」留给分诊判断。**对比基线 = 本机已安装版（设计门拍板 Q1）**：报告 OpenSpec
  节明示「drift 基于已安装版 X，registry 最新 Y」；registry 新版的 schema 细节延迟到升级后
  一轮呈现，「有新版」信号由版本对照子项独立承担 [spec-review-amendment]。
- **TD4 anchors.yaml 读写走 `yq`**：与 `retro_report.py` 的 mirror-dispositions 解析同模式
  （三态错误语义：文件缺失=首轮初始化；yq 失败=fail-loud；值缺失=该源视为无锚首轮），
  **含其 mikefarah-flavor 探测 idiom（各自实现、不跨目录 import；非 mikefarah 家族 yq 直接报错
  阻止误用）** [spec-review-amendment]。
  为什么不用 JSON：D4 已定 YAML 名（人可扫读），且 yq 是本仓机械层既有依赖，不新增面。
- **TD5 报告 = 模型判断产物，事实来自 facts JSON**：脚本不写报告正文；SKILL 编排模型读
  facts JSON 写 `reports/<UTC时间戳>.md`（文件名含 UTC 时间戳到秒，一次运行一份，消同日互相
  覆盖 [spec-review-amendment]；按源分节、三分诊、seed 条目）。**三分诊证据条款**：证据不足时
  MUST 标「观望/待核查」不硬判吸/不吸；允许对候选 commit 在 bare 缓存 `git show` 按需取内容
  （blobless clone 按需拉 blob，git 自己回答）[spec-review-amendment]。**入池命令模板**：报告内
  为每条「吸收候选」预生成完整 recorder `add` 命令（含 `source_change`），人拍板后直接执行
  [spec-review-amendment]。**展示层降级**：
  某源 facts 缺失时报告该节写「采集降级：<原因>，请自行核查 <上游 URL>」，MUST NOT 罢工
  （基准 5 的降级判据——判定与展示不同门）；**本地元数据格式漂移分支例外**——修复提示指向本地
  文件路径与键路径断言，不复用「上游 URL」模板 [spec-review-amendment]。
- **TD6 提醒线读运行 checkout 的锚**：`sdflow-upgrade` 第 5 步读
  `~/.skills/sdflow-skills/openspec/upstream/anchors.yaml` 的 `last_run`（pull 后即最新，
  路径不依赖 cwd）；缺失/不可解析静默跳过（提醒是 nice-to-have，不得给 upgrade 增加失败面）。

## 数据模型（TG-05）

`openspec/upstream/anchors.yaml`（脚本 owns，git 跟踪）：

```yaml
schema_version: 1
last_run: 2026-08-11T09:00:00Z          # UTC，报告产出即更新
sources:
  gstack:
    kind: git-checkout
    checkout: ~/.skills/gstack           # 本地锚源
    upstream: https://github.com/garrytan/gstack.git
    anchor_sha: 960c3a8...               # 上次分诊到的上游 commit
  superpowers:
    kind: plugin-cache
    upstream: https://github.com/anthropics/claude-plugins-official.git
    anchor_sha: 920824c...               # marketplace 仓 HEAD；delta 经 marketplace.json source.sha 字段
    installed_version: 6.2.0             # 辅助信息，来自 installed_plugins.json；该文件为
                                         # per-plugin 多记录数组（跨 scope 版本可异）——取值策略：
                                         # 优先 scope=user，无则取版本最大 [spec-review-amendment]
  matt:
    kind: skill-lock
    upstream: https://github.com/mattpocock/skills.git
    anchor_sha: 84fdeff...
  openspec:
    kind: npm+schema-fork
    package: "@fission-ai/openspec"
    anchor_version: 1.8.0
    schema_fork_digest: <fork 目录聚合 sha256>   # 双侧任一变动都触发 drift 节
```

facts JSON（`collect` 输出，落 `openspec/upstream/.facts/<UTC时间戳>.json`，`.gitignore` 该目录；
advance 的唯一观测值来源 [spec-review-amendment]）：per-source
`{status: ok|degraded, reason?, head_sha/latest_version, commits: [{sha, subject}],
changed_paths: [...], schema_drift?: {changed: [], added: [], removed: []}}`。

## 组件与数据流（TG-13 / TG-11）

```
                    ┌─────────────────────────────────────────────┐
                    │ sdflow-upstream-watch/SKILL.md（模型编排）    │
                    │  分诊判断 · 报告成文 · 入池衔接（人拍板后）      │
                    └───────┬─────────────────────────┬───────────┘
                            │ ① collect               │ ③ advance（报告存在才推锚）
                            ▼                         ▼
                    ┌──────────────────────────────────────────────┐
                    │ scripts/upstream_watch.py（机械层）            │
                    │  gstack: fetch+log │ superpowers: bare 缓存    │
                    │  matt: bare 缓存    │ openspec: npm view+digest │
                    └───┬──────────────┬───────────────┬───────────┘
                        │ 读            │ 写            │ 读（只读外部）
                        ▼              ▼               ▼
              anchors.yaml      facts JSON      上游 git 仓 ×3 / npm registry /
              (openspec/upstream/) (scratch)    本地锚源（plugins json · skill-lock ·
                        ▲                        gstack checkout · schema fork 双侧）
                        │ 只读 last_run
              ┌─────────┴───────────┐    ② 模型写 reports/<date>.md
              │ sdflow-upgrade 第5步 │       ↑（facts → 三分诊 → 报告，人读）
              │ 陈旧提醒（零网络）     │    ④ 人拍板「吸」→ recorder add（显式 source_change）
              └─────────────────────┘
```

运行序列：`collect` → 模型写报告 → `advance`（校验报告→推锚）→ 人拍板 → recorder 入池。

## 失败模式表（TG-08）

| 失败 | 检测 | 处置 | 报告呈现 |
|---|---|---|---|
| 某上游不可达（快速失败） | git/npm 非零退出 | 该源 degraded，其余源照采 | 该节「采集降级 + 原因 + 上游 URL」 |
| 某上游挂起（无退出）[spec-review-amendment] | subprocess 超时常量（默认 60s/次，单点定义）到点终止 | 该源 degraded（原因=超时），其余源照采 | 同上 |
| 上游历史被重写（锚非 HEAD 祖先）[spec-review-amendment] | `git merge-base --is-ancestor` 非零 | 该源 degraded「锚失效」，锚不动 | 同上 |
| bare 缓存损坏 [spec-review-amendment] | fetch 非零退出 | 删缓存重 clone 一次自愈，再失败才 degraded | 同上 + 缓存路径 |
| 本地锚源缺失（如 gstack checkout 不在） | 路径/命令探测 | 该源 degraded | 同上 + 修复提示（如 clone 路径） |
| `installed_plugins.json` / `.skill-lock.json` 形状漂移（A2） | 键路径断言失败 | fail-loud 报格式漂移，该源 degraded，MUST NOT 静默给错锚 | 修复提示指向本地文件与键路径断言（不用「上游 URL」模板）[spec-review-amendment] |
| cwd 非 sdflow-skills 仓 [spec-review-amendment] | git remote 守卫 | fail-loud 退出，不写任何文件（proposal A4） | — |
| anchors.yaml 缺失 | 文件探测 | 首轮初始化语义（per-source，见 Risks）：gstack 以本地 checkout HEAD 为天然锚（首轮即出真 delta），其余源「无锚 ⇒ 报当前态为基线」，advance 时建档 [spec-review-amendment] | 报告标注「首轮建锚」 |
| anchors.yaml yq 解析失败 | yq 非零退出 | fail-loud 硬停（状态文件坏了不能猜） | — |
| 报告未产出就 advance | advance 前置校验 | 拒绝推锚，exit 非零 | — |
| 提醒线读锚失败 | — | 静默跳过（TD6） | — |

可观测性：facts JSON 落 scratch 留档一轮；报告含每源采集状态行（ok/degraded/首轮）。

## Risks / Trade-offs

- [bare 缓存目录膨胀] → blobless filter + 仅 3 仓，量级 MB 级；`~/.cache` 可随时删除重建。
- [marketplace 仓 HEAD 前移但 superpowers 插件本身没动] → `git log` 限定
  `-- plugins/superpowers`（按路径过滤 commit，git 自己回答，无解析）；路径若变动则全量呈报靠分诊压噪。
- [首轮基线 per-source 拆分 [spec-review-amendment]] → gstack 有本地滞后锚（checkout HEAD
  960c3a8）⇒ 首轮以它为锚跑出真 delta（Success Metric 所要求）；其余三源无天然滞后锚 ⇒
  「当前态即基线」仅建锚零 delta + seed 条目 T245/T246/T267。两规则各成 spec Scenario，
  消除「真 delta vs 当前态基线」的文档间互斥。
- [提醒阈值 30 天不合适] → config 可调（`openspec/config.yaml` 或 anchors.yaml 内
  `remind_after_days`，实现时取后者——单文件自足）。
- [watch 在开发 checkout 跑、提醒线读运行 checkout 锚 [spec-review-amendment]] → 锚经
  commit+push（开发侧）→ pull（运行侧）可见；未 push 期间提醒可陈旧——接受（单人单机、
  提醒是 nice-to-have），SKILL 正文写明 watch 的运行位置约定（A4 守卫同源）。

## 组件清单（TG-13 / BASE-25）[spec-review-amendment]

| 组件 | 职责 | 技术形态 | 部署/落点 |
|---|---|---|---|
| `sdflow-upstream-watch/SKILL.md` | 分诊判断 · 报告成文 · 入池衔接编排 | Markdown + 模型判断 | setup.sh 全局软链（守卫单仓运行） |
| `scripts/upstream_watch.py` | collect/advance 机械层（四源采集 + 锚读写） | Python3 + yq + git + npm | 仓内脚本 |
| `openspec/upstream/anchors.yaml` | 四源锚 + last_run 状态 | YAML（脚本 owns） | git 跟踪 |
| `openspec/upstream/reports/` | 分诊报告（一次运行一份） | Markdown（模型写） | git 跟踪 |
| `openspec/upstream/.facts/` | facts JSON 中间产物 | JSON（collect 写、advance 读） | `.gitignore` |
| `~/.cache/sdflow-upstream/` | matt/superpowers bare 克隆缓存 | git bare repo | 机器级可再生缓存 |
| `sdflow-upgrade/SKILL.md` 第 5 步 | 陈旧提醒消费端 | Markdown 指令（零网络） | 既有 skill 追加段 |

## Migration Plan

- 部署：merge → 运行 checkout `git pull` + `bash setup.sh`（新顶层 skill 自动建链）→
  首轮 `/sdflow-upstream-watch`。
- 回滚：删 `sdflow-upstream-watch/` 目录 + 重跑 `setup.sh`（孤儿清理）；`openspec/upstream/`
  为独立数据目录，`git rm` 即净；`sdflow-upgrade` 提醒段整段删除即回退（TD6 零耦合）。
- 不涉及存量数据迁移（全新数据面）。

## Compliance

- `openspec/rules/doc-authoring.md`（DOC-1）：本文正文只写最终态，无演进史。遵守。
- `openspec/rules/premise-verification.md`：全部外部事实（上游可达、文件形状、schema 双侧
  路径、SKILL 结构）已于本 session 实查，锚记 memo C1–C5。遵守。
- 新增 Python 入口脚本带 4 行 reconfigure 前导（CLAUDE.md 机械门）。遵守。
- 测试沙盒化（tmp_path + 可注入路径/命令 stub，无网络依赖），零全局影响。遵守。
- git 跟踪产物（anchors.yaml / reports/）中的本机路径一律 tilde 记法不展开（本仓为公开仓，
  见 proposal Compliance）[spec-review-amendment]。
- 无豁免项。
