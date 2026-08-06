# 设计评审报告 · fix-probe-scan-precision

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-10,TG-12,TG-14,TG-15,TG-18,TG-19,TG-22,TG-23" evidence="命中集无一属 HR-TG 子集{TG-04,06,07,08,09,16,17,26,27}——本 change 无 DB 迁移/API 契约/外部依赖/状态机/NFR/信任边界/并发共享状态/LLM 产出消费" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="adversarial,grounding" -->
<!-- sdflow:declared-sites v1 declared="design-voice" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="section-not-found" host="claude" runner="codex" reason_code="ok" findings="3" truncated="false" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="13" 采纳="13" 裁掉="0" defer="0" 独立="10" sev="致1/高5/中4/低3" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="15" 采纳="11" 裁掉="1" defer="3" 独立="5" sev="致2/高8/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="3" 采纳="2" 裁掉="1" defer="0" 独立="2" sev="致0/高0/中0/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="0" sev="致0/高3/中0/低0" -->

> **一句话结论**：**不建议直接进设计 HARD-GATE 批准。**判据形式的大方向（内容探测 → 版本对比）是对的，
> 但**具体判据在三个地方指错了对象**（比错了东西 / 比错了时点 / 比错了粒度），且本 change 自称要解决的
> 「结构上无法机械守」**并未解决**。返工面已被精确定位，见下方 Q1–Q4 与 F1–F15。

## 本轮实际跑过的镜（roster · 如实降级）

| 镜 | 数量 | runner | 跑了吗 | 说明 |
|---|---|---|---|---|
| **broad**（autoplan） | 1 | claude（主 session 原生） | ✅ | CEO 双声齐备；Eng 单声；Design/DX 未跑，见 `gstack-review.md`「本轮明示偏离」 |
| **领域镜 domain** | **0** | — | ❌ **未跑，且不应跑** | `spec-checklists/domains/` 只有 backend·go / embedded·{ml307c,esp32} / frontend 四份，本 change 命中**零个**（`config.yaml` context 已显式声明「不命中 domains 清单中任一领域」）。**MUST NOT 为凑镜数编一个领域镜** ⇒ roster 不含 domain 行 |
| **对抗镜 adversarial** | 2 | claude/sonnet | ✅ | A=前瞻性（防二次返工）· B=文档完整性/可测性 |
| **接地镜 grounding** | 1 | claude/haiku | ✅ | 18 项代码事实核验；1 条结论被驳回（X3） |
| **outside-voice** | 1 站点 | **codex/gpt-5.6-sol（跨模型）** | ✅ | site=`design-voice`，复用守卫判 `section-not-found` → 回落自跑，exit 0 |

**base 清单（BASE-01~30）的覆盖**：由 autoplan + 对抗镜 B + 主 session 共同覆盖（无领域镜可依托）。

## 决策登记区

```
  ┌───────────────────────────────────────────────────────────────────┐
  │ [需拍板] Q1  是否把 scope 扩到「消灭双链」（删消费仓 tools 副本）  │ ← TENSION-1，两把声音正面冲突
  │ [需拍板] Q2  判据是否从 commit SHA 改为「实际部署集的内容摘要」    │ ← 一改解四条（F5/F7/F8/F10）
  │ [需拍板] Q3  机械化落点：新 helper vs 并进 resolve-workflow.sh    │ ← 推翻 ADR 砍候选③的理由
  │ [需拍板] Q4  D4「两条链各写各的版本」是否改为单写入点             │ ← D4 是人已拍板项，故上抛
  │ [自动决策] D-a 领域镜 0 个（无命中领域，不编镜）                  │ 默认接受
  │ [自动决策] D-b Eng/DX 部分声音未跑（已在 gstack-review 显著标注）  │ 默认接受
  │ [已裁掉] X1  「新 SKILL 忘实现工具能力 ⇒ 假绿」降级              │ 附理由，可审计
  │ [已裁掉] X2  copy_bundle 沿软链删仓外目录 → defer 记 bug（非本轮）│ 附 AND 门判定
  │ [已裁掉] X3  接地镜「Success Metrics 已归零」→ 实跑证伪，驳回      │ 附实测证据
  └───────────────────────────────────────────────────────────────────┘
```

---

### Q1【需拍板 · TENSION-1】是否把 scope 扩到「消灭双链」

**两把 CEO 声音正面冲突**（详见 `gstack-review.md` TENSION-1）：

- **codex CEO #6（主张删）**：`adr/0003:8` 保留消费仓 `tools/` 副本的承重理由是 review HTML 服务器根
  （「不落地即 404」）；而**同一 ADR 的 `:3` 已声明该 viewer 整体移除**，`:18` 砍掉「连 tools 也不落地」
  的唯一理由是「省 serve.sh 重写」——**serve.sh 已不存在**。∴ 原始承重理由已死，删掉副本即从根上
  消灭 skew 这一整类问题（非 pin 仓本来就执行全局 tools）。
- **Claude CEO F3（主张留）**：**不能删**。`ship_gate.py:953-955` 需要该路径在**消费仓自己的 git 历史里**
  存在（`ls_tree_map` 比对锚 commit 与 HEAD 做 code 域失鲜判定）。这是一条 `adr/0003` 与本 change
  **都没写过的新承重理由**。

**主 session 裁决与推荐**：**推荐本次不扩 scope**，把它登记为独立 roadmap 项。

依据（我独立复核 `ship_gate.py:953-957` 后确认）：删掉副本会让 `tools_spec` 的两次 `ls_tree_map`
**双双返回空集** ⇒ 该失鲜腿**静默退化为恒真锚**（永远判"没漂移"），而不是报错。
∴ 删副本**可行但不免费**，须同时给 ship_gate 的 tools 失鲜信号重新安家——这是一个独立设计问题。

**三镜代价**：
- **系统镜**：扩 scope ⇒ 一次性消灭整类 skew（探测器可整体删除，净复杂度大降）；但要动 `ship_gate.py`
  的失鲜判定（**门禁代码**，高 blast-radius），且 pin 仓语义要重新定义。不扩 ⇒ 保留探测器的复杂度。
