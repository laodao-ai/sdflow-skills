# Design — done-roadmap-writeback

> 〔spec-review-amendment · adr/0014〕本 design 经 7 镜 spec-review + 两次用户目标态纠正**重构骨架**：从「起手锚 + best-effort 回写」（adr/0013）转为「**编号统一 + producer 机械生成投影链**」。根因——spec-review 揭穿「起手锚 producer 契约无机械闭环」（靠人写对锚 = adr/0006 静默跳步）+ 致命误勾（锚 subtask 集起手写死 ≠ 归档实况）。正解：真相源 = 归档 tasks.md 完成态，roadmap 子任务号与 change tasks 号统一，producer 机械生成整链。完整档案见 `adr/0014`（部分 supersede `adr/0013`）。

## Context

`sdflow-done` 收尾六步（核验一致，见 spec-review 接地镜 9 事实）：`0 对账 → 1 verify → 2 hand-off(内含§2.1 sweep) → 3 archive(不commit) → 4 commit(git add openspec/) → 5 merge → 6 摘要`。缺口：全流程对 `openspec/roadmaps/` 零触碰，roadmap 驱动 change 归档后靠人工回填。

**spec-review 根因**：起手锚（adr/0013）把关联信息在 change 起手固化成快照，但 ① 无 lint/gate 校验锚是否真被写对（哲学镜：靠人遵守无门禁 prose MUST = adr/0006 静默跳步）② 锚 subtask 集 ≠ 归档实况交付集（对抗镜：defer 后误勾）。

**两条既有事实**（定新骨架）：
- `sdflow-done` 第 0.3 步已对账 change **tasks.md 复选框完成态**——这是归档时的**现成盘面**，可作真相源。
- 第四步 `git add openspec/` 自动收纳 `openspec/roadmaps/` 回写产物（无需额外 commit）。

## Goals / Non-Goals

**Goals:**
- roadmap 子任务完成态 = change tasks.md 完成态的**直接投影**（编号统一、零映射、盘面即状态）。
- 关联/勾选/阶段状态全**机械**（读盘面 + 同号镜像），真判断仅剩里程碑散文句 + 完成总结叙述。
- producer 机械生成整链（roadmap 结构化 → change scaffold → 镜像回写），不靠人写对编号/锚。
- 无关联 change / 无 roadmap 仓零差异。

**Non-Goals:**
- 不碰 issues 回写（§2.1 sweep）。不做 4.D.4 Review 对账（校验非回写）。
- 不改 opsx:ff（官方）——scaffold 作其外/后的本仓 producer 环，不侵入官方 skill。
- 不全 frontmatter 化 roadmap（叙述层留散文）。不背 dual-read（旧 2 迁移）。
- 暂不做阶段状态 enum 漂移对账（人工编辑 roadmap 后的回读校验）——显式记风险接受（见 Open Questions），不留白。

## Decisions

### D-1 真相源 = 归档实况盘面 + 编号统一

roadmap 子任务号（`4.D.1`）= **唯一编号体系**（跨 change 全局）。roadmap 驱动 change 的 tasks.md **顶层组采用之**：

```
# tasks.md  (change: implement-mlh-p4-small-guards)
<!-- roadmap: mechanical-layer-hardening -->      ← 唯一关联锚：仅 name

## 4.D.1 outside-voice 复用守卫
- [ ] 4.D.1.1 实现   - [ ] 4.D.1.2 测试
## 4.D.2 HR-TG 交集判定
- [ ] 4.D.2.1 …
## 4.D.4 roadmap Review 对账        ← defer 则整组留 [ ]
```

回写 = **镜像**：扫 tasks 顶层 `## N.X.Y` 组，组内全 `[x]` → 勾 roadmap 同号复选框；有 `[ ]` → 不勾。真相源 = tasks 完成态盘面，非起手锚。**Q2 误勾消解**（defer 组在 tasks 就是 `[ ]`）；**编号映射消失**（同号）。

### D-2 producer 机械生成投影链

```
① roadmap 生成侧 (sdflow-roadmap)
   子任务稳定号 4.D.1 + 索引层结构化(复选框/阶段状态enum/task-log机器锚)
              │ 机械生成，不靠人抄
              ▼
② change scaffold (新 producer 能力: sdflow-roadmap 子命令 / roadmap-scaffold)
   从 roadmap 指定子任务 → 生成 tasks.md 骨架:
     <!-- roadmap: {name} --> 锚(机械写) + ## 4.D.x 顶层组(编号抄自 roadmap) + proposal 引用
              │
              ▼
③ 实现: 勾 tasks (defer 组留 [ ])
              │ 纯镜像，同号
              ▼
④ done 回写(第3.5步): 镜像 tasks完成态→roadmap复选框 + 阶段enum聚合 + 完成总结 + 里程碑句
```

