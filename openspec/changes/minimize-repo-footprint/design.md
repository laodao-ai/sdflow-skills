# 设计：minimize-repo-footprint

> 决策真相源 = [`adr/0003`](../../adr/0003-deploy-footprint-global-rules-minimal-repo-copy.md)（分层 + explore 骨架 + **grill-amendment 2026-07-03**）+ [`adr/0005`](../../adr/0005-dev-runtime-checkout-split.md)（dev/runtime checkout 分离）。术语见 [CONTEXT.md](../../CONTEXT.md)（**反静默守卫** 已扩到 bundle 解析 + 陈旧遮蔽；**开发/运行 checkout**）。
> 本文经一轮逐决策 grill 收敛（2026-07-03），下列 §四/§五/§六/§七 的 〔grill-amendment〕 标记处为本轮修正。
> 另经一轮执行模型基线重审（explore 2026-07-03，[`adr/0006`](../../adr/0006-execution-model-baseline-fleet-anchored.md) 机队锚定）：〔model-baseline-amendment〕 标记处 = resolver 从 prose 协议改**全局脚本**执行。

## 一、依赖与前置

- 依赖 Phase A（`streamline-workflow-automation`，已归档）：三阶段骨架 + review UI B1 归位（tools/ 入 `openspec/workflow/tools/`、serve.sh/review.html 留 openspec/ 根）。
- 依赖 `adr/0005` 的 **dev/runtime checkout 分离**：本 change 的 canonical 锚点 = 运行 checkout；resolver 的 local-first 步正牌用户 = 开发 checkout。
- 与 `issues-pool-batch-mgmt`（Phase B）交集：共享 issues 层脚本 `issues.py` 的物理落点随本 change 的脚本全局化一并定。
- 与 `opsx-ship-orchestrator` 互不依赖，均只依赖 A。

## 二、命中触发（TG，起手判定）

| TG | 命中点 | 激活 |
|---|---|---|
| **TG-14** | 重构部署/解析组件（canonical 机制、resolver 新增） | 组件/依赖图（§四）+ 组件清单 BASE-25（§六） |
| **TG-12** | resolver 三步 + 平台回落链决策逻辑 | 决策图（§三） |
| **TG-21** | 有未决实现细节 | proposal 开放问题 |
| **TG-20** | 影响所有外部消费仓 | proposal 利益相关方 |
| **TG-23** | ≥2 方案（提根 or 不提；软链 or 指针；checkpoint 全局 or per-repo） | 决策记录 = `adr/0003`+`adr/0005`（引，不复制） |

## 三、解析 resolver（决策图，TG-12）

skills（spec-review / impl-review / opsx-done / recorders / opsx-ship）读规则的统一顺序，一条链覆盖两类仓。
〔model-baseline-amendment / `adr/0006`〕**执行主体 = 全局脚本 `~/.sdflow/hack/resolve-workflow.sh`，非 SKILL.md prose 协议**——下图三步链由脚本确定性执行（stdout = 规则根路径；全局缺失 → 非零退出 + stderr 固定告警文案），SKILL.md 只写"跑脚本、用输出路径；非零退出 → 显式降级 + 转发脚本告警文案"：

```
              skill 要读某规则文件（如 workflow.md / spec-checklists/…）
                                 │
                                 ▼
        ┌────────────────────────────────────────────────┐
        │ 步1：仓内有"规则文件本体"？                     │
        │   （查 workflow.md / spec-checklists/ /          │
        │     code-checklists/，**不查 openspec/workflow/  │
        │     目录**——tools/ 使该目录处处存在）           │
        └───────────────┬──────────────────┬─────────────┘
                     有 │                  │ 无
                        ▼                  ▼
              ┌──────────────────┐   ┌──────────────────────────────────┐
              │ 用本地           │   │ 步2：解析全局 canonical bundle     │
              │ · 开发 checkout  │   │  ┌ 试 ~/.sdflow/workflow/ 目录     │
              │   dogfood 在用端 │   │  │   (Unix 软链命中,透明)           │
              │ · 消费仓显式 pin │   │  └ 否则读 ~/.sdflow/workflow-path  │
              │  〔adr/0005〕    │   │      (Windows 指针命中)            │
              └──────────────────┘   └────────┬─────────┬───────────────┘
                                           有 │         │ 无
                                              ▼         ▼
                                    ┌──────────────┐ ┌────────────────────────┐
                                    │ 用全局       │ │ 步3：显式降级 = 反静默守卫│
                                    │ 外部消费仓   │ │ 通用评审 + 告警(不静默当  │
                                    │ 跟 released  │ │ "本项目无此评审层")       │
                                    │ HEAD         │ │ 〔CONTEXT: 反静默守卫〕   │
                                    └──────────────┘ └────────────────────────┘
```

