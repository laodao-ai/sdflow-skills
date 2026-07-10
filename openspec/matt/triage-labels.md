# Triage 标签

Engineering skills 使用五个 canonical triage role。下表将它们映射到本仓库本地 Markdown 工作项中的状态词。

| 角色 | 标签 | 含义 |
| --- | --- | --- |
| 待评估 | `needs-triage` | 维护者需要评估该工作项 |
| 等待补充信息 | `needs-info` | 等待提出者补充信息 |
| 可交给 agent | `ready-for-agent` | 已完整定义，可由 AFK agent 执行 |
| 需人工处理 | `ready-for-human` | 需要人工实现或决策 |
| 不处理 | `wontfix` | 不再推进 |

当 skill 指向某个 canonical role 时，在工作项的 `Status:` 行使用上表对应的标签字符串。
