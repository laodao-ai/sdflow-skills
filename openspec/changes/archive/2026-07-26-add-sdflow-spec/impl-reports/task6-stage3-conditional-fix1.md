# Task 6 · fix 轮次 1（双轴审合并：2 Important + 4 Minor + 1 条编排层交办）

> 基线 `cbe6aa3`（Task 6 首轮）· 本轮**未动** `proposal.md` / `design.md` / `specs/` /
> `tasks.md` / `superpowers-plan.md`。
> 本体报告 `task6-stage3-conditional.md` 已按本轮结论**就地订正**（B/C/D/E/F/G）。

---

## 🔴 G · 票级偏离：如实写进本体报告，交人认账

**复审指出（成立）**：`tasks.md` 的 **8.1 / 8.3 / 8.4 与 8.2 同在**
「阶段三 · 产品化（阶段二达标才做）」这一个标题之下（实读 `tasks.md:86-96`），
而 Task 6 票面首句是「仅当 Task 5 判 GO 时执行；判回退则本票不执行」。

⇒ 「①③④ 在回退下依然该做」是**编排层（主 session）的裁定**，**不是 `tasks.md` 分节的字面**；
且本票据此**改了生产代码**（`setup.sh`）。

**旁证（实读，不构成授权）**：`tasks.md` §9 头部自带
「〔窄复核订正：原挂在阶段三下，会随阶段二失败一起搁浅〕」——
说明「阶段三分节下的条目会随阶段二失败一起搁浅」在本 change 里被认定为**需要修正的形态**，
而修正手段是**把条目移出阶段三**，不是「由执行者临场判定它该不该做」。本票走的是后者。

**处置（编排层已定，照做）**：**不回退**（净收益为正 —— 8.3 的实跑捞出一个使回滚**正序**
静默失效的真洞），但已在本体报告 **§0.0（开头第一节）** 显著写明知情偏离与
「认账权在人 / 可 revert 本票的 `setup.sh` 与文档改动」。

**登记 `T241`**（`change: add-sdflow-spec`）：`tasks.md:96` 的阶段三验收门
**只有 ✅ 分支、无 ❌/回退分支**（对照：阶段二验收门 `tasks.md:82-83` 同时写了 ✅/❌ 两支）
⇒ 回退形态下「可进 `/sdflow-done`」在票面上**无书面出处**，须在 archive 阶段补该分支。

---

## 🔴 A [Important] · `rm -f` / `ln -snf` 失败 + `set -e` ⇒ 中止整个 setup

### A.1 复现（TDD 红）

新增用例 `hack/tests/test_install_agents.py::test_a_readonly_dest_degrades_to_skip_and_does_not_abort_setup`
——落点**已存在但只读**（`chmod 555`）+ 一条同形状**悬空**链。先跑，红：

```
E  AssertionError: 落点只读竟中止了整个 setup.sh：
E    ln: …/home/.claude/agents/sdflow-local-researcher.md: Permission denied
E  assert 1 == 0
1 failed, 7 passed
```

（顺带这次红也是 **B 的实测证据**：修复前该文件 `1 failed, 7 passed` = **7** 个用例，不是 8。）

**为什么已有的 ⑥ 号用例照不到**：它构造的是「落点被占为**普通文件**」⇒ 卡在 `mkdir -p`，
而那一格**已经**降级过了。落点**建得出来、写不进去**是另一条控制流：`mkdir -p` 对已存在目录
返回 0 ⇒ 一路走到 `ln -snf`（铺设）与 `rm -f`（孤儿清理），这两处当时都是**裸调用**。

### A.2 修法（面治：`install_agents()` / `cleanup_agent_orphans()` 全过一遍）

逐条过了两个函数里**每一个**会在 `set -e` 下中止全脚本的调用：

| 调用 | 位置 | 处置 |
|---|---|---|
| `mkdir -p "$dest"` | `install_agents` | **首轮已降级**（`2>/dev/null \|\| { skipped+=…; return 0; }`），无需改 |
| `ln -snf "$f" "$target"` | `install_agents` | 🔧 **本轮改**：`if ! ln … 2>/dev/null; then skipped+=(…); continue; fi` |
| `rm -f "$entry"` | `cleanup_agent_orphans` | 🔧 **本轮改**：`if ! rm … 2>/dev/null; then skipped+=(…); continue; fi` |
| `link="$(readlink … 2>/dev/null \|\| true)"` | 两处 | 已有 `\|\| true` 兜底，安全 |
| `find … ` （`done < <(find …)`） | 两处 | 进程替换的退出码不被 `set -e` 检查，安全 |
| `basename` / `[ … ]` / `case` / `continue` / 数组 `+=` | 两处 | 不构成中止路径 |
| Windows 分支 `if [ -d "$src_dir" ]; then … fi` | `install_agents` | 首轮已是 `if/fi`（非 `[ … ] && …`），安全 |

