# Task 1 实现报告：截断产出的两半各自都是合法 UTF-8（R1）

**状态**：DONE
**改动文件**：
- `sdflow-init/assets/hack/outside-voice.sh`（bundle 唯一权威源；仓内无第二份副本，已 `find` 核实）
- `sdflow-init/tests/test_outside_voice_utf8.py`（新增，38 个用例）
- `sdflow-init/tests/test_outside_voice.py`（版本 golden 1.3.0 → 1.4.0）

---

## 1. 做了什么

### 1.1 病灶

`render_prompt()` 超过 `OV_MAX_CONTEXT_BYTES` 时用 `head -c half` / `tail -c half` 在**字节**边界切。
多字节字符被劈成两半 → 头段末尾留残缺序列、尾段开头留孤儿 continuation 字节 →
跨模型 runner 收到非法 UTF-8 可拒收**整个** prompt = voice 静默失效。

### 1.2 修法（design D1，纯 bash 边界回扫，零新增运行时依赖）

新增三个函数（`render_prompt` 之前）：

| 函数 | 契约 |
|---|---|
| `_ov_bytes_at <file> <offset> <count>` | 用 `od -An -tu1 -j -N` 取十进制字节值，每行一个 |
| `utf8_head_trim <file> <n>` | 头段末尾需丢弃的字节数（0-3） |
| `utf8_tail_skip <file> <n>` | 尾段开头需跳过的字节数（0-3） |

**头段算法**：只看末 ≤4 字节，从末尾回扫找最近的「起始字节」（不在 128-191）。由其值定序列长度
`len`（<128→1；240-247→4；224-239→3；192-223→2；≥248 非 UTF-8 起始字节→1，即不动）。
若头段内该序列已有字节数 `avail < len` ⇒ 序列残缺 ⇒ 丢弃这 `avail` 字节。

**尾段算法**：尾段起点必落在原文件某个真实字节上 ⇒ 跳掉开头连续的 continuation 字节（128-191，最多 3 个）后，
下一个必是完整序列的起始字节（其后续字节在文件里原封不动）。∴ 只需数前导 continuation，无需回读文件前部。

**基准 ⑤ 边界（design D1 硬约束）**：只认 UTF-8。UTF-8 是**有界**语法面（序列 ≤4 字节、continuation
形态确定 0x80-0xBF）∴ 可手写回扫。遇到非 UTF-8 字节（0xF8-0xFF、全 continuation 尾巴）一律**回退 0 不动**，
**没有**任何编码检测/嗅探分支。该边界由 `test_non_utf8_bytes_are_left_alone` 机械锁住。

### 1.3 render_prompt 截断分支

```
half=$(( OV_MAX_CONTEXT_BYTES / 2 ))
htrim=$(utf8_head_trim "$ctx" "$half");  hlen=$(( half - htrim ))
tskip=$(utf8_tail_skip "$ctx" "$half");  tlen=$(( half - tskip ))
head -c "$hlen" "$ctx"
printf '\n===== [TRUNCATED: 原 %s bytes, 保头 %s + 尾 %s bytes] =====\n' "$size" "$hlen" "$tlen"
tail -c "$tlen" "$ctx"
echo "OV_TRUNCATED_DROPPED_BYTES=$(( size - hlen - tlen ))" >&2
echo "OV_UTF8_BACKSCAN_DROPPED=$(( htrim + tskip ))" >&2
```

**可观测性**（design「可观测性」约束：新增 stderr **MUST NOT 含 context 正文**）：新增两行**只有字节计数**，
无任何正文片段。`test_stderr_reports_dropped_byte_counts` 反向断言 stderr 中不出现三个正文探针。

两个计数各自对应票上一条判据：`DROPPED_BYTES` = 操作者判断「截断吃掉多少有效内容」；
`BACKSCAN_DROPPED` = 边界回扫**额外**多退的字节（纯 ASCII 恒 0，即「不能靠无脑多切蒙混」）。

