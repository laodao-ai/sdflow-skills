---
name: sdflow-todolist
description: >
  自动把优化想法 / 技术债 / 改进点等**非缺陷**项记录进 openspec/issues/todolist/YYYY-MM-todolist.md
  （每月一文件，全局唯一 T-ID），并支持状态回写（OPEN→PROPOSED→DONE…）与扫描列表。**只要冒出一个
  "以后可以改进 / 这里能优化 / 这是个技术债 / 记个 TODO / 加进待办池"的想法，或用户说"记一下这个优化、
  这个改进想法存一下、标记 Txx 已完成、列一下待办"，就用本 skill**——别手动拼 Markdown，交给脚本保证
  T-ID 不撞号、轻量项只写一个 frontmatter item、DONE 必带关联 change/commit。注意：这是攒"没坏但可以更好"的池子，
  已确认的 bug（坏了的东西）该用 sdflow-buglist 而不是本 skill。本 skill 自包含整套 todolist 约定，
  是该约定的唯一真相源。Trigger with /sdflow-todolist。
---

# sdflow-todolist — 自动记录 / 回写 / 扫描 todolist

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

把"冒出改进想法 → 落进收集池 → 实施时回写"这条易丢的流程交给脚本兜底。
todolist 是**优化/技术债/改进**的收集池（没坏但能更好），实施时再走 OpenSpec change 落地。
**本 skill 自包含整套约定**（不依赖任何外部 rule）。

> **和 buglist 的分工**：buglist 记**已确认的缺陷**（坏了，需根因+修复）；todolist 记**改进想法**
> （没坏，按价值/成本排，不紧迫）。发现的是 bug → 用 `sdflow-buglist`；是"可以更好" → 用本 skill。

> **为什么要脚本**：两池 ID 语义唯一、frontmatter↔marker 关系一致、DONE 必带关联 change——手工易错。脚本兜住这些，
> 模型专注判断：这值不值得记、归哪个类型、要不要写动机/思路。

脚本：[scripts/todolist.py](scripts/todolist.py)（`python scripts/todolist.py --help`）。

---

## 何时用 / 何时不用

- ✅ **随手记录**：发现可优化点、技术债、想做的增强 → 当月落池，别靠记忆。
- ✅ **状态跟踪**：某项被 change 包入（PROPOSED）、做完（DONE）、决定不做（WONTDO）→ 回写。
- ✅ **盘点**：列出还没做的 TODO、按类型筛、检查一致性。
- ⚠️ **change review 阶段冒出的改进默认不进 todolist**：直接在该 change 内处理或写进它的 deferred 列表。
  只有用户明确说"这个也存一笔"才记——记前先确认。
- ⚠️ **已确认的 bug 不要记这里** → 用 `sdflow-buglist`。

## 三件事怎么做

### 1. 记录新 TODO（add）

先判断（模型的活）：这值得记吗？归哪个**类型**？需不需要写动机/思路？然后交给脚本——
它定位当月文件（缺则建）、在仓级 snapshot lock 内扫描两池并分配 ID、写 canonical frontmatter item；
**只有给了动机/思路/备注才建 marker block**；轻量项只有 frontmatter item，不建 prose block。

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
- **时间**自动记录 `YYYY-MM-DD HH:MM`（当月文件不含日，需完整时间戳才能定位是哪天），
  需要回填历史记录时用 `--time` 覆盖。
- **关联Change**（`change` 字段，可选）：不传时脚本自动探测——优先取 `openspec/changes/` 下唯一未归档
  目录名，找不到再退化到当前 git branch 名（去掉 `feat/`/`fix/` 等前缀）；**多个 change 并行时脚本
  探测不到，这时模型应结合当前 session 上下文判断这个 TODO 是在哪个 change 里冒出来的，显式传
  `change` 字段覆盖**。轻量项的字段同样进入 frontmatter，不复制到 prose。
