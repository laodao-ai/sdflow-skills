# code-review 报告 — streamline-workflow-automation（Phase A）

> 冷独立 impl-review（fresh-context 子代理，脱作者上下文）。范围：**Phase A 代码面**
> （Python 部署逻辑 + Bash 脚本 + 各 producer 路径改动 + 测试）；markdown/spec/skill 定义走 grill + `openspec validate`，不在本次代码审内。
> 方式：不止读码——reviewer **实测执行**（起 live 服务器 curl、脚本全边界跑）。

## 命中范围

- 栈：backend·python（`init.py`、`change-review-stub.py`、`gen_review_stub.py`）+ bash（`checkpoint-commit.sh`）+ 测试
- 清单：CR-01~09 base（正确性 / 错误路径 / 资源 / 边界）+ 部署顺序耦合 + 脚本注入安全 + B1 运行时路径模型 + 测试覆盖
- 未审：markdown 文档、skill SKILL.md、spec delta（另经 grill / validate）

## Findings（置信 ≥80）

**无 blocker、无 major。** reviewer 对抗式实测（不是读码）确认：

- **B1 运行时端到端 resolve**（live 服务器验证）：`init` 后 `serve.sh` cd 自身目录使 HTTP 根 = `openspec/`；`/review.html`、`/workflow/tools/{engine.js,engine.css,vendor/marked.min.js}`、`/INDEX.md`、`/changes/`、`/changes/<name>/proposal.md` 全 200；旧 `/tools/engine.js` 正确 404；per-change stub 在任意嵌套深度的根相对资产路径均 resolve。
- **顺序耦合安全**：`copy_review_tool` 仅一个调用点，`run()` 中 `copy_bundle`（造 `openspec/workflow/tools/review-stub.html`）先于它跑；测试用 `_deploy()` 复刻该序。
- **checkpoint-commit.sh 对注入安全**：`desc` 含 `$HOME`/反引号/引号被逐字提交，无展开、无执行、无 message 损坏；单行 `-m`，无 heredoc/续行。
- **无残留旧 `openspec/tools/` 功能路径**；三个 producer 均已指向 `openspec/workflow/tools/`。
- **测试非平凡**：资产路径回归有正/负断言（有 `/workflow/tools/` 且无 `/tools/`）。

## 已裁掉（反静默压制，可审计）

无。reviewer 未提出被主 session 判"不成立"的 finding；亦无 <80 置信项需滤除记录。

## 修复 / defer 台账

3 个 minor（blocker 线下），已全部**自动修 `[impl-review-fix]`**（commit `08d2a95`）：

| # | 问题 | 处理 |
|---|---|---|
| 1 | `copy_hack()` / `checkpoint-commit.sh` 无自动化测试（最新两处逻辑只有手工验证） | 补 `test_checkpoint_commit.py`（6 例含注入安全）+ `test_init.py::TestCopyHack`（2 例）；py 测试 21→29 passed |
| 2 | `serve.sh:3` 注释残留 `/tools/engine.js`（B1 归位后应为 `/workflow/tools/`） | 改注释 |
| 3 | `checkpoint-commit.sh` 非 git 分支措辞"跳过"但 exit 2（错误路径） | 措辞改"中止" |

无 defer 项（无修不了/需拍板的残差）。

## 结论

- ☑ 建议进 `/opsx-done`（Phase A 代码面已冷独立 review、无 blocker、minor 已清、全绿）。
- 测试：py 29 passed + js 18 passed。
- 遗留（不在本 change 内）：laodao-skills 自身 dogfood 副本刷新（`openspec/workflow/`、旧 `openspec/tools/`）属下游 routine，A merge 后另做。
