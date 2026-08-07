# 消灭 workflow bundle 双分发链：规则与评审工具全局单份共享，取消 pin 旁路

> 状态：**Accepted**（2026-08-07，`fix-probe-scan-precision` 设计门拍板）· 关联 change：`fix-probe-scan-precision`
> 取代：`adr/0038`（删除，见下「取舍：被否决的候选」）· 补充状态注记：`adr/0003`、`adr/0005`、`adr/0019`、`adr/0036`

## Context

`$RULES_ROOT`（评审规则与机械层脚本的解析根）此前有两个可能来源，而只有其中一个涉及「拷贝」：

| resolver 步 | 判据 | 结果 | 涉及拷贝？ |
|---|---|---|---|
| ①（本 ADR 删除） | 仓内有规则文件本体（`workflow.md` / `spec-checklists/` / `code-checklists/` 任一） | 命中仓内 `openspec/workflow/` 本地副本 | **是**（`sdflow-init update` 拷的 `tools/` + `lens-metric-contract.md`） |
| ②（保留，改名两步链的唯一步） | `~/.sdflow/workflow`（Unix 软链）或 `~/.sdflow/workflow-path`（Windows 指针） | `global-canonical` = 运行 checkout 内的文件树本身 | 否 |
| ③（保留） | 以上皆不可达 | `exit 2` → 调用方显式降级通用评审 | — |

步②的两个平台实现都指向**活 checkout**（Unix 实测 `readlink ~/.sdflow/workflow` →
`~/.skills/sdflow-skills/sdflow-init/assets/workflow`；Windows 由 `setup.sh` 写入活 checkout 路径），
而两个评审 SKILL 亦软链自同一 checkout ⇒ **步②路径上 tools 与 SKILL 恒同代，结构上不存在失鲜轴**。

**∴ bundle 拷贝链的 skew，唯一成因 = 步①（消费仓持有一份需要人手动 `sdflow-init update` 才能追新的
拷贝）。删掉步①，这条链的 skew 无处可生**——不是把探测做准，是让被探测的对象不再存在。

此前（`adr/0038`）为堵这个 skew 窗口，走的是「探测器」路线：先是两个评审 SKILL 里的逐能力内容信号散文
（`sdflow-code-review` 四条、`sdflow-spec-review` 两条），后改为 bundle 版本对比。两者都在**症状层**求
精确，都会随 bundle 特性增长而不断补新分支（CLAUDE.md 基准 5 警号：「每轮 review 都在同一处补一个新
分支 ⇒ 这个函数本来就不该存在」）。人在设计拷问中给出方向性改变：**去掉 pin 仓这个逻辑，所有规则文件
都应该是共享的**——把问题从「如何精确探测拷贝陈旧」搬到「让拷贝本身不存在」，即本 ADR。

`~/.sdflow/hack/` 拷贝链（checkpoint-commit.sh / resolve-workflow.sh 等）与 Windows 上「旧 SKILL ×
新 canonical tools」是另外两个独立的失鲜面，**本 ADR 不覆盖**——见下「Non-Goals」与「接受的边角」。

## Decision

**一、resolver 收缩为两步链，删除步①（本地 pin 判定）**：`sdflow-init/assets/hack/resolve-workflow.sh`
不再检查仓内是否有规则文件本体，解析直接从全局 canonical 开始；退出码集不变（`0`/`2`/`64`）。
`sane()` 健全性检查扩面为**形状级**判据——`tools/` 目录存在且非空 + `lens-metric-contract.md` 非空——
**MUST NOT 枚举具体 `.py` 成员**（成员清单 = 每加一个工具补一条守卫 = 本 ADR 要消灭的补丁螺旋在守卫里
复活；现实的半坏态是整目录/整文件缺失，「缺某一个工具」由该工具自身 fail-closed 兜）。

