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
        ▼  该值被 19 处调用当可写根拼路径，落到三处无条件建目录的写入器：
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
- `repo_root` 校验**根的身份**而非路径形状：证明返回值是起点所属仓库的根，否则响亮失败。
- 仓根在单次调用内**只解析一次**，消除锁与写入分裂到两个根的可能（ADR-5）。
- 起点（含显式 `--root`）与 git 输出**同等对待**，都在被当作可写根前经过校验。
- 三份同步，保持 `determinism-guards` 的 AST 三向等价守护为绿；且保持**抽取友好**（T170）。
- 消除假绿测试，使 `preserves_derived_bytes` 承诺可被变异验证证伪。
- 一份仓根 `conftest.py` 的 cwd 泄漏回归断言，覆盖全仓，防同类副作用再次隐形。

**Non-Goals:**
- 不重构镜像机制——已登记 **T170**（下一步工作，与 B11/B12 同 batch）。本次仍手工三改，但
  `repo_root` 最终形态须**抽取友好**（消息用通用文案、不含脚本名），使 T170 落地时是纯搬运。
- 不动 `sdflow-init/scripts/init.py:543` 的 `_git_root_or_dot()`：**其唯一消费链
  （`cmd_config_lint` → `lint_config`）不含 `os.makedirs`**，只读 config.yaml 且包在
  `except (OSError, UnicodeDecodeError)` 里 ⇒ 坏根只产生一条 lint 提示，不具现目录。
  （该文件另有 4 处 `os.makedirs`，走 `init`/`update`/`retire-hooks` 三个 mode 的
  `args.root` 路径，与 `_git_root_or_dot()` 不相交——**故不可表述为「全文件无 makedirs」**。）
  **这是安全论证，不是「不属 roster」的程序性理由。**
- 不给 `detect_change()`（`buglist.py:596-613` / `todolist.py` 同款）加同款加固：它内部有一次
  结构相同的 `git rev-parse --abbrev-ref HEAD` 子进程调用，**同样面临网络 FS 挂死的无限阻塞**，
  但其返回值只用作 provenance 字段（change 名），**不参与任何路径拼接、不进写入根** ⇒ 坏值的
  后果是「记错了来源 change」而非「写错目录」。**已记 todo**，与 T170 同批处理。
- 不动 `sdflow-ship/scripts/ship_gate.py:837`（同款反模式第 4 处）：其 `decide()` 开头即有
  `git rev-parse --git-dir` 前置兜底，坏根会安全落 `UNKNOWN`；全文件亦无 `makedirs`。
- 不在 helper 内做进程终止（`sys.exit` / `_die`）——抛异常交调用方处置，见 ADR-4。
- 不把「非 git 仓库」变成失败——那是正常用法，回落保持不变，见 ADR-1。
- 不限制 git stdout 的**读取量**：`capture_output=True` 无界读入，坏 wrapper 吐超大输出可在校验
  前耗内存。这是 DoS 面而非正确性面，且 `timeout=30` 已限住时间窗；改用 `Popen` + 定量读的复杂度
  不成比例。**已记 todo。**
- 不支持 Windows SUBST 盘符：pre-commit 为绕它才改用 `--show-cdup`；我们用 `--show-toplevel`
  在 `.git/` 目录内会 fatal（被 `check=True` 兜住）而 cdup 会静默返回空串——这一点上 toplevel 更
  安全，代价是放弃 SUBST。
- 不加 `--path-format=absolute`：git <2.31 不识别该选项时**不报错**，而是把它回显进 stdout 首行
  且 rc=0（实测），会让老 git 用户直接不可用。保留 `isabs` 校验即可。

## Decisions

### ADR-1：按「git 是否履行契约」分流，异常态不回落

**决策**：

