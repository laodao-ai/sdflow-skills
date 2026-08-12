# Task 5 — 四编排 SKILL 全面适配 + B25 诊断修复 + bundle 同步

**R-ID:** SW-1, SW-2, SW-3, IO-2, HAE-1 · **Blocked-by:** 1,2,3,4（全部已合并进本分支，实查确认）

## (a) B25 诊断：lens_metric_emit.py 未调用（非调用失败）

**方法**：`grep -rl "lens-metric" openspec/changes/archive/` 定位 08-07 起的 6 份归档
`code-review-report.md`（`fix-probe-scan-precision` / `absorb-gstack-autoplan` /
`implement-workflow-optimization-2026-08-{p1,p2,p3}` / `remove-superpowers-pipeline`），逐份 grep
`lens-metric` 锚。

**结果（确定性证据）**：

1. **6/6 归档 code-review-report.md 全部零 `sdflow:lens-metric` 锚**，而同期 `openspec/config.yaml`
   的 `metrics.enabled=true` 自 2026-07-06（`b092591`）起持续为 `true`，未变过——门控条件全程满足，
   不是「metrics 关着所以没落锚」。
2. **对照组（同期 spec-review-report.md）锚齐全**：同 4 份 change 的 `spec-review-report.md`
   分别含 6~8 处 `lens-metric` 出现——证明 `lens_metric_emit.py` 本身、`metrics.enabled` 门控、
   以及"评审 SKILL 落锚"这条机制路径**整体是通的**，故障局限在 `sdflow-code-review` 一侧。
3. **`lens_metric_emit.py` 独立冒烟测试正常**：
   - 非法输入（缺 `outside-voice` 强制行）→ `exit 1` + 清晰报错，未崩溃。
   - 合法输入 → `exit 0` 正确产出 `<!-- sdflow:lens-metric v1 ... -->` 逐行 stdout。
   排除"脚本本体损坏/路径错误"作为直接成因。
4. **关键证物**：`2026-08-12-remove-superpowers-pipeline/code-review-report.md` 已写出
   `### 度量锚` 标题 + `（metrics.enabled=true）` 说明，段内却只有 `sdflow:outside-voice` /
   `sdflow:declared-sites` 两条锚，**唯独缺 `sdflow:lens-metric`**——说明执行者已经"知道"该落
   度量锚（写了标题+条件说明），但**从未实际调用 `lens_metric_emit.py` 这个具体工具调用**，也
   从未跑旧 SKILL.md 规定的「锚行自检」（`anchor_lint.py`——若真跑过，脚本会因 `metrics_on` 时
   缺 `lens-metric` 锚判 `VIOLATION`、退出非 0，SKILL 旧文按"退出码非 0 即本步报错阻塞"的措辞本
   应挡住该报告落盘/归档，但报告照常存在于归档目录）。

**结论**：**未调用**，非"调用失败未记录"。根因不是脚本 bug，而是**旧版 SKILL.md 把"调 emitter +
调 `anchor_lint.py` 自检"两个具体工具调用，作为一句散文子弹埋在编号步骤 6「写报告」内部**（旧
Step5：1 工作树检查→2 修复→3 checkpoint→4 复审→5 取锚→6 写报告〔含度量锚落锚+锚行自检+反馈回路
三个子弹〕→7 checkpoint→8 收敛口）——执行者在实践中把"写报告"理解为"生成 markdown 文本"，顺带略过
了嵌在其中、需要真实 Bash 调用的两个动作，且没有任何机制在当轮拦下这个疏漏（旧锚行自检本身也是被
埋在同一处、同样被跳过的自检步）。spec-review 侧同一时期未复现此故障（对照组锚齐全），提示两个
SKILL 在"写报告"步骤的结构组织上有实质差异，code-review 侧的嵌套更深、密度更高，更容易被整体略过。

## (b) B25 修复

**已有的外部机械兜底（Task 3，本次未改动）**：`ship_gate.py` 的 `guard_report_anchors()` +
`metrics_enabled()` 现在会在 `metrics.enabled=true` 时，对 code-review 报告强制要求
`sdflow:lens-metric layer="code-review"` 锚与 `sdflow:ref-check` 锚，缺任一即判
`STEP_IN_PROGRESS`（阻断进 verify）。这是本 change 设计层面对 B25 的**主防线**——未来即便 SKILL
侧再度被跳过，`ship_gate` 也会拒绝放行、逼一次重跑。

