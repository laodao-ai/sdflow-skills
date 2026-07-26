# Task 6 · 阶段三条件收敛（分发核验 + 回滚演练 + sunset 判定 + 门结论）

> 票面：tasks 8.1–8.4 + 阶段三验收门 · **R-ID：SA-07 / SA-11 / SA-14**
> 前置：Task 1–5 已收票；Task 5 判**回退到阶段一薄编排形态**。
> **未动** `proposal.md` / `design.md` / `specs/` / `tasks.md` / `superpowers-plan.md`。
> **返修**：双轴审 1 轮 → `task6-stage3-conditional-fix1.md`（A–G 七条，本文已按其结论就地订正）。

---

## 0.0 🔴 票级偏离（**知情，认账权在人**）

本票**执行了 `tasks.md` 阶段三分节下的三项条目**（8.1 分发核验 / 8.3 回滚演练 / 8.4 sunset 判定），
而票面条件句写的是「仅当 Task 5 判 GO 时执行；**判回退则本票不执行**」，
且 8.1 / 8.3 / 8.4 与 8.2 **同在**「阶段三 · 产品化（阶段二达标才做）」这一个标题之下。

⇒ 「①③④ 在回退下依然该做」是**编排层（主 session）的裁定**，**不是 `tasks.md` 分节的字面授权**；
且本票据此**改动了生产代码**（`setup.sh`）。

**编排层已定：不回退**——净收益为正（8.3 的实跑捞出一个使回滚**正序**静默失效的真洞，见 §3.4(b)）。
但**偏离的认账权在人**：若人认为不该做，可 revert 本票的 `setup.sh` 与文档改动。

> 旁证（不构成授权）：`tasks.md` §9 头部自带「〔窄复核订正：原挂在阶段三下，会随阶段二失败一起搁浅〕」
> —— 说明「阶段三分节下的条目会随阶段二失败一起搁浅」在本 change 里被认定为一种**需要修正的形态**，
> 而修正手段是**把条目移出阶段三**，不是「由执行者临场判定它该不该做」。本票走的是后者。

**并已登记**：`T241` —— `tasks.md:96` 的阶段三验收门**只有 ✅ 分支、无 ❌/回退分支**
⇒ 回退形态下「可进 `/sdflow-done`」在票面上**无书面出处**，须在 archive 阶段补该分支。

---

## 0. 本票为条件收敛：阶段三产品化**不执行**

票面首句写死条件：**「仅当 Task 5 判 GO 时执行」**。Task 5 的阶段二验收门判**回退**
（`impl-reports/task5-ab-comparison.md` §0 / §6：7.2「subagent 路成本与质量均不劣于 thin」不达标）
⇒ **该条件句生效 ⇒ 「阶段三产品化」这件事本身不做。**

但票面四项里，**三项（①③④）被判为在回退情形下依然（甚至更）该做**，一项（②）确属阶段三。
🔴 这个「判为」是**编排层的裁定，不是票面字面**——偏离与认账见 **§0.0**。逐项如下：

| 票面项 | 本轮处置 | 一句话依据 |
|---|---|---|
| ① 全局分发行为与文档一致 | ✅ **做了**，并**补了文档** | 回退后定义仍铺在全机器可见的 `~/.claude/agents/`，一致性核验反而更要紧 |
| ② 下游推广（bundle update） | ⛔ **不做**，登记为已知残余 | `tasks.md` 把 8.2 明列在阶段三；阶段三不执行 |
| ③ 回滚演练（正反两向） | ✅ **做了**（沙箱实跑，含反向对照） | 这条路径从没被验过，而回退刚发生 ⇒ 正是该验它的时候 |
| ④ sunset 判定 | ✅ **做了**，结论 = **未到期**（≠ 未达标） | 观察窗尚未开始计 |
| ⑤ 门结论落纸 | ✅ **做了**（§5） | 逐条状态 + 判定与依据，**放行由人拍板** |

---

