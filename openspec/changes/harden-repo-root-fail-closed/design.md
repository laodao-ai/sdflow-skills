## Context

三份 recorder 各自内联一份逐字同款的 `repo_root(start)`（`determinism-guards` 明文要求的镜像
helper，剥 docstring 后 AST 全等已实测确认）。它调用 `git rev-parse --show-toplevel` 并**直接
返回 stdout**，无任何校验：

```
repo_root(start)
   └─ subprocess.run(["git","rev-parse","--show-toplevel"], check=True)
        ├─ 抛异常 ──────────────────► return abspath(start)      ← 既有回落，安全
        └─ rc=0 ────────────────────► return out.stdout.strip()  ← 零校验，本次缺口
                                            │
        ┌───────────────────────────────────┘
        ▼  该值被 14 个调用点当可写根拼路径，落到三处无条件建目录的写入器：
   recorder_lock   issues.py:200   os.makedirs(dirname(path), exist_ok=True)
   atomic_write         :1093      os.makedirs(d, exist_ok=True)
   atomic_write_bytes   :1114      os.makedirs(directory, exist_ok=True)
                                            │
                                            ▼
                        任意字符串 → 目录树被静默具现，无报错、无日志
```

**实证 PoC**：`test_reindex_cli_non_string_id_...` monkeypatch 全局 `subprocess.run` 后，
`repo_root` 拿到整段 scan JSON 当根（JSON 内嵌的 `/` 被当路径分隔符），在 cwd 建出 4 棵目录树；
`recorder_lock` 的 `finally` 随后 unlink 掉 lock 文件，**空目录树留存**——因而对 `git status`
隐形，在仓根躺了两天无人发现。

同一 PoC 暴露该测试假绿：其 `preserves_derived_bytes` 断言成立的真实原因是 reindex 全程没访问
`tmp_path`，而非派生字节受保护。

## Goals / Non-Goals

**Goals:**
- `repo_root` 对外部进程输出 fail-closed：git 违反契约时**响亮失败**，只有「非 git 仓库」这类
  正常场景才回落 `abspath(start)`。
- 三份逐字同步，保持 `determinism-guards` 的 AST 三向等价守护为绿。
- 消除假绿测试，使 `preserves_derived_bytes` 承诺可被变异验证证伪。
- 一份仓根 `conftest.py` 的 cwd 泄漏回归断言，覆盖全仓，防同类副作用再次隐形。

**Non-Goals:**
- 不重构镜像机制（`determinism-guards` 的既定设计，D4 隔离要求）。
- 不动 `sdflow-init/scripts/init.py:553` 的 `_git_root_or_dot()`（不属镜像 roster）。
- 不在 helper 内做进程终止（`sys.exit` / `_die`）——抛异常交调用方处置，见 ADR-4。
- 不把「非 git 仓库」也变成失败——那是正常用法，回落保持不变，见 ADR-1。

## Decisions

### ADR-1：按「git 是否履行契约」分流，异常态不回落

**决策**：

```
git 抛异常 / rc≠0            ──► abspath(start)     # 正常场景，不变
git rc=0 且 isabs 且 isdir   ──► 该路径              # 正常路径
git rc=0 但值不可用           ──► raise ValueError   # 违反契约，响亮失败
```

**备选**：三种情况统一回落 `abspath(start)`。

**理由**：两种失败的语义根本不同——「非 git 仓库」是**正常用法**（常见），「git rc=0 却给出
非目录」是**git 违反自身契约**（实测在真实 git 姿势下不可达，bare repo 是 rc=128 走异常分支）。
把异常当正常处理正是静默失败的定义，而消灭静默失败是本变更的全部意义。

统一回落还有一个**具体且严重**的后果：回落值是 `abspath(start)`，默认 `start="."` ⇒ 坏值会让
recorder 在 **cwd** 建出一棵**看起来完全合法**的 `openspec/issues/` 树并打印「已重建」、exit 0
（实测：非 git 仓库下跑 `reindex` 即此行为）。这比现状的垃圾 JSON 目录名**更隐蔽**——垃圾名扎眼
到能被人在文件树里一眼发现，`openspec/issues/` 不会。

**实测影响面**（分流补丁 spike，三份同改后还原）：三份 recorder + hack 全套件
`478 passed, 2 skipped, 4 failed`，红的只有本变更本就要改的 4 个用例；非 git 仓库下 `reindex`
仍 exit 0 正常完成；仓内 `scan` 正常。

**代价**：`repo_root` 从「永不失败」变为「可能抛异常」，契约变化需在 docstring 明写。

### ADR-2：校验判据是 `isabs` **与** `isdir`，两者缺一不可

**决策**：`top and os.path.isabs(top) and os.path.isdir(top)`。

**备选**：只用 `isdir`；或只用 `isabs`。

**理由**：这**不是二选一**——两个判据挡的是不同的东西：

- 只用 `isabs`：挡不住「绝对路径但不存在」（已删除的仓、多行输出的首行）。
- 只用 `isdir`：**可被 cwd 绕过**。`os.path.isdir` 对相对路径按当前工作目录解析，坏值只要在
  cwd 下恰好对应一个真实目录就会通过校验。

