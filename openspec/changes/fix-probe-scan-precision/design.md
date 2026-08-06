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

∴ skew 的全部存在空间 = 步①。**删掉步①，skew 无处可生。**

**约束**：`spec-workflow` 既有安全红线——`sdflow-init update` **MUST NOT 自动删除**消费仓内既有
规则文件。本设计不触碰该红线，只把「已无生效路径」的事实通过告警告知。

## Goals / Non-Goals

**Goals（设计层）**
- 规则与 tools 收敛为**全局单份**，消费仓侧零执行依赖。
- 删除路径上**不留半态**：不存在「SKILL 已删探测 × 消费仓仍有旧副本」导致的新失败模式。
- 存量 pin 仓的切换**可被人察觉**（告警），而非静默换了规则来源。

**Non-Goals（设计层，proposal 的 Non-Goals 不重复）**
- 不为「规则版本冻结」提供新机制——`SDFLOW_HOME` 指向自备 canonical 即可，走步②主路径。
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
> **`pull → setup` 这条既有纪律**，且 `~/.sdflow/hack/` 那条链由 `capability-manifest.json`
> 独立守（`manifest skew`，不在本 change 范围）。

## Decisions

全部承重决策（D1–D16）与承重约束（C1–C18）见 [`decision-memo.md`](./decision-memo.md)。
本 change 命中 TG-23（≥2 合理方案），决策记录落 `openspec/adr/0039`；`openspec/adr/0038` 同批标
**Superseded**（其问题域随本 change 消失）。

## 失败模式表（TG-08）

| # | 失败模式 | 触发条件 | 现行行为 | 本 change 后行为 |
|---|---|---|---|---|
| F-a | 全局 canonical 不可达 | 未跑 `setup.sh` / `~/.sdflow` 被删 | `exit 2` → 显式降级通用评审 | **不变**（唯一变化：更多情形落到这条，因为没有 pin 兜底了） |
| F-b | 全局 canonical 半坏（`workflow.md` 空 / checklists 空） | pull 中断、磁盘满 | `sane()` 不过 → `exit 2` | **不变** |
| F-c | 消费仓残留旧规则副本 | 存量 pin 仓 | 步① 命中 → **用旧规则** | **改用全局规则** + `stale_shadow_warnings` 告警「已无生效路径、可删」 |
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
  `setup.sh` 就一起旧 ⇒ **结构上不可自举**。且本仓对 Windows 分支无测试面
  （`IS_WINDOWS` 由 `uname -s` 定、无环境变量覆盖入口，`hack/tests/test_install_agents.py:14` 自述）。
- **[「tools 的 fail-closed 覆盖所有旧版失败形态」是未完全验证的前提]** → 已核 `anchor_lint.py`
  （`EnumsError` → exit 2「绝不回落硬编码」）与 `hr_tg_intersect.py`（`EmitError`「不静默按空集放行」）
  两个主要消费方；**其余 tools 未逐一核验**。缓解：本 change 后该兜底只对**步②路径不存在的失败**
  起作用（即基本不再被触发），风险敞口随之收窄；仍在 proposal 的假设表登记。
- **[删除范围大，半态危险]** → P0 的四项（resolver 删步① · `copy_bundle` 停铺 · 两个 SKILL 删探测段 ·
  测试）**MUST 同批落地**。任一遗漏的最坏形态：SKILL 仍探测而副本已不铺 ⇒ **每个消费仓每轮永久硬停**。
  Migration Plan 的顺序即为此设计。

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

> 🔴 **步 1 必须在步 3 之前**：反序（先停铺、SKILL 仍探测）⇒ 每个消费仓每轮评审永久硬停。

**发布**：push → 运行 checkout `git pull` → **立即** `bash setup.sh`（刷 `~/.sdflow/hack/` 与 canonical）。
消费仓**不再需要** `sdflow-init update` 才能评审；跑它只为拿新的 `WORKFLOW-GUIDE.md`。

**回滚**：本 change 的改动集中且**几乎全是删除** ⇒ `git revert` 即复原；复原后消费仓需重跑
`sdflow-init update` 才能拿回 `tools/`（因为回滚后 SKILL 又会去读 `$RULES_ROOT/tools/`）。
**该顺序须写进 revert 说明**，否则回滚后首轮评审会因缺 tools 裸崩。

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
