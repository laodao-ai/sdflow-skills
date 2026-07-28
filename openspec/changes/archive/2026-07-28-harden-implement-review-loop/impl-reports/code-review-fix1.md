# 冷层代码审裁决修复轮 · code-review-fix1

change: `harden-implement-review-loop` · 分支 `feat/harden-implement-review-loop`
四项裁决（FIX-1 CRITICAL 多镜收敛 / FIX-2 CRITICAL 跨模型 voice / FIX-3 · FIX-4 Important 跨模型 voice）
全部落地。所有改动处标记 `[impl-review-fix ...]`。**未 commit**（按编排层两段时序处理）。

---

## FIX-1 · `plan_was_renamed()` 判据机制整体换代（CRITICAL）

### 撤除的旧实现

`sdflow-ship/scripts/ship_gate.py::plan_was_renamed(root, plan_rel)` —— 比较
`git log --diff-filter=A --format=%H -- <plan_rel>` **带**与**不带** `--follow` 的首行 sha，
不同即判「plan 曾被改名」→ `decide()` emit `UNKNOWN`。函数 + `decide()` 调用点**整体删除**
（未保留作「双保险」：它既误报又漏报，留着只会让误报面继续存在）。

### 新判据

`stray_done_tag_commits(root, sha, change)` —— **不检测「有没有发生过改名」（原因），直接检测
「危害有没有发生」（结果）**：本 change 是否存在落在完成判据窗口 `[plan_first_sha, HEAD]` **之外**
的 `checkpoint(<change>:task<N>-` 标签提交。有 ⇒ 窗口起点是错的 ⇒ fail-closed `UNKNOWN`（exit 6）。

- **窗口外的枚举方式（零新解析器）**：「窗口外」= 从 `sha` **可达、但不是 `sha` 自身**的提交
  （HEAD 的历史恰好 = `sha` 可达集 ∪ `sha..HEAD`，二者互补 ∴ 无需列 HEAD 全史再做差集）。
  一次 `git log <sha> --no-merges --format=%H %s`，git 自己出格式，无手搓解析。
- **复用既有单一源**：抽出 `_tag_task_id(subject, change, require_namespace=False)` 作为完成标签
  识别的**唯一**判据（字面前缀 + `TAG_RE` 锚定匹配 + 命名空间归属），`done_task_ids()`（窗口内计数）
  与 `stray_done_tag_commits()`（窗口外检出）**共用**它。未手抄第二份正则或第二份枚举逻辑。
- 🔴 **窗口外只认带本 change 命名空间的标签**（`require_namespace=True`）：裸标签
  `checkpoint(task<N>-` 无从归属，本仓 main 上大量存在别的 change 的遗留裸标签
  （见 `test_window_excludes_legacy_and_merge`），认它即**每个 change 全数误报**。
  窗口**内**仍保留 A1 向后兼容（裸标签按窗口计入），语义未变。
- **调用点位置变化**：由「`plan_closing_ticket_check` 之前、`plan_first_sha` 之前」移到
  「`plan_first_sha` 之后」（新判据需要窗口起点）。`sha` 为空（plan 未提交）⇒ 无窗口 ⇒ 跳过，
  交由既有「双通道皆不可判」分支处置。

**提示信息（可操作）**：
```
检测到本 change 有 N 个完成标签提交（如 <sha7>）落在完成判据窗口 [<sha7>, HEAD] 之外，
窗口起点不可信、已完成 ticket 会被判未完成并可能重派；通常是在途 plan（<plan 名>）被重命名 /
删除重建所致（MUST NOT 重命名在途 plan，见 design Migration Plan）。
请把 plan 恢复为其首次提交时的路径，或人工确认后处理
```
（旧文案「请改回原文件名」在模式 ① 下**无原名可改回** = 永久自锁，已撤。）

### 🔬 三种模式的 fixture 实测记录（本次修复的核心证据）

先用独立 git 仓复算旧判据，再落成 pytest 用例。**每个用例都带一条非空锚断言
`_old_heuristic_would_flag()`**，复算已撤除的旧判据、钉死「本 fixture 确实落在旧判据的哪一格」
——没有它，三个用例可能全是恒真绿（vacuous anchor）。

#### 模式 ① 误报 → 永久自锁（旧判据 True，新判据 MUST 绿）

同一 commit 里「删掉 change A 的 `tickets.md` + 新建 change B 的 `tickets.md`」。实测输出：

