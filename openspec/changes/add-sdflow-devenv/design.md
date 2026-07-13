# design — add-sdflow-devenv

> 设计源：`docs/sad/07-devenv-skill-design.md` · 接地证据：`docs/sad/06-process-axis-grounding-receipt.md`
> 命中 TG：05 · 08 · 09 · 10 · 11 · 12 · 13 · 14 · 15 · 17 · 18 · 19 · 21 · 22 · 23 · 25 · 26（HR-TG：08 / 09 / 17 / 26）
>
> **本文档已按 round-2 设计门（2026-07-13）整体重写。** 前一版的正文（含 ADR-4 的 ⟺ 定义、嵌套 YAML 数据模型、
> 行号出处锚、11 条失败模式表、"无 secret 出境面"、以及两张与新 spec 逐字相反的图）**已作废**。
> **考古层不在本文件维护——`git show 626f741^:.../design.md` 即完整旧稿。**
> 真相源 = `specs/`；本文档只讲**为什么这么设计**。

---

## ADR-0：总则——无法明确确定的问题，交给模型研究，人确认〔凌驾于以下所有 ADR〕

**决策**：skill 的机械层**只保证「过程完整」与「诚实」**——有没有验证方法 · 执行了没 · 证据是不是执行者本人写的 · 状态有没有撒谎。**机械层 MUST NOT 试图替人判断「这个方案好不好」「这个验证有没有效」。**

**MUST NOT 硬凑假机械**：凡机械够不着的（验证方法是否有效 · 依赖分类是否属实 · smoke 断言是否语义恒真 · `covers` 是否真命中），一律**诚实划归语义层**（模型提 + 人拍 + 冷审），MUST NOT 用枚举 / dispatch 表 / 白名单包装成"脚本判定"。

**理由（这条 ADR 是被 round-2 评审逼出来的）**：前一版把 negative control 写成 `verified` 的**定义**（⟺），随即被迫为它发明 `isolate` 字段 / `expected-failure predicate` / `kind → 策略 dispatch` / runner 白名单。八镜评审逐条拆穿：这些"机械判定"的输入**全是模型自填的裸声明**——

| 号称"机械保证" | 机械层实际只查了 | 谁在真正承担 |
|---|---|---|
| R1 红线（只停 `owned_by: skill`） | 字段**存在** | 模型自填 |
| 硬件不执行（`kind`） | 字段**存在** | 模型自填 |
| 门槛②（`expected-failure predicate`） | **schema 里根本没这个字段** | 无 |
| 门槛①（测试真跑） | `collected≥1 ∧ skipped=0` ← `assert True` **完美满足** | 冷审 |
| `verified` 的诚实性（`blocked_by`） | **非空** ← `"TODO"` 即过 | 模型自觉 |

**七条里没有一条的机械层在检查它声称要保证的那个语义。**这不是七个 bug，是一个**面**——而它的源头，是「让脚本替人判断质量」这个从一开始就错的目标。

**后果**：**假机械比诚实的语义层更危险**——它让人以为有防线。本 ADR 把"诚实边界"从一个补丁提升为设计的第一原则。

**先例**：CLAUDE.md 设计基准 1（机械化优先 + 诚实边界）· 基准 3（面治优先于点补）。

---

## Context

生态里「技术架构定了之后把 dev/test 环境真正建起来」无 skill 覆盖：`sdflow-architecture` 交棒止于「过程轴文档指路（指出不代写）」，下游为空；`sdflow-init` 铺的是 **workflow 的运行环境**（规则 bundle），按定义不管项目内容。

mqtt-console 接地实测（`06`）给出的硬事实（**证据分层见 proposal，此处不复述强度**）：

1. **SAD 投影率 12%（严）/ 41%（宽）**——「从 SAD 生成文档」这条腿不成立。**注**：前一版据此推出"那 88% 恰恰全是待决策项"，已被 `06` 自己的**三分法**（SAD 投影 / 构建配置投影 / 纯人写）**证伪**——三者并存，不是二分。
2. **真正的机械投影源是构建配置**（Makefile / package.json），不是 SAD ⇒ 命令表可对构建配置核验、甚至渲染。
3. **纯文档型产物有虚构命令的风险**——**但 `06` 的实测结果是「零虚构、行号全中」**（此为**预测风险，非观测事实**，proposal 已如实分层）。本 skill 亲手写 Makefile，命令天然为真，是**消除该风险**而非**修复已发生的问题**。

**现状约束**：`sdflow-architecture` 已确立 recorder 式直写 + 双脚本（scaffold 写 / lint 读）+ fresh 子代理冷审 + 人门的骨架，本 skill 与之**对称**（空间轴 ↔ 过程轴）。

## Goals / Non-Goals

**Goals：**

- **不管什么项目，操作者都能拿到一份完整的测试与验证策略框架**——单元 / 集成 / e2e 三层各自交代清楚（怎么实现 · 规范 · 方法流程 · 要配什么工具 · 状态）。做不了的写**不适用 + 后果**，要人做的写**人怎么做**。
- 把 dev/test 环境**真正建起来**：决策 → 落地物（Makefile / CI / harness / smoke / doctor）→ 验证 → 两份真相源 + 入口索引。
- **渐进 DoD**：泳道逐条推进，不强制全绿；**框架可迭代**，不是一次定死。
- **诚实是硬要求**：跑不绿合法，**跑不绿却装作跑得绿**不合法。
- 与既有生态**零冲突**：独立 marker、真硬件复用 `embedded-test-sop`。

**Non-Goals：**

