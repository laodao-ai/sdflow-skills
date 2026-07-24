# 0030 · Codex-host 后台能力失败不再同步等待 Claude

> **[grill-amendment] Status: accepted** · 关联 change：`enable-codex-background-outside-voice`

Codex-host 在 Claude background-exec 能力不满足或 dispatch 失败时，须在 5 秒级立即派同族 fresh Codex fallback，不再进入同步 Claude 300 秒兼容分支。`zhws_ops_api` 的目标真实负载已有五个站点全部 rc124 的证据，保留该分支只会在 fallback 前追加确定性等待；Claude Code ≥2.1.169 又已被定为 background 路径的支持下限 **[grill-amendment]**，旧版不应靠已证低效的同步执行伪装受支持。代价是旧版 CLI 在小型仓库中可能失去一次 300 秒内成功的机会；换取的是一致、可预测且如实标注的降级行为。Claude-host → Codex 的既有同步兼容分支不在本 ADR 范围内。
