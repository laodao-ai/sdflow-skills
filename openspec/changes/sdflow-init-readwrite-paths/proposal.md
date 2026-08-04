## Why

`sdflow-init/scripts/init.py` 有三个读写路径缺陷（issues-triage B4 批）：settings.json 原子写用固定名 tmp 文件在无锁降级时可撕裂（T64），config.yaml lint 检测不到 YAML 重复键（T149），hook 安装仅 Claude 侧、Codex 会话静默不生效（T6）。三条同一文件、改动面内聚，一次做完。

## What Changes

- **T64**：`_atomic_write_settings()` 的 tmp 文件从固定名 `<settings>.tmp` 改为 `tempfile.mkstemp` 唯一名，关闭无锁降级路径下的并发撕裂窗口
- **T149**：`lint_config()` 在 yq 解析之前增加行级顶层键重复检测，对 last-wins 静默合并的重复键发出告警
- **T6**：`ensure_global_hooks()` 检测 `~/.codex/` 存在时打印降级告警，消除 Codex 会话下 branch-guard 静默不生效的信息盲区

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。本次改动是纯代码质量修复（防御深度提升），不改变任何 spec 级行为。`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- **代码**：`sdflow-init/scripts/init.py` 三处函数
- **测试**：`sdflow-init/tests/` 需补对应用例（mkstemp 验证、重复键检测、Codex 告警）
- **依赖**：无新增依赖（`tempfile` 已在标准库）
- **下游**：消费仓行为无变化；仅 `sdflow-init update` 运行时日志多一行 Codex 告警（条件触发）

## Success Metrics

- T64：`_atomic_write_settings()` 使用 `mkstemp` 唯一名，测试验证 tmp 文件名不固定
- T149：`lint_config()` 对含重复顶层键的 config.yaml 返回非空 reason，测试覆盖
- T6：存在 `~/.codex/` 时 `ensure_global_hooks()` 输出含 `⚠` 告警，测试覆盖

## Non-Goals

- T63（inject fence-aware + 多块收敛）：已 WONTDO——无真实攻击面
- Windows 并发完美解（T64 scope 不含）
- 嵌套键重复检测（T149 只扫顶层）
- Codex hook 等价实现（T6 只做告警，Codex 无 hook 机制）

## Compliance

N/A
