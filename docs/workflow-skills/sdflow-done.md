# 自制 skill 展开 · `sdflow-done`

> 属 [工作流总览](../workflow-overview.md) 的展开。这是**阶段三收尾闭环**（第 9 步）——
> 把 reconcile → **verify** → **hand-off** → archive → commit → merge 串成一条收尾流水线。
>
> **一句话**：各步独立子代理、按本步性质选 model——**verify 强档**（唯一终门），archive 中档，commit 弱档，merge 留主 session。

---

## 1. 位置与契约

| 维度 | 内容 |
|---|---|
| 谁调它 | 阶段三第 9 步；`/sdflow-ship` 判 `RUN_VERIFY` 时（透传 merge 意图） |
| 进（输入） | `{change_name}` + 实现代码 + 四件套 |
| 出（产物） | `verify-report.md` + `hand-off.md` + 归档 `archive/{date}-{change}/` + 主 specs 同步 + INDEX + commit + ff-merge |
| 关键改进（v3） | ① 归档**必须**走 `openspec archive` CLI 同步 delta 到主 specs（旧版手动 mv 漏了）；② 默认分支自动检测（勿假设 main）；③ merge 缺省执行（ff）；④ verify 必产报告；⑤ 步骤固定 + 各步独立子代理按性质选 model |

---

## 2. 内部流程（串行门禁，失败即中止）

```mermaid
flowchart TD
    S0["Step0 · 确认 change + 捕获 merge 意图 + 检测默认分支 + tasks.md 复选框对账"]
    S1["Step1 · Verify（强档）<br/>Do Not Trust the Report · 每✅附机验锚点 · 产 verify-report.md（头部 frontmatter 机判锚）"]
    G1{"PASS?"}
    S2["Step2 · hand-off.md（P3g）<br/>§2.1 issues sweep：issues.py sweep --change 一键（内封 scan→triage→batch add→reindex）<br/>§2.2 roadmap 回填草稿：roadmap_writeback_draft.py 退出码分流"]
    S3["Step3 · Archive + Spec 同步（中档）<br/>openspec archive CLI（禁手动 mv）；中文遗留用 --skip-specs 手动同步"]
    S4["Step4 · Git Commit（弱档）<br/>git add openspec/ + git add -u；Conventional 中文 message；禁 push"]
    S5["Step5 · Merge（主 session）<br/>merge 前 untracked 硬检查（?? 即 halt）；缺省 ff-only；ff 不可行/冲突则停；不自动 push"]
    S6["Step6 · 最终摘要"]
    S0 --> S1 --> G1
    G1 -->|PASS +Minor| S2 --> S3 --> S4 --> S5 --> S6
    G1 -->|FAIL 核心缺口| STOP["停止，展示原因，等修复重触发"]
```

| 步 | 目标 | 注意事项 |
|---|---|---|
| 0 | 确认 + 对账 | **勿假设 main**（`git symbolic-ref` 检测默认分支）；**复选框对账**：SDD 实现常没勾 change 自己的 tasks.md → 勾真实完成的、未完成留 `[ ]` + 说明（**别假勾过 archive**） |
| 1 · Verify | 唯一终门，判 PASS/FAIL | **P3h 禁降档**：强档 + 「Do Not Trust the Report」冷启；**每 ✅ 必附机验锚点**（测试名/commit/文件:行），无锚点降 gap；只核心缺口 FAIL，Minor 判 PASS 注明；**必产 verify-report.md**，产报告后在文件**最顶端 prepend frontmatter 首块** `ship-gate:` → `verify: PASS`/`FAIL`（大写，非布尔；mlh-p5 起机判锚迁 frontmatter，旧 `<!-- ship-gate: verify=… -->` inline 注释锚已退役、live 不再读） |
| 2 · hand-off | 异步人类再入口 + 下个 change 种子 | verify **之后**（引其权威）/ archive **之前**（随归档留档）；三段（完成/未完成延后/下一阶段）；**不直接搬运 verify 的 ✅**（复核锚点存在性）；§2.1 sweep（一键）与 §2.2 roadmap 回填草稿先跑 |
| 3 · Archive | 归档 + delta 同步主 specs | **必用 CLI**（同步 delta + INDEX + 校验），**禁手动 mv**；中文遗留 spec → `--skip-specs` + 手动同步；**读真实代码核对每条 delta**（非照搬，审查可能改过方案） |
| 4 · Commit | 暂存 + 提交收尾变更 | `git add openspec/` + `git add -u`；Conventional 中文 message；**禁 push** |
| 5 · Merge | 缺省 ff 合并 | **merge 前 untracked 硬检查**（SR-2）：`git -c core.quotePath=false status --porcelain` 存在任何 `??` untracked 行 → **非交互 halt+报告**（列清单交人分诊；**MUST NOT AskUserQuestion 中途问、MUST NOT 静默继续 ff-merge**）；检查通过后缺省 `--ff-only`（勿硬编码 `--no-ff`）；ff 不可行/冲突 → 停下交用户；**不自动 push** |

