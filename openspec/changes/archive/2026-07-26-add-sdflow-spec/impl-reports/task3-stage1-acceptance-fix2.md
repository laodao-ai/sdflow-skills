# Task 3 · fix 轮次 2（接缝复审 · 1 Important + 3 Minor · 窄修收口）

> 承接 `task3-stage1-acceptance.md` + `task3-stage1-acceptance-fix1.md`（两份**均不覆盖**）。
> 基线 HEAD = `68c896c`。全部定点变异均在 **`git worktree` 副本**（scratchpad 下 detached worktree）里做，
> 主工作树未被变异污染（收尾 `git status` 亲验）。
>
> **未改**（按契约）：`proposal.md` / `design.md` / `specs/` / `tasks.md` / `superpowers-plan.md`
> —— 含**未改测试覆盖图**、**未勾任何复选框**、**未打完成标签**。

---

## 0. 一览

| # | 级别 | 处置 | 变异回验 |
|---|---|---|---|
| F-A | Important | 故障④ 补 C.1 处置**指令在场锚**；面治扫全 19 格，另补故障② 的 B.1② 判定在场锚 | ✅ 7 处（含复审原样那条） |
| F-B | Minor | `map_stage` tail 回退：短前缀（≤4）要求 token 边界（全等或后接 `-`） | ✅ 3 处 |
| F-C | Minor | slug 守卫期望集 `*/SKILL.md` → 四片 producer glob（+8 调用点，下限 9→17） | ✅ 4 处 |
| F-D | Minor | 删掉 docstring 里未断言的「零重试/零写入」两词 + 说明它们由弱锚承载；顺带把 ⑤ 的三件事断满 | ✅ 3 处 |

**净变化**：`hack/tests/test_sdflow_spec_failure_modes.py` 19 → **21** 用例；
`hack/tests/test_checkpoint_slug_coverage.py` 2 → **3** 用例；
`sdflow-retro/scripts/tests/test_retro_report.py` +**1** 用例。

---

## F-A · 故障④ 自评「强锚」实测假绿（Important）

### 复现（先证伪，再动手）

在 HEAD `68c896c` 的 worktree 副本里，把 `sdflow-spec/SKILL.md` 里那句

```
身份不符（判 3）或 hash 不符（判 4）⇒ **呈现旧 memo 摘要 + `generated_at` 给人确认**
```

**整行删掉**，跑旧的 19 用例：

```
$ /usr/bin/python3 -m pytest hack/tests/test_sdflow_spec_failure_modes.py -q
19 passed in 2.79s
```

**复审的 M-B 属实。** 成因：判 3/判 4 的实现 `check_memo_identity` **住在测试文件里**
（`sdflow-spec` 是纯 Markdown skill，无 `scripts/`，见文件头「为什么放在 hack/tests/」），
故那五条 fixture 用例只证明「**判得出**」，证不了「**处置还写在 SKILL.md 里**」。
删掉处置句 ⇒ 模型不再核身份 ⇒ 陈旧纪要静默复用，而覆盖图 4.5 照旧绿。
**这正是本文件要治的假绿病，复发在自评最高的那一格。**

### 修法

1. 新增 `test_fault4_dispositions_are_present_in_the_skill`，把 C.1 的**四判 + 三条处置**逐条落锚：
   - 判 3「身份字段匹配当前盘面」、判 4「`decision_hash` 重算后匹配 / 重算纪要正文」；
   - 处置 A：「任一不过 ⇒ **拒绝进入生成，退回相位 B**」；
   - 处置 B（stale）：「身份不符（判 3）或 hash 不符（判 4）⇒ **呈现旧 memo 摘要**」+「**MUST NOT 静默复用**」；
   - 处置 C（undrafted）：「**退回 B 补定稿**，MUST NOT 按「身份不匹配」去问人复用与否」。
2. 面治扫全 19 格（下表），另发现**故障② 同型缺口** ⇒ 新增
   `test_fault2_branch_judgment_instruction_is_present`。
3. 文件头分级表：④ 行改注「四 fixture 真跑判 3/判 4 **+ C.1 四判与两条处置指令在场**」，
   ② 行改注「真跑 hook **+ B.1② 判定指令在场**」，⑤ 行改注「指令在场（三件事逐条）」。
