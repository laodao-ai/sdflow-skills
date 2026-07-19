# outside-voice-exec-integrity Specification

## Purpose
`outside-voice.sh`（跨 Claude/Codex 两机队复用的 outside-voice 执行 helper）的机械层执行完整性契约：截断长 context 时不得产出非法 UTF-8、父进程被回收时不得让 runner 子进程逃逸成孤儿。两条需求各自显式登记了 shell 层/信号交付层不可消除的残余边界，实现与文档一律 MUST NOT 声称已彻底根治。
## Requirements
### Requirement: 送出的 prompt 恒为合法 UTF-8

`outside-voice.sh` 在因超长而截断 context 时，产出的 prompt **SHALL** 始终是合法 UTF-8。截断 **MUST** 在切点上回退到字符边界，**MUST NOT** 在字节边界切断多字节序列。

保留头尾两段时，**两段各自** MUST 独立合法：头段 MUST NOT 以不完整的多字节序列结尾，尾段 MUST NOT 以孤立的 continuation 字节开头。

边界回扫 **MUST** 只处理 UTF-8（有界语法面：单字符 ≤4 字节、continuation 字节形态确定），**MUST NOT** 演化为通用编码检测 / 嗅探（基准 ⑤：禁止在无界语法面上手搓解析器）。

#### Scenario: 超长中文 context 被截断后 runner 正常接收

- **WHEN** context 文件为合法 UTF-8 且字节数超过 `OV_MAX_CONTEXT_BYTES`，其中截断点落在一个多字节字符内部
- **THEN** `outside-voice.sh exec` 送出的 prompt 通过 UTF-8 解码校验，runner **不**报 `input is not valid UTF-8`，退出码为 0，调用方落锚 `reason_code="ok"`

#### Scenario: 连续切点全覆盖不产生非法字节

- **WHEN** 对含 ASCII、3 字节 CJK 与 4 字节 emoji 混合的语料，令截断阈值在一段连续字节偏移区间内逐一取值
- **THEN** 每个偏移产出的头段与尾段**分别**以严格模式解码 UTF-8 均成功，失败数为 0

#### Scenario: 纯 ASCII context 不被改动

- **WHEN** context 全为 ASCII 且超长
- **THEN** 回扫丢弃 0 字节，截断结果与按字节直接截断逐字节相同（不引入无谓损耗）

### Requirement: 父进程被回收时 runner 子进程必死

`outside-voice.sh` **SHALL** 保证：当自身因 `SIGINT` / `SIGTERM` / `SIGHUP` 被回收时，其派出的 runner 进程（`timeout` 及其后代 `codex` / `claude`）**一并终止**，**MUST NOT** reparent 到 PID 1 后继续运行至内层超时。

清理 **MUST** 覆盖 `INT TERM HUP` 三个信号，**MUST NOT** 只依赖 `EXIT` trap 清理临时目录而放任子进程存活。

**诚实边界（MUST 显式登记，MUST NOT 声称根治）**：父进程收到 `SIGKILL` 时 trap 不可执行，孤儿**仍会**产生。这是 shell 层不可消除的残余，实现与文档 **MUST NOT** 宣称已覆盖该情形。

**诚实边界（第二类，MUST 显式登记，MUST NOT 与上一条混同）**：`INT`/`TERM`/`HUP` 均为可捕获信号、trap 机制本身单一信号类型下工作正常，但**高频（3 秒内 20–150ms 随机间隔）× 多类型交替**投递会整体压垮 trap 机制本身（helper 进程被信号默认处置直接终止，`ov_cleanup` 未执行一行），实测复现率 **67%（15 次跑 10 次）**。这与上一条「trap 不可执行」同属一类失效机理，但触发条件不同（可捕获信号 ≠ SIGKILL），**MUST 分别登记**。修法（更换整套回收原语，如外层去抖节流 / `flock` 单实例互斥）属设计级决策，超出本机械层契约的修复范围；实现与文档 **MUST NOT** 因单信号路径已达成就声称「父被回收则子必死」在混合高频信号下同样成立，**MUST NOT** 将该残余弱化描述为「极少见」或「可忽略」。

#### Scenario: SIGTERM 回收父进程后无孤儿残留

- **WHEN** `outside-voice.sh exec` 正在等待 runner，外部向其发送 `SIGTERM`
- **THEN** 该次调用派出的 `timeout` 进程及其全部后代在清理完成后均不存在（`ps` 查无 ppid 为 1 的残留 runner），临时 workdir 亦被删除

#### Scenario: 正常执行时退出码语义不回归

- **WHEN** runner 正常结束、超时（124）或以其他非零码结束
- **THEN** `outside-voice.sh` 对外呈现的退出码与改动前逐一相同（0 / 124 / 1 等既有契约取值不变）

#### Scenario: SIGKILL 残余被显式登记而非掩盖

- **WHEN** 父进程被 `SIGKILL` 强杀
- **THEN** 孤儿 runner 可能存活；该情形在设计文档中作为**已知残余边界**明确记录，实现 **不**声称已处理

#### Scenario: 高频混合信号风暴残余被显式登记而非掩盖

- **WHEN** 3 秒内以 20–150ms 随机间隔向父进程交替发送 `SIGTERM`/`SIGINT`/`SIGHUP`（均为可捕获信号）
- **THEN** trap 机制存在整体被压垮、`ov_cleanup` 未执行的已知残余（实测 67% 复现），runner 与其后代可能双双存活成孤儿；该情形在设计文档中作为**已知残余边界**（与 SIGKILL 残余同属「trap 未执行」类但触发条件不同）明确记录，实现 **不**声称「父被回收则子必死」在此路径下同样成立，修法留给专门的设计级 change

