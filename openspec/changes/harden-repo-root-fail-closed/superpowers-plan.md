---
impl-pipeline: tickets
---

## Global Constraints

以下条款**逐字**摘自本 change 的 `design.md`，适用于每一张 ticket 的实现与评审。

### 结构与实现约束

🔴 **黑名单 MUST 写成 `repo_root` 函数体内的局部常量，MUST NOT 写成模块级常量。**
`test_mirror_consistency` 的三向 AST 比较**只 `getattr` roster 里的函数对象**，从不检查模块级
常量的**值**——一个 `Name` 节点只表示「引用了这个名字」，不携带绑定值。实测：三份现存的
`RECORDER_PARTICIPANT_ALLOWLIST` / `RECORDER_LOCK_ENV` 等模块级常量目前值相同，**纯属人肉维护
的巧合，零机械守护**。若黑名单按最自然的风格写成模块级常量，它会**完全落进既有安全网的盲区**，
三份漏一个变量名或 typo 时 `determinism-guards` 不会红——而「静默漂移」正是本 change 要铲除的
类别，不能在修它的同时原样复刻一份。

⚠️ **祖先校验对 `GIT_DISCOVERY_ACROSS_FILESYSTEM` 结构性无效，不是「兜底」**：git 向上搜索
发现的任何 `.git` 所在目录，**按发现机制本身必然是 start 的文件系统祖先** ⇒ `commonpath` 恒成立。
该变量只影响「搜多远」，不影响「结果是不是祖先」。与之相对，`core.worktree` / `GIT_DIR` /
`GIT_WORK_TREE` 可指向**任意**目录，祖先校验对它们才是真防线。
**⇒ MUST NOT 因「反正有祖先校验兜底」而把它从环境净化清单中移除**——那会让缺口静默回归，
且没有任何测试会红。

⏱ **`timeout=30` 是单次 `repo_root()` 调用的界，不是命令级预算**：底层 FS 挂死时最坏总耗时
≈ `(4 + N) × 30s`，随命中项数线性增长。这是可接受的（最终仍会失败退出，非无限阻塞），但
**MUST NOT 把失败模式表读成「30s 封顶」**。

### 可观测性约束

🔴 **被拒值 MUST 用 `ascii(value)[:N]` 生成，MUST NOT 用字节截断**。一招同时解决三个已实测问题：
多字节 UTF-8 卡边界（`("a"*78+"雪茄").encode()[:80].decode()` **抛 `UnicodeDecodeError`** ——
fail-closed 路径**自身先崩**，且击穿 spec 的「MUST NOT 含 Traceback」）、控制字符伪造多行日志、
字符 vs 字节混淆。

MUST NOT 写入 stdout：recorder 的 stdout 是机器可读契约（`scan --json` 的消费方会解析它），
污染 stdout 会把这次修复变成新的解析故障。

**退出码可区分性**：坏 root 与坏 scan id 都产生 exit 2 ⇒ 相关测试 MUST 断言 stderr 的具体
诊断内容，MUST NOT 仅凭退出码判定通过（否则「在更早的关口崩了」会被误判为「测中了目标」——
本变更修复的假绿正是这个形状）。

### 测试方法论约束

负例测试 MUST NOT mock `os.path.isabs` / `isdir` / `realpath`（mock 掉判据本身 = 测了个寂寞），
用 `tmp_path` 下真实存在/不存在的路径构造。

**MUST NOT 用「理论上大概率能过」结案**——那正是 `premise-verification.md` 规则 1 要拦的。

**基准 5「无界语法不手搓」**：本次不新增任何解析器；`isdir` 是让文件系统自己回答。
判断「`cmd_*` 里还有没有 `repo_root(` 调用」MUST 用 `ast.walk` 数 Call 节点，
**MUST NOT 用 grep**——grep 会把 `def repo_root(` 与 docstring 里的字面量一并算入。

### Compliance

- **BASE-06 失败模式表** / **BASE-11 可观测性**：TG-08 命中，见 design 对应节。
- **BASE-12 决策记录**：ADR-1 … ADR-7（TG-23 命中）。
- **DOC-1 正文即最终态**：文档改动不留演进史，正文只写最终态。
- **PV 规则 2「引用即打开」**：任何 `file:line` 引用 MUST 在落笔前真实打开确认。
- **PV 规则 5「正反双向」**：新增守护 MUST 有「删掉它就变红」的变异确认，
  MUST NOT 只验证正向通过。
- **D4 隔离**：三脚本不互相 import 的约定不变，本次只改各自内联副本。

### 跨 ticket 硬约束

- **三份 recorder（`issues.py` / `buglist.py` / `todolist.py`）的 `repo_root` MUST 在同一提交内
  同步修改**，剥 docstring 后 `ast.dump` 相等——`determinism-guards` 的三向镜像守护会拦截漂移。
- **`raise` 消息 MUST 是通用文案，不含脚本名 / `__file__`**：否则 AST 镜像守护当场变红，
  且破坏 T170（把 helper 抽进 canonical 源）的抽取友好性。
