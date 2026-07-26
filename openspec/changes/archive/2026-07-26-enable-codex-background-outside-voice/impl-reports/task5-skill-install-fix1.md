# Task 5 fix1 —— 双轴审双 FAIL 的修复报告

**上轮报告**：`task5-skill-install.md`（未覆盖，本文件是增量）
**起手 HEAD**：`6084403`
**主线问题**：**宣称有锚、实则假绿** —— 上轮 impl-report 列为「机械锚」的多条断言，
经反向变异实测对其声称守护的不变量**完全不敏感**。∴ 本轮重点不是补功能，是**让锚真的会红**。

---

## 〇、方法：每条 fix 都有反向变异自证

- 变异**只在 scratchpad 唯一命名副本**跑：`…/scratchpad/mutant-65e03876-task5-fix1/`（全仓 rsync 副本），
  驱动脚本 `…/scratchpad/mutate_task5_fix1.py`。**仓内零变异残留**（末尾 `git status` 亲验）。
- SKILL 的变异一律**同时打到两侧**——只改一侧的话红的是 parity 等值门、而非内容 golden，归因会被混淆。
- ⚠️ **harness 自身踩过一次假逃逸**：`MIN_CLAUDE_VERSION = (2, 1, 169)` → `(2, 1, 170)` 是**等长**改写，
  与上一次编译**同秒**落盘 ⇒ mtime(秒粒度)+size 双双未变 ⇒ `importlib` 复用了旧 `.pyc`，M7 报绿。
  隔离单跑立即红。修法：跑 pytest 前清 `__pycache__` **且**加 `-B` / `PYTHONDONTWRITEBYTECODE=1`。
  （**这是 harness 的坑，不是 golden 的坑**——同一条 golden 在隔离运行与关字节码缓存后均稳定红。）

### 变异矩阵（15 条，**全红，零逃逸**）

| # | 变异 | 结果 | 捕获者 |
|---|---|---|---|
| M1 | 删掉整条 `unknown_cost=true` MUST 行 | **RED** `1 failed, 40 passed` | `test_codex_branch_gates_auto_fallback_on_unknown_cost` |
| M2 | dispatch 子命令 `dispatch`→`submit` | **RED** `2 failed, 39 passed` | `…goes_through_the_background_job_helper` + `…dispatch_command_line_is_byte_exact` |
| M3 | dispatch 命令丢掉 `--repo-root <repo-root>` | **RED** `1 failed, 40 passed` | `test_codex_dispatch_command_line_is_byte_exact` |
| M4 | `--effort high` → `--effort medium` | **RED** `1 failed, 40 passed` | `test_codex_dispatch_command_line_is_byte_exact` |
| M5 | 删掉「**MUST NOT 重新 dispatch**（重派 = 第二次计费）」 | **RED** `1 failed, 40 passed` | `test_barrier_invariants_survive` |
| M6 | printf 格式串退回 3 个 `%s`（实参仍 4 个） | **RED** `1 failed, 40 passed` | `test_dispatch_manifest_records_job_id_and_attempt_nonce` |
| M7 | helper 提版到 `2.1.170`（SKILL 未同步） | **RED** `1 failed, 40 passed` | `test_usage_notes_cover_version_policy_preview_and_platform_boundary` |
| M8 | 删掉「MUST NOT 回落任何「同步等 Claude」的长路径」整句 | **RED** `1 failed, 40 passed` | `test_sync_wait_for_claude_compat_path_is_deleted_in_prose_too` |
| M9a | 续等条件退回「`terminal=false` ⇒ 再调一次 await」 | **RED** `1 failed, 40 passed` | `test_reserved_await_does_not_loop_forever` |
| M9b | 删掉 RESERVED 止损行 | **RED** `1 failed, 40 passed` | `test_reserved_await_does_not_loop_forever` |
| M10a | 退回「标注 payload 的 `detail` 与 orphan warning」 | **RED** `1 failed, 40 passed` | `test_dispatch_hard_failure_lands_a_legal_no_exec_anchor` |
| M10b | 删掉 dispatch 硬失败的锚形行 | **RED** `1 failed, 40 passed` | `test_dispatch_hard_failure_lands_a_legal_no_exec_anchor` |
| M11 | ⑦ 例外行退回「判 `exec-error`」 | **RED** `1 failed, 40 passed` | `test_exit_code_table_exception_row_pins_the_same_anchor_shape` |
| M12 | `_reject` 默认翻回 `fallback_allowed=True` | **RED** `1 failed` | `test_reject_defaults_to_fail_closed_fallback` |
| M13 | `setup.sh` 版本闸门退回 `(3, 6)` | **RED** `1 failed` | `test_setup_sh_has_version_check` |