每环确定性产出、不靠自觉——同 lens-metric emitter/gate frontmatter「靠人做对 → 机械产出」的升格。

### D-3 关联判据（收缩）

- **L1 关联哪个 roadmap** = 读 tasks.md 的 `<!-- roadmap: {name} -->` 锚（scaffold 机械写）。**漏锚兜底 lint**：tasks 顶层用 roadmap 式编号 `N.X.Y` 却无 name 锚 → **fail-closed 拦，非静默**（编号形态是「roadmap 驱动 change」的机械可判信号，堵住 spec-review B3「漏锚静默吞」）。
- **L2 哪些子任务 + 完成没** = 扫 tasks 顶层组完成态（靠盘面，**不靠锚 subtask**）——Q1 subtask 校验消解。
- **本 change 自身**无 roadmap 锚（非 roadmap 驱动）→ dogfood 无关联跳过分支。

### D-4 索引层结构化 schema（生成侧）

| 索引元素 | 新模板（sdflow-roadmap） | 回写动作 |
|---|---|---|
| 子任务 | `- [ ] 4.D.1 <描述>` + 交付标注槽 | 脚本镜像勾选（**行首锚定** `^- \[ \] {id}\b`，防散文层 id 误命中，spec-review D3） |
| 阶段状态 | 概览表加 `状态` enum 列（`planned/in-progress/delivered/deferred`） | 脚本**机械聚合**：该阶段全子任务复选框 → 无完成=planned/部分=in-progress/全非deferred完成=delivered/显式放弃=deferred（spec-review D4，codex 函数） |
| task-log 条目 | 散文 + 机器锚行 `<!-- roadmap-writeback: change=… subtask=… archive=… status=… -->` | 模型写叙述、脚本校验锚（每 `(change,subtask)` 一锚，幂等，D8） |
| 里程碑句 | 散文（叙述层） | 模型判断改（仅阶段状态跨阈值时提示，D-a） |

enum 值集纳入同一份机读契约（roadmap-template + 回写脚本共读，不各自硬编码，spec-review D9）。

### D-5 回写机械/判断切分

- **脚本机械**：镜像勾选（同号）+ 阶段状态 enum 聚合（从复选框，机械化——spec-review 揭穿原设计误把它当判断）+ 机器锚校验。
- **模型判断（仅两处）**：完成总结叙述（提炼评审价值/defer/下一步）+ 里程碑散文句（跨 6 阶段综述，仅阶段跨阈值时更新，非每次）。
- 3.5 回写步 **model 档位** = 并入第三步 archive 中档子代理（仿 §2.1 sweep 折进第二步先例，spec-review D6）。

### D-6 时序（承 adr/0013 D-4，不变）

回写放第 3.5 步（archive 后 / commit 前），随第四步 `git add openspec/` 提交；完成总结用 change 名 + archive 路径追溯、不写 merge hash（流水线内拿不到自己的 merge hash）。降级标注 MUST 落 **task-log**（在 roadmaps/、随归档 commit），**不落 hand-off**（spec-review codex：hand-off 在 3.5 步已随 archive 移走）、不只落 stdout 摘要。

### D-7 fail-safe（简化：同号镜像 + 显式非静默）

同号镜像消除原 best-effort 三级的散文误命中/subtask 校验补丁。残余分支：
- 无 name 锚 + 无 roadmap 式编号 → 无关联，静默跳过（真无关，正常）。
- 有 roadmap 式编号但无 name 锚 → **lint fail-closed 拦**（起手主路径），或 done 时 **fail-closed 提示留人工**（非静默，堵 B3）。
- name 锚有但 roadmap 目录/子任务号不匹配（roadmap 改号）→ 镜像不上，**降级标注落 task-log 留人工**（残余 best-effort）。
- 回写全程不阻塞 archive/merge（记录维护 altitude）。

### D-8 组件清单（新骨架 scope）

