# 前端 checklist 吸收候选表（2026-08-13 调研合并稿）

> **拍板结果（2026-08-13 用户）**：A/B/C/D 全部 24 条采纳；B6 独立成条（不并入 CR-04）；
> 备选区 a11y #3（模态框焦点生命周期）、#5（表单错误恢复）以**纯键盘交互正确性**名义捞回，
> 进 code-frontend 作 B7/B8（条文措辞不用 a11y/辅助技术口径）。其余备选维持冻结。

> 调研路：React 官方（curl 亲抓 react.dev 6 页）· 性能（web.dev vitals/inp）· 安全（OWASP 5 cheat sheet）·
> 业界汇编（Front-End-Checklist / web.dev forms）· a11y（子代理，W3C 16 页，→ 备选区）。
> 过滤判据：lint/自动扫描能确定性抓的不收；与 base（BASE-*/CR-*）及现有 FE-01~05 不重复；每条防一类真实失效。
> 标记：〔未核实〕= 该条部分依据模型知识、未逐字核对页面原文。
> 用户已裁剪：a11y 整路、多端条目 → 备选区，不进正式清单。

## A. spec-frontend 增补（FE-06 起，设计审）

| # | 候选 | 检查点 | 防什么失效 | 来源 |
|---|---|---|---|---|
| A1 | CWV 指标锚定 | 涉及新页面/首屏/重交互时，设计期按 Core Web Vitals 定数字目标：LCP≤2.5s、INP≤200ms、CLS≤0.1（75 分位真实用户）；INP 已取代 FID。是 BASE-16「NFR 数字化」的前端特化：告诉你该定哪些数、参考什么阈值 | 无指标可审 → 上线后靠感觉扯皮；INP 时代还盯 FID = 盯错靶 | web.dev/articles/vitals ✅ |
| A2 | 请求瀑布设计审查 | 新页面数据依赖画一张「谁等谁」图：render→fetch→render→fetch 串行瀑布是设计出来的（组件各自 fetch）；能并行/提升/预取的在设计期定 | 每层瀑布 = 一倍往返延迟；实现后再改动组件数据契约成本高 | 〔未核实〕（web.dev patterns 方向） |
| A3 | CSP 与嵌入策略规划 | 新产品面/新站点设计期定：strict CSP（nonce/hash）vs allowlist（官方推荐前者）；内联脚本/内联事件处理器架构是否与 CSP 冲突（onclick= 会被禁）；frame-ancestors 要不要允许被嵌入；report-only 渐进上线路径 | CSP 后补 = 全站内联代码重构；不定 frame-ancestors = clickjacking 面 | OWASP CSP cheat sheet ✅ |
| A4 | URL 即状态 | 筛选/分页/tab/选中态是否进 URL：刷新不丢、可分享、后退符合直觉；深链接可直达；滚动位置恢复策略 | SPA 把状态锁内存 → 刷新全丢、无法分享复现，用户与客服双输 | 〔未核实〕（业界共识） |
| A5 | 表单设计语义 | 校验时机分级（格式类 blur 后即时、跨字段 submit）；错误恢复路径（改完即消错）；autocomplete 属性利用（地址/支付自动填充）；不收不需要的数据；流程摩擦审查（如强制注册才能结账） | 校验时机错 = 输入中被打断/提交后才知道错；表单摩擦直接掉转化 | web.dev payment-and-address-form-best-practices ✅ |
| A6 | 错误边界与降级设计 | Error Boundary 布点粒度 = 白屏半径设计（一个组件炸不该白整页）；第三方脚本（统计/客服/广告）失败的降级行为；全局兜底页 | 无布点设计 → 任意子树异常白屏整页；第三方挂了拖死主功能 | 〔未核实〕（React 官方概念 + 业界实践） |
| A7 | i18n 就绪度（仅多语言目标产品） | 文案不硬编码；日期/数字/货币用 Intl API 不手拼；翻译文本膨胀 30-50% 的布局余量；复数规则用 Intl.PluralRules/ICU 不用单复数二分 | 后补 i18n = 全量文案考古；德语/俄语撑爆定宽布局 | Front-End-Checklist i18n 节 ✅ |
| A8 | 响应式断点策略 | 新页面/布局改动声明断点策略（内容驱动而非设备驱动）；窗口极值（最窄/最宽）布局不破；图片/表格在窄屏的降级形态 | 只按设计稿一档宽度实现 → 其他宽度布局破碎 | 〔未核实〕（业界共识；多端条目已按裁剪剔除） |

