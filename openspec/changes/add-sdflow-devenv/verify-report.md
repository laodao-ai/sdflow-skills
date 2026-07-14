---
ship-gate:
  verify: FAIL
---

# verify-report —— `add-sdflow-devenv`

**日期**：2026-07-14 · **change**：`add-sdflow-devenv` · **分支**：`feat/add-sdflow-devenv`

## 结论：**FAIL**

**skill 本体（`devenv-provisioning`）可用且实证过**——1248 tests 全绿（devenv+hack 计 123），17 条 Requirement 里 16 条有机验锚点，mqtt-console 真实试点跑过。

**FAIL 的原因不是「skill 不能用」，而是「本 change 的三份 spec 里有两份未落地，若就此 archive 会把未实现的 Requirement 同步进 `openspec/specs/` 成为永久假绿」**：

- `maintain-scan`（本 change **ADDED** 的整条 capability）—— **0/6 Scenario 实现**，`sdflow-maintain/` 全目录零 `devenv` 字样。
- `architecture-design`（**MODIFIED**）—— **2/4 Scenario 未实现**（description 过程轴分流句 + 交棒话术改写，两条都是本 change 新增的 delta，两条都没做）。
- `devenv-provisioning` 的 lint 第 5 条报项（SAD contract 差集）—— **生产路径不可达**，且 `references/review-lenses.md:70` 对模型**谎报「机械部分已经算好了」**。

三项修复成本都低（一句 description + 一段交棒话术 + maintain 里几十行接线 + lint 加一个 `--sad` 入口），**建议补完再 archive**，而不是 archive 一份说谎的 spec。

---

## 逐需求核对表

### spec `devenv-provisioning`（17 Req）

