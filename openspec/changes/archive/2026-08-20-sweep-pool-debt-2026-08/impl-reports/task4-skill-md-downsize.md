# Task 4 impl-report：sdflow-spec/SKILL.md 判据下沉（T287 · DT-5）

## 结果摘要

- `sdflow-spec/SKILL.md`：17,934 → **16,930** 字符（净减 1,004 字符 / 5.6%）。
- 新增 `sdflow-spec/references/execution-protocol-details.md`（既有 references/ 同类风格），承接四段
  按 DT-5「可下沉 = 执行到该步才需要展开读的判据表/参考细节」判据挑出的内容：
  1. **0.2 档位解析**：为何四步一步不能少的假绿场景说明 + `impl-review-fix FIX-3` 引用（本体只留
     四步骤 (a)(b)(c)(d) 的 MUST 动作本身）。
  2. **B.1② FF-0 三分支判定**：全局 hook 匹配 grammar 的完整细节（正向 grammar、未判定路径处置、
     stacking deny 优先级）——本体只留三分支表 + fallback 规则。
  3. **0.3 重入探测**：`isComplete` 三态判定表 + 两条 MUST NOT 说明——本体只留探测动作与"必须问人"
     的骨架句，附指针。
  4. **C.2 强制阅读清单**：生成阶段"哪个产物先读哪些既有产物"的判据表——本体只留一句路由。
  5. **C.4 已知限制**：CLI 1.5.0 `validate --strict` 覆盖边界的诚实边界说明。
  在"按需资料路由（默认不加载）"列表补一条路由句指向该文件（不影响既有 5 条 REFERENCE_ROUTES
  的机械匹配，仅新增第 6 条，未纳入契约测试的严格 regex 校验范围）。
- 另对 **B.1（起手四步）**、**B.6/B.7（ADR/术语判据去重）**、**C.1（判 3/4 失败分支）**、
  **C.3（schema 断言/字段清单）**、**降级与诊断** 做了不改变任何 MUST/MUST NOT 语义的纯词economy
  压缩（信息零丢失，仅措辞更紧凑）——这部分不属于"下沉"，是通则④简化范畴内的安全压缩。

## 未下沉的部分（明确判定为"不可下沉"）

按 DT-5「不可下沉 = 流程骨架、铁律、fail-closed 分支」，以下内容有意保留在 SKILL.md 本体，未移动：

- **C.3 逐产物生成协议**（schema 断言字段清单、delegation 标记剥离、路径净化三条件、原子写入）——
  这是核心安全防护（confused deputy / symlink 逃逸防护），是"执行时必须遵守的 fail-closed 分支"
  本身，不是"事后才需展开的参考细节"。
- **C.1 起手核验纪要四判**及其失败分支处置——resident-contract 明确锚了四判的字面短语，且失败时
  的动作（拒绝进入生成 / 呈现旧 memo 确认）是 fail-closed 流程骨架。
- **终审**三项核验清单——resident-contract 锚了多条字面短语，且是本 skill 的最终判断层兜底逻辑。
- **B.1 起手四步**的实际动作（工作树检查 halt、FF-0 三分支表、建目录、落草稿纪要）——均为
  fail-closed 分支本身。

## 未达到的目标（如实报告）

`impl-reports/task4-brief.md` 与 `design.md` DT-5 写的目标是"本体 ≤16,000 字符（余量 ≥2,000）"，
design.md 原文明确称之为「目标」，**红线是** `test_sdflow_spec_resident_contract.py` 既有断言全绿
（含 frontmatter/结构断言）。本次交付：

- **红线（测试全绿）已达成**：10/10 通过，含硬编码 18,000 字符上限的 `test_entry_is_within_unicode_character_budget`（当前 16,930，margin 1,070）。
- **目标（≤16,000）未完全达成**：还差约 930 字符。已排查过 SKILL.md 全部 30+ 个小节的可下沉空间，
  剩余大头（C.3 1,441 字符、B.1 1,547 字符、终审 708 字符、principles 托管块 5,182 字符固定不可动）
  均被判定为流程骨架/fail-closed 分支或托管块，继续下沉/删减会实质性削弱生成安全防护或破坏
  resident-contract 锚点——按通则③"不可为凑字数砍目标范围"，未继续压缩。

如需进一步逼近 16,000，需要人工确认是否接受更激进的手段（如进一步精简 C.3 的字段清单描述、
或重新评估 principles 托管块之外还能否有结构性调整），本票范围内未做该判断，留给人拍板。

## 测试

```
/usr/bin/python3 -m pytest hack/tests/test_sdflow_spec_resident_contract.py -q
```
输出：`10 passed in 0.01s`（本票红线全绿）。按 dispatch 指令，本票测试范围限定该文件，未跑全仓 pytest。
