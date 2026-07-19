# Task 6 — 面治闭环与收尾

**Ticket**：Task 6（Blocked-by 2,3,4,5）· **R-ID**：R1 / R4（收敛验证）
**约束**：未碰 `scripts/`（三份 AST 镜像保持相等）；未碰 `proposal.md` / `design.md` / `tasks.md` / `specs/`。

---

## 1. 面治扫描（tasks 4.7）—— 实测重跑，非核对自洽

**执行的命令（不限扩展名，非 `--include` 版）**：

```
grep -rln "show-toplevel" . | grep -v "^./.git/" | grep -v "/tests/" | grep -v "^./openspec/changes/"
```

**为什么用不限扩展名版**：tasks 4.7 写的 `--include="*.py" --include="*.sh"` 本身就是一个前提
（「可执行面只有 py 和 sh」）。不限扩展名跑一遍才验得了它。

**结果**：命中 **8 处可执行面**（与 tasks 4.7 实测的 8 处一致），另有 **6 处 `SKILL.md` + 2 处
`openspec/specs/*/spec.md` + 1 处 `docs/superpowers/plans/*.md`** 的散文提及。散文提及**零可执行性**
（无解析、无路径拼接、无进程调用），不构成面。⇒ **不限扩展名相对 `--include` 版无新增可执行面**，
tasks 4.7 的口径经此确认成立（此前是未验证的前提）。

### 逐处裁定

| # | 站点 | 裁定 | 理由（安全论证） |
|---|---|---|---|
| 1 | `sdflow-buglist/scripts/buglist.py` | **纳入**（已改） | recorder，`root` 直通 `makedirs` |
| 2 | `sdflow-todolist/scripts/todolist.py` | **纳入**（已改） | 同上 |
| 3 | `sdflow-issues/scripts/issues.py` | **纳入**（已改） | 同上 |
| 4 | `sdflow-init/scripts/init.py:543 _git_root_or_dot` | **排除** | **sink 只读**：唯一消费者 `init.py:883` → `cmd_config_lint(root)` → `lint_config(root)`，该函数对 `<root>/openspec/config.yaml` 只做 `open(..., encoding="utf-8").read()`（`init.py:472-481`），全路径**无任何目录创建/写入**。坏值的最坏后果 = 读到别的仓的 config 并报 lint reason，**不落盘**。另有前置兜底：`except (OSError, CalledProcessError) → "."`，且 `top` 为空时也回落 `"."` ⇒ 不会把空串当根拼路径。 |
| 5 | `sdflow-ship/scripts/ship_gate.py:836-837` | **排除** | **sink 只读**：全文件 `grep -nE 'mkdir\|makedirs\|open\(\|write_text\|write_bytes\|shutil\.\|os\.remove\|unlink\|rmtree'` **零命中**（实测）——它是自称「只读盘面判官」的判官脚本，`root` 只用于拼读路径与 `emit()` 到 stdout。坏值最坏后果 = 对错误的 change 目录做判定并给出错误 verdict（可观测、不静默落盘）。 |
| 6 | `sdflow-init/assets/hack/resolve-workflow.sh:26` | **排除** | **无目录创建**：`$ROOT` 唯一 sink 是 `LOCAL="$ROOT/openspec/workflow"`（:38），随后全是 `[ -f ]` / `[ -d ]` / `ls -A` 只读探测。**有前置兜底**：`git … \|\| pwd \|\| true`，空值时 :27-30 显式 `exit 64` 并要求 `--root`（cwd 已删场景 fail-closed，不静默取 `.`）。 |
| 7 | `sdflow-init/assets/hack/resolve-models.sh:42` | **排除** | **无目录创建**：`$ROOT` 两个 sink——`resolve-workflow.sh --root "$ROOT"`（:68，转交给 #6，性质同上）与 `cfg="$ROOT/openspec/config.yaml"`（:111，只读）。写操作零命中。空值兜底为 `ROOT="."`（:43）。 |
| 8 | `sdflow-init/assets/hack/outside-voice.sh:587` | **排除，但论证独立** | 见下（**MUST NOT 套用 #4-#7 的「只读拼路径」模板**） |

