# Proposal: complete-openspec-170-followup

## Why

openspec CLI 1.7.0 引入了 `operations.{apply,archive}.guidance` 配置通道、`archive --json` 的 `warnings[]` 字段、
delta spec 的 `## Purpose` 抬升机制、以及修复了 REMOVED 需求导致 archive abort 的问题。
P1（schema 契约面重整）已交付，本 change 完成剩余三块跟进：

1. **P2 prevention 层扩到 apply/archive**：把 `sdflow-done` 中只在走 sdflow-done 路径时生效的硬约束
   下沉到 CLI 的 `operationGuidance` 通道，使走官方 `/opsx:archive` 时也能读到。
2. **P3 sdflow-done archive 现代化**：改用结构化 `--json` 输出替代文本解析、瘦身因 1.7.0 修复而
   多余的 fallback 分支、让 archive 侧认识 `skip_specs` 的 skipped 态。
3. **Q2 amendment 双向 coherence**：`sdflow-spec-review` 的 amendment 写回从「只改 design/specs」
   扩到四件套任意产物，借 `/opsx:update` 的双向原则但不直接调（`reviewed_sha` 时序冲突）。

## What Changes

### P2: config 层注入 archive 硬约束
- `openspec/config.yaml` 新增 `operations.archive.guidance` 段，写入两条硬约束
- `sdflow-init/assets/workflow/config.template.yaml` 同步新增 `operations` 段（推给下游）
- `rules.specs` 加一条 `## Purpose` 规则（≥50 字符，1.7.0 archive 抬升机制）

### P3: sdflow-done archive 步现代化
- `sdflow-done/SKILL.md` 的 archive 子代理 prompt 改用 `archive --json` 读 `warnings[]`
- fallback 阶梯瘦身：去掉 REMOVED abort 相关 workaround（1.7.0 已修），保留中文遗留格式 fallback
- archive 侧认 `skip_specs` 的 skipped 态——没有 delta 不算异常

### Q2: amendment 双向 coherence
- `sdflow-spec-review/SKILL.md:298` 从「据此更新 design/specs」扩到四件套任意产物
- 引用 `/opsx:update` 的双向原则：「Build order is a useful reading order, not a constraint on which artifacts may be revised」

## Success Metrics

- `openspec instructions archive --json` 在配置 `operations.archive.guidance` 后返回 `operationGuidance` 数组
- `sdflow-done` archive 步能正确处理 `archive --json` 的 `warnings[]` 输出
- `sdflow-spec-review` 的 amendment 写回明确覆盖 proposal/tasks（不止 design/specs）
- 新项目 `sdflow-init` (init 模式) 后获得 `operations` 段和 `## Purpose` 规则；已铺设项目按 update 提示手动合并 [spec-review-amendment]

## Non-Goals

- 不改 apply 面的 guidance（当前无需下沉的 apply 硬约束）
- 不实现 amendment coherence 的机械门验证（设计门人工兜底）
- 不迁移中文遗留 spec 格式（fallback 保留正是因为遗留仍存在）
- 不改 `sdflow-spec` 的相位 C（P1 已完成 skipped 态的生成侧处理）

## Compliance

N/A — 本 change 全部是指令层 / config 层调整，无安全 / 合规 / 数据面影响。
