## Purpose

`issues-v2-single-file-model` 把 issues 台账从「三薄入口（`buglist.py`/`todolist.py`/`issues.py`）+
dated 总览表 + 批次注册表 `batches.md` + `sweep`/`triage`」的 v1 架构改造为「单一入口 `issues_v2.py`
+ 单文件模型（`open/`/`closed/` 各一个 issue 一个 `.md` 文件）+ 两维度（源 change / status，无批次）」。
本 delta 修正 `spec-workflow` 能力内硬编码这套 v1 目录/命令/机制断言的 Requirement 与 Scenario；
不改动与 issues 架构无关的 prose 引用或 Requirement（如阶段三 ship_gate、outside-voice 对抗裁决主体
流程），仅同步其中提及的 issues 台账相关路径/命令措辞。

## MODIFIED Requirements

### Requirement: 阶段三过设计门后连续自动跑到 merge

阶段三 SHALL 在阶段二设计门之后无任何阻塞人类门地连续运行 `实现管线 → sdflow-code-review → sdflow-done`；实现管线为可选双轨——缺省 `writing-plans → subagent-dev`，或经 `impl-orchestration` 能力的手动路由（config 键 + 盘面 marker，缺省/非法值一律 superpowers）选择 `sdflow-implement 双模式（出 ticket → 执行）`；**编排层入口 = `/sdflow-ship`**（一次调用驱动 5.5→9，按「阶段三编排台账确定性」需求经 ship_gate 推进；手动逐步仍为合法 reference 路径）。**两轨的计划文件名 SHALL 分列**——tickets 轨 `tickets.md`、superpowers 轨 `superpowers-plan.md`，由 gate 与 route helper 经同一份共享 resolver 定位；两者同时存在 SHALL fail-closed 判 UNKNOWN；**文件名 MUST NOT 参与轨道路由判定**（路由权威仍是 config 键 + plan frontmatter marker）〔spec-review-amendment · adr/0033〕。管线选择 MUST NOT 引入模型自动判断，MUST NOT 新增人类门。实现管线内不可消解的 BLOCKED 停机属「defer-to-human 异常终态」而非人类门——与既有 BLOCKED_UPSTREAM 同构（停并上抛、人工再入口），不违背「无阻塞人类门」承诺（正常路径仍连续到 merge）〔spec-review-amendment F7〕。能修的自动修；**遇 ≥2 方案 MUST 按三级决策协议 `T10-choice`**〔具名规则，取代旧「T10」单一编号；"T10" 保留为历史别名。语义边界见 `adr/0031`：本规则**只覆盖「多个候选方案选哪个」**，`sdflow-implement` 的「同一发现反复未消解」熔断由 `review-loop-breaker` 独立定义，两者 MUST NOT 互相引用〕：①有客观判据（测试/断言/基准可判）→ 自动选并**按三镜 + 主次**记理由；②无客观判据 → 派 **strong 档**对抗镜复核推荐项，通过方自动选（复核记录进报告；出票模式无报告产物时落 `impl-reports/planning-decisions.md`）；③复核不过或无从复核 → **记入 issues 台账（bug/todo 两池，`openspec/issues/open/`）并由 hand-off 引导另开 change 清理**〔`issues-v2-single-file-model`：原「defer 进 buglist/todolist」是 v1 目录名，v2 台账目录为 `open/`/`closed/`，不再有 buglist/todolist 子目录〕。MUST NOT 以自评置信（"有把握"）作为自动选定的唯一依据。修不了或需拍板的 MUST 记入 issues 台账延后。

#### Scenario: 修不了的问题延后而非阻塞

- **WHEN** sdflow-code-review 发现一个本 change 修不掉的问题
- **THEN** 它记入 issues 台账（defer）并写入 hand-off，流程继续跑到 sdflow-done，不设人类门阻塞

#### Scenario: 无客观判据的两方案走 strong 档对抗复核

- **WHEN** 阶段三某步遇两个可行方案且无测试/断言可判优劣
- **THEN** 派 strong 档对抗镜尝试证伪推荐方案：未被证伪 → 自动选并按三镜+主次记复核记录；被证伪或复核无法开展 → defer，MUST NOT 凭"有把握"直接选，MUST NOT 用 mid 档同档互判代替 strong 档仲裁

