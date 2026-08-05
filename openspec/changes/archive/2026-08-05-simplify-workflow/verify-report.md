---
ship-gate:
  verify: PASS
  reviewed_sha: 6a35f75ce3b1722363d2467bca151a84fc54ec62
---

# Verify Report — simplify-workflow

**日期**: 2026-08-05
**Change**: simplify-workflow
**结论**: **PASS**

## 逐需求核对表

### Spec: spec-workflow

| 需求 | 代码出处 / 证据锚 | 状态 |
|------|-------------------|------|
| 阶段一入口为唯一线性路径（删双轨分支 A/B） | `CLAUDE.md` 无"四入口选择规则"/"旧入口 sunset"/"分支 B" 段落；`generation-process.md` 无 §四 分支 B；`claude-section.md` 无分支 B/wayfinder/grill-with-docs | PASS |
| sdflow-spec 自动触发（删 disable-model-invocation） | `sdflow-spec/SKILL.md` frontmatter 无 `disable-model-invocation: true`；description 无"由人显式触发"/"只能人触发" | PASS |
| 拷问不可省（decision-memo.md 非空门） | sdflow-spec 管线相位 B 逻辑未被本 change 改动（scope 外，保持不变） | PASS |
| FF-0 三分支判定不受影响 | 未触及 FF-0 逻辑 | PASS |
| ship gate 不输出 RUN_SOP | `ship_gate.py` 无 `RUN_SOP` / `tg02_hit` / `embedded-test-sop` 引用 | PASS |
| embedded-test-sop skill 不可安装 | `embedded-test-sop/` 目录不存在；`bash setup.sh` 正常运行 | PASS |
| impl-pipeline 缺省为 tickets（无键→tickets） | `impl_route.py:194,199,202,206,208,211` 六处 `return "tickets"` | PASS |
| 显式 superpowers 不受影响 | `impl_route.py` 逻辑保留 `superpowers` 合法值路由 | PASS |
| REMOVED: wayfinder 衔接契约 | `workflow.md` 无 wayfinder；`ff-generation-constraints.md` 删 §wayfinder→ff 衔接（残留L46 `wayfinder-resolved:` 前缀命名约束是 roadmap 概念，非流程入口） | PASS |
| REMOVED: grill 独立步骤 | `step3-grill.md` 已删除；`grill-with-docs` 仅在 `generation-process.md` §二 技能描述表保留（描述独立 skill 功能，非流程步骤） | PASS |

### Spec: impl-orchestration

| 需求 | 代码出处 / 证据锚 | 状态 |
|------|-------------------|------|
| 无 impl-pipeline 键默认走 tickets | `impl_route.py:194` `return "tickets", "absent"` | PASS |
| 非法值/YAML 损坏回退到 tickets | `impl_route.py:199,206,211` 回退 tickets + stderr 诊断 | PASS |
| 已有 plan 缺 marker → 保持 superpowers（在途保护） | `impl_route.py:246,261` `return "superpowers"` 刻意冻结 | PASS |
| _cmd_route 折叠逻辑对称翻转 | `impl_route.py:540-549` 折叠锚点注释说明翻转设计 | PASS |

### Spec: spec-authoring

| 需求 | 代码出处 / 证据锚 | 状态 |
|------|-------------------|------|
| 删除 disable-model-invocation 声明 | `sdflow-spec/SKILL.md` frontmatter 无该键 | PASS |
| REMOVED: SA-14 四入口选择规则 | `CLAUDE.md` / `claude-section.md` / `generation-process.md` 无四入口段落 | PASS |

### Tasks 逐条

| Task | 要求 | 证据锚 | 状态 |
|------|------|--------|------|
| T1: 删 embedded-test-sop + RUN_SOP | 目录删除 + ship_gate.py 清理 + 测试清理 | 目录不存在；`grep -rn RUN_SOP ship_gate.py` = CLEAN；`pytest sdflow-ship/tests/` 345 passed | PASS |
| T2: 翻转 impl-pipeline 缺省 | 6处→tickets + 2处保持 superpowers + config/template 更新 | `impl_route.py:194,199,202,206,208,211`；`config.yaml:64` `impl-pipeline: tickets`；`config.template.yaml:79-83`；`pytest sdflow-implement/tests/` 79 passed | PASS |
| T3: 解除 sdflow-spec 手动限制 | 删 frontmatter + description 清理 | `sdflow-spec/SKILL.md` 无 `disable-model-invocation` 和手动触发措辞 | PASS |
| T4: 重写 workflow bundle 文档 | workflow.md 线性化 + generation-process.md 精简 + 删 prompts + 重生成 WORKFLOW-GUIDE.md | `workflow.md` 无旧步骤(0/1b/5.5)/wayfinder/embedded-test-sop；`step2-ff.md`/`step3-grill.md`/`step5_5-embedded-sop.md` 已删；`WORKFLOW-GUIDE.md` 存在 | PASS |
| T5: snippets + CLAUDE.md 更新 | 删四入口/sunset/grill-with-docs 段 + 删 test_grill_handoff.py + AGENTS.md 清理 | `CLAUDE.md` 无四入口/sunset；`claude-section.md` 无分支B/wayfinder/grill-with-docs/disable-model-invocation；`test_grill_handoff.py` 已删；`AGENTS.md` 无旧引用 | PASS |
| T5b: 本地 pin + companion 文档 | 删规则文件恢复全局解析 + companion 文档同步 | `openspec/workflow/` 仅剩 `lens-metric-contract.md` + `tools/`（规则文件已删）；`workflow-overview.md` 无 RUN_SOP；`criteria-mechanization-tracker.md` 无 tg02_hit；`02-module-reference.md` 无 RUN_SOP/embedded-test-sop | PASS |
| T6: 全量验证 + README | pytest 全绿 + setup.sh 正常 + 残留扫描 + README | `pytest` 2443 passed, 10 skipped, 0 failed；`README.md:57` 仅"已迁出 skills"历史记录（allowlist 内） | PASS |

## 缺口清单

无核心功能缺口。

**Minor 注记（不阻塞 PASS）**：
- `generation-process.md:29` 保留 `grill-with-docs` 在 §二 技能描述表——这是对独立 skill 功能的描述，不是流程入口指南，保留合理。
- `ff-generation-constraints.md:46` 保留 `wayfinder-resolved:` 前缀命名约束——这是 roadmap wayfinding 的命名空间概念，不是被删除的流程入口 wayfinder。
- `.claude/worktrees/agent-*` 目录下存在旧版文件副本——这是 worktree 临时目录，不属于主工作树。
