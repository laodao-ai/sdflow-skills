---
name: sdflow-issues
description: >
  issues 台账的唯一 skill——owns 整个 `openspec/issues/` 台账：**两池记录 + 跨池管理**。
  **① 记 bug（缺陷）**：烧板验证、日志分析、代码审查、调试中确认了 bug 或缺陷，或用户说
  "记一下这个 bug / 这个问题记到 buglist / 标记 Bxx 已修 / 列一下还没修的 bug"→ 落
  `openspec/issues/buglist/YYYY-MM-DD-buglist.md`（每天一文件）。**② 记 todo（非缺陷）**：
  冒出"以后可以改进 / 这里能优化 / 这是个技术债 / 记个 TODO / 加进待办池"的想法，或用户说
  "记一下这个优化 / 标记 Txx 已完成 / 列一下待办"→ 落 `openspec/issues/todolist/YYYY-MM-todolist.md`
  （每月一文件）。**③ 跨池管理**：`reindex` 重建 `openspec/issues/INDEX.md` + 同步
  `openspec/issues/batches.md` 批次状态；`batch add/set-status/rename` 维护批次注册表；
  `sweep` 一键分诊本 change 未分批非终态项——主要由 `sdflow-done` 收尾自动调用。全局唯一
  ID（B=bug / T=todo）不撞号、versioned frontmatter 与 marker block 一致、终态门禁（FIXED
  必带根因+证据 / DONE 必带 change|commit）全部交脚本兜底。本 skill 自包含整套 issues 台账约定，
  是该约定的唯一真相源。**bug（坏了）vs todo（没坏但可更好）的分池判据见正文「骑墙判定」段。**
  Trigger with /sdflow-issues。
---

# sdflow-issues — issues 台账（记 bug · 记 todo · 跨池 reindex/batch/sweep）

<!-- sdflow:principles:start —— 真相源 sdflow-init/assets/hack/skill-principles.md，由 hack/sync_principles.py 注入，勿手改本区块 -->
## 🟢 三条通则（所有 sdflow skill 共用 · 违反即本次运行失败）

### ① 能查的自己查，能调研的自己调研

答案在**仓里 / 这台机器上 / 公开资料里** ⇒ **自己去拿**，查完**直接给结论**。
**MUST NOT 拿一个自己查得到的问题去占用人的注意力。**

❌「你们前端用什么测试框架？」（`package.json` 里写着）
❌「有没有 CI？」（`.github/workflows/` 看一眼）
❌「这个函数在哪调用？」（grep）

**给结论，不给过程**：「你们的集成测试是 `make integration`，我跑过了，绿」——
**而不是**「我看到 Makefile 里好像有个 integration target，你确认一下？」

### ② 不确定的方案，先调研再给推荐 —— **MUST NOT 甩开放题**

拿不准的时候，**MUST NOT 把几个选项原样丢给人**——那是**把调研的活布置给了人**。
正确动作：**先把能查的查了，带着「推荐 + 依据 + 代价 + 备选」进人门，人只负责拍板。**

> ❌「Windows 包怎么产出？（买台机器？GitHub Actions？还是 non-goal？）」——三个选项，零调研，零推荐
> ✅「**建议走 GitHub Actions 的 windows runner。** 依据：① 本仓已有 workflows ② 工具链官方支持
> ③ 公开仓免费。**代价**：签名要证书，首版只能出未签名包。**备选**：降为 non-goal（后果：Windows
> 用户没有可用产物）。**要不要这么定？**」

**⇒ ①② 合起来的三分判据**（每个问句先归一次类）：

| 答案在哪 | 动作 |
|---|---|
| 仓 / 机器 / 公开资料 | **自己查** → 给结论。**不问**（①） |
| 查得到候选与依据（选型 · 路线 · 工具） | **调研 → 推荐 + 依据 + 代价 + 备选 → 人拍板**（②） |
| **只在人脑子里**（偏好 · 踩过的坑 · 拍板权 · 组织约束） | **问** —— **注意力该全花在这里** |

> **人做的是拍板，不是替你做调研。**
> 人的注意力是唯一消耗掉就补不回来的资源：每问一个「你们用什么测试框架？」，
> 就挤掉一个「你上次被这个东西坑到是什么事？」——**而后者只有人知道。**

### ③ 以最终目标为准，MUST NOT 拿现状反驳目标

判断「该不该做 / 做到什么程度」**一律锚目标态**，**不受现有代码与设计的束缚**。

