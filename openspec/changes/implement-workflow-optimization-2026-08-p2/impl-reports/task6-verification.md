# Task 6: 实现验证收尾

## 证据

| 层 | 命令原文 | 退出码 | SHA |
|---|---|---|---|
| unit | `/usr/bin/python3 -m pytest -q` | 0 (2549 passed, 10 skipped) | 8663fce27e6fc78950f34dd844f48ac02a5227ca |
| integration (anchor_lint) | `python3 $RULES_ROOT/tools/anchor_lint.py --report ...spec-review-report.md --layer spec-review ...` | 0 (CLEAN) | 8663fce27e6fc78950f34dd844f48ac02a5227ca |
| integration (sync_principles) | `python3 hack/sync_principles.py --check` | 0 (22 投放面全部一致) | 8663fce27e6fc78950f34dd844f48ac02a5227ca |
| e2e | — | 未覆盖 | 本仓无 e2e 测试层（纯 Markdown+Python skill 仓，无用户可感知的端到端场景） |

所有「通过」行锚同一 SHA：`8663fce27e6fc78950f34dd844f48ac02a5227ca`。

## Bundle 权威源一致性

- 所有规则改动已确认落 `sdflow-init/assets/workflow/`（bundle 权威源）
- `openspec/workflow/` 下仅 `WORKFLOW-GUIDE.md`（由 `gen_workflow_guide.py` 托管刷新，已通过 `--check`）
- `sync_principles.py --check` 绿（22 个投放面）
- `gen_workflow_guide.py --check`（Task 3 已验证）

## 状态

DONE
