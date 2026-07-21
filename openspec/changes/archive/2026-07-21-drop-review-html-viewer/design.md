## Context

`sdflow-init` 通过 `copy_review_tool()` 给消费仓铺一套 HTML 文档查看器：根锚 `openspec/serve.sh` + `openspec/review.html`，配 `openspec/workflow/tools/` 下的 `engine.js` / `engine.css` / `vendor/marked.min.js` / `review-stub.html`。本 change 整体移除它。

关键约束：`tools/` 目录**同时**装着评审流程运行时依赖的机械层脚本（`anchor_lint.py` / `lens_metric_emit.py` / `outside_voice_guard.py` / `hr_tg_intersect.py` / `review_disposition_check.py` / `trivial_shape.py`）——这些**必须保留**，只删查看器资产。

## Goals / Non-Goals

**Goals:**
- 从权威源删除查看器全部资产与 `init.py` 铺设代码。
- 存量消费仓在下次 `init/update` 时被清理（根锚文件 + tools/ 资产），不留孤儿。
- 清理对用户自建同名文件 fail-safe（不误删）。

**Non-Goals:**
- 不动 `tools/` 下的机械层脚本、不动退役 hook 机制（`change-review-stub.py` 反注册照旧）。
- 不提供替代查看器；浏览 change/spec/roadmap 直接读 Markdown。

## Decisions

**D1：根锚文件（serve.sh + review.html）用签名门控删除，不裸按文件名删。**
- `tools/` 下的查看器资产（engine.*/vendor/review-stub.html）无需专门清理代码——既有 `copy_bundle` 非 full 模式对 `tools/` 是「先 `rmtree` 再 `copytree`」，权威源删掉这些文件后，下次 update 自动清除（已被现有 spec 场景「update 后 tools/ 收敛」覆盖）。
- 但 `serve.sh` + `review.html` 落在 `openspec/` **根**（非 tools/，服务器根约束逼留根），不在 rmtree 范围内 → 停止铺设后会变孤儿，须显式删。
- **为何签名门控而非裸删**：这两个文件在用户仓内，理论上用户可能自建同名文件。承 adr/0022 精神（skill 只删自己确知铺设过的、不猜用户文件），删除前校验内容含 bundle 部署签名：`review.html` 含 `__OPENSPEC_PROJECT_NAME__`（模板渲染 token 的宿主变量名，查看器独有）、`serve.sh` 含 `openspec-review-serve-`（PIDFILE key 前缀，查看器独有）。签名不匹配 → 跳过，用户文件原样保留。
- **备选（否决）**：裸按文件名 `os.remove`——简单但会误删用户同名文件，违 adr/0022。签名门控成本极低（读文件 + 子串判断），值得。

**D2：清理机制与退役 hook（`retire_hooks`）同构，但独立函数。**
- 新增 `RETIRED_DEPLOY_FILES`（相对 `openspec/` 的路径 + 签名）+ `retire_deploy_files(root)`，在 `run()` 里 init/update 都调用（紧邻现有 `retire_hooks()` 调用）。
- **为何不复用 `retire_hooks`**：退役 hook 操作的是 `~/.claude/`（全局、按文件名删 + 摘 settings 注册）；退役部署文件操作的是消费仓 `openspec/`（仓内、签名门控删）。语义与作用域不同，各写一个短函数比塞进一个通用函数清晰（避免 over-abstraction）。

**D3：`copy_review_tool()` 及 `REVIEW_TOOL_SRC` 常量整体删除，`run()` 里的调用与报告行同删。**
- `run()` 报告改为一行说明查看器已移除（或直接删该报告行，报告 `retire_deploy_files` 的清理动作）。

## Risks / Trade-offs

- **[风险] 签名字符串漂移**：若未来查看器模板改了 token 名而签名没跟上——不适用，本 change 是**删除**查看器，签名是针对**存量已铺**的旧文件内容（固定历史值），不会再变。
- **[风险] 误删用户文件** → 签名门控 mitigate；配单测覆盖「用户同名无签名文件不被删」。
- **[取舍] 双写窗口**：pull（下游拉到新版 init）与 setup/update 之间，存量查看器仍在——可接受，与既有 pull→setup 窗口期性质相同，一次 update 即清。

## Migration Plan

1. 删权威源资产 + `init.py` 代码，加 `retire_deploy_files`。
2. 删本仓 dogfood 部署副本（`openspec/{serve.sh,review.html}` + `openspec/workflow/tools/` 查看器资产）。
3. 更新 test_init.py（摘查看器测试、加清理测试）+ 删 engine.test.js。
4. 更新文档引用。
5. 下游消费仓经 `sdflow-init update` 自动清理——非破坏性，无需人工干预。
- **回滚**：`git revert` 本 change 的 merge commit + 下游重跑 update（会重新铺回查看器）。
