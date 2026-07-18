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
| `problems_out` **默认 None ⇒ 诊断默认被丢弃**，只有 `cmd_reindex` 显式传 | `issues.py` `_scan_pool` / `read_pool` docstring 原话 |
| `reindex --strict` **已存在且零消费者**（「本 change 内无消费者主动传它」） | `issues.py` `cmd_reindex` docstring 原话；全仓 grep 无调用 |
| `problems` 是**自由散文字符串列表**（`f"marker 嵌套：…"` 等） | `buglist.py` 各 `problems.append(...)` 点 |
| sibling 恒解析到**同一 checkout**（两个入口实测） | `SKILLS_ROOT` = 本脚本位置上两级 |
| `truncated=` 落锚但**全仓零消费者** | grep 仅命中两层 SKILL.md 的锚行模板 |
| 未知退出码有 catch-all → `exec-error` | 两层 SKILL.md async 段第 ⑦ 条 |
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
〔gstack-amendment · 初版此图为**虚构拓扑**，经广审 critical 打穿后按实测重画〕

```
   ── 路径 ①：subprocess scan（有 JSON 字段，可承载 additive 阻断集）──────────────
     cmd_sweep ──── 自己 subprocess 解析 `scan --json`（不经 read_pool）
     _reindex_core ── read_pool ──► _scan_pool ──► subprocess buglist.py / todolist.py
         ▲                                             （诊断在产生处分级）
         ├── cmd_reindex
         └── cmd_batch_rename（**但见路径 ②：它先写盘、后到这里**）

   ── 路径 ②：in-process 解析（**无 JSON 字段，缺席即阻断在此完全失效**）─────────
     cmd_batch_rename ──► read_rename_snapshot ──► retag
                          └─► atomic_write(registry)      ← 写盘 ①
                          └─► atomic_write_bytes(dated)   ← 写盘 ②
                          └─► _reindex_core               ← 阻断判定**才**发生（太晚）

   ── 路径 ③：只读 batches.md，根本不碰两池 ─────────────────────────────────
     cmd_batch_lint ──► _batch_lint_snapshot
     cmd_batch_add / cmd_batch_set_status ──► _read_batches_lines

   ⚠ 偏斜面：脚本 ↔ 盘面数据（不是脚本 ↔ 脚本——sibling 恒同 checkout）
   ⚠ 第三份 parser：`issues.py` 自持 recorder parser（`:298-511`），路径 ② 用它，**不在任何防线内**
```

**初版断言「6 个调用方经共用入口 ⇒ 一次全保」是虚构的**，实测拓扑如上。据此重定：

| 路径 | 调用方 | 阻断机制 | 说明 |
|---|---|---|---|
| ① | `sweep`、`reindex`、`rename`(后半) | **additive 字段 + 缺席即阻断** | 有 JSON 边界，枢纽机制成立 |
| ② | `rename`(前半) | **须另立机制**（见 D5′） | in-process、无字段可缺席；且**写盘先于判定** |
| ③ | `lint`、`batch add`、`set-status` | **不适用** | 不读两池 ⇒ 无「读残缺」风险，**不该为它们写阻断断言** |

🔴 **路径 ③ 的三个调用方原本被写进 tasks 4.4 的「逐调用方阻断断言」——那会是三条写不出真断言的假绿。已删。**（讽刺：本 change 正是为消灭假绿而开。）

**现状对照（仍成立）**：`_scan_pool(script, root, pool, problems_out=None)` 的 `problems_out` **默认 None**，注释写明「只有显式传入列表的调用方（`cmd_reindex`）才会拿到这份信号」⇒ 路径 ① 上 `rename` 拿不到诊断。这不是"漏了一处"，是取数层默认丢弃诊断。

## 阻断判定时序（写盘类子命令）