## B. code-frontend 新建（CR-FE-01 起，代码审）

| # | 候选 | 检查点 | 防什么失效 | 来源 |
|---|---|---|---|---|
| B1 | XSS sink 数据流追踪（接走 CR-BE-02 IOU） | 三步追踪 source（location.hash/search、postMessage、storage、API 返回的富文本）→ 转换链 → sink（`dangerouslySetInnerHTML`/`v-html`/`innerHTML`/`outerHTML`/`document.write`/`setAttribute` 动态属性名/`href|src` 的 `javascript:`）。纯文本一律 textContent；富文本必须 DOMPurify 且 sanitize 后不得再 DOM 改写；框架逃逸口（React 危险 API、Angular bypassSecurityTrust*）逐处理由 | 存储型/DOM 型 XSS：一处 sink 失守 = 会话/凭证全线暴露 | OWASP XSS + DOM-XSS ✅ |
| B2 | postMessage 双向校验 | 发送方 targetOrigin 禁 `*`；接收方 event.origin 精确匹配 FQDN（禁 indexOf/endsWith 模糊匹配）；消息内容只当数据（禁 eval/innerHTML 消费） | 任意站点可向你的 window 投毒/窃听跨域消息 | OWASP HTML5 ✅ |
| B3 | 凭证与敏感数据存放 | session token/凭证禁 localStorage/sessionStorage（应 httpOnly cookie）；bundle 里不得有密钥（`VITE_`/`NEXT_PUBLIC_` 前缀 = 公开，逐个核不是密钥）；低敏数据 sessionStorage 优于 localStorage | 一个 XSS 即可批量收割 localStorage 里的 token；打进 bundle 的密钥 = 已泄露 | OWASP HTML5 ✅（env 前缀部分〔未核实〕） |
| B4 | CSRF 前端侧配合 | 状态变更禁走 GET；写请求带 CSRF token（经 header/payload，禁经 cookie 传）或 custom header 方案；CORS 白名单明确指定源（禁 `*`+credentials、禁正则通配子域）；依赖 SameSite 时核对官方严苛条件表 | SameSite 当银弹 → 子域/GET 变更/旧浏览器场景被绕 | OWASP CSRF ✅ |
| B5 | 跳转与嵌入安全 | location/href 赋值的目标若含用户输入：白名单校验路径、拒绝协议注入（javascript:/data:）防 open redirect；不信任内容 iframe 加 sandbox | 钓鱼跳板：合法域名 + ?redirect=恶意站；第三方内容逃逸 | OWASP ✅ |
| B6 | 长驻页面资源清理（CR-04 前端特化） | 挂在 window/document/外部 emitter 上的 listener、定时器、observer（Intersection/Resize/Mutation）在组件卸载时成对清理；SPA 无整页刷新，泄漏只积累不清零 | 长驻单页内存持续增长、幽灵 listener 触发已卸载组件逻辑 | 〔未核实〕（与 CR-04 重叠度请拍板：可并入其检查点或独立成条） |

## C. spec-react 新建（REACT-01 起，设计审）