- **MUST NOT 在 `repo_root` 内 `sys.exit`**：抛 `ValueError`，由三份 `main()` 既有的
  `except ValueError` 出口转 stderr + exit 2。

---

### Task 1: 清理污染环境，建立可信验证基线

**Blocked-by:** none
**R-ID:** R4（测试套件不得在当前工作目录留下副作用）

仓库根目录下 4 棵以 JSON 字符串命名的垃圾目录树被删除，删除前先列出确认；删除后同一条列举命令
无输出。

**为什么必须是第 1 张**：`os.path.isdir` 按 cwd 解析相对路径，这些残留会让坏值通过校验
（实测：`isdir`-only 判据在仓根 4 passed、在空 cwd 4 failed）。**在被污染的环境里得到的任何绿
都不可信**——本 change 的第一次 spike 就因此产生过一轮假绿。

- [x] 仓根不再有以 `{` 开头的目录条目
- [x] 删除动作在提交历史中可见（列举 → 删除 → 复核三步留痕）

---

### Task 2: repo_root 六步身份校验（三份同步）

**Blocked-by:** 1
**R-ID:** R1（仓根解析证明根的身份）· R3（三份逐字一致）

三份 recorder 的 `repo_root` 在**同一提交内**同步重写为六步判据：起点校验 → 环境净化 → 调 git →
形状校验 → **祖先校验** → worktree marker 校验。任何不满足者抛 `ValueError`；仅「git 命令失败」
（非 git 仓库、bare repo 等正常场景）保持回落 `abspath(start)`。

行为上可观察的结果：

- 起点不可信（显式传入的路径不是既存目录，或未指定时进程 cwd 已被删除）→ 在**调 git 之前**
  受控失败，且该路径不被创建；
- 环境中的 `GIT_DIR` / `GIT_WORK_TREE` 等仓库选择类变量被净化后，返回的仍是真实仓根；
- `.git/config` 里的 `core.worktree` 指向仓外目录时（**完全不依赖任何 `GIT_*` 环境变量**）→
  被拒绝，仓外目录下不出现任何 `openspec/`；
- git 探测超时 → 受控失败，**不回落**；
- linked worktree / submodule（`.git` 是文件）/ symlink 起点 / 子目录起点 → 均正常返回。

结构硬约束（违反其一即本 ticket 不通过）：`try` 只包 `subprocess.run`，只捕
`OSError` / `CalledProcessError`；`TimeoutExpired` 单独 `raise`；**一切校验与 `raise` 位于 try
之外**（否则新抛的 `ValueError` 被自己的 except 接住，fail-closed 归零）；禁 `except Exception`。

- [x] 六步判据三份逐字一致，`determinism-guards` 的三向 AST 等价测试保持绿
- [x] 形状负例（非绝对 / 绝对但不存在 / 空串 / 纯空白 / 末尾含空格 / 多行）各自被拒，
      **且断言对应路径未被创建**
- [x] `core.worktree` 回归用例存在，且**删掉祖先校验后该用例变红**（变异确认，非仅正向通过）
- [x] `GIT_DIR`/`GIT_WORK_TREE` 重定向：净化后返回真实根；**再单独验证不净化时祖先校验也拦得住**
      （证明两层防御各自独立有效）
- [x] 起点负例：坏路径在调 git 前被拒且不被创建；进程 cwd 被删除时得到受控失败
      （实测依据：此时 `os.path.isdir(".")` 仍返回 `True`）
- [x] 超时负例：注入不返回的 fake git → 受控失败且不回落
- [x] 正向回归：linked worktree / submodule / symlink / 子目录起点均正常；
      非 git 仓库 / bare repo / `.git/` 内回落且 CLI exit 0

---

### Task 3: 单点解析——仓根在一次调用内只解析一次

**Blocked-by:** 2
**R-ID:** R2（仓根在单次调用内只解析一次，边界=进程）

同一次 CLI 调用内仓根只被解析一次：入口解析并校验，各命令直接消费已验证的值，不再自行重解析。
消除「锁建在一个根、数据写进另一个根」的可能——该分裂已实测可复现（两次解析之间目标失去 `.git`
时，第二次静默爬升到外层祖先仓库，两次都 rc=0 且判据全放行）。

跨进程不在「单次调用」的边界内：子进程重新解析得到不同根时，由参与者校验的 path/token 绑定
兜底、响亮失败，而非静默写入。

- [x] 命令函数内的 `repo_root` 调用归零；全脚本 Call 节点从 **19** 降到 **3**（三份入口各一），
      统计手段用 `ast.walk`
