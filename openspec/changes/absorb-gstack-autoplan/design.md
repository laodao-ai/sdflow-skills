## Context

见 proposal.md「Why」。设计对象是三块既有结构:① `sdflow-spec-review` 的 Step1(autoplan 原生执行 + gstack-review.md 落盘 + outside_voice_guard 复用判定)与两段 dispatch 时序;② `sdflow-roadmap` 的 review 节(分档调用外部 skill);③ bundle 机械层(trigger-catalog / spec-checklists / lens-metric-contract fold 表 / anchor_lint / retro 标签解析)。

关键现状事实(已核验):
- `anchor_lint.py:676` 的 `_MIRRORS_LEGAL` 已含 `broad`,`:674` 的 dead-fanout 计数域已排除 broad(absorb-gstack-review 铺好)——spec-review 侧复用,**枚举零改动**。
- `anchor_lint.py:73,203` 对 `step1-broad-review` 锚只验存在性(前缀匹配),mode 枚举换值零脚本改动。
- trigger-catalog 现用编号至 TG-27,devex TG 取 **TG-28**。
- `outside-voice.sh` sync 分支自足(`sdflow-spec-review/SKILL.md:426`),roadmap 挂 voice 不触碰 `sdflow:async-branch` 等值门。

## Goals / Non-Goals

**Goals(设计级)**:
- Step1 与 Step2 合并为**单批全并行 dispatch**(广审×2 + 领域×N + 对抗×2-3 + 接地×1),消灭 T20 串行等待。
- 广审镜与领域镜的分工线清晰可述:广审镜过 **base 清单 R 项**(计划级、domain-agnostic),领域镜过 **domains/ 栈特定 R 项**。
- roadmap review 换执行体后,其对 spec-review SKILL 的镜 prompt 定义**引用复用**(单一源),不复制两份。

**Non-Goals(设计级)**:
- 不改 Step3/Step4(裁决/置信分流/决策登记/lens-metric 落锚/拍板回写协议原样)。
- 不改 outside-voice helper 本体与 async 协议。
- 不做 devex 的 code-checklists 侧对应文件(TG-28 首版 spec-review-only,同 TG-27 反向先例;code 侧待实测需要再补)。

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)(D1-D7)。以下为设计级技术选择:

**DD1 单批 dispatch 结构(T20 退役)**。旧结构领域/对抗镜等 Step1 checkpoint,理由是 autoplan 会原地产 `[gstack-amendment]` 修订四件套;新广审镜只回结构化 findings、不改盘面,等待理由消失。新结构:

```
第零步(规则/档位解析)
  │
  ├─ 能力探针(host=codex 才探,恒一次,结果对全部镜共用)
  ▼
单批 dispatch(一条消息内并行派出全部镜,fresh context)
  ├─ strategy 镜(中档)──┐
  ├─ plan-eng 镜(中档)──┤ raw 名 strategy/plan-eng,折叠 broad
  ├─ 领域镜 ×N(中档,按 TG 命中,含 devex)
  ├─ 对抗镜 ×2-3(中档)
  ├─ 接地镜 ×1(弱档)
  └─ design-voice(codex,恒自跑;async 协议不变,Step3 barrier collect)
  ▼
Step3 合并去重 + 对抗裁决(不变)──▶ Step4 报告 + amendment(不变)
```

`checkpoint(spec-review-autoplan)`(P2c 第 1 次)随 Step1 退役——本 skill 只剩 `checkpoint(spec-review)` 一次。备选「保留两段 dispatch」被砍:唯一收益是领域镜能看到 broad amendment,而 amendment 已不存在。

**DD2 广审镜 prompt 契约**。两镜各自 prompt MUST 含:`{change_dir}` 路径、四条通则原文、职责清单(strategy:BASE-01/10/12/13/14/27 等计划级 R 项 + 前提/范围/长期轨迹/后悔场景;plan-eng:BASE-05/06/16/17/19/25/28 等工程 R 项 + 架构耦合/错误路径/测试计划/隐藏复杂度)、返回结构化 findings(问题/证据 file:line/置信/严重度/建议)、不 AskUserQuestion。两镜清单划分写死在 SKILL 的镜表里,与领域镜的分工线:**base 的 R 项归广审镜,domains/ 的 R 项归领域镜**(原「防重叠 1.4」条款删除,由此分工线替代)。

**DD3 锚与降级**。`step1-broad-review` 锚 mode 枚举 `subagent|main-session`(比照 `sdflow-code-review/SKILL.md:275`):正常=subagent;探针判 `subagents="unavailable"` 时广审镜由主 session 亲做(恒跑守卫,mode=main-session),`mirrors=` 计入 `broad` token(合法降级,不触发 dead-fanout,`anchor_lint.py:674-676` 现行为已支持)。gstack-review.md 与 `mode="native|simulated"` 枚举、outside_voice_guard 调用步整体删除。`outside-voice` 锚的 `guard=` 字段随守卫退役从新锚文法移除——`anchor_lint.py:555` 明确 MUST NOT 解析该字段、declared-sites 判据也不用它(仅人读死字段);归档旧锚不迁移,lint 不解析故无兼容问题。

**DD4 fold 表直接替换**。`lens-metric-contract.md` fold 块 `autoplan-ceo/design/eng/dx: broad` 四行替换为 `strategy: broad` + `plan-eng: broad`(直接替换不共存,同 `gstack-adv→scope-audit` 先例);归档报告旧 raw 名不迁移,聚合器按 unknown 处置。

