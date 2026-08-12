# workflow-optimization-2026-08 实施路线图

> 版本：v1（2026-08-10）
>
> 相关文档（全部位于 `openspec/roadmaps/workflow-optimization-2026-08/` 下）：
> - 整体设计：`design.md`
> - 任务日志：`task-log.md`（每完成一个子任务追加一条记录）

## 概览

**近期范围**：阶段 1 + 阶段 2。**理由**：阶段 2（镜复评 + 裁决改造）依赖阶段 1（度量
判据补全）的实修率数据，两者交付节奏需同步规划；阶段 3 虽无依赖、可随时提前起手，但其
机制设计需一次独立 grill，现在预写子任务分解会是假精确，留雾。

> **进度快照（2026-08-12）**：阶段 1–4 全部完成归档。阶段 4 归档 SHA `e202feb`（6 tickets,
> verify PASS 2639 tests, zero code-review findings；effort 分档全链 + B25/B26 机械门 +
> render-review-prefix + 四 SKILL 全面适配）。B25/B26→FIXED、T105/T103/T98/T124→DONE。
> 阶段 5 仍待 frontier 到达后补细。

五阶段演进，每阶段独立可交付；阶段 3 与阶段 1/2 无依赖关系，可并行或提前。

| 阶段 | 时长预估 | 里程碑 | 细化程度 |
|---|---|---|---|
| **阶段 1** · 度量决策端补全 + 池对账 | 本周 | retro 报实修率 + token 快照锚开始累积；四条错关项理由归真 | **✅ 全部完成 2026-08-10** |
| **阶段 2** · 镜 roster 复评 + 裁决地基改造 | 阶段 1 后 1-2 周 | 13 面待复评镜逐一处置；置信硬滤被替代方案取代 | **✅ 完成 2026-08-11**（验收 3 窗口判读 ✅ 2026-08-12，双 PASS） |
| **阶段 3** · 上游套件吸收机制 | 无依赖，随时 | 四源有锚、watch 跑通一轮 delta 分诊 | **✅ 完成 2026-08-11**（5/5 ticket + code-review 修复，归档 SHA `c4b8c6f`） |
| **阶段 4** · 成本工程剩余 | 阶段 1 数据到位后 | effort/thinking 按步分档落地 | **✅ 完成 2026-08-12**（6 tickets, verify PASS 2639 tests, 归档 SHA `e202feb`） |
| **阶段 5** · 人类门减负与 context 工程 | 远期 | 设计门报告摘要头 + SKILL 考古层清理 | 雾区（目标句 + 备注） |

（时长预估仅取定性口径，与本仓既有 roadmap 惯例一致；小时级数字无历史推导基础，不写。）

每阶段建议开一个独立 OpenSpec 变更（`implement-workflow-optimization-2026-08-p<N>`，
池对账类直写操作除外），完成归档后进下一阶段。

---

## 阶段 1 · 度量决策端补全 + 池对账

### 前置条件

- [x] 本 roadmap 三件套过 review 并收尾（含本文件）
      **✅ 2026-08-10**（strategy/plan-eng 双镜 + sync voice，11 组全采纳）
- [x] `openspec/retro/report.md` 可正常再生（`python3 sdflow-retro/scripts/retro_report.py --root .` 跑通）
      **✅ 2026-08-10**

### 目标

- retro 具备砍留拍板所需的两个判据：per-镜实修率（历史回算）+ per-change token 维
  （新 change 起累积）（见 design.md 决策 1）
- issues 池的四条错关项（T98/T99/T101/T102）关闭理由与事实一致（见 design.md 决策 5）
- 两条新增缺口（SKILL.md 考古层清理、编排条件变化记录）入池可追踪（见 design.md 决策 4）

### 子任务

#### 1.A 池对账（recorder 操作；1.A.1 依赖 1.B.4 的 reopen 命令先落地）

- [x] 1.A.1 用 `reopen` 命令（1.B.4 交付）重开 T98/T99/T101/T102，逐条跑五问重分诊，
      重写 `closed_reason` 或保持 OPEN（T101/T102 倾向排入阶段 5 / 阶段 2；T98 需先审计
      dispatch prompt 前缀构成；T99 需正面回答「change 粒度 vs 仓级 CI 信号」的错位）。
      **MUST NOT 手工搬 `closed/` 文件绕过 recorder 契约**（`issues_v2.py` 拒改终态是
      既有不变量，见 design.md 假设 A3）
      **✅ 2026-08-10 完成**——六条重分诊（含 roadmap 未列的 T97/T100，验收标准覆盖）：
      T98→PROPOSED（排入阶段 4）；T99→WONTDO（粒度错位，verify 全仓 pytest 已兜底）；
      T101→PROPOSED（排入阶段 5）；T102→PROPOSED（fold 进阶段 2）；
      T97→DONE（已由 resolve-models.sh 落地）；T100→WONTDO（理由归真：收益不抵复杂度）
