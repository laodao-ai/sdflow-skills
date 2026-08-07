<!-- sdflow:step1-broad-review v1 mode="native" -->

# autoplan 广审 · fix-probe-scan-precision

> **执行方式（native 佐证）**：本轮 autoplan 由主 session 经 Skill 机制**原生执行**（其 SKILL.md 指令直接进主
> session，未派子代理转述模拟）。侧信道佐证：preamble 实跑（`BRANCH: feat/fix-probe-scan-precision`、
> `REPO_MODE: solo`、`SLUG=laodao-ai-sdflow-skills`）、restore point 实落
> `~/.gstack/projects/laodao-ai-sdflow-skills/feat-fix-probe-scan-precision-autoplan-restore-20260806-232404.md`（627 行）、
> 四次 `codex exec` 真实调用（CEO/eng/DX 三次 + 探针）与三次 Agent 派发均有运行痕迹。
>
> **G2 适配**：autoplan 的两处人类门（premise 确认 · 最终批准）按 `sdflow-spec-review` 的 G2/C5 不弹窗，
> 连同全部自动决策登记进本文「决策登记」节与 `spec-review-report.md` 的决策登记区，人在设计 HARD-GATE 一次拍板。

---

## Phase 0 · Intake

**评审对象**：`openspec/changes/fix-probe-scan-precision/` 四件套 + `decision-memo.md`（305 行，D1–D16 / C1–C18）。

**盘面新鲜度**：四件套 mtime 23:16（commit `0f8b0a3` 相位 C 重写），存量 `spec-review-report.md` mtime 18:48 —— **早于重写**，
故本轮为对**重写后盘面**的重新评审，不复用上一轮结论。

**plan 摘要**：评审工具经两条更新方式不同的分发链落地（SKILL 走 symlink，`openspec/workflow/tools/` 走拷贝），
两个评审 SKILL 各写了一段手工 skew 探测散文。本 change 不修探测器，而是**消灭被探测的对象**：
resolver 删本地 pin 步、`copy_bundle` 停铺 tools/contract、两个 SKILL 删探测段、`ship_gate` 退役 `tools_spec` 腿、
`--dev`/`full` 退役、本仓 `openspec/workflow/` 下删 7 个文件。

**scope 检测**：
- **UI scope：无**。`grep -oiE "component|screen|form|button|modal|layout|dashboard|sidebar|nav|dialog"` 命中全部落在
  评审产物（`gstack-review.md`/`spec-review-report.md`/`decision-memo.md`）里的中文词英文子串，四件套本体零命中 ⇒ **Phase 2 跳过**。
- **DX scope：有**。开发者工具链（SKILL.md / CLI / agent / 升级路径 / 错误文案）55 处命中 ⇒ **Phase 3.5 执行**。

**Codex preflight**：`codex-cli 0.146.1`、auth OK ⇒ 三个阶段双声齐全，无降级。

**基线事实**：`/usr/bin/python3 -m pytest` = **2469 passed, 10 skipped**（全绿，296s）；
`openspec validate fix-probe-scan-precision --strict --type change` = valid。

---

## 执行偏离（如实登记）

autoplan 规定「双声顺序前台跑、Phase 逐个完成再进下一个」。本轮为控墙钟做了一处偏离：
**Phase 3（Eng）与 Phase 3.5（DX）的双声在 Phase 1 的 codex CEO 归位后即并发起跑**，
而非等 Phase 1 的 Claude 镜也归位。补偿：① eng/DX 的 prompt 已注入 codex CEO 的实质发现；
② 各阶段共识表仍在**两声均归位后**才构建；③ 跨阶段综合由主 session 在全部五镜归位后统一做。
**未偏离的部分**：每个阶段的两个声音都真实独立跑过，无一镜是主 session 代笔。

---

## Phase 1 · CEO Review（模式：SELECTIVE EXPANSION）

### 0A 前提拷问

本 change 的**承重前提**只有一条：**「skew 的唯一成因是消费仓副本；删掉 local-pin 步，skew 结构上不再可能。」**

拷问结果：**该前提在「稳态 Unix × 完整成功的 setup × 无 override」下成立，在其余状态下不成立。** 三条反例：

1. **部署期窗口**：SKILL 走 symlink（`git pull` 即生效），`resolve-workflow.sh` 走 `cp`（须 `bash setup.sh`，`setup.sh:536-545`）
   ⇒ pull 与 setup 之间是「新 SKILL（已无探测）× 旧 resolver（步①还在）」。
2. **`SDFLOW_HOME` 官方复活该组合**：delta spec 把它立为冻结规则版本的唯一路径，即「新 SKILL × 自备旧 bundle」。
3. **部分安装是被支持的成功态**：`setup.sh` 把每一处安装失败降级为 `skipped[]` 并 exit 0（`setup.sh:98-164`、`:471-484`）。

**防御性反驳（Eng 镜独立核验后提出，已采纳为限定条件）**：对**非 pin 仓**（本机 2/3）窗口期行为完全不受影响——
旧 resolver 的步②/③ 未变，而 canonical 是软链、内容已随 pull 变新。∴ 窗口的实际受害面 = **存量 pin 仓**，本机恰好 1 个。

**可辩护的表述**（建议 proposal/design 改用）：
> 删除 local-pin 消除的是「消费仓副本 skew」，且该消除在**完整成功的 setup 之后**生效。
> 它不消除 `~/.sdflow/hack/` 拷贝链的失鲜，也不消除 Windows 的 SKILL 快照失鲜。

### 0B 既有代码杠杆（What already exists）