```
start 非既存目录             ──► raise ValueError   # 起点不可信，在调 git 之前
git 抛 OSError / rc≠0        ──► abspath(start)     # 正常场景（非 git 仓库/bare/.git 内），不变
git 超时                     ──► raise ValueError   # 超时 ≠ 不在仓库里，不回落
git rc=0 且通过全部身份校验   ──► realpath(top)      # 形状 + 祖先 + marker，见 ADR-2
git rc=0 但任一校验不过       ──► raise ValueError   # 配置或调用被污染，响亮失败
```

**备选**：所有失败统一回落 `abspath(start)`。

**理由**：两种失败的语义根本不同——「非 git 仓库」是**正常用法**（常见），「git rc=0 却给出
坏值」是**配置或调用被污染**。把后者当前者处理正是静默失败的定义，而消灭静默失败是本变更的
全部意义。

⚠️ **「rc=0 + 坏 stdout 在真实 git 下不可达」这个论断已被推翻**，本 change 早期版本据此
弱化过风险，现予订正。实测两条真实可达路径：

1. **`core.worktree`**（`.git/config` 一行）⇒ rc=0 + 指向仓外的合法目录（见 ADR-2）。
2. **未知选项**：`git rev-parse` 对不认识的选项**不报错**，而是原样回显再继续，rc=0：
   ```
   $ git rev-parse --bogus-option --show-toplevel
   --bogus-option              ← 回显
   /path/to/toplevel
   rc=0
   ```
   ⇒ stdout 变成多行、首行是垃圾。

生产路径上命令是写死的三元组、不会有未知选项，故第 2 条不影响生产；但它证明「rc=0 + 坏值」
在 git 的行为空间里**真实存在**，不是理论构造。bare repo 与 `.git/` 目录内确实是 rc≠0
（实测 128）走回落分支，这一条仍成立。

统一回落还有一个**具体且严重**的后果：回落值是 `abspath(start)`，默认 `start="."` ⇒ 坏值会让
recorder 在 **cwd** 建出一棵**看起来完全合法**的 `openspec/issues/` 树并打印「已重建」、exit 0
（实测：非 git 仓库下跑 `reindex` 即此行为）。这比现状的垃圾 JSON 目录名**更隐蔽**——垃圾名扎眼
到能被人在文件树里一眼发现，`openspec/issues/` 不会。

**实测影响面**（分流补丁 spike，三份同改后还原）：三份 recorder + hack 全套件
`478 passed, 2 skipped, 4 failed`，红的只有本变更本就要改的 4 个用例；非 git 仓库下 `reindex`
仍 exit 0 正常完成；仓内 `scan` 正常。

**代价**：`repo_root` 从「永不失败」变为「可能抛异常」，契约变化需在 docstring 明写。

### ADR-2：校验的是**根的身份**，不是路径的形状；祖先校验是主防线

**决策**：形状校验（非空 + `isabs` + `isdir`）之后，**必须**再过身份校验：

```python
rt = os.path.normcase(os.path.realpath(top))
rs = os.path.normcase(os.path.realpath(start_abs))
if os.path.commonpath([rs, rt]) != rt:      # start 必须位于 top 之内
    raise ValueError(...)
if not os.path.exists(os.path.join(top, ".git")):   # worktree marker
    raise ValueError(...)
```

**备选**：只做形状校验（非空 + `isabs` + `isdir`）。

**理由**：形状校验回答「这是个既存绝对目录吗」，而我们要问的是「**这是不是起点所属仓库的根**」。
两者的差距不是理论——**两条实测可达的重定向路径都能通过形状校验**：

| 攻击渠道 | 环境净化能拦？ | 祖先校验能拦？ |
|---|---|---|
| `GIT_DIR` / `GIT_WORK_TREE` 环境变量 | ✅ | ✅ |
| **`core.worktree` 写在 `.git/config`（on-disk）** | ❌ **穿透** | ✅ **唯一防线** |

`core.worktree` 实测（git 2.50.1）：`.git/config` 里一行 `core.worktree = <仓外目录>`，在
**完全没有任何 `GIT_*` 环境变量**（`env -u` 全清）的情况下，`--show-toplevel` 返回那个仓外目录，
且 `isabs`/`isdir` 双双放行。而 `.git/config` 可以随 tarball、共享目录、NFS、别人递过来的仓库
一起到达。

