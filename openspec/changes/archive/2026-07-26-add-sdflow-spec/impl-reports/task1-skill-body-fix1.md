# Task 1 · fix 轮次 1 — 双轴审 8 条发现的修补报告

**票**：Task 1（`sdflow-spec` skill 本体 + 两道机械门）
**输入**：双轴审发现清单 8 条（1 Critical / 3 Important / 4 Minor）
**基线**：`210298a`（首轮实现）→ **本轮**：`4d6638a` + 守卫加固一处（见 F-4）
**分支**：`feat/add-sdflow-spec`

> 首轮报告 `task1-skill-body.md` **未覆盖**，只订正了两处失真的证据锚（见 F-8）。

---

## 0. 一览

| # | 级别 | 发现 | 状态 |
|---|---|---|---|
| F-1 | Critical | `_section_body` 对 fenced code block 无感 → 假绿 | ✅ 修（复用单一源） |
| F-2 | Minor（同函数） | docstring 称「同级/更高级」，代码对任何 `#` 都断 → 假红 | ✅ 修（按级数比对） |
| F-3 | Important | validate 门在 4 条 CI 泳道恒 skip | ✅ 修（装 openspec CLI） |
| F-4 | Important | 共享字符串第三处消费者未被守 | ✅ 修 + **守卫本身的子串坑一并修** |
| F-5 | Important | C.1 身份核验丢掉 SA-13 的「时间戳 / 决策 hash」 | ✅ 修（增第 4 判 + schema 同步） |
| F-6 | Minor | `subprocess.run` 无 timeout | ✅ 修（面治：全文件） |
| F-7 | Minor | 正文夹「否决理由 / 元教训」违反 DOC-1 | ✅ 修（四份文件扫全，建附录 A） |
| F-8 | Minor | 同族硬编码计数残留 + 行数锚失真 | ✅ 修 + 同族全量重扫 |
| **F-9** | **fold** | `test_downstream_reference_guard` **本就是红的** | ✅ 修（见 §2.9） |

**全量 pytest**：`2 failed → 1 failed`（唯一残红 = 已知 baseline 宿主依赖，见 §3.1）。

---

## 1. 逐条：修法与证据锚

### F-1 [Critical] `_section_body` 围栏无感 → dogfood 自指假绿

**修法**：`hack/tests/test_decision_memo_gate.py:31-43` 从**文件路径**加载
`sdflow-ship/scripts/ship_gate.py`，直接复用其 `FenceTracker` / `HtmlCommentTracker`
（本仓 fence 识别的**单一源**，`ship_gate.py:568-579` 原文即「MUST NOT 再各自手抄」）。

- **跨目录 import 可行 ⇒ 取最优解，不需要次优方案**：目录名含 `-`（非合法包名），故用
  `importlib.util.spec_from_file_location` —— 与既有先例
  `sdflow-ship/tests/test_gate_breaker.py:13-16` 同一 idiom，不碰 `sys.path` / `sys.modules`。
- **∴ 不需要「防两处漂移」的守卫**：两处**是同一份实现**（一个 module 对象），不是两份拷贝，
  结构上不存在漂移面。加一条守卫反而会暗示「这里有两份」。
- 判据落点：`_visible_flags()`（:77）逐行算「可当标题看」的行 = 非围栏行 ∧ 不在围栏内 ∧
  不在 HTML 注释块内；`_section_body()`（:92）的**定位**与**终止**两处都只认可见行。

**面治（基准 3）**：一并把 **HTML 注释块**纳入（把整节 `<!-- … -->` 掉，此前同样假绿）。
它与既有的 `_strip_noise` 是两件事：那条管「小节里只有注释」，这条管「标题本身被注释掉」。

**新增用例**（TDD：先写、确认红、再修绿）：

| 用例 | 断言 |
|---|---|
| `test_heading_inside_fenced_block_is_not_a_real_heading` | ``` / `~~~` / 四 backtick **三族各一发**：模板块内的 `## 承重约束` 不算小节 ⇒ 真正空着的那节判红 |
| `test_fenced_heading_neither_truncates_nor_relocates_the_section` | 直接打 `_section_body`：围栏内的标题既不截断本节正文、也不把定位抢过去 |
| `test_heading_hidden_in_html_comment_block_is_red` | 整节被注释掉 ⇒ 仍判缺失 |

**红→绿实测**：加用例后 `3 failed, 14 passed` → 修完 `17 passed`。

