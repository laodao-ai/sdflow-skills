---
schema_version: 1
change: fix-windows-encoding-crash
branch: feat/fix-windows-encoding-crash
generated_at: 2026-07-28T13:29:53+00:00
decision_hash: ebe58f30ec71
---

# 决策纪要 · fix-windows-encoding-crash

## 目标态

Windows(GBK) 环境下运行 sdflow 仓内任意 Python 脚本（含 `setup.sh` 四道机械门 + `sdflow-init` init/update）都不再因打印 Unicode 字符发生 `UnicodeEncodeError` 崩溃或产出乱码文件；新增脚本被机械门挡住、不会遗漏防护。

## 拍板决策

- **D1 检测机制选存在性检查（非语义扫描）** — 依据：`hack/check_encoding_hygiene.py` 只检查目标 glob 下每个含 `if __name__ == "__main__":` 的入口脚本、前几行内是否存在 `reconfigure(encoding=` 调用，不判断文件内容是否含 emoji。有界字符串匹配，对齐本仓 CLAUDE.md 基准⑤"机械化 ≠ 手搓解析器"；**砍掉的候选**：AST 语义扫描"风险字符是否流入 print()"——语法面无界（变量拼接/间接构造/多行 f-string 均可漏检），且本仓 `docs/sad/07` 已有同构反面教训（7 个 fail-closed 语法分支的补丁螺旋）。
- **D2 CI 验证走真实子进程，不靠 pytest 内跑** — 依据：pytest 的 capsys/capfd 用内存 buffer 替换 `sys.stdout`，不触发真实 OS 管道编码，无法复现本 bug（已用「崩的是 stdout 被管道捕获时」的既有诊断印证）；**砍掉的候选**：扩大 pytest 覆盖率顺带触发这些 print——pytest capture 机制本身规避了这个 bug class，覆盖率再高也测不出来。CI 步骤须显式 `PYTHONIOENCODING=gbk python3 <script>` / `PYTHONIOENCODING=gbk bash setup.sh` 真跑。
- **D3 修复范围 = buglist B23 原方案 A+B+C+D+E 全做**（人已确认），change 名 `fix-windows-encoding-crash`。
- **D4 `openspec/workflow/tools/*.py` 只改源，不手改镜像副本** — 依据：`diff -rq` 确认它与 `sdflow-init/assets/workflow/tools/*.py` 逐字节相同（除 `tests/`），由 `sdflow-init update` 的 `copy_bundle()` 托管刷新；手改镜像会被下次 update 覆盖，形成假修复。
- **D5 先写 D 检测器、后驱动 A 的注入** — 依据：人工 grep 圈定的"~19 个脚本"与实测的 27 个入口脚本有偏差（见 C6），说明手工枚举不可靠；正确顺序是先落地 `check_encoding_hygiene.py`（--check-only，无 --apply，仿 `check_async_branch_parity.py` 的裸调用模式而非 `sync_principles.py` 的 --check/--apply 模式——各脚本注入点格式可能有细微差异，交给实现阶段逐文件核验，不做批量自动写入），再拿它的失败列表作为 A 步骤真正要改的清单，自证完整覆盖。

## 承重约束

