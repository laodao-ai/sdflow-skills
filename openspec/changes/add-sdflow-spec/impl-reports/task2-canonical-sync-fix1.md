# Task 2 · fix 轮次 1 —— hook 两个真 bug + 机械守补齐 + 残余分叉面清扫

**R-ID**：SA-05 · SA-11 · SA-14（承 `task2-canonical-sync.md`，**不覆盖首轮报告**）
**基线 HEAD**：`2ab6fd7`
**结论**：`DONE`（8 条待修全部落地；变异回验 53/53 无 MISS；全量绿）

---

## 零、总览

| 组 | 条目 | 处置 | 关键证据 |
|---|---|---|---|
| A | `:111` detached HEAD 落进分支③ | 修 + 1 用例 | 变异 A1 → 红 |
| A | `:31` 受保护集写死 `{main,master}` 致 ack 开后门 | 修（探测默认分支）+ 4 用例 | 变异 A2 / A2' / A2'' → 红 |
| A | `:47` ack 注释与实现分叉 | **改实现**（锚 env 前缀）+ 改注释 + 1 用例 | 变异 A3 → 红 |
| B | 人读侧 62 行零机械守 | 新增 5 条守（含逐字相等 + 同串） | 变异 B⑧a–j 十条 → 红 |
| B | `test_manual_residue_is_declared` 恒真锚 | **删用例**，残余移入模块 docstring | 见 §三.2 |
| B | `keeps_legacy_path_alive` 锚打偏 | 重锚 §四 明说那句 | 变异 B①f → 红；B①g 记录「仍不红」的合法残余 |
| B | 面治：全文件逐条变异 | 又挖出 1 条弱锚（`has_two_branches`）+ 2 条新锚自身弱点 | 见 §三.4 |
| C | `workflow-overview.md` / `workflow-map.html` 阶段一仍旧入口 | 修 + **面治扫出另 4 份载体** | 变异 B⑨a–i 九条 → 红 |
| C | `adr/0008` 正文实证句已成假事实 | 正文就地改写 + 演进史进附录〔A-1〕 | §五 |

**全量验证**：`/usr/bin/python3 -m pytest` → **2695 passed, 10 skipped, 3 xfailed**（270s，较基线 +12 用例）。
已知抖动用例 `test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret` **本轮通过**。
`bash setup.sh` 绿（`sync_principles ✅ 19 个投放面一致` / `gen_workflow_guide ✅` / `async-branch-parity ✅`）；
`hack/sync_principles.py --check` ✅。

---

## 一、A 组 —— `ff0-branch-guard.py` 三处

> ⚠️ blast radius：该 hook 装在 `~/.claude/hooks/`、注册于 `~/.claude/settings.json`，
> **拦本机所有项目**的 `openspec new change`。三处都按此严格度处理（TDD：先红后绿）。

### A1 `:111` detached HEAD 落进分支③ deny（fail-closed 回归）

- **成因**：`git rev-parse --abbrev-ref HEAD` 在 detached HEAD 下返回**字面量 `HEAD`**（实测：
  `git checkout --detach` 后输出 `HEAD`）。它非空、不在受保护集 ⇒ 落进分支③，提示
  「当前在 feature 分支 `HEAD`」——一个不存在的分支。worktree / bisect / tag checkout 全命中。
- **修法**：`current_branch()` 里 `return "" if branch == "HEAD" else branch`，并把
  `if not branch: sys.exit(0)` **前移到分支①判定之前**（原顺序里空串永远走不到那条 fail-open，
  是死代码）。
- **用例**：`test_detached_head_fails_open`。
- **变异回验**：去掉 `HEAD` 特判 → 该用例红。

### A2 `:31` `PROTECTED_BRANCHES` 写死两名，与规则文本分叉致 ack 开后门

- **规则文本**：`ff-generation-constraints.md:18` 明写受保护分支 =「main / master / **默认分支**」。
- **后果**：默认分支为 `trunk`/`develop` 的仓里，默认分支被**误分类成分支③**——而分支③**有** ack
  逃生口、分支①**没有** ⇒ `SDFLOW_FF0_ACK=1 openspec new change x` 在默认分支上被放行，
  FF-0 核心不变量被击穿。
