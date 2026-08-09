## Why

`sdflow-spec-review` 的 Step1 依赖第三方 gstack `/autoplan` 原生执行(1853 行,~800 行为平台样板,另按 scope 从磁盘读入最多 4 个子 skill 各 1050-1514 行),存在四个结构性问题:① **context 污染**——主 session 每轮吃 ~7300 行 gstack 文本;② **路径语义错位**——autoplan 的 design doc 发现、restore point、任务 JSONL、review logs 全写 `~/.gstack/projects/`,其「plan file」概念对不上 openspec 四件套;③ **人类门冲突**——premise gate / User Challenge 被钉为 NEVER auto-decided,与阶段二 G2「中途不弹窗」按字面冲突,靠 prompt 适配软扛;④ **第三方漂移**——gstack 活跃演进(v1.60.2),Step1 行为不受本仓控制。`sdflow-roadmap` 的 review 分档(`/plan-eng-review`/`/autoplan`)是同源姊妹依赖。code-review 侧已由 `absorb-gstack-review` 内化,本侧处置即 T268。retro 聚合(broad 镜 20 轮 166 findings、采纳率 90%、独立率 33%)证明广审能力真实承重——**吸收是搬家,不是删层**。

## What Changes

- **Step1 自持化**:autoplan 原生执行退役,改为恒跑两个中档 fresh 子代理广审镜——**strategy 镜**(CEO 高度:前提/范围/长期轨迹/后悔场景)+ **plan-eng 镜**(计划级工程审:架构耦合/错误路径/测试计划/隐藏复杂度);锚名 `step1-broad-review` 保留,mode 枚举 `native|simulated` → `subagent|main-session`;`gstack-review.md` 落盘环节退役。
- **串行纪律 T20 退役**:广审镜只回 findings、不再原地修订四件套(amendment 统一在 Step3 裁决后落)⇒ 两段 dispatch 合并为**单批全并行** fan-out(广审 + 领域 + 对抗 + 接地),`checkpoint(spec-review-autoplan)` 标签随之退役。
- **DX 吸收**:trigger-catalog 新增 devex TG(developer-facing 交付面:CLI/公共 API/SDK/skill/配置面/错误信息;**不入 HR-TG**)+ 新建 `spec-checklists/domains/devex.md`(蒸馏 plan-devex-review:TTHW 分档/错误信息 problem+cause+fix/命名可猜性/Claude Code Skill DX 清单);`frontend.md` 增补 design 镜 litmus/AI-slop 精华。
- **outside-voice 简化**:C2 复用路径与 `outside_voice_guard.py`(及其测试)退役,design-voice 恒自跑(原回落路径转正)。
- **roadmap 侧**:review 分档判定点②退役,恒跑同一套 strategy/plan-eng 双镜 + **sync-only** outside voice(`outside-voice.sh` sync 分支,不移植 async 段);review 契约(整体 plan 声明/未审待恢复阻塞收尾/处置四态)不变。
- **机械消费点同步**:`lens-metric-contract.md` fold 表 `autoplan-ceo/design/eng/dx→broad` 四行替换为 `strategy/plan-eng→broad`;`anchor_lint` spec-review 层 mirrors token 面;`sdflow-retro` 的 checkpoint 标签解析(`spec-review-autoplan` 退役)与测试。
- **ADR**:0040「gstack 运行时依赖全退役」已立(相位 B),0002 加 superseded 指针(已落盘)。
- **文档 sweep**:`CONTEXT.md`「镜」词条 autoplan 例句、`spec-review.md`、`workflow.md`、`WORKFLOW-GUIDE.md`、`quality-layering.md`、`docs/workflow-skills/*`、`docs/external-dependencies.md`、README。

## Capabilities

### New Capabilities

(无——devex TG/清单为 workflow bundle 数据资产,不引入行为级新能力,同 absorb-gstack-review 先例)

### Modified Capabilities

