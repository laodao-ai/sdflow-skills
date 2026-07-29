> `[spec-review-amendment]` 本文件已按阶段二 spec-review 的裁决整体修订（`spec-review-report.md`，24 条采纳）。
> 主要变化：入口脚本 27→**28**、subprocess 16→**15 站点 / 14 编辑点**、`write_text` 2 处→**0 处（改为核实确认）**、
> `ship_gate.py` 的修复点从调用点改到 `_git_run` 函数体内（照原样改会 `TypeError`）、
> 检测器判据从「前几行含某子串」改为「整文件 + 三项契约」、新增常驻 pytest、CI 断言拆分并补覆盖。

## 1. 检测器先行（`decision-memo.md` D5：用检测器输出驱动后续注入，不手工枚举）

- [x] 1.1 新增 `hack/check_encoding_hygiene.py`：扫描目标 glob（`hack/**/*.py` + `sdflow-*/scripts/**/*.py` + `sdflow-init/assets/{hack,hooks,workflow/tools}/**/*.py`），对每个含 `if __name__ == "__main__":` 的文件**分别**验证三项契约在场：① `sys.stdout` 的 `reconfigure` 调用 ② `sys.stderr` 的 `reconfigure` 调用 ③ `errors="replace"`；无 `--apply`，裸调用仿 `check_async_branch_parity.py` 模式（对应 Requirement: 新增机械门守护 reconfigure 前导块的存在性）`[spec-review-amendment]`
- [x] 1.1a 🔴 **判据 MUST 是整文件匹配，MUST NOT 设行数窗口** `[spec-review-amendment]`——实测目标脚本 `import sys` 位置跨度 5→191 行（`ship_gate.py:191` / `outside-voice-job.py:154` / `ff0-branch-guard.py:79` / `check_codex_efficacy_evidence.py:70`），任何小窗口都会把已正确修复的文件误判成缺失，即本 change 要消除的假红
- [x] 1.1b 🔴 **排除规则 MUST 锚定仓根** `[spec-review-amendment]`：排除 `**/tests/**`；排除 `openspec/workflow/tools/**` MUST 写成 `path.startswith("openspec/workflow/tools/")` 之类的锚定判据，**MUST NOT** 用 `*/workflow/tools/*` 这类任意深度通配——它会连坐排掉 `sdflow-init/assets/workflow/tools/` 下的 6 个**源**文件，导致门静默报「全部通过」
- [x] 1.2 脚本自身从第一行起即带 reconfigure 前导（自证满足自己的规则，`design.md` Risks 第 1 条）
- [x] 1.3 跑一遍 `python3 hack/check_encoding_hygiene.py`，记录当前缺失清单（即第 2 节要处理的真实文件集合，覆盖并核对是否等于实测的 **28** 个入口脚本）`[spec-review-amendment]`
- [x] 1.4 🔴 **新增常驻测试 `hack/tests/test_encoding_hygiene.py`** `[spec-review-amendment]`——五道门里另外四道**每一道**都有 `hack/tests/test_*.py` 直接 import 模块跑逻辑（`test_sync_principles.py:15` / `test_async_branch_parity.py:24` / `test_tier_resolution_parity.py:22` / `test_workflow_split.py:16` / `test_codex_efficacy_evidence.py:20`）；本门是本 change 新增的**唯一常驻防线**，MUST NOT 是唯一没有自测的那道。用例至少含：
      - 正向：临时 fixture 目录下带完整前导的入口脚本 → 退出码 0
      - 负向 A：缺前导 → 非零退出码 + 报出该路径
      - 负向 B：只有 `sys.stdout` 一处调用（缺 stderr）→ 非零 + 指明缺的是哪一项
      - 负向 C：缺 `errors="replace"` → 非零 + 指明缺项
      - 🔴 负向 D（守 1.1b）：`sdflow-init/assets/workflow/tools/` 路径下的文件缺前导 → **MUST 被检出**（证明排除规则没把源连坐排掉）
      - 边界：`import sys` 在第 190 行之后的文件带正确前导 → **MUST 判过**（守 1.1a，防窗口回归）

## 2. 28 个入口脚本注入 reconfigure 前导（对应 Requirement: 入口脚本 SHALL NOT 因 stdout/stderr 编码崩溃）

