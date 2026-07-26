# code-review-fix —— 代码审合并池 F1–F7 修复报告

> 触发：阶段三代码审（跨模型 voice + 对抗镜）合并池 **5 高 + 2 中**。
> 基线 commit `bbf62bd`（`feat/add-sdflow-spec`）。所有改动标 `[impl-review-fix]`。
> 纪律：F1/F2/F3/F4/F5/F7 **先写会红的用例 → 确认红 → 修绿 → 定点变异复验**（判据「期望红 ⊆ 实际红」）；
> 变异一律在 scratchpad 的仓副本 / 假 HOME 里做，真实工作树与 `~/.claude/{agents,hooks}/` 跑前跑后快照一致。

| # | 面 | 结论 |
|---|---|---|
| F1 | `outside-voice.sh` secret-scan fail-open | ✅ 修复 + 2 用例 + 2 变异 |
| F2 | FF-0 只解析第一个 change 名 | ✅ 修复 + 6 用例 + 2 变异 |
| F3 | 跨 checkout 废弃 agent 永留全局名册 | ✅ 修复（installer-owned manifest）+ 1 用例 + 2 变异 |
| F4 | S4 路径检查漏 change root 及祖先软链 | ✅ 修复 + 4 用例 + 1 变异；**指令侧同步**（SKILL.md + writer 定义） |
| F5 | `set -e` 下裸外部命令中止全脚本 | ✅ 面治（`install_into` / `cleanup_orphans` / `install_sdflow` 全扫）+ 3 用例 + 3 变异 |
| F6 | 重入状态机漏两态 | ✅ 修复（B.1 ④ 草稿纪要 + 0.3 三态分治 + 承诺改为有界损失）；无新增机械门（见 §6） |
| F7 | deny 文案 `touch {token}` 未 quoting | ✅ 修复 + 2 用例 + 1 变异 |

---

## F1 · `secret_scan` 扫描器执行失败被判「干净」（安全门 fail-open）

**复现**（注入恒返回 2 的 `grep` 到 PATH 首位，真跑 `secret-scan --context-file <干净文件>`）：

```
returncode=0, stdout='', stderr=''      ← 扫描器坏了 ⇒ 判没命中 ⇒ 出境查询直接放行
```

**根因**：`lines=$(grep -nE -- "$pattern" "$file" 2>/dev/null | head -3 | cut … | tr … | sed …)`
的 `$?` 只反映管道尾端的 `sed`。grep 的 **rc≥2（命令错误：文件不可读 / 非法正则 / 坏 locale /
二进制被沙箱拦）** 与 **rc=1（真·无匹配）** 产出同一个空 `lines` ⇒ 函数 `return 0`。
与本文件早先修过的 `_ov_bytes_at` M2 同族（**成败信号不得经管道尾端转手**）。

**修法**（`sdflow-init/assets/hack/outside-voice.sh`）：

- `raw=$(grep …)` + `rc=$?` **单独捕获**；三分 `0=命中 / 1=无匹配 / ≥2=命令错误`，后者 stderr
  报 `secret-scan 扫描器失败（fail-closed 拒发）: 规则=… grep_rc=…` 并 `return 2`。
- 新增 `secret_scan_or_exit()`，**四个**调用点（`render_prompt` / `do_exec` 预扫 / A1 出境侧 /
  `secret-scan` 子命令）统一改走它：`1 → exit 3`（既有 secret-hit 码）、`其余 → exit 2`（没扫成 ≠ 干净）。
  MUST NOT 退回 `secret_scan … || exit 3`——那会把「压根没扫成」报成「扫到了密钥」，归因错误。
- 文件头契约与 `OV_VERSION` 同步（**1.5.1 → 1.5.2**，`test_version` 的版本日志一并补记）。
- **消费侧对齐**：`sdflow-spec/SKILL.md` 的 `exit 2` 一格补「扫描器自身跑挂」（catch-all 本已覆盖）。

**面治核验**（全文扫「管道/子壳调外部命令且据其结果做安全判定」）：

| 位置 | 结论 |
|---|---|
| `secret_scan` grep 管道 | **本次修复** |
| `_ov_bytes_at` `od \| tr \| grep` | 已修（M2：先捕 od 的 rc 与输出，再格式化） |
| `utf8_*` / `render_prompt` 的 `wc -c \| tr` | 安全判定锚**取值**（空/非数字 ⇒ fail-loud），不依赖管道 rc |
| `resolve_timeout_bin` `command -v … \|\| true` | 调用方判空串 → `missing-deps` |
| `_ov_pgid_of` `ps \| tr` | 取值校验，取不到 ⇒ `single:pgid-unavailable` 保守退回 |