**MUST NOT** 用下面这些来论证「目标不该做 / 该缩水 / 可以妥协」：

- ❌「现在的代码不是这么写的」
- ❌「存量数据里没出现过这种情况」
- ❌「现状里这种情况很少见」
- ❌「现有设计不支持，所以改小一点」

> 迁移中「旧数据还没有新形态」是**必然**——拿它当风险基线，会把「**目标态才暴露的面**」
> 误判成「不存在」。这是**拿现状给目标松绑**。
>
> **正确的问法**：「**目标态下的 producer 会不会产出这种形态？**」
> **不是**：「现存文件里有没有？」

> 🔴 **评审类场景是本条的高发区**——评审时，**现状是唯一摆在眼前的东西**，
> 于是「它现在能跑 / 现在没出过事」极易被当成「它是对的 / 不用改」。
> **评审的基准是目标态，不是现状。**

### 🔴 传播纪律：**fan-out 子代理 / outside-voice MUST 原文带上这三条**

**子代理与 outside-voice 跑在 fresh context —— 它们看不见本文件。**

⇒ **每一个 fan-out 子代理的 prompt、每一份 outside-voice 的 context，MUST 把本区块
（`sdflow:principles` 从 `start` 到 `end`）原文整段复制进去。**
**MUST NOT 转述、MUST NOT 摘要、MUST NOT 只给指针。**

> **漏带的后果是确定的，不是概率的**：一个冷上下文的镜子，眼前只有现状，
> 它**必然**把「现在能跑」当成「是对的」，把「存量里没见过」当成「不会发生」——
> 而这正是 ③ 要杀的病。**冷是它的价值，也正是它的破绽。**

<!-- sdflow:principles:end -->

本 skill owns 整个 `openspec/issues/` 台账，覆盖**两池记录 + 跨池管理**，是这套约定的**唯一真相源**
（不依赖任何外部 rule 文件）。台账被当**一个概念**：一条债务 item、三正交字段（源change/批次/status）、
status 词表按 pool 各异——即「一个东西 + 一个 pool 参数」（`CONTEXT.md`「三维度分家」）。

| 池 / 面 | 管什么 | 脚本入口 |
|---|---|---|
| **bug 池** | 已确认缺陷的 add/scan/set-status/triage | `scripts/buglist.py`（前缀 `B`，每天一文件） |
| **todo 池** | 优化/技术债/改进想法的 add/scan/set-status/triage | `scripts/todolist.py`（前缀 `T`，每月一文件） |
| **跨两池** | `reindex`（生成 `issues/INDEX.md`）+ `batch`（`issues/batches.md` 注册表）+ `sweep`（一键分诊封装，非原子） | `scripts/issues.py` |

三个脚本同在 `sdflow-issues/scripts/` 下、随本 skill 整目录 symlink 分发；`issues.py` 用**同目录**
路径 spawn `buglist.py`/`todolist.py` 子进程（`os.path.join(SCRIPT_DIR, ...)`，与 `--root` 无关）。

> **为什么要脚本**：两池 ID 语义唯一、frontmatter ↔ marker 关系一致、终态门禁（FIXED 必带根因+证据 /
> DONE 必带 change|commit）——这些手工做极易出错（撞号、破坏 shared envelope、只写完成没写为什么）。
> 脚本把它们变成确定性操作，模型省下来的注意力用在真正需要判断的地方：这是不是真 bug、现象 vs 根因、
> 定几级、这值不值得记、归哪个类型、**落 bug 池还是 todo 池**。

`python scripts/{buglist,todolist,issues}.py --help` 查各命令。

---

## 🔀 骑墙判定：bug（坏了）还是 todo（没坏但可更好）？

**触发面只有一个 `/sdflow-issues`。** 落哪个池不再由「选哪个 skill 触发」在门口决定，而由模型在 skill
内按下面的判据判定 pool，再走对应脚本入口。

**核心判据 =「坏了没」**：

| 问 | 是 → **bug 池**（`buglist.py`，前缀 B） | 否 → **todo 池**（`todolist.py`，前缀 T） |
|---|---|---|
| 存在偏离预期的**可观察故障 / 错误行为**吗？ | 有明确故障：崩溃、数据错、逻辑走错、契约违背、性能**违反 SLA/预期的可测退化** | 当前行为**符合预期**，只是"能更好/更快/更清晰"——优化、技术债、增强 |
| 需要**根因 + 修复**吗？ | 需要（现象 vs 根因分开，定优先级 P0–P4） | 不需要（按价值/成本排 type，不紧迫） |

