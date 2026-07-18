# Task 1 返修轮 1 — UTF-8 边界回扫（双轴评审返修）

> 承 `task1-utf8-boundary.md`（**保留不改**，审计轨迹）。本文只记返修内容与**对前文错误主张的更正**。
> 改动文件：`sdflow-init/assets/hack/outside-voice.sh`、`sdflow-init/tests/test_outside_voice_utf8.py`。

## 0. 一句话

两面镜收敛的 I1（测试接缝静默 exit 0）已按「source-only + 执行态 fail-loud + 变量改名」修掉并加了
两条正反向机械锁；I2 采纳**方案 (a) golden 序列 + 改名**，D1 的「机械锁」主张由「不成立」转为**成立**
（附嗅探器变异验证）；M3-M6 同片面一并治。全套件 1708 passed / 2 skipped。

---

## 1. I1 — `OV_LIB_ONLY` 测试接缝制造静默 exit 0（Important，两轴独立收敛）

**病灶**：`OV_LIB_ONLY=1` 对**执行态**也直接 `exit 0` ⇒ 该变量从父进程环境泄漏（子代理 / CI /
嵌套调用继承 env）时，helper 产出 **0 字节 prompt + exit 0**，调用方读成「成功但无 findings」。
**这正是本 change 要消灭的那一类静默失效，长在治这个病的 change 自己身上。**

**修法（两条一起做，采纳 Standards 轴推荐 + Spec 轴建议）**：

| 维度 | 修前 | 修后 |
|---|---|---|
| 生效范围 | 执行态 + source 态 | **仅 source 态**（`[ "${BASH_SOURCE[0]:-}" != "$0" ]`） |
| 执行态带该变量 | 静默 `exit 0`、stdout 0 字节 | **`exit 2` + stderr 明示误用**（fail-loud） |
| 变量名 | `OV_LIB_ONLY`（无前缀，泄漏面大） | `_OV_TEST_LIB_ONLY`（下划线 + TEST 前缀，不与任何公开契约变量同形） |

`exit 2` 而非 1：与既有「用法错」语义一致（见文件头契约块，用法错/文件不可读 = 2）。

**机械锁（新增两条，正反向各一）**：

- `test_lib_only_seam_is_source_only_and_fails_loud_when_executed` — 执行态注入该 env ⇒ 断言
  `returncode == 2` ∧ `stdout == b""` ∧ stderr 含变量名。**反向**：锁死"不许静默"。
- `test_lib_only_seam_still_works_when_sourced` — source 态仍只加载函数、不派发命令
  （故意多传一个 `version` 参数，断言 stdout 里**没有** `outside-voice.sh` 版本串）。**正向**：
  锁死修 I1 时没把接缝一并弄坏。

**同步引用**：`test_outside_voice_utf8.py` 的 `_scan()` 已改用新变量名（全仓 grep 确认无其它引用；
`task1-utf8-boundary.md` 里的旧名是历史记录，按审计轨迹要求不改）。

---

## 2. I2 — `test_non_utf8_bytes_are_left_alone` 不承重且名实不符

### 2.1 先更正前文的错误主张（诚实优先）

`task1-utf8-boundary.md` §5 合规表把该测试列为 design D1「MUST NOT 演化成嗅探」的**机械锁**。
**该主张当时不成立**，原因两条：

1. **断言太松**：只断言 `0 <= trim/skip <= 3`。**任何**返回 0-3 的实现都能通过——**包括一个完整的
   编码嗅探器**（它会返回全 0，恰在区间内）。锁不住任何东西。
2. **名实不符**：`..._are_left_alone` 是**假的**。实测 `abc\xe9\xff\xfe def` 语料在 `k=4` 得
   `trim=1` —— 字节并未原样保留。

### 2.2 选定方案：(a) golden 序列 + 改名（两条都做）

**为什么选 (a) 而不是 (b) 撤主张**：0xE9 处退 1 字节**不是缺陷、正是 D1 要的行为**——0xE9 是合法的
3 字节序列首字节，回扫**只看首字节形态、不看后续字节是否真构成合法序列**（看了就是嗅探）。
所以这里可锁的真实行为是存在的，(b) 撤下主张等于白扔一个能锁住 D1 的机会。改成 golden 后，
「机械锁 D1」这句话**由不成立变为成立**，而不是被删掉。

**golden 不是"跑一遍抄下来"，是 UTF-8 规则推出来的**（语料每 14 字节一轮，0xE9 在轮内 offset 3）：

- 切点 `k ≡ 4 (mod 14)` ⇒ 头段末字节正是 0xE9，`avail=1 < len=3` ⇒ **trim = 1**
- 其余切点末字节非 continuation 且自身完整 ⇒ **trim = 0**
- 0xFF / 0xFE 不在 0x80-0xBF ⇒ 从不被当 continuation 跳过 ⇒ **skip 恒 0**

⇒ `expected = {k: (1 if k % 14 == 4 else 0, 0)}`，全 55 个切点逐点比对。