### 1.4 测试接缝

在命令派发（`cmd="${1:-}"`）之前加：

```bash
if [ "${OV_LIB_ONLY:-}" = 1 ]; then
  return 0 2>/dev/null || exit 0
fi
```

`OV_LIB_ONLY=1 . outside-voice.sh` ⇒ 只加载函数、不派发命令。这让两个回扫函数成为**可被 pytest 直接驱动
的公共函数边界**（无需端到端跑 runner），也是变异验证的落点。默认路径（不设该变量）行为逐字不变。

### 1.5 版本

`OV_VERSION` 1.3.0 → **1.4.0**（头部契约注释同步：render-prompt 的 stderr 契约补两行计数 + 边界安全承诺）。
`version` 命令的 golden 断言同步更新并注明升版理由。

---

## 2. 测试怎么设计的

新文件 `sdflow-init/tests/test_outside_voice_utf8.py`，沿用 `test_outside_voice.py` 的既有 idiom
（`subprocess.run(["bash", str(HELPER), ...])` + `tmp_path` + 清 ambient `SDFLOW_VOICE_*`），未自造框架。

**语料**：`MIXED` = ASCII / 2 字节拉丁(`café ñ`) / 3 字节 CJK / 4 字节 emoji(`😀🎉🚀`) 混排 ×3，共 258 字节
——每种多字节宽度都出现，才能覆盖「切在序列第 1/2/3 字节之后」的全部残缺形态。`ASCII_ONLY` 为纯 ASCII 对照。

**全切点扫描**：`_scan()` 起**一个** bash 进程，`OV_LIB_ONLY=1` source 后循环 `k=1..size-1`，一次取回所有
切点的 `(head_trim, tail_skip)`（避免每偏移两次 subprocess 的慢法）。Python 侧用 `bytes.decode("utf-8",
errors="strict")` 分别解 `data[:k-trim]` 与 `data[len-k+skip:]`——**分别**，不是拼起来（两半在 prompt 里
被 TRUNCATED 横幅隔开，从不相邻）。

| 用例 | 锁的判据 |
|---|---|
| `test_every_cut_offset_yields_two_valid_utf8_halves` | ⭐ 每一个切点，头/尾段各自严格解码成功，失败数 0 |
| `test_mutation_constant_zero_backscan_turns_the_scan_red` | ⭐ 变异验证（见 §3） |
| `test_backscan_never_over_trims` | 回扫 ≤3 字节 —— 防「无脑多切」蒙混 |
| `test_pure_ascii_loses_zero_bytes` | 纯 ASCII 全切点 `(trim, skip) == (0, 0)` |
| `test_non_utf8_bytes_are_left_alone` | 基准 ⑤ 边界：非 UTF-8 字节不猜编码 |
| `test_render_prompt_emits_valid_utf8_when_truncating[60..89]` | 端到端 30 参数化：整个 stdout 严格解码 |
| `test_stderr_reports_dropped_byte_counts` | 两行计数存在、数值自洽、**不含正文** |
| `test_ascii_truncation_reports_zero_backscan_loss` | ASCII 截断 `BACKSCAN_DROPPED=0` |
| `test_secret_scan_still_covers_whole_file_before_truncation` | 密钥落在**被丢弃的中段**仍 exit 3 |

最后一条对应票上「密钥扫描覆盖面未缩小」：密钥被刻意放在 400 字节 filler 中间（截断后既不在头段
也不在尾段），仍返回 exit 3 —— 证明 `secret_scan` 依旧先于截断扫**整个文件**。这是行为验证，
不是「读代码确认顺序没动」。

---

## 3. 变异验证（票上明列的判据）

**做法**：`_scan(..., mutate=True)` 在 `OV_LIB_ONLY=1` source 之后注入

```bash
utf8_head_trim() { echo 0; }
utf8_tail_skip() { echo 0; }
```

