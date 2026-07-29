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

- **D1 检测机制选存在性检查（非语义扫描），但检查的是前导块的三项契约、不是一个子串** `[spec-review-amendment]` — 依据：`hack/check_encoding_hygiene.py` 对目标 glob 下每个含 `if __name__ == "__main__":` 的入口脚本，**分别**验证 ① `sys.stdout` 的 `reconfigure` 调用、② `sys.stderr` 的 `reconfigure` 调用、③ `errors="replace"` 参数三项均在场，不判断文件内容是否含 emoji。**砍掉的候选**：AST 语义扫描"风险字符是否流入 print()"——语法面无界（变量拼接/间接构造/多行 f-string 均可漏检），且本仓 `docs/sad/07` 已有同构反面教训（7 个 fail-closed 语法分支的补丁螺旋）。
  🔴 **论证范围的修正（spec-review Q1 · 跨模型镜 VOICE-3 + autoplan CEO-2 双向命中）**：本条**原先**用「语法面无界」一并论证了「连前导块自身的三项契约也不必验证」——**这是把两件事混为一谈**。按基准⑤自己的措辞（**「有界 ⇒ 可手写解析」**），被砍掉的候选（扫描 `print()` 数据流）确实无界，但**被检查的对象**（一个固定 4 行的前导块）是**有限、可机械验证的结构**，落在「有界」那一侧。∴ **结论不变（不做语义扫描），论证收窄，检测强度从 1 个断言提到 3 个**——仍是有界匹配，不是回到被砍掉的 AST 方案。
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
- **C6 真实需要前导的入口脚本 = 28 个（非 buglist 估算的 ~19，亦非本 memo 初版写的 27）** `[spec-review-amendment]` — 验证方式：按 D5 的目标 glob **穷举**，逐文件检查是否含 `if __name__ == "__main__":`；证据锚：glob 下共 **32** 个文件 = **28 个 ENTRY + 4 个 lib**(no `__main__`：`sad_schema.py` / `devenv_paths.py` / `devenv_schema.py` / `sdflow_issues_core/__init__.py`，后者由调用它的入口脚本进程级 `sys.stdout` 覆盖，无需重复注入)；`conftest.py` 命中字符经核实全部在模块级文档字符串内（非 print 调用），排除在外。
  🔴 **初版错在哪（spec-review M1 · autoplan ENG-3 + 接地镜 F1 双向命中）**：初版写「27 ENTRY + 5 lib = 32」，**总数 32 是对的、两个分项都是错的**——`sdflow-issues/scripts/migrate_legacy.py`（`:383` 有 `__main__`，在 glob 内，不被任何排除规则命中）被误计进了 lib 一侧。**一个算得通的等式掩盖了两个都错的数**，且本条是以「已验证的承重约束」形态写死的，不是待检测器确认的估算 ⇒ 会误导读者信以为真。D5 的「检测器输出驱动注入」在实现期能自我纠正，但**校对承重约束不能靠下游步骤兜底**。
- **C7 `subprocess text=True` 缺 `encoding=` 的真实调用站点 = 15，实际编辑点 = 14** `[spec-review-amendment]` — 验证方式：逐站点读取上下文核实是否已含 `encoding=`；证据锚：全 glob 内 `text=True` 原始命中 **20**，减去 **2 处非代码**（`sdflow-issues/scripts/sdflow_issues_core/__init__.py:1055` 注释、`sdflow-ship/scripts/ship_gate.py:464` —— 后者在 `run_git_bytes` 的 **docstring** 内）与 **3 处已带 `encoding=`**（`sdflow-issues/scripts/migrate_legacy.py:321`、**`sdflow-init/assets/hack/outside-voice-job.py:755`**、**`sdflow-issues/scripts/sdflow_issues_core/__init__.py:1057`** —— 后两处初版**遗漏未提**）= **15**。
  🔴 **站点数 ≠ 编辑点数**：`ship_gate.py` 的 `:334`/`:341` 两个站点调用的是同一个 wrapper `_git_run`，**塌缩为其函数体内一处编辑** ⇒ 真实编辑点 **14**。初版的「16」是笔误（其自身枚举恰好 15 条，枚举是对的）。三方计数曾报 16/15/14 的根因即在此。
