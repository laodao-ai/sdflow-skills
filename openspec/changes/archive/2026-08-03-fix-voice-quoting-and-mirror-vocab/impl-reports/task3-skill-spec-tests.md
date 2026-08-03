# Task 3 impl report：code-review SKILL 真名替换 + spec SHALL 条款 + 反漂移锁测试

**Blocked-by:** 2（已满足——`anchor_lint._FANOUT_MIRRORS` 已含 `history`，见 commit `3ee8e50`）
**R-ID:** R2, R3

## 变更清单

### 2.3 `sdflow-code-review/SKILL.md`

- L242：`mirrors=` 锚模板 `"domain,adversarial,grounding|—"` → `"domain,adversarial,history|—"`
- L244-248：重写。保留 L244 开头的 MUST 规范语句（`mirrors=` MUST 由本 skill 在 fan-out 决策落定时直接
  写本轮实际派出/独立完成的镜清单），token 集改为 `{domain,adversarial,history}`，删除借用叙事
  （原「`anchor_lint._FANOUT_MIRRORS` 是跨层共用的固定三 token 词表……本 skill 第三镜借用既有 token
  `grounding` 记该镜跑过」整段——T148 已让 `_FANOUT_MIRRORS` 扩至四 token，code-review 不再需要借用）
- L545：`mirrors=` 示例锚同步为 `"domain,adversarial,history|—"`

`sdflow-spec-review/SKILL.md` 未改动——它的第三镜是接地镜，`mirrors="domain,adversarial,grounding"`
语义本就正确（design.md「不改的文件」段明示）。

### 2.4 三份主 spec 的 SHALL 条款扩展

`{domain,adversarial,grounding}` → `{domain,adversarial,grounding,history}`：

- `openspec/specs/host-adaptive-execution/spec.md`：L157（锚模板示例）、L159（取值文法 XOR 子集）、
  L161（去重计数集）、L174（Scenario 去重计数集）共四处
- `openspec/specs/workflow-metrics/spec.md`：L37（Scenario 去重计数集）一处
- `openspec/specs/spec-workflow/spec.md`：L890（per-lens 完整性集，`domain/adversarial/grounding`
  → `domain/adversarial/grounding/history`）一处

三份均直接改主 spec（非 delta → archive），依据 `specs/host-adaptive-execution/spec.md`
[spec-review-amendment S1/Q1] 已定的先例。

### 2.5 反漂移锁测试更新（`sdflow-init/tests/test_codex_subagent_authorization.py`）

- `test_mirrors_tokens_are_subset_of_anchor_lint_vocabulary`：原来两份 SKILL 共享同一条断言
  （`"domain,adversarial,grounding" in t`），现按文件拆成 `{SPEC_REVIEW_SKILL: "domain,adversarial,
  grounding", CODE_REVIEW_SKILL: "domain,adversarial,history"}` 的映射循环，各自断言自己的字面
  token 串、且该 token 集合仍是 `anchor_lint._FANOUT_MIRRORS`（现四 token）的子集。
- `test_code_review_history_mirror_alias_honestly_documented`：重写为验证真名行为——断言
  code-review SKILL.md 的 `mirrors=` 字面含 `'mirrors="domain,adversarial,history'`，且旧借用措辞
  `"借用既有 token"` 不再出现在文档里。
- 顺带修正模块顶部 docstring（L17-22）「固定三 token 词表（domain/adversarial/grounding）」的过期
  描述，改为四 token 并说明两份 SKILL 按文件区分预期 token 串的原因（避免文档自身与代码产生新漂移）。

## 验证

```
pytest sdflow-init/tests/test_codex_subagent_authorization.py -v
```

11 passed（含两条改写的测试 `test_mirrors_tokens_are_subset_of_anchor_lint_vocabulary`、
`test_code_review_history_mirror_alias_honestly_documented`）。

TDD 纪律：先确认旧断言在改动前描述的是「三 token 借用」事实（读码验证 `grounding` 字面确实在
code-review 旧文档中），改字面之后旧断言字符串（`"借用既有 token"`、`` '`grounding` 记该镜跑过' ``）
已不在文件中出现——若未重写测试，旧断言会因文档字面消失而红，从而确认测试确实在守真实内容而非
恒真。

另跑了一轮全仓 `pytest`（含 `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py` 等 Task 2
产出的测试）作面级核验；该轮包含若干 subprocess 起 `claude`/`codex` CLI 的慢测试，耗时较长，
在本报告落盘时尚未跑完（非任务验收要求项，Task 3 验收清单只要求跑
`test_codex_subagent_authorization.py`，已确认绿）。

## 未改动 / 不在本票范围

- `openspec/changes/archive/**` 下的历史归档报告（`code-review-report.md` / `spec-review-report.md`
  / `design.md` / `tasks.md` 等）里出现的 `mirrors="domain,adversarial,grounding"` 字面——按 DOC-1
  与「目标态导向」，这些是已归档变更的历史快照，不回溯改写。
- `openspec/issues/todolist/2026-07-todolist.md` 的 T148 条目——是否在本 change 内标 DONE 不在
  Task 3 的验收清单里，留给该 change 的收尾阶段处理。
