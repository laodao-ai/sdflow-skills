# Hand-off Notes · implement-workflow-optimization-2026-08-p5

## 拍板三问首个真实 dogfood（时序注记，proposal Success Metrics）

**背景**：本 change 交付「拍板三问」（`sdflow:gate-questions` 锚 + `sdflow-spec-review/SKILL.md`
Step4 报告模版三问小节，Task 1 + Task 3）。但本 change **自身**的
`openspec/changes/implement-workflow-optimization-2026-08-p5/spec-review-report.md`
产出于 Task 1/3 落地**之前**——那一轮设计审跑的是旧版 `sdflow-spec-review/SKILL.md`（无
`sdflow:gate-questions` 锚、无三问小节模版），**结构性无法自证**（不是执行疏漏，是时序先后
决定的：先有设计门通过、才有本 change 开工实现，而本 change 实现的正是「下一次」设计门要用的
新报告结构）。

**处置**（proposal.md Success Metrics 已预先记此注记，本条为 change 收尾时的正式挂起）：

- 拍板三问的**首个真实 dogfood** = **本 change 归档之后、任意下一个 OpenSpec change 走
  `/sdflow-spec-review` 产出的第一份 `spec-review-report.md`**。
- 验证方式：该报告的决策登记区顶端应出现「拍板三问」小节（①范围认不认 ②依赖/顺序认不认
  ③风险赌注/HR-TG 对策认不认）+ 紧邻一条 `<!-- sdflow:gate-questions v1 q="scope,deps,risk" -->`
  锚行；`anchor_lint --layer spec-review` 对该报告跑一遍应 `CLEAN`（exit 0）。
- **本条不是本 change 的验收缺口**——是设计阶段已知、proposal 已预告的时序注记，不需要本
  change 补一轮「伪造」的自证；下一次真实设计审自然验证，验证结果不需要专门回填本文件
  （若未来发现三问在真实报告中不生效/被漏放，按正常 issue 记录处理，不属于本 change 遗留）。
- 机验部分（`anchor_lint` 对新旧报告的 PASS/FAIL 行为）已在 Task 1 用 p4 归档报告**副本**
  完成回放核验（原样 FAIL → 手工加段后 PASS，见 `impl-reports/task1-anchor-lint.md`）——
  这证明了锚检查器本身的正确性，与「下一次真实报告是否会正确产出该锚」是两件事，后者才是
  本条挂起的 dogfood。

## 与 roadmap 阶段 5 验收标准的对应

`openspec/roadmaps/workflow-optimization-2026-08/roadmap.md` 阶段 5 验收标准第 3 条
（「拍板三问在下一轮真实 spec-review 报告出现」）本次收尾回填**刻意保持未勾选**，并在该行
下方注明指向本文件——理由同上，不是遗漏。
