# Verify Report — workflow-metrics-loop

日期：2026-07-06

## 结论：PASS

<!-- ship-gate: verify=PASS -->

证据锚点全部机验（契约字段/聚合器代码行/测试名/config 值/commit）；无核心缺口。仅 1 项 INDEX 索引未登记新契约，判 ⚠️Minor（文档索引 polish，契约文件本体存在且被消费者正确引用、随 canonical 部署覆盖）。

## 逐需求核对表

| 需求 | 代码出处（文件:行 / 测试） | 状态 |
|---|---|---|
| 1.1 契约锚形/字段/取值域/site/sev 子格式定序/enum 治理 v2/config 门控/fence MUST | `lens-metric-contract.md:1-32`（锚形 L4、字段域 L6-14、归属钉死 L16-19、折叠表 L21-24、enum治理 L25-26、config门控 L28-29、示范锚 fence MUST L31-32） | ✅ |
| 1.2 bundle INDEX 登记新规范 | `openspec/INDEX.md:13-24` 规则表**未列** lens-metric-contract.md（tools/、spec-checklists 同为未列，INDEX 为curated子集）；但契约随 canonical(assets/workflow/)部署、三 SKILL 直引"规则根…唯一权威源" | ⚠️Minor |
| 2.1 code-review Step3 落锚 + voice分桶吸收 + 台账同步 + 只引用 | `sdflow-code-review/SKILL.md:85,92-93,102-103,166-171`；`grep -c 'voice分桶:'`=0（活指令零，2 处均"已被吸收取代"描述） | ✅ |
| 2.2 spec-review 每镜落锚 + 只引用不复制 | `sdflow-spec-review/SKILL.md:73,78,100-102` | ✅ |
| 2.3 独立导出 + 自检扩枚举(缺字段/layer/lens/runner/sev越域阻塞) + 数值属信任边界 + SR-M 拍板最终化 + 旁路声明 | code-review `:109-117`；spec-review `:79-80,115-121`（SR-M best-effort）+ 旁路 code-review `:117` | ✅ |
| 2.4 机械核对无残留 voice分桶 prose | `grep -c voice分桶` spec-review=0、code-review=2(均描述性)；`'voice分桶:'`=0 | ✅ |
| 3.1 只读聚合器：fence-aware(长度感知)/parse_anchor行首独占/runner入键/坏文件try-except/数值非法flag/无锚计数/不写持久/不import ship_gate | `lens_metric_aggregate.py`: `_fence_aware_lines`(L20-36 长度感知嵌套)、`parse_anchor` strip+startswith(L39-46)、key含 runner(L104)、aggregate try/except(L65-77)、`_int` bad flag(L80-90)、no_anchor 计数(L75)、仅 print 不写文件(L156)、无 ship_gate import(grep 仅docstring) | ✅ |
| 3.2 正例 ≥2 归档锚聚合成表 | `test_aggregate_two_changes`(L63) | ✅ |
| 3.3 反例矩阵(fence/漂移/缺字段/越域/sev/substring/坏编码/嵌套fence/非法数值/负值) | `test_fence_block_lines_skipped`,`test_malformed_anchor_does_not_corrupt`,`test_out_of_enum_lens/layer_flagged`,`test_sev_subformat_robust`,`test_non_anchor_line_returns_none`(行中非行首哨兵),`test_bad_encoding..`,`test_nested_fence_length_aware_no_leak`,`test_illegal/negative_numeric_value_flagged`,`test_unclosed_fence..` | ✅ |
| 3.4 端到端 独立列非空（真值入表） | `test_render_table_has_independent_and_flags`(L76: 断言 `| 20 |`、`| 50 |` 真值) | ✅ |
| 4.1 per-镜泛化 采纳率+独立率双列 + 人决声明 | code-review `:119-123`、spec-review `:104` | ✅ |
| 4.1b maintain surfacing 步(≥10 显著提示、不判断、不埋长报告)所有路径可达 | `sdflow-maintain/SKILL.md:69-94`；`继续执行步骤 5`×2(L63,66)+`直接执行步骤 5`(L41) 三分支全可达 | ✅ |
| 4.1c 可选 site 字段(仅 outside-voice、键升含 site、聚合解析) | 契约 `:10-12`；聚合器 key 含 site(L104)、`test_runner_distinguishes_outside_voice` | ✅ |
| 4.1d config `metrics.enabled` 门控 + 默认值 | 源仓 `openspec/config.yaml:60-62`=true；模版 `assets/workflow/config.template.yaml:64-65`=false；契约 `:28-29` | ✅ |
| 4.2 grill 不落锚 + T54 留档(口径未定义/非本 change/T29 伞下) | 两 SKILL 无 grill 落锚指令；`issues/todolist/2026-07-todolist.md:62,715-742`(T54 全字段) | ✅ |
| copy_bundle 排除 tools/tests | `init.py:129` ignore_patterns("tests")；`test_init.py:113 test_tools_tests_not_deployed`+`:122 full_flag_still_includes`（41 passed） | ✅ |
| 5.1 delta 对码一致 + openspec validate | `openspec validate workflow-metrics-loop` → valid | ✅ |
| 5.2 setup.sh 部署 canonical | checkpoint `d3c18b4 task9-deploy` | ✅ |

## 测试实况

- 聚合器：`python3 -m pytest sdflow-init/assets/workflow/tools/tests/ -q` → **19 passed**
- init：`python3 -m pytest sdflow-init/tests/test_init.py -q` → **41 passed**
- 已知无关红：`sdflow-ship/tests/test_gate_anchor_scope.py::test_contract_archived_corpus_anchor_hits` FAIL — pre-existing，main 分支同红，该测试文件由 gate-anchor / cross-model change 触及，与本 change 无关，判 PASS 注明。

## 缺口清单

- 无核心缺口。
- ⚠️Minor（不阻塞）：`openspec/INDEX.md` 规则表未登记 `lens-metric-contract.md`（task 1.2 前半）。判 Minor 理由：INDEX 规则表为 curated 子集（tools/、spec-checklists 详细项同未逐一列），契约文件本体存在、随 canonical(assets/workflow/) 部署被 `sdflow-init update` 覆盖（1.2 后半"权威源纪律"已满足），且三 SKILL 均直引"规则根 lens-metric-contract.md，唯一权威源"，功能与可发现性不受损。可后续补一行索引。

PASS
