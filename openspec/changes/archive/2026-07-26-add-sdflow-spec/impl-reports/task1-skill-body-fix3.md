# Task 1 · fix 轮次 3 — 接缝复审轮 2 的 2 条恒真锚修补报告

**票**：Task 1（`sdflow-spec` skill 本体 + 两道机械门）
**输入**：接缝复审轮 2 的 2 条 Important（**同族：恒真锚 —— 一起面治**）
**基线**：`961a936`（fix 轮 2 收尾）
**分支**：`feat/add-sdflow-spec`
**改动面**：**只有 `hack/tests/test_decision_memo_gate.py` 一个文件，产品面（SKILL.md / references / 脚本）零改动**

> 前三轮报告 `task1-skill-body.md` / `-fix1.md` / `-fix2.md` **未覆盖、未改动**。
> 四件套（proposal / design / specs / tasks）与 `superpowers-plan.md` **未动**，复选框未勾。

---

## 0. 一览

| # | 级别 | 发现 | 状态 |
|---|---|---|---|
| M-C | Important | hash 覆盖面锚**只在「拍板决策」节内取样**，窄于 schema 承诺的「frontmatter 之外全文」⇒ 收窄型变异静默放行 | ✅ 修（取样范围改为 frontmatter 之后**全部**非空行 + 三个跨区探针 + 下限 12） |
| M-F | Important | 两条 inline fixture 硬编码 `## 承重约束` ⇒ 小节改名后两条 ⭐⭐ dogfood 自指锚**双双恒真** | ✅ 修（全文件消灭硬编码小节名 + 断言换带右界的真相源判据） |

**共同根因（本轮）**：**「锚的取样范围/输入数据没有跟着真相源走」** ——
M-C 是取样**范围**写死在某一节（而契约是全文），M-F 是取样**输入**写死了字面量（而契约在 `REQUIRED_SECTIONS`）。
两者都表现为「门被抽空了，锚还是绿的」。

**本票门文件**：`19 passed → 19 passed`（用例数不变，锚的覆盖面变宽）。
**仓根全量**：`1 failed, 2651 passed, 11 skipped, 3 xfailed`（唯一残红 = 已知 baseline，见 §4.2）。

---

## 1. M-C [Important] hash 覆盖面锚窄于契约

### 1.1 复现（先证伪，再落笔）

`git worktree` 副本（detached @ `961a936`），按复审给的变异改 schema 文档里那条**唯一算法**：

```diff
- body=re.sub(r"\A---\n.*?\n---\n","",raw,count=1,flags=re.DOTALL)
+ body=raw[raw.index("## 拍板决策"):]
```

即把覆盖范围从「frontmatter 之外全文」收窄成「从 `## 拍板决策` 起到 EOF」——
**丢掉 H1 `# 决策纪要 · demo` 与整个 `## 目标态` 小节**。

```
$ /usr/bin/python3 -m pytest hack/tests/test_decision_memo_gate.py -q
19 passed in 6.76s          ← 静默，复审所报属实
```

**为什么旧锚看不见**：它的取样范围是 `_section_span(original, REQUIRED_SECTIONS[0])`
——只在「拍板决策」小节内逐行变异。而 M-C 的收窄**恰好从该小节的第一行开始**，
节内每一行都仍在覆盖内 ⇒ 逐行断言全过。
另一条 `..._frontmatter_independent` 只采样了「承重约束」一行（在收窄后的范围内）⇒ 也过。
∴ fix2 只堵住了「窄于门认可的正文」这半边，**「窄于文档承诺的范围」那半边是敞的**：
定稿后手改 `# 决策纪要` 标题或 `## 目标态`，只要未来有人做一次这样的收窄，判 4 就重新放行。

### 1.2 修法：取样范围 = 文档写的那个范围

`hack/tests/test_decision_memo_gate.py`：

