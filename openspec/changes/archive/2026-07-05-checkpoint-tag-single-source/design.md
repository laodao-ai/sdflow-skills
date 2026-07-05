<!-- [spec-review-amendment] Q1=B：原 D1/D2/D3（doc 正则抽取绑定 + SKILL.md 瘦身）被四路冷审证伪，
     整节重写为 producer→parser 集成测试 + 负例矩阵。证伪细节见 spec-review-report.md H1-H4/A-1~A-5。 -->

## Context

checkpoint 标签 `checkpoint(<change>:task<N>-<slug>)` 是 gate 完成判据主锚。真正决定"标签能否被 gate 认"的是两个**代码**站点，不是文档：

```
  producer                              parser
  checkpoint-commit.sh                  ship_gate.py TAG_RE
  ($1 → "checkpoint($1): $desc")  ───▶  checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-
  sdflow-init/assets/hack/…:46/48       ship_gate.py:231
```

workflow.md / SKILL.md 是给 implementer 看的**人读文档**，里面是**占位符**（`<change>:task<N>-<slug>`）不是真标签——它们影响 implementer 手写什么，但不参与机器解析。**真正无守卫、且漂移即假✅的是 producer→parser 这条链**：脚本改包裹（如 `ckpt($1)`）或 `TAG_RE` 改捕获，标签就静默不计入完成集。

> **本 change 的初版设计（doc 正则抽取双向绑定 + SKILL.md 瘦身）已被 spec-review 实质证伪**：doc 侧是占位符非真标签（抽取→实例映射是作者手写，锚的是作者理解非文档字面）；"MUST NOT 硬编码期望串"与"doc 漂移即红"两条 MUST 互斥（A-1）；`TAG_RE` 三种真放松实测全部保绿（A-2）；SKILL.md 瘦身反造 design 自己要避免的读依赖、退化路径正是要防的假✅（H4）。详见 `spec-review-report.md`。此版据 Q1=B 收敛到经得起冷审的内核。

## Goals / Non-Goals

**Goals:**
- 焊 **producer→parser** 链：`checkpoint-commit.sh` 真产的 subject MUST 能被 `TAG_RE` 认且捕获正确——用真实脚本调用的**集成测试**，非文档文本比对。
- 给 `TAG_RE` 补**负例矩阵**：一组 MUST NOT match 的 subject，使"正则被放松"能被测出（补上 parser 侧唯一 happy 例的盲区）。
- 零运行时行为变更（`TAG_RE` / `checkpoint-commit.sh` 逻辑逐字不变）。

**Non-Goals:**
- **不**瘦身 SKILL.md、**不**改 workflow.md（原 D3 撤销——自毁）。
- **不**试图机械化 doc↔doc 文案 DRY（证伪为循环；既有 `test_workflow_authority.py` 子串断言作弱守卫、保持现状）。
- **不**碰标签格式语义（命名空间/裸兼容/窗口全不动）。
- 不碰 T33/T35。

## Decisions

### D1：契约测试 = 真实脚本调用的集成测试（不是文档文本比对）

在临时 git repo 里跑**仓内真实** `sdflow-init/assets/hack/checkpoint-commit.sh`，传 `demo:task1-slug` 作 `$1`，读回 `git log -1 --format=%s` 的 subject，喂给 `import` 来的 `TAG_RE`，断言 `match` 且 `group(1),group(2)==("demo","1")`；裸 `task1-slug` 断言 match 且 `group(1) is None`。

**为何这样才 sound**：它锚的是**脚本真吐的字节**（`checkpoint(demo:task1-slug): …`）↔ **gate 真跑的正则**，中间没有"作者对占位符的理解"这层。producer 改包裹或 parser 改捕获，任一即红——这才是名副其实的"任一站漂移即红"（限定在两个 code 站点，不虚张"文档也钉死"）。

### D2：`TAG_RE` 负例矩阵——把 parser 侧从"单 happy 例"升级到有边界