```
 openspec/changes/{change-a => change-b}/tickets.md | 2 +-      ← git 确实配对成改名
no-follow=e382f655ba5cad38a1673637bfe74e22c8b2032e
follow   =66d55c3dddd6ca30e1b3736f3c36d176f827c6af
>>> 模式1 旧判据 = True（误报，B 从未被改名）
```

成因：本 change 强制所有 `tickets.md` 用同一套 `### Task N:` / `Blocked-by:` / `R-ID:` 模板，
git 的内容相似度（默认 ~50%）天然过线。危害：错误提示无原名可改回，用户唯一出路是历史重写
（本仓明禁 `git rebase -i`，且会击穿 `reviewed_sha` 审计锚）。

新判据不误报：change B 是全新 change，其命名空间下不存在早于 plan 创建的完成标签。
用例 `test_mode1_lookalike_plan_in_another_change_is_not_flagged` → `CONTINUE_IMPL` ✅

#### 模式 ② 两步改名漏报（旧判据 False，新判据 MUST 红）

先 `git rm` 一次提交、后新建一次提交。实测输出：

```
no-follow=f8c39b0c21ac796cf068996ed44b16294c52b18e
follow   =f8c39b0c21ac796cf068996ed44b16294c52b18e     ← 两者相等 ⇒ 旧判据 False
--- 全史 ---
f8c39b0 chore: 以新名重建 plan
0385187 chore: 删掉旧名 plan
20fb2e8 checkpoint(demo:task1-a): 改名前完成 task1     ← 落在窗口 [f8c39b0, HEAD] 之外
```

成因：git 的重命名配对**只在单个 commit 的 diff 内**做，跨 commit 无从判断。而这正是设计要防的
场景本身，旧判据静默放行。新判据检出 `20fb2e8`。
用例 `test_mode2_two_step_rename_is_detected` → `UNKNOWN` / exit 6 ✅

#### 模式 ③ `git mv` + 同提交大幅编辑漏报（旧判据 False，新判据 MUST 红）

实测输出：

```
no-follow=2949e94b058cb3e693ce6b1c7d294090de1b398c
follow   =2949e94b058cb3e693ce6b1c7d294090de1b398c     ← 相似度跌破阈值 ⇒ 旧判据 False
>>> 模式3 旧判据 = False（漏报）
```

成因：相似度跌破默认阈值。**天然触发路径**：`superpowers-plan.md` → `tickets.md` 迁移**正需要**
给每个 Task 段补 `R-ID:` / `Blocked-by:`（本 change 新引入的格式要求）= 改名 + 大幅编辑同提交。
用例 `test_mode3_rename_with_heavy_edit_is_detected` → `UNKNOWN` / exit 6 ✅

> 两镜给出的修法互相冲突（调低相似度阈值 `-M1%` 能救 ③ 却加重 ①）——这本身证伪了启发式路线：
> 拿模糊启发式回答一个需要精确答案的问题（CLAUDE.md 基准 5 的警号）。

### 测试改动（`sdflow-ship/tests/test_plan_resolver.py`）

| 动作 | 用例 |
|---|---|
| **删** | `test_inflight_plan_rename_rejected_as_unknown`、`test_never_renamed_plan_not_flagged`（针对旧函数） |
| **新增** | `test_mode1_lookalike_plan_in_another_change_is_not_flagged`（绿）<br>`test_mode2_two_step_rename_is_detected`（红→检出）<br>`test_mode3_rename_with_heavy_edit_is_detected`（红→检出）<br>`test_normal_inflight_change_not_flagged`（正常在途不触发）<br>`test_legacy_bare_tags_outside_window_do_not_trigger`（🔴 防大面积误报：窗口外裸标签）<br>`test_other_change_namespaced_tags_outside_window_do_not_trigger`（窗口外他 change 命名标签） |

全部为**真实 git fixture 仓**（`repo` fixture + 真 `git mv` / `git rm` / 真提交），无 mock。
`sdflow-ship/tests/test_plan_resolver.py` 15 passed。

### 🔴 gate 自验（本 change 自己）

```
$ python3 sdflow-ship/scripts/ship_gate.py --change harden-implement-review-loop --root "$(git rev-parse --show-toplevel)"
[ship-gate] RUN_CODE_REVIEW → next=sdflow-code-review — 在途 plan 未含收尾票校验（grandfathered：
文件名 'superpowers-plan.md' 非 tickets.md 新名，见 design Migration Plan）；实现完成，进入代码审
exit=0
```
仍为 `RUN_CODE_REVIEW`，**未误报本 change 自己**。

