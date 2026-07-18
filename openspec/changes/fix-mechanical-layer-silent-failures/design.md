# design — fix-mechanical-layer-silent-failures

## Context

三条缺陷同形：**`exit 0`，事情没做成**。动机与实证见 `proposal.md`，需求见 `specs/`。本文只讲**怎么做**。

**代码事实**（D-1，均已 grep 核验，非记忆）：

| 事实 | 出处 |
|---|---|
| 截断用 `head -c` / `tail -c` 在字节边界切 | `outside-voice.sh` `render_prompt()` |
| trap 只清 workdir、runner 前台执行 | `outside-voice.sh` `do_exec()`：`trap "rm -rf '$workdir'" EXIT` |
| 脚本是 **bash 不是 POSIX sh** | `outside-voice.sh` 第 1 行 `#!/usr/bin/env bash`；内部已用 bash 数组与 `local` |
| sibling 按**自身文件位置**定位（设计如此，有长注释） | `issues.py` `SCRIPT_DIR` / `SKILLS_ROOT` / `BUGLIST_SCRIPT` / `TODOLIST_SCRIPT` |
| `problems` 非空**只回显、显式不收紧退出码** | `issues.py` `cmd_sweep` 内 `[impl-review-fix] FIX-1` 注释原话 |
| `tagged` 为空直接 `return`（0 命中当合法幂等态） | `issues.py` `cmd_sweep` 内 `[impl-review-fix] FIX-2` |
| 共用取数路径 | `issues.py`：`_scan_pool` → `read_pool` → `_reindex_core` → `cmd_reindex` / `cmd_batch_rename` 等 |
| frontmatter **数据** schema 常量 = `1` | `buglist.py`：`model["schema"] != 1` 校验 |
| `buglist.py` 现有子命令 | `next-id, add, set-status, triage, scan`（**无版本自报入口**） |

## Goals / Non-Goals

**Goals**：R1–R5（见 proposal 优先级表）。
**Non-Goals**：见 `proposal.md`「Non-Goals」节，每条附可证伪假设（D-3），此处不复制。

## 组件与调用关系

```
        ┌──────────────────────────── issues.py（调用方）────────────────────────────┐
        │  cmd_sweep   cmd_reindex   cmd_batch_rename   cmd_batch_add   set-status   │
        │      │            │              │                 │              │        │
        │      │            └──────┬───────┴─────────────────┴──────────────┘        │
        │      │            _reindex_core                                            │
        │      │                   │                                                 │
        │      └───────────┬───────┘                                                 │
        │              read_pool ──► _scan_pool ──►【★ 握手闸门落这里 ★】             │
        └───────────────────────────────┬─────────────────────────────────────────────┘
                                        │ subprocess（按自身文件位置定位 sibling）
                        ┌───────────────┴───────────────┐
                  buglist.py                       todolist.py
                （版本自报入口 + scan）           （版本自报入口 + scan）

   ⚠ 偏斜面：~/.claude/skills/sdflow-issues ─symlink─► 运行 checkout（可滞后于开发 checkout）
```

**闸门位置是本设计的核心判断**：落在 `_scan_pool`（唯一的派子进程点）⇒ `sweep` / `reindex` / `batch rename` / `batch add` / `set-status` / `lint` **一次全保**。落在 `cmd_sweep` 里就是点补，会重演「修完 sweep、reindex 照瞎」（基准 ③ 面治）。

## 握手时序（写盘类子命令）

```
 caller            issues.py            buglist.py / todolist.py        盘面
   │                   │                          │                      │
   │─ reindex ────────►│                          │                      │
   │                   │─ 版本自报 ──────────────►│                      │
   │                   │◄─ 支持的 frontmatter ────│                      │
   │                   │   schema 上限 (int)       │                      │
   │            ┌──────┴──────┐                                          │
   │            │ < 预期 或    │  ── 非零退出 + 可执行指令 ──────────────►│ 字节未变 ✅
   │            │ 入口不存在   │     （MUST 前置于任何 discovery/写盘）    │
   │            └──────┬──────┘                                          │
   │                   │ ≥ 预期                                           │
   │                   │─ scan --json ───────────►│                      │
   │                   │◄─ items + problems ──────│                      │
   │                   │─ 计算 → 写盘 ───────────────────────────────────►│
```

## Decisions〔TG-23 · ADR 记录〕

### D1 — 截断：纯 bash 边界回扫（在切点上调整），零新增运行时依赖

