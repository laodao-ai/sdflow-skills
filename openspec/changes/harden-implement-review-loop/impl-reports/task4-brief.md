### Task 4: 文件名措辞全量同步（宽重构迁移批次，不计入 3–6 预算）

**Blocked-by:** 3
**R-ID:** R-tickets（出 ticket 模式产出 tracer-bullet ticket）

**交付的行为**：tickets 轨在**指令、bundle 规则、文档、测试断言**四类面上一致地称呼新计划文件名，superpowers 轨的引用原样保留且可逐条归因；历史记录面（归档 change、issues 池、指向归档文件的 docstring 实路径）**一律不动**。

> 这是 `design.md` D5 的宽重构迁移批次：expand（两名并存的 resolver）已由 Task 3 落地，**本序列无 contract 阶段**——旧名对 superpowers 轨永久合法，不存在「删旧形态」这一步。

工作清单权威见 `tasks.md` §5.4、§5.5、§5.6、§5.7（既有测试断言同步）、§5.8、§5.9 与 §7.3。

要点提醒：**MUST NOT 全局 sed**；改共享字符串前先不带 `--include` 全量 grep，测试断言 / 生成物 / docstring 全纳入；`docs/*.html` 这类生成物若有源，改源重跑而非手改产物。

- [ ] skill 指令面（出票落盘路径与全部文件名措辞、done 的引用）已同步
- [ ] bundle 面已同步，且 `step6-writing-plans.md` 明确其**只管 superpowers 轨、文件名不变**；仓内托管副本同步
- [ ] 文档面（overview / map / html / tracker / workflow-skills 三篇 / INDEX）已同步
- [ ] 测试断言面已同步，全量 `/usr/bin/python3 -m pytest` 绿
- [ ] **不动面**核验：归档 change 与 issues 池原样；`adr/0017` 只追加一行指针、正文不改；指向归档文件的 docstring 实路径未改
- [ ] 全仓 `grep -rn "superpowers-plan"`（不带 `--include`）剩余命中**全部**可逐条归因为：① superpowers 轨合法引用 ② 明确标注的历史记录引用 ③ **本 change 在途 plan 文件自身**（在途禁改名，见 Global Constraints）

---

