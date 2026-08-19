## Context

动机见 proposal.md - Why。理解本设计只需三个现状事实（均已核验）：

1. **出票步档位焊死**：`sdflow-implement` 由 ship 主 session inline 执行（`sdflow-implement/SKILL.md:158-159`），出票模式自身要派 T10-choice strong 档对抗镜（`:256`），子代理不能再派子代理 ⇒ 出票必须留在主 session 位置，模型 = 阶段三 session 档。
2. **切片建议现为 MAY + 建议语义**：design.md 决策区 MAY 含「切片建议」节，出票消费语义是「建议，非契约；节缺席时完全自主出 ticket」（`ff-generation-constraints.md:40-42`）。
3. **T10-choice 复核现仅粒度争议触发**（`sdflow-implement/SKILL.md:255-256`）；BASE-18（change 级 fold-vs-defer）已落地且 strategy 镜已覆盖（`spec-quality-base.md:42`、`sdflow-spec-review/SKILL.md:248`、`sdflow-roadmap/SKILL.md:472`）。

**切分判断流（变更前 → 变更后）**：

```
变更前：
  阶段一(强档产)      阶段二(强档审+人门)        阶段三(session 档)
  design/tasks ───▶ spec-review ──HARD-GATE──▶ RUN_PLAN 自主切票 ★判断在这里
                    (切片方案通常不存在,审不到)   (无独立审查)

变更后：
  阶段一(强档产)         阶段二(强档审+人门)        阶段三(session 档)
  design.md 含          strategy 镜 BASE-31 ──▶  RUN_PLAN 物化已审草图
  切片建议 SHOULD ★──▶  审存在性/内聚质量           │ 默认采纳
  (判断前移到这里)        HARD-GATE 人可见           │ 偏离→记 planning-decisions.md
                                                  └ 无草图/偏离/矛盾→T10-choice
                                                    必触发(strong 档对抗镜)
```

住所选 design.md 的白捡性质：切片建议自动进设计门失鲜监视集（design 域 = proposal/design/tasks.md/specs，`sdflow-implement/SKILL.md:557`），评审 amendments 改设计 ⇒ 出票时草图机械保证文件级新鲜。**文件级新鲜 ≠ 节级一致**（amendments 只改别的节时切片节可残留旧切分）——该缺口由必触发条件第三条「草图与 design 正文矛盾」在出票侧兜住。

## Goals / Non-Goals

**Goals**（proposal 范围之内的设计级边界）：

- 全部改动落在**指令层与 bundle 规则文本**：`ship_gate.py` 及一切机械层脚本零改动；出票步位置、`plan_first_sha` 窗口、design 域失鲜监视集、gate 第四道 plan 校验原样保留。
- 拆分标准单一源放 bundle 的 `reference/`（随 `sdflow-init update` 铺给消费仓），三处消费点指针引用不复制文本。

**Non-Goals**（设计级排除；proposal 级排除见 proposal.md - Non-Goals）：

- 不引入「切片建议」的机械格式校验（节标题识别、票数比对等）——「偏离」无确定性信号（票数增减 ≠ 偏离），按基准 1 划为语义残余；引入解析器还会撞基准 5。
- 不改 `openspec instructions` 载荷或 openspec CLI 侧任何东西——切片建议 SHOULD 经 `ff-generation-constraints.md` 生效（该文件已是 sdflow-spec 相位 C 的生成约束源）。

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)（D1–D8）。

设计级落点补充（不改变 memo 决策，只定位改动面）：

