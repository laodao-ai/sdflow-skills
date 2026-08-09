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
- 不做 devex 的 code-checklists 侧对应文件(TG-28 首版 spec-review-only,同 TG-27 反向先例;**再入阈值:≥2 份归档 code-review 报告独立出现 devex 类 findings 且 spec 侧 devex.md 未能上游拦住 → 升级补 code-checklists/domains/devex.md**)[spec-review-amendment M22:原「实测需要再补」无判据]。

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

**DD2 广审镜 prompt 契约**。两镜各自 prompt MUST 含:`{change_dir}` 路径、四条通则原文、职责清单、返回结构化 findings(问题/证据 file:line/置信/严重度/建议)、不 AskUserQuestion。**base R 项完整划分〔spec-review-amendment M15:原「等」字例举不穷尽,BASE-08/09/18/22/26/30 无归属——BASE-30 恰是 18 镜漏审事故的元教训〕**:strategy 镜=BASE-01/08/09/10/12/13/14/18/22/26/27/30(计划级:前提/范围/长期轨迹/后悔场景/一致性/清晰度/分解/成本/正文最终态);plan-eng 镜=BASE-05/06/16/17/19/25/28(工程级:架构耦合/错误路径/测试计划/隐藏复杂度/NFR/安全/组件);**默认规则:未列明的既有或未来新增 base R 项归 strategy 镜**(实现时以 spec-quality-base.md 当时的 R 项全集核对一次划分完整性)。两镜清单划分写死在 SKILL 的镜表里,与领域镜的分工线:**base 的 R 项归广审镜,domains/ 的 R 项归领域镜**(原「防重叠 1.4」条款删除,由此分工线替代);**防重叠语义补句〔M15/F-adv5〕**:plan-eng 镜 prompt MUST 含一句「栈特定错误处理/重试熔断(domains 的 BE-04/BE-08 类条目)由领域镜负责,本镜只审跨领域/架构级错误路径」——文件归属线不足以消解话题层重叠。

**DD3 锚与降级**。`step1-broad-review` 锚 mode 枚举 `subagent|main-session`(比照 `sdflow-code-review/SKILL.md:275`):正常=subagent;探针判 `subagents="unavailable"` 时广审镜由主 session 亲做(恒跑守卫,mode=main-session),`mirrors=` 计入 `broad` token(合法降级,不触发 dead-fanout,`anchor_lint.py:674-676` 现行为已支持);`host=unknown`(不 fan-out)时广审同走主 session 亲做,mode=`main-session`〔spec-review-amendment M24:原文未定义此路径取值〕。**诚实边界〔M24〕**:mode 值为主 session 自报、guard 退役后无机械枚举校验(anchor_lint 对 step1 锚仅验存在性,与 code-review 层同口径)——mode 的消费者是人读复盘,非机械门,MUST NOT 声称有机械保证。gstack-review.md 与 `mode="native|simulated"` 枚举、outside_voice_guard 调用步整体删除。`outside-voice` 锚的 `guard=` 字段随守卫退役从新锚文法移除——`anchor_lint.py:555` 明确 MUST NOT 解析该字段、declared-sites 判据也不用它(仅人读死字段);归档旧锚不迁移,lint 不解析故无兼容问题。

**DD4 fold 表直接替换**。`lens-metric-contract.md` fold 块 `autoplan-ceo/design/eng/dx: broad` 四行替换为 `strategy: broad` + `plan-eng: broad`(直接替换不共存,同 `gstack-adv→scope-audit` 先例);归档报告旧 raw 名不迁移,聚合器按 unknown 处置。

**DD5 retro 标签解析:旧前缀保留识别、新轮次停产**。`sdflow-retro` 的步类型解析继续识别历史 `checkpoint(spec-review-autoplan)` 标签(归档 change 复盘需要),SKILL 侧不再产生;测试断言相应调整(识别历史 + 不要求新产)。备选「解析器删除该前缀」被砍:会让 49 个已归档 change 的阶段墙钟归类漂移。

