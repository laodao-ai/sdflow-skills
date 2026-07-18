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
     cmd_batch_rename ──► read_rename_snapshot ──► classify_batch_rename(纯读) ──► retag_rename_snapshot
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

🔴 **但初版的「缺席 ⇒ 全部 problems 视为阻断」有个洞 〔spec-review-amendment · hr-tg high〕**：若滞后 producer 同时产出 **空 items + 空 problems + 无该字段**（它完全不认识新盘面格式时的典型形态），「全部 problems 视为阻断」作用在空集上 ⇒ 阻断集仍为空 ⇒ **放行**。
**修正**：**字段缺席本身即生成一个独立的 blocker sentinel**，与 `problems` 是否为空**无关**。测试 MUST 含 `items=[] ∧ problems=[] ∧ 字段缺席` 的零写盘用例。

**字段形状（初版未定义，12 处提及无一处给形状 〔领域镜 medium〕）**——两个池脚本各自实现前 MUST 定死，否则必然各起各的名、造出新漂移面：

```
scan --json 输出新增：
  "blocking": [ {"code": "E-DROP-MARKER-ONLY", "id": "B12", "detail": "…"}, … ]
```
- `code` 取自 D5′ 的 diagnostic code taxonomy（稳定机器码，**不是**散文）；
- `problems` 字段**类型与内容一字不动**（既有消费者零影响）；
- **字段整体缺席** ≠ `"blocking": []`——前者是「产出方不认识该字段」⇒ sentinel 阻断，后者是「明确无阻断项」⇒ 放行。**二者 MUST 可区分**。

**切分判据（承 `adr/0018` 铁律 (d)）**：**该信号是否污染本次输出的完整性**，而非严重程度感受。

🔴 **初版分类表方向写反，且漏掉真正会丢条目的那条 〔spec-review-amendment · design-voice critical〕**。返修依据（实测 `buglist.py` `_build_effective_snapshot` 与诊断产生处）：

- `_build_effective_snapshot` **无条件纳入 `frontmatter_items`** ⇒ frontmatter 是真相源；
- 诊断按 `result["format"]` **分两套**：`legacy` 出 `marker-only legacy` / `块有 X 但缺总览表行`；**canonical / overlay（= 目标态）出的是另一对**；
- ⇒ 我拿**本次事故现象（legacy 路径的诊断）**去定义**目标态**的阻断判据，正是通则③ 的反面：**目标态下 `块有 X 但缺总览表行` 根本不会产生**。

**修正后的分类表**（按「该条目会不会从 `effective_items` 里消失」定，不按名字像不像严重）：

| 诊断 | 产生条件 | 条目会丢吗 | 归类 |
|---|---|---|---|
| `marker block 有 X 但缺 frontmatter item` | canonical/overlay | **会**（不在 frontmatter ⇒ 不被纳入） | 🔴 **阻断** |
| `marker-only legacy：X` | legacy | **会**（无表行、无 frontmatter） | 🔴 **阻断** |
| `块有 X 但缺总览表行` | **仅** legacy | 会 | 🔴 **阻断**（目标态不产生，留作迁移期兜底） |
| `X 行 arity 异常：N 列` | 任意 | **会/错位** —— `parse_table_rows` 只要 `len(cells) >= 5` 就收，随后按**固定下标**读 `status/change/batch`；缺列/多 `|` 会错位，令 `sweep --change` **漏项** | 🔴 **阻断**〔hr-tg high，初版误归告警〕 |
| `frontmatter 有 X 但缺 marker block` | canonical/overlay | **不会**（frontmatter 已纳入，只是缺人读的 prose 块） | 告警 |
| `marker block 重复：X` / `marker 嵌套` / `orphan end marker` | 任意 | 不会（结构脏但条目在） | 告警 |

🔴 **实现期 MUST 逐条重审，不得照抄本表**：判据是「顺着 `effective_items` 的实际纳入路径走一遍，这条诊断对应的条目会不会掉出去」。**MUST NOT** 凭诊断措辞的严重感归类——初版就是这么错的。

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

`reindex` 现状是**先算后覆盖**；判定若落在计算之后，仍可能在报错前已经写盘。

🔴 **初版措辞逻辑上不可实现，已更正 〔spec-review-amendment · design-voice high〕**：初版写「MUST 前置到任何 discovery / stat / open 之前」——**阻断集只能在打开并解析盘面之后才产生**，不可能早于 open。我把 `adr/0025` 对 **lock 获取**的纪律错误复用到了**数据校验**上；两者不是一回事。