4. 文件头「锚质量纪律」新增两条通用规则（**这才是面治的落点，不是逐条补丁**）：
   - **算法锚 MUST 配一条指令在场锚**，判据只有一句：「它守的那条处置，从 SKILL.md 里删掉，会红吗？」
   - 指令在场锚的 needle 要么**足够长**、要么**整句连读** —— 短 needle 会被文档别处的同词满足
     （恒真锚的第二种成因）。⑤/⑥ 各有一处 `fail-closed 中止`，正是这个坑，已按整段连读断。

### 逐格判定表（**19 格全过一遍**：「它守的那条处置，从 SKILL.md 删掉会红吗」）

| # | 用例 | 它守的处置写在哪 | 删掉那句会红吗 | 处置 |
|---|---|---|---|---|
| 1 | `test_fault1_dirty_worktree_halt_instruction_is_present` | SKILL.md B.1① | ✅ 会（本身就是在场锚） | 不动 |
| 2 | `test_fault1_design_failure_table_still_lists_it` | `design.md` 失败模式表 | ✅ 会（在场锚，打在 design 一侧） | 不动 |
| 3 | `test_fault2_deny_offers_exactly_the_three_documented_choices` | hook 的 deny 文案（**可执行 producer**） | ⚠️ **不会** —— 它断的是 hook 输出；B.1② 判定表删掉照样绿 | 🔧 **补** `test_fault2_branch_judgment_instruction_is_present` |
| 4 | `test_fault3_fallback_instruction_is_present` | SKILL.md B.1② fallback | ✅ 会（在场锚） | 不动 |
| 5 | `test_fault3_git_really_behaves_as_the_instruction_assumes` | 无（锚 **git 自身行为**） | ❌ 不会 —— **但它不自称守指令**，指令那半由 #4 承载 | 不动（同格已有在场锚） |
| 6 | `test_identity_keys_all_come_from_the_schema_doc` | `decision-memo-schema.md` §2 | ✅ 会（schema 文档改名即红，fix1 M④d 实测） | 不动 |
| 7 | `test_fault4_fixtureA_intact_memo_is_admitted` | SKILL.md C.1 判 1–4 | ❌ **不会** | 🔧 **补 #13** |
| 8 | `test_fault4_fixtureB_branch_mismatch_is_stale` | SKILL.md C.1 判 3 + stale 处置 | ❌ **不会** | 🔧 **补 #13** |
| 9 | `test_fault4_fixtureC_edited_after_finalize_is_stale` | SKILL.md C.1 判 4 + stale 处置 | ❌ **不会** | 🔧 **补 #13** |
| 10 | `test_fault4_fixtureD_missing_finalize_fields_is_undrafted_not_stale` | SKILL.md C.1 undrafted 段 | ❌ **不会** | 🔧 **补 #13** |
| 11 | `test_fault4_three_verdicts_are_distinguishable` | SKILL.md C.1 三态分流 | ❌ **不会** | 🔧 **补 #13** |
| 12 | `test_declared_field_set_includes_the_confused_deputy_field` | SKILL.md C.3 §2 字段集 | ✅ 会（字段名改错即红，fix1 M⑥a 实测） | 不动 |
| 13 | `test_fault6_real_cli_payload_carries_every_documented_field` | SKILL.md C.3 §2 字段集 | ✅ 会（同上；无 CLI 时 skip） | 不动 |
| 14–16 | `test_fault6_malformed_payload_fails_closed[×3]` | SKILL.md C.3 §2 字段集 | ✅ 会（`documented_required_fields` 从 C.3 §2 抠，删小节即 `assert head >= 0` 红） | 不动（docstring 另修，见 F-D） |
| 17 | `test_fault5_missing_cli_is_detected` | 无（锚 **PATH/exit code**） | ❌ 不会 —— 不自称守指令，指令那半由 #18 承载 | 不动（同格已有在场锚） |
| 18 | `test_fault5_preflight_instruction_is_present` | SKILL.md 0.1 | ⚠️ **半会** —— 只断了 3 件事里的 1 件（另两件 docstring 宣称却未断） | 🔧 **断满三件**（F-D 同型） |
| 19 | `test_fault6_no_retry_instruction_is_present` | SKILL.md C.3 §2 处置句 | ⚠️ **半会** —— 只断「MUST NOT 重试」 | 🔧 **整句连读断满**（F-D） |