**DD6 devex 蒸馏范围(TG-28 + domains/devex.md)**。TG-28 触发条件:「变更**新增/修改/重命名/废弃/删除** developer-facing 交付面——CLI 命令/flag/公共 API/SDK/skill 调用契约/配置面(消费方可见的配置键与默认值,不含纯仓内实现配置)/错误信息文案」〔spec-review-amendment M17/K-6:补删改废动作(最需 DX 审的动作)+「配置面」定义收紧〕;领域列 `devex`(spec-review-only,见 Non-Goals)。**本仓(产品即 skill/CLI)预期 TG-28 近乎轮轮命中,属预期而非过触发——消费仓(业务代码库)才体现条件触发收益**〔M17/D-2:显式记录,防未来按「过宽」误收窄〕。devex.md 条目 MUST 采用可判表式:每条 `ID / 触发条件 / 必需文本证据 / PASS / FAIL / N.A 判据`,证据找不到时输出 `UNVERIFIABLE`(MUST NOT 脑补 PASS)〔M17/K-5〕。收录条目(只收 spec 级可判项):TTHW 分档基准(<2min champion / >10min red flag,**判定 MUST 附文本推导规则:从 design/README 的 quickstart/onboarding 段数步骤/命令数,按固定每步时间假设折算并标注「估算」,MUST NOT 无方法拍数字**〔M17/D-5:失去 persona/竞品接地后须给推导规则〕)、错误信息三件套(problem+cause+fix,须引用确切错误文案与触发条件)、命名可猜性/默认值合理性/渐进式披露(须列新增 surface 与相邻既有命名对照)、升级路径(废弃警告/迁移说明,须含 from/to 与混版本行为)、Claude Code Skill DX 清单(description 触发精度/自包含性/降级路径可读性——**此子清单为按 sdflow skill 形态新作,非蒸馏**〔spec-review-amendment M16:gstack 原 8 项清单(AskUserQuestion 设计/状态存储/渐进同意等)面向有状态 skill 生态,与 sdflow 无状态编排器形态不匹配,原「蒸馏」出处声明不实〕)。**不收**:persona 拷问/共情叙事/竞品 WebSearch 基准/DX Scorecard 趋势(取证式过程方法论,依赖 gstack 家目录生态,非清单项)。frontend.md 增补:litmus 精华(首屏品牌可辨/卡片必要性/去装饰仍显高级)+ AI-slop 黑名单浓缩(紫渐变/图标圆圈三列/全局居中/装饰 blob/emoji 当设计元素)为 R 项。
**分类判据(收/不收)**:一条内容进 devex.md 当且仅当它是「对着 design/specs 文本可判真伪的检查项」;需要跑外部工具、查竞品、或依赖 `~/.gstack/` 状态的过程方法论一律不收。

**DD7 roadmap sync voice 落法**。site 名 `roadmap-voice`;context = `design.md`「Decisions」+ `roadmap.md` 全文(超 200KB 收敛,同全量 diff 截断纪律;**task-log 有意不入 context——整体 plan 契约由双镜承载,voice 是补充第二意见维度,控制出境体积**〔spec-review-amendment M19/X-8:显式记录排除理由〕);run 目录 `openspec/roadmaps/{name}/.outside-voice/<run-id>/`(`.gitignore` 的 `**/.outside-voice/` 递归覆盖,已验);**voice 与双镜重叠启动**(双镜派出后立即前台跑 voice,墙钟≈max(双镜,voice) 而非相加)〔K-3〕;前台 exec `--timeout 300`(沿 helper sync 分支既有常量——roadmap context 量级小于全量 diff,300s 足;不接 `outside-voice.async-timeout-seconds` 键,该键契约限定 async 两路径〔M19/adv2-F6〕)外层 ≥330000ms,退出码按 ⑦ 表映射;失败同族 fallback 只读子代理(带时间预算,超时按双败落「未审待恢复」,见 roadmap delta)〔M12〕;findings 进 task-log「Review 处置」四态,**一行留痕 runner/reason_code(同族降级含「降级」字样),不落 anchor_lint/lens-metric 锚**。roadmap 的双镜 prompt 引用 spec-review SKILL 的镜定义段(职责清单同源),差异仅评审对象声明(三件套整体 plan 话术,C7 契约保留)——**引用机制的具体形态(prose 引用 vs 同源复制+机械等值守)见评审报告决策登记区 Q2,拍板后落**。

**DD8 roadmap SKILL 结构改动面**。判定点②(review 分档)整节删除,判定留痕总则从三判定点改两判定点;「review 依赖不可用」条款改述为「双镜派发失败/voice 失败」的对应处置(未审待恢复语义不变)。

