# Task 2 impl-report：翻转 impl-pipeline 缺省为 tickets 并更新相关配置文档

## 范围核验（worktree 起手偏离，已自行修复）

本 worktree 起手时未挂在 `feat/simplify-workflow` 分支上（挂在其 merge-base 的更早祖先），
`openspec/changes/simplify-workflow/` 整个目录（含 tickets.md/tasks.md/design.md 等）在本
worktree 里不存在。核验 `git merge-base --is-ancestor HEAD feat/simplify-workflow` 为真后，
用 `git merge --ff-only feat/simplify-workflow` 快进合并补齐（工作树干净、无本地改动，纯快进、
零冲突），随后才能读到 `task2-brief.md` 与本 change 全部四件套。

## 改动清单

1. **`sdflow-implement/scripts/impl_route.py`**
   - `read_config_pipeline`：6 处 `return "superpowers", ...` 改为 `return "tickets", ...`
     （缺失文件 / 缺键 / 空值 / yq 解析异常 / 非字符串结构 / 非法值兜底，共 6 个 return 点），
     docstring 同步更新。
   - `read_plan_marker`：**未改**——2 处 `return "superpowers"`（无 frontmatter / frontmatter
     无键）按 brief 要求冻结不变，避免静默切换在途 change；在其 docstring 补一段说明冻结理由。
   - 模块头部三跳路由说明（③ 那行）同步改写，区分「config 缺省已翻转」与「marker 缺省冻结」。
   - `_cmd_route` 展示折叠逻辑（`config_display`/`marker_display`）：**函数行为未改**（无测试
     要求变更，marker 侧的折叠触发条件本就锚在 marker 自己的缺省值——marker 缺省冻结不翻转，
     折叠触发条件因此也不随之改变；config 侧本就不折叠，凭 `config_note` 元组已区分三态，
     无需新增折叠）。按 tickets.md checkbox 要求补了一段显式注释，说明两侧折叠锚点为何在
     翻转后刻意不对称（config 锚新缺省 tickets、marker 锚旧缺省 superpowers），供后续读者
     不再误判为遗漏。**决策记录**：design.md/spec-review-report 里「`_cmd_route` 展示折叠逻辑
     需对称翻转」一句缺乏更细粒度的行为规格，现有测试矩阵（`test_cli_route_marker_explicit_
     superpowers_displays_none` 等）明确将 marker 侧折叠行为标注为「现行折叠行为...锁定现状
     （display 改进已 defer）」——即该模糊性在更早阶段已被识别并显式 defer，本任务未在此
     基础上新造行为，只补齐说明性注释。

2. **`sdflow-implement/tests/test_impl_route.py`**（TDD：先红后绿）
   - `read_config_pipeline` 相关 8 个用例：期望值从 `"superpowers"` 改为 `"tickets"`（缺失文件/
     缺键/空值/typo/commented-line/indented-mention/引号损坏×2）。
   - CLI 用例 2 个：`test_cli_route_absent_absent_defaults_superpowers` 更名为
     `test_cli_route_absent_absent_defaults_tickets`，`pipeline=` 断言改 `tickets`；
     `test_cli_route_unknown_config_value_echoed` 的 `pipeline=` 断言改 `tickets`。
   - `read_plan_marker` 相关用例、marker 锁定优先于 config 的用例（含
     `test_cli_route_marker_implicit_superpowers_locks_over_config`、
     `test_cli_route_marker_explicit_superpowers_displays_none`）**全部未改**——marker 行为冻结，
     断言本就仍然成立（未修改即验证了冻结正确）。
   - 先跑一遍确认 10 个用例转红（与预期改动点一一对应），再实现 `impl_route.py` 的翻转，
     复跑转绿。

3. **`openspec/config.yaml`（本仓）**
   - `impl-pipeline` 注释块（原 62-64 行）：「缺省请勿填（缺失/非法值一律 superpowers 旧管线）」
     → 改为「缺省一律 tickets（缺失/非法值同归此路径）」，补一句「显式 `impl-pipeline:
     superpowers` 仍生效，走旧管线」。
   - 删除两处 wayfinder 规则引用（`rules.proposal`/`rules.design` 下各一条 `change 源于
     wayfinder map 时：...` bullet，对应 spec-review-report M6 finding 定位的 L38/L48）。

4. **两份 `config.template.yaml`**（`sdflow-init/assets/workflow/` + `openspec/workflow/`）
   - 注释同步改为「缺省一律 tickets；缺失/非法值同归此路径」+ 显式 superpowers 仍生效说明。
   - 未删这两份模版里的 wayfinder bullet——tasks.md/spec-review-report M6 finding 明确只点名
     `openspec/config.yaml:38/48`（本仓 config），模版文件的 wayfinder 引用清理属于另一票
     （`ff-generation-constraints.md` §wayfinder→ff 衔接契约删除 + companion 文档清理任务），
     不在本票范围内，未越界处理。

