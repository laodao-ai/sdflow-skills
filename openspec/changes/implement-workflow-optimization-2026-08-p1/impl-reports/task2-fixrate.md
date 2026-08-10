# Task 2：实修率历史回算——实现报告

## 范围

`sdflow-retro/scripts/retro_report.py` 新增聚合④「per-镜实修率（历史回算）」——从归档评审
报告 finding 行机械提取 fix-status（三态+未知）与 lens 归属（封闭关键词表，仅有界记号内
查），按 (layer, lens) 聚合可判定/实修/未修/defer 三数 + 覆盖率 + 阈值参考标注 + commit
佐证 flag。对应 tickets.md Task 2 全部 4 项（2.0 真语料试算前置 / 2.1 窄文法提取函数 /
2.2 聚合④段渲染 / 2.3 测试）。

## 2.0 真语料试算前置（一次性脚本，非本 change 交付物）

用一次性脚本（未提交，位于本机 scratchpad）对本仓 `openspec/changes/archive/**/*-review-
report.md`（124 份，62 code-review + 62 spec-review）跑窄文法逐行试算，迭代三轮定位真实
密度与假阳性面：

**第一轮**（naive：任意〔〕/【】即候选门）→ 候选行 842(code)/749(spec)，看似合理但抽查
发现「决策登记区」大量非-finding 内容（Q&A 条目、X-引用标签如 `〔X7〕`）被误当候选——这
类 bracket 在真实语料里是**通用注记符号**，不专属 lens 归属场景。

**第二轮**（发现 bug：`defer`/`已修`/`采纳` 裸子串误命中 `<!-- sdflow:lens-metric v1 ...
defer="0" 采纳="2" ... -->` 锚行的 KV 字段名）→ 修法：整行以 `<!-- sdflow:` 起始即跳过
（机械锚非 finding 行）；`defer` 类标注改词边界 + 负向前瞻 `\bdefer\b(?!=")`，防止未来任何
KV 字段名撞车。**该 bug 直接导致「度量锚」类 section 出现 30–80 条虚假 unknown_disposal
计数**，修复后归零。

**第三轮**（核心发现）：「已裁掉」类表格（列为「裁掉理由」而非「处置」）的行，若无任何
disposal 关键词，会被朴素「有来源记号即候选」判据误判「未修」——单份报告即可贡献 33+7
条虚假未修/defer 样本，方向性拉低实修率（污染砍留判据，与 design.md 已修正的 fix-status
三态问题同族但是**另一根轴**：不是"信号不精确"而是"候选门太宽，把非 finding 行也当
finding"）。**修法**：`not_fixed`（无任何处置信号）分支追加结构门——只有当该行是「处置」
列表格的数据行（`_fr_table_cols` 解析表头同时含「来源」列与「处置」列）时才可能落入未修；
「已裁掉」表因缺「处置」列（只有「裁掉理由」）被此结构信号天然排除，不再产生假未修。
`fixed`/`defer`/`unknown_disposal` 三个正向分支不受此门限制（有处置信号即候选，覆盖
bullet〔〕与表格两种真实 finding 形态）。

**密度结论**（三轮修正后，真语料实测，见下表）：全部 5 个非零 (layer,lens) 格子里，2 个
达到阈值 5（code-review×adversarial=6、code-review×domain=6），其余 3 个（history=2、
spec-review×broad=2、spec-review×grounding=3）低于阈值标「参考」。**大面积低密度与
design.md 已接受的风险一致**（"覆盖率低的镜标「参考」...大面积「参考」亦为合法产出"）——
本试算未推翻该判断，只是把窄文法本身的两个隐藏假阳性源（KV 字段误命中、候选门过宽）在
落地前修正掉，避免生产实现继承同样的坑。

| layer | lens | 可判定 | 实修 | defer | 未修 |
|---|---|---|---|---|---|
| code-review | adversarial | 6 | 2 | 4 | 0 |
| code-review | domain | 6 | 3 | 3 | 0 |
| code-review | history | 2 | 1 | 1 | 0 |
| spec-review | broad | 2 | 0 | 2 | 0 |
| spec-review | grounding | 3 | 0 | 0 | 3 |

（此表由试算脚本产出，与正式实现 `fixrate_aggregate()` 对同一语料的输出一致——已交叉核对，
详见下方「与试算结果交叉核对」。）

## 2.1 窄文法提取函数（`sdflow-retro/scripts/retro_report.py`）

新增函数（均为纯新增，不改 `lens_metric_aggregate.py` 任何既有函数签名，复用其
`_fence_aware_lines` 滤围栏示范锚）：

- `_fr_lens_hits(text)` — 封闭关键词表（对抗/领域/域→领域别名/接地/历史/outside-voice|
  voice→同一 canonical 值/广审）去重命中集合。
- `_fr_table_cols(lines, idx)` — 解析表格数据行所属表头的「来源」列与「处置」列 cell。
  「处置」列存在与否是 `not_fixed` 分支的结构候选门（见上）。
- `_fr_classify_status(line)` — fix-status 三态 + 未修兜底：精确 needle → fixed；defer
  类标注（词边界+防 KV 误命中）→ defer；裸 `impl-review-fix` 或处置动词
  （已修/采纳/自动修）但不命中精确 needle → unknown_disposal（MUST NOT 判未修，
  [spec-review-amendment] 宁缺毋假修正）；否则 → not_fixed。
