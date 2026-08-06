<!-- sdflow:step1-broad-review v1 mode="native" -->

# Step1 广审报告 · fix-probe-scan-precision

**执行方式**：`mode="native"` —— autoplan 经 Skill 机制原生执行于主 session（其 SKILL.md 指令直接进主
session 执行，未派子代理转述模拟）。
**native 声明的侧信道佐证**：autoplan 的 preamble bash 真跑并回显 `BRANCH: feat/fix-probe-scan-precision` /
`REPO_MODE: solo` / `SLUG: laodao-ai-sdflow-skills`；Phase 0 restore point 真落盘
`~/.gstack/projects/laodao-ai-sdflow-skills/feat-fix-probe-scan-precision-autoplan-restore-20260806-180448.md`
（500 行）；Phase 0.5 codex preflight 真跑并回显 `codex-cli 0.146.1` / `CODEX_AVAILABLE=true`。

## 相位覆盖与如实降级

| autoplan 相位 | 本轮是否跑 | 说明 |
|---|---|---|
| Phase 0 intake + restore point | ✅ 跑了 | restore point 落盘（上方路径） |
| Phase 0.5 codex preflight | ✅ 跑了 | `CODEX_AVAILABLE=true`，codex-cli 0.146.1 |
| Phase 1 CEO（codex voice） | ✅ 跑了 | 9 条 finding，见下 |
| Phase 1 CEO（Claude 独立子代理） | ✅ 跑了 | 见下 |
| Phase 2 Design | ⏭️ 跳过 | UI scope 未命中。grep 到的 `form` 等命中经逐条核验为假阳（`--format=%H` 里的 `format`），本 change 零 UI 面 |
| Phase 3 Eng（codex voice） | ✅ 跑了 | 见下 |
| Phase 3 Eng（Claude 独立子代理） | ❌ **未跑（如实降级）** | 见下方「本轮明示偏离」 |
| Phase 3.5 DX（双声） | ❌ **未跑（如实降级）** | 见下方「本轮明示偏离」 |

## 🔴 本轮明示偏离 autoplan 标准流程（两条，均非静默）

**偏离①：Phase 1/3 的两把声音改为并发起跑，未按 autoplan 的「先子代理、后 codex，均前台」串行。**
理由：autoplan 要求两把声音串行的落点是「both must complete before building the consensus table」，
而 Claude 子代理被明确要求 **NO prior-phase context**（设计上就独立于 codex 那把），
∴ 并发不破坏它要保的性质，只省墙钟。已实测本机主 session 的后台任务不会被轮次终结回收。
**代价**：无（consensus table 仍在两把都回来之后才建）。

**偏离②：Phase 3 的 Claude 子代理与整个 Phase 3.5（DX 双声）未跑。**
理由（④ 简化 + 止损）：CEO 相位已产出 **2 条 critical + 4 条 high**，且每一条都经主 session
**独立读码复核确认**（非采信 voice 自述），设计已确定需要返工；在一份即将返工的设计上再加两对声音，
边际价值低于其成本。
**代价（如实登记）**：DX 镜的「报错文案是否 actionable」这一维度未被独立跑过——
但该维度已由 F5（不等分支文案指错方向）从 CEO/Eng 侧覆盖到；
Eng 侧的 Claude 独立视角缺失，其覆盖面由 codex Eng 声 + 接地镜 + Step2 的对抗镜替代。
**⚠️ 本报告 MUST NOT 被读作「autoplan 全相位已跑」。** 设计返工后若需要，这两处可单独补跑。

---

## CODEX SAYS（CEO — strategy challenge）

**runner**：codex / gpt-5.6-sol · exit 0 · 108,743 tokens
**结论原文**：「当前计划不应批准。它没有可靠探测目标 skew，反而会同时制造假绿和高频误停。」

9 条 finding（原文摘要，主 session 复核结论见括号）：