- **修法（实测选型，非猜）**：新增 `default_branch(cwd)`，两个信号按可靠度降序——
  | 信号 | 本机实测 | 取舍 |
  |---|---|---|
  | `git symbolic-ref --short refs/remotes/origin/HEAD` | 本仓返回 `origin/main`；`git init` 的新仓无此 ref（rc≠0） | **首选**：`git clone` 时由 git 自己写入，是**这个仓**的远端认的默认分支 |
  | `git config --get init.defaultBranch` | 本机返回 `main`；**在 `git init` 出的临时仓里同样返回 `main`（继承全局配置）** | **次选**：严格说是「新建仓用什么名」，对本地 `git init` 的仓是好代理，对已有仓不等价 |
  两者都取不到 ⇒ 退回固定 `{main, master}`（fail-open 方向）。
  误判方向是「多保护一个分支名」，deny 文案会明确告诉人该敲 `git checkout -b`，代价可接受。
- **「ack 只对分支③生效」已结构性保证**：分支①的 `deny()` 在 ack 检查**之前**且不返回（`sys.exit`），
  无论 ack 如何都到不了分支③。用例 `test_default_branch_is_protected_even_with_human_ack` 钉住。
- **用例**：`test_default_branch_from_origin_head_is_protected`（`trunk` + 伪造 origin/HEAD）、
  `..._from_init_default_branch_config_is_protected`（`develop` + 本地 `init.defaultBranch`）、
  `..._is_protected_even_with_human_ack`、`test_feature_branch_still_denies_when_default_branch_is_unusual`（回归保护）。
- **变异回验**：A2（受保护集退回写死）→ 3 条红；A2'（只砍 origin/HEAD 信号）→ 2 条红；
  A2''（只砍 init.defaultBranch 信号）→ 1 条红。**两个信号各自被独立钉住，无一是装饰。**

### A3 `:47` 注释称「命令前缀带上它即放行」，实现是全串 `search`

- **实测复现**：旧实现下 `openspec new change add-foo # note: SDFLOW_FF0_ACK=1 was discussed` 即放行。
- **我选「改实现锚前缀」，不是「改注释」**。判据（题面给的那条：模型能不能自己把字面量抄进命令里就绕过）：
  - 两个选项都**不构成**安全边界——hook 无法区分「人敲的」和「模型敲的」，模型照样能写出正确的 env 前缀。
  - 但两者的**失效形态不同**：全串匹配下，绕过**不需要任何有意动作**——deny 文案本身就把
    `SDFLOW_FF0_ACK=1` 原样回传给模型，模型在解释「我为什么要建这个 change」时顺手引用一次即放行，
    **复现门槛为零、且没有任何一方做过决定**。锚前缀后，绕过至少是一次**有意的调用形态**，
    在 transcript 里可见、可审计。这正是「通则的『人』只指真人用户」那条的机械投影——
    守卫守不住意图，但**必须守住「有没有发生过一个决定」**。
  - 代价（三镜）：系统镜 = 正则从 1 行变 5 行，仍是**有界**形态识别（基准 5 未被违反，见下）；
    用户镜 = 人若敲成 `SDFLOW_FF0_ACK=1 && openspec …` 会被拒，但 deny 文案里就写着确切形态，可重敲；
    开发循环镜 = 零。**主次：用户镜那点摩擦远小于「零门槛静默绕过」的代价。**
- **基准 5 自检**：这不是解析 shell。它是**一个 bounded 形态的 allowlist**（口令作为 env 赋值前缀、
  其后可跟别的赋值、紧接被拦的那条 `openspec` 命令），认不出就落回分支③的正常 deny——
  **没有新增任何「语法不支持」的 fail-closed 罢工分支**。
- **fail-open 纪律边界（已写进 docstring）**：fail-open 管的是「**探测不出上下文**」（分支名 / change 名），
  不管「**人没拍板**」。认不出 ack ⇒ 就是没拍板 ⇒ deny 照常成立。
- **注释也一并改准**（两处：`:47` 常量注释 + 模块 docstring 新增一节说明为什么）。
- **用例**：`test_incidental_mention_of_the_ack_literal_is_not_an_ack`（三种「只是提及」形态：注释 / `echo` / `&&`），
  外加 `test_ack_allows_when_preceded_by_other_shell_work`（`cd . && SDFLOW_FF0_ACK=1 FOO=bar openspec …` 仍放行，防修过头）。
- **变异回验**：ACK_RE 整块换回 `re.compile(r"\bSDFLOW_FF0_ACK=1\b")` → 该用例红。

