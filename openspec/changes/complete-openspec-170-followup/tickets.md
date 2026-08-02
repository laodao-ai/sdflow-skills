---
impl-pipeline: tickets
---

## Global Constraints

- 遵守 bundle 权威源纪律：先改 `sdflow-init/assets/workflow/config.template.yaml`，下游通过 `sdflow-init update` 获得
- 遵守 `reviewed_sha` 时序契约（ADR-7(b)）：Q2 amendment 不直接调 `/opsx:update`
- 无安全 / 数据面影响
- `operations.archive.guidance` 形状为**字符串数组**（非字符串），否则 CLI 拒绝并打警告
- archive 子代理 prompt 改用 `--json` 后，旧的文本匹配判据（`"archived as ..."` / `"Validation error"` / `"incomplete task(s)"`）在 `--json` 模式下**不出现在 stdout**（被 `if (!json)` 守卫），MUST 全部替换为 JSON 字段判据
- 不配 `apply.guidance`（D4：当前无需下沉的 apply 面硬约束）
- 不实现 amendment coherence 的机械门验证（设计门人工兜底）
- 不迁移中文遗留 spec 格式（fallback 保留正是因为遗留仍存在）
- 不改 `sdflow-spec` 的相位 C（P1 已完成 skipped 态的生成侧处理）

### Task 1: P2 config 层注入 archive guidance 与 Purpose 规则

**Blocked-by:** none
**R-ID:** archive-guidance-injection, purpose-rule-in-specs

在 `openspec/config.yaml` 新增 `operations.archive.guidance` 段（两条硬约束字符串数组）和 `rules.specs` 的 `## Purpose` 规则。同步到 `sdflow-init/assets/workflow/config.template.yaml`（bundle 权威源纪律：先改 template 再改本仓 config）。

验收标准：
- [x] `openspec/config.yaml` 含 `operations.archive.guidance` 段，值为两条硬约束的字符串数组
- [x] `openspec/config.yaml` 的 `rules.specs` 含 `## Purpose` 规则（≥50 字符，1.7.0 archive 抬升机制）
- [x] `sdflow-init/assets/workflow/config.template.yaml` 同步新增 `operations` 段和 `## Purpose` 规则
- [x] diff template 与 config 确认 `operations` 段和 `## Purpose` 规则内容对齐（项目特有段不要求一致）

### Task 2: P3 sdflow-done archive 步现代化

**Blocked-by:** none
**R-ID:** archive-json-warnings, fallback-ladder-slim, archive-recognizes-skipped

改 `sdflow-done/SKILL.md` 第三步 archive 子代理 prompt：(a) 将 `openspec archive {change_name} -y 2>&1 | tail -30` 改为 `openspec archive {change_name} -y --json`；(b) 完整重写成功/失败判据为基于 JSON 结构的版本（成功=exit 0 且 `archive` 非 null，失败=exit≠0 或 `archive` 为 null）；(c) 新增对 `skip_specs` change 的处理（specs status=skipped 时无 delta 是正常的，不走 fallback）；(d) 确认现有 fallback 文本不提及 REMOVED abort（grep 实证零命中即通过）。

验收标准：
- [x] archive 命令已改为 `openspec archive {change_name} -y --json`
- [x] 成功/失败判据基于 JSON 字段（`archive` 非 null=成功，`archive.warnings` 展示警告，`archive` 为 null=失败走 fallback）
- [x] 旧文本匹配判据（`"archived as ..."` / `"Validation error"` / `"incomplete task(s)"`）已全部替换
- [x] archive 子代理 prompt 含对 skip_specs 的处理路径（specs status=skipped 时无 delta 不算异常）
- [x] `grep -c "REMOVED" sdflow-done/SKILL.md` 返回 0（确认无 REMOVED abort 描述）

### Task 3: Q2 amendment 双向 coherence

**Blocked-by:** none
**R-ID:** amendment-bidirectional-coherence

改 `sdflow-spec-review/SKILL.md:298` 从「据此更新 design/specs」扩展到四件套任意产物（proposal/design/specs/tasks），引用 `/opsx:update` 的双向原则但不直接调用（`reviewed_sha` 时序冲突）。

验收标准：
- [x] `sdflow-spec-review/SKILL.md` 的 amendment 写回段明确覆盖 proposal/design/specs/tasks 四件套
- [x] 引用了双向原则（build order is a useful reading order, not a constraint on which artifacts may be revised）
- [x] 提到最常见场景（评审发现 design 问题但根因在 proposal 的 Non-Goals 划错了）
- [x] 未直接调用 `/opsx:update`

### Task 4: roadmap 回写

**Blocked-by:** 1,2,3
**R-ID:** archive-guidance-injection, archive-json-warnings, amendment-bidirectional-coherence

更新 `openspec/roadmaps/openspec-1.7.0-followup/roadmap.md` 的阶段切分表，将 P2/P3/Q2 状态从 ⬜/❓ 更新为反映当前进度（合入同一 change `complete-openspec-170-followup`）。

验收标准：
- [x] roadmap 阶段切分表中 P2 状态更新
- [x] roadmap 阶段切分表中 P3 状态更新
- [x] roadmap 阶段切分表中 Q2 状态更新（从 ❓ 待拍板更新为已拍板+含入本 change）

### Task 5: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落 `impl-reports/task5-verify-all.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

- [x] 单元测试证据齐全并通过
- [x] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [x] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
