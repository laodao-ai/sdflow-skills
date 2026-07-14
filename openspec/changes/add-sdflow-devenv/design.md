# design — add-sdflow-devenv

> 设计源：`docs/sad/07-devenv-skill-design.md`（**已按三轮 spec-review 重定基**）· 接地证据：`docs/sad/06-process-axis-grounding-receipt.md`
> 命中 TG：05 · 08 · 09 · 10 · 11 · 12 · 13 · 14 · 15 · 17 · 18 · 19 · 21 · 22 · 23 · 25 · 26（HR-TG：08 / 09 / 17 / 26）
>
> **本文档已按 round-3 设计门整体重写。** 前两版的正文（negative control ⟺ 定义 · 嵌套 YAML · 行号锚 · `owned_by` 派生 · cleanup ledger 自动记账 · `confirm-lane` 身份保证）**已作废**。
> **考古层不在本文件维护——`git log` 即完整历史。** 真相源 = `specs/`；本文档只讲**为什么这么设计**。

---

## ADR-0：机械层**防漏，不防伪**〔凌驾于以下所有 ADR〕

**决策**：skill 的目标是「**有了这些过程，也有了人认可的结果**」（操作者原话）——**不是「证明模型没有撒谎」**。

| | 机械层 **MUST** 保证 | 机械层 **MUST NOT** 试图保证 |
|---|---|---|
| | **防漏（完整性）** | **防伪（真实性）** |
| 内容 | 三层五槽有没有留白 · 泳道有没有验证方法 · `不适用` 有没有记后果 · `human` 有没有写「为什么程序跑不了」和「人怎么做」· 未完成的有没有被逐条列出来 | 这个 `verified` 是不是真跑过 · 人是不是真确认了 · smoke 是不是真穿过依赖 · `covers` 是不是真命中 |
| 性质 | **结构检查**——全部有确定性信号 | **需要信号锚**——脆弱或不存在，**且本就不必防** |

**理由（这条 ADR 是被三轮评审逼出来的，代价：14 镜、100+ findings）**：

前两版把 skill 设计成了一个**审计机器**——negative control、测试计数门槛、执行证据、`method_digest`、`owned_by` 派生、cleanup ledger 记账、`confirm-lane` 的调用者身份保证……**这一整套东西都在回答同一个问题：「怎么证明模型没撒谎」。**

**而使用这个 skill 的就是那个人自己。他没有动机骗自己。** 模型真乱盖章，下次跑测试跑不起来，用户当场就发现——**这不是需要密码学级防护的场景。**

**证据**：三轮评审里，几乎每一条致命 finding 都长这样「你这个机械保证有洞」，而**没有一条**是「这个 skill 不好用」或「它建不起环境」。**在防一个不存在的攻击者，所以每一条防线都站不住——它们本来就没有存在的必要。**

**三条推论（MUST 遵守）**：

1. **写下任何一条「MUST 机械保证 X」之前，先问「这个保证的信号从哪来」。** 答不上来 ⇒ 删掉它，或诚实划归语义层。**MUST NOT 硬凑一个长得像机械的东西。**
2. **假机械比诚实的语义层更危险**——它让人以为有防线。
3. **能力边界如实写。**

**后果**：删掉了 negative control / 测试计数门槛 / `isolate` / `predicate` / `kind → dispatch` / runner 白名单 / **`owned_by`** / **cleanup ledger 自动记账** / **`confirm-lane` 身份保证** / **`method_digest` 的「可达」覆盖**——**一整片复杂度**。被否方案全集见 `07` 附录 A13–A20。

---

## ⭐ 字段与动作的信号来源表（本设计的核心自查机制）

> **round-3 教训**：前一版的这张表**只审「数据字段」，漏掉了「动作的发起者」**——因为后者不长得像一个 schema 字段。于是 `confirm-lane` 的调用者身份**既没被机械化，也没被诚实地划进语义层清单**，成了全篇唯一的真空地带。**本表因此扩展为「字段 + 动作」两段。**

### 段一：数据字段

| 字段 | 信号来源 | 机械 / 语义 |
|---|---|---|
| `evidence.exit` · `output_digest` | **脚本 fork 执行的实际结果** | **机械**（`executor: script` 时——脚本自己产的） |
| `evidence.confirmed_what` | **人门产物** | **语义**（`executor: human` 时——**人说的**，标 `attested_by: human`） |
| `evidence.file_digests` | **文件的原始字节 sha256**（零规范化） | **机械**（`devenv_digest.py` **零 make 知识**〔A21〕） |
| **target 存在且能跑** | **`verify-lane` 真跑 `make <selector>`，看 `exit`** | **机械**——但**判官是 make 自己**，**MUST NOT 静态解析**〔A21〕 |
| `evidence.at_commit` | **`git rev-parse HEAD`** | **机械** |
| `status` | 由 `evidence` 是否齐全推出 | **机械** |
| `verification.method` | 模型研究 + 人拍板 | **语义**（存在性可机械查；**有效性不能**） |
| **`verification.strength`** | 模型自陈 | **语义**（存在性可机械查；**内容真伪不能**——冷审「验证方法镜」） |
| **`executor`** | 模型判断 | **语义** ← **前一版漏了这一行** |
| **`why_not_scriptable`** | 模型判断 | **语义**（冷审专查「这个理由成不成立」） |
| `kind` · `layer` | 模型判断 | **语义**（③-pre 人门分类清单 + 冷审「分类镜」）——**MUST NOT 佯装机械** |
| **`fixtures[]`** · **`env[]`** | 模型声明 | **语义** ← **前一版漏了这两行** |
| `covers` | 模型判断 | **语义**（冷审「覆盖镜」） |
| ~~`owned_by`~~ | **删除**——「运行时派生」的锚**不存在** | — |

