# impl-notes — rebuild-sdflow-roadmap-v2（归档材料）

## 4.1 wayfinding 最小实测（2026-07-11，演练 effort=drill-docs-site，阅后即删、本 notes 为存证）

从**真实 `/sdflow-roadmap` 调用起步**（演练议题自带起手显性信号：三阶段+跨天+三子系统），新 SKILL.md（task1 重写版，经 dev setup symlink 生效）驱动全程；路由判档自然发生、非预供目的地路径〔SR-16/E8〕。

| 步 | 操作/约定 | 判定 |
|---|---|---|
| 判定点① | gate-0 不足 + 起手显性信号 → 直入 wayfinder chart（对话显式陈述一行） | ✓ 路由对照表第 1 行命中 |
| 宿主中立探测 | 当前宿主 Claude：`ls ~/.claude/skills/wayfinder` 在场 | ✓ |
| tracker doc preflight | `openspec/matt/issue-tracker.md` + Wayfinding 小节在场 | ✓ |
| 命名权先定 | skill 定 `drill-docs-site` + 字面量调用语（完整 map 路径） | ✓ |
| 无雾预检 | 判有雾（生成器/迁移范围未定）才落盘建 map | ✓ |
| chart | map.md 含**持久字段**（Tracker root/Effort kind）+ 顶部路标行 + 2 票（02 Blocked by 01） | ✓ 落 `roadmaps/{name}/footage/`，未落 `openspec/matt/` |
| claim → resolve | 01 claim→resolved，Resolution 落票 + map 双写（勾框 + Decisions so far 追加） | ✓ |
| frontier | 01 resolved 后 next-ready = 02（Blocked by 解锁） | ✓ |
| 中断恢复 | 02 claim 后中断；「新会话」仅凭 map 路径进入：**从持久字段派生路径**（零语义判别）→ stale claim 追加中断注记后重认领 → 新建票 03 落字段派生根 | ✓ `openspec/matt/` 无误落 |
| 收尾 | 删演练目录 + `git diff openspec/CONTEXT.md openspec/adr/` 对基线**零增量**（演练噪声零 revert 需求）〔SR-4〕 | ✓ |

**方法说明（诚实边界）**：wayfinder chart 的 HITL 广度 grilling 全流程属 matt 套件自身行为（adr/0002 零改动、非本 change 交付面），演练中六操作（chart/child/blocking/frontier/claim/resolve）按 wayfinder SKILL.md + 本 change 改后的 tracker doc 约定**亲执行**，验证对象 = 本 change 新增约定（分流根/持久字段/路标行/再入/重认领/引用边界）的落盘正确性。全程零错位、零丢失。

**结论**：proposal 假设 1（wayfinding 六操作在本地 markdown tracker 上真实可跑）消解——PASS，无需降级 explore+memo，无需回炉 Task 1 措辞。

## 5.1-5.3 存量迁移前置核验与受控延后（Q-C 拍板，2026-07-11 核验）

- **前置①（包无进行中实施 change）**：`openspec list` 当前 active 仅 rebuild-sdflow-roadmap-v2 自身；wco 剩 P2/P3+Phase C 占位、mlh 剩 P4 残项+P6，均无在飞实施 change——①满足。
- **前置②（首个新流程 roadmap 已走通端到端）**：**不满足**——新流程（三件套直写）本 change 才落地，尚无任何真实 roadmap 包走通端到端（4.1 演练为 wayfinding 操作实测，非完整 roadmap 走通）。
- **处置**：按设计门 Q-C 拍板与 design Migration step3 前置，5.1（wco 迁移）/5.2（mlh 迁移）/5.3（总检）本轮 **MUST NOT 执行**，受控延后——非缺口，是拍板的时序约束。排期已登记 todolist（见 T129，显式挂本 change），触发条件 = 首个新流程 roadmap SHIPPED 且目标包无在飞 change；操作序列以 tasks.md 5.1-5.3 + design Migration step3 为准（全节清点表/考古注记四要素/编号不位移/清点表落盘随 commit/per 包 maintain_scan 全部继续有效）。

## 6.1 语境判读处置清单（全仓 grep「四件套」，见 task5 commit）

由 task5 实施时逐命中落档于其 commit 与本节（task5 执行后补写）。

## 6.2 双宿主 wayfinder 装载核验（task6 执行后补写）