> **归纳（面治结论）**：19 格里 **8 格无在场锚**。其中
> **5 格（#7–#11，故障④）是真缺口**——算法锚独撑，删指令不红；
> **1 格（#3，故障②）是真缺口**——hook 锚独撑，SKILL.md 自判那一跳删掉不红；
> **2 格（#5 / #17）不是缺口**——它们锚的是外部依赖行为（git / PATH），且**不自称**守指令，
> 同故障格里已有 #4 / #18 的在场锚。
> 另有 **2 格半（#18 / #19）** 是「宣称三件、只断一件」，与 F-D 同型，一并断满。

### 变异回验（判据「期望红 ⊆ 实际红」· 全部 worktree 副本）

| 变异 | 期望红 | 实测 |
|---|---|---|
| **M-A1** 删 C.1 判3/判4 处置首句（**复审 M-B 原样**） | `test_fault4_dispositions_are_present_in_the_skill` | ✅ `1 failed, 20 passed`，正是该用例（同一变异在 HEAD 旧 19 用例上 = `19 passed`） |
| M-A2 判 3「身份字段匹配当前盘面」改写 | 同上 | ✅ `1 failed, 20 passed` |
| M-A3 判 4 从「重算后匹配」降为「存在即可」 | 同上 | ✅ `1 failed, 20 passed` |
| M-A4 「任一不过 ⇒ 拒绝进入生成」改成「记一笔」 | 同上 | ✅ `1 failed, 20 passed` |
| M-A5 undrafted 分支并入「按身份不匹配处理」 | 同上 | ✅ `1 failed, 20 passed` |
| M-A6 删 B.1② 三分判定表「其它 feature 分支」那一行 | `test_fault2_branch_judgment_instruction_is_present` | ✅ `1 failed, 20 passed` |
| M-A7 B.1② 的「MUST NOT 沿用弱判据」反写 | 同上 | ✅ `1 failed, 20 passed` |

---

## F-B · `map_stage` tail 回退把短前缀误配到 `<step>` 段（Minor）

### 问题

fix1 的 F1 回退（整串无命中 ⇒ 拿剥掉命名空间的 `tail` 再试一次）**放宽了匹配面**，
而 `gate`(4) / `ff`(2) / `plan`(4) 这三条规则是**词**、不是**前缀**：

| 输入 | 修前 | 修后 |
|---|---|---|
| `checkpoint(c:gateway-refactor)` | spec-review ❌ | unknown ✅ |
| `checkpoint(c:ffmpeg-upgrade)` | ff ❌ | unknown ✅ |
| `checkpoint(c:planner)` | other ❌ | unknown ✅ |

归因静默出错（不报错、不缺文件）——**与本词表要治的病同型**。

### 修法

`sdflow-retro/scripts/retro_report.py`：新增 `_TAIL_STRICT_MAXLEN = 4` + `_prefix_hit()`，
回退这一跳（**且仅这一跳**）要求短前缀落在 token 边界上（全等或后接 `-`）：

```python
for candidate, token_boundary in ((inner, False), (tail, True)):
    for prefix, stage in ordered:
        if _prefix_hit(candidate, prefix, token_boundary=token_boundary):
            return stage
```

整串 `inner` 的匹配语义**一字未动**（change 名本身带阶段词的既有归类照旧，
`checkpoint(gateway-refactor)` 仍归 spec-review）——严格化只加在 fix1 新引入的那一跳上，
MUST NOT 顺手改既有语义。

### 真实历史核对（**不是只跑造的例子**）

对全仓 `git log --all` 的 **682 个 checkpoint** 逐条跑改前/改后：

```
old: {'impl': 366, 'spec-review': 141, 'code-review': 78, 'grill': 31, 'other': 27,
      'ff': 18, 'unknown': 19, 'done': 2}
new: {'impl': 366, 'spec-review': 141, 'code-review': 78, 'grill': 31, 'other': 27,
      'ff': 18, 'unknown': 19, 'done': 2}
changed: 0
```

