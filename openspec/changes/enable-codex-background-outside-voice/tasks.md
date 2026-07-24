## 1. Background Job Helper

- [ ] 1.1 **[grill-amendment]** 先为 `outside-voice-job.py` 建立 CLI/shape 测试，覆盖 `preflight/dispatch/status/await/collect/cleanup/worker` 子命令、Claude `2.1.169+` 版本解析、agents JSON 顶层解析、非法 timeout/site/path 与 `disableAgentView`/dispatch 失败的快速诚实降级；preflight 负向 golden 必须证明不会执行 `--bg --exec 'true'` 或创建任何 dummy job，再实现参数与 repo/run-dir 边界校验。〔OVBG-01, OVBG-02〕
- [ ] 1.2 实现 dispatch/worker：以 argv + `shlex.quote` 构造唯一 `claude --bg --exec` worker 命令，解析并核验唯一 short id/session id，atomic 写 `<site>.job.json`，worker 调同一 `outside-voice.sh exec` 并以 0600 权限写 stdout/stderr、最后 atomic 发布纯十进制 rc。补同 site 重复派发拒绝与两站点隔离测试。〔OVBG-01, OVBG-02〕
- [ ] 1.3 实现 status/await/collect 的状态笛卡尔：rc=0+非空、124、其他码、坏 rc、空 stdout、agent working/done/failed/stopped/missing、job JSON 缺字段/schema drift；终态前不读 stdout，deadline+30 秒无 rc 归 `exec-error`，只允许真实 124 归 timeout。〔OVBG-02, OVBG-03, HAE-09〕
- [ ] 1.4 实现可重入 collect 与 cleanup：外层 await 中断后按相同 job/run-dir 恢复、不得重派；terminal collect 后 `claude rm`，取消/失联先 stop 后 rm，cleanup 失败显式保留 short id 且不改写已取得结果。〔OVBG-03, OVBG-05〕

## 2. Runner Isolation and Safety

- [ ] 2.1 **[grill-amendment]** 先扩充 `sdflow-init/tests/test_outside_voice.py` 的 Claude argv golden，再给 `outside-voice.sh` Claude 分支增加 `--effort high --safe-mode --no-session-persistence` 并升级 helper 版本；模型继续只取 `SDFLOW_VOICE_MODEL`（Claude strong，目标仓解析为 `opus`），四旗、stdout/rc、FRAME、两次 secret scan 与 200KB 截断必须保持同源。〔OVBG-04, HAE-09〕
- [ ] 2.2 增加 safe-mode 真机/可替身回归：SessionStart hooks/plugins/skills/memory 不执行，显式 read-fence 仍拒凭证路径，只读工具精确为 `Read,Grep,Glob`；失败 stderr 仅留 gitignored run-dir，tracked 报告只可写 rc/行数/字节数。〔OVBG-04〕
- [ ] 2.3 对 background worker 的 context/run-dir/site/model/timeout 做注入与越界攻击测试，证明 NUL/换行、仓外路径、重复 site、shell 元字符不能改写命令或越出本轮目录；job/output 文件权限为 0600。〔OVBG-02, OVBG-04〕

## 3. Host-Adaptive Review Orchestration

- [ ] 3.1 **[grill-amendment]** 同步修改 `sdflow-spec-review/SKILL.md` 与 `sdflow-code-review/SKILL.md` 的 `sdflow:async-branch` 等值段：Claude-host 保留 harness async；Codex-host preflight ready 走 job helper async；不可用时 5 秒级同族 fallback，删除 Codex sync 300 秒路径，并加负向 golden 证明 marker 段不再含该兼容分支。〔HAE-08〕
- [ ] 3.2 把 Codex dispatch short id 追加 `dispatch-manifest.tsv`，在 Step3 用 job helper 的有界 await/collect；逐站点按 rc 映射 `ok/timeout/exec-error/secret-hit`，RUNNING 不早退、外层 wait 回收后不重派、stderr 不进 findings/报告。〔OVBG-03, HAE-09〕
- [ ] 3.3 更新调度协议中的执行模式矩阵、timeout 解析、preflight/actionable 文案、站点↔任务记账与 cleanup 纪律；跑 `hack/check_async_branch_parity.py` 证明两 SKILL marker 段逐字节一致，并保留 `declared-sites` 公式与 anchor 合法组合矩阵不变。〔HAE-08, HAE-09, OVBG-05〕

## 4. Installation and Compatibility

