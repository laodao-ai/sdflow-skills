# Task 1 · fix 轮次 2 — 接缝复审 2 条发现的修补报告

**票**：Task 1（`sdflow-spec` skill 本体 + 两道机械门）
**输入**：接缝复审 2 条（1 Important / 1 Minor·同文件同族 —— **同源同族，一起面治**）
**基线**：`fc483a4`（fix 轮 1 收尾）
**分支**：`feat/add-sdflow-spec`

> 前两轮报告 `task1-skill-body.md` / `task1-skill-body-fix1.md` **未覆盖、未改动**。

---

## 0. 一览

| # | 级别 | 发现 | 状态 |
|---|---|---|---|
| G-1 | Important | `decision_hash` 命令与 fence-aware 的门**本轮分叉** ⇒ C.1 判 4 静默放行 | ✅ 修（hash 改零解析全正文 + 逐行变异用例钉恒等性） |
| G-2 | Minor·同族 | 守卫看不见同一文件内的第 N 处消费者（`re.search` 只看第一处） | ✅ 修（消灭可执行字面量 + 守卫改 `re.findall` 计数下限 + 全量重扫消费面） |

**共同根因**：fix 轮 1 把 `_section_body` 扩成 fence-aware，**派生判据没跟着改**——
典型「扩枚举不回改派生判据」。G-1 是**语义派生判据**（hash 的范围口径），
G-2 是**守卫的派生判据**（「一处一致」推不出「处处一致」）。

**本票门文件**：`17 passed → 19 passed`。**仓根全量**：`1 failed, 2652 passed`
（唯一残红 = 已知 baseline 宿主依赖，见 §3.1）。

---

## 1. G-1 [Important] `decision_hash` 与门的口径分叉

### 1.1 复现（先证伪，再落笔）

固定 fixture = 门**认可**的形态（`test_heading_inside_fenced_block_is_not_a_real_heading`
明确背书）：「拍板决策」节内贴 schema 模板（含 `## 承重约束` 字面量），**围栏之后**还有 D2。

修**前**，把围栏之后的 D2 改成相反的决策，跑 schema 文档里那条唯一算法：

```
E   assert 'eec647db128a' != 'eec647db128a'
```

⇒ hash 只覆盖到 ` ```markdown ` 那一行，**C.1 判 4 对 D2 是静默放行的**。
`hack/tests/test_decision_memo_gate.py:392` 同时证明改「承重约束」也不动 hash。

### 1.2 修法：**零解析**——hash = frontmatter 之外全文

`sdflow-spec/references/decision-memo-schema.md:56-73`，命令主体从「逐行 `startswith("## ")`
切段」换成：

```python
raw=open(sys.argv[1],encoding="utf-8").read()
body=re.sub(r"\A---\n.*?\n---\n","",raw,count=1,flags=re.DOTALL)
print(hashlib.sha256(body.strip().encode()).hexdigest()[:12])
```

**为什么不取复审给的 (a)/(b) 原样**（通则②：带推荐 + 依据 + 代价 + 备选）：

| 候选 | 依据 / 代价 | 判 |
|---|---|---|
| **(a) 命令复用 `_section_body`** | `_section_body` 住在 `hack/tests/`——**repo-only，不是 skill 的一部分**，`setup.sh` 不装它。而这条命令要在**消费项目**里跑（B.7④ 定稿 / C.1 判 4）。它进一步依赖 `sdflow-ship/scripts/ship_gate.py` 的 `FenceTracker`⇒ 从一条文档 bash 一行式跨两个 skill 目录取实现 | ❌ 消费项目里跑不起来 |
| **(b) 命令自己实现「节内全部可见行」** | 要在命令里手抄一份围栏追踪——`test_decision_memo_gate.py:32-38` 与 `ship_gate.py:568-572` **两处原文都写着 MUST NOT 手抄**（手抄口径只认 ` ``` `）。且立刻造出第三个漂移面 | ❌ 违反本仓 fence 单一源 |
| **(c)（采纳）frontmatter 之外全文，零解析** | **不切小节 ⇒ 没有可分叉的口径**：门认作正文的每一行都必然在覆盖内，恒等性是结构性的而非靠对齐维持。这正是 CLAUDE.md 基准 5 附录 A21 的同一手法（「digest 一律整文件原始字节，零解析零规范化」） | ✅ |

**排除 frontmatter 是必需的**：`decision_hash` 自己写在 frontmatter 里，算进去则写回即自毁
（判 4 恒红）。frontmatter 语法在本 schema 下**有界**（文件首行 `---`，到下一行 `---` 为止，
字段全是标量）⇒ 两行正则，符合基准 5 的「有界可手写」。

**代价（如实写进文档）**：定稿后手改**任何**小节都会 hash 不符。判定 = **不是误报**——
定稿之后纪要是冻结件（schema §4：增量落盘全在定稿之前；SKILL.md 里定稿后无任何写 memo 的路径，
`grep -n "decision-memo\|纪要" sdflow-spec/SKILL.md` 全量核过），要改就退回相位 B 重新定稿。
覆盖面是**扩大**不是缩小 ⇒ 不触通则③「砍窄」。