### #8 `outside-voice.sh` 的单独论证（值域与 #4-#7 不同）

`repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || repo_root="$PWD"`（:587，**无任何校验**），
两个 sink 都不是「拼路径读文件」，而是**把该值交给一个外部 agent 进程当工作域**：

- **codex 路径**（:639）：`codex exec -C "$repo_root" -s read-only --ephemeral`
  `-C` 设的是子进程 cwd。**写边界由 `-s read-only` 提供，与 `$repo_root` 的取值正交**——
  沙箱是 read-only，`-C` 指到哪里都写不进去。voice 的一切产物落 `mktemp -d` 出来的 `$workdir`
  （:588），**从不写 `$repo_root`**。
- **claude 路径**（:659）：`--tools "Read,Grep,Glob" --strict-mcp-config --add-dir "$repo_root" --settings <读围栏>`
  该文件 :656-657 的实测注释明确记载：**`--add-dir` 是增量授权提示、不是访问围栏**（Read 无它也读全盘）；
  真正的写边界是 `--tools` 只给 `Read,Grep,Glob`（**无 Write / Bash / WebFetch**），真正的读边界是
  `--settings` 的 `permissions.deny`。**两条边界都不以 `$repo_root` 为参数** ⇒ 坏值改不动它们。

**⇒ 排除理由（安全论证，非程序性）**：本站点的两个 sink 在**工具权限层**就是只写不进 / 只读受限的，
写能力不由 `$repo_root` 的正确性决定。recorder 的危险来自「坏值 → `makedirs` → 数据写进错误的树」，
该因果链在此**结构上不存在**。

**诚实的残余（MUST 一并登记，不得当成"已闭环"）**：

1. 该值**确实未经校验**（无形状/祖先/marker 校验）。坏值的后果类别是
   **evidence 相关性失效**——outside voice 在错误的树上取证 ⇒ 该次 voice efficacy 趋零，
   属**质量面**、非**数据完整性面**。可观测（voice 输出明显不着边际），非静默数据损坏。
2. 回落 `"$PWD"` 与 recorder 的 `abspath(start)` 同类，恒为绝对路径，不引入新面。
3. `-C` 指向的目录若在调用瞬间消失 ⇒ `codex exec` 自身非零退出 ⇒ 走既有失败通道，非安全问题。

> 🔴 **须在设计门回写 `proposal.md` Non-Goals**：以上 #4–#8 五处的裁定与理由（尤其 #8 的独立论证）
> 目前只存在于本报告。本票**不能改 proposal**（ship gate 设计门失鲜）。

---

## 2. Windows 泳道（tasks 4.6 / CF-6）

**先查了 workflow 再动手**：`.github/workflows/windows-recorder-smoke.yml` 的 `paths` 精确匹配
`sdflow-buglist/**`、`sdflow-todolist/**`、`sdflow-issues/**`、`sdflow-init/scripts/init.py`，
但 `run:` 只跑**一个文件**：`sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py -W error`。
⇒ 新用例**必须落进这个文件**才会在 Windows 真跑。已落入该文件（+5 个用例）。