| 子问题 | 已存在的东西 | 本 change 是否复用 |
|---|---|---|
| 全局规则解析 | `resolve-workflow.sh` 步②（canonical，两平台回落已实现并已测） | ✅ 复用，只删步① |
| 半坏 canonical 拦截 | `sane()`（`:69-73`） | ⚠️ 复用但**未随职责扩张而扩面**（见 F16） |
| 显式降级 | `exit 2` + 固定告警（`:82`） | ✅ 复用，不新增码位 |
| 残留告警 | `stale_shadow_warnings()`（`init.py:346`）+ `maintain_scan` | ✅ 复用，只改文案 |
| 冻结规则版本 | `SDFLOW_HOME`（`:8` 契约已明写，第 1 层测试已在用） | ⚠️ 复用但**它同时是 `setup.sh` 的安装根**（见 F4） |
| 托管子树整删重拷 | `copy_bundle` 非-full 分支的 `rmtree(tools_dst)`（`init.py:260-265`），`spec-workflow:194` 已授权 | ❌ **未考虑**（见 F38） |
| hack 链失鲜守卫 | `capability-manifest.json`（成员仅 3 项） | ❌ **被误当作已覆盖**（见 F1） |

### 0C Dream state

```
  CURRENT STATE                    THIS PLAN                      12-MONTH IDEAL
  两条分发链（bundle 拷贝链 +      删掉 bundle 拷贝链；            一条链、一个版本身份：
  hack 拷贝链），一个手工探测器    hack 链原样保留、探测器归零     SKILL/resolver/tools 同代且可机验
  ──────────────────────────  ──▶  ────────────────────────  ──▶  ──────────────────────────
  skew 面 2 · 探测器 1             skew 面 1 · 探测器 0            skew 面 1 · 机验 1
```

**Dream state delta**：本 plan 把 skew **面**从 2 减到 1，同时把 skew **探测**从 1 减到 0。
净方向对（消灭对象优于探测对象），但它在**仅存的那条链上恰好写入了新语义**（resolver 步①删除），
而那条链此刻既无探测也无机验。距 12-月理想的缺口 = 「一个 O(1)、可机械守的同代断言」。

### 0C-bis 实现备选（MANDATORY）

```
APPROACH A：照原样交付（plan 现状）
  Summary: 删双链、删探测、不做任何替代。
  Effort: M   Risk: Med
  Pros: 净删除；终结「新增特性要不要补探测信号」这个问题；符合人拍板的方向（D13）。
  Cons: 承重论证有事实错误（F1）；窗口期对 pin 仓从「起手硬停」降级为「末步裸崩」；
        `SDFLOW_HOME` 替代不成立（F4/F5）。
  Reuses: resolver 步②、sane()、exit 2、stale_shadow_warnings。

APPROACH B（推荐）：照原样交付 + 三处**零新机制**的收口
  Summary: 方向、范围、删除集全部不动；只做 ①订正 F1 的事实错误（改为"该链目前无守，登记为诚实边界"）
           ②扩 sane() 覆盖 tools/contract（它此后是唯一交付路径，扩面是目标态的必然推论，非加宽）
           ③把 `stale_shadow_warnings` 文案从绝对断言改为带前置条件的表述。
  Effort: M（比 A 多 ~1 天 CC ~20 分钟）   Risk: Low
  Pros: 不新建任何机制、不改 scope；把三条"会在 6 个月后咬人"的假陈述在落笔前修掉；
        ②本身就是 F16 指出的目标态缺口，不做才是缩水。
  Cons: sane() 扩面需要一份"runtime 必需成员"清单，该清单会随 tools 增删而维护（低频）。
  Reuses: 同 A，全部既有机制。

APPROACH C：codex 提的「版本化原子安装 + 仓级 `workflow-release` 键」
  Summary: `~/.sdflow/releases/<id>/` + `current` 指针原子切换；仓级配置键选 release。
  Effort: XL   Risk: High
  Pros: 真正解决 release 一致性；`workflow-release` 是 pin 的真替代（有仓级 producer）。
  Cons: **加宽**——人拍的板是"去掉 pin、规则共享"，不是"建版本化发布系统"；
        新建两套机制、跨平台原子性另是一个 change。命中通则③「不加宽」与④「不为低概率纠结完美方案」。
  Reuses: 几乎不。
```

**RECOMMENDATION：B。** 依据：它把 A 的三处**假陈述**修成真陈述而**不动目标范围**——
通则④说简化只能砍防御深度、不能砍目标范围；反过来，"论证里的事实错误"和"目标态下必然要覆盖的健全性面"
都不属于可简化的边角。C 被否：人已明确拍板方向（D13 证据锚「去掉 pin 仓这个逻辑，所有规则文件都应该是共享的」），
C 是替他重新定义目标。

### 0D SELECTIVE EXPANSION 分析

**复杂度检查**：本 change 触 8+ 文件、跨 5 个组件，但**几乎全是删除**，不新增类/服务 ⇒ 不触发"超 8 文件即 smell"的实质关切。

**最小达成集**：P0 四项（resolver 删步① · `copy_bundle` 停铺 · 两 SKILL 删探测段 · 对应测试）。

**扩张候选（cherry-pick，全部按 6 原则自动决策，不弹窗）**：

