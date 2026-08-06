# hand-off — absorb-gstack-review

> 产出于 verify（PASS）之后、archive 之前。随归档留档，作**异步人类再入口 + 下个 change 种子**。
> 日期：2026-08-06 · 收尾走 `/sdflow-ship` 全自动链（出票 → 6 票实现 → 代码审 → done）。

## ✅ 完成了什么

每条均已**独立复核锚点存在性**（不直接搬运 verify 的 ✅）：

| 交付 | 锚点（已亲验） |
|---|---|
| **Step1 从第三方 gstack `/review` 原生执行改为自持 scope 审计** | `sdflow-code-review/SKILL.md` 第一步全段；`grep -rn "gstack" sdflow-code-review/SKILL.md` **exit 1 零输出**（Success Metric 严格归零，无「历史注记」豁免） |
| 意图源改锚四件套 + 完成度五态（判定纪律逐条钉死） | `SKILL.md` Step1「审计两轴」段；**本轮 dogfood 实跑产出 23 条五态表**，其中 6.4 如实判 `UNVERIFIABLE` 而非静默判 DONE |
| 锚 mode 新枚举 `subagent\|main-session` | `code-review-report.md` 实落 `<!-- sdflow:step1-broad-review v1 mode="subagent" -->` |
| **mirrors 合法集 / dead-fanout 计数集真拆分** | `anchor_lint.py:674` `_FANOUT_MIRRORS`（不含 broad，计数域）+ `:676` `_MIRRORS_LEGAL = _FANOUT_MIRRORS \| {"broad"}`（合法集）；双轴审各自做过**定点变异**验证非恒真 |
| lens-metric fold raw 名替换 | `lens-metric-contract.md:66` `scope-audit: broad`；本轮 emitter 以该 raw 名输入、exit 0 归约出 `lens="broad"` 锚行 |
| checklist 吸收五类缺口 | `code-review-base.md` CR-10/CR-11；`domains/backend.md` CR-BE-03 + CR-BE-02 扩点；新建 `domains/llm.md`（CR-LLM-01/02） |
| TG-27 + HR-TG 成员 | `trigger-catalog.md:47` TG-27 行（含排除句 + code-review-only 注）+ `:131` HR-TG 成员；`test_reads_real_catalog_members` 断言真实 catalog 解出 9 成员 |
| pre-emit 引文纪律 + Suppressions 扩两条 | `SKILL.md` Step2 prompt 模板 + Step3 置信过滤 |
| 实现期聚合覆盖（tickets 轨） | `impl-reports/task6-impl-verification.md:29` 三层 schema 齐全，unit 层 `\|/usr/bin/python3 -m pytest -q -rs\|0\|458d44d…`；integration/e2e 记「未覆盖（本仓无此分层）」+ 判定依据。**锚语义 = 「实现期结束时聚合套件通过」，不是「最终代码通过全量回归」** |
| 全仓回归 | `2466 passed, 10 skipped`（verify 独立重跑复现；10 skip 经溯源确认早于本分支、非本 change 新增） |

### 本 change 自身即首次 dogfood（tasks 6.4）

Task 6 收尾票只做开窗前置并**显式声明**实跑观测不由本票执行（子代理不能派子代理）。
该观测由紧随的 code-review 步兑现，三项待核锚全部落定：`mode="subagent"` 锚 ✅ ·
`scope-audit` 折叠出的 `lens="broad"` 行 ✅ · `anchor_lint` **CLEAN** ✅。

**新加的 TG-27 排除句首验有效**：本 change 改的 `anchor_lint.py` / `lens_metric_emit.py` 正是
「评审工作流自身读自报控制面锚」，被排除句正确判为**不命中** TG-27——这正是该句设计要防的自指假阳。

## ⏳ 未完成 / 延后

### 本 change defer 的 issues（4 条，均 OPEN，各见 `openspec/issues/open/todo/{ID}.md`）

