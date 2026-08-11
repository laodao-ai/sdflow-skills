### Task 1: 脚手架 + anchors 基础设施 + cwd 守卫

**Blocked-by:** none
**R-ID:** R1, R7

建立 `sdflow-upstream-watch/` 目录骨架与核心基础设施：

1. 建 `sdflow-upstream-watch/` 目录：SKILL.md（frontmatter + 编排指令占位）、`scripts/upstream_watch.py`（4 行 reconfigure 前导 + `collect`/`advance` 子命令骨架 + argparse 入口）、`tests/` 目录。
2. 跑 `python3 hack/sync_principles.py --apply` 注入通则托管块并确认自报投放面计数 +1。
3. 建 `openspec/upstream/` 数据目录（`reports/` 留 `.gitkeep`）。
4. 实现 cwd 守卫（两子命令起手 git remote 判定，非 sdflow-skills 仓 fail-loud 不写文件）。
5. 实现 anchors.yaml 读写层（yq，三态错误语义 + mikefarah-flavor 探测）+ `schema_version` 与 `remind_after_days` 字段。
6. 实现外部子进程统一超时常量（单点定义，默认 60s）。
7. 测试覆盖：cwd 守卫（非本仓 cwd 拒绝零写入）+ anchors 语义（首轮初始化 / yq 失败硬停 / 值缺失无锚）。

- [ ] SKILL.md 骨架已建、通则托管块已注入（sync_principles --apply 绿且计数 +1）
- [ ] `openspec/upstream/` 目录在 git 中（reports/ 有 .gitkeep）
- [ ] cwd 守卫在非 sdflow-skills 仓 cwd 下 fail-loud 退出且零写入
- [ ] anchors.yaml 三态读写正确（缺失=初始化 / yq 坏=硬停 / 值缺失=无锚）
- [ ] mikefarah-flavor yq 探测正确，非 mikefarah 报错
- [ ] 超时常量单点定义且 argparse 入口可用
- [ ] 上述各路径有对应 pytest 测试绿

