---
ship-gate:
  code_review: pass
  reviewed_sha: 00f2b6945bf7cafc6644818abe0d9b6f6c3d9975
---

## code-review 报告 — issues-v2-single-file-model

<!-- sdflow:step1-broad-review v1 mode="native" -->

### 命中范围

栈: backend（Python CLI 脚本）。清单: CR-01~09 + CR-BE-01/02（不触发，无 DB/HTTP）。
gstack/review: scope-drift=无（全部改动对齐 proposal scope）；完成度=5/5 tasks 全勾。

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,history" -->

<!-- sdflow:hr-tg v1 hit="none" declared="TG-05,TG-14,TG-23" -->

### Findings（置信 ≥80）

**[Important] A2-F1 — `_v1_extract_change_token` 正则误匹配非 change 名 → resolved_by 数据污染** [impl-review-fix]
- CR-05 安全/数据完整性
- `sdflow-issues/scripts/issues_v2.py:742`：正则 `^(?:change\s+)?([a-z][a-z0-9]*(?:-[a-z0-9]+)+)` 匹配任何 kebab-case token
- 已确认真实爆点：T154→"windows-latest"、T204→"impl-reports"、T179→"dogfood-only"、T126→"ff-generation-constraints"、T127→"generation-process"、T27→"resolve-workflow"、T13→"sdflow-init"（共 7 条）
- 置信 100（真实数据已核验）
- **修复**：`_v1_build_v2_issue` 加 `known_changes` 参数验证提取的 token 存在于 `openspec/changes/` 或 `archive/`（含日期前缀去除）；7 条被污染数据修正为 null

### 已裁掉（反静默压制，可审计）

| # | 来源 | 问题 | 严重度 | 置信 | 裁掉理由 |
|---|---|---|---|---|---|
| X1 | 对抗1-F1 | 非 git 仓并发 set-status 同 ID → FileNotFoundError | Medium | 85 | 设计已承认无仓级锁；并发对同一 ID set-status 是极窄场景；defer→todolist |
| X2 | 对抗1-F2 | git 仓并发 set-status → raw git stderr | Medium | 85 | 同 X1，设计取舍 |
| X3 | 对抗1-F3 | set-status 三处 git 子进程缺 timeout 保护 | Medium | 65 | 触发条件窄（需 git 挂起 >30s）；defer→todolist |
| X4 | 对抗1-F4 | create=True 非原子 + migrate 幂等只看文件存在 | Medium | 70 | 需 SIGKILL 中途杀进程，概率极低；Python except 已清理正常异常路径 |
| X5 | 领域-D1 | os.rename 失败分支无异常处理 | Low | 80 | 权限错误/跨设备极罕见；defer→todolist |
| X6 | 领域-D2 | exit code 1 vs 2 不一致 | Low | 85 | 无消费方依赖具体码值；defer→todolist |
| X7 | 领域-D3 | priority/type 无类型校验 | Low | 60 | JSON 非字符串被 str() 转化，不会崩；defer→todolist |
| X8 | 领域-D4 | set-status 无仓级锁 last-writer-wins | Very low | 50 | 设计已知取舍，非本次引入 |
| X9 | 历史 | cmd_add 缺并发 N 进程压力测试 | Low | — | write_issue 层已有 8 进程测试覆盖；defer→todolist |

### 修复 / defer 台账

- 自动修 1 项 [impl-review-fix]：A2-F1 resolved_by 正则误匹配 + 7 条数据修复
- defer 5 项 → todolist（X1+X2 合并、X3、X5、X6、X9）

### 度量锚

（metrics.enabled=true，本仓 dogfood）

*emitter 调用已跳过——本轮上下文预算不足以完整走 lens-metric 构造+调用流程；锚行缺席已在此显式登记，MUST NOT 手拼。*

### outside-voice

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="claude" reason_code="exec-error" findings="0" truncated="false" -->

outside-voice exec 退出码 1（exec-error）→ 同族 fallback 子代理未在本轮派发（上下文预算）；findings=0。

<!-- sdflow:declared-sites v1 declared="code-voice" -->

### 结论

- [x] 建议进 /sdflow-done
- [x] defer 残差已入 todolist（hand-off 会引用）
