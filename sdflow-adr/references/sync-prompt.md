## 你的任务

你是本次 `sdflow-done` 收尾第 1.5 步「ADR 同步」派出的子代理，负责本批（≤20 篇）候选 ADR
的核对。格式与更新规则的唯一真相源是 `sdflow-adr/references/format.md`——不确定格式时先读它。

**输入**：change 名 `{change_name}`、本批候选 ADR 文件路径列表（每条含编号、路径、Status、
命中词、是否显式引用，来自 `adr.py refs` 的输出）、`{change_dir}/decision-memo.md` 与
`{change_dir}/design.md` 的路径（判断「本 change 是否声明了取代」的唯一依据）。

## 先读 Status，按分支处理

对本批每一篇候选 ADR：

1. **先读 Status 行**：
   - `Superseded by …` / `` `Superseded by `<spec>` spec` `` / `Deprecated`（终态）
     → **跳过正文核对**，不改动该文件，直接记「无变化」。
   - `Partially superseded by …`（活跃态）→ **只核对未被取代的部分**（Status 行标注的
     `（决策范围）` 之外的其余决策）；被取代部分不管。
   - `Accepted` → 正文全篇核对。
2. 对需要核对的部分，把 ADR 正文的每条陈述与代码现状对照（用 Grep/Read 找证据），归入以下
   五类之一：

| 分类 | 判据 | 动作 |
|---|---|---|
| **一致** | 陈述与代码一致 | 不动 |
| **细节变化** | 决策不变，路径 / 缺省值 / 机制位置 / 行号等细节不符 | 改正文为现状 + `## 附录：修订历史` 记一条 |
| **已声明取代但 Status 未改** | `decision-memo.md` 或 `design.md` 明确声明本 change 取代了该 ADR 的决策，且被声明的新 ADR **已存在**于 `openspec/adr/`，但旧 ADR 的 Status 行还没改 | 改旧 ADR 的 Status 行（按 §2 转换矩阵：整体取代写 `Superseded by NNNN`；部分取代写/追加 `Partially superseded by NNNN（范围）`） |
| **未声明的偏离** | 代码走向与该 ADR 陈述相反，且 memo/design **均未**声明取代——含「声明了取代但新 ADR 不存在」两种子情况 | **MUST NOT 改该 ADR**；记 issues bug（见下） |
| **对象已删除** | 决策所指对象（文件/机制）在代码里已整体不存在，且无继任 | **MUST NOT 改该 ADR**（Deprecated 须人拍板）；记 issues bug（见下） |

`Considered Options` 属正文的一部分，与 `Decision`/`Consequences` 同样核对。

## `## 附录：修订历史` 条目格式

追加在文件末尾 `## 附录：修订历史` 节下（无此节则新建，紧跟在 `## Consequences` 之后、
文件末尾）。每条一行，含：原来是什么、现在是什么、原因、证据 `file:line`：

```
- **YYYY-MM-DD**（`{change_name}`）：<字段/路径/缺省值> 从 `<旧值>` 改为 `<新值>`，
  原因：<一句话>。证据：`<file>:<line>`。
```

日期用今天。正文里被替换的旧值直接删除、写成现状，不在正文里保留新旧对照（新旧对照只在附录）。

## 未声明偏离 / 对象已删除 → 记 issues bug（add 前先查重）

**不直接改 ADR**。先查重再记录，避免同一批 / 重跑 sync 时对同一发现重复建号：

```bash
python3 <issues_v2.py 路径> --root . scan --json --pool bug --source-change {change_name}
```

扫描返回里若已有同一 ADR、同一类偏离的未闭合项（`OPEN`/`PROPOSED`），跳过、不再记；否则：

```bash
python3 <issues_v2.py 路径> --root . add --pool bug --json '{
  "module": "adr/<NNNN>",
  "summary": "<一句话：ADR <NNNN> 陈述 X，代码现状是 Y（未声明取代/对象已删除）",
  "priority": "<按影响自行判断>",
  "source_change": "{change_name}"
}'
```

`issues_v2.py` 定位：随 `sdflow-issues` skill symlink 到 `~/.claude/skills/sdflow-issues/scripts/issues_v2.py`；
固定路径不存在时依次尝试 `~/.agents/skills/sdflow-issues/scripts/issues_v2.py`、仓内
`find . -name issues_v2.py`。

## 完成后返回

对本批逐篇给出：

```
<NNNN>: <一致 / 细节变化 / 已声明取代但 Status 未改 / 未声明的偏离 / 对象已删除>
  [若改了正文/Status：一句话说明改了什么]
  [若记了 bug：issues ID]
```

末尾附**已触碰文件清单**（本批中被你 Edit/Write 过的 ADR 文件绝对路径，无论最终是否保留——
供主 session 人工核对；主 session 实际以 `git diff --name-only -- <本批候选路径>` 取到的
改动集为准（只看本批候选路径，**MUST NOT** 改本批以外的 ADR），对该集合跑 `adr.py lint`，非 `completed` 终态或该集合内任一文件仍有红项，
会对该集合整体 `git checkout --` 撤销）：

```
已触碰文件：
- <path>
- <path>
```

无改动则写「已触碰文件：无」。

## 边界（Non-Goals）

- 不判断本篇 ADR 是否「值得写」或「该不该存在」——那是 audit / 人的事。
- 不做全目录 lint——只管本批涉及的文件；lint 由主 session 在你返回后统一跑。
- 不删除任何 ADR 文件。
- 不越权把「未声明的偏离」自行判为「已声明取代」——没有 memo/design 白纸黑字，一律走 bug 池。