- **用户镜**：扩 ⇒ 长期不再有仪式性硬停；短期一次迁移。不扩 ⇒ 现状延续。
- **开发循环镜**：扩 ⇒ 本 change 从"改判据"变成"改分发架构 + 改门禁"，需自身设计审 ⇒ 撞
  BASE-18 防吸积 AND 门的「需自身设计审查」「高 blast-radius」两项。不扩 ⇒ 本轮返工面可控。
- **主次判定**：**开发循环镜为主**。BASE-18 的 AND 门（同 capability ∧ 高耦合 ∧ 低增量）在此
  **不满足后两项** ⇒ defer 是纪律要求，不是偷懒。且**通则③ 明令 MUST NOT 自行加宽** ⇒ 我不会自己扩，
  这条必须由人拍板。

**备选**：人若要求本次就扩，则本 change 应整体重开为 roadmap 阶段（`sdflow-roadmap`），而非在
现有四件套上加节。

### Q2【需拍板】判据是否从 commit SHA 改为「实际部署集的内容摘要」

**背景**：proposal 的 Non-Goals 明确砍掉「给 **bundle 全文件**算内容指纹」，理由是把 O(1) 变回 O(n)。
但本轮发现，**摘要口径可以只覆盖「实际部署集」**（`tools/` + `lens-metric-contract.md` + `WORKFLOW-GUIDE.md`），
这比被砍掉的那个候选**窄得多**，且**一次解掉四条独立 finding**：

| 一并解掉 | 为什么 commit SHA 解不了 |
|---|---|
| **F5** dev 窗口未提交编辑假绿 | SHA 只看已提交历史，看不到工作树字节 |
| **F7** Windows 永久硬停 | 摘要不需要 git，副本自己就能算 |
| **F8** 空版本假绿 | 摘要恒非空（空目录也有确定性摘要） |
| **F10** 拷贝不收敛（上游删文件后残留） | 摘要覆盖"文件集"，SHA 不覆盖 |

**成本实测**（codex 侧核算 + 我复核量级）：bundle 非测试文件 64 个 / ≈566 KB，实际部署集 ≈391 KB。
对一次动辄十万 token 的多镜评审，sha256 全部部署文件是**毫秒级**。

**推荐**：**采纳内容摘要为主判据**（scope = 实际部署集，非全 bundle）。
**依据**：它同时是 F3（粒度）的正解，且把四条 high 一次性归零；`~/.sdflow/hack/capability-manifest.json`
已是本仓同款先例（`setup.sh` 写 sha256 entries、`preflight` 消费）——**不是新范式**。
**代价**：① 系统镜——多一处需要维护"部署集清单"的地方（但 `copy_bundle()` 本来就是那份清单的唯一权威）；
② 用户镜——无差异（同样硬停、同样文案）；③ 开发循环镜——摘要可被 pytest 精确断言，比 SHA 更好测。
**主次**：**系统镜为主**（正确性），开发循环镜次之。
**备选**：保留 commit SHA，但必须**显式登记** F5/F7/F8/F10 四条为已知残余（而非现在这样"未被发现"）。

> ⚠️ **这条改动了人已拍板的 D2/D3**（「版本对比」「纯 commit SHA」），故 **MUST 由人拍板，我不自行改**。
> 需要说明的是：D2 的核心（不再逐能力探内容特征）**在本推荐里完整保留**——摘要不是"逐能力探测"，
> 它是 O(1) 维护、加特性零改动的，与 D2 的立意一致；改的只是"用什么当版本"。

### Q3【需拍板】机械化落点：新 helper vs 并进 `resolve-workflow.sh`

**推荐**：**并进 `resolve-workflow.sh`**（新增专属退出码，如 `exit 3`），**不新开 `bundle_skew.py`**。

**依据**（对抗镜 A F5 的论证，我复核认可）：`resolve-workflow.sh` 已经是**唯一**同时知道
「这是不是 pin」「全局 canonical 在哪」「Unix/Windows 差异」「`SDFLOW_HOME` 重定向」的地方。
F2/F6/F7 三条 finding 的共同根因，恰恰是**把同一件事的计算摆到了两个独立文件里各写一遍**。
收拢到一处 ⇒ 值域不一致的风险从设计层面消失，不靠"两边记得用同一条命令"的约定维持。
两个评审 SKILL 已有「读退出码 2 = 降级」的分支，加一支 `exit 3` 即可，无需再调第二个脚本。

**代价**：`resolve-workflow.sh` 契约从"纯解析路径"加宽到"解析 + 顺带判新鲜度"。
**但这是收敛不是发散**——它本来就是唯一有资格做该判断的地方。
且 `hack/tests/` 已有「假 HOME 真跑 bash」的成熟模式可直接复用（该脚本已被这么测过）。
**备选**（不推荐）：独立 helper，但不自己重做解析，而是 shell out 调 `resolve-workflow.sh --explain`。
仍是两文件维护同一逻辑，F7 的核心风险仍靠约定维持。

> ⚠️ **这条推翻了 `adr/0038` 砍候选③的理由**。ADR 砍 `skew_probe.sh` 的理由是「它仍然是检查内容特征，
> 只是把补丁螺旋从散文搬进脚本」——但该理由描述的是**一种实现**（脚本里逐特性写 grep），
> 不是"脚本化"这条路径的必然结果。**ADR 把「判据形式」和「是否机械化」两个正交轴绑在一起砍了。**
> 两把独立声音（codex CEO #9 / Claude CEO F2）+ 对抗镜 A 各自指出同一处逻辑滑移。

### Q4【需拍板】D4「两条分发链各自写下自己的版本」是否改为单写入点

D4 是人已拍板项。但 F1 + F2 合起来推翻了它的**一半**：

- **全局侧不该写快照**（F1）：`~/.sdflow/workflow` 在 Unix 下是**实时软链** → 运行 checkout
  （实测 `readlink` = `~/.skills/sdflow-skills/sdflow-init/assets/workflow`），Windows 下
  `workflow-path` 指针文件里存的**也是活 checkout 路径**（`setup.sh:489`）。
  ⇒ 全局侧版本**可以实时算**，写快照反而**凭空引入一个 SKILL 没有的失鲜轴**。
- **消费仓侧仍需要落盘**：那是一份真拷贝，无实时来源，必须有戳。