| # | 候选 | 效果 | 自动决策 | 依据 |
|---|---|---|---|---|
| X1 | 扩 `capability-manifest` 成员到安装目录全体 + 评审第零步无条件验一次 | 消灭 F1/F2 的根因 | **DEFER**（记 todo） | 是**另一条链**的问题（proposal Non-Goals 已明写不动 hack 链）；本 change 只需**不谎称它已被守**。P2 边界 |
| X2 | 扩 `sane()` 覆盖 tools/contract | 消灭 F16 | **ACCEPT** | 目标态下 canonical 是唯一 tools 源 ⇒ 健全性面必须跟着扩；不扩=缩水（通则③） |
| X3 | 最后一次 update 清删消费仓 `tools/`+contract 再停铺 | 终态零死码 | **需拍板**（见 Q2） | 既有 spec 已授权整删重拷，但触及"不自动删"的措辞边界，人拍板 |
| X4 | `--dev` 留一版 tombstone（识别参数 → fail-loud 给新命令） | 迁移引导 | **ACCEPT** | 成本 ~5 行；否则老用法只得 argparse generic error |
| X5 | resolver 加 `--help` | `SDFLOW_HOME` 可发现性 | **DEFER**（记 todo） | 与本 change 目标正交，属独立 DX 改进 |
| X6 | 仓级 `workflow-root` / `workflow-release` 配置键 | 给冻结能力一个真 producer | **REJECT** | 加宽，人未要求（同 APPROACH C 之否） |

### 0E 时序拷问（实现期该现在定的事）

| 阶段 | 实现者会撞到什么 | 现在该定 |
|---|---|---|
| HOUR 1 | 删 `copy_bundle` 的 tools copytree 后，`openspec/workflow/` 没人创建 | **F15**：3.1 必须显式加 `os.makedirs(dst, exist_ok=True)` |
| HOUR 2-3 | 跑 pytest 发现一批"tasks 没提过"的红测试 | **F10–F14**：把 6 个文件写进 tasks，并把检测方法从 grep 换成"直接跑 pytest" |
| HOUR 4-5 | 改 `CLAUDE.md:401/404/419` 后发现它们在托管块内 | **F17**：6.4 的动作对象是 `assets/snippets/claude-section.md`，不是 CLAUDE.md |
| HOUR 6+ | 归档时发现 4 个主 spec 与新契约矛盾 | **F6–F9**：现在就补 delta |

### 0F 模式确认

**SELECTIVE EXPANSION**（autoplan override）。已接受 X2/X4，DEFER X1/X5，REJECT X6，X3 交人。
选定实现路径 = **APPROACH B**。

### Step 0.5 · CEO 双声

**CODEX SAYS（CEO — strategy challenge）** — verdict: *Do not approve as written*。六节：
① "structurally impossible" 被仓库自身证伪（4 条路径：pull-without-setup 窗口 · `SDFLOW_HOME` 官方复活该组合 ·
部分安装被当成功 · capability-manifest 不含 `resolve-workflow.sh`）；② 探测器经济学不可信（无分母、n=1、
成本相等是断言非测量、"其余 tools fail-closed"未验却被 delta 当既成事实）；③ `SDFLOW_HOME` 是降级不是替代
（列出 pin 的 6 条属性 vs SDFLOW_HOME 的 6 条对立属性）；④ big-bang 捆绑是 release engineering 失败，
回滚不是 `git revert`；⑤ 备选被过快否决（版本戳 ≠ 整 bundle SHA；字节比对有界不撞基准 5；
pin-only 的弱点是"任一文件即 pin"的隐式激活而非 pin 本身；原子版本化安装从未被认真考虑）；
⑥ 老 checkout / Windows / 离线三类风险。

**CLAUDE SUBAGENT（CEO — strategic independence）** — 13 条 findings（C-1…C-13），实读代码 + 实跑 glob 变异验证。
最强五条：C-1（manifest 事实错误，critical）· C-2（部署窗口精确命中唯一存量 pin 仓）· C-3（`SDFLOW_HOME` 无仓级
producer，且 agent 宿主 Bash 不跨调用保留环境变量）· C-4（三条 live spec 条款未被 delta 覆盖）· C-11（encoding
排除分支**今天就已是**不可达死码，其守卫用例是恒真锚——实跑证实候选集只有权威源那一份）。

```
CEO DUAL VOICES — CONSENSUS TABLE:
═══════════════════════════════════════════════════════════════════════
  Dimension                              Claude    Codex     Consensus
  ─────────────────────────────────────  ────────  ────────  ──────────
  1. Premises valid?                     NO        NO        CONFIRMED-NO
  2. Right problem to solve?             方向对    方向对    CONFIRMED-YES(方向)
  3. Scope calibration correct?          是        否        DISAGREE
  4. Alternatives sufficiently explored? NO        NO        CONFIRMED-NO
  5. Competitive/market risks covered?   N/A       N/A       N/A(内部工具链)
  6. 6-month trajectory sound?           NO        NO        CONFIRMED-NO
═══════════════════════════════════════════════════════════════════════
5/6 有效维度中 4 项 CONFIRMED，1 项 DISAGREE（scope 是否切错）。
DISAGREE 裁决：Claude 镜对（scope 由人拍板、删除集内聚）；codex 的"应拆成 5 个 release"是加宽，
且其第 3 步（保留探测跑一版）在 global-only 解析下探测恒过，零收益。→ 归入决策登记，不改 scope。
```

### CEO Sections 1–11

**S1 架构**。依赖图（目标态）：

```
运行 checkout ──symlink──▶ ~/.claude/skills/*        （即时）
     │        ──symlink──▶ ~/.sdflow/workflow        （即时，canonical）
     └────────── cp ──────▶ ~/.sdflow/hack/*.sh      （须 setup.sh）★ 仅存的失鲜面
消费仓 openspec/workflow/ ──▶ 只剩 WORKFLOW-GUIDE.md
```
**耦合变化**：解耦 —— 消费仓不再耦合 bundle 版本。**新增单点**：canonical 成为 tools 的**唯一**来源，
而守它的 `sane()` 不查 tools ⇒ **F16**。**回滚姿态**：`git revert` + 每台机 setup + 每仓 update，
顺序不可颠倒且**无处记载** ⇒ **F28**。四路径（happy/nil/empty/error）：resolver 三码语义不变，
nil/empty 由 `sane()` 兜——但兜的面不含 tools（F16）。

