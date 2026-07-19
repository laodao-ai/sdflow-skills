# tasks — fix-mechanical-layer-silent-failures

> Requirement ID 对应 `proposal.md` 优先级表的 R1–R2，双向追溯，无幽灵任务。
> **范围经三轮评审后收缩**：recorder 侧（B11/B12）连同其结构性根因拆出为 `T170` 统一处理；R7（截断覆盖面诚实）拆出为 `T171`。收缩依据见 `proposal.md`「范围收缩记录」。

## 1. 截断字符边界安全（R1 · B9）

- [x] 1.1 【R1】在 `outside-voice.sh` 加 UTF-8 边界回扫：头段回退到完整字符结尾、尾段跳过前导 continuation 字节；只认 UTF-8，**不做编码检测**（基准 ⑤）
- [x] 1.2 【R1】`render_prompt()` 的 `head -c` / `tail -c` 切点接入回扫结果
- [x] 1.3 【R1】stderr 增补实际丢弃字节数；**MUST NOT** 写出 context 正文（未经出境扫描）
- [x] 1.4 【R1】测试：连续切点扫描——混合 ASCII / 3 字节 CJK / 4 字节 emoji 语料，覆盖区间内每个偏移，断言**头尾两段分别**以严格模式解码 UTF-8 成功
- [x] 1.5 【R1】测试：纯 ASCII 语料丢弃 0 字节（不引入无谓损耗）
- [x] 1.6 【R1】**变异验证**：把回扫改成恒返回 0，1.4 必须转红——否则该测试不承重
- [x] 1.7 【安全复核】〔广审已定论，不留实现期〕`secret_scan "$ctx"`（:153）在截断分支（:158）**之前**扫整个文件，`do_exec` 另有预扫 ⇒ **无出境安全回归**

## 2. runner 子进程生命周期（R2 · B10）

- [x] 2.1 【R2】`do_exec()` 改后台启动 runner + 记 PID + `wait` 取回退出码
- [x] 2.2 【R2】清理函数：`kill -TERM` → 宽限 → `kill -KILL` 兜底 → 删 workdir；trap 覆盖 `INT TERM HUP` 与 `EXIT`
- [x] 2.3 【R2】stderr 记「已终止 runner PID N」
- [x] 2.4 【R2】测试：起脚本 → 外部 SIGTERM → `ps` 验尸，断言无 ppid=1 的残留 runner
- [x] 2.5 【R2】测试：退出码无回归——`0` / `124` / 其他非零码经 `wait` 后原样透传
- [x] 2.6 【R2】文档显式登记 **SIGKILL 残余**（trap 不可执行、孤儿仍存活），**MUST NOT** 写成「已消除孤儿」

## 3. 跨平台闭环与收尾（A1）

- [x] 3.1 【A1】`mechanical-gates.yml`（ubuntu-latest）纳入 1.4 切点扫描与 2.4 验尸测试，闭 Linux 侧未实测缺口
- [x] 3.2 开发 checkout 跑 `bash setup.sh`（`assets/hack/` 是拷贝非 symlink，不跑就是新 SKILL 调旧脚本）
- [x] 3.3 全套件 pytest 绿
- [x] 3.4 跑 `hack/check_async_branch_parity.py`，确认未触碰两层 SKILL 的 async 字节等值 marker 段（Non-Goal 守卫）
- [x] 3.5 用真实中文 diff 造 >200KB context 实跑一次 `outside-voice.sh exec`，记 rc 与锚行 `reason_code`（Success Metric 1 的度量）

## 测试覆盖图〔TG-18〕

```
code path                                    │ 测试类型            │ 任务
─────────────────────────────────────────────┼────────────────────┼──────
outside-voice.sh  utf8 边界回扫              │ 参数化单元(切点扫描)  │ 1.4
                  ├─ 纯 ASCII 退化           │ 单元               │ 1.5
                  └─ 承重验证                │ 变异               │ 1.6
                  render_prompt 截断接入      │ 单元(解码断言)       │ 1.4
                  丢弃字节数 stderr           │ 单元               │ 1.3
                  secret_scan 次序           │ ✅已核实(广审定论)   │ 1.7
                  do_exec 子进程回收          │ 集成(起进程+信号+ps)  │ 2.4
                  退出码透传 0/124/其他       │ 集成               │ 2.5
                  SIGKILL 残余               │ 不测(登记为残余)     │ 2.6
─────────────────────────────────────────────┼────────────────────┼──────
Linux 平台一致性(A1)                          │ CI 泳道             │ 3.1
async marker 段未被碰                         │ 机械门(parity)      │ 3.4
真实超长中文 context 端到端                    │ 手工实跑(度量锚)     │ 3.5
```

**覆盖缺口（显式登记，非遗漏）**：
- **SIGKILL 孤儿**——不可 trap，**无测试可写**，登记为残余边界（2.6）。
- **`outside-voice.sh` 自身的版本偏斜**——它不走 recorder 取数路径、无诊断通道，**不在本 change 任何机制的保护范围内**。
