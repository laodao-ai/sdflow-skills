# 代码审查领域：ML307C（蜂窝模组 · 芯片 delta）

> `extends: embedded` —— ML307C / FreeRTOS-on-ML307C 平台专属代码审查项；
> RTOS+C 通用见 [`embedded.md`](./embedded.md)，通用维度见 [`../code-review-base.md`](../code-review-base.md)。
> 保留平台/SDK 真实技术内容（`cm_calloc`、`osTimerNew`、二进制配置结构体等）；不含具体项目文件路径。

---

| ID | 规则 | 触发条件 | 检查点 |
|----|------|---------|--------|
| CR-ML307C-01 | **定时器回调安全** | 新增 `osTimerNew` 回调 | 所有 osTimer 回调共享 System Timer Thread，违规致 OSA 断言→静默复位。回调体只发信号给工作线程、无其他操作；回调链无 `cm_calloc`/`cm_malloc`/`malloc`、无 `osMutexAcquire`/`osDelay`/`osThreadJoin`/`osSemaphoreAcquire`、无含 mutex 的 LOG 宏；工作线程消息循环已加新消息类型 case |
| CR-ML307C-02 | **堆内存** | 含动态分配 | 用模组 SDK 分配器 `cm_calloc`/`cm_malloc`/`cm_free`，不用标准 `malloc`/`free`、不混用；NULL 检查（细化 CR-EMB-02） |
| CR-ML307C-03 | **二进制配置结构体迁移** | 改配置结构体 | 新字段追加末尾（不中间插）；descriptor 的 version 递增、size 更新为 sizeof(新结构)；set_default 为新字段设默认；migrate 用 `if (old_version < N)` 覆盖所有已发布旧版本；位域 reserved 从高位（末尾方向）扩展，现有字段位置不变 |
| CR-ML307C-04 | **缓存与数据管道** | 含缓存转发 | 环形缓存静态数组分配（非堆）、大小由宏定义；pop_copy 在 mutex 下原子完成（先拷贝再移读指针）；满时覆盖最老 + WARN 可区分丢了哪条；RX 解析无条件入缓存，不依赖网络/NTP 就绪；发送定时器回调只发信号不直接发送；Flash 持久化唯一触发点（统一的重启前钩子） |
| CR-ML307C-05 | **文件注册与栈** | 新增 .c / 改结构体 | 新 `.c` 在构建脚本中按高频(RAM 段)/低频(flash 段)分类注册；栈大小以平台栈基准单位的倍数定义；改配置结构体布局时同步更新静态断言（`_Static_assert`）的期望大小 |
| CR-ML307C-06 | **日志格式** | 新增日志 | 每个新 `.c` 定义 `static const char *TAG`；日志级别正确（ERROR 仅真正错误）；格式符与变量类型严格匹配（uint32→%lu、uint16→%hu、int32→%ld、size_t→%zu）；单位标签与打印值一致（s/ms 不混）；同函数不同路径用不同消息文本 |
| CR-ML307C-07 | **数据时间戳** | 含时间戳 | 三层降级：RTC 可用用 RTC → 否则 uptime 回推 → 不可用留 0 由服务端反推；uptime 与 RTC timestamp 语义分离、不混用同一字段；跨重启缓存数据的时间补偿（pre_boot_age）已处理 |

*规则集 v1 · extends embedded · 平台专属（ML307C）· 不含具体项目文件耦合*