### §2.1 issues sweep 子步

原手写 4 步循环已固化为 `issues.py` 的**一键封装子命令 `sweep`**，一行跑完：

```bash
python3 ~/.claude/skills/sdflow-issues/scripts/issues.py --root . sweep --change {change_name}
```

- **`--change {本change}` 必须显式传**（D4）——不靠 `detect_change` 自动探测。
- **非原子、fail-closed**：任一内部子步非零退出即整体非零退出，stderr 报明失败步与点位、不静默继续；已 tag 项重跑时被「批次空」过滤天然排除 → **半途失败直接重跑同一条命令即可收敛**，无需回滚。

内部仍是原来这 4 步（下图保留作机制说明，**已封装成单命令，勿再手写循环**）：

```mermaid
flowchart LR
    A["scan 两池 --open-ungrouped --change {本change}<br/>（非终态 ∧ 批次空）"] --> B["triage --批次 {本change}<br/>（幂等，已 PROPOSED no-op）"]
    B --> C["issues.py batch add {本change}<br/>（PLANNED，key=本 change 名）"]
    C --> D["issues.py reindex<br/>刷新 INDEX + 同步批次状态"]
    D --> E["hand-off 第2段引用该批次号"]
```

> **范围边界**：sweep 只圈**源==本change ∧ 非终态 ∧ 批次空**；孤儿项（源=""）不归本 sweep，交独立通用清理流程兜底（Q2 保守：永远只建 1 个批次、禁跨 change 合并）。

### §2.2 roadmap 回填助手子步（§2.1 之后、写 hand-off 三段之前）

verify 判完后跑 `roadmap_writeback_draft.py`（`sdflow-done/scripts/` 自带，sibling 路径 `~/.claude/skills/sdflow-done/scripts/`）机械生成 roadmap 回填草稿，供人异步确认回填 roadmap。**切分线（adr/0015）：机械只定位 phase 行；勾哪几行 / 算不算满足验收标准 / 价值叙述——判断留人**，助手 MUST NOT 代判、MUST NOT 直接改 roadmap。

```bash
python3 ~/.claude/skills/sdflow-done/scripts/roadmap_writeback_draft.py --change {change_name} --root .
```

**MUST 在非 `set -e` 语境执行**——exit 3/4/5/6/7 均属预期分支、非异常（`set -e` 下非零退出会中断脚本，吞掉后续 stderr 转述与 hand-off 记录）。

