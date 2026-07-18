## ADDED Requirements

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

#### Scenario: SIGTERM 回收父进程后无孤儿残留

- **WHEN** `outside-voice.sh exec` 正在等待 runner，外部向其发送 `SIGTERM`
- **THEN** 该次调用派出的 `timeout` 进程及其全部后代在清理完成后均不存在（`ps` 查无 ppid 为 1 的残留 runner），临时 workdir 亦被删除

#### Scenario: 正常执行时退出码语义不回归

- **WHEN** runner 正常结束、超时（124）或以其他非零码结束
- **THEN** `outside-voice.sh` 对外呈现的退出码与改动前逐一相同（0 / 124 / 1 等既有契约取值不变）

#### Scenario: SIGKILL 残余被显式登记而非掩盖

- **WHEN** 父进程被 `SIGKILL` 强杀
- **THEN** 孤儿 runner 可能存活；该情形在设计文档中作为**已知残余边界**明确记录，实现 **不**声称已处理

### Requirement: 截断过的 voice 必须声明其覆盖面残缺

当某次 outside-voice 调用的锚行记录 `truncated="true"` 时，该 voice 在评审报告中的 findings 段 **MUST** 携带覆盖面声明（本镜基于截断上下文、中段未见），且该声明的存在性 **SHALL** 由 `anchor_lint` 机械核验。

**MUST NOT** 把截断过的 voice 与完整 voice 在报告中呈现为等价——前者无法对被挖掉的中段作任何断言，把它的 findings 当作全量覆盖是**覆盖面撒谎**，与退出码撒谎同族。

**边界**：本需求只要求「截断了要说出来」。分块多轮送、动态调整上限、按内容智能裁剪均**不在**本需求范围内。

#### Scenario: 截断时报告必带覆盖声明

- **WHEN** 某 outside-voice 站点的锚行为 `truncated="true"`
- **THEN** `anchor_lint` 在该报告中找不到对应的覆盖面声明时判违规、非零退出

#### Scenario: 未截断时不强加声明

- **WHEN** 锚行为 `truncated="false"`
- **THEN** `anchor_lint` 不要求覆盖面声明，报告无该句亦判通过

#### Scenario: 锚行字段与合法组合矩阵不变

- **WHEN** 本需求落地后运行既有锚行校验
- **THEN** `truncated` 及其余锚行字段的取值域、`anchor_lint` 的合法组合矩阵均与改动前一致（本需求只**新增**一条存在性核验，不改契约）
