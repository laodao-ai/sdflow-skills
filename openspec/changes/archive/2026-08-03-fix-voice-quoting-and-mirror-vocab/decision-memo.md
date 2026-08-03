---
schema_version: "1"
change: fix-voice-quoting-and-mirror-vocab
branch: feat/fix-voice-quoting-and-mirror-vocab
generated_at: "2026-08-03T12:00:00Z"
decision_hash: "8899a6d37ac9932e"
---

## 承重约束

### C1 · spec 改动在本 change scope 内

T148 原文「需另开 change 走 spec-review」是在 async-outside-voice change 的语境下说的——
当时 T148 不在那个 change 的 scope 内。现在 T148 就是本 change 的目标，spec 的 SHALL 条款
扩展 `{domain,adversarial,grounding}` → `{domain,adversarial,grounding,history}` 是枚举放宽，
不改变既有条款语义，本 change 内 fold 合理。

**证据锚**：T148 条目原文 `openspec/issues/todolist/2026-07-todolist.md:309`。

### C2 · anchor_lint.py 改权威源、sdflow-init update 刷消费拷贝

`anchor_lint.py` 有两份拷贝：`sdflow-init/assets/workflow/tools/`（权威源）和
`openspec/workflow/tools/`（`sdflow-init update` 刷新的消费拷贝）。改权威源后在仓内跑
`sdflow-init update` 同步。两份当前字节一致（`diff` 验证）。

**证据锚**：`ls -la openspec/workflow/tools/anchor_lint.py` 显示非 symlink；
CLAUDE.md「tools（copy，须 sdflow-init update 刷新）」。

### C3 · mirrors= 模板在 async-branch marker 外，两份 SKILL 可独立改

`sdflow-code-review/SKILL.md` 的 `mirrors=` 模板在 242 行，async-branch marker 在 409-495 行。
二者不重叠。code-review 改 `grounding` → `history`（真名），spec-review 保持 `grounding`
（它的第三镜就是接地镜，语义正确）。不触发 parity 守卫。

**证据锚**：`grep -n 'sdflow:async-branch' sdflow-code-review/SKILL.md` → 409/495；
`grep -n 'mirrors=' sdflow-code-review/SKILL.md` → 242/545。

### C4 · T164 引号改动在 async-branch 内，两份 SKILL 必须字节对称

路径引号修正涉及的命令模板（行 436/443/452/462/467）全在 async-branch marker（409-495）内。
`hack/check_async_branch_parity.py` 机械守要求两份 SKILL 的该段字节一致。改动必须同步。

**证据锚**：两份 SKILL 的 async-branch marker 位置一致（code-review 409-495，
spec-review 405-491）。

## 拍板决策

### D1 · T164 修法 = 给路径模板加双引号

9 处改动：`<f>` → `"<f>"`、`{run-dir}` → `"{run-dir}"`、`<repo-root>` → `"<repo-root>"`、
`{change_dir}` → `"{change_dir}"`（`mkdir -p` 行）。`<T>` 和 `<site>` 不需要（受控值）。
两份 SKILL 的 async-branch 内改动字节对称。

### D2 · T148 修法 = 扩展枚举 + 改真名 + 删借用文档

1. `anchor_lint.py:672` 加 `"history"` 到 `_FANOUT_MIRRORS`（改权威源 + update 刷消费拷贝）
2. `sdflow-code-review/SKILL.md` 的 `mirrors=` 模板和说明文本：`grounding` → `history`，
   删借用说明段落
3. 三份 spec 的 SHALL 条款：`{domain,adversarial,grounding}` → `{domain,adversarial,grounding,history}`
4. `test_codex_subagent_authorization.py` 的反漂移锁和借用文档测试同步更新
