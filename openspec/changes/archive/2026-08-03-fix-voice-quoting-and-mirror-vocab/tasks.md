## Tasks

### 1. T164 · SKILL.md 路径引号修正

**Requirement**: N/A（SKILL 模板层修正，无对应 spec requirement）

- [x] 1.1 在 `sdflow-code-review/SKILL.md` 的 async-branch marker 内（L409-495），给所有路径模板加双引号：`<f>` → `"<f>"`、`{run-dir}` → `"{run-dir}"`、`<repo-root>` → `"<repo-root>"`；另含人工恢复命令的 `<d>` → `"<d>"`、`<确切目录>` → `"<确切目录>"` [spec-review-amendment S6]
- [x] 1.2 在 `sdflow-spec-review/SKILL.md` 的 async-branch marker 内做字节对称的同样修改
- [x] 1.3 在两份 SKILL.md 的 `mkdir -p` 行（async-branch 外）加引号：`{change_dir}` → `"{change_dir}"`
- [x] 1.4 在两份 SKILL.md 的 fallback 行加引号：`--context-file <f>` → `--context-file "<f>"`
- [x] 1.5 跑 `python3 hack/check_async_branch_parity.py` 验证 parity

### 2. T148 · _FANOUT_MIRRORS 枚举扩展

**Requirement**: mirrors= 合法 token 集扩展为四值

- [x] 2.1 `sdflow-init/assets/workflow/tools/anchor_lint.py:672`：`_FANOUT_MIRRORS` 加 `"history"`；同步 L702 `check_fanout_consistency()` docstring 的硬编码枚举 [spec-review-amendment S9]
- [x] 2.2 跑 `sdflow-init update` 刷新本仓 `openspec/workflow/tools/anchor_lint.py` 消费拷贝
- [x] 2.3 `sdflow-code-review/SKILL.md`：mirrors= 模板 `"domain,adversarial,grounding"` → `"domain,adversarial,history"`；重写 L244-248（保留 L244 开头的 MUST 规范语句 + token 集改为 `{domain,adversarial,history}`，删除 L246-248 的借用叙事）；L545 示例同步 [spec-review-amendment S3]
- [x] 2.4 三份 spec 直接改主 spec 的 SHALL 条款 `{domain,adversarial,grounding}` → `{domain,adversarial,grounding,history}`（非经 delta → archive，理由：枚举值放宽不改变既有条款语义，三份一致走直接改避免 delta 必须携带全部现有 Scenario 的重量）[spec-review-amendment S1/Q1]：
  - `openspec/specs/host-adaptive-execution/spec.md` L157/159/161/174
  - `openspec/specs/workflow-metrics/spec.md` L37
  - `openspec/specs/spec-workflow/spec.md` L890
- [x] 2.5 `sdflow-init/tests/test_codex_subagent_authorization.py`：拆分反漂移锁测试的共享循环为按文件区分预期（spec-review 期望 `grounding`、code-review 期望 `history`）；重写借用文档测试为验证真名（断言 `mirrors=` 字面含 `history`、且旧借用措辞不再出现）[spec-review-amendment S5/S8]
- [x] 2.6 `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py`：补 `history` token 功能测试——`_parse_mirrors("history")` 接受 + `mirrors="domain,history"` + `subagents="unavailable"` 触发 `dead-fanout-multi-mirror` [spec-review-amendment S2]

### 3. 验证

- [x] 3.1 `pytest sdflow-init/` 全绿（含 `sdflow-init/assets/workflow/tools/tests/`）[spec-review-amendment S2]
- [x] 3.2 `python3 hack/check_async_branch_parity.py` 通过
- [x] 3.3 `openspec validate "fix-voice-quoting-and-mirror-vocab" --strict --type change` 通过

## 测试覆盖图（TG-18）[spec-review-amendment S2]

| 代码路径 | 测试类型 | 测试文件 |
|---|---|---|
| `anchor_lint._parse_mirrors()` 接受 `history` | 功能单测（新增） | `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py` |
| `anchor_lint.check_fanout_consistency()` 覆盖 `history`（dead-fanout-multi-mirror） | 功能单测（新增） | 同上 |
| async-branch parity | 机械守卫 | `hack/check_async_branch_parity.py` |
| code-review SKILL mirrors= 真名 | 反漂移锁（既有测试拆分更新） | `sdflow-init/tests/test_codex_subagent_authorization.py` |
| SKILL.md 文档 token ⊆ `_FANOUT_MIRRORS` | 反漂移锁（按文件区分期望） | 同上 |
