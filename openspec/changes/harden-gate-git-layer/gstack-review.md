<!-- sdflow:step1-broad-review v1 mode="simulated" -->

# 广审（Step1）— harden-gate-git-layer · 第二轮（设计重写后）

> ⚠️ **模拟广审（降级模式）· 诚实标注**
>
> 本轮 `mode="simulated"`，**不是** autoplan 原生执行。第一轮（针对重写前的设计，内容见
> git 历史 `6424751`）是 `native`，有 preamble 实跑痕迹 + restore point 落盘。
> 本轮主 session **有意选择**按重写后的实际风险面自定三镜角度（CEO / eng / DX），
> 未跑 autoplan 的完整原生流程（含 restore point、premise 确认等一次性引导步）。
>
> **MUST NOT 伪装原生** ⇒ 锚行落 `simulated`，非 `native`。
>
> 双声：Codex（`gpt-5.6-sol`，跨模型，经 `outside-voice.sh` 真实调用，两站点 `rc=0`）
> + Claude 子代理三镜（`sonnet`，各自 fresh context，prompt 均原文携带三条通则）。

**评审对象**：`646fcc1` 版四件套（录锚 + 比内容 + 限定求值窗口；补偿机制整体取消）。

---

## CEO 镜（战略 / scope / 价值）

### C-F1 🔴 A2「窗口内无合法 churn」的实证前提被仓内真实历史证伪

**原始发现**：proposal 假设表 A2 与 ADR-3 均断言「全仓历史零个实现期提交
（`checkpoint(<change>:taskN-…)`）改过监视集」，据此论证「无需任何逃生口」。
CEO 镜举出 2 个反例并核对了 `design_approved` 时间线。

**主 session 复核（用更宽口径重扫全仓）**：反例**不止 2 个**。
以 `checkpoint(<change>:taskN-*)` 匹配、且触碰自身 change 的 `design.md`/`proposal.md`/`specs/`
（`tasks.md` 单列，因含复选框噪声）为口径，全仓命中 **6 个**；再逐个核对该 change 的
`design_approved: true` 首次写入时间：

| commit | change | 判定 |
|---|---|---|
| `94c20b79b` | fix-mechanical-layer-silent-failures | ✅ 反例（拍板后 **1.6 小时**，改 design.md +13/−3） |
| `55489213a` | add-sdflow-devenv | ✅ 反例（拍板后 14.9 小时，改 proposal + specs） |
| `cfb9a670d` | add-sdflow-devenv | ✅ 反例（拍板后 14.6 小时，改 design.md +26/−12 + proposal + 2 个 specs） |
| `a309fd899` | sdflow-init-hardening | ⬜ 不计（旧 inline 锚，查不到拍板时间） |
| `2ef7ba526` | drop-per-dir-review-stub | ⬜ 不计（同上） |
| `26aeb2dec` | checkpoint-tag-single-source | ⬜ 不计（同上） |

**保守结论：至少 3 个确证反例，跨 2 个 change。最近一个发生在本 change 起草前一天。**

**为什么这条重要**：它**不推翻求值窗口**（这些提交按新设计理应被判失鲜，正是判据要抓的东西），
但推翻「零成本」这个论证。当前措辞是「这种情况不存在，所以没有代价」，真相是
「这种情况存在且不算罕见，我们选择把它拦下、逼回正规流程」——**后者才诚实**，
且同样支持「不需要逃生口」的结论。

**置信度**：高（两轮独立核实：镜举证 + 主 session 全仓重扫 + 时间线逐个核对）
**严重度**：高（不是设计错，是假设表的 ✅ 是假绿）

### C-F2 / C-F3 / C-F4 / C-F5 —— 确认性发现（本角度无问题）

- **C-F2 scope 拆分**：四件事合并成一个 change **无问题**。P0 三项强耦合（比内容依赖录锚提供锚点；
  求值窗口的「无需逃生口」结论依赖比内容已消灭大部分假阳），拆开会产生「A 单独上线不构成完整能力」的中间态。
