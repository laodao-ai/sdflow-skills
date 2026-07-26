# 0028 · Outside Voice 后台执行复用 Claude supervisor 托管现有 helper

> **[grill-amendment] Status: accepted** · 关联 change：`enable-codex-background-outside-voice`

Codex-host 的 Claude Outside Voice 采用 Claude Code ≥2.1.169 的 `claude --bg --exec` 托管现有 `outside-voice.sh exec`，不改用交互式 background agent，也不自建常驻 daemon。**[grill-amendment] 2.1.169 是 background exec、safe mode 与当前 agents JSON 的共同能力下限。**真实探针已证明 dispatch 快返、后台环境不继承 `CLAUDECODE=1`，并能在后台 shell 内成功启动嵌套 `claude -p`；此路线因此保留既有 secret scan、read-fence、stdout 与退出码契约，同时避免依赖私有 transcript/TUI 日志。代价是依赖 research-preview supervisor；能力不可用时必须快速同族 fallback，而不是回到已被 5/5 rc124 证伪的同步 300 秒路径。

## Considered Options

- `claude --bg '<prompt>'`：弃选，因为结果只能从 agent transcript/logs 回收，稳定结构化契约不足。
- 自建 launchd/systemd daemon：弃选，因为跨平台安装、存活与清理面远大于目标所需。
- 同步等待 900 秒：弃选，因为只抬高超时上限，没有解除主评审关键路径阻塞与外层 shell 回收风险。
