# Task 4 · fix 轮次 1（双轴审 4 Important + 4 Minor 全修）

> 前置：`task4-agents-step1.md`（探针最小面）+ `task4-agents-step2.md`（GO 之后的完整交付）。
> 本轮只修双轴审点出的缺口与其同片面，**未动 proposal / design / specs / tasks / superpowers-plan**。

## 0. 一览

| # | 严重度 | 落点 | 修法 | 变异回验 |
|---|---|---|---|---|
| A | Important | `sdflow-spec/SKILL.md` 出境扫描段 | `[ -x ]` 预检 + 「非 0 一律拒发」catch-all | M-A1 / M-A2 **RED** |
| B | Important | `hack/tests/test_sdflow_spec_agents.py` | 诚实声明门改**句级**判据；面治扫全部在场型用例，另修 S4 处置锚 | M-B1…M-B4 **RED**，M-B1′/M-B4′ 反向对照**绿** |
| C | Important | `setup.sh install_agents()` | 自属判据改**位置无关路径后缀**（接管 + 孤儿清理同宽） | M-C1 / M-C2 / M-C3 **RED** |
| D | Important | `hack/tests/test_sync_principles.py` | 探针移出真实工作树（`tmp_path` + monkeypatch），另立静态断言 | M-D1 / M-D2 **RED**；并行 6 路：旧版 5 红 / 新版 4 绿 |
| E | Minor | `SKILL.md:460` | 「具体 id」→「字面值（枚举边界见外派协议）」 | 全文 `grep` 该措辞族已归零 |
| F | Minor | `SKILL.md:276` | 内联模型 id → 占位形态 | 同上 |
| G | Minor | `setup.sh:132` | `mkdir` 失败降级为 `skipped[]`，不中止全脚本 | M-G1 **RED**（回退后 rc=1、裸 `mkdir:` 错误） |
| H | Minor | `test_sdflow_spec_agents.py:85` | 删考古层，只留最终事实 | — |

判据一律 **「期望红 ⊆ 实际红」**：下文每条都贴了实际失败的用例名。
所有变异在 **scratchpad 的工作树副本**（`scratchpad/mut/`）里做，逐条改 → 跑 → `rsync --delete` 还原，
**真实工作树零残留**（`git status --porcelain` 全程只有本轮 6 个文件的 ` M`）。

---

## A · 出境 secret scan 的 fail-open 面

### 病灶

原文只枚举 `exit 0|3|2`，**无 `[ -x ]` 预检、无 catch-all**。
`~/.sdflow/hack/` 是 **copy 而非 symlink**（`setup.sh` 每次重拷）⇒ pull 与 setup 之间的 skew 窗口里
调用**实测 exit 127**，落在枚举之外 ⇒ 模型可能把「不是 3」读成「没命中」而**放行一条从未被扫描过的
出境查询**。这是 BASE-28 S2「命中即拒发且禁 fallback」的直接击穿面。
同仓 `sdflow-code-review/SKILL.md:362`、`sdflow-spec-review/SKILL.md:362` 均有 `[ -x "$HELPER" ]` 预检 +
fail-loud，本文件 0.2(b)（`resolve-models.sh`）也有 —— 此处缺失属**回退**。

### 修法

`sdflow-spec/SKILL.md` 出境扫描节：

- 调用前加 **`[ -x ~/.sdflow/hack/outside-voice.sh ]` 预检**，不成立 ⇒ 拒发并 fail-loud（同 0.2(b) idiom）；
- `exit 0` 一条补「**只有这一个码是「扫过了且干净」**」；
- 新增 catch-all：**「其余任何非 0 退出码一律拒发」**（点名 `127` 是 skew 窗口高发码）+
  **「MUST NOT 把「不是 3」读成「没命中」」**。

新用例 `test_outbound_scan_prechecks_the_helper_and_has_a_catch_all` 钉住这三句。

### 面治：SKILL.md 里其它外部 helper 调用点

`grep -n '\.sdflow/hack\|resolve-workflow\|resolve-models\|checkpoint-commit\|outside-voice' sdflow-spec/SKILL.md`
逐个过：

