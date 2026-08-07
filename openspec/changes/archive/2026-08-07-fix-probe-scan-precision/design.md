## Context

动机见 [`proposal.md` — Why](./proposal.md)。此处只列解释方案所需的现状与约束。

**现状：`$RULES_ROOT` 有两个可能来源，而只有其中一个涉及「拷贝」。**

`~/.sdflow/hack/resolve-workflow.sh` 的三步链（实读 `:38-83`）：

| 步 | 判据 | 结果 | 涉及拷贝？ |
|---|---|---|---|
| ① | 仓内有**规则文件本体**（`workflow.md` / `spec-checklists/` / `code-checklists/` 任一） | `local-pin` = 仓内 `openspec/workflow/` | **是**（`sdflow-init update` 拷的 tools） |
| ② | `~/.sdflow/workflow`（Unix 软链）或 `~/.sdflow/workflow-path`（Windows 指针） | `global-canonical` = **运行 checkout 内的文件树本身** | 否 |
| ③ | 以上皆不可达 | `exit 2` → 调用方显式降级通用评审 | — |

步②的两个平台实现**都指向活 checkout**（Unix 实测 `readlink ~/.sdflow/workflow` →
`~/.skills/sdflow-skills/sdflow-init/assets/workflow`；Windows 由 `setup.sh:489`
`printf '%s\n' "$bundle"` 写入活 checkout 路径）。而 SKILL 亦软链自同一 checkout ⇒
**步②路径上 tools 与 SKILL 恒同代**。

∴ **bundle 拷贝链**的 skew 全部存在空间 = 步①。**删掉步①，这条链的 skew 无处可生。**
〔spec-review-amendment F49〕`~/.sdflow/hack/` 拷贝链与 Windows SKILL 快照是另外两个失鲜面，本 change
不动它们（见 Risks 与 Non-Goals）——MUST NOT 表述为「消费仓副本是 skew 的唯一成因」。

**约束**：`spec-workflow` 既有安全红线——`sdflow-init update` **MUST NOT 自动删除**消费仓内既有
规则文件。本设计不触碰该红线，只把「已无生效路径」的事实通过告警告知。

## Goals / Non-Goals

**Goals（设计层）**
- 规则与 tools 收敛为**全局单份**，消费仓侧零执行依赖。
- 删除路径上**不留半态**：不存在「SKILL 已删探测 × 消费仓仍有旧副本」导致的新失败模式。
- 存量 pin 仓的切换**可被人察觉**（告警），而非静默换了规则来源。

**Non-Goals（设计层，proposal 的 Non-Goals 不重复）**
- 不提供「规则版本冻结」能力承诺〔设计门 Q4〕——`SDFLOW_HOME` 保持其既有「测试隔离重定向」契约
  （`resolve-workflow.sh:8`）；操作者自设该 env 指向自备目录属环境行为、自担后果（注意它同时是
  `setup.sh` 的安装根 `setup.sh:468`，对其跑 setup 会覆盖所指内容——F4 的自毁形态因此不构成 spec
  缺口，spec 本就不承诺冻结），spec MUST NOT 将其立为面向使用者的版本冻结路径。
- 不改 `resolve-workflow.sh` 的退出码语义（`0` / `2` / `64` 三码原样保留，**不新增码位**）。
- 不改两个评审 SKILL 对 `exit 2` 的既有降级分支（它们已实现，本 change 只是让更多情形落到它）。

## 组件与依赖（最终态）

```
                    运行 checkout  (~/.skills/sdflow-skills)
                    ├── sdflow-*/SKILL.md ──────symlink──▶ ~/.claude/skills/
                    ├── sdflow-init/assets/workflow/  ◀──symlink── ~/.sdflow/workflow
                    │     ├── tools/*.py            （评审机械层·全局单份）
                    │     ├── lens-metric-contract.md（anchor_lint 机读依赖）
                    │     ├── trigger-catalog.md 等规则
                    │     └── WORKFLOW-GUIDE.md     （人读·仍下发）
                    └── sdflow-init/assets/hack/resolve-workflow.sh ──cp──▶ ~/.sdflow/hack/

  消费仓  openspec/
          ├── workflow/WORKFLOW-GUIDE.md      ← 由 sdflow-init update 铺（唯一残留）
          └── schemas/sdflow-spec-driven/     ← openspec CLI 读，非 workflow 规则
```

**被删除的边**：消费仓 `openspec/workflow/{tools/,lens-metric-contract.md}`（不再铺）·
resolver 步① 的 `local-pin` 分支 · `ship_gate.py` 的 `tools_spec` 比较腿。

