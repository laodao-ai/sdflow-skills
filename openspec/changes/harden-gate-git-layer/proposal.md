## Why

`ship_gate.py` 判定「评审结论是否已失鲜」时，长期从 git 管道信号**推断**「被审过的内容变了没有」。一轮 grill + 一轮多镜设计审（4 镜 + 广审双声 + 2 站点跨模型 voice）在这条推断链上累计挖出**八个缺陷，全部实测复现**：

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

**外加两个不在枚举链上、但同属失鲜判定的 fail-open**：

| # | 缺陷 | 证据 |
|---|---|---|
| 9 | **锚点可被无声前移** — `report_last_sha` = 「最后一次触碰报告**路径**的提交」，任何后续触碰（一个空行、一次 CI reformat）都把锚推到未审改动之后 | 实测：后门提交 + 一个无关的报告排版提交 ⇒ 判 fresh |
| 10 | **锚获取本身 fail-open** — `run_git` 非零退出折成 `''`，`is_stale` 判 `(False,'uncommitted')` = fresh | 实测：非 git 目录下返回 `(False,'uncommitted')` |

**这不是十个 bug，是同一根因的十张脸**：拿 git 管道当「内容是否改变」的代理。4 与 5 互为解药兼病灶（`-m` 修假阳造假阴，`--cc` 修假阴造假阳），7 与 8 只需一个 config / 一个环境变量就能翻转判定。**在枚举面上补不完**——正是 `CLAUDE.md` 基准 5 点名的补丁螺旋。

∴ 本 change **不修补推断链，改掉推断本身**：录锚 + 直接比内容。决策与实证落 `openspec/adr/0026`。

触发 TG：**TG-17**（HR-TG）· TG-14 · TG-18 · TG-19 · TG-22 · TG-23。

## What Changes

### 机械层只保**召回**，精确率交语义层

机械层承诺「任何实质改动都不漏」，**不承诺不误报**；误报由主 session 读 diff 分诊，**分诊结论 MUST 落盘留痕**。

### P0 — 录锚，取代「从最后触碰反推」

- 三个评审 producer（`/sdflow-spec-review`、`/sdflow-code-review`、`/sdflow-done`）在报告 frontmatter 写 `reviewed_sha: <当时 HEAD>`。
- gate reader 读它：**缺失 / 格式非法 / 对象不存在 ⇒ fail-closed**（`UNKNOWN(6)`）。**MUST NOT 在缺字段时静默回退旧的可移动锚**——回退 = 缺陷 9 原样存活。
- 缺陷 9、10 由此消失。

### P0 — 直接比内容，取代路径枚举

- **design 域**（监视集是固定清单）：`proposal.md`/`design.md`/`tasks.md` 逐个 `git show <锚>:<path>` 与 HEAD 比字节；`specs/` 子树经 `ls-tree -r -z` 枚举后同样逐个比；`tasks.md` 比之前过既有的 `_normalize_checkbox_lines`。
- **code 域**（监视集列不出固定清单）：`git ls-tree <锚>` 与 HEAD 各取一次**顶层条目**，去掉 `openspec` 那一行后比较，不等即失鲜。任何 `openspec/` 之外的改动都会改变某个顶层条目的 sha ⇒ 召回完整；而 `openspec/` 内的记账（写 verify 报告、archive 移目录）不影响其余顶层条目 ⇒ 不假阳。
- 缺陷 1/2/4/5/6/7/8 由此**整类消失**（不枚举路径、不调 diff 做判定）。

> 🔴 **砍的是枚举，不是监视集。** 监视集（只盯四件套 / 只盯非 `openspec/`）是**承重的**——它才是「实现期改源码不该让设计门失鲜」的来源。裸 `reviewed_sha == HEAD` 已实测证伪：实现期每个 ticket 都勾 `tasks.md`、每个提交都动 HEAD ⇒ 设计门从实现的第一个提交起永远失鲜，等于把 `fix-design-gate-freshness-proxy` 修的缺陷退回去。

### P1 — git 调用失败落进退出码契约

- `run_git` / `run_git_rc` / `run_git_bytes` 统一捕获 `OSError`（含 `FileNotFoundError`、`PermissionError`、无效可执行格式）与 `subprocess.TimeoutExpired`，映射 `UNKNOWN(6)`。
- 三处补 `timeout`。
- 子进程**清理 `GIT_*` 环境变量**（实测 `ls-tree` 在 `GIT_ICASE_PATHSPECS=1` 下 fatal 罢工）。

### 退役

BR-7（`checkpoint(impl-review)` subject 豁免）、`frame_touched_paths`、帧遍历、`design_frame_exempt_reason`、触发点诊断管道。BR-7 承载的政策（阶段三 impl-review 修订可改设计产物而不作废设计门）**迁入语义层**：主 session 读真实 diff 判断，重锚 + 写理由。

### 验证要求（贯穿全部）