- **替人判断验证方法有没有效**（ADR-0）· 业务测试用例（归各 change）· 生产 runbook · 替用户装系统依赖 · smoke debug 到通 · monorepo 多系统（v1）· 时间轴排期 · 从 SAD 自动生成文档。

## 组件清单〔TG-13/14〕

| 组件 | 职责 | 类型 |
|---|---|---|
| `SKILL.md` | 五步编排 · 三模式分流 · 时序纪律 · **两道人门**议程 | Markdown |
| `scripts/devenv_scaffold.py` | **写**：`init` · `set-lane`（**只管 planned/scaffolded**）· **`verify-lane`**（script 通道：脚本亲自执行）· **`confirm-lane`**（human 通道：人门写证据）· `render` · `inject` · `log` · `doctor-gen` | Python |
| `scripts/devenv_lint.py` | **读**：诚实检查（**不查质量**）+ 测试三层框架完整性 | Python |
| `scripts/devenv_schema.py` | JSON schema 定义与校验（两脚本共用，防口径漂移） | Python |
| `references/lane-patterns.md` | 依赖形态四问 + 阶梯判据 + 参考实例（**非规格**） | Markdown |
| **`references/verification-patterns.md`** | **验证方法参考实例（非规格）+ 已知负面知识** | Markdown |
| `references/boundary-rules.md` | 切线表 + 归属判据 | Markdown |
| `references/environments-template.md` · `testing-strategy-template.md` | 槽位模板（后者含**三层 × 五槽**强制框架） | Markdown |
| `references/quality-criteria.md` | E 判据真相源（三处投影的唯一源） | Markdown |
| `references/review-lenses.md` | 冷审镜单（含**验证方法镜**与**分类镜**） | Markdown |
| `tests/` | pytest（本仓纪律：改 `scripts/` 必跑 `tests/`） | Python |

## 数据模型〔TG-05〕

**机械真相源 = `openspec/architecture/.devenv-lanes.json`**（标准库 `json`，零依赖）。
`environments.md` 的 frontmatter 只留三个**扁平标量**：`sad` · `mode` · `schema_version`。
正文命令表由 `render` 生成（`DO NOT EDIT` banner），**不双写**。

```json
{
  "schema_version": 1,
  "lanes": [{
    "id": "mqtt-integration",
    "layer": "unit | integration | e2e",          // ← 对应 testing-strategy 的哪一层
    "kind": "external-dep | ui | lang-bridge | hardware | pure",
    "status": "planned | scaffolded | verified",
    "verification": {
      "method":   "<模型提出、人拍板：怎么验>",      // MUST 非空
      "executor": "script | human",                // 决定证据由谁写
      "strength": "<模型自陈：证明了什么、盲区是什么>",
      "evidence": { "at": "...", "at_commit": "<HEAD SHA>",
                    "exit": 0, "output_digest": "...",
                    "method_digest": "<方法+smoke+harness+fixture+lockfile 联合摘要>",
                    "confirmed_what": "<executor=human 时：人确认了什么>" }
    },
    "source": {"file": "Makefile", "kind": "make-target",
               "selector": "integration", "digest": "<recipe 规范化后 sha256>"},
    "smoke": "<path>",
    "deps": [{"name": "mosquitto", "kind": "compose|host-service|port|toolchain|testcontainer",
              "owned_by": "skill | operator"}],      // ← owned_by 为【派生】非声明
    "covers": ["<SAD contract 锚>"],
    "blocked_by": "<scaffolded 时必填：卡在哪 + 怎么修 + 怎么 continue>"
  }]
}
```

**字段的信号来源（ADR-0 的落地）**——这张表是本设计的核心，每个"机械判定"都必须交代它的信号：

| 字段 | 信号来源 | 机械还是语义 |
|---|---|---|
| `evidence.*` | **脚本 fork 执行的实际结果** / **人门产物** | **机械**（执行者本人写，模型填不进来） |
| `source.digest` · `method_digest` | **文件内容的 sha256** | **机械** |
| `owned_by` | **运行时事实**：本次运行内 skill 自己调过启动命令 ⇒ `skill`；此前已在跑 ⇒ `operator` | **机械（派生）** |
| `status` | 由 `evidence` 是否齐全推出 | **机械** |
| `verification.method` · `strength` | 模型研究 + 人拍板 | **语义**（进人门 + 冷审「验证方法镜」） |
| `kind` · `layer` | 模型判断 | **语义**（进 ③-pre 人门分类清单 + 冷审「分类镜」）——**MUST NOT 佯装机械** |
| `covers` | 模型判断 | **语义**（冷审「覆盖镜」） |

## 状态机图〔TG-09〕（round-2 重画）

