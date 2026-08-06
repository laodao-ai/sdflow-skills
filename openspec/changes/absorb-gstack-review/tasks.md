## 1. Step1 自持化（P0 · SKILL.md）

- [ ] 1.1 重写 `sdflow-code-review/SKILL.md` 第一步：删除 gstack/review 原生执行与 simulated 降级分支，替换为 fresh 子代理 scope 审计协议（输入 = proposal scope/Non-Goals + tasks.md + design.md + `DIFF_BASE..HEAD` diff；prompt 原文携带四条通则 + 「不 AskUserQuestion、返回结构化 findings」）。**〔spec-review-amendment〕时序同步重排：能力探针段从第二步挪至第零步（与 tier-resolution 同位、每轮恰一次，Step1/Step2 共用同一次结果，fanout-capability 锚仍每轮恰一条）；dispatch 并行边界 = EXEMPT 候选时 Step2 免除判定阻塞等 Step1 结果、非白名单形状才并行**〔Req: spec-workflow·sdflow-code-review 为每次全跑的独立强制主审〕
- [ ] 1.2 SKILL 第一步写入审计两轴指令：scope-drift（diff ↔ proposal scope 出圈比对，Non-Goals 被实现算 creep）+ 完成度五态（DONE 从严 / CHANGED 从宽 / UNVERIFIABLE 诚实 / **PARTIAL=部分子项有 diff 内证据、NOT DONE=diff 内无任何相关证据**，判定纪律逐条写明）；**产出含逐 task 五态表（DONE/CHANGED 也在列）+ 负向态 findings；明写不勾 tasks.md、不替代 verify 终审；Step4 自动修后复审一轮纳入 scope-drift 维度**〔spec-review-amendment〕〔Req: 同上·五态 Scenario〕
- [ ] 1.3 SKILL 锚更新：`step1-broad-review` mode 枚举改 `subagent|main-session`（如实记执行位）；降级分支 = host=codex 探针 unavailable → 主 session 亲做 + 报告显著标注「⚠️ scope 审计降级（存在自查偏置）」；恒跑守卫（trivial_shape EXEMPT 时照跑、揭出隐藏逻辑则 EXEMPT 作废）原语义保留〔Req: 同上·降级 Scenario〕
- [ ] 1.4 SKILL 报告格式区同步：「命中范围」行删 gstack 提法；能力探针段 mirrors= 说明扩 broad token；lens-metric **findings 的 `hits[].raw`** 改 `scope-audit`（roster 行保持 canonical `lens="broad"` 不变——契约 schema 禁 raw 名进 roster〔spec-review-amendment〕）；**领域镜选择段加一行 `TG-27 → domains/llm.md`（防 llm.md 注册表孤儿）**〔spec-review-amendment〕；「与 gstack/review、官方 code-review 的分工」表改写为吸收后定位（DOC-1：正文即最终态，不留考古层）

## 2. 机械消费点同步（P0 · contract / anchor_lint / prompt）

