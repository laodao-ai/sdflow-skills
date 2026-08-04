---
schema_version: 1
change: harden-outside-voice-scripts
branch: feat/harden-outside-voice-scripts
generated_at: "2026-08-04T14:32:51+00:00"
decision_hash: "dd02230da8ec"
---

# 决策纪要 · harden-outside-voice-scripts

## 目标态

修复 outside-voice.sh + outside-voice-job.py 的 6 处正确性/安全缺陷（T176/T227/T174/T173/T230/T178），补对应测试。

## 拍板决策

- **D1 T176 拒绝 timeout=0** — outside-voice.sh:893 的 `--timeout` 校验已排非数字，补排 `0`（GNU timeout `DURATION=0` = 禁用超时 = 进程挂死）。保留 `usage` 退出（exit 2），与既有非法值行为一致。
- **D2 T227 worker 信号转发用 Popen 替代 call** — `cmd_worker` 改 `subprocess.Popen` + 装 SIGTERM/SIGINT handler 转发给子进程 + `proc.wait(timeout)` + `proc.kill()` 兜底。不改 `run_cleanup`（它已有 probe_subtree + claude stop + 子树核验的完整路径）。**砍掉的候选**：(a) 改 `run_cleanup` 加主动 kill runner_pid 路径 — 代价大且 cleanup 已有完整机制；(b) 不改 — 失效面真实（`claude stop` 可能只杀 worker PID 不杀组 → helper 逃逸）。
- **D3 T174 fake-timeout 取整** — 测试桩里 `lim=$(( sec * 10 ))` 在非整数 sec（如 0.5）下 bash 算术错。改用 `awk` 或 `printf '%.0f'` 取整后算。
- **D4 T173 补 KILL 兜底测试** — 用 `trap '' TERM` 的 stub 进程触发 ov_cleanup 的 KILL 升级路径，验证该分支确实执行。
- **D5 T230 出境 stdout 加上限** — `do_exec` 最后 `cat last-message.md` 前 `wc -c` 检查，超 `OV_MAX_CONTEXT_BYTES`（同入境阈值 200KB）时截断 + stderr 警告。**砍掉的候选**：拒绝输出（exit 1）— 丢弃已付费结果不合理，截断 + 警告够了。
- **D6 T178 磁盘满测试接缝** — `render_prompt` 的 workdir 已由 `mktemp -d` 外部创建，测试可通过 `chmod 500` 使其不可写来模拟磁盘满。补测试验证 M3 诊断行确实产出。

## 承重约束

- **C1 outside-voice.sh `--timeout` 校验 MUST 拒绝 0** — 验证方式：改后 `echo exec --context-file /dev/null --timeout 0 | bash outside-voice.sh` 应 exit 2；证据锚：`outside-voice.sh:893-894` 修改点
- **C2 cmd_worker 信号转发 MUST 不改 run_cleanup** — 验证方式：`run_cleanup` 无 diff；证据锚：`outside-voice-job.py:1899` 不动
- **C3 出境截断阈值复用入境 OV_MAX_CONTEXT_BYTES** — 验证方式：代码中 `wc -c` 比较同一个变量；证据锚：`outside-voice.sh:206` 既有定义
- **C4 fake-timeout 补丁 MUST 向下兼容整数 sec** — 验证方式：既有整数 sec 测试不红；证据锚：测试文件

## 接受的边角

- T227 的 worker 信号转发只覆盖 SIGTERM/SIGINT，不覆盖 SIGKILL — 概率：低（`claude stop` 正常路径不发 SIGKILL）；影响：与 outside-voice.sh 自身残余 (a) 同族（shell 层不可干净消除）；完美成本：需要进程组/cgroup 级别控制。简化：只转发可捕获信号够了。
- T230 出境截断不截到字符边界 — 概率：低（模型输出大概率 UTF-8 ASCII）；影响：截断后结尾可能有半个多字节字符，但下游（评审 SKILL 的 findings 解析）做文本解析不做字节验证；完美成本：复用入境 UTF-8 回扫逻辑代价过高（两段代码的 stdout 协议不同）。简化：按字节截 + 告警。

## 三镜代价

本次无 TG-23 命中。