**推荐**：改为 **1 个写入点（消费仓侧）+ 1 个实时解析（全局侧）**。
**依据**：直接消灭 F1 的两个方向（漏报的"pull 未 setup"窗口 + 误报且文案指错方向的"pull→update→未 setup"窗口），
并顺带删掉 tasks 1.1 与 3.1（少一处写入、少一组测试）。
**代价**：系统镜——全局侧多一次 `readlink`/`cat` + `git`（或摘要）计算，微；用户镜——无；
开发循环镜——**少一个落点、少一组测试、少一条"两侧取值必须一致"的约定**（tasks 1.3 可整条删除）。
**主次**：**开发循环镜为主**（它删掉的正是最易漂移的那条约定）。
**备选**：保留双写入点，则 F1 必须另有解法（例如 setup.sh 之外再挂一个 pull hook），成本更高。

---

## Findings（合并去重后 · 按严重度）

> **置信度分流**：高=直接采信；中=标"需人确认"；低=仍上抛一行，**绝不静默滤除**。
> 「命中镜」列记录去重前哪些镜独立报到过同一条——多镜收敛 ⇒ 置信度上调。

### 🔴 致命（判据指错对象，直接击穿机制目的）

**F1 · 全局侧版本是 `setup.sh` 时的快照，而 SKILL 走 symlink 实时生效 ⇒ 双向失效**
`design.md:71` 规定全局侧只由 `setup.sh` 写；而 `proposal.md:3` 自己说 SKILL 「`git pull` 即生效」。
两个窗口：① **pull 后未 setup 未 update** ⇒ 两侧仍是旧值、相等 ⇒ **放行**，而 SKILL 已是新的（**漏报/假绿**）；
② **pull 后先 update 再未 setup** ⇒ 消费仓=新、全局=旧 ⇒ 硬停，但文案只说「跑 `sdflow-init update`」，
而真正该跑的是 `bash setup.sh` ⇒ **误报且指错方向，用户按提示做会陷入循环**（`design.md:94` 的不等分支
未按缺失侧分流，只有 `:95` 的缺失分支分了流）。
**证据**：`design.md:71/94/95`、`setup.sh:503`（canonical `ln -snf`）、实测 `readlink ~/.sdflow/workflow`
→ `~/.skills/sdflow-skills/sdflow-init/assets/workflow`（**活软链**）。
**命中镜**：codex-CEO#1（critical）· design-voice#2（部分）· 主 session 独立
**置信度**：高 | **严重度**：致
**建议**：见 Q4（全局侧改实时解析）。**最低限度**：不等分支的文案 MUST 同时给出两侧命令，
不能只说 update。

**F2 · 判据比的不是本轮真正执行的 tools（非 pin 仓比了一个从未被读的副本）**
`resolve-workflow.sh:37-51` 的 pin 判据只看 `workflow.md` / `spec-checklists/` / `code-checklists/`，
注释明写「**不查 `openspec/workflow/` 目录——`tools/` 使其恒存在**」。
⇒ 非 pin 消费仓 `$RULES_ROOT` = **全局 canonical**，评审执行的是全局 tools（与 SKILL 同一 checkout，
**天然原子、不可能 skew**）；而 `design.md:87` **无条件**去读消费仓 `.bundle-version`。
∴ 对非 pin 仓：既**拦不住任何真 skew**（不存在），又会**因一个不参与执行的副本硬停**。
**实测锚**：本机三个装了 workflow 的仓 → `04-sdflow-skills`=global-canonical、`10-michi`=global-canonical、
`05-sarvelo`=**local-pin**；11 处 `$RULES_ROOT/tools` 调用点**全部**经 resolver，无一硬编码消费仓副本。
**命中镜**：codex-CEO#2（critical）· Claude-CEO-F3 · 对抗A-F3（反向确认本仓被正确排除）· 主 session 实测
**置信度**：高 | **严重度**：致
**建议**：只在 `RULES_ROOT == local-pin` 时比对；否则本层直接放行并说明原因。
**副产物**：`proposal.md` 「每个未 update 消费仓的每轮评审」**高估了覆盖面**，MUST 改写为
「本机制保护 pin 仓与源仓 dogfood，不保护每个外部消费仓的每一轮评审」。

### 🟠 高

**F3 · 版本 scope（整个 bundle）比实际部署集宽一个刻度 ⇒ 三分之一到一半的硬停是纯仪式**
非 full 实拷集 = `tools/`（去 tests）+ `lens-metric-contract.md` + `WORKFLOW-GUIDE.md`（`init.py:257-278`），
而版本取整个 `assets/workflow/`（`design.md:56`）⇒ 只改 `workflow.md` 一句措辞也触发硬停，
而 `sdflow-init update` **没有任何内容要同步**。
**三个独立口径实测**：codex 33/97（34%，近 30 天）· Claude 镜 45/129（35%，历史全量）·
主 session 10/19（53%，近 200 提交）。窗口不同故数字不同，**方向完全一致**。
**这一条最讽刺之处**：`design.md:60-62` 已经用**同一手法**否决了「整仓 HEAD」（理由：变太频繁 ⇒ 会被绕过），
却没把同一逻辑推到底。**本 change 标题里的 "precision" 正栽在这里。**
**命中镜**：codex-CEO#3+#5 · Claude-CEO-F1（critical）+F4 · 主 session
**置信度**：高 | **严重度**：高
**建议**：`git log` 的 pathspec 收窄到实际部署集（零额外成本，同一条命令换 pathspec）；
若采纳 Q2 则天然解决。

**F4 · 无事务语义，且「签版本」未绑定「canonical 接管成功」⇒ 给半复制/未切换现场签绿**
`init.py:262-264` 是 `rmtree(tools_dst)` → `copytree`；若中途失败而旧 `.bundle-version` 留存，
下一轮两侧仍相等 ⇒ 放行一个半残现场。
更进一步：`setup.sh:495-510` 的 canonical 更新失败**只记 `skipped` 并继续** ⇒ 若版本戳在该块之后统一写，
会给一个**未切换成功、甚至外来的** canonical 签上当前 SHA，**直接绕过 fail-loud**。
**本仓已有正解先例且本 change 声称复用却漏了最重要一条**：`setup.sh:513-524` 注释原文
「🔴 **先删 manifest、最后才写**……MUST NOT 留一份『自洽但陈旧』的快照」+ `cap_broken` 记账。
**命中镜**：codex-CEO#8 · codex-Eng#3 · design-voice#2
**置信度**：高 | **严重度**：高
**建议**：拷贝/安装前先**作废**版本戳；全部成功且 canonical 解析后确认指向本次 bundle，才原子 rename 写入。

