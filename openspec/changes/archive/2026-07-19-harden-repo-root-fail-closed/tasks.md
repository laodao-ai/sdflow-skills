## 0. 清理污染环境（**MUST 先于一切实现与验证**）

- [x] 0.1 删除仓根 4 棵 JSON 命名的垃圾目录树（`find . -maxdepth 1 -name '{*'`，删前先列出确认）
      〔Success Metric 5；design Risks「自我掩盖」〕
- [x] 0.2 确认干净：`find . -maxdepth 1 -name '{*'` 无输出
      **为什么必须最先做**：`os.path.isdir` 按 cwd 解析相对路径，这 4 棵树会让坏值通过校验
      （ADR-2 实测：`isdir`-only 在仓根 4 passed、在空 cwd 4 failed）。在被污染的环境里得到的
      任何绿都不可信。

## 1. repo_root 分流校验（三份同步）

- [x] 1.1 三份 recorder 的 `repo_root` **同一提交内**同步重写为「起点校验 → 环境净化 →
      调 git → 形状校验 → 祖先校验 → marker 校验」六步（完整判据见 spec Requirement 1）。
      结构硬约束：**`try` 只包 `subprocess.run`**，只捕 `OSError`/`CalledProcessError` 走回落，
      `TimeoutExpired` 单独 `raise`；**一切校验与 `raise` 位于 try 之外**（否则新抛的
      `ValueError` 会被自己的 except 接住，fail-closed 归零）。禁 `except Exception`。
      诊断消息用 `ascii(value)[:N]`，禁字节截断；MUST NOT 在 helper 内 `sys.exit`；
      MUST NOT 写 stdout；**raise 消息 MUST 是通用文案，不含脚本名/`__file__`**
      （否则 AST 镜像守护当场变红，且破坏 T170 的抽取友好）。
      🔴 **env 剔除清单 MUST 写成 `repo_root` 函数体内的局部常量，MUST NOT 写成模块级常量**
      ——AST 三向比较只覆盖 roster 内的函数体，不比较模块级常量的**值**（实测：现存
      `RECORDER_PARTICIPANT_ALLOWLIST` 等三份值相同纯属人肉巧合、零机械守护）。
      写成模块级 = 新引入的东西直接落进既有安全网盲区（ADR-6）。
      🔴 **起点求法**：`start=None` → `os.getcwd()`（`FileNotFoundError` 转受控 `ValueError`）；
      显式传入 → `os.path.isdir(start)`。**MUST NOT 用 `os.path.isdir(".")`**（ADR-7）
      〔Req: 仓根解析证明根的身份；三份逐字一致；ADR-1/2/4/6〕
      - `sdflow-issues/scripts/issues.py:1132-1150`
      - `sdflow-buglist/scripts/buglist.py:581-590`
      - `sdflow-todolist/scripts/todolist.py:581-590`
- [x] 1.2 **单点解析**（ADR-5）：删除 16 处 `cmd_*` 内的 `root = repo_root(args.root)`，
      改为 `root = args.root`。断言手段 **MUST 用 `ast.walk` 统计 Call 节点**，
      **MUST NOT 用 grep**——grep 会把 `def repo_root(` 与 docstring 里的字面量一并算入
      （现存 docstring 就含 `` `root = repo_root(args.root)` `` 字样），得到假红或脆件偏移量。
      期望：Call 节点从 **19** 降到 **3**（三份 `main()` 各一）
      〔Req: 仓根在单次调用内只解析一次〕
- [x] 1.2b **同步更新 `repo_root` 的 docstring**：现文描述的是旧架构
      （「所有 cmd_* 现在统一先 `root = repo_root(args.root)` 再拼路径」），ADR-5 后失真。
      三份同步改（docstring 被 `_ast_no_doc` 剥离，不影响镜像守护，但**它是给人读的真相源**）
      〔ADR-5；DOC-1 正文即最终态〕
- [x] 1.2c **`--root` argparse 默认值改 `None`**（三份各一处：`issues.py:2265` /
      `buglist.py:1554` / `todolist.py:1527`），区分「未指定→`os.getcwd()` 探测」与
      「显式指定→`isdir` 校验」
      〔Req: Scenario「进程当前工作目录在运行期被删除」；ADR-7〕