- **步1 查规则文件、不查目录**〔grill-amendment〕：`tools/`（≈5 文件）因"服务器根=openspec/"必须留在每个消费仓 `openspec/workflow/tools/`，故 `openspec/workflow/` 目录处处存在。查目录→恒真→每个消费仓误命中 pin。查**规则文件本体**才把"有 tools/ 无规则"的消费仓正确落到步2。
- **步1 正牌用户 = 开发 checkout**〔grill-amendment / adr/0005〕：开发 checkout 有本地 `openspec/workflow`（WIP）→ 命中步1 → dogfood 自己未发布编辑；消费仓显式 pin 也走此步。**无需 config flag 声明"我是源仓"**——本地规则副本的存在即声明。
- **步2 平台回落链**〔grill-amendment〕：Unix 命中软链目录（透明）、Windows 命中指针文件；skill 不判平台（**判平台的是脚本**）。
- **步3 = 反静默守卫**〔grill-amendment / CONTEXT〕：全局也缺 → 显式降级 + 告警，绝不静默当"无此层"。调用方 skill MUST NOT 静默吞脚本的非零退出码。
- **为何脚本化**〔model-baseline-amendment / `adr/0006`〕：执行机队 = opus / sonnet / gpt-5.5（机队锚定，非开发时模型）。弱一档模型执行三步 prose 协议的典型失效 = 静默跳步（跳过本地直读全局、或全局缺时静默降级）——恰是反静默守卫要防的形态。脚本化后跨模型行为一致，且 resolver 分支测试从"模型行为测试"变普通脚本单测。这也是本仓「机械活交脚本、模型只做判断」哲学的应用。
- **契约细则**〔spec-review-amendment，tasks 3.1 为准〕：`--root`（缺省 `git rev-parse --show-toplevel`，防 cwd 非仓根误判滑向全局）；`${SDFLOW_HOME:-$HOME/.sdflow}` env override（测试隔离）；步① 粒度 = **any-of 即 pin** + 部分残留专门告警（迁移期必经态，隐式语义两种实现各有一种静默失效）；步② 命中后最小健全性检查（workflow.md 非空 + 三顶层单元在，防 pull 半坏态静默广播）；步③ = 退出码 2；调用侧 `[ -x ]` 先判**脚本自身缺失**（专属"重跑 setup"文案，与步③ bundle 缺失区分）；`--explain` 来源诊断。

## 四、部署拓扑（组件/依赖图，TG-14）

〔grill-amendment：**撤销提根**——bundle 留 `assets/workflow/` 不动；canonical 用**软链(Unix)/指针(Windows)**藏住 assets/ 布局。〕

> ⚠️〔spec-review-amendment / 图过时警示〕原图"运行 checkout = `~/.skills/laodao-skills`（与开发 checkout 同 repo 两 clone）"的假设**与实测不符**：两 remote 分家（laodao-skills 旧 @b248c2d / sdflow-skills 新）、git 历史不相交，`push→pull→setup` 发布边界曾断裂。
> ✅〔设计门拍板 2026-07-03，Q1=A〕运行 checkout 迁移为 **`~/.skills/sdflow-skills/`**（fresh clone 新仓 + setup.sh，tasks 0.1，先于 1.1/1.2）；配套 **`sdflow-upgrade`** skill（pull→setup→版本展示，tasks §7）承担日常升级，结构性堵 pull→setup 窗口。下图运行 checkout 路径已按拍板更新。

```
  ── 改前 ────────────────────────────────────────────────────
  opsx-project-init/assets/workflow/ (34)  ──copy_bundle──▶  消费仓 openspec/workflow/ (34)

  ── 改后 ────────────────────────────────────────────────────
  运行 checkout = ~/.skills/sdflow-skills （canonical 锚点, setup 在此跑；0.1 迁入〔设计门拍板〕）
  ├── opsx-project-init/assets/workflow/   ← bundle 仍是唯一权威源(不提根)
  │        └──[copy_bundle 只部署 tools/ 子树]──┐
  ├── ~/.sdflow/  ← setup 建的 agent 中立全局家：
  │     ├── workflow  ─软链(Unix)→ 上面 assets/workflow   /   workflow-path 指针(Windows)
  │     └── hack/{checkpoint-commit.sh, resolve-workflow.sh}  ← 拷贝(两平台, exec 位一次设好)
  └── (openspec/ 在此惰性存在, 不 run workflow on 自己  〔adr/0005〕)

  开发 checkout（独立目录 clone）
  ├── 编辑 assets/workflow / skill
  └── openspec/workflow/(WIP) → resolver 步1 local-first dogfood 自己

  消费仓（外部）
  └── openspec/
       ├── workflow/tools/ + serve.sh + review.html  ← 唯一复制项(≈5, 服务器根逼留)
       ├── config.yaml / changes/ / specs/           ← 仓本体
       └──(无规则文件 → resolver 步2 全局)

  workflow.md line62 [checkpoint] 约定 ──指向──▶ ~/.sdflow/hack/checkpoint-commit.sh(不再仓相对)
```

## 五、dev/release 隔离 = 两个物理 checkout（〔grill-amendment〕，详见 adr/0005）