```
                          ②泳道拍板 + 验证方法拍板
                                    │
                                    ▼
                            ┌──────────────┐
                            │   planned    │  决定要有；验证方法可后定
                            └──────┬───────┘
                                   │ ③落地：smoke/harness 已写
                                   │        ∧ verification.method 非空
                                   ▼
                            ┌──────────────┐
             ┌─────────────▶│  scaffolded  │◀────────────┐
             │              └──────┬───────┘             │
             │  continue 推进       │                     │  【回落】
             │  (装完依赖/修完      │  按 executor 分流    │  method_digest 失配
             │   smoke/换方法)      │                     │  (人改了 recipe/smoke/
             │                     │                     │   fixture/验证方法)
             │         ┌───────────┴───────────┐         │
             │         │                       │         │
             │  executor=script         executor=human   │
             │         │                       │         │
             │         ▼                       ▼         │
             │  ┌─────────────┐         ┌─────────────┐  │
             │  │ verify-lane │         │ confirm-lane│  │
             │  │ 脚本亲自 fork│         │ 人门写证据   │  │
             │  │ 执行、捕获   │         │ (模型 MUST  │  │
             │  │ exit/输出    │         │  NOT 代填)  │  │
             │  └──────┬──────┘         └──────┬──────┘  │
             │         │                       │         │
             │      失败│                    成功│成功     │
             └─────────┘                       │         │
                       │                       │         │
                       └───────────┬───────────┘         │
                                   ▼                     │
                            ┌──────────────┐             │
                            │   verified   │─────────────┘
                            └──────────────┘
                              evidence 齐全
                              ∧ blocked_by 为空

  ┌─ 铁律 ────────────────────────────────────────────────────────────┐
  │ • `set-lane --status verified`  →  一律 exit 5 拒绝               │
  │   （set-lane 只管 planned / scaffolded；verified 只能由           │
  │     verify-lane 或 confirm-lane 产出——证据只能由执行者本人写）    │
  │ • verification.method 为空       →  lint fail-closed              │
  │   （不存在"不知道怎么验"的泳道——人工测试也是方法）                │
  │ • scaffolded ∧ blocked_by 空/敷衍 →  lint fail-closed             │
  │ • verified ∧ blocked_by 非空     →  lint fail-closed              │
  │   （绿泳道上挂着「本机无 mosquitto」= 文档在说谎）                 │
  │ • 非 POSIX 平台 → verify-lane refuse → 该泳道改走 human 通道       │
  │ • kind: hardware → verify-lane refuse → 走 human（embedded-test-sop）│
  └───────────────────────────────────────────────────────────────────┘
```

> **「无法验证」不是一个合法状态**——故**没有** `n/a` 态。人工测试也是验证方法；区别只在 `executor`。

## 关键时序图〔TG-10〕（round-2 重画：**diff 门移到执行之前**）

```
操作者      主 session       devenv_scaffold    冷审子代理(fresh)    消费仓
  │              │                  │                  │              │
  │/sdflow-devenv│  init            │                  │              │
  ├─────────────▶├─────────────────▶│ preflight+分流   │              │
  │              │◀─────────────────┤ exit code        │              │
  │              │                  │                  │              │
  │ ①事实复核(批量呈现,一次确认)     │                  │              │
  │◀────────────▶│                  │                  │              │
  │ ②泳道 + 三层框架 + 验证方法(模型提,人拍)            │              │
  │◀────────────▶│ set-lane(planned)│                  │              │
  │              ├─────────────────▶│──── 持锁+原子写 ───────────────▶│
  │              │                  │                  │              │
  │              │ ③写落地物(追加)   │                  │              │
  │              │   先记 touched-files 事务清单        │              │
  │              ├──────────────────────────────────────────────────▶│
  │              │                  │                  │              │
  ╞══════════════╪══════ ③-pre 人门（执行任何验证之前）═══════════════╡
  │ ① 新写落地物 diff 全文(recipe body + smoke 源码)    │              │
  │ ② 验证方法逐条确认(含模型自陈的强度与盲区)          │              │
  │ ③ 依赖分类清单(kind/owned_by/executor —— 无独立信号,必须人看)      │
  │ ④ 将执行的命令(recipe 展开)                        │              │
  │ ⑤ 「将改变机器状态」显著呈现(若有)                  │              │
  │◀─────────────┤                  │                  │              │
  │  同意 / 否决  │                  │                  │              │
  ├─────────────▶│                  │                  │              │
  │              │ 否决 → 按 touched-files 清单逐项回退  │              │
  │              │   (新写的→删；既有的→复原。MUST NOT git clean)      │
  ╞══════════════╪════════════════════════════════════════════════════╡
  │              │                  │                  │              │
  │              │ verify-lane      │ 脚本亲自 fork 执行│              │
  │              ├─────────────────▶│ (最小环境 allowlist│             │
  │              │                  │  + 进程组 + 超时  │              │
  │              │                  │  + cleanup ledger)│             │
  │              │                  ├──────────────────────────────▶│
  │              │◀─────────────────┤ 写 evidence(原子)│              │
  │              │                  │                  │              │
  │              │ 派冷审(禁自查)    │                  │              │
  │              ├─────────────────────────────────────▶│ 读产物      │
  │              │                  │                  ├─────────────▶│
  │              │◀─────────────────────────────────────┤ 镜单发现     │
  │              │                  │                  │              │
  ╞══════════════╪══════════ ④ 人门（执行后 + 冷审后）═══════════════╡
  │ ① 泳道设计复核  ② 未 verified 泳道逐条确认                        │
  │ ③ N/A 槽逐条确认(三层框架的"不适用"必须记后果)                     │
  │ ④ executor=human 泳道的人工验证结果 → confirm-lane                │
  │ ⑤ 【归位模式】删源清单 —— 单独拎出,不可逆,不与常规议程同级         │
  │◀────────────▶│                  │                  │              │
  ╞══════════════╪════════════════════════════════════════════════════╡
  │              │ render + inject  │                  │              │
  │              ├─────────────────▶│──── 持锁+原子写 ───────────────▶│
  │ ⑤收尾: 逐条列未 verified 泳道 + 整体判定 + 下一步怎么调用          │
  │◀─────────────┤                  │                  │              │
```

> **为什么 diff 门必须在执行之前**：前一版把它放在执行之后 ⇒ **模型生成的 recipe body 与 smoke 源码，在任何人看过一眼之前就已经被执行了**。而"跑前列命令给操作者过目"给人看的是 `make integration` 这**一行调用**，对"target 里到底跑什么"提供**零信息量**——真正危险的内容恰恰不在那个门里。

## 三模式分流决策图〔TG-12〕

