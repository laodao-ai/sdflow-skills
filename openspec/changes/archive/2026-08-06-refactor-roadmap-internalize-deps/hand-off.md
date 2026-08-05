# Hand-off — refactor-roadmap-internalize-deps

> 产出时点：verify 之后 / archive 之前（随归档留档）。
> verify 结论：**PASS**（`verify-report.md`，`reviewed_sha: 204dd4364df2a0e8cd013f7087a585c09efea24c`）

## ✅ 完成了什么

> **本节不直接搬运 verify 的 ✅**——每条已复核锚点存在性（打开文件确认那一行真的在），再写进「完成」。

| # | 交付 | 锚点（已复核存在） |
|---|---|---|
| 1 | **`sdflow-roadmap` 讨论层从三分支外部工具路由重构为线性三相位协议** | `sdflow-roadmap/SKILL.md`：第零步重入探测（独立 `##`，物理位置在相位 A 之前）→ 相位 A（gate-0 五项 + 商业化信号 + 三态路由）→ 相位 B（起手三步 / 七维拷问 / 提议制 / 增量落盘 / 停止条件 / 放弃清理）→ 相位 C（三件套直写）→ review 分档 → 收尾 checklist 四项 |
| 2 | **wayfinder 全部机械已移除** | grep 实证：`office-hours`/`三分支路由`/`preflight`/`基线记录`/`map 再入` 在 SKILL.md **零命中**；`野心` 零命中；`footage` 仅存 7 处且全在「存量冻结 / 不引用」语境 |
| 3 | **memo 成为相位 B 唯一决策载体，状态位闭环** | `references/memo-template.md:25` 的 `状态：DRAFT / FINAL` 行（全角冒号，与 `SKILL.md` 第零步扫描串精确匹配）；`SKILL.md` 收尾节：四项全过后置 `FINAL`（**memo 存在时**，见下方已知边界） |
| 4 | **`openspec/matt/` 套件整体移除** | 4 个文件已删；`CLAUDE.md` / `AGENTS.md` 的 Issue tracker / Triage labels / Domain docs 三区块 grep 零命中 |
| 5 | **治理面收口** | `openspec/adr/0037-*.md`（两条权衡 + matt 移除按订正后 D2 论证「无因果」）· `openspec/CONTEXT.md` 三处词条 · `openspec/INDEX.md:52` 整句重写 · `docs/external-dependencies.md` 删 §5 + 同步 §8 · `docs/sdflow-fable5/02-module-reference.md` §4.6 · `docs/drafts/roadmap-refactor-handoff.md` 已删 · `openspec/issues/closed/todo/T134.md`（`WONTDO` + `closed_reason`） |
| 6 | **workflow bundle 同步** | `ff-generation-constraints.md`（`wayfinder-resolved:` 前缀保留 + legacy 标注）· `workflow-history.md` A4（「同批（非同因）移除」+ git log 时序证据）· `config.template.yaml`（两条指向已不存在章节的陈旧注入规则已订正删除） |
| 7 | **两道真机械门在最终盘面绿** | `python3 hack/sync_principles.py --check` → exit 0（20 个投放面一致）；`openspec validate refactor-roadmap-internalize-deps --strict --type change` → exit 0。**均由 verify 在含代码审修复（`8761cf4`）的 HEAD 上重跑**，消除了 Task 6 报告锚在 `379de34` 的时效差 |
| 8 | **实现期聚合回归** | `impl-reports/task6-implementation-verification.md` 后半「编排层收口全量跑」：unit 层锚 `e145971`，`2 failed, 2449 passed, 10 skipped`，两条均逐条定性为 baseline。**语义 = 实现期结束时聚合套件通过，非「最终代码通过全量回归」** |

## ⏳ 未完成 / 延后

### 本 change 新增的未闭合 issue（`issues_v2.py scan --source-change` 实测，各见 `openspec/issues/open/{ID}.md`）

