<!-- sdflow:step1-broad-review v1 mode="native" -->

# Autoplan 广审 — sdflow-init-readwrite-paths

原生执行（autoplan skill 直接在主 session 跑），非子代理模拟。

## CEO Review (Strategy & Scope)

### Premise 评估

1. **T64 前提有效**：`_atomic_write_settings()` L953 确认 `settings + ".tmp"` 固定名 + 无锁降级路径存在（Windows / fcntl 失败），并发撕裂窗口真实。
2. **T149 前提有效**：YAML spec 规定重复键 last-wins，yq 遵循，`lint_config()` 拿到去重后 dict 无法检测。
3. **T6 前提有效**：Codex 无 hook 事件机制（无 `~/.codex/hooks/`），`ensure_global_hooks()` 静默不生效。
4. **T63 WONTDO 充分**：4 仓 grep 证据（`opsx-init` marker 全在 fenced block 外 × 每文件仅 1 对），无真实攻击面。

### Scope 评估

- T64+T149+T6 同文件内聚，一次做完合理（不拆散跨 change）
- T63 WONTDO 有充分论证，non-goal 划定合理
- 无范围膨胀风险

### 结论

Scope 正确，前提有效，修法直接。无 strategic concern。

## Eng Review (Architecture & Code)

### T64 · mkstemp 唯一名

- 修法对齐同文件 `_atomic_write()` L553 已有范例，`tempfile.mkstemp` + `os.fdopen` + 失败时 `os.unlink`
- `os.replace` 语义不变（POSIX + Windows 同卷原子）
- **无 concern**

### T149 · 行级重复键检测

- 正则 `[A-Za-z_][\w-]*:` 覆盖现有顶层键（`schema`, `rules`, `model-tiers`, `metrics`）
- 前置条件正确排除缩进行和注释行
- 空行守卫 `line and` 正确
- 只扫顶层合理（嵌套键重复概率极低）
- **无 concern**

### T6 · Codex 降级告警

- `os.path.isdir("~/.codex")` 检测 Codex 安装
- 仅追加告警行，不改功能
- **注意**：当前 `ensure_global_hooks()` L891-893 是单行 `return "\n".join(...)`，实现时需拆结构以便末尾追加条件告警行
- **低风险 concern**（实现注意事项，非设计问题）

### 测试覆盖图

tasks.md 的测试覆盖图完整，4 条代码路径各有对应测试类型和覆盖任务。

### 结论

三处修法安全、直接，无架构影响。测试计划充分。

## Decision Audit Trail

| # | Phase | Decision | Classification | Principle | Rationale |
|---|-------|----------|---------------|-----------|-----------|
| 1 | CEO | T63 WONTDO | Mechanical | Pragmatic | 4 仓 grep 证据，无真实攻击面 |
| 2 | CEO | Scope=T64+T149+T6 | Mechanical | Completeness | 同文件内聚 |
| 3 | Eng | T64 mkstemp 对齐 | Mechanical | Explicit | 同文件已有范例 |
| 4 | Eng | T149 只扫顶层 | Mechanical | Pragmatic | 嵌套键概率极低 |
| 5 | Eng | T6 仅告警 | Mechanical | Pragmatic | Codex 无等价机制 |

## Status

**DONE** — 0 taste decisions, 0 user challenges, 5 auto-decided (all mechanical)。无 unresolved issues。
