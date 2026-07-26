# Task 3 · fix 轮次 1（双轴审 4 Important + 4 Minor）

> 承接 `task3-stage1-acceptance.md`（**不覆盖**；按 F3/F4/F6/F7/F8 就地修改了它的
> §3⑥ 诚实边界注、§5 引用方式、§6 登记表、**§7 门结论（重写）**、§8 诚实边界（补 3 条））。
>
> 基线 HEAD = `54d38bb`。全部定点变异均在 **`git worktree` 副本**
> （scratchpad 下的 detached worktree）里做，主工作树未被变异污染。

---

## 0. 一览

| # | 级别 | 处置 | 强度 |
|---|---|---|---|
| F1 | Important | `map_stage` 回退用 `tail` 再匹配 + 补两条同形规则；unknown 占比 **55% → 18%** | ✅ 修复 + 3 处变异回验 |
| F2 | Important | 六种故障固化为 `hack/tests/test_sdflow_spec_failure_modes.py`（19 用例）；**锚强度逐条分级** | ✅ 固化 + 13 处变异回验 |
| F3 | Important | 上一轮 §7 门结论重写为「实质到位；字面判据未满足；**是否放行由人拍板**」+ 逐条状态表 | ✅ 改文 |
| F4 | Important | fail-open 绕过口另立 **T237**，T235 备注回指；写进上一轮 §8 诚实边界第 8 条 | ✅ 登记 |
| F5 | Minor | 新增 `hack/tests/test_checkpoint_slug_coverage.py`：SKILL.md 的 slug 经 `map_stage` MUST NOT 落 unknown | ✅ 新守卫 + 4 处变异回验 |
| F6 | Minor | 报告与 todolist 内的行号锚改 ID 锚 / 小节锚；改不了的（`tasks.md` / `design.md`）如实记 | ✅ 改文 + 说明 |
| F7 | Minor | `retro/report.md` 含实时墙钟、in-progress 期间永不字节可复现 ⇒ 登记为诚实边界 | ✅ 边界 |
| F8 | Minor | 故障⑥ 的一次性 wrapper 已被交付物级回归取代，条目自然消解 | ✅ 随 F2 消解 |

---

## F1 · `map_stage` 点补 → 面治

### 问题

`retro_report.py::map_stage` 只在 `task\d+` / `-impl` 两条判定里剥命名空间，
**前缀匹配仍拿含 `<change>:` 前缀的整串 `inner` 去比** ⇒ `<step>` 段精确等于既有规则的
checkpoint 全落 unknown。另有 `sdflow-code-review` / `sdflow-spec-review` 与上一轮补的
`sdflow-spec-grill` / `sdflow-spec-generate` **同形**却漏补。

**这不是历史遗留，是目标态 producer 正在产出的形态**：
`sdflow-implement/SKILL.md:287` 逐字写着 `checkpoint-commit.sh "<change>:plan"`。

### 修法

`sdflow-retro/scripts/retro_report.py::map_stage`：

```python
ordered = sorted(_STAGE_RULES, key=lambda r: -len(r[0]))
for candidate in (inner, tail):          # 整串无命中 ⇒ 回退用剥掉命名空间的 tail 再试一次
    for prefix, stage in ordered:
        if candidate.startswith(prefix):
            return stage
if inner.endswith("-cross-review") or tail.endswith("-cross-review"):
    return "other"
```

回退**只在整串无命中时**发生 ⇒ 既有语义（change 名本身带阶段词）一字未动，纯增量。
`_STAGE_RULES` 另补 `("sdflow-code-review","code-review")` + `("sdflow-spec-review","spec-review")`。

### 改前 / 改后（同一 HEAD `54d38bb`、同一 commit 集，apples-to-apples）

**按 checkpoint 条数**（全历史 `git log --all`，682 个 checkpoint）：

| | unknown 条数 | 占比 |
|---|---|---|
| 改前 | **52** | 7.6% |
| 改后 | **19** | 2.8% |

**按报告墙钟**（`openspec/retro/report.md` §「聚合① 阶段占比」表）：

