# design — add-sdflow-devenv

> 设计源：`docs/sad/07-devenv-skill-design.md`（九条设计点逐条拍定）· 接地证据：`docs/sad/06-process-axis-grounding-receipt.md`
> 命中 TG：05 · 08 · 09 · 10 · 11 · 12 · 13 · 14 · 15 · 17 · 18 · 19 · 21 · 22 · 23 · 25 · 26（HR-TG：08 / 09 / 17 / 26）

---

## ⚠️ spec-review 修订摘要（2026-07-13 · 设计门拍板后）

> **四声（CEO×2 + Eng×2，零 DISAGREE）判定：三根承重柱空心。以下决策已被推翻或重写——正文中被推翻的段落保留为考古层，其结论以本节与 `specs/` 为准。**
> 完整 findings 见 `gstack-review.md`；裁决与拍板记录见 `spec-review-report.md`。

| 原决策 | 状态 | 新结论（真相源 = `specs/`） |
|---|---|---|
| **ADR-4**：negative control 为 `verified` 的 ⟺ **定义** | ❌ **推翻**（Q3） | **降为强信号**。它只证「命令**耦合**依赖」，不证「断言有效」（`assert True` 照样正绿反红）；对 testcontainers / 内嵌 fallback（**主流写法**）永久误判。改为：独立字段 `neg_control` · 仅对抽离机制已定义的依赖类生效 · 必须匹配 expected-failure predicate。**并行强制**新机械门槛：解析 `go test -json` / pytest `collected N`，断言「至少跑了 ≥1 个测试且 0 skipped」 → `spec.md` R「negative control 是强信号而非定义」 |
| **组件清单**：`devenv_scaffold` 子命令 = init/set-lane/render/inject/log/doctor-gen | ❌ **致命缺失**（ENG-1） | **没有一个子命令会执行 smoke** ⇒ `verified` 实为「模型自称、脚本盖章」。**新增 `verify-lane` 子命令**（脚本自己 fork 正/反两跑 + 原子写执行证据）；**`set-lane --status verified` 一律拒绝**（exit 5） → `spec.md` R「`verified` 由脚本亲自执行并落执行证据」 |
| **数据模型**：`lanes[]` 存 `environments.md` frontmatter（嵌套 YAML） | ❌ **无解析方案**（ENG-5 · Q4） | 目标环境**无 PyYAML**，本仓唯一先例只支持扁平标量。**改落 `.devenv-lanes.json`**（标准库、零依赖）；frontmatter 只留 `sad`/`mode`/**`schema_version`** 三个扁平标量 |
| **数据模型**：`deps: [<name>]` 裸字符串 · lane 无 `kind` | ❌ **推翻**（ENG-2） | 无类型 ⇒ negative control 无从机械分派；无 `kind` ⇒「真硬件不执行」无从机械识别。**`deps` 升为结构化描述符**（`kind`/`up`/`down`/`owned_by`/`isolate`）+ **lane 加 `kind`** |
| **ADR-5 / lint ①**：`source: "Makefile:11-14"` + 查「那行存不存在」 | ❌ **恒真断言**（ENG-4） | 「第 11-14 行存不存在」**对任何长度 ≥14 行的文件恒为真** = 设计好的假绿。**改内容 digest 锚**（`{file, kind, selector, digest}`），行号仅供阅读、不作真相 |
| **ADR-10**：「复用 `sad_scaffold` 已验证模式」 | ⚠️ **不充分**（ENG-6/ENG-10） | ① **互斥性不可组合**——devenv 的锁挡不住 `sdflow-init`（不同锁名，且 `init.py` 的 inject 是**裸 `open(w)` 无锁无原子写**）⇒ 锁提升为 **`openspec/` 写域单一锁**，三 skill 共用；**顺带给 `init.py` 补锁 + 原子写**（面治优先于点补）② **锁参数与长跑 smoke 冲突**（`STALE=120s`，smoke 可跑数分钟 ⇒ 活锁被判残留锁 ⇒ 提示删锁 ⇒ 两 session 同写）⇒ 锁**短持有** + **CAS**（`--expect`）③ `chmod 0o644` ⇒ 生成的 doctor/broker 脚本**落盘即不可执行** ⇒ `atomic_write` 加 mode 参数 |
| **失败模式表（11 条）** | ❌ **漏最危险的一条**（ENG-3，CRITICAL） | **无一条要求「恢复被抽离的依赖」**——超时/崩溃/Ctrl-C ⇒ 用户的 broker 永久停在停止态。且原设计只禁「装依赖」（**加法**）不禁「停服务」（**减法，更破坏性**）。**新红线**：只能停 `owned_by: skill` 的依赖 · **首选隔离式抽离**（endpoint 指向不可达地址，副作用为零）· `try/finally` 恢复 · **超时杀进程树 + cleanup ledger** → `spec.md` R「执行边界与『不伤害』红线」 |
| **人门 diff 位置**（议程 ④，执行之后） | ❌ **推翻**（ENG-7） | **模型生成的代码在任何人看过之前就已被执行**。**diff 门移到 ③-pre（执行之前）**，且 MUST 展开 recipe body 与 smoke 全文（原先给人看的 `make integration` 一行**零信息量**）；补「否决 → 回退」路径 |
| **安全节**：「不外发 ⇒ 无 secret 出境面」 | ❌ **结论错误**（ENG-12） | 漏了 **ingress → git**：命令继承 agent session 的**完整环境变量**，失败回显（`AMQP_URL=...:pass@...`）写进 `blocked_by`/`devenv-log` → **commit → push**。**不主动外发，但把 secret 写进了必然被外发的载体** ⇒ 输出捕获 MUST 截断 + 过 secret 正则 + MUST NOT dump 环境变量 |
| **lint 的触发点** | ❌ **完全缺失**（CEO-2，CRITICAL · Q6) | 「无门禁」是立项理由之一，而 `devenv_lint` **自己也没有触发点** ⇒ **dogfood 自指坑**；且它是「渐进 DoD」防僵尸的**唯一解药**。**挂进 `sdflow-maintain` 扫描** → `specs/maintain-scan/spec.md`（新增 capability delta）。**诚实边界**：maintain 人主动跑 ⇒ 是「更响的提醒」非硬门禁 |
| **ADR-9**：归位模式并入同一 skill | ✅ **维持**（设计门 Q1 推翻推荐） | 操作者拍定**留在同一 change**。**连带义务**：删源护栏从「工作区干净」升级为**逐文件前置校验**（HEAD 有效 / 已 tracked / 非 submodule / 非 symlink / digest 与人门确认时一致）+ **可恢复 backup manifest**——`clean worktree` **不足以**保护删除 |
| **ADR-1**：编排器路线 | ✅ **维持**（Q5=B），但**如实记天花板** | 未重开 ADR。但 proposal MUST 写明：greenfield 能问出来的**不含** `06` 认定的全部价值（坑/护栏/盲区 day-0 问不出来）；且**已修掉两条伪证据**（「命令虚构是实测」实为**零虚构**；「88% 全是待决策项」被 `06` 三分法证伪） |
| **实现前置（新增）** | ➕ **Q2** | **先跑 `sdflow-architecture` 的首个真实试点**（用同一个绿地项目）——它是上游 hand-off 自己写下的最高优先 next action，至今未做。一个项目的成本，同时验证：真实 SAD 能否长出 devenv 的锚 · greenfield 的虚构风险是否真实 · `lane-patterns` 五格在第二个样本上是否成立 |

**ADR-2（全直写）· ADR-3（渐进 DoD）· ADR-6（依赖形态分格）· ADR-7（fence-aware）· ADR-8（SAD 缺失降级）维持不变**（ADR-7 另需扩测 CommonMark fence 变体：`~~~` / 四 backtick / 缩进 fence / 孤儿 / 逆序）。

## Context

生态里「技术架构定了之后把 dev/test 环境真正建起来」无 skill 覆盖：`sdflow-architecture` 交棒止于「过程轴文档指路（指出不代写）」，下游为空；`sdflow-init` 铺的是 **workflow 的运行环境**（规则 bundle），按定义不管项目内容。

mqtt-console 接地实测（`06`）给出三条硬事实，直接约束本设计：

1. **SAD 投影率仅 12%（严）/ 41%（宽）**——「从 SAD 生成文档」这条腿不成立；但那 88% 恰恰**全是待决策项** ⇒ 需要的是**编排器**（问 / 拍 / 留痕），不是生成器。
2. **真正的机械投影源是构建配置**（Makefile / package.json），不是 SAD ⇒ 命令表可对构建配置核验、甚至渲染。
3. **纯文档型产物会虚构命令**（为对齐模板范式编造 `make dev/test/build`）⇒ 本 skill 亲手写 Makefile，命令天然为真。

**现状约束**：`sdflow-architecture` 已确立 recorder 式直写 + 双脚本（scaffold 写 / lint 读）+ fresh 子代理冷审 + 人门的骨架，本 skill 与之**对称**（空间轴 ↔ 过程轴），复用其已验证的机械层模式。

## Goals / Non-Goals

**Goals:**

- 把 dev/test 环境**真正建起来**：决策 → 落地物（Makefile / broker / CI / harness / smoke / doctor）→ 跑通 → 两份真相源 + 入口索引。
- **渐进 DoD**：泳道逐条推进，不强制全绿；但**诚实是硬要求**。
- `verified` 有**可执行的判定**（negative control），不靠模型自称。
- 与既有生态**零冲突**：独立 marker、不改 `sdflow-init`、真硬件复用 `embedded-test-sop`。

**Non-Goals:**

- 业务测试用例（归各 change）· 生产 runbook · 替用户装系统依赖 · smoke debug 到通 · monorepo 多系统（v1）· 时间轴排期 · 从 SAD 自动生成文档。

## 组件清单〔TG-13/14〕

| 组件 | 职责 | 类型 |
|---|---|---|
| `SKILL.md` | 五步编排 · 三模式分流 · 时序纪律 · 人门议程 | Markdown（模型消费） |
| `scripts/devenv_scaffold.py` | **写**：`init`（preflight+分流）· `set-lane` · `render` · `inject` · `log` · `doctor-gen` | Python |
| `scripts/devenv_lint.py` | **读**：五条机械检查 + 按泳道状态分档核验 | Python |
| `scripts/devenv_schema.py` | frontmatter schema 定义与校验（两脚本共用，防口径漂移） | Python |
| `references/lane-patterns.md` | 依赖形态四问 + 阶梯判据 + 参考实例（**非规格**） | Markdown |
| `references/boundary-rules.md` | 切线表 + 归属判据（归位模式判每节归哪个格） | Markdown |
| `references/environments-template.md` | 十六槽 | Markdown |
| `references/testing-strategy-template.md` | 九槽 | Markdown |
| `references/quality-criteria.md` | **E1–E11 真相源**（三处投影的唯一源） | Markdown |
| `references/review-lenses.md` | 冷审镜单（E 编号投影） | Markdown |
| `tests/` | pytest（本仓纪律：改 `scripts/` 必跑 `tests/`） | Python |

## C4 Context + Container〔TG-13〕

```
┌─────────────────────────────────────────── Context ───────────────────────────────────────────┐
│                                                                                                │
│   操作者(人) ──触发/拍板/人门──▶ ┌──────────────────┐                                          │
│                                  │  sdflow-devenv   │                                          │
│   sdflow-architecture ──交棒──▶  │   (本 skill)     │ ──读──▶ SAD (openspec/architecture/sad.md)│
│   (SAD §2/§3/§5/§7/§8 锚)        │                  │ ──写──▶ 消费仓落地物 + 真相源 + 入口      │
│                                  └────────┬─────────┘                                          │
│   sdflow-init ──前置(布局)──▶             │ 派                                                 │
│   embedded-test-sop ◀──指向(真硬件)──     │                                                    │
│                                           ▼                                                    │
│                                    fresh 冷审子代理                                            │
└────────────────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────── Container (消费仓视角) ──────────────────────────────────────┐
│                                                                                                │
│  openspec/architecture/          项目各处(落地物)              入口(托管块)                     │
│  ├─ sad.md          (读)         ├─ Makefile      (追加)      ├─ CLAUDE.md   ┐                 │
│  ├─ environments.md (写:渲染)    ├─ compose/hack/ (追加)      ├─ AGENTS.md   ├ opsx-devenv     │
│  ├─ testing-strategy.md (写)     ├─ CI 配置       (追加:壳)   ├─ README.md   ┘                 │
│  └─ devenv-log.md   (写:append)  ├─ test harness  (追加)      └─ openspec/INDEX.md             │
│                                  ├─ smoke × N     (追加/登记)                                   │
│  frontmatter = 泳道单一真相源     └─ doctor        (追加)                                       │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 数据模型与生命周期〔TG-05〕

**唯一机械真相源 = `environments.md` frontmatter**。正文命令表由 `render` 生成（`DO NOT EDIT` banner），**不双写**。

```yaml
---
sad: present | missing            # 降级留痕；missing ⇒ covers 对账跳过并告警
mode: greenfield | brownfield     # 首次分流结果（供 continue 复用）
lanes:
  - id: <slug>                    # 唯一；kebab-case
    status: planned | scaffolded | verified
    command: <string>             # planned 态可为空
    source: <path:line-range> | <string> | planned   # verified 态必须指向真实存在的行
    smoke: <path>                 # scaffolded/verified 必填；文件必须存在
    deps: [<name>...]             # 外部依赖；[] ⇒ 豁免 negative control
    covers: [<SAD contract 锚>...] # E2 对账用；sad: missing 时可空
    blocked_by: <string>          # scaffolded 态 MUST 非空
---
```

**字段的生命周期**（谁在哪一步写）：

| 字段 | 写入步 | 写入者 |
|---|---|---|
| `sad` / `mode` | 起手 A | `init`（脚本，机械） |
| `id` / `covers` / `deps` | ② 泳道拍板 | `set-lane`（人拍板后） |
| `command` / `source` / `smoke` | ③ 落地 | `set-lane`（登记已有 或 追加新写后） |
| `status` / `blocked_by` | ③ 真跑后 | `set-lane`（**脚本执行结果驱动**，非模型自称） |

## 状态机图〔TG-09〕

```
                    ┌──────────────────────────────────────────────┐
                    │                                              │
     ②拍板          ▼            ③落地+真跑                        │ 环境变更失效
   ────────▶ ┌──────────┐  smoke已写  ┌─────────────┐  双向判据成立 │  (依赖升级破坏)
             │ planned  │───────────▶ │ scaffolded  │──────────────┼──▶ ┌──────────┐
             └──────────┘             └─────────────┘              │    │ verified │
                  ▲                     │        ▲                 └────└──────────┘
                  │                     │        │                          │
                  │ 操作者指定跳过       │        │ continue 推进            │
                  └─────────────────────┘        │ (装完依赖/修完 smoke)    │
                                                 └──────────────────────────┘

  合法迁移（表外一律拒绝，只由 set-lane 执行；模型/人 MUST NOT 手改 frontmatter 跳级）：
  ─────────────────────────────────────────────────────────────────────────────────
  — → planned          ②拍板后
  planned → scaffolded  smoke 文件存在 ∧ blocked_by 非空
  scaffolded → verified 【双向判据】依赖就绪时绿 ∧ 抽掉依赖时红   ← 脚本执行验证
                        (deps: [] 豁免第二条，退回「含断言语句」最低门槛)
                        ∧ source 指向行存在
  verified → scaffolded 【回落】环境变更导致失效，blocked_by 必须写明原因

  异常转换（fail-closed）：
  ─────────────────────────────────────────────────────────────────────────────────
  scaffolded 且 blocked_by 为空          → lint 拒绝（诚实硬要求）
  抽掉依赖仍绿(vacuous)                  → 拒绝置 verified，记 blocked_by="smoke 未穿过依赖"
  smoke 超时                             → scaffolded + blocked_by="超时，未确认环境问题还是 smoke 挂了"
  真硬件泳道                             → 直接 scaffolded（不尝试执行）+ 指向 embedded-test-sop
```

## 三模式分流决策图〔TG-12〕

```
                        触发 /sdflow-devenv
                               │
                               ▼
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
              (跳到③推进泳道)   (重走②)      ┌────┴────┐
                                            ▼         ▼
                                          有        没有
                                            │         │
                                            ▼         ▼
                                    ┌──────────┐ ┌──────────┐
                                    │ 归位模式  │ │ 新建模式 │
                                    │ ①'盘点   │ │ ①事实采集│
                                    │ 判归属    │ │          │
                                    │ 搬运表人门│ │          │
                                    └────┬─────┘ └────┬─────┘
                                         └──────┬─────┘
                                                ▼
                                      ②泳道拍板 → ③落地+真跑
                                      → ④冷审+人门 → ⑤文档+入口

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
                 │              │              │
                 └──────────────┴──────────────┘
                                ▼
                    删源(git 前置: 工作区必须干净)
                                ▼
                    扫残留引用(含代码注释!)  ← lint 检查③
```

## 关键时序〔TG-10〕

```
操作者        主 session(强档)      devenv_scaffold      冷审子代理(fresh)     消费仓
  │                 │                    │                     │                │
  │  /sdflow-devenv │                    │                     │                │
  ├────────────────▶│   init             │                     │                │
  │                 ├───────────────────▶│  preflight+分流     │                │
  │                 │◀───────────────────┤  exit code          │                │
  │   事实复核/提问  │                    │                     │                │
  │◀───────────────▶│                    │                     │                │
  │  泳道候选(选)    │                    │                     │                │
  │◀───────────────▶│  set-lane(planned) │                     │                │
  │                 ├───────────────────▶│─────── 持锁+原子写 ─────────────────▶│
  │  「将执行这些命令」                   │                     │                │
  │◀────────────────┤                    │                     │                │
  │  同意           │                    │                     │                │
  ├────────────────▶│  写落地物(追加)     │                     │                │
  │                 ├────────────────────────────────────────────────────────────▶│
  │                 │  跑 smoke (正向)    │                     │                │
  │                 ├────────────────────────────────────────────────────────────▶│
  │                 │  跑 smoke (抽依赖)  │  ◀── negative control                 │
  │                 ├────────────────────────────────────────────────────────────▶│
  │                 │  set-lane(verified/scaffolded+blocked_by) │                │
  │                 ├───────────────────▶│                     │                │
  │                 │  派冷审(禁自查)     │                     │                │
  │                 ├──────────────────────────────────────────▶│  读产物        │
  │                 │                    │                     ├───────────────▶│
  │                 │◀─────────────────────────────────────────┤  镜单发现       │
  │  人门(4 议程,含 diff 过目)            │                     │                │
  │◀───────────────▶│                    │                     │                │
  │                 │  render + inject   │                     │                │
  │                 ├───────────────────▶│─────── 持锁+原子写 ─────────────────▶│
  │  收尾: 逐条列出未 verified 泳道       │                     │                │
  │◀────────────────┤                    │                     │                │
```

## 并发与共享状态访问策略〔TG-26 · HR〕

**风险为已证实而非推测**：`sdflow-architecture` 的多镜 code-review 在同款场景抓出 **5 个 CRITICAL 并发缺陷**，最终以 exclusive-create lock 修复。本 skill 同样对 `openspec/architecture/` 下三个文件做读-改-写，**两个 session 并发跑必然撞车**。故并发安全**从设计期内建，MUST NOT 后补**（proposal 假设 A-4）。

**策略 = 直接复用 `sad_scaffold.py` 已验证的模式**（核验自 `sdflow-architecture/scripts/sad_scaffold.py`）：

| 机制 | 实现（照抄已验证模式，不自创） |
|---|---|
| **仓级写互斥锁** | `os.open(lockp, O_CREAT\|O_EXCL\|O_WRONLY, 0o644)`——**跨平台，不用 `fcntl`**；锁文件 `openspec/.devenv-scaffold.lock` |
| **陈旧锁检测** | 比对 `lockp.stat().st_mtime` 年龄，超阈值提示「若确认无并发进程，删除锁文件后重试」，**不静默夺锁** |
| **原子写** | `tempfile.mkstemp(dir=同目录)` → 写 → `os.chmod(0o644)`（mkstemp 默认 0600）→ `os.replace()`。**tmp 名必须唯一化**——固定名会并发撞车（`sad_scaffold` 的 B8 修复即此） |
| **锁作用域** | contextmanager 包裹**整个读-改-写序列**，MUST NOT 只包 write |
| **append-only log** | `devenv-log.md` 仅追加；`--line` 含换行符 → 坏输入退出码拒绝（防伪造审计行） |

**MUST NOT**：以「读入内存 → 改 → 覆写」的裸序列写任何产物文件。

## 失败模式表〔TG-08 · HR〕

skill 执行外部命令（`make` / `go test` / `npm` / `docker` / `git`），失败面丰富：

| # | 失败模式 | 检测 | 处理 | 状态后果 |
|---|---|---|---|---|
| F1 | 依赖缺失（无 mosquitto / 无 Docker） | 命令非零退出 + stderr 特征 | 如实记 `blocked_by`（差什么 + 怎么装 + 怎么 continue） | `scaffolded` |
| F2 | smoke 超时 | 超时阈值 | `blocked_by` 写明「超时，未确认是环境问题还是 smoke 本身挂了」——**不臆断归因** | `scaffolded` |
| F3 | **vacuous smoke**（抽掉依赖仍绿） | negative control | 拒绝置 `verified`，`blocked_by="smoke 未穿过依赖"` | `scaffolded` |
| F4 | smoke 本身有 bug（正向就红） | 命令非零退出 | 记 `blocked_by` + 报错摘要，**MUST NOT 进 debug 循环** | `scaffolded` |
| F5 | Makefile target 重名且语义不符 | 追加前扫描已有 target 名 | **fail-closed** 报冲突，留人裁决 | 中止该泳道 |
| F6 | 端口占用 / 容器启动失败 | 命令非零退出 | 记 `blocked_by`，提示可能的端口冲突 | `scaffolded` |
| F7 | `source` 指向行失效（人改了 Makefile） | lint 检查① | lint fail-closed 报出该泳道 | 需 continue 重登记 |
| F8 | 冷审子代理无产出 | 无镜单结果 | **重派一次**；再失败**显式报告缺口**，MUST NOT 无冷审静默过人门 | 阻塞人门 |
| F9 | 宿主无 fresh 子代理原语（Codex） | 能力探测 | **显式降级 + 响亮留痕**，MUST NOT 佯装冷审 | 降级标记 |
| F10 | 并发锁被占 | `O_EXCL` 失败 | 陈旧则提示删锁重试；否则拒绝本次写 | 中止写 |
| F11 | 删源时工作区不干净 | `git status` 非空 | **fail-closed**，提示先 commit/stash | 中止删源 |

**统一纪律**：失败**一律如实记录，MUST NOT 静默、MUST NOT 重试到通、MUST NOT 臆断归因**。「跑不绿」是合法状态。

## 可观测性〔TG-08 / TG-15〕

| 面 | 载体 | 内容 |
|---|---|---|
| **审计留痕** | `devenv-log.md`（append-only） | 模式分流 · 泳道状态迁移（含**执行者字段**：脚本验证 vs 人工指定）· SAD 降级 · 冷审轮次与执行者（fresh-subagent vs 降级 main-session）· 人门通过 · 删源清单 |
| **断点恢复** | 同上 | `continue` 靠它定位断点（候选只活在对话里，session 断即丢） |
| **当前态** | `environments.md` frontmatter | 泳道状态全景（机器可读） |
| **对话可见** | 收尾报告 | **逐条列出**未 `verified` 泳道 + `blocked_by`——**MUST NOT 只埋进文件** |
| **诚实码** | lint 退出码/通过码 | `structure-ok-SEMANTICS-UNCHECKED`：结构通过 ≠ 内容已审 |

## 安全与数据保护〔TG-17 · HR〕

本 skill 有两个高危操作面，均需显式护栏：

| 面 | 风险 | 护栏 |
|---|---|---|
| **执行任意 shell 命令**（`make` / `docker` / 测试命令） | 命令来自 Makefile（人写）或 skill 追加；可能起容器、占端口、写文件 | ① **跑前列出命令给操作者过目**，不偷跑 ② 每条有超时 ③ **MUST NOT 替操作者装系统依赖**（`brew install` / `docker pull` 副作用不可逆） |
| **删除用户文件**（归位模式） | 误删不可逆 | ① **fail-closed 要求工作区干净**（否则 `git revert` 会波及操作者其他改动，「可回滚」不成立）② 搬运表**显著呈现**「以下 N 个文件将被删除」③ **人门确认后**才删 ④ `grep` 引用面给判据（引用面广 → 降为指针而非删）⑤ MUST NOT 静默删 |
| **写真代码进仓** | 引入不可信内容 | 人门议程含 **diff 过目**（最后一道人类护栏） |

**敏感数据**：本 skill **不外发任何内容**（冷审子代理为本地 Agent，无 outside-voice / 无跨模型出境）⇒ 无 secret 出境面。生成的示例/fixture **SHALL 用占位符**（`<mqtt-host>` / `<device-id>`），MUST NOT 写入真实凭证。

## 协议文档套件 scope-check 表〔TG-25〕

**`quality-criteria.md`（E1–E11）是唯一真相源，三处投影**——改一处牵连一组，故需 scope-check：

| 真相源 | 投影 1（机械） | 投影 2（语义） | 投影 3（价值） |
|---|---|---|---|
| `references/quality-criteria.md`<br>E1–E11 + 拆解表 | `scripts/devenv_lint.py`<br>（「可结构化」列） | `references/review-lenses.md`<br>（「语义残余」列） | `SKILL.md` 人门议程<br>（价值类残余） |

**一致性纪律**（承 `sdflow-architecture` §6.2 同款）：三处投影 **SHALL 带 E 编号引用**（脚本注释 / 镜单条目 / 议程条目）⇒「投影与真相源一致」本身**可机械核对**，防三处各自漂移。

| 改动 | 必须同步检查 |
|---|---|
| 新增/修改 E 条目 | 三处投影是否都需更新？（可结构化列 → lint；语义残余列 → 镜单；价值类 → 人门） |
| lint 新增断言 | 是否对应某个 E 编号？无对应 ⇒ 要么补 E 条目，要么该断言不该存在 |
| 镜单新增一镜 | 是否对应某个 E 的语义残余？ |

## Decisions〔TG-23〕

### ADR-1：编排器，不是生成器（推翻 `05` §5「D 不立」）

**决策**：立 skill，但其本质是**编排器**（问 / 拍 / 落地 / 验 / 留痕），不是「从 SAD 生成文档」的生成器。
**备选**：(a) 不立 skill，用「模板 + 手跑 prompt」（`05` 的 C）——**否**：拿不到 lint / 冷审 / 托管注入 / 真跑，正是要做 skill 的四条理由全落空。(b) 并入 `sdflow-init`（`05` 的 B）——**否**：init 按定义只管 workflow 运行环境，不管项目内容。
**后果**：`05` §5 的候选表被证明定义过窄（把 skill 等同于生成器）；88% 纯人写不是「生成价值低」，而是「88% 全是待决策项 ⇒ 正需要编排器」。

### ADR-2：全直写，不走 change 壳

**决策**：文档与脚手架**都直落盘**，质量门内建（lint + smoke 真跑 + 冷审 + 人门 diff）。
**备选**：走 openspec change 壳——**否**：**鸡生蛋**（该 change 自己的测试要靠这套环境才能跑）；且 env 文档是 live 单例（会反复重入更新），套 change 壳会反复开壳。
**先例**：`sdflow-architecture` 规则 4 / `sdflow-roadmap`（recorder 式直写）。

### ADR-3：泳道三态 + 渐进 DoD（非一次性全绿）

**决策**：`planned → scaffolded → verified` 逐条推进，**不强制全绿**；诚实为硬要求（`scaffolded` MUST 带非空 `blocked_by`）。
**备选**：一次性 fail-closed 全绿 DoD——**否**：项目初期定不下所有事（操作者原话：「有个方向和基本能力就行」）；本机缺依赖不是失败。
**后果**：fail-closed 的落点从「完成度」移到「诚实度」——跑不绿合法，**跑不绿却装作跑得绿**不合法。风险见 R-3（永久 scaffolded）。

### ADR-4：negative control 作为 `verified` 判据（非变异测试）

**决策**：`verified ⟺ 依赖就绪时绿 ∧ 抽掉依赖时红`。
**备选**：(a) 只要求「跑绿」——**否**：vacuous smoke（跑绿但没穿过依赖）是本 skill 头号假绿风险，「环境建好了」的全部证据就是它。(b) 变异测试（删被测逻辑看红不红）——**否**：太重（改代码 + 跑两遍全量）。
**理由**：negative control 提供**同等强度的「能因缺失而红」证据**，但**近乎免费**（不改代码，只是不启动依赖再跑一遍，且失败很快）。
**边界**：`deps: []` 豁免（无「假装穿过」的空间），退回「含断言语句」最低门槛 + 冷审。
**残余**：**语义恒真**（如 MQTT `CleanSession=1` ⇒ CONNACK 恒 `SessionPresent=0`，断言恒真）机械绝无可能抓到 ⇒ 冷审专职一镜，该真案例挂进镜单当范例。

### ADR-5：skill 是追加者，不是拥有者（落地物不设托管块）

**决策**：Makefile / CI / harness / smoke **不设托管区块**；skill 只「登记已有 + 追加缺失」；重名 fail-closed。
**备选**：给 Makefile 设 `opsx-devenv` 托管块——**否**：托管块 = 整块替换语义，而 Makefile 是**人机共有的活文件**（人随时改 target 实现），整块覆盖会吞掉人的改动。
**关键洞察**：frontmatter 的 `source` **可以指向人写的行** ⇒ skill 无需拥有 Makefile；lint 只查「那行存不存在」，不关心谁写的。
**推论**：归位模式的 smoke **复用已有测试**（`smoke:` 指过去），不新写冗余。

### ADR-6：`lane-patterns` 按依赖形态分格 + 只固化「问什么」

**决策**：按**依赖形态**（外部有状态依赖 / UI / 语言桥 / 真硬件 / 纯计算）分格，**非按语言**；**固化维度与判据，不固化工具选型**。
**备选**：(a) 按语言分格——**否**：泳道结构不由语言决定（同是 Go，连 broker 的服务与纯算法库泳道完全不同；Go 服务与 Java 服务连同一 broker 则几乎一样）。(b) 查表式权威规格库（每栈一套完整规格 + 工具选型）——**否**：工具随生态演进、固化即腐烂；且模型知识面本就比静态表广（操作者校准：「不宜做太细太明确的限定，让大模型推荐、人做决策」）。
**自验**：mqtt-console = 外部依赖(3) + UI(2) + 语言桥(1) = **6 条泳道**，精确复现其真实泳道列表 ⇒ 模型可被证伪。
**兜底**：未覆盖形态 → 临场推导 + **显式标注「无参考实例」** + 登记 todo，MUST NOT 凭空编造权威候选。

### ADR-7：独立 marker `opsx-devenv` + **实现 fence-aware（不继承 init.py 的已知缺陷）**

**决策**：用自己的 marker token；**复用 `init.py` 的 token 定位 + 幂等替换语义，但注入实现 MUST 为 fence-aware**。
**理由（代码事实，已核验）**：`sdflow-init/scripts/init.py` 的 `inject()` 在源码注释里明确标注（T21）：判据**尚非 fence-aware**，会命中 ``` 代码块内演示的 marker，fence-aware 版本**已 defer**。**直接照抄将继承该缺陷**——而消费仓的 README/CLAUDE 很可能在代码块里演示 marker（本仓自身即是此类文档仓）。
**同款先例**：`ship_gate.py` 的子串检测曾在「讨论 gate 自身」的 change 上假阳，修法即**行锚定 + fence-aware + 头部声明区**。
**MUST NOT**：写入 `opsx-init` 区块（整块替换语义 ⇒ 两 skill 互相覆盖）。

### ADR-8：SAD 缺失 → 显式降级，非 fail-closed

**决策**：无 `sad.md` → 响亮警告 + frontmatter 留痕 `sad: missing` + 继续；MUST NOT 佯装。
**备选**：fail-closed 要求先跑 `/sdflow-architecture`——**否**：会把所有没做过 SAD 的**存量项目**挡在门外（而它们恰恰最需要补测试环境）。
**代价（诚实记录）**：损失 SAD 的**两条高价值投影**——`§5 contract → 集成测试点`（E2 覆盖对账失效）与 `§3 外边界 → 依赖形态`（泳道设计失去锚）⇒ 告警必须**响亮**，不是走过场。

### ADR-9：归位模式并入同一 skill

**决策**：归位（brownfield）与新建（greenfield）**同一个 skill**，起手分流。
**备选**：拆两个 skill / 归位留作手跑 prompt——**否**：归位模式的后半段（补泳道、落脚手架、跑 smoke、出文档、注入入口）与新建**完全共用**，独有的只是前面一段「盘点 + 判归属 + 删源」；为一段前置拆两个 skill 不划算。
**后果**：SKILL.md 变长，且两条路**纪律不同**（新建防「虚构命令」，归位防「只建不删源」）——须在 SKILL.md 显式分述。

### ADR-10：并发安全复用 `sad_scaffold` 已验证模式

**决策**：仓级 `O_CREAT|O_EXCL` 锁（跨平台，不用 `fcntl`）+ `mkstemp` 唯一 tmp 名 + `os.replace` 原子写 + 陈旧锁检测。
**备选**：自创锁方案 / 不加锁——**否**：`sdflow-architecture` code-review 已在同款场景抓出 5 个 CRITICAL 并发缺陷；重犯同一错误不可接受。
**纪律**：锁作用域包裹**整个读-改-写序列**，MUST NOT 只包 write。

## Risks / Trade-offs

| # | 风险 | 缓解 |
|---|---|---|
| **R-1** | **negative control 误判**：若某依赖有「优雅降级」路径（缺失时 fallback 而非报错），smoke 抽掉依赖仍绿 → 好泳道被误判 vacuous、卡在 `scaffolded` | `deps: []` 显式豁免通道 + 冷审复核；`blocked_by` 如实写「疑似优雅降级，negative control 不适用」留人裁决。**宁可误报不可漏报**——漏报=假绿 |
| **R-2** | **依赖形态五格覆盖不足**：大量项目落到未覆盖形态 ⇒ 退化为纯临场推导，枚举完备性丧失、两次运行推荐面不一致 | 兜底流程强制**显式标注「无参考实例」** + 登记 todo；补格由首个撞上的项目驱动（Q-1） |
| **R-3** | **永久 `scaffolded`**：渐进 DoD 下无人回来 `continue`，环境名存实亡（「一条 verified + 五条 scaffolded」长期挂着） | 收尾**MUST 逐条列出**未 verified 泳道（不许埋进文件）；`blocked_by` 必须含**可操作**的修复指引；lint 每次跑都复述未完成清单 |
| **R-4** | **fence-aware 实现遗漏**：若照抄 init.py 的 inject，将在含 marker 演示代码块的消费仓劫持注入 | ADR-7 明确要求 fence-aware；pytest **必须**覆盖「代码块内有 marker 演示」的用例（本仓自身即此类语料，可 dogfood） |
| **R-5** | **归位模式登记错位**：已有 Makefile target 语义模糊（一个 `test` 跑了三条泳道）→ `covers` 对账失真 | 登记结果进**搬运表人门**，由操作者确认；模糊者宁可标 `planned` 不强行登记 |
| **R-6** | **E 编号三投影漂移**：真相源改了但 lint/镜单/人门未同步 | scope-check 表（TG-25 节）+ 三处投影带 E 编号引用 ⇒ 一致性**可机械核对** |
| **R-7** | **skill 执行任意命令的信任面** | 跑前列命令过目 + 超时 + 不装依赖 + 人门 diff（TG-17 节） |

## Migration Plan

**部署**：纯增量。新增 `sdflow-devenv/` 顶层目录 → 重跑 `bash setup.sh`（建 symlink）；改 `sdflow-architecture/SKILL.md`（交棒话术 + description）；改 `README.md`（Skills 列表）。
**消费仓**：不跑本 skill 则**完全无感**（无任何文件变动）。
**回滚**：`git revert` 本 change + 重跑 `setup.sh` 清理孤儿链接。消费仓侧产物（`environments.md` 等）由消费仓自己的 git 管理，回滚互不影响。
**dev/runtime checkout 纪律**（承 CLAUDE.md adr/0005）：本 change 改 skill 源 ⇒ 须在开发 checkout 跑 `setup.sh` 才测得到；合并后在运行 checkout 重跑 setup 还原。

## Open Questions

| # | 问题 | 处置 |
|---|---|---|
| Q-1 | `lane-patterns` 未覆盖形态（Java / 移动 / 分布式）何时补格 | v1 走兜底（临场推导 + todo）；补格由首个撞上的项目驱动 |
| Q-2 | monorepo 多系统演进需 SAD 先支持多系统（`covers` 才锚得住） | v1 单例 + 显式提示；与 SAD 绑定升级 |
| Q-3 | lint「入口复述检测」是弱启发，阈值待接地校准 | 实现期给保守阈值（只在出现**完整命令表**时告警），首跑后校准 |
| Q-4 | `deps` 的「抽掉依赖」如何机械执行？（停容器 / 改端口 / 设环境变量？） | **实现期需定**：v1 建议按 `deps` 声明的类型分派（compose 服务 → `docker compose stop`；本地进程 → 不启动它；端口类 → 指向不存在的端口）。此为 negative control 的落地关键，spec-review 应重点审 |

## Compliance

- **skill 目录约定**：`SKILL.md` + `scripts/` + `references/` + `tests/`，`setup.sh` 自动装载（**无需改 setup.sh**）。
- **bundle 权威源纪律**：本 change **不改** `sdflow-init/assets/workflow/`（未新增/修改 spec 工作流规则）⇒ 无需 `sdflow-init update` 回灌。
- **托管区块纪律**：`opsx-devenv` 为新 marker token，**MUST NOT** 写入 `opsx-init` 区块。
- **机械化优先基准**（CLAUDE.md 设计基准 1）：一致性能机械化的一律机械化（命令表渲染 / 状态迁移 / 五条 lint / negative control）；残余（归属判定 / 语义恒真 / `covers` 正确性）**诚实划归语义层**，非弱点。
- **目标态导向**（基准 2）：泳道设计锚目标态（该有哪些泳道），**MUST NOT** 以「现存项目大多只有单元测试」论证「集成泳道可省」。
- **一个 change 一个完整阶段结果**（基准 4）：本 change = 一个完整可用的 skill（P0 全含）；P2 项（doctor 生成 / CI 壳生成）属同一内聚交付物，不另开 change。
- **审查顺序**：`/sdflow-spec-review`（设计门）→ 实现 → `/review` → push → `/sdflow-code-review` → `/sdflow-done`。
- **HR-TG**：命中 TG-08 / TG-09 / TG-17 / TG-26 ⇒ spec-review **单开领域 cross-model**。
- **测试纪律**：改 `scripts/` 必跑 `tests/`（本仓强制）。