### 段二：**动作**（前一版整段缺失）

| 动作 | 「谁发起的」这件事有信号吗 | 处置 |
|---|---|---|
| `verify-lane` 执行验证命令 | **有**——脚本自己 fork，exit code 是它自己拿到的 | **机械** |
| **`confirm-lane` 写入人工验证证据** | **没有** ⇒ **在 agent session 里，模型是唯一的命令执行者**；人只在对话里回答「同意/否决」，从无「人亲自开终端敲命令」的通道。「模型 MUST NOT 代替操作者调用」这句话**按字面永远为假** | **语义 + 如实标注**：产出的绿标 `attested_by: human`（**人说的，不是脚本验的**），渲染进文档时**与脚本验证的绿可区分**。**MUST NOT 声称脚本保证了执行者身份**。**且本就不必防**（ADR-0） |
| ③-pre 人门「操作者已同意」 | **没有**（同上） | **同上**——如实呈现，不设防伪 |

> **这张表是 ADR-0 的执行工具。新增任何字段或动作，MUST 先在此表登记它的信号来源。**

---

## Context

生态里「技术架构定了之后把 dev/test 环境真正建起来」无 skill 覆盖：`sdflow-architecture` 交棒止于「过程轴文档指路（指出不代写）」，下游为空；`sdflow-init` 铺的是 **workflow 的运行环境**，按定义不管项目内容。

mqtt-console 接地实测（`06`，**证据强度分层见 proposal**）：

1. **SAD 投影率 12%（严）/ 41%（宽）**——「从 SAD 生成文档」这条腿不成立。**注**：前一版据此推出「那 88% 全是待决策项」，已被 `06 §4.2` 的**三分法**（SAD 投影 / **构建配置投影** / 纯人写）**证伪**。
2. **真正的机械投影源是构建配置**（Makefile / package.json）。
3. **纯文档型产物有虚构命令的风险**——但 `06` 的实测结果是「**零虚构、行号全中**」（**预测风险，非观测事实**）。

## Goals / Non-Goals

**Goals：**

- **⭐ 不管什么项目，操作者都能拿到一份完整的测试与验证策略框架**——单元 / 集成 / e2e 三层各自交代清楚。做不了的写**不适用 + 后果**，要人做的写**人怎么做**。**一层都不许留白。**
- 把 dev/test 环境**真正建起来**，并**尽可能跑一遍确认**。
- **渐进 DoD** + **框架可迭代**：不强制全绿，不是一次定死。
- **诚实是硬要求**：跑不绿合法，**跑不绿却装作跑得绿**不合法。

**Non-Goals：**

- **⭐ 替人判断验证方法有没有效**（ADR-0）
- **⭐ 堵住 `assert True`**——任何外部插桩都堵不住，要堵只有变异测试（太重）⇒ **机械层堵不死，归冷审**
- **⭐ 证明「人真的做了人工验证」**——agent session 的架构边界，**且本就不必防**
- **⭐ 管理 skill 没有启动过的资源**——recipe 内部起的容器**不属于子进程组**
- 业务测试用例 · 生产 runbook · 替用户装系统依赖 · debug 到通 · monorepo · 时间轴排期 · 从 SAD 自动生成文档

## 组件清单〔TG-13/14〕

| 组件 | 职责 |
|---|---|
| `SKILL.md` | 五步编排 · 三模式分流 · **两道人门**议程 |
| `scripts/devenv_scaffold.py` | `init` · `set-lane`（**只管 planned/scaffolded**）· **`verify-lane`**（script：脚本亲自 fork）· **`confirm-lane`**（human：人门写，标 `attested_by: human`）· `render` · `inject` · `log` · `doctor-gen` |
| `scripts/devenv_lint.py` | **只查诚实（防漏），不查质量（防伪）** |
| `scripts/devenv_schema.py` | **两份** JSON schema（`.devenv-lanes.json` + **`.devenv-strategy.json`**）+ **containment helper** |
| `references/lane-patterns.md` | 依赖形态四问 + 参考实例（**非规格**） |
| **`references/verification-patterns.md`** | 验证方法参考实例（**非规格**）+ **已知负面知识** |
| **`references/exit-codes.md`** | **退出码表**（一码一义；实现期照抄，不留现场发明空间） |
| `references/env-allowlist.md` | 按栈的最小环境 allowlist 推荐起步集（**实例，非规格**） |
| `references/review-lenses.md` | 冷审镜单（含**验证方法镜**、**分类镜**、**vacuous 镜**） |
| `tests/` | pytest |

## 数据模型〔TG-05〕