⇒ **祖先校验是主防线，环境净化是纵深防御。删掉祖先校验 = `core.worktree` 缺口静默回归**，
且从代码上看不出来。本 ADR 的次序必须这样读，配套回归测试见 tasks 1.4。

**判据的三个实现细节**（均有实测依据）：
- 用 `os.path.commonpath` 按**路径组件**比较，不用裸字符串前缀匹配。
- `normcase` 处理 Windows 大小写不敏感（`C:\Users` vs `c:\users` 是同一路径）。
- `.git` marker 用 `os.path.exists` 而非 `isdir`——linked worktree 与 submodule 下它是**文件**
  （实测：linked worktree 的 `.git` 是 149 字节 ASCII 文件）。

**同时保留形状校验**：`isdir` 单独使用会被 cwd 绕过（`os.path.isdir` 对相对路径按 cwd 解析），
这是本 change 早期 spike 的实测结论——`isdir`-only 版本在仓根 cwd 下 4 passed、在空 cwd 下
4 failed，因为本 bug 自己产出的垃圾目录树就躺在仓根，形成自我掩盖。`isabs` 消除该差异。

**代价**：`repo_root` 从纯字符串处理变为带多次 IO 的函数；负例测试 MUST NOT mock
`os.path.isdir`/`isabs`/`realpath`（mock 掉判据本身等于没测）。

### ADR-5：仓根在单次调用内只解析一次

**决策**：`main()` 解析一次并写回 `args.root`；16 处 `cmd_*` 内的 `root = repo_root(args.root)`
改为 `root = args.root`。

**备选**：保留二次解析，但在第二次解析后用 `(st_dev, st_ino)` 与第一次结果比对身份。

**理由**：`repo_root()` 的校验是**逐次独立**的，不保证两次拿到同一个仓。实测复现：

```
$ git -C outer/proj rev-parse --show-toplevel   →  .../outer/proj     # call#1
$ rm -rf outer/proj/.git                                              # 窗口期
$ git -C outer/proj rev-parse --show-toplevel   →  .../outer          # call#2，爬升到外层
```

两次都 rc=0、都是既存绝对目录、都能通过全部校验——但 `recorder_lock` 的 metadata 记的是
call#1 的根，而 `cmd_batch_add`/`set_status`/`rename` 在第二次解析后**直接 `atomic_write`**
⇒ 把数据写进外层错误仓库的 `batches.md`。这正是本 change 开篇要消灭的「静默写错目录」，
只是触发条件从「git 输出乱码」换成「git 身份随时间漂移」。

选单点解析而非身份比对：**二次解析本来就是冗余的**（`main()` 已把结果写回 `args.root`），
删掉它是减法；加身份比对是往一个不该存在的调用上再加机制。

🔴 **「单次调用」的边界 = 进程，不是逻辑命令。** `_scan_pool` / `cmd_sweep` 会以 `--root <已解析值>`
拉起 `buglist.py` / `todolist.py` 子进程，子进程自己的 `main()` **仍会对该值再跑一次 `repo_root()`**。
跨进程看仍是「每进程各一次」，Success Metric 3 的「全脚本仅剩 3 处」正是按此计数。

跨进程二次解析的风险**由另一套机制兜底**：子进程重解析若得到不同的根，它拼出的 `_lock_path(root)`
处不存在锁文件 ⇒ `validate_recorder_participant` 走 `RecorderLockError` 响亮失败，而非静默写入。
**这层依赖是有意为之，此处显式登记**——将来若有人「简化」`validate_recorder_participant` 的
path/token 绑定（觉得两道校验重复），跨进程静默写错目录的风险会在没有任何 ADR-5 提示的情况下
重新出现。tasks 1.11 为此加锚定测试。

**代价**：16 处各改一行。副作用已核实——几个绕过 `main()` 直调 `cmd_*` 的测试传的都是真实存在
的 `tmp_path`（已是绝对路径），改后 `root = args.root` 行为等价。