1. **[critical] 全局版本记录的不是「当前 SKILL 所期待的版本」** —— `~/.sdflow/bundle-version` 只在
   `setup.sh` 时更新，SKILL 经 symlink 在 `git pull` 后立即变化 ⇒「pull 后、setup 前」窗口两侧旧版本
   仍相等 ⇒ **假绿**。证据 `design.md:71` vs `setup.sh:163`/`setup.sh:503`。
   （**主 session 复核：确认成立**，见下方 F1。）
2. **[critical] 判据比较的不是本轮真正执行的 tools** —— `resolve-workflow.sh` 对非 pin 消费仓解析到
   全局 canonical，实际执行的是全局 tools；设计却无条件读消费仓 `.bundle-version`。
   证据 `resolve-workflow.sh:37/53`、`design.md:87`。（**主 session 复核：确认成立**，见 F2。）
3. **[high] 「整个 bundle 的 SHA」被写给一个只复制部分 bundle 的产物** —— 版本取整个
   `assets/workflow/`，非 full 模式只拷 `tools/` + contract + guide。证据 `design.md:56`、
   `init.py:229/260-278`。（**确认成立**，见 F3。）
4. **[high] Commit SHA 不证明内容相同，更不证明能力兼容** —— dirty 假绿 / rebase 假红 /
   `unknown==unknown` 保护消失。（**部分成立**：dirty 与 `unknown` 两项 ADR 已显式接受并登记；
   「新 SKILL 忘实现工具能力」属单提交内自洽性 bug，非 skew 探测应负责的面 ⇒ 主 session 降级为 medium，
   见 X1。）
5. **[high] 误报率高到足以训练出「无脑 update」肌肉记忆** —— codex 实测近 30 天 33/97（34%）硬停中
   `update` 不改变任何既有部署文件。（**确认成立且被独立复现**：主 session 另一口径实测近 200 提交
   19 个动 bundle、其中 10 个不动 `tools/` ⇒ 约 53% 属纯仪式停。见 F3。）
6. **[high] 10 倍收益的「消灭双链」方案根本没进候选集** —— 且 `adr/0003` 当初保留消费仓 tools 的
   承重理由是 HTML viewer/server 路径，而同一 ADR 顶部已声明该 viewer 整体移除。
   （**确认成立，且这是本轮最重的一条**，见 Q1。）
7. **[medium] 「全文件指纹」被草率否掉** —— ADR 以 O(n) 为由砍掉，但 bundle 仅 64 个非测试文件
   / ≈566 KB，对一次多代理评审可忽略。（**成立**，见 Q2。）
8. **[high] 版本戳没有失败事务语义，会给半复制现场签绿** —— `copy_bundle()` 先 rmtree 后 copytree；
   仓内既有 `capability-manifest` 已确立「先删、最后写」，本计划声称复用该模式却漏了最重要的事务规则。
   证据 `init.py:261`、`setup.sh:513`。（**确认成立**，见 F4。）
9. **[medium] 新方案仍没机械守住真正的判定逻辑** —— 判据仍是散文、复制进两个 SKILL、由 agent 自行解释；
   测试只守写入点。证据 `design.md:120`、`tasks.md:37/74`。（**确认成立且升为 high**，见 F6。）

**战略盲点总结（原文）**：「这个计划在给错误的系统边界加版本戳。它比较的是『上次 setup』与『上次 update』，
不是『当前 SKILL』与『本轮实际执行工具』。」

## CLAUDE SUBAGENT（CEO — strategic independence）

**runner**：claude / sonnet 档 · fresh context · 无前序相位 context（独立性设计使然）· 27 次工具调用

5 条 finding + scope 结论：

1. **[critical] 新判据自身犯了它要根治的那种「精度错误」——版本 SHA 的 scope 比实际可漂移集合更宽。**
   非 full 分支只拷 `tools/` + `lens-metric-contract.md` + `WORKFLOW-GUIDE.md`；而版本取整个
   `assets/workflow/`。**独立实测**：`git log -- assets/workflow/` = 129 个提交，
   其中只碰"会被拷进消费仓那部分"的 = 84 ⇒ **35%（45/129）的版本变更只碰从不拷贝的规则文件**。
   「`design.md:60-62` 已用同一手法否决了整仓 HEAD，却没把同一逻辑推到底——bundle 目录本身
   也不是最小可漂移集合」。修法零成本：同一条 `git log` 换 pathspec。
