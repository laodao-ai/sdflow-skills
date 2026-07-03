---
name: opsx-project-init
description: >
  把整套 OpenSpec spec 工作流（openspec/workflow/ bundle）一键铺进一个项目：建目录骨架、拷规则集、
  从模版生成/合并 config.yaml、注入 INDEX.md 与 CLAUDE.md/AGENTS.md 的托管区块，并说明 3 个配套 skill。
  **只要用户想在新项目里启用这套 spec 工作流，或说"给这个项目初始化 openspec 工作流 / 把 workflow
  铺过来 / 装一下 spec 工作流 / 新项目搭一套和 04-iot-tools 一样的 openspec / 更新这个项目的 workflow
  规则到最新"，就用本 skill**——别手动一个个拷文件。脚本兜底确定性铺设与幂等注入，模型只管判断
  （填 config 的本项目段、合并已存在的 config）。本 skill 的 assets/workflow/ 是这套 bundle 的唯一
  权威源；init 铺设、update 重拉最新。Trigger with /opsx-project-init。
---

# opsx-project-init — 一键铺设 OpenSpec spec 工作流

把 `openspec/workflow/` 这套**项目无关**的 spec 工作流 bundle 铺进任意项目，并接好 config / INDEX /
CLAUDE.md。**本 skill 的 `assets/workflow/` 是该 bundle 的唯一权威源**——新项目从这里铺，bundle 有改动
先改这里、再用 `update` 推到各项目。

> **为什么要 skill**：手动铺要拷 28 个文件、另存 config 模版、改 INDEX、改 CLAUDE.md，易漏易错。
> 脚本把确定性部分（拷贝、建目录、标记区块**幂等**注入）一次做对；模型只处理需要判断的两点
> （填 config 本项目段、合并已存在 config）。

脚本：[scripts/init.py](scripts/init.py)。bundle 源：`assets/workflow/`。注入片段：`assets/snippets/`。

---

## 两种模式

| 模式 | 用于 | 行为 |
|------|------|------|
| **init** | 空项目首次铺设 | 建目录骨架 + 拷 bundle + 从模版生成 config.yaml + 注入 INDEX/CLAUDE/AGENTS 托管区块 + 确保全局 FF-0 hook |
| **update** | 已铺过的项目 | 重拉最新 bundle（覆盖 `workflow/` 托管文件）+ 重注入托管区块 + 幂等确保全局 FF-0 hook；**不动 config.yaml、不覆盖用户内容** |

## 怎么用

### 第零步：确认 openspec 已就绪
若目标项目还没 `openspec/`，先让 OpenSpec 自身初始化核心（`openspec init`），再铺本 bundle。
（脚本也会自建所需目录与 config，但 `openspec init` 能把核心 schema/CLI 接好。）

### 第一步：跑脚本
```bash
# 在目标项目根目录
python ~/.claude/skills/opsx-project-init/scripts/init.py init      # 首次铺设
python ~/.claude/skills/opsx-project-init/scripts/init.py update    # 重拉最新 bundle
# 或显式指定项目根
python <skill>/scripts/init.py init --root /path/to/project
```
脚本会打印每步动作（建了哪些目录、bundle 多少文件、config/INDEX/CLAUDE/AGENTS 各做了什么）。

### 第二步：处理需要判断的两点（模型的活）
脚本结束会提示下一步：

1. **填 config 的「本项目」段**（init 新建 config 时）：编辑 `openspec/config.yaml` 的 `## 本项目`
   context 段，填该项目的 tech stack、命中的领域（backend·go / embedded·ml307c·esp32 / frontend）、
   硬边界等。**通用段与 rules 照搬模版、勿改**。
2. **合并已存在的 config**（config.yaml 已存在时）：把模版（`openspec/workflow/config.template.yaml`）的
   「通用」context 段 + 全部 `rules:` 并入现有 config.yaml，**保留**用户的「本项目」段和自定义键。
   这步用模型读两份做 YAML 合并，别让脚本硬改（block scalar 易破坏）。

### 第三步：装配套 skill
workflow.md 的流程依赖 3 个 laodao skill，提示用户安装：
```bash
bash ~/.skills/laodao-skills/setup.sh
```
- `/spec-review` — 设计审主审 · `/impl-review` — 代码审主审 · `/opsx-done` — 闭环（verify→archive→commit→merge）
（记录类按需：`/buglist-recorder`、`/todolist-recorder`。）

