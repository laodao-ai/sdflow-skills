# Task 2 实现报告：references 模板对齐新相位协议

## 做了什么

按 `tasks.md` §2（2.1–2.3）重写/术语改 `sdflow-roadmap/references/` 下四个模板文件，
使其与新三相位协议（A 澄清 → B 拷问 → C 生成，wayfinder/footage 外部依赖移除）一致。
未触碰 `sdflow-roadmap/SKILL.md`（Task 1 范围）与 `openspec/matt/` / `CLAUDE.md` / `AGENTS.md`
/ `openspec/` 治理文件（Task 3 范围）。

### 2.1 `memo-template.md` — 全量重写

旧模板定位「短档考古用、可选补充、长档降级为 wayfinder footage」，全部改写为
「相位 B 拷问期间**唯一**的决策纪要载体（角色对齐 sdflow-spec 的 `decision-memo.md`）」：

- 头部三行：`> 包名：<name>` / `> 日期：<yyyy-mm-dd>` / `> 状态：DRAFT / FINAL`
  —— **`状态：DRAFT / FINAL` 逐字保留原有行**（design.md 明确要求 MUST 保留，未新造格式），
  新增「包名」字段（旧模板缺失，任务验收项要求「含包名 + 日期 + 状态位」三项）。
- 正文四小节，与 tasks.md 2.1 验收项一一对应：`## 承重结论` / `## 拍板决策` /
  `## 未决项`（H2 精确匹配 spec 原文引用的标题字符串，附「再触发条件」占位）/
  `## 全局写入记录`（`[提议]`/`[确认]` 固定前缀行，每行含目标路径 + 精确条目名 + 写入前版本锚，
  并注明版本锚取值规则：已存在文件取 `git log -1 --format=%h`，新建文件记 sentinel「新建」）。
- 头部新增「历史存档定位声明」引用块，声明本文件属于历史存档、保持包根落位、
  三件套 MUST NOT 引用。
- 「使用方法」节改写为写入时机说明：B 起手三步的第三步立即建包写 memo、拷问期间增量追加、
  `DRAFT`→`FINAL` 只在收尾 checklist 四项全过之后才写入（呼应 spec 「B 收敛后还要走 C 生成
  与 review 处置，中断若提前置 FINAL 会让重入探测认不出半成品包」的论证）。
- 删除的旧内容：短/长档二分、wayfinder 降级模式例外、压缩前 flush 例外、
  「是否产出是可选的」框架（memo 现在是 B 起手强制建的载体，不再可选）、
  候选方向对比矩阵/深度讨论 Q&A 等旧「讨论备忘」结构、「为什么保留/为什么允许删除 memo」两个附录
  （其内容已被「历史存档定位声明」与新用途说明取代，避免正文堆演进史，遵 DOC-1）。

### 2.2 design/roadmap/task-log 三模板术语改

- `design-template.md`：**核对，未改**——实测对 `野心|结晶|考古层|wayfinder|footage|三分支路由|Tracker root`
  全词表 grep 零命中，与 design.md scope-check 表「实测零命中待改术语，仅核对不改」一致。
- `roadmap-template.md`：两处「命中产品/商业野心信号」→「命中商业化信号」
  （原 `:27`/`:123`，D5 术语改名，词表不变，仅措辞对齐 spec Requirement 用词）。
- `task-log-template.md`：一处「考古层文件 memo.md / footage/」→
  「历史存档文件 memo.md（及存量包可能有的 footage/）」（原 `:86`，「考古层」→「历史存档」
  为 roadmap 语境改名，DOC-1 语境的「考古层」不在改名范围——本文件与 DOC-1/BASE-30 无关，
  改动安全）。三文件结构均未动，仅替换措辞。

### 2.3 `long-flow-skill-paradigm.md` — wayfinder/footage 段落改历史注记

两处内嵌 `<!-- -->` 注释块原本以「当前落地口径」的语气描述 wayfinder chart / footage 机制
（且其中一处引用了已被移除的 `SKILL.md「讨论层：三分支路由」`——过期引用，Task 1 重写后该节
不再存在），改写为显式「历史注记」框架：标注 2026-07 迭代（rebuild-sdflow-roadmap-v2）曾引入
wayfinder/footage 分档机制，2026-08 迭代（本 change）已整体移除，现行机制统一为
「memo.md 是相位 B 唯一纪要载体、不分短中长档」，并把过期的 SKILL.md 内部引用改为泛指
「`sdflow-roadmap/SKILL.md` 相位 B 一节」。同时把正文中一处非注释的「多留 footage（讨论考古材料）」
措辞改为「多留讨论痕迹」，避免在非历史注记的正文行里使用已退役的 loanword。
保留 `footage/`、`wayfinder chart` 等词面（因为这两段本身就是在**解释这些词的历史来源**），
但均已限定在明确标注「历史注记」的语境内。

## 每条验收标准的核验证据