**骑墙举例**（AD-6 点名的高误判点）：

- 「**性能退化**」——若是相对基线**可观测的退化**且违反性能预期/SLA（本来达标、现在不达标）→ **bug**
  （坏了）；若只是"还能更快"、当前速度本就在预期内 → **todo**（`type=性能优化`，没坏但可更好）。
- 「日志不够」——服务本身工作正常，只是想更好诊断 → **todo**（`type=可观测性`）；若因为缺日志导致
  某故障**无法定位/复现是已知障碍** → 该故障本身是 **bug**，加日志是它的 fix 项。
- 「命名乱 / 结构该重构」→ **todo**（`type=代码质量`），除非当前命名已导致**实际调用错误** → bug。
- 「spec 与 impl 不一致」→ 看**哪边错**：impl 违背 spec 契约 → **bug**（P3）；spec 只是可写得更清楚、
  impl 行为正确 → **todo**。

> 知道 pool 的**调用方**（如 `sdflow-done`、自动化脚本）直接走**显式入口**（`buglist.py add` /
> `todolist.py add`），不经 NL 路由、不受本判据影响。骑墙判定只用于**人/模型从自然语言起手**记录时。

### ⚠️ 已知代价：误判落错池不可机械恢复

触发面塌缩为一个后，分池由模型 NL 判定承担。**残余缺口（记为已知代价，非阻断）**：骑墙输入被误判 →
item 落错池，拿错前缀（B↔T）/文件粒度（日↔月）/schema（`priority`↔`type`）/状态词表；而 CLI **无
`move`/`reclassify` 命令**（此缺口 pre-merge 即存在，非本合并新引入）→ 纠正须**手删 + 重 add**，会
**丢原 ID 与历史**。降误判率靠上面的判据 + 举例；跨池 `move --to-pool` 搬运命令为 nice-to-have，
显式 defer（换前缀+粒度文件+schema+保 provenance，将来另开）。

---

## 何时用 / 何时不用

- ✅ **发现即记录**：烧板、日志分析、代码审查、调试中确认 bug → 当天落 bug 池；冒出优化/技术债/
  改进想法 → 当月落 todo 池。别靠记忆。
- ✅ **状态跟踪**：被某 change 包入（PROPOSED）、修完/做完（FIXED / DONE）、决定不修/不做
  （WONTFIX / WONTDO）→ 回写。
- ✅ **盘点**：列未闭合项、按优先级/类型/状态筛、检查一致性。
- ✅ **跨池管理 & sweep**：重建 INDEX、建/推进/改名批次、盘点批次完成度 → `issues.py`；`sdflow-done`
  收尾自动跑 `sweep`+`reindex`。
- ⚠️ **change review 阶段发现的问题/改进默认不进台账**：直接在该 change 内修掉 / 处理，或写进它的
  deferred 列表。只有用户明确说"这个也记一笔"时才记——记前先确认，避免噪音。
- ⚠️ **不要手改 `issues/INDEX.md`**：首行固定 `<!-- GENERATED by issues.py reindex — DO NOT EDIT -->`
  banner，全量确定性重建（禁读旧 INDEX，D3），手改内容不会被合并、只会在下次 reindex 时被无条件覆盖。

---

## 记录 / 回写 / 扫描

### bug 池：记录新 bug（`buglist.py add`）

先判断（模型的活）：这是不是真 bug（见骑墙判定）？**现象**（外在可观察）与**根因**（代码层因果）分开；
定**优先级**。然后把结构化内容交给脚本——它负责定位今日文件（缺则建目录+头部）、在仓级 snapshot lock
内扫描两池并分配 ID，把 canonical frontmatter item + marker block 一次写齐。

```bash
echo '{
  "module": "data_publish.c:120",
  "summary": "DATA/LOG envelope type 字段为空",
  "priority": "P1",
  "status": "OPEN",
  "phenomenon": "服务端收到的 envelope.type 恒为空字符串",
  "rootcause": "publish 前未从 ctx 取 type，结构体零值直接发出",
  "fix": ["发送前用 ctx->msg_type 填充 envelope.type", "加单测覆盖三种 type"],
  "impact": "所有 DATA/LOG 上行；server 侧无法路由",
  "source": "0628 烧板日志",
  "change": "add-envelope-type",
  "doc": ["changes/add-envelope-type/design.md", "rules/envelope-format.md"]
}' | python scripts/buglist.py add
```