| 调用点 | 预检 | 非 0 处置 | 判定 |
|---|---|---|---|
| `resolve-models.sh`（0.2 b/c/d） | ✅ `[ -x ]` | ✅ 「非 0 → fail-loud 硬停并原样转发 stderr」+ eval 后枚举/非空校验 | 已合规，不动 |
| `outside-voice.sh secret-scan`（外派协议） | ❌ → ✅ 本轮补 | ❌ → ✅ 本轮补 | **本条即 A** |
| `checkpoint-commit.sh`（B.7 ⑤ / 终审后） | ❌ | ❌ | **不补，判为不同类**（见下） |
| `resolve-workflow.sh` | 本 SKILL **不调用**（`grep` 零命中） | — | 不适用 |

**为什么 `checkpoint-commit.sh` 不补**（按通则④五问，写在这里以免下轮再问一次）：
根因同族（helper 是 copy、有 skew 窗口），但**影响不同类** —— 它失败的后果是**commit 没打出来**，
下一步 `git log` / `git status` 立刻可见，属**可观测失败**；
而 secret-scan 失败的后果是**一条未扫描的查询被发出去**，属**静默放行**，且不可逆。
A 补的是 fail-**open**，checkpoint 是 fail-**visible**。完美成本（给每个 helper 调用点加预检）会把
SKILL.md 推向 D12 的 600 行上限而收益接近零。∴ 按通则④判为可接受边角，**如实登记不做**。

### 变异回验

| # | 变异 | 结果 |
|---|---|---|
| M-A1 | 删掉 `[ -x ~/.sdflow/hack/outside-voice.sh ]` 预检那两行 | **RED** `test_outbound_scan_prechecks_the_helper_and_has_a_catch_all`（`test_sdflow_spec_agents.py:284`） |
| M-A2 | 删掉 catch-all 那条（保留 0/3/2 三条） | **RED** 同一用例（`:286`） |

---

## B · 诚实声明门 needle 过窄，实测可绕

### 病灶

`test_no_definition_claims_to_be_fully_read_only` 原本整文件 squash 后找**肯定式 needle**
（`是全只读` / `全只读的` / `白名单挡住写权` / `白名单挡得住`）。
Spec 轴实测：追加「本 agent 的工具面全只读，工具白名单挡住**了**写权。」→ **仍绿**。
`白名单挡住了写权` 比枚举多一个「了」，而这正是定义自身**禁令句**的措辞
（`sdflow-local-researcher.md:213`：`MUST NOT 对外声称「全只读」或「工具白名单挡住了写权」`）——
**把那句从禁令翻成声称，门不会红** ⇒ 守不住 BASE-28 S1。

根因：**肯定式写法是无界的，枚举必然漏**（同 CLAUDE.md 基准 5 的形状：无界面上补丁循环不收敛）。

### 修法：判据反过来问

新增 `_sentences()`：**先按空行切段、段内压掉全部空白，再按 `。；` 切句**。
判据 = **含 `全只读` / `白名单挡` 的句子 MUST 自带否定标记**（`MUST NOT` / `不得` / `不许` / `并非` / `别声称`）。

- **为什么先段内压空白**：中文正文硬折行位置随时会变，纯行级 needle 被折断后**一条都不会红**
  （是假绿，不是假红）——压空白后 needle 折不断。
- **为什么还要切句**：整段/整文件判定分不清「禁止这么说」和「就这么说了」，
  禁令句与声称句必须落在**不同的判定单位**里。
- **为什么这次绕不过去**：「把禁令翻成声称」这个动作**本身**就会把否定标记带走。

### 面治：全部「断言某句话在场」型用例的逐条判定

问题一律是：**「把它自称守的那句从禁令翻成声称，会红吗？」**

