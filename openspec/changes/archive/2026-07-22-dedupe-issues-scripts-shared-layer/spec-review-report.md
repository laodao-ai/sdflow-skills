---
ship-gate:
  design_approved: true
  reviewed_sha: c7f666da17451f53805def51c8956a1646a59564
---

# spec-review-report — dedupe-issues-scripts-shared-layer

> **设计 HARD-GATE 已拍板批准 · 2026-07-22**（用户过本报告 + amendments + 窄复核批准 → 阶段三 /sdflow-ship）。
> 被批准盘面 `reviewed_sha=c7f666d`（四件套最终态：D1-D7 amendments + Q1-Q4 按推荐 + 窄复核 4 洞已修）。
> ship-gate 机判锚见头部 frontmatter；初评（v1）总裁决为「打回」，收敛历程见文末〔窄复核收敛 + 拍板登记〕。

<!-- sdflow:step1-broad-review v1 mode="native" -->

> **阶段二设计评审（sdflow-spec-review 编排）**。Step1 autoplan 广审（native·见 `gstack-review.md`）（Claude 独立广审子代理 + Codex 广审 voice）
> → Step2 并行多镜（1 领域镜 backend + 2 对抗镜 + 1 接地镜）+ hr-tg 领域 cross-model voice → Step3 合并去重 +
> 对抗裁决。宿主 host=claude（档位 opus/sonnet/haiku），metrics.enabled=true。
>
> **初评（v1）总裁决：设计 HARD-GATE 当前不应通过——方向对，契约机械层未做全。**（**已被后续 amendments + 窄复核推翻，最终态=批准**，见文末〔窄复核收敛 + 拍板登记〕）方向（三 skill 3→1 合一、撤「独立分发」）
> **站得住**（setup.sh 实测无单装路径、CONTEXT「三维度分家」把台账当一个概念）；问题**全在目标态契约的机械守卫与
> 引用完备性**：1 个合并后必打红 CI 的 Critical（R1）+ 5 个 High 契约缺口（R2/R3/R5/R6 + R4 tension）。
> 初评建议**打回补 amendments 后重过窄复核再拍板**——已按此走完（D1-D7 落定 + Q1-Q4 拍板 + 窄复核 4 洞修复）。

---

## 决策登记区

```
  spec-review-report.md · 决策登记区
  ┌──────────────────────────────────────────────────────────────────────────┐
  │ [自动决策] D1  R1 AD-5 补全 + 机械引用守卫       fail-closed 必改·默认采纳     │
  │ [自动决策] D2  R2 守卫升 AST 级(禁窄扫描当保证)    守法即剧场·必改·默认采纳       │
  │ [自动决策] D3  R3 POOL_SPEC 封闭 schema+关系守     6镜收敛·必改·默认采纳         │
  │ [自动决策] D4  R5 零回归门改覆盖判据(非≥603魔数)   算术自证伪·必改·默认采纳       │
  │ [自动决策] D5  R6 golden 诚实降级(不再宣称抓漏)    tautology·必改·默认采纳        │
  │ [自动决策] D6  R8 issues.py sibling 常量+注释+措辞  必改·默认采纳                │
  │ [自动决策] D7  R9 thinness 同一性守 + R11 数字修正  必改·默认采纳                │
  │ [需拍板]  Q1  R4 import core 加载策略(TENSION)     裸import/唯一包/__file__      │
  │ [需拍板]  Q2  R3 callable 逃生口去留               禁任意callable vs 命名限签     │
  │ [需拍板]  Q3  R7 误判落错池恢复(TENSION)           补move命令 vs 记已知代价       │
  │ [需拍板]  Q4  R10 god module vs 内部拆包            内部package vs 单core vs defer │
  │ [已核清]  X1  并发/锁竞态          对抗A+领域镜独立 refute·仓级锁不变·无新race    │
  │ [已核清]  X2  回滚干净            对抗A refute·预存幸存者+统一marker·无数据坑     │
  │ [已核清]  X3  迁移中态假红/绿      对抗A refute·单次提交·中态不进CI              │
  └──────────────────────────────────────────────────────────────────────────┘
```