- [x] 1.A.2 新增 todo：SKILL.md 考古层清理——对 SKILL.md **落实 DOC-1 审计**（规则
      `openspec/rules/doc-authoring.md` 从制定起即覆盖 SKILL.md，此前未系统审计过；
      7/14 个 SKILL 超 500 行，修订锚保留界线需人拍板）
      **✅ 2026-08-10 入池 T275**
- [x] 1.A.3 新增 todo：评审编排大改的条件更新（宿主已有 Workflow 确定性编排原语 +
      Stop hook 四级 gate 阶梯；触发条件 = 下次评审编排必须动刀时一并重估）
      **✅ 2026-08-10 入池 T276**
- [x] 1.A.4 顺手关闭已实质落地项：T119（fog-of-war 已是 roadmap 模版硬约束），
      `closed_reason` 写实际落地位置
      **✅ 2026-08-10 T119→DONE**（sdflow-roadmap/SKILL.md:445 硬约束）

#### 1.B 度量补全（change `implement-workflow-optimization-2026-08-p1`）

- [x] 1.B.1 T108 实修率指标：retro join 修复 commit，历史存量回算 per-镜 resolution rate；
      join 歧义规则显式定义，报告 MUST 输出可判定样本数/未知数/覆盖率三数；未达最小
      无歧义样本量的镜，实修率标「参考」不入砍留依据（design.md 假设 A1）
      **✅ 2026-08-10 交付**（change `implement-workflow-optimization-2026-08-p1`，verify PASS）
- [x] 1.B.2 T104 token 维度量：**先定采集机制再实现**——机械路径（hook 读 transcript
      usage，checkpoint 级）vs 自报路径（可信降级标注），在本 change 设计相位定案
      （design.md 假设 A2；wco P2 已确认 harness 无 per-子代理 token，逐镜 token 不做
      机械承诺）；checkpoint 落 token 快照锚 + retro join，新 change 起累积
      **✅ 2026-08-10 交付**（定案自报路径，`token_snapshot.py` + `checkpoint-commit.sh` 接线）
- [x] 1.B.3 retro 报告模版增列（实修率列 + token 列，缺数据显式「无锚」不留空）
      **✅ 2026-08-10 交付**（per-change tokens 列 `out/in/cc/cr` 四计数紧凑串）
- [x] 1.B.4 recorder 增强：`issues_v2.py` 新增 `reopen` 命令（closed→open 原子迁移 +
      终态字段清理 + 历史追加 + reindex），带契约测试；验收核对 canonical issue、目录
      位置与 INDEX/CLOSED 再生一致性（1.A.1 的机械前置）
      **✅ 2026-08-10 交付**（12 个契约测试，全仓 2513 passed）

### 验收标准

- [x] `openspec/retro/report.md` 再生后含实修率列，13 面待复评镜的实修率可读
      **✅ 2026-08-10**（聚合④段 7 行 (layer,lens) 数据，低样本量标「（参考）」）
- [x] 新开任一 change 的 checkpoint 含 token 快照锚（跑一次真实 checkpoint 验证）
      **✅ 2026-08-10**（dogfood `token-log.jsonl` 8 行 anchor=true 真实数据）
- [x] `grep -c "wco roadmap P0-P5 全交付" openspec/issues/CLOSED.md` 对四条错关项归零
      （理由已改写为与事实一致的表述）
      **✅ 2026-08-10**（六条重分诊，含 T97/T100；CLOSED.md 中 count=0）
- [x] 全仓 pytest 绿（retro 脚本改动带同步测试）
      **✅ 2026-08-10**（2513 passed, 10 skipped）

### 交付物

- retro 报告新增两个判据列（阶段 2 的拍板输入）
- issues 池对账完成：4 条重分诊 + 2 条新增 + 1 条实质落地关闭

---

## 阶段 2 · 镜 roster 复评 + 裁决地基改造

### 前置条件

- [x] 阶段 1 已通过全部验收（实修率列 + 覆盖率三数可用）
      **✅ 2026-08-10**（阶段 1 完成总结见 task-log）
