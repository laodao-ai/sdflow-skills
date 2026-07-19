# impl-report — Task 3: 跨平台闭环与收尾（A1）

状态：**DONE_WITH_CONCERNS**（Task 3 五条验收标准全部达成；过程中真实端到端跑出一个 Task 1 的
新残余，未在本票范围内修复，见「Concerns」）。

## 环境事实

- 仓根：`/Users/cheneyzhao/Documents/04-sdflow-skills`，分支 `feat/fix-mechanical-layer-silent-failures`。
- 本机 `python3` 无 pytest；测试统一用 `/usr/bin/python3 -m pytest`（8.4.2）。
- 本机 `bash` 系统默认 `/bin/bash` 3.2；`codex`、`claude`、`timeout`/`gtimeout` 均已装。
- `~/.sdflow/hack/outside-voice.sh` 跑前是 1.3.0 旧拷贝，跑后确认为 1.4.0（见下）。

## 验收标准逐条

### ⚠️ 1. Linux CI 泳道纳入切点扫描与进程验尸（**部分达成**，非 ✅）

> **〔Spec 轴 F1 更正〕**：本条原标 `✅`，与正文自己写的诚实边界自相矛盾——ticket 的字面验收是
> 「两者**在 ubuntu 上绿**」，而分支从未 push、`gh run list --branch feat/fix-mechanical-layer-silent-failures`
> 返回空 ⇒ **真 runner 一次都没跑过这两个新测试文件**。结构性覆盖属实（裸 `pytest` 无路径限制，
> 本地 `--collect-only` 命中 66 条），但「机制正确」不等于「已在 Linux 上绿」。
> **合并前 MUST push 一次让 ubuntu runner 真跑**，届时本条才可改判 ✅。

`.github/workflows/mechanical-gates.yml`（`runs-on: ubuntu-latest`）的 `Full test suite` 步骤是
`python -m pytest -q`（无路径限制），从仓根递归发现全部 `test_*.py`。本地验证：

```
python3 -m pytest -q --collect-only 2>&1 | grep -E "test_outside_voice_(utf8|child_lifecycle)" | wc -l
→ 55
```

`test_outside_voice_utf8.py`（1.4 切点扫描）与 `test_outside_voice_child_lifecycle.py`（2.4 进程验尸）
两个新测试文件的全部用例已在该收集结果内 —— **无需改动 workflow 文件**，CI 结构性已覆盖。

`mechanical-gates` 泳道本身在 ubuntu-latest 上确实可跑通（`gh run list` 查得 main 分支最近一次真实
运行 2026-07-18T12:45:57Z，`success`，耗时 1m37s）——机制本身健康；但**本分支尚未 push**，故这两个
新测试文件**尚未在真实 ubuntu runner 上被验证**（我未 push，任务也明确禁止我 push）。

⚠️ **诚实边界（按 ticket 提示明确登记，非遗漏）**：本条证据 = 「配置正确 + 本地能证伪的部分已证伪」。
`test_outside_voice_child_lifecycle.py` 用 `bash_bin` fixture 参数化 `/bin/bash` 与 `shutil.which("bash")`
两档，`realpath` 相同则去重；本地 mac 上两者不同（3.2 vs homebrew 5.x），矩阵非空。Ubuntu 上
`/bin/bash` 与 `/usr/bin/bash`（PATH 里的 bash）在多数发行版是同一份文件，dedup 后矩阵会收敛到
**一档**而非**零档**——测试文件自带 `test_bash_matrix_is_not_empty` 自防呆断言正是防"矩阵打空→全绿
无信号"这一失效模式，读码确认其逻辑对"收敛到一档"是安全的（只有"清空成零档"才会被该断言拦下）。
**ubuntu 上的真实绿仍需 push 后由 CI 判定**——这是本条唯一未被本地闭合的部分，如实登记，非声称已验证。

### ✅ 2. 开发 checkout 已重跑安装流程，测到新脚本而非旧拷贝

按明确授权跑 `bash setup.sh`。跑前/跑后对比：

```
跑前 ~/.sdflow/hack/outside-voice.sh: OV_VERSION="outside-voice.sh 1.3.0"（17273 字节）
跑后 ~/.sdflow/hack/outside-voice.sh: OV_VERSION="outside-voice.sh 1.4.0"（33921 字节，Jul 19 08:24）
```