- **C-F3 求值窗口的取舍**：独立评估后判 **值**。让出的保护面有明文工作流兜底且落进既有残余面；
  换回的复杂度删减是实打实的；且被取消的那套逃生口机制其机械性本来就被高估
  （gate 只能比较 `reviewed_sha` 的值，拦不住谁去写它）。
- **C-F4 有无更简单方案被漏掉**：无。两条更简的路（整树 sha、负向 pathspec）均已实测证伪，
  现选方案已是化简后的下限；亦未见「简化过头」。
- **C-F5 30 项 tasks 与价值匹配**：合理。上一轮「测试存在但不构成证明」（rename 用例只调
  `blob_pair` 未走 `is_stale`）是本轮把变异证明立为贯穿要求的直接来源。

### C-F6 「阶段判定前移」有真实重构成本，design.md 只字未提（低）

`decide()` 的阶段判定靠三处提前 `emit()` 实现分支跳转，前移是真实控制流重排。
**与 eng 镜 E-F1 高度重合，以 E-F1 的更具体版本为准。**

---

## eng 镜（工程 / 架构 / 实现可行性）

### E-F1 🔴 求值窗口「前移」不是移动一行，是要拆进 3 个 early-return 分支

`RUN_SOP`（`:1237`）/ `RUN_PLAN`（`:1243`）/ `CONTINUE_IMPL`（`:1269`）不是一次算出后统一 emit 的，
而是分散在三处各自独立的 `emit()`，而 `emit()` 内部 `sys.exit()` 是**硬 early-return**。
现状 design 域失鲜检查是**单一调用点**且在三者之前（`:1214`）。

⇒ 「把检查前移进窗口」**不能**靠挪动 `:1214` 这一次调用实现：挪到三者之后永远到不了
（前面已 `sys.exit()`），挪到三者之前又等于没做窗口限定。唯一可行实现是把检查**分别塞进
三个分支各自的 emit 之前**，或把 steps 5.5–7 重构成「算出 tentative verdict 但不 emit」再统一检查。

🔴 **实现若走捷径**（只在 step 7 后加一次检查）⇒ `RUN_SOP` / `RUN_PLAN` 两条路径**完全逃出失鲜检查**，
方向 fail-open，且恰是本 change 要堵的洞的同类。

**置信度**：高（直接读控制流）｜**严重度**：高

### E-F2 🔴 `reviewed_sha` 与现有 `FIELD_ENUMS` 有限枚举架构不兼容

`parse_ship_gate_frontmatter` 的字段校验是**有限枚举**：

```python
FIELD_ENUMS = {"design_approved": (True, False), "verify": ("PASS", "FAIL"),
               "code_review": ("pass", "blocked")}
...
if val not in FIELD_ENUMS[field]:      # :884
    return {}, (field, "out-of-domain")
```

`reviewed_sha` 的合法值域是「任意 40 位十六进制」——**不可枚举**，套不进这条判据。

⇒ 按现状架构直接加字段的结果就是 `out-of-domain`，等价于「**新锚永远读不到**」——
**正是 ADR-1 自己点名最该避免的那个失败模式**。

**另需明确两层校验的职责切分**（设计未写）：`parse_ship_gate_frontmatter` 是纯文本函数
（live 读与 archived git-show 文本读共用），只能做**语法级**校验（40 位 hex 格式）；
**commit-object 存在性**是语义级，必须在有 `root` 的 `read_reviewed_sha` 里另做一次 git 调用
（如 `git cat-file -e <sha>^{commit}`，确认解析为 commit 而非任意 blob/tree）。

**主 session 复核**：已直接读码确认 `FIELD_ENUMS` 定义与 `:884` 判据原文，断言属实。

**置信度**：高｜**严重度**：中高

### E-F3 🔴 `specs/` 子树比较未指定双侧并集枚举，单侧枚举会漏检增/删

**三重独立命中**（eng 镜 + design-voice + hr-tg voice，三个 fresh context 各自发现）。