| 用例 | 覆盖 | 类型 |
|---|---|---|
| `test_windows_repo_root_positive_regression` | 真实 git 仓库下不抛异常；仓根起点 / 子目录起点 / **盘符大小写翻转**起点三种姿势解析到同一根 | 正向回归（design Open Questions 前两问的实测答案：`isabs("C:\…")`、`normcase`+`commonpath`） |
| `test_windows_repo_root_rejects_nonexistent_start` | 起点不存在 ⇒ 调 git 前受控 `ValueError` + 三段式消息 + **该路径未被创建** | 负例① |
| `test_windows_repo_root_rejects_core_worktree_redirect` | `core.worktree` on-disk 重定向 ⇒ 祖先校验拦下；目标目录零产物。含**前提核验**（先真跑 git 确认重定向确实生效，不假设） | 负例②（主防线） |
| `test_windows_commonpath_cross_drive_raises_without_recorder_format` | **CF-6 判据层，无条件跑**：`os.path.commonpath` 跨盘符自抛 `ValueError`，消息**不带** `ERROR:/cause:/fix:` 三段式 | 负例③（可观测性降级钉桩） |
| `test_windows_repo_root_cross_drive_redirect_is_fail_closed` | **CF-6 端到端**：`core.worktree` 指向另一盘符 ⇒ 仍 `ValueError` fail-closed、目标零产物 | 负例④（需第二个可写盘符，否则诚实 skip） |

### 🔴 诚实的验证边界（MUST NOT 读成"已验证"）

- 本机是 **macOS**。这 5 个用例在本地 **`7 skipped`**（模块级 `skipif(sys.platform != "win32")`）。
  **我没有在 Windows 上跑过任何一条。** 已验证的只有：**收集通过**（pytest 成功 import 该模块
  ⇒ 语法与 import 正确）+ 三条平台中立的构造配方（`_init_repo` / `core.worktree` 重定向 /
  前提核验探针）**已在 macOS 上由 `test_repo_root_identity_buglist.py` 的同款用例证明可跑通**。
- **只能由 CI 的 Windows runner 验证的部分**：① `isabs`/`normcase`/`realpath` 对盘符路径的真实行为；
  ② `git init` + `core.worktree` 在 Git for Windows 下是否同样重定向 toplevel（用例内已写**前提核验断言**，
  若前提不成立会以「前提不成立」文案红，不会假绿）；③ 跨盘符端到端路径。
- **CF-6 的处理方式**：端到端用例需要 runner 上真有第二个可写盘符，**没有就 skip**——但同一事实
  由**无条件运行**的判据层用例（`commonpath` 跨盘符）钉住，**不存在「全 skip ⇒ 零覆盖」的窗口**。
  这条按 PV 规则 1 办：**不用「理论上大概率能过」结案**，而是把不可构造的部分降到可无条件构造的判据层。
- **结论口径**：Windows 覆盖**已写好、未验证**。下一次 push 触发 `windows-recorder-smoke.yml` 才产生证据。
  在那之前 MUST NOT 声称 Windows 泳道已通过。

### CF-6 的降级结论（实现层含义，不改代码）

跨盘符时步骤⑤抛的是 **stdlib 的** `ValueError` ⇒ `main()` 的 `except ValueError` 照样接住
（`buglist.py:1714-1716`：打 stderr + `SystemExit(2)`）⇒ **fail-closed 成立、无 traceback**；
但消息不带 recorder 三段式 ⇒ **可观测性降级**。ADR-2 的 written decision 是 `commonpath`，
备选 `PurePath.is_relative_to`（跨盘符返回 `False` 而非抛）是**对 written decision 的偏离**，
**MUST 走设计门，不在本票就地改**。已用测试把当前行为钉死：将来若换实现，该用例当场变红。

---

## 3. `CLAUDE.md` 两处改动

- **4.3（proposal P2）**：在 `openspec/rules/` 段 `DOC-1` 条目下方新增
  `premise-verification.md` 指针。只写路径 + 一句适用面，**未复制规则文本**。
  🔴 **如实报告**：该文件**没有文档级编号**——H1 是「# 前提验证规则（写断言之前先落地）」，
  对照 `doc-authoring.md:1` 的「# DOC-1：…」自带前缀；全仓 `grep "PV-"` 除本 change 外零命中
  （与 `gstack-review.md:70` D1 的判断一致）。**故未自造编号**，登记写作
  「（无文档级编号，引用写路径 + 内部「规则 N」）」。**建议设计门拍板**是否给它补一个
  `PV-1` 式 H1 前缀——那是改 `openspec/rules/` 的独立动作，不属本票。
