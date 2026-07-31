# Code review · adversarial 镜

审查对象：`align-sdflow-spec-with-openspec-schema`  
盘面：`bed0c093eac91b0e998e0d623f8011c186f00e2e`  
范围：相对 `bf026aa63a8dc6833029e81c9b91f2a91c76152b` 的实现；重点覆盖迁移、版本门、安装刷新与跨平台错误路径。未改业务代码。

## Findings（置信 ≥80）

### A1 · 高 · CR-02 · 迁移写入不是原子的，重试可将在途 change 错切到新 schema

- 证据：[`migrate_changes`](../../../../sdflow-init/scripts/init.py:406) 以 `open(marker, "x")` 后直接 `write()` 写入；后续 [存在性检查](../../../../sdflow-init/scripts/init.py:421) 只看文件是否存在，不校验其内容。
- 可复现：临时目录中模拟 `write()` 已落下 `schema: ` 后抛 `OSError`。首次运行按设计中止；再次调用返回 `0`，保留截断的 `.openspec.yaml`。之后 `run()` 会继续切换 `config.schema`，该 change 会回退到 config 的新 fork，而不是被钉在原 `spec-driven`。
- 影响：这正是迁移步骤要避免的「在途 change 被按新 schema 重解读」；磁盘满、进程中断或网络文件系统写失败时会破坏 P0 的零回归保证。
- 建议：用同目录临时文件写全内容、`fsync` 后 `os.replace`；对已存在 marker 至少校验其 `schema:` 值可解析，异常或截断时 fail-loud，不能把“存在”当作“迁移完成”。
- 置信：99%。**采纳**：直接由控制流和临时目录复现证实，影响的是配置切换前置安全条件。

### A2 · 中 · CR-01 / CR-02 · 缺失 `schema:` 键时更新假报成功，实际不会启用 project-local schema

- 证据：[`handle_config`](../../../../sdflow-init/scripts/init.py:364) 在 update 分支忽略 [`_set_schema_key`](../../../../sdflow-init/scripts/init.py:337) 的布尔返回值；后者在找不到顶层 `schema:` 行时返回 `False`（第 360 行），调用方仍返回 `("updated", ...)`（第 371 行）。
- 可复现：临时 `openspec/config.yaml` 仅含 `context: keep` 时，`handle_config(..., schema="sdflow-spec-driven")` 返回 `updated`，文件字节保持不变。
- 影响：CLI ≥1.7.0 的已有消费仓可拿到 fork 文件，却仍无 `config.schema` 选择该 fork；安装输出会误导用户以为已切换。随后工作流继续使用默认 schema，委派与依赖图下沉均不生效。
- 建议：若找不到唯一顶层键则 fail-loud（最小且不改用户其余内容），或以明确、已测试的插入策略补入该键；无论哪种都必须以 `_set_schema_key()` 成功为前提再报告 `updated`。
- 置信：95%。**采纳**：控制流与复现一致；虽属于异常配置形态，但安装器不能在未完成切换时输出成功。

## 已裁掉 / 不阻断项

- X1 · 旧 CLI 下先前已存在的 `openspec/schemas/` 不会由 `include_schema=False` 删除。置信 76%，**裁掉**：配置会回退到 `spec-driven`，旧目录不会被 CLI 使用；本 change 只承诺不铺新 schema，未承诺为降级环境清理历史安装，不能据此扩大范围。
- X2 · Windows 上 bare `openspec` 解析风险。置信 88%，**裁掉**：版本探测已使用 `shutil.which("openspec") or shutil.which("openspec.cmd")`，覆盖了该宿主的 `.cmd` 入口；未见当前路径仍会调用裸 subprocess 的证据。

## 验证

- 定向回归：`pytest -q sdflow-init/tests/test_init.py sdflow-init/tests/test_task5_regression.py hack/tests/test_task3_phase_c_contract.py` → `65 passed, 1 skipped`。
- 全量 `pytest`：按用户明确批准跳过；此前超时退出码为 `124`，本报告不将其记为通过。

## 结论

**建议：BLOCKED。** A1 会在真实失败/重试路径突破迁移顺序保证；A2 会把未完成配置切换误报为成功。两项修复后需补相应回归用例并复审。
