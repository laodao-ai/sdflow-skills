# tasks — fix-mechanical-layer-silent-failures

> Requirement ID 对应 `proposal.md` 优先级表的 R1–R7，双向追溯，无幽灵任务。
> 形状经 grill 收敛：删「sibling 版本握手」两切片（恒绿门），加「诊断分级」「退出码分类」「截断覆盖诚实」三切片。

## 1. 截断字符边界安全（R1 · B9）

- [ ] 1.1 【R1】在 `outside-voice.sh` 加 UTF-8 边界回扫：头段回退到完整字符结尾、尾段跳过前导 continuation 字节；只认 UTF-8，**不做编码检测**（基准 ⑤）
- [ ] 1.2 【R1】`render_prompt()` 的 `head -c` / `tail -c` 切点接入回扫结果
- [ ] 1.3 【R1】stderr 增补实际丢弃字节数（可观测性）
- [ ] 1.4 【R1】测试：连续切点扫描——混合 ASCII / 3 字节 CJK / 4 字节 emoji 语料，覆盖区间内每个偏移，断言**头尾两段分别**以严格模式解码 UTF-8 成功
- [ ] 1.5 【R1】测试：纯 ASCII 语料丢弃 0 字节（不引入无谓损耗）
- [ ] 1.6 【R1】**变异验证**：把回扫改成恒返回 0，1.4 必须转红——否则该测试不承重
- [x] 1.7 【安全复核】〔gstack-amendment · **广审已定论，不留实现期**（通则①）〕`outside-voice.sh:153` 的 `secret_scan "$ctx"` 在 `:158` 截断分支**之前**扫整个文件，`do_exec:204` 另有预扫 ⇒ **无出境安全回归**，截断改动不缩小密钥扫描覆盖面

## 2. runner 子进程生命周期（R4 · B10）

- [ ] 2.1 【R4】`do_exec()` 改后台启动 runner + 记 PID + `wait` 取回退出码
- [ ] 2.2 【R4】清理函数：`kill -TERM` → 宽限 → `kill -KILL` 兜底 → 删 workdir；trap 覆盖 `INT TERM HUP` 与 `EXIT`
- [ ] 2.3 【R4】stderr 记「已终止 runner PID N」
- [ ] 2.4 【R4】测试：起脚本 → 外部 SIGTERM → `ps` 验尸，断言无 ppid=1 的残留 runner
- [ ] 2.5 【R4】测试：退出码无回归——`0` / `124` / 其他非零码经 `wait` 后原样透传
- [ ] 2.6 【R4】文档显式登记 **SIGKILL 残余**（trap 不可执行、孤儿仍存活），**MUST NOT** 写成「已消除孤儿」

## 3. 诊断产生处分级 + additive 承载（R2）

- [ ] 3.1 【R2】`buglist.py`：逐个 `problems.append(...)` 点判类——「可能没读全」进阻断集，「读全了但脏」不进。判据表见 design D3
- [ ] 3.2 【R2】`todolist.py`：同款分级，与 3.1 语义逐字一致
- [ ] 3.3 【R2】`scan --json` 新增阻断集字段；**`problems` 字段类型与内容一字不动**
- [ ] 3.4 【R2】`issues.py` 自身产生的诊断同样分级（它也有 `problems.append` 点）
- [ ] 3.5 【R2】测试：完整性类诊断进阻断集、瑕疵类不进（两池各一组）
- [ ] 3.6 【R2】测试：只读 `problems` 的既有消费者解析新输出不失败（向后兼容断言）
- [ ] 3.7 【R2】**MUST NOT** 在消费方用正则/子串还原分级——若实现期发现绕不开文本匹配，停下重议（那意味着分级没落在产生处，违基准 ⑤）
- [ ] 3.8 【R2】给 `_validated_recorder_model()` 的 `schema != 1` fail-closed 补回归锁 + 变异验证（承重却无测试锁）

## 4. 收集下发 + 缺席即阻断 + 面治覆盖（R2 · R5）

