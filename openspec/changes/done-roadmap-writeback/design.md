# Design — done-roadmap-writeback

> 〔spec-review-amendment · adr/0014 + grill-amendment 第二轮〕骨架 = 「**归属镜像投影 + producer 机械生成链**」。经两轮 grill + 7 镜 spec-review + 三次用户目标态纠正收敛：① 起手锚 producer 契约无机械闭环 → scaffold 机械生成；② best-effort 误套正确性范式 → 盘面镜像；③ 「tasks 号=roadmap 号」强编号统一粒度失配 → **roadmap 保规划粒度仅借格式、change 归属 roadmap 子任务**。完整档案见 `adr/0014`（含第二轮 grill 粒度精化，部分 supersede `adr/0013`）。

## Context

`sdflow-done` 收尾六步（接地镜 9 事实核验一致）：`0 对账 → 1 verify → 2 hand-off(§2.1 sweep) → 3 archive(不commit) → 4 commit(git add openspec/) → 5 merge → 6 摘要`。缺口：全流程对 `openspec/roadmaps/` 零触碰，靠人工回填。

**两轮 grill / spec-review 收敛的真相源与粒度**：
- 真相源 = **归档实况盘面**（change tasks.md 完成态，第 0.3 步已对账），非起手锚快照。
- **粒度失配实证**：roadmap 复选框 `4.C.1` = 一次 change 粒度；change tasks `1.1~7.x`（lens-metric-emit 实测 7 功能组 30+ 任务）= 该 change 内部实现分解，天生细一层。故 roadmap 与 tasks **不能靠「同号」对齐**——roadmap 保规划粒度、仅借复选框/编码**格式**，change **归属** roadmap 子任务。

## Goals / Non-Goals

**Goals:**
- roadmap 子任务完成态 = change tasks 完成态的**盘面镜像**（归属对齐、盘面即状态）。
- 关联/勾选/阶段状态全机械（scaffold 生成 + 盘面镜像），真判断仅剩里程碑散文句 + 完成总结叙述。
- producer 机械生成整链（roadmap 结构化 → scaffold 双向写 → 镜像回写），不靠人写对。

**Non-Goals:**
- 不碰 issues（§2.1 sweep）。不做 4.D.4 Review 对账。
- 不改 opsx:ff（官方）——scaffold 作其外/后的本仓 producer 环。
- **roadmap MUST NOT 下沉到 openspec tasks 实现步粒度**（只借复选框/编码格式，保规划粒度）。
- 不全 frontmatter 化 roadmap。不 dual-read（旧 2 迁移）。
- 暂不做阶段 enum 漂移对账（风险接受 + todolist）。

## Decisions

### D-1 真相源 = 归档盘面 + 归属镜像

roadmap **保规划粒度**（子任务 `4.C.1` = 一次 change / 一个交付点），**仅借鉴** tasks 的复选框 `- [ ]` + 层级编码 `N.X.Y` **格式**使其机械可镜像。change **归属** roadmap 子任务：

```
roadmap (规划粒度, 借格式不借粒度):
  #### 4.D · 小校验器组
  - [ ] 4.D.1 outside-voice 复用守卫      ← 复选框+编码格式(借tasks), 粒度=change级交付点
  - [ ] 4.D.2 HR-TG 交集判定
  - [ ] 4.D.4 roadmap Review 对账

change tasks.md (合批做 4.D.1/4.D.2/4.D.4):
  <!-- roadmap: mechanical-layer-hardening subtasks: 4.D.1,4.D.2,4.D.4 -->   ← 归属锚(scaffold写)
  ## 4.D.1 <归属标签>          ← 顶层组借 roadmap 子任务号作归属标签
  - [ ] 4.D.1.1 实现  - [ ] 4.D.1.2 测试   ← 组内=change 自己的实现分解
  ## 4.D.2 …
  ## 4.D.4 …                  ← defer 则整组留 [ ]
```

回写 = **归属镜像**：扫 tasks 归属组完成态 → 勾 roadmap 同号复选框（组全 `[x]`→勾、有 `[ ]`→不勾）。**实际勾选 = 归属范围（锚 subtasks）∩ tasks 盘面完成**。**Q2 误勾消解**（defer 组 `[ ]` 不勾，盘面兜底）。**单子任务 change**（对应一个 roadmap 复选框如 4.C.1）：一个归属组、组内实现分解自由。

### D-2 producer 机械生成投影链（scaffold 双向）

