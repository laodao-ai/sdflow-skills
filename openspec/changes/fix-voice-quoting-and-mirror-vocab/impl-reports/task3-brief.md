### Task 3: code-review SKILL 真名替换 + spec SHALL 条款 + 反漂移锁测试

**Blocked-by:** 2
**R-ID:** R2, R3

把 code-review SKILL.md 的 `mirrors=` 模板从借用 `grounding` 改为真名 `history`；重写 L244-248（保留 MUST 规范语句，token 集改为 `{domain,adversarial,history}`，删除借用叙事）；L545 示例同步。

三份主 spec 的 SHALL 条款枚举从 `{domain,adversarial,grounding}` 扩展到 `{domain,adversarial,grounding,history}`。

更新反漂移锁测试：拆分共享循环为按文件区分预期（spec-review 期望 `grounding`、code-review 期望 `history`）；重写借用文档测试为验证真名行为。

- [ ] code-review SKILL.md `mirrors=` 模板改为 `"domain,adversarial,history"`
- [ ] L244-248 重写：保留 MUST 规范语句 + token 集 `{domain,adversarial,history}` + 删借用叙事
- [ ] L545 示例 `mirrors=` 同步更新
- [ ] `openspec/specs/host-adaptive-execution/spec.md` 四处 SHALL 条款扩展
- [ ] `openspec/specs/workflow-metrics/spec.md` 一处扩展
- [ ] `openspec/specs/spec-workflow/spec.md` 一处扩展
- [ ] 反漂移锁测试拆分：spec-review 期望 `grounding`、code-review 期望 `history`
- [ ] 借用文档测试改为验证真名（断言 `mirrors=` 含 `history`、旧借用措辞不再出现）