| exit | 语义 | 处置 |
|---|---|---|
| 0 | 草稿已产出 | stdout 即草稿，**原样贴进 hand-off「▶ 下一阶段建议」**；stderr 的 `WARN` 一并转述 |
| 2 | `CHANGE_DIR_MISSING` | 异常，停下核对 |
| 3 | 无 roadmap 关联 | 退现状、**不产草稿**；疑似 roadmap 驱动则 hand-off 留一行提示人工回填 |
| 4 | `BOARD_ABSENT`（verify-report 缺/无 frontmatter）或 `ROADMAP_MISSING` | 留人工，hand-off 记一行「未生成：<stderr 原因>」 |
| 5 | `BOARD_MALFORMED`（frontmatter 畸形） | **fail-closed 留人工**，不静默、不伪造 |
| 6 | `VERIFY_NOT_PASS` | 不出完成候选 |
| 7 | `BAD_ROADMAP_FLAG`（`--roadmap` 覆写格式不符） | **不静默 fallback**，记原因、修正后重跑 |

> 第六步最终摘要须抬一行 `Roadmap:`（⚠ 草稿待人确认 ｜ ⛔ 未生成（exit 4/5/6/7）｜ — 无关联），merge 时点可见；草稿产出即止，apply 由人异步、不保证。

---

## 3. Model 按本步性质（步骤固定 + 各步独立子代理）

| 步 | 性质 | 档位 | 理由 |
|---|---|---|---|
| verify | **唯一终门** + grep 代码判 PASS/FAIL | **强档** | 中档/弱档假 PASS = 放不完整活进归档；门不能省（P3h 禁降档） |
| archive | spec 同步 + 读代码核 delta | **中档** | judgment 活 |
| commit | git add + 从 diff 生成 message | **弱档** | 纯机械；失败也就重生成；独立上下文无副作用 |
| merge | 单向 git | **主 session** | 缺省执行、留主 session 可见 |

> **无运行时误分类**：步骤固定（非动态路由），写 skill 时一次定死，混用 model 无耦合。

---

## 4. 内部调度的子 skill / 子代理 / 脚本

| 被调 | 类型 | 角色 |
|---|---|---|
| verify / archive / commit 子代理 | 独立子代理（各自上下文） | 按本步性质选档；verify 冷启不信报告 |
| `openspec archive` CLI | 官方 CLI | 归档 + 同步 delta→主 specs + INDEX + 校验 |
| `issues.py` | 脚本 | **`sweep --change {本change}` 一键封装**（内封 scan→triage→batch add→reindex）；另有人工场景的 `batch add` / `reindex` |
| `buglist.py`/`todolist.py` | 脚本 | sweep **内部**调用的 `scan`/`triage`（不再由 skill 手写循环逐条调） |
| `roadmap_writeback_draft.py` | 脚本（sdflow-done 自带） | §2.2 roadmap 回填草稿机械核：退出码 0/2/3/4/5/6/7 分流，勾行与价值叙述判断留人（adr/0015） |

---

## 5. 人类门

**无强制人类门**（阶段三无人类门）。唯一「停」是 verify **FAIL（核心缺口）** → 中止、展示原因、等修复重触发；以及 merge 前 untracked 硬检查命中 `??` → 非交互 halt+列清单交人分诊、merge 的 ff 不可行/冲突 → 停下交用户决策。merge 缺省执行，仅当调用时**明确 opt-out**（「不要 merge」等）才跳过。

---

## 6. ★ 本 workflow 注入的规则/prompt —— 建议式 vs 强制