**DD5 retro 标签解析:旧前缀保留识别、新轮次停产**。`sdflow-retro` 的步类型解析继续识别历史 `checkpoint(spec-review-autoplan)` 标签(归档 change 复盘需要),SKILL 侧不再产生;测试断言相应调整(识别历史 + 不要求新产)。备选「解析器删除该前缀」被砍:会让 49 个已归档 change 的阶段墙钟归类漂移。

**DD6 devex 蒸馏范围(TG-28 + domains/devex.md)**。TG-28 触发条件:「变更新增/修改 developer-facing 交付面——CLI 命令/公共 API/SDK/skill/配置面/错误信息文案」;领域列 `devex`(spec-review-only,见 Non-Goals)。devex.md 收录条目(蒸馏自 plan-devex-review v1.60.2 快照,只收 spec 级可判项):TTHW 分档基准(<2min champion / >10min red flag)、错误信息三件套(problem+cause+fix)、命名可猜性/默认值合理性/渐进式披露、升级路径(废弃警告/迁移说明)、Claude Code Skill DX 清单(description 触发精度/自包含性/降级路径可读性)。**不收**:persona 拷问/共情叙事/竞品 WebSearch 基准/DX Scorecard 趋势(取证式过程方法论,依赖 gstack 家目录生态,非清单项)。frontend.md 增补:litmus 精华(首屏品牌可辨/卡片必要性/去装饰仍显高级)+ AI-slop 黑名单浓缩(紫渐变/图标圆圈三列/全局居中/装饰 blob/emoji 当设计元素)为 R 项。
**分类判据(收/不收)**:一条 gstack 内容进 devex.md 当且仅当它是「对着 design/specs 文本可判真伪的检查项」;需要跑外部工具、查竞品、或依赖 `~/.gstack/` 状态的过程方法论一律不收。

**DD7 roadmap sync voice 落法**。site 名 `roadmap-voice`;context = `design.md`「Decisions」+ `roadmap.md` 全文(超 200KB 收敛,同全量 diff 截断纪律);run 目录 `openspec/roadmaps/{name}/.outside-voice/<run-id>/`(`.gitignore` 的 `**/.outside-voice/` 递归覆盖,已验);前台 exec `--timeout 300` 外层 ≥330000ms,退出码按 ⑦ 表映射;失败同族 fallback 只读子代理;findings 进 task-log「Review 处置」四态,**一行留痕 runner/reason_code,不落 anchor_lint/lens-metric 锚**。roadmap 的双镜 prompt 引用 spec-review SKILL 的镜定义段(职责清单同源),差异仅评审对象声明(三件套整体 plan 话术,C7 契约保留)。

**DD8 roadmap SKILL 结构改动面**。判定点②(review 分档)整节删除,判定留痕总则从三判定点改两判定点;「review 依赖不可用」条款改述为「双镜派发失败/voice 失败」的对应处置(未审待恢复语义不变)。

## Risks / Trade-offs

- [3 声 vs 旧 6-7 声能力等价性不可事前证明] → retro ≥10 轮复评盯 broad 采纳率/独立率,下滑则加声(memo 边角 1;proposal 假设节)。
- [devex 清单首版蒸馏偏差(收多/收漏)] → 与其它领域清单同待遇:retro 数据 + 领域镜 findings 实绩驱动增删,不追求首版完美(通则④)。
- [roadmap voice 无度量锚,效果不可量化] → 四态留痕已够审计;低频场景不建锚体系(memo 边角 2)。
- [消费仓 bundle skew:旧 SKILL(经 symlink 已更新)+ 旧 bundle(未跑 update)] → SKILL 引用的 fold 新 raw 名在旧 contract 无映射 ⇒ emitter fail-closed 非假绿(先例同款);修复=`sdflow-init update`。
- [历史 broad 锚与新 broad 锚语义混读(旧=autoplan 6 声,新=双镜)] → retro 聚合按 raw 名分行呈现,复评时人工可辨;不做数据迁移。

## Migration Plan

1. bundle 资产先行(trigger-catalog TG-28 / devex.md / frontend.md / fold 表 / spec-review.md 等规则文档)+ anchor_lint golden 用例 + retro 测试调整,全仓 pytest 绿。
2. `sdflow-spec-review/SKILL.md` 重写 Step1/Step2 为单批 dispatch;删 guard 调用步与 gstack-review.md 环节;`sdflow-roadmap/SKILL.md` 换 review 执行体。
3. `outside_voice_guard.py` + 其测试删除(退役腿最后动,前两步绿后执行)。
4. 文档 sweep(P2)。
5. 发布:push → 运行 checkout pull + `bash setup.sh`(SKILL symlink 即时生效;`~/.sdflow/hack/` 无本次改动);消费仓 `sdflow-init update` 拿新 bundle。
6. 回退:revert 本 change(SKILL/bundle 集中改动,git revert 即复原)+ 消费仓再跑一次 `sdflow-init update`;gstack 本身未卸载,恢复复用态无需重装(ADR 0040 记方向性成本)。

## Compliance

遵守 `openspec/rules/doc-authoring.md`(DOC-1:正文即最终态,gstack 演进史只入 ADR 0040 与本 change 归档)、`premise-verification.md`(本 design 引用的脚本行号/枚举/编号均已实际打开核验)、CLAUDE.md 基准 1-5(机械消费点走确定性脚本面;无手搓解析器新增;fold/锚枚举均为有界集合)。无豁免项。

## Open Questions

(无——可延后项均已按边角显式接受并记入 decision-memo)
