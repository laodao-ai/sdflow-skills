# Task 4：考古层审计清理（15 个 SKILL.md）——实现报告

## 范围与方法

按 `find . -maxdepth 2 -name SKILL.md` 实测名单，逐文件读全文，过 DOC-1 删除测试（「只有读过
上一版的人才需要的句子，不属于正文」），删/迁两类处置外迁载体统一为 `<skill>/references/
evolution-notes.md`，正文末尾统一一行指针（`历史取舍不进入默认运行；仅在审计历史依据时读取
references/evolution-notes.md。`）。每处编辑后即跑该 skill 对应 `tests/`（有则跑）+ `hack/tests/`
+ `python3 hack/sync_principles.py --check`。

7 个超 500 行文件重点清理，8 个 ≤500 行文件轻量审计。详细骨架与逐 skill 删/迁/留三计数见
`audit/skill-doc1-audit.md`（同批产出，与本报告互补——audit 是判定依据表，本报告是执行过程与
证据）。

## 逐文件处置

| skill | 处置 | 证据 |
|---|---|---|
| sdflow-implement (821行) | 零改动，留档说明 | 审计确认文中历史提及均为「why」注记（如「裁剪边界声明」防未来误加回已砍机制），不满足删除测试 |
| sdflow-code-review (771行) | 迁 2 处到新建 references/evolution-notes.md + 正文改写 4 处 | git diff: 26 行变动；新文件 `sdflow-code-review/references/evolution-notes.md` |
| sdflow-roadmap (715行) | 正文改写 2 处（判定点②沿革、未决项小节 wayfinder 回指） | git diff: 4 行变动，无新文件（就地精简，未外迁独立段落） |
| sdflow-spec-review (610行) | 迁 3 处到新建 references/evolution-notes.md + 正文改写 4 处 | git diff: 20 行变动；新文件 `sdflow-spec-review/references/evolution-notes.md` |
| sdflow-done (567行) | 删 1 处（v3 changelog 摘要）+ 迁 2 处到新建 references/evolution-notes.md | git diff: 13 行变动；新文件 `sdflow-done/references/evolution-notes.md` |
| sdflow-architecture (562行) | 删 10 处 impl-review-fix HTML 内联审校注释 + 2 处并入正文 | git diff: 27 行变动；新文件 `sdflow-architecture/references/evolution-notes.md`（记录本次清理动作） |
| sdflow-spec (528行) | 零改动——已是本次要推广的目标形态 | 抽查确认已有 references/evolution-notes.md + 正文顶部资料路由小节 + 尾部指针，早于本 task 存在 |
| sdflow-devenv (464行) | 零改动 | 全文当前操作指令，无历史段落 |
| sdflow-issues (345行) | 删 1 处（migrate 节具体历史数字） | git diff: 3 行变动 |
| sdflow-upstream-watch (335行) | 删 1 处 impl-review-fix HTML 注释 | git diff: 3 行变动 |
| sdflow-init (251行) | 零改动 | 「退役 hook/文件清理」两节判定为当前活跃自愈机制的操作数据，非历史 |
| sdflow-retro (249行) | 零改动 | 全文当前行为说明 |
| sdflow-maintain (225行) | 删 1 处裸引用标签 `[impl-review-fix CF-3]` | git diff: 2 行变动 |
| sdflow-ship (193行) | 删 2 处 impl-review-fix HTML 注释 | git diff: 2 行变动 |
| sdflow-upgrade (183行) | 零改动 | 纯操作步骤，无历史段落 |

## 关键发现

考古层关键词命中确实为个位数级别的独立段落（sdflow-done 的 changelog 摘要与踩坑速记表、
sdflow-code-review/sdflow-spec-review 的历史沿革说明），符合任务简报预期「对抗镜抽查显示大文件
体量主要来自当前有效指令」。

另发现一类简报未预判的独立违规类别：**`<!-- [impl-review-fix] ... -->` 风格的 HTML 内联审校
注释**——这些是 markdown 渲染时不可见、专门记录"本轮代码审对某处措辞的修订理由"的诊断性文字，
教科书式符合 DOC-1 删除测试（只有比对版本差异的审校者才需要）。主要集中在 `sdflow-architecture`
（10 处），另在 `sdflow-ship`（2 处）、`sdflow-upstream-watch`（1 处）各有残留，`sdflow-maintain`
另有 1 处退化为裸标签（`[impl-review-fix CF-3]`，无任何解释内容）。这类内容因无实质设计依据，
直接删除而非外迁保存；其中携带真实操作语义的片段（sdflow-architecture 的 adr-new 机械化范围
说明）已并入正文对应位置，不丢信息。