**GUIDE 保留下发（D14 不动，人已确认）**〔spec-review-amendment F45〕：`WORKFLOW-GUIDE.md` 照旧铺进
消费仓，但其生成器（`hack/gen_workflow_guide.py`）MUST 把指向 sibling 规则文件的相对链接
（`./ff-generation-constraints.md` · `./reference/quality-layering.md`×4 · `./workflow-history.md`）
降为文字引用或内联对应小节——目标态消费仓 `openspec/workflow/` 只有 GUIDE 一个文件，相对链接全部
断链，而「随仓走、不用跳文件」正是 D14 保留它的理由，断链会击穿该理由（tasks 6.10）。

## 决策图：resolver 两步链（TG-12）

```
       ┌─────────────────────────────┐
       │ resolve-workflow.sh --root  │
       └──────────────┬──────────────┘
                      ▼
        ~/.sdflow/workflow 目录存在？(Unix 软链透明命中)
                      │
          ┌───── 是 ──┴── 否 ─────┐
          ▼                        ▼
          │              ~/.sdflow/workflow-path 可读？(Windows)
          │                  ┌── 是 ──┴── 否 ──┐
          │                  ▼                  │
          └────────▶  sane() 健全性检查          │
                     (workflow.md 非空 +          │
                      两个 checklists 目录非空)   │
                          │                      │
                    ┌─ 过 ┴─ 不过 ───────────────┤
                    ▼                             ▼
              exit 0 + stdout=路径          exit 2 + stderr 告警
                                          （调用方显式降级通用评审）
```

🔴 **与现状的唯一差别**：入口处**没有了**「先看仓内有没有规则文件」这一步。仓内副本无论存在与否，
都不再影响解析结果。

## 时序：为什么「没有可错位的时点」（TG-10）

本 change 跨 5 个组件（`resolve-workflow.sh` / `init.py` / 两个评审 SKILL / `ship_gate.py`），
其协作的关键在于**改动传播的时点**。左为现状、右为目标态：

```
现状（两条链，两个时点）              目标态（一条链，一个时点）
──────────────────────────────      ──────────────────────────────
开发者 push bundle 改动               开发者 push bundle 改动
        │                                     │
运行 checkout: git pull ─┐            运行 checkout: git pull
        │                │                    │
   SKILL 立刻新 ◀────────┤              SKILL 立刻新 ─┐
        │                │                    │        │
        │          消费仓: sdflow-init   全局 canonical │ 同一 checkout
        │          update  ← 人手动       立刻新 ◀──────┘   同时生效
        │                │                    │
        │          消费仓 tools 才新          评审读全局 tools
        ▼                ▼                    ▼
   ⚠ 两点之间 = skew 窗口              ✅ 无中间态，无窗口
```

**右侧没有任何「人手动」的方框 ⇒ 没有可遗漏的步骤 ⇒ 没有可错位的时点。** 这正是删除探测器的
充分理由：探测器要探的那个窗口，在图上已经不存在了。

> 附带说明：`setup.sh` 仍是必须跑的一步（它刷 `~/.sdflow/hack/` 与 canonical 软链），但那是
> **`pull → setup` 这条既有纪律**。〔spec-review-amendment F1〕`~/.sdflow/hack/` 这条拷贝链**目前无守**
> ——`capability-manifest.json` 成员仅 `outside-voice-job.py` / `outside-voice.sh` / `skill-principles.md`
> 三项（`outside-voice-job.py:201` `MANIFEST_ENTRIES`），不含 `resolve-workflow.sh`，且只在 codex 宿主
> 后台 voice 的 preflight 被消费。登记为诚实边界；根因项（hack 链 symlink 化）记 todo（tasks 6.11），
> 不在本 change 范围。

## Decisions

全部承重决策（D1–D16）与承重约束（C1–C18）见 [`decision-memo.md`](./decision-memo.md)。
本 change 命中 TG-23（≥2 合理方案），决策记录落 `openspec/adr/0039`；`openspec/adr/0038`（本分支新建
于 `164bb88`、从未进 main、其版本对比机制从未实现）同批**删除**〔设计门 Q3〕，其候选与砍因写进 0039
取舍段——引用砍因时 MUST 写「起手前提被证伪 ⇒ 决策撤销」，MUST NOT 写「问题域消失」（F32）。

## 协议文档套件 scope-check（TG-25 · BASE-29）