- [x] 逐镜确认实修率样本量是否达可判定阈值：未达阈值的镜以独立率 + 人工复核为准
      （design.md 假设 A1 的闸门）
      **✅ 2026-08-10**（`FIXRATE_MIN_SAMPLE=5`，未达阈值格标「（参考）」不入砍留依据）
- [x] 复评护栏确认：冷层（冷主审 / 冷全 diff 审）不在候选砍单（见 design.md 决策 2）
      **✅ 2026-08-11**（13 面镜处置表零冷层淘汰，见 `mirror-dispositions.yaml`）

### 目标

- 13 面待复评镜逐一有处置决定（保留 / 降采样 / 淘汰），每镜依据 = 实修率（达样本量阈值
  时）+ 独立率为主判据，token 维为 per-change 总量趋势参考（逐镜 token 无机械承诺，
  design.md 假设 A2）（见 design.md 决策 1、决策 2）
- 裁决协议不再以裸自报置信 <80 作唯一硬门（见 design.md 决策 2）

### 子任务

#### 2.A 复评 + 裁决改造（change `implement-workflow-optimization-2026-08-p2`）

- [x] 2.A.1 镜 roster 复评：按阶段 1 判据对 13 面镜逐一拍板，产出处置表；弱产出镜优先
      考虑「按 change 类型降采样」而非直接淘汰；SKILL roster 段同步改动。**roster 改动
      与 2.A.2 裁决协议改动落独立 commit，可分别 revert**（design.md 决策 2）
      **✅ 2026-08-11 交付**（commit A 独立）——`openspec/retro/mirror-dispositions.yaml`
      13 面镜处置：11 保留 + history 降采样（条件化：diff ≥200 行 / 含 rename 才派）+
      1 不适用；SKILL roster 段条件化 + `retro_report.py` 处置注记（yq 解析，三态错误语义）
- [x] 2.A.2 T106 裁决协议改造：二元 pass/fail + critique / severity 三级 / 置信降级排序
      信号——形态在该 change 设计相位定（以实修率数据为输入）
      **✅ 2026-08-11 交付**（commit B 独立）——D2 拍板合成形态（`openspec/adr/0041`）：
      机械前置门 → 二元裁决（采纳/裁掉/defer + critique）→ 置信降级为排序信号；<80 硬滤、
      置信封顶、跨模型豁免矩阵条款全删；历史重放部署门：5 份归档报告 49 条 finding 重裁，
      ③类（协议缺陷）= 0
- [x] 2.A.3 T112 弱档 validator 复核层：置信过滤（或其替代）后加一级 findings 引用真实性
      复核
      **✅ 2026-08-11 交付**——`findings_ref_check.py` 机械引用核（三查三态 + 崩溃降级，
      20 pytest），作为裁决协议的机械前置门（与 2.A.2 合成，见 adr/0041）
- [x] 2.A.4 lens-metric emitter 输入 schema 兼容 + retro 再生冒烟（裁决输出格式变更不得
      破坏度量锚）
      **✅ 2026-08-11 交付**——lens-metric contract v2 合法组合扩展，`anchor_lint` CLEAN，
      retro 再生冒烟通过
- [x] 2.A.5 评估在 sdflow-done 收尾（verify/archive/merge）加终态 token 快照——p1 设计门
      Q2 拍板遗留：最后一次 checkpoint 之后的用量对每个 change 系统性缺失（稳定同向偏差，
      p1 已脚注呈现）；评估结论可为「做」或「明确不做并记因」
      **✅ 2026-08-11 评估结论 = 做，已交付**——`sdflow-done` §3.0 接入
      `token_snapshot.py --step done-final` + host 判定补丁（codex/unknown 不走 mtime
      fallback）+ retro join 冒烟

### 验收标准

- [x] retro 报告「待复评」区块清空或逐镜带处置记录
      **✅ 2026-08-11**（13 面镜逐镜带「已处置: 保留/降采样/不适用」注记）
- [x] 评审 SKILL 的 Step3 条款与新裁决协议一致，anchor_lint 全绿
      **✅ 2026-08-11**（两评审 SKILL Step3 重写与 adr/0041 一致；anchor_lint CLEAN）
