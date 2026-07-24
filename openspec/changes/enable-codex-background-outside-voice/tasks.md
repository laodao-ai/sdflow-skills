## 1. Background Job Helper

- [ ] 1.1 **[grill-amendment]** 先为 `outside-voice-job.py` 建立 CLI/shape 测试，覆盖 `preflight/dispatch/status/await/collect/cleanup/reconcile/worker` 子命令、Claude `2.1.169+` 版本解析、agents JSON 顶层解析、已安装 helper/data capability manifest、受支持 POSIX shell、非法 timeout/site/path 与 `disableAgentView`/dispatch 失败的快速诚实降级；preflight 负向 golden 必须证明不会执行 `--bg --exec 'true'` 或创建任何 dummy job，再实现参数与 repo/run-dir 边界校验。**[spec-review-amendment]**〔OVBG-01, OVBG-02〕
- [ ] 1.2 **[spec-review-amendment]** 实现 dispatch/worker：任何外部副作用前以 `O_CREAT|O_EXCL` reserve 并机械限制同 run 最多两个站点；v1 仅在已验证 POSIX shell 用 `shlex.join`/等价 quoting 构造唯一 `claude --bg --exec` 命令，设置 monotonic 5 秒 deadline，解析并核验 canonical id/session id，atomic 写含 attempt/runner/model/effort/platform 的 `<site>.job.json`。worker 第一动作发布 started/process-tree identity，调用同一 `outside-voice.sh exec` 并将自身/child 输出直接重定向至 0600 文件，最后发布 terminal witness 与纯十进制 rc。补同 site/第三站点拒绝、两站点隔离、dispatch→metadata 崩溃与挂起 dispatch 进程树回收测试。〔OVBG-01, OVBG-02〕
- [ ] 1.3 **[spec-review-amendment]** 实现 status/await/collect 的状态笛卡尔：rc=0+非空、124、其他码、坏 rc、空 stdout、agent working/done/failed/stopped/missing、job JSON 缺字段/schema drift；终态前不读 stdout。startup deadline 独立；worker deadline 从可信 `started_at` 起算，started+timeout+30 秒无 rc 才归失联。只允许真实 124 归 timeout；collect 幂等返回 dispatch/start/terminal/collect 时刻、自然 duration、model/effort 与 stdout digest。〔OVBG-02, OVBG-03, HAE-09〕
- [ ] 1.4 **[spec-review-amendment]** 实现可重入 collect、显式 `reconcile --run-dir` 与 identity-safe cleanup：同一主评审 session 的 await 中断后按保留的 exact job/run-dir 恢复，不得重派；整个 session 丢失时禁止猜“最新 run”。terminal collect 后核验 identity 再 `claude rm`；取消/失联按 stop→核验 worker/inner child 子树退出→rm，无法核验时落 `unknown-cost/orphan-warning` 并抑制自动 fallback。〔OVBG-03, OVBG-05〕

## 2. Runner Isolation and Safety

- [ ] 2.1 **[grill-amendment]** 先扩充 `sdflow-init/tests/test_outside_voice.py` 的 Claude argv golden，再给 `outside-voice.sh` Claude 分支增加 `--effort high --safe-mode --no-session-persistence` 并升级 helper 版本；模型继续只取 `SDFLOW_VOICE_MODEL`（Claude strong，目标仓解析为 `opus`），四旗、stdout/rc、FRAME、两次 secret scan 与 200KB 截断必须保持同源。〔OVBG-04, HAE-09〕
- [ ] 2.2 增加 safe-mode 真机/可替身回归：SessionStart hooks/plugins/skills/memory 不执行，显式 read-fence 仍拒凭证路径，只读工具精确为 `Read,Grep,Glob`；失败 stderr 仅留 gitignored run-dir，tracked 报告只可写 rc/行数/字节数。〔OVBG-04〕
- [ ] 2.3 **[spec-review-amendment]** 对 background worker 的 context/run-dir/site/model/timeout 做注入与越界攻击测试，证明 NUL/换行、仓外路径、重复 site、shell 元字符不能改写命令或越出本轮目录；非 POSIX 平台 fail-closed。用真实 `claude logs <id>` canary 回归证明 context、partial stdout、stderr、fake secret 不进入 supervisor transcript/state；job/output 文件权限为 0600。〔OVBG-02, OVBG-04〕

## 3. Host-Adaptive Review Orchestration

