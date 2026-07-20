## Why

`ship_gate.py` 判定「评审结论是否已失鲜」时，长期从 git 管道信号**推断**「被审过的内容变了没有」。一轮 grill + 两轮多镜设计审（累计 11 镜 + 4 站点跨模型 voice）在这条链上累计挖出**十个缺陷、全部实测复现**：

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

- 三个评审 producer（`/sdflow-spec-review`、`/sdflow-code-review`、`/sdflow-done`）在报告 frontmatter 写 `reviewed_sha: <被批准/被审的那个提交>`。
- gate reader 读它：**缺失 / 非 40 位 OID / 对象不存在 ⇒ fail-closed**（`UNKNOWN(6)`）。**MUST NOT 在缺字段时静默回退反推式锚**——回退 = 缺陷 9 原样存活。
- **`reviewed_sha` 记的是「被批准的盘面」，不是「写报告的时刻」**：拍板/放行这个动作批准的是哪个提交，锚就指哪个。gate 的职责是「批准之后有没有被改」，不是「批准的内容对不对」。
- **code-review 的写入时序 MUST 与自动修复分离**（见 design ADR-7）：自动修复先单独提交 → 锚指该提交 → 报告单独提交。否则锚不含修复，checkpoint 一落即自失鲜。
- 退役 `report_last_sha`。

### P0 — 比内容，取代路径枚举（解 1–8）

- **design 域**：对锚与 HEAD **各跑一次** `git ls-tree -r -z <ref> -- proposal.md design.md specs/`，比较 `path → (mode, type, oid)` **映射**。映射不等即失鲜。
  `tasks.md` 因需过 `_normalize_checkbox_lines` 才单独取内容比较（2 次 `git show`）。
- **code 域**：比 `git ls-tree` 的**顶层条目**（浅层、不递归）、排除 `openspec` 条目后求等值。**MUST NOT 用整棵树的 sha**——实测 done 写 `verify-report.md` 即改变整树 sha ⇒ 正常流程第一步就假阳。
- 勾选豁免**常开、按内容切、不按阶段切**：`tasks.md` 勾选框的写入方是 **agent 自由行为、不是 SKILL 契约**（前序 change 假设表 A1′ 已证），按阶段切会立刻假失鲜。

> 🟢 **为什么 design 域比映射而不是逐文件比字节**：`ls-tree -r` 的输出本身就是 `mode type oid\tpath`，
> **天然含 mode 与 type** ⇒ 一次比较即覆盖「存在性 / 对象类型 / mode / 内容」四者，
> 且**新增、删除、rename 自动落网**（单侧枚举会漏掉「另一侧独有」的路径，这是逐文件比字节的固有缺口）。
> 副作用是 git 调用从 8–10 次降到 4 次。**这是减法**：更少的调用、更全的覆盖、更少的可出错分支。

> 🔴 **砍的是枚举，不是监视集。** 监视集（只盯四件套 / 只盯非 `openspec/`）是**承重的**——它才是「实现期改源码不该让设计门失鲜」的来源。裸 `reviewed_sha == HEAD` 已实测证伪：实现期每个提交都在动 HEAD ⇒ 设计门从第一个实现提交起永远失鲜。

### P0 — 限定求值窗口（消掉剩余假阳，且**取消整套补偿机制**）

design 域失鲜的风险是「照着一份已经变了的设计继续建」——该风险**只在实现期存在**。∴ design 域失鲜**只在阶段三起手至实现完成期间求值**（`RUN_SOP` / `RUN_PLAN` / `CONTINUE_IMPL`），进入代码审后不再求值。code 域两个检查**已经是「位置即阶段」**（`:1291` 在代码审之后才可达、`:1311` 在 done 之后），无需改动。

**该判据的必要性有历史数据支撑**：全仓 **14 个 `checkpoint(impl-review)` 提交改过四件套**（`design.md`/`proposal.md`/`specs/`/`tasks.md`）——代码审期修订设计产物是**常态而非偶发**，全阶段求值会把这 14 类情形全部误拦。

