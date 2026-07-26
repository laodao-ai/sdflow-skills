# Task 1 双轴审存档 — 后台派发落地

**票**：Task 1（R-ID: OVBG-01, OVBG-02）
**轮次**：轮 1（`890c6e4`）双 FAIL → fix1（`e791679`）→ 轮 2 双 PASS

## 领域清单覆盖声明（Standards 轴，两轮均原样重述）

本 change 的 `proposal.md` 明确声明「不命中 backend、frontend、embedded 技术栈领域清单」，而
`code-checklists/domains/` 下只有 `backend*.md` / `embedded*.md` —— 故**领域清单未覆盖**，
Standards 轴以 `code-review-base.md` + 仓内 `CLAUDE.md` 基准 + Fowler code smell 为标准源。
**这是诚实降级，不是「全覆盖通过」。**

## 轮 1 发现（双 FAIL）

| 级别 | 轴 | 发现 |
|---|---|---|
| **Critical** | Spec | worker 构造的 `env` 从未传给 `subprocess.call` ⇒ 真 helper 必然 rc=1（`SDFLOW_VOICE_RUNNER 未设置`），后台通道对真实 voice **dead on arrival**。全部 worker 用例走 fake helper 且 `_env()` 主动 pop 掉这两个变量 ⇒ **41 条全绿也照不到** |
| Important | Standards | `effort` 被校验、被记进 `job.json`，却从未送达 runner ⇒ `"effort":"high"` 是未经核实即落盘的事实 |
| Important | 双轴 | nonce 核验窗口与 dispatch 共用同一个 5 秒预算（成功路径）+ kill 后零 grace（超时路径）⇒ 成功 dispatch 被误判 `unknown-cost`；或留下孤儿付费 job 同时再 fallback 重付 |
| Important | 双轴 | `dispatch_duration_seconds` 在 nonce 核验之前算完 ⇒ `assert duration < 5` **结构性恒真**，「5 秒级诚实降级」无有效机械锚 |
| Minor | Spec | `state=done` 的 agents 条目**无 `name` 字段**（真 CLI 实测）⇒ 极快失败的 worker 让轮询扑空、误落 `unknown-cost` |
| Minor | Standards | `run_preflight` 不在任何 deadline 内（两条探针各 `timeout=30`）；`_parse_job_id_hint` docstring 与用法自相矛盾；两处 `os.unlink` 无保护 |

## 轮 2 复审（双 PASS）——判据是**反向变异**，不是「有没有新增测试」

两轴各自在隔离副本上把实现改回错误形态，逐条确认锚会变红（仓内文件零改动，验完 `git checkout` 还原）：

| 发现 | 变异 | 结果 |
|---|---|---|
| C1 `env` 未传 | 删 `env=env` | **RED** — `test_worker_env_reaches_the_real_shell_helper` 报出真 helper 的 `SDFLOW_VOICE_RUNNER 未设置` |
| I 核验窗口/零 grace | 还原 `lookup_deadline` 旧式 | **RED** — `test_dispatch_grants_bounded_grace_when_job_registers_after_the_kill` |
| I duration 恒真 | duration 移回 `communicate()` 之后 | **RED** — `test_dispatch_duration_covers_nonce_verification_not_just_the_spawn` |
| M `state=done` 无 name | id 通道改 `return False` | **RED** — `test_dispatch_verifies_attempt_by_job_id_when_done_entry_has_no_name` |
| M hint 自相矛盾 | 恢复 `hint != job_id` 判死 | **RED** |
| M 探针无上界 | `CLI_PROBE_TIMEOUT_SECONDS` 回 30 | **RED** |
| M 裸 `os.unlink` | 换回裸 unlink | **RED** |

独立核实的两条承重前提（非自述）：① 真 `claude agents --all --json` 中 `state=done` 的 background
条目**确实无 `name`** ⇒ id 通道必需非冗余；② `outside-voice.sh` 的 `SDFLOW_VOICE_MODEL` 检查先于
context 存在性检查 ⇒ C1 新用例的探针是有效判别器、非空断言。

**7 条验收标准最终态全 ✅**（轮 1 判 ⚠️ 的第 4 条已升级，四条锚全部变异可判别）。
实跑 `pytest sdflow-init/tests/test_outside_voice_job.py -q` → **49 passed**；全量 **2199 passed / 8 skipped / 3 xfailed**。

## 编排层裁决

- **T10 ①（有客观判据 → 自动选）**：OVBG-01 字面「5 秒 deadline 内返回」vs 实现最坏 ~10 秒 ⇒
  **代码不动、spec 现在也不动**。客观判据 = `ship_gate` 的 design 域失鲜监视集含 `specs/`，实现期
  改它当场 `REFUSE_START`；且把 grace 收回 5 秒总预算等于把已消解的竞态请回来。措辞对齐记 **T214**，
  留到代码审 / done 阶段（失鲜窗口已关闭、流程明文允许修订四件套）执行。
- **Minor defer**（全部显式带 `change` 字段）：**T212**（id 通道补 `cwd == repo_root`）·
  **T213**（`CLI_PROBE_TIMEOUT_SECONDS` 改可调）· **T214**（OVBG-01 措辞对齐）·
  **T215**（删近似恒真旧断言）。
- **裁定不修**（非遗漏）：`cmd_dispatch` 长函数拆分（属重构非正确性）· `timeout="abc"` 走 argparse
  exit 2（现状 fail-closed 方向安全）· `_parse_job_id_hint` 交叉核验降级为并列通道（有 `..._not_blocked_by_a_drifted_backgrounded_stdout_format` 锚兜底）。

## 跨票交接（下游票 MUST 消费）

- **Task 4**：`SDFLOW_VOICE_EFFORT` 已由 worker 下发但**全仓零消费者**，`outside-voice.sh` 头部
  env 契约块亦未登记该名 ⇒ Task 4 落 `--effort high` argv 时须一并登记契约块。
- **Task 4**：`claude agents --all --json` 的 `name` 字段承载**完整 worker 命令串**（含 run-dir /
  context 文件的绝对**路径**，不含正文）⇒ `claude logs` canary 回归须把这条纳入口径，
  **不该被意外判红**（路径不是 payload，但它是一条已存在的结构化外泄面）。
- **Task 5**：`setup.sh` 仍未写 `capability-manifest.json` ⇒ **真实安装态 preflight 必红**。
  `write_manifest()` 已作为单一计算源就位，安装步直接调它。
