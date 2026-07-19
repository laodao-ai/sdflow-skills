# design — fix-mechanical-layer-silent-failures

## Context

两条缺陷同形：**`exit 0`，事情没做成**。动机与范围收缩记录见 `proposal.md`，需求见 `specs/`。本文只讲**怎么做**。

**代码事实**（D-1，均已 grep 核验并经接地镜逐条复核，非记忆）：

| 事实 | 出处 |
|---|---|
| 截断用 `head -c` / `tail -c` 在字节边界切 | `outside-voice.sh` `render_prompt()`（:160, :162） |
| trap 只清 workdir、runner 前台执行 | `do_exec()`：`trap "rm -rf '$workdir'" EXIT`（:202） |
| 脚本是 **bash 不是 POSIX sh**，且**无 `set -e`**（只有 `set -u`） | 第 1 行 `#!/usr/bin/env bash`；:57 |
| `secret_scan "$ctx"` 在截断分支**之前**扫整个文件 | :153（截断在 :158）；`do_exec` 另有预扫 |

## Goals / Non-Goals

**Goals**：R1（截断字符边界安全）、R2（父被回收则子必死）。
**Non-Goals**：见 `proposal.md`，每条附可证伪假设（D-3），此处不复制。

## Decisions〔TG-23 · ADR 记录〕

### D1 — 截断：纯 bash 边界回扫（在切点上调整），零新增运行时依赖

**选它的理由**：UTF-8 是**有界**语法面（单字符 ≤4 字节、continuation 字节形态确定）⇒ 基准 ⑤ 允许确定性处理；且**在切点上回退**比「切完再清洗」语义更干净——不产生「先造出非法字节再补救」的中间态。

**实测**（macOS，混合 ASCII / 3 字节 CJK / 4 字节 emoji 语料）：201 个连续切点，头段与尾段**分别**严格模式解码 UTF-8，**失败 0**；纯 ASCII 时丢弃 0 字节；100KB 文件耗时 `0.016s`（只读 ≤4 字节，与文件大小无关）。

**代价**：约 20 行 bash + 依赖 `od`（macOS / Linux 基础系统均自带，且 `head -c` / `tail -c` 已在用）。

**备选（均已实测，记录证伪结论以免后人重蹈）**：

| 备选 | 结论 |
|---|---|
| `iconv -f UTF-8 -t UTF-8 -c` | **部分证伪**。macOS 实测：尾部序列不完整的**头段** `rc=1` + stderr `unexpected end of file; the last character is incomplete.`（stdout 仍合法）⇒ 必须显式吞 rc 与 stderr，否则在日志里制造假故障。且**本机无 GNU iconv、无容器可验** ⇒ GNU 侧一致性**未验证** = 跨平台风险，这是不选它的决定性理由 |
| `python3 -c … .decode('utf-8','ignore')` | 实测两半均正确。缺点：给 helper 新增 python3 运行时依赖。〔广审修正：helper 的调用方本就是**跑 python 脚本的 skill 链**，∴ 这是**偏好而非硬约束**，MUST NOT 写成技术证伪。若 bash 版在实现期显出维护成本，切 python3 是正当的〕**保留为干净次选** |
| `perl -Mopen=std,:utf8` | macOS 系统 perl 上 `rc=255`（`Unknown PerlIO layer class 'std'`）。既然要调外部解释器，不如 python3 |

**边界（MUST）**：只认 UTF-8，**MUST NOT** 演化成编码检测 / 嗅探——那是无界面，正是基准 ⑤ 的警号（「每轮 review 都在同一个函数里补一个新分支」）。

### D2 — 子进程：后台 + `wait` + trap 补 `INT TERM HUP`

**先证实两件事**（避免修错地方）：① bash 的 **EXIT trap 在 SIGTERM 下确实会跑**（实测 `EXIT-TRAP-RAN`，所以 workdir 才被清了）；② 但**前台 `timeout` 完全不受影响**（实测 `42998 1 timeout -k 10 60 sleep 45`，ppid 已成 1）。**∴ 病根不是 trap 没跑，是 trap 里没有子 PID 可杀。**

**做法**：runner 改后台启动、记 PID、`wait` 取回退出码；清理函数先 `kill -TERM` 该 PID、宽限后 `kill -KILL` 兜底，再删 workdir；trap 覆盖 `INT TERM HUP` 与 `EXIT`。

**关键实测**：杀 `timeout` **会连带杀掉孙进程**——让 `timeout` 跑一个自己再 spawn `sleep 300` 的脚本，TERM 后 `timeout` / 中间脚本 / `sleep 300` **三层全灭**（GNU timeout 自建进程组并转发信号，实测三者 pgid 相同）。∴ 无需自己管进程组。