**窗口内的合法 churn 存在但不合规范**（见假设表 A2）⇒ 判定保持全机械、**不设逃生口**：撞门的正解是走重审，不是加旁路。

### P1 — git 调用失败落进退出码契约

- `run_git` / `run_git_rc` / `run_git_bytes` 统一捕获 `OSError`（含 `FileNotFoundError`、`PermissionError`、无效可执行格式）与 `subprocess.TimeoutExpired`，映射 `UNKNOWN(6)`。
- 三处补 `timeout=30`。
- 子进程 **env 清理走 denylist**（复制 `os.environ` 后剔除 `GIT_` 前缀键），**MUST NOT 用 allowlist**——后者在 Windows 会漏 `SYSTEMROOT`/`COMSPEC` 等 `CreateProcess` 依赖变量，致子进程启动失败（本地 macOS 测不出）。
- **`GateIndeterminate` MUST 携带结构化 payload 区分五类失败原因**（git 不可用 / 超时 / 锚缺失 / 锚非法或对象不存在 / 读失败），各自给可行动诊断——五者的补救动作完全不同。

### 退役

BR-7（`checkpoint(impl-review)` subject 豁免）、`report_last_sha`、以及 **design 域帧比较链条整簇**：
`frame_touched_paths`、帧遍历、`design_frame_exempt` / `_reason`、`commit_parents`、`_parent_path_status`、
`_plain_content_modification`、`_plain_modification_from_raw`、`blob_pair`、`design_watched_subs`、
`STALE_CATEGORIES`、`_stale_trigger_hint`、`StaleResult.trigger`。

**保留复用（MUST NOT 误删）**：`DESIGN_WATCHED_NAMES`（固定清单常量本身）、`_tasks_content_exempt`
（签名 `(before_bytes, after_bytes) -> bool`，语义与新设计要求吻合）、`_normalize_checkbox_lines`。

### 验证要求（贯穿全部）

每条新增守卫 MUST 附**变异证明**：删掉该守卫 ⇒ 对应用例变红。上一轮的 rename 用例只直接调 `blob_pair`、没走 `is_stale`，因此**在真实洞存在的情况下仍是绿的**——这是本项要求的直接实证来源。

**两条守卫的变异手段与其余不同源，MUST 在 impl-report 显式说明**（见 tasks 4.5 / 4.3）：
「排版提交不移锚」的守卫本体是架构决策，新实现里没有可删的反推逻辑（复活 `report_last_sha` 会直接违反 Compliance）；
「求值窗口」是控制流结构，删开关只验证了开关本身、验证不了前移是否正确落地。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `spec-workflow`: 失鲜判定由「从 git 管道推断路径变更」改为「录锚 + 比内容」，并新增求值窗口约束（判据只在其保护的风险真实存在的阶段求值）；新增 `reviewed_sha` 的 producer/reader 契约与 git 调用失败的退出码契约。

## Impact

- **代码**：`sdflow-ship/scripts/ship_gate.py`（`is_stale` 两分支重写、锚获取、求值窗口、`run_git*` 系列、`FIELD_ENUMS` 校验机制、`emit` 诊断；退役帧比较整簇与 BR-7）
- **SKILL**：`sdflow-spec-review` / `sdflow-code-review` / `sdflow-done` 的报告模板各加 `reviewed_sha`；
  `sdflow-code-review` 的 checkpoint 时序改为「修复 / 报告」两段提交；
  `sdflow-spec-review` 收敛口加一条拍板前复核纪律；`sdflow-ship/SKILL.md` 链序段补求值窗口行为边界说明
