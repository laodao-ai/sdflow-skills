# 代码审查领域：嵌入式（RTOS + C）

> `extends: base` —— 嵌入式代码审查特有维度；通用维度见 [`../code-review-base.md`](../code-review-base.md)。
> 不含具体芯片/SDK 专属约束（堆分配器名、构建脚本等）——那些在芯片 delta 文件。

---

| ID | 规则 | 触发条件 | 检查点 |
|----|------|---------|--------|
| CR-EMB-01 | **受限回调上下文合规**〔TG-26〕 | 定时器/ISR/URC/UART RX 等受限回调 | 回调有 `@context: restricted-callback` 类注释；回调体（含完整调用链）无内存分配、无阻塞等待（mutex/delay/semaphore/join）、无 IO、无（含 mutex 的）日志宏；实际工作 defer 到工作线程（消息队列/信号量） |
| CR-EMB-02 | **内存分配失败处理** | 含动态分配 | 所有 malloc/calloc（及平台等价 API）查 NULL；NULL 有明确动作（LOG+error/assert/fallback），不默默解引用；alloc/free 配对，early-return 路径都释放 |
| CR-EMB-03 | **线程初始化顺序** | 新增 RTOS 线程 | `initialized` 标志在创建线程（osThreadNew 等）**之前**置 true（高优先级线程创建后立即抢占，读到 false 会静默退出）；初始化失败回滚重置 false |
| CR-EMB-04 | **volatile 正确性**〔TG-26〕 | ISR/回调与线程共享变量 | 共享变量加 `volatile`；volatile 变量只做简单读写（避免参与复杂表达式致重复读）；多核/DMA 加必要内存屏障 |
| CR-EMB-05 | **栈深度与递归** | 新增函数/线程 | 无递归（RTOS 任务栈有限，递归致不可预期溢出）；栈上无大数组（>256B → 静态/全局）；最深调用链帧大小在栈范围内（含余量） |
| CR-EMB-06 | **无 busy-wait** | 含轮询/等待逻辑 | 无 `while(cond){}` 忙等（polling without yield）；轮询加 osDelay/taskYIELD 释放 CPU；定时重试由 RTOS 定时器驱动而非死循环+sleep |

> 注：并发互斥、整数类型、错误路径、常量魔法数字等已由 base（CR-05/06/02/08）覆盖，本层不重复。

*规则集 v1 · extends base · 项目无关*