> 变异前基线：`hack/tests/test_async_branch_parity.py` **41 passed**（fix 前 35）。

---

## 一、Critical F1 —— `unknown_cost` 分支的锚形不合法

**发现**：`:437` 要求「不 fallback、落 `reason_code="exec-error"`」，但全段只在 exit 0 / exit 3
指定过 `runner=`。而 `declared-sites` 强制该站点必须有锚 ⇒ 报告自检**必红，或者必须撒谎**。

**先读实际合法矩阵**（`openspec/workflow/tools/anchor_lint.py:429 classify_combo`），**实跑自证**：

```
('codex', 'none',   'fallback-unavailable', 0) -> no-exec       ← 新钉死的形态，合法
('claude','none',   'fallback-unavailable', 0) -> no-exec
('codex', 'none',   'exec-error',           0) -> illegal       ← 原措辞照字面落出来的锚
('codex', 'codex',  'exec-error',           0) -> same-family   ← runner==host = 谎称同族 fallback 跑过
```

**修法（选「不改既有矩阵」的那条，验收标准第 3 条）**：钉死
`host="$SDFLOW_HOST" runner="none" findings="0" reason_code="fallback-unavailable"`，
并**显式禁止**落 `exec-error`（它属同族降级码集，与 `runner="none"` 组合判 illegal；
与 `runner=host` 组合则蕴含「fallback 真跑过」）。语义读法写进正文：
成本闸门**禁止**同族 fallback ⇒ 与 F8「同族 fallback 起不来」同属矩阵的**无执行行**。

`_NOEXEC_KNOWN_CODES` / `classify_combo` / `anchor_lint.py` **零改动**（`git status` 无这些文件）。

**面治**：同一病灶还有两处，一并订正（否则只补被点穿的一处）——
- ④ 的 `fallback_allowed=false` 分支（原文根本没写落什么锚，见 F5）；
- ⑦ 的「唯一例外」行（原写「判 `exec-error`」，与 ⑥ 同源，MUST NOT 留第二份说法）。

**锚**：`test_codex_branch_gates_auto_fallback_on_unknown_cost`（M1）、
`test_dispatch_hard_failure_lands_a_legal_no_exec_anchor`（M10a/M10b）、
`test_exit_code_table_exception_row_pins_the_same_anchor_shape`（M11）。

---

## 二、Important（假绿锚 → 真锚）

### F2 · `:437` 整条删掉仍全绿

**根因**：四个断言子串（`unknown_cost` / `cleanup --run-dir` / `--cancel` / `fallback_allowed`）
在段内**别的行**也有 ⇒ 「出现在段内任意处」这个判据本身是空的。

**修法**：新增 `_the_line_with(rel, seg, key)` —— 取段内**唯一**含 key 的那一行（0 行或 ≥2 行即红），
把同一条指令的全部要件断言在**同一行**上。这是本轮最通用的一处结构性修正，下面多条复用它。

**变异**：M1 删整行 → `1 failed`（fix 前：35 passed）。

### F3 · `:435` 对 RESERVED 会无限 re-await

