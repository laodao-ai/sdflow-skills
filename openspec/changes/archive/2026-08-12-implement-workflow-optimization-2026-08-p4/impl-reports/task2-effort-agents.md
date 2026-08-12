# Task 2 impl-report：effort agent 定义铺设与 install_agents 验证

## 做了什么

1. **5 个 effort 档位 agent 定义**，新增于 `sdflow-spec/agents/`：
   `sdflow-effort-{low,medium,high,xhigh,max}.md`。frontmatter：
   `name: sdflow-effort-<值>` / `description: "effort 档位定义（仅由 sdflow 编排 SKILL 派发选用，勿手动使用）"`
   / `model: inherit` / `effort: <值>`；无 `tools` 字段（design 决策：「无 tools 限制，工具面由派发
   prompt 约束」）。正文各一行说明自身用途；`sdflow-effort-max` 额外注明「目前不进任何档位的缺省
   映射，仅作为值域内的显式逃生口保留」（design Q3）。

2. **目录内注记**：`sdflow-spec/agents/README`（**故意不带 `.md` 后缀**——`install_agents()` 与
   `hack/tests/` 的 `_expected_names()` 都用 `*.md` glob 判定"这是不是一个 agent 定义"，若叫
   `README.md` 会被当成第 9 个定义误铺进 `~/.claude/agents/`；无扩展名精确落在两处 glob 匹配面
   之外，不需要改任何铺设/测试逻辑）。内容说明目录混装两类定义（sdflow-spec 角色 + effort 档位）
   及各自铺设契约。

3. **CLAUDE.md** `install_agents()` 一节：把「三个定义」的表述改为「混装两类定义」，列出 8 个
   `.md` 定义的构成，并指明 `README`（无 `.md` 后缀）的存在与理由。未动 `sdflow:principles`
   托管块。

4. **`hack/tests/test_install_agents.py`** 新增 5 条 effort 专项断言（原有 9 条通用测试因
   `_expected_names()` 已是全目录 glob，本就会自动覆盖新文件，无需改动）：
   - `test_effort_definitions_have_correct_frontmatter_and_are_not_confused_with_role_defs`
     （静态，不跑 setup）——5 个定义各自 frontmatter 正确，且与 3 个角色定义共存不冲突。
   - `test_readme_note_is_not_swept_into_agent_installation` —— README（无 `.md` 后缀）
     不会被当成 agent 定义铺出去。
   - `test_effort_definitions_are_symlinked_and_rerun_stays_idempotent` —— 5 个定义各自铺出
     软链 + 重跑幂等。
   - `test_effort_definition_foreign_same_name_is_never_clobbered` —— 非本仓同名文件占用
     `sdflow-effort-low.md` ⇒ 不覆盖 + 进 `skipped[]`。
   - `test_effort_definition_removed_from_source_is_orphan_cleaned` —— 用替身仓
     （`_symlink_farm`）删除一个 effort 定义源文件后重跑 ⇒ 该链被孤儿清理撤下，其余 effort
     定义与角色定义原样保留。

   **红绿验证**：先把 5 个新文件 + README 移出 `sdflow-spec/agents/` 跑这 5 条新测试，全部按预期
   失败（`AssertionError`）；文件放回后全部转绿。confirms 非恒真锚。

5. **副作用修复（不在 brief 字面清单里，但由本任务直接引入，按四条通则③"完成=全部完成"必须
   一并处理）**：`hack/tests/test_sdflow_spec_agents.py` 有两条既有测试用
   `AGENT_DIR.glob("*.md")` 扫**全目录**（不写死三个名字），在新增 5 个 effort 定义后于本地
   实测**当场变红**：
   - `test_no_agent_def_uses_scoped_tool_syntax` 原假设"每个定义都有 `tools` 字段"——effort
     定义按 design 决策没有该字段。修法：字段缺失时跳过（非本门管辖），字段存在时仍强制无括号。
   - `test_every_definition_has_an_exclusive_description` 原假设"每个定义的排他式声明都是
     `仅由/sdflow-spec编排派发`"——effort 定义用的是不同措辞
     `仅由sdflow编排SKILL派发选用`（design 原文用词）。修法：按文件名前缀分两支断言，各自
     核对各自 family 的排他式措辞逐字在场。
   同时更新了该文件的模块级 docstring，说明现在同目录混装两类定义、哪些用例覆盖哪一类。

## 验证

- `pytest hack/tests/test_install_agents.py` —— 14 passed（9 条既有 + 5 条新增）。
- `pytest hack/tests/test_sdflow_spec_agents.py hack/tests/test_check_dependencies.py
  hack/tests/test_sync_principles.py` —— 全绿（74 passed，含被本任务波及后修复的 2 条）。
- `python3 hack/sync_principles.py --check` —— ✅ 28 个投放面一致（5 个新 agent 定义的
  `sdflow:principles` 托管块由既有 `AGENT_TARGETS` glob 自动纳入并注入，零改脚本）。
- 全仓 `pytest -q`：结果见下方"发现"一节（后台跑，结果到达后回填）。

## 关键发现

- **`install_agents()` 零改动生效**：既有实现已是「glob `sdflow-spec/agents/*.md` + manifest
  驱动的所有权/孤儿清理」，design Q2=C「复用既有源目录、零改守卫」在铺设脚本层面**天然成立**，
  无需碰 `setup.sh` 一行。
- **`.md` glob 是把双刃剑**：任何直接放进 `sdflow-spec/agents/` 的 `.md` 文件都会被
  `install_agents()` 当作"要铺出去的 agent 定义"，包括文档说明文件本身。用无扩展名文件名
  规避，是本仓已有 bash/Python 两处 `*.md` glob 判据下最简单、零改动量的解法。
- **`sync_principles.py` 的 `AGENT_TARGETS` 同样是全目录 glob**（`sdflow-spec/agents` +
  `SOURCE`），5 个新增 effort 定义在 Write 后被自动注入 `sdflow:principles` 托管块（本仓已有
  的 hook/机制行为），无需我手动处理；这也是为什么最终每个 `sdflow-effort-*.md` 文件比最初
  写入时多了托管块正文。
- **既有测试文件里"扫全目录"与"扫三个具名定义"两种模式并存**——前者（S1 tools 形态 / S5
  description 排他式）天然会照到新增的 effort 定义，后者（工具集合精确匹配 / canonical 诚实
  声明 / S2-S4 / 派发协议）硬编码 `LOCAL`/`WEB`/`WRITER` 三个路径，effort 定义不适用、也不该
  适用（它们不承载角色语义）。改动前须先分清楚一条断言属于哪一类，否则会把"角色专属"的断言
  错误地泛化到 effort 定义头上，或反过来把"全目录"断言收窄漏检新增文件类。

## 未做 / 越权说明

- 未勾选 `tasks.md` 复选框、未打 checkpoint 标签——按信号权威表由双轴审通过后的执行模式补打。
- design 组件清单里其余行（`effort-tier-defaults` 机读块 / `resolve-models.sh` 导出 /
  `render-review-prefix.sh` / ship_gate B25/B26 门 / 4 个编排 SKILL 派发条款）不在本票范围内，
  未触碰。