```
① roadmap 生成侧 (sdflow-roadmap): 子任务组(规划粒度) + 索引层结构化(复选框/编码格式/阶段enum/task-log机器锚)
              │ scaffold 起 change 时机械生成，不靠人写
              ▼
② change scaffold (新 producer 能力: sdflow-roadmap 子命令): --subtasks 4.D.1,4.D.2,4.D.4 →
     双向同源写: ├─ roadmap 索引复选框(若规划期只有组、此时补细复选框, 结构化格式)
                ├─ change tasks 归属组骨架(## 4.D.x)
                └─ 归属锚 <!-- roadmap: {name} subtasks: … -->  + proposal 引用
              │
              ▼
③ 实现: 勾 change tasks (defer 组留 [ ])
              │ 归属镜像, 盘面兜底
              ▼
④ done 回写(第3.5步): 镜像 tasks归属组完成态→roadmap复选框 + 阶段enum聚合 + 完成总结 + 里程碑句
```

每环确定性产出、不靠自觉——同 lens-metric emitter/gate frontmatter「靠人做对 → 机械产出」升格。

### D-3 关联判据

- **L1 关联哪个 roadmap** = 读 tasks 的 `<!-- roadmap: {name} subtasks: … -->` 锚 name（scaffold 机械写）。**漏锚兜底 lint**：tasks 顶层用 roadmap 式编号 `N.X.Y`（含字母组段，如 `## 4.D.1`）却无 name 锚 → **fail-closed 拦，非静默**（编号形态是机械可判信号，堵 spec-review B3）。
- **L2 哪些子任务完成** = 锚 `subtasks`（归属范围）∩ tasks 归属组盘面完成态。**subtasks 是关联范围声明（这个 change 打算做哪些复选框），非完成声明**；完成看 tasks 盘面。
- **本 change 自身**无 roadmap 锚 → dogfood 无关联跳过分支。

### D-4 roadmap 借结构化格式（保规划粒度）+ 阶段 enum

| 索引元素 | 新模板（sdflow-roadmap，规划粒度） | 回写动作 |
|---|---|---|
| 子任务复选框 | `- [ ] 4.D.1 <规划级描述>` + 交付标注槽（**借** tasks 复选框/编码格式，**粒度=change 级**、不下沉实现步） | 脚本镜像勾选（**行首锚定** `^- \[ \] {id}\b`，防散文层 id 误命中，spec-review D3） |
| 阶段状态 | 概览表加 `状态` enum 列（`planned/in-progress/delivered/deferred`，值集入机读契约） | 脚本**机械聚合**：该阶段全子任务复选框 → 无完成=planned/部分=in-progress/全非deferred完成=delivered/显式放弃=deferred（spec-review D4 codex 函数） |
| task-log 条目 | 散文 + 机器锚 `<!-- roadmap-writeback: change=… subtask=… archive=… status=… -->` | 模型写叙述、脚本校验锚（每 `(change,subtask)` 一锚，幂等，D8） |
| 里程碑句 | 散文（叙述层，规划粒度） | 模型判断改（仅阶段跨阈值时，D-a） |

### D-5 回写机械/判断切分

- **脚本机械**：归属镜像勾选（同号）+ 阶段 enum 聚合（从复选框，机械化）+ 机器锚校验。
- **模型判断（仅两处）**：完成总结叙述 + 里程碑散文句（跨阶段综述，仅阶段跨阈值时更新）。
- 3.5 回写步 model 档位 = 并入第三步 archive 中档子代理（仿 §2.1 sweep 先例，spec-review D6）。

### D-6 时序（承 adr/0013，不变）

回写放第 3.5 步（archive 后 / commit 前），随第四步 `git add openspec/` 提交；完成总结用 change 名 + archive 路径追溯、不写 merge hash。降级标注 MUST 落 **task-log**（不落 hand-off——已随 archive 移走，spec-review codex；不只落 stdout 摘要）。

### D-7 fail-safe（归属镜像 + 显式非静默）

- 无 name 锚 + 无 roadmap 式编号 → 无关联，静默跳过（真无关，正常）。
- 有 roadmap 式编号但无 name 锚 → **lint fail-closed 拦**（起手），或 done **fail-closed 提示留人工**（非静默，堵 B3）。
- 归属锚 subtasks 里某号在 roadmap 找不到同号复选框（roadmap 改号）→ **降级标注落 task-log 留人工**（残余 best-effort）。
- 回写全程不阻塞 archive/merge（记录维护 altitude）。

### D-8 组件清单（scope）