**接地核实**（读码，非推断）：`outside-voice-job.py`
`PENDING_STATES = {RESERVED, STARTING, RUNNING}`、`derive_status` 的
`"terminal": state not in PENDING_STATES` ⇒ RESERVED 恒 `terminal=false`；
`:1274` 该形态带 `unknown_cost=True`；`cmd_await` 的 `:2141` 注释自写
「RESERVED（unknown-cost，**永远不会自行到达终态**，交 reconcile）」。
∴ 原文「`terminal=false` ⇒ MUST 再调一次 await」照字面执行 = 无限循环，
而 SKILL 从未提 `state` 字段，模型无判别手段。

**修法**：续等条件加 `∧ unknown_cost=false`；另起一条 RESERVED 止损行（`MUST NOT 再调 await`，
直接走 unknown-cost 处置）。

**锚**：`test_reserved_await_does_not_loop_forever`——除了两行文本判据，还**机械绑住前提**
`assert JOB.STATE_RESERVED in JOB.PENDING_STATES`（helper 哪天把 RESERVED 移出 PENDING，
这条断言当场红、提示回来复核 SKILL）。变异 M9a / M9b 各 `1 failed`。

### F4 · `:416` dispatch 命令形态零 golden

**修法**：
1. **整行字面 golden** `_DISPATCH_COMMAND_LINE`（`test_codex_dispatch_command_line_is_byte_exact`）；
2. **子命令交叉断言**（不手抄第二份名单）：`JOB.build_parser()` 取 `_SubParsersAction.choices`，
   段内所有 `outside-voice-job.py <sub>` 出现过的名字 MUST ⊆ 真实子命令集，且四个生命周期子命令一个不缺；
3. **flag 双向交叉断言**（`test_dispatch_command_flags_agree_with_the_helper_parser`）：
   命令行用的 `--flag` MUST ⊆ dispatch 子解析器接受集，且 helper 的**必填**参数
   （`--run-dir` / `--site` / `--context-file` / `--repo-root`）MUST ⊆ 命令行 —— 丢 `--repo-root` 当场红，
   且这份必填清单是从 parser 里读出来的，helper 改必填项时测试自动跟着变。

**变异**：M2（`dispatch`→`submit`）`2 failed`、M3（丢 `--repo-root`）`1 failed`、
M4（`high`→`medium`）`1 failed`。

### I1 · `:298` 3 字前缀空断言

`assert "MUST NOT 重" in seg` —— 该串段内另有出处（④ 的「MUST NOT 重派」）。
**修法**：`assert "MUST NOT 重新 dispatch" in seg`。**变异** M5 → `1 failed`。

### I2 · dispatch-manifest golden 不验列数

POSIX `printf` 在实参多于转换符时**复用格式串** ⇒ 3 个 `%s` + 4 个实参落盘的不是「少一列」，
而是**每次多一行 `<nonce>\t\t`**，而 run-dir + site + `attempt_nonce` 是 unknown-cost 后**唯一**可核身份。
**修法**：`re.search(r"printf '([^']*)'")` 取格式串，断言 `%s` 计数 == 4；并断言重定向 `>>` 之前的
双引号实参恰好 4 个（两侧对齐，不是只查其一）。**变异** M6 → `1 failed`。

### I3 · 版本下限手抄第二份

`MIN_CLAUDE_VERSION` 是 helper 里的机械常量（有确定性信号 ⇒ 基准 1 要求机械化）。
**修法**：测试按 `test_setup_sdflow.py:208-213` 的 importlib 模式在模块顶层导入 `JOB`，
`min_version = ".".join(map(str, JOB.MIN_CLAUDE_VERSION))` 再断言它在段内。
两份 SKILL 各断言一次（`_segments()` 逐侧遍历）。**变异** M7 → `1 failed`。

---

## 三、编排层裁定的 Concern 2（散文形态照不到）—— 已补