**F5 · 「手改不回灌」被 memo 估为低概率边角，但它在 dev 窗口是常态 ⇒ 最关键窗口假绿**
`decision-memo.md`「接受的边角」判该项概率**低**，理由是「`CLAUDE.md:172` 明令禁止手改下游副本」。
**但那条明令管的是「改下游副本」，而 dev 窗口的实际路径是「改权威源后忘记 update」——不同的事。**
codex-Eng#9 的逐步推演（我认为成立）：dev setup 后首次硬停 → 跑一次 update 解除 →
**此后继续编辑未提交的 bundle，两侧 Git SHA 都不变 ⇒ 假绿**，而 local pin 已陈旧。
「主问题不是『把自己锁在评审之外』，而是**在真正开发 bundle 的窗口无法识别陈旧 dogfood 副本**。」
> 这一条同时**纠正了我自己**：我在复核早期曾推演为「本仓会被永久锁死」，codex-Eng 的推演证明是
> **可恢复停机**而非死锁。已按其结论修正。
**命中镜**：codex-Eng#9 · codex-CEO#4（dirty 子项）
**置信度**：高 | **严重度**：高
**建议**：采纳 Q2（内容摘要，覆盖工作树字节）；若维持 SHA，则 memo 该条 MUST 改写——
把概率从「低」改为「dev 窗口下为常态」，并如实登记本机制**不覆盖**该窗口。

**F6 · `SDFLOW_HOME` 非对称：写入方支持重定向，设计读取方硬编码 `~/.sdflow`**
`setup.sh:468` 用 `${SDFLOW_HOME:-$HOME/.sdflow}`；`resolve-workflow.sh:8-12` 把该变量列为**正式契约**
并明写「测试用它重定向，**绝不写真实 $HOME**」；而 `design.md:84-89` / `tasks.md:3` 固定 `~/.sdflow/bundle-version`。
**后果比"误停"更重**：它**违反本仓自己的开发期测试三层纪律**——第 1 层（零全局影响）依赖
`SDFLOW_HOME` 重定向，读取方硬编码 ⇒ 这套判据的 pytest **无法在沙盒内测**，只能翻真实 `$HOME`。
**命中镜**：codex-Eng#6 · design-voice#1
**置信度**：高 | **严重度**：高
**建议**：读取方统一 `${SDFLOW_HOME:-$HOME/.sdflow}`；测试 MUST 显式设一个 ≠ `$HOME/.sdflow` 的值。

**F7 · Windows 永久硬停，且有一个比 `unknown` 更坏的静默错值变体**
Windows 上 skill 由 `setup.sh` 的 `cp -r` 安装成**副本**，而 `init.py:44-46` 的 `BUNDLE_SRC` 由
`__file__` 推导 ⇒ 副本不在任何 checkout 内 ⇒ 消费侧只能得 `unknown`，全局侧（在源码仓跑 setup）得 SHA
⇒ **永久 `SHA != unknown` ⇒ Windows 永久硬停**。
**主 session 加重（codex 未点出）**：若用户的 `~/.claude` 恰好**是另一个 git 仓**（dotfiles 很常见），
`git -C <副本路径>` 会向上走到**那个无关仓**并返回一个**貌似合法的 40-hex SHA**
——比 `unknown` 更坏：**静默错值**，两侧永不相等且毫无线索。
（本机 `git -C ~/.claude rev-parse` = `fatal: not a git repository`，所以本机测不出来——
**这正是"本地 mac 照不到、必须真 Windows runner"那类坑**。）
**Unix 侧我实测可行**：`git -C ~/.claude/skills/sdflow-init/assets/workflow rev-parse --show-toplevel`
→ `~/.skills/sdflow-skills`（目录级 symlink 被 git 解析穿透）⇒ 取值 `ee5b4f4…` ✅。
**命中镜**：codex-Eng#2 · 对抗A-F2（值域一致性）· 主 session 加重
**置信度**：高 | **严重度**：高
**建议**：两侧**共用同一个版本计算例程**（Q3 的合并方案天然满足）；Windows 走
`~/.sdflow/workflow-path` 指针定位活 checkout（`setup.sh:489` 存的就是活路径，机制与 Unix `readlink` 对称）；
**且 MUST 在 Windows CI 真跑三态**，不接受只在 mac 推演。

**F8 · 空版本假绿：`git log` 对无历史路径是 rc=0 + 空 stdout，`|| echo unknown` 不兜底**
**本机实跑**：`V="$(git log -1 --format=%H -- no/such/path 2>/dev/null || echo unknown)"` → **`V=[] len=0`**。
`||` 只在**非零退出**时触发，而这里 git **成功退出**。⇒ 写出**空文件**。
而 delta spec（`spec.md:13`）只定义了「缺失」与字面 `unknown` 两态，**没有「存在但为空/畸形」态**
⇒ 两份空文件"均存在且相等" ⇒ **放行**。shallow clone（CI 常见）与 Q2/F3 收窄 pathspec 后都会命中此路径。
**命中镜**：codex-Eng#4 · design-voice#3 · 主 session 实跑复现
**置信度**：高 | **严重度**：高
**建议**：写入侧空输出**归一化为 `unknown`**；读取侧只接受严格 `^[0-9a-f]{40}$` 或字面 `unknown`，
空/空白/截断/畸形**一律按缺失硬停**；delta spec 补该态的 Scenario。

**F9 · 本 change 自称要解决的「结构上无法机械守」并未解决**
`design.md:120` 与 `tasks.md:37` 都明确承认「SKILL 是否真照判定表执行仍由执行方自报」，
`tasks.md:74` 把行为测试降为人工「真跑」。⇒ 新判据**仍然是散文、仍然复制进两个 SKILL、仍然无机械守**，
只是散文内容换了。`proposal.md:14` 把这一点列为旧方案的**第 2 条罪状**——新方案没解决它。
且 `adr/0038` 砍候选③的理由**张冠李戴**：它描述的是"脚本里逐特性写 grep"这一种**实现**，
不是"脚本化"路径的必然结果 ⇒ **ADR 把「判据形式」与「是否机械化」两个正交轴绑在一起砍了**。
**命中镜**：codex-CEO#9 · Claude-CEO-F2 · 对抗A-F5
**置信度**：高 | **严重度**：高
**建议**：见 Q3（并进 `resolve-workflow.sh`，两个 SKILL 只读退出码）。

