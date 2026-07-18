# Task 3 实施报告：code-review 层同款分支 + 机械等值门

**R-ID**: R1 · **Blocked-by**: 2（已完成）
**改动面**：`sdflow-code-review/SKILL.md`、`hack/check_async_branch_parity.py`（新增）、
`hack/tests/test_async_branch_parity.py`（新增）、`setup.sh`

---

## 做了什么

1. **搬运**：把 `sdflow-spec-review/SKILL.md` 的 `sdflow:async-branch` marker 段（含两条 marker 行本身，5528 字节）
   **原样字节复制**替换 `sdflow-code-review/SKILL.md` 原有的 5 行同步 exec 块
   （`exec：$HELPER exec --context-file <f>` + 外层超时条款 + exit 0/124/1/3 四行）。
   搬运用脚本做（读 → 写），不是手抄，∴ 不存在手抄漂移。
2. **圈外未动**：code-review 的站点枚举（`site=code-voice` / `site=hr-tg`）、context 构造、
   preflight、fallback、锚行段一律保持原样——两层这些部分本就应当不同。
3. **Step3 barrier**：code-review 第三步新增第 0 条（与 spec-review 第三步同款措辞，站点相关措辞按本层调整为「汇总去重」）：
   进汇总去重前 MUST 先完成 collect barrier，逐站点取，RUNNING 站点让出轮次等通知、MUST NOT 早退落 `timeout`。
4. **等值门**：新增 `hack/check_async_branch_parity.py`，比对两处 marker 段字节（含 marker 行），
   并机械守「圈内 MUST NOT 出现任一评审 SKILL 的文件名 / skill 名 / 报告名」（Task 2 约定）。
5. **挂门**：`setup.sh` 三条通则门之后追加一条（与 `sync_principles.py --check` / `gen_workflow_guide.py --check` 同 idiom）；
   `hack/tests/test_async_branch_parity.py` 16 个用例进仓内 pytest 套件。

### 隐含前提已显式落盘（ticket 第 3 条要求）

`check_async_branch_parity.py` 模块 docstring 记下两条：
- **(1)** 圈内站点无关约定（脚本机械守）。
- **(2)** 🔴 段内 `Step3` ×4 处在两侧都成立，**前提是两个评审 SKILL 的第三步恰好同为「合并 / 裁决 barrier」**；
  若将来任一侧重编步号即失效，必须同时重写两侧，**而不是只改一侧再来放宽本门**。

---

## 验收证据

### ① code-review 层分支与 spec-review 逐字对齐（站点无关部分）

```
$ /usr/bin/python3 hack/check_async_branch_parity.py
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致
rc=0
```

### ② 两层 async host 调度段被 marker 成对圈定，圈内仅站点无关逻辑

`sdflow-spec-review/SKILL.md:286,335` 与 `sdflow-code-review/SKILL.md:284,333` 各一对 marker。
圈内内容 = ①内层超时解析 ②后台能力自探 ③执行模式矩阵 ④命令形态 ⑤哨兵 envelope ⑥collect barrier
⑦退出码→reason_code 表 ⑧站点↔任务标识记账——全部站点无关。
`test_interior_names_no_review_skill` 机械守圈内不出现 `sdflow-spec-review` / `sdflow-code-review` /
`spec-review-report` / `code-review-report`。

### ③ 新增等值校验断言两段字节相同，不同则非零退出

真仓一字节漂移实验（把 async 行的 `默认 900` 改成 `默认 901`，跑完已还原）：

```
[async-branch-parity] FAIL: async host 调度段已漂移 —— …/sdflow-spec-review/SKILL.md 与 …/sdflow-code-review/SKILL.md 不逐字节相同
   首个不同在段内第 14 行：
     A:     | async | … | `<VOICE_TIMEOUT>`（默认 900） | …
     B:     | async | … | `<VOICE_TIMEOUT>`（默认 901） | …
   修：以一侧为准，把整段（含 marker 行）原样复制到另一侧
rc=1
（还原后）[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致 · restored rc=0
```

marker 形态错误各自明确报错（`MarkerError`，MUST NOT 静默放行），测试逐项覆盖：
缺 marker、有 start 无 end、有 end 无 start、两对 marker、end 在 start 之前、段为空、marker 行文字漂移。

### ④ 该校验挂进安装脚本与仓内测试套件

```
$ grep -n check_async_branch_parity setup.sh
  # 两个评审 SKILL 的 async host 调度段必须逐字节相同 —— 漂了 = 一个宿主路径静默行为分叉
  if ! python3 "$REPO_DIR/hack/check_async_branch_parity.py"; then
$ bash -n setup.sh && echo OK   → setup.sh syntax OK
```

`test_setup_sh_runs_the_gate` 机械守这条挂载存在（「存在但没人跑的门 = 不存在的门」）。

### ⑤ 首次跑确认绿

```
$ /usr/bin/python3 -m pytest hack/tests/test_async_branch_parity.py -q
16 passed in 0.05s

$ /usr/bin/python3 -m pytest -q
1635 passed, 2 skipped in 72.85s        （基线 1619 → +16）

$ /usr/bin/python3 hack/sync_principles.py --check
[sync_principles] ✅ 20 个投放面全部与真相源一致
```

**TDD 次序留痕**：先写 `hack/tests/test_async_branch_parity.py` → 跑得
`ModuleNotFoundError: No module named 'check_async_branch_parity'`（红）→ 再写脚本 → 绿。

---

## 遗留 concerns

1. **`--check` 无 `--apply`（ADR-5 已知次优，非本票遗漏）**：本脚本只报漂、不回填，
   修法是「以一侧为准整段原样复制」（错误输出已直接给出该指引）。`--apply` 式单一源运行时注入是 DRY todo，
   ADR-5 明确判为越 scope，本票不做。
2. **`setup.sh` 未在本机实跑**：本仓是开发 checkout，跑 `setup.sh` 会把 `~/.claude/skills` 指向开发版
   （CLAUDE.md 的 dev/runtime checkout 纪律）。∴ 只做了 `bash -n` 语法核 + 脚本单独实跑 + 测试守挂载存在，
   未做 setup.sh 端到端实跑。
3. **前提 (2) 是跨文件的语义前提，无机械守**：「两侧第三步同为合并 barrier」这件事没有确定性信号可捕获
   （机械/语义切分线判据：有无确定性信号），∴ 落成 docstring 里的显式注记 + 本报告，是合法的语义残余，不是漏做的机械门。
4. **等值门比对的是 marker 段，不覆盖圈外**：圈外的 preflight / fallback / 锚行段两层目前也高度相似，
   但按 ADR-5 刻意不圈（站点相关成分混杂），漂了不会红——这是设计选择，非缺陷。