#### Scenario: 一次调用驱动到 merge 建议

- **WHEN** 对已过设计门的 change 调用 /sdflow-ship 且各步门禁全通过
- **THEN** 链依 gate 判定逐步推进至 sdflow-done 完成（含 merge 缺省语义），输出最终摘要；全程无 AskUserQuestion

#### Scenario: ship 零 git 写操作、merge 意图透传〔grill-amendment〕

- **WHEN** 用户以"跑到 merge 前停"类意图调用 /sdflow-ship
- **THEN** ship 将 opt-out 原样透传给 sdflow-done（merge 由 done 一处执行/跳过）；ship 自身 MUST NOT commit/merge/push，MUST NOT 自动 push（摘要提醒手动 push；toolkit 源仓附激活提示）

#### Scenario: 实现管线按手动确定值路由

- **WHEN** gate 判定 RUN_PLAN 且 config 键值为 `tickets`
- **THEN** ship 派发 sdflow-implement 出 ticket 模式；键缺省/非法/为 superpowers 时派发 writing-plans，行为与本变更前一致；CONTINUE_IMPL 一律按 plan 文件 marker 路由

### Requirement: 债务池统一为 issues 结构且 INDEX 只生成

recorder 债务池 SHALL 统一为 `openspec/issues/{open,closed}/` 结构（每个 issue 一个 `.md` 文件），每
个 item MUST 分**源change(`source_change`，provenance，不可变) / status(生命周期)** 两维度记录
〔`issues-v2-single-file-model`：v1 版本此处是三维度（源change / 批次 / status），批次维度随单文件
模型退役——PLANNED 批次的计划文本迁移时已搬入对应 issue 的 body〕；`issues/INDEX.md` MUST 只由
`reindex` 命令从 `open/` 目录全部文件重建生成、`issues/CLOSED.md` MUST 只由 `reindex` 命令从
`closed/` 目录全部文件重建生成，两者均禁止手改，SHALL NOT 成为独立的手维护真相源（杜绝第三漂移源）。

#### Scenario: reindex 从 open/closed 目录重建 INDEX/CLOSED

- **WHEN** 对 issues 池运行 `issues_v2.py reindex`
- **THEN** 它从 `open/` 目录全部 `.md` 文件重建 `issues/INDEX.md`、从 `closed/` 目录全部 `.md` 文件重建 `issues/CLOSED.md`，按 ID 排序列出每个 issue 一行，不读取也不信任任何手改的 INDEX/CLOSED 内容

#### Scenario: 两维度分家、status 回归干净

- **WHEN** 一个 issue 的 status 发生变更（如 `OPEN → PROPOSED`）
- **THEN** status 字段独立更新，`source_change` 维度保持不可变（不因 status 变化而改写发现处 provenance）；`resolved_by`（关闭时填的解决处）与 `source_change`（发现处）是两个独立字段，不混用

### Requirement: skill 命名与品牌一致性

工具链自制 skill MUST 统一使用 `sdflow-` 前缀命名（目录名 = 安装名 = 斜杠命令名）；合一后台账类 skill 收敛为单一 `sdflow-issues`，`sdflow-buglist`/`sdflow-todolist` 已删除。

> `[spec-review-amendment]`（`dedupe-issues-scripts-shared-layer`）：原 requirement 的 sdflow- 前缀枚举含
> `sdflow-buglist`/`sdflow-todolist` 为独立 skill，且「sibling 脚本路径随名迁移」Scenario 假定 `issues.py` 上溯
> SKILLS_ROOT 后 join **sibling 目录** `sdflow-buglist`/`sdflow-todolist`。三 skill 合一为 `sdflow-issues`（`adr/0027`）后：
> ① 枚举中 `sdflow-buglist`/`sdflow-todolist` **删除**（并入 `sdflow-issues`）；② sibling-spawn 改为**同目录**定位。
> 命名规范其余部分（前缀约束、豁免名单、触发等价、trigger-map 留档）不变。

