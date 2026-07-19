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

- `repo_root()` 重写为**证明根的身份**而非校验路径形状：起点可信性（含显式 `--root`）→ 环境净化
  → 调 git → 形状校验 → **祖先校验（主防线）** → worktree marker。git 失败（非 git 仓库等正常
  场景）保持回落 `abspath(start)`；其余一切抛 `ValueError`，经三份 `main()` 既有出口转为 stderr
  诊断 + exit 2。三份 recorder **同步修改**。
- **仓根在单次调用内只解析一次**：删除 16 处 `cmd_*` 内的二次解析（本就冗余），消除「锁建在一个
  根、数据写进另一个根」的可能。
- 修复 `test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes` 的假绿：
  让 root 解析不受 mock 污染，使 `preserves_derived_bytes` 这一半承诺真正被验证。
- 新增 **cwd 泄漏回归断言**：测试套件跑完后当前工作目录 MUST 无新增条目。
- 清理仓库根目录下 4 棵 JSON 命名的垃圾目录树——**必须最先做**：`os.path.isdir` 按 cwd 解析
  相对路径，这些残留会让坏值通过校验（实测：`isdir`-only 判据在仓根 4 passed、在空 cwd
  4 failed），在被污染环境里得到的绿不可信。
- 在 `CLAUDE.md` 的 `openspec/rules/` 段登记 `premise-verification.md` 的编号 + 路径指针。

## Capabilities

### New Capabilities
- `recorder-root-resolution`: recorder 仓根解析的信任边界——任何值在被当作可写根之前 MUST 被
  证明是**起点所属仓库的根**（形状 + 祖先 + worktree marker），起点本身（含显式 `--root`）亦须
  先经校验；配置被污染时 MUST 抛异常响亮失败，MUST NOT 静默回落；仓根在单次调用内 MUST 只解析
  一次。仅「非 git 仓库」这类正常场景才回落。

### Modified Capabilities
<!-- 无。`determinism-guards` 的 roster 已含 `repo_root`，本次三份同步修改后 AST 三向等价
     仍然成立，该 capability 的行为要求不变。 -->

## Impact

**受影响代码**：
- `repo_root` 本体三处 MUST 同步（非可选）：`issues.py:1132-1150` · `buglist.py:581-590` ·
  `todolist.py:581-590`
- **二次解析点 16 处**删除（ADR-5）：`issues.py` 6 处 + `buglist.py` 5 处 + `todolist.py` 5 处
  （`ast.walk` 精确统计：全仓 `repo_root` 调用共 **19** 处，减去三份 `main()` 各一 = 16）

**镜像约束**：`openspec/specs/determinism-guards/spec.md` 已把 `repo_root` 列入三向镜像
helper roster，由「剥 docstring 后 `ast.dump` 相等」的一致性测试守护。⇒ 只改一份会让该守护
当场变红；三份必须逐字一致。

**受影响测试**：
- `sdflow-issues/tests/test_task4_rename_snapshot.py:149`（假绿修复）
- 三份 recorder 各自的 `repo_root` 负例测试（新增）
- determinism-guards 的 AST 等价测试（须保持绿）

**同款反模式的全仓扫描**（`grep -rln "show-toplevel" --include="*.py" --include="*.sh"`，
排除 `.git/`/`tests/`/`openspec/changes/` 后**实测命中 8 个文件**，逐处论证见 Non-Goals）：
三份 recorder（本次修）· `init.py:543` · `ship_gate.py:837` · `assets/hack/resolve-models.sh` ·
`resolve-workflow.sh` · `outside-voice.sh`（后五处**有安全论证的排除**，非遗漏）。
⚠️ 早期版本此处写「4 处」且只枚举了 `.py`——**漏扫三个 shell 脚本**，由第三轮冷复审抓出。

**技术栈**：Python 脚本 + pytest，不命中 backend / embedded / frontend 任一领域清单。

## Success Metrics

1. **主防线可证伪**：`core.worktree` 回归测试存在且有效——在**完全没有 `GIT_*` 环境变量**的
   情况下，`.git/config` 里的 `core.worktree` 重定向 MUST 被拒绝；**删掉祖先校验该测试必须变红**
   （实现后跑一次变异确认）。这是整套判据里唯一能拦 on-disk 重定向的一环。
2. **fail-closed 覆盖全部输入面**：形状负例（非绝对/不存在/空/空白/末尾空格/多行）、起点负例
   （坏 `--root` 在调 git 前被拦；**cwd 被删除时得到受控 `ValueError` 而非裸 traceback**）、
   **环境净化负例**（`GIT_DIR`/`GIT_WORK_TREE` 重定向后仍返回真实根）、超时负例——三份各有
   测试且**不产生任何目录**。
3. **单点解析**：三份 `cmd_*` 函数体内 `repo_root(` 出现 **0** 次，全脚本仅剩 3 处调用。
4. **假绿被消除**（变异验证）：故意让 reindex 写入 `tmp_path` 时，
   `test_reindex_cli_non_string_id_...` MUST 变红。当前它恒绿，正是假绿的判据。
5. **零 cwd 残留**：仓内**任一** skill 的套件在干净临时目录跑完，该目录条目数 = 0——由仓根
   单一份 `conftest.py` 的 autouse fixture 机械保证（机械可验）。
6. **镜像守护仍绿**：determinism-guards 的 AST 三向等价测试通过，且 `repo_root` 保持**抽取友好**
   （消息用通用文案、不含脚本名）供 T170 纯搬运。
7. **仓根干净**：4 棵垃圾目录树清除，且重跑全套件不再生成。

## Non-Goals

