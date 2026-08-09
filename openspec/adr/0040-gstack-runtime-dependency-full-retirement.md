# gstack 运行时依赖全退役(supersede adr/0002)

评审工作流对 gstack 的最后一段运行时依赖(sdflow-spec-review 的 autoplan 原生执行 + gstack-review.md 复用守卫、sdflow-roadmap 的 /plan-eng-review//autoplan 分档)整体退役,能力自持化:广审层由 strategy/plan-eng 两个恒跑 fresh 子代理承载,DX 视角降为 devex 领域(新 TG + spec-checklists/domains/devex.md),跨模型第二意见由 outside-voice.sh 全责(spec-review 恒自跑 design-voice;roadmap 挂 sync-only voice)。adr/0002 的「复用产出物合法」边界随其最后一个实例消失而废止——自制 skill 对 gstack 既不依赖内部、也不再读产出物。

演进链:adr/0002(复用产出物省 codex)→ absorb-gstack-review(code-review 侧内化)→ refactor-roadmap-internalize-deps(roadmap 讨论层内化)→ 本决策(spec-review + roadmap review 侧收尾,依赖归零)。

## Considered Options

- **全退役 + 自持广审镜(选中)**:消灭 context 污染(autoplan 原生执行 ≈7300 行 gstack 文本/轮)、`~/.gstack/` 路径语义错位、AskUserQuestion 门与 G2 的字面冲突、第三方漂移面(gstack 活跃演进);codex 调用不升反降(每轮 2-3 次 → 1 次 design-voice)。代价:广审多声结构(3 视角 × 2 模型)收敛为 3 声,能力等价性事前不可证,由 retro ≥10 轮复评兜底。
- **维持 adr/0002 复用态**:省一次 design-voice 自跑,但四个结构性问题(context/路径/人类门/漂移)在复用态下无解,且 code-review 侧已内化 ⇒ 两侧口径分裂长期存在。
- **只退役 spec-review 侧、roadmap 侧另行处置**:再留一个「姊妹依赖 todo」(T268 同款),违背「一个 change = 一个完整阶段结果」拆分标准;roadmap 侧改动小,fold 进本次成本低。

## Consequences

- `sdflow-spec-review` Step1 重写为恒跑双镜 fan-out;锚名 `step1-broad-review` 保留,mode 枚举 `native|simulated` → `subagent|main-session`;`outside_voice_guard.py` 及其测试删除。
- `sdflow-roadmap` review 分档判定点②退役,恒跑双镜 + sync-only outside voice;review 契约(整体 plan 声明/未审待恢复阻塞收尾/处置四态)不变。
- `lens-metric-contract.md` fold 表 `autoplan-*→broad` 四行替换为 `strategy/plan-eng→broad`;归档报告旧锚不迁移,旧 raw 名按 unknown 处置(历史行降级可接受)。
- 新增 `spec-checklists/domains/devex.md` + devex TG(不入 HR-TG);devex 清单蒸馏自 gstack v1.60.2 快照,此后按本仓 retro 数据演进,不跟第三方。
- gstack 系 skill 仍可作为独立工具手动使用;`docs/workflow-skills/gstack-*.md` 降级为非运行时参考。回退 = revert 本 change 各 SKILL/bundle 改动并重装 gstack(方向性成本高,不设计快捷回退)。
