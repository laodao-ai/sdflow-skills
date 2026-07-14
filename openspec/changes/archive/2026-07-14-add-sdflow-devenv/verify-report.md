---
ship-gate:
  verify: PASS
---

# verify-report —— `add-sdflow-devenv`

**日期**：2026-07-14 · **change**：`add-sdflow-devenv` · **分支**：`feat/add-sdflow-devenv`

## 结论：**PASS**

上一轮判 FAIL 的三条（G1 / G2 / G3）**逐条独立复核，全部真实落地**——不是「有人说修了」，而是我亲自跑了消费仓 CLI、亲自核了 `main()` 的可达性、亲自读了每条 Scenario 的对应测试。

**亲跑证据**

| 命令 | 结果 |
|---|---|
| `/usr/bin/python3 -m pytest -q` | **1260 passed**（上一轮 1248 → +12） |
| `maintain_scan.py --root .../mqtt-console` | exit 0，报告含 **`## devenv 健康度（提醒，非门禁 —— adr/0021）`** 一节，lint 全文原样并入（commit 锚 `1634967` 与日期在，无「✓ 已通过」式绿灯），且 devenv 的待定**未**把 maintain 判成有差异 |
| `devenv_lint.py --root .../mqtt-console` | exit 0，**SAD contract 差集 18 条真的印出来了**（Engine 接口 / SSH 隧道 DialFunc / …） |

---

## 上一轮三条 FAIL 的独立复核

### G1 · `maintain-scan`（6 Scenario）—— ✅ 真实现

`scan_devenv()` 在 `maintain_scan.py:263`，由 `run_scan()` **真调用**（`maintain_scan.py:300`），非孤儿函数。

| Scenario | 锚点 | 状态 |
|---|---|---|
| 逐条报出未 verified 泳道 | `test_maintain_scan.py:537 test_scenario_unverified_lanes_listed_one_by_one`（断言 `mqtt-real` + `本机无 mosquitto`、`pkg-smoke` + `打包冒烟脚本未建`——逐条带 `blocked_by`，非计数） | ✅ |
| 代价横幅原样透传 | `test_maintain_scan.py:514`（断言 `⚠️ 本框架 12/15 格待定，尚不构成一份可用的测试策略`） | ✅ |
| 它是提醒不是门禁 | `test_maintain_scan.py:524`（15/15 全待定 **且** 报告仍含「一致，无差异」）+ 代码：`build_report()` 的 `any_diff` 计算（`maintain_scan.py:307-311`）**不含 devenv** | ✅ |
| verified 不得渲染成无条件的绿 | `test_maintain_scan.py:558`（断言 `abc123f` + `2026-07-14` 在，`✓ 已通过` 不在）；代码 `maintain_scan.py:355` `lines += ["", text]` = **一个字都不改**地并入 | ✅ |
| 无 `.devenv.json` 时跳过 | `test_maintain_scan.py:507`（`scan_devenv → ("absent","")`，报告无「devenv 健康度」节） | ✅ |
| `devenv_lint` 不可用时显式提示 | 代码 `maintain_scan.py:286` `return "unavailable"` → `maintain_scan.py:349` 打印「检出 `.devenv.json` 但 `devenv_lint` 不可用…跳过健康度扫描」 | ⚠️ 见 Minor-2（分支有、无专测） |
| 坏 JSON 报出不吞 | `test_maintain_scan.py:581`（状态 `bad` + 报告含「数据坏了」） | ✅（超出 spec 的加测） |

**单一源核实**：maintain **不重实现** lint，而是 `import devenv_lint` 调其 `render(root)`（`maintain_scan.py:284-288` ↔ `devenv_lint.py:238`）⇒ 重渲染丢锚的路被结构性堵死。

### G2 · `architecture-design`（2 条 delta）—— ✅ 真实现