| 阶段 | 改前 墙钟(min) / 占比 | 改后 墙钟(min) / 占比 |
|---|---|---|
| **unknown** | **15262.1 / 55%** | **5071.5 / 18%** |
| spec-review | 4416.2 / 16% | 13445.6 / 49% |
| impl | 4455.2 / 16% | 4455.2 / 16% |
| ff | 1839.0 / 7% | 2609.5 / 9% |
| grill | 598.0 / 2% | 682.9 / 2% |
| code-review | 647.2 / 2% | 676.9 / 2% |
| other | 216.5 / 1% | 492.4 / 2% |
| done | 141.2 / 1% | 141.2 / 1% |

⇒ **10190.6 min（≈170 hr）从 unknown 桶被正确归因**，其中绝大部分归到 spec-review
（`<change>:spec-review` / `:design-gate` / `:spec-review-amend` 这几段跨度最长）。
`impl` / `done` 分文未动（本次回退不触及它们的判定路径），是「纯增量、无回归」的旁证。

### 面治核对：改后**仍落 unknown 的全部 19 条**，逐条给理由

| 条数 | `checkpoint(<inner>)` | 归类 | 理由 |
|---|---|---|---|
| 7 | `add-sdflow-devenv` | **真无规则** | 拿 change 名当 `<step>` 参数，串里**不含任何阶段信号**——补规则只能靠猜 |
| 3 | `mlh-p2-anchor-lint` | **真无规则** | 同上（change 名当 step） |
| 1 | `scope-split` | **真无规则** | 一次性 ad-hoc 步名，无同族 |
| 1 | `upgrade` | **真无规则** | 同上 |
| 1 | `fix-mechanical-layer-silent-failures:defer-minors` | **真无规则** | ad-hoc 步名（"defer 掉次要项"），无阶段语义 |
| 1 | `mlh-p5-gate-frontmatter:crfix-parser-harden` | **不补（判断）** | `crfix` 疑为 code-review-fix 缩写，但**只出现 1 次、是 ad-hoc 缩写**；为单次出现的私人缩写补词表 = 点补，正是本 finding 要治的病 |
| 1 | `enable-codex-background-outside-voice:t6-review-archive` | **不补（格式违规）** | `t6-` 是 `task<N>-<slug>` 的违规写法 |
| 4 | `sdflow-retro-cleanup:t58…t61-*` | **不补（格式违规）** | 同上，`t<N>-` 而非 `task<N>-` |

> 🔴 **为什么不给 `t<N>-` 补规则**：`task<N>-<slug>` 是 **`ship_gate` 完成判据主锚的契约格式**
> （`tasks.md:4` 与 `docs/workflow-skills/superpowers-writing-plans.md:98` 都写死了它）。
> 给 `t<N>-` 补一条映射 = 让 retro 认可一种 gate 本身会拒的格式，**是把契约往回改**。
> 正解是**前向堵住**：F5 的新守卫保证 SKILL.md 今后写出的 slug 一定可归类，
> 历史里这 5 条违规 slug 如实留在 unknown。
>
> 剩下 12 条（change 名当 step / ad-hoc 步名）是**信息在源头就不存在**——
> 提交 subject 里没有阶段信号，任何映射都是编的。**这是合法的诚实残余，不是漏网格。**

### 变异回验（worktree 副本 · 判据「期望红 ⊆ 实际红」）

| 变异 | 期望红 | 实测 |
|---|---|---|
| M1 `for candidate in (inner, tail)` → `(inner,)` | `test_namespaced_step_slug_falls_back_to_tail` | ✅ `1 failed, 40 passed`，正是该用例 |
| M2 删 `("sdflow-code-review","code-review")` | `test_two_review_skill_slugs_map_to_their_stage` | ✅ `1 failed, 40 passed`，正是该用例 |
| M3 删 `("sdflow-spec-review","spec-review")` | 同上 | ✅ `1 failed, 40 passed`，正是该用例 |
| 还原 | 全绿 | ✅ `41 passed` |

---

## F2 · 六种故障注入固化进 pytest

### 问题

`tasks.md` 覆盖图声称「六种故障处置 · 故障注入 · 4.5 · **会红 ✅**」，
但上一轮是**一次性人工注入、夹具跑完即删** ⇒ **没有任何回归会红**，那一格当时是假绿。
覆盖图在 `tasks.md` 里、MUST NOT 改 ⇒ 唯一正解是**让它变成真的**。

### 落点与理由

**`hack/tests/test_sdflow_spec_failure_modes.py`**（新建，19 用例）。