**本票新增的 SKILL 侧直接成因修复**（`sdflow-code-review/SKILL.md` 第五步）：

1. **拆分编号步骤，把"度量锚落锚 + 锚行自检"从"写报告"内部的子弹提升为独立编号步骤**：
   旧 `6. 写报告（含三个子弹：度量锚落锚/锚行自检/反馈回路）` → 新
   `6. 写报告初稿（不含度量锚，明确声明"本步不产出度量锚/引用核锚，MUST NOT 顺带调用或省略"）` +
   `7. 度量锚落锚 + 锚行自检（独立编号，标注"是本轮输出锚的唯一途径，是一个具体、不可省略的工具
   调用，不是写报告那句散文里可以顺带略过的细节"）` + `8. checkpoint（原 7）` +
   `9. 收敛口（原 8）`。执行顺序小节已有"MUST 按下方编号，不是按小标题在文档里出现的先后"的
   既有纪律，本次是在**同一纪律下**新增一个不可跳过的编号项，而非新造机制。
2. **新增历史注记（原文引用本次诊断的确定性证据）**，直接挂在新 Step7 内，说明"这不是假设性风险，
   是本仓 6/6 归档报告实测复现过的真实故障"，并注明 `ship_gate.py` B25 门已作为外部兜底存在。
3. **Step3 新增 `sdflow:ref-check` 结构化锚落盘指令**（见 (e)），使锚存在门 ① 的第二个检测对象
   （引用核落盘锚）在 SKILL 侧也有明确产出指令，不再只有 lens-metric 一侧。

**未做的事（按诊断结论排除）**：未改 `lens_metric_emit.py`、未改脚本调用路径——冒烟测试证明脚本
本体正常，改脚本不解决"SKILL 执行时跳过调用"这个根因。

## (c) 四 SKILL effort 适配

`sdflow-spec-review` / `sdflow-code-review` / `sdflow-implement` / `sdflow-done` 四个 SKILL.md：

- **tier-resolution 托管块**（4 处逐字节相同，`hack/check_tier_resolution_parity.py` 机械守）：
  `unset` 清脏清单由 6 变量扩至 9（新增 `SDFLOW_EFFORT_STRONG SDFLOW_EFFORT_MID SDFLOW_EFFORT_LIGHT`），
  并在"取回本轮变量"那句尾部补充三个 effort 变量的取值说明（"claude 机队按档位推导的 effort 值……
  codex/unknown 宿主或旧版 resolver 未导出时为空串，空值即回落不带 `subagent_type`"）。四文件用
  同一段 Python 替换脚本做逐字节相同编辑，`check_tier_resolution_parity.py` 复跑仍绿（4 处一致）。
- **`hack/tests/test_tier_resolution_parity.py`**：`test_unset_clears_all_six_vars` 更名为
  `test_unset_clears_all_nine_vars`，断言串同步扩至 9 变量（红绿验证：改动前该测试对新文本会失败，
  改动后转绿；未新增独立断言函数，因原测试已完整覆盖"清脏清单必须逐字符匹配"这条不变量）。
- **各 SKILL 的镜/步派发表格加"effort 档"列**，并在紧邻处补一句 `subagent_type` 构造规则
  （`$SDFLOW_EFFORT_<档位>` 非空则附带 `subagent_type: sdflow-effort-$SDFLOW_EFFORT_<档位>`，空
  则不带、行为与引入前完全相同）：
  - `sdflow-spec-review`：领域镜/对抗镜/接地镜表格 + "模型选择"节改写为含 model/effort 两列的表格
    （含主 session / 广审双镜 / 领域对抗镜 / 接地镜四行）。
  - `sdflow-code-review`：领域镜/对抗镜/历史镜表格 + "模型选择"节同款表格（含 Step1 scope 审计
    子代理一行）。
  - `sdflow-implement`：无既有"模型选择"表格（该 SKILL 是散文式派发，三处各自写
    `model: $SDFLOW_TIER_MID`），新增一张"effort 派发"小表放在 tier-resolution 块之后，列出
    implementer / Standards+Spec 轴 / fix 子代理三个 dispatch 点，并在三处原有派发说明句里各自
    补一句 effort 附带规则；**`T10-choice` 三级协议 / `review-loop-breaker` 熔断仲裁用的 strong
    档对抗镜/fix 子代理不在本票范围**（design 组件清单未点名，未加宽范围）。
  - `sdflow-done`："模型选择"表格加 effort 档列 + 派发构造说明段；verify/archive/commit 三处
    "派发 Agent（model: ...）"行原地补一句 `subagent_type` 附带规则。