**F11 · tasks 第 3 节存在恒真锚，且失败注入矩阵缺失**
`tasks.md:30-32` 只断言「40-hex 或 `unknown`」、`:33-35` 只断言「有内容」、`:36` 只断言「两边相同」
⇒ 两边**恒写 `unknown`**、**恒写整仓 HEAD**、甚至**恒写一个固定 SHA**，三种错实现**都能全绿**。
本仓已有同形状先例告警：`sdflow-init/tests/test_init.py:163-175`「fixture 与断言共用一个常量会恒真」。
**公允记录**：codex-Eng#7 同时指出 `full=True` 的**位置**断言（task 3.2）**确实**能在「写到调用点」时变红
——那一条是有效的，只是守不住版本**来源与准确性**。
失败注入全缺：并发双 setup / 双 update、ENOSPC、只读落点、`~/.sdflow` 被普通文件占位、
foreign canonical、`EACCES`、Windows CRLF、shallow clone、空/畸形/单侧 unknown，
且每个失败态都应断言「**没有可被判绿的旧戳**」。
**命中镜**：codex-Eng#7+#8
**置信度**：高 | **严重度**：高
**建议**：独立 Git fixture——提交 A 改 bundle、提交 B 只改仓外文件，**期望值精确等于 A**
（这样 HEAD / 固定值 / `unknown` 三种错实现全红）；**期望值独立计算，MUST NOT 调用生产 helper**。

### 🟡 中

**F10 · 拷贝不收敛，却仍发布「当前版本」证明** —— full 模式 `dirs_exist_ok=True` 不删上游已移除文件；
非-full 对 contract/guide 是 `if os.path.isfile(src)` 才覆盖 ⇒ **上游删除后下游副本永久残留**，
而版本戳照写当前 SHA（`init.py:254-259` / `:268-278`）。**命中镜**：codex-Eng#5 | 置信度高 | 严重度中
**建议**：为 managed bundle 建文件清单，部署到临时树后整体替换；未收敛时禁止写戳。若采纳 Q2 亦自然覆盖。

**F12 · 若采纳 Q3/F9 的下沉 helper，「helper 自己不存在」时的契约未定 ⇒ 裸 traceback**
**实测锚（真实数据，非假设）**：本机唯一真 pin 仓 `/Users/cheneyzhao/Documents/05-sarvelo`
（`resolve-workflow.sh --explain` → `source=local-pin`）的 `openspec/workflow/` **连 `tools/` 都没有**
（`workflow.md` mtime = Jun 29 2026）。⇒ 新 helper 在那里必然不存在，SKILL 会拿到
`python3: can't open file …` 的**裸错误**，而不是承诺的 fail-loud + actionable 文案。
**这恰好复刻了本 change 要消灭的形状**，只是崩溃点从"四条散文信号"搬到了"探测器自己"。
**命中镜**：对抗A-F1 | 置信度高 | 严重度中
**建议**：tasks 显式加契约——helper **不存在 / 不可执行 / 任何非零退出**一律折叠进「陈旧」同一路径；
补 pytest：删掉本地 helper 后断言走陈旧分支而非抛异常。

**F13 · 命中 TG 的三个模版必填槽全缺，且其中一个的缺失与 F1 因果相关**
我独立判定命中 `TG-10,TG-12,TG-14,TG-15,TG-18,TG-19,TG-22,TG-23`。核对必填槽：
- **TG-10（跨 3+ 组件协作）⇒ MUST 有序列图**（`design-diagrams.md:39`，`:85` 自检项）。
  本 change 跨 `setup.sh` / `init.py` / 两个 SKILL / `resolve-workflow.sh` **五个**组件，
  `design.md` 只有一张**静态**依赖图，**无序列图**。
  🔴 **这不是形式问题**：一张时序图（setup 写 → 用户 pull → update 写 → SKILL 读）会**立刻**暴露
  F1 的"快照 vs 实时"时间错位。**必填槽缺失与最严重的那条 finding 是因果关系，不是巧合。**
- **TG-12（复杂分支/决策逻辑）⇒ 流程/决策图**（`:42`）：四态判定表有表无图（表可部分代偿，从轻）。
- **TG-15（新增 codepath）⇒ 失败模式表(BASE-06) + 可观测性(BASE-11)**：`design.md` **两者全无**
  （只有 `Risks / Trade-offs`，不是失败模式表）。**F4/F8/F10 三条恰恰都是失败模式表会强制枚举出来的。**
**置信度**：高 | **严重度**：中（形式面）→ 但其**因果后果**已计入 F1/F4/F8
**建议**：补序列图（**优先，它是 F1 的诊断工具**）+ 失败模式表 + 可观测性一句话（本机制的可观测性
= 硬停文案本身，写明即可）。

### ⚪ 低（一行带过 · 可审计不静默丢）

- **F14** delta spec 引用 `anchor_lint.py:148` **错**——实际 `MANDATORY = (...)` 在 **`:203`**，`:148` 是 fence 解析代码。（接地镜；违反 `premise-verification`）
- **F15** `design.md:12` 的 `copy_bundle` 事实偏差——真实签名是 `copy_bundle(root, full=False, include_schema=True)`（**漏了 `include_schema`**），行号 `:228-286` 实为 **`:229-295`**。（接地镜 + 主 session）
- **F16** `decision-memo.md` D6 / `adr/0038` 引的实测值 `HEAD=0d024ae` 已过期（现 HEAD=`fc0f1ae`）。属时点测量、**非缺陷**；但 bundle 版本仍是 `ee5b4f4` ⇒ **D6 的结论依然成立**（我已复测）。
- **F17** `proposal.md` 无「假设列表」节（BASE-14）。本 change 确有未验证前提（「版本相等 ⇒ 能力兼容」「消费仓副本会被执行」——后者已被 F2 证伪），建议补。

---

### 🟠 高（续 · 对抗镜 B 独家，均经主 session 实跑复核）