- [x] `--root` 未指定与显式指定两条路径行为可区分（未指定 → 探测；显式 → 先校验）
- [x] `repo_root` 的 docstring 与新架构一致（现文描述的是旧架构，ADR-5 后失真）
- [ ] 跨进程锚定用例存在：父进程持锁 → 子进程解析出不同根 → 子进程响亮失败。
      **这条锚定的是一个隐含依赖**，无此用例，将来「简化」该校验会让静默写错目录无声回归
      ⚠️ **有条件达成，故本框不勾（勾一个「有条件达成」= 假绿）**：spike 双向独立复现证明
      spec R2 Scenario 3 的 MUST **当前不成立**——`recorder_lock` 吞掉 `RecorderLockError`
      回落 owner 模式，子进程 rc=0 静默写进外层根。已落 `xfail(strict=True)` 机械锚
      （堵上即 XPASS 判红）+ **B15**（P1，含 6 个生产 spawn 站点影响面 + 完整修法）。
      修法须触 lock spec ⇒ **属设计门议题，本 change 内不 fold**（改 spec 会令已拍板设计门失鲜）。

---

### Task 4: 消除 reindex 假绿测试

**Blocked-by:** 2
**R-ID:** R5（坏 root 下的 reindex 不得静默通过派生字节校验）

`test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes` 当前的
`preserves_derived_bytes` 断言之所以成立，是因为 reindex 全程没碰过临时目录，而非派生字节真被
保护住了。修复后该断言真正被验证。

- [ ] root 解析不再受该用例的全局 `subprocess.run` mock 污染，reindex 真正作用于临时目录
- [ ] **变异验证**：故意让 reindex 向临时目录的派生文件写入 → 该测试**变红**；恢复后变绿
      （当前它对该变异恒绿，正是假绿判据）
- [ ] 断言集完整：退出码 + **stderr 含可区分的具体诊断**（坏 root 与坏 scan id 都是 exit 2，
      仅凭退出码判定 = 复刻同一类假绿）+ 派生字节不变 + cwd 无新增条目
- [ ] 修复后若暴露此前从未执行过的 reindex 分支失败 → **当场 fold 修掉，不 defer**

---

### Task 5: cwd 泄漏回归断言（全仓覆盖）

**Blocked-by:** 1
**R-ID:** R4（测试套件不得在当前工作目录留下副作用）

任一 skill 的测试套件在干净目录跑完后，该目录不新增顶层条目；泄漏发生时测试失败并报出条目名。
覆盖面是全仓而非仅 recorder，由**仓根单一份**断言承载——MUST NOT 在各 skill 的 `tests/` 下复制
副本（那会构成第四组无守护的镜像，正是本 change 要铲除的类别）。

- [ ] 断言为仓根唯一一份，全仓生效
- [ ] 12 个 skill + hack 各自在干净临时目录跑一遍，全部生效且**无误报**
      （实测基线：本 change 前均 0 残留）
- [ ] **反向验证**：临时插一个在 cwd 建目录的用例，确认被捕获并报出条目名
      （只验证「没红」不构成证据）

---

### Task 6: 面治闭环与收尾

**Blocked-by:** 2, 3, 4, 5
**R-ID:** R1, R4（收敛验证）

同款反模式的全仓扫描闭环、跨平台覆盖补齐、文档与规则指针同步。

**扫描 MUST 不限扩展名**，且验证手段 MUST 是「重跑扫描」而非「核对与文档处数自洽」——后者只验
内部自洽、验不了漏扫（本轮冷复审正是这样抓到 4→8 的）。其中 `outside-voice.sh` 把仓根传给
`codex exec -C … --add-dir …`，**值域与「只读拼路径」不同，MUST 单独论证，不得套用豁免模板**。

- [ ] 重跑扫描确认命中处数，逐处给出纳入/排除理由，排除理由是**安全论证**（sink 只读 / 无目录
      创建 / 有前置兜底），**不是**「不属 roster」这种程序性理由
- [ ] Windows 泳道真实覆盖 `repo_root`：正向回归（真实 git 仓库下不抛异常）+ 至少一条负例。
      现状是该泳道只跑直传临时目录的用例、**绕开 `repo_root`**，主矩阵只有 ubuntu/macos ⇒
      新判据从未在 Windows 真跑过。design Open Questions 的三条（盘符 `isabs`、
      `normcase`+`commonpath` 在大小写/UNC 下的行为、`realpath` 对 SUBST）全部未实测
- [ ] `CLAUDE.md` 登记 `premise-verification.md` 的编号 + 路径指针（**只写编号 + 路径，
      MUST NOT 复制规则文本**）
- [ ] `CLAUDE.md`「运行测试」段同步：「没有根级 pytest 配置」一句已被 Task 5 证伪，
      改为如实描述（不改即为本变更自己制造的文档漂移）
- [ ] 垃圾目录树**未再生**（Task 1 删的是存量，本条验证的是「修完之后不会重新长出来」）
- [ ] 两条 defer 如实登记（`outside_voice` 用例的 order-dependent 失败 → buglist；
      git stdout 无界读入的 DoS 面 → todolist），登记时**显式带 `change` 字段**
- [ ] 全仓 `pytest` 无回归