| # | 用例 | 类型 | 翻成声称会红吗 | 处置 |
|---|---|---|---|---|
| 1 | `test_no_agent_def_uses_scoped_tool_syntax` | 结构（括号不许出现） | 不适用（不是在场型） | 不动 |
| 2 | `test_tool_faces_match_the_spec` | 结构（集合相等） | 不适用 | 不动 |
| 3 | `test_web_researcher_has_neither_repo_access_nor_bash` | 缺席型 | 不适用 | 不动 |
| 4 | `test_no_definition_claims_to_be_fully_read_only` | 缺席型（枚举肯定式） | 🔴 **不会红**（实测 M-B1′） | **已改句级判据** |
| 5 | `test_bash_holders_carry_the_honest_non_mechanical_disclaimer` | 在场型 | 🔴 **不会红**：两 needle 只要全文各出现一次即可 ⇒ 可分居两处、或写成「这里没有非机械门」 | **已改「同句内」判据** |
| 6 | `test_every_definition_has_an_exclusive_description` | 在场型 | ✅ 会红（needle 自带 `其它场景 MUST NOT 选用`） | 不动 |
| 7 | `test_frontmatter_tiers_match_the_design` | 结构（值相等） | 不适用 | 不动 |
| 8 | `test_web_content_is_declared_non_executable_data` | 在场型 | ✅ 会红（三条 needle 全部自带 `MUST NOT`） | 不动 |
| 9 | `test_second_source_requirement_for_design_affecting_conclusions` | 在场型 | ✅ 会红（needle = `影响设计决策的结论 MUST 有第二来源`） | 不动 |
| 10 | `test_secret_scan_*`（3 条） | 行为（真跑脚本） | 不适用 | 不动 |
| 11 | `test_sdflow_spec_does_not_ship_a_second_scanner` | 缺席型 | 不适用 | 不动 |
| 12 | `test_skill_routes_outbound_queries_through_the_shared_scanner` | 在场型 | ✅ 会红（`拒发，且 MUST NOT fallback` / `没扫成 ≠ 干净` / `MUST NOT 含`） | 不动（A 另加一条） |
| 13 | `test_s4_disposition_is_written_in_the_skill_and_the_writer_def` | 在场型 | 🔴 **不会红**：needle 全是**话题词**（`canonicaliz` / `artifactallowlist` / `confuseddeputy`）—— 把整段翻成「CLI 已经 canonicalize 过了，allowlist 由它保证，无须复查」四个 needle 全在（实测 M-B4′） | **已改祈使形态判据** |
| 14 | `test_skill_dispatches_by_subagent_type_for_all_three_agents` | 在场型 | ✅ 会红（`MUST NOT 用 agentType`）；三个 agent 名是**标识符**不是主张，不适用 | 不动 |
| 15 | `test_skill_records_the_model_enum_measured_limit` | 在场型（**实测事实**） | ⚠️ **部分可绕**：保留三个 needle 再补一句「该限制已解除」即可全绿 | **按通则④不改**（见下） |
| 16 | `test_skill_degrades_to_doing_it_itself_not_to_a_generic_subagent` | 在场型 | ✅ 会红（`MUST NOT 退通用子代理顶替` + `降级即提权`） | 不动 |
| 17 | `test_skill_documents_that_the_agent_roster_loads_at_session_start` | 在场型（**运维事实**） | ⚠️ **部分可绕**：同 15 | **按通则④不改**（见下） |

**15 / 17 为什么按通则④不改**（五问）：
根因 = needle 是**事实陈述**而非祈使句，「翻成声称」这个动作对它不适用，只能靠「加一句推翻它」来绕；
概率低（改实测边界的人必然是重新实测过，会连 needle 一起改）；
影响小 —— 15 的后果是模型填了完整 id 被 `InputValidationError` **当场拒**（fail-loud，不是静默放行），
17 的后果是诊断段误导、人多试一次 session；
完美成本 = 给事实类 needle 也造一套「有没有被后文推翻」的判据，那是**无界语义面**（基准 5）；
简化方案 = 保持现状 + 本表如实登记。∴ 不做。

### 修法的第二处：S4 处置锚（#13）

`_S4_MUST_SATISFY` / `_S4_ALLOWLIST` / `_S4_REFUSE` 三条正则，钉住**带 `MUST` / `拒写` 的那半句**：

- `canonicaliz\w*.{0,40}?MUST[^。]{0,8}满足`
- `落在\**artifactallowlist`
- `任一不满足⇒\**拒写`

三条在 `SKILL.md`（C.3 §3）与 `sdflow-spec-writer.md`（「写入前 MUST 净化」节）**两处措辞不同但都命中**，
原有的话题词断言（symlink 拒绝 / confused deputy 理由）保留。

### 变异回验