- [ ] 2.1 `sdflow-init/assets/workflow/lens-metric-contract.md`：`lens-metric-fold` 机读块 `gstack-adv: broad` 行替换为 `scope-audit: broad`；折叠表 prose 同步改述〔Req: workflow-metrics·度量锚契约〕
- [ ] 2.2 `sdflow-init/assets/workflow/tools/anchor_lint.py`：mirrors 合法 token 集扩 `broad`；dead-fanout-multi-mirror 计数集维持不变（broad 不入）。**〔spec-review-amendment〕当前 `_FANOUT_MIRRORS`（:674）单常量同时充当合法集（:694 _parse_mirrors）与计数集（:765 check_fanout_consistency）——MUST 拆成两个独立常量（如 `_MIRRORS_LEGAL` 含 broad / `_FANOUT_MIRRORS` 计数用不含 broad），直接往原常量塞 broad 会污染计数集**〔Req: host-adaptive-execution·子代理不可用时镜数如实降级〕
- [ ] 2.3 anchor_lint golden 测试四用例：mirrors 含 broad 合法；unavailable + `broad,history` 不触发 dead-fanout；unavailable + `broad,domain,history` 仍触发；**step1-broad-review 锚 `mode="subagent"` 通过（锁定「lint 不校验 mode 值」不变量，防未来误加校验）**〔spec-review-amendment〕〔Req: 同上·unavailable 时 mirrors 含 broad Scenario〕
- [ ] 2.4 `sdflow-init/assets/workflow/prompts/step8-code-review.md` 提示词删 gstack 提法 + 同步 `hack/tests/test_workflow_split.py` needle 断言（新 needle 措辞对齐「自持 scope 审计」提法，实现时与 5.1 的 workflow.md 改述一致）〔Req: proposal·机械消费点同步〕
- [ ] 2.5 〔spec-review-amendment〕skew 探测新信号 + 可操作报错：SKILL「skew 探测」段追加两信号（contract `lens-metric-fold` 块含 `scope-audit:` 行；anchor_lint 支持 `broad` token），任一探不到 ⇒ 既有「硬停 + 提示 `sdflow-init update`」文案；`lens_metric_emit.py` 未知 raw 名与 `anchor_lint.py` mirrors-unknown-token 两处报错文案追加「若本仓 openspec/workflow/ 为旧版，请先跑 `sdflow-init update`」指引（+ 对应测试断言）〔Req: spec-workflow·主审恒跑（fail-loud 纪律）〕

## 3. checklist 吸收（P1 · code-checklists）

- [ ] 3.1 `code-review-base.md` 新增 CR-10（命令/代码注入：shell 串插值→参数数组；eval/exec 执行模型或外部输入生成的代码须沙箱/白名单）、CR-11（枚举/取值完备性：新值逐消费者 trace **必须读 diff 外代码**、allowlist 数组核对、case 链 fall-through）——语言无关措辞 + 括号多语言示例〔Req: proposal·checklist 吸收；ID 纪律新号不复用〕
- [ ] 3.2 `domains/backend.md` 新增 CR-BE-03（DB 层竞态：find-or-create 无唯一索引 / check-then-set 原子 WHERE / 状态迁移非原子 / 绕过模型校验直写）；CR-BE-02 检查点追加 XSS/不安全 HTML 渲染〔Req: 同上〕
- [ ] 3.3 新建 `domains/llm.md`（CR-LLM-01 输出信任边界：持久化/外发前格式与 shape 校验、URL allowlist 防 SSRF、入库防存储型 prompt 注入；CR-LLM-02 prompt 一致性：1-indexed、工具声明与 wiring 一致、限额单一声明）+ `README.md` 注册表加行〔Req: 同上〕
- [ ] 3.4 `trigger-catalog.md`：领域清单段加 TG-27 行（LLM 集成面，触发措辞=「代码消费 LLM/agent 产出并持久化/执行/外呼」，**例证删「锚行 parse」并附排除句：评审工作流自身读自报控制面锚不算、只有外部/不可信 LLM 产出才算；行内注「code-review-only domain」**〔spec-review-amendment〕）；HR-TG 成员行追加 `TG-27`（hr_tg_intersect.py 动态 parse 零代码改动，跑一次脚本验证成员 parse 正常）〔Req: proposal·TG-27〕
- [ ] 3.5 〔spec-review-amendment〕`code-checklists/README.md`「选用规则」示例块同步补 `TG-27 → llm.md` 行（与注册表加行同步，两处一致）〔Req: proposal·checklist 吸收〕

## 4. pre-emit 引文纪律 + Suppressions（P1 · SKILL Step2/3）

- [ ] 4.1 SKILL Step2 子代理 prompt 模板追加产出纪律：每条 finding 附触发行 file:line + 逐字引文（框架元构造引创建处），引不出 ⇒ 自报置信 ≤50〔Req: spec-workflow·代码审 finding 须引出触发行原文〕
- [ ] 4.2 SKILL Step3 置信过滤追加：无引文 finding 置信上限 50 → 滤出主结论、已裁掉区一行留痕；明确滤除类目扩两条 Suppressions（阈值常量不强制求注释、无害冗余助可读性不标）；措辞声明「产出纪律非机械门」〔Req: 同上·两 Scenario〕