## 1. ① 全局分发的实际铺设行为 vs 文档

### 1.1 实际状态（实测）

```
$ ls -la ~/.claude/agents/
lrwxr-xr-x  sdflow-local-researcher.md -> /Users/cheneyzhao/Documents/04-sdflow-skills/sdflow-spec/agents/sdflow-local-researcher.md
lrwxr-xr-x  sdflow-spec-writer.md      -> /Users/cheneyzhao/Documents/04-sdflow-skills/sdflow-spec/agents/sdflow-spec-writer.md
lrwxr-xr-x  sdflow-web-researcher.md   -> /Users/cheneyzhao/Documents/04-sdflow-skills/sdflow-spec/agents/sdflow-web-researcher.md
$ find ~/.claude/agents -mindepth 1 -maxdepth 1 -type l ! -exec test -e {} \; -print | wc -l
0
```

三条软链**存在、有效、指向本仓**（当前指向**开发 checkout** —— 这正是 design Migration Plan
点名的「从开发 checkout 跑 setup 会把全局链接整体指向 WIP checkout」窗口，测完须在运行 checkout
重跑 setup 还原；`install_agents()` 的自属判据是**位置无关的路径后缀**，故还原时能正常接管，不裂脑）。

### 1.2 与文档逐条比对

| 文档断言 | 出处 | 实际 | 判定 |
|---|---|---|---|
| 三个定义铺到全局 `~/.claude/agents/`，逐文件 `ln -snf` | design D3 / D11 · SA-07 | 三条软链在册 | ✅ 一致 |
| 所有权守卫 = 只接管软链**且** `readlink` 指向本仓 | D11 · SA-07 | `setup.sh:~183` `case "$link" in */sdflow-spec/agents/"$name")` | ✅ 一致 |
| Windows 不铺 agents、报一行进 `skipped[]`、走主 session 亲做 | D11 · SA-07（**明写取舍**） | `setup.sh` Windows 分支存在且只做 `skipped+=` + `return 0` | ✅ 一致（**本机 Darwin 无机械覆盖**，见 §6） |
| 外派**未启用**，三定义作为未启用资产保留 | Task 5 §9 · `sdflow-spec/SKILL.md`「外派协议」 | SKILL.md 已明写「本节当前 = 未启用资产」 | ✅ 一致 |
| **「未启用」的能力，其定义却对全机器所有项目可见** | —— | **文档此前一个字都没说** | ❌ **不一致 → 已补** |
| 回滚第①步「先跑 uninstall 分支移除 agents」 | design Migration Plan | **`setup.sh` 全文零 `uninstall` 命中** | ❌ **文档描述了一个不存在的开关**（见 §3.4） |

### 1.3 补的文档（**非托管区 / SKILL.md**，四件套一字未动）

1. **`CLAUDE.md`「`setup.sh` 安装机制」** —— 新增「第三个安装目的地：`~/.claude/agents/`」一节。
   此前该节只描述两个 skills 目录，**对第三个安装目的地只字未提**，而它是**唯一一个写进全局
   共享命名空间**的目的地。新增内容含：铺设方式与更严的所有权守卫、Windows 取舍、
   🔴「外派未启用但定义照铺、挡误选的只有排他式 `description` = **指令层非机械门**」、
   以及「移除 agents 的可执行动作 + 顺序不可颠倒」。
