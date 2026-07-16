# Codex 侧验证观察点清单 — add-codex-host-support

> 用途：本 change 的核心价值（Codex 宿主里**真跨模型** outside voice）押在两个至今**未在真实 Codex 宿主验证**的假设上（`hand-off.md` 顶部 🔴 登记）。本清单让你切到 Codex session 后，照着核几个锚 + `reason_code` 就能判 efficacy 真伪，并把实测真值写回归档 proposal/design。
>
> **一切事实取自真实代码**（`resolve-models.sh` / `outside-voice.sh` / `anchor_lint.py::classify_combo` / `lens-metric-contract.md` 机读块），非凭记忆。
>
> 日期：2026-07-16 · 归档：`openspec/changes/archive/2026-07-16-add-codex-host-support/`

---

## 0. 前置（切 Codex 后先做，否则测的是旧脚本）

本 change 改了 `assets/hack/`（`resolve-models.sh` / `outside-voice.sh`），它们是 **copy 非 symlink**，不重跑 setup 就还是旧版：

```bash
# 在 Codex session、本仓开发 checkout 里：
git pull                       # 拿到 a09afb0 + tag v0.10.0（已合并的本 change）
bash setup.sh                  # 把新 resolve-models.sh / outside-voice.sh 装进 ~/.sdflow/hack/
~/.sdflow/hack/outside-voice.sh version   # 必须回 "outside-voice.sh 1.3.0"，否则 setup 没生效
```

---

## 1. 待验的三个假设 → 各由哪个观察点证实

| 假设 | 内容 | 观察点（跑什么、看哪个锚） | 判赢信号 |
|---|---|---|---|
| **A1** | `CODEX_THREAD_ID` 在 Codex 各形态都在场（宿主判定正信号） | `resolve-models.sh` 输出的 `SDFLOW_HOST`；评审报告的 `lens-metric` / `outside-voice` / `fanout-capability` 锚的 `host=` | `SDFLOW_HOST=codex`（**当前形态**） |
| **A3** | Codex 宿主能发出反向 `claude -p …` 并拿到 findings | `outside-voice` 锚的 `runner=` + `reason_code=` | `runner="claude"` ∧ `reason_code="ok"` |
| **e2e (10.1)** | 全链路产出 `host="codex"` 锚且 `anchor_lint` 绿 | 跑 `/sdflow-code-review` → 报告落锚 → `anchor_lint.py` 退出 0 | 锚含 `host="codex"` 且 lint 绿 |

> **A1 的边界**：一次评审只证**当前形态**（交互 / headless / `codex exec` / spawned subagent 之一）的 `CODEX_THREAD_ID` 在场。**完整 A1 需在每种形态各跑一次**看 `SDFLOW_HOST` 是否恒 `codex`。交互形态在本次 change 收尾里顺带就验了；其余形态需另跑。

---

## 2. 30 秒快速自查（做完整 change 之前先跑，最快拿 A1 + A3-preflight 信号）

```bash
# ① A1：宿主判定信号
eval "$(~/.sdflow/hack/resolve-models.sh --root "$(git rev-parse --show-toplevel)")"
echo "HOST=$SDFLOW_HOST  VOICE_RUNNER=$SDFLOW_VOICE_RUNNER  VOICE_MODEL=$SDFLOW_VOICE_MODEL"
#   期望：HOST=codex  VOICE_RUNNER=claude  VOICE_MODEL=<claude 强档 id>
#   若 HOST=unknown → 见 §5「HOST=unknown」；若 stderr 有「宿主信号冲突」→ CLAUDECODE 也被设了

# ② A3-preflight：claude CLI 在不在这台 Codex 机器上
~/.sdflow/hack/outside-voice.sh preflight
#   "ready"          → claude CLI 在 + timeout 在 → A3 有戏，做完整 change 时看 exec 结果
#   "not_installed"  → claude CLI 没装 → A3 现在证不了，见 §4
#   "missing-deps"   → claude 在但 timeout/gtimeout 没装（macOS: brew install coreutils）
```