**退出码无回归**：`wait` 后 `rc=124`（超时）/ `0` / 其他非零码**原样透传**；后台化后 stdin/stdout 重定向照常。**与 shell 选项相容**〔广审核实〕：脚本只有 `set -u`、**无 `set -e`** ⇒ `wait` 返回非零不会误中止。

**备选**：`setsid` + `kill -- -PGID` —— **证伪**：`setsid` 在 macOS（Darwin 25）**不存在**（Linux util-linux 才有）；且上条实测表明 timeout 已自建进程组、信号转发足够，**收益为零**（此处指 TERM 阶段；KILL 升级阶段的收益见 D2.1）。

**143 无需新增枚举**〔广审核实〕：两层 SKILL 的 async 段第 ⑦ 条已有 catch-all——「其余一切情形（未知码 / `.rc` 缺席或内容不匹配 …）→ **保守** fallback（`reason_code="exec-error"`）」。且 helper 被 TERM 时 `printf '%s' "$?" > <site>.rc` 本就没机会执行 ⇒ `.rc` 缺席 ⇒ 本来就走 exec-error。**B10 的修复是锚语义中性的**，改变的只是孤儿不再白烧至内层超时。

### D2.1 — 组级 KILL 升级：治愈残余(d)（runner 忽略 TERM 后子树逃逸）〔fix-mechanical-layer-silent-failures 根治，1.4.2〕

**上一轮（F-新2）实测坐实的根因**：`OV_RUNNER_PID` 记的是 **`timeout` 自身**的 PID，不是 runner 的 PID。`ov_cleanup` 的 KILL 升级只对这一个 PID 发 SIGKILL——不可捕获、瞬间生效，`timeout` 来不及跑到它自己那条「向子进程组转发 KILL」的 `-k 10` 升级逻辑 ⇒ runner 若 `trap '' TERM` 忽略终止信号，其子孙进程逃逸成孤儿（手工探针 + pytest 实测复现，见 F-新2 / `task3-cross-platform-fix1.md`）。

**修法（已实测验证，见 impl-report `task3-cross-platform-fix2.md`）**：GNU `timeout` 会 `setpgid` 把自己放进**独立进程组**，且该组的 **PGID 恒等于 `timeout` 自己的 PID**（即 `OV_RUNNER_PID`）、**不等于**脚本自身的 PGID。∴ 把 KILL 升级步的目标从「单个 PID」改成「负号进程组」（`kill -KILL -"$OV_RUNNER_PID"`），SIGKILL 直接打穿整棵子树，不再依赖 `timeout` 来不及跑完的组内转发。这不是 D2 已证伪的「主动 `setsid` 建组」——而是**借用** `timeout` 本来就会自建的那个既有组，只在升级步、且守卫通过时才对它下手。

**实测（macOS，手工探针 + pytest 双证）**：`timeout pid=X pgid=X`（组长，且 ≠ 脚本自身 PGID）；对忽略 TERM 的 runner，组级 KILL 后 runner 与孙进程**均已死亡**（此前单 PID KILL 下二者均存活，见 F-新2）。**Linux 侧本轮未实测**，由 CI 泳道（`mechanical-gates.yml`，ubuntu-latest）判定，同 D1 的 A1 分工——不接受「macOS 绿就算过」。

**🔴 自杀风险守卫（MUST）**：`kill -KILL -"$PID"` 前 MUST 同时满足：① 目标确实是组长（`ps -o pgid= -p "$PID"` 取到的值 == `$PID` 本身）；② 该 PGID 不等于脚本自身的 PGID（`ps -o pgid= -p $$`）。任一不满足（含 PGID 取不到）一律退回既有单 PID `kill -KILL "$PID"`，**MUST NOT 猜**。实现见 `_ov_group_kill_decision`（纯判定函数，`_ov_pgid_of` 取值）。

**守卫自身的诚实边界（新增，与(a)(b)(c)那类不可消除的时序窗口性质不同，是刻意的保守退化）**：守卫不通过时退回单 PID KILL——对「runner 未忽略 TERM」的绝大多数场景无影响（TERM 阶段本就已把子树带走，见上方实测）；仅在「runner 主动忽略 TERM **且** 组信号守卫两条件之一不满足（如 `timeout` 实现不是 GNU/未 `setpgid`）」的交集场景，会退回旧行为（子树可能仍逃逸）。降级时 stderr 打印 `OV_GROUP_KILL_DEGRADED=1 reason=<pgid-unavailable|not-leader|own-group> pid=<PID> target_pgid=<val> own_pgid=<val>`（结构化字段，MUST NOT 含 context 正文，同 `OV_UTF8_BACKSCAN_UNAVAILABLE=1` 规格），使该退化路径对外可见、不再是零信号静默降级。

