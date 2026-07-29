# Code review fix 1

[impl-review-fix] 已落实三项 confirmed finding：

- 通过正式 `python3 sdflow-init/scripts/init.py update --root .` 将 canonical
  `trivial_shape.py` 同步到 dogfood mirror；新增 `TestUpdateDev` 回归断言，确保
  `update --dev` 后该工具与 canonical 内容完全一致。
- Windows forced-GBK 的 setup smoke 保留原有异常输出断言，并直接运行
  `python3 hack/check_encoding_hygiene.py`；编码契约违规将令 CI job 失败。
- 移除 `docs/drafts/20260712.md` 尾部两个空白行，未改正文。

## 验证

- `python3 -m pytest -q hack/tests/test_encoding_hygiene.py sdflow-init/tests/test_init.py::TestUpdateDev::test_dev_update_deploys_full_bundle -W error` → `9 passed`
- `python3 hack/check_encoding_hygiene.py` → 通过
- `git diff --check` → 通过