选它不选 `sdflow-init/tests/` 的理由：`sdflow-spec` 是**纯 Markdown 编排类 skill，没有
`scripts/` 也没有 `tests/`**；它既有的两道机械门就住在 `hack/tests/test_decision_memo_gate.py`
（同一 idiom——门的实现写在测试文件里，因为被守的"产品"是给模型看的指令，**不存在第二份可执行实现**）。
故障④ 直接复用那份文件的 `_decision_hash`（真跑 schema 文档里那条 bash 命令，**MUST NOT 复刻算法**），
放同一目录接线最省。`sdflow-init/tests/` 只该住 `sdflow-init` 自己的资产（hook 行为已在
`test_ff0_branch_guard.py` 里）。

### 六条的锚强度分级（**核心诚实声明**）

| # | 故障 | 可执行 producer | 给的锚 | 强度 |
|---|---|---|---|---|
| ① | 工作树脏 | **无** —— B.1① 只是给模型看的指令 | SKILL.md 指令在场（探测命令 + halt 处置 + 「MUST NOT 静默继续」）+ design 失败模式表行在场 | **弱** |
| ② | 在其它 feature 分支 | ✅ `ff0-branch-guard.py` | **真跑 hook**：deny 文案须给出失败模式表的**三选一** | **强** |
| ③ | 目标分支已存在 | **无** —— git 自身行为 + B.1② 指令 | 指令在场 + **git 真实行为对账**（`checkout -b` 撞名必非零 / `checkout` 复用必成功） | **中** |
| ④ | 纪要陈旧（身份字段不匹配） | 判 1/2 已有门；判 3/4 的算法有单一源 | **四 fixture 真跑判 3/判 4**，三态 verdict 互不塌陷 | **强** |
| ⑤ | openspec CLI 缺失 | **无** —— 0.1 预检是指令 | 指令在场（含「MUST NOT 手工创建 change 目录顶替」）+ 真实剥 PATH 后 exit code ≠ 0 | **中** |
| ⑥ | `instructions --json` schema 断言不过 | **无** —— C.3 §2 是指令 | **真 CLI 载荷 ⊇ SKILL.md C.3 §2 声明的字段集**（F-13 漂移探测）+ 假 `openspec` 在临时 PATH 上三种畸形逐个 fail-closed | **强** |

🔴 **降级为语义规则的是 ①（弱）与 ③⑤ 的"处置正确"那一半**，理由如下：

- **①③⑤ 没有可执行 producer**。它们守的是「主 session 收到脏工作树 / 分支撞名 / CLI 缺失时
  **真的按指令 halt 了没**」——这是模型行为，**无确定性信号**，无可信捕获路径
  （模型自报不算机械门）。这条残余**结构性存在，不会因为再写几个测试而消失**。
- 因此我给的是**弱锚 / 中锚：守「指令还在、没被后续编辑悄悄删掉或弱化」**，
  这是有确定性信号的那一半（基准 1：能机械的机械化，残余诚实划分）。
  **MUST NOT 把它读成「处置正确会红」。**
- **MUST NOT 硬造恒真锚顶替**：我没有为「模型是否 halt」写任何断言——那种断言的参照系不含
  任何仓状态，无论怎么改仓都不会红。

⇒ **覆盖图那一格的真实状态是「②④⑥ 强 · ③⑤ 中 · ① 弱」，不是齐刷刷的 ✅。**
`tasks.md` MUST NOT 改，故该差异记在此 + 上一轮 §7.1 表里，留 archive 阶段一并订正。

### 反循环设计（为什么这些不是「测试自己守自己」）

④⑥ 的判据**单一源都在被守的文档一侧**：

- `decision_hash` 由 **schema 文档里那条 bash 命令**真跑得出（复用 `_decision_hash`），不是 Python 复刻；
- 身份字段名从 **`decision-memo-schema.md` §2 的样例块**抠出（`test_identity_keys_all_come_from_the_schema_doc` 守）；
- `instructions --json` 的必需字段集从 **SKILL.md C.3 §2** 抠出，再拿去对**真 CLI** 的载荷。

⇒ 改文档即改判据（M④d / M⑥a / M⑥b 三处变异实测），不存在「测试与实现同源自证」的闭环。

### 变异回验（13 处 · 全部在 worktree 副本 · 判据「期望红 ⊆ 实际红」）