| # | 候选 | 检查点 | 防什么失效 | 来源 |
|---|---|---|---|---|
| C1 | Suspense/加载边界设计 | FE-02 三态的 React 特化：Suspense 边界切在哪一层（整页 vs 分区）；边界粒度与 CLS 的权衡（骨架尺寸预留）；并行 reveal vs 逐层瀑布展示 | 边界切太粗 = 整页骨架闪烁；太细 = 弹跳式加载 | 〔未核实〕（react.dev 概念） |
| C2 | 状态架构：server state 与 client state 分离 | 远端数据（缓存/失效/重取语义）与本地 UI 状态分开管理；远端数据不复制进 useState 二次维护；全局 store 只放真全局 | 复制态与源不同步 = 一整类"数据不一致"bug 的根因 | 〔未核实〕（业界共识） |
| C3 | [仅RSC] 服务端/客户端职责切分 | 用 RSC 框架时：哪些树留 server（数据获取靠近数据源）、client 边界推到叶子；Server Actions 是公开 HTTP 端点——输入校验/鉴权在 server 侧设计，不信 client 传参 | client 边界画太高 = RSC 白用；Server Action 不设防 = 裸 API | react.dev use-client ✅ + React 19 博客 ✅ |

## D. code-react 新建（CR-REACT-01 起，代码审）

| # | 候选 | 检查点 | 防什么失效 | 来源 |
|---|---|---|---|---|
| D1 | Effect 存在性审查 | 对每个新增 useEffect 问「官方八问」：派生值→渲染期算（禁 effect+setState 镜像 props/state）；重置→key；事件因果→handler 不是 effect；链式 effect 级联 setState 禁；外部 store→useSyncExternalStore；应用级一次性初始化不进组件 effect；数据 fetch effect 必须有 cleanup 防竞态（race condition 官方明示） | effect 滥用 = 多余渲染循环、竞态旧数据覆盖新数据、不可追因的级联更新 | react.dev you-might-not-need-an-effect ✅（Recap 逐条核） |
| D2 | 纯度语义违规（官方标注 lint 抓不了的那半） | 渲染幂等（渲染期禁自增/随机/Date.now 决定输出）；渲染期禁读写组件外可变值；props/state/hook 返回值深层 mutation（push/直接改字段）；JSX 已使用的值事后不得改 | StrictMode 双渲染下行为漂移、Compiler 优化后直接出错（纯度是 Compiler 生效前提） | react.dev/reference/rules ✅（官方自标 ESLint ❌ 项） |
| D3 | Compiler 时代 memo 观 | 项目启用 React Compiler：新增手写 useMemo/useCallback/React.memo 须给理由（默认不写）；未启用：memo 仅加在实测热点，禁反射式包裹。评审方向反转：从「该加没加」变成「不该加还加」 | 手写 memo 噪音掩盖真热点；违反纯度的组件 Compiler 静默跳过不优化 | react.dev compiler 页 ✅ |
| D4 | React 19 API 采用正确性 | 表单/异步提交用 Actions/useActionState 接管 pending/error/乐观序列（替代手搓 isSubmitting+try/catch 样板）；useOptimistic 的失败回滚路径真实存在；新码 ref 直接作 prop（不再 forwardRef）；ref 回调返回 cleanup 函数 | 手搓提交状态机 = FE-01/FE-03 那些边缘场景逐个重踩；旧模式混用新 API 语义冲突 | react.dev React 19 博客 ✅ |
| D5 | 列表 key 语义（lint 抓不了的那半） | key 是否稳定业务身份（可变列表用 index = 重排时状态串行）；反向技巧：需要重置子树状态时**该用**key 变化而没用 | 列表重排后输入框内容/选中态窜到别的行 | react.dev ✅（Preserving State 概念）|
| D6 | 状态所有权与 re-render 半径 | 状态放置层级 = 最低公共祖先（放太高 = 全树 re-render 放大；太低 = 兄弟不同步）；context 按变更频率拆分（高频值与低频配置不同 context）；大列表虚拟化时机判断 | 打字卡顿类性能病的头号来源；context 一改全树刷 | 〔未核实〕（业界共识 + react.dev 概念） |
| D7 | [仅RSC] 边界纪律 | 'use client' 只标真需要交互的模块（边界会传染整个 import 子图）；Server→Client props 过序列化约束（函数/类实例传不过去）；server-only 代码（密钥/DB client）经 server-only 包或结构隔离，禁被 client 模块 import | 边界标错 = 密钥/DB 代码被打进浏览器 bundle | react.dev use-client ✅ |