- `spec-workflow`: 阶段二 Step1 实现主体由「autoplan 原生执行」改为「自持双广审镜 fan-out」;串行时序条款(领域/对抗镜等 autoplan checkpoint)退役为单批 dispatch;roadmap review 衔接提法同步。
- `host-adaptive-execution`: spec-review 层 `fanout-capability` 锚 `mirrors=` 合法 token 集扩 `broad`(广审镜为被派子代理时计入);`subagents="unavailable"` 时广审镜主 session 降级路径与 dead-fanout 豁免口径对齐 code-review 层。
- `workflow-metrics`: 折叠表 prose「autoplan 各子声折叠到 broad」改述为「spec-review 广审镜(strategy/plan-eng)与 code-review scope-audit 折叠到 broad」。
- `roadmap-planning`: review 条款重写——分档(eng 单审/autoplan 三连)退役为恒跑双镜 + sync-only outside voice;调用契约/跳过授权/阻塞收尾条款保留。

## Impact

- **代码/资产**:`sdflow-spec-review/SKILL.md` · `sdflow-roadmap/SKILL.md` · `sdflow-init/assets/workflow/`(trigger-catalog.md · spec-checklists/domains/devex.md 新增 + frontend.md · lens-metric-contract.md · tools/anchor_lint.py + golden 测试 · tools/outside_voice_guard.py 删除 + 测试删除 · spec-review.md · workflow.md · WORKFLOW-GUIDE.md · reference/quality-layering.md)· `sdflow-retro/scripts/`(checkpoint 标签解析 + 测试)· `openspec/CONTEXT.md` · `docs/`。栈标注:markdown workflow 资产 + Python 工具(非 TG-01/02/03 业务栈)。
- **依赖**:移除 spec-review/roadmap 侧对 gstack 的全部运行时依赖(本仓 gstack 运行时依赖归零);无新增外部依赖。gstack 系 skill 作为独立工具仍可手动使用。
- **消费仓**:经 `sdflow-init update` 获得新 trigger-catalog/checklists/contract/tools;SKILL 经 setup.sh symlink 即时生效;guard 脚本消失对消费仓无感(其唯一调用点在 spec-review SKILL 内)。

## 需求优先级

- **P0**:Step1 自持化(双镜 + 锚枚举 + T20 退役)+ C2/guard 退役 + fold 表/anchor_lint/retro 标签机械消费点同步 + spec 四 delta(依赖移除的完整闭环,缺任一即新旧混态)。
- **P1**:DX 吸收(devex TG + domains/devex.md)+ roadmap 侧(分档退役 + 双镜 + sync voice)(能力增强与姊妹依赖收尾,独立可验)。
- **P2**:frontend.md litmus/AI-slop 增补 + 文档面 sweep(纯文档)。

## Success Metrics

- `grep -rn "autoplan\|gstack" sdflow-spec-review/SKILL.md sdflow-roadmap/SKILL.md` 严格归零(DOC-1 口径:正文即最终态,零残留)。
- spec-review 与 roadmap review 全流程在未安装 gstack 的机器上可完整跑通(无降级日志)。
- 全仓 pytest 绿(含 anchor_lint golden、retro 标签测试更新、guard 测试删除)。
- dogfood:本 change 自身的设计审报告产出 `strategy`/`plan-eng` raw 名 broad 镜行 + 新 mode 锚,`anchor_lint` 通过。

## 假设

- **3 声广审结构(strategy + plan-eng + design-voice)≈ 旧 broad 6-7 声的发现能力**——若不成立,`/sdflow-retro` ≥10 轮复评将显示 broad 采纳率/独立率下滑,处置为加声(如 HR 场景加第二 voice),不阻塞本 change。

## Non-Goals

- 不动 code-review 侧(absorb-gstack-review 已内化)。
- 不迁移归档报告旧锚(autoplan-* raw 名按 unknown 处置,历史行降级可接受)。
- 不给 roadmap 建 lens-metric 锚体系;不移植 async voice 段到 roadmap。
- 不卸载 gstack 系 skill 本身(手动使用不受影响);不追踪 gstack 后续演进。

## Compliance

N/A——无 PII/数据居留/行业合规约束;voice 出境扫描沿用既有 `secret_scan` 机制,本 change 不新增出境面。
