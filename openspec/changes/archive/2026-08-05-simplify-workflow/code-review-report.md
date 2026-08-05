---
ship-gate:
  code_review: pass
  reviewed_sha: ffc14ed4944cf10771c1adc08e2ab3289b9ad1d5
---

## code-review 报告 — simplify-workflow

### 命中范围

栈: Markdown + Python 脚本仓（无标准后端/前端栈）
清单: CR-01~09（通用 base），领域清单未覆盖（domains/ 下无匹配）
gstack/review: scope-drift CLEAN，完成度 6/6 DONE

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="none" declared="" evidence="纯文档+脚本仓，无领域 TG 命中" -->

### 子代理能力锚

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="—" -->

本 change 为纯文档+脚本简化（108 files，以删除为主），逻辑面改动集中在 ship_gate.py（删 RUN_SOP 约 76 行净减）和 impl_route.py（翻转缺省值 6 处 return），风险极低，主 session 亲自全量审查替代多镜 fan-out。

### Findings（置信 ≥80）

无 Critical 或 Important 发现。

**逻辑面审查结论**：

1. **ship_gate.py RUN_SOP 删除**（CR-05 完整性）：`tg02_hit()` 函数、RUN_SOP verdict 定义、`decide()` 分支、`emit_windowed` 调用点全部删除。`guard_design_freshness` 和 `emit_windowed` 保留完整，仅更新注释计数（三→两）。`grep -n "RUN_SOP\|tg02_hit" ship_gate.py` 零命中。345 tests passed。

2. **impl_route.py 缺省翻转**（CR-05 完整性）：`read_config_pipeline` 6 处 return 正确改为 `"tickets"`。`read_plan_marker` 冻结不变（docstring 详细解释原因——避免静默切换在途 change）。`_cmd_route` 仅新增解释性注释，无行为改动。79 tests passed。

3. **setup.sh 改动**（CR-01 安全）：新增 `cleanup_legacy_marker_installs()` 函数清理遗留 `.laodao-skills` marker 的 embedded-test-sop 安装。符合既有安全守卫模式（只处理自属 marker）。

4. **文档改动**（scope）：workflow.md/generation-process.md/ff-generation-constraints.md 重写为单轨，CLAUDE.md/AGENTS.md/claude-section.md 删旧入口段落，companion HTML docs 更新，本地 pin 40 个文件删除恢复全局解析。全部在 proposal 声明范围内。

### 已裁掉（反静默压制）

- [Minor] ship_gate.py:268 FenceTracker 消费者计数注释"三个"实为四个（`_plan_task_r_ids` 漏计）——comment-only，无逻辑影响，defer
- [Minor] impl_route.py 重复字面量 `"tickets"` 可提取为常量——预存模式（原 `"superpowers"` 同样重复），defer
- [Info] test_gate_freshness.py 窗口子用例标签 5.3b-d 未从 a 重编号——纯装饰

### 修复 / defer 台账

自动修 0 项；defer 2 项 → todolist（FenceTracker 计数注释、字面量常量提取）

### 结论

☑ 建议进 /sdflow-done
☑ defer 残差为 2 项 Minor（comment-only + 预存模式），不阻塞

<!-- sdflow:declared-sites v1 declared="code-voice" -->
