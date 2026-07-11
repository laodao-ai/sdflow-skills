> **grill 收敛（2026-07-11）**：全深度 grill 逮 3 个实现前真洞——T81 假阴（Q1→B）、T82 假绿（Q2→C）、T80 假新鲜（Q3）；升 adr/0018。
> **spec-review 收敛（2026-07-11，5 镜冷审）+ 设计门拍板**：冷层推翻/订正 grill 两处 + 定 T82 去留 + 修 2 design bug，改动标 `[spec-review-amendment]`：
> - **Q-C（撤销 grill Q3 的 git 反转）**：T80 新鲜度改「源文件 fs-mtime vs 产物 fs-mtime、排除评审产物」——fs-mtime 本就捕获未提交编辑，**无需 git**；grill Q3「自跑 git + `stale-dirty-tree` 第7码」撤销，T80 回纯 stdlib、回 6 码。（grill Q3 的 dirty→全目录扫描会把评审产物自身算进 dirty→守卫恒判 stale→双 codex，冷镜 F1 揭穿。）
> - **Q-D（推翻 grill Q1）**：T81 输入改**模型传入命中 TG 集**（grill Q1 否决的备选 A）——冷镜爆点5 证明「读 proposal 声明」根本捕不全（TG 声明散落 proposal 括号/design section 锚，本 change 的 TG-08 就在 design.md）；「命中哪些 TG」无确定性信号=判断归模型，脚本只做 ∩ HR-TG 子集 + 出锚。
> - **T82 保留**（设计门裁）：靠自身 merit（把防真空守卫机械化成不可跳，adr/0006），删 D4 原「凑 3 票 frontier」justification（自指矛盾）。
> - **adr/0018 降 Proposed**：从未实现样例蒸馏，待首形态 ship+dogfood 再升 Accepted。

## Context

MLH 阶段 4·4.D：三处评审 / 规划步各有一段模型手做的机械判定，按 adr/0006(b)「凡机械 prose 协议 MUST 脚本化」下沉为三个 reason_code 确定性校验器。同族 4.C `lens_metric_emit.py`（merge `bd7c05f`）立形态样板。本 change 亦选作首个 tickets 试点（跨桶/confounding caveat 记入 pilot 执行记录）。

**接地事实（已核验，带锚）：**

- **形态样板** `openspec/workflow/tools/lens_metric_emit.py`：stdlib-only、`EmitError`+`EXIT_OK/EXIT_FAIL=0,1`、all-or-nothing fail-closed（`:190-194`）、单一源契约 fenced 机读块、重实现不 import、本地常量豁免先例 `VERDICTS`（`:9`：输入独有、不写进锚、不与他模块共享）。
- **T80** outside-voice 复用守卫：**spec-review 专属**（code-review 恒重跑，`sdflow-code-review/SKILL.md:88`）。三前置 `sdflow-spec-review/SKILL.md:39-44`：①来源（`step1-broad-review` 锚 mode，simulated→无效）②新鲜度③结构（codex 段/findings）。reason_code 六枚举锚 `:180`。codex#N 外部所有，adr/0002:21「改名只降级回落」。**〔spec-review Q-C〕现状手做用 `git log`（看不到未提交）→ 本 change 改 fs-mtime 直比，无此坑、无需 git。**
- **T81** HR-TG 交集：HR-TG 子集单一源 `trigger-catalog.md:127-131`（TG-04/06/07/08/09/16/17/26，8 个）。**〔spec-review Q-D〕命中 TG 集无可靠机械来源**——声明散落 proposal 括号 `（TG-01）`/design section 锚 `## …〔TG-08〕`（本 change 即如此），tg02_hit 头部扫描抓不全 → 命中判定归模型、非脚本。
- **T82** roadmap Review 对账：小节 `## Review 处置`（模版 `task-log-template.md:62`）；替换 `sdflow-roadmap/SKILL.md:344-346` 收尾 checklist ① 的**存在半场**（(b) 小节缺失=不通过、防真空）；**逐条无未处置 (a) 仍归模型**（机械不可达）。状态枚举锚 `SKILL.md:312-316`。收尾句「无『未处置』」子串陷阱（memory `gate-substring-detection-dogfood`）。

## Goals / Non-Goals

**Goals：** 三处机械判定下沉为 fail-closed、门控外置、**纯 stdlib**（Q-C 后无 subprocess）的确定性校验器；口径锚定各自单一源；**不可验输入在信号里可见**（adr/0018）：T81 `依据模型判定:[...]`、T82 `-DISPOSITION-UNCHECKED`、T80 新鲜度 fail-safe；判断/编排保留给模型；各配 pytest。

**Non-Goals：** 不替代裁决；**T82 不断言逐条已处置**、**T81 不判命中哪些 TG**（均归模型）；不做 4.D.3/4.A；不引第三方依赖；不改 setup.sh；试点执行机制不入设计。

## Decisions

