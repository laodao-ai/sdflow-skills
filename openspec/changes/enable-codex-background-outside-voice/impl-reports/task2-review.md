# Task 2 双轴审存档 — 终态派生的 status/await/collect

**票**：Task 2（R-ID: OVBG-02, OVBG-03, HAE-09）
**轮次**：轮 1（`6b0313e`）Spec PASS / Standards FAIL → fix1（`f558722`）→ 轮 2 双 PASS

## 领域清单覆盖声明（Standards 轴，两轮均原样重述）

本 change 的 `proposal.md` 明确声明「不命中 backend、frontend、embedded 技术栈领域清单」，而
`code-checklists/domains/` 下只有 `backend*.md` / `embedded*.md` —— 故**领域清单未覆盖**，
Standards 轴以 `code-review-base.md` + 仓内 `CLAUDE.md` 基准 + Fowler code smell 为标准源。
**这是诚实降级，不是「全覆盖通过」。**

## 轮 1 发现

| 级别 | 轴 | 发现 |
|---|---|---|
| **Important** | Standards | `collect` 把「rc 尚未发布」的 LOST 判定**永久冻结**。实测：collect#1 出 LOST 并落 witness；worker 随后真跑完发布 `rc=0` + 真实 findings，collect#2 仍原样回放 `LOST/exec-error`、`stdout_path=None` ⇒ **一次已计费的 voice 被静默丢弃**。`design.md:214` 的幂等只要求「**terminal rc 后**」，实现把它扩到了 rc 之前 = 自行加宽 |
| **Important** | Standards | `await` 每个 poll 都 spawn 一次 `claude agents --all --json`：默认 0.5s 间隔 × 上界 930s ⇒ 单站点单次 await 最多 ~1860 次 Node CLI 冷启动，两站点翻倍 |
| Minor | Standards | 三处 `open(...).read()` 未关闭句柄（违 CR-04）· `LIVENESS_ALIVE` dead constant · `derive_status` 自递归无深度保护 · 模块 docstring 的 exit 契约与实现不符 |
| Minor | Spec | LOST 路径未带 `unknown_cost`/orphan-warning ⇒ **Task 3 MUST 在此路径上翻该字段**，否则 Task 5 无可 gate 的字段 |
| Minor | Spec | helper 对越界 `--timeout` 是 fail-closed 拒绝，而既有 SKILL 对越界 config 是「回落 900」⇒ **Task 5 MUST 保留 SKILL 侧 clamp**，否则 config 打错字会变成 `usage-error` |

**Spec 轴轮 1 即 PASS**（7 条验收标准全 ✅）。其最有价值的动作是**排除参数化自证嫌疑**：
`_expected_classification` 经核验是测试内独立手写的 if-链、不 import 任何实现分类逻辑；变异实测
（把 `rc124→SUCCEEDED/ok`、`bytes > 0` 改 `>= 0`）→ **15 failed**，含笛卡尔 2 例、零-ok 遍历断言、
collect 表。「126 格笛卡尔」因此不是自证。

## Spec 轴对两条「是否越界」Concerns 的独立裁断

- **`<site>.collected.json` 新 sidecar = 必要落地，非加宽**：OVBG-02 明写「collect SHALL 幂等返回
  **首次** `collected_at`」，跨进程唯一实现路径即落盘；`os.link` 首写者胜不可变，未引入第二份可变
  status，不违 ADR-2。
- **`rc=3 → secret-hit` = 必要落地，非加宽**：HAE-09「`reason_code` 枚举语义 MUST 保持不变」；
  两份 SKILL 与 `outside-voice.sh` 三处既有 exit 3 = secret-hit 且**不 fallback**。并入 exec-error
  反而**改变**语义并放开 fallback（会让调用方拿同一份命中 secret 的 context 再派一次）。

## 轮 2 复审（双 PASS）——判据是**反向变异**

| 项 | 变异 | 结果 |
|---|---|---|
| I1 冻结闸门 | 改回 `if kind == "ok":`（只要 terminal 就冻结） | **RED** |
| I2 CLI 轰炸 | 删节流、每轮 `liveness = None` | **RED**（spy 读的是 fake claude **可执行文件自己**追加的 jsonl，一行 = 一次真实进程 exec，非函数调用计数） |
| M3 递归守卫 | 去掉 `_rechecked` | **RED** |
| M1/M2/M4 | `with` 三处 · 常量已删（全仓零引用） · docstring 逐子命令补 `2=usage-error` | 均已落地 |

**新回归扫描（实测非读码）**：`rc=0→SUCCEEDED` · `124→TIMED_OUT` · `3→secret-hit` · `7→exec-error` ·
`rc0_empty→CORRUPT` · `rc 有但缺 witness→CORRUPT` —— **六种 rc 已发布形态全部仍冻结**，闸门收窄
未误伤正常终态。

Spec 轴定向复审确认第 6 条验收标准仍成立：`test_collect_is_idempotent_byte_for_byte` 仍是活锚
（实现对 rc 后重复 collect 有**两重冗余保证**：`os.link` 首写者胜 + 写后回读 stored，**同时**打掉才红），
且新语义引 spec 原文判为**正解**——OVBG-02 的语境前提就是 rc 已发布，未授权冻结 rc 之前的探针性终态。

实跑 `pytest sdflow-init/tests/test_outside_voice_job.py -q` → **245 passed**；全量 **2395 passed / 8 skipped / 3 xfailed**。

## 编排层裁决

- **Minor defer**（全部显式带 `change` 字段）：**T216**（collect 幂等的两条冗余路径缺单路径回归锚）·
  **T217**（`parse_utc_iso` 的宽 `except Exception` 吞噬面收窄）· **T218**（`rc_bad` 路径重复 collect
  非逐字节一致，与 Global Constraint 字面偏差）。
- **T217 值得单独一提**：宽 except 的危害已被实证——去掉 `_rechecked` 守卫后 `RecursionError` 被吞，
  静默降级成**假的** `CORRUPT / "job metadata dispatched_at 时刻不可解析"` 而非崩溃。`_rechecked`
  只堵了当前这一条入口，吞噬面仍在。

## 跨票交接（下游票 MUST 消费）

- **Task 3**：① LOST 路径 **MUST** 翻 `unknown_cost` / orphan-warning 字段（Spec 轴轮 1 Minor 1），
  否则 Task 5 无可 gate 的字段；② `<site>.collected.json` 是本票新增的第 6 个 sidecar，reconcile
  需知其存在（terminal 已 collect 过的 job 可直接 `rm`）；③ 无 rc 的终态**不再冻结**，正是留给
  reconcile 去修正的面。
- **Task 5**：helper 对越界 `--timeout` fail-closed，而既有 SKILL 对越界 config 回落 900 ——
  **MUST 保留 SKILL 侧 clamp**，否则 config 打错字从「回落默认」变成「usage-error 罢工」。
- **Task 6**：Concern 1 —— `startup deadline = dispatch + 5s` 是 `design.md` 状态机原文（无 liveness
  限定），已照原样实现；supervisor 冷启动慢时会把一次**已计费**的合法 dispatch 降级。
  **留到真实 efficacy 跑完后按实测决定是否加 liveness 限定**（现在改属于拿推测反驳设计）。