- **C1 真实 Windows(GBK) 环境复现崩溃** — 验证方式：本机 `python3 -c "print('test ✅ done')"`；证据锚：本机实测 `UnicodeEncodeError: 'gbk' codec can't encode character '✅'`，`sys.stdout.encoding=gbk`，`locale.getpreferredencoding()=cp936`（此前 buglist 只有 mac 模拟证据，本次是首次真机验证）。
- **C2 reconfigure 前导块实测修复有效** — 验证方式：同一崩溃语句加 4 行 `for s in (sys.stdout, sys.stderr): s.reconfigure(encoding="utf-8", errors="replace")` 后重跑；证据锚：本机实测 exit 0，正常输出 `test ✅ done`。
- **C3 Python 版本兼容无问题** — 验证方式：`grep -n "python-version\|matrix" .github/workflows/mechanical-gates.yml`；证据锚：CI matrix 最低 Python 3.9（`ubuntu-24.04, python: "3.9"`），`TextIOWrapper.reconfigure()` 自 Python 3.7 起可用。
- **C4 跨 skill 无法共享模块，inline 复制是唯一分发路径** — 验证方式：`grep -rn "sys.path.insert\|sys.path.append" sdflow-*/scripts/*.py`；证据锚：全部命中都只 insert 脚本自身所在目录，无一处导入其它 skill 或共享 `hack/` 模块。
- **C5 `openspec/workflow/tools/` 是 `sdflow-init/assets/workflow/tools/` 的字节级镜像** — 验证方式：`diff -rq openspec/workflow/tools sdflow-init/assets/workflow/tools`；证据锚：仅 `tests/` 目录差异（未部署），其余文件零差异。
- **C6 真实需要前导的入口脚本 = 27 个（非 buglist 估算的 ~19）** — 验证方式：对含 GBK 编不出字符的文件逐个检查是否含 `if __name__ == "__main__":`；证据锚：命令输出见本轮 grill 记录，27 个 ENTRY + 5 个 lib(no `__main__`)（后者由调用它的入口脚本进程级 `sys.stdout` 覆盖，无需重复注入）；`conftest.py` 命中字符经核实全部在模块级文档字符串内（非 print 调用），排除在外。
- **C7 `subprocess text=True` 缺 `encoding=` 的真实站点 = 16（非 buglist 估算的 18）** — 验证方式：逐站点读取上下文核实是否已含 `encoding=`；证据锚：排除 2 处纯注释引用（`sdflow-issues/scripts/sdflow_issues_core/__init__.py:1055`、`sdflow-ship/scripts/ship_gate.py:464`）与 1 处已带 `encoding="utf-8"`（`sdflow-issues/scripts/migrate_legacy.py:321`）。
- **C8 `write_text()` 缺 `encoding=` 的真实站点 = 2，与 buglist 一致** — 验证方式：`grep -rn "write_text(" --include="*.py" . | grep -v encoding`；证据锚：`hack/check_codex_efficacy_evidence.py:418`、`sdflow-devenv/scripts/devenv_scaffold.py:59`。
- **C9 `PYTHONIOENCODING` 覆盖 `PYTHONUTF8`，buglist 否决方案①依据成立** — 验证方式：`PYTHONUTF8=1 PYTHONIOENCODING=gbk python3 -c "print(sys.stdout.encoding)"`；证据锚：本机实测输出 `gbk`（单独 `PYTHONUTF8=1` 时输出 `utf-8`，对照组确认变量确实生效）。
- **C10 `windows-recorder-smoke.yml` 现状不足以验证本次改动** — 验证方式：读 `.github/workflows/windows-recorder-smoke.yml`；证据锚：`paths:` 仅 3 条（不含 `hack/**`、`sdflow-architecture/**`、`sdflow-devenv/**`、`sdflow-done/**`、`sdflow-implement/**`、`sdflow-init/assets/**`、`sdflow-maintain/**`、`sdflow-retro/**`、`sdflow-ship/**`），唯一 job 步骤只跑一个 pytest 文件、未曾以 `PYTHONIOENCODING=gbk` 方式真跑过任何脚本。

## 接受的边角

- **D 检测器不验证 reconfigure 前导块内容是否完全正确**（比如漏写 `errors="replace"` 或拼错 `encoding` 值），只验证"是否存在类似调用"——概率低（4 行模板复制粘贴，非自由手写）、影响小（`reconfigure(encoding="utf-8")` 本身已覆盖仓内几乎所有真实字符，`errors="replace"` 只是极端兜底）、完美方案成本高（要做到语义完全正确需要真正执行每个脚本验证）。**接受**：D 只做存在性检查防遗漏，E 的真实子进程执行验证兜底正确性，双层防御，不单独为"防止手滑写错前导内容"再建一层检测。
- **库模块（5 个无 `__main__` 的文件）不在 D 的检测范围内**——如果未来它们被改造成可独立运行（新增 `__main__`），会自动进入检测范围而非遗漏；这不是遗留风险，是设计的自洽性，不需要额外动作。

## 三镜代价

命中 TG-23（D1「检测机制选型」是 ≥2 合理方案的非显然设计选择）：

- **系统镜**：存在性检查规则简单、零新依赖；不保证检测的语义完备性，但运行时安全性不依赖检测完备——`reconfigure(errors="replace")` 兜底保证即使某脚本漏检也不会真崩，检测只是「强制养成习惯」的机械门，不是唯一防线。
- **用户镜**（本仓贡献者）：新脚本被机械门挡住必须补 4 行前导，增加轻量摩擦，但报错明确、修复成本低（复制模板）。
- **开发循环镜**：语义扫描方案的维护成本会随时间推移持续增长（新 emoji range、新的间接构造漏检模式不断被发现、不断打补丁）；存在性检查一次写完，之后靠机械门而非人工记忆挡住遗漏，长期心智负担更低。
- **主次判定**：系统简单性与开发循环长期可维护性是主要考量（避免重蹈 `07` change 补丁螺旋覆辙）；用户侧的轻量摩擦是次要、可接受的代价。
