### Task 5: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4
**R-ID:** all

按「聚合套件发现契约」运行本 change 的聚合测试套件（单元+集成+e2e）并全部通过，证据落
`impl-reports/task5-<slug>.md`（每层一行 `<层> | <命令原文> | <退出码> | <SHA>`）。

**命令来源（已核，走发现契约第②路径）**：`openspec/config.yaml` **无** `test-suites` 键 ⇒ 由本票
implementer 依仓内既有约定判定并写明判定依据。本机既有约定（逐字带入，MUST NOT 重新猜）：

- 单元层 = `/usr/bin/python3 -m pytest`（全仓）。**裸 `pytest` 命令在本机不存在，默认 `python3` 亦未装 pytest** ——
  必须用 `/usr/bin/python3 -m pytest`。
- 托管块回归 = `python3 hack/sync_principles.py --check`（本 change 改了多个 SKILL.md 业务段，确认 `sdflow:principles` 托管块未损）。
- 集成层 / e2e 层：按发现契约判定；仓内确无该层则记「未覆盖（本仓无此层）」+ 判定依据，**MUST NOT fail-closed 罢工**。

**执行契约差异（本票专属，与普通票不同）**：① 豁免 red-before-green（本票不写产品代码，验收物是
证据不是 diff）；② 主证据锚 = 本票 impl-report 文件 + 其内 SHA，**MUST NOT 依赖本票产生 commit**；
③ Standards 轴核验范围 = 「修复方式未靠**加 skip / 改测试配置 / 删除或弱化断言**蒙混过关」。

**收口盘面单一**：所有判「通过」的行 MUST 锚**同一个最终 SHA**（= 最后一次修复之后的
`git rev-parse HEAD`）；拼接不同盘面的「全部通过」非法。

- [ ] 单元测试证据齐全并通过（命令原文 + 退出码 + SHA 三元组）
- [ ] 托管块回归证据齐全并通过（`sync_principles.py --check` 退出码 0）
- [ ] 集成测试证据齐全并通过（或记「未覆盖（本仓无此层）」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖（本仓无此层）」+ 判定依据）
- [ ] 所有通过行锚同一最终 SHA