> 〔gstack-amendment · 广审 critical〕拓扑经实测重定：**路径 ①**（subprocess scan，有 JSON 边界）= `sweep`/`reindex`/`rename` 后半；**路径 ②**（in-process，无字段可缺席、且写盘先于判定）= `rename` 前半；**路径 ③**（只读 `batches.md`，不碰两池）= `lint`/`batch add`/`set-status`。
> 🔴 **原 4.4 要求给路径 ③ 三个调用方写「阻断断言」——它们根本不读两池，那会是三条写不出真断言的假绿。已删。**

- [ ] 4.1 【R5】路径 ①：`_scan_pool` / `read_pool` 收集阻断集并**默认下发**（改掉 `problems_out=None` 默认丢弃）
- [ ] 4.2 【R2】**缺席 ⇒ 全部 `problems` 视为阻断**（fail-closed）；**MUST NOT** 解释为「无阻断项」
- [ ] 4.3 【R5】【D5】路径 ① 判定前置于任何 discovery / stat / open（承 `adr/0022`）
- [ ] 4.4 【R5】【D5′】**路径 ② 另立机制**：`read_rename_snapshot` 解析后、`retag` 与任何 `atomic_write` **之前**就地判完整性，非空即 fail-closed 零写盘
- [ ] 4.5 【R5】【D5′】路径 ①② 的完整性判据 **MUST 抽成单一函数共用**，MUST NOT 各写一套（防漂移，承 `adr/0011`）
- [ ] 4.6 【R5】测试（**逐调用方各一条**，只覆盖真读两池的）：`sweep` / `reindex` / `batch rename` 在阻断下各自断言非零退出
- [ ] 4.7 【R5】测试：`reindex` 阻断断言 **`INDEX.md` 与 `batches.md` 字节均未变**（B12 核心）
- [ ] 4.8 【R5】测试：**`batch rename` 阻断断言 registry 与 dated 文档字节均未变**（D5′ 核心——现状是写盘先于判定）
- [ ] 4.9 【R2】测试：**字段缺席**场景（模拟滞后产出方）断言全部按阻断处置
- [ ] 4.10 【R2】测试：阻断集为空时行为无变化——〔gstack-amendment〕**在真实仓盘面上跑**（原「造干净 fixture」不承重：fixture 刻意造干净必绿），**接受它可能红**并当作真实信号
- [ ] 4.11 【R5】**变异验证**：把判定改为恒放行，4.6/4.7/4.8/4.9 必须转红
- [ ] 4.12 【路径 ③ 显式不做】记录判定：`lint`/`batch add`/`set-status` 不读两池 ⇒ 无「读残缺」风险 ⇒ **不写阻断断言**。此为**有依据的排除**，非遗漏

## 5. 严格默认 + 退出码分类 + 逃生口（R3 · R6）

- [ ] 5.1 【R3】阻断集非空 ⇒ 非零退出，**默认开**（翻转 `cmd_reindex` 的 `--strict` 默认；红线取阻断集非空，**不取 `tagged == 0`**）
- [ ] 5.2 【R6】`sweep` 退出码分两类：`1` = 重跑可收敛（既有语义不变），`2` = 重跑无用须人介入
- [ ] 5.2b 【R6】〔gstack-amendment〕**显式透传子进程的 2**：现状 `cmd_sweep` 调 `reindex`/`batch add` 后只判 `!= 0` → `_die`（恒 exit 1）⇒ **2 被压平**。MUST 改为按子进程实际退出码分流，MUST NOT 走既有 `_die` 路径
- [ ] 5.2c 【DX·可见成本】〔gstack-amendment〕`sweep`/`reindex` 起手打印**所调脚本绝对路径 + 版本戳**——这是唯一能让「consumer+producer 双旧」场景变可见的动作（本 change 其余机制在双旧下**不在场**）。**登记为可见成本非机械门**（`adr/0021`）
- [ ] 5.3 【R6】exit 2 的 stderr 含「重跑无用」字样 + 阻断明细全列 + 涉及文件路径 + 两条出路
- [ ] 5.4 【R3】逃生口三约束：① 放行时 `INDEX.md` 头部 banner 增记「N 条阻断被放行、索引可能不完整」；② **仅认显式 CLI**，MUST NOT 支持 config / 环境变量；③ `/sdflow-done` sweep 子步 MUST NOT 自动传
- [ ] 5.5 【R3】【A3】通读 `/sdflow-done` §2.1 全部调用点，确认 exit 1/2 分治与其「非原子、fail-closed、重跑收敛」契约相容；不相容则停下重议
- [ ] 5.6 【R3】测试：缺省即严格 / 放行留疤（banner 断言）/ 逃生口不可环境化
- [ ] 5.7 【R6】测试：exit 2 场景 + exit 1 场景各一，断言退出码与 stderr 关键字
- [ ] 5.8 【R3】**变异验证**：把退出码改回恒 0，5.6/5.7 必须转红
- [ ] 5.9 【R3】INDEX banner 新增行进 golden bytes 测试

