### Task 3: 解除 sdflow-spec 手动触发限制并删除旧 workflow prompts

**Blocked-by:** none
**R-ID:** R1

从 `sdflow-spec/SKILL.md` 删除 frontmatter `disable-model-invocation: true`，description 删「由人显式触发」「只能人触发」等语句。删除三个旧步骤的 prompt 文件：`sdflow-init/assets/workflow/prompts/step2-ff.md`、`sdflow-init/assets/workflow/prompts/step3-grill.md`、`sdflow-init/assets/workflow/prompts/step5_5-embedded-sop.md`。删除 `sdflow-init/tests/test_grill_handoff.py`（grill 不再是独立步骤，回归门退役）。

- [ ] `sdflow-spec/SKILL.md` frontmatter 无 `disable-model-invocation: true`
- [ ] `sdflow-spec/SKILL.md` description 无手动触发限制语言
- [ ] `prompts/step2-ff.md`、`prompts/step3-grill.md`、`prompts/step5_5-embedded-sop.md` 已删除
- [ ] `sdflow-init/tests/test_grill_handoff.py` 已删除