| # | 变异 | 结果 |
|---|---|---|
| M-B1 | 往 `sdflow-local-researcher.md` 追加「本 agent 的工具面全只读，工具白名单挡住了写权。」（**Spec 轴实测那条**） | **RED** `test_no_definition_claims_to_be_fully_read_only`（`:150`） |
| **M-B1′** | **反向对照**：同一变异 + **旧的整文件枚举判据** | **GREEN**（`1 passed`）⇒ 旧门确实守不住，修复是承重的 |
| M-B2 | 删掉 local 的「属指令层，非机械门」整句 | **RED** `test_bash_holders_carry_the_honest_non_mechanical_disclaimer`（`:163`） |
| M-B3 | 改写成「你的只读性属指令层。这里没有非机械门。」（两 needle 都还在，但**分居两句**） | **RED** 同一用例 ⇒ 「同句」判据生效 |
| M-B4 | 把 `SKILL.md` C.3 §3 翻成声称（「CLI 已经 canonicalize 过了…无须复查」，**话题词全保留**） | **RED** `test_s4_disposition_is_written_in_the_skill_and_the_writer_def`（`:429`） |
| **M-B4′** | **反向对照**：同一变异 + **旧的话题词判据** | **GREEN**（`1 passed`）⇒ 该锚原本是恒绿的 |

---

## C · `install_agents()` 接管守卫只认当前 checkout

### 病灶

守卫 `case "$link" in "$REPO_DIR"/*)` 只认**当前** checkout；孤儿清理判据更窄（`"$src_dir"/*`）。
⇒ 指向**本仓另一 checkout** 的链**既不接管、也不清理**，名册**裂脑**（一条来自 A、其余来自 B）。
而 `CLAUDE.md` 的 dev/runtime 纪律**明写**「测完/合并后在运行 checkout 重跑 setup **还原**」
「**回滚** = 运行 checkout `git checkout <上一已知良好 commit>` + 重跑 setup.sh」
⇒ 这两条对 agent 定义**静默失效**。skills 侧无此问题（`install_into` 对同名软链无条件 `ln -snf`）。

### 两个候选与决策

| 候选 | 判据 | 能不能解决本病灶 |
|---|---|---|
| ① 沿用 `cleanup_orphans:91` 的位置无关 idiom `*/"$REPO_NAME"/*` | 按**仓目录名**认自属 | 🔴 **不能**。`REPO_NAME` 是**当前** checkout 的 basename，而真实的两个 checkout **目录名本就不同**（运行 `~/.skills/sdflow-skills` vs 开发 `04-sdflow-skills`）⇒ 从开发 checkout 跑 setup 时，`*/04-sdflow-skills/*` 匹配不上指向运行 checkout 的链。step1 §5.1 已记过这一点，本轮实测复现 |
| ② 按后缀 `*/sdflow-spec/agents/<name>` 认自属 | 按**仓内布局形状**认自属 | ✅ 位置无关、与目录名解耦 |

**推荐并已实现 ②。** 依据：① 在本仓的真实命名下**不解决问题**（这不是偏好之争，是可证伪的事实）。

**代价（决策三镜）**

- **系统镜**：② 把守卫耦合到「`sdflow-spec/agents/` 这个路径形状」。代价可控 —— 该形状与同函数第一行
  `src_dir="$REPO_DIR/sdflow-spec/agents"` **相邻且同源**，改布局时两处一起改，不构成远距离耦合。
  依赖不变（纯 shell `case`），复杂度 +0（同一条 `case` 换了 pattern），可回退（一行）。
  ① 的耦合面看似更小，但它耦合的是**运行时才知道的 basename**，反而不可预测。
- **用户镜**：② 令 dev↔runtime 来回切时 setup **自动接管**，`CLAUDE.md` 明写的「重跑 setup 还原」
  与「回滚」两条路径真正生效；人不必先 `rm` 再重跑。可感知行为变化仅此一处，无干扰。
  ① 在真实命名下仍静默失效 —— **用户按文档做了，结果没生效**，是最贵的一种失败。
- **开发循环镜**：② 的心智负担低（判据一句话说得清：「链指向某个 `sdflow-spec/agents/` 下的同名文件」），
  测试成本低（假 HOME 预置一条指向另一路径的自属链即可，见新用例）。
  ① 还要额外解释「REPO_NAME 何时相同、何时不同」，反而更绕。

**主次判定：以用户镜为主。** 本条修的是「文档承诺的操作路径静默失效」，
系统镜两候选的耦合面等价（都是一行 `case`），开发循环镜差异小 —— 决定性的是「照文档做能不能生效」。

⚠️ **MUST NOT 放宽到「是软链就覆盖」**（`CLAUDE.md`：绝不覆盖非本仓库拥有的同名目录）。
既有用例 `test_a_foreign_file_is_never_clobbered_and_lands_in_skipped` 守这条边界，两条一起绿。

### 面治：孤儿清理判据同步放宽