- **4.4（CF-9d）**：把「没有根级 pytest 配置——测试各 skill **自包含**」改为**两文件**表述：
  `conftest.py`（断言本体）+ `pytest.ini`（把 rootdir 钉在仓根，否则 conftest 收集止于塌缩后的
  rootdir、断言静默失效），并写明**缺一即失效**、MUST NOT 塞其他配置。

---

## 4. defer 登记（均显式带 `change` 字段，脚本回执确认）

先跑了两池 `scan` 确认无重复（B15 是「跨进程根分裂」、T181 是「回落返回 lexical abspath」，
均与本次三条不同）。用的是**本仓 `sdflow-*/scripts/` 下的脚本**，非 `~/.claude/skills` symlink。

| ID | 池 | 内容 | 备注 |
|---|---|---|---|
| **B16** | buglist P3 | `test_exec_claude_reverse_path_three_flags_golden` 间歇性失败 | **按 CF-3 如实写「触发条件未定位」**：原记的「全量跑必红 / 单独跑绿」已被 Task 1（1753 passed / 0 failed）与 Task 6（1870 passed / 0 failed）两次全量跑**证伪**。已写入下一步排查建议（捕获失败时的用例序 + 断言差异）。**未照抄已证伪的描述。** |
| **T182** | todolist 基础设施 | `repo_root` 不限制 git stdout 读取量的 DoS 面 | tasks 4.8 / design Non-Goals / codex X10 后半 |
| **T183** | todolist 代码质量 | `isdir(start)` 与 `subprocess.run(cwd=start)` 之间的 TOCTOU 窗口 ⇒ 落回落分支而非 fail-closed | **CF-7**；含修法方向与「须先确认与 spec 回落措辞是否冲突」的定性 |

---

## 5. 回归确认（实测输出）

| 项 | 命令 | 结果 |
|---|---|---|
| 4.9 全仓无回归 | `/usr/bin/python3 -m pytest -q` | **1870 passed, 9 skipped, 3 xfailed** in 115.38s |
| — xfail 锚 | 同上 | **3 xfailed 原样保留**（Task 3 的 R2 缺口锚，未动） |
| — skipped 增量 | 同上 | 4 → **9**：+5 恰为本票新增的 Windows-only 用例（macOS 上模块级 skip），**无其他用例被静默跳过** |
| 4.1 垃圾树未再生 | `find . -maxdepth 1 -name '{*'`（全套件跑完后） | **无输出** |
| 4.2 干净临时目录 | `cd $(mktemp -d) && pytest <abs>/sdflow-issues/tests/` | **253 passed, 1 xfailed**；该目录 `ls -A \| wc -l` = **0** |

---

## 6. 诚实边界（MUST NOT 读成"全覆盖"）

1. **CF-8**：`timeout=30` 的**数值本身无自动化锚**——真等满 30s 会给每次跑套件加 30s 墙钟，
   代价不可接受。已覆盖的是契约层（`ValueError` + 不回落 + `subprocess.run` 确收正数 `timeout`）
   与真 PATH 注入 shim（外层 timeout 收窄到 1s）。**MUST NOT 宣称「超时面已全覆盖」。**
2. **Windows 泳道未验证**（见 §2 边界段）——写好了，没跑过。
3. **CF-2**：R4 的达成锚在 **Task 5**（仓根 `conftest.py` + `pytest.ini` 的机械保证），
   **不在 Task 1**（Task 1 清的是 R4 被违反后的历史产物）。本票的 4.1 / 4.2 是 R4 的
   **收敛验证**，不是 R4 的达成本身。
4. **#8 `outside-voice.sh` 的 `$repo_root` 仍未经校验**——排除是基于「sink 无写能力」，
   不是基于「值是对的」。质量面残余（voice 在错树取证）已如实记在 §1。
