# task1 返修第 2 轮 — 三个接缝洞（S1/S2/S3）

修改文件：
- `sdflow-init/assets/hack/outside-voice.sh`
- `sdflow-init/tests/test_outside_voice_utf8.py`（追加 3 个接缝测试）

未动：I1 / I2 / M5 / M6（上一轮已被 re-review 实跑核实为真消解）；锚行字段与 `anchor_lint`
矩阵、recorder、两层 SKILL 的 async 字节等值 marker 段（`git diff -- '*SKILL.md'` 空）。

---

## S1（Critical）— `2>/dev/null` 位置错，M3 压根没生效

**位置**：`utf8_tail_skip`（原 208 行）

**病理**：bash **从左到右**处理重定向。`wc -c < "$file" 2>/dev/null` 里 `< "$file"` 先执行，
打开失败的报错由 **shell 自身**打到**尚未被重定向**的 stderr ⇒ 原样进契约通道。

**原症复现**（`chmod 000`，实跑）：

```
--- wrong order (current) ---
(eval):1: permission denied: f.txt
size=[]
--- right order (fix) ---
size=[]
```

**修法**：`size=$(wc -c 2>/dev/null < "$file" | tr -d ' ')` —— `2>/dev/null` 排到
`< "$file"` **之前**。后续 `case ... echo 0` 守卫保留未动（本就可达且正确）。
另在源码加注：重定向顺序是**语义性**的、不是风格。

**修复后实跑**：

```
=== S1: utf8_tail_skip on chmod-000 file, stderr must be EMPTY ===
stderr=[]
S1 PASS
stdout=[0] (expect 0)
```

---

## S2（Important）— `render_prompt` 同函数体内同一个病，面治漏网

**位置**：`render_prompt`（原 222 行）

**病理**：`size=$(wc -c < "$ctx" | tr -d ' ')` 既无 `2>/dev/null` 也无数字守卫。
TOCTOU（220 行 `-r` 检查后权限变化）⇒ size 为空 ⇒ ① `[ "" -gt N ]` 抛
`integer expression expected` 进契约通道；② **静默走 else 分支把超限 context 全量 `cat`**。

**修法**：同 S1 的重定向顺序 + **空/非数字 fail-loud `exit 2`**。
**不兜底成 0** 的理由（写进源码注释）：size 是**截断判据本身**，兜底成 0 会让
`[ 0 -gt N ]` 为假、静默走非截断分支全量送出——正是本 change 要消灭的那类静默失效
（与 S3 同一方向）。

**实跑验证**（两路，都真跑）：

```
=== S2a: shadow wc -> size unreadable, must fail-loud exit 2, no partial prompt ===
rc=2  stdout_len=0  stderr=[context file size 读取失败（不可读/竞态改动）: ok.txt]
S2a PASS

=== S2b: genuine TOCTOU race (chmod 000 after -r check) ===
hit! rc=2 stderr=[context file size 读取失败（不可读/竞态改动）: race.txt]
```

S2b 是**真实竞态**（200KB 文件 + `-r` 检查后 2ms 处 `chmod 000`），第 1 轮即命中。
注意其 stderr **只有我们的固定字面**——无 `Permission denied`、无
`integer expression expected`，即 S1 式的重定向顺序修复在这条路径上同样得到实跑印证。

---

## S3（Minor，方向要紧）— 回扫兜底到 0 = 静默退回 R1 原病

**位置**：`render_prompt` 截断分支（原 236-237 行）

**病理**：`htrim`/`tskip` 取不到时兜底成 0 即恢复「按字节切」＝ **R1 的原病**，而外部
**零信号**：`OV_UTF8_BACKSCAN_DROPPED=0` 与「纯 ASCII 无需回扫」不可区分。
当前实际不可达（两函数恒 echo 数字），但方向与本 change 论点相反。

**修法**：兜底时**额外**打一行纯字面标记 `OV_UTF8_BACKSCAN_UNAVAILABLE=1` 到 stderr。
不含 context 正文 ⇒ 不违硬约束。契约注释块同步登记该行。

**实跑验证**：

```
=== S3a: normal truncation -> marker MUST NOT appear ===
OV_UTF8_BACKSCAN_DROPPED=2
OV_TRUNCATED=true
S3a PASS (no marker)

=== S3b: backscan fns broken -> marker MUST appear ===
OV_UTF8_BACKSCAN_DROPPED=0
OV_UTF8_BACKSCAN_UNAVAILABLE=1
S3b PASS
```

---

## 新增测试（3 条，全部机械断言 stderr 契约通道）

追加到 `sdflow-init/tests/test_outside_voice_utf8.py`：

| 测试 | 锁什么 |
|---|---|
| `test_tail_skip_unreadable_file_does_not_pollute_stderr_contract` | S1：`chmod 000` 下 stderr **恒为空串** |
| `test_render_prompt_size_read_failure_is_fail_loud_not_silent_full_dump` | S2：`exit 2` + stdout 为空（不得产出半截 prompt）+ 不含 `integer expression expected` |
| `test_backscan_fallback_emits_visible_marker` | S3：正常路径**无**标记 / 降级路径**有**标记；且 stderr 不泄漏正文 |

**变异验证**（证明测试真承重，不是恰好为真）——三个变异体逐个实跑，全部转红：

| 变异 | 结果 |
|---|---|
| 把 S1 重定向顺序换回 `< "$file" 2>/dev/null` | ❌ `test_tail_skip_...pollute_stderr_contract` FAILED |
| 删掉 S2 的 `case ... exit 2` 块（退回隐式兜底） | ❌ `test_render_prompt_size_read_failure...` FAILED |
| 删掉 S3 的 `OV_UTF8_BACKSCAN_UNAVAILABLE` 那行 | ❌ `test_backscan_fallback_emits_visible_marker` FAILED |

变异后均已 `cp /tmp/ov.bak` 还原，`git status` 复核无残留。

---

## 门禁

```
/usr/bin/python3 -m pytest sdflow-init/tests/ -q     → 263 passed in 31.45s
/usr/bin/python3 -m pytest -q                        → 1711 passed, 2 skipped in 79.51s
/usr/bin/python3 -m pytest -q -k async_branch_parity  → 26 passed
```

> 注：`python3` 在本机解析到 `~/.local/bin/python3`（无 pytest）；实跑一律走
> `/usr/bin/python3`（pytest 8.4.2）。

## 硬约束自查

- 只认 UTF-8，无编码检测/嗅探引入 ✅（三处改动均不碰回扫算法本身）
- 新增 stderr 只有固定字面 + 路径，无 context 正文 ✅（S3 测试机械断言）
- 未改锚行字段 / `anchor_lint` 矩阵 / recorder / SKILL async marker 段 ✅
- 脚本仍只 `set -u`，无 `set -e` ✅（新增 `exit 2` 是显式退出，不依赖 errexit）

## 状态

改动留工作树，**未提交**（`git status`：2 个 M + 2 个 ??）。
