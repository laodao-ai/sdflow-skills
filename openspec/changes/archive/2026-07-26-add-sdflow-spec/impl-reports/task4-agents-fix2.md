# Task 4 · fix 轮次 2（换方向：诚实声明门收窄到确定性信号 + 孤儿清理宽度自述订正）

> 前置：`task4-agents-step1.md` · `task4-agents-step2.md` · `task4-agents-fix1.md`。
> 本轮两条：**待修 1**（Important，编排层已拍板换方向）+ **待修 2**（Minor）。
> **未动** `proposal.md` / `design.md` / `specs/` / `tasks.md` / `superpowers-plan.md`。

## 0. 一览

| # | 落点 | 修法 | 变异回验 |
|---|---|---|---|
| 1 | `hack/tests/test_sdflow_spec_agents.py` + 两个 `agents/*.md` | 删掉句级分割判据；门收窄为「`tools` 字段精确匹配 + 一条**逐字 canonical** 诚实声明在场」；其余**如实降级为语义残余** | ①③⑤ / ② / ⑥ / ⑦ **RED**；④ 绿（折行不假红）；P2a/P2c/P2d/P5-append 绿（**诚实点**）；P5-replace **RED** |
| 2 | `setup.sh:185-201` + `hack/tests/test_install_agents.py` | 候选 ① **实测证伪**（会击穿孤儿清理主用途）⇒ 取候选 ②：如实改注记，并**把代价钉成两格用例** | M-2a/2b/2c/2d 各打**不同**一条断言（无恒真锚） |

---

## 1 · 换方向的理由（为什么不补第三批分割规则）

### 1.1 被否的方向

复审给的补丁是**第三批分割规则**（加 `.!?！？` 终止符 + 列表项边界 + 位置判定）。
它在当轮四个探针上绿——但没有任何理由相信下一轮不会有第五种形态。**MUST NOT 走这条。**

### 1.2 基准 5 警号

> **当你发现「每轮 review 都在同一个函数里补一个新的语法分支」，那不是"还差最后一个 case"，
> 那是"这个函数本来就不该存在"。**

`_sentences()` 的补丁史（可查，非推测）：

| 轮次 | 判据 | 当轮结局 |
|---|---|---|
| step2 | 整文件枚举**肯定式 needle** | fix1 的 Spec 轴实测：加一个「了」即绕过 |
| fix1 | 段内压空白 → 按 `。；` **切句** + 查否定标记 | 本轮复审实测：**四种真实措辞形态**当场绕过（P2a 无句号列表项 / P2c 英文句号 / P2d 换行无标点 / P5 拆列表项并反转） |
| （被否的下一轮） | 再加一批终止符 + 列表项边界 + 位置判定 | —— |

**连续两轮、同一个函数、各补一批分割规则**。警号成立。

### 1.3 根因（不是"分割规则还差一条"）

这个门在试图用**文本分析**判定「这份文档有没有做出虚假声称」。
「做出一个声称」在自然语言里的表达方式**无界**——它不像 CommonMark 的 fence 变体那样数得完。
∴ 按基准 5：**无界 ⇒ MUST NOT 手搓**，正解是「把门收窄到工具自己能回答的那部分」。

这里没有「让工具自己回答」的对应物（没有一个能判「这段话是不是声称」的权威工具），
∴ 走基准 1 的另一半：**能确定性保证的机械化，机械真够不着的残余如实退到语义规则。**

### 1.4 通则④ 五问

- **根因**：门的判定对象是自然语言语义面（无界），不是结构化字段。
- **概率**：绕过形态**已实测出现四种**——不是低概率，是**当轮 100%**。
- **影响**（三镜）：
  - **系统镜**：`_sentences()` 每轮膨胀，且它是**假绿源**——门在场却守不住，比没有门更贵
    （没有门时人知道要人读，有假门时人以为已经守住了）。
  - **用户镜**：无直接可感知行为（测试文件），但假绿会传导到「这个 change 的安全面已机械保证」
    这个错误结论上。
  - **开发循环镜**：每轮 review 都要在这个函数上耗一轮，且**永不收敛**。
