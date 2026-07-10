---
ship-gate:
  code_review: pass
---

## code-review 报告 — matt-workflow-integration

> DIFF_BASE=`979da42`（merge-base main..HEAD），39 文件 +3095/-19。评审时点：实现 10/10 任务后（gate RUN_CODE_REVIEEW→本审）。
> 结论（人读）：**pass**——26 条 canonical findings，21 采纳全部当场修复〔impl-review-fix〕（含 1 致命 7 高），4 裁掉（附理由），1 defer（T128）；修复后仓级 pytest 877 全绿。

### 命中范围

- 栈：纯 Markdown 编排 + Python stdlib 脚本——domains 清单（backend·go/embedded/frontend）不命中，领域镜位由 **base 清单镜**（CR-01~09 通用）承担。
- 镜配置：base 清单镜×1（中档）+ 对抗镜×2（中档：机械层运行期 / 编排规则层）+ 历史镜×1（弱档）+ outside-voice codex×2（code-voice 全量 diff + hr-tg 领域切片）。
- trivial_shape 免除判定：**未跑判器即按 NOT_EXEMPT 处理**——diff 命中行为面路径（SKILL.md/workflow.md/scripts），肉眼即判有逻辑面，照常全量 fan-out（保守向，无静默免）。
- gstack/review（Step1 并入，原生执行·G2 适配不弹窗；Codex 侧审查由本编排 Step2.5 outside-voice 承担，避免双 codex——与 spec-review C2 复用守卫同理）：
  - **Scope Check: CLEAN**。Intent = superpowers-plan 10 任务（tasks.md 20 项映射）；Delivered = 10 任务全落 + change 流程产物（四件套/评审报告为 pre-plan 阶段合法产物）。说明 1：`openspec/workflow/{lens-metric-contract.md,tools/anchor_lint.py,tools/lens_metric_emit.py}` 3 文件为 task6 `init.py update --dev` 托管刷新带入的 bundle 追平文件（init.py:161 注释明确契约须与 tools/ 同批刷新），非本 change 语义改动、非并行 change 产物——update --dev 越界灌入的 43 个规则副本已按仓约定当场清理（先例 b013172），`openspec/workflow/` 只保留 tools/ 的不变量已复核。说明 2：issues/roadmap 文件改动 = 圈选池批次赋值（pre-plan）+ task9 Phase C 占位（in-plan）。
  - **完成度：10/10 任务 DONE**（checkpoint 标签通道 + 复选框通道双齐；plan 复选框已同步勾至 50/51）。唯一悬项 = Task 10 Step 4「运行 checkout 还原」，**按计划后置到 merge+push 后执行**（发布边界步，用户已授权自动 push+upgrade），hand-off 将记录执行结果——非缺口，PARTIAL-by-design。
<!-- sdflow:step1-broad-review v1 mode="native" -->

- **HR-TG 判定：命中**（沿 spec-review 先例，代码 diff 实证同两面）→ 已单开 hr-tg cross-model。
<!-- sdflow:hr-tg v1 hit="TG-06,TG-08" evidence="plan 外衣为 gate/implement/ship 三方共享解析契约且实证口径分歧（frontier 对 fenced 伪 Task 判 2 9、gate 判 {1,2,3}）；matt 套件跨 skill 运行时依赖未 pin" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="none" findings="3" truncated="true" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" runner="codex" reason_code="none" findings="2" truncated="false" -->

### Findings（置信 ≥80，全部已裁决；采纳项全部当场修复〔impl-review-fix〕）

机械层（`sdflow-implement/scripts/impl_route.py` + tests，修复后 61 用例全绿）：

