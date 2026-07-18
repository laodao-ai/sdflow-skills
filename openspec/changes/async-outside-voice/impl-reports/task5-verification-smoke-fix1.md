# Task 5 返修轮（fix1）：双轴审结论处置

> 首轮报告 = `task5-verification-smoke.md`（**保留不覆盖**，已就地加返修注 + 顶部指针）。
> 本文件是**双轴审（Spec 轴 / Standards 轴）结论的逐条处置记录**。

- **分支**：`feat/async-outside-voice`
- **执行**：2026-07-18（UTC 11:2x–11:4x）
- **提交标记**：`[impl-review-fix]`
- **未修改 change 四件套**（`proposal.md` / `design.md` / `tasks.md` / `specs/`）——设计门未失鲜。

---

## 处置总表

| # | 来源 | 结论 | 处置 | 证据 |
|---|---|---|---|---|
| 1 | Standards 轴（B8 受控对比有混淆变量） | 成立 | B8 降级 + 补主 session 反证 | §1 |
| 2 | Standards 轴（barrier 执行位未焊死） | 成立 | 两 SKILL marker 段 ⑥ 加执行位约束（fold） | §2 |
| 3 | 双轴一致（报告三条 ✅ 证据测的是另一个对象） | 成立 | 首轮报告 3/4/5 降为 ⚠️ 部分达成 | §3 |
| 4a | Spec 轴 I2（voice 反馈第 2 条漏登记） | 成立 | **T164** | §4 |
| 4b | Standards 轴 I2（canonical 分支 `continue` ⇒ 覆盖面归零） | 成立 | **直接修掉**（成本低）+ 变异验证 | §5 |
| 5 | Spec 轴 C1（R1 Scenario 1 未被实证） | 成立 | **T165** 显式登记 | §6 |

---

## 1. B8 降级：从「主 session 空闲即回收」收窄为子代理域缺陷

### 1.1 Standards 轴的指摘（**成立**）

首轮把 B8 的依据写成一组「受控对比」——**空闲 399s 被 SIGTERM vs 活跃 660s exit 0**，
并断言「**单一变量 = 活跃 / 空闲**」。该断言**不成立**：

- 首轮全部观测都发生在 **implementer 子代理上下文**内（首轮报告 §11 自己也写了这一点）；
- 在子代理里，「**转入空闲**」与「**该子代理轮次终结**」是**同一个动作、不可分辨**
  ⇒ 对比同时改变了**两个**因子，不是单一变量；
- ∴ 原证据只支持「**子代理轮次终结** ⇒ 回收」，**推不出**「主 session 空闲 ⇒ 回收」。

而 barrier 的**实际执行位正是主 session** ⇒ 原结论对本 change 的杀伤力被**高估**了。

> 这同时是首轮报告的一处**内部自相矛盾**：§9.2c 写「单一变量」，§11 写「主 session 是否同样受影响
> 未直接测过」。两句话不能同时为真。已在首轮报告 §9.2c 就地补交叉引用（见 §3）。

### 1.2 编排层的判别实验（**证伪了主 session 半边**）

在**主 session**（非子代理）起 `run_in_background` 心跳探针（每 5s 落盘），
期间**多次让出轮次转入空闲**等待双轴审子代理的完成通知：

| 指标 | 结果 |
|---|---|
| 存活 | **702s 跑满，exit 0**（`COMPLETED exit0 total=702s`） |
| 跨过 B8 的 399s 死亡点 | **是** |
| 跨过 600000ms 外层上限 | **是**（702s > 600s） |
| ppid | **全程稳定 53240，无 reparent** |
| 心跳连续性 | **141 拍无断点**（仅 2 处 6s 间隔 = 1s 调度抖动） |
| 主 session 期间是否空闲 | **是**，多次让出轮次等通知 |

原始证据：`/tmp/mainsess_probe.log`。

⇒ **「主 session 让出轮次转空闲 ⇒ 回收」被证伪。触发点是「子代理轮次终结」，不是「空闲」。**

### 1.3 落盘处置