### F-2 [Minor·同函数] 级数比对（`###` 子标题假红）

`_atx_level()`（:66）按 CommonMark ATX 的**有界**词法取级数（行首 ≤3 空格 + 1–6 个 `#` +
空白/行尾）；`_section_body` 只在 `lv <= level` 时终止 ⇒ `### D1 …` 属本节正文。

- 顺带：「行首缩进 ≥4 列的行按定义是缩进代码块、不是标题」被这条正则**免费覆盖**，
  无需像 `ship_gate.py` 那样另设 `is_indented_code_line`（那边判的是勾选框行，不是标题行）。
- 新增用例 `test_subheading_does_not_end_the_section`（决策纪要必然用 `###` 列决策）。
- docstring 已与代码一致（:93-99）。

### F-3 [Important] CI 装 openspec CLI

`.github/workflows/mechanical-gates.yml:71-94`：新增 `actions/setup-node@v4`（node 22）+
`npm install -g @fission-ai/openspec@1.5.0` + `openspec --version` 回显。

- **版本是实查的**，不是凭记忆：`openspec --version` → `1.5.0`；
  `npm ls -g` → `@fission-ai/openspec@1.5.0`；该包 `package.json` 的
  `engines: {node: ">=20.19.0"}` ⇒ node 钉 22（满足下限且是 LTS）。
- **钉死版本**的理由与本文件既有取舍一致（第 31 行「MUST NOT 用浮动版本」）：门 2 的用例
  断言的是 **1.5.0 的具体行为**（`validate --strict` 只覆盖 delta specs），浮动会在新版
  发布当天无预警变红。
- **只铺一条泳道**（`ubuntu-latest` × py3.12）：沿本文件既有论证「两条轴各自的理由互不相干，
  交叉只是重复验证」—— openspec 是 node CLI，行为与 os / python 版本均无关，铺满 4 条只是
  同一信息重复 4 次，且 macOS 泳道按 10 倍计费。
- **实测锚**：`env PATH=/usr/bin:/bin /usr/bin/python3 -m pytest hack/tests/test_decision_memo_gate.py -q -rs`
  → `11 passed, 6 skipped`，skip 理由逐条为「openspec CLI 未安装」；有 CLI 时 `17 passed`。
  ⇒ 这 6 条此前在**全部**泳道恒 skip 属实。
- YAML 语法已解析核验（`yaml.safe_load` 出 9 个 step，顺序正确）。

### F-4 [Important] 共享字符串的第三处消费者 + **守卫自身的子串坑**

**先全量 grep（不加 `--include`）**：`grep -rn "拍板决策" .` / `grep -rln "承重约束" .`。
命中按「是不是**格式消费者**（改标题会坏掉的地方）」分类：

| 命中 | 归类 | 处置 |
|---|---|---|
| `hack/tests/test_decision_memo_gate.py:36` | 门本体 | 真相源 |
| `sdflow-spec/references/decision-memo-schema.md`（模板 + §3 表） | **格式消费者** | 已守（既有） |
| `sdflow-spec/SKILL.md:365`（C.1 起手核验） | **格式消费者** | ✅ **本次纳入** |
| `openspec/changes/add-sdflow-spec/{proposal,design,specs,tasks}.md`、评审报告 | 散文提及（`（拍板决策/承重约束）`），非标题字面量；且四件套按票禁令冻结 | 不纳入 |
| `docs/workflow-skills/matt-pocock-workflow.md:120` | 「批处理拍板决策登记区」——**不同词义**，非本 schema | 不纳入 |

落点：`MEMO_SECTION_CONSUMERS`（:50-53），`test_schema_doc_and_gate_agree` 逐个消费者断言。

🔴 **变异实测把守卫自己的洞打出来了**（本轮的额外收获）：
第一版守卫写成 `assert heading in doc`，跑变异 **M5「只把 SKILL.md 里的
`## 承重约束` 改成 `## 承重约束项`」⇒ 竟然全绿** —— 因为原名是新名的**前缀**（本仓「gate
子串检测自指坑」的同形）。修法：判据加右界
`re.search(re.escape(heading) + r"(?![^\s\`|])", doc)` —— 紧跟其后的字符须 ∈ {空白, 反引号,
竖线} 或已到文末，覆盖三种真实出现形态（代码块内独占一行 / 行内 `` `## X` `` / 表格单元格）。
**不能用行锚定**：SKILL.md 里这两个名字是**行内**出现的。

