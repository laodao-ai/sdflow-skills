# Claude Code Token 节省策略

记录在使用 Claude Code + superpowers 工作流时，经过验证的 token 节省方法。

---

## 一、关闭高消耗 Hook / Skill / Plugin

### 1. 关闭 `explanatory-output-style` 插件

**效果**：每次回复少生成 `★ Insight` 教育说明块，直接减少输出 token。
**影响范围**：全局每条回复。插件 README 自带 WARNING: "token cost"。
**操作**：

```bash
/plugin disable explanatory-output-style@claude-plugins-official
```

### 2. 关闭 `learning-output-style` 插件

**效果**：同 explanatory，叠加了"互动教学"功能，token 消耗更重。若未装可忽略；若装了必须关。
**说明**：官方 README 警告更强——同时包含 explanatory 全部功能 + 互动学习，是耗 token 最重的 style 插件。
**操作**：

```bash
/plugin disable learning-output-style@claude-plugins-official
```

### 3. 关闭 `superpowers:using-superpowers`

**效果**：减少每次对话开始时加载的 prompt 体积（该 skill 主要作用是提醒 Claude "先查 skill 再行动"）。
**适用场景**：已熟悉工作流、会主动调用所需 skill（如 `write-plans`、`subagent-driven-development`）的用户。
**注意**：`using-superpowers` 是 `superpowers` plugin 的一部分，不能在 plugin 级别单独关闭，需通过 `skillOverrides` 覆盖。
**全局关闭**（写入 `~/.claude/settings.json`）：

```json
"skillOverrides": {
  "superpowers:using-superpowers": "off"
}
```

**项目级关闭**（写入项目 `.claude/settings.json`，相同格式）。

---

## 二、使用 Caveman 模式压缩输出

### 5. `/caveman` — 超压缩回复模式

**效果**：官方数据约省 ~75% 输出 token。去除冠词、口头禅、客套话，保留全部技术内容。
**来源**：自建 skill，已安装到 `~/.skills/caveman/SKILL.md`，symlink 到 `~/.claude/skills/caveman`。
**官方市场**：无同类 style 插件（已验证 `anthropics/claude-plugins-official`，两个官方 style 插件均为加 token，非减）。
**操作**：

```bash
/caveman          # 开启，之后每条回复保持压缩风格
stop caveman      # 或 "normal mode" 退出
```

**安装方法**（新机器）：

```bash
mkdir -p ~/.skills/caveman
# 写入 SKILL.md（内容见 ~/.skills/caveman/SKILL.md）
ln -s ../../.skills/caveman ~/.claude/skills/caveman
```

---

## 三、减少权限提示往返

### 6. 运行 `fewer-permission-prompts`

**效果**：扫描会话历史，把常见的只读 Bash/MCP 调用（`ls`、`rg`、`git log` 等）批量加入项目 `.claude/settings.json` 白名单，之后不再弹权限提示。
**适用场景**：在一个项目工作一段时间后，权限提示反复出现时运行一次。
**操作**：

```bash
/fewer-permission-prompts
```

---

## 四、模型选择

### 7. 执行类 Skill 切换 Haiku 模型

**效果**：Haiku 4.5 token 成本约为 Sonnet 的 1/5，对流程明确的执行任务表现够用。
**适用 Skill**：`/tag`、`/ssh-tunnel`、`/tdd`、`/commit-message` 等步骤固定的流程 skill。
**操作**：

```
/model haiku       # 切到 Haiku
/tdd               # 跑 skill
/model             # 跑完切回 Sonnet
```

### 8. `/sdflow-done` — OpenSpec 收尾自动派发 Haiku 子 agent

**效果**：verify → archive → git commit → (可选) merge to main 四步机械操作全部由 Haiku 子 agent 执行，主 session 上下文隔离，不触发 model 切换 / cache reload。
**原理**：skill 调用 Agent tool 时指定 `model: haiku`，子 agent 只接收任务 prompt，不携带主 session 的大上下文。
**来源**：自建 skill，位于 `~/.skills/sdflow-skills/sdflow-done/SKILL.md`，symlink 到 `~/.claude/skills/sdflow-done`。
**操作**：

```bash
/sdflow-done                    # 自动检测 active change
/sdflow-done add-mqtt-filter    # 指定 change 名
```

**步骤**（串行，任一失败则中止）：
1. **Verify**（Haiku）— 核对 tasks.md + specs，输出 verify-report.md
2. **Archive**（Haiku）— 归档到 openspec/archive/，更新 INDEX.md
3. **Commit**（Haiku）— `git add openspec/ && git add -u`，生成 commit message，提交（不 push）
4. **Merge**（Haiku，询问后执行）— `git checkout main && git merge feat/{change} --no-ff`

---

## 五、调用方式优化

### 8. 明确 scope，避免 skill 扫描全 codebase

**效果**：越具体的 prompt → skill 读取的上下文越少 → token 越少。
**示例**：

```
# 差：范围不明
/tdd

# 好：明确文件和函数
使用 TDD 为 src/mqtt/parser.ts 的 parsePayload 函数写测试
```

### 9. 避免触发重型 skill 组合

`/review`（本地 diff）和 `/code-review`（远程 PR）都会开子 agent，组合使用 token 消耗很高。
- 本地开发阶段：只用 `/review`
- 需要远程 PR 评审时：再用 `/code-review`
- 低优先级改动：`/code-review low`（低 effort，只看高置信度问题）

### 10. 适时 `/clear` 重置上下文

对话过长后，历史消息会被压缩成摘要并仍占 token。完成一个独立任务后用 `/clear` 重置，下个任务从干净上下文开始。

---

## 六、快速参考

| # | 方法 | 省 token 幅度 | 操作成本 |
|---|------|--------------|---------|
| 1 | 关闭 `explanatory-output-style` 插件 | 高（每条回复） | 一次性 |
| 2 | 关闭 `learning-output-style` 插件 | 高（每条回复） | 一次性 |
| 3 | 关闭 `using-superpowers` | 中（每次会话） | 一次性 |
| 4 | `/caveman` 压缩回复 | ~75% 输出 token | 按需触发 |
| 5 | `fewer-permission-prompts` | 低-中（减少往返） | 偶尔运行 |
| 6 | 切换 Haiku 跑执行类 skill | ~80% | 每次手动切换 |
| 7 | `/sdflow-done` OpenSpec 收尾派发 Haiku 子 agent | 高（verify+archive+commit 全隔离） | 装一次，按需触发 |
| 8 | 明确 scope 再调 skill | 中 | 改写习惯 |
| 9 | 避免重型 skill 组合 | 高（按需） | 流程意识 |
| 10 | 适时 `/clear` 重置上下文 | 中 | 任务完成后 |