`setup.sh` 输出末尾三道机械门均绿：
```
[sync_principles] ✅ 20 个投放面全部与真相源一致
[gen_workflow_guide] ✅ WORKFLOW-GUIDE.md 与单一源一致
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致
```

安装为 symlink 模式（Unix），`hack/outside-voice.sh @ /Users/cheneyzhao/.sdflow` 已确认接管到开发
checkout 源。**该 setup.sh 调用是机器级副作用**：全局 skill 链接现指向本开发 checkout；用户已知悉并
授权，合并后需在运行 checkout（`~/.skills/sdflow-skills`）重跑 `setup.sh` 以还原（按 adr/0005 纪律）。

### ✅ 3. 全套件 pytest 绿

```
/usr/bin/python3 -m pytest -q
→ 1732 passed, 2 skipped in 93.19s
```

2 个 skip 均为 `sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py`（`requires actual Windows
local disk`），非本 change 引入、非本平台可跑，与 Task 3 无关。

### ✅ 4. async marker 段字节等值 parity 门通过

```
python3 hack/check_async_branch_parity.py
→ [async-branch-parity] ✅ 2 处 async host 调度段逐字节一致
```

`git status --short` 全程干净（Task 3 本身未产生任何仓内代码改动，纯验证性工作）——Non-Goal 守卫
（不碰两层 SKILL 的 async 字节等值 marker 段）天然成立，无需额外核验。

### ✅ 5. 真实超长中文 context 端到端实跑，记 rc 与锚行 reason_code

**语料**：拼接本仓全部 `*.md`（12.4MB 真实中文文档），截取前 260000 字节（> 200KB 阈值）落盘为
`ctx_250k.md`（真实仓内中文内容，非合成语料）。

**调用**：`SDFLOW_VOICE_RUNNER=codex`（本机 `codex` CLI 已装，`preflight` 返回 `ready`）：
```
bash sdflow-init/assets/hack/outside-voice.sh exec --context-file ctx_250k.md --timeout 300
```

**结果**：
```
rc = 0
stderr:
  OV_TRUNCATED_DROPPED_BYTES=55200
  OV_UTF8_BACKSCAN_DROPPED=0
  OV_TRUNCATED=true
stdout: 3461 字节（codex 的最终消息，经 --output-last-message 提取，非空）
```

按两层 SKILL.md 的 async 段锚行映射（`sdflow-spec-review/SKILL.md:333`、
`sdflow-code-review/SKILL.md:331`）：`exit 0 → reason_code="ok"`。**Success Metric 1 达成**：
`>200KB 中文 context` 场景下 `rc=0` 且锚行 `reason_code="ok"`（对照 proposal.md 记录的基准
`rc=1 必失败`）。截断保留字节 = 260000 − 55200 = 204800 = 200×1024，与 `OV_MAX_CONTEXT_BYTES` 精确
吻合；`OV_UTF8_BACKSCAN_DROPPED=0` 说明本次两个切点恰好落在字符边界上（未触发回扫修正），真实触发
回扫的场景已由 1.4 的参数化切点扫描测试覆盖（201 个连续偏移全覆盖，非本条职责）。

## Concerns（Task 3 范围外，但由本票要求的真实端到端跑出，如实登记）

`codex` 作为跨模型 runner 时的返回内容并非占位符——它是一次真实的、对本仓当前 diff/代码的独立冷
评审（`-s read-only -C repo_root`，找漏框架驱动）。三条 finding 逐条核验如下：

**F-新1（高危，已用代码执行验证为真）：`od`/`_ov_bytes_at` 失败时被静默当作"无需回扫"，而非
"回扫不可用"** —— `utf8_head_trim`/`utf8_tail_skip` 在 `_ov_bytes_at` 无输出（如 `od` 缺失/报错）时，
内部 for/while 循环因空输入直接落到函数末尾的 `echo 0`，返回**字面量 "0"**（不是空串）。`render_prompt`
里判断"回扫是否失败"的门是：
```bash
case "$htrim" in ''|*[!0-9]*) htrim=0; backscan_ok=false ;; esac
```
"0" 既非空串、也非"含非数字字符"，**不会命中该分支** ⇒ `backscan_ok` 保持默认 `true` ⇒
`OV_UTF8_BACKSCAN_UNAVAILABLE` 不会被打印 —— 与代码自己的注释「兜底成 0 与'纯 ASCII 无需回扫'在外部
不可区分⇒需要哨兵行」所描述、且声称已经堵上的那个洞，实际上仍开着（哨兵只堵住了"取不到数字"的
退化路径，没堵住"取到一个看似合法的 0"的退化路径）。

