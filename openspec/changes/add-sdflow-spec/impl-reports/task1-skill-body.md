# Task 1 · `sdflow-spec` skill 本体上线且机械门会红 — 实现报告

**票**：Task 1（tasks.md 的 2.1–2.10 + 3.2 + 4.1–4.3）
**R-ID**：SA-01, SA-03, SA-04, SA-05, SA-06, SA-08, SA-09, SA-10, SA-13
**分支**：`feat/add-sdflow-spec`

---

## 1. 落地物清单

| 文件 | 动作 | 行数 |
|---|---|---|
| `sdflow-spec/SKILL.md` | 新增 | 499（含 140 行通则托管块）〔@`210298a`〕 |
| `sdflow-spec/references/decision-memo-schema.md` | 新增 | 81 |
| `sdflow-spec/references/degradation-ladder.md` | 新增 | 74 |
| `sdflow-spec/references/adr-and-glossary-templates.md` | 新增 | 63 |
| `hack/tests/test_decision_memo_gate.py` | 新增 | 13 个用例 |
| `CLAUDE.md` | 改（`:192` 删硬编码计数） | 1 行 |
| `hack/tests/test_sync_principles.py` | 改（docstring 删硬编码计数） | 3 行 |

---

## 2. 逐条验收标准 → 证据锚

### ✅ `/sdflow-spec` 在两个 runtime 均可见，且模型无法自行唤起

- `sdflow-spec/SKILL.md:1-12` frontmatter：`name: sdflow-spec` +
  **`disable-model-invocation: true`**（`:3`）+ `description`（末尾 `Trigger with /sdflow-spec。`）。
- 双 runtime 可见性：`bash setup.sh` 后 `~/.claude/skills/sdflow-spec` 与
  `~/.codex/skills/sdflow-spec` 各出一条指向本仓的软链（命令输出见 §3）。
- ⚠️ `disable-model-invocation` 在 Codex 宿主的语义未核（tasks 9.2 已登记为独立工作），本票不覆盖。

### ✅ 三相位管线的全部判据在指令中可查

| 判据 | 锚 |
|---|---|
| A 的收束禁止清单**三项** | `SKILL.md` §「相位 A · 澄清」A.2（跨模块依赖未查清 / ≥2 方案未给推荐 / 目标态一句话写不出） |
| B 起手**三步** | B.1：①`git status --porcelain` 脏则 halt ②FF-0 **三分支判定**表（保护分支建 / 本 change 分支跳过 / **其它 feature 分支 halt 问人**）+ `checkout -b` 失败 fallback ③`openspec new change`（含「MUST NOT 暂定名后改名」+ CLI 无 rename 实证） |
| B 的停止信号**最小充分条件** | B.5：「人机共识达成 ∧ 承重约束逐条站稳」；「站稳」= 有可核验证据锚（file:line / 命令输出 / 人的确认记录）；显式 MUST NOT 用「问了 N 轮」 |
| C 的**强制阅读清单**（specs 步显式读 design） | C.2 四行表，`specs/**` 一行含 **`design.md`**；下附实测反驳（CLI `design.dependencies`/`specs.dependencies` **都只有 `[proposal]`**、`tasks.dependencies` = `[specs, design]` 不含 proposal） |
| 写后 `status` + `validate --strict` 双判 | C.4，两条命令 + 「存在态判据是文件存在性」的 CLI 源码锚 |
| 终审的 design↔specs 互验 + 中间态判据 | §终审 第 2 条 + 「中间态判据」段（「砍掉的候选 + 理由」**完全消失**才算判断性偏差） |
| 出口序列三步**原样贴**且**只引两条理由** | §出口序列：代码块内三步原样文本 + 两条理由（cache 按模型隔离 / 产审错档）+ 🔴 MUST NOT 引用「主审裁决需冷视角」 |

其余承载：重入探测 §0.3、相位状态机 §0.4、纪要身份核验 §C.1、ADR/术语惰性钩子 §B.6、
降级阶梯与三要素诊断 §降级与诊断、相位 checkpoint §checkpoint 纪律、
档位解析四步加固协议 §0.2（(a) unset →(b) `[ -x ]` 预检 →(c) 捕获退出码再 eval →(d) eval 后校验枚举与非空）。

### ✅ 决策纪要字段集与增量落盘时机明确；纪要不并入 design.md

- 字段与身份字段（`schema_version` / `change` / `branch` / `generated_at` / `decision_hash`）：
  `sdflow-spec/references/decision-memo-schema.md` §2 的完整模板。
