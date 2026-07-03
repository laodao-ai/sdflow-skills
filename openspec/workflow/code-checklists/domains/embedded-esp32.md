# 代码审查领域：ESP32-C3（WiFi SoC · 芯片 delta）

> `extends: embedded` —— ESP32-C3 / ESP-IDF 平台专属代码审查项；
> RTOS+C 通用见 [`embedded.md`](./embedded.md)，通用维度见 [`../code-review-base.md`](../code-review-base.md)。
> 保留平台/SDK 真实技术内容（`esp_timer`、`IRAM_ATTR`、`*FromISR`、`heap_caps`、NVS、`RTC_NOINIT_ATTR`）；不含具体项目文件路径。

---

| ID | 规则 | 触发条件 | 检查点 |
|----|------|---------|--------|
| CR-ESP32-01 | **esp_timer 回调安全** | 新增 `esp_timer` 回调 | 回调及调用链无 Level 0 操作（`vTaskDelay`、`xSemaphoreTake(portMAX_DELAY)`、NVS 读写、`esp_restart`）；回调内 `xQueueSend` 超时参数必须为 0（非阻塞），>0 即违规；Level 1 操作（GPIO/日志/gettimeofday）须标注确认；高频回调（≤100ms）避免频繁日志；重操作（NVS 写/网络发送）defer 到工作线程 |
| CR-ESP32-02 | **ISR 安全** | 新增中断 | ISR 及调用链**所有**函数标 `IRAM_ATTR`；仅用 `*FromISR` 变体 FreeRTOS API；无 malloc/calloc/free、无日志宏、无 NVS/Flash；用 `xHigherPriorityTaskWoken` + `portYIELD_FROM_ISR`；与 task 共享变量标 `volatile` |
| CR-ESP32-03 | **堆内存** | 含动态分配 | 标准 `malloc`/`calloc`/`free`；需特殊内存区（DRAM/IRAM）用 `heap_caps_malloc`/`heap_caps_free` 配对；NULL 检查；队列消息数据按「生产者分配、消费者释放」约定；值语义的发送 API 调用方传栈/静态变量地址，勿额外 malloc 致原指针泄漏 |
| CR-ESP32-04 | **NVS 配置迁移** | 改配置结构体 | 新字段追加末尾；对应升级后行为标志（`AFTER_UPGRADE_CLEAR_DATA`/`UPDATE_CONFIG`/`FACTORY_ALL`）已设置；loadDefault 为新字段设默认；改结构（运行配置/累积数据/log/ringbuffer 条目）时评估旧设备升级后的数据兼容性 |
| CR-ESP32-05 | **NVS Ringbuffer** | 含 ringbuffer 操作 | push 在工作线程中（非 esp_timer 回调）；操作在对应 mutex 保护下；满时覆盖最老 + WARN 可区分；RX 解析无条件入缓存、不依赖网络/NTP 就绪 |
| CR-ESP32-06 | **文件注册与栈** | 新增 .c/头文件 | 新 `.c` 目录注册到构建系统 `SRC_DIRS`、头文件目录注册 `INCLUDE_DIRS`；外部组件依赖在 `REQUIRES`/`PRIV_REQUIRES` 或组件清单声明；任务栈以平台基准单位倍数定义；优先级与现有体系一致；栈上无大数组（>256B） |
| CR-ESP32-07 | **日志格式** | 新增日志 | 每个新 `.c` 定义 `static const char *TAG`；用项目封装日志宏，不直接用 `ESP_LOGI` 等；格式符与类型严格匹配（uint32→%lu、uint16→%hu、int32→%ld、size_t→%zu）；单位标签一致；同函数不同路径用不同消息文本 |
| CR-ESP32-08 | **数据时间戳** | 含时间戳 | 用封装的时间 API（封装 gettimeofday），不直接调底层；`RTC_NOINIT_ATTR` 变量语义正确（软重启保留、硬断电为随机值——定义处不赋初值）；uptime（`esp_timer_get_time`）与 RTC（`gettimeofday`）语义分离、不混用同一字段 |

*规则集 v1 · extends embedded · 平台专属（ESP32-C3）· 不含具体项目文件耦合*