| Scenario | 锚点 | 状态 |
|---|---|---|
| description 含过程轴分流句 | `sdflow-architecture/SKILL.md:8`：「**过程轴（搭开发/测试环境 · 定测试策略 · 配 CI）→ 用 /sdflow-devenv**」，与时间轴分流句（`:9`→roadmap）并列 | ✅ |
| 两侧 description 均含分工指路 | 上句 + `sdflow-roadmap/SKILL.md:10`「新项目起步尚无架构设计（SAD）时，先 /sdflow-architecture（消费仓需已 sdflow-init）」 | ✅ |
| 交棒指向下游 skill 而非模板路径 | `sdflow-architecture/SKILL.md:425-436`：「⭐ 跑 `/sdflow-devenv`（它 owns 这一层，不要手写）」+ 五个 SAD 锚（§2 约束 / §3 外边界 / §5 contract 对账 / §7 部署 / §8 配置） | ✅ |
| 交棒仍不代写过程轴文档 | `SKILL.md:420-422`「本 skill MUST NOT 代写、MUST NOT 写进 SAD…architecture 是上游**指路者**：给锚、不成文」 | ✅ |

### G3 · `devenv_lint` 的 SAD contract 差集 —— ✅ 可达性真修好（重点复核）

上一轮的病是「函数有、单测有、全绿，但 `main()` 不传 ⇒ 生产路径恒空」。本轮：

- **生产链路**：`main()`（`devenv_lint.py:266`）→ `render(root)`（`:238`）→ `report(data, sad=sad_contracts(root), root=root)`（`:258`）——`sad` **真的传进去了**。
- **CLI 回归测试**：`test_lint.py:280 test_uncovered_contracts_reach_the_CLI_report` —— **走 `L.main(["--root", …])` 断言 stdout**，不走函数（注释明写「单测证明不了可达性」）。
- **真消费仓亲跑**：mqtt-console 上 18 条未覆盖 contract 全部印出。**不是假绿。**
- **无 SAD 时响亮降级**：`test_lint.py:301`（stdout 含「泳道覆盖对账失效」「可能漏掉边界」）；`sad_contracts()` 用 `None`（算不了）≠ `[]`（算过了没有）区分（`devenv_lint.py:120-148` + `test_lint.py:272`）。
- **单一源**：contract 行格式 owner 是 `sdflow-architecture`，lint **import 其 `scan_contract_names`**（`devenv_lint.py:144`），不另抄正则。

---

## 逐需求核对表

### spec `devenv-provisioning`（17 Requirement · 29 Scenario）