1. 新增 `_body_start_line(text)` —— **取样范围定位器**（不是 hash 算法的复刻）：
   回答「frontmatter 之外是哪几行」。frontmatter 语法在本 schema 下**有界**
   （首行 `---`，到下一行 `---` 为止）⇒ 可手写（基准 5）。
2. `test_decision_hash_covers_every_line_the_gate_calls_body` 的变异循环
   由 `range(*_section_span(...))` 改为 `range(_body_start_line(original), len(lines))`
   —— 逐行遍历 **frontmatter 之后的全部非空行**，每一行改动后 hash MUST 变。
3. 取样范围**自身**的自检（防本条将来又被缩回单节）：三个探针必须都在取样集合里，
   且分踞「拍板决策」小节两侧 ——
   `# 决策纪要`、`## 目标态`（在它**之前**，M-C 那种收窄会丢）、
   `- **C1 CLI`（在它**之后**，旧的单节取样会丢）。
4. `checked >= 5` → `len(checked) >= 12`（fixture 实测非空行 = 12），仍是**下限**语义。

**为什么不改成「全文逐行 iff frontmatter」的对称写法**（通则②：带推荐+依据+代价）：
frontmatter 的两条 `---` 分隔行是**结构行**——给它们追加字符会让文档那条正则的
`\A---\n` 失配、frontmatter 整段不再被剥除 ⇒ hash 反而变 ⇒ 对称写法必须为分隔行开特例。
两条方向已由 `..._frontmatter_independent`（语义更好的变异：往 frontmatter 塞
`decision_hash: deadbeefcafe`）独立钉住，合起来正好等于文档承诺的范围 ⇒ 不为它加特例（通则④）。

**顺带的死代码清理**：`_section_span` 的存在理由（docstring 原文）就是
「给 `decision_hash` 覆盖面用例逐行变异用」。本轮该用例不再用它，全仓 `grep -rn "_section_span"`
确认只剩 `_section_body` 一个调用方 ⇒ 折回 `_section_body`，判据本体零变化（用例数不变可证）。

---

## 2. M-F [Important] inline fixture 硬编码 ⇒ 两条 dogfood 锚改名后恒真

### 2.1 复现（fix2 报告 §2.1 的声明被证伪）

fix2 报告 §2.1 表格里写着：inline 文本 fixture「改名后当场判红（**响亮**，不是假绿）」。
同一副本上做**完整改名 + 抽掉门的围栏/注释感知**：

- 改名：`承重约束` → `承重约束项`，改 `REQUIRED_SECTIONS`、`MEMO_SECTION_CONSUMERS`
  两行期望表、`sdflow-spec/SKILL.md`（8 处）、`references/decision-memo-schema.md`（6 处）；
  `test_schema_doc_and_gate_agree` 全绿（= 一次「合规的改名」）。
- 抽门：`_visible_flags` 改为 `return [True] * len(lines)`（门失去围栏与 HTML 注释块感知）。

| 组 | 变异 | 结果 |
|---|---|---|
| **M-G 对照** | 只抽门，不改名 | **4 failed**（含 `..._inside_fenced_block...` / `..._hidden_in_html_comment_block...`） |
| **M-F** | 抽门 **+** 完整改名 | **2 failed** ← 上述两条 ⭐⭐ 自指锚**消失了** |

⇒ 改名后 fixture 里的 `## 承重约束` 不再是「真标题的同名字面量」，
围栏/注释里塞的那行对门已无意义，两条用例**双双恒真**；
**HTML 注释块感知就此失去唯一守卫，而套件照样绿**。fix2 的那句声明不成立。

### 2.2 修法：全文件扫一遍，硬编码一处不留（基准 3 面治）

`grep -n "拍板决策\|承重约束" hack/tests/test_decision_memo_gate.py` 逐处归类后处置：

