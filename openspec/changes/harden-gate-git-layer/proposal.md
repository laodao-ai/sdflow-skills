## Why

`ship_gate.py` 判定「评审结论是否已失鲜」时，长期从 git 管道信号**推断**「被审过的内容变了没有」。一轮 grill + 一轮多镜设计审（4 镜 + 广审双声 + 2 站点跨模型 voice）在这条链上累计挖出**十个缺陷、全部实测复现**：

| # | 缺陷 | 方向 |
|---|---|---|
| 1 | `git log --name-only` 对 merge 提交不输出路径 ⇒ 整帧跳过 | fail-open |
| 2 | rename detection 默认开，源路径逃出监视集 | fail-open |
| 3 | 非零退出被折叠成空串 ⇒ 零帧 ⇒ 等价「无可疑提交」 | fail-open |
| 4 | `-m` 逐 parent 输出，parent2 常早于锚 ⇒ 重报锚前历史 | 假阳（例行 merge 即误拦） |
| 5 | `--cc` 只报「相对所有 parent 都不同」者 ⇒ 合并结果等于某 parent 时隐身 | fail-open |
| 6 | 控制字符路径被 C-quote 弄花，前缀判定失准 | 两域方向相反 |
| 7 | `diff.ignoreSubmodules=all` ⇒ 未审 submodule bump 判 fresh | fail-open |
| 8 | `GIT_ICASE_PATHSPECS=1` ⇒ 负向 pathspec 误排除真实代码目录 | fail-open |
| 9 | `report_last_sha` = 「最后触碰报告路径的提交」⇒ 任何后续触碰（一个空行、一次 CI reformat）把锚推到未审改动之后 | fail-open |
| 10 | 锚获取的 `run_git` 非零退出折成 `''` ⇒ 判 `uncommitted` ⇒ fresh | fail-open |

**两个根因**：**(一)** 1–8、10 都是「拿 git 管道当内容变更的代理」——4 与 5 互为解药兼病灶，7 与 8 只需一个 config / 一个环境变量即可翻转判定，**在枚举面上补不完**（基准 5 的补丁螺旋）。**(二)** 9 是「拿最后触碰反推锚」。

∴ 本 change **不修补推断链，改掉推断本身**。决策与实证落 `openspec/adr/0026`。

触发 TG：**TG-17**（HR-TG）· TG-14 · TG-18 · TG-19 · TG-22 · TG-23。

## What Changes

### P0 — 录锚，取代反推（解 9、10）

- 三个评审 producer（`/sdflow-spec-review`、`/sdflow-code-review`、`/sdflow-done`）在报告 frontmatter 写 `reviewed_sha: <当时 HEAD>`。
- gate reader 读它：**缺失 / 非 40 位 OID / 对象不存在 ⇒ fail-closed**（`UNKNOWN(6)`）。**MUST NOT 在缺字段时静默回退反推式锚**——回退 = 缺陷 9 原样存活。
- 退役 `report_last_sha`。

### P0 — 比内容，取代路径枚举（解 1–8）

- **design 域**（监视集是固定清单）：`proposal.md`/`design.md`/`tasks.md` 逐个 `git show <锚>:<path>` 与 HEAD 比字节；`specs/` 子树经 `ls-tree -r -z` 枚举后同样逐个比；`tasks.md` 比之前过既有的 `_normalize_checkbox_lines`。
- **code 域**（监视集列不出清单）：比 `git ls-tree` 的**顶层条目**、排除 `openspec` 条目后求等值。**MUST NOT 用整棵树的 sha**——实测 done 写 `verify-report.md` 即改变整树 sha ⇒ 正常流程第一步就假阳。
- 勾选豁免**常开、按内容切、不按阶段切**：`tasks.md` 勾选框的写入方是 **agent 自由行为、不是 SKILL 契约**（前序 change 假设表 A1′ 已证），按阶段切会立刻假失鲜。