第二条不是理论风险，是**实测事实**：`isdir`-only 的 spike 在仓根 cwd 下 4 passed、在空目录 cwd
下 4 failed——**同一份代码两种结果**。原因是本 bug 自己产出的 4 棵垃圾目录树就躺在仓根，
使坏值 `{"bugs": ...openspec/issues/...` 相对解析后命中真实目录。**这个 bug 的产物让针对它的
校验失效，形成自我掩盖闭环。** 加上 `isabs` 后差异消失：两种 cwd 均拒绝、均 0 残留。

**代价**：`repo_root` 从纯字符串处理变为带 IO 的函数；负例测试 MUST NOT mock `os.path.isdir`
（mock 掉判据本身等于没测）。

### ADR-4：坏 root 抛 `ValueError`，不在 helper 内 `sys.exit`

**决策**：校验失败时 `raise ValueError(...)`，由调用方 `main()` 转为诊断 + 退出码。

**备选**：helper 内 `sys.exit(2)`；或调用既有 `_die`（exit 1）。

**理由**：
- **零新增机制**：三份 `main()` 都已有 `except ValueError → stderr + SystemExit(2)` 的统一出口
  （`issues.py:2339-2341` / `buglist.py:1607-1609` / `todolist.py:1581-1583`），且
  `args.root = repo_root(args.root)` 的调用点都在该 try 块内（`2324` / `1594` / `1568`）。
  抛出即自动得到「exit 2 + stderr」，无需在 helper 里手搓进程控制。
- **语义对齐**：exit 2 在这套脚本里就是「输入非法」，坏 root 正属此类；`_die` 的 exit 1 会错位。
- **保持可测**：`repo_root` 有 4 个既有单测直接当纯函数调用并断言返回值
  （`test_issues.py:322/331/341/349`）；`pytest.raises(ValueError)` 比 `SystemExit` 更贴库函数
  契约，也不会在直接调用场景单方面杀进程。
- **不破分层**：三份脚本现有架构中**没有任何 helper 内部 `sys.exit`**——终止进程是 main/cmd 层
  职责。往三向镜像 helper 里塞 `sys.exit` 会让它在任何 import 场景下都能杀进程。

**代价**：`repo_root` 的失败依赖「调用方在 try 内调用」。三份 main 当前都满足，但将来在 try 外
新增调用点会退化为裸 traceback ⇒ 由 tasks 的调用点断言测试守住。

### ADR-3：cwd 泄漏断言 = 仓根**单一份** `conftest.py` 的 autouse fixture

**决策**：在仓库根新建一份 `conftest.py`，autouse fixture 对比每个用例运行前后的 cwd 条目集。

**备选**：三份 recorder 的 `tests/` 各建一份 conftest；或写独立扫描脚本挂 CI。

**理由**：
- pytest 沿**测试文件的祖先目录**收集 conftest（实测确认——本轮探针最初的假阴性正源于把
  conftest 放在 cwd 而非祖先目录）⇒ 仓根一份天然覆盖全部 12 个 skill，无需任何注册。
- **三份副本会构成第四组无守护镜像**：三份 recorder 的 `tests/` 当前均无 conftest，新建三份
  内容相同的文件却不在 `determinism-guards` 的 AST roster 内 ⇒ 漂移无人拦。本变更治的正是
  「镜像 + 漂移」，不该在修它的同时再造一组。
- **面治**：普查显示当前仅 `sdflow-issues` 泄漏，但目标态该问「哪个 skill 的测试**可能**往 cwd
  写」——答案是任何一个。一份根级把整个面盖住，边际成本为零。
- 独立扫描脚本只能报「套件跑完后多了东西」，丢失用例归属；fixture 能直接指认是哪个用例。
- **误报风险已实测排除**：12 个 skill + hack 各自在干净目录跑完均 0 残留 ⇒ 仓内不存在「合法
  往 cwd 写」的测试。

**代价**：仓库首次出现根级 pytest 文件，`CLAUDE.md` 中「没有根级 pytest 配置——测试各 skill
自包含」一句须同步改（否则文档与事实漂移，正是本变更在治的病）。对 skill 自包含的让步为零：
`setup.sh` 分发 `SKILL.md` / `scripts/` / `assets/`，`tests/` 本就不进分发。

## 失败模式表（TG-08：外部依赖 git）

