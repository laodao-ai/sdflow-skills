---
name: openspec-upgrade
description: 升级 openspec CLI（@fission-ai/openspec npm 包）并刷新当前项目的 openspec skills 文件。当用户说"升级 openspec"、"更新 openspec"、"openspec upgrade"、"openspec 有新版本吗"、"openspec update"、"刷新 openspec skills"时触发。
allowed-tools:
  - Bash
  - AskUserQuestion
---

# /openspec-upgrade

升级 openspec CLI，然后更新当前项目的 openspec instruction 文件。

## Step 1：检查版本

```bash
CURRENT=$(npm list -g --depth=0 @fission-ai/openspec 2>/dev/null \
  | grep openspec | sed 's/.*@//' | tr -d ' ')
LATEST=$(npm view @fission-ai/openspec version 2>/dev/null)
echo "CURRENT=$CURRENT"
echo "LATEST=$LATEST"
```

**如果 npm 命令失败 / CURRENT 为空**：说明 openspec 未安装，告知用户：
```
openspec 未安装。安装命令：npm install -g @fission-ai/openspec
```
停止执行。

## Step 2：判断是否需要升级

**版本相同（CURRENT == LATEST）**：

用 AskUserQuestion 询问：
- 问题：`openspec 已是最新版本（v{CURRENT}）。是否仍要重新刷新项目的 skill 文件？`
- 选项：`["刷新 skill 文件", "不需要，已是最新"]`

选"不需要"则报告 `✓ openspec v{CURRENT} 已是最新，无需操作。` 并结束。
选"刷新"则跳到 Step 4。

**版本不同（CURRENT != LATEST）**：

用 AskUserQuestion 询问：
- 问题：`openspec 有新版本可用：v{CURRENT} → v{LATEST}。立即升级？`
- 选项：`["升级", "取消"]`

选"取消"则结束。选"升级"则继续 Step 3。

## Step 3：升级 CLI

```bash
npm install -g @fission-ai/openspec@latest
```

验证安装成功：
```bash
openspec --version
```

如果命令失败，报告错误信息并停止。

## Step 4：刷新项目 skill 文件

检查当前目录是否已初始化 openspec：
```bash
# openspec 初始化后会在 .claude/skills/ 下生成 openspec-* 文件
ls .claude/skills/openspec-* 2>/dev/null | head -3
```

**如果存在 openspec-\* 文件**（已初始化的项目）：
```bash
openspec update
```

**如果不存在**：告知用户当前目录未初始化 openspec，如需初始化可运行：
```
openspec init --tools claude
```
不做自动 init（避免在错误目录执行）。

## Step 5：汇报结果

升级成功后输出：
```
✓ openspec v{LATEST} 升级完成

CLI：v{CURRENT} → v{LATEST}
Skills：已通过 openspec update 刷新

如需查看变更：https://github.com/Fission-AI/OpenSpec
```

仅刷新（版本相同）时输出：
```
✓ openspec v{CURRENT} skill 文件已刷新
```
