# Task 2 实现报告：接线（trigger-catalog + 两侧 README + backend IOU + 栈枚举）

## 改动摘要（5 处）

### 2.1 `sdflow-init/assets/workflow/trigger-catalog.md`
TG-03 领域列 `` `frontend` `` → `` `frontend`(+`frontend-react`) ``，与 TG-01/02 的 `` `backend`(+`backend-go`) `` /
`` `embedded`(+芯片 delta) `` 同构 +delta 记法。

### 2.2 `sdflow-init/assets/workflow/spec-checklists/README.md`
- 架构图：`frontend.md` 下加一行 `└ frontend-react.md   React delta (extends frontend)`（沿用
  `backend.md → └ backend-go.md` 单子节点画法）。
- ID 约定表：加 `REACT-NN | frontend-react delta | REACT-01 Suspense/加载边界设计` 行。
- 领域注册表：`domains/frontend.md` 行后加 `domains/frontend-react.md | frontend | React | REACT- | ✅ 就绪` 行。

### 2.3 `sdflow-init/assets/workflow/code-checklists/README.md`
- 架构图：`embedded` 链后加 `frontend.md` + `└ frontend-react.md` 两行链（与 `backend`→`backend-go` 单子链同构）。
- 选用规则：L33 `命中 TG-03(前端) → code-review-base + frontend（如有）` → `+ frontend(+frontend-react)`（接实，去掉「如有」的悬空承诺）。
- ID 约定表：加 `CR-FE-NN | 前端通用`、`CR-REACT-NN | React delta` 两行。
- 领域注册表：加 `domains/frontend.md`（base / CR-FE-）、`domains/frontend-react.md`（frontend / CR-REACT-）两行。
- 新增「扩展约定」小节（该侧原无此节）：指针到 `../spec-checklists/README.md` §如何新增一个领域，
  注明两侧同法、本侧 ID 前缀改用 `CR-` 系。

### 2.4 `sdflow-init/assets/workflow/code-checklists/domains/backend.md`（CR-BE-02）
IOU 句「客户端框架渲染（`dangerouslySetInnerHTML` / `v-html` 等）待 frontend domain 覆盖，本条不声称覆盖」
→ 「客户端框架渲染 XSS 见 `domains/frontend.md` CR-FE-01（本条聚焦服务端模板渲染）」。
交叉验证：`code-checklists/domains/frontend.md` 的 CR-FE-01 检查点原文已含
「框架逃逸口……逐处理由（接走 CR-BE-02 客户端渲染 XSS IOU）」，双向引用闭环。
`grep -rn "待 frontend domain 覆盖" sdflow-init/assets/workflow/` 已归零。

### 2.5 三处栈枚举文本追加 `(+frontend-react)`
- `sdflow-spec-review/SKILL.md:223`：`（backend·go / embedded·ml307c·esp32 / frontend）` →
  `（backend·go / embedded·ml307c·esp32 / frontend(+frontend-react)）`
- `sdflow-init/SKILL.md:195`：同上
- `sdflow-init/assets/workflow/config.template.yaml:24`：同上

## 验收自查

- [x] TG-03 行含 delta 记法
- [x] spec 侧 README 注册表 +1 行、ID 表含 `REACT-`
- [x] code 侧 README 注册表 +2 行、ID 表含 `CR-FE-`/`CR-REACT-`、扩展约定指针行到位
- [x] `grep -rn "待 frontend domain 覆盖" sdflow-init/assets/workflow/` 归零（exit 1，无匹配）
- [x] 三处栈枚举行含 `frontend(+frontend-react)`

## 范围说明

本票仅做「接线」——使 Task 1 已落盘的 `frontend.md` / `frontend-react.md`（spec + code 两侧）在触发目录、
两份 README 的架构图/ID表/注册表/选用规则中可达，并关闭 backend.md 的 IOU 交叉引用。未新增/修改任何
domain 规则条目本身、未动 checklists-guide.html（属 Task 3 范围）。tickets.md 验收复选框留空，按信号权威表
由执行模式在双轴审通过后补打，本报告不代打勾。