| 需求 | 代码出处（文件:行 / 测试名） | 状态 |
|---|---|---|
| 核心承诺：三层框架一层不留白；全待定合法且可见 | `test_lint.py:51 test_exit_zero_even_when_everything_is_pending`（exit 0）· `test_schema.py:188 test_pending_slots_are_legal` · `banner()` `devenv_lint.py:69` | ✅ |
| 三层骨架缺失 fail-closed | `test_schema.py:181 test_missing_layer_is_fail_closed`（参数化三层） | ✅ |
| 层=保真度刻度；`layer` 是唯一封闭枚举 | `test_schema.py:425 test_only_layer_is_a_closed_enum` | ✅ |
| 未列举依赖形态照样合法 / `deps[].kind` 已废 | `test_schema.py:162 test_deps_accepts_any_dependency_shape` · `test_schema.py:156 test_deps_kind_is_dead` | ✅ |
| 六槽；`not-applicable` 豁免其余槽 | `test_schema.py:223 test_not_applicable_exempts_the_six_slots` · lint 分母排除（`test_lint.py:123`） | ✅ |
| `not-applicable` MUST 带 `consequence` | `test_schema.py:212` · `test_scaffold.py:65 test_not_applicable_requires_consequence` | ✅ |
| 层状态是投影，MUST NOT 手写 | `devenv_schema.py:117 layer_status()` · `test_schema.py:236 test_handwritten_layer_status_is_rejected` · `test_scaffold.py:80 test_set_layer_never_writes_layer_status` | ✅（**实现比 spec 更严，见缺口 C-1**） |
| 从未跑绿的层不得称「已实现」 | `test_schema.py:293` · `test_scaffold.py:255 test_render_scaffolded_layer_is_not_called_implemented` | ✅ |
| 验证方法：`script` 默认首选；条件不具备 ≠ 不可脚本化 | `test_scaffold.py:228 test_confirm_lane_refuses_script_executor`（拒 + 「是在撒谎」）· `test_scaffold.py:204 test_verify_lane_refuses_human_executor` | ✅ |
| `set-lane --status verified` 一律拒绝（exit 5） | `test_scaffold.py:99 test_set_lane_rejects_verified` | ✅ |
| `verify-lane` 亲自 fork 拿真 exit code；跑红 → `scaffolded`，脚本仍 exit 0 | `test_scaffold.py:125 test_verify_lane_green` · `:143 test_verify_lane_red_becomes_scaffolded_not_failure` · `:159 test_verify_lane_nonexistent_command_lets_the_tool_judge` | ✅ |
| 超时如实记不确定性 | `test_scaffold.py:173 test_verify_lane_timeout`（断言 `blocked_by` 含「未确认是环境问题还是 smoke 本身挂了」） | ✅ |
| `confirm-lane` 如实标 `attested_by: human` | `test_scaffold.py:214 test_confirm_lane_marks_human_attested` | ✅ |
| target 重名由 make 自己揭发（捕 `overriding recipe`） | `test_scaffold.py:184 test_verify_lane_surfaces_make_overriding_warning`（真造双 target Makefile，断言 stderr 含「target 重名」「后定义的赢」） | ✅ |
| MUST NOT 解析 Makefile/shell〔A21〕 | `test_scaffold.py:325 test_scaffold_does_not_parse_build_files`（AST：不 `import re`）· `test_schema.py:366 test_no_resurrected_mechanisms` | ✅ |
| 执行边界与「不伤害」（跑前过目 / ③-pre 给 diff / 超时 / 不重试不 debug / 不装依赖 / 真硬件不跑） | `sdflow-devenv/SKILL.md:257-303`（六条逐条成文）+ `SKILL.md:90-99` 五条红线 | ✅ |
| skill 无删除能力〔adr/0022〕 | `test_scaffold.py:300 test_scaffold_has_no_delete_capability`（AST 扫 `unlink`/`rmtree`/`remove`/`rmdir`）· 归位模式加失效标记 `SKILL.md:195-207` | ✅ |
| 路径 containment（含 symlink 祖先 / 空字节） | `devenv_paths.py` · `test_paths.py`（13 例：`:41 rejects_symlink_ancestor` · `:87 rejects_embedded_null_byte`）· `test_scaffold.py:115 test_set_lane_rejects_path_escape`（exit 2） | ✅ |
| 数据模型：一份 JSON，零 digest / 零锁 / 零 make 知识 | `test_schema.py:366 test_no_resurrected_mechanisms`（AST 扫标识符与导入：无 `digest`/`sha256`/`recipe`/`makefile`/`atomic_write`；不 `import re`/`hashlib`/`fcntl`） | ✅ |
| 两文档切线：`render` 只管 `testing-strategy.md` | `test_scaffold.py:368 test_render_never_touches_environments` · `:360 test_init_never_overwrites_existing_environments` | ✅ |
| `environments.md` 十槽骨架；test 节只是一行指针 | `test_scaffold.py:341 test_init_seeds_environments_skeleton`（`count(PENDING)==10`）· `:351 test_environments_test_section_is_a_pointer_only` | ✅ |
| lint 只报不拦（永远 exit 0），唯一 fail-closed = 坏 JSON | `devenv_lint.py:272` `return 0` · `test_lint.py:51/64/70`（有 findings 仍 0）· `:83 test_bad_json_is_fail_closed`（exit 2） | ✅ |
| lint 五项报告（横幅 / env 待定 + 最贵三槽 / 未 verified 逐条 / 敷衍 blocked_by / SAD 差集） | `devenv_lint.py:168-235 report()`；真消费仓输出五项齐全（见亲跑证据） | ✅（**Minor-1**：`unverified_lanes()` 死代码） |
| `environments.md` 待定用固定字符串计数，MUST NOT 解析 MD | `devenv_lint.py:151 env_pending()`（`.count(S.PENDING)`）· `test_lint.py:216 test_env_pending_counts_only_a_fixed_string` · `:195 test_skeleton_spells_pending_only_in_slots` | ✅ |
| 报告永不因坏数据崩溃 | `test_lint.py:170 test_report_never_raises_on_weird_data`（缺 `id` 仍打印） | ✅ |
| 五步流程（核心承诺在 ② 步产出）+ 时序纪律 + 收尾报告逐条列出 | `sdflow-devenv/SKILL.md:160-356`（① 事实采集 → ② 三层框架逐层问 → ③ 落地+真跑 → ④ 冷审+人门 → ⑤ 渲染；`:336` 收尾报告 MUST 逐条列出） | ✅ |
| 冷审：fresh 子代理 + vacuous 镜 + 盲区镜是心脏 | `SKILL.md:304-311`（「🔴 MUST 由 fresh 子代理执行」「①vacuous 镜 与 ②盲区镜 是心脏，永远取」）· `references/review-lenses.md` | ✅ |
| 负面知识记入 `verification-patterns.md`（三条机械方案证伪） | `references/verification-patterns.md`（计数门槛 §1 · negative control · 轮询观测 §3「❌ 5/5 全漏」+ 证伪表） | ✅ |
| 入口托管注入用独立 marker `opsx-devenv` | `devenv_scaffold.py:36-37` · `test_scaffold.py:279 test_inject_is_idempotent` · `:291 test_inject_replaces_block_in_place` | ✅ |
| 触发分工 + 前置：无 `openspec/` → exit 3；无 SAD → 响亮降级不阻塞 | `test_scaffold.py:28 test_init_without_openspec_is_fail_closed` · `:40 test_init_warns_loudly_on_missing_sad_but_does_not_block` | ✅ |

