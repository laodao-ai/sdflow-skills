# Task 1 实现报告：四个 domain 文件落盘

## 落盘文件与条目数

| 文件 | 状态 | 条目 |
|---|---|---|
| `sdflow-init/assets/workflow/spec-checklists/domains/frontend.md` | 增补 | FE-06~FE-13（8 条） |
| `sdflow-init/assets/workflow/spec-checklists/domains/frontend-react.md` | 新建 | REACT-01~03（3 条） |
| `sdflow-init/assets/workflow/code-checklists/domains/frontend.md` | 新建 | CR-FE-01~08（8 条） |
| `sdflow-init/assets/workflow/code-checklists/domains/frontend-react.md` | 新建 | CR-REACT-01~07（7 条） |

合计 8+3+8+7 = **26 条**，与候选表全量一致。

## 各条 ID 列表

- **A 组 → FE-06~13**：FE-06 CWV 指标锚定、FE-07 请求瀑布设计审查、FE-08 CSP 与嵌入策略规划、
  FE-09 URL 即状态、FE-10 表单设计语义、FE-11 错误边界与降级设计、FE-12 i18n 就绪度、
  FE-13 响应式断点策略。
- **B 组 → CR-FE-01~08**：CR-FE-01 XSS sink 数据流追踪、CR-FE-02 postMessage 双向校验、
  CR-FE-03 凭证与敏感数据存放、CR-FE-04 CSRF 前端侧配合、CR-FE-05 跳转与嵌入安全、
  CR-FE-06 长驻页面资源清理（CR-04 的前端特化）、CR-FE-07 模态框焦点生命周期（纯键盘交互口径）、
  CR-FE-08 表单错误提示与恢复（纯键盘交互口径）。
- **C 组 → REACT-01~03**：REACT-01 Suspense/加载边界设计、REACT-02 状态架构：server state 与
  client state 分离、REACT-03 服务端/客户端职责切分 [仅RSC]。
- **D 组 → CR-REACT-01~07**：CR-REACT-01 Effect 存在性审查、CR-REACT-02 纯度语义违规、
  CR-REACT-03 Compiler 时代 memo 观、CR-REACT-04 React 19 API 采用正确性、CR-REACT-05 列表 key 语义、
  CR-REACT-06 状态所有权与 re-render 半径、CR-REACT-07 边界纪律 [仅RSC]。

## 逐点核对

- **触发条件**：候选表原表无独立触发条件列，26 条均已提炼独立短语（沿 FE-01~05 /
  CR-BE-01/02「新增 X / 含 Y 操作」句式），无留空、无检查点散文充数。
- **形制一致**：4 文件均为 `extends` 头注 + 四列表（ID/规则/触发条件/检查点）+
  `*规则集 v1 · extends … · 项目无关*` 尾注，与 `frontend.md`(FE-01~05)、`backend.md`(CR-BE)、
  `backend-go.md`（base+delta 层先例）逐点对齐。
- **机械层前置注记**：4 文件头（extends 头注之后、表格之前）各加一条 blockquote：
  - spec/frontend：TypeScript strict + ESLint 通用规则集 + Lighthouse CI/性能预算 CI。
  - spec/frontend-react：eslint-plugin-react-hooks（含 React Compiler 插件）+
    eslint-plugin-jsx-a11y + TypeScript strict。
  - code/frontend：TypeScript strict + eslint-plugin-no-unsanitized + eslint-plugin-security。
  - code/frontend-react：eslint-plugin-react-hooks（含 Compiler 纯度检查）+ eslint-plugin-react +
    TypeScript strict。
- **CR-FE-06** 检查点内注明「CR-04 的前端特化」（人拍板 D4）。
- **CR-FE-07/08** 措辞为纯键盘交互口径（焦点移入/Tab 圈禁/Esc/焦点还原；焦点移动到错误字段/错误摘要/
  即时消错），未使用 a11y / 辅助技术叙述。
- **REACT-03 / CR-REACT-07** 规则名后缀 `[仅RSC]`，触发条件列均写「项目实际启用 React Server
  Components（如 Next.js App Router / 显式 RSC 配置）——非仅『使用支持 RSC 的框架』或仅
  SSR/Pages Router」（design.md D6 细化措辞）。
- **ID 连续无冲突**：FE-06~13 接续既有 FE-01~05；CR-FE-01~08、REACT-01~03、CR-REACT-01~07
  均为新前缀首次使用，grep 确认仓内此前未被占用。
- **DOC-1**：条目不携带候选表的〔未核实〕标记 / 来源列 / 演进史，正文即最终态，与既有 FE-01~05
  风格一致（候选表 F 节已确认落盘时不携带该标记）。

## 未涉及范围

本报告仅覆盖 Task 1（四个 domain 文件落盘）。Task 2（trigger-catalog 接线、两侧 README、
backend IOU 交叉引用、栈枚举同步）不在本票范围内，未动。