采纳裁定：`MUST NOT 回落任何「同步等 Claude」的长路径` 是**段内唯一字面串**，一条 assert 即可守，
与既有正向 golden 同级成本 ⇒ 不属基准 1 的「机械够不着的残余」。
新增 `test_sync_wait_for_claude_compat_path_is_deleted_in_prose_too`（字面串 + `efficacy=0`）。
**变异** M8（删掉整句）→ `1 failed`。

> 上轮把它记为「合法语义残余」的理由（「散文不构成可执行指令」）被 SKILL 自身结构证伪：
> ②④⑤⑥⑦⑨ 全是散文 MUST，矩阵只是其中一处。此说撤回。

---

## 四、Minor（一并 fold）

| 项 | 修法 | 锚 |
|---|---|---|
| **F5** `:421` 措辞与实际 payload 不符 | 读码核实：dispatch 的失败 payload 全经 `_reject()`，**只有 `detail`，无 `orphan_warning`**（`orphan_warning` 只出现在 `collect`/`cleanup`/`reconcile` 的 payload 里）。措辞订正 + 补上该分支缺失的锚形（见 F1 面治） | `test_dispatch_hard_failure_lands_a_legal_no_exec_anchor`（M10a/M10b） |
| **`outside-voice-job.py:497`** `_reject` fail-open 默认 | 默认翻 `fallback_allowed=False`。**先 grep 全部 29 个调用点、逐个确认已显式传值** ⇒ 翻默认不改任何现行行为，只改「下一个分支忘了传」时的落点 | `test_reject_defaults_to_fail_closed_fallback`（M12）+ 面治的 `test_every_reject_call_site_states_its_fallback_stance`（要求每个调用点仍显式表态，默认只当兜底） |
| **`setup.sh:191`** 归因错误 | `if [-z $_py] / elif [! -f helper] / elif 写 manifest / else 写失败` 四路分开归因 | 无独立机械锚（**如实降级**，见第七节） |
| **`setup.sh:200`** 闸门 3.6 vs helper 需 3.7 | `sys.version_info >= (3, 7)`（`subprocess.run(capture_output=…)` 是 3.7 起）；`_py` 是 manifest 与 retire-hooks 共用的解释器 ⇒ 闸门取两个消费者的**上确界**。同步刷新两条 ⚠ 文案与注释；`test_init_hardening.py` 的三处 `(3, 6)` 字面、`NOPY36` 标记与用例名一并对齐 | `TestT48SetupVersionCheck::test_setup_sh_has_version_check` + `test_setup_sh_retire_block_binds_to_real_construct`（M13 两测同时红） |

> ⚠️ **这条踩到了 memory「重命名共享字符串消费者跨文件」**：首轮只 grep 了 `setup.sh` 与
> `test_init_hardening.py`，**漏了第二个 bind 测** `test_setup_failsafe.py:50`（也硬编码
> `version_info >= (3, 6)`）⇒ 全量套件 1 red。**只有全仓 grep + 全量 pytest 照得到**。
> 补修：`test_setup_failsafe.py:48-52` 与 `sdflow-init/scripts/init.py:29`（注释里「setup.sh 探测 3.6+ 才喂」已陈旧）。
> 归档目录下的历史记录（`openspec/changes/archive/2026-07-06-sdflow-init-hardening/*`）**MUST NOT 改** —— 那是当时的事实。
| **`test_async_branch_parity.py:308`** docstring 写「四项」 | 按本仓惯例**删掉数字**（「使用说明各项 + 两条不可互相替代的分发链」），让断言自己说话 | —（文档串） |

---

## 五、两份 SKILL 的一致性纪律

marker 段的四处改动由**单一脚本** `…/scratchpad/splice_segment.py` 对两个文件跑**同一组 (old,new) 常量**
（`assert count == 1` 逐条 fail-closed），**MUST NOT 手抄两侧**。