**S2 错误与救援图**。本 change 净删除，新增可失败路径为零；但**既有救援的文案**被目标态改变：

| 路径 | 会出什么错 | 现行救援 | change 后是否仍正确 |
|---|---|---|---|
| `resolve-workflow.sh` exit 2 | canonical 不可达/半坏 | stderr「跑 `bash setup.sh`」 | ❌ `SDFLOW_HOME` 自定义场景指错方向（F31） |
| `stale_shadow_warnings` | 残留副本 | 「删=跟全局/留=显式 pin」 | ❌ 新文案在部署窗口内**是假的**（F3） |
| tools 自身 fail-closed | 旧工具被新 SKILL 调 | 「先跑 `sdflow-init update`」 | ❌ 该命令 change 后对 workflow 已无作用（F21） |
| fresh init | `openspec/workflow/` 不存在 | 无 | ❌ **新 GAP** — `FileNotFoundError`（F15） |

**S3 安全**。攻击面**收缩**（Eng 镜独立发现，本 change 未记）：删步①后，对不可信仓跑评审不再可能执行
该仓自带的 `openspec/workflow/tools/*.py` ⇒ 消灭一个"克隆不可信仓 + 跑评审 = 执行仓自带代码"的供应链点。
建议 proposal 正面记一笔（**F39**，正向）。无新增攻击面。

**S4 数据流与交互边界**。无用户可见交互。数据流唯一新形态 = fresh init 的 `openspec/workflow/` 创建路径（F15）。

**S5 代码质量**。删除为主，无新抽象、无 DRY 违规、无复杂度上升。
一处 DRY 正向：`resolve-workflow.sh` 内联的第三份 `RULE_MARKERS` 副本随步①消失（其守卫测试应整条删而非改写，F11）。

**S6 测试**。新增/变化的 codepath → 覆盖：

| codepath | 测试类型 | 现状 | 错实现会不会红 |
|---|---|---|---|
| resolver 忽略仓内副本 | pytest 假 HOME 真跑 bash | tasks 2.3 已列 | ✅ |
| `SDFLOW_HOME` 冻结 | 同上 | tasks 2.4 已列 | ⚠️ 只测直接调脚本，**测不到真实消费路径**（F5） |
| `copy_bundle` 只铺 GUIDE | pytest 全集断言 | tasks 3.4 已列 | ✅ |
| fresh init 目录创建 | pytest | **缺** | ❌ **F15** |
| canonical 缺 tools | pytest | **缺** | ❌ **F16** |
| `ship_gate` 腿退役 | pytest | tasks 5.3 只有正向 | ❌ **单向锚**，留着旧腿也绿（F23） |
| 6 个必红测试文件 | pytest | **tasks 未提** | ❌ **F10–F14** |

🔴 **面级结论**：tasks 用 `grep` 枚举「哪些测试依赖将被删的东西」，而 grep 对
Python path-join（`wf / "tools"`）、`full=False`、函数名下划线写法、以及**目录范围外**的文件结构性失明。
这命中 CLAUDE.md **基准 5** 的同构形态：**正解是让 pytest 自己回答**（先跑一遍看谁红），而不是用字符串匹配去猜。

**S7 性能**。N/A —— 无循环、无 IO 热点、无数据结构变化。删除只会更快（少一次 `copytree`）。

**S8 可观测性**。design 自述「无新增日志、无新增落盘产物」——成立。但**既有可观测面的真值被削弱**：
`resolve-workflow.sh --explain` 的 `source=` 是判断"resolver 换代没有"的唯一信号，而它没有被写进任何
升级验收步骤（DX 镜给出了完整 runbook，见 Phase 3.5）。

**S9 部署与灰度**。**这是本 change 最弱的一节**。Migration Plan 排的是**源码编辑顺序**，不是**部署生效顺序**；
`setup.sh` 的部分失败被降级为 `skipped[]` + exit 0；回滚顺序有要求但无载体（F28）。

**S10 长期轨迹**。技术债：净减。路径依赖：`SDFLOW_HOME` 若不修（F4/F5），会把"冻结规则版本"这个能力
悄悄变成一条**写在 spec 里但没有生产者的 SHALL**——这是最典型的文档债。
**可逆性：4/5**（几乎全是删除，`git revert` 可复原，但消费仓需重跑 update）。

**S11 设计/UX**。跳过（无 UI scope）。

---

## Phase 2 · Design Review

**跳过 —— 无 UI scope**（依据见 Phase 0 的 grep 证据）。

---

## Phase 3 · Eng Review

**CODEX SAYS（eng — architecture challenge）** — verdict: *阻断实现*。9 条，其中 6 条 high/critical：
①Migration Plan 顺序不保证运行态安全（列出 5 种可达半态）；②`sane()` 不验它即将独家提供的工具；
③**Task 3.1 直接改会让 fresh init 报 ENOENT**；④`SDFLOW_HOME` 既是冻结选择器又是安装目标，会自毁冻结；
⑤delta spec 对存量 tools 的处理自相矛盾（:68/:73/:83-85）；⑥至少四个主 spec 被违反却无 delta；
⑦tasks 的 grep 漏掉多组必红测试；⑧改 CLAUDE.md 会被 canonical snippet 覆盖回去；
⑨Task 5.3 只能证明顶层腿有效、证不出旧腿已退役。

**CLAUDE SUBAGENT（eng — independent review）** — 6 条，**实跑了 tasks 自己 prescribe 的两条 grep 并核对命中集**：
E-1（`test_resolve_models.py` 整文件 ~25 用例靠 local-pin 注入测试 bundle，两条 grep 只命中一行中文注释，**critical**）·
E-2（`test_marker_consistency.py` 连 grep 的**目录范围**都进不去）· E-3（`test_init.py` 两个测试类 +
两个整文件必红，grep 漏检过半）· E-4/E-5（maintain-scan / yq 主 spec 未声明）·
**E-6（反向核验，非缺陷）**：Migration Plan 对非 pin 仓的半态安全性**独立成立**，且本仓自身当前解析为
`global-canonical`、`openspec/workflow/` 无规则本体 ⇒ task 6.1 对本仓评审零行为影响。