每条新增守卫 MUST 附**变异证明**：删掉该守卫 ⇒ 对应用例变红。上一轮的 rename 用例只直接调 `blob_pair`、没走 `is_stale`，因此**在真实洞存在的情况下仍是绿的**——这是本项要求的直接实证来源。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `spec-workflow`: 失鲜判定由「从 git 管道推断路径变更」改为「录锚 + 直接比内容」；新增 `reviewed_sha` 的 producer/reader 契约、机械召回与语义精确的切分、语义重锚的留痕要求、git 调用失败的退出码契约。

## Impact

- **代码**：`sdflow-ship/scripts/ship_gate.py`（`is_stale` 两分支重写、`run_git*` 系列、锚获取；退役帧遍历与 BR-7）
- **SKILL**：`sdflow-spec-review` / `sdflow-code-review` / `sdflow-done` 的报告模板各加一行 `reviewed_sha`；`sdflow-ship` 加语义重锚协议
- **测试**：`sdflow-ship/tests/test_gate_freshness.py`（BR-7 真值表 8 格随 BR-7 退役；新增内容比较与录锚用例）
- **行为变更**：① 此前被误判 fresh 的盘面今后判 stale（**修复**）；② 此前被例行 merge 误拦的盘面今后判 fresh（**修复**）；③ impl-review 修订设计产物今后须语义判 + 重锚（**流程变更**）
- **迁移**：存量 active 报告无 `reviewed_sha` ⇒ fail-closed ⇒ 须重审一次。在途的只有本 change 自己
- **消费方**：本仓为 toolkit 源仓，改动经 push → 各仓 `/sdflow-upgrade` 后生效

## 需求优先级〔BASE-23 · TG-19〕

| 级 | 项 | 依据 |
|---|---|---|
| **P0** | 录锚（缺陷 9、10） | 安全面：锚可被无声前移 / 读不到 git 就放行。缺陷 9 存在时，其余修复的威胁模型**一行都不成立** |
| **P0** | 直接比内容（缺陷 1–8） | 安全面 + 可用性面：五个 fail-open + 一个假阳。已全部复现 |
| **P1** | git 调用失败落契约 + `GIT_*` 清理 | 可用性面：退出码脱离契约集致链序误判；无 timeout 致无限阻塞；env 致无故罢工 |

P0 两项同处 `is_stale` 同一函数、同一片面，分开做要付两遍 workflow 循环成本，故合并（基准 4）。P1 动的是同一批 `run_git*`，同理。

## 假设列表〔BASE-14 · TG-22〕

| # | 假设 | 已验证？ | 若不成立 |
|---|---|---|---|
| A1 | 缺陷 1–10 均真实存在 | ✅ 全部本地 fixture 复现，多数经真 `is_stale` 求值 | — |
| A2 | 实现期提交不触及 design 域监视集 ⇒ 内容比较保持 fresh | ✅ 实测：改源码 + 勾复选框后 `design.md` 内容等值 | 若不成立则设计门实现期常失鲜，方案不可用 |
| A3 | `_normalize_checkbox_lines` 可直接复用且已是 bytes 口径 | ✅ 源码核实（`ship_gate.py:537`，`raw.split(b"\n")`） | 需另写归一化 |
| A4 | 失鲜判定有两个 scope、**三个消费方** | ✅ `:1214` design / `:1291` code(code-review-report) / `:1311` code(verify-report)。承 `adr/0011`「MUST grep 列全调用点」 | — |
| A5 | code 域现存测试仅 1 例且走 `verify-report` ⇒ `code-review-report` 零覆盖 | ✅ 核实（`test_gate_freshness.py:989`） | — |
| A6 | 内容比较对敌意 config/env 稳定 | ✅ 实测 `git show` 在 `diff.ignoreSubmodules=all` + `GIT_ICASE_PATHSPECS=1` 下如实返回 | — |
| A7 | `ls-tree` 在 `GIT_ICASE_PATHSPECS=1` 下 fatal（非静默错答） | ✅ 实测 `fatal: pathspec magic not supported` | 若静默错答则为 fail-open，须改用其他枚举 |
| A8 | 退役 BR-7 后，其政策可由语义层承载 | ❌ **待实现期验证**：需确认 impl-review 修订四件套的实际频率与分诊成本 | 若频率过高则须回补一条机械豁免 |

## 开放问题

无。

## Non-Goals

- **T189**（`_normalize_checkbox_lines` 口径反转为白名单）——它在本方案里成为 design 域内容比较的**核心依赖**，须在 design.md 残余面显式登记其耦合，但口径反转本身属独立面，不在本次。
- **B18**（`maintain_scan.py` 的 `find_repo_root`）——属仓根解析面。
- **全仓 git 调用安全面盘点**（另有约 8 个脚本存在同类无 timeout / 无异常捕获）——gate 是仅有的两道质量门，风险等级高于记录类脚本，本次只做 gate（基准 4：不为「顺手」把不相关的面拖进来）。
