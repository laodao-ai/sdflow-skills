# Task 1 impl-report：bundle 规则面成型（切片建议升档 + BASE-31 + 拆分标准单一源）

**Blocked-by:** none · **R-ID:** SA-17 · **起点 SHA:** `969cadac6691aa36c55343bfb98f0e4d43fa75e6`

## 改了哪些文件

| 文件 | 改动 |
|---|---|
| `sdflow-init/assets/workflow/ff-generation-constraints.md` | §切片建议：MAY→SHOULD + 缺席理由要求 + 票数预算兼容提示 + 消费语义指向单一源（不复制） |
| `sdflow-init/assets/workflow/spec-checklists/spec-quality-base.md` | 新增 BASE-31 一行（存在性/缺席理由成立性/切片内聚质量/票数预算兼容，适用域显式限定 design.md）；BASE-18 行尾追加与新标准文的互指指针 |
| `sdflow-init/assets/workflow/reference/change-decomposition-standard.md`（新增） | 4 规则 + why：一个 change/phase=一个完整阶段结果、不按批次/凑票拆、related 优先 fold（defer 判定入口=BASE-18 AND 门）、缺依赖模块是经典 defer 形态非绝对句 |
| `sdflow-init/assets/workflow/reference/README.md` | 标题/intro 从「非 load-bearing 全可删」改为「一份例外」；新增表格行登记新文件为 load-bearing |
| `sdflow-init/assets/snippets/index-section.md`（真相源） | 改一行：reference/ 目录描述从「说明类（可删不影响执行）」改为「多为说明类…另含 change 拆分标准单一源…执行必需」 |
| `openspec/INDEX.md` | 经注入路径（`init.py` 的 `inject()` + `read_snippet("index-section.md")`）刷新，非手改托管块——与真相源字节一致 |

未新增/修改任何 `scripts/` 或 `ship_gate.py`（见下方验证）。

## 每条验收标准的达成证据

1. **MAY→SHOULD + 缺席理由 + 二择一恒成立措辞** — `sdflow-init/assets/workflow/ff-generation-constraints.md:40-41`：
   `design.md 决策区 **SHOULD** 含「切片建议」节...节缺席时决策区 **MUST** 写明一句为何不需要——「有节」或「有缺席理由」二择一恒成立，不存在两者皆缺的合规态。`
2. **票数预算兼容提示（3–6 张或 expand–contract 例外）** — 同文件 `:43-44`：
   `草图票数须落 **3–6 张垂直切片**预算内；超出该预算须在节内注明 expand–contract 例外依据。`
3. **BASE-31 新增，四要素齐全 + 适用域显式限定** — `sdflow-init/assets/workflow/spec-checklists/spec-quality-base.md:55`（BASE-31 行）：存在性/缺席理由成立性/切片内聚质量/票数预算兼容四要素齐全；行首括注 `（适用域 = change 四件套评审的 design.md；roadmap 三件套无切片建议契约，本项 N/A）`。
4. **BASE-31 未改动镜表** — `git diff --stat` 未涉及 `sdflow-spec-review/SKILL.md` / `sdflow-roadmap/SKILL.md`（见下方全量 diff --stat）；归镜依据既有默认规则句「未列明的既有或未来新增 base R 项归本镜」（`sdflow-spec-review/SKILL.md:248`，本票未改动，仅读取核实）。
5. **新增 change-decomposition-standard.md：4 规则 + why** — 文件 `sdflow-init/assets/workflow/reference/change-decomposition-standard.md` 全文；「## 规则」节 4 条编号 1–4，「## Why」节讲 fold-vs-defer 两方向失衡的成因。
6. **「缺依赖模块」写为经典 defer 形态非绝对句** — 同文件规则 4：`「缺依赖模块 → 占位 + 记 todo」是 related 语境下的经典 defer 形态，不是与规则 3 的 AND 门并列的「唯一合理 defer」绝对句——AND 门未满足的其余情形...同样合法落 defer，缺依赖模块只是其中最常见的一种，不得被写成排除其它 defer 理由的绝对句。`
7. **与 BASE-18 互为指针不复制** — 标准文头部指向 `spec-checklists/spec-quality-base.md` 的 `BASE-18`；`spec-quality-base.md` 的 BASE-18 行尾反向指向 `../reference/change-decomposition-standard.md`（`spec-quality-base.md:42`）；两处均只放一句判定语义/链接，不复制对方正文。
8. **INDEX 可发现（改源 + 经注入路径刷新，两侧一致）**：
   - 改源：`sdflow-init/assets/snippets/index-section.md` 第 20-21 行。
   - 刷新仓内 INDEX：用 `python3 -c` 调用 `sdflow-init/scripts/init.py` 的 `inject()` + `read_snippet("index-section.md")` 只重写 `openspec/INDEX.md` 的 `<!-- opsx-init:rules:start -->...end` 托管块（返回值 `"更新托管区块"`），未手改托管块内部字符。
   - 一致性核验：`diff <(sed -n '/opsx-init:rules:start/,/opsx-init:rules:end/p' openspec/INDEX.md) <(...)` 未跑独立 diff 脚本，但 `git diff openspec/INDEX.md` 显示改动内容与 `git diff sdflow-init/assets/snippets/index-section.md` 的新增两行逐字一致（见下方 diff）。