- 增量落盘时机：`SKILL.md` B.4（「一条承重约束拿到证据锚 ⇒ 当场追加写」）+ schema 文档 §4；
  两处都如实标注「两次保存点之间的部分是已知损失，MUST NOT 声称零损失」。
- 不并入 design.md：`SKILL.md` §终审 的 🔴 段 + schema 文档 §5（含三条理由：design 原生 Sections
  无「承重约束」槽位 / memo 单独已满足不变式 / 双写无优先级规则）。

### ✅ 通则托管块由 `sync_principles.py --apply` 落入，`--check` 无漂移

```
$ /usr/bin/python3 hack/sync_principles.py --apply
[sync_principles] ✅ 已回填 1 个：
   sdflow-spec/SKILL.md
$ /usr/bin/python3 hack/sync_principles.py --check
[sync_principles] ✅ 19 个投放面全部与真相源一致
```

投放面从 18 → 19 自动扩张：`sync_principles.py:58-60` 的 `skills()` 用 `REPO.iterdir()` 发现
顶层含 `SKILL.md` 的目录，**无需改脚本**。块内文本未手写一个字。

### ✅ SKILL.md 主体行数 ≤ 上限，超出部分已外置

```
$ git show 210298a:sdflow-spec/SKILL.md | wc -l
     499
```

上限 600（design NFR 表 / tasks 2.10）。外置三份 `references/`：降级阶梯表 + 失败模式表 +
退避与错误分类、决策纪要字段 schema + 模板、ADR/术语最小模板 —— 均为「表格型、少判断」内容，
对齐 `sdflow-code-review` 外置 `code-checklists/domains`、`sdflow-roadmap` 外置模板的既有模式。

### ✅ 新增 pytest 用例：`decision-memo.md` 缺失 / 必填小节为空 → 红（非恒真锚）

`hack/tests/test_decision_memo_gate.py`：

| 用例 | 断言 |
|---|---|
| `test_missing_memo_is_red` | 文件不存在 ⇒ 判红 |
| `test_empty_required_section_is_red` | `## 承重约束` 有标题无正文 ⇒ 判红 |
| `test_comment_only_section_is_red` | 小节只剩模板注释 ⇒ 仍判空 |
| `test_both_sections_missing_reports_both` | 两节都缺 ⇒ 两条都报（不短路） |
| `test_complete_memo_is_green` | **反向锚**：填齐必须判绿（防恒红假门） |
| `test_schema_doc_and_gate_agree` | 小节名是共享字符串 ⇒ 门与 `references/decision-memo-schema.md` 逐字一致 |
| `test_repo_memos_all_pass_the_gate` | 面级守卫：本仓 `openspec/changes/*/decision-memo.md` 逐份过门 |

⚠️ **诚实标注**：`test_repo_memos_all_pass_the_gate` 当前扫到 **0 份**（本仓尚无 change 由
`/sdflow-spec` 产出），是**目标态**的面级守卫，不是当下就在挡什么。这一点在用例 docstring 里写死了。
非空的挡拦力由上面六条 fixture 用例提供。

**定点删门 = 必红（四次变异实测，每次跑完即从备份还原）**：

| 变异 | 结果 |
|---|---|
| `check_decision_memo` 首行插 `return []`（删掉门本体） | `4 failed, 9 passed` — 四条红侧用例全红 |
| `_strip_noise` 改为恒返回 `"x"`（放宽「非空」判据） | `2 failed, 11 passed` — 空小节两例红 |
| `REQUIRED_SECTIONS` 改「拍板决策」→「拍板决定」 | `4 failed, 9 passed` — 含真相源漂移守卫 |
| 把截断 fixture 换成完好 spec（验红不是被别的门满足） | `2 failed, 11 passed` |
| 还原后 | `13 passed` |

### ⚠️ 「截断的 design.md 经 `openspec validate --strict` → 红」— **该断言实测不成立**，见 §4 Concerns C1

已交付的是**同一判据的可达形态** + 一枚覆盖边界钉子：

| 用例 | 断言 |
|---|---|
| `test_intact_change_passes_strict_validate` | 反向锚：完好四件套必绿 |
| `test_truncated_spec_delta_is_caught_by_strict_validate` | ⭐ 截断的 `specs/foo/spec.md`（Requirement 后被切断）⇒ **exit≠0**，stderr 含 `scenario` |
| `test_status_says_done_while_validate_says_red` | ⭐⭐ 同一份盘面：`status.isComplete == True` **且** `validate --strict` 非 0 —— 「存在态 ≠ 合格态」的正面证明 |
| `test_validate_strict_only_covers_delta_specs`（3 参数化） | 覆盖边界钉子：半截 design.md / 半截 proposal.md / **空 proposal.md** 三者 `validate --strict` 均 **exit 0** |