```
                        触发 /sdflow-devenv
                               │
                    devenv_scaffold.py init
                               │
             ┌─────────────────┼──────────────────┐
             ▼                 ▼                  ▼
      exit 3 无 openspec  exit 4 已有产物    exit 0 全新
             │                 │                  │
             ▼                 ▼                  │
      ┌────────────┐   ┌───────────────┐          │
      │ fail-closed│   │ 显式区分:      │          │
      │ 指引 init  │   │ continue/replan│          │
      └────────────┘   └───────┬───────┘          │
                               │                  │
                    ┌──────────┴─────┐            │
                    ▼                ▼            ▼
              continue          replan      检出存量素材?
              (推进泳道 /      (栈或测试策略  ┌────┴────┐
               改验证方法 /    被推翻,重走②)  ▼         ▼
               某层从"不适用"                有        没有
               改"已实现")                    │         │
                                              ▼         ▼
                                      ┌──────────┐ ┌──────────┐
                                      │ 归位模式  │ │ 新建模式 │
                                      │ ①'盘点   │ │ ①事实采集│
                                      │ 判归属    │ │          │
                                      │ 搬运表人门│ │          │
                                      └────┬─────┘ └────┬─────┘
                                           └──────┬─────┘
                                                  ▼
                                    ②泳道 + 三层框架 + 验证方法拍板
                                    → ③落地 → ③-pre 人门 → 验证
                                    → 冷审 → ④人门 → ⑤文档+入口

  SAD 缺失(任何模式)：显式降级 + 响亮告警 + frontmatter 留痕 sad:missing，MUST NOT 佯装
```

## 归位模式数据流图〔TG-11〕

```
散落素材                    判归属(唯一无信号步)              目标格
──────────                 ────────────────────            ──────────
docs/getting-started.md ─┐                              ┌─▶ environments.md
docs/**/testing*.md      ├─▶ 盘点(逐节)                  ├─▶ testing-strategy.md
roadmaps/*/testing-*.md  ├─▶   ↓ boundary-rules.md 切线  ├─▶ roadmap (时间轴)
README/CLAUDE/AGENTS     ├─▶ 搬运表 ──【人门·必先确认】──┼─▶ SAD (架构决策)
已有 Makefile/测试       ─┘     ↓                        ├─▶ 入口(最小命令+指针)
                                │                        └─▶ 删除
                                ▼
                    grep 被引用面 (确定性信号)
                                │
                 ┌──────────────┼──────────────┐
                 ▼              ▼              ▼
             引用=0         引用可枚举      引用面广/散
                 │              │              │
                 ▼              ▼              ▼
            整体删除      改引用后删     降为一行指针
                 └──────────────┴──────────────┘
                                ▼
              删源前置(一次性入口检查): git status 干净
                                ▼
              逐文件校验: 有效 HEAD ∧ tracked ∧ 非 submodule/symlink
                          ∧ digest 与人门确认时一致
                                ▼
              backup manifest (入 git, 可跨机器还原)
                                ▼
              扫残留引用(含代码注释, 排除 .devenv-backup/)
```

## 并发与共享状态访问策略〔TG-26 · HR〕

**风险为已证实而非推测**：`sdflow-architecture` 的多镜 code-review 在同款场景抓出 **5 个 CRITICAL 并发缺陷**。本 skill 同样对 `openspec/architecture/` 下多个文件做读-改-写。

| 机制 | 实现 |
|---|---|
| **写域锁（三 skill 共用）** | `openspec/.sdflow-write.lock`，`os.open(O_CREAT\|O_EXCL\|O_WRONLY)`——**跨平台，不用 `fcntl`** |
| **原子写** | `mkstemp`（唯一 tmp 名）→ 写 → `chmod(mode)` → `os.replace()`。**`atomic_write` MUST 接受 mode 参数**——`sad_scaffold` 现硬编码 `0o644` ⇒ 生成的 doctor 脚本**落盘即不可执行** |
| **锁作用域** | 包裹**整个读-改-写序列**；**MUST 短持有，MUST NOT 跨验证执行持有** |
| **CAS** | 覆盖 lane 的**全部验证输入快照**（`status` + `method` + `source` + `smoke` + `deps`），**不只是 `status`** |
| **owner 核对** | 锁文件记 UUID + PID + 时间戳；释放前核对，MUST NOT 删他人的锁 |

**「互斥性不可组合」——三条腿必须一起改**（承基准 3：面治优先于点补）：

1. `devenv_scaffold.py` — 用新锁
2. `sdflow-init/scripts/init.py` — `inject()` 现为**裸 `open(w)` 全量覆写，无锁无原子写** ⇒ 补锁 + 原子写
3. **`sdflow-architecture/scripts/sad_scaffold.py` — 现用 `.sad-scaffold.lock`（另一把锁），且释放时不核 owner** ⇒ 迁到共用锁 + 补 owner 核对

> **前一版只改了 `init.py`，漏了 `sad_scaffold`——「三 skill 共锁」在 tasks 里只有两条腿**（codex 接地实证：`sad_scaffold.py:38`）。

**锁不跨长跑持有的理由**：`sad_scaffold` 的 `LOCK_STALE_SEC = 120` 是为**亚秒级**操作而调；而验证可跑数分钟 ⇒ 锁若跨验证持有，并发 session 会把**活锁判成残留锁** → 提示"删锁重试" → 用户照做 → **两 session 同时写**。**陈旧锁检测由保护变成攻击面。**

**CAS 必须覆盖全部输入快照的理由**：仅比对 `status` 不够——`verify-lane` 在无锁状态下读了 `method`/`smoke` 去跑数分钟，期间另一 session 可改同一 lane 的这些字段而**保持 `status` 不变**（它自己的 CAS 照样通过）⇒ 旧验证回写成功 ⇒ **lane 记的是新命令，证据是旧执行的**。**修活锁的那个修法，亲手打开了这个洞。**

