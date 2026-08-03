# 高价值 issues 清理 实施路线图

> 版本：v1（2026-08-02，初始规划）

## 概览

7 个高价值 issue（6 todo + 1 bug），按依赖关系和改动文件集分为 4 个阶段。
原则：**能合批的合批**（同一文件集 / 同一 skill），**有依赖的串行**，**无依赖的可并行**。

| 阶段 | 内容 | 涉及 issue | 就绪度 |
|---|---|---|---|
| **P1** · issues 读写路径加固 | 读取路径诚实化 + reindex 丢数据 bug | T231 + B12 | ✅ 已完成（change `harden-issues-read-write`） |
| **P2** · 安全与锚一致性 | voice 路径注入 + anchor_lint 镜名缺失 | T164 + T148 | ⬜ 可立即开始（与 P1 并行） |
| **P3** · gate 基础设施 | archive 打断测试 + tickets 存储改造 | T179 + T244 | ⬜ 可立即开始（与 P1/P2 并行） |
| **P4** · 下游推送 | canonical 改动推给消费项目 | T239 | ✅ 已完成（消费项目已跑 sdflow-init update） |

---

## 阶段 1 · issues 读写路径加固（T231 + B12）

### 合批理由

T231（读取路径诚实化）和 B12（reindex 丢数据）改的是同一份代码（`sdflow_issues_core/__init__.py`
的 `_scan_pool` / `_legacy_item_from_row` / `reindex`），根因相交（脏数据进入后的处理路径），
修法互补（T231 补校验 + B12 补 fail-closed）。分开做会产生两次对同一文件的 spec-review。

### 目标

- **T231**：status/type/priority 词表校验（显红）+ reindex 遇脏行降级而非 raise 罢工 + triage 解耦不强推状态
- **B12**：版本偏斜下 reindex 拿残缺集合覆盖 INDEX 且 exit 0 → 写盘前校验项数不降/降幅 fail-closed

### 前置条件

- 无。dedupe-issues-scripts-shared-layer 已交付（三脚本合一），阻塞已解除。

### 预估规模

中型 change。改动面：`sdflow_issues_core/__init__.py` 若干处 + 对应测试。
T231 描述里已有详细修法（一处 `problems.append` + 删两个 raise + 拆 `open_untriaged` 链 + 测试）。

### 验收标准

- 脏 status/type/priority 行 → scan 报 problem 不 raise，reindex 降级跳过不中止
- 版本偏斜下 reindex → 检测到项数骤降 fail-closed，不覆盖 INDEX
- triage 不再对有归属项强推 OPEN→PROPOSED

---

## 阶段 2 · 安全与锚一致性（T164 + T148）

### 合批理由

T164（路径引号注入）改 `outside-voice.sh`，T148（anchor_lint 镜名）改 `anchor_lint.py` + spec 文本。
文件集不重叠，但都是单点修复 + 需走 spec-review 改 spec 文本。合批减一次评审循环。

### 目标

- **T164**：outside-voice exec 的 `--context-file` 路径加引号防空格/元字符注入
- **T148**：`_FANOUT_MIRRORS` 加 `history` + 同步 spec.md/design.md 三处 SHALL 条款

### 前置条件

- 无。

### 预估规模

小型 change。T164 是 outside-voice.sh 一两处路径引号；T148 是 anchor_lint.py 一行 + spec 文本三处。

### 验收标准

- 含空格/`$()`/`\`` 的 context-file 路径 → 不触发命令注入
- `_FANOUT_MIRRORS` 含 `history`，code-review 不再借用 `grounding` token

---

## 阶段 3 · gate 基础设施（T179 + T244）

### T179 和 T244 不合批

**T179**（archive 打断测试）是中型，改 sdflow-done/sdflow-ship SKILL + 测试。
**T244**（tickets 存储改造）是大型，改 ship_gate.py 六函数 + 大量测试。
文件集有交集（ship_gate.py）但工作量悬殊，且 T244 描述明确说「不建议现在动——除非 Phase C 并行真正启动」。

### 建议

- **T179 先做**（中型，独立）：archive 后补跑测试 / gate 判 SHIPPED 前校验绿。
- **T244 观察**（大型，条件触发）：等 Edit 追加 ticket 出过事故，或 Phase C 并行真正需要时再起。
  当前 tickets 管线用单文件 `tickets.md` + `impl_route.py task-text` 机械提取已运转正常。

### T179 目标

- sdflow-done archive 步骤后补跑 `pytest`，失败不 merge
- 或 gate 的 SHIPPED 判定加「最近 commit 测试绿」前置

### 前置条件

- 无。

### 预估规模

- T179：中型（SKILL 编排改动 + gate 校验逻辑）
- T244：大型（ship_gate.py 六函数 + 2x 测试），**暂不排期**

### 验收标准（T179）

- archive 后若 pytest 红 → 不自动 merge，报告哪些用例挂了
- gate SHIPPED 判定不再对测试状态盲视

---

## 阶段 4 · 下游推送（T239）

### 目标

在每个已铺 workflow bundle 的消费项目跑 `sdflow-init update`，核验：
- `generation-process.md` §四 含分支 A/B
- `workflow.md` §三.2 含 G1 具名例外
- `reference/quality-layering.md` 含 G1 具名例外

### 前置条件

- 无技术前置。操作性质：人在各消费项目逐个跑 `sdflow-init update` + 核验。

### 预估规模

操作型，每个消费项目 ~5 分钟。

### 验收标准

- 所有消费项目的 `openspec/workflow/` 规则已同步到最新 canonical

---

## 阶段依赖图

```
  P1 (issues 读写) ──独立──▶ ✅ 已完成
  P2 (安全+锚)    ──独立──▶ ⬜     四阶段无强依赖，可并行
  P3 (gate T179)  ──独立──▶ ⬜     T244 暂不排期
  P4 (下游推送)   ──独立──▶ ✅ 已完成
```

## 建议执行顺序

虽然四阶段可并行，建议按**风险×紧迫度**排序逐个做（减并行改 review 冲突）：

1. **P2**（安全 T164 + 锚一致性 T148）— 最小且含安全修复
2. **P1**（issues 加固 T231 + B12）— 真实数据丢失 bug
3. **P4**（下游推送 T239）— 纯操作，可穿插
4. **P3**（gate T179）— 中型改动，T244 观望