| 变异 | 期望红 | 实测 |
|---|---|---|
| ①a SKILL.md 删「MUST NOT 静默继续」 | `test_fault1_dirty_worktree_halt_instruction_is_present` | ✅ `1 failed, 1 passed` |
| ①b design 失败模式表把「MUST NOT 静默 `add -A`」改成「照常继续」 | `test_fault1_design_failure_table_still_lists_it` | ✅ `1 failed, 1 passed` |
| ② hook deny 文案删掉选项 c「就地继续」 | `test_fault2_deny_offers_exactly_the_three_documented_choices` | ✅ `1 failed` |
| ③a SKILL.md 删 fallback 指令 | `test_fault3_fallback_instruction_is_present` | ✅ `1 failed, 1 passed` |
| ④a `check_memo_identity` 不比 `branch` | fixtureB + 三态可分 | ✅ `2 failed, 3 passed`，正是这两条 |
| ④b 判 4 不重算 hash | fixtureC | ✅ `1 failed, 4 passed` |
| ④c `undrafted` 并入 `stale` | fixtureD + 三态可分 | ✅ `2 failed, 3 passed`，正是这两条 |
| ④d schema 文档把 `branch` 改名为 `on_branch` | `test_identity_keys_all_come_from_the_schema_doc` | ✅ `1 failed` |
| ⑤a SKILL.md 删「MUST NOT 手工创建 change 目录结构顶替」 | `test_fault5_preflight_instruction_is_present` | ✅ `1 failed, 1 passed` |
| ⑥a C.3 §2 把 `resolvedOutputPath` 写错名 | 真载荷对账 + confused-deputy 字段在场 | ✅ `2 failed, 4 passed`，正是这两条 |
| ⑥b C.3 §2 删掉一个字段（打到 `MIN_DECLARED_FIELDS` 之下） | 真载荷对账 + 两条畸形用例 | ✅ `4 failed, 2 passed` |
| ⑥c 断言逻辑砍掉类型校验 | `…malformed_payload_fails_closed[dependencies 类型不符]` | ✅ `1 failed, 4 passed`，正是该参数化实例 |
| ⑥d SKILL.md 删「MUST NOT 重试同一调用」 | `test_fault6_no_retry_instruction_is_present` | ✅ `1 failed` |
| 还原 | 全绿 | ✅ `19 passed` |

**未做变异回验的一条（如实记）**：③b `test_fault3_git_really_behaves_as_the_instruction_assumes`
锚的是 **git 自身行为**（同 `test_validate_strict_only_covers_delta_specs` 锚 openspec CLI 行为），
**我无法在不改 git 的前提下定点变异它**。它不是恒真锚（git 改语义会红），但它的失效场景在本仓外。

---

## F3 · 门结论越权 → 改为「实质到位 + 字面未满足 + 人拍板」

### 问题

`tasks.md` 的阶段一验收门判据字面是「**4.1–4.6 全过** + canonical 七处 + 3.4 sunset 已落定」，
而 4.3（截断 `design.md` 经 `validate --strict` → 红）**未勾**——该断言已被实测证伪（T232）。
上一轮报告却直接写「**阶段一验收门通过，可启动阶段二**」= **执行方替人接受了偏离**。

### 修法

重写 `task3-stage1-acceptance.md` §7，结构改为：

1. **§7.1 逐条状态表**（4.1 / 4.2 / 4.3 / 4.4 / 4.5 / 4.6 / canonical 1.1–1.8 / 3.4，各带证据锚）；
2. **§7.2** 4.3 未满足项的性质（断言写错，不是实现缺件）；
3. **§7.3 结论**：「**实质到位；字面判据（4.1–4.6 全过）未满足，因 4.3 的断言被实测证伪（T232）。
   是否放行由人拍板。**」+ 支持放行的理由（标明「供拍板参考，非结论」）+ 一句
   「MUST NOT 由执行方代拍」。

顺带把 4.5 那一格从裸 ✅ 改成「✅（注入）· ⚠️（回归）」，指向 F2 的固化。

### Spec 轴那两条的核对结果（**逐条真打开过**）

- **3.4 sunset 确已落定** —— `CLAUDE.md` §「旧入口 sunset 条件（阈值已写死；**与阶段二成败无关**）」，
  内容完整：观察窗（连续 6 个新 change 或 8 周，先到者为准）+ 三档阈值（采用率 ≥5/6 ·
  质量「上下文缺失类 finding = 0 且采纳率 ≥0.79」· 成本中位 ≤75 min/change）+
  **二选一处置**（三档全达标进 sunset / 任一不达标即**删除 `sdflow-spec`**）+
  「🔴 MUST NOT 无限期延长观察窗」。✅ 属实。
