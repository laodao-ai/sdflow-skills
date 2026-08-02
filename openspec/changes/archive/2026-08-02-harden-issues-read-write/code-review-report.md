---
ship-gate:
  code_review: pass
  reviewed_sha: 27436506162081bb5b7f6c699c5eab370611d528
---

<!-- sdflow:step1-broad-review v1 mode="native" -->

## code-review 报告 — harden-issues-read-write

### 命中范围

栈: Python（sdflow-issues scripts）
清单: CR-01~09（Python 通用）
gstack/review: scope-drift 无超范围改动，完成度 4/4 tasks 全勾

<!-- sdflow:hr-tg v1 hit="TG-06" declared="TG-01,TG-06,TG-18" evidence="reindex 写盘前总项数骤降检测（B12 数据完整性）" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->

### Findings（置信 ≥80）

**[Critical] R1 — `_validated_recorder_model` frontmatter 枚举硬 raise 未降级（对抗镜×2 收敛，置信 95-100%）**
- 证据：`__init__.py:618-621`（改前）对 frontmatter 项 status/specific_field 硬 raise → Task 1 的 `_build_effective_snapshot` 软校验对 canonical 格式不可达（死代码）
- 严重度：Critical（击穿本 change 核心承诺——"一条脏值不该拖垮整个 reindex"）
- 修复：`[impl-review-fix]` 移除 `_validated_recorder_model` 的 status/specific_field 枚举检查，统一由 `_build_effective_snapshot` 软降级覆盖 legacy + frontmatter

**[Important] R2 — `_count_index_items` 未按设计承诺记 problem 警告（领域镜，置信 85%）**
- 证据：`design.md:85` 承诺"跳过校验 + 记 problem 警告"，`issues.py:653` 实现只 return 0 无警告
- 严重度：Important（操作者不知道骤降守卫这次没生效）
- 修复：`[impl-review-fix]` `_reindex_core` 在 `old_count==0 and file exists` 时 `problems.append`

**[Minor] R3 — `_count_index_items` 未处理 UnicodeDecodeError（领域镜，置信 55%，采纳因一行修复）**
- 证据：`issues.py:626` 用 `open(..., encoding="utf-8")` 无 `errors="replace"`
- 修复：`[impl-review-fix]` 加 `errors="replace"`

### 已裁掉（反静默压制，可审计）

- X1 领域镜 F3（置信 40%）：triage 顶层 help 文案未提及 `--batch-only` — nitpick，`--help` 输出已含 flag 自身说明
- X2 历史镜 F1（置信 65%）：downstream 脏值处理链路 — design.md 已验证 `_is_terminal` 用 `.get(..., set())` 兜底
- X3 历史镜 F2（置信 55%）：`_count_index_items` 正则精度 — 降级设计天然覆盖（损坏→0→跳过）
- X4 历史镜 F3（置信 35%）：promote 参数隐式关系 — 无直调点，低风险

### 修复 / defer 台账

自动修 3 项 `[impl-review-fix]`（R1/R2/R3）；defer 0 项。

### outside-voice

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="claude" reason_code="exec-error" findings="0" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="claude" reason_code="exec-error" findings="0" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="code-voice,hr-tg" -->

两站点 voice helper exec 因 env vars 未持久化到后台 shell 返回 exit 1（exec-error），同族 fallback 未派出（本轮无 fallback 子代理可用时段）。findings=0。

### 结论

- [x] 建议进 /sdflow-done
- [x] 自动修复 3 项已提交（`2743650`），测试全绿 684 passed
