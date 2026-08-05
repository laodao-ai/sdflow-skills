### Task 6: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1, 2, 3, 4, 5
**R-ID:** all

按「聚合套件发现契约」运行本 change 的聚合测试套件（单元 + 集成 + e2e）并收集证据，证据落
`impl-reports/task6-<slug>.md`，每层一行 `<层> | <命令原文> | <退出码> | <SHA>`；未覆盖层写
`<层> | — | 未覆盖 | <判定依据>`。

契约与已知边界：

- `openspec/config.yaml` **无 `test-suites` 键**（实测），命令来源走优先级 ②：依仓内既有约定判定，
  并在报告里写明命令原文与判定依据。本仓 `CLAUDE.md` 与实测结论：单元层 =
  `/usr/bin/python3 -m pytest`（裸 `pytest` 不存在、默认 `python3` 未装 pytest）。
  某层仓内确无 ⇒ 记「未覆盖（本仓无此层）」+ 判定依据，**MUST NOT fail-closed 罢工**。
- 🔴 **pytest 判据是「相对 merge-base 无新增失败」，不是「全仓绿」**〔SR-18〕。当前 baseline
  **已有 1 个先于本分支存在的失败**——
  `hack/tests/test_harden_sdflow_spec_followup_closure.py::test_spec_authoring_requirement_ids_and_resident_identity_are_consistent`
  （断言 `SA-14` 存在于 `openspec/specs/spec-authoring/spec.md`，实测 grep 0 命中），与本 change
  无关，**不在本 change 修复范围**（要修另开 change）。全仓 2461 用例、本机 >280s，需后台跑或加长
  timeout。
- 本票**豁免 red-before-green**（不写产品代码，验收物是证据不是 diff）；主证据锚 = 本票
  impl-report 文件 + 其内 SHA 三元组，**不依赖本票产生 commit**。
- 判「通过」的证据行 MUST 锚**同一个最终 SHA**（最后一次修复之后的 `git rev-parse HEAD`）。
- 触发回归时的产品代码修复由编排层回派到对应功能票范围，本票只重跑套件收集证据。
- 🔴 `tasks.md` 6.9（archive 后对提升进主 spec 的结果重扫词表 + 逐 Requirement 与 SKILL.md 对码）
  依赖 archive 步，**本票不执行**——在报告中写明它由 `sdflow-done` 的 archive 步承接。

- [ ] 单元测试证据齐全，判据为「相对 merge-base 无新增失败」并附 baseline 已知失败的复核结论
- [ ] 集成测试证据齐全并通过（或记「未覆盖（本仓无此层）」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖（本仓无此层）」+ 判定依据）
- [ ] `python3 hack/sync_principles.py --check` 单独跑，退出码 0（6.3）
- [ ] `openspec validate refactor-roadmap-internalize-deps --strict --type change` 通过（6.7）
- [ ] 所有判「通过」的证据行锚同一个最终 SHA
- [ ] 6.9 与 4.5 两项 hand-off 承接已在报告中写明
