### Task 1: P2 config 层注入 archive guidance 与 Purpose 规则

**Blocked-by:** none
**R-ID:** archive-guidance-injection, purpose-rule-in-specs

在 `openspec/config.yaml` 新增 `operations.archive.guidance` 段（两条硬约束字符串数组）和 `rules.specs` 的 `## Purpose` 规则。同步到 `sdflow-init/assets/workflow/config.template.yaml`（bundle 权威源纪律：先改 template 再改本仓 config）。

验收标准：
- [ ] `openspec/config.yaml` 含 `operations.archive.guidance` 段，值为两条硬约束的字符串数组
- [ ] `openspec/config.yaml` 的 `rules.specs` 含 `## Purpose` 规则（≥50 字符，1.7.0 archive 抬升机制）
- [ ] `sdflow-init/assets/workflow/config.template.yaml` 同步新增 `operations` 段和 `## Purpose` 规则
- [ ] diff template 与 config 确认 `operations` 段和 `## Purpose` 规则内容对齐（项目特有段不要求一致）

