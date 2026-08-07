---
schema_version: 1
change: fix-probe-scan-precision
branch: feat/fix-probe-scan-precision
generated_at: 2026-08-06T23:00:49+08:00
decision_hash: cf72d0d3da2c
---

# 决策纪要 · fix-probe-scan-precision

## 目标态

**消灭 workflow bundle 的双分发链**——规则与工具**全局单份共享**，消费仓不再持有任何 workflow 副本
（`WORKFLOW-GUIDE.md` 是显式例外，纯人读、不参与执行），取消 `resolve-workflow.sh` 的 pin 旁路。
⇒ skew 这一整类问题**结构上不再存在**，两个评审 SKILL 的 skew 探测段整段删除、不做替代。

> 〔本句于重开相位 B 第二轮改写。原目标态为「让 skew 探测与残留扫描的写法精确到不产生假阴/假阳」——
> 那是在**症状层**求精确；人在第二轮给出方向性改变后，目标移到**根因层**：让被探测的对象根本不存在。〕

## 拍板决策

- **D1 T269 从「删两个孤儿副本」改为「订正 CLAUDE.md 措辞 + 关闭 T269 为误判」** — 依据：那两个文件
  在消费仓是活件，T269 的「功能死件」判断只对源仓成立，而它抱怨的真问题（`grep gstack` 假阳）与 T270
  同根因——都是**扫描/探测写法不精确导致误判**，正解是修探测不是删数据；**砍掉的候选**：①让 `init.py`
  区分源仓/消费仓、源仓不铺（砍因：给 init.py 加一个只为源仓服务的分支，且源仓 dogfood 真实性下降）
  ②照原 todo 删文件 + 加防重铺机制（砍因：与 update 的托管刷新语义正面冲突，每次 update 都要打架）。
  **证据锚**：「人 2026-08-06 明确确认（回复『同意』）」

- **D2 用「bundle 版本对比」整体替代四条内容特征信号（人提出，推翻 todo 与我先前的两个方案）** —
  依据：四条信号是「每加一个 bundle 特性补一条」堆出来的（本 change 原本还要再加③④两条），命中
  CLAUDE.md 基准 5 的警号形状「每轮都在同一处补新分支 ⇒ 这个东西本来就不该长这样」；版本对比是 O(1)，
  加多少特性探测逻辑零改动，且不存在 fence 提取撞散文这类假阴面（T270 的坑在此方案下**不存在**）。
  **砍掉的候选**：①把四条命令写字面进两个 SKILL（砍因：结构上无法机械守，见 C5；且两处重复）
  ②下沉 `skew_probe.sh`（砍因：仍是「检查内容特征」，只是脚本化了——补丁螺旋没停，加特性还要加 check）。
  **证据锚**：「人 2026-08-06 明确提出并确认（『init 时自动生成一个记录当前 git 版本的文件就可以了，
  检查时对比 git 版本号』/ 回复『同意』）」
- **D3 版本形式 = 纯 git commit SHA，MUST NOT 用 `git describe --dirty`** — 依据：开发时工作树常脏，
  `-dirty` 后缀会让版本恒不相等、天天误报；脏状态应单独提示，不混进相等性判断。**证据锚**：人 2026-08-06 确认
- **D4 两条分发链各自在被刷新时写下自己的版本，探测 = 比两个字符串** — 依据：`setup.sh` 刷全局、
  `init.py update` 刷消费仓 bundle，各写各的落点，语义自洽无第三方协调。**证据锚**：人 2026-08-06 确认
- **D5 非 git 环境两边同为 `unknown` ⇒ 相等 ⇒ 放行（fail-open）** — 依据：与 `setup.sh:735` 现有
  `|| echo "unknown"` 降级一致；改 fail-closed 会让非 git 安装完全跑不了评审。**证据锚**：人 2026-08-06 确认
- **D6 版本取值用 bundle 作用域而非整仓 HEAD**：`git log -1 --format=%H -- sdflow-init/assets/workflow/` —
  依据：整仓 HEAD 每个 commit 都变、而 bundle 大多数 commit 没动，用 HEAD 会让源仓每提交一次就得
  update 一次才能评审，方案会因烦人被绕过；bundle 作用域精确匹配「bundle 是不是旧的」这个探测语义。
  **砍掉的候选**：整仓 `git rev-parse HEAD`（砍因：见上实测）。
  **证据锚**：实测 `git rev-parse HEAD`=`0d024ae`（改 setup.sh）vs
  `git log -1 --format=%H -- sdflow-init/assets/workflow/`=`ee5b4f4` ⇒ 二者确实不同，误报真实存在

- **D7 写版本的动作放在 `copy_bundle()` 内部，覆盖 full/非-full 两分支** — 依据：`init.py:1127`
  `copy_bundle(root, full=dev)` 两分支共用一个出口，放调用点会漏掉源仓 `update --dev` 路径，
  导致源仓铺完没版本文件、反被自己的探测判成陈旧。**证据锚**：`sdflow-init/scripts/init.py:1127`