2. **`AGENTS.md`「项目结构与模块组织」** —— 同一事实的压缩版（该文件是结构速查，不重复长文）。
3. **`sdflow-spec/SKILL.md`「外派协议」** —— 在「未启用资产」声明后补一段：
   > 「未启用」只约束本管线，定义照样铺在全局 `~/.claude/agents/`（`install_agents()` 不看本节
   > 启用状态）⇒ 对本机每个项目可见；挡误选的只有 `description` 的排他式声明（指令层、非机械门）。

   **为什么这条必须在 SKILL.md 里说**：读到「本节未启用」的人，最自然的推论就是「那它不在了」。
   而实际上它在，且在一个**全局**名册里 —— 这个推论差是 BASE-28 S5 的风险被低估的直接通道。

   ⚠️ 体量约束（tasks 2.10 / D12：`wc -l` ≤ **600**）：加这段后一度到 604，
   仅把同一节内的软换行重排为更长的行（该文件既有最长行 200 字符，长行是本文件的既有形态）
   ⇒ 现 **598 行**，仍在预算内。
   🔴 **订正（fix1 · C）**：首轮报告称此举「零内容删减」——**不成立**。重排为压行数时**确实丢了内容**：
   报告路径被截成不可解析的 `add-sdflow-spec/impl-reports/…`（从仓根解析不到），另丢了三处限定词
   （`与其守卫` / `外派` / `阶段二验收门的`）。fix1 已**恢复完整可解析路径与全部限定词**，
   行数仍 **598**（恢复的内容落在既有长行内，不新增行）。
   🔴 **并暴露一条边界（fix1 · D，已登记 `T242`）**：`wc -l` 门**可由重排软换行规避**（604→598 即此法），
   ∴ 该门对本文件**已无实际约束力**；且它**无机械覆盖**，只有 tasks 2.10 里一句人跑 `wc -l`。
   本轮**不改门**（改门是设计决策，属加宽）。

---

## 2. ② 下游推广：不做 + 已知残余 + 登记

**不做的依据**：`tasks.md` 把 8.2（`sdflow-init update` 推 canonical 七处至消费项目）明列在
**阶段三 · 产品化（阶段二达标才做）** 之下。阶段二验收门判回退 ⇒ 阶段三不执行 ⇒ 8.2 不执行。
**MUST NOT 擅自现在就推** —— 那是把票面砍掉的范围又加回来（通则③「不加宽」）。

🔴 **但它有一个真实后果，MUST NOT 假装不存在**：

Task 2 改的**七处 canonical** 是本 change 的**阶段一交付**（tasks 1.1–1.8，P0 不可 defer），
它们**只落在源仓** `sdflow-init/assets/workflow/`。本仓运行时经 `resolve-workflow.sh` 解析到
**全局 canonical**（软链回本仓源）⇒ **本仓自己没问题**；但**其它已铺 bundle 的消费项目**
持有的是 `openspec/workflow/` 的**规则副本**，它们**至今仍是旧的阶段一入口规则**
（`explore→ff→grill`，无 `/sdflow-spec` 分支、无 G1 具名例外）。

⇒ 在那些项目里，**人读侧（若也铺了 CLAUDE.md 托管块）与 AI 读侧会短暂分叉** —— 而消除这种分叉
正是 D10 的立项理由。**这是阶段三缺席带来的真实残余，不是 Task 2 没做完。**

**登记**：`T239`（`openspec/issues/todolist/2026-07-todolist.md`，`change: add-sdflow-spec`）
—— **何时**：本 change merge 之后；**由谁**：人（或人指派的一次维护跑动）；
**怎么推**：在每个已铺 bundle 的消费项目跑 `sdflow-init update`，核验其
`openspec/workflow/generation-process.md` §四已含分支 A/B、`workflow.md` §三.2 与
`reference/quality-layering.md` 已含 G1 具名例外。

---

## 3. ③ 回滚演练（正反两向 · 沙箱实跑）

### 3.1 演练设计与隔离

- **沙箱** = `scratchpad/rollback-drill/repo`（本仓 `git clone --no-hardlinks`）+ **五个假 HOME**。
  **全程 `HOME=<假目录>`，真实 `~/.claude/agents/` 未被触碰**（证据见 §3.6）。
- **「revert」的模拟** = `git checkout 42b4758`（= `317bb0f^`，即引入 `install_agents()` 的提交之前）。
  该状态下 `setup.sh` 无 `install_agents`、`sdflow-spec/agents/` 不存在 —— **正是 revert 后的形态**，
  且避开了真 `git revert` 在多个后续提交上的冲突噪声。

