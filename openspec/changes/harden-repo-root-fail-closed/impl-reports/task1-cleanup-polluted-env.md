# Task 1 — 清理污染环境，建立可信验证基线

**R-ID:** R4（测试套件不得在当前工作目录留下副作用）
**分支:** `feat/harden-repo-root-fail-closed` · **起始 HEAD:** c0bad01

## 做了什么

删除仓根下 4 棵以 scan JSON 字符串命名的垃圾目录树，并在删除前后留痕核验。
执行中定位到**污染的产生源**：它不是历史残留，而是**每次跑 pytest 都会被重新生成**——
根因正是本 change 要修的 `repo_root` 无校验信任 `git` stdout。详见「关键发现」。

## 证据

### ① 删除前列举（4 棵，0 个普通文件，0 个被 git 跟踪）

顶层条目（`os.listdir('.')` 中 `startswith('{')`），4 条，均为真实目录、非 symlink：

```
'{"bugs": [{"id": 7,    "module": "core", ... "file": "openspec'
'{"bugs": [{"id": [],   "module": "core", ... "file": "openspec'
'{"bugs": [{"id": null, "module": "core", ... "file": "openspec'
'{"bugs": [{"id": {},   "module": "core", ... "file": "openspec'
```

`os.walk` 全量统计：**每棵 5 个子目录、0 个普通文件；合计 20 子目录 / 0 文件**（纯空目录树）。

形态即 bug 签名：整段 scan JSON 被当路径，JSON 内的 `/` 成为目录分隔符，
完整路径 = `<payload>/openspec/issues`（payload 自身含
`"file": "openspec/issues/buglist/2026-01-01-buglist.md"`，故被切成 4 层）。

跟踪状态核验：

- `git ls-files | grep -c '^{'` → **0**（完全未跟踪，删除无版本历史损失）
- `git status --porcelain` → **空**（空目录树不进 git 索引）

### ② 删除

`shutil.rmtree`，删除前逐棵断言四道闸：cwd 确为仓根 · 目标数恰为 4 · 是目录且非 symlink ·
`realpath` 的父目录仍是仓根（防越界）· 树内无任何普通文件。全部通过后才删。
未用 shell glob，规避目录名中空格/引号/花括号/方括号的二次展开风险。

### ③ 删除后复核

- 同一条列举命令 → `count = 0`，**无输出** ✅
- `git status --porcelain` → 空，**无跟踪文件受影响** ✅

## pytest 全量结果

`/usr/bin/python3 -m pytest -q`（仓根跑）：

```
1753 passed, 3 skipped in 115.14s (0:01:55)
```

**0 failed。** 两点如实说明：

1. 仓根 `python3`（`~/.local/bin/python3`）**无 pytest 模块**；系统 `/usr/bin/python3`
   有 pytest 8.4.2，本次用它跑。
2. 工单预告的已知 order-dependent 失败用例
   `sdflow-init/tests/test_outside_voice.py::test_exec_claude_reverse_path_three_flags_golden`
   **本轮全量跑并未失败**（1753 全绿）。未做进一步归因——它是既有登记缺陷，不在本票范围。

## 🔴 关键发现：污染是每轮 pytest 主动再生的，根因即本 change 的靶心

跑完全量 pytest 后再查，**4 棵树原样重现**（`brace entries after full pytest run: 4`）。
即：单纯删除**不构成持久的可信基线**——下一次 `pytest` 就会再污染一遍。

### 定位链（逐层实证，非推断）

1. 隔离 cwd 复现：单跑 `sdflow-issues/tests/test_task4_rename_snapshot.py` → 该 cwd 下出现同样 4 棵树。
2. 二分到具体用例：
   - `test_validate_scan_envelope_rejects_non_string_id_with_controlled_diagnostic` → 0 棵
   - `test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes` → **4 棵**
3. 插桩 `os.makedirs` 抓栈，得到确定性调用链：

```
test_task4_rename_snapshot.py:171   issues_mod.main()
issues.py:2331                      with recorder_lock(args.root, command) ...
issues.py:200                       os.makedirs(os.path.dirname(path), exist_ok=True)
```

### 机制

`sdflow-issues/tests/test_task4_rename_snapshot.py:165` 把 `issues_mod.subprocess.run`
**整体**替换为返回 `Proc`（`Proc.stdout` = 那段坏 scan JSON）的 lambda。

而 `sdflow-issues/scripts/issues.py:1132` 的 `repo_root` 恰恰也走 `subprocess.run`：

```python
out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=start, ...)
return out.stdout.strip()          # ← 无任何校验，直接采信
```

⇒ `main()` 第 2324 行 `args.root = repo_root(args.root)` 拿回的不是仓根，而是**那段 scan JSON**；
紧接着 `recorder_lock` 就拿它 `makedirs`，于是 JSON 落成目录树。

**这正是本 change 的论点本身**：`repo_root` 无条件信任 `git` 的 stdout，不校验
「绝对路径 / 目录存在」——任何进到那个 stdout 的垃圾都会直接变成**文件系统写入根**。
测试里的 blanket mock 只是触发器；产线上同一份信任同样成立。

### 处理建议（本票未动手，理由如下）

**未修 `repo_root`** —— 该函数的 fail-closed 加固是 Task 2+ 的正题，在 Task 1 里抢修会与后续票撞车。
本票边界是「清理 + 建立基线 + 如实登记」。

预期：Task 2+ 给 `repo_root` 加上「绝对路径 + `isdir` + 祖先校验」的 fail-closed 后，
本污染**作为副产物一并消失**（坏 root 会在 `recorder_lock` 之前就被拒），届时
`test_reindex_cli_non_string_id_...` 会改为撞诊断而非 makedirs。
**Task 2+ 完成后建议复跑一次全量 pytest 并复查仓根 brace 条目数 = 0，作为 R4 的收口证据。**

## Concerns

1. **基线的时效性**：当前仓根干净，但**这是一个会被下一次 `pytest` 破坏的干净**。
   在 Task 2+ 落地前，任何在仓根跑完 pytest 的人都会重新看到这 4 棵树——
   不要误判为「Task 1 没做」或「又有新 bug」。
2. **测试自身的 mock 粒度过宽**（次要，非本票范围）：把整个 `subprocess.run` 替换掉，
   会连带劫持被测函数之外的所有子进程调用（此处即 `repo_root` 的 `git`）。
   即便 `repo_root` 加固后不再 makedirs，这个 mock 仍会让 `repo_root` 走进 fail-closed 分支。
   Task 2+ 改动该用例时需一并考虑（建议按 argv 分派、只拦 recorder scan 那一次调用）。
3. **pytest 解释器不唯一**：仓根默认 `python3` 无 pytest。若 CI/他人用默认 `python3`
   会直接 `No module named pytest`。本次以 `/usr/bin/python3` 为准。

## 验收对照

- [x] 仓根不再有以 `{` 开头的目录条目（复核 `count = 0`）
- [x] 删除动作在提交历史中可见（列举 → 删除 → 复核三步留痕，本报告随 commit 入库）