`resolve-models.sh` 判宿主的正信号（`resolve-models.sh:48-63`）：`CLAUDECODE=1`⇒claude；`CODEX_THREAD_ID` 非空⇒codex；两者皆无 / 皆有⇒`unknown`（fail-loud，**MUST NOT 猜**）。

---

## 3. 该看哪几个锚（评审报告 `code-review-report.md` 里）

### 3.1 `outside-voice` 锚（**A3 的主证据**）

```
<!-- sdflow:outside-voice v1 site="code-voice" guard="…" host="claude|codex|unknown" runner="claude|codex|none" reason_code="…" findings="N" truncated="…" -->
```

在 **Codex 宿主**上，`SDFLOW_VOICE_RUNNER=claude`，所以：

| 你看到 | 含义 | A3 判定 |
|---|---|---|
| `host="codex" runner="claude" reason_code="ok"` | 反向 `claude -p` **真的发出去且拿到 findings** | ✅ **A3 证实** |
| `host="codex" runner="codex" reason_code="not-installed"` | claude CLI 不在这台机器 → 回落**同族** codex 子代理 | ❌ A3 未证（claude 没装，见 §4） |
| `host="codex" runner="codex" reason_code="timeout"` | claude CLI 在，但 `-p` 调用超时（默认 300s） | ❌ A3 未证（网络/认证/模型慢，见 §5） |
| `host="codex" runner="codex" reason_code="exec-error"` | claude CLI 在，但 `-p` 非零退出/空输出 | ❌ A3 未证（多半是**未认证**，见 §4） |
| `host="codex" runner="none" reason_code="secret-hit"` | context 或回传含密钥形状 → 拒发（安全兜底，非 A3 失败） | ⏸ 换个不含密钥的 change 再测 |
| `host="codex" runner="none" reason_code="fallback-unavailable"` | 连同族 fallback 子代理都派不出（Codex 子代理不可用） | ❌ A3 未证 + 子代理层也不可用 |

> **关键区分**：`runner="claude"` = 真跨模型走通了；`runner="codex"`（=host）= 回落到了同族，`claude -p` **没走通**，`reason_code` 告诉你为什么。

### 3.2 `fanout-capability` 锚（Codex 子代理能力 + A1 佐证）

```
<!-- sdflow:fanout-capability v1 host="codex" subagents="available|unavailable" mirrors="…" -->
```

- `host="codex"` → A1 交互形态再获一个佐证点。
- `subagents="available"` → Codex 能派子代理（探针哨兵回来了）；`unavailable` → 派不出，roster 已缩（诚实降级，非 bug），但 fan-out 覆盖变薄。

### 3.3 `lens-metric` 锚（受 `config.metrics.enabled` 门控）

```
<!-- sdflow:lens-metric v1 layer="code-review" lens="…" runner="…" host="codex" … -->
```

本仓 dogfood 默认 `metrics.enabled=true`，会落。看 `host="codex"` 是否贯穿全部镜行。

> ⚠ `metrics.enabled=false` 的仓不落此锚——不是 bug。

---

## 4. claude CLI 没装 / 没认证怎么办（A3 阻塞时）

`reason_code="not-installed"` 或 `reason_code="exec-error"` 时，A3 现在证不了。处置：

1. **装 claude CLI** 到这台 Codex 机器（`preflight` 探的就是 `command -v claude`，`outside-voice.sh:255`）。
2. **认证**：`claude -p` 需已登录/有 API key，否则装了也会 `exec-error`（非零退出）。装完先手验一句：
   ```bash
   echo "回 PONG" | claude -p --model "$SDFLOW_VOICE_MODEL" --output-format text
   ```
   拿到回复 → 再重跑评审，`outside-voice` 锚应翻成 `runner="claude" reason_code="ok"`。