2. **[high] ADR 砍候选③（`skew_probe.sh`）的理由张冠李戴** —— 该理由描述的是"脚本里逐特性写 grep"
   这一种**实现**，不是"脚本化"路径本身的必然结果；而「恰好 scope 到拷贝集合的 SHA」这个
   **选中方案的更精确变体**从未作为独立候选被比较过。
3. **[medium] 「杀掉拷贝链」这个 reframe 被正确放弃了，但暴露面从未追到底。**
   → 见下方 **TENSION-1**（本条与 codex CEO #6 正面冲突）。
   同时独立得出与 codex #2 相同的结论：非 pin 消费仓 `$RULES_ROOT` 恒 = 全局 canonical，
   本地拷贝**在真正会执行的路径上从头到尾没被读过** ⇒ 实际暴露面只有两类：
   ① 显式本地 pin 的仓；② **本仓自己的 dev-checkout dogfood 循环**
   （`docs/sdflow-fable5/20260717.md:193` 已实锚过一次真实漂移事故）。
   ⇒ proposal 的「每个未 update 消费仓的每轮评审」**高估了覆盖面**。
4. **[medium] 伪阳性率比 memo 承认的更糟**：近 30 天 1083 提交中 97 个（9%）动 bundle；
   历史 35% 的 bundle 提交只碰非拷贝文件 ⇒ 约每 33 个提交 1 次**功能上完全不必要**的硬停。
   memo 把该代价估低了，因为没把 scope 错配计入。
5. **[low] 「检测到不等直接自动跑 update」从未进候选集**，也没记"为何不自动修"的一行论证
   （可能撞 `init.py:234-236` R-MRF-1 的"绝不自动改消费仓文件"纪律）。建议补一行，省得下次重新纠结。

**scope 校准结论**：**范围本身没问题**。把「机制替换(P0) + CLAUDE.md 订正(P1) + 关闭 T269/T270(P1)」
折进同一 change 符合本仓既有 fold-vs-defer 纪律，**未发现拆碎或混入不相干功能**。
「真正的问题是精度不够，不是装的东西不该在这里。」

## CODEX SAYS（Eng — architecture challenge）

**runner**：codex / gpt-5.6-sol · exit 0 · 137,387 tokens
**结论原文**：「这份计划不应进入实现。除已知 5 条外，仍有 2 个可导致数据破坏的边界和多条稳定假绿路径。」

9 条 finding（主 session 复核结论见括号）：

1. **[critical] `copy_bundle()` 会沿消费仓软链删除仓外目录** —— `init.py:253` 直接拼
   `dst = root/openspec/workflow` 未做 `lstat`/containment，随后 `rmtree(dst/tools)`；
   若 `openspec/workflow/` 是软链，可删掉全局 canonical 或任意仓外目录。`--dev` 守卫只校验仓根。
   （**成立，但属既存 bug、非本 change 引入** ⇒ 主 session 按 BASE-18 的 AND 门判 **defer + 记 bug**，
   见 X2。）
2. **[high] Windows 下两侧不可能稳定取得同一个 Git 版本** —— Windows 装的是 skill **副本**
   （`setup.sh` `cp -r`），`init.py:44-46` 的 `BUNDLE_SRC` 由 `__file__` 推导 ⇒ 副本不在任何 checkout 内
   ⇒ 消费仓侧只能得 `unknown`，而 `setup.sh` 在源码仓得 SHA ⇒ **永久 `SHA != unknown` ⇒ Windows 永久硬停**。
   （**确认成立，且主 session 复核发现一个 codex 没点出的更坏变体**，见 F8。）
3. **[high] 新版本戳没有安装状态机，会和 canonical、capability manifest 裂脑** —— Unix canonical
   更新失败只记 `skipped` 并继续（`setup.sh:495-510`）⇒ 版本戳可能给**未切换成功**的 canonical
   签发「最新」证明。（**确认成立**，见 F4 的同族，合并入 F4。）