| 失败模式 | 当前行为 | 目标行为 | 可观测信号 |
|---|---|---|---|
| git 不存在 / 非 git 仓库 | 抛异常 → `abspath(start)` | 不变 | 无（正常场景） |
| git rc≠0（bare repo 等，实测 rc=128） | 抛异常 → `abspath(start)` | 不变 | 无（正常场景） |
| git rc=0，stdout 为空 | 返回 `""` → 拼路径退化为相对 cwd | `ValueError` → exit 2 | stderr 诊断 |
| git rc=0，stdout 非绝对路径 | **静默建垃圾目录树**（cwd 下） | `ValueError` → exit 2 | stderr 诊断 |
| git rc=0，stdout 绝对但非目录（已删除的仓） | **静默建垃圾目录树** | `ValueError` → exit 2 | stderr 诊断 |
| git rc=0，stdout 为合法绝对目录 | 返回该目录 | 不变 | 无 |
| 坏值恰好命中 cwd 下同名目录 | 静默放行 | `ValueError`（`isabs` 拦） | stderr 诊断 |
| 调用方注入的 `subprocess.run` 被 mock 污染（测试） | **静默建垃圾目录树** | `ValueError` → exit 2 | stderr 诊断 + cwd 泄漏断言 |

## 可观测性（TG-08）

诊断信息由 `ValueError` 的消息承载，经三份 `main()` 既有的 `except ValueError` 出口落 **stderr**，
进程以 exit code 2 结束。消息 MUST 含：被拒值（**截断至 80 字节**，避免把整段污染输出灌进日志）、
`cause:`（git rc=0 但输出不是既存的绝对路径目录）、`fix:`（检查 git 包装脚本 / alias 是否向
stdout 多写内容）——与 recorder 既有诊断的 `ERROR: ... ; cause: ...; fix: ...` 格式一致。

MUST NOT 写入 stdout：recorder 的 stdout 是机器可读契约（`scan --json` 的消费方会解析它），
污染 stdout 会把这次修复变成新的解析故障。

**退出码可区分性**：坏 root 与坏 scan id 都产生 exit 2 ⇒ 相关测试 MUST 断言 stderr 的具体
诊断内容，MUST NOT 仅凭退出码判定通过（否则「在更早的关口崩了」会被误判为「测中了目标」——
本变更修复的假绿正是这个形状）。

## Risks / Trade-offs

- **[三份漂移]** 只改一份或改得不逐字一致 → determinism-guards 测试变红。
  **缓解**：这正是守护的设计意图，红即拦截；tasks 中三处修改列为同一任务，不拆。
- **[isdir 引入 IO]** 单元测试若在无真实目录的环境构造用例会失败。
  **缓解**：负例测试用 `tmp_path` 下真实存在/不存在的路径构造，不 mock `os.path.isdir`
  （mock 掉判据本身 = 测了个寂寞）。
- **[自我掩盖]** 仓根现存的 4 棵垃圾目录树会让 `isdir` 判据被绕过（ADR-2 实测）。虽然
  `isabs` 已堵住这条路径，但**任何在被污染环境里得到的绿都不可信**。
  **缓解**：清理提到 Task 0，先于一切实现与验证。
- **[try 外调用点]** 将来在 `except ValueError` 之外新增 `repo_root` 调用点，异常会退化为
  裸 traceback。
  **缓解**：docstring 明写该契约 + 三份各加一条「main 的调用点在 try 内」的断言测试。
- **[修完假绿测试后覆盖仍不足]** 修好 root 解析后，该测试才第一次真正执行 reindex 的写入路径，
  可能暴露此前从未被执行过的分支。
  **缓解**：Success Metric 2 用变异验证兜底（故意写入 → 必须变红）；若修复后出现新失败，
  按「执行中撞到与本次功能相关的 bug 立即 fold」处理，不 defer。

## Migration Plan

无数据迁移、无外部接口变更。落地顺序：

1. 三份 `repo_root` 同步改 + 各自负例测试（同一提交，保证 AST 等价守护不中间态变红）。
2. 修假绿测试 + 变异验证。
3. 加 cwd 泄漏 fixture。
4. 回归确认垃圾树未再生（清理已在步骤 0 完成，此处只验「不会重新长出来」）。
5. CLAUDE.md 登记 PV 规则指针。

**回滚**：`git revert` 单个提交即可，无状态残留。

## Open Questions

无。proposal 假设列表中的 4 条已全部验证完毕。

## Compliance

- **BASE-06 失败模式表**：见上「失败模式表」节（TG-08 命中）。
- **BASE-11 可观测性**：见上「可观测性」节（TG-08 命中）。
- **BASE-12 决策记录**：ADR-1 / ADR-2 / ADR-3 / ADR-4（TG-23 命中）。
- **BASE-14 假设列表**：见 proposal「假设」节，4 条均已验证。
- **DOC-1 正文即最终态**：本文不含演进史；PoC 描述属当前事实证据，非考古层。
- **PV 规则 2「引用即打开」**：本文所有 `file:line`（`issues.py:200/1093/1114/1132-1150`、
  `determinism-guards/spec.md:8`、`init.py:553`）均在本次会话中真实打开或 grep 确认。
- **PV 规则 5「正反双向」**：三份 `repo_root` 的逐字同款经 AST dump 全等实测（长度均 1146）
  确认，非凭 grep 行号推断。
- **D4 隔离**：三脚本不互相 import 的约定不变，本次只改各自内联副本。
- **基准 5「无界语法不手搓」**：本次不新增任何解析器；`isdir` 是让文件系统自己回答
  「这个路径能不能当根」，而非解析路径字符串猜测其合法性。
