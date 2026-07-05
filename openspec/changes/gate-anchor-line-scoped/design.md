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

故扫描时维护 fence 状态：遇 `^\s*\`\`\`` 行翻转 in-fence 标志，**in-fence 的行不参与锚等值判定**。此惯例与 T34 `checkbox_done_ids`（`ship_gate.py:305-332` 已落地的整文 fence 状态扫描）**同款**，不引新解析器、与既有代码风格一致。

> **边界**：ADR-2 只排除 \`\`\` 围栏；行内反引号 span（`` `<!-- ... -->` `` 出现在句中）由 ADR-1 天然挡住（该行 `strip()` 后含反引号与其它字符 ≠ 锚字面）——两者叠加覆盖「内联提及」与「代码块示例」两类假阳性。

> **〔grill-amendment Q2〕ADR-2 定位 = 防御性，非复现 bug**：grill 实证——全部 15 份归档报告的假阳出现**全是内联描述**（ADR-1 territory），**从无**「锚独占一行落在 \`\`\` 内」的真实案例；且模板照抄的近似盘面要么带尾注（ADR-1 已杀）、要么 PASS/FAIL 并存判 UNKNOWN（安全）。故 ADR-2 **不针对任何已发生案例**，保留理由 = ①类闭合（一次堵死 fenced 变体）②与 T34 复选框 fence-aware 对称 ③成本 ≈1 行、复用既有惯例。**此为知情保留、非隐性 scope 扩张。**

### ADR-3：多命中/冲突语义逐字保留

`anchors_in` 仍返回**所有**命中的候选（行级），调用侧冲突检测（`verify=PASS` 与 `verify=FAIL` 各独占一行并存 → 返回二者 → UNKNOWN 点名冲突行）行为不变。收紧只作用于「子串→行等值」这一维，不改「返回命中集合」的契约。

### ADR-4〔grill-amendment Q1〕：锚检测第二路径 `archived_verify_state` 折入，抽共用文本级核心

grill 证伪 proposal 初稿「`anchors_in` 是唯一解析入口」——`ship_gate.py:143` 的 `archived_verify_state` 用**裸子串** `ANCHOR_VERIFY_PASS in out` / `ANCHOR_VERIFY_FAIL in out` 直接查 `git show <ref>:.../verify-report.md` 的文本 `out`，**不经 `anchors_in`**。它有**同一 B4 bug 类**：归档 verify-report 若在正文/代码块**描述性提及** `verify=PASS` 而无真独占锚（正是 B4「描述了却没真写」的形态）→ `has_pass=True` → 可致**假 SHIPPED**。穷举确认锚检测**仅此两处**（`anchors_in` 覆盖设计门 408 / `pick_exclusive` 219 / verify-fail peek 478；`archived_verify_state` 143 独立）；`ship_gate.py:237` 的 `"TG-02" in ...` 是触发标签检测、非 ship-gate 锚、故意子串（全角括号混用），**不在本 change 动**。

**决策**：抽文本级核心 `_line_scoped_hits(text, candidates)`（行等值 + fence-aware），`anchors_in`（读文件）与 `archived_verify_state`（git-show 文本）**共用**——修的是 bug 类不是单实例。

**失败方向接地（为何折入纯赚）**：设计门（`anchors_in` 查 design-approved）假阳=越门（危险）、假阴=拒起跑（安全）；SHIPPED（`archived_verify_state`）假阳=假 SHIPPED（危险，正是要堵）、假阴=判「未 ship」让用户复核（无害）。两处收紧都**只降危险假阳、只增无害假阴**，方向一致。

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
- **不处理未闭合 fence〔grill-amendment Q2 残差〕**：ADR-2 用简单 \`\`\` 奇偶翻转（同 T34），不检测未闭合围栏 / \`~~~\` 变体 / 带语言标签围栏。未闭合 \`\`\` 可能把其后的真锚吞进 in-fence 而漏检——但失败方向为**安全侧**（设计门→拒起跑、SHIPPED→判未 ship 让人复核，均非危险假阳），且模板产的报告短、围栏成对，未观测此形态；不为它加 T34 式 unbalanced→UNKNOWN 复杂度（超出窄修）。头注释「已知不覆盖」声明。
- **T37/T38（delta spec Scenario 措辞）不在本 change**：属 `checkpoint-tag-single-source` 批次的文档 prose 清理，与 `anchors_in` 代码正交，另行处理。
