## Tasks

### 1. T164 · SKILL.md 路径引号修正

**Requirement**: N/A（SKILL 模板层修正，无对应 spec requirement）

- [ ] 1.1 在 `sdflow-code-review/SKILL.md` 的 async-branch marker 内（L409-495），给所有路径模板加双引号：`<f>` → `"<f>"`、`{run-dir}` → `"{run-dir}"`、`<repo-root>` → `"<repo-root>"`
- [ ] 1.2 在 `sdflow-spec-review/SKILL.md` 的 async-branch marker 内做字节对称的同样修改
- [ ] 1.3 在两份 SKILL.md 的 `mkdir -p` 行（async-branch 外）加引号：`{change_dir}` → `"{change_dir}"`
- [ ] 1.4 在两份 SKILL.md 的 fallback 行加引号：`--context-file <f>` → `--context-file "<f>"`
- [ ] 1.5 跑 `python3 hack/check_async_branch_parity.py` 验证 parity

### 2. T148 · _FANOUT_MIRRORS 枚举扩展

**Requirement**: mirrors= 合法 token 集扩展为四值

- [ ] 2.1 `sdflow-init/assets/workflow/tools/anchor_lint.py:672`：`_FANOUT_MIRRORS` 加 `"history"`
- [ ] 2.2 跑 `sdflow-init update` 刷新本仓 `openspec/workflow/tools/anchor_lint.py` 消费拷贝
- [ ] 2.3 `sdflow-code-review/SKILL.md`：mirrors= 模板 `"domain,adversarial,grounding"` → `"domain,adversarial,history"`；删借用说明段落（L244-248）；L545 示例同步
- [ ] 2.4 三份 spec 的 SHALL 条款 `{domain,adversarial,grounding}` → `{domain,adversarial,grounding,history}`：
  - `openspec/specs/host-adaptive-execution/spec.md` L157/159/161/174
  - `openspec/specs/workflow-metrics/spec.md` L37
  - `openspec/specs/spec-workflow/spec.md` L890
- [ ] 2.5 `sdflow-init/tests/test_codex_subagent_authorization.py`：更新反漂移锁期望字符串 + 删/改借用文档测试

### 3. 验证

- [ ] 3.1 `pytest sdflow-init/tests/` 全绿
- [ ] 3.2 `python3 hack/check_async_branch_parity.py` 通过
- [ ] 3.3 `openspec validate "fix-voice-quoting-and-mirror-vocab" --strict --type change` 通过

## 测试覆盖图（TG-18）

| 代码路径 | 测试类型 | 测试文件 |
|---|---|---|
| `anchor_lint._parse_mirrors()` 接受 `history` | 单元（既有 pytest 扩展） | `sdflow-init/tests/test_codex_subagent_authorization.py` |
| `anchor_lint.check_fanout_consistency()` 覆盖 `history` | 单元（既有 pytest 扩展） | 同上 |
| async-branch parity | 机械守卫 | `hack/check_async_branch_parity.py` |
| code-review SKILL mirrors= 真名 | 反漂移锁（既有测试更新） | `sdflow-init/tests/test_codex_subagent_authorization.py` |