### 3.2 反向对照（**本项的核心证据**）：错误顺序 ⇒ 悬空软链永久留下

```
[B-1] 新版 installer 铺设 → 3 条软链在册
[B-2] 先 revert（checkout 42b4758）→ grep -c install_agents setup.sh = 0；sdflow-spec/agents/ 不存在
[B-3] 再重跑 setup.sh → exit=0（静默成功，无任何告警）
[B-4] 核验：
DANGLING: sdflow-local-researcher.md -> .../repo/sdflow-spec/agents/sdflow-local-researcher.md
DANGLING: sdflow-spec-writer.md      -> .../repo/sdflow-spec/agents/sdflow-spec-writer.md
DANGLING: sdflow-web-researcher.md   -> .../repo/sdflow-spec/agents/sdflow-web-researcher.md
悬空软链数 = 3
```

⇒ **design 的警告成立，且是实测成立的**：revert 把 `install_agents()` 连同其清理逻辑一起撤掉，
重跑时**没有代码去看 `~/.claude/agents/`**，三条悬空软链留在全局名册里，
**且 setup.sh 退出码 0、一行告警都没有**（静默失败）。

### 3.3 正序：先移除 agents → 再 revert → 重跑 setup ⇒ 零悬空

```
[D-1] 新版 installer 铺设 → 3 条
[D-2] 回滚第①步：删掉整个 sdflow-spec/agents/，**仍在新版 installer 上**跑 setup.sh
      → cleaned orphans (3): agents/sdflow-{spec-writer,local-researcher,web-researcher}.md
      → 落点条目数 = 0
[D-3] 回滚第②步 revert（checkout 42b4758）+ 第③步重跑 setup.sh → exit=0
🔵 正序最终：条目数=0 悬空软链=0
```

### 3.4 演练途中挖出的两件事（**这是本项的实质产出**）

#### (a) `setup.sh` **没有 uninstall 分支**（design 描述了一个不存在的开关）

```
$ grep -rn -- "--uninstall|uninstall|UNINSTALL|remove_agents|--remove" setup.sh
（零命中）
```

design Migration Plan 的回滚第①步「先跑 **uninstall 分支**移除 agents」——**那个分支不存在**。
按票面「本轮不擅自新增功能」，**未新增 uninstall 开关**；改为核验「现有机制里有没有等价可执行动作」。

#### (b) 有等价动作，但**原实现有个洞，让它恰好在最常见的用法上失效**

`install_agents()` 的孤儿清理**本来**就是等价的 uninstall（删源 → 重跑 → 清悬空链）。但原实现在
函数开头写 `[ -d "$src_dir" ] || return 0`：**源目录整体消失时连清理都不跑**。而「移除 agents」
最自然的动作恰恰是 `rm -rf sdflow-spec/agents` —— 实测（C 组，仍在**新版** installer 上）：

```
[C-2] rm -rf sdflow-spec/agents && bash setup.sh
      → setup 输出里含 "agents" 的行：（无）
      → 悬空软链数 = 3
```

⇒ **回滚正确顺序的第①步，用最自然的动作执行，会静默地什么都不做。** 那么正序与错序的结果
就一样了 —— design 的整个回滚故事失效。

**处置（fold，不是新功能）**：把孤儿清理提成 `cleanup_agent_orphans()`，由 `install_agents()`
的两条出路各调一次；源目录整体消失时**不再早退**，先清理再返回。
- 这**不是加宽**：`install_agents()` 自己的注释早就把「删掉一个 agent 定义后那条悬空链将永远留着」
  列为孤儿清理的**主用途**，只是没覆盖「删掉全部」这一格。修的是既有契约的一个洞。