- 输入走 **stdin 或 `--json <file>`**（多行内容用 JSON 天然安全）。
- 必填：`module` / `summary` / `priority` / `phenomenon`。`rootcause`/`fix`/`impact` 缺省留占位。
- `source` 只在**新建当日文件**时用作头部「来源」。
- 不传 `id` 则自动分配（默认前缀 `B`，要 `A`/其它分类用 `--prefix A`）。
- **时间**自动记录当前 `HH:MM`（当日文件已含日期），需要回填历史用 `--time HH:MM` 覆盖。
- **摘要 vs 标题**：frontmatter 的 `summary` 讲现象（不是根因），可含 `|`、换行、Unicode；详细块标题默认
  取其单行投影，要不同可加 `"title"`。额外字段（触发路径/时序/前置条件/验证方式）放 `"optional": {...}`。
- 脚本回 `{"id","file","status","time","change"}`——把分到的 ID 告诉用户。

### todo 池：记录新 TODO（`todolist.py add`）

先判断（模型的活）：这值得记吗（见骑墙判定，确认是"没坏但可更好"而非 bug）？归哪个**类型**？需不需要
写动机/思路？然后交给脚本——它定位当月文件（缺则建）、在仓级 snapshot lock 内扫描两池并分配 ID、写
canonical frontmatter item；**只有给了动机/思路/备注（或显式 `doc`）才建 marker block**；轻量项只有
frontmatter item，不建 prose block。

```bash
# 简单项：只写一个 frontmatter item，不建 prose block
echo '{"module":"meter_collect.c","summary":"温度采样改 DMA 批量读取","type":"性能优化","project":"smartrelay-4g"}' \
  | python scripts/todolist.py add

# 需要说明的项：带动机/思路 → 自动建详细块
echo '{
  "module":"meter_collect.c","summary":"温度采样改 DMA 批量读取","type":"性能优化",
  "motivation":"当前 4 步逐次 ADC 读取 ~1.2s，DMA 可降至 <100ms",
  "approach":"配置 ADC DMA 连续转换，一次读 4 通道",
  "note":"需确认 ML307C ADC 是否支持 DMA"
}' | python scripts/todolist.py add
```

- 输入走 **stdin 或 `--json <file>`**。必填：`module` / `summary`（描述）/ `type`。
- **类型**（受控词表）：`性能优化` `可观测性` `代码质量` `功能增强` `基础设施`。
- 可选块字段：`motivation`（动机）/ `approach`（思路）/ `note`（备注）——任一存在才建块。
- `project` 只在**新建当月文件**时写入头部。不传 `id` 则自动分配（默认前缀 `T`）。
- **时间**自动记录 `YYYY-MM-DD HH:MM`（当月文件不含日，需完整时间戳定位是哪天），回填历史用 `--time` 覆盖。
- **显式**传 `doc` 会强制建块（哪怕没写动机/思路/备注），否则这行没地方放；轻量项即便 `change` 恰好探测到
  文档，仍只写 frontmatter item、不建块——不让随手记的轻量 TODO 被悄悄升级成带块的项。

### 两池共有的字段

- **关联Change**（`change`，可选）：不传时脚本自动探测——优先取 `openspec/changes/` 下唯一未归档目录名，
  找不到再退化到当前 git branch 名（去 `feat/`/`fix/` 前缀）；**多个 change 并行时脚本探测不到，模型应
  结合当前 session 上下文判断在哪个 change 里冒出来的，显式传 `change` 覆盖**。
- **关联文档**（`doc`，可选，string 或 list[string]）：填对格式后 review 工具里能直接点开。路径不带
  `openspec/` 前缀会自动补上；写进详细块的 **关联文档** 行（多路径用「、」分隔）。路径不存在只警告不阻断。
  不传时若能从 `change` 探测到 `design.md`/`proposal.md`（含已归档的 `changes/archive/*-{change}/`）会
  尝试自动带上。

### 回写状态（`set-status`）

状态变更只更新 frontmatter 机器索引，并在 marker block **追加一条人读历史**（不写可变状态副本）。legacy
item 首次触碰时 same-file promotion 为 overlay，旧表 bytes 不变。带门禁：

