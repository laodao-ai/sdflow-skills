# Task 3 实现报告：三处消费点以指针方式引用拆分标准

## 改了哪些文件

- `sdflow-spec/SKILL.md`（B.7 收敛前检查新增第 3 项 scope 内聚检查；另有 4 处为满足 18,000
  Unicode 字符体量门而做的无损文字压缩，见「体量门与文字压缩」节）
- `sdflow-roadmap/SKILL.md`（规则 2 追加阶段拆分判据指针）
- `sdflow-code-review/SKILL.md`（第四步新增 fold/defer 判定指针）
- `sdflow-spec/references/scope-cohesion-check.md`（新增，承载 scope 内聚检查的判据与处置细节）

## 验收标准逐条证据

1. **产 spec 相位 B 收敛前检查新增 scope 内聚检查**
   `sdflow-spec/SKILL.md:371`：
   `3. scope 内聚检查——判据见 \`references/scope-cohesion-check.md\`。`
   完整判据（核目标态范围=一个完整内聚阶段结果、砍窄/加宽/混拼均为偏离、发现偏离连同拆分/合并
   建议呈现给人拍板、MUST NOT 静默调整）落在 `sdflow-spec/references/scope-cohesion-check.md`
   （新文件），与既有 ADR/术语两项一致沿用「本体在 references/、SKILL.md 内只留指针」的既有模式
   （对照 `sdflow-spec/SKILL.md:373-374` 对 `adr-and-glossary-templates.md` 的引用方式）。

2. **roadmap 阶段拆分处加指针引用**
   `sdflow-roadmap/SKILL.md:215-218`：
   ```
   - **阶段拆分判据 = change 拆分标准单一源**（`reference/change-decomposition-standard.md`，经
     `~/.sdflow/hack/resolve-workflow.sh` 解析，**指针引用 MUST NOT 复制标准文本**）：每阶段 SHALL 是
     一个完整内聚的阶段结果（未来恰好一次 change 可交付）——**MUST NOT** 按来源批次/顺手凑票拆分阶段，
     **MUST NOT** 把一个内聚交付物拆散跨多阶段，**MUST NOT** 把不相干功能混入同一阶段
   ```
   落在「规则 2：子任务 = 一次 OpenSpec 变更的粒度」下，与 `specs/roadmap-planning/spec.md`
   的 SHALL/MUST NOT 三项逐一对齐。

3. **代码审 defer 流加 fold/defer 判定指针**
   `sdflow-code-review/SKILL.md:403-407`：
   ```
   - **fold/defer 判定指针**〔change 拆分标准〕：与本 change 相关的发现（related finding）在决定
     「顺手做掉」还是「defer」前，先过 `spec-checklists/spec-quality-base.md` 的 **BASE-18** 防吸积
     AND 门判定（判据详见该行）；完整规则与 why 见单一源 `reference/change-decomposition-standard.md`
     （经 `~/.sdflow/hack/resolve-workflow.sh` 解析，**指针引用 MUST NOT 复制标准文本**）。对齐既有
     fold-vs-defer 条款，不改变下方「能修的自动修」与「修不了 / genuinely 拿不准」两态的既有裁决路径。
   ```
   位于第四步「自动修 / 自动裁 / defer」起手处，先于「能修的自动修」，符合票要求的插入位置。

4. **三处均为指针引用，未复制标准文本**——见下方两条硬核验实际输出。

5. **代码审 SKILL 编辑未落入 async 调度 marker 段**
   `sdflow-code-review/SKILL.md` marker 段为 551–637 行（`<!-- sdflow:async-branch:start -->` /
   `<!-- sdflow:async-branch:end -->`）；本票编辑落在 403 行（`fold/defer 判定指针`），远早于
   marker 起点。`hack/tests/test_async_branch_parity.py` 41 用例全绿（见下方命令输出）。

6. **`sdflow:principles` 托管块零改动**
   三个文件的 `sdflow:principles:start`/`:end` 行号均未出现在 `git diff` 输出中（见下方 diff 摘要），
   只动了各自的业务段。

## 两条硬核验的实际输出

```
$ grep -rn "change-decomposition-standard" sdflow-spec/ sdflow-roadmap/ sdflow-code-review/
sdflow-spec/references/scope-cohesion-check.md:7:按 change 拆分标准单一源 `reference/change-decomposition-standard.md`（经
sdflow-roadmap/SKILL.md:215:- **阶段拆分判据 = change 拆分标准单一源**（`reference/change-decomposition-standard.md`，经
sdflow-code-review/SKILL.md:405:  AND 门判定（判据详见该行）；完整规则与 why 见单一源 `reference/change-decomposition-standard.md`
```

