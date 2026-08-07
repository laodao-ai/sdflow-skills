### Task 2: resolver 收缩两步链 + 停铺 tools + 退役 --dev/full

**Blocked-by:** 1
**R-ID:** R2 (spec-workflow MODIFIED 规则解析), R3 (spec-workflow MODIFIED bundle 下发)

P0 核心：在 bundle 权威源 `sdflow-init/assets/hack/resolve-workflow.sh` 删除步①（本地 pin 判定），使规则解析只剩两步链（全局 canonical → 显式降级）。同批在 `sdflow-init/scripts/init.py` 删除 `copy_bundle` 的 tools/contract 铺设逻辑（只保留 GUIDE + schema）、退役 `--dev` 与 `full=True` 分支（`--dev` 留 tombstone fail-loud）。`sane()` 扩面追加 `tools/` 非空 + contract 非空两条形状级检查。配套测试全面改写——以 `pytest` 实跑红名单为准。

- [ ] 删除 resolver 步①（本地 pin 判定），头部契约注释同批订正为两步链
- [ ] 确认退出码集不变（0/2/64），`--root`/`--explain`/`SDFLOW_HOME` 入参契约保留
- [ ] `sane()` 扩面：`tools/` 存在且非空 + `lens-metric-contract.md` 非空（形状级，不枚举 `.py` 成员）
- [ ] `init.py` `copy_bundle()`：删 tools/contract 铺设，只保留 GUIDE + schema；GUIDE `copy2` 前加 `os.makedirs(dst, exist_ok=True)`
- [ ] 退役 `--dev` argparse + toolkit 仓根守卫 + `stale_shadow_warnings` 豁免；留 tombstone fail-loud
- [ ] 删除 `full=True` 分支 + `ignore_tools_tests()` + `LOCAL_TOOL_CACHES`
- [ ] resolver 测试：新增「仓内放全套规则副本，断言仍解析到全局 canonical」反向锚
- [ ] resolver 测试：`SDFLOW_HOME` 指向自备 canonical 正常解析（既有测试隔离契约）
- [ ] `sane()` 反向锚：canonical 缺 `tools/` 或 contract → `exit 2`
- [ ] 所有「造假 canonical 过 sane()」的 fixture 同步补 `tools/` + contract
- [ ] init 测试：断言 `init` 后消费仓 `openspec/workflow/` 下只有 `WORKFLOW-GUIDE.md`（文件全集断言）
- [ ] init 测试：断言 fresh init（裸 `tmp_path`）不抛异常
- [ ] 先跑 pytest 看红名单，逐个改写/删除，不留与新契约矛盾的绿测试