- **测试**：`sdflow-ship/tests/test_gate_freshness.py` + **共享 fixture `approved_change` / `tail_ok` / `impl_done` 须重构为两段提交模型**（影响 `test_gate_impl_progress.py` / `test_gate_namespace.py` / `test_gate_tail.py` 共 44 处调用点，其中 30 处与本 change 主题无关）
- **文档**：`openspec/CONTEXT.md` 新增「求值窗口（Evaluation Window）」术语条目（已随 grill 完成）
- **行为变更**：① 此前被误判 fresh 的盘面今后判 stale（**修复**）；② 此前被例行 merge 误拦的盘面今后判 fresh（**修复**）；③ 代码审期与 done 期不再求值 design 域失鲜（**范围收窄**，见 design.md 残余面）；④ **实现期直接改设计文档纠偏将被 `REFUSE_START` 拦下**（**有意的行为收紧**，见 A2）
- **迁移**：存量 active 报告无 `reviewed_sha` ⇒ fail-closed ⇒ 须重审一次。在途的只有本 change 自己
- **消费方**：本仓为 toolkit 源仓，改动经 push → 各仓 **`/sdflow-upgrade`** 后生效。
  ⚠️ **`sdflow-init update` 对本 change 无效**——`ship_gate.py` 与三个评审 SKILL 都不在 `sdflow-init/assets/workflow/` bundle 内

## 合规声明〔BASE-21〕

本变更处理对象为 git commit SHA、文件路径、报告 frontmatter 字段，**不涉及 PII，无合规约束**（无数据居留 / 审计留存 / 隐私要求）。

## 需求优先级〔BASE-23 · TG-19〕

| 级 | 项 | 依据 |
|---|---|---|
| **P0** | 录锚（缺陷 9、10） | 安全面：锚可被无声前移 / 读不到 git 就放行。缺陷 9 存在时，其余修复的威胁模型**一行都不成立** |
| **P0** | 比内容（缺陷 1–8） | 安全面 + 可用性面：七个 fail-open + 一个假阳。已全部复现 |
| **P0** | 限定求值窗口 | 可用性面 + **复杂度面**：判据只在风险真实存在的阶段求值，使其保持全机械、无语义层、无逃生口；14 个 `impl-review` 提交是其必要性的实证 |
| **P1** | git 调用失败落契约 + `GIT_*` 清理 | 可用性面：退出码脱离契约集致链序误判；无 timeout 致无限阻塞；env 致无故罢工 |

P0 三项同处 `is_stale` 同一函数、同一片面，分开做要付三遍 workflow 循环成本，故合并（基准 4）。P1 动的是同一批 `run_git*`，同理。

## 假设列表〔BASE-14 · TG-22〕