---

## Findings（合并去重 · 命中镜集 · 对抗裁决）

置信分流：spec 评审优化召回（设计漏项传导进实现代价高），低置信项亦上抛不静默滤除。严重度 = 目标态代价。

### 🔴 R1 [Critical] AD-5 下游引用清单不全 → 合并后 CI 必红 + 主 spec 留死路径
**命中：broad(Claude G1) · design-voice(Codex Critical，独家抓 CI) · 接地镜(⑨ refine + overclaim) · 领域镜(BE-10.2/10.3)**
可证伪假设 **A3**（下游引用已枚举全）的证伪信号在多个未列点触发：

| 未列点 | 性质 | 后果 |
|---|---|---|
| 🔴 `.github/workflows/windows-recorder-smoke.yml:35` | CI 跑 `sdflow-buglist/tests/...`（合并后已删），`:18` trigger 含 `sdflow-issues/**` | **改幸存 skill 即触发必然失败的 workflow**。本地 mac pytest 照不到 CI YAML（dogfood 盲区），只 5.5 手 grep 能抓 |
| 🟡 `recorder-root-resolution/spec.md:5-6,77-78`（主 spec） | 把三 recorder 路径写死为契约，本 change **无该 capability 的 delta** | 归档不修正 → 主 spec 留死路径 |
| 🟡 `spec-workflow/spec.md:285,293,297`（主 spec） | `:285` 是活跃 **MUST**（RENAME-MAP 枚举旧 skill 名）+ Scenario | 删 skill 使 accepted spec 失真、无 delta；task 5.5 grep-replace 会静默重写 spec requirement（过程错误） |
| 🟡 `sdflow-init/tests/test_setup_sdflow.py:106,151` | 断言 setup 后 `sdflow-buglist` 建链 | 目录删后断言 FAIL（6.2 pytest 撞红，但 AD-5 未列为编辑目标、无预期改法指引） |
| 🟢 `sdflow-retro:107`/`sdflow-implement:378`/`sdflow-init:138` SKILL.md | prose 引用已删触发面 `/sdflow-buglist`·`/sdflow-todolist` | 指向不存在 slash 命令（DOC-1：正文指向不存在物） |
| 🟢 `sdflow-done/SKILL.md:207-211` | **语义块**（描述整个 sibling-独立分发架构，正是被反转的东西） | 需语义重写、非路径前缀替换 |

**接地镜 ⑨ 的两个反向修正（AD-5 亦 overclaim）**：
- AD-5 把 `sdflow-ship`/`sdflow-code-review` SKILL.md 列为「路径引用需同步」——实测 **0 处脚本路径引用**，只有「defer 进 buglist/todolist **池**」概念。**关键 nuance：合并是 skills 3→1，两个 POOL 目录（`openspec/issues/buglist/`+`todolist/`）不合并** → 池名引用**仍有效、无需改**（已实测池目录名不变）。真 ship 侧路径在 `ship_gate.py`（AD-5 已单列，对）。
- **`setup.sh:26 OUR_LEGACY_NAMES` 必须保留旧名**（领域镜 BE-10.3）——Windows `.laodao-skills` legacy marker orphan 回收按名匹配，5.5 sweep 若当「陈旧引用」删掉会破坏 Windows 清理。