## 6. 截断覆盖面诚实（R7 · grill fold）

- [ ] 6.0 【R7】〔gstack-amendment · 广审 high〕**先把捕获权从模型手里拿走**：`outside-voice.sh` 把 truncated 落成 **per-site sidecar**（复用 `.rc` 形态，runner 只读写不了）。原设计把「模型抄写进锚行的值」当确定性信号，是**假机械门**
- [ ] 6.1 【R7】两层评审 SKILL.md 报告格式段：sidecar 为 true ⇒ 该 voice findings 段必带覆盖声明
- [ ] 6.2 【R7】`anchor_lint` 核**两件事**：① sidecar ↔ 锚行 `truncated=` **一致**（防抄错/省事写 false）；② sidecar 为 true 而报告无声明 ⇒ 判违规非零退出
- [ ] 6.2b 【R7】**降级条款**：若实现期证明 sidecar 落不下来（如 async 分支写入时序冲突）⇒ **MUST 把 R7 如实降级为语义层约定**（报告写声明、无机械核），**MUST NOT** 保留只核模型自洽的门却称其机械门
- [ ] 6.3 【R7】`openspec/workflow/tools/anchor_lint.py` 与 `sdflow-init/assets/workflow/tools/anchor_lint.py` **保持字节一致**（bundle 权威源纪律）
- [ ] 6.4 【R7】测试：truncated=true 缺声明判红 / 有声明判绿 / truncated=false 不强加声明
- [ ] 6.5 【R7】**跑 `hack/check_async_branch_parity.py`** 确认未碰两层 SKILL 的 async 字节等值 marker 段
- [ ] 6.6 【R7】确认锚行字段取值域与 `anchor_lint` 合法组合矩阵**逐一未变**（Non-Goal 守卫）

## 7. 调用方认识 exit 2（R6）

- [ ] 7.1 【R6】`sdflow-done/SKILL.md` §2.1 失败语义段补 exit 1/2 分治，标 `[grill-amendment]`
- [ ] ~~7.2 `sdflow-ship/SKILL.md` 链序~~ 〔gstack-amendment · **删**〕实测 `grep -c sweep sdflow-ship/SKILL.md` = **0**——ship 不直接调 sweep，经 `/sdflow-done` 链序。改它是无效编辑
- [ ] 7.3 【R6】跑 `hack/sync_principles.py --check` 确认 SKILL.md 改动未碰托管区块

## 8. 跨平台闭环与收尾（A1）

- [ ] 8.1 【A1】`mechanical-gates.yml`（ubuntu-latest）纳入 1.4 切点扫描与 2.4 验尸测试，闭 Linux 侧未实测缺口
- [ ] 8.2 开发 checkout 跑 `bash setup.sh`（`assets/hack/` 是拷贝非 symlink，不跑就是新 SKILL 调旧脚本）
- [ ] 8.3 全套件 pytest 绿
- [ ] 8.4 用真实中文 diff 造 >200KB context 实跑一次 `outside-voice.sh exec`，记 rc 与锚行 `reason_code`（Success Metric 1 的度量）
- [ ] 8.5 实跑一次滞后产出方场景，断言 `INDEX.md` 字节未变（Success Metric 3 的度量）