- **门禁步不降档**：四处均显式写明"带门禁、无人逐条复核的步（主 session 综合裁决 / verify 终门）
  MUST NOT 以低于 high 的 effort 执行"。

## (d) 两评审 SKILL 三段组装序

`sdflow-spec-review`（领域镜/对抗镜/接地镜）与 `sdflow-code-review`（领域镜/对抗镜/历史镜）的 Step
fan-out 章节各新增一段"三段组装序"说明：

- **段①**：`~/.sdflow/hack/render-review-prefix.sh --layer <层>` 的 stdout 原文整体，非零退出
  fail-loud、MUST NOT 半段前缀继续。
- **段②**：per-镜角色声明 + 清单/角度 + 该层专属补充（code-review 层的 CR 编号字段 + pre-emit
  引文纪律细则；spec-review 层的置信度自报字段）。
- **段③**：动态内容（diff 范围/四件套当前内容）。

**收敛的重复散文**：删除原先"每个子代理 prompt 必须自带……不要 AskUserQuestion"与"🔴 每个子代理
prompt MUST 原文携带……四条通则区块"两段——这两段内容现在唯一源是脚本（段①），SKILL 正文只留一句
引用（"SKILL.md 禁静态内联"同款 idiom）。**保留未删的部分**：code-review 层的 pre-emit 引文纪律
细则（`evidence_pack`/`uncheckable` 分类自报的诚实边界说明）——这部分不在 `render-review-prefix.sh`
的通用契约段范围内（脚本只含 code-review-base.md 全文 + 通用 findings schema，不含 code-review 层
专属的 evidence_pack 细则），故保留为段②内容，未误删有效信息。

**未触碰**：`sdflow-spec-review` 的"广审镜（strategy/plan-eng）"prompt 契约仍在独立管理块
`sdflow:broad-mirror-def`（真相源 `sdflow-init/assets/snippets/broad-mirrors.md`，同时供
`sdflow-roadmap` 消费）——本票未改该块。理由：该块的"四条通则原文复制"契约与三段组装序是两条
并行有效的机制，改它会连带影响 `sdflow-roadmap`（不在本票 R-ID/design 组件清单范围内），属加宽
scope；spec-review 的"模型选择"节已把 effort 覆盖到广审双镜（同中档 `$SDFLOW_EFFORT_MID`），
effort 维需求已满足，三段组装序对广审双镜的收益（避免重复散文）留待未来若有票同时改
`sdflow-roadmap` 时一并处理。

## (e) sdflow-code-review defer 当场入池

`sdflow-code-review/SKILL.md` 四处改动：

1. **Step4「修不了/拿不准」分支**：从"defer → 写 buglist/todolist"改为"当场调用 recorder
   （`issues_v2.py add --pool bug|todo --json '{...,"source_change":"{change_name}"}'`，
   **`source_change` MUST 显式传**，不依赖脚本自动探测——防多 change 并行挂错）取得返回 id，
   **当场写入报告台账表行**；新增 🔴 recorder 调用失败 fail-loud 分句：非零退出 MUST NOT 记为
   已入池、MUST NOT 写"已入 todolist"，报告如实记录失败与待人工补录。
2. **Step3 新增"机械引用核落盘锚"子弹**：无论有无 findings，都构造
   `<!-- sdflow:ref-check v1 status="ran|skipped" pass="N" fail="N" uncheckable="N" -->`
   落进报告——`degraded` 分支才是 `status="skipped"`，其余（含零 findings）恒 `status="ran"`；
   本锚受 `metrics.enabled` 同款门控，`true` 时是 `ship_gate` B25 门 `require_ref_check=True`
   的机判对象。
