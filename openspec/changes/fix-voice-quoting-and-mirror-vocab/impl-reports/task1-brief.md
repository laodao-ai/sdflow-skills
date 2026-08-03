### Task 1: T164 路径引号修正

**Blocked-by:** none
**R-ID:** R1

在两份 review SKILL.md 的 async-branch marker 内和 marker 外的 `mkdir -p` 行、fallback 行，给所有路径模板加双引号，防止路径含空格时参数拆分。

async-branch 内改动 MUST 两份 SKILL 字节对称。marker 外 `mkdir -p` 行和 fallback 行各 SKILL 独立改。人工恢复命令的路径占位符（`<d>`、`<确切目录>`）同步加引号。

验收后跑 parity 守卫确认。

- [ ] code-review SKILL.md async-branch 内所有路径模板加双引号（`<f>` → `"<f>"`、`{run-dir}` → `"{run-dir}"`、`<repo-root>` → `"<repo-root>"`、`<d>` → `"<d>"`、`<确切目录>` → `"<确切目录>"`）
- [ ] spec-review SKILL.md async-branch 内做字节对称的同样修改
- [ ] 两份 SKILL.md 的 `mkdir -p` 行加引号：`{change_dir}` → `"{change_dir}"`
- [ ] 两份 SKILL.md 的 fallback 行加引号：`--context-file <f>` → `--context-file "<f>"`
- [ ] `python3 hack/check_async_branch_parity.py` 通过

