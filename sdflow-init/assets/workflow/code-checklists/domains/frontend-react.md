# 代码审查领域：React（前端框架 delta）

> `extends: frontend` —— React 框架特有的代码审查项；前端通用见 [`frontend.md`](./frontend.md)，
> 通用维度见 [`../code-review-base.md`](../code-review-base.md)。

> **机械层前置**：本域推荐 lint 面 = eslint-plugin-react-hooks（含 React Compiler ESLint 插件的纯度/
> 规则检查）+ eslint-plugin-react（部分 key/prop-types 规则）+ TypeScript strict；上述工具能确定性抓的
> 不进本清单，仅列语义/架构判断类检查点。

---

| ID | 规则 | 触发条件 | 检查点 |
|----|------|---------|--------|
| CR-REACT-01 | **Effect 存在性审查** | 新增/改动 `useEffect` | 对每个新增 `useEffect` 问「官方八问」：派生值→渲染期算（禁 effect+setState 镜像 props/state）；重置→key；事件因果→handler 不是 effect；链式 effect 级联 setState 禁；外部 store→`useSyncExternalStore`；应用级一次性初始化不进组件 effect；数据 fetch effect 必须有 cleanup 防竞态 |
| CR-REACT-02 | **纯度语义违规** | 新增/改动组件渲染逻辑 | 渲染幂等（渲染期禁自增/随机/`Date.now` 决定输出）；渲染期禁读写组件外可变值；props/state/hook 返回值深层 mutation（push/直接改字段）；JSX 已使用的值事后不得改——StrictMode 双渲染下会漂移，是 Compiler 优化的前提 |
| CR-REACT-03 | **Compiler 时代 memo 观** | 新增手写 `useMemo`/`useCallback`/`React.memo` | 项目启用 React Compiler：新增手写 memo 化须给理由（默认不写）；未启用：memo 仅加在实测热点，禁反射式包裹——评审方向反转为「不该加还加」 |
| CR-REACT-04 | **React 19 API 采用正确性** | 新增表单提交/异步操作 或 ref 转发 | 表单/异步提交用 Actions/`useActionState` 接管 pending/error/乐观序列（替代手搓 `isSubmitting`+try/catch 样板）；`useOptimistic` 的失败回滚路径真实存在；新码 ref 直接作 prop（不再 `forwardRef`）；ref 回调返回 cleanup 函数 |
| CR-REACT-05 | **列表 key 语义** | 新增/改动可变列表渲染 | key 是否稳定业务身份（可变列表用 index = 重排时状态串行）；反向技巧：需要重置子树状态时该用 key 变化而没用 |
| CR-REACT-06 | **状态所有权与 re-render 半径** | 新增/改动共享状态或 context | 状态放置层级 = 最低公共祖先（放太高 = 全树 re-render 放大；太低 = 兄弟不同步）；context 按变更频率拆分（高频值与低频配置不同 context）；大列表虚拟化时机判断 |
| CR-REACT-07 | **边界纪律 [仅RSC]** | 项目实际启用 React Server Components（如 Next.js App Router / 显式 RSC 配置）——非仅"使用支持 RSC 的框架"或仅 SSR/Pages Router | `'use client'` 只标真需要交互的模块（边界会传染整个 import 子图）；Server→Client props 过序列化约束（函数/类实例传不过去）；server-only 代码（密钥/DB client）经 server-only 包或结构隔离，禁被 client 模块 import |

*规则集 v1 · extends frontend · 项目无关*
