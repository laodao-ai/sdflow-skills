### Task 2: T10 拆成 `T10-choice` 与 `review-loop-breaker` 两条具名规则

**Blocked-by:** 1
**R-ID:** R-stage3（阶段三过设计门后连续自动跑到 merge）, R-tension（outside-voice tension 不静默采纳）, R-tickets（出 ticket 模式产出 tracer-bullet ticket）, R-dualaxis（每 ticket 双轴审加修复环）

**交付的行为**：阶段三「≥2 方案自动选」与「同一发现反复未消解」两个语义不同的场景不再共用一个标签——前者具名 `T10-choice`（15 处规范性落点措辞统一、②步统一升 strong 档），后者具名 `review-loop-breaker` 独立成文（不再出现 "T10" 字样，身份键跨轮稳定，三级处置收敛到互斥终态）。术语表登记两条新规则与 "T10" 的历史别名关系。

工作清单权威见 `tasks.md` §2（2.1–2.11）、§3（3.1–3.4）、§6.3–6.4 与 §7.1；落点清单与统一计数口径见 `design.md`「T10 scope-check」表。

要点提醒：【别名保留】那 1 处**确认不改**；【不动】那 2 处的 "T10" 字样 **MUST 原样保留**（delta MODIFIED 是整段替换，极易静默删除）；行号只作阅读索引，定位一律用原文片段锚。

- [ ] Group A 15 处规范性落点全部改名为 `T10-choice`，②步统一声明 strong 档，且「按三镜 + 主次」限定词在两处 spec 落点补回
- [ ] `review-loop-breaker` 就地独立成文：不出现 "T10" 字样，写明触发条件、②步 strong 档仲裁
- [ ] 身份键为「同文件 + 规范化问题指纹」，明写**行号只作定位不作身份**
- [ ] 三级处置为互斥终态：不成立→关闭；成立且可修→strong 档 fixer 修复并**仅复验一次**；成立但不可修→进 buglist 并停；MUST NOT 停在「已确认成立」而无后续动作
- [ ] Group B ①档保留并附一句「预期极少触发」的原因说明
- [ ] `CONTEXT.md` 术语条目登记两条具名规则 + "T10" 别名关系；`adr/0031` 仅追加一行指针、正文不改
- [ ] 全仓 `grep -rn "T10"`（不带 `--include`）复核：Group A 措辞一致、Group B 落点零 "T10" 字样、【不动】2 处与【别名保留】1 处**原样健在未被误删**

---