## 铺设了什么

```
openspec/
├── workflow/              ← 整套 bundle（assets/workflow 的副本，托管，update 会覆盖）
│   ├── workflow.md trigger-catalog.md ff-generation-constraints.md
│   ├── generation-process.md design-diagrams.md spec-review.md
│   ├── config.template.yaml
│   ├── spec-checklists/  code-checklists/   (base + domains)
│   ├── tools/            ← engine.js + engine.css + vendor/marked.min.js + review-stub.html（B1 归位进 bundle）
│   │                       （review-stub.html 是模板，roadmap/change 目录的 review.html 由它生成）
│   └── reference/         (说明类，可删)
├── config.yaml            ← init 从 config.template.yaml 生成（本项目段待填）
├── INDEX.md               ← 注入「工作流规则」托管区块
├── changes/  specs/       ← 目录骨架
├── review.html            ← 文档查看器根入口（scope="" 全树导航；资产引用 /workflow/tools/…）
├── serve.sh                ← 后台起停封装：start [port] / stop / restart [port]，
│                             cd 到 openspec/ 再起 python3 -m http.server（服务器根=openspec/，
│                             故 review UI 能 HTTP 覆盖 changes/specs；根锚留根，工具机械在 workflow/tools/）
CLAUDE.md / AGENTS.md      ← 注入「OpenSpec 工作流」托管区块（强制规范 + 3 配套 skill 说明）
```

> **FF-0 hook 是全局的**：装于 `~/.claude/hooks/ff0-branch-guard.py` + 注册进 `~/.claude/settings.json`（**不写项目 `.claude/`**），init/update 幂等确保、跨所有项目生效。

## 托管区块（幂等、勿手改区块内）

脚本用 HTML 注释标记包裹注入内容，重跑只替换标记间、不动其余：
- `CLAUDE.md` / `AGENTS.md`：`<!-- opsx-init:start -->` … `<!-- opsx-init:end -->`
- `INDEX.md`：`<!-- opsx-init:rules:start -->` … `<!-- opsx-init:rules:end -->`

要改这些托管内容，改 `assets/snippets/` 再 `update`，别手改目标文件区块内（会被下次 update 覆盖）。

## 注意

- **权威源唯一**：bundle 改动一律先改本 skill 的 `assets/workflow/`，再 `update` 推到各项目；
  别在某个项目里直接改 `openspec/workflow/` 然后忘了回灌（会被下次 update 覆盖）。
- **不覆盖用户内容**：config.yaml 的本项目段、CLAUDE.md/AGENTS.md 标记区块外的内容，脚本一律不动。
- **`openspec/rules/` 不在本 bundle**（destructive-commands、task-completion 等是独立通用规则，按需自行加）。
- **FF-0 硬强制（全局）**：hook 脚本源在本 skill 的 `assets/hooks/ff0-branch-guard.py`，由 `init`/`update` **全局安装**到 `~/.claude/hooks/` + 注册进 `~/.claude/settings.json` 的 PreToolUse.Bash（幂等、跨所有项目，**不写项目 `.claude/`**）。使得在 `master`/`main` 上跑 `openspec new change`（`/opsx:new`、`/opsx:propose`、`/opsx:ff`、`/opsx:onboard` 共用此 CLI 入口）被直接拦下，逼先开 feature 分支。想卸载：删 `~/.claude/hooks/ff0-branch-guard.py` + 移除 `~/.claude/settings.json` 中对应 PreToolUse entry。权威定义见 `workflow/ff-generation-constraints.md` FF-0。
- **change 目录自动补 review.html（全局第二个 hook）**：hook 脚本源在本 skill 的
  `assets/hooks/change-review-stub.py`，由 `init`/`update` 全局安装到 `~/.claude/hooks/` + 注册进
  `~/.claude/settings.json` 的 `PostToolUse.Bash`。`openspec new change <name>` 跑完后，若项目已铺设
  review 工具（`openspec/review.html` 存在），自动在新建的 `openspec/changes/<name>/` 下补一份
  `review.html`（scope 指向该目录），随 `openspec archive` 一起搬迁、无需重新生成。项目未铺设 review
  工具时静默跳过，不强迫铺设顺序。
- 脚本默认 `--root .`（当前目录）；务必在目标项目根跑，或用 `--root` 指定。