| 需求 | 代码出处 / 测试锚点 | 状态 |
|---|---|---|
| 核心承诺：三层框架，一层不许留白（全待定合法 + 骨架 fail-closed） | `devenv_schema.py:239-241`（缺层报错）· `test_schema.py::test_missing_layer_is_fail_closed` · `test_schema.py::test_pending_slots_are_legal` · `test_lint.py::test_exit_zero_even_when_everything_is_pending` | ✅ |
| 「层」= 保真度刻度；`layer` 是唯一封闭枚举，其余自由文本〔A24〕 | `devenv_schema.py:38`（`LAYERS`）· `test_schema.py::test_only_layer_is_a_closed_enum` · `test_schema.py::test_deps_kind_is_dead` · `test_schema.py::test_deps_accepts_any_dependency_shape` | ✅ |
| 六槽（⑤ 不问）· 不适用豁免其余槽 + MUST 带 consequence | `devenv_schema.py:41,88-93` · `test_schema.py::test_not_applicable_exempts_the_six_slots` · `test_scaffold.py::test_not_applicable_requires_consequence` · lint 分母排除：`test_lint.py::test_not_applicable_layer_is_out_of_the_denominator` | ✅ |
| 层状态 = 泳道投影，MUST NOT 手写〔A25〕 | `devenv_schema.py:117-141`（`layer_status`，且**全绿才 verified，有绿有非绿 → partial**）· `test_schema.py::test_handwritten_layer_status_is_rejected` · `test_schema.py::test_one_green_lane_does_not_make_the_layer_green` · `test_schema.py::test_scaffolded_layer_is_not_called_implemented` | ✅ |
| 验证方法：`script` 默认首选；「跑不了」两种分清 | `devenv_scaffold.py:392-396`（confirm-lane 拒 script executor，原样打出「把前者标成后者是在撒谎」）· `test_scaffold.py::test_confirm_lane_refuses_script_executor` | ✅ |
| 状态迁移：`set-lane --status verified` 一律 exit 5 | `devenv_scaffold.py:232-235` · `test_scaffold.py::test_set_lane_rejects_verified` | ✅ |
| 跑红不是失败（脚本退出码仍 0） | `devenv_scaffold.py:360-374` · `test_scaffold.py::test_verify_lane_red_becomes_scaffolded_not_failure` | ✅ |
| 超时如实记不确定性 | `devenv_scaffold.py:364` · `test_scaffold.py::test_verify_lane_timeout` | ✅ |
| 人工确认如实标 `attested_by: human` | `devenv_scaffold.py:398-409` · `test_scaffold.py::test_confirm_lane_marks_human_attested` · `test_lint.py::test_report_marks_human_attested` | ✅ |
| `verified` = `verified-at <sha>`，渲染带 commit 锚 + 日期 | `devenv_scaffold.py:483-494` · `test_lint.py::test_report_shows_verified_with_commit_anchor` | ✅ |
| 落地物：MUST NOT 解析 Makefile/shell〔A21〕 | `test_scaffold.py::test_scaffold_does_not_parse_build_files`（AST 扫 import，无 `re`）· `test_schema.py::test_no_resurrected_mechanisms`（无 digest/sha256/recipe/makefile/hashlib/fcntl） | ✅ |
| 命令不存在由工具自己判 | `test_scaffold.py::test_verify_lane_nonexistent_command_lets_the_tool_judge` | ✅ |
| target 重名由 make 自己揭发（读它已打出的 warning） | `devenv_scaffold.py:340-342` · `test_scaffold.py::test_verify_lane_surfaces_make_overriding_warning` | ✅ |
| skill 无删除能力〔adr/0022〕 | `test_scaffold.py::test_scaffold_has_no_delete_capability`（AST 扫调用，无 `unlink`/`rmtree`/`remove`/`rmdir`） | ✅ |
| 路径 containment（含 symlink 祖先 · 空字节） | `devenv_paths.py` · `test_paths.py::test_rejects_symlink_ancestor` · `::test_rejects_embedded_null_byte_as_path_escape` · `::test_rejects_dotdot` · scaffold 侧 `test_scaffold.py::test_set_lane_rejects_path_escape`（exit 2） | ✅ |
| 数据模型：一份 JSON，零 digest / 零锁 / 零封闭枚举（除 layer） | `test_schema.py::test_no_resurrected_mechanisms`（AST 符号+导入扫描） · `test_schema.py::test_owned_by_stays_dead` | ✅ |
| 两文档切线（`environments.md` 归人 own，test 节仅指针） | `devenv_scaffold.py:98-156`（ENV_SKELETON 十槽）· `test_scaffold.py::test_environments_test_section_is_a_pointer_only` · `::test_init_never_overwrites_existing_environments` · `::test_render_never_touches_environments` | ✅ |
| **lint——只报不拦**（退出码 0；唯一 fail-closed = 坏 JSON） | `devenv_lint.py:217`（永远 0）· `test_lint.py::test_exit_zero_even_when_everything_is_pending` · `::test_bad_json_is_fail_closed`（exit 2）· `::test_report_never_raises_on_weird_data` | ✅ |
| ├ 报项 1 代价横幅 | `devenv_lint.py:69-83` · `test_lint.py::test_banner_counts_pending` | ✅ |
| ├ 报项 2 `environments.md` 待定计数（固定字符串，非解析结构） | `devenv_lint.py:119-133` · `test_lint.py::test_env_pending_counts_only_a_fixed_string` · `::test_skeleton_spells_pending_only_in_slots` | ✅ |
| ├ 报项 3 未 verified 泳道逐条 | `devenv_lint.py:156-178` | ✅ |
| ├ 报项 4 敷衍 blocked_by | `devenv_lint.py:99-107` · `test_lint.py::test_exit_zero_with_lazy_blockers` | ✅ |
| └ **报项 5 SAD contract 差集** | 函数在（`devenv_lint.py:86-96`，单测 `test_lint.py::test_uncovered_contracts_listed_but_not_blocking`），但 **`main()` 从不传 `sad_contracts`、CLI 无 `--sad` 入口** ⇒ 生产路径恒空集 | **❌ 核心缺失（G3）** |
| 五步流程 + 收尾报告逐条列出 | `SKILL.md:160-353`（五步 + ⑤ 步收尾报告样例） | ✅ |
| 冷审：vacuous 镜 + 盲区镜永远取，fresh 子代理 | `SKILL.md:304-311` · `references/review-lenses.md`(129 行) | ✅ |
| 入口托管注入用独立 marker `opsx-devenv`，幂等整块替换 | `devenv_scaffold.py:36-37,513-537` · `test_scaffold.py::test_inject_is_idempotent` · `::test_inject_replaces_block_in_place` | ✅ |
| 触发分工与前置（无 openspec → exit 3；无 SAD → 响亮降级不阻塞） | `devenv_scaffold.py:164-174` · `test_scaffold.py::test_init_without_openspec_is_fail_closed` · `::test_init_warns_loudly_on_missing_sad_but_does_not_block` | ✅ |

