# 代码审查领域：后端服务（通用）

> `extends: base` —— 后端代码审查特有维度（DB / HTTP），语言无关；
> Go 语言习惯见 `backend-go.md`，通用维度见 [`../code-review-base.md`](../code-review-base.md)。

---

| ID | 规则 | 触发条件 | 检查点 |
|----|------|---------|--------|
| CR-BE-01 | **数据库操作安全** | 含 DB 读写 | 参数化查询防注入（禁字符串拼接 SQL）；事务用 defer rollback 保证 panic/early-return 自动回滚；游标/结果集 defer close 防连接泄漏；迭代后检查 rows 错误；无 N+1（循环单查 → 批量 IN）；大结果集流式处理而非全量入内存 |
| CR-BE-02 | **HTTP Handler 安全** | 新增/改 endpoint | 请求体大小限制（防超大 payload 打爆内存）；输入校验在 handler 最前（必填/格式/长度）；响应设正确 Content-Type；不重复写响应头；redirect 目标校验防 open redirect；CORS 收紧（Origin/Method/Header 最小化）；用户可控数据进不安全 HTML 渲染前防 XSS——**仅服务端模板渲染场景**（如 Jinja2 `\|safe` / Django `mark_safe` / Rails `html_safe` / Go `template.HTML`）；客户端框架渲染 XSS 见 `domains/frontend.md` CR-FE-01（本条聚焦服务端模板渲染） |
| CR-BE-03 | **DB 层竞态** | 含并发写路径的 DB 操作 | find-or-create 类操作无唯一索引兜底会在并发下重复插入（先查后插不是原子操作）；check-then-set（先读状态再据其更新）须用带旧值条件的原子 `UPDATE ... WHERE 状态=旧值`，而非读出来判断后再单独写；状态迁移的多步更新非原子会导致中间态可见或非法跳变（双跳）；绕过 ORM/模型层校验直接写 DB（原生 SQL/批量脚本）会漏掉模型内建的约束检查 |

*规则集 v1 · extends base · 项目无关*