## 失败模式表〔TG-08 · HR〕

| # | 失败模式 | 检测 | 处理 | 状态后果 |
|---|---|---|---|---|
| F1 | 依赖缺失 | 命令非零退出 + stderr 特征 | 如实记 `blocked_by`（差什么 + 怎么装 + 怎么 continue） | `scaffolded` |
| F2 | 验证超时 | 超时阈值（默认 300s，可按 lane 覆盖；**实际用值写进 evidence**） | `blocked_by` 写明「超时，未确认是环境问题还是 smoke 挂了」——**不臆断归因** | `scaffolded` |
| F3 | **超时后留下孤儿进程/容器** | 进程组仍存活 / cleanup ledger 有未回收项 | **杀整棵进程树** + 按 ledger 回收；**cleanup 失败 = 独立失败状态**，不能只写普通 `blocked_by` | 独立失败 |
| F4 | **脚本被 SIGKILL，ledger 随进程蒸发** | **下次启动扫描落盘的 ledger** | ledger **落盘**（资源创建成功后**立即**写）；启动时自愈扫描 + 回收或响亮报告 | 启动时处理 |
| F5 | **改变了机器状态但未恢复**（停了服务 / 改了配置） | `try/finally` | **`finally` 恢复**；恢复失败 **MUST 响亮报告 + 写 devenv-log** | 响亮报告 |
| F6 | smoke 本身有 bug（正向就红） | 命令非零退出 | 记 `blocked_by` + 报错摘要，**MUST NOT 进 debug 循环** | `scaffolded` |
| F7 | Makefile target **名字**冲突 | 追加前扫描已有 target 名 | **fail-closed** 报冲突，留人裁决。**脚本只判名字碰撞，语义符不符归模型+人** | 中止该泳道 |
| F8 | `source.digest` / `method_digest` 失配（人改了 recipe/smoke/fixture） | lint | fail-closed 报「验证证据已失效，需重验」 | `verified` → 回落 |
| F9 | **③-pre 被否决** | 人门 | 按 **touched-files 事务清单**逐项回退（新写的→删，既有的→复原）。**MUST NOT** 用无路径限定的 `git clean` | 中止本轮 |
| F10 | 冷审子代理无产出 | 无镜单结果 | **重派一次**；再失败**显式报告缺口**，MUST NOT 无冷审静默过人门 | 阻塞人门 |
| F11 | 宿主无 fresh 子代理原语 | 能力探测 | **显式降级 + 响亮留痕**，MUST NOT 佯装冷审 | 降级标记 |
| F12 | **非 POSIX 平台** | preflight 探测 | `verify-lane` **refuse**（不做无证据的执行）；该泳道走 `executor: human` | `human` 通道 |
| F13 | 并发锁被占 | `O_EXCL` 失败 | 陈旧则提示删锁重试；否则拒绝本次写 | 中止写 |
| F14 | **CAS 快照失配**（长跑期间 lane 被改） | 回写时锁内重读比对 | **拒绝回写**，要求重跑验证 | 拒绝 |
| F15 | 删源时工作区不干净 / 文件 untracked / digest 变了 | git 前置 + 逐文件校验 | **fail-closed** | 中止删源 |
| F16 | **未知 `schema_version`**（高于本实现） | 读取时比对 | **fail-closed**「skill 版本过旧，请升级」，MUST NOT 尽力解析 | 拒绝运行 |

**统一纪律**：失败**一律如实记录，MUST NOT 静默、MUST NOT 重试到通、MUST NOT 臆断归因**。「跑不绿」是合法状态。

## 安全与数据保护〔TG-17 · HR〕

> **前一版的结论「不外发 ⇒ 无 secret 出境面」是错的**——它漏了 **ingress → git**：命令继承 agent session 的完整环境变量，失败回显（`AMQP_URL=amqp://user:pass@host`）写进 `blocked_by` / `devenv-log` → **commit → push**。**不主动外发，但把 secret 写进了必然被外发的载体。**

| 面 | 风险 | 护栏 |
|---|---|---|
| **执行外部命令** | 命令来自 Makefile（人写）或 skill 追加；可能起容器、占端口、写文件 | ① **③-pre 人门 diff 过目**（recipe body + smoke 全文，**执行前**）② 每条有超时 + **杀进程树** ③ **MUST NOT 替操作者装系统依赖** |
| **凭证泄露（ingress → git）** | 子进程继承 agent 的完整环境 ⇒ recipe 或其下游脚本可把凭证写进文件、发往网络 | ① **子进程走最小环境 allowlist**（`PATH`/`HOME`/lane 显式声明的变量），**MUST NOT 继承完整环境**——**这是主护栏** ② 落盘输出**额外**截断 + secret 正则打码——**但此为 best-effort，非保证**；正则集合 SHALL 登记已知盲区，**MUST NOT 用绝对语气佯装** |
| **改变机器状态** | 停服务是**减法**，比装依赖（加法）更破坏性 | ① `owned_by` **派生**（只有本次运行内 skill 自己启动过的才是 `skill`）② `owned_by: operator` → **MUST NOT stop** ③ `try/finally` 恢复 + cleanup ledger **落盘** ④ 跑前**单列显著呈现** |
| **删除用户文件** | 误删不可逆 | ① 入口一次性 `git status` 干净检查 ② **逐文件校验**（有效 HEAD ∧ tracked ∧ 非 submodule/symlink ∧ digest 与人门确认时一致）③ **backup manifest 入 git**（可跨机器还原）④ 搬运表**显著呈现** + 人门**单独拎出** |
| **写真代码进仓** | 引入不可信内容 | **③-pre diff 门（执行之前）** + 否决可按 touched-files 清单精确回退 |

