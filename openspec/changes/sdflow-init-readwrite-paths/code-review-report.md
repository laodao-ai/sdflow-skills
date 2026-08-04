---
ship-gate:
  code_review: pass
  reviewed_sha: d052677f588dc5d3e8f8117778b4f75262c22607
---

# code-review 报告 — sdflow-init-readwrite-paths

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,history" -->
<!-- sdflow:hr-tg v1 hit="none" declared="" evidence="" -->
<!-- sdflow:declared-sites v1 declared="code-voice" -->

## 命中范围

| 维度 | 值 |
|------|------|
| Change | sdflow-init-readwrite-paths（T64+T149+T6 纯代码质量修复） |
| 栈 | Python（sdflow-init/scripts/init.py） |
| 清单 | CR-01~09（通用 base） |
| gstack/review | scope-drift: 无偏离；完成度: 4/4 任务全完成 |
| 命中 TG | 无（纯内部函数修复） |
| HR-TG∩ | 空集 |
| 镜头 | 领域镜(domain) + 对抗镜×2(adversarial) + 历史镜(history) + broad(scope-drift) |

<!-- sdflow:step1-broad-review v1 mode="native" -->

## Findings（置信 ≥80）

无。三处修复均正确实现设计要求：

1. **T64 `_atomic_write_settings`**：mkstemp 在外层 try 内（CR-1 闭合）、内层 BaseException 清理残留 tmp、flush+fsync 对齐同文件风格（CR-7）、os.fdopen 接管 fd 生命周期。fail-safe 契约（OSError→False）保持。
2. **T149 `_detect_duplicate_top_keys`**：encoding=utf-8-sig（CR-3 闭合）、except (OSError, UnicodeDecodeError)（CR-2 闭合）、正则 `[A-Za-z_][\w-]*:` 只匹配顶层非注释行。lint_config 中重复键提前返回阻断后续 yq 解析（语义正确——重复键下 yq 结果不可信）。
3. **T6 `ensure_global_hooks`**：重构为 list 收集 + 条件追加，文案弱化（CR-5 闭合）。

对抗镜注意到 mkstemp 后 os.fdopen 失败时 fd 可能泄漏——但 os.fdopen 在有效 fd 上失败概率极低（仅内存耗尽等系统级异常），且外层 except OSError 会 return False，函数退出后进程级 fd 表正常回收。通则④判：低概率、低影响、不纠结。

## 已裁掉（反静默压制）

| # | 原始发现 | 裁掉理由 |
|---|----------|----------|
| X1 | fd 泄漏（对抗镜） | 低概率（os.fdopen 在有效 fd 上几乎不失败）+ 低影响（函数 return False 后 fd 随进程回收）+ 完美修复成本不对称（需拆分 fd 打开与 fdopen 的错误处理路径）。通则④。 |

## 修复 / defer 台账

无自动修复、无 defer。

## 度量锚

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="none" site="code-voice" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="none" reason_code="fallback-unavailable" findings="0" truncated="false" -->

## 结论

- [x] 建议进 /sdflow-done
- [x] 无 defer 残差
