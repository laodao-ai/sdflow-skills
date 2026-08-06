## Context

见 [`proposal.md`](./proposal.md)「Why」。设计所需的现状事实（均已实查）：

- **两条分发链**：`sdflow-code-review/SKILL.md:557` 明写「两条分发链不可互相替代：全局 helper 与
  SKILL 走 `bash setup.sh`（**capability manifest 正是在这一步写**）；消费仓的
  `openspec/workflow/tools/` 走 `sdflow-init update`」。
- **hack 链已有 manifest**：`~/.sdflow/hack/capability-manifest.json` 实内容为
  `{"entries": {...三项 sha256...}, "generation": "...", "schema_version": 1}`，由 `setup.sh` 写、
  `outside-voice-job.py preflight` 消费。**bundle 链无对应物** ⇒ 只好用手工内容信号补。
- **`setup.sh:735`** 已在算 `git describe --tags --always --dirty`，但**仅用于汇总打印、未落盘**。
- **`init.py` 的 `copy_bundle(root, full=False, include_schema=True)`**（`:229-295`）两分支共用一个出口；
  调用点在 `:1127`（`copy_bundle(root, full=dev, include_schema=schema_enabled)`）。
  〔spec-review-amendment：原写签名 `copy_bundle(root, full=dev)`（漏 `include_schema`）、行号 `:228-286`，
  均与实际不符，已按实读订正〕
- **现有探测段**：`sdflow-code-review/SKILL.md:206`（四信号）、`sdflow-spec-review/SKILL.md:180`
  （信号①②，描述与前者逐字相同）。
- **仓根 `openspec/workflow/tools/` 有真消费方**：`ship_gate.py:953-955`
  `tools_spec = (b"openspec/workflow/tools/",)`，参与 code 域失鲜判定 ⇒ 不可清理。

### 消费点依赖图（改动面一览）

```
版本产出侧
  ├─ setup.sh（刷 canonical 时）────────▶ 全局侧版本落点
  └─ init.py copy_bundle()（内部）──────▶ 消费仓 openspec/workflow/ 版本落点
        └─ 两分支：full=True（源仓 --dev 整刷）· full=False（消费仓常规 update）

版本消费侧
  ├─ sdflow-code-review/SKILL.md 第零步 ─▶ 删四条内容信号，换版本对比
  └─ sdflow-spec-review/SKILL.md 第零步 ─▶ 删两条内容信号，换版本对比（同一判据，两处措辞一致）

机械守
  └─ hack/tests/ ─▶ 两处写入点真写了版本 + 相等/不等/缺失三态判定

不动（Non-Goals，显式登记防误改）
  ├─ ~/.sdflow/hack/capability-manifest.json 及其 preflight（hack 链，与本 change 并存不合并）
  ├─ openspec/workflow/tools/（ship_gate 消费方）与 lens-metric-contract.md / WORKFLOW-GUIDE.md
  └─ init.py 的 bundle 拷贝范围（不为源仓/消费仓分叉）
```

## Goals / Non-Goals

**Goals（设计级边界）**：判据形式替换对**语义契约零改动**——fail-loud 强度、硬停时点（任何 fan-out /
调 emitter / 落 v2 锚之前）、报错须 actionable，三者均保持既有形状，只换判据来源。

**Non-Goals**：见 proposal；另加设计级两条——不改 `ship_gate.py`（`tools_spec` 判定不受影响）；
不改 `outside-voice-job.py preflight` 的 manifest 消费逻辑（两条链各管各的）。

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)；
判据本身的长期依据见 [`adr/0038`](../../adr/0038-bundle-skew-detected-by-version-not-capability-probes.md)。

## 设计细节

### 1. 版本取值与形式（D3/D6）

```bash
git -C <checkout> log -1 --format=%H -- sdflow-init/assets/workflow/
```

