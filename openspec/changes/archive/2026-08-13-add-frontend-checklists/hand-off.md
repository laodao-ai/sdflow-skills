# Hand-off · add-frontend-checklists

## ✅ 完成了什么

- 4 个前端 domain checklist 文件落盘，26 条全部落位（FE-06~13 / REACT-01~03 / CR-FE-01~08 / CR-REACT-01~07）
  锚：`sdflow-init/assets/workflow/{spec,code}-checklists/domains/frontend{,-react}.md`
- 5 处接线完成（trigger-catalog TG-03 delta 记法 + 两侧 README 注册 + backend IOU 关闭 + 三处栈枚举）
  锚：checkpoint(task2-wiring) commit 1e20ac95
- checklists-guide.html 更新为目标态（§一~§五 全 6 处改动面）+ INDEX.md 括注
  锚：checkpoint(task3-guide-sync) commit 726e820c
- research 附件（absorption-candidates.md）随 change 落盘，26 条 + 备选冻结区完整
- 实现期 Success Metrics 6 项全绿（verify-report.md 逐条锚点）

## ⏳ 未完成 / 延后

- **T284**（todo/OPEN）：注册一致性机械守——domains/*.md ↔ README 注册表/ID 表一致性 pytest。触发条件=下次新增 domain 时再现同类手工镜像失鲜即建。
- **T285**（todo/OPEN）：guide 长期治理——覆盖矩阵/缺口内容改为指向 README 注册表或脚本生成，消除手工 HTML 失鲜重灾区。触发条件=下次 guide 失鲜返工时。
- pytest 因 Windows 环境超时未完整运行（2246 tests 收集正常，零 Python 改动，不构成回归风险；verify 判定为可接受的 Minor 缺口）。

## ▶ 下一阶段建议

- T284/T285 均为「下次触发时建」类 defer，当前无紧急性。
- 本 change 发布路径：push → 运行 checkout `git pull` + `bash setup.sh`（canonical symlink 即时生效，规则对所有消费仓可用）。
- 无 roadmap 关联。