| 位置 | 归类 | 处置 |
|---|---|---|
| `REQUIRED_SECTIONS` | **真相源** | — |
| `MEMO_SECTION_CONSUMERS` 的 key | **`grep` 普查快照**（故意留字面量） | **保留** —— `set(expected) == set(REQUIRED_SECTIONS)` 在改名时当场判红、逼人回来核对消费面；若改成引真相源，那条断言即恒真（注释已写明） |
| `test_heading_inside_fenced_block_is_not_a_real_heading` 的 fixture | inline 硬编码 | ✅ 改 f-string 引 `REQUIRED_SECTIONS[1]` |
| `test_heading_hidden_in_html_comment_block_is_red` 的 fixture | inline 硬编码 | ✅ 同上（两个小节名都改） |
| `test_fenced_heading_neither_truncates_nor_relocates_the_section` 的 text + 两处查询参数 | inline 硬编码（复审未点名，**面治扫出**） | ✅ 同上 |
| `_memo_with_fence_then_more_decisions` 围栏内的 `## 承重约束`（复审未点名，**面治扫出**） | inline 硬编码 —— 它正是 hash 覆盖面 fixture 的「围栏自指」性质所在 | ✅ 同上 |
| 4 处 `assert "承重约束"/"拍板决策" in problems[0]`（:198/:206/:257/:288） | 裸子串断言 | ✅ 换 `_names_section(problem, heading)` |
| docstring / 注释里的散文提及 | 说明文字，非可执行 | 不动 |

**新判据 `_names_section(problem, heading)` = `f"「{heading}」" in problem`** ——
引真相源**且带右界**：门给出的消息形如 `必填小节「## 承重约束」为空`，`「…」` 就是天然右界。
裸子串在**前缀改名**（`## 承重约束` → `## 承重约束项`）下照样为真 ⇒ 恒真假绿，
与 `test_schema_doc_and_gate_agree` 的右界判据是同一个坑（本仓「gate 子串检测自指坑」同形）。

---

## 3. 定点变异回验（本轮核心交付）

⚠️ 全部变异在 `git worktree` 副本（scratchpad，detached @ `961a936`）里做，**主工作树零改动**；
实测完 `git worktree remove --force`，`git worktree list` 已确认只剩主树。
变异组一律**把修后的测试文件拷进副本**再改被测面。

| # | 变异 | 修**前** | 修**后** | 判 |
|---|---|---|---|---|
| **控制组** | 零变异 | 19 passed | **19 passed** | ✅ 非恒红假门 |
| **M-C** | hash 命令收窄成 `body=raw[raw.index("## 拍板决策"):]` | **19 passed（静默！）** | **1 failed** — `..._covers_every_line...`，报「改了 frontmatter 之外的第 2 行（`'# 决策纪要 · demo'`）而 decision_hash 不变」 | ✅ 由静默转必红 |
| **M-G 对照** | 抽掉 `_visible_flags` 围栏/注释感知，不改名 | 4 failed | **3 failed** — 三条围栏/注释用例 | ✅ 见下方说明 |
| **M-F** | 抽门 **+** 完整改名 `承重约束→承重约束项` | **2 failed**（两条 ⭐⭐ 自指锚恒真） | **3 failed** — **与 M-G 逐条同名**，两条 ⭐⭐ 自指锚回到失败集 | ✅ 恒真消除，M-F ≡ M-G |
| **M-R 控制组** | **只**完整改名，不动门 | — | **19 passed** | ✅ 合规改名不误红（fixture 跟着真相源走） |

**M-G 从 4 failed 变 3 failed 的说明（如实报告，不是回退）**：
掉出的那条是 `..._covers_every_line...`。修**前**它是**间接**红的——旧取样范围
`_section_span(拍板决策)` 依赖 `_visible_flags`，门被抽空后该 span 在围栏那行就断，
只剩 2 行可变异，撞 `checked >= 5` 的「fixture 太瘦」下限而红，**不是因为 hash 覆盖面真出了问题**。
修**后**取样范围改由 schema 文档的契约（frontmatter 之外全文）直接定义、不再经过门的小节口径，
∴ 抽门不再牵动它。这是**解耦，不是失守**：

