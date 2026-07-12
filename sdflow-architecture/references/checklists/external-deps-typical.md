# 外部依赖典型集

> 供 SAD 第 3 节「外部系统清单」起草提名参考，也供 `intake-questionnaire.md` 第②问追问时协助 owner 枚举。命中项仍需补文档指针（无指针 → 显式登记为待补）。

- **云服务**：对象存储、CDN、云函数/Serverless、托管数据库、托管消息队列。
- **DB**：关系型（MySQL/PostgreSQL）、文档型（MongoDB）、缓存（Redis）、时序（InfluxDB/TimescaleDB）。
- **消息**：MQTT broker、Kafka、RabbitMQ、云厂商托管队列（SQS/PubSub）。
- **固件外设**：传感器/执行器串口协议、蓝牙/BLE 设备、专有硬件 SDK。
- **第三方 API**：支付网关、短信/邮件网关、地图/定位服务、第三方登录（OAuth）、监控/告警平台。

> 本清单为通用起点，不穷尽；领域特有外部依赖仍需人补，遗漏兜底见评审镜单「考虑面完整性镜」（S7，`review-lenses.md`）。
