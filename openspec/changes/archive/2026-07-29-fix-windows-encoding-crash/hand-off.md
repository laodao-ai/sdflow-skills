# Hand-off: fix-windows-encoding-crash

## ✅ 完成了什么

- 为 29 个 Python CLI 入口建立并接入编码前导机械门；`python hack/check_encoding_hygiene.py` 通过，入口枚举与负向/边界回归见 `hack/tests/test_encoding_hygiene.py`。
- 为 16 个文本模式 subprocess 站点补齐显式 UTF-8 解码与替换容错；其中 `_scan_pool` 动态 kwargs 站点由真实 cp936 sweep 暴露并由 `test_reindex_nested_scan_decodes_child_json_as_utf8` 守护。
- Windows workflow 覆盖 GBK setup、已铺设 probe 的 init→update、cp936 console 与重定向输出；`chcp.com 936`、fail-closed console checker 和重定向日志 grep 的连续顺序由常驻测试锁定。
- 最终源码锚为 `867c97566ca9990d55015ced7bf2ccf5ad1605ba`；Task 5 聚合报告在该 SHA 记录 19 passed，终验报告 frontmatter 为 PASS，reviewed SHA 为 `49a7f388d7586e93c27b11899c54ff7018fc0fac`。

## ⚠️ 未完成 / 延后项

- 全量 pytest 在本机 Windows / Python 3.14 仍有 2 项收集错误；相关文件相对本地 `main` merge-base 未变化，归类为既有兼容性缺口，不是本 change 回归。
- 远端 `windows-latest` 尚未实际执行，平台 e2e 如实记为未覆盖；本机 Windows Git Bash 的承重命令与 cp936 调用链已实跑。
- 本 change 新增的非阻断改进项已归入批次 `fix-windows-encoding-crash`：见 `openspec/issues/batches.md` 与 `openspec/issues/INDEX.md`（当前成员 T263）。

## ▶ 下一阶段建议

- Roadmap 助手返回 `NO_ASSOCIATION`（exit 3）：本 change 未声明 roadmap 关联且名称无 roadmap 前缀，因此无回填草稿。
- 后续可单独处理批次 `fix-windows-encoding-crash`；不要把该预存 setup interpreter 一致性问题扩回本 change。