- **D8 版本不等 ⇒ 硬停，不降级为警告** — 依据：硬停发生在**起手**（尚未 fan-out、未跑 voice），
  损失仅为重新起手；放行的代价是整轮评审白跑；与既有 pull→setup 纪律同构。报错文案 MUST 含
  「跑 `sdflow-init update`」。**证据锚**：现有四条信号即硬停语义（`sdflow-code-review/SKILL.md:206`），
  本决策维持该强度不变

### 〔重开相位 B · 2026-08-06〕

- **D9 判据整体收缩为「pin-only + 零写入点内容比对」** — `resolve-workflow.sh` 判出 `local-pin` 时，
  才逐文件比对 pin 副本与活 checkout 同名文件的 `sha256`；判出 `global-canonical` **直接放行**
  （C9：结构上同代，无失鲜轴可探）。**两个写入点全删，不落任何版本戳，不调 `git`。**
  依据：C9 + C10 —— 全局侧恒指活 checkout、消费仓副本只在 pin 时被读。一并归零 F1/F2/F3/F4/F5/
  F7/F8/F10/F18/F19/F20。**证据锚**：「人 2026-08-06 明确拍板（回复『采纳 pin-only + 零写入点内容比对』）」
  - **⇒ 推翻 D3**（纯 commit SHA）：不再有「版本」这个中间物，比的是字节。
  - **⇒ 推翻 D4**（两条链各写各的版本）：写入点由 2 降为 **0**，全部实时计算。
  - **⇒ 推翻 D7**（写入动作放 `copy_bundle()` 内部）：无写入动作。
  - **⇒ D2 的立意保留、取值方式改写**：仍不做逐能力内容探测、仍是「加 bundle 特性零改动」，
    但「版本对比」改为「字节比对」。
  - **⇒ D5（`unknown` 双侧 fail-open）随之作废**：不调 git ⇒ 无 `unknown` 态，判定表从四态降为
    「全等放行 / 有差异硬停」两态（差异含：内容不同 · pin 侧缺文件 · pin 侧多残留文件）。
  - **⇒ D8（不等即硬停）维持不变**，文案落点改为 pin 仓专属指引。

- **D10 比对面 = `tools/**`（去 `tests/` 与 `__pycache__` 等本机缓存）+ `lens-metric-contract.md`；
  排除 `WORKFLOW-GUIDE.md`、`trigger-catalog.md` 与全部规则层文件** — 依据：① 比对面须对齐
  `copy_bundle()` 非-full 的**实拷集**（C13），guide 是纯人读产物、陈旧无害，排除它即 F3「改一句人读
  措辞就硬停」的正解；② `trigger-catalog.md` 属 pin 有意冻结的规则层（C12），纳入即让每个 pin 仓
  **永久硬停且无法通过 update 解除**（update 刷 tools 不刷规则 ⇒ 死锁而非可恢复停机）= 取消 pin 逃生口。
  **砍掉的候选**：①比对面 + `trigger-catalog.md`（砍因：见上，pin 死锁）②pin 仓禁用需机读规则的工具
  （砍因：砍功能，且要改两个 SKILL 的降级路径，scope 加宽）。
  **顺带覆盖 F12**：`05-sarvelo` 实测**有**旧 `trigger-catalog.md`、**无** `tools/` 与 contract ⇒ 现状跑评审
  会在 `python3 $RULES_ROOT/tools/anchor_lint.py` 裸崩；本判据的「pin 侧缺文件 ⇒ 硬停」把该既存洞收进 fail-loud。
  **证据锚**：「人 2026-08-06 明确拍板（回复『取 A』）」

- **D11 落点 = `resolve-workflow.sh --check-skew` + canonical 侧 `bundle_skew.py`，SKILL 只读 `exit 3`** —
  `RULES_ROOT == global-canonical` ⇒ 直接 `exit 0` 零开销；`local-pin` ⇒ shell out 调
  **`$CANON/tools/bundle_skew.py`**（canonical 侧，非 pin 侧）比对 D10 面；helper 不存在 / 不可执行 /
  任何非零退出 ⇒ **一律折叠进「陈旧」同一路径**（fail-closed + actionable 文案，MUST NOT 漏裸 traceback）。
  依据：C14（helper 须与 SKILL 同代）+ Q3 原论证（`resolve-workflow.sh` 是唯一同时知道 pin/canonical/
  平台/`SDFLOW_HOME` 的地方，收拢即消灭 F2/F6/F7 的共同根因「同一件事写两遍」）+ 不手搓 bash
  （纯 bash 要重写排除口径并分支 `sha256sum`/`shasum`，即 F6 换位复发）。
  **砍掉的候选**：①纯 bash 并进 resolver（砍因：排除口径双实现 + 跨平台 sha 分支手搓）
  ②helper 落 `~/.sdflow/hack/`（砍因：该链是拷贝、自身需 capability-manifest 守，凭空多一层可漂移面）。
  码位 `3` 未被占用（现有 0/2/64）。**证据锚**：「人 2026-08-06 明确拍板（回复『同意』）」

