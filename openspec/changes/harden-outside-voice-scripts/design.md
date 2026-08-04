## Context

见 proposal.md — Why。标的脚本：`sdflow-init/assets/hack/outside-voice.sh`（910 行，bash）和 `outside-voice-job.py`（~2100 行，Python 3）。两者由 `setup.sh` 安装到 `~/.sdflow/hack/`，运行时被 `sdflow-spec-review` 和 `sdflow-code-review` 两个评审 SKILL 消费。

## Goals / Non-Goals

**Goals:**
- 修复 6 处缺陷（T176/T227/T174/T173/T230/T178）
- 每处修复有对应测试锚

**Non-Goals:**
- 不改 `run_cleanup` / `probe_subtree`（已有完整路径）
- 不改 outside-voice.sh 的 trap 机制本身（残余 (a)(b)(c)(d*) 是 shell 层限制）
- 不做出境 UTF-8 回扫（入境已有，出境只截字节 + 告警）

## Decisions

### D1 · `--timeout 0` 拒绝方式

`case "$2"` 分支加 `0)` 拒绝，`exit 2`（与 `usage` 一致）。

**砍掉的候选**：改为最小值下限（如 `[ "$tmo" -lt 1 ]`）— 过度设计，0 是唯一的危险值（禁用超时），负数已被 `*[!0-9]*` 拦。

**改动点**：`outside-voice.sh:893-894`，在既有 `''|*[!0-9]*)` 后加 `0)` 分支。

### D2 · worker 信号转发

`cmd_worker` 的 `subprocess.call`（第 1009 行）改为 `subprocess.Popen`：

```
proc = subprocess.Popen(...)
def _fwd(signum, frame):
    proc.send_signal(signum)
signal.signal(signal.SIGTERM, _fwd)
signal.signal(signal.SIGINT, _fwd)
try:
    rc = proc.wait()
except:
    proc.terminate()
    try: proc.wait(timeout=10)
    except: proc.kill()
    rc = proc.wait()
```

**砍掉的候选**：(a) `start_new_session=True` — 但 helper 的 `ov_cleanup` 已经在处理同组信号，加 `start_new_session` 反而让组信号传不到 helper；(b) 不改 — 失效面真实。

**改动点**：`outside-voice-job.py:1005-1018`

### D3 · fake-timeout 非整数兼容

测试桩的 `lim=$(( sec * 10 ))` 改为 `lim=$(awk "BEGIN{printf \"%d\", $sec * 10}")` 或等价。

**改动点**：`sdflow-init/tests/` 下的 fake-timeout 桩

### D4 · KILL 兜底路径测试

补测试：spawn 一个 `trap '' TERM; sleep 60` 的子进程作 runner 替身，触发 `ov_cleanup` 的 KILL 升级路径，断言子进程确实被杀。

**改动点**：`sdflow-init/tests/test_outside_voice.py` 新增用例

### D5 · 出境 stdout 大小限制

`do_exec` 的 `cat "$workdir/last-message.md"` 前加检查：

```bash
ov_outsize=$(wc -c 2>/dev/null < "$workdir/last-message.md" | tr -d ' ')
if [ "${ov_outsize:-0}" -gt "$OV_MAX_CONTEXT_BYTES" ]; then
    echo "OV_OUTPUT_TRUNCATED=1 original_bytes=$ov_outsize limit=$OV_MAX_CONTEXT_BYTES" >&2
    head -c "$OV_MAX_CONTEXT_BYTES" "$workdir/last-message.md"
else
    cat "$workdir/last-message.md"
fi
```

复用入境同一个 `OV_MAX_CONTEXT_BYTES`（200KB 默认）。截断按字节、不做 UTF-8 回扫（接受的边角，见 decision-memo）。

**改动点**：`outside-voice.sh:832` 附近

### D6 · 磁盘满测试接缝

`render_prompt` 的 workdir 由外部 `mktemp -d` 创建。测试：

1. 创建 workdir
2. `chmod 500`（不可写）
3. 调用 `do_exec`（会在 workdir 内写文件）
4. 断言 exit 非零 + stderr 含 `render.meta` 为空时的固定诊断行

**改动点**：`sdflow-init/tests/test_outside_voice.py` 或 `test_outside_voice_job.py` 新增用例

## Risks / Trade-offs

- D2 的 `signal.signal` 在 Python 主线程内注册——`cmd_worker` 已在主线程跑，无问题。但 `signal.signal` 会替换 Python 默认的 SIGTERM handler，函数返回后应恢复（`signal.signal(signal.SIGTERM, signal.SIG_DFL)`），否则影响后续代码。
- D5 的字节截断可能劈开多字节字符——影响低（模型输出大概率 ASCII/英文为主），且下游解析做文本匹配非字节验证。

## Decisions

见 [decision-memo.md](decision-memo.md)。