**敏感数据**：冷审子代理为本地 Agent（无 outside-voice / 无跨模型出境）。生成的示例/fixture **SHALL 用占位符**（`<mqtt-host>` / `<device-id>`），MUST NOT 写入真实凭证。

## 可观测性〔TG-08 / TG-15〕

| 面 | 载体 | 内容 |
|---|---|---|
| **审计留痕** | `devenv-log.md`（append-only） | 模式分流 · 泳道状态迁移（**含执行者字段**：`verify-lane` / `confirm-lane`）· SAD 降级 · 冷审轮次与执行者 · 人门通过 · **机器状态改变与恢复** · 删源清单 |
| **cleanup ledger** | `.devenv-cleanup.ledger`（**落盘**） | 已创建的资源（容器/进程）；启动时自愈扫描 |
| **断点恢复** | `devenv-log.md` | `continue` 靠它定位断点 |
| **当前态** | `.devenv-lanes.json` | 泳道状态全景（机器可读） |
| **对话可见** | 收尾报告 | **逐条列出**未 `verified` 泳道 + `blocked_by` + **整体判定 + 下一步怎么调用** |
| **诚实码** | lint 通过码 | `structure-ok-SEMANTICS-UNCHECKED`：结构通过 ≠ 内容已审 |

## Decisions

### ADR-1：编排器，不是生成器

**决策**：立 skill，其本质是**编排器**（问 / 拍 / 落地 / 验 / 留痕），不是「从 SAD 生成文档」的生成器。
**备选**：(a) 模板 + 手跑 prompt——**否**：拿不到 lint / 冷审 / 托管注入 / 真验证。(b) 并入 `sdflow-init`——**否**：init 按定义只管 workflow 运行环境，不管项目内容。
**天花板（如实记）**：greenfield 首跑能问出来的**不含** `06` 认定的全部价值——**坑与护栏 day-0 问不出来**。首跑的诚实交付 = 一个可跑的 Makefile + 一张三层框架表 + 一张泳道表 + 一张待建清单。

### ADR-2：全直写，不走 change 壳

**决策**：文档与脚手架**都直落盘**，质量门内建（lint + 验证 + 冷审 + ③-pre 人门 diff）。
**备选**：走 openspec change 壳——**否**：**鸡生蛋**（该 change 自己的测试要靠这套环境才能跑）；且 env 文档是 live 单例，套 change 壳会反复开壳。
**先例**：`sdflow-architecture` 规则 4 / `sdflow-roadmap`（recorder 式直写）。

### ADR-3：泳道三态 + 渐进 DoD + 框架可迭代

**决策**：`planned → scaffolded → verified` 逐条推进，**不强制全绿**；`testing-strategy.md` 的三层框架**可迭代调整**，不是一次定死。诚实为硬要求。
**备选**：一次性 fail-closed 全绿 DoD——**否**：项目初期定不下所有事（操作者原话：「有个方向和基本能力就行」）。
**后果**：fail-closed 的落点从「完成度」移到「诚实度」——跑不绿合法，**跑不绿却装作跑得绿**不合法。

### ADR-4：验证方法由模型研究提出、人拍板（**取代前一版的 negative control ⟺ 定义**）

**决策**：spec **只定证据的形状**（`method` / `executor` / `evidence`），**不枚举验证方法**。方法由模型根据项目实际环境现场研究推荐，人拍板。
**推翻的旧决策**：前一版 `verified ⟺ 依赖就绪时绿 ∧ 抽掉依赖时红`。
**为什么推翻**（三条独立理由，任一条足够）：
1. **它只证"耦合"，不证"断言有效"**——smoke 写 `assert True`，只要 fixture 连不上 broker 就会 error，照样拿到「正向绿 + 反向红」⇒ 判 `verified`。
2. **对 testcontainers / 内嵌 fallback（Go/Node 主流写法）永久误判 vacuous**——`docker compose stop` 对它们毫无影响。
3. **在本 change 自己的接地样本上结构性失效**（对抗镜实证）：mqtt-console 的 `Makefile:11-14` 把**连接参数与依赖启停打包进同一条 recipe 的字面文本**（`MQTT_PORT=1883` 是 shell 前缀赋值，不是 `$(MQTT_PORT)`）⇒ 对任何外部覆盖免疫 ⇒ 隔离式没有注入点、停服务接不上、改 Makefile 被禁止。**三条路全堵死。** 而这种写法**常见且合理**，不是反面案例。

**接地实验（round-2 现场跑，结论入 `references/verification-patterns.md`）**：
- **轮询式连接观测**（`lsof` 轮询进程组的出站连接）——**对瞬时连接漏检率 100%**（5/5 全漏，把真穿过依赖的好 smoke 误判为 vacuous）。**证伪，不可作为判据。**
- **proxy 计数**（占住 smoke 要连的端口、转发到内部端口、数连接）——瞬时连接 **5/5 全中**，零漏检（它在数据必经之路上，不是采样）。**但适用面 ⊆「skill 能控制依赖启动」**，对"依赖内嵌 recipe"同样无效。
- **两者都堵不住 `assert True`**——证明"跟依赖说过话"≠证明"断言有效"。**要堵它只有变异测试（判为太重）⇒ 机械层堵不死，诚实划归冷审语义镜。**

**后果**：negative control **降级为 `references/` 里的一个参考实例**（标注"实例，非规格"），连同它的适用边界与已知盲区一起记。删掉了 `isolate` / `expected-failure predicate` / `kind → 策略 dispatch` / runner 白名单**一整片复杂度**。

