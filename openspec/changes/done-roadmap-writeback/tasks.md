# Tasks — done-roadmap-writeback

> Requirement 追溯：**R1**=roadmap 关联锚契约；**R2**=sdflow-done best-effort 回写；**R3**=roadmap 生成索引层结构化。
> 〔grill-amendment · adr/0013〕scope 经 grill 扩为 6 件（含改 `sdflow-roadmap` 生成格式 + 迁 2 roadmap + 脚本）；机械活（勾选/阶段状态/写锚）进脚本，判断（完成总结叙述/里程碑句）留模型。

## 1. 关联锚契约

- [ ] 1.1 定义关联锚格式 `<!-- roadmap: {name} phase: {PN} subtask: {id,...} -->` 机读规范，落一处契约定义（复用 `lens-metric-contract.md` 机读块范式）〔R1〕
- [ ] 1.2 起手 MUST 带锚规范：workflow 规则 / CLAUDE 托管区块声明「roadmap 驱动 change 的 proposal MUST 含关联锚」〔R1〕

## 2. roadmap-link 写锚脚本

- [ ] 2.1 `roadmap-link` 脚本：`--change/--roadmap/--phase/--subtask` → 机械拼锚行写入 proposal 头部，幂等（已有锚更新而非重复），格式非法/缺参 fail-closed 非零退出〔R1〕
- [ ] 2.2 `tests`：坏参数 / 缺 roadmap / 多 subtask 列表 / 幂等重跑 断言〔R1〕

## 3. sdflow-roadmap 生成侧结构化

- [ ] 3.1 `roadmap-template.md`：概览表加 `状态` enum 列（planned/in-progress/delivered/deferred）+ 子任务固定「交付标注槽」位〔R3〕
- [ ] 3.2 `task-log-template.md`：条目加机器锚行 `<!-- roadmap-writeback: … -->` 格式〔R3〕
- [ ] 3.3 `sdflow-roadmap/SKILL.md`：说明索引层/叙述层约定 + 状态 enum 值集 + 关联锚起手要求〔R3/R1〕

## 4. 旧 2 roadmap 迁移

- [ ] 4.1 `mechanical-layer-hardening`：概览表加状态 enum 列（映射现散文「就绪度」）+ task-log 新条目走机器锚（历史条目标 legacy 不强补）〔R3〕
- [ ] 4.2 `workflow-cost-optimization`：同上迁移新格式〔R3〕

## 5. done 回写消费端 + 回写脚本

- [ ] 5.1 `sdflow-done/SKILL.md` 第 3.5 步：archive 后 / commit 前，读锚（L1 name / L2 subtask）→ best-effort 回写编排（三级）〔R2〕
- [ ] 5.2 回写脚本：勾选（定位 subtask id 复选框行→`[x]` + 交付标注）+ 阶段状态 enum cell 更新（机械写；部分定位 best-effort、全无法解析 fail-closed）〔R2〕
- [ ] 5.3 回写脚本：task-log 机器锚校验 + 幂等（模型写叙述、脚本校验锚在场，anchor_lint 式）〔R2〕
- [ ] 5.4 降级标注 + 反静默：未定位项写 hand-off + 最终摘要「未能自动回写：{subtask}」；回写全程不阻塞 archive/merge〔R2〕
- [ ] 5.5 `sdflow-done/SKILL.md` 设计原则区补回写步说明（与 §2.1 sweep 对称登记）+ 第六步最终摘要模板加回写结果行（全写/部分+标注/跳过/fail-closed 四态）〔R2〕
- [ ] 5.6 `tests`：回写脚本全定位 / 部分定位+标注 / 全无法解析 fail-closed / 幂等 / 不阻塞 断言〔R2〕

## 6. 验证（TG-18 测试覆盖）

- [ ] 6.1 三级场景端到端：无锚跳过 / 全定位全写 / 部分定位+标注 / 全无法解析 fail-closed〔R1/R2〕
- [ ] 6.2 时序核对：回写随第四步 `git add openspec/` 进同一 commit、无 merge 后额外 commit；完成总结含 archive 路径、无 merge hash〔R2〕
- [ ] 6.3 dogfood：本 change 自身无锚 → 跳过；构造带锚 fixture roadmap → 回写三级〔R1/R2〕
- [ ] 6.4 `pytest` 全绿 + `-W error` 0 warning；脚本坏输入非零退出〔R1/R2/R3〕

### 测试覆盖图（TG-18）

```
code path                              测试类型
─────────────────────────────────────  ────────────────────────────────
roadmap-link 写锚·幂等/坏参 fail-closed  pytest（2.2）
L1/L2 读锚·无锚跳过                      pytest + 场景核对（6.1/6.3）
勾选+阶段状态 cell·机械写                pytest（5.6）
部分定位·best-effort+降级标注            pytest 构造缺 id fixture（5.6/6.1）
全无法解析·fail-closed                   pytest 坏格式 fixture（5.6）
task-log 机器锚·幂等校验                 pytest（5.6）
时序·随归档提交无 merge 后 commit        git 状态核对（6.2）
不阻塞 archive/merge                     场景核对（6.1）
sdflow-roadmap 模板/迁移                 生成产物核对 + validate（3/4）
```

> 有脚本（roadmap-link / 回写）→ pytest 覆盖坏输入非零退出（全局红线）；判断面（完成总结叙述/里程碑句）走场景核对 + dogfood，非 pytest（对应 verify 阶段机验锚点）。