### ADR-6：环境净化用**具名黑名单**，不用「全剔 `GIT_*` + 白名单」

**决策**：剔除 9 个具名变量 + 2 个前缀族：

```
GIT_DIR · GIT_WORK_TREE · GIT_COMMON_DIR · GIT_CEILING_DIRECTORIES · GIT_INDEX_FILE
GIT_DISCOVERY_ACROSS_FILESYSTEM · GIT_CONFIG_COUNT · GIT_CONFIG_GLOBAL · GIT_CONFIG_SYSTEM
GIT_CONFIG_KEY_* · GIT_CONFIG_VALUE_*        （前缀族，与 GIT_CONFIG_COUNT 必须一起剔）
```

**备选**：照抄 pre-commit 的 `no_git_env()`——剔除所有 `GIT_*`，再用白名单放回
`GIT_EXEC_PATH` / `GIT_SSH*` / `GIT_SSL*` / `GIT_ASKPASS` 等。

**理由**：pre-commit 的白名单是为 `clone` / 网络操作准备的，`rev-parse` 用不上那一套；全剔 +
白名单会引入「维护白名单」的负担和误伤 `GIT_EXEC_PATH` 的风险。具名黑名单只覆盖**仓库/工作树
发现**这一类，职责更窄。

清单依据 git 官方 environment variables 文档。后三组（`GIT_CONFIG_*`）是 config 注入通道——
本机实测它们当前**未能**重定向 toplevel（git 对非 `$GIT_DIR` 场景的 `core.worktree` 有额外约束），
但按目标态判据，它们在语义上就是注入通道、git 版本间行为会变，留着零收益。

**CI 影响已核实为零**：GitHub Actions（含 `actions/checkout`）与 GitLab Runner 均**不导出**
git 原生 `GIT_DIR`/`GIT_WORK_TREE`（GitLab 的 `GIT_STRATEGY` 等是 runner 自定义变量名，不传给
git）。**真正会导出它们的是 git hook**——submodule 中的 hook 会导出 `GIT_DIR`/`GIT_INDEX_FILE`，
git 2.6.3 起会导出 `GIT_WORK_TREE`。recorder 作为可分发 skill 会跑在任意消费项目里，hook 场景
真实存在 ⇒ 环境净化是必需项而非可选项。

🔴 **黑名单 MUST 写成 `repo_root` 函数体内的局部常量，MUST NOT 写成模块级常量。**
`test_mirror_consistency` 的三向 AST 比较**只 `getattr` roster 里的函数对象**，从不检查模块级
常量的**值**——一个 `Name` 节点只表示「引用了这个名字」，不携带绑定值。实测：三份现存的
`RECORDER_PARTICIPANT_ALLOWLIST` / `RECORDER_LOCK_ENV` 等模块级常量目前值相同，**纯属人肉维护
的巧合，零机械守护**。若黑名单按最自然的风格写成模块级常量，它会**完全落进既有安全网的盲区**，
三份漏一个变量名或 typo 时 `determinism-guards` 不会红——而「静默漂移」正是本 change 要铲除的
类别，不能在修它的同时原样复刻一份。

**这条约束同时是 T170 的前置**：若黑名单是模块级常量而 T170 只把 `repo_root` 函数体抽进
canonical 源，该常量的三向一致性将**永久**失去镜像保护。写在函数体内则随函数一起搬走。

**净化加在哪一层**：加在 `repo_root` 内部（局部），**不改 `recorder_child_env`**。后者是三向镜像
helper，另有两类调用方——`detect_change` 的 git 调用、跨进程 token 转发（`_scan_pool`/`cmd_sweep`
共 6 处）——在那里剔 `GIT_*` 会顺带改变它们的行为，而本次没有为这些消费点准备任何验证。
`detect_change` 的同类风险另行处置，见 Non-Goals。