原稿"assets vs openspec 目录隔离"经 grill 换成**更本质的物理 checkout 隔离**：

- **开发 checkout**（独立目录）：编辑 skill/bundle、跑 workflow dogfood；本地 `openspec/workflow` → local-first 吃**未发布**编辑。
- **运行 checkout**（`~/.skills/sdflow-skills`〔设计门拍板 Q1=A，0.1 迁入〕）：只 pull 完成品 + setup（日常经 `sdflow-upgrade` skill 一键）；canonical 锚点；只含**已发布**、不 run workflow on 自己。
- **发布边界** = push(开发) → pull(运行) → setup。
- **运营细节（写进纪律段）**：改**规则**→ local-first 自动 dogfood；改 **skill 本身**→ 需在开发 checkout 跑 setup 才测得到（本机无外部消费者，canonical 临时指 dev 无碍）。

## 六、组件清单（BASE-25，TG-14）

| 组件 | 角色 | 本 change 动作 |
|---|---|---|
| `opsx-project-init/assets/workflow/` | bundle 唯一权威源 | **不提根**〔grill-amendment〕；`copy_bundle` 改为只部署 `tools/` |
| `~/.sdflow/workflow`（软链）/ `workflow-path`（指针） | canonical 解析位 | `setup.sh` 建：Unix 软链 / Windows 指针，锚运行 checkout〔grill-amendment〕 |
| `~/.sdflow/hack/checkpoint-commit.sh` | 过场提交工具（全局） | 从消费仓 `hack/` 移此；拷贝、两平台、exec 位根治〔grill-amendment〕 |
| `~/.sdflow/hack/resolve-workflow.sh` | **resolver 执行主体**（全局脚本） | 新增：确定性实现 §三 三步链（stdout=规则根路径 / 非零退出+告警文案）；随 setup 装，同 checkpoint〔model-baseline-amendment / adr/0006〕 |
| `opsx-project-init/scripts/init.py` | 部署器 | `copy_bundle` 去规则（只 tools/）；`copy_hack` 改为不进消费仓（全局装） |
| `setup.sh` | 安装器 | 加建 canonical 软链/指针 + 装 checkpoint 到 `~/.sdflow/hack/` |
| 各 skill SKILL.md 规则读点 | 规则消费者 | 改为**调用 resolve-workflow.sh 用其输出路径**（不在指令内自行执行三步链）〔model-baseline-amendment〕 |
| `workflow.md` line62 `[checkpoint]` 约定 | 调用点单一源 | 路径改指 `~/.sdflow/hack/checkpoint-commit.sh`〔grill-amendment〕 |
| `opsx-project-init update` 迁移路径 | 存量仓迁移 | 停复制规则 + 陈旧遮蔽告警（不自动删） |

**issues.py 落点〔6.1 决策〕**：留 `issues-recorder/scripts/`（随 skill 软链全局可用，不迁 ~/.sdflow——它是 skill 私有脚本，非跨 skill 共享协议）

## 七、迁移（opt-in 删，永不自动删；措辞对齐反静默守卫）

```
  opsx update（存量消费仓）:
    · 停止复制规则（只刷 tools/ 5 个）
    · 检测仓内残留旧规则文件 → 告警(反静默守卫·陈旧遮蔽变体):
        "openspec/workflow/ 下残留规则遮蔽全局 bundle 且不再被 update 刷新。
         想跟全局最新 → 手动删它;想 pin 在这一版 → 留着(即显式逃生口)。"
    · 绝不自动删（安全红线 + 免分辨源/消费仓 + 老仓平滑）
```

〔grill-amendment / CONTEXT〕本告警 = **反静默守卫**的"陈旧遮蔽"变体（元原则清单已补"悄悄用了旧的"）：不是"读不到"（缺席），是"读到旧的还当新的"（静默陈旧），同样须显形。

〔spec-review-amendment / D4〕触发点裁决（关闭 proposal 开放问题 4）：**update 内联为主 + `opsx-maintain` 兜底扫描**——两触发点均被动，兜底扫描收窄"常年不 update 的仓"敞口。检测范围**含旧版仓内 `hack/checkpoint-commit.sh` 孤儿副本**（不再被任何机制刷新/关注的旧全局化脚本），给对称提示："删=用全局 `~/.sdflow/hack/` / 本地 workflow.md 副本仍引用它则勿删"。

## 八、不做（Non-Goals，见 proposal）

- **不提根**〔grill-amendment〕：bundle 不搬仓根，canonical 间接层已解耦。
- **移无关 skill（≈17）切出去**：单独卫生 change，不在本 change（失败模式/验证方式与 footprint 机制不同）。
- 纯激进（tools/ 也全局 + 重写 serve.sh）· 按仓 pin 转默认 · 动归档 umbrella · 改 config.yaml 契约/specs 本体。

## 九、规则/边界合规声明

不引入跨产品共享数据模型（D-6 不适用）· 无 DB 迁移（D-2 不适用）· 无外部计费（TG-24 不适用）· 迁移守"绝不自动删"安全红线。
