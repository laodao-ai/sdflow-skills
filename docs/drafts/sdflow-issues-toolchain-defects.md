# sdflow issues 工具链缺陷报告（给 sdflow-skills 工具仓）

> **来源**：2026-07-14 在消费仓 `zhws_ops_api` 做 issues 台账规范化时，实战撞出的一组缺陷。
> 全部结论均已回读工具源码坐实，附 `文件:行号`。
>
> **涉及脚本**（三者互为镜像，多数缺陷同构存在于两个池）：
> - `sdflow-todolist/scripts/todolist.py`
> - `sdflow-buglist/scripts/buglist.py`
> - `sdflow-issues/scripts/issues.py`
>
> **提交者立场**：本报告只描述问题、给出证据与建议方向，**不预设实现**。修法请工具仓自行判断。

---

## 0. 先澄清一个**不是** bug 的东西（防止误修）

排查初期我曾判断「`issues.py` 的 open 板过滤与已闭合计数判据不一致，工具自相矛盾」——**这是错的，不要去"修"它**。

`issues.py:220-228` + `:256-257`：

```python
TERMINAL_STATUSES = {"bug": {"FIXED", "WONTFIX"}, "todo": {"DONE", "WONTDO"}}
def _is_terminal(item):
    return item.get("status") in TERMINAL_STATUSES.get(item.get("pool"), set())

open_items   = [it for it in items if not _is_terminal(it)]
closed_items = [it for it in items if     _is_terminal(it)]
```

同一判据、互补分割，**逻辑完全自洽**。已完成项被列进 open 板，是因为它们的状态列写的是
`**DONE**〔2026-06-22〕tsc 20→0（A 类 15 ProTable…）` 这种混写文本，`!= "DONE"` → 非终态。
工具严格按自己的规则办事，没错。

**错的是数据能变脏而工具不吭声** —— 这才是下面 A 的问题。

---

## A（根因 · 建议 P0）读取路径完全不校验状态词表

### 现象

状态列可以写成任何字符串，`scan` / `reindex` 一声不吭地接受，然后**静默失效**：
- `scan --status OPEN` 精确匹配，`挂账·5F` / `[确认保持挂起] OPEN（YAGNI…）` 一个都匹配不到
- `reindex` 的 open/closed 分割把非字面量一律算作 open

结果：**盘点数字是假的，但没有任何告警**。实测消费仓 INDEX 报 `open 60`，真实值 43，
其中 16 项是已完成但状态列混写的项；而 `scan --status OPEN` 只能返回 **2** 项（真实 25 项）——
即「还有哪些没做」这个最基本的问题，工具答不出来，且不自知。

### 证据

`STATUS_CODES` 校验**只存在于写入路径两处**：

| 位置 | 校验对象 |
|---|---|
| `todolist.py:345` / `buglist.py:377` | `add` 传入的 status |
| `todolist.py:443` / `buglist.py:459` | `set-status` 传入的**新值** |

读取路径（`todolist.py:583-615` 的 scan 一致性自检）查的是：

- 块有 ID 但缺总览表行（`:589`）
- 表↔块状态不一致（`:597`）
- **同文件内**重复 ID（`:613`）
- 行 arity 异常

**没有任何一项检查「状态列的值 ∈ STATUS_CODES」。**

更要命的是 `:597` 那条「表↔块不一致」天然抓不到本类问题：当表和块**双双写着同一个脏状态**
（如两边都是 `挂账·5F`）时，两者一致 → 不报。脏得越彻底越安静。

### 为什么脏数据必然进池

skill 文档明确鼓励「轻量项只记一行」，**人手写表格行是被设计允许的路径**——它绕过 `add`/`set-status`
的写入校验。既然这条路开着，读取侧就必须有对应的校验，否则脏数据永远无人发现。

### 建议方向

`scan` / `reindex` 的 problems 增加一类：状态列 ∉ 该池 `STATUS_CODES` → 报 problem
（含 file / id / 实际值）。一条校验即可，让脏状态**一进池就红**，而不是攒几个月后靠人考古。

---

## B（真 bug · 静默失败 · 建议 P0）跨文件重复 ID 时 `set-status` 改错文件，并报成功

### 现象

`--id T1 --month 2026-06` 明确指定了月份，命令 exit 0、输出 `{"id":"T1","old":"…","new":"DONE"}`，
**但 06 月文件里那行纹丝未动**——被改的是 05 月的同名 T1。