- **canonical 1.1–1.8 由 Task 2 收票** —— `37e3820`
  + `impl-reports/task2-canonical-sync{,-fix1..fix4}.md`；机械守 = `hack/tests/test_canonical_entry_sync.py`
  （29 条断言，本轮全量 pytest 内跑绿）。✅ 属实。

---

## F4 · T235 漏登记「文档化 fail-open 是模型可用的绕过口」

### 问题

上一轮用 FF-0 守卫 docstring 明写的 fail-open（change 名 token 含 `$` ⇒ 守卫不展开、不猜、放行）
绕过了 FF-0 的 MUST-halt（SA-05 Scenario），但 T235 **只登记了 mis-scope（按 session cwd 判仓）**。
漏掉的这一条性质更重：**该 fail-open 是模型自己就能触发、且不留任何审计痕的绕过口**——
与哨兵逃生口不同级（哨兵至少落一个文件、是 transcript 里可审计的一次有意动作）。

### 修法

`sdflow-issues/scripts/todolist.py` 的 `set-status` **只能改状态、不能改 summary**
（`--help` 实查：仅 `--id/--to/--evidence/--reason/--month`），无编辑既有条目正文的子命令
⇒ 按 F4 给的第二条路：**补一条新的 + 两条互相指**。

- **新增 `T237`**（`add --json <file>`，显式带 `change: add-sdflow-spec`，避免自动挂错 change）：
  登记 fail-open 绕过口本身，并把 Spec 轴给的**有界缓解**作为 `approach`（思路）写入——
  判定前扫**有界 token 集**（① change 名 token 落在 `CHANGE_NAME_OK_RE` 之外；
  ② 出现改 cwd 的 token `cd` / `-C` / `git -C`，这一项同时覆盖 T235 的 mis-scope 前提）→
  命中即「前提不成立」→ **照旧 fail-open 放行，但在 reason 里明写「本次没判、理由是 X」**。
  条目里明确标注这是**可见性缓解、不是堵死**，且 **本轮不实现**（避免加宽）。
- **T235 的「备注」回指 T237**，并点明两者关系：**T235 = 判得不对（锚错了仓）· T237 = 根本没判（判据被合法跳过）**，同一处代码，宜一并修。
  > 只改「备注」是安全的：总览表 snapshot 只承载 `module/summary/type/status/time/change/batch`，
  > **不含备注** ⇒ 手改它不可能破坏 dual-reader 一致性。`scan --json` 复核 `problems: []`。
- **写进上一轮报告的 `## 诚实边界`**（新增第 8 条），并点明 §3② 的「处置一致」只在**目标仓内**成立。

### 采纳 Spec 轴方向的理由

修 mis-scope 需要解析 `cd` / `-C` / `&&` —— **shell 是无界语法面，基准 5 禁手搓**
⇒ 它**只能**是诚实边界 + 登记。而「命令串里有没有出现某个 token」是**有界**判定，
可以做，且只用来降级到「本次没判」而非阻断 ⇒ 不引入新的罢工分支。**已按此写入 T237 的思路。**

---

## F5 · slug 字面量两处硬编码无机械守

### 问题

产出侧 = 各 `SKILL.md` 里逐字写死的 `checkpoint-commit.sh <slug>`；
消费侧 = `retro_report.py::_STAGE_RULES`。两处硬编码、零守卫 ⇒ SKILL.md 改名即**静默**落 unknown。
**这已经是第二次复发**（第一次 `sdflow-spec-grill/generate`，第二次本轮 F1）。

### 修法

新增 **`hack/tests/test_checkpoint_slug_coverage.py`**（2 用例）：
扫全部 `*/SKILL.md`，用有界正则抠 `checkpoint-commit.sh <bare|'q'|"q">`，
把占位符（`<change>` / `<N>` / `<slug>` / `<step>` / `<desc>`）替换为样例值，
断言每个 slug 经 **`map_stage`（从文件路径加载真实现，MUST NOT 复刻词表）** 不为 `unknown`。