3. **报告格式模板改写**：
   - 新增"### 机械引用核锚"小节示范 `sdflow:ref-check` 锚行。
   - "### 修复 / defer 台账"改为机读表格（`| id | 池 | 摘要 | critique |`），并附一段"台账行
     判别契约"说明（id 列单元格须恰为单个 `T\d+`/`B\d+`，MUST NOT 出现无 id 的散文 defer 声明）。
   - Findings 区示例行、聚合摘要句、结论区三处的"defer→buglist"/"defer 残差已入
     buglist/todolist"改写为"递延见下方台账 T142"/"本轮新增待处理 K 项"/"本轮新增待处理项已入池"
     —— 移除裸露的英文 "defer" 词，聚合摘要句不再含无 id 的 defer 声明。
   - **验证**：手工核对新表格格式与 `sdflow-ship/scripts/ship_gate.py::_defer_ledger_id_cells`
     的解析口径逐字节吻合——`_TABLE_ROW_RE = r"^\s*\|(.*)\|\s*$"` 要求整行首尾 pipe，我新增的
     `T10-choice复核: <方案> | 对抗镜结论 ... | <理由...>` 散文行不以 `|` 开头，不会被误判为表格行；
     新表格的表头列名 `id`（大小写不敏感）精确匹配 `_defer_ledger_id_cells` 的 `id_col` 判据。
4. **Step5 义务措辞对齐**：锚行自检段落新增"该残余缺口现已由 `ship_gate.py` 的 B25 锚存在门在
   消费点兜底"一句，`旁路声明`段落改写为提及 `ship_gate.py` B25 门的实际判定结果
   （"该步进行中，重跑"），不再只泛泛提"报告完整性"。

## (f) sdflow-done 三步接 effort

`sdflow-done/SKILL.md`：verify（强档）/archive（中档）/commit（弱档）三处"派发 Agent"行原地补
`subagent_type` 附带规则；"模型选择"表格加 effort 档列 + 统一的 effort 派发构造说明段，并显式
"verify 是唯一终门，MUST NOT 以低于 high 的 effort 执行"。

## (g) bundle 同步

1. **`sdflow-init/assets/workflow/config.template.yaml`**：在既有 `model-tiers`（可选覆盖段）
   示例注释块后新增 `effort-tiers`（可选覆盖段）示例注释块——`claude.{strong,mid,light}`，值域
   `{low,medium,high,xhigh,max}`，标注"仅 claude 机队有对应物"。
2. **`sdflow-init/assets/snippets/claude-section.md`**：新增独立小节"## effort 派发（Claude 宿主
   专属，与上方 model-tiers/Codex 授权是正交维度）"，说明 effort 维的机制、config 覆盖键、
   前向兼容语义、门禁步下限。
3. **`sdflow-init/scripts/init.py::lint_config`**：新增 `EFFORT_FLEET_KEYS = {"claude"}`（**与
   `TIER_FLEET_KEYS` 的关键差异**：不含 `codex`——codex 无 effort 原语，出现即报越域）+
   `EFFORT_ALLOWED_VALUES = {low,medium,high,xhigh,max}`（封闭域校验，非 model-tiers 的自由字符
   集）；新增 `_valid_effort_value()` + `_effort_tiers_from_dict()`（**与
   `_model_tiers_from_dict()` 的关键差异**：无扁平旧格式分支——顶层非 `claude` 的键一律落
   `bad`，不像 model-tiers 那样把顶层 `strong`/`mid`/`light` 归入 `flat.*`，因为 effort-tiers
   是本 change 新引入的键、无历史遗留包袱）；`lint_config()` 主体新增条件化校验分支（块整段
   缺失放行，同 model-tiers/metrics 既有纪律）。
4. **测试**：`sdflow-init/tests/test_config_lint.py` 新增 `TestConfigLintEffortTiers`（10 用例：
   无块放行、合法块放行、5 个合法值枚举放行、codex 键越域、扁平旧格式越域、叶子越域、非法值、
   model-id 风格字符串误放行防护、空值、机队头标量误用）+ `TestEffortTiersFromDict`（5 条白盒
   用例，锁 `entries`/`bad`/`bad_headers` 归属，含"codex 落 bad 不落 entries"与"扁平顶层键落
   bad 不落 flat.*"两条关键差异断言）。**红绿验证**：临时 `git stash` 还原 `init.py`
   改动后重跑新增的 15 个用例，全部因 `AttributeError`（`_effort_tiers_from_dict` 不存在）/
   断言失败而红；`stash pop` 还原后全绿。
