# 设计 — drop-per-dir-review-stub

变更很小，唯一有实质权衡的是**如何安全退役一个已铺进存量安装的全局 hook**。其余（删脚本、删测试、改 SKILL.md）是机械操作，无设计决策。

## 背景：hook 安装是"只增不减"的

`sdflow-init/scripts/init.py` 的 `HOOKS` 列表 + `ensure_global_hook()` 只做**幂等安装**：
- 把 `assets/hooks/<name>.py` 拷进 `~/.claude/hooks/`；
- 往 `~/.claude/settings.json` 的 `PostToolUse`/`PreToolUse` 对应事件列表**追加**一条 `{"type":"command","command":"python3 \"$HOME/.claude/hooks/<name>.py\""}`（已存在则跳过）。

**没有任何移除路径**。所以「把 change-review-stub 从 HOOKS 列表删掉 + 删 asset」在存量安装上会留下：
1. `~/.claude/hooks/change-review-stub.py`（旧安装拷进去的副本，init 不再覆盖也不删）；
2. `~/.claude/settings.json` PostToolUse.Bash 里那条注册命令。

若只删①不删②→ 每次 Bash 触发 hook 时 `python3 .../change-review-stub.py` 报 `No such file`（**每次都报**，非静默）。若①②都不管→ 死 hook 永久残留 + 冗余 stub 继续产。

## ADR-1：加 `RETIRED_HOOKS` 反注册机制（自愈式退役）

**决策**：在 `init.py` 引入一个 `RETIRED_HOOKS`（退役 hook 名单，先放 `change-review-stub.py`），init/update 主流程每次都对名单里每项执行**反注册**：
- 从 `~/.claude/settings.json` 各事件列表中**外科式摘除** command 匹配该 hook 脚本路径的条目（只删匹配项，保留用户其余 hook；空列表/无该事件/无匹配→ no-op）；
- 删除 `~/.claude/hooks/<name>.py`（不存在→ no-op）；
- 幂等：跑几次结果一致；fresh 安装（从没装过该 hook）全程 no-op、零告警。

**为什么这样**：
- **自愈**——存量安装无需用户手动编辑 settings.json，跑一次 `sdflow-init update` 即清干净（部署边界 = update 已是既定升级动作）。
- **对称补齐**——安装框架本就该有的反向能力；`RETIRED_HOOKS` 成为后续任何 hook 退役的通用出口（一次建、复用）。
- **surgical 摘除**——settings.json 可能含用户自定义或其他 skill 的 hook，MUST 按 command 字符串精确匹配退役脚本、只删该条，绝不整清事件列表。

**权衡的替代**（均劣）：
| 替代 | 否决理由 |
|---|---|
| B. 不改 init，文档告知用户手删 settings.json | 脆弱、易漏；每 Bash 报错的体验差；违"脚本 owns 机械活" |
| C. hook 脚本保留但改成 `sys.exit(0)` 空壳 | 死注册 + 死文件永久残留；治标不治本 |
| D. 仅删 asset、不动注册 | 存量安装每次 Bash 报 `No such file`，明确不可接受 |

**edge cases（写进测试）**：
- settings.json 不存在 / 非法 JSON → fail-safe 跳过（不因反注册崩坏 init，沿用现有 fail-open 姿态）；
- 该 hook 从未安装（fresh）→ 反注册全 no-op；
- settings.json 里有该事件但无该 hook（用户只装了别的 hook）→ 保留他项、只 no-op 本项；
- 同一 hook 被误注册多条 → 全部摘除。

## 范围外的确认（无需 ADR）

- **root anchor 保留**：`copy_review_tool()` 铺 `openspec/review.html` + `serve.sh` 不动；engine bundle 随 `copy_bundle` 的 `tools/` 不动。查看能力 100% 由根锚承接（engine.js 从 pathname 推 scope 是既有能力，非本 change 引入）。
- **roadmap 生产者**是显式调用步、无全局注册，直接删脚本 + SKILL.md 步 + 测试即可，无迁移问题。
- **Codex 侧无 hook**：PostToolUse hook 是 Claude Code 机制，只在 `~/.claude/`；反注册只需处理 `~/.claude/`。

## 图：退役前后

```
退役前（存量安装）                     退役后（update 自愈）
~/.claude/hooks/                       ~/.claude/hooks/
  ff0-branch-guard.py     ← 保留         ff0-branch-guard.py     ← 保留
  change-review-stub.py   ← 删           (已删)
~/.claude/settings.json                ~/.claude/settings.json
  PreToolUse.Bash:                       PreToolUse.Bash:
    ff0-branch-guard        ← 保留          ff0-branch-guard        ← 保留
  PostToolUse.Bash:                       PostToolUse.Bash:
    change-review-stub      ← 摘除          (该事件下无 sdflow 项 / 保留他项)
```