- [x] 2.1 按 1.3 的缺失清单，逐文件在顶部（`import sys` 之后、首个业务逻辑之前）插入 4 行前导：
      ```python
      for _s in (sys.stdout, sys.stderr):
          try: _s.reconfigure(encoding="utf-8", errors="replace")
          except Exception: pass
      ```
      注：该块落在**模块顶层裸作用域**（非 `__main__` 守卫内）是**有意为之**——lib 模块靠调用方的进程级 reconfigure 覆盖，放进守卫内会让被 import 的路径失去保护。其 blast radius 已记入 `design.md` Risks。
- [x] 2.2 `hack/*.py`（`sync_principles.py` / `gen_workflow_guide.py` / `check_async_branch_parity.py` / `check_tier_resolution_parity.py` / `check_codex_efficacy_evidence.py` 等）
- [x] 2.3 `sdflow-architecture/scripts/*.py`（`sad_lint.py` / `sad_scaffold.py`）
- [x] 2.4 `sdflow-devenv/scripts/*.py`（`devenv_lint.py` / `devenv_scaffold.py`）
- [x] 2.5 `sdflow-done/scripts/roadmap_writeback_draft.py`
- [x] 2.6 `sdflow-implement/scripts/impl_route.py`（注：其 `import sys` 在第 32 行、`from __future__ import annotations` 在第 27 行，顺序正确，插入语法安全；实测未发现任何目标文件顺序倒置）
- [x] 2.7 `sdflow-init/scripts/init.py` + `sdflow-init/assets/hack/outside-voice-job.py` + `sdflow-init/assets/hooks/ff0-branch-guard.py`
- [x] 2.8 `sdflow-init/assets/workflow/tools/*.py`（`anchor_lint.py` / `hr_tg_intersect.py` / `lens_metric_emit.py` / `outside_voice_guard.py` / `review_disposition_check.py` / `trivial_shape.py`——**只改源，不手改 `openspec/workflow/tools/` 镜像**，`decision-memo.md` C5/D4）
- [x] 2.9 `sdflow-issues/scripts/*.py`（`buglist.py` / `issues.py` / `todolist.py` / **`migrate_legacy.py`**）🔴 `[spec-review-amendment]` `migrate_legacy.py:383` 确有 `__main__`、在 glob 内、不被任何排除规则命中，初版漏枚举（并因此被误计进 lib 侧，见 `decision-memo.md` C6 修正段）
- [x] 2.10 `sdflow-maintain/scripts/maintain_scan.py`
- [x] 2.11 `sdflow-retro/scripts/*.py`（`lens_metric_aggregate.py` / `retro_report.py`）
- [x] 2.12 `sdflow-ship/scripts/ship_gate.py`（注：`import sys` 在第 191 行，被长模块 docstring 顶下去；插入点在其后）
- [x] 2.13 重跑 `python3 hack/check_encoding_hygiene.py`，确认缺失清单归零

## 3. subprocess 编码补全 + write_text 面核实（对应 Requirement: subprocess 文本解码与文件写入 SHALL 显式声明 UTF-8 编码）

- [x] 3.1 **15 个** `subprocess ... text=True` 调用站点补 `encoding="utf-8", errors="replace"`，**实际编辑 14 处** `[spec-review-amendment]`：
      | 文件 | 站点 | 编辑方式 |
      |---|---|---|
      | `sdflow-devenv/scripts/devenv_scaffold.py` | `:49`、`:324` | 各自就地 |
      | `sdflow-done/scripts/roadmap_writeback_draft.py` | `:301` | 就地 |
      | `sdflow-implement/scripts/impl_route.py` | `:433` | 就地 |
      | `sdflow-init/assets/hack/outside-voice-job.py` | `:357` | 就地（`:755` **已带**，跳过） |
      | `sdflow-init/assets/hooks/ff0-branch-guard.py` | `:125` | 就地 |
      | `sdflow-init/assets/workflow/tools/trivial_shape.py` | `:210` | 就地（**已有** `errors="replace"`，只补 `encoding=`） |
      | `sdflow-init/scripts/init.py` | `:567` | 就地 |
      | `sdflow-issues/scripts/issues.py` | `:1104`、`:1117`、`:1133`、`:1140` | 各自就地 |
      | `sdflow-retro/scripts/retro_report.py` | `:47` | 就地 |
      | **`sdflow-ship/scripts/ship_gate.py`** | `:334`、`:341` | 🔴 **MUST NOT 在这两行加参数** —— 见 3.1a |