> **首轮踩坑记录（诚实登记）**：我第一次写这条变异时用 `#` 注释掉正则首行，
> 但 Python 隐式串拼接的**后续行仍然生效** ⇒ 正则没真回退、变异假绿。
> 是「实际红集合 ≠ 期望红集合」当场暴露的（它把两条 ack **放行**用例打红了，方向反了）。
> **教训：变异脚本本身也会写错，判据必须是「期望红集合 ⊆ 实际红集合」而不是「有没有红」。**

### hook 重装到全局（执行契约第 4 条）

`sdflow-init/scripts/init.py` 的 `HOOKS` 表（`:72-79`）声明 `ff0-branch-guard.py` 由
`ensure_global_hooks()` 幂等安装 —— 确认 `init.py update` 就是正确入口（读了源，非沿用上轮说法）。

```
$ /usr/bin/python3 sdflow-init/scripts/init.py update --root .
  · ff0-branch-guard.py：脚本已更新 /Users/cheneyzhao/.claude/hooks/ff0-branch-guard.py；已注册（全局）
$ diff ~/.claude/hooks/ff0-branch-guard.py sdflow-init/assets/hooks/ff0-branch-guard.py
  → 无差异
```

⚠️ `init.py update` 会把 `CLAUDE.md`/`AGENTS.md` 托管块刷新成**少一个空行**的形态，需再跑
`hack/sync_principles.py --apply` 才回到基线（两步是既有的成对机制，跑完 `git status` 里这两个文件
**无改动**、`--check` ✅）。两个托管块内部**未手改**。

---

## 二、B 组 —— 人读侧机械守（SA-14 + 基准 1）

**评审实测复现**：改动前删掉 `CLAUDE.md` + `AGENTS.md` 整节 ⇒ `pytest hack/tests/` 全绿。
本 change 的立项理由正是「人读侧与 AI 读侧分叉」，却在人读侧留下唯一无守的手抄面。

新增 5 条守（`hack/tests/test_canonical_entry_sync.py` §⑧）：

| 用例 | 守什么 |
|---|---|
| `test_entry_section_exists_in_both_human_carriers` | 两份文件里「阶段一入口」小节存在且非空 |
| `test_two_human_carriers_are_verbatim_identical` | 两份该节**逐字相等**（实测基线：2492 字节 × 2，49 行，完全一致） |
| `test_human_carriers_state_the_default_entry_and_the_model_ban` | 「默认走 `/sdflow-spec`」+「MUST NOT 默认拿 `opsx:ff` 起手」+ 模型侧禁令 |
| `test_human_carriers_state_the_sunset_thresholds_and_disposition` | 7 个**具体数字/处置**：`连续 6 个新开 change` · `8 周` · `5/6` · `0.79` · `75 min` · `删除 sdflow-spec` · `MUST NOT 无限期延长观察窗` |
| `test_human_side_and_canonical_use_the_same_wording` | 人读侧与 canonical（`generation-process.md` §四）**同串**：默认入口句、模型侧禁令、例外三情形整句 |

**为什么这一面用「压掉空白后比对」而不是单行锚**（已写进模块 docstring）：人读侧是**硬折行的中文散文**
（例外三情形那句在 `CLAUDE.md` 里跨两行），单行锚会随折行位置变化而假红/假绿。canonical bundle 那边
**仍然一律单行锚**（ASCII 图的空判据问题依旧成立），两套判据各有其适用面。

---

## 三、B 组 —— 全文件逐条变异（基准 3 面治）

### 1. 方法

在 scratchpad 的仓副本（`rsync` 排除 `.git`）上跑 `mutate.py`：逐个把「某条锚自称守的那句话」
改掉/删掉 → 跑 `test_canonical_entry_sync.py` + `test_ff0_branch_guard.py` → 记录实际变红集合 → 还原。
**工作树全程未被变异触碰**（`git status` 全程只含我的真实改动）。

判据 = **期望红集合 ⊆ 实际红集合**（不是「有没有红」——见 A3 那条踩坑）。

### 2. 恒真锚：`test_manual_residue_is_declared` —— 已删除

`assert MANUAL_ONLY.strip()` 断言的是**同文件里的模块级字面量**，参照系不含任何仓状态：
**无任何仓改动能使它红**。且它就坐在「MUST NOT 硬造恒真锚」的小节标题下，形式上自相矛盾。

