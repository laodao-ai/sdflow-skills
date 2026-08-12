---
ship-gate:
  verify: PASS
  reviewed_sha: 082d0284e85038f63ad5a12a301cbf6fba5e4545
---

# Verify Report: implement-workflow-optimization-2026-08-p4

**结论：PASS**（核心功能全部实现并有机械测试覆盖；task 4.3 书记性更新未执行属 Minor 级缺口，
不阻塞归档，在 hand-off 注明待补。）

## 全仓测试套件

| 层 | 命令 | 结果 | SHA |
|---|---|---|---|
| pytest (全量) | `/usr/bin/python3 -m pytest -q --tb=line` | **2639 passed, 10 skipped, 0 failed** (393s) | `082d0284` |

## 逐需求核对表

### Task 1 · B25/B26 修复 + ship_gate 机械门（P0）

| 需求 | 判定 | 证据锚 |
|---|---|---|
| 1.1 B25 诊断定案 | ✅ | `impl-reports/task5-skill-adaptation.md:1-38`（结论 = 未调用、非调用失败；6/6 archived reports 零锚） |
| 1.2 锚存在门：lens-metric 检查 | ✅ | `sdflow-ship/scripts/ship_gate.py:1722-1729`（`_lens_metric_layer_present`） |
| 1.2 锚存在门：ref-check 检查 | ✅ | `sdflow-ship/scripts/ship_gate.py:1732-1740`（`_ref_check_present`） |
| 1.2 三态 config（缺省放行/true 拦截/坏值 fail-closed） | ✅ | `sdflow-ship/scripts/ship_gate.py:1662-1689`（`metrics_enabled`） |
| 1.2 config 文件不存在 => 放行 | ✅ | `sdflow-ship/scripts/ship_gate.py:1676-1678`（`if not cfg.exists(): return False`） |
| 1.2 fence-aware 解析 | ✅ | `sdflow-ship/scripts/ship_gate.py:1692-1703`（`_fence_outside_text_lines` + `FenceTracker`） |
| 1.2 verdict 复用 STEP_IN_PROGRESS | ✅ | `sdflow-ship/scripts/ship_gate.py:2021,2024,1916` |
| 1.3 defer 台账窄化提取（id 列） | ✅ | `sdflow-ship/scripts/ship_gate.py:1782-1808`（`_defer_ledger_id_cells`，按表头定位 id 列） |
| 1.3 T\d+\|B\d+ id 正则 | ✅ | `sdflow-ship/scripts/ship_gate.py:1765`（`_TICKET_ID_RE`） |
| 1.3 文件系统存在性判定 | ✅ | `sdflow-ship/scripts/ship_gate.py:1843`（`Path.glob`，非 git 跟踪） |
| 1.3 source_change 字段比对 | ✅ | `sdflow-ship/scripts/ship_gate.py:1847-1850` |
| 1.3 四类 cause 区分 | ✅ | `sdflow-ship/scripts/ship_gate.py:1841,1845,1849` + pass path |
| 1.4 config 态矩阵测试 | ✅ | `sdflow-ship/tests/test_gate_report_anchors.py:113-172`（7 unit tests：缺文件/缺段/缺键/true/false/非 bool/坏 yaml） |
| 1.4 锚缺失/在场/仅缺 ref-check 测试 | ✅ | `sdflow-ship/tests/test_gate_report_anchors.py:251-291` |
| 1.4 defer 无 id/池文件缺失/change 不符测试 | ✅ | `sdflow-ship/tests/test_gate_report_anchors.py:341-395` |
| 1.4 描述列旧票号不误抓（窄化负例） | ✅ | `sdflow-ship/tests/test_gate_report_anchors.py:199,386` |
| 1.4 聚合摘要句不假阳 | ✅ | `sdflow-ship/tests/test_gate_report_anchors.py:211` |
| 1.4 fence 假阳负例 | ✅ | `sdflow-ship/tests/test_gate_report_anchors.py:182,187,216` |
| 1.5 Step4 recorder add + source_change + id | ✅ | `sdflow-code-review/SKILL.md:406-417` |
| 1.5 台账机读结构（表格 + id 列） | ✅ | `sdflow-code-review/SKILL.md:698-713` |
| 1.5 聚合摘要改写出 gate 检测范围 | ✅ | `sdflow-code-review/SKILL.md:711-713` |
| 1.5 Step3 ref-check 结构化锚 | ✅ | `sdflow-code-review/SKILL.md:373-381,690-692` |
| 1.5 Step5 义务措辞对齐 | ✅ | `sdflow-code-review/SKILL.md:477-498`（独立 Step 7，历史证据注记） |
| 1.5 recorder 失败 fail-loud | ✅ | `sdflow-code-review/SKILL.md:414-417` |
| 1.6 B25 修复落地 | ✅ | `impl-reports/task5-skill-adaptation.md:40-63`（gate 机械兜底 + SKILL step 提级双修） |

