# Task 2 实现报告：project-local schema 下发与迁移

## 结论

**DONE_WITH_CONCERNS**：Task 2 已实现并完成定点验证；完整 `sdflow-init/tests` 在 120 秒内无输出并超时，按要求停止，未将未完成的全量验证宣称为通过。

## 实现范围

- `sdflow-init/scripts/init.py`
  - 增加 `openspec --version` 的 semver 数值门，最低版本为 `1.7.0`；版本不足、命令失败或输出不可解析时 fail-closed。
  - 版本门通过后，仅扫描 `openspec/changes/*/` 中含 `proposal.md` 的在途 change，给缺失 `.openspec.yaml` 的 change 补写切换前实际 schema；跳过 archive、stray 目录和已有绑定，支持幂等运行。
  - 固化“先迁移、后切配置”的顺序；迁移写入失败会在配置切换前中止。
  - `copy_bundle()` 增加 `openspec/schemas/` 的 rmtree-first 整删重拷，支持旧版 CLI 下不铺 schema。
  - update 模式只原子改写顶层 `schema:` 单行，保留其余 config 字节不变。
- `sdflow-init/assets/workflow/config.template.yaml`
  - `schema:` 默认指向 `sdflow-spec-driven`。
- `sdflow-init/tests/test_init.py`
  - 增加版本门、1.10.0 数值比较、异常/非数字输出、迁移幂等与 archive 隔离、配置窄改、schema 孤儿清理测试。

## TDD 证据

- Red：新增 Task 2 测试在实现前失败，失败集中在 schema 未清理/未部署及版本门测试支撑缺失。
- Green：`pytest sdflow-init/tests/test_init.py -q` → **50 passed, 1 skipped**。
- 相关全量：`pytest sdflow-init/tests -q` → **超时（120 秒，无测试结果输出）**；随后按用户指示停止仍运行的排除慢测命令。
- `git diff --check` → **通过**。

## 约束遵守

- 未修改 `tickets.md`。
- 未创建 task checkpoint commit。
- 仅修改 Task 2 涉及的安装器、配置模板、测试和本报告。
