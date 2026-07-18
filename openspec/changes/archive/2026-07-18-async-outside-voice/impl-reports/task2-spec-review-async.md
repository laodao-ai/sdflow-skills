# Task 2 实现报告 — spec-review 层 host-adaptive async dispatch/collect

**Ticket**: Task 2（Blocked-by 1）· **R-ID**: R1, R2 · **分支**: `feat/async-outside-voice`

## 改动面

| 文件 | 改动 |
|---|---|
| `sdflow-spec-review/SKILL.md` | 「outside-voice helper 调用协议」节的 `exec：…` 块（原 line 285–289）整体替换为 `<!-- sdflow:async-branch:start/end -->` 圈定的**站点无关 host 调度段**（八小节 ①–⑧） |
| `openspec/config.yaml` | 追加**注释形态**的 `outside-voice.async-timeout-seconds` 可选覆盖段（沿 `model-tiers` 注释先例；零行为改动，缺键即默认 900） |

**未改动**（按 Non-Goal / 票边界）：`outside-voice.sh`、`anchor_lint` 矩阵、change 四件套、`sdflow-code-review/SKILL.md`（Task 3）、`sdflow:principles` 托管块。

## marker 圈定（ADR-5，为 Task 3 等值门预留）

- **marker 内**（站点无关，Task 3 将原样复制过去）：内层超时 config 取值与校验 ①、后台能力自探 ②、执行模式矩阵 ③、命令形态与哨兵 wrapper ④、envelope 整行锚定解析 ⑤、通知驱动 collect barrier + 安全约束 ⑥、退出码→reason_code 全表 ⑦、站点↔task_id 记账表骨架 ⑧。
- **marker 外**（两层不同，放进去会令等值门永红）：站点枚举（`site=design-voice` / `site=hr-tg`）、context 构造与 run-id/manifest 段、reuse-guard 门控（第一步 §5）、`declared-sites` 计算。
- 记账表 ⑧ 用占位行 `| <逐个填本轮涉及的站点> | … |`，不写具体站点名 ⇒ 段内保持站点无关、可整段搬运。

## 验收标准逐条证据

### 1. Claude 宿主 voice 后台派发、主 session 无 ≥330s 单次阻塞调用

③ 矩阵 async 行：内层 `$VOICE_TIMEOUT`（默认 900），外层「不适用——dispatch 调用 <1s 即返回；后台任务不受 Bash 工具超时约束」，并写明 **MUST NOT 因它"是长命令"就给 dispatch 调用设长超时**。④ 明写 async 分支「以 run_in_background 派出，立刻记下后台任务标识」。collect 走 ⑥ 通知/暂存，无单条长阻塞 Bash。

### 2. 站点↔后台任务标识映射显式列出、collect 按站点逐一取

⑧ 给出三列表格（站点 / 本轮是否 dispatch / `<task_id>` 或字面 `sync`）+ 三条 MUST：集合 = 实际 dispatch 过的站点、**与「应有锚站点集」MUST NOT 混用**、collect **按本表逐站点取**、真伪以 `dispatch-manifest.tsv` 为准不靠会话记忆。

### 3. Step3 barrier 语义

⑥ 正向 barrier 段：RUNNING 站点 **MUST 让出轮次等完成/超时通知**；MUST NOT 长 sleep、MUST NOT 自造轮询循环；**`reason_code="timeout"` 只允许由实际观测到的 `exit 124` 产生**，并注明该假绿逃得过 per-site 站点集核 ∴ 本条是唯一防线。

### 4. 哨兵 envelope 三条 —— **真跑验证（本票主要机械信号）**

构造「上游无尾换行 + 正文自带伪造哨兵」的假 voice，跑三组对照：

```
$ ./fakevoice.sh > out.txt 2>&1; rc=$?; printf '\n<<<SDFLOW_EXEC_EXIT>>>%s\n' "$rc" >> out.txt
$ od -c out.txt | tail -2
0000100   **  **  行  **  **  \n   <   <   <   S   D   F   L   O   W   _
0000120    E   X   I   T   >   >   >   1   2   4  \n
$ grep -cE '^<<<SDFLOW_EXEC_EXIT>>>[0-9]+$' out.txt
2
```

| 样本 | 整行锚定命中 | 判定 |
|---|---|---|
| A 正常 voice（**末行无尾换行**）+ 规定 `printf '\n…'` wrapper | **1** | `ok` ✅ 前置换行确实分出独立物理行 |
| B 正文含伪造 `<<<SDFLOW_EXEC_EXIT>>>0` | **2** | `exec-error`（≥2 行 = 注入的确定性信号）✅ |
| C **对照组**：朴素 `echo "<<<…>>>$rc"`（无前置换行） | **0** | 末行实际粘成 `finding 2: 末行无尾换行<<<SDFLOW_EXEC_EXIT>>>0` —— 设计预言的「把成功 voice 假降级」**实测复现** ✅ 故 wrapper 必须用 `printf '\n…'` |

