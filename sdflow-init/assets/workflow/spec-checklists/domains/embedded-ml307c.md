# 领域规则集：ML307C（蜂窝模组 · 嵌入式芯片 delta）

> `extends: embedded` —— ML307C / FreeRTOS-on-ML307C 平台专属设计审查规则；
> RTOS+C 通用维度见 [`embedded.md`](./embedded.md)，通用质量门禁见 [`../spec-quality-base.md`](../spec-quality-base.md)。
>
> 读 ML307C 完整规则 = `base` + `embedded` + `embedded-ml307c` 三层并集。
> 保留平台/SDK 真实技术内容（`cm_calloc`、CMSIS-RTOS、二进制配置结构体、SConscript 等）；
> 通用的「规则合规声明」「Capability 完整性」由 base（BASE-04 / BASE-01·17）覆盖，本层不重复。

---

| ID | 规则 | 触发条件 | 检查点 |
|----|------|---------|--------|
| ML307C-01 | **并发与中断安全** | 新增 `osTimerNew` 回调 / URC 回调 / 线程 | 声明遵守定时器回调安全约束；线程优先级与创建时序（高优先级线程在 `osThreadNew` 后立即抢占，`initialized` 标志须在创建前置 `true`）；多 mutex 声明固定获取顺序防死锁；跨任务用「信号 + 工作线程」，不在回调/中断上下文直接跑业务逻辑 |
| ML307C-02 | **二进制配置结构体持久化** | 配置结构体变更 | `version` 递增 + `migrate` 回调；新字段**追加在结构体末尾**（不中间插），兼容旧 flash blob；为新字段设默认值；若有结构体大小的静态断言（`_Static_assert`），同步更新期望大小 |
| ML307C-03 | **Flash 写入触发点** | 涉及持久化写入 | 写入触发时机明确，且为**唯一触发点**（如统一的重启前动作钩子），而非多处分散触发 |
| ML307C-04 | **环形缓存队列** | 引入缓存队列 | 静态数组分配 + mutex 保护 + 满时覆盖策略明确 |
| ML307C-05 | **内存与栈（平台具体化）** | 新增模块 / 线程（细化 EMB-02·03） | 使用模组 SDK 分配器 `cm_calloc`/`cm_free`，不用标准 `malloc`/`free`；栈大小以平台栈基准单位的倍数估算；新源文件在 SConscript 中按高频调用（RAM 段）vs 低频操作（flash 段）分类登记 |
| ML307C-06 | **时间戳降级（RTC/uptime）** | 涉及时间戳 | 区分模组 RTC（绝对时间）与 uptime（相对时间）；规划三层降级：模组 RTC → uptime 回推 → 服务端反推 |
| ML307C-07 | **缓存优先转发** | 数据缓存转发路径 | 遵循「缓存优先转发」：RX 无条件入队、定时器只发信号、三类错误分类（回压 / 丢弃 / 跳过） |

*规则集 v1 · extends embedded · 平台专属（ML307C）· 不含具体项目文件耦合*
