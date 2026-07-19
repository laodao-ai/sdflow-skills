# Task 5 实现报告 — cwd 泄漏回归断言（全仓覆盖）

**R-ID**: R4（测试套件不得在当前工作目录留下副作用） · **tasks**: 3.1 / 3.2 / 3.3
**交付文件**: `conftest.py`（新增，仓根单一份） · `pytest.ini`（新增，仓根）

---

## 1. 🔴 关键发现：ADR-3 的覆盖机制单靠 conftest **不成立**

ADR-3 的理由第一条写：「pytest 沿**测试文件的祖先目录**收集 conftest ⇒ 仓根一份天然覆盖全部
12 个 skill，无需任何注册。」

**这一条在本仓的实际条件下是错的**，且错法恰好是隐形的：

pytest 的 conftest 收集**止于 `confcutdir`，而 `confcutdir` 默认 = `rootdir`**。本仓在本票之前
**没有任何 ini 文件**（无 `pytest.ini` / `pyproject.toml` / `tox.ini` / `setup.cfg`，也无 `setup.py`），
于是 `rootdir` 是**推断**出来的：

| 调用姿势 | 推断出的 rootdir | 仓根 conftest 是否被收集 |
|---|---|---|
| 仓根 cwd 下 `pytest hack/tests/...` | `/…/04-sdflow-skills` | ✅ 是 |
| **仓外干净目录**下 `pytest /abs/…/hack/tests/...` | **`/…/04-sdflow-skills/hack/tests`** | ❌ **否** |

实测（`pytest --version` 8.4.2 / Python 3.9.6）：

```
$ cd $(mktemp -d) && pytest /Users/…/04-sdflow-skills/hack/tests/test_zz_probe.py
rootdir: /Users/cheneyzhao/Documents/04-sdflow-skills/hack/tests      ← 塌缩了
```

**而「仓外干净目录跑」正是验收框 2 与 spec Scenario「干净目录跑任一套件」规定的姿势** ——
也就是说，只放 conftest 的话，**这个断言会在它唯一被要求生效的场景下静默失效**。

**这个洞差点被我自己放过**：我在落笔前先做了一个 conftest 收集探针，探针**通过了**。事后查明
是目录几何的巧合——探针的调用目录与被测目录同在 `scratchpad/` 下，公共祖先被抬到了 `spike/`
之上，rootdir 于是落在仓根之上。**探针绿 ≠ 机制成立**；真正证伪它的是验收框 3 的反向验证
（注入泄漏用例，11 个套件**全部 `1 passed`**，一个都没红）。这正是本票被反复强调
「只验证正向通过 = 没验证」的实证。

**修法**：新增仓根 `pytest.ini`（仅一个空的 `[pytest]` 段 + 说明注释），把 `rootdir` 钉死在仓根 ⇒
`confcutdir` 恒 = 仓根 ⇒ 仓根 conftest 在任何调用姿势下都被收集。
`conftest.py` 与 `pytest.ini` **是一套，缺一即失效**，两个文件的注释里各写了这层依赖。

> ⚠️ 这是对 design ADR-3「代价」段的**增量**：该段只提到「仓库首次出现根级 pytest 文件」是
> `conftest.py`，实际是**两个**根级文件。tasks 4.4 要改的 CLAUDE.md 那句话（「没有根级 pytest
> 配置」）因此更该改——它现在被证伪了两次，而且 `pytest.ini` 恰恰就是「根级 pytest **配置**」。
> 我未改四件套（本票禁止，会触发设计门失鲜），**留给设计门/后续票处理**。

## 2. fixture 的最终形态

实现为 **hook wrapper 而非 autouse fixture**：

| | 报告形态 | 摘要行 |
|---|---|---|
| autouse fixture（teardown 抛异常） | passed + teardown error | **`1 passed`** ← 泄漏被降级成脚注 |
| **hook wrapper 包 call 阶段** | **failed** | **`1 failed`** ← 归属就是那个用例 |

三个 wrapper：`pytest_runtest_setup`（前取基线）→ `pytest_runtest_call`（查一次，走 FAILED）→
`pytest_runtest_teardown`（再查一次，覆盖 fixture teardown 阶段）。基线在每次查完后推进到当前
状态，同一用例不重复报同一批条目。用 `@pytest.hookimpl(wrapper=True)`（新式）而非
`hookwrapper=True`（旧式）——旧式在 wrapper 内抛异常会带出 `PluggyTeardownRaisedWarning` 噪声，
且已被 pytest 标记弃用；CI 两条 workflow 均 `pip install pytest` 不钉版本，新式更耐升级。

**豁免清单显式枚举**（`_CWD_LEAK_EXEMPT`）：`.pytest_cache` · `__pycache__` · `.DS_Store` ·
`Thumbs.db` · `desktop.ini`。不靠「碰巧没生成」蒙混。

## 3. 契约边界（诚实声明：守得住什么 / 守不住什么）