- **完美成本**：要正确判「这段话是不是声称」需要 NLU；就算做了也没有确定性信号可锚。**成本无上限。**
- **简化方案**：收窄到**确定性信号**（`tools` 字段 + 逐字串），其余如实降级。
  代价 = 承认「别处说反话不会红」。**取此。**

**主次判定：以系统镜为主**——本条修的是「一道假绿的门」，而假绿是本仓 CLAUDE.md 与四条通则
反复点名的最贵失效模式；开发循环镜（不再无限补丁）是同向的次要收益。

---

## 2 · 采纳方案的落地

### 2.1 保留（机械、有界、确定性信号）

1. **`tools:` frontmatter 行的实际内容** —— 结构化字段的精确匹配：
   - `test_no_agent_def_uses_scoped_tool_syntax`（不许有括号，glob 扫全部定义）
   - `test_tool_faces_match_the_spec`（三个集合逐一相等）
   - `test_web_researcher_has_neither_repo_access_nor_bash`（缺席型）
2. **一条逐字 canonical 的诚实声明必须在场** —— 新增常量 `CANONICAL_DISCLAIMER`，
   守卫与两个持 `Bash` 的定义**同源**（守卫里是唯一权威副本，定义逐字带上，改动三处一起改）：

   ```
   本 agent 的工具面**不是机械边界**：`Bash` **非只读**，工具 allowlist 也管不到已授权工具的用法；上述限制**只由角色纪律约束，属指令层非机械门**。
   ```

   措辞来源 = **SA-12 S1**（`openspec/changes/add-sdflow-spec/specs/spec-authoring/spec.md:272`）的两条：
   「`Bash` 非只读 …… 只读性由角色纪律约束，**属指令层非机械门**」+「MUST NOT 声称『全只读』
   或『工具白名单挡住写权』」—— 合并成**一句对两个 `Bash` 持有者都字面成立**的话
   （原 SA-12 措辞「只读性由角色纪律约束」对 `spec-writer` 不字面成立：它本来就不是只读的，
   它的约束是「写入只限 change 目录」。∴ 用「工具面不是机械边界 / 上述限制只由角色纪律约束」
   这个对二者都真的表述，承重短语 **「属指令层非机械门」逐字保留**）。

   **`sdflow-web-researcher` 不带这句**：它 `tools: WebFetch, WebSearch`，**没有 `Bash`**，
   写「`Bash` 非只读」是假话。它那一面已由 `test_web_researcher_has_neither_repo_access_nor_bash`
   **完全机械覆盖**（工具集合缺席型断言），不需要诚实声明兜底。

   **唯一的文本规范化 = `_squash()`（压掉全部空白）**，因为中文正文硬折行位置随时会变
   （不压 ⇒ 假红，见变异 ④）。压空白是**确定性变换**，压完两边做**精确子串**比较——
   不是分割规则、不是启发式。`_squash()` 的 docstring 里已写明「MUST NOT 在这里长出按句切 /
   查否定标记那一类东西」。

3. **删除**：`_sentences()` · `_NEGATION` · `CLAIM_WORDS` · `test_no_definition_claims_to_be_fully_read_only`。

### 2.2 降级为语义残余（如实写进诚实边界，未硬造锚顶替）

「正文别处会不会用别的措辞说反话 / 把禁令翻成声称」——**无确定性信号，机械够不着**。
已写进 `test_sdflow_spec_agents.py` 模块 docstring 的
**【诚实边界 · 本文件明确不保证的】** 一节 + 本报告 §5。

### 2.3 `SKILL.md:291,302` 的三条 needle（A 的 catch-all 与 `[ -x ]` 预检）

按同法处理：**保留「删掉即红」这一维**（字符串在不在，有界），
**放弃「翻成声称也要红」这一维**（无界）。
`test_outbound_scan_prechecks_the_helper_and_has_a_catch_all` 的 docstring 已重写——
原文以「⭐ 出境扫描 MUST NOT fail-open」起手（读起来像行为保证），现改为
「**指令在场锚**：三句逐字还在」+ 明写「实测：给任一 needle 后面加『（已放宽）』，本用例全绿」
+ 「**MUST NOT 把本用例写成『出境面 MUST NOT fail-open』的证明**」。

