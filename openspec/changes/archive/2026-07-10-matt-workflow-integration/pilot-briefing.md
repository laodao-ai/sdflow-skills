# Pilot Briefing — matt-workflow-integration 试点判赢材料

> 归属：tasks 5.1/5.2（plan Task 9）。用途：为 Phase A 试点执行准备判赢框架 + 首个消费仓缺省路径验证证据。
> 本文档只做**材料准备**，不启动任何试点执行——试点 change 的选定与切换归试点期（proposal 假设表①：「试点首 change 即全链实测；跑不通则该 change 改 config 回 superpowers 续跑」）。
> 判据口径源：`design.md` D8（试点 A/B 设计）+ spec-review-amendment F3a 修补项；对照口径与 Success Metrics 表见 `proposal.md`。

## ① 候选池（3-5 个有逻辑面中型项）

从 `openspec/issues/todolist/2026-07-todolist.md` 与两份 roadmap（`mechanical-layer-hardening`、`workflow-cost-optimization`）阶段项中挑选真实存在、当前仍 PROPOSED/未启动的候选——不虚构候选。

| ID/名 | 来源 | 类型 | 一句入选理由 |
|---|---|---|---|
| mlh-P4·4.B `maintain_scan.py`（todolist T79） | `openspec/roadmaps/mechanical-layer-hardening/roadmap.md` 阶段 4 | 基础设施 | INDEX↔文件系统 set-diff 只读报告脚本化（+ CLAUDE.md 过时引用 + bundle 陈旧告警）；2026-07-09 explore 已拍板独立单开一次 change 粒度，判断部分（归哪组/是否修）显式留人，边界清、规模中型（新脚本 + 接入 `sdflow-maintain` + 测试）。 |
| mlh-P4·4.D 小校验器组（todolist T80/T81/T82） | `openspec/roadmaps/mechanical-layer-hardening/roadmap.md` 阶段 4 | 代码质量/可观测性 | 三个同型 `reason_code` 判定小校验器（outside-voice 复用守卫 / HR-TG 交集判定 / roadmap task-log 对账），已拍板三合一单开一次 change；三张票逻辑独立、互不纠缠，是「多 ticket 天然可并行阻塞边」的典型中型样本（本身仍走 tickets 首版严格串行 frontier，只是依赖图天然稀疏，便于观察 frontier 契约表现）。 |
| T63 | `openspec/issues/todolist/2026-07-todolist.md` | 代码质量 | `sdflow-init/scripts/init.py:inject` 多块收敛须 fence-aware + start/end 配对校验（naive collapse 已回退）——单文件解析状态机改造，逻辑面集中（fence 状态跟踪），已有明确失败案例可直接转 TDD seam。 |
| T51 | `openspec/issues/todolist/2026-07-todolist.md`（gate-checkpoint-hardening 批次） | 代码质量 | `sdflow-done/SKILL.md` commit 步暂存策略须与 merge 卫生检查对齐（tracked 非-openspec 改动被 `git add -u` 先提交、绕过 merge 前 untracked 硬检查）——单 SKILL.md 决策逻辑改动，契约点收敛、非纯文档。 |
| T89 | `openspec/issues/todolist/2026-07-todolist.md`（done-roadmap-writeback 批次） | 代码质量 | `roadmap_writeback_draft.py` 的 `probe_format` 全文扫描非限定 phase，混合格式 roadmap 会误判 checkbox——修法为增 phase 参数只扫该 phase 行段；单文件解析逻辑修复，输入输出契约明确。 |

## ② 选样拒绝条件（成文）

三条任一命中即拒绝入样；候选池挑选时已按此三条筛过，以下各附一条本仓真实反例说明口径（非穷举被拒项全集）：