### spec `maintain-scan`（ADDED，1 Req / 6 Scenario）

| 需求 | 代码出处 | 状态 |
|---|---|---|
| `sdflow-maintain` 检出 `.devenv.json` → 调 `devenv_lint`，结果原样并入报告 | **无**（`grep -rn devenv sdflow-maintain/` 零命中） | **❌ 核心缺失（G1）** |
| 报告含代价横幅 / env 待定槽 / 未 verified 泳道逐条 / 敷衍 blocked_by / SAD 差集 | 同上，全部未接 | ❌ |
| 两条诚实边界（它是提醒不是门禁 · `verified` 带 commit 锚不渲染成无条件绿） | 同上 | ❌ |
| 降级（无 `.devenv.json` 跳过 · lint 不可用显式提示不静默） | 同上 | ❌ |

### spec `architecture-design`（MODIFIED，1 Req / 4 Scenario）

| 需求 | 代码出处 | 状态 |
|---|---|---|
| description 含时间轴分流句（存量） | `sdflow-architecture/SKILL.md:8` | ✅（本 change 前已有） |
| **description 含过程轴分流句「建 dev/test 环境 / 定测试策略 → /sdflow-devenv」** | **无**（`sdflow-architecture/SKILL.md` frontmatter 零 `devenv`） | **❌ 核心缺失（G2）** |
| **交棒话术从「给模板路径」改为指向 `/sdflow-devenv`** | **未改**——`sdflow-architecture/SKILL.md:417-426` §5.3 仍是「指出不代写 + 给模板路径 + SAD 锚」，无一处提 `/sdflow-devenv` | **❌ 核心缺失（G2）** |
| 交棒仍不代写过程轴文档（边界保留） | `sdflow-architecture/SKILL.md:419-420` | ✅（未回归） |

### tasks.md 非 spec 项（fold 进本 change 的相邻工作）

| 任务 | 出处 | 状态 |
|---|---|---|
| 三条通则托管注入 17 个 skill + 单一真相源 + 机械守 | `sdflow-init/assets/hack/skill-principles.md`（真相源）· `hack/sync_principles.py` · 17 份 `*/SKILL.md` 均含 `sdflow:principles:start` 块（已核数 = 17）· `hack/tests/test_sync_principles.py`（6 tests，含 `test_source_is_the_only_place_it_is_authored`、`test_outside_voice_frame_carries_the_principles`） | ✅ |
| workflow 三分（prompts 单一源 + WORKFLOW-GUIDE 生成物） | `sdflow-init/assets/workflow/prompts/`（9 个 step*.md）· `WORKFLOW-GUIDE.md` · `hack/gen_workflow_guide.py` · `hack/tests/test_workflow_split.py`（5 tests，含 `test_guide_is_in_sync_with_its_sources`、`test_history_is_out_of_the_body`） | ✅ |
| 仓级集成：setup.sh / README / CLAUDE.md | `~/.claude/skills/sdflow-devenv` 与 `~/.codex/skills/sdflow-devenv` 均为指向本仓的 symlink（已核）· `README.md:24,32` · `CLAUDE.md:85` · commit `db7b6dc` | ✅ |
| 首个真实试点（mqtt-console）+ 验 A-8 / 核心承诺 / ⑥ 槽 | commit `fb165c3`（「首个真实试点（mqtt-console）实证 + 两条问话纪律 + 修试点暴露的两个假绿」）· 试点结论落 `docs/sad/07` 附录 C · 试点直接产出两条机械修复（`layer_status` partial 态 A29 · `env_pending` 图例假阳） | ✅ |
| 107 tests green | 实测 **1248 passed**（全仓）· devenv+hack 子集 **123 passed** | ✅（超额） |

---

## 缺口清单