**同步改动的措辞**（同一片一致性面，一次扫全）：
- `decision-memo-schema.md:22` frontmatter 注释；
- `decision-memo-schema.md:83` §3 表「`decision_hash` 匹配」判据行；
- `sdflow-spec/SKILL.md:367-370` C.1 判 4。
- `SKILL.md:347-350`（B.7④）只说「用 §2 的那一条命令」，不含范围措辞 ⇒ 无需改。

**四件套未动**：`specs/spec-authoring/spec.md:297` 与 `design.md:116` 只写「决策 hash」，
不指定范围 ⇒ 本改动在 SA-13 的字面之内。

### 1.3 机械钉住（基准 1：有确定性信号 ⇒ MUST NOT 只写一句 SHOULD）

新增两条用例（`hack/tests/test_decision_memo_gate.py:283-395`）。
🔴 **两条都从 schema 文档里把那条 ```bash 命令抽出来真跑**（`_documented_hash_command()` /
`_decision_hash()`），**不在用例里手抄一份等价实现**——手抄 = 又一个漂移面，
且漂移方向恰好是「文档改了、用例还在给旧算法背书」。

| 用例 | 断言 |
|---|---|
| `test_decision_hash_covers_every_line_the_gate_calls_body` | 取 `_section_span(memo, REQUIRED_SECTIONS[0])`（门认的正文行区间），**逐行**定点变异，每一行都 MUST 让 hash 变；`checked >= 5` 防 fixture 太瘦导致锚接近恒真 |
| `test_decision_hash_is_deterministic_and_frontmatter_independent` | 三条反向锚：① 同一份文件两次算出同值；② 往 frontmatter 塞 `decision_hash: deadbeefcafe` 后 hash **不变**（自指坑）；③ 改「承重约束」正文 hash **变**（覆盖面已扩大） |

配套小重构：`_section_body` 拆出 `_section_span(text, heading) → (start, end)`
（`test_decision_memo_gate.py:93-124`）——逐行变异需要知道「门认的正文」到底是**哪几行**，
而不是一个拼好的字符串。`_section_body` 改为薄封装，判据本体零变化。

**TDD 红→绿实测**：先加用例 → `2 failed, 17 passed`（失败信息即 §1.1 那段）→ 改文档 → `19 passed`。

---

## 2. G-2 [Minor·同族] 守卫看不见同文件内的第 N 处消费者

### 2.1 全量重扫消费面（基准 3 面治：不加 `--include`）

```
$ grep -rn "## 拍板决策" .   # 与 "## 承重约束"，均排除 .git
```

带右界（`(?![^\s\`|])`）逐处归类：

| 位置 | 归类 | 处置 |
|---|---|---|
| `hack/tests/test_decision_memo_gate.py:59` `REQUIRED_SECTIONS` | **真相源** | — |
| `..._gate.py:_write_memo`（旧 :148） | fixture，**曾硬编码** | ✅ 改为直接解包 `REQUIRED_SECTIONS` ⇒ 跟着真相源走，不再是消费者 |
| `..._gate.py` 两条 inline 文本 fixture（`test_fenced_heading_neither_truncates_nor_relocates_the_section` / `test_heading_hidden_in_html_comment_block_is_red`） | `_section_body` 的行为样本 | 不纳入：改名后当场判红（**响亮**，不是假绿） |
| `sdflow-spec/SKILL.md:322`（B.4「当场追加写 `## 拍板决策`」）、`:365`（C.1 判 2） | **格式消费者 ×2**，同一文件 | ✅ 计数下限 `{拍板决策: 2, 承重约束: 1}` |
| `decision-memo-schema.md:31/36`（模板）、`:80/81`（§3 表）、`:95/96`（§4） | **格式消费者 ×3+3** | ✅ 计数下限 `{3, 3}` |
| ~~`decision-memo-schema.md:60` `lines.index("## 拍板决策")`~~ | **可执行字面量** | ✅ **随 G-1 整段消失**（新算法不切小节 ⇒ 命令里再无标题名） |
| `openspec/changes/add-sdflow-spec/impl-reports/*`、`*.diff`、评审报告 | 冻结的历史记录 | 不纳入 |

⇒ 复审点名的那处消费者（可执行字面量）**不是被守住，是被消灭**——比守更彻底：
G-1 的修法让它不再存在，∴ 「改名后运行时 `ValueError`」这条失效路径整条没了。

### 2.2 守卫本体：`re.search` → `re.findall` 计数下限

`MEMO_SECTION_CONSUMERS` 由 tuple 改为 `{path: {heading: 最少出现次数}}`
（`test_decision_memo_gate.py:49-66`），`test_schema_doc_and_gate_agree` 改判：

```python
hits = re.findall(re.escape(heading) + r"(?![^\s`|])", doc)
assert len(hits) >= minimum
```

- **语义是下限（`>=`）**：新增一处合法提及 ⇒ 计数上升，不红；漏改 / 删掉一处 ⇒ 红。
  取 `>=` 而非 `==` 是为了不让「加一句散文」变成误红；而**部分改名必然让新名计数低于下限**，
  正是要抓的那个失效模式。
- 右界判据（fix1 F-4 的子串坑修法）原样保留，两条判据缺一不可（用例 docstring 已写明理由）。
- 另加一条 `set(expected) == set(REQUIRED_SECTIONS)`：将来新增必填小节时，期望表漏补即红。

---

## 3. 非恒真锚：定点变异实测

⚠️ **全部变异在 `git worktree` 副本里做**（scratchpad，detached HEAD），主工作树零改动；
实测完 `git worktree remove --force`，`git worktree list` 已确认只剩主树。

| # | 变异 | 结果 | 说明 |
|---|---|---|---|
| N1 | schema 文档里的 hash 命令**整段回退**成 fix1 的逐行 `startswith` 口径 | **2 failed, 17 passed** | G-1 的两条锚都非恒真 |
| N2 | 命令改成 `body=raw`（把 frontmatter 也算进 hash） | **1 failed** — `..._frontmatter_independent` | 自指坑那条锚独立成立 |
| N3 | 改名 `## 拍板决策`→`## 拍板决策项`，改遍门 / SKILL.md / schema，**只漏 schema §4 一处** | **1 failed** — `test_schema_doc_and_gate_agree`（`2 = len([...])` < 下限 3） | G-2 的锚非恒真 |
| N3-old | **同一变异** + fix1 的「出现过就行」旧守卫 | **19 passed（假绿！）** | 复审所报失效模式的直接复现 —— 这就是本条修补的全部理由 |
| N4 | `_visible_flags` 恒返回 `True`（门失去围栏感） | **4 failed**，其中含 `..._covers_every_line...` | 证明 hash 覆盖面锚**真的挂在门的口径上**，不是自说自话 |
| N5 | 改掉 schema 文档里 `### \`decision_hash\` 的唯一算法` 标题（抽取锚失效） | **2 failed**（`:304` 断言，报「算法的单一源不见了」） | 「从文档抽命令」这条链路不会静默降级成「用例自带一份实现」 |
| 还原后 | — | **19 passed** | — |

