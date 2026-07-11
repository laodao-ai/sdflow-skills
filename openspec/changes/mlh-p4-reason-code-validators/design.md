> **grill 收敛记录（2026-07-11）**：全深度 grill 逐分支死磕，逮出 3 个实现前的真洞并收敛——T81 高风险**假阴**（Q1→B）、T82 **假绿-薄**（Q2→C）、T80 **假新鲜**（Q3→(1)+(i)，D1 反转）；次级分支 batch（Q4）；首个试点适配性复检（Q5→继续）。改动段标 `[grill-amendment]`。另修一处 grill 查码揭穿的引用错误（D2/Compliance 的「ADR-11」不实，改引代码先例）。统一原则升格 **adr/0018**。

## Context

MLH 阶段 4·4.D：三处评审 / 规划步各有一段模型手做的机械判定，按 adr/0006(b)「凡机械 prose 协议 MUST 脚本化」下沉为三个同型 reason_code 确定性校验器。同族 4.C `lens_metric_emit.py`（merge `bd7c05f`）已立形态样板。三者逻辑独立、依赖图稀疏，本 change 亦选作首个 tickets 实现管线试点。

**接地事实（已核验，带锚）：**

- **形态样板** `openspec/workflow/tools/lens_metric_emit.py`：stdlib-only（`argparse/json/re/sys/pathlib`），`EmitError` + `EXIT_OK/EXIT_FAIL=0,1`，all-or-nothing fail-closed（任一坏输入 raise→`main` 捕获 `return EXIT_FAIL` 且**不产部分输出**，`:190-194`）；单一源契约用 fenced 机读块读；跨模块口径**重实现不 import**（`_read_block_pairs` 重实现 anchor_lint 口径，`:19-43`）；本地常量豁免先例 `VERDICTS`（`:9`：输入独有、不写进锚、不与他模块共享）。
- **T80** outside-voice 复用守卫：**spec-review 专属**（code-review 恒重跑 code-voice，无对称守卫，`sdflow-code-review/SKILL.md:88`）。现状手做步 `sdflow-spec-review/SKILL.md:39-44`「三前置·R2」：①来源（读 `gstack-review.md` 的 `step1-broad-review` 锚 `mode`，`simulated`→无效）②新鲜度（产物 mtime < `git log -1 --format=%ct -- {change_dir}`→陈旧）③结构（文件缺失 / 解析不出 codex 段 / findings=0）。reason_code 现状六枚举 `none|file-missing|section-not-found|zero-findings|stale|simulated-source`（仅存于 SKILL.md 锚注释 prose `:179`，code-review 侧 `:169` 同款 guard 字段）。codex 段格式（`codex#N` 标签）**gstack 外部所有**，adr/0002:21 明定其改名「只触发降级回落、不静默失效」。**〔grill 揭穿〕** 新鲜度用 `git log` 时间**看不到未提交改动** → 工作树 dirty 时**假新鲜**（复用陈旧审查）；此坑已登记 todolist T33/T35。
- **T81** HR-TG 交集：HR-TG 子集单一源 `trigger-catalog.md:127-131`「## 七、HR-TG 子集」→ `> 成员：**TG-04, TG-06, TG-07, TG-08, TG-09, TG-16, TG-17, TG-26**`（8 个，blockquote prose）。匹配先例 `sdflow-ship/scripts/ship_gate.py:tg02_hit`（`:495-519`）三道防线：①fence-aware ②只扫头部声明区（首个 `## ` 前）③只认 strip 后 `startswith("〔TG")` 声明行。proposal 头部 `〔TG-NN：…〕` 声明约定已证（`gate-anchor-line-scoped/proposal.md:3`）。**〔grill 查码确认〕** 全仓**无**「proposal 须声明全部命中 TG」的机械强制——欠声明会让高风险 TG 假阴。`openspec/workflow/` 下**无** trigger-catalog 副本，须从 `$RULES_ROOT/trigger-catalog.md` 读。
- **T82** roadmap Review 对账：小节标题精确 `## Review 处置`（模版 `sdflow-roadmap/references/task-log-template.md:62`）；状态枚举单一源 `sdflow-roadmap/SKILL.md:312-316`。**格式三实例不统一**（bullet / 表格单元格 / 分组组头）；task-log **无任何 `sdflow:` 机读锚**；收尾句「本小节**无**『未处置』状态条目」**含子串「未处置」**（裸子串假阳，同 memory `gate-substring-detection-dogfood`）。