- [x] 1.3 三份各加**形状校验负例**：git rc=0 但 stdout 为「非绝对路径 / 绝对但不存在 /
      空串 / 纯空白 / 末尾含空格致截短后命中另一目录 / 多行」时抛 `ValueError`，
      **且断言该值对应路径未被创建**。用 `tmp_path` 构造真实路径，
      MUST NOT mock `os.path.isabs`/`isdir`/`realpath`——mock 掉判据本身等于没测
      〔Req: 仓根解析证明根的身份〕
- [x] 1.3b **cwd 不变性双态实测**（恢复被返修弱化掉的验证方式）：「坏值恰好命中 cwd 下既存目录」
      这一用例 MUST **在仓内 cwd 与仓外 cwd 各跑一次，断言结果一致**。
      理由：spec Scenario 明写「该行为与进程的当前工作目录无关」，而这条断言唯一可信的验证手段
      就是双态对照跑——与 Task 0「污染环境里得到的绿不可信」同一纪律，标准须统一
      〔Req: Scenario「坏值恰好匹配 cwd 下的既存目录」〕
- [x] 1.3c **cwd 被删除负例**：进程 cwd 在调用前被外部删除后调 `repo_root()`（未指定 root），
      断言得到受控 `ValueError`、CLI 层 exit 2、stderr **不含 `Traceback`**。
      实测依据：`os.path.isdir(".")` 此时仍返回 `True`，而 `os.getcwd()`/`abspath(".")` 抛
      `FileNotFoundError`
      〔Req: Scenario「进程当前工作目录在运行期被删除」；ADR-7〕
- [x] 1.4 🔴 **`core.worktree` 回归测试（主防线用例，三份各一）**：真建一个仓，
      `git config core.worktree <仓外目录>`，**清空所有 `GIT_*` 环境变量**后调 `repo_root`——
      MUST 抛 `ValueError`，且那个仓外目录下 MUST NOT 出现任何 `openspec/`。
      **这条测试是祖先校验存在的唯一证明**：删掉祖先校验它必须变红（实现后跑一次变异确认）
      〔Req: Scenario「core.worktree 在 .git/config 中重定向工作树」；ADR-2〕
- [x] 1.5 **环境重定向测试**：设 `GIT_DIR`+`GIT_WORK_TREE` 指向另一仓 → 环境净化后正常返回
      真实根；再单独验证「即使不净化，祖先校验也拦得住」（证明两层防御各自独立有效）
      〔Req: Scenario「GIT_DIR / GIT_WORK_TREE 环境变量重定向」；ADR-6〕
- [x] 1.6 **边缘场景正向回归**：linked worktree（`.git` 是文件）、submodule（同）、
      symlink 起点、子目录起点 → 均正常返回；非 git 仓库 / bare repo / `.git/` 目录内 →
      回落 `abspath(start)`，CLI 仍 exit 0
      〔Req: Scenario「linked worktree 与 submodule」「git 命令失败」〕
      > 骨架可直接取自本轮 spec-review 的实测探针（10 场景全过，见报告「Q1 调研」段）
- [x] 1.7 **起点校验测试**：`--root` 指向不存在的路径 / 非目录文件 → 在调 git **之前**抛
      `ValueError`，且该路径 MUST NOT 被创建
      〔Req: Scenario「起点不是既存目录」〕
- [x] 1.8 **超时测试**：注入一个不返回的 fake git（PATH 注入 `sleep` 包装），确认
      `TimeoutExpired` → `ValueError` → exit 2，**MUST NOT 回落**
      〔Req: Scenario「git 探测超时」；ADR-1〕
- [x] 1.9 **CLI 级调用点契约测试（真跑，三份各一）**：以子进程真跑
      `python <script> --root <不存在的路径> <cmd>`，断言 `exit == 2` 且 stderr **不含**
      `Traceback` 且含诊断关键字。MUST NOT 用 AST/源码扫描判断「调用点是否在 try 内」——
      那是语法结构问题，手搓判断会掉进补丁循环（基准 5）；让 Python 自己回答
      〔Req: Scenario「抛出点在调用方的异常出口内」；ADR-4〕
      > 注意：**坏 `--root` 现在能触发目标分支了**（起点校验先于 git 调用），
      > 不再需要 fake git —— 这是把「起点校验」提到 git 之前的附带收益
