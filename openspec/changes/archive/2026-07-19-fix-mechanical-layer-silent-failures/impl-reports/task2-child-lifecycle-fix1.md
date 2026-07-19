# Task 2 返修轮 1 — 子进程生命周期两轴审 Important ×2 + Minor ×1

**范围**：`fix-mechanical-layer-silent-failures` / Task 2（runner 子进程生命周期）。
原实现报告 = `task2-child-lifecycle.md`（**未覆盖**，本文件为返修轮记录）。
两轴审结论：Critical 0 · Important 2（I1 / I2）· Minor 1（M3 两轴收敛 + M4 措辞）。**四条全修**。

---

## I1 — bash 3.2 multibyte 危害补机械门

**问题**：本轮撞到的真 bug —— bash 3.2 扫变量名不是 multibyte-aware，`"$src，"` 会把全角逗号
首字节 `0xEF` 吞进标识符 ⇒ `set -u` 下**运行时硬罢工，清理逻辑整个不执行**（罢工点在 `kill` 之前，
孤儿照跑）。修好之后**只有源码注释在守**，复发靠人眼 —— 撞 CLAUDE.md 基准 ①（能机械化的一致性
优先机械化）+ 基准 ③（面治不点补）。

**修法**：新增 `sdflow-init/tests/test_hack_shell_multibyte_guard.py`，扫 `sdflow-init/assets/hack/*.sh`
的**非注释行**，命中 `$变量` 紧跟非 ASCII 字节即红。

- 正则 `\$[A-Za-z_][A-Za-z0-9_]*[^\x00-\x7F]` —— `${var}` 不命中（`{` 非变量名首字符）。
  用 python 扫文件内容，**不用 grep `-P`**（BSD grep 无此选项）。
- **注释判据（故意保守）**：整行以 `#` 开头（含前导空白）⇒ 纯注释行、永不执行 ⇒ 跳过；
  其余行**整行扫**（含行尾注释）。行尾注释里的 `$var，` 是误报，但 shell 注释起点无法在不写一个
  shell 词法器的前提下可靠判定（`#` 可出现在字符串 / `${#x}` / `$#` 中 —— 无界语法面，基准 ⑤
  明令 MUST NOT 手搓）。∴ 宁可保守多报；误报的修法是加花括号，零代价且本就更好。
- 自防呆：`test_hack_dir_has_shell_files_to_guard` —— glob 打空时不许「全绿」。

**实跑**：7 passed。
**变异验证（对真源码，非合成串）**：把 `outside-voice.sh:316` 的 `${src}` 还原成 `$src`
⇒ `test_no_unbraced_variable_before_non_ascii[outside-voice.sh]` **当场红**，
报 `L316: 命中 '$src，'`。已还原。另有 `test_detector_catches_the_known_regression_shape`
把该变异固化进测试内部。

**面治核实**：全仓 7 个 `.sh` 扫过（`sdflow-init/assets/hack/*.sh` 5 个 + 其余），
非注释行**零命中** —— 无活实例，门是干净起立的。

---

## I2 — 生命周期测试钉 `/bin/bash` 3.2 + PATH bash 两档

**问题**：`test_outside_voice_child_lifecycle.py:96,220` 用 PATH 里的 `bash`。本机
`command -v bash` 恰为 `/bin/bash`（**3.2.57**）才照出 I1 那个 bug。换台装了 brew bash 5 的
开发机，3.2 路径一次都不跑，同类 bug 静默出厂 —— 与已记录的
`windows-ci-bash-subprocess-traps` 同形（本地照不到、真 runner 才抓到）。

**修法**：新增 `_bash_params()` + `bash_bin` fixture，两档参数化：

| 档 | 取值 | 处置 |
|---|---|---|
| `system` | `/bin/bash`（**总是**作为一个 param 出现） | 不存在 ⇒ **skip 而非 fail**（多数 Linux 把 bash 装在 `/usr/bin`）；skip 是**可见**的，不是悄悄消失的一档 |
| `path` | `shutil.which("bash")` | 与 system **realpath 相同则去重**（本机即此情形，不白跑一遍） |

六个 spawn helper 的用例（3 信号 + 清理痕迹 + 变异 + 3 退出码）全部经 `bash_bin` 注入；
`_run_until_killed` / `_exec` 新增 `bash_bin` 形参。另加 `test_bash_matrix_is_not_empty` 自防呆。

