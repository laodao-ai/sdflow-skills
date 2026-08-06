### Task 2: lens-metric 折叠源改认 scope-audit 并给出旧版修法指引

**Blocked-by:** none
**R-ID:** WM-1

度量锚的折叠映射单一源不再认识 `gstack-adv` 这个原始镜名，改认 `scope-audit`——两者**不共存**，
是替换而非新增。折叠目标仍是 canonical lens `broad`，因此下游（retro 聚合、MIN_LENS_ROWS、
锚行 `lens="broad"`）对本次替换零感知。契约文档里描述折叠关系的散文同步改述，与机读块不得分叉。

同样地，emitter 遇到不认识的原始镜名而 fail-closed 时，报错须带上「bundle 可能是旧版」的
可操作指引——这条路径正是 SKILL 已更新而消费仓 bundle 未更新时的第一现场。

- [ ] 折叠机读块含 `scope-audit: broad` 行，且不再含 `gstack-adv` 行
- [ ] 契约文档中描述折叠关系的散文与机读块一致（无 `gstack-adv` 残留）
- [ ] 原始镜名 `scope-audit` 经折叠后产出 `lens="broad"` 的锚行
- [ ] emitter 遇未知原始镜名时报错文案含「若本仓 `openspec/workflow/` 为旧版，请先跑 `sdflow-init update`」（有测试断言）
- [ ] `sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py` 既有 fold 用例全绿

