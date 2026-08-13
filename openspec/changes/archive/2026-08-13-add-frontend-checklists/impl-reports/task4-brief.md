### Task 4: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落 `impl-reports/task4-verification.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

另逐条自验 proposal Success Metrics：
- `grep -rn "frontend（如有）"` 归零
- TG-03 行含 delta 记法
- 4 文件 ID 连续无冲突、形制一致
- spec 侧注册表 +1 行 / code 侧 +2 行
- `grep -rn "待 frontend domain 覆盖" sdflow-init/assets/workflow/` 归零
- 三处栈枚举行含 `frontend(+frontend-react)`
- `grep -n "缺失\|已知缺口" sdflow-init/assets/workflow/checklists-guide.html` 逐条判定

- [ ] 单元测试证据齐全并通过
- [ ] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