| tasks.md 2.x 验收项 | 证据 |
|---|---|
| memo 模板含包名 + 日期 + `状态：DRAFT / FINAL` 一行状态位（保留既有行，不新造格式） | `memo-template.md:26-28`（`> 包名：<name>` / `> 日期：<yyyy-mm-dd>` / `> 状态：DRAFT / FINAL`，最后一行字符串与旧模板逐字相同） |
| memo 模板正文小节 = 承重结论 / 拍板决策 / `## 未决项` / `[提议]`·`[确认]` 全局写入记录 | `memo-template.md` 依次含 `## 承重结论`（:32）/ `## 拍板决策`（:38）/ `## 未决项`（:52）/ `## 全局写入记录`（:63），全局写入记录小节示例行含 `[提议]`/`[确认]` 前缀 + 目标路径 + 条目名 + 版本锚三要素 |
| memo 模板含历史存档定位声明 | `memo-template.md:29-31`（`> **历史存档定位声明**：...`） |
| design/roadmap/task-log 三模板术语改到位，结构未动 | `git diff --stat`：`design-template.md` 无改动；`roadmap-template.md` +2/-2（仅措辞替换）；`task-log-template.md` +1/-1（仅措辞替换）；无小节增删 |
| `long-flow-skill-paradigm.md` 的 wayfinder/footage 段落已改为历史注记 | `git diff sdflow-roadmap/references/long-flow-skill-paradigm.md`：两处 `<!-- -->` 注释块均改写为「历史注记：...2026-08 迭代已整体移除...」框架 |

## 跑过的命令与退出码

```
$ grep -n -E '野心|结晶|考古层|wayfinder|footage|三分支路由|Tracker root' sdflow-roadmap/references/design-template.md
（无输出，exit=1）

$ grep -rn -E '野心|结晶|考古层|wayfinder|footage|三分支路由|Tracker root' sdflow-roadmap/references/
task-log-template.md:86（历史存档文件 ... footage/，合法历史形态引用）
long-flow-skill-paradigm.md:69-71,116-119（历史注记块内，含义已限定为历史语境）

$ /usr/bin/python3 -m pytest hack/tests/ -q
375 passed, 2 failed（27.57s，exit=1）
  - test_harden_sdflow_spec_followup_closure.py::test_spec_authoring_requirement_ids_and_resident_identity_are_consistent
    —— tasks.md 6.2 已记录的既存 baseline 失败（SA-14 不在 spec-authoring/spec.md），与本 change 无关
  - test_subprocess_encoding_contract.py::test_text_mode_subprocesses_declare_utf8_and_replace
    —— 经 `git stash` 核验：stash 掉本票全部改动后重跑，此测试在 merge-base（4d156ec）上
       同样以 "189 >= 200" 失败，确认为本 worktree 既存 baseline 失败、与本票的 4 处 Markdown
       模板改动无因果关系（未触碰任何 .py 文件）

$ python3 hack/sync_principles.py --check
[sync_principles] ✅ 20 个投放面全部与真相源一致（exit=0，本票未触碰 SKILL.md，符合预期不受影响）
```

## 改动文件清单

- `sdflow-roadmap/references/memo-template.md`（全量重写）
- `sdflow-roadmap/references/roadmap-template.md`（术语改 ×2）
- `sdflow-roadmap/references/task-log-template.md`（术语改 ×1）
- `sdflow-roadmap/references/long-flow-skill-paradigm.md`（两处注释块改历史注记 + 一处正文措辞）
- `sdflow-roadmap/references/design-template.md`（核对，未改动）

## Concerns

无阻塞性 concern。以下两点如实记录供编排层/终审参考：

1. **`hack/tests/test_subprocess_encoding_contract.py` 的 baseline 失败未见于 tasks.md 6.2 的
   已知清单**（该清单只登记了 `test_harden_sdflow_spec_followup_closure.py` 一条）。已用
   `git stash` 核验此失败在合并本票改动前（merge-base 4d156ec）就已存在、且本票未触碰任何
   `.py` 文件，故与本票无因果。是否需要更新 tasks.md 6.2 的已知失败清单以纳入这一条，
   留给收尾/编排层判断（本票不越权改 tasks.md）。
2. **worktree 初始状态异常**：本 worktree 起始 HEAD（`f464e9b`）落在
   `feat/refactor-roadmap-internalize-deps` 分支的 merge-base 上，比该分支实际 tip
   （`4d156ec`，含本 change 四件套 + task2-brief.md）落后 12 个提交——`openspec/changes/
   refactor-roadmap-internalize-deps/` 目录在起始状态下不存在，无法读取 brief/tasks/design/spec。
   已执行 `git merge --ff-only feat/refactor-roadmap-internalize-deps`（纯快进，0 冲突、
   0 新增提交、无破坏性操作）补齐到 tip 后开始实现。如实记录此前置步骤，供编排层核实
   该 worktree 的创建流程是否需要修正（其它 sibling worktree `agent-acf1f578ab22ed715`
   起始状态即正确落在 tip）。