**正确口径**：**完成同一把锁内的快照读取、取得阻断集之后，在任何 `render` / `retag` / `atomic_write` 之前判定**。测试锚点是**阻断时零写盘**，不是「判定发生得多早」。

### D8 — sweep 的两个新洞（本 change 自己造的）〔spec-review-amendment〕

**D8a — 按池写盘，第二池的阻断拦不住第一池 〔hr-tg high〕**：`cmd_sweep` 现状是 `for pool: scan → 逐项 triage(写盘) → 下一池`。第一池 triage 已落盘后才扫第二池 ⇒ 第二池的阻断**来不及**阻止第一池的写入。
**改法**：两阶段——**先扫完两池、汇总阻断集、确认可放行**，再统一 triage。测试 MUST 含「第二池阻断 ⇒ 两池 dated 文件、`batches.md`、`INDEX.md` **全部字节未变**」。

**D8b — 阻断后重跑会静默漏掉 `reindex` 〔对抗镜 A critical，本 change 严格默认自己造的〕**：

```
第1轮  triage 全部打上 batch=X（已写盘）→ batch add 成功 → reindex 因【与本次无关】的既存问题阻断退出
第2轮  scan --open-ungrouped 的 `not b.get("batch")` 把已 tag 项全滤掉 → tagged==[]
       → 命中既有 FIX-2 早退 `if not tagged: return` → 不跑 batch add、不跑 reindex → exit 0
```
⇒ 第 1 轮写进 `batches.md` 的批次条目**永远等不到同步进 `INDEX.md`**，而 `/sdflow-done` 见 exit 0 即认为分诊完成。**这与本 change 要根治的病灶同型，只是换了触发路径，且只在新机制生效后才出现。**
**改法**：`reindex` 的触发判据 **MUST NOT** 是「本轮 `tagged` 是否非空」。改为：**只要该 change 在 `batches.md` 里存在条目，`sweep` 就无条件跑终步 `reindex`**（保守、幂等、零额外状态）。

### D9 — 写侧存在同款洞，面治必须扫到 〔spec-review-amendment · 对抗镜 C high〕

**面治漏了写侧。** `cmd_add` / `cmd_set_status` / `cmd_triage` 三个高频写操作在写前调 `_reject_document_mutation`，其判据是**对同一份自由散文 `problems` 做子串匹配**：

```python
structural = [p for p in document["problems"] if "marker" in p or "frontmatter" in p]
```

实测反例：`'块有 B10 但缺总览表行'` → `False` ⇒ **放行写入**——往一个可能正在漏读条目的文件里继续追加新 item。

🔴 **双重讽刺，MUST 记牢**：① 我一直在治「读残缺时别写盘」，而**写侧本来就有一套更老、判据完全不同的放行逻辑**，四件套初版全文零提及；② 这正是我在 tasks 3.7 明令禁止的「消费方用子串还原分级」的**存量实例**——**我禁了未来，没看见现在**。

**改法**：`_reject_document_mutation`（及同族 `_validated_rendered_mutation`）**MUST** 改用与 D3 同一套结构化分级，**MUST NOT** 保留子串匹配。这条**补 task，不只登记残余**——它是「承诺 vs 实得」差距的主要来源（读路径已堵、写路径仍开）。

### D5′ — 路径 ② (`batch rename`) 须另立机制 〔gstack-amendment · 广审 critical〕

**D5 在 rename 路径上直接不成立**，实测调用序：

```
read_rename_snapshot → retag → atomic_write(registry) → atomic_write_bytes(dated) → _reindex_core
                                └── 写盘已发生 ──┘          └── 阻断判定在这之后才跑（太晚）
```

且该路径是 **in-process 解析**（`issues.py` 自持的第三份 recorder parser，`:298-511`），**没有 JSON 边界** ⇒ 「additive 字段 + 缺席即阻断」这个枢纽机制**在此完全失效**——不存在"可缺席的字段"。

**做法**：`read_rename_snapshot` 完成解析后、**在 `retag` 与任何 `atomic_write` 之前**，就地对 snapshot 做同款完整性判定（复用与 `buglist.py` 分级**同一判据**：可能漏读 ⇒ 阻断），非空即 fail-closed 退出，零写盘。

🔴 **「抽成单一函数」与本仓架构冲突，已改判 〔spec-review-amendment · design-voice + 对抗镜 B 双命中〕**：初版要求两路调同一个函数。但 `_scan_pool` 的 docstring 明写走 subprocess 就是为了**避免跨 skill import**、让三个 skill 各自独立演进（`adr/0025`：三份 helper 继续物理复制）。照字面落地只有两条路：**引入被禁的跨 skill runtime 耦合**，或**各写两份却伪称同源**——后者更坏（测不出漂移，`assert fn_a is fn_b` 这类身份核验根本写不出来）。