- **D12 Windows 两条残余：① 「旧 SKILL × 新 tools」登记为诚实边界不做；② 硬停文案按缺失侧分流并同时给两条命令** —
  依据（C9②）：Windows 下 SKILL 与 `init.py` 均为 `cp -r` 快照（`setup.sh:119`），而 canonical 指活 checkout（`:489`）。
  - **①** 该面结构上**不可自举**——探测器由 SKILL 自己调用，旧 SKILL 不会去调新探测；完美成本不是"高"
    而是"死结"。且本仓对 Windows 分支**结构性无测试面**（`IS_WINDOWS` 由 `uname -s` 定、无环境变量覆盖入口，
    `hack/tests/test_install_agents.py:14` 自述）。⇒ 按通则④简化，proposal 的 Why 与 delta spec MUST 各
    写明「本机制不覆盖 Windows 的 SKILL 快照失鲜」。
  - **②** Windows 上 `init.py` 的 `BUNDLE_SRC` 是快照 ⇒ `git pull` 后未跑 setup 时，`sdflow-init update`
    铺的仍是旧 tools ⇒ **硬停无法解除**（与 F1 第二窗口同病：文案指错方向致用户循环）。
    ⇒ 文案 MUST 分流：**pin 侧缺文件 ⇒ 先 `sdflow-init update`**；**内容不等 ⇒ 先在运行 checkout 跑
    `bash setup.sh`，再 `sdflow-init update`**。pytest 可断言文案内容。
  **证据锚**：「人 2026-08-06 明确拍板（回复『同意』）」

### 〔重开相位 B · 第二轮 · 2026-08-06 · 人给出方向性改变〕

- **D13 去掉 pin 仓逻辑；规则与工具全局单份共享，消费仓不再持有任何 workflow 副本** —
  **证据锚**：「人 2026-08-06 明确指示（『去掉 pin 仓这个逻辑，所有规则文件都应该是共享的』）」
  - **这一条使 skew 结构上不再可能**：skew 的**唯一**成因是「消费仓有一份拷贝，且拷贝需人手动跑
    `sdflow-init update`」。取消拷贝 ⇒ 没有第二份 ⇒ 没有可错位的对象。
  - **⇒ D9/D10/D11/D12② 整体作废**（它们都是「如何精确判定拷贝是否陈旧」的方案，判定对象已消失）。
    **保留**：D12①（Windows SKILL 快照边界，与 bundle 分发无关，仍是诚实边界）· D1（CLAUDE.md 措辞
    订正 + T269 关闭为误判）· D8 的 fail-loud 立意（转由 resolver 既有 `exit 2` 承载）。
  - **⇒ B 层（skew 探测）整段删除，不做任何替代**：两个评审 SKILL 的内容信号散文
    （`sdflow-code-review/SKILL.md:206` 四条 · `sdflow-spec-review/SKILL.md:180` 两条）整段移除。
  - **⇒ A 层（pin 仓机械层缺失）一并消失**：不再有 pin 仓，`$RULES_ROOT` 恒为全局 canonical，
    其健全性已由 `resolve-workflow.sh` 既有 `sane()` + `exit 2` 覆盖。

- **D14 `WORKFLOW-GUIDE.md` 保留铺设进消费仓** — 依据：它是**人体验决策，与「规则共享」正交**——
  不参与任何执行、不被任何脚本机读 ⇒ 结构上不可能 skew，陈旧无害。`init.py:272-275` 注释
  「【给人看的】完整手册……人需要一份不用跳文件的完整参考，**且它得在自己的仓里、随仓走**」是有意为之。
  **砍掉的候选**：一并删除、人去读全局那份（砍因：不再随仓走、不进消费仓 git 历史）。
  **证据锚**：「人 2026-08-06 明确拍板（回复『保留铺设』）」
  - **⇒ `copy_bundle()` 非-full 分支删剩两项**：`WORKFLOW-GUIDE.md` + `openspec/schemas/<PROJECT_SCHEMA>`
    （后者是 openspec CLI 要读的 project-local schema，非 workflow 规则，不受 D13 影响）。