```
$ python3 hack/check_async_branch_parity.py
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致

$ python3 hack/sync_principles.py --check
[sync_principles] ✅ 18 个投放面全部与真相源一致
（rc=0）

$ bash -n setup.sh
setup.sh syntax OK

$ git diff --check
（无输出）
```

---

## 六、全量测试

```
$ /usr/bin/python3 -m pytest -q
2496 passed, 11 skipped, 3 xfailed in 258.92s (0:04:18)
```

> **中途红过一次并如实记录**：首次全量跑 `1 failed, 2495 passed` ——
> `test_setup_failsafe.py::test_setup_sh_retire_block_binds_to_real_construct`
> （第二个硬编码 `version_info >= (3, 6)` 的 bind 测，见下节 ⚠️）。修完复跑即全绿。

上轮基线 `2488 passed, 11 skipped, 3 xfailed`。差额 = 本轮新增 **8** 条用例：
parity 6 条（`…dispatch_command_line_is_byte_exact` / `…flags_agree_with_the_helper_parser` /
`…reserved_await_does_not_loop_forever` / `…dispatch_hard_failure_lands_a_legal_no_exec_anchor` /
`…exit_code_table_exception_row_pins_the_same_anchor_shape` /
`…sync_wait_for_claude_compat_path_is_deleted_in_prose_too`）
+ helper 2 条（`test_reject_defaults_to_fail_closed_fallback` /
`test_every_reject_call_site_states_its_fallback_stance`）。
另有 5 条既有用例**被加强**（判据从「段内任意处」收紧到「共处一行」/「与 helper 交叉」），不计数。

---

## 七、未做 / 降级项（如实报告）

1. **`setup.sh` 的归因分叉没有机械锚**。它是 4 路 `echo` 分支，触发「helper 未装但 `_py` 合格」
   需要构造一个「装了 `*.py` 循环却没落文件」的安装态 —— 现行 `install_sdflow` 里两者同源，
   造这个态要改 `setup.sh` 本身。按 ④ 五问：概率低（只在 `cp` 部分失败时出现，而那已被
   `set -e` 挡在前面）、影响止于**一句错误的诊断文案**、完美成本明显过高 ⇒ 简化，接受无锚。
   语法与四路结构由 `bash -n` + 人读 diff 兜。
2. **`bash setup.sh` 仍未在本机真实 HOME 上跑过**（编排层已裁定本轮 MUST NOT 跑，破坏性动作）。
   `test_setup_sdflow.py` 的安装用例走 `HOME`/`SDFLOW_HOME` 重定向到 tmp 的真实 `setup.sh` 执行，
   已覆盖新的 4 路分支中的正常路径（`_py` 合格 + helper 已装 + manifest 写成）。
3. **`fallback-unavailable` 的语义是被复用的**：spec 的 Scenario 描述的是「同族 fallback 也**起不来**」，
   而本轮新增的两处是「同族 fallback 被成本闸门**禁止**」。两者共享矩阵里同一条**无执行行**
   （`runner="none" ∧ findings=0`），锚形合法性无疑义；差别只在人读语义。
   之所以复用而不新增枚举值：验收标准第 3 条要求「anchor 合法组合矩阵保持不变」。
   **若评审认为该语义需要独立枚举值，那是一次跨 `openspec/specs/` + `anchor_lint` + 全笛卡尔 golden 的
   矩阵变更，超出本票范围，MUST 上抛编排层裁决**——本轮按「矩阵不变」执行。
4. **知情不改**（沿用上轮裁定）：T220 的两处 docstring（已 defer 冷层）、`openspec/specs/` 主 spec（归 archive）、
   降级项 ③（manifest 写失败只告警不中止安装，已判自洽）、`$_py` 可能是 `python`、非 darwin 的 `cp` 行为。
5. **未动**：`proposal.md` / `design.md` / `specs/` / `tasks.md` / `openspec/specs/`；
   未勾任何复选框、未打 `task5-` 完成标签；`anchor_lint.py`（两份）零改动。
