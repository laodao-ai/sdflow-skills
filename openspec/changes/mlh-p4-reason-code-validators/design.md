## Context

MLH 阶段 4·4.D：三处评审 / 规划步各有一段模型手做的机械判定，按 adr/0006「凡机械 prose 协议 MUST 脚本化」下沉为三个同型 reason_code 确定性校验器。同族 4.C `lens_metric_emit.py`（merge `bd7c05f`）已立形态样板。三者逻辑独立、依赖图稀疏，本 change 亦选作首个 tickets 实现管线试点。

**接地事实（已核验，带锚）：**

- **形态样板** `openspec/workflow/tools/lens_metric_emit.py`：stdlib-only（`argparse/json/re/sys/pathlib`），`EmitError` + `EXIT_OK/EXIT_FAIL=0,1`，all-or-nothing fail-closed（任一坏输入 raise→`main` 捕获 `return EXIT_FAIL` 且**不产部分输出**，`:190-194`）；单一源契约用 fenced 机读块读；跨模块口径**重实现不 import**（`_read_block_pairs` 重实现 anchor_lint 口径，`:19-43`）；本地常量豁免先例 `VERDICTS`（`:9`，ADR-11：输入独有、不写进锚、不与他模块共享）。
- **T80** outside-voice 复用守卫：**spec-review 专属**（code-review 恒重跑 code-voice，无对称守卫，`sdflow-code-review/SKILL.md:88`）。现状手做步 `sdflow-spec-review/SKILL.md:39-44`「三前置·R2」：①来源（读 `gstack-review.md` 的 `step1-broad-review` 锚 `mode`，`simulated`→无效）②新鲜度（产物 mtime < `git log -1 --format=%ct -- {change_dir}`→陈旧）③结构（文件缺失 / 解析不出 codex 段 / findings=0）。reason_code 六枚举 `none|file-missing|section-not-found|zero-findings|stale|simulated-source` 现仅存于 SKILL.md 锚注释 prose（`:179`，code-review 侧 `:169` 同款 guard 字段）。codex 段格式（`codex#N` 标签）**gstack 外部所有**，adr/0002:21 明定其改名「只触发降级回落、不静默失效」。
- **T81** HR-TG 交集：HR-TG 子集单一源 `trigger-catalog.md:127-131`「## 七、HR-TG 子集」→ `> 成员：**TG-04, TG-06, TG-07, TG-08, TG-09, TG-16, TG-17, TG-26**`（8 个，blockquote prose）。匹配先例 `sdflow-ship/scripts/ship_gate.py:tg02_hit`（`:495-519`）三道防线：①fence-aware ②只扫头部声明区（首个 `## ` 前）③只认 strip 后 `startswith("〔TG")` 声明行（排除描述性提及 / 反引号 / 否定句）。proposal 头部 `〔TG-NN：…〕` 声明约定已证（`gate-anchor-line-scoped/proposal.md:3` 甚至已声明「HR-TG 子集命中 = none」）。`openspec/workflow/` 下**无** trigger-catalog 副本，须从 `$RULES_ROOT/trigger-catalog.md` 读。
- **T82** roadmap Review 对账：小节标题精确 `## Review 处置`（模版 `sdflow-roadmap/references/task-log-template.md:62`）；状态枚举单一源 `sdflow-roadmap/SKILL.md:312-316`（✅采纳/❌拒绝/⏭延后 + 前序放弃视为已处置）。**格式三实例不统一**：模版=bullet、mlh 实例=表格单元格、wco 实例=分组加粗组头；task-log **无任何 `sdflow:` 机读锚**；实例收尾句「本小节**无**『未处置』状态条目」**含子串「未处置」**（裸子串检测假阳，同 memory `gate-substring-detection-dogfood` 坑）。

## Goals / Non-Goals

**Goals：**
- 三处机械判定下沉为三个 stdlib-only、fail-closed、门控外置（不读 config）的确定性校验器，出 reason_code 退出码。
- 各校验器口径锚定各自单一源（HR-TG 清单不硬编码、matching 复用 tg02_hit 声明式口径），改单一源即生效。
- 三处 SKILL.md 手做 prose → 「调校验器」，判断 / 编排语义保留给模型。
- 每校验器配 pytest（正例 + 坏输入 fail-closed 非零退出）。

**Non-Goals：**
- 不替代模型 / 人的判断（采纳 / 处置 / 复用与否的裁决）。
- **T82 不断言「逐条已处置」**（见 D4，机械不可达，显式信任边界）。
- 不做 4.D.3（待 embedded 契约）/ 4.A；不引第三方依赖；不改 setup.sh。
- 试点执行机制（config 翻键 / PIPELINE_RECEIPT / 档位钉死）不入本设计。

## Decisions