### T257 已因本次重构失效（未处理，交编排层）

`openspec/issues/todolist/2026-07-todolist.md` 的 **T257**（「`plan_was_renamed` 内部已算出不带
`--follow` 的首次新增 sha，紧随其后的 `plan_first_sha` 又对同一 `plan_rel` 重发一次完全相同的
`git log --diff-filter=A`」）—— `plan_was_renamed` 已整体删除，那次重复的 git 调用随之消失，
**该 todo 的标的不复存在**。按指示**未改 todolist**，处置交编排层。

---

## FIX-2 · `sdflow-done` verify 用文件名判轨（CRITICAL）

**位置**：`sdflow-done/SKILL.md` 第一步 verify prompt 的步骤 4（实现期聚合覆盖需求）。

**旧措辞**：按 `tickets.md` / `superpowers-plan.md` **文件名**判轨——旧名即判 superpowers 轨 ⇒
该需求判「不适用」。**违反 delta 明文**：`specs/impl-orchestration/spec.md` 第 102 行
「**文件名 MUST NOT 参与轨道路由判定**——路由权威仍是 config 键 + plan frontmatter marker」。

**新措辞**：轨道判定改读**路由权威** = 仓 `openspec/config.yaml` 的 `impl-pipeline` 键 + plan 文件头
frontmatter 的 `impl-pipeline` marker（引用 `sdflow-implement/scripts/impl_route.py` 的
`read_plan_marker` / `resolve_pipeline`：marker 存在则 marker 胜出，缺失则取 config 键；marker
键重复 / 值非法 / frontmatter 未闭合 → UNKNOWN 语义停）。**文件名只用于「定位」plan 文件**，
两个名字都要找（含归档路径）。并显式写入两条防误读：

- ⚠️ MUST NOT 因为叫 `superpowers-plan.md` 就判 superpowers 轨——grandfather 条款下**旧文件名同样
  覆盖在途的 tickets 轨 plan**。**本 change 自身即反例**：plan 名 `superpowers-plan.md`、frontmatter
  marker 是 `impl-pipeline: tickets`，它是 tickets 轨、有收尾票；按旧写法 verify 会静默跳过该需求。
- 〔区分〕`ship_gate` **第四道 plan 校验以文件名为判据是对的**（delta 明确它「仅用于区分『新出 plan /
  在途或他轨 plan』」）——**未改动 gate 的第四道校验**。

---

## FIX-3 · 第零步未检 `eval` 自身退出码（Important）

**缺陷**：四个编排 SKILL 共享的第零步核心段只检 `resolve-models.sh` 的退出码，随后
`eval "$MODELS_ENV"` **不检 eval 自身退出码**，直接进 (d) 变量校验。voice 实测反例：resolver 输出
**先**设合法 host/tiers、**再**跟一条非法命令 ⇒ eval 退出码 127，而变量校验全 PASS ⇒ 放行。
delta 失败清单第 ② 项「非零退出**或输出无法 eval**」，后半未实现。

**修法**：(c) 步改为 `eval "$MODELS_ENV"; EVAL_RC=$?`，**立即捕获并检查** `EVAL_RC`，非 0 →
fail-loud 硬停（同文案 + 注明「resolver 输出无法 eval，eval 退出码 $EVAL_RC」），
**MUST NOT 带着半成品环境继续做 (d) 的变量校验**。

**同步落点**（该段被 `hack/check_tier_resolution_parity.py` 逐字节锁死，四处经脚本同一次替换写入）：
`sdflow-implement` / `sdflow-done` / `sdflow-code-review` / `sdflow-spec-review` 的 `SKILL.md`。

- `python3 hack/check_tier_resolution_parity.py` → ✅ 4 处逐字节一致
- `hack/tests/test_tier_resolution_parity.py` 新增 golden 用例 `test_eval_own_exit_code_is_checked`
  （钉死 `eval "$MODELS_ENV"; EVAL_RC=$?` / 「MUST 立即捕获并检查」/「`EVAL_RC` 非 0 → fail-loud
  硬停」/「MUST NOT 带着半成品环境继续做 (d) 的变量校验」四条 needle）→ 绿
- `sdflow-implement/SKILL.md` 的 8 类失败表第 4 行「输出无法 eval」原按「`$SDFLOW_HOST` 仍为空」
  描述症状（正是这个 fail-open 洞），一并改成按 `EVAL_RC≠0` 判定。