接管判据放宽而清理判据不放宽 ⇒ 「指向另一 checkout **且源已删**」的链永远留着，
既不接管也不清理 —— 那是裂脑的另一半。∴ `*/sdflow-spec/agents/*.md` 与接管判据**同宽**。

### 新增/扩充的用例

- `test_a_link_from_another_checkout_of_this_repo_is_taken_over`（新）——
  假 HOME 预置一条指向 `<tmp>/sdflow-skills-runtime/sdflow-spec/agents/<name>` 的链
  （**故意取不同的目录名**，复现真实 dev/runtime 命名），跑 setup 后 MUST 指向本仓，且**名册不裂脑**。
- `test_dangling_link_of_a_deleted_source_is_cleaned`（扩一格）——
  再预置一条**跨 checkout 且悬空**的链，MUST 被清；外来悬空链 MUST 保留。

### 变异回验

| # | 变异 | 结果 |
|---|---|---|
| M-C1 | 自属判据回退成 `"$REPO_DIR"/*`（**Standards 轴实测那条**） | **RED** `test_a_link_from_another_checkout_of_this_repo_is_taken_over`（`:145`，链仍指向 `…/sdflow-skills-runtime/…`） |
| M-C2 | 删掉整个 `case` 守卫（= 是软链就覆盖） | **RED** `test_a_foreign_file_is_never_clobbered_and_lands_in_skipped`（`:108`，外来悬空链被覆盖） |
| M-C3 | 孤儿判据回退成 `"$src_dir"/*`（比接管判据窄） | **RED** `test_dangling_link_of_a_deleted_source_is_cleaned`（`:175`，跨 checkout 悬空链没被清） |

---

## D · 探针写进真实工作树

### 病灶

`test_a_new_agent_file_turns_check_red` 把探针 `.md` 写进**真实** `sdflow-spec/agents/`，
并以 `assert not probe.exists()` 起手：
① 并行跑 pytest 时互踩（一方的探针触另一方的起手断言）；
② 测试被中断 ⇒ 残留文件进 **tracked 目录**，且下次 `bash setup.sh` 会把它**软链进全局 `~/.claude/agents/`**。

### 修法

- 探针改 `tmp_path` 造目录 + `monkeypatch.setattr(SP, "AGENT_TARGETS", (probe_dir, SP.SOURCE))`；
- 另立 `test_the_delivery_surface_points_at_the_real_agents_dir`（**静态断言**
  `SP.AGENT_TARGETS[0] == SP.REPO / "sdflow-spec" / "agents"` 且它是目录），
  承担「投放面确实指向真实目录」这一维 —— 两条合起来 == 旧版一条的全部证明力，且不碰工作树。
- 连带修 `hack/sync_principles.py`：`drift.append(p.relative_to(REPO))` → `os.path.relpath(p, REPO)`。
  **理由**：`Path.relative_to` 对**仓外**投放面直接抛 `ValueError` ⇒ 「报告一个漂移」变成「`--check` 整个崩掉」。
  这一行只是**打印用的显示形式**，不该有能力中止判定。正常路径下两者输出**同一个字符串**（已实测）。

### 面治：全仓扫「往真实工作树写文件」的测试

两轮机械扫描（不加 `--include`）：
① 逐行扫 `write_text|write_bytes|touch|mkdir|unlink|symlink_to|rename|os.symlink|shutil.*` 且同行出现
`REPO|ROOT|SRC_DIR|AGENT_DIR|REPO_DIR|PROJECT_ROOT` 的；
② 扫「变量赋值自 `REPO`/`AGENT_DIR`/… 之下」再被写操作消费的。

命中三处，逐条判定：

| 落点 | 判定 |
|---|---|
| `hack/tests/test_sync_principles.py:166` | 🔴 **真往工作树写** ⇒ **本轮修掉** |
| `sdflow-init/tests/test_setup_sdflow.py:80,102` | 软链**指向** `REPO/...`，但链**本身建在 tmp 目录**里 ⇒ 不写工作树，合规 |
| `hack/tests/test_install_agents.py:123` | 同上（`os.symlink(str(SRC_DIR / …), gone)`，`gone` 在假 HOME 下） | 

另外逐个看过全部 `finally:` 收尾块（20 处）：其余都是 `tmp_path` 下的 fixture 或 `chmod` 还原，
无第二处工作树写入。**全仓仅此一处**。

