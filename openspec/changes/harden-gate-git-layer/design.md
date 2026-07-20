## Context

`ship_gate.py` 的失鲜判定有两个 scope、**三个消费方**：

| scope | 消费方（调用点） | 锚 | 监视谓词 |
|---|---|---|---|
| `design` | `:1214` spec-review-report | `design_approved` | 路径落在四件套监视集内（**白名单**） |
| `code` | `:1291` code-review-report | `code_review` | 路径不在 `openspec/` 下（**黑名单补集**） |
| `code` | `:1311` verify-report | `verify` | 同上 |

`fix-design-gate-freshness-proxy` 把 design 域的帧枚举协议换成 `git diff-tree -m -r --raw --no-renames -z --root`，并抽出 `frame_touched_paths(root, sha)` 承载它。**code 域没跟上**——`is_stale` 的 code 分支仍是四行 `git log --name-only` 直判。

grill 期实测（fixture + 真 `is_stale`）确立了三件事，全部落 `openspec/adr/0026`：

1. **`-m` 会过报，造成假失鲜，且已在 design 域上线**。`-m` 输出 merge 相对**每个 parent** 的 diff，parent2 通常早于锚 ⇒ 锚**之前**的工作被当成本帧触及路径重报。侧支只碰 `openspec/changes/c/notes.md` 时 design 域仍判 `stale` → `REFUSE_START`。正解 `--cc`：例行 merge 输出 `[]`，evil merge 输出 `src.py`，`::` 三列形态在 `-z` 下被既有 `:`-前缀成对解析器原样吃下。
2. **两域不该共用原语**。design 域要 per-commit 判豁免（必须逐帧）；code 域只要「当前树 vs 被审过的树」（状态比较，与拓扑无关）。「共用」是被假设的目标，不是被推导的结论。
3. **控制字符方向反转**。`-z` 输出原始字节、无 C-quote ⇒ `openspec/` 下的怪路径正确解析为豁免。老 fail-closed 是字符串被弄花的意外产物。此反转是 `-z` 的属性，与选哪个原语无关。

一个额外事实：design 域的枚举协议**从未写进 spec**。它是代码审阶段的 `[impl-review-fix]`，那个阶段只改代码不回写 spec。∴ 目前该行为只有测试在守，需求层无约束——本 change 的 delta 一并追认并修正。

## Goals / Non-Goals

**Goals:**

- code 域的三个 fail-open 关闭；design 域的 `-m` 假阳修复。
- 每个域的枚举原语由**该域要回答的问题**决定（adr/0026）。
- git 调用的环境级失败（二进制缺失、挂起）落进退出码契约集 `{0,3,4,5,6}`。
- code 域失鲜携带触发点。
- design 域**除「例行 merge 不再假阳」外语义不变**。

**Non-Goals:**

- 不改 design 域的判定语义（BR-7 subject 豁免、内容豁免、二者优先级、监视集构成）——`--cc` 只修假阳，不动这些。
- **不追求「两域共用一份枚举实现」**（adr/0026 已否决该目标）。
- **不做 T189**（`_normalize_checkbox_lines` 白名单反转）——属内容豁免面。
- **不做 B18**（`maintain_scan.py` 仓根解析）——属仓根解析面。
- 不改 `run_git*` 的返回值形状与既有调用方契约（除新增异常映射）。
- 不引入任何第三方依赖（`ship_gate.py` 保零依赖不变量）。

## 组件清单〔BASE-25 · TG-14〕

| 组件 | 现状 | 本次动作 |
|---|---|---|
| `run_git` / `run_git_rc` / `run_git_bytes` | 三处裸 `subprocess.run`，无 `timeout`、无 `FileNotFoundError` 防护 | **修改**：统一异常映射 + 超时 |
| `frame_touched_paths(root, sha)` | `diff-tree -m …`，design 域逐帧调用 | **修改**：`-m` → `--cc`（修假阳）。仍**仅** design 域使用 |
| `code_changed_paths(root, sha)` | 不存在 | **新增**：`git diff --raw --no-renames -z <锚> HEAD`，返回路径列表或 `None` |
| `is_stale(root, rel, scope, change)` | design 分支约 50 行；code 分支 4 行 | **修改**：design 分支只换底层原语；code 分支重写为单次树比较 |
| `StaleResult` / `_stale_trigger_hint` | design 域专用的 detail 通道与渲染器 | **扩展**：code 域复用，新增 category 取值 |
| `main()` | 无顶层异常处置 | **修改**：`GitUnavailable` → `UNKNOWN(6)` 的唯一映射点 |

## Decisions

### ADR-1：按消费方的问题选原语，不抽「两域共用枚举源」

**决定**：design 域逐帧 + `--cc`；code 域单次累积 diff。两域各有一处枚举代码。

**备选（已否决）**：抽 `iter_frames(root, sha)` 作两域共用源，各域套自己的谓词（本 change 初稿方案）。

