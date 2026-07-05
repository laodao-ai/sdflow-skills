# gate-anchor-line-scoped — Design

## 背景

`anchors_in(path, candidates)` 现实现（`ship_gate.py:198-203`）：

```python
def anchors_in(path, candidates):
    """字面查找（零正则）。文件不存在返回 []。"""
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    return [a for a in candidates if a in text]   # ← B4：纯子串，误配描述性提及
```

调用点消费其返回：设计门 pre-flight 判 `design-approved` 是否在 `spec-review-report.md`；verify/code-review 判结论锚；冲突检测（同报告并存 `verify=PASS` 与 `verify=FAIL` → UNKNOWN）也靠它返回多命中。**收紧假阳性不得破坏冲突多命中语义**。

## 决策

### ADR-1：锚检测 = 逐行整行等值（`line.strip() == anchor`），非子串

候选锚 MUST 作为**独占一行**出现才算命中：扫描文件各行，`line.strip() == candidate` 才计入。三个生成模板都把锚写在自己一行（「结论区末行为机器锚行」/「紧跟机器锚行」），故真锚在此判据下仍命中；描述句里内联的锚（前后有其它字符，`strip` 后 ≠ 锚字面）不再命中。

**保「字面查找（非正则）」**：行级仍是字面等值比较（`==`），不引正则——需求原文「gate 以字面查找（非正则）解析」的精神是「不靠脆弱正则匹配自然语言」，行级等值比子串**更**字面、更严格，契合而非违背。

**为何不选行首匹配 `line.startswith(anchor)`**：`startswith` 会让「锚 + 尾部垃圾」同行仍命中（如 `<!-- ... -->evil`），比等值弱；且描述句若恰以锚开头即误配。等值最严、最贴合「锚独占一行」的真实产出形态。

**为何不选正则 `^anchor$`**：语义等同 `strip()==`，但引入需求明令避开的正则，且锚字面含 `<!-- -->` 等正则元字符需 `re.escape`，徒增脆性。等值更简。

### ADR-2：fence-aware——忽略 fenced code block（\`\`\`）内的行

仅行等值仍不够：报告/SKILL 模板**合法地**在 \`\`\` 代码块里展示锚字面作文档（本仓 `spec.md`、各 SKILL.md「报告格式」段皆如此），代码块内的锚**独占一行**但它是文档不是结论。若某报告复制模板文档段（含代码块内的锚示例），仅 ADR-1 会误命中。

故扫描时维护 fence 状态：遇 `^\s*\`\`\`` 行翻转 in-fence 标志，**in-fence 的行不参与锚等值判定**。此惯例与 T34 `_parse_plan`（`ship_gate.py:302-329`，fence 翻转在 :313-317）已落地的整文 fence 状态扫描**同款**，不引新解析器、与既有代码风格一致〔spec-review-amendment：行号按接地镜校正〕。

