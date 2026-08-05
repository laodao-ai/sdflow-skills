# Task 1 — 双轴审 fix 轮（FIX-1 / FIX-2）

修复对象：`sdflow-roadmap/SKILL.md`。对应首轮报告 `task1-skill-rewrite.md`（不覆盖，本文件是追加的 fix 记录）。

## FIX-1（Critical，Spec 轴）：`状态：FINAL` 写入指令全文缺失

**权威依据**（改前已打开核实）：
- `openspec/changes/refactor-roadmap-internalize-deps/specs/roadmap-planning/spec.md:43` —— 「**写入时机**：B 起手写 `DRAFT`；🔴 **`FINAL` SHALL 只在收尾 checklist 四项全过之后写入**（附定稿日期），**MUST NOT 在 B 收敛时就改写**」
- `openspec/changes/refactor-roadmap-internalize-deps/design.md:120` —— 状态机图「定稿包 ◀──收尾四项过（判定点③）+ memo 置 FINAL ──」

**修法与落点**：`sdflow-roadmap/SKILL.md:517`（收尾 checklist 四项软门节，紧接第④项之后、原「软提示纳入版本控制」句之前）新增一条 SHALL 指令：

> 四项全部通过后，**SHALL** 将该包 `memo.md` 头部的 `状态：DRAFT` 改写为 `状态：FINAL`（附定稿日期）——该行是第零步重入探测唯一识别的定稿标记，四项软门通过即视为定稿。**MUST NOT 在相位 B 收敛时就提前改写**：B 收敛之后还要走相位 C 生成与 review 处置，此间若中断（如三件套只写出 1-2 个）而已置 `FINAL`，重入探测（只扫 `状态：DRAFT`）就再也认不出这个半成品包，直接击穿第零步机制自身要保护的目标。

未扩写该节其余内容，仅补这一条缺失指令。

## FIX-2（Minor，Standards 轴）：裁剪规则两处逐字重复

**修法与落点**：`sdflow-roadmap/SKILL.md:319`（相位 A 三态路由 ASCII 图注，原 :319-321 三行具体维度组合）改为一行指针句：

> 裁剪规则见下文「七维拷问与裁剪表」

只保留三态状态编号（①②③）与流转箭头，不再复述「技术重构 → ②③④⑤⑦」「新产品/新项目 → ①②④⑤⑥⑦」「商业化信号命中 → ① 加重逼问」三条具体维度组合。相位 B「七维拷问与裁剪表」（:356-361，权威源）原样保持不动。

**未处理的第三处同串命中（不在本次 finding 范围内，如实记录）**：`grep -n "②③④⑤⑦"` 改后仍有 2 处命中（`:356` 权威表 + `:332`）。`:332` 位于「路由对照表（自检基准）」节（相位 A 三态路由自检示例表，:330-338），是一行**示例行**（"帮我做一个未来半年的博客重建 roadmap……" → "状态③：相位 B 按技术重构裁剪基准跑 ②③④⑤⑦"），用于说明"给定开场白应落哪个路由状态"，不是本次 finding 指认的「逐字重复同一条规则陈述」的第二个位置（finding 明确指认的两处是 :319-320 图注 与 :358-359 表侧）。该行是否也应改为指针句不在本轮授权范围内（编排层 finding 未提及、非我自行扩权判断），故未动。如需处理需回编排层确认范围。

## 核验（亲跑，实际输出）

1. `python3 hack/sync_principles.py --check`
   ```
   [sync_principles] ✅ 20 个投放面全部与真相源一致
   ```
   退出码 = 0。托管块未被碰。

2. `grep -n "FINAL" sdflow-roadmap/SKILL.md`
   ```
   517:四项全部通过后，**SHALL** 将该包 `memo.md` 头部的 `状态：DRAFT` 改写为 `状态：FINAL`（附定稿日期）——...
   ```
   命中且在收尾 checklist 节内（四项之后、版本控制软提示之前）。

3. `grep -n "②③④⑤⑦" sdflow-roadmap/SKILL.md`
   ```
   332:| "帮我做一个未来半年的博客重建 roadmap，从选主题到迁移" | ... | 状态③：相位 B 按技术重构裁剪基准跑 ②③④⑤⑦ |
   356:| 技术重构 | ②③④⑤⑦ 为主，①⑥按需 |
   ```
   图注侧（原 :319-320）的具体维度组合已清空、改为指针句；`:356` 表侧权威源保持不动；`:332` 为自检示例表的既有内容，不在本次 finding 范围内（见上节说明），非漏改。

4. `git diff --stat` / `git diff sdflow-roadmap/SKILL.md`
   ```
    sdflow-roadmap/SKILL.md | 6 +++---
    1 file changed, 3 insertions(+), 3 deletions(-)
   ```
   两处改动均已落盘（图注三行 → 一行指针句；收尾节新增一段 FINAL 写入指令）。

## 状态

`DONE`
