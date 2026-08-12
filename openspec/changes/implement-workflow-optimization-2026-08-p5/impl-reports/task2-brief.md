### Task 2: sdflow-spec 分批条款 + 规范面同步

**Blocked-by:** none
**R-ID:** SA-03

重写 `sdflow-spec/SKILL.md` A.1 + B.3 条款为 D3 全文（呈现与拍板分离协议）：
- 独立批 ≤4 问必附推荐
- 依赖链整链呈现（链结构 + 每环推荐 + 推荐整链路径），人可拍整链或链头
- 链头改判时下游按新前提重提（背景不重复）
- 组合爆炸时退回链头 + 一句话预告各选项下游影响
- 只拍链头时下游保持待拍板状态，MUST NOT 把沉默当授权

同步「一次一问」残留规范面三处（design De）：
① `sdflow-spec/SKILL.md:161` 相位流程图字样改为与 D3 一致
② `sdflow-init/assets/workflow/generation-process.md:75` 拷问协议括号措辞同步（bundle 权威源）
③ spec-workflow 主 spec 的「拷问协议不因触发方式改变」Scenario 经本 change delta MODIFIED 同步

核对 `hack/tests/` 中消费 sdflow-spec SKILL 文本的既有测试（已知 `test_sdflow_spec_resident_contract.py:28` 一处），如断言旧「一次一问」字面则同步断言。

完成后全仓负向 grep `一次只问一个|一次一问` 确认规范面归零（docs/ 与 reference/ 描述性提法除外）。

- [ ] A.1 + B.3 条款重写为 D3 全文
- [ ] 相位流程图「一次一问」字样已改
- [ ] `generation-process.md:75` 括号措辞已同步
- [ ] spec-workflow 主 spec Scenario 措辞已同步
- [ ] 既有测试断言已同步（旧字面不再命中）
- [ ] 全仓规范面 grep 确认归零