措辞已按 D6 收窄为「**禁止在 cwd 新增顶层条目**」，**不宣称**覆盖 spec 原文的「一切落盘物」。

- ✅ **守得住**：用例 setup / call / teardown 三阶段中，快照目录的**顶层条目集**不得新增；
  新增即失败并报出**条目名 + 所在目录**。
- ❌ **守不住**：既存文件**内容**被改写；条目被**删除**；快照目录**子目录内部**的新增
  （只要顶层没冒出新名字）。这些面无确定性的通用判据，是合法的语义残余（基准 1）。
- ❌ **守不住**：用例 fork 出的**非阻塞**子进程在阶段边界之后才落盘。
  （前提已由 spec-review X2 实测：仓内子进程调用均为阻塞式 `subprocess.run`，`pytest-xdist` 未安装。）
- ⚠️ **主动让路**：用例**自身已失败**时不再报泄漏——否则会盖掉真正的失败原因。
  代价是「又失败又泄漏」的用例只报前者。已实测确认（见 4.3）。

配套纪律写进 conftest 文档串：用例内改工作目录 MUST 用 `monkeypatch.chdir`，禁裸 `os.chdir`（D6）。

**未在各 skill `tests/` 下复制任何副本**（ADR-3）。`sdflow-issues/tests/conftest.py`（Task 4 的
argv 分派工厂）**未被触碰**，cwd 断言也未塞进它。

## 4. 实测结果

先自己数了带 `tests/` 的目录：**10 个 skill + `hack` = 11 个套件**（票面写「12 个 skill」；
`sdflow-retro` 在 CLAUDE.md 里被列为带测试，实际 **无 `tests/` 目录**，故是 10 不是 12）。

### 4.1 覆盖面验证 · 无误报（验收框 2）

11 个套件**各自**在**独立的干净临时目录**跑（`mktemp -d`，`-p no:cacheprovider`）：

| skill | 结果 | 该临时目录残留 |
|---|---|---|
| hack | 37 passed | `[]` |
| sdflow-architecture | 108 passed | `[]` |
| sdflow-buglist | 202 passed, 2 skipped, 1 xfailed | `[]` |
| sdflow-devenv | 116 passed | `[]` |
| sdflow-done | 48 passed | `[]` |
| sdflow-implement | 61 passed | `[]` |
| sdflow-init | **1 failed**, 304 passed, 1 skipped | `[]` |
| sdflow-issues | 253 passed, 1 xfailed | `[]` |
| sdflow-maintain | 45 passed | `[]` |
| sdflow-ship | 164 passed | `[]` |
| sdflow-todolist | 108 passed, 1 xfailed | `[]` |

**误报数 = 0**。仓内不存在「合法往 cwd 写」的测试 ⇒ 无需为任何套件放宽 fixture。

`sdflow-init` 那条 failed = `test_outside_voice.py::test_exec_claude_reverse_path_three_flags_golden`，
**与本票无关，是 tasks 4.5 已登记的负载敏感用例**。把 `conftest.py` + `pytest.ini` 双双移走后
对照跑，结果逐字相同：

```
BASELINE(无本票改动): 1 failed, 50 passed in 10.94s   ← 同一条 FAILED
WITH(本票改动):       1 failed, 50 passed in 10.93s   ← 同一条 FAILED
```

### 4.2 反向验证 —— 输出一：**修 rootdir 之前**（只有 conftest，无 pytest.ini）

注入用例（在 cwd 建一目录 + 一文件），11 个套件各跑一遍：

```
hack                   | 1 passed |
sdflow-architecture    | 1 passed |
sdflow-buglist         | 1 passed |
…（11 行全部 1 passed，无一红，且无任何「新增条目」输出）
```

**全绿 = fixture 根本没被加载**。这就是 §1 那个洞的直接证据。

### 4.3 反向验证 —— 输出二：**修 rootdir 之后**（conftest + pytest.ini）

同一注入用例，11 个套件各跑一遍：

```
hack                   | 1 failed, 1 warning in 0.01s | 新增条目: SENTINEL_LEAK_DIR, SENTINEL_LEAK_FILE
sdflow-architecture    | 1 failed, 1 warning in 0.01s | 新增条目: SENTINEL_LEAK_DIR, SENTINEL_LEAK_FILE
sdflow-buglist         | 1 failed, 1 warning in 0.01s | 新增条目: SENTINEL_LEAK_DIR, SENTINEL_LEAK_FILE
sdflow-devenv          | 1 failed, 1 warning in 0.01s | 新增条目: SENTINEL_LEAK_DIR, SENTINEL_LEAK_FILE
sdflow-done            | 1 failed, 1 warning in 0.01s | 新增条目: SENTINEL_LEAK_DIR, SENTINEL_LEAK_FILE
sdflow-implement       | 1 failed, 1 warning in 0.01s | 新增条目: SENTINEL_LEAK_DIR, SENTINEL_LEAK_FILE
sdflow-init            | 1 failed, 1 warning in 0.01s | 新增条目: SENTINEL_LEAK_DIR, SENTINEL_LEAK_FILE
sdflow-issues          | 1 failed, 1 warning in 0.01s | 新增条目: SENTINEL_LEAK_DIR, SENTINEL_LEAK_FILE
sdflow-maintain        | 1 failed, 1 warning in 0.01s | 新增条目: SENTINEL_LEAK_DIR, SENTINEL_LEAK_FILE
sdflow-ship            | 1 failed, 1 warning in 0.01s | 新增条目: SENTINEL_LEAK_DIR, SENTINEL_LEAK_FILE
sdflow-todolist        | 1 failed, 1 warning in 0.01s | 新增条目: SENTINEL_LEAK_DIR, SENTINEL_LEAK_FILE
```