design.md ADR-2 与 tasks.md 2.1 只写「经 `ls-tree -r -z` 枚举后同样逐个比」，**未说枚举哪一侧**：

- 只枚举 HEAD 侧 ⇒ 锚存在、HEAD 已删除的 spec **根本不出现在枚举里**，删除动作被完全跳过（fail-open）
- 只枚举锚侧 ⇒ HEAD 新增的 spec 同样被跳过

`git ls-tree <ref> -- specs/` 对不存在路径不报错、只返回空输出（仓内已有先例：
`archived_dirs_in_tree` `:194-204`、`archived_verify_state` `:207-231` 都依赖「查不到→空，非异常」），
所以两侧都拿得到，但**代码必须显式取两侧路径集合的并集**。

**置信度**：高｜**严重度**：高（这正是本 change 想根治的那类缺陷，选错侧就原样复活）

### E-F4 `GIT_*` 清理若做成 allowlist 会撞本仓已知 Windows 坑（中）

tasks 3.3「清理 `GIT_*`（保留 `PATH`/`HOME` 等必要项）」可有两种实现：
**denylist**（复制 `os.environ` 剔除 `GIT_` 前缀，正确）vs **allowlist**（只显式构造几个 key，有风险）。
后者在 Windows 上会漏掉 `SYSTEMROOT`/`COMSPEC` 等 `CreateProcess` 依赖变量 ⇒ 子进程启动本身失败。
与本仓已踩过的坑同一类风险面（本地 macOS 测不出，只有真实 Windows runner 暴露）。

**建议**：tasks 3.3 明确写成 denylist；测试补「非 `GIT_*` 环境变量原样透传」这条方向。

**置信度**：中｜**严重度**：中

### E-F5 退役清单不完整：一整簇帧比较 helper 会变悬空引用 / 死代码（中高）

design.md 组件清单与 tasks 2.6 点名退役的只有 6 项。grep 全部调用点后发现，
另有一批函数**唯一存在的理由就是给帧遍历链条打下手**，清单里一个都没提：

| 符号 | 唯一调用方 | 退役清单点名 |
|---|---|---|
| `design_frame_exempt`（`:646`） | 调 `design_frame_exempt_reason` ⇒ 后者删则**悬空引用**；另有 8 处测试在调 | 间接 |
| `commit_parents`（`:313`） | 仅 `design_frame_exempt_reason`（`:624`） | **0 次** |
| `_parent_path_status`（`:342`） | 仅 `design_frame_exempt_reason`（`:631`） | **0 次** |
| `_plain_content_modification`（`:366`） | 仅 `blob_pair`（`:380`） | **0 次** |
| `_plain_modification_from_raw`（`:325`） | 仅 `_parent_path_status`（`:363`） | **0 次** |
| `blob_pair`（`:371`） | 仅 `design_frame_exempt_reason`（`:638`） | **0 次** |
| `design_watched_subs`（`:253`） | `design_frame_exempt_reason` + 帧遍历循环 | **0 次** |
| `STALE_CATEGORIES`（`:600`） | 五个取值全是帧比较 / blob 读取语境专属 | **0 次** |

⇒ 严格按 tasks 2.6 字面清单只删点名的六项，`design_frame_exempt` 会 `NameError`；
其余七项变成无生产调用方的死代码，`test_gate_freshness.py` 里六七十个测试函数
（`test_blob_pair_*` / `test_commit_parents_*` / `test_*frame_exempt*` / `test_stale_trigger_category_*`
/ `test_evil_merge_*` / `test_merge_frame_*` / `test_frame_paths_*`）同样失去存在意义。

design.md Risks 已要求「MUST 在 impl-report 逐条说明每个删除的用例对应哪个退役机制」——
但**退役机制清单本身不完整**，这条要求落不到实处。

**主 session 复核**：已逐符号 grep 核对——7 项在 tasks/design 中确为 **0 次点名**，属实。