## E. 备选区（用户裁剪，冻结存档，不进正式清单）

### E1. a11y 全路 12 条（子代理调研，W3C 一手来源，含完整检查点与 URL）

| # | 候选 | 拟落点 | 来源 |
|---|---|---|---|
| 1 | 原生元素优先，role 即承诺（div+role 重造控件须兑现整套键盘语义） | code | w3.org/TR/using-aria + webaim.org/projects/million |
| 2 | 自定义 widget 键盘契约对表 APG 模式（combobox/dialog/menu/tabs） | code | w3.org/WAI/ARIA/apg/patterns/combobox |
| 3 | 模态框焦点生命周期四段（移入/圈禁/Esc/还原） | code | w3.org/WAI/ARIA/apg/patterns/dialog-modal |
| 4 | SPA 路由切换焦点去向+title+播报三件事 | spec | gatsbyjs.com 用户实测 + WCAG 2.4.3 Understanding |
| 5 | 表单错误可编程关联（aria-describedby/aria-invalid+焦点移动） | code | w3.org/WAI/tutorials/forms/notifications |
| 6 | 认证流程无认知测验路径（禁拦粘贴/2FA 可粘贴，WCAG 3.3.8） | spec | WCAG22 Understanding accessible-authentication |
| 7 | live region 实现正确性（先空置存在再注入；polite/assertive 语义） | code | MDN Live_regions |
| 8 | 拖拽必有单指针替代（WCAG 2.5.7；仅键盘替代不满足） | spec | WCAG22 Understanding dragging-movements |
| 9 | 获焦元素不被 sticky 层遮没（WCAG 2.4.11；scroll-padding 修法） | code | WCAG22 Understanding focus-not-obscured |
| 10 | 触达目标尺寸例外判断（24px；等价控件/essential 真伪，WCAG 2.5.8） | spec | WCAG22 Understanding target-size |
| 11 | 流程内不强迫重复输入（WCAG 3.3.7；自动回填/同地址勾选） | spec | WCAG22 Understanding redundant-entry |
| 12 | alt/可访问名称语义质量（功能图标写功能不写外观） | code | w3.org/WAI/tutorials/images |

注：#3（模态框焦点/Esc）与 #5（表单错误恢复）同时是纯键盘交互 UX 正确性，如愿意可以非 a11y 名义收进 B 组，已单独提请复核。

### E2. 多端条目（用户裁剪）

- 触屏 vs 鼠标（hover 依赖失效）、safe-area 适配、移动键盘 inputmode/enterkeyhint —— 均剔除。

### E3. 调研中主动淘汰（不值得进清单）

- minify/console 清理/const-let/TS strict/lint 配置类 —— 构建与 lint 层的活，非评审语义项（Front-End-Checklist 里大量此类）。
- SEO 节（hreflang/meta）—— 面向内容站，与当前项目面不符；需要时另起 domain。
- 浏览器兼容基线（Baseline）—— 工具（browserslist/caniuse CI）活。
- 「记得加 useMemo」类过时性能建议 —— 与 Compiler 时代方向相反，明确不收。

## F. 调研诚实边界

- 〔未核实〕标记的条目（A2/A4/A6/A8/B6/C1/C2/D6 及 B3 局部）依据模型知识/业界共识，未逐字核对权威页面——检查点内容成熟稳定，风险低，但引用不指向具体页面。
- web.dev rendering-on-the-web（SSR/CSR 权衡）未抓取：渲染策略选型未入候选，如需要可补一条。
- web.dev inp.html 已抓取但未细读（阈值已从 vitals 页核实）。
- 子代理调研故障复盘：本日 WebFetch 后端在子代理侧挂死率约五成（并行/串行皆中招），最终 React/性能/安全/汇编四路全部由主 session curl+WebFetch 完成；a11y 为唯一子代理完整跑通的路。