## 测试覆盖图〔TG-18〕

```
code path                                    │ 测试类型            │ 任务
─────────────────────────────────────────────┼────────────────────┼──────
outside-voice.sh  utf8 边界回扫              │ 参数化单元(切点扫描)  │ 1.4
                  ├─ 纯 ASCII 退化           │ 单元               │ 1.5
                  └─ 承重验证                │ 变异               │ 1.6
                  render_prompt 截断接入      │ 单元(解码断言)       │ 1.4
                  secret_scan 次序           │ 人工复核(非自动)     │ 1.7
                  do_exec 子进程回收          │ 集成(起进程+信号+ps)  │ 2.4
                  退出码透传 0/124/其他       │ 集成               │ 2.5
                  SIGKILL 残余               │ 不测(登记为残余)     │ 2.6
─────────────────────────────────────────────┼────────────────────┼──────
buglist.py   诊断分级(完整性/瑕疵)            │ 单元(两池各一组)     │ 3.5
todolist.py  诊断分级                        │ 单元               │ 3.5
             problems 向后兼容               │ 单元               │ 3.6
             _validated_recorder_model 回归锁 │ 单元 + 变异         │ 3.8
─────────────────────────────────────────────┼────────────────────┼──────
issues.py    _scan_pool 收集下发             │ 单元               │ 4.1
             缺席即阻断                       │ 单元(模拟滞后产出方) │ 4.6
             ├─ sweep        阻断            │ 集成               │ 4.4
             ├─ reindex      阻断 + 零写盘   │ 集成(字节断言)       │ 4.4/4.5
             ├─ batch rename 阻断            │ 集成               │ 4.4
             ├─ batch add    阻断            │ 集成               │ 4.4
             ├─ set-status   阻断            │ 集成               │ 4.4
             ├─ lint         阻断            │ 集成               │ 4.4
             ├─ 阻断集空则无回归              │ 集成               │ 4.7
             └─ 承重验证                     │ 变异               │ 4.8
             严格默认 / 留疤 / 禁环境化        │ 单元               │ 5.6
             exit 1 vs exit 2                │ 单元               │ 5.7
             INDEX banner                    │ golden bytes       │ 5.9
             └─ 承重验证                     │ 变异               │ 5.8
─────────────────────────────────────────────┼────────────────────┼──────
anchor_lint  truncated ⇒ 覆盖声明存在性       │ 单元(红/绿/不适用)   │ 6.4
             两份 tools 字节一致              │ 机械门              │ 6.3
             async marker 段未被碰            │ 机械门(parity)      │ 6.5
             锚行字段与矩阵未变               │ 人工复核 + 既有用例   │ 6.6
─────────────────────────────────────────────┼────────────────────┼──────
SKILL.md     托管区块未被碰                   │ 机械门(sync)        │ 7.3
Linux 平台一致性(A1)                          │ CI 泳道             │ 8.1
真实超长中文 context 端到端                    │ 手工实跑(度量锚)     │ 8.4
滞后产出方端到端零写盘                         │ 手工实跑(度量锚)     │ 8.5
```

**覆盖缺口（显式登记，非遗漏）**：
- **SIGKILL 孤儿**——不可 trap，**无测试可写**，登记为残余边界（2.6）。
- **`secret_scan` 次序**——属代码阅读复核，非自动化断言（1.7）。
- **逃生口被反复手敲**——三条约束只保证「留痕可审计」，**不构成机械门**；残余（`adr/0021` 可见成本定位）。
- **已出厂的滞后脚本自身**——无法回溯加保护，唯一防线是新消费方按「缺席即阻断」处置。
- **`outside-voice.sh` 的版本偏斜**——它不走 recorder 取数路径、无诊断通道，**不在本 change 任何机制的保护范围内**。
- **Windows**——recorder 脚本的 Windows 兼容仅 smoke 级（`adr/0025` 既有边界），本 change 不扩大该面。