`sdflow-spec/SKILL.md` **本轮零改动**（needle 与正文都不动，只改守卫的自述）。

### 2.4 `_S4_*` 三条正则：保留，只改自述（通则④）

fix1 的 docstring 写「判据必须钉住带 `MUST` / `拒写` 的那半句 —— **那是翻成声称时必然消失的部分**」
—— 这是**假绿的措辞形态**（复审已证伪同类主张），本轮删掉。

正则**本体保留**，五问：**根因** = 正则是为「已放弃的翻转维」造的；
**概率/影响** = 它作为在场锚工作正常（变异证实删掉即红），无失效风险；
**完美成本** = 改成朴素子串要先把 `SKILL.md` 与 `spec-writer.md` 两处措辞统一
（fix1 记录「两处措辞不同但都命中」），而 `SKILL.md` 已 590 行 / D12 上限 600、余量 10 行；
**简化方案** = 保留正则 + 把自述改到与实际能力一致（祈使形态 needle 堵的是**删除维**上的假绿——
「判据被删成一句背景介绍」时话题词仍全在——**不**堵翻转维）。⇒ 取简化方案。

---

## 3 · 全部 24 条用例的逐条判定表（面治）

判据：**这条用例守的是「有界信号」还是「语义」？** 有界 = 结构化字段 / 精确串 / 真跑代码；
语义 = 需要判断一段自然语言在主张什么。

| # | 用例 | 守的东西 | 判定 | 本轮处置 |
|---|---|---|---|---|
| 1 | `test_no_agent_def_uses_scoped_tool_syntax` | frontmatter `tools` 行有无 `()` | **有界**（结构化字段） | 不动 |
| 2 | `test_tool_faces_match_the_spec` | 三个工具集合相等 | **有界** | 不动 |
| 3 | `test_web_researcher_has_neither_repo_access_nor_bash` | 工具集合缺席 | **有界** | 不动 |
| 4 | `test_bash_holders_carry_the_canonical_honest_disclaimer` **（新）** | canonical 句逐字在场 | **有界**（精确串） | **新增**，替下旧的 #4/#5 |
| ~~4′~~ | ~~`test_no_definition_claims_to_be_fully_read_only`~~ | 「含 claim 词的句子必须自带否定标记」 | 🔴 **语义 · 无界** | **删除**（四形态实测可绕） |
| ~~5′~~ | ~~`test_bash_holders_carry_the_honest_non_mechanical_disclaimer`~~ | 「两 needle 落同一『句』」 | 🔴 **语义**（依赖切句） | **删除**，由 #4 接手 |
| 5 | `test_every_definition_has_an_exclusive_description` | frontmatter `description` 字段精确子串 | **有界**（字段边界由 `frontmatter()` 结构化取出） | docstring 补边界（不保证宿主真没选中） |
| 6 | `test_frontmatter_tiers_match_the_design` | `name`/`model`/`effort` 值相等 | **有界** | 不动 |
| 7 | `test_web_content_is_declared_non_executable_data` | 三条 needle 逐字在场 | **有界（在场维）· 语义（翻转维已放弃）** | docstring 明写「别处翻过来不会红」 |
| 8 | `test_second_source_requirement_for_design_affecting_conclusions` | 一条 needle 在场 | 同上 | docstring 补边界 |
| 9 | `test_secret_scan_rejects_a_query_carrying_a_key` | **真跑** `secret-scan` → exit 3 + 密钥不进流 | **有界**（行为，真跑） | 不动 |
| 10 | `test_secret_scan_passes_a_clean_query` | 真跑 → exit 0 | **有界**（行为） | 不动 |
| 11 | `test_unreadable_query_fails_closed` | 真跑 → exit 2 | **有界**（行为） | 不动 |
| 12 | `test_sdflow_spec_does_not_ship_a_second_scanner` | 四条规则片段全仓缺席 | **有界**（精确串缺席） | 不动 |
| 13 | `test_skill_routes_outbound_queries_through_the_shared_scanner` | 四条 needle 在场 | **有界（在场维）** | docstring 改：不保证「真先扫再发」、不保证没说反话 |
| 14 | `test_outbound_scan_prechecks_the_helper_and_has_a_catch_all` **（点名）** | 三条 needle 在场 | **有界（在场维）· 语义（翻转维已放弃）** | **docstring 重写**（见 §2.3） |
| 15 | `test_s4_accepts_the_legitimate_targets` | 纯函数放行 | **有界**（真跑） | 不动 |
| 16 | `test_s4_rejects_out_of_contract_targets`（5 参数化） | 纯函数拒绝**且拦它的是预期那道门** | **有界**（真跑） | 不动 |
| 17 | `test_s4_rejects_absolute_path_outside_the_repo` | 纯函数 | **有界** | 不动 |
| 18 | `test_s4_rejects_a_symlinked_target` | 纯函数 + 真 symlink | **有界** | 不动 |
| 19 | `test_s4_rejects_a_symlinked_ancestor` | 纯函数 + 真 symlink | **有界** | 不动 |
| 20 | `test_s4_disposition_is_written_in_the_skill_and_the_writer_def` | 三条祈使正则 + 两条话题词在场 | **有界（在场维）· 语义（翻转维已放弃）** | **docstring 重写**（见 §2.4） |
| 21 | `test_skill_dispatches_by_subagent_type_for_all_three_agents` | 三个 agent 名（**标识符**）+ 禁 `agentType` 在场 | **有界** | 补 docstring（不保证真派发用了它） |
| 22 | `test_skill_records_the_model_enum_measured_limit` | 实测事实的记录在场 | **有界（在场维）** | docstring 明写「不保证后文没说『已解除』；真防线是 fail-loud」 |
| 23 | `test_skill_degrades_to_doing_it_itself_not_to_a_generic_subagent` | 两条 needle 在场 | **有界（在场维）** | 补 docstring |
| 24 | `test_skill_documents_that_the_agent_roster_loads_at_session_start` | 运维事实的记录在场 | **有界（在场维）** | 补 docstring |