⇒ 本轮为该面**最后一处**残余。

**用例**（`hack/tests/test_sdflow_spec_agents.py`）：
`test_secret_scan_fails_closed_when_the_scanner_itself_fails`（rc=2 ⇒ 拒发 exit 2 + stderr 有归因）
+ `test_secret_scan_still_passes_when_grep_reports_no_match`（rc=1 ⇒ exit 0，**区分力校准**，防这门恒红）。

**变异**：

| 变异 | 实测 |
|---|---|
| M-F1a `rc -ge 2` → `rc -ge 99`（吞掉扫描器失败） | **RED** `…fails_closed_when_the_scanner_itself_fails` |
| M-F1b 调用点退回 `secret_scan "$ctx" \|\| exit 3` | **RED** 同上（`assert 3 == 2`，归因码被改错） |

---

## F2 · FF-0 只解析第一个 change 名，前置文本可绕过

**复现**（在 `feat/add-sdflow-spec` 上）：

```
echo openspec new change add-sdflow-spec; openspec new change unrelated-change
→ 旧实现：无 deny 输出、exit 0
```
第一处匹配的名字等于当前 change ⇒ 判成分支②幂等放行，而 Bash 真正执行的是第二条（stacking）。

**修法**（`sdflow-init/assets/hooks/ff0-branch-guard.py`，**不解析 shell**，判据仍是有界正则）：

- `change_name()` → `change_names()`：`search()` 改 `finditer()`，**枚举全部**有界匹配；
  任一 token 非法（`$VAR`/反引号/通配符）⇒ 返回 `[]`（沿用 fail-open）。
- 主流程加**两个有界计数之差**：`occurrences = len(NEW_CHANGE_RE.findall(command))` 与读得出的名字数。
  `occurrences > 1` 且（数量不等 或 名字不唯一）⇒ **deny 要求拆成独立调用**；
  名字集合 >1 ⇒ deny；**全部匹配同名**才走原②③。
- **单次**调用认不出名字的 fail-open 纪律**不放宽**（`test_unparseable_change_name_fails_open` 仍绿）。
- 模块 docstring 补该判据与其边界。

**用例**（`sdflow-init/tests/test_ff0_branch_guard.py`）：
`test_second_creation_call_behind_a_decoy_is_denied`（原样复现）·
`test_multiple_distinct_change_names_are_denied`（3 参数：`&&` / `;` / 管道+引号变体）·
`test_repeated_identical_change_name_stays_idempotent`（收紧不误伤幂等）·
`test_multiple_calls_with_an_unreadable_name_are_denied`（`$(cat …)` 那一处）。

**变异**：

| 变异 | 实测 |
|---|---|
| M-F2a `finditer` 退回只取第一个 + `occurrences=1` | **RED** 5 条（诱饵 + 3 个多名参数 + 读不出名字） |
| M-F2b 只删「出现次数 vs 读出名字数」这一格 | **RED** 1 条（`…with_an_unreadable_name…`）——两格各有独立区分力 |

---

## F3 · 跨 checkout 删除 agent 后，废弃定义永留全局名册

**缺口**：接管循环只认「**当前**源目录里还在的名字」，孤儿清理只删「**悬空**的链」。
「旧 checkout 的 `.md` 还在、新 checkout 已删」同时落在两者之外 ⇒ 一份废弃、却仍持
`Bash`/`Write` 的定义对本机所有项目持续可见。

**方案取舍**（通则④五问）：voice 建议的 **installer-owned manifest** 被采纳，**未**简化为
「本仓路径形状的链就删」——后者会删掉别人仓里同布局的**有效**链（`test_dangling_link_of_a_deleted_source_is_cleaned`
第六格明写那是真实数据丢失，且与 `CLAUDE.md`「绝不覆盖非本仓库拥有的同名目录」冲突）。
manifest 的全部作用就是把「**我们装的**」与「碰巧同形的」分开，代价 = 一个 74 字节的 dotfile。

**修法**（`setup.sh`）：

- 新常量 `AGENTS_MANIFEST=".sdflow-agents"`；新函数 `write_agents_manifest()`（临时文件 + `mv -f`
  原子写；写不成 ⇒ `skipped[]` + 继续）。