## 5. docs 同步（P2 · 纯文档）

- [ ] 5.1 `sdflow-init/assets/workflow/workflow.md` 三处（§编排器描述 / §代码侧质量层 / §checklist 勾选项）改述为自持 scope 审计〔Req: proposal·机械消费点同步〕
- [ ] 5.2 `sdflow-init/assets/workflow/reference/quality-layering.md` 相关行（gstack/review 补全 / 并入提法）同步〔Req: 同上〕
- [ ] 5.3 `docs/workflow-skills/`（sdflow-code-review.md 提法更新；gstack-review.md **保留**〔设计门拍板 Q4〕，仅改述为「非运行时依赖的第三方 skill 参考」定位）、`docs/external-dependencies.md`、`docs/workflow-overview.md`、**`docs/workflow-console.html`（:390-526 多处 Step1=gstack 叙述，显式点名防 .html 漏扫**〔spec-review-amendment〕**）**提法更新；本仓 CLAUDE.md 若有 gstack/review 提法一并扫（`grep -rn "gstack" --include="*.md"` 全量核，改共享字符串纪律：不带 --include 限定再扫一次含 .py/.sh/.html）〔Req: 同上〕

## 6. 验证与收尾（P0-P2 共用出口）

- [ ] 6.1 全仓 pytest 绿（`/usr/bin/python3 -m pytest`——含 anchor_lint golden 新用例、test_workflow_split needle、hr_tg_intersect 成员 parse）
- [ ] 6.2 Success Metrics 核验：`grep -rn "gstack" sdflow-code-review/SKILL.md` **严格归零（DOC-1 口径：正文零残留，不留「历史注记」豁免——与 proposal 同步统一）**〔spec-review-amendment〕；`openspec validate --strict` 绿；**「gstack 不在场可跑通」Scenario 以此 grep 归零静态证成（SKILL 无任何 gstack 调用路径 = 无运行时依赖），无须真造缺席环境**〔spec-review-amendment：证明方式显式化〕
- [ ] 6.3 issues 池记三条 todo（用开发 checkout 脚本、显式传 change 字段）：① python.md domain（Async/Sync 混用条目落点）② spec-review 侧 autoplan 姊妹依赖处置 ③ 仓根 `openspec/workflow/` 孤儿副本清理（lens-metric-contract.md / WORKFLOW-GUIDE.md，非 pin 死件、grep 假阳来源）〔spec-review-amendment defer〕
- [ ] 6.4 dogfood：**前置——开发 checkout 跑 `bash setup.sh` 开全局窗口（`readlink ~/.sdflow/workflow` 确认指向本开发树；时间盒操作，测完在运行 checkout 重跑 setup 还原）**〔spec-review-amendment：全局指针现指运行 checkout，不开窗即 dogfood 打在旧代码上假绿〕；然后本 change 自身跑 `/sdflow-code-review`，验证报告产出 `mode="subagent"` 锚 + `scope-audit` raw 名折叠的 broad 行 + anchor_lint 通过

## 测试覆盖图（TG-18）

```
code path                          测试类型
─────────────────────────────      ─────────────────────────────
anchor_lint mirrors token 扩集  →  golden pytest（2.3 三用例）
dead-fanout 计数集不变          →  golden pytest（既有用例回归 + 2.3）
step8 提示词改动               →  needle 断言（test_workflow_split）
trigger-catalog HR-TG 成员行    →  hr_tg_intersect.py 实跑 parse（6.1）
contract fold 块替换           →  lens_metric_emit 既有 fold 测试回归（6.1）
SKILL Step1 行为（子代理/降级/锚）→  dogfood 实跑（6.4，指令层无自动化）
checklists/llm.md 内容         →  人审（markdown 数据资产，无自动化）
```
