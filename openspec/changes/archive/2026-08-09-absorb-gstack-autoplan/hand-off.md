# Hand-off — absorb-gstack-autoplan

日期：2026-08-09

## ✅ 完成了什么

1. **Step1 自持化**：autoplan 原生执行退役，改为自持 strategy+plan-eng 双广审镜（单批 dispatch）。验证锚：`sdflow-spec-review/SKILL.md` 重写 + `grep -rn "autoplan|gstack"` 归零 + `test_sync_principles.py` 19 passed。
2. **守卫脚本退役**：`outside_voice_guard.py` + 436 行测试删除；矩阵全笛卡尔 golden 迁移到 anchor_lint 单工具测试。验证锚：`test_anchor_lint.py::test_matrix_full_cartesian_golden` 18 passed。
3. **DX 吸收**：TG-28 新增 + `domains/devex.md` 创建（可判表式 DX-01~05）。验证锚：`trigger-catalog.md:48` + `devex.md` 存在。
4. **Roadmap 侧重写**：判定点②退役，恒跑双镜 + sync-only outside voice。验证锚：`sdflow-roadmap/SKILL.md` 重写 + `grep` 归零。
5. **同源注入机制**：`broad-mirrors.md` 真相源 + `sync_principles.py` 第二类注入块。验证锚：`sync_principles.py --check` 22 投放面一致。
6. **Bundle 机械层**：fold 表替换 + retro attribute-to-next + anchor_lint hint 修复。验证锚：全仓 pytest 2444 passed。
7. **文档 sweep**：20+ 文件 autoplan/gstack 残留清理。验证锚：`grep` 验收归零。
8. **盲测**：3 归档 change × 3 声边际贡献测试。验证锚：`blind-test-report.md` 落盘。

## ⏳ 未完成 / 延后

本 change 无 open issues（scan 返回空集）。code-review defer 的 3 项：

1. **roadmap SKILL 裸 eval 缺清脏保护**（Voice V2，既有债务非本 change 引入）：`sdflow-roadmap/SKILL.md:507` 的 tier-resolution 未用完整保护序列（unset + 捕获退出码 + eval 校验）。建议：下一个触碰 roadmap SKILL 的 change 顺手补。
2. **test_sync_principles.py order dependency**（Voice V5）：`original = SP.BROAD_MIRROR_TARGETS` 是引用非拷贝。建议：改为 `list()` 拷贝或 monkeypatch。
3. **criteria-mechanization-tracker.md 残留**（Voice V6）：仍列 guard 为现役门。建议：下次文档 change 顺手更新。

## ▶ 下一阶段建议

1. **盲测后续**：盲测显示新 3 声结构对旧 broad 独家高危 findings 严格召回率 0/11。retro ≥10 轮复评盯 broad 采纳率/独立率，若下滑则加声（design D1 假设节已预案）。
2. **发布**：push → 运行 checkout `git pull` + `bash setup.sh`（同代翻转），消费仓零动作。
3. 上述 3 项 defer 可并入下一个自然触碰相关文件的 change，无需专门开 cleanup change。

（roadmap 回填：未检测到 roadmap 关联标记，本 change 非 roadmap 驱动。）
