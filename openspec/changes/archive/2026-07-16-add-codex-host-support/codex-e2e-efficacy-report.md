# Codex 宿主 e2e efficacy 验收报告 — add-codex-host-support 欠债兑现

> 日期：2026-07-17 · 验收载体：`mlh-p6-recorder-frontmatter` 的 spec-review（首次在真实 Codex 宿主跑整轮 workflow）
> 依据：本目录 `codex-verification-checklist.md`（锚剧本）+ `hand-off.md` §7（欠债登记）
> 一切事实取自真实评审锚（`mlh-p6-recorder-frontmatter/spec-review-report.md`、`gstack-review.md`、`.outside-voice/`），非凭记忆。

---

## 0. 这份报告闭合什么

`add-codex-host-support`（v0.10.0，2026-07-16）在**用户 C 授权「未验即合并、风险自负」**下合并，把 A1/A3/e2e 三个核心假设的真机验证记为**最高优先级合并后欠债**（`hand-off.md` §7）。

- 07-16 收尾跑在 Claude 宿主，只用**交互形态手动 smoke**（`--timeout 120` + 小 context）验了 A1+A3 ✅（`codex-verification-checklist.md` §9）。
- checklist §184 明列 **仍待验 = e2e (10.1)**：正式 `/sdflow-*-review` 全链路产出 `host="codex"` 锚 + `anchor_lint` 绿。

**`mlh-p6-recorder-frontmatter` 的 spec-review 就是那次「仍待验」的正式评审**——首次让 autoplan + 多镜 + outside-voice + lens-metric 整条链在真 Codex 宿主上跑。本报告按 checklist 锚剧本核完，给出 e2e 实测结论。

---

## 1. 结论速览（三层）

| 假设 | 判定 | 相对 07-16 smoke 的变化 |
|---|---|---|
| **A1** 宿主判定（`CODEX_THREAD_ID` → `HOST=codex`） | ✅ **证实并升级** | 从「交互单点 smoke」升级到「真实评审全链路 9 锚」 |
| **A3** 反向 `claude -p` 跨模型 voice | ❌ **真实负载下系统性失效** | **与 smoke 结论相反**：smoke `runner="claude" ok`；实跑 3/3 `runner="codex" timeout` |
| **e2e (10.1)** 全链路锚 + lint | ✅ 机械层 / ❌ efficacy 层 | 机械层达标（合法降级不假绿）；目标价值 efficacy=0 |

> **一句话**：codex 这轮 workflow 跑通了、且诚实暴露了核心目标的失效（A3 真实负载 efficacy=0），这是**合格的 e2e 验收**；但它止步于「暴露」，未完成 checklist §8 要求的闭环——真值未回写归档、纪律要求的缩 scope/换机制决策未做。**价值兑现一半，欠债收口一半悬空。**

---

## 2. A1（宿主判定）：✅ 证实并升级

真实评审全链路 **9 处锚全部 `host="codex"`**，不再是单点 smoke：

| 锚 | 出处 |
|---|---|
| `fanout-capability … host="codex" subagents="available"` | `spec-review-report.md:7` |
| `outside-voice … host="codex"`（×3） | `spec-review-report.md:129,133`、`gstack-review.md:195` |
| `lens-metric … host="codex"`（×5） | `spec-review-report.md:156–160` |

- `subagents="available"`：Codex 能派子代理（capability probe 真派出、收到 `PROBE_OK`，见 `spec-review-report.md` §「执行与独立性」Step2）。
- **A1 从「交互形态手动 smoke」升级为「真实评审全链路」证实**——这是本轮实跑的正面兑现。

---

## 3. A3（反向跨模型 `claude -p`）：❌ 真实评审负载下系统性失效

### 3.1 锚证据（3/3 全降级）

三个 outside-voice site 全部 `runner="codex" reason_code="timeout"`：

```
spec-review-report.md:129  site="hr-tg"        host="codex" runner="codex" reason_code="timeout" findings="3"
spec-review-report.md:133  site="design-voice" host="codex" runner="codex" reason_code="timeout" findings="3"
gstack-review.md:195       site="design-voice" host="codex" runner="codex" reason_code="timeout" findings="3"
```

对照 checklist §3.1 判定表，`host="codex" runner="codex" reason_code="timeout"` = **「❌ A3 未证——claude CLI 在，但 `-p` 调用超时，回落同族 codex」**。

报告正文两处明确记录（失效方向诚实，未假绿）：
- `spec-review-report.md:28`：**「两个 Claude outside voice 都真实运行至 300 秒 timeout……本轮没有跨模型第二意见，只有可审计的同族 fallback。」**
- `gstack-review.md:193`：**「跨模型 Claude runner 按 helper 契约运行到真实 300 秒超时，未返回 findings；随后用 helper 的同一 prompt 回落 fresh Codex 子代理。」**

### 3.2 根因判定：不是配置问题，是真实负载问题

| 维度 | 07-16 smoke（A3 ✅） | 本次真实评审（A3 ❌） |
|---|---|---|
| timeout | 120s | 300s（**2.5×**，仍全超时） |
| context | 小 smoke 文件 | `design-voice-context.md` 10.9KB + `hr-tg-context.md` 3.3KB + 真实评审推理 |
| 结果 | `runner="claude"` 拿到 4 findings | `runner="codex"` timeout，3/3 |

**根因不是 timeout 设太小**（用了默认 300s 仍系统性超时）**，而是 `claude -p` 在真实评审负载下出境评审跑不完** → outside-voice 层这轮退化成 **codex 看 codex**，efficacy = 0。

