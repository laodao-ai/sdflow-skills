## Why

评审 SKILL（`sdflow-spec-review` / `sdflow-code-review`）的 outside-voice 调度段存在两个基础设施缺陷：

1. **T164 · 路径注入**：shell 命令模板中 `<f>`（context 文件）、`{run-dir}`（运行目录）、
   `<repo-root>`（仓根）三类路径模板未加双引号。模型照模板拼 Bash 命令时，路径含空格或
   shell 元字符会导致参数拆分或执行非预期命令。跨模型 voice 独立提出（async-outside-voice
   Task 5 报告 §10 第 2 条），原 change 未处理。
2. **T148 · 镜名词汇缺失**：`anchor_lint.py` 的 `_FANOUT_MIRRORS` frozenset 只有
   `{domain, adversarial, grounding}`，缺 `history`。code-review 的第三镜是历史镜而非接地镜，
   被迫借用 `grounding` token 记录——语义不精确，且 `dead-fanout-multi-mirror` 的交集计数
   漏算 `history` token（`mirrors="domain,history"` + `subagents="unavailable"` 不会被拦）。

两者改动文件高度重叠（两份 review SKILL.md），合一个 change 避免两次同文件 spec-review。

**来源**：roadmap `high-value-issues-cleanup` 阶段 P2（安全与锚一致性）。

## What Changes

### T164 · 路径引号修正（SKILL.md 模板层）

在两份 review SKILL.md 的 async 调度段（`sdflow:async-branch` marker 内）和 `mkdir -p`
命令模板中，给所有路径模板加双引号：

- `--context-file <f>` → `--context-file "<f>"`
- `> {run-dir}/<site>.rc` → `> "{run-dir}/<site>.rc"`
- `--run-dir {run-dir}` → `--run-dir "{run-dir}"`
- `--repo-root <repo-root>` → `--repo-root "<repo-root>"`
- `mkdir -p {change_dir}/.outside-voice` → `mkdir -p "{change_dir}/.outside-voice"`
- fallback 行 `--context-file <f>` → `--context-file "<f>"`

async-branch 内改动必须两份 SKILL 字节对称（parity 机械守）。

### T148 · 镜名词汇扩展

1. `sdflow-init/assets/workflow/tools/anchor_lint.py:672`：`_FANOUT_MIRRORS` 加 `"history"`
2. `sdflow-code-review/SKILL.md`：`mirrors=` 模板从 `"domain,adversarial,grounding"` 改为
   `"domain,adversarial,history"`；删借用说明段落
3. 三份 spec 的 SHALL 条款 `{domain,adversarial,grounding}` → `{domain,adversarial,grounding,history}`：
   - `openspec/specs/host-adaptive-execution/spec.md`（四处）
   - `openspec/specs/workflow-metrics/spec.md`（一处）
   - `openspec/specs/spec-workflow/spec.md`（一处）
4. `sdflow-init/tests/test_codex_subagent_authorization.py`：反漂移锁 + 借用文档测试同步更新
5. 跑 `sdflow-init update` 刷新本仓 `openspec/workflow/tools/` 消费拷贝

## Impact

- **TG-17（信任边界）**：T164 涉及 shell 命令路径注入修复
- **TG-18（测试计划）**：T148 改 anchor_lint 有现有测试需同步

## Success Metrics

1. 两份 review SKILL 的 async 调度段内所有路径模板均用双引号包裹
2. `_FANOUT_MIRRORS` 包含 `history`，code-review SKILL 的 `mirrors=` 使用真名
3. 三份 spec 的 SHALL 条款与 `_FANOUT_MIRRORS` 枚举一致
4. `pytest sdflow-init/tests/` 全绿
5. `hack/check_async_branch_parity.py` 通过

## Non-Goals

- 不改 `outside-voice.sh` 或 `outside-voice-job.py`（它们自身已正确处理引号/list 传参）
- 不改 `sdflow-spec-review/SKILL.md` 的 `mirrors=` 模板（它的第三镜就是接地镜，`grounding` 语义正确）
- 不改 retro 管线（它只读 `lens-metric` 不读 `fanout-capability`，不受影响）

## Compliance

N/A