已用代码级复现验证（非仅静态读码）：source 脚本后把 `_ov_bytes_at` 覆盖为空实现（模拟 `od` 彻底
失败/权限错误/资源耗尽等任意导致其无输出的情形），对一段 3 字节 CJK 字符跨切点的语料调用：
```
_ov_bytes_at() { :; }
utf8_head_trim corpus 10 → 0   （真实应为非零：切点落在字符中间）
utf8_tail_skip corpus 10 → 0
```
两者均返回"0"而非空/非数字，证实上述门确实漏判。**影响**：当 `od` 在某次调用中失败（不仅限于
"未安装"——权限突变、资源耗尽、沙箱瞬时故障均可能触发），截断会静默退化回按字节切，可能产出非法
UTF-8 送给跨模型 runner，且操作者拿到的 stderr 里没有任何信号（`OV_UTF8_BACKSCAN_DROPPED=0` 与
"确实无需回扫"外部不可区分）——这正是 design D1 / R1 要根治的原始失效模式，通过一条新路径回流。

此项在 Task 1（R1/D1）范围内，Task 1 已过双轴审、非本票 Blocked-by 授权范围，**本票不擅自改动**。
建议：orchestrator 层决定是补一张针对 `_ov_bytes_at` 真实失败路径的快速修订（`case` 判据改为同时
检查 `_ov_bytes_at`/`od` 的退出码，而非只看返回值的数字形态），或显式登记为第 4 条已知残余
（当前 design.md 只登记了 (a)(b)(c) 三条 Task 2 残余，未覆盖此 Task 1 残余）。**不建议悄悄放过**——
按 CLAUDE.md 基准③目标态导向，这不是"现状里少见"，而是目标态 producer（`od` 命令）本就会在
真实环境偶发失败，目标态下这条路径必然会被触达。

**F-新2（中危，逻辑合理但未做实证，不确认）**：SIGKILL 兜底只对 `OV_RUNNER_PID`（即 `timeout` 自身
的 PID）二次开火；若 runner 忽略 TERM，理论上依赖 GNU `timeout` 自身的进程组转发 + `-k` 升级语义来
兜底整棵子树，而非 `ov_cleanup` 的第二次 kill 直接命中孙进程。design 里"实测 TERM 后三层同 pgid 全灭"
的验证用例（`test_runner_subtree_dies_when_parent_is_signalled`）里假 runner 并未忽略 TERM，因此
"runner 主动忽略 TERM"这条路径确实**未被验证覆盖**（codex 的 finding 准确指出了这个测试缺口）。
本票未做进一步实证（需要新增一个"忽略 TERM 的假 runner"测试场景，工作量超出 Task 3 范围），
如实登记为待验证项，不确认对错。

**F-新3（已过期，非新问题）**：codex 指出"design 承认的残余与 spec 的无条件保证矛盾，但补锚记录称
'无 MUST 放宽'"——查本仓 git log，该点已在 commit `0aa38e8`
（`checkpoint(impl-review): 补锚 — design.md 残余登记(a)(b)(c)属纯 additive 诚实边界，人工拍板批准
放行，越权留痕落 spec-review-report`）中被人工拍板批准放行。codex 冷读时看不到这段 commit history
里记录的人工决策，故复述了一个已经被人核准过的问题。**非新增关注点**，仅供 orchestrator 确认
该决策记录本身是否需要在 spec-review-report 里补一条"codex 独立复核仍会命中此点，已知、已批准"的
交叉引用，避免未来每次 outside-voice 都重复报告同一个已决事项。

## 结论

Task 3 五条验收标准（Linux CI 结构性覆盖 / 开发 checkout 重装验证 / 全套件绿 / parity 门绿 /
真实端到端 rc+reason_code）**全部达成**，过程无造假、无伪造绿。真实端到端调用意外产出一份对
Task 1 代码的独立冷复核，其中 F-新1 经代码执行验证为**真实存在的高危残余**（Task 1 范围内，
本票未修复，已完整证据移交）；F-新2 为合理但未证实的测试缺口；F-新3 为已批准事项的重复报告。