我实测时一次跑了 16 条 `set-status`，屏幕上 16 行全绿，实际有 2 条打在了错误的文件上。
若不是我事后逐行复核表格，这两条会被当成已完成悄悄放过。

### 证据

`todolist.py cmd_set_status`：

```python
path, lines, sec, rows = _find_row_file(root, args.id)   # ← 定位只看 id
...
hist = f"> {this_month(args.month)} 状态：{old} → {new}…"  # ← --month 只用在这里（历史行文本）
```

`_find_row_file`（`todolist.py`，`buglist.py` 有同名镜像）：

```python
for path in list_files(root):
    ...
    if item_id in rows:
        return path, lines, sec, rows   # ← first-match-wins，不看后面还有没有同 ID
_die(f"未找到 ID：{item_id}")
```

**`--month` 完全不参与定位**，只拼进历史行的月份文本。

### 双重陷阱

1. **参数名骗人**：`--month` 让调用者（人和 agent 都一样）合理地以为它能消歧。**存在但不起你以为的作用的参数，比没有这个参数更坏。**
2. **工具自己知道有重复，却不用**：`issues.py reindex` **能**检测跨文件重复 ID 并 WARNING（消费仓里 T1/T2 的重复警告已经喊了很久），但 `set-status` 的 `_find_row_file` 一个字都不查。
   `todolist.py:613` 的重复检测只覆盖**同文件内**。

### 建议方向

`_find_row_file` 必须**扫完所有文件**再决定：
- 命中 0 个 → 现有行为（`_die`）
- 命中 1 个 → 正常返回
- 命中 ≥2 个 → **fail-closed 拒绝执行**，报出所有命中文件，要求调用方用 `--month`/`--file` 消歧
  （若采纳 `--month` 消歧，则必须让它真正参与定位，而不是只写历史行）

**绝不能再 first-match-wins 之后报成功。**

---

## C（设计缺陷 · 静默丢数据 · 建议 P1）`set-status` 无条件覆盖状态列，抹掉其中的叙述

### 现象

历史文件里大量项把「状态 + 一大段完成/triage 说明」混写在状态列同一个单元格（实测最长 **739 字符**，
含 commit hash、决策理由、复核结论）。`set-status` 直接 `cells[4] = new`，**这些内容当场蒸发，无任何警告**。

我在消费仓不得不手工建立一条纪律：**先把叙述搬进详细块，再改状态**——顺序反了就丢数据。
这条纪律应该由工具强制，而不是靠操作者记得。

### 证据

`todolist.py cmd_set_status`：

```python
old = rows[args.id]["cells"][4]
cells = rows[args.id]["cells"]
cells[4] = new                       # ← 写前不看 old 是什么
lines[rows[args.id]["line"]] = "| " + " | ".join(cells) + " |\n"
```

`old` 只被用来拼历史行 `> {month} 状态：{old} → {new}`。若 old 是 739 字符的叙述，
它会被整段塞进历史行（本身也是问题：历史行被撑爆、可读性归零），而原单元格的信息则失去了结构化归宿。

### 建议方向

写盘前检查 `old` 是否 ∈ `STATUS_CODES`：
- 是 → 正常覆盖
- 否 → **fail-closed 拒绝**，提示「状态列含非状态码内容（前 N 字符…），请先将其移入详细块再重试」

配合 A 的读取校验，这类脏数据就无处遁形。

---

## D（格式债的制造机 · 建议 P1）老文件缺列，导致归属信息无处可放，只能塞状态列

### 现象

批次系统是后加的。早期文件是 5 列（`ID/模块/描述/类型/状态`），**没有批次列**。于是
「这项归属 phase-5 的 5F backlog」这个信息**没有合法归宿**，操作者只能塞进状态列 →
写出 `挂账·5F`、`未落实(订正假✅)·5F`、`OPEN·5C后续` 这类自造状态。

**这不是有人乱写，是格式逼出来的。** A 类脏数据的绝大部分源头在这。

### 证据（消费仓实测）

| 文件 | 列数 |
|---|---|
| `2026-05/06-todolist.md`、`2026-06-29/30-buglist.md` | **5** |
| `2026-07-01/02/03-buglist.md` | **7**（缺批次列） |
| `2026-07-todolist.md` 等新文件 | 8 ✅ |

`triage` 的 docstring 已经说了「旧格式行（无批次列）先补齐到 8 列再写」——**说明工具作者知道这个问题，
但只在 triage 的数据行上补，表头不补、其它命令不补**。表头仍是 5 列而数据行 8 列 → 表格渲染错位。

### 建议方向

