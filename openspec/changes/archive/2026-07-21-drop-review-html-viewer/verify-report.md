---
ship-gate:
  verify: PASS
  reviewed_sha: 233775f323ce5ca012015a698ac67fcc4ab9c08a
---

# verify-report — drop-review-html-viewer

**结论：PASS**（核心功能删除完整、退役自愈机制到位、机械层脚本未误删；无核心缺口，无 Minor 遗留）
**日期**：2026-07-21
**change**：drop-review-html-viewer

## 逐需求核对表

| 需求/任务 | 代码出处（文件:行/测试） | 状态 |
|---|---|---|
| T1.1 删 `REVIEW_TOOL_SRC` 常量、`copy_review_tool()` 函数、`run()` 调用与报告行 | `grep copy_review_tool\|REVIEW_TOOL_SRC sdflow-init/` → 零命中 | ✅ |
| T1.2 加 `RETIRED_DEPLOY_FILES` + 签名门控 | `init.py:94-97`（`review.html`→`__OPENSPEC_PROJECT_NAME__`、`serve.sh`→`openspec-review-serve-`） | ✅ |
| T1.2 `retire_deploy_files(root)` 签名门控删除、fail-safe | `init.py:255-278`（isfile 检查 → 读文件（OSError/UnicodeDecodeError 跳过）→ signature not in content 跳过 → os.remove（OSError pass）） | ✅ |
| T1.2 `run()` init/update 都调用并入报告 | `init.py:823`（`report.append("退役部署文件清理：\n" + retire_deploy_files(root))`，紧邻 `retire_hooks()`） | ✅ |
| T2.1 删 `sdflow-init/assets/review-tool/` | 目录不存在 | ✅ |
| T2.2 删 assets `tools/{engine.js,engine.css,vendor/,review-stub.html}` | 四项均不存在 | ✅ |
| T2.3 删 `sdflow-init/memo-review-html-tool.md` | 不存在 | ✅ |
| T3.1 删 `openspec/{serve.sh,review.html}` | 两项均不存在 | ✅ |
| T3.2 删 `openspec/workflow/tools/` 查看器资产 | engine.js/engine.css/vendor/review-stub.html 均不存在 | ✅ |
| **反向核对：机械层脚本必须保留** | assets 源 6 个全在（anchor_lint/lens_metric_emit/outside_voice_guard/hr_tg_intersect/review_disposition_check/trivial_shape）；本仓 `openspec/workflow/tools/` 同 6 个全在 | ✅ |
| T4.1 删 `sdflow-init/tests/engine.test.js` | 不存在 | ✅ |
| T4.2 test_init.py 摘查看器测试 + 加清理测试 | `test_init.py:17 class TestRetireDeployFiles`（清理 :38 / 跳过无签名用户文件 :42 / fresh no-op :50 / 幂等 :57 / e2e run :65-70）；`:94 assert not engine.js exists` | ✅ |
| T4.2 test_runtime_gitignore stub 换 retire_deploy_files | `test_runtime_gitignore.py:19 monkeypatch.setattr(INIT, "retire_deploy_files", lambda _root: "")` | ✅ |
| buglist DOGFOOD_OVERLAY_DELTAS T47 条目 | `test_task5_delivery_contract.py:149 "T47": {"status": ("PROPOSED", "WONTDO")}` | ✅ |
| T4.3 测试全绿 | `/usr/bin/python3 -m pytest sdflow-init/tests/ -q` → 303 passed, 1 skipped；buglist contract → 8 passed | ✅ |
| T5.1 SKILL.md 去查看器 | `sdflow-init/SKILL.md:176/179` 仅剩「退役名单含 …（已废弃/已整体移除）」的退役注记，无活引用 | ✅ |
| T5.2 sdflow-roadmap SKILL 删 serve.sh/review.html 行 | grep 零命中 | ✅ |
| T5.3 ROADMAP.md / INDEX.md / todolist 引用清理 | `ROADMAP.md:34` 已改为「已由 drop-review-html-viewer 整体移除」注记；INDEX.md 零命中 | ✅ |
| adr/0003 加注 | `adr/0003:3` 顶部「部分被取代（2026-07，drop-review-html-viewer）」注记，决策本身不变、review UI 收缩为机械层脚本 | ✅ |
| T47 置 WONTDO | 机器索引 frontmatter `todolist:8 status "WONTDO"`；详细块 `:801` 有「PROPOSED → WONTDO（engine.js 已被删除，载体不存在）」overlay 注（dogfood overlay 机制，contract test 已守） | ✅ |
| T6.1 冷读全 diff（机械脚本未误删/签名门控正确/无悬挂引用） | 见上机械层反向核对 + 悬挂引用扫描（仅剩退役注记，无活引用） | ✅ |
| T6.2 dogfood 验证（本仓不再铺查看器、机械脚本仍在） | 本仓 `openspec/workflow/tools/` 已只余 6 机械脚本 + `openspec/` 根无 serve.sh/review.html | ✅ |

## 缺口清单

**核心缺口**：无。查看器全部资产与铺设代码已从权威源、本仓 dogfood 副本、测试、文档中删净；`retire_deploy_files` 签名门控删除 + fail-safe（读失败/无签名/删失败均保守跳过）实现正确并在 run() init/update 调用；6 个评审机械层脚本（assets 源 + 本仓副本）均完好保留。

**Minor 缺口**：无。SKILL.md / ROADMAP.md / adr/0003 中所有对查看器的提及均为「已移除/已废弃」的退役注记（符合 DOC-1 演进史注记性质），非悬挂活引用。T47 detail 块 legacy 行 frozen 于 PROPOSED、机器索引 overlay 为 WONTDO，属既有 dogfood overlay 机制，contract test 已断言守护。

PASS