- **C8 `write_text()` 缺 `encoding=` 的真实站点 = 0（初版写 2，系验证方法假阳性）** `[spec-review-amendment]` — 🔴 **初版的验证命令 `grep -rn "write_text(" --include="*.py" . | grep -v encoding` 是逐行 grep，看不见跨行的函数调用参数**。实际读取上下文：`hack/check_codex_efficacy_evidence.py:418-420` 的 `encoding="utf-8"` 在第 **420** 行、`sdflow-devenv/scripts/devenv_scaffold.py:59-60` 的在第 **60** 行——**两处都已经带了**。目标 glob 内其余全部 `write_text()` 站点（`gen_workflow_guide.py:116`、`sync_principles.py:168`、`devenv_scaffold.py:155/505/534`、`devenv_schema.py:286`、`impl_route.py:568`）亦全部已带 `encoding="utf-8"`。
  ⇒ **该 Requirement 的 write_text 那一半，当前代码已 100% 满足**，`tasks.md` §3.2 由「新增编辑」降为「核实确认」。**验证方式更正为**能感知多行调用的方式（AST，或 `grep -Pzo` 多行匹配）。**spec 的 Requirement 保留不动**——它约束的是目标态，「现在恰好满足」不等于「不必写进 spec」；没有 spec 就没有机械门守住它不回退。
- **C9 `PYTHONIOENCODING` 覆盖 `PYTHONUTF8`，buglist 否决方案①依据成立** — 验证方式：`PYTHONUTF8=1 PYTHONIOENCODING=gbk python3 -c "print(sys.stdout.encoding)"`；证据锚：本机实测输出 `gbk`（单独 `PYTHONUTF8=1` 时输出 `utf-8`，对照组确认变量确实生效）。
- **C10 `windows-recorder-smoke.yml` 现状不足以验证本次改动** — 验证方式：读 `.github/workflows/windows-recorder-smoke.yml`；证据锚：`paths:` 仅 3 条**（此处口径为「不含 workflow 文件自引用路径」；连自引用共 4 行）** `[spec-review-amendment]`（不含 `hack/**`、`sdflow-architecture/**`、`sdflow-devenv/**`、`sdflow-done/**`、`sdflow-implement/**`、`sdflow-init/assets/**`、`sdflow-maintain/**`、`sdflow-retro/**`、`sdflow-ship/**`），唯一 job 步骤只跑一个 pytest 文件、未曾以 `PYTHONIOENCODING=gbk` 方式真跑过任何脚本。

## 接受的边角

- **D 检测器验证前导块的三项契约（stdout / stderr 两处调用 + `errors="replace"`），但不验证 `encoding` 的值拼写是否为 `"utf-8"`** `[spec-review-amendment]`——概率低（4 行模板复制粘贴，非自由手写）、影响小（拼错会让 `reconfigure` 当场抛异常，而模板的 `except Exception` 会吞掉 ⇒ 退化为「前导块不生效」而非崩溃，等价于修复前的行为，不制造新的坏状态）、完美方案成本高（要断言值正确需真正执行每个脚本）。**接受**：D 守三项契约的**在场性**，E 的真实子进程执行验证兜底**有效性**，双层防御。
  > **本条相对初版已收紧**（spec-review Q1）：初版接受的是「只验证是否存在类似调用」（1 个子串），被跨模型镜指出**这一面是有界的、不该拿「无界语法面」豁免**。现接受的边角只剩「值的拼写」这一项。
- **库模块（4 个无 `__main__` 的文件）不在 D 的检测范围内** `[spec-review-amendment]`——如果未来它们被改造成可独立运行（新增 `__main__`），会自动进入检测范围而非遗漏；这不是遗留风险，是设计的自洽性，不需要额外动作。（数量由 5 更正为 4，见 C6。）

## 三镜代价

命中 TG-23（D1「检测机制选型」是 ≥2 合理方案的非显然设计选择）：

- **系统镜**：存在性检查规则简单、零新依赖；不保证检测的语义完备性，但运行时安全性不依赖检测完备——`reconfigure(errors="replace")` 兜底保证即使某脚本漏检也不会真崩，检测只是「强制养成习惯」的机械门，不是唯一防线。
- **用户镜**（本仓贡献者）：新脚本被机械门挡住必须补 4 行前导，增加轻量摩擦，但报错明确、修复成本低（复制模板）。
- **开发循环镜**：语义扫描方案的维护成本会随时间推移持续增长（新 emoji range、新的间接构造漏检模式不断被发现、不断打补丁）；存在性检查一次写完，之后靠机械门而非人工记忆挡住遗漏，长期心智负担更低。
- **主次判定**：系统简单性与开发循环长期可维护性是主要考量（避免重蹈 `07` change 补丁螺旋覆辙）；用户侧的轻量摩擦是次要、可接受的代价。
