---
ship-gate:
  code_review: pass
  reviewed_sha: f6b890311c945d6e8993c3c03f9cebacbc3afa5d
---

# code-review 报告 — harden-outside-voice-scripts

## 命中范围

栈: backend（bash 脚本 + pytest 测试）
清单: CR-01~09 + CR-BE-01/02（BE 两条不适用）
gstack/review: scope-drift PASS（源码改动仅 `outside-voice.sh` + `test_outside_voice.py`，在 proposal Impact 声明范围内）、完成度 PASS（3/3 task done，全部 checkbox 已勾）

<!-- sdflow:step1-broad-review v1 mode="native" -->

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,history" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-14" evidence="改 outside-voice.sh 参数校验（安全输入验证）" -->

## Findings（置信 ≥80）

无。全部 findings 置信 <80 或已在设计门接受。

## 已裁掉（反静默压制，可审计）

| # | 原始发现 | 来源 | 置信 | 裁掉理由 |
|---|---------|------|------|---------|
| X1 | wc 失败时 `original_bytes` 报伪值（`OV_MAX_CONTEXT_BYTES+1`） | domain + outside-voice(code-voice) | 75 | <80 + design D2 有意 fail-closed 手段，`OV_OUTPUT_SIZE_CHECK_FAILED=1` 已区分真截断 vs wc 失败；调用方按子串匹配取该哨兵即知 original_bytes 不可信 |
| X2 | 缺 `--timeout 008` 测试锁定 `10#` 前缀 | domain 独家 | 78 | <80，代码正确（domain reviewer 已实测验证），仅未 test-lock；后续若误删 `10#` 有 CI 红（bash 报 `value too great for base`），非静默退化 |
| X3 | 出境 `head -c` 无 UTF-8 回扫 | adversarial-1 | 85 | 设计门已接受的边角（spec-review F4 → decision-memo「接受的边角」），code-review 不重开设计决策 |

## 修复 / defer 台账

无自动修复。无 defer。

## outside-voice

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="1" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="code-voice" -->

code-voice（跨模型，codex runner）返回 1 条 finding（X1，已裁掉）。

## 度量锚

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="1" 采纳="0" 裁掉="1" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="2" 采纳="0" 裁掉="2" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="code-voice" findings="1" 采纳="0" 裁掉="1" defer="0" 独立="0" sev="致0/高0/中0/低0" -->

## 结论

- [x] 建议进 /sdflow-done
- [x] 无 defer 残差