（上表的 `1 warning` 是旧式 `hookwrapper=True` 的 `PluggyTeardownRaisedWarning`；随后改用新式
`wrapper=True` 已消除，见 4.4 的输出里已无 warning。）

完整消息形态（`hack` 一例的原文）：

```
E           AssertionError: 测试用例在工作目录留下了新增顶层条目（一切落盘物应位于 tmp_path 等 pytest 托管路径下）:
E             工作目录: /private/var/folders/xl/…/T/tmp.W0R8kVTj55
E             新增条目: SENTINEL_LEAK_DIR, SENTINEL_LEAK_FILE
```

### 4.4 反向验证 —— 四态矩阵（新式 wrapper，无 warning）

一次跑五个探针用例，验证各阶段归属与「不盖掉真失败」：

```
E             新增条目: TEARDOWN_LEAK          ← fixture teardown 阶段泄漏 → error
E             新增条目: SETUP_LEAK             ← fixture setup 阶段泄漏   → failed
E             新增条目: BODY_LEAK              ← 用例体内泄漏             → failed
>   def test_genuine_failure_not_masked(): assert 1 == 2, "REAL_REASON"
E   AssertionError: REAL_REASON                ← 真失败未被泄漏断言盖掉
3 failed, 2 passed, 1 error in 0.02s           ← 干净对照用例(tmp_path)正常 passed
```

### 4.5 变异确认：两个文件**各自**都是承重的（PV 规则 5）

同一个注入泄漏用例，逐个移走再跑：

```
=== 变异: 移走 conftest.py（pytest.ini 在位）===   1 passed in 0.00s   ← 变绿
=== 变异: 移走 pytest.ini（conftest.py 在位）===   1 passed in 0.00s   ← 变绿
=== 两者都恢复 ===                                 1 failed in 0.01s   ← 变红
```

⇒ 「删掉它就变红」双向成立，且证明 `pytest.ini` 不是可有可无的装饰。

### 4.6 全套件（仓根）

```
1871 passed, 3 skipped, 3 xfailed in 115.39s (0:01:55)
```

**与基线逐项相等**：1871 passed / **0 failed** / 3 skipped / **3 xfailed**（Task 3 的 R2 锚原样保留）。
`find . -maxdepth 1 -name '{*'` 无输出。

## 5. Concerns

1. **四件套需要一次修订，本票无权改**（禁止碰 proposal/design/tasks/specs）：
   - **ADR-3 的机制表述失准**：「仓根一份天然覆盖」漏了 `confcutdir = rootdir` 这一前置条件，
     且其「代价」段只列了 `conftest.py` 一个根级文件，实际是两个。
   - **tasks 4.4 的改法要跟着扩**：CLAUDE.md 那句「没有根级 pytest 配置」现在被 `pytest.ini`
     正面证伪（它就是根级 pytest **配置**），改后的措辞需同时提到两个文件及其耦合关系。
   - **spec R4 措辞**：D6 已决「收窄为禁止新增 cwd **顶层条目**」，但 spec 第 157-158 行仍写
     「测试产生的**一切落盘物** MUST 位于 tmp_path」——该收窄尚未落到 spec 正文。
     实现与 conftest 文档串已按收窄口径写，**spec 正文仍宣称了实现不覆盖的东西**。
2. **`rootdir` 全局变了**（此前随调用姿势漂移，现恒为仓根）。全套件与逐套件实测均无回归
   （§4.1 / §4.6），但这是一次全仓生效的行为改变，值得代码审单独看一眼。
3. **`wrapper=True` 需要 pytest ≥ 8**。本机 8.4.2、CI 两条 workflow 均不钉版本装最新 ⇒ 满足。
   若将来有人把 pytest 钉回 7.x，这三个 hook 会静默失效（pytest 7 不认 `wrapper=` 关键字，
   会报错而非静默——属于响亮失败，可接受）。
4. **`sdflow-retro` 无 `tests/` 目录**，但 CLAUDE.md「运行测试」段把它列进了「带脚本+测试的
   skill」名单。与本票无关的既存文档漂移，未处理，登记于此。