- [ ] 3.1 **[grill-amendment]** 同步修改 `sdflow-spec-review/SKILL.md` 与 `sdflow-code-review/SKILL.md` 的 `sdflow:async-branch` 等值段：Claude-host 保留 harness async；Codex-host preflight ready 走 job helper async；不可用时 5 秒级同族 fallback，删除 Codex sync 300 秒路径，并加负向 golden 证明 marker 段不再含该兼容分支。〔HAE-08〕
- [ ] 3.2 **[spec-review-amendment]** 把 Codex dispatch 的 CLI job id、site 与 attempt nonce 追加 `dispatch-manifest.tsv`，在 Step3 用 job helper 的有界 await/collect；逐站点按 rc 映射 `ok/timeout/exec-error/secret-hit`，RUNNING 不早退、外层 wait 回收后不重派、stderr 不进 findings/报告。〔OVBG-03, HAE-09〕
- [ ] 3.3 更新调度协议中的执行模式矩阵、timeout 解析、preflight/actionable 文案、站点↔任务记账与 cleanup 纪律；跑 `hack/check_async_branch_parity.py` 证明两 SKILL marker 段逐字节一致，并保留 `declared-sites` 公式与 anchor 合法组合矩阵不变。〔HAE-08, HAE-09, OVBG-05〕

## 4. Installation and Compatibility

- [ ] 4.1 **[spec-review-amendment]** 修改 `setup.sh`：把 job helper、shell helper与所需 data file 作为带同一 capability manifest/hash 的兼容快照原子安装到 `~/.sdflow/`；补执行权限/解释器、安装中断、新旧混配与 stale-copy 测试。运行 `bash setup.sh` 后从临时 `SDFLOW_HOME` 的已安装路径验证完整 lifecycle，任一 skew preflight fail-closed。〔OVBG-01〕
- [ ] 4.2 **[grill-amendment]** 更新 canonical workflow/使用说明和版本 skew 探测，明确 Claude Code 最低 `2.1.169`（共同能力下限）、agent view 被策略禁用的修法、`--exec` 是本机验证的 research-preview 形态、v1 POSIX 支持边界及旧版本/未验证平台快速 fallback；明确 `bash ~/.skills/sdflow-skills/setup.sh` 刷新全局 helper/SKILL，`sdflow-init update` 只刷新消费仓 workflow tools。**[spec-review-amendment]**〔OVBG-01, HAE-08〕

## 5. Test Matrix and Regression Gates

- [ ] 5.1 **[spec-review-amendment]** 完成 fake `claude` + fake `outside-voice.sh` 单元测试：dispatch ≤5 秒与挂起回收、canonical/session id 解析、reserve/job/started/terminal/rc 原子证据、两站点并发与第三站点拒绝、dispatch→metadata 崩溃、延迟启动、所有 rc/liveness 组合、await/reconcile 恢复、stop 后 child 仍活、identity-safe rm、schema drift 与无假 `ok`。〔OVBG-01, OVBG-02, OVBG-03, OVBG-05〕
- [ ] 5.2 **[spec-review-amendment]** 增加从已安装快照运行的无模型真集成 smoke：`claude --bg --exec` 托管一个跨发起 shell 生命周期的可控 worker，验证 `claude agents --all --json`、sidecar、collect、cleanup 及 `claude logs` 无 payload/secret canary；该 smoke 只证明编排，不得替代真实模型 efficacy 证据。〔OVBG-01, OVBG-03, OVBG-04, OVBG-05〕
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

- [ ] 6.1 **[grill-amendment]** 在安装新 canonical tools 后，以 Codex 宿主对 `zhws_ops_api` 跑至少一轮 `opus` + `high` 的真实 spec-review/code-review；实际 dispatch 的全部站点必须取得 `host="codex" runner="claude" reason_code="ok"`。**[spec-review-amendment]** 报告必须落不含 context/stderr 的结构化 efficacy 证据（runner/model/effort、dispatch/start/terminal/collect 时刻、自然 duration、stdout digest），并由确定性检查器判定。〔OVBG-01, OVBG-03, HAE-08, HAE-09〕
- [ ] 6.2 **[grill-amendment]** 该完整层必须至少含一个 `opus` + `high` 的真实 Claude 推理自然耗时 >300 秒并成功，证明跨过旧天花板；sleep/shim、无模型命令或短调用不得替代。若全部自然短于 300 秒，只能记“功能可用、原失效窗口未复现”，不得关闭 efficacy 缺口。〔OVBG-01, HAE-08〕
- [ ] 6.3 **[grill-amendment]** 仅当 6.1/6.2 同时达标且确定性 evidence checker 通过后关闭 T162，更新相关 design/CONTEXT/hand-off 里的“Codex efficacy=0”陈述；若任一站点未可信 collect/未 `ok`、没有自然 >300 秒成功证据或证据字段不可机读，则保留 T162 并如实记录，不得以编排 smoke 假绿。**[spec-review-amendment]**〔HAE-08, HAE-09〕
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
