# Claude Code Skill 命名前缀（namespace）调研

> 调研日期：2026-04-16
> 问题：skill 能否加 `laodao-ai:` 前缀，如 `/laodao-ai:embedded-lint`？

---

## 结论

**可以，但需要插件系统（plugin），不是修改 `~/.claude/skills/` 目录。**

---

## 机制：两种 skill 加载路径

### 路径 A：`~/.claude/skills/`（普通 skill，无前缀）

```
~/.claude/skills/<skill-name>/SKILL.md  →  /skill-name
~/.claude/skills/<subdir>/<skill-name>/SKILL.md  →  /skill-name（子目录不产生前缀）
```

`laodao-skills/setup.sh` 就是把 skill 复制/链接到这个扁平结构。所有 skill 都没有前缀。

### 路径 B：插件 marketplace（有前缀）

```
~/.claude/plugins/marketplaces/<marketplace>/plugins/<plugin-name>/skills/<skill-name>/SKILL.md
                                                              ↑
                                                  目录名 = namespace 前缀
→ /plugin-name:skill-name
```

**`plugin-name` 目录名就是前缀。** 没有额外的 `plugin.json` 或 frontmatter 配置，目录名即命名空间。

---

## 现有插件示例

| 前缀 | Plugin 目录 | Marketplace |
|------|------------|-------------|
| `superpowers:` | `plugins/superpowers/` | `claude-plugins-official` (GitHub: anthropics/claude-plugins-official) |
| `commit-commands:` | `plugins/commit-commands/` | `claude-plugins-official` |
| `code-review:` | `plugins/code-review/` | `claude-plugins-official` |
| `example-skills:` | `plugins/example-skills/` | `anthropic-agent-skills` |

---

## 相关命令

```bash
# 查看已安装插件
claude plugin list

# 添加本地 marketplace
claude plugin marketplace add <local-path-or-git-url> --name <marketplace-name>

# 安装插件（从指定 marketplace）
claude plugin install <plugin-name>@<marketplace-name>

# 验证插件结构是否合法
claude plugin validate <path>

# 查看 marketplace 列表
claude plugin marketplace list
```

---

## 获得 `laodao-ai:skill-name` 的最小步骤

### 目录结构

```
~/laodao-ai-marketplace/
└── plugins/
    └── laodao-ai/               ← 这个名字就是前缀
        └── skills/
            └── embedded-lint/
                └── SKILL.md
            └── another-skill/
                └── SKILL.md
```

### 命令

```bash
# 注册本地目录为 marketplace
claude plugin marketplace add ~/laodao-ai-marketplace --name laodao-ai

# 安装名为 laodao-ai 的插件
claude plugin install laodao-ai@laodao-ai

# 验证（重启 claude 后）
# /laodao-ai:embedded-lint 应可用
```

---

## 选项对比

| 方案 | 调用方式 | 维护成本 |
|------|---------|---------|
| 现状（`~/.claude/skills/`） | `/embedded-lint` | 零，`setup.sh` 已管理 |
| 本地 plugin（单 skill） | `/laodao-ai:embedded-lint` | 需维护两份文件 |
| 将 `laodao-skills` 整体改为 marketplace | `/laodao-ai:*` 全部 skill | 一次性重构 `setup.sh` |

**建议**：有命名冲突或需要品牌归属时才值得加前缀。如果整体改造，最干净的路是将 `laodao-skills` 仓库从"flat skills 安装包"重构为"本地 marketplace"，`plugins/laodao-ai/skills/` 下存放所有 skill，一次性让全部 skill 带 `laodao-ai:` 前缀，同时废弃 `setup.sh`。

---

## 文件位置速查

```
~/.claude/plugins/installed_plugins.json     已安装插件注册表
~/.claude/plugins/known_marketplaces.json    已添加 marketplace 列表
~/.claude/plugins/marketplaces/<name>/       marketplace 本地缓存
~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/skills/  skill 实际文件
```