**改判为**：同源的不是**函数**，是**契约**——
1. 建立**机器可读的 diagnostic code taxonomy**（稳定码，如 `E-DROP-*` / `W-DIRTY-*`），三个 producer/parser 各自实现但**发同一套码**；
2. 用**同一份 conformance fixtures** 跑三方，任一方对同一畸形输入吐出不同码即红——**这才是能机械测出漂移的东西**，且不违反自包含架构；
3. taxonomy 与 fixtures 是**单一源**，放 bundle 权威源随 `sdflow-init update` 分发。

**MUST NOT** 保留 spec 里那条 WHEN 写「检视实现」的 Scenario——它不是运行时可触发条件，只能靠人读代码，属**伪机械门**（同 R7 的病）。

**残余（显式登记）**：`issues.py` 自持的第三份 parser 若本身滞后（不认 frontmatter），路径 ② 与 ③ 无任何防线——**本 change 不覆盖该面**，见 Risks。

### D6 — sweep 退出码分两类，补全而非推翻既有契约

既有承诺是「非原子、fail-closed、**重跑收敛**」。但阻断类失败**重跑不收敛**——盘面失配不会因再跑一次而消失，会**永久卡死 done 的收尾步**，在 `/sdflow-ship` 全自动链上表现为无限重试。

🔴 **`2` 这个码已被占用，初版分配不安全 〔spec-review-amendment · 对抗镜 B critical〕**：`issues.py` `main()` 有 `except ValueError → SystemExit(2)`，而 `RecorderLockError(ValueError)` **就是并发锁冲突**（`.recorder.lock` 已存在即抛）。锁冲突是**典型瞬时、重跑即好**的场景，若沿用初版语义，`/sdflow-done` 会把「等一秒就好」硬停成「需人工介入」——**新契约反而制造一类新的错误停机**。

**返修后的码位分配**（先证明码位空闲，再赋语义）：

| 失败类 | 退出码 | 语义 | 调用方 |
|---|---|---|---|
| 半途失败（triage / batch add 挂） | `1` | 重跑可收敛 | 自动重跑 |
| **并发锁冲突**（既有 `RecorderLockError`） | `2`（**既有占用，不动**） | **瞬时，重跑可收敛** | 自动重跑 |
| 阻断集非空 | **`4`**（新取空闲码） | **重跑无用** | **停下上抛，不重试** |

**实现期 MUST 先跑一遍码位盘点**：把 `issues.py` 全部 `SystemExit` / `_die` / 未捕获异常路径的实际退出码列出来，确认所选码**当前无人占用**，再落地。**MUST NOT** 凭「2 看起来没被用」直接赋义——这次就是这么差点错的。

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

🔴 **sidecar 还缺身份与生命周期契约，光说「落 sidecar」不够 〔spec-review-amendment · hr-tg + design-voice 双命中 high〕**：run 目录是**per-run 不可变、永久保留、可并发多轮**的（本轮就因重试产生了两个 run-id）。而报告锚行只有 `site=`、**没有 run-id**，`anchor_lint` 的入参也只有 report/layer/catalog/root ⇒ **它根本不知道该读哪个 run 的 sidecar**。用「最新目录」在并发或重跑时会**串轮**，门照样假绿。

**补齐契约（缺一不可）**：
1. **provenance**：报告落一条受校验的 run-id 锚（或给 `anchor_lint --voice-run-dir`），把「本报告对应哪一次 voice」变成机器可读；
2. **路径固定**：sidecar 恒为 `<run-dir>/<site>.truncated`，与 `.rc` 同目录同命名法；
3. **fail-closed 三态**：缺失 / 重复 / 站点不匹配**一律判红**，MUST NOT 猜；
4. **覆盖两条执行路径**：`exec` 与 **fallback 的 `render-prompt`**（同族降级路径今天根本不产生 sidecar，初版漏了）；
5. **reuse 分支**：`design-voice` 走 reuse-guard 复用时**本轮没有 helper sidecar** ⇒ MUST 为该分支定义独立的来源证明，MUST NOT 让它落进「sidecar 缺失 ⇒ 判红」而误杀。

**若实现期证明这套契约落不下来** ⇒ **MUST 把 R7 如实降级为语义层约定**（报告写声明、无机械核），**MUST NOT** 保留一个只核模型自洽的门却称其为机械门。

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