3. **失效方向是安全的**：没装/没认证只会**降级到同族 fallback**（`same-family`，`reason_code∈{not-installed,preflight-error,timeout,exec-error}`）——**不假绿**，锚如实记录。但**目标 efficacy 在该机器上 = 0**（Codex 里拿不到真跨模型意见）。

> **🔴 若 Codex 主力形态（headless/CI）本就不会有 claude CLI** —— 这不是"装一下"能解的，是 `hand-off.md` 定的纪律：**「任一在主力形态失效 ⇒ 须补 headless 替代信号或缩 scope」**（design Migration step 0）。这时把实测结论写回 design Risks，另开 scope 收缩 change。

---

## 5. `HOST=unknown` / 信号冲突怎么办

| stderr 告警 | 根因 | 处置 |
|---|---|---|
| 「宿主判不出（CLAUDECODE 与 CODEX_THREAD_ID 均未设置）」 | 当前形态没有 `CODEX_THREAD_ID`（**这正是 A1 在该形态失效**！） | 记录：该形态 A1 = 假。这是重要发现，不是环境问题——按 hand-off 补 headless 替代信号 |
| 「宿主信号冲突（CLAUDECODE=1 且 CODEX_THREAD_ID 非空）」 | 两个信号都设了（如从 Claude 嵌套起 Codex） | 清掉 `CLAUDECODE` 再测；这是脏环境，非目标态 |

`HOST=unknown` 时全链路走 `runner="none" reason_code="host-unknown"`，**不跑 voice**（fail-loud），报告显著标注本轮无跨模型第二意见——这是设计好的安全降级。

---

## 6. `anchor_lint` 合法组合矩阵判读（`classify_combo`，🔴 自审红线单一源）

`anchor_lint.py` 对每条 `outside-voice` 锚跑 `classify_combo(host, runner, reason_code, findings)`，分五类（`anchor_lint.py:428-451`）：

| 类别 | 条件 | 对 A3 的意义 | lint 行为 |
|---|---|---|---|
| **cross-model** | host,runner∈{claude,codex} ∧ runner≠host ∧ `reason_code="ok"` | ✅ **真跨模型**（A3 证实） | 放行 |
| **same-family** | runner==host ∧ `reason_code∈{not-installed,preflight-error,timeout,exec-error}` | 回落同族，A3 未证 | 放行（合法降级） |
| **no-exec** | runner="none" ∧ findings==0 ∧（host=unknown∧`host-unknown` 或 host∈{claude,codex}∧`reason_code∈{secret-hit,fallback-unavailable}`） | 没执行 | 放行 |
| **self-review** 🔴 | runner==host ∧ `reason_code∉` 降级码集 | **假绿红线**——同族却谎称正常 | **报错阻塞** |
| **illegal** | 其余一切（含 `runner="unknown"`） | 锚自相矛盾 | **报错阻塞** |

> **矩阵的诚实边界**（`anchor_lint.py:459`）：它只判**锚行自身内部一致性**（字段是否自洽），**堵不住伪造**——有人手写 `reason_code="ok"` 谎称跨模型仍会过（无 host 真伪的机械信号，属语义残余）。∴ 真正的 A3 证据是**你亲眼看到 `runner="claude" reason_code="ok"` 且报告里 outside-voice 真的带回了 findings**，不是"lint 绿了"。

---

## 7. `reason_code` 全枚举速查（`lens-metric-contract.md` 机读块 + SKILL 映射）

枚举域：`ok · not-installed · preflight-error · timeout · exec-error · host-unknown · secret-hit · fallback-unavailable`

