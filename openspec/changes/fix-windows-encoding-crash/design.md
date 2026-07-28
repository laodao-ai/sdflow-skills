## Context

见 [`proposal.md`](./proposal.md) 的 Why/What Changes：Windows(GBK/cp936) 环境下，本仓 Python 脚本 `print()`/`write_text()` 遇到 GBK 编不出的字符（`✅🔴⚠✓` 等）即 `UnicodeEncodeError` 崩溃，命中 `setup.sh` 的四道机械一致性门与 `sdflow-init` 的 `init.py`，且恰好崩在"打印成功消息"那一行，把通过判定误判成假红（`openspec/issues/buglist/2026-07-28-buglist.md` B23）。本机 Windows Git Bash 实测复现，详细证据见 [`decision-memo.md`](./decision-memo.md) C1/C2/C9。

约束：① 每个 skill 是独立分发目录，被 symlink/复制安装到消费者的 `~/.claude/skills/`，脚本之间**不能共享公共 Python 模块**（`decision-memo.md` C4 已用 grep 验证全仓无此类跨 skill import）；② `openspec/workflow/tools/*.py` 是 `sdflow-init/assets/workflow/tools/*.py` 的托管镜像，只能改源（C5）。

## Goals / Non-Goals

**Goals:**
- 消除全部 27 个入口脚本在 GBK 环境下因打印 Unicode 字符触发的崩溃。
- 补全 `subprocess text=True`（16 处）与 `write_text()`（2 处）的显式编码，避免解码崩溃与乱码文件。
- 新增机械门防止后续新脚本遗漏防护（面治而非点补）。
- 在真实 Windows CI（`windows-latest` + `PYTHONIOENCODING=gbk` 真实子进程）上验证，而非仅靠此前的 mac 模拟。

**Non-Goals:**
- 不做语义级"扫描字符串内容是否含风险字符"的检测器（见 Decisions D1）。
- 不引入跨 skill 共享模块。
- 不处理本仓之外消费该 bundle 的下游项目自身脚本（它们随后续 `sdflow-init update` 自然获得修复）。

## Components（TG-14：新增组件 `hack/check_encoding_hygiene.py`）

新增一个脚本，与既有 `setup.sh` 四道机械门并列、同构接线（独立守卫，不挂在其它门的条件下）：

```
setup.sh
  ├── hack/sync_principles.py            （既有，四条通则漂移）
  ├── hack/gen_workflow_guide.py         （既有，WORKFLOW-GUIDE 单一源）
  ├── hack/check_async_branch_parity.py  （既有，async host 段落一致）
  ├── hack/check_tier_resolution_parity.py（既有，档位解析段落一致）
  └── hack/check_encoding_hygiene.py     （新增，本 change）
        │  扫描目标 glob（见下）下每个含 `if __name__ == "__main__":` 的脚本，
        │  存在性检查：前几行是否含 `reconfigure(encoding=` 调用
        ▼
  目标 glob：hack/**/*.py + sdflow-*/scripts/**/*.py
            + sdflow-init/assets/{hack,hooks,workflow/tools}/**/*.py
            （排除 **/tests/**；排除 openspec/workflow/tools/**——
             它是 sdflow-init/assets/workflow/tools/ 的托管镜像，检查源即覆盖镜像）
```

依赖方向：`setup.sh` → 调用 `check_encoding_hygiene.py` → 读取仓内脚本文件（只读，无侧写）。与既有四道门同级并列，互不依赖。

## Decisions

本 change 的决策全文、砍掉的候选、三镜代价与证据锚见 [`decision-memo.md`](./decision-memo.md)（D1–D5、C1–C10）。TG-23（≥2 合理方案：检测机制存在性检查 vs 语义扫描）命中，其 ADR 结构化记录（方案对比 + 理由 + 三镜代价）已在 `decision-memo.md` D1 与"三镜代价"节完整给出，不在此重复。

补充两条实现顺序上的技术选择（不改变已拍板的 D1–D5，属于落地细节）：

- **先实现 `check_encoding_hygiene.py`，用它的失败列表驱动 27 个脚本的注入顺序**（对应 `decision-memo.md` D5）——避免人工枚举遗漏（本轮 grill 已发现人工估算 ~19 与实测 27 的偏差，见 C6）。
- **`check_encoding_hygiene.py` 只有裸调用模式（无 `--apply`）**，仿 `check_async_branch_parity.py` / `check_tier_resolution_parity.py` 的纯验证模式，而非 `sync_principles.py` 的 `--check/--apply` 模式——因为本检查没有单一"canonical 内容"可回填，各脚本的 reconfigure 前导插入点需要实现时逐文件确认语法正确（比如是否已有 `import sys`、shebang 行位置），批量自动写入有破坏语法的风险。

## Risks / Trade-offs

- **[风险] 27 个脚本手工插入前导块，逐文件确认插入点存在出错概率** → **缓解**：`check_encoding_hygiene.py` 是插入后的验证闸门，任何遗漏或格式错误都会被它挡在 CI/`setup.sh` 之外；且插入内容 4 行固定模板，复制粘贴出错概率低。
- **[风险] 16 处 `subprocess text=True` 补 `encoding="utf-8"` 后，若被解码的子进程输出本身不是 UTF-8（如某些 git 配置下 commit message 用 GBK 提交）** → **缓解**：统一加 `errors="replace"`，解码失败时替换而非抛异常，行为从"崩溃"降级为"局部字符丢失"，不引入新的失败模式。
- **[风险] CI 新增的 `PYTHONIOENCODING=gbk` 真实子进程验证步骤增加 CI 时长** → **缓解**：只在 `windows-recorder-smoke.yml` 一个已存在的 Windows-only job 里追加步骤，不新建 job，增量时长有限（真跑 `setup.sh` 本身已是现有步骤的量级）。
- **[风险] `check_encoding_hygiene.py` 本身是新脚本，如果它自己打印 emoji 又没加前导，会自相矛盾地成为下一个假红源** → **缓解**：实现时该脚本自身从第一行起就带 reconfigure 前导（构造即满足自己的规则），CI 步骤里让它自检自身文件（目标 glob 覆盖 `hack/**`，包含它自己）。

## Migration Plan

- 无运行时部署步骤——本 change 只改仓内 Python 脚本与 CI 配置，通过正常 PR 合并生效；消费下游仓通过后续 `sdflow-init update` / `sdflow-upgrade` 获得修复后的 `hack/` 与 `openspec/workflow/tools/` 镜像。
- **回滚**：`git revert` 本 change 的合并提交，或运行 checkout `git checkout <上一已知良好 commit>` + 重跑 `setup.sh`（与本仓既有回滚约定一致，见 `CLAUDE.md`"dev/runtime checkout 纪律"）。

## Compliance

N/A——本仓无外部合规/隐私/安全审计要求适用于本次改动（纯工具链内部编码健壮性修复，无用户数据、无网络暴露面变化，见 `proposal.md` Compliance）。