**选它的理由**：UTF-8 是**有界**语法面（单字符 ≤4 字节、continuation 字节形态确定）⇒ 基准 ⑤ 允许确定性处理；且**在切点上回退**比「切完再清洗」语义更干净——不产生「先造出非法字节再补救」的中间态。

**实测**（macOS，混合 ASCII / 3 字节 CJK / 4 字节 emoji 语料）：201 个连续切点，头段与尾段**分别**严格模式解码 UTF-8，**失败 0**；纯 ASCII 时丢弃 0 字节；100KB 文件耗时 `0.016s`（只读 ≤4 字节，与文件大小无关）。

**代价**：约 20 行 bash + 依赖 `od`（macOS / Linux 基础系统均自带，且 `head -c` / `tail -c` 已在用）。

**备选（均已实测，记录证伪结论以免后人重蹈）**：

| 备选 | 结论 |
|---|---|
| `iconv -f UTF-8 -t UTF-8 -c` | **部分证伪**。macOS 实测：尾部序列不完整的**头段** `rc=1` + stderr `unexpected end of file; the last character is incomplete.`（stdout 仍合法）⇒ 必须显式吞 rc 与 stderr，否则在日志里制造假故障。且**本机无 GNU iconv、无容器可验** ⇒ GNU 侧一致性**未验证** = 跨平台风险，这是不选它的决定性理由 |
| `python3 -c … .decode('utf-8','ignore')` | 实测两半均正确。**唯一缺点**：给 helper 新增 python3 运行时依赖（该脚本目前零 python3 依赖）。**保留为干净次选** |
| `perl -Mopen=std,:utf8` | macOS 系统 perl 上 `rc=255`（`Unknown PerlIO layer class 'std'`）。可写对，但既然要调外部解释器，不如 python3 |

**边界（MUST）**：只认 UTF-8，**MUST NOT** 演化成编码检测 / 嗅探——那是无界面，正是基准 ⑤ 的警号（「每轮 review 都在同一个函数里补一个新分支」）。

### D2 — 子进程：后台 + `wait` + trap 补 `INT TERM HUP`

**先证实两件事**（避免修错地方）：① bash 的 **EXIT trap 在 SIGTERM 下确实会跑**（实测 `EXIT-TRAP-RAN`，所以 workdir 才被清了）；② 但**前台 `timeout` 完全不受影响**（实测 `42998 1 timeout -k 10 60 sleep 45`，ppid 已成 1）。**∴ 病根不是 trap 没跑，是 trap 里没有子 PID 可杀。**

**做法**：runner 改后台启动、记 PID、`wait` 取回退出码；清理函数先 `kill -TERM` 该 PID、宽限后 `kill -KILL` 兜底，再删 workdir；trap 覆盖 `INT TERM HUP` 与 `EXIT`。

**关键实测**：杀 `timeout` **会连带杀掉孙进程**——让 `timeout` 跑一个自己再 spawn `sleep 300` 的脚本，TERM 后 `timeout` / 中间脚本 / `sleep 300` **三层全灭**（GNU timeout 自建进程组并转发信号，实测三者 pgid 相同）。∴ 无需自己管进程组。

**退出码无回归**：`wait` 后 `rc=124`（超时）/ `0` / 其他非零码**原样透传**；后台化后 stdin/stdout 重定向照常。

**备选**：`setsid` + `kill -- -PGID` —— **证伪**：`setsid` 在 macOS（Darwin 25）**不存在**（Linux util-linux 才有）；且上条实测表明 timeout 已自建进程组、信号转发足够，**收益为零**。

**🔴 诚实边界（MUST NOT 声称根治）**：父进程被 **SIGKILL** 时 trap 不可执行，实测孤儿**仍存活**。shell 层无解。文档与实现 **MUST** 显式登记该残余，**MUST NOT** 写成「已消除孤儿」。

### D3 — 握手信号：sibling 自报「能读的 frontmatter schema 上限」，而非脚本版本号

**为什么不用脚本版本 / git SHA**：版本号与「能不能读懂这份盘面」只是相关、不是**因果**；一旦分叉或本地改动就失真。

**为什么不直接复用现成的 `schema=1` 常量**：那是**数据** schema（frontmatter 里写的那个 `1`），描述的是**盘面**；握手要问的是**脚本的能力**——「你读得懂 schema=1 的 frontmatter 吗」。两者是不同范畴，混用会造出一个**看起来像机械门、实则问错问题**的假绿（`signal-exists-not-equal-mechanical-capture` 同族坑）。

