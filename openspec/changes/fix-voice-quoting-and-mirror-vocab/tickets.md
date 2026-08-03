---
impl-pipeline: tickets
---

## Global Constraints

- async-branch marker 内（`sdflow:async-branch:start` 到 `end`）的改动两份 review SKILL.md MUST 字节对称（`hack/check_async_branch_parity.py` 机械守）
- `anchor_lint.py` 改权威源 `sdflow-init/assets/workflow/tools/`，然后跑 `sdflow-init update` 刷消费拷贝 `openspec/workflow/tools/`
- `sdflow-spec-review/SKILL.md` 的 `mirrors=` 模板保持 `grounding`（它的第三镜就是接地镜，语义正确），不改
- 三份 spec 走直接改主 spec（非 delta → archive），理由见 `specs/host-adaptive-execution/spec.md` [spec-review-amendment S1/Q1]
- 双引号只防空格导致的参数拆分与 glob 展开，不防 `$(...)` 命令替换——此残留已在 design.md 显式声明为可接受风险 [spec-review-amendment S7]
- DOC-1：正文只写最终态，不保留借用说明的演进叙事
- task 2.3 重写 L244-248：保留 MUST 规范语句，token 集改为 `{domain,adversarial,history}`，删除借用叙事 [spec-review-amendment S3]

### Task 1: T164 路径引号修正

**Blocked-by:** none
**R-ID:** R1

在两份 review SKILL.md 的 async-branch marker 内和 marker 外的 `mkdir -p` 行、fallback 行，给所有路径模板加双引号，防止路径含空格时参数拆分。

async-branch 内改动 MUST 两份 SKILL 字节对称。marker 外 `mkdir -p` 行和 fallback 行各 SKILL 独立改。人工恢复命令的路径占位符（`<d>`、`<确切目录>`）同步加引号。

验收后跑 parity 守卫确认。

- [x] code-review SKILL.md async-branch 内所有路径模板加双引号（`<f>` → `"<f>"`、`{run-dir}` → `"{run-dir}"`、`<repo-root>` → `"<repo-root>"`、`<d>` → `"<d>"`、`<确切目录>` → `"<确切目录>"`）
- [x] spec-review SKILL.md async-branch 内做字节对称的同样修改
- [x] 两份 SKILL.md 的 `mkdir -p` 行加引号：`{change_dir}` → `"{change_dir}"`
- [x] 两份 SKILL.md 的 fallback 行加引号：`--context-file <f>` → `--context-file "<f>"`
- [x] `python3 hack/check_async_branch_parity.py` 通过

### Task 2: anchor_lint 枚举扩展 + 消费拷贝刷新

**Blocked-by:** none
**R-ID:** R2

`_FANOUT_MIRRORS` frozenset 加入 `"history"` token，同步 docstring 硬编码枚举，然后跑 `sdflow-init update` 刷新本仓消费拷贝。

- [x] `anchor_lint.py:672` `_FANOUT_MIRRORS` 加 `"history"`
- [x] `check_fanout_consistency()` docstring 的硬编码枚举同步更新
- [x] 跑 `sdflow-init update` 刷新 `openspec/workflow/tools/anchor_lint.py`
- [x] `_parse_mirrors("history")` 返回合法结果（非 unknown-token）
- [x] 补 `test_anchor_lint.py` 功能测试：`history` token 接受 + `mirrors="domain,history"` 加 `subagents="unavailable"` 触发 `dead-fanout-multi-mirror`

### Task 3: code-review SKILL 真名替换 + spec SHALL 条款 + 反漂移锁测试

**Blocked-by:** 2
**R-ID:** R2, R3

把 code-review SKILL.md 的 `mirrors=` 模板从借用 `grounding` 改为真名 `history`；重写 L244-248（保留 MUST 规范语句，token 集改为 `{domain,adversarial,history}`，删除借用叙事）；L545 示例同步。

三份主 spec 的 SHALL 条款枚举从 `{domain,adversarial,grounding}` 扩展到 `{domain,adversarial,grounding,history}`。

更新反漂移锁测试：拆分共享循环为按文件区分预期（spec-review 期望 `grounding`、code-review 期望 `history`）；重写借用文档测试为验证真名行为。

- [ ] code-review SKILL.md `mirrors=` 模板改为 `"domain,adversarial,history"`
- [ ] L244-248 重写：保留 MUST 规范语句 + token 集 `{domain,adversarial,history}` + 删借用叙事
- [ ] L545 示例 `mirrors=` 同步更新
- [ ] `openspec/specs/host-adaptive-execution/spec.md` 四处 SHALL 条款扩展
- [ ] `openspec/specs/workflow-metrics/spec.md` 一处扩展
- [ ] `openspec/specs/spec-workflow/spec.md` 一处扩展
- [ ] 反漂移锁测试拆分：spec-review 期望 `grounding`、code-review 期望 `history`
- [ ] 借用文档测试改为验证真名（断言 `mirrors=` 含 `history`、旧借用措辞不再出现）

### Task 4: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落 `impl-reports/task4-verify.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

- [ ] 单元测试证据齐全并通过
- [ ] parity 守卫证据齐全并通过
- [ ] `openspec validate` 证据齐全并通过（或记「未覆盖」+ 判定依据）
