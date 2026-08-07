### Task 4: ship_gate 腿退役 + 死件清理 + 文档面级订正

**Blocked-by:** 2,3
**R-ID:** R6 (spec-workflow MODIFIED bundle 下发后果), R7 (encoding-hygiene), R8 (yq-yaml-operations), R9 (workflow-metrics)

退役 `ship_gate.py` 的 `tools_spec` 比较腿（正向锚 + 反向锚）。删除本仓 `openspec/workflow/` 下 7 个文件（6 tools + contract）。同批处理两处硬编码引用（yq TARGETS + encoding hygiene 排除分支）。GUIDE 生成器链接降级。托管块权威源 + 本仓 CLAUDE.md/AGENTS.md 非托管区 + ADR + docs + CONTEXT + 修法文案面——全部按 sweep 命中处置。记 todo（4 条，用开发 checkout 脚本、显式传 change 字段）。

- [ ] `ship_gate.py`：删 `tools_spec` 比较腿，退役理由注释按仓型分开写
- [ ] 正向锚：改 `sdflow-init/assets/workflow/tools/` 下文件，失鲜仍为 stale
- [ ] 反向锚：fixture 仓在 `openspec/workflow/tools/` 造文件 → 判 fresh（腿真退役）
- [ ] 删本仓 `openspec/workflow/` 下 7 个文件（只留 GUIDE）
- [ ] `hack/tests/test_yq_wrapper_consistency.py` 删镜像条目
- [ ] `hack/check_encoding_hygiene.py` 删不可达排除分支 + 测试改写
- [ ] 托管块权威源 `claude-section.md` 订正 + 对本仓跑 `sdflow-init update` 刷新
- [ ] `CLAUDE.md` 非托管区四处订正 + `AGENTS.md` 四处同义描述订正
- [ ] 修法文案面统一口径（lens_metric_emit / resolve-models / sdflow-upgrade / README）
- [ ] docs 面按 sweep 命中处置
- [ ] ADR 面：0003/0005/0019/0036 状态注记 + 0038 删除 + 0039 新落（含回滚步骤）
- [ ] `openspec/CONTEXT.md` 补 skew 术语 + T269 分治关闭 + T270 关闭
- [ ] `hack/gen_workflow_guide.py` 链接降级 + 重新生成 GUIDE
- [ ] 记 4 条 todo（hack 链 symlink 化 / resolver --help / setup.sh skipped 非零退出 / Windows 失鲜 CI）