### D1〔TG-23〕T80 新鲜度：源文件 fs-mtime 直比、纯 stdlib `[spec-review-amendment Q-C]`
**决策：freshness = 产物 `gstack-review.md` 的 fs-mtime vs 源文件（proposal/design/tasks/specs）最大 fs-mtime，产物较旧 → `stale`；排除评审产物自身（gstack-review.md / spec-review-report.md / .outside-voice/）。纯 stdlib，无 subprocess。** 入参 = `gstack-review.md` 路径 + `{change_dir}`；脚本 os.stat 比 mtime、parse mode、best-effort codex parse → 6 枚举 `none|file-missing|section-not-found|zero-findings|stale|simulated-source`。
- **为何 fs-mtime 而非 git**：fs-mtime 直接捕获未提交编辑（原 `git log` 之坑的根治）；且「产物 vs 源文件」正确界定 staleness（评审产物自身未提交不算源变动）。
- **撤销 grill Q3**：Q3 曾反转为「自跑 git + dirty 全目录扫描 + `stale-dirty-tree`」——但全目录 dirty 含评审产物自身 → 守卫恒判 stale → 双 codex（冷镜 F1 揭穿反噬）。fs-mtime 直比无需 git、无需 dirty、无第 7 码，更简更准。
- **主次**：源文件对比 fs-mtime > git-log/全目录 dirty。

### D2〔TG-23〕T80 reason_code 枚举落点
**决策：六枚举留脚本本地常量（`lens_metric_emit.py:9` `VERDICTS` 本地常量先例），不进 fenced 契约块。** 依据：输入独有、不跨模块共享、脚本不写进共享锚。〔Q-C 撤销 `stale-dirty-tree` 后回 6 码；guard 锚 `:180` 6 枚举无需改（A6 消解）。〕

### D3〔TG-23〕T81 输入：模型传入命中 TG 集，脚本只做交集 `[spec-review-amendment Q-D·推翻 grill Q1]`
**决策：hr_tg_intersect 吃「模型判好的命中 TG 集」作入参，脚本只做 ∩ HR-TG 子集（从 `trigger-catalog.md` `## 七、HR-TG` `> 成员：` 行 parse，单一源不硬编码）+ 出锚。输出 `hit:[...]｜依据模型判定:[...]` / `none｜依据模型判定:[...]`（模型给的集可见）+ 扩 hr-tg 锚加 `declared=` 字段。**
- **为何推翻 grill Q1（Q1 曾选"读 proposal 声明"、否决"模型传入"）**：冷镜爆点5 证明"读声明"的前提是假的——TG 声明散落且格式不一（proposal 括号 / design section 锚 / 顶部 `〔TG〕` 行不统一），tg02_hit 头部扫描**捕不全**（本 change 的 TG-08 就在 design.md、proposal 用括号 → 头部扫描得空集，却实际命中 HR-TG 成员）。"读声明"只是**假装**机械化了「命中哪些 TG」。
- **正确切分**（memory 机械/判断切分线=有无确定性信号）：「命中哪些 TG」无确定性信号 → 判断归模型；「给定集 ∩ HR-TG 子集 + 出锚」确定性 → 机械归脚本（HR-TG 清单仍单一源读、不硬编码，防漂移）。
- **假阴真解**：模型负责命中完整性（本该如此），脚本不冒充；`依据模型判定` 使模型给的集可见供复审。

### D4〔TG-23〕T82 机械天花板 = 去危险信任边界（保留·靠自身 merit）`[spec-review-amendment]`
**决策：脚本只断言「`## Review 处置` 小节存在+非空」→ `section-missing|section-empty|section-ok-DISPOSITION-UNCHECKED`；逐条已处置归模型，SKILL 接入步显式划界。保留 T82。**
- **保留理由（自身 merit，非试点）**：把防真空守卫（`SKILL.md:346` 小节缺失=不通过）从 prose **机械化成不可跳**（adr/0006：弱模型跑 prose 静默跳步）+ 防子串陷阱。〔**删原 justification「维持 3 票 frontier（试点目的）」——proposal 称试点不影响设计，此为自指矛盾，冷镜洞察4 揭穿。〕**
- **诚实边界**：输出码点明 `-DISPOSITION-UNCHECKED`（防 `present` 被误读为已核=假绿，mlh F1 同型）；**MUST NOT naive-grep `未处置`**，测试含收尾句负例（fence 感知）；Success Metric 对 T82 打星降级（存在+非空机械化，逐条判定=模型信任边界，A7）。

### D5 三者共性契约（承 4.C 形态，全纯 stdlib）`[spec-review-amendment]`
`EmitError`+`EXIT_OK/EXIT_FAIL=0,1` all-or-nothing fail-closed；门控外置（不读 config）；跨模块口径重实现不 import；`argparse main(argv=None)`；单一源缺失/不可读 → 非零退出+stderr。**三者均纯 stdlib、无 subprocess**（Q-C 撤销 T80 git 例外后，D5「唯 T80 git 例外」删除）。

## Risks / Trade-offs（双收敛后）