### ADR-5：证据只能由执行者本人写（`verified` 不可由模型传入）

**决策**：`set-lane --status verified` **一律拒绝（exit 5）**。两条通道：`executor: script` → `verify-lane`（**脚本自己 fork 执行**）；`executor: human` → `confirm-lane`（**人门写**）。
**理由**：若无脚本亲自执行，实际数据流只能是「模型跑 → 模型读 exit code → 模型调 `set-lane --status verified`」⇒ 脚本对「到底跑没跑、绿没绿」**零独立证据** ⇒「脚本验证」退化为「**模型自称，脚本盖章**」。
**推论**：`evidence` 是冷审「诚实镜」的**唯一接地面**——冷审子代理只能读文件、无法复跑命令，看到 `status: verified` 只能选择相信。

### ADR-6：`lane-patterns` 按依赖形态分格 + 只固化「问什么」

**决策**：按**依赖形态**（外部有状态依赖 / UI / 语言桥 / 真硬件 / 纯计算）分格，**非按语言**；**固化维度与判据，不固化工具选型**。
**备选**：(a) 按语言分格——**否**：泳道结构不由语言决定。(b) 查表式权威规格库——**否**：工具随生态演进、固化即腐烂；模型知识面本就比静态表广（操作者校准：「不宜做太细太明确的限定，让大模型推荐、人做决策」）。
**自验**：mqtt-console = 外部依赖(3) + UI(2) + 语言桥(1) = **6 条泳道**，精确复现其真实泳道列表 ⇒ 模型可被证伪。
**注**：ADR-0 把这条原则**从"泳道设计"推广到了"验证方法"**——前一版只把它用在了前者。

### ADR-7：skill 是追加者，不是拥有者（落地物不设托管块）

**决策**：Makefile / CI / harness / smoke **不设托管区块**；skill 只「登记已有 + 追加缺失」；**重名 fail-closed（只判名字，不判语义）**。
**备选**：给 Makefile 设托管块——**否**：托管块 = 整块替换语义，而 Makefile 是**人机共有的活文件**，整块覆盖会吞掉人的改动。
**关键洞察**：`source` **可以指向人写的行** ⇒ skill 无需拥有 Makefile。
**出处锚 MUST 按内容 digest，MUST NOT 按行号**：`source: "Makefile:11-14"` + 查「那行存不存在」——**对任何长度 ≥14 行的文件恒为真**，是**设计好的假绿**。

### ADR-8：SAD 缺失 → 显式降级，非 fail-closed

**决策**：无 `sad.md` → 响亮警告 + 留痕 `sad: missing` + 继续；MUST NOT 佯装。
**备选**：fail-closed 要求先跑 `/sdflow-architecture`——**否**：会把所有没做过 SAD 的**存量项目**挡在门外（而它们恰恰最需要补测试环境）。
**代价（诚实记录）**：损失 SAD 的两条高价值投影——`§5 contract → 集成测试点`（覆盖对账失效）与 `§3 外边界 → 依赖形态`（泳道设计失去锚）⇒ 告警必须**响亮**。

### ADR-9：归位模式并入同一 skill

**决策**：归位（brownfield）与新建（greenfield）**同一个 skill**，起手分流。
**设计门 Q1 拍定：留在本 change。**
**连带义务**：删源护栏从「工作区干净」升级为**逐文件校验 + 可恢复 backup manifest（入 git）**——**clean worktree 并不足以保护删除**（不保证有效 HEAD / 已 tracked / 非 submodule / 非 symlink）。

### ADR-10：独立 marker `opsx-devenv` + fence-aware

**决策**：用自己的 marker token；**复用 `init.py` 的 token 定位 + 幂等替换语义，但注入实现 MUST 为 fence-aware**。
**理由（代码事实，已核验）**：`init.py:49-52` 的源码注释明确标注：判据**尚非 fence-aware**，会命中代码块内演示的 marker，fence-aware 版本**已 defer**。**直接照抄将继承该缺陷**——而消费仓的 README/CLAUDE 很可能在代码块里演示 marker（本仓自身即是）。
**同款先例**：`ship_gate.py` 的子串检测曾在「讨论 gate 自身」的 change 上假阳，修法即行锚定 + fence-aware + 头部声明区。
**MUST NOT**：写入 `opsx-init` 区块（整块替换 ⇒ 两 skill 互相覆盖）。

### ADR-11：v1 只承诺 POSIX 的进程树杀灭〔round-2〕

**决策**：进程树杀灭（`start_new_session` + `os.killpg`）v1 **只承诺 POSIX**。非 POSIX ⇒ `verify-lane` **显式 refuse**，该泳道走 `executor: human`。
**备选**：(a) 引入 `psutil`——**否**：违反本仓零第三方依赖纪律（`test_anchor_contract.py` 有专门测试断言禁第三方 import）。(b) 写 Windows 的 `taskkill /T /F` 分支——**技术上零依赖可行**（`taskkill` 是系统自带命令），**但我们没有 Windows 环境实测** ⇒ **写一段从未在该平台执行过的代码并声称它能杀进程树，正是本 change 反复批判的"无证据的绿"**。
**后果**：Windows **不是特例**——它命中的就是 `executor: human` 这条通道（与"真硬件"「依赖内嵌 recipe」同类）。**先诚实，再扩面**：挂 todo，实测后升为 `script`。

## Risks / Trade-offs

