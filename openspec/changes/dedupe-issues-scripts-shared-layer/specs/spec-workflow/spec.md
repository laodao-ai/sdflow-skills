## MODIFIED Requirements

### Requirement: skill 命名与品牌一致性

工具链自制 skill MUST 统一使用 `sdflow-` 前缀命名（目录名 = 安装名 = 斜杠命令名）；合一后台账类 skill 收敛为单一 `sdflow-issues`，`sdflow-buglist`/`sdflow-todolist` 已删除。

> `[spec-review-amendment]`（`dedupe-issues-scripts-shared-layer`）：原 requirement 的 sdflow- 前缀枚举含
> `sdflow-buglist`/`sdflow-todolist` 为独立 skill，且「sibling 脚本路径随名迁移」Scenario 假定 `issues.py` 上溯
> SKILLS_ROOT 后 join **sibling 目录** `sdflow-buglist`/`sdflow-todolist`。三 skill 合一为 `sdflow-issues`（`adr/0027`）后：
> ① 枚举中 `sdflow-buglist`/`sdflow-todolist` **删除**（并入 `sdflow-issues`）；② sibling-spawn 改为**同目录**定位。
> 命名规范其余部分（前缀约束、豁免名单、触发等价、trigger-map 留档）不变。

工具链自制 skill MUST 统一使用 `sdflow-` 前缀命名（目录名 = 安装名 = 斜杠命令名），按 RENAME-MAP（design §三）执行。
**RENAME-MAP 随本次台账合一更新**：原 map 中的 `sdflow-buglist`/`sdflow-todolist` **从 map 移除**（两 skill 删除、并入
`sdflow-issues`），map 台账项收敛为单一 `sdflow-issues`（owns 两池 + 跨池）；RENAME-MAP 其余项不变。
（注：RENAME-MAP 是那次改名 change 的映射子集、**非现役 skill census**——map 之后新增的 skill 如 `sdflow-architecture`/
`sdflow-devenv`/`sdflow-implement`/`sdflow-retro`/`sdflow-ship`/`sdflow-upgrade` 本就不在 map 内、不受本条约束。）
豁免保留名单 = `embedded-test-sop`（域技能）、
`openspec-upgrade`（升级外部 CLI）、`sdflow-upgrade`。主 spec 与功能性文件全文中的旧 skill 名 SHALL 随合一同步替换
（语义不变）；文档性历史记录（`adr/`、ROADMAP 历史行、CONTEXT 术语史、`changes/archive/`、`setup.sh` 的
`OUR_LEGACY_NAMES` 孤儿清理名单）MUST NOT 回改。各 SKILL.md 的 description MUST 触发等价：合并前分属两 skill 的触发
场景语句集（如「记一下这个 bug」「记个 TODO」）SHALL 全部保留、并入 `sdflow-issues` 单一触发面。

#### Scenario: 目录名与斜杠命令一致切换

- **WHEN** 合一完成并在运行 checkout 重跑 `setup.sh`
- **THEN** `~/.claude/skills/` 与 `~/.codex/skills/` 下存在 `sdflow-issues`、**不存在** `sdflow-buglist`/`sdflow-todolist`（旧名 dangling 链被孤儿清理收走，MUST NOT 残留）

#### Scenario: 触发等价不回退（并入单一触发面）

- **WHEN** 用户说出合并前即可触发某台账 skill 的语句（如「记一下这个 bug」「记个 TODO」）
- **THEN** 该语句仍触发 `sdflow-issues`（bug↔todo 分池分类由模型在 skill 内按「坏了没」判）；合并前两 skill 的触发短语集全部保留

#### Scenario: sibling 脚本路径改同目录

- **WHEN** `sdflow-issues` 的 `issues.py reindex`/`sweep` 需要子进程调用兄弟脚本
- **THEN** 它按**同目录**（`os.path.join(SCRIPT_DIR, "buglist.py")`）join 路径并成功调用，**MUST NOT** 再上溯 SKILLS_ROOT 后 join 已删除的 sibling 目录 `sdflow-buglist`/`sdflow-todolist`；`sdflow-done` 引用的脚本固定路径同为 `sdflow-issues/scripts/`
