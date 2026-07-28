### Task 5: 每票测试范围分层 + 强制「实现验证」收尾票 + gate 第四道校验

**Blocked-by:** 3
**R-ID:** R-frontier（执行模式串行工作 frontier）, R-tickets（出 ticket 模式产出 tracer-bullet ticket）, R-tier（收尾票的双轴审定制）

**交付的行为**：每 feature ticket 的 implementer 只跑「单元 + 本票声明的 e2e 场景 + 本票 `Blocked-by` 链上模块的集成测试」，不再无差别付全套件成本；出票模式恒产出一张不计预算的「实现验证」收尾票承担聚合回归，其套件发现走**真跑一遍让工具自己判**的契约（MUST NOT 解析构建文件）、缺层记「未覆盖」而非罢工；收尾票的存在与位置由 `ship_gate` 的第四道校验机械保证，旧名 plan grandfather 跳过；`sdflow-done` 的 verify 按管线条件化地引用该票证据锚。

工作清单权威见 `tasks.md` §4（4.1–4.10）、§6.1 与 §7.6。

要点提醒（皆已在 Global Constraints 逐字给出）：禁令是「MUST NOT 跑**与本票无依赖关系**的集成/e2e」的中间档、不是绝对禁令；收尾票三处执行契约定制（豁免 red-before-green / 证据锚不依赖 commit / Standards 轴核验范围含「加 skip」）；verify 锚语义 MUST NOT 写成「最终全量回归通过」，且 **MUST 按管线条件化**——superpowers 轨判「不适用」而非 gap。

- [ ] 每票测试范围契约已改写，「本票声明的 e2e 场景」的表达方式已在 ticket 骨架层面定义（验收标准标注为 e2e 的条目即是；未标注则该票无 e2e）
- [ ] 出票模式恒含「实现验证」收尾票的规则落地：`Blocked-by` 全部功能票号、不计入 3–6 预算、`R-ID: all`
- [ ] 聚合套件发现契约五条（命令来源优先级 / 真跑一遍 / 缺层不罢工 / 证据 schema / 四类失败分诊）完整落地
- [ ] 收尾票与普通票的三处执行契约差异已显式写明
- [ ] `sdflow-done` verify 引用规则落地，锚语义限定为「实现期聚合覆盖」且**按管线条件化**
- [ ] `ship_gate` 第四道校验落地：当且仅当计划文件名为新名时校验；旧名跳过并输出一行 grandfather 提示；**gate 无需读 config/marker 即可执行本校验**
- [ ] `[e2e]` 第四道校验的测试：含收尾票绿、**删掉收尾票必红**、`Blocked-by` 缺一张功能票必红、grandfather 路径不红
- [ ] `[e2e]` superpowers 轨回归（dogfood 盲区）：切到 superpowers 轨验证 gate 仍按旧名判 RUN_PLAN、verify 的聚合覆盖锚判「不适用」而非 gap
- [ ] `adr/0032` 落地（含被砍候选：verify 主动执行 / 移到 code-review 之后；含接受的残余风险）

---

