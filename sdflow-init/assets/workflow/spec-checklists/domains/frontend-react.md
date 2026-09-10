# 领域规则集：React（前端框架 delta）

> `extends: frontend` —— 只列 **React 框架**特有的设计审查规则；前端通用维度见
> [`frontend.md`](./frontend.md)，通用质量门禁见 [`../spec-quality-base.md`](../spec-quality-base.md)。
>
> 读 React 前端完整规则 = `base` + `frontend` + `frontend-react` 三层并集。

> **机械层前置**：本域推荐 lint 面 = eslint-plugin-react-hooks（含 React Compiler ESLint 插件）+
> eslint-plugin-jsx-a11y + TypeScript strict；上述工具能确定性抓的不进本清单，仅列架构/职责划分类
> 检查点。

---

| ID | 规则 | 触发条件 | 检查点 |
|----|------|---------|--------|
| REACT-01 | **Suspense/加载边界设计** | React 项目新增数据依赖的加载态 | FE-02 三态的 React 特化：Suspense 边界切在哪一层（整页 vs 分区）；边界粒度与 CLS 的权衡（骨架尺寸预留）；并行 reveal vs 逐层瀑布展示 |
| REACT-02 | **状态架构：server state 与 client state 分离** | 新增远端数据与本地 UI 状态并存的组件 | 远端数据（缓存/失效/重取语义）与本地 UI 状态分开管理；远端数据不复制进 `useState` 二次维护；全局 store 只放真全局 |
| REACT-03 | **服务端/客户端职责切分 [仅RSC]** | 项目实际启用 React Server Components（如 Next.js App Router / 显式 RSC 配置）——非仅"使用支持 RSC 的框架"或仅 SSR/Pages Router | 哪些树留 server（数据获取靠近数据源）、client 边界推到叶子；Server Actions 是公开 HTTP 端点——输入校验/鉴权在 server 侧设计，不信 client 传参 |

*规则集 v1 · extends frontend · 项目无关*
