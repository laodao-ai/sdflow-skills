### Task 2: 翻转 impl-pipeline 缺省为 tickets 并更新相关配置文档

**Blocked-by:** none
**R-ID:** R3

修改 `impl_route.py` 的 `read_config_pipeline` 和 `read_plan_marker` 函数：缺配置/缺键/空值的 return 改为 `"tickets"`，非法值/YAML 损坏的 return 改为 `"tickets"`；已有 plan 缺 frontmatter/marker 的 return 保持 `"superpowers"` 不变（避免静默切换在途 change）。同步修改 `_cmd_route` 展示折叠逻辑使其对称翻转。更新 `openspec/config.yaml`（本仓）impl-pipeline 注释 + 删除 wayfinder 规则引用。更新两份 `config.template.yaml`（`sdflow-init/assets/workflow/` + `openspec/workflow/`）注释改"缺省一律 tickets"。更新 `sdflow-ship/SKILL.md` 缺省描述。更新 `sdflow-init/assets/workflow/workflow.md` impl-pipeline 缺省描述。`pytest sdflow-implement/tests/` 全绿。

- [ ] impl_route.py 中缺配置/缺键/空值/非法值的 return 已改为 `"tickets"`
- [ ] impl_route.py 中 `_cmd_route` 展示折叠逻辑已对称翻转
- [ ] `openspec/config.yaml` impl-pipeline 注释已更新 + wayfinder 引用已删
- [ ] 两份 `config.template.yaml` 注释已改为"缺省 tickets"
- [ ] `sdflow-ship/SKILL.md` 缺省描述已更新
- [ ] `pytest sdflow-implement/tests/` 全绿