**理由**：两域问的问题结构不同（见 Context 第 2 条）。让 code 域背一套它不需要的帧循环，除了继承 `-m` 假阳，还带来 N 次 subprocess 与「`timeout` 每帧 30 秒、总量无上界」。防漂移的职责改由 spec 的**逐域 Scenario** 承担——两域正确行为本就不同（控制字符即一例），共用反而诱导「顺手统一」把方向改错。

**详细论证与实测数据**：`openspec/adr/0026`。

### ADR-2：`-m` → `--cc`，修 design 域已上线的假阳

**决定**：`frame_touched_paths` 改用 `--cc`。

**备选（已否决）**：保留 `-m`，在调用方过滤掉「parent 早于锚」的那一路输出。

**理由**：过滤方案要调用方自己重建「哪个 parent 在范围内」的拓扑判断——把 git 的语义搬进 Python 手搓一遍（撞基准 5）。`--cc` 是 git 自己对「这一帧引入了什么」的回答，零维护、零解析新增。实测两个方向都对：例行 merge `[]`、evil merge `['src.py']`。

**fold 而非另开**：同一原语面、同一批测试文件、同一个函数。分开做要付两遍 workflow 循环成本（基准 4）。

### ADR-3：git 环境失败映射 `UNKNOWN(6)`，不映射「判失鲜」

**决定**：定义 `GitUnavailable` 异常，`run_git*` 三处捕获 `FileNotFoundError` / `TimeoutExpired` 后抛出，`main()` 统一捕获 → `UNKNOWN(6)`。

**备选（已否决）**：把它当成"枚举失败"走既有的保守判失鲜路径。

**理由**：两者的**正确下一步动作不同**。枚举失败 → 判失鲜 → 提示重跑设计门，这在 git 没装的机器上是错误引导：重跑一百次也不会好。`UNKNOWN(6)` 的语义正是"盘面判不了，须人裁"，与「环境坏了」精确对应。`decide()` 内已有一处 `rev-parse --git-dir` 失败 → `UNKNOWN` 的先例（`:1165`），本决定与之同向。

**映射点唯一性**：`main()` 里 `decide()` 之前就有一次 `run_git`（解析 `--root`），∴ 捕获 MUST 包住整个 `main` 函数体，不能只包 `decide()`。

### ADR-4：`timeout = 30`，对齐仓内既有先例

**决定**：三个 helper 统一 `timeout=30`。

**理由**：本仓已有同类先例——`sdflow-buglist/scripts/buglist.py::repo_root` 的 `git_timeout = 30`，其注释写明判据：「本调用是纯本地元数据查询（正常毫秒级），30 秒是**文件系统卡死 / 网络文件系统挂起**的判定线，**不是性能预算**」。gate 的 git 调用同属本地元数据查询，判据一致 ⇒ 取同值，不另发明数字。

**MUST NOT** 按"最慢的仓要多久"来定这个值——那会把它误当性能预算，越调越大直至失去意义。

**与 ADR-1 的耦合**：code 域降到 1 次调用后，该域的 `timeout` 才真正是**总**上界；design 域仍是逐帧 N 次，总量上界为 30N——这是 per-commit 判豁免的固有代价，显式登记，本次不额外收敛。

### ADR-5：code 域诊断复用 design 域的 detail 通道

**决定**：code 域的 `StaleResult` 填同一个 detail 字典，经同一个 `_stale_trigger_hint` 渲染。

**category 取值**（code 域）：`code-touched`（正常触发）、`enum-failed`（枚举失败，与 design 域同名同义）。

**代价（已接受）**：树比较语义下 `sha` / `subject` 两字段**无值可填**。撞门后的正确动作是重跑代码审，路径比 sha 更可操作；MUST NOT 为凑齐 sha 而退回逐帧枚举。

### 关于文本解码（显式接受，非疏漏）

`frame_touched_paths` 与新增的 `code_changed_paths` 都经 `run_git_rc`（`text=True, errors="replace"`）读 `-z` 输出。路径若含非 UTF-8 字节会被替换成 U+FFFD。

**这不构成 fail-open**：两域的谓词都只检查路径**前缀**（`openspec/changes/{change}/` 或 `openspec/`），前缀是纯 ASCII，替换只可能发生在其后的文件名部分 ⇒ 归属判定不受影响。`.strip()` 同理无害（NUL 在 Python 中不是 whitespace，末尾 NUL 会让 strip 立即停下，不会吃掉路径尾部空格）。

登记于此是为了让后续评审知道**这一点被看过并判定为安全**。若将来谓词从"前缀匹配"改成"全路径精确匹配"，本结论失效，须改用 `run_git_bytes`。

## 安全与数据保护〔BASE-28 · TG-17〕

**被保护的资产**：「代码审已放行」与「verify 已通过」这两个结论的有效性。它们是阶段三挡在 merge 之前仅有的两道质量门。

