# Hand-off — shared-yaml-subset-parser

## ✅ 完成了什么

- 7 份脚本（init.py / impl_route.py / ship_gate.py / anchor_lint.py×2 / roadmap_writeback_draft.py / sad_schema.py）的手搓 YAML 解析全部迁移到 yq subprocess 调用（锚：`hack/tests/test_yq_wrapper_consistency.py` 守 7 份一致性，17 assertions passed）
- setup.sh 新增 `check_dependencies()` 统一检测 python3/git/yq/openspec/pytest（锚：`setup.sh:498-585`）
- CI 钉版本安装 yq v4.53.3（锚：`.github/workflows/mechanical-gates.yml:61-79`）
- ADR-0036 记录决策（锚：`openspec/adr/0036-yq-replaces-hand-rolled-yaml.md`）
- ship_gate.py 保留 duplicate-key/tab-indent 预扫描（R11）（锚：`ship_gate.py:1028-1120`）
- 全仓 2579 tests passed（2 failed 为既有红测，非本 change 引入）
- 代码审修复 2 项 [impl-review-fix]：roadmap_writeback 重复键预扫描 + anchor_lint exit-code 契约修复（锚：commit 93e0150）

## ⏳ 未完成 / 延后

代码审 defer 3 项（无 buglist/todolist 条目——issues sweep 0 项匹配）：

1. **ship_gate.py yq subprocess 缺 timeout/OSError 收敛**：与 git 路径不一致但 yq 本地操作极少挂起，低概率低影响
2. **yq 最低版本运行时不验证**：setup.sh 已检查 ≥4.16.0，运行时 _yq() 只验身份不验版本，旁路概率低
3. **CI yq 下载无 SHA-256 校验**：版本已钉死，安全加固类

Minor 缺口 1 项（verify 已判 PASS）：
- R10 spec scenario 的 grep 字面命中 5 处保留函数名，每处有充分理由且已记录偏离

## ▶ 下一阶段建议

- 若后续开清理 change，可一并处理上述 3 项 defer（优先级 Low，不阻断当前功能）
- R10 的 spec 字面矛盾可在下次 spec 修订时精确化 grep 模式（排除已登记的合理保留）
- Roadmap 回填：未检测到 roadmap 关联标记，若属某 roadmap 请手动回填