**处置**：删用例 + 删常量，三条人核残余移入**模块 docstring** 的「人核残余」小节（原文保留），
并补一句为什么不需要测试背书。登记残余的载体是 docstring 与 git 审计，不是一条恒真的 assert。

### 3. 锚打偏：`keeps_legacy_path_alive` —— 已重锚

原锚 `opsx:explore` / `grill-with-docs` 两个裸词，被 §五 的 skill 选择表满足 ⇒ **删掉 §四 分支 B 整块仍绿**。
重锚到 §四内真正表达这件事的那句：`旧三步仍是合法路径` + `三个原入口未被删除`，
以及 `分支 B` + `grill 一律全深度` + `MUST NOT`。变异 B①f（删该行）→ **红**。

> **B①g 如实登记「仍不红」**：删掉 §四 分支 B 的 ASCII 块本身，本文件**不红**（期望如此）。
> 那是模块 docstring 已登记的人核残余之一（跨行结构无单行锚），**不是漏网**；
> 该块被删的实际后果由 B①b（删 `### 分支 B` 小节标题）与 B①f 覆盖。

### 4. 面治扫全文件时**新挖出**的三条（评审未点名）

| # | 用例 | 弱在哪（实测） | 修法 |
|---|---|---|---|
| a | `test_generation_process_has_two_branches` | 锚裸词「分支 A」+「sdflow-spec」，被 **§八 检查清单**那行满足 ⇒ 删掉 §四 整个分支 A 小节仍绿 | 改锚小节标题本身：`### 分支 A` + `已装` + `单入口`（B 同理） |
| b | 本轮新增的 `test_docs_stage_one_carriers_present_branch_a`（初版） | 只查「全文提过分支 A」⇒ 删 overview §2 分支 A 小节标题、删 map.html 入口行，**都仍绿** | 改成**逐处**锚（每份文档 2–4 个位置，见下表） |
| c | 同上（二版） | `("propose","/sdflow-spec")` 被阶段表行满足；`("chip","sdflow-spec")` 被 `sdflow-spec-review` 的**前缀**满足 | 分别改锚 `("──▶", …)` 与 `(">sdflow-spec<")` 带定界 |

> c 是「重命名共享字符串消费者」那类坑的近亲：**裸子串锚会被更长的同族名字满足**。

### 5. 变异回验全表（53 条，**MISS 0**）