**汇总**：删 2 条（唯二的语义判据）· 新增 1 条（有界替代）· 改 docstring 10 条 · 其余 12 条不动。
**表里已无一条用例的自述超出它的实际能力。**

> fix1 表格里「15 / 17 部分可绕、按通则④不改」两条（= 本表 #22 / #24），
> 本轮**不再用「部分可绕」这种含糊措辞**：它们与 #7/#8/#13/#14/#20 是**同一类**——
> 在场维有界、翻转维无界。已统一按「在场锚」如实标注，不再单列例外。

---

## 4 · 变异实测（全部输出）

判据 **「期望红 ⊆ 实际红」**。变异一律在 scratchpad 的工作树副本
（`scratchpad/mut/`，`rsync -a --delete` 逐条还原）里做，**真实工作树零残留**。

### 4.1 编排层 MUST 跑的六条

```
### P2a 无句号 Markdown 列表项 + 同段 MUST NOT（追加）
    28 passed in 0.09s
### P2c 英文句号 + 同段 MUST NOT（追加）
    28 passed in 0.08s
### P2d 换行无标点 + 「不得」（追加）
    28 passed in 0.08s
### P5-append 诚实声明**保留**，另处加两个无句号反转列表项
    28 passed in 0.08s
### P5-replace 把诚实声明**改写**成两个反转列表项
    FAILED hack/tests/test_sdflow_spec_agents.py::test_bash_holders_carry_the_canonical_honest_disclaimer
    1 failed, 27 passed in 0.09s
### ① 删掉 canonical 诚实声明句
    FAILED hack/tests/test_sdflow_spec_agents.py::test_bash_holders_carry_the_canonical_honest_disclaimer
    1 failed, 27 passed in 0.09s
### ② tools: 行加上 Write
    FAILED hack/tests/test_sdflow_spec_agents.py::test_tool_faces_match_the_spec
    1 failed, 27 passed in 0.09s
```

**四条绕过形态为什么绿是诚实、不是退步**：

- 它们**追加**了与诚实声明矛盾的文字，而 canonical 句**仍逐字在场** ⇒
  门按其**声明的能力**（「规定的诚实声明在场」）判定为满足，**这就是正确结果**。
  门此刻的自述（模块 docstring + 用例 docstring）**明写**它不管这一维 ⇒
  绿**不构成假绿**：假绿 = 门声称守住了却没守住；这里门**没有声称**。