- [ ] 4.1 修改 `setup.sh` 以原子安装 `sdflow-init/assets/hack/*.py` 到 `~/.sdflow/hack/`，补 source/installed hash、执行权限/解释器与 stale-copy 测试；运行 `bash setup.sh` 后验证 `outside-voice-job.py preflight` 与现有 shell helper 同时可用。〔OVBG-01〕
- [ ] 4.2 **[grill-amendment]** 更新 canonical workflow/使用说明和版本 skew 探测，明确 Claude Code 最低 `2.1.169`（共同能力下限）、agent view 被策略禁用的修法、research-preview/机器睡眠边界及旧版本快速 fallback；下游只经 `sdflow-init update` 分发。〔OVBG-01, HAE-08〕

## 5. Test Matrix and Regression Gates

- [ ] 5.1 完成 fake `claude` + fake `outside-voice.sh` 单元测试：dispatch ≤5 秒、short/session id 解析、atomic job/rc、两站点并发、所有 rc/liveness 组合、await 恢复、stop/rm、schema drift 与无假 `ok`。〔OVBG-01, OVBG-02, OVBG-03, OVBG-05〕
- [ ] 5.2 增加无模型真集成 smoke：`claude --bg --exec` 托管一个跨发起 shell 生命周期的可控 worker，验证 `claude agents --all --json`、sidecar、collect、cleanup；该 smoke 只证明编排，不得替代真实模型 efficacy 证据。〔OVBG-01, OVBG-03, OVBG-05〕
- [ ] 5.3 跑并记录 `pytest sdflow-init/tests/test_outside_voice*.py hack/tests/test_async_branch_parity.py`、`python3 hack/check_async_branch_parity.py`、`python3 hack/sync_principles.py --check`、`git diff --check`，再跑全量 `pytest`；任一既有四旗/secret/child-lifecycle/anchor golden 回归即阻塞。〔OVBG-04, HAE-09〕

### Test Coverage Map

```text
Codex dispatch codepath
├─ version/capability gate ── unit + fake CLI + old/disabled negative
├─ --bg --exec lifecycle ─── unit + no-model real supervisor smoke
├─ worker terminal publish ─ unit + rc/liveness Cartesian matrix
├─ await/collect recovery ── interruption + deadline + lost-job integration
├─ security boundary ─────── argv golden + secret/read-fence/injection tests
├─ two-site concurrency ──── isolated-file + duplicate-dispatch tests
└─ review integration ────── parity/anchor tests + zhws_ops_api real >300s smoke
```

## 6. Real Efficacy and Closure

- [ ] 6.1 **[grill-amendment]** 在安装新 canonical tools 后，以 Codex 宿主对 `zhws_ops_api` 跑至少一轮 `opus` + `high` 的真实 spec-review/code-review；实际 dispatch 的全部站点必须取得 `host="codex" runner="claude" reason_code="ok"`，并记录 dispatch/terminal/collect 三时刻与单条 shell 时长。〔OVBG-01, OVBG-03, HAE-08, HAE-09〕
- [ ] 6.2 **[grill-amendment]** 该完整层必须至少含一个 `opus` + `high` 的真实 Claude 推理自然耗时 >300 秒并成功，证明跨过旧天花板；sleep/shim、无模型命令或短调用不得替代。若全部自然短于 300 秒，只能记“功能可用、原失效窗口未复现”，不得关闭 efficacy 缺口。〔OVBG-01, HAE-08〕
- [ ] 6.3 **[grill-amendment]** 仅当 6.1/6.2 同时达标后关闭 T162，更新相关 design/CONTEXT/hand-off 里的“Codex efficacy=0”陈述；若任一站点未可信 collect/未 `ok` 或没有自然 >300 秒成功证据，则保留 T162 并如实记录，不得以编排 smoke 假绿。〔HAE-08, HAE-09〕
- [ ] 6.4 运行 `openspec validate enable-codex-background-outside-voice --strict` 与 repo 规定的最终检查，确认 source change 只包含本 change 授权范围，且下游 `zhws_ops_api` 没有被直接手改 canonical workflow 规则。〔OVBG-01, OVBG-04, HAE-09〕

## 7. Requirement Traceability

| Requirement | 实现任务 | 验证任务 |
|---|---|---|
| OVBG-01 | 1.1, 1.2, 4.1, 4.2 | 5.1, 5.2, 6.1, 6.2, 6.4 |
| OVBG-02 | 1.1, 1.2, 1.3, 2.3 | 5.1 |
| OVBG-03 | 1.3, 1.4, 3.2 | 5.1, 5.2, 6.1 |
| OVBG-04 | 2.1, 2.2, 2.3 | 5.3, 6.4 |
| OVBG-05 | 1.4, 3.3 | 5.1, 5.2 |
| HAE-08 | 3.1, 3.3, 4.2 | 6.1, 6.2, 6.3 |
| HAE-09 | 1.3, 2.1, 3.2, 3.3 | 5.3, 6.1, 6.3, 6.4 |
