# hand-off — drop-per-dir-review-stub

> 2026-07-05。异步人类再入口 + 下个 change 种子。verify=PASS 后、archive 前产出，随归档留档。

## ✅ 完成了什么（每条附机验锚点）

- **退役 hook 自愈机制**：`init.py` 新增 `RETIRED_HOOKS`(:63) + `retire_hooks()`(:319) + `_deregister_hook_in_settings`(:279) + `_hook_command`(:269)；`run()` 内无条件调用(:382)，init/update 两路径都跑。证据：commit `cbe469f`，测试 `TestRetiredHooks` 8 例（含 CR-F1 两负例）。
- **两个每目录 stub 生产者移除**：`change-review-stub.py` hook（资产 + HOOKS 注册项 + `test_change_review_stub_hook.py`）、roadmap `gen_review_stub.py`（+ 测试）全删。证据：commit `102649d` / `a808551`；`sdflow-roadmap/{scripts,tests}` 目录已不存在。
- **文档同步**：`sdflow-init/SKILL.md`、`sdflow-roadmap/SKILL.md`、`openspec/ROADMAP.md`、`CLAUDE.md`、`README.md`（roadmap 归入纯 Markdown 编排类）。证据：commit `1fa9263`。
- **代码审修复**：CR-F1 崩溃（isinstance 守卫 + 2 负例）、CR-F2 engine.js 注释、CR-V2/F3 措辞诚实化。证据：commit `2ef7ba5`，`code-review-report.md` `code-review=pass`。
- **根查看器能力不回退**：`copy_review_tool` + `tools/` bundle 未动（verify 核实）。
- **回归**：仓级 `pytest` 364 passed（+2 负例）；E2E 真实 `init.py init` 自愈闭环验证（退役 hook 摘除 + 根锚渲染 + 每目录 stub=0）。

## ⏳ 未完成 / 延后（批次 `drop-per-dir-review-stub`，见 `openspec/issues/batches.md` + `INDEX.md`）

代码审 defer 2 项（均 PROPOSED 入本批次）：

- **T44（P2，基础设施）** — 退役 hook 自愈未接进 toolkit 标准更新路径（setup.sh/README）。属 setup.sh 责任扩张，超本 change ADR-1（per-project init/update 触发）范围。
- **T45（P3，功能增强）** — 给 engine.js 加 hash 深链（`/review.html#/changes/X/`），补齐本 change 的**可接受降级**（根查看器丢了 per-change scoped 深链）。

**无 ≥2 方案延后决策**；**verify 无 Minor 缺口**（文档已同步）。

## ⚠️ 合并后必做（CR-V1 缓解）

本仓（dogfood 消费者）合并后**须先跑一次 `sdflow-init update`**（或 `init`）触发 `retire_hooks` 自愈——清掉本机残留的 `~/.claude/hooks/change-review-stub.py` + `settings.json` 注册。否则该 working copy 仍会在新建 change 时产每目录 stub（本 change 的删除对本机不生效，直到自愈跑一次）。

## ▶ 下一阶段建议

- 开一个 **cleanup change 清批次 `drop-per-dir-review-stub`**（T44 + T45）：T44 优先（部署一致性，避免其它消费仓/本机遗留），T45 可与 T44 同 change（都围绕 review 工具收尾）或单独排 P3。
- T44 落地时需一个设计小决策：自愈接进 setup.sh（扩 setup 责任）vs 独立 `sdflow-init cleanup` 命令 vs 仅文档要求——建议走 grill/轻设计审定夺。