4. **[high] shallow clone / 无路径历史会写出空版本，两份空文件被当作同步** ——
   `git log ... || echo unknown` 只处理**非零退出**；路径在浅历史中无可见提交时 git **成功退出但输出为空**。
   （**主 session 本机实跑复现**：`rc=0 stdout_len=0` ⇒ 见 F9。）
5. **[high] 拷贝并不收敛，却会发布「当前版本」证明** —— full 模式 `dirs_exist_ok=True` 不删上游已移除文件；
   非-full 对 contract/guide 是「源存在才覆盖」，源删除时旧副本永久残留，而版本戳照写当前 SHA。
   （**确认成立**，见 F10。）
6. **[high] 写入方支持 `SDFLOW_HOME`，读取方却硬编码 `~/.sdflow`** —— `setup.sh:468`
   `${SDFLOW_HOME:-$HOME/.sdflow}`、`resolve-workflow.sh:8-12` 把该变量列为正式契约
   （「测试用它重定向，**绝不写真实 $HOME**」），而 `design.md:84-89` 固定读 `~/.sdflow/bundle-version`。
   （**确认成立，且后果比 codex 说的更重**，见 F6。）
7. **[high] 第 3 节测试存在恒真锚，守不住 1.1/1.3** —— 只断言「像版本」「两边相等」⇒
   两边恒写 `unknown`、恒写整仓 HEAD、甚至恒写固定 SHA **都能全绿**。
   并引本仓既有先例 `test_init.py:163-175`「fixture 与断言共用一个常量会恒真」。
   **公允之处**：它同时指出 `full=True` 的位置断言**确实**能在「写到调用点」时变红（task 3.2 对该目的有效），
   只是守不住版本来源与准确性。（**确认成立**，见 F11。）
8. **[high] 失败注入矩阵缺失** —— 自动化只有三条成功态断言，相等/不等/缺失全留人工实测。
   给出 10 条具体注入用例（并发双 setup / 双 update、`/dev/full` 注 ENOSPC、只读落点、
   foreign canonical 真实目录、`EACCES`、Windows CRLF、shallow clone、空值/畸形/单侧 unknown，
   且**每个失败态都要断言「没有可被判绿的旧戳」**）。（**确认成立**，见 F11。）
9. **[high] Dogfood 不会永久锁死本仓，但会在最关键的开发窗口假绿** ——
   **这条纠正了主 session 自己的一个错误假设**（我此前推演的是"本仓被永久锁在评审之外"）。
   codex 的逐步推演结论：dev setup 后首次会硬停（本仓无 `.bundle-version`）→ 跑一次 update 即解除
   → **此后再编辑未提交的 bundle，两个 Git SHA 都不变 ⇒ 判据假绿**，而 local pin 已陈旧。
   「主问题不是『把自己锁在评审之外』，而是**在真正开发 bundle 的窗口无法识别陈旧 dogfood 副本**。」
   （**确认成立，且这一条推翻了 memo 对「手改不回灌」概率的估计**，见 F5。）

## ENG DUAL VOICES — CONSENSUS TABLE

```
ENG DUAL VOICES — CONSENSUS TABLE:
═══════════════════════════════════════════════════════════════
  Dimension                            Claude  Codex  Consensus
  ──────────────────────────────────── ─────── ─────── ─────────
  1. Architecture sound?               N/A     NO      单声（Claude Eng 未跑，见「本轮明示偏离②」）
  2. Test coverage sufficient?         N/A     NO      单声
  3. Performance risks addressed?      N/A     N/A     N/A（无性能面）
  4. Security threats covered?         N/A     NO      单声（#1 软链越界删除）
  5. Error paths handled?               N/A     NO      单声
  6. Deployment risk manageable?       N/A     NO      单声
═══════════════════════════════════════════════════════════════
⚠️ Eng 相位为**单声降级**（只有 codex 一把）。按 autoplan 口径「Missing voice = N/A，不算 CONFIRMED」，
   本表 6 项**无一条达到 CONFIRMED**；但「单一 voice 的 critical finding 照样上报」，
   且下方 6 条已由主 session **独立读码复核**（复核实据见「主 session 的独立读码复核」表的第二批）。
```