**做法**：`buglist.py` / `todolist.py` 各加只读入口，输出其**支持的 frontmatter schema 上限**（整数）。`issues.py` 要求 `≥ 1`。

**语义自然正确**：滞后版本根本没有 frontmatter 解析能力（实测 `grep -c overlay`：开发版 **7** / 运行版 **0**）⇒ 它**连这个入口都没有** ⇒ 调用即报错 ⇒ 按失配处置（已写进 spec 的第三个 Scenario）。**不存在「旧脚本误报支持」的路径**——这正是选这个信号的价值。

### D4 — 反静默红线取 `problems` 非空，不取 `tagged == 0`

`tagged == 0` **是合法幂等态**（重跑时本就无未分诊项），拿它当红线会把正常重跑判红。`problems` 非空才是「两套投影失配」的确定性信号。缺省严格，**MAY** 留显式逃生口（`--allow-problems`），逃生时 stderr 仍完整记录。

> 现状注释写着「不收紧退出码（更强的 enforcement 是延后的 roadmap T2.5）」——本 change **提前兑现该 defer**，因为已实证它正是损害放大器。这是「以目标态为准」，不是「因为原计划延后所以继续延后」。

### D5 — 闸门前置于 discovery / 写盘（承 `adr/0022`）

`reindex` 现状是**先算后覆盖**；握手若落在计算之后，仍可能在报错前已经写盘。∴ 校验 **MUST** 前置到任何 discovery / stat / open 之前——与 `adr/0025` 对 lock owner 的「必须在所有 result-affecting discovery 前 acquire」同款纪律。

## 失败模式表〔TG-08 · BASE-06〕

| # | 失败模式 | 检测方式 | 处置 | 退出码 |
|---|---|---|---|---|
| F1 | context 截断落在多字节字符内 | 回扫检查 continuation 字节 | 回退到字符边界 | 不影响（0） |
| F2 | `od` 不可用 | 命令预检 | **fail-loud**：报缺依赖（同既有 `timeout` 缺失路径） | 非零 |
| F3 | runner 超时 | `timeout` 返回 124 | 原样透传，落 `reason_code="timeout"` | 124 |
| F4 | 父进程 SIGTERM/INT/HUP | trap | 杀 runner + 清 workdir | 143（TERM 惯例） |
| F5 | 父进程 **SIGKILL** | **不可检测** | **残余：孤儿存活**，显式登记不掩盖 | — |
| F6 | sibling 版本滞后 / 无自报入口 | 握手预检 | fail-closed，零写盘 + 可执行指令 | 非零 |
| F7 | sibling 脚本文件不存在 | 路径预检（既有） | 沿用既有 `_die` | 非零 |
| F8 | scan 返回 `problems` 非空 | JSON `problems` 字段 | 非零退出（除非显式逃生口） | 非零 |
| F9 | 握手通过但 scan 仍失败 | `proc.returncode` | 沿用既有 `_die` | 非零 |

**F4 的退出码 143 需登记**：现有 outside-voice 契约 `reason_code` 枚举中**无对应值**。本 change **不新增枚举**（Non-Goal）——143 只在「父进程被信号回收」时出现，此时**调用方自身也已死**，无人落锚，故不构成锚契约缺口。**该推理 MUST 在实现期复核**：若发现存在「父活着但 helper 收到 TERM」的路径，则此假设被证伪，须回头议枚举。

## 可观测性〔TG-08 · BASE-11〕

- **B9**：截断时 stderr 已有 `OV_TRUNCATED=true`（既有）。**新增**：回扫实际丢弃的字节数，便于事后判断截断是否吃掉了有效内容。
- **B10**：清理路径 stderr 记一行「已终止 runner PID N」，让「父被回收」在日志里可见，而非静默消失。
- **B11**：失配时 stderr **MUST** 同时给出**期望值、实得值、sibling 的解析路径**——只说「版本不匹配」不 actionable；给出路径才能让人一眼看出「哦我调的是运行 checkout」。

## 安全与数据保护〔TG-17 · BASE-28〕