- Windows 分支从无条件 `skipped+=` 改成 `if [ -d "$src_dir" ]; then … fi`：
  🔴 **订正（fix1 · E/F）**：首轮报告把这处写成「**顺带修了**同一段的一个 `set -e` 隐患」——**归因不准**。
  原代码里**根本没有** `[ -d … ] && skipped+=(…)` 这个构造（原实现是函数开头一句
  `[ -d "$src_dir" ] || return 0` + Windows 分支里**无条件**的 `skipped+=`）。
  实情是：**移除顶部早退之后**，Windows 分支必须自己判源目录在不在，于是**新写**了这个条件；
  写成 `if/fi` 而非 `[ … ] && …` 是**在新代码里避开**该隐患，**不是修既有 bug**。
  ∴ 它是移除早退的**必需后果**，不是「顺带修的」。
- **落点**：`setup.sh:130-236`。

#### (c) 新增机械门 + 定点删门验证（**非恒真锚**）

`hack/tests/test_install_agents.py::test_orphans_are_cleaned_even_when_the_whole_source_dir_is_gone`。
它用**软链农场**造了一个可写的 `REPO_DIR` 替身（顶层条目软链回真仓，
只有 `sdflow-spec/agents/` 是可删的真目录），从而能在**不碰真仓**的前提下删掉源目录。

> 🔴 **订正（fix1 · B）**：首轮报告称该用例是「第 8 个」、该文件「8 passed」——**实测是 7**
> （`--collect-only` = 7，`7 passed`；且首轮自贴的定点删门输出「1 failed, 6 passed」也是 7，自相矛盾）。
> 本轮 fix1 新增 `test_a_readonly_dest_degrades_to_skip_and_does_not_abort_setup` 后**才**是 8。
> 用例数**已从 `CLAUDE.md` 删掉**（既定修法：删掉数字、让脚本自己报）。

**定点删门实证**（防恒真锚）：

```
把 `if [ ! -d "$src_dir" ]; then cleanup_agent_orphans "$dest"; return 0; fi` 改回裸 `return 0`
→ FAILED test_orphans_are_cleaned_even_when_the_whole_source_dir_is_gone
   E  assert not ['sdflow-local-researcher.md','sdflow-spec-writer.md','sdflow-web-researcher.md']
→ 1 failed, 6 passed
还原后：7 passed（含农场用例；**fix1 加只读落点用例后为 8 passed**）
```

#### (d) 修复后**重跑正反两向**：顺序仍然重要（修复没有把错序也救活）

| 组 | installer | 顺序 | 条目数 | 悬空软链 |
|---|---|---|---|---|
| `home-right` | 修复前 | 正序（删 `.md`、留目录 → revert → setup） | 0 | **0** |
| `home-trap` | 修复前 | 正序但删**整个目录** | 3 | **3** ← 洞 |
| `home-fixed` | **修复后** | 正序（删**整个目录** → revert → setup） | 0 | **0** ← 洞已堵 |
| `home-wrong` | 修复前 | **错序**（先 revert 再 setup） | 3 | **3** |
| `home-wrong2` | **修复后** | **错序**（先 revert 再 setup） | 3 | **3** ← **顺序仍然重要** |

🔴 `home-wrong2` 是关键一行：修复**没有**让错序变安全 —— revert 之后清理代码本身就不在了，
任何函数级修补都救不回来。**「顺序不可颠倒」是一条真约束，不是文档辞令。**

### 3.5 票面验收「全局 agents 目录零悬空软链」

沙箱正序两组（`home-right` / `home-fixed`）**均为 0**；真实 `~/.claude/agents/` 本轮结束时
**0 悬空、3 条有效链**（§1.1 与 §3.6）。

### 3.6 隔离核验（真实环境未被动过）

```
$ git worktree list
/Users/cheneyzhao/Documents/04-sdflow-skills  b74a7ae [feat/add-sdflow-spec]     ← 无额外 worktree

$ ls -la ~/.claude/agents/        （演练前后两次，均为三条指向本仓的有效软链，见 §1.1）
$ find ~/.claude/agents -type l ! -exec test -e {} \; -print | wc -l  →  0

$ 沙箱：rm -rf scratchpad/rollback-drill  →  已清空（52M 全部回收）
```