| 决策 | 落点文件 | 改动性质 |
|---|---|---|
| D2 切片建议 MAY→SHOULD | `sdflow-init/assets/workflow/ff-generation-constraints.md` §切片建议 | 升档 + 缺席理由要求 |
| D7 BASE-31 审项 | `sdflow-init/assets/workflow/spec-checklists/spec-quality-base.md` | 新增一行（默认规则自动归 strategy 镜，`sdflow-spec-review`/`sdflow-roadmap` 镜表零改动） |
| D3 消费语义升级 | `sdflow-implement/SKILL.md` 出票模式起手检查段 | 「建议输入」→「默认采纳 + 偏离记 `impl-reports/planning-decisions.md`」（复用 M15 既有落点与行格式） |
| D4 必触发条件集 | `sdflow-implement/SKILL.md` 同段 | 触发条件从「仅粒度争议」扩为三条件析取；复核协议与记录格式原样复用 |
| D6 拆分标准单一源 | 新增 `sdflow-init/assets/workflow/reference/change-decomposition-standard.md` + `openspec/INDEX.md` 同步 | 4 规则 + why（内容锚 BASE-18 已有判定，标准文与判定门分工：标准文讲 why 与完整规则，BASE-18 是评审判定入口，互为指针不复制） |
| D6/D8 三处引用 | `sdflow-roadmap/SKILL.md`（phase 拆分）、`sdflow-spec/SKILL.md` 相位 B（scope 内聚检查）、`sdflow-implement/SKILL.md` + `sdflow-code-review/SKILL.md`（票外问题上报 fold/defer） | 指针引用 + 一句判定语义，不复制标准文本 |

ADR：无提议——所有决策均为规则文本变更，可整体 revert，不满足「难逆转」条件（B.7 回扫结论）。

## 切片建议

初步 ticket 划分（供出票模式作建议输入；阻塞边草图，非契约）：

- **T-a bundle 规则面**：ff-generation-constraints 升档 + BASE-31 + 新增 change-decomposition-standard.md + INDEX 同步（同一片 bundle 一致性面，一票做完）。Blocked-by: none
- **T-b 出票侧**：sdflow-implement 消费语义 + 必触发条件集（含 planning-decisions.md 记录格式）。Blocked-by: T-a（引用标准文与升档后的节语义）
- **T-c 三处引用**：sdflow-spec 相位 B 检查项 + sdflow-roadmap phase 拆分 + sdflow-code-review fold/defer 判定。Blocked-by: T-a
- **T-d 收尾**：T141 set-status DONE（开发 checkout 脚本）+ 全仓 pytest + `sync_principles.py --check`（SKILL.md 被改动，确认托管块未损）。Blocked-by: T-b, T-c

## Risks / Trade-offs

- [必触发判定靠出票方自报（无机械捕获路径）] → 诚实边界写进 SKILL 文本本身（「指令层约束，MUST NOT 表述为机械保证」，沿用既有能力探针的措辞惯例）；spec-review/code-review 的冷层作为事后兜底。
- [SHOULD 档被滥用为「一句敷衍理由」] → BASE-31 审项同时核「缺席理由是否成立」，strategy 镜强制过；人门可见。
- [amendments 波及切片但评审侧不强制同步] → 已接受的边角（memo「接受的边角」第 1 条）：出票侧矛盾触发 T10-choice 单点兜住。
- [SKILL.md 文本改动踩托管块] → 只动业务段落，`sync_principles.py --check` 在 setup.sh 与 tests 双门守着，改完跑一遍。
- [bundle 新增文件消费仓拿不到] → 既有 `sdflow-init update` 通道；本仓 INDEX 同步是 CLAUDE.md 已有纪律，进 tasks 显式一条。

## Migration Plan

1. 全部改动随本 change 一次落（无分阶段）；权威源改完后消费仓靠 `sdflow-init update` 重拉——改的是权威源而非部署副本，无回灌漂移面。
2. 无存量迁移：既有已归档 change 的 design.md 无切片建议节是历史事实，不补写；SHOULD 只约束目标态 producer（新 change）。
3. 回滚 = `git revert` 本 change 的提交（纯文本规则，无数据、无 schema、无 gate 契约变更）；消费仓已 update 过的，revert 后再 update 一次即回旧版。

## Open Questions

无——可安全后置的未知项不存在；全部决策已在 decision-memo 拍板。

## Compliance

- 遵守 `openspec/rules/doc-authoring.md`（DOC-1）：本文只写最终态，无演进史。
- 遵守 CLAUDE.md 基准 1/5：新增判定均为语义层（无确定性信号），不引入任何格式解析器。
- 遵守「勿手改 `sdflow:principles` 托管块」：本 change 触碰的 SKILL.md 均只改业务段。
- 遵守 workflow bundle 部署纪律（spec-workflow「改在权威源」Requirement）：只改 `sdflow-init/assets/workflow/`，不动消费仓副本。
- 无豁免项。