⇒ **零条历史归类被改动**，`openspec/retro/report.md` 的数字不变（unknown 仍 18%）。
本条是**纯防御性收窄**，防的是目标态 producer 今后写出 `<change>:gateway-*` 这类 `<step>`。

### 变异回验

| 变异 | 期望红 | 实测 |
|---|---|---|
| M-B1 回退跳改回裸 `startswith`（`(tail, False)`） | `test_short_prefix_tail_fallback_requires_a_token_boundary` | ✅ `1 failed, 41 passed` |
| M-B2 `_TAIL_STRICT_MAXLEN = 0`（等价于不严格） | 同上 | ✅ `1 failed, 41 passed` |
| M-B3 边界判据只认全等（漏掉后接 `-`） | 同上 | ✅ `1 failed, 41 passed`（守住「收窄不能收过头」的另一侧） |

---

## F-C · slug 守卫期望集漏下发权威源（Minor）

### 面治扫描（`grep -rn "checkpoint-commit.sh"`，**不加 `--include`**）

全仓 tracked 命中 160+ 处，按「**会不会被照抄执行**」二分：

**producer（必须纳入期望集）**

| 文件 | 调用点 | 性质 |
|---|---|---|
| `sdflow-code-review/SKILL.md` ×2 · `sdflow-spec-review/SKILL.md` ×3 · `sdflow-spec/SKILL.md` ×2 · `sdflow-implement/SKILL.md` ×2 | 9 | 旧期望集已覆盖 |
| `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md` · `prompts/step6-writing-plans.md` · `workflow.md` | 3 | **下发给每个消费仓的权威源**（复审点名前两处） |
| `openspec/workflow/WORKFLOW-GUIDE.md` | 1 | 本仓已解析副本（`gen_workflow_guide` 刷新） |
| `sdflow-init/assets/hack/checkpoint-commit.sh` | 4 | 脚本 `--help` 样例（人照着敲）：`<step>` ×3 + `ff` + `spec-review` |

⇒ **17 处**，逐条经 `map_stage` 实测全部可归类（无 unknown）。

**非 producer（如实排除，理由写进文件头 docstring）**

- `docs/**` —— 讲这套工作流是怎么回事的散文/视图文档，没人从这里执行；
- `openspec/specs/**` · `openspec/adr/**` —— 规格与决策记录；
- `openspec/changes/**`（含 `archive/`）—— per-change 四件套与 `superpowers-plan.md`：
  **一次性、已执行完**，slug 早在 git 历史里定型，回头改词表也追不回来；
- 各 `tests/` —— 夹具字面量。

> 这是**合法的期望集边界**，不是漏网格：把它们纳入 = 让守卫去管一堆改不动的历史文本
> （与 fix1 F1 里「不给 `t<N>-` 补规则」同一条判据：MUST NOT 让机械层去追认改不动的存量）。

### 修法

`hack/tests/test_checkpoint_slug_coverage.py`：

- 抽出 `PRODUCER_GLOBS` 四条（含 `.md` 与 `.sh` 两种文件类型），`collect_slugs()` 按它遍历并去重；
- `MIN_CALLSITES` 9 → **17**（恒真锚下限随之抬高）；
- 新增 `test_producer_globs_cover_the_downstream_authority_bundle`：**逐个文件名**断言 bundle 权威源
  真的在抠到的集合里 —— 只抬 `MIN_CALLSITES` 挡不住「换一片 glob 凑够数」；
- 文件头 docstring 写清「期望集为什么是这四片，不是全仓」。

### 变异回验

| 变异 | 期望红 | 实测 |
|---|---|---|
| M-C1 bundle `WORKFLOW-GUIDE.md` 的 slug 改 `task<N>-` → `step<N>-` | `test_every_skill_slug_is_classifiable` | ✅ `1 failed, 2 passed` |
| M-C2 `PRODUCER_GLOBS` 缩回只 `*/SKILL.md`（**复现 F-C 原状**） | `…_finds_the_callsites` + `…_covers_the_downstream_authority_bundle` | ✅ `2 failed, 1 passed`，正是这两条 |
| M-C3 下发 prompt `step6-writing-plans.md` 的 slug 改 `phase<N>-` | `test_every_skill_slug_is_classifiable` | ✅ `1 failed, 2 passed` |
| M-C4 `checkpoint-commit.sh --help` 样例换成无规则 slug | 同上 | ✅ `1 failed, 2 passed` |

