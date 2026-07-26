# Task 2 · fix 轮次 2 —— ACK 逃生口换机制（正则 → 一次性哨兵）+ 扫法期望集纠偏

**R-ID**：SA-05 · SA-11 · SA-14（承 `task2-canonical-sync-fix1.md`，**不覆盖前两轮报告**）
**基线 HEAD**：`463c35a`
**结论**：`DONE_WITH_CONCERNS`（两条待修全部落地；变异回验 18/18 MISS 0；全量绿。
一条 Minor 的预期与不变量冲突，按不变量处置并如实上报，见 §四 / C1）

---

## 零、总览

| 组 | 条目 | 处置 | 关键证据 |
|---|---|---|---|
| A | `:66` ACK 逃生口被行首注释绕过 | **换机制**：命令串正则 → 仓根一次性哨兵文件 | 变异 M1–M11 全红 |
| A-minor | `:67` `SDFLOW_FF0_ACK=1; …` 假阴 | 随机制更换整类消失（已实跑核对） | §一.4 探针表 |
| A-minor | `:113` 名为 `trunk` 的 feature 分支无逃生口 | **仍无逃生口**（与不变量冲突，不改）——如实上报 | §四 |
| B | `docs/sdflow-fable5/README.md:21` 只画旧三步 | 修 + 上机械守 | 变异 D1 → 红 |
| B | `docs/workflow-skills/grill-with-docs.md:18` 位置声明无条件成立即错 | 修（两处）+ 上机械守 | 变异 D6/D7 → 红 |
| B | 扫法期望集取错范畴 | 换判据重扫全仓，**又挖出 3 处**（overview ×2、map.md ×1） | §三 |
| C | 机制更换的下游载体（规则文本 / CONTEXT / ADR / 机械守） | 5 处同步 | 变异 M9/M10 → 红 |

**全量验证**（见 §六）：`/usr/bin/python3 -m pytest` → **2698 passed, 10 skipped, 3 xfailed**；
`bash setup.sh` 绿；`hack/sync_principles.py --check` ✅。

---

## 一、第 1 条 —— ACK 逃生口换机制

### 1. 复现（TDD 起手，先红）

在既有 `test_incidental_mention_of_the_ack_literal_is_not_an_ack` 里加入题面给的形态：

```
"# 人已 ack: SDFLOW_FF0_ACK=1\nopenspec new change add-foo"
```

```
$ /usr/bin/python3 -m pytest sdflow-init/tests/test_ff0_branch_guard.py -q
FAILED …::test_incidental_mention_of_the_ack_literal_is_not_an_ack
E  AssertionError: 口令只是被提及、并未作为 env 前缀传给命令，不该放行：# 人已 ack: SDFLOW_FF0_ACK=1
E    openspec new change add-foo
1 failed, 17 passed
```

成因：`ACK_RE` 的 `\s+` 吃换行 ⇒ 上一行注释里的口令与下一行的 `openspec …` 被拼成一个匹配。
即 docstring `:27` 自称已堵的「写进一句注释就绕过」原样存活，只从行尾挪到行首；`:65`
「只是在命令里被提及不算」当场为假。

### 2. 修法：零解析的一次性哨兵（按编排层拍板方向，未回去补正则）

| 维度 | 落点 |
|---|---|
| 哨兵路径 | 仓根下 `openspec/.ff0-ack`（常量 `ACK_FILE`；仓根由 `git rev-parse --show-toplevel` 解析，**不锚 cwd**——人可能在子目录里跑） |
| 语义 | `consume_ack()`：`os.remove` 成功 ⇒ 放行；**放行 ⇔ 成功删掉**（删不掉不放行，令牌不会残留成后门） |
| 生效面 | 只在分支③检查；分支① 的 `deny()` 在其**之前**且 `sys.exit`，哨兵既不被消费也不放行 |
| deny 文案 | 直接给出带**绝对路径**、可复制的整条命令 `touch <abs>/openspec/.ff0-ack && openspec new change <name>` |
| 罢工分支 | **0**（判据只有「文件在不在」，无任何语法解析） |

`ACK_RE` 及其 `SDFLOW_FF0_ACK` 字面量**已从 hook 中全部删除**；`hack/tests/` 新增一条机械守
断言 `"SDFLOW_FF0_ACK" not in hook`，防止它从后门复活。

### 3. 信任级别（已写进 docstring，MUST NOT 声称是安全边界）

