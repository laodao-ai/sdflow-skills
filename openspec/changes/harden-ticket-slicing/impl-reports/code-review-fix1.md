# code-review-fix1 — 4 条已采纳 finding 的自动修

来源：sdflow-code-review 裁决，标注 `[impl-review-fix]`。change = `harden-ticket-slicing`，分支
`feat/harden-ticket-slicing`。

## 修复 1（high）：「单票交付」合规路径 vs 3–6 张预算 互相矛盾

补一条与 expand–contract 并列的显式「不足预算」例外：design.md 写明成立的「单票交付」缺席理由、且
出票确为 1 张功能票时合规。三处口径一致：

- `sdflow-init/assets/workflow/ff-generation-constraints.md:43-46`
  改前：「草图票数须落 3–6 张垂直切片预算内；超出该预算须在节内注明 expand–contract 例外依据。」
  改后：补一句「不足预算也有一条与 expand–contract 并列的合法例外〔impl-review-fix，
  harden-ticket-slicing〕：本节写明成立的『单票交付』缺席理由、且出票确为 1 张功能票时视为合规
  ——该例外不需要额外注明依据，缺席理由本身即依据。」
- `sdflow-implement/SKILL.md`「### 产出：3–6 张 tracer-bullet 垂直切片」标题下方
  改前：标题后直接进入 bullet list。
  改后：标题下方插入 blockquote 说明同一例外，指回「起手检查」T10-choice 必触发条件①，标题本身
  未改（不为一个例外重写标题，符合任务要求）。
- `openspec/changes/harden-ticket-slicing/specs/impl-orchestration/spec.md`
  MODIFIED Requirement「出 ticket 模式产出 tracer-bullet ticket…」首句括号说明处，追加
  「design.md 写明成立的『单票交付』缺席理由且出票确为 1 张功能票时，是与 expand–contract 并列的
  合法例外，同样不受该预算约束〔impl-review-fix〕」，与既有的 expand–contract 迁移批次/收尾票
  不占预算的说明并列。

收尾票（`R-ID: all`）规则未动。

## 修复 2（high）：「切片建议」落在 ff-generation-constraints.md 自述范围之外，四处摘要口径不一致

改「扩摘要口径」（非编 D-7 号），依据：编号要动 D 表 + 触发条件表 + prompt 片段 + 检查清单四处，
爆炸半径远大于范围；根因是「摘要范围窄于全文」，改摘要口径即消除。全部五处均改：

- `ff-generation-constraints.md:1` 标题：`# 生成起手强制规范（FF-0 + D-1~D-6）`
  → `# 生成起手强制规范（FF-0 + D-1~D-6 + 切片建议）`
- `ff-generation-constraints.md:3` 定位声明：原句只列「FF-0（开分支）」与「D-1~D-6」
  → 追加「以及『切片建议』节的生成侧规范〔impl-review-fix，harden-ticket-slicing〕」
- `openspec/config.yaml:10`：`ff-generation-constraints.md  生成时硬约束 D-1~D-6`
  → `ff-generation-constraints.md  生成时硬约束 D-1~D-6 + 切片建议〔impl-review-fix〕`
- `sdflow-init/assets/workflow/config.template.yaml:26`：同上句同改法（下游模板）
- `sdflow-init/assets/snippets/index-section.md:12`（源）与 `openspec/INDEX.md:17`（注入产物）：
  「生成起手强制：FF-0 开分支 + 生成硬约束 D-1~D-6（…）」
  → 「生成起手强制：FF-0 开分支 + 生成硬约束 D-1~D-6 + 切片建议（…）」
  —— 先改 snippet 源，再手工使 INDEX.md 该行逐字相同（已用 `diff` 自验一致，见下方核验）。
- `sdflow-init/assets/workflow/workflow-rules-guide.html:263`（ASCII 目录图行）：
  「FF-0 分支判定 + D-1~D-6 生成硬约束」→「FF-0 分支判定 + D-1~D-6 生成硬约束 + 切片建议」
  `:352`（rule-card 摘要段）：标题「FF-0 前置动作 + D 约束」→「FF-0 前置动作 + D 约束 + 切片建议」，
  段落追加一句「『切片建议』是 design.md 决策区的初步 ticket 划分规范」。只改这两处描述短语，
  未动 HTML 结构。

