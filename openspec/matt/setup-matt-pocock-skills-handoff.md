# 交接：setup-matt-pocock-skills 配置  openspec/matt/setup-matt-pocock-skills-handoff.md

## 目标

为本仓库配置 Matt Pocock engineering skills 的工作项位置、triage 标签与领域文档路径，并同步根目录 `AGENTS.md` 与
`CLAUDE.md`。

## 已确认的决策

### Issue tracker

- 类型：本地 Markdown
- 工作项根目录：`openspec/matt/`
- 单个功能的工作项目录：`openspec/matt/<feature>/`
- 不使用 GitHub/GitLab Issues。
- 外部 PR 不作为 triage 输入。

### Triage 标签

保持五个默认标签：

- `needs-triage`
- `needs-info`
- `ready-for-agent`
- `ready-for-human`
- `wontfix`

### 领域文档

- 布局：单一上下文
- 领域上下文：`openspec/CONTEXT.md`
- 架构决策记录：`openspec/adr/`
- 不使用 `CONTEXT-MAP.md`。

### 配置说明文件位置

用户要求简化默认的 `docs/agents/` 布局，将三份说明文件直接放到 `openspec/matt/`：

- `openspec/matt/issue-tracker.md`
- `openspec/matt/triage-labels.md`
- `openspec/matt/domain.md`

## 待写入内容

### `AGENTS.md` 和 `CLAUDE.md`

两个文件均应新增或原位更新以下区块，不覆盖周边用户内容：

  ```markdown
  ## Agent skills

  ### Issue tracker

  工作项使用本地 Markdown，存放在 `openspec/matt/<feature>/`；外部 PR 不作为 triage 输入。详见 `openspec/matt/issue-
  tracker.md`。

  ### Triage labels

  使用默认的五种 triage 标签：`needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix`。详见
  `openspec/matt/triage-labels.md`。

  ### Domain docs

  单一上下文布局：`openspec/CONTEXT.md` 与 `openspec/adr/`。详见 `openspec/matt/domain.md`。

  ### openspec/matt/issue-tracker.md

  应说明：

  - 工作项采用本地 Markdown。
  - 根目录为 openspec/matt/。
  - 每个功能使用 openspec/matt/<feature>/。
  - to-tickets、triage、to-spec、qa 应在该位置读写工作项。
  - 不调用 gh 或 glab，也不处理外部 PR。

  ### openspec/matt/triage-labels.md

  应记录五个 canonical role 与同名标签的映射：

   角色            标签
  ━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━
   待评估          needs-triage
  ──────────────  ─────────────────
   等待补充信息    needs-info
  ──────────────  ─────────────────
   可交给 agent    ready-for-agent
  ──────────────  ─────────────────
   需人工处理      ready-for-human
  ──────────────  ─────────────────
   不处理          wontfix

  ### openspec/matt/domain.md

  应说明：

  - 本仓采用单一上下文。
  - 使用前先阅读 openspec/CONTEXT.md。
  - 涉及既有架构取舍时，按需阅读 openspec/adr/。
  - 不使用 CONTEXT-MAP.md。
  - 新增或调整领域术语、决策记录时，应更新相应文件。

  ## 当前阻塞

  未对仓库做任何写入或可靠的状态检查。

  所有本地命令均在启动 shell 前失败，错误为：

  failed to spawn code-mode host /opt/homebrew/bin/codex-code-mode-host:
  No such file or directory

  这说明 Codex 运行时所需的辅助程序不存在、被移动，或当前会话仍引用旧安装路径；与仓库内容、权限和本次配置无关。

  ## 重启后续作

  1. 验证运行时：

     ls -l /opt/homebrew/bin/codex-code-mode-host
     which codex
     codex --version

  2. 在仓库根目录执行 git status --short，保护既有改动。
  3. 按 setup-matt-pocock-skills 的 Explore 阶段复查：
      - git remote -v、.git/config
      - AGENTS.md、CLAUDE.md
      - openspec/CONTEXT.md、openspec/adr/
      - openspec/matt/ 既有内容

  4. 读取该 skill 的模板后，按上述已确认路径写入三份 Markdown，并同步更新 AGENTS.md 与 CLAUDE.md。
  5. 检查引用路径和 git diff，再向用户报告完成情况。

  ## 备注

  handoff skill 的本地说明文件同样因上述运行时错误而无法读取；本交接文档依据本次对话中用户已确认的决策整理。