- [x] 3.1a 🔴 **`ship_gate.py` 的正确修复点在 `_git_run` 函数体内，不在调用点** `[spec-review-amendment]`：`_git_run(root, args, text)` 定义在 `:304`，**三参定签、无 `**kwargs`**；`:334`/`:341` 是它的调用点而非 `subprocess.run` 本体 ⇒ 在那两行加 `encoding=` 会直接抛 `TypeError: _git_run() got an unexpected keyword argument 'encoding'`。正解 = 在 `:317-320` 的 `kwargs` 构造里加 `kwargs["encoding"] = "utf-8"`（那里**已有** `errors="replace"`，只缺 `encoding`）——**一处编辑覆盖两个调用点及未来任何新增调用方**。注意 `run_git_bytes`（`:472`）走 `text=False` 取原始字节，不受影响
- [x] 3.1b 对 15 个站点做一次「输出是否流入等值 / 去重 / 分类判断」的过目（Q2 拍板中档）`[spec-review-amendment]`——本次**新加** `errors="replace"` 的站点若流入判定路径，须在 `design.md` Risks 写明为何仍沿用；已确认 `ship_gate` 的保真比对走 `run_git_bytes`、`trivial_shape.py:210` 的 `errors="replace"` 是既有非新增
- [x] 3.2 **`write_text()` 面：核实确认，无编辑** `[spec-review-amendment]`——初版的「2 处待补」是假阳性（`check_codex_efficacy_evidence.py:418-420` 与 `devenv_scaffold.py:59-60` 的 `encoding="utf-8"` 都写在下一行，逐行 grep 看不见）。目标 glob 内**全部** `write_text()` 站点已带 `encoding="utf-8"`。本步 = 用**能感知多行调用**的方式（AST 或 `grep -Pzo`）复跑一次确认，并把该验证方式回写 `decision-memo.md` C8

## 4. `openspec/workflow/tools/` 镜像同步（对应 Requirement: 入口脚本 SHALL NOT 因 stdout/stderr 编码崩溃）

- [x] 4.1 跑 `python3 sdflow-init/scripts/init.py update --root .`，确认 `openspec/workflow/tools/*.py` 随源刷新，`diff -rq openspec/workflow/tools sdflow-init/assets/workflow/tools` 除 `tests/` 外零差异
- [x] 4.1a 🔴 **跑完 MUST `git diff` 核对副作用范围** `[spec-review-amendment]`：`init.py` 的 `run()`（`:807-864`）**不只**刷新 tools 镜像，还会注入/改写 `CLAUDE.md`/`AGENTS.md` 的 `sdflow:*` 托管块、改写 `openspec/INDEX.md`、跑 `handle_config()` 合并 `config.yaml`、合并 `.gitignore`、`ensure_global_hooks()`、`retire_hooks()`、`retire_deploy_files()`——**全在本 change 的 Non-Goals 之外**。确认除 `openspec/workflow/tools/**` 外无意外改动；若有，单独说明或剔出本 PR。（另注：`copy_bundle()` docstring `:202-214` 说非 `--dev` 是给消费仓用的、`--dev` 才是源仓 dogfood，而 `2026-07-todolist.md:148` T15 记着本仓用 `--dev` 有 2 条已知假警告——本 change 不解决该历史分歧，仅要求核对 diff）

## 5. `setup.sh` 接线新机械门（对应 Requirement: 机械门 SHALL 准确报告真实一致性状态，不因编码问题产生假红）

- [x] 5.1 在 `setup.sh` 现有四道门之后，独立接入 `hack/check_encoding_hygiene.py`（不挂在其它门的条件分支下，同 `check_async_branch_parity.py` 的独立守卫写法）
- [x] 5.2 本机 `bash setup.sh` 全程**输出不含 `UnicodeEncodeError` / `Traceback`**，五道机械门全部报告真实状态 `[spec-review-amendment]`
      🔴 **MUST NOT 用「`setup.sh` 退出码 0」当判据**：`setup.sh` 全文无自身 `exit`，四道门全包在 `if ! …; then echo "⚠️"; fi` 里，`set -e` 对 `if` 条件位置的命令豁免 ⇒ 退出码**恒为 0**，与门状态解耦（`mechanical-gates.yml` 注释亦自陈 warn-only）。该断言改前改后都为真，零信息量