- `install_agents()` 记录本趟真正铺出去的名字 `laid[]`（被 skip 的不算），
  **顺序不可换**：先 `cleanup_agent_orphans "$dest" "$src_dir"`（读上一趟 manifest）再写新 manifest。
  源目录整体消失的早退路径同样调用（源集合传空串 ⇒ manifest 里全是废弃项）。
- `cleanup_agent_orphans()` 加第 (0) 格：manifest 里有、当前源集合里没有 ⇒ 撤下。
  三道守卫：① 名字必须是**裸文件名**（manifest 被写坏也不许变成任意路径删除）
  ② 落点必须是**软链**（真实文件不碰）③ 链指向必须是本仓布局（与接管判据同一路径形状）。
- **诚实边界**（已写进注释）：升级到本版本后的**首趟**盘上没有 manifest ⇒ 撤不出废弃项，一趟后自愈；
  人手删 manifest 亦然。MUST NOT 声称零窗口。

**用例**（`hack/tests/test_install_agents.py::test_an_agent_deleted_in_the_new_checkout_is_retired_even_though_the_old_file_lives`）：
替身仓多铺一个 `sdflow-legacy-agent.md`（真实文件）→ 换真仓跑 setup ⇒ 链被撤下、**源文件未被删**、
别人仓的**有效**链 `their-live-agent.md` 原样保留；再跑一次不误撤自己刚铺的三条。

**变异**：

| 变异 | 实测 |
|---|---|
| M-F3a 关掉 manifest 驱动的撤下 | **RED** 1 条（新用例） |
| M-F3b 判据放宽成「路径形状就删」（去掉「有效链留着」） | **RED** 4 条（含既有的第六格与幂等用例）——边界两侧都锁住 |

---

## F4 · S4 路径检查漏 change root 及上级目录的 symlink 逃逸

**根因**：`check_output_path` 的第 ④ 道从 `change_root` 起步，且 ①②③ 全是**纯词法**判定
（`normpath` + `relative_to`，对软链一无所知）⇒ `openspec` / `changes` / `<name>` 任一层
是指向仓外的软链时，全部放行、写入落到仓外。既有用例只覆盖目标文件与 `specs` 两格。

**修法**：

- **判据（`hack/tests/test_sdflow_spec_agents.py::check_output_path`）**：④ 改为**从仓根逐组件**
  走到目标（`ancestors + parts`，含 change root 自身及其每一级祖先）；越出仓根 ⇒ 「越界」拒。
  末尾保留一次解析后复核，并**诚实标注它在当前构造下被逐组件循环蕴含**（没有输入能单独走到它；
  保留理由是 TOCTOU 二次快照 + 起点被放宽时的最后一格），MUST NOT 把它算作「已被用例证明的门」。
- **产品指令同步**（真正被消费的是指令，不是这个纯函数）：
  `sdflow-spec/SKILL.md` C.3 §3 与 `sdflow-spec/agents/sdflow-spec-writer.md` 的第 3 条
  都改为「**从仓根到目标逐组件都不是 symlink**（含 change 目录自身及其祖先）」，
  writer 定义补一句「1 与 2 是纯词法判定、接不住这一格」的理由。

**用例**：`test_s4_rejects_a_symlinked_ancestor_above_the_change_root`（**三层祖先**参数化：
`openspec` / `changes` / `demo`，各自软链到仓外并断言拦它的是**软链**那道门）
+ `test_s4_rejects_a_change_root_outside_the_repo_root`（连**哪道门**一起断言＝「越界」，
且注释写明它**不是**在给那条被蕴含的复核背书——防恒真锚）。

**变异**：M-F4「④ 退回从 change_root 起步 + 去掉解析复核」⇒ **RED** 5 条（3 个新祖先格 +
既有的目标自身/`specs` 两格）。期望红 ⊆ 实际红。

---

## F5 · `set -e` 下裸外部命令中止整个 setup.sh

**复现（修复前，4 轮并发实跑）**：两个 `bash setup.sh` 并发铺同一个全新假 HOME ——

```
round 1: A EXIT:0 B EXIT:0
round 2: A EXIT:1 B EXIT:0   ← stdout 只有一行：ln: …/.codex/skills/sdflow-devenv: File exists
round 3: A EXIT:0 B EXIT:1   ← ln: …/.claude/skills/embedded-test-sop: File exists
round 4: A EXIT:0 B EXIT:0
```
命中 2/4；命中的那一趟**无汇总**。根因：`ln -sf` 不是单一系统调用（内部 unlink→symlink），
并发下后者 `EEXIST`。同款防御 `install_agents()` 早已写好，上一轮只补了一处（点补 vs 面治）。