- 若为了让它们红而回去补分割规则，得到的是「当轮绿、下轮又被第五种形态绕过」的
  **循环补丁 + 一个依然自称防住了翻转的假绿门**——比现在贵得多。
- **P5 有两个读法，两个都跑了**：`P5-append`（保留 canonical 句、别处加反转列表项）⇒ 绿，
  属上述残余；`P5-replace`（把诚实声明**本身**改写成两个反转列表项）⇒ **RED**，
  因为 canonical 句被带走了 —— 这一格是新门相对旧门的**真实增益**
  （旧门在 P5 下是绿的，正是它 docstring 自称防住的形态）。

### 4.2 本轮新写/改写锚的定点变异（恒真锚排查）

```
### ③ canonical 句改一个字（`非只读`→`只读`）
    FAILED hack/tests/test_sdflow_spec_agents.py::test_bash_holders_carry_the_canonical_honest_disclaimer
    1 failed, 27 passed in 0.09s
### ④ canonical 句被硬折行（**预期绿** —— 压空白的意义）
    28 passed in 0.08s
### ⑤ 只删 writer 的 canonical 句（LOCAL 保留）
    FAILED hack/tests/test_sdflow_spec_agents.py::test_bash_holders_carry_the_canonical_honest_disclaimer
    1 failed, 27 passed in 0.09s
### ⑥ tools: 行加作用域括号
    FAILED hack/tests/test_sdflow_spec_agents.py::test_no_agent_def_uses_scoped_tool_syntax
    FAILED hack/tests/test_sdflow_spec_agents.py::test_tool_faces_match_the_spec
    2 failed, 26 passed in 0.10s
### ⑦ 删 SKILL.md 的 [-x] 预检 needle
    FAILED hack/tests/test_sdflow_spec_agents.py::test_outbound_scan_prechecks_the_helper_and_has_a_catch_all
    1 failed, 27 passed in 0.09s
### ⑧ 给 catch-all needle 追加「（已放宽）」——**翻转维，预期绿**
    28 passed in 0.08s
```

⑤ 证明门**逐个定义**判（不是「任一个带了就算」）；⑧ 是 §2.3 那条边界的**实测证据**，
它现在写在 #14 的 docstring 里。

### 4.3 待修 2 的四条（每条打**不同**一条断言 ⇒ 五格无恒真锚）

```
### M-2a 清理加「名字∈$src_dir」限定（候选①）
    >       assert not gone.is_symlink() and not gone.exists(), "悬空孤儿链没被清"
    1 failed in 0.47s
### M-2b 删掉整个路径形状守卫（=悬空就清）
    >       assert foreign_dangling.is_symlink(), "清了别人的悬空链 —— 守卫太宽"
    1 failed in 0.47s
### M-2c 形状收窄到 sdflow-* 前缀（定点：只打第 5 格）
    >       assert not shaped_dangling.exists() and not shaped_dangling.is_symlink(), \
    1 failed in 0.47s
### M-2d 删掉「有效链接留着」那行（定点：只打第 6 格）
    >       assert live_foreign.is_symlink() and live_foreign.is_file(), \
    1 failed in 0.48s
```

---

## 5 · 待修 2：孤儿清理宽度与自述不符

### 5.1 复审的观测成立

清理判据 `*/sdflow-spec/agents/*.md`（**任意名**）比接管判据 `*/sdflow-spec/agents/"$name"`
（`$name` 来自 `for f in "$src_dir"/*.md`，即**本仓现存的名**）在**名字维度更宽**。
fix1 报告自述「接管 + 孤儿清理**同宽**」**不准确**，本轮订正。

### 5.2 候选 ①（清理限定 `name` ∈ `$src_dir/*.md`）**实测证伪**

M-2a：加这条限定 ⇒ `test_dangling_link_of_a_deleted_source_is_cleaned` **当场红**
（`sdflow-gone-agent.md` 没被清）。

**根因**：**孤儿的定义就是「源已删」**——它的名字**必然**已不在 `$src_dir` 里。
候选 ① 会击穿孤儿清理的**主用途**：删掉一个 agent 定义后，它留下的悬空链将永远清不掉。
∴ 两条判据在名字维度**必然不同宽，这是设计不是疏忽**。

