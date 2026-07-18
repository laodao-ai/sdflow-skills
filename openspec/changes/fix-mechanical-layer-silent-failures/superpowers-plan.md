---
impl-pipeline: tickets
---

## Global Constraints

> 以下条款**逐字**摘自本 change 的 `design.md` / `proposal.md`，作为每个 implementer 与 reviewer 子代理的共享注意力透镜。

### 来自 design.md D1（截断）

**边界（MUST）**：只认 UTF-8，**MUST NOT** 演化成编码检测 / 嗅探——那是无界面，正是基准 ⑤ 的警号（「每轮 review 都在同一个函数里补一个新分支」）。

### 来自 design.md D2（子进程）

**🔴 诚实边界（MUST NOT 声称根治）**：父进程被 **SIGKILL** 时 trap 不可执行，实测孤儿**仍存活**。shell 层无解。文档与实现 **MUST** 显式登记该残余。

### 来自 design.md「可观测性」

- **新增 stderr 内容 MUST NOT 含 context 正文**——只报字节计数与 PID（该内容未经出境扫描）。

### 来自 design.md「安全与数据保护」

- **截断改动位于 `secret_scan` 之后**〔广审已核实定论，非待办〕：`secret_scan "$ctx"`（:153）在截断分支（:158）**之前**扫**整个 context 文件**，`do_exec` 另有预扫 ⇒ 修改截断**不缩小**密钥扫描覆盖面，无出境安全回归。
- **不改出境侧扫描**：runner 回传的 findings 仍走既有 `secret_scan`（`host-adaptive-execution`「出境安全三件套对两条 runner 路径一视同仁」）。

### 来自 design.md「Compliance」

- **D-1**：上方「代码事实」表全部经 grep 核验并由接地镜逐条复核，无记忆直写。
- **D-4**（外部依赖声明超时与回滚）：runner 超时沿用既有 `--timeout`（缺省 300s）+ `timeout -k 10`；本 change 无写盘操作 ⇒ 无回滚路径需求。
- **基准 ⑤**：D1 明确限定 UTF-8 有界面，禁止演化为编码嗅探。

### 来自 proposal.md「Non-Goals」（每条附可证伪假设——假设被证伪须停下重议，MUST NOT 自行扩范围）

- **不改 recorder 侧任何代码**（B11/B12 已拆出）。*可证伪假设*：B9/B10 的修复只触及 `outside-voice.sh`，与 recorder 取数路径零交集——若实现期发现必须动 recorder 才能完成，则假设被证伪，须停下重议拆分决定。
- **不做 R7（截断覆盖面诚实）**。*可证伪假设*：「截断产出合法 UTF-8」与「截断了要说出来」是两件可分离的事——若发现不做 R7 就无法验证 R1 的效果，则假设被证伪。
- **不做「让截断变聪明」**（分块多轮送 / 动态调上限 / 按内容智能裁剪）。*可证伪假设*：保头尾各半的既有策略本身不在本次讨论范围，本次只保证它产出的字节合法——若发现字符边界安全无法在现策略下达成，则假设被证伪。
- **不改锚行字段与 `anchor_lint` 合法组合矩阵**。*可证伪假设*：B9 修复后 `reason_code` 由 `exec-error` 变 `ok` 属既有枚举内取值变化；B10 引入的 143 由既有 catch-all（未知码 ⇒ 保守 `exec-error`）吸收——若需新状态才能诚实落锚，则假设被证伪。
- **不做 async/backgrounding 相关改动**。*可证伪假设*：B10 只涉及 `do_exec` 内部信号与子进程，不触碰两层 SKILL 的字节等值 marker 段——若修复必须改段内内容，则假设被证伪，须同步两侧并跑 parity 门。

### 来自 proposal.md「Compliance」与「利益相关方」

- `adr/0005`（dev/runtime checkout 分离）：遵守——改 `assets/hack/` 后须在开发 checkout 跑 `setup.sh` 才测得到。
- `adr/0018`（机械校验器输出诚实性）：遵守——SIGKILL 残余显式登记，**不声称根治**。
- 基准 ⑤（无界语法禁手搓）：**UTF-8 是有界语法面**（≤4 字节、continuation 形态确定）⇒ 边界回扫合规，实测 201 切点 0 失败。**禁止演化成通用编码嗅探器**——只认 UTF-8，不做编码检测。
- **下游消费项目**：`outside-voice.sh` 是 bundle **唯一权威源**，改动经 `sdflow-init update` 推给所有消费仓。**禁止只改仓内副本。**
- **运行 checkout 纪律**：改 `assets/hack/` 下脚本后**必须重跑 `setup.sh`**（拷贝非 symlink），否则新 SKILL 调旧脚本。

### 实现事实基线（design.md「代码事实」表，已 grep 核验）