用**本仓开发版脚本**（`sdflow-buglist/scripts/buglist.py`，非 `~/.claude/skills` 下的 symlink）核对，
B8 的 frontmatter 与详细块已改为：

- **summary**：「子代理上下文的轮次终结会回收该上下文在飞的 `run_in_background` 任务
  （主 session 让出轮次转空闲已实证不受影响：702s 跑满 exit 0）——∴ 后台任务 MUST NOT 由子代理
  派出后跨其轮次边界等待」
- **priority：P1 → P2**。理由：**不再冲击本 change 的核心机制**（barrier 执行位已焊死在主 session），
  但它**仍是真实的、必须遵守的子代理域约束**（任何在子代理内派后台任务并期望跨轮次存活的编排都会中招）
  ⇒ 不降到 P3、不关掉。
- **status：仍 VERIFIED**——收窄后的命题（子代理轮次终结 ⇒ 回收）**确有实证**（3 个在飞任务同时被回收）。
- 详细块补入：混淆变量说明、主 session 判别实验全表、根因（触发点 = 子代理轮次终结）、
  修复方案（已落地的 SKILL 焊死 + 通则），并把初记时的原始影响评估**保留、标注「其前提已被证伪」**供追溯。

**机械核验**：

```
$ /usr/bin/python3 sdflow-buglist/scripts/buglist.py scan
B8    P2 VERIFIED     harness 后台任务生命周期（子代理上下文）…
✓ frontmatter/marker/legacy 关系一致
```

> **诚实注记（工具面缺口）**：`buglist.py` 只有 `add` / `set-status` / `triage` / `scan`，
> **没有 amend 命令**——改既有条目的 `summary` / `priority` / 详细块正文只能编辑 Markdown。
> 本次即如此，且改完跑 `scan` 让脚本的一致性自检背书（frontmatter/marker/legacy 三者一致）。
> 这是 recorder 的一个真实工具缺口，登记在此，**未另开 todo**（不属本 change 面）。

---

## 2. barrier 执行位焊进两个 SKILL（fold）

Standards 轴的建议：B8 收窄后，**真正需要落地的不是改 design，而是把 barrier 的执行位钉死**——
因为「子代理轮次终结 ⇒ 回收」在**目标态下确实可达**（编排器完全可能把 collect 派给子代理做）。

**这是站点无关逻辑 ⇒ 落在 `sdflow:async-branch` marker 圈内**，两 SKILL MUST 字节相同。
加在 ⑥「正向 barrier 语义」之后，措辞中**不出现任一评审 SKILL 的文件名 / skill 名**：

> 🔴 **barrier 的执行位：MUST 在主 session，MUST NOT 委派子代理**：本 barrier 的「让出轮次等通知」
> 以及各站点的 collect，MUST 由**主 session 自己**执行——MUST NOT 把等待/取回动作交给任何子代理，
> 也 MUST NOT 在子代理内 dispatch 后由外层跨轮次接手。
> 依据（2026-07-18 实测，**两侧都有正面证据**）：子代理上下文的轮次终结会连带回收该上下文在飞的
> 后台任务——一次观测中该上下文 3 个在飞任务同时被 SIGTERM，**无 envelope、无完成通知** ⇒ 等待方
> 既拿不到退出码、也永远等不到那条通知；而主 session 让出轮次转空闲**不触发回收**——心跳探针
> 702s 跑满、exit 0、ppid 全程稳定无 reparent、并跨过 600000ms 外层上限。
> ∴ dispatch 与 collect MUST 同在主 session。

**核验**：

```
$ /usr/bin/python3 hack/check_async_branch_parity.py
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致        exit=0

$ 段内禁词扫描（sdflow-spec-review / sdflow-code-review / spec-review / code-review / SKILL.md）
sdflow-spec-review/SKILL.md 禁词命中: 无
sdflow-code-review/SKILL.md 禁词命中: 无
```

**未越界确认**：本次只在 marker 段**内**新增（additive），站点枚举 / context 构造 / reuse-guard 门控 /
declared-sites 计算**均未触碰**；`outside-voice.sh`、`anchor_lint` 合法组合矩阵**零改动**。

---