- [x] 改造后真实 change 评审 dogfood：按预定义指标**分别判读**——漏检信号归因 roster
      改动、噪声/采纳率信号归因裁决协议（观察窗口与阈值在该 change 设计相位定；历史
      评审语料重放作为候选验证手段一并评估）
      **✅ 2026-08-12 窗口判读完成（3/3：p2/p3/remove-superpowers-pipeline）**——
      ① 漏检（归因 roster）：无——三样本归档后池内零新增缺陷，rsp 大 diff 正确触发
      history 镜条件化派发 ⇒ roster 改动 PASS；② 采纳率偏移（归因裁决协议）：spec-review
      侧 p3 96% / rsp 100%（≥基线 87-93%）；code-review 侧表面 43-46% vs 基线 73%，但
      口径不同构（旧协议置信硬滤在入池前静默丢弃、新协议全量入池显式裁掉），裁掉项逐条
      复核全部合法（Speculative Generality / 实查证伪 / 非问题）⇒ 裁决协议 PASS，无需
      回滚。附带发现两条与 p2 改动无关的既有断链（B25 code-review 报告机械层落盘自
      08-07 起静默缺失、B26 defer 入池通道 3/3 断），已入池；漏记 defer 补录 T278-T280
- [x] 全仓 pytest 绿
      **✅ 2026-08-11**（2549 passed, 10 skipped）

### 交付物

- 13 面镜处置表 ✅（`openspec/retro/mirror-dispositions.yaml` + retro 报告逐镜注记）
- 新裁决协议 ✅（`openspec/adr/0041` + 两评审 SKILL Step3 + `findings_ref_check.py` 机械前置门）

### 遗留（如实记录）

- **T102（对抗镜措辞收紧）fold 计划未执行**：阶段 1 重分诊曾拍板「fold 进阶段 2，随裁决
  协议一起改」，但 p2 实际 scope（decision-memo D2 / tasks.md）未纳入对抗镜 dispatch prompt
  的措辞收紧。处置：挂验收 3 观察窗口结论后重判——若采纳率偏移显示噪声仍高，再收紧措辞
  源头；若二元裁决已足够压噪，T102 改 WONTDO 记因。
  **✅ 2026-08-12 已按预定规则重判 T102 → WONTDO**（窗口 3 样本显示二元裁决足够压噪：
  spec-review 采纳率 ≥ 基线，对抗镜无高噪声证据——rsp spec 对抗镜 10 findings 全采纳、
  独立 5，为当轮最高产镜）。
- hand-off 残项 D1–D5（docs 六处旧协议描述同步、ref-check 路径穿越防护、done-final 降级
  确认、前瞻窗口判读、README 等一行描述）见
  `openspec/changes/archive/2026-08-11-implement-workflow-optimization-2026-08-p2/hand-off.md`。

---

## 阶段 3 · 上游套件吸收机制

**阶段目标**：建立四源（gstack / superpowers / matt 套件 / OpenSpec CLI）的版本锚与
delta 分诊机制（`sdflow-upstream-watch`，数据类 skill），一次运行产出「锚点以来
可吸收项」报告，吸掉 T264/T245/T246/T267 散点（见 design.md 决策 3）。

### 前置条件

- [x] 阶段 1/2 已归档，无阻塞依赖（阶段 3 本无入边，可独立起手）
      **✅ 2026-08-11**
- [x] `/sdflow-spec implement-workflow-optimization-2026-08-p3` 相位 B 拷问补细：
      D1 scope 边界（只建机制，T264 一关三留）/ D2 触发节奏（手动 + upgrade 轻提醒）/
      D3 上游观察面（superpowers 盯 marketplace 仓、matt 盯上游全量）等拍板
      **✅ 2026-08-11**（decision-memo.md D1–D3，过 spec-review HARD-GATE）

### 目标

- 四源采集器（gstack / matt / superpowers / openspec）零解析出 delta 事实，单源失败
  降级、不互相传染（design.md 基准 5 + 决策 3）
- `anchors.yaml` 只由脚本维护，锚推进与本轮报告+facts 绑定（R1）
- `sdflow-upstream-watch` SKILL 编排出人可拍板的三分诊报告，入池衔接经 recorder
  显式 `source_change`（R4/R5）
- T264 收口关闭；T245/T246/T267 作为首轮报告 seed 分诊条目，池内原状保留（D1）

### 子任务（tickets 管线，change `implement-workflow-optimization-2026-08-p3`）

- [x] Task 1 脚手架 + anchors 基础设施 + cwd 守卫
      **✅ 2026-08-11 交付**——SKILL.md 骨架 + 通则托管块注入、`openspec/upstream/` 目录、
      cwd 守卫（git remote 判定 fail-loud）、anchors.yaml 三态读写（yq mikefarah 探测）