### 变异 / 实测回验

| # | 变异 | 结果 |
|---|---|---|
| M-D1 | `agent_defs()` 的 glob → 硬编码三文件清单 | **RED** `test_a_new_agent_file_turns_check_red`（`:182`）⇒ 换了落点后，它守的仍是 glob 发现机制 |
| M-D2 | `AGENT_TARGETS[0]` 指向 `sdflow-spec/references` | **RED** 4 条（含新的静态断言 `test_the_delivery_surface_points_at_the_real_agents_dir`） |
| M-D3 | `AGENT_TARGETS` 的源 `SOURCE` → `SOURCE_PROJECT`（既有门回归确认） | **RED** `test_agent_defs_are_paired_with_the_skill_flavored_source` + `--check` |

**并发实证（病灶本身）**——同一份代码、6 路并行跑 `test_sync_principles.py`：

```
旧版（HEAD 的探针写真目录）：  1 failed, 11 passed   × 5 路   ← 互踩
新版（tmp_path + monkeypatch）：13 passed            × 4 路   ← 全绿，且 sdflow-spec/agents/ 无残留
```

---

## E · 残留「填解析出的具体 id」措辞

`SKILL.md:460`（C.3 阶段二那段）仍写「`model` 填 0.2 解析出的具体 id」——
与 step2 §4.1 的实测结论（`model` 是**枚举** `sonnet|opus|haiku|fable`，填完整版本化 id 被
`InputValidationError` 拒）矛盾，是 :205 / 外派协议改过之后的**点补漏网**。

**修法**：改为「填 0.2 解析出的**字面值**（枚举边界见「外派协议」）」。

**面治**：`grep -rn '具体模型 id\|具体 id\|完整版本化\|模型 id'` 全仓（不加 `--include`）。
`sdflow-spec/` 下该措辞族已**归零**。其余命中全在 `openspec/changes/add-sdflow-spec/`
的 proposal / design / specs / tasks / superpowers-plan 与前两份 impl-report 里 —— 那些是
**MUST NOT 改**的设计定稿与历史报告，本轮不动（spec 侧措辞与实测的差异已由 step2 §4.1 记录在案）。

## F · 正文内联具体模型 id

`SKILL.md:276` 举反例时内联了一个完整版本化 id，与 SA-07「SKILL.md 正文写变量名，
MUST NOT 内联具体模型 id」字面擦边。
**修法**：改成占位形态「填**完整版本化 id**（`<族>-<代>-<日期>` 那种形态）」——
反例的教学作用保留，具体串不落地。
枚举值 `sonnet|opus|haiku|fable` **保留**：它们是**参数枚举的合法取值**（用例
`test_skill_records_the_model_enum_measured_limit` 钉着），不是「具体模型 id」。

## G · `mkdir -p` 失败中止整个 `setup.sh`

`install_agents` 排在 `install_sdflow` **之前**，`set -e` 下 `mkdir -p "$dest"` 失败会当场中止全脚本
⇒ 连 `~/.sdflow/` 的 canonical 与 hack 脚本（`resolve-models.sh` / `outside-voice.sh` /
`checkpoint-commit.sh`）都一并装不上，用户只看到一行裸 `mkdir:` 错误、无汇总。
与同文件「外来同名条目 → skip + 报告」的既定取向不一致。

**修法**：`mkdir -p "$dest" 2>/dev/null || { skipped+=("agents @ $dest — 落点建不出来（被占为普通文件？权限？），未铺设"); return 0; }`

**新用例** `test_an_occupied_dest_degrades_to_skip_and_does_not_abort_setup`：
假 HOME 里把 `.claude/agents` 占成普通文件 ⇒ `rc == 0`、进 `skipped` 段、占位文件未被动、
**且 `~/.sdflow/hack/` 照常装出来**（后半条才是这个 bug 真正的代价）。

| # | 变异 | 结果 |
|---|---|---|
| M-G1 | 回退成裸 `mkdir -p "$dest"` | **RED** 该用例（`:195`）：`returncode=1`，stderr 只有 `mkdir: …/.claude/agents: File exists` |

## H · docstring 考古层

`test_sdflow_spec_agents.py` 的 `test_no_agent_def_uses_scoped_tool_syntax` docstring 里
「同轮的另一条观测已被证伪，别再引用：当时以为…」是纯考古层（只有读过上一版的人才需要），违反 DOC-1。