- [x] 1.10 跑 determinism-guards 的 recorder 镜像一致性测试，确认 `repo_root` 三向 AST 等价仍绿
      〔Req: fail-closed 校验在三份 recorder 间逐字一致〕
- [ ] 1.11 **跨进程二次解析的兜底锚定测试**：构造「父进程持锁 → 子进程重解析得到不同根」，
      断言子进程以 `RecorderLockError` 响亮失败而非静默写入。
      **这条锚定的是一个隐含依赖**——ADR-5 的「单次解析」边界是进程，跨进程风险靠
      `validate_recorder_participant` 的 path/token 绑定兜底；无此测试，将来「简化」该校验
      会让跨进程静默写错目录无声回归
      〔Req: Scenario「子进程解析出不同的根时响亮失败」；ADR-5〕
      🔴 **保持未勾（诚实盘面）**：测试**写了且是活锚**（`xfail(strict=True)` + 独立的、刻意不带
      xfail 的前提核验用例，前提一烂当场判红），但**被锚的那条 MUST 当前不成立**——`recorder_lock`
      捕到 `RecorderLockError` 后回落 owner 模式，根分裂的子进程在外层根静默 `makedirs` + rc=0。
      **勾了就是把「未达成」记成「已完成」**。已登记 **B15**（P1，含修法与 6 个生产 spawn 站点
      影响面）；修法触 lock spec ⇒ 属设计门议题，不在本 change 内 fold。

## 2. 假绿测试修复

- [x] 2.1 修 `sdflow-issues/tests/test_task4_rename_snapshot.py:149`
      `test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes`：
      让 root 解析不受 monkeypatch 全局 `subprocess.run` 污染（mock 收窄到 `_scan_pool` 的
      调用点，或让 mock 对 `git rev-parse` 透传真实行为），使 reindex 真正作用于 `tmp_path`
      〔Req: 坏 root 下的 reindex 不得静默通过派生字节校验〕
- [x] 2.2 **变异验证**：故意让 reindex 向 `tmp_path` 的 `INDEX.md`/`batches.md` 写入，确认该
      测试**变红**；恢复后确认变绿。当前它对该变异恒绿，正是假绿判据
      〔Req: 坏 root 下的 reindex 不得静默通过派生字节校验，Scenario「变异验证——写入即变红」；Success Metric 2〕
- [x] 2.3 补齐该用例的完整断言集：exit=2 + **stderr 含 `scan item[0].id`** + 派生字节不变
      + **cwd 无新增条目**。MUST NOT 仅凭 exit 2 判定通过——坏 root 与坏 scan id 都产生 exit 2
      〔Req: Scenario「坏 scan 输出被受控拒绝且不误伤派生字节」「拒绝理由必须可区分」〕
- [x] 2.4 若 2.1 修复后暴露此前从未执行过的 reindex 分支失败 → **当场 fold 修掉**，不 defer
      〔design Risks「修完假绿测试后覆盖仍不足」〕

## 3. cwd 泄漏回归断言

- [x] 3.1 新建**仓根单一份** `conftest.py`：autouse fixture 比对每个用例运行前后的 cwd 条目集，
      新增条目即失败并报出条目名（`.pytest_cache` 等 pytest 自身产物除外）。
      MUST NOT 在各 skill 的 `tests/` 下复制副本（ADR-3：会构成第四组无守护镜像）
      〔Req: 测试套件不得在当前工作目录留下副作用；ADR-3〕
- [x] 3.2 覆盖面验证：12 个 skill + hack 各自在干净临时目录跑一遍，确认 fixture 全部生效
      且**无误报**（实测基线：本 change 前均 0 残留）
      〔Req: Scenario「覆盖面为全仓而非仅 recorder」〕
      ⚠️ **实为 11 个套件**（10 skill + hack；`sdflow-retro` 无 `tests/`）——票面「12」沿用 ADR-3 的失准基线，见 CF-9e。
- [x] 3.3 反向验证 fixture 真的会红：临时插一个在 cwd 建目录的用例，确认被捕获并报出条目名
      〔Req: Scenario「泄漏被回归断言捕获」〕

## 4. 清理与收尾

- [x] 4.1 回归确认垃圾树未再生：实现全部完成后 `find . -maxdepth 1 -name '{*'` 仍无输出
      （Task 0 已删除；本条验证的是「修完之后不会重新长出来」）
      〔Success Metric 5〕
