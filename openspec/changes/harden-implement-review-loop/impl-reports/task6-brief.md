### Task 6: 实现验证（收尾票，不计入 3–6 预算）

**Blocked-by:** 1, 2, 3, 4, 5
**R-ID:** all（覆盖本 change 全部需求的聚合验证，Spec 轴据此核验而非逐条溯源）

**交付的行为**：全部功能票实现完毕这一刻，按聚合套件发现契约跑本仓的单元 / 集成 / e2e 三层并产出确定性证据；同时完成跨票才看得见的一致性核验（两份 delta 与实际改动逐条对码、`openspec validate`）。

> **定位（Global Constraints 已逐字给出）**：本票是**实现期**聚合回归门，**不声称**「最终代码通过聚合套件」；不是 verify、不替代 verify、不前移 verify。
>
> **执行契约定制**：豁免 red-before-green（本票不写产品代码，验收物是证据不是 diff）；主证据锚 = 本票 impl-report 文件 + 其内的 SHA 三元组，**不依赖本票产生 commit**；Standards 轴核验范围 = 修复方式未靠**加 skip / 改测试配置 / 删除或弱化断言**蒙混过关。

- [ ] 聚合套件命令来源已按优先级判定（config `test-suites.*` 优先；缺失则依仓内既有约定判定并**在本票报告写明命令原文与判定依据**），且**未解析 Makefile / package.json 预判 target**
- [ ] `[e2e]` 三层各跑一遍，证据按 schema 落本票 impl-report：每层一行 `<层> | <命令原文> | <退出码> | <测试时 git rev-parse HEAD>`；未覆盖层写 `<层> | — | 未覆盖 | <依据>`
- [ ] 退出码非 0 者已按四类分诊处置（本 change 回归 → fix 循环；既有红测以 base SHA 复跑确认 → 记录放行；flaky 复跑一次即绿 → 记录放行；环境故障 → halt envelope 停并上抛）
- [ ] `openspec validate harden-implement-review-loop --strict --type change` 通过
- [ ] 两份 delta 归档后内容与各 SKILL.md / bundle 的实际改动**逐条对得上**（防 delta 与实现漂移）
- [ ] 本票 impl-report 汇总四条 Success Metric 的证据落点（含 Metric 1 若未验证则如实记「未验证」+ todo 号）