---

## 4. 命令输出（实跑）

### 4.1 本票门文件

```
$ /usr/bin/python3 -m pytest hack/tests/test_decision_memo_gate.py -q
19 passed in 6.78s        （fix1 收尾为 17 passed）
```

### 4.2 仓根全量 pytest

```
$ /usr/bin/python3 -m pytest -q
FAILED sdflow-init/tests/test_outside_voice_job.py::test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret
1 failed, 2652 passed, 10 skipped, 3 xfailed in 325.18s (0:05:25)
```

唯一残红 = 编排层已告知的 baseline 宿主依赖（`claude --bg --exec` 探针；失败点是**对照组**
断言 `CONTROL_TRANSCRIPT_CANARY_A1B2 not in ''`，即本机根本没有 `claude logs` 输出）
⇒ 与本票无关，未当回归处理。

### 4.3 收尾

```
$ /usr/bin/python3 hack/sync_principles.py --check
[sync_principles] ✅ 19 个投放面全部与真相源一致

$ wc -l sdflow-spec/SKILL.md                        → 528（上限 600，本轮 ±0）
$ wc -l sdflow-spec/references/decision-memo-schema.md → 110（+1）

$ git diff --stat
 hack/tests/test_decision_memo_gate.py          | 193 +++++++++++++++++----
 sdflow-spec/SKILL.md                           |   4 +-
 sdflow-spec/references/decision-memo-schema.md |  29 ++--
```

---

## 5. Concerns（交编排层）

1. **前两轮的 Concerns 未变，逐条仍悬**：① 首轮 C1（「截断的 design.md → `validate --strict`
   判红」在 CLI 1.5.0 上不成立）是否走 `[spec-review-amendment]` 修订 spec 措辞；
   ③ `setup.sh` 曾从开发 checkout 跑，全局 skill 链接仍指向本 WIP checkout，合并后须在
   `~/.skills/sdflow-skills` 重跑 `setup.sh` 还原；④ CI 那条 openspec 泳道尚未在真 runner 上跑过。
   **本轮均未处置**（不在本票范围）。
2. **`task1-review-package.diff` 仍是颗未爆弹**（fix1 §5-2）：工作树里 untracked，正文含已删除
   skill 的旧名字面 ⇒ **谁 `git add` 谁把 `test_downstream_reference_guard` 打红**。非本票产物，未动。
3. **`decision_hash` 覆盖面扩大的一个可感知后果**：定稿后若有人手改「接受的边角」这类**非决策**
   小节，C.1 判 4 也会拦下来问人。判定为**正确行为**（定稿即冻结），但它是相对 fix1 的**行为变化**，
   若编排层认为该放行非决策小节的编辑，需回到设计层重定范围——**MUST NOT** 靠把 hash 改窄来实现
   （那会把 G-1 原样放回来）。