**修法（面治，`setup.sh` 全文按同一取向）**：新增「`set -e` 面治」节注释，并逐处降级为
`skipped[] + 汇总`：

| 函数 | 处理的裸调用 |
|---|---|
| `install_into` | `mkdir -p` · `rm -rf`（marker 旧拷贝，Unix/Windows 各一）· `cp -r` · **`ln -snf`** |
| `cleanup_orphans` | `rm -rf`（孤儿） |
| `install_sdflow` | `mkdir -p` · `printf > workflow-path` · **`ln -snf`**（canonical）· `rm -f`（旧 manifest）· 三个循环的 `cp` / `chmod +x` |

⚠️ 这**不放宽所有权守卫**：谁能被覆盖仍由 `-L` / marker / readlink 判据决定，本节只管
「判定放行之后那条命令跑挂了怎么办」。

**🔴 接缝：这次改动自己开了一个洞，被既有用例当场抓住**
`TestCapabilitySnapshot::test_interrupted_install_leaves_no_consistent_snapshot` 在改完后变红。
原因不是它过时：`cp` 从「裸调用 + set -e 中止」变成「skip + 继续」后，控制流会一路走到
**写 manifest** 那一步，而它算的是**当前盘上的字节** ⇒ 会给一份「新旧混装」的现场签一个自洽的名，
preflight 从此判绿 —— 正是那段注释要防的「自洽但陈旧」。
修法：`install_sdflow` 记账 `cap_broken` / `cap_broken_pre`（任一成员没装上 / 旧 manifest 删不掉）
⇒ **跳过写 manifest** 并打印归因，现场无 manifest ⇒ preflight 仍 fail-closed（与中止时同一终态，
但其余东西照样装完、失败也进了汇总）。
该用例同步改判据：**从「setup 非零退出」改为「manifest 不在场 + verify 判红 + 失败可见于 skipped 汇总」**
——前者是被替换掉的机制（降级后会恒红），后者才是承重不变量。理由已写进用例 docstring。

**复现（修复后，6 轮并发实跑）**：

```
round 1: A:0 B:0 | skipped(ln):0 | both summaries: 2
round 2: A:0 B:0 | skipped(ln):2 | both summaries: 2
round 3: A:0 B:0 | skipped(ln):2 | both summaries: 2
round 4: A:0 B:0 | skipped(ln):0 | both summaries: 2
round 5: A:0 B:0 | skipped(ln):1 | both summaries: 2
round 6: A:0 B:0 | skipped(ln):0 | both summaries: 2
```
6/6 双方跑完并出汇总；EEXIST 竞态现在表现为 `skipped[]` 条目（可见、不致命）。

**用例**（`sdflow-init/tests/test_setup_sdflow.py::TestSetEDoesNotKillTheWholeInstall`）：
只读 skills 落点 / 只读 `~/.sdflow` / **两进程并发**（确定性方向：修复后必须两边都 0）。

**变异**：

| 变异 | 实测 |
|---|---|
| M-F5a `install_into` 的 `ln` 退回裸调用 | **RED** 只读 skills 落点 + 并发（+ 快照用例，同源） |
| M-F5b `install_sdflow` 的 `ln` 退回裸调用 | **RED** 只读 `~/.sdflow` |
| M-F5c manifest 门退回（成员没装上仍签名） | **RED** `test_interrupted_install_leaves_no_consistent_snapshot` |

---

## F6 · 重入状态机漏两态，与「崩溃无损」承诺冲突

**缺口**：探测谓词要求「**含** `decision-memo.md` **且** `isComplete=false`」，而 change 在
B.1 ③ 才建、首次落盘在 B.4 ⇒ 期间崩溃留下的是一个**没有纪要**的在途 change（探测不到）；
`isComplete=true` 被谓词排除 ⇒ `complete` 只剩 0.4 的一句声明、**没有对应的操作判定**。

**修法**（`sdflow-spec/SKILL.md`，三处一起）：

1. **B.1 新增第 ④ 步「立即落最小草稿纪要」**：change 目录一建成就当场写身份 frontmatter
   （`decision_hash` 留空——定稿才算）+ 空的两个必填小节。它同时是「崩溃只丢上一次保存之后
   那一段」的**第一个保存点**；草稿必然过不了 C.1 判 4 ⇒ 走那里既有的「缺失 ⇒ 退回 B 补定稿」。
   连带：B.1 标题「起手三步 → 起手四步」，B.7 两步 `④⑤ → ⑤⑥`，0.4 状态机与顶部流程图同步。