- **D15 D1 由「T269 整体误判」修正为分治；T270 关闭理由改写** — 依据：D13/D14 使 D1 的支撑理由
  （「那两个文件在消费仓是活件」）**只剩一半成立**。**证据锚**：「人 2026-08-06 明确拍板（回复『同意』）」
  - **T269 拆两半**：`lens-metric-contract.md` —— 它是 `tools/` 的机读依赖，随 tools 一并走全局
    ⇒ **在消费仓不再是活件** ⇒ T269 对它的「孤儿副本」判断**成立**，随 D13 删除；
    `WORKFLOW-GUIDE.md` —— D14 保留铺设，本仓作为消费仓也仍要读 ⇒ **仍是误判**，保留。
  - **D13 超额完成 T269**：本仓 `openspec/workflow/` 现有 8 个文件（6 个 tools + contract + guide），
    D13 后**只剩 `WORKFLOW-GUIDE.md`**。T269 只要求删 2 个，实删 7 个。
  - **T270 关闭理由改写**：从「改探测写法修复」改为「**skew 探测段整体移除，问题对象消失**」
    ——不是修好了，是不存在了。MUST NOT 在 issue 里写成"已修复"（那会让未来读者以为探测器还在）。

- **D16 落一条新 ADR + 把 `adr/0038` 标记为 Superseded；`openspec/CONTEXT.md` 只补 `skew` 一条术语** —
  **证据锚**：「人 2026-08-06 明确拍板（回复『同意』）」
  - **新 `adr/0039`**（编号实查 `openspec/adr/` 现止于 0038）：主题 = 消灭双链，规则与工具全局单份、
    取消 pin 旁路。ADR 三条件全中：难逆转（删机制 + 删副本，回退要重铺）· 缺上下文会令人意外
    （未来读者见 resolver 只剩一条路径会问「当初为何有 pin」）· 有真实权衡（pin 逃生口 ↔ `SDFLOW_HOME`）。
    MUST 涵盖：skew 的唯一成因、pin 两用途的替代（C15）、`ship_gate` 腿退役推理（C14）、GUIDE 例外（D14）。
  - **`adr/0038` 标 Superseded**：其主题「bundle skew 用版本对比而非能力探测」的**问题域随 D13 整个消失**
    ——不是结论被推翻，是问题不再存在。MUST 在 0038 头部注明被 0039 取代及该理由。
  - **术语**：`openspec/CONTEXT.md`（66KB）实查 **`skew` 与 `pin` 均无定义**。只补 `skew`——因为
    **`manifest skew`（`~/.sdflow/hack/` 各 helper 之间，由 `capability-manifest.json` 守）在 D13 后仍存在**，
    该词继续使用。`pin` **不入 CONTEXT**：机制已删，历史交代放 `adr/0039` 即可。

## 承重约束

- **C1 那两个文件在消费仓是活件，不是死件** — 验证方式：读 `init.py` 非-full 分支的拷贝逻辑与其注释；
  **证据锚**：`sdflow-init/scripts/init.py:266-278`——contract 注释「是 tools/anchor_lint.py 的运行时
  机读依赖（读 lens-metric-enums 块），须与 tools/ 同批刷新，否则本地 pin 消费仓 update 后『新脚本+旧
  契约无块』永久 fail-closed」；guide 注释「【给人看的】完整手册……人需要一份不用跳文件的完整参考」
- **C2 仓根 `openspec/workflow/tools/` 有真消费方，不可一并清理** — 验证方式：全量 grep 引用点；
  **证据锚**：`sdflow-ship/scripts/ship_gate.py:953-955` `tools_spec = (b"openspec/workflow/tools/",)`
  注释「含真运行代码（anchor_lint.py 等），排除整棵 openspec 会漏判」——它参与 code 域失鲜判定
- **C3 行首锚定的单条 grep 已足够精确，fence 块提取非必需** — 验证方式：对真实 contract 实跑；
  **证据锚**：`grep -c "^runner:.*none" lens-metric-contract.md` = 1（精确命中 :28）；散文里的同名条目
  形如 `- runner∈ {claude, codex, none, unknown}`（:11，行首为 `- `、用 `∈` 非 `:`）⇒ 不被 `^runner:` 误命中
- **C4 两个评审 SKILL 共享信号①②，spec-review 侧有完全相同的假阴风险** — 验证方式：逐字比对两处探测段；
  **证据锚**：`sdflow-code-review/SKILL.md:206`（四信号）与 `sdflow-spec-review/SKILL.md:180`（信号①②
  描述逐字相同）⇒ 只修 code-review 是点补，两处同治才是面治（基准 3）
- **C5 散文里的字面命令结构上无法被机械守** — 验证方式：推演测试可行性；
  **证据锚**：要测「SKILL 里写的命令是否仍对」必须先从 markdown 里提取命令 = 解析 markdown（基准 5
  禁手搓无界语法面）⇒ 「写进 SKILL 散文」这个方案**结构上排除了机械守**，只能靠下一次 dogfood 误停
  一轮评审才发现（本次即该路径）
- **C6 探测产物自身缺失，本身即最强的 bundle 陈旧信号（鸡生蛋自解）** — 验证方式：推演旧 bundle 场景；
  **证据锚**：旧 bundle 无版本文件 ⇒ SKILL 读不到 ⇒ 该缺失**正是**「bundle 陈旧（从没跑过新版 update）」
  的判定结果，语义自洽且比内容信号更早触发；与 `resolve-models.sh` 的 `[ -x ]` 预检同 idiom
  （`sdflow-code-review/SKILL.md` 第零步已有先例）。〔本条原为 `skew_probe.sh` 而立，D2 改用版本对比后
  论证同样成立，故保留并改述——判据形状不变：产物缺失 = 陈旧〕