- 围栏/注释感知的守卫本来就是那 3 条专用用例，M-F/M-G 下它们**全数必红**；
- 「门认可的正文 ⊆ hash 覆盖面」这条 G-1 性质**变得更强**了 ——
  新取样是全体正文行，任何小节的正文都必然是它的子集，恒等性由取值范围结构性保证。

---

## 4. 命令输出（实跑）

### 4.1 本票门文件

```
$ /usr/bin/python3 -m pytest hack/tests/test_decision_memo_gate.py -q
19 passed in 6.93s
```

### 4.2 仓根全量 pytest

```
$ /usr/bin/python3 -m pytest -q
FAILED sdflow-init/tests/test_outside_voice_job.py::test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret
1 failed, 2651 passed, 11 skipped, 3 xfailed in 326.20s (0:05:26)
```

唯一残红 = 编排层已三次独立复现的 baseline 宿主依赖（失败点是**对照组**断言
`assert 'CONTROL_TRANSCRIPT_CANARY_A1B2' in ''`，即本机根本没有 `claude logs` 输出）
⇒ 与本票无关，未当回归处理。

`skipped` 由 fix2 的 10 变 11：`-rs` 逐条核过，11 条全是环境依赖
（`sdflow-issues` Windows 本地盘 ×7、`sdflow-init` 真机模型探针 ×2、
`test_outside_voice_child_lifecycle` 的信号风暴复现率 ×1、`test_outside_voice_utf8` 满盘前提 ×1）
—— 后两条 docstring 自述「复现率环境敏感」，即两次运行之间的抖动源，**不涉本票文件**。

### 4.3 收尾

```
$ /usr/bin/python3 hack/sync_principles.py --check
[sync_principles] ✅ 19 个投放面全部与真相源一致

$ git diff --stat
 hack/tests/test_decision_memo_gate.py | 128 +++++++++++++++++++++++-----------
 1 file changed, 86 insertions(+), 42 deletions(-)
```

产品面（`sdflow-spec/SKILL.md`、`references/*`、任何 `scripts/`）**本轮零改动** —— `git diff` 亲验。

---

## 5. Concerns（交编排层）

1. **前三轮 Concerns 逐条仍悬，本轮均未处置（不在本票范围）**：
   ① 首轮 C1（「截断的 design.md → `validate --strict` 判红」在 CLI 1.5.0 上不成立）是否走
   `[spec-review-amendment]` 修订 spec 措辞；
   ② `setup.sh` 曾从开发 checkout 跑，全局 skill 链接仍指向本 WIP checkout，
   合并后须在 `~/.skills/sdflow-skills` 重跑 `setup.sh` 还原；
   ③ CI 那条 openspec 泳道尚未在真 runner 上跑过；
   ④ fix2 §5-3：`decision_hash` 覆盖面扩大后，定稿后手改「接受的边角」这类非决策小节
   也会被 C.1 判 4 拦下问人 —— 判定为正确行为（定稿即冻结），若要放行需回设计层重定范围，
   **MUST NOT 靠把 hash 改窄来实现**。
2. **fix1 §5-2 的 `task1-review-package.diff` 未爆弹已消失**（本轮核实，可从 Concerns 摘掉）：
   `ls` + `git status --short --ignored` 双验 —— 工作树里已无此文件、也不在 ignore 名单中。
   本轮 `git add -A` 后重跑 `-k "guard or reference or report or memo or gate"`
   共 **526 passed**，`test_downstream_reference_guard` 在内，绿。
3. **本轮暴露的一个方法论信号（供编排层判要不要推广）**：fix2 报告里那句
   「改名后当场判红（响亮，不是假绿）」是**未经变异实测的推断**，本轮当场证伪。
   凡在报告里写「这里不用守，因为改了会红」，**MUST 附一条真跑过的变异**——
   否则它就是下一轮复审要挖的恒真锚。