## Goals / Non-Goals

**Goals：**
- 三处机械判定下沉为三个 fail-closed、门控外置（不读 config）的确定性校验器，出 reason_code 退出码。
- 各校验器口径锚定各自单一源（HR-TG 不硬编码、matching 复用 tg02_hit 声明式口径），改单一源即生效。
- **不可验输入须在输出信号里可见**（adr/0018）：T81 输出带「已声明依据」、T82 输出码点明 `DISPOSITION-UNCHECKED`、T80 dirty→fail-safe `stale-dirty-tree`——不向消费方投射假信心。
- 三处 SKILL.md 手做 prose → 「调校验器」，判断 / 编排语义保留给模型；每校验器配 pytest（正例 + 坏输入 fail-closed 非零退出）。

**Non-Goals：**
- 不替代模型 / 人的判断（采纳 / 处置 / 复用与否的裁决）。
- **T82 不断言「逐条已处置」**、**T81 不强制声明完整性**（均机械不可达 / 属模型职责，见 D3/D4）。
- 不做 4.D.3（待 embedded 契约）/ 4.A；不引第三方依赖；不改 setup.sh。
- 试点执行机制（config 翻键 / PIPELINE_RECEIPT / 档位钉死）不入本设计。

## Decisions

### D1〔TG-23〕T80 输入契约 + 新鲜度所有权 `[grill-amendment]`（Q3 反转初版）
**决策（反转）：outside_voice_guard 自己跑 git，做「新鲜度事实」的天然 owner；工作树 dirty 时 fail-safe 判 `stale-dirty-tree`。** 入参 = `gstack-review.md` 路径 + `{change_dir}`；脚本自跑 `git log -1 --format=%ct -- {change_dir}`（新鲜度）+ `git status --porcelain -- {change_dir}`（dirty 检测），parse `step1-broad-review` mode，best-effort parse codex 段 → 归约单一 reason_code。
- **为何反转初版（初版：mtime 由 SKILL 传参、脚本保纯）**：① git-log **看不到未提交改动**的语义 bug 与「谁跑 git」无关；② 初版把 git 调用挪进**没测的 SKILL prose**，是接缝转移不是消除。新鲜度是 git 派生事实，脚本自持 + git-fixture 测才可锁死。
- **dirty fail-safe**：change_dir 工作树 dirty → git-log 时间不可信 → 无法确认新鲜 → 输出 `stale-dirty-tree`（保守重跑 outside-voice；**重跑只是成本、复用陈旧才是危害**，安全方向朝 stale）。承 `archived_verify_state` 判不准→保守的 tri-state 诚实先例 + adr/0018。
- **纯度代价**：T80 成为唯一带 subprocess 的同族校验器（D5 显式例外），换来新鲜度正确性；hr_tg / review_disposition 仍纯。**主次**：新鲜度正确 > stdlib 纯度洁癖。

### D2〔TG-23〕T80 reason_code 枚举落点
**决策：枚举留脚本本地常量（`lens_metric_emit.py:9` 的 `VERDICTS` 本地常量先例），不进 fenced 契约块。** 依据：该枚举**输入独有、不与其它模块共享、本脚本不把它写进任何跨模块共享锚**（guard 字段由 SKILL / 模型 emit 进 outside-voice 锚，非本脚本职责）。〔grill 修：初版误引「ADR-11」为豁免依据——adr/0011 实为「共用解析核心返回语义」，与本地常量无关；改引代码先例。〕
- **备选（否决）**：新增 fenced 契约块。→ 过度工程；无第二消费方、无跨模块漂移面。
- 新鲜度反转（D1）新增第 7 码 `stale-dirty-tree` → 七枚举 `none|file-missing|section-not-found|zero-findings|stale|stale-dirty-tree|simulated-source`；落点判据不变。