| 变异 | 期望变红 | 实际变红 | 结果 |
|---|---|---|---|
| A1 hook 去掉 detached HEAD 特判 | detached_head_fails_open | 同 | ✅ 红 |
| A2 受保护集退回写死 {main,master} | default_branch ×3 | 同 | ✅ 红 |
| A2' 只砍 origin/HEAD 信号 | origin_head, even_with_human_ack | 同 | ✅ 红 |
| A2'' 只砍 init.defaultBranch 信号 | init_default_branch_config | 同 | ✅ 红 |
| A3 ACK_RE 整块退回全串匹配 | incidental_mention_…_is_not_an_ack | 同 | ✅ 红 |
| B①a 删 §四「### 分支 A」标题 | has_two_branches | 同 | ✅ 红 |
| B①b 删 §四「### 分支 B」标题 | has_two_branches | 同 | ✅ 红 |
| B①c 「默认走 `/sdflow-spec`」→「默认走 `opsx:ff`」 | states_entry_selection_rule, same_wording | 同 | ✅ 红 |
| B①d 「仅下列三种情形用旧三步」弱化 | states_entry_selection_rule | 同 | ✅ 红 |
| B①e 删「模型侧」禁令行 | states_entry_selection_rule | 同 | ✅ 红 |
| B①f 删「旧三步仍是合法路径」行 | keeps_legacy_path_alive | 同 | ✅ 红 |
| B①g 删 §四 分支 B 的 ASCII 块 | **（期望不红 —— 已登记人核残余）** | 无 | ✅ 符合 |
| B①h 改例外三情形措辞（canonical 侧） | same_wording | 同 | ✅ 红 |
| B②a 「全流程不用 `/clear`」改写 | g1_still_states_the_rule | 同 | ✅ 红 |
| B②b 删含「具名例外」的行 | g1_names_the_exception | + cites_two_reasons | ✅ 红 |
| B②c 删「cache 按模型隔离」 | cites_exactly_the_two_allowed_reasons | 同 | ✅ 红 |
| B②d 删「产 / 审错档」 | cites_exactly_the_two_allowed_reasons | 同 | ✅ 红 |
| B②e 删 workflow.md 冷视角禁令行 | forbids_the_cold_view_reason | 同 | ✅ 红 |
| B③a 「无 `/clear`（G1）」改写 | quality_layering_still_states_the_rule | 同 | ✅ 红 |
| B③b 删 QL 含「具名例外」的行 | names_the_same_exception | 同 | ✅ 红 |
| B③c 删 QL 冷视角禁令行 | forbids_the_cold_view_reason | 同 | ✅ 红 |
| B③d QL 检查清单去掉例外 | checklist_carries_the_exception, names_the_same_exception | 同 | ✅ 红 |
| B④a 「三分支判定」→「两分支判定」 | ff0_rule_is_three_way | 同 | ✅ 红 |
| B④b 「halt 问人」→「跳过」 | ff0_rule_is_three_way | 同 | ✅ 红 |
| B④c 删「MUST NOT 沿用…弱判据」 | ff0_rule_is_three_way | 同 | ✅ 红 |
| B④d 规则文本 ack 口令改名 | agree_on_the_escape_hatch | 同 | ✅ 红 |
| B④e hook 里 ack 口令全部改名 | agree_on_the_escape_hatch + 3 条行为用例 | 同 | ✅ 红 |
| B⑤a 「本条只管分支 B」→「一律适用」 | scopes_the_grill_clause_to_branch_b | 同 | ✅ 红 |
| B⑤b 归属改回 superpowers 插件 | attribution_is_fixed | 同 | ✅ 红 |
| B⑤c 删「阶段一入口二选一」 | carries_the_entry_selection_rule | 同 | ✅ 红 |
| B⑤d 删「FF-0 三分支判定」（claude-section） | carries_the_entry_selection_rule | 同 | ✅ 红 |
| B⑥a 「新旧入口共存与路由」→「入口说明」 | declares_coexistence_and_routing | 同 | ✅ 红 |
| B⑥b 删「分支 A（默认）」行（spec 侧） | declares_coexistence_and_routing | 同 | ✅ 红 |
| B⑦a 生成物阶段一段落改回旧入口 | generated_guide_reflects_the_new_entry | 同 | ✅ 红 |
| B⑧a **删掉 CLAUDE.md 整节**（改动前实测全绿） | 5 条人读侧守全部 | 同 | ✅ 红 |
| B⑧b 删掉 AGENTS.md 整节 | 5 条人读侧守全部 | 同 | ✅ 红 |
| B⑧c 只改 CLAUDE.md 一侧（两副本漂移） | verbatim_identical, sunset_thresholds | 同 | ✅ 红 |
| B⑧d 两侧一起改默认入口 | default_entry_and_the_model_ban, same_wording | 同 | ✅ 红 |
| B⑧e 两侧一起去掉模型侧禁令 | default_entry_and_the_model_ban | 同 | ✅ 红 |
| B⑧f 两侧一起抹掉采用率阈值 5/6 | sunset_thresholds_and_disposition | 同 | ✅ 红 |
| B⑧g 两侧一起把处置软化（删除→再评估） | sunset_thresholds_and_disposition | 同 | ✅ 红 |
| B⑧h 两侧一起删「MUST NOT 无限期延长观察窗」 | sunset_thresholds_and_disposition | 同 | ✅ 红 |
| B⑧i 两侧一起改例外三情形（与 canonical 分叉） | same_wording | 同 | ✅ 红 |
| B⑧j 两侧一起抹掉成本阈值 75 min | sunset_thresholds_and_disposition | 同 | ✅ 红 |
| B⑨a overview 删 §2 分支 A 小节标题 | docs_stage_one_carriers | 同 | ✅ 红 |
| B⑨f overview 只删 §0 全局图分支 A 节点 | docs_stage_one_carriers | 同 | ✅ 红 |
| B⑨g overview 只删 §7 自检清单那条 | docs_stage_one_carriers | 同 | ✅ 红 |
| B⑨b map.md 阶段表回退旧入口 | docs_stage_one_carriers | 同 | ✅ 红 |
| B⑨h map.md 只回退 ASCII 轨 | docs_stage_one_carriers | 同 | ✅ 红 |
| B⑨c map.html 删 STAGE 1 入口行 | docs_stage_one_carriers | 同 | ✅ 红 |
| B⑨e map.html 只回退 stage-skill 行 | docs_stage_one_carriers | 同 | ✅ 红 |
| B⑨d console.html 回退 role 文案 | docs_stage_one_carriers | 同 | ✅ 红 |
| B⑨i console.html 只删 chips 里的 sdflow-spec | docs_stage_one_carriers | 同 | ✅ 红 |

