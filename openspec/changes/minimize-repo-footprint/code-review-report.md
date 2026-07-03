# code-review 报告 — minimize-repo-footprint

> 2026-07-03 · impl-review 编排器（每次全跑·独立冷·强制主审）· diff base `fcbe3a3` → `22cefad`（17+2 commits）
> 第零步规则解析 = **经本 skill 协议真实触发 resolver**（`source=local-pin`，证据已入 activation-log.md——同时闭合 tasks 5.7 后半句 / subagent-dev 终审 Important#1）。

## 命中范围

- 栈：bash + python 部署工具链 → **无 domains 领域清单命中**，过通用 base CR-01~09。
- 镜面：gstack/review 审计（scope-drift + 完成度）+ CR 清单镜 + 对抗镜×2（错误路径 / 部署幂等，均实测复现型）+ 历史镜。
- gstack/review 结论：**无 scope-drift**（34 文件逐一归位；ROADMAP 扩展有 adr/0006 决策出处，判合法）；完成度 25/25 有实现，2 项守卫粒度低于计划措辞 + 1 缺测试用例（均已本轮修复/记债）。
- 历史镜结论：8 检查点无重蹈/无 revert/无决策矛盾。
- 前置说明：subagent-dev 终审已 READY-TO-MERGE 并 triage 5 债（T13–T17），本轮各镜已知悉、未重复计。

## Findings（置信 ≥80，全部已裁决）

| # | 严重度 | CR | 问题 | 证据 | 置信 | 处置 |
|---|---|---|---|---|---|---|
| 1 | 高 | CR-02 | cwd 被删时 resolver 违反 0/2/64 退出码契约（bash 裸 1 + getcwd 噪声；worktree 场景可信） | B1 复现命令+输出 | 95 | ✅ 已修[impl-review-fix]：pwd 失败守护 → exit 64 + 可读文案 + 测试 |
| 2 | 高→中 | — | 多 checkout 先后 setup，canonical 与 skills 链被**静默**夺权 | B2 双 checkout 复现，无任何 skip/warn 输出 | 95 | **裁决降级为可见性缺陷**（接管语义 = adr/0005 设计内，迁移/setup-from-dev 依赖）：canonical 侧✅已修[impl-review-fix]（指向变更打印"接管：旧→新"）；skills 链侧 defer→**T18** |
| 3 | 中 | — | `update --dev` 无仓身份校验，误用一次即把 34 文件整套规则灌进消费仓 | B2 复现 | 92 | ✅ 已修[impl-review-fix]：realpath 校验 root=源仓否则 `_die` + 测试 |
| 4 | 中 | — | 陈旧遮蔽告警绑定 `mode=="update"`，老仓误跑 `init` 假绿通过 | B2 复现"NO WARNING under init" | 92 | ✅ 已修[impl-review-fix]：告警改按磁盘状态触发（两 mode 都跑）+ 测试 |
| 5 | 中 | CR-02 | `sane()` 两清单目录只判存在不判非空——"防半坏态"意图有漏缝 | CR 镜 resolve-workflow.sh:55-56，测试盲区与代码盲区一致 | 88 | ✅ 已修[impl-review-fix]：目录非空判据 + 空目录测试 |
| 6 | 中 | CR-01 | init.py 文件系统失败抛裸 traceback，不走自身 `_die` 惯例；中途炸留半初始化态（幂等可自愈） | B1 复现（readonly/NotADirectory） | 90 | ✅ 已修[impl-review-fix]：run() 包 OSError→`_die` + 测试 |
| 7 | 中(latent) | — | `copy_bundle` tools/ 只增不删，上游删/改名文件在消费仓永久累积且零告警 | B2 植入 legacy 文件复现 | 85 | ✅ 已修[impl-review-fix]：非 full 模式 tools/ 清后拷（托管子树、覆盖刷新语义，不触"绝不删"红线）+ 测试 |
| 8 | 低 | — | SDFLOW_HOME 相对路径时"带路径的假成功"（结果随 invoker cwd 漂移） | B1 复现 | 85 | ✅ 已修[impl-review-fix]：步2 拒非绝对路径（本地 pin 不受影响）+ 测试 |
| 9 | 低 | — | `--root` 无条件吞下一 token，`--root --explain` 静默吃掉 flag | B1 复现 | 85 | ✅ 已修[impl-review-fix]：值以 `-` 开头 → exit 64 + 测试 |
| 10 | 低 | CR-01 | 指针读取 `\|\| true` 缺"为何安全"行内注释 | CR 镜 :52 | 80 | ✅ 已修[impl-review-fix]：补行内注释 |

**修复批附带发现**：又一处 bash 3.2 全角括号紧邻变量名触发 `set -u` 误报（与 Task 3 同类），已顺手 `${}` 界定——该坑本 change 内已出现两次，模式已知。

**gstack 完成度缺口处置**：5.3 缺"中文路径"用例 → ✅ 已随修复批补齐；1.1 Unix 软链所有权粒度 → 由 #2 可见化修复 + T14/T18 批次覆盖；5.7 后半句 → 本报告第零步已闭合；tasks.md 勾选 → opsx-done Step1 reconcile。

## 已裁掉（反静默压制，可审计）

- **X1** B2-F1 的"接管前要求交互确认"方案 → 裁掉。理由：阶段三无人类门 + setup.sh 须可非交互跑（迁移 0.1、sdflow-upgrade、CI 场景）；接管语义本身是 adr/0005"知情临时切 dev"的载体，防的该是"无感"而非"发生"——已用打印提示满足反静默。
- **X2** B1"setup.sh 对部分 checkout 产生悬空软链但报 ✓ installed（用词偏乐观）"→ 降级批注不立项。理由：悬空链下游被 resolver `sane()` 正确降级（B1 自证未爆），属文案精度问题，并入 T16（setup 摘要文案批次）语境。
- **<80 滤除**：无（本轮全部 findings 均有复现或逐字核验，无低置信项进入池）。

## 修复 / defer 台账

- 自动修 **10 项** `[impl-review-fix]`（commit `935eb42`，+244/−56，7 文件；新增测试 14 个，全仓 224 passed 无回归）。
- 自动选推荐 **2 项**（记理由）：#2 可见化而非阻断（理由见 X1）；#7 tools/ 清后拷而非 rsync 依赖（无新外部依赖，托管语义已覆盖）。
- defer **1 项** → **T18**（skills 链接管可见化，与既有 T13–T17 同属收尾打磨批次候选）。

## 结论

☑ **建议进 `/opsx-done`**（verify → hand-off → archive → commit → merge）。
☑ defer 残差已入 todolist（T13–T18，hand-off 将引用）；无 buglist 级残留——本轮 10 findings 全部当场修复并有测试锚点。
