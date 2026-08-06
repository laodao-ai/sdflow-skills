## Why

评审工具分两条**更新速度不同**的分发链：SKILL.md 走 symlink（`git pull` 即生效），
`openspec/workflow/` 下的 tools 与契约走拷贝（须 `sdflow-init update`）。二者不原子 ⇒ 存在
「新 SKILL × 旧 tools」窗口。不在起手拦下，整轮评审（多镜 fan-out + 跨模型 voice）会在**末步**
lint 才 fail-closed，成本全部报废。

此前的拦法是**逐能力内容探测**——两个评审 SKILL 的第零步各写一段散文，列举若干条「打开某文件、
grep 某字符串」的检查（`sdflow-code-review` 四条、`sdflow-spec-review` 两条，其中①②逐字重复）。
该形状有三个已实证的问题：

1. **它是补丁螺旋**。每给 bundle 加一个特性就补一条信号——`absorb-gstack-review` 刚补了③④两条。
   命中 CLAUDE.md 基准 5 的警号：「每轮都在同一处补一个新分支 ⇒ 这个东西本来就不该存在」。
2. **它结构上无法被机械守**。SKILL 只描述「检查什么」不给命令，实施者各自发挥；而验证「SKILL 里写的
   检查还对不对」需先从 markdown 抠出命令 = 手写 markdown 解析器，撞同一条基准 5。∴ 探测写法失效时
   **无任何机制报警**，只能等下次评审误停才被发现。
3. **实证误停**。`absorb-gstack-review` 的 dogfood 首跑，信号②用
   `sed -n '/```lens-metric-enums/,/```/p'`（无行首锚定）提取机读块，命中了文件散文里对该 fence 名的
   一处提及，截出一段散文 ⇒ 假阴 ⇒ 差点硬停整轮评审，而 bundle 实际是新的。

同批还有一条 `T269`（清理仓根 `openspec/workflow/` 的两个「孤儿副本」）。**调研后判定为误判**：
那两个文件在消费仓是活件（`init.py` 注释写明 contract 是 `anchor_lint.py` 的运行时机读依赖、
guide 是有意为之的人读手册）；T269 抱怨的真问题是 `grep gstack` 假阳，与上面的假阴**同根因**——
都是扫描/探测写法不精确导致误判。正解是修探测，不是删数据。

## What Changes

- **bundle skew 判据整体替换**：从「逐能力内容探测」改为「**分发链版本对比**」。两条链各自在被刷新时
  写下自己的版本，探测 = 比两个字符串。版本取值为 **bundle 作用域**的
  `git log -1 --format=%H -- sdflow-init/assets/workflow/`（非整仓 HEAD），形式为纯 40 位 commit SHA
  （非 `git describe --dirty`）。判据、取值与全部边界见 [`adr/0038`](../../adr/0038-bundle-skew-detected-by-version-not-capability-probes.md)。
- **两处写入点**：`setup.sh` 刷全局 canonical 时写全局侧版本；`sdflow-init` 的 `copy_bundle()`
  **内部**写消费仓侧版本（放函数内以同时覆盖 full / 非-full 两分支）。
- **两个评审 SKILL 的内容信号散文整段删除**（`sdflow-code-review` 四条、`sdflow-spec-review` 两条），
  替换为版本对比 + `[ -x ]` 式缺失即陈旧判定。
- **机械守**：新增 pytest 覆盖「两处写入点真的写了版本」「版本相等/不等/缺失三态的判定」。
- **文档订正**：`CLAUDE.md` 关于仓根 `openspec/workflow/` 的描述由「只保留 `tools/`」订正为实际形态
  （`tools/` + 其运行时机读依赖 contract + 人读 guide），并写明它们各自为何在那里。
- **关闭 issues**：`T270` 由本 change 解决；`T269` 关闭为**误判**（附判定依据，不是静默丢弃）。

## Capabilities

### New Capabilities

（无——本 change 替换既有 skew 判据的实现方式，不引入新的行为级能力）

### Modified Capabilities

- `host-adaptive-execution`：「落锚/调 emitter 前探 tools 能力」的**判据形式**由逐能力内容探测
  改为分发链版本对比；fail-loud 强度、硬停时点（任何 fan-out / 调 emitter / 落 v2 锚之前）均不变。

## Impact

- **代码/资产**：`setup.sh` · `sdflow-init/scripts/init.py` · `sdflow-code-review/SKILL.md` ·
  `sdflow-spec-review/SKILL.md` · `hack/tests/`（新增） · `CLAUDE.md`（订正） ·
  `openspec/adr/0038`（本 change 落）。栈标注：bash + Python 工具 + markdown 指令资产
  （命中行为面路径 bundle/SKILL.md，非 TG-01/02/03 业务栈）。
- **依赖**：无新增外部依赖。版本取值只用 `git log`（已是既有依赖）。
- **消费仓**：需跑一次 `sdflow-init update` 获得版本文件；在此之前评审起手会硬停并给出该指引
  （**这正是设计的 fail-loud 路径**，非缺陷）。
- **分发窗口**：本 change 同时改 SKILL（symlink 即时）与 bundle（拷贝惰性），发布纪律沿用既有
  push → pull → **立即** `setup.sh`；消费仓 `sdflow-init update`。

## 需求优先级

- **P0**：版本写入（两处）+ 两个 SKILL 的判据替换 + 对应 pytest——缺任一则新旧判据混态。
- **P1**：`CLAUDE.md` 措辞订正 + 关闭 T269/T270（记录一致性，独立可验）。

## Success Metrics

- 两个评审 SKILL 中**不再有任何逐能力内容探测的描述**：
  `grep -n "lens-metric-enums\|scope-audit:\|_MIRRORS_LEGAL" sdflow-code-review/SKILL.md sdflow-spec-review/SKILL.md`
  在探测段内归零（其它段落的合法引用不计）。
- 全仓 pytest 绿，含新增的版本写入与三态判定用例。
- 三态实测：版本相等 ⇒ 放行；不等 ⇒ 硬停且文案含 `sdflow-init update`；文件缺失 ⇒ 硬停。
- `openspec validate --strict` 绿。

## Non-Goals

- **不给 bundle 全文件算内容指纹**——那会把 O(1) 的版本对比变回 O(n) 逐文件校验，绕回本 change 要
  消灭的形状。「手改部署副本不回灌」探测不到是**已知且接受**的边角（现有内容信号同样探不到，
  未引入新洞），已由 CLAUDE.md:172 的明令覆盖。
- **不删仓根 `openspec/workflow/` 的任何文件**——T269 判定为误判（依据见 Why）。尤其
  `openspec/workflow/tools/` 有真消费方：`ship_gate.py:953-955` 用它参与 code 域失鲜判定。
- **不改 `init.py` 的 bundle 拷贝范围**（不为源仓/消费仓分叉）——那会给 `init.py` 加一个只为源仓
  服务的分支，且降低源仓 dogfood 的真实性。
- **不动 `~/.sdflow/hack/capability-manifest.json`** 及其 preflight 消费方——那是 hack 链的 skew
  机制，本 change 只补 bundle 链缺失的那半，两者并存不合并。
- 不改 fail-loud 强度与硬停时点（仍在任何 fan-out / 调 emitter / 落 v2 锚之前）。

## Compliance

N/A（本仓为本地开发工具链，无外部合规面）。
