## Why

Windows(GBK/cp936) 环境下运行本仓任意 Python 脚本，只要 `print()`/`write_text()` 内容含 `✅🔴⚠✓` 等 GBK 编不出的字符，就会 `UnicodeEncodeError` 崩溃。这直接命中本仓自己的 `setup.sh` 四道机械一致性门（`sync_principles.py` / `gen_workflow_guide.py` / `check_async_branch_parity.py` / `check_tier_resolution_parity.py`）与 `sdflow-init` 的 `init.py`：门在**打印成功消息**那一行自爆，非零退出码被判成"有漂移"的假红——门的内容判断其实是对的，只是崩在报告结果那一刻。已在本机 Windows Git Bash 环境实测复现（`openspec/issues/buglist/2026-07-28-buglist.md` B23，P1）。危害方向是 fail-closed 假红而非误放行，但长期会训练用户忽略这四道门，真漂移时也不再被信任；且 `init.py` 的假红会让消费仓误以为 `sdflow-init update` 铺设失败。

## What Changes

- 全仓 **28** 个 Python 入口脚本（含 `if __name__ == "__main__":` 的脚本，`hack/**` + `sdflow-*/scripts/**` + `sdflow-init/assets/{hack,hooks,workflow/tools}/**`）顶部内联 4 行 stdout/stderr 自愈：`reconfigure(encoding="utf-8", errors="replace")`（skill 是独立分发单元，不能共享公共模块，与"四条通则"托管块同构：内联 + 脚本守）。`[spec-review-amendment]`
- **16 个**文本模式 `subprocess` 调用站点补 `encoding="utf-8", errors="replace"`（避免读中文 git commit message / JSON 等内容时 `UnicodeDecodeError`）——其中 15 个是直接 `text=True` 调用，另 1 个是 `_scan_pool` 通过 `**kwargs` 动态传入 `text=True`；**实际编辑点 15**，因 `ship_gate.py` 的两个站点共用 wrapper `_git_run`、塌缩为其函数体内一处。`[spec-review-amendment]`
- `Path.write_text()` 经复核**当前全部已带 `encoding="utf-8"`（0 处待补）**——初版写"2 处"系逐行 grep 看不见跨行参数造成的假阳性（见 `decision-memo.md` C8）。本 change 对该面只做**核实确认**并写进 spec 防回退，不做编辑。`[spec-review-amendment]`
- 新增 `hack/check_encoding_hygiene.py`，进 `setup.sh` 与现有四道机械门并列——**分别**检查前导块的三项契约（`sys.stdout` 调用 / `sys.stderr` 调用 / `errors="replace"`）在场性，**整文件匹配、不设行数窗口**，不做语义扫描；防止新脚本遗漏防护。`[spec-review-amendment]`
- `.github/workflows/windows-recorder-smoke.yml` 的 `paths:` 从 3 条扩到本次改动覆盖的全部脚本目录，并新增以 `PYTHONIOENCODING=gbk` 真实子进程方式跑 `setup.sh`、受影响脚本、**以及至少一条真正调用 `subprocess text=True` 站点的路径**的验证步骤；另加一条**不设 `PYTHONIOENCODING`、改由 Windows code page 决定编码**的用例（覆盖真实故障面，见 `decision-memo.md` D2 的补充）。`[spec-review-amendment]`
- `openspec/workflow/tools/*.py` 是 `sdflow-init/assets/workflow/tools/*.py` 的托管镜像副本，只改源文件，镜像由既有 `sdflow-init update` 机制自动刷新。

## Capabilities

### New Capabilities

- `encoding-hygiene`：本仓 Python 入口脚本在 Windows(GBK) 环境下的 stdout/stderr 编码安全契约——入口脚本 SHALL NOT 因打印 Unicode 字符崩溃，机械门 SHALL 准确报告真实一致性状态（不因编码问题产生假红），并由新增机械门（`hack/check_encoding_hygiene.py`）持续守护。这是本仓 `openspec/specs/` 里已有惯例（`determinism-guards`、`outside-voice-exec-integrity` 等内部质量契约）的同类新增，非用户可见产品功能。

### Modified Capabilities

（无——四道既有机械门与 `sdflow-init` init/update 的判定内容、退出码语义不变，只修正"判定过程中自身崩溃"这一实现缺陷；新契约作为独立能力域新增，不改写现有 spec 的需求。）

## Impact

