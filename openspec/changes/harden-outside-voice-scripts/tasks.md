## 1. outside-voice.sh 修复

- [ ] 1.1 T176: `--timeout` 校验拒绝 0 — `outside-voice.sh:893` 在 `''|*[!0-9]*)` 后加 `0)` 分支，exit 2
- [ ] 1.2 T230: 出境 stdout 大小限制 — `outside-voice.sh:832` 附近，`cat last-message.md` 前加 `wc -c` 检查 + 超阈值 `head -c` 截断 + stderr 告警 `OV_OUTPUT_TRUNCATED=1`

## 2. outside-voice-job.py 修复

- [ ] 2.1 T227: cmd_worker 信号转发 — `subprocess.call` 改 `Popen` + SIGTERM/SIGINT handler 转发 + 有界等待 + kill 兜底；函数返回前恢复默认 handler

## 3. 测试补全

- [ ] 3.1 T174: fake-timeout 非整数兼容 — 测试桩 `$(( sec * 10 ))` 改支持浮点数（`awk` 或 `printf`）+ 补 sec=0.5 的测试用例
- [ ] 3.2 T173: KILL 兜底路径测试 — spawn `trap '' TERM; sleep 60` 的 stub 进程，触发 ov_cleanup KILL 升级，断言进程被杀
- [ ] 3.3 T178: 磁盘满测试 — 创建 workdir + `chmod 500` 不可写，调用 do_exec，断言 exit 非零 + stderr 含诊断行

## 4. 回归验证

- [ ] 4.1 全量测试通过 — `/usr/bin/python3 -m pytest sdflow-init/tests/` 全绿