**🔴 诚实边界（MUST NOT 声称根治）** — 以下**三条残余并列**，性质相同：都是 shell 层**不可干净消除**的窗口，只登记、不声称已解决（adr/0018）。文档与实现 **MUST** 显式登记：

| # | 残余 | 成因 | 后果 |
|---|---|---|---|
| **(a)** | 父进程被 **SIGKILL** | trap 在 `-9` 下根本不执行 | 孤儿**仍存活**（实测） |
| **(b)** | **PID 记录窗口**：`<runner> … &` 与 `OV_RUNNER_PID=$!` 之间 | 后台启动与 `$!` 赋值**不可原子化** | pending trap 带**空 PID** 执行 ⇒ 该次 runner **逃逸成孤儿** |
| **(c)** | **PID 清零窗口**：`wait` 返回与 `OV_RUNNER_PID=""` 之间 | `wait` 返回与清零**不可原子化** | 对**已回收、可能已被系统复用**的 PID 开火（`kill -0` 会通过）⇒ 可能误杀无关进程 |

**(c) 在 D2.1 之后爆炸半径变大，一并登记〔Standards 轴 Minor〕**：`ov_cleanup` 的 `kill -0` 探活成功、到 `_ov_pgid_of` 取 PGID 之间同样存在不可原子化的窗口。若 PID 恰在此刻被回收并复用给一个**碰巧自身即组长**的无关新进程，守卫两条件会双双通过 ⇒ 误杀落到**整个无关进程组**上，而非 D2.1 之前的单个无关进程。**这是 (c) 的同族扩展，不是新残余**（成因同为「PID 复用 + 不可原子化窗口」），但**代价被组级升级放大了**，故显式记此一笔——**MUST NOT** 让读者以为组级 KILL 路径不含 (c) 类残余。概率极低（PID 复用 ∧ 新进程恰为异组组长），且与 (a)(b)(c) 同样**须由调用方在更外层回收**才能真正覆盖。

三者要覆盖都须由调用方在**更外层**（进程组 / cgroup / 容器）回收。本 helper 只保证「可捕获信号 + 正常退出」两类路径，且**窗口外的绝大多数时刻正确**。**MUST NOT** 因为 D2.1 治好了 (d) 就顺手声称孤儿问题已彻底根治——(a)(b)(c) 依然是真实、无解的残余。

## 失败模式表〔TG-08 · BASE-06〕

| # | 失败模式 | 检测方式 | 处置 | 退出码 |
|---|---|---|---|---|
| F1 | context 截断落在多字节字符内 | 回扫检查 continuation 字节 | 回退到字符边界 | 不影响（0） |
| F2 | `od` 不可用 | 命令预检 | **fail-loud**：报缺依赖（同既有 `timeout` 缺失路径） | 非零 |
| F3 | runner 超时 | `timeout` 返回 124 | 原样透传，落 `reason_code="timeout"` | 124 |
| F4 | 父进程 SIGINT / SIGTERM / SIGHUP | trap | 杀 runner + 清 workdir | 143（TERM 惯例；调用方侧 `.rc` 缺席 ⇒ catch-all → `exec-error`） |
| F5 | 父进程 **SIGKILL** | **不可检测** | **残余(a)：孤儿存活**，显式登记不掩盖 | — |
| F6 | 信号落在 `&` 与 `OV_RUNNER_PID=$!` 之间 | **不可检测** | **残余(b)：空 PID ⇒ 该次 runner 逃逸**，显式登记 | 128+signum |
| F7 | 信号落在 `wait` 返回与 `OV_RUNNER_PID=""` 之间 | **不可检测** | **残余(c)：对已回收/可能已复用的 PID 开火**，显式登记 | 128+signum |
| F8 | runner 主动 `trap '' TERM` 忽略终止信号 | pytest 实测（`test_runner_ignoring_term_dies_under_group_kill_escalation`） | **已治〔D2.1〕**：`ov_cleanup` 的 KILL 升级在守卫通过时改投递目标为负号进程组，子树随 `timeout` 一并灭失；守卫未通过时退回单 PID KILL 并打 `OV_GROUP_KILL_DEGRADED=1` 哨兵，不再是零信号静默降级 | 143（父侧退出码不变） |

## 可观测性〔TG-08 · BASE-11〕