- **C7 本仓已有同款 manifest 模式，但只覆盖了两条分发链中的一条** — 验证方式：读实际落盘文件 + SKILL 自述；
  **证据锚**：`~/.sdflow/hack/capability-manifest.json` 实内容为
  `{"entries": {"outside-voice-job.py": "28dbed6d…", "outside-voice.sh": "8e8742c3…",
  "skill-principles.md": "ed61e1e2…"}, "generation": "41183542…", "schema_version": 1}`（`setup.sh` 所写，
  供 `outside-voice-job.py preflight` 检 skew）；而 `sdflow-code-review/SKILL.md:557` 明写
  「两条分发链不可互相替代……**capability manifest 正是在这一步写**；消费仓的 `openspec/workflow/tools/`
  走 `sdflow-init update`」⇒ **hack 链有 manifest、bundle 链没有**，缺的那半才不得不用四条手工内容信号补。
  ∴ D2 不是新造机制，是把已有模式补全到另一条链
- **C8 `setup.sh` 已在算版本，但只打印未落盘** — 验证方式：读源码；
  **证据锚**：`setup.sh:735` `version="$(git -C "$REPO_DIR" describe --tags --always --dirty 2>/dev/null || echo "unknown")"`
  ——仅用于汇总打印，没有写进 `~/.sdflow/` 供消费方比对（D3 另定改用纯 SHA，故此处不复用其 describe 形式，
  只复用「取版本 + `|| unknown` 降级」这一 idiom）

### 〔重开相位 B · 2026-08-06 · 由 spec-review-report F1/F2/F3 触发〕

- **C9 全局 canonical 恒指向「活 checkout」，两平台皆然；但「canonical 与 SKILL 同代」只在 Unix 成立** —
  验证方式：读 `resolve-workflow.sh` 步 2 + 读 `setup.sh` 两处安装分支 + 实测 readlink；**证据锚**：
  ① canonical 侧两平台一致：`~/.sdflow/hack/resolve-workflow.sh:56-66` ——Unix 走
  `[ -d "$SDFLOW_HOME/workflow" ]`（软链透明命中，实测 `readlink ~/.sdflow/workflow`
  → `~/.skills/sdflow-skills/sdflow-init/assets/workflow`），Windows 读 `workflow-path` 指针文件
  （`setup.sh:489` `printf '%s\n' "$bundle"` 存的**也是活 checkout 路径**）⇒ 两条路径都解析到
  **运行 checkout 内的文件树本身**，是实时而非快照；
  ② **SKILL 侧两平台不对称**：`setup.sh:163` Unix `ln -snf`（软链，与 canonical 同一 checkout ⇒
  `git pull` 一次两者同时变）vs `setup.sh:119` Windows `cp -r`（**拷贝，setup 时快照**）。
  ∴ **Unix**：全局侧不存在需要被探测的失鲜轴，D4 的全局侧那一半失去被保护的对象（本条支撑 D9）。
  **Windows**：canonical 实时而 SKILL 是快照 ⇒ 「旧 SKILL × 新 tools」是真实面，且方向与 proposal
  原描述相反。该面不被 D9 判据覆盖（判据只比 pin 副本 vs canonical，看不到 SKILL 侧）⇒ 见 D12。

- **C10 消费仓 `openspec/workflow/` 副本只在 `local-pin` 时参与评审执行；非 pin 仓它是纯死件** —
  验证方式：读 resolver pin 判据 + 三仓实测 + 全仓调用点 grep；**证据锚**：
  ① `resolve-workflow.sh:38-51` pin 判据只看 `workflow.md`/`spec-checklists/`/`code-checklists/`，
  注释明写「不查 `openspec/workflow/` 目录——`tools/` 使其恒存在」；
  ② 实测三仓：`04-sdflow-skills`=global-canonical、`10-michi`=global-canonical、`05-sarvelo`=local-pin；
  ③ 全仓 grep `RULES_ROOT` 只落两个评审 SKILL + `sdflow-roadmap/SKILL.md` + `hr_tg_intersect.py`，
  `openspec/workflow/tools/` 的硬编码引用全部属于 **ship_gate 失鲜判定 / hack 测试 / docs / specs**，
  **无一条是评审运行时的工具执行路径**。
  ∴ 对非 pin 仓，版本对比既拦不住真 skew（结构上不存在，见 C9），又会因一个不被读的副本硬停。