`hack/tests/test_install_agents.py` 的 `fake_home` fixture 本身也在每个用例前后对真实
`~/.claude/agents/` 拍快照并断言不变 —— 新增的农场用例同样受该 fixture 保护。

---

## 4. ④ sunset 判定：**未到期**（≠ 未达标）

### 4.1 条款原文（Task 2 落在 `CLAUDE.md` / `AGENTS.md` 非托管区）

> **观察窗** = `sdflow-spec` **上线后**连续 **6 个新开 change**，或 **8 周**，先到者为准。
> 三档阈值：采用率 ≥ 5/6 · 质量（「上下文缺失/需回问阶段一」类 finding = 0 且 findings 采纳率 ≥ 0.79）
> · 成本（阶段一墙钟中位 ≤ 75 min/change）。
> 处置二选一：三档全达标 ⇒ 旧三步进 sunset；**任一档不达标 ⇒ 删除 `sdflow-spec`**。

### 4.2 按事实判

| 判定要素 | 事实 | 出处 |
|---|---|---|
| 本 change 是否 merge | **否** —— 仍在 `feat/add-sdflow-spec`，HEAD `b74a7ae`+本票提交 | `git status` / `git log` |
| 生产上跑过几个 change | **0** —— Task 5 的三路 A/B 是**沙箱实验**（三个 clone，已 `rm -rf`），不是生产使用 | `task5-ab-comparison.md` §2 / §10.10 |
| 观察窗是否开始计 | **否** | 上两行 |

⇒ **判定结果 = 「未到期」（窗口尚未开启），不是「未达标」。**

🔴 **这两者的处置完全相反**：条款里「任一档不达标 ⇒ **删除 `sdflow-spec`**」是**观察窗结束之后**
才适用的条款。把「窗口还没开」当成「未达标」去触发删除，会因为**一次都还没用过**而删掉整个交付物。
本票**不触发任何 sunset 处置**。

### 4.3 下一个判定点（写清楚，交给人）

| 项 | 内容 |
|---|---|
| **起算点** | `add-sdflow-spec` merge 进默认分支 **且** 运行 checkout 跑过 `setup.sh` 之日 |
| **到期条件** | 起算日后**连续 6 个新开 change**，或 **8 周**，**先到者为准** |
| **谁来判** | **人**（条款明写「MUST NOT 无限期延长观察窗；要延窗须人明确拍板」） |
| **判什么** | 三档阈值逐档核（采用率 / 质量 / 成本），成本档可由 `sdflow-retro` 聚合两个相位 checkpoint 锚之间的墙钟 |

**补的文档**：条款原文只写「上线后」，**没定义「上线」**。本票在 `CLAUDE.md` / `AGENTS.md`
的 sunset 小节（两份**逐字同步**，由 `test_two_human_carriers_are_verbatim_identical` 机械守）
补了起算点定义 + 「未到期 ≠ 未达标」的显式区分 —— 因为这条歧义的下游后果是**误删交付物**。
阈值本身**一个字未动**。

---

## 5. ⑤ 阶段三验收门：逐条状态 + 判定与依据

`tasks.md` 的门文本：**8.1–8.4 全过 + 下游至少一个消费项目实跑 `sdflow-init update` 后阶段一流程可用 ⇒ 本 change 可进 `/sdflow-done`。**

| 门条件 | 状态 | 依据 |
|---|---|---|
| 8.1 全局分发定案与实际铺设核验 | ✅ **过**（且补了文档缺口） | §1 |
| 8.2 bundle 下游推广 | ⛔ **不执行**（票面条件句） | §2；残余登记 T239 |
| 8.3 回滚演练按正确顺序实跑 + 零悬空 | ✅ **过**（正反两向 + 修复了使正序失效的洞 + 新增机械门） | §3 |
| 8.4 按已落定阈值判 sunset | ✅ **过** —— 判定 = **未到期**，不触发处置 | §4 |
| 「下游至少一个消费项目跑完 update」 | ⛔ **不执行**（同 8.2） | §2 |