任一写入命令（`add`/`set-status`/`triage`）遇到 < 8 列的文件时，**自动把整表升到 8 列**（表头 + 分隔行 + 全部数据行），
而不是只补当前操作的那一行。我在消费仓写的一次性升列脚本核心逻辑约 30 行，不复杂：
只处理「## 状态总览」到下一个 `## ` 之间的表格区（详细块里的 `| 属性 | 值 |` 表不能碰）。

---

## E（语义问题 · 需先定性 · 建议 P2）`triage` 强制 OPEN→PROPOSED，但「有批次」≠「有 change 认领」

### 现象

`triage` 赋批次时会把状态从 OPEN 推进到 **PROPOSED**（`todolist.py cmd_triage` docstring 与
`:523-524` 的 `open_untriaged` 推导）。而 PROPOSED 的定义是「**已被某 OpenSpec change 包入 scope**」。

消费仓有 18 项属于 product-model roadmap 的 **5F backlog**——它们有明确归属分组，但**至今没有任何
change 认领**（5F 是 roadmap 的挂账区，不是 change）。给它们赋批次就会被强推成 PROPOSED = **撒谎**。

我因此选择**不给它们赋批次**（留空 → 落进 INDEX「未分组」板），归属信息只好写进详细块注记。
这是被工具语义逼出来的妥协：**一个真实存在的分组，无法在工具里表达。**

### 更深的问题：文档定义与实践已经脱节

skill 文档说「批次 key = **清理 change** 名」。但消费仓 `batches.md` 里现存的 5 个批次：

```
fix-test-isolation-and-auth-security
fix-dict-code-lpad-truncation
fix-logs-partition-and-test-determinism
refactor-dynapi-error-routing
remove-auth-positions
```

**全部是「发现这些 issue 的那个 change」的名字，不是「将要修它们的清理 change」的名字。**
而且这 5 个批次全是 `PLANNED`、`优先级`/`计划` 全是 `<待填>`——从没有任何清理 change 真正认领过它们。

也就是说，实践中批次已经退化成了**「这批 issue 是哪来的」的分组标签**，而文档还在说它是
「谁会来修」的认领凭证。两者语义相反（一个朝后看 provenance，一个朝前看 ownership）。

### 建议方向

**先定性，再改代码**。两条路：

1. **批次 = 分组标签**（承认实践）：那 `triage` 不该动状态，赋批次与状态推进解耦；
   「谁来修」另用字段表达（或就靠 PROPOSED + 关联Change）。
2. **批次 = 清理 change 认领**（坚持文档）：那需要一个**独立的分组维度**来承载 5F 这类
   「有归属、无认领」的 backlog，否则这类项在工具里无法表达。

无论选哪条，现状（文档说 A、实践做 B、代码按 A 强推状态）都是要修的。

---

## 附：实战案例（这些缺陷凑在一起会怎样）

消费仓 `zhws_ops_api` 2026-07-14 的一次台账盘点：

1. INDEX 报 `open 60` → 决策者以为还有 60 件事没做（**真实 43**，其中 16 项早已完成）
2. 想用 `scan --status OPEN` 列出真实待办 → 只返回 **2** 项（真实 25 项）——工具答不出最基本的问题
3. 人工考古发现根因：状态列混写（因为 D：老文件没有批次列）
4. 规范化时必须自建纪律「先搬叙述进块、再改状态」（因为 C 会静默抹掉）
5. 批量 `set-status` 16 条全绿，实际 2 条打错文件（因为 B），靠逐行复核才发现
6. 全程无任何工具告警（因为 A）

**修完 A + B + C，第 1/2/4/5/6 步都不会发生；修 D 则第 3 步的根因消失。**

---

## 优先级建议（供工具仓参考）

| # | 问题 | 性质 | 建议 |
|---|---|---|---|
| **A** | 读取路径无状态词表校验 | 根因，脏数据静默失效 | **P0**，最便宜（一条 problem 检查） |
| **B** | 跨文件重复 ID 改错文件还报成功 | **静默失败**，且参数名骗人 | **P0** |
| **C** | set-status 无条件覆盖状态列 | 静默丢数据 | **P1**（fail-closed） |
| **D** | 老文件缺列 → 归属信息无处放 | 格式债制造机 | **P1**（写入命令自动升列） |
| **E** | triage 强制改状态 / 批次语义脱节 | 设计问题 | **P2**（先定性再动代码） |

三个脚本（todolist / buglist / issues）互为镜像，A/B/C 在两个池里同构存在，修的时候请一并处理。