- **纯文档类不入样**：改动只涉及 Markdown 描述性文字、无可测试的行为分支（如 README 表行新增、CHANGELOG 记录、纯措辞同步）。tickets 管线的价值锚（TDD seam + 每 ticket 双轴审）对无逻辑分支的改动是纯开销，判据本不适用。本轮候选池未纳入任何仅涉及 README.md/CLAUDE.md 表述同步类 todolist 项。
- **跨模块宽重构不入样**：单个候选触达面横跨 ≥3 个 skill，或属于「改 N 处写路径 + consumer dual-read + 重写测试套」级别的迁移（expand-contract 例外机制本身仍待试点验证，不能拿宽重构类候选当首批试金石）。反例：`mechanical-layer-hardening` 阶段 6（recorder 索引 → frontmatter，端态 A）roadmap 原文自注「全 roadmap 最大 change（改 3 recorder 写路径 + consumer dual-read 读 + 重写测试套）」——明确排除出候选池。
- **接口高度不确定不入样**：候选的实现路径本身还需一轮设计探索才能定案（即其应产出「如何设计」而非「按此设计实现」）。tickets 出票模式假设 design.md 已有可切片的行为级决策——接口未定会使 3-6 张 ticket 的 tracer-bullet 切分本身沦为空中楼阁。反例：T63 同批次的 T24（`setup.sh install_into` 软链所有权校验）todolist 原文明写「需专门设计『何为自属目标』再修，与 T18（可见性）分立」——排除出候选池。

## ③ 判据三条 + 对照分桶口径（design D8，逐字）

**定性人读拍板，不设数字阈值**（n=3-5，adr/0009 小样本警告）：

1. retro per-change impl 阶段墙钟 Δ 方向性下降。
2. 冷层（`sdflow-code-review`）Critical/严重 findings 与 `sdflow-done` verify FAIL 不升。
3. 护栏哨兵——冷层捕获「本应被每 ticket 审拦住的严重项」占比不恶化；**恶化 = 熔断，停试点、回退 config 键至缺省**。

**对照口径**：retro 30-change 池按同类型分桶的历史基线（change 类型是实证混杂因子，见 memory: test-ratio-by-stack）——每个试点 change 需先归入其类型桶（如「代码质量/单脚本解析修复」「基础设施/新增只读脚本」），再与该桶历史 impl 阶段墙钟中位数对照，禁跨桶比较。

**变量控制**：试验期不叠加降档实验（implementer 档位钉死 mid，见 ⑦）；「plan 含码→最便宜档誊抄」降档通道随预写代码消失而失效，model-tiers 判据重标另议（design D8 逐字）。

## ④ PIPELINE_RECEIPT 逐 change 留档 + 计样前核对

- 每个试点 change 首次 `RUN_PLAN` 时，ship 链序会先跑 `python3 sdflow-implement/scripts/impl_route.py route --root <仓根> --change <change>` 并把整行 `PIPELINE_RECEIPT ...` 回显进对话（Task 3 已落地的链序行为）——该行需摘录进该 change 的 hand-off 或本文档「试点执行记录」追加表（试点期建表，本材料只定格式：change / PIPELINE_RECEIPT 原文 / 核对结论）。
- **计入判赢样本前核对**：receipt 的 `pipeline=tickets` 须与该 change 出票时刻的 config/marker 意图一致——典型不一致场景：config 键在出票后被改动、marker 与 receipt 当次 `pipeline` 字段不符、`config=unknown-value:*` 误落 superpowers 却被误记为 tickets 样本。**不一致 → 该 change 从判赢样本中剔除**（Success Metrics 表「试点样本有效性」原文口径）。
- 核对动作机械：`config=` / `marker=` / `pipeline=` 三字段两两对照 receipt 原文即可，不需模型判断；有疑义（如 receipt 缺失、change 名拼写偏差）一律排除该 change 出样本，不臆测补全。

## ⑤ 观测项（非判据，尽力采集）

与 ③ 的三条判据分离——以下为**观测**，不参与熔断/判赢裁定，仅供 Phase B 立项参考：

