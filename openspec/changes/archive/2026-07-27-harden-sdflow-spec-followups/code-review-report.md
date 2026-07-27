---
ship-gate:
  code_review: pass
  reviewed_sha: 6a3d67708e5259de31934c564b756bd237eb2f2e
---

## code-review 报告 — harden-sdflow-spec-followups

### 范围与执行形态

- **diff base**：`9cb4229acd78995955355273b1b1f7946a345677` → `6a3d67708e5259de31934c564b756bd237eb2f2e`，42 文件 / +2127 −243。
- **目标**：FF-0 只对完整直接 literal 创建调用执法；`sdflow-spec` 薄化但保留常驻执行契约；逐票闭合规格/台账；刷新安装并完成回归。
- **清单**：通用 CR-01~09。未命中 backend / frontend / embedded 技术领域清单，因此没有伪报领域镜覆盖。
- **gstack broad**：原生在主 session 完成 scope、计划完成度与 critical checklist；没有 PR，Greptile 不适用。
- **能力**：Codex 子代理探针通过。resolver 的 light 档 `gpt-5.6-luna` 不受当前宿主支持，历史镜使用最低可用的 `gpt-5.6-terra`；安全、接地、历史三镜均独立 PASS。

<!-- sdflow:step1-broad-review v1 mode="native" -->

<!-- sdflow:fanout-capability v1 host="codex" subagents="available" mirrors="adversarial,grounding" -->

<!-- sdflow:hr-tg v1 hit="TG-08,TG-17" declared="TG-08,TG-12,TG-14,TG-15,TG-17,TG-18,TG-19,TG-23" evidence="外部 Claude CLI preflight 依赖与 PreToolUse 命令信任边界均被修改" -->

### Scope 与完成度

- 实现范围与 proposal/design 一致；Task 4 对 `copy_bundle`、嵌套托管块和非 POSIX preflight 的窄修复，是为了满足本 change 明示的全量回归与安装一致性验收，不是周边重构。
- `superpowers-plan.md` 四张 ticket 已全部完成且两轴复审通过。
- broad review 发现 `tasks.md` 的 13 个子任务仍为未勾选，与实施报告、ticket 验收和全量回归证据矛盾；已在 `0023760` 同步为完成。

### Findings（置信 ≥80）

| # | 严重度 | 位置 | 问题 | 处置 |
|---|---|---|---|---|
| F1 | 低 | `openspec/changes/harden-sdflow-spec-followups/tasks.md:3-24` | 13 个任务的完成状态落后于已验证实施事实，会让 archive/交接读取到错误进度 | 已修 `[impl-review-fix]`（`0023760`） |
| F2 | 中 | `hack/tests/test_harden_sdflow_spec_followup_closure.py:17-55` | change 级闭合测试硬编码 live 路径，归档移动目录后必然 `FileNotFoundError` | 已修 `[impl-review-fix]`：live-first、唯一 archive fallback，并以真实 rename 场景验证（`6a3d677`） |

### 对 outside-voice 挑战的裁决

- **裁掉：非 direct 命令应重新进入保护分支执法**。批准后的目标契约明确要求“整条命令完整匹配”才使用 payload `cwd`；prefix/`ask` 方案会重新扩大词法面并改变已批准权限行为。FF-0 也已明确自报它是纪律与审计 guard，不是安全边界。
- **裁掉：`additionalContext` 无宿主契约**。Claude Code 官方 Hooks Reference 明确规定 PreToolUse 的 `hookSpecificOutput.additionalContext` 会加入 Claude 上下文；当前安装的 Claude 2.1.220 通过 preflight。没有必要再造本地 transcript 门。
- **裁掉：非 kebab change 名可能被 OpenSpec 接受**。在 OpenSpec 1.5.0 scratch repo 实跑：`Add_Foo`、`add.foo`、`add--foo` 均 exit 1，只有 `add-foo` 成功。
- **裁掉：只读提及、stacking 文案、nested marker、18,000 字符余量**。前两项是“不解析 shell”的已知词法代价；后两项已有真安装、通则同步、字节比对和全量回归守卫。继续加共享常量/新门只增加低概率防御深度，不改善本 change 目标态。

### outside-voice

<!-- sdflow:declared-sites v1 declared="code-voice,hr-tg" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="codex" runner="claude" reason_code="ok" findings="6" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="codex" runner="claude" reason_code="ok" findings="5" truncated="false" -->

两站点均由 Claude Opus 执行，exit 0、stdout 非空、identity/nonce 核验通过，collect 后已清理 supervisor roster；不存在 unknown-cost 或 orphan warning。语义去重后仅 F2 被采纳，其余均按上节证据裁掉。

### 度量锚

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="codex" runner="codex" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="codex" runner="codex" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="grounding" host="codex" runner="codex" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="codex" runner="codex" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="codex" runner="claude" site="code-voice" findings="6" 采纳="1" 裁掉="5" defer="0" 独立="1" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="codex" runner="claude" site="hr-tg" findings="5" 采纳="0" 裁掉="5" defer="0" 独立="0" sev="致0/高0/中0/低0" -->

### 验证

- Task 4 主 session 全量：`2846 passed, 11 skipped, 3 xfailed in 285.92s`，exit 0。
- 本轮归档路径修复 focused：`16 passed in 1.36s`。
- `openspec validate harden-sdflow-spec-followups --strict`：valid。
- `git diff --check`：通过。
- canonical/installed hook、Claude/Codex skill、workflow 与 settings 注册已在 Task 4 机械比对一致。

### 结论

代码审 **PASS**。两项高置信缺口均已修复并形成独立 checkpoint；没有 Critical/Important 未处置项，建议进入 `/sdflow-done` 完成 verify → archive → commit → merge。