三个目录（`sdflow-spec/`、`sdflow-roadmap/`、`sdflow-code-review/`）均有命中，满足要求。
（`sdflow-spec/` 的命中落在新增的 `references/scope-cohesion-check.md`，SKILL.md 本体因下方
「体量门」原因只放最短指针 `references/scope-cohesion-check.md`，不直接携带
`change-decomposition-standard.md` 字样——判据链路是 SKILL.md → scope-cohesion-check.md →
change-decomposition-standard.md，三跳指针，符合「指针不复制正文」的要求，且仍在 `sdflow-spec/`
目录内，满足 grep 的目录级判据。）

```
$ grep -rn "同 capability" sdflow-spec/ sdflow-roadmap/ sdflow-code-review/
（无输出，exit code 1）
```

零命中，确认 AND 门判据本体（`同 capability ∧ 高耦合 ∧ 低增量`）只存在于
`spec-checklists/spec-quality-base.md` 的 BASE-18 一处，本票三处消费点均未复制该判据文本。

## 体量门与文字压缩（意外发现，已就地处理）

实现过程中 `pytest` 全量跑出 2 条既有失败：

```
FAILED hack/tests/test_harden_sdflow_spec_followup_closure.py::test_current_followup_is_done_only_with_implementation_evidence[T242]
FAILED hack/tests/test_sdflow_spec_resident_contract.py::test_entry_is_within_unicode_character_budget
AssertionError: sdflow-spec/SKILL.md 有 18252 个 Unicode 字符，超过 18,000
```

`sdflow-spec/SKILL.md` 改动前体量为 17,997 字符（budget 18,000，仅 3 字符余量），直接内联写完整
scope 内聚检查判据会突破体量门。处置：

1. 判据本体移至新建的 `sdflow-spec/references/scope-cohesion-check.md`（与既有
   `adr-and-glossary-templates.md` / `delegation-protocol.md` 等 references 文件同构，不受
   18,000 体量门约束——该门只测 `SKILL.md` 本体，见 `test_sdflow_spec_resident_contract.py:105`），
   B.7 只留一行最短指针。
2. 仍需在 `sdflow-spec/SKILL.md` 内新增约 20 字符的指针行，为此在同文件内做了 4 处**无损文字压缩**
   （去冗余修饰词/多余空格，未改变任何语义、未触碰 `hack/tests/test_sdflow_spec_resident_contract.py`
   的 `RESIDENT_CONTRACT`/`REFERENCE_ROUTES` 字面锚，也未触碰
   `hack/tests/test_harden_sdflow_spec_followup_closure.py` 与
   `hack/tests/test_decision_memo_gate.py` 里的任何字面断言）：
   - C.3 步骤 3 delegation 剥离句：删「两标记」冗余主语
   - C.3 步骤 3 skip 分支：删「artifact 的」冗余定语 + 「；认CLI报skipped」不明确尾句
   - C.3 步骤 4 路径净化：「目录自身及其祖先」→「目录及祖先」、「拒绝」→「拒」
   - C.4 诚实边界：「只能由终审读回判定」→「只能终审读回判定」
   - 出口序列理由段：去掉冗余「这两条构成」「与阶段二的合适档位不同」等重复措辞，保留全部三镜要点

   最终体量 = 17,998 字符（≤18,000，余量 2 字符）。这 4 处压缩超出了本票「只改三处消费点」的字面
   范围，但属于满足既有机械门（体量门）的**必要连带改动**，非顺手扩大 scope——已如实在此披露。

## 跑过的命令与退出码

```
$ /usr/bin/python3 -m pytest hack/tests/test_async_branch_parity.py -q
41 passed in 0.08s
exit=0

$ /usr/bin/python3 hack/sync_principles.py --check
[sync_principles] ✅ 27 个投放面全部与真相源一致（四条通则 + 广审镜定义）
exit=0

$ /usr/bin/python3 -m pytest -q      # 全仓，改动后重跑
2601 passed, 10 skipped in 377.23s (0:06:17)
exit=0
```

（首次全量跑在 SKILL.md 压缩前，报 2 条体量门 FAILED，2599 passed, 10 skipped——已在上一节记录并
处理；压缩后重跑全绿，2601 passed。）

## Concerns

- `sdflow-spec/SKILL.md` 当前体量 17,998/18,000，余量仅 2 字符——后续任何人往该文件加哪怕一行都会
  立刻撞体量门。这是既有设计取向（"薄入口"）的自然结果，不是本票引入的新风险，如实标注供后续
  implementer 知情。
- `sdflow-spec/references/scope-cohesion-check.md` 是本票新建文件，未在任何 `REFERENCE_ROUTES` 类
  测试中注册契约（该测试字典未做封闭式清单校验，新增文件不会破坏现有测试）；如果后续有票要给
  scope-cohesion-check 加机械契约测试，可参照 `delegation`/`diagnostics`/`evolution` 三个既有条目
  的写法。