5. **scope-check 表复查**（design.md「协议文档套件 scope-check 表」逐行核对）：
   - `model-tiers.md` 表格 + 机读块 —— Task 1 已完成，本票核验未漂移。
   - `resolve-models.sh` 头注释导出变量清单 6→9 —— Task 1 已完成，本票核验已含 effort 三变量。
   - bundle `config.template.yaml` / `claude-section.md` —— 本票完成（见上 1/2）。
   - 4 个编排 SKILL 派发段 effort 列引用 —— 本票完成（见 (c)）。
   - `CLAUDE.md`/`AGENTS.md` 托管区块 —— **未手改**（按纪律"经 sync/init 工具，勿手改托管块"）。
     本仓自身的 `CLAUDE.md`/`AGENTS.md` 是从 `claude-section.md` 铺设/更新而来的部署副本
     （dogfooding），本票已改的是**权威源** `claude-section.md`；部署副本要拿到新增的"effort
     派发"小节，需下一次 `sdflow-init update` 在本仓自身运行——这不在本票动作范围内（`sdflow-init
     update` 是全局命名空间操作，且本票未被要求执行它），如实记为已知的、符合既有部署链设计的
     滞后状态（[[deployed-copy-drift-surfaces-only-on-update]]），非遗漏。
   - `hack/tests/` + 各 `tests/` 契约测试同步 —— 本票完成（`test_tier_resolution_parity.py` +
     `test_config_lint.py`，见上）。
   - `anchor_lint.py::_metrics_enabled` ↔ `ship_gate` B25 门一致性测试 —— Task 3 已完成
     （`test_metrics_enabled_parity_with_anchor_lint`），本票未改 `anchor_lint.py`（design
     Non-Goals 明确"不给 anchor_lint 增加新功能"，`sdflow:ref-check` 锚的机判方是 `ship_gate.py`
     自己的独立解析，不复用 `anchor_lint.py`，故本票的新增内容不触发这条一致性守卫，也未使其
     失效）。
   - `init.py::lint_config` ↔ `effort-tiers` 新键 —— 本票完成（见上 3/4）。

## (h) e2e dogfood 判据

本 change 自身即将经历的 `sdflow-code-review`（由 `/sdflow-ship` 在收尾阶段调用）将是 B25/B26 两道
gate 的**首次真实 dogfood**——它会用本票刚改写的 Step3/Step4/Step5 新指令产出报告，报告须真正含
`sdflow:lens-metric`、`sdflow:ref-check` 两类锚与机读 defer 台账（若有 defer 项），随后被 Task 3
实现的 `ship_gate.py` B25/B26 门读取判定。这是设计层面刻意安排的自证闭环，本票不需要（也不能）
提前模拟它——如实记录该判据存在、无需额外动作。

## 测试结果

```
/usr/bin/python3 -m pytest sdflow-init/tests/test_config_lint.py -q
50 passed

/usr/bin/python3 -m pytest sdflow-init/tests/ hack/tests/ -q
1240 passed, 4 skipped in 248.59s

python3 hack/check_tier_resolution_parity.py
[tier-resolution-parity] ✅ 4 处宿主/档位解析核心段逐字节一致
```

```
/usr/bin/python3 -m pytest -q   （全仓，覆盖全部 skill 的 tests/）
2639 passed, 10 skipped in 380.89s (0:06:20)
```

全仓零失败、零回归（对照 Task 3 impl-report 记录的基线 2591 passed，本票 + 期间其余并入分支的
提交合计新增净 48 条通过用例，量级与本票新增的 tier-resolution 1 条改写 + config-lint 15 条
新增用例相符）。

## 未做 / 越权说明

- 未勾选 `tasks.md`/`tickets.md` 复选框、未打 checkpoint 标签——按信号权威表由双轴审通过后的
  执行模式补打。
- 未运行 `bash setup.sh`（开发期测试三层第 3 层，机器级影响）——`render-review-prefix.sh` 尚未
  部署到真实 `~/.sdflow/hack/`（Task 4 已把脚本落 bundle 权威源，未跑 setup 前全局路径不可达），
  本票的 SKILL.md 文本改动本身不需要该脚本真跑即可完成（编辑的是指令文本，非脚本本体）；按
  design Migration Plan 步骤 0，`bash setup.sh` 留给本 change 收尾阶段真正跑 `/sdflow-code-review`
  之前统一执行一次，不在本票单独开该窗口。
- 未改 `sdflow-roadmap/SKILL.md`、未改 `sdflow-init/assets/snippets/broad-mirrors.md`
  （`sdflow:broad-mirror-def` 管理块）——见 (d) 说明，避免加宽 scope。
- 未手改本仓 `CLAUDE.md`/`AGENTS.md` 的部署副本——见 (g) scope-check 表说明。
- 未改 `anchor_lint.py`——design Non-Goals 明确排除，`sdflow:ref-check` 锚的机判方是
  `ship_gate.py` 独立实现（Task 3），不经 `anchor_lint.py`。