> `[issues-v2-single-file-model]`：`sdflow-issues` 内部脚本入口进一步从「三薄入口（`issues.py`/
> `buglist.py`/`todolist.py`）+ 共享 `sdflow_issues_core` 包」合为单一文件 `issues_v2.py`——不再有
> 任何跨脚本 sibling 子进程调用（`add`/`set-status`/`scan`/`reindex`/`next-id` 全在同一进程内完成，
> 唯一子进程调用是执行 `git` 本身），「sibling 脚本路径改同目录」Scenario 因此失去前提，见下方替换
> Scenario。skill 目录名/安装名/斜杠命令名（`sdflow-issues`）与本条其余部分不变。

工具链自制 skill MUST 统一使用 `sdflow-` 前缀命名（目录名 = 安装名 = 斜杠命令名），按 RENAME-MAP（design §三）执行。
**RENAME-MAP 随本次台账合一更新**：原 map 中的 `sdflow-buglist`/`sdflow-todolist` **从 map 移除**（两 skill 删除、并入
`sdflow-issues`），map 台账项收敛为单一 `sdflow-issues`（owns 两池 + 跨池）；RENAME-MAP 其余项不变。
（注：RENAME-MAP 是那次改名 change 的映射子集、**非现役 skill census**——map 之后新增的 skill 如 `sdflow-architecture`/
`sdflow-devenv`/`sdflow-implement`/`sdflow-retro`/`sdflow-ship`/`sdflow-upgrade` 本就不在 map 内、不受本条约束。）
豁免保留名单 = `embedded-test-sop`（域技能）、
`openspec-upgrade`（升级外部 CLI）、`sdflow-upgrade`。主 spec 与功能性文件全文中的旧 skill 名 SHALL 随合一同步替换
（语义不变）；文档性历史记录（`adr/`、ROADMAP 历史行、CONTEXT 术语史、`changes/archive/`、`setup.sh` 的
`OUR_LEGACY_NAMES` 孤儿清理名单）MUST NOT 回改。各 SKILL.md 的 description MUST 触发等价：合并前分属两 skill 的触发
场景语句集（如「记一下这个 bug」「记个 TODO」）SHALL 全部保留、并入 `sdflow-issues` 单一触发面。

#### Scenario: 目录名与斜杠命令一致切换

- **WHEN** 合一完成并在运行 checkout 重跑 `setup.sh`
- **THEN** `~/.claude/skills/` 与 `~/.codex/skills/` 下存在 `sdflow-issues`、**不存在** `sdflow-buglist`/`sdflow-todolist`（旧名 dangling 链被孤儿清理收走，MUST NOT 残留）

#### Scenario: 触发等价不回退（并入单一触发面）

- **WHEN** 用户说出合并前即可触发某台账 skill 的语句（如「记一下这个 bug」「记个 TODO」）
- **THEN** 该语句仍触发 `sdflow-issues`（bug↔todo 分池分类由模型在 skill 内按「坏了没」判）；合并前两 skill 的触发短语集全部保留

#### Scenario: 单文件脚本内无 sibling 子进程调用

- **WHEN** `sdflow-issues` 的 `issues_v2.py` 执行 `reindex`/`scan`/`add`/`set-status`
- **THEN** 全部逻辑在同一进程内完成，**MUST NOT** 以子进程方式调用同目录或其它任何脚本文件（`add`/`set-status` 到终态时唯一的子进程调用是执行外部 `git`/`git mv`/`git add` 命令本身）；`sdflow-done` 引用的脚本固定路径为 `sdflow-issues/scripts/issues_v2.py`

### Requirement: outside-voice tension 不静默采纳

outside voice 与主审分歧（tension）SHALL 中立并陈、标 TENSION：sdflow-spec-review 写入报告决策登记区（选项 + 推荐 + 两方视角 + **三面后果（系统 / 用户 / 开发循环）+ 主次判定**，设计 HARD-GATE 人一次性拍板）；sdflow-code-review 按 `T10-choice` 三级协议自动裁决（有客观判据自动裁 / 无则派 **strong 档**对抗镜复核 / 复核不过或无从复核则 **defer 进 issues 台账**〔`issues-v2-single-file-model`：原文「defer 进 buglist/todolist」是 v1 目录名，v2 无该子目录，措辞订正为「issues 台账」，与下方「代码侧分歧派 strong 档自动裁决或 defer」Scenario 既有措辞一致〕 + hand-off）并**按三镜 + 主次记理由**，MUST NOT 以自评置信（"有把握"）为自动裁决唯一依据〔impl-review-fix F1/CV2〕。outside voice 的建议 MUST NOT 被静默自动采纳（不直接改代码/设计而不留痕）。