- **B9**：截断时 stderr 已有 `OV_TRUNCATED=true`（既有）。**新增**：回扫实际丢弃的字节数，便于事后判断截断是否吃掉了有效内容。
- **B10**：清理路径 stderr 记一行「已终止 runner PID N」，让「父被回收」在日志里可见，而非静默消失。
- **新增 stderr 内容 MUST NOT 含 context 正文**——只报字节计数与 PID（该内容未经出境扫描）。

## 安全与数据保护〔TG-17 · BASE-28〕

- **截断改动位于 `secret_scan` 之后**〔广审已核实定论，非待办〕：`secret_scan "$ctx"`（:153）在截断分支（:158）**之前**扫**整个 context 文件**，`do_exec` 另有预扫 ⇒ 修改截断**不缩小**密钥扫描覆盖面，无出境安全回归。
- **不改出境侧扫描**：runner 回传的 findings 仍走既有 `secret_scan`（`host-adaptive-execution`「出境安全三件套对两条 runner 路径一视同仁」）。

## Risks / Trade-offs

- **[A1 未闭：Linux 侧截断行为未实测]** → 缓解：CI 泳道跑切点扫描测试（`mechanical-gates.yml` 已是 ubuntu-latest）。**不接受「macOS 绿就算过」**——`windows-ci-bash-subprocess-traps` 就是这么被咬的。
- **[SIGKILL 孤儿 (a) · PID 记录窗口 (b) · PID 清零窗口 (c)]** → 均**无缓解**，见 D2 诚实边界三条表。要覆盖须调用方在更外层（进程组 / cgroup / 容器）回收。
- **[组级 KILL 守卫的退化路径〔D2.1〕]** → 缓解：`OV_GROUP_KILL_DEGRADED=1` 结构化 stderr 哨兵使降级可观测；**MUST NOT** 声称该守卫覆盖所有 `timeout` 实现——非 GNU / 未 `setpgid` 的 `timeout` 会触发 `reason=not-leader` 降级，此时仍退回原有的单 PID 行为（旧残余(d)在该交集场景下未变化）。
- **[改 `assets/hack/` 后忘记跑 `setup.sh`]** → **显式登记**：`outside-voice.sh` 不在任何机械保护范围内（它是 shell、不走 recorder 取数路径）。本 change **不**声称覆盖它。

## Migration Plan

1. 改 `sdflow-init/assets/hack/outside-voice.sh`（bundle **唯一权威源**）→ 开发 checkout 跑 `bash setup.sh` 才测得到（拷贝非 symlink）。
2. **回滚**：两条改动彼此独立，可单独 revert；回滚后须重跑 `setup.sh`。
3. **下游**：经 `sdflow-init update` 推 bundle；对下游是纯修复、无接口变化。

## 切片建议（仓 `impl-pipeline: tickets`，建议非契约）

| # | 切片 | Blocked-by | 覆盖 |
|---|---|---|---|
| 1 | 截断字符边界安全 + 切点扫描测试 + 变异验证 | none | R1 |
| 2 | runner 子进程生命周期 + SIGTERM 验尸测试 | none | R2 |
| 3 | Linux CI 泳道 + `setup.sh` + 全套件 + parity 门 | 1,2 | A1 |

1 与 2 无耦合，可并行。

## Open Questions〔TG-21〕

*（全部关闭，保留结论供追溯）*

| # | 问题 | 结论 |
|---|---|---|
| Q1 | 截断用 bash 回扫还是 python3？ | **bash**（零新增依赖；且 helper 是 bundle 权威源，加依赖的代价由所有下游承担）。python3 留作干净次选，属**偏好非技术证伪** |
| Q2 | 143 是否需进 `reason_code` 枚举？ | **不需要**。async 段已有未知码 catch-all → `exec-error`；且 helper 被 TERM 时 `.rc` 本就缺席，走同一条路 |
| Q3 | `secret_scan` 与截断的次序要不要实现期复核？ | **不需要**，广审已定论：扫描在截断之前、扫的是整文件，无回归 |

## Compliance

逐条 ADR / 边界核对见 `proposal.md`「Compliance」节（D-6），此处不复制。

**本文额外承担的合规点**：
- **D-1**：上方「代码事实」表全部经 grep 核验并由接地镜逐条复核，无记忆直写。
- **D-4**（外部依赖声明超时与回滚）：runner 超时沿用既有 `--timeout`（缺省 300s）+ `timeout -k 10`；本 change 无写盘操作 ⇒ 无回滚路径需求。
- **基准 ⑤**：D1 明确限定 UTF-8 有界面，禁止演化为编码嗅探。