## 3. 首轮报告三条 ✅ 的诚实性返修

双轴一致指出的**同一病灶**：**证据测的是另一个对象**。三条均已就地降为 ⚠️ 部分达成，
并在对应章节写清「实测的是什么 / 缺什么才算达成」：

| 验收标准 | 实测的是什么 | 缺什么才算达成 |
|---|---|---|
| **#3 真实评审 smoke** | voice 262s，envelope `>>>0`，`reason_code="ok"` 属实 | 262s **< 300s 同步窗口** ⇒ **从未进入 R1 Scenario 1 的 WHEN**（voice 时长 > 外层同步窗口）——async **唯一要救的场景未被证**。补证 = 一次 voice 真实耗时 > 300s 的评审跑动（→ **T165**） |
| **#4 三时刻单调** | `dispatch(10:38:10) ≤ terminal(10:42:32) ≤ collect(10:43:35)` 单调属实 | collect 在终态**之后 63s** ⇒ barrier 检查时该站点**早已终态、从未处于 RUNNING 等待态**。「barrier 未早退」只是**没机会早退**，⑥ 的正向语义本轮**一次都没执行过**。补证 = 一次 collect 时站点仍 RUNNING 的跑动 |
| **#5 重叠非叠加** | **两条 voice 互相重叠**（async design-voice ∥ sync 降级 voice），span 316s < 叠加 443s | 验收标准原文是「**fan-out 墙钟** vs voice 完成时刻」，而 §9.5 自陈**本轮未跑任何 fan-out 多镜编排** ⇒ **被测对象被换掉**。实测只证明「两个 exec 可并行」，不证明「voice 与 fan-out 重叠非叠加」。补证同 T165 |

另：**§9.2c「单一变量」措辞与 §11 自陈的未知面自相矛盾** —— 已就地补交叉引用 + 本轮主 session
判别结论（首轮报告 §9.2c 的返修块），并把该段「结论（高危）」标注为**推论不再成立**。

首轮报告顶部亦加了指向本文件的指针（「以 fix1 为准，本文件保留原始记录供追溯」）。

---

## 4. Spec 轴 I2 → T164（voice 反馈第 2 条，原文已找回并落池）

首轮报告 §10 第 2 条（跨模型 voice 的 `[high]` 项，**原文**）：

> **[high]** context 路径直接拼进 shell 且未引用——路径含空格/shell 元字符时会参数拆分或执行非预期命令。

首轮的处理是「本票未处理（属 SKILL 命令形态，改它会动等值门 marker 段），建议转 buglist/todolist」——
**但从未真的记入任何池**，会随报告归档丢失。已补记：

```
T164  OPEN  基础设施  change=async-outside-voice
  module: sdflow-spec-review / sdflow-code-review 的 async 调度段 ④ 命令形态（context 路径拼接）
```

**目标态注记（写进条目 detail）**：per-run 路径含 `mktemp -d` 生成的 run 目录名，路径形态由 producer
决定——**MUST NOT** 拿「现存路径恰好没有空格」当安全依据。修法方向 = ④ 的逐字命令形态给 `<f>` 加引号
（marker 段内，两 SKILL 同改、MUST 字节相同）。

> 为何是 todo 而非 bug：现网不可达（当前 run 目录名由脚本生成、字符集受控），是**加固面**不是已发生缺陷。

---

## 5. Standards 轴 I2 → **直接修掉**（canonical 分支覆盖面归零）

### 5.1 缺陷

`sdflow-buglist/tests/test_task5_delivery_contract.py::
test_repository_legacy_corpus_matches_independent_projection_item_by_item`
在首轮 fold 修复中，对 canonical-only 文件走了 `continue`：

```python
baseline = _reference_legacy_rows(path, pool)
if baseline is None:        # canonical-only 文件：无 legacy 表可对拍，跳过
    continue
```

⇒ 该文件**完全退出独立投影对拍**。而**目标态下新建文件全是 canonical**（`buglist.py:1320`），
legacy 文件不再新增 ⇒ **本测试的覆盖面随时间归零**。
**这正是它自己诊断出的那个 dogfood 盲区的镜像**（首轮 §12.1：「存量语料的形态掩盖了目标态 producer
会产出的形态」）——修盲区的那次修复，自己又造了一个同形状的盲区。