| # | 风险 | 缓解 |
|---|---|---|
| **R-1** | **模型提的验证方法很弱**（甚至无效），而 skill 按设计不判断质量 | ③-pre 人门**逐条确认验证方法**（含模型自陈的强度与盲区）+ 冷审**验证方法镜**专查"是否名副其实"。**这是有意的设计取舍**（ADR-0）：质量由模型能力 + 人判断保证，不由脚本 |
| **R-2** | **`kind` / `layer` / `covers` 误判**——它们无独立信号，却是机械层的输入 | ③-pre **依赖分类清单必过人门** + 冷审**分类镜**专查。**MUST NOT 佯装机械识别** |
| **R-3** | **永久 `scaffolded`**：渐进 DoD 下无人回来 `continue` | 收尾**MUST 逐条列出** + `blocked_by` 必须含**可操作**修复指引（lint 做最小结构校验）+ **`sdflow-maintain` 每次扫描复述未完成清单**（唯一自动触发点）。**诚实边界：maintain 是人主动跑的 ⇒ 是"更响的提醒"非硬门禁** |
| **R-4** | **人门疲劳**：③-pre 全量倾倒 recipe + smoke ⇒ 橡皮图章 | **呈现分级**：新写的落地物全文展示；**仅登记的既有 target 只展示登记映射**（不要求人重读他自己写的、skill 不会改的代码） |
| **R-5** | **依赖形态五格覆盖不足** | 兜底强制**显式标注「无参考实例，系临场推导」** + 登记 todo；补格由首个撞上的项目驱动 |
| **R-6** | **fence-aware 实现遗漏**：照抄 init.py 将在含 marker 演示代码块的消费仓劫持注入 | ADR-10 明确要求；pytest **必须**覆盖「代码块内有 marker 演示」的用例（本仓自身即此类语料，可 dogfood） |
| **R-7** | **E 编号三投影漂移**：真相源改了但 lint/镜单/人门未同步 | 三处投影带 E 编号引用 ⇒ 一致性**可机械核对** |

## Migration Plan

**部署**：纯增量。新增 `sdflow-devenv/` 顶层目录 → 重跑 `bash setup.sh`。
**跨 skill 改动**（面治，非可选）：`sdflow-init/scripts/init.py`（inject 补锁 + 原子写）· `sdflow-architecture/scripts/sad_scaffold.py`（迁共用锁 + owner 核对 + `atomic_write` 加 mode 参数）· `sdflow-maintain`（新增 devenv 健康度扫描）· 两个 skill 的 description（**双向**分流句）。
**消费仓**：不跑本 skill 则**完全无感**。
**回滚**：`git revert` 本 change + 重跑 `setup.sh`。消费仓侧产物由消费仓自己的 git 管理。
**dev/runtime checkout 纪律**（承 CLAUDE.md adr/0005）：本 change 改 skill 源 ⇒ 须在开发 checkout 跑 `setup.sh` 才测得到。

## Open Questions

| # | 问题 | 处置 |
|---|---|---|
| Q-1 | `lane-patterns` / `verification-patterns` 未覆盖形态何时补格 | v1 走兜底（临场推导 + 显式标注 + todo）；补格由首个撞上的项目驱动 |
| Q-2 | monorepo 多系统演进需 SAD 先支持多系统（`covers` 才锚得住） | v1 单例 + 显式提示；与 SAD 绑定升级 |
| Q-3 | lint「入口复述检测」是弱启发，阈值待接地校准 | 实现期给保守阈值（只在出现**完整命令表**时告警），首跑后校准 |
| Q-4 | `sdflow-maintain` 是人主动跑 ⇒ devenv 健康度只是"更响的提醒"，是否需 `ship_gate` 硬拦截？ | **延后**：首个僵尸 `scaffolded` 出现时再定。**诚实登记：当前无硬门禁** |
| Q-5 | Windows 的 `taskkill /T /F` 分支何时补 | 有 Windows 环境实测后，从 `human` 升为 `script`（ADR-11） |
| Q-6 | SAD 处于 `draft` 态时 contract 随时改名 ⇒ `covers` 锚可能悄悄失真 | **已知局限**：`sad` 字段只有 `present\|missing`，不区分 SAD 生命周期。v1 显式登记，不做三态 |

## Compliance

- **skill 目录约定**：`SKILL.md` + `scripts/` + `references/` + `tests/`，`setup.sh` 自动装载。
- **bundle 权威源纪律**：本 change **不改** `sdflow-init/assets/workflow/`（未新增/修改 spec 工作流规则）⇒ 无需 `sdflow-init update` 回灌。
- **托管区块纪律**：`opsx-devenv` 为新 marker token，**MUST NOT** 写入 `opsx-init` 区块。
- **机械化优先 + 诚实边界**（CLAUDE.md 基准 1 · **本 change 的 ADR-0**）：能机械化的一律机械化（证据落盘 / digest 锚 / `owned_by` 派生 / 三层框架完整性 / 状态迁移）；**机械够不着的诚实划归语义层，MUST NOT 硬凑假机械**。
- **面治优先于点补**（基准 3）：撞到的相邻漏网格一次扫全——`init.py` 补锁、`sad_scaffold` 迁锁 + `atomic_write` 加 mode、双向分流句，均在本 change 内做掉。
- **目标态导向**（基准 2）：三层框架锚目标态（该有哪些层），**MUST NOT** 以「现存项目大多只有单元测试」论证「e2e 层可省」——省了就 `不适用 + 后果`，而不是不问。
- **一个 change 一个完整阶段结果**（基准 4）：本 change = 一个完整可用的 skill。
- **HR-TG**：命中 TG-08 / TG-09 / TG-17 / TG-26 ⇒ spec-review **单开领域 cross-model**。
- **测试纪律**：改 `scripts/` 必跑 `tests/`（本仓强制）。