**两份机械真相源，均落 `openspec/architecture/`，均标准库 `json`（零依赖）**：

- **`.devenv-lanes.json`** —— 泳道
- **`.devenv-strategy.json`** —— **测试三层框架**（**round-3 新增**）

> **为什么三层框架必须落 JSON**：若让 lint 去解析自由格式 Markdown（定位「单元测试」这一节、切出五个子槽、判断非空），就是**又一个手搓解析器**——本仓前科：`parse_frontmatter` 只支持扁平标量 · `inject` 至今非 fence-aware · `ship_gate` 子串检测曾假阳。**`lanes[]` 已经落 JSON 了，同一道理必须贯彻**〔`07` 附录 A20〕。

两份 Markdown（`environments.md` / `testing-strategy.md`）**由脚本从 JSON 渲染**，`DO NOT EDIT` banner。

**渲染 MUST 携带诚实信息**：`verified` → **`verified-at <sha>`**（不是无条件的绿）· `human-attested` **与脚本验证的绿可区分** · **每条泳道的 `strength`（强度与盲区）MUST 渲染进文档**。

> **理由**：三个月后另一个人打开 `environments.md`，若只看到「泳道 X：verified ✓」，当初那句「这个方法只证明命令耦合了依赖，不证明断言有效」**已经蒸发**。对首次拍板的操作者，`verified` 是「有盲区披露的、经人确认的绿」；对**任何后来者**，它退化成「绿灯」两个字。

## 状态机图〔TG-09〕

```
                     ②泳道 + 三层框架 + 验证方法拍板
                                 │
                                 ▼
                         ┌──────────────┐
                         │   planned    │
                         └──────┬───────┘
                                │ ③落地：smoke/harness 已写
                                │        ∧ verification.method 非空
                                │        ∧ verification.strength 非空
                                ▼
                         ┌──────────────┐
          ┌─────────────▶│  scaffolded  │◀────────────┐
          │              └──────┬───────┘             │
          │  continue 推进       │                     │ 【回落】
          │  (装完依赖/修完      │  按 executor 分流    │ file_digests 失配
          │   smoke/换方法)      │                     │ (人改了 source.file/
          │                     │                     │  smoke/声明的 fixture)
          │        ┌────────────┴────────────┐        │
          │        │                         │        │
          │  executor=script           executor=human │
          │  (默认·首选)               (降级·MUST 写   │
          │        │                    why_not_       │
          │        │                    scriptable)    │
          │        ▼                         ▼         │
          │  ┌─────────────┐          ┌─────────────┐  │
          │  │ verify-lane │          │confirm-lane │  │
          │  │ 脚本亲自fork │          │ 人门写证据   │  │
          │  │ 真实 exit    │          │ attested_by:│  │
          │  │ code         │          │   human     │  │
          │  └──────┬──────┘          └──────┬──────┘  │
          │         │                        │         │
          │  跑红 / │                     确认│         │
          │  缺依赖 │                        │         │
          └─────────┘                        │         │
                    │                        │         │
                    └───────────┬────────────┘         │
                                ▼                      │
                       ┌────────────────┐              │
                       │  verified-at   │──────────────┘
                       │     <sha>      │
                       └────────────────┘
                    evidence 齐全 ∧ blocked_by 空

  ┌─ 铁律 ──────────────────────────────────────────────────────────────┐
  │ • set-lane --status verified       →  一律拒绝                      │
  │ • verification.method/strength 空  →  lint fail-closed              │
  │   （不存在"不知道怎么验"的泳道——人工测试也是方法）                  │
  │ • scaffolded ∧ blocked_by 空/敷衍  →  lint fail-closed              │
  │ • verified   ∧ blocked_by 非空     →  lint fail-closed              │
  │ • kind: hardware / 非 POSIX        →  verify-lane refuse → human    │
  └─────────────────────────────────────────────────────────────────────┘

  ⚠️ 两种"跑不了"MUST 分清（前一版混成一条通道 ⇒「缺个依赖」被标成
     「只能人工验证」= 撒谎）：
       方法本身没法程序跑  → executor: human （真硬件/UI 视觉/非 POSIX）
       能跑但条件不具备    → scaffolded + blocked_by （本机没装 mosquitto）
```

## 关键时序图〔TG-10〕（**diff 门在执行之前**）