| # | 假设 | 已验证？ | 若不成立 |
|---|---|---|---|
| A1 | 缺陷 1–10 均真实存在 | ✅ 全部本地 fixture 复现，多数经真 `is_stale` 求值 | — |
| A2 | 实现期**不应**有四件套实质修订（`sdflow-implement` 只读 `design.md`，撞问题走 halt 上抛） | ⚠️ **契约成立、但历史有违例**：全仓 **3 个确证反例**（`94c20b79b` 拍板后 1.6h 改 design.md；`55489213a`/`cfb9a670d` 分别 14.9h/14.6h），跨 2 个 change，最近一个在本 change 起草前一天；另 3 个候选因用旧 inline 锚查不到拍板时间、保守不计入 | **不改设计**：这些提交按新判据**理应**被判失鲜。措辞已从「零发生⇒零成本」改为「**存在但不合规，新窗口有意把它逼回正规流程**」 |
| A3 | 代码审期与 done 期的四件套修订是工作流明文允许的 | ✅ **14 个 `checkpoint(impl-review)` 提交改过四件套**（常态而非偶发）；`opsx:verify` step 7「revise design.md to match reality」（`.claude/commands/opsx/verify.md:99`） | 若不允许则窗口须延长 |
| A4 | `tasks.md` 勾选的写入方不受阶段约束 | ✅ 前序 change 假设表 A1′「写入方是 agent 自由行为、不是 SKILL 契约」；本仓 20 个 checkpoint 提交碰过 `tasks.md`，散在各阶段 | 若受契约约束则豁免可按阶段切（但无收益） |
| A5 | 失鲜判定有两个 scope、**三个 `is_stale` 消费方** | ✅ `:1214` design / `:1291` code(code-review-report) / `:1311` code(verify-report)。承 `adr/0011`「MUST grep 列全调用点」 | — |
| A5′ | **frontmatter 另有第二个独立消费方** | ✅ `sdflow-done/scripts/roadmap_writeback_draft.py:151-202` 是独立的 `verify-report.md` reader；**已核实对新增字段免疫**（`re.match(r"^\s*verify:\s*(\S+)\s*$")` 只认 `verify:`） | 若不免疫则新增字段会击穿 roadmap 回填 |
| A6 | code 域现存测试仅 1 例且走 `verify-report` ⇒ `code-review-report` 零覆盖 | ✅ 核实（`test_gate_freshness.py:989`） | — |
| A7 | 内容比较对敌意 config/env 稳定 | ✅ 实测 `git show` / `ls-tree` 在 `diff.ignoreSubmodules=all` + `GIT_ICASE_PATHSPECS=1` 下如实返回或 fatal（无静默错答） | — |
| A8 | `ls-tree` 在 `GIT_ICASE_PATHSPECS=1` 下 fatal（非静默错答） | ✅ 实测 `fatal: pathspec magic not supported` | 若静默错答则为 fail-open，须改用其他枚举 |
| A9 | 阶段判定与失鲜判定无循环依赖 | ✅ 阶段只取决于盘面上存在哪些产物（plan / code-review-report / verify-report），不取决于失鲜结论 | 若有循环则窗口不可实现 |
| A10 | **阶段判定散落在三处 early-return，前移是真实控制流重排** | ✅ `RUN_SOP`(`:1237`)/`RUN_PLAN`(`:1243`)/`CONTINUE_IMPL`(`:1269`) 各自 `emit()`，而 `emit()` 内部 `sys.exit()` | 若实现走捷径只在 step7 后加检查 ⇒ `RUN_SOP`/`RUN_PLAN` 逃出检查（fail-open） |
| A11 | **`ls-tree -r` 的 `path→(mode,type,oid)` 映射比较可覆盖增/删/rename/改且无假阳** | ✅ 实测五格全绿：新增 ✅ / 删除 ✅ / rename（内容不变）✅ / 内容改动 ✅ / 无改动→fresh ✅ | 若有假阳则退回逐文件比字节 + 双侧并集 |
| A12 | **旧 gate 对未知 frontmatter 字段静默忽略**（决定回滚路径通不通） | ✅ `ship_gate.py:876-877` `if field not in FIELD_ENUMS: continue`，注释写明「非本 schema 字段（外来 metadata），忽略」 | 若报错则回滚路径断裂 |

## 开放问题

无。

## Non-Goals

- **T189**（`_normalize_checkbox_lines` 口径反转为白名单）——它在本方案里是 design 域内容比较的**核心依赖**，须在 design.md 残余面显式登记其耦合与**承重升格**，但口径反转本身属独立面，不在本次。
- **B18**（`maintain_scan.py` 的 `find_repo_root`）——属仓根解析面。
- **全仓 git 调用安全面盘点**（另有约 8 个脚本存在同类无 timeout / 无异常捕获）——gate 是仅有的两道质量门，风险等级高于记录类脚本，本次只做 gate（基准 4）。
- **归档终态（`verify` → `merge` 之间）的失鲜检查**——已评估并**有意不做**，理由见 design.md 残余面。
- **BASE-20 / BASE-22 / BASE-29 的形式化产物**（利益相关方表 / proposal 与 design 的实现细节分层 / 契约 scope-check 表）——本 change 规模下形式收益低于维护成本。