- **bundle 作用域，非整仓 HEAD**：实测 `git rev-parse HEAD`=`0d024ae`（该 commit 改的是 `setup.sh`）
  而 bundle 版本仍为 `ee5b4f4` ⇒ 用 HEAD 会让源仓每提交一次就得 update 一次才能评审，方案会因烦人
  被绕过。bundle 作用域精确匹配「bundle 是不是旧的」这一探测语义。
- **纯 40 位 commit SHA，MUST NOT 用 `git describe --dirty`**：开发时工作树常脏，`-dirty` 后缀会让
  版本恒不相等、天天误报。
- **非 git / 命令失败 ⇒ 字面 `unknown`**：沿用 `setup.sh:735` 现有 `|| echo "unknown"` idiom。

### 2. 两个落点（D4/D7）

| 侧 | 落点 | 写入方 | 时机 |
|---|---|---|---|
| 全局 | `~/.sdflow/bundle-version` | `setup.sh` | 刷 canonical 软链的同一步 |
| 消费仓 | `openspec/workflow/.bundle-version` | `init.py` 的 `copy_bundle()` | 拷贝 bundle 的同一函数内 |

- 单行纯文本（SHA 或 `unknown`），末尾换行。**不复用 `capability-manifest.json`**——那是 hack 链的
  载体、语义不同，混入会让一个文件承两个职责。
- 🔴 **`init.py` 的写入 MUST 放在 `copy_bundle()` 函数内部**，不放调用点（`:1127`）：两分支
  （`full=True` 源仓 `--dev` 整刷 / `full=False` 消费仓常规）共用该出口，放调用点会漏掉 `--dev` 路径，
  导致源仓铺完没版本文件、**反被自己的探测判成陈旧**。
- **消费仓侧落点选 `openspec/workflow/.bundle-version`**（而非 `openspec/` 根）：与它描述的对象同目录，
  且随 `tools/` 的 update 覆盖语义一起走；点号前缀避免与 bundle 内容文件混淆。

### 3. 判定逻辑（D5/D8）

两个评审 SKILL 第零步的 skew 探测段统一为：

```
读全局侧版本 G = cat ~/.sdflow/bundle-version
读消费仓侧版本 L = cat <repo>/openspec/workflow/.bundle-version
```

| 情形 | 判定 | 处置 |
|---|---|---|
| G、L 均存在且**相等** | 同步 | 放行，进第一步 |
| G、L 均存在但**不等** | bundle 陈旧 | **硬停**，文案含「跑 `sdflow-init update`」 |
| **任一缺失** | 陈旧（从没跑过新版写入方） | **硬停**，文案分别指向 `bash setup.sh` / `sdflow-init update` |
| 两者**同为 `unknown`** | 非 git 环境 | **放行**（fail-open，与 `setup.sh:735` 降级一致） |

- **缺失即陈旧**（C6）：语义自洽——从没跑过新版 update 的消费仓正是陈旧态；与第零步
  `resolve-models.sh` 的 `[ -x ]` 预检同 idiom。
- **不等即硬停、不降级为警告**（D8）：硬停发生在起手（尚未 fan-out、未跑 voice），损失仅为重新起手；
  放行的代价是整轮白跑。方向上宁可多报。
- **两处 SKILL 的判定措辞 SHALL 一致**——同一判据，MUST NOT 各写一套（现状①②逐字重复已是漂移面，
  本 change 收敛为同一段）。

### 4. 删除面（面治，基准 3）

- `sdflow-code-review/SKILL.md` 第零步 skew 段：**四条内容信号整段删除**（含本 change 上游
  `absorb-gstack-review` 刚加的③④），换为上表判定。
- `sdflow-spec-review/SKILL.md` 第零步 skew 段：**两条内容信号整段删除**，换为同一段判定。
- 🔴 删除时 MUST 保留该段既有的**语义契约措辞**：fail-loud、硬停时点、「MUST NOT 产出无锚报告 /
  MUST NOT 落 v1 旧锚（假绿）/ MUST NOT 静默清零本段」——这些不随判据形式改变。