```
操作者      主 session       devenv_scaffold    冷审子代理(fresh)    消费仓
  │              │                  │                  │              │
  │/sdflow-devenv│  init            │                  │              │
  ├─────────────▶├─────────────────▶│ preflight+分流   │              │
  │              │◀─────────────────┤ exit code        │              │
  │ ①事实复核（批量呈现，一次确认）  │                  │              │
  │◀────────────▶│                  │                  │              │
  │ ②三层框架(3×5槽) + 泳道 + 验证方法（模型提，人拍；批量呈现）        │
  │◀────────────▶│ set-lane(planned)│                  │              │
  │              ├─────────────────▶│─── 持锁+原子写 ─────────────────▶│
  │              │                  │                  │              │
  │              │ ③写落地物之前:    │                  │              │
  │              │   原子落盘 txn journal（记【原完整内容】，非 digest）│
  │              ├─────────────────▶│─────────────────────────────────▶│
  │              │ ③写落地物(追加)   │                  │              │
  │              ├──────────────────────────────────────────────────▶│
  │              │                  │                  │              │
  ╞══════════════╪══════ ③-pre 人门（执行任何验证之前）═══════════════╡
  │ ① 新写落地物 diff 全文（recipe body + smoke 源码）                 │
  │    （仅登记的既有 target 只展示登记映射，不要求人重读）             │
  │ ② 验证方法逐条确认（含 strength 的强度与盲区）  ← 表格化一次呈现    │
  │ ③ 声明清单过目: kind/layer/executor/fixtures/env ← 全部无独立信号   │
  │ ④ 将执行的命令（recipe 展开）                                      │
  │◀─────────────┤                  │                  │              │
  │  同意 / 否决  │                  │                  │              │
  ├─────────────▶│                  │                  │              │
  │              │ 否决 → 按 txn journal 逐项回退                      │
  │              │   （原先存在的→用原内容复原；新写的→删）             │
  │              │   MUST NOT git checkout--（对 untracked 无效）      │
  │              │   MUST NOT 无路径限定的 git clean（会误删用户文件）  │
  ╞══════════════╪════════════════════════════════════════════════════╡
  │              │ verify-lane      │ 脚本亲自 fork    │              │
  │              ├─────────────────▶│（最小环境 allowlist│            │
  │              │                  │ + 独立进程组 + 超时)│            │
  │              │                  ├──────────────────────────────▶│
  │              │◀─────────────────┤ 写 evidence(原子) │              │
  │              │                  │                  │              │
  │              │  ⚠️ 超时/中断 → 杀得到的进程树杀掉，                 │
  │              │     杀不到的（recipe 内部起的容器）【如实报告】       │
  │              │     "可能留下孤儿资源，请检查" —— MUST NOT 假装已清理 │
  │              │                  │                  │              │
  │              │ 派冷审(禁自查)    │                  │              │
  │              ├─────────────────────────────────────▶│ 读产物      │
  │              │◀─────────────────────────────────────┤ 镜单发现     │
  │              │                  │                  │              │
  ╞══════════════╪══════════ ④ 人门（执行后 + 冷审后）═══════════════╡
  │ ① 泳道设计复核  ② 未 verified 泳道逐条确认                        │
  │ ③ 三层框架的「不适用」槽逐条确认（后果写对了吗）                    │
  │ ④ executor=human 泳道的人工验证结果 → confirm-lane                │
  │ ⑤ 【归位模式】删源清单 —— 单独拎出，不可逆，不与常规议程同级        │
  │◀────────────▶│                  │                  │              │
  ╞══════════════╪════════════════════════════════════════════════════╡
  │              │ render + inject  │                  │              │
  │              ├─────────────────▶│─── 持锁+原子写 ─────────────────▶│
  │ ⑤收尾: 逐条列未 verified 泳道 + 整体判定 + 下一步怎么调用           │
  │◀─────────────┤                  │                  │              │
```

> **为什么 diff 门必须在执行之前**：否则**模型生成的 recipe body 与 smoke 源码，在任何人看过一眼之前就已经被执行了**。而「跑前列命令给操作者过目」给人看的是 `make integration` 这**一行调用**——**零信息量**。真正危险的内容恰恰不在那个门里。

## 并发与共享状态〔TG-26 · HR〕

| 机制 | 实现 |
|---|---|
| **写域锁（三 skill 共用）** | `openspec/.sdflow-write.lock`，`os.open(O_CREAT\|O_EXCL)`——跨平台，不用 `fcntl` |
| **原子写** | `mkstemp` → 写 → `chmod(mode)` → `os.replace()`。**`atomic_write` MUST 接受 mode 参数**（`sad_scaffold` 现硬编码 `0o644` ⇒ 生成的 doctor 脚本**落盘即不可执行**） |
| **锁作用域** | 包裹整个读-改-写；**MUST 短持有，MUST NOT 跨验证执行持有** |
| **CAS** | 覆盖**整个不可变的 verification plan**：`status`+**`executor`**+**`kind`**+`method`+`source`+`smoke`+`fixtures`+`env`+`deps`。算法钉死：`sha256(json.dumps(snap, sort_keys=True, ensure_ascii=False))` |
| **owner** | 锁文件记 UUID+PID+ts；释放前核对 |

**「互斥性不可组合」——三条腿必须一起改**（面治优先于点补）：

1. `devenv_scaffold.py` — 用新锁
2. `sdflow-init/scripts/init.py` — `inject()` 现为**裸 `open(w)` 全量覆写，无锁无原子写** ⇒ 补锁 + 原子写
3. **`sdflow-architecture/scripts/sad_scaffold.py` — 迁到共用锁 + 加 owner**（接地核实：`_acquire_lock` **根本没写入过 owner 信息**，`_release_lock` 直接 `unlink` ⇒ **是从零加机制，不是"补核对"**）

**CAS 必须覆盖 `executor` 与 `kind` 的理由**〔codex round-3〕：长跑期间 lane 从 `script`/`pure` 被改成 `human`/`hardware`，**旧脚本仍能通过只比 `status` 的 CAS 回写** ⇒ 一条本该拒绝执行的硬件泳道被盖上脚本验证的章。