**代价**：清单需随 git 演进维护（缓解：祖先校验对**可指向任意目录**的那类攻击兜底，见 ADR-2；
但对 `GIT_DISCOVERY_ACROSS_FILESYSTEM` 无兜底，见失败模式表⚠️）。

### ADR-7：起点解析用 `os.getcwd()`，`--root` 默认值改 `None`

**决策**：三份 argparse 的 `--root` 默认值从 `"."` 改为 `None`；`repo_root(start=None)` 时以
`os.getcwd()` 求起点（其 `FileNotFoundError` 转为受控 `ValueError`），显式传入时才走
`os.path.isdir(start)` 校验。

**备选**：保持 `default="."`，起点校验用 `os.path.isdir(".")`。

**理由**：**`os.path.isdir(".")` 在进程 cwd 被删除后仍返回 `True`**（实测，POSIX 通用行为），
而 `os.path.abspath(".")` 与 `os.getcwd()` 此时抛 `FileNotFoundError`。备选方案的连锁后果：

```
cwd 被外部删除
  → isdir(".") 误判通过（起点校验形同虚设）
  → git 以非 0 退出 → 落入「正常场景」回落分支
  → return os.path.abspath(start) 自身抛 FileNotFoundError
  → 该异常在 except 块内部抛出，不被同一 except (OSError, ...) 捕获
  → 裸传播 → main() 的 except ValueError 接不住 → 裸 traceback
```

这正是本 change 通篇要消灭的失败形状，只是触发条件换成了「cwd 被删除」。用 `os.getcwd()` 求
起点则**立即**抛出、就地转成受控 `ValueError`，缺口从源头消失。

**代价**：三份 argparse 定义各改一行；`repo_root` 的签名语义从「默认当前目录」变为「默认自动
探测」（行为等价，但把「未指定」与「显式指定 `.`」区分开了——后者仍走 `isdir` 校验）。

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

| 失败模式 | 当前行为 | 目标行为 | 拦它的判据 |
|---|---|---|---|
| git 不存在 / 非 git 仓库 | 抛异常 → `abspath(start)` | 不变 | —（正常场景） |
| git rc≠0（bare repo / `.git/` 内，实测 128） | 抛异常 → `abspath(start)` | 不变 | —（正常场景） |
| **`--root` 指向不存在/非目录** | 回落 `abspath(start)` → **下游 makedirs 具现该坏路径** | `ValueError` → exit 2 | 起点可信性（调 git 前） |
| **`core.worktree` on-disk 重定向** | **静默写进仓外目录** | `ValueError` → exit 2 | **祖先校验（唯一防线）** |
| `GIT_DIR`/`GIT_WORK_TREE` 重定向 | **静默写进另一个仓** | 正常返回真实根 | 环境净化 + 祖先校验兜底 |
| `GIT_DISCOVERY_ACROSS_FILESYSTEM` 越过挂载点 | 可能取到上层另一个仓 | 正常返回真实根 | **环境净化（唯一防线）**——见下方⚠️ |
| git rc=0，stdout 为空 / 非绝对 / 非目录 | **静默建垃圾目录树** | `ValueError` → exit 2 | 形状校验 |
| 坏值恰好命中 cwd 下同名目录 | 静默放行 | `ValueError` | `isabs`（形状校验） |
| 未知选项致 stdout 多行（rc=0） | 首行垃圾被当根 | `ValueError` → exit 2 | 形状校验（首行非绝对路径） |
| 路径末尾含合法空格/Tab | `strip()` 截短 → 可能命中另一目录 | 保留 | `rstrip("\r\n")` |
| **git 挂死（网络 FS 失联）** | **无限阻塞，不失败不可观测** | `ValueError` → exit 2 | `timeout=30`（**单次调用的界，非命令级预算**——见下方⏱） |
| **进程 cwd 在运行期被删除** | 起点校验被 `isdir(".")` 绕过 → 回落分支的 `abspath` 自身抛 `FileNotFoundError` → **裸 traceback** | `ValueError` → exit 2 | 起点解析用 `os.getcwd()` 而非 `isdir(".")`（ADR-7） |
| **两次解析间仓身份漂移** | 锁与写入分裂到两个根 | 不可能发生 | **单点解析（ADR-5）** |
| git rc=0，合法且通过身份校验 | 返回该目录 | 不变 | — |
| 调用方注入的 `subprocess.run` 被 mock 污染（测试） | **静默建垃圾目录树** | `ValueError` → exit 2 | 形状 + 祖先校验 |

