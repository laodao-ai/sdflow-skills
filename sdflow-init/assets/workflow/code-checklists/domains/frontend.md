# 代码审查领域：前端 / UI（通用）

> `extends: base` —— 前端代码审查特有维度（XSS/凭证/CSRF/资源清理/键盘交互），框架无关；
> React 语言习惯见 `frontend-react.md`，通用维度见 [`../code-review-base.md`](../code-review-base.md)。

> **机械层前置**：本域推荐 lint 面 = TypeScript strict + eslint-plugin-no-unsanitized（`innerHTML`/
> `dangerouslySetInnerHTML` 等危险 sink 静态抓取）+ eslint-plugin-security（不安全正则/`eval` 等）；
> 上述工具能确定性抓的不进本清单，仅列跨文件数据流追踪与语义判断类检查点。

---

| ID | 规则 | 触发条件 | 检查点 |
|----|------|---------|--------|
| CR-FE-01 | **XSS sink 数据流追踪** | 用户可控数据流向 DOM 渲染 sink | 三步追踪 source（location.hash/search、postMessage、storage、API 返回富文本）→ 转换链 → sink（`dangerouslySetInnerHTML`/`v-html`/`innerHTML`/`outerHTML`/`document.write`/动态 `setAttribute` 属性名/`href\|src` 的 `javascript:`）；纯文本一律 textContent；富文本必须 DOMPurify 且 sanitize 后不得再 DOM 改写；框架逃逸口（React 危险 API、Angular `bypassSecurityTrust*`）逐处理由（接走 CR-BE-02 客户端渲染 XSS IOU） |
| CR-FE-02 | **postMessage 双向校验** | 使用 `postMessage` 跨窗口/跨源通信 | 发送方 `targetOrigin` 禁 `*`；接收方 `event.origin` 精确匹配 FQDN（禁 indexOf/endsWith 模糊匹配）；消息内容只当数据（禁 eval/innerHTML 消费） |
| CR-FE-03 | **凭证与敏感数据存放** | 存储会话凭证/敏感数据 | session token/凭证禁 `localStorage`/`sessionStorage`（应 httpOnly cookie）；bundle 里不得有密钥（`VITE_`/`NEXT_PUBLIC_` 前缀 = 公开，逐个核对不是密钥）；低敏数据 `sessionStorage` 优于 `localStorage` |
| CR-FE-04 | **CSRF 前端侧配合** | 新增写请求 / 状态变更操作 | 状态变更禁走 GET；写请求带 CSRF token（经 header/payload，禁经 cookie 传）或 custom header 方案；CORS 白名单明确指定源（禁 `*`+credentials、禁正则通配子域）；依赖 SameSite 时核对官方严苛条件表 |
| CR-FE-05 | **跳转与嵌入安全** | 跳转目标/iframe 来源含用户输入 | location/href 赋值的目标若含用户输入：白名单校验路径、拒绝协议注入（`javascript:`/`data:`）防 open redirect；不信任内容 iframe 加 sandbox |
| CR-FE-06 | **长驻页面资源清理**（CR-04 的前端特化） | 组件挂载期间注册全局/外部资源监听 | 挂在 window/document/外部 emitter 上的 listener、定时器、observer（Intersection/Resize/Mutation）在组件卸载时成对清理；SPA 无整页刷新，泄漏只积累不清零 |
| CR-FE-07 | **模态框焦点生命周期** | 新增模态框/对话框类组件 | 打开模态：焦点移入模态内首个合理元素；开启期间 Tab/Shift+Tab 循环圈禁在模态内、不落到被遮罩内容；Esc 关闭；关闭后焦点还原到触发元素——四段缺一即键盘操作断链 |
| CR-FE-08 | **表单错误提示与恢复** | 表单提交失败/字段校验不通过 | 提交失败：焦点移动到首个错误字段或错误摘要（摘要项可激活跳转对应字段）；错误提示与字段结构关联、紧邻可见；修正后该字段错误即时消除（呼应 FE-10 校验时机分级） |

*规则集 v1 · extends base · 项目无关*
