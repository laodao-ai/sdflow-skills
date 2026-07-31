# Code review · adversarial fix2

审查对象：`align-sdflow-spec-with-openspec-schema`
被审盘面：`7e572fb65d20067876a1f0dbbf982351d3a27380`
范围：fix1 对原子迁移 marker、已有 marker 校验、缺失 `schema:` 插入、兄弟 schema 保留和 inline comment 保留的修复；本复审只读，未修改业务代码或 `code-review-report.md`。

## Findings（置信 ≥80）

### A1 · 高 · CR-02 · 已切到 fork 后新建的在途 change 会让后续 update 失败

- 证据：[`run`](../../../../sdflow-init/scripts/init.py) 在每次版本门通过时固定调用 `migrate_changes(root, BUILTIN_SCHEMA)`；[`migrate_changes`](../../../../sdflow-init/scripts/init.py) 对任何已有 marker 强制要求其 schema 等于 `spec-driven`。
- 运行期路径：首次切换完成后，配置已选择 `sdflow-spec-driven`，随后 `openspec new change` 创建的 change 会依设计生命周期把自身 `.openspec.yaml` 绑定为 `sdflow-spec-driven`。下一次 `sdflow-init update` 仍扫描该在途 change，并把这个正常的当前 schema marker 判为“非法或不匹配”，在 bundle/config 刷新前退出。
- 独立复现：临时项目中创建含 `proposal.md` 与 `schema: sdflow-spec-driven` 的在途 change，执行 `migrate_changes(root, BUILTIN_SCHEMA)`，得到 `RuntimeError: 在途 change 的 schema marker 非法或不匹配`。
- 影响：这是已完成首次安装后必经的正常更新路径，不是畸形输入；它违背迁移“已有绑定者 no-op”的契约，使后续 bundle 更新被完全阻断。
- 建议：迁移仅为缺 marker 的旧 change 补写 `spec-driven`；已有 marker 应做严格可解析校验后保留其实际合法 schema（至少接受内置 `spec-driven` 与项目 fork `sdflow-spec-driven`），而不是在每轮 update 固定要求旧值。相应补充“切换后新建 fork-bound change 再 update”为 no-op 的回归测试。
- 置信：98%。设计的生命周期明确新 change 会钉入 config 选定的 fork；代码与临时执行均直接证实该控制流。

## 已验证的 fix1 项

- 原子 marker 发布与截断/畸形 marker fail-loud：实现使用同目录临时文件、`fsync`、`os.replace`，并对已有内容做单一可解析 schema 校验。
- 缺失顶层 `schema:`：确定性插入，且保留原有换行和其它配置字节；已有行会保留 inline comment 与尾部字节。
- schema 下发：只整删重拷受管的 `sdflow-spec-driven/`，不会删除兄弟 schema。

## 验证

- `python -m pytest -q sdflow-init/tests/test_init.py sdflow-init/tests/test_task5_regression.py` → `67 passed, 1 skipped`，退出码 0。
- `git diff --check` → 通过。
- 全量 `pytest`：按用户明确批准跳过；此前超时退出码为 `124`，本报告不将其记为通过。

## 结论

**BLOCKED。** fix1 已修复前轮的写入与分发问题，但 A1 会在目标态的正常 fork-bound change 上阻断后续 `sdflow-init update`；修复并补回归后需要再次复审。