- **C11 「实际部署集」不是 tools+contract+guide 三件，`copy_bundle` 还铺 `openspec/schemas/<PROJECT_SCHEMA>`** —
  验证方式：读 `copy_bundle` 全文 + 三仓落盘实况；**证据锚**：`sdflow-init/scripts/init.py:278-288`
  （`include_schema` 默认 True ⇒ 拷 `assets/schemas/sdflow-spec-driven` → 消费仓 `openspec/schemas/`）；
  实测 `04-sdflow-skills` 有 `openspec/schemas/sdflow-spec-driven`，而 `10-michi`/`05-sarvelo` **无**
  （且 `10-michi` 有 tools+contract 但**无** `WORKFLOW-GUIDE.md`）⇒ 三仓落盘形态互不相同。
  ∴ **「部署集清单」本身是一个会随版本增删的活物**——把它硬编码进探测器，就是把补丁螺旋从
  「每加特性补一条信号」搬成「每加一个部署项补一行清单」，形状未变（基准 5 警号）。

- **C12 `trigger-catalog.md` 既是「pin 有意冻结的规则」又是「tools 的机读输入」⇒ pin 仓的规则/工具异代
  是 pin 语义内建的，不是「忘了 update」** — 验证方式：grep 机读消费点 + 读 `copy_bundle` 拷贝集 + pin 仓实况；
  **证据锚**：① `sdflow-code-review/SKILL.md:296`、`sdflow-spec-review/SKILL.md:208` 均以
  `--trigger-catalog $RULES_ROOT/trigger-catalog.md` 传参，`anchor_lint.py` 调用处（`:418`/`:271`）同样传；
  `hr_tg_intersect.py:184` help 明写「HR-TG 单一源，禁 `__file__` 推导」⇒ **它是机读输入不是纯人读规则**；
  ② `init.py:253-278` 非-full 分支**只拷** `tools/` + `lens-metric-contract.md` + `WORKFLOW-GUIDE.md`，
  **不拷 `trigger-catalog.md`**（它属规则层，pin 仓故意冻结）；
  ③ 实测 `05-sarvelo` 有 `trigger-catalog.md`（mtime Jun 29 2026）但**无 `tools/`、无 `lens-metric-contract.md`**。
  ∴ 「新 tools × 旧 trigger-catalog」在 pin 仓是**设计后果**，把它纳入 skew 比对面 = 让每个 pin 仓永久硬停 = 取消 pin。

- **C13 `lens-metric-contract.md` 与 `tools/` 同批刷新，二者恒同代；`WORKFLOW-GUIDE.md` 是纯人读产物** —
  验证方式：读 `copy_bundle` 非-full 分支三处 `copy2` 及其注释；**证据锚**：`init.py:266-278`
  ——contract 注释「是 `tools/anchor_lint.py` 的运行时机读依赖……须与 `tools/` 同批刷新」；
  guide 注释「【给人看的】完整手册……人需要一份不用跳文件的完整参考」。
  ∴ 比对面纳入 contract 是必需（机读）、纳入 guide 是纯仪式（陈旧无害，且正是 F3「改一句措辞即硬停」的来源）。

- **C14 `ship_gate.py` 的 `tools_spec` 失鲜腿在源仓是冗余的，删副本后可整条退役、无需重新安家** —
  验证方式：读 `ship_gate.py` 两条腿的实际比较范围；**证据锚**：`sdflow-ship/scripts/ship_gate.py:947-950`
  第一条腿 `ls_tree_map(root, sha, recursive=False)` 比的是**顶层条目 → tree sha**（仅排除 `openspec`），
  而 tools 权威源 `sdflow-init/assets/workflow/tools/` 位于顶层条目 **`sdflow-init`** 之下
  ⇒ 改权威源必改 `sdflow-init` 的 tree sha ⇒ **已被第一条腿抓到**。`:955-959` 的 `tools_spec` 腿只多抓一种
  情形：**直接改消费仓镜像而不改权威源**——而该动作本就被 `CLAUDE.md:172` 明令禁止，且删掉副本后
  **文件不存在、动作不可能发生**。∴ 逻辑闭环，该腿随副本一同退役。
  🔴 **更正我在本轮第 5 问的判断**：我当时说「删副本会让该腿静默退化为恒真锚」——退化属实，但我漏了
  「它保护的东西已被顶层腿覆盖」⇒ 结论从「必须重新安家（独立设计问题）」更正为「可整条删除」。

- **C15 pin 的两个既有用途都有更干净的现成替代：`SDFLOW_HOME` 重定向** — 验证方式：读 CLAUDE.md 对 pin
  的两处承诺 + `resolve-workflow.sh` 契约；**证据锚**：① `CLAUDE.md:237`「任意仓可留规则副本形成 pin
  免疫全局翻动（逃生口）」；② `CLAUDE.md:226-228` 开发期测试第 2 层「把规则副本拷进沙盒仓形成本地 pin
  ⇒ 全局不动」；③ `resolve-workflow.sh:8` 契约**已明写** `env: SDFLOW_HOME（缺省 ~/.sdflow；测试用它
  重定向，绝不写真实 $HOME）`，且**第 1 层测试已在用它**。
  ∴ 两个用途改用 `SDFLOW_HOME` 指向自备 canonical 即可，**且比 pin 更真实**——测的是真正的 canonical
  解析路径（步 2），而非 pin 分支（步 1）这条即将删除的旁路。替代物无需新建，是既有正式契约。

