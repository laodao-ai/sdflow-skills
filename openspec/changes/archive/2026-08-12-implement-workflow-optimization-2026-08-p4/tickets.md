---
impl-pipeline: tickets
---

## Global Constraints

以下逐字摘自本 change design.md 的 MUST/MUST NOT/SHALL 硬约束与 Compliance 条款：

- effort 机读块键路径**仅含** `claude.{strong,mid,light}`（codex 不写键即 n/a，MUST NOT 引入空值语义）。
- resolver 导出 `SDFLOW_EFFORT_{STRONG,MID,LIGHT}` 与既有六变量同一 eval 契约；effort 分支 MUST NOT 复用 model tier 的 unknown 回落逻辑；codex/unknown 分支 MUST 显式初始化三变量为空串（`set -u` 下漏初始化中止整个 resolver）。
- config 覆盖值域校验 ∈ {low,medium,high,xhigh,max}，非法值忽略覆盖回落缺省 + 告警（与 model 覆盖同语义）。MUST NOT 引入 yaml import。
- 带门禁、无人逐条复核的步 MUST NOT 低于 high（effort 铁律延伸）。
- `$SDFLOW_EFFORT_*` 为空（codex/unknown/未升级 resolver）⇒ 不带 subagent_type，行为与引入前完全相同（前向兼容）。
- config 读取 `metrics.enabled`：缺省/false = 放行、**config.yaml 文件整体不存在 = 放行**（`_yq()` 对缺文件裸 raise，MUST 先判文件存在性）；存在坏 = fail-closed 报 problem+cause+fix。MUST NOT 引入 yaml import。
- ship_gate 两门 verdict MUST 字面复用 `STEP_IN_PROGRESS`，MUST NOT 新增 verdict 名。
- 台账行判别窄化：台账行 = 表格数据行，id 取专用 id 列且单元格全部内容 = 单 id；MUST NOT 全行子串搜索。fence-aware 解析复用 ship_gate 既有口径。
- render-review-prefix.sh 源缺失 MUST fail-loud 非零退出；段① 稳定前缀 byte-stable 可测。
- `SKILL.md 禁静态内联` 不变；编排 SKILL MUST NOT 内联模型名/effort 值。
- tier-resolution 托管块 unset 清脏清单 SHALL 扩含 `SDFLOW_EFFORT_*` 三变量。
- 全部 bundle 改动落 `sdflow-init/assets/` 权威源（scope-check 表复查，防 [[deployed-copy-drift]]）。
- 遵守基准 5：机读块/config 解析均为有界键路径行锚定，MUST NOT 长成通用解析器。
- 通则托管块不手改。

### Task 1: effort 维解析与导出全链

**Blocked-by:** none
**R-ID:** HAE-1

为 effort 分档建立从机读块到 eval 导出的完整数据通路：在 model-tiers 文档新增独立 `effort-tier-defaults` 机读块（仅 claude 三键 strong→high / mid→medium / light→low），resolver 脚本按有界键路径行锚定提取并导出 `SDFLOW_EFFORT_{STRONG,MID,LIGHT}`（与既有六变量同一 eval 契约）；codex/unknown 宿主显式初始化三变量为空串（MUST NOT 复用 model tier 的 unknown 回落路径或 `_resolve_tier` 告警路径）。消费仓 config.yaml `effort-tiers.claude.*` 覆盖按有界键路径解析，值域校验 ∈ {low,medium,high,xhigh,max}，非法值回落缺省 + stderr 告警。resolver 头注释变量清单 6→9。

起手做 A1 最小实测：手工临时放一个 `effort: low` 探针 agent 定义到 `~/.claude/agents/`，派探针子代理对比 token 用量/耗时/输出规模多信号确认 effort 经 subagent_type 生效；结论记入 impl-report；失效 ⇒ 止损按 ADR 0043 备选重估。