---

## 4. e2e (10.1)：机械层 ✅ / efficacy 层 ❌

- ✅ **机械层达标**：host 锚落盘、`anchor_lint` 判 **same-family 合法降级**（`runner==host=codex ∧ reason_code=timeout` ∈ 降级码集，checklist §132）、未触发 self-review 红线、报告正常产出。**失效方向安全、不假绿**——三处都显式标注「没有跨模型第二意见」。这是 `hand-off`「失效方向安全」+ checklist §132 same-family「合法降级」的**正例**，是本 change 做对的部分。
- ❌ **efficacy 层未达**：目标价值（真跨模型第二意见）= 0。checklist §75 的关键区分——`runner="claude"`=真跨模型走通；`runner="codex"`（=host）=回落同族、`claude -p` 没走通。

---

## 5. 三个评估判断

### ① 本轮实跑证伪了 07-16 smoke 验证的充分性（最大价值产出）

120s + 小 smoke context 让 A3 当时判赢（`runner="claude" ok`），给了 A3 一个**虚假的正当性**；真实评审用 2.5 倍时长仍 3/3 系统性超时。**checklist 的 A3 验收剧本从设计上漏了「真实负载」这一维**——判赢信号只问「能否拿到 findings」，没问「在真实评审 context + 可接受时延内拿到」。这正是「smoke=现状快照，真实评审负载才是目标态」（CLAUDE.md 基准③）。**codex 这轮把一个被 smoke 掩盖的目标态失效照出来了——这本身是合格的验收。**

### ② 触发了红线纪律，但纪律动作只做了一半

checklist §110 / `hand-off` §20 定：「任一在**主力形态**失效 ⇒ 须补 headless 替代信号或缩 scope」。A3 在**主力评审负载**下 3/3 全失效（不是边缘 case，是主路径），应触发**缩 scope 决策或换机制**，但：

- ❌ 实测真值**未回写**归档：`proposal.md:76`（A3 假设行）、`design` Risks、`tasks.md:98`（10.1）还停在 07-16 交互 smoke 的 ✅；`tasks 10.1` 甚至仍写「正式评审尚未跑」——**其实已经跑了，结论是 timeout 降级**。
- ⚠️ 根因**易被误诊为「调 timeout」**：现有 `T31`（`cross-model-outside-voice`）记的是**反方向**（claude→codex，185KB→300s）的 timeout；本次 **codex→claude 反向、10KB context 就超时**尚无独立 todo。而「调 timeout」很可能不是正解——`claude -p` 出境真实评审动辄 10+ 分钟，每轮 N 个 site 各等这么久不现实，**这更像「Codex 宿主下 outside-voice 本质就是同族 fallback」的 scope 边界，不是调参能解的**。

### ③ 主要 gap = 验了但没收口

欠债从「未验」变成了「**已验未记**」：拿到决定性结论，却没回填归档、没翻 `tasks 10.1` 的牌、没建反向 timeout 的 todo、更没做缩 scope 决策。**风险**——下次翻 `proposal.md`，看到的还是交互 smoke 的 A3 ✅，会以为 Codex 宿主下跨模型 voice 是通的，而实测 efficacy=0。

---

## 6. 建议（需拍板）

1. **回填实测真值**（checklist §8 闭债动作）：把本次 A3 timeout 结论写回 `proposal.md` A3 行 + `design` Risks；翻 `tasks 10.1` 为「真实评审已跑，机械层 ✅、efficacy 层未达（3/3 timeout 降级）」，附本报告与锚证据。
2. **建独立 todo**：Codex→Claude 反向 voice 在真实评审负载下 300s 超时（区别于 `T31` 的反方向），记 efficacy=0 与候选解（异步/分片/加大 timeout/headless 替代信号）。
3. **拍 scope 决策（最关键，无法代拍）**：Codex 宿主下 outside-voice 接受「就是同族 fallback」这个边界，还是换机制根治？按纪律它现在就该被摆上台。

---

## 附录：锚证据清单（本报告全部结论的机读出处）

| 结论 | 锚 / 正文 | 出处 |
|---|---|---|
| A1 host=codex（fanout） | `fanout-capability … host="codex" subagents="available"` | `spec-review-report.md:7` |
| A1 host=codex（lens×5） | `lens-metric … host="codex"` | `spec-review-report.md:156–160` |
| A3 timeout（hr-tg） | `outside-voice … runner="codex" reason_code="timeout"` | `spec-review-report.md:129` |
| A3 timeout（design-voice） | 同上 | `spec-review-report.md:133`、`gstack-review.md:195` |
| A3 正文「300s timeout / 无跨模型」 | 「都真实运行至 300 秒 timeout……没有跨模型第二意见」 | `spec-review-report.md:28`、`gstack-review.md:193` |
| context 大小 | design-voice 10.9KB / hr-tg 3.3KB | `.outside-voice/design-voice-context.md`、`hr-tg-context.md` |
| smoke 基线（A3 曾 ✅） | `--timeout 120` exit=0，claude -p 返 4 findings | `codex-verification-checklist.md` §9（177–178） |
| 待验声明 | 「仍待验：10.1 正式评审 host=codex 锚 + anchor_lint 绿」 | `codex-verification-checklist.md:184` |
| 纪律 | 「主力形态失效 ⇒ 补 headless 替代信号或缩 scope」 | `codex-verification-checklist.md:110`、`hand-off.md` §20 |
| 归档未回写现状 | A3 行/10.1 停在 07-16 交互 smoke | `proposal.md:76`、`tasks.md:98` |
