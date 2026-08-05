# Task 6 impl-report：实现验证（收尾）

## 测试证据

| 层 | 命令原文 | 退出码 | SHA |
|---|---|---|---|
| unit (全仓) | `/usr/bin/python3 -m pytest -q` | 0 | b69e210 (fix 前) → 见下 |
| unit (fix 后) | `/usr/bin/python3 -m pytest -q` | 0 | 见最终 SHA |
| integration | — | 未覆盖 | 本仓无集成测试层 |
| e2e | — | 未覆盖 | 本仓无 e2e 测试层 |

全仓结果：**2443 passed, 10 skipped, 0 failed**

## 收尾期修复

- `hack/tests/test_checkpoint_slug_coverage.py`：MIN_CALLSITES 17→16（embedded-test-sop 删除减少了调用点）；期望集删除 `openspec/workflow/WORKFLOW-GUIDE.md`（本地 pin 已删）

## 残留引用扫描

`grep -rn "embedded-test-sop|RUN_SOP|wayfinder|分支 B|分支B|disable-model-invocation" --include="*.md" --include="*.py" --include="*.yaml"` 结果分析：

**allowlist 内（合理残留）**：
- README.md:57 — 「已迁出 skills」历史记录
- sdflow-ship/tests/test_workflow_authority.py — 反面断言（确保不含已退役步骤）
- sdflow-devenv/ — embedded-test-sop 作为"真硬件泳道手动 SOP 指向"（devenv 自身功能）
- sdflow-roadmap/ — wayfinder 是 roadmap skill 的核心概念（长档落盘工具），非工作流入口
- openspec/changes/ — 本 change 自身目录
- openspec/adr/ — ADR 历史引用
- openspec/issues/ + openspec/roadmaps/ — issue/roadmap 历史

**allowlist 外残留**：无

## setup.sh 验证

Task 5 implementer 已验证 `bash setup.sh` 全绿（五道机械门通过）。
FINAL_SHA=b69e210605478255d480635da318d84241ee34ad