`sdflow-spec` 的审计结果值得记录：它已经是本次清理要推广到其余 6 个大文件的目标形态——
`references/{delegation-protocol,degradation-ladder,evolution-notes,decision-memo-schema,
adr-and-glossary-templates}.md` 早已存在，正文顶部即有「按需资料路由（默认不加载）」小节与
末尾指针，与本次为其余大文件建立的模式完全一致。这是本次清理方案设计的直接参照。

## 测试证据

每文件清理后即验证，逐处记录：

- `sdflow-code-review` 编辑后：`hack/tests/` 374 passed, 8 skipped, 9 deselected（9 项为
  Windows 沙箱环境的预存在失败，已用 `git stash` 验证与本次改动无关，详见下方"预存在失败"节）；
  `python3 hack/sync_principles.py --check` 通过。
- `sdflow-roadmap` 编辑后：同上 hack/tests 结果；principles check 通过。
- `sdflow-spec-review` 编辑后：`hack/tests/` 374 passed, 8 skipped, 9 deselected；principles
  check 通过。
- `sdflow-done` 编辑后：`sdflow-done/tests/` 48 passed；`hack/tests/` 374 passed（同口径）；
  principles check 通过。
- `sdflow-architecture` 编辑后：`sdflow-architecture/tests/` 106 passed, 2 skipped；
  principles check 通过。
- `sdflow-issues` 编辑后：`sdflow-issues/tests/` 114 passed, 12 skipped。
- `sdflow-upstream-watch` 编辑后：`sdflow-upstream-watch/tests/` 55 passed, 5 failed——用
  `git stash` 验证 5 项失败在未改动树上同样失败（环境相关，非本次改动引入）。
- `sdflow-maintain` 编辑后：`sdflow-maintain/tests/` 49 passed。
- `sdflow-ship` 编辑后：`sdflow-ship/tests/` 360 passed, 12 skipped。
- 全程 `python3 hack/sync_principles.py --check` 每次均报「28 个投放面全部与真相源一致」，
  `sdflow:principles` 托管块自始至终未被触碰。

### 预存在失败（与本次改动无关，已用 git stash 逐一验证）

1. `hack/tests/test_check_dependencies.py::test_missing_yq_reports_cross_and_three_platform_install_commands`
   ——本机 Windows 环境 PATH 操纵模拟"yq 缺失"未生效（yq 实际仍可探测到），与 SKILL.md 内容无关。
2. `hack/tests/test_render_review_prefix.py` 8 项——Windows 沙箱内 `SDFLOW_HOME` 到全局
   workflow bundle 的路径解析在测试沙箱环境下失败（`resolve-workflow.sh` 报 `SDFLOW_HOME 非
   绝对路径`），与被测脚本消费的 SKILL.md 内容无关（脚本本身未改动）。
3. `sdflow-upstream-watch/tests/test_upstream_watch.py` 5 项——bare cache 自愈与 yq flavor
   校验相关，Windows git/yq 环境差异导致，`git stash` 验证未改动树上同样失败。

以上 14 项预存在失败均已用 `git stash && pytest ... && git stash pop` 方式确认改动前后失败
结果一致，判定为环境噪音而非本次编辑引入的回归。

## 完成核对

- [x] `audit/skill-doc1-audit.md` 骨架建立（15 节，含删/迁/留三计数 + 边界个案注记格式）
- [x] 7 个超 500 行 SKILL 逐文件审计清理 + 每文件测试绿
- [x] 8 个 ≤500 行 SKILL 审计（含零改动留档：sdflow-devenv / sdflow-init / sdflow-retro /
      sdflow-upgrade 四个零改动 + 大文件组 sdflow-implement / sdflow-spec 两个零改动，共 6 个
      零改动结论全部留档）
- [x] `sync_principles.py --check` 全仓通过（每次编辑后即验证）
- [x] 全仓 pytest 无回归（14 项预存在失败已逐一用 git stash 验证与本次改动无关）
