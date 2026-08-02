# Task 2: P3 sdflow-done archive 步现代化

## 改动摘要

- 改 `sdflow-done/SKILL.md` 第三步「Archive + Spec 同步」子代理 prompt（原 370-415 行区域）：
  - (a) archive 命令由 `openspec archive {change_name} -y 2>&1 | tail -30` 改为
    `openspec archive {change_name} -y --json`。
  - (b) 成功/失败判据从文本匹配（"archived as ..." / "Validation error" / "Aborted"）
    完整重写为基于 JSON 结构的判据：
    - 成功 = exit code 0 且顶层 `archive` 字段非 null；`archive.warnings` 非空数组时展示警告；
      `archive.specsUpdated` 标出本次是否真更新了主 specs。
    - 失败 = exit code ≠ 0 或顶层 `archive` 字段为 null（失败 JSON 形如
      `{"archive": null, "status": [{"code": "archive_validation_failed", ...}]}`，不含
      `warnings` 字段）→ 走第 2 节 fallback。
  - (c) 在原「## 1. 先试 CLI」之前新增「## 0. 先查 specs artifact 状态」段：先跑
    `openspec status --change {change_name} --json`，若 specs artifact 的 status 为
    `skipped`，明确该 change 无 delta 可同步是**正常**情况，MUST NOT 当异常、MUST NOT 因此
    走第 2 节 fallback；归档命令照常执行。
  - (d) 确认无 REMOVED 描述——恒真确认，未做改动。

## 验收核对

- archive 命令已改为 --json：✅
- 成功/失败判据基于 JSON 字段：✅
- 旧文本匹配判据已全部替换：✅（`grep -n "incomplete task\|Validation error\|archived as"` 仅剩
  一处，是新判据里对 `archive.warnings` 语义的举例说明，非文本匹配逻辑本身）
- skip_specs 处理路径已添加：✅（新增「## 0.」节，明确 specs status=skipped 时不算异常、不走
  fallback）
- grep REMOVED 返回 0：✅（`grep -c "REMOVED" sdflow-done/SKILL.md` = 0）

## 依赖的 JSON 字段（来自 brief：CLI 1.7.0 archive.js）

`archive`（null=失败）、`archive.warnings`（可选数组）、`archive.specsUpdated`（布尔）、
`status`（失败时的结构化错误数组）——均已在新 prompt 文本中体现并说明用途。