### D3〔TG-23〕T81 输入来源 + 假阴诚实 `[grill-amendment]`（Q1→B）
**决策：泛化 `tg02_hit` 扫 proposal 头部声明区全部 `〔TG-\d\d` 得命中集，交 HR-TG 子集，输出不 emit 裸 `none`——emit `none｜依据已声明:[TG-01,TG-19]`（把输入依据显式暴露）。** 交集非空则 `hit:[...]｜依据已声明:[...]` + 规范锚串。HR-TG 子集从 `trigger-catalog.md` `## 七、HR-TG` `> 成员：` 行 parse（单一源不硬编码）。
- **为何暴露依据（grill 揭穿的高风险假阴）**：机械校验器**无法**知道真实命中集（那要判 change 内容 = 模型领域）；若作者漏声明高风险 `〔TG-07〕`，裸 `none` 会静默绿灯放行「跳过强制领域 cross-model」——**安全门假阴**。暴露「依据已声明的哪些 TG」让复审者一眼能 sanity-check「是不是漏声明」，把不可验的输入依赖变可见（adr/0018）。
- **完整性强制**（声明 vs 实际命中）是模型 / spec-review 职责，**不塞进机械校验器**（Non-Goal）。
- **备选 A（否决）**：模型传入 TG 列表——把手做塞回模型，漂移未消除。

### D4〔TG-23〕T82 机械天花板 = 去危险的诚实信任边界 `[grill-amendment]`（Q2→C，留门已裁=保留）
**决策：脚本只断言「`## Review 处置` 小节存在 + 非空」，reason_code = `section-missing|section-empty|section-ok-DISPOSITION-UNCHECKED`；输出码本身点明「逐条已处置未核」，SKILL 接入步显式划界「逐条处置是你的活」。** 保留三合一（设计门 Q5 已裁）。
- **为何输出码带 `-DISPOSITION-UNCHECKED`（grill 揭穿的假绿）**：一个只查「存在+非空」却叫 `review_disposition_check` 的工具，`present ✓` 极易被误读成「处置已核」——即 mlh F1 `check_lens_metric` truthy **假过门**同型。**薄不可怕，假装不薄才可怕**——输出码把信任边界焊进信号本身（adr/0018）。
- **为何不做「逐条已处置」**：格式三实例不统一 + 「未处置」无字面 token + 收尾句子串自指陷阱 → 子串 / 单行正则必假阳或假绿。**MUST NOT naive-grep `未处置`**；测试须含「收尾声明句不触发命中」负例（fence / 结构感知，memory gate-substring-detection）。
- **保住的真价值**：防真空通过（小节缺失≠无未处置）+ 防子串陷阱（memory 实证反复踩）+ 维持 3 票 frontier（试点目的）。

### D5 三者共性契约（承 4.C 形态）+ T80 git 例外 `[grill-amendment]`
`EmitError`+`EXIT_OK/EXIT_FAIL=0,1` all-or-nothing fail-closed（坏输入非零退出、不产部分输出）；门控外置（不读 config）；跨模块口径重实现不 import；`argparse main(argv=None)`；单一源缺失 / 不可读 → fail-closed 非零退出 + stderr 原因。
- **stdlib-only 例外**：`hr_tg_intersect` / `review_disposition_check` 纯 stdlib、无 subprocess；**唯 `outside_voice_guard` 因新鲜度事实需 `git`（D1）**——显式例外，用 git-fixture 测，不沉默。

## Risks / Trade-offs（grill 后）

