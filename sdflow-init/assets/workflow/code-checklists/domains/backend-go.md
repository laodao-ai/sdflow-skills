# 代码审查领域：Go（后端语言 delta）

> `extends: backend` —— Go 语言习惯特有的代码审查项；后端通用见 [`backend.md`](./backend.md)，
> 通用维度见 [`../code-review-base.md`](../code-review-base.md)。

---

| ID | 规则 | 检查点 |
|----|------|--------|
| CR-GO-01 | **错误包装与比较** | 用 `%w` 包装保留调用链（`fmt.Errorf("doing X: %w", err)`）；哨兵错误用 `errors.Is` 而非 `==`；HTTP handler 中 error 后有 `return`，无"未 return 继续执行"的遗漏 |
| CR-GO-02 | **Context 传播** | `ctx` 作第一参数；DB/HTTP/RPC 调用都传 ctx（支持超时取消）；不滥用 `context.Background()` 覆盖传入 ctx；外部调用用 `WithTimeout`/`WithDeadline` 设超时 |
| CR-GO-03 | **Goroutine 生命周期** | 新 goroutine 有明确退出条件（channel close / ctx.Done）；用 WaitGroup/errgroup 等待防泄漏；goroutine 内 panic 有 recover 兜底；循环变量捕获陷阱；channel 死锁风险 |
| CR-GO-04 | **资源 defer 惯用法** | 文件 / `resp.Body` 用 `defer Close()`；循环内 defer 陷阱 → 改匿名函数立即释放；锁用 `defer mu.Unlock()` 紧跟 `mu.Lock()` |
| CR-GO-05 | **类型断言 / 转换** | `interface{}`/`any` 断言用双值形式防 panic；`[]byte ↔ string` 避免不必要 copy（热路径 unsafe 须注明理由）；JSON 数字默认 `float64`，需 `int64` 用 Decoder + UseNumber |
| CR-GO-06 | **共享状态并发正确性**〔TG-26〕 | 多 goroutine 读写共享变量有一致加锁策略（Mutex/RWMutex/channel 三选一并说明理由）；check-then-act 复合操作的原子性（TOCTOU）；map 并发写保护；对照 spec 侧 GO-01/GO-03（评审实证：CR-GO-03 只管生命周期不管竞态，故新增本条） |

*规则集 v1 · extends backend · 项目无关*