⇒ 面上**只有 `ln` 与 `rm` 两处**是裸的，两处一并按同一取向（skip + 汇总）处理。

依据 = `CLAUDE.md` 同文件既定取向（外来同名条目 ⇒ skip + 汇总报告，MUST NOT 中止 setup），
以及 `install_agents` **排在 `install_sdflow` 之前**这一事实：中止 ⇒ `~/.sdflow/` 的
canonical 与 hack 脚本全装不上，用户只看到一行裸 `ln:` / `rm:` 错误。

复审提到「新增的 `! -d src_dir` 分支扩大了可达面（该路径下 dest 从未被 mkdir 校验）」——
成立，且**正是本轮修的第二处**（该路径直接进 `cleanup_agent_orphans`，唯一的写操作就是 `rm -f`）。

### A.3 修后（绿）

```
$ /usr/bin/python3 -m pytest hack/tests/test_install_agents.py -q -p no:randomly
........                                                                 [100%]
8 passed in 10.52s
```

### A.4 定点删门变异回验（判据：**期望红 ⊆ 实际红**）

变异**全部在 scratchpad 的软链农场**里做（农场顶层条目软链回真仓，**唯独 `setup.sh` 是可变异的
真文件拷贝**；`REPO_DIR="$(dirname $0)"` ⇒ 指向农场）。**工作树一字未动，全程 `HOME=` 假目录。**

| 变异 | 期望 | 实测 |
|---|---|---|
| **baseline**（修复后原样） | exit 0 + 4 条 `agents/*` 进 skipped | ✅ `exit=0`，skipped 4 条（3 条「软链建不出来」+ 1 条「悬空链清不掉」） |
| **M1** 把 `ln` 守卫改回裸 `ln -snf` | 红 | ✅ `exit=1`，`ln: …: Permission denied`，skipped 0 条 |
| **M2** 把 `rm` 守卫改回裸 `rm -f` | 红 | ✅ `exit=1`，`rm: …: Permission denied`，skipped 0 条 |
| **M3** 两处守卫同时撤掉 | 红 | ✅ `exit=1`，`ln: …: Permission denied`，skipped 0 条 |

🔴 **M2 单独也红** ⇒ 两处守卫**各自独立**被锚住，不是「一处红顺带盖住另一处」（非恒真锚）。

baseline 的 skipped 全文（截自实跑）：

```
⚠ agents/sdflow-local-researcher.md @ …/.claude/agents — 软链建不出来（落点只读？权限？），未铺设
⚠ agents/sdflow-spec-writer.md      @ …/.claude/agents — 软链建不出来（落点只读？权限？），未铺设
⚠ agents/sdflow-web-researcher.md   @ …/.claude/agents — 软链建不出来（落点只读？权限？），未铺设
⚠ agents/sdflow-gone-agent.md       @ …/.claude/agents — 悬空链清不掉（落点只读？权限？），未清理
```

**隔离核验**：真实 `~/.claude/agents/` 跑前跑后各 `ls -la` 一次 —— 三条指向本仓的有效软链、
0 悬空，前后一致；`git worktree list` 无额外 worktree。（`fake_home` fixture 本身也对真实目录
拍快照并断言不变，新用例同样受其保护。）

---

## 🔴 B [Important] · 「8 个用例 / 8 passed」实测是 7

### B.1 实测

```
$ git show cbe6aa3^:hack/tests/test_install_agents.py | grep -c '^def test_'   → 6
$ git show cbe6aa3 :hack/tests/test_install_agents.py | grep -c '^def test_'   → 7
$ grep -c '^def test_' hack/tests/test_install_agents.py                       → 8   （本轮 fix1 之后）
```

⇒ 首轮报告的「该文件第 8 个用例」「8 passed（原 7 + 新增农场用例）」**均为 7**；
且首轮 §3.4(c) **自贴**的定点删门输出「1 failed, 6 passed」= 7，**自相矛盾**。

### B.2 修法

- **`CLAUDE.md`：删掉数字**（本仓既定手法「删掉数字、让脚本自己报」，本 change 已用过）：
  `（全仓首个 setup.sh 测试；**用例数不写死在这里**——以 pytest 自己报的为准）`。
  顺带把 A 的教训写成一条纪律（`mkdir`/`ln`/`rm` 一律降级为 `skipped[]`，因为
  `install_agents` 排在 `install_sdflow` 之前）。