### D1〔TG-23〕T80 输入契约 + stdlib 纯度（是否自跑 git）
**决策：校验器吃「已备齐的原始事实」，不自跑 subprocess。** 入参 = `gstack-review.md` 路径 + `change_mtime`（`{change_dir}` 最新改动 epoch 秒，由 SKILL 侧 `git log -1 --format=%ct -- {change_dir}` 算好传入）。脚本只做：parse `step1-broad-review` 锚 `mode`、比对产物 mtime 与 `change_mtime`、best-effort parse codex 段 → 归约出**单一** reason_code。
- **备选 A（否决）**：脚本自跑 `git log`。→ 破 stdlib-only 纯度（首个引 subprocess 的同族校验器）、不可纯函数测试、环境耦合。
- **备选 B（采纳）**：mtime 由 SKILL 算好传参。「取 git 事实」是环境动作归 orchestration，「三判归约」是确定性逻辑归脚本——切分对齐「机械活交脚本、模型 / 编排只做判断 / 取值」。
- **三面后果**：系统=脚本保持纯函数可测、无环境副作用；用户（判赢人）=判据逻辑可单测锁死不漂移；开发循环=SKILL 侧多一行 `git log` 传参，成本极低。**主次**：纯度 > 省一行传参。

### D2〔TG-23〕T80 reason_code 枚举落点
**决策：六枚举留脚本本地常量（`VERDICTS` 先例），不进 fenced 契约块。** 依据 ADR-11 豁免：该枚举**输入独有、不与其它模块共享、本脚本不把它写进任何跨模块共享锚**（guard 字段由 SKILL / 模型 emit 进 outside-voice 锚，非本脚本职责）。
- **备选（否决）**：新增 `outside-voice-guard-enums` fenced 契约块。→ 过度工程；无第二消费方，单一源没有跨模块漂移面。

### D3〔TG-23〕T81 输入 TG 集来源
**决策：泛化 `tg02_hit`——扫 proposal.md 头部声明区全部 `〔TG-\d\d` 声明行得命中 TG 集**，交 HR-TG 子集（从 `trigger-catalog.md` 的 `## 七、HR-TG` `> 成员：` 行 parse，单一源不硬编码）→ 输出 hit 列表 / `none` + 规范锚串。复用 tg02_hit 三防线（fence-aware + 头部区 + 声明行 startswith `〔TG`）。
- **备选 A（否决）**：模型传入 TG 列表。→ 把「命中哪些 TG」的手做重新塞回模型，漂移面未消除，违 change 目的。
- **备选 B（采纳）**：泛化 tg02_hit。已有声明约定 + 匹配先例，确定性可测。
- **假设**：proposal 头部声明区列全命中 TG（未声明的 TG 视同未命中，与 tg02_hit 今日行为一致——非本脚本兜底责任）。

### D4〔TG-23〕T82 机械天花板 = 诚实信任边界（本 change 最关键决策）
**决策：脚本只断言「`## Review 处置` 小节存在 + 非空（非仅脚手架注释）」，reason_code = `section-missing|section-empty|present`；「逐条已处置」不机械断言，显式声明为模型信任边界。**
- **为何不做「逐条已处置」**：格式三实例不统一（bullet / 表格 / 组头）+ 「未处置」无字面 token + 收尾句「无『未处置』」子串自指陷阱——任何子串 / 单行正则检测都会假阳或假绿（重蹈 mlh F1 `check_lens_metric` truthy 假过门）。**MUST NOT naive-grep `未处置`**；测试须含「收尾声明句不得触发命中」的负例（fence-aware / 结构感知，同 memory gate-substring-detection）。
- **诚实声明**：对齐 lens_metric_emit「数值一致性仍是主 session 信任边界」先例——脚本能力上限写进 SKILL 接入步与本 design，不假装覆盖。
- **设计门待裁〔留 HARD-GATE〕**：T82 机械价值薄（存在 + 非空 + 防陷阱守卫）。**保留三合一（推荐）** vs **T82 剥离另排**（缩到 2 校验器）。推荐保留：维持 3 票 frontier 观测（试点目的）+ 防子串陷阱守卫本身是真价值（memory 实证是反复踩的坑）。

### D5 三者共性契约（承 4.C 形态）
stdlib-only；`EmitError`+`EXIT_OK/EXIT_FAIL=0,1` all-or-nothing fail-closed（坏输入非零退出、不产部分输出）；门控外置（不读 config）；跨模块口径重实现不 import；`argparse main(argv=None)`；单一源缺失 / 不可读 → fail-closed 非零退出 + stderr 原因。

## Risks / Trade-offs

