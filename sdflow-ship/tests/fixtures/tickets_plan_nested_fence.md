---
impl-pipeline: tickets
---

## Global Constraints

- 本 fixture 的判别点：**嵌套示例围栏**（外层 ```markdown 内嵌 ```bash）。
- 旧手抄口径 `line.lstrip().startswith("```")` 会被内层 ``` **提前关掉**外层围栏，
  于是外层块内后续的伪标题 / 伪复选框被当成真内容 ⇒ 两个解析器给出不同段落边界。
- 单一源 FenceTracker 口径：闭合符须**同种**、长度 ≥ 开启符、其后只余空白，
  故 ```bash（带 info string）关不掉外层 ```markdown，整块内容一律不可见。

### Task 1: 写一份带嵌套示例的说明

**Blocked-by:** none
**R-ID:** R1

文档里要贴一段"如何写 ticket"的示例，示例本身又含一个 shell 代码块。

````markdown
```text
### Task 9: 这是示例里的伪标题，不是真任务

**Blocked-by:** none

- [ ] 示例里的伪复选框 A
- [ ] 示例里的伪复选框 B
```
````

- [x] 真复选框 1

### Task 2: 收尾

**Blocked-by:** 1
**R-ID:** R2

- [ ] 真复选框 2