即把边界回扫退化回「按字节切」，再跑同一套全切点扫描。

**结果**：`test_mutation_constant_zero_backscan_turns_the_scan_red` 通过 ——
变异体下失败切点集**非空**，证明该扫描断言确实由回扫承重，不是语料恰好没被切中而全绿。

**第二重红证（因为我是先写实现后写测试，按诚实原则必须补真红）**：
把整套测试指向 `git show HEAD:sdflow-init/assets/hack/outside-voice.sh`（改动前的脚本），实跑结果：

```
29 failed, 9 passed in 1.17s
```

失败含 `test_every_cut_offset_yields_two_valid_utf8_halves`、`test_stderr_reports_dropped_byte_counts`、
`test_ascii_truncation_reports_zero_backscan_loss` 及大部分 `test_render_prompt_emits_valid_utf8_when_truncating[*]`
参数化实例（9 个 pass 的是切点恰好落在字符边界上的偏移 + secret_scan 那条）。

---

## 4. 跑了哪些命令与真实输出

### 4.1 新测试文件

```
$ /usr/bin/python3 -m pytest sdflow-init/tests/test_outside_voice_utf8.py -q
......................................                                   [100%]
38 passed in 7.38s
```

### 4.2 改动前脚本（红证）

```
$ OV_PRE_HELPER=<HEAD 版脚本> /usr/bin/python3 -m pytest <指向 HEAD 版的测试副本> -q
29 failed, 9 passed in 1.17s
```

### 4.3 全套件（改动后）

```
$ /usr/bin/python3 -m pytest -q
1705 passed, 2 skipped in 79.06s (0:01:19)
```

全套件跑了两次（加版本 golden 前后各一次），两次均 `1705 passed, 2 skipped`，含本票新增的 38 条。
**诚实登记**：我**没有**单独跑一次「改动前的全套件基线数」，∴ 无法给出「基线 N → 现在 N+38」的对照；
「未打破既有测试」的依据是全套件 0 failed、且唯一被我改过的既有断言是 `test_version` 的版本 golden
（改动理由已写进该行注释）。

### 4.4 手工端到端实证

语料 = `("中文汉字 emoji 😀🎉 mixed ASCII text 更多内容\n" * 20)`，1160 字节。

```
$ for n in $(seq 100 2 160); do ... done
OV_MAX=100 → OV_UTF8_BACKSCAN_DROPPED=3
OV_MAX=102 → OV_UTF8_BACKSCAN_DROPPED=2
OV_MAX=104 → OV_UTF8_BACKSCAN_DROPPED=1
OV_MAX=106 → OV_UTF8_BACKSCAN_DROPPED=3
...
```

回扫在 0-3 之间随切点变化（不是恒定值，也不是恒 0）。同批每个 n 的 stdout 均严格 UTF-8 解码通过。

```
$ OV_MAX_CONTEXT_BYTES=201 ... render-prompt --context-file demo.md
exit=0
OV_TRUNCATED_DROPPED_BYTES=960
OV_UTF8_BACKSCAN_DROPPED=0
OV_TRUNCATED=true
stdout 严格 UTF-8 解码 OK, 5380 bytes
横幅: ===== [TRUNCATED: 原 1160 bytes, 保头 100 + 尾 100 bytes] =====
```

---

## 5. 约束合规