### 5.3 取候选 ②，并把代价钉成用例

`setup.sh:185-201` 的注记改写为三段（同宽的是**路径形状**；名字维度必然更宽 + 理由 + 实测；
**承认的代价**）。`hack/tests/test_install_agents.py` 的
`test_dangling_link_of_a_deleted_source_is_cleaned` 从三格扩到六格，新增：

- **第五格**（承认的代价）：`their-own-agent.md` → 指向 `<tmp>/someone-else-repo/sdflow-spec/agents/`
  的**悬空**链，MUST 被清。钉在这里是为了让这条边界**可见且是有意的**——
  日后想「收严」的人会先撞上第一格（收严即红）。
- **第六格**（边界另一侧）：同样路径形状但链**有效** ⇒ MUST 原样保留。

### 5.4 CLAUDE.md「绝不覆盖非本仓库拥有的同名目录」算不算被越界？

**不算。** 判据是「守的是什么」：那条纪律守的是**真实内容不被覆盖 / 丢失**。

| 形态 | 处置 | 是否触及该纪律 |
|---|---|---|
| 真实文件（第三方内容） | skip + `skipped[]` | ✅ 守住（既有用例 `test_a_foreign_file_is_never_clobbered_and_lands_in_skipped`） |
| **有效**的第三方软链（含本仓路径形状） | 原样保留 | ✅ 守住（**本轮新增第六格**，M-2d 证实非恒真） |
| **悬空**软链，且路径形状非本仓 | 原样保留 | ✅ 守住（第四格，M-2b 证实非恒真） |
| **悬空**软链，路径形状是本仓专有布局但名字非本仓 | 清掉 | ⚠️ **承认的代价**：目标已不存在 ⇒ **零数据丢失**，且 `sdflow-spec/agents/` 是本仓专有布局 |

按通则④：**概率**极低（第三方要同时采用本仓的 `sdflow-spec/agents/` 布局、软链进
`~/.claude/agents/`、且那条链已悬空）；**影响**为零数据丢失（只是一条已经坏掉的链消失）；
**完美成本**（识别链目标所属仓身份）要在**目标已不存在**的前提下判定归属——做不到；
**简化方案** = 承认代价 + 钉成用例 + 写进注记。⇒ 取之。

---

## 诚实边界

**本轮明确降级、未硬造锚顶替的项**（同表已写进 `test_sdflow_spec_agents.py` 模块 docstring）：

1. 🔴 **「正文别处会不会用别的措辞说反话」——无机械覆盖。**
   门保证的是**规定的诚实声明在场**（逐字）与 **`tools` 字段不越界**；
   **不保证**正文别处不会用其它措辞做出相反声称。实测证据：P2a / P2c / P2d / P5-append
   四种形态全绿；`SKILL.md` 的 needle 后加「（已放宽）」（变异 ⑧）也全绿。
   ⇒ 属**指令层**，由 `/sdflow-code-review` 与人读把关。
   **MUST NOT 在任何文档里把本文件描述成「防住了虚假声称 / 防住了措辞翻转」。**
2. **`SKILL.md:291,302` 三条 needle（A 的 catch-all 与 `[ -x ]` 预检）同上**：
   只保留「删掉即红」这一维（变异 ⑦ 实测），**放弃**「翻成声称也要红」。
   #14 的 docstring 已如实写明，并显式禁止把它写成「出境面 MUST NOT fail-open」的证明。
3. **`_S4_*` 三条正则同上**：堵的是**删除维**（判据被删成背景介绍时话题词仍在），
   **不**堵翻转维（在后面追加「由 CLI 保证，此处无须复查」⇒ 三条 needle 仍全在、用例全绿）。
4. **行为面一律无机械覆盖**（承 step2 §6.3/§6.4，本轮仍成立）：
   「子代理真的没写文件」（`Bash` 在手就没有机械边界）· 「主 session 真的先扫再发」·
   「模型真的没执行网页里的指令」· 「writer 真的调了 S4 那套判据」· 「真降级时走的是亲做路径」
   —— **均无确定性信号**。
