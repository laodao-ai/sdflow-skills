## 1. sdflow-implement 档位解析机制〔R:sdflow-implement 档位解析与声明〕

- [ ] 1.1 给 `sdflow-implement/SKILL.md` 新增"第零步:宿主/档位解析"四步(清脏→预检→捕获退出码→eval后校验),逐字对齐 `sdflow-code-review`/`sdflow-spec-review`/`sdflow-done` 现有模板
- [ ] 1.2 implementer dispatch prompt 改为引用 `$SDFLOW_TIER_MID`,不内联模型名
- [ ] 1.3 Standards 轴/Spec 轴 dispatch prompt 改为引用 `$SDFLOW_TIER_MID`
- [ ] 1.4 fix 子代理 dispatch prompt 改为引用 `$SDFLOW_TIER_MID`

## 2. T10 标签拆分——Group A(≥2方案语义,继续复述,②步升 strong)〔R:阶段三过设计门后连续自动跑到 merge / R:outside-voice tension 不静默采纳 / R:出ticket模式产出tracer-bullet ticket〕

- [ ] 2.1 `sdflow-init/assets/workflow/workflow.md:106` canonical 定义②步补 strong 限定
- [ ] 2.2 `sdflow-ship/SKILL.md:164` 复述②步补 strong 限定
- [ ] 2.3 `sdflow-code-review/SKILL.md:283` 复述②步补 strong 限定
- [ ] 2.4 `openspec/specs/spec-workflow/spec.md`(阶段三过设计门后连续自动跑到 merge)②步补 strong + 补回丢失的"按三镜+主次"措辞(delta 已含,核对归档同步)
- [ ] 2.5 `openspec/specs/spec-workflow/spec.md`(outside-voice tension 不静默采纳)code-review 自动裁决②步补 strong(delta 已含,核对归档同步)
- [ ] 2.6 `sdflow-implement/SKILL.md:203,271`(出票模式"粒度争议")升 strong
- [ ] 2.7 `sdflow-implement/SKILL.md:282,545`(全ticket语义一致性自扫"矛盾裁决")升 strong
- [ ] 2.8 `openspec/specs/impl-orchestration/spec.md`(出ticket模式产出tracer-bullet ticket)"粒度争议"与"一致性自扫矛盾裁决"两处升 strong(delta 已含,核对归档同步)

## 3. T10 标签拆分——Group B(熔断仲裁语义,独立成文,②步升 strong)〔R:每ticket双轴审加修复环〕

- [ ] 3.1 `sdflow-implement/SKILL.md:490-493` 熔断仲裁段落独立改写,不再出现"T10"字样,就地描述触发条件(同一发现连续2轮re-review仍未消解)与三级处置,②步注明用 strong 档

## 4. 测试范围分层 + 实现验证收尾 ticket〔R:执行模式串行工作frontier并以文件交接 / R:出ticket模式产出tracer-bullet ticket〕

- [ ] 4.1 `sdflow-implement/SKILL.md`"每 ticket 派 fresh implementer"节的测试契约,从"结束前跑一次全套件"改为"单元测试 + 本票声明的 e2e 场景",MUST NOT 跑全量集成/e2e 套件
- [ ] 4.2 `sdflow-implement/SKILL.md` 出票模式新增"实现验证"收尾 ticket 规则:`Blocked-by` 全部功能票号,不计入 3-6 张预算,验收标准="聚合套件(单元+集成+e2e)运行且全部通过"
- [ ] 4.3 明确该收尾 ticket 走跟普通 ticket 相同的 implementer + 双轴审 + fix 循环:Spec 轴核验聚合套件确实运行且通过,Standards 轴核验修复方式未靠删除/弱化断言蒙混过关
- [ ] 4.4 `sdflow-done/SKILL.md` 补一句:verify 引用该收尾 ticket 自身的 commit/报告作为"聚合覆盖"需求的证据锚,不新增 verify 主动执行职责

## 5. 一致性收尾核验

- [ ] 5.1 全仓 `grep -rn "T10"` 复核:Group A 落点措辞一致(含"按三镜+主次"限定词)、Group B 落点(`sdflow-implement:490-493`)不再出现"T10"字样、`sdflow-implement:372` 与 `impl-orchestration/spec.md:60` 两处尾部引用未被误改
- [ ] 5.2 `grep -n "model-tier\|SDFLOW_TIER" sdflow-implement/SKILL.md` 确认不再是零命中(对照 C1 现状)
- [ ] 5.3 `openspec validate harden-implement-review-loop --strict --type change` 通过
- [ ] 5.4 手动核对 `openspec/specs/spec-workflow/spec.md` 与 `openspec/specs/impl-orchestration/spec.md` 两份 delta 归档后,内容与 `sdflow-implement/SKILL.md`/`workflow.md`/`sdflow-ship/SKILL.md`/`sdflow-code-review/SKILL.md` 的实际改动逐条对得上(防止 delta 与实现漂移)