### Task 2 · 面 A · effort 分档（P1）

| 需求 | 判定 | 证据锚 |
|---|---|---|
| 2.2 model-tiers.md effort-tier-defaults 机读块 | ✅ | `sdflow-init/assets/workflow/model-tiers.md:46-50`（claude.strong=high/mid=medium/light=low） |
| 2.2 model-tiers.md 表格 effort 列 | ✅ | `sdflow-init/assets/workflow/model-tiers.md:11-15` |
| 2.2 resolve-models.sh effort 提取/导出 | ✅ | `sdflow-init/assets/hack/resolve-models.sh:83-98`（`_default_get` 行锚定）, `:288-309`（`_resolve_effort_tier`）, `:351-353`（export） |
| 2.2 头注释 9 变量清单 | ✅ | `sdflow-init/assets/hack/resolve-models.sh:5-16` |
| 2.2 值域校验 + 非法回落告警 | ✅ | `sdflow-init/assets/hack/resolve-models.sh:111-117`（`_valid_effort_value`）, `:300`（fallback 告警） |
| 2.2 codex/unknown 显式空串初始化 | ✅ | `sdflow-init/assets/hack/resolve-models.sh:314-316,325,339`（不复用 `_resolve_tier`） |
| 2.3 claude 导出缺省值测试 | ✅ | `sdflow-init/tests/test_resolve_models.py:306`（`test_claude_host_exports_effort_defaults_without_override`） |
| 2.3 codex 空串无噪声测试 | ✅ | `sdflow-init/tests/test_resolve_models.py:315`（`test_codex_host_effort_vars_are_empty_with_no_warning_noise`） |
| 2.3 unknown 空串测试 | ✅ | `sdflow-init/tests/test_resolve_models.py:326` |
| 2.3 覆盖生效测试 | ✅ | `sdflow-init/tests/test_resolve_models.py:339,372`（含值域全量参数化） |
| 2.3 非法值回落告警测试 | ✅ | `sdflow-init/tests/test_resolve_models.py:361` |
| 2.3 eval 契约测试 | ✅ | `sdflow-init/tests/test_resolve_models.py:382`（9 变量一次 eval） |
| 2.4 5 个 effort agent 定义 | ✅ | `sdflow-spec/agents/sdflow-effort-{low,medium,high,xhigh,max}.md`（frontmatter: name/description 含排他声明/model:inherit/effort:<值>） |
| 2.4 install_agents 幂等/守卫/孤儿测试 | ✅ | `hack/tests/test_install_agents.py:435-548`（4 个 effort 专项测试） |
| 2.5 四个编排 SKILL 接 effort | ✅ | `sdflow-spec-review/SKILL.md:179,293-301`; `sdflow-code-review/SKILL.md:201,336-344`; `sdflow-implement/SKILL.md:174,177-189`; `sdflow-done/SKILL.md:198,211,370,435` |
| 2.5 subagent_type 构造 + 空值回落 | ✅ | 四 SKILL 均含 `sdflow-effort-$SDFLOW_EFFORT_<档位>` + 空值不带 subagent_type |
| 2.5 门禁步 >= high 铁律句 | ✅ | 四 SKILL 均含 MUST NOT 低于 high |
| 2.5 unset 清单扩 SDFLOW_EFFORT_* 三变量 | ✅ | `hack/tests/test_tier_resolution_parity.py:254-265`（机械守 9 变量一致性） |
| 2.6 config.template effort-tiers 段 | ✅ | `sdflow-init/assets/workflow/config.template.yaml:77-85` |
| 2.6 init.py lint_config 扩 effort-tiers | ✅ | `sdflow-init/scripts/init.py:663-664,717-748,834-846` |
| 2.6 init 测试覆盖 | ✅ | `sdflow-init/tests/test_config_lint.py:266-406`（15 个测试用例） |

