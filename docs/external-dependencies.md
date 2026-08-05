# 外部依赖参考

本文档列出 sdflow-skills 仓库的所有外部依赖——运行本仓库的 skill 需要什么环境、什么工具、什么三方 skill。

---

## 1. 系统运行环境

### 必须

| 依赖 | 最低版本 | 用途 | 出处 |
|------|---------|------|------|
| **bash** | 4.x | 全仓脚本运行（数组、`[[ ]]` 等特性） | `setup.sh` 全文、`outside-voice.sh` 等 |
| **Python** | 3.7+ | 数据类 skill 脚本（`ship_gate.py`、`retro_report.py` 等） | `setup.sh:536-547` 检测逻辑 |
| **git** | — | 版本报告、freshness 检测、分支管理、checkpoint 提交 | `setup.sh:588-593`、各 SKILL.md |
| **POSIX 工具链** | — | `ln`/`cp`/`rm`/`mkdir`/`find`/`grep`/`sed`/`wc`/`mktemp` 等 | `setup.sh` 全文 |

### 有降级路径

| 依赖 | 用途 | 缺失时行为 | 出处 |
|------|------|-----------|------|
| **timeout** / **gtimeout** | 跨模型 voice 超时守卫 | voice 通道 fail-closed 降级为同族 fallback 子代理 | `outside-voice.sh:509-510` |
| **yq** (mikefarah/yq ≥ 4.16.0) | YAML frontmatter 读写（`--front-matter` 选项） | `setup.sh` 报警 + 部分 gate 路径不可用 | `setup.sh:597-616` |

> **注意**：macOS 自带的 `timeout` 不存在，需 `brew install coreutils` 获取 `gtimeout`；yq 有两个同名包（mikefarah/yq vs kislyuk/yq），必须是前者。

---

## 2. Python 依赖

### 生产脚本

**零三方包依赖**。所有生产 Python 脚本仅使用标准库（`json`、`os`、`sys`、`subprocess`、`pathlib`、`re`、`hashlib`、`textwrap`、`argparse`、`collections`、`datetime` 等）。

`ship_gate.py` 甚至有显式守卫禁止引入三方包：

```python
# ship_gate.py:198 — MUST NOT import yaml
```

### 开发/测试

| 依赖 | 用途 | 出处 |
|------|------|------|
| **pytest** | 全仓测试框架 | `conftest.py:37`、各 `tests/` 目录 |

---

## 3. npm 全局包

| 依赖 | 必要性 | 用途 | 出处 |
|------|--------|------|------|
| **@fission-ai/openspec** | 可选 | change 生命周期管理（`openspec new`/`archive`/`instructions`） | `setup.sh:618-623`、`CLAUDE.md:193`、各 opsx 命令 |

`setup.sh` 检测到缺失时仅输出提示，不阻断安装。部分 skill（`sdflow-spec`、`sdflow-done`）的 change 管理功能依赖此包；纯编排类 skill 不需要。

---

## 4. CLI 工具依赖（跨模型 voice）

| 依赖 | 必要性 | 用途 | 出处 |
|------|--------|------|------|
| **claude** CLI | 有降级路径 | Codex 宿主下的跨模型 voice runner | `outside-voice.sh:18`、`resolve-models.sh:10` |
| **codex** CLI | 有降级路径 | Claude 宿主下的跨模型 voice runner | 同上 |

跨模型 voice 机制：当前宿主是 Claude 时调 `codex` 做第二意见，反之亦然。两者均缺失时降级为同族 fallback 子代理（`runner==host`），voice 层 efficacy 归零但 skill 不中断。

---

## 5. 三方 Skill 依赖

### 评审流程依赖（gstack 系列）

| Skill | 用途 | 调用处 | 缺失时行为 |
|-------|------|--------|-----------|
| **gstack `/review`** | 代码审的 scope-drift + 完成度审计（Step1） | `sdflow-code-review/SKILL.md:206-209` | 显式降级为子代理模拟 + 标注 `mode="simulated"` |
| **gstack `/autoplan`** | 设计审的广审层（CEO/Eng/Design 三连） | `sdflow-spec-review/SKILL.md`、`sdflow-roadmap/SKILL.md:426` | 显式提示 + 留「未审待恢复」痕迹 |
| **`/plan-eng-review`** | roadmap 的技术评审（默认档） | `sdflow-roadmap/SKILL.md:425` | 同上 |

### Wayfinder 依赖（仅 sdflow-roadmap 使用）