```
ENG DUAL VOICES — CONSENSUS TABLE:
═══════════════════════════════════════════════════════════════════════
  Dimension                              Claude    Codex     Consensus
  ─────────────────────────────────────  ────────  ────────  ──────────
  1. Architecture sound?                 部分      NO        DISAGREE
  2. Test coverage sufficient?           NO        NO        CONFIRMED-NO
  3. Performance risks addressed?        N/A       N/A       N/A
  4. Security threats covered?           YES(+改善) YES      CONFIRMED-YES
  5. Error paths handled?                NO        NO        CONFIRMED-NO
  6. Deployment risk manageable?         部分      NO        DISAGREE
═══════════════════════════════════════════════════════════════════════
DISAGREE(1,6) 裁决：两镜差异源于**受害面口径**——codex 按"任意可达半态"论，Claude 镜按"实际受影响仓"论。
主 session 裁定：架构本身 sound（删除为主、耦合下降），**部署论证不 sound**；
受害面限定为「存量 pin 仓 × pull-without-setup 窗口」，本机 1 个仓、窗口可由纪律关闭。
⇒ 采纳 codex 的"论证需修正"，不采纳其"阻断实现/拆 5 个 release"。
```

**架构图（S1 已给）· 测试图（S6 已给）· 失败模式（S2 已给）** —— 不重复。

---

## Phase 3.5 · DX Review

**CODEX SAYS（DX — developer experience challenge）** — verdict: *不通过，实现前补齐*。7 条：
①**新告警在"已 pull、未成功 setup"状态下是假的（critical）**；②升级路径没有"机器 × 消费仓"可验证 runbook
（并给出了完整的分步 runbook）；③真正下发给消费仓的托管文档源没进任务清单；④`SDFLOW_HOME`/`--dev`
替代路径不足以让开发者照着做；⑤回滚说明缺机器级步骤且放错位置；⑥`exit 2` 固定文案在 `SDFLOW_HOME` 场景指错方向；
⑦文档与主规格残留远多于 tasks 列出的两行（含 ADR 0003/0005/0019/0036）。

**CLAUDE SUBAGENT（DX — independent review）** — 12 条（D-1…D-12）。独家发现：
D-2（`CLAUDE.md:401/404` 两处"规则副本则用之"不在 6.4 四项清单内）·
D-3（`stale_shadow_warnings` 的**第二条**告警仍含 pin 措辞，4.1/4.3 只覆盖第一条）·
**D-5（`WORKFLOW-GUIDE.md` —— 消费仓唯一常驻人读文档 —— 对 `SDFLOW_HOME` 零次提及，实测 `grep -c` = 0）**·
D-7（design 要求的"revert 说明"无任何任务产出，且 design 归档后不是应急回滚会翻的地方）·
D-8/D-9/D-10/D-11（`workflow-map.html` 5 处 + `workflow-map.md` 另 2 处 + `sdflow-spec-review.md:83` + `ROADMAP.md:34`）。

```
DX DUAL VOICES — CONSENSUS TABLE:
═══════════════════════════════════════════════════════════════════════
  Dimension                              Claude    Codex     Consensus
  ─────────────────────────────────────  ────────  ────────  ──────────
  1. 升级路径可照做?                     NO        NO        CONFIRMED-NO
  2. 命令/参数可猜?                      部分      NO        DISAGREE(轻)
  3. 错误/告警文案 actionable?           NO        NO        CONFIRMED-NO
  4. 文档可找到且完整?                   NO        NO        CONFIRMED-NO
  5. 升级/回滚路径安全?                  NO        NO        CONFIRMED-NO
  6. 开发环境无摩擦?                     NO        NO        CONFIRMED-NO
═══════════════════════════════════════════════════════════════════════
6 维中 5 项 CONFIRMED-NO。DX 是本 change 最薄的一面——这不是巧合：
change 把"人手动一步"从流程里删掉了（好事），但**它自己的落地恰恰需要人手动两步**（pull→setup、逐仓 update），
而这两步没有被写成 runbook。
```

**DX 记分卡**：升级路径 3/10 · 错误文案 3/10 · 逃生口可发现性 2/10 · 回滚 3/10 ·
开发期测试三层第②层可执行性 2/10 · 文档一致性 3/10 · `--dev` 迁移引导 1/10 · 综合 **2.4/10**。

**TTHW（这里 = 「从 merge 到我确信所有仓都对了」的时间）**：当前无 runbook ⇒ 不可估；
补上 DX codex 给的 runbook 后 ≈ 每机 3 分钟 + 每仓 2 分钟。

---

## 跨阶段主题（2+ 阶段独立命中 = 高置信信号）

| 主题 | 命中阶段 | 判定 |
|---|---|---|
| **T-A：承重论证里有事实错误（manifest 覆盖面）** | CEO(双) · Eng(codex) · DX(codex) | 三阶段五镜中四镜独立命中 ⇒ **最高置信** |
| **T-B：`SDFLOW_HOME` 不是 pin 的替代** | CEO(双) · Eng(codex) · DX(双) | 三阶段全命中，且各自给出**不同**的破法（无仓级 producer / 与安装根同名 / 不可发现） |
| **T-C：tasks 用 grep 枚举消费者 ⇒ 结构性漏检** | Eng(双) · DX(双) | 两阶段四镜；命中 CLAUDE.md 基准 5 的同构形态 |
| **T-D：未声明的主 spec 分叉（4 份）** | CEO(claude) · Eng(双) · DX(codex) | 三阶段四镜 |
| **T-E：托管块/文档面只点补不面治** | CEO(claude) · Eng(codex) · DX(双) | 三阶段四镜；且 `claude-section.md` 是**推给下游**的源 |