> **边界**：ADR-2 只排除 \`\`\` 围栏；行内反引号 span（`` `<!-- ... -->` `` 出现在句中）由 ADR-1 天然挡住（该行 `strip()` 后含反引号与其它字符 ≠ 锚字面）——两者叠加覆盖「内联提及」与「代码块示例」两类假阳性。

> **〔grill-amendment Q2〕ADR-2 定位 = 防御性，非复现 bug**：grill 实证——全部 15 份归档报告的假阳出现**全是内联描述**（ADR-1 territory），**从无**「锚独占一行落在 \`\`\` 内」的真实案例；且模板照抄的近似盘面要么带尾注（ADR-1 已杀）、要么 PASS/FAIL 并存判 UNKNOWN（安全）。故 ADR-2 **不针对任何已发生案例**，保留理由 = ①类闭合（一次堵死 fenced 变体）②与 T34 复选框 fence-aware 对称 ③成本 ≈1 行、复用既有惯例。**此为知情保留、非隐性 scope 扩张。**

### ADR-3：多命中/冲突语义逐字保留

`anchors_in` 仍返回**所有**命中的候选（行级），调用侧冲突检测（`verify=PASS` 与 `verify=FAIL` 各独占一行并存 → 返回二者 → UNKNOWN 点名冲突行）行为不变。收紧只作用于「子串→行等值」这一维，不改「返回命中集合」的契约。

### ADR-4〔grill-amendment Q1〕：锚检测第二路径 `archived_verify_state` 折入，抽共用文本级核心

grill 证伪 proposal 初稿「`anchors_in` 是唯一解析入口」——`ship_gate.py:143` 的 `archived_verify_state` 用**裸子串** `ANCHOR_VERIFY_PASS in out` / `ANCHOR_VERIFY_FAIL in out` 直接查 `git show <ref>:.../verify-report.md` 的文本 `out`，**不经 `anchors_in`**。它有**同一 B4 bug 类**：归档 verify-report 若在正文/代码块**描述性提及** `verify=PASS` 而无真独占锚（正是 B4「描述了却没真写」的形态）→ `has_pass=True` → 可致**假 SHIPPED**。穷举确认锚检测**仅此两处**（`anchors_in` 覆盖设计门 408 / `pick_exclusive` 219 / verify-fail peek 478；`archived_verify_state` 143 独立）；`ship_gate.py:237` 的 `"TG-02" in ...` 是触发标签检测、非 ship-gate 锚、故意子串（全角括号混用），**不在本 change 动**。

**决策**：抽文本级核心 `_line_scoped_hits(text, candidates)`（行等值 + fence-aware），`anchors_in`（读文件）与 `archived_verify_state`（git-show 文本）**共用**——修的是 bug 类不是单实例。

**失败方向接地（为何折入纯赚）**：设计门（`anchors_in` 查 design-approved）假阳=越门（危险）、假阴=拒起跑（安全）；SHIPPED（`archived_verify_state`）假阳=假 SHIPPED（危险，正是要堵）、假阴=判「未 ship」让用户复核（无害）。两处收紧都**只降危险假阳、只增无害假阴**，方向一致。

### ADR-5〔spec-review-amendment OV-2 · 设计门 Q1=A〕：未闭合 fence → 互斥锚对保守判定

spec-review 的 codex outside-voice（OV-2）证伪了原 grill Q2 的「未闭合 fence 一律安全侧」前提。反例：文本 `<正锚>` 在 fence 外、随后**未闭合** \`\`\`、`<负锚>` 在其内被吞 → `_line_scoped_hits` 只返正锚 → `pick_exclusive`（:220 `positive in found` 真 → 返 `"pos"`）/ `archived_verify_state`（`has_pass=T/has_fail=F`）从**应有 conflict/UNKNOWN 翻成 pass** → 危险假阳（旧裸子串两锚都命中→conflict，安全）。**即 ADR-2 对此盘面是引入假阳的回归。**

**决策（设计门 Q1=A 拍板）**：`_line_scoped_hits` 扫描末尾若 `in_fence` 仍为真（未闭合）→ 返回信号（`(hits, unbalanced=True)` 或旁挂谓词，复用现成 `plan_unbalanced_fence` :353-356 的检测惯例）。**互斥锚对调用方**（`pick_exclusive`、`archived_verify_state`）遇 `unbalanced=True` → 判 **UNKNOWN/none**（保守失败到安全侧，宁可多一次人工核验也不放假阳）。**单锚调用方**（设计门 `anchors_in` 查 design-approved，无互斥对）不受影响——未闭合吞掉唯一锚 → 空命中 → REFUSE_START，仍是安全侧假阴。

**为何选 A（而非接受）**：本 change 本旨即堵锚检测假阳；旧行为对此盘面安全、ADR-2 使其危险=回归，留新洞自相矛盾；`plan_unbalanced_fence` 现成、成本 ≈5 行 + 2 测试。ADR-2 定位维持「防御性」，但 ADR-5 把其唯一真危险副作用（互斥锚对回归）焊死。

### ADR-6〔spec-review-amendment · dogfood 发现 · 设计门 Q3=A1〕：`tg02_hit` 触发检测从裸子串→声明式匹配

跑 gate 现场暴露**第三个同类子串 bug**：`tg02_hit`（`ship_gate.py:234`）`return "TG-02" in proposal.md 文本` 会把 proposal 里对 `TG-02` 的**描述性提及/代码引用/否定句**误判为命中 → 假 RUN_SOP（误当嵌入式 change 要跑 embedded-test-sop）。本 change 的 proposal 讨论该函数（`"TG-02" in`）即触发，卡住自己的 ship——与 B4 同一「子串误配描述性提及」bug 类。

**与锚检测的关键区别**：TG 标签**合法内联**于 proposal 散文/头注（`〔TG-02：嵌入式固件变更〕`），**不能行锚定**（不像机判锚独占一行）。

**决策（Q3=A1→A3，dogfood 二轮修正）**：初判 `〔TG-02` 整体子串匹配——但实现期跑 gate 再暴露：本 change proposal 正文文档化 tg02 修复、含示例声明串 `〔TG-02：`（proposal.md line 42），整体子串（含加冒号 `〔TG-02：`）**仍假阳**。故收敛为 **A3 头部区域限定**：`tg02_hit` 只在 proposal **头部声明区**（文件开头→首个 `## ` 标题前）找 `〔TG-02`——真 TG 声明都在头部预置区（title 下 `〔TG-NN：…〕` 串），正文（`## ` 段内）的文档性提及天然排除。接地：全部 8 份归档 proposal 的 TG 声明皆头部 `〔TG-NN：` 形，ff-generation 强制此头注格式。
- **备选** A1（整体 `〔TG-02` 子串）：一行改动但被 dogfood 证伪（正文示例声明串假阳）；A2（剥反引号 span 后匹配）：正文无反引号的 `〔TG-02：` 散文仍假阳。A3 头部区域最 robust——结构性排除全部正文提及。
- **残差（如实记）**：未用 `〔〕` 括号声明 TG-02 的（非常规）embedded proposal 会漏检 → 不跑 SOP = 安全侧假阴（且约定强制括号，实际不发生）；记入 Non-Goals。

