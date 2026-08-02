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

### 改动 4: archive 子代理 prompt 改用 `--json` [spec-review-amendment]

`sdflow-done/SKILL.md` 第三步的 archive 子代理 prompt 中，将：
```
openspec archive {change_name} -y 2>&1 | tail -30
```
改为：
```
openspec archive {change_name} -y --json
```

并**完整重写 SKILL.md:376-380 的成功/失败判据**为基于 JSON 结构的版本：

- **成功**: exit 0 且 JSON 的 `archive` 字段非 null → 归档+同步完成；如 `archive.warnings` 数组存在且非空，展示警告
- **失败**: exit ≠ 0 或 `archive` 为 null → 走第 2 节 fallback。失败 JSON 形状为 `{"archive": null, "status": [{"code": "archive_validation_failed", ...}]}`，**不含 `warnings` 字段**
- 旧的文本匹配判据（`"archived as ..."` / `"Validation error"` / `"incomplete task(s)"`）在 `--json` 模式下**不出现在 stdout**（被 `if (!json)` 守卫），MUST 全部替换为 JSON 字段判据

依赖的 JSON 字段清单（CLI 1.7.0 archive.js）：`archive`（null=失败）、`archive.warnings`（可选数组）、`archive.specsUpdated`（布尔）、`status`（失败时的结构化错误数组）。CLI 未声明该 schema 为稳定 API，但 JSON 严格优于文本匹配。

### 改动 5: fallback 阶梯确认（无实际文本改动）[spec-review-amendment]

`sdflow-done/SKILL.md:378-380` 的 fallback 触发条件描述**已经只提中文遗留格式一种触发原因**，
通篇不提 REMOVED abort（grep 实证零命中）。1.7.0 修复的是 CLI 自身行为（REMOVED 需求不再
导致 abort），不是 SKILL.md 文本中存在这段话待删。

∴ 本改动 = **确认现有描述准确，无需文本改动**。保留中文遗留格式导致的 Validation error
作为 fallback 的唯一触发条件。

同批 1.7.0 修复的其他 CLI 行为（收窄了 fallback 的触发面，但均不影响 SKILL.md 文本）：
- delta 里非 `### Requirement:` 的分隔标题不再被当幽灵需求告警
- `## REMOVED Requirements` 不再被报「缺 scenario」
- symlink 化的 `specs/<cap>/spec.md` 不再被静默丢弃

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