**二、`sdflow-init` 停止铺设 `tools/` 与 `lens-metric-contract.md`**：`copy_bundle()` 非-full 分支只保留
`WORKFLOW-GUIDE.md` 复制与 project-local schema 下发；`--dev`、`full=True` 分支、`ignore_tools_tests()`
与 T15 为其开的 `stale_shadow_warnings` 豁免一并退役（源仓 dogfood 同样走全局 canonical，不再需要本地
instance）。

**三、`WORKFLOW-GUIDE.md` 保留铺设——人体验决策，与「规则共享」正交**：它不参与任何执行、不被任何脚本
机读，结构上不可能 skew，陈旧无害；人需要一份「不用跳文件、随仓走」的完整参考。其生成器
（`hack/gen_workflow_guide.py`）须把指向 sibling 规则文件的相对链接降为文字引用或内联小节——目标态
消费仓 `openspec/workflow/` 只有 GUIDE 一个文件，相对链接目标态全部断链，而「随仓走、不用跳文件」正是
保留它的理由，断链会击穿该理由。

**四、`stale_shadow_warnings()` 判据扩员为死件表述**：存量消费仓残留的 `openspec/workflow/` 规则文件、
`tools/`、`lens-metric-contract.md`**不自动删除**（`spec-workflow` 既有安全红线不变），但告警文案改写为
带前置条件的死件表述 + 可复制删除命令，MUST NOT 输出无条件的「已无任何生效路径」；人执行命令即达终态
零死件，不新增一次性自动清删代码。

**五、`ship_gate.py` 的 `tools_spec` 失鲜比较腿整条删除，理由按仓型分开写**（`sdflow-ship/scripts/ship_gate.py`
原 `:955-959`）：
- **toolkit 源仓**：tools 权威源 `sdflow-init/assets/workflow/tools/` 位于顶层条目 `sdflow-init` 之下，
  改权威源必翻该顶层条目的 tree oid ⇒ 已被顶层腿（比较仓库顶层条目浅层快照、排除 `openspec`）覆盖，
  `tools_spec` 腿只多抓「直接改消费仓镜像而不改权威源」一种情形。
- **消费仓**：镜像 `openspec/workflow/tools/` 本身不复存在（第二条决策）——「直接改镜像」这个动作不可能
  发生。**MUST NOT 用「顶层腿覆盖」概括消费仓**：消费仓顶层无 `sdflow-init` 条目（实证 `10-michi`），
  是「被比较的对象已消失」，不是「被别的腿接住」。
  消费仓侧「全局 canonical 在 review 与 done 之间变更不可见」是 change 前即存在的盲区（旧腿只守仓内
  镜像，从不守 canonical）——净回归仅「窗口内有人跑 update 刷镜像会被察觉」一种情形，而镜像删除后该
  动作不可能发生，故**接受，不建替代**。

**六、`pin` 的两个既有用途改用 `SDFLOW_HOME` 既有测试隔离契约，不立版本冻结承诺**：
- 用途 A（开发期沙盒消费仓测试新规则）：把规则副本放进自备目录，`SDFLOW_HOME` 指向它，
  `resolve-workflow.sh --root` 解析命中该目录并过 `sane()`。
- 用途 B（存量仓想固定某版规则）：`SDFLOW_HOME` 同样可行，但**这不是本 ADR 立的新承诺**——
  `resolve-workflow.sh` 头部契约注释一贯写明 `SDFLOW_HOME` 缺省 `~/.sdflow`、测试用它重定向，
  它同时是 `setup.sh` 的安装根，对其跑 setup 会覆盖所指内容。唯一存量 pin 仓（`05-sarvelo`）实际诉求
  是跟最新，为无人要的「冻结」能力立做不到的 SHALL 比不立更坏，故 spec 不将其立为面向使用者的版本
  冻结路径。

## Considered Options