- [x] 5.3 补新门的**失败输出契约** `[spec-review-amendment]`：仿三道同侪门给出 `修：` 行——逐文件列「路径 + 缺哪一项契约」+ 指向 `CLAUDE.md` 里模板的规范住所（见 8.1）

## 6. CI 扩面与真实子进程验证（对应 Requirement: 机械门 SHALL 准确报告真实一致性状态，不因编码问题产生假红）

> 🔴 **本节所有新增步骤 MUST 显式 `shell: bash`** `[spec-review-amendment]`——`windows-latest` 的 `run:` 默认 shell 是 pwsh，不认 `VAR=val cmd` 这种 POSIX 内联环境变量前缀语法（会把 `PYTHONIOENCODING=gbk` 当程序名报错）；现有 workflow 步骤都没有 `shell:` 键。Windows GitHub-hosted runner 自带 Git Bash，可用。

- [x] 6.1 `.github/workflows/windows-recorder-smoke.yml` 的 `paths:` 从 3 条扩到本次改动覆盖的全部脚本目录（`hack/**`、`sdflow-architecture/scripts/**`、`sdflow-devenv/scripts/**`、`sdflow-done/scripts/**`、`sdflow-implement/scripts/**`、`sdflow-init/assets/**`、`sdflow-issues/**` 已含、`sdflow-maintain/scripts/**`、`sdflow-retro/scripts/**`、`sdflow-ship/scripts/**`）
- [x] 6.2 新增步骤：`shell: bash` + `PYTHONIOENCODING=gbk bash setup.sh` 真实子进程运行，**断言输出不含 `UnicodeEncodeError` / `Traceback`** `[spec-review-amendment]`（**退出码断言剔除**，理由同 5.2）
- [x] 6.3 新增步骤：`shell: bash`；`--root` 指向 CI 内从空目录开始创建的 probe（先 `mkdir -p` + `git init`，再用 `init.py init` 铺设），随后执行 `PYTHONIOENCODING=gbk python3 sdflow-init/scripts/init.py update --root "$RUNNER_TEMP/probe"` 并断言退出码 0 `[spec-review-amendment]`。`update` 只接受已铺设项目，probe MUST NOT 在未 `init` 时直接调用 `update`
      注：**此处退出码是有效判据**——`init.py:868` 的崩溃点未被 try/except 或 `if !` 吞，异常真会传到非零退出码（与 6.2 的情况相反）
- [x] 6.4 🔴 **新增步骤：真正跑到 `subprocess text=True` 站点** `[spec-review-amendment]`——追调用图确认：6.2 跑的 `setup.sh` 只调那四道门，而四道门**全都不调 subprocess**；6.3 跑的 `init.py update` 也够不着（`init.py:567` 在 `_git_root_or_dot()` 内，只有 `mode == "config-lint"` 走得到，`run()` 从不调它）⇒ **现状下 15 处修复零 CI 覆盖**。补 `shell: bash` + `PYTHONIOENCODING=gbk` 下各跑一次 `sdflow-issues/scripts/issues.py`、`sdflow-retro/scripts/retro_report.py`、`sdflow-ship/scripts/ship_gate.py` 的只读子命令（三者合计覆盖 15 站点中的 7 个）+ 一个稳定输出中文与非法 UTF-8 字节的夹具子进程，断言不崩且替换行为符合预期
      （不追求 15/15——按通则④，造 15 份非 UTF-8 夹具的完美成本过高，7/15 + 夹具是成本大幅降、结果可接受的次优解）
- [x] 6.5 🔴 **新增步骤：不设 `PYTHONIOENCODING` 的真实故障面用例** `[spec-review-amendment]`——`PYTHONIOENCODING` 会**主动覆盖**标准流编码，∴ 6.2/6.3/6.4 测的是「人为强制 GBK 的进程」，而不是 Windows **无该变量**时由控制台 / 重定向管道 / locale 决定编码的路径（还可能掩盖环境继承问题）。补：`shell: bash` + 移除该变量 + `chcp 936` 设 code page；控制台路径直接运行会输出中文/emoji 且以退出码 fail-closed 的 `check_encoding_hygiene.py`，重定向路径运行 `setup.sh` 并显式 grep 日志，**控制台与重定向管道至少各一**
      注：**本条使 `windows-latest` 真正承重**——该路径只在 Windows 上存在，不能挪去 Linux runner

