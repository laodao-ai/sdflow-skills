### Task 2: 接线（trigger-catalog + 两侧 README + backend IOU + 栈枚举）

**Blocked-by:** 1
**R-ID:** R2

完成所有消费面的接线，使新 domain 文件在选用链中可达：

- `trigger-catalog.md` TG-03 领域列改为 `` `frontend`(+`frontend-react`) ``
- `spec-checklists/README.md`：架构图加 frontend-react 分支、ID 约定表加 `REACT-` 行、注册表加 frontend-react 行
- `code-checklists/README.md`：架构图加 frontend 链、选用规则 L33 接实、ID 表加 `CR-FE-`/`CR-REACT-` 行、注册表加 2 行、扩展约定指针行
- `code-checklists/domains/backend.md:11` CR-BE-02 IOU 句改为交叉引用 CR-FE-01
- 三处栈枚举文本追加 `(+frontend-react)`：`sdflow-spec-review/SKILL.md:223`、`sdflow-init/SKILL.md:195`、`config.template.yaml:24`

- [ ] TG-03 行含 delta 记法
- [ ] spec 侧 README 注册表 +1 行、ID 表含 `REACT-`
- [ ] code 侧 README 注册表 +2 行、ID 表含 `CR-FE-`/`CR-REACT-`、扩展约定指针行到位
- [ ] `grep -rn "待 frontend domain 覆盖" sdflow-init/assets/workflow/` 归零
- [ ] 三处栈枚举行含 `frontend(+frontend-react)`