| 约束 | 状态 |
|---|---|
| design D1「只认 UTF-8，MUST NOT 演化成编码嗅探」 | ✅ 无编码检测分支；非 UTF-8 字节回退 0；`test_non_utf8_bytes_are_left_alone` 机械锁 |
| 可观测性「stderr MUST NOT 含 context 正文」 | ✅ 只有两行字节计数；`test_stderr_reports_dropped_byte_counts` 反向断言三个正文探针不出现 |
| 安全「`secret_scan` 仍先于截断扫整个文件」 | ✅ `secret_scan` 调用点（`render_prompt` 开头、`do_exec` 预扫）**一行未动**；行为级验证见 §2 末条 |
| 「不改出境侧扫描」 | ✅ 未触碰 `do_exec` 末尾的出境 `secret_scan` |
| D-1「代码事实全部经 grep 核验」 | ✅ 所有引用的行号/调用点均现场 grep/read 确认，无记忆直写 |
| Non-Goal「不改 recorder 侧任何代码」 | ✅ 假设未被证伪：修复只触及 `outside-voice.sh` |
| Non-Goal「不做 R7（截断覆盖面诚实）」 | ⚠️ 见 §6 concern 1 |
| Non-Goal「不做『让截断变聪明』」 | ✅ 保头尾各半策略原样，只在切点上回退 ≤3 字节 |
| Non-Goal「不改锚行字段与 `anchor_lint` 矩阵」 | ✅ 未触碰 |
| Non-Goal「不做 async/backgrounding」 | ✅ 未触碰两 SKILL 的字节等值 marker 段（`test_async_branch_parity` 仍绿） |
| bundle「禁止只改仓内副本」 | ✅ `find . -name outside-voice.sh` 只有 `sdflow-init/assets/hack/` 一份 |

---

## 6. 遗留 concerns

1. **`OV_TRUNCATED_DROPPED_BYTES` 与 R7 的边界**（需下游确认，我没自行扩范围）：
   票要求「操作者能看出实际丢弃了多少字节」，我实现为**总丢弃量**（含既有的保头尾策略本身丢的中段）
   + **回扫额外丢弃量**两个独立计数。这**逼近**但不等于 R7「截断覆盖面诚实」（R7 大概涉及锚行字段留痕/
   向调用方回传）。我只加了 stderr 计数，**没有**碰锚行字段、没有改调用方读取逻辑 ⇒ Non-Goal 未破。
   若 R7 后续开工，这两行计数是现成的数据源。

2. **`setup.sh` 未跑（有意）**（adr/0005）：`~/.sdflow/hack/outside-voice.sh` 目前仍是 1.3.0，
   `~/.sdflow/workflow` symlink 指向**运行 checkout** `~/.skills/sdflow-skills`。在开发 checkout 跑
   `setup.sh` 会把用户的全局运行时**重指到 dev**——那是有副作用的机器级改动，不该由 ticket 子代理
   单方面做。本票的全部验证都直接打在 `sdflow-init/assets/hack/` 源文件上，不依赖已安装副本 ⇒ 验证完整。
   **发布时须按 adr/0005 在运行 checkout 走 pull → 立即 setup.sh**，否则新 SKILL 调旧脚本。

3. **`local` 在 `if` 块内**：`render_prompt` 里 `local half htrim ...` 写在 `if` 分支内部。bash 允许
   （函数内任意位置），脚本首行是 `#!/usr/bin/env bash` 且既有代码已依赖 bash 特性（`local -a`、
   `(( ))`、进程替换、数组），非 POSIX sh 兼容性问题。已在 macOS bash 3.2 与测试全套件下实跑通过。

4. **性能**：每次截断多跑 2 次 `od`（各读 ≤4 字节）+ 1 次 `wc -c`。相对于 200KB 的 `head`/`tail`
   与随后的 runner 调用（默认 300s 超时），可忽略。测试里的全切点扫描（258 偏移 × 2 函数 = 516 次
   `od`）约 2s，可接受。

5. **未验证**：Linux 侧的 `od` 行为未实跑（仅 macOS/Darwin 25.5.0）。`od -An -tu1 -j N -N M` 是
   POSIX 规定的选项组合，GNU coreutils 与 BSD od 均支持，风险低但我**没有**在 Linux 上实测。

---

## 7. 提交

未提交，改动留在工作树（按 ticket 契约，实现期 commit 不带 `task<N>-` 完成标签；本票可由编排层
在双轴审后统一处理）。