## 实现草图（ADR-1/2/4 一并）

```python
def _line_scoped_hits(text, candidates):
    """文本级行锚定核心（零正则）：候选须独占一行（strip 后等值），忽略 fenced code block。
    anchors_in（读文件）与 archived_verify_state（git-show 文本）共用此核心〔ADR-4〕。"""
    cand = set(candidates)
    hit = set()
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.strip() in cand:
            hit.add(line.strip())
    return [a for a in candidates if a in hit]   # 保持入参顺序，去重


def anchors_in(path, candidates):
    """行级字面查找（零正则）：文件不存在返回 []。"""
    if not path.is_file():
        return []
    return _line_scoped_hits(path.read_text(encoding="utf-8", errors="replace"), candidates)


# archived_verify_state 内（ship_gate.py:143）——git-show 文本 out 改走同一核心：
#   hits = _line_scoped_hits(out, [ANCHOR_VERIFY_PASS, ANCHOR_VERIFY_FAIL])
#   has_pass, has_fail = ANCHOR_VERIFY_PASS in hits, ANCHOR_VERIFY_FAIL in hits
#   （返回 'conflict'/'pass'/'none' 三态逐字不变，只把「子串」换成「行锚定」）
```

（`line.lstrip().startswith("```")` 复用 T34 fence 追踪写法；返回按 `candidates` 原序去重，与旧 `anchors_in` 及旧 `archived_verify_state` 的对外语义一致。）

## Non-Goals / 已知不覆盖

- **不校验锚出现次数**：同一锚独占多行只算命中一次（`set`）；模板产一行，多行属异常但不改门禁方向（仍命中=已过），不在本 change 处理。
- **不做 HTML 注释语义解析**：不判断锚是否在更大的 `<!-- ... -->` 多行注释块内被「注释掉」——模板锚本身就是单行 HTML 注释，独占一行等值已足；多行注释嵌套锚属人为构造，归「显式越权同权级」（git 留痕可审计），头注释「已知不覆盖」声明。
- **未闭合 fence：已由 ADR-5 处理（设计门 Q1=A）**——不再列为不覆盖项。互斥锚对遇未闭合 fence → 保守判 UNKNOWN/none（见 ADR-5，复用 plan_unbalanced_fence）。仍不覆盖：`~~~` 围栏 / 带语言标签围栏的**误判**（对抗镜1 核实非本仓现实语料，且方向=安全侧假阴）——如需再收由后续 change 处理。
- **T37/T38（delta spec Scenario 措辞）不在本 change**：属 `checkpoint-tag-single-source` 批次的文档 prose 清理，与 `anchors_in` 代码正交，另行处理。