### 5. 机械守（C5 的正解）

新增 pytest（落 `hack/tests/`，沿用 `test_install_agents.py` 的假 HOME 真跑模式）：

- **写入点存在性**：`setup.sh` 跑完后全局落点有内容且形如 40-hex 或 `unknown`；
  `init.py` 的 `copy_bundle()` 在 `full=True` / `full=False` **两分支**跑完后消费仓落点均有内容。
- **三态判定**：构造相等 / 不等 / 缺失三种盘面，断言判定结果符合上表。
- **诚实边界**：判定逻辑写在 SKILL 指令层（由主 session 执行），测试守的是**两个写入点与版本取值
  命令**这两个机械面；「SKILL 是否真的照判定表执行」仍是指令层约束、由执行方自报，
  **MUST NOT 声称机械保证**。这与现状相比是净增益——现状连写入点都没有，整条路径零机械覆盖。

### 6. 文档订正（T269 的落点）

`CLAUDE.md` 中「`openspec/workflow/`（仓库根）— **只保留 `tools/`**」订正为实际形态，并写明各自理由：
`tools/`（`ship_gate` 参与 code 域失鲜判定的真代码）+ `lens-metric-contract.md`
（`anchor_lint.py` 的运行时机读依赖，须与 tools/ 同批刷新）+ `WORKFLOW-GUIDE.md`（人读手册）
+ 本 change 新增的 `.bundle-version`。**目的是让下一个人 `grep` 到它们时不再误判为死件**。

## Risks / Trade-offs

- [版本不等未必真不兼容 ⇒ 误报] → 明确接受：误报成本 = 起手硬停一次 + 一次秒级 update；漏报成本 =
  整轮评审白跑。方向上宁可多报。见 adr/0038 Consequences。
- [手改部署副本不回灌探测不到] → **现有内容信号同样探不到**，未引入新洞；为它加内容指纹会绕回本
  change 要消灭的形状。已由 `CLAUDE.md:172` 明令覆盖。
- [本 change 同改 SKILL 与 bundle，自身发布即处于 skew 窗口] → 发布纪律沿用既有 push → pull →
  **立即** `setup.sh`；消费仓 `sdflow-init update`。**本 change 合并后首次评审必然硬停一次**
  （消费仓尚无版本文件）——这是设计内的 fail-loud，hand-off 须写明。
- [两个 SKILL 的判定段措辞漂移] → 收敛为同一段措辞；未来若再分叉，可考虑等值门（本仓已有
  `check_async_branch_parity.py` 先例）——**本次不加**，避免为尚未发生的漂移预付成本（基准 4）。

## Migration Plan

1. 单 change 内一次完成：两处写入 + 两个 SKILL 判据替换 + pytest + CLAUDE.md 订正 + 关闭 T269/T270。
2. 发布：merge 后运行 checkout `git pull` + **立即** `bash setup.sh`（写全局侧版本）；
   各消费仓 `sdflow-init update`（写消费仓侧版本）。**在消费仓跑 update 之前，其评审起手会硬停并
   给出该指引**——设计内路径。
3. 回滚：单 commit revert + 重跑 `setup.sh` / `update`；版本文件残留无害（无消费方即被忽略）。

## Open Questions

无——三条边界（版本形式 / 比对双方 / 非 git 降级）与 bundle 作用域取值均已在相位 B 拍板，见 memo D3–D6。

## Compliance

- 遵守 DOC-1（正文即最终态，四条内容信号的历史不留正文——其存在理由与被替换的原因写在 adr/0038）；
  premise-verification（本设计引用的 file:line 均实查）；机械化优先基准（版本对比即确定性信号，
  写入点可机械守）；**基准 5**（本 change 的核心动因即终止无界内容探测的补丁螺旋）。
- 托管区块（`sdflow:principles` / `sdflow:tier-resolution` / `sdflow:async-branch`）零触碰——
  改的 skew 段在三者 marker 之外。
- 无豁免项。