- **受影响脚本**：`hack/*.py`（5 个含目标字符的入口 + 若干其余入口脚本一并纳入 D 检测范围）、`sdflow-architecture/scripts/*.py`、`sdflow-devenv/scripts/*.py`、`sdflow-done/scripts/roadmap_writeback_draft.py`、`sdflow-implement/scripts/impl_route.py`、`sdflow-init/scripts/init.py`、`sdflow-init/assets/{hack,hooks,workflow/tools}/**`、`sdflow-issues/scripts/*.py`、`sdflow-maintain/scripts/maintain_scan.py`、`sdflow-retro/scripts/*.py`、`sdflow-ship/scripts/ship_gate.py`。精确清单由新增的 `hack/check_encoding_hygiene.py` 自身检测输出产出（不手工枚举，见 `decision-memo.md` D5）。
- **受影响基础设施**：`setup.sh`（新增第五道机械门）、`.github/workflows/windows-recorder-smoke.yml`（paths 扩面 + 新验证步骤）。
- **技术域**：Markdown + Python 脚本为主的工具链仓库，不命中 `spec-checklists/domains` 的 backend·go / embedded·ml307c·esp32 / frontend 任一领域清单。
- **不受影响**：四道现有机械门与 `init.py` 的判定逻辑本身（漂移检测规则不变）；`openspec/workflow/tools/` 镜像内容（随源同步，无需手改）；macOS/Linux 行为（`reconfigure()` 在 UTF-8 locale 下是幂等 no-op）。

## Requirements Priority（TG-19：多条子需求）

- **P0**（止血，直接消除假红）：全部 **28** 个入口脚本的 reconfigure 前导注入（对应 What Changes 第 1 条）。`[spec-review-amendment]`
- **P1**（防再犯，面治而非点补）：新增 `hack/check_encoding_hygiene.py` 机械门 + **其常驻 pytest**（第 4 条）；CI 扩面 + 真实子进程验证步骤（第 5 条）。`[spec-review-amendment]`
- **P2**（同源加固，非本 bug 直接触发但同批修复更省心智负担）：`subprocess text=True` 的 encoding 补全（第 2 条）；`write_text()` 面的核实确认（第 3 条，无编辑）。`[spec-review-amendment]`

## Success Metrics

`[spec-review-amendment]` 🔴 **「`setup.sh` 退出码 0」不再作为判据**——`setup.sh` 全文无自身 `exit`，四道门全包在 `if ! …; then echo "⚠️"; fi` 里（`set -e` 对 `if` 条件位置的命令豁免）⇒ 其退出码**恒为 0**，与门是否报漂移完全解耦。该断言改之前就为真、改之后还是真，零信息量。

- 本机 Windows Git Bash 环境下 `bash setup.sh` 全程**输出不含 `UnicodeEncodeError` / `Traceback`**（这一半是真信号），且五道机械门准确报告真实一致性状态。
- `python3 sdflow-init/scripts/init.py update --root <目标>` 全程无 `UnicodeEncodeError` **且退出码为 0**——**此处退出码是有效判据**：`init.py:868` 的崩溃点未被 try/except 或 `if !` 吞，异常真会传到非零退出码。
- `hack/check_encoding_hygiene.py` 对全部目标入口脚本判定通过；其**常驻 pytest**（`hack/tests/test_encoding_hygiene.py`）覆盖正向 + 两条负向（缺前导的脚本被拦下；`sdflow-init/assets/workflow/tools/` 下的文件**未被排除规则连坐放过**）。
- `windows-recorder-smoke.yml` 新增的两类验证步骤（`PYTHONIOENCODING=gbk` 强制档 + 无该变量的 code-page 档）在 `windows-latest` 上通过，且**至少覆盖到一条真正调用 `subprocess text=True` 站点的路径**。

## Non-Goals

- 不改造脚本的业务逻辑或用户可见的判定规则——只修"判定过程崩溃"这一实现缺陷。
- 不引入跨 skill 的共享 Python 模块（违反"skill 是独立分发单元"惯例，见 `decision-memo.md` C4）。
- 不追求 `hack/check_encoding_hygiene.py` 能语义判断"某段字符串是否含 GBK 编不出的字符"——只做**前导块三项契约的**存在性检查（有界匹配），见 `decision-memo.md` D1 及其论证收窄段、"接受的边角"。`[spec-review-amendment]`
- 不处理本仓之外（其他消费 `sdflow-skills` 的下游项目自身脚本）的同类编码问题——那些项目通过后续 `sdflow-init update`/`sdflow-upgrade` 自然获得已修复的 `hack/` 与 `workflow/tools/`，不在本 change 范围内主动改造。

## Compliance

N/A——本仓无外部合规/隐私/安全审计要求适用于本次改动（纯工具链内部编码健壮性修复，无用户数据、无网络暴露面变化）。