---

## 决策登记（autoplan 自动决策 + 需拍板 + 已裁掉）

### 自动决策（默认接受，可在设计门覆盖）

| # | 决策 | 分类 | 原则 | 理由 |
|---|---|---|---|---|
| A1 | 模式 = SELECTIVE EXPANSION | Mechanical | — | autoplan override |
| A2 | Phase 2（Design）跳过 | Mechanical | — | 无 UI scope，grep 证据在 Phase 0 |
| A3 | Phase 3.5（DX）执行 | Mechanical | — | DX scope 命中 |
| A4 | 实现路径 = APPROACH B | Taste | P1 完整性 + P5 显式 | 只修假陈述与目标态缺口，不动 scope |
| A5 | X2（扩 `sane()` 覆盖 tools/contract）**接受进 scope** | Taste | P1 | canonical 成唯一 tools 源 ⇒ 健全性面必须跟着扩，不扩=缩水 |
| A6 | X4（`--dev` tombstone 一版）**接受进 scope** | Mechanical | P5 | ~5 行；否则老用法只得 argparse generic error |
| A7 | X1（扩 capability-manifest）**DEFER 记 todo** | Taste | P2 边界 | 属 hack 链，proposal Non-Goals 已声明不动；本 change 只需不谎称它已被守 |
| A8 | X5（resolver `--help`）**DEFER 记 todo** | Mechanical | P3 | 与本 change 目标正交 |
| A9 | X6 / codex 的 `workflow-release` + 版本化原子安装 **拒绝** | Taste | P2/通则③ | 加宽；人拍的板是"去掉 pin、规则共享" |
| A10 | codex 的"拆 5 个 release 分阶段迁移"**拒绝** | Taste | P3/P6 | 其第 3 步（保留探测跑一版）在 global-only 解析下探测恒过，零收益 |
| A11 | Eng-Claude E-6 vs CEO-C2 冲突：**分治采纳** | Taste | P1 | 非 pin 仓 E-6 对；pin 仓窗口期 C-2 对（从起手硬停降为末步裸崩） |
| A12 | 「其余 tools 未验 fail-closed」前提**当场结掉** | Mechanical | 通则① | 6 个 tool 全 argparse `required=True` 无静默默认；只有 3 个读版本化契约，恰为已核那 3 个 |

### 需拍板（人在设计 HARD-GATE 决）

- **Q1｜删掉探测器后，仅存的 hack 拷贝链要不要留一条机验？**
  三镜（CEO×2、Eng-codex）独立给出同一建议：扩 `capability-manifest` 成员到安装目录全体 + 第零步无条件验一次（<10 行 + 一条 pytest）。
  **推荐：不做（A7 DEFER），但 MUST 订正 design.md:109-111 的事实错误。**
  三镜代价 —— 系统镜：做=新增一条跨 change 的机验依赖，不做=仅存链无守但**失败形态是响的**（旧 resolver 语义未变）；
  用户镜：做=窗口期得到 actionable 硬停，不做=pin 仓窗口期从"起手硬停"降为"末步裸崩"（本机 1 个仓）；
  开发循环镜：做=多一个 change 的 scope，不做=零成本。**主次：开发循环镜为主**（受害面 1 个仓 × 一个可由纪律关闭的窗口）。
- **Q2｜要不要在停铺前做「最后一次托管子树清删」（X3）？**
  既有 `spec-workflow:194` 已授权 `tools/` 整删重拷，`copy_bundle` 现在每次 update 都在 `rmtree` 它 ⇒
  "最后一次 update 删掉托管子树再停铺"完全在既有授权内，终态零死码。红线（"不自动删除"）的对象是**规则副本**，非托管子树。
  **推荐：做。** 三镜 —— 系统镜：终态零死码 vs 每仓永久留一份可执行死 `.py`；用户镜：少一次"这些文件要不要删"的判断；
  开发循环镜：`copy_bundle` 保留一次性 rmtree，代价近零（revert 后需重跑 update，而 design.md:172 **已经**要求这一步）。
  **主次：系统镜为主。** 备选（照原样）：接受每仓永久死码 + 靠告警提示。
- **Q3｜`adr/0038` 留还是删？**
  它在**本分支**新建（commit `164bb88`）、从未进 main、其 Decision（版本对比机制）从未实现，现在同一 change 内标 Superseded。
  而 tasks 6.5 已要求 0039 的取舍段涵盖被砍候选（含版本戳）⇒ 内容会重复一份。
  **推荐：删除 0038，只落 0039**，理由写进 0039 取舍段。三镜 —— 系统镜：少一份"描述从未存在过的机制"的档案；
  用户镜：未来读者不会被一条 born-superseded 的 ADR 误导；开发循环镜：少一次 supersede 记账。
  **主次：用户镜为主**（DOC-1「正文即最终态」的同构）。**备选**（保留并标 Superseded）：ADR 追加不删是常规，
  但**若保留，理由 MUST 改为「起手前提被证伪 ⇒ 决策撤销，机制从未实现」，MUST NOT 写「问题域消失」**（F32）。