哨兵与旧口令一样**分不出人和模型**——模型同样能 `touch`。它买到的只有两件：
① 把「顺手引用一次 deny 文案就绕过」变成**一次独立的、transcript 里可审计的有意动作**；
② 消灭了那个无界解析面。真正的防线是纪律 + review，不是本 hook。
`fail-open` 边界原样保留：管「探测不出上下文」，不管「人没拍板」。

### 4. 实跑探针（源版 hook，scratchpad 临时仓，`feat/add-bar` 上建 `add-foo`）

| 命令形态 | 判决 |
|---|---|
| 裸命令（无哨兵） | DENY |
| `SDFLOW_FF0_ACK=1; openspec new change add-foo`（Minor `:67` 旧假阴） | DENY |
| `SDFLOW_FF0_ACK=1 openspec new change add-foo`（旧机制的合法形态） | DENY |
| `# 人已 ack: SDFLOW_FF0_ACK=1\nopenspec new change add-foo`（**本轮待修**） | DENY |
| `openspec new change add-foo # touch openspec/.ff0-ack`（提到哨兵路径） | DENY |
| 人 `touch openspec/.ff0-ack` 后 | **ALLOW** |
| 同一哨兵第二次 | DENY（已被消费删除） |

> Minor `:67` 的假阴不是被单独修掉的，而是**整类消失**：命令串上不再有任何判据。

### 5. 僵尸用例清理

删除三条测已不存在机制的用例：`test_other_feature_branch_with_human_ack_allows`、
`test_ack_allows_when_preceded_by_other_shell_work`、`test_incidental_mention_of_the_ack_literal_is_not_an_ack`。
`test_default_branch_is_protected_even_with_human_ack` 改用哨兵重写，并**加强**为两条断言
（分支① deny **且哨兵仍在**——静默吃掉人的令牌会让下一次分支③的 ack 莫名失效）。
新增 5 条：`sentinel_allows_on_other_feature_branch` / `sentinel_is_one_shot` /
`sentinel_found_from_repo_subdirectory` / `undeletable_sentinel_does_not_allow` /
`mentioning_the_ack_in_the_command_string_is_not_an_ack`。用例数 18 → 20。

### 6. 机制更换的下游载体（canonical 单一源，逐处同步）

| 载体 | 改了什么 |
|---|---|
| `sdflow-init/assets/workflow/ff-generation-constraints.md:30` | hook 段改述哨兵逃生口 + 「判据只看文件在不在，**MUST NOT 从命令串里认口令**」 |
| `hack/tests/test_canonical_entry_sync.py` | `agree_on_the_escape_hatch` 改锚哨兵路径 + `ACK_FILE` 常量表达式；**新增** `test_ff0_escape_hatch_is_not_a_command_string_passphrase`（锚机制本身：两侧禁令 + hook 里不许再出现 `SDFLOW_FF0_ACK`） |
| `openspec/CONTEXT.md:108` | Stacking 条的「仍然可达」路径改为 `touch openspec/.ff0-ack` |
| `openspec/adr/0008` 正文 `:5` + 附录〔A-1〕`:32` | 同上（`:18`/`:36` 只说「ack 逃生口」，仍成立，未动） |
| `.gitignore` | 新增 `/openspec/.ff0-ack` + 一句说明 |

### 7. hook 重装到全局（执行契约第 4 条）

```
$ /usr/bin/python3 sdflow-init/scripts/init.py update --root .
  · ff0-branch-guard.py：脚本已更新 /Users/cheneyzhao/.claude/hooks/ff0-branch-guard.py；已注册（全局）
  - .gitignore runtime：已有（byte-noop）
$ diff ~/.claude/hooks/ff0-branch-guard.py sdflow-init/assets/hooks/ff0-branch-guard.py
  → 无差异
```

`init.py update` 照例把 `CLAUDE.md`/`AGENTS.md` 托管块刷成少一个空行的形态，跑
`hack/sync_principles.py --apply` 回填后两文件 `git status` **干净**（净 0 改动，块内未手改）。

---

## 二、第 2 条 —— 两处旧入口载体

| 位置 | 原文 | 改法 |
|---|---|---|
| `docs/sdflow-fable5/README.md:21` | 速览图节点 `G["生成<br/>explore→ff→grill"]` | 改为两分支节点（与同包 01/02 的 `S0`/`SP` 节点一致，消除包内自相矛盾） |
| `docs/workflow-skills/grill-with-docs.md:3, 18` | 文首「阶段一生成的人类对话岛（第 3 步）」+ §1「谁调它 \| 阶段一第 3 步」 | 两处都限定为**分支 B**，并明写分支 A 不经本 skill（拷问在 `/sdflow-spec` 相位 B，**前置于成文**） |