### spec `maintain-scan` · `architecture-design`

见上文 G1 / G2 表——**6 + 4 个 Scenario 全部有锚点**。

### tasks.md 其余项

| 任务 | 锚点 | 状态 |
|---|---|---|
| A 层六份 `references/` + `SKILL.md` | 六文件实存（`testing-framework.md` 17KB / `environments-template.md` 13KB / `lane-patterns` / `verification-patterns` / `review-lenses` / `boundary-rules`）+ `SKILL.md` 22KB | ✅ |
| 仓级集成（setup / README / CLAUDE） | `~/.claude/skills/sdflow-devenv` 与 `~/.codex/skills/sdflow-devenv` 均为指向本仓的 symlink · `README.md:24,32` · `CLAUDE.md:85` | ✅ |
| 首个真实试点（mqtt-console）+ 验 A-8 / 核心承诺 / ⑥ 槽 | `docs/sad/07 附录 C`（13 泳道 / 10 条真跑绿 / 真落代码 `hack/doctor.sh`、`e2e-live.sh`、`schema_golden_test.go`）；试点反过来抓出 **A29 假绿**（一绿即绿）与 **A30**（甩开放题）并已修进代码与 SKILL | ✅ |
| 试点结论回灌 `references/` | tasks.md:78 未勾 | ⚠️ Minor-3 |
| `/sdflow-code-review` | tasks.md:83 未勾（用户明示跳过） | ⚠️ Minor-4 |

---

## 缺口清单

### 核心（阻塞 archive，不阻塞本次 PASS）

**C-1 · delta spec 的层状态投影表已被本 change 自己的试点证伪，archive 前 MUST 同步**
`specs/devenv-provisioning/spec.md:99-106` 的表仍写：

> \| `verified` \| **至少一条 `verified`** → 渲染成「已验证 @ `<sha>`」\|