## 失败模式表〔TG-08 · HR〕

| # | 失败模式 | 处理 | 状态后果 |
|---|---|---|---|
| F1 | 依赖缺失 | 如实记 `blocked_by`（差什么 + 怎么装 + 怎么 continue）。**`executor` 保持 `script`——MUST NOT 改标 `human`** | `scaffolded` |
| F2 | 验证超时 | `blocked_by` 写明「超时，未确认是环境问题还是 smoke 挂了」——**不臆断归因**。默认 300s，可按 lane 覆盖，**实际用值写进 evidence** | `scaffolded` |
| F3 | **超时后留下孤儿资源** | 杀掉**能杀到的**进程树；**recipe 内部起的容器不属于子进程组，杀不到** ⇒ **响亮报告「可能留下孤儿资源（容器/端口占用），请检查」**写进 `blocked_by` + devenv-log。**MUST NOT 声称已清理** | `scaffolded` + 显式提示 |
| F4 | smoke 本身有 bug（正向就红） | 记 `blocked_by` + 报错摘要，**MUST NOT 进 debug 循环** | `scaffolded` |
| F5 | Makefile target **名字**冲突 | **fail-closed** 留人裁决。**脚本只判名字碰撞，语义符不符归模型+人** | 中止该泳道 |
| F6 | `evidence.file_digests` 失配（`source.file` / `smoke` / `fixtures[]` 任一字节变了） | lint 报「验证证据已过期：`<file>` 已改动，需重验」（**允许多报**） | `verified` → 回落 |
| F6b | `source.selector` 拼错 / target 不存在 | **`verify-lane` 跑 `make <selector>` → make 报 `No rule to make target` → `exit≠0`**（**make 自己判**，lint **MUST NOT** 静态解析〔A21〕） | 进不了 `verified`，落 `scaffolded` + `blocked_by` |
| F7 | **③-pre 被否决** | 按 **txn journal** 逐项回退（原先存在的→**用 journal 里的原内容**复原；新写的→删）。**MUST NOT** `git checkout --`（对 untracked 无效）或无路径限定的 `git clean` | 中止本轮 |
| F8 | **写落地物后、③-pre 前崩溃** | **下次启动检测到未完成的 txn journal** ⇒ 向操作者报告并提供「回退 / 继续」选择，**MUST NOT 无视** | 启动时处理 |
| F9 | **路径逃逸**（绝对路径 / `..` / symlink 祖先 / 仓外 realpath） | **containment helper fail-closed** | 拒绝 |
| F10 | 冷审子代理无产出 | **重派一次**；再失败**显式报告缺口**，MUST NOT 无冷审静默过人门 | 阻塞人门 |
| F11 | 宿主无 fresh 子代理原语 | **显式降级 + 响亮留痕**，MUST NOT 佯装冷审 | 降级标记 |
| F12 | **非 POSIX 平台** | `verify-lane` **refuse**（不做无证据的执行）⇒ 走 `executor: human` | `human` 通道 |
| F13 | 并发锁被占 | 陈旧则提示删锁重试；否则拒绝本次写（**与 CAS 冲突不同码**） | 中止写 |
| F14 | **CAS 快照失配** | 拒绝回写，要求重跑（**与锁被占不同码**——前者重读重跑，后者退避重试） | 拒绝 |
| F15 | 删源时工作区不干净 / untracked / digest 变了 | **fail-closed** | 中止删源 |
| F16 | **未知 `schema_version`**（高于本实现） | **fail-closed**「skill 版本过旧，请升级」，MUST NOT 尽力解析 | 拒绝运行 |

**统一纪律**：失败**一律如实记录，MUST NOT 静默、MUST NOT 重试到通、MUST NOT 臆断归因**。「跑不绿」是合法状态。

## 安全与数据保护〔TG-17 · HR〕

| 面 | 风险 | 护栏 |
|---|---|---|
| **执行外部命令** | 命令来自 Makefile（人写）或 skill 追加 | ① **③-pre 人门 diff 过目**（recipe body + smoke 全文，**执行前**）② 超时 + 杀进程树（**能力边界如实告知**）③ **MUST NOT 替操作者装系统依赖** |
| **凭证泄露（ingress → git）** | 子进程继承 agent 的完整环境 ⇒ recipe 或其下游脚本可把凭证**写进文件、发往网络** | ① **最小环境 allowlist**（`PATH`/`HOME`/`SHELL`/`TMPDIR`/`LANG`/`TERM` + 按栈追加 + lane 显式声明的 `env[]`），**MUST NOT 继承完整环境**——**这是主护栏** ② 落盘输出**额外**截断 + secret 正则打码——**但此为 best-effort，非保证**；正则集合 SHALL 登记已知盲区 |
| **路径逃逸** | `source.file` / `smoke` / `fixtures[]` **全是模型填的自由文本** | **统一的 containment helper**：只接受 repo-relative 规范化路径 · 拒绝绝对路径与 `..` · **逐级 `lstat` 拒绝 symlink 祖先** · 验证最终 `realpath` 在仓内 |
| **删除用户文件** | 误删不可逆 | ① 入口一次性 `git status` 干净检查 ② 逐文件校验（有效 HEAD ∧ tracked ∧ 非 submodule/symlink ∧ digest 与人门确认时一致）③ **backup manifest 入 git 且含完整原内容**（可跨机器还原）④ 人门**单独拎出** |
| **写真代码进仓** | 引入不可信内容 | **③-pre diff 门（执行之前）** + 否决可按 **txn journal** 精确回退 |