## Risks / Trade-offs

- [3 声 vs 旧 6-7 声能力等价性不可事前证明] → retro ≥10 轮复评盯 broad 采纳率/独立率,下滑则加声(memo 边角 1;proposal 假设节)。
- [devex 清单首版蒸馏偏差(收多/收漏)] → 与其它领域清单同待遇:retro 数据 + 领域镜 findings 实绩驱动增删,不追求首版完美(通则④)。
- [roadmap voice 无度量锚,效果不可量化] → 四态留痕已够审计;低频场景不建锚体系(memo 边角 2)。
- [版本 skew 窗口] → 真实部署模型(adr/0039):SKILL 软链与全局 canonical 同指运行 checkout 同一棵树,`git pull` + `bash setup.sh` 同代翻转,Unix 下无「SKILL 新 bundle 旧」的持续错代;残余窗口仅 Windows(SKILL 为 copy 快照)与 pull↔setup 之间的短暂间隙——期间新 SKILL 若遇旧 fold 表,emitter 对旧 raw 名 fail-closed 非假绿,错误文案指引「回运行 checkout 跑 `bash setup.sh`」(该文案已正确;`anchor_lint._MIRRORS_UPGRADE_HINT` 的失效指引 `sdflow-init update` 一并修,tasks 1.6)。[spec-review-amendment M3:原表述基于已退役的「消费仓持有 bundle 副本经 update 刷新」模型]
- [历史 broad 锚与新 broad 锚语义混读(旧=autoplan 6 声,新=双镜)] → **机械不可分辨——emitter 在落锚时已把 raw 名折叠为 canonical `lens="broad"`,锚行与聚合器均无 raw 维度**(lens_metric_emit.py:202 / lens_metric_aggregate.py 分组键核验);接受此盲区,复评窗口按**本 change 归档日期**切分:D1 的 ≥10 轮复评 MUST 只统计归档日期晚于本 change 的轮次(逐份报告按日期筛选),MUST NOT 与旧结构轮次混算平均;不做数据迁移、不为此升 v2 加代际字段(低频人工动作,完美成本过高)。[spec-review-amendment M2:原「retro 聚合按 raw 名分行呈现」与代码不符,该错误同时出现在 decision-memo 边角 4(「聚合器按 unknown raw 处置」混淆 emit 时与聚合时——归档锚行已是 canonical,fold 表变动不影响历史行),memo 为相位 B 冻结产物不回改,以本条为准]

## Migration Plan

1. bundle 资产先行(trigger-catalog TG-28 / devex.md / frontend.md / fold 表 / spec-review.md 等规则文档)+ anchor_lint golden 用例 + retro 测试调整,全仓 pytest 绿。
2. `sdflow-spec-review/SKILL.md` 重写 Step1/Step2 为单批 dispatch;删 guard 调用步与 gstack-review.md 环节;`sdflow-roadmap/SKILL.md` 换 review 执行体。
3. `outside_voice_guard.py` + 其测试删除(退役腿最后动,前两步绿后执行)。
4. 文档 sweep(P2)。
5. 发布:push → 运行 checkout `git pull` + **立即** `bash setup.sh`(SKILL 软链与全局 canonical 同树同代翻转;`~/.sdflow/hack/` 无本次改动);消费仓**零动作**——规则/tools/contract 经全局 canonical 实时解析(adr/0039),`sdflow-init update` 只在需要刷新 WORKFLOW-GUIDE/托管区块时跑,与本 change 生效无关。[spec-review-amendment M3]
6. 回退:revert 本 change(SKILL/bundle 集中改动,git revert 即复原)+ 消费仓再跑一次 `sdflow-init update`;gstack 本身未卸载,恢复复用态无需重装(ADR 0040 记方向性成本)。

## Compliance

遵守 `openspec/rules/doc-authoring.md`(DOC-1:正文即最终态,gstack 演进史只入 ADR 0040 与本 change 归档)、`premise-verification.md`(本 design 引用的脚本行号/枚举/编号均已实际打开核验)、CLAUDE.md 基准 1-5(机械消费点走确定性脚本面;无手搓解析器新增;fold/锚枚举均为有界集合)。无豁免项。

## Open Questions

(无——可延后项均已按边角显式接受并记入 decision-memo)