本 change 删除的是一个**概念**（pin / 双链）。其牵连面由**概念词表 sweep** 枚举——产表方法即验收方法
（见下「验收三判据」判据 1），MUST NOT 手工维护行号清单（写死行号违反本仓「让脚本自己报」取向）：

| 面 | 载体 | 处置 |
|---|---|---|
| 本 change delta（spec-workflow） | resolver / bundle 下发 / 迁移告警 / **锚自检**（「契约与 tools 同批下发」句 + pin 错配 Scenario）共 4 个 Requirement | delta 已含（锚自检为 spec-review 后补，F6） |
| 其他主 spec | `maintain-scan`（pin 遮蔽语义 + 「仅剩 tools 判干净」Scenario，F7）· `workflow-metrics`（「`ignore_patterns("tests")` MUST 保留」注，F8）· `yq-yaml-operations`（R12 计数 + Purpose 枚举含镜像，F9） | 各新增 delta；yq 的 Purpose 段非 Requirement，随 change 直接订正主 spec |
| 托管块权威源 | `sdflow-init/assets/snippets/claude-section.md`（「规则副本则用之」×3 + INDEX 同步 pin 措辞） | tasks 6.4——**动作对象是权威源，非本仓 CLAUDE.md 直改**（直改会被下次 update 覆写回，F17） |
| 项目指令 | `CLAUDE.md`（托管块经 update 刷新 + 非托管区手写节）· `AGENTS.md` 四处 | tasks 6.4 / 6.5 |
| 修法文案 | `lens_metric_emit.py` · `resolve-models.sh` · `sdflow-upgrade/SKILL.md`（含 frontmatter）· `README.md` | tasks 6.6（口径统一为「回运行 checkout 跑 `bash setup.sh`」） |
| docs | `workflow-map.{md,html}` · `02-module-reference.md` · `workflow-skills/sdflow-spec-review.md` · `ROADMAP.md` | tasks 6.7（按 sweep 命中处置） |
| ADR | 0003 / 0005 / 0019 / 0036 加状态注记；0038 删除；0039 新落 | tasks 6.8 |
| resolver 自述 | `resolve-workflow.sh` 头部契约注释（「三步链 / 本地 pin」） | tasks 2.1（F34） |
| 测试 | 必红文件集（`test_resolve_models.py` · `test_resolve_workflow.py` · `test_marker_consistency.py` · `test_init.py` · `test_init_contract_sync.py` · `test_task5_regression.py` · `test_maintain_scan.py` · `test_async_branch_parity.py`） | **以 pytest 实跑红名单为准**（tasks 2.6 / 3.5 / 4.3 / 1.6） |
| 豁免 | `adr/0039` 取舍段 · `decision-memo.md` · `openspec/changes/archive/**` · 本 change 目录内评审产物 | 历史叙述合法保留，进 sweep 豁免清单 |

## 验收三判据（删除类 change 的闭环验收）

1. **概念词表 sweep 归零**（tasks 7.6）：归零词（`local-pin` · `两条分发链` · `显式 pin` · `pin 遮蔽`）
   全仓 grep **不带 `--include` 限定**（`.py`/`.sh`/`.yml`/`.md` 全吃）归零，豁免表显式列出；逐条判词
   （`规则副本` · `sdflow-init update` · `openspec/workflow/tools`）每个命中要么处置、要么登记豁免。
   **MUST NOT 以某条 grep 零命中推断「无消费者」**——grep 对 pathlib 拼接 / `full=False` / 目录范围外
   文件结构性失明（F10–F14 实证），必红集一律以 pytest 实跑为准。
2. **全仓 pytest 绿 + 反向锚在场**（tasks 7.1）：「绿」可被删测试满足（F50），故同时要求 4 条新增反向
   锚用例在场且实现中途验证过「会红」。
3. **三态真跑**（tasks 7.3–7.5）。

## sane() 扩面决策（A5 · 形状级判据，拒绝成员清单）

canonical 成为 tools 的**唯一**交付路径 ⇒ `sane()` 健全性面必须跟着扩（不扩 = 缩水，通则③）。但扩的
方式 MUST 是**形状级**：`tools/` 目录存在且非空 + `lens-metric-contract.md` 非空——**MUST NOT 枚举具体
`.py` 成员**。成员清单 = 每加一个工具补一条守卫 = 本 change 要杀死的补丁螺旋在守卫里复活；而现实的
半坏态（pull 中断、部分安装）是整目录/整文件缺失，「缺某一个工具」由该工具调用自身 fail-loud 兜
（proposal 论证 2 的原话）。