```
 caller            issues.py            buglist.py / todolist.py        盘面
   │                   │                          │                      │
   │─ reindex ────────►│                          │                      │
   │                   │─ scan --json ───────────►│                      │
   │                   │◄─ items + problems ──────│                      │
   │                   │   + 阻断集（可能缺席）      │                      │
   │            ┌──────┴──────────────┐                                  │
   │            │ 阻断集非空，或        │ ── exit≠0 + 出路 ───────────────►│ 字节未变 ✅
   │            │ 字段缺席(⇒全阻断)     │   （MUST 前置于任何 discovery/写盘）│
   │            └──────┬──────────────┘                                  │
   │                   │ 阻断集为空                                        │
   │                   │─ 计算 → 写盘 ───────────────────────────────────►│
   │                   │  （若经逃生口放行 ⇒ INDEX banner 增记留疤）        │
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
| `python3 -c … .decode('utf-8','ignore')` | 实测两半均正确。**唯一缺点**：给 helper 新增 python3 运行时依赖。〔gstack-amendment · 广审 medium：措辞修正——helper 的调用方本就是**跑 python 脚本的 skill 链**，∴ 这是**偏好而非硬约束**，MUST NOT 写成技术证伪。若 bash 版在实现期显出维护成本，切 python3 是正当的〕**保留为干净次选** |
| `perl -Mopen=std,:utf8` | macOS 系统 perl 上 `rc=255`（`Unknown PerlIO layer class 'std'`）。可写对，但既然要调外部解释器，不如 python3 |

**边界（MUST）**：只认 UTF-8，**MUST NOT** 演化成编码检测 / 嗅探——那是无界面，正是基准 ⑤ 的警号（「每轮 review 都在同一个函数里补一个新分支」）。

### D2 — 子进程：后台 + `wait` + trap 补 `INT TERM HUP`

**先证实两件事**（避免修错地方）：① bash 的 **EXIT trap 在 SIGTERM 下确实会跑**（实测 `EXIT-TRAP-RAN`，所以 workdir 才被清了）；② 但**前台 `timeout` 完全不受影响**（实测 `42998 1 timeout -k 10 60 sleep 45`，ppid 已成 1）。**∴ 病根不是 trap 没跑，是 trap 里没有子 PID 可杀。**

**做法**：runner 改后台启动、记 PID、`wait` 取回退出码；清理函数先 `kill -TERM` 该 PID、宽限后 `kill -KILL` 兜底，再删 workdir；trap 覆盖 `INT TERM HUP` 与 `EXIT`。

**关键实测**：杀 `timeout` **会连带杀掉孙进程**——让 `timeout` 跑一个自己再 spawn `sleep 300` 的脚本，TERM 后 `timeout` / 中间脚本 / `sleep 300` **三层全灭**（GNU timeout 自建进程组并转发信号，实测三者 pgid 相同）。∴ 无需自己管进程组。

**退出码无回归**：`wait` 后 `rc=124`（超时）/ `0` / 其他非零码**原样透传**；后台化后 stdin/stdout 重定向照常。

**备选**：`setsid` + `kill -- -PGID` —— **证伪**：`setsid` 在 macOS（Darwin 25）**不存在**（Linux util-linux 才有）；且上条实测表明 timeout 已自建进程组、信号转发足够，**收益为零**。

**🔴 诚实边界（MUST NOT 声称根治）**：父进程被 **SIGKILL** 时 trap 不可执行，实测孤儿**仍存活**。shell 层无解。文档与实现 **MUST** 显式登记该残余，**MUST NOT** 写成「已消除孤儿」。

### D3 — 诊断信号在产生处分级，additive 字段承载，缺席即阻断 〔grill 收敛，取代初版握手方案〕

**初版方案（sibling 版本握手）已被实测证伪，记录于此防重提**：sibling 恒由 `SKILLS_ROOT`（本脚本位置上两级）解析 ⇒ **永远同 checkout** ⇒ 二者永不相对偏斜。真实故障里两个都是旧的，握手一致放行——**那是一道在它本该拦住的故障上恒绿的门**。真正的偏斜轴是**脚本 ↔ 盘面数据**。

**改判后的做法**：

1. **分级落产生处**：`problems.append(...)` 的同一位置就知道这条属于「可能没读全」还是「读全了但某条脏」，直接分类。**MUST NOT 由消费方正则匹配散文文本还原**——那是无界语法面手搓解析器（基准 ⑤），且三脚本措辞各自演进必然漂移，正是「每轮 review 补一个新分支」的警号。
2. **additive 承载**：新增阻断集字段，`problems` 字段本身不动 ⇒ 只读 `problems` 的既有消费者零影响。
3. **缺席 ⇒ 全部阻断**（fail-closed）。

**第 3 条是本设计的枢纽**，它一条办三件事：老 sibling 没这个字段 ⇒ 全阻断 ⇒ **版本偏斜被同一机制接住**（初版要造的那道门，功能在这里自然长出来）；新 sibling ⇒ 精确分级；第三方只读 `problems` ⇒ 零影响。**向后兼容与保守处置在这里指向同一个方向，不需要在两者之间权衡。**

**切分判据（承 `adr/0018` 铁律 (d)）**：**该信号是否污染本次输出的完整性**，而非严重程度感受。

| 诊断 | 含义 | 归类 |
|---|---|---|
| `块有 X 但缺总览表行` | 可能漏读条目 | **阻断** |
| `frontmatter 有 X 但缺 marker block` | 同上 | **阻断** |
| `X 行 arity 异常：N 列` | 读全了，某行脏 | 告警 |
| `marker block 重复：X` | 读全了，某条脏 | 告警 |

**前向保护不重复造**：`buglist.py` 的 `_validated_recorder_model()` 已对 `schema != 1` fail-closed（schema 升 2 时旧脚本硬停）。本 change 只给它补**回归锁 + 变异验证**——它是承重的却没有测试锁。

### D4 — 严格是默认值；逃生口留疤、禁环境化、禁自动传

红线取**阻断集非空**，不取 `tagged == 0`（后者是合法幂等态，拿它当红线会把正常重跑判红）。

**默认必须翻转，理由是实证而非偏好**：现状注释写着「默认仍 exit 0——reindex 本身该做的事已经做完」，而 `--strict` **已存在且零消费者**。**一个没人传的开关，等于给错误的默认值发了一张免责声明。** 实测后果：INDEX 从 122 项塌成 108 项、B9–B12 蒸发，exit 0。

∴ 逃生口的设计标准不是「存不存在」而是「**用了留不留痕**」，三条约束缺一不可：

1. **产物带疤**：放行时 `INDEX.md` 头部 banner 增记一行（N 条阻断被放行、索引可能不完整）——**妥协随产物进 git**，下一个读 INDEX 的人一眼看见，而不是只在某次终端输出里闪过。
   🔴 **适用面受限 〔gstack-amendment · 广审 high〕**：banner 由 `INDEX_BANNER` 生成，**只有写 INDEX 的命令有这个载体**（`reindex`，及经它的 `sweep`/`rename`）。`lint`/`batch add`/`set-status` 走路径 ③、不读两池，本就不产生阻断 ⇒ 无此问题。**spec 的「放行留痕」Scenario MUST 限定适用调用方**，MUST NOT 写成对所有命令成立——那会是一条永远测不出来的空要求；
2. **禁环境化**：只认显式 CLI 参数，**MUST NOT** 支持 config / 环境变量——逃生口的真正死法是被写进配置后全仓永久生效、之后没人记得门还在；
3. **禁自动传**：`/sdflow-done` sweep 子步 **MUST NOT** 自动传。

**为什么不干脆不给**：手工编辑过的老仓可能长期存在合法的表↔块失配 ⇒ `reindex` 被**永久楔死**、INDEX 再也重建不了，还会逼人去手改带 `DO NOT EDIT` banner 的生成文件。那比给逃生口更糟。

### D5 — 阻断判定前置于 discovery / 写盘（承 `adr/0022`）

`reindex` 现状是**先算后覆盖**；判定若落在计算之后，仍可能在报错前已经写盘。∴ **MUST** 前置到任何 discovery / stat / open 之前——与 `adr/0025` 对 lock owner 的「必须在所有 result-affecting discovery 前 acquire」同款纪律。

### D5′ — 路径 ② (`batch rename`) 须另立机制 〔gstack-amendment · 广审 critical〕

**D5 在 rename 路径上直接不成立**，实测调用序：

```
read_rename_snapshot → retag → atomic_write(registry) → atomic_write_bytes(dated) → _reindex_core
                                └── 写盘已发生 ──┘          └── 阻断判定在这之后才跑（太晚）