**✅ 顺带的正面核实（值得写进实现指引，防误删）**：
`DESIGN_WATCHED_NAMES`（`:238`）与 `_tasks_content_exempt`（`:576-595`，签名
`(before_bytes, after_bytes) -> bool`，内部即「过 `_normalize_checkbox_lines` 后逐行等值」）
**可被新内容比较逻辑直接复用、无需改动**——前者就是固定清单常量本身，后者语义与新设计要求完全吻合。

**置信度**：高｜**严重度**：中高

---

## DX 镜（撞门者体验 / 可诊断性 / 迁移摩擦）

### D-F1 🔴 ADR-4 用来证成「诊断可退役」的论据本身不成立

ADR-4 的理由是「撞门者需要细节时 `git diff <reviewed_sha> HEAD` 一条命令即得」。
但三处 stale 的 `emit`（`:1220-1224` design、`:1302` cr、`:1324` v）的 `reason`/`extra`
**都不含锚值本身**；四件套通篇也没有任何一处要求把 `reviewed_sha` 写进 emit。

⇒ 撞门者拿到的只有「design 域失鲜」五个字，要跑那条命令得先手动打开报告 frontmatter
肉眼抄 `reviewed_sha:` ——**这不是「一条命令」，是「开文件抄值 + 一条命令」**。

**建议**：`emit()` 的 `extra` 补 `reviewed_sha`，reason 直接拼出可执行命令。
**这不违反 ADR-2/ADR-4 的红线**——`reviewed_sha` 现在是**录下来的常量**，读出来打印零推断成本，
与被退役的帧遍历诊断管道是完全不同性质的东西。

**置信度**：高（读码 + 全文档 grep 双重确认零覆盖）｜**严重度**：高（击穿一项退役决策的论据本身）

### D-F2 🔴 `GateIndeterminate` 的诊断文本未强制结构化，五类失败原因可能坍缩成一句话

tasks 1.2 / 3.1 / 3.4 全程只说「可读诊断」，未规定 `GateIndeterminate` 携带的信息结构；
spec 四个新增 Scenario 逐条只锁**行为**、不锁诊断文案。

五种原因的补救动作**完全不同**：git 不在 PATH（装 git）· 超时（查磁盘 / 网络文件系统）·
`reviewed_sha` 缺失（重跑评审）· 对象不存在（可能 force-push 改写了历史，需人工排查）· 读失败（仓可能损坏）。
若实现走最省事路径（`except GateIndeterminate: emit("UNKNOWN", ..., "git 调用失败")` 一句话打天下），
撞门者拿到裸退出码 + 无法行动的话——而 `UNKNOWN` 在链序里的处置正是「停并转述 reason」。

**仓内已有对照先例**：`_fail_closed_on_bad(err, label)`（`:956-959`）把 `(field, category)`
结构化后拼进 reason。本 change 没要求复用或对齐这个模式。

**置信度**：高｜**严重度**：高

### D-F4 求值窗口的行为收窄只落进源码头注释，`SKILL.md` 未同步（中）

`sdflow-ship/SKILL.md` 对「失鲜 / 陈旧 / `reviewed_sha`」零命中；tasks 5.1 只要求改
`ship_gate.py` 头注释，**没有任务项要求同步 `SKILL.md`**。
⇒ 从 `SKILL.md` 理解链序的人（或 agent）完全看不出「进入代码审后 gate 不再检查设计文档」这一行为边界。

**关于是否该在每次 emit 加运行时提示**：DX 镜**不建议**——按仓内既有惯例
（T33/T35 工作树 dirty 软提示只在 `SHIPPED`/resume 时信息性附加一行），逐次 emit 加噪声不是本仓风格。

**置信度**：高｜**严重度**：中（文档同步缺口，非安全问题）

### D-F3 fail-closed 迁移提示是一次性的，未覆盖未来撞门者（中）

**核实为真**：`openspec/changes/` 下只有 `archive/` 与本 change，后者尚无
`code-review-report.md`/`verify-report.md` ⇒ proposal「在途的只有本 change 自己」在当前时点成立。