| 事实 | 出处 |
|---|---|
| 截断用 `head -c` / `tail -c` 在字节边界切 | `outside-voice.sh` `render_prompt()`（:160, :162） |
| trap 只清 workdir、runner 前台执行 | `do_exec()`：`trap "rm -rf '$workdir'" EXIT`（:202） |
| 脚本是 **bash 不是 POSIX sh**，且**无 `set -e`**（只有 `set -u`） | 第 1 行 `#!/usr/bin/env bash`；:57 |
| `secret_scan "$ctx"` 在截断分支**之前**扫整个文件 | :153（截断在 :158）；`do_exec` 另有预扫 |

---

### Task 1: 截断产出的两半各自都是合法 UTF-8

**Blocked-by:** none
**R-ID:** R1

超长 context 被截断后送给跨模型 runner 时，runner 不再因非法字节拒收整个 prompt。头段与尾段**分别**在严格模式下解码 UTF-8 都成功——不是「拼起来合法」，是各自合法（两半被分别嵌进 prompt 的不同位置）。

纯 ASCII 语料经过截断时不产生任何额外损耗（丢弃 0 字节）——修复不能以「无脑多切几个字节」的方式蒙混过关。

截断发生时，操作者能从 stderr 看出**实际丢弃了多少字节**，据此判断截断是否吃掉了有效内容。该输出只含计数，不含 context 正文。

本票的边界回扫只处理 UTF-8 这一种编码；不引入任何形式的编码检测或嗅探。

- [x] 截断后头段、尾段分别以严格模式解码 UTF-8 成功，覆盖一段混合 ASCII / 3 字节 CJK / 4 字节 emoji 语料在截断区间内的**每一个**切点偏移，失败数为 0
- [x] 纯 ASCII 语料经截断丢弃 0 字节
- [x] 存在一个变异验证：把边界回扫改成恒返回 0（即退化回按字节切）后，上述切点扫描断言**转红**——证明该测试真的承重
- [x] 截断时 stderr 可见实际丢弃字节数，且新增输出不含 context 正文
- [x] 密钥扫描覆盖面未缩小（`secret_scan` 仍先于截断扫整个 context 文件）

### Task 2: 父进程被回收时 runner 子进程必死

**Blocked-by:** none
**R-ID:** R2

helper 被 SIGINT / SIGTERM / SIGHUP 回收后，它启动的 runner 子进程不再存活为孤儿、不再 reparent 到 PID 1 继续跑满内层超时烧 API 调用。

runner 的退出码语义不因此改变：正常完成的 0、超时的 124、以及其他非零码都原样透传给调用方，锚行 `reason_code` 的取值不发生非预期漂移。

清理路径在 stderr 留下可见痕迹（终止了哪个 PID），让「父被回收」这件事在日志里看得见，而不是静默消失。

父进程被 **SIGKILL** 时孤儿仍会存活——这是 shell 层无解的残余。本票**必须**把它显式登记为已知残余，**MUST NOT** 在任何文档或输出中声称孤儿问题已被根治。

- [x] 起 helper → 从外部发 SIGTERM → `ps` 验尸，无 ppid=1 的残留 runner 进程
- [x] 退出码无回归：`0` / `124` / 其他非零码在改造后仍原样透传
- [x] 清理时 stderr 记录被终止的 runner PID，且该输出不含 context 正文
- [x] SIGKILL 残余在文档中被显式登记为不可消除的边界，措辞不声称「已消除孤儿」

### Task 3: 修复在 Linux 上同样成立，且未破坏既有约束

**Blocked-by:** 1,2
**R-ID:** R1, R2

前两票的行为在 Linux 上与 macOS 一致——不接受「macOS 绿就算过」。切点扫描与子进程验尸在 ubuntu 泳道上同样跑绿。

改动经开发 checkout 的安装流程真实生效（`assets/hack/` 下是拷贝非 symlink，不重装就是新 SKILL 调旧脚本），全套件测试通过，且两层 SKILL 的 async 字节等值 marker 段未被触碰（Non-Goal 守卫）。

用一段真实的超长中文 context 端到端跑一次，坐实 Success Metric 1 的度量——记录 rc 与锚行 `reason_code`。

- [ ] Linux CI 泳道纳入 Task 1 的切点扫描与 Task 2 的进程验尸，两者在 ubuntu 上绿
- [ ] 开发 checkout 已重跑安装流程，测到的是新脚本而非旧拷贝
- [ ] 全套件 pytest 绿
- [ ] async marker 段字节等值 parity 门通过（未触碰两层 SKILL 的 async 段）
- [ ] 以真实中文 diff 造 >200KB context 实跑一次 `outside-voice.sh exec`，记录 rc 与锚行 `reason_code`