spec-review A-2 实测：仅"正例 match + 捕获对"时，`task(\d+)-?`（尾 dash 可选）、`[a-zA-Z0-9]`（大写命名空间）、`task(\d*)`（号可空）三种放松都保绿。故 MUST 加负例集，每条断言 `TAG_RE.match(...) is None`：

| 负例 subject | 该挡住的放松 |
|---|---|
| `checkpoint(task1slug)` | 尾 dash 变可选（丢 `task1`/`task12` 边界锚） |
| `checkpoint(DEMO:task1-)` | 命名空间允许大写（破 kebab 锁） |
| `checkpoint(task-1-)` | 号位允许非数字 |
| `checkpoint(:task1-)` | 空命名空间 |

负例集是本 change 的核心 sound 增量——它把"漂移即红"从口号变成可复现断言。（具体条目实现期可微调，但**空号/大写 ns/无尾 dash 三类 MUST 覆盖**。）

### D3：既有测试与文档一律不动（避冲突、保 doc 侧弱守卫）

`test_workflow_authority.py` 现有的 workflow.md/SKILL.md 子串断言（`test_step6_tag_contract`、`test_skill_producer_arg_namespaced`）**保留不改**。它们是 doc↔doc 侧的（弱但真实的）守卫；本 change 不动 SKILL.md 故不与之冲突（撤 D3 瘦身即消解 spec-review H1）。本 change 只**新增** producer↔parser + 负例两组测试，不改任何既有断言。

### D4：`import TAG_RE` 的 sys.path 注入

现有测试全走 subprocess/`read_text`，`scripts/` 不在 sys.path。负例矩阵与集成测试断言 `TAG_RE` 需 `import`，故测试文件内 `sys.path.insert(0, str(<scripts 目录>))` 后再 `from ship_gate import TAG_RE`（`ship_gate.py` 有 `__main__` 守卫，import 无副作用）。照既有 `GATE = …/"scripts"/"ship_gate.py"` 路径约定定位。

## Risks / Trade-offs

- **不覆盖 doc↔doc 漂移**：本 change 不新增 doc↔doc 机械守卫（证伪为循环）。残差 = 既有子串断言（弱） + **人工评审**（无自动化兜底）。**接受**——原想机械化的那层被证明不 sound，硬做只会造假绿。
  - <!-- [spec-review-amendment DF2] --> 诚实披露：既有 `test_workflow_authority.py` 两条 doc 子串断言中，`assert "task<N>-" in t`（第 19 行）是同段 `"<change>:task<N>-"`（第 18 行）的**子串**，逻辑恒真——对"裸兼容语义"**零守卫力**（Round 1 的 M2）。故 doc↔doc 侧真正有效的弱守卫只有命名格式那条，别把这对断言笼统当"弱但真实守卫"高估。
  - <!-- [spec-review-amendment DF3] --> 措辞更正：先前把残差写作"spec-review **G1 兜底**"是不当类比——G1（见 proposal）是过去一次靠人工评审**运气**抓到的漏改事故，非可重复触发的机械机制。doc↔doc 链**无自动化兜底、纯依赖人工评审**，已知比 producer→parser 链（有本 change 的机械绑定测试）弱；不拿 G1 包装成防线。
- **producer 站点漂移概率低**：`checkpoint-commit.sh` 包裹逻辑稳定、少改。但集成测试便宜、且它是**唯一**真铸造 subject 的地方，值得一测（防未来重构无声破链）。
- **负例集非穷举**：负例矩阵挡的是已知放松类，不能证明 `TAG_RE` 对所有畸形输入正确。接受——目标是封住 spec-review 实证的漏报类，非形式化验证。
  - <!-- [spec-review-amendment DF1] --> 已补 Round 2 冷审（对抗镜#1 mutation）实证的一类漏报：号位加宽为字母数字（`task(\d+)-`→`task([a-z0-9]+)-`），负例 `checkpoint(taskab-slug)`；并修正 `checkpoint(task-1-)` 注释（其实挡的是"号位空/含前导符号"，非"号位允许非数字"）。已知仍不穷举（DF4-7 记 todolist）。
