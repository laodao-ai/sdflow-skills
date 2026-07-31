# 领域规则集：ESP32-C3（WiFi SoC · 嵌入式芯片 delta）

> `extends: embedded` —— ESP32-C3 / ESP-IDF 平台专属设计审查规则；
> RTOS+C 通用维度见 [`embedded.md`](./embedded.md)，通用质量门禁见 [`../spec-quality-base.md`](../spec-quality-base.md)。
>
> 读 ESP32-C3 完整规则 = `base` + `embedded` + `embedded-esp32` 三层并集。
> 保留平台/SDK 真实技术内容（`esp_timer`、`IRAM_ATTR`、NVS、`heap_caps`、OTA 双槽、`RTC_NOINIT_ATTR` 等）；
> 通用的「规则合规声明」「Capability 完整性」由 base（BASE-04 / BASE-01·17）覆盖，本层不重复。

---

| ID | 规则 | 触发条件 | 检查点 |
|----|------|---------|--------|
| ESP32-01 | **esp_timer 回调安全** | 新增 `esp_timer_create()` 回调 | 回调内每个操作按三级模型分类（Level 0 禁止 / Level 1 标注 / Level 2 推荐）；确认无 Level 0 违规（`vTaskDelay`、NVS I/O、`portMAX_DELAY` 等）；重操作（NVS 写、网络发送）走「回调发信号 → 工作线程处理」defer 模式 |
| ESP32-02 | **ISR 安全与 IRAM** | 新增 GPIO / 硬件中断 | ISR 及其调用链全部 `IRAM_ATTR`；ISR 仅做最小工作（读参数 + `xQueueSendFromISR` / `xSemaphoreGiveFromISR`），业务逻辑 defer 到工作线程；ISR 与 task 共享变量标 `volatile` |
| ESP32-03 | **NVS 配置与升级标志** | 配置结构体变更 | 规划升级后行为标志（`AFTER_UPGRADE_*`：clear data / update config / factory all）；新字段**追加在结构体末尾**，兼容旧 NVS blob；各配置模块的默认值函数为新字段设默认 |
| ESP32-04 | **内存区域分配** | 新增模块 / 需特殊内存 | 一般用标准 `malloc`/`calloc`/`free`；需特殊区域（IRAM / DRAM / PSRAM）时用 `heap_caps_malloc()` 并说明原因 |
| ESP32-05 | **栈预算与构建注册** | 新增 FreeRTOS 任务 / 源文件（细化 EMB-03） | 任务栈以平台栈基准单位的倍数估算；新源文件注册到构建系统（`SRC_DIRS` / `INCLUDE_DIRS`） |
| ESP32-06 | **RTC 漂移与跨重启变量** | 涉及时间戳 / 跨重启保留数据 | 区分 RTC（`gettimeofday`，绝对）与 uptime（`esp_timer_get_time`，相对）；考虑 RTC 漂移（~6s/24h）的校时/服务端同步；`RTC_NOINIT_ATTR` 变量语义（跨软重启保留、硬断电清零）+ 硬断电后恢复/重置逻辑 |
| ESP32-07 | **WiFi/MQTT 重连** | 网络连接逻辑 | WiFi 重连指数退避（`initial/factor/cap` + 成功重置）；MQTT 用库自动重连，自定义逻辑避免裸 `while(retry)`；连接恢复事件（`WIFI_EVENT_STA_CONNECTED` / `MQTT_EVENT_CONNECTED`）触发缓存数据立即转发 |
| ESP32-08 | **OTA 双槽安全** | 涉及 OTA 升级 | 双 OTA 槽（`partitions.csv`）回滚机制；OTA 过程断电/断网恢复策略；OTA 后版本号校验 + 必要的数据迁移 |

*规则集 v1 · extends embedded · 平台专属（ESP32-C3）· 不含具体项目文件耦合*
