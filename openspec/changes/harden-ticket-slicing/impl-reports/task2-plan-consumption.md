# Task 2 impl-report: 出票侧消费语义与必触发复核

- **票**: Task 2（`tasks.md` 第 2 组 2.1–2.3）
- **base**: `e81e6636f5294ca7e26687fc386eb3b6b805c49c`（feat/harden-ticket-slicing，含 Task 1 已落地
  的 `change-decomposition-standard.md` + BASE-31）
- **改动文件**: `sdflow-implement/SKILL.md`（唯一改动文件，其余文件零改动）
- **`sdflow:principles` 托管块**: 未动，`python3 hack/sync_principles.py --check` 通过（见下）

## 起手环境问题（非本票工作内容，但影响可核验性，如实记录）

本 worktree 分配时基于的分支是 `main`（`1540703`），不含 `feat/harden-ticket-slicing` 分支上
`e81e663`（落盘 task2/task3 brief 的提交）。任务说明里指定「基于 `e81e663`」与实际 worktree 状态
不一致——`git merge-base --is-ancestor e81e663 HEAD` 判 NOT ANCESTOR。核实该 worktree 分支
（`worktree-agent-a44ae4fa6eba1863b`）无任何独有提交（`git status` clean、HEAD 恰为 `main` tip）后，
判定为无损操作：`git reset --hard e81e663` 把本 worktree 分支对齐到正确 base。此后方能读到
`impl-reports/task2-brief.md`。

## 验收标准逐条对照

| # | 验收标准 | 落点 | 达成证据 |
|---|---|---|---|
| 1 | 消费语义改为默认采纳 + 偏离逐条记 `planning-decisions.md`，行格式「切片偏离: <偏离点> \| <理由(三镜+主次)>」，MUST NOT 静默偏离 | `sdflow-implement/SKILL.md:254-260`（起手检查段） | 新增「切片建议消费语义 = 默认采纳 + 偏离审计」小节，逐字给出行格式与 MUST NOT 静默偏离；替换原「建议输入」措辞 |
| 2 | `T10-choice` 复核必触发三条件写入 | `sdflow-implement/SKILL.md:262-269` | 三条件编号列表①既无节也无成立缺席理由②实质偏离草图③草图与 design 正文矛盾，逐字对应 spec `impl-orchestration/spec.md:9` |
| 3 | 条件①取 Q1-A 口径：合规缺席不触发；缺席理由蕴含单票而出 >1 张功能票 ⇒ 视同条件③矛盾触发 | `sdflow-implement/SKILL.md:264` | 条件 1 括注原样写入该口径 |
| 4 | 既有「粒度争议」触发路径保留不变，与必触发三条件并存 | `sdflow-implement/SKILL.md:262`、`:280-283` | 三条件标题句明写「既有路径保留不变，与下列三条件并存」；段尾补回「粒度争议…走同一 `T10-choice` 三级决策协议」一句，未删除原有粒度争议路径的语义 |
| 5 | 复核结论接三级协议出口：通过⇒按方案出票；证伪或无从复核⇒停并上抛，MUST NOT 继续用被证伪方案 | `sdflow-implement/SKILL.md:270-272` | 「复核结论按既有 `T10-choice` 三级协议出口」句 + 证伪/无从复核 ⇒ 停并上抛 + MUST NOT 继续出票 |
| 6 | 附诚实边界句：必触发为指令层约束，判定由出票方自报无确定性信号，MUST NOT 表述为机械保证 | `sdflow-implement/SKILL.md:274-275` | 🔴 诚实边界 blockquote，逐字对应 spec 措辞 |
| 7 | 新增「票外发现上报」段：implementer 撞到相关但票外的发现 MUST NOT 自行扩 scope，上报编排层按 BASE-18 AND 门判 fold/defer，判定记一行入该票 impl-report | `sdflow-implement/SKILL.md:615-618`（dispatch 必含项）+ `:643-658`（编排层处置新节「票外发现的 fold/defer」） | dispatch bullet 要求 implementer 上报不自扩；新节写明判定入口=`change-decomposition-standard.md`→BASE-18 AND门，fold/defer 两分支处置，「判定与去向 SHALL 记一行入该票 impl-report」 |
| 8 | fold 时序边界：未进双轴审可并入当前票；已在途/已完成 ⇒ 追加进后续票或新增 Blocked-by 当前票的票，MUST NOT 中途改动已在双轴审途中的票的验收标准 | `sdflow-implement/SKILL.md:651-655` | 两分支列表逐字覆盖，含 MUST NOT 中途改动一句 |
| 9 | implementer dispatch 模板同步带上报指令（未声明即等同未约束） | `sdflow-implement/SKILL.md:615-618` | 该 bullet 在「派发 Agent…dispatch prompt 必含」列表内，且带🔴与「子代理是 fresh context，未声明即等同未约束」原文措辞 |
| 10 | `sdflow:principles` 托管块零改动 | 见下机械核验 | `sync_principles.py --check` 通过 |

## 硬核验点（编排层指定）

```
$ grep -rn "change-decomposition-standard" sdflow-implement/
sdflow-implement/SKILL.md:647:`openspec/workflow/reference/change-decomposition-standard.md`（经 resolver 解析）指向的
```
命中。Task 1 已在 bundle 文档（`reference/change-decomposition-standard.md` 头部）写下「本标准文
被 `sdflow-implement` 等三处消费点以指针方式引用」的断言，本行是该断言在 `sdflow-implement` 侧成真
的落点。

## 命令与退出码

```
$ python3 hack/sync_principles.py --check
[sync_principles] ✅ 27 个投放面全部与真相源一致（四条通则 + 广审镜定义）
exit=0

$ /usr/bin/python3 -m pytest -q
2601 passed, 10 skipped in 413.27s (0:06:53)
exit=0
```

## TDD 契约说明（未新增自动化测试及理由）

本票改的是 `sdflow-implement/SKILL.md` 指令文本，非可执行代码；`grep` 确认仓内对该文件**没有**
针对措辞/节结构的机械守卫（唯一相关的机械门是 `sync_principles.py --check`，只守
`sdflow:principles` 托管块，本票未触碰该块，已核验通过）。为凑 TDD 而对该指令文本硬造断言测试会
落进「无界语法面手搓解析器」（CLAUDE.md 基准 5）——故本票**无新增自动化测试**，验证手段 = 全仓
既有 pytest 保持绿（未破坏任何既有守卫）+ 逐条验收标准的 `file:line` 锚（上表）。

## Concerns

无。全部验收标准逐条达成，硬核验点命中，全仓测试与托管块门禁均绿。

## 范围内未做的事

无——tasks.md 第 2 组三项（2.1/2.2/2.3）全部完成，未发现票外相关发现需上报 fold/defer。