> 🔴 **砍的是枚举，不是监视集。** 监视集（只盯四件套 / 只盯非 `openspec/`）是**承重的**——它才是「实现期改源码不该让设计门失鲜」的来源。裸 `reviewed_sha == HEAD` 已实测证伪：实现期每个提交都在动 HEAD ⇒ 设计门从第一个实现提交起永远失鲜。

### P0 — 限定求值窗口（消掉剩余假阳，且**取消整套补偿机制**）

design 域失鲜的风险是「照着一份已经变了的设计继续建」——该风险**只在实现期存在**。∴ design 域失鲜**只在阶段三起手至实现完成期间求值**（`RUN_SOP` / `RUN_PLAN` / `CONTINUE_IMPL`），进入代码审后不再求值。code 域两个检查**已经是「位置即阶段」**（`:1291` 在代码审之后才可达、`:1311` 在 done 之后），无需改动。

窗口内**无合法 churn**（`sdflow-implement` 只读 `design.md`，撞问题走 halt 上抛；全仓历史零个实现期提交改过监视集）⇒ **无需任何逃生口**，判定保持全机械。

> 起草期曾为「后期合法修订」设计过语义分诊 + 重锚协议 + 重锚留痕 + 不可变锚字段，**已随本条整体取消**——那些修订（`[impl-review-fix]`、`opsx:verify` 的「revise design.md to match reality」）本就是工作流明文允许的，gate 拦它只能多加一道仪式。

### P1 — git 调用失败落进退出码契约

- `run_git` / `run_git_rc` / `run_git_bytes` 统一捕获 `OSError`（含 `FileNotFoundError`、`PermissionError`、无效可执行格式）与 `subprocess.TimeoutExpired`，映射 `UNKNOWN(6)`。
- 三处补 `timeout=30`。
- 子进程**清理 `GIT_*` 环境变量**（实测 `ls-tree` 在 `GIT_ICASE_PATHSPECS=1` 下 fatal 罢工）。

### 退役

BR-7（`checkpoint(impl-review)` subject 豁免）、`frame_touched_paths`、帧遍历、`design_frame_exempt_reason`、触发点诊断管道、`report_last_sha`。

### 验证要求（贯穿全部）

每条新增守卫 MUST 附**变异证明**：删掉该守卫 ⇒ 对应用例变红。上一轮的 rename 用例只直接调 `blob_pair`、没走 `is_stale`，因此**在真实洞存在的情况下仍是绿的**——这是本项要求的直接实证来源。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `spec-workflow`: 失鲜判定由「从 git 管道推断路径变更」改为「录锚 + 比内容」，并新增求值窗口约束（判据只在其保护的风险真实存在的阶段求值）；新增 `reviewed_sha` 的 producer/reader 契约与 git 调用失败的退出码契约。

## Impact

- **代码**：`sdflow-ship/scripts/ship_gate.py`（`is_stale` 两分支重写、锚获取、求值窗口、`run_git*` 系列；退役帧遍历与 BR-7）
- **SKILL**：`sdflow-spec-review` / `sdflow-code-review` / `sdflow-done` 的报告模板各加一行 `reviewed_sha`
- **测试**：`sdflow-ship/tests/test_gate_freshness.py`（BR-7 真值表 8 格随 BR-7 退役；新增内容比较、录锚、求值窗口用例）
- **行为变更**：① 此前被误判 fresh 的盘面今后判 stale（**修复**）；② 此前被例行 merge 误拦的盘面今后判 fresh（**修复**）；③ 代码审期与 done 期不再求值 design 域失鲜（**范围收窄**，见 design.md 残余面）
- **迁移**：存量 active 报告无 `reviewed_sha` ⇒ fail-closed ⇒ 须重审一次。在途的只有本 change 自己
- **消费方**：本仓为 toolkit 源仓，改动经 push → 各仓 `/sdflow-upgrade` 后生效

## 需求优先级〔BASE-23 · TG-19〕

