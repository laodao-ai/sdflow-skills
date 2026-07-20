## Why

`ship_gate.py` 判定「评审结论是否已失鲜」时，靠调 `git` 枚举锚提交之后的改动。**这一层调用有四个已复现的缺陷，其中三个是 fail-open**——门在该拦的时候放行。

`fix-design-gate-freshness-proxy` 已把 **design 域**的枚举协议换成 `git diff-tree -m -r --raw --no-renames -z --root`；**code 域一行未动**，仍是老协议 `git log --name-only`，同一批洞原样留存。这不是"还差最后一个 case"，是**同一片面只治了一半**。

〔grill-amendment〕grill 期实测又揪出**第五个缺陷，且它在 design 域已经上线**：`-m` 输出 merge 相对**每个 parent** 的 diff，而 parent2 通常**早于锚提交** ⇒ 整条分支在锚**之前**的工作被当成「本帧触及路径」重报 ⇒ **例行「把 main 合进 feature 分支」即误判失鲜**。实测：侧支只碰 `openspec/changes/c/notes.md`、锚后四件套一字未动，design 域仍判 `stale` → `REFUSE_START`。正解 `--cc`（只报相对**所有** parent 都不同的文件 = merge 自身引入的内容）。同一原语面 ⇒ 按基准 4 fold 进本 change，不另开循环。

同一轮 grill 推翻了本 change 的起手式：**「两域共用一份枚举实现」被当成目标写进了 Goals，但两域问的不是同一个问题**——design 域要 per-commit 判豁免（必须逐帧），code 域只要「现在的树 vs 被审过的树」（状态比较，与拓扑无关）。决策与实证落 `openspec/adr/0026`。

触发 TG：**TG-17**（HR-TG）· TG-14 · TG-18 · TG-19 · TG-22 · TG-23。

## What Changes

### P0 — code 域失鲜判据的 fail-open（安全面）

〔grill-amendment〕**按消费方要回答的问题选原语，MUST NOT 为「统一」而统一**（adr/0026）：

- **code 域改用累积 diff** `git diff --raw --no-renames -z <锚> HEAD`——它问的是「现在的树和被审过的那棵，在 `openspec/` 之外有没有差别」，是状态比较，零豁免、零 subject 判断、与提交拓扑无关，一次调用答完。三个 fail-open 由此**结构性关闭**（merge 拓扑不参与、rename 天然分解成 A+D、失败只剩一个 rc）。
- **design 域保留逐帧**（BR-7 是 per-commit subject 判断，必须逐帧），但 `-m` 换 `--cc`，修上线中的假阳。
- **MUST NOT 把 design 的补丁照抄进 code 域**——两域谓词方向相反（design = 命中白名单才管；code = 不在 `openspec/` 下就管），逐条判方向的结论见下表。

| 老协议缺陷 | design 域 | code 域（本次） |
|---|---|---|
| merge 提交不产 diff | 🔴→✅ 已修 | 🔴 **fail-open**，已复现 |
| rename 只报目标路径 | 🔴→✅ 已修 | 🔴 **fail-open**，已复现（仅「码→`openspec/`」方向） |
| 枚举失败折成空串 | 🔴→✅ 已修 | 🔴 **fail-open** |
| **`-m` 过报锚前历史** | 🔴 **fail-closed 假阳，已上线** 〔本次 fold，改 `--cc`〕 | 🟢 不适用（累积 diff 无帧） |
| 控制字符路径被 C-quote | ✅ `-z` 后正确解析 | 🔄 **方向反转**：`-z` 后判 fresh，**这是正解**（详下） |

**控制字符那格 MUST 读完再实现**〔grill-amendment〕：初稿把 code 域现状的 fail-closed 当成「本就正确、MUST NOT 改动」。实测证伪——那个 fail-closed 是**字符串被 C-quote 弄花的意外产物**（`'"openspec/…'` 带前导引号 ⇒ 前缀不匹配 ⇒ 判失鲜），不是有原则的保守。`-z` 输出原始字节、引号不存在，路径正确解析为 `openspec/…` ⇒ 判 fresh，**而文件确实在 `openspec/` 下，豁免它才对**。此反转是 `-z` 的属性，**与选哪个原语无关**（帧枚举走 `-z` 一样反转）。

### P1 — git 调用的失败路径脱离契约

- `run_git` / `run_git_rc` / `run_git_bytes` 统一捕获 `FileNotFoundError`，映射到 `UNKNOWN(6)`。
- 同三个函数补 `timeout`，超时同样映射到 `UNKNOWN(6)`。

### P2 — code 域撞门无诊断

- code 域失鲜时返回裸 `(True, 'stale')`，撞门者拿不到任何线索。补触发点诊断（哪个 commit、哪些路径、哪一类），与 design 域已有的能力对齐。

### 验证要求（贯穿全部三级）

每条新增守卫 MUST 附**变异证明**：删掉该守卫 ⇒ 对应用例变红。上一轮的 rename 用例只直接调 `blob_pair`、没走 `is_stale`，因此**在真实洞存在的情况下仍是绿的**——这是本项要求的直接实证来源，不是形式主义。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `spec-workflow`: 失鲜判定的枚举协议要求从 design 域推广为**两域统一**；新增 code 域 fail-open 的禁止性要求、git 调用失败的退出码契约、code 域诊断要求。