- **关联文档**（`doc` 字段，可选，string 或 list[string]）：记录时如果这个改进想法关联某个 openspec
  文档（design/proposal/rule 等），尽量把该文档路径填进 `doc` 字段——填对格式后在 review 工具里能直接
  点开。路径不带 `openspec/` 前缀也会被自动补上；写进详细块的 **关联文档** 行（多个路径用「、」分隔）。
  **显式**传 `doc` 会强制建块（哪怕没写动机/思路/备注），否则这行没地方放。路径不存在只警告不阻断。
  不传 `doc` 时，若能从 `change` 探测到 `design.md`/`proposal.md`（含已归档的 `changes/archive/*-{change}/`，
  且归档目录唯一不歧义），会尝试自动带上——但这个 auto-default 结果**只用来丰富一个本来就会建的块**
  （因为写了动机/思路/备注，或显式传了 `doc`），它自己不会单独触发建块：轻量项（无动机/思路/备注、
  无显式 `doc`）即便 `change` 恰好探测到了文档，仍然只写 frontmatter item、不建块——不然一个随手记的轻量 TODO
  会因为当时恰好有个 change 在跑而被悄悄升级成带块的项，破坏"轻量项无 prose"的默认体验。

```bash
# 带显式关联文档：即使没写动机/思路，也会建块只为承载 doc 行
echo '{"module":"meter_collect.c","summary":"温度采样改 DMA 批量读取","type":"性能优化",
       "doc":"changes/dma-sampling/design.md"}' | python scripts/todolist.py add
```

### 2. 回写状态（set-status）

```bash
python scripts/todolist.py set-status --id T1 --to PROPOSED --evidence "change dma-sampling"
python scripts/todolist.py set-status --id T1 --to DONE     --evidence "commit a1b2c3d"
python scripts/todolist.py set-status --id T7 --to WONTDO   --reason "ROI 太低，硬件下一版才支持"
```

- **DONE 门禁**：必须 `--evidence`（关联的 change 名或 commit）——挡住"只标完成、不留线索"。
- **WONTDO 门禁**：必须 `--reason`，理由留痕。
- 状态码：`OPEN PROPOSED DONE WONTDO`。
- 机制：只更新 frontmatter 状态并在 marker block 追加历史；legacy item 首次触碰时提升为 same-file
  overlay，旧表 bytes 不变。DONE/WONTDO 的证据/理由只作追加式人读留痕。

### 3. 扫描 / 盘点（scan）

```bash
python scripts/todolist.py scan                      # 全部，按状态排
python scripts/todolist.py scan --status OPEN        # 只看没做的
python scripts/todolist.py scan --type 性能优化       # 按类型筛
python scripts/todolist.py scan --json               # 机器可读
```

末尾自动做 **frontmatter/marker/未提升 legacy 表**关系自检。

## 约定速查（本 skill 即真相源）

> issues 结构标准（目录/schema/状态/命令/sweep/D9）由 `issues-pool-batch-mgmt`（Phase B）落地，
> **本段 + [sdflow-buglist/SKILL.md](../sdflow-buglist/SKILL.md) 的对应段是这套标准唯一的
> 真相源（I13），不另起 rules 文件**——两边正文各自完整（自包含），共享 `issues.py` 部分互为镜像，
> 改一处需同步另一处。

### 目录结构

**本池**：`openspec/issues/todolist/YYYY-MM-todolist.md`，每月一个，当月所有 TODO 追加进去。
过渡期兼容旧路径 `openspec/todolists/`——`next-id`/`scan`/`set-status`/`triage` 全部
**dual-read**（新旧两个目录都扫）；**新记录只写新路径的 canonical frontmatter**。自定义 prefix 的
`next-id`/自动 add/显式 ID 查重都在同一仓级 exclusive snapshot lock 内读取 bug+todo 两池全集。
跨新旧路径撞同一 ID 会在 `next-id` 时打 WARNING，提示尽快把旧数据迁移到新路径。

**跨两池共享文件**（不是 todolist 私有，owner 是 `sdflow-issues/scripts/issues.py`；
sdflow-buglist 依赖同一份，见其 SKILL.md 对应段）：

- `openspec/issues/INDEX.md`——`issues.py reindex` 从 bug+todo 两池全部 dated 文件重建，首行
  固定 banner `<!-- GENERATED by issues.py reindex — DO NOT EDIT -->`。**只生成、禁手改**，不是
  独立真相源——手改内容会在下次 reindex 时被无条件覆盖，不做任何合并。
