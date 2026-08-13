### Task 2: generation-process 收史 + ff-generation-constraints 外壳更新

**Blocked-by:** none
**R-ID:** D4, D5

`generation-process.md` 按 DOC-1 收史（§二现行化 + §三移入 workflow-history A5 + §六措辞 + §四定点两处 spec 回归）、`ff-generation-constraints.md` 外壳更新，具体位点：

- `generation-process.md` §二改现行两工具表（explore + /sdflow-spec），含 :21 节标题行同步 `[A8]`
- §三整节移除、原位留一行指路 workflow-history A5（§四编号不重排）
- §六「grill 是对话执行器」→「/sdflow-spec 相位 B 拷问」
- §四流水线图在 `/sdflow-spec` 与 `HARD-GATE 批准` 之间插一行 `↓ /clear → /sdflow-spec-review（阶段二设计审）` `[A11]`
- §四 :72 自动触发规则 ② 删「判断」二字 `[A12]`
- 改后跑 `pytest hack/tests/test_canonical_entry_sync.py` 核验 presence 六子串逐字保留 `[A9]`
- `workflow-history.md` 新增 A5 条目承接 §三论证考古
- `ff-generation-constraints.md`：标题改「生成起手强制规范（FF-0 + D-1~D-6）」；定位声明与调用方示例改 /sdflow-spec 语境（保「或 /opsx:ff 直呼」）；`@openspec/workflow/` 路径表述改 canonical；背景/历史节不动

- [ ] `generation-process.md` §二/§三/§六按 D4 改写完毕
- [ ] §四流水线图正确插入阶段二行，其余行未变
- [ ] §四 ② 已删「判断」二字，其余措辞未变
- [ ] `pytest hack/tests/test_canonical_entry_sync.py` 全绿（presence 六子串保留）
- [ ] `workflow-history.md` A5 条目已新增
- [ ] `ff-generation-constraints.md` 按 D5 更新完毕，背景/历史节未动

