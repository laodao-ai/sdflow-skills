# Hand-off: fix-probe-scan-precision

## ✅ 完成了什么

- **消灭 workflow bundle 双分发链**：resolver 三步链收缩为两步（删 local-pin），规则与工具全局单份共享
  - 锚：`resolve-workflow.sh` 无 local-pin 代码 + 反向锚 `TestLocalCopyIgnored`
- **停铺 tools/contract 到消费仓**：`copy_bundle` 只保留 GUIDE + schema
  - 锚：`test_deploys_only_guide` 文件全集断言
- **sane() 形状级扩面**：tools/ 非空 + contract 非空
  - 锚：`TestSaneExpandedShapeChecks` 4 条反向锚
- **两个评审 SKILL 的 skew 探测段整段删除**
  - 锚：grep 各文件恰 1 处合法引用
- **ship_gate tools_spec 腿退役**
  - 锚：正向+反向锚 `test_gate_tools_leg_retirement.py`
- **告警语义改写**：判据扩员 + 带前置条件死件表述 + 可复制删除命令
  - 锚：正反双断言（init + maintain）
- **跨文件一致性守卫**补齐：`DEAD_RESIDUAL_MARKERS` + `_STALE_SHADOW_PRECONDITION`
  - 锚：`test_marker_consistency.py` 5 passed
- **7 个死件删除** + 文档面 sweep（CLAUDE.md/AGENTS.md/ADR/docs/CONTEXT/修法文案）
- **ADR 0039 新落**（含回滚步骤）；0038 删除；0003/0005/0019/0036 状态注记
- **GUIDE 生成器链接降级**
- **全量 pytest 2476 passed, 10 skipped**

## ⏳ 未完成 / 延后

### defer 的 todo（本 change 新增，各见 `openspec/issues/open/todo/`）

- **T271**: hack 链 symlink 化（Unix）——根治部署窗口/告警失真/hack 链无守三症状的共同成因
- **T272**: resolve-workflow.sh 补 --help
- **T273**: setup.sh 关键项 skipped 应非零退出
- **T274**: 补 Windows 失鲜 CI 回归用例

### code-review defer（1 条 Minor）

- `copy_bundle` 的 `n = sum(os.walk(dst))` 在停铺后包含残留文件的计数（display-only，不影响功能）

### code-review 双轴审 defer（若干 Minor，各 ticket 审时记录）

- Task 1: 测试 docstring 含 change 名（DOC-1 摩擦，不阻塞）
- Task 2: sane() 反向锚可参数化（纯风格）; copy_bundle/test docstring 重复（受众不同可接受）
- Task 3: 无额外 defer

## ▶ 下一阶段建议

1. **T271（hack 链 symlink 化）**是根因项，建议优先开 change——它同时解决 F2/F3/Q1 三个遗留面
2. T272-T274 可合并一个清理 change 处理
3. 发布纪律：push → 运行 checkout `git pull` → **立即** `bash setup.sh`（消费仓不再需要 `sdflow-init update` 才能评审）