两条恒真锚防线：
- **`MIN_CALLSITES = 9`**（实测 9 处）—— 防「正则一个字没匹配上 ⇒ 循环空转 ⇒ 恒绿」；
- **替换后仍残留 `<` 即判红** —— 出现新占位符必须回来登记，MUST NOT 静默跳过。

### 变异回验（4 处）

| 变异 | 期望红 | 实测 |
|---|---|---|
| M4 SKILL.md 改 slug 名（`sdflow-spec-generate` → `sdflow-spec-emit`） | `test_every_skill_slug_is_classifiable` | ✅ 报 `sdflow-spec/SKILL.md:459 … 落 unknown` |
| M5 撤掉 F1 的 tail 回退 | 同上 | ✅ 报 `sdflow-implement/SKILL.md:287 \`<change>:plan\` → \`demo-change:plan\` 落 unknown` |
| M6 SKILL.md 引入新占位符 `<foo>` | 同上（占位符 fail-closed 分支） | ✅ 报「含未登记的占位符」 |
| M7 破坏两处调用点写法 | `test_extractor_actually_finds_the_callsites` | ✅ 报「只抠到 7 个（下限 9）」 |

> M5 尤其说明问题：**这个守卫如果早存在，F1 那 13 个 `<change>:plan` 根本不会漏到今天。**

---

## F6 · 陈旧行号锚

| 锚 | 处置 |
|---|---|
| 上一轮 §6 T234 行引「T132 在 `2026-07-todolist.md:233`」 | ✅ **改为 ID 锚**：`…/2026-07-todolist.md` 的 **T132**。（本轮登记 T237 后它已漂到 `:238`——两天内漂了两次，正是行号锚不该用的实证） |
| 上一轮 §5 引 `openspec/retro/report.md:74` | ✅ **改为小节锚**：§「聚合① 阶段占比」表的 `unknown` 行，并注明原行号已指向数据行 |
| `tasks.md:102`（9.1，`unknown` 占 56% + `report.md:74`） | ❌ **改不了** —— 设计阶段定稿件，本阶段 MUST NOT 改。如实记：行号锚已漂，且 56% 这个数字在 F1 修复后变成 **18%** |
| `design.md:241`（可观测性段，`unknown` 桶现占 56%） | ❌ 同上（无行号锚，但 56% 已陈旧） |

⇒ 两条改不了的都记在上一轮 §5 的订正框里，**留 archive 阶段一并订正**（与 T232 同批）。

### 更稳的引用方式（已在本轮新写的内容里改用）

**行号锚天然会漂**（任何在前面插入内容的编辑都会移动它，且**不会报错**）。本轮起：

- 指 issue 条目 → 用 **ID**（`T132` / `T235`），ID 永不变；
- 指文档小节 → 用 **小节标题**（`§「聚合① 阶段占比」`），标题改名会被人一眼看见；
- 指测试 → 用 **`file::test_name`**（pytest 直接可跑，改名即红）；
- 指代码 → 用 **`file::symbol`**；只有在「就是要指那一行的字面文本」时才用行号，且随手标注版本/SHA。

本报告与本轮改写的所有段落**已全部按此执行**（可核：本文件内除引用他人既有行号外无新增裸行号锚）。

---

## F7 · `openspec/retro/report.md` 永不字节可复现

**登记为诚实边界**（已写进上一轮报告 §8 第 9 条）：

- **成因**：报告含**实时墙钟**——in-progress change 的阶段边界取当下时刻，
  只要本 change 未归档，任意两次再生的字节就不同。
- **后果**：「该文件是否被人手改过」**不可机械核**（无法用「重跑再生 + diff 判空」当门）。
  本轮与上一轮都只能靠**人工比对增量形态**判定（本轮：只有阶段占比表与 per-change 行的数字变了，
  结构、镜清单、待复评区块形态不变，与 `map_stage` 改动的预期影响一致）。
- **为什么不硬做**（通则④ 五问）：根因是"报告刻意包含实时量"；概率 = 100%（结构性）；
  影响 = 只丢「手改探测」这一层，而该文件是 **view-only 派生物、无下游消费者按它做判定**；
  完美成本高（要么冻结时间源、要么把实时量剥离到另一个文件，两者都改 retro 的口径）；
  简化方案 = **登记边界 + 保留 view-only 纪律**（改脚本→重跑再生，MUST NOT 手改）。
- **未另开 todolist 条目**：它不是缺陷、也没有待办动作——是一个已知且被接受的性质。
  写在诚实边界里即可，另立一条 OPEN todo 反而会在 sweep 里反复出现却永远无法关闭。