- **本方案（消灭双链，选中）**：净删除远大于净新增——删 resolver 步①、删 `init.py` 的 tools/contract
  拷贝与 `--dev`/`full` 分支、删两个评审 SKILL 的 skew 探测段、删 `ship_gate.py` 的 `tools_spec` 腿、
  删本仓 `openspec/workflow/` 下 7 个文件。新增为零——pin 两用途改用既有正式契约 `SDFLOW_HOME`，
  不新建任何机制。可回退（改动集中且几乎全是删除，`git revert` 即复原）。
- **按症状层求精确（本地副本字节比对）**：`resolve-workflow.sh` 判出仓内有本地副本时才逐文件比对
  该副本与活 checkout 同名文件的 sha256；判出 `global-canonical` 直接放行。曾是重开相位 B 第一轮的
  拍板方向（决策纪要 D9–D12），后被人的方向性改变推翻——它仍然保留了「拷贝」这个对象，只是把探测做
  精确，未消灭 skew 存在的空间。
- **维持现状 + 只修 grep 写法**：原 issue T270 的口径。砍因：探测写法精确到不产生假阴/假阳，仍是在
  症状层缝缝补补，且探测器本身仍是补丁螺旋（每加一个 bundle 特性补一条信号）。

## 取舍：被否决的候选（含 `adr/0038` 并入）

`adr/0038`（bundle skew 由分发链版本对比判定）已删除——**起手前提被证伪 ⇒ 决策撤销**，而非「问题域
消失」：0038 假设的前提是「拷贝链会继续存在，只需要更准确地探测它是否陈旧」；人的方向性改变
（「去掉 pin 仓这个逻辑」）证伪了这个前提——拷贝本身不该存在，而非需要被更好地探测。0038 本分支新建、
从未进 main、其版本对比机制从未实现。其候选与砍因一并归档于此：

- **版本戳对比**（0038 原方案）：两条分发链各自在被刷新时写下自己的版本（`setup.sh` 写全局侧、
  `init.py` 的 `copy_bundle()` 写消费仓侧），探测 = 比两个 commit SHA 字符串。砍因：起手前提被证伪——
  拷贝对象本身被消灭后，没有「两个版本」可比。
- **字节比对（pin-only + 零写入点）**：`resolve-workflow.sh` 判出 `local-pin` 时，逐文件比对 pin 副本与
  活 checkout 同名文件的 sha256；比对面 = `tools/**` + `lens-metric-contract.md`，排除 `WORKFLOW-GUIDE.md`
  与规则层文件（含 `trigger-catalog.md`，纳入会让 pin 仓永久硬停且无法通过 update 解除）。砍因：同上，
  起手前提被证伪——判定对象（拷贝）已消失，判据无处附着。
- **pin-only 判据**（不比对内容，只要判出 `local-pin` 就硬停要求 update）：砍因：过度惩罚——很多存量
  仓的 pin 副本其实是最新的，无条件硬停会制造不必要的摩擦；且仍未解决「pin 本身该不该存在」这个更
  根本的问题。
- **纯 bash 并进 resolver**（不落 Python helper）：砍因：排除口径需双实现（shell 与 Python 各写一遍
  「哪些文件参与比对」）+ 跨平台 `sha256sum`/`shasum` 分支手搓，与本 ADR「不新增机制」的方向相悖。

## 时序：为什么改动传播无窗口期

本变更跨 5 个组件（`resolve-workflow.sh` / `init.py` / 两个评审 SKILL / `ship_gate.py`），删除后：

```
目标态（一条链，一个时点）
──────────────────────────────
开发者 push bundle 改动
        │
运行 checkout: git pull
        │
   SKILL 立刻新 ─┐
        │        │ 同一 checkout
   全局 canonical │ 同时生效
   立刻新 ◀──────┘
        │
   评审读全局 tools
        ▼
   无中间态，无窗口
```

右侧没有任何「人手动」的方框 ⇒ 没有可遗漏的步骤 ⇒ 没有可错位的时点。`setup.sh` 仍是必须跑的一步
（刷 `~/.sdflow/hack/` 与 canonical 软链），但那是既有的 `pull → setup` 纪律，不是本 ADR 新增的义务。

