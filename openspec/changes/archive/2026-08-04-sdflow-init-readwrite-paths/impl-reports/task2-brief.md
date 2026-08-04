### Task 2: T149 顶层重复键检测

**Blocked-by:** none
**R-ID:** —

在 `lint_config()` 中 `_yq` 调用之前增加行级顶层键重复检测。新增 `_detect_duplicate_top_keys()` 函数，行级扫描 config.yaml 缩进=0 的 `key:` 行，返回重复键列表。重复键追加 lint reason，告警 yq last-wins 静默合并。

- [ ] 新增 `_detect_duplicate_top_keys()` 函数（行级扫描，encoding=utf-8-sig，except (OSError, UnicodeDecodeError)）
- [ ] 在 `lint_config()` 的 `_yq` 调用之前调用，重复键追加 reason
- [ ] 测试：构造含重复顶层键的 config.yaml，验证 `lint_config()` 返回含「重复」的 reason
- [ ] 测试：非 UTF-8 config.yaml 不让 `_detect_duplicate_top_keys` 裸抛
- [ ] 测试：BOM config.yaml 首键正确识别

