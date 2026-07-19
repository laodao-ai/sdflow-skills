## Why

三份 recorder（`issues.py` / `buglist.py` / `todolist.py`）的镜像 helper `repo_root()` 把
`git rev-parse --show-toplevel` 的 stdout **零校验**地当仓根返回，而下游 `recorder_lock`、
`atomic_write`、`atomic_write_bytes` 三处都会对该值 `os.makedirs(..., exist_ok=True)`——
**任意字符串都会被静默具现成目录树并往里写数据**，不报错、不留痕。

这条路径已有实证 PoC：`sdflow-issues/tests/test_task4_rename_snapshot.py:149` 在 monkeypatch
全局 `subprocess.run` 后，`repo_root` 拿到整段 scan JSON 当根，在 **cwd** 建出 4 棵垃圾目录树
（仓根现存 4 棵，因全是空目录而对 `git status` 隐形）。同一个 PoC 还暴露该测试**假绿**：它的
`preserves_derived_bytes` 断言之所以成立，是因为 reindex 全程没碰过 `tmp_path`，而非派生字节
真被保护住了。

## What Changes

- `repo_root()` 按「git 是否履行契约」**分流**：git 失败（非 git 仓库等正常场景）保持回落
  `abspath(start)`；git rc=0 但输出不是**既存的绝对路径目录**则抛 `ValueError`，经三份 `main()`
  既有出口转为 stderr 诊断 + exit 2，**不再静默回落**。三份 recorder **同步修改**（见 Impact
  的镜像约束）。
- 修复 `test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes` 的假绿：
  让 root 解析不受 mock 污染，使 `preserves_derived_bytes` 这一半承诺真正被验证。
- 新增 **cwd 泄漏回归断言**：测试套件跑完后当前工作目录 MUST 无新增条目。
- 清理仓库根目录下 4 棵 JSON 命名的垃圾目录树——**必须最先做**：`os.path.isdir` 按 cwd 解析
  相对路径，这些残留会让坏值通过校验（实测：`isdir`-only 判据在仓根 4 passed、在空 cwd
  4 failed），在被污染环境里得到的绿不可信。
- 在 `CLAUDE.md` 的 `openspec/rules/` 段登记 `premise-verification.md` 的编号 + 路径指针。

## Capabilities

### New Capabilities
- `recorder-root-resolution`: recorder 仓根解析的 fail-closed 契约——外部进程输出在被当作
  可写根之前 MUST 通过「绝对路径 + 既存目录」校验；git 未履行契约（rc=0 却给出坏值）时
  MUST 抛异常响亮失败，MUST NOT 静默回落；仅「非 git 仓库」这类正常场景才回落。

### Modified Capabilities
<!-- 无。`determinism-guards` 的 roster 已含 `repo_root`，本次三份同步修改后 AST 三向等价
     仍然成立，该 capability 的行为要求不变。 -->

## Impact

**受影响代码**（三处 MUST 同步，非可选）：
- `sdflow-issues/scripts/issues.py:1143-1148`
- `sdflow-buglist/scripts/buglist.py:588`
- `sdflow-todolist/scripts/todolist.py:588`

**镜像约束**：`openspec/specs/determinism-guards/spec.md` 已把 `repo_root` 列入三向镜像
helper roster，由「剥 docstring 后 `ast.dump` 相等」的一致性测试守护。⇒ 只改一份会让该守护
当场变红；三份必须逐字一致。

**受影响测试**：
- `sdflow-issues/tests/test_task4_rename_snapshot.py:149`（假绿修复）
- 三份 recorder 各自的 `repo_root` 负例测试（新增）
- determinism-guards 的 AST 等价测试（须保持绿）

**不影响**：`sdflow-init/scripts/init.py:553` 的 `_git_root_or_dot()` 不属镜像 roster，
本次不动（其已有空值兜底，缺 isdir 校验一并见 Non-Goals）。

**技术栈**：Python 脚本 + pytest，不命中 backend / embedded / frontend 任一领域清单。

## Success Metrics