**总计 53 条，MISS 0。** 原始输出留在 scratchpad `mutation-results.json`（不入库）。

---

## 四、C 组 · 残余分叉面 —— 面治扫全仓

### 扫法

`grep -rn "opsx:explore"`（**不加 `--include`**，排除 `.git` / `archive/` / 本 change 四件套），
逐条判「这是不是**呈现阶段一流程**的人读载体」。

### 改了的（6 处，评审只点名前 2）

| 文档 | 改了什么 |
|---|---|
| `docs/workflow-overview.md` **（点名）** | §0 全局流程图加分支 A 节点并纳入「阶段一」subgraph；§2 阶段一段落**拆成分支 A / 分支 B 两个小节**（分支 A 加步骤 0 表 + 出口序列；分支 B 标注三种例外 + 全深度 grill）；§7 自检清单首条改为「装了 `sdflow-spec` 吗」，其余两条标〔分支 B〕 |
| `docs/workflow-map.html` **（点名）** | STAGE 1 的 `stage-skill` 加 `/sdflow-spec（分支 A · 默认）`；新增一整行「入口」说明两分支 + 指向 `generation-process.md` §四 |
| `docs/workflow-map.md` **（面治新增）** | 它自称是 `workflow-map.html` 的 **markdown 对应版（可 diff / tracked）**——只改 html 不改它就是新分叉。ASCII 全景轨与阶段表同步两分支 |
| `docs/workflow-console.html` **（面治新增）** | 「阶段一 · 生成」卡片的 role 文案 + chips 补 `sdflow-spec`（它是 overview 的视觉精简版，同一内容面） |
| `docs/sdflow-fable5/01-goals-and-rationale.md` **（面治新增）** | §2 全局形态图加分支 A 节点；§7「目标 vs 现状对照」两行改为「分支 A（默认）… / 分支 B …」（该表是**现状**声明） |
| `docs/sdflow-fable5/02-module-reference.md` **（面治新增）** | §7 端到端调用拓扑图加分支 A 节点 |

前 4 份**已上机械守**（`test_docs_stage_one_carriers_present_branch_a`，逐处锚，9 条变异全红）。

### 查了但**未改**的（如实登记 + 理由）

| 位置 | 为什么不改 |
|---|---|
| `docs/sad/*.md`（6 处 `/opsx:explore`） | 全是文首「来源：2026-07-12 `/opsx:explore` 探讨记录」的**出处标注**，不呈现阶段一流程 |
| `sdflow-roadmap/SKILL.md:289`「分支 A（默认）：`/opsx:explore`」 | 它是 **roadmap 讨论层**的三分支路由（explore vs wayfinder chart，判「讨论工具怎么选」），不是 change 级阶段一入口；与「四入口选择规则」是两个决策点。**同名不同物**，改它反而制造新混淆 |
| `.claude/commands/opsx/*`、`.claude/skills/openspec-*`、`.codex/skills/openspec-*` | openspec CLI 生成物，`CLAUDE.md` 明令「非本仓库维护的源，勿在此手改」 |
| `README.md:28` | 已同时呈现两分支（首轮已改） |
| `docs/sdflow-fable5/02-module-reference.md` 的 `RM -.每阶段.-> FF` 边 | roadmap 每阶段落成的 change 现在默认走分支 A，该边严格说也该改；但它是 2026-07-10 的**调研快照**，同图已加分支 A 节点足以不误导。按通则④ 不为这个边角再动刀（**登记，未做**） |
| `docs/sdflow-fable5/*` 未上机械守 | 它是**带日期的调研文档集**（非流程真相源、非 wayfinding 入口）；给快照类文档上门禁属加宽，未做 |

---

## 五、C 组 · `adr/0008` 正文实证句（DOC-1）