**裁决（采纳·致）**：fail-closed 必改。修法：① 新增 `recorder-root-resolution` + `spec-workflow` 两份 MODIFIED delta
（spec-workflow 的 RENAME-MAP requirement 须**修订**——skill 已不存在，非 grep 替换）；② CI YAML（path-trigger + line35 调用 +
测试文件迁移）、`test_setup_sdflow.py`、三 prose SKILL 引用**提升进 AD-5 显式枚举任务**，不只靠 5.5 兜；③ **增机械引用守卫**
（allowlist 放行 archive/历史 ADR/issue ledger/`setup.sh` OUR_LEGACY_NAMES 旧名/**在途 change 自身四件套**——对抗B 注记：四件套满是 sdflow-buglist 字样，不豁免则 archive 前自伤；池名 `buglist/todolist` 目录引用亦放行）；④ 删去 AD-5 对
sdflow-ship/sdflow-code-review SKILL.md「路径引用」的 overclaim。

### 🔴 R2 [High] 「core 无 pool 分支」守法 spec 定义过窄 + 可平凡绕过 → 守法即剧场
**命中：broad(G2) · design-voice(Codex) · 对抗镜2(F2) · 主 session 独立接地确认**
spec 把禁止形写死 `if pool == "bug"/"todo"`，但**真实待上移 core 的 pool 分支四形态**，扫字面必漏：
`document["pool"] == "bug"`（issues.py:900/991/1001/1056，**subscript 形扫变量名必漏 4 处**）· `expected_pool == "bug"`
（677/689、buglist.py:1218/1230）· `"bugs" if pool == "bug" else "items"`（1365 三元）· dict-dispatch（issues.py:1522/1528）。
Codex 另举 `match pool`/`kind=pool` 别名/callable 内部比较等绕法。**这是 CLAUDE.md 基准 5（无界语法禁手搓、补丁循环永不收敛）+「gate 子串检测自指坑」的复发**——「源码是否按 pool 分叉」是语义无界面。
**裁决（采纳·高）**：修法：诚实承认源码扫描是 **best-effort 代理、非 fail-closed 保证**（基准 5：机械判定须正确 ⇒ 别靠扫描猜语义）；正解 = 靠 POOL_SPEC 完备（R3）+ 无跨 pool 硬编码常量正面保证；若保留扫描须 AST 级列全形态（`If`/`IfExp`/`Match`/`Compare` 右操作数 ∈{"bug","todo"} 且左操作数解析到 pool 值 + 别名）+ mutation test 证反红；tasks 显式列「迁移期把 1365/677/689 三处重写为 POOL_SPEC 取值」。

### 🔴 R3 [High] A1 POOL_SPEC 维度不全 + 完备守只查 presence 不查关系/正确性 + callable 逃生口不可证伪
**命中最广（6 镜）：broad(G3) · design-voice(Codex) · hr-tg(H2/H3) · 对抗镜1(NEW-2) · 对抗镜2(F3) · 领域镜(BE-05.1)**
- **维度漏项**（实测的真实分岔不在 AD-3 五维表内）：**ID 前缀 `DEFAULT_PREFIX` B/T**（buglist.py:83、canonical_id 隔离依赖它，领域镜+对抗A）· **scan 输出键 `"bugs"` vs `"items"`**（issues.py:1456 注释自认「不统一」，对抗A）· **legacy dir glob** `openspec/buglists/*` vs `todolists/*`（issues.py:245-247，领域镜）。
- **只守 presence 不守关系**（hr-tg H2 + 对抗B F3）：现有代码依赖 `terminal_set ⊆ STATUS_CODES`（test_issues.py:169-260），新「完备」门放行「terminal_set 含非法状态/漏合法终态/entry 注错 pool」→ INDEX/batch 完成判定**静默漂移**。
- **完备集本身不可信**（对抗A NEW-2 = G3 callable 逃生口根因）：完备维是人手枚举，**结构上无法发现作者没想到的 pool 差异**；AD-3「值可为可调用」（design.md:93）= 任何整段逻辑塞进 callable，A1 永不失败。
- **registry-consumer 无闭包**（hr-tg H3）：新增第三 pool 时 config 过完备检查，但 global ID/INDEX/batches/sweep 仍硬编码两池。
**裁决（采纳·高）**：修法：POOL_SPEC 定义为**封闭 dataclass/TypedDict**（required 维=字段全集，新增维必须改 schema）；补 DEFAULT_PREFIX/scan-key/legacy-glob 维；对可枚举维加**值正确性**断言（`terminal_set ⊆ statuses`、与 `RECORDER_POOL_CONFIG` 现值一致）；fail-closed 断言 `POOL_SPEC.keys()=={"bug","todo"}` 或令 snapshot/read/sweep roster 从同一 registry 派生。**callable 去留 → Q2 人拍板**。

### 🟡 R4 [High·TENSION] 同目录 `import core` 是否「只换路径前缀」——两声分歧，领域镜实测
**命中：design-voice(Codex G4 High) · broad(Claude 判无问题) · 领域镜(实测 CLI 两平台成立)**
- **Codex**：非纯替换。多数测试用 `importlib.spec_from_file_location()` 按文件加载、**不改 sys.path**（test_task2_semantic_lock.py:15、test_frontmatter_dual_reader.py:17）——wrapper 加 `import core` 后这些测试 `ModuleNotFoundError`；裸模块名 `core` 共享全局 `sys.modules["core"]`，别处先加载同名 → 拿错 core（无 `__file__` 校验）。
- **Claude + 领域镜**：CLI 直跑 `sys.path[0]`=realpath 脚本目录、core 在场，两平台成立（领域镜实测）。
**对抗裁决**：二者**不矛盾——是两条加载路径**。领域镜实测的是 **CLI 执行**（sys.path[0]=脚本目录）；Codex 攻的是**测试的 file-based 加载**（spec_from_file_location 不设 sys.path[0] 为 wrapper 目录）——领域镜**未覆盖**该路径，故 Codex 的测试加载 + 模块名碰撞担忧**未被 refute**。∴ 采信为真实实现风险，「只换路径前缀」的表述掩盖了它 → **Q1 人拍板**。推荐**唯一命名内部 package**（如 `scripts/sdflow_issues_core/`）——同时消碰撞 + 令测试加载显式。〔置信：高（Codex 具体、领域镜证 CLI 侧、未证测试侧）〕

### 🔴 R5 [High] 「≥603」零回归门形态错误——算术自相矛盾 + 可游戏化 + 漏跨池命令
**命中：broad(G5) · design-voice(Codex) · 对抗镜2(F1 sharp) · hr-tg(H1) · 接地镜(count 事实)**
- **算术自证伪**（对抗B F1，主 session 核实）：`test_mirror_consistency.py` 实测 **7 个测试函数**（本 change 全删）+ 新守 2 → 603 − 7 + 2 = **598 < 603**，**合规重构必然卡红**，除非灌水补 ≥5 trivial 测试（教科书级游戏化）。
- **漏跨池命令**（hr-tg H1）：等价快照只列 `add/scan/set-status/triage/reindex/batch`，漏 **`next-id`**（跨池 ID 分配 buglist.py:1403-1416）+ **`sweep`**（两池 issues.py:2365-2448）——合并边界最受影响的两命令。
- **6.1 是一次性快照非留存测试**（对抗B F4）：archive 后无人能重放，样本外命令等价失守。
**裁决（采纳·高）**：修法：门改为**覆盖判据非计数**——① 冻结 pytest node-id manifest，只允许 allowlist 删除（`test_mirror_consistency.py` 7 个）；② 断言 argparse 全 subcommand（含 next-id/sweep/batch 子命令/错误路径）migration 后逐一有测试触达；③ 6.1 产物改为**留存 param 化等价测试**（遍历 subcommand 全集），非丢弃快照。〔注：603 基线本 env 未能 collect 复核，但门形态错误与确切基线无关〕

### 🔴 R6 [High·NEW] direct↔scan golden 合一后变 tautology（自测自己，spec 自相矛盾）
**命中：对抗镜2(F6，唯一报，sharp)**
合一后 direct-snapshot 与 scan 两 code path 跑**同一 core parser** ⇒「一方漏某 rule」**结构上不可能**（两方同漏），golden 恒绿（自己==自己）。`determinism-guards/spec.md:12` **自认**降级为「同源、由 603 零回归被动保持」，但同文件 :32-34 **仍宣称主动抓漏**「任一方漏 rule 则失败」——**两者不能同真**。合一后该测试从「抓 rule 遗漏」退化为「抓 divergence」，而 divergence 已被单一源构造性消除。
**裁决（采纳·高）**：单镜报但**证据在 spec 自身文字、机理坐实、置信高**。修法：诚实重述 golden 不再是 rule-omission 守（该能力已由「core 是 rule 单一源」结构事实取代）、删 :34「漏 rule→失败」宣称；若要真 rule-完整性守，须 **core-parse vs 外部 golden fixture**（外部锚，非 core 自比 core）。**含 tautology 诚实降级判定 → Q4 参考**。

### 🟡 R7 [Medium·TENSION] 触发面塌缩：模型判 pool + 无跨池改判命令 → 误判落错池不可机械恢复
**命中：对抗镜1(NEW-1) · broad(Claude G8 per-pool 粒度较弱 + DX 判可接受)**
- **对抗A**：CLI 无 move/reclassify/repool 命令（grep 零命中），pool 在 `add` 落盘锁死。骑墙输入（「性能退化」——todo 的 type 恰有「性能优化」）模型误判 → 错前缀 B↔T/错粒度/错 schema/错词表，纠正须手删+重 add **丢 ID 与历史**。design 用「无人单装」（安装耦合）论证「触发面塌缩代价可接受」——**混淆了安装耦合与分类代价两轴**，Risks 无此条。
- **broad-claude DX（TENSION）**：判可接受，因 **CLI 仍保显式 pool 入口**（`buglist.py add`/`todolist.py add`），「坏了没」路由只在 SKILL.md NL 层，误判低代价可恢复。
**对抗裁决**：显式 CLI 入口确是逃生口（broad-claude 对）；但「无 move 命令」的恢复缺口真实（对抗A 对）——不过该缺口**今天也存在**（pre-merge 也无 move 命令），NEW 的只是 NL 层误路由。∴ **降级 High→中**：真实但非新的高危。修法（→ Q3）：推荐 **design 显式记「误判落错池不可机械恢复」为已知代价 + 合一 SKILL.md 给骑墙输入判定规则 + 人门确认**；`move --to-pool` 命令为 nice-to-have（可 defer），非必须。〔置信：中〕

### 🟡 R8 [Medium] issues.py sibling-spawn 常量 + 承重注释被作废，tasks/AD 措辞主动误导
**命中：对抗镜1(NEW-3) · 领域镜(BE-10.1) · broad(G1 sub) · 主 session 确认 68-69 存在**
`issues.py:66-69` 用上两级 sibling join 到 `sdflow-buglist`/`sdflow-todolist` 拼 `BUGLIST_SCRIPT`/`TODOLIST_SCRIPT`，reindex/sweep 靠它真跑子进程（1443/1500-1501）；承重注释 59-65 明写「siblings」前提。合一后 buglist.py 迁到同目录 → sibling 前提摧毁。**tasks 2.3「子进程契约保持」+ AD-2「只有脚本路径前缀」两句均误导**（spawn 用两级计算，非 CLI 契约、非简单前缀）。
**裁决（采纳·中）**：gate 兜得住（6.2 reindex 测试真跑子进程 → FileNotFoundError 红，**非假绿**）但可避免返工 + 遗留错注释（DOC-1）。修法：tasks 补「`SKILLS_ROOT`/两常量改同目录 `os.path.join(SCRIPT_DIR,...)` + 重写 59-65 注释去 sibling 前提」；AD-2「只有路径前缀」表述显式排除内部两级 spawn 常量。

### 🟡 R9 [Medium·NEW] 三薄入口 thinness 零机械守——可 shadow core helper 不拉红
**命中：对抗镜2(F5，唯一报)**
承诺（spec:23）「顶层不再存在同名镜像函数对」，度量「同名 def 交集**大幅归零**」——「大幅归零」**非阈值、写不成会 fail 的断言**，且 tasks 无任何守法建它（4.2 只建 no-branch+completeness、4.4 只检 import 形态）。合一后薄入口**本地重定义** `atomic_write`（shadow `core.atomic_write`）或私留 `_build_effective_snapshot` **无守法拉红**。thinness 是设计核心承诺（写进标题「三薄入口」）却零机械守。
**裁决（采纳·中）**：修法：断言 THREE_WAY/TWO_WAY 名单每个 helper 从薄入口 `getattr` 解析的对象 `__module__ == 'core'`（证未被 shadow，复用旧 mirror 名单把「等价守」转「同一性守」，成本极低）；删「大幅归零」不可判词。

### 🟢 R10 [Medium] 「一个 skill」误等同「一个巨型 core.py」+ 保留已失理由的子进程边界
**命中：design-voice(Codex G7) · broad(Claude F4)**
去重不要求全塞一个文件，目标 core.py 可能仍数千行 god module；设计保留 `issues.py → buglist/todolist scan --json` 子进程（design.md:66、issues.py:1499），两 scan 各读全 snapshot 再过滤 pool、一次 reindex 重复扫全台账，合一后该进程边界无独立分发价值。ADR Considered Options 未评估「一个 skill + 内部 cohesive package + wrapper」。
**裁决（defer·中·非阻断）→ Q4**：修法建议内部 package（recorder/document/locking/ledger/policies）+ 三 wrapper，issues 内部对一 snapshot 调两次 pool view 不自调子进程；或显式 defer 留档（如 CLI-子命令树 defer 先例）。

### 🟢 R11 [Low] 数字/措辞瑕疵（接地镜实测）
**命中：接地镜(grounding) · broad(G8)**
- 「77 同名 def / 90% AST 等价」→ 实测 **75 / 85.3%**（proposal+design 乐观，定性成立）。
- 「SKILL.md 正文 133 行 / 58% 相同」→ 实测 **189 行相同 / 61.6%**（**低报**实际重复，诚实边界更强、非虚报，133 不可复现）。
- AD-5「自动少一个」自相矛盾于「17→15」（=−2），应「少两个」（sync_principles 动态枚举会自动收敛，只 test docstring 常量需改）。
**裁决（采纳·低）**：数字改实测值或软化为「~75/~85%/多数逐字相同」；「少一个」改「少两个」。

---

## 已裁掉 / 已核清区（反静默压制·可审计）

以下角度经镜子**主动攻击后 refute 为无问题**（非我静默丢弃，是 mirror 自身的诚实负结果），记录供人门复核「refute 得对不对」：

- **X1 并发/锁竞态**（对抗A + 领域镜**独立双证**）：`recorder_lock` 锚在目标仓根 `openspec/issues/.recorder.lock`（issues.py:128）、**非 skill/脚本身份**；跨池 reindex/sweep 与单池 add 早已在同一仓级锁下靠 env-token 委托串行。合一是纯物理搬迁，锁粒度/ID 空间（前缀+目录隔离）**零变化**，无目标态新死锁/竞态。
- **X2 回滚干净**（对抗A）：`sdflow-issues` 是**预存幸存者**（非本 change 新建），revert 恢复两目录 + 移除新增 core/wrapper + setup.sh 重链；三脚本**合一前已统一 `sdflow-issues:` frontmatter marker**（409），合并期台账文件被 reverted 代码可读，**无数据格式回滚坑**。
- **X3 迁移中态假红/绿**（对抗A）：复选框 archive 阶段才勾、单次提交，渐进中态不进 CI，中态红不落盘。
- **X4 分发/import/orphan/fail-closed 机制正确性**（领域镜实测）：两平台分发、CLI `import core`、orphan 回收 dangling、`validate_scan_envelope` fail-closed 均实测成立（`import core` 的**测试加载**侧例外 = R4）。

---

## outside-voice

- **design-voice（复用 autoplan Codex 广审·跨模型）**：outside_voice_guard reason_code=`none`（三前置全过）→ 复用不重开，避免双 codex。Codex 广审 7 findings 已并入 R1/R2/R3/R4/R5/R10。
- **hr-tg（领域 cross-model·TG-06 命中单开）**：runner=codex、exit 0、3 边界层 findings（H1 等价漏 next-id/sweep→R5、H2 POOL_SPEC 关系守→R3、H3 registry 闭包→R3）。sidecar `.rc`=0 取退出码（非 stdout 推断）。

<!-- sdflow:hr-tg v1 hit="TG-06" declared="TG-06,TG-10,TG-13,TG-14,TG-18,TG-19,TG-23" evidence="TG-06 重评并变更 D-6独立分发边界·三skill合一+共享core" -->

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->

<!-- sdflow:outside-voice v1 site="design-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="7" truncated="false" -->

<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="3" truncated="false" -->

<!-- sdflow:declared-sites v1 declared="design-voice,hr-tg" -->

### lens-metric（度量锚·metrics.enabled=true·emitter 确定性归约·SR-M：中置信项设计门可翻改，拍板时最终化）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="7" 采纳="7" 裁掉="0" defer="0" 独立="2" sev="致0/高4/中3/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="8" 采纳="7" 裁掉="0" defer="1" 独立="0" sev="致1/高3/中2/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="0" sev="致1/高1/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="0" sev="致1/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="6" 采纳="5" 裁掉="0" defer="1" 独立="0" sev="致1/高3/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="0" sev="致0/高2/中0/低0" -->

---

## 收敛口

🔴 **不建议进设计 HARD-GATE。** 本设计的**方向正确**（合一去重、撤独立分发有据），但目标态契约的**机械守卫层与引用完备性有 1 Critical + 5 High 未做全**——其中 R1（CI 必红）会在合并第一时间打红、R2/R3/R6 会让新守法「看着守、实测放行」（守法即剧场 / tautology），正是本仓「机械化优先」基准最该拦的假绿面。

**建议流程**：人门**打回** → 按 D1-D7 补 amendments（重点：AD-5 两 delta + 机械引用守卫、POOL_SPEC 封闭 schema + 关系守、守卫升 AST 级并诚实标 best-effort、零回归门改覆盖判据、golden 诚实降级）→ 对 Q1-Q4 拍板 → **跑一次窄复核（只审增量 amendments）** → 再拍板批准。amendments 落定前不写 `ship-gate.design_approved`。

> 注：R2/R3/R6 三条共享同一模式——**「有确定性信号的外壳」骗过「机械化」闸门**（源码扫描像机械、POOL_SPEC 完备像机械、golden 像交叉校验），但都在语义无界面 / 自比自己上失效。修 amendments 时统一按基准 5「机械判定须正确、best-effort 展示须诚实标注」处理，别逐条补丁。

---

## 窄复核收敛 + 拍板登记〔最终态〕

初评（v1，收敛口以上）总裁决为**打回**（1 Critical + 5 High 契约机械层缺口）。已按初评建议的流程走完，最终 **HARD-GATE 批准**：

| 阶段 | 提交 | 内容 |
|---|---|---|
| ① D1-D7 二次修订 | `5078c62` | 唯一命名内部 package / 守卫升 AST / POOL_SPEC 封闭 schema / 零回归门改覆盖判据 / golden 诚实降级 / AD-5 补全 + 机械引用守卫 / 2 主 spec delta |
| ② Q1-Q4 拍板 | `5078c62` | Q1 唯一命名内部 package（消 import 碰撞 + 令测试加载显式）· Q2 命名限签 callable · Q3 记「误判落错池不可机械恢复」为已知代价 + 合一 SKILL.md 骑墙判定规则 · Q4 内部 package 拆分 |
| ③ 接缝修正 | `9ccdd89` | 4 处残留 `core.py`/`import core` 漏改（determinism-guards Scenario + Goals + TG-14 + 旧注记）改 package |
| ④ 窄复核（只审增量） | `c7f666d` | 4 洞修复：F1（spec-workflow census→RENAME-MAP 框架）· F2（allowlist 豁免整个在途 change 目录非仅四件套）· F3（implement:378 doc-pointer 非 slash）· L1（determinism-guards 2 delta header 匹配主 spec 防 archive 失配） |

**拍板**：用户 2026-07-22 过本报告 + 全部 amendments + 窄复核后批准 → 回写 `ship-gate.design_approved=true`、`reviewed_sha=c7f666d`（被批准盘面）→ 进入阶段三 /sdflow-ship。初评列出的 R1（CI 必红）/R2/R3/R6（机械化假绿面）均已在 ①②④ 中按基准 5 收口。
