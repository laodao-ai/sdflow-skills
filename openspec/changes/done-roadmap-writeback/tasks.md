# Tasks — done-roadmap-writeback

> Requirement 追溯：**R1**=roadmap 归属镜像与关联判据；**R2**=sdflow-done 归属镜像回写；**R3**=roadmap 生成侧结构化与 change scaffold。
> 〔spec-review-amendment · adr/0014 + grill-amendment 第二轮〕骨架 =「归属镜像投影 + producer 机械生成链」——roadmap 保规划粒度仅借复选框/编码格式、change 归属 roadmap 子任务、scaffold 双向生成、done 盘面镜像。机械活（scaffold 双向生成/归属镜像勾选/阶段 enum 聚合/写锚）进脚本，判断（完成总结叙述/里程碑句）留模型。

## 1. roadmap 生成侧结构化（R3）

- [ ] 1.1 `roadmap-template.md`：子任务复选框**借** tasks 的 `- [ ]`+`N.X.Y` 格式（**保规划粒度**、不下沉实现步）+ 交付标注槽；概览表加 `状态` enum 列〔R3〕
- [ ] 1.2 `task-log-template.md`：条目加机器锚行 `<!-- roadmap-writeback: change=… subtask=… archive=… status=… -->`〔R3〕
- [ ] 1.3 阶段状态 enum 值集 `{planned,in-progress,delivered,deferred}` 落一处机读契约（roadmap-template 与回写脚本共读，不各自硬编码）〔R3〕
- [ ] 1.4 `sdflow-roadmap/SKILL.md`：说明索引层借格式保规划粒度 + change 归属 roadmap 子任务 + 阶段 enum 聚合规则〔R3/R1〕

## 2. change scaffold（双向）+ 关联 lint（R1/R3）

- [ ] 2.1 scaffold（`sdflow-roadmap` 子命令）：`--subtasks 4.D.1,4.D.2` → **双向机械生成** roadmap 索引复选框（结构化格式、保规划粒度）+ change tasks 顶层归属组 `## 4.D.x` + 归属锚 `<!-- roadmap: {name} subtasks: … -->` + proposal 引用；坏参/roadmap 缺/子任务号不存在 fail-closed〔R3/R1〕
- [ ] 2.2 关联 lint：tasks 顶层用 roadmap 式编号 `N.X.Y`（含字母组段）却无 name 锚 → fail-closed 拦（非静默）；改 `sdflow-init/assets/workflow/`（权威源）+ `sdflow-init update` 回灌，不只改仓内〔R1〕
- [ ] 2.3 `tests`：scaffold 双向生成/幂等/坏参、lint 漏锚拦/真无关放行 断言〔R1/R3〕

## 3. done 归属镜像回写消费端（R2）

- [ ] 3.1 `sdflow-done/SKILL.md` 第 3.5 步（**并入第三步 archive 中档子代理**，仿 §2.1 sweep 先例）：L1 读 name 锚 → L2 锚 `subtasks`（归属范围）∩ tasks 归属组盘面完成态 → 归属镜像回写编排〔R2〕
- [ ] 3.2 降级标注 + 反静默：镜像不上（roadmap 改号）/漏锚 → 落 **task-log**（非 hand-off——已随 archive 移走；非仅 stdout 摘要）；不阻塞 archive/merge〔R2〕
- [ ] 3.3 `sdflow-done/SKILL.md` 设计原则区补归属镜像回写步（与 §2.1 sweep 对称登记）+ 第六步摘要模板加回写结果行 + 模型选择表加 3.5 步档位〔R2〕

## 4. 回写脚本（R2）

- [ ] 4.1 归属镜像勾选：扫 tasks `## N.X.Y` 归属组完成态 → 勾 roadmap 同号复选框（**行首锚定** `^- \[ \] {id}`，防散文层 id 误命中；已 `[x]` 幂等 no-op；defer 组不勾）〔R2〕
- [ ] 4.2 阶段状态 enum 机械聚合：从该阶段全子任务复选框推 enum（结构化表解析，防 cell `|`/加粗错位，插入后校验列数与表头一致）〔R2〕
- [ ] 4.3 task-log 机器锚：每 `(change,subtask)` 一条锚，幂等（重跑认锚不重复追加）；模型写叙述、脚本校验锚〔R2〕
- [ ] 4.4 `tests`：归属组全完成镜像勾 / defer 组不误勾 / 归属范围∩盘面 / 阶段 enum 聚合 / 镜像不匹配降级标注 / 幂等 / 不阻塞 断言〔R2〕

## 5. 旧 2 roadmap 迁移（R3）

- [ ] 5.1 `mechanical-layer-hardening`：概览表加状态 enum 列（映射现「就绪度」；「端态A已定」类不可映射值显式补 enum 或标 legacy）+ 子任务复选框借格式 + task-log 新条目走机器锚〔R3〕
- [ ] 5.2 `workflow-cost-optimization`：同上迁移〔R3〕

## 6. 验证（TG-18 测试覆盖）

- [ ] 6.1 关联判据场景：真无关跳过 / 漏锚 fail-closed / L2 归属范围∩盘面 / roadmap 保规划粒度〔R1〕
- [ ] 6.2 归属镜像场景：组全完成勾 / defer 组不误勾 / 阶段 enum 聚合 / 镜像不匹配降级标注〔R2〕
- [ ] 6.3 **正路径真实 dogfood**（补 spec-review Q3/MEMORY 教训）：给某 mlh 剩余子项起 change 走 scaffold→实现→归属镜像回写一次真实全链，非仅 fixture〔R1/R2/R3〕
- [ ] 6.4 时序：回写随第四步 `git add openspec/` 同 commit、无 merge 后额外 commit；完成总结含 archive 路径无 merge hash〔R2〕
- [ ] 6.5 `pytest` 全绿 + `-W error` 0 warning；scaffold/回写/lint 坏输入非零退出〔R1/R2/R3〕

### 测试覆盖图（TG-18）

```
code path                              测试类型
─────────────────────────────────────  ────────────────────────────────
scaffold 双向生成·幂等/坏参 fail-closed  pytest（2.3）
关联 lint·漏锚拦/真无关放行              pytest（2.3）
归属镜像勾选·组全→勾/行首锚定            pytest（4.4/6.2）
defer 组·不误勾（范围∩盘面）             pytest 构造 defer fixture（4.4/6.2）
阶段 enum·机械聚合                       pytest（4.4/6.2）
镜像不匹配·降级标注落 task-log           pytest（4.4）
task-log 机器锚·幂等                     pytest（4.4）
正路径全链·scaffold→实现→镜像            真实 dogfood（6.3）← 补 MEMORY 教训
时序·随归档提交无 merge 后 commit        git 状态核对（6.4）
sdflow-roadmap 模板/迁移(借格式保粒度)   生成产物核对 + validate（1/5）
```

> 脚本（scaffold/回写/lint）pytest 覆盖坏输入非零退出（全局红线）；判断面（完成总结叙述/里程碑句）走场景核对 + dogfood。**正路径 6.3 必须真实全链跑一次**（非仅 fixture）——补 spec-review Q3 + MEMORY「emitter dogfood 独家挖致命」教训。
