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

### 评审流程——已全部自持化，零外部依赖

设计审（`sdflow-spec-review`）的广审层（`strategy`/`plan-eng` 双镜）、roadmap（`sdflow-roadmap`）的
review（同一套 `strategy`/`plan-eng` 双镜）、代码审（`sdflow-code-review`）的 scope 审计，均已内化为
各 SKILL 自持的 fresh 子代理，**不再调用任何外部第三方评审 skill**。

> `/grill-with-docs` 已被 `sdflow-spec` 内置取代（`sdflow-spec/SKILL.md:10`），不再是外部依赖。
> `/grilling`、`/domain-modeling`（原 wayfinder 票内依赖）已随 `refactor-roadmap-internalize-deps`
> 内化进 `sdflow-roadmap` 自身的三相位结构，不再是外部依赖。
> 代码审 Step1 的 scope-drift + 完成度审计已随 `absorb-gstack-review` change
> 内化为 `sdflow-code-review` 自持 fresh 子代理；说明文档保留在
> [`docs/workflow-skills/gstack-review.md`](./workflow-skills/gstack-review.md) 作非运行时依赖的第三方 skill 参考。
> 设计审广审层与 roadmap review 双镜已随 `absorb-gstack-autoplan` change 内化为自持 fresh 子代理；
> 说明文档保留在
> [`docs/workflow-skills/gstack-autoplan.md`](./workflow-skills/gstack-autoplan.md) 作非运行时依赖的第三方 skill 参考。
>
> 以上参考文档均已降级为非运行时参考——仅供了解设计脉络，不构成任何调用关系。

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
│   └── Step1 自持 scope 审计（fresh 子代理，无外部依赖）
└── sdflow-done（闭环）

sdflow-spec-review（设计审编排器）
└── 单批 dispatch：strategy/plan-eng 双镜（自持广审）+ 领域/对抗/接地镜 + design-voice（均并行 fresh 子代理，无外部依赖）

sdflow-spec（阶段一产 spec）
└── 内置澄清→拷问→生成三相位

sdflow-roadmap
└── review：恒跑 strategy/plan-eng 双镜（自持）+ sync-only outside voice（无外部依赖）
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