**F18 · `init.py` 侧的 `-C <checkout>` 从未定义，而 git pathspec 是相对 cwd 的 ⇒ 字面照抄必得空值，且该 bug 与 D5 的 fail-open 同形 ⇒ 被永久伪装成「非 git 环境」**
`design.md:56-58` 给的是一条模板命令 `git -C <checkout> log -1 --format=%H -- sdflow-init/assets/workflow/`。
`setup.sh` 侧 `<checkout>` = `$REPO_DIR`（仓根）✅；但**消费仓侧（`tasks.md:7-10`，1.2）从头到尾没说 `<checkout>` 取什么**。
而 `init.py:44-46` 的 `SKILL_DIR` = **`sdflow-init` 这一层**（非仓根），`BUNDLE_SRC` 更深一层
——**init.py 现有变量里没有任何一个指向仓根**。
**主 session 实跑复核（决定性）**：
```
$ git -C .           log -1 --format=%H -- sdflow-init/assets/workflow/   → ee5b4f4…   rc=0  ✅
$ git -C sdflow-init log -1 --format=%H -- sdflow-init/assets/workflow/   → []  len=0  rc=0  ❌
$ git -C sdflow-init log -1 --format=%H -- :/sdflow-init/assets/workflow/ → ee5b4f4…   rc=0  ✅
```
⇒ 照字面拿最顺手的 `SKILL_DIR`/`BUNDLE_SRC` 当 `-C`，得到的是 **rc=0 + 空输出**（pathspec 相对 cwd 解析成
`sdflow-init/sdflow-init/assets/workflow/`）。
🔴 **最毒的部分**：这个实现错误的**表现形态与 D5 拍板的合法 fail-open 完全同形**
（都是"取不到版本 ⇒ 降级 `unknown`"）⇒ **一个真 bug 会被永久伪装成"这台机器不是 git 环境"**，
没有任何人会怀疑。若两侧都误配，`unknown == unknown` ⇒ **判相等 ⇒ 放行 ⇒ 机制形同虚设却永远显绿**。
**命中镜**：对抗B-F1 · 主 session 实跑复核
**置信度**：高 | **严重度**：高
**建议**：**推荐用 `:/` 前缀的 magic pathspec**（上面第三条实跑已验证）——它让命令**与 cwd 无关**，
比"记得传 `dirname(SKILL_DIR)`"更抗错，且天然满足 F7/Q3 的"两侧共用同一例程"。
并且：pytest MUST 断言两侧对**同一 checkout** 取到的值**逐位相等**，而不是各自"形如 40-hex"（后者测不出本 bug）。

**F19 · Windows 分支根本没有「刷 canonical 软链」这一步 ⇒ tasks 1.1 的写入锚点在该分支不存在 ⇒ Windows 永不创建版本文件**
`tasks.md:3` 把写入锚定在「**刷 canonical 软链的同一步**」。但 `setup.sh:475-511`：
Windows 分支写的是**指针文件** `workflow-path`（`printf > "$sdflow/workflow-path"`），**不创建软链**；
`ln -snf` 只存在于 else 分支。⇒ 照字面把写入代码插进 else 分支，**Windows 上 `~/.sdflow/bundle-version`
永远不会被创建** ⇒ 按设计自己的「缺失即陈旧」规则 ⇒ **Windows 永久硬停**，
且文案「跑 `bash setup.sh`」**具有欺骗性**（用户已经跑过了，文件就是不出现）。
**本仓已有正解先例，而 design 没引用它**：`capability-manifest.json` 的写入块在
**if/else 之外**（主 session 复核确认：三个 `fi` 收尾于 `:501-511`，manifest 段起于其后），对两个 OS 分支都生效。
🔴 **并且测试层同样失明**：`hack/tests/test_install_agents.py:14` docstring 自述
「Windows 分支：`IS_WINDOWS` 由 `uname -s` 决定，无环境变量覆盖入口 ⇒ 本机（Darwin）测不到」
——design 计划"沿用该模式"，却**没有登记这条诚实边界** ⇒ 绿色 pytest 会造成
「机械守住了」的假象，而 Windows 写入点**从未被验证过**。
**命中镜**：对抗B-F2 · 主 session 复核（与 F7 互补：F7 是取值端，本条是写入端）
**置信度**：高 | **严重度**：高
**建议**：写入点放在 `install_sdflow()` 的 if/else **之外**（仿 manifest 写法）；
`tasks.md` 3.4 的诚实边界 MUST 加一句「Windows 分支的写入点未被本机测试覆盖」。

**F20 · 判定表是四态，两处测试计划都只有三态 ⇒ 双-`unknown` 分支零覆盖，而它恰是 F18 的伪装面**
`design.md:91-96` 的判定表**四行**（相等 / 不等 / 任一缺失 / **两者同为 `unknown`**）。但：
`design.md:31` 与 `:119` 都写「相等/不等/缺失**三态**判定」；`tasks.md:59-60`「**三态**实测」；
`tasks.md:74` 更是**自己把四态映射到三态**——「SKILL 判定表（**四态**）行为 → 真跑**三态**实测」。
⇒ 「两侧同为 `unknown` ⇒ 相等 ⇒ 放行」这一整支，**从 pytest 到人工真跑，全计划无任何一处会触发**。
🔴 **这不是无害遗漏**：它正是 F18 那个 bug 最容易伪装成"正常"的分支
⇒ 一个让两侧都退化到 `unknown` 的实现错误，会在「全仓 pytest 绿 + 三态实测三项全过」的报告下**顺利过关**。
**命中镜**：对抗B-F4 · 主 session 复核（grep 实证四处计数不一致）
**置信度**：高 | **严重度**：高
**建议**：3.x 与 5.3 补第四态，且该测试 MUST 验证**两侧确实各自独立跑过取值命令并得到 `unknown`**，
而不是手写两个 `unknown` 字符串进文件再测比较逻辑（后者仍测不出 F18）。

### 🟡 中（续 · 对抗镜 B）