## 主 session 独立读码复核（第二批 · Eng 相位）

| 复核项 | 命令 / 文件 | 实测结果 |
|---|---|---|
| 空版本假绿（Eng #4） | `V="$(git log -1 --format=%H -- no/such/path 2>/dev/null \|\| echo unknown)"` | **`V=[] len=0`** —— rc=0 ⇒ `\|\| echo unknown` **不触发** ⇒ 写出**空文件**；spec 只定义「缺失」与字面 `unknown` 两态，**无「存在但空/畸形」态** ⇒ 两份空文件相等 ⇒ 放行 |
| `BUNDLE_SRC` 推导（Eng #2） | `init.py:44-46` | `SKILL_DIR = dirname(dirname(abspath(__file__)))` → `BUNDLE_SRC = SKILL_DIR/assets/workflow`（**由 `__file__` 推导，非仓根**） |
| Unix 侧是否可行 | `git -C ~/.claude/skills/sdflow-init/assets/workflow rev-parse --show-toplevel` | → `~/.skills/sdflow-skills`，取值 `ee5b4f4…` ✅ **Unix 可行**（目录级 symlink 被 git 解析穿透） |
| Windows 侧 | `setup.sh` Windows 分支 `cp -r "$skill_dir" "$target"` | 副本**不在任何 checkout 内** ⇒ 见下方 F8 的**加重结论** |
| `~/.claude` 是否 git 仓（本机） | `git -C ~/.claude rev-parse --show-toplevel` | `fatal: not a git repository` ⇒ 本机无误落风险，但**这是本机偶然事实、非契约** |
| `SDFLOW_HOME` 契约（Eng #6） | `setup.sh:468`、`resolve-workflow.sh:8-12` | 写入方走 `${SDFLOW_HOME:-...}`；resolver 契约明写「测试用它重定向，**绝不写真实 $HOME**」；而 design 固定读 `~/.sdflow` |
| 拷贝不收敛（Eng #5） | `init.py:254-259` / `:268-278` | full 用 `dirs_exist_ok=True`；contract/guide 仅 `if os.path.isfile(src)` 才 copy ⇒ **上游删除后下游永久残留**，确认 |
| 恒真锚先例（Eng #7） | `sdflow-init/tests/test_init.py:163-175` | 该文件确有「fixture 与断言共用常量会恒真」的既有告警先例，codex 引用属实 |
| 命中 TG 的模版必填槽 | `design-diagrams.md:39/85`、`spec-quality-base.md` BASE-06/11 | TG-10 命中 ⇒ **MUST 有序列图**（`:39`「跨 3+ 组件协作 → **序列图**」、`:85` 自检项）；TG-12 ⇒ 流程/决策图；TG-15 ⇒ 失败模式表(BASE-06)+可观测性(BASE-11)。**design.md 三者全无**（只有一张静态依赖图） |

## 🔀 TENSION-1（两把 CEO 声音正面冲突 —— MUST NOT 静默采纳任一方）

**冲突点**：能不能直接**删掉消费仓的 `openspec/workflow/tools/` 拷贝**，从根上消灭 skew 这一整类问题？

- **codex CEO #6（主张删）**：`adr/0003:8` 保留该拷贝的承重理由是 review HTML 服务器根
  （「不落地即 404」），而 `adr/0003:3` 已声明该 viewer **整体移除**；`:18` 砍掉「连 tools 也不落地」
  的唯一理由是「省 serve.sh 重写」——**serve.sh 已不存在**。∴ 原始承重理由已死，应优先删拷贝，
  让 SKILL / tools / contract 原子同源。「只有证明这条路不可行后，才批准 skew 探测器。」
