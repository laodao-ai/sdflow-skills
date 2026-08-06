### Task 1: anchor_lint 接纳 broad 镜而不误判降级为自相矛盾

**Blocked-by:** none
**R-ID:** HAE-1, WM-1

评审报告的 `fanout-capability` 锚在 `mirrors=` 里写出 `broad` 时被 lint 判为合法；同时，
「子代理机制报 unavailable 却声称跑了多个 fan-out 镜」这一自相矛盾的判定**不因 broad 的加入
而变松**——`broad` 有「主 session 亲做仍算独立完成」的合法降级路径，故它进合法 token 集、
不进 dead-fanout 计数集。当前实现把合法集与计数集混用同一个常量，本票须把二者拆开，
使「扩合法集」不会顺带污染计数判据。

另外，当消费仓的 workflow bundle 是旧版（不认识 `broad`）时，lint 报出的 unknown-token 错误
须自带可操作的修法指引，而不是让使用者对着一个陌生 token 名发呆。

- [ ] `mirrors=` 含 `broad` 时 lint 判合法通过
- [ ] `subagents="unavailable"` + `mirrors="broad,history"` 不触发 dead-fanout-multi-mirror
- [ ] `subagents="unavailable"` + `mirrors="broad,domain,history"` 仍触发 dead-fanout-multi-mirror
- [ ] `step1-broad-review` 锚取新枚举值 `mode="subagent"` 时 lint 通过（锁定「lint 不校验 mode 值」不变量）
- [ ] mirrors-unknown-token 报错文案含「若本仓 `openspec/workflow/` 为旧版，请先跑 `sdflow-init update`」
- [ ] 合法 token 集与 dead-fanout 计数集为两个独立常量，改前者不影响后者（有测试佐证）；**合法集常量名钉死为 `_MIRRORS_LEGAL`**（`design.md:106` 已按此名声明 SKILL 侧 skew 探测信号，Task 3 据此写探测段——改名即断链）
- [ ] `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py` 既有用例全绿