- [x] Task 2 四源采集器 + facts 输出 + advance 门
      **✅ 2026-08-11 交付**——gstack/matt/superpowers/openspec 四采集器、bare 缓存自愈、
      is-ancestor 锚祖先守卫、facts JSON 输出、advance 报告+facts 双参数绑定门
- [x] Task 3 SKILL 编排层 + 消费端
      **✅ 2026-08-11 交付**——SKILL.md 编排正文（collect→报告→advance→呈报）、首轮 seed
      条款（T245/T246/T267）、入池衔接模板、`sdflow-upgrade` 第 5 步提醒段、README 登记
- [x] Task 4 首轮 dogfood + 收口
      **✅ 2026-08-11 交付**——真实四源网络 collect + 报告落盘 + advance 建锚；
      T264→DONE（evidence 指 schema drift 采集器）；T245/T246/T267 池内原状保留
- [x] Task 5 实现验证收尾
      **✅ 2026-08-11 交付**——全仓 `/usr/bin/python3 -m pytest -q`：2607 passed,
      10 skipped（SHA `7e1e06d`）；集成/e2e 层判定「本仓无该层」，Task 4 手工验收作旁证
- [x] code-review 修复（6 项 finding 采纳）
      **✅ 2026-08-11 交付**——advance 报告读取异常保护、schema drift OSError 不再丢版本
      数据、错误消息路径脱敏（`_tildify`）、SKILL.md 缓存路径模板改真实路径、
      `_observed_anchor` 拒绝 null 锚（新增 2 项契约测试）、本节 roadmap 回填
      （标 `[impl-review-fix]`）

### 验收标准

- [x] 首轮 `/sdflow-upstream-watch` 真实运行产出报告 + 锚已建立
      **✅ 2026-08-11**（`openspec/upstream/reports/` 首份报告 + `anchors.yaml` 首轮建档）
- [x] 全仓 pytest 绿
      **✅ 2026-08-11**（2607 passed, 10 skipped；本轮 fix 后复测仍绿，60/60 skill 内测试）
- [x] change 归档（code-review → sdflow-done → merge）
      **✅ 2026-08-11**（code-review 6 项修复 → verify PASS → archive → merge main，SHA `c4b8c6f`）

### 交付物

- `sdflow-upstream-watch/`（SKILL.md + `scripts/upstream_watch.py` + `tests/`）新 skill
- `openspec/upstream/anchors.yaml`（首轮建档）+ 首份分诊报告
- T264 收口关闭；`sdflow-upgrade` 陈旧提醒段接入

**雾区备注（已解除，保留存档）**：原「锚文件格式、四源采集器各自的锚信号、触发节奏、
与 setup-matt-pocock-skills 既有 triage-labels 的关系」等待拍板项，均已在
`/sdflow-spec implement-workflow-optimization-2026-08-p3` 相位 B 拷问中定案
（decision-memo.md D1–D3），不再是雾区。

---

## 阶段 4 · 成本工程剩余

**阶段目标**：把宿主原生 effort 分档吃满——T105（thinking/effort 按步分档）+ T103
（每镜 effort 预算 + 输出封顶）+ T124（规则注入分界）+ 重分诊后存活的 T98（前缀缓存）
落地（见 design.md 决策 1 的度量前置逻辑）。

### 子任务（tickets 管线，change `implement-workflow-optimization-2026-08-p4`）

- [x] Task 1 effort 维解析与导出全链（model-tiers 机读块 + resolve-models.sh 9 变量 + config 覆盖）
- [x] Task 2 effort agent 定义铺设（5 个 sdflow-effort-*.md + install_agents 测试）
- [x] Task 3 ship_gate B25/B26 机械门（锚存在门 + defer 对账门 + 32 测试）
- [x] Task 4 render-review-prefix.sh 段① 渲染器（byte-stable + fail-loud + 14 测试）
- [x] Task 5 四编排 SKILL 全面适配 + B25 诊断修复 + bundle 同步（15 lint 测试）
- [x] Task 6 实现验证收尾（2639 passed, 0 failed）
- [x] code-review（零 findings）
- [x] B25/B26 断链修复（诊断=emitter 未调用；修复=SKILL Step7 独立步 + gate 机械门双保险）

### 验收标准

- [x] 全仓 pytest 绿
      **✅ 2026-08-12**（2639 passed, 10 skipped）
- [x] effort 全链生效（resolver 导出 + agent 定义 + SKILL 派发接入）
      **✅ 2026-08-12**（A1 探针方向性确认 + 43 resolver 测试 + 14 install_agents 测试）