但 tasks 5.3 的提醒只写进**本 change 的 hand-off.md**，是一次性通知。
未来若有人从更早 fork 恢复、或跨仓迁移未经 `/sdflow-upgrade` 同步，撞上无 `reviewed_sha` 的存量报告，
看到的只是 `UNKNOWN(6)` + D-F2 里那句可能语焉不详的文本。

**建议**：并入 D-F2 的修法——`reviewed_sha` 缺失这一支单独给针对性措辞
（「该报告产出于本次硬化之前 → 请重跑 sdflow-spec-review 补锚」），一次写对，不依赖每次有人记得写 hand-off。

**置信度**：中｜**严重度**：中

### D-F5 `timeout=30` 的聚合最坏情况约 4–5 分钟，design 只论证「有界」未给数量级（低）

按 design 自陈的「8–10 次调用」× `timeout=30`，最坏（文件系统挂起）单次 `decide()`
可能等 **4–5 分钟**才落进 `UNKNOWN(6)`。ADR-5 的「聚合上界」论证的是**有界**（对，是常数、不随提交数增长），
但**有界 ≠ 短**。

**不建议改 timeout 值本身**（ADR-5 判据「文件系统卡死线，非性能预算」是对的，
且与仓内 `buglist.py` 先例一致，不该按最慢场景反推调小）。建议把这个数量级写进 ADR-5。

**置信度**：高（纯算术）｜**严重度**：低

---

## Codex outside voice（跨模型 · site=design-voice · `rc=0`）

<!-- sdflow:outside-voice v1 site="design-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="3" truncated="false" -->

### V-F1 🔴🔴 归档 / merge 后缺终态 code freshness 消费点（critical）

`:1311` 在 archive/merge **之前**检查 `verify-report`；随后返回 `RUN_VERIFY` 交 `sdflow-done` 收尾，
而 `sdflow-done` 此后执行 `git add -u`（`sdflow-done/SKILL.md:321`）、commit、merge。
归档后 active 目录消失 ⇒ **D3 短路仅凭归档 `verify=PASS` 判 `SHIPPED`**（`:1172` 起），**不再调用 `is_stale`**。

⇒ design.md 所称「merge 后源码改动会 stale」**并未实现**；A5 所列「三个消费方」也漏了**终态消费方**。

**主 session 复核（已确证）**：
- `grep "is_stale("` ⇒ 全脚本仅 3 个调用点（`:1214`/`:1291`/`:1311`），A5 的**数字本身没错**
- **但 D3 短路段（`cdir` 不存在 → SHIPPED 路径）内 `is_stale` 出现 0 次** —— 该路径完全不做失鲜检查
- ⇒ **verify 检查点之后、archive commit 之间塞进的源码改动，不被任何失鲜检查覆盖，然后直接 merge**。
  不需要恶意：`git add -u` 是 `sdflow-done` 第四步的正常动作。

**同片面已有登记**：T179「archive 步骤可能打断测试，其后无人重跑全套件 —— gate 判 SHIPPED 时 main 实际是红的」
⇒ 「测试没重跑」与「代码改动没重查」是**同一个盲区的两半**，本条不是孤例。

**建议（voice 原文）**：D3 判 `SHIPPED` 前，从 base 树中的归档 `verify-report.md` 读 `reviewed_sha`，
比该锚的非 `openspec/` 顶层树与待判 SHIPPED 的 base 树；不等则拒绝 `SHIPPED`。
补「verify 后修改 tracked 源码 → 收尾 commit → merge」端到端变异用例。

**置信度**：高（三重核实）｜**严重度**：致

### V-F2 🔴 求值窗口由盘面反推，区分不了「实现期最后一刻改设计」与「代码审期合法对账」

