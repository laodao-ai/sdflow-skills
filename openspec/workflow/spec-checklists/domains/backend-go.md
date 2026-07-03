# 领域规则集：Go（后端语言 delta）

> `extends: backend` —— 只列 **Go 语言习惯**特有的设计审查规则；后端通用维度见
> [`backend.md`](./backend.md)，通用质量门禁见 [`../spec-quality-base.md`](../spec-quality-base.md)。
>
> 读 Go 后端完整规则 = `base` + `backend` + `backend-go` 三层并集。

---

| ID | 规则 | 触发条件 | 检查点 |
|----|------|---------|--------|
| GO-01 | **goroutine 并发与同步** | 多 goroutine 竞争写同一共享状态 | 加锁策略明确（`sync.Mutex` / `sync.RWMutex` / channel 二选一并说明理由）；避免数据竞争 |
| GO-02 | **goroutine 生命周期** | 启动长期 goroutine | 受 `context` 控制；有退出路径（channel close / context cancel）；无泄漏（启动处即规划终止条件） |
| GO-03 | **TOCTOU 与原子性** | 先查后改的操作（查余额再扣款等） | 识别 check-then-use 竞态；配合 DB 乐观锁（version 字段）或悲观锁（`SELECT FOR UPDATE`）保证原子性 |
| GO-04 | **panic recovery** | 新增 handler / goroutine | 是否有全局 recovery middleware，还是依赖各处自理；goroutine 内 panic 不会被 handler recovery 捕获，需就地 recover |
| GO-05 | **定时任务重叠防护** | cron / `time.Ticker` 周期任务 | 重叠执行防护（分布式锁 / 单例 worker），避免上一轮未结束下一轮又起 |
| GO-06 | **资源清理** | 打开连接 / 文件 / 锁 | `defer` 释放；连接池在 shutdown 时正确关闭；避免 defer 在循环内堆积 |

*规则集 v1 · extends backend · 项目无关*
