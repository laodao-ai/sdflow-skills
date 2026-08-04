---
schema_version: "1"
change: sdflow-init-readwrite-paths
branch: feat/sdflow-init-readwrite-paths
generated_at: "2026-08-04T07:00:32Z"
decision_hash: "3c15272a66a1607a"
---

# Decision Memo — sdflow-init-readwrite-paths

## 承重约束

### C1 · T63 WONTDO — inject() fence-aware + 多块收敛无真实场景

- **fence-aware**：4 个消费仓 `opsx-init` marker 全在 fenced block 外面，消费仓 CLAUDE.md 不会在 fence 内示例这些 marker——场景上不会出现（不是"还没出现"）
- **多块收敛**：4 个消费仓每文件仅 1 对 `opsx-init` marker，无多块场景
- **`sync_principles.py` 独立**：通则注入走自己的 `_blocks()` 不经 `inject()`，那边 CLAUDE.md 2 对 `sdflow:principles` marker 已正确处理
- **证据**：`grep -l 'opsx-init:start'` 4 仓 × fence 状态检查全 False + `grep -c` 全 1 对

### C2 · T64 修法确定 — mkstemp 对齐同文件范例

- `_atomic_write_settings()` L953 `settings + ".tmp"` → `tempfile.mkstemp(prefix=".settings-", dir=…)`
- 同文件 `_atomic_write()` L551 已用 `mkstemp`，直接对齐
- 无锁降级路径（Windows / fcntl 失败）仍保持 best-effort，不新增崩溃面（T64 scope 不含 Windows 并发完美解）

### C3 · T149 修法确定 — 行级重复键检测

- yq last-wins 合并后 Python dict 看不到重复键，须在 yq 之前做行级扫描
- 修法：读 config.yaml 原文，行级扫描 `^\s*(\w[\w-]*):\s` 收集键出现次数，>1 即 append reason
- 只扫顶层缩进（indent=0），不解析嵌套——顶层重复是唯一有意义的检测面（`metrics.enabled` 重复属嵌套，yq 同样 last-wins，但嵌套键极少且影响更低，按通则④不做）

### C4 · T6 修法确定 — Codex 降级告警

- Codex 无 hook 事件机制（`~/.codex/` 无 `hooks/` 目录、无 `settings.json`），不是路径遗漏
- 修法：`ensure_global_hooks()` 末尾检测 `~/.codex/` 存在时追加一行告警 `⚠ hook 仅 Claude 侧生效，Codex 会话无 branch-guard`
- 不在 `setup.sh` 层告警（hook 是 init.py owns 的）

## 拍板决策

### D1 · scope = T64 + T149 + T6，T63 WONTDO

B4 原 4 条缩为 3 条。T63 无真实攻击面，WONTDO 并关闭。

### D2 · T149 只扫顶层键

嵌套键重复（如 `metrics.enabled` 出现两次）不做检测——概率极低、影响低、检测成本不对称（要追踪缩进层级）。按通则④可接受的简化。

### D3 · T64 mkstemp 权限收窄可接受 [spec-review-amendment]

`tempfile.mkstemp` 默认创建 0600 文件，`os.replace` 后权限跟源 inode，`settings.json` 会从典型 0644 收窄到 0600。对单用户机器影响极小（owner 自己在用），且 0600 更安全（敏感配置默认收紧权限）。接受此行为变化，不额外 `os.chmod`。
