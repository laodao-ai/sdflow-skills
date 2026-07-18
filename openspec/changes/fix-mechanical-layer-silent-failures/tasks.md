# tasks — fix-mechanical-layer-silent-failures

> Requirement ID 对应 `proposal.md` 优先级表的 R1–R5，双向追溯，无幽灵任务。

## 1. 截断字符边界安全（R1 · B9）

- [ ] 1.1 【R1】在 `outside-voice.sh` 加 UTF-8 边界回扫：头段回退到完整字符结尾、尾段跳过前导 continuation 字节；只认 UTF-8，**不做编码检测**（基准 ⑤）
- [ ] 1.2 【R1】`render_prompt()` 的 `head -c` / `tail -c` 切点接入回扫结果
- [ ] 1.3 【R1】stderr 增补实际丢弃字节数（可观测性）
- [ ] 1.4 【R1】测试：连续切点扫描——混合 ASCII / 3 字节 CJK / 4 字节 emoji 语料，覆盖区间内每个偏移，断言**头尾两段分别**以严格模式解码 UTF-8 成功
- [ ] 1.5 【R1】测试：纯 ASCII 语料丢弃 0 字节（不引入无谓损耗）
- [ ] 1.6 【R1】**变异验证**：把回扫改成恒返回 0，1.4 必须转红——否则该测试不承重
- [ ] 1.7 【安全复核，design「安全与数据保护」】核对 `secret_scan` 确在截断**之前**扫整个 context 文件；若次序相反则属出境安全回归，停下重议

## 2. runner 子进程生命周期（R4 · B10）

- [ ] 2.1 【R4】`do_exec()` 改后台启动 runner + 记 PID + `wait` 取回退出码
- [ ] 2.2 【R4】清理函数：`kill -TERM` → 宽限 → `kill -KILL` 兜底 → 删 workdir；trap 覆盖 `INT TERM HUP` 与 `EXIT`
- [ ] 2.3 【R4】stderr 记「已终止 runner PID N」
- [ ] 2.4 【R4】测试：起脚本 → 外部 SIGTERM → `ps` 验尸，断言无 ppid=1 的残留 runner
- [ ] 2.5 【R4】测试：退出码无回归——`0` / `124` / 其他非零码经 `wait` 后原样透传
- [ ] 2.6 【R4】design F4 待复核假设结账（Q2）：确认不存在「父存活但 helper 收 TERM」的路径；若存在则 143 需进 `reason_code` 枚举，停下重议（触碰 Non-Goal）
- [ ] 2.7 【R4】文档显式登记 **SIGKILL 残余**（trap 不可执行、孤儿仍存活），**MUST NOT** 写成「已消除孤儿」

## 3. sibling 版本自报入口（R2 前半 · B11/B12）

- [ ] 3.1 【R2】`buglist.py` 加只读入口，输出其支持的 **frontmatter schema 上限**（整数）——不是脚本版本号、不是数据 schema 常量（design D3）
- [ ] 3.2 【R2】`todolist.py` 加同款入口，与 3.1 语义逐字一致
- [ ] 3.3 【R2】测试：两脚本各断言入口输出确定性整数

## 4. 握手闸门 + 面治覆盖（R2 后半 · R5）

- [ ] 4.1 【R2】【R5】闸门落 `issues.py` 的 `_scan_pool`（唯一派子进程点），**MUST NOT** 只补 `cmd_sweep`
- [ ] 4.2 【R2】【D5】校验前置于任何 discovery / stat / open —— 写盘类子命令须在动盘面前就关门（承 `adr/0022`）
- [ ] 4.3 【R2】失配时 stderr 给出**期望值 + 实得值 + sibling 解析路径**（只说「版本不匹配」不 actionable）
- [ ] 4.4 【R2】sibling **无该入口**（更旧版本）时按失配处置，**不得**解释为「无版本要求」而放行
- [ ] 4.5 【R5】测试（**逐调用方各一条**，承 `adr/0011`）：`sweep` / `reindex` / `batch rename` / `batch add` / `set-status` / `lint` 在偏斜下各自断言非零退出
- [ ] 4.6 【R5】测试：`reindex` 偏斜场景断言 **`INDEX.md` 字节未变**（这是 B12 的核心——写盘丢数据）
- [ ] 4.7 【R2】测试：版本一致时行为**完全无变化**（退出码 / stdout JSON 形状 / 写盘结果）
- [ ] 4.8 【R5】**变异验证**：闸门改为恒放行，4.5/4.6 必须转红