1. **roadmap 生成侧结构化**（sdflow-roadmap 两模板：子任务号 + 阶段状态 enum 列 + task-log 机器锚 + enum 机读契约）
2. **change scaffold**（新 producer 能力：从 roadmap 子任务生成 tasks 骨架 + name 锚 + proposal 引用；机械写编号，不靠人抄）+ 漏锚 lint
3. **done 镜像回写消费端**（sdflow-done 第 3.5 步，并入 archive 中档子代理：扫 tasks 组完成态 → 镜像）
4. **回写脚本**（镜像勾选行首锚定 + 阶段 enum 机械聚合 + task-log 机器锚校验；结构化表解析防 cell `|` 错位）
5. **关联 lint**（tasks roadmap 式编号无 name 锚 → 拦；改 `sdflow-init/assets/workflow/` 权威源再 update，spec-review D7 bundle 纪律）
6. **旧 2 roadmap 迁移**新格式（概览表加 enum 列——现散文「就绪度」值如「端态A已定」需显式映射规则或标 legacy）

### spec-review D1–D10 处置

D3 定位鲁棒**大半消解**（同号结构化、无散文误命中；残余=行首锚定 + 表解析已入 D-4/D-8#4）；D4 enum 机械化（D-4/D-5）；D5 SKILL:195 误引**已删**（本 design 不再引它撑 sdflow-roadmap scope，改用 scaffold 是投影链必要环的正当性）；D6 model 档位（D-5）；D7 bundle 纪律（D-8#5）；D8 幂等键（D-4）；D9 enum 单一源（D-4）；D1/D2 fail-safe 简化（D-7/D-6）；D10 漂移对账（Open Questions 记）。

## Risks / Trade-offs

- **[scaffold 是新 producer 能力、scope 增一环]** → 但它是投影链必要环、机械生成消解 Q1/Q2 一堆补丁，净复杂度可能降；放 sdflow-roadmap 子命令、不侵入 opsx:ff。
- **[tasks 用 roadmap 编号是新约定]** → scaffold 机械生成（非自觉）+ lint 兜底（编号形态可判）；比「起手额外写一行锚」更难漏（编号是必写结构）。
- **[roadmap 改子任务号 → 镜像不上]** → 降级标注留人工（残余 best-effort）；同号体系下概率低。
- **[里程碑句仍判断]** → 仅阶段跨阈值时更新、模型写，脚本不碰；设计门/hand-off 人工复核。
- **[阶段 enum 漂移]** → 人工编辑 roadmap 后 enum 缓存漂移、无 reindex 兜底 → Open Questions 显式记风险接受 + todolist。

## Migration Plan

- 改 sdflow-roadmap 两模板 + 新增 scaffold/回写/lint 脚本（+tests）+ sdflow-done 3.5 步；workflow 规则改 `sdflow-init/assets/workflow/` 再 `sdflow-init update`；跑 `setup.sh`。
- 迁移 2 roadmap：概览表加 enum 列（「就绪度」散文值映射，「端态A已定」类无对应 enum → 标 legacy 或补 enum 值，迁移时显式裁定）。
- **正路径真实 dogfood（spec-review Q3）**：给某个 mlh 剩余子项起 change 时走 scaffold→实现→镜像回写一次真实全链（不只 fixture 单测），补 MEMORY「emitter dogfood 独家挖致命」教训的正路径覆盖。
- 回退：叠加步 + 新脚本，删除即回现状。

## Open Questions

- **scaffold 归属**：sdflow-roadmap 子命令 vs 独立 roadmap-scaffold 脚本？倾向前者（与 roadmap 生成同 skill、单一源）。
- **change 辅助任务编号**（测试/文档等 roadmap 子任务外的活）：放 roadmap 组号下细分（`4.D.1.2 测试`）vs 另起一区（回写只镜像 `N.X.Y` 组）——倾向前者（组内含辅助，组全 `[x]` 才算子任务交付）。
- **阶段 enum 漂移对账**：暂不做，风险接受 + todolist 记（reindex 式回读校验留 backlog）。
- **旧 roadmap「就绪度」不可映射值**（端态A已定）：迁移时补 enum 值 vs 标 legacy——迁移执行时裁定。

## Compliance

- 全局红线：scaffold/回写/lint 脚本 fail-closed + pytest 覆盖坏输入非零退出；判断（完成总结/里程碑句）显式留模型。
- 反静默守卫：漏锚（有编号无 name）fail-closed 非静默；降级标注落 task-log。
- 目标态论证正解：producer 契约机械保证（scaffold），非「人遵守 prose MUST」（adr/0014）。
- bundle 纪律：workflow 规则改 assets/workflow 再 update；sdflow-done/roadmap skill 本体改后跑 setup.sh。
- 审查顺序：`/review` → push → `/code-review`。