## 失败模式表（TG-08）

| # | 失败模式 | 触发条件 | 现行行为 | 本 change 后行为 |
|---|---|---|---|---|
| F-a | 全局 canonical 不可达 | 未跑 `setup.sh` / `~/.sdflow` 被删 | `exit 2` → 显式降级通用评审 | **不变**（唯一变化：更多情形落到这条，因为没有 pin 兜底了） |
| F-b | 全局 canonical 半坏（`workflow.md` 空 / checklists 空） | pull 中断、磁盘满 | `sane()` 不过 → `exit 2` | **不变** |
| F-c | 消费仓残留旧规则副本 | 存量 pin 仓 | 步① 命中 → **用旧规则** | **改用全局规则** + `stale_shadow_warnings` 死件告警（带「先跑 setup 再判断」前置条件 + 可复制删除命令，见 tasks 4.1） |
| F-d | 消费仓残留旧 `tools/` | 存量仓 | 可能被步① 路径执行 | **永不被执行**（无步①）；作为死件由告警提示 |
| F-e | 旧 tools 被新 SKILL 调用 | 仅步① 路径可能，本 change 后**不可能** | `anchor_lint` exit 2 / `hr_tg_intersect` EmitError | **该情形消失** |
| F-f | Windows：旧 SKILL × 新 canonical tools | `git pull` 后未跑 `setup.sh` | 无机制覆盖 | **仍无机制覆盖**（结构上不可自举，见 Risks） |
| F-g | `resolve-workflow.sh` 自身缺失 | 未跑 `setup.sh` | 调用方 `[ -x ]` 预检 → 提示跑 `setup.sh` | **不变** |

**可观测性**：本机制的**全部**可观测面 = ① `resolve-workflow.sh --explain` 的
`source=global-canonical path=…` stderr 行；② `exit 2` 时的固定告警文案；
③ `sdflow-init` 的陈旧遮蔽告警。**无新增日志、无新增落盘产物**——本 change 净删除机制，
不引入需要观测的新状态。

## Risks / Trade-offs

- **[存量 pin 仓的规则来源被静默切换]** → 由 `stale_shadow_warnings()` 与 `maintain_scan` 的既有残留
  检查告警覆盖（二者**行为不变、只改文案**）。但告警只在跑 `sdflow-init` / `sdflow-maintain` 时出现，
  **不在评审起手出现** ⇒ 该仓下一轮评审会直接用全局规则而当场无提示。**接受**：规则来源切换不改变
  评审的正确性（全局规则是权威源），且 pin 语义的取消本身就是本 change 的目标。
- **[Windows 上「旧 SKILL × 新 tools」仍无覆盖（F-f）]** → **不缓解，登记为诚实边界**。检查者只能是
  SKILL 自己或 `~/.sdflow/hack/` 的 helper，二者同为一次 `cp -r` 的产物（`setup.sh:119`），没跑
  `setup.sh` 就一起旧 ⇒ **运行时自检结构上不可自举**。〔spec-review-amendment F48〕该边界的准确表述
  到此为止——**CI 层面可测但目前未测**：`.github/workflows/windows-recorder-smoke.yml` 在
  `windows-latest` 跑全量 pytest，触发 paths 覆盖本 change 的全部脚本/资产面（两个 SKILL.md 为纯指令
  资产、不在 paths 亦无可执行测试面）。MUST NOT 写成「结构性无测试面」；补 CI 回归记 todo，不在本 change。
- **[「tools 的 fail-closed 覆盖所有旧版失败形态」前提已验证关闭〔A12〕]** → 6 个 tool 全部
  `argparse` + `required=True` + `sys.exit(main())`，无静默默认；运行时真读版本化输入的只有 3 个——
  `anchor_lint.py`（读 contract，`EnumsError` → exit 2「绝不回落硬编码」）· `lens_metric_emit.py`
  （读 contract，受控 fail-closed）· `hr_tg_intersect.py`（读 trigger-catalog，`EmitError`「不静默按
  空集放行」）。前提成立，不再挂账（proposal 假设表同步关闭）。
- **[删除范围大，半态危险]** → P0 的四项（resolver 删步① · `copy_bundle` 停铺 · 两个 SKILL 删探测段 ·
  测试）**MUST 同批落地**。依据〔spec-review-amendment F37，订正过度演绎〕：不同批会留下混合语义半态，
  最坏形态 =「SKILL 仍探测 × resolver 仍有步① × 存量 pin 仓 contract 旧」⇒ 该仓每轮评审起手硬停、且
  硬停给出的修法提示（跑 `sdflow-init update`）已失效——受害面是**存量 pin 仓**而非全体消费仓，但
  「提示失效的死循环硬停」同样不可接受；且四项同属一个概念的删除面、量小，分批无收益。