⚠️ **祖先校验对 `GIT_DISCOVERY_ACROSS_FILESYSTEM` 结构性无效，不是「兜底」**：git 向上搜索
发现的任何 `.git` 所在目录，**按发现机制本身必然是 start 的文件系统祖先** ⇒ `commonpath` 恒成立。
该变量只影响「搜多远」，不影响「结果是不是祖先」。与之相对，`core.worktree` / `GIT_DIR` /
`GIT_WORK_TREE` 可指向**任意**目录，祖先校验对它们才是真防线。
**⇒ MUST NOT 因「反正有祖先校验兜底」而把它从环境净化清单中移除**——那会让缺口静默回归，
且没有任何测试会红。

⏱ **`timeout=30` 是单次 `repo_root()` 调用的界，不是命令级预算**：`cmd_sweep` 等命令会级联拉起
多个子进程（2 次 `scan` + 每命中项 1 次 `triage` + 1 次 `batch-add` + 1 次 `reindex`，后者内部又
拉 2 次 `scan`），每个子进程各自跑一次带 `timeout` 的 `repo_root()`。底层 FS 挂死时最坏总耗时
≈ `(4 + N) × 30s`，随命中项数线性增长。这是可接受的（最终仍会失败退出，非无限阻塞），但
**MUST NOT 把失败模式表读成「30s 封顶」**。

## 可观测性（TG-08）

诊断信息由 `ValueError` 的消息承载，经三份 `main()` 既有的 `except ValueError` 出口落 **stderr**，
进程以 exit code 2 结束。格式与 recorder 既有诊断一致：`ERROR: ...; cause: ...; fix: ...`
（全仓约 60 处同款）。

🔴 **被拒值 MUST 用 `ascii(value)[:N]` 生成，MUST NOT 用字节截断**。一招同时解决三个已实测问题：

| 问题 | 朴素做法的后果 | `ascii()` 为何解决 |
|---|---|---|
| 多字节 UTF-8 卡边界 | `("a"*78+"雪茄").encode()[:80].decode()` **抛 `UnicodeDecodeError`** —— fail-closed 路径**自身先崩**，且击穿 spec 的「MUST NOT 含 Traceback」 | 输出纯 ASCII，任意切片安全 |
| 控制字符伪造多行日志 | stdout 含 `\n`/`\r`/ANSI escape 时可伪造出多行诊断 | 全部转义为 `\n` 等字面 |
| 字符 vs 字节混淆 | 「80 字节」在 Python 切片语义下其实是字符 | 转义后二者一致 |

**诊断内容的取舍**：不携带 `start`、git 可执行文件路径、生效的 `GIT_*` 变量名——这些能提升可
诊断性，但 recorder 的 stderr **不过出境 `secret_scan`**（其 scope 限定在 outside-voice 的跨模型
prompt 出境路径），而本变更是**新增**的信息暴露面（修复前完全静默）。被拒值本身已是定位所必需
的最小信息，其余留给复现时的人工排查。

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
  **缓解**：ADR-5 的单点解析已把调用点从 19 处收到 3 处（三份 main 各一）⇒ 面大幅收窄；
  加 docstring 契约 + 三份各一条 CLI 级断言测试（真跑，让 Python 自己回答异常被没被接住）。
- **[祖先校验被后人删掉]** 它是唯一能拦 `core.worktree` 的判据，但从代码上看像是「多余的
  paranoia」——一次「简化重构」就能让缺口静默回归。
  **缓解**：ADR-2 明写其主防线地位 + tasks 1.4 的 `core.worktree` 回归测试（删掉判据即变红）。
