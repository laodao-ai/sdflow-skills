# Design — done-roadmap-writeback

> 〔grill-amendment · adr/0013〕本 design 经 grill 逐分支死磕重构，初版四 ADR 全翻案——纠正两处基准误用：**① 用现状快照否定目标**（L1 曾靠解析 proposal 自然语言引用，被「现存 6 change 引用不统一」误证伪 → 改锚目标态 producer 机器锚）；**② emitter 正确性范式误套记录维护**（回写曾用 all-or-nothing fail-closed → 改 best-effort + 降级标注）。scope 从「纯 Markdown 一步」扩为 6 件（含改 `sdflow-roadmap` 生成格式 + 迁移 2 roadmap）。完整决策档案见 `openspec/adr/0013`。

## Context

`sdflow-done` 收尾流水线经核验为六步（`sdflow-done/SKILL.md`）：

```
0 确认change+默认分支+tasks复选框对账
1 Verify（强档，产 verify-report.md）
2 hand-off.md ── 内含 §2.1 issues sweep（archive 前跑，随归档 commit）
3 Archive + Spec 同步（中档子agent；openspec archive CLI；明确「不 git add/commit」）
4 Git Commit（弱档；git add openspec/ + git add -u）
5 Merge（主session；缺省 ff；untracked 硬检查）
6 最终摘要
```

**现状缺口**：全流程对 `openspec/roadmaps/{name}/` 零触碰。roadmap 驱动的分阶段 change 归档后，roadmap 复选框 / task-log 完成总结 / 里程碑状态全靠人工手动回填（本会话刚为 lens-metric-emit=P4/4.C 手动补过一次）。issues 侧早有 §2.1 sweep 自动化——roadmap 侧是对称的缺口。

**两条既有事实**（定时序与落点）：
- 第四步 `git add openspec/` 会暂存所有 `openspec/` 变更——roadmap 在 `openspec/roadmaps/` 下，故**任何在第四步前完成的回写，其文件被第四步自动提交**，无需额外 commit。
- `sdflow-roadmap/SKILL.md:195` 自述「将来若给 verify/done 接 hook 可自动化此检查」——producer 侧**本就预期 done 来做自动化消费**，改 sdflow-roadmap 配合非越界。

**grill 两纠正**（基准）：
- 不用现状 proposal 引用形态否定「L1 机械提取」——锚**目标态 producer 契约**会不会产确定性信号（`adr/0011` 目标态论证）。
- roadmap 回写是**记录维护**非正确性门——best-effort + 缺失显形，非 emitter 式 fail-closed 全停（CONTEXT『记录维护回写 vs 正确性门』）。

## Goals / Non-Goals

**Goals:**
- sdflow-done 归档收尾时，roadmap 驱动 change **确定性**回写关联 roadmap（勾选 + 完成总结 + 里程碑/阶段状态）。
- 关联检测 / 子任务定位 / 勾选**机械化**（读机器锚，非解析自然语言）；真正判断收窄到两处（完成总结叙述、里程碑句）。
- 结构化投入放**生成侧**（sdflow-roadmap 模板），回写侧机械消费。
- 记录维护 best-effort：能回写的回写、未做项降级标注显形，不阻塞 archive/merge。

**Non-Goals:**
- 不碰 issues 回写（§2.1 sweep 已覆盖）。
- 不做 roadmap Review 处置对账（mlh 4.D.4，校验非回写）。
- 不**全** frontmatter 化 roadmap——只结构化索引层，叙述层留人读散文。
- 不背 dual-read——旧 2 roadmap 一次性手动迁移。
- ~~不改 sdflow-roadmap~~（初版 Non-Goal，grill 翻案：生成侧结构化已纳入 scope）。

## Decisions

### D-1 关联锚 schema（producer 机器锚）

roadmap 驱动 change 起手在 **proposal 头部**写一行机器锚：

```
<!-- roadmap: mechanical-layer-hardening phase: P4 subtask: 4.C.1 -->
```

| 字段 | 取值 | 用途 |
|---|---|---|
| `name` | kebab | L1 定位 `openspec/roadmaps/{name}/`；单一源 |
| `phase` | `P4` | 里程碑/阶段行更新定位 `\|**P4**\|`；与 subtask 阶段号交叉校验 |
| `subtask` | 复选框级 `4.C.1`，多项逗号 `4.D.1,4.D.2,4.D.4` | L2 定位勾选行 |