## Migration Plan

**顺序不可颠倒**（每一步都保证中途中断时系统仍可用）：

1. **先删 SKILL 侧的探测段**（`sdflow-code-review` / `sdflow-spec-review`）。此时副本仍在、resolver
   仍有步①——系统完全可用，只是不再做那个从未抓到真阳的检查。
2. **再删 resolver 步①**（`sdflow-init/assets/hack/resolve-workflow.sh`）。此时所有仓改走步②；
   存量副本变死件但无害。
3. **再停 `copy_bundle` 铺 tools/contract**，并退役 `--dev` / `full` / T15 豁免。
4. **最后**退役 `ship_gate.py` 的 `tools_spec` 腿、改写告警文案、订正 CLAUDE.md / ADR / CONTEXT、
   删除本仓 `openspec/workflow/` 下 7 个文件、关闭 T269/T270、同批处理两处硬编码引用
   （`hack/tests/test_yq_wrapper_consistency.py` 的 `TARGETS`、`hack/check_encoding_hygiene.py`
   的镜像排除分支）。

反序（先停铺、SKILL 仍探测）会让仍处旧 resolver/pin 状态的存量仓在失效提示下硬停。

**发布**：push → 运行 checkout `git pull` → **立即** `bash setup.sh`（刷 `~/.sdflow/hack/` 与 canonical）。
消费仓不再需要 `sdflow-init update` 才能评审；跑它只为拿新的 `WORKFLOW-GUIDE.md`。

## 回滚

本变更的改动集中且几乎全是删除 ⇒ `git revert` 即复原；复原后 **MUST 依次执行**：

1. 每台机回运行 checkout 重跑 `bash setup.sh`（拿回三步链 resolver）。
2. 各消费仓重跑 `sdflow-init update`（拿回 `tools/`，否则回滚后首轮评审因缺 tools 裸崩）。

顺序不可颠倒——步骤 1 未完成前跑步骤 2，消费仓拿到的 `sdflow-init` 仍是新版（不铺 tools），
`update` 不会产生任何效果，人会误以为回滚失败。

## Consequences

- **正**：skew 这一整类问题结构上不再存在（不是探测更准，是被探测的对象消失）；`sdflow-init update`
  的职责收缩到 GUIDE + schema 两项，其收敛性/事务性顾虑随之消失；消费仓侧再无「先跑 update 才能评审」
  的硬停仪式。
- **负 / 代价**：`openspec/specs/spec-workflow/spec.md` 的 Requirement 需从「review 机械层脚本 SHALL
  复制进消费仓」翻转为「MUST NOT 复制」，是契约级改动；存量 pin 仓（如 `05-sarvelo`）的规则来源从
  「跟随本地拷贝」静默切换为「跟随全局 canonical」——由 `stale_shadow_warnings()` 与 `maintain_scan`
  的死件告警覆盖，但只在跑 `sdflow-init` / `sdflow-maintain` 时出现，不在评审起手出现。
- **诚实边界（本 ADR 不覆盖）**：
  - `~/.sdflow/hack/` 拷贝链目前无 `capability-manifest` 守（该 manifest 仅覆盖
    `outside-voice-job.py` / `outside-voice.sh` / `skill-principles.md` 三项），根因项（hack 链
    symlink 化）记 todo，不在本 ADR 范围。
  - Windows 上「旧 SKILL × 新 canonical tools」不被任何机制覆盖——检查者只能是 SKILL 自己或
    `~/.sdflow/hack/` 的 helper，二者同为一次 `cp -r` 的产物，没跑 `setup.sh` 就一起旧，运行时自检
    结构上不可自举。CI 层面可测但目前未测（`windows-recorder-smoke.yml` 在 `windows-latest` 跑全量
    pytest，触发 paths 覆盖本变更的全部脚本面），记 todo。
