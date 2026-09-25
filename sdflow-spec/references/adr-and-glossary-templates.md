# ADR 与术语的惰性提议 — 判据与落盘流程

> 被 `sdflow-spec/SKILL.md` 相位 A/B 的「惰性提议钩子」引用。
> 🔴 **两者一律「只提议、不写入」**——未经人确认 MUST NOT 自动落盘。

## 1. ADR 提议

### 何时提议（三条件，缺一不提）

1. **难以逆转** —— 改回来要动多处、或已有下游消费者。
2. **缺乏上下文会令人意外** —— 半年后的读者看到这个形状会问「为什么不是显而易见的那种做法？」
3. **经过真实权衡** —— 有被砍掉的候选，且砍它有代价。

> 可轻易逆转、或没有真实权衡的决策 ⇒ **只记进 `decision-memo.md`，不产生 ADR 提议。**

### 怎么提议

一句话，附三条件的逐条命中理由 + 建议标题：

> 「建议把 D3 落成 ADR：① 难逆转（三个 skill 已按此派发）② 缺上下文会令人意外（读者会问为什么不用
> 通用子代理）③ 有真实权衡（砍掉了 fallback，代价是 Windows 无 agent）。
> 建议标题：`00NN-agent-fallback-is-self-do-not-generic-subagent.md`。要落吗？」

### 格式真相源

**格式见 `sdflow-adr/references/format.md`**——本 skill MUST NOT 自带 ADR 模板，MUST NOT 照同目录
既有文件的格式写（那会把存量格式漂移带进新文件）。流程固定三步：

1. 人确认后跑 `adr.py new`（编号与骨架机械分配，`--root`/`--title`/`--slug`/`--source` 必填）：
   ```
   python3 ~/.claude/skills/sdflow-adr/scripts/adr.py new --root <消费仓根> \
     --title "<一句话结论>" --slug "<kebab-slug>" --source "<本次 change 名>"
   ```
   找不到该脚本时的定位与提示，见 `sdflow-adr/SKILL.md`「脚本定位」一节。
   该决策**推翻既有 ADR**时加 `--supersedes NNNN`（部分推翻再带 `--partial "<决策范围一句话>"`），
   旧 ADR 的 Status 行由 `adr.py` 一并改写，MUST NOT 手改。
2. 补写正文：骨架的 `Decision` / `Considered Options` / `Consequences` 三节含字面占位
   `TODO(adr)`，按 format.md 的结构与措辞要求逐节补写。
3. `adr.py lint <新文件路径>` 全绿（`TODO(adr)` 清零、Status 行、H2 顺序均通过）后才算落盘完成。

🔴 **MUST NOT 另起一套 `docs/adr/`** —— 那会形成第二套真相源，正是这套工作流一路在消除的漂移。
落点恒为项目的 `openspec/adr/`。

## 2. 术语 / CONTEXT.md 提议

### 何时提议

- 同一个东西在对话里出现了 **≥2 个名字**（且不是同义词随口换）；
- 一个名字在不同人/不同文档里指 **≥2 个东西**；
- 出现「大概/差不多/一般来说」这类**模糊语言**承载了承重约束。

### 怎么提议

> 「『纪要』在本次对话里指了两个东西：相位 A→B 的**锚点纪要**（对话内、不落盘、当拷问靶）与
> `decision-memo.md`（落盘、承重件）。建议在 `openspec/CONTEXT.md` 的术语表各加一行区分。要加吗？」

确认后按 `openspec/CONTEXT.md` **现有的**术语段格式追加（先读该文件，别自造小节）。
项目无 `CONTEXT.md` 时，提议内容降级为写进 `decision-memo.md` 的「目标态」小节旁注，
**MUST NOT 为此新建一个文件**。