5. **`sdflow-init/assets/workflow/workflow.md`**
   - 3 处 `impl-pipeline` 相关描述：把「缺省不变（=writing-plans→subagent-dev / 无说明）」
     改为准确描述当前状态——流程图分支处改为「实现管线缺省 = tickets；显式设
     `impl-pipeline: superpowers` 才走 writing-plans→subagent-dev」；两处步骤表描述改
     「缺省即 tickets」。未触碰流程图/步骤表的整体结构（那是另一张更大票——tasks.md 第
     54 项「流程图改为线性单轨；步骤表精简...删全部 wayfinder/embedded-test-sop/分支 B
     引用」——的范围，本票只纠正 impl-pipeline 缺省值的文字描述）。
   - 连带重跑 `python3 hack/gen_workflow_guide.py --write` 重生成
     `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md`（单一源同步机械门，`hack/tests/
     test_workflow_split.py::test_guide_is_in_sync_with_its_sources` 要求 GUIDE 与
     workflow.md+prompts/ 保持一致，改 workflow.md 不重生成会转红——已用 baseline worktree
     核验此为本票改动引入，非既有失败）。
   - **未触碰** `openspec/workflow/workflow.md`（本仓「本地 pin」副本，同样残留旧文案）——
     tickets.md 明确把「处理 openspec/workflow/ 本地 pin：删除规则文件恢复全局解析或同步刷新」
     列为另一票（README/AGENTS.md 那一组任务），本票越界处理会侵犯该票范围；
     `hack/tests/test_workflow_split.py` 也只校验 `sdflow-init/assets/workflow/` 权威源一侧，
     未覆盖本地 pin，机械层不会因此转红。

## 未改动项 + 原因（premise-verification）

**`sdflow-ship/SKILL.md` 未改动。** 逐字核验：全文 `grep -n "impl-pipeline"` **零命中**——
该文件描述 RUN_PLAN/CONTINUE_IMPL 分支时完全以 `impl_route.py route` 的运行时回执
（`pipeline=tickets` / `pipeline=superpowers`）为准分支处理，两个分支的处理描述本就
对称、不预设任何一侧为"缺省"，故文件里原本就不存在需要翻转的"缺省描述"文本。design.md
（L57/L85）与 tickets.md 把这条与 impl_route.py 的翻转点并列提及，但这是设计阶段的
预判性描述，未必对应文件里存在具体可改的文字——核验后确认此处无内容需要改动，如实报告，
未强行编造改动凑数。

## 测试结果

- `pytest sdflow-implement/tests/`：**79 passed**（改动前 10 个用例先跑一遍确认转红，逐一对应
  `read_config_pipeline`/CLI route 期望值改动点；实现翻转后复跑转绿）。
- 全仓 `pytest -q`：**2489 passed, 10 skipped, 3 failed**（首次跑）。逐一核验 3 个失败：
  1. `hack/tests/test_workflow_split.py::test_guide_is_in_sync_with_its_sources` ——
     **本票引入**（改了 `workflow.md` 未同步重生成 GUIDE）。已修：跑
     `python3 hack/gen_workflow_guide.py --write`，复跑转绿。
  2. `sdflow-init/tests/test_setup_sdflow.py::TestBrandAndMarkerNarrowing::
     test_legacy_marker_recognized_only_for_our_names` —— **既有失败，非本票引入**。用
     `git worktree add <tmp> 30f10e6 --detach`（本票改动前的 merge 基线）核验：该用例在
     30f10e6 上同样红（`embedded-test-sop` 孤儿目录未被清理），与本票 impl_route.py/config
     改动无关，源头是更早一次 ff-merge 已删除 `embedded-test-sop/SKILL.md` 但清理逻辑未跟上，
     属于另一票（embedded-test-sop 移除相关）范围。
  3. `hack/tests/test_subprocess_encoding_contract.py::
     test_text_mode_subprocesses_declare_utf8_and_replace` —— **既有失败，非本票引入**，同一
     baseline worktree 核验为 30f10e6 上已红（全仓 subprocess 调用点计数 187 < 200 门槛，
     与本票无关，同样是前序 SKILL 目录删除的连带效应）。
  修复 #1 后复跑 `pytest hack/tests/test_workflow_split.py sdflow-implement/tests/`：
  **84 passed**。最终一次全仓 `pytest -q` 复核：仅剩 #2/#3 两个既有失败（详见下方 Global
  Constraints 核验行）。

## Global Constraints 核验

- impl_route.py 改动后 `pytest sdflow-implement/tests/` 全绿 ✅（79 passed）
- 未触碰 `sdflow-ship/scripts/ship_gate.py`（gate 零改动铁律，本票未涉及）
- workflow bundle 权威源改动（`sdflow-init/assets/workflow/`）已同步（含 WORKFLOW-GUIDE.md 重生成）；
  本仓 `openspec/config.yaml` 改动仅影响本仓，未误推到模版。
- 全仓 `pytest -q` 最终态：本票改动引入的失败已全部修复归零；残留 2 个失败均已用 30f10e6
  baseline worktree 核验为既有失败（与本票无关，不阻塞本票交付）。