**修法**：只留最终事实 ——「本 harness 不存在 `Glob` / `Grep` 这两个工具（主 session 与
`general-purpose` 子代理的工具清单里都没有），检索走 `Bash`」，删掉「当时以为…」。

**面治**：本轮新写的用例 docstring 与本报告一律按 DOC-1 写（正文即最终态）——
唯一保留「曾经不是这样」的地方是**变异回验表**，那是**证据**不是演进史（它证明门此刻真会红）。

---

## 门禁与全量

```
$ git add -A && /usr/bin/python3 -m pytest        # 仓根全量
2775 passed, 10 skipped, 3 xfailed in 274.55s (0:04:34)
  （已知抖动用例 test_outside_voice_job.py::test_supervisor_transcript_… 本轮**通过**）

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

上一轮（step2）为 `2771 passed` ⇒ 本轮净增 **4** 条用例
（`test_outbound_scan_prechecks_the_helper_and_has_a_catch_all` ·
`test_a_link_from_another_checkout_of_this_repo_is_taken_over` ·
`test_an_occupied_dest_degrades_to_skip_and_does_not_abort_setup` ·
`test_the_delivery_surface_points_at_the_real_agents_dir`），
另有 4 条既有用例的判据被收紧（B 的 #4 / #5 / #13，C 的孤儿清理格），零删除。

`sdflow-spec/SKILL.md` = **590 行**（D12 上限 600，余量 10 行）。

**`~/.claude/agents/` 真实目录**（跑 `test_install_agents.py` 前后各记一次，逐字节一致）：

```
sdflow-local-researcher.md -> …/04-sdflow-skills/sdflow-spec/agents/sdflow-local-researcher.md
sdflow-spec-writer.md      -> …/04-sdflow-skills/sdflow-spec/agents/sdflow-spec-writer.md
sdflow-web-researcher.md   -> …/04-sdflow-skills/sdflow-spec/agents/sdflow-web-researcher.md
```

（`fake_home` fixture 的前后快照断言本轮全程绿；本报告的手工核验是它的第二道。）

## 诚实边界（本轮新增/仍然成立的）

1. **A 的预检与 catch-all 是指令层锚，不是机械门。** 机械可验的只有「这三句还写在 SKILL.md 里」
   （删任一即红）。「主 session 派发前真的跑了预检」没有确定性信号 —— 除非把派发本身脚本化，
   那超出本 change 范围。step2 §6.3 的同一条边界继续成立。
2. **B 的句级判据守的是「措辞没被翻成声称」，不是「子代理真的没写文件」。** 后者在 `Bash` 在手时
   没有机械边界（step2 §6.4）。本轮把门从「可绕」修到「翻成声称必红」，**没有**把它升级成机械门。
3. **B 表格里 15 / 17 两条仍部分可绕**，按通则④如实登记不做（理由见上）。
4. **C 的判据认的是路径形状，不是仓身份。** 一个第三方若把自己的 agent 定义放在
   `<任意路径>/sdflow-spec/agents/<同名>.md` 并软链过来，会被接管。判为可接受边角：
   该路径形状是本仓专有布局，且**同名**才会撞（`~/.claude/agents/` 里同名本就只能有一个）。
   备选（更严：同时要求 `<name>` 在本仓源目录里存在）已被 `for f in "$src_dir"/*.md` 的循环隐含 —— 只有
   本仓真有的定义名才会走到那段守卫。
5. **`install_agents()` 的 Windows 分支仍无机械覆盖**（`IS_WINDOWS` 由 `uname -s` 决定、无环境变量
   覆盖入口，本机 Darwin 测不到）。同 step2 §6.6，未为测它给生产代码开覆盖开关。

## 偏离与遗留

- **无偏离**。八条全部按票面修法实现；C 的两个候选按票面要求「自己判并给三镜 + 主次」，
  判为 ②（票面列的两个候选之一），理由是 ① 在本仓真实命名下**不解决问题**（可证伪，非偏好）。
- **未改动** `proposal.md` / `design.md` / `specs/` / `tasks.md` / `superpowers-plan.md`（票面硬约束）。
- **E 的 spec 侧措辞差异未回改**（`specs/spec-authoring/spec.md:163,177` 仍写「具体模型 id」）——
  那是设计定稿，MUST NOT 改；实测结论与它的关系已由 step2 §4.1 记录在案，留给编排层判是否需要 amendment。