5. **`test_skill_records_the_model_enum_measured_limit` / `..._roster_loads_at_session_start`
   的 needle 是事实陈述**：只保证没被删掉，不保证后文没有一句推翻它。
   #22 的真实防线是 fail-loud（填错当场被参数校验拒），不是本用例。
6. **`install_agents()` 的 Windows 分支仍无机械覆盖**（`IS_WINDOWS` 由 `uname -s` 决定、
   无环境变量覆盖入口，本机 Darwin 测不到）。同 step2 §6.6。
7. **孤儿清理的承认代价**（§5.4 表末行）：本仓路径形状 + 非本仓名字的**悬空**链会被清掉。
   零数据丢失，已钉成第五格用例使其**可见且有意**。
8. **`sdflow-web-researcher` 不带 canonical 诚实声明**是有意的（它没有 `Bash`），
   其工具面**完全**由集合断言机械覆盖 —— 这一条是**加强**不是缺口，登记于此以免下轮被当漏网。

---

## 6 · 门禁与全量

```
$ git add -A && /usr/bin/python3 -m pytest        # 仓根全量
2773 passed, 11 skipped, 3 xfailed in 274.64s (0:04:34)

$ bash setup.sh
    ✓ agents/sdflow-local-researcher.md @ /Users/cheneyzhao/.claude/agents
    ✓ agents/sdflow-spec-writer.md @ /Users/cheneyzhao/.claude/agents
    ✓ agents/sdflow-web-researcher.md @ /Users/cheneyzhao/.claude/agents
    ✓ workflow @ /Users/cheneyzhao/.sdflow   （+ hack/*.sh|md|py + capability-manifest.json）
  [sync_principles]      ✅ 22 个投放面全部与真相源一致
  [gen_workflow_guide]   ✅ WORKFLOW-GUIDE.md 与单一源一致
  [async-branch-parity]  ✅ 2 处 async host 调度段逐字节一致
  skipped / cleaned：均为空

$ /usr/bin/python3 hack/sync_principles.py --check
[sync_principles] ✅ 22 个投放面全部与真相源一致        # exit=0
```

**计数核对**：fix1 为 `2775 passed, 10 skipped`，本轮 `2773 passed, 11 skipped`。
逐项对得上，**无静默丢失**：

- **passed −2**：删 2 条（`test_no_definition_claims_to_be_fully_read_only` ·
  `test_bash_holders_carry_the_honest_non_mechanical_disclaimer`）+ 新增 1 条
  （`test_bash_holders_carry_the_canonical_honest_disclaimer`）= **净 −1**；
  另 **−1** 是下面那条转为 skip 的。
- **skipped +1**：`sdflow-init/tests/test_outside_voice_child_lifecycle.py:436`
  「15 次高频混合信号风暴本轮一次都没复现」——**自述复现率环境敏感**的用例，
  其 docstring 明写「MUST NOT 因为经常 skip 就删除它」。**与本轮改动无关**，如实登记。
- 已知抖动用例 `test_outside_voice_job.py::test_supervisor_transcript_…` 本轮**通过**。
- `test_install_agents.py` 前后各记一次 `ls -la ~/.claude/agents/`：三条软链的
  名字 / 指向 / 权限**逐字节一致**（只有目录 mtime 因 setup.sh 重建链而变），真实目录未被动坏。

`sdflow-spec/SKILL.md` 本轮**零改动**，仍 590 行（D12 上限 600）。

## 偏离与遗留

- **无偏离**。待修 1 按编排层拍板的方案实现（收窄 + 如实降级），**未补第三批分割规则**；
  待修 2 的两个候选按票面要求「自己判并给理由」，取 ②，理由是 ① **实测**会击穿孤儿清理主用途
  （可证伪，非偏好）。
- **未改动** `proposal.md` / `design.md` / `specs/` / `tasks.md` / `superpowers-plan.md`。
- **未改动** `sdflow-spec/SKILL.md`（本轮只改守卫的自述，不动被守的正文；行数仍 590 / 上限 600）。
- **复审已核验成立的三条本轮未动**：`checkpoint-commit.sh` 判 fail-visible ·
  `sync_principles.main` 的 `os.path.relpath` · C 的后缀判据会接管第三方路径。