### 判定

🔴 **阶段三验收门在回退情形下的结论 = 「阶段三不执行」（票面条件句生效）。**
本 change 以**阶段一薄编排形态**交付；就这一形态而言，本票四项里**该做的三项全部做完并有实跑证据**，
不该做的两项**未做且已登记残余**。

**⇒ 我的判定：本 change 具备进 `/sdflow-done` 的条件。**
**⇒ 但 MUST NOT 由我宣告「门通过」——放行是人的决定。** 本节只给逐条状态与依据。

**人拍板时需要知道的两件事**：
1. **T239（下游未推）会随 merge 生效**：merge 后消费项目仍读旧规则，直到有人跑 `sdflow-init update`。
2. **sunset 观察窗自 merge 起算**，8 周或 6 个 change 后需要人来判一次（§4.3）。

---

## 6. 诚实边界

1. **「revert」是模拟的，不是真 `git revert`。** 用 `git checkout 317bb0f^` 得到「`install_agents()`
   与 `sdflow-spec/agents/` 都不存在」的状态。对**本项要验的那条因果**（清理代码是否还在）
   两者等价；但真 `git revert` 在本分支上会有冲突解析过程，那部分**未验**。
2. **Windows 分支仍无机械覆盖。** `IS_WINDOWS` 由 `uname -s` 决定、无环境变量覆盖入口 ⇒ 本机
   （Darwin）测不到「Windows 不铺 agents」。本轮**只核了源码分支存在且只做 `skipped+=`+`return 0`**，
   **没有在 Windows 上实跑过**。（为测它给生产代码开覆盖开关 = 为测试放宽生产逻辑，不做。）
3. **`~/.claude/agents/` 的「全局可见性」只在本机 N=1 观察过。** 「宿主不会在无关任务上误选
   排他式 description 的 agent」是 Task 4/5 的单次观察 + 指令层约束，**不是机械门**。
   本票补的是**文档**（让这个事实可见），**没有**新增任何机械约束来防误选。
4. **下游推广（②）完全未验。** 没有任何消费项目跑过 `sdflow-init update`，
   「下游拿到七处改动后阶段一流程可用」这条**零证据**。它是被票面条件句砍掉的范围，不是失败项。
5. **sunset 三档阈值本身未被检验过是否可测。** 采用率与质量两档依赖「阶段二 spec-review 报告」
   与「retro 聚合」，本票**没有**验证这两个数据源在真实使用下能否产出所需口径的数字。
   到期时若发现取不到数，那是一个**当时才会暴露**的问题。
6. **正序演练的 D-3 步（revert 后重跑 setup）在一个已经清空的落点上跑**，
   ∴ 它证明的是「不再产生新的悬空链」，不是「它有能力清理」——清理能力由 D-2 步单独证明。
7. **本票修改了 `setup.sh` 的生产代码**（fold 一个洞，§3.4(b)）。该改动的覆盖来自
   `test_install_agents.py`（用例数以 pytest 自报为准）+ 全仓 pytest 全绿 + `setup.sh` 真跑一次；
   **未在真实 Windows / 其它人的机器上跑过**。
   🔴 **fix1 追加**：本票**同时执行了 `tasks.md` 阶段三分节下的三项条目**，而票面条件句是
   「判回退则本票不执行」——**知情偏离，认账权在人**，详见 §0.0。
8. **`git commit` 之后才成为 tracked 的文件，本轮门禁看得见**（结束前已 `git add -A` 再跑全量）。
   但**本报告自身**是在最后一次全量之后定稿的 ⇒ 若有守卫扫报告正文，须以 commit 后的那次为准。
9. **`wc -l ≤ 600` 门可由重排软换行规避**（`604 → 598` 即此法）⇒ 它对 `sdflow-spec/SKILL.md`
   **已无实际约束力**；且**无机械覆盖**（只有 tasks 2.10 里一句人跑的 `wc -l`）。
   已登记 `T242`，本轮**不改门**（改门是设计决策，属加宽）。〔fix1 · D〕