### F-5 [Important] C.1 补第 4 判（`decision_hash` + `generated_at`）

**先亲自打开 SA-13 对照**（`specs/spec-authoring/spec.md:297`）：
「C 起手 SHALL 比对 memo 的 `change`/`branch`/**时间戳**/**决策 hash** 与当前盘面」。

- `sdflow-spec/SKILL.md:360-378`：三判 → **四判**。判 4 = 重算 `decision_hash` 比对 +
  `generated_at` 读出来呈现给人（不可解析 / 落在未来 ⇒ 同样请人确认）。
- **两种缺口分开处置**（新写死，防止把「没定稿」误当「身份不符」）：
  hash/身份**不符** ⇒ 呈现旧 memo 摘要请人拍板复用还是重做 B；
  `decision_hash`/`generated_at` **缺失** ⇒ 那是相位 B 收敛两步没走完 ⇒ 退回 B 补定稿。
- `references/decision-memo-schema.md`：新增「`decision_hash` 的唯一算法」小节（§2 末）+
  §3 表新增两行 + 表下一句分流说明。
- 🔴 **口径的单一源 = 那条命令本身**：定稿（B.7 ④）与核验（C.1 判 4）跑**同一条命令**
  ⇒ 结构上没有「两端口径不同」的失配面。**已实跑验证**（scratchpad 造 memo）：
  `1f410675946c`，且 `### D1.1` 子标题不会提前截断。
  同时如实写明它的边界：逐行字面量、不认围栏 ⇒ 该节内若出现 `## ` 开头的行（含代码块内），
  hash 只覆盖到那一行为止；两端同命令 ⇒ 不失配，只是覆盖面变窄（通则④：低概率小影响，
  完美解法要在 skill 里复制一份 fence 逻辑，而那正是 F-1 明令禁止的）。

### F-6 [Minor] subprocess timeout（面治：全文件）

`_CLI_TIMEOUT_S = 60`，`_validate()` 与 `_status_is_complete()` **两处** `subprocess.run`
全部带上（文件内 subprocess 调用共两处，已扫全）。

### F-7 [Minor] DOC-1：正文只留最终态

**扫的是四份新文件全体**，不只被点名的三处。逐句过 DOC-1 的「删除测试」——
「只有读过上一版的人才需要的句子」才搬：

| 位置 | 判定 | 处置 |
|---|---|---|
| `SKILL.md` B.1「—— 本仓已真实发生过」 | 历史事件 | → 附录〔A-1〕 |
| `SKILL.md` C.3「那是 Workflow `agent()` 的参数，该调度路径已被否决」 | 否决理由 | → 附录〔A-2〕，正文只留 `MUST NOT 用 agentType` |
| `SKILL.md` 出口序列「拿它当理由是漏查」 | 元教训 | → 附录〔A-3〕 |
| `degradation-ladder.md`「重试次数为什么是 1……MUST NOT 为此单独返工」 | 元教训/自辩 | → 附录〔A-1〕，正文改成「判据是错误类别，不是次数」 |
| `SKILL.md` C.2「实跑 `instructions --json` 核验：`specs.dependencies` 只有 `[proposal]`」 | **首次阅读者需要**（否则会把强制阅读清单「优化」回 CLI 依赖图） | **留正文** |
| `SKILL.md` B.1③「CLI 无 rename change（实查：仅 new change / archive）」 | 同上 | **留正文** |
| `SKILL.md` 0.2「裸 eval 会被静默吞 + 旧值留存」 | 同上（解释四步为何存在） | **留正文** |
| `degradation-ladder.md` §2「通用子代理 = 降级即提权」/ §5 覆盖面实证 | 同上 | **留正文** |
| `decision-memo-schema.md` §5 三条理由 | 同上 | **留正文** |
| `adr-and-glossary-templates.md` 全文 | 无同类句子 | 无改动（故不建附录） |

新增：`sdflow-spec/SKILL.md` 末尾「附录 A · 依据与演进史」（三条）、
`references/degradation-ladder.md` 末尾「附录 A」（一条）。正文引用写成〔A-n〕。

### F-8 [Minor] 硬编码计数 + 失真的行数锚

- `docs/drafts/principle-4-simplicity-triage-draft.md:85`：「推 18 个投放面」→「推全部投放面
  （数量由脚本 glob 自报，**MUST NOT 在文档里硬编码计数**）」。