### Task 3 · 面 B · dispatch prompt 构造（P2）

| 需求 | 判定 | 证据锚 |
|---|---|---|
| 3.1 render-review-prefix.sh 存在 + --layer 参数 | ✅ | `sdflow-init/assets/hack/render-review-prefix.sh:23-41` |
| 3.1 固定序 cat：通则 + 通用契约 + base checklist | ✅ | `sdflow-init/assets/hack/render-review-prefix.sh:74,76-108,110` |
| 3.1 通用契约含 findings schema/引文纪律/封顶句/不问人 | ✅ | `sdflow-init/assets/hack/render-review-prefix.sh:80-108` |
| 3.1 源缺失 fail-loud（problem+cause+fix） | ✅ | `sdflow-init/assets/hack/render-review-prefix.sh:45-70`（6 个 exit 2/64 点） |
| 3.1 不输出半段前缀 | ✅ | `sdflow-init/assets/hack/render-review-prefix.sh:72-73`（注释 + 结构保证） |
| 3.1 byte-stable golden 测试 | ✅ | `hack/tests/test_render_review_prefix.py:104-110`（`test_output_is_byte_stable_across_two_runs`） |
| 3.1 源缺失非零退出测试 | ✅ | `hack/tests/test_render_review_prefix.py:154-188`（4 个缺失场景） |
| 3.2 spec-review SKILL 三段组装 | ✅ | `sdflow-spec-review/SKILL.md:304-323`（段①脚本原文引用 + 段② per-镜 + 段③动态） |
| 3.2 code-review SKILL 三段组装 | ✅ | `sdflow-code-review/SKILL.md:310-332` |
| 3.2 散文契约收敛为引用 | ✅ | `sdflow-spec-review/SKILL.md:313`; `sdflow-code-review/SKILL.md:318-319`（MUST NOT 复制粘贴） |
| 3.3 setup.sh hack 拷贝部署 | ✅ | `setup.sh:536-545`（`*.sh` glob 含 render-review-prefix.sh） |

### Task 4 · 实现验证收尾

| 需求 | 判定 | 证据锚 |
|---|---|---|
| 4.1 全仓 pytest 绿 | ✅ | 本次跑：2639 passed, 10 skipped, 0 failed @ `082d0284` |
| 4.2 retro 再生冒烟 | ✅ | `retro_report.py` 跑通；`openspec/retro/report.md:71,165` 含 p4 token-log 锚（out 1.2M / in 1.6k / cc 2.6M / cr 128.5M） |
| 4.3 roadmap 阶段 4 回填 | **GAP (Minor)** | `openspec/roadmaps/workflow-optimization-2026-08/roadmap.md:274-280` 仍为雾区、无子任务表；task-log 无阶段 4 里程碑 |
| 4.3 B25/B26 池状态 set-status FIXED | **GAP (Minor)** | `openspec/issues/open/bug/B25.md` status=OPEN；`B26.md` status=OPEN |
| 4.3 T105/T103/T98/T124 set-status DONE | **GAP (Minor)** | `T105.md` status=PROPOSED；`T103.md` status=PROPOSED；`T98.md` status=PROPOSED；`T124.md` status=PROPOSED |

## 缺口清单

| # | 严重度 | 描述 | 处置建议 |
|---|---|---|---|
| G1 | Minor | task 4.3 书记性更新未执行：6 个 issue 池状态（B25/B26→FIXED, T105/T103/T98/T124→DONE）+ roadmap 阶段 4 回填 + task-log 里程碑。tasks.md 复选框标 `[x]` 为假绿 | 归档前或 hand-off 中补执行 `set-status`；roadmap 回填可在 `/sdflow-done` archive 步一并处理 |

## 判定依据

- **核心功能（Tasks 1-3, 4.1-4.2）**：ship_gate 双门（锚存在 + defer 对账）、effort 分档全链路
  （resolver → agent 定义 → install_agents → 四 SKILL 派发 → config lint）、dispatch prompt 三段
  组装脚本，均有代码实现 + 机械测试覆盖（2639 passed），无核心缺失。
- **Gap G1 为纯书记性操作**（issue 池 frontmatter 字段翻转 + roadmap 文档回填），不影响任何
  代码路径或机械门行为。tasks.md 的 `[x]` 标记不准确（假绿），但该操作本身可在 done 流程中
  完成，不阻塞 verify 判定。
- **综上判 PASS**。