- **Q4｜`SDFLOW_HOME` 这条"冻结规则版本"的能力，是修还是撤？**
  现状：spec 里写着一条**没有生产者**的 SHALL（F5），且它与 `setup.sh` 的安装根同名会自毁冻结（F4）。
  **推荐：撤 —— 把「仓级冻结规则版本」明写进 Non-Goals，delta 删掉那条 SHALL 与对应 Scenario；
  `SDFLOW_HOME` 恢复为它原本的定位（测试隔离）。** 依据：本机唯一已知的 pin 仓（05-sarvelo）实际诉求是**跟全局最新**，
  不是冻结；为一个无人要的能力写一条做不到的 SHALL，比不写更坏。
  **备选**：给它真 producer（`openspec/config.yaml` 加 `workflow-root` 键，~10 行行锚定 shell）——但那是加宽（A9 已拒）。
  三镜 —— 系统镜：撤=删一条假 SHALL；用户镜：撤=CLAUDE.md 测试三层第②层需要另写替代（见 F30/DX-D6）；
  开发循环镜：撤=零成本。**主次：系统镜为主。**

### 已裁掉（反静默压制：原始发现 + 裁掉理由，可审计）

| # | 原始发现（镜） | 裁掉理由 |
|---|---|---|
| X-1 | codex-CEO：「应改为 `~/.sdflow/releases/<id>/` + `current` 原子指针」 | 加宽。人拍板方向是"去掉 pin、规则共享"，不是建版本化发布系统。通则③ |
| X-2 | codex-CEO：「分 5 个 release staged migration，第 3 步保留探测」 | 其第 3 步在 global-only 解析下探测**恒过**（canonical tools 恒新）⇒ 多一个 release 周期换零收益。通则④ |
| X-3 | codex-CEO：「pin 有 6 条属性，`SDFLOW_HOME` 全不满足 ⇒ 应保留 pin」 | 属性对比成立（已采纳为 F5 的论据），但**结论**不采纳：删 pin 是人的明确指示（D13 证据锚）。改为"如实登记能力损失"（Q4） |
| X-4 | codex-eng：「blocking，先修 1–8 再批准」 | "阻断"是 codex 的建议不是裁决；本报告改为把 F1–F17 列为**拍板前必修**，人拍板即可放行。流程上等价、不越权 |
| X-5 | Eng-Claude E-6 的「pin 仓不算退化」 | 部分裁掉：解析**结果**确实不变，但**失败形态**从"起手 actionable 硬停"降为"末步裸崩"，是退化。保留其"非 pin 仓无影响"的正确部分（A11 分治） |
| X-6 | codex-DX：「`stale_shadow_warnings` 应实调 resolver 验 `source=global-canonical` 再宣称死件」 | 降级为备选。让告警函数去 exec 另一个脚本引入新耦合；**更简的等价解**=文案不写绝对断言（"评审一律走全局；若刚 `git pull` 还没跑 `setup.sh`，先跑 setup 再判断"）。通则④ |
| X-7 | codex-eng：「`setup.sh` 关键项 skipped 应非零退出」 | 超本 change scope（改 `setup.sh` 的失败语义是独立 change）。记 todo |

---

## Findings 汇总（39 条，供 Step 3 合并）

见 `spec-review-report.md` 的合并池；本节仅给 ID ↔ 命中镜的归属，供去重与独立率计算。