## Impact

- **代码**：`sdflow-ship/scripts/ship_gate.py`（`run_git*` 系列、`is_stale` 的 code 分支、帧枚举 helper）
- **测试**：`sdflow-ship/tests/test_gate_freshness.py`（新增 code 域三个 fail-open 用例 + 各自变异证明）
- **行为变更**：此前被判 `fresh` 而放行的三类盘面，今后判 `stale` → `REFUSE_START`。**这是修复不是回归**，但在途 change 若正处于这三类盘面之一，升级后会撞门并需重跑代码审。
- **消费方**：本仓为 toolkit 源仓，改动经 push → 各仓 `/sdflow-upgrade` 后生效。
- **不影响**：design 域判定逐字不变（本次只抽共用源，不改其语义）。

## 需求优先级〔BASE-23 · TG-19〕

| 级 | 项 | 依据 |
|---|---|---|
| **P0** | code 域三个 fail-open | 安全面：代码审拍板后的源码改动可绕过二次审查随档 ship。已复现 |
| **P0** | design 域 `-m` 过报假阳 → `--cc`〔grill-amendment〕 | 可用性面但同属安全原语：例行 merge 即误判 `REFUSE_START`，已上线、已复现。同一原语面 ⇒ fold（基准 4） |
| **P1** | `FileNotFoundError` + `timeout` → `UNKNOWN(6)` | 可用性面：退出码脱离契约集致链序误判语义；无 timeout 致 gate 无限阻塞。已复现/已核实 |
| **P2** | code 域触发点诊断 | DX 面：不影响判定正确性，只影响撞门后能不能自救 |

P0 是本 change 的存在理由；P1 与 P0 同处 git 调用层，分开做要付两遍 workflow 循环成本，故合并（基准 4）。P2 是同面的顺手补齐（基准 3）。

## 假设列表〔BASE-14 · TG-22〕

| # | 假设 | 已验证？ | 若不成立 |
|---|---|---|---|
| A1 | code 域 evil-merge 与 rename 两洞真实存在 | ✅ 本地构造仓复现，真调 `is_stale` 返回 `(False,'fresh')` | — |
| A2 | git 缺失时 gate 退出码为 1、脱离契约集 | ✅ `PATH=/nonexistent` 实测 exit=1 | — |
| A3 | `run_git*` 三处 `subprocess.run` 均无 `timeout` | ✅ 源码核实，零 `timeout=` | — |
| ~~A4~~ | ~~控制字符路径在 code 域是 fail-closed（不必改）~~ | ❌ **grill 实测证伪** — 见上表「控制字符」格。老 fail-closed 系 C-quote 弄花字符串所致；`-z` 后判 fresh 才是正解。**Requirement 2 已按新方向重写** | — |
| A5 | 失鲜判定只有 design/code 两个 scope | ✅ 但**消费方是三个不是两个**〔grill-amendment，初稿写「无第三消费方」有误〕：`:1214` design（spec-review-report）、`:1291` code（code-review-report）、`:1311` code（**verify-report**）。承 adr/0011「MUST grep 列全调用点、不得凭记忆枚举」 | 三消费方同谓词，修法一致；但**测试覆盖不一致**（见 A7） |
| A6 | design 域语义在换 `--cc` 后，除「例行 merge 不再假阳」外逐字不变 | ❌ **待实现期以现有 design 域全部用例回归证明**〔grill-amendment：口径由「抽共用源后逐字不变」改为「除假阳修复外不变」——`--cc` 是行为修复，不是等价重构〕 | 若另有语义变动则须回滚重做 |
| A7 | code 域现存测试覆盖 | ✅ **仅 1 个用例**（`test_gate_freshness.py:996`），且用的是第三个消费方 `verify-report` ⇒ **`code-review-report` 那条路径今天零覆盖**〔grill-amendment〕 | — 改写爆炸半径近乎零，但须为 `code-review-report` 补首个用例 |
| A8 | 累积 diff 对「改了又改回去」判 fresh、对 amend 成孤儿的锚判 fresh | ✅ 实测。二者均为**正确**（树等值 ⇒ 无新内容会被 ship；改报告错别字不该要求重跑代码审），但**是行为变更、非等价重构** | 若判错则须回退到范围语义 |

## 开放问题

无。`timeout` 具体秒数属实现期可判项（有客观判据：现有 git 调用均为本地元数据查询，量级明确），走 T10 ①。

## Non-Goals

- **T189**（`_normalize_checkbox_lines` 口径反转为白名单）——属**内容豁免面**，与本次的 **git 枚举面**是两片面。混进来会让本 change 同时动两个不相干的判据，违反「一个 change 一个完整阶段结果」。
- **B18**（`maintain_scan.py` 的 `find_repo_root`）——属仓根解析面。
- 不改 design 域的任何判定语义（含 BR-7 subject 豁免、内容豁免、其优先级）。
