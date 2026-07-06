---
name: sdflow-retro
description: >
  只读再生**本项目 OpenSpec change 的成本×价值复盘报告**——从 git 提交历史抽取各 change 的
  阶段墙钟（成本维），join 归档评审报告（spec-review-report.md / code-review-report.md）里的
  lens-metric 锚（价值维），聚合出 `openspec/retro/report.md`：per-change 明细、阶段占比、
  成本双峰、per-镜价值表。**只呈现不决策**——砍镜/降采样/优先级永远人决，本 skill 不做判断、
  不改动任何 change/spec/issues 内容。专指「openspec change 评审工作流复盘」，
  与通用工程回顾（gstack `retro`：团队周度复盘会）和 `sdflow-maintain`（扫 openspec 目录结构
  一致性、无成本×价值维度）都不是一回事——本 skill 只做这一件事：把 review 工作流自身的
  成本和产出价值摆到一张报告上给人看。触发：想看"这套评审流程到底值不值"、"哪个镜出的问题多"、
  "复盘一下最近几个 change 的耗时"、"regenerate/刷新复盘报告"。Trigger with /sdflow-retro。
---

# sdflow-retro — OpenSpec change 成本×价值复盘

把"从 git 历史和归档评审报告里手工拼数字"这件机械活交给脚本，模型只负责判断
「要不要跑」「跑完怎么呈现待复评区块」——**本 skill 不做任何取舍决策**。

> **为什么只读**：成本（墙钟）来自 git 提交时间戳，价值（findings/采纳率/独立发现）来自
> lens-metric 锚——两者都是既成事实，脚本能确定性算，模型判断反而容易带偏见。
> 复盘的产出是**呈现**，"某镜该不该砍"永远留给人：这是价值度量回路的
> user-sovereignty 设计（lens-metric 一脉相承）。

脚本：[scripts/retro_report.py](scripts/retro_report.py)。

---

## 何时用 / 何时不用

- ✅ 想知道最近几个 change 在评审流程上花了多少时间、哪个阶段最重。
- ✅ 想看 per-镜（lens）出的 findings 数、采纳率、独立发现数——判断某镜是否还值得跑。
- ✅ 归档了新 change 之后，想让 `openspec/retro/report.md` 反映最新数据。
- ⚠️ 不用于：扫 openspec 目录结构一致性（那是 `/sdflow-maintain` 的事）；不用于团队周度
  工程复盘会（那是 gstack `retro`）；不用于记录单个 bug/todo（`/sdflow-buglist` /
  `/sdflow-todolist`）。

## 怎么做

**先判断**（模型的活）：确认在 git 仓内、`python3` 可用、脚本存在——任一条件不满足就
**显式降级提示**，不要静默跳过或伪造结果：

- 不在 git 仓根：提示用户 `cd` 到项目根，或明确本次跑在哪个仓。
- 找不到 `python3`：提示先装 Python 3。
- 找不到脚本本体：提示先跑 `bash setup.sh`（skill 安装未完成或版本落后）。

**再调脚本**（机械活交它）——**必须用绝对 skill 路径调用，禁止 cwd 相对路径**
（F3 铁律：调用方 cwd 是消费仓根，不是 skill 目录本身；两个 agent 运行时都装了 skill，
按实际运行环境二选一，找不到就都试一遍）：

```bash
python3 ~/.claude/skills/sdflow-retro/scripts/retro_report.py --root "$(git rev-parse --show-toplevel)"
# Codex 运行时 sibling 路径兜底：
python3 ~/.codex/skills/sdflow-retro/scripts/retro_report.py --root "$(git rev-parse --show-toplevel)"
```

脚本内部做的事（全部确定性、幂等、无副作用外溢）：

1. 扫 `openspec/changes/`（active + archive）识别全部 change，用 git log 边界探测各自的
   提交区间（跨大规模合并提交的 seed 会被过滤，避免污染单 change 归因）。
2. 按 checkpoint 提交 subject 的 `checkpoint(<inner>)` 前缀把相邻提交的时间差归入阶段
   （spec-review / code-review / impl / grill / ff / other / done / unknown），累加成
   「阶段墙钟」——口径是**阶段级 elapsed（含人读/拍板/生成时间）**，不是纯 agent 耗时。
3. 扫每个 change 的 `spec-review-report.md` / `code-review-report.md`，复用
   `lens_metric_aggregate.py` 的 fence-aware 解析取 lens-metric 锚，按 layer 聚合
   findings/采纳率/独立发现数；坏文件（IO/解码错误）fail-safe 跳过，不崩报告。
4. 原子写 `openspec/retro/report.md`：顶部覆盖计数（覆盖 N change / 有真锚 M / 边界
   不可解析 K——**M 必须显性**，样本量 N 不等于有真实度量锚的 M，实测常见 M ≪ N）、
   D12 待复评区块、per-change 明细表（含 hr-tg 双列 + in-progress/archived 状态）、
   阶段占比、成本双峰（总墙钟 vs code-review 占比）、per-镜价值表。

## 跑完之后

**显著呈现报告顶部的 `⚠️ 待复评:` 区块**（不要一句话带过或藏进长回复里）——这是 D12 机械
契约：某个 (layer, lens, runner, site) 组合的出现轮数 ≥ 10 时会被列出，含义是"这面镜子已经
跑了足够多轮，值得回头看看它还值不值"。**本 skill 只把这些镜子点出来，不建议保留/降采样/
淘汰哪一个**——这个判断交给看报告的人，参考 lens-metric 的历史 findings/采纳率数据自己定。
若该区块显示「无（所有镜出现轮数<10）」，如实呈现这一行，不要因为"没有待复评项"就整段省略——
省略掉的空箱和 hr-tg 空箱、grill 跳过类判定一样，会让"长期无信号"被静默吞掉。

## report.md 是什么

`openspec/retro/report.md` 是**view-only 再生 + tracked 活文档**——每次跑本 skill 都会
用当前 git 历史 + 归档评审报告**全量重建**（不是增量 patch），旧内容会被覆盖。这意味着：

- 归档了新 change 但还没跑 retro 之前，report.md 是 **stale** 的——这是已知且接受的取舍
  （不是每次归档都自动触发复盘），report.md 本身不是真相源，**git 历史和归档报告里的
  lens-metric 锚才是真相源**，report.md 只是它们的一份可读快照。
- 进行中（未归档）的 change 也会被扫进 per-change 表，状态列显式标 `in-progress`——
  这类行的墙钟/findings 数据会随后续提交继续变化，读报告时按状态列区分「还在动的」和
  「已经定型的」。
- 提交 report.md 到 git 是为了让复盘结果可追溯、可 diff——每次重新跑退应视为一次
  正常的内容刷新提交，不是需要人工核对的异常。

## 反馈回路免责

本 skill 承接 lens-metric 价值度量回路的**user-sovereignty**原则：聚合和呈现是脚本的活，
"哪面镜子还留着、要不要降采样、要不要淘汰"是人的活，两者不混在一起。sdflow-retro 本身
**不做复评判断、不自动砍任何镜**——即便某镜的采纳率长期为 0 或出现轮数远超 10，报告也只
如实呈现数字和待复评标记，不给出"建议淘汰"之类的结论性语言，避免度量指标被反噬性地
用来自动优化掉那些短期看似"低效"但长期有价值的镜。