2. **0.3 改为无条件读 `isComplete` + 三态分治表**：`false ∧ 无纪要` → 回相位 B（A 的共识随
   上下文丢了，先重述锚点纪要）；`false ∧ 有纪要` → 跳过 A、核验纪要后进 C；
   `true` → **拒绝重生成**。并显式写死两条 MUST NOT（别拿「有没有纪要」当探测前提、
   别只探 `isComplete=false`）。
3. **承诺改为有界损失**：frontmatter description 由「`/clear` 与 session 崩溃无损」
   改为「**`/clear` 无损，崩溃只丢「上一次保存之后」那一段**」——与 B.4 既有的诚实表述、
   与 SA-04「/clear 无损」一致。

**体量**：`wc -l sdflow-spec/SKILL.md` = **600**（上限 600）。腾出的行**全部来自纯重排**
（顶部流程图 5→4、B.2 引注 2→1、A.3 / 出口序列两条理由 / 终审两段各合并一行、0.4 由 ASCII 图
改为一行状态串 + 回边说明），**零字丢失、未截断任何引用路径、未删任何限定词**。

**机械覆盖（诚实标注）**：本条**没有**新增机械门——它改的是给模型看的指令，与本仓既有
「指令在场锚」同类；`hack/tests/test_sdflow_spec_*.py` 中无 needle 锁这几段（已 grep 核实），
故本次也没有用例会因这段被删而红。属**语义残余**，交人读与后续 review。MUST NOT 把 §6 记成
「已机械验证」。

---

## F7 · deny 文案的 `touch {token}` 未经 shell quoting

**复现**：仓库目录名 `pro;j $(id) &x` 时，把文案里那条 `touch` 原样丢给 shell ——

```
/bin/sh: x/openspec/.ff0-ack: No such file or directory      （exit 127；`$(id)` 被展开、`&` 起了后台命令）
```
空格路径（`pro j`）则造出两个错文件、哨兵根本不存在 ⇒ **逃生口不可用**。

**修法**：`token` 经 `shlex.quote()` 后再进文案（干净路径原样返回 ⇒ 常见情形文案不变），
并注明理由。

**用例**：`test_escape_hatch_command_is_shell_quoted`（两参数：空格 / 元字符）——
端到端跑人的动作：执行文案给的 `touch` ⇒ 断言哨兵**恰好**被造出（`openspec/` 下新增集合
精确等于 `{.ff0-ack}`，防拆词多造文件）⇒ 再跑一次创建命令必须放行。

**变异**：M-F7「去掉 `shlex.quote`」⇒ **RED** 2 条。

---

## 全量核验

```
$ git add -A && /usr/bin/python3 -m pytest          → 2795 passed, 11 skipped, 3 xfailed in 279.65s（0 failed）
                                                     （已知抖动用例 test_outside_voice_job.py::…no_context_stdout_or_secret 本轮绿）
$ bash setup.sh                                    → rc=0；sync_principles ✅ / gen_workflow_guide ✅ / async-branch-parity ✅
$ /usr/bin/python3 hack/sync_principles.py --check  → ✅ 22 个投放面全部与真相源一致
$ wc -l sdflow-spec/SKILL.md                        → 600（上限 600）
$ /usr/bin/python3 sdflow-init/scripts/init.py update --root .
$ diff ~/.claude/hooks/ff0-branch-guard.py sdflow-init/assets/hooks/ff0-branch-guard.py → IDENTICAL
$ bash ~/.sdflow/hack/outside-voice.sh version      → outside-voice.sh 1.5.2（安装态与源同代）
```

**副作用核验**：`~/.claude/agents/` 跑前跑后均为三条指向本仓的软链（+ 本次新增的
installer-owned `.sdflow-agents` 名册文件）；`~/.claude/hooks/` 仅 `ff0-branch-guard.py`
按预期更新，另两个第三方 hook 未动。全部变异均在 scratchpad 仓副本 / 假 HOME 内进行。

**未做 / 边界**（如实登记）：

- F4 的解析后复核在当前构造下**被逐组件循环蕴含**，保留但已在代码与用例里标注「无输入能单独走到它」。
- F3 的 manifest 有**首趟无名册**的一次性窗口（升级后第一次运行撤不出废弃项），已写进 `setup.sh` 注释。
- F6 无新增机械门（指令层改动），已在上面标注。
- `AGENTS.md` / `CLAUDE.md`：`init.py update` 会顺手删掉托管块内一个空行；与本轮修复无关，
  已 `git checkout` 还原，保持 diff 聚焦。