- **[消费仓 gate 不再看见评审机械层变更（`tools_spec` 腿退役的后果，F44）]** → 消费仓顶层无
  `sdflow-init` 条目（实证 `10-michi`）⇒ 退役后，code-review 与 done 之间若全局 canonical 的 tools
  变了，`ship_gate` 两条腿都看不见。准确口径：对 global-canonical 仓该盲区**change 前即存在**（旧腿
  只守仓内镜像，从不守 canonical）；净回归仅「窗口内有人跑 update 刷镜像会被察觉」一种情形，而镜像
  删除后该动作不可能发生。**接受，不建替代**——为它建 canonical identity 对比等于把本 change 刚消灭
  的版本核对机制请回来。

## Migration Plan

**顺序不可颠倒**（每一步都保证中途中断时系统仍可用）：

1. **先删 SKILL 侧的探测段**（`sdflow-code-review` / `sdflow-spec-review`）。此时副本仍在、resolver
   仍有步①——系统完全可用，只是不再做那个从未抓到真阳的检查。
2. **再删 resolver 步①**（bundle 权威源 `sdflow-init/assets/hack/resolve-workflow.sh`）。此时所有仓
   改走步②；存量副本变死件但无害。
3. **再停 `copy_bundle` 铺 tools/contract**，并退役 `--dev` / `full` / T15 豁免。
4. **最后** 退役 `ship_gate.py` 的 `tools_spec` 腿、改写告警文案、订正 CLAUDE.md / ADR / CONTEXT、
   删除本仓 `openspec/workflow/` 下 7 个文件、关闭 T269/T270。
   🔴 **删本仓镜像必须与两处硬编码引用同批**：`hack/tests/test_yq_wrapper_consistency.py` 的 `TARGETS`（`:57`）与 `hack/check_encoding_hygiene.py`（`:83`）的镜像排除分支——前者不处置即因文件不存在而红，后者留着是死代码。

> 🔴 **步 1 必须在步 3 之前**：反序（先停铺、SKILL 仍探测）会让仍处旧 resolver/pin 状态的存量仓
> 在失效提示下硬停（精确口径见 Risks「半态危险」条）。

**发布**：push → 运行 checkout `git pull` → **立即** `bash setup.sh`（刷 `~/.sdflow/hack/` 与 canonical）。
消费仓**不再需要** `sdflow-init update` 才能评审；跑它只为拿新的 `WORKFLOW-GUIDE.md`。

**回滚**：本 change 的改动集中且**几乎全是删除** ⇒ `git revert` 即复原；复原后 MUST 依次：每台机
回运行 checkout 重跑 `bash setup.sh`（拿回三步链 resolver）→ 各消费仓重跑 `sdflow-init update`
（拿回 `tools/`，否则回滚后首轮评审因缺 tools 裸崩）。〔spec-review-amendment F28〕该顺序 MUST 落进
两个应急时真会翻的载体：`adr/0039` 的「回滚」节 + 本仓 `CLAUDE.md` 的回滚条目（tasks 6.5/6.8）——
design 归档后不是应急回滚会翻的地方。

## Open Questions

无。（`--dev` / `full` 退役后 toolkit 源仓 dogfood 的具体验证路径属实现细节，由 tasks 覆盖。）

## Compliance

- **DOC-1（正文即最终态）**：本文正文只描述目标态；被推翻的中间方案（版本戳、字节比对、pin-only
  判据）**不进正文**，其记录在 `decision-memo.md` 的 D9–D12 与 `adr/0039` 的取舍段。
- **基准 5（无界语法禁手搓）**：本 change **不新增任何解析器**；删除的正是一段依赖 `grep`/`sed` 提取
  markdown 内容的探测逻辑。
- **`spec-workflow` 安全红线**：不自动删除消费仓既有规则文件，仅告警。**遵守，无豁免。**
- **`premise-verification`**：本文引用的代码事实（`resolve-workflow.sh:38-83` · `setup.sh:119/489` ·
  `init.py:253-288` · `ship_gate.py:947-959` · `anchor_lint.py` / `hr_tg_intersect.py` 的
  fail-closed 路径）均在相位 B 实读或实跑核验，未从记忆写入。
