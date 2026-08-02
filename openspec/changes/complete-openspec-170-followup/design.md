# Design: complete-openspec-170-followup

## Overview

三块独立改动，文件集不相交，分别描述。

## P2: config 层注入 archive guidance

### 改动 1: `openspec/config.yaml` 新增 `operations` 段

```yaml
operations:
  archive:
    guidance:
      - "归档 MUST 走 openspec archive CLI（它同步 delta→openspec/specs/ + 更新 INDEX + 校验），禁手动 mv（漏 spec 同步）"
      - "archive 前 MUST 先 reconcile tasks.md 复选框（否则 CLI 报 N/M incomplete 警告 + verify 误判）"
```

不配 `apply.guidance`（D4：当前无需下沉的 apply 面硬约束）。

### 改动 2: `sdflow-init/assets/workflow/config.template.yaml` 同步

在 template 中同步新增 `operations.archive.guidance` 段，使下游 `sdflow-init update` 后自动获得。

### 改动 3: `rules.specs` 加 `## Purpose` 规则

在 `openspec/config.yaml` 和 `config.template.yaml` 的 `rules.specs` 中加一条：

```
新能力 delta spec MUST 以 `## Purpose` 开头（≥50 字符）；1.7.0 archive 抬升此段进主 spec，缺则写 TBD 占位符
```

## P3: sdflow-done archive 步现代化

### 改动 4: archive 子代理 prompt 改用 `--json`

`sdflow-done/SKILL.md` 第三步的 archive 子代理 prompt 中，将：
```
openspec archive {change_name} -y 2>&1 | tail -30
```
改为：
```
openspec archive {change_name} -y --json
```
并改判断逻辑为读 JSON 输出的 `warnings` 数组（如存在），替代文本匹配。

### 改动 5: fallback 阶梯瘦身

`sdflow-done/SKILL.md:378-380` 的 fallback 触发条件描述中，去掉 REMOVED abort 的相关说明
（1.7.0 已修：REMOVED 需求不再导致 abort，改为 warn + 按已应用处理）。
保留中文遗留格式导致的 Validation error 作为 fallback 的主要触发条件。

同批 1.7.0 修复的其他 fallback 原因：
- delta 里非 `### Requirement:` 的分隔标题不再被当幽灵需求告警
- `## REMOVED Requirements` 不再被报「缺 scenario」
- symlink 化的 `specs/<cap>/spec.md` 不再被静默丢弃

这些修复进一步收窄了 fallback 的触发面，但中文遗留格式仍是不可消除的触发源。

### 改动 6: archive 侧认 skipped 态

`sdflow-done/SKILL.md` 第三步的 archive 子代理 prompt 中，新增对 `skip_specs` change 的处理：
- 先读 `openspec status --change {change_name} --json`，检查 specs artifact 的 status
- 若 specs status 为 skipped：archive 时无 delta 可同步，这是正常的（不是异常）
- MUST NOT 把「没有 delta」判成走 fallback 的理由
- 归档命令本身不变（CLI 已知道 skip_specs）

## Q2: amendment 双向 coherence

### 改动 7: `sdflow-spec-review/SKILL.md:298` 扩展

当前：
> 据此更新 design/specs，改动处标 `[spec-review-amendment]`

改为明确覆盖四件套任意产物，并引用双向原则：
> 据此更新四件套中需要修订的产物（proposal / design / specs / tasks），改动处标 `[spec-review-amendment]`。
> 原则：an edit to a later artifact may require revising an earlier one, not only the other way around
> （引自 `/opsx:update` 1.6.0）。最常见场景：评审发现 design 问题但根因在 proposal 的 Non-Goals 划错了。

**不直接调 `/opsx:update`**（D3/C1）：它不知道本仓的 `reviewed_sha` 时序契约——二次修订必须先单独
checkpoint 再回写锚（ADR-7(b)），直接调会打破这个时序。

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)。

## Compliance

- 遵守 bundle 权威源纪律：先改 `sdflow-init/assets/workflow/config.template.yaml`，下游通过 `sdflow-init update` 获得
- 遵守 `reviewed_sha` 时序契约（ADR-7(b)）：Q2 amendment 不直接调 `/opsx:update`
- 无安全 / 数据面影响