- **本体报告**：三处（§3.4(c) 正文、变异输出注记、§7 验证记录表）改成实测值 + 订正说明。

### B.3 面治：全量 grep（**不加 `--include`**）扫本 change 引入的所有硬编码计数

```
$ grep -rn "8 passed\|8 个用例\|第 8 个用例\|个用例" --exclude-dir=.git .
$ git diff main...HEAD -- . ':!openspec/changes' | grep "^+" \
    | grep -E "[0-9]+\s*(个用例|个文件|个投放面|处|条)|[0-9]+ passed"
```

本 change 在**非 change 目录**里引入的计数只有三处，逐条核过：

| 出处 | 文本 | 判定 |
|---|---|---|
| `CLAUDE.md:145` | 「8 个用例」 | ❌ **错（实为 7）→ 已删数字** |
| `hack/tests/test_canonical_entry_sync.py` | 「当前实测 17 处：SKILL.md 侧 9 …」 | ✅ 保留 —— 是**变异实测记录**（写明「当前实测」），且该守卫本身以**下限**方式机械自守，不是被引用的权威计数 |
| `sdflow-devenv` 相关注释 | 「这 6 条用例断言的是…」 | ✅ 保留 —— 描述**同一个 `parametrize` 的固定枚举**，随枚举一起改，非跨文件断言 |

其余命中全在 `openspec/changes/archive/**`（历史归档，非本 change 引入）。

### B.4 `CLAUDE.md` / `AGENTS.md` 逐字守卫

`test_two_human_carriers_are_verbatim_identical` 守的是**「阶段一入口」小节**
（`hack/tests/test_canonical_entry_sync.py:426`，`entry_section()` 取的就是那一节）。
本轮改的是 `CLAUDE.md` 的**「`setup.sh` 安装机制」小节**，**不在该守卫辖区**；
且 `AGENTS.md` 对应段（`:79-84`）**从未写用例数**（全量 grep 零命中）⇒ 无需同步。
全仓 pytest 复跑确认该守卫仍绿。

---

## C [Minor] · `sdflow-spec/SKILL.md`「零内容删减」不成立

### C.1 实测：重排究竟丢了什么

`git show cbe6aa3^:sdflow-spec/SKILL.md` 与当前版逐字比：

| 原文 | 重排后 | 性质 |
|---|---|---|
| `openspec/changes/add-sdflow-spec/impl-reports/task5-ab-comparison.md` | `add-sdflow-spec/impl-reports/task5-ab-comparison.md` | **从仓根不可解析** |
| 三个 agent 定义、`install_agents()` **与其守卫** | 三个 agent 定义与 `install_agents()` | 丢限定词 |
| `tasks.md` **阶段二验收门的**失败分支 | `tasks.md` 失败分支 | 丢限定词 |
| **本节**仅在人明确指示启用**外派**时生效 | 仅在人明确指示启用时生效 | 丢限定词 |

⇒ 「零内容删减」**不成立**，已在本体报告 §1.3 就地订正。

### C.2 修法

四处**全部恢复**（完整可解析路径 + 三处限定词）。同族的两处顺带补全（同一批重排引入）：

- `SKILL.md:271` 的「见 … 与 **task6 报告** 的正反两向实跑」→ 补全为
  `openspec/changes/add-sdflow-spec/impl-reports/task6-stage3-conditional.md`。
- `setup.sh:138` 注释里同样被截短的那条报告路径 → 补全。

**行数未超**：恢复的字都落在既有长行内 ⇒ `wc -l sdflow-spec/SKILL.md` = **598** ≤ 600，
**没有再靠截断引用路径省行**。

---

## D [Minor] · 「≤600 行门可由重排换行规避」⇒ 该门对本文件已无约束力

**如实登记，本轮不改门**（改门是设计决策，属加宽）：

- 本体报告 §1.3 与 §6「诚实边界」第 9 条各记一处。
- 登记 **`T242`**（`change: add-sdflow-spec`）：门以 `wc -l` 计 ⇒ 重排软换行即可规避
  （`604 → 598` 就是这么来的），且该文件既有最长行 200+ 字符、无行宽门可依；
  并且它**无机械覆盖**——实测 `grep -rn 600 hack/tests/*.py` 零命中，
  唯一出处是 `tasks.md:33` 里一句人跑的 `wc -l`。
  修法候选（需人拍板）：① 改计字符/字节；② 加行宽上限联判；③ 承认它是软提示、从验收门降为注记。

---

## E [Minor] · 「顺带修了 `set -e` 隐患」归因不准