**F21 · delta spec 正文内嵌 `sed` 事故叙事，与 `adr/0038` 几乎逐字重复 ⇒ 违反 DOC-1 / BASE-30**
`spec.md:9` 内嵌「已实证一次 `sed` 无行首锚定命中散文、截出散文段而误判陈旧，几乎硬停一轮完整评审」，
与 `adr/0038:24-27` 近乎逐字。**而同一句话里已经写了「理由全文见 `openspec/adr/0038`」**
——作者知道该指哪，却仍把叙事也复制进正文，形成双份存档。
按 DOC-1 判据②（删除测试）：删掉该叙事后，「MUST NOT 回退为逐能力内容探测，因结构上无法机械守、
失效方向为假阴」依然完整自洽。**命中镜**：对抗B-F5 | 置信度中 | 严重度中
**建议**：正文只留禁令 + 一句"结构上无法机械守" + 指针；事故叙事整段留在 ADR。

**F22 · 落点字面路径只出现在 `design.md`/`tasks.md`，delta spec 用占位符 ⇒ 归档后主 spec 不自足**
全仓 grep `bundle-version` 只命中 `design.md`（:71-72/79/87-88/129）与 `tasks.md`（:3/8/30/34/46）；
`decision-memo.md`、`adr/0038`、**delta spec 一次都没出现**具体路径，delta spec 只写占位符 `<bundle 路径>`（`:7`）。
本 change 归档后，长期查阅入口是 `openspec/specs/host-adaptive-execution/spec.md`（"盘面即状态"的单一源），
而 change 目录不是 ⇒ **未来只读主 spec 的人读不到版本文件落在哪**。
且**同一份 spec 文件的其它 Requirement 都给了字面路径**（如 `~/.sdflow/hack/resolve-models.sh`）
⇒ 同文档内具体化程度不一致（BASE-07）。**命中镜**：对抗B-F6 | 置信度中 | 严重度中
**建议**：delta spec 补一行字面路径即可。

**F23 · Scenario「探测判据不得随 bundle 新增特性而增条目」不可测 ⇒ 孤儿需求（BASE-17）**
该 Scenario（`spec.md:29-31`）的 WHEN/THEN 描述的不是系统在某输入下的可观察行为，
而是**对未来人类作者的写作约束**——没有脚本能在当下判定它过/不过，它永远处在"尚未被违反"状态。
**tasks.md 自己证实了这点**：5 个 task 组无一引用它；「测试覆盖图（TG-18）」（`:65-77`）**没有对应行**。
**命中镜**：对抗B-F3 | 置信度高 | 严重度中
**建议**：它本质是 `adr/0038` 的设计原则复述（ADR 里已有对等表述）⇒ 从 Scenario 撤出，
留在 design/ADR 的 Decision 陈述里。Scenario 是要驱动测试的，包不能测的东西进去只会制造"永远空转"的假象。

### ⚪ 低（续 · 对抗镜 B）

- **F24** `tasks.md:18` 标「〔Req: 同上·**四个 Scenario**〕」，而该 Requirement 实际有 **5 个** `#### Scenario`；且「四态」（表格行数）与「Scenario 数」是两个不同计数维度，混用会让 task↔spec 追溯数错。
- **F25** 版本写入**自身**失败（磁盘满 / 只读 / 并发）未在 design 显式声明兜底路径。可论证"写失败 ⇒ 文件缺失 ⇒ 按缺失硬停"能兜住，但**这是推出来的、design 没明说**，用户看到硬停不会知道是"没跑 update"还是"写失败了"。对照 `setup.sh:516-526` 的 manifest 写入失败已有专门 `skipped+=()` + 注释。按 ④ 属可接受简化，但**应有一句显式声明**，不该留白。

## 对抗镜 B 的 BASE-01~30 逐条判定（独立跑的，主 session 未改其判定）

**判「不过」9 项**：BASE-03（可测试性，F20/F23）· **BASE-05（可行性，F18/F19）** · BASE-06（失败模式表，F25）·
BASE-07（内部一致性，F22）· **BASE-09（清晰度：工程师拿着 design 无法直接实现，F18）** ·
BASE-14（假设列表缺失）· BASE-17（孤儿 Scenario + 计数不符）· **BASE-27（时序可执行性：F18/F19 正是"实现者第 1-2 小时会撞到但 spec 没提前说清"的典型）** · BASE-30（正文考古层，F21）。
**判 N/A 8 项**：BASE-16/20/25/26/28/29 等（无 NFR / 无外部方 / 非新架构 / 无计费 / 无信任边界 / TG-25 未命中）。
**其余判过**，部分标注"弱"或"轻量"。

> **一处镜间分歧（如实登记，未静默压制）**：对抗镜 B 判 **BASE-19「过（弱）」**，认为
> 「TG-10 序列图是否强制触发**存疑**但非硬缺」；**主 session 维持 F13 的判定**——
> `design-diagrams.md:39` 是「跨 3+ 组件协作 → **序列图**」的明文表格行，`:85` 还有对应自检项，
> 本 change 跨五个组件 ⇒ **命中即 MUST**。
> **但我采纳 B 的"非硬缺"这一半**：故 F13 严重度定为**中**（形式面），
> 其**实质后果**已分别计入 F1/F4/F8，不重复计数。

## 已裁掉（反静默压制 · 原始发现 + 裁掉理由，供人复核"裁得对不对"）

**X1 · codex-CEO#4 的子项「新 SKILL 忘记实现对应工具能力 ⇒ bundle SHA 不变 ⇒ 假绿」——降级不采纳**
**裁掉理由**：若 SKILL 与 tools 来自**同一个提交**，该提交内部的自洽性（SKILL 要求的能力，tools 里有没有）
是**开发者在单次提交内的 bug**，任何 skew 探测器都不该也无法负责——skew 探测的定义域是
"两侧是否同代"，不是"同代的东西对不对"。codex 的另两个子项（dirty 假绿、`unknown==unknown` 保护消失）
**已分别并入 F5 与 F8**，未丢弃。