- **同族全量重扫**（`grep -rniE "[0-9]+ *个[^。，、）)]{0,14}(投放面|skill)"`，**不加 `--include`**）
  ——排除冻结/历史载体后**零残留**。逐条归类：

| 命中 | 归类 |
|---|---|
| `docs/sdflow-fable5/*`（4 处「15 个 skill」） | **定基线快照**：文档集头部写死「2026-07-10 产出（git HEAD `fc1b98b` / v0.9.0）」——改数字会产出更误导的产物（首轮 C2 结论维持） |
| `openspec/adr/0007:3,29,34`（「12 个 skill」「9 个改名 skill」） | 历史决策记录（ADR 描述决策当时的盘面） |
| `openspec/issues/todolist/2026-07-todolist.md:1674`（「17 个 SKILL.md」） | issue 台账里的**带日期实测**记录 |
| `openspec/changes/add-sdflow-spec/**`（design/proposal/评审报告） | 四件套按票禁令冻结；评审报告是冻结记录 |
| `sdflow-init/SKILL.md`「3 个配套 skill」 | **不同族**：那是固定的配套集合（spec-review/code-review/done），不是会漂的计数 |
| `docs/workflow-skills/matt-pocock-workflow.md:6`「6 个只读深读代理」 | **不同族**：调研方法学记录 |

- `impl-reports/task1-skill-body.md:13,75`：`497` → `499`，并把证据锚改成
  `git show 210298a:sdflow-spec/SKILL.md | wc -l`（钉死在首轮那个提交，**不会再随后续编辑失真**）。

### F-9 [fold] `test_downstream_reference_guard` 本就是红的（清单外，本票自造）

**发现**：本轮全量 pytest 出现**第二条**红——
`sdflow-issues/tests/test_downstream_reference_guard.py::test_no_legacy_skill_references_outside_allowlist`，
offender 是**首轮自己的报告** `impl-reports/task1-skill-body.md`（C2 段落里逐字写了两个已删除
skill 的目录名）。

**为什么首轮没看见**（根因，值得记）：该守卫扫的是 `git ls-files`（**tracked**）。首轮跑全量
pytest 时那份报告还是 untracked（首轮报告 §3.2 的 `git status --porcelain` 输出里就写着
`?? …/impl-reports/`）⇒ 守卫看不见它；`210298a` 提交之后才进入扫描面。
**已用 `git stash -u` 亲验：在 `210298a` 干净树上单跑该文件同样红** ⇒ 不是本轮引入。

**修法（取窄的那个）**：改自己的措辞（不复述旧名，改为指路 `docs/sdflow-fable5/02-module-reference.md`
——`docs/**` 在该守卫的 allowlist 内），**而不是**把 `openspec/changes/add-sdflow-spec/` 整个目录
加进 allowlist。理由：那会为一句散文永久放宽整个 change 目录的扫描面；而这里既不是调用点、
也不是 CI/spec 承重点，改一句话即可。

⚠️ **同一个坑还有一颗未爆弹**（**不是我的产物，故未动**）：工作树里有一份 untracked 的
`openspec/changes/add-sdflow-spec/impl-reports/task1-review-package.diff`（双轴审留下的），
其 diff 正文里**含那两个旧名的字面**。**谁把它 `git add` 谁就会把该守卫打红**——建议直接删除
或不入库。

---

## 2. 非恒真锚：定点变异实测

⚠️ **全部变异在 scratchpad 的 `git worktree` 副本里做**（`$SCRATCH/mut`，detached HEAD），
工作树零改动；实测完 `git worktree remove --force` 清理（`git worktree list` 已确认只剩主树）。