**`owned_by` / cleanup ledger 已删除** —— skill **不主动启停任何依赖服务**，也**不管理它没有启动过的资源**。

## Decisions

### ADR-1：编排器，不是生成器

**决策**：本质是**编排器**（问 / 拍 / 落地 / 验 / 留痕），不是「从 SAD 生成文档」的生成器。
**天花板（如实记）**：greenfield 首跑能产出的是「**一份三层测试框架** + 一个可跑的 Makefile + 一张泳道表 + 一张待建清单」——**坑与护栏 day-0 问不出来**。

### ADR-2：全直写，不走 change 壳

**备选**：走 openspec change 壳——**否**：**鸡生蛋**（该 change 自己的测试要靠这套环境才能跑）；且 env 文档是 live 单例。

### ADR-3：泳道三态 + 渐进 DoD + 框架可迭代

**决策**：不强制全绿；`testing-strategy.md` 的三层框架**可迭代调整**。
**后果**：fail-closed 的落点从「完成度」移到「**诚实度**」。

### ADR-4：验证方法由模型研究提出、人拍板（**取代 negative control**）

**决策**：spec **只定证据的形状**，**不枚举验证方法**。**`script` 是默认首选；`human` 是降级路径，MUST 写明 `why_not_scriptable`。**

**推翻的旧决策**：`verified ⟺ 依赖就绪时绿 ∧ 抽掉依赖时红`。**三条独立理由（任一足够）**：

1. **只证「命令耦合依赖」，不证「断言有效」**——`assert True` + fixture 连不上 ⇒ 照样正绿反红。
2. **对 testcontainers / 内嵌 fallback（主流写法）永久误判 vacuous。**
3. **在本 skill 自己的接地样本上结构性失效**：mqtt-console 的 `Makefile:11-14` 把连接参数与依赖启停**打包进同一条 recipe 的字面文本**（`MQTT_PORT=1883` 是 shell 前缀赋值）⇒ 对任何外部覆盖免疫 ⇒ 三条抽离路径全堵死。**而这种写法常见且合理。**

**接地实验（round-3 现场跑，结论入 `references/verification-patterns.md` 作为负面知识）**：

| 方法 | 瞬时连接 | 副作用 | 结论 |
|---|---|---|---|
| 测试计数门槛 | — | 零 | **`assert True` 完美满足它** ⇒ 等于没有 |
| negative control | — | **改机器状态** | 真实项目里**常常抽不动** |
| **轮询式连接观测**（`lsof` 轮询进程组） | **❌ 5/5 全漏** | 零 | **证伪**——采样抓不住瞬时事件 |
| **proxy 计数** | **✅ 5/5 全中** | 零 | 零漏检，**但适用面 ⊆「skill 能控制依赖启动」** |

**两条硬边界**：**`assert True` 类语义恒真，任何外部插桩都堵不住**（要堵只有变异测试，太重）⇒ **机械层堵不死，诚实划归冷审 vacuous 镜**。

### ADR-5：证据只能由执行者本人写；**`human` 通道如实标注，不设防伪**

**决策**：`set-lane --status verified` **一律拒绝**。`script` → `verify-lane`（脚本自己 fork）；`human` → `confirm-lane`（人门写，标 **`attested_by: human`**）。

**`verify-lane` 保留的理由（注意：不是防伪）**：**脚本顺手就能拿到真实的 exit code，成本极低，且对「过程完整」确实有用**——能当场告诉操作者「这条跑得起来 / 这条缺 mosquitto」。**它保证的是「跑过了」，不是「模型没撒谎」。**

**`confirm-lane` 的身份保证已删除**〔`07` 附录 A18〕：**在 agent session 里，模型是唯一的命令执行者**——「模型 MUST NOT 代替操作者调用」**按字面永远为假**。**且本就不必防**（ADR-0）⇒ **如实标注 `human-attested`，MUST NOT 声称脚本保证了执行者身份。**

**`verified` 的语义钉死**：**`verified-at <sha>`——一次历史执行的记录，不是「当前状态的绿灯」**（`file_digests` **不覆盖被测实现**）。

### ADR-6：`lane-patterns` 按依赖形态分格 + 只固化「问什么」

**决策**：按**依赖形态**分格，**非按语言**；**固化维度与判据，不固化工具选型**（操作者校准：「不宜做太细太明确的限定，让大模型推荐、人做决策」）。
**注**：ADR-0 把这条原则**推广到了「验证方法」**——前一版只把它用在了泳道设计。

### ADR-7：skill 是追加者，不是拥有者