### ✅ 硬编码的 SKILL.md 计数已删除并改由脚本自报

- `CLAUDE.md:192`：`**15 个 \`SKILL.md\`**` → `**每个顶层 \`SKILL.md\`**（由 sync_principles.py glob
  发现并自报数量，**MUST NOT 在文档里硬编码计数**——新增一个 skill 就会让它过期）`。
- `hack/tests/test_sync_principles.py:4`（模块 docstring）与 `:18`（用例 docstring）同族残留同步清理。
- 全量扫（**不加 `--include`**）：

```
$ grep -rn "15 个" . --exclude-dir=.git | grep -v archive/ | grep -v changes/add-sdflow-spec/
docs/workflow-skills/impl-pipeline-matt-vs-superpowers.md:35   # 「8-15 个 task」——非同族
docs/sad/07-devenv-skill-design.md:1088,1102,1158              # 「15 个格子/小节」——非同族
docs/sdflow-fable5/{README,01-…,02-…}.md（5 处）               # 同族但为定基线快照，见 Concerns C2
```

`openspec/changes/archive/**` 与 `openspec/changes/add-sdflow-spec/**` 未动（归档为冻结记录；
本 change 四件套按票禁令 MUST NOT 修改）。

### 仓根 pytest 全绿 / `setup.sh` 幂等 → 见 §3

---

## 3. 命令输出（实跑）

### 3.1 仓根全量 pytest

```
$ /usr/bin/python3 -m pytest -q
…
FAILED sdflow-init/tests/test_outside_voice_job.py::test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret
1 failed, 2646 passed, 10 skipped, 3 xfailed in 330.92s (0:05:30)
```

⚠️ **那一条红是既有的、与本票无关**，已按通则③亲验：

```
$ git stash -u -q            # 把本票全部改动移开，回到 baseline
$ /usr/bin/python3 -m pytest "sdflow-init/tests/test_outside_voice_job.py::test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret" -q
E               assert 'CONTROL_TRANSCRIPT_CANARY_A1B2' in ''
FAILED …::test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret
1 failed in 62.04s
$ git stash pop -q           # 还原
```

**baseline 同样红** ⇒ 本票未引入回归。红因：该用例的**对照组探针**要求真跑
`claude --bg --exec` 并从 `claude logs` 里读回哨兵，本机该链路当前取不到输出（用例自己的断言
消息即写着「对照组不成立 ⇒ 下面的断言不构成证据」）。属宿主环境依赖，非本票范围。

**本票新增用例单独跑**：

```
$ /usr/bin/python3 -m pytest hack/tests/test_decision_memo_gate.py -q
.............                                                            [100%]
13 passed in 7.84s
```

### 3.2 `setup.sh` 幂等 + 双 runtime 可见

```
$ bash setup.sh > /tmp/s1.txt 2>&1; bash setup.sh > /tmp/s2.txt 2>&1
exit1=0 exit2=0
$ diff /tmp/s1.txt /tmp/s2.txt && echo IDENTICAL
IDENTICAL ✅

$ tail -4 /tmp/s2.txt
[sync_principles] ✅ 19 个投放面全部与真相源一致
[gen_workflow_guide] ✅ WORKFLOW-GUIDE.md 与单一源一致
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致

$ ls -l ~/.claude/skills/sdflow-spec ~/.codex/skills/sdflow-spec
… /Users/cheneyzhao/.claude/skills/sdflow-spec -> …/04-sdflow-skills/sdflow-spec
… /Users/cheneyzhao/.codex/skills/sdflow-spec  -> …/04-sdflow-skills/sdflow-spec

$ git status --porcelain      # setup.sh 无仓内副作用
 M CLAUDE.md
 M hack/tests/test_sync_principles.py
?? hack/tests/test_decision_memo_gate.py
?? openspec/changes/add-sdflow-spec/impl-reports/
?? sdflow-spec/
```

### 3.3 「存在态 ≠ 合格态」实证（写进 §4 C1 的依据）