**统一判据**见[总览 §8](../workflow-overview.md#8-外部-skill-的注入强制性建议式-vs-强制统一规律)。sdflow-done 是**收尾闭环**，机械载体最密集（CLI、脚本、git、ship-gate 锚）。

| 项 | 类型 | 靠什么 |
|---|---|---|
| **frontmatter `ship-gate: verify` 锚（PASS/FAIL）** | **强制（下游门读 + 闭环）** | `ship_gate` 只读**报告文件首块 frontmatter**（`FIELD_ENUMS`/`parse_ship_gate_frontmatter`）判 SHIPPED / VERIFY_FAIL；live 读坏块 fail-closed UNKNOWN(6)；FAIL 不归档。旧 inline 注释锚已退役（仅归档读半场对旧档 dual-read 兜底） |
| **归档走 openspec archive CLI** | **强制（CLI 校验）** | CLI 做 delta 同步 + INDEX + validate；手动 mv 漏 spec 会被 validate 抓 |
| **issues sweep 脚本链** | **强制（脚本）** | `issues.py sweep --change` 一键封装（内封 scan/triage/batch add/reindex，非原子、fail-closed、重跑收敛）；FIXED 门禁必带根因+证据；批次完成判据（成员≥1 且全终态） |
| **merge 前 untracked 硬检查** | **强制（机械判据）** | `git status --porcelain` 存在任何 `??` 即 halt+报告，分诊交人；不 AskUserQuestion、不静默 ff-merge |
| **roadmap 回填草稿（§2.2）** | **半强制** | 退出码 0/2/3/4/5/6/7 分流机械且不静默（脚本兜底）；但勾行/价值叙述判断留人、apply 由人异步不保证（adr/0015） |
| **复选框对账**（勾真实完成的） | **半强制** | `openspec archive` 会警告 "N/M incomplete"（机械提示），但「诚实勾」靠子代理遵从（可假勾骗过 -y） |
| **verify 每 ✅ 附机验锚点（防假✅）** | **建议式（强框架）** | 无脚本逐条校验每个锚点真存在；靠**强档 + Do-Not-Trust 冷启**约束，禁降档是纪律。真实事故：曾把没落实的需求标 ✅ 静默放过（design §7.3.1/adr/0001） |
| **verify 强档 / archive 中档 / commit 弱档** | **建议式** | 无机制强制控制者真按档选；靠遵从 model-tiers（分类会过期=软成本） |
| **hand-off 不直接搬运 verify 的 ✅** | **建议式** | 靠主 session/子代理复核锚点存在性，无校验 |
| **merge 缺省 ff-only、不自动 push** | **半强制** | `git merge --ff-only` 本身会拒绝非快进（git 强制）；「不 push」靠遵从（prompt 禁 push） |

**结论**：sdflow-done 的**产物正确性**由机械门层层兜底——**verify frontmatter 锚**（ship_gate 读首块、坏块 fail-closed、FAIL 不归档）、**archive CLI**（validate 抓漏同步）、**issues sweep 一键脚本**（FIXED 门禁 + 批次判据）、**merge 前 untracked 硬检查**（`??` 即 halt）、**`git --ff-only`**（拒绝非快进）；而**verify 的「防假✅」本身是建议式**——没有脚本能逐条验证每个 ✅ 的锚点真成立，它靠**强档 + Do-Not-Trust 冷启 + 禁降档纪律**顶住。这是全流程去人类门后**最关键的一处「靠模型自觉」**，也是为什么 verify 铁律禁用弱档。

---

## 7. 小结

- 结构 = 对账 → verify（强档终门）→ hand-off（含 §2.1 sweep 一键 + §2.2 roadmap 回填草稿）→ archive（CLI 同步）→ commit（弱档）→ merge（untracked 硬检查 + ff）。
- **机械兜底**：verify frontmatter 锚（gate 读首块、坏块 fail-closed）、archive CLI validate、issues sweep 一键脚本门禁、roadmap 回填退出码分流、merge 前 untracked 硬检查、`git --ff-only`。
- **最关键的建议式**：verify「每 ✅ 附锚点防假✅」无脚本逐条校验——靠强档 + Do-Not-Trust + 禁降档，是去人类门后的唯一终门底线。

---

*接地基线：2026-07-10 · 对照 `sdflow-done/SKILL.md`（:76-93 verify frontmatter · :135-147 §2.1 sweep · :149-171 §2.2 roadmap 回填 · :262-288 merge untracked 硬检查）、`sdflow-done/scripts/roadmap_writeback_draft.py`（main() 退出码）、`sdflow-ship/scripts/ship_gate.py`（`FIELD_ENUMS` :288-292 · `parse_ship_gate_frontmatter` :295-386）。frontmatter 机判锚与正文 4 类 v1 锚（anchor_lint 机验）是两套锚，勿混述；口径详见 [workflow-map §3](../workflow-map.md)。*