| # | 变异 | 结果 | 说明 |
|---|---|---|---|
| M1 | `_section_body` 整体回退成首轮旧口径（任何 `#` 都断 + 无可见性） | **4 failed, 13 passed** | 新旧口径的差集全部落在断言上 |
| M2 | `_visible_flags` 恒返回 `True`（放宽可见性） | **3 failed** — 三条围栏/注释用例 | 围栏与注释块两支各自有锚 |
| M3 | 终止条件 `lv <= level` → `lv is not None`（放宽级数） | **1 failed** — `test_subheading_does_not_end_the_section` | F-2 的锚非恒真 |
| M4 | `check_decision_memo` 首行插 `return []`（删门本体） | **6 failed, 11 passed** | 红侧用例全红 |
| M5 | **只**把 `SKILL.md` 的 `## 承重约束` 改名为 `## 承重约束项` | 第一版守卫 **17 passed（假绿！）** → 修判据后 **1 failed** | 见 F-4，这条变异直接抓出守卫自己的子串坑 |
| M6 | 守卫里去掉 SKILL.md 那一行 + 同一改名 | **17 passed** | 反向对照：证明 M5 的红**确实来自新增的那一条消费者**，不是被别的门顺带满足 |
| M7 | 只改 schema 文档侧的小节名 | **1 failed** | 既有那一侧仍在守 |
| 还原后 | — | **17 passed** | — |

---

## 3. 命令输出（实跑）

### 3.1 仓根全量 pytest

修补**前**（本轮起手，`210298a`）：

```
2 failed, 2648 passed, 11 skipped, 3 xfailed in 333.92s
FAILED sdflow-init/tests/test_outside_voice_job.py::test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret
FAILED sdflow-issues/tests/test_downstream_reference_guard.py::test_no_legacy_skill_references_outside_allowlist   ← F-9
```

修补**后**：见 §3.4（唯一残红 = `test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret`，
宿主环境依赖，首轮已用 `git stash -u` 在 baseline 上验过同样红，与本票无关）。

### 3.2 本票门文件

```
$ /usr/bin/python3 -m pytest hack/tests/test_decision_memo_gate.py -q
17 passed

$ env PATH=/usr/bin:/bin /usr/bin/python3 -m pytest hack/tests/test_decision_memo_gate.py -q -rs
11 passed, 6 skipped        ← 6 条 skip 理由全部是「openspec CLI 未安装」（F-3 的实测依据）
```

### 3.3 `decision_hash` 唯一算法实跑

```
$ printf '…## 拍板决策\n\n- **D1 拷问前置** — 依据：便宜\n\n### D1.1 细节\n\n补充\n\n## 承重约束\n…' > memo.md
$ python3 -c '<schema §2 的那条命令>' memo.md
1f410675946c
```

`### D1.1` 未提前截断；换成 `## 其它` 才截断 ⇒ 与文档写的口径一致。

### 3.4 收尾三件（全量 pytest / `--check` / `setup.sh`）

见文末 §4「收尾核验」（报告落盘后实跑，输出已回填）。

---

## 4. 收尾核验

```
$ /usr/bin/python3 -m pytest -q
FAILED sdflow-init/tests/test_outside_voice_job.py::test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret
1 failed, 2649 passed, 11 skipped, 3 xfailed in 334.32s (0:05:34)

$ /usr/bin/python3 hack/sync_principles.py --check
[sync_principles] ✅ 19 个投放面全部与真相源一致

$ bash setup.sh   → exit 0
[sync_principles] ✅ 19 个投放面全部与真相源一致
[gen_workflow_guide] ✅ WORKFLOW-GUIDE.md 与单一源一致
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致

$ wc -l sdflow-spec/SKILL.md   → 528（上限 600，含 140 行通则托管块；本轮 +29 = 附录 A + C.1 判 4）
```

---

## 5. Concerns（交编排层）

1. **首轮 C1 未变**：「截断的 design.md → `validate --strict` 判红」在 CLI 1.5.0 上不成立
   （`specs/` 之外三份产物无机械门）。SA-05 Scenario 与 design.md 失败模式表两处措辞是否走
   `[spec-review-amendment]` 修订，仍待编排层裁决。本轮同样未动四件套。
2. **`task1-review-package.diff` 是颗未爆弹**（见 F-9 末段）：untracked、含旧 skill 名字面，
   `git add` 即打红 `test_downstream_reference_guard`。非本票产物，未处置。
3. **`setup.sh` 从开发 checkout 跑**：全局 skill 链接仍指向本 WIP checkout（首轮 C4 同）。
   合并后须在运行 checkout（`~/.skills/sdflow-skills`）重跑 `setup.sh` 还原。
4. **CI 那条泳道尚未在真 runner 上跑过**：node/npm 步骤是按实查的版本约束写的（本机
   `openspec 1.5.0` + `engines.node >=20.19.0`），但 GitHub runner 上的实跑要等 push。
   若 `npm install -g` 在 runner 上撞权限，改用 `npx` 或 `sudo npm` 即可，判定逻辑不受影响。