---

## F-D · docstring 宣称未断言的维度（Minor）

### 判据（基准 1：这两维有确定性信号吗？）

- **「零重试」** —— 「模型要不要再调一次 `openspec instructions`」是**模型行为**，
  无可信捕获路径（模型自报不算机械门）。**无信号。**
- **「零写入」** —— 同理：写盘发生在 C.3 §4，是模型在断言失败后**不该走到**的一步。
  在本用例里断「没写文件」只会断到本用例自己写的那一次 `subprocess.run` 上 —— **恒真锚**。

⇒ 采**选项 ①（删词 + 标弱锚）**，MUST NOT 硬造断言顶替。

### 修法

1. `test_fault6_malformed_payload_fails_closed` 的 docstring 改为
   「**全部 fail-closed（抛异常）+ 诊断带 `problem:` 三要素**」，并显式写明：
   「零重试 / 零写入」不在本用例断言里、无确定性信号、由 `test_fault6_no_retry_instruction_is_present`
   的**指令在场锚（弱）**承载。
2. **把那条弱锚断满**（原来只断「MUST NOT 重试同一调用」）：改为整句连读断
   `任一缺失或类型不符 ⇒ **fail-closed 中止**，报**实际 CLI 版本** + 修复命令，**MUST NOT 重试同一调用**`。
   整句连读而非三段散断的理由：`fail-closed 中止` 在 SKILL.md 出现两处（0.1 与 C.3 §2），
   拆开单断会被另一处满足 ⇒ 删掉它自称守的那句仍绿（**恒真锚的第二种成因**）。
3. **同型面治**：`test_fault5_preflight_instruction_is_present` 的 docstring 同样宣称三件事
   （fail-closed 中止 · 报实际版本 · MUST NOT 手工创建目录），实际只断了第三件 ⇒ **三件断满**，
   其中 fail-closed 那件用 `命令不存在或非零退出 ⇒ **fail-closed 中止**` 整段连读。
4. 文件头分级表 ⑤ 行改注「指令在场（三件事逐条）」，⑥ 行补「+ 处置句在场」。

### 变异回验

| 变异 | 期望红 | 实测 |
|---|---|---|
| M-D1 C.3 §2 处置句删掉「报**实际 CLI 版本**」 | `test_fault6_no_retry_instruction_is_present` | ✅ `1 failed, 20 passed` |
| M-D2 0.1 三要素删掉「实际版本」 | `test_fault5_preflight_instruction_is_present` | ✅ `1 failed, 20 passed` |
| M-D3 0.1 的「fail-closed 中止」弱化为「提示一下」 | 同上 | ✅ `1 failed, 20 passed` |

---

## 诚实边界（本轮新增/沿用）

1. **①③⑤ 的「处置正确」那一半仍是语义残余**（沿用 fix1）：模型收到脏工作树 / 分支撞名 /
   CLI 缺失时**真的 halt 了没**，无确定性信号。本轮补的全是「指令还在」这一半，
   **MUST NOT 被读成「处置正确会红」。**
2. **故障④ 的强锚现在是「算法 + 指令在场」两半**，但两半都**不证明模型真的跑了 C.1 四判**。
   覆盖图 4.5 那一格的真实状态仍是「②④⑥ 强 · ③⑤ 中 · ① 弱」，不是齐刷刷 ✅
   （`tasks.md` MUST NOT 改，差异留 archive 阶段一并订正，与 T232 同批）。
3. **F-B 是纯防御性收窄**：682 条真实历史 **0 条归类改变** ⇒ 它防的是目标态 producer
   今后写出的形态，**不是**当下已发生的错误归因。
