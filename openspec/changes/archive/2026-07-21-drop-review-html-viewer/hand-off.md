# hand-off — drop-review-html-viewer

## ✅ 完成了什么（锚点已复核存在）

- **删查看器铺设代码**：`sdflow-init/scripts/init.py` 删净 `copy_review_tool()` + `REVIEW_TOOL_SRC`（grep 零命中）。
- **加退役自愈**：`init.py` 新增 `RETIRED_DEPLOY_FILES`（`init.py:94-97`）+ `retire_deploy_files()`（`init.py:255-278`，签名门控删除、三重 fail-safe），`run()`（`init.py:823`）init/update 都调用。
- **删查看器资产**：`assets/review-tool/`、`assets/workflow/tools/{engine.js,engine.css,vendor/,review-stub.html}`、`memo-review-html-tool.md`、本仓 dogfood 副本 `openspec/{serve.sh,review.html}` + `openspec/workflow/tools/` 查看器资产、`tests/engine.test.js` —— 逐项确认不存在。
- **机械层脚本保留**（反向核对）：`anchor_lint.py` / `lens_metric_emit.py` / `outside_voice_guard.py` / `hr_tg_intersect.py` / `review_disposition_check.py` / `trivial_shape.py` 在 assets 源与本仓 tools/ 两处均完好。
- **测试**：`sdflow-init/tests/` 303 passed（新增 `TestRetireDeployFiles`：清理/跳过无签名用户文件/fresh no-op/幂等/e2e run；`test_runtime_gitignore.py` stub 改 `retire_deploy_files`）；全仓 `/usr/bin/python3 -m pytest` **2082 passed, 8 skipped, 3 xfailed, 0 failed**。
- **文档**：`sdflow-init/SKILL.md`（布局图/退役说明）、`sdflow-roadmap/SKILL.md`（浏览方式改直读 Markdown）、`openspec/ROADMAP.md`、`adr/0003`（superseded 注）已同步；`T47`（engine.js 深链单测 todo）→ WONTDO（对象已删）。
- **dogfood 验证**：模拟已铺查看器的消费仓跑 `sdflow-init update` → 查看器根锚（signature-gated）+ tools/ 陈旧资产删净、机械脚本存活。

## ⏳ 未完成 / 延后

- **无本 change 新增 debt**：issues sweep `--change drop-review-html-viewer` tagged 0 项。
- **精简流程有意跳过**：grill / sdflow-spec-review / sdflow-code-review（用户拍板：功能删除、风险集中在「别误删机械层」+「清理正确性」，靠测试 + 主 session 自审覆盖）。自审已当场修一处（`set-status T47` 触发 buglist 冻结 corpus `KeyError` → 注册 `T47:PROPOSED→WONTDO` delta）。
- **≥2 方案决策**：无待决——唯一设计点（根锚文件用签名门控删除 vs 裸删）已在 design.md D1 定（签名门控，承 adr/0022 精神），无需人再拍。

## ▶ 下一阶段建议

- **下游消费仓**：装了 sdflow-skills 的机器经 `/sdflow-upgrade`（pull + setup.sh）后，各消费仓下次跑 `sdflow-init update` 即自动清理残留查看器——非破坏性、无需人工干预。
- **无后续清理 change**：本 change 自包含，无 fold-out 残项。
- 非 roadmap 驱动（`roadmap_writeback_draft` exit 3 NO_ASSOCIATION），无 roadmap 回填。
