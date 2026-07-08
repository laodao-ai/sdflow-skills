# Tasks — done-roadmap-writeback

> Requirement 追溯：**R1**=roadmap 回填降摩擦助手（判断留人）；**R2**=关联声明轻量、漏则退现状。
> 〔spec-review-amendment · adr/0015〕最小核骨架——机械搬运（盘面读 + 草稿骨架）自动化、判断（算不算完成/价值叙述/阶段状态/deferred）留人确认。**弃** scaffold/enum 聚合/编号统一/迁移。

## 1. 回填草稿生成（R1）

- [ ] 1.1 读确定性盘面：archive 路径 + verify=PASS frontmatter + merge + tasks 完成态 + 验证数字（pytest 数）——复用 ship_gate/done 已有的盘面读取，不新造真相源〔R1〕
- [ ] 1.2 生成候选复选框列表：借 roadmap 现状 `- [ ] {id}` 格式定位 change 声明关联的子任务，列「建议勾」候选（定位不到 → 标「留人工」，不猜写）〔R1〕
- [ ] 1.3 生成 task-log 完成总结骨架：预填机械锚（change 名/merge/archive 路径/pytest 数）+ 交付标注模板；价值叙述留空位给人补〔R1〕
- [ ] 1.4 （可选）轻脚本辅助读盘面拼骨架 + `tests`（盘面缺失/定位不到 → fail-closed 或标留人工）；若纯 done 指令步则免脚本〔R1〕

## 2. sdflow-done 收尾提示步（R1）

- [ ] 2.1 `sdflow-done/SKILL.md` hand-off 步：检测 change 关联 → 生成回填草稿写进 `hand-off.md` + 提示「检测到关联 roadmap {name}，草稿见下，请过目后回填」；**阶段三无门**——不弹窗、不阻塞归档/merge〔R1〕
- [ ] 2.2 `sdflow-done/SKILL.md` 设计原则区登记：与 `§2.1 issues sweep` 对称——sweep 自动 triage / roadmap 回填**助人确认**（完成判定含判断，非无人干预）〔R1〕
- [ ] 2.3 助手 MUST NOT 写 change 产物文件（tasks/proposal）——只读盘面 + 写 hand-off（避 C1）；MUST NOT 机械改 roadmap / 聚合 enum（判断留人）〔R1〕

## 3. 关联声明约定（R2）

- [ ] 3.1 change 轻量关联标记约定 `<!-- roadmap: {name} -->`（proposal/tasks）或 done `--roadmap {name}`；done 检测逻辑〔R2〕
- [ ] 3.2 未声明 → 退现状人工回填、不 fail-closed 阻塞；MAY 对疑似 roadmap 驱动轻量提示〔R2〕
- [ ] 3.3 （若关联约定入 workflow 规则）改 `sdflow-init/assets/workflow/` 权威源 + `sdflow-init update` 回灌（bundle 纪律）〔R2〕

## 4. 验证（TG-18）

- [ ] 4.1 关联场景：声明关联 → 草稿进 hand-off（含机械锚）；判断留人（助手不改 roadmap/不聚合 enum）〔R1〕
- [ ] 4.2 边界：未声明 → 退现状不阻塞；助手不碰 change 产物文件（避 C1）；盘面缺/定位不到 → 标留人工〔R1/R2〕
- [ ] 4.3 dogfood：本 change 无关联 → 跳过；构造带 `<!-- roadmap: {name} -->` 标记的 fixture → 验证草稿生成〔R1/R2〕
- [ ] 4.4 若加脚本：`pytest` 覆盖坏输入（盘面缺失/定位不到）非零退出或标留人工；`-W error` 0 warning〔R1〕

### 测试覆盖图（TG-18）

```
code path                          测试类型
─────────────────────────────────  ────────────────────────────────
读确定性盘面·缺失 fail-closed/留人工  pytest 或场景核对（1.4/4.2）
候选复选框定位·借现状格式/定位不到留人工 场景核对（4.1/4.2）
task-log 骨架·机械锚预填             场景核对（4.1）
不碰 change 产物文件（避 C1）         静态核对 + 场景（2.3/4.2）
判断留人·助手不改 roadmap/不聚合 enum  场景核对（4.1）
关联声明/未声明退现状不阻塞           场景核对（4.2）
带标记 fixture→草稿生成              dogfood（4.3）
```

> 最小核：机械部分（盘面读 + 骨架）若脚本化则 pytest 覆盖坏输入；判断部分（算不算完成/价值叙述/阶段状态/deferred）走人确认、场景核对。**无** scaffold/enum/编号统一/迁移的重机制，无对应测试面。