两份**均非生成物**（`grep -rl` 无任何脚本产出它们，已核）。两份**均已上机械守**（见 §三.3）。

---

## 三、根因 —— 扫法的期望集取错范畴

### 1. 旧扫法错在哪

上一轮按「当轮恰好 grep 到的字面」（`opsx:explore`）定义期望集，而非按「**会呈现阶段一流程的载体**」。
裸 `explore→ff→grill`（fable5/README）与纯位置声明（grill-with-docs，全文不含 `opsx:explore`）都逃出网外。

### 2. 新扫法（三层，逐层放宽，不加 `--include`）

```bash
# ① 流程串 + 位置声明
grep -rnE 'explore *(→|->) *ff|explore.*ff.*grill|阶段一第 *[0-9]+ *步|阶段一.*第.*步' .
# ② 任何提到阶段一三个旧入口的载体（最宽的一网）
grep -rn "opsx:ff\|grill-with-docs" .
# ③ 任何提到「阶段一」却不带分支词的行
grep -rn "阶段一" docs/ *.md sdflow-*/SKILL.md | grep -vE "分支 A|分支 B|sdflow-spec|入口二选一"
```

排除 `.git/` · `openspec/changes/archive/` · `openspec/changes/add-sdflow-spec/`。

### 3. 扫出的**全部**命中及处置

**改了（新增 3 处，评审未点名）**：

| 位置 | 问题 | 改法 |
|---|---|---|
| `docs/workflow-overview.md:62` | 「三阶段一句话画像」表把阶段一的自动化载体只写 `opsx:ff`、本性只写 grill | 两列都补两分支（分支 A `/sdflow-spec` 一次跑完 / 分支 B `opsx:ff`） |
| `docs/workflow-overview.md:247` | 「黑盒 skill」表 `opsx:ff \| 阶段一生成骨架` 无条件成立 | 加注〔**仅分支 B**；分支 A 由自制 `/sdflow-spec` 承担，非黑盒〕 |
| `docs/workflow-map.md:30` | ASCII 全景轨的人类门① 标为 `grill / 前提确认`，分支 A 无 grill | 改为 `拷问 / 前提确认` + 一行 `（A: 相位B · B: grill）` |

**新上机械守（`DOCS_CARRIERS` 4 → 8 份，逐处锚）**：

| 文档 | 锚（单行命中） |
|---|---|
| `docs/sdflow-fable5/README.md` | `("分支 A（默认）/sdflow-spec", "分支 B explore→ff→grill")` |
| `docs/sdflow-fable5/01-goals-and-rationale.md` | `("S0[", "分支 A · 默认")` · `("需求明确", "分支 A（默认）", "分支 B")` · `("生成 Spec", …)` |
| `docs/sdflow-fable5/02-module-reference.md` | `("SP[", "分支 A · 默认")` |
| `docs/workflow-skills/grill-with-docs.md` | `("人类对话岛", "分支 B 的第 3 步")` · `("谁调它", "分支 B", "分支 A 不经本 skill")` |

> **为什么推翻上一轮「fable5 是调研快照，不上守」的判断**：本轮的缺陷形态正是**包内自相矛盾**
> （01/02 改了、README 没改）。上一轮把该风险登记为 C4 未做，一轮之后它就实际发生了。
> 逐处锚 ~6 行成本，直接封住这个复发面（基准 3 面治）。**上一轮那条判断本身是错的，此处纠正。**

**查了但未改（逐处登记理由）**：

