<!-- sdflow:step1-broad-review v1 mode="simulated" -->

# 广审报告 — fix-mechanical-layer-silent-failures

> **降级声明（MUST NOT 伪装原生）**：`mode="simulated"`。autoplan skill 在本机**可用**，但其 Phase 0
> 要求把 restore-point HTML 注释与 Decision Audit Trail **写进 plan file**；本仓对应物是 OpenSpec 四件套，
> 往 `design.md` 注入 gstack 脚手架会违反 `openspec/rules/doc-authoring.md`（DOC-1：正文即最终态）。
> ∴ 以独立 fresh-context 子代理（`opus`）执行 CEO / eng / DX 三视角广审，**强制读真实代码**。
> 这是**架构不匹配下的等价替代**，不是"跑过了 autoplan"。上一 change（`async-outside-voice`）同因同判。

## 视角 A — 战略 / 范围

| 严重度 | 发现 | 证据 | 处置 |
|---|---|---|---|
| medium | 三条 bug 无技术耦合，评审面涨到 7 需求 / 8 切片 / 4 文件族 | `design.md`「1/2/6 与 3/4/5/7 分属两个文件族，无耦合可并行」——设计自认 | **接受**（同类缺陷面治，符合基准 ④）；但采纳其建议：B9/B10 应可**独立 merge**，不被 B11 返修拖住 |
| **high** | 6 个月后最显愚蠢的决定 = R7 把「机械核」建在 `truncated=` 锚行上 | 两层 SKILL.md：`truncated 取 helper stderr 的 OV_TRUNCATED`——该值由**主 session 模型抄写**，非 helper 落盘 ⇒ `design.md` 称「锚行是确定性信号」**为假** | **采纳，改设计**（见下 G-1） |
| medium | python3 备选被「新增依赖」否掉过快——helper 的唯一调用方本就是跑 python 脚本的 skill 链 | `design.md` D1 备选表 | **采纳措辞修正**：记为「偏好而非硬约束」，不写成技术证伪 |

## 视角 B — 工程

| 严重度 | 发现 | 证据 | 处置 |
|---|---|---|---|
| **critical** | `_scan_pool` **不是**唯一闸门：`read_rename_snapshot` 是第二条独立取数路径 | `issues.py:764`；`cmd_batch_rename` 调用序：`read_rename_snapshot` → `retag` → `atomic_write(registry)` → `atomic_write_bytes(dated)` → **才** `_reindex_core` | **采纳，重构**（G-2）：① 写盘发生在阻断判定**之前**，D5 在此路失效；② 该路径 in-process 解析、**无 JSON 字段可缺席** ⇒「缺席即阻断」在此**完全失效**，须另立机制 |
| **critical** | 「6 个取数调用方经同一路径」是**虚构**的 | `cmd_batch_lint`→`_batch_lint_snapshot` 只读 `batches.md`；`cmd_batch_add` / `cmd_batch_set_status` 只调 `_read_batches_lines`；`cmd_sweep` 自己 subprocess 解析 `scan --json`。真正经 `read_pool` 的只有 `_reindex_core` ← {reindex, rename} | **采纳，改断言**（G-3）：`proposal.md` / `design.md` 的拓扑断言须重写；`tasks 4.4` 对 lint/add/set-status 的「阻断断言」**写不出真断言 = 假绿三条** |
| high | 失败模式表漏一条偏斜轴：`issues.py` **自持第三份 recorder parser** | `issues.py:298-511` | **采纳**：老 `issues.py` 自身 parser 不认 frontmatter 时，rename/lint 路径无任何防线；F 表新增并登记为残余 |
| medium | exit 2 在 sweep 内部被**压平**：sweep 调子进程 reindex 后只判 `!= 0` → `_die`（exit 1） | `issues.py` `cmd_sweep` 末段 `if ri.returncode != 0: _die(...)` | **采纳**：tasks 5.2 须显式要求**透传 2** |
| medium | tasks 4.7「阻断集为空行为完全无变化」不承重——fixture 须刻意造干净盘面才绿 | — | **采纳**：改为「在真实仓盘面上跑」并接受它可能红 |

## 视角 C — 开发者体验

| 严重度 | 发现 | 证据 | 处置 |
|---|---|---|---|
| high | 逃生口「产物留疤」**只对 reindex 成立**：banner 由 `INDEX_BANNER` 生成，只有写 INDEX 的命令有载体 | `issues.py:1327` | **采纳**（G-4）：`set-status`/`batch add`/`lint`/`sweep` 阻断时要么楔死（正是 D4 要避免的）、要么放行无痕；spec「放行留痕」场景须**限定适用调用方**，其余给出别的出路 |
| medium | 本 change **救不了本次事故本身**：事故是 consumer + producer **双旧**，新逻辑根本不在场 | `sdflow-done/SKILL.md:214` 调运行 checkout 的 `~/.claude/skills/sdflow-issues/…` | **采纳其建议**：sweep 起手打印**所调脚本绝对路径 + 版本戳**（近零成本，把「跑的是哪份」变可见）——这是唯一能覆盖双旧场景的动作 |
| medium | task 7.2 前提**不成立**：`sdflow-ship/SKILL.md` 全文 grep `sweep` = **0** | 实测 `grep -c sweep` = 0 | **采纳**：exit 2 语义只落 `sdflow-done`，改 ship 是无效编辑 |

## 已检查且判定无问题（防「没写＝没查」）

- **1.7 `secret_scan` 次序**：`outside-voice.sh:153` 的 `secret_scan "$ctx"` 在截断分支之前扫**整个文件**，`do_exec` 另有预扫 ⇒ **无出境回归**。此题现在即可定论 ⇒ tasks 1.7 **标已核**，不留到实现期（通则①）。
- **`anchor_lint` 两份字节一致**：`shasum` 两份同为 `fa389e81…` ⇒ tasks 6.3 是「维持」不是「新建」，无隐藏工作量。
- **D2 的 `wait` 方案与 shell 选项相容**：`outside-voice.sh:57` 只有 `set -u`、**无 `set -e`** ⇒ `wait` 返回非零不会误中止脚本，后台化在这点上安全。
- **D3 分级落 parse 层可行**：`buglist.py:991-1044` 的 `problems.append` 全在同一函数内、语义已知；`_scan_snapshot` 收集的是**全池未经 `--change` 过滤**的 problems ⇒ sweep 的 `--open-ungrouped` 不会漏诊断。todolist 侧 12 个同形 append 点，对称成立。

## 主 session 复核（我自己跑的验证，非转述）

上述两条 critical + exit 2 压平 + ship 无 sweep，**均已由我独立跑命令确认**，非采信子代理转述。`lint/add/set-status` 不经 `read_pool` 一条以「函数体内 grep 无 `read_pool`/`_scan_pool` 命中」确认。
