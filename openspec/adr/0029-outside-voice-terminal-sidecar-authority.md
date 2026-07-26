# 0029 · Outside Voice 后台终态以 atomic rc sidecar 为权威

> **[grill-amendment] Status: accepted** · 关联 change：`enable-codex-background-outside-voice`

Outside Voice 后台作业只以 worker 最后原子发布的 `<site>.rc` 决定终态语义：`rc=0 + 非空 stdout` 才成功，`rc=124` 才是 timeout，其他 rc 为失败；supervisor 状态只提供 liveness。真机反例中 `exit 7` 与 `exit 124` 都被 `claude agents --json` 压成 `failed`，作业退出后 `claude logs` 还可能因 control socket 消失而不可读，因此从 agent state、summary、transcript 或 logs 推断 `ok/timeout` 会制造假信心。worker 在 child 退出与 rc 发布之间崩溃时诚实落 LOST/exec-error，不用猜测或自动重派补偿这个极窄窗口。