- [x] 4.2 验证锚：在干净临时目录跑 `pytest sdflow-issues/tests/`，确认条目数 = 0
      〔Req: 测试套件不得在当前工作目录留下副作用；Success Metric 3〕
- [x] 4.3 在 `CLAUDE.md` 的 `openspec/rules/` 段登记 `premise-verification.md` 的编号 + 路径
      指针（**只写编号 + 路径，MUST NOT 复制规则文本**——该段的既定约定）
      〔proposal P2〕
- [x] 4.4 同步 `CLAUDE.md` 的「运行测试」段：「没有根级 pytest 配置——测试各 skill 自包含」
      一句已被 Task 3.1 的根级 `conftest.py` 证伪，改为「测试各 skill 自包含在
      `<skill>/tests/`；仓根有唯一一份 `conftest.py`，只承载全仓通用的 cwd 副作用断言」
      〔ADR-3 代价；不改即为本变更自己制造的文档漂移〕
- [x] 4.5 记 buglist：`sdflow-init/tests/test_outside_voice.py::test_exec_claude_reverse_path_three_flags_golden`
      全量跑 FAILED / 单独跑 PASSED（order-dependent 或负载敏感），显式传 `change` 字段
      〔proposal Non-Goals〕
- [x] 4.6 **〔Q3 按推荐落，可在设计门覆盖〕Windows 泳道覆盖**：把 `repo_root` 的正向回归
      （真实 git 仓库下不抛异常）+ 至少一条负例，追加进 `windows-recorder-smoke.yml` 覆盖的
      测试文件。**依据**：该 workflow 的 `paths` 精确匹配本 change 改的三个目录，却只跑
      `test_task2_windows_local_fs_smoke.py`——该文件直传 `tmp_path` 给 `recorder_lock`，
      **绕开 `repo_root`**；主矩阵 `mechanical-gates.yml` 只有 ubuntu/macos ⇒ 新判据从未在
      Windows 真跑过。design Open Questions 的三条（`isabs("C:/…")`、`normcase`+`commonpath`
      在盘符/大小写/UNC 下的行为、`realpath` 对 SUBST）全部未实测
      〔design Open Questions；DX D2〕
      ⚠️ **用例已写并挂进泳道，但本机 macOS 全 skip、从未在真 Windows 跑过**——达成的是「覆盖已就位」，不是「已验证」。
- [x] 4.7 **〔Q4 按推荐落，可在设计门覆盖〕面治闭环**：全仓扫描 **MUST 不限扩展名**
      （`grep -rln "show-toplevel" --include="*.py" --include="*.sh"`，排除 `.git/`、`tests/`、
      `openspec/changes/`），**实测命中 8 处而非早期写的 4 处**——除三份 recorder + `init.py`
      + `ship_gate.py` 外，还有三个 shell 脚本：`assets/hack/resolve-models.sh`、
      `resolve-workflow.sh`、`outside-voice.sh`。逐条给出纳入/排除理由并写进 Non-Goals：
      前两者把 `$ROOT` 拼进只读路径（`cfg="$ROOT/openspec/config.yaml"`）可援引与 `init.py`
      同款豁免；**`outside-voice.sh` 把 `$repo_root` 传给 `codex exec -C … --add-dir …`，
      值域与「只读拼路径」不同，MUST 单独论证，不得套用模板**。
      ⚠️ 验证手段 MUST 是「重跑扫描」而非「核对与 Non-Goals 处数自洽」——后者只验内部自洽，
      验不了漏扫（本轮冷复审正是这样抓到 4→8 的）
      〔CEO E2/E3；冷复审镜 A finding 3.2；CLAUDE.md 基准 3〕
      ⚠️ 两点未闭：① shell 脚本的排除论证仍在 impl-report、**未回写 proposal Non-Goals**（四件套冻结所致，属 CF-9 回写批次）；② `maintain_scan.py::find_repo_root` 是同面第四份实现，**因不含 `show-toplevel` 关键词未被扫描口径命中** → **B18**。扫描口径按「实现手段」而非「所解决的问题」来定，必然漏。
