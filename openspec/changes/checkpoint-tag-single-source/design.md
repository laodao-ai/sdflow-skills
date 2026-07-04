## Context

checkpoint 任务标签格式 `<change>:task<N>-<slug>` 是 `/sdflow-ship` gate 完成判据的主锚。这条约定当前活在**三个耦合站点**：

```
  ①  ship_gate.py  TAG_RE = checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-   ← 真·解析权威（gate 认什么）
  ②  workflow.md:74   「checkpoint-commit.sh <change>:task<N>-<slug>」          ← bundle 权威文档
  ③  sdflow-ship/SKILL.md  同一句 <change>:task<N>-<slug>                      ← 派发指令（告诉 implementer 产什么）
```

漂移分两类，危险度不同：

- **doc↔doc（②↔③）**：ship-gate-hardening-2 实证发生过（改格式漏改 ③，spec-review G1 抓到）。烦，但 spec-review 兜得住。
- **doc↔parser（②③↔①）**：文档说一种、`TAG_RE` 解析另一种 → implementer 照文档产标签、gate 却不认 → 标签**静默不计入完成集** → 假✅或假阴。**当前无任何守卫**，这才是要焊的。

## Goals / Non-Goals

**Goals:**
- 用一条**机械绑定测试**把 ②③ 的文档格式串与 ① 的 `TAG_RE` 双向钉死——任一站漂移即测试红。
- 把格式**字面**收敛到单一文档源（`workflow.md`），③ 引用而非复述。
- 零运行时行为变更（`TAG_RE` 解析逻辑逐字不变）。

**Non-Goals:**
- 不改标签格式语义（命名空间/裸兼容/窗口全不动）。
- 不追求 markdown 层的文本 DRY（跨运行时安装树无构建期 include，硬做收益边际）。
- 不碰 T33/T35（新鲜度越 committed 边界）——那是需 grill 的独立设计问题。

## Decisions

### D1：单一真相源 = 测试绑定，不是 markdown include

**为何不让 ③ include ②**：`workflow.md` 运行时经 `resolve-workflow.sh` 解析到 `~/.sdflow/workflow/`，`SKILL.md` 安装在 `~/.claude/skills/sdflow-ship/`，两者不同安装树、Markdown 无构建期 include 机制。强行让 ③ 运行时去读 ② 取字面，会给 RUN_PLAN 派发添一个间接读依赖（派发时 workflow.md 未必在上下文），得不偿失。

**改用测试作 enforcement 单源**：文档仍是两份人读文本（服务不同读者），但**正确性**由一条 pytest 契约测试保证——它是「三站一致」这个不变量的唯一机械裁判。这与本 spec 既有的防漂移先例同构（INDEX.md 靠 `reindex` 单生成杜绝第三漂移源、bundle 靠权威源单改）。

### D2：`TAG_RE` 是 parser 权威，`workflow.md` 是 doc 权威——测试同时锚定两端

契约测试断言两件事：
1. **doc→parser 正向**：从 `workflow.md`（及 `SKILL.md` 若仍含字面）里出现的格式，构造一个真实 checkpoint subject（如 `checkpoint(demo:task1-slug): msg`），断言 `TAG_RE.match` 成功且捕获组 = `("demo","1")`。
2. **向后兼容仍在文档**：裸格式 `checkpoint(task1-slug)` 也被 `TAG_RE` match（`<change>` 组为 None），且文档仍声明裸格式向后兼容——防有人「顺手」把裸兼容从文档删掉却忘了 `TAG_RE` 仍认。

测试**直接读文档文件 + import `TAG_RE`**（非硬编码期望串），这样文档改字面、正则改捕获组，任一单改都会让断言失衡→红。

### D3：③ SKILL.md 瘦身范围——只删「独立格式文案」，保留派发语义

SKILL.md RUN_PLAN 段现含完整格式串 + 命名空间语义解释。瘦身**只**把「格式字面」替换为对 workflow.md 的引用，**保留**派发动作、「由 implementer 执行」「gate 只认当前 change」等语义要点（这些是派发时必须在场的操作指令，不是可外链的字面）。避免过度瘦身把操作语义也抽走、反而让派发指令不自足。

## Risks / Trade-offs

- **测试脆性**：契约测试读文档正则匹配格式串，文档正常改写措辞可能误伤。缓解：测试锚定的是**格式 token**（`task<N>-`、`<change>:` 这类结构串）而非整句散文，匹配点收窄到格式片段；文档措辞自由改、只要格式 token 在即绿。
- **③ 引用增间接性**：读 SKILL.md 的人要跳去 workflow.md 才见完整字面。接受——代价是一次跳转，换掉一个反复发生的漂移源；且 workflow.md 经 resolve 一直可达。
- **仍存 doc↔doc 残差**：若②③都改错成同一个错格式、恰好 `TAG_RE` 也被同步改成认这个错格式，测试会绿。这是「三站一起改错」的极端，超出单点漂移防护范围，接受（与本 spec 其他单源守卫的边界一致）。