⑤ 据此写死：整行锚定正则、恰好 1 行才取码、**0 行或 ≥2 行 → `exec-error`**、MUST NOT 用宽松 grep/子串/取末行。

### 5. 退出码全表无遗漏、未知码不读作 ok

⑦：`0`→ok / `124`→timeout（仅实测）/ `1`→exec-error / `2`（用法错·context 不可读）→**并入 exec-error**（枚举不新增）/ `3`→secret-hit 不 fallback / **其余一切（未知码、envelope 0 或 ≥2 行、task 标识查不到、输出取不回）→ 保守 exec-error，MUST NOT 读作 ok、MUST NOT 静默丢站点、MUST NOT 落零锚**。

参考实现跑通同口径判定（`/usr/bin/python3` 一次性脚本）：

```
A 正常/无尾换行     -> ok
B 正文伪造哨兵      -> exec-error (envelope 命中 2 行)
C 朴素echo粘行      -> exec-error (envelope 命中 0 行)
D 未知码 77         -> exec-error (未知码 77)
E exit2            -> exec-error
```

### 6. 后台能力自探 + 降级标注

② 自探：`host≠claude` 免探直走 sync；`host=claude` 用 run_in_background 派 trivial `printf PROBE_OK`，拿得到标识**且**取回哨兵才 `available`。`unavailable` ⇒ 降级 sync + 报告显著标注「⚠️ voice 同步降级（后台能力不可用，host=claude）」+ **MUST NOT 假装 async 成功 / MUST NOT 跳过 voice / MUST NOT 改锚行契约**。承 ADR-6：这是验证 A2 的实际防线。

### 7. 天花板 900/300 与「外层 ≥ 内层+30s」

③ 三行矩阵：async=900（可配）；codex sync=300 外层 ≥330000ms；claude 自探失败降级 sync=300 外层 ≥330000ms。async 行的「外层 ≥ 内层+30s」由 **backgrounding 本身**满足（有效外层无界），依据是 spike 实证（后台跑满 660s、跨过 600000ms 上限、exit 0、ppid 稳定）——**诚实写法，不假称给 dispatch 设了 930s 外层**（harness Bash 上界 600000ms 根本设不出）。sync 两行保留原「外层超时是指令层约束、helper 无法机械强制」的诚实边界句（tasks §4.3 G7 引用的那句）。

### 8. 可配 + 校验 + 非法值回落默认

① config.yaml 直读 `outside-voice.async-timeout-seconds`（沿 `metrics.enabled` 先例、**MUST NOT 走 resolver**，两 SKILL 同法否则等值门红）；校验正整数且 `1 ≤ v ≤ 3600`；缺键/读失败/非整/0/负/越界 → **回落 900**，MUST NOT fail-closed、MUST NOT 传 `--timeout 0`。校验规则参考实现实跑：

```
raw=None -> (900,'缺失→默认')   raw=0 -> (900,'越界')      raw=-5 -> (900,'越界')
raw='900'-> (900,'非整')        raw=1.5-> (900,'非整')     raw=3601-> (900,'越界')
raw=True -> (900,'非整')        raw=600-> (600,'采纳')
```

`3601` 上界的依据写进 ① 正文：helper 内层 `timeout -k 10` 自身无上限，误配 `86400` 会把一轮评审永久挂住；3600 远高于 900 默认、留足调宽空间。

## 门禁

```
$ /usr/bin/python3 -m pytest -q          → 1619 passed, 2 skipped
$ /usr/bin/python3 hack/sync_principles.py --check → ✅ 20 个投放面全部与真相源一致（exit 0）
```

## 遗留 concerns（交后续 ticket / 设计门）

1. **`3600` 上界是本票拍的理智值**，design 只写「harness 上界」而未给数——harness Bash 上界 600000ms 不适用于后台任务（async 默认 900 已越过它），故不能直接引用。若评审认为该常数应另定，改 ① 一处即可（marker 内 ⇒ Task 3 需同步）。
2. **config 键名 `outside-voice.async-timeout-seconds` 为本票新造**；`sdflow-init` 的 config 模版尚未列该键（本仓 config.yaml 已加注释形态说明）。是否回灌 bundle 模版超本票范围，未做。
3. **等值门脚本尚不存在**（Task 2.2/Task 3）——marker 文本已按「站点无关」写好并自查可整段搬运，但「两段字节相同」目前无机械验证；Task 3 首次跑 `check_async_branch_parity.py` 才是实证。
4. **`declared-sites` 机械核（tasks §3.5）不在本票验收项内**，未实现。
5. tasks §4.1/4.3/4.5 的真实评审 smoke（含「dispatch/终态通知/落锚三时刻单调」锚）需在 Claude 宿主真跑一轮，本票只落指令，未跑端到端 smoke。