4. **F-C 的期望集边界是划分、不是遗漏**：`docs/**` / `openspec/changes/**` 等非 producer 面
   明确排除，理由写在被守文件的 docstring 里（不在本报告里孤立存在）。
5. **`test_fault3_git_really_behaves_as_the_instruction_assumes` 仍无定点变异**（沿用 fix1）：
   它锚 git 自身行为，我无法在不改 git 的前提下变异它。

---

## 收尾（**全部亲跑，输出如实**）

```
$ git add -A && /usr/bin/python3 -m pytest -q          # 仓根全量
<见下>

$ bash setup.sh
$ python3 hack/sync_principles.py --check
$ python3 sdflow-retro/scripts/retro_report.py --root . # map_stage 动过 ⇒ 重跑再生，MUST NOT 手改
```

**实测输出**：

```
$ git add -A && /usr/bin/python3 -m pytest -q
2735 passed, 10 skipped, 3 xfailed in 278.86s (0:04:38)
```

- 相对 fix1 的 `2731 passed`，**+4**（F-A 的 2 条 + F-C 的 1 条 + F-B 的 1 条），零失败零 warning。
- 已知环境抖动用例
  `sdflow-init/tests/test_outside_voice_job.py::test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret`
  本轮**绿**。
- ⚠️ `git add -A` 在跑全量**之前**做过（`test_downstream_reference_guard.py` 扫 git tracked 文件，
  看不见未 add 的新报告 —— CLAUDE.md「tracked 守卫看不见未 add 文件」）。

```
$ bash setup.sh
  mode: symlink (Unix)
  [sync_principles]      ✅ 19 个投放面全部与真相源一致
  [gen_workflow_guide]   ✅ WORKFLOW-GUIDE.md 与单一源一致
  [async-branch-parity]  ✅ 2 处 async host 调度段逐字节一致
  exit=0

$ python3 hack/sync_principles.py --check
  [sync_principles] ✅ 19 个投放面全部与真相源一致   (exit 0)

$ python3 sdflow-retro/scripts/retro_report.py --root .
  [sdflow-retro] 复盘报告已再生 → openspec/retro/report.md
```

**再生结果与 F-B 的关系（如实）**：报告有 diff，但**与 `map_stage` 改动无关** ——
diff 全部落在实时墙钟上（`add-sdflow-spec` 这个 in-progress change 的墙钟 644.4 → 685.7 min，
连带总计 459.6 → 460.3 hr、unknown 占比 18% → 19%）。
`map_stage` 侧的证据是上面 F-B 那张 682 条真实历史对账表：**changed: 0**。
这正是 fix1 F7 登记的诚实边界（报告含实时量 ⇒ 永不字节可复现）在本轮的又一次实证。

> **dev/runtime checkout 纪律（adr/0005）**：`~/.claude/skills/*` 与 `~/.codex/skills/*` 的软链
> 在本票开始前**已经**指向本开发 checkout，本轮 `setup.sh` 只是幂等重跑。
> **合并后须在运行 checkout（`~/.skills/sdflow-skills`）重跑 `setup.sh` 还原。**

**变异纪律核验**：全部 17 处定点变异在 scratchpad 的 detached `git worktree` 副本里做，
收尾时该副本已 `git checkout -- .` 还原并跑绿（`66 passed`），主工作树 `git status` 无变异残留。

## 本轮改动清单

| 文件 | 性质 |
|---|---|
| `hack/tests/test_sdflow_spec_failure_modes.py` | F-A（+2 用例 + 分级表 + 锚质量纪律两条）· F-D（断满 ⑤⑥ + docstring 去虚报） |
| `hack/tests/test_checkpoint_slug_coverage.py` | F-C（`PRODUCER_GLOBS` 四片 + `MIN_CALLSITES` 17 + 新用例 + docstring 边界） |
| `sdflow-retro/scripts/retro_report.py` | F-B（`_TAIL_STRICT_MAXLEN` + `_prefix_hit`，仅作用于 tail 回退） |
| `sdflow-retro/scripts/tests/test_retro_report.py` | F-B 的新用例 |
| `openspec/retro/report.md` | 脚本再生（view-only 派生物；F-B 后数字不变） |
| 本文件 | fix 轮次 2 报告 |
