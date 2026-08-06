### Task 3: 代码审 Step1 改为自持 scope 审计，全 SKILL 去 gstack 依赖

**Blocked-by:** none
**R-ID:** SW-1, SW-2, SW-3, HAE-1

代码审编排器的第一步不再借道第三方 skill 的原生执行，而是自己派一个 fresh 中档子代理，
以本 change 目录的四件套为确定性意图源，做 scope-drift 与完成度两轴审计——意图不再靠
commit message 猜。审计产出逐 task 五态表（DONE / PARTIAL / NOT DONE / CHANGED /
UNVERIFIABLE，DONE/CHANGED 也在表内）与负向态 findings，findings 汇入既有合并池按普通
finding 走裁决，不设门、不向用户提问。

能力探针的位置随之上移到第零步、每轮恰一次，Step1 与 Step2 共用同一次结果；探针判不可用时
Step1 由主 session 亲做，并在报告显著标注存在自查偏置。`trivial_shape` 判 EXEMPT 时本步照跑，
且审计一旦揭出隐藏逻辑即作废 EXEMPT——因此 EXEMPT 候选形状下的免除判定必须等 Step1 结果，
不能与之并行。

Step1 的执行位如实写进 `step1-broad-review` 锚的 mode 值（新枚举 `subagent|main-session`），
度量侧的原始镜名改用 `scope-audit`（只出现在 findings 的 hits 里，roster 行仍是 canonical
`broad`）。SKILL 的 skew 探测段要能在起跑前发现「本 SKILL 已是新版、但本仓 bundle 还是旧版」
这个高发方向，而不是让整轮 fan-out 跑完在末步 lint 才炸。

同一票内还落两条产出纪律：Step2 各镜的 finding 必须引出触发行原文或等价的可复核证据包，
引不出则自报置信封顶 50；Step3 置信过滤据此把它们滤出主结论并在「已裁掉」区留一行痕迹，
另扩两条明确滤除类目。

本票收尾时，本 SKILL 正文里不得再有任何 gstack 提法——包括分工表、报告格式区、命中范围行。

- [ ] `grep -n "gstack" sdflow-code-review/SKILL.md` 无输出（严格归零，不留「历史注记」豁免）
- [ ] Step1 描述为恒跑 fresh 中档子代理的 scope 审计，输入明列 proposal/tasks/design + `DIFF_BASE..HEAD` diff，且要求 prompt 原文携带四条通则区块与「不 AskUserQuestion」声明
- [ ] Step1 审计两轴写明：scope-drift（出圈改动逐条列 SCOPE CREEP，Non-Goals 被实现算 creep）+ 完成度五态，且五态判定纪律逐条钉死（DONE 从严 / CHANGED 从宽 / UNVERIFIABLE 诚实 / PARTIAL=部分子项有 diff 内证据 / NOT DONE=diff 内无任何相关证据）
- [ ] Step1 产出含逐 task 五态表（DONE/CHANGED 也在列）+ 负向态 findings，并明写不勾 tasks.md、不替代 verify 终审、Step4 自动修后复审一轮纳入 scope-drift 维度
- [ ] 能力探针段落位于第零步（与档位解析同位），文中声明 Step1/Step2 共用同一次探针结果、`fanout-capability` 锚每轮恰一条
- [ ] 并行边界写明：EXEMPT 候选形状下 Step2 免除判定阻塞等 Step1 结果，非白名单形状才并行
- [ ] 降级分支写明主 session 亲做 + 报告显著标注「⚠️ scope 审计降级（存在自查偏置）」；恒跑守卫（EXEMPT 时照跑、揭出隐藏逻辑则 EXEMPT 作废）语义保留
- [ ] 锚 mode 枚举为 `subagent|main-session`
- [ ] 报告格式区：mirrors 说明含 `broad` token；lens-metric 的 `findings[].hits[].raw` 用 `scope-audit`，roster 行仍写 canonical `lens="broad"`
- [ ] 领域镜选择段含一行 `TG-27 → domains/llm.md`
- [ ] skew 探测段追加两个新信号（contract 折叠块含 `scope-audit:` 行；anchor_lint 支持 `broad` token），任一探不到沿用既有「硬停 + 提示先跑 `sdflow-init update`」文案
- [ ] Step2 子代理 prompt 模板含引文纪律全文（含非局部 finding 的可复核证据包替代路径），并声明「产出纪律非机械门」
- [ ] Step3 置信过滤含「既无引文又无证据包 ⇒ 置信上限 50 ⇒ 落已裁掉区一行留痕」，明确滤除类目扩两条 Suppressions（阈值/常量不强制求注释；无害冗余助可读性不标）
- [ ] `sdflow:principles` / `sdflow:tier-resolution` / `sdflow:async-branch` 托管区块字节级未变