## 5. 反静默退出语义（R3）

- [ ] 5.1 【R3】`cmd_sweep`：`problems` 非空 ⇒ 非零退出（改 `[impl-review-fix] FIX-1` 处「不收紧退出码」的现状）
- [ ] 5.2 【R3】红线取 `problems` 非空、**不取 `tagged == 0`**——后者是合法幂等态
- [ ] 5.3 【Q1】通读 sweep 全部调用点后定夺 `--allow-problems` 逃生口是否提供；**若无真实使用场景则不提供**（少一个假绿入口），决定写进报告
- [ ] 5.4 【R3】【A3】通读 `/sdflow-done` §2.1 调用点，确认 fail-loud 与其「非原子、fail-closed、重跑收敛」契约相容；不相容则停下重议
- [ ] 5.5 【R3】测试：`problems` 非空 ⇒ 非零；干净盘面 `tagged == 0` ⇒ 0 退出（幂等重跑不误红）
- [ ] 5.6 【R3】**变异验证**：把退出码改回恒 0，5.5 必须转红

## 6. 跨平台闭环与收尾（A1）

- [ ] 6.1 【A1】`mechanical-gates.yml`（ubuntu-latest）纳入 1.4 切点扫描测试与 2.4 验尸测试，闭 Linux 侧未实测缺口
- [ ] 6.2 开发 checkout 跑 `bash setup.sh`（`assets/hack/` 是拷贝非 symlink，不跑就是新 SKILL 调旧脚本）
- [ ] 6.3 全套件 pytest 绿；`hack/check_async_branch_parity.py` 绿（确认未触碰两层 SKILL 的字节等值 marker 段）
- [ ] 6.4 用真实中文 diff 造 >200KB context 实跑一次 `outside-voice.sh exec`，记 rc 与锚行 `reason_code`（Success Metric 1 的度量）

## 测试覆盖图〔TG-18〕

```
code path                                    │ 测试类型          │ 任务
─────────────────────────────────────────────┼──────────────────┼──────
outside-voice.sh  utf8 边界回扫              │ 参数化单元(切点扫描) │ 1.4
                  ├─ 纯 ASCII 退化           │ 单元             │ 1.5
                  └─ 承重验证                │ 变异             │ 1.6
                  render_prompt 截断接入      │ 单元(解码断言)     │ 1.4
                  secret_scan 次序           │ 人工复核(非自动)   │ 1.7
                  do_exec 子进程回收          │ 集成(起进程+信号+ps) │ 2.4
                  退出码透传 0/124/其他       │ 集成             │ 2.5
                  SIGKILL 残余               │ 不测(登记为残余)   │ 2.7
─────────────────────────────────────────────┼──────────────────┼──────
buglist.py   版本自报入口                    │ 单元             │ 3.3
todolist.py  版本自报入口                    │ 单元             │ 3.3
─────────────────────────────────────────────┼──────────────────┼──────
issues.py    _scan_pool 握手闸门             │ 单元             │ 4.1
             ├─ sweep        偏斜            │ 集成             │ 4.5
             ├─ reindex      偏斜 + 零写盘   │ 集成(字节断言)     │ 4.5/4.6
             ├─ batch rename 偏斜            │ 集成             │ 4.5
             ├─ batch add    偏斜            │ 集成             │ 4.5
             ├─ set-status   偏斜            │ 集成             │ 4.5
             ├─ lint         偏斜            │ 集成             │ 4.5
             ├─ 版本一致无回归               │ 集成             │ 4.7
             └─ 承重验证                     │ 变异             │ 4.8
             cmd_sweep problems ⇒ 非零        │ 单元             │ 5.5
             cmd_sweep tagged==0 幂等 ⇒ 0     │ 单元             │ 5.5
             └─ 承重验证                     │ 变异             │ 5.6
─────────────────────────────────────────────┼──────────────────┼──────
Linux 平台一致性(A1)                          │ CI 泳道          │ 6.1
真实超长中文 context 端到端                    │ 手工实跑(度量锚)   │ 6.4
```

**覆盖缺口（显式登记，非遗漏）**：
- SIGKILL 孤儿——不可 trap，**无测试可写**，登记为残余边界（2.7）。
- `secret_scan` 次序——属代码阅读复核，非自动化断言（1.7）。
- Windows——recorder 脚本的 Windows 兼容仅 smoke 级（`adr/0025` 既有边界），本 change 不扩大该面。