### 🔎 面治追加（超出 FIX-3 字面范围，明说）

`grep -rl "捕获退出码再 eval"` 查出**第五处**同缺陷：`sdflow-spec/SKILL.md` §0.2 的 (c) 步
（该 SKILL 用的是有意精简的变体、不在 parity 的 `SITES` 名单内，故门禁照不到）。按 CLAUDE.md
基准 3「面治优先于点补」一并补上同一条检查，措辞标 `[impl-review-fix FIX-3 · 面治]`。
这是**同片一致性面的一次扫全**，不是加宽目标范围。

---

## FIX-4 · 聚合套件允许各层锚不同 SHA（Important）

**缺陷**：`sdflow-implement/SKILL.md` 的聚合套件证据 schema 要求每层记测试时 `git rev-parse HEAD`，
且允许发现回归后进 fix 循环——但**没有要求修复后重跑先前已绿的层**，也没要求所有通过行锚**同一**
SHA。于是「unit@A 通过 → integration 失败 → 修到 B → integration/e2e@B 通过」也能拼出「全部通过」。
delta 与 design 都把收尾票定义为回答「**全部功能票实现完毕这一刻**，聚合套件是否通过」——
**「这一刻」蕴含单一盘面**。∴ 这是**实现 spec**，不是加宽。

**生产侧（`sdflow-implement/SKILL.md`「聚合套件发现契约」）** 新增第 6 条：

> 🔴 **单一盘面**：任何产品代码修复之后（fix 循环的每一轮）**MUST 重跑全部已覆盖层**，MUST NOT
> 只重跑刚失败的那一层；报告里所有判「通过」的行 MUST 锚**同一个最终 SHA**（= 最后一次修复之后的
> `git rev-parse HEAD`）。未覆盖层不受此约束（其 SHA 位写的是判定依据，本就无盘面语义）。
> ❌ 反例：unit@A 通过 → integration 在 A 失败 → 修到 B → integration/e2e@B 通过。

**消费侧（`sdflow-done/SKILL.md` verify 步骤 4 tickets 轨分支）** 新增核验：

> 🔴 MUST 核验各「通过」层的 SHA 一致；若锚在不同 SHA（如 unit@A、integration@B），说明先绿的层
> 从未在最终盘面上跑过、「全部通过」是拼出来的 ⇒ 判**核心缺口**，MUST NOT 判 ✅
> （未覆盖层不参与此核验）。

---

## 收尾验证

| 门 | 命令 | 结果 |
|---|---|---|
| 全量测试 | `/usr/bin/python3 -m pytest` | **2927 passed, 11 skipped, 3 xfailed** in 300.96s，**0 failed** |
| tier parity | `python3 hack/check_tier_resolution_parity.py` | ✅ 4 处逐字节一致（exit 0） |
| principles sync | `python3 hack/sync_principles.py --check` | ✅ 22 个投放面一致（exit 0） |
| workflow guide | `python3 hack/gen_workflow_guide.py --check` | ✅ 一致（exit 0） |
| gate 自验 | `ship_gate.py --change harden-implement-review-loop` | `RUN_CODE_REVIEW`（exit 0） |

**用例数差**：基线 2922 → 2927（+5）= FIX-1 净 +4（删 2 增 6）+ FIX-3 golden +1。

## 改动清单（`git diff --stat`）

```
 hack/tests/test_tier_resolution_parity.py |  15 +++
 sdflow-code-review/SKILL.md               |   2 +-
 sdflow-done/SKILL.md                      |  26 +++-
 sdflow-implement/SKILL.md                 |  11 +-
 sdflow-ship/scripts/ship_gate.py          | 125 +++++++++++++-------
 sdflow-ship/tests/test_plan_resolver.py   | 189 +++++++++++++++++++++++++-----
 sdflow-spec-review/SKILL.md               |   2 +-
 sdflow-spec/SKILL.md                      |   5 +-
 8 files changed, 296 insertions(+), 79 deletions(-)
```

**未触碰**（硬约束）：`proposal.md` / `design.md` / `tasks.md` / `specs/`（design 域失鲜面）、
`superpowers-plan.md`（未改名、未新建 `tickets.md`、未勾复选框、未打 `task<N>-` 标签）、
`openspec/issues/todolist/`。历史 impl-report 里对 `plan_was_renamed` 的记述**按考古层原样保留**，
未回改（它们记录的是当时的事实）。**未 commit**，工作树留给编排层。
