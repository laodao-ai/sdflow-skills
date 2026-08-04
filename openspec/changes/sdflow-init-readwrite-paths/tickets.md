---
impl-pipeline: tickets
---

## Global Constraints

- 三处修复均在 `sdflow-init/scripts/init.py` 既有函数内部，**不改公开接口、不改文件格式、不引入新依赖**
- `_atomic_write_settings()` 的 fail-safe 契约（OSError → 返回 False，绝不中止 retire_hooks 循环 / setup.sh）**MUST** 保持
- `tempfile` 已在标准库，是唯一新 import（若尚未导入）
- `_detect_duplicate_top_keys()` 用 `encoding="utf-8-sig"` 处理 BOM（对齐同文件 `_schema_from_config()`）
- `_detect_duplicate_top_keys()` 捕获 `(OSError, UnicodeDecodeError)`——后者不是 OSError 子类
- T6 告警文案**弱化**：「检测到 Codex 环境，如使用 Codex 会话请注意：hook 仅 Claude 侧生效」
- mkstemp 默认 0600 权限收窄**已接受**（D3），不额外 `os.chmod`
- 测试在 `sdflow-init/tests/` 下，用 pytest 跑

### Task 1: T64 mkstemp 唯一名修复

**Blocked-by:** none
**R-ID:** —

将 `_atomic_write_settings()` 的 tmp 文件从固定名 `<settings>.tmp` 改为 `tempfile.mkstemp` 唯一名，关闭无锁降级路径下的并发撕裂窗口。mkstemp **MUST** 在外层 `try` 内（CR-1：mkstemp 底层 `open(O_CREAT|O_EXCL)` 权限拒绝/只读/满盘时抛 OSError，放在 try 外会击穿 fail-safe 契约）。内层 `try/except BaseException` 确保 mkstemp 成功后的残留 tmp 被清理。加 `flush()` + `os.fsync()` 对齐 `_atomic_write()` 风格（CR-7）。

- [ ] `_atomic_write_settings()` 使用 `tempfile.mkstemp` 替代固定名 tmp，mkstemp 在外层 try 内
- [ ] 测试：验证 tmp 文件名非固定（mock mkstemp 或检查 os.replace 被调用时的源路径前缀）
- [ ] 测试：mkstemp 失败时返回 False 而非裸抛（mock mkstemp 抛 OSError，断言返回 False）

### Task 2: T149 顶层重复键检测

**Blocked-by:** none
**R-ID:** —

在 `lint_config()` 中 `_yq` 调用之前增加行级顶层键重复检测。新增 `_detect_duplicate_top_keys()` 函数，行级扫描 config.yaml 缩进=0 的 `key:` 行，返回重复键列表。重复键追加 lint reason，告警 yq last-wins 静默合并。

- [ ] 新增 `_detect_duplicate_top_keys()` 函数（行级扫描，encoding=utf-8-sig，except (OSError, UnicodeDecodeError)）
- [ ] 在 `lint_config()` 的 `_yq` 调用之前调用，重复键追加 reason
- [ ] 测试：构造含重复顶层键的 config.yaml，验证 `lint_config()` 返回含「重复」的 reason
- [ ] 测试：非 UTF-8 config.yaml 不让 `_detect_duplicate_top_keys` 裸抛
- [ ] 测试：BOM config.yaml 首键正确识别

### Task 3: T6 Codex 降级告警

**Blocked-by:** none
**R-ID:** —

`ensure_global_hooks()` 末尾检测 `~/.codex/` 存在时追加告警行，消除 Codex 会话下 branch-guard 静默不生效的信息盲区。告警文案弱化（CR-5）。

- [ ] `ensure_global_hooks()` 末尾检测 `os.path.isdir(~/.codex/)` 时追加告警行
- [ ] 测试：mock `~/.codex/` 存在，验证输出含 `⚠` 告警；不存在时无告警

### Task 4: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落
`impl-reports/task4-verify-aggregate.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

- [ ] 单元测试证据齐全并通过
- [ ] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