**置信过滤豁免 SHALL 按合法组合矩阵的「跨模型」判定，MUST NOT 自写 `runner ≠ host` 或按 runner 枚举值硬编码**〔add-codex-host-support · spec-review-r2 C1〕：**矩阵判「跨模型」为真**（`host,runner 均∈{claude,codex} ∧ runner≠host ∧ reason_code="ok"`）的 outside-voice findings MUST NOT 经自评置信阈值（<80）预过滤——跨模型自评不可比、异见易被同族标尺误杀——一律直通对抗裁决，被裁掉的连理由落报告「已裁掉」区〔grill-amendment Q4〕；**其余**（同族 fallback `runner==host`、**及无执行 `runner="none"`**）照过同族置信滤（豁免理由对其不成立；`runner="none"` 的 findings 恒 0、豁免无意义）。

> 〔为何引用矩阵而非自写 `runner≠host`〕旧规则写死 `runner=codex` 豁免——该值在 Codex 宿主下恰恰是**自审**；而首轮改的 `runner ≠ host` 又被 `runner="none"` 击穿（`none≠host` 恒真 → 无执行轮被误豁免，spec-review-r2 C1）。∴ 判据 MUST 引用合法组合矩阵的单一「跨模型」判定，不在此重写关系式。

#### Scenario: 设计侧分歧进决策登记区
- **WHEN** outside voice 与 spec-review 主审对同一设计点结论相反
- **THEN** 报告决策登记区新增 TENSION 条目（两方观点 + 推荐 + 三面后果 + 主次判定），不中途 AskUserQuestion

#### Scenario: 代码侧分歧派 strong 档自动裁决或 defer
- **WHEN** outside voice 与 code-review 主审分歧且裁决无客观判据
- **THEN** 派 strong 档对抗镜复核，复核不过或无从复核则 defer 进 issues 池并写入 hand-off，不静默采纳任一方，MUST NOT 用 mid 档同档互判代替

#### Scenario: 低自评置信的跨模型 finding 不被预筛
- **WHEN** 某条 `runner ≠ host` 的 finding 自评置信低于 Step3 阈值（<80）
- **THEN** 该条仍进入对抗裁决（不被置信滤拦截）；若裁决不成立，连理由落报告「已裁掉」区

#### Scenario: 同族 fallback finding 照过同族滤
- **WHEN** 某条 `runner == host` 的 finding 自评置信低于阈值
- **THEN** 按同族 findings 常规处理（过滤规则一致），不享受跨模型豁免

## REMOVED Requirements

### Requirement: 批次注册表与 reindex 被动同步状态

**Reason**：`issues-v2-single-file-model` 的单文件模型砍除批次机制——`batch`/`triage`/`sweep` 三个
命令与 `issues/batches.md` 注册表均不存在于 v2 架构（design.md「与 v1 的架构差异」：无
`triage`/`sweep` 命令，batch 机制已砍）。本 Requirement 描述的「sweep 分诊本 change 新增 OPEN 项入
批次」「reindex 拿 item 池同步批次完成态为 DONE」等行为均已失去载体。

**Migration**：批次机制无等价替代——`sdflow-done` §2.1 改为只读查询
`issues_v2.py scan --json --source-change {change} --status OPEN --status PROPOSED`（见
`sdflow-done/SKILL.md` §2.1），hand-off 直接列出查到的 issue ID，不再引批次号或需要「批次完成态」
这一概念。PLANNED 批次的历史计划文本在本仓一次性迁移（`issues_v2.py migrate`）时已搬入对应 issue
的 body（`> [迁移自批次 {batch_key}] 原计划: ...`）。