| 观测项 | 采集方式 | 备注 |
|---|---|---|
| NEEDS_CONTEXT 停摆率 | 试点期每 ticket 执行的状态词落点统计（DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED 四值中 NEEDS_CONTEXT 占比） | 高停摆率提示「行为级 ticket 文本即 brief」假设（proposal 假设表③）可能不成立 |
| 阶段一上下文成本（T126 关联） | 若试点 change 源于 wayfinder map，记录 ff 起手逐区读 map 的 token/轮次开销 | 仅当 change 走三段分流的 wayfinder 分支时适用；直接 ff 的 change 无此项 |
| token 维度 | 会话侧可见即录（如子代理返回摘要中的 token 用量），不做额外埋点、不阻塞试点推进 | 「尽力采集」= 缺失不算失败，采集不到就留空 |

## ⑥ 试点执行节奏：单变量串行 + retro 再生核对

试点 change **一次只跑一个**（不并行试点，避免多变量互相污染判据①的对照）：

1. 从候选池（①）取一个未试的候选，翻其消费仓 `openspec/config.yaml` 的 `impl-pipeline: tickets` 键，走完整阶段三（RUN_PLAN → CONTINUE_IMPL → 冷层 code-review → done SHIPPED）。
2. 每个候选 **SHIPPED 后**，先跑 `python3 sdflow-retro/scripts/retro_report.py --root .` 再生 `openspec/retro/report.md`，据新数据核对 ③ 判据三条（尤其哨兵③）。
3. 哨兵未恶化 → 记录本次结论（含 ④ 的 receipt 核对结果），再从候选池选下一个继续；哨兵恶化 → **熔断**：停止试点、该 change 及后续候选池项目的 config 键回退缺省（不再新开 tickets 管线试点），已收集材料原样记入判赢材料供设计回炉参考，不因熔断而回填美化数据。
4. 候选池耗尽（3-5 个全试完）或提前熔断，均视为 Phase A 试点收尾——由人读判据三条拍板是否进 Phase B（默认翻转）。

## ⑦ implementer 档位钉死 mid

试验期 tickets 执行模式的 implementer 子代理档位**钉死 mid**，不与降档实验叠加（design D8「变量控制」逐字）——理由：「plan 含码 → 最便宜档誊抄」的降档通道在 tickets 管线下随「禁预写代码」的行为级 ticket 假设消失而失效，若同时变动档位会与判据①②③混杂多个自变量，无法归因墙钟/质量变化来自管线本身还是模型档位；model-tiers 判据重标留待另议（不在本次试点范围内）。

## 消费仓缺省路径验证（Step 2 / tasks 5.2）

**消费仓选定**：`~/Documents/10-michi`（本机已具备 `openspec/config.yaml` 的消费仓，无需换用 `~/Documents/05-sarvelo/mqtt-console`）。

**验证方法**：只读命令，验证前后核对该仓 git 状态零变化。

```
$ grep -n "impl-pipeline" ~/Documents/10-michi/openspec/config.yaml
（无匹配，exit 1 ——确认该仓 config 无 impl-pipeline 键）

$ python3 sdflow-implement/scripts/impl_route.py route --root ~/Documents/10-michi --change probe
PIPELINE_RECEIPT change=probe config=absent marker=absent pipeline=superpowers plan_sha=-
（exit 0）
```

**验证前/后 `cd ~/Documents/10-michi && git status --short`**：均为空输出（clean）——确认本次验证对该仓**零写入**。`impl_route.py` 的 `route` 子命令本身也是只读实现（只 `read_config_pipeline` 读 config 文本行、`read_plan_marker` 读一个不存在的 plan 文件返回 `None`，无任何写路径）。

**结论**：`pipeline=superpowers`，与 ship 链序缺省行为一致——不开 `impl-pipeline` 键的消费仓走阶段三时，`RUN_PLAN` 仍派发 `superpowers:writing-plans`（tasks 5.2 验证条款：「该仓 RUN_PLAN 仍派 writing-plans」）达成；因 `ship_gate.py` 零改动，`RUN_PLAN` emit 提示串本就未变，此结论同时覆盖 gate 侧行为不变的隐含断言。

**试点期归属声明**：本节只验证「缺省路径不炸」这一单点（Task 9 范围），完整阶段三试点执行（含实际 tickets 管线全链跑通、冷层 code-review、SHIPPED）归试点期执行，不在本材料准备阶段发生。