| # | 严重度 | 问题 | 证据 | 命中镜 | 处置 |
|---|---|---|---|---|---|
| M1 | 高 | frontier 解析不 fence-aware：fenced 伪 `### Task 9:` 被计真任务且污染分段（gate 判 {1,2,3}、frontier 判含 9，实证 `--done 1`→`2 9`） | impl_route.py:30,158 vs ship_gate.py:584-611；fixture tickets_plan_fenced_header.md | 对抗A+code-voice+hr-tg（三源收敛） | 已修：fence-aware 逐行扫描（口径同 gate）+ 悬空 fence→TopoError + golden fixtures 跨脚本回归 |
| M2 | 高 | Blocked-by 缺失/小写/全角冒号静默 fail-open 成「无依赖」，拓扑保护形同虚设 | impl_route.py:31,153-186（实测三变体均吞） | 对抗A+code-voice+hr-tg | 已修：每段恰一条 canonical 声明，缺失/重复/疑似变体→TopoError exit 6 |
| M3 | 高 | 未闭合引号 `"tickets` 被兜底成合法值，绕过「损坏 marker→停」 | impl_route.py:50（原 _extract_scalar） | code-voice | 已修：损坏标量 config→unknown-value 诊断、marker→RouteStop |
| M4 | 高 | BOM 不剥离→「有 frontmatter」误判「无」→ marker 静默锁错管线（永久误路由无报错） | impl_route.py:112 vs ship_gate.py:308 | 对抗A | 已修：两读点统一剥 BOM |
| M5 | 中 | `impl-pipeline :`（冒号前空格）被当键不存在，诊断信息缺失 | impl_route.py:27,83 | 对抗A | 已修：`^impl-pipeline\s*:` 容忍匹配后进值校验 |
| M6 | 中 | TASK_HEADER_RE 比 gate TASK_TITLE_RE 宽松（`###Task`/双空格两边判不同任务集） | impl_route.py:30 vs ship_gate.py:483 | 对抗A | 已修：收紧为逐字同款 `^### Task (\d+):` |
| M7 | 中 | 测试缺口：fence/BOM/键变体/Blocked-by 变体全裸奔，跨脚本一致性无回归 | test_impl_route.py（原 30 例） | 对抗A+code-voice+hr-tg+清单镜(CR-09) | 已修：+31 用例（61 总），含 golden fixtures 跨脚本断言 |
| M8 | 低 | 4 处硬编码 `return 6` 无具名常量（与 gate EXIT_UNKNOWN 隐性耦合） | impl_route.py:268 等 | 清单镜(CR-08) | 已修：EXIT_ROUTE_STOP=6 + 手动同步注释 |

编排/规则层（SKILL.md ×2 + ff-generation-constraints.md）：

| # | 严重度 | 问题 | 证据 | 命中镜 | 处置 |
|---|---|---|---|---|---|
| O4 | **致** | design 失败模式表承诺的「逐 ticket 核对双信号、单边缺失补齐」未落 SKILL.md——「勾框已写、checkpoint 未打」半态被 gate 工作树直读通道计 done，未审 ticket 混过 resume | sdflow-implement/SKILL.md（原 :193-206 无核对指令）；ship_gate.py:614-618,744 | 对抗A | 已修：resume 双信号核对段（勾框无标签→撤勾+剔除 done 集+续审；宁重复审不假阳） |
| O1 | 高 | CONTINUE_IMPL 无字面 route 命令 +「marker 在但非法」第三态未覆盖，弱模型可绕过 fail-closed | sdflow-ship/SKILL.md:29 | 对抗B | 已修：字面命令+零内存声明+exit 6 三态齐全（两处路由调用均适用） |
| O2 | 高 | spec-review 采纳项 F10a（起手检查升级语义能力集）半漏且报告称已修——假绿 | SKILL.md 原 :60-63 仅目录存在判 | 对抗B | 已修：目录+SKILL.md description 语义关键词轻核验，不符显式停 |
| O3 | 高 | 「落盘即返回」节在 checkpoint 节之前，「立即返回」祈使语气诱导跳过强制 checkpoint（与 adr/0017「不依赖捎带自愈」矛盾） | SKILL.md 原 :131-147 | 对抗B | 已修：合并为「写盘→checkpoint→返回」显式三步序列 |
| O5 | 中 | SHIPPED 摘要 pipeline 字段在纯 resume 场景无来源，弱模型会猜 | ship SKILL.md:43 | 对抗B | 已修：未回显 receipt 则先补跑 route，禁猜测 |
| O6 | 中 | DONE_WITH_CONCERNS「逐字附两轴」与「一行摘要」上限矛盾，取全文支路缺失 | SKILL.md :171-180 | 对抗B | 已修：读 report file Concerns 节取全文 |
| O7 | 中 | 执行模式无起手依赖复核（出 ticket 与执行跨会话，红线只护半场） | SKILL.md :149 起 | 对抗B | 已修：执行模式起手同款语义源复核 |
| O8 | 中 | fix→re-review「循环直至通过」无熔断（全仓唯一无熔断循环） | SKILL.md :233-235 | 对抗B | 已修：同一发现连续 2 轮未消解→T10/停上抛 |
| O10 | 中 | wayfinder 回链锚无具体格式 + 与切片建议「ticket」撞词→grill 瘦跑误判面 | ff-generation-constraints.md 新节 | 对抗B | 已修：`wayfinder-resolved:` 固定前缀样例 + 切片建议节禁用该前缀 |
| O9 | 低 | fix 轮 implementer 报告复用同路径覆盖首轮，丢审计轨迹 | SKILL.md :171 | 对抗B | 已修：`-fix<轮次>` 后缀 |
| O12 | 低 | matt 套件 Claude-only 范围收窄未显性声明（Codex 宿主开 tickets 键会撞无因显式停） | SKILL.md :61；setup-matt-pocock-skills 全文无 Codex | 对抗B | 已修：起手检查节声明已知范围收窄 |
| O13 | 低 | 试验期权威声明埋千字散文中（design 自认已知债） | ship SKILL.md:29 | 对抗B | 已修：整句加粗（最小改动） |
| S2 | 低 | Task 10 Step 4（运行 checkout 还原）为 post-push 悬项 | plan Task10 | broad(Step1) | 采纳：push 后立即执行 /sdflow-upgrade + readlink 验证，hand-off 记录 |