```

且该路径是 **in-process 解析**（`issues.py` 自持的第三份 recorder parser，`:298-511`），**没有 JSON 边界** ⇒ 「additive 字段 + 缺席即阻断」这个枢纽机制**在此完全失效**——不存在"可缺席的字段"。

**做法**：`read_rename_snapshot` 完成解析后、**在 `retag` 与任何 `atomic_write` 之前**，就地对 snapshot 做同款完整性判定（复用与 `buglist.py` 分级**同一判据**：可能漏读 ⇒ 阻断），非空即 fail-closed 退出，零写盘。

🔴 **判据 MUST 与路径 ① 同源**：两条路径若各写一套「什么算读残缺」，必然漂移——这正是本仓 `adr/0011`（共用解析核心的返回语义按消费方各自定）要人**逐调用方验证**的原因。实现期 MUST 把判据抽成单一函数供两路调用，**MUST NOT** 各写各的。

**残余（显式登记）**：`issues.py` 自持的第三份 parser 若本身滞后（不认 frontmatter），路径 ② 与 ③ 无任何防线——**本 change 不覆盖该面**，见 Risks。

### D6 — sweep 退出码分两类，补全而非推翻既有契约

既有承诺是「非原子、fail-closed、**重跑收敛**」。但阻断类失败**重跑不收敛**——盘面失配不会因再跑一次而消失，会**永久卡死 done 的收尾步**，在 `/sdflow-ship` 全自动链上表现为无限重试。

| 失败类 | 退出码 | 语义 | 调用方 |
|---|---|---|---|
| 半途失败（triage / batch add 挂） | `1` | 重跑可收敛 | 自动重跑 |
| 阻断集非空 | `2` | **重跑无用** | **停下上抛，不重试** |

exit 2 的 stderr **MUST** 明说「重跑无用」+ 列全阻断明细 + 给两条出路（修盘面 / 显式逃生口）。

**这是补全不是推翻**：既有契约描述的是**写操作幂等性**，本就没覆盖「输入数据有问题」这一类。`/sdflow-done` SKILL.md 的失败语义段须同步补一句 `[grill-amendment]`。

🔴 **exit 2 现状会被 sweep 自己压平 〔gstack-amendment · 广审 medium〕**：`cmd_sweep` 调子进程 `reindex` 后只判 `if ri.returncode != 0: _die(...)`，而 `_die` 恒 exit 1 ⇒ **子进程的 2 到不了调用方**。∴ 实现 MUST 显式**透传 2**（同理 `batch add` 子调用），MUST NOT 依赖现有 `_die` 路径。

**全自动链遇 exit 2 硬停，MUST NOT 跳过 sweep 继续推进**——跳过等于丢失 defer 分诊，那正是本次事故本身。

🔴 **落点修正 〔gstack-amendment · 广审 medium〕**：`sdflow-ship/SKILL.md` 全文 grep `sweep` = **0**（实测）——ship 不直接调 sweep，它经 `/sdflow-done` 链序。∴ exit 2 语义**只落 `sdflow-done/SKILL.md`**；改 ship 是无效编辑，已从 tasks 删除。

### D7 — 截断过的 voice 必须声明覆盖面残缺 〔grill fold〕

`truncated=` 已经在落锚，但**全仓零消费者**（实测：只在两层 SKILL.md 的锚行模板里出现，无任何读取方）。于是：voice 拿到一份**中间被挖掉**的 diff，照常评审、照常输出 findings，报告照常收录、照常计入镜位——**没有任何地方说过「这面镜子只看了两头」**。

这与退出码撒谎同族，只是换到**覆盖面**维度；且与上一个 change 修掉的 `declared` 站点集漏核是同一种病。

**关键**：**R1 会让这条路径更常成功**。今天超长中文 context 是 rc=1 吵闹地失败；修完之后它会**安静地成功，基于残缺证据**。∴ R1 与 R7 必须同批做——只做 R1 是把病灶做得更隐蔽。

**🔴 初版做法的机械性是假的 〔gstack-amendment · 广审 high〕**：初版写「锚行是确定性信号 ⇒ 属基准 ① 该机械化的面」。**错。** 两层 SKILL.md 明写「`truncated` 取 helper stderr 的 `OV_TRUNCATED`」——helper 只把它**写 stderr**，落进锚行那一步是**主 session 模型抄写**的。∴ `anchor_lint` 核「锚行说 true ⇒ 报告有声明」只是在核**模型自己写的两句话彼此自洽**；模型把 `truncated="false"` 抄错（或省事写 false），门**恒绿**。

这正是本仓已登记的坑：**有信号 ≠ 有可机械捕获路径**（`adr/0018` 同族；捕获环节由被监管方把持就不是机械门）。我在设计里把它当机械门写，是同一个错误的复发。

**改后做法**：把捕获权从模型手里拿走——**helper 侧把 truncated 落成 per-site sidecar**（复用已有的 `.rc` sidecar 形态：runner 只读、写不了），`anchor_lint` 核 **sidecar ↔ 锚行一致** + 「sidecar 为 true ⇒ 报告有覆盖声明」。这才是机械门。

**代价**：要动 `outside-voice.sh`（本就在改）+ 两层 SKILL 的 sidecar 读取约定。**收益**：门从"核模型自洽"升级为"核事实"。

**若实现期证明 sidecar 落不下来**（如 async 分支下 helper 与 `.rc` 写入时序冲突）⇒ **MUST 把 R7 如实降级为语义层约定**（报告写声明、无机械核），**MUST NOT** 保留一个只核模型自洽的门却称其为机械门。

**明确不做**：分块多轮送、动态调 `OV_MAX_CONTEXT_BYTES`、按内容智能裁剪——那些是「让截断变聪明」，是另一个 change。**这一刀只解决「截断了要说出来」。**

## 失败模式表〔TG-08 · BASE-06〕

| # | 失败模式 | 检测方式 | 处置 | 退出码 |
|---|---|---|---|---|
| F1 | context 截断落在多字节字符内 | 回扫检查 continuation 字节 | 回退到字符边界 | 不影响（0） |
| F2 | `od` 不可用 | 命令预检 | **fail-loud**：报缺依赖（同既有 `timeout` 缺失路径） | 非零 |
| F3 | runner 超时 | `timeout` 返回 124 | 原样透传，落 `reason_code="timeout"` | 124 |
| F4 | 父进程 SIGTERM/INT/HUP | trap | 杀 runner + 清 workdir | 143（TERM 惯例） |
| F5 | 父进程 **SIGKILL** | **不可检测** | **残余：孤儿存活**，显式登记不掩盖 | — |
| F6 | 阻断集字段缺席（产出方滞后） | JSON 缺字段 | **全部 problems 按阻断**，零写盘 | 非零（sweep 为 `2`） |
| F7 | sibling 脚本文件不存在 | 路径预检（既有） | 沿用既有 `_die` | 非零 |
| F8 | 阻断集非空 | JSON 阻断集字段 | 非零退出、零写盘（除非显式逃生口 ⇒ 放行但 INDEX 留疤） | 非零（sweep 为 `2`） |
| F9 | scan 子进程本身失败 | `proc.returncode` | 沿用既有 `_die` | 非零（sweep 为 `1`） |
| F10 | 仅瑕疵类诊断（不进阻断集） | JSON `problems` 非空、阻断集空 | 回显 stderr，正常完成 | 0 |
| F11 | `truncated="true"` 但报告无覆盖声明 | `anchor_lint` | 判违规 | 非零 |

**F4 的退出码 143 已查明无需新增枚举**：async 段第 ⑦ 条已有 catch-all——「其余一切情形（未知码 / `.rc` 缺席或内容不匹配 …）→ **保守** fallback（`reason_code="exec-error"`）；**MUST NOT 读作 `ok`**」。且 helper 被 TERM 时 `printf '%s' "$?" > <site>.rc` 本就没机会执行 ⇒ `.rc` 缺席 ⇒ 本来就走 exec-error。**B10 的修复是锚语义中性的**：它改变的只是孤儿 runner 不再白烧至内层超时（design open question Q2 就此关闭）。

## 可观测性〔TG-08 · BASE-11〕

- **B9**：截断时 stderr 已有 `OV_TRUNCATED=true`（既有）。**新增**：回扫实际丢弃的字节数，便于事后判断截断是否吃掉了有效内容。
- **B10**：清理路径 stderr 记一行「已终止 runner PID N」，让「父被回收」在日志里可见，而非静默消失。
- **B11/B12**：阻断时 stderr **MUST** 给出**阻断明细全列 + 涉及文件路径 + 两条出路**（修盘面 / 显式逃生口），sweep 另加「重跑无用」字样。只说「有 problems」不 actionable；给出文件路径才能让人一眼看出是哪个池、哪一份盘面。
- **逃生口留疤**：`INDEX.md` 头部 banner 增记的那行**进版本库**——这是本设计里唯一进入产物的可观测性，也是唯一一条在人不看终端时仍然有效的。

## 安全与数据保护〔TG-17 · BASE-28〕

- **截断改动位于 `secret_scan` 之后**：`secret_scan` 扫的是**整个 context 文件**（截断前），故修改截断**不缩小**密钥扫描覆盖面。**MUST 在实现期复核该次序**——若次序反了，截断改动会改变送出内容而未被扫描，属出境安全回归。
- **不改出境侧扫描**：runner 回传的 findings 仍走既有 `secret_scan`（`host-adaptive-execution`「出境安全三件套对两条 runner 路径一视同仁」）。
- **B11 的 fail-closed 是数据保护动作**：阻止用残缺集合覆盖权威 INDEX，属**防数据丢失**，与 `adr/0022`（可改不可删）同向。
- **新增 stderr 内容不含 context 正文**：只报字节计数与路径，**MUST NOT** 把 context 片段写进日志（该内容未经出境扫描）。

## Risks / Trade-offs

- **[A1 未闭：Linux 侧截断行为未实测]** → 缓解：CI 泳道跑切点扫描测试（`mechanical-gates.yml` 已是 ubuntu-latest）。**不接受「macOS 绿就算过」**——`windows-ci-bash-subprocess-traps` 就是这么被咬的。
- **[fail-closed 卡住自动链路]** → 缓解：exit 2 与 exit 1 分开，调用方对 2 停下上抛而非无限重试（D6）；错误信息必须 actionable。**须在实现期通读全部调用点确认**（假设 A3）。
- **[存量含 legacy 不一致的仓开始变红]** → 接受：本就该修；`--allow-problems` 提供知情放行，代价是 INDEX 带疤。
- **[逃生口被滥用成常态]** → 缓解三条约束（留疤 / 禁环境化 / 禁自动传）。**残余**：人仍可每次手敲；但每次都会在 git 里留下一行，**可事后审计**——这是可见成本而非机械门（`adr/0021` 同款定位），**MUST NOT 宣称已杜绝**。
- **[改 `assets/hack/` 后忘记跑 `setup.sh`]** → **`outside-voice.sh` 不在任何本 change 机制的保护范围内**（它是 shell、不走 recorder 取数路径，也没有诊断信号通道）⇒ **残余风险，显式登记**。本 change **不**声称覆盖它。
- **[旧脚本已出厂，无法回溯加保护]** → **不可缓解，显式登记**：已发布的滞后脚本不知道 frontmatter 存在，任何前向机制都救不了它自己。唯一防线是它**自己喊出来的 `problems`** 被新消费方按阻断处置——即「缺席即阻断」那一条。**MUST NOT 把本 change 描述为「版本偏斜已被机械杜绝」。**
- **[🔴 本 change 救不了本次事故本身 〔gstack-amendment · 广审 medium〕]** → 本次事故是 **consumer + producer 双旧**（`/sdflow-done` 调运行 checkout 的 `~/.claude/skills/sdflow-issues/…`，那份 `issues.py` 与 `buglist.py` 同旧）⇒ **新逻辑根本不在场**，「缺席即阻断」需要新 `issues.py` 才生效。
  **唯一能覆盖双旧场景的动作 = 让「跑的是哪一份」变可见**：`sweep` / `reindex` 起手打印**所调脚本的绝对路径 + 版本戳**（近零成本，且旧版本也能被人一眼认出）。已纳入 tasks。
  **诚实边界**：这是**可见成本**（`adr/0021`）、**不是机械门**——旧脚本不会打印版本戳，能看见的前提是至少有一端已升级。**MUST NOT 声称它拦得住双旧。**
- **[`issues.py` 自持第三份 parser 〔gstack-amendment · 广审 high〕]** → 路径 ②/③ 用的是 `issues.py:298-511` 自己的 recorder parser。该 parser 若滞后（不认 frontmatter），这两条路径**无任何防线**。**本 change 不覆盖该面，显式登记为残余**——覆盖它需要把三份 parser 的版本能力统一暴露，属另一个 change。
- **[SIGKILL 孤儿]** → 无缓解，见 D2 诚实边界。

## Migration Plan

1. 改 `sdflow-init/assets/hack/outside-voice.sh`（bundle **唯一权威源**）→ 开发 checkout 跑 `bash setup.sh` 才测得到（拷贝非 symlink）。
2. 改三个 recorder 脚本 → symlink 场景即时生效，但**运行 checkout 仍需 pull + setup** 才拿到新版。
3. **回滚**：三处改动彼此独立，可单独 revert；`outside-voice.sh` 回滚后须重跑 `setup.sh`。
4. **下游**：经 `sdflow-init update` 推 bundle；对下游是纯修复、无接口变化。

## 切片建议（仓 `impl-pipeline: tickets`，建议非契约）

| # | 切片 | Blocked-by | 覆盖 |
|---|---|---|---|
| 1 | 截断字符边界安全 + 切点扫描测试 + 变异验证 | none | R1 |
| 2 | runner 子进程生命周期 + SIGTERM 验尸测试 | none | R4 |
| 3 | 诊断产生处分级 + additive 阻断集字段（两个池脚本） | none | R2 |
| 4 | `_scan_pool` 收集下发 + 缺席即阻断 + 逐调用方断言 + `reindex` 零写盘断言 | 3 | R2、R5 |
| 5 | 严格默认 + exit 1/2 分类 + 逃生口三约束 + INDEX banner | 4 | R3、R6 |
| 6 | `truncated="true"` ⇒ 覆盖声明 + `anchor_lint` 存在性核 | none | R7 |
| 7 | `/sdflow-done` §2.1 与 `/sdflow-ship` 链序认识 exit 2 | 5 | R6 |
| 8 | Linux CI 泳道 + `setup.sh` + 全套件 + parity 门 | 1,2 | A1 |

1/2/6 与 3/4/5/7 分属两个文件族，无耦合可并行；族内 3→4→5→7 严格串行。

## Open Questions〔TG-21〕

*（grill 已全部关闭，保留结论供追溯）*

| # | 问题 | 结论 |
|---|---|---|
| Q1 | `--allow-problems` 逃生口给不给？ | **给，但加三条约束**（产物留疤 / 禁环境化 / 禁自动传）。不给会楔死有合法历史失配的老仓，并逼人手改 `DO NOT EDIT` 生成文件 |
| Q2 | 143 是否需进 `reason_code` 枚举？ | **不需要**。async 段已有未知码 catch-all → `exec-error`；且 helper 被 TERM 时 `.rc` 本就缺席，走同一条路。B10 锚语义中性 |
| Q3 | sibling 版本握手要不要做？ | **不做**，实测证伪（sibling 恒同 checkout ⇒ 门恒绿）。功能由「阻断集字段缺席 ⇒ 全阻断」自然覆盖 |
| Q4 | 分级判据落 `adr/0018` 还是新开 ADR？ | **落 0018 新增铁律 (d)**——同一命题在「信号强度」维度的细化，新开会让主题裂成两处 |

## Compliance

逐条 ADR / 边界核对见 `proposal.md`「Compliance」节（D-6，含 `adr/0005` / `0008` / `0010` / `0011` / `0018` / `0022` / `0025` 与跨模块共享数据模型边界的显式未越界确认），此处不复制。

**本文额外承担的合规点**：
- **D-1**：上方「代码事实」表全部经 grep 核验，无记忆直写。
- **D-4**（外部依赖声明超时与回滚）：runner 超时沿用既有 `--timeout`（缺省 300s）+ `timeout -k 10`；握手为只读预检、无写操作故无回滚路径；写盘类子命令的回滚 = fail-closed 前置 ⇒ **不产生需回滚的中间态**。
- **基准 ⑤**：D1 明确限定 UTF-8 有界面，禁止演化为编码嗅探。