阶段由完成集决定：计划任务齐全后**立即**进入 `RUN_CODE_REVIEW`（`:1279` `if not cr.is_file()`）。
新设计要求进入代码审后跳过 design freshness ⇒ **同一提交「实质修改 `design.md` + 完成最后一个 task」**，
或**任务已齐、代码审尚未真正启动时修改设计**，都会被归类为代码审期而跳过检查。

A9 只证明了**无循环依赖**，没有证明阶段来源具备**时间顺序**或**来源可信性**。

**主 session 独立命中同一条**（在 voice 回来前已自行推出，故本条不计 voice 独立）：
窗口右边界恰好是「最后一个 task 打勾的那一刻」（`CONTINUE_IMPL` 条件是 `plan_ids - done` 非空，`:1268`），
而不是「实现结果被检查过的那一刻」——中间存在一个未被求值的间隙。

**置信度**：高｜**严重度**：高

### V-F3 🔴 `specs/` 枚举未规定比较两侧完整路径集合（与 E-F3 / H-F3 三重命中）

见 E-F3。voice 额外要求：比较完整 `path → (mode, type, oid)` 映射，
**单侧缺失应判 stale，不应混作 git 读取失败**（与「读失败 ≠ 内容为空」是两件事，别合流）。

**置信度**：高｜**严重度**：高

---

## Codex outside voice（跨模型 · site=hr-tg · TG-17 安全面 · `rc=0`）

<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="4" truncated="false" -->

### H-F1 🔴🔴 未提交源码可在 verify 后绕过 freshness 并被最终提交 / 合并（critical）

gate 明确只检查 **committed** 状态，dirty worktree 仅 MAY 软提示（`ship_gate.py:90` 起、
`sdflow-ship/SKILL.md:108`）；但 `sdflow-done` 随后执行**无范围限制的 `git add -u`**
（`sdflow-done/SKILL.md:321`），把所有已追踪源码纳入最终提交。

⇒ verify PASS 后修改已追踪源码、**保持 HEAD 不变**，gate 仍判 fresh，最终提交却携带未审改动。

**与 V-F1 的关系**：同一盲区的**两条不同路径**——V-F1 是「检查点之后新 commit 的改动」，
H-F1 是「根本没进 commit、靠 `git add -u` 一次性收编的工作树改动」。**两条都真实、都通向 merge。**

**建议（voice 原文）**：verify 前后及 merge 前对非 `openspec/` tracked dirty 设硬门；
收尾提交不得用无范围 `git add -u`；或提交后、archive/merge 前再针对最终 commit 跑一次 code-review 与 verify freshness。

**置信度**：高｜**严重度**：致

### H-F2 🔴 `code-review` 的 `reviewed_sha` 写入时序与自动修复 checkpoint 不原子 ⇒ 锚立刻自失鲜

tasks 1.1 要求 code-review「**出报告时**」记录当时 HEAD。但 `sdflow-code-review` 在同一轮**自动修源码**
（第五步「修复代码，改动处标 `[impl-review-fix]`」），**最后才把修复与报告一起 checkpoint**
（`sdflow-code-review/SKILL.md:256-257`：「产出报告 + 自动修复后 → checkpoint-commit.sh impl-review」）。

⇒ 写报告那一刻的 HEAD **不含**尚未提交的修复；checkpoint 一落，HEAD 前进、源码顶层条目改变
⇒ **code 域相对自己刚写下的锚立刻失鲜**。**每一轮有自动修复的代码审都会自锁。**

**主 session 复核**：已读 `sdflow-code-review/SKILL.md:256-257` 确认修复与报告同属一个 checkpoint commit，断言属实。

**建议（voice 原文）**：先提交修复形成候选 commit → 审该 commit → 用**独立的 report-only commit** 写入其 SHA；
补「code-review 自动修复非空」端到端用例。
**主 session 补充**：该修法在本设计下天然可行——code 域比较**排除 `openspec` 条目**，
故 report-only commit（只动 `openspec/`）不改变非 openspec 顶层条目 ⇒ 不触发失鲜。

