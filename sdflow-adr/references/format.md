# ADR 格式与更新规则（唯一真相源）

本文件是 `openspec/adr/` 下 ADR 文件的**唯一格式真相源**（AM-1）。新建（`adr.py new`）、
同步（`adr.py refs` + sync 子代理）、体检（`adr.py lint` + audit 子代理）三个入口都读它；
`sdflow-spec`、`sdflow-architecture` 提议 ADR 时也只引用它，不得另带模板或
「照同目录既有文件写」的规则。`adr.py lint` 是本文件规则的机械化实现（ADR-L1–L8）。

## 文件命名

`openspec/adr/NNNN-<kebab-slug>.md`。`NNNN` 为四位数字编号，全目录唯一；`kebab-slug` 匹配
`[a-z0-9][a-z0-9-]*`。目录中不允许出现不匹配此模式的其他 `.md` 文件。

## 正文结构（AM-2）

```
# <一句话结论>                                  ← H1，第一个非空行，不带编号前缀
                                                （空行）
**Status: <取值>** · <来源 change / 日期 / 原因>  ← H1 后第一个非空行，· 之后不可为空
                                                （空行）
<背景段，无标题的普通段落或列表>
## Decision
## Considered Options
## Consequences
## 附录：修订历史
```

- H1 **MUST** 是文件的第一个非空行，只写一句话结论，**MUST NOT** 带 `ADR NNNN:` 或
  `NNNN ·` 这类编号前缀——ADR 的编号已经在文件名里，正文标题不重复。
- Status 行 **MUST** 是 H1 后的第一个非空行，格式固定为 `**Status: <取值>** · <文本>`，
  `·` 之后的文本 **MUST NOT** 为空（写来源 change、日期，或 Deprecated/Superseded 的原因）。
- Status 行之后、第一个 H2 之前 **MUST** 有一个非标题、非围栏代码块的背景段（普通段落或
  列表均可）——空壳 ADR（Status 后直接跳 H2）不合规。
- H2 只允许以下四个标题，且必须按此顺序出现，缺节可以省略，**MUST NOT** 出现其他标题、
  **MUST NOT** 重复：`Decision`、`Considered Options`、`Consequences`、`附录：修订历史`。
  `Considered Options` 属于正文（不是附录内容）——DOC-1 对 ADR 的例外见
  `openspec/rules/doc-authoring.md`。
- 正文 **MUST NOT** 插入修订块（如 `> 更新于 …` 这类夹在正文中间的补丁式段落）；修订记录
  一律进 `## 附录：修订历史`。

## Status 取值枚举（AM-3）

- `Accepted`
- `Superseded by NNNN`
- `` Superseded by `<spec>` spec ``（被某个 OpenSpec spec 取代）
- `Partially superseded by NNNN（<决策范围>）`——多个取代者用 `、` 连接：
  `Partially superseded by 0044（决策 1、2）、0050（决策 3）`
- `Superseded by 0044（决策 1、2）、0050（决策 3）`——Partially 件其余部分也被取代后的
  多目标形态，**MUST** 保留全部取代者与各自范围，**MUST NOT** 退化为单目标
  `Superseded by 0050`；最后一个取代者（整体取代剩余部分的那篇）的范围可省：
  `Superseded by 0044（决策 1、2）、0050`
- `Deprecated`（原因写在 `·` 之后）

## 状态机

```
             细节变化：改正文 + 附录记一条（自环）
                    ┌────┐
                    ▼    │
 new ──────────▶ Accepted ─────────────── 整体取代 ──────────────▶ Superseded by NNNN
                    │  │                                                ▲
                    │  └── 部分取代 ──▶ Partially superseded ── 其余部分也被取代 ─┘
                    │                    │     ▲
                    │                    └─────┘ 再被另一篇部分取代（追加 NNNN（…））
                    └── 对象整体删除、无继任 ──▶ Deprecated
```

终态：`Superseded` / `Deprecated`——正文不再改动，只改 Status 行。
`Partially superseded → Deprecated`（剩余对象整体删除、无继任）也是合法转换。

`Partially superseded` 是**活跃态**：未被取代部分可以按下面「更新四分规则」的「细节变化」
处理并记附录，ADR-L6 / ADR-L8（H2 白名单、背景段存在）同样适用于它；只有 `Superseded` /
`Deprecated` 冻结正文（除 Status 行外不得再改动）。

## 更新四分规则（AM-3）

| 情况 | 动作 |
|---|---|
| 决策不变，细节变了（路径、缺省值、机制位置、行号） | 正文改成现状；`## 附录：修订历史` 追加一条，写明原来是什么、现在是什么、原因、证据 `file:line` |
| 决策整体被推翻 | 写新 ADR；旧 ADR 的 Status 改为 `Superseded by <新编号>`，正文不再改动 |
| 决策部分被推翻 | 写新 ADR；旧 ADR 的 Status 改为或追加 `Partially superseded by <新编号>（<决策范围>）` |
| 决策对象已不存在，且无继任 | Status 改为 `Deprecated`，`·` 之后写原因，正文不再改动 |

`Accepted` ADR 的正文 **MUST NOT** 插入修订块，**MUST NOT** 保留已过期的内容——过期内容按
上表处理，要么改成现状记附录，要么整篇转入取代/废弃状态。

## 转换矩阵

`adr.py new --supersedes` 在创建新文件前按此矩阵机械校验，非法转换退出码 2、目录内容
（字节级）不变：

| 目标当前 Status | 不带 `--partial` | 带 `--partial` |
|---|---|---|
| Accepted（或无 Status 行的旧格式目标） | → `Superseded by <新>` | → `Partially superseded by <新>（TEXT）` |
| Partially superseded by … | → 多目标 `Superseded by <既有列表>、<新>（TEXT 可省）` | → 追加 `、<新>（TEXT）` |
| Superseded / Deprecated | 拒绝（退出 2） | 拒绝（退出 2） |

目标 ADR 若是存量旧格式、没有 Status 行：Status 行插在 H1 下一行，`·` 之后固定写
`由 <新编号> 取代（<日期>；迁移前无 Status 行）`；若目标已有 Status 行，`·` 之后的原文
**MUST** 保留不动，只改 Status 取值本身。

## 修订历史条目写法

`## 附录：修订历史` 每条记录写成一条列表项，含：原来是什么、现在是什么、原因、证据
`file:line`。例：

```
## 附录：修订历史

- **2026-09-25**（`add-sdflow-adr`）：路径由 `sdflow-issues/scripts/issues.py` 改为
  `sdflow-issues/scripts/issues_v2.py`（Task 3 删除 v1 三脚本）。证据：
  `sdflow-issues/scripts/issues_v2.py:1`。
```

新建 ADR 时的骨架各节写字面标记 `TODO(adr)` 占位；`adr.py lint`（ADR-L7）要求全文无
`TODO(adr)` 才算合规——占位标记的存在本身就是「这篇 ADR 还没写完」的机械信号。