**实跑**：`10 passed in 11.19s`；collect 确认 ID 形如
`test_runner_subtree_dies_when_parent_is_signalled[system:/bin/bash-Signals.SIGTERM-TERM]`。

**三条路径均实测，非推断**：
1. **去重**（本机 `/bin/bash` == `which bash`）→ 单档，10 个用例；
2. **两档**（注入一个另路径的真实 bash 可执行文件当 `which` 返回值）→
   `[('system','/bin/bash'), ('path','…/bash5-stand-in')]`，两档都产出；
3. **缺失即 skip**（把 system 档临时指向 `/nonexistent/bin/bash`）→
   `10 passed, 8 skipped`，skip reason 逐条可见、**零 fail**。已还原。

---

## M3 — PID 窗口残余显式登记（两轴独立收敛）

两轴各自指出一条 shell 层**不可干净消除**的窗口，与 SIGKILL **同性质**。本票主题恰是
「残余诚实登记」⇒ 在 D2 诚实边界处与 SIGKILL **并列登记**，**只登记、不声称已解决**（adr/0018）。

| # | 残余 | 成因 | 后果 |
|---|---|---|---|
| (a) | 父进程 **SIGKILL** | trap 在 `-9` 下不执行 | 孤儿仍存活（既有） |
| (b) | **PID 记录窗口**：`… &` 与 `OV_RUNNER_PID=$!` 之间（Standards 轴） | 后台启动与 `$!` 赋值不可原子化 | pending trap 带**空 PID** ⇒ 该次 runner 逃逸 |
| (c) | **PID 清零窗口**：`wait` 返回与 `OV_RUNNER_PID=""` 之间（Spec 轴） | 两者不可原子化 | 对已回收、**可能已被系统复用**的 PID 开火 |

**落点**（四处，措辞一致）：
- `outside-voice.sh` 头部契约 `exec` 段的诚实边界块 —— 三条并列展开；
- `outside-voice.sh` D2 实现块注释 —— 三条并列；
- **代码行内标记** —— codex / claude 两条 runner 路径的 `OV_RUNNER_PID=$!` 与 `OV_RUNNER_PID=""`
  各挂 `⚠ 残余(b)/(c)` 注记，让窗口在**出事的那一行**看得见；
- `design.md` D2 诚实边界（三行表）+ 失败模式表新增 **F6 / F7** + Risks 条目。

**未声称根治**：三者统一处置 = 「须由调用方在更外层（进程组 / cgroup / 容器）回收」，
与 (a) 完全一致。`test_sigkill_residue_is_documented_not_claimed_solved` 的越界断言黑名单
（`已根治` / `彻底解决` / `孤儿已消除` …）**仍绿**。

---

## M4 — 措辞歧义对齐

`outside-voice.sh:239` `render_prompt` 头注原写「stderr **末行** `OV_TRUNCATED=`」，与头部契约
`:52` 的「调用方按**子串命中**取，不假定它是 stderr 末行」并读易生歧义。
改为「stderr 含 `OV_TRUNCATED=` 一行（调用方按【子串命中】取，MUST NOT 假定它是 stderr 末行
——见头部契约 :52）」。**子串命中**是正确口径（两层 SKILL.md 原文如此，已被两轴独立核实）。

---

## 收尾核实

- `/usr/bin/python3 -m pytest -q` 全套件：**1729 passed, 2 skipped in 89.45s**（0 failed）。
- `test_async_branch_parity`：**26 passed**（两层 SKILL 的 async 字节等值 marker 段未被触碰）。
- `/bin/bash -n outside-voice.sh`：语法 OK（**bash 3.2 自身**校验，非 bash 5）。
- 硬约束复核：新增 stderr **零新增**（M3/M4 只动注释与文档，不新增输出）；
  锚行字段与 `anchor_lint` 矩阵未动；recorder 未动；两层 SKILL 的 async marker 段未动。
- **未提交**，改动留工作树。临时文件全在 scratchpad，仓内无 debris。

### 明确未做（本轮 defer，两轴已判非缺陷）

- SIGKILL 兜底行无测试 —— 实测该行不会误打，属**未锁行为**非缺陷。
- `test_outside_voice.py` 看门狗 `lim=$(( sec * 10 ))` 对非整数 `sec` 会炸 —— stub 内部，不影响被测面。