```bash
# bug 池
python scripts/buglist.py set-status --id B17 --to FIXED --evidence "commit a1b2c3d"
python scripts/buglist.py set-status --id B4  --to WONTFIX --reason "硬件限制，3.0 板子才有"
# todo 池
python scripts/todolist.py set-status --id T1 --to DONE   --evidence "commit a1b2c3d"
python scripts/todolist.py set-status --id T7 --to WONTDO --reason "ROI 太低，硬件下一版才支持"
```

- **bug FIXED 门禁**：必须 `--evidence`（commit/change）且详细块**根因已补全**（非空、非 `<...>` 占位）——
  挡住"只写已修、没写为什么"；根因还空先补根因再回写。**bug WONTFIX 门禁**：必须 `--reason`。
- **todo DONE 门禁**：必须 `--evidence`（关联 change 名或 commit）——挡住"只标完成、不留线索"。
  **todo WONTDO 门禁**：必须 `--reason`。
- 状态码：bug = `OPEN VERIFIED PROPOSED IN_PROGRESS FIXED WONTFIX BLOCKED`；todo = `OPEN PROPOSED DONE WONTDO`。

### 扫描 / 盘点（`scan`）

```bash
python scripts/buglist.py scan --status OPEN      # bug，只看未修（默认按优先级排）
python scripts/todolist.py scan --type 性能优化    # todo，按类型筛（默认按状态排）
python scripts/buglist.py scan --json             # 机器可读（两池皆有 --json）
```

末尾自动做 **frontmatter/marker/未提升 legacy 表**关系自检。盘点或交接前先跑一次。

---

## 跨池：`reindex` / `batch` / `sweep`（`issues.py`）

这些命令**独占**跨 bug+todo 两池、owns `issues/INDEX.md` + `issues/batches.md`。安装后可用绝对路径调：

### 1. `reindex`——重建 INDEX + 同步批次状态

```bash
python3 ~/.claude/skills/sdflow-issues/scripts/issues.py --root . reindex
```

流程：`read_pool`（子进程调**同目录** `buglist.py scan --json` + `todolist.py scan --json` join 两池，
join 前先做 D9 跨池 ID 冲突检测，冲突即报错中止、不生成半截 INDEX）→ 纯函数式重建 `issues/INDEX.md`
（open 项按批次分组的物化板 + 已闭合项计数摘要，幂等——相同输入两次跑逐字节输出相同）→ 原子写落盘 →
同步 `issues/batches.md` 的 `成员:`/`状态:` 生成行（D1 完成判据、Q3 不越权纠正、Q2 orphan 报警）。

### 2. `batch add / set-status / rename`——批次注册表操作

```bash
# 新建批次（状态=PLANNED，成员空占位；人写字段缺省留占位符）
python3 ~/.claude/skills/sdflow-issues/scripts/issues.py --root . batch add {change_name} \
  --title "清理项标题" --优先级 P1 --计划 "一句范围"

# 批次进入实施阶段（人工权限，reindex 只会把它推到 DONE，不会推 PLANNED→IN_PROGRESS）
python3 ~/.claude/skills/sdflow-issues/scripts/issues.py --root . batch set-status {change_name} IN_PROGRESS

# 批次改名（同步 bug+todo 两池所有该批次成员的批次 tag；不做跨 change 合并；
# 任一阶段失败均 non-zero，修正故障后重跑原命令）
python3 ~/.claude/skills/sdflow-issues/scripts/issues.py --root . batch rename {old_key} {new_key}
```

- `batch add` 对已存在的 key 是**报错**而非静默 no-op（`_die`）——add 是"新建"语义，撞号多半是误操作；
  需要 ensure 语义的自动化调用方必须显式传 `--if-exists skip`。`sweep` 固定使用该选项，撞号时由脚本按
  幂等成功处理，调用方不得解析错误文案猜测结果。
- `batch rename` 刻意不复用 per-type 脚本的 `triage` 子命令改批次列，因为 `triage` 会顺带把"未分诊
  开放态"状态推进到 `PROPOSED`——`rename` 只该改标签本身，不该有这个副作用。
- `batch rename` 先在 registry 写 target + machine-owned `重命名自: old` provenance，再用每池一次
  direct-bytes snapshot retag dated items，最后由同一更新后 snapshot 写 INDEX/batches。任一阶段未收敛均
  non-zero，并报告阶段、原始命令与"重跑原命令"；同一命令可从全 old、混合或全 new 盘面继续。无 provenance
  的 `old missing/new exists` 仍 fail-closed，不吸收 orphan。