| 位置 | 为什么不改 |
|---|---|
| `docs/workflow-overview.md:29-30 / 100-107 / 111-128`、`docs/workflow-map.{md,html}` 阶段表、`docs/workflow-console.html` chips | 上一轮已改成两分支且已上机械守，本轮逐条复核成立 |
| `docs/sad/*.md`（6 处 `/opsx:explore`） | 文首「来源：… 探讨记录」出处标注（复审已抽查确认） |
| `sdflow-roadmap/SKILL.md:284/394` | roadmap **讨论层**三分支路由（判「讨论工具怎么选」），与 change 级入口是两个决策点（复审已抽查确认） |
| `docs/sdflow-context-policy.md:36/40/100/141` | 论证的是「阶段一的独立对抗方是**人**」——分支 A 的相位 B 同样是人类对抗，结论不受影响；grill 只是举例 |
| `docs/skill-authoring-best-practices.md:88`、`docs/workflow-skills/setup-matt-pocock-skills.md`、`docs/workflow-skills/matt-pocock-workflow.md` | 讲 grill 这个 skill 的性质/装配，不声称阶段一流程位置 |
| `hack/gen_workflow_guide.py:49`、`openspec/workflow/WORKFLOW-GUIDE.md` | 前者是 prompt 文件名映射表；后者是生成物（一致性由 `gen_workflow_guide --check` 守，且 `:18` 已有分支 A 默认入口段）。**未手改生成物** |
| `.claude/commands/opsx/*`、`.claude/skills/openspec-*`、`.codex/skills/openspec-*` | openspec CLI 生成物，`CLAUDE.md` 明令勿手改 |
| `docs/superpowers/plans/2026-07-01-*.md` | 带日期的历史 plan 归档，非流程载体 |
| `openspec/specs/spec-workflow/spec.md:970-1002`、`sdflow-spec/SKILL.md:10` | 已是分支感知的权威表述 |

---

## 四、Minor `:113` —— 与不变量冲突，**按不变量处置**（编排层预期未成立）

编排层预期「换成哨兵后它就有逃生口了」。**实测不成立，且不应成立**：

```
（全局 init.defaultBranch=trunk、无 origin/HEAD、当前在名为 trunk 的 feature 分支，且已 touch 哨兵）
DENY  FF-0 守卫：当前在受保护分支 `trunk`，禁止在此创建 OpenSpec 变更。
哨兵仍在: True
```

理由：分支① 的 `deny()` 在哨兵检查**之前**且不返回——这正是
`test_default_branch_is_protected_even_with_human_ack`（SA-05：保护分支必须先 `checkout -b`）
钉住的核心不变量。要让 `:113` 有逃生口，只能把哨兵检查前移到分支①之前，而那**等于给「在默认
分支上建 change」开后门**（变异 M4 实测：该不变量用例当场红）。
故维持现状：`:113` 仍无逃生口，自救 = `git checkout -b`（概率极低，deny 文案已直接给出该命令）。
附带确认一条好性质：分支① **不消费**哨兵，人的令牌不会被静默吃掉。

---

## 五、变异回验（18 条，**MISS 0**）

方法同上一轮：scratchpad 仓副本（`rsync` 排除 `.git`）跑 `mutate2.py`，逐条变异 → 跑
`test_canonical_entry_sync.py` + `test_ff0_branch_guard.py` → 记实际红集 → 还原。
**工作树全程未被变异触碰**。判据 = **期望红 ⊆ 实际红**。

| 变异 | 期望变红 | 实际变红 | 结果 |
|---|---|---|---|
| M1 哨兵只检测不消费（`os.remove`→`os.stat`） | sentinel_is_one_shot | +undeletable_sentinel | ✅ |
| M2 整个哨兵逃生口失效（分支③恒 deny） | sentinel_allows / is_one_shot / found_from_subdirectory | 同 | ✅ |
| M3 哨兵锚 cwd 而非仓根 | sentinel_found_from_repo_subdirectory | 同 | ✅ |
| M4 哨兵检查前移到分支①之前 | default_branch_is_protected_even_with_human_ack | 同 | ✅ |
| M5 删不掉也放行 | undeletable_sentinel_does_not_allow | 同 | ✅ |
| M6 **退回「从命令串里认口令」** | mentioning_…_is_not_an_ack + escape_hatch_is_not_a_command_string_passphrase | 同 | ✅ |
| M7 deny 文案删掉那条可复制的 touch 命令 | other_feature_branch_denies | 同 | ✅ |
| M8 hook 侧哨兵路径改名 | agree_on_the_escape_hatch + denies + sentinel_allows | +2 | ✅ |
| M9 规则文本侧哨兵路径改名（只改一侧） | agree_on_the_escape_hatch | 同 | ✅ |
| M10 规则文本删「MUST NOT 从命令串里认口令」 | escape_hatch_is_not_a_command_string_passphrase | 同 | ✅ |
| M11 hook docstring 删同一条禁令 | 同上 | 同 | ✅ |
| D1 fable5/README 速览图回退旧三步 | docs_stage_one_carriers | 同 | ✅ |
| D2 fable5/01 删 §2 图的 S0 节点 | 同 | 同 | ✅ |
| D3 fable5/01 §7「需求明确」行回退 | 同 | 同 | ✅ |
| D4 fable5/01 §7「生成 Spec」行回退 | 同 | 同 | ✅ |
| D5 fable5/02 删 §7 拓扑图 SP 节点 | 同 | 同 | ✅ |
| D6 grill-with-docs 文首回退成无条件「第 3 步」 | 同 | 同 | ✅ |
| D7 grill-with-docs §1「谁调它」回退成无条件定位 | 同 | 同 | ✅ |