- **[T80 codex#N 外部格式变]** → best-effort parse 失败 fail-closed `section-not-found`（adr/0002:21）。
- **[T80 fs-mtime 跨 git 操作]** → checkout 重置 mtime 使产物≈源同时；活跃编辑场景 fs-mtime 有意义、fail-safe 朝 stale（重跑只成本），可接受。
- **[T81 模型给的集不完整]** → 完整性归模型（本该如此）；`依据模型判定` 可见供复审；HR-TG 清单单一源不硬编码防漂移。
- **[T82 假绿-薄]** → 输出码点明 UNCHECKED + SKILL 划界 + 子串陷阱负例（取真实 in-repo task-log 两实例，A13）。
- **[bundle 回灌遗忘]** → Migration 段固化。

## 失败模式表〔TG-08〕

| 校验器 | 坏输入/失败 | 行为 | 可观测 |
|---|---|---|---|
| 三者共性 | 单一源/输入文件缺失或不可读 | `EXIT_FAIL`、不产部分输出 | `[<tool>] FAIL: <原因>` |
| T80 | `step1-broad-review` 锚缺失/mode 非枚举 | `EXIT_FAIL` | 锚解析失败 |
| T80 | codex 段不可 parse | `section-not-found`（非崩溃） | 正常输出码 |
| T80 | 产物 fs-mtime 早于源文件最大 mtime | `stale`（fail-safe 重跑，排除评审产物自身） | 正常输出码 |
| T81 | 模型给的命中集为空 | `none｜依据模型判定:[]` | — |
| T81 | `## 七、HR-TG`/`> 成员：` 缺失 | `EXIT_FAIL`（单一源损坏不静默空交集） | HR-TG 单一源缺失 |
| T82 | 小节缺失/仅脚手架 | `section-missing`/`section-empty`（非真空通过） | — |

## 组件 / 数据流图〔TG-11〕

```
单一源（各自，不硬编码）                    校验器（sdflow-init/assets/workflow/tools/，全纯 stdlib）      消费方 SKILL
gstack-review.md + 源文件 fs-mtime ───────►  outside_voice_guard.py ──► reason_code(6枚举) ────────────►  sdflow-spec-review
模型判定的命中 TG 集（入参）─┐  纯 stdlib
trigger-catalog 七.HR-TG 成员 ─┼──────────►  hr_tg_intersect.py ─────► hit/none｜依据模型判定:[...]+锚 ──►  sdflow-spec-review / sdflow-code-review
roadmap task-log ## Review 处置 ──────────►  review_disposition_check.py ► section-*｜...-DISPOSITION-UNCHECKED ►  sdflow-roadmap
  权威源改动 ──sdflow-init update──► openspec/workflow/tools/(下游副本)；消费方经 $RULES_ROOT/tools/<名>.py 调用
  三校验器互不 import、依赖图稀疏（3 宽独立票）；T80/T81/T82 均纯 stdlib
```

## Migration Plan（bundle 回灌纪律）

1. 三校验器+测试写权威源 `sdflow-init/assets/workflow/tools/(tests/)`。
2. 改三处 SKILL.md 手做步 → 调 `$RULES_ROOT/tools/<名>.py`（T81 由 SKILL 传模型判定的 TG 集 + `$RULES_ROOT/trigger-catalog.md`；T82 接入步写「逐条处置是你的活」）。
3. dev checkout 跑 `bash setup.sh` 同步 canonical。
4. `sdflow-init update` 推下游副本（下游不含 tests/，一致核对仅脚本本体）。
5. 回滚：删三 tool + 还原三 SKILL.md 手做步；无数据迁移、无消费方破坏。

## Open Questions

- 三校验器精确文件名为建议名，实现期可微调。
- ~13 条实现落地修（A1-A13，spec-review-report 决策区）带进 tickets 实现期；其中 A2/A4/A6 因 Q-C 撤销 git 已消解。

## Compliance

- **adr/0006(b)**「凡机械 prose MUST 脚本化」：三处手做→脚本；T82 机械化防真空守卫（不可跳）。
- **adr/0018（Proposed）**「机械校验器输出诚实」：不可验输入信号里可见（T81 依据模型判定 / T82 UNCHECKED / T80 fail-safe）；引 adr/0008+0016 家族。**状态 Proposed**——待首形态 ship+dogfood 验证再升 Accepted（spec-review 洞察5）。
- **机械/判断切分**：脚本只出信号；命中哪些 TG（T81）、逐条处置（T82）、取新鲜度事实归模型/环境。
- **单一源**：HR-TG 从 trigger-catalog 读、T80 枚举本地常量（`lens_metric_emit.py:9` 先例）、T82 状态枚举锚 SKILL.md（**T82 校验器不读，仅 design 引作语义来源，A11 订正 Compliance 措辞**）。
- **bundle 回灌**：改 assets/workflow 须 sdflow-init update + dev setup.sh，无沉默例外。
- **纯 stdlib / 门控外置 / fail-closed**：三者均无第三方依赖、无 subprocess（Q-C 后）、不读 config、坏输入非零退出。