- L1（关联哪个 roadmap）= grep `name`；L2（哪些子任务）= 读 `subtask` 列表——**均读锚字段、MUST NOT 解析 proposal 自然语言引用**。
- 无锚 → 按无关联静默跳过（producer 违约 fail-safe）。
- **本 change 自身无 roadmap 锚**（它非 roadmap 驱动）→ 正好 dogfood「无关联静默跳过」分支。

### D-2 索引层结构化 schema（生成侧，改 sdflow-roadmap 两模板）

roadmap 分**索引层**（机器消费）/**叙述层**（人读）。优化 = 结构化索引层：

| 索引元素 | 现状 | 新模板 | 回写动作 |
|---|---|---|---|
| 子任务 | `- [ ] 4.C.1 <描述>` | 保持 + 固定「交付标注槽」位 | 脚本勾选（靠 id） |
| 阶段状态 | 概览表**无状态列**（mlh 自加散文「就绪度」列） | 概览表加 `状态` **enum 列**（`planned`/`in-progress`/`delivered`/`deferred`） | 脚本更新 cell |
| task-log 条目 | 纯散文 | 散文 + 固定**机器锚行** `<!-- roadmap-writeback: change={n} subtask={id} archive={path} status=delivered -->` | 模型写叙述、脚本校验+幂等锚 |
| 里程碑句 | 散文 | 保持散文（叙述层） | 模型判断改 |

改 `roadmap-template.md`（概览表加状态列 + 子任务标注槽）+ `task-log-template.md`（条目加机器锚行）。

### D-3 ADR-1 关联判据 → 锚 producer 机器锚

初版「解析 proposal 自然语言引用」被 grill 揭穿为现状快照谬误（实证 2/6 全路径、余别名/缺失）。翻案：锚 D-1 机器锚，L1 grep name / L2 读 subtask——**L2 从「判断活」降为「读锚字段=机械」**。措辞属概率空间、弃之（同 gate frontmatter / lens-metric 契约）。

### D-4 ADR-2 时序（不变）

回写放**第 3.5 步**（archive 后 / commit 前），文件随第四步 `git add openspec/` 提交。完成总结用 **change 名 + archive 路径**追溯，**不写 merge hash**——流水线内自动回写结构上拿不到自己的 merge hash（merge 在其后），非现状快照。

### D-5 ADR-3 机械/判断切分

| 回写面 | 谁做 | 范式 |
|---|---|---|
| 勾选 `- [ ]{id}`→`- [x]` | 脚本写（机械） | lens-metric 归约式 |
| 阶段状态 enum cell | 脚本写（机械） | 同上 |
| task-log 完成总结 | 模型写叙述 + 脚本校验机器锚 | anchor_lint 产出侧校验式 |
| 里程碑句 | 模型判断改（脚本不碰） | — |

初版「纯指令步不引脚本」是被现状散文格式（脆弱）限制的；D-2 结构化后勾选/阶段状态机械核心进脚本。

### D-6 ADR-4 回写 = best-effort + 降级标注（三级 fail-safe）

```
             ┌──────────────────────────────┐
   3.5 回写步 │ proposal 有关联锚(name)?       │
             └───────────────┬──────────────┘
                     否 │            │ 是
             ┌──────────▼─┐   ┌──────▼────────────────────┐
             │ 静默跳过     │   │ roadmaps/{name}/ 四件套存在? │
             │（无关联,正常）│   └──────┬──────────────┬─────┘
             └─────────────┘       否 │            是 │
                          ┌───────────▼┐   ┌─────────▼──────────────────┐
                          │ 静默跳过     │   │ 逐 subtask id 定位复选框行    │
                          └─────────────┘   └──┬───────────┬────────────┬┘
                                        全定位│      部分定位│    全无法解析│
                                  ┌──────────▼┐ ┌─────────▼──────┐ ┌───▼─────────┐
                                  │ 全回写:     │ │ best-effort:    │ │ fail-closed: │
                                  │ 勾选+阶段   │ │ 回写能做的 +     │ │ 不写、提示    │
                                  │ +总结+里程碑│ │ 降级标注未做项    │ │ 留人工        │
                                  └────────────┘ │(task-log/摘要)  │ └─────────────┘
                                                 └─────────────────┘
```

- **记录维护非正确性门**：漏=记录陈旧、可事后补 → best-effort + 缺失显形（反静默），非 emitter 式 all-or-nothing。
- **回写失败三级**：全定位→全写；部分定位→回写能做的 + 降级标注（未定位 subtask 就地标 task-log/摘要）；完全无法解析格式→ fail-closed 留人工。
- **全程不阻塞** archive/merge（vs verify FAIL 阻塞；altitude 不同）；但 MUST 不静默——未做项写进 hand-off + 最终摘要。

### D-7 组件清单（6 件 + 插入位置）

```
起手: opsx:ff 后 → [roadmap-link 脚本: 写关联锚进 proposal] (producer 侧②④)
                                    │
归档: 3 Archive ─► [3.5 回写步 ⑤⑥] ─► 4 Git Commit(git add openspec/ 收纳回写) ─► 5 Merge
```

1. **关联锚契约**（D-1 schema，spec Requirement + 机读格式定义）
2. **sdflow-roadmap 两模板优化**（D-2，索引层 enum/锚）
3. **旧 2 roadmap 迁移**新格式（mechanical-layer-hardening / workflow-cost-optimization）
4. **`roadmap-link` 写锚脚本**（起手注入锚，机械拼行，幂等 fail-closed）+ 起手 MUST 带锚规范
5. **done 回写消费端**（SKILL 第 3.5 步：读锚 → best-effort 回写编排 + 降级标注）
6. **回写脚本**（勾选 + 阶段状态机械写；完成总结/里程碑机验锚校验，anchor_lint 式）

## Risks / Trade-offs

- **[误写 roadmap 真相源]** → 定位靠机器锚 id（确定性），部分失败 best-effort + 标注、全失败 fail-closed；回写在 commit 前、git 可 revert。
- **[producer 漏写锚 → L1 跳过]** → 起手 MUST 带锚规范 + `roadmap-link` 脚本降低漏写；真漏 → 按无关联跳过 + hand-off 显式提示（反静默）。
- **[scope 大：6 件含改 sdflow-roadmap + 迁 2 roadmap]** → fold 判据（related + 生成/回写同一契约闭环）；迁移只 2 个可控，dogfood 即验。
- **[里程碑句判断误写]** → 里程碑句是叙述层、模型判断改，脚本不碰；设计门/hand-off 人工复核兜底。
- **[roadmap 格式约定漂移]** → 生成侧 D-2 结构化后 done 只认新格式（旧已迁移），单一格式收敛漂移面。

## Migration Plan

- 改 `sdflow-roadmap/references/{roadmap,task-log}-template.md`（索引层结构化）+ `sdflow-done/SKILL.md`（第 3.5 步）+ 新增 `roadmap-link` / 回写脚本 + tests → 跑 `setup.sh`（symlink 即时生效）。
- **迁移 2 roadmap**：`mechanical-layer-hardening` / `workflow-cost-optimization` 的概览表加状态 enum 列、task-log 补机器锚行（历史条目可补最小锚或标 legacy）——无损、内容不丢。
- **回退**：回写步是叠加步，删除步 / 关联锚恒不产即回到现状；模板改动可 revert。
- dogfood：本 change 自身（无锚 → 跳过分支）+ 构造带锚 fixture 验证全写/部分写+标注/fail-closed 三级。

## Open Questions

- **里程碑句更新粒度**：回写只更新本 change 对应阶段行（enum cell，机械），里程碑**散文句**是否也改？倾向仅当阶段状态跨阈值（如某阶段全子任务 delivered）时提示模型更新句，否则不碰（跨子项判断，保守）。
- **旧 roadmap 历史 task-log 条目**：迁移时是否回补机器锚？倾向新条目走新格式、历史条目标 legacy 不强补（回写只作用于新归档 change 的新条目）。

## Compliance

- 全局红线：脚本（roadmap-link / 回写勾选）fail-closed + pytest 覆盖坏输入非零退出；判断（完成总结叙述/里程碑句）显式留模型。
- 反静默守卫：回写未做项 MUST 降级标注（hand-off + 摘要），MUST NOT 静默。
- bundle 纪律：sdflow-done / sdflow-roadmap 是 skill 本体、非 workflow bundle 规则；改后跑 `setup.sh`。
- 审查顺序：`/review`（本地 diff）→ push → `/code-review`（远程 PR）。