**问题**：标题与正文首段的「关键实证：FF-0 只拦 main/master，不拦 feature 分支上 stacking」已不是当前行为，
更正却挂在文末。按 DOC-1 判据①「只有读过上一版的人才需要的句子，不属于正文」：新读者按顺序读到的是
**当前已错的断言**，得读到文末才知作废。对照 `openspec/CONTEXT.md` 的 Stacking 条是**就地改写**的——
同一事实两处处置不一致。

**处置**：

1. **标题**：`…即便 FF-0 不拦 stacking 也有价值` → `…即便有入口守卫也有价值`（去掉已失效的事实断言，
   保留承重主张）。
2. **正文首段就地改写为三分支现状**：明写「入口守卫拦不住 stacking 的**全部路径**」，
   并列出仍可达的四条（ack / 取不到 change 名 / detached HEAD fail-open / 非 Bash 入口与手工 `git`）。
   **ADR 的承重论证「守卫仍可绕过 ⇒ 隔离仍必要」原样保留并加粗成 MUST NOT**，未随演进史搬走。
3. **演进叙事移入 `## 附录`〔A-1〕**：立案时的旧实证、`add-sdflow-spec` 的升级、两条否决理由为何各自仍成立。
   正文只留 `〔A-1〕` 编号（DOC-1「正文 →〔A-n〕只给编号，不解释」）。
4. `Considered Options` 里那条被否决的选项**保留原文**（它记录的是当时的决策，是 ADR 的合法附录内容），
   只加一句括注指向〔A-1〕，避免读者以为该选项与现状矛盾。

---

## 六、改动文件清单（`git diff` 亲验）

```
M AGENTS.md                                          （init.py update + sync_principles 往返，净 0 改动）
M CLAUDE.md                                          （同上，净 0 改动）
M docs/sdflow-fable5/01-goals-and-rationale.md
M docs/sdflow-fable5/02-module-reference.md
M docs/workflow-console.html
M docs/workflow-map.html
M docs/workflow-map.md
M docs/workflow-overview.md
M hack/tests/test_canonical_entry_sync.py            （19 → 24 用例）
M openspec/adr/0008-gate-defense-in-depth-not-trust-discipline.md
M sdflow-init/assets/hooks/ff0-branch-guard.py
M sdflow-init/tests/test_ff0_branch_guard.py         （11 → 18 用例）
```

`CLAUDE.md` / `AGENTS.md` 最终 `git status` 干净（托管块往返后回到基线），**块内部未手改**。
`openspec/changes/add-sdflow-spec/` 的 proposal / design / specs / tasks.md / superpowers-plan.md **一字未动**。

---

## Concerns

### C1（承首轮 C1，**范围扩大，需人知情**）默认分支探测让全局 hook 的拦截面变宽

本轮把受保护集从写死的 `{main, master}` 改为「∪ 探测到的默认分支」。⇒ **本机所有项目**里，
默认分支为 `trunk`/`develop`/其它名字的仓，从现在起也会在其默认分支上被 deny（且**无 ack 逃生口**）。
这是 `ff-generation-constraints.md:18` 规则文本一直写着的语义（「main / master / **默认分支**」），
本轮只是让实现追上规则；但生效面确实变宽了。
误判方向是「多保护一个分支名」，deny 文案会告诉人敲 `git checkout -b`，可自救。
回退 = `git checkout` 该 asset 后重跑 `init.py update`。

### C2 `init.defaultBranch` 是**次优信号**，诚实边界

它是「新建仓用什么名」，本机实测在 `git init` 出的临时仓里返回的是**全局配置值**，与该仓实际默认分支
不等价。选它是因为本地 `git init` 的仓根本没有 `origin/HEAD`，而那正是「默认分支不叫 main」最常见的场景。
两个信号都取不到时退回 `{main, master}`（fail-open 方向）。这条残余**无更好的确定性信号**——
git 本身不为无远端的仓记录「默认分支」这个概念。

### C3 首轮 C4 仍然成立且本轮又扩大了一档

`tasks.md` 的测试覆盖图把若干处标为「人核 ❌」，实现里已机械化；本轮又把**人读侧（CLAUDE.md/AGENTS.md）
与 docs/ 四份载体**也机械化了。**未修改 `tasks.md`**（设计门产物，实现期不得改）——
应在 `sdflow-done` 的 archive 阶段一并订正覆盖图。

### C4 `docs/sdflow-fable5/` 两份未上机械守

理由见 §四表末。若日后认为调研快照也该守，加两条锚即可（成本 ~4 行），但那是范围决定，不是我该替人做的。
