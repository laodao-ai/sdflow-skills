# T45 engine.js 四态行为验证（chrome-devtools 真浏览器）

> engine.js 无 pytest——本记录是 T45 的行为级验证网（BR-9 硬约束）。
> 环境：`python3 -m http.server` rooted at `openspec/`，chrome-devtools MCP 驱动，2026-07-05。
> 服务的 engine.js 已确认为新版（含 `resolveInitialDir`）。

| 态 | URL hash | 期望 | 实测 | 判定 |
|----|----------|------|------|------|
| ① scoped 深链 | `#/changes/review-tool-followups/` | 首屏直接 scoped 到该 change（非全树 INDEX） | pathBar=`/changes/review-tool-followups/`；侧栏=该 change 自身文件（design/proposal/tasks…）+🏠+↑；notice=null | ✅ |
| ② 任意同源路径（宽目标） | `#/specs/spec-workflow/spec.md` | 深链亦生效、渲染该 spec 文档 | title=`/specs/spec-workflow/spec.md`；body="spec-workflow Specification…"；notice=null | ✅ |
| ③ 跨源守卫 | `#//evil.com/x` | 拒绝跨源、回落全树 INDEX、不越界 fetch | reload 后 title=`/INDEX.md`（未落 evil.com） | ✅ |
| ④ 陈旧 404 回落显形 | `#/changes/does-not-exist/` | 回落 INDEX + notice 出现 + 不卡死 + 清坏 hash 防递归 | hash=已清（`replaceState` F-D）；title=`/INDEX.md`；notice="深链未找到（可能已归档），已回首页。"；notice 为 `#content` 子节点（sibling of contentBody，未被 innerHTML 擦，NEW-1）；侧栏 8 链接不卡死；无"加载失败" | ✅ |

**结论**：A1（自派发，navigate 吞错不阻碍 404 检测）· A2（notice 回落后注入、专用节点不被擦）· A3（origin 守卫抽 pathname）· A7（`#/`→INDEX 一致）· A8（`replaceState` 写回/Back）· F-D（清坏 hash 防递归）全部机制真浏览器验证通过。

**附**：hash-only 变更不重跑 bootstrap（无 hashchange 监听，与设计一致）——深链首屏靠整页加载触发，符合"打开分享的深链 URL"场景。
