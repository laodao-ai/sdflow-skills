## Why

`sdflow-init` 给每个消费仓铺设一套 HTML 文档查看器（`serve.sh` 起本地 HTTP 服务 → 浏览器开 `review.html` → `engine.js`/`engine.css` + `vendor/marked.min.js` 渲染 changes/specs/roadmaps）。实际价值不大——浏览 change/spec/roadmap 直接读 Markdown 文件即可，而这套查看器却是一份持续维护的负担（engine 的 hash 深链/同源守卫/404 回落逻辑历经多轮 grill 加固、附带 `vendor/` 第三方 JS + `serve.sh` 后台进程管理），且作为 bundle 一部分推给所有下游消费仓。移除它以缩减部署足迹与维护面。

## What Changes

- **移除** HTML 文档查看器全部资产与代码：`serve.sh` + `review.html` + `tools/{engine.js, engine.css, vendor/, review-stub.html}`，及 `init.py` 的 `copy_review_tool()` 铺设逻辑。
- **保留** `tools/` 下的评审机械层脚本（`anchor_lint.py` / `lens_metric_emit.py` / `outside_voice_guard.py` / `hr_tg_intersect.py` / `review_disposition_check.py` / `trivial_shape.py`）——它们是评审流程运行时依赖，与查看器无关。
- **新增自愈清理**：曾铺设过查看器的消费仓，在下次 `sdflow-init init/update` 时被清理——`tools/` 下的查看器资产随既有 `tools/` 整删重拷机制自动清除；根锚的 `openspec/serve.sh` + `openspec/review.html` 经**签名门控删除**（仅当文件内容含 bundle 部署签名时删，防误删用户同名文件），机制与既有退役 hook 反注册（`retire_hooks`）同构。
- **同步删除**本仓 dogfood 部署副本（`openspec/{serve.sh, review.html}` + `openspec/workflow/tools/` 查看器资产）、`sdflow-init` 的 memo 与测试（`engine.test.js`、`test_init.py` 的查看器测试）、以及 `SKILL.md` / `sdflow-roadmap` SKILL 中的查看器描述。

## Capabilities

### New Capabilities
（无）

### Modified Capabilities
- `spec-workflow`: 「workflow bundle 改在权威源、经部署下发」需求中，review UI 部署条款从「铺设根锚查看器 + hash 深链」改为「不再铺设任何查看面、tools/ 只留机械脚本」；相关查看器场景（每目录 stub、hash 深链、同源守卫、404 回落）删除，新增「退役部署文件签名门控清理」场景。

## Impact

- **代码**：`sdflow-init/scripts/init.py`（删 `copy_review_tool` + `REVIEW_TOOL_SRC`；加 `RETIRED_DEPLOY_FILES` + `retire_deploy_files`）。
- **资产**：`sdflow-init/assets/review-tool/`、`sdflow-init/assets/workflow/tools/{engine.js,engine.css,vendor/,review-stub.html}`（删）。
- **测试**：`sdflow-init/tests/engine.test.js`（删）、`sdflow-init/tests/test_init.py`（摘查看器测试、加清理测试）。
- **本仓 dogfood 部署**：`openspec/{serve.sh,review.html}` + `openspec/workflow/tools/` 查看器资产（删）。
- **文档**：`sdflow-init/SKILL.md`、`sdflow-init/memo-review-html-tool.md`（删）、`sdflow-roadmap/SKILL.md`、`openspec/ROADMAP.md`、`openspec/INDEX.md` 及 todolist 中的查看器引用。
- **下游消费仓**：`sdflow-init update` 后查看器被清理；无查看器不影响任何评审流程（机械层脚本保留）。**非破坏性**——查看器仅为可选浏览便利。