| ID | 摘要 | 来源 |
|---|---|---|
| **T267** | 建 `python.md` checklist domain 承接 Async/Sync 混用等 Python 专属检查点 | proposal Non-Goals 显式 defer（归属 domain 不存在） |
| **T268** | 处置 `sdflow-spec-review` 侧 autoplan 姊妹依赖 + `outside_voice_guard.py` | proposal Non-Goals 显式 defer——**本 change 只吸收 code-review 一侧，spec-review 侧仍留第三方运行时依赖** |
| **T269** | 清理仓根 `openspec/workflow/` 孤儿副本（`lens-metric-contract.md` / `WORKFLOW-GUIDE.md`） | 存量债，非本 change 引入；本轮三个独立镜各自撞到它并各自核实「非 pin、不遮蔽权威源」 |
| **T270** | skew 探测信号②的 grep 写法须**行首锚定** | **本轮 dogfood 现场发现**：无锚定的 `sed` 会撞上散文里对 fence 名的提及而假阴 ⇒ 误停整轮评审。方向 fail-safe（假阴致停非放行），但会误停 |

### 代码审已裁掉、但值得知道的

- **hr-tg voice 判 high 的一条被裁**：它断言本仓 `openspec/workflow/` pin 陈旧会硬停评审——
  前提被证伪（pin 三判据实测全不存在，resolver 实判 `source=global-canonical`）。
  但**消费仓**在 `sdflow-init update` 之前确实会命中硬停——那是 skew 探测的**设计意图**（fail-loud +
  带修法指引），不是 bug。**发布后若有人报「评审起手就硬停」，先让他跑 `sdflow-init update`。**
- 五态判据未区分「未做」与「天然不产生 diff 痕迹的验证动作」（置信 55，被 <80 滤除）。
  本轮实证未踩坑（Step1 把 6.4 判成 UNVERIFIABLE），但**判据本身确实没写这条区分**，
  未来若出现误判 PARTIAL/NOT DONE，根因在此。

### verify 的 Minor 缺口（均可接受）

1. 仓根孤儿副本含旧 `gstack-adv` → 即 T269，已 defer，无功能影响。
2. `docs/skill-authoring-best-practices.md` 仍以 gstack review 作**设计案例**引用 → 非运行时依赖描述，与本 change 目标不冲突。

### ≥2 方案的延后决策

**无**。本轮代码审未触发 `T10-choice`（4 条采纳的 finding 均有客观判据、直接自动修，无方案分歧）。

## ▶ 下一阶段建议

1. **优先级最高：T268（spec-review 侧姊妹依赖）**。本 change 只砍了代码审一侧的第三方依赖，
   设计审侧的 autoplan 依赖仍在——**依赖移除只做了一半**。建议比照本 change 的路子开一个
   `absorb-gstack-autoplan`（或明确判定「spec-review 侧保留第三方依赖」并写进 ADR，别悬着）。
   顺带可一并处置 `outside_voice_guard.py` 的 `VALID_MODES = ("native","simulated")`——
   它现在只服务 spec-review 侧的 `gstack-review.md`，与本 change 换的新枚举不相交（对抗镜 A 已核实），
   但两套 mode 枚举并存是认知负担。
2. **T270 与 T269 可一起清**（都是 workflow bundle 的小面）：T270 把四条 skew 信号写成字面命令
   （行首锚定）、T269 删孤儿副本。两者合起来是一个小 change，**别各开一个**。
3. **T267（python.md domain）单独排期**——它不是本条线的收尾，是新建一个 domain 清单，
   scope 与上面两条不同，混在一起会违反「一个 change = 一个完整阶段结果」。
4. **发布纪律提醒**（本 change 特有）：本 change 改了 `sdflow-init/assets/workflow/` 下的
   contract + tools，且 SKILL 里新加了会对它们 fail-loud 的 skew 探测 ⇒
   **消费仓必须跑 `sdflow-init update`**，否则下一轮评审起手即硬停（带修法指引，非静默）。

## ⚠️ 收尾环境状态（须人工还原）

本 change 的 dogfood 前置在**开发 checkout 跑了 `bash setup.sh`**，当前
`~/.sdflow/workflow`、`~/.claude/skills/*`、`~/.codex/skills/*` **全部指向本开发树**
（`/Users/cheneyzhao/Documents/04-sdflow-skills`）。

**这是时间盒操作，窗口期本机所有项目仓都吃开发版。**
**还原方式**：在运行 checkout `~/.skills/sdflow-skills` 跑一次 `bash setup.sh`
（`hack/` 是拷贝不是软链，只改软链还原不了）。
若打算立即发布本 change，正确顺序是：push → 运行 checkout `git pull` → **立即** `bash setup.sh`
（pull 与 setup 之间是「新 SKILL 调旧脚本」的窗口期）。