- **Claude CEO F3（主张留）**：**不能删，且这不是疏忽**。`ship_gate.py:953-955` 需要
  `openspec/workflow/tools/` 在**消费仓自己的 git 历史里**真实存在——它用 `git ls-tree`
  对比锚 commit 与 HEAD 做 code 域失鲜判定。这是一条**新的**承重理由，
  `adr/0003` 与本 change 都没写过（本 change 只引用了已作废的"服务器根"理由）。

**主 session 裁决**：**两边都对了一半，且 codex 的结论不能直接照做。**
主 session 独立复核 `ship_gate.py:953-957` 确认：它对 `tools_spec` 做 `ls_tree_map(root, sha)` 与
`ls_tree_map(root, "HEAD")` 两次比对。**若拷贝被删，两侧都返回空集 ⇒ 该失鲜腿静默退化为恒真锚**
（永远判"没漂移"），而不是报错——即「删拷贝」有一个 codex 没算到的具体爆炸半径。
∴ 删拷贝**可行但不免费**：须同时给 ship_gate 的 tools 失鲜信号重新安家。
**这超出本 change 的 scope，且 MUST NOT 由我自行加宽（通则③）** ⇒ 升 `Q1` 交人拍板。

## CEO DUAL VOICES — CONSENSUS TABLE

```
CEO DUAL VOICES — CONSENSUS TABLE:
═══════════════════════════════════════════════════════════════
  Dimension                            Claude  Codex  Consensus
  ──────────────────────────────────── ─────── ─────── ─────────
  1. Premises valid?                   NO      NO      CONFIRMED(否)
  2. Right problem to solve?           YES     NO      DISAGREE → TENSION-1
  3. Scope calibration correct?        YES     NO      DISAGREE → TENSION-1
  4. Alternatives sufficiently explored?NO     NO      CONFIRMED(否)
  5. Competitive/market risks covered? N/A     N/A     N/A（本地开发工具链，无市场面）
  6. 6-month trajectory sound?         NO      NO      CONFIRMED(否)
═══════════════════════════════════════════════════════════════
CONFIRMED = 两把声音一致。DISAGREE = 分歧 → 升 TENSION/决策登记区。
```

**跨声音收敛（两把独立声音 + 主 session 各自到达同一结论 ⇒ 高置信）**：

| 结论 | codex CEO | Claude CEO | 主 session 实测 |
|---|---|---|---|
| 版本 scope 比实际部署集宽 ⇒ 纯仪式硬停 | #3 + #5（33/97 ≈ 34%） | F1 + F4（45/129 ≈ 35%） | 10/19 ≈ 53%（近 200 提交口径） |
| 非 pin 仓 `$RULES_ROOT` = 全局 ⇒ 判据对象错 | #2（critical） | F3 | `resolve-workflow.sh --root .` → `~/.sdflow/workflow` |
| ADR 砍候选③ 的理由不成立 | #9 | F2 | ADR 原文比对确认 |

**三个口径的数字不同（34% / 35% / 53%）但方向一致**——差异来自统计窗口不同
（30 天 / 历史全量 / 近 200 提交），非互相矛盾。三者独立得出同一结论 ⇒ 该 finding 置信度**高**。

## 主 session 的独立读码复核（不是采信 voice 自述）

每一条被采信的 voice finding 都由主 session 亲自打开文件复核过。复核实据：