- **[T80 codex#N 外部格式变]** → 缓解：best-effort parse 失败 fail-closed 到 `section-not-found`（合法 reason_code，触发安全自跑回落；adr/0002:21 明定此为可接受退化）。
- **[T82 薄价值 / 假绿风险]** → 缓解：D4 诚实窄化 + 子串陷阱负例测试 + 信任边界显式声明。
- **[T81 头部声明约定假设失效]**（proposal 漏声明某命中 TG）→ 缓解：与 tg02_hit 今日同口径（未声明=未命中），非本脚本兜底；风险等同现状、不新增。
- **[bundle 回灌遗忘]** → 缓解：Migration 段固化操作序（改 assets → `sdflow-init update` → dev 跑 setup.sh）。

## 失败模式表〔TG-08〕

| 校验器 | 坏输入 / 失败 | 行为（fail-closed） | 可观测（stderr） |
|---|---|---|---|
| 三者共性 | 单一源 / 输入文件缺失或不可读 | `EXIT_FAIL`，不产部分输出 | `[<tool>] FAIL: <原因>` |
| T80 | `step1-broad-review` 锚缺失 / mode 非枚举 | `EXIT_FAIL`（区别于 `simulated-source` 正常判定） | 锚解析失败原因 |
| T80 | codex 段不可 parse | 归约为 `section-not-found`（正常 reason_code，非崩溃） | —（正常输出该码） |
| T81 | `## 七、HR-TG` 段 / `> 成员：` 行缺失 | `EXIT_FAIL`（单一源损坏不可静默空交集） | HR-TG 单一源缺失 |
| T81 | proposal 无头部声明区 | hit=`none`（与 tg02_hit 同，非错误） | — |
| T82 | 小节标题 `## Review 处置` 缺失 | reason_code=`section-missing`（非崩溃） | — |

## 组件 / 数据流图〔TG-11/组件图〕

```
单一源（各自，不硬编码）                 校验器（sdflow-init/assets/workflow/tools/）        消费方 SKILL
─────────────────────────                ──────────────────────────────────────────        ──────────────
gstack-review.md(step1锚+codex段) ┐
{change_dir} git mtime ───────────┼───►  outside_voice_guard.py ──► reason_code(6枚举) ──►  sdflow-spec-review(复用守卫步)
                                  ┘
proposal.md 头部〔TG声明 ─────────┐
trigger-catalog.md 七.HR-TG成员 ──┼───►  hr_tg_intersect.py ─────► hit列表/none+锚串 ────►  sdflow-spec-review / sdflow-code-review(HR-TG判定步)
                                  ┘
roadmap task-log ## Review 处置 ──────►  review_disposition_check.py ► present/section-* ─►  sdflow-roadmap(收尾 checklist)

  权威源改动 ──sdflow-init update──► openspec/workflow/tools/(下游副本) ；消费方经 $RULES_ROOT/tools/<名>.py 调用（resolve-workflow.sh 解析）
  三校验器互不 import、互不依赖（依赖图稀疏 → tickets frontier 天然 3 宽独立）
```

## Migration Plan（bundle 回灌纪律）

1. 三校验器 + 测试写入**权威源** `sdflow-init/assets/workflow/tools/(tests/)`（唯一真相源，CLAUDE.md）。
2. 改三处 SKILL.md（`sdflow-spec-review` / `sdflow-code-review` / `sdflow-roadmap`）手做步 → 调 `$RULES_ROOT/tools/<名>.py`。
3. dev checkout **跑一次 `bash setup.sh`**（同步 `~/.sdflow/` canonical，否则测不到）。
4. `python3 sdflow-init/scripts/... update`（或 `sdflow-init update`）推 `openspec/workflow/tools/` 下游副本。
5. **回滚**：删三 tool 文件 + 还原三 SKILL.md 手做步；无数据迁移、无消费方破坏（新增能力，旧 prose 可原样恢复）。

## Open Questions

- D4 的「T82 保留三合一 vs 剥离」留设计门 HARD-GATE 裁（推荐保留）。
- 三校验器精确文件名（`outside_voice_guard.py` / `hr_tg_intersect.py` / `review_disposition_check.py`）为建议名，spec-review 可微调。

## Compliance

- **adr/0006**「凡机械 prose 协议 MUST 脚本化」：正向落实（三处手做→脚本）。
- **「机械活交脚本、模型只做判断」**：脚本只出 reason_code / hit 列表，不做裁决 / 处置 / 复用与否的决定（D1 取 git 事实亦归 orchestration）。
- **信任边界诚实**（承 lens_metric_emit 先例）：T82 显式声明「逐条已处置」为模型信任边界、不假装机械覆盖（D4）；禁子串假绿。
- **单一源原则**：HR-TG 清单从 `trigger-catalog.md` 读、T80 枚举本地常量豁免（ADR-11 判据）、T82 状态枚举锚 `sdflow-roadmap/SKILL.md`——无第二真相源。
- **bundle 回灌纪律**（CLAUDE.md）：改 `assets/workflow/` 权威源须 `sdflow-init update` 推下游 + dev 跑 setup.sh，禁只改下游遗忘回灌——Migration 段固化，无沉默例外。
- **stdlib-only / 门控外置 / fail-closed**：承 4.C 契约（D5），无第三方依赖、不读 config、坏输入非零退出。
