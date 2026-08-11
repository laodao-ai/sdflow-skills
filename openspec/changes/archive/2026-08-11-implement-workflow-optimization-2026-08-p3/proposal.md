# Proposal · implement-workflow-optimization-2026-08-p3

> 背景：`openspec/roadmaps/workflow-optimization-2026-08/` 阶段 3（design.md 决策 3）。
> 决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)。

## Why

四个上游源（gstack / superpowers / matt 套件 / OpenSpec CLI）的吸收全部是一次性快照式：
调研冻结在 2026-07，无版本锚 ⇒ 每次重看都是全量成本，实证结果是「从不重看」；
散点 todo（T264/T245/T246/T267）各自孤立无机制承接。需要一个把「重看」变成增量成本的
机制：锚点 + delta 采集 + 分诊报告，人只拍板。

## What Changes

- **新增数据类 skill `sdflow-upstream-watch/`**（SKILL.md + `scripts/` + `tests/`）：
  - 机械层脚本：维护 `openspec/upstream/anchors.yaml`（四源锚 + `last_run`）；四源采集器
    （gstack=git ls-remote+log、superpowers=marketplace 仓 `.claude-plugin/marketplace.json`
    条目 `source.sha` 字段追踪〔该仓不 vendor 插件内容，路径过滤不可行，评审实查坐实〕
    [spec-review-amendment]、matt=mattpocock/skills 全量 +
    `.skill-lock.json` 已装项 hash 辅助、OpenSpec=npm registry + **schema fork 内容对比
    （T264 的机械实现）**）；产出 `openspec/upstream/reports/<UTC时间戳>.md` delta 报告骨架
    （文件名含 UTC 时间戳到秒，一次运行一份 [spec-review-amendment]）。
  - 模型层（SKILL 编排）：对 delta 逐条「与本仓同类面对照」三分诊（吸收候选 / 观望 / 不吸）；
    人拍板「吸」的经 recorder `add` 入池（显式 `source_change`），watch 自身不改池。
- **`sdflow-upgrade/SKILL.md` 加轻提醒段**：收尾读 `anchors.yaml` 的 `last_run`，距今 >30 天
  （可配）打一行提醒；零网络、锚缺失静默跳过。
- **四散点收口（一关三留）**：T264 → DONE（evidence 指 schema drift 采集器）；
  T245/T246/T267 原地保留，作为首轮分诊报告的 seed 条目呈报。
- 安装面随动：`setup.sh` 既有路径自动纳入新顶层 skill；README「Skills 列表」同步。

无 BREAKING：新 skill 零侵入既有 skill，锚目录独立、整体可移除。

## Capabilities

### New Capabilities

- `upstream-watch`: 四源版本锚维护、delta 机械采集（含 OpenSpec schema fork drift 对比）、
  分诊报告产出与 recorder 入池衔接、`sdflow-upgrade` 陈旧提醒线。

### Modified Capabilities

（无——既有 specs 无行为变更；`sdflow-upgrade` 提醒线属新能力的消费端，无既有 spec 覆盖。）

## 需求优先级

- **P0**：锚文件 + 四源采集器 + 报告产出（机制核心，没有它什么都没有）
- **P1**：schema fork drift 对比（T264 收口）、分诊入池衔接、首轮真实运行（roadmap 里程碑
  「四源有锚、watch 跑通一轮 delta 分诊」）
- **P2**：`sdflow-upgrade` 提醒段（机制可用后的习惯保障）

## 利益相关方与外部依赖

- 外部依赖：github.com 三仓（garrytan/gstack、mattpocock/skills、anthropics/claude-plugins-official，
  均 `git ls-remote` 免认证可达，已实测）+ npm registry（`@fission-ai/openspec`）。
  不可达时降级只报本地锚，如实标注。
- 本地依赖（只读）：`~/.claude/plugins/installed_plugins.json`、`~/.agents/.skill-lock.json`、
  `~/.skills/gstack`（git checkout）、`openspec --version`。
- 利益相关方：仅本仓维护者（单人流程），无跨团队面。

## 假设

- **A1 四上游免认证可达持续成立**（失效影响：该源 delta 降级为「仅本地锚」，报告如实标注；
  机制不崩）。
- **A2 `installed_plugins.json` / `.skill-lock.json` 为第三方内部格式，形状可能随宿主升级变化**
  （失效影响：对应采集器读不出锚 ⇒ fail-loud 报格式漂移 + 降级，MUST NOT 静默给错锚；
  形状断言进 tests）。
- **A3 recorder `add` 契约稳定**（`--json` + 显式 `source_change`；本 session 实操验证，
  失效影响：入池步骤手工执行，报告仍产出）。
- **A4 `/sdflow-upstream-watch` 仅在 sdflow-skills 仓（开发 checkout）根目录下运行**
  [spec-review-amendment]——本 skill 随 setup.sh 全局分发但语义单仓专用（四源与本地锚源均硬编码
  指向本仓工具生态）；脚本起手守卫检测 cwd 非本仓时 fail-loud 退出，不在其他项目写入任何文件。

## Success Metrics

- 一次 `/sdflow-upstream-watch` 运行产出含四源节的分诊报告，且首轮跑在真 delta 上
  （gstack 本地 `960c3a8` vs 上游 `94993f7` 已确认非空）。
- T264 关闭（evidence 指采集器实现）；T245/T246/T267 出现在首轮报告 seed 条目中。
- 全仓 pytest 绿（新增 `tests/` 沙盒化，零全局影响）。

## Non-Goals

- 不实现 T245/T246/T267 的内容本身（拍板「吸」后各开后续 change；T245/T246 另有
  「解除 D8 mid 档钉死」前置人工决定）。
- 不做自动吸收 / 自动改池——watch 只报告，人拍板。
- 不做定时任务 / 后台轮询——触发 = 手动命令 + upgrade 末尾本地提醒。
- 不监视 `impl-pipeline: superpowers` 旧执行轨的去留（T277 独立 change）。

## Impact

- 新增：`sdflow-upstream-watch/`（SKILL.md、`scripts/`、`tests/`）、`openspec/upstream/`
  （anchors.yaml + reports/，git 跟踪）。
- 修改：`sdflow-upgrade/SKILL.md`（提醒段）、README「Skills 列表」、
  `openspec/issues/`（T264 关闭）。
- 技术栈：Python 3 脚本 + pytest（TG-01 命中：仓内既有约定——UTF-8 reconfigure 4 行前导、
  `/usr/bin/python3 -m pytest` 跑测试）；网络访问仅 `git ls-remote` / `npm view`。

## Compliance

无合规 / 隐私 / 许可证面：只读公开仓元数据与本机自有文件，不主动上传数据。
[spec-review-amendment] 注：anchors.yaml 与报告为 git 跟踪文件、本仓为公开仓——写入其中的本机路径
一律用 tilde（`~/...`）记法不展开绝对路径（避免用户名等本机信息进入公开历史），不含凭证/密钥。
