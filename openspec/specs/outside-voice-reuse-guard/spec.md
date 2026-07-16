# outside-voice-reuse-guard Specification

## Purpose
TBD - created by archiving change mlh-p4-reason-code-validators. Update Purpose after archive.
## Requirements
### Requirement: outside-voice 复用三判归约为单一 reason_code

校验器 SHALL 对 spec-review 复用 outside-voice 的三前置（来源 / 新鲜度 / 结构）按序判定，归约出**唯一** reason_code，取值属固定七枚举 `none|file-missing|section-not-found|zero-findings|stale|simulated-source|same-family`〔add-codex-host-support：新增 `same-family`；原六码〕。`none` = 三判全过（可复用），退出码 0；任一不过 = 对应原因码。

**结构判 MUST 按合法组合矩阵的「跨模型」判定认定可复用的 voice 段，MUST NOT 自写 `runner ≠ host` 或按 runner 枚举值硬编码**〔add-codex-host-support · spec-review-r2 C1〕：可复用的 outside-voice 段 SHALL 为**矩阵判「跨模型」为真**的段（`host,runner 均∈{claude,codex} ∧ runner≠host ∧ reason_code="ok"`）。旧实现判 `runner == "codex"` 会把 Codex 宿主的 codex 自审放行复用；而首轮改的 `runner ≠ host` 又被 `runner="none"` 击穿（`none≠host` 恒真 → 把无执行段误认作可复用跨模型段，spec-review-r2 C1）。∴ 判据 MUST 引用矩阵单一判定。产物中只有 `runner == host` 的同族 fallback 段、**或 `runner="none"` 的无执行段**时 SHALL 输出 `same-family`（视同无有效跨模型 voice，回落自跑），MUST NOT 复用。

`host` SHALL 取自被复用产物的锚行 `host=` 字段；产物锚行无 `host`（v1 旧锚）时 SHALL 读作 `host="claude"`（历史事实：所有存量轮次均为 Claude 宿主），MUST NOT fail-closed 罢工（旧产物依然可复用）。

#### Scenario: mode=simulated 判无效
- **WHEN** `gstack-review.md` 的 `step1-broad-review` 锚 `mode="simulated"`
- **THEN** 输出 `simulated-source`，退出码非 0

#### Scenario: 产物早于源文件（陈旧）〔spec-review Q-C〕
- **WHEN** 产物 `gstack-review.md` 的 fs-mtime 早于源文件（proposal/design/tasks/specs）最大 fs-mtime（**排除评审产物自身**：gstack-review.md / spec-review-report.md / .outside-voice/）
- **THEN** 输出 `stale`（fail-safe 重跑，非假新鲜复用陈旧审查）

#### Scenario: outside-voice 段不可解析
- **WHEN** `gstack-review.md` 存在但解析不出 outside-voice findings 段
- **THEN** 输出 `section-not-found`（best-effort parse 失败 fail-closed 到此码）

#### Scenario: outside-voice findings 为 0 条
- **WHEN** 段可解析但 findings 计数为 0
- **THEN** 输出 `zero-findings`

#### Scenario: 文件缺失
- **WHEN** `gstack-review.md` 路径不存在
- **THEN** 输出 `file-missing`

#### Scenario: 三判全过可复用
- **WHEN** mode=native 且产物不早于源文件 且 outside-voice 段可解析（**矩阵判「跨模型」为真**：`host,runner∈{claude,codex}∧runner≠host∧reason_code="ok"`）且 findings>0
- **THEN** 输出 `none`，退出码 0

#### Scenario: 同族 fallback 段不得复用为跨模型 voice〔add-codex-host-support〕
- **WHEN** 产物中 outside-voice 段的 `runner == host`（如 `host="codex" runner="codex"`，即 codex 自审 / 同族 fallback）
- **THEN** 输出 `same-family`、退出码非 0，回落自跑真跨模型 voice，MUST NOT 因其"格式完整、findings>0"而复用（复用它等于把自审当成第二意见）

#### Scenario: runner="none" 无执行段不得复用〔spec-review-r2 C1〕
- **WHEN** 产物中 outside-voice 段 `runner="none"`（host-unknown/secret-hit/fallback-unavailable 的无执行轮次，`none≠host` 会满足首轮 `runner≠host` 误判）
- **THEN** 矩阵判「跨模型」为假 ⇒ 输出 `same-family`、退出码非 0，回落自跑，MUST NOT 复用（无执行段无 findings、非第二意见）

#### Scenario: v1 旧锚缺 host 字段不因缺字段罢工（向后兼容读）〔add-codex-host-support；code-review V3 据实订正〕
- **WHEN** 产物锚行为 v1 格式（无 `host=`，`runner="codex"`）
- **THEN** 读作 `host="claude"`，MUST NOT 因缺 `host=` 字段罢工（向后兼容读，非 fail-closed）
- **事实订正（V3，实测归档语料）**：原 Scenario 假设「v1 **无** `reason_code` 字段 ⇒ 兼容读作 `ok` ⇒ 可复用」——**与实况不符**：真实归档 v1 outside-voice 锚**带** `reason_code`（实测 `reason_code="none"` ×35 / `""` ×30 / `native-run` 等非枚举值），非"无字段"。guard `attrs.get("reason_code","ok")` 仅在**字段缺失**时补 `ok`；v1 锚字段**存在但值=none/""**（≠`ok`）时按存在值读 ⇒ 矩阵判非 cross-model（`reason_code≠ok`）⇒ **保守判不可复用、回落重跑 voice**。∴ 真 v1 codex 产物**不会被复用**（与原「v1 仍可复用」措辞出入），但方向**安全**（宁重跑不假复用）。运行期影响有界：done 不重 lint 旧报告、aggregator 只读 lens-metric 锚不读此 reason_code。（可选后续增强：让 guard 把 v1 `reason_code∈{none,""}` 兼容读作 `ok` 以恢复复用——记 todolist，非本 change）

### Requirement: 新鲜度用源文件 fs-mtime 直比、纯 stdlib、门控外置〔spec-review Q-C·撤销 grill Q3〕

校验器 SHALL 用 `os.stat` 比较产物 fs-mtime 与源文件最大 fs-mtime 判新鲜度，MUST NOT 调 subprocess / git，MUST NOT 读 config——纯 stdlib、纯函数可测。〔grill Q3 曾反转为「自跑 git + `git status --porcelain` 全目录 dirty」，但全目录 dirty 含评审产物自身 → 守卫恒判 stale → 双 codex（冷镜 F1 揭穿反噬）；fs-mtime 源文件直比既根治「git-log 看不到未提交」之坑、又无需 git。〕

#### Scenario: 纯 stdlib 无 subprocess
- **WHEN** 校验器执行任意判定路径
- **THEN** 进程不 fork / exec 子进程；新鲜度用 fs-mtime 直比、不调 git

### Requirement: 坏输入 fail-closed

校验器 SHALL 对无法判定的坏输入（`step1-broad-review` 锚缺失、mode 非枚举值）以非零退出 + stderr 原因结束，MUST NOT 静默产出某个 reason_code 掩盖损坏。

#### Scenario: 锚缺失非零退出
- **WHEN** `gstack-review.md` 缺 `step1-broad-review` 锚或 mode 值不在 `native|simulated`
- **THEN** 退出码非 0，stderr 打印 `[outside_voice_guard] FAIL: <原因>`（区别于正常的 `simulated-source` 判定）