**决策**：落地物**不设托管区块**；**重名 fail-closed（只判名字，不判语义）**。
**出处锚 MUST NOT 按行号**——行号锚是**恒真断言**（「第 11–14 行存不存在」对任何长度 ≥14 行的文件恒为真）。

**〔round-4 重写，见 `07` 附录 A21〕`source: {file, kind, selector}`，无 `digest` 字段；`devenv_digest.py` MUST 零 make 知识。**

**lint 对 `source` 只查一件事**：**`evidence.file_digests` 未失配** = `source.file` + `smoke` + 声明的 `fixtures[]`，**逐文件原始字节 sha256，零规范化**。

**「target 存在且能跑」由 `verify-lane` 真 fork 执行保证——make 自己是权威判官**：

| 失效模式 | 谁抓住它 |
|---|---|
| `selector` 拼错 / target 不存在 | **`verify-lane` 跑 `make <selector>`** → make 报 `No rule to make target` → `exit≠0` → **进不了 `verified`**（**make 自己解释自己的语法，100% 覆盖，零解析器**） |
| target 后来被删/改名 | **`file_digests` 失配**（改 Makefile 必然改字节） |

> **为何删掉「按 selector 重定位 + 提取 recipe 做 digest」**：**GNU make 语法面无界**（`ifeq`/`define`/双冒号/模式规则/续行/内联 `;`/target-specific 变量…），手搓解析器必带一堆「语法不支持」罢工分支——**而它罢工一次就击穿「不管什么项目都能给一份三层框架」这条核心承诺**（`ifeq`、双冒号在真实 Makefile 里常见且合理）。**A20（手搓 Markdown 解析器）的理由逐字适用，只是当时没往这边看。**
>
> **为何连「target 存在性正则」也删**（同轮二次收缩）：它过不了 §0.0 的信号闸门。**正则找不到 target 时**——**① fail-closed 报「不存在」**：但「正则找不到」≠「不存在」（`ifeq` 包裹 / `define` 内 / 一行多 target 都会漏判）⇒ **误报罢工，原病复发**；**② 不报**：**永远不 fail = 恒真断言 = 假绿**。**两条路都错 ⇒ 删。** 而它**本就冗余**（上表已夹死该失效面）。
>
> **一般化规则**：机械层想知道「某个 make/shell/语言构造是什么意思」，**正解是让那个工具自己回答**（真跑一遍 / `make -n`），**MUST NOT 手搓解析器去猜**。本 skill 的核心机制恰好就是「**尽可能跑一遍确认**」——**跑一遍，就是最强的解析器。**
>
> **连带删除「digest 规范化按文件类型分治」**：那条规则是 **recipe 提取的衍生债**——只有切出 recipe body 才有缩进噪声、才需要 normalize。**不提取 recipe ⇒ 无需规范化 ⇒「通用 `normalize()` 把两份缩进不同的 YAML 算出同一 digest」这个假绿在结构上不可能发生**。严格更强，且不可能踩错。
>
> **代价 = 允许多报**（改了 Makefile 里别的 target 也提醒重跑）。**刻意如此**：多报的代价是重跑一次 smoke，消除多报的代价是 300 行解析器——**且方向反了，防漏宁可多报**。

### ADR-8：SAD 缺失 → 显式降级，非 fail-closed

**备选**：fail-closed 要求先跑 `/sdflow-architecture`——**否**：会把所有没做过 SAD 的**存量项目**挡在门外（而它们恰恰最需要补测试环境）。

### ADR-9：归位模式并入同一 skill

**连带义务**：删源护栏 = **逐文件校验 + backup manifest（入 git，含完整原内容）**——**clean worktree 并不足以保护删除**。

### ADR-10：独立 marker `opsx-devenv` + fence-aware

**理由（代码事实）**：`init.py:49-52` 的注释明确标注判据**尚非 fence-aware**，fence-aware 版本**已 defer**。**直接照抄将继承该缺陷**。

### ADR-11：v1 只承诺 POSIX 的进程树杀灭

**备选**：(a) 引入 `psutil`——**否**：违反零依赖纪律。(b) 写 Windows 的 `taskkill /T /F` 分支——**技术上零依赖可行**（系统自带命令），**但我们没有 Windows 环境实测** ⇒ **写一段从未在该平台执行过的代码并声称它能杀进程树，正是 ADR-0 反复批判的「无证据的绿」**。
**后果**：Windows **不是特例**——它命中的就是 `executor: human` 通道。**先诚实，再扩面。**

### ADR-12：**三层框架落 JSON，Markdown 从 JSON 渲染**〔round-3 新增〕

**决策**：`.devenv-strategy.json` 是三层框架的机械真相源；`testing-strategy.md` 由脚本渲染。
**备选**：让 lint 解析自由格式 Markdown——**否**：**又一个手搓解析器**（本仓前科：`parse_frontmatter` / `inject` / `ship_gate` 全部踩过）。且「三层五槽全部非空」+「`不适用`」并存而**无豁免条款** ⇒ **逼模型为「不做这件事」编造废话** ⇒ **机械层奖励空话、惩罚诚实**（填表游戏）。
**后果**：`not-applicable` ⇒ **①–④ 槽豁免**；lint 检查的是 **JSON 字段**——**真机械**。

## Risks / Trade-offs

