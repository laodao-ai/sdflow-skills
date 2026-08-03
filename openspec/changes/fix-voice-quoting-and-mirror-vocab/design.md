## Overview

两项评审基础设施修正：T164（shell 命令模板路径引号）+ T148（`_FANOUT_MIRRORS` 镜名词汇扩展）。
改动文件高度重叠，合一个 change。

## Decisions

见 [decision-memo.md](./decision-memo.md)。

## T164 · 路径引号修正

### 问题

两份 review SKILL.md 的 outside-voice 调度段（`sdflow:async-branch` marker 内，行 409-495）
包含 shell 命令模板，路径模板 `<f>`、`{run-dir}`、`<repo-root>` 未加双引号。模型照模板拼
Bash 命令时，路径含空格或 shell 元字符会导致参数拆分。

脚本自身安全：`outside-voice.sh` 内部 `"$ctx"` 带引号，`outside-voice-job.py` 用
`subprocess` list 传参 + `shlex.join()`。漏洞仅在 SKILL.md 指令模板层。

### 修改清单

async-branch marker 内（两份 SKILL 字节对称，parity 守卫）：

| 原模板 | 修正后 | 行号（code-review / spec-review） |
|---|---|---|
| `--context-file <f>` | `--context-file "<f>"` | 436,496 / 432,492 |
| `> {run-dir}/<site>.rc` | `> "{run-dir}/<site>.rc"` | 436 / 432 |
| `--run-dir {run-dir}` | `--run-dir "{run-dir}"` | 443,452,462,467 / 439,448,458,463 |
| `--repo-root <repo-root>` | `--repo-root "<repo-root>"` | 443 / 439 |

async-branch marker 外（各 SKILL 独立，不受 parity 约束）：

| 原模板 | 修正后 | 行号（code-review / spec-review） |
|---|---|---|
| `mkdir -p {change_dir}/.outside-voice` | `mkdir -p "{change_dir}/.outside-voice"` | 396 / 392 |

### 安全分析（TG-17）

**攻击面**：路径由 `mktemp -d` 输出（安全）+ change 名（用户输入，`openspec new change` 可能
接受含空格的名称）+ 仓根路径（macOS 允许 `/Users/First Last/`）。当前系统路径无空格，但
按通则③不拿现状反驳目标——目标态 producer（任意用户在任意机器跑评审）会产出含空格路径。

**修法影响**：纯模板层，只加引号。`<T>` 和 `<site>` 不需要（clamped integer / controlled enum）。

## T148 · 镜名词汇扩展

### 问题

`anchor_lint.py:672` 的 `_FANOUT_MIRRORS = frozenset({"domain", "adversarial", "grounding"})` 缺
`history`。code-review 的第三镜是历史镜（非接地镜），被迫借用 `grounding` token，导致：

1. 语义不精确——`mirrors="domain,adversarial,grounding"` 中 `grounding` 实际代表 `history`
2. `dead-fanout-multi-mirror` 检查漏洞——`mirrors="domain,history"` + `subagents="unavailable"`
   的交集只算出 `{domain}`（`history` 不在集合中被忽略），计数 ≤1，不触发报错

### 修改清单

```
sdflow-init/assets/workflow/tools/anchor_lint.py
├── L672: _FANOUT_MIRRORS 加 "history"
└── 消费拷贝由 sdflow-init update 刷新

sdflow-code-review/SKILL.md
├── L242: mirrors= 模板 "domain,adversarial,grounding" → "domain,adversarial,history"
├── L244-248: 删借用说明段落
└── L545: mirrors= 示例同步更新

openspec/specs/host-adaptive-execution/spec.md
├── L157: 锚模板示例加 history
├── L159: 取值文法 {d,a,g} → {d,a,g,h}
├── L161: 去重计数集 {d,a,g} → {d,a,g,h}
└── L174: Scenario 去重计数集同步

openspec/specs/workflow-metrics/spec.md
└── L37: 去重计数集 {d,a,g} → {d,a,g,h}

openspec/specs/spec-workflow/spec.md
└── L890: 完整性集 (d/a/g) → (d/a/g/h)

sdflow-init/tests/test_codex_subagent_authorization.py
├── 反漂移锁测试：更新期望字符串
└── 借用文档测试：删除或改为验证真名
```

### 不改的文件

- `sdflow-spec-review/SKILL.md` 的 `mirrors=` 模板——它的第三镜是接地镜，`grounding` 语义正确
- `sdflow-retro/` 的 retro 管线——只读 `lens-metric` 锚（`LENS_ENUM` 已含 `history`），
  不读 `fanout-capability` 锚
- `outside-voice.sh` / `outside-voice-job.py`——它们自身引号处理正确

### 依赖图

```
anchor_lint.py (_FANOUT_MIRRORS)
  ↓ 枚举扩展
code-review SKILL.md (mirrors= 模板)    spec SHALL 条款 (×6 处)
  ↓ 真名替换                              ↓ 枚举同步
test_codex_subagent_authorization.py     sdflow-init update (消费拷贝)
```

## Compliance

- **parity 守卫**：async-branch 内改动两份 SKILL 字节对称
- **anchor_lint.py 两份拷贝**：改权威源 `sdflow-init/assets/workflow/tools/`，
  跑 `sdflow-init update` 刷消费拷贝 `openspec/workflow/tools/`
- **DOC-1**：正文只写最终态，不保留借用说明的演进叙事