### 3. `sweep --change X`——一键分诊本 change 未分批非终态项（sdflow-done §2.1 的一行封装）

```bash
python3 ~/.claude/skills/sdflow-issues/scripts/issues.py --root . sweep --change {change_name}
```

语义：把「源 == X ∧ 非终态 ∧ 批次空」的 bug/todo 一次性归入批次 X——即 `sdflow-done` §2.1 原手写 4 步
循环（scan 两池 → 逐项 triage → batch add → reindex）的一键封装，内部全走子进程 CLI（不直调 `cmd_*`），
对外只暴露一个单一入口（**非原子**——见下）。

- **扫描口径 `--open-ungrouped`**：等价于 `scan --change X --open-ungrouped --json`——非终态（非
  CLOSED/VERIFIED 等终态）∧ 批次空，**不是** `--status OPEN`（后者漏非 OPEN 的非终态项、也不过滤批次空）。
- **幂等**：`batch add` 内部固定带 `--if-exists skip` + `triage` 对已 PROPOSED/已终态项 no-op +
  `reindex` 确定性重建——同一 `--change` 连跑多次，第二次 exit 0 且盘面无净变化。
- **空 change 入口守卫**：`--change` 为空/纯空白，或未过 `_reject_batch_key_unsafe`（含 `|`/换行/` — `/
  首尾空白）→ 先于任何写盘 `_die`，防止把源 = `""` 的孤儿项误纳进空批次。
- **非原子、fail-closed、重跑收敛**：任一子步非零退出即整体非零退出，stderr 报明失败步 + 失败点位（第 i 项/
  哪个 pool/已 tag 的 id 列表）；已 tag 项因「批次空」过滤在重跑时天然被排除，故半途失败后**直接重跑同一条
  命令即可收敛**，不需手工回滚。reindex 失败也判整体失败；INDEX 未刷新即闭环未完成。
- **exclusive owner + participant 委派**：`sweep` 顶层持有仓级 snapshot lock，scan/triage/batch-add/reindex
  子命令只沿 allowlist delegation chain 作为 participant 进入同一锁域；其他 cooperative recorder 命令在整个
  写窗口 fail-closed 冲突退出。token 不是安全边界，非 cooperative writer 仍属明确不承诺的 TOCTOU 边界。
- 孤儿项（源 = `""`）不归 sweep 管，仍由独立的 `scan --open-ungrouped` 兜底工作流处理。

---

## 约定速查（本 skill 即真相源）

> issues 结构标准（目录/schema/状态/命令/sweep/D9）的**唯一真相源**就是本段——不另起 rules 文件。

### 目录结构

- **bug 池**：`openspec/issues/buglist/YYYY-MM-DD-buglist.md`，每天一个，当天所有 bug 追加进去，不拆分。
- **todo 池**：`openspec/issues/todolist/YYYY-MM-todolist.md`，每月一个，当月所有 TODO 追加进去。
- 过渡期兼容旧路径 `openspec/buglists/`·`openspec/todolists/`——`next-id`/`scan`/`set-status`/`triage`
  全部 **dual-read**（新旧两目录都扫）；**新记录只写新路径的 canonical frontmatter**。自定义 prefix 的
  `next-id`/自动 add/显式 ID 查重都在同一仓级 exclusive snapshot lock 内读取 bug+todo 两池全集。跨新旧
  路径撞同一 ID 会在 `next-id` 时打 WARNING，提示尽快迁移旧数据。

**跨两池共享文件**（owner = `scripts/issues.py`）：

- `openspec/issues/INDEX.md`——`issues.py reindex` 从 bug+todo 两池全部 dated 文件重建，首行固定 banner
  `<!-- GENERATED by issues.py reindex — DO NOT EDIT -->`。**只生成、禁手改**——手改内容会在下次 reindex
  时被无条件覆盖，不做任何合并。
- `openspec/issues/batches.md`——批次注册表，**半手维护**（`状态:`/`成员:` 两条生成行归脚本管，`优先级:`/
  `计划:` 等是人写行，reindex/batch 绝不覆写人写行），格式契约见下方「batches.md 字段级 grammar」。

### 三维度 schema

每条 item 三个独立维度，互不覆盖：