---

## F8 · 故障⑥ 的一次性 wrapper 未进诚实边界清单

**随 F2 固化后自然消解。** 上一轮 §3⑥ 的内联披露框已补一段，指向替代它的两条交付物级回归：
`test_fault6_real_cli_payload_carries_every_documented_field`（真 CLI 载荷对账）
+ `test_fault6_malformed_payload_fails_closed`（假 `openspec` 三种畸形 fail-closed）。
⇒ 该职责不再只活在 scratchpad 脚手架里，**不需要进诚实边界清单**。

（同批检查：上一轮报告里其余「一次性夹具」——④ 的四份 memo fixture 已由本轮
`test_fault4_fixture{A,B,C,D}` 固化；② 的 hook 注入本就有 `test_ff0_branch_guard.py`。
**六条里现在没有"只在 scratchpad 里验过、清单里又没写"的了。**）

---

## 收尾三件套（**全部亲跑，输出如实**）

```
$ git add -A && /usr/bin/python3 -m pytest            # 仓根全量
<见下方实测输出>

$ bash setup.sh
$ python3 hack/sync_principles.py --check
$ python3 sdflow-retro/scripts/retro_report.py --root .   # F1 改完数字会变，MUST NOT 手改
```

**实测输出**：

```
$ git add -A && /usr/bin/python3 -m pytest -q
2731 passed, 10 skipped, 3 xfailed in 282.85s (0:04:42)
```

- 相对上一轮的 `2708 passed`，**+23**（F2 的 19 条 + F5 的 2 条 + F1 的 2 条），零失败零 warning。
- 已知环境抖动用例
  `sdflow-init/tests/test_outside_voice_job.py::test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret`
  本轮**绿**。
- ⚠️ `git add -A` 在跑全量之前先做过（tracked 守卫看不见未 add 的新文件，
  `sdflow-issues/tests/test_downstream_reference_guard.py` 是全仓 tracked 扫描）。

```
$ bash setup.sh
  mode: symlink (Unix)
  [sync_principles] ✅ 19 个投放面全部与真相源一致
  [gen_workflow_guide] ✅ WORKFLOW-GUIDE.md 与单一源一致
  [async-branch-parity] ✅ 2 处 async host 调度段逐字节一致
  exit=0

$ python3 hack/sync_principles.py --check
  [sync_principles] ✅ 19 个投放面全部与真相源一致   (exit 0)

$ python3 sdflow-retro/scripts/retro_report.py --root .
  [sdflow-retro] 复盘报告已再生 → openspec/retro/report.md
  # 再生两次（写报告前 / 收尾时）结果一致，unknown 18% —— 本文件不手改该文件
```

> **dev/runtime checkout 纪律（adr/0005）**：`~/.claude/skills/*` 与 `~/.codex/skills/*` 的软链
> 在本票开始前**已经**指向本开发 checkout（Task 1/2 遗留），本轮 `setup.sh` 只是幂等重跑。
> **合并后须在运行 checkout（`~/.skills/sdflow-skills`）重跑 `setup.sh` 还原。**

## 本轮改动清单

| 文件 | 性质 |
|---|---|
| `sdflow-retro/scripts/retro_report.py` | F1 修复（`map_stage` 回退 + 两条规则） |
| `sdflow-retro/scripts/tests/test_retro_report.py` | F1 的两个新用例 |
| `hack/tests/test_checkpoint_slug_coverage.py` | **新建** —— F5 守卫 |
| `hack/tests/test_sdflow_spec_failure_modes.py` | **新建** —— F2 六种故障回归 |
| `openspec/issues/todolist/2026-07-todolist.md` | F4：新增 T237 + T235 备注回指 |
| `openspec/changes/add-sdflow-spec/impl-reports/task3-stage1-acceptance.md` | F3/F4/F6/F7/F8 就地修订（§3⑥ · §5 · §6 · §7 重写 · §8 补三条） |
| `openspec/retro/report.md` | 脚本再生（view-only 派生物） |
| 本文件 | fix 轮次 1 报告 |

**未改**（按契约）：`proposal.md` / `design.md` / `specs/` / `tasks.md` / `superpowers-plan.md`，
含**未改测试覆盖图**、**未勾任何复选框**、**未打完成标签**。