9. **消解分类矛盾（改一行 snippet，落点不换目录）** — `index-section.md` 第 20 行原文 `说明类（可删不影响执行）：[workflow/reference/](./workflow/reference/)。` 改为 `多为说明类（可删不影响执行），另含 change 拆分标准单一源（\`change-decomposition-standard.md\`，被三处 SKILL 引为执行必需的规范文本，详见目录内 README）：[workflow/reference/](./workflow/reference/)。`——落点仍在 `workflow/reference/`，未换目录。（连带在 `reference/README.md` 自身 intro 与新增表格行做同向一致性修正，非验收硬性要求但消解目录内部的同一矛盾，避免刚改完索引又留下一处未同步的自相矛盾描述。）
10. **`ship_gate.py` 及机械层脚本零改动** — `git diff --stat`（见下方）不含任何 `scripts/` 路径或 `ship_gate.py`。

## `git diff --stat`

```
$ git diff --stat
 openspec/INDEX.md                                                     |  3 ++-
 sdflow-init/assets/snippets/index-section.md                          |  3 ++-
 sdflow-init/assets/workflow/ff-generation-constraints.md              | 12 +++++++++---
 sdflow-init/assets/workflow/reference/README.md                       | 16 ++++++++++------
 sdflow-init/assets/workflow/spec-checklists/spec-quality-base.md      |  3 ++-
 5 files changed, 25 insertions(+), 12 deletions(-)
$ git status --short
 M openspec/INDEX.md
 M sdflow-init/assets/snippets/index-section.md
 M sdflow-init/assets/workflow/ff-generation-constraints.md
 M sdflow-init/assets/workflow/reference/README.md
 M sdflow-init/assets/workflow/spec-checklists/spec-quality-base.md
?? sdflow-init/assets/workflow/reference/change-decomposition-standard.md
```
（`openspec/changes/harden-ticket-slicing/impl-reports/task1-brief.md` 为编排层落盘的票原文，非本票产物，未列入。）

## 跑过的测试与输出摘要

- `/usr/bin/python3 hack/sync_principles.py --check` → `[sync_principles] ✅ 27 个投放面全部与真相源一致（四条通则 + 广审镜定义）`，exit 0（本票未改任何 `SKILL.md`，托管块本应无影响；跑一遍确认未误伤，按信号权威表「本仓的机械事实」建议执行）。
- `/usr/bin/python3 -m pytest -q`（全仓）→ `2601 passed, 10 skipped in 380.15s (0:06:20)`，exit 0。10 个 skip 为既有 skip（未新增/未减少，本票未触碰任何 `scripts/`/测试文件，属预期不变）。

本票范围内无新增/修改代码逻辑（纯 bundle 规则文本 + 新增 reference 文档 + INDEX 注入），无需新增单元测试；TDD 契约中的 red→green 循环不适用于纯文档改动（无可执行的公共接口边界）——与 Global Constraints「新增判定均为语义层，不引入任何格式解析器」一致。

## Concerns

- **BASE-18 行长度已很长**，本次在行尾又追加一句指针，表格单元格进一步变长（可读性代价，非功能问题）——若后续再有类似追加，建议评估是否该拆表格外附注，本票未做该重构（避免加宽超出票范围）。
- **reference/README.md 的编辑超出 tasks.md 1.1–1.4 字面枚举**（tasks.md 未显式要求改 README.md），是我基于 BASE-07 内部一致性 + 编排层给出的「新文件按该目录既有文风落」机械事实，判断为同一片一致性面内的必要联动而主动补的一处（未改变任何验收标准判定的落点文件，仍在 `reference/` 目录内、`change-decomposition-standard.md` 文件本身之外的最小联动）。如认为超出本票范围，可在双轴审时单独裁定是否收窄。