- **截断改动位于 `secret_scan` 之后**：`secret_scan` 扫的是**整个 context 文件**（截断前），故修改截断**不缩小**密钥扫描覆盖面。**MUST 在实现期复核该次序**——若次序反了，截断改动会改变送出内容而未被扫描，属出境安全回归。
- **不改出境侧扫描**：runner 回传的 findings 仍走既有 `secret_scan`（`host-adaptive-execution`「出境安全三件套对两条 runner 路径一视同仁」）。
- **B11 的 fail-closed 是数据保护动作**：阻止用残缺集合覆盖权威 INDEX，属**防数据丢失**，与 `adr/0022`（可改不可删）同向。
- **新增 stderr 内容不含 context 正文**：只报字节计数与路径，**MUST NOT** 把 context 片段写进日志（该内容未经出境扫描）。

## Risks / Trade-offs

- **[A1 未闭：Linux 侧截断行为未实测]** → 缓解：CI 泳道跑切点扫描测试（`mechanical-gates.yml` 已是 ubuntu-latest）。**不接受「macOS 绿就算过」**——`windows-ci-bash-subprocess-traps` 就是这么被咬的。
- **[fail-closed 卡住自动链路]** → 缓解：错误信息必须 actionable（升级 + `setup.sh` 两条命令）；且 `/sdflow-done` 的 sweep 子步契约本就是「非原子、fail-closed、重跑收敛」，硬停与之相容。**须在实现期通读全部调用点确认**（假设 A3）。
- **[存量含 legacy 不一致的仓开始变红]** → 接受：本就该修；且 `--allow-problems` 提供知情放行。
- **[改 `assets/hack/` 后忘记跑 `setup.sh`]** → 这正是本 change R2 要机械化的那类偏斜；但 **`outside-voice.sh` 自身不在握手保护范围内**（它是 shell、不走 recorder 取数路径）⇒ **残余风险，显式登记**。
- **[SIGKILL 孤儿]** → 无缓解，见 D2 诚实边界。

## Migration Plan

1. 改 `sdflow-init/assets/hack/outside-voice.sh`（bundle **唯一权威源**）→ 开发 checkout 跑 `bash setup.sh` 才测得到（拷贝非 symlink）。
2. 改三个 recorder 脚本 → symlink 场景即时生效，但**运行 checkout 仍需 pull + setup** 才拿到新版。
3. **回滚**：三处改动彼此独立，可单独 revert；`outside-voice.sh` 回滚后须重跑 `setup.sh`。
4. **下游**：经 `sdflow-init update` 推 bundle；对下游是纯修复、无接口变化。

## 切片建议（仓 `impl-pipeline: tickets`，建议非契约）

| # | 切片 | Blocked-by | 覆盖 |
|---|---|---|---|
| 1 | 截断字符边界安全 + 切点扫描测试 | none | R1 |
| 2 | runner 子进程生命周期 + SIGTERM 验尸测试 | none | R4 |
| 3 | sibling 版本自报入口（两个被调脚本） | none | R2 前半 |
| 4 | `_scan_pool` 握手闸门 + 逐调用方偏斜断言 | 3 | R2 后半、R5 |
| 5 | `problems` 非空 ⇒ 非零退出 + 逃生口 | none | R3 |
| 6 | Linux CI 泳道覆盖（闭 A1） | 1 | A1 |

1/2 与 3/4/5 分属两个文件族，无耦合，可并行；4 依赖 3。

## Open Questions〔TG-21〕

| # | 问题 | 负责人 | 截止 |
|---|---|---|---|
| Q1 | `--allow-problems` 逃生口是否真有使用场景？若无，缺省严格且**不提供**逃生口更干净（少一个假绿入口） | 实现期，读完全部调用点后定 | Task 5 前 |
| Q2 | 143 退出码是否需要进 `reason_code` 枚举（见失败模式表 F4 的待复核假设） | 实现期复核 | Task 2 前 |

## Compliance

逐条 ADR / 边界核对见 `proposal.md`「Compliance」节（D-6，含 `adr/0005` / `0008` / `0010` / `0011` / `0018` / `0022` / `0025` 与跨模块共享数据模型边界的显式未越界确认），此处不复制。

**本文额外承担的合规点**：
- **D-1**：上方「代码事实」表全部经 grep 核验，无记忆直写。
- **D-4**（外部依赖声明超时与回滚）：runner 超时沿用既有 `--timeout`（缺省 300s）+ `timeout -k 10`；握手为只读预检、无写操作故无回滚路径；写盘类子命令的回滚 = fail-closed 前置 ⇒ **不产生需回滚的中间态**。
- **基准 ⑤**：D1 明确限定 UTF-8 有界面，禁止演化为编码嗅探。