原始输出留在 scratchpad `mutation-results-fix2.json`（不入库）。

---

## 六、全量验证

```
$ /usr/bin/python3 -m pytest -q
2698 passed, 10 skipped, 3 xfailed in 273.83s     （较基线 +3 用例）
$ bash setup.sh
  [sync_principles] ✅ 19 个投放面全部与真相源一致
  [gen_workflow_guide] ✅ WORKFLOW-GUIDE.md 与单一源一致
  [async-branch-parity] ✅ 2 处 async host 调度段逐字节一致
$ /usr/bin/python3 hack/sync_principles.py --check   → ✅
```

已知抖动用例 `test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret` **本轮通过**。

> 全量跑完之后我又改了一次 `docs/workflow-map.md`（把人类门①的分支注释挪到框线**外**，
> 原位置夹在框内破坏了 ASCII 框）。该行不在任何锚上，改后复跑
> `hack/tests/ + test_ff0_branch_guard.py` → **234 passed**。如实登记这个次序。

---

## 七、改动文件清单（`git diff` 亲验）

```
M .gitignore                                          （+/openspec/.ff0-ack）
M docs/sdflow-fable5/README.md
M docs/workflow-map.md
M docs/workflow-overview.md
M docs/workflow-skills/grill-with-docs.md
M hack/tests/test_canonical_entry_sync.py             （24 → 25 用例；DOCS_CARRIERS 4 → 8 份）
M openspec/CONTEXT.md
M openspec/adr/0008-gate-defense-in-depth-not-trust-discipline.md
M sdflow-init/assets/hooks/ff0-branch-guard.py
M sdflow-init/assets/workflow/ff-generation-constraints.md
M sdflow-init/tests/test_ff0_branch_guard.py          （18 → 20 用例）
```

`CLAUDE.md` / `AGENTS.md` 最终 `git status` 干净，托管块内部未手改。
`openspec/changes/add-sdflow-spec/` 的 proposal / design / specs / tasks.md / superpowers-plan.md **一字未动**。

---

## Concerns

### C1（须人知情）Minor `:113` 未修，且**不建议修**

见 §四。修它必须牺牲「ack MUST NOT 解锁保护分支」这条 SA-05 不变量。若人认为该场景值得
处理，正解不是给分支①开逃生口，而是**改进默认分支探测**（当前 `init.defaultBranch` 是次优
信号，承上一轮 C2），例如「仅当该名字确实是当前仓的某个 remote HEAD 才纳入受保护集」——
但那会削弱本地 `git init` 仓的保护，是范围决定，不是我该替人做的。

### C2 哨兵只进了**本仓** `.gitignore`，未进下游 canonical snippet

`sdflow-init/assets/snippets/runtime-gitignore.txt` 是消费仓 `.gitignore` 的真相源（ADR-0025），
而本 hook 是**全局**安装、拦所有项目 ⇒ 消费仓里 `.ff0-ack` 不被忽略。
**未加**，理由：① 题面明写「查**本仓** `.gitignore` 现状再决定加在哪」；② 本仓既有先例即如此
（`**/.outside-voice/` 同样由全局工具产出、也只在本仓 `.gitignore`）；③ 加它会改动 8 个
逐字节断言的 `test_runtime_gitignore.py` 用例并触碰 spec 锁定的 SW-RI-2。
残余风险很小：哨兵只在「人 touch」到「下一次 `openspec new change`」之间存在（用后即焚）。
若要补，一行 snippet + 改那批断言为「每条 canonical 条目恰一条 + 用户 bytes 保留」即可。

### C3 承 fix1 的 C1/C2/C3，全部仍然成立

默认分支探测让全局 hook 拦截面变宽（C1）；`init.defaultBranch` 是次优信号（C2）；
`tasks.md` 覆盖图仍标「人核 ❌」而实现已机械化（C3）——本轮又把 fable5 三份 + grill-with-docs
也机械化了，**未修改 `tasks.md`**（设计门产物），应在 `sdflow-done` 的 archive 阶段一并订正。