| 级 | 项 | 依据 |
|---|---|---|
| **P0** | 录锚（缺陷 9、10） | 安全面：锚可被无声前移 / 读不到 git 就放行。缺陷 9 存在时，其余修复的威胁模型**一行都不成立** |
| **P0** | 比内容（缺陷 1–8） | 安全面 + 可用性面：七个 fail-open + 一个假阳。已全部复现 |
| **P0** | 限定求值窗口 | 可用性面 + **复杂度面**：它把整套补偿机制（语义分诊 / 重锚协议 / 留痕字段）证明成不必要 |
| **P1** | git 调用失败落契约 + `GIT_*` 清理 | 可用性面：退出码脱离契约集致链序误判；无 timeout 致无限阻塞；env 致无故罢工 |

P0 三项同处 `is_stale` 同一函数、同一片面，分开做要付三遍 workflow 循环成本，故合并（基准 4）。P1 动的是同一批 `run_git*`，同理。

## 假设列表〔BASE-14 · TG-22〕

| # | 假设 | 已验证？ | 若不成立 |
|---|---|---|---|
| A1 | 缺陷 1–10 均真实存在 | ✅ 全部本地 fixture 复现，多数经真 `is_stale` 求值 | — |
| A2 | 实现期无合法的四件套实质修订流程 | ✅ `sdflow-implement` 只读 `design.md`，BLOCKED 走 halt 上抛；**全仓历史零个实现期提交（`checkpoint(<change>:taskN-…)`）改过监视集** | 若存在则窗口内需豁免，须回补 |
| A3 | 代码审期与 done 期的四件套修订是工作流明文允许的 | ✅ `[impl-review-fix]` 历史多次实证；`opsx:verify` step 7「revise design.md to match reality」（`.claude/commands/opsx/verify.md:99`） | 若不允许则窗口须延长 |
| A4 | `tasks.md` 勾选的写入方不受阶段约束 | ✅ 前序 change 假设表 A1′「写入方是 agent 自由行为、不是 SKILL 契约」；本仓 20 个 checkpoint 提交碰过 `tasks.md`，散在各阶段 | 若受契约约束则豁免可按阶段切（但无收益） |
| A5 | 失鲜判定有两个 scope、**三个消费方** | ✅ `:1214` design / `:1291` code(code-review-report) / `:1311` code(verify-report)。承 `adr/0011`「MUST grep 列全调用点」 | — |
| A6 | code 域现存测试仅 1 例且走 `verify-report` ⇒ `code-review-report` 零覆盖 | ✅ 核实（`test_gate_freshness.py:989`） | — |
| A7 | 内容比较对敌意 config/env 稳定 | ✅ 实测 `git show` 在 `diff.ignoreSubmodules=all` + `GIT_ICASE_PATHSPECS=1` 下如实返回 | — |
| A8 | `ls-tree` 在 `GIT_ICASE_PATHSPECS=1` 下 fatal（非静默错答） | ✅ 实测 `fatal: pathspec magic not supported` | 若静默错答则为 fail-open，须改用其他枚举 |
| A9 | 阶段判定与失鲜判定无循环依赖 | ✅ 阶段只取决于盘面上存在哪些产物（plan / code-review-report / verify-report），不取决于失鲜结论 | 若有循环则窗口不可实现 |

## 开放问题

无。

## Non-Goals

- **T189**（`_normalize_checkbox_lines` 口径反转为白名单）——它在本方案里是 design 域内容比较的**核心依赖**，须在 design.md 残余面显式登记其耦合，但口径反转本身属独立面，不在本次。
- **B18**（`maintain_scan.py` 的 `find_repo_root`）——属仓根解析面。
- **全仓 git 调用安全面盘点**（另有约 8 个脚本存在同类无 timeout / 无异常捕获）——gate 是仅有的两道质量门，风险等级高于记录类脚本，本次只做 gate（基准 4）。
