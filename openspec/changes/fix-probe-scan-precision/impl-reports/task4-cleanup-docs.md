# Task 4 实现报告：ship_gate 腿退役 + 死件清理 + 文档面级订正

**Blocked-by:** 2, 3（均已完成，见 task2-resolver-init.md / task3-warnings.md）
**R-ID:** R6（spec-workflow MODIFIED bundle 下发后果）、R7（encoding-hygiene）、R8（yq-yaml-operations）、R9（workflow-metrics）

## 范围

tasks.md 第 5、6 节，14 条验收标准（5.1–5.4、6.1–6.11 拆细算共 14 条）。第 7 节（全链路验证）不在本
ticket——留给独立的验证 ticket。

## 第 5 节：`ship_gate` 失鲜腿退役

| 子任务 | 状态 | 说明 |
|---|---|---|
| 5.1 删 `tools_spec` 比较腿 | ✅ | `sdflow-ship/scripts/ship_gate.py` 原 `:953-959`，含两行旧注释一并删除 |
| 5.2 退役理由按仓型分开写 | ✅ | 新注释明确区分 toolkit 源仓（顶层腿覆盖，`sdflow-init` 顶层条目 tree oid 必翻）与消费仓（镜像不复存在，动作不可能发生），**未**用「顶层腿覆盖」概括消费仓 |
| 5.3 正向锚 | ✅ | `sdflow-ship/tests/test_gate_tools_leg_retirement.py::test_forward_anchor_toolkit_source_change_is_still_stale` |
| 5.4 反向锚（MUST NOT 省略） | ✅ | 同文件 `test_reverse_anchor_consumer_mirror_change_alone_is_fresh` |

新建 `sdflow-ship/tests/test_gate_tools_leg_retirement.py`（2 用例）。反向锚已实测验证「会红」：
`git stash` 回退 `ship_gate.py` 改动后单独跑该测试文件，`test_reverse_anchor_consumer_mirror_change_alone_is_fresh`
报 `AssertionError: assert (True, 'stale') == (False, 'fresh')`（旧 `tools_spec` 腿判 stale），正向锚
两版本均绿（顶层腿本就覆盖，符合 C14 论证）；`git stash pop` 已还原。

## 第 6 节：死件清理 + 面级文档订正

