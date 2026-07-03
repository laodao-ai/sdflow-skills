# 领域规则集：后端服务（通用）

> `extends: base` —— 只列**后端服务特有**的高风险设计审查规则；通用质量门禁见
> [`../spec-quality-base.md`](../spec-quality-base.md)。语言无关；语言习惯（如 Go）见 `backend-go.md`。
>
> 落点：后端领域项多为 **R（评审）**，部分有物证形态可落 **T**（如失败模式表）。

---

| ID | 规则 | 触发条件 | 检查点 |
|----|------|---------|--------|
| BE-01 | **DB Schema 迁移** | 新增/改/删字段、约束、类型、索引、重命名列 | v_old/v_new 对照表（列名+类型+约束+默认值+nullable），禁散文；迁移脚本含回滚步骤，不可逆操作有备份；存量数据影响（NOT NULL 列 backfill、删列前排查读写方）；大表（>100万行）锁策略（online DDL）；zero-downtime 路径（加列→双写→切读→删旧列） |
| BE-02 | **API 合约变更** | 增/改/删 endpoint、改请求/响应、改 method/status | 区分 breaking（删字段/改类型/改必填）vs non-breaking；breaking 有版本化（路径/header/渐进废弃）；完整请求/响应示例含错误响应；幂等性声明；分页+排序+边界（空/越界）；体大小/超时/限流 |
| BE-03 | **Auth / 权限边界** | 新增 endpoint 或权限相关 | 每 endpoint 声明所需权限；横向越权防护（数据层 `WHERE owner=?` 而非仅路由参数）；token 校验层级（middleware vs handler，无遗漏）；敏感数据存储/传输处理（hash/encrypt/不落日志） |
| BE-04 | **错误处理与失败模式** | 每个调用外部依赖的 codepath | 每个外部依赖（DB/缓存/第三方）声明超时；失败模式表（场景/检测/降级/用户可见性）；可重试性区分（幂等可重试，非幂等写不可）；至少描述一个真实生产失败场景 |
| BE-05 | **数据一致性** | 跨表/跨服务写操作 | 事务边界明确（哪些同 tx）；隔离级别说明；分布式最终一致方案（MQ/Saga/补偿）；缓存与 DB 一致性策略（cache-aside/write-through）+ 失效时机 |
| BE-06 | **性能与容量** | 高频查询、大批量、热点数据 | 高频查询索引规划（联合索引顺序）；N+1 风险（JOIN/batch/dataloader）；大批量分批 + 限速；缓存 TTL/内存上限/淘汰；延迟预算量化（P99<Xms） |
| BE-07 | **可观测性（后端具体化）** | 新 codepath（细化 BASE-11） | 关键操作 metrics（成功/失败/延迟 histogram）；tracing span（start/end/错误标记）；日志字段（request_id/user_id/耗时）+ 高频路径采样；健康检查 endpoint（存活 vs 就绪分离） |
| BE-08 | **退避重试与熔断** | 调用外部依赖（HTTP/gRPC/DB/MQ）的操作 | 最大重试次数 + 退避，避免立即全量重试雪崩；指数退避 + jitter；仅幂等操作自动重试；熔断策略（触发阈值 + 恢复条件） |
| BE-09 | **优雅退出与部署** | 服务级变更 | SIGTERM graceful shutdown（等待 in-flight，最长 Xs）；连接池正确关闭；zero-downtime 部署（新 handler 兼容旧 schema）；配置变更需重启 vs 热重载 |
| BE-10 | **分发管道** | 新产物（CLI 二进制 / npm 包 / 容器镜像） | 构建/发布流水线已规划；目标平台（os × arch，如 linux/darwin/windows × amd64/arm64）已定义 |
| BE-11 | **可用性与恢复目标（SLA/RTO/RPO）** | 服务级可用性 / 数据恢复有要求 | 可用性 SLA 目标（如 99.9% + 计划内停机）；RTO（故障后多快恢复）；RPO（最多可丢多少数据）；备份频率 / 保留期 / 恢复验证方式 |

*规则集 v1 · extends base · 项目无关*