| ID | 一句话 | 严重度 | 命中镜 |
|---|---|---|---|
| F1 | design.md:109-111「hack 链由 capability-manifest 守」是事实错误（成员只 3 项，不含 resolve-workflow.sh） | critical | CEO-codex · CEO-claude · 主session |
| F2 | 部署窗口「新 SKILL × 旧 resolver」对 pin 仓从起手硬停降为末步裸崩 | high | CEO-codex · CEO-claude · eng-codex · DX-codex |
| F3 | `stale_shadow_warnings` 新文案「已无任何生效路径」在该窗口内是假的 | critical | DX-codex |
| F4 | `SDFLOW_HOME` 同时是冻结选择器与 `setup.sh` 安装根 ⇒ 跑 setup 静默解冻 | high | eng-codex |
| F5 | `SDFLOW_HOME` 无仓级 producer（SKILL 裸调用 + harness Bash 不跨调用留 env）⇒ 一条无生产者的 SHALL | high | CEO-claude · CEO-codex · DX-claude |
| F6 | `spec-workflow:871`/`:935-938` 另一条 Requirement 仍规定 contract 与 tools 同批下发 + pin Scenario，无 delta | high | CEO-claude · eng-codex · DX-codex |
| F7 | `maintain-scan/spec.md:61/63` + Scenario「仅剩 tools 判干净」与 task 4.2 冲突，无 delta | high | eng-codex · eng-claude |
| F8 | `workflow-metrics/spec.md:62` 明写 `ignore_patterns("tests")` MUST 保留，task 3.2 要删，无 delta | high | CEO-claude · eng-codex · 主session |
| F9 | `yq-yaml-operations` 的「7 个脚本」计数在 6.2 后失真，无 delta | medium | eng-claude · eng-codex · 主session |
| F10 | `test_resolve_models.py` 整文件 ~25 用例靠 local-pin 注入 bundle，两条 prescribed grep 只命中一行注释 | critical | eng-claude |
| F11 | `sdflow-maintain/tests/test_marker_consistency.py:38-48` 必红，且该**目录**不在 task 2.5 的 grep 范围 | high | eng-claude · eng-codex |
| F12 | `test_init.py` 两个测试类 + `test_init_contract_sync.py` + `test_task5_regression.py` 必红，grep 对 path-join/`full=False` 失明 | high | eng-claude · eng-codex · 主session |
| F13 | `hack/tests/test_async_branch_parity.py:464` 硬断言 `sdflow-init update` ⇒ task 1.4 必红，不在 Impact | high | CEO-claude |
| F14 | `test_maintain_scan.py:220-229` `test_stale_shadow_only_tools_clean` 与新语义冲突 | high | eng-codex |
| F15 | task 3.1 删 tools copytree ⇒ fresh init 无人创建 `openspec/workflow/` ⇒ `copy2(GUIDE)` FileNotFoundError | high | eng-codex |
| F16 | `sane()` 不校验它此后独家交付的 tools/contract ⇒ 半坏 canonical 仍 exit 0 | high | eng-codex |
| F17 | `assets/snippets/claude-section.md:71/74/89`（推给下游的托管块源）仍写"仓内副本优先"；改 CLAUDE.md 会被 update 覆盖回去 | high | eng-codex · DX-codex · DX-claude · 主session |
| F18 | `AGENTS.md:109/218/221/236` 四处未进 tasks | high | CEO-claude · DX-claude |
| F19 | `workflow-map.html`(5) + `workflow-map.md`另2 + `02-module-reference.md` + `sdflow-spec-review.md:83` + `ROADMAP.md:34` 全 stale，6.9 只点 2 个行号 | medium | DX-claude · eng-codex · DX-codex · 主session |
| F20 | ADR 0003/0005/0019/0036 核心结论仍是 local-first/tools 副本/pin，只 supersede 0038 不够 | medium | DX-codex · eng-codex |
| F21 | 「修法文案」面（`lens_metric_emit.py:104`、`resolve-models.sh:74`、`sdflow-upgrade/SKILL.md:160`、`README.md:119`）仍指向已失效的 `sdflow-init update` | medium | CEO-claude |
| F22 | task 4.1 自相矛盾：「判据函数不动」vs「检测范围扩到 tools/contract」（必须动 `RULE_MARKERS`） | medium | CEO-claude |
| F23 | task 5.3 是单向锚：留着 `tools_spec` 腿也照绿，证不出退役 | medium | eng-codex |
| F24 | tasks 1.1/1.2 错标悬空指代位置（真正的在 `code-review:204`/`spec-review:179` 的档位解析步） | medium | 主session |
| F25 | `stale_shadow_warnings` 的**第二条**告警仍含 pin 措辞，4.1/4.3 只覆盖第一条 | medium | DX-claude |
| F26 | encoding 排除分支**今天就已**不可达（`TARGET_GLOBS` 全 root-anchored），delta 称"镜像消失后才成死码"是错的；守卫用例是恒真锚 | medium | CEO-claude |
| F27 | delta spec 自相矛盾：:68/:83-85 说查看器随 tools 整删重拷清除，:73 又说不自动删 + 目标实现不再触碰 tools | medium | eng-codex |
| F28 | design 要求的「revert 说明」无任务产出，且 design 归档后不是应急回滚会翻的地方 | medium | DX-claude · DX-codex |
| F29 | `--dev` 直接从 argparse 删 ⇒ 老用法只得 generic error，无迁移引导 | medium | DX-codex |
| F30 | `WORKFLOW-GUIDE.md`（消费仓唯一常驻人读文档）0 次提及 `SDFLOW_HOME` | medium | DX-claude |
| F31 | resolver exit-2 固定文案在 `SDFLOW_HOME` 自定义场景指错方向 | medium | DX-claude · DX-codex |
| F32 | `adr/0038` 本分支新建、同 change 内 Superseded；理由应写"起手前提被证伪"而非"问题域消失" | medium | CEO-claude · 主session |
| F33 | tasks 3.3 的豁免行号 `:1125` 实为 `:1144-1146` | low | 接地镜 |
| F34 | `resolve-workflow.sh` 头部契约注释 `:5`/`:37` 未列入 2.1 更新范围 | low | DX-claude |
| F35 | 「真阳 0·假阳 1」ROI 无分母、n=1、真阳目标从未跑过评审 ⇒ 应从承重位降为旁证 | medium | CEO-codex · CEO-claude |
| F36 | 「其余 tools 未验 fail-closed」前提当场可结（已代结，见 A12） | medium | 主session（对冲 CEO-codex） |
| F37 | P0 捆绑理由「缺一即每仓每轮永久硬停」演绎不出来 | medium | CEO-claude |
| F38 | 未分析的备选：既有 spec 已授权 tools/ 整删重拷 ⇒ 可"最后一次清删再停铺"，终态零死码 | medium | CEO-claude |
| F39 | **正向**：本 change 收缩攻击面（不再执行被评审仓自带的 tools/*.py），design 未记 | low | eng-claude |

---

## Completion Summary

| 项 | 值 |
|---|---|
| 阶段 | CEO ✅ · Design ⏭️(无 UI scope) · Eng ✅ · DX ✅ |
| 双声 | 6 个声音全部真实独立跑过（codex×3 + Claude 子代理×3），零降级、零代笔 |
| 接地镜 | 1（dispatch①，与 Step1 并行），85+ 条代码事实核验，1 条不符（F33） |
| Findings | **39**（critical 3 · high 13 · medium 20 · low 3） |
| 跨阶段主题 | 5（T-A…T-E），最高置信 = T-A（四镜独立命中） |
| 自动决策 | 12（A1–A12） |
| 需拍板 | 4（Q1–Q4） |
| 已裁掉 | 7（X-1…X-7，全部附理由） |
| 方向判定 | **方向成立、范围成立、论证与落地清单不成立** |

**STATUS：DONE_WITH_CONCERNS。**
本 change 的**方向**（消灭被探测的对象而非把探测做准）经六镜独立审视后无一反对，
**范围**由人明确拍板（D13）不予改动。不成立的是两样东西：
① **承重论证里有三处可证伪的事实陈述**（F1/F3/F26），其中 F1 被四镜独立命中；
② **落地清单是点补而非面治**——tasks 用 `grep` 枚举消费者，而 grep 对 path-join、`full=False`、
目录范围外的文件结构性失明，已实证漏掉 **6 个必红测试文件与 4 份主 spec**。