- `openspec/issues/batches.md`——批次注册表，**半手维护**，格式契约见下方「batches.md 字段级
  grammar」。

### 三维度 schema

每条 TODO 三个独立维度，互不覆盖：

| 维度 | 落点 | 可变性 | 含义 |
|---|---|---|---|
| 源change（关联Change） | frontmatter item `change` | **不可变**（provenance） | 在哪个 change 里冒出来的 |
| 批次 | frontmatter item `batch` | 可变 | 被哪个「清理 change」包走去做（批次 key = 清理 change 名） |
| status | frontmatter item `status` | 生命周期 | 见下方状态词表；marker prose 只追加历史，不是状态真相源 |

新写结构是 shared frontmatter envelope 下唯一 `sdflow-issues` namespace（短键
`schema/pool/mode/items`）；新文件 `mode=canonical`。历史 8 列表永久只读，活跃 legacy item 首次 mutation
以 `mode=overlay` shadow 旧 row，旧表与旧 block 内部 bytes 不改。reader 在 namespace 在场但损坏时
fail-closed，只有 namespace 不存在才回退 legacy parser。

**类型标签**

| 类型 | 含义 |
|------|------|
| 性能优化 | 提速 / 降资源占用 |
| 可观测性 | 日志 / metrics / 诊断增强 |
| 代码质量 | 重构 / 命名 / 结构改进 |
| 功能增强 | 新能力 / 扩展现有功能 |
| 基础设施 | 构建 / CI / 工具链 |

**状态码 + 终态集**

| 状态 | 含义 |
|------|------|
| OPEN | 已记录，未排期 |
| PROPOSED | 已被某 OpenSpec change 包入 scope |
| DONE | 已完成（注明 change/commit） |
| WONTDO | 评估后放弃（保留理由） |

**终态集 = `{DONE, WONTDO}`**——进入即"这条待办不再挂着"（WONTDO 是"决定不做"的合法闭合，
和 DONE 一样从 INDEX 的 open 板消失）。**批次完成判据**：批次**成员数 ≥ 1** 且**全部成员
∈ 终态集** → `issues.py reindex` 把该批次同步判/标 `DONE`；reindex 的自动判据**不会**把
0 成员批次判/标为 `DONE`（保持 `PLANNED`，防"空集全称为真"的 vacuous-truth 假 DONE）——但人
可用 `batch set-status` 手动把它标成任意状态（含 0 成员标 `DONE`），reindex 不会越权纠正，
只在状态与成员终态不一致时追加 `⚠️ 不一致` 警告。**注意**：bug 池终态集是 `{FIXED, WONTFIX}`——
两 recorder 词表不同，`reindex` 按各自 pool 判定，不硬编码字面 `"DONE"`（对 bug 池根本不成立）。

### 命令面

**per-type**（本脚本 `todolist.py`，只管 todo 池自己，不碰 bug）：

`add` / `scan`（`--status` / `--type` / `--change` / `--批次` / `--open-ungrouped`） /
`set-status` / `triage`（赋批次 + 把「未分诊开放态」（即 `OPEN`）推进到 `PROPOSED`，幂等——已
`PROPOSED`/已终态都 no-op，不倒退状态） / `next-id`。全部命令 dual-read 新旧两个目录（见上
「目录结构」）。

**共享**（`sdflow-issues/scripts/issues.py`，独占跨 bug+todo 的命令；与
[sdflow-buglist/SKILL.md](../sdflow-buglist/SKILL.md) 对应段互为镜像）：

- `reindex`——子进程分别调 `buglist.py scan --json` / `todolist.py scan --json` join 两池
  （join 前先做跨池 ID 冲突检测，见下方 D9）→ 生成 `issues/INDEX.md`（open 项按批次分组的物化板
  + 已闭合项计数摘要，全量确定性重建、幂等）→ 顺带同步 `issues/batches.md` 的 `状态:`/`成员:`
  两条生成行（按上面「批次完成判据」）。