- **[env 剔除清单随 git 演进失效]** 新版 git 可能引入新的发现类变量。
  **缓解**：祖先校验对**可指向任意目录**的那类攻击兜底（`core.worktree` 已实证）；但对
  `GIT_DISCOVERY_ACROSS_FILESYSTEM` 这类「只能返回祖先」的攻击面**无兜底**，清单是唯一防线
  （见失败模式表⚠️）。
- **[`cmd_*` 直调绕过全部校验]** ADR-5 后，六步校验**只在 `main()` 入口成立**；而绕过 `main()`
  直调 `cmd_*` 是本仓测试套件自身认可的合法形态（`test_issues.py` / `test_task4_rename_snapshot.py`
  / `test_frontmatter_dual_reader.py` 共 9 处）。若未来有编程式调用方直调并传入未校验的
  `args.root`，六步校验一步都不会执行。
  **缓解**：显式登记该契约——`cmd_*` **信任调用方已校验 `args.root`**，只有经 `main()` CLI 入口
  才有此保证。新增非 CLI 调用路径时须自行保证。（当前全部直调点传的都是 `str(tmp_path)`，已核实。）
- **[新增模块级常量逃出镜像守护]** AST 三向比较只覆盖 roster 内的**函数体**，不比较模块级常量的
  **值**。
  **缓解**：ADR-6 强制黑名单写在函数体内（局部常量），随函数一起被守护、也随函数被 T170 搬走。
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

**Windows 上的三条判据未经实测**（本地 macOS 照不到）：

1. `os.path.isabs("C:/Users/x")` → True（查 `ntpath` 文档得，未在真机跑）；但 MSYS 风格
   `/c/x` → False。git.exe 原生输出是 `C:/...`，正常路径安全。
2. `normcase` + `commonpath` 的祖先判据在盘符 / 大小写不敏感 / UNC 下的行为。
3. `realpath` 对 SUBST 盘符的行为——**无权威文档**，pre-commit 是靠换命令绕开而非修正，
   说明这条路他们也没走通。

⇒ 这三条构成 Q3（Windows 泳道）的直接依据。本仓已有同形状教训
（`windows-ci-bash-subprocess-traps`：本地 mac 照不到、真 Windows runner 跑才抓到）。
**MUST NOT 用「理论上大概率能过」结案**——那正是 `premise-verification.md` 规则 1 要拦的。

## Compliance

- **BASE-06 失败模式表**：见上「失败模式表」节（TG-08 命中）。
- **BASE-11 可观测性**：见上「可观测性」节（TG-08 命中）。
- **BASE-12 决策记录**：ADR-1 / ADR-2 / ADR-3 / ADR-4 / ADR-5 / ADR-6 / ADR-7（TG-23 命中）。
- **BASE-14 假设列表**：见 proposal「假设」节，4 条均已验证。
- **DOC-1 正文即最终态**：本文不含演进史；PoC 描述属当前事实证据，非考古层。
- **PV 规则 2「引用即打开」**：本文所有 `file:line`（`issues.py:200/1093/1114/1132-1150`、
  `determinism-guards/spec.md:8`、`init.py:543`、`ship_gate.py:837`）均在本次会话中真实打开或
  grep 确认。**第三轮冷复审订正**：`init.py` 的「全文件无 makedirs」表述过度概括（实为 4 处，
  但与目标消费链不相交），已改为按消费链表述。
- **PV 规则 5「正反双向」**：三份 `repo_root` 剥 docstring 后 `ast.dump` 相等，经现场跑
  `test_mirror_consistency.py` 确认（**不记具体 dump 长度**——该值随 Python 版本变化，
  3.9 与 3.14 下各不相同，不构成稳定锚）。
- **D4 隔离**：三脚本不互相 import 的约定不变，本次只改各自内联副本。
- **基准 5「无界语法不手搓」**：本次不新增任何解析器；`isdir` 是让文件系统自己回答
  「这个路径能不能当根」，而非解析路径字符串猜测其合法性。
