## Tasks

skip_specs=true，无 Requirement ID 追溯（纯代码质量修复）。

### 1. T64 · `_atomic_write_settings()` mkstemp 唯一名

- [ ] 1.1 改 `_atomic_write_settings()` 用 `tempfile.mkstemp`，失败时 `os.unlink` 清理残留
- [ ] 1.2 补测试：验证 tmp 文件名非固定（mock `tempfile.mkstemp` 或检查 `os.replace` 被调用时的源路径）
- [ ] 1.3 补测试：mkstemp 失败时返回 False 而非裸抛（mock mkstemp 抛 OSError，断言返回 False）[spec-review-amendment] CR-1

### 2. T149 · `lint_config()` 顶层重复键检测

- [ ] 2.1 新增 `_detect_duplicate_top_keys()` 函数（行级扫描顶层 `key:` 行）
- [ ] 2.2 在 `lint_config()` 中调用，重复键追加 reason
- [ ] 2.3 补测试：构造含重复顶层键的 config.yaml，验证 `lint_config()` 返回非空 reason
- [ ] 2.4 补测试：非 UTF-8 config.yaml 不让 `_detect_duplicate_top_keys` 裸抛（复用现有 F2 fixture）[spec-review-amendment] CR-2
- [ ] 2.5 补测试：BOM config.yaml 首键正确识别 [spec-review-amendment] CR-3

### 3. T6 · `ensure_global_hooks()` Codex 降级告警

- [ ] 3.1 `ensure_global_hooks()` 末尾检测 `~/.codex/` 存在时追加告警行
- [ ] 3.2 补测试：mock `~/.codex/` 存在，验证输出含 `⚠` 告警；不存在时无告警

### 4. 收尾

- [ ] 4.1 全量 pytest 跑绿（`sdflow-init/tests/`）
- [ ] 4.2 关闭 T64、T149、T6（set-status DONE + evidence）

## 测试覆盖图

| 代码路径 | 测试类型 | 覆盖任务 |
|---|---|---|
| `_atomic_write_settings()` mkstemp 路径 | 单元测试（mock mkstemp） | 1.2 |
| `_atomic_write_settings()` mkstemp 失败 → False | 单元测试（mock mkstemp 抛 OSError） | 1.3 |
| `_detect_duplicate_top_keys()` | 单元测试（构造 YAML） | 2.3 |
| `_detect_duplicate_top_keys()` 非 UTF-8 | 单元测试（复用 F2 fixture） | 2.4 |
| `_detect_duplicate_top_keys()` BOM 首键 | 单元测试（BOM YAML） | 2.5 |
| `lint_config()` 重复键 → reason | 集成测试（真 config 文件） | 2.3 |
| `ensure_global_hooks()` Codex 告警 | 单元测试（mock isdir） | 3.2 |
