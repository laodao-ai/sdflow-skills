---
ship-gate:
  code_review: pass
  reviewed_sha: de52b3b59ffb85cd346f58475b6d9f9bfae4f948
---

## code-review 报告 — remove-superpowers-pipeline

### 命中范围

栈: Python + Markdown（backend 通用）
清单: CR-01~09 + backend.md
Step1 自持 scope 审计: DONE（子代理独立完成）— scope-drift 1 条低危 fold（step7 配对文件），完成度全部 DONE/PARTIAL（主 spec 未同步属正常 pre-archive 状态）
trivial_shape: NOT_EXEMPT（68 文件含脚本+SKILL+bundle assets）

<!-- sdflow:step1-broad-review v1 mode="subagent" -->
<!-- sdflow:hr-tg v1 hit="none" declared="" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,history,broad" -->

### Findings（已采纳，共 3 条）

**[Minor] ship_gate.py 文件头契约表 next 列陈旧** | ship_gate.py:45-46 | 已修 [impl-review-fix]
契约表 RUN_PLAN/CONTINUE_IMPL 行的 next 列仍写 `writing-plans`/`subagent-dev`，而 decide() 内实际 emit 已改为 `sdflow-implement`。同步修正。命中镜：domain(D1/D2)

**[Minor] test_gate_impl_progress.py:18 陈旧注释** | test_gate_impl_progress.py:18-20 | 已修 [impl-review-fix]
注释仍写「gate 第四道校验只对文件名 tickets.md（新名）生效」，而收尾票校验已改为无条件。已修正措辞。命中镜：adversarial(B1), domain(D1 相关)

**[Minor → defer] sdflow-spec-review/SKILL.md:366 引用 writing-plans** | OV1 | defer → todolist
spec-review SKILL 收敛口仍写「用户批准 → writing-plans」，应改为 `/sdflow-ship`。该文件不在本 change 的 proposal scope 内（仅 ship/implement/done 三份 SKILL 在 scope），defer 至 todolist 另开 change 修复。命中镜：outside-voice(code-voice)

### 已裁掉（反静默压制，可审计）

X1 D3（领域镜）：next 字段无测试断言 — 裁掉：next 字段对 RUN_PLAN/CONTINUE_IMPL 是 informational only（ship SKILL 用固定字面串派发，不读 next），加测试 = Speculative Generality
X2 OV2（voice）：sdflow-code-review/SKILL.md 引用 subagent-dev — 裁掉：检查确认是「注入点 B 关系」架构比较节（§2.4），设计溯源说明文本而非路由指令残留
X3 OV3（voice）：legacy hint 建议迁移到 tickets.md 可能破坏窗口 — 裁掉：该 message 仅在 tickets.md 缺席时触发（无窗口起点），此场景下 rename 不破坏窗口；措辞改善可议但非阻塞
X4 F2（scope）：主 spec 文件未同步 — 裁掉：正常 pre-archive 状态（delta spec 齐全正确），sdflow-done 的 archive delta-sync 步骤解决

### 修复 / defer 台账

自动修 2 项 [impl-review-fix]（gate 文件头契约表 + test 注释）
defer 1 项 → todolist（sdflow-spec-review SKILL 收敛口 writing-plans 残留）

### 度量锚

（metrics.enabled=true）

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="3" truncated="true" -->
<!-- sdflow:declared-sites v1 declared="code-voice" -->

### 结论

☑ 建议进 /sdflow-done
☑ defer 残差已入 todolist（sdflow-spec-review 收敛口）