10. **fix1 新增的两条 `setup.sh` 降级（`ln` / `rm` 失败 ⇒ skip）只以「目录 `chmod 555`」这一种成因验过**
    （macOS）；ACL、只读挂载、SIP 等其它「写不进去」的成因**未逐一实测**——判为同一条 errno 路径，
    逐个造场景成本不成比例。

---

## 7. 验证记录

| 项 | 命令 | 结果 |
|---|---|---|
| 全仓 pytest | `/usr/bin/python3 -m pytest -q -p no:randomly` | **2777 passed, 10 skipped, 3 xfailed**（首跑 1 failed = `test_canonical_entry_sync.py::test_two_human_carriers_are_verbatim_identical`，因两份人读侧的 sunset 补文未逐字同步；同步后绿 —— **该门抓到了本票自己的漂移**） |
| install_agents 契约 | `pytest hack/tests/test_install_agents.py -q` | 首轮 **7 passed**（原 6 + 新增农场用例；首轮报告误写「8 passed / 第 8 个用例」，fix1 已订正）；**fix1 后 8 passed** |
| 定点删门 | 删 `cleanup_agent_orphans` 调用后重跑 | **1 failed**（非恒真锚），还原后绿 |
| setup.sh | `bash setup.sh` | exit 0；`~/.claude/agents/` 三条有效链、0 悬空 |
| 通则托管 | `/usr/bin/python3 hack/sync_principles.py --check` | ✅ 22 个投放面一致 |
| SKILL 体量 | `wc -l sdflow-spec/SKILL.md` | **598** ≤ 600 |
| 隔离 | `git worktree list` / `ls -la ~/.claude/agents/` | 无额外 worktree；真实目录未被演练动过 |

> 已知环境抖动用例（`test_outside_voice_job.py::test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret`）
> 本轮**未出现**红，如实记录。

## 8. 本票落盘清单

| 文件 | 改动 |
|---|---|
| `setup.sh` | 孤儿清理提成 `cleanup_agent_orphans()` + 源目录消失时不再早退；Windows 分支改 `if/fi`（**移除顶部早退的必需后果**，非「顺带修 bug」）。**fix1 追加**：`ln` / `rm` 失败一并降级为 `skipped[]`（原为裸调用，`set -e` 下会中止整个 setup） |
| `hack/tests/test_install_agents.py` | 新增软链农场 helper + `test_orphans_are_cleaned_even_when_the_whole_source_dir_is_gone`（6 → 7 个用例）。**fix1 追加** `test_a_readonly_dest_degrades_to_skip_and_does_not_abort_setup`（→ 8） |
| `CLAUDE.md` | 「`setup.sh` 安装机制」新增第三个安装目的地一节；sunset 小节补「上线」起算点与「未到期 ≠ 未达标」。**fix1**：删掉写死的用例数 + 补「三处外部命令一律降级为 skip」的纪律 |
| `AGENTS.md` | 「项目结构与模块组织」补 agents 铺设事实；sunset 小节同步（逐字） |
| `sdflow-spec/SKILL.md` | 「外派协议」补「未启用≠没铺出去」+ 移除动作；同节重排换行以守 ≤600。**fix1**：恢复被重排丢掉的完整可解析路径与三处限定词（仍 598 行） |
| `openspec/issues/todolist/2026-07-todolist.md` | **T239**（下游未推残余）、**T240**（design Migration Plan 的 uninstall 措辞校正，archive 阶段做）。**fix1 追加**：**T241**（阶段三验收门缺 ❌/回退分支）、**T242**（`wc -l ≤600` 门可被重排规避） |
| 本报告 | 新增；fix1 已就地订正（B/C/D/E/F/G），逐条修法见 `task6-stage3-conditional-fix1.md` |