**威胁模型**：

| 谁 | 怎么做 | 修复前 | 修复后 |
|---|---|---|---|
| 走正常流程的开发者/agent | 代码审通过后，合并时在 merge 提交里 resolve 出源码改动 | 🔴 判 fresh，改动随档 ship | ✅ 判 stale |
| 同上 | 代码审通过后 `git mv` 把源码文件迁进 `openspec/` | 🔴 判 fresh | ✅ 判 stale |
| 环境异常（非攻击者） | git 调用失败 | 🔴 判 fresh | ✅ 保守判 stale / `UNKNOWN(6)` |
| 无（假阳面） | 设计门拍板后例行合并 main | 🔴 假判 stale，`REFUSE_START` 卡死正常流程 | ✅ 判 fresh |

**残余面（显式登记，本次不覆盖）**：

- **手工伪造 commit subject 绕 design 域 BR-7 豁免** —— 既有的已登记取舍，属显式越权同权级（git 留痕可审计）。本 change 不触碰。
- **有写权限者直接改报告 frontmatter** —— 盘面即状态的设计前提是人机同权（`grill-amendment D9`）；篡改留痕可审计。不在失鲜判据的职责内。
- 本 change 提升的是**误操作与流程漏洞**的拦截率，**不声称**能挡有意规避者。

## Risks / Trade-offs

- **[改 `frame_touched_paths` 影响 design 域]** → 缓解：design 域现有全部用例（含 BR-7 真值表 8 格、短路次序、内容豁免）必须逐一通过。**唯一允许的用例改动是「例行 merge 假阳」那一类**——若有其他用例需要改，说明语义额外变了，须停下重判。
- **[树比较的两条语义变更被当成 bug]** → 缓解：「改回即 fresh」「孤儿锚按内容判」已写进 spec Requirement 并各配用例；实现期在 `ship_gate.py` 注释写明成因。
- **[行为变更导致在途 change 撞门]** → 缓解：三类 fail-open 盘面此前是被误放行的，撞门是修复的预期效果。hand-off 与升级提示中显式说明「升级后若撞 code 域失鲜，先确认不是真的漏审」。反向地，设计门假阳的消失会让此前被卡住的 change 自然放行，无需干预。
- **[`timeout=30` 在极慢环境产生假 `UNKNOWN`]** → 缓解：30s 对本地元数据查询有两个数量级余量；且假 `UNKNOWN` 是**停下问人**，方向安全（非假放行）。
- **[变异证明流于形式]** → 缓解：spec 已把"删掉守卫即变红"写成需求；实现期每条守卫的变异结果须落进 impl-report，不得只写"已加测试"。

## Migration Plan

1. 本仓为 toolkit 源仓：改动经 push → 各消费仓 `/sdflow-upgrade` 生效。
2. **回滚**：`ship_gate.py` 是纯只读判官，无持久状态、无数据迁移。回滚 = 还原文件 + 重跑 `setup.sh`。
3. 无 schema 变更、无退出码集合变更（`UNKNOWN(6)` 是既有取值，只是新增到达它的路径）。

## Open Questions

无。

## Compliance

实现期 MUST 遵守（本节逐字进 `superpowers-plan.md` 的 `## Global Constraints`）：

- **MUST NOT** 改动 design 域的判定语义；design 域既有用例**除「例行 merge 假阳」一类外** MUST NOT 被修改，须原样通过。
- **MUST NOT** 以「两域统一」为由把 code 域改回帧枚举，或把 design 域改成树比较（adr/0026：按各自要回答的问题选原语）。
- **MUST NOT** 把 design 域的防护逐条照搬进 code 域——每条须**独立判定其在 code 域的方向**。
- 枚举 **MUST NOT** 使用 `git log --name-only`；**MUST NOT** 使用 `-m`（过报锚前历史）；**MUST NOT** 加 `--no-merges` / `--first-parent`（承 BR-6 护栏）。
- 控制字符路径在 `-z` 下判豁免是**正解** ⇒ **MUST NOT** 以「恢复 fail-closed」为由改回，用例旁 MUST 注明成因。
- 枚举或路径获取失败 **MUST** 保守判失鲜，**MUST NOT** 与合法空结果共用同一表示。
- 每条新增守卫 **MUST** 附变异证明（删掉即变红），结果落 impl-report；**MUST NOT** 以"用例存在且为绿"充当证明。
- 新增用例 **MUST** 经 `is_stale` 公共入口求值，**MUST NOT** 只直接调内部 helper。
- code 域的**两个**消费方（`code-review-report`、`verify-report`）MUST 各有覆盖——后者今天是唯一有用例的一个，前者零覆盖。
- `ship_gate.py` **MUST** 保持零第三方依赖。
- 退出码 **MUST** 落在 `{0,3,4,5,6}` 内。
