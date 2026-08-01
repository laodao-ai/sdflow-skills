### Task 2: anchor_lint.py 的 YAML 解析改为 yq

**Blocked-by:** none
**R-ID:** R3, R7, R9, R10

两份 `anchor_lint.py`（`openspec/workflow/tools/anchor_lint.py` 与 `sdflow-init/assets/workflow/tools/anchor_lint.py`）的 `read_metrics_enabled` 函数替换为 `_yq('.metrics.enabled', config_path, default=False)`。新增 `_yq()` 薄封装（含身份校验 + fail-loud）。删除被替代的手搓 YAML 读取代码。同步更新零依赖声明注释。两份副本保持字节一致。

- [ ] `read_metrics_enabled` 改为通过 `_yq()` 读取
- [ ] `_yq()` 封装含 `shutil.which` 检测 + `--version` 身份校验 + 进程内缓存 + fail-loud
- [ ] 两份 `anchor_lint.py` 副本字节一致
- [ ] `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py` 全绿
- [ ] 零依赖声明注释已更新