| 维度 | 落点 | 可变性 | 含义 |
|---|---|---|---|
| 源change（关联Change） | frontmatter item `change` | **不可变**（provenance） | 在哪个 change 里发现/冒出来的 |
| 批次 | frontmatter item `batch` | 可变 | 被哪个「清理 change」包走去修/做（批次 key = 清理 change 名） |
| status | frontmatter item `status` | 生命周期 | 见下方状态词表；marker prose 只追加历史，不是状态真相源 |

新写结构是 shared frontmatter envelope 下唯一 `sdflow-issues` namespace（短键 `schema/pool/mode/items`）；
新文件 `mode=canonical`。历史 8 列表永久只读，活跃 legacy item 首次 mutation 以 `mode=overlay` shadow 旧
row，旧表与旧 block 内部 bytes 不改。reader 在 namespace 在场但损坏时 fail-closed，只有 namespace 不存在
才回退 legacy parser。

### 特定字段（按 pool 各异）

**bug 优先级**：

| 级 | 定义 |
|----|------|
| P0 | 阻塞交付 / 不可用（Silent Reset、数据全丢） |
| P1 | 严重功能缺陷（核心异常、栈溢出风险、数据错误） |
| P2 | 中等 / 有绕过（精度偏差、需服务端配合） |
| P3 | 低 / 已知豁免（spec/impl 不一致、编译警告） |
| P4 | hygiene（残留、风格、纯清理） |

**todo 类型标签**（受控词表）：`性能优化`（提速/降资源） `可观测性`（日志/metrics/诊断） `代码质量`
（重构/命名/结构） `功能增强`（新能力/扩展） `基础设施`（构建/CI/工具链）。

### 状态词表 + 终态集（按 pool 各异）

| pool | 状态码 | 终态集 |
|---|---|---|
| bug | `OPEN`(已识别未排期) `VERIFIED`(复现确认真 bug) `PROPOSED`(被 change 包入) `IN_PROGRESS`(实现中) `FIXED`(commit+验证) `WONTFIX`(评估不修) `BLOCKED`(等外部依赖) | `{FIXED, WONTFIX}` |
| todo | `OPEN`(已记录未排期) `PROPOSED`(被 change 包入) `DONE`(已完成) `WONTDO`(评估放弃) | `{DONE, WONTDO}` |

进入终态即"这条债/待办不再挂着"（WONTFIX/WONTDO 是"决定不修/不做"的合法闭合，和 FIXED/DONE 一样从
INDEX 的 open 板消失）。**批次完成判据**：批次**成员数 ≥ 1** 且**全部成员 ∈ 该池终态集** → `issues.py
reindex` 把该批次同步判/标 `DONE`；reindex 的自动判据**不会**把 0 成员批次判/标为 `DONE`（保持 `PLANNED`，
防"空集全称为真"的 vacuous-truth 假 DONE）——但人可用 `batch set-status` 手动标任意状态（含 0 成员标
`DONE`），reindex 不越权纠正，只在状态与成员终态不一致时追加 `⚠️ 不一致` 警告。**两池终态集不同，reindex
按各自 pool 判定，不硬编码字面 `"DONE"`**（对 bug 池根本不成立）。

### 命令面

**per-pool**（`buglist.py` 只管 bug 池、`todolist.py` 只管 todo 池，互不碰对方）：

`add` / `scan`（bug：`--status`/`--change`/`--批次`/`--open-ungrouped`；todo：另有 `--type`） /
`set-status` / `triage`（赋批次 + 把「未分诊开放态」（即 `OPEN`）推进到 `PROPOSED`，幂等——已
`PROPOSED`/已终态都 no-op，不倒退状态） / `next-id`。全部命令 dual-read 新旧两目录。

**跨两池**（`issues.py`，独占跨 bug+todo 的命令）：`reindex` / `batch add|set-status|rename` / `sweep`
（详见上方「跨池」段）。

### sweep 协议（每个 change 收尾时）

`sdflow-done` 生成 hand-off 那一步跑 sweep：以 **源==本change ∧ status 非终态 ∧ 批次==空** 为界，只分诊
**本 change 自己新增**的未分诊 OPEN 项——显式传 `--change {本change}`（不靠 `detect_change` 猜，从源头减少
假孤儿）→ `triage` 分诊入批次 → `batches.md` 登记 `PLANNED` → 末尾跑 `issues.py reindex` 刷新 INDEX →
hand-off 引用这次 sweep 结果。已在各自 change 分诊过的老 OPEN 项不被重诊；**源为空的孤儿项不归本次 sweep**，
交独立的通用清理流程兜底（`scan --open-ungrouped` → `triage` → 另开 cleanup change）。