1. **roadmap 生成侧结构化**（sdflow-roadmap 两模板：借复选框/编码格式保规划粒度 + 阶段 enum 列 + task-log 机器锚 + enum 机读契约）
2. **change scaffold**（新 producer 能力：sdflow-roadmap 子命令，`--subtasks` → 双向写 roadmap 复选框 + change tasks 归属骨架 + 归属锚，机械不靠人）+ 漏锚 lint
3. **done 归属镜像回写消费端**（sdflow-done 3.5 步，并入 archive 中档子代理）
4. **回写脚本**（归属镜像勾选行首锚定 + 阶段 enum 机械聚合 + task-log 机器锚校验；结构化表解析防 cell `|` 错位）
5. **关联 lint**（tasks roadmap 式编号无 name 锚 → 拦；改 `sdflow-init/assets/workflow/` 权威源再 update，spec-review D7 bundle 纪律）
6. **旧 2 roadmap 迁移**（概览表加 enum 列 + 子任务复选框借格式；「端态A已定」类不可映射值显式补 enum 或标 legacy）

### spec-review D1–D10 处置

D3 定位鲁棒（行首锚定 + 表解析，D-4/D-8#4）；D4 enum 机械化（D-4/D-5）；D5 SKILL:195 误引**已删**（改用 scaffold 是投影链必要环的正当性）；D6 model 档位（D-5）；D7 bundle 纪律（D-8#5）；D8 幂等键（D-4）；D9 enum 单一源（D-4）；D1/D2 fail-safe 简化（D-7/D-6）；D10 漂移对账（Open Questions 记）。

## Risks / Trade-offs

- **[scaffold 新 producer 能力 + 双向写]** → 双向机械生成消解 Q1/Q2 一堆补丁，净复杂度可能降；放 sdflow-roadmap 子命令、不侵入 opsx:ff。
- **[roadmap 借格式的编号约定]** → scaffold 机械生成（非自觉）+ lint 兜底（编号形态可判）。
- **[roadmap 改子任务号 → 镜像不上]** → 降级标注留人工（残余 best-effort）；概率低。
- **[里程碑句仍判断]** → 仅阶段跨阈值时更新、模型写；人工复核兜底。
- **[阶段 enum 漂移]** → 人工编辑 roadmap 后 enum 缓存漂移、无 reindex 兜底 → Open Questions 显式记风险接受 + todolist。

## Migration Plan

- 改 sdflow-roadmap 两模板 + 新增 scaffold/回写/lint 脚本（+tests）+ sdflow-done 3.5 步；workflow 规则改 `sdflow-init/assets/workflow/` 再 `sdflow-init update`；跑 `setup.sh`。
- 迁移 2 roadmap：概览表加 enum 列 + 子任务复选框借格式（现散文「就绪度」值映射，「端态A已定」类不可映射 → 补 enum 或标 legacy，迁移时裁定）。
- **正路径真实 dogfood（spec-review Q3）**：给某 mlh 剩余子项起 change 走 scaffold→实现→镜像回写一次真实全链（非仅 fixture）。
- 回退：叠加步 + 新脚本，删除即回现状。

## Open Questions

- **scaffold 归属**：sdflow-roadmap 子命令 vs 独立脚本？倾向前者（与 roadmap 生成同 skill、单一源）。
- **scaffold 与 opsx:ff 时序**：opsx:ff 生成 change 骨架（含 tasks），scaffold 补 roadmap 归属编号 + 锚——先后/覆盖策略待定（倾向 scaffold 在 opsx:ff 后补写归属组头 + 锚，不覆盖 opsx 内容）。
- **change 辅助任务**（测试/文档等归属子任务外的活）：放归属组下 vs 单独区——倾向组内（组全 `[x]` 含辅助才算子任务交付）。
- **阶段 enum 漂移对账**：暂不做，风险接受 + todolist。
- **旧 roadmap 不可映射「就绪度」值**（端态A已定）：补 enum vs 标 legacy——迁移时裁定。

## Compliance

- 全局红线：scaffold/回写/lint 脚本 fail-closed + pytest 覆盖坏输入非零退出；判断（完成总结/里程碑句）显式留模型。
- 反静默守卫：漏锚 fail-closed 非静默；降级标注落 task-log。
- 目标态论证正解：producer 契约机械保证（scaffold 双向生成），非「人遵守 prose MUST」；roadmap 与 tasks 各保粒度、不互拖（adr/0014）。
- bundle 纪律：workflow 规则改 assets/workflow 再 update；skill 本体改后跑 setup.sh。
- 审查顺序：`/review` → push → `/code-review`。
