# laodao-skills

老刀AI码场自建 Claude Code Skills 统一管理仓库。

## Skills 列表

| 分类 | Skill | 说明 |
|------|-------|------|
| 内容创作 | bilibili-research | B站搜索词调研与选题分析 |
| 内容创作 | x-research | X/Twitter 调研 |
| 内容创作 | youtube-research | YouTube 调研 |
| 内容创作 | zhihu-research | 知乎调研 |
| 开发工具 | commit-message | Git commit 信息生成 |
| 开发工具 | ssh-tunnel | SSH 隧道管理 |
| 开发工具 | tag | Git 语义化版本标签 |
| 开发工具 | gstack-project-init | gstack 项目级文档归集 |
| OpenSpec | opsx-maintain | OpenSpec 目录维护 |
| OpenSpec | opsx-roadmap-planner | 分阶段 roadmap 规划工作流 |
| 嵌入式 | embedded-lint | C 语言静态分析 |
| 嵌入式 | embedded-test-sop | 嵌入式手动测试 SOP 生成 |
| 文档转换 | docx2md | Word 转 Markdown |
| 文档转换 | pdf2md | PDF 转 Markdown |
| 文档转换 | xlsx2md | Excel 转 CSV |
| 元工具 | **config-setup** | **模版驱动的项目级 settings 编排（详见下方专章）** |
| 元工具 | update | 更新 laodao-skills |

## 安装

```bash
cd ~/.claude/skills
git clone https://github.com/laodao-ai/laodao-skills.git
cd laodao-skills
bash setup.sh
```

## 更新

在 Claude Code 中直接使用：

```
/ld-update
```

或手动更新：

```bash
cd ~/.claude/skills/laodao-skills
git pull
bash setup.sh
```

## 工作原理

- **Linux/macOS**：setup.sh 在 `~/.claude/skills/` 下为每个 skill 创建相对路径 symlink
- **Windows**：setup.sh 将 skill 目录复制到 `~/.claude/skills/`，并写入 `.laodao-skills` 标记文件用于更新检测

---

## config-setup — 模版驱动的项目级 settings 编排

进新项目的一站式设置入口。分析项目类型 → 匹配/生成模版 → 串行完成 plugin→skill 配置，写入 `.claude/settings.json`。

### 架构

`config-setup` 是一个编排入口，内含两个子 skill：

| 命令 | 说明 |
|------|------|
| `/config-setup` | 主入口：分析项目、匹配模版、串行调度下面两个子 skill |
| `/config-plugins` | 项目级 plugin 编排：浏览/决策/写入 `enabledPlugins` |
| `/config-skills` | 项目级自建 skill 编排：4 态（on/name-only/user-invocable-only/off）编排 `skillOverrides` |

### 模版

预置模版按项目类型匹配，也可自定义：

| 模版 | 适用场景 |
|------|----------|
| `content-creator` | SDD 内容创作工作区（OpenSpec + Hugo + 写作流水线） |
| `go-backend` | Go 后端服务项目 |
| `hugo-blog` | Hugo 静态博客项目 |

### 三层 settings 模型

settings 读取遵循三层合并：

1. **Layer 1** — 用户全局 `~/.claude/settings.json`
2. **Layer 2** — 用户本地 `~/.claude/settings.local.json`
3. **Layer 3** — 项目级 `.claude/settings.json`（config-setup 的写入目标）

### 安全特性

- **备份**：每次写入前自动 `.bak.YYYYMMDD-HHMMSS`，保留最近 3 份
- **原子写回**：tmp 文件 + `os.replace`，防止写一半崩溃
- **健康检查**：检测 phantom（已删除）/ unset（新增未配置）的 plugin 和 skill
- **幂等**：已 up-to-date 提前结束

### 用法

```
/config-setup
```

或自然触发："配一下这个项目"、"进新项目"、"配 settings.json"等。

详见 `config-setup/SKILL.md`。


---

## 许可

MIT
