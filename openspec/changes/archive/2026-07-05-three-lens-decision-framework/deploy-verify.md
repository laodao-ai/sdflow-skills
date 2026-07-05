# Task 7 — 部署 + 残留终检记录（three-lens-decision-framework）

## 部署（setup.sh，开发 checkout）
`bash setup.sh` 完成——全局 canonical `~/.sdflow/workflow` **接管**指向本开发 checkout：
`~/.skills/sdflow-skills/…/assets/workflow → /Users/cheneyzhao/Documents/04-sdflow-skills/sdflow-init/assets/workflow`。
故编辑后的 BASE-12 / BASE-18 / workflow.md G2 规则 + code-review/spec-review/ship SKILL 已 **live 生效可测**。
> 合并后由运行 checkout `/sdflow-upgrade` 还原 canonical 至运行 checkout（不在本 change 内做）。

## 六权威源残留终检（精确到真该清的格式串，排除 docs/ 镜像）
- `grep "两方后果\|各自后果"`（六权威源）→ **空 ✓**（旧决策后果格式串全清）
- `grep "≥2 方案有把握\|方案有把握自动"`（code-review）→ **空 ✓**（「有把握自动选」主动指令全清）
- **刻意保留**：`两方视角`（tension 本质=voice/主审两方视角，只升级其后果）；canonical T10 文本内「替换旧『有把握自动选』」元引用 + MUST NOT『有把握』条款（ship:23 canonical 自带，正确）。

## 一致性
- `openspec validate three-lens-decision-framework` → **valid ✓**
- ③⑤ 台账格式对齐：`理由(三镜+主次)` 于 ship:23 与 code-review:143 各命中 ✓
- 六处决策后果口径统一为 workflow.md G2「三面后果(系统/用户/开发循环)+主次判定」基准 ✓
- **live 佐证**：setup.sh 后 skill 描述已显示更新措辞（code-review「按 T10 三级协议…按三镜+主次记理由」/ spec-review「三面后果(系统/用户/开发循环)+主次判定」）。

## 实现期发现（交 code-review / hand-off）
- 计划两处 grep 硬门 over-broad（裸「有把握」含 canonical 引用、「两方视角」应保留）——被两个 fresh 实现子代理独立捕获、正确处理，计划门措辞已精确化修正。属计划瑕疵、非实现缺陷。
