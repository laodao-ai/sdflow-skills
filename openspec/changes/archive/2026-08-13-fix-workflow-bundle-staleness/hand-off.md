# Hand-off — fix-workflow-bundle-staleness

## ✅ 完成了什么

- **两处正面矛盾修正**：README:18 P3c 口径 + spec-review:72 G2 决策登记区（锚：`git diff` 实证两文件改写）
- **退役机制清理**：subagent-dev / writing-plans / 官方 code-review / `/clear +` 措辞（锚：quality-layering.md:84 已删 subagent-dev、:25/:42 已改）
- **`/review` 消费方 8 处统一改写**为 sdflow-code-review（锚：`grep -rn '/review' assets/workflow/` 零命中 skill 名义用法）
- **generation-process 收史**：§二两工具表、§三→workflow-history A5、§六措辞、§四流水线图补阶段二 + ②删「判断」（锚：`test_canonical_entry_sync.py` 8 passed）
- **ff-generation-constraints 外壳更新**（锚：标题/定位/路径已改）
- **号段上界去除**：TG/BASE/CR 共 5 处（锚：`grep 'TG-01~\|BASE-01~\|CR-01~'` 零命中）
- **reference 处置**：3 文件横幅/标注 + Token_Saving git mv + PRD_vs_Spec 4 处改写（锚：`git status` rename 确认）
- **同族面治**：index-section 6 行 + config.template + config.yaml + fable5 号段（锚：init.py update 绿 + diff 对照）
- **init.py bug fix**：`_marker_schema()` 放宽 `.openspec.yaml` 键校验（锚：新增 `test_migration_accepts_marker_with_extra_keys` 测试）
- **机械门全绿**：2650 passed / 10 skipped（锚：task4-verification.md SHA 证据）

## ⏳ 未完成 / 延后

- **T282**（todo/OPEN）：CR-01~09 号段上界残留于 bundle 外消费面（SKILL.md ×4 / docs/workflow-skills ×2），当前值准确但 CR 扩号时会漂。见 `openspec/issues/open/todo/T282.md`
- **T283**（todo/OPEN）：评审裁决层证据纪律两条（溯源三查 + 推荐亲验锚），从 spec-review 实证提炼。见 `openspec/issues/open/todo/T283.md`
- **fable5 02-module-reference.md:173-174**：D 组 + HR-TG 子集里的 TG-27/28 描述为举例层面遗留（已去数字改组范围，但 HR-TG 行的枚举未同步——低优先级，不影响机械消费）

## ▶ 下一阶段建议

1. **T283 优先**：评审纪律改进涉及 sdflow-spec-review / sdflow-code-review 两个 SKILL 的 Step3，一个小 change 做完
2. **T282 可与 T283 并行或顺序**：bundle 外 CR 号段去上界，触发面小（6 个位点），只需确认无 CR-10 再去掉数字
3. **消费仓 update**：merge 后人择机跑 `sdflow-init update`（本 change Non-Goals 明确不主动触发）
4. **发布路径**：push → 运行 checkout `git pull` + `setup.sh`（canonical 即时生效）
