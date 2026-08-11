### Task 5: docs 与全仓扫尾

**Blocked-by:** 1,2,3,4
**R-ID:** R7

**docs 收口**：`docs/workflow-skills/impl-pipeline-matt-vs-superpowers.md` 头部加 obsolete 标注（一行，指向 adr/0042）。现役视图文档同步：`docs/workflow-overview.md` / `docs/workflow-map.md`(+`.html`) / `docs/workflow-console.html` / `docs/criteria-mechanization-tracker.md` 去 superpowers 管线/writing-plans 阶段叙述。

**ADR 互指**：`adr/0033` 头部加一行 `> **Superseded by [adr/0042](./0042-tickets-sole-impl-pipeline.md)**` 指针；`adr/0042` 加一句 supersede adr/0033 声明（互指，两文正文其余逐字不动）。

**CLAUDE.md 手写段修正**：`CLAUDE.md`:215（托管区块外手写 prose）改写为不依赖 `impl-pipeline` 键存在性的表述。

**grep 扫尾**：`grep -rn "superpowers" --exclude-dir=archive --exclude-dir=.git` 在运行时路径（scripts / SKILL / bundle assets / specs 主文件）仅剩合法残留清单（upstream-watch 追踪目标、superpowers 插件非管线技能引用、docs 历史参考、adr 历史文本）——Success Metrics 判据。

**全仓 pytest**：`/usr/bin/python3 -m pytest` 全绿（含保留半场、gate 回归、hack 守卫全量）；verify-report 对 Success Metrics 第三条（ship 直连 e2e）显式标注「事后锚——由下一真实 change 的 /sdflow-ship 首跑承接」，MUST NOT 留白或假绿。

- [ ] `impl-pipeline-matt-vs-superpowers.md` 头部已加 obsolete 标注
- [ ] 现役视图文档已去 superpowers 管线叙述
- [ ] ADR 0033/0042 已互加指针
- [ ] `CLAUDE.md`:215 手写段已修正
- [ ] grep 扫尾判据通过（运行时路径仅剩合法残留）
- [ ] [e2e] 全仓 `/usr/bin/python3 -m pytest` 全绿