- [x] A1 探针实测通过，effort 经 subagent_type 全链生效（结论记入 impl-report）
- [x] model-tiers 文档新增 `effort-tier-defaults` 机读块（仅 claude 三键），与上方表格两处不漂移
- [x] resolver 导出 `SDFLOW_EFFORT_{STRONG,MID,LIGHT}`（claude 宿主 high/medium/low；codex/unknown 空串不阻断）
- [x] config `effort-tiers.claude.*` 覆盖生效 + 非法值回落告警
- [x] 测试覆盖：三宿主态导出 × 覆盖生效 × 非法值回落 × eval 契约 × codex/unknown 空串无告警噪声

### Task 2: effort agent 定义铺设与 install_agents 验证

**Blocked-by:** 1
**R-ID:** HAE-2

铺设 5 个全局 agent 定义 `sdflow-effort-{low,medium,high,xhigh,max}`（frontmatter 含排他 description「仅由 sdflow 编排 SKILL 派发选用」、`model: inherit`、`effort: <值>`），放入既有 `sdflow-spec/agents/` 目录（设计门拍板 Q2=C：install_agents 守卫/manifest 零改动，新增 `.md` 自动纳入）。同步 CLAUDE.md/design 对该目录的描述 + 目录内注记。假 HOME 测试加 effort 定义专项断言（铺设幂等 / 不覆盖他人 / 孤儿清理 / Windows skip）。

- [x] 5 个 `sdflow-effort-*.md` 定义文件就位于 `sdflow-spec/agents/`，frontmatter 正确
- [x] install_agents 铺设到 `~/.claude/agents/` 且既有所有权守卫/孤儿清理行为不变
- [x] 假 HOME 测试覆盖：effort 定义铺设幂等、非本仓同名不覆盖、源删除后孤儿清理
- [x] CLAUDE.md 对 `sdflow-spec/agents/` 目录描述同步更新

### Task 3: ship_gate B25/B26 机械门

**Blocked-by:** none
**R-ID:** IO-1

在 ship_gate 既有 code-review 报告消费点新增两道机械门：① 锚存在门——`metrics.enabled=true` 时 code-review 报告 MUST 含 `sdflow:lens-metric layer="code-review"` 锚行与 `sdflow:ref-check` 结构化锚；缺任一 ⇒ STEP_IN_PROGRESS + 修复指引；config 缺省/false/文件不存在 = 放行，yq 非零 = fail-closed。② defer 对账门——台账行（表格数据行，id 取专用 id 列，单元格全内容=单 id）携 `T\d+|B\d+` id 且对应池文件文件系统存在且 `source_change` = 当前 change；不满足 ⇒ STEP_IN_PROGRESS。fence-aware 口径复用既有解析。spec-review 报告在 design 门加同款锚存在检查（含转换态指引）。

- [x] 锚存在门：metrics 开启 + 报告缺锚 ⇒ 被拦（STEP_IN_PROGRESS + 修复指引）
- [x] 锚存在门：metrics 缺省/false/config 文件不存在 ⇒ 放行
- [x] 锚存在门：config 不可解析 ⇒ fail-closed 报 problem+cause+fix
- [x] defer 对账门：台账行无 id / 池文件缺失 / source_change 属另一 change ⇒ 被拦
- [x] defer 对账门：fence 内锚样例不触发判定（负例）
- [x] defer 对账门：台账窄化——描述列旧票号不误抓 + 聚合摘要句不假阳（负例）
- [x] spec-review 报告 design 门同款锚存在检查 + 转换态指引
- [x] 测试矩阵：双向 config 态 × 缺锚/缺 ref-check/defer 无 id/池文件缺失/change 不符/窄化负例/fence 负例

### Task 4: render-review-prefix.sh 与部署链

**Blocked-by:** none
**R-ID:** SW-1

新建 `render-review-prefix.sh`（落 `sdflow-init/assets/hack/`，setup 装 `~/.sdflow/hack/`）：接受 `--layer code-review|spec-review` 参数；按固定序 cat 通则区块（`~/.sdflow/hack/skill-principles.md`）+ 内嵌通用契约段 heredoc（含 T103 输出封顶句「回传目标 ≤2k token，超出按严重度截优先」）+ base checklist（`$RULES_ROOT` 解析到的对应层 base checklist 全文）。任一源缺失 ⇒ fail-loud 非零退出 + stderr 含 problem+cause+fix。byte-stable 可测试（同规则集连续两跑逐字节同）。setup.sh 布署链验证：脚本随 hack 拷贝就位。