- **C16 「规则不复制进消费仓」在 spec 里早已是定论，pin 只是 resolver 留的旁路；D13 是把同一条规则
  贯彻到 tools** — 验证方式：读现行主 spec；**证据锚**：`openspec/specs/spec-workflow/spec.md:175`
  已写「**规则**（`workflow/*.md` + `spec-checklists/` + `code-checklists/`）MUST **不再复制进消费仓**，
  改由 skills 从全局 canonical bundle 解析」；而 `:176` 写「**review 机械层脚本** SHALL 复制进消费仓
  `openspec/workflow/tools/`」。∴ D13 的 delta = **把 `:176` 从「SHALL 复制」翻转为「MUST NOT 复制」**，
  并删掉 resolver 步 1 这条让规则副本仍能生效的旁路。**不是新方向，是把已定方向做完。**

- **C17 `stale_shadow_warnings()` 与 `maintain_scan` 的规则残留检查，方向与 D13 一致且已存在** —
  验证方式：读实现 + 其 spec；**证据锚**：`init.py:346` `stale_shadow_warnings(root)`（`:1145` 消费）
  告警消费仓 `openspec/workflow/` 下残留的规则文件本体；`openspec/specs/maintain-scan/spec.md:61`
  以 `RULE_MARKERS`（`workflow.md` / `spec-checklists` / …）做同类检查。
  ∴ D13 之后二者**语义增强而非冲突**：从「警告你有副本会遮蔽全局」变成「副本不再有任何生效路径」。
  🔴 但 `init.py:1125` 的 **`--dev` 跳过该告警**（T15：dev 刻意铺规则）在 D13 后失去前提 ⇒ 见 C18。

- **C18 `--dev` / `full=True` 整 bundle 铺设在 D13 后失去用途** — 验证方式：读唯一调用链；
  **证据锚**：`init.py:1127` `copy_bundle(root, full=dev, …)`，`full=True` 的 docstring（`:231`）
  自述「**仅供 toolkit 源仓 `update --dev` dogfood 刷新 instance 用**」。D13 后源仓 dogfood 同样走
  全局 canonical ⇒ 无需本地 instance ⇒ `--dev`、`full` 分支、以及 T15 为它开的
  `stale_shadow_warnings` 豁免（`:1125`）三者可一并退役。**此项属 D13 的落地清单，非独立决策。**

## 接受的边角

- **Windows 上「旧 SKILL × 新 tools」不被任何机制覆盖** — 见 D12①。根因：Windows 无 symlink，
  `setup.sh:119` 用 `cp -r` 装 SKILL ⇒ SKILL 是快照而 canonical 指活 checkout。**完美成本不是"高"是"死结"**：
  检查者只能是 SKILL 自己或 `~/.sdflow/hack/` 的 helper，二者同为一次 `cp -r` 的产物，没跑 setup 就一起旧。
  **为何接受**：无可自举的检查位置；且本仓对 Windows 分支结构性无测试面
  （`hack/tests/test_install_agents.py:14` 自述）。⇒ proposal 与 delta spec MUST 各写明此边界。
- **消费仓 `WORKFLOW-GUIDE.md` 可能陈旧** — D14 保留铺设的直接后果。影响：低（纯人读、不参与执行、
  不被任何脚本机读）；**为何接受**：它的价值正是"随仓走、不用跳文件"，为它建新鲜度机制会把
  D13 刚消灭的那类问题原样请回来。

## 三镜代价

命中 TG-23（≥2 合理方案），书面写满。**第二轮候选集**：①按症状层求精确（pin-only 字节比对，即 D9–D11）
②本方案（消灭双链，D13）③维持现状 + 只修 grep 写法（原 T270 口径）。

- **系统镜**：**净删除远大于净新增**——删 `resolve-workflow.sh` 步 1（pin 判定）· 删 `init.py` 的
  tools/contract 拷贝与 `--dev`/`full` 分支（C18）· 删两个评审 SKILL 的 skew 探测段 · 删 `ship_gate.py`
  的 `tools_spec` 腿（C14）· 删本仓 `openspec/workflow/` 下 7 个文件。**新增为零**——pin 两用途改用
  既有正式契约 `SDFLOW_HOME`（C15），不新建任何机制。可回退（改动集中且都是删除，revert 即复原）。
  代价：`openspec/specs/spec-workflow/spec.md:176` 的 Requirement 需从「SHALL 复制进消费仓」翻转，
  是**契约级改动**，需 delta spec 明写。