而 **A29（mqtt-console 试点实证）证明这正是假绿**——e2e 层三条泳道只绿了一条（打包冒烟压根没做），标题照报「✅ 已验证」。代码已按 A29 修为**投影取最弱**：全绿才 `verified`，有绿有非绿 ⇒ **`partial`**（`devenv_schema.py:117-137` · `test_schema.py:267 test_one_green_lane_does_not_make_the_layer_green` · `layer_lane_tally` 报「3 条里绿了 1 条」）。

- **实现是对的**（更严、防假绿），**spec 文本是 stale 的**。判 ✅ 而非 ❌ 的理由：该 Requirement 的契约意图（层状态不可手写、不可伪造、不得称「已实现」）**已完全兑现**，代码只是比 spec 更保守。
- **但 archive 会把 delta 同步进 `openspec/specs/`** ⇒ 若不改，**被证伪的假绿规则会被固化成正式 spec**（且 spec 里没有 `partial` 这个层状态）。
- **处置**：`/sdflow-done` 的 archive 步（其职责本就是「delta 对码核验」）**MUST** 在同步前把该表更新为 A29 后的判据 + 补 `partial` 行。**verify 阶段不动四件套**（改 change 文档会触发 ship_gate 设计门失鲜）。

### Minor

| # | 缺口 | 影响 |
|---|---|---|
| **M-1** | `devenv_lint.py:110 unverified_lanes()` 是**死代码**——`report()` 直接遍历 `lanes` 打印全量泳道，从未调它（全仓 grep 只在测试注释里出现名字）。spec 要求的「逐条列出未 verified 泳道 + `blocked_by`」由泳道状态块**实际满足**（真消费仓输出可证）。 | 无功能影响；同类死代码本仓有清理先例（`a147bd7`） |
| **M-2** | `maintain-scan` 的 Scenario「`devenv_lint` 不可用时显式提示」**只有代码分支（`maintain_scan.py:286,349`），无对应测试**——其余 5 个 Scenario 均有专测。 | 分支可读可信但无机验；ImportError 路径回归无网 |
| **M-3** | 试点结论未回灌 `references/`（tasks.md:78）。**独立判定：不构成核心缺失**——spec 唯一强制的回灌（三条机械方案的负面知识）**已在** `verification-patterns.md`；A29/A30 的修**已进代码 + SKILL.md 问话纪律 + `environments-template.md` 三分判据**。剩余的只是「未覆盖形态 → 补 `lane-patterns.md` 的格」，无 spec Requirement 强制。 | 建议转 todolist |
| **M-4** | `/sdflow-code-review` 未跑（用户明示跳过）。**独立判定：不构成核心缺失**，但按记忆库「冷 code-review 层 load-bearing」——本 change 恰恰是**冷层三次抓到承重级假绿**的活样本（G3 不可达 · A29 一绿即绿 · sad_schema fence 假绿），跳过它是**真实的残余风险**，须在 hand-off 显式登记。 | 残余风险，人已知情 |
| **M-5** | 观察（非本仓代码缺陷）：mqtt-console 的存量 `environments.md:8` 图例仍复现 `⚠️ 待定` 字面量 ⇒ `env_pending` 报 **3/10，真待定只有 2**。A30-F2 的修（图例「指称而不复现」）**已进骨架**（`devenv_scaffold.py:76-82` + `test_lint.py:195`），但**存量消费仓文件未回刷**。 | 消费仓数据，下次 `continue` 自愈 |

---

## 判定

**PASS** —— 三份 spec 的 **全部 29 + 6 + 4 个 Scenario 均有可机验证据锚点**（唯 M-2 一条 Scenario 只有代码锚、无测试锚）；上一轮三条 FAIL 逐条**独立复核为真**（含在真消费仓上亲跑 CLI 验可达性，不信任任何报告）；1260 tests 全绿。

**⚠️ 交给 archive 的硬要求**：**C-1 必须在 delta 同步进 `openspec/specs/` 之前修掉**——否则本 change 自己试点证伪的那条假绿规则，会被写成永久 spec。