| reason_code | 何时落 | outside-voice.sh 出处 |
|---|---|---|
| `ok` | exec exit 0，findings 到手 | `do_exec` 成功、`cat last-message.md`（:244） |
| `not-installed` | preflight `command -v <runner>` 不存在 | :255-256 |
| `preflight-error` | preflight `missing-deps`（timeout 缺）**或**任何畸形/非零 | SKILL 映射（**MUST NOT 原样落 `missing-deps`**，D7；否则撞矩阵 illegal） |
| `timeout` | exec exit 124 | timeout `-k 10` 触发（:228） |
| `exec-error` | exec exit 1（runner 报错/空输出/命令缺失） | :229-239 |
| `host-unknown` | `SDFLOW_VOICE_RUNNER` 空（host 判不出），不跑 voice | :251-253 / :175-178 |
| `secret-hit` | 入境 context 或**出境回传**含密钥形状 → 拒发 exit 3 | `secret_scan`（:150, :201, :243） |
| `fallback-unavailable` | 主路径失败 + 同族 fallback 子代理也派不出 | SKILL F8 分支（runner=none findings=0） |

---

## 8. 验完把真值写回哪里（闭合欠债）

按 `hand-off.md` 「合并后 MUST 补做」：

1. **proposal 假设表**（`…/add-codex-host-support/proposal.md` 的 `## Assumptions` / A1·A3 行）：把「未在真实 Codex 沙箱内验证」改为实测结论（形态 + 日期 + 锚证据）。
2. **design Risks**（`…/design.md`）：A1/A3 风险行补实测。
3. **tasks 0.1/0.2/0.3/10.1**：真跑通了才勾 `- [x]`，附锚证据；任一形态失效则保持 `- [ ]` + 一句失效说明（诚实，勿假勾）。
4. **若主力形态失效** → 另开 scope 收缩 change（补 headless 替代信号或缩 Codex scope），别默默留着假设。

> 归档目录通常只读——回写真值时可在归档 change 内就地订正这几处（它们本就是本 change 的产物），或按项目习惯在新的 follow-up change 里记录实测结论并引用本清单。

---

## 9. 实测结果记录（2026-07-16，真 Codex 宿主·交互形态）

| 项 | 命令 | 结果 | 判定 |
|---|---|---|---|
| A1 交互 | `env` in Codex exec env | `CODEX_THREAD_ID=019f696d-706d-7b91-a05f-bf8541089bd2` 在场（PATH 含 `.codex/tmp/arg0/…` 确证 Codex 执行环境） | ✅ 证实 |
| 宿主/档位解析 | `eval "$(resolve-models.sh …)"; echo …`（**一个 shell 内**） | `HOST=codex  VOICE_RUNNER=claude  VOICE_MODEL=opus` | ✅ 正确 |
| A3 前置 | `outside-voice.sh preflight` | `ready`（claude CLI + timeout 在场） | ✅ |
| A3 出境 | `outside-voice.sh exec --context-file <smoke> --timeout 120` | `exit=0` + 反向 `claude -p --model opus` 返回真 findings（4 条，含 `/` 空参放大器 + 缺 `--` 选项注入）；`OV_TRUNCATED=false`；reviewer 跑 `Glob **/demo.sh` 证仓库访问生效、FRAME 隔离生效 | ✅ 证实 |

**结论**：**A1 + A3 交互形态在真 Codex 宿主验通**，Codex 出境网络未封、认证可用、真跨模型 voice 有实际增量价值（非走过场）。

**踩坑留痕（对后续验证有用）**：首次 `HOST=unknown` 是**误判**——命令分三条跑、每条独立 shell，`eval` export 的六变量不跨命令持久（Codex 与 Claude Bash 工具同此模型）。**必须把 `eval` 与消费它的命令拼在同一条命令里（`;` 连接）**，否则下一条命令读到空。此非脚本缺陷；workflow SKILL 里"eval 一次、后续读 `$SDFLOW_*`"靠的是执行 agent 把值读进上下文再作字面量拼命令，不靠 shell 变量存活。

**仍待验（未闭合）**：A1 的 `headless` / `codex exec` / `spawned subagent` 三形态（各需在该形态跑一次看 `CODEX_THREAD_ID`）；10.1 正式评审的 `host="codex"` 锚 + `anchor_lint` 绿（拟随 Codex 上 `scoped-test-per-task` 的 `/sdflow-code-review` 产出）。