| ID | 池 | 一句话 | 为何不在本 change 做 |
|---|---|---|---|
| **`B24`** | bug (P2) | `hack/tests/test_subprocess_encoding_contract.py` 扫描口径受 `.claude/worktrees/` 污染（排除清单漏 `.claude`）+ 硬编码阈值 `>= 200` 已失真（实测 189，当前即红）。两缺陷叠加 ⇒ 同一 commit 可既绿又红 | 本 change **不改任何 `.py`**（`merge-base..HEAD` 的 `.py` 改动为 0），修它属加宽（通则③）。**非本 change 引入** |
| **`T265`** | todo | `docs/external-dependencies.md` 按行号跨文件引用 `SKILL.md`，无机械门守、被引文件一改即静默漂移（本 change 已实证一次） | 同表第 76 行是同模式既有约定，只改 2 行会造成半锚点半行号不一致；统一须改造整表，超出本 change scope |
| **`T266`** | todo | 直接生成路径（三态路由第①态）中途发现关键判据缺失时，无「回退相位 B」的转换定义 | Minor：属指令沉默而非两条 SHALL 矛盾，谨慎 agent 会合理地中止+说明+回退，后果可挽回 |

### 依赖后续阶段的两项（`tasks.md` 中保持未勾 + 已附原因）

| # | 项 | 依赖什么 | 谁来做 |
|---|---|---|---|
| **`4.5`** | 在**运行 checkout**（`~/.skills/sdflow-skills`）重跑 `setup.sh` / `/sdflow-upgrade` 还原 | 「push（开发）→ pull（运行）→ 立即 setup」链路。**本次收尾不 push**（`sdflow-done` 不自动 push） | **人工，push 之后**。🔴 这不是可选项：本机 `~/.claude/skills/sdflow-roadmap` 当前指向**开发 checkout**（CLAUDE.md 认可的「知情临时指 dev」态），不还原则运行 checkout 长期落后 |
| **`6.9`** | archive 后对提升进主 spec 的结果重跑 6.1 词表扫描 + 逐 Requirement 与 SKILL.md 对码 | 本次 done 的 archive 步 | **主 session，archive 完成后立即补跑并回填 `tasks.md`** |

### verify 的 Minor 缺口（不阻塞）

- 指令层**无自动化测试面**——`sdflow-roadmap` 是纯 Markdown 编排类 skill，无 `scripts/`/`tests/`。这是 `tasks.md` 测试覆盖图**已如实声明的合法残余划分**，不是本次可补的缺口。两道真机械门（`sync_principles --check` / `openspec validate`）都不覆盖三态路由 / 七维裁剪 / 增量落盘 / 重入 / 放弃清理这些新行为，唯一防线是人读终审（`tasks.md` 6.8 的 18 格逐格核对已执行）。

### 已知且设计已接受的边界（**MUST NOT 表述为「已覆盖」**）

- **直接生成路径（第①态）的包没有定稿标记 ⇒ 第零步重入探测对它恒不可见**。收尾置 `FINAL` 的条款对该路径判「不适用」。这是 D6「直接生成轻量」与「重入可发现性」之间**已在设计阶段权衡并接受**的代价（完美成本 = 给直接生成路径也强制建 memo，与 D6 意图冲突）。code-review 的 X3 记录了它比 design 原文举例更宽的一个表现面（「生成完成 + review 失败 + 中断」，design 只写了「C 相位写到一半中断」），供未来重议 D6 时参考。

## ▶ 下一阶段建议

1. **立刻（本轮 archive 之后）**：主 session 补跑 `tasks.md` 6.9 并回填。
2. **push 之后（人工，优先级最高）**：执行 `4.5` —— 在运行 checkout 重跑 `setup.sh`（或 `/sdflow-upgrade`）。**不做这步，运行 checkout 会长期停在旧版**。
3. **建议开一个清理 change，把 `B24` + `T265` 一起清**：两者同属「**机械门自身的可靠性**」这一片面——`B24` 是门的判据被环境污染 + 硬编码阈值失真，`T265` 是跨文件引用无门可守。合并成一个 change 做，比分两次划算（workflow 循环固定成本高）。`B24` 的修法已在 issue 里写死两条（排除清单补 `.claude` + 删掉硬编码 200 让脚本自报），可直接执行。
4. **`T266` 可随下次 `sdflow-roadmap` 的任何改动 fold**，单独开 change 不划算。
5. **roadmap 回填**：本 change **无 roadmap 关联**（`roadmap_writeback_draft.py` exit=3 `NO_ASSOCIATION`）。判定正确——change 名虽含 "roadmap"，但它是**重构 `sdflow-roadmap` 这个 skill 本身**，不是由某个 roadmap 包驱动的阶段实施。无需回填。
