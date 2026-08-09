### Task 4: DX 吸收与 roadmap 侧重写

**Blocked-by:** 2
**R-ID:** R-roadmap-planning, R-spec-workflow

DX 领域清单新建 + roadmap review 节重写(镜定义同源注入已在 Task 2 建立):

1. `trigger-catalog.md` 新增 TG-28(developer-facing 交付面触发条件,领域列 devex,spec-review-only,不入 HR-TG)。
2. 新建 `spec-checklists/domains/devex.md`:可判表式条目(TTHW 分档含文本推导规则/错误信息三件套/命名可猜性/默认值/渐进式披露/升级路径/Claude Code Skill DX 清单)。
3. `spec-checklists/domains/frontend.md` 增补 design 镜 litmus/AI-slop 精华 R 项。
4. `sdflow-roadmap/SKILL.md` review 节重写:判定点②(商业化分档)删除;判定留痕总则三判定点改两;恒跑 strategy/plan-eng 双镜(镜职责经 2.5 同源注入托管块承载);失败处置改述(未审待恢复语义不变)。
5. Roadmap sync-only outside voice 接入:site=roadmap-voice,context=design.md Decisions+roadmap.md(>200KB 收敛),run 目录 `.outside-voice/<run-id>/`,前台 --timeout 300 外层 ≥330000ms,⑦ 表映射,失败同族 fallback 带时间预算,task-log 一行 runner/reason_code 留痕。
6. `openspec/INDEX.md` 同步:devex.md 行新增;移除 outside-voice-reuse-guard capability 行与 outside_voice_guard.py 工具行。

- [ ] TG-28 已加入 trigger-catalog.md
- [ ] devex.md 创建且条目为可判表式
- [ ] frontend.md litmus/AI-slop 条目已增补
- [ ] roadmap SKILL 中 autoplan/gstack 引用归零(grep 验证)
- [ ] roadmap review 恒跑双镜 + sync voice 描述完整
- [ ] INDEX.md 同步(新增 devex + 移除 guard 相关行)