**实读原代码**（`git show 317bb0f:setup.sh`）：`install_agents()` 开头是
`[ -d "$src_dir" ] || return 0`，Windows 分支里是**无条件**的 `skipped+=(…)` + `return 0`。
⇒ **原代码里根本没有** `[ -d … ] && skipped+=(…)` 这个构造，也就无「既有 bug」可修。

修法：本体报告 §3.4(b) 改述为「**在新写的代码里避开**该隐患」，不是「顺带修 bug」。

## F [Minor] · 同一处的第二重归因错误

那个 `if [ -d "$src_dir" ]` 条件**是移除顶部 `[ -d … ] || return 0` 之后的必需后果**
（早退没了 ⇒ Windows 分支必须自己判源目录在不在，否则源目录不存在时也会报一行 skipped）；
写成 `if/fi` 而非 `[ … ] && …` 只是**实现该必需条件时的写法选择**。
⇒ 与 E 合并订正在本体报告 §3.4(b) 的同一条 bullet 里。

---

## 落盘清单（本轮）

| 文件 | 改动 |
|---|---|
| `setup.sh` | `ln -snf` 与 `rm -f` 两处裸调用 ⇒ 失败降级为 `skipped[]` + `continue`（A）；注释里被截短的报告路径补全（C） |
| `hack/tests/test_install_agents.py` | 新增 `test_a_readonly_dest_degrades_to_skip_and_does_not_abort_setup`（A，含定点删门法说明） |
| `CLAUDE.md` | 删掉写死的用例数 + 补「三处外部命令一律降级为 skip」纪律（A/B） |
| `sdflow-spec/SKILL.md` | 恢复完整可解析路径 + 三处限定词（C）；仍 598 行 |
| `openspec/issues/todolist/2026-07-todolist.md` | **T241**（阶段三验收门缺 ❌ 分支，archive 阶段做）、**T242**（≤600 行门可被重排规避） |
| `impl-reports/task6-stage3-conditional.md` | 就地订正：新增 §0.0 票级偏离（G）、§0 三项/一项计数、§1.3（C/D）、§3.4(b)（E/F）、§3.4(c) 与 §7（B）、§6 诚实边界 +9/+10 |
| 本报告 | 新增 |

---

## 验证记录

| 项 | 命令 | 结果 |
|---|---|---|
| TDD 红 | `pytest hack/tests/test_install_agents.py -q -p no:randomly`（修 `setup.sh` 前） | **1 failed, 7 passed** —— `ln: … Permission denied`，`assert 1 == 0` |
| TDD 绿 | 同上（修后） | **8 passed** |
| 变异回验 | scratchpad 软链农场 · M1/M2/M3 | 三个变异**全部 exit=1**；baseline exit=0 + 4 条 skipped（详见 §A.4） |
| 全仓 pytest | `git add -A && /usr/bin/python3 -m pytest -q -p no:randomly` | **2778 passed, 10 skipped, 3 xfailed**（首轮 2777 + 本轮新增 1；**零红**，`test_two_human_carriers_are_verbatim_identical` 亦绿） |
| setup.sh 真跑 | `bash setup.sh` | **exit 0**；三条 agent 软链 ✓ 铺出，`hack/*` 与 canonical 全装上 |
| 通则托管 | `/usr/bin/python3 hack/sync_principles.py --check` | ✅ **22 个投放面全部一致**（另 `gen_workflow_guide --check` ✅、`check_async_branch_parity` ✅） |
| SKILL 体量 | `wc -l sdflow-spec/SKILL.md` | **598** ≤ 600 |
| 隔离 | `ls -la ~/.claude/agents/` 跑前 / 跑后 | 三条指向本仓的有效软链、**0 悬空**，前后一致 |

> 已知环境抖动用例（`test_outside_voice_job.py::test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret`）
> 本轮**未出现**红，如实记录。

## 诚实边界

1. **只读落点只以「目录 `chmod 555`」这一种成因验过**（macOS）；ACL / 只读挂载 / SIP
   等其它「写不进去」的成因**未逐一实测**——判为同一条 errno 路径，逐个造场景成本不成比例。
2. **本用例在 root 下无区分力**，已显式 `pytest.skip`（root 无视目录写权限位）。
   ∴ 若 CI 以 root 跑，这一格是**静默跳过**，不是绿。
3. **Windows 分支仍无机械覆盖**（承首轮同一条边界，本轮未改变）。
4. **G 的处置是「不回退 + 交人认账」，不是「已获授权」**——偏离仍然存在，
   人若判定不该做，可 revert 本票的 `setup.sh` 与文档改动。
5. **本报告自身**在最后一次全量之后定稿 ⇒ 若有守卫扫报告正文，须以 commit 后的那次为准
   （本轮已按契约先 `git add -A` 再跑全量）。