| 复核项 | 命令 / 文件 | 实测结果 |
|---|---|---|
| resolver 的 pin 判据 | `resolve-workflow.sh:37-53` | pin ⇔ `workflow.md` / `spec-checklists/` / `code-checklists/` 三者之一在；注释明写「**不查 openspec/workflow/ 目录——tools/ 使其恒存在**」 |
| 本仓实际 RULES_ROOT | `~/.sdflow/hack/resolve-workflow.sh --root .` | `/Users/cheneyzhao/.sdflow/workflow`（**全局 canonical，非仓内副本**） |
| canonical 是否实时 | `readlink ~/.sdflow/workflow` | `→ ~/.skills/sdflow-skills/sdflow-init/assets/workflow`（**软链 = 实时跟随运行 checkout 工作树**） |
| 工具执行路径是否都经 resolver | `grep -rn 'RULES_ROOT/tools' --include=SKILL.md` | 11 处**全部**经 resolver；无任何执行路径硬编码消费仓副本 |
| 消费仓副本的唯一非执行消费方 | `ship_gate.py:953-955` | `tools_spec = (b"openspec/workflow/tools/",)`，仅作 git pathspec 参与 code 域失鲜判定，**不执行** |
| 非 full 实际拷贝集 | `init.py:257-278` | `tools/`（去 tests）+ `lens-metric-contract.md` + `WORKFLOW-GUIDE.md`，**不含规则** |
| rmtree-then-copytree | `init.py:262-264` | `if os.path.isdir(tools_dst): shutil.rmtree(...)` 然后 `copytree(...)` —— 确认无事务语义 |
| manifest 的「先删最后写」先例 | `setup.sh:513-524` | 注释明写「🔴 **先删 manifest、最后才写**……MUST NOT 留一份『自洽但陈旧』的快照」+ `cap_broken` 记账 |
| adr/0003 的承重理由是否已死 | `adr/0003:3` 与 `:8`/`:18` | `:8` 「故 tools/ 是唯一不得不留的机械副本」，理由 = review 服务器根不落地即 404；`:3` 「该 viewer **已整体移除**」；`:18` 砍「连 tools 也不落地」的唯一理由是「省 serve.sh 重写」——**serve.sh 已不存在** |
| bundle churn（误报率） | `git log --format=%H -200` ∩ bundle | 200 提交中 19 动 bundle（9.5%）、9 动 `tools/`（4.5%）⇒ **约 10/19 ≈ 53% 的硬停不涉及任何被部署文件** |
| D6 的 bundle 作用域仍成立 | `git log -1 --format=%H -- sdflow-init/assets/workflow/` | `ee5b4f4…` vs `HEAD=fc0f1ae…` ⇒ 二者确实不同，D6 前提**成立**（memo 记的 `0d024ae` 已因两个新提交过期，属时点测量、非缺陷） |
| 删除面是否已扫全（面治） | `grep -rn "skew 探测" --include=SKILL.md` | 仅 `sdflow-code-review`、`sdflow-spec-review` 两处 ⇒ **删除面完整**，无第三份遗留 |
| `.bundle-version` 会否触 ship_gate 失鲜 | `ship_gate.py:95/955` | 监视集限于 `openspec/workflow/tools/`，`.bundle-version` 不在其下 ⇒ **不会**触发 |

## outside-voice 复用守卫（Step1.5）—— 判定复用不成立，已回落自跑

```
python3 $RULES_ROOT/tools/outside_voice_guard.py --review-path .../gstack-review.md --change-dir ...
→ stdout: section-not-found    rc=1
```

**遵其判定，未静默吞**：`reason_code != none` ⇒ **回落自跑设计 outside voice**（site=`design-voice`），
未复用本文件里的 codex 段。该自跑的 findings 不进本文件，进 `spec-review-report.md` 的合并池，
锚行落在那里（本层的 `declared-sites` 亦在那里）。

## 被复核后**驳回 / 降级**的输入（反静默压制）

- **接地镜（haiku 档）自相矛盾的结论**：它一方面正确报告「仓内无 `.bundle-version` 实现（设计未落地）」，
  另一方面又断言「Success Metrics 的归零条件**已满足**，SKILL:180/206 是**新版本对比逻辑**」。
  主 session 实跑 `grep -n "lens-metric-enums\|scope-audit:\|_MIRRORS_LEGAL"` 复核：
  180/206 两行**仍是旧的逐能力内容信号原文**（code-review 四条、spec-review 两条），
  归零条件**尚未满足**（本 change 未实现，这是预期状态）。
  ⇒ **该条结论被驳回**，不进合并池。（其余 17 项事实核验经抽查为真，予以采信。）
- **接地镜报的 `anchor_lint.py:148`** —— 主 session 复核：实际 `MANDATORY` 定义在 **`:203`**，
  `:148` 是 fence 解析代码。⇒ 该偏差**被采信**并升格为 F7（delta spec 引用错行号）。