### 已裁掉（反静默压制，可审计）

- X1〔对抗A/清单镜〕未捕获异常（如 PermissionError）以 exit 1 而非 6 逸出——裁掉：调用方契约为「非 0 → UNKNOWN 停」，行为在契约内，仅错误信息友好度差；两镜自判可接受。
- X2〔对抗B-11，中〕与 rebuild-sdflow-roadmap-v2「不相交」论证薄弱、疑似同改 wayfinder 入口判据——裁掉（主审核实）：rebuild 的 R3 双判据落点是 `sdflow-roadmap/SKILL.md`（roadmap 讨论层），本 change 三段分流落点是 `workflow.md` 阶段一（mainflow），**物理文件不相交**；且两者判据同源同一拍板（F11 事中触发、禁事前轮数预估），语义一致非冲突。已在串行实施线 2 时列为一致性核对项（见收尾提示）。
- X3〔清单镜 scope 观察〕task6 checkpoint 捎带 3 个 openspec/workflow 文件疑似他 change 产物——裁掉（主审 ground truth）：为 `update --dev` 托管刷新的 bundle 追平文件（init.py:161 契约同批刷新），已在 Step1 scope 说明中记录，非 drift。
- X4〔清单镜，很低〕test_impl_route.py 用 sys.path.insert 而非 importlib 按路径加载，与 golden 测试风格不一——裁掉：模块名仓内唯一、877 全绿无冲突；风格统一属美化，不值本轮改（若未来撞名再改）。
- 置信 <80 滤除项：无（本轮全部 findings 均有 file:line 实证，最低置信项即 X4，已上列）。

### 修复 / defer 台账

- 自动修 **21** 项〔impl-review-fix〕：机械层 8（impl_route.py + 31 新用例）+ 编排层 12（SKILL.md×2 + ff-generation-constraints.md）+ S2（流程排期项，post-push 执行）。
- defer **1** 项 → todolist **T128**（receipt marker 显示折叠，display-only，JSON 显式带 change=matt-workflow-integration）。
- T10复核: 无「无客观判据的 ≥2 方案」项——全部修复均有测试/grep 客观判据，无需对抗镜复核自动选。
- 修复后验证：`python3 -m pytest` 仓级 **877 passed**（sdflow-implement 61 / sdflow-ship 163，golden 跨脚本回归含 fenced/dangling fixtures）；手工复核 frontier 对 fenced fixture 输出 `2`（不含 9）、dangling fixture exit 6。

### 度量锚（lens-metric）

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="—" findings="20" 采纳="18" 裁掉="2" defer="0" 独立="15" sev="致1/高6/中8/低3" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="claude" site="—" findings="2" 采纳="1" 裁掉="1" defer="0" 独立="1" sev="致0/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="—" findings="6" 采纳="2" 裁掉="3" defer="1" 独立="1" sev="致0/高0/中1/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="code-voice" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="1" sev="致0/高3/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="hr-tg" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="0" sev="致0/高2/中1/低0" -->

（emitter 确定性归约产出，exit 0 落锚；分类正确性/roster 完备性/誊写准确仍是主 session 信任边界。历史镜 findings=0 为真实值——其结论「无重蹈/无覆盖历史修复/无 revert」是排除性价值，锚计数天然不体现。聚合与复评归 /sdflow-retro，本报告只落锚。）

### 结论

☑ **建议进 /sdflow-done**（verify → hand-off → archive → commit → merge）。defer 残差已入 todolist（T128，hand-off 将引用）。
串行提示（供线 2）：rebuild-sdflow-roadmap-v2 实施时核对其 sdflow-roadmap/SKILL.md 讨论层判据与本 change workflow.md 三段分流的措辞一致性（同源 F11，见 X2 裁决）。
