## 1. init.py 删查看器铺设 + 加退役清理

- [x] 1.1 删 `REVIEW_TOOL_SRC` 常量、`copy_review_tool()` 函数、`run()` 里 `copy_review_tool()` 调用与其报告行
- [x] 1.2 加 `RETIRED_DEPLOY_FILES`（`serve.sh` 签名 `openspec-review-serve-`、`review.html` 签名 `__OPENSPEC_PROJECT_NAME__`）+ `retire_deploy_files(root)`（签名门控删除，fail-safe），在 `run()` init/update 都调用并入报告

## 2. 删权威源查看器资产

- [x] 2.1 删 `sdflow-init/assets/review-tool/`（serve.sh）
- [x] 2.2 删 `sdflow-init/assets/workflow/tools/{engine.js, engine.css, vendor/, review-stub.html}`
- [x] 2.3 删 `sdflow-init/memo-review-html-tool.md`

## 3. 删本仓 dogfood 部署副本

- [x] 3.1 删 `openspec/{serve.sh, review.html}`
- [x] 3.2 删 `openspec/workflow/tools/{engine.js, engine.css, vendor/, review-stub.html}`

## 4. 测试

- [x] 4.1 删 `sdflow-init/tests/engine.test.js`
- [x] 4.2 改 `sdflow-init/tests/test_init.py`：摘除查看器测试类/方法 + `copy_review_tool` import；新增 `retire_deploy_files` 测试（清理已铺文件、跳过无签名用户文件、fresh 安装 no-op）
- [x] 4.3 跑 `pytest sdflow-init/tests/` + 全仓 `pytest` 全绿

## 5. 文档引用清理

- [x] 5.1 `sdflow-init/SKILL.md`：删布局图/文本里 review.html / serve.sh / 查看器 tools 资产描述
- [x] 5.2 `sdflow-roadmap/SKILL.md`：删「用 serve.sh 起服务开 review.html 浏览 roadmap」行
- [x] 5.3 `openspec/ROADMAP.md` / `openspec/INDEX.md` / todolist 里的查看器引用清理

## 6. 自审 + 收尾

- [x] 6.1 冷读全 diff：确认机械层脚本（anchor_lint.py 等）未误删、签名门控删除正确、无悬挂引用
- [x] 6.2 `sdflow-init update --dev --root .` dogfood 验证（本仓不再铺查看器、机械脚本仍在）