### batches.md 字段级 grammar（半手维护，跨两池）

```
### {批次key} — {标题}
状态: PLANNED            ← 生成行（issues.py reindex / batch set-status 维护）
成员: (生成) B1, T2      ← 生成行（reindex 拿 item 池当 ground truth 回填）
优先级: P1               ← 人写行（reindex/batch 绝不覆写）
计划: 一句范围           ← 人写行（同上）
```

`状态:`/`成员:` 两个固定前缀是**生成行**；其余（含条目里额外追加的字段）都是**人写行**。reindex **只精确
patch 生成行**，绝不覆写人写行；发现「人写 `状态: DONE` 但成员未全进终态集」不会越权纠正这个值，只在条目尾
追加一行 `⚠️ 不一致` 警告，等人工核实后自己用 `batch set-status` 改回或补完成员状态。批次 tag 指向
`batches.md` 里不存在的 key（orphan）也只报警、不静默生成 ghost 条目。批次生命周期 `PLANNED → IN_PROGRESS
→ DONE`（`PLANNED→IN_PROGRESS` 由人在真正开 cleanup change 时手动 `set-status`；`→DONE` 通常由 reindex
按完成判据被动同步）。

### ID 两池语义唯一〔ADR-0025 / D9〕

默认 bug=`B`、todo=`T`，公开的单字母自定义 `--prefix` 保留。ID semantic key 是 `(uppercase ASCII prefix,
decimal integer)` 且**不含 pool**，因此 `A007`/`A7` 及 bug/todo 的 `A7` 均冲突。`next-id`、自动 add 与
显式 ID 查重必须在同一 snapshot lock 内读两池全集；`reindex` 仍作 fail-closed 防护网（join 前跨池 ID 冲突
检测），但不承担事后修复。

### 铁律（脚本已替你守住大半）

① ID 在 bug+todo 两池语义全局唯一；② frontmatter 是机器真相源，legacy 表永久只读；③ 状态追加式、不删历史
（脚本追加历史行）；④ 终态门禁——bug FIXED 必带根因+证据、todo DONE 必带关联 change/commit（脚本门禁）；
⑤ 机器索引只写 frontmatter，marker prose 不反解析；⑥ `issues/INDEX.md` 只生成禁手改（issues.py 兜底无
条件覆盖重建）；⑦ 轻量优先——todo 简单项只写 frontmatter item，要说明动机/思路才建块；⑧ 实施走 change——
台账只是记录/收集池，真做时通过 OpenSpec change 落地，不在此直接改代码。

---

## `--root` 与 git 根

三个脚本（`buglist.py`/`todolist.py`/`issues.py`）统一探测 **git 仓库根**（`git rev-parse --show-toplevel`），
非 git 仓库时退化为 `os.path.abspath(--root)`——`--root` 可指向仓库内任意子目录，不要求必须是仓库根本身；
`reindex`/`batch add/set-status/rename` 等命令都会先 resolve 到 git 根再拼 `openspec/issues/...` 路径，且
`read_pool` 调 `buglist.py`/`todolist.py` 子进程时会把这个已 resolve 的根通过 `--root` 传下去，保证三脚本
落到同一目录、不会因调用时的 cwd/子目录不同而把文件散落到不同位置。

## 注意

- **并发与耐久边界**：三 recorder 的权威读/写共用 `openspec/issues/.recorder.lock` exclusive snapshot lock；
  owner/participant token 只协调 cooperative CLI，不是安全边界。支持本地 POSIX 自动门与 Windows 本地盘 smoke；
  network FS、完整 power-loss durability 及非 cooperative writer 的 TOCTOU 不承诺。process crash 留锁时先停该
  repo 全部 recorder，再删除错误中给出的精确 lock path，随后重跑原命令（break-glass）；不提供 TTL/自动偷锁。
- 一个 bug/想法一条 ID；后续进展走 `set-status`，不要新开 ID。
- 模型的核心价值在**判断**：这是不是真 bug、落哪个池、定几级/归哪类、该不该建/改批次——命令本身是确定性
  操作，交给脚本。拒绝把 review 期琐碎问题、还没确认的猜测、太琐碎/重复的想法记进台账（噪音比漏记更难清理）。