| Skill | 用途 | 调用处 | 缺失时行为 |
|-------|------|--------|-----------|
| **`/grilling`** | wayfinder 票内的计划拷问 | `sdflow-roadmap/SKILL.md:306` | 降级为普通对话式讨论 |
| **`/domain-modeling`** | wayfinder 票内的术语/ADR 建模 | `sdflow-roadmap/SKILL.md:312` | 同上 |

> `/grill-with-docs` 已被 `sdflow-spec` 内置取代（`sdflow-spec/SKILL.md:10`），不再是外部依赖。
>
> 所有三方 skill 都设计了显式降级路径——缺失时报告但不中断工作流。

---

## 6. Claude Code / Codex 运行时依赖

| 依赖 | 用途 | 出处 |
|------|------|------|
| **Claude Code** harness | Skill tool、Agent tool、Bash tool 等核心机制 | 全仓 SKILL.md |
| **子代理能力** (Agent tool) | 评审多镜 fan-out、实现管线派发 | `sdflow-spec-review`、`sdflow-code-review`、`sdflow-implement` |
| **model-tiers 机队** | 按步骤性质选模型（强档/中档/弱档） | `resolve-models.sh`、各 SKILL.md 的第零步 |

Codex 宿主额外要求：
- 项目指令文件显式授权子代理（本仓 `CLAUDE.md` 的「Codex 子代理授权」节）
- `spawn_agent` 指定 `model` 需附 task-specific reason（本仓以 `model-tiers.md` 档位表为由）

---

## 7. 全局安装路径

`setup.sh` 写入以下 6 个位置：

| 路径 | 内容 | 机制 |
|------|------|------|
| **`~/.claude/skills/`** | 各 skill 目录的 symlink | `ln -snf`（Unix）/ copy + `.sdflow-skills` marker（Windows） |
| **`~/.codex/skills/`** | 同上，给 Codex 用 | 同上 |
| **`~/.claude/agents/`** | `sdflow-spec/agents/*.md` 的 3 个 agent 定义 | `ln -snf`（仅 Unix；Windows 跳过） |
| **`~/.sdflow/workflow`** | canonical workflow bundle 的 symlink → 运行 checkout 的 `sdflow-init/assets/workflow/` | `ln -snf` |
| **`~/.sdflow/hack/`** | helper 脚本（5 `.sh` + 1 `.py` + 1 `.md`） | 文件拷贝（非 symlink，改后需重跑 `setup.sh`） |
| **`~/.claude/hooks/`** | FF-0 branch guard hook（`init.py` 安装） | `sdflow-init` 铺设 |

### 所有权守卫

- `~/.claude/skills/` 和 `~/.codex/skills/`：只覆盖自己的 symlink 或带 `.sdflow-skills` marker 的目录，绝不覆盖非本仓库拥有的同名目录
- `~/.claude/agents/`：更严——只接管 `readlink` 命中 `*/sdflow-spec/agents/<同名>` 的软链
- 孤儿清理：源已删除的 skill 的残留 symlink 会被自动清除

---

## 8. 内部跨 Skill 依赖（本仓库内）

本仓库的 skill 之间存在编排调用关系：

```
sdflow-ship（阶段三编排器）
├── sdflow-implement（实现管线）
├── sdflow-code-review（代码审）
│   └── gstack /review（外部，Step1 并入）
└── sdflow-done（闭环）

sdflow-spec-review（设计审编排器）
├── gstack /autoplan（外部，广审层）
└── 并行多镜子代理

sdflow-spec（阶段一产 spec）
└── 内置澄清→拷问→生成三相位

sdflow-roadmap
├── /plan-eng-review 或 /autoplan（外部，review 分档）
└── /grilling、/domain-modeling（外部，wayfinder 票内可选）
```

---

## 9. 快速检查清单

新机器 / 新环境首次使用前：

```bash
# 1. 必须
bash --version          # >= 4.x
python3 --version       # >= 3.7
git --version

# 2. 推荐
yq --version            # mikefarah/yq >= 4.16.0
command -v timeout || command -v gtimeout   # macOS: brew install coreutils

# 3. 可选
openspec --version      # npm i -g @fission-ai/openspec
claude --version        # 跨模型 voice（Claude CLI）
codex --version         # 跨模型 voice（Codex CLI）

# 4. 安装 skills
bash setup.sh

# 5. 测试（开发用）
python3 -m pytest
```