**置信度**：高｜**严重度**：高（P0 级实现阻断，不修则代码审每轮自锁）

### H-F3 🔴 `specs/` 文件集合比较未规定取锚与 HEAD 并集（第三次独立命中）

见 E-F3 / V-F3。voice 要求比较**存在性、对象类型、mode 与内容**四者。

### H-F4 🔴 限定窗口使正常工作流能取消设计批准的真实性，登记为残余面仍与被保护资产直接冲突

被保护资产含「设计审已拍板」的有效性（design.md:109），但代码审后完全停止 design freshness，
并明确允许把 `design.md` 改成匹配现实（design.md:69）。

🔴 **这不是只有恶意写权限者才触发的篡改，而是正常 agent 被工作流授权执行**，
**随后 verify 会依据改写后的目标判 PASS**。

**主 session 评注**：这条比 V-F2 与我自己的版本**深一层**——它串出了完整后果链：
`design.md` 被改成匹配现实 → verify 拿改写后的 design 去核对 → **当然 PASS**。
即「唯一终门」实际在核对一个**可被移动的靶子**。

**建议（voice 原文）**：保留不可变的 approved-design tree/digest，最终归档前比较；
除纯复选框归一化外任何实质差异都要求重新拍板，或作为新 change / addendum 处理。

**置信度**：高｜**严重度**：高

---

## 主 session 独立发现（无镜命中）

### M-1 `_normalize_checkbox_lines` 的承重程度在新设计下升格，而它自己带着基准 5 警号

本 change 的旗帜是**基准 5**（补丁螺旋不收敛 ⇒ 砍掉整个推断面）。但它把
`_normalize_checkbox_lines` 作为核心依赖「保留复用」，而该函数**自己就登记着基准 5 警号**——
T189 原文：「基准 5 警号：`_normalize_checkbox_lines` 已**第 4 轮**往同一函数补语法分支，口径应反转为白名单」。

关键在于**承重程度变了**：旧设计里 checkbox 豁免只是众多判据之一；
**新设计里（比内容 + 唯一豁免）它是 design 域唯一的放行闸门**。

design.md 已登记 T189 耦合（未隐瞒），但措辞是「其口径缺陷会直接影响豁免面」——
**低估了它从「判据之一」升格为「唯一放行闸门」这件事**。

**建议**：不必 fold T189（独立面，且与简化方向冲突），但残余面登记须升级措辞。

**置信度**：高｜**严重度**：中

### M-2（简化机会）`ls-tree -r` 本就返回 oid ⇒ design 域可比 `path → oid` 映射，省掉大部分 `git show`

E-F3 / V-F3 / H-F3 要求「两侧枚举取并集」。顺着这条走，有一个**同时修 bug 且减复杂度**的做法：

`git ls-tree -r` 的输出本身就含每个文件的 **oid**。⇒ design 域可以两侧各跑一次
`ls-tree -r <ref> -- proposal.md design.md specs/`，直接比 `path → oid` 映射：

- 天然覆盖新增 / 删除 / rename（并集问题自动消失——映射不等即 stale）
- git 调用从「8–10 次」降到 **3 次**（两次 ls-tree + `tasks.md` 一次内容取用）
- 只有 `tasks.md` 因需过 `_normalize_checkbox_lines` 才必须取内容
- 顺带把 D-F5 的最坏等待从 4–5 分钟压到约 1.5 分钟

**符合用户 steer**（「方案不能越改越复杂，应该适当简化」）：这不是加机制，是**用更少的调用做更全的覆盖**。

**置信度**：高（`ls-tree -r` 输出格式是确定的 git 行为）｜**严重度**：—（改进建议，非缺陷）

---

<!-- sdflow:hr-tg v1 hit="TG-17" declared="TG-14,TG-17,TG-18,TG-19,TG-22,TG-23" evidence="被保护资产=设计审拍板/代码审放行/verify 通过三个结论的有效性，是 merge 前仅有的质量门；威胁模型表 + 残余面登记构成 TG-17 触发点" -->