## 修复 3（high · 两面镜独立收敛）：票外发现上报未接进 implementer↔编排层通信契约

比照既有 `DONE_WITH_CONCERNS` 的同构解法（固定小节 + 一行摘要标注 + MUST Read 契约），三处改动：

- `sdflow-implement/SKILL.md` 「每 ticket 派 fresh implementer」节 dispatch 必含项里的
  「🔴 票外发现上报」bullet：追加通道形状——有发现时全量写入该票 report file 固定小节
  `## 票外发现`（无发现可省略）；dispatch 返回值一行摘要追加标注 `[has-off-ticket-finding]`。
- 同文件「### 票外发现的 fold/defer」段：追加一段「读取契约」blockquote，比照 `DONE_WITH_CONCERNS`
  澄清段的措辞——看到该标注时执行模式 MUST Read 该小节全文再判 AND 门，MUST NOT 只凭一行摘要判定；
  未标该记号视为无票外发现，无需去读。
- delta spec `specs/impl-orchestration/spec.md` ADDED Requirement「执行期票外发现上报编排层按拆分
  标准判 fold/defer」正文中插入同一通道契约句（固定小节 + 返回值标注 + MUST Read），并同步更新对应
  Scenario「implementer 撞到相关票外 bug 上报而非顺手修」的 THEN 分支措辞，使其与新通道一致
  （不再是笼统的「在返回中上报」）。

## 修复 4（medium）：fold 新增票未声明是否须过出票期治理

`sdflow-implement/SKILL.md` 「### 票外发现的 fold/defer」段的 fold 子条目末尾，追加一句：「执行期
新增的票 SHALL 补齐上方『出票模式』节对 ticket 的强制字段与闸门（`Blocked-by` / `R-ID` / 验收
复选框 / 语法面有界性闸门），或在该票文本中显式列出豁免哪些、为何〔impl-review-fix〕。」——按指针
引用出票模式既有那节，未复制清单。delta spec 未同步改动（任务范围未要求，本条为 SKILL 层执行细则，
与既有 spec 无直接冲突）。

## 核验

```
$ git diff --stat -- '*.py' '*.sh'
(空，退出码 0)

$ python3 hack/sync_principles.py --check
[sync_principles] ✅ 27 个投放面全部与真相源一致（四条通则 + 广审镜定义）
exit=0

$ /usr/bin/python3 -m pytest -q
2601 passed, 10 skipped in 374.92s (0:06:14)

$ grep -n "D-1~D-6" openspec/config.yaml sdflow-init/assets/workflow/config.template.yaml \
    sdflow-init/assets/snippets/index-section.md openspec/INDEX.md
openspec/config.yaml:10:  - ff-generation-constraints.md  生成时硬约束 D-1~D-6 + 切片建议〔impl-review-fix〕
openspec/INDEX.md:17:| `ff-generation-constraints` | ... D-1~D-6 + 切片建议（`/sdflow-spec` 调用，或 `opsx:ff` 直呼） |
sdflow-init/assets/snippets/index-section.md:12:| `ff-generation-constraints` | ... D-1~D-6 + 切片建议（`/sdflow-spec` 调用，或 `opsx:ff` 直呼） |
sdflow-init/assets/workflow/config.template.yaml:26:  - ff-generation-constraints.md  生成时硬约束 D-1~D-6 + 切片建议〔impl-review-fix〕

$ diff <(sed -n '12p' sdflow-init/assets/snippets/index-section.md) <(sed -n '17p' openspec/INDEX.md)
(空，退出码 0 —— 两侧逐字一致)
```

## Concerns

- `workflow-rules-guide.html:350` 的 `<span class="rule-card-meta">198 行</span>` 在本轮修改前
  就已经与 `ff-generation-constraints.md` 实际行数（本轮改后 208 行）不一致——这是本 change 之前
  遗留的漂移（新增「切片建议」节时未同步该计数），不在本次 4 条 finding 范围内，未改动，如实记录
  供后续处理。
- 修复 4 只改了 `sdflow-implement/SKILL.md`，未同步 delta spec 的 ADDED Requirement 正文。任务
  描述里修复 4 的修法只指名 SKILL.md（「一句话明示…指向出票模式既有那节即可」），未要求同步 spec，
  按原样交付；若后续认为需要 spec 侧也声明该约束，需另行确认。