### 5.2 修法（成本低 ⇒ 就地做掉，不 defer）

新增 `_reference_canonical_rows(path, pool)`：与 `_reference_legacy_rows` **对偶**——
legacy 的独立投影对象是 `## 状态总览` 表，canonical 的独立投影对象是 frontmatter 的 `items:` 块。
用最朴素的逐行正则 + `json.loads` **重实现**，**刻意不 import recorder 的任何解析函数**，保持
「独立对拍」语义。调用方把 `continue` 换成 canonical 分支逐字段对拍，并加尾断言：

```python
assert canonical_compared, "dogfood corpus must contain canonical items to project"
```

（该断言让「canonical 覆盖归零」变成**机械可见的红**，而不是静默滑走。）

### 5.3 变异验证（证明新断言真在看，不是空转）

在 recorder 侧注入一处变异（`effective_items.update(...)` 时把 canonical 项的 `status` 改写为
`'MUTANT'`），跑测试：

```
FAILED …::test_repository_legacy_corpus_matches_independent_projection_item_by_item
2 failed, 6 passed
```

还原后：

```
$ /usr/bin/python3 -m pytest sdflow-buglist/tests/test_task5_delivery_contract.py -q
8 passed
$ git diff --stat sdflow-buglist/scripts/buglist.py    → 无残留修改
```

⇒ **新分支对 recorder 侧的投影错误敏感**，且**未放宽任何既有断言**（legacy 分支一行未动：
`>1 个总览表`、`表体非空`、逐字段对拍全部照旧）。

---

## 6. Spec 轴 C1 → T165（R1 Scenario 1 未被实证，显式登记）

```
T165  OPEN  基础设施  change=async-outside-voice
  R1 Scenario 1 的 WHEN（voice 时长 > 外层同步窗口）在本 change 全程未被满足
  ⇒ async 的收益面未获端到端实证
```

- **性质**：真实的 **R-ID 覆盖缺口**，不是文书问题。
- **为何不阻塞合入**：fail-closed 未破、安全面完好、异常路径全部保守落 `exec-error`
  ⇒ 最坏后果是**收益未被证**，不是正确性有洞。
- **补证条件**：一次真实评审跑动中 voice 耗时 > 300s。模型推理时长无可控注入点
  ⇒ 只能等真实长 context 的评审自然产生。
- 🔴 **MUST NOT 用 fake runner 冒充本条的补证**——fake runner 走的是同一条 async 分支，
  但 WHEN 里的「voice 比同步窗口慢」只有在**真实模型**上才有意义。

---

## 7. 关于 design.md 是否需要返工（**结论：不需要，未动**）

Spec 轴曾建议「design 返工 barrier 语义」。读完 `design.md` 后的判断：**barrier 语义对主 session 成立**
（702s 判别实验），design 里关于「通知驱动 barrier / 让出轮次等通知 / timeout 只由实测 124 产生」的
论述**无一条被证伪**。真正缺的是**执行位**这一维——而它属于**指令层**（谁来执行），
落在 SKILL 的调度段更恰当（§2 已落）。

∴ **四件套一字未改**，设计门未失鲜。若 archive 阶段的复核认为 design 仍应补一句执行位的呼应，
**留给 archive 处理**（本轮不动，避免触 `ship_gate` 失鲜）。

---

## 8. 三门核验

```
$ /usr/bin/python3 -m pytest -q
1667 passed, 2 skipped            ← 与基线一致

$ /usr/bin/python3 hack/check_async_branch_parity.py
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致

$ /usr/bin/python3 hack/sync_principles.py --check
[sync_principles] ✅ 20 个投放面全部与真相源一致
```

**Compliance**：未碰 `sdflow:principles` 托管块、未碰 `outside-voice.sh`、未碰 `anchor_lint` 合法组合矩阵、
未碰 change 四件套。marker 圈内改动为 additive 且站点无关、两侧字节相同、无 SKILL 名泄漏。
