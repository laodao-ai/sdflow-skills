### Task 4: 重写 workflow bundle 核心文档为单轨线性流程

**Blocked-by:** 1,2,3
**R-ID:** R1

重写 workflow bundle 三个核心文档（权威源）：① `workflow.md` 流程图改为线性单轨，步骤表精简（删旧步骤），G1 分析移入附录正文只留一条规则，删全部 wayfinder/embedded-test-sop/分支 B 引用；② `generation-process.md` 删分支 B + 四入口选择规则，简化为单入口描述，加 explore→sdflow-spec 自动衔接规则；③ `ff-generation-constraints.md` 删 wayfinder→ff 衔接契约，更新切片建议触发条件措辞反映缺省=tickets。更新 `hack/gen_workflow_guide.py` 的 STEP_FILES 字典并重新生成 `WORKFLOW-GUIDE.md`。

- [ ] `workflow.md` 流程图为线性单轨，步骤表精简，G1 分析在附录
- [ ] `generation-process.md` 为单入口描述，含 explore→sdflow-spec 自动衔接规则
- [ ] `ff-generation-constraints.md` 无 wayfinder 衔接契约，切片建议反映缺省=tickets
- [ ] `WORKFLOW-GUIDE.md` 已通过 `python3 hack/gen_workflow_guide.py --write` 重新生成