```
$ openspec validate demo --strict --type change     # 完好
Change 'demo' is valid                    EXIT=0
$ # 截断 specs/foo/spec.md（Requirement 后切断）
Change 'demo' has issues
✗ [ERROR] foo/spec.md: ADDED "Foo SHALL work" must include at least one scenario
                                          EXIT=1
$ # 删掉整份 proposal.md
Change 'demo' is valid                    EXIT=0     ← proposal 根本不被 validate 读
$ # 半截 design.md
Change 'demo' is valid                    EXIT=0     ← design 根本不被 validate 读
$ # 移走整个 specs/
✗ [ERROR] file: Change must have at least one delta…   EXIT=1
```

---

## 4. Concerns

### 🔴 C1 · 「截断的 design.md → `validate --strict` 判红」在 CLI 1.5.0 上**不成立**

**这不是实现取舍，是设计前提被实测证伪。**

`openspec validate <change> --strict` 只跑 `validateChangeDeltaSpecs`，**只读
`specs/*/spec.md`**。实证三条：

1. `dist/core/validation/validator.js` 全文**无 `design` 字样**（`grep -rln design` 在
   `dist/core/validation/` 下零命中）。
2. 把 `proposal.md` **整份删除**，`openspec validate demo --strict --type change` 仍输出
   `Change 'demo' is valid`、exit 0。
3. 只有把 `specs/` 整个移走（`Change must have at least one delta`）或截断 delta spec
   （`must include at least one scenario`）才会红。

**受影响的设计断言**（都在已过设计门的四件套里，本票 MUST NOT 改）：

- `specs/spec-authoring/spec.md:133-135` SA-05 Scenario「半截产物不被判完成」逐字点名
  **design.md**：「`status` 报 done 但 `validate --strict` 不过」—— 对 design.md **恒假**。
- `design.md:230` 失败模式表「writer 写半截/垃圾 → validate 判该产物未完成」同理，
  对 4 份产物里的 3 份（proposal / design / tasks）不成立。

**本票的处置（不改盘，只做可达的 + 如实标注）**：

- 机械门锚在 **delta spec** 上（`test_truncated_spec_delta_is_caught_by_strict_validate`）——
  「存在态 ≠ 合格态」这条判据**在它能覆盖的面上是真的挡得住的**，并由
  `test_status_says_done_while_validate_says_red` 正面证明。
- 新增 `test_validate_strict_only_covers_delta_specs` 把「design/proposal/tasks 无机械门」这个事实
  **机械钉住**：openspec 哪天扩了覆盖面，该用例会红，提示回来收紧文档。
- `SKILL.md` C.4 与 `references/degradation-ladder.md` §5 各写一段诚实边界，并把这三份产物的
  「未截断」显式交给**终审人判**（§终审 第 3 条）。

**需要编排层裁决的**：SA-05 Scenario 与 design.md 失败模式表这两处措辞是否要走
`[spec-review-amendment]` 修订。本票未动它们（票禁令 + 它们已过设计门）。

### C2 · `docs/sdflow-fable5/` 的「15 个 skill」未改（定基线快照，改反而更错）

该文档集头部写明「2026-07-10 由深度调研产出（git HEAD `fc1b98b` / v0.9.0）」，
且其总表**仍列着两个此后被合并删除的旧 issues skill**（见 `docs/sdflow-fable5/02-module-reference.md`
总表，旧名不在此复述——`test_downstream_reference_guard.py` 只豁免 `docs/**`，不豁免本目录）
—— 它描述的是一个与当前 HEAD 已不同的 roster。把 15 改成 16 会产出一个
「写着 16、列着旧 15」的更误导的产物；正解是重新生成整份模块参考，属另一件工作。
本票按通则③「不加宽」留置并在此登记。

### C3 · 相位二 / 相位三的内容在 SKILL.md 里只留了**接缝**，未实装

`subagent_type` 派发（C.3 末段）、外派阈值（A.3）按 spec 写进了指令，但三个 agent 定义、
`install_agents()`、`sync_principles.py` 的 `AGENT_TARGETS` 均属 tasks §5–§6（阶段二），
不在本票。SKILL.md 已把这些段落显式标注为「**阶段二**」，阶段一读者不会误以为它现在就该派子代理。

### C4 · `setup.sh` 从开发 checkout 跑会把全局 skill 链接整体指向本 WIP checkout

`CLAUDE.md:177,182` 与 design Migration Plan 已记载该已知行为。本票按执行契约第 5 条
只验证「跑通且幂等」，**未还原**——编排层/后续步骤需在运行 checkout 重跑 `setup.sh` 还原。