**X2 · codex-Eng#1「`copy_bundle()` 会沿消费仓软链 `rmtree` 删除仓外目录」[critical] —— defer + 记 bug，不 fold**
**原始发现成立**：`init.py:253` 直接拼 `dst = root/openspec/workflow` 未做 `lstat`/containment，
随后 `rmtree(dst/tools)`；若 `openspec/workflow/` 是软链，会沿链删掉真实目标（可能是全局 canonical）。
`--dev` 守卫（`:1097-1100`）只校验仓根，不查 workflow 路径组件。
**裁掉（defer）理由**：这是**既存 bug、非本 change 引入**。过 BASE-18 防吸积 AND 门
（同 capability ∧ 高耦合 ∧ 低增量）：同函数 ⇒ 高耦合 ✅；但**不同 capability**（路径 containment 安全 ≠ skew 判据）❌；
**非低增量**（需逐级 `lstat` + victim-sentinel 测试矩阵 + 自身设计审）❌ ⇒ **两项不满足 ⇒ defer**。
**⇒ 建议单独记 bug**（`/sdflow-issues`），标 critical。**MUST NOT 因为"顺手"折进本 change**——
那正是通则③ 的"不加宽"。
> 🔴 **本条我未擅自记入 issues**——记 bug 会改仓内状态，且本轮是评审、不是实现。请人拍板后我再记。

**X3 · 接地镜「Success Metrics 的归零条件已满足，SKILL:180/206 是新版本对比逻辑」—— 驳回**
**驳回依据（实跑证伪）**：`grep -n "lens-metric-enums\|scope-audit:\|_MIRRORS_LEGAL" sdflow-code-review/SKILL.md
sdflow-spec-review/SKILL.md` 实际输出显示 `:206`（code-review，四条信号）与 `:180`（spec-review，两条信号）
**仍是旧的逐能力内容信号原文**。该镜自身在同一份报告里也正确报告了「仓内无 `.bundle-version` 实现（设计未落地）」
——**它自相矛盾**。本 change 未实现，归零条件**尚未满足**（这是预期状态，不是缺陷）。
该镜其余 17 项事实核验经抽查为真，予以采信（F14/F15 即出自它）。

---

## 度量锚说明（信任边界，MUST NOT 读作机械保证）

上方四条 `lens-metric` 锚由 `lens_metric_emit.py --layer spec-review --host claude` 产出（exit 0），
**MUST NOT 手拼**。emitter 只保证「给定输入的确定性归约」，**不保证输入本身对不对**：
分类正确性（某条 finding 该归哪个镜）· roster 完备性 · findings JSON 誊写准确
**仍是主 session 的信任边界**。

**两条如实登记的口径说明**：
1. **主 session 独家的 finding 不进 lens-metric**——F13（TG 必填槽缺失）、F16（D6 实测值过期）
   与 Q4 是我自己在复核中发现的，**没有任何镜独立报到过** ⇒ 它们不属于任何 lens，
   计入会污染各镜的 `独立` 数。故 lens-metric 的 findings 总数（28）**小于**本报告的条目总数。
2. **`outside-voice` 行 `独立=0` 不代表它没价值**——它报的 3 条全部与 autoplan-eng 收敛
   （F4/F6/F8）。**收敛本身就是它的价值**：它拿到的 context 只有 `proposal「What Changes」+
   design「Decisions」`（摘录规则定死，design 的 Decisions 段本身只有 3 行指针），
   却仍独立走到同样的结论 ⇒ 这三条的置信度因此被上调到高。

**〔SR-M〕** 上述锚为**门前草稿值**。设计门拍板可翻改「需拍板」项（Q1–Q4）的去向 ⇒
拍板回写时 MUST 原地重算覆盖这四行（不新开行）。此重算**无机械兜底**（聚合器分不清草稿/最终），
是已知局限。

## 收敛口

🔴 **不建议进设计 HARD-GATE 批准；建议返工后再审。**

**理由**：判据形式的大方向（逐能力内容探测 → 版本对比）**是对的，且论证充分**，
本报告没有任何一条主张推翻它。但落到具体判据，它在**三个正交维度上各指错了一次**：

| 维度 | 错在哪 | finding |
|---|---|---|
| **比错了东西** | 非 pin 仓真正执行的是全局 tools，消费仓副本从未被读 | F2（致） |
| **比错了时点** | 全局侧是 setup 时快照，而 SKILL 实时生效 | F1（致） |
| **比错了粒度** | scope 取整个 bundle，实际部署集只有其中一部分 | F3（高） |

加上**四条会让机制静默失效的实现级洞**（F18 取值上下文未定义且伪装成 fail-open ·
F19 Windows 写入点不存在 · F8 空值假绿 · F20 第四态零测试覆盖），
以及**本 change 自称要解决的「结构上无法机械守」并未解决**（F9）。

**返工面已被精确定位，不是"推倒重来"**：F1/F2/F3 各自的修法都在同一条 `git log` 命令的
参数层面（换 pathspec / 加 pin 判断 / 改实时解析），F18 的正解（`:/` magic pathspec）已实跑验证。
若一并采纳 Q2（内容摘要）与 Q3（并进 `resolve-workflow.sh`），
则 F5/F7/F8/F10 与 F6/F7 的双实现漂移面**同时归零**。

**人需要拍板的只有 4 件事（Q1–Q4），其余 21 条 finding 的修法我已给到可直接落 tasks 的粒度。**
Q1（是否扩 scope 消灭双链）与 Q2/Q4（改动人已拍板的 D2/D3/D4）**MUST 由人决定**——
通则③ 明令我 MUST NOT 自行加宽、也 MUST NOT 悄悄改人拍过板的决策。

**下一步建议**：`/sdflow-spec`（相位 B 重开拷问，带上本报告的 Q1–Q4 与 F1/F2/F3 三条致命/高）
→ 修订四件套 → `/clear` → 换评审档 → 重跑 `/sdflow-spec-review`（窄复核，只审增量）。

> **本报告的诚实边界汇总**（MUST NOT 被读作"全相位已跑"）：
> ① **领域镜 0 个**——本 change 命中零个栈领域，`domains/` 下无适用清单，故 roster 无 domain 行（非遗漏）。
> ② **autoplan 的 Eng 相位为单声**（只有 codex），**Design/DX 双声未跑**——理由与代价见
>    `gstack-review.md`「本轮明示偏离②」。
> ③ **能力探针**（`fanout-capability` 锚）与 **native 声明**均为主 session 自报，
>    `anchor_lint` 只核锚行文法自洽，**核不了它是否对应一次真 spawn** ⇒ 非机械门。
> ④ **Windows 相关的两条（F7/F19）本机结构性测不到**——`IS_WINDOWS` 由 `uname -s` 决定、无环境变量覆盖入口
>    （`hack/tests/test_install_agents.py:14` 自述）。它们是**读码推演 + 实测旁证**，不是本机实跑结论。