**它真的锁住嗅探吗 —— 变异验证（已实跑）**：把回扫替换成"Latin-1 嗅探器结论"（认定全是单字节
字符 ⇒ 恒返回 0），golden 断言**转红**，差异切点 `[4, 18, 32, 46]`。∴ 承重成立。

**改名**：`test_non_utf8_lead_bytes_follow_utf8_semantics_not_sniffing`（名实相符：讲的是"按 UTF-8
首字节语义走、不嗅探"，而**不是**"字节原样保留"）。粗粒度护栏拆成独立的
`test_non_utf8_backscan_never_over_trims` 保留（≤3 不越界），两条互补。
模块 docstring 的旧测试名引用已同步。

---

## 3. Minor（同一片面，面治不点补）

| # | 位置 | 病 | 修法 |
|---|---|---|---|
| **M3** | `utf8_tail_skip` 的 `wc -c` | 文件不可读时裸 shell 重定向错误打进 stderr，而 **stderr 是被 SKILL.md 解析的契约通道**（`truncated` 取 `OV_TRUNCATED`）⇒ 污染契约 | 加 `2>/dev/null`；**并**加 `case` 守卫：拿不到数字大小就 `echo 0` 早返（不动）——否则空串会让后续 `$(( size - n ))` 拿脏值继续算 |
| **M4** | `render_prompt` 的 `htrim=$(...)` / `tskip=$(...)` | 命令替换失败时变量只是**空串**（已被 `local` 预声明 ⇒ `set -u` 抓不到，本脚本又无 `set -e`）⇒ `head -c ""` 静默无输出、TRUNCATED 横幅照打，拿无效数据继续走 | 两处加 `case ... ''\|*[!0-9]*) x=0` 兜底 ⇒ 退化为按字节切（输出不空；合法 UTF-8 保证降级但不静默产空） |
| **M5** | 3 处 continuation 判据 `[ b -ge 128 ] && [ b -le 191 ]` | 重复 | 抽出 `_ov_is_cont()`，两处代码点调用；第 3 处是注释（`0x80-0xBF = 128-191` 说明），保留为文档 |
| **M6** | `OV_DIR="$(cd "$(dirname "$0")" && pwd)"` | 被 source 时 `$0` 是宿主进程 ⇒ 解析到 cwd | 当前接缝只驱动两个纯函数（不读 `OV_DIR`）∴ **不受影响**；按要求加注释标明**接缝适用范围** + 将来把 `emit_frame`/`render_prompt` 纳入 source 态驱动前 MUST 改 `${BASH_SOURCE[0]}` 基准（否则通则文件静默走「缺失降级」分支） |

> M4 的注释里显式写明了「为什么 `set -u` 在这里不管用」——`local` 预声明使变量**已定义但为空**，
> 这是 `set -u` 的已知盲区，不写下来下一个人会以为 `set -u` 兜住了。

---

## 4. 硬约束自查

| 约束 | 状态 |
|---|---|
| 只认 UTF-8，MUST NOT 演化成编码检测/嗅探 | ✅ 无新增编码分支；golden 测试**新获得**锁住该边界的能力（§2.2 变异已验） |
| 新增 stderr MUST NOT 含 context 正文 | ✅ 本轮新增 stderr 仅 I1 的误用提示（固定字面串，无文件内容）；`test_stderr_reports_dropped_byte_counts` 的正文探针仍绿 |
| 不改出境侧扫描 / `secret_scan` 仍先于截断扫全文 | ✅ 未触碰；`test_secret_scan_still_covers_whole_file_before_truncation` 绿 |
| 不改锚行字段与 `anchor_lint` 合法组合矩阵 | ✅ 未触碰 |
| 不改 recorder 侧代码 | ✅ 未触碰 |
| 不做 async/backgrounding 改动（不碰两层 SKILL 字节等值 marker 段） | ✅ 未触碰；`test_async_branch_parity` **26 passed** |
| `outside-voice.sh` 唯一权威源 = `sdflow-init/assets/hack/` | ✅ 只改这一份 |
| 脚本是 bash、只有 `set -u` 无 `set -e` | ✅ 兜底逻辑正是按「无 `set -e`」前提写的（M4） |

## 5. 验证

```
/usr/bin/python3 -m pytest sdflow-init/tests/ -q   → 260 passed in 31.21s
/usr/bin/python3 -m pytest -q                      → 1708 passed, 2 skipped in 86.30s
/usr/bin/python3 -m pytest -q -k async_branch_parity → 26 passed（Non-Goal 守卫）
嗅探器变异验证（§2.2）                              → golden 断言转红，差异切点 [4,18,32,46]
```

> 注：仓内 `python3` 解析到 `~/.local/bin/python3`（无 pytest），实跑用 `/usr/bin/python3`（pytest 8.4.2）。

**未提交**——按要求改动留工作树（实现期 commit MUST NOT 带 `task<N>-` 标签）。