1. **fail-closed 生效**：三份 `repo_root` 各有负例测试——喂入「非绝对路径 / 绝对但不存在 /
   空 / 纯空白」时抛 `ValueError`（CLI 级表现为 exit 2 + stderr 诊断），且**不产生任何目录**；
   其中「坏值恰好命中 cwd 下同名目录」的用例在仓内/仓外两种 cwd 下结果一致。
2. **假绿被消除**（变异验证）：故意让 reindex 写入 `tmp_path` 时，
   `test_reindex_cli_non_string_id_...` MUST 变红。当前它恒绿，正是假绿的判据。
3. **零 cwd 残留**：仓内**任一** skill 的套件在干净临时目录跑完，该目录条目数 = 0——由仓根
   单一份 `conftest.py` 的 autouse fixture 机械保证（机械可验）。
4. **镜像守护仍绿**：determinism-guards 的 AST 三向等价测试通过。
5. **仓根干净**：4 棵垃圾目录树清除，且重跑全套件不再生成。

## Non-Goals

- **不重构三份 recorder 的重复结构**：镜像是 `determinism-guards` 明文要求的设计（skill 自包含
  + D4 隔离），本次只加固共享 helper 的输入校验，不动镜像机制本身。
- **不给 `init.py:_git_root_or_dot()` 加同款校验**：它不属镜像 roster，是独立一件事。
- **不修 `sdflow-init/tests/test_outside_voice.py::test_exec_claude_reverse_path_three_flags_golden`**
  的 order-dependent 失败（全量跑红、单独跑绿）——不相干缺陷，另记 buglist。
- **不为 cwd 泄漏断言建独立扫描脚本 / CI 门**：一份仓根 `conftest.py` 的 autouse fixture 即
  覆盖全仓，价值定位是回归防护而非发现更多（普查证实当前仅 `sdflow-issues` 泄漏）。

## 需求优先级（TG-19）

| 优先级 | 需求 | 依据 |
|---|---|---|
| **P0** | 三份 `repo_root` fail-closed 校验 | 本体缺陷；下游三处 `makedirs` 无条件信任 |
| **P0** | 假绿测试修复 | 同一缺陷的另一半；当前 `preserves_derived_bytes` 未被验证 |
| **P1** | cwd 泄漏回归断言 | 回归防护；本次靠肉眼扫 IDE 侧栏才发现 |
| **P0** | 清理 4 棵垃圾目录树 | **前置条件**：残留会让 isdir 判据被绕过，污染环境下的验证不可信 |
| **P2** | CLAUDE.md 登记 PV 规则指针 | 规则已落盘但无索引，会漂 |

## 假设（TG-22）

| 假设 | 验证状态 | 失效影响 |
|---|---|---|
| 生产环境不会触发这条路径 | ✅ 已实测：`check=True`，bare repo 下 `git rev-parse --show-toplevel` 返 rc=128 走异常分支，非「rc=0 + 坏 stdout」 | 若某 git wrapper／企业包装脚本往 stdout 多吐一行，则静默建垃圾树 —— **这正是本次要堵的目标态缺口** |
| 仅 `sdflow-issues` 泄漏 cwd | ✅ 已实测：12 个 skill + hack 各自干净目录跑一遍，其余 0 残留 | 若他处也泄漏，回归断言的覆盖面需扩大 |
| `repo_root` 三份逐字一致 | ✅ 已查 `determinism-guards/spec.md:8` roster + AST 等价守护 | 若守护实际未覆盖，则三份可能已漂移，需先对齐再改 |
| 加「isabs + isdir」校验不破坏既有调用方 | ✅ 已查：三份共 14 个调用点形态一致（`root = repo_root(args.root)` → 拼 `openspec/issues/...`），且 `abspath(start)` 回落分支既有（非 git 仓库时走它）；无调用方依赖「返回不存在的路径再自建」 | 若存在此类调用方，会被 fail-closed 拦下 |

## Compliance

N/A —— 本变更不涉及外部合规要求、个人数据或计费服务。