- `batch add / set-status / rename`——`issues/batches.md` 注册表操作：`add` 新建 `PLANNED`
  条目（成员空）；`set-status` 只改状态生成行；`rename` 改批次 key + 同步两池里所有该批次成员的
  批次 tag；rename 先写 registry provenance `重命名自:`，复用每池单次 direct-bytes snapshot 更新 dated/INDEX/batches。
  任一步失败均 non-zero 并提示**重跑原命令**，全 old/混合/全 new retry 均可收敛。批次生命周期
  `PLANNED → IN_PROGRESS → DONE`（`PLANNED→IN_PROGRESS` 由人在真正开
  cleanup change 时手动 `set-status`；`→DONE` 通常由 reindex 按完成判据被动同步——人也可以用
  `set-status` 直接标，reindex 不会越权纠正，只在状态和成员终态不一致时追加 `⚠️` 警告）。

### sweep 协议（每个 change 收尾时）

`sdflow-done` 生成 hand-off 那一步跑 sweep：以 **源==本change ∧ status 非终态 ∧ 批次==空**
为界，只分诊**本 change 自己新增**的未分诊 OPEN 项——显式传 `--change {本change}`（不靠
`detect_change` 猜，从源头减少假孤儿）→ `triage` 分诊入批次 → `batches.md` 登记 `PLANNED`
→ 末尾跑 `issues.py reindex` 刷新 INDEX → hand-off 引用这次 sweep 结果。已在各自 change 分诊过
的老 OPEN 项不被重诊；**源为空的孤儿项不归本次 sweep**，交独立的通用清理流程兜底
（`scan --open-ungrouped` → `triage` → 另开 cleanup change）。

### batches.md 字段级 grammar（半手维护，跨两池）

```
### {批次key} — {标题}
状态: PLANNED            ← 生成行（issues.py reindex / batch set-status 维护）
成员: (生成) B1, T2      ← 生成行（reindex 拿 item 池当 ground truth 回填）
优先级: P1               ← 人写行（reindex/batch 绝不覆写）
计划: 一句范围           ← 人写行（同上）
```

`状态:`/`成员:` 两个固定前缀是**生成行**；其余（含条目里额外追加的字段）都是**人写行**。
reindex **只精确 patch 生成行**，绝不覆写人写行；发现「人写 `状态: DONE` 但成员未全进终态集」
不会越权纠正这个值，只在条目尾追加一行 `⚠️ 不一致` 警告，等人工核实后自己用 `batch set-status`
改回或补完成员状态。批次 tag 指向 `batches.md` 里不存在的 key（orphan）也只报警、不静默生成
ghost 条目。

### ID 两池语义唯一〔ADR-0025〕

默认 bug=`B`、todo=`T`，公开的单字母自定义 `--prefix` 保留。ID semantic key 是
`(uppercase ASCII prefix, decimal integer)` 且不含 pool，因此 `A007`/`A7` 及 bug/todo 的 `A7`
均冲突。`next-id`、自动 add 与显式 ID 查重必须在同一 snapshot lock 内读两池全集；`reindex`
仍作 fail-closed 防护网，但不承担事后修复。

### 铁律（脚本守住大半）

① ID 在 bug+todo 两池语义全局唯一；② 轻量优先——简单项只写 frontmatter item，要说明
动机/思路才建块；③ DONE 必带关联 change/commit（门禁）；④ 实施走 change——todolist 只是收集池，
真做时通过 OpenSpec change 落地，不在此直接改代码；⑤ 状态追加式、不删历史；⑥ `issues/INDEX.md`
只生成禁手改（issues.py 兜底无条件覆盖重建）；⑦ B/T 前缀跨池互斥（D9，见上，issues.py reindex
兜底检测）。

## 注意

- 脚本默认在 **git 仓根**下找 `openspec/issues/todolist/`（新路径，写入目标）；`openspec/todolists/`
  仅作过渡期 dual-read 只读兼容。不在 git 仓时用 `--root` 指定。
- 一个想法一条 T-ID；后续进展走 `set-status`，不要新开 ID。
- 模型的价值在**判断**：把噪音（太琐碎、重复、其实是 bug 的）挡在池子外，比记全更重要。