- [x] 4.8 记 todo：`repo_root` 不限制 git stdout 读取量（`capture_output=True` 无界读入，
      坏 wrapper 吐超大输出可在校验前耗内存）——DoS 面而非正确性面，`timeout=30` 已限时间窗，
      改 `Popen`+定量读复杂度不成比例
      〔design Non-Goals；codex X10 后半〕
- [x] 4.9 全仓跑一遍 `pytest`，确认无回归

## 测试覆盖图（TG-18）

| code path | 测试类型 | 落点 | 对应 Requirement |
|---|---|---|---|
| **`core.worktree` on-disk 重定向** | 单元（**主防线**，删判据即红） | 三份各一 · **1.4** | 根身份 · core.worktree Scenario |
| `GIT_DIR`/`GIT_WORK_TREE` 重定向 | 单元（两层防御各自独立） | 1.5 | 根身份 · env Scenario |
| `repo_root` 形状负例（非绝对/不存在/空/空白/末尾空格/多行） | 单元（负例 ×6 值） | 三份各一 · 1.3 | 根身份（形状层） |
| 起点非既存目录（坏 `--root`） | 单元（调 git 前拦截） | 1.7 | 起点不是既存目录 |
| **进程 cwd 被删除**（`isdir(".")` 仍 True） | 单元（负例） | **1.3c** | cwd 在运行期被删除 |
| cwd 不变性（仓内/仓外双态） | 单元（**双态对照跑**） | **1.3b** | 坏值恰好匹配 cwd 既存目录 |
| **跨进程重解析 → RecorderLockError** | 集成（父子进程） | **1.11** | 子进程解析出不同根时响亮失败 |
| git 探测超时 | 单元（fake git 注入） | 1.8 | git 探测超时 |
| linked worktree / submodule（`.git` 是文件） | 单元（正向回归） | 1.6 | linked worktree 与 submodule |
| symlink 起点 / 子目录起点 | 单元（正向回归） | 1.6 | git 返回合法仓根 |
| 非 git 仓库 / bare repo / `.git/` 内 → 回落 | 单元 + CLI exit 0 | 1.6 | git 命令失败 |
| **`cmd_*` 内 `repo_root(` 出现 0 次** | 静态断言（**`ast.walk` Call 节点，非 grep**） | **1.2** | 仓根只解析一次 |
| `--root` 默认值为 `None` | 静态（三份各一处） | 1.2c | cwd 在运行期被删除 |
| 坏 root 经 CLI → exit 2 + stderr 非 traceback | 集成（CLI 真跑） | 1.9 | 抛出点在异常出口内 |
| 三份 `repo_root` AST 等价 | 一致性（既有） | determinism-guards · 1.10 | 三份逐字一致 |
| 单份漂移被拦截 | 一致性（**既有通用机制**） | `test_logic_drift_is_caught`（跨 change，非本次新增） | 三份逐字一致 · 负向 Scenario |
| `reindex` 坏 scan id → exit 2 + 派生字节不变 | 集成（CLI） | 2.1 / 2.3 | reindex 不得假绿 |
| `reindex` 写入 `tmp_path` → 测试必红 | **变异验证** | 2.2 | reindex 不得假绿 |
| 任意用例的 cwd 副作用 | autouse fixture | 3.1 / 3.2 | 测试套件无 cwd 副作用 |
| fixture 自身有效性 | 反向验证（故意泄漏） | 3.3 | 测试套件无 cwd 副作用 |

## 追溯核对

| Requirement | 覆盖任务 |
|---|---|
| 仓根解析证明根的身份（含形状/祖先/marker/起点/超时/cwd 删除） | 1.1, 1.2c, 1.3, 1.3b, 1.3c, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9 |
| 仓根在单次调用内只解析一次（边界=进程） | 1.2, 1.2b, 1.11 |
| fail-closed 校验在三份 recorder 间逐字一致 | 1.1, 1.10（负向见既有 `test_logic_drift_is_caught`） |
| 测试套件不得在当前工作目录留下副作用 | 0.1, 0.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2 |
| 坏 root 下的 reindex 不得静默通过派生字节校验 | 2.1, 2.2, 2.3, 2.4 |

无幽灵任务：4.3 锚 proposal P2；4.4 锚 ADR-3 的代价（根级 conftest 使 CLAUDE.md 现有表述失真）；
4.5 锚 proposal Non-Goals；4.6 为全局回归。均在 proposal/design 中有出处。