- **不重构三份 recorder 的重复结构**：已登记 **T170**（下一步工作，与 B11/B12 同 batch）。本次
  仍手工三改，但 `repo_root` 须保持**抽取友好**，使 T170 落地时是纯搬运。
- **不给 `init.py:543` 的 `_git_root_or_dot()` 加同款校验**：**其唯一消费链
  （`cmd_config_lint` → `lint_config`）不含 `os.makedirs`**，只读 config.yaml 且包在
  `except (OSError, UnicodeDecodeError)` 里 ⇒ 坏根只产生一条 lint 提示，不具现目录。
  （该文件另有 4 处 `os.makedirs`，走 `init`/`update`/`retire-hooks` 的 `args.root` 路径，
  与 `_git_root_or_dot()` 不相交——故不可表述为「全文件无 makedirs」。）
  **这是安全论证，不是「不属 roster」的程序性理由。**
- **不动 `ship_gate.py:837`**：其 `decide()` 开头即有 `git rev-parse --git-dir` 前置兜底，坏根
  安全落 `UNKNOWN`；全文件亦无 `makedirs`。
- **不限制 git stdout 读取量**：DoS 面而非正确性面，`timeout` 已限时间窗，改 `Popen`+定量读复杂度
  不成比例。
- **不加 `--path-format=absolute`**：git <2.31 不识别时**不报错**而是回显进 stdout 首行且 rc=0
  （实测），会让老 git 用户直接不可用。
- **不支持 Windows SUBST 盘符**（`--show-toplevel` 换 `--show-cdup` 才能绕，但 cdup 在 `.git/`
  内静默返回空串，更不安全）。
- **不修 `sdflow-init/tests/test_outside_voice.py::test_exec_claude_reverse_path_three_flags_golden`**
  的 order-dependent 失败（全量跑红、单独跑绿）——不相干缺陷，另记 buglist。
- **不为 cwd 泄漏断言建独立扫描脚本 / CI 门**：一份仓根 `conftest.py` 的 autouse fixture 即
  覆盖全仓，价值定位是回归防护而非发现更多（普查证实当前仅 `sdflow-issues` 泄漏）。

## 需求优先级（TG-19）

| 优先级 | 需求 | 依据 |
|---|---|---|
| **P0** | `repo_root` 身份校验重写（形状 + 祖先 + marker + 起点） | 本体缺陷；祖先校验是 `core.worktree` 的唯一防线 |
| **P0** | 单点解析（删 16 处二次解析） | 锁与写入可分裂到两个根，实测可复现 |
| **P0** | 假绿测试修复 | 同一缺陷的另一半；当前 `preserves_derived_bytes` 未被验证 |
| **P1** | cwd 泄漏回归断言 | 回归防护；本次靠肉眼扫 IDE 侧栏才发现 |
| **P0** | 清理 4 棵垃圾目录树 | **前置条件**：残留会让 isdir 判据被绕过，污染环境下的验证不可信 |
| **P2** | CLAUDE.md 登记 PV 规则指针 | 规则已落盘但无索引，会漂 |

## 假设（TG-22）

| 假设 | 验证状态 | 失效影响 |
|---|---|---|
| ~~生产环境不会触发这条路径~~ | ❌ **已推翻**（本轮 spec-review）：`core.worktree` 写在 `.git/config` 即可 rc=0 返回仓外目录（无需任何环境变量，实测）；`GIT_DIR`/`GIT_WORK_TREE` 亦实测可重定向；`git rev-parse` 对未知选项回显且 rc=0。bare repo rc=128 走回落这一条仍成立 | 原假设曾被用来弱化风险，现予订正 |
| 仅 `sdflow-issues` 泄漏 cwd | ✅ 已实测：12 个 skill + hack 各自干净目录跑一遍，其余 0 残留 | 若他处也泄漏，回归断言的覆盖面需扩大 |
| `repo_root` 三份逐字一致 | ✅ 已查 `determinism-guards/spec.md:8` roster + AST 等价守护 | 若守护实际未覆盖，则三份可能已漂移，需先对齐再改 |
| 校验升级不破坏既有调用方 | ✅ 已查：`ast.walk` 精确统计**19** 处调用（非早期误写的 14），除三份 `main()` 入口外 16 处均为 `root = repo_root(args.root)` 形态，ADR-5 直接删除；`abspath(start)` 回落分支既有 | 若存在依赖「返回不存在路径再自建」的调用方，会被 fail-closed 拦下 |
| 判据在 macOS + git 2.50.1 下正确 | ✅ 已实测 10 场景全过：普通仓/子目录/linked worktree/submodule/symlink/`GIT_DIR` 攻击/`core.worktree` 攻击/非 git/bare/起点不存在 | — |
| 环境净化不打破 CI | ✅ 已查：GitHub Actions（含 `actions/checkout`）与 GitLab Runner 均不导出 git 原生 `GIT_DIR`/`GIT_WORK_TREE`；真正导出它们的是 **git hook**（submodule hook 导出 `GIT_DIR`/`GIT_INDEX_FILE`，git 2.6.3 起导出 `GIT_WORK_TREE`）⇒ 净化是必需项 | 若某 CI 依赖 `GIT_DIR` 指向非标准位置，recorder 会改为按真实仓根工作 |
| **判据在 Windows 上成立** | ⚠️ **未实测**（本地 macOS 照不到）：`isabs("C:/…")`、`normcase`+`commonpath` 在盘符/大小写/UNC 下的行为、`realpath` 对 SUBST | 若不成立，Windows 用户的正常调用会从「能跑」变成 exit 2 硬失败 ⇒ 见 tasks 4.6 |

## Compliance

N/A —— 本变更不涉及外部合规要求、个人数据或计费服务。