- [x] B25/B26 门机械守住（本 change 自身 code-review 为首个 dogfood）
      **✅ 2026-08-12**（code-review-report.md 含 lens-metric + ref-check 锚，gate 放行）
- [x] change 归档（code-review → sdflow-done → merge）
      **✅ 2026-08-12**（verify PASS → archive → merge main，SHA `e202feb`）

### 交付物

- `model-tiers.md` effort 机读块 + `resolve-models.sh` 9 变量导出
- 5 个 `sdflow-effort-*.md` 全局 agent 定义
- `render-review-prefix.sh` 段① 渲染器
- `ship_gate.py` B25/B26 双门（锚存在 + defer 对账）
- 四 SKILL effort 派发 + 三段组装序 + defer 当场入池改造
- `openspec/adr/0043`（effort 分档经全局 effort-keyed agent 定义）

---

## 阶段 5 · 人类门减负与 context 工程

**阶段目标**：压设计门人读墙钟（重分诊后的 T101 三层摘要头 + 拍板三问为主力候选）+
SKILL.md 考古层清理（1.A.2 入池项的执行）+ compaction/PreCompact 落盘（T256 同题合并）。

**雾区备注**：缺三件事——1.A.1 对 T101/T102 的重分诊结论、1.A.2 考古层保留界线的人工
拍板、阶段 2 改造后设计门报告的实际形态（摘要头设计依赖报告结构稳定）。到 frontier 补细。

---

## 附录 A · 阶段间依赖图

```
阶段 1（度量 + 池对账）──▶ 阶段 2（复评 + 裁决改造）──▶ 阶段 5（人类门减负，部分依赖）
        │
        └────────▶ 阶段 4（成本工程，依赖 token 基线）

阶段 3（上游吸收机制）    （独立，无任何入边/出边；可先于阶段 1/2 起手）
```

## 附录 B · 子任务总数与估时

| 阶段 | 子任务数 | 时长预估（定性） |
|---|---|---|
| 阶段 1 | 8（1.A×4 + 1.B×4） | **✅ 8/8 完成 2026-08-10** |
| 阶段 2 | 5（2.A×5） | **✅ 5/5 完成 2026-08-11**（验收 3 窗口判读 ✅ 2026-08-12） |
| 阶段 3 | 5（tickets 管线 Task1–5） | **✅ 5/5 完成 2026-08-11**（含 code-review 修复，归档 SHA `c4b8c6f`） |
| 阶段 4 | 8（tickets 管线 Task1–6 + CR + B25/B26） | **✅ 8/8 完成 2026-08-12**（verify PASS 2639 tests，归档 SHA `e202feb`） |
| 阶段 5 | （雾区——frontier 到达补细后再登记） | — |
| **合计**（仅计入近期已细化阶段） | **18** | — |

## 附录 C · 未来 OpenSpec 变更映射

| 阶段 | 建议变更名 | 引用契约 |
|---|---|---|
| 阶段 1 | `implement-workflow-optimization-2026-08-p1` **✅ 归档 2026-08-10**（1.B 四项交付，verify PASS；1.A 为 recorder 直写操作，待独立执行） | spec-workflow（度量锚相关 Requirement） |
| 阶段 2 | `implement-workflow-optimization-2026-08-p2` **✅ 归档 2026-08-11**（2.A 五项全交付，verify PASS；验收 3 窗口判读 ✅ 2026-08-12 双 PASS） | spec-workflow（评审编排 Requirement） |
| 阶段 3 | `implement-workflow-optimization-2026-08-p3` **✅ 归档 2026-08-11**（5/5 ticket + code-review 修复，verify PASS 2607 passed，SHA `c4b8c6f`） | — |
| 阶段 4 | （雾区——frontier 到达补细后再登记） | — |
| 阶段 5 | （雾区——frontier 到达补细后再登记） | — |

每个实施变更的 proposal 引用本文件对应阶段作为背景，design 复用
`openspec/roadmaps/workflow-optimization-2026-08/design.md`，specs 扩展
`openspec/specs/spec-workflow/`（如涉及）。

## 附录 D · 任务完成追踪

执行过程中同步更新 `task-log.md`：完成一个显著子任务或子任务组即追加一条；遇计划外
情况（预期外问题、决策调整、规范扩展）必须记录；每阶段全部完成后追加「阶段 N 完成
总结」里程碑。详见 `task-log.md` 使用约定。
