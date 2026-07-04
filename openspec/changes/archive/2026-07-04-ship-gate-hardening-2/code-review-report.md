# code-review 报告 — ship-gate-hardening-2

## 命中范围

- **栈**：Python + bash 工具链（gate 脚本）。清单：通用正确性/资源/错误路径 + 假✅ 防线（本项目核心）。
- **审 diff**：`9b5501b..HEAD`（设计门后实现 task1-5）= `ship_gate.py` + `workflow.md` + `SKILL.md` + 3 测试文件。
- **镜**：Step1 广审/scope-drift（历史接地镜）+ code outside-voice（codex→claude-fallback）+ 对抗镜 ×2（T32 假✅ / T34 假✅）。

<!-- sdflow:step1-broad-review v1 mode="simulated" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="命中 TG-25/23/19/22/12 均不属 HR-TG 子集{04,06,07,08,09,16,17,26}；改 gate 完成判据、非运行期爆炸/数据损坏/安全泄漏类" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="claude-fallback" reason_code="exec-error" findings="3" truncated="false" -->

> **outside-voice 降级留痕**：codex `exec` exit 1 = **用量上限**（`ERROR: You've hit your usage limit`，非 helper 故障）→ 按协议回落 fresh 只读 Claude 子代理（runner=claude-fallback，反静默不跳）。fallback 独立命中 CR-F1（与对抗镜 B 两声共识）+ CR-F2/F3。

---

## Findings（置信 ≥ 采信线，带裁决）

| # | 来源 | 严重 | finding | 裁决 |
|---|------|------|---------|------|
| **CR-F1** | 对抗B + fallback（**2声共识**） | **critical·假✅** | `_checkbox_states` 的 `in_fence` 每段独立重置、`_plan_segments` 对围栏无感知 → **未闭合围栏吞段内真实未勾项** / **围栏跨 Task 段边界** → 假✅（端到端 subprocess 复现：零 checkpoint + 未提交 plan 也能 RUN_CODE_REVIEW） | **采信→当场修 [impl-review-fix]** |
| **CR-F2** | 对抗B场景4 + fallback F2（2声） | medium·假阻 | `TASK_TITLE_RE` 对围栏无感知（与 CHECKBOX_RE 不对称）→ fenced 里的示例 `### Task N:` 被当真 task/误判重号 UNKNOWN（方向安全但卡死良构 plan） | **采信→同根因一并修** |
| CR-diag | 对抗B场景3 | medium·诊断 | `plan_has_any_checkbox`（整文）与 `checkbox_done_ids`（分段）对同一围栏缺陷判断矛盾 | **采信→统一 _parse_plan 顺带修** |
| CR-F3 | fallback | low·边界 | 命名组 `[a-z0-9][a-z0-9-]*` 不覆盖大写/下划线 change 名 → 该命名标签整体不匹配、假阴（不误归属）；openspec 强制 kebab 已兜底 | **采信→加防御性守卫测试锁定行为** |
| CR-naming | 历史镜 | low·命名 | 2 个 T34 锚测实际名多 `t34_` 前缀（vs tasks 文档预期名）；断言完全覆盖设计场景 | **裁掉（非功能性，命名习惯）** |

## 修复 / defer 台账

**自动修 [impl-review-fix]（假✅ 穿门 MUST 当场修，不 defer）**：CR-F1 + CR-F2 + CR-diag **同根因**（Task 标题与复选框未共享全文 fence 状态），一次重构统一解决：
- 新 `_parse_plan(text)`：**fence-aware 单遍解析**，Task 标题与复选框共享同一全文 `in_fence` 状态；fenced 内行对标题/复选框**均不可见**；返回 `(task_order, boxes_by_task, any_checkbox, unbalanced)`。
- **未闭合围栏（EOF 时 in_fence=True）→ `decide()` 判 UNKNOWN**（fail-safe，先于其余判据）——悬空围栏吞真实项无法可靠解析。
- `plan_task_ids` / `plan_has_duplicate_task` / `checkbox_done_ids` / `plan_has_any_checkbox` 全部改走 `_parse_plan`（口径统一，CR-diag 矛盾消失）；移除旧 `_checkbox_states` / `_plan_segments`。
- 锚测：`test_t34_unclosed_fence_unknown`（CR-F1）/ `test_t34_task_header_in_fence_not_counted`（CR-F2）/ `test_t34_fence_any_checkbox_consistent`（CR-diag）/ `test_namespace_noncanonical_ns_degrades_safe`（CR-F3 守卫）。

**voice分桶**〔M4〕：codex 采纳0/裁掉0/defer0（用量上限未产出）· **claude-fallback 采纳3[impl-review-fix：CR-F1/F2/F3]** /裁掉0/defer0。

**无 defer**：所有 finding 当场修或裁掉；CR-naming 裁掉（非功能）。

## 已裁掉区（反静默压制·可审计）

- **T32 全部方向 refuted**（对抗镜 A + 历史镜 + fallback 三重确认）：`startswith("checkpoint(")` 放宽是纯优化/修复（`TAG_RE.match` 已蕴含该前缀，旧硬前缀反是吞命名标签的真 bug）；命名归属精确 `==` 无假阳（逐一验证 `checkpoint(impl-review/spec-review/ff/design-gate/Revert...)` 全 `match=None`）；self_subject 同路径无新增面；B1/B4 回归 18 passed。**裁定：T32 实现稳。**
- **scope-check 9/9 落地、无 scope-drift、实现忠实 ADR**（历史镜）：diff 仅 7 文件均计划内；TAG_RE/归属/分段/startswith/头注释/producer 零改逐条对设计；仓级 342、ship 78 全绿，B1-B4 既有测试全在。
- **CR-naming**（历史镜，低）：t34_ 前缀命名差异，测试逻辑与断言完全覆盖设计场景，非功能缺口 → 裁掉不改。
- **T34 refuted 子项**（对抗B）：`all([])` 空列表短路（`states and all(states)` 非 bug）、` ```python ` 尾串 toggle 正确、空格变体标题三通道一致不可见、"复选框全勾但没做"属设计接受（checkpoint 主锚）。

---

## 结论

代码审**抓出并当场修掉 1 枚 critical 假✅（CR-F1，grill+spec-review 均未覆盖的围栏边界）+ 2 枚同根因中等**——正是 sdflow-code-review「独立冷视角抓生成循环放过的真问题」的实测价值。T32 经三镜确认稳、scope-check 9/9 落地、无 scope-drift。仓级 342 passed 零回归。

□ 建议进 /sdflow-done（verify → hand-off → archive → merge）

<!-- ship-gate: code-review=pass -->