| # | 风险 | 缓解 |
|---|---|---|
| **R-1** | **模型提的验证方法很弱**（甚至无效），而 skill 按设计不判断质量 | ③-pre 人门**逐条确认验证方法**（含 `strength` 的强度与盲区）+ 冷审**验证方法镜**。**这是有意的设计取舍（ADR-0）**：质量由模型能力 + 人判断保证，不由脚本 |
| **R-2** | **无独立信号的声明误判**（`kind`/`layer`/`fixtures`/`env`/`executor`） | ③-pre **声明清单必过人门**（表格化一次呈现）+ 冷审**分类镜**。**MUST NOT 佯装机械识别** |
| **R-3** | **冷审与提方案的模型同档同源** ⇒ 系统性盲区共享 | **如实登记为已知局限**〔round-3 对抗镜〕：「轮询式观测漏检」这个盲区**不是冷审子代理发现的，是人现场跑实验挖出来的** ⇒「冷审能独立挖出同类盲区」**无实证支持**。缓解：`verification-patterns.md` 沉淀**负面知识**，让下一次的模型站在已知盲区之上 |
| **R-4** | **永久 `scaffolded`** | 收尾**逐条列出** + `blocked_by` 必须含**可操作**修复指引 + **`sdflow-maintain` 每次扫描复述未完成清单**。**诚实边界：maintain 是人主动跑的 ⇒ 是「更响的提醒」非硬门禁** |
| **R-5** | **人门疲劳** ⇒ 橡皮图章 | **呈现分级**（新写的全文 / 仅登记的只展示映射）+ **②③ 表格化一次性呈现**（不逐条打断） |
| **R-6** | **首跑交互成本上升**——三层 15 槽 + 每条泳道的验证方法都要人拍 | **这是 ADR-0「诚实优先于假机械」的直接代价**：脚本内部复杂度下降，**流向人的决策负荷上升**。**上游试点 MUST 记录 SM-7 的「人工回答数」以验证这个权衡是否可接受** |
| **R-7** | **fence-aware 实现遗漏** | pytest **必须**覆盖「代码块内有 marker 演示」（**checkin 固定 fixture，MUST NOT 拿本仓活语料**） |

## Migration Plan

**部署**：纯增量。新增 `sdflow-devenv/` → 重跑 `bash setup.sh`。
**跨 skill 改动**（面治，非可选）：`sdflow-init/scripts/init.py`（inject 补锁 + 原子写 + description 反向排除句）· `sdflow-architecture/scripts/sad_scaffold.py`（迁共用锁 + **从零加 owner** + `atomic_write` 加 mode 参数）· `sdflow-maintain`（**新增** devenv 健康度扫描）。
**消费仓**：不跑本 skill 则**完全无感**。
**回滚**：`git revert` + 重跑 `setup.sh`。

## Open Questions

> **编号以 proposal 为准**（前一版三份文档的 Q 编号互相打架）。

| # | 问题 | 处置 |
|---|---|---|
| Q-1 | `lane-patterns` / `verification-patterns` 未覆盖形态何时补格 | v1 走兜底；补格由首个撞上的项目驱动 |
| Q-2 | monorepo 多系统（需 SAD 先支持） | v1 单例 + 显式提示 |
| Q-3 | lint「入口复述检测」阈值待接地校准 | 实现期给保守阈值 |
| Q-4 | **harvest loop**（从 buglist / code-review 机械喂坑与盲区进 testing-strategy） | **最高价值演进方向**，v2 |
| Q-5 | Windows 的 `taskkill /T /F` 分支 | 有 Windows 环境实测后，从 `human` 升为 `script` |
| Q-6 | `sdflow-maintain` 是人主动跑 ⇒ 是否加 `ship_gate` 硬拦截？ | **延后**：首个僵尸 `scaffolded` 出现时再定 |
| Q-7 | SAD `draft` 态时 contract 随时改名 ⇒ `covers` 锚可能悄悄失真 | **已知局限**：`sad` 字段只有 `present\|missing`，v1 显式登记 |
| Q-8 | `schema_version` **低于**本实现时的策略 | v1 无需处理（只有 v1）；**MUST 在引入 v2 的 change 里显式定义**，MUST NOT 现场处理 |

## Compliance

- **机械化优先 + 诚实边界**（CLAUDE.md 基准 1 · **本 change 的 ADR-0**）：**防漏的一律机械化；防伪的一律诚实划归语义层，MUST NOT 硬凑假机械。**
- **面治优先于点补**（基准 3）：`init.py` 补锁 · `sad_scaffold` 迁锁 + 加 owner + `atomic_write` 加 mode · 双向分流句——一次扫全。
- **目标态导向**（基准 2）：三层框架锚目标态，**MUST NOT** 以「现存项目大多只有单元测试」论证「e2e 可省」——省了就写 `不适用 + 后果`。
- **托管区块纪律**：`opsx-devenv` 为新 marker token，**MUST NOT** 写入 `opsx-init` 区块。
- **HR-TG**：命中 TG-08 / 09 / 17 / 26 ⇒ spec-review 单开领域 cross-model。
- **测试纪律**：改 `scripts/` 必跑 `tests/`。
