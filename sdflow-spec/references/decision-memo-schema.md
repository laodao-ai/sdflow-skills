# 决策纪要 `decision-memo.md` — 字段 schema 与模板

> 被 `sdflow-spec/SKILL.md` 相位 B/C 引用。**本文是纪要格式的单一源**——小节标题
> 被 `hack/tests/test_decision_memo_gate.py` 的机械门逐字消费，**改标题 = 改共享字符串**，
> MUST 先 `grep -rn` 谁在用（不加 `--include` 限定），再同步改门。

## 1. 落点与身份

- **路径**：`openspec/changes/<change>/decision-memo.md`（git 跟踪）。
  **MUST NOT** 写进 session 级临时目录（scratchpad）——session 崩即丢承重件。
- **落点何时存在**：相位 B **起手**三步（工作树检查 → FF-0 → `openspec new change`）跑完即存在，
  故相位 B 进行中就能增量落盘。

## 2. 文件形状

```markdown
---
schema_version: 1
change: <change 名，与目录名逐字相同>
branch: <生成时所在分支，通常 feat/<change>>
generated_at: <ISO-8601，如 2026-07-26T14:03:11+08:00>
decision_hash: <「拍板决策」小节全文的 sha256 前 12 位>
---

# 决策纪要 · <change>

## 目标态

<一句话。写不出这句 = 相位 A 禁止收束。>

## 拍板决策

- **D1 <决策>** — 依据：<why>；**砍掉的候选**：<候选 + 砍的理由>
- **D2 …**

## 承重约束

- **C1 <约束>** — 验证方式：<怎么验的>；**证据锚**：<file:line / 命令输出 / 「人 YYYY-MM-DD 明确确认」>
- **C2 …**

## 接受的边角

- <风险> — 概率/影响/完美成本；**为何接受**：<通则④ 五问的结论>

## 三镜代价

<仅命中 TG-23 的方案选择才写；否则写「本次无 TG-23 命中」。
 系统镜 / 用户镜 / 开发循环镜 + 一句主次判定。>
```

### `decision_hash` 的唯一算法

**定稿（B 收敛）与核验（C 起手）跑的是同一条命令 ⇒ 定义就是这条命令本身**，
不存在「两端口径不同」的失配面。MUST NOT 手算、MUST NOT 换等价写法：

```bash
python3 -c '
import hashlib,sys
lines=open(sys.argv[1],encoding="utf-8").read().splitlines()
i=lines.index("## 拍板决策")
b=[]
for l in lines[i+1:]:
    if l.startswith("## ") or l.startswith("# "): break
    b.append(l)
print(hashlib.sha256("\n".join(b).strip().encode()).hexdigest()[:12])
' openspec/changes/<change>/decision-memo.md
```

范围 = `## 拍板决策` 下一行起、到下一个以 `## ` / `# ` 开头的行（或 EOF）为止，两端 strip。
🔴 **口径边界**：它是**逐行字面量**判断，不认围栏 ⇒ 「拍板决策」节内若出现以 `## ` 开头的行
（**包括代码块内的**），hash 只覆盖到那一行为止。两端同命令 ⇒ 不会因此失配，只是覆盖面变窄；
故 SHOULD 不在该节内贴含 `## ` 的代码块。

## 3. 必填与判红

| 项 | 判据 | 谁判 |
|---|---|---|
| 文件存在 | `openspec/changes/<change>/decision-memo.md` 存在 | **机械门**（pytest） |
| `## 拍板决策` 非空 | 该 H2 与下一个**同级/更高级** ATX 标题（或 EOF）之间存在非空白、非注释正文；围栏与 HTML 注释块内的标题不算标题 | **机械门**（pytest） |
| `## 承重约束` 非空 | 同上 | **机械门**（pytest） |
| 身份字段匹配当前盘面 | `change` == 当前 change 名 ∧ `branch` == 当前分支 | **指令层**（相位 C 起手，主 session 判） |
| **`decision_hash` 匹配** | 按上方唯一算法**重算**「拍板决策」全文 hash，与 frontmatter 比对 —— 不符 = 定稿后被手改 | **指令层**（重算本身是机械的，处置是判断） |
| **`generated_at` 合理** | 存在、可解析、不落在未来；**其值呈现给人**做陈旧判断（旧运行留下的 memo 可能 change/branch 都对得上，只有时间戳看得出） | **指令层** |
| 每条承重约束真有证据锚 | 锚是不是真的、指的对不对 | **指令层**（无确定性信号，语义残余） |

> `decision_hash` / `generated_at` 缺失 ⇒ 视为**未定稿**（相位 B 的收敛两步没走完）⇒ 退回相位 B，
> **不是**身份不匹配。二者处置不同：前者继续做 B，后者要人拍板「复用还是重做」。

🔴 **诚实边界**：机械门只证明「纪要存在且这两节非空」，**MUST NOT** 被表述为「证明发生过对抗拷问」。
拷问是管线的**内建默认路径**，跳过须主动偏离指令——**结构性改善，不是机械保证**。

## 4. 增量落盘时机

- **每条承重约束站稳（拿到证据锚）即追加写 `## 承重约束`**，不等全部站稳。
- 拍板一条决策即追加写 `## 拍板决策`。
- 相位 B **收敛点**才补 frontmatter 的 `generated_at` / `decision_hash`（定稿动作）。
- 已知损失：**两次保存点之间**的部分。SHALL 在报告中如实标注，MUST NOT 声称「零损失」。

## 5. 与 design.md 的关系

**MUST NOT 并入 design.md。** design.md 的 `## Decisions` 只写一行指针：

```markdown
本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)。
```

理由：① `openspec instructions design --json` 的原生 Sections（Context / Goals-Non-Goals /
Decisions / Risks-Trade-offs / Migration Plan / Open Questions）**无「承重约束」槽位**，而它最承重；
② `/clear` 无损这条不变式单靠 memo 已满足；③ 双写失配时无优先级规则。