- `extract_fixrate_samples(text)` — 逐行窄文法提取，产出 `(lens_or_None, status)` list。
  跳过机械锚行（`<!-- sdflow:` 前缀）与 section 标题行（`##`~`####`，防标题自带裸
  `impl-review-fix` 字面量误判，真实语料确有 "Findings（置信 ≥80，均已自动修
  [impl-review-fix]）" 这类标题）。
- `_change_has_fix_commit(root, name)` — change 边界内是否存在 impl-review-fix 类修复
  commit（commit subject 子串匹配，D2 拍板：commit 降为佐证 flag，不参与判定）。
- `fixrate_aggregate(root)` — 扫 archive 全部 `*-review-report.md`，聚合为
  `(rows: {(layer,lens): {可判定,实修,未修,defer,未知,佐证}}, lens_unknown: {layer: n})`。
  两级未知桶：① lens 已解析但 fix-status 不可判 → 计入该 (layer,lens) 自身「未知」字段；
  ② lens 本身不可解析（0/2+ 命中或无有界记号）→ 无法归属具体镜，按 layer 汇总另计
  （`lens_unknown`）。坏文件 fail-safe 跳过，同 `LMA.aggregate` 处理口径。

## 2.2 聚合④段渲染

- `render_fixrate_table(rows, lens_unknown)` — 渲染 `| layer | lens | 可判定 | 实修 |
  defer | 未修 | 未知(本镜) | 覆盖率 | 实修率 | 佐证 |` 表，覆盖率 = 可判定/(可判定+本镜
  未知)；实修率 = 实修/可判定，可判定 < `FIXRATE_MIN_SAMPLE`（=5，单一源常量）追加
  「（参考）」；佐证列展示（不参与判定）。表后附脚注：layer 级 lens-不可归属未知计数 +
  阈值/宁缺毋假声明。
- `build_report()` 尾部新增 `## 聚合④ per-镜实修率（历史回算）` 段，接在既有聚合③之后。

## 2.3 测试

`sdflow-retro/scripts/tests/test_retro_report.py` 新增 21 个用例：

- 合成语料单元（对应 tasks 2.3 六类）：表格来源列可判定 / 〔〕标签可判定 / 来源列零命中
  未知 / 〔〕多命中未知 / 处置信号歧义（裸串/动词变体）进未知非未修（两例）/ 自由文本关键词
  不构成归属 / 围栏内示范锚不入计 / defer 标注分类 / defer 防 KV 字段误命中（负向对照）/
  处置列表格无信号→未修（正例）/ 无处置列表格（已裁掉形态）无信号→非候选（负例，直接对应
  2.0 发现的假阳性）/ section 标题裸串不入候选 / `域`别名识别。
- `fixrate_aggregate`/`render_fixrate_table`：聚合三数正确性、参考阈值展示（≥5 与 <5 两
  方向）、空输入不崩、缺 archive 目录返空、佐证 flag 正反两例（真跑 git commit）。
- `build_report` 集成：聚合④段在场、无 archive 时不崩。
- 真仓再生冒烟：`R.build_report(str(_REPO))` 对本仓真实 archive 语料跑通，聚合④在场；
  且 `surfacing_block` 当前标记的全部待复评 (layer,lens,host,runner,site) 镜，其粗粒度
  (layer,lens) 若在 `fixrate_aggregate` 结果中出现，实修率字符串可读不崩溃（可判定=0
  的镜允许缺行——真实窄文法密度低是已接受风险，非本冒烟测试的失败判据）。

**与试算结果交叉核对**：正式实现 `fixrate_aggregate()` 对本仓真实 archive 目录跑出的
5 个非零 (layer,lens) 计数与上方 2.0 试算表逐格一致（`git checkout -- openspec/retro/
report.md` 前曾用 `retro_report.py --root .` 真跑验证，输出对齐后已还原该 view-only 文件
——report.md 再生提交是 Task 5 职责，不在本票范围内提交）。

## 验证结果

```
/usr/bin/python3 -m pytest sdflow-retro/scripts/tests/ -q
110 passed
```

新增 21 个测试全部通过，既有 89 个测试零回归。

## 偏离/决策记录

- **候选门比 tickets.md 字面描述更窄**：tickets.md 原文「行含处置标注但有界来源记号内...」
  隐含存在一个独立于处置信号之外的「finding 行」判定，但未给出其机械定义。2.0 试算证实
  朴素判据（任意有界记号即候选）会被「决策登记区」通用注记〔〕与「已裁掉」表污染，方向性
  错误分类。落地时收窄为：正向三态（fixed/defer/unknown_disposal）门槛=处置信号存在本身
  （信号本身即证据，不需要额外结构判据）；`not_fixed`（无信号）门槛=处置列表格数据行
  （结构信号，弥补"无信号时无法区分 finding 行与任意散文"的缺口）。此收窄不改变 spec.md
  四个 Scenario 的字面语义（均未直接覆盖"决策登记区污染""已裁掉表污染"这两个真实语料
  边角），是**基准⑤对无界 prose 判据的实现级补强**，非缩小承诺范围——仍锚"MUST NOT 猜
  测归属""宁缺毋假"的目标态，具体实证见上方 2.0 三轮记录。
- **"未知"拆两级（本镜未知 + layer 级 lens-不可归属）**：spec.md 字面「每镜 SHALL 输出
  可判定/未知/覆盖率三数」未明确 lens 本身不可解析时未知数该记在哪面镜。落地按信息量分层：
  lens 已知但 fix-status 未知 → 归该镜；lens 未知（不知道该记哪面镜）→ 归 layer 级共享池，
  避免编造归属。两者均不参与任何镜的可判定分母。