### 核心缺口（FAIL 项，建议 archive 前补齐）

**G1 · `maintain-scan` 整条 capability 零实现**
`sdflow-maintain/` 全目录无任何 `devenv` 字样，`.devenv.json` 无人检出、`devenv_lint` 无任何自动触发点。
**为什么它不是 Minor**：这条 spec 的立论就写在自己正文里——「devenv 的渐进 DoD 允许泳道停在 `scaffolded`、槽停在 `⚠️ 待定`，而**防止它烂成僵尸文档的唯一措施就是把代价摆到人眼前**；**若无人调用该 lint，该措施为空**。『不强制完成』+『不检查未完成』= 名存实亡，两者只能选一个。」
本 change 选了「不强制完成」（`adr/0021`），却没配上那一半。**且立项理由之一正是「无门禁——某些检查全靠人记得跑」，现在 `devenv_lint` 自己就是这样一个检查。**
> 用户已明示此项未做。我的独立判断：**不接受降级为 Minor**——它是 ADDED spec 的全部内容，archive 会把 6 个 Scenario 原样同步进 `openspec/specs/maintain-scan/`，形成「规格说有、代码没有」的永久假绿。修复成本低（maintain 扫描里加一个存在性检查 + subprocess 调 lint + 原样贴报告）。

**G2 · `architecture-design` 的两条 delta 均未落地**
- description 无过程轴分流句 ⇒ 三轴路由在 description 层**不完整**（空间轴 ✅ / 时间轴 ✅ / 过程轴 ❌）。用户说「这个项目怎么测」时，architecture 的 description 不会把他分流出去。
- §5.3 交棒话术仍停在「给模板路径」——而该段的存在理由就是「过程轴此前无下游」；`sdflow-devenv` 落地后**该前提已失效**，继续只给模板路径 = 把操作者留在手搓状态（spec 原话）。
> 用户只提了 description 一条；实测**交棒话术那条也没做**（`SKILL.md:417-426` 零 `devenv`）。两条都在本 change 的 MODIFIED delta 里。修复成本 = 改两段文字。

**G3 · lint 的 SAD contract 差集在生产路径不可达，且 references 对模型谎报**
`uncovered_contracts()` 写了、单测覆盖了，但 `devenv_lint.main()` 调用 `report(data, root=...)` **不传 `sad_contracts`**，CLI 也没有 `--sad` 入口 ⇒ 无论 SAD 有多少条未覆盖的 contract，lint 输出恒为空。
更糟的是 `sdflow-devenv/references/review-lenses.md:70` 明写：「**机械部分已经算好了**（脚本对账 SAD §5 contract 集合 vs 泳道 `covers` 并集，差集交给 skill 去问人）」——**脚本从未读过 `sad.md`**。冷审子代理读到这句会以为差集已算，从而**不去问人**。这是一条会主动误导模型的假陈述。
> 它同时是 `devenv-provisioning`（lint 报项 5）和 `maintain-scan`（报告项 5）两份 spec 的 SHALL。

### Minor 缺口（可接受 / deferred）

- **试点结论未回灌 `references/`**（tasks 7 最后一项）——mqtt-console 的结论已落 `docs/sad/07` 附录 C，且**已回灌的部分恰恰是最关键的两条**（`layer_status` partial 投影 A29 · `env_pending` 图例假阳修复，见 commit `fb165c3`）。剩下的是「补形态格 / 记证伪方法」这类增量素材，属**内容丰富度**而非功能。**判 Minor，可 deferred。**
- **`/sdflow-code-review` 未跑**（用户明示跳过）——verify 作为唯一终门已逐条对码核验；本 change 无外部 PR 血液。**判可接受**，但注意此前实证「冷 code-review 层曾独家挖出致命假绿」，跳过是有代价的知情选择。
- `tasks.md` 写「107 tests green」，实测 123（devenv+hack）/ 1248（全仓）——**计数 stale，非缺陷**。

---

## 附：本次 verify 的机验基线

```
/usr/bin/python3 -m pytest -q          →  1248 passed in 48.05s
/usr/bin/python3 -m pytest sdflow-devenv/tests hack/tests -q  →  123 passed
```
