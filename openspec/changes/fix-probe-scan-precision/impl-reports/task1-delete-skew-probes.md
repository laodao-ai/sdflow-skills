# Task 1 实现报告：删除两个评审 SKILL 的 skew 探测段

## 范围

严格对齐 `tasks.md` 第 1 节（Blocked-by: none）。只改：

- `sdflow-code-review/SKILL.md`
- `sdflow-spec-review/SKILL.md`
- `hack/tests/test_async_branch_parity.py`

未触碰 task 2–7（resolver 收缩、`copy_bundle` 停铺、告警语义、`ship_gate` 腿退役、
本仓死件清理、全链路验证）——那些是后续票。

## 改动内容（对齐 tasks.md 1.1–1.6）

1. **1.1/1.2 删除 skew 探测整段**
   - `sdflow-code-review/SKILL.md`：删除原「第零步」列表项 5（四条信号版 skew 探测），
     原列表项 6「能力探针」顺延为列表项 5。
   - `sdflow-spec-review/SKILL.md`：删除原「第零步」列表项 4（两条信号版 skew 探测）——
     该项是本列表的最后一项，删除后无需顺延（下一个结构是 `## 第一步` 标题，非列表项）。

2. **1.3 悬空指代清理**（档位解析步下方的括注段）
   - 原文引用「同下方『skew 探测』的 fail-loud 精神——三处均为…」，随探测段删除该指代
     对象消失。两文件同改为：「空值/unknown 分家同样遵循 fail-loud 精神——均为『落任何
     v2 锚 / fan-out / 调 emitter 之前』的硬停关口」——去掉对已删段的具名引用和不再成立
     的「三处」计数，保留对「规则根解析」预检与能力探针的既有引用。
   - 原 tasks 描述的「能力探针步『MUST 排在 skew 探测之后』时序理由」文字在探测段自身
     内部（`🔴 本步 MUST 排在下一项「能力探针」之前…`），随整段删除一并消失，未单独处置
     （与 1.3 的说明一致）。

3. **1.4 exit 2 降级分支保持不变**——`git diff` 核对，两文件「第零步」第 3 项（规则根
   解析，含 `退出码 2 → 显式降级...`）与「宿主/档位解析」第 4 项内部的 fail-loud 分支
   逐字未动（diff 中不含这些行的改动）。

4. **1.5 验收 grep**：`grep -n "skew 探测\|lens-metric-enums\|scope-audit:\|_MIRRORS_LEGAL" sdflow-code-review/SKILL.md sdflow-spec-review/SKILL.md`
   命中数各 1（均为 `anchor_lint` 自检段对 `lens-metric-enums` 契约块的合法引用，
   `sdflow-code-review/SKILL.md:419`、`sdflow-spec-review/SKILL.md:270`）——`skew 探测`
   / `scope-audit:` / `_MIRRORS_LEGAL` 三个随探测段删除的词全部归零。

5. **1.6 「两条分发链」→ 单链表述**（`sdflow:async-branch` marker 区间内，两文件同改，
   逐字节相同）：
   - 旧文案描述两条链——全局 helper/SKILL 走 `bash setup.sh`；消费仓
     `openspec/workflow/tools/` 走 `sdflow-init update`——并强调「跑了其中一条不等于
     另一条也刷新了」。
   - 新文案只保留 `bash setup.sh` 这一条链（刷新 `~/.sdflow/hack/` 的 capability
     manifest 同代快照），去掉对 `openspec/workflow/tools/` / `sdflow-init update`
     链的提及；`manifest skew` 的修法「回运行 checkout 重跑 `bash setup.sh`」原样保留。
   - `hack/tests/test_async_branch_parity.py::test_usage_notes_cover_version_policy_preview_and_platform_boundary`
     同批改写：断言从 `"setup.sh" in seg and "sdflow-init update" in seg` 改为
     `"setup.sh" in seg and "manifest skew" in seg` + 新增反向断言
     `"sdflow-init update" not in seg`（防止旧词残留被漏改）。docstring 同步更新说明。

## TDD 记录

- **Red**：先改测试断言（新增 `"sdflow-init update" not in seg` 反向断言 + 关键词替换），
  在未改 SKILL.md 前跑：
  `assert "sdflow-init update" not in seg` 在 `sdflow-spec-review/SKILL.md` 段上失败
  （`AssertionError: sdflow-spec-review/SKILL.md`）——确认测试先红。
- **Green**：完成 SKILL.md 两处编辑后，`hack/tests/test_async_branch_parity.py` 41 项
  全绿（含逐字节相同的 parity 门 `test_repo_sites_are_byte_identical`）。

## 测试结果

```
/usr/bin/python3 -m pytest hack/tests/test_async_branch_parity.py -v
41 passed

/usr/bin/python3 -m pytest hack/tests/ -q
380 passed in 28.90s
```

未额外跑全仓 pytest——本票 Blocked-by: none，且改动只涉及两份 SKILL.md（无脚本消费方
在 `sdflow-code-review/`、`sdflow-spec-review/` 下）与 `hack/tests/` 内的一个测试文件，
`hack/tests/` 全量绿已覆盖唯一消费方（`check_async_branch_parity.py` 的 pytest 套件）。
按测试范围纪律（单元 + 本票 Blocked-by 链上模块）不跑与本票无依赖关系的其余套件
（`sdflow-init/tests/`、`sdflow-ship/tests/` 等针对 task 2–5 才会变化）。

## 验收清单核对（对齐 tasks.md 1.1–1.6 + brief）

- [x] 删除 `sdflow-code-review/SKILL.md` skew 探测整段，步序号顺延（6→5）
- [x] 删除 `sdflow-spec-review/SKILL.md` skew 探测整段（列表末项，无需顺延）
- [x] 清理档位解析步悬空指代（两文件同改，不再引用「skew 探测」与「三处」计数）
- [x] 逐字比对确认两文件 `exit 2` 降级分支未被误改
- [x] `sdflow:async-branch` 区间内「两条分发链」→ 单链表述，两文件逐字节同改
- [x] `hack/tests/test_async_branch_parity.py` 断言同批改写（正向 + 反向）
- [x] 验收 grep：命中数各文件恰为 1

## 已知诚实边界（沿用 tasks.md 「测试覆盖图」的既有登记，非本票新增）

- SKILL.md 是指令资产，「是否照做」由执行方自报——本票验证止于 grep 文本级 + parity
  测试的字节级一致性，不构成行为级证明（tasks.md 已登记，非本票遗留缺口）。

## 未做事项

无。Task 1 的全部 6 个子任务（1.1–1.6）已完成，验收 grep 与既有测试套件均通过。