- [x] `render-review-prefix.sh --layer code-review` 按固定序输出通则 + 通用契约段 + base checklist
- [x] `render-review-prefix.sh --layer spec-review` 同构输出对应层
- [x] 任一源缺失 ⇒ 非零退出 + stderr 含 problem+cause+fix（MUST NOT 输出半段前缀）
- [x] byte-stable golden 测试：连续两跑逐字节同 + 源缺失非零退出
- [x] setup.sh 部署链：脚本随 hack 拷贝到 `~/.sdflow/hack/`

### Task 5: 四编排 SKILL 全面适配 + B25 诊断修复 + bundle 同步

**Blocked-by:** 1,2,3,4
**R-ID:** SW-1, SW-2, SW-3, IO-2, HAE-1

B25 诊断定案：在归档报告数据上重放 `lens_metric_emit.py` 调用，判定「未调用 vs 调用失败未记录」，结论记入 impl-report。按结论修复 emitter 落盘直接成因。

四个编排 SKILL（sdflow-spec-review / sdflow-code-review / sdflow-implement / sdflow-done）全面适配：
(a) 派发条款接 effort——表格加 effort 档列，派发时构造 `subagent_type: sdflow-effort-$SDFLOW_EFFORT_<档位>`，空值回落不带 subagent_type；门禁步不低于 high。tier-resolution 托管块 unset 清脏清单扩含 `SDFLOW_EFFORT_*` 三变量。
(b) 两评审 SKILL 镜派发改三段组装序——段① = `render-review-prefix.sh` 输出原文一句引用；段②③ 界线显式化；SKILL 内与段①重复的散文契约收敛为引用。
(c) sdflow-code-review Step4 defer 改「当场 recorder add（显式 source_change）+ 返回 id 写台账」；台账改机读结构（表格行 + 专用 id 列）+ 聚合摘要句改写移出 gate 检测范围；Step3 引用核结果落 `sdflow:ref-check` 结构化锚；Step5 义务措辞与门对齐；recorder 失败 fail-loud。
(d) sdflow-done 三步子代理接 effort 档。

bundle 同步：config.template `effort-tiers` 段示例 + claude-section 说明 + `init.py lint_config` 扩 `effort-tiers` 结构/值域校验（与 resolver 同口径）+ scope-check 表全组复查。

- [x] B25 诊断结论记入 impl-report（未调用 vs 调用失败，有确定性证据）
- [x] B25 直接成因修复（SKILL/脚本改动，按诊断结论定）
- [x] 四编排 SKILL 派发条款接 effort（subagent_type 构造 + 空值回落 + 门禁步 ≥ high + unset 扩面）
- [x] 两评审 SKILL 镜派发改三段组装序（段① 脚本引用 + 段②③ 显式化 + 重复散文收敛）
- [x] sdflow-code-review defer 当场入池（recorder add + id 台账 + ref-check 锚 + 聚合摘要改写）
- [x] sdflow-done 三步子代理接 effort 档
- [x] bundle 同步：config.template effort-tiers 段 + claude-section + init.py lint_config 扩面 + scope-check
- [ ] [e2e] 本 change 自身 code-review 报告含 lens-metric 锚 + ref-check 锚 + defer id 对账（dogfood 首证）

### Task 6: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4,5
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落
`impl-reports/task6-verify.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

自审窗口操作：触发本 change 自身 code-review/verify 之前，在开发 checkout 跑 `bash setup.sh`（全局窗口层时间盒）——否则自审调运行 checkout 旧 gate/旧 SKILL，dogfood 自证不成立；自审完毕回运行 checkout 重跑 setup 还原，还原动作记入 impl-report。

附加验证：retro 再生冒烟（`retro_report.py` 跑通 + 本 change token-log 锚在列 + anchor_lint CLEAN）；roadmap 阶段 4 回填（子任务表 + 快照行 + task-log 里程碑）；B25/B26 池状态 set-status FIXED + evidence；T105/T103/T98/T124 set-status DONE + evidence。

- [x] 单元测试证据齐全并通过
- [x] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [x] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