- **[T80 codex#N 外部格式变]** → best-effort parse 失败 fail-closed 到 `section-not-found`（adr/0002:21 明许）。
- **[T81 高风险假阴]**（已收敛 Q1/B）→ 暴露「已声明依据」使假阴可见；完整性强制归 spec-review，非本脚本兜底。
- **[T82 假绿-薄]**（已收敛 Q2/C）→ 输出码点明 UNCHECKED + SKILL 划界 + 子串陷阱负例。
- **[T80 假新鲜]**（已收敛 Q3）→ dirty→fail-safe `stale-dirty-tree`；接 T33/T35 已知账。
- **[bundle 回灌遗忘]** → Migration 段固化操作序。

## 失败模式表〔TG-08〕

| 校验器 | 坏输入 / 失败 | 行为（fail-closed / fail-safe） | 可观测 |
|---|---|---|---|
| 三者共性 | 单一源 / 输入文件缺失或不可读 | `EXIT_FAIL`，不产部分输出 | `[<tool>] FAIL: <原因>` |
| T80 | `step1-broad-review` 锚缺失 / mode 非枚举 | `EXIT_FAIL`（区别于 `simulated-source` 判定） | 锚解析失败原因 |
| T80 | codex 段不可 parse | 归约 `section-not-found`（非崩溃） | 正常输出该码 |
| T80 | change_dir 工作树 **dirty** | **fail-safe** `stale-dirty-tree`（保守重跑，非假新鲜） | 正常输出该码 |
| T81 | `## 七、HR-TG` 段 / `> 成员：` 行缺失 | `EXIT_FAIL`（单一源损坏不静默空交集） | HR-TG 单一源缺失 |
| T81 | proposal 无头部声明 / 交集空 | `none｜依据已声明:[]`（依据可见，非静默 none） | — |
| T82 | 小节缺失 / 仅脚手架 | `section-missing` / `section-empty`（非真空通过） | — |

## 组件 / 数据流图〔TG-11/组件图〕

```
单一源（各自，不硬编码）                 校验器（sdflow-init/assets/workflow/tools/）           消费方 SKILL
─────────────────────────                ──────────────────────────────────────────           ──────────────
gstack-review.md(step1锚+codex段) ┐  自跑 git
{change_dir}(git mtime + dirty) ──┼───►  outside_voice_guard.py ──► reason_code(7枚举,含stale-dirty) ─►  sdflow-spec-review(复用守卫步)
                                  ┘
proposal.md 头部〔TG声明 ─────────┐  纯 stdlib
trigger-catalog.md 七.HR-TG成员 ──┼───►  hr_tg_intersect.py ─────► hit/none｜依据已声明:[...] ──────►  sdflow-spec-review / sdflow-code-review
                                  ┘
roadmap task-log ## Review 处置 ── 纯 stdlib ► review_disposition_check.py ► section-*｜...-DISPOSITION-UNCHECKED ►  sdflow-roadmap(收尾 checklist)

  权威源改动 ──sdflow-init update──► openspec/workflow/tools/(下游副本) ；消费方经 $RULES_ROOT/tools/<名>.py 调用
  三校验器互不 import、互不依赖（依赖图稀疏 → tickets frontier 天然 3 宽独立；T80 因 git+新鲜度+parse 是最重单链）
```

## Migration Plan（bundle 回灌纪律）

1. 三校验器 + 测试写入**权威源** `sdflow-init/assets/workflow/tools/(tests/)`（唯一真相源，CLAUDE.md）。
2. 改三处 SKILL.md（`sdflow-spec-review` / `sdflow-code-review` / `sdflow-roadmap`）手做步 → 调 `$RULES_ROOT/tools/<名>.py`；T82 接入步显式写「逐条处置是你的活」。
3. dev checkout **跑一次 `bash setup.sh`**（同步 `~/.sdflow/` canonical，否则测不到）。
4. `sdflow-init update` 推 `openspec/workflow/tools/` 下游副本。
5. **回滚**：删三 tool 文件 + 还原三 SKILL.md 手做步；无数据迁移、无消费方破坏。

## Open Questions

- 三校验器精确文件名（`outside_voice_guard.py` / `hr_tg_intersect.py` / `review_disposition_check.py`）为建议名，spec-review 可微调。
- （D4「保留 vs 剥离」已于设计门 Q5 裁定 = 保留三合一，出清。）

## Compliance

- **adr/0006(b)**「凡机械 prose 协议 MUST 脚本化」：正向落实（三处手做→脚本）。
- **adr/0018（本 change 新立）**「机械校验器输出诚实」：不可验输入须在信号里可见（T81 依据 / T82 UNCHECKED / T80 fail-safe），不向消费方投射假信心；引 adr/0008（防御纵深不信任纪律）+ adr/0016（报告工具反静默）为家族。
- **「机械活交脚本、模型只做判断」**：脚本只出信号，不做裁决；T80 取 git 事实是环境动作、非判断。
- **单一源原则**：HR-TG 从 `trigger-catalog.md` 读、T80 枚举本地常量（`lens_metric_emit.py:9` 先例）、T82 状态枚举锚 `sdflow-roadmap/SKILL.md`——无第二真相源。
- **bundle 回灌纪律**（CLAUDE.md）：改 `assets/workflow/` 权威源须 `sdflow-init update` + dev 跑 setup.sh，无沉默例外。
- **stdlib-only / 门控外置 / fail-closed**：承 4.C（D5），无第三方依赖、不读 config、坏输入非零退出；**唯 T80 显式 git 例外**（D1/D5）。