| 子任务 | 状态 | 说明 |
|---|---|---|
| 6.1 删本仓 `openspec/workflow/` 下 7 个文件 | ✅ | `git rm` 删除 `tools/` 全部 6 个 `.py` + `lens-metric-contract.md`，只留 `WORKFLOW-GUIDE.md`（随 6.10 重新生成） |
| 6.2 `test_yq_wrapper_consistency.py` 去镜像 | ✅ | `TARGETS` 删 `openspec/workflow/tools/anchor_lint.py` 条目，计数 7→6；docstring/断言消息同批订正（`7 份`→`6 份`、差异枚举里"两份 anchor_lint.py"改单数）；`openspec/specs/yq-yaml-operations/spec.md` Purpose 段脚本枚举同批订正为 6 个 |
| 6.3 `check_encoding_hygiene.py` 删不可达分支 | ✅ | 删 `:83-84` 的 `openspec/workflow/tools/` 排除分支；`test_encoding_hygiene.py` 的恒真锚（原 `test_canonical_bundle_source_is_not_excluded_with_its_mirror`）改写为 `test_target_globs_are_root_anchored_and_never_reach_consumer_mirror`——新增对 `TARGET_GLOBS` root-anchored 性质的结构断言，判据=定点把某条 pattern 改宽即可让本用例失败 |
| 6.4 托管块权威源订正 | ✅ | `sdflow-init/assets/snippets/claude-section.md`：3 处「本仓有 `openspec/workflow/` 规则副本则用之」改为「真相源=全局 canonical，两步链解析，消费仓不再持有规则副本」；「INDEX 同步（仅规则副本 pin 仓…）」改为「仅 toolkit 源仓维护 canonical bundle 时适用」。改后已对本仓跑等效 `sdflow-init update`（见下「sdflow-init update 执行说明」）刷新 `CLAUDE.md`/`AGENTS.md` 托管块 |
| 6.5 CLAUDE.md 非托管区 4 处 + AGENTS.md 4 处 | ✅ | CLAUDE.md：①`openspec/workflow/` 描述改为「只保留 WORKFLOW-GUIDE.md」②测试三层第 2 层改 `SDFLOW_HOME` 重定向语义③「pin 免疫全局翻动逃生口」表述移除④回滚节补 `git revert`→重跑 setup→各仓重跑 update 顺序。AGENTS.md：仓库解剖行、沙盒消费仓层描述、`per-project pin`/`pin 免疫`收尾句共 3+ 处同批订正（管理块内 2 处随 `sdflow-init update` 自动刷新，非托管区 2 处手工订正） |
| 6.6 修法文案口径统一 | ✅ | `lens_metric_emit.py:104`、`resolve-models.sh:74`、`sdflow-upgrade/SKILL.md`（frontmatter + body 步骤 4）统一为「回运行 checkout 跑 `bash setup.sh`」；`README.md:119` 按设计要求原样保留（GUIDE/schema 用途合法） |
| 6.7 docs 面 | ✅ | `workflow-map.md`（§4 段首 + resolve-workflow.sh 行 + §6 两处）、`workflow-map.html`（同构 4 处）、`02-module-reference.md`（mermaid 图 G 节点 + 边 + 一句 prose）、`sdflow-spec-review.md`（resolve-workflow.sh 一行）、`ROADMAP.md`（两处历史决策追加指针注记，原文不改）全部订正 |
| 6.8 ADR 面 | ✅ | 0003/0005/0019/0036 各加状态注记指针（不重写正文）；`adr/0038` 删除；新落 `adr/0039-eliminate-dual-distribution-chain.md`（Context/Decision/Considered Options/取舍段/时序/Migration Plan/回滚/Consequences 全节齐全） |
| 6.9 CONTEXT.md + T269/T270 | ✅ | 补 `skew` 术语（区分「已消灭的 bundle 拷贝链 skew」与「仍在用的 manifest skew」）；`pin` 未入 CONTEXT。T269 用 `issues_v2.py set-status --to DONE` 分治关闭（evidence 记录 lens-metric-contract.md 成立/GUIDE 误判）；T270 用 `set-status --to WONTDO` 关闭（reason 写「skew 探测段整体移除，问题对象消失」，未写"已修复"） |
| 6.10 GUIDE 链接降级 + 重新生成 | ✅ | `hack/gen_workflow_guide.py` 新增 `_SIBLING_LINK_RE`/`_downgrade_sibling_link`，把 `ff-generation-constraints.md`/`quality-layering.md`×4/`workflow-history.md` 共 6 处相对链接降为纯文字（inline code），BANNER 加一句降级说明；`--write` 重新生成两份 `WORKFLOW-GUIDE.md`（canonical 源 + 本仓消费副本，字节一致） |
| 6.11 记 4 条 todo | ✅ | 用本仓开发 checkout 脚本 `sdflow-issues/scripts/issues_v2.py add`，均显式传 `source_change: "fix-probe-scan-precision"`：T271（hack 链 symlink 化根因项，含 capability-manifest 扩员备选）、T272（resolver `--help`）、T273（`setup.sh` skipped 应非零退出）、T274（Windows 失鲜 CI 回归用例） |

## `sdflow-init update` 执行说明（偏离记录）

`python3 sdflow-init/scripts/init.py update` 直接跑会在 `migrate_changes()` 处报
`ERROR: 文件系统操作失败：schema marker 不可解析：./openspec/changes/fix-probe-scan-precision/.openspec.yaml`
——该文件是 `openspec new change --schema sdflow-spec-driven` 生成的真实 project-local schema marker
（`schema:` + `created:` 两个键），而 `_marker_schema()` 的严格校验假设 marker **只可能**是
`migrate_changes` 自己写的单键格式，命中额外 `created:` 键即 fail-closed。**这是与本 change 目标无关
的预先存在的缺陷**（不在 tasks.md 5/6 节范围，未修复代码，未记新 todo——已有 T271-T274 的既定四条,
超范围加宽会违反通则③）。

为不阻塞托管块刷新，改为直接调用 `init.py` 内部函数完成等效操作：
- `inject(CLAUDE.md, *MARK_DOC, read_snippet("claude-section.md"))` / 同法处理 `AGENTS.md`
  ——与 `update` 主流程里刷新托管块那步完全一致的调用，仅跳过了会报错的 `migrate_changes` 步骤。
- `copy_bundle(".", include_schema=True)` ——刷新本仓 `openspec/workflow/WORKFLOW-GUIDE.md`
  与 `openspec/schemas/` project-local schema，与 `update` 主流程的铺设步等价。