## 7. 回归验证

- [ ] 7.1 本仓既有 pytest 套件全绿（`pytest`，仓根 rootdir）
  - 未完成说明：当前 Windows / Python 3.14 环境下全量 `pytest` 有 2 项收集错误；相关测试文件相对本地 `main` 的 merge-base `3b4f838b99f2ccd3bf7a246e8ab675a9b6c40943` 未变化，确认不是本 change 引入；本 change 相关测试与 GBK setup 集成验证已通过。
      注：该断言**不构成对本 bug 的覆盖**（pytest 的 capsys/capfd 用内存 buffer 替换 `sys.stdout`，规避了这个 bug class，见 `decision-memo.md` D2）；它守的是「本次改动没有打坏别的东西」
- [x] 7.2 `openspec validate "fix-windows-encoding-crash" --strict --type change` 通过
- [x] 7.3 ~~人工核对负向用例~~ → **已升为常驻测试，见 1.4** `[spec-review-amendment]`（一次性人工核对跑完即删临时脚本，等于把本 change 唯一常驻防线的自测扔掉；改为 `hack/tests/test_encoding_hygiene.py` 永久保留）

## 8. 模板住所与文档 `[spec-review-amendment]`

- [x] 8.1 在 `CLAUDE.md` 的「修改本仓库的注意」段补一条：新增 Python 入口脚本须带 4 行 reconfigure 前导，否则第五道机械门会拦；附模板原文
      （理由：模板目前只写在本文件里，而 change 归档后 tasks 不再是活文档 ⇒ 下一个写脚本的人无处可查）
- [x] 8.2 `design.md` Migration Plan 已更正交付面为三条路径（`hack/**` 随仓库、各 skill `scripts/**` 随 `setup.sh:60-77` 的 `rm -rf`+`cp -r`/symlink、bundle 走 `sdflow-init update`）——实现时核对无遗漏

## 9. 记 todo（不阻塞本 change）`[spec-review-amendment]`

- [x] 9.1 `setup.sh` 里沿袭的 `command -v python3` 写法不一致（存量问题，非本 change 引入）→ 记入 `openspec/issues/todolist/`

## 测试覆盖图（TG-18）`[spec-review-amendment]`

| Code Path | 测试类型 | 对应任务 |
|---|---|---|
| 28 个入口脚本 stdout/stderr reconfigure | `check_encoding_hygiene.py` 三项契约检查（机械门） | 1.1, 1.3, 2.13 |
| `check_encoding_hygiene.py` 自身检测逻辑 | **常驻 pytest**（正向 + 4 条负向 + 1 条窗口边界） | **1.4** |
| 排除规则未连坐排掉 bundle 源 | 常驻 pytest 负向 D | **1.4** |
| 「无行数窗口」不回归 | 常驻 pytest 边界用例（`import sys` 在 190 行后） | **1.4** |
| `subprocess text=True` 解码（15 站点 / 14 编辑点） | **CI 真实子进程直达该路径 + 非法字节夹具**（7/15 覆盖）；余下靠 review | **6.4** |
| `ship_gate.py` 的 `_git_run` 单点修复 | 既有 `sdflow-ship/tests/` + 6.4 的 ship_gate 只读子命令实跑 | 3.1a, 6.4, 7.1 |
| `write_text()` 编码 | **核实确认**（AST / 多行 grep），当前已全满足 | 3.2 |
| 四道既有机械门 + `init.py` 在 GBK 环境下的真实行为 | CI 真实子进程（`PYTHONIOENCODING=gbk` 强制档） | 6.2, 6.3 |
| **Windows 真实 code-page 路径（无 `PYTHONIOENCODING`）** | CI 真实子进程（控制台 + 重定向管道各一） | **6.5** |
| `setup.sh` 五道门整体接线 | 本机 `bash setup.sh` 全跑（**判据 = 输出无异常，非退出码**）+ CI 6.2 | 5.2, 6.2 |
| 前导块 `except Exception` 触发时的行为 | ⚠️ **无自动化覆盖**（已知边角，`design.md` Risks 显式记录） | — |