5. 面治扫描证明的是「**`show-toplevel` 这个字面量**的全部出现处已裁定」。**其他求仓根的姿势**
   （如 `--git-dir`、向上找 `.git`、`Path(__file__).parents[N]`）不在本次扫描口径内，未被排除。

---

## 7. 🔴 须在设计门回写四件套的完整清单（CF-9 + 本票新发现）

> 四件套在设计门拍板后冻结（改动触发 `ship_gate` 失鲜 REFUSE_START），故一律汇总到此、一次性回写。

**承自 CF-9（Task 5 双轴审确认，全部是「实现对、文档措辞旧」）**：

| # | 文件 | 落差 | 回写动作 |
|---|---|---|---|
| a | `spec.md:157-158` | 仍写「一切落盘物 MUST 位于 `tmp_path`」，而 design **D6 已收窄**为「禁止新增 cwd **顶层条目**」，决议没落到 spec 正文 ⇒ spec 目前宣称了实现不覆盖的东西 | 正文改到 D6 的收窄口径 |
| b | `spec.md:160` + ADR-3 标题/决策 + `tasks.md 3.1` | 均写「**autouse fixture**」，实现用的是 `pytest_runtest_{setup,call,teardown}` **hook wrapper**（理由：autouse fixture 的 teardown 异常会被记成「passed + teardown error」，摘要行写 `1 passed`，泄漏降级成脚注 ⇒ 照字面实现反而制造假绿） | 三处措辞改 hook wrapper + 记录「为什么不是 autouse fixture」 |
| c | ADR-3 覆盖机制 | 「仓根一份天然覆盖」**漏了前置条件**：conftest 收集止于 `confcutdir`（默认 = rootdir），本仓此前无 ini ⇒ 从仓外跑 rootdir 塌缩、仓根 conftest 不被收集（双向变异实证） | 补 `confcutdir` 前置条件；**「代价」段从一个根级文件改为两个**（`conftest.py` + `pytest.ini`，缺一即失效） |
| d | `tasks.md 4.4` | 「没有根级 pytest 配置」被新增的 `pytest.ini` 正面证伪 | **本票已按两文件口径执行完毕**（见 §3）；tasks 正文待回写 |
| e | ADR-3 基线 | 自称「**12 个** skill + hack 均 0 残留」，实测是 **11 个**（10 skill + hack；`sdflow-retro` 无 `tests/`） | 订正为 11 |

**本票新增**：

| # | 文件 | 内容 |
|---|---|---|
| f | `proposal.md` Non-Goals | 写入 §1 的 **8 处扫描结果 + #4–#8 五处排除的安全论证**，其中 **#8 `outside-voice.sh` MUST 保留为独立论证段**（工具权限层无写能力），**MUST NOT 与 #4–#7 的「只读拼路径」豁免合并成一条模板** |
| g | `proposal.md` Non-Goals | 补记 §6.5 的**扫描口径边界**：本次只穷举了 `show-toplevel` 字面量，其他求根姿势未裁定 |
| h | `tasks.md 4.3` / `proposal.md` P2 | 「登记**编号** + 路径」按字面不可执行——`premise-verification.md` 无文档级编号（`gstack-review.md:70` D1 已指出）。本票已改为「路径 + 内部规则 N」登记。**待拍板**：是否给该 rules 文件补 `PV-1` 式 H1 前缀（改 `openspec/rules/`，独立动作） |
| i | ADR-2 / `spec.md` 祖先校验段 | 补记 **CF-6 的可观测性降级**：跨盘符时 `commonpath` 自抛 stdlib `ValueError`，行为 fail-closed 但消息不带三段式。当前保留 `commonpath`（written decision），已用测试钉死；若将来换 `PurePath.is_relative_to` 须走设计门 |
| j | design「测试覆盖图」 | 补 Windows 泳道 5 条用例；并**如实标注其证据状态 = 待 CI Windows runner**，MUST NOT 直接标 ✅ |