`git diff CLAUDE.md AGENTS.md` 确认改动仅限托管块内容本体，无其它副作用；`openspec/workflow/WORKFLOW-GUIDE.md`
经 `diff` 核对与 `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md`（canonical 源）字节一致。

## 概念词表自查（非 7.6 完整 sweep，仅自查本 ticket 引入的新增命中）

对 `local-pin` / `两条分发链` / `显式 pin` / `pin 遮蔽` 四个归零词做了一轮自查：
- 本 ticket 新写的 `CLAUDE.md`/`AGENTS.md`/`adr/0039` 中出现的字面命中已改写为同义 paraphrase
  （如「resolver 的本地规则副本判定分支」替代 `local-pin`），仅 `adr/0039`「取舍：被否决的候选」节
  （设计豁免的段落）保留原字面（描述被否决方案本就需要该词）。
- 遗留的字面命中（未改动）：`adr/0003`/`adr/0005` **原有正文**（按 6.8 明确要求「不重写历史正文」，
  只加指针注记）；`sdflow-init/tests/test_init.py`/`sdflow-maintain/tests/test_maintain_scan.py` 里
  作为负断言字符串字面量出现的 `"显式 pin"`（测试 6.4/task3 已完成的功能，属 task3 范围）；
  `openspec/specs/{maintain-scan,spec-workflow}/spec.md` 的历史 Requirement/Scenario 正文（未合并
  归档，主 spec 仍是 change 前基线，按 openspec 流程属 `sdflow-done` archive 阶段的 delta 同步职责，
  非本 task 范围）；`docs/design-methodology.md`（未列入 6.7 已知面清单）；`openspec/issues/CLOSED.md`
  与已关闭历史 issue（`T27`/`T147`）；`openspec/roadmaps/archive/**`。
- **完整的归零词 sweep + 逐条判词登记豁免清单是 tasks 7.6 的职责**，不在本 ticket（本 ticket 边界=
  section 5、6，明确排除 section 7），以上仅为诚实记录、不代表已完成 7.6。

## 测试

```
/usr/bin/python3 -m pytest sdflow-ship/tests/ hack/tests/ -x --tb=short   → 729 passed
/usr/bin/python3 -m pytest sdflow-init/tests/ -q                          → 789 passed, 4 skipped
/usr/bin/python3 -m pytest -q（全仓）                                      → 2476 passed, 10 skipped
```

全仓首轮跑出 1 处遗漏：`sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py::
test_fold_hit_unknown_raw_error_mentions_update_hint` 断言旧文案 `"sdflow-init update" in
str(exc_info.value)`——因 6.6 把 `lens_metric_emit.py` 的报错文案改为统一口径「回运行 checkout 跑
`bash setup.sh`」而失效。已改写断言为 `assert "bash setup.sh" in str(exc_info.value)`，第二轮全仓
回归绿（2476 passed）。

`hack/gen_workflow_guide.py --check` 绿；`openspec validate fix-probe-scan-precision --strict --type
change` 绿。

## 范围边界（诚实报告）

- **未做**：tasks.md 第 7 节全链路验证（三判据闭环）——按 brief 明确排除，属独立验证 ticket。
- **未做**：`openspec/specs/{spec-workflow,maintain-scan}/spec.md` 主 spec 本体订正——这两份 delta
  spec 已在本 change 目录 `specs/` 下就位（task 2/3/4 各自的 MODIFIED Requirement），主 spec 合并是
  `sdflow-done` archive 阶段的 delta-sync 职责，提前手改主 spec 会打乱该流程的对码核验。
- **未做**：修复 `sdflow-init/scripts/init.py::_marker_schema()` 对 project-local schema marker
  （含 `created:` 等额外键）的 fail-closed 誤判——与本 change 目标无关的预先存在缺陷，见上文
  「sdflow-init update 执行说明」，未新增 todo（避免超出 6.11 已定的四条范围）。
- **未做**：`docs/design-methodology.md`、`openspec/specs/*.md` 历史 Scenario 正文、`openspec/issues/
  CLOSED.md` 与已关闭历史 issue、`openspec/roadmaps/archive/**` 中的归零词遗留命中——留给 7.6 sweep
  判定是否需登记豁免。

## 完成状态

第 5、6 节共 14 条验收标准全部完成。未勾选 tasks.md 复选框、未打 checkpoint 标签——按信号权威表，
该动作留给双轴审后的执行模式。
