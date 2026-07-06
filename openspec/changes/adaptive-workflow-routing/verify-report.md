# verify 报告 — adaptive-workflow-routing

> 收尾终门。每 ✅ 挂可机验锚点（测试名 / 文件:行 / commit / 命令输出）；无锚 ✅ 降 gap。Do-Not-Trust 冷启。

## 需求 → 证据核验

**Requirement（spec-workflow MODIFIED）：sdflow-code-review 为每次全跑的独立强制主审——两层深度按逻辑面自适应**

| Scenario / 主张 | 证据锚 | 判定 |
|---|---|---|
| Step1（scope-drift+完成度）恒跑不降 | `sdflow-code-review/SKILL.md` 第一步（:57）未改、判器门控只在 Step2 前；SKILL:64-70 明写「Step1 已恒跑守卫」 | ✅ |
| Step2 仅机判无逻辑面白名单免 | `SKILL.md:64-70` 接入 `trivial_shape.py`，exit 0=EXEMPT→免 fan-out；exit 1/2→照常 | ✅ |
| 有逻辑面照跑多镜 | `test_comment_plus_logic_not_exempt` / `test_mixed_one_logic_file_not_exempt` | ✅ |
| 白名单三形状命中 | `test_py_comment_only_exempt` / `test_new_test_file_exempt` / `test_version_file_exempt` / `test_docs_dir_txt_exempt` | ✅ |
| 行为面路径护栏（改 SKILL/workflow/gate 即便 markdown 也 NOT） | `test_skill_md_behavior_path_not_exempt` / `test_workflow_md_behavior_path_not_exempt` / `test_ship_gate_behavior_path_not_exempt` | ✅ |
| load-bearing 版本常量不免 | `test_api_version_in_code_not_exempt` | ✅ |
| scope-drift 揭穿伪装 | 判器只判 diff 形状、伪装逻辑由 Step1 守卫（SKILL:64-70 措辞）；伪装成注释的逻辑=`logic-line`→NOT（`test_comment_plus_logic_not_exempt`） | ✅ |
| 危险方向守卫（logic→EXEMPT 全堵） | code-review F1-F7 全修 + `test_requirements_txt/docs_dir_code/readme_named_code/mode_only_chmod/removed_line_dashdash/copy_detected_not_exempt` | ✅ |
| dogfood 自洽（本 change NOT_EXEMPT） | 命令输出 `[trivial_shape] NOT_EXEMPT — non-doc-markdown/behavior-path`（commit `task1-impl` 后运行） | ✅ |

## 测试证据
- 判器单测：**34 passed**（`test_trivial_shape.py`，含 F1-F7 危险方向补洞 12 例）。
- 全仓回归：**429 passed, 1 failed**——唯一 failed = `test_gate_anchor_scope::test_contract_archived_corpus_anchor_hits`。

## Gap / 已知残余（不阻断，诚实留痕）
- **B5（pre-existing，非本 change 引入）**：上述唯一 failed。**已独立验证 clean main 亦红**（切 main 单跑 `1 failed`）——归档报告 ship-gate 锚在 fenced 示例块内、契约测试过严。归 workflow-metrics-loop hand-off 已记录的 B5，可随任一 ship-gate change 顺手修。**非本 change 回归。**
- **T56（新记 todolist）**：判器 F6 残余（tests/ 免多镜排除未盖 plugins/* 等）+ 更宽轻量化已证不可做的留档。低危、非阻断。
- **激活未做**：`setup.sh` 部署到全局 canonical 属激活步（merge→push→`/sdflow-upgrade`），非本地验证前提（判器已 pytest 直测、非经 canonical 路径）。

## 结论
本 change 需求逐条有机验锚点、34 判器测试全绿、危险方向 7 洞全堵、dogfood 自洽；唯一 failed 已证 pre-existing 非本 change。

<!-- ship-gate: verify=PASS -->