- **用户镜**：消费仓侧**再无任何「先跑 `sdflow-init update` 才能评审」的硬停**——该仪式连同它的
  误报风险一起消失。代价：pin 作为"免疫全局翻动"的逃生口不再存在，需要隔离的场景改用 `SDFLOW_HOME`
  （一个环境变量替一堆拷贝文件，但**是使用方式的改变**，CLAUDE.md 开发期测试三层第 2 层须同步改写）。
- **开发循环镜**：「新增 bundle 特性要不要补探测信号」这个问题**整个消失**（无探测器）；
  `sdflow-init update` 的职责收缩到 GUIDE + schema 两项，其收敛性/事务性顾虑随之消失。
  代价：开发期测试第 2 层的做法要重写（pin ⇒ `SDFLOW_HOME`），是一次性文档成本。
- **主次判定**：**系统镜为主**——本方案的全部价值在于**消灭被探测的对象本身**，而非把探测做准；
  开发循环镜次之（终结整类问题）；用户镜为附带收益（少一道仪式）。

## 设计门前修订纪要〔spec-review-amendment · 2026-08-07〕

> 本节为阶段二评审（`spec-review-report.md` + `gstack-review.md`，对 commit `0f8b0a3` 盘面）后、
> 经人同意的修订登记。上文 D1–D16 / C1–C18 的原文**不回改**（本 memo 是决策日志）；与本节冲突处
> 以本节为准，四件套正文已按本节重写。

### 新增拍板决策

- **D17（Q4）｜不立「规则版本冻结」承诺** — `SDFLOW_HOME` 保持既有测试隔离契约（`resolve-workflow.sh:8`），
  delta 撤销「冻结的唯一受支持路径」SHALL 与对应 Scenario。依据：唯一存量 pin 仓（05-sarvelo）实际
  诉求是跟最新；该 env 同时是 `setup.sh:468` 安装根（自毁形态 F4）；为无人要的能力立做不到的 SHALL
  比不立更坏。开发期测试三层第 2 层用既有隔离契约即可改写，无需冻结承诺。C15「pin 两用途改用
  SDFLOW_HOME」修订为「测试隔离走既有契约；冻结不立承诺」。
- **D18（Q2）｜存量死件清理不写自动代码** — 告警附可复制删除命令，人一次执行即达终态零死件。
  依据（④五问）：收益规模 = 本机个位数仓 × 一次；为此在 `init.py` 永久留一段一次性 `rmtree` 迁移
  逻辑 + 测试，持久复杂度与一次性收益倒挂。安全红线（不自动删）因此完全不被触碰。
- **D19（Q3）｜删除 `adr/0038`** — 本分支新建（`164bb88`）、从未进 main、其版本对比机制从未实现；
  born-superseded 的 ADR 只会误导未来读者。候选与砍因并入 0039 取舍段，引用砍因 MUST 写「起手前提
  被证伪 ⇒ 决策撤销」，MUST NOT 写「问题域消失」（F32）。

### 事实订正（评审证伪的 memo 陈述，读旧文时以此为准）

- **F1**：D12/design 附带说明称「hack 链由 capability-manifest 独立守」——**错**。`MANIFEST_ENTRIES`
  仅 3 项（`outside-voice-job.py:201`），不含 `resolve-workflow.sh`，且仅 codex 后台 voice preflight
  消费。hack 链目前**无守**，登记诚实边界；根因项（hack 链 symlink 化）记 todo。
- **F48**：「本仓对 Windows 分支结构性无测试面」（接受的边角 · D12①）——**过度**。准确表述：运行时
  自检不可能（论证成立）；CI 层可测但目前未测（`windows-recorder-smoke.yml` 在 windows-latest 跑
  全量 pytest，触发 paths 覆盖本 change 全部脚本面）。
- **F49**：「消费仓副本是 skew 的唯一成因」——收窄为「bundle 拷贝链 skew 的成因」；hack 拷贝链与
  Windows SKILL 快照两个失鲜面仍在。
- **F26**：encoding 排除分支「镜像消失后才成死码」——**错**。`TARGET_GLOBS` 全 root-anchored，该分支
  现在就已不可达；本 change 是顺带清既存死码，其守卫用例是恒真锚。
- **A12**：C 组「其余 tools 未验 fail-closed」前提**已结**：6 tool 全 argparse `required=True`，
  运行时读版本化输入的 3 个（anchor_lint→contract · lens_metric_emit→contract ·
  hr_tg_intersect→trigger-catalog）均 fail-closed。
- **A5**：`sane()` 扩面进 scope，但 MUST 形状级判据（tools/ 非空 + contract 非空），MUST NOT 成员
  清单（防守卫内复活补丁螺旋）。
- **验收模型**：改为三条闭环判据（概念词表 sweep 归零 + 全仓 pytest 绿含 4 反向锚 + 三态真跑），
  BASE-29 scope-check 表落 design、由 sweep 产出。
- **D14 追加（人已确认）**：GUIDE 保留铺进消费仓不变；其生成器把 sibling 相对链接降为文字引用
  （F45——6 条断链会击穿 D14 的保留理由）。
