# 代码审查领域：后端服务（通用）

> `extends: base` —— 后端代码审查特有维度（DB / HTTP），语言无关；
> Go 语言习惯见 `backend-go.md`，通用维度见 [`../code-review-base.md`](../code-review-base.md)。

---

| ID | 规则 | 触发条件 | 检查点 |
|----|------|---------|--------|
| CR-BE-01 | **数据库操作安全** | 含 DB 读写 | 参数化查询防注入（禁字符串拼接 SQL）；事务用 defer rollback 保证 panic/early-return 自动回滚；游标/结果集 defer close 防连接泄漏；迭代后检查 rows 错误；无 N+1（循环单查 → 批量 IN）；大结果集流式处理而非全量入内存 |
| CR-BE-02 | **HTTP Handler 安全** | 新增/改 endpoint | 请求体大小限制（防超大 payload 打爆内存）；输入校验在 handler 最前（必填/格式/长度）；响应设正确 Content-Type；不重复写响应头；redirect 目标校验防 open redirect；CORS 收紧（Origin/Method/Header 最小化） |

*规则集 v1 · extends base · 项目无关*